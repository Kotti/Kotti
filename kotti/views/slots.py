"""This module implements a method by which packages external to Kotti
can render pieces of HTML that are to be included in the page.

A simple example that'll render 'Hello, World!' in in the left column
of every page::

  def render_something(context, request):
      return u'Hello, World!'  

  from kotti.views.slots import register
  register(RenderLeftSlot, None, render_something)

Usually you'll want to call ``register`` inside a ``includeme``
function and not on a module level, to allow users of your package to
conditionally include your slot renderers.
"""

from pyramid.renderers import render

from kotti.events import ObjectEvent
from kotti.events import objectevent_listeners

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

class RenderLeftSlot(ObjectEvent):
    name = u'left'

class RenderRightSlot(ObjectEvent):
    name = u'right'

class RenderAboveContent(ObjectEvent):
    name = u'abovecontent'

class RenderBelowContent(ObjectEvent):
    name = u'belowcontent'

slot_events = [
    RenderLeftSlot, RenderRightSlot, RenderAboveContent, RenderBelowContent]

def render_local_navigation(context, request):
    from kotti.views.util import TemplateAPI
    api = TemplateAPI(context, request)
    parent, children = api.list_children_go_up()
    if parent != api.root and children:
        return render('../templates/view/slot-local-navigation.pt',
                      dict(parent=parent, children=children, api=api),
                      request)

def includeme(config):
    register(RenderRightSlot, None, render_local_navigation)
