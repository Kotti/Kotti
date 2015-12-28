# coding:utf8

from StringIO import StringIO
from mock import patch

import pytest
from webtest.forms import Upload

from kotti.testing import BASE_URL
from kotti.testing import user


class TestLogin:
    def test_it(self, app):
        res = app.post(
            '/@@login', dict(login='admin', password='secret', submit='submit'))
        assert res.status == '302 Found'
        res = res.follow()
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
        file_ctrl = browser.getControl("File").mech_control
        file_ctrl.add_file(StringIO(contents), filename='my_image.gif')
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
        file_ctrl = browser.getControl("File").mech_control
        file_ctrl.add_file(StringIO("abc"), filename='my_image.gif')
        browser.getControl('save').click()
        assert "Item was added" in browser.contents

    @user('admin')
    def test_title_max_length_file_ko(self, browser):
        browser.open(BASE_URL + '/@@add_file')
        from kotti.resources import Node
        max_length = Node.name.property.columns[0].type.length
        browser.getControl("Title").value = '1' * (max_length + 1)  # the error
        file_ctrl = browser.getControl("File").mech_control
        file_ctrl.add_file(StringIO("abc"), filename='my_image.gif')
        browser.getControl('save').click()
        assert "Item was added" not in browser.contents


class TestBrowser:
    """ This is a one to one conversion of the former browsert.txt.
    These tests should definitively be rewritten and splitted into multiple
    methods to ease readability.
    """

    def test_login(self, webtest):

        # get the frontpage
        resp = webtest.app.get('/')
        assert "You have successfully installed Kotti." in resp.body

        # access a protected URL
        resp = webtest.app.get('/edit', status=302).follow()
        assert "Log in" in resp.body

        # submit the login form
        form = resp.forms['login-form']
        assert form['came_from'].value == 'http://localhost/edit'
        form['login'] = 'admin'
        form['password'] = 'secret'

        resp = form.submit('submit', status=302).follow()
        assert "Welcome, Administrator" in resp.body

        # log out
        resp = resp.click('Logout').follow().follow()
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
        resp = form.submit('submit', status=302).follow()
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
        resp = form.submit('save', status=302).follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/child-one/'

        # Edit the document
        resp = resp.click('Edit')
        assert "Edit Child One" in resp.body
        form = resp.forms['deform']
        form['title'] = "First Child"
        resp = form.submit('save', status=302).follow()
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
        resp = form.submit('cancel', status=302).follow()
        assert 'deform' not in resp.forms
        assert "Firstborn" not in resp.body

        # Now click the 'Cancel' button for an invalid form entry:
        resp = resp.click('Edit')
        form = resp.forms['deform']
        form['title'] = ""
        resp = form.submit('cancel', status=302).follow()
        assert 'deform' not in resp.forms
        assert "Firstborn" not in resp.body

        # Add two more documents, at different levels
        resp = app.get('/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Second Child"
        resp = form.submit('save', status=302).follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/second-child/'

        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        resp = form.submit('save', status=302).follow()
        assert "Item was added" in resp.body
        assert resp.request.path == '/second-child/grandchild/'

        # Add another grandchild with the same name:
        resp = app.get('/second-child/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        resp = form.submit('save', status=302).follow()
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
        resp = form.submit('save', status=302).follow()
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
        form.submit('save', status=302).follow()
        resp = app.get('/second-child/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = "Grandchild"
        form['tags'] = 'tag 1, tag 2,tag 3'
        form.submit('save', status=302).follow()
        resp = app.get('/second-child/grandchild-2/@@edit')
        form = resp.forms['deform']
        assert 'tag 1' in resp.body
        assert 'tag 2' in resp.body
        assert 'tag 3' in resp.body
        form['tags'] = 'tag 1, tag 4, tag 5,tag 6, tag 7, übertag'
        form.submit('save', status=302).follow()
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
        resp = form.submit('delete', value='delete', status=302).follow()
        assert "Grandchild was deleted" in resp.body
        assert resp.request.path == '/second-child/'

        # Copy and paste
        resp = app.get('/second-child/')
        resp = resp.click('Cut', index=0).follow()
        assert "Second Child was cut" in resp.body
        resp = app.get('/child-one/')
        resp = resp.click('Paste', index=0).follow()
        assert "Second Child was pasted" in resp.body
        app.get('/second-child/', status=404)
        resp = app.get('/child-one/second-child/')
        resp = resp.click('Copy', index=0).follow()
        assert "Second Child was copied" in resp.body
        resp = app.get('/')
        resp = resp.click('Paste', index=0).follow()
        assert "Second Child was pasted" in resp.body

        # We can paste twice since we copied:
        resp = app.get('/')
        resp = resp.click('Paste', index=0).follow()
        assert "Second Child was pasted" in resp.body
        resp = app.get('/second-child/')
        assert "Second Child" in resp.body
        resp = app.get('/second-child-1/')
        assert "Second Child" in resp.body

        # We can also copy and paste items that contain children,
        # like the whole site:
        resp = app.get('/')
        resp = resp.click('Copy', index=0).follow()
        assert "Welcome to Kotti was copied" in resp.body
        resp = app.get('/second-child/')
        resp = resp.click('Paste', index=0).follow()
        assert "Welcome to Kotti was pasted" in resp.body
        resp = app.get('/second-child/welcome-to-kotti/')
        assert resp.status_code == 200
        resp = app.get('/second-child/welcome-to-kotti/second-child/')
        assert resp.status_code == 200

        # And finally cut and paste a tree:
        resp = app.get('/second-child/')
        resp.click('Cut', index=0).follow()
        resp = app.get('/child-one/second-child/')
        resp = resp.click('Paste', index=0).follow()
        assert "Second Child was pasted" in resp.body
        app.get('/second-child/', status=404)

        # Note how we can't cut and paste an item into itself:
        resp = app.get('/child-one/')
        resp.click('Cut', index=0).follow()
        with pytest.raises(IndexError):
            resp.click('Paste', index=0).follow()
        resp = app.get('/child-one/second-child/')
        with pytest.raises(IndexError):
            resp.click('Paste', index=0).follow()

        # Whether we can paste or not also depends on the
        # ``type_info.addable`` property:
        resp = app.get('/child-one/')
        resp.click('Copy', index=0).follow()
        resp = app.get('/child-one/second-child/')
        resp.click('Paste', index=0).follow()
        try:
            Document.type_info.addable_to = ()
            resp = app.get('/child-one/second-child/')
            with pytest.raises(IndexError):
                resp.click('Paste', index=0).follow()
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
        resp = form.submit('rename', status=302).follow()
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
        resp = resp.forms['form-contents'].submit('copy', status=302).follow()
        assert 'You have to select items' in resp.body
        form = resp.forms['form-contents']
        form['children'] = ['3', ]
        resp = resp.forms['form-contents'].submit('copy', status=302).follow()
        resp = resp.follow()
        assert 'My Third Child was copied.' in resp.body
        resp = app.get('/second-child-1/@@contents')
        assert 'My Third Child' not in resp.body
        resp = resp.forms['form-contents'].submit('paste', status=302).follow()
        resp = resp.follow()
        assert 'My Third Child' in resp.body
        resp = app.get('/second-child-1/@@contents')
        form = resp.forms['form-contents']
        form['children'] = ['15', ]
        resp = form.submit('cut', status=302).follow().follow()
        assert 'cut.' in resp.body
        resp = app.get('/child-one/@@contents')
        assert "Grandchild" not in resp.body
        resp = resp.forms['form-contents'].submit('paste', status=302).follow()
        resp = resp.follow()
        assert "Grandchild" in resp.body
        with pytest.raises(IndexError):
            resp.click('Paste')
        resp = app.get('/child-one/@@contents')
        form = resp.forms['form-contents']
        form['children'] = ['3', '15', ]
        form.submit('cut', status=302).follow().follow()
        resp = app.get('/')
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = 'Forth child'
        form.submit('save', status=302).follow()
        resp = app.get('/forth-child/@@contents')
        assert "Grandchild" not in resp.body
        assert "My Third Child" not in resp.body
        resp = resp.forms['form-contents'].submit('paste', status=302).follow()
        resp.follow()
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
        form = resp.forms['form-contents']
        form['children'] = ['3', '15', ]
        resp = form.submit('rename_nodes', status=302).follow()
        resp = resp.forms['form-rename-nodes'].submit('cancel', status=302)
        resp = resp.follow()
        assert 'No changes were made.' in resp.body
        assert resp.request.path == '/forth-child/@@contents'
        form = resp.forms['form-contents']
        form['children'] = ['3', '15', ]
        resp = form.submit('rename_nodes', status=302).follow()
        form = resp.forms['form-rename-nodes']
        form['3-name'] = 'child-the-third'
        form['3-title'] = 'child, the third'
        form['15-name'] = 'hello-bob'
        form['15-title'] = 'Hello Bob'
        resp = form.submit('rename_nodes', status=302).follow()
        assert resp.request.path == '/forth-child/@@contents'
        assert 'third-child' not in resp.body
        assert 'Grandchild' not in resp.body
        assert 'child-the-third' in resp.body
        assert 'Hello Bob' in resp.body

        resp = resp.click('File', index=0)
        form = resp.forms['deform']
        form['description'] = 'A file'
        form['upload'] = Upload('some.txt', 'something', 'text/plain')
        form.submit('save', status=302).follow()
        resp = app.get('/forth-child/@@contents')
        form = resp.forms['form-contents']
        form['children'] = ['3', '15', '104', ]
        resp = form.submit('delete_nodes', status=302).follow()
        resp = resp.forms['form-delete-nodes'].submit('cancel', status=302)
        resp = resp.follow()
        assert 'No changes were made.' in resp.body
        assert resp.request.path == '/forth-child/@@contents'
        form = resp.forms['form-contents']
        form['children'] = ['3', '15', '104', ]
        resp = form.submit('delete_nodes', status=302).follow()
        assert "Are you sure" in resp.body
        resp = resp.forms['form-delete-nodes'].submit('delete_nodes',
                                                      status=302).follow()
        assert "child, the third was deleted." in resp.body
        assert "Hello Bob was deleted." in resp.body
        assert "some.txt was deleted." in resp.body
        resp = app.get('/forth-child/@@contents')
        assert "Welcome to Kotti" in resp.body
        assert '<i class="glyphicon glyphicon-home"></i>' in resp.body
        assert '<i class="glyphicon glyphicon-folder-open"></i>' in resp.body
        assert '<i class="glyphicon glyphicon-folder-close"></i>' \
               not in resp.body

        # Contents view change state actions
        resp = resp.click("Second Child")
        resp = resp.click("Contents")
        assert '/second-child-1/third-child/@@workflow-change' \
               '?new_state=public' in resp.body
        resp = resp.click(href='/second-child-1/third-child/@@workflow-change'
                               '\?new_state=public').follow()
        assert '/second-child-1/third-child/@@workflow-change' \
               '?new_state=private' in resp.body
        resp = app.get('/second-child-1/third-child/@@contents')
        form = resp.forms['form-contents']
        form['children'] = ['58', '57', '2', ]
        resp = form.submit('change_state', status=302).follow()
        assert 'Change workflow state' in resp.body
        resp = resp.forms['form-change-state'].submit('cancel', status=302)
        resp = resp.follow()
        assert 'No changes were made.' in resp.body
        assert resp.request.path == '/second-child-1/third-child/@@contents'
        form = resp.forms['form-contents']
        form['children'] = ['58', '57', '2', ]
        resp = form.submit('change_state', status=302).follow()
        form = resp.forms['form-change-state']
        form['children-to-change-state'] = []
        resp = form.submit('change_state', status=302).follow()
        assert 'No changes were made.' in resp.body
        form = resp.forms['form-contents']
        form['children'] = ['58', '57', '2', ]
        resp = form.submit('change_state', status=302).follow()
        form = resp.forms['form-change-state']
        form['to-state'] = 'public'
        resp = form.submit('change_state', status=302).follow()
        assert 'Your changes have been saved.' in resp.body
        assert '/second-child-1/third-child/grandchild-1/@@workflow-change' \
               '?new_state=private' in resp.body
        assert '/second-child-1/third-child/grandchild-2/@@workflow-change' \
               '?new_state=private' in resp.body
        assert '/second-child-1/third-child/grandchild-3/@@workflow-change' \
               '?new_state=public' in resp.body

        resp = resp.click('My Third Child')
        assert '/second-child-1/third-child/child-one/@@workflow-change' \
               '?new_state=public' in resp.body
        resp = app.get('/second-child-1/third-child/child-one/@@workflow-change?new_state=public')
        resp = app.get('/second-child-1/third-child/@@contents')
        assert '/second-child-1/third-child/child-one/@@workflow-change' \
               '?new_state=private' in resp.body

        resp = resp.click('First Child', index=1)
        resp = resp.click('Document', index=0)
        form = resp.forms['deform']
        form['title'] = 'Sub child'
        resp = form.submit('save', status=302).follow()
        assert '/second-child-1/third-child/child-one/sub-child/' \
               '@@workflow-change?new_state=public' in resp.body

        resp = resp.click("Second Child", index=0)
        resp = resp.click("Contents")
        form = resp.forms['form-contents']
        form['children'] = ['14', '16', '56', ]
        resp = form.submit('change_state', status=302).follow()
        form = resp.forms['form-change-state']
        form['include-children'] = 'include-children'
        form['to-state'] = 'public'
        resp = form.submit('change_state', status=302).follow()
        assert 'Your changes have been saved.' in resp.body
        assert '/second-child-1/third-child/@@workflow-change' \
               '?new_state=private' in resp.body
        resp = app.get('/second-child-1/third-child/child-one/sub-child/')
        assert '/second-child-1/third-child/child-one/sub-child/' \
               '@@workflow-change?new_state=private' in resp.body

        # Navigation
        resp = resp.click("Navigate")
        resp = resp.click("Second Child", index=0)
        assert resp.request.path == '/second-child-1/'


"""
User management
---------------
The user management screen is available through the "Site Setup" submenu:

  >>> browser.getLink("User Management").click()

We add Bob's Group and assign the ``Viewer`` role:

  >>> ctrl("Name", index=1).value = "bobsgroup"
  >>> ctrl("Title", index=1).value = "Bob's Group"
  >>> ctrl("Viewer", index=1).click()
  >>> ctrl(name="add_group").click()
  >>> "Bob's Group was added" in browser.contents
  True
  >>> ctrl(name="role::group:bobsgroup::role:viewer").value
  True

And a Bob.  Only alphanumeric characters are allowed for the name:

  >>> ctrl("Name", index=0).value = "bob:"
  >>> ctrl("Full name", index=0).value = "Bob Dabolina"
  >>> ctrl("Password", index=0).value = "secret"
  >>> ctrl(name='password-confirm').value = "secret"
  >>> ctrl("Email", index=0).value = "bob@DABOLINA.com"
  >>> ctrl(name="add_user").click()
  >>> "There was a problem" in browser.contents
  True

Use a valid username now.  Note how the checkbox to send a password
registration link is ticked:

  >>> ctrl("Name", index=0).value = u"Bob"
  >>> ctrl("Email", index=0).value = "bob@dabolina.com"
  >>> ctrl("Send password registration link", index=0).selected
  True
  >>> ctrl(name="add_user").click()
  >>> "Bob Dabolina was added" in browser.contents
  True

We cannot add Bob twice:

  >>> ctrl("Name", index=0).value = "bob"
  >>> ctrl("Full name", index=0).value = "Bobby Brown"
  >>> ctrl("Password", index=0).value = "secret"
  >>> ctrl(name='password-confirm').value = "secret"
  >>> ctrl(name="add_user").click()
  >>> "A user with that name already exists" in browser.contents
  True

We cannot add Bob Dabolina's email twice:

  >>> ctrl("Name", index=0).value = "bob2"
  >>> ctrl("Full name", index=0).value = "Bobby Brown"
  >>> ctrl("Email", index=0).value = "bob@dabolina.com"
  >>> ctrl("Password", index=0).value = "secret"
  >>> ctrl(name='password-confirm').value = "secret"
  >>> ctrl(name="add_user").click()
  >>> "A user with that email already exists" in browser.contents
  True
  >>> ctrl("Email", index=0).value = "bob@gmail.com"
  >>> ctrl(name="add_user").click()
  >>> "Bobby Brown was added" in browser.contents
  True

Searching for Bob will return both Bob and Bob's Group:

  >>> ctrl(name="query").value = "Bob"
  >>> ctrl(name="search").click()
  >>> "Bob Dabolina" in browser.contents
  True
  >>> "Bob's Group" in browser.contents
  True
  >>> ctrl(name="role::group:bobsgroup::role:viewer").value
  True
  >>> ctrl(name="role::group:bobsgroup::role:editor").value
  False
  >>> ctrl(name="role::bob::role:editor").value
  False

We can click on the Bob's entry to edit the list of groups he belongs
to:

  >>> browser.getLink("Bob Dabolina").click()
  >>> ctrl(name="group").value = "bobsgroup"
  >>> ctrl(name="save").click()
  >>> "Your changes have been saved" in browser.contents
  True

We cannot update on the Bobby Brown's entry with duplicated email:

  >>> browser.getLink("Back to User Management").click()
  >>> ctrl(name="query").value = "Bobby"
  >>> ctrl(name="search").click()
  >>> browser.getLink("Bobby Brown").click()
  >>> ctrl("Email", index=0).value = "bob@dabolina.com"
  >>> ctrl(name="save").click()
  >>> "A user with that email already exists" in browser.contents
  True

If we cancel the edit of the user, we are redirected to the user management
screen:

  >>> ctrl(name="cancel").click()
  >>> "No changes were made." in browser.contents
  True
  >>> browser.url
  'http://localhost:6543/@@setup-users'


Back in user management we can see how Bob's inherited the Viewer role
from Bob's Group:

  >>> ctrl(name="query").value = "Bob"
  >>> ctrl(name="search").click()
  >>> ctrl(name="role::group:bobsgroup::role:viewer").value
  True
  >>> ctrl(name="role::group:bobsgroup::role:viewer").disabled
  False
  >>> ctrl(name="role::bob::role:viewer").value
  True
  >>> ctrl(name="role::bob::role:viewer").disabled
  True

We can click on the Bob's Group entry to edit an email address:

  >>> browser.getLink("Bob's Group").click()
  >>> ctrl(name="email").value = 'bogsgroup@gmail.com'
  >>> ctrl(name="save").click()
  >>> "Your changes have been saved" in browser.contents
  True

Set password
------------

Remember that we sent Bob an email for registration.  He can use it to
set his own password:

  >>> [email, email2] = mailer.outbox
  >>> print email.recipients
  [u'"Bob Dabolina" <bob@dabolina.com>']
  >>> print email.subject
  Your registration for Website des Kottbusser Tors
  >>> print email.body # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  Hello, Bob Dabolina!
  You are joining Website des Kottbusser Tors.
  Click here to set your password and log in:
  http://localhost:6543/@@set-password?token=...

We'll use that link to set our password:

  >>> browser.getLink("Logout").click()
  >>> link = email.body[email.body.index('http://localhost'):].split()[0]
  >>> browser.open(link)
  >>> ctrl("Password", index=0).value = "newpassword"
  >>> ctrl(name='password-confirm').value = "newpasswoops" # a silly error
  >>> ctrl(name="submit").click()
  >>> "There was a problem with your submission" in browser.contents
  True
  >>> ctrl("Password", index=0).value = "newpassword"
  >>> ctrl(name='password-confirm').value = "newpassword"
  >>> ctrl(name="submit").click()
  >>> "You have reset your password" in browser.contents
  True
  >>> browser.getLink("Logout").click()

We cannot use that link again:

  >>> browser.open(link)
  >>> ctrl("Password", index=0).value = "wontwork"
  >>> ctrl(name='password-confirm').value = "wontwork"
  >>> ctrl(name="submit").click()
  >>> "Your password reset token may have expired" in browser.contents
  True

Log in as Bob with the new password:

  >>> browser.open(testing.BASE_URL + '/@@edit')
  >>> ctrl("Username or email", index=0).value = "bOB"
  >>> ctrl("Password").value = "newpassword"
  >>> ctrl(name="submit").click()
  >>> "Welcome, Bob Dabolina" in browser.contents
  True
  >>> browser.open(testing.BASE_URL + '/@@edit')
  >>> browser.getLink("Logout").click()

The login form has a "Reset password" button.  Let's try it:

  >>> browser.open(testing.BASE_URL + '/@@edit')
  >>> ctrl("Username or email", index=1).value = "bobby" # silly error
  >>> ctrl("Password").value = ""
  >>> ctrl(name="reset-password").click()
  >>> "That username or email is not known by this system" in browser.contents
  True
  >>> ctrl("Username or email", index=1).value = "bob"
  >>> ctrl(name="reset-password").click()
  >>> "You should be receiving an email" in browser.contents
  True

  >>> [email1, email2, email3] = mailer.outbox
  >>> print email3.body # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  Hello, Bob Dabolina!
  <BLANKLINE>
  Click this link to reset your password at Website des Kottbusser Tors:...

User preferences
----------------

The "Preferences" link leads us to a form where the user can change
their preferences so the user need to be authenticated:

  >>> browser.open(testing.BASE_URL + '/@@prefs')
  >>> ctrl("Username or email", index=0).value = "admin"
  >>> ctrl("Password").value = "secret"
  >>> ctrl(name="submit").click()
  >>> "Welcome, Administrator" in browser.contents
  True

  >>> ctrl("Full name").value = "Mr. Administrator"
  >>> ctrl("Email").value = 'admin@minad.com'
  >>> ctrl(name="save").click()
  >>> "Your changes have been saved" in browser.contents
  True

The email could not be used if already a users with that email exists:

  >>> ctrl("Email").value = 'bob@dabolina.com'
  >>> ctrl(name="save").click()
  >>> "A user with that email already exists" in browser.contents
  True


If the user cancel the process he will be redirected to the site root:

  >>> ctrl(name="cancel").click()
  >>> 'Welcome to Kotti' in browser.contents
  True


Share
-----

The Share tab allows us to assign users and groups to roles:

  >>> browser.open(testing.BASE_URL)
  >>> browser.getLink("Edit").click()
  >>> browser.getLink("Share").click()

We can search for users:

  >>> ctrl(name='query').value = "Bob"
  >>> ctrl(name="search").click()

Bob and Bob's Group are listed now:

  >>> "Bob Dabolina" in browser.contents
  True
  >>> "Bob's Group" in browser.contents
  True

We add Bob's Group to Owners and Editors before taking away Owners
again:

  >>> ctrl(name="role::group:bobsgroup::role:owner").value = True
  >>> ctrl(name="role::group:bobsgroup::role:editor").value = True
  >>> ctrl(name="apply").click()
  >>> "Your changes have been saved" in browser.contents
  True
  >>> browser.reload()
  >>> ctrl(name="role::group:bobsgroup::role:owner").value
  True
  >>> ctrl(name="role::group:bobsgroup::role:editor").value
  True
  >>> ctrl(name="role::group:bobsgroup::role:owner").value = False
  >>> ctrl(name="apply").click()
  >>> "Your changes have been saved" in browser.contents
  True
  >>> ctrl(name="role::group:bobsgroup::role:owner").value
  False

Not making any changes will give us a different feedback message:

  >>> ctrl(name="apply").click()
  >>> "Your changes have been saved" in browser.contents
  False
  >>> ctrl(name="role::group:bobsgroup::role:owner").value
  False
  >>> ctrl(name="role::group:bobsgroup::role:editor").value
  True

Bob should now have an inherited Editor role, because he's part of
Bob's Group:

  >>> ctrl(name="query").value = "Bob Dabolina"
  >>> ctrl(name="search").click()
  >>> ctrl(name="role::bob::role:editor").value
  True
  >>> ctrl(name="role::bob::role:owner").value
  False
  >>> ctrl(name="role::bob::role:editor").disabled
  True

Lastly, let's take away the remaining Editor role from Bob's Group
again:

  >>> "Bob's Group" in browser.contents
  True
  >>> ctrl(name="role::group:bobsgroup::role:editor").value = False
  >>> ctrl(name="apply").click()
  >>> "Your changes have been saved" in browser.contents
  True
  >>> "Bob's Group" in browser.contents
  False


Delete users
------------

  >>> browser.getLink("User Management").click()

We add a group and assign the ``Manager`` role to one:

  >>> ctrl("Name", index=1).value = "pelayogroup"
  >>> ctrl("Title", index=1).value = "Pelayo Group"
  >>> ctrl("Admin", index=1).click()
  >>> ctrl(name="add_group").click()
  >>> "Pelayo Group was added" in browser.contents
  True
  >>> ctrl(name="role::group:pelayogroup::role:admin").value
  True

And add some users to this group.

  >>> ctrl("Name", index=0).value = "Bruce"
  >>> ctrl("Full name", index=0).value = "Bruce Pelayo"
  >>> ctrl("Password", index=0).value = "secret"
  >>> ctrl(name='password-confirm').value = "secret"
  >>> ctrl("Email", index=0).value = "bruce@pelayno.com"
  >>> ctrl(name="group", index=0).value = "pelayogroup"
  >>> ctrl(name="add_user").click()
  >>> "Bruce Pelayo was added" in browser.contents
  True

  >>> ctrl("Name", index=0).value = "Brian"
  >>> ctrl("Full name", index=0).value = "Brian Pelayo"
  >>> ctrl("Password", index=0).value = "secret"
  >>> ctrl(name='password-confirm').value = "secret"
  >>> ctrl("Email", index=0).value = "brian@pelayno.com"
  >>> ctrl(name="group", index=0).value = "pelayogroup"
  >>> ctrl(name="add_user").click()
  >>> "Brian Pelayo was added" in browser.contents
  True

Lets login as Bruce and add some content:

  >>> browser.getLink("Logout").click()
  >>> browser.open(testing.BASE_URL + '/login')
  >>> ctrl("Username or email", index=0).value = "bruce"
  >>> ctrl("Password").value = "secret"
  >>> ctrl(name="submit").click()
  >>> "Welcome, Bruce Pelayo!" in browser.contents
  True

  >>> browser.getLink("Document").click()
  >>> ctrl("Title").value = "Bruce one"
  >>> ctrl("save").click()
  >>> browser.open(testing.BASE_URL)
  >>> browser.getLink("Document").click()
  >>> ctrl("Title").value = "Bruce two"
  >>> ctrl("save").click()

Now let's delete Bruce::

  >>> browser.getLink("Logout").click()
  >>> browser.open(testing.BASE_URL + '/login')
  >>> ctrl("Username or email", index=0).value = "admin"
  >>> ctrl("Password").value = "secret"
  >>> ctrl(name="submit").click()

  >>> browser.getLink("User Management").click()
  >>> ctrl(name="query").value = "Bruce"
  >>> ctrl(name="search").click()
  >>> browser.getLink("Bruce Pelayo").click()
  >>> ctrl(name='delete').click()

  >>> "Delete <em>Bruce Pelayo</em>" in browser.contents
  True
  >>> "Are you sure you want to delete <span>User</span> <em>Bruce Pelayo</em>?" in browser.contents
  True

  >>> ctrl(name='delete').click()
  >>> "User Bruce Pelayo was deleted." in browser.contents
  True

  >>> ctrl(name="query").value = "Bruce"
  >>> ctrl(name="search").click()
  >>> "No users or groups were found." in browser.contents
  True

TearDown
--------

  >>> testing.tearDown()
"""
