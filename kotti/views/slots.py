"""This module allows add-ons to assign views to slots defined in
the overall page.  In other systems, these are called portlets or
viewlets.

A simple example that'll include the output of the 'hello_world' view
in in the left column of every page::

  from kotti.views.slots import assign_slot
  assign_slot('hello_world', 'left')

It is also possible to pass parameters to the view::

  assign_slot('last_tweets', 'right', params=dict(user='foo'))

In the view you can get the slot in that the view is rendered from
the request::

    @view_config(name='last_tweets')
    def view(request, context):
        slot = request.kotti_slot
        # ...

If no view can be found for the given request and slot, the slot
remains empty.  If you want to force your slot not to be rendered,
raise :class:`pyramid.exceptions.PredicateMismatch` inside your view::

    from pyramid.exceptions import PredicateMismatch

    @view_config(name='last_tweets')
    def view(request, context):
        if some_condition:
            raise PredicateMismatch()
        return {...}

Usually you'll want to call :func:`kotti.views.slots.assign_slot`
inside an ``includeme`` function and not on a module level, to allow
users of your package to include your slot assignments through the
``pyramid.includes`` configuration setting.
"""

from urllib.parse import urlencode

from pyramid.exceptions import PredicateMismatch
from pyramid.httpexceptions import HTTPException
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import render_view

from kotti.events import ObjectEvent
from kotti.events import objectevent_listeners

REQUEST_ATTRS_TO_COPY = ("context", "registry", "user", "cookies", "session")


def _encode(params):
    if not params:
        return ""
    return urlencode({k: v.encode("utf-8") for k, v in params.items()})


def _render_view_on_slot_event(view_name, event, params):
    context = event.object
    request = event.request

    view_request = request.__class__.blank(
        "{}/{}".format(request.path.rstrip("/"), view_name),
        base_url=request.application_url,
        POST=_encode(params),
    )

    if request.POST:
        view_request.POST.update(request.POST)

    # This is quite brittle:
    for name in REQUEST_ATTRS_TO_COPY:
        setattr(view_request, name, getattr(request, name))
    setattr(view_request, "kotti_slot", event.name)

    try:
        result = render_view(context, view_request, view_name)
    except (PredicateMismatch, HTTPForbidden):
        return None
    if isinstance(context, HTTPException):
        return None
    return result.decode("utf-8")


def assign_slot(view_name, slot, params=None):
    """Assign view to slot.

    :param view_name: Name of the view to assign.
    :type view_name: str

    :param slot: Name of the slot to assign to.  Possible values are: left,
                 right, abovecontent, belowcontent, inhead, beforebodyend,
                 edit_inhead
    :type slot: str

    :param params: Optionally allows to pass POST parameters to the view.
    :type params: dict
    """

    event = [e for e in slot_events if e.name == slot]
    if not event:
        raise KeyError(f"Unknown slot '{slot}'")
    objectevent_listeners[(event[0], None)].append(
        lambda ev: _render_view_on_slot_event(view_name, ev, params)
    )


class RenderLeftSlot(ObjectEvent):
    name = "left"


class RenderRightSlot(ObjectEvent):
    name = "right"


class RenderAboveContent(ObjectEvent):
    name = "abovecontent"


class RenderBelowContent(ObjectEvent):
    name = "belowcontent"


class RenderInHead(ObjectEvent):
    name = "inhead"


class RenderBeforeBodyEnd(ObjectEvent):
    name = "beforebodyend"


class RenderEditInHead(ObjectEvent):
    name = "edit_inhead"


slot_events = [
    RenderLeftSlot,
    RenderRightSlot,
    RenderAboveContent,
    RenderBelowContent,
    RenderInHead,
    RenderBeforeBodyEnd,
    RenderEditInHead,
]
