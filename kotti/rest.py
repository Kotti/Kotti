""" JSON Encoders, serializers, REST views and utilities


WIP: we need schema factory.

We need to serialize an object, to publish it as JSON.

We need to extract appropriate struct from json by calling schema().deserialize(form)

We need to be able to have different schema factories, based on 'view' name and content type name.

We want to have flexible schema factories that can take various discriminators:
    * optional - the context object for which we want a schema
    * optional - the schema 'type'. It can be 'default', 'edit', 'view', etc.
    * optional - the schema content type name. Useful when we want to build new
                 objects

def get_schema_factory(context=None, type_='default', name=None):
    if not (context or name):
        raise Exception("Need an object for context or a content type name")


"""

from kotti.resources import Content, Document, File #, IImage
from pyramid.renderers import JSONP
from pyramid.view import view_config, view_defaults
from zope.interface import Interface
import colander
import datetime
import decimal
import json
import venusian


class ISchemaFactory(Interface):
    """ A factory that can return a schema
    """

    def __call__(context, request):
        """ Returns a colander schema instance """


def _schema_factory_name(context=None, type_name=None, name=u'default'):

    if (context is None) and (type_name is None):
        raise Exception("Need a context or a type name")

    if (context is not None) and (type_name is None):
        type_name = context.type_info.name

    return u"{}/{}".format(type_name, name)


def schema_factory(klass, name=u'default'):
    """ A decorator to be used to mark a function as a serializer.

    The decorated function should return a basic python structure usable (along
    the lines of colander's cstruct) by a JSON encoder.
    """

    name = _schema_factory_name(context=klass, name=name)

    def wrapper(wrapped):
        def callback(context, funcname, ob):
            config = context.config.with_package(info.module)
            config.registry.registerUtility(wrapped, ISchemaFactory, name=name)

        info = venusian.attach(wrapped, callback, category='pyramid')
        return wrapped

    return wrapper


@schema_factory(Content)
def content_serializer(context, request):
    from kotti.views.edit.content import ContentSchema
    return ContentSchema()


@schema_factory(Document)
def document_serializer(context, request):
    from kotti.views.edit.content import DocumentSchema
    return DocumentSchema()


@schema_factory(File)
def file_serializer(context, request):
    from kotti.views.edit.content import FileSchema
    return FileSchema(None)


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
        schema = schema_factory(self.context, name='edit')(
            self.context, self.request)
        validated = schema.deserialize(self.request.form.get('data'))
        self.context.__dict__.update(**validated)

    @view_config(request_method='PATCH')
    def patch(self):
        # data, type, id
        # data = {}
        # context = self.context
        # attrs = data['attributes']
        # schema = get_schema(obj, request)
        pass

    @view_config(request_method='PUT')
    def put(self):
        # we never accept id, it doesn't conform to jsonapi format
        return

    @view_config(request_method='DELETE')
    def delete(self):
        pass


def get_schema(obj, request, name=u'default'):
    factory_name = _schema_factory_name(context=obj, name=name)
    schema_factory = request.registry.getUtility(ISchemaFactory,
                                                 name=factory_name)
    return schema_factory(obj, request)


def serialize(obj, request, name=u'default'):
    """ Serialize an object with the most appropriate serializer
    """
    serialized = get_schema(obj, request, name).serialize(obj.__dict__)

    if not 'id' in serialized:  # colander schemas don't usually expose 'name'
        serialized['id'] = obj.__name__

    return serialized


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
