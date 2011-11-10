from contextlib import contextmanager
import os
import unittest
import warnings

import transaction
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
import colander
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.config import DEFAULT_RENDERERS
from pyramid.exceptions import Forbidden
from pyramid.registry import Registry
from pyramid.security import ALL_PERMISSIONS
from pyramid import testing

from kotti import conf_defaults
from kotti import get_settings
from kotti import _resolve_dotted
from kotti import main
from kotti import DBSession
from kotti.events import clear
from kotti.message import _inject_mailer
from kotti.resources import Node
from kotti.resources import Content
from kotti.resources import Document
from kotti.resources import LocalGroup
from kotti.resources import initialize_sql
from kotti.resources import get_root
from kotti.security import list_groups
from kotti.security import list_groups_ext
from kotti.security import list_groups_raw
from kotti.security import set_groups
from kotti.security import list_groups_callback
from kotti.security import principals_with_local_roles
from kotti.security import map_principals_with_local_roles
from kotti.security import get_principals
from kotti.security import is_user
from kotti.util import ViewLink
from kotti.util import clear_cache

BASE_URL = 'http://localhost:6543'

class DummyRequest(testing.DummyRequest):
    is_xhr = False

    def is_response(self, ob):
        return ( hasattr(ob, 'app_iter') and hasattr(ob, 'headerlist') and
                 hasattr(ob, 'status') )

def testing_db_url():
    return os.environ.get('KOTTI_TEST_DB_STRING', 'sqlite://')

def _initTestingDB():
    from sqlalchemy import create_engine
    database_url = testing_db_url()
    session = initialize_sql(create_engine(database_url), drop_all=True)
    return session

def setUp(init_db=True, **kwargs):
    #warnings.filterwarnings("error")
    tearDown()
    settings = conf_defaults.copy()
    settings['kotti.secret'] = 'secret'
    settings['kotti.secret2'] = 'secret2'
    _resolve_dotted(settings)
    settings.update(kwargs.get('settings', {}))
    kwargs['settings'] = settings
    config = testing.setUp(**kwargs)
    for name, renderer in DEFAULT_RENDERERS:
        config.add_renderer(name, renderer)

    if init_db:
        _initTestingDB()

    transaction.begin()
    return config

def tearDown():
    _inject_mailer[:] = []
    clear()
    transaction.abort()
    testing.tearDown()

class UnitTestBase(unittest.TestCase):
    def setUp(self, **kwargs):
        self.config = setUp(**kwargs)

    def tearDown(self):
        tearDown()

class TestMain(UnitTestBase):
    def required_settings(self):
        return {'sqlalchemy.url': 'sqlite://',
                'kotti.secret': 'dude'}

    def test_override_settings(self):
        class MyType(object):
            pass

        def my_configurator(conf):
            conf['kotti.base_includes'] = ''
            conf['kotti.available_types'] = [MyType]
            
        settings = self.required_settings()
        settings['kotti.configurators'] = [my_configurator]
        main({}, **settings)

        self.assertEqual(get_settings()['kotti.base_includes'], [])
        self.assertEqual(get_settings()['kotti.available_types'], [MyType])

    def test_persistent_settings(self):
        from kotti import get_version
        from kotti.resources import Settings
        session = DBSession()
        [settings] = session.query(Settings).all()
        self.assertEqual(settings.data, {'kotti.db_version': get_version()})
        self.assertEqual(get_settings()['kotti.db_version'], get_version())
        settings.data['foo.bar'] = u'baz'
        self.assertEqual(get_settings()['foo.bar'], u'baz')

    def test_persistent_settings_add_new(self):
        from kotti.resources import Settings
        session = DBSession()
        [settings] = session.query(Settings).all()
        data = {'foo.bar': u'spam', 'kotti.db_version': u'next'}
        new_settings = settings.copy(data)
        session.add(new_settings)
        self.assertEqual(get_settings()['foo.bar'], u'spam')
        self.assertEqual(get_settings()['kotti.db_version'], u'next')

class TestNode(UnitTestBase):
    def test_root_acl(self):
        root = get_root()

        # The root object has a persistent ACL set:
        self.assertEquals(
            root.__acl__[1:], [
                ('Allow', 'system.Everyone', ['view']),
                ('Allow', 'role:viewer', ['view']),
                ('Allow', 'role:editor', ['view', 'add', 'edit']),
                ('Allow', 'role:owner', ['view', 'add', 'edit', 'manage']),
                ])
        # Note how the first ACE is class-defined.  Users of the
        # 'admin' role will always have all permissions.  This is to
        # prevent lock-out.
        self.assertEquals(root.__acl__[:1], root._default_acl())

    def test_set_and_get_acl(self):
        root = get_root()

        # The __acl__ attribute of Nodes allows access to the mapped
        # '_acl' property:
        del root.__acl__
        self.assertRaises(AttributeError, root._get_acl)

        root.__acl__ = [['Allow', 'system.Authenticated', ['edit']]]
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'role:admin', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['edit']),
                ])

        root.__acl__ = [
            ('Allow', 'system.Authenticated', ['view']),
            ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
            ]
        
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'role:admin', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['view']),
                ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
                ])

        # We can reorder the ACL:
        first, second = root.__acl__[1:]
        root.__acl__ = [second, first]
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'role:admin', ALL_PERMISSIONS),
                ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['view']),
                ])
        session = DBSession()
        session.flush() # try serialization
        self.assertEquals(root.__acl__[1:], [second, first])

        root._del_acl()
        self.assertRaises(AttributeError, root._del_acl)

    def test_unique_constraint(self):
        # Try to add two children with the same name to the root node:
        session = DBSession()
        root = get_root()
        session.add(Node(name=u'child1', parent=root))
        session.add(Node(name=u'child1', parent=root))
        self.assertRaises(IntegrityError, session.flush)

    def test_container_methods(self):
        session = DBSession()

        # Test some of Node's container methods:
        root = get_root()
        self.assertEquals(root.keys(), [])

        child1 = Node(name=u'child1', parent=root)
        session.add(child1)
        self.assertEquals(root.keys(), [u'child1'])
        self.assertEquals(root[u'child1'], child1)

        del root[u'child1']
        self.assertEquals(root.keys(), [])        

        # When we delete a parent node, all its child nodes will be
        # released as well:
        root[u'child2'] = Node()
        root[u'child2'][u'subchild'] = Node()
        self.assertEquals(
            session.query(Node).filter(Node.name == u'subchild').count(), 1)
        del root[u'child2']
        self.assertEquals(
            session.query(Node).filter(Node.name == u'subchild').count(), 0)

        # We can pass a tuple as the key to more efficiently reach
        # down to child objects:
        root[u'child3'] = Node()
        subchild33 = Node(name=u'subchild33', parent=root[u'child3'])
        session.add(subchild33)
        self.assertTrue(
            root[u'child3', u'subchild33'] is root[u'child3'][u'subchild33'])
        self.assertTrue(
            root[(u'child3', u'subchild33')] is subchild33)
        self.assertRaises(KeyError, root.__getitem__, (u'child3', u'bad-name'))
        del root[u'child3']

        # Overwriting an existing Node is an error; first delete manually!
        child4 = Node(name=u'child4', parent=root)
        session.add(child4)
        self.assertEquals(root.keys(), [u'child4'])

        child44 = Node(name=u'child4')
        session.add(child44)
        root[u'child4'] = child44
        self.assertRaises(SQLAlchemyError, session.flush)
        
    def test_node_copy(self):
        # Test some of Node's container methods:
        root = get_root()
        copy_of_root = root.copy(name=u'copy_of_root')
        self.assertEqual(copy_of_root.name, u'copy_of_root')
        self.assertEqual(root.name, u'')

    def test_annotations_mutable(self):
        root = get_root()
        session = DBSession()
        root.annotations['foo'] = u'bar'
        self.assertTrue(root in session.dirty)
        del root.annotations['foo']

    def test_annotations_coerce_fail(self):
        root = get_root()
        self.assertRaises(ValueError, setattr, root, 'annotations', [])

class TestSecurity(UnitTestBase):
    def test_root_default(self):
        root = get_root()
        self.assertEqual(list_groups('admin', root), ['role:admin'])
        self.assertEqual(list_groups_raw(u'admin', root), set([]))

    def test_empty(self):
        root = get_root()
        self.assertEqual(list_groups('bob', root), [])

    def test_simple(self):
        root = get_root()
        set_groups('bob', root, ['role:editor'])
        self.assertEqual(
            list_groups('bob', root), ['role:editor'])
        self.assertEqual(
            list_groups_raw(u'bob', root), set(['role:editor']))

    def test_not_a_node(self):
        self.assertEqual(list_groups_raw(u'bob', object()), set())

    def test_overwrite_and_delete(self):
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
        session = DBSession()
        root = get_root()
        child = root[u'child'] = Node()
        session.flush()

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
        session = DBSession()
        root = get_root()
        child = root[u'child'] = Node()
        grandchild = child[u'grandchild'] = Node()
        session.flush()
        
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
        session = DBSession()
        root = get_root()
        child = root[u'child'] = Node()
        session.flush()

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
        session = DBSession()
        root = get_root()
        child = root[u'child'] = Node()
        session.flush()

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
        session = DBSession()
        root = get_root()
        child = root[u'child'] = Node()
        session.flush()

        # We set a local group on child and delete child.  We then
        # expect the LocalGroup entry to have been deleted from the
        # database:
        self.assertEqual(session.query(LocalGroup).count(), 0)
        set_groups('group:bobsgroup', child, ['role:editor'])
        self.assertEqual(session.query(LocalGroup).count(), 1)
        del root[u'child']
        session.flush()
        self.assertEqual(session.query(LocalGroup).count(), 0)

class TestPrincipals(UnitTestBase):
    def get_principals(self):
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
        self.make_bob()

        session = DBSession()
        root = get_root()
        child = root[u'child'] = Node()
        session.flush()

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

class TestEvents(UnitTestBase):
    def setUp(self):
        # We're jumping through some hoops to allow the event handlers
        # to be able to do 'pyramid.threadlocal.get_current_request'
        # and 'authenticated_userid'.
        registry = Registry('testing')
        request = DummyRequest()
        request.registry = registry
        super(TestEvents, self).setUp(registry=registry, request=request)
        self.config.include('kotti.events')

    def test_owner(self):
        session = DBSession()
        self.config.testing_securitypolicy(userid=u'bob')
        root = get_root()
        child = root[u'child'] = Content()
        session.flush()
        self.assertEqual(child.owner, u'bob')
        self.assertEqual(list_groups(u'bob', child), [u'role:owner'])

        clear_cache()
        # The event listener does not set the role again for subitems:
        grandchild = child[u'grandchild'] = Content()
        session.flush()
        self.assertEqual(grandchild.owner, u'bob')
        self.assertEqual(list_groups(u'bob', grandchild), [u'role:owner'])
        self.assertEqual(len(list_groups_raw(u'bob', grandchild)), 0)

    def test_sqlalchemy_events(self):
        from kotti import events

        insert_events = []
        def insert(event):
            insert_events.append(event)
        update_events = []
        def update(event):
            update_events.append(event)
        delete_events = []
        def delete(event):
            delete_events.append(event)

        lis = events.objectevent_listeners
        lis[(events.ObjectInsert, None)].append(insert)
        lis[(events.ObjectUpdate, None)].append(update)
        lis[(events.ObjectDelete, None)].append(delete)

        root = get_root()
        child = root[u'child'] = Content()
        DBSession.flush()
        self.assertEqual(
            (len(insert_events), len(update_events), len(delete_events)),
            (1, 0, 0))
        self.assertEqual(insert_events[0].object, child)

        child.title = u"Bar"
        DBSession.flush()
        self.assertEqual(
            (len(insert_events), len(update_events), len(delete_events)),
            (1, 1, 0))
        self.assertEqual(update_events[0].object, child)

        DBSession.delete(child)
        DBSession.flush()
        self.assertEqual(
            (len(insert_events), len(update_events), len(delete_events)),
            (1, 1, 1))
        self.assertEqual(delete_events[0].object, child)

@contextmanager
def contents_addable():
    # Allow Nodes to be added to documents:
    save_node_type_info = Content.type_info.copy()
    Content.type_info.addable_to = [u'Document']
    Content.type_info.add_view = u'add_document'
    get_settings()['kotti.available_types'].append(Content)
    try:
        yield
    finally:
        get_settings()['kotti.available_types'].pop()
        Content.type_info = save_node_type_info

class TestAddableTypes(UnitTestBase):
    def test_view_permitted_yes(self):
        self.config.testing_securitypolicy(permissive=True)
        self.config.include('kotti.views.edit')
        root = DBSession().query(Node).get(1)
        request = DummyRequest()
        self.assertEquals(Document.type_info.addable(root, request), True)

    def test_view_permitted_no(self):
        self.config.testing_securitypolicy(permissive=False)
        self.config.include('kotti.views.edit')
        root = DBSession().query(Node).get(1)
        request = DummyRequest()
        self.assertEquals(Document.type_info.addable(root, request), False)

    def test_multiple_types(self):
        from kotti.views.util import addable_types
        # Test a scenario where we may add multiple types to a folder:
        root = get_root()
        request = DummyRequest()

        with contents_addable():
            # We should be able to add both Nodes and Documents now:
            possible_parents, possible_types = addable_types(root, request)
            self.assertEqual(len(possible_parents), 1)
            self.assertEqual(possible_parents[0]['factories'],
                             [Document, Content])

            document_info, node_info = possible_types
            self.assertEqual(document_info['factory'], Document)
            self.assertEqual(node_info['factory'], Content)
            self.assertEqual(document_info['nodes'], [root])
            self.assertEqual(node_info['nodes'], [root])

    def test_multiple_parents_and_types(self):
        from kotti.views.util import addable_types
        # A scenario where we can add multiple types to multiple folders:
        root = get_root()
        request = DummyRequest()

        with contents_addable():
            # We should be able to add both to the child and to the parent:
            child = root['child'] = Document(title=u"Child")
            possible_parents, possible_types = addable_types(child, request)
            child_parent, root_parent = possible_parents
            self.assertEqual(child_parent['node'], child)
            self.assertEqual(root_parent['node'], root)
            self.assertEqual(child_parent['factories'], [Document, Content])
            self.assertEqual(root_parent['factories'], [Document, Content])

            document_info, node_info = possible_types
            self.assertEqual(document_info['factory'], Document)
            self.assertEqual(node_info['factory'], Content)
            self.assertEqual(document_info['nodes'], [child, root])
            self.assertEqual(node_info['nodes'], [child, root])

class TestNodeEdit(UnitTestBase):
    def test_single_choice(self):
        from kotti.views.edit import add_node

        # The view should redirect straight to the add form if there's
        # only one choice of parent and type:
        root = get_root()
        request = DummyRequest()
        
        response = add_node(root, request)
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location,
                         'http://example.com/@@add_document')

    def test_order_of_addable_parents(self):
        from kotti.views.edit import add_node
        # The 'add_node' view sorts the 'possible_parents' returned by
        # 'addable_types' so that the parent comes first if the
        # context we're looking at does not have any children yet.
        root = get_root()
        request = DummyRequest()

        with contents_addable():
            # The child Document does not contain any other Nodes, so it's
            # second in the 'possible_parents' list returned by 'node_add':
            child = root['child'] = Document(title=u"Child")
            info = add_node(child, request)
            first_parent, second_parent = info['possible_parents']
            self.assertEqual(first_parent['node'], root)
            self.assertEqual(second_parent['node'], child)

            # Now we add a grandchild and see that this behaviour changes:
            child['grandchild'] = Document(title=u"Grandchild")
            info = add_node(child, request)
            first_parent, second_parent = info['possible_parents']
            self.assertEqual(first_parent['node'], child)
            self.assertEqual(second_parent['node'], root)

class TestNodeMove(UnitTestBase):
    def test_paste_without_edit_permission(self):
        from kotti.views.edit import move_node
        root = DBSession().query(Node).get(1)
        request = DummyRequest()
        request.params['paste'] = u'on'
        self.config.testing_securitypolicy(permissive=False)

        # We need to have the 'edit' permission on the original object
        # to be able to cut and paste:
        request.session['kotti.paste'] = (1, 'cut')
        self.assertRaises(Forbidden, move_node, root, request)

        # We don't need 'edit' permission if we're just copying:
        request.session['kotti.paste'] = (1, 'copy')
        response = move_node(root, request)
        self.assertEqual(response.status, '302 Found')

    def test_rename_to_empty_name(self):
        from kotti.views.edit import move_node
        root = DBSession().query(Node).get(1)
        child = root['child'] = Document(title=u"Child")
        request = DummyRequest()
        request.params['rename'] = u'on'
        request.params['name'] = u''
        request.params['title'] = u'foo'
        move_node(child, request)
        self.assertEqual(request.session.pop_flash('error'),
                         [u'Name and title are required.'])

class TestNodeShare(UnitTestBase):
    @staticmethod
    def add_some_principals():
        P = get_principals()
        P[u'bob'] = {'name': u'bob', 'title': u"Bob"}
        P[u'frank'] = {'name': u'frank', 'title': u"Frank"}
        P[u'group:bobsgroup'] = {
            'name': u'group:bobsgroup', 'title': u"Bob's Group"}
        P[u'group:franksgroup'] = {
            'name': u'group:franksgroup', 'title': u"Frank's Group"}

    def test_roles(self):
        # The 'share_node' view will return a list of available roles
        # as defined in 'kotti.security.SHARING_ROLES'
        from kotti.views.users import share_node
        from kotti.security import SHARING_ROLES
        root = get_root()
        request = DummyRequest()
        self.assertEqual(
            [r.name for r in share_node(root, request)['available_roles']],
            SHARING_ROLES)

    def test_search(self):
        from kotti.views.users import share_node
        root = get_root()
        request = DummyRequest()
        P = get_principals()
        self.add_some_principals()

        # Search for "Bob", which will return both the user and the
        # group, both of which have no roles:
        request.params['search'] = u''
        request.params['query'] = u'Bob'
        entries = share_node(root, request)['entries']
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0][0], P['bob'])
        self.assertEqual(entries[0][1], ([], []))
        self.assertEqual(entries[1][0], P['group:bobsgroup'])
        self.assertEqual(entries[1][1], ([], []))

        # We make Bob an Editor in this context, and Bob's Group
        # becomes global Admin:
        set_groups(u'bob', root, [u'role:editor'])
        P[u'group:bobsgroup'].groups = [u'role:admin']
        entries = share_node(root, request)['entries']
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0][0], P['bob'])
        self.assertEqual(entries[0][1], ([u'role:editor'], []))
        self.assertEqual(entries[1][0], P['group:bobsgroup'])
        self.assertEqual(entries[1][1], ([u'role:admin'], [u'role:admin']))

        # A search that doesn't return any items will still include
        # entries with existing local roles:
        request.params['query'] = u'Weeee'
        entries = share_node(root, request)['entries']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][0], P[u'bob'])
        self.assertEqual(entries[0][1], ([u'role:editor'], []))
        self.assertEqual(request.session.pop_flash('notice'),
                         [u'No users or groups found.'])

        # It does not, however, include entries that have local group
        # assignments only:
        set_groups(u'frank', root, [u'group:franksgroup'])
        request.params['query'] = u'Weeee'
        entries = share_node(root, request)['entries']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][0], P['bob'])

    def test_apply(self):
        from kotti.views.users import share_node
        root = get_root()
        request = DummyRequest()
        self.add_some_principals()

        request.params['apply'] = u''
        share_node(root, request)
        self.assertEqual(request.session.pop_flash('notice'),
                         [u'No changes made.'])
        self.assertEqual(list_groups('bob', root), [])
        set_groups('bob', root, ['role:special'])

        request.params['role::bob::role:owner'] = u'1'
        request.params['role::bob::role:editor'] = u'1'
        request.params['orig-role::bob::role:owner'] = u''
        request.params['orig-role::bob::role:editor'] = u''

        share_node(root, request)
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Your changes have been saved.'])
        self.assertEqual(
            set(list_groups('bob', root)),
            set(['role:owner', 'role:editor', 'role:special'])
            )

        # We cannot set a role that's not displayed, even if we forged
        # the request:
        request.params['role::bob::role:admin'] = u'1'
        request.params['orig-role::bob::role:admin'] = u''
        self.assertRaises(Forbidden, share_node, root, request)
        self.assertEqual(
            set(list_groups('bob', root)),
            set(['role:owner', 'role:editor', 'role:special'])
            )

class TestUserManagement(UnitTestBase):
    def test_roles(self):
        from kotti.views.users import users_manage
        from kotti.security import USER_MANAGEMENT_ROLES
        root = get_root()
        request = DummyRequest()
        self.assertEqual(
            [r.name for r in users_manage(root, request)['available_roles']],
            USER_MANAGEMENT_ROLES)

    def test_search(self):
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

class TestTemplateAPI(UnitTestBase):
    def _make(self, context=None, request=None, id=1, **kwargs):
        from kotti.views.util import TemplateAPI
        if context is None:
            session = DBSession()
            context = session.query(Node).get(id)
        if request is None:
            request = DummyRequest()
        return TemplateAPI(context, request, **kwargs)

    def _create_contents(self, root):
        # root -> a --> aa
        #         |
        #         \ --> ab
        #         |
        #         \ --> ac --> aca
        #               |
        #               \ --> acb
        a = root['a'] = Content()
        aa = root['a']['aa'] = Content()
        ab = root['a']['ab'] = Content()
        ac = root['a']['ac'] = Content()
        aca = ac['aca'] = Content()
        acb = ac['acb'] = Content()
        return a, aa, ab, ac, aca, acb

    def test_page_title(self):
        api = self._make()
        api.context.title = u"Hello, world!"
        self.assertEqual(api.page_title, u"Hello, world! - Hello, world!")

        api = self._make()
        api.context.title = u"Hello, world!"
        api.site_title = u"Wasnhierlos"
        self.assertEqual(api.page_title, u"Hello, world! - Wasnhierlos")

    def test_list_children(self):
        api = self._make() # the default context is root
        root = api.context
        self.assertEquals(len(api.list_children(root)), 0)

        # Now try it on a little graph:
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        self.assertEquals(api.list_children(root), [a])
        self.assertEquals(api.list_children(a), [aa, ab, ac])
        self.assertEquals(api.list_children(aca), [])

        # The 'list_children_go_up' function works slightly different:
        # it returns the parent's children if the context doesn't have
        # any.  Only the third case is gonna be different:
        self.assertEquals(api.list_children_go_up(root), (root, [a]))
        self.assertEquals(api.list_children_go_up(a), (a, [aa, ab, ac]))
        self.assertEquals(api.list_children_go_up(aca), (ac, [aca, acb]))

    def test_root(self):
        api = self._make()
        root = api.context
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        self.assertEquals(self._make().root, root)
        self.assertEquals(self._make(acb).root, root)

    def test_edit_links(self):
        api = self._make()
        self.assertEqual(api.edit_links, [
            ViewLink('edit'),
            ViewLink('add'),
            ViewLink('move'),
            ViewLink('share'),
            ])

        # Edit links are controlled through
        # 'root.type_info.edit_links' and the permissions that guard
        # these:
        class MyLink(ViewLink):
            permit = True
            def permitted(self, context, request):
                return self.permit
        open_link = MyLink('open')
        secure_link = MyLink('secure')
        secure_link.permit = False

        root = api.root
        root.type_info = root.type_info.copy(
            edit_links=[open_link, secure_link])
        api = self._make()
        self.assertEqual(api.edit_links, [open_link])

    def test_context_links(self):
        # 'context_links' returns a two-tuple of the form (siblings,
        # children), where the URLs point to edit pages:
        root = self._make().root
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        api = self._make(ac)
        siblings, children = api.context_links

        # Note how siblings don't include self (ac)
        self.assertEqual(
            [item['node'] for item in siblings],
            [aa, ab]
            )
        self.assertEqual(
            [item['node'] for item in children],
            [aca, acb]
            )

    def test_breadcrumbs(self):
        root = self._make().root
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        api = self._make(acb)
        breadcrumbs = api.breadcrumbs
        self.assertEqual(
            [item['node'] for item in breadcrumbs],
            [root, a, ac, acb]
            )

    def test_getitem(self):
        api = self._make()
        self.assertRaises(KeyError, api.__getitem__, 'no-exit')

    def test_bare(self):
        # By default, no "bare" templates are used:
        api = self._make()
        self.assertEqual(api.bare, None)

        # We can ask for "bare" templates explicitely:
        api = self._make(bare=True)
        self.assertEqual(api.bare, True)
        self.assertEqual(api.macro_templates['master_view'], api.BARE_TMPL)

        # An XHR request will always result in bare master templates:
        request = DummyRequest()
        request.is_xhr = True
        api = self._make(request=request)
        self.assertEqual(api.bare, True)

        # unless overridden:
        api = self._make(request=request, bare=False)
        self.assertEqual(api.bare, False)

    def test_slots(self):
        from kotti.views.slots import register, RenderAboveContent
        def render_something(context, request):
            return u"Hello, %s!" % context.title
        register(RenderAboveContent, None, render_something)

        api = self._make()
        self.assertEqual(api.slots.abovecontent, [u'Hello, My Site!'])

        # Slot renderers may also return lists:
        def render_a_list(context, request):
            return [u"a", u"list"]
        register(RenderAboveContent, None, render_a_list)
        api = self._make()
        self.assertEqual(
            api.slots.abovecontent,
            [u'Hello, My Site!', u'a', u'list']
            )

        self.assertRaises(
            AttributeError,
            getattr, api.slots, 'foobar'
            )

    def test_slots_only_rendered_when_accessed(self):
        from kotti.views.slots import register, RenderAboveContent

        called = []
        def render_something(context, request):
            called.append(True)
        register(RenderAboveContent, None, render_something)
        
        api = self._make()
        api.slots.belowcontent
        self.assertFalse(called)

        api.slots.abovecontent
        self.assertEquals(len(called), 1)
        api.slots.abovecontent
        self.assertEquals(len(called), 1)

    def test_slots_render_local_navigation(self):
        from kotti.views.slots import render_local_navigation
        root = DBSession().query(Node).get(1)
        request = DummyRequest()
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        self.assertEqual(render_local_navigation(root, request), None)
        self.assertNotEqual(render_local_navigation(a, request), None)
        self.assertEqual("ab" in render_local_navigation(a, request), True)
        ab.in_navigation = False
        self.assertEqual("ab" in render_local_navigation(a, request), False)

    def test_format_datetime(self):
        import datetime
        from babel.dates import format_datetime
        from babel.core import UnknownLocaleError
        api = self._make()
        first = datetime.datetime(2012, 1, 1, 0)
        self.assertEqual(
            api.format_datetime(first),
            format_datetime(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_datetime(first, format='short'),
            format_datetime(first, format='short', locale='en'),
            )
        api.locale_name = 'unknown'
        self.assertRaises(UnknownLocaleError, api.format_datetime, first)

    def test_format_date(self):
        import datetime
        from babel.dates import format_date
        from babel.core import UnknownLocaleError
        api = self._make()
        first = datetime.date(2012, 1, 1)
        self.assertEqual(
            api.format_date(first),
            format_date(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_date(first, format='short'),
            format_date(first, format='short', locale='en'),
            )
        api.locale_name = 'unknown'
        self.assertRaises(UnknownLocaleError, api.format_date, first)

    def test_format_time(self):
        import datetime
        from babel.dates import format_time
        from babel.core import UnknownLocaleError
        api = self._make()
        first = datetime.time(23, 59)
        self.assertEqual(
            api.format_time(first),
            format_time(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_time(first, format='short'),
            format_time(first, format='short', locale='en'),
            )
        api.locale_name = 'unknown'
        self.assertRaises(UnknownLocaleError, api.format_time, first)

    def test_render_view(self):
        from pyramid.response import Response
        def first_view(context, request):
            return Response(u'first')
        def second_view(context, request):
            return Response(u'second')
        self.config.add_view(first_view, name='')
        self.config.add_view(second_view, name='second')
        api = self._make()
        self.assertEqual(api.render_view(), u'first')
        self.assertEqual(api.render_view('second'), u'second')
        self.assertEqual(
            api.render_view(context=api.context, request=api.request), u'first')

    def test_get_type(self):
        from kotti.resources import Document
        api = self._make()
        self.assertEqual(api.get_type('Document'), Document)
        self.assertEqual(api.get_type('NoExist'), None)

class TestViewUtil(UnitTestBase):
    def test_add_renderer_globals_json(self):
        from kotti.views.util import add_renderer_globals

        event = {'renderer_name': 'json'}
        add_renderer_globals(event)
        self.assertEqual(event.keys(), ['renderer_name'])

    def test_add_renderer_globals_request_has_template_api(self):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        request.template_api = template_api = object()
        event = {'request': request, 'renderer_name': 'foo'}
        add_renderer_globals(event)
        self.assertTrue(event['api'] is template_api)

    def test_add_renderer_globals(self):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        event = {
            'request': request,
            'context': object(),
            'renderer_name': 'foo',
            }
        add_renderer_globals(event)
        self.assertTrue('api' in event)

class TestUtil(UnitTestBase):
    def test_title_to_name(self):
        from kotti.views.util import title_to_name
        self.assertEqual(title_to_name(u'Foo Bar'), u'foo-bar')

    def test_disambiguate_name(self):
        from kotti.views.util import disambiguate_name
        self.assertEqual(disambiguate_name(u'foo'), u'foo-1')
        self.assertEqual(disambiguate_name(u'foo-3'), u'foo-4')

    def test_ensure_view_selector(self):
        from kotti.views.util import ensure_view_selector
        wrapper = ensure_view_selector(None)
        request = DummyRequest(path='/edit')
        # Ignoring the result since it's not useful with DummyRequest.
        # We check that path_info was set accordingly though:
        wrapper(None, request)
        self.assertEqual(request.path_info, u'/@@edit')

class TestRequestCache(UnitTestBase):
    def setUp(self):
        from kotti.util import request_cache

        registry = Registry('testing')
        request = DummyRequest()
        request.registry = registry
        super(TestRequestCache, self).setUp(registry=registry, request=request)
        self.cache_decorator = request_cache

    def test_it(self):
        called = []

        @self.cache_decorator(lambda a, b: (a, b))
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 1)
        my_fun(2, 1)
        self.assertEqual(len(called), 2)

        clear_cache()
        my_fun(1, 2)
        self.assertEqual(len(called), 3)

    def test_dont_cache(self):
        from kotti.util import DontCache
        called = []

        def dont_cache(a, b):
            raise DontCache

        @self.cache_decorator(dont_cache)
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 2)

class TestLRUCache(TestRequestCache):
    def setUp(self):
        from kotti.util import lru_cache
        
        super(TestLRUCache, self).setUp()
        self.cache_decorator = lru_cache

def setUpFunctional(global_config=None, **settings):
    import wsgi_intercept.zope_testbrowser

    _settings = {
        'sqlalchemy.url': testing_db_url(),
        'kotti.secret': 'secret',
        'kotti.site_title': 'Website des Kottbusser Tors', # for mailing
        'mail.default_sender': 'kotti@localhost',
        }
    _settings.update(settings)

    host, port = BASE_URL.split(':')[-2:]
    app = main({}, **_settings)
    wsgi_intercept.add_wsgi_intercept(host[2:], int(port), lambda: app)

    return dict(Browser=wsgi_intercept.zope_testbrowser.WSGI_Browser)

def registerDummyMailer():
    from pyramid_mailer.mailer import DummyMailer
    mailer = DummyMailer()
    _inject_mailer.append(mailer)
    return mailer
