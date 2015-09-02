from kotti.resources import Document
from pyramid.renderers import JSONP
from pyramid.view import view_config, view_defaults
import colander
import datetime
import decimal
import json


def content_serializer(context, request):
    from kotti.views.edit.content import ContentSchema
    return ContentSchema().serialize(context.__dict__)


def document_serializer(context, request):
    from kotti.views.edit.content import DocumentSchema
    return DocumentSchema().serialize(context.__dict__)


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
        pass

    @view_config(request_method='DELETE')
    def delete(self):
        pass


datetime_types = (datetime.time, datetime.date, datetime.datetime)

def _encoder(basedefault):
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
jsonp.add_adapter(Document, document_serializer)

def includeme(config):

    config.add_renderer('kotti_jsonp', jsonp)
    config.scan(__name__)

