import unittest

import transaction
from sqlalchemy.exc import IntegrityError
from pyramid.config import DEFAULT_RENDERERS
from pyramid import security
from pyramid import testing

from kotti import configuration
from kotti.views.view import node_view
from kotti.views.edit import node_add
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.resources import initialize_sql
from kotti.security import ACE
from kotti import main

BASE_URL = 'http://localhost:6543'

## Unit tests

def _initTestingDB():
    from sqlalchemy import create_engine
    session = initialize_sql(create_engine('sqlite://'))
    return session

def setUp():
    tearDown()
    _initTestingDB()
    config = testing.setUp()
    for name, renderer in DEFAULT_RENDERERS:
        config.add_renderer(name, renderer)
    transaction.begin()
    return config

def tearDown():
    transaction.abort()
    testing.tearDown()

class UnitTestBase(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

class TestNode(UnitTestBase):
    def test_root_acl(self):
        session = DBSession()
        root = session.query(Node).get(1)

        # The root object has a persistent ACL set:
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'group:managers', security.ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ('view',)),
                ('Allow', 'group:editors', ('add', 'edit')),
            ])

        # Note how the last ACE is class-defined, that is, users in
        # the 'managers' group will have all permissions, always.
        # This is to prevent lock-out.
        self.assertEquals(root.__acl__[:-2], root._default_acl())

    def test_set_and_get_acl(self):
        session = DBSession()
        root = session.query(Node).get(1)

        # The __acl__ attribute of Nodes allows ACEs to be retrieved
        # and set:
        del root.__acl__
        self.assertRaises(AttributeError, root._get_acl)

        # When setting the ACL, we can also pass 3-tuples instead of
        # instances of ACE:
        root.__acl__ = [('Allow', 'system.Authenticated', ('edit',))]
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'group:managers', security.ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ('edit',))
                ])

        root.__acl__ = [
            ACE('Allow', 'system.Authenticated', ('view',)),
            ACE('Deny', 'system.Authenticated', ('view',)),
            ]
        
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'group:managers', security.ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ('view',)),
                ('Deny', 'system.Authenticated', ('view',)),
                ])

        # We can reorder the ACL:
        first, second = root.aces
        root.__acl__ = [second, first]
        self.assertEquals(
            root.__acl__, [
                ('Allow', 'group:managers', security.ALL_PERMISSIONS),
                ('Deny', 'system.Authenticated', ('view',)),
                ('Allow', 'system.Authenticated', ('view',)),
                ])
        self.assertEquals(root.aces, [second, first])
        self.assertEquals((first.position, second.position), (1, 0))

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

class TestNodeView(UnitTestBase):
    def test_it(self):
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
        info = node_view(root, request)
        self.assertEqual(info['api'].context, root)

class TestNodeEdit(UnitTestBase):
    def _make_node_addable(self):
        # Allow Nodes to be added to documents:
        self.save_node_type_info = Node.type_info.copy()
        Node.type_info.addable_to = [u'Document']
        Node.type_info.add_view = u'document_add'
        configuration['kotti.available_types'].append(Node)

    def _make_node_addable_cleanup(self):
        configuration['kotti.available_types'].pop()
        Node.type_info = self.save_node_type_info

    def test_single_choice(self):
        # The view should redirect straight:
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()
        
        response = node_add(root, request)
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location, 'http://example.com/document_add')

    def test_multiple_types(self):
        # Test a scenario where we may add multiple types to a folder:
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()

        self._make_node_addable()

        # We should be able to add both Nodes and documents now:
        info = node_add(root, request)
        (possible_parent,) = info['possible_parents']
        self.assertEqual(possible_parent['factories'], [Document, Node])

        document_info, node_info = info['possible_types']
        self.assertEqual(document_info['factory'], Document)
        self.assertEqual(node_info['factory'], Node)
        self.assertEqual(document_info['nodes'], [root])
        self.assertEqual(node_info['nodes'], [root])

        self._make_node_addable_cleanup()

    def test_multiple_parents_and_types(self):
        # A scenario where we can add multiple types to multiple folders:
        session = DBSession()
        root = session.query(Node).get(1)
        request = testing.DummyRequest()

        self._make_node_addable()

        # We should be able to add both to the child and to the parent:
        child = root['child'] = Document(title=u"Child")
        info = node_add(child, request)
        child_parent, root_parent = info['possible_parents']
        self.assertEqual(child_parent['node'], child)
        self.assertEqual(root_parent['node'], root)
        self.assertEqual(child_parent['factories'], [Document, Node])
        self.assertEqual(root_parent['factories'], [Document, Node])

        document_info, node_info = info['possible_types']
        self.assertEqual(document_info['factory'], Document)
        self.assertEqual(node_info['factory'], Node)
        self.assertEqual(document_info['nodes'], [child, root])
        self.assertEqual(node_info['nodes'], [child, root])

        self._make_node_addable_cleanup()

class TestTemplateAPI(UnitTestBase):
    def _make(self, context=None, id=1):
        from kotti.views import TemplateAPI

        if context is None:
            session = DBSession()
            context = session.query(Node).get(id)

        request = testing.DummyRequest()
        return TemplateAPI(context, request)

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

    def test_list_children(self):
        api = self._make() # the default context is root
        root = api.context
        self.assertEquals(len(api.list_children(root)), 0)

        # Now try it on a little graph:
        a, aa, ab, ac, aca, acb = self._create_nodes(root)
        self.assertEquals(api.list_children(root), [a])
        self.assertEquals(api.list_children(a), [aa, ab, ac])
        self.assertEquals(api.list_children(aca), [])

        # We can set 'go_up' to True to go up in the hierachy if
        # there's no children.  Only the third case gets a different
        # result:
        self.assertEquals(api.list_children(root, go_up=True), [a])
        self.assertEquals(api.list_children(a, go_up=True), [aa, ab, ac])
        self.assertEquals(api.list_children(aca, go_up=True), [aca, acb])

    def test_root(self):
        api = self._make()
        root = api.context
        a, aa, ab, ac, aca, acb = self._create_nodes(root)
        self.assertEquals(self._make().root, root)
        self.assertEquals(self._make(acb).root, root)

## Functional tests

def includeme(config):
    config.testing_securitypolicy()

def setUpFunctional(global_config=None, **settings):
    import wsgi_intercept.zope_testbrowser

    configuration = {
        'sqlalchemy.url': 'sqlite://',
        'kotti.includes': 'kotti.tests kotti.views.view kotti.views.edit',
        'kotti.secret': 'secret',
        }

    host, port = BASE_URL.split(':')[-2:]
    app = lambda: main({}, **configuration)
    wsgi_intercept.add_wsgi_intercept(host[2:], int(port), app)

    return dict(Browser=wsgi_intercept.zope_testbrowser.WSGI_Browser)
