from pyramid.decorator import reify
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.security import has_permission
from pyramid.url import resource_url

from kotti import configuration

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

    def list_children(self, context=None, go_up=False, secure=True):
        if context is None:
            context = self.context
        children = []
        for child in context.values():
            if not secure or has_permission('view', child, self.request):
                children.append(child)
        if go_up and not children and context.__parent__ is not None:
            return self.list_children(context.__parent__)
        return children

    inside = staticmethod(inside)


def addable_types(context, request):
    all_types = configuration['kotti.available_types']

    # 'possible_parents' is a list of dicts with 'node' and 'factories',
    # where 'node' is the context to add to and 'factories' is the list
    # of factories that can be applied in the contetx:
    possible_parents = []
    parent = context
    while parent is not None:
        possible_parents.append({'node': parent, 'factories': []})
        parent = parent.__parent__

    for entry in possible_parents:
        parent = entry['node']
        for factory in all_types:
            if factory.type_info.addable(parent, request):
                entry['factories'].append(factory)

    possible_parents = filter(lambda e: e['factories'], possible_parents)

    _possible_types = {}
    for entry in possible_parents:
        for factory in entry['factories']:
            name = factory.type_info.name
            pt = _possible_types.get(
                name, {'factory': factory, 'nodes': []})
            pt['nodes'].append(entry['node'])
            _possible_types[name] = pt

    possible_types = []
    for t in all_types:
        entry = _possible_types.get(t.type_info.name)
        if entry:
            possible_types.append(entry)

    return possible_parents, possible_types
