from mock import patch

from kotti.testing import EventTestBase
from kotti.testing import UnitTestBase


class TestEvents(EventTestBase, UnitTestBase):
    @patch('kotti.events.authenticated_userid')
    @patch('kotti.events.get_current_request')
    def test_owner(self, get_current_request, authenticated_userid):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Content
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.util import clear_cache

        get_current_request.return_value = not None
        authenticated_userid.return_value = 'bob'
        root = get_root()
        child = root[u'child'] = Content()
        DBSession.flush()
        self.assertEqual(child.owner, u'bob')
        self.assertEqual(list_groups(u'bob', child), [u'role:owner'])

        clear_cache()
        # The event listener does not set the role again for subitems:
        grandchild = child[u'grandchild'] = Content()
        DBSession.flush()
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

        after_delete_events = []

        def after_delete(event):
            after_delete_events.append(event)

        def lengths():
            return (len(insert_events), len(update_events),
                    len(delete_events), len(after_delete_events))

        lis = events.objectevent_listeners
        lis[(events.ObjectInsert, None)].append(insert)
        lis[(events.ObjectUpdate, None)].append(update)
        lis[(events.ObjectDelete, None)].append(delete)
        lis[(events.ObjectAfterDelete, None)].append(after_delete)

        root = get_root()
        child = root[u'child'] = Content()
        DBSession.flush()
        assert lengths() == (1, 0, 0, 0)
        assert insert_events[0].object == child

        child.title = u"Bar"
        DBSession.flush()
        assert lengths() == (1, 1, 0, 0)
        assert update_events[0].object == child

        DBSession.delete(child)
        DBSession.flush()
        assert lengths() == (1, 1, 1, 1)
        assert delete_events[0].object == child
        assert after_delete_events[0].object == child
