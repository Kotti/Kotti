# -*- coding: utf-8 -*-
from webob.multidict import MultiDict
from pytest import raises
from pyramid.exceptions import Forbidden

from kotti.testing import DummyRequest


class TestAddableTypes:
    def test_view_permitted_yes(self, config, root):
        from kotti.resources import Document

        config.testing_securitypolicy(permissive=True)
        config.include('kotti.views.edit.content')
        request = DummyRequest()
        assert Document.type_info.addable(root, request) is True

    def test_view_permitted_no(self, config, root):
        from kotti.resources import Document

        config.testing_securitypolicy(permissive=False)
        config.include('kotti.views.edit.content')
        request = DummyRequest()
        assert Document.type_info.addable(root, request) is False

    def test_addable_views_registered_to_some_context(self, config, root):

        from kotti.resources import Document, File

        _saved = Document.type_info.addable_to
        Document.type_info.addable_to = ['File']

        config.testing_securitypolicy(permissive=True)
        config.add_view(
            lambda context, request: {},
            name=Document.type_info.add_view,
            permission='add',
            renderer='kotti:templates/edit/node.pt',
            context=File,
        )
        request = DummyRequest()

        assert Document.type_info.addable(Document(), request) is False
        assert Document.type_info.addable(File(), request) is True

        Document.type_info.addable_to = _saved


class TestNodePaste:
    def test_get_non_existing_paste_item(self, root):
        from kotti.util import get_paste_items

        request = DummyRequest()
        request.session['kotti.paste'] = ([1701], 'copy')
        item = get_paste_items(root, request)
        assert item == []

    def test_paste_non_existing_node(self, root):
        from kotti.views.edit.actions import NodeActions

        request = DummyRequest()

        for index, action in enumerate(['copy', 'cut']):
            request.session['kotti.paste'] = ([1701], 'copy')
            response = NodeActions(root, request).paste_nodes()
            assert response.status == '302 Found'
            assert len(request.session['_f_error']) == index + 1

    def test_paste_without_edit_permission(self, config, root):
        from kotti.views.edit.actions import NodeActions

        request = DummyRequest()
        request.params['paste'] = u'on'
        config.testing_securitypolicy(permissive=False)

        # We need to have the 'edit' permission on the original object
        # to be able to cut and paste:
        request.session['kotti.paste'] = ([1], 'cut')
        view = NodeActions(root, request)
        with raises(Forbidden):
            view.paste_nodes()

        # We don't need 'edit' permission if we're just copying:
        request.session['kotti.paste'] = ([1], 'copy')
        response = NodeActions(root, request).paste_nodes()
        assert response.status == '302 Found'


class TestNodeRename:
    def setUp(self):
        from pyramid.threadlocal import get_current_registry
        from kotti.url_normalizer import url_normalizer
        r = get_current_registry()
        settings = r.settings = {}
        settings['kotti.url_normalizer'] = [url_normalizer]
        settings['kotti.url_normalizer.map_non_ascii_characters'] = False

    def test_rename_to_empty_name(self, root):
        from kotti.resources import Document
        from kotti.views.edit.actions import NodeActions

        child = root['child'] = Document(title=u"Child")
        request = DummyRequest()
        request.params['rename'] = u'on'
        request.params['name'] = u''
        request.params['title'] = u'foo'
        NodeActions(child, request).rename_node()
        assert (request.session.pop_flash('error') ==
                [u'Name and title are required.'])

    def test_multi_rename(self, root):
        from kotti.resources import Document
        from kotti.views.edit.actions import NodeActions
        self.setUp()
        root['child1'] = Document(title=u"Child 1")
        root['child2'] = Document(title=u"Child 2")
        request = DummyRequest()
        request.POST = MultiDict()
        id1 = str(root['child1'].id)
        id2 = str(root['child2'].id)
        request.POST.add('children-to-rename', id1)
        request.POST.add('children-to-rename', id2)
        request.POST.add(id1 + '-name', u'')
        request.POST.add(id1 + '-title', u'Unhappy Child')
        request.POST.add(id2 + '-name', u'happy-child')
        request.POST.add(id2 + '-title', u'')
        request.POST.add('rename_nodes', u'rename_nodes')
        NodeActions(root, request).rename_nodes()
        assert request.session.pop_flash('error') ==\
            [u'Name and title are required.']

        request.POST.add(id1 + '-name', u'unhappy-child')
        request.POST.add(id1 + '-title', u'Unhappy Child')
        request.POST.add(id2 + '-name', u'happy-child')
        request.POST.add(id2 + '-title', u'Happy Child')
        request.POST.add('rename_nodes', u'rename_nodes')
        NodeActions(root, request).rename_nodes()
        assert request.session.pop_flash('success') ==\
            [u'Your changes have been saved.']


class TestNodeDelete:

    def test_multi_delete(self, root):
        from kotti.resources import Document
        from kotti.resources import File
        from kotti.views.edit.actions import NodeActions

        root['child1'] = Document(title=u"Child 1")
        root['child2'] = Document(title=u"Child 2")
        root['file1'] = File(title=u"File 1")

        request = DummyRequest()
        request.POST = MultiDict()
        id1 = str(root['child1'].id)
        id2 = str(root['child2'].id)
        id3 = str(root['file1'].id)
        request.POST.add('delete_nodes', u'delete_nodes')
        NodeActions(root, request).delete_nodes()
        assert request.session.pop_flash('info') ==\
            [u'Nothing was deleted.']

        request.POST.add('children-to-delete', id1)
        request.POST.add('children-to-delete', id2)
        request.POST.add('children-to-delete', id3)
        NodeActions(root, request).delete_nodes()
        assert request.session.pop_flash('success') == \
            [u'${title} was deleted.',
             u'${title} was deleted.',
             u'${title} was deleted.']


class TestNodeMove:
    def test_move_up(self, root):
        from kotti.resources import Document
        from kotti.views.edit.actions import NodeActions

        root['child1'] = Document(title=u"Child 1")
        root['child2'] = Document(title=u"Child 2")
        assert root['child1'].position < root['child2'].position

        request = DummyRequest()
        request.session['kotti.selected-children'] = [str(root['child2'].id)]
        NodeActions(root, request).up()
        assert request.session.pop_flash('success') ==\
            [u'${title} was moved.']
        assert root['child1'].position > root['child2'].position

    def test_move_down(self, root):
        from kotti.resources import Document
        from kotti.views.edit.actions import NodeActions

        root['child1'] = Document(title=u"Child 1")
        root['child2'] = Document(title=u"Child 2")
        root['child3'] = Document(title=u"Child 3")
        assert root['child1'].position < root['child3'].position
        assert root['child2'].position < root['child3'].position

        request = DummyRequest()
        ids = [str(root['child1'].id), str(root['child2'].id)]
        request.session['kotti.selected-children'] = ids
        NodeActions(root, request).down()
        assert request.session.pop_flash('success') ==\
            [u'${title} was moved.', u'${title} was moved.']
        assert root['child1'].position > root['child3'].position
        assert root['child2'].position > root['child3'].position

    def test_move_child_position_post(self, root, db_session):

        import transaction

        from kotti.resources import Document
        from kotti.resources import get_root
        from kotti.views.edit.actions import move_child_position

        # Create some documents
        root['child1'] = Document(title=u"Child 1")
        root['child2'] = Document(title=u"Child 2")
        root['child3'] = Document(title=u"Child 3")
        root['child4'] = Document(title=u"Child 4")
        root['child5'] = Document(title=u"Child 5")

        assert [c.position for c in root._children] == [0, 1, 2, 3, 4]
        assert [c.name for c in root._children] == [
            u'child1', u'child2', u'child3', u'child4', u'child5']

        request = DummyRequest()

        # Move down
        request.POST = {'from': '0', 'to': '3'}
        result = move_child_position(root, request)
        transaction.commit()
        root = get_root()
        assert result['result'] == 'success'
        assert [c.position for c in root._children] == [0, 1, 2, 3, 4]
        assert [c.name for c in root._children] == [
            u'child2', u'child3', u'child4', u'child1', u'child5']

        # Move up
        request.POST = {'from': '4', 'to': '0'}
        move_child_position(root, request)
        transaction.commit()
        root = get_root()
        assert result['result'] == 'success'
        assert [c.position for c in root._children] == [0, 1, 2, 3, 4]
        assert [c.name for c in root._children] == [
            u'child5', u'child2', u'child3', u'child4', u'child1']

        # Invalid param value
        request.POST = {'from': 'a', 'to': '3'}
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        request.POST = {'from': '0', 'to': '10'}
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        request.POST = {'from': '10', 'to': '0'}
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        # Missing param
        request.POST = {'from': 'a', }
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        # we have to clean up, because we committed transactions
        del root['child1']
        del root['child2']
        del root['child3']
        del root['child4']
        del root['child5']
        transaction.commit()

    def test_move_child_position_json(self, root, db_session):

        import transaction

        from kotti.resources import Document
        from kotti.resources import get_root
        from kotti.views.edit.actions import move_child_position

        # Create some documents
        root['child1'] = Document(title=u"Child 1")
        root['child2'] = Document(title=u"Child 2")
        root['child3'] = Document(title=u"Child 3")
        root['child4'] = Document(title=u"Child 4")
        root['child5'] = Document(title=u"Child 5")

        assert [c.position for c in root._children] == [0, 1, 2, 3, 4]
        assert [c.name for c in root._children] == [
            u'child1', u'child2', u'child3', u'child4', u'child5']

        request = DummyRequest()

        # Move down
        request.json_body = {'from': '0', 'to': '3'}
        result = move_child_position(root, request)
        transaction.commit()
        root = get_root()
        assert result['result'] == 'success'
        assert [c.position for c in root._children] == [0, 1, 2, 3, 4]
        assert [c.name for c in root._children] == [
            u'child2', u'child3', u'child4', u'child1', u'child5']

        # Move up
        request.json_body = {'from': '4', 'to': '0'}
        move_child_position(root, request)
        transaction.commit()
        root = get_root()
        assert result['result'] == 'success'
        assert [c.position for c in root._children] == [0, 1, 2, 3, 4]
        assert [c.name for c in root._children] == [
            u'child5', u'child2', u'child3', u'child4', u'child1']

        # Invalid param value
        request.json_body = {'from': 'a', 'to': '3'}
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        request.json_body = {'from': '0', 'to': '10'}
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        request.json_body = {'from': '10', 'to': '0'}
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        # Missing param
        request.json_body = {'from': 'a', }
        result = move_child_position(root, request)
        assert result['result'] == 'error'

        # we have to clean up, because we committed transactions
        del root['child1']
        del root['child2']
        del root['child3']
        del root['child4']
        del root['child5']
        transaction.commit()


class TestNodeShowHide:
    def test_show_hide(self, root):
        from kotti.resources import Document
        from kotti.views.edit.actions import NodeActions

        root['child1'] = Document(title=u"Child 1")
        assert root['child1'].in_navigation is True

        request = DummyRequest()
        request.session['kotti.selected-children'] = [str(root['child1'].id)]
        NodeActions(root, request).hide()
        assert request.session.pop_flash('success') ==\
            [u'${title} is no longer visible in the navigation.']
        assert root['child1'].in_navigation is False

        request.session['kotti.selected-children'] = [str(root['child1'].id)]
        NodeActions(root, request).show()
        assert request.session.pop_flash('success') ==\
            [u'${title} is now visible in the navigation.']
        assert root['child1'].in_navigation is True


class TestNodeShare:
    def test_roles(self, root):
        from kotti.views.users import share_node
        from kotti.security import SHARING_ROLES

        # The 'share_node' view will return a list of available roles
        # as defined in 'kotti.security.SHARING_ROLES'
        request = DummyRequest()
        assert (
            [r.name for r in share_node(root, request)['available_roles']] ==
            SHARING_ROLES)

    def test_search(self, extra_principals, root):
        from kotti.security import get_principals
        from kotti.security import set_groups
        from kotti.views.users import share_node

        request = DummyRequest()
        P = get_principals()

        # Search for "Bob", which will return both the user and the
        # group, both of which have no roles:
        request.params['search'] = u''
        request.params['query'] = u'Bob'
        entries = share_node(root, request)['entries']
        assert len(entries) == 2
        assert entries[0][0] == P['bob']
        assert entries[0][1] == ([], [])
        assert entries[1][0] == P['group:bobsgroup']
        assert entries[1][1] == ([], [])

        # We make Bob an Editor in this context, and Bob's Group
        # becomes global Admin:
        set_groups(u'bob', root, [u'role:editor'])
        P[u'group:bobsgroup'].groups = [u'role:admin']
        entries = share_node(root, request)['entries']
        assert len(entries) == 2
        assert entries[0][0] == P['bob']
        assert entries[0][1] == ([u'role:editor'], [])
        assert entries[1][0] == P['group:bobsgroup']
        assert entries[1][1] == ([u'role:admin'], [u'role:admin'])

        # A search that doesn't return any items will still include
        # entries with existing local roles:
        request.params['query'] = u'Weeee'
        entries = share_node(root, request)['entries']
        assert len(entries) == 1
        assert entries[0][0] == P[u'bob']
        assert entries[0][1] == ([u'role:editor'], [])
        assert (request.session.pop_flash('info') ==
                [u'No users or groups were found.'])

        # It does not, however, include entries that have local group
        # assignments only:
        set_groups(u'frank', root, [u'group:franksgroup'])
        request.params['query'] = u'Weeee'
        entries = share_node(root, request)['entries']
        assert len(entries) == 1
        assert entries[0][0] == P['bob']

    def test_apply(self, extra_principals, root):
        from kotti.security import list_groups
        from kotti.security import set_groups
        from kotti.views.users import share_node

        request = DummyRequest()

        request.params['apply'] = u''
        share_node(root, request)
        assert (request.session.pop_flash('info') == [u'No changes were made.'])
        assert list_groups('bob', root) == []
        set_groups('bob', root, ['role:special'])

        request.params['role::bob::role:owner'] = u'1'
        request.params['role::bob::role:editor'] = u'1'
        request.params['orig-role::bob::role:owner'] = u''
        request.params['orig-role::bob::role:editor'] = u''

        share_node(root, request)
        assert (request.session.pop_flash('success') ==
                [u'Your changes have been saved.'])
        assert (
            set(list_groups('bob', root)) ==
            {'role:owner', 'role:editor', 'role:special'}
            )

        # We cannot set a role that's not displayed, even if we forged
        # the request:
        request.params['role::bob::role:admin'] = u'1'
        request.params['orig-role::bob::role:admin'] = u''
        with raises(Forbidden):
            share_node(root, request)
        assert (
            set(list_groups('bob', root)) ==
            {'role:owner', 'role:editor', 'role:special'}
            )
