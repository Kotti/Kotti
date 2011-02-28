from contextlib import contextmanager
import unittest

import transaction
from sqlalchemy.exc import IntegrityError
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.config import DEFAULT_RENDERERS
from pyramid.exceptions import Forbidden
from pyramid.registry import Registry
from pyramid.security import ALL_PERMISSIONS
from pyramid import testing

import kotti
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.resources import initialize_sql
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
from kotti.util import clear_request_cache
from kotti import main

BASE_URL = 'http://localhost:6543'

## Unit tests

def _initTestingDB():
    from sqlalchemy import create_engine
    session = initialize_sql(create_engine('sqlite://'))
    return session

def setUp(**kwargs):
    tearDown()
    kotti.configuration.secret = 'secret'
    _initTestingDB()
    config = testing.setUp(**kwargs)
    for name, renderer in DEFAULT_RENDERERS:
        config.add_renderer(name, renderer)
    transaction.begin()
    return config

def tearDown():
    transaction.abort()
    testing.tearDown()

class UnitTestBase(unittest.TestCase):
    def setUp(self, **kwargs):
        self.config = setUp(**kwargs)

    def tearDown(self):
        tearDown()

class TestMain(UnitTestBase):
    def setUp(self, **kwargs):
        super(TestMain, self).setUp(**kwargs)
        self.save_configuration = kotti.configuration.copy()

    def tearDown(self):
        super(TestMain, self).tearDown()
        kotti.configuration.clear()
        kotti.configuration.update(self.save_configuration)

    def required_settings(self):
        return {'sqlalchemy.url': 'sqlite://',
                'kotti.secret': 'dude'}

    def test_override_settings(self):
        class MyType(object):
            pass

        def my_configurator(conf):
            conf['kotti.includes'] = ''
            conf['kotti.available_types'] = [MyType]
            
        settings = self.required_settings()
        settings['kotti.configurators'] = [my_configurator]
        main({}, **settings)

        self.assertEqual(kotti.configuration['kotti.includes'], [])
        self.assertEqual(kotti.configuration['kotti.available_types'], [MyType])

class TestNode(UnitTestBase):
    def test_root_acl(self):
        session = DBSession()
        root = session.query(Node).get(1)

        # The root object has a persistent ACL set:
        self.assertEquals(
            root.__acl__[1:], [
                ('Allow', 'system.Authenticated', ['view']),
                ('Allow', 'role:viewer', ['view']),
                ('Allow', 'role:editor', ['view', 'add', 'edit']),
                ('Allow', 'role:owner', ['view', 'add', 'edit', 'manage']),
                ])
        # Note how the first ACE is class-defined.  Users of the
        # 'admin' role will always have all permissions.  This is to
        # prevent lock-out.
        self.assertEquals(root.__acl__[:1], root._default_acl())

    def test_set_and_get_acl(self):
        session = DBSession()
        root = session.query(Node).get(1)

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
        session.flush() # try serialization
        self.assertEquals(root.__acl__[1:], [second, first])

        root._del_acl()
        self.assertRaises(AttributeError, root._del_acl)

    def test_unique_constraint(self):
        session = DBSession()

        # Try to add two children with the same name to the root node:
        root = session.query(Node).get(1)
        session.add(Node(name=u'child1', parent=root))
        session.add(Node(name=u'child1', parent=root))
        self.assertRaises(IntegrityError, session.flush)

    def test_container_methods(self):
        session = DBSession()

        # Test some of Node's container methods:
        root = session.query(Node).get(1)
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

    def test_node_copy(self):
        # Test some of Node's container methods:
        root = DBSession().query(Node).get(1)
        copy_of_root = root.copy(name=u'copy_of_root')
        self.assertEqual(copy_of_root.name, u'copy_of_root')
        self.assertEqual(root.name, u'')

class TestSecurity(UnitTestBase):
    def test_root_default(self):
        session = DBSession()
        root = session.query(Node).get(1)
        self.assertEqual(list_groups('admin', root), ['role:admin'])
        self.assertEqual(list_groups_raw('admin', root), set([]))

    def test_empty(self):
        session = DBSession()
        root = session.query(Node).get(1)
        self.assertEqual(list_groups(root, 'bob'), [])

    def test_simple(self):
        session = DBSession()
        root = session.query(Node).get(1)
        set_groups('bob', root, ['role:editor'])
        self.assertEqual(
            list_groups('bob', root), ['role:editor'])
        self.assertEqual(
            list_groups_raw('bob', root), ['role:editor'])

    def test_inherit(self):
        session = DBSession()
        root = session.query(Node).get(1)
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
            list_groups_raw('bob', child), ['group:somegroup'])

    @staticmethod
    def add_some_groups():
        session = DBSession()
        root = session.query(Node).get(1)
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
        session = DBSession()
        root = session.query(Node).get(1)
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
        root = session.query(Node).get(1)
        child = root[u'child'] = Node()
        session.flush()

        request = testing.DummyRequest()
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
        
        request = testing.DummyRequest()
        self.assertEqual(
            list_groups_callback(u'bob', request), [])
        self.assertEqual(
            list_groups_callback(u'group:bobsgroup', request), None)

    def test_principals_with_local_roles(self):
        session = DBSession()
        root = session.query(Node).get(1)
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
            set(principals_with_local_roles(root)),
            set(['bob', 'group:franksgroup'])
            )

    def test_map_principals_with_local_roles(self):
        self.test_principals_with_local_roles()
        session = DBSession()
        root = session.query(Node).get(1)
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
        hashed = self.get_principals().hash_password(u'secret')
        self.assertEqual(admin.password, hashed)
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
        self.assertEqual(users.search(), [])

    def test_groups_from_users(self):
        self.make_bob()

        session = DBSession()
        root = session.query(Node).get(1)
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

    def test_hash_password(self):
        password = u"secret"
        hash_password = self.get_principals().hash_password

        # For 'hash_password' to work, we need to set a secret:
        kotti.configuration.secret = 'there is no secret'
        hashed = hash_password(password)
        self.assertEqual(hashed, hash_password(password))
        kotti.configuration.secret = 'different'
        self.assertNotEqual(hashed, hash_password(password))        
        del kotti.configuration.secret

    def test_bobs_hashed_password(self):
        bob = self.make_bob()
        hash_password = self.get_principals().hash_password
        self.assertEqual(bob.password, hash_password(u'secret'))

        # When we set the 'password' attribute directly, we have to do
        # the hashing ourselves.
        bob.password = u'hashed secret'
        self.assertEqual(bob.password, u'hashed secret')

    def test_active(self):
        bob = self.make_bob()
        self.assertEqual(bob.active, True)
        bob.active = False
        self.assertEqual(bob.active, False)

    def test_login(self):
        from kotti.views.login import login
        request = testing.DummyRequest()

        # No login attempt:
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('success'), [])
        self.assertEqual(request.session.pop_flash('error'), [])

        # Attempt to log in before Bob exists:
        request.params['submitted'] = u'on'
        request.params['login'] = u'bob'
        request.params['password'] = u'secret'
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('success'), [])
        self.assertEqual(request.session.pop_flash('error'),
                         [u'Login failed.'])

        # Make Bob and do it again:
        bob = self.make_bob()
        result = login(None, request)
        self.assertEqual(result.status, '302 Found')
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Welcome, Bob Dabolina!'])
        self.assertEqual(request.session.pop_flash('error'), [])

        # Log in with e-mail:
        request.params['login'] = u'bob@dabolina.com'
        result = login(None, request)
        self.assertEqual(result.status, '302 Found')
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Welcome, Bob Dabolina!'])

        # Deactive Bob, logging in is no longer possible:
        bob.active = False
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('error'),
                         [u'Login failed.'])

        # If Bob has a 'confirm_token' set, logging in is not possible:
        bob.active = True
        bob.confirm_token = u'token'
        result = login(None, request)
        self.assert_(isinstance(result, dict))
        self.assertEqual(request.session.pop_flash('error'),
                         [u'Login failed.'])

        # Allow logging in again:
        bob.confirm_token = None
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
        request = testing.DummyRequest()
        request.registry = registry
        super(TestEvents, self).setUp(registry=registry, request=request)
        self.config.include('kotti.events')

    def test_owner(self):
        session = DBSession()
        self.config.testing_securitypolicy(userid=u'bob')
        root = session.query(Node).get(1)
        child = root[u'child'] = Node()
        session.flush()
        self.assertEqual(child.owner, u'bob')
        self.assertEqual(list_groups(u'bob', child), [u'role:owner'])

        clear_request_cache()
        # The event listener does not set the role again for subitems:
        grandchild = child[u'grandchild'] = Node()
        session.flush()
        self.assertEqual(grandchild.owner, u'bob')
        self.assertEqual(list_groups(u'bob', grandchild), [u'role:owner'])
        self.assertEqual(len(list_groups_raw(u'bob', grandchild)), 0)

class TestNodeView(UnitTestBase):
    def test_it(self):
        from kotti.views.view import view_node
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
        info = view_node(root, request)
        self.assertEqual(info['api'].context, root)

@contextmanager
def nodes_addable():
    # Allow Nodes to be added to documents:
    save_node_type_info = Node.type_info.copy()
    Node.type_info.addable_to = [u'Document']
    Node.type_info.add_view = u'add_document'
    kotti.configuration['kotti.available_types'].append(Node)
    try:
        yield
    finally:
        kotti.configuration['kotti.available_types'].pop()
        Node.type_info = save_node_type_info

class TestAddableTypes(UnitTestBase):
    def test_view_permitted_yes(self):
        self.config.testing_securitypolicy(permissive=True)
        self.config.include('kotti.views.edit')
        root = DBSession().query(Node).get(1)
        request = testing.DummyRequest()
        self.assertEquals(Document.type_info.addable(root, request), True)

    def test_view_permitted_no(self):
        self.config.testing_securitypolicy(permissive=False)
        self.config.include('kotti.views.edit')
        root = DBSession().query(Node).get(1)
        request = testing.DummyRequest()
        self.assertEquals(Document.type_info.addable(root, request), False)

    def test_multiple_types(self):
        from kotti.views.util import addable_types
        # Test a scenario where we may add multiple types to a folder:
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()

        with nodes_addable():
            # We should be able to add both Nodes and Documents now:
            possible_parents, possible_types = addable_types(root, request)
            self.assertEqual(len(possible_parents), 1)
            self.assertEqual(possible_parents[0]['factories'], [Document, Node])

            document_info, node_info = possible_types
            self.assertEqual(document_info['factory'], Document)
            self.assertEqual(node_info['factory'], Node)
            self.assertEqual(document_info['nodes'], [root])
            self.assertEqual(node_info['nodes'], [root])

    def test_multiple_parents_and_types(self):
        from kotti.views.util import addable_types
        # A scenario where we can add multiple types to multiple folders:
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()

        with nodes_addable():
            # We should be able to add both to the child and to the parent:
            child = root['child'] = Document(title=u"Child")
            possible_parents, possible_types = addable_types(child, request)
            child_parent, root_parent = possible_parents
            self.assertEqual(child_parent['node'], child)
            self.assertEqual(root_parent['node'], root)
            self.assertEqual(child_parent['factories'], [Document, Node])
            self.assertEqual(root_parent['factories'], [Document, Node])

            document_info, node_info = possible_types
            self.assertEqual(document_info['factory'], Document)
            self.assertEqual(node_info['factory'], Node)
            self.assertEqual(document_info['nodes'], [child, root])
            self.assertEqual(node_info['nodes'], [child, root])

class TestNodeEdit(UnitTestBase):
    def test_single_choice(self):
        from kotti.views.edit import add_node

        # The view should redirect straight to the add form if there's
        # only one choice of parent and type:
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
        
        response = add_node(root, request)
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location,
                         'http://example.com/@@add_document')

    def test_order_of_addable_parents(self):
        from kotti.views.edit import add_node
        # The 'add_node' view sorts the 'possible_parents' returned by
        # 'addable_types' so that the parent comes first if the
        # context we're looking at does not have any children yet.

        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()

        with nodes_addable():
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
        request = testing.DummyRequest()
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
        from kotti.views.edit import share_node
        from kotti.security import SHARING_ROLES
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
        self.assertEqual(
            [r.name for r in share_node(root, request)['available_roles']],
            SHARING_ROLES)

    def test_principals_to_roles(self):
        # 'share_node' returns a list of tuples of the form
        # (principal, (all, inherited)) akin to what
        # 'map_principals_with_local_roles' returns
        from kotti.views.edit import share_node
        TestSecurity.add_some_groups()
        session = DBSession()
        root = session.query(Node).get(1)
        child = root['child']
        grandchild = child['grandchild']
        request = testing.DummyRequest()
        P = get_principals()

        # If our principals do not exist in the database, nothing is
        # returned:
        ptr = share_node(root, request)['principals_to_roles']
        self.assertEqual(len(ptr), 0)

        self.add_some_principals()
        # For root:
        ptr = share_node(root, request)['principals_to_roles']
        self.assertEqual(len(ptr), 3)
        self.assertEqual(ptr[0], (P['bob'], (['group:bobsgroup'], [])))
        self.assertEqual(ptr[1][0], P['frank'])
        self.assertEqual(
            set(ptr[1][1][0]),
            set(['role:editor', 'group:franksgroup'])
            )
        self.assertEqual(ptr[1][1][1], ['role:editor'])
        self.assertEqual(ptr[2], (
            P['group:franksgroup'],
            (['role:editor'], []))
            )

        # For child:
        ptr = share_node(grandchild, request)['principals_to_roles']
        # Bob has only inherited groups here:
        self.assertEqual(set(ptr[0][1][0]), set(ptr[0][1][1]))
        # While Franksgroup has two local group assignments:
        franksgroup = ptr[3]
        self.assertEqual(
            set(franksgroup[1][0]),
            set(['role:owner', 'group:bobsgroup', 'role:editor'])
            )
        self.assertEqual(
            set(franksgroup[1][1]),
            set(['role:editor'])
            )

    def test_search(self):
        from kotti.views.edit import share_node
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
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
        self.assertEqual(request.session.pop_flash('info'),
                         [u'No users or groups found.'])

        # It does not, however, include entries that have local group
        # assignments only:
        set_groups(u'frank', root, [u'group:franksgroup'])
        request.params['query'] = u'Weeee'
        entries = share_node(root, request)['entries']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][0], P['bob'])

    def test_apply(self):
        from kotti.views.edit import share_node
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
        self.add_some_principals()

        request.params['apply'] = u''
        share_node(root, request)
        self.assertEqual(request.session.pop_flash('info'),
                         [u'No changes made.'])
        self.assertEqual(list_groups('bob', root), [])
        set_groups('bob', root, ['role:special'])

        request.params['role::bob::role:owner'] = u'1'
        request.params['role::bob::role:editor'] = u'1'
        request.params['orig-role::bob::role:owner'] = u''
        request.params['orig-role::bob::role:editor'] = u''

        share_node(root, request)
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Your changes have been applied.'])
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

class TestTemplateAPI(UnitTestBase):
    def _make(self, context=None, id=1):
        from kotti.views.util import TemplateAPIEdit

        if context is None:
            session = DBSession()
            context = session.query(Node).get(id)

        request = testing.DummyRequest()
        return TemplateAPIEdit(context, request)

    def _create_nodes(self, root):
        # root -> a --> aa
        #         |
        #         \ --> ab
        #         |
        #         \ --> ac --> aca
        #               |
        #               \ --> acb
        a = root['a'] = Node()
        aa = root['a']['aa'] = Node()
        ab = root['a']['ab'] = Node()
        ac = root['a']['ac'] = Node()
        aca = ac['aca'] = Node()
        acb = ac['acb'] = Node()
        return a, aa, ab, ac, aca, acb

    def test_page_title(self):
        from kotti.views.util import TemplateAPI
        edit_api = self._make()
        view_api = TemplateAPI(edit_api.context, edit_api.request)
        view_api.root.title = u"Hello, world!"
        self.assertEqual(edit_api.page_title, u" - Hello, world!")
        self.assertEqual(view_api.page_title, u"Hello, world! - Hello, world!")

    def test_list_children(self):
        api = self._make() # the default context is root
        root = api.context
        self.assertEquals(len(api.list_children(root)), 0)

        # Now try it on a little graph:
        a, aa, ab, ac, aca, acb = self._create_nodes(root)
        self.assertEquals(api.list_children(root), [a])
        self.assertEquals(api.list_children(a), [aa, ab, ac])
        self.assertEquals(api.list_children(aca), [])

        # The 'list_children_go_up' function works slightly different:
        # it returns the parent's children if the context doesn't have
        # any.  Only the third case is gonna be different:
        self.assertEquals(api.list_children_go_up(root), [a])
        self.assertEquals(api.list_children_go_up(a), [aa, ab, ac])
        self.assertEquals(api.list_children_go_up(aca), [aca, acb])

    def test_root(self):
        api = self._make()
        root = api.context
        a, aa, ab, ac, aca, acb = self._create_nodes(root)
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
        a, aa, ab, ac, aca, acb = self._create_nodes(root)
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
        a, aa, ab, ac, aca, acb = self._create_nodes(root)
        api = self._make(acb)
        breadcrumbs = api.breadcrumbs
        self.assertEqual(
            [item['node'] for item in breadcrumbs],
            [root, a, ac, acb]
            )

    def test_getitem(self):
        api = self._make()
        self.assertRaises(KeyError, api.__getitem__, 'no-exit')

class TestUtil(UnitTestBase):
    def test_title_to_name(self):
        from kotti.views.util import title_to_name
        self.assertEqual(title_to_name(u'Foo Bar'), u'foo-bar')

    def test_disambiguate_name(self):
        from kotti.views.util import disambiguate_name
        self.assertEqual(disambiguate_name(u'foo'), u'foo-1')
        self.assertEqual(disambiguate_name(u'foo-3'), u'foo-4')

class TestRequestCache(UnitTestBase):
    def setUp(self):
        registry = Registry('testing')
        request = testing.DummyRequest()
        request.registry = registry
        super(TestRequestCache, self).setUp(registry=registry, request=request)

    def test_it(self):
        from kotti.util import request_cache
        called = []

        @request_cache(lambda a, b: (a, b))
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 1)
        my_fun(2, 1)
        self.assertEqual(len(called), 2)

        clear_request_cache()
        my_fun(1, 2)
        self.assertEqual(len(called), 3)

    def test_dont_cache(self):
        from kotti.util import request_cache
        from kotti.util import DontCache
        called = []

        def dont_cache(a, b):
            raise DontCache

        @request_cache(dont_cache)
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 2)

## Functional tests

def setUpFunctional(global_config=None, **settings):
    import wsgi_intercept.zope_testbrowser

    configuration = {
        'sqlalchemy.url': 'sqlite://',
        'kotti.secret': 'secret',
        }

    host, port = BASE_URL.split(':')[-2:]
    app = main({}, **configuration)
    wsgi_intercept.add_wsgi_intercept(host[2:], int(port), lambda: app)

    return dict(Browser=wsgi_intercept.zope_testbrowser.WSGI_Browser)
