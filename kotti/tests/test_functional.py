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
