import string

from pyramid.decorator import reify
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.security import has_permission
from pyramid.security import view_execution_permitted
from pyramid.url import resource_url

from kotti import configuration
from kotti.resources import DBSession
from kotti.resources import Node

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

    @reify
    def page_title(self):
        return u'%s - %s' % (self.context.title, self.root.title)

    def url(self, context=None, *args, **kwargs):
        if context is None:
            context = self.context
        return resource_url(context, self.request, *args, **kwargs)

    @reify
    def root(self):
        return self.lineage[-1]

    @reify
    def lineage(self):
        return list(lineage(self.context))

    def has_permission(self, permission, context=None):
        if context is None:
            context = self.context
        return has_permission(permission, context, self.request)

    def list_children(self, context=None, go_up=False, permission='view'):
        if context is None:
            context = self.context
        children = []
        for child in context.values():
            if (not permission or
                has_permission(permission, child, self.request)):
                children.append(child)
        if go_up and not children and context.__parent__ is not None:
            return self.list_children(context.__parent__)
        return children

    inside = staticmethod(inside)

class TemplateAPIEdit(TemplateAPI):
    @reify
    def page_title(self):
        return u'%s - %s' % (
            self.request.view_name.replace('_', ' ').title(), self.root.title)

    @reify
    def first_heading(self):
        return u'<h1>Edit <em>%s</em></h1>' % self.context.title

    @reify
    def breadcrumbs(self):
        links = []
        for item in tuple(reversed(self.lineage)):
            view_name = self.request.view_name
            if not view_execution_permitted(item, self.request, view_name):
                view_name = u'edit' # XXX testme
            if not view_execution_permitted(item, self.request, view_name):
                view_name = u'' # XXX testme
            url = resource_url(item, self.request, view_name)
            links.append(dict(
                url=url,
                name=item.title,
                is_edit_link=view_name != '',
                node=item,
                ))
        return links

    def edit_links(self):
        links = []
        for name in self.context.type_info.edit_views:
            if not view_execution_permitted(self.context, self.request, name):
                continue # XXX testme
            url = resource_url(self.context, self.request, name)
            links.append(dict(
                url=url,
                name=name,
                selected=self.request.url.startswith(url),
                ))
        return links

    def get_paste_item(self):
        info = self.request.session.get('kotti.paste')
        if info:
            id, action = info
            item = DBSession().query(Node).get(id)
            if item.type_info.addable(self.context, self.request):
                return item

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

def title_to_name(title):
    name = u''.join(
        ch if ch in string.letters + string.digits else u'-' for ch in title)
    return name.lower()

def disambiguate_name(name):
    parts = name.split(u'-')
    if len(parts) > 1:
        try:
            index = int(parts[-1])
        except ValueError:
            parts.append(u'1')
        else:
            parts[-1] = unicode(index+1)
    else:
        parts.append(u'1')
    return u'-'.join(parts)
