from UserDict import DictMixin
from pyramid.compat import json
import string
import urllib

from repoze.lru import LRUCache
from pyramid.threadlocal import get_current_request
from pyramid.url import resource_url
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import Mutable

class JsonType(TypeDecorator):
    """http://www.sqlalchemy.org/docs/core/types.html#marshal-json-strings
    """
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class MutationDict(Mutable, dict):
    """http://www.sqlalchemy.org/docs/orm/extensions/mutable.html
    """
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()

def _keyerror_to_attributeerror(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            raise AttributeError(*e.args)
    return decorator

class MutableAnnotationsWrapper(object, DictMixin):
    def __init__(self, data, mutable):
        self.__dict__['__data__'] = data
        self.__dict__['__mutable__'] = mutable

    def changed(self):
        self.__mutable__.changed()

    def __getitem__(self, key):
        value = self.__data__[key]
        if isinstance(value, dict):
            value = self.__class__(value, self.__mutable__)
        return value
    __getattr__ = _keyerror_to_attributeerror(__getitem__)

    def __setitem__(self, key, value):
        self.__data__[key] = value
        self.changed()
    __setattr__ = _keyerror_to_attributeerror(__setitem__)

    def __delitem__(self, key):
        del self.__data__[key]
        self.changed()
    __delattr__ = _keyerror_to_attributeerror(__delitem__)

    def keys(self):
        return self.__data__.keys()

class MutableAnnotationsMixin(object):
    @property
    def __annotations__(self):
        return MutableAnnotationsWrapper(self.annotations, self.annotations)

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

def extract_from_settings(prefix):
    """
      >>> from pyramid.threadlocal import get_current_registry
      >>> get_current_registry().settings = {
      ...     'kotti_twitter.foo_bar': '1', 'kotti.spam_eggs': '2'}
      >>> print extract_from_settings('kotti_twitter.')
      {'foo_bar': '1'}
    """
    from kotti import get_settings
    extracted = {}
    for key, value in get_settings().items():
        if key.startswith(prefix):
            extracted[key[len(prefix):]] = value
    return extracted

def title_to_name(title):
    okay = string.letters + string.digits + '-'
    name = u'-'.join(title.lower().split())
    name = u''.join(ch for ch in name if ch in okay)
    return name
