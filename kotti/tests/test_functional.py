from StringIO import StringIO
from mock import patch

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
