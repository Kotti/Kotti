import re
import urllib

from docopt import docopt
from plone.i18n.normalizer import urlnormalizer
from pyramid.i18n import get_locale_name
from pyramid.i18n import TranslationStringFactory
from pyramid.paster import bootstrap
from pyramid.threadlocal import get_current_request
from pyramid.url import resource_url
from repoze.lru import LRUCache
from zope.deprecation import deprecated

_ = TranslationStringFactory('Kotti')


class ViewLink(object):
    def __init__(self, path, title=None):
        self.path = path
        if title is None:
            title = path.replace('-', ' ').replace('_', ' ').title()
        self.title = title

    def url(self, context, request):
        return resource_url(context, request) + '@@' + self.path

    def selected(self, context, request):
        return urllib.unquote(request.url).startswith(
            self.url(context, request))

    def permitted(self, context, request):
        from kotti.security import view_permitted
        return view_permitted(context, request, self.path)

    def __eq__(self, other):
        return isinstance(other, ViewLink) and repr(self) == repr(other)

    def __repr__(self):
        return "ViewLink(%r, %r)" % (self.path, self.title)


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
                #print "\n*** MISS %r ***" % key
                cached_value = cache[key] = func(*args, **kwargs)
            else:
                #print "\n*** HIT %r ***" % key
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
    name = unicode(urlnormalizer.normalize(title, locale_name, max_length=40))
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
