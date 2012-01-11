import colander
from mock import patch

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

class TestUserManagement(UnitTestBase):
    def test_roles(self):
        from kotti.resources import get_root
        from kotti.security import USER_MANAGEMENT_ROLES
        from kotti.views.users import users_manage

        root = get_root()
        request = DummyRequest()
        self.assertEqual(
            [r.name for r in users_manage(root, request)['available_roles']],
            USER_MANAGEMENT_ROLES)

    def test_search(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.tests.test_node_views import TestNodeShare
        from kotti.views.users import users_manage

        root = get_root()
        request = DummyRequest()
        P = get_principals()
        TestNodeShare.add_some_principals()

        request.params['search'] = u''
        request.params['query'] = u'Joe'
        entries = users_manage(root, request)['entries']
        self.assertEqual(len(entries), 0)
        self.assertEqual(request.session.pop_flash('notice'),
                         [u'No users or groups found.'])
        request.params['query'] = u'Bob'
        entries = users_manage(root, request)['entries']
        self.assertEqual(entries[0][0], P['bob'])
        self.assertEqual(entries[0][1], ([], []))
        self.assertEqual(entries[1][0], P['group:bobsgroup'])
        self.assertEqual(entries[1][1], ([], []))

        P[u'bob'].groups = [u'group:bobsgroup']
        P[u'group:bobsgroup'].groups = [u'role:admin']
        entries = users_manage(root, request)['entries']
        self.assertEqual(entries[0][1],
                         (['group:bobsgroup', 'role:admin'], ['role:admin']))
        self.assertEqual(entries[1][1], (['role:admin'], []))

    def test_apply(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.security import list_groups
        from kotti.tests.test_node_views import TestNodeShare
        from kotti.views.users import users_manage

        root = get_root()
        request = DummyRequest()

        TestNodeShare.add_some_principals()
        bob = get_principals()[u'bob']

        request.params['apply'] = u''
        users_manage(root, request)
        self.assertEqual(request.session.pop_flash('notice'),
                         [u'No changes made.'])
        self.assertEqual(list_groups('bob'), [])
        bob.groups = [u'role:special']

        request.params['role::bob::role:owner'] = u'1'
        request.params['role::bob::role:editor'] = u'1'
        request.params['orig-role::bob::role:owner'] = u''
        request.params['orig-role::bob::role:editor'] = u''

        users_manage(root, request)
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Your changes have been saved.'])
        self.assertEqual(
            set(list_groups('bob')),
            set(['role:owner', 'role:editor', 'role:special'])
            )

    def test_group_validator(self):
        from kotti.views.users import group_validator
        self.assertRaises(
            colander.Invalid,
            group_validator, None, u'this-group-never-exists')

class TestSetPassword(UnitTestBase):
    def setUp(self):
        super(TestSetPassword, self).setUp()

        Form_patcher = patch('kotti.views.login.Form')
        self.Form_mock = Form_patcher.start()

        _find_user_patcher = patch('kotti.views.login._find_user')
        self._find_user_mock = _find_user_patcher.start()
        self.user = self._find_user_mock.return_value

        validate_token_patcher = patch('kotti.views.login.validate_token')
        self.validate_token_mock = validate_token_patcher.start()

        self.patchers = (
            Form_patcher, _find_user_patcher, validate_token_patcher)

    def tearDown(self):
        super(TestSetPassword, self).tearDown()
        for patcher in self.patchers:
            patcher.stop()

    def form_values(self, values):
        self.Form_mock.return_value.validate.return_value = values

    def test_success(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.views.login import set_password

        self.form_values({
            'token': 'mytoken',
            'email': 'myemail',
            'password': 'mypassword',
            'continue_to': '',
            })
        self.user.confirm_token = 'mytoken'
        self.user.password = 'old_password'
        context, request = get_root(), DummyRequest(post={'submit': 'submit'})
        res = set_password(context, request)

        assert self.user.confirm_token is None
        assert get_principals().validate_password(
            'mypassword', self.user.password)
        assert res.status == '302 Found'

    def test_wrong_token(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.views.login import set_password

        self.form_values({
            'token': 'wrongtoken',
            'email': 'myemail',
            'password': 'mypassword',
            'continue_to': '',
            })
        self.user.confirm_token = 'mytoken'
        self.user.password = 'old_password'
        context, request = get_root(), DummyRequest(post={'submit': 'submit'})
        res = set_password(context, request)

        assert self.user.confirm_token == 'mytoken'
        assert not get_principals().validate_password(
            'mypassword', self.user.password)
        assert not request.is_response(res)

    def test_success_continue(self):
        from kotti.resources import get_root
        from kotti.views.login import set_password

        self.form_values({
            'token': 'mytoken',
            'email': 'myemail',
            'password': 'mypassword',
            'continue_to': 'http://example.com/here#there',
            })
        self.user.confirm_token = 'mytoken'
        context, request = get_root(), DummyRequest(
            post={'submit': 'submit'})
        res = set_password(context, request)

        assert res.status == '302 Found'
        assert res.location == 'http://example.com/here#there'
