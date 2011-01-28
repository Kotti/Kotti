from pyramid.decorator import reify
from pyramid.exceptions import NotFound
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.security import has_permission
from pyramid.url import resource_url
from pyramid.view import render_view_to_response

from kotti import configuration

def node_default_view(context, request):
    """This view is always registered as the default view for any Node.

    Its job is to delegate to a view of which the name may be defined
    per instance.  If a instance level view is not defined for
    'context' (in 'context.defaultview'), we will fall back to a view
    with the name 'view'.
    """
    view_name = context.default_view or u'view'
    response = render_view_to_response(context, request, name=view_name)
    if response is None:
        raise NotFound()
    return response

class TemplateAPI(object):
    """This implements the 'api' object that's passed to all
    templates.

    Use dict-access as a shortcut to retrieve template macros from
    templates.  ``api['snippets.head']`` will return the 'head' macro
    from the 'snippets' template.
    """
    macro_templates = dict(
        snippets=configuration['kotti.templates.snippets'],
        master_view=configuration['kotti.templates.master_view'],
        master_edit=configuration['kotti.templates.master_edit'],
        )
    
    def __init__(self, context, request, **kwargs):
        self.context, self.request = context, request
        self.__dict__.update(kwargs)

    def __getitem__(self, dottedname):
        template_name, macro_name = dottedname.split('.')
        template = self.macro_templates[template_name]
        if isinstance(template, basestring):
            template = self.macro_templates[template_name] = get_renderer(
                template).implementation()
        return template.macros[macro_name]

    def url(self, context=None, *args, **kwargs):
        if context is None:
            context = self.context
        return resource_url(context, self.request, *args, **kwargs)

    @reify
    def root(self):
        return list(lineage(self.context))[-1]

    def has_permission(self, permission, context=None):
        if context is None:
            context = self.context
        return has_permission(permission, context, self.request)

    def list_children(self, context=None, go_up=False):
        if context is None:
            context = self.context
        children = []
        for child in context.values():
            if has_permission('view', child, self.request):
                children.append(child)
        if go_up and not children and context.__parent__ is not None:
            return self.list_children(context.__parent__)
        return children

    inside = staticmethod(inside)
