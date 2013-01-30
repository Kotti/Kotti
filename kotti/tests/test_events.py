from mock import patch


class TestEvents:
    def test_owner(self, root, db_session, events, dummy_request):
        from kotti.resources import Content
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.util import clear_cache

        with patch('kotti.events.authenticated_userid', return_value='bob'):
            child = root[u'child'] = Content()
            db_session.flush()
        assert child.owner == u'bob'
        assert list_groups(u'bob', child) == [u'role:owner']

        clear_cache()
        # The event listener does not set the role again for subitems:
        with patch('kotti.events.authenticated_userid', return_value='bob'):
            grandchild = child[u'grandchild'] = Content()
            db_session.flush()
        assert grandchild.owner == u'bob'
        assert list_groups(u'bob', grandchild) == [u'role:owner']
        assert len(list_groups_raw(u'bob', grandchild)) == 0

    def test_sqlalchemy_events(self, root, db_session, events):
        from kotti import events
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

        child = root[u'child'] = Content()
        db_session.flush()
        assert lengths() == (1, 0, 0, 0)
        assert insert_events[0].object == child

        child.title = u"Bar"
        db_session.flush()
        assert lengths() == (1, 1, 0, 0)
        assert update_events[0].object == child

        db_session.delete(child)
        db_session.flush()
        assert lengths() == (1, 1, 1, 1)
        assert delete_events[0].object == child
        assert after_delete_events[0].object == child
