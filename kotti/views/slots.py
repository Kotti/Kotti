"""This module allows add-ons to register renderers that add pieces of
HTML to the overall page.  In other systems, these are called portlets
or viewlets.

A simple example that'll render *Hello, World!* in in the left column
of every page::

  def render_hello(context, request):
      return u'Hello, World!'  

  from kotti.views.slots import register
  from kotti.views.slots import RenderLeftSlot
  register(RenderLeftSlot, None, render_hello)

Slot renderers may also return ``None`` to indicate that they don't
want to include anything.  We can change our ``render_hello`` function
to include a message only when the context is the root object::

  from kotti.resources import get_root
  def render_hello(context, request):
      if context == get_root():
          return u'Hello, World!'  

The second argument to :func:`kotti.views.slots.register` allows you
to filter on context.  These two are equivalent::

  from kotti.views.slots import RenderRightSlot
  from mypackage.resources import Calendar

  def render_agenda1(context, request):
      if isinstance(context, Calendar):
          return '<div>...</div>'
  register(RenderRightSlot, None, render_agenda1)
  
  def render_agenda2(context, request):
      return '<div>...</div>'
  register(RenderRightSlot, Calendar, render_agenda2)

Usually you'll want to call :func:`kotti.views.slots.register` inside
an ``includeme`` function and not on a module level, to allow users of
your package to include your slot renderers through the
``kotti.includes`` configuration setting.
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

class RenderInHead(ObjectEvent):
    name = u'inhead'

class RenderBeforeBodyEnd(ObjectEvent):
    name = u'beforebodyend'

slot_events = [
    RenderLeftSlot, RenderRightSlot, RenderAboveContent, RenderBelowContent,
    RenderInHead, RenderBeforeBodyEnd,
    ]

def render_local_navigation(context, request):
    from kotti.views.util import template_api
    api = template_api(context, request)
    parent, children = api.list_children_go_up()
    children = [c for c in children if c.in_navigation]
    if parent != api.root and children:
        return render('kotti:templates/view/slot-local-navigation.pt',
                      dict(parent=parent, children=children, api=api),
                      request)

def includeme(config):
    register(RenderRightSlot, None, render_local_navigation)
