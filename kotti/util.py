# -*- coding: utf-8 -*-

"""
Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.util
"""

import re
import urllib

from docopt import docopt
from pyramid.i18n import get_localizer
from pyramid.i18n import get_locale_name
from pyramid.i18n import make_localizer
from pyramid.i18n import TranslationStringFactory
from pyramid.interfaces import ITranslationDirectories
from pyramid.location import inside
from pyramid.paster import bootstrap
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from pyramid.threadlocal import get_current_request
from pyramid.url import resource_url
from pyramid.view import render_view_to_response
from repoze.lru import LRUCache
from zope.deprecation import deprecated

from kotti import DBSession

_ = TranslationStringFactory('Kotti')


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


def get_paste_items(context, request):
    from kotti.resources import Node

    items = []
    info = request.session.get('kotti.paste')
    if info:
        ids, action = info
        for id in ids:
            item = DBSession.query(Node).get(id)
            if item is None or not item.type_info.addable(context, request):
                continue
            if action == 'cut' and inside(context, item):
                continue
            if context == item:
                continue
            items.append(item)
    return items


def render_view(context, request, name='', secure=True):
    from kotti.security import authz_context

    with authz_context(context, request):
        response = render_view_to_response(context, request, name, secure)
    if response is not None:
        return response.ubody


class TemplateStructure(object):
    def __init__(self, html):
        self.html = html

    def __html__(self):
        return self.html
    __unicode__ = __html__

    def __getattr__(self, key):
        return getattr(self.html, key)


class LinkBase(object):
    def __call__(self, context, request):
        return TemplateStructure(
            render(
                self.template,
                dict(link=self, context=context, request=request),
                request,
                )
            )

    def selected(self, context, request):
        return urllib.unquote(request.url).startswith(
            self.url(context, request))

    def permitted(self, context, request):
        from kotti.security import view_permitted
        return view_permitted(context, request, self.name)

    def visible(self, context, request):
        permitted = self.permitted(context, request)
        if permitted:
            if self.predicate is not None:
                return self.predicate(context, request)
            else:
                return True
        return False

    @property
    def path(self):  # BBB
        return self.name
    path = deprecated(
        path,
        "The 'path' attribute has been deprecated as of Kotti 0.10.  Please "
        "use 'name' instead.",
        )


class LinkRenderer(LinkBase):
    """A menu link that renders a view to render the link.
    """
    def __init__(self, name, predicate=None):
        self.name = name
        self.predicate = predicate

    def __call__(self, context, request):
        return TemplateStructure(render_view(context, request, name=self.name))

    def selected(self, context, request):
        return False


class LinkParent(LinkBase):
    """A menu link that renders sublinks in a dropdown.
    """
    template = 'kotti:templates/edit/el-parent.pt'

    def __init__(self, title, children):
        self.title = title
        self.children = children

    def visible(self, context, request):
        return any([ch.visible(context, request) for ch in self.children])

    def selected(self, context, request):
        return any([ch.selected(context, request) for ch in self.children])

    def get_visible_children(self, context, request):
        return [ch for ch in self.children if ch.visible(context, request)]


class Link(LinkBase):
    template = 'kotti:templates/edit/el-link.pt'

    def __init__(self, name, title=None, predicate=None):
        self.name = name
        if title is None:
            title = name.replace('-', ' ').replace('_', ' ').title()
        self.title = title
        self.predicate = predicate

    def url(self, context, request):
        return resource_url(context, request) + '@@' + self.name

    def selected(self, context, request):
        return urllib.unquote(request.url).startswith(
            self.url(context, request))

    def __eq__(self, other):
        return isinstance(other, Link) and repr(self) == repr(other)

    def __repr__(self):
        return "Link(%r, %r)" % (self.name, self.title)


class ActionButton(Link):
    def __init__(self, path, title=None, no_children=False, css_class=u"btn"):
        super(ActionButton, self).__init__(path, title)
        self.no_children = no_children
        self.css_class = css_class


class DontCache(Exception):
    pass

_CACHE_ATTR = 'kotti_cache'


def request_container():
    request = get_current_request()
    if request is None:
        return None
    cache = getattr(request, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _CACHE_ATTR, cache)
    return cache


def cache(compute_key, container_factory):
    marker = object()

    def decorator(func):
        def replacement(*args, **kwargs):
            cache = container_factory()
            if cache is None:
                return func(*args, **kwargs)
            try:
                key = compute_key(*args, **kwargs)
            except DontCache:
                return func(*args, **kwargs)
            key = '%s.%s:%s' % (func.__module__, func.__name__, key)
            cached_value = cache.get(key, marker)
            if cached_value is marker:
                cached_value = cache[key] = func(*args, **kwargs)
            else:
                pass
            return cached_value
        replacement.__doc__ = func.__doc__
        return replacement
    return decorator


def request_cache(compute_key):
    return cache(compute_key, request_container)


class LRUCacheSetItem(LRUCache):
    __setitem__ = LRUCache.put

_lru_cache = LRUCacheSetItem(1000)


def lru_cache(compute_key):
    return cache(compute_key, lambda: _lru_cache)


def clear_cache():  # only useful for tests really
    request = get_current_request()
    if request is not None:
        setattr(request, _CACHE_ATTR, None)
    _lru_cache.clear()


def extract_from_settings(prefix, settings=None):
    """
      >>> settings = {
      ...     'kotti_twitter.foo_bar': '1', 'kotti.spam_eggs': '2'}
      >>> print extract_from_settings('kotti_twitter.', settings)
      {'foo_bar': '1'}
    """
    from kotti import get_settings
    settings = settings if settings is not None else get_settings()
    extracted = {}
    for key, value in settings.items():
        if key.startswith(prefix):
            extracted[key[len(prefix):]] = value
    return extracted


def disambiguate_name(name):
    parts = name.split(u'-')
    if len(parts) > 1:
        try:
            index = int(parts[-1])
        except ValueError:
            parts.append(u'1')
        else:
            parts[-1] = unicode(index + 1)
    else:
        parts.append(u'1')
    return u'-'.join(parts)


def title_to_name(title, blacklist=()):
    request = get_current_request()
    if request is not None:
        locale_name = get_locale_name(request)
    else:
        locale_name = 'en'
    from kotti import get_settings
    urlnormalizer = get_settings()['kotti.url_normalizer'][0]
    name = unicode(urlnormalizer(title, locale_name, max_length=40))
    while name in blacklist:
        name = disambiguate_name(name)
    return name


def camel_case_to_name(text):
    """
      >>> camel_case_to_name('FooBar')
      'foo_bar'
      >>> camel_case_to_name('TXTFile')
      'txt_file'
      >>> camel_case_to_name ('MyTXTFile')
      'my_txt_file'
      >>> camel_case_to_name('froBOZ')
      'fro_boz'
      >>> camel_case_to_name('f')
      'f'
    """
    return re.sub(
        r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r'_\1', text).lower()


def command(func, doc):
    args = docopt(doc)
    pyramid_env = bootstrap(args['<config_uri>'])
    try:
        func(args)
    finally:
        pyramid_env['closer']()
    return 0


from kotti.sqla import JsonType
from kotti.sqla import MutationDict
from kotti.sqla import MutationList
from kotti.sqla import NestedMixin
from kotti.sqla import NestedMutationDict
from kotti.sqla import NestedMutationList


for cls in (JsonType, MutationDict, MutationList, NestedMixin,
            NestedMutationDict, NestedMutationList):
    name = cls.__name__
    deprecated(
        name,
        "kotti.util.{0} has been moved to the kotti.sqla "
        "module as of Kotti 0.6.0.  Use kotti.sqla.{0} instead".format(name)
        )


ViewLink = Link
deprecated(
    'ViewLink',
    "kotti.util.ViewLink has been renamed to Link as of Kotti 0.10."
    )
