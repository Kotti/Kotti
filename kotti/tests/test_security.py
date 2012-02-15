from unittest import TestCase

from mock import patch
from pyramid.authentication import CallbackAuthenticationPolicy

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

class TestGroups(UnitTestBase):
    def test_root_default(self):
        from kotti.resources import get_root
        from kotti.security import list_groups
        from kotti.security import list_groups_raw

        root = get_root()
        self.assertEqual(list_groups('admin', root), ['role:admin'])
        self.assertEqual(list_groups_raw(u'admin', root), set([]))

    def test_empty(self):
        from kotti.resources import get_root
        from kotti.security import list_groups

        root = get_root()
        self.assertEqual(list_groups('bob', root), [])

    def test_simple(self):
        from kotti.resources import get_root
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.security import set_groups

        root = get_root()
        set_groups('bob', root, ['role:editor'])
        self.assertEqual(
            list_groups('bob', root), ['role:editor'])
        self.assertEqual(
            list_groups_raw(u'bob', root), set(['role:editor']))

    def test_not_a_node(self):
        from kotti.security import list_groups_raw
        
        self.assertEqual(list_groups_raw(u'bob', object()), set())

    def test_overwrite_and_delete(self):
        from kotti.resources import get_root
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.security import set_groups

        root = get_root()
        set_groups('bob', root, ['role:editor'])
        self.assertEqual(
            list_groups('bob', root), ['role:editor'])
        self.assertEqual(
            list_groups_raw(u'bob', root), set(['role:editor']))

        set_groups('bob', root, ['role:admin'])
        self.assertEqual(
            list_groups('bob', root), ['role:admin'])
        self.assertEqual(
            list_groups_raw(u'bob', root), set(['role:admin']))

        set_groups('bob', root)
        self.assertEqual(
            list_groups('bob', root), [])
        self.assertTrue(get_root() is root)

    def test_inherit(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.security import set_groups

        root = get_root()
        child = root[u'child'] = Node()
        DBSession.flush()

        self.assertEqual(list_groups('bob', child), [])
        set_groups('bob', root, ['role:editor'])
        self.assertEqual(list_groups('bob', child), ['role:editor'])

        # Groups from the child are added:
        set_groups('bob', child, ['group:somegroup'])
        self.assertEqual(
            set(list_groups('bob', child)),
            set(['group:somegroup', 'role:editor'])
            )

        # We can ask to list only those groups that are defined locally:
        self.assertEqual(
            list_groups_raw(u'bob', child), set(['group:somegroup']))

    @staticmethod
    def add_some_groups():
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node
        from kotti.security import set_groups

        root = get_root()
        child = root[u'child'] = Node()
        grandchild = child[u'grandchild'] = Node()
        DBSession.flush()
        
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

    def test_nested_groups(self):
        from kotti.resources import get_root
        from kotti.security import list_groups
        from kotti.security import list_groups_ext

        self.add_some_groups()
        root = get_root()
        child = root[u'child']
        grandchild = child[u'grandchild']

        # Check bob's groups on every level:
        self.assertEqual(list_groups('bob', root), ['group:bobsgroup'])
        self.assertEqual(
            set(list_groups('bob', child)),
            set(['group:bobsgroup', 'group:franksgroup', 'role:editor'])
            )
        self.assertEqual(
            set(list_groups('bob', grandchild)),
            set(['group:bobsgroup', 'group:franksgroup', 'role:editor',
                 'role:owner'])
            )

        # Check group:franksgroup groups on every level:
        self.assertEqual(
            set(list_groups('frank', root)),
            set(['group:franksgroup', 'role:editor'])
            )
        self.assertEqual(
            set(list_groups('frank', child)),
            set(['group:franksgroup', 'role:editor'])
            )
        self.assertEqual(
            set(list_groups('frank', grandchild)),
            set(['group:franksgroup', 'role:editor', 'role:owner',
                 'group:bobsgroup'])
            )

        # Sometimes it's useful to know which of the groups were
        # inherited, that's what 'list_groups_ext' is for:
        groups, inherited = list_groups_ext('bob', root)
        self.assertEqual(groups, ['group:bobsgroup'])
        self.assertEqual(inherited, [])

        groups, inherited = list_groups_ext('bob', child)
        self.assertEqual(
            set(groups),
            set(['group:bobsgroup', 'group:franksgroup', 'role:editor'])
            )
        self.assertEqual(
            set(inherited),
            set(['group:bobsgroup', 'group:franksgroup', 'role:editor'])
            )

        groups, inherited = list_groups_ext('group:bobsgroup', child)
        self.assertEqual(
            set(groups),
            set(['group:franksgroup', 'role:editor'])
            )
        self.assertEqual(inherited, ['role:editor'])

        groups, inherited = list_groups_ext('group:franksgroup', grandchild)
        self.assertEqual(
            set(groups),
            set(['group:bobsgroup', 'role:owner', 'role:editor'])
            )
        self.assertEqual(inherited, ['role:editor'])

    def test_works_with_auth(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node
        from kotti.security import get_principals
        from kotti.security import list_groups_callback
        from kotti.security import set_groups

        root = get_root()
        child = root[u'child'] = Node()
        DBSession.flush()

        request = DummyRequest()
        auth = CallbackAuthenticationPolicy()
        auth.unauthenticated_userid = lambda *args: 'bob'
        auth.callback = list_groups_callback

        request.context = root
        self.assertEqual( # user doesn't exist yet
            auth.effective_principals(request),
            ['system.Everyone']
            )

        get_principals()[u'bob'] = dict(name=u'bob')
        self.assertEqual(
            auth.effective_principals(request),
            ['system.Everyone', 'system.Authenticated', 'bob']
            )

        # Define that bob belongs to bobsgroup on the root level:
        set_groups('bob', root, ['group:bobsgroup'])
        request.context = child
        self.assertEqual(
            set(auth.effective_principals(request)), set([
                'system.Everyone', 'system.Authenticated',
                'bob', 'group:bobsgroup'
                ])
            )

        # define that bob belongs to franksgroup in the user db:
        get_principals()[u'bob'].groups = [u'group:franksgroup']
        set_groups('group:franksgroup', child, ['group:anothergroup'])
        self.assertEqual(
            set(auth.effective_principals(request)), set([
                'system.Everyone', 'system.Authenticated',
                'bob', 'group:bobsgroup', 'group:franksgroup',
                'group:anothergroup',
                ])
            )

        # And lastly test that circular group defintions are not a
        # problem here either:
        get_principals()[u'group:franksgroup'] = dict(
            name=u'group:franksgroup',
            title=u"Frank's group",
            groups=[u'group:funnygroup', u'group:bobsgroup'],
            )
        self.assertEqual(
            set(auth.effective_principals(request)), set([
                'system.Everyone', 'system.Authenticated',
                'bob', 'group:bobsgroup', 'group:franksgroup',
                'group:anothergroup', 'group:funnygroup',
                ])
            )

    def test_list_groups_callback_with_groups(self):
        from kotti.security import list_groups_callback
        from kotti.security import get_principals

        # Although group definitions are also in the user database,
        # we're not allowed to authenticate with a group id:
        get_principals()[u'bob'] = dict(name=u'bob')
        get_principals()[u'group:bobsgroup'] = dict(name=u'group:bobsgroup')
        
        request = DummyRequest()
        self.assertEqual(
            list_groups_callback(u'bob', request), [])
        self.assertEqual(
            list_groups_callback(u'group:bobsgroup', request), None)

    def test_principals_with_local_roles(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node
        from kotti.security import map_principals_with_local_roles
        from kotti.security import principals_with_local_roles
        from kotti.security import set_groups

        root = get_root()
        child = root[u'child'] = Node()
        DBSession.flush()

        self.assertEqual(principals_with_local_roles(root), [])
        self.assertEqual(principals_with_local_roles(child), [])
        self.assertEqual(map_principals_with_local_roles(root), [])
        self.assertEqual(map_principals_with_local_roles(child), [])

        set_groups('group:bobsgroup', child, ['role:editor'])
        set_groups('bob', root, ['group:bobsgroup'])
        set_groups('group:franksgroup', root, ['role:editor'])

        self.assertEqual(
            set(principals_with_local_roles(child)),
            set(['bob', 'group:bobsgroup', 'group:franksgroup'])
            )
        self.assertEqual(
            set(principals_with_local_roles(child, inherit=False)),
            set(['group:bobsgroup'])
            )
        self.assertEqual(
            set(principals_with_local_roles(root)),
            set(['bob', 'group:franksgroup'])
            )

    def test_copy_local_groups(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.security import principals_with_local_roles
        from kotti.security import set_groups

        self.test_principals_with_local_roles()
        root = get_root()
        child = root[u'child']
        self.assertEqual(
            set(principals_with_local_roles(child)),
            set(['bob', 'group:bobsgroup', 'group:franksgroup'])
            )

        # We make a copy of 'child', and we expect the local roles to
        # be copied over:
        child2 = root['child2'] = child.copy()
        DBSession.flush()
        self.assertEqual(
            set(principals_with_local_roles(child2)),
            set(['bob', 'group:bobsgroup', 'group:franksgroup'])
            )
        self.assertEqual(len(principals_with_local_roles(child)), 3)

        # When we now change the local roles of 'child', the copy is
        # unaffected:
        set_groups('group:bobsgroup', child, [])
        self.assertEqual(len(principals_with_local_roles(child)), 2)
        self.assertEqual(len(principals_with_local_roles(child2)), 3)

    def test_map_principals_with_local_roles(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.security import map_principals_with_local_roles

        self.test_principals_with_local_roles()
        root = get_root()
        child = root[u'child']
        P = get_principals()

        # No users are defined in P, thus we get the empty list:
        self.assertEqual(map_principals_with_local_roles(root), [])

        P['bob'] = {'name': u'bob'}
        P['group:bobsgroup'] = {'name': u'group:bobsgroup'}

        value = map_principals_with_local_roles(root)
        self.assertEqual(len(value), 1)
        bob, (bob_all, bob_inherited) = value[0]
        self.assertEqual(bob_all, ['group:bobsgroup'])
        self.assertEqual(bob_inherited, [])

        value = map_principals_with_local_roles(child)
        self.assertEqual(len(value), 2)
        bob, (bob_all, bob_inherited) = value[0]
        bobsgroup, (bobsgroup_all, bobsgroup_inherited) = value[1]
        self.assertEqual(set(bob_all),
                         set(['group:bobsgroup', 'role:editor']))
        self.assertEqual(set(bob_inherited),
                         set(['group:bobsgroup', 'role:editor']))
        self.assertEqual(bobsgroup_all, ['role:editor'])
        self.assertEqual(bobsgroup_inherited, [])

    def test_local_roles_db_cascade(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import LocalGroup
        from kotti.resources import Node
        from kotti.security import set_groups

        root = get_root()
        child = root[u'child'] = Node()
        DBSession.flush()

        # We set a local group on child and delete child.  We then
        # expect the LocalGroup entry to have been deleted from the
        # database:
        self.assertEqual(DBSession.query(LocalGroup).count(), 0)
        set_groups('group:bobsgroup', child, ['role:editor'])
        self.assertEqual(DBSession.query(LocalGroup).count(), 1)
        del root[u'child']
        DBSession.flush()
        self.assertEqual(DBSession.query(LocalGroup).count(), 0)

class TestPrincipals(UnitTestBase):
    def get_principals(self):
        from kotti.security import get_principals
        return get_principals()

    def make_bob(self):
        users = self.get_principals()
        users[u'bob'] = dict(
            name=u'bob',
            password=u'secret',
            email=u'bob@dabolina.com',
            title=u'Bob Dabolina',
            groups=[u'group:bobsgroup'],
            )
        return users[u'bob']
    
    def _assert_is_bob(self, bob):
        self.assertEqual(bob.name, u'bob')
        self.assertEqual(bob.title, u'Bob Dabolina')
        self.assertEqual(bob.groups, [u'group:bobsgroup'])

    def test_default_admin(self):
        admin = self.get_principals()[u'admin']
        self.assertTrue(
            self.get_principals().validate_password(u'secret', admin.password))
        self.assertEqual(admin.groups, [u'role:admin'])

    def test_users_empty(self):
        users = self.get_principals()
        self.assertRaises(KeyError, users.__getitem__, u'bob')
        self.assertRaises(KeyError, users.__delitem__, u'bob')
        self.assertEqual(users.keys(), [u'admin'])

    def test_users_add_and_remove(self):
        self.make_bob()
        users = self.get_principals()
        self._assert_is_bob(users[u'bob'])
        self.assertEqual(set(users.keys()), set([u'admin', u'bob']))

        del users['bob']
        self.assertRaises(KeyError, users.__getitem__, u'bob')
        self.assertRaises(KeyError, users.__delitem__, u'bob')

    def test_users_search(self):
        users = self.get_principals()
        self.assertEqual(list(users.search(name=u"*Bob*")), [])
        self.make_bob()
        [bob] = list(users.search(name=u"bob"))
        self._assert_is_bob(bob)
        [bob] = list(users.search(name=u"*Bob*"))
        self._assert_is_bob(bob)
        [bob] = list(users.search(name=u"*Bob*", title=u"*Frank*"))
        self._assert_is_bob(bob)
        self.assertRaises(AttributeError,
                          users.search, name=u"bob", foo=u"bar")
        self.assertEqual(list(users.search()), [])

    def test_groups_from_users(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node
        from kotti.security import list_groups
        from kotti.security import set_groups

        self.make_bob()
        root = get_root()
        child = root[u'child'] = Node()
        DBSession.flush()

        self.assertEqual(list_groups('bob', root), ['group:bobsgroup'])

        set_groups('group:bobsgroup', root, ['role:editor'])
        set_groups('role:editor', child, ['group:foogroup'])

        self.assertEqual(
            set(list_groups('bob', root)),
            set(['group:bobsgroup', 'role:editor'])
            )
        self.assertEqual(
            set(list_groups('bob', child)),
            set(['group:bobsgroup', 'role:editor', 'group:foogroup'])
            )

    def test_is_user(self):
        from kotti.security import is_user
        
        bob = self.make_bob()
        self.assertEqual(is_user(bob), True)
        bob.name = u'group:bobsgroup'
        self.assertEqual(is_user(bob), False)

    def test_hash_and_validate_password(self):
        password = u"secret"
        principals = self.get_principals()
        hashed = principals.hash_password(password)
        self.assertTrue(principals.validate_password(password, hashed))
        self.assertFalse(principals.validate_password(u"foo", hashed))

    def test_bobs_hashed_password(self):
        bob = self.make_bob()
        principals = self.get_principals()
        self.assertTrue(principals.validate_password(u"secret", bob.password))

        # When we set the 'password' attribute directly, we have to do
        # the hashing ourselves.  This won't work:
        bob.password = u'anothersecret'
        self.assertFalse(
            principals.validate_password(u"anothersecret", bob.password))

        # This will:
        bob.password = principals.hash_password(u"anothersecret")
        self.assertTrue(
            principals.validate_password(u"anothersecret", bob.password))

    def test_active(self):
        bob = self.make_bob()
        self.assertEqual(bob.active, True)
        bob.active = False
        self.assertEqual(bob.active, False)

    def test_login(self):
        from kotti.views.login import login
        request = DummyRequest()

        # No login attempt:
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('success'), [])
        self.assertEqual(request.session.pop_flash('error'), [])

        # Attempt to log in before Bob exists:
        request.params['submit'] = u'on'
        request.params['login'] = u'bob'
        request.params['password'] = u'secret'
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('success'), [])
        self.assertEqual(request.session.pop_flash('error'),
                         [u'Login failed.'])

        # Make Bob and do it again:
        bob = self.make_bob()
        self.assertEqual(bob.last_login_date, None)
        result = login(None, request)
        self.assertEqual(result.status, '302 Found')
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Welcome, Bob Dabolina!'])
        last_login_date = bob.last_login_date
        self.assertNotEqual(last_login_date, None)
        self.assertEqual(request.session.pop_flash('error'), [])

        # Log in with email:
        request.params['login'] = u'bob@dabolina.com'
        result = login(None, request)
        self.assertEqual(result.status, '302 Found')
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Welcome, Bob Dabolina!'])
        self.assertTrue(last_login_date < bob.last_login_date)

        # Deactive Bob, logging in is no longer possible:
        bob.active = False
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('error'),
                         [u'Login failed.'])

        # If Bob has a 'confirm_token' set, logging in is still possible:
        bob.active = True
        bob.confirm_token = u'token'
        result = login(None, request)
        self.assertEqual(result.status, '302 Found')
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Welcome, Bob Dabolina!'])

class TestAuthzContextManager(TestCase):
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

class TestHasPermission(TestCase):
    def test_basic(self):
        from kotti.security import has_permission

        permission, context, request = object(), object(), DummyRequest()
        args = []

        def has_permission_fake(permission, context, request):
            args.append((permission, context, request))
            assert request.environ['authz_context'] == context

        with patch('kotti.security.base_has_permission',
                   new=has_permission_fake):
            has_permission(permission, context, request)

        assert args == [(permission, context, request)]

class TestRolesSetters(UnitTestBase):
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
