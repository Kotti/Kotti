from contextlib import contextmanager

from pyramid.exceptions import Forbidden

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

@contextmanager
def contents_addable():
    from kotti import get_settings
    from kotti.resources import Content
    
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
        from kotti import DBSession
        from kotti.resources import Node
        from kotti.resources import Document
        
        self.config.testing_securitypolicy(permissive=True)
        self.config.include('kotti.views.edit')
        root = DBSession().query(Node).get(1)
        request = DummyRequest()
        self.assertEquals(Document.type_info.addable(root, request), True)

    def test_view_permitted_no(self):
        from kotti import DBSession
        from kotti.resources import Node
        from kotti.resources import Document

        self.config.testing_securitypolicy(permissive=False)
        self.config.include('kotti.views.edit')
        root = DBSession().query(Node).get(1)
        request = DummyRequest()
        self.assertEquals(Document.type_info.addable(root, request), False)

    def test_multiple_types(self):
        from kotti.resources import get_root
        from kotti.resources import Document
        from kotti.resources import Content
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
        from kotti.resources import get_root
        from kotti.resources import Content
        from kotti.resources import Document
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
        from kotti.resources import get_root
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
        from kotti.resources import get_root
        from kotti.resources import Document
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
        from kotti import DBSession
        from kotti.resources import Node
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
        from kotti import DBSession
        from kotti.resources import Node
        from kotti.resources import Document
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
        from kotti.security import get_principals

        P = get_principals()
        P[u'bob'] = {'name': u'bob', 'title': u"Bob"}
        P[u'frank'] = {'name': u'frank', 'title': u"Frank"}
        P[u'group:bobsgroup'] = {
            'name': u'group:bobsgroup', 'title': u"Bob's Group"}
        P[u'group:franksgroup'] = {
            'name': u'group:franksgroup', 'title': u"Frank's Group"}

    def test_roles(self):
        from kotti.views.users import share_node
        from kotti.resources import get_root
        from kotti.security import SHARING_ROLES

        # The 'share_node' view will return a list of available roles
        # as defined in 'kotti.security.SHARING_ROLES'
        root = get_root()
        request = DummyRequest()
        self.assertEqual(
            [r.name for r in share_node(root, request)['available_roles']],
            SHARING_ROLES)

    def test_search(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.security import set_groups
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
        from kotti.resources import get_root
        from kotti.security import list_groups
        from kotti.security import set_groups
        from kotti.views.users import share_node

        root = get_root()
        request = DummyRequest()
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
