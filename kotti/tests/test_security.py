from mock import patch
from pyramid.authentication import CallbackAuthenticationPolicy
from pytest import raises

from kotti.testing import DummyRequest


class HasPermissionTests:

    def test_has_permission(self):
        import mock
        from kotti.security import has_permission
        permission = 'edit'
        context = object()
        request = mock.MagicMock()
        has_permission(permission, context, request)
        assert request.has_permission.assert_called_once_with(
            permission, context=context) is None


class TestGroups:
    def test_root_default(self, db_session, root):
        from kotti.security import list_groups
        from kotti.security import list_groups_raw

        assert list_groups('admin', root) == ['role:admin']
        assert list_groups_raw('admin', root) == set([])

    def test_empty(self, db_session, root):
        from kotti.security import list_groups

        assert list_groups('bob', root) == []

    def test_simple(self, db_session, root):
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.security import set_groups

        set_groups('bob', root, ['role:editor'])
        assert list_groups('bob', root) == ['role:editor']
        assert list_groups_raw('bob', root) == {'role:editor'}

    def test_not_a_node(self):
        from kotti.security import list_groups_raw

        assert list_groups_raw('bob', object()) == set()

    def test_overwrite_and_delete(self, db_session, root):
        from kotti.resources import get_root
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.security import set_groups

        set_groups('bob', root, ['role:editor'])
        assert list_groups('bob', root) == ['role:editor']
        assert list_groups_raw('bob', root) == {'role:editor'}

        set_groups('bob', root, ['role:admin'])
        assert list_groups('bob', root) == ['role:admin']
        assert list_groups_raw('bob', root) == {'role:admin'}

        set_groups('bob', root)
        assert list_groups('bob', root) == []
        assert get_root() is root

    def test_inherit(self, db_session, root):
        from kotti.resources import Node
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.security import set_groups

        child = root['child'] = Node()
        db_session.flush()

        assert list_groups('bob', child) == []
        set_groups('bob', root, ['role:editor'])
        assert list_groups('bob', child) == ['role:editor']

        # Groups from the child are added:
        set_groups('bob', child, ['group:somegroup'])
        assert (
            set(list_groups('bob', child)) ==
            {'group:somegroup', 'role:editor'}
            )

        # We can ask to list only those groups that are defined locally:
        assert list_groups_raw('bob', child) == {'group:somegroup'}

    @staticmethod
    def add_some_groups(db_session, root):
        from kotti.resources import Node
        from kotti.security import set_groups

        child = root['child'] = Node()
        grandchild = child['grandchild'] = Node()
        db_session.flush()

        # root:
        #   bob               -> group:bobsgroup
        #   frank             -> group:franksgroup
        #   group:franksgroup -> role:editor
        # child:
        #   group:bobsgroup   -> group:franksgroup
        # grandchild:
        #   group:franksgroup -> role:admin
        #   group:franksgroup -> group:bobsgroup

        # bob and frank are a site-wide members of their respective groups:
        set_groups('bob', root, ['group:bobsgroup'])
        set_groups('frank', root, ['group:franksgroup'])

        # franksgroup has a site-wide editor role:
        set_groups('group:franksgroup', root, ['role:editor'])

        # bobsgroup is part of franksgroup on the child level:
        set_groups('group:bobsgroup', child, ['group:franksgroup'])

        # franksgroup has the admin role on the grandchild.
        # and finally, to test recursion, we make franksgroup part of
        # bobsgroup on the grandchild level:
        set_groups('group:franksgroup', grandchild,
                   ['role:owner', 'group:bobsgroup'])

    def test_nested_groups(self, db_session, root):
        from kotti.security import list_groups
        from kotti.security import list_groups_ext

        self.add_some_groups(db_session, root)
        child = root['child']
        grandchild = child['grandchild']

        # Check bob's groups on every level:
        assert list_groups('bob', root) == ['group:bobsgroup']
        assert (set(list_groups('bob', child)) ==
                {'group:bobsgroup', 'group:franksgroup', 'role:editor'})
        assert (set(list_groups('bob', grandchild)) ==
                {'group:bobsgroup', 'group:franksgroup', 'role:editor',
                 'role:owner'})

        # Check group:franksgroup groups on every level:
        assert (set(list_groups('frank', root)) ==
                {'group:franksgroup', 'role:editor'})
        assert (set(list_groups('frank', child)) ==
                {'group:franksgroup', 'role:editor'})
        assert (set(list_groups('frank', grandchild)) ==
                {'group:franksgroup', 'role:editor', 'role:owner',
                 'group:bobsgroup'})

        # Sometimes it's useful to know which of the groups were
        # inherited, that's what 'list_groups_ext' is for:
        groups, inherited = list_groups_ext('bob', root)
        assert groups == ['group:bobsgroup']
        assert inherited == []

        groups, inherited = list_groups_ext('bob', child)
        assert (set(groups) ==
                {'group:bobsgroup', 'group:franksgroup', 'role:editor'})
        assert (set(inherited) ==
                {'group:bobsgroup', 'group:franksgroup', 'role:editor'})

        groups, inherited = list_groups_ext('group:bobsgroup', child)
        assert set(groups) == {'group:franksgroup', 'role:editor'}
        assert inherited == ['role:editor']

        groups, inherited = list_groups_ext('group:franksgroup', grandchild)
        assert (set(groups) ==
                {'group:bobsgroup', 'role:owner', 'role:editor'})
        assert inherited == ['role:editor']

    def test_works_with_auth(self, db_session, root):
        from kotti.resources import Node
        from kotti.security import get_principals
        from kotti.security import list_groups_callback
        from kotti.security import set_groups

        child = root['child'] = Node()
        db_session.flush()

        request = DummyRequest()
        auth = CallbackAuthenticationPolicy()
        auth.unauthenticated_userid = lambda *args: 'bob'
        auth.callback = list_groups_callback

        request.context = root
        assert (  # user doesn't exist yet
            auth.effective_principals(request) ==
            ['system.Everyone']
            )

        get_principals()['bob'] = dict(name='bob')
        assert (
            auth.effective_principals(request) ==
            ['system.Everyone', 'system.Authenticated', 'bob']
            )

        # Define that bob belongs to bobsgroup on the root level:
        set_groups('bob', root, ['group:bobsgroup'])
        request.context = child
        assert (
            set(auth.effective_principals(request)) == {'system.Everyone',
                                                        'system.Authenticated',
                                                        'bob',
                                                        'group:bobsgroup'}
            )

        # define that bob belongs to franksgroup in the user db:
        get_principals()['bob'].groups = ['group:franksgroup']
        set_groups('group:franksgroup', child, ['group:anothergroup'])
        assert (
            set(auth.effective_principals(request)) == {'system.Everyone',
                                                        'system.Authenticated',
                                                        'bob',
                                                        'group:bobsgroup',
                                                        'group:franksgroup',
                                                        'group:anothergroup'}
            )

        # And lastly test that circular group defintions are not a
        # problem here either:
        get_principals()['group:franksgroup'] = dict(
            name='group:franksgroup',
            title="Frank's group",
            groups=['group:funnygroup', 'group:bobsgroup'],
            )
        assert (
            set(auth.effective_principals(request)) == {'system.Everyone',
                                                        'system.Authenticated',
                                                        'bob',
                                                        'group:bobsgroup',
                                                        'group:franksgroup',
                                                        'group:anothergroup',
                                                        'group:funnygroup'}
            )

    def test_list_groups_callback_with_groups(self, db_session):
        from kotti.security import list_groups_callback
        from kotti.security import get_principals

        # Although group definitions are also in the user database,
        # we're not allowed to authenticate with a group id:
        get_principals()['bob'] = dict(name='bob')
        get_principals()['group:bobsgroup'] = dict(name='group:bobsgroup')

        request = DummyRequest()
        assert list_groups_callback('bob', request) == []
        assert list_groups_callback('group:bobsgroup', request) is None

    def test_principals_with_local_roles(self, db_session, root):
        from kotti.resources import Node
        from kotti.security import map_principals_with_local_roles
        from kotti.security import principals_with_local_roles
        from kotti.security import set_groups

        child = root['child'] = Node()
        db_session.flush()

        assert principals_with_local_roles(root) == []
        assert principals_with_local_roles(child) == []
        assert map_principals_with_local_roles(root) == []
        assert map_principals_with_local_roles(child) == []

        set_groups('group:bobsgroup', child, ['role:editor'])
        set_groups('bob', root, ['group:bobsgroup'])
        set_groups('group:franksgroup', root, ['role:editor'])

        assert (
            set(principals_with_local_roles(child)) ==
            {'bob', 'group:bobsgroup', 'group:franksgroup'}
            )
        assert (
            set(principals_with_local_roles(child, inherit=False)) ==
            {'group:bobsgroup'}
            )
        assert (
            set(principals_with_local_roles(root)) ==
            {'bob', 'group:franksgroup'}
            )

    def test_copy_local_groups(self, db_session, root):
        from kotti.security import principals_with_local_roles
        from kotti.security import set_groups

        self.test_principals_with_local_roles(db_session, root)
        child = root['child']
        assert (
            set(principals_with_local_roles(child)) ==
            {'bob', 'group:bobsgroup', 'group:franksgroup'}
            )

        # We make a copy of 'child', and we expect the local roles set
        # on 'child' to not be copied over:
        child2 = root['child2'] = child.copy()
        db_session.flush()
        assert (
            set(principals_with_local_roles(child2)) ==
            {'bob', 'group:franksgroup'})
        assert len(principals_with_local_roles(child)) == 3

        # When we now change the local roles of 'child', the copy is
        # unaffected:
        set_groups('group:bobsgroup', child, [])
        assert len(principals_with_local_roles(child)) == 2
        assert len(principals_with_local_roles(child2)) == 2

    def test_map_principals_with_local_roles(self, db_session, root):
        from kotti.security import get_principals
        from kotti.security import map_principals_with_local_roles

        self.test_principals_with_local_roles(db_session, root)
        child = root['child']
        P = get_principals()

        # No users are defined in P, thus we get the empty list:
        assert map_principals_with_local_roles(root) == []

        P['bob'] = {'name': 'bob'}
        P['group:bobsgroup'] = {'name': 'group:bobsgroup'}

        value = map_principals_with_local_roles(root)
        assert len(value) == 1
        bob, (bob_all, bob_inherited) = value[0]
        assert bob_all == ['group:bobsgroup']
        assert bob_inherited == []

        value = map_principals_with_local_roles(child)
        assert len(value) == 2
        bob, (bob_all, bob_inherited) = value[0]
        bobsgroup, (bobsgroup_all, bobsgroup_inherited) = value[1]
        assert (set(bob_all) == {'group:bobsgroup', 'role:editor'})
        assert (set(bob_inherited) == {'group:bobsgroup', 'role:editor'})
        assert bobsgroup_all == ['role:editor']
        assert bobsgroup_inherited == []

    def test_local_roles_db_cascade(self, db_session, root):
        from kotti.resources import LocalGroup
        from kotti.resources import Node
        from kotti.security import set_groups

        child = root['child'] = Node()
        db_session.flush()

        # We set a local group on child and delete child.  We then
        # expect the LocalGroup entry to have been deleted from the
        # database:
        assert db_session.query(LocalGroup).count() == 0
        set_groups('group:bobsgroup', child, ['role:editor'])
        assert db_session.query(LocalGroup).count() == 1
        del root['child']
        db_session.flush()
        assert db_session.query(LocalGroup).count() == 0


class TestPrincipals:
    def get_principals(self):
        from kotti.security import get_principals
        return get_principals()

    def make_bob(self):
        users = self.get_principals()
        users['bob'] = dict(
            name='bob',
            password='secret',
            email='bob@dabolina.com',
            title='Bob Dabolina',
            groups=['group:bobsgroup'],
            )
        return users['bob']

    def _assert_is_bob(self, bob):
        assert bob.name == 'bob'
        assert bob.title == 'Bob Dabolina'
        assert bob.groups == ['group:bobsgroup']

    def test_hash_password_non_ascii(self, db_session):
        self.get_principals().hash_password('\xd6TEst')

    def test_default_admin(self, db_session):
        admin = self.get_principals()['admin']
        assert self.get_principals().validate_password(
            'secret', admin.password)
        assert admin.groups == ['role:admin']

    def test_users_empty(self, db_session):
        users = self.get_principals()
        with raises(KeyError):
            users['bob']
        with raises(KeyError):
            del users['bob']
        assert users.keys() == ['admin']

    def test_users_add_and_remove(self, db_session):
        self.make_bob()
        users = self.get_principals()
        self._assert_is_bob(users['bob'])
        assert set(users.keys()) == {'admin', 'bob'}

        del users['bob']
        with raises(KeyError):
            users['bob']
        with raises(KeyError):
            del users['bob']

    def test_users_search(self, db_session):
        users = self.get_principals()
        assert list(users.search(name="*Bob*")) == []
        self.make_bob()
        [bob] = list(users.search(name="bob"))
        self._assert_is_bob(bob)
        [bob] = list(users.search(name="*Bob*"))
        self._assert_is_bob(bob)
        [bob] = list(users.search(name="*Bob*", title="*Frank*"))
        self._assert_is_bob(bob)
        with raises(AttributeError):
            users.search(name="bob", foo="bar")
        assert list(users.search()) == []
        # search on a non string attribute
        assert bob in list(users.search(active=True))
        # test operator
        assert len(list(users.search(name='bob', active=True))) == 2
        assert len(list(users.search(match='all', name='bob',
                                     active=True))) == 1

    def test_groups_from_users(self, db_session, root):
        from kotti.resources import Node
        from kotti.security import list_groups
        from kotti.security import set_groups

        self.make_bob()
        child = root['child'] = Node()
        db_session.flush()

        assert list_groups('bob', root) == ['group:bobsgroup']

        set_groups('group:bobsgroup', root, ['role:editor'])
        set_groups('role:editor', child, ['group:foogroup'])

        assert (set(list_groups('bob', root)) ==
                {'group:bobsgroup', 'role:editor'})
        assert (set(list_groups('bob', child)) ==
                {'group:bobsgroup', 'role:editor', 'group:foogroup'})

    def test_is_user(self, db_session):
        from kotti.security import is_user

        bob = self.make_bob()
        assert is_user(bob) is True
        bob.name = 'group:bobsgroup'
        assert is_user(bob) is False

    def test_hash_and_validate_password(self, db_session):
        password = "secret"
        principals = self.get_principals()
        hashed = principals.hash_password(password)
        assert principals.validate_password(password, hashed)
        assert principals.validate_password("foo", hashed) is False

    def test_bobs_hashed_password(self, db_session):
        bob = self.make_bob()
        principals = self.get_principals()
        assert principals.validate_password("secret", bob.password)

        # When we set the 'password' attribute directly, we have to do
        # the hashing ourselves.  This won't work:
        bob.password = 'anothersecret'
        assert principals.validate_password(
            "anothersecret", bob.password) is False

        # This will:
        bob.password = principals.hash_password("anothersecret")
        assert principals.validate_password("anothersecret", bob.password)

    def test_active(self, db_session):
        bob = self.make_bob()
        assert bob.active is True
        bob.active = False
        assert bob.active is False

    def test_reset_password(self, db_session):
        from kotti.views.login import login

        request = DummyRequest()
        self.make_bob()
        request.params['reset-password'] = 'on'
        request.params['login'] = 'bob'
        request.params['password'] = 'secret'
        with patch(
                'kotti.views.login.email_set_password') as email_set_password:
            login(None, request)
        assert (request.session.pop_flash('success') == [
            "You should be receiving an email with a link to reset your "
            "password. Doing so will activate your account."])
        assert email_set_password.call_count == 1

    def test_reset_password_inactive_user(self, db_session):
        from kotti.views.login import login

        request = DummyRequest()
        self.make_bob().active = False
        request.params['reset-password'] = 'on'
        request.params['login'] = 'bob'
        request.params['password'] = 'secret'
        with patch(
                'kotti.views.login.email_set_password') as email_set_password:
            login(None, request)
        assert (request.session.pop_flash('error') ==
                ["That username or email is not known by this system."])
        assert email_set_password.call_count == 0

    def test_login(self, db_session):
        from kotti.views.login import login
        request = DummyRequest()

        # No login attempt:
        result = login(None, request)
        assert isinstance(result, dict)
        assert request.session.pop_flash('success') == []
        assert request.session.pop_flash('error') == []

        # Attempt to log in before Bob exists:
        request.params['submit'] = 'on'
        request.params['login'] = 'bob'
        request.params['password'] = 'secret'
        result = login(None, request)
        assert isinstance(result, dict)
        assert request.session.pop_flash('success') == []
        assert (request.session.pop_flash('error') == ['Login failed.'])

        # Make Bob and do it again:
        bob = self.make_bob()
        assert bob.last_login_date is None
        result = login(None, request)
        assert result.status == '302 Found'
        assert (
            [request.session.pop_flash('success')[0].interpolate()] ==
            ['Welcome, Bob Dabolina!'])
        last_login_date = bob.last_login_date
        assert last_login_date is not None
        assert request.session.pop_flash('error') == []

        # Log in with email:
        request.params['login'] = 'bob@dabolina.com'
        result = login(None, request)
        assert result.status == '302 Found'
        assert (
            [request.session.pop_flash('success')[0].interpolate()] ==
            ['Welcome, Bob Dabolina!'])
        assert last_login_date < bob.last_login_date

        # Deactive Bob, logging in is no longer possible:
        bob.active = False
        result = login(None, request)
        assert isinstance(result, dict)
        assert (request.session.pop_flash('error') == ['Login failed.'])

        # If Bob has a 'confirm_token' set, logging in is still possible:
        bob.active = True
        bob.confirm_token = 'token'
        result = login(None, request)
        assert result.status == '302 Found'
        assert (
            [request.session.pop_flash('success')[0].interpolate()] ==
            ['Welcome, Bob Dabolina!'])

    def test_login_with_email_remembers(self, db_session):
        from kotti.views.login import login
        request = DummyRequest()

        self.make_bob()
        request.params['submit'] = 'on'
        request.params['login'] = 'bob@dabolina.com'
        request.params['password'] = 'secret'
        with patch('kotti.views.login.remember') as remember:
            login(None, request)
            remember.assert_called_with(request, 'bob')


class TestAuthzContextManager:
    def test_basic(self):
        from kotti.security import authz_context

        context, request = object(), DummyRequest()
        with authz_context(context, request):
            assert request.environ['authz_context'] == context
        assert 'authz_context' not in request.environ

    def test_set_before(self):
        from kotti.security import authz_context

        context, context2, request = object(), object(), DummyRequest()
        request.environ['authz_context'] = context2
        with authz_context(context, request):
            assert request.environ['authz_context'] == context
        assert request.environ['authz_context'] == context2

    def test_with_exception(self):
        from kotti.security import authz_context

        context, context2, request = object(), object(), DummyRequest()
        request.environ['authz_context'] = context2
        try:
            with authz_context(context, request):
                assert request.environ['authz_context'] == context
                raise ValueError
        except ValueError:
            assert request.environ['authz_context'] == context2


class TestViewPermitted:
    @patch('kotti.security.view_execution_permitted')
    def test_with_post_request(self, view_execution_permitted):
        from kotti.security import view_permitted

        context, request = object(), DummyRequest()
        request.method = 'POST'
        calls = []

        def view_execution_permitted_mock(context, request, name):
            calls.append((context, request, name))
            assert request.method == 'GET'

        view_execution_permitted.side_effect = view_execution_permitted_mock
        view_permitted(context, request)
        assert len(calls) == 1
        assert request.method == 'POST'


class TestHasPermission:

    def test_request_has_permission(self):

        from kotti.request import Request

        permission, context = object(), object()
        args = []

        def has_permission_fake(self, permission, context=None):
            args.append((permission, context))
            assert self.environ['authz_context'] == context

        with patch('kotti.request.pyramid.request.Request.has_permission',
                   new=has_permission_fake):
            request = Request.blank('/')
            request.has_permission(permission, context)

        assert args == [(permission, context)]


class TestRolesSetters:
    def test_set_roles(self):
        from kotti.security import ROLES
        from kotti.security import set_roles
        from kotti.security import reset_roles

        before = ROLES.copy()
        set_roles({'role:admin': ROLES['role:admin']})
        assert ROLES == {'role:admin': ROLES['role:admin']}
        reset_roles()
        assert ROLES == before

    def test_set_sharing_roles(self):
        from kotti.security import SHARING_ROLES
        from kotti.security import set_sharing_roles
        from kotti.security import reset_sharing_roles

        before = SHARING_ROLES[:]
        set_sharing_roles(['role:admin'])
        assert SHARING_ROLES == ['role:admin']
        reset_sharing_roles()
        assert SHARING_ROLES == before

    def test_set_user_management_roles(self):
        from kotti.security import USER_MANAGEMENT_ROLES
        from kotti.security import set_user_management_roles
        from kotti.security import reset_user_management_roles

        before = USER_MANAGEMENT_ROLES[:]
        set_user_management_roles(['role:admin'])
        assert USER_MANAGEMENT_ROLES == ['role:admin']
        reset_user_management_roles()
        assert USER_MANAGEMENT_ROLES == before
