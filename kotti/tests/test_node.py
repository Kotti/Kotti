# -*- coding: utf-8 -*-
from pytest import mark
from pytest import raises
from pyramid.security import ALL_PERMISSIONS, Deny, Everyone
from pyramid.security import Allow
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError


class TestNode:
    def test_root_acl(self, db_session, root):

        # The root object has a persistent ACL set:
        for ace in (
            (Allow, 'role:owner', u'view'),
            (Allow, 'role:owner', u'add'),
            (Allow, 'role:owner', u'edit'),
            (Allow, 'role:owner', u'delete'),
            (Allow, 'role:owner', u'manage'),
            (Allow, 'role:owner', u'state_change'),
            (Allow, 'role:viewer', u'view'),
            (Allow, 'role:editor', u'view'),
            (Allow, 'role:editor', u'add'),
            (Allow, 'role:editor', u'edit'),
            (Allow, 'role:editor', u'delete'),
            (Allow, 'role:editor', u'state_change'),
            (Allow, Everyone, u'view'),
        ):
            assert ace in root.__acl__[1:-1]

        # The first ACE is here to prevent lock-out:
        assert (
            root.__acl__[0] ==
            (Allow, 'role:admin', ALL_PERMISSIONS))

        # The last ACE denies everything for everyone
        assert (
            root.__acl__[-1] ==
            (Deny, Everyone, ALL_PERMISSIONS)
        )

    def test_set_and_get_acl(self, db_session, root):

        # The __acl__ attribute of Nodes allows access to the mapped
        # '_acl' property:
        del root.__acl__
        with raises(AttributeError):
            root._get_acl()

        root.__acl__ = [('Allow', 'system.Authenticated', ['edit'])]
        assert (
            root.__acl__ == [('Allow', 'system.Authenticated', ['edit'])])

        root.__acl__ = [
            ('Allow', 'system.Authenticated', ['view']),
            ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
            ]

        assert (
            root.__acl__ == [
                ('Allow', 'system.Authenticated', ['view']),
                ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
                ])

        # We can append to the ACL, and it'll be persisted fine:
        root.__acl__.append(('Allow', 'system.Authenticated', ['edit']))
        assert (
            root.__acl__ == [
                ('Allow', 'system.Authenticated', ['view']),
                ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['edit']),
                ])

        db_session.flush()
        db_session.expire_all()

        assert (
            root.__acl__ == [
                ('Allow', 'role:admin', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['view']),
                ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['edit']),
                ])

    def test_append_to_empty_acl(self, db_session, root):
        from kotti.resources import Node

        node = root['child'] = Node()
        node.__acl__ = []

        db_session.flush()
        db_session.expire_all()

        node.__acl__.append(('Allow', 'system.Authenticated', ['edit']))
        db_session.flush()
        db_session.expire_all()

        assert node.__acl__ == [
            ('Allow', 'role:admin', ALL_PERMISSIONS),
            ('Allow', 'system.Authenticated', ['edit']),
            ]

    def test_unique_constraint(self, db_session, root):
        from kotti.resources import Node

        # Try to add two children with the same name to the root node:
        db_session.add(Node(name=u'child1', parent=root))
        db_session.add(Node(name=u'child1', parent=root))
        with raises(IntegrityError):
            db_session.flush()

    def test_container_methods(self, db_session, root):
        from kotti.resources import Node

        # Test some of Node's container methods:
        assert root.keys() == []

        child1 = Node(name=u'child1', parent=root)
        db_session.add(child1)
        assert root.keys() == [u'child1']
        assert root[u'child1'] == child1

        del root[u'child1']
        assert root.keys() == []

        # When we delete a parent node, all its child nodes will be
        # released as well:
        root[u'child2'] = Node()
        root[u'child2'][u'subchild'] = Node()
        assert (
            db_session.query(Node).filter(
                Node.name == u'subchild').count() == 1)
        del root[u'child2']
        assert (
            db_session.query(Node).filter(
                Node.name == u'subchild').count() == 0)

        # We can pass a tuple as the key to more efficiently reach
        # down to child objects:
        root[u'child3'] = Node()
        subchild33 = Node(name=u'subchild33', parent=root[u'child3'])
        db_session.add(subchild33)
        del root.__dict__['_children']  # force a different code path
        assert root[u'child3', u'subchild33'] is root[u'child3'][u'subchild33']
        assert root[(u'child3', u'subchild33')] is subchild33
        assert root[(u'child3', u'subchild33')] is subchild33
        with raises(KeyError):
            root[u'child3', u'bad-name']
        root.children  # force a different code path
        with raises(KeyError):
            root[u'child3', u'bad-name']
        del root[u'child3']

        # Overwriting an existing Node is an error; first delete manually!
        child4 = Node(name=u'child4', parent=root)
        db_session.add(child4)
        assert root.keys() == [u'child4']

        child44 = Node(name=u'child4')
        db_session.add(child44)

        with raises(SQLAlchemyError):
            root[u'child4'] = child44
            db_session.flush()

    def test_node_copy_name(self, db_session, root):

        copy_of_root = root.copy(name=u'copy_of_root')
        assert copy_of_root.name == u'copy_of_root'
        assert root.name == u''

    def test_node_copy_variants(self, db_session, root):
        from kotti.resources import Node

        child1 = root['child1'] = Node()
        child1['grandchild'] = Node()
        child2 = root['child2'] = Node()

        # first way; circumventing the Container API
        child2.children.append(child1.copy())

        # second way; canonical way
        child2['child2'] = child1.copy()

        # third way; this is necessary in cases when copy() will
        # attempt to put the new node into the db already, e.g. when
        # the copy is already being back-referenced by some other
        # object in the db.
        child1.copy(parent=child2, name=u'child3')

        assert [child.name for child in child2.children] == [
            'child1', 'child2', 'child3']

    def test_node_copy_parent_id(self, db_session, root):
        from kotti.resources import Node

        child1 = root['child1'] = Node()
        grandchild1 = child1['grandchild1'] = Node()
        db_session.flush()
        grandchild2 = grandchild1.copy()
        assert grandchild2.parent_id is None
        assert grandchild2.parent is None

    def test_node_copy_with_local_groups(self, db_session, root):
        from kotti.resources import Node
        from kotti.resources import LocalGroup

        child1 = root['child1'] = Node()
        local_group1 = LocalGroup(child1, u'joe', u'role:admin')
        db_session.add(local_group1)
        db_session.flush()

        child2 = root['child2'] = child1.copy()
        db_session.flush()
        assert child2.local_groups == []

    def test_clear(self, db_session, root):
        from kotti.resources import Node

        child = root['child'] = Node()
        assert db_session.query(Node).filter(Node.name == u'child').all() == [
            child]
        root.clear()
        assert db_session.query(Node).filter(Node.name == u'child').all() == []

    def test_annotations_mutable(self, db_session, root):

        root.annotations['foo'] = u'bar'
        assert root in db_session.dirty
        del root.annotations['foo']

    def test_nested_annotations_mutable(self, db_session, root):

        root.annotations['foo'] = {}
        db_session.flush()
        db_session.expire_all()

        root.annotations['foo']['bar'] = u'baz'
        assert root in db_session.dirty
        db_session.flush()
        db_session.expire_all()

        assert root.annotations['foo']['bar'] == u'baz'

    def test_annotations_coerce_fail(self, db_session, root):

        with raises(ValueError):
            root.annotations = []


class TestPath:
    def test_attribute(self, db_session, root, events):
        from kotti.resources import Node

        assert root.path == "/"
        child = root['child-1'] = Node()
        assert child.path == u'/child-1/'
        subchild = root['child-1']['subchild'] = Node()
        assert subchild.path == '/child-1/subchild/'

    def test_object_moved(self, db_session, root, events):
        from kotti.resources import Node
        child = root['child-1'] = Node()
        subchild = child['subchild'] = Node()
        subchild.parent = root
        assert subchild.path == '/subchild/'

    @mark.parametrize("flush", [True, False])
    def test_parent_moved(self, db_session, root, events, flush):
        from kotti.resources import Node
        child1 = root['child-1'] = Node()
        child2 = child1['child-2'] = Node()
        subchild = child2['subchild'] = Node()

        if flush:
            db_session.flush()

        assert subchild.path == '/child-1/child-2/subchild/'
        child2.parent = root
        assert subchild.path == '/child-2/subchild/'

    def test_object_renamed(self, db_session, root, events):
        from kotti.resources import Node
        child = root['child-1'] = Node()
        subchild = child['subchild'] = Node()

        subchild.name = u'renamed'
        assert subchild.path == '/child-1/renamed/'

    @mark.parametrize("flush", [True, False])
    def test_parent_renamed(self, db_session, root, events, flush):
        from kotti.resources import Node
        child1 = root['child-1'] = Node()
        child2 = child1['child-2'] = Node()
        subchild = child2['subchild'] = Node()

        if flush:
            db_session.flush()

        child2.name = u'renamed'
        assert subchild.path == '/child-1/renamed/subchild/'
        child1.name = u'renamed-1'
        assert child2.path == '/renamed-1/renamed/'
        assert subchild.path == '/renamed-1/renamed/subchild/'
        assert child1.path == '/renamed-1/'

    @mark.parametrize("flush", [True, False])
    def test_parent_copied(self, db_session, root, events, flush):
        from kotti.resources import Node
        c1 = root['c1'] = Node()
        c2 = c1['c2'] = Node()
        c2['c3'] = Node()

        if flush:
            db_session.flush()

        c1copy = root['c1copy'] = c1.copy()

        assert c1copy.path == '/c1copy/'
        assert c1copy['c2'].path == '/c1copy/c2/'
        assert c1copy['c2']['c3'].path == '/c1copy/c2/c3/'

        c2copy = c2['c2copy'] = c2.copy()

        assert c2copy.path == '/c1/c2/c2copy/'
        assert c2copy['c3'].path == '/c1/c2/c2copy/c3/'

    def test_children_append(self, db_session, root, events):
        from kotti.resources import Node

        child = Node(u'child-1')
        root.children.append(child)
        assert child.path == '/child-1/'

        child2 = Node(u'child-2')
        child.children.append(child2)
        assert child2.path == '/child-1/child-2/'

    def test_replace_root(self, db_session, root, events):
        from kotti.resources import Node
        db_session.delete(root)
        new_root = Node(u'')
        db_session.add(new_root)
        assert new_root.path == '/'

    def test_query_api(self, db_session, root, events):
        from kotti.resources import Node
        child1 = root['child-1'] = Node()
        child2 = child1['child-2'] = Node()
        subchild = child2['subchild'] = Node()

        assert db_session.query(Node).filter(
            Node.path.startswith(u'/')).count() == 4

        assert db_session.query(Node).filter(
            Node.path.startswith(u'/child-1/')).count() == 3

        objs = db_session.query(Node).filter(
            Node.path.startswith(u'/child-1/child-2/')).all()

        assert len(objs) == 2
        assert subchild in objs
        assert child2 in objs

        db_session.query(Node).filter(
            Node.path.startswith(u'/child-1/child-3/')).count() == 0

    def test_add_child_to_unnamed_parent(self, db_session, root, events):
        from kotti.resources import Node
        parent = Node()
        child1 = parent['child-1'] = Node()
        child2 = child1['child-2'] = Node()
        assert child2.__parent__.__parent__ is parent
        root['parent'] = parent
        assert parent.path == u'/parent/'
        assert child1.path == u'/parent/child-1/'
        assert child2.path == u'/parent/child-1/child-2/'

    def test_add_child_to_unrooted_parent(self, db_session, root, events):
        from kotti.resources import Node
        parent = Node('parent')
        child1 = parent['child-1'] = Node()
        child2 = child1['child-2'] = Node()
        root['parent'] = parent
        assert parent.path == u'/parent/'
        assert child1.path == u'/parent/child-1/'
        assert child2.path == u'/parent/child-1/child-2/'

    def test_node_lineage_not_loaded_new_name(self, db_session, root, events):

        from kotti.resources import Node
        parent = root['parent'] = Node()
        child1 = parent['child-1'] = Node()
        child2 = child1['child-2'] = Node()

        db_session.flush()
        child2_id = child2.id
        db_session.expunge_all()    # empty the identity map

        child2 = db_session.query(Node).get(child2_id)
        child3 = Node('child-3', parent=child2)
        assert child3.path == u'/parent/child-1/child-2/child-3/'

    def test_node_lineage_not_loaded_new_parent(self, db_session, root, events):

        from kotti.resources import Node
        from kotti.resources import get_root
        from kotti.events import ObjectEvent
        from kotti.events import objectevent_listeners

        # We want to guarantee that an object event handler can call
        # get_root(), which is only possible if our event handler
        # avoids flushing:
        objectevent_listeners[(ObjectEvent, Node)].append(
            lambda event: get_root())

        parent = root['parent'] = Node()
        child1 = parent['child-1'] = Node()

        db_session.flush()
        child1_id = child1.id
        db_session.expunge_all()

        child2 = Node(name=u'child-2')
        child3 = Node(name=u'child-3')

        child1 = db_session.query(Node).get(child1_id)
        child3.parent = child2
        child2.parent = child1

        assert child3.path == u"/parent/child-1/child-2/child-3/"


class TestLocalGroup:
    def test_copy(self, db_session, root):
        from kotti.resources import LocalGroup

        node, principal_name, group_name = root, 'p', 'g'
        lg = LocalGroup(node, principal_name, group_name)
        lg2 = lg.copy()
        assert lg2 is not lg
        assert lg.node is lg2.node
        assert lg.principal_name == lg2.principal_name
        assert lg.group_name == lg2.group_name


class TestTypeInfo:

    def test_add_selectable_default_view(self):

        from kotti.resources import Content
        from kotti.resources import Document
        from kotti.resources import TypeInfo

        type_info = TypeInfo(selectable_default_views=[])
        type_info.add_selectable_default_view('foo', u'Fannick')
        assert type_info.selectable_default_views == [
            ('foo', u'Fannick'),
            ]

        Document.type_info.add_selectable_default_view('one', 'two')
        assert ('one', 'two') in Document.type_info.selectable_default_views
        assert ('one', 'two') not in Content.type_info.selectable_default_views

    def test_type_info_add_permission_default(self):
        from kotti.resources import TypeInfo
        type_info = TypeInfo()
        assert type_info.add_permission == 'add'

    def test_type_info_add_permission_custom(self):
        from kotti.resources import TypeInfo
        type_info = TypeInfo(add_permission='customadd')
        assert type_info.add_permission == 'customadd'
