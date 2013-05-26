"""
Edit views.
"""

from zope.deprecation.deprecation import deprecate

from kotti.util import _
from kotti.util import get_paste_items  # BBB
from kotti.views.edit.content import ContentSchema
from kotti.views.edit.content import DocumentSchema
from kotti.views.form import AddFormView
from kotti.views.form import EditFormView
from kotti.views.util import ensure_view_selector
from kotti.workflow import get_workflow


# API
ContentSchema = ContentSchema
DocumentSchema = DocumentSchema


def _eval_titles(info):
    result = []
    for d in info:
        d = d.copy()
        d['title'] = eval(d['title']) if 'title' in d else d['name']
        result.append(d)
    return result


def _state_info(context, request):
    wf = get_workflow(context)
    state_info = []
    if wf is not None:
        state_info = _eval_titles(wf.state_info(context, request))
    return state_info


def _states(context, request):
    state_info = _state_info(context, request)
    return dict([(i['name'], i) for i in state_info])


@deprecate(
"""'generic_edit' is deprecated as of Kotti 0.8.  Use a form class
derived from 'kotti.views.form.EditFormView' instead.  See
'kotti.views.edit.content' for an example.
""")
def generic_edit(context, request, schema, **kwargs):  # pragma: no cover
    return EditFormView(
        context,
        request,
        schema=schema,
        **kwargs
        )()


@deprecate(
"""'generic_add' is deprecated as of Kotti 0.8.  Use a form class
derived from 'kotti.views.form.AddFormView' instead.  See
'kotti.views.edit.content' for an example.
""")
def generic_add(context, request, schema, add, title, **kwargs):  # pragma: no cover
    return AddFormView(
        context,
        request,
        schema=schema,
        add=add,
        item_type=title,
        **kwargs
        )()


def make_generic_edit(schema, **kwargs):  # pragma: no cover
    @ensure_view_selector
    def view(context, request):
        return generic_edit(context, request, schema, **kwargs)
    return view


def make_generic_add(schema, add, title=None, **kwargs):  # pragma: no cover
    def view(context, request):
        return generic_add(context, request, schema, add, title, **kwargs)
    return view


def includeme(config):
    pass
