# -*- coding: utf-8 -*-

"""
Edit views.
"""

import warnings

# noinspection PyProtectedMember
from kotti.util import _
from kotti.views.edit.content import ContentSchema
from kotti.views.edit.content import DocumentSchema
from kotti.workflow import get_workflow

# API
ContentSchema = ContentSchema
DocumentSchema = DocumentSchema


def _translate_titles(info):
    result = []
    for d in info:
        d = d.copy()
        try:
            d['title'] = eval(d['title']) if 'title' in d else d['name']
            warnings.warn(u'_() in workflow.zcml is deprecated. '
                          u'Support will be removed in Kotti 2.0.0.',
                          DeprecationWarning)
        except (NameError, SyntaxError):
            d['title'] = _(d['title']) if 'title' in d else d['name']
        result.append(d)
    return result


def _state_info(context, request):
    wf = get_workflow(context)
    state_info = []
    if wf is not None:
        state_info = _translate_titles(wf.state_info(context, request))
    return state_info


def _states(context, request):
    state_info = _state_info(context, request)
    return dict([(i['name'], i) for i in state_info])


# noinspection PyUnusedLocal
def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    pass
