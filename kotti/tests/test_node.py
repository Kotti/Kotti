from pyramid.security import ALL_PERMISSIONS
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from kotti.testing import UnitTestBase

class TestNode(UnitTestBase):
    def test_root_acl(self):
        from kotti.resources import get_root
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
        from kotti import DBSession
        from kotti.resources import get_root
        
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
        DBSession.flush()
        DBSession.expire_all()
        self.assertEquals(root.__acl__[1:], [second, first])

        root._del_acl()
        self.assertRaises(AttributeError, root._del_acl)

    def test_unique_constraint(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

        # Try to add two children with the same name to the root node:
        session = DBSession()
        root = get_root()
        session.add(Node(name=u'child1', parent=root))
        session.add(Node(name=u'child1', parent=root))
        self.assertRaises(IntegrityError, session.flush)

    def test_container_methods(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Node

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
        from kotti.resources import get_root
        
        # Test some of Node's container methods:
        root = get_root()
        copy_of_root = root.copy(name=u'copy_of_root')
        self.assertEqual(copy_of_root.name, u'copy_of_root')
        self.assertEqual(root.name, u'')

    def test_annotations_mutable(self):
        from kotti import DBSession
        from kotti.resources import get_root
        
        root = get_root()
        root.annotations['foo'] = u'bar'
        self.assertTrue(root in DBSession.dirty)
        del root.annotations['foo']

    def test_nested_annotations_mutable(self):
        from kotti import DBSession
        from kotti.resources import get_root

        root = get_root()
        root.annotations['foo'] = {}
        DBSession.flush()
        DBSession.expire_all()

        root = get_root()
        root.annotations['foo']['bar'] = u'baz'
        self.assertTrue(root in DBSession.dirty)
        DBSession.flush()
        DBSession.expire_all()

        root = get_root()
        self.assertEqual(root.annotations['foo']['bar'], u'baz')

    def test_annotations_coerce_fail(self):
        from kotti.resources import get_root

        root = get_root()
        self.assertRaises(ValueError, setattr, root, 'annotations', [])
