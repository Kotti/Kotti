""" JSON Encoders, serializers, REST views and miscellaneous utilities

The main focus of this module are the REST views. You can trigger them by making
a request with the ACCEPT value of 'application/vnd.api+json' to any Content
subclass. The HTTP verb used in the request determines the action that is taken.

When making requests and publishing objects, we try to follow the JSONAPI
format.

To serialize objects to JSON we reuse Colander schemas.  All
``kotti.resources.Content`` derivates will be automatically serialized, but
they'll only include the fields in ``ContentSchema``. For custom content types,
you should write a serializer such as this:

    from kotti.views.edit.content import DocumentSchema

    @content_factory(Document)
    def document_schema_factory(context, request):
        from kotti.views.edit.content import DocumentSchema
        return DocumentSchema()

This will also register a content factory for types with name 'Document'.

When deserializing (extracting values from request) we reuse the Colander
schemas to validate those values. Then, these values will be applied to the
context, in POST and PATCH requests. The REST views also handle GET, PUT and
DELETE.

TODO: handle exceptions in the REST view. Any exception should be sent as JSON
response
TODO: handle permissions/security
"""

from kotti.resources import Content, Document, File #, IImage
from kotti.util import _
from kotti.util import title_to_name
from pyramid.httpexceptions import HTTPNoContent
from pyramid.httpexceptions import HTTPCreated
from pyramid.renderers import JSONP, render
from pyramid.view import view_config, view_defaults
from zope.interface import Interface
import colander
import datetime
import decimal
import json
import venusian


class ISchemaFactory(Interface):
    """ A factory for colander schemas.
    """

    def __call__(context, request):
        """ Returns a colander schema instance """


class IContentFactory(Interface):
    """ A factory for content factories. Can be a class, ex: Document
    """

    def __call__(context, request):
        """ Returns a factory that can construct a new object """


def _schema_factory_name(context=None, type_name=None, name=u'default'):

    if not any(map(lambda x: x is not None, [context, type_name])):
        raise Exception("Provide a context or a type name")

    type_name = (context is not None) and context.type_info.name or type_name

    return u"{}/{}".format(type_name, name)


def schema_factory(klass, name=u'default'):
    """ A decorator to be used to mark a function as a serializer.

    The decorated function should return a basic python structure usable (along
    the lines of colander's cstruct) by a JSON encoder.

    It will also register the context class as a factory for that content.
    """

    name = _schema_factory_name(context=klass, name=name)

    def wrapper(wrapped):
        def callback(context, funcname, ob):
            config = context.config.with_package(info.module)
            config.registry.registerUtility(wrapped, ISchemaFactory, name=name)
            config.registry.registerUtility(klass, IContentFactory,
                                            name=klass.type_info.name)

        info = venusian.attach(wrapped, callback, category='pyramid')
        return wrapped

    return wrapper


@schema_factory(Content)
def content_schema_factory(context, request):
    from kotti.views.edit.content import ContentSchema
    return ContentSchema()


@schema_factory(Document)
def document_schema_factory(context, request):
    from kotti.views.edit.content import DocumentSchema
    return DocumentSchema()


@schema_factory(File)
def file_schema_factory(context, request):
    from kotti.views.edit.content import FileSchema
    return FileSchema(None)


ACCEPT = 'application/vnd.api+json'


@view_defaults(name='', accept=ACCEPT, renderer="kotti_jsonp")
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
        data = self.request.json_body['data']

        assert data['id'] == self.context.name
        assert data['type'] == self.context.type_info.name

        schema = schema_factory(self.context, name='edit')(
            self.context, self.request)
        validated = schema.deserialize(data['attributes'])

        for k, v in validated.items():
            setattr(self.context, k, v)

        return self.context

    @view_config(request_method='PATCH')
    def patch(self):
        data = self.request.json_body['data']

        assert data['id'] == self.context.name
        assert data['type'] == self.context.type_info.name

        schema = get_schema(self.context, self.request)
        validated = schema.deserialize(data['attributes'])
        attrs = dict((k, v) for k, v in validated.items()
                     if k in data['attributes'])
        for k, v in attrs.items():
            setattr(self.context, k, v)

        return self.context

    @view_config(request_method='PUT')
    def put(self):
        # we never accept id, it doesn't conform to jsonapi format
        data = self.request.json_body['data']

        name=_schema_factory_name(type_name=data['type'])
        schema_factory = self.request.registry.getUtility(ISchemaFactory,
                                                          name=name)
        schema = schema_factory(None, self.request)
        validated = schema.deserialize(data['attributes'])

        klass = get_factory(self.request, data['type'])
        name = title_to_name(validated['title'], blacklist=self.context.keys())
        new_item = self.context[name] = klass(**validated)

        response = HTTPCreated()
        response.body = render('kotti_jsonp', new_item, self.request)
        return response

    @view_config(request_method='DELETE')
    def delete(self):
        # data = self.request.json_body['data']

        parent = self.context.__parent__
        del parent[self.context.__name__]
        return HTTPNoContent()


def get_schema(obj, request, name=u'default'):
    factory_name = _schema_factory_name(context=obj, name=name)
    schema_factory = request.registry.getUtility(ISchemaFactory,
                                                 name=factory_name)
    return schema_factory(obj, request)


def get_factory(request, name):
    return request.registry.getUtility(IContentFactory, name=name)


# def filter_schema(schema, allowed_fields):
#     """ Filters a schema to include only allowed fields
#     """
#
#     cloned = schema.__class__(self.typ)
#     cloned.__dict__.update(schema.__dict__)
#     cloned.children = [node.clone() for node in self.children
#                        if node.name in allowed_fields]
#     return cloned
#

class MetadataSchema(colander.MappingSchema):
    """ Schema that exposes some metadata information about a content
    """

    modification_date = colander.SchemaNode(
        colander.Date(),
        title=_(u'Modification Date'),
    )

    creation_date = colander.SchemaNode(
        colander.Date(),
        title=_(u'Modification Date'),
    )

    state = colander.SchemaNode(
        colander.String(),
        title=_(u'State'),
    )
    state = colander.SchemaNode(
        colander.String(),
        title=_(u'State'),
    )

    default_view = colander.SchemaNode(
        colander.String(),
        title=_(u'Default view'),
    )

    in_navigation = colander.SchemaNode(
        colander.String(),
        title=_(u'In navigation'),
    )


def serialize(obj, request, name=u'default'):
    """ Serialize a Kotti content item.

    The response JSON conforms with JSONAPI standard.

    TODO: implement JSONAPI filtering and pagination.
    """
    data = get_schema(obj, request, name).serialize(obj.__dict__)

    res = {}
    res['type'] = obj.type_info.name
    res['id'] = obj.__name__
    res['attributes'] = data
    res['links'] = {
        'self': request.resource_url(obj),
        'children': [request.resource_url(child)
                     for child in obj.children_with_permission(request)]
    }
    meta = MetadataSchema().serialize(obj.__dict__)

    return dict(data=res, meta=meta)


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
            elif isinstance(obj,
                            (datetime.time, datetime.date, datetime.datetime)):
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
