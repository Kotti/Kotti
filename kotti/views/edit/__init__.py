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


def includeme(config):
    pass
