"""A simple events system that allows users to subscribe to specific
events and object events with specific object types.

Listeners are called in the order in which they were registered.

To subscribe to any event, do::

  def all_events_handler(event):
      print event  
  kotti.events.listeners[object].append(all_events_handler)

To subscribe only to insert events of documents, do::

  def document_insert_handler(event):
      print event.object, event.request
  kotti.events.objectevent_listeners[(ObjectInsert, Document)].append(
      document_insert_handler)

Events of type ``ObjectEvent`` carry a ``request`` argument with them
that may be ``None`` if no ``request`` was present at the time the
event was fired.
"""

from collections import defaultdict
try:
    from collections import OrderedDict
except ImportError: # pragma: no cover
    from ordereddict import OrderedDict
from datetime import datetime

import sqlalchemy.event
from sqlalchemy.orm import mapper
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid

from kotti.resources import DBSession
from kotti.resources import Node
from kotti.security import list_groups
from kotti.security import list_groups_raw
from kotti.security import set_groups

class ObjectEvent(object):
    def __init__(self, object, request=None):
        self.object = object
        self.request = request

class ObjectInsert(ObjectEvent):
    pass

class ObjectUpdate(ObjectEvent):
    pass

class ObjectDelete(ObjectEvent):
    pass

class DispatcherDict(defaultdict, OrderedDict):
    def __init__(self, *args, **kwargs):
        defaultdict.__init__(self, list)
        OrderedDict.__init__(self, *args, **kwargs)

class Dispatcher(DispatcherDict):
    """Dispatches based on event type.

      >>> class BaseEvent(object): pass
      >>> class SubEvent(BaseEvent): pass
      >>> class UnrelatedEvent(object): pass
      >>> def base_listener(event):
      ...     print 'Called base listener'
      >>> def sub_listener(event):
      ...     print 'Called sub listener'
      >>> def unrelated_listener(event):
      ...     print 'Called unrelated listener'

      >>> dispatcher = Dispatcher()
      >>> dispatcher[BaseEvent].append(base_listener)
      >>> dispatcher[SubEvent].append(sub_listener)
      >>> dispatcher[UnrelatedEvent].append(unrelated_listener)

      >>> dispatcher(BaseEvent())
      Called base listener
      >>> dispatcher(SubEvent())
      Called base listener
      Called sub listener
      >>> dispatcher(UnrelatedEvent())
      Called unrelated listener
    """
    def __call__(self, event):
        for event_type, handlers in self.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)

class ObjectEventDispatcher(DispatcherDict):
    """Dispatches based on both event type and object type.

      >>> class BaseObject(object): pass
      >>> class SubObject(BaseObject): pass
      >>> def base_listener(event):
      ...     print 'Called base listener'
      >>> def subobj_insert_listener(event):
      ...     print 'Called sub listener'
      
      >>> dispatcher = ObjectEventDispatcher()
      >>> dispatcher[(ObjectEvent, BaseObject)].append(base_listener)
      >>> dispatcher[(ObjectInsert, SubObject)].append(subobj_insert_listener)

      >>> dispatcher(ObjectEvent(BaseObject()))
      Called base listener
      >>> dispatcher(ObjectInsert(BaseObject()))
      Called base listener
      >>> dispatcher(ObjectEvent(SubObject()))
      Called base listener
      >>> dispatcher(ObjectInsert(SubObject()))
      Called base listener
      Called sub listener
    """
    def __call__(self, event):
        for (event_type, object_type), handlers in self.items():
            if (isinstance(event, event_type) and
                isinstance(event.object, object_type)):
                for handler in handlers:
                    handler(event)

listeners = Dispatcher()
notify = listeners.__call__
objectevent_listeners = ObjectEventDispatcher()
listeners[ObjectEvent].append(objectevent_listeners)

def _before_insert(mapper, connection, target):
    notify(ObjectInsert(target, get_current_request()))

def _before_update(mapper, connection, target):
    session = DBSession.object_session(target)
    if session.is_modified(target, include_collections=False):
        notify(ObjectUpdate(target, get_current_request()))

def _before_delete(mapper, conection, target):
    notify(ObjectDelete(target, get_current_request()))

def set_owner(event):
    obj, request = event.object, event.request
    if request is not None and isinstance(obj, Node) and obj.owner is None:
        userid = authenticated_userid(request)
        if userid is not None:
            # Set owner metadata:
            obj.owner = userid
            # Add owner role for userid if it's not inherited already:
            if u'role:owner' not in list_groups(userid, obj):
                groups = list_groups_raw(userid, obj) | set([u'role:owner'])
                set_groups(userid, obj, groups)

def set_creation_date(event):
    obj = event.object
    if obj.creation_date is None:
        obj.creation_date = obj.modification_date = datetime.now()

def set_modification_date(event):
    event.object.modification_date = datetime.now()

def includeme(config):
    sqlalchemy.event.listen(mapper, 'before_insert', _before_insert)
    sqlalchemy.event.listen(mapper, 'before_update', _before_update)
    sqlalchemy.event.listen(mapper, 'before_delete', _before_delete)

    objectevent_listeners[(ObjectInsert, Node)].append(set_owner)
    objectevent_listeners[(ObjectInsert, Node)].append(set_creation_date)
    objectevent_listeners[(ObjectUpdate, Node)].append(set_modification_date)
