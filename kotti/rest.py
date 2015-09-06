""" JSON Encoders, serializers, REST views and utilities
"""

from kotti.resources import Content, Document, File #, IImage
from pyramid.interfaces import IRequest
from pyramid.renderers import JSONP
from pyramid.view import view_config, view_defaults
from zope.interface import Interface
import colander
import datetime
import decimal
import json
import venusian


class ISerializer(Interface):
    """ A serializer to change objects to colander cstructs
    """

    def __call__(request):
        """ Returns a colander cstruct for context object """


def serialize(obj, request, name=None):
    """ Serialize an object with the most appropriate serializer
    """

    reg = request.registry

    if name is None:
        name = obj.type_info.name

    serialized = reg.queryMultiAdapter((obj, request), ISerializer, name=name)
    if serialized is None:
        serialized = reg.queryMultiAdapter((obj, request), ISerializer)

    if not 'id' in serialized:  # colander schemas don't usually expose 'name'
        serialized['id'] = obj.__name__

    return serialized


def serializes(klass, name=None):
    """ A decorator to be used to mark a function as a serializer.

    The decorated function should return a basic python structure usable (along
    the lines of colander's cstruct) by a JSON encoder.
    """

    if name is None:
        name = klass.type_info.name

    def wrapper(wrapped):
        def callback(context, funcname, ob):
            config = context.config.with_package(info.module)
            config.registry.registerAdapter(
                wrapped, required=[Content, IRequest],
                provided=ISerializer, name=name
            )

        info = venusian.attach(wrapped, callback, category='pyramid')

        return wrapped

    return wrapper


@serializes(Content)
def content_serializer(context, request):
    from kotti.views.edit.content import ContentSchema
    return ContentSchema().serialize(context.__dict__)


@serializes(Document)
def document_serializer(context, request):
    from kotti.views.edit.content import DocumentSchema
    return DocumentSchema().serialize(context.__dict__)


@serializes(File)
def file_serializer(context, request):
    from kotti.views.edit.content import FileSchema
    return FileSchema(None).serialize(context.__dict__)


ACCEPT = 'application/vnd.api+json'

@view_defaults(name='json', accept=ACCEPT, renderer="kotti_jsonp")
class RestView(object):
    """ A generic @@json view for any and all contexts.

    Its response depends on the HTTP verb used. For ex:
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(request_method='GET')
    def get(self):
        return self.context

    @view_config(request_method='POST')
    def post(self):
        pass

    @view_config(request_method='PATCH')
    def patch(self):
        pass

    @view_config(request_method='PUT')
    def put(self):
        data = self.request.form.get('data')
        type_ = data['type']
        pass

    @view_config(request_method='DELETE')
    def delete(self):
        pass


datetime_types = (datetime.time, datetime.date, datetime.datetime)

def _encoder(basedefault):
    """ A JSONEncoder that can encode some basic odd objects.

    For most objects it will execute the basedefault function, which uses
    adapter lookup mechanism to achieve the encoding, but for some basic
    objects, such as datetime and colander.null we solve it here.
    """

    class Encoder(json.JSONEncoder):

        def default(self, obj):
            """Convert ``obj`` to something JSON encoder can handle."""
            # if isinstance(obj, NamedTuple):
            #     obj = dict((k, getattr(obj, k)) for k in obj.keys())
            if isinstance(obj, decimal.Decimal):
                return str(obj)
            elif isinstance(obj, datetime_types):
                return str(obj)
            elif obj is colander.null:
                return None

            return basedefault(obj)

    return Encoder


def to_json(obj, default=None, **kw):
    return json.dumps(obj, cls=_encoder(default), **kw)


jsonp = JSONP(param_name='callback', serializer=to_json)
jsonp.add_adapter(Content, serialize)


def includeme(config):

    config.add_renderer('kotti_jsonp', jsonp)
    config.scan(__name__)

