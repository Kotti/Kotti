import colander
import pytest
from mock import patch

from kotti.testing import (
    DummyRequest,
    UnitTestBase,
    EventTestBase,
)


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
        self.assertEqual(request.session.pop_flash('info'),
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
        self.assertEqual(request.session.pop_flash('info'),
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


class TestUserDelete(EventTestBase, UnitTestBase):
    def test_user_delete(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.tests.test_node_views import TestNodeShare
        from kotti.views.users import user_delete

        root = get_root()
        request = DummyRequest()
        TestNodeShare.add_some_principals()
        bob = get_principals()[u'bob']

        request.params['name'] = u''
        user_delete(root, request)
        assert request.session.pop_flash('error') == [u'No name given.']
        assert u'bob' in get_principals().keys()

        request.params['name'] = u'bob'
        result = user_delete(root, request)
        assert u'api' in result
        api = result[u'api']
        assert api.principal == bob
        assert api.principal_type == u'User'
        assert u'bob' in get_principals().keys()

        request.params['name'] = u'john'
        request.params['delete'] = u'delete'
        user_delete(root, request)
        assert request.session.pop_flash('error') == [u"User not found."]
        assert u'bob' in get_principals().keys()

        request.params['name'] = u'bob'
        request.params['delete'] = u'delete'
        user_delete(root, request)
        with pytest.raises(KeyError):
            get_principals()[u'bob']

    def test_deleted_group_removed_in_usergroups(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.tests.test_node_views import TestNodeShare
        from kotti.views.users import user_delete

        root = get_root()
        request = DummyRequest()
        TestNodeShare.add_some_principals()
        bob = get_principals()[u'bob']
        bob.groups = [u'group:bobsgroup']
        assert bob.groups == [u'group:bobsgroup']

        request.params['name'] = u'group:bobsgroup'
        request.params['delete'] = u'delete'
        user_delete(root, request)
        with pytest.raises(KeyError):
            get_principals()[u'group:bobsgroup']
        assert bob.groups == []

    def test_deleted_group_removed_from_localgroups(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.security import set_groups
        from kotti.resources import LocalGroup
        from kotti.views.users import user_delete
        from kotti.tests.test_node_views import TestNodeShare

        root = get_root()
        request = DummyRequest()
        TestNodeShare.add_some_principals()
        set_groups(u'group:bobsgroup', root, ['role:admin'])
        local_group = DBSession.query(LocalGroup).first()
        assert local_group.principal_name == u'group:bobsgroup'
        assert local_group.node == root

        request.params['name'] = u'group:bobsgroup'
        request.params['delete'] = u'delete'
        user_delete(root, request)
        assert DBSession.query(LocalGroup).first() == None

    def test_reset_owner_to_none(self):
        from kotti.resources import get_root
        from kotti.resources import Content
        from kotti.views.users import user_delete
        from kotti.tests.test_node_views import TestNodeShare

        root = get_root()
        request = DummyRequest()
        TestNodeShare.add_some_principals()

        root[u'content_1'] = Content()
        root[u'content_1'].owner = u'bob'
        assert root[u'content_1'].owner == u'bob'

        request.params['name'] = u'bob'
        request.params['delete'] = u'delete'
        user_delete(root, request)
        assert root[u'content_1'].owner == None


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
        self.user.last_login_date = None
        res = set_password(context, request)

        assert self.user.confirm_token is None
        assert self.user.last_login_date is not None
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

    def test_inactive_user(self):
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
        self.user.active = False
        self.user.last_login_date = None
        res = set_password(context, request)

        assert self.user.confirm_token == 'mytoken'
        assert self.user.last_login_date is None
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
