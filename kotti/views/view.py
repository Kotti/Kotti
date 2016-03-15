# -*- coding: utf-8 -*-

import warnings

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import notfound_view_config
from pyramid.view import render_view_to_response
from pyramid.view import view_config

from kotti.interfaces import IContent
from kotti.views.util import search_content
from kotti.views.util import search_content_for_tags


@view_config(context=IContent)
def view_content_default(context, request):
    """This view is always registered as the default view for any Content.

    Its job is to delegate to a view of which the name may be defined
    per instance.  If a instance level view is not defined for
    'context' (in 'context.defaultview'), we will fall back to a view
    with the name 'view'.
    """

    view_name = context.default_view or 'view'
    response = render_view_to_response(context, request, name=view_name)
    if response is None:  # pragma: no cover
        warnings.warn(
            u'Failed to look up default view called {0!r} for {1!r}.'.format(
                view_name, context))
        raise HTTPNotFound()
    return response


# noinspection PyUnusedLocal
def view_node(context, request):  # pragma: no cover
    return {}  # BBB


# noinspection PyUnusedLocal
@view_config(name='search-results', permission='view',
             renderer='kotti:templates/view/search-results.pt')
def search_results(context, request):
    results = []
    if u'search-term' in request.POST:
        search_term = request.POST[u'search-term']
        results = search_content(search_term, request)
    return {'results': results}


# noinspection PyUnusedLocal
@view_config(name='search-tag', permission='view',
             renderer='kotti:templates/view/search-results.pt')
def search_results_for_tag(context, request):
    results = []
    if u'tag' in request.GET:
        # Single tag searching only, is allowed in default Kotti. Add-ons can
        # utilize search_content_for_tags(tags) to enable multiple tags
        # searching, but here it is called with a single tag.
        tags = [request.GET[u'tag'].strip()]
        results = search_content_for_tags(tags, request)
    return {'results': results}


# noinspection PyUnusedLocal
@view_config(name='search', permission='view',
             renderer='kotti:templates/view/search.pt')
@view_config(name='folder_view', context=IContent, permission='view',
             renderer='kotti:templates/view/folder.pt')
@view_config(name='view', context=IContent, permission='view',
             renderer='kotti:templates/view/document.pt')
def view(context, request):
    return {}


@notfound_view_config(renderer='kotti:templates/http-errors/notfound.pt')
def notfound_view(context, request):
    request.response = context
    return {}


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.scan(__name__)
