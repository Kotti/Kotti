from StringIO import StringIO
from mock import patch
from kotti.testing import FunctionalTestBase


class TestLogin:
    def test_it(self, app):
        res = app.post('/@@login', dict(login='admin',
                password='secret', submit='submit'))
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
        with patch('kotti.views.login.authenticated_userid', return_value='foo'):
            res = app.get('/@@edit', status=302)
        assert res.location == 'http://localhost/@@forbidden'


class TestUploadFile(FunctionalTestBase):
    def add_file(self, browser, contents='ABC'):
        file_ctrl = browser.getControl("File").mech_control
        file_ctrl.add_file(StringIO(contents), filename='my_image.gif')
        browser.getControl('save').click()

    def get_browser(self):
        browser = self.Browser()
        browser.open(self.BASE_URL + '/edit')
        browser.getControl("Username or email").value = 'admin'
        browser.getControl("Password").value = 'secret'
        browser.getControl(name="submit").click()
        browser.open(self.BASE_URL + '/@@add_file')
        return browser

    def test_it(self):
        browser = self.get_browser()
        self.add_file(browser)
        assert "Successfully added item" in browser.contents
        return browser

    def test_view_uploaded_file(self):
        browser = self.get_browser()
        self.add_file(browser)
        browser.getLink("View").click()
        browser.getLink("Download file").click()
        assert browser.contents == 'ABC'

    def test_tempstorage(self):
        browser = self.get_browser()
        self.add_file(browser)
        browser.getLink("Edit").click()
        browser.getControl("Title").value = ''  # the error
        self.add_file(browser, contents='DEF')
        assert "Your changes have been saved" not in browser.contents
        browser.getControl("Title").value = 'A title'
        browser.getControl('save').click()
        assert "Your changes have been saved" in browser.contents
        browser.getLink("View").click()
        browser.getLink("Download file").click()
        assert browser.contents == 'DEF'
