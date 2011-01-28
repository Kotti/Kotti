from kotti.resources import Document
from kotti.views import TemplateAPI

def node_view(context, request):
    return {
        'context': context,
        'api': TemplateAPI(context, request),
        }

def includeme(config):
    config.add_view(
        node_view,
        context=Document,
        name='view',
        permission='view',
        renderer='../templates/document_view.pt',
        )
