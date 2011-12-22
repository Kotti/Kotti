from pyramid.registry import Registry

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

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
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Content
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.util import clear_cache

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
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Content

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
