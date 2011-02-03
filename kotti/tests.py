from contextlib import contextmanager
import unittest

import transaction
from sqlalchemy.exc import IntegrityError
from pyramid.config import DEFAULT_RENDERERS
from pyramid import security
from pyramid import testing

from kotti import configuration
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
    configuration['kotti.available_types'].append(Node)
    try:
        yield
    finally:
        configuration['kotti.available_types'].pop()
        Node.type_info = save_node_type_info

class TestAddableTypes(UnitTestBase):
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
        self.assertEqual(response.location, 'http://example.com/add_document')

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
        self.assertEqual(
            api.edit_links, [
                {'name': 'edit', 'selected': False,
                 'url': 'http://example.com/edit'},
                {'name': 'add', 'selected': False,
                 'url': 'http://example.com/add'},
                {'name': 'move', 'selected': False,
                 'url': 'http://example.com/move'},
                {'name': 'share', 'selected': False,
                 'url': 'http://example.com/share'},
                ])

        # Edit links are controlled through
        # 'root.type_info.edit_views' and the permissions that guard
        # these:
        root = api.root
        root.type_info = root.type_info.copy(edit_views=['edit'])

        api = self._make()
        self.assertEqual(
            api.edit_links, [
                {'name': 'edit', 'selected': False,
                 'url': 'http://example.com/edit'},
                ])

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

class TestUtil(UnitTestBase):
    def test_title_to_name(self):
        from kotti.views.util import title_to_name
        self.assertEqual(title_to_name(u'Foo Bar'), u'foo-bar')

    def test_disambiguate_name(self):
        from kotti.views.util import disambiguate_name
        self.assertEqual(disambiguate_name(u'foo'), u'foo-1')
        self.assertEqual(disambiguate_name(u'foo-3'), u'foo-4')

## Functional tests

def setUpFunctional(global_config=None, **settings):
    import wsgi_intercept.zope_testbrowser

    configuration = {
        'sqlalchemy.url': 'sqlite://',
        'kotti.authentication_policy_factory': 'kotti.none_factory',
        'kotti.authorization_policy_factory': 'kotti.none_factory',
        'kotti.secret': 'secret',
        }

    host, port = BASE_URL.split(':')[-2:]
    app = lambda: main({}, **configuration)
    wsgi_intercept.add_wsgi_intercept(host[2:], int(port), app)

    return dict(Browser=wsgi_intercept.zope_testbrowser.WSGI_Browser)
