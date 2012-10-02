from collections import defaultdict
from datetime import datetime
import hashlib
import urllib

from babel.dates import format_date
from babel.dates import format_datetime
from babel.dates import format_time
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer
from pyramid.i18n import get_locale_name
from pyramid.i18n import make_localizer
from pyramid.interfaces import ITranslationDirectories
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from pyramid.threadlocal import get_current_request
from pyramid.view import render_view_to_response
from zope.deprecation import deprecated
from sqlalchemy import and_
from sqlalchemy import not_
from sqlalchemy import or_
from zope.deprecation.deprecation import deprecate

from kotti import get_settings
from kotti import DBSession
from kotti.util import disambiguate_name
disambiguate_name  # BBB
from kotti.util import _
from kotti.events import objectevent_listeners
from kotti.resources import Content
from kotti.resources import Document
from kotti.security import get_user
from kotti.security import has_permission
from kotti.security import view_permitted
from kotti.views.form import get_appstruct
from kotti.views.form import BaseFormView
from kotti.views.form import AddFormView
from kotti.views.form import EditFormView
from kotti.views.slots import slot_events
from kotti.views.site_setup import CONTROL_PANEL_LINKS


def template_api(context, request, **kwargs):
    return get_settings()['kotti.templates.api'][0](
        context, request, **kwargs)


def render_view(context, request, name='', secure=True):
    response = render_view_to_response(context, request, name, secure)
    if response is not None:
        return response.ubody


def add_renderer_globals(event):
    if event['renderer_name'] != 'json':
        request = event['request']
        api = getattr(request, 'template_api', None)
        if api is None and request is not None:
            api = template_api(event['context'], event['request'])
        event['api'] = api


def is_root(context, request):
    return context is TemplateAPI(context, request).root


def get_localizer_for_locale_name(locale_name):
    registry = get_current_registry()
    tdirs = registry.queryUtility(ITranslationDirectories, default=[])
    return make_localizer(locale_name, tdirs)


def translate(*args, **kwargs):
    request = get_current_request()
    if request is None:
        localizer = get_localizer_for_locale_name('en')
    else:
        localizer = get_localizer(request)
    return localizer.translate(*args, **kwargs)


class TemplateStructure(object):
    def __init__(self, html):
        self.html = html

    def __html__(self):
        return self.html
    __unicode__ = __html__

    def __getattr__(self, key):
        return getattr(self.html, key)


class Slots(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __getattr__(self, name):
        for event_type in slot_events:
            if event_type.name == name:
                break
        else:
            raise AttributeError(name)
        value = []
        event = event_type(self.context, self.request)
        for snippet in objectevent_listeners(event):
            if snippet is not None:
                if isinstance(snippet, list):
                    value.extend(snippet)
                else:
                    value.append(snippet)
        setattr(self, name, value)
        return value


class TemplateAPI(object):
    """This implements the 'api' object that's passed to all
    templates.

    Use dict-access as a shortcut to retrieve template macros from
    templates.
    """
    # Instead of overriding these, consider using the
    # 'kotti.overrides' variable.
    BARE_MASTER = 'kotti:templates/master-bare.pt'
    VIEW_MASTER = 'kotti:templates/view/master.pt'
    EDIT_MASTER = 'kotti:templates/edit/master.pt'
    SITE_SETUP_MASTER = 'kotti:templates/site-setup/master.pt'

    body_css_class = ''

    def __init__(self, context, request, bare=None, **kwargs):
        self.context, self.request = context, request

        if getattr(request, 'template_api', None) is None:
            request.template_api = self

        self.S = get_settings()
        if request.is_xhr and bare is None:
            bare = True  # use bare template that renders just the content area
        self.bare = bare
        self.slots = Slots(context, request)
        self.__dict__.update(kwargs)

    @reify
    def edit_needed(self):
        if 'kotti.static.edit_needed' in self.S:
            return [r.need() for r in self.S['kotti.static.edit_needed']]

    @reify
    def view_needed(self):
        if 'kotti.static.view_needed' in self.S:
            return [r.need() for r in self.S['kotti.static.view_needed']]

    def macro(self, asset_spec, macro_name='main'):
        if self.bare and asset_spec in (
                self.VIEW_MASTER, self.EDIT_MASTER, self.SITE_SETUP_MASTER):
            asset_spec = self.BARE_MASTER
        return get_renderer(asset_spec).implementation().macros[macro_name]

    @reify
    def site_title(self):
        value = get_settings().get('kotti.site_title')
        if not value:
            value = self.root.title
        return value

    @reify
    def page_title(self):
        view_title = self.request.view_name.replace('_', ' ').title()
        if view_title:
            view_title += u' '
        view_title += self.context.title
        return u'%s - %s' % (view_title, self.site_title)

    def url(self, context=None, *elements, **kwargs):
        if context is None:
            context = self.context
        return self.request.resource_url(context, *elements, **kwargs)

    @reify
    def root(self):
        return self.lineage[-1]

    @reify
    def lineage(self):
        return list(lineage(self.context))

    @reify
    def breadcrumbs(self):
        return reversed(self.lineage)

    @reify
    @deprecate('api.user is deprecated as of Kotti 0.7.0.  '
               'Use ``request.user`` instead.')
    def user(self):  # pragma: no cover
        return get_user(self.request)

    def has_permission(self, permission, context=None):
        if context is None:
            context = self.context
        return has_permission(permission, context, self.request)

    def render_view(self, name='', context=None, request=None, secure=True,
                    bare=True):
        if context is None:
            context = self.context
        if request is None:
            request = self.request

        before = self.bare
        try:
            self.bare = bare
            html = render_view(context, request, name, secure)
        finally:
            self.bare = before
        return TemplateStructure(html)

    def render_template(self, renderer, **kwargs):
        return TemplateStructure(render(renderer, kwargs, self.request))

    def list_children(self, context=None, permission='view'):
        if context is None:
            context = self.context
        children = []
        if hasattr(context, 'values'):
            for child in context.values():
                if (not permission or
                        has_permission(permission, child, self.request)):
                    children.append(child)
        return children

    inside = staticmethod(inside)

    def avatar_url(self, user=None, size="14", default_image='identicon'):
        if user is None:
            user = self.request.user
        email = user.email
        if not email:
            email = user.name
        h = hashlib.md5(email).hexdigest()
        query = {'default': default_image, 'size': str(size)}
        url = 'https://secure.gravatar.com/avatar/%s?%s' % (
            h, urllib.urlencode(query))
        return url

    @reify
    def locale_name(self):
        return get_locale_name(self.request)

    def format_date(self, d, format=None):
        if format is None:
            format = self.S['kotti.date_format']
        return format_date(d, format=format, locale=self.locale_name)

    def format_datetime(self, dt, format=None):
        if format is None:
            format = self.S['kotti.datetime_format']
        if not isinstance(dt, datetime):
            dt = datetime.fromtimestamp(dt)
        return format_datetime(dt, format=format, locale=self.locale_name)

    def format_time(self, t, format=None):
        if format is None:
            format = self.S['kotti.time_format']
        return format_time(t, format=format, locale=self.locale_name)

    def get_type(self, name):
        for class_ in get_settings()['kotti.available_types']:
            if class_.type_info.name == name:
                return class_

    def find_edit_view(self, item):
        view_name = self.request.view_name
        if not view_permitted(item, self.request, view_name):
            view_name = u'edit'
        if not view_permitted(item, self.request, view_name):
            view_name = u''
        return view_name

    @reify
    def edit_links(self):
        if not hasattr(self.context, 'type_info'):
            return []
        return [l for l in self.context.type_info.edit_links
                if l.permitted(self.context, self.request)]

    def more_links(self, name):
        return [l for l in getattr(self, name)
                if l.permitted(self.context, self.request)]

    @reify
    def site_setup_links(self):

        return [l for l in CONTROL_PANEL_LINKS
                if l.permitted(self.root, self.request)]


def ensure_view_selector(func):
    def wrapper(context, request):
        path_els = request.path_info.split(u'/')
        if not path_els[-1].startswith('@@'):
            path_els[-1] = '@@' + path_els[-1]
            request.path_info = u'/'.join(path_els)
            return HTTPFound(location=request.url)
        return func(context, request)
    wrapper.__doc__ = func.__doc__
    return wrapper


class NavigationNodeWrapper(object):
    def __init__(self, node, request, item_mapping, item_to_children):
        self._node = node
        self._request = request
        self._item_mapping = item_mapping
        self._item_to_children = item_to_children

    @property
    def __parent__(self):
        if self.parent_id:
            return self._item_mapping[self.parent_id]

    @property
    def children(self):
        return [NavigationNodeWrapper(
            child, self._request, self._item_mapping, self._item_to_children)
            for child in self._item_to_children[self.id]
            if has_permission('view', child, self._request)]

    def __getattr__(self, name):
        return getattr(self._node, name)


def nodes_tree(request):
    item_mapping = {}
    item_to_children = defaultdict(lambda: [])
    for node in DBSession.query(Content).with_polymorphic(Content):
        item_mapping[node.id] = node
        if has_permission('view', node, request):
            item_to_children[node.parent_id].append(node)

    for children in item_to_children.values():
        children.sort(key=lambda ch: ch.position)

    return NavigationNodeWrapper(
        item_to_children[None][0],
        request,
        item_mapping,
        item_to_children,
        )


def search_content(search_term, request=None):
    return get_settings()['kotti.search_content'][0](search_term, request)


def default_search_content(search_term, request=None):

    searchstring = u'%%%s%%' % search_term

    # generic_filter can be applied to all Node (and subclassed) objects
    generic_filter = or_(Content.name.like(searchstring),
                         Content.title.like(searchstring),
                         Content.description.like(searchstring))

    generic_results = DBSession.query(Content).filter(generic_filter)

    # specific result contain objects matching additional criteria
    # but must not match the generic criteria (because these objects
    # are already in the generic_results)
    document_results = DBSession.query(Document).filter(
        and_(Document.body.like(searchstring),
             not_(generic_filter)))

    all_results = [c for c in generic_results.all()] \
        + [c for c in document_results.all()]

    result_dicts = []

    for result in all_results:
        if has_permission('view', result, request):
            result_dicts.append(dict(
                name=result.name,
                title=result.title,
                description=result.description,
                path=request.resource_path(result)))
    return result_dicts


# BBB starts here --- --- --- --- --- ---

appstruct = get_appstruct
BaseFormView = BaseFormView
AddFormView = AddFormView
EditFormView = EditFormView


deprecated(
    'appstruct',
    'appstruct is deprecated as of Kotti 0.6.2.  Use '
    '``kotti.views.form.get_appstruct`` instead.'
    )

deprecated(
    'get_appstruct',
    'get_appstruct is deprecated as of Kotti 0.6.3.  Use '
    '``kotti.views.form.get_appstruct`` instead.'
    )

deprecated(
    'disambiguate_name',
    'disambiguate_name is deprecated as of Kotti 0.6.2.  Use '
    '``kotti.util.disambiguate_name`` instead.'
    )

for cls in BaseFormView, AddFormView, EditFormView:
    new_name = 'kotti.views.form.{0}'.format(cls.__name__)
    deprecated(
        cls.__name__,
        '{0} is deprecated as of Kotti 0.6.3.  Use ``{1}`` instead.'.format(
            cls.__name__, new_name)
        )
