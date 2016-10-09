# coding:utf8

import pytest
from kotti.testing import BASE_URL
from kotti.testing import user
from mock import patch
from webtest.forms import Upload


class TestLogin:
    def test_it(self, app):
        res = app.post(
            '/@@login', dict(login='admin', password='secret', submit='submit'))
        assert res.status == '302 Found'
        res = res.maybe_follow()
        assert res.status == '200 OK'


class TestForbidden:
    def test_forbidden(self, app):
        app.get('/@@edit', headers={'Accept': '*/json'}, status=403)

    def test_forbidden_redirect(self, app):
        res = app.get('/@@edit', headers={'Accept': 'text/html'}, status=302)
        assert res.location.startswith('http://localhost/@@login?came_from=')

    def test_forbidden_redirect_when_authenticated(self, app):
        with patch('pyramid.request.Request.authenticated_userid', 'foo'):
            res = app.get('/@@edit', status=302)
        assert res.location == 'http://localhost/@@forbidden'


class TestUploadFile:

    def add_file(self, browser, contents='ABC'):
        file_ctrl = browser.getControl("File")
        file_ctrl.add_file(contents, 'image/gif', 'my_image.gif')
        browser.getControl('save').click()

    @user('admin')
    def test_it(self, browser, filedepot):
        browser.open(BASE_URL + '/@@add_file')
        self.add_file(browser)
        assert "Item was added" in browser.contents

    @user('admin')
    def test_view_uploaded_file(self, browser, filedepot):
        browser.open(BASE_URL + '/@@add_file')
        self.add_file(browser)
        browser.getLink("View").click()
        browser.getLink("Download file").click()
        assert browser.contents == 'ABC'

    @user('admin')
    def test_tempstorage(self, browser, filedepot):
        browser.open(BASE_URL + '/@@add_file')
        self.add_file(browser, contents='DEF')
        browser.getLink("Edit").click()
        browser.getControl("Title").value = ''  # the error
        assert "Your changes have been saved" not in browser.contents
        browser.getControl("Title").value = 'A title'
        browser.getControl('save').click()
        assert "Your changes have been saved" in browser.contents
        browser.getLink("View").click()
        browser.getLink("Download file").click()
        assert browser.contents == 'DEF'

    @user('admin')
    def test_edit_uploaded_file(self, browser, filedepot):
        browser.open(BASE_URL + '/@@add_file')
        self.add_file(browser, contents='GHI')
        browser.getLink("Edit").click()
        browser.getControl('save').click()
        browser.getLink("Download file").click()
        assert browser.contents == 'GHI'


class TestValidatorMaxLength:

    @user('admin')
    def test_title_max_length_document_ko(self, browser, filedepot):
        browser.open(BASE_URL + '/@@add_document')
        from kotti.resources import Node
        max_length = Node.name.property.columns[0].type.length
        browser.getControl("Title").value = '1' * (max_length + 1)  # the error
        browser.getControl('save').click()
        assert "Item was added" not in browser.contents

    @user('admin')
    def test_title_max_length_document_ok(self, browser):
        browser.open(BASE_URL + '/@@add_document')
        from kotti.resources import Node
        max_length = Node.name.property.columns[0].type.length
        browser.getControl("Title").value = '1' * max_length
        browser.getControl('save').click()
        assert "Item was added" in browser.contents

    @user('admin')
    def test_title_max_length_file_ok(self, browser):
        browser.open(BASE_URL + '/@@add_file')
        from kotti.resources import Node
        max_length = Node.name.property.columns[0].type.length
        browser.getControl("Title").value = '1' * max_length
        file_ctrl = browser.getControl("File")
        file_ctrl.add_file("abc", 'image/gif', 'my_image.gif')
        browser.getControl('save').click()
        assert "Item was added" in browser.contents

    @user('admin')
    def test_title_max_length_file_ko(self, browser):
        browser.open(BASE_URL + '/@@add_file')
        from kotti.resources import Node
        max_length = Node.name.property.columns[0].type.length
        browser.getControl("Title").value = '1' * (max_length + 1)  # the error
        file_ctrl = browser.getControl("File")
        file_ctrl.add_file("abc", 'image/gif', 'my_image.gif')
        browser.getControl('save').click()
        assert "Item was added" not in browser.contents


class TestBrowser:
    """ This is a one to one conversion of the former browsert.txt.
    These tests should definitively be rewritten and splitted into multiple
    methods to ease readability.
    """

    @staticmethod
    def _login(app, login, password):
        resp = app.get('/@@login')
        form = resp.forms['login-form']
        form['login'] = login
        form['password'] = password
        resp = form.submit('submit')
        return resp

    @staticmethod
    def _select_children(resp, *child_idx):
        """ Mark the checkbox(es) of the rows in the ``contents`` view

        :param resp: response which's body contains the contents table
        :type resp: :class:`webtest.response.TestResponse`

        :param *child_idx: index of the child in the folder listing
                           (starting with 0)
        :type *child_idx: int

        :return: contents form with children selected (ready for submission)
        :rtype: :class:`webtest.forms.Form`
        """

        form = resp.forms['form-contents']
        form['children'] = [
            cb._value for cb in [
                form.fields['children'][idx] for idx in child_idx]]

        return form

    def test_login(self, webtest):

        # get the frontpage
        resp = webtest.app.get('/')
        assert "You have successfully installed Kotti." in resp.body

        # access a protected URL
        resp = webtest.app.get('/edit').maybe_follow()
        assert "Log in" in resp.body

        # submit the login form
        form = resp.forms['login-form']
        assert form['came_from'].value == 'http://localhost/edit'
        form['login'] = 'admin'
        form['password'] = 'secret'

        resp = form.submit('submit').maybe_follow()
        assert "Welcome, Administrator" in resp.body

        # log out
        resp = resp.click('Logout').maybe_follow()
        assert "You have been logged out" in resp.body

        # attempt to login with wrong credentials
        form = resp.forms['login-form']
        assert form['came_from'].value == 'http://localhost/edit'
        form['login'] = 'admin'
        form['password'] = 'funny'

        resp = form.submit('submit')
        assert "Welcome, Adminstrator" not in resp.body
        assert "Login failed" in resp.body

        # and again, this time with correct credentials
        form = resp.forms['login-form']
        assert form['came_from'].value == 'http://localhost/edit'
        form['login'] = 'admin'
        form['password'] = 'secret'
        resp = form.submit('submit').maybe_follow()
        assert "Welcome, Administrator" in resp.body

    @pytest.mark.user('admin')
    def test_content_management(self, webtest):

        from kotti.resources import Document
        from kotti.resources import File
        from kotti_image.resources import Image

        save_addable_document = Document.type_info.addable_to
        save_addable_file = File.type_info.addable_to
        save_addable_image = Image.type_info.addable_to

        app = webtest.app
        resp = app.get('/')

        # Add a document
        resp = resp.click('Document', index=0)
        assert "Add Document to Welcome to Kotti" in resp.body
        form = resp.forms['deform']
        form['title'] = "Child One"
        resp = form.submit('save').maybe_follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/child-one/'

        # Edit the document
        resp = resp.click('Edit')
        assert "Edit Child One" in resp.body
        form = resp.forms['deform']
        form['title'] = "First Child"
        resp = form.submit('save').maybe_follow()
        assert "Your changes have been saved" in resp.body
        resp = resp.click('Edit')
        form = resp.forms['deform']
        assert form['title'].value == "First Child"
        resp = resp.click('Edit')
        assert "First Child" in resp.body

        # And now force a validation error:
        resp = resp.click('Edit')
        form = resp.forms['deform']
        form['title'] = ""
        resp = form.submit('save')
        assert "There was a problem" in resp.body
        assert form['title'].value == ''

        # And now click the 'Cancel' button:
        resp = resp.click('Edit')
        form = resp.forms['deform']
        form['title'] = "Firstborn"
        resp = form.submit('cancel').maybe_follow()
        assert 'deform' not in resp.forms
        assert "Firstborn" not in resp.body

        # Now click the 'Cancel' button for an invalid form entry:
        resp = resp.click('Edit')
        form = resp.forms['deform']
        form['title'] = ""
        resp = form.submit('cancel').maybe_follow()
        assert 'deform' not in resp.forms
        assert "Firstborn" not in resp.body

        # Add two more documents, at different levels
        resp = app.get('/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Second Child"
        resp = form.submit('save').maybe_follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/second-child/'

        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        resp = form.submit('save').maybe_follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/second-child/grandchild/'

        # Add another grandchild with the same name:
        resp = app.get('/second-child/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        resp = form.submit('save').maybe_follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/second-child/grandchild-1/'

        # There's no Add link if nothing can be added:
        resp = app.get('/second-child/grandchild-1/')
        try:
            Document.type_info.addable_to = ()
            File.type_info.addable_to = ()
            Image.type_info.addable_to = ()
            with pytest.raises(IndexError):
                resp.click(href='add_')
        finally:
            Document.type_info.addable_to = save_addable_document
            File.type_info.addable_to = save_addable_file
            Image.type_info.addable_to = save_addable_image

        # Add a file
        resp = app.get('/')
        resp = resp.click('File', index=0)
        form = resp.forms['deform']
        form['description'] = "A tiny file"
        form['upload'] = Upload('tiny.txt', 'tiny', 'text/plain')
        resp = form.submit('save').maybe_follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/tiny.txt/'

        # Add a file larger than maximum file size
        resp = app.get('/')
        resp = resp.click('File', index=0)
        form = resp.forms['deform']
        form['title'] = "Huge file"
        form['description'] = "An uge file"
        form['upload'] = Upload('huge.txt',
                                '*' * (10 * 1024 * 1024 + 1), 'text/plain')
        resp = form.submit('save')
        assert "There was a problem" in resp.body
        assert "Maximum file size" in resp.body

        # Add tags to a document:
        resp = app.get('/second-child/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        form['tags'] = ''
        form.submit('save').maybe_follow()
        resp = app.get('/second-child/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        form['tags'] = 'tag 1, tag 2,tag 3'
        form.submit('save').maybe_follow()
        resp = app.get('/second-child/grandchild-2/@@edit')
        form = resp.forms['deform']
        assert 'tag 1' in resp.body
        assert 'tag 2' in resp.body
        assert 'tag 3' in resp.body
        form['tags'] = 'tag 1, tag 4, tag 5,tag 6, tag 7, übertag'
        form.submit('save').maybe_follow()
        resp = app.get('/second-child/grandchild-2/@@edit')
        assert 'value="tag 1,tag 4,tag 5,tag 6,tag 7,übertag"' in resp.body

        # Delete a document
        resp = app.get('/second-child/grandchild/')
        resp = resp.click('Delete', index=0)
        form = resp.forms['form-delete']
        resp = form.submit('cancel')
        assert "Grandchild was deleted" not in resp.body
        resp = app.get('/second-child/grandchild/')
        resp = resp.click('Delete', index=0)
        form = resp.forms['form-delete']
        resp = form.submit('delete', value='delete').maybe_follow()
        assert "Grandchild was deleted" in resp.body
        assert resp.request.path == '/second-child/'

        # Copy and paste
        resp = app.get('/second-child/')
        resp = resp.click('Cut', index=0).maybe_follow()
        assert "Second Child was cut" in resp.body
        resp = app.get('/child-one/')
        resp = resp.click('Paste', index=0).maybe_follow()
        assert "Second Child was pasted" in resp.body
        app.get('/second-child/', status=404)
        resp = app.get('/child-one/second-child/')
        resp = resp.click('Copy', index=0).maybe_follow()
        assert "Second Child was copied" in resp.body
        resp = app.get('/')
        resp = resp.click('Paste', index=0).maybe_follow()
        assert "Second Child was pasted" in resp.body

        # We can paste twice since we copied:
        resp = app.get('/')
        resp = resp.click('Paste', index=0).maybe_follow()
        assert "Second Child was pasted" in resp.body
        resp = app.get('/second-child/')
        assert "Second Child" in resp.body
        resp = app.get('/second-child-1/')
        assert "Second Child" in resp.body

        # We can also copy and paste items that contain children,
        # like the whole site:
        resp = app.get('/')
        resp = resp.click('Copy', index=0).maybe_follow()
        assert "Welcome to Kotti was copied" in resp.body
        resp = app.get('/second-child/')
        resp = resp.click('Paste', index=0).maybe_follow()
        assert "Welcome to Kotti was pasted" in resp.body
        resp = app.get('/second-child/welcome-to-kotti/')
        assert resp.status_code == 200
        resp = app.get('/second-child/welcome-to-kotti/second-child/')
        assert resp.status_code == 200

        # And finally cut and paste a tree:
        resp = app.get('/second-child/')
        resp.click('Cut', index=0).maybe_follow()
        resp = app.get('/child-one/second-child/')
        resp = resp.click('Paste', index=0).maybe_follow()
        assert "Second Child was pasted" in resp.body
        app.get('/second-child/', status=404)

        # Note how we can't cut and paste an item into itself:
        resp = app.get('/child-one/')
        resp.click('Cut', index=0).maybe_follow()
        with pytest.raises(IndexError):
            resp.click('Paste', index=0).maybe_follow()
        resp = app.get('/child-one/second-child/')
        with pytest.raises(IndexError):
            resp.click('Paste', index=0).maybe_follow()

        # Whether we can paste or not also depends on the
        # ``type_info.addable`` property:
        resp = app.get('/child-one/')
        resp.click('Copy', index=0).maybe_follow()
        resp = app.get('/child-one/second-child/')
        resp.click('Paste', index=0).maybe_follow()
        try:
            Document.type_info.addable_to = ()
            resp = app.get('/child-one/second-child/')
            with pytest.raises(IndexError):
                resp.click('Paste', index=0).maybe_follow()
        finally:
            Document.type_info.addable_to = save_addable_document

        # You can't cut the root of a site:
        resp = app.get('/child-one/')
        resp.click('Cut', index=0)
        resp = app.get('/')
        with pytest.raises(IndexError):
            resp.click('Cut', index=0)

        # We can rename an item. Slashes will be stripped out.:
        resp = app.get('/child-one/second-child/')
        resp = resp.click('Rename', index=0)
        form = resp.forms['form-rename']
        assert form['name'].value == 'second-child'
        assert form['title'].value == 'Second Child'
        form['name'] = 'thi/rd-ch/ild'
        form['title'] = 'My Third Child'
        resp = form.submit('rename').maybe_follow()
        assert "Item was renamed" in resp.body
        assert resp.request.path == '/child-one/third-child/'

        # We cannot rename the root:
        resp = app.get('/')
        with pytest.raises(IndexError):
            resp.click('Rename', index=0)

        # On setup pages we can't use the actions:
        resp = app.get('/')
        resp = resp.click('User Management', index=0)
        with pytest.raises(IndexError):
            resp.click('Copy', index=0)
        resp = resp.click('Preferences', index=0)
        with pytest.raises(IndexError):
            resp.click('Copy', index=0)

        # Contents view actions
        resp = app.get('/child-one')
        resp = resp.click('Contents', index=0)
        assert resp.request.path == '/child-one/@@contents'
        resp = resp.forms['form-contents'].submit('copy').maybe_follow()
        assert 'You have to select items' in resp.body
        form = self._select_children(resp, 0)
        resp = form.submit('copy').maybe_follow()
        assert 'My Third Child was copied.' in resp.body
        resp = app.get('/second-child-1/@@contents')
        assert 'My Third Child' not in resp.body
        resp = resp.forms['form-contents'].submit('paste').maybe_follow()
        assert 'My Third Child' in resp.body
        resp = app.get('/second-child-1/@@contents')
        form = self._select_children(resp, 0)
        resp = form.submit('cut').maybe_follow()
        assert 'cut.' in resp.body
        resp = app.get('/child-one/@@contents')
        assert "Grandchild" not in resp.body
        resp = resp.forms['form-contents'].submit('paste').maybe_follow()
        assert "Grandchild" in resp.body
        with pytest.raises(IndexError):
            resp.click('Paste')
        resp = app.get('/child-one/@@contents')
        form = self._select_children(resp, 0, 1)
        form.submit('cut').maybe_follow()
        resp = app.get('/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = 'Forth child'
        form.submit('save').maybe_follow()
        resp = app.get('/forth-child/@@contents')
        assert "Grandchild" not in resp.body
        assert "My Third Child" not in resp.body
        resp.forms['form-contents'].submit('paste').maybe_follow()
        resp = app.get('/forth-child/@@contents')
        assert "Grandchild" in resp.body
        assert "My Third Child" in resp.body
        resp = app.get('/child-one/@@contents')
        assert "Grandchild" not in resp.body
        resp = app.get('/forth-child/@@contents')
        assert 'third-child' in resp.body
        assert 'Grandchild' in resp.body
        assert 'child-the-third' not in resp.body
        assert 'Hello Bob' not in resp.body
        form = self._select_children(resp, 0, 1)
        resp = form.submit('rename_nodes').maybe_follow()
        resp = resp.forms['form-rename-nodes'].submit('cancel').maybe_follow()
        assert 'No changes were made.' in resp.body
        assert resp.request.path == '/forth-child/@@contents'
        form = self._select_children(resp, 0, 1)
        resp = form.submit('rename_nodes').maybe_follow()
        form = resp.forms['form-rename-nodes']
        form[form.submit_fields()[1][0]] = 'child-the-third'
        form[form.submit_fields()[2][0]] = 'child, the third'
        form[form.submit_fields()[4][0]] = 'hello-bob'
        form[form.submit_fields()[5][0]] = 'Hello Bob'
        resp = form.submit('rename_nodes').maybe_follow()
        assert resp.request.path == '/forth-child/@@contents'
        assert 'third-child' not in resp.body
        assert 'Grandchild' not in resp.body
        assert 'child-the-third' in resp.body
        assert 'Hello Bob' in resp.body

        resp = resp.click('File', index=0)
        form = resp.forms['deform']
        form['description'] = 'A file'
        form['upload'] = Upload('some.txt', 'something', 'text/plain')
        form.submit('save').maybe_follow()
        resp = app.get('/forth-child/@@contents')
        form = self._select_children(resp, 0, 1, 2)
        resp = form.submit('delete_nodes').maybe_follow()
        resp = resp.forms['form-delete-nodes'].submit('cancel').maybe_follow()
        assert 'No changes were made.' in resp.body
        assert resp.request.path == '/forth-child/@@contents'
        form = self._select_children(resp, 0, 1, 2)
        resp = form.submit('delete_nodes').maybe_follow()
        assert "Are you sure" in resp.body
        resp = resp.forms['form-delete-nodes'].submit('delete_nodes',
                                                      status=302).maybe_follow()
        assert "child, the third was deleted." in resp.body
        assert "Hello Bob was deleted." in resp.body
        assert "some.txt was deleted." in resp.body
        resp = app.get('/forth-child/@@contents')
        assert "Welcome to Kotti" in resp.body
        assert '<i class="glyphicon glyphicon-home"></i>' in resp.body
        assert '<i class="glyphicon glyphicon-folder-open"></i>' in resp.body
        assert '<i class="glyphicon glyphicon-folder-close"></i>' not in resp.body  # noqa

        # Contents view change state actions
        resp = resp.click("Second Child")
        resp = resp.click("Contents")
        assert '/second-child-1/third-child/@@workflow-change?new_state=public' in resp.body  # noqa
        resp = app.get('/second-child-1/third-child/@@workflow-change?new_state=public').maybe_follow()  # noqa
        assert '/second-child-1/third-child/@@workflow-change?new_state=private' in resp.body  # noqa
        resp = app.get('/second-child-1/third-child/@@contents')
        form = self._select_children(resp, 0, 1, 2)
        resp = form.submit('change_state').maybe_follow()
        assert 'Change workflow state' in resp.body
        resp = resp.forms['form-change-state'].submit('cancel').maybe_follow()
        assert 'No changes were made.' in resp.body
        assert resp.request.path == '/second-child-1/third-child/@@contents'
        form = self._select_children(resp, 0, 1, 2)
        resp = form.submit('change_state').maybe_follow()
        form = resp.forms['form-change-state']
        form['children-to-change-state'] = []
        resp = form.submit('change_state').maybe_follow()
        assert 'No changes were made.' in resp.body
        form = self._select_children(resp, 0, 1, 2)
        resp = form.submit('change_state').maybe_follow()
        form = resp.forms['form-change-state']
        form['to-state'] = 'public'
        resp = form.submit('change_state').maybe_follow()
        assert 'Your changes have been saved.' in resp.body
        assert '/second-child-1/third-child/grandchild-1/@@workflow-change?new_state=private' in resp.body  # noqa
        assert '/second-child-1/third-child/grandchild-2/@@workflow-change?new_state=private' in resp.body  # noqa
        assert '/second-child-1/third-child/grandchild-3/@@workflow-change?new_state=private' in resp.body  # noqa

        resp = resp.click('My Third Child')
        assert '/second-child-1/third-child/child-one/@@workflow-change?new_state=public' in resp.body  # noqa
        app.get('/second-child-1/third-child/child-one/@@workflow-change?new_state=public')  # noqa
        resp = app.get('/second-child-1/third-child/@@contents')
        assert '/second-child-1/third-child/child-one/@@workflow-change?new_state=private' in resp.body  # noqa
        resp = resp.click('First Child', index=1)
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = 'Sub child'
        resp = form.submit('save').maybe_follow()
        assert '/second-child-1/third-child/child-one/sub-child/@@workflow-change?new_state=public' in resp.body  # noqa
        resp = resp.click("Second Child", index=0)
        resp = resp.click("Contents")
        form = self._select_children(resp, 0, 1, 2)
        resp = form.submit('change_state').maybe_follow()
        form = resp.forms['form-change-state']
        form['include-children'] = 'include-children'
        form['to-state'] = 'public'
        resp = form.submit('change_state').maybe_follow()
        assert 'Your changes have been saved.' in resp.body
        assert '/second-child-1/third-child/@@workflow-change?new_state=private' in resp.body
        resp = app.get('/second-child-1/third-child/child-one/sub-child/')
        assert '/second-child-1/third-child/child-one/sub-child/@@workflow-change?new_state=private' in resp.body

        # Navigation
        resp = resp.click("Navigate")
        resp = resp.click("Second Child", index=0)
        assert resp.request.path == '/second-child-1/'

    def test_user_management(self, webtest, settings, dummy_mailer):
        from kotti import get_settings
        get_settings()['kotti.site_title'] = u'Website des Kottbusser Tors'

        app = webtest.app
        resp = self._login(app, 'admin', 'secret').maybe_follow()

        # The user management screen is available through
        # the "Site Setup" submenu
        resp = resp.click('User Management')

        # Add Bob's Group and assign the ``viewer`` role
        form = resp.forms['deform_group_add']
        form['name'] = 'bobsgroup'
        form['title'] = "Bob's Group"
        form.get('checkbox', index=0).checked = True
        resp = form.submit('add_group').maybe_follow()
        assert "Bob's Group was added" in resp.body
        assert resp.forms['form-global-roles'][
            'role::group:bobsgroup::role:viewer'].value == 'on'

        # And a Bob.
        # Only alphanumeric characters are allowed for the name
        form = resp.forms['deform_user_add']
        form["name"] = "bob:"
        form["title"] = "Bob Dabolina"
        form["password"] = "secret"
        form['password-confirm'] = "secret"
        form["email"] = "bob@DABOLINA.com"
        resp = form.submit("add_user")
        assert "There was a problem" in resp.body

        # Use a valid username now.  Note how the checkbox to send a password
        # registration link is ticked:
        form = resp.forms['deform_user_add']
        form["name"] = "Bob"
        form["email"] = "bob@DABOLINA.com"
        form["send_email"].checked = True
        resp = form.submit("add_user").maybe_follow()
        assert "Bob Dabolina was added" in resp.body

        # We cannot add Bob twice:
        form = resp.forms['deform_user_add']
        form["name"] = "bob"
        form["title"] = "Bobby Brown"
        form["password"] = "secret"
        form["password-confirm"] = "secret"
        resp = form.submit("add_user")
        assert "A user with that name already exists" in resp.body

        # We cannot add Bob Dabolina's email twice:
        form = resp.forms['deform_user_add']
        form["name"] = "bob2"
        form["title"] = "Bobby Brown"
        form["email"] = "bob@dabolina.com"
        form["password"] = "secret"
        form['password-confirm'] = "secret"
        resp = form.submit("add_user")
        assert "A user with that email already exists" in resp.body
        form = resp.forms['deform_user_add']
        form["email"] = "bob@gmail.com"
        resp = form.submit("add_user").maybe_follow()
        assert "Bobby Brown was added" in resp.body

        # Searching for Bob will return both Bob and Bob's Group:
        form = resp.forms['form-principal-search']
        form["query"] = "Bob"
        resp = form.submit("search")
        assert "Bob Dabolina" in resp.body
        assert "Bob's Group" in resp.body
        form = resp.forms['form-global-roles']
        assert form["role::group:bobsgroup::role:viewer"].checked
        assert not form["role::group:bobsgroup::role:editor"].checked
        assert not form["role::bob::role:editor"].checked

        # We can click on the Bob's entry to edit the list of groups
        # he belongs to:
        resp = resp.click("Bob Dabolina")
        form = resp.forms['deform']
        form["group"] = "bobsgroup"
        resp = form.submit("save").maybe_follow()
        assert "Your changes have been saved" in resp.body

        # We cannot update on the Bobby Brown's entry with duplicated email:
        resp = resp.click("Back to User Management")
        form = resp.forms['form-principal-search']
        form["query"] = "Bobby"
        resp = form.submit("search")
        resp = resp.click("Bobby Brown")
        form = resp.forms['deform']
        form["email"] = "bob@dabolina.com"
        resp = form.submit("save")
        assert "A user with that email already exists" in resp.body

        # If we cancel the edit of the user, we are redirected to the
        # user management screen:
        resp = resp.forms['deform'].submit("cancel").maybe_follow()
        assert "No changes were made." in resp.body
        assert resp.request.path == '/@@setup-users'

        # Back in user management we can see how Bob's inherited the
        # viewer role from Bob's Group:
        form = resp.forms['form-principal-search']
        form["query"] = "Bob"
        resp = form.submit("search")
        form = resp.forms['form-global-roles']
        assert form["role::group:bobsgroup::role:viewer"].checked
        assert 'disabled' not in form[
            "role::group:bobsgroup::role:viewer"].attrs
        assert form["role::bob::role:viewer"].checked
        assert 'disabled' in form["role::bob::role:viewer"].attrs

        # We can click on the Bob's Group entry to edit an email address:
        resp = resp.click("Bob's Group")
        form = resp.forms['deform']
        form["email"] = 'bogsgroup@gmail.com'
        resp = form.submit("save").maybe_follow()
        assert "Your changes have been saved" in resp.body

        # Set password
        # ------------

        # Remember that we sent Bob an email for registration.
        # He can use it to set his own password:
        [email, email2] = dummy_mailer.outbox
        assert email.recipients == [u'"Bob Dabolina" <bob@dabolina.com>']
        assert email.subject == "Your registration for Website des " \
                                "Kottbusser Tors"
        assert "Hello, Bob Dabolina!" in email.body
        assert "You are joining Website des Kottbusser Tors." in email.body
        assert "Click here to set your password and log in:" in email.body
        assert "@@set-password?token=" in email.body

        # We'll use that link to set our password:
        resp.click("Logout").maybe_follow()
        path = email.body[email.body.index('http://localhost'):].split()[0][16:]
        resp = app.get(path)
        form = resp.forms['deform']
        form['password'] = "newpassword"
        form['password-confirm'] = "newpasswoops"  # a silly error
        resp = form.submit("submit")
        assert "There was a problem with your submission" in resp.body
        form = resp.forms['deform']
        form['password'] = "newpassword"
        form['password-confirm'] = "newpassword"
        resp = form.submit("submit").maybe_follow()
        assert "You have reset your password" in resp.body

        # We cannot use that link again:
        resp = app.get(path)
        form = resp.forms['deform']
        form['password'] = "won't work"
        form['password-confirm'] = "won't work"
        resp = form.submit("submit")
        assert "Your password reset token may have expired" in resp.body

        # Log in as Bob with the new password:
        resp = self._login(app, 'bOB', 'newpassword').maybe_follow()
        assert "Welcome, Bob Dabolina" in resp.body
        app.get('/@@edit')
        resp = resp.click("Logout").maybe_follow()

        # The login form has a "Reset password" button.  Let's try it:
        resp = self._login(app, "bobby", "")
        assert "Login failed." in resp.body
        form = resp.forms['forgot-password-form']
        form['login'] = "bob"
        resp = form.submit('reset-password').maybe_follow()
        assert "You should be receiving an email" in resp.body
        [email1, email2, email3] = dummy_mailer.outbox
        assert 'Hello, Bob Dabolina!' in email3.body
        assert 'Click this link to reset your password at Website des ' \
               'Kottbusser Tors:' in email3.body

        # User preferences
        # ----------------

        # The "Preferences" link leads us to a form where the user can change
        # their preferences so the user need to be authenticated:
        resp = self._login(app, 'admin', 'secret').maybe_follow()
        assert "Welcome, Administrator" in resp.body
        resp = app.get('/@@prefs')
        form = resp.forms['deform']
        form['title'] = "Mr. Administrator"
        form['email'] = 'admin@minad.com'
        resp = form.submit("save").maybe_follow()
        assert "Your changes have been saved" in resp.body

        # The email could not be used if already a users with that email exists:
        form = resp.forms['deform']
        form['email'] = 'bob@dabolina.com'
        resp = form.submit("save")

        # If the user cancel the process he will be redirected to the site root:
        form = resp.forms['deform']
        resp = form.submit("cancel").maybe_follow()
        assert 'Welcome to Kotti' in resp.body

        # Share
        # -----

        # The Share tab allows us to assign users and groups to roles:
        resp = app.get('/')
        resp = resp.click("Edit")
        resp = resp.click("Share")

        # We can search for users:
        form = resp.forms['form-share-search']
        form['query'] = "Bob"
        resp = form.submit("search")

        # Bob and Bob's Group are listed now:
        assert "Bob Dabolina" in resp.body
        assert "Bob's Group" in resp.body

        # We add Bob's Group to Owners and Editors before taking away Owners
        # again:
        form = resp.forms['form-share-assign']
        form["role::group:bobsgroup::role:owner"].checked = True
        form["role::group:bobsgroup::role:editor"].checked = True
        resp = form.submit("apply").maybe_follow()
        assert "Your changes have been saved" in resp.body
        resp = app.get(resp.request.path)  # >>> browser.reload()
        form = resp.forms['form-share-assign']
        assert form["role::group:bobsgroup::role:owner"].checked
        assert form["role::group:bobsgroup::role:editor"].checked
        form["role::group:bobsgroup::role:owner"].checked = False
        resp = form.submit("apply").maybe_follow()
        assert "Your changes have been saved" in resp.body
        form = resp.forms['form-share-assign']
        assert not form["role::group:bobsgroup::role:owner"].checked

        # Not making any changes will give us a different feedback message:
        resp = form.submit("apply")
        assert "Your changes have been saved" not in resp.body
        form = resp.forms['form-share-assign']
        assert not form["role::group:bobsgroup::role:owner"].checked
        assert form["role::group:bobsgroup::role:editor"].checked

        # Bob should now have an inherited Editor role, because he's part of
        # Bob's Group:
        form = resp.forms['form-share-search']
        form["query"] = "Bob Dabolina"
        resp = form.submit("search")
        form = resp.forms['form-share-assign']
        assert form["role::bob::role:editor"].checked
        # TODO assert 'disabled' in form["role::bob::role:editor"].attrs
        # TODO assert not form["role::bob::role:owner"].checked

        # Lastly, let's take away the remaining Editor role from Bob's Group
        # again:
        assert "Bob's Group" in resp.body
        form["role::group:bobsgroup::role:editor"].checked = None
        resp = form.submit("apply").maybe_follow()
        assert "Your changes have been saved" in resp.body
        # TODO assert "Bob's Group" not in resp.body
        form = resp.forms['form-share-assign']
        assert not form["role::group:bobsgroup::role:editor"].checked

        # Delete users
        # ------------

        resp = app.get('/')
        resp = resp.click("User Management")

        # We add a group and assign the ``Manager`` role to one:
        form = resp.forms['deform_group_add']
        form['name'] = "pelayogroup"
        form['title'] = "Pelayo Group"
        form.get('checkbox', index=3).checked = True
        resp = form.submit("add_group").maybe_follow()
        assert "Pelayo Group was added" in resp.body
        form = resp.forms['form-global-roles']
        assert form["role::group:pelayogroup::role:admin"].checked

        # And add some users to this group.
        form = resp.forms['deform_user_add']
        form['name'] = "Bruce"
        form['title'] = "Bruce Pelayo"
        form['password'] = "secret"
        form['password-confirm'] = "secret"
        form['email'] = "bruce@pelayno.com"
        form["group"] = "pelayogroup"
        resp = form.submit("add_user").maybe_follow()
        assert "Bruce Pelayo was added" in resp.body

        form = resp.forms['deform_user_add']
        form['name'] = "Brian"
        form['title'] = "Brian Pelayo"
        form['password'] = "secret"
        form['password-confirm'] = "secret"
        form['email'] = "brian@pelayno.com"
        form["group"] = "pelayogroup"
        resp = form.submit("add_user").maybe_follow()
        assert "Brian Pelayo was added" in resp.body

        # Lets login as Bruce and add some content:
        resp.click("Logout").maybe_follow()
        resp = self._login(app, 'bruce', 'secret').maybe_follow()
        assert "Welcome, Bruce Pelayo!" in resp.body
        resp = resp.click("Document", index=0)
        form = resp.forms['deform']
        form["title"] = "Bruce one"
        form.submit("save").maybe_follow()
        resp = app.get('/')
        resp = resp.click("Document", index=0)
        form = resp.forms['deform']
        form["title"] = "Bruce two"
        form.submit("save").maybe_follow()

        # Now let's delete Bruce::
        resp.click('Logout').maybe_follow()
        resp = self._login(app, 'admin', 'secret').maybe_follow()
        resp = resp.click("User Management")
        form = resp.forms['form-principal-search']
        form["query"] = "Bruce"
        resp = form.submit("search").maybe_follow()
        resp = resp.click("Bruce Pelayo")
        resp = resp.forms['deform'].submit('delete').maybe_follow()
        assert "Delete <em>Bruce Pelayo</em>" in resp.body
        assert "Are you sure you want to delete <span>User</span> " \
               "<em>Bruce Pelayo</em>?" in resp.body
        resp = resp.forms['form-delete-user'].submit('delete').maybe_follow()
        assert "User Bruce Pelayo was deleted." in resp.body
        form = resp.forms['form-principal-search']
        form["query"] = "Bruce"
        resp = form.submit("search").maybe_follow()
        assert "No users or groups were found." in resp.body
