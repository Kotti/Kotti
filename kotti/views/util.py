import hashlib
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlencode

from babel.dates import format_date
from babel.dates import format_datetime
from babel.dates import format_time
from babel.numbers import format_currency
from pyramid.decorator import reify
from pyramid.i18n import get_locale_name
from pyramid.interfaces import ILocation
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.renderers import render
from pyramid.settings import asbool
from sqlalchemy import and_
from sqlalchemy import not_
from sqlalchemy import or_

from kotti import DBSession
from kotti import get_settings
from kotti.events import objectevent_listeners
from kotti.interfaces import INavigationRoot
from kotti.resources import Content, Node
from kotti.resources import Document
from kotti.resources import Tag
from kotti.resources import TagsToContents
from kotti.resources import get_root
from kotti.sanitizers import sanitize
from kotti.security import view_permitted
from kotti.util import TemplateStructure
from kotti.util import render_view
from kotti.views.site_setup import CONTROL_PANEL_LINKS
from kotti.views.slots import slot_events


class SettingHasValuePredicate(object):
    def __init__(self, val, config):
        self.name, self.value = val
        if not isinstance(self.value, bool):
            raise ValueError("Only boolean values supported")

    def text(self):
        return 'if_setting_has_value = {0} == {1}'.format(
            self.name, self.value)

    phash = text

    def __call__(self, context, request):
        return asbool(request.registry.settings[self.name]) == self.value


class RootOnlyPredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'root_only = {0}'.format(self.val)

    phash = text

    def __call__(self, context, request):
        return (context is request.root) == self.val


def template_api(context, request, **kwargs):
    return get_settings()['kotti.templates.api'][0](
        context, request, **kwargs)


def add_renderer_globals(event):
    if event.get('renderer_name') != 'json':
        request = event['request']
        api = getattr(request, 'template_api', None)
        if api is None and request is not None:
            api = template_api(event['context'], event['request'])
        event['api'] = api


class Slots(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __getattr__(self, key):
        for event_type in slot_events:
            if event_type.name == key:
                break
        else:
            raise AttributeError(key)
        value = []
        event = event_type(self.context, self.request)
        for snippet in objectevent_listeners(event):
            if snippet is not None:
                if isinstance(snippet, list):
                    value.extend(snippet)
                else:
                    value.append(snippet)
        setattr(self, key, value)
        return value


class TemplateAPI(object):
    """This implements the ``api`` object that's passed to all templates.

    Use dict-access as a shortcut to retrieve template macros from templates.
    """

    # Instead of overriding these, consider using the
    # ``kotti.overrides`` variable.
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

    @staticmethod
    def is_location(context):
        """Does `context` implement :class:`pyramid.interfaces.ILocation`?

        :param context: The context.
        :type context: kotti.interfaces.INode
        :rtype: bool
        :returns: True if Is the context object implements
                  :class:`pyramid.interfaces.ILocation`.
        """
        return ILocation.providedBy(context)

    @reify
    def edit_needed(self):
        if 'kotti.fanstatic.edit_needed' in self.S:
            return [r.need() for r in self.S['kotti.fanstatic.edit_needed']]

    @reify
    def view_needed(self):
        if 'kotti.fanstatic.view_needed' in self.S:
            return [r.need() for r in self.S['kotti.fanstatic.view_needed']]

    def macro(self, asset_spec, macro_name='main'):
        if self.bare and asset_spec in (
                self.VIEW_MASTER, self.EDIT_MASTER, self.SITE_SETUP_MASTER):
            asset_spec = self.BARE_MASTER
        return get_renderer(asset_spec).implementation().macros[macro_name]

    @reify
    def site_title(self):
        """ The site title.

        :result: Value of the ``kotti.site_title`` setting (if specified) or
                 the root item's ``title`` attribute.
        :rtype: str
        """
        value = get_settings().get('kotti.site_title')
        if not value:
            value = self.root.title
        return value

    @reify
    def page_title(self):
        """
        Title for the current page as used in the ``<head>`` section of the
        default ``master.pt`` template.

        :result: '[Human readable view title ]``context.title`` -
                 :meth:`~TemplateAPI.site_title`''
        :rtype: str
        """

        view_title = self.request.view_name.replace('_', ' ').title()
        if view_title:
            view_title += ' '
        view_title += self.context.title
        return '{0} - {1}'.format(view_title, self.site_title)

    def url(self, context=None, *elements, **kwargs):
        """
        URL construction helper. Just a convenience wrapper for
        :func:`pyramid.request.resource_url` with the same signature.  If
        ``context`` is ``None`` the current context is passed to
        ``resource_url``.
        """

        if context is None:
            context = self.context
        if not ILocation.providedBy(context):
            return self.request.url
        return self.request.resource_url(context, *elements, **kwargs)

    @reify
    def root(self):
        """
        The site root.

        :result: The root object of the site.
        :rtype: :class:`kotti.resources.Node`
        """

        if ILocation.providedBy(self.context):
            return self.lineage[-1]
        else:
            return get_root()

    @reify
    def navigation_root(self):
        """
        The root node for the navigation.

        :result: Nearest node in the :meth:`lineage` that provides
                 :class:`kotti.interfaces.INavigationRoot` or :meth:`root` if
                 no node provides that interface.
        :rtype: :class:`kotti.resources.Node`
        """
        for o in self.lineage:
            if INavigationRoot.providedBy(o):
                return o
        return self.root

    @reify
    def lineage(self):
        """
        Lineage from current context to the root node.

        :result: List of nodes.
        :rtype: list of :class:`kotti.resources.Node`
        """
        return list(lineage(self.context))

    @reify
    def breadcrumbs(self):
        """
        List of nodes from the :meth:`navigation_root` to the context.

        :result: List of nodes.
        :rtype: list of :class:`kotti.resources.Node`
        """
        breadcrumbs = self.lineage
        if self.root != self.navigation_root:
            index = breadcrumbs.index(self.navigation_root)
            breadcrumbs = breadcrumbs[:index + 1]
        return reversed(breadcrumbs)

    def has_permission(self, permission, context=None):
        """ Convenience wrapper for :func:`pyramid.security.has_permission`
        with the same signature.  If ``context`` is ``None`` the current
        context is passed to ``has_permission``."""
        if context is None:
            context = self.context
        return self.request.has_permission(permission, context)

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

        if isinstance(context, Node):
            if permission is None:
                return context.children
            return context.children_with_permission(self.request, permission)

        return [c for c in getattr(context, 'values', lambda: [])()
                if (not permission or
                    self.request.has_permission(permission, c))]

    inside = staticmethod(inside)

    def avatar_url(self, user=None, size="14", default_image='identicon'):
        if user is None:
            user = self.request.user
        email = user.email
        if not email:
            email = user.name
        h = hashlib.md5(email.encode('utf8')).hexdigest()
        query = {'default': default_image, 'size': str(size)}
        url = 'https://secure.gravatar.com/avatar/{0}?{1}'.format(
            h, urlencode(query))
        return url

    @reify
    def locale_name(self):
        return get_locale_name(self.request)

    def format_date(self, d, fmt=None):
        if fmt is None:
            fmt = self.S['kotti.date_format']
        return format_date(d, format=fmt, locale=self.locale_name)

    def format_datetime(self, dt, fmt=None):
        if fmt is None:
            fmt = self.S['kotti.datetime_format']
        if not isinstance(dt, datetime):
            dt = datetime.fromtimestamp(dt)
        return format_datetime(dt, format=fmt, locale=self.locale_name)

    def format_time(self, t, fmt=None):
        if fmt is None:
            fmt = self.S['kotti.time_format']
        return format_time(t, format=fmt, locale=self.locale_name)

    def format_currency(self, n, currency, fmt=None):
        return format_currency(n, currency,
                               format=fmt, locale=self.locale_name)

    @staticmethod
    def get_type(name):
        for class_ in get_settings()['kotti.available_types']:
            if class_.type_info.name == name:
                return class_

    def find_edit_view(self, item):
        view_name = self.request.view_name
        if not view_permitted(item, self.request, view_name):
            view_name = 'edit'
        if not view_permitted(item, self.request, view_name):
            view_name = ''
        return view_name

    @reify
    def edit_links(self):
        if not hasattr(self.context, 'type_info'):
            return []
        return [l for l in self.context.type_info.edit_links
                if l.visible(self.context, self.request)]

    @reify
    def site_setup_links(self):
        return [l for l in CONTROL_PANEL_LINKS
                if l.visible(self.root, self.request)]

    @staticmethod
    def sanitize(html, sanitizer='default'):
        """ Convenience wrapper for :func:`kotti.sanitizers.sanitize`.

        :param html: HTML to be sanitized
        :type html: str

        :param sanitizer: name of the sanitizer to use.
        :type sanitizer: str

        :result: sanitized HTML
        :rtype: str
        """

        return sanitize(html, sanitizer)


class NodesTree(object):
    def __init__(self, node, request, item_mapping, item_to_children,
                 permission):
        self._node = node
        self._request = request
        self._item_mapping = item_mapping
        self._item_to_children = item_to_children
        self._permission = permission

    @property
    def __parent__(self):
        if self.parent_id:
            return self._item_mapping[self.parent_id]

    @property
    def children(self):
        return [
            NodesTree(
                child,
                self._request,
                self._item_mapping,
                self._item_to_children,
                self._permission,
            )
            for child in self._item_to_children[self.id]
            if self._request.has_permission(self._permission, child)
        ]

    def _flatten(self, item):
        # noinspection PyProtectedMember
        yield item._node
        for ch in item.children:
            for item in self._flatten(ch):
                yield item

    def tolist(self):
        return list(self._flatten(self))

    def __getattr__(self, key):
        return getattr(self._node, key)


def nodes_tree(request, context=None, permission='view'):
    item_mapping = {}
    item_to_children = defaultdict(lambda: [])
    for node in DBSession.query(Content).with_polymorphic(Content):
        item_mapping[node.id] = node
        if request.has_permission(permission, node):
            item_to_children[node.parent_id].append(node)

    for children in item_to_children.values():
        children.sort(key=lambda ch: ch.position)

    if context is None:
        node = item_to_children[None][0]
    else:
        node = context

    return NodesTree(
        node,
        request,
        item_mapping,
        item_to_children,
        permission,
    )


def search_content(search_term, request=None):
    return get_settings()['kotti.search_content'][0](search_term, request)


def default_search_content(search_term, request=None):

    # noinspection PyUnresolvedReferences
    searchstring = '%{0}%'.format(search_term)

    # generic_filter can be applied to all Node (and subclassed) objects
    generic_filter = or_(Content.name.like(searchstring),
                         Content.title.like(searchstring),
                         Content.description.like(searchstring))

    results = DBSession.query(Content).filter(generic_filter).\
        order_by(Content.title.asc()).all()

    # specific result contain objects matching additional criteria
    # but must not match the generic criteria (because these objects
    # are already in the generic_results)
    document_results = DBSession.query(Document).filter(
        and_(Document.body.like(searchstring),
             not_(generic_filter)))

    for results_set in [content_with_tags([searchstring]),
                        document_results.all()]:
        [results.append(c) for c in results_set if c not in results]

    result_dicts = []

    for result in results:
        if request.has_permission('view', result):
            result_dicts.append(dict(
                name=result.name,
                title=result.title,
                description=result.description,
                path=request.resource_path(result)))

    return result_dicts


def content_with_tags(tag_terms):

    return DBSession.query(Content).join(TagsToContents).join(Tag).filter(
        or_(*[Tag.title.like(tag_term) for tag_term in tag_terms])).all()


def search_content_for_tags(tags, request=None):

    result_dicts = []

    for result in content_with_tags(tags):
        if request.has_permission('view', result):
            result_dicts.append(dict(
                name=result.name,
                title=result.title,
                description=result.description,
                path=request.resource_path(result)))

    return result_dicts


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.add_view_predicate('root_only', RootOnlyPredicate)
    config.add_view_predicate('if_setting_has_value', SettingHasValuePredicate)
