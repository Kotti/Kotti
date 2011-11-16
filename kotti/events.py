"""This module includes a simple events system that allows users to
subscribe to specific events, and more particularly to *object events*
of specific object types.

To subscribe to any event, write::

  def all_events_handler(event):
      print event  
  kotti.events.listeners[object].append(all_events_handler)

To subscribe only to *ObjectInsert* events of *Document* types,
write::

  def document_insert_handler(event):
      print event.object, event.request
  kotti.events.objectevent_listeners[(ObjectInsert, Document)].append(
      document_insert_handler)

Events of type ``ObjectEvent`` have ``object`` and ``request``
attributes.  ``event.request`` may be ``None`` when no request is
available.

Notifying listeners of an event is as simple as calling the
``listeners_notify`` function::

  from kotti events import listeners
  listeners.notify(MyFunnyEvent())

Listeners are generally called in the order in which they are
registered.
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

from kotti import DBSession
from kotti.resources import Node
from kotti.resources import Content
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
      ...     return 1

      >>> dispatcher = Dispatcher()
      >>> dispatcher[BaseEvent].append(base_listener)
      >>> dispatcher[SubEvent].append(sub_listener)
      >>> dispatcher[UnrelatedEvent].append(unrelated_listener)

      >>> dispatcher(BaseEvent())
      Called base listener
      [None]
      >>> dispatcher(SubEvent())
      Called base listener
      Called sub listener
      [None, None]
      >>> dispatcher(UnrelatedEvent())
      Called unrelated listener
      [1]
    """
    def __call__(self, event):
        results = []
        for event_type, handlers in self.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    results.append(handler(event))
        return results

class ObjectEventDispatcher(DispatcherDict):
    """Dispatches based on both event type and object type.

      >>> class BaseObject(object): pass
      >>> class SubObject(BaseObject): pass
      >>> def base_listener(event):
      ...     return 'base'
      >>> def subobj_insert_listener(event):
      ...     return 'sub'
      >>> def all_listener(event):
      ...     return 'all'
      
      >>> dispatcher = ObjectEventDispatcher()
      >>> dispatcher[(ObjectEvent, BaseObject)].append(base_listener)
      >>> dispatcher[(ObjectInsert, SubObject)].append(subobj_insert_listener)
      >>> dispatcher[(ObjectEvent, None)].append(all_listener)

      >>> dispatcher(ObjectEvent(BaseObject()))
      ['base', 'all']
      >>> dispatcher(ObjectInsert(BaseObject()))
      ['base', 'all']
      >>> dispatcher(ObjectEvent(SubObject()))
      ['base', 'all']
      >>> dispatcher(ObjectInsert(SubObject()))
      ['base', 'sub', 'all']
    """
    def __call__(self, event):
        results = []
        for (event_type, object_type), handlers in self.items():
            if (isinstance(event, event_type) and
                (object_type is None or isinstance(event.object, object_type))):
                for handler in handlers:
                    results.append(handler(event))
        return results

def clear():
    listeners.clear()
    objectevent_listeners.clear()
    listeners[ObjectEvent].append(objectevent_listeners)

listeners = Dispatcher()
notify = listeners.__call__
objectevent_listeners = ObjectEventDispatcher()
clear()

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

_WIRED_SQLALCHMEY = False
def wire_sqlalchemy(): # pragma: no cover
    global _WIRED_SQLALCHMEY
    if _WIRED_SQLALCHMEY:
        return
    else:
        _WIRED_SQLALCHMEY = True
    sqlalchemy.event.listen(mapper, 'before_insert', _before_insert)
    sqlalchemy.event.listen(mapper, 'before_update', _before_update)
    sqlalchemy.event.listen(mapper, 'before_delete', _before_delete)

def includeme(config):
    wire_sqlalchemy()
    objectevent_listeners[(ObjectInsert, Content)].append(set_owner)
    objectevent_listeners[(ObjectInsert, Content)].append(set_creation_date)
    objectevent_listeners[(ObjectUpdate, Content)].append(set_modification_date)
