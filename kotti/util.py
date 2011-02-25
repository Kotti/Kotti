from pyramid.compat import json
import urllib

from pyramid.threadlocal import get_current_request
from pyramid.url import resource_url
from pyramid.security import view_execution_permitted
from sqlalchemy.types import TypeDecorator, VARCHAR

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
        return view_execution_permitted(context, request, self.path)

    def __eq__(self, other):
        return isinstance(other, ViewLink) and repr(self) == repr(other)

    def __repr__(self):
        return "ViewLink(%r, %r)" % (self.path, self.title)

_CACHE_ATTR = 'kotti_cache'

class DontCache(Exception):
    pass

def request_cache(compute_key):
    marker = object()
    def decorator(func):
        def replacement(*args, **kwargs):
            request = get_current_request()
            if request is None:
                return func(*args, **kwargs)
            cache = getattr(request, _CACHE_ATTR, None)
            if cache is None:
                cache = {}
                setattr(request, _CACHE_ATTR, cache)
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

def clear_request_cache(): # only useful for tests really
    request = get_current_request()
    if request is not None:
        setattr(request, _CACHE_ATTR, None)
