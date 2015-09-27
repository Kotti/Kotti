"""This module includes a simple events system that allows users to
subscribe to specific events, and more particularly to *object events*
of specific object types.

See also: :ref:`events`.

Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.events

"""

from collections import defaultdict
from datetime import datetime
try:  # pragma: no cover
    from collections import OrderedDict
    OrderedDict  # pyflakes
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict

import sqlalchemy.event
from sqlalchemy.orm import load_only
import venusian
from sqlalchemy.orm import mapper
from sqlalchemy_utils.functions import has_changes
from pyramid.location import lineage
from pyramid.threadlocal import get_current_request
from zope.deprecation.deprecation import deprecated

from kotti import DBSession
from kotti import get_settings
from kotti.resources import Content
from kotti.resources import LocalGroup
from kotti.resources import Node
from kotti.resources import Tag
from kotti.resources import TagsToContents
from kotti.security import get_principals
from kotti.security import list_groups
from kotti.security import list_groups_raw
from kotti.security import Principal
from kotti.security import set_groups
from kotti.sqla import no_autoflush


class ObjectEvent(object):
    """Event related to an object."""

    def __init__(self, object, request=None):
        """Constructor.

        :param object: The (content) object related to the event.  This is an
                       instance of :class:`kotti.resources.Node` or one its
                       descendants for content related events, but it can be
                       anything.
        :type object: arbitrary

        :param request: current request
        :type request: :class:`kotti.request.Request`
        """

        self.object = object
        self.request = request


class ObjectInsert(ObjectEvent):
    """This event is emitted when an object is inserted into the DB."""


class ObjectUpdate(ObjectEvent):
    """This event is emitted when an object in the DB is updated."""


class ObjectDelete(ObjectEvent):
    """This event is emitted when an object is deleted from the DB."""


class ObjectAfterDelete(ObjectEvent):
    """This event is emitted after an object has been deleted from the DB.

    .. deprecated:: 0.9
    """
deprecated('ObjectAfterDelete',
           "The ObjectAfterDelete event is deprecated and will be no longer "
           "available starting with Kotti 0.10.")


class UserDeleted(ObjectEvent):
    """This event is emitted when an user object is deleted from the DB."""


class DispatcherDict(defaultdict, OrderedDict):
    """Base class for dispatchers"""

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
        for (evtype, objtype), handlers in self.items():
            if (isinstance(event, evtype) and
                    (objtype is None or isinstance(event.object, objtype))):
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


def _after_delete(mapper, connection, target):
    """ Trigger the Kotti event :class:``ObjectAfterDelete``.

    :param mapper: SQLAlchemy mapper
    :type mapper: :class:`sqlalchemy.orm.mapper.Mapper`

    :param connection: SQLAlchemy connection
    :type connection: :class:`sqlalchemy.engine.base.Connection`

    :param target: SQLAlchemy declarative class that is used
    :type target: Class as returned by ``declarative_base()``
    """

    notify(ObjectAfterDelete(target, get_current_request()))


def _before_flush(session, flush_context, instances):
    """Trigger the following Kotti :class:``ObjectEvent`` events in
    this order:

    - :class:``ObjectUpdate``
    - :class:``ObjectInsert``
    - :class:``ObjectDelete``
    """
    req = get_current_request()

    for obj in session.dirty:
        if session.is_modified(obj, include_collections=False):  # XXX ?
            notify(ObjectUpdate(obj, req))
    for obj in session.new:
        notify(ObjectInsert(obj, req))
    for obj in session.deleted:
        notify(ObjectDelete(obj, req))


def set_owner(event):
    """Set ``owner`` of the object that triggered the event.

    :param event: event that trigerred this handler.
    :type event: :class:`ObjectInsert`
    """

    obj, request = event.object, event.request
    if request is not None and isinstance(obj, Node) and obj.owner is None:
        userid = request.authenticated_userid
        if userid is not None:
            userid = unicode(userid)
            # Set owner metadata:
            obj.owner = userid
            # Add owner role for userid if it's not inherited already:
            if u'role:owner' not in list_groups(userid, obj):
                groups = list_groups_raw(userid, obj) | set([u'role:owner'])
                set_groups(userid, obj, groups)


def set_creation_date(event):
    """Set ``creation_date`` of the object that triggered the event.

    :param event: event that trigerred this handler.
    :type event: :class:`ObjectInsert`
    """

    obj = event.object
    if obj.creation_date is None:
        obj.creation_date = obj.modification_date = datetime.now()


def set_modification_date(event):
    """Update ``modification_date`` of the object that triggered the event.

    :param event: event that trigerred this handler.
    :type event: :class:`ObjectUpdate`
    """

    exclude = []

    for e in get_settings()['kotti.modification_date_excludes']:
        if isinstance(event.object, e.class_):
            exclude.append(e.key)

    if has_changes(event.object, exclude=exclude):
        event.object.modification_date = datetime.now()


def delete_orphaned_tags(event):
    """Delete Tag instances / records when they are not associated with any
    content.

    :param event: event that trigerred this handler.
    :type event: :class:`ObjectAfterDelete`
    """

    DBSession.query(Tag).filter(~Tag.content_tags.any()).delete(
        synchronize_session=False)


def cleanup_user_groups(event):
    """Remove a deleted group from the groups of a user/group and remove
       all local group entries of it.

       :param event: event that trigerred this handler.
       :type event: :class:`UserDeleted`
       """
    name = event.object.name

    if name.startswith("group:"):
        principals = get_principals()
        users_groups = [p for p in principals if name in principals[p].groups]
        for user_or_group in users_groups:
            principals[user_or_group].groups.remove(name)

    DBSession.query(LocalGroup).filter(
        LocalGroup.principal_name == name).delete()


def reset_content_owner(event):
    """Reset the owner of the content from the deleted owner.

    :param event: event that trigerred this handler.
    :type event: :class:`UserDeleted`
    """

    contents = DBSession.query(Content).filter(
        Content.owner == event.object.name).all()
    for content in contents:
        content.owner = None


def _update_children_paths(old_parent_path, new_parent_path):
    for child in DBSession.query(Node).options(
        load_only('path', 'type')).filter(
            Node.path.startswith(old_parent_path)):
        if child.path == new_parent_path:
            # The child is the node itself and has already be renamed.
            # Nothing to do!
            continue
        child.path = new_parent_path + child.path[len(old_parent_path):]


@no_autoflush
def _set_path_for_new_name(target, value, oldvalue, initiator):
    """Triggered whenever the Node's 'name' attribute is set.

    Is called with all kind of weird edge cases, e.g. name is 'None',
    parent is 'None' etc.
    """
    if getattr(target, '_kotti_set_path_for_new_name', False):
        # we're being called recursively (see below)
        return

    if value is None:
        # Our name is about to be set to 'None', so skip.
        return

    if target.__parent__ is None and value != u'':
        # Our parent hasn't been set yet.  Skip, unless we're the root
        # object (which always has an empty string as name).
        return

    old_path = target.path
    line = tuple(reversed(tuple(lineage(target))))
    target_path = u'/'.join(node.__name__ for node in line[:-1])
    if target.__parent__ is None and value == u'':
        # We're a new root object
        target_path = u'/'
    else:
        target_path += u'/{0}/'.format(value)
    target.path = target_path
    # We need to set the name to value here so that the subsequent
    # UPDATE in _update_children_paths will include the new 'name'
    # already.  We have to make sure that we don't end up in an
    # endless recursion, which is why we set this flag:

    target._kotti_set_path_for_new_name = True
    try:
        target.name = value
    finally:
        del target._kotti_set_path_for_new_name

    if old_path and target.id is not None:
        _update_children_paths(old_path, target_path)
    else:
        for child in _all_children(target):
            child.path = u'{0}{1}/'.format(child.__parent__.path,
                                           child.__name__)


def _all_children(item, _all=None):
    if _all is None:
        _all = []

    for child in item.children:
        _all.append(child)
        _all_children(child, _all)

    return _all


@no_autoflush
def _set_path_for_new_parent(target, value, oldvalue, initiator):
    """Triggered whenever the Node's 'parent' attribute is set.
    """
    if value is None:
        # The parent is about to be set to 'None', so skip.
        return

    if target.__name__ is None:
        # The object's name is still 'None', so skip.
        return

    if value.__parent__ is None and value.__name__ != u'':
        # Our parent doesn't have a parent, and it's not root either.
        return

    old_path = target.path
    line = tuple(reversed(tuple(lineage(value))))
    names = [node.__name__ for node in line]
    if None in names:
        # If any of our parents don't have a name yet, skip
        return

    target_path = u'/'.join(node.__name__ for node in line)
    target_path += u'/{0}/'.format(target.__name__)
    target.path = target_path

    if old_path and target.id is not None:
        _update_children_paths(old_path, target_path)
    else:
        # We might not have had a path before, but we might still have
        # children.  This is the case when we create an object with
        # children before we assign the object itself to a parent.
        for child in _all_children(target):
            child.path = u'{0}{1}/'.format(child.__parent__.path,
                                           child.__name__)


class subscribe(object):
    """Function decorator to attach the decorated function as a handler for a
    Kotti event.  Example::

        from kotti.events import ObjectInsert
        from kotti.events import subscribe
        from kotti.resources import Document

        @subscribe()
        def on_all_events(event):
            # this will be executed on *every* event
            print "Some kind of event occured"

        @subscribe(ObjectInsert)
        def on_insert(event):
            # this will be executed on every object insert
            context = event.object
            request = event.request
            print "Object insert"

        @subscribe(ObjectInsert, Document)
        def on_document_insert(event):
            # this will only be executed on object inserts if the object is
            # is an instance of Document
            context = event.object
            request = event.request
            print "Document insert"

    """

    venusian = venusian  # needed for testing

    def __init__(self, evttype=object, objtype=None):
        """Constructor.

        :param evttype: Event to subscribe to.
        :type evttype: class:`ObjectEvent` or descendant

        :param objtype: Object type on which the handler will be called
        :type objtype: class:`kotti.resources.Node` or descendant.
        """

        self.evttype = evttype
        self.objtype = objtype

    def register(self, context, name, obj):
        if issubclass(self.evttype, ObjectEvent):
            objectevent_listeners[(self.evttype, self.objtype)].append(obj)
        else:
            listeners[self.evttype].append(obj)

    def __call__(self, wrapped):

        self.venusian.attach(wrapped, self.register, category='kotti')

        return wrapped


_WIRED_SQLALCHMEY = False


def wire_sqlalchemy():  # pragma: no cover
    """ Connect SQLAlchemy events to their respective handler function (that
    fires the corresponding Kotti event). """

    global _WIRED_SQLALCHMEY
    if _WIRED_SQLALCHMEY:
        return
    else:
        _WIRED_SQLALCHMEY = True
    sqlalchemy.event.listen(mapper, 'after_delete', _after_delete)
    sqlalchemy.event.listen(DBSession, 'before_flush', _before_flush)

    # Update the 'path' attribute on changes to 'name' or 'parent'
    sqlalchemy.event.listen(
        Node.name, 'set', _set_path_for_new_name, propagate=True)
    sqlalchemy.event.listen(
        Node.parent, 'set', _set_path_for_new_parent, propagate=True)


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    from kotti.workflow import initialize_workflow

    # Subscribe to SQLAlchemy events and map these to Kotti events
    wire_sqlalchemy()

    # Set content owner on content creation
    objectevent_listeners[
        (ObjectInsert, Content)].append(set_owner)

    # Set content creation date on content creation
    objectevent_listeners[
        (ObjectInsert, Content)].append(set_creation_date)

    # Set content modification date on content updates
    objectevent_listeners[
        (ObjectUpdate, Content)].append(set_modification_date)

    # Delete orphaned tags after a tag association has ben deleted
    objectevent_listeners[
        (ObjectAfterDelete, TagsToContents)].append(delete_orphaned_tags)

    # Initialze the workflow on content creation.
    objectevent_listeners[
        (ObjectInsert, Content)].append(initialize_workflow)

    # Perform some cleanup when a user or group is deleted
    objectevent_listeners[
        (UserDeleted, Principal)].append(cleanup_user_groups)

    # Remove the owner from content when the corresponding user is deleted
    objectevent_listeners[
        (UserDeleted, Principal)].append(reset_content_owner)
