from pyramid.compat import json
import urllib

from plone.i18n.normalizer import urlnormalizer
from pyramid.i18n import get_locale_name
from pyramid.threadlocal import get_current_request
from pyramid.url import resource_url
from repoze.lru import LRUCache
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import Mutable

def dump_default(obj):
    if isinstance(obj, MutationDict):
        return obj._d
    elif isinstance(obj, MutationList):
        return obj._d

class JsonType(TypeDecorator):
    """http://www.sqlalchemy.org/docs/core/types.html#marshal-json-strings
    """
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, default=dump_default)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class MutationDict(Mutable):
    """http://www.sqlalchemy.org/docs/orm/extensions/mutable.html
    """
    def __init__(self, data):
        self._d = data
        super(MutationDict, self).__init__()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return cls(value)
            return Mutable.coerce(key, value)
        else:
            return value

class MutationList(Mutable):
    def __init__(self, data):
        self._d = data
        super(MutationList, self).__init__()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutationList):
            if isinstance(value, list):
                return cls(value)
            return Mutable.coerce(key, value)
        else:
            return value

    def __radd__(self, other):
        return other + self._d

def _make_mutable_method_wrapper(wrapper_class, methodname, mutates):
    def replacer(self, *args, **kwargs):
        method = getattr(self._d, methodname)
        value = method(*args, **kwargs)
        if mutates:
            self.changed()
        return value
    replacer.__name__ = methodname
    return replacer

for wrapper_class in (MutationDict, MutationList):
    for methodname, mutates in (
        ('__iter__', False),
        ('__len__', False),
        ('__eq__', False),
        ('__add__', False),
        ('get', False),
        ('keys', False),

        ('__setitem__', True),
        ('__delitem__', True),
        ('append', True),
        ('insert', True),
        ('setdefault', True),
        ):
        setattr(
            wrapper_class, methodname,
            _make_mutable_method_wrapper(
                wrapper_class, methodname, mutates),
            )

class NestedMixin(object):
    __parent__ = None
    
    def __init__(self, *args, **kwargs):
        self.__parent__ = kwargs.pop('__parent__', None)
        super(NestedMixin, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        value = self._d.__getitem__(key)
        return self.try_wrap(value)

    def changed(self):
        if self.__parent__ is not None:
            self.__parent__.changed()
        else:
            super(NestedMixin, self).changed()

    def try_wrap(self, value):
        for typ, wrapper in MUTATION_WRAPPERS.items():
            if isinstance(value, typ):
                value = wrapper(value, __parent__=self)
                break
        return value

class NestedMutationDict(NestedMixin, MutationDict):
    pass

class NestedMutationList(NestedMixin, MutationList):
    pass

MUTATION_WRAPPERS = {
    dict: NestedMutationDict,
    list: NestedMutationList,
    }

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

def clear_cache(): # only useful for tests really
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

def title_to_name(title):
    request = get_current_request()
    if request is not None:
        locale_name = get_locale_name(request)
    else:
        locale_name = 'en'
    return unicode(urlnormalizer.normalize(title, locale_name))
