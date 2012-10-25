from pytest import raises
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError


class TestNode:
    def test_root_acl(self, db_session):
        from kotti.resources import get_root
        root = get_root()

        # The root object has a persistent ACL set:
        assert (
            root.__acl__[1:] == [
                ('Allow', 'system.Everyone', ['view']),
                ('Allow', 'role:viewer', ['view']),
                ('Allow', 'role:editor', ['view', 'add', 'edit', 'state_change']),
                ('Allow', 'role:owner', ['view', 'add', 'edit', 'manage', 'state_change']),
                ])

        # The first ACE is here to preven lock-out:
        assert (
            root.__acl__[0] ==
            (Allow, 'role:admin', ALL_PERMISSIONS))

    def test_set_and_get_acl(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root

        root = get_root()

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

        DBSession.flush()
        DBSession.expire_all()

        assert (
            root.__acl__ == [
                ('Allow', 'role:admin', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['view']),
                ('Deny', 'system.Authenticated', ALL_PERMISSIONS),
                ('Allow', 'system.Authenticated', ['edit']),
                ])

    def test_append_to_empty_acl(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

        root = get_root()
        node = root['child'] = Node()
        node.__acl__ = []

        DBSession.flush()
        DBSession.expire_all()

        node.__acl__.append(('Allow', 'system.Authenticated', ['edit']))
        DBSession.flush()
        DBSession.expire_all()

        assert node.__acl__ == [
            ('Allow', 'role:admin', ALL_PERMISSIONS),
            ('Allow', 'system.Authenticated', ['edit']),
            ]

    def test_unique_constraint(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

        # Try to add two children with the same name to the root node:
        root = get_root()
        DBSession.add(Node(name=u'child1', parent=root))
        DBSession.add(Node(name=u'child1', parent=root))
        with raises(IntegrityError):
            DBSession.flush()

    def test_container_methods(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

        # Test some of Node's container methods:
        root = get_root()
        assert root.keys() == []

        child1 = Node(name=u'child1', parent=root)
        DBSession.add(child1)
        assert root.keys() == [u'child1']
        assert root[u'child1'] == child1

        del root[u'child1']
        assert root.keys() == []

        # When we delete a parent node, all its child nodes will be
        # released as well:
        root[u'child2'] = Node()
        root[u'child2'][u'subchild'] = Node()
        assert (
            DBSession.query(Node).filter(Node.name == u'subchild').count() == 1)
        del root[u'child2']
        assert (
            DBSession.query(Node).filter(Node.name == u'subchild').count() == 0)

        # We can pass a tuple as the key to more efficiently reach
        # down to child objects:
        root[u'child3'] = Node()
        subchild33 = Node(name=u'subchild33', parent=root[u'child3'])
        DBSession.add(subchild33)
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
        DBSession.add(child4)
        assert root.keys() == [u'child4']

        child44 = Node(name=u'child4')
        DBSession.add(child44)
        root[u'child4'] = child44
        with raises(SQLAlchemyError):
            DBSession.flush()

    def test_node_copy_name(self, db_session):
        from kotti.resources import get_root

        root = get_root()
        copy_of_root = root.copy(name=u'copy_of_root')
        assert copy_of_root.name == u'copy_of_root'
        assert root.name == u''

    def test_node_copy_variants(self, db_session):
        from kotti.resources import get_root
        from kotti.resources import Node

        root = get_root()
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

    def test_node_copy_parent_id(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

        root = get_root()
        child1 = root['child1'] = Node()
        grandchild1 = child1['grandchild1'] = Node()
        DBSession.flush()
        grandchild2 = grandchild1.copy()
        assert grandchild2.parent_id is None
        assert grandchild2.parent is None

    def test_node_copy_with_local_groups(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node
        from kotti.resources import LocalGroup

        root = get_root()
        child1 = root['child1'] = Node()
        local_group1 = LocalGroup(child1, u'joe', u'role:admin')
        DBSession.add(local_group1)
        DBSession.flush()

        child2 = root['child2'] = child1.copy()
        DBSession.flush()
        assert child2.local_groups == []

    def test_clear(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

        child = get_root()['child'] = Node()
        assert DBSession.query(Node).filter(Node.name == u'child').all() == [
            child]
        get_root().clear()
        assert DBSession.query(Node).filter(Node.name == u'child').all() == []

    def test_annotations_mutable(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root

        root = get_root()
        root.annotations['foo'] = u'bar'
        assert root in DBSession.dirty
        del root.annotations['foo']

    def test_nested_annotations_mutable(self, db_session):
        from kotti import DBSession
        from kotti.resources import get_root

        root = get_root()
        root.annotations['foo'] = {}
        DBSession.flush()
        DBSession.expire_all()

        root = get_root()
        root.annotations['foo']['bar'] = u'baz'
        assert root in DBSession.dirty
        DBSession.flush()
        DBSession.expire_all()

        root = get_root()
        assert root.annotations['foo']['bar'] == u'baz'

    def test_annotations_coerce_fail(self, db_session):
        from kotti.resources import get_root

        root = get_root()
        with raises(ValueError):
            root.annotations = []


class TestLocalGroup:
    def test_copy(self, db_session):
        from kotti.resources import get_root
        from kotti.resources import LocalGroup

        node, principal_name, group_name = get_root(), 'p', 'g'
        lg = LocalGroup(node, principal_name, group_name)
        lg2 = lg.copy()
        assert lg2 is not lg
        assert lg.node is lg2.node
        assert lg.principal_name == lg2.principal_name
        assert lg.group_name == lg2.group_name


class TestTypeInfo:
    def test_add_selectable_default_view(self):
        from kotti.resources import TypeInfo

        type_info = TypeInfo(selectable_default_views=[])
        type_info.add_selectable_default_view('foo', u'Fannick')
        assert type_info.selectable_default_views == [
            ('foo', u'Fannick'),
            ]
