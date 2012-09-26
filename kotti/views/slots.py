"""This module allows add-ons to assign views to slots defined in
the overall page.  In other systems, these are called portlets or
viewlets.

A simple example that'll include the output of the 'hello_world' view
in in the left column of every page::

  from kotti.views.slots import assign_slot
  assign_slot('hello_world', 'left_slot')

It is also possible to pass parameters to the view:

  assign_slot('last_tweets', 'right_slot', params=dict(user='foo'))

If no view can be found for the given request and slot, the slot
remains empty.

Usually you'll want to call :func:`kotti.views.slots.assign_slot`
inside an ``includeme`` function and not on a module level, to allow
users of your package to include your slot assignments through the
``pyramid.includes`` configuration setting.  """

from pyramid.exceptions import PredicateMismatch
from pyramid.request import Request
from pyramid.view import render_view
import urllib
from zope.deprecation import deprecate

from kotti.events import ObjectEvent
from kotti.events import objectevent_listeners
from kotti.security import has_permission

REQUEST_ATTRS_TO_COPY = ('context', 'registry', 'user', 'cookies')


@deprecate("""\
kotti.views.slots.register is deprecated as of Kotti 0.7.0.

Convert your slot renderer function to a normal view, and register it
using Pyramid's ``config.add_view``.  Then use
``kotti.views.slots.assign_slot(view_name, slot_name)`` to assign your
view to a slot, e.g.: ``assign_slot('my-navigation', 'left')``.
""")
def register(slot, objtype, renderer):
    """Register a new slot renderer.

    The ``slot`` argument must be one of ``RenderLeftSlot``,
    ``RenderRightSlot`` etc.

    The ``objtype`` argument may be specified to limit rendering to
    special types of contexts.

    The ``renderer`` argument is the callable that receives an
    ``ObjectEvent`` as its single argument and returns HTML for
    inclusion.
    """
    objectevent_listeners[(slot, objtype)].append(
        lambda ev: renderer(ev.object, ev.request))


def _encode(params):
    if not params:
        return u''
    return urllib.urlencode(
        dict((k, v.encode('utf-8')) for k, v in params.items()))


def _render_view_on_slot_event(view_name, event, params):
    context = event.object
    request = event.request

    view_request = Request.blank(
        "{0}/{1}".format(request.path.rstrip('/'), view_name),
        base_url=request.application_url,
        POST=_encode(params),
        )

    post_items = request.POST.items()
    if post_items:
        view_request.POST.extend(post_items)

    # This is quite brittle:
    for name in REQUEST_ATTRS_TO_COPY:
        setattr(view_request, name, getattr(request, name))

    try:
        result = render_view(
            context,
            view_request,
            view_name,
            )
    except PredicateMismatch:
        return None
    else:
        return result.decode('utf-8')


def assign_slot(view_name, slot, params=None):
    """Assign view to slot.

    The ``view_name`` argument is the name of the view to assign.

    The ``slot`` argument is the name of the slot to assign to.
    Possible values are: left, right, abovecontent, belowcontent,
    inhead, beforebodyend, edit_inhead

    The  ``params`` argument optionally allows to pass POST parameters
    specified as a dictionary to the view.
    """
    event = [e for e in slot_events if e.name == slot]
    if not event:
        raise KeyError("Unknown slot '{0}'".format(slot))
    objectevent_listeners[(event[0], None)].append(
        lambda ev: _render_view_on_slot_event(view_name, ev, params))


class RenderLeftSlot(ObjectEvent):
    name = u'left'


class RenderRightSlot(ObjectEvent):
    name = u'right'


class RenderAboveContent(ObjectEvent):
    name = u'abovecontent'


class RenderBelowContent(ObjectEvent):
    name = u'belowcontent'


class RenderInHead(ObjectEvent):
    name = u'inhead'


class RenderBeforeBodyEnd(ObjectEvent):
    name = u'beforebodyend'


class RenderEditInHead(ObjectEvent):
    name = u'edit_inhead'

slot_events = [
    RenderLeftSlot, RenderRightSlot, RenderAboveContent, RenderBelowContent,
    RenderInHead, RenderBeforeBodyEnd, RenderEditInHead,
    ]


def local_navigation(context, request):
    from kotti.resources import get_root

    def ch(node):
        return [child for child in node.values()
                if child.in_navigation and
                has_permission('view', child, request)]

    parent = context
    children = ch(context)
    if not children and context.__parent__ is not None:
        parent = context.__parent__
        children = ch(parent)
    if len(children) and parent != get_root():
        return dict(parent=parent, children=children)
    return dict(parent=None)


def includeme_local_navigation(config):
    config.add_view(
        local_navigation,
        name='local-navigation',
        renderer='kotti:templates/view/nav-local.pt')
    assign_slot('local-navigation', 'right')
