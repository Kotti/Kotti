import json
import urllib

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
