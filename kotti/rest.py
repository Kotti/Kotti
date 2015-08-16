from kotti.interfaces import IContent, IDocument, IFile, IImage
from pyramid.interfaces import IRequest
from zope.interface import Interface
import colander
import datetime
import decimal
import json


class ISchemaFactory(Interface):
    """ Schema factory
    """

    def __call__(request):
        """ Returns a colander schema for context object """


def serialize(obj, request, view='add', schema=None):
    """ Use an object's schema to serialize to a colander cstruct """
    reg = request.registry

    if schema is None:
        schema = reg.queryMultiAdapter((obj, request), ISchemaFactory, name=view)
        if schema is None:
            schema = reg.queryMultiAdapter((obj, request), ISchemaFactory)


    serialized = schema.serialize(obj.__dict__)
    if not 'id' in serialized:  # colander schemas don't usually expose 'name'
        serialized['id'] = obj.__name__

    return serialized


def content_schema(request, context):
    from kotti.views.edit.content import ContentSchema
    return ContentSchema()


def document_schema(request, context):
    from kotti.views.edit.content import DocumentSchema
    return DocumentSchema()


def file_schema(request, context):
    from kotti.views.edit.content import FileSchema
    # TODO: implement a Base64 file store
    return FileSchema(None)


default_content_schemas = {
    IContent: content_schema,
    IDocument: document_schema,
    IFile: file_schema,
    IImage: file_schema,
}


datetime_types = (datetime.time, datetime.date, datetime.datetime)

class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        """Convert ``obj`` to something JSON encoder can handle."""
        # if isinstance(obj, NamedTuple):
        #     obj = dict((k, getattr(obj, k)) for k in obj.keys())
        if isinstance(obj, decimal.Decimal):
            obj = str(obj)
        elif isinstance(obj, datetime_types):
            obj = str(obj)
        elif obj is colander.null:
            obj = None
        return obj


def to_json(obj):
    return json.dumps(obj, cls=JSONEncoder)


def includeme(config):
    for klass, factory in default_content_schemas.items():
        config.registry.registerAdapter(factory, required=[klass, IRequest],
            provided=ISchemaFactory)

