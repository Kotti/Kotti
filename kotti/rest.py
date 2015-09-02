# import venusian
#from kotti.interfaces import IContent, IDocument, IFile #, IImage
#from pyramid.interfaces import IRequest
#from pyramid.response import Response
#from zope.interface import Interface

from kotti.resources import Document
from pyramid.view import view_config, view_defaults
import colander
import datetime
import decimal
import json


# class ISerializer(Interface):
#     """ A serializer to change objects to colander cstructs
#     """
#
#     def __call__(request):
#         """ Returns a colander cstruct for context object """
#
#
# def serialize(obj, request, view='add'):
#     """ Use an object's schema to serialize to a colander cstruct """
#     reg = request.registry
#
#     serialized = reg.queryMultiAdapter((obj, request), ISerializer, name=view)
#     if serialized is None:
#         serialized = reg.queryMultiAdapter((obj, request), ISerializer)
#
#     if not 'id' in serialized:  # colander schemas don't usually expose 'name'
#         serialized['id'] = obj.__name__
#
#     return serialized
#
#
# def serializes(iface_or_class, name=''):
#
#     def wrapper(wrapped):
#         def callback(context, funcname, ob):
#             config = context.config.with_package(info.module)
#             config.registry.registerAdapter(
#                 wrapped, required=[iface_or_class, IRequest],
#                 provided=ISerializer, name=name
#             )
#
#         info = venusian.attach(wrapped, callback, category='pyramid')
#
#         return wrapped
#
#     return wrapper
#
#
# @serializes(IContent)
def content_serializer(context, request):
    from kotti.views.edit.content import ContentSchema
    return ContentSchema().serialize(context.__dict__)


#@serializes(IDocument)
def document_serializer(context, request):
    from kotti.views.edit.content import DocumentSchema
    return DocumentSchema().serialize(context.__dict__)


#@serializes(IFile)
def file_serializer(context, request):
    from kotti.views.edit.content import FileSchema
    # TODO: implement a Base64 file store
    return FileSchema(None).serialize(context.__dict__)


ACCEPT = 'application/vnd.api+json'

@view_defaults(name='json',
               accept=ACCEPT,
               renderer="jsonp")
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

        #return serialize(self.context, self.request)
        #return Response(to_json(serialize(self.context, self.request)))

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

            try:
                return basedefault(obj)
            except:
                import pdb; pdb.set_trace()

    return Encoder


def to_json(obj, default=None, **kw):
    return json.dumps(obj, cls=_encoder(default), **kw)


from pyramid.renderers import JSONP
jsonp = JSONP(param_name='callback', serializer=to_json)
jsonp.add_adapter(Document, document_serializer)

def includeme(config):

    config.add_renderer('jsonp', jsonp)
    config.scan(__name__)

