from StringIO import StringIO

from mock import patch

from kotti.testing import FunctionalTestBase

class TestLogin(FunctionalTestBase):
    def test_it(self):
        res = self.login()
        assert res.status == '302 Found'
        res = res.follow()
        assert res.status == '200 OK'

class TestForbidden(FunctionalTestBase):
    def test_forbidden(self):
        self.test_app.get(
            '/@@edit', headers={'Accept': '*/json'}, status=403)

    def test_forbidden_redirect(self):
        res = self.test_app.get(
            '/@@edit', headers={'Accept': 'text/html'}, status=302)
        assert res.location.startswith('http://localhost/@@login?came_from=')

    @patch('kotti.views.login.authenticated_userid')
    def test_forbidden_redirect_when_authenticated(self, userid):
        userid.return_value = "foo"
        res = self.test_app.get('/@@edit', status=302)
        assert res.location == 'http://localhost/@@forbidden'

class TestUploadFile(FunctionalTestBase):
    def add_file(self, browser, contents='ABC'):
        file_ctrl = browser.getControl("File").mech_control
        file_ctrl.add_file(StringIO(contents), filename='my_image.gif')

    def test_it(self):
        browser = self.login_testbrowser()
        browser.open(self.BASE_URL + '/@@add_file')
        self.add_file(browser)
        browser.getControl('save').click()
        assert "Successfully added item" in browser.contents
        return browser

    def test_view_uploaded_file(self):
        browser = self.test_it()
        browser.getLink("View").click()
        browser.getLink("Download file").click()
        assert browser.contents == 'ABC'

    def test_tempstorage(self):
        browser = self.test_it()
        browser.getControl("Title").value = '' # the error
        self.add_file(browser, contents='DEF')
        browser.getControl('save').click()
        assert "Your changes have been saved" not in browser.contents
        browser.getControl("Title").value = 'A title'
        browser.getControl('save').click()
        assert "Your changes have been saved" in browser.contents
        browser.getLink("View").click()
        browser.getLink("Download file").click()
        assert browser.contents == 'DEF'
