import warnings

from pytest import mark


class DummyVenusian(object):
    def __init__(self):
        self.attached = []

    def attach(self, wrapped, fn, category=None):
        self.attached.append((wrapped, fn, category))


class TestEvents:
    @mark.user('bob')
    def test_owner(self, root, db_session, events, dummy_request):
        from kotti.resources import Content
        from kotti.security import list_groups
        from kotti.security import list_groups_raw
        from kotti.util import clear_cache

        child = root[u'child'] = Content()
        db_session.flush()
        assert child.owner == u'bob'
        assert list_groups(u'bob', child) == [u'role:owner']

        clear_cache()

        # The event listener does not set the role again for subitems:
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
        with warnings.catch_warnings(record=True):
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

    def test_subscribe(self, root, db_session):

        from kotti.events import ObjectEvent
        from kotti.events import clear
        from kotti.events import listeners
        from kotti.events import objectevent_listeners
        from kotti.events import subscribe
        from kotti.resources import Document

        def handler(event):
            pass

        dec = subscribe()
        dec.venusian = DummyVenusian()
        decorated = dec(handler)
        dec.register(None, None, handler)
        assert dec.evttype is object
        assert dec.objtype is None
        assert decorated == handler
        assert (handler, dec.register, 'kotti') in dec.venusian.attached
        assert handler in listeners[object]
        assert handler not in objectevent_listeners[object]

        clear()

        dec = subscribe(ObjectEvent)
        dec.venusian = DummyVenusian()
        decorated = dec(handler)
        dec.register(None, None, handler)
        assert dec.evttype is ObjectEvent
        assert dec.objtype is None
        assert decorated == handler
        assert (handler, dec.register, 'kotti') in dec.venusian.attached
        assert handler not in listeners[ObjectEvent]
        assert handler in objectevent_listeners[(ObjectEvent, None)]

        clear()

        dec = subscribe(ObjectEvent, Document)
        dec.venusian = DummyVenusian()
        decorated = dec(handler)
        dec.register(None, None, handler)
        assert dec.evttype is ObjectEvent
        assert dec.objtype is Document
        assert decorated == handler
        assert (handler, dec.register, 'kotti') in dec.venusian.attached
        assert handler not in listeners[ObjectEvent]
        assert handler in objectevent_listeners[(ObjectEvent, Document)]
