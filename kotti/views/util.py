import hashlib
import string
import urllib

from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.security import authenticated_userid
from pyramid.security import has_permission
from pyramid.url import resource_url
from deform import ValidationFailure

from kotti import get_settings
from kotti import DBSession
from kotti.events import objectevent_listeners
from kotti.resources import Node
from kotti.security import get_principals
from kotti.security import view_permitted
from kotti.views.slots import slot_events

class TemplateAPI(object):
    """This implements the 'api' object that's passed to all
    templates.

    Use dict-access as a shortcut to retrieve template macros from
    templates.  ``api['master_view.messages']`` will return the
    'messages' macro from the 'master_edit' template.
    """
    BARE_TMPL = 'kotti:templates/master-bare.pt'

    def __init__(self, context, request, bare=None, **kwargs):
        self.context, self.request = context, request

        if request.is_xhr and bare is None:
            bare = True
        self.bare = bare
        S = get_settings()
        bare_tmpl = self.BARE_TMPL

        self.macro_templates = dict(
            master_view=bare and bare_tmpl or S['kotti.templates.master_view'],
            master_edit=bare and bare_tmpl or S['kotti.templates.master_edit'],
            master_cp=bare and bare_tmpl or S['kotti.templates.master_cp'],
            snippets='kotti:templates/snippets.pt',
            )
        self.base_css = S['kotti.templates.base_css']
        self.view_css = S['kotti.templates.view_css']
        self.edit_css = S['kotti.templates.edit_css']

        self.__dict__.update(kwargs)

    def __getitem__(self, dottedname):
        try:
            template_name, macro_name = dottedname.split('.')
        except ValueError: # Chameleon will try dict access after attr access
            raise KeyError(dottedname)
        
        template = self.macro_templates[template_name]
        if isinstance(template, basestring):
            template = self.macro_templates[template_name] = get_renderer(
                template).implementation()
        return template.macros[macro_name]

    @reify
    def site_title(self):
        return get_settings().get('kotti.site_title', self.root.title)

    @reify
    def page_title(self):
        return u'%s - %s' % (self.context.title, self.site_title)

    def url(self, context=None, *elements):
        if context is None:
            context = self.context
        rhs = '/'.join(elements)
        return resource_url(context, self.request) + rhs

    @reify
    def root(self):
        return self.lineage[-1]

    @reify
    def lineage(self):
        return list(lineage(self.context))

    @reify
    def user(self):
        userid = authenticated_userid(self.request)
        return get_principals().get(userid)
    
    def has_permission(self, permission, context=None):
        if context is None:
            context = self.context
        return has_permission(permission, context, self.request)

    def list_children(self, context=None, permission='view'):
        if context is None:
            context = self.context
        children = []
        for child in context.values():
            if (not permission or
                has_permission(permission, child, self.request)):
                children.append(child)
        return children

    def list_children_go_up(self, context=None, permission='view'):
        if context is None:
            context = self.context
        parent = context
        children = self.list_children(context, permission)
        if not children and context.__parent__ is not None:
            parent = context.__parent__
            children = self.list_children(parent)
        return (parent, children)

    inside = staticmethod(inside)

    def avatar_url(self, user=None, size="20", default_image='identicon'):
        if user is None:
            user = self.user
        email = user.email
        if not email:
            email = user.name
        h = hashlib.md5(email).hexdigest()
        query = {'default': default_image, 'size': str(size)}
        url = 'https://secure.gravatar.com/avatar/%s?%s' % (
            h, urllib.urlencode(query))
        return url

    @reify
    def slots(self):
        value = {}
        for event_type in slot_events:
            event = event_type(self.context, self.request)
            this_slots = value[event.name] = []
            for snippet in objectevent_listeners(event):
                if snippet is not None:
                    if isinstance(snippet, list):
                        this_slots.extend(snippet)
                    else:
                        this_slots.append(snippet)
        return value

class TemplateAPIEdit(TemplateAPI):
    @reify
    def page_title(self):
        return u'%s - %s' % (
            self.request.view_name.replace('_', ' ').title(), self.site_title)

    @reify
    def first_heading(self):
        return u'<h1>Edit <em>%s</em></h1>' % self.context.title

    def _find_edit_view(self, item):
        view_name = self.request.view_name
        if not view_permitted(item, self.request, view_name):
            view_name = u'edit'
        if not view_permitted(item, self.request, view_name):
            view_name = u''
        return view_name

    def _make_links(self, items):
        links = []
        for item in items:
            view_name = self._find_edit_view(item)
            view_name = view_name and '@@' + view_name
            url = resource_url(item, self.request) + view_name
            links.append(dict(
                url=url,
                name=item.title,
                is_edit_link=view_name != '',
                node=item,
                is_context=item == self.context,
                ))
        return links

    @reify
    def breadcrumbs(self):
        return self._make_links(tuple(reversed(self.lineage)))

    @reify
    def context_links(self):
        siblings = []
        if self.context.__parent__ is not None:
            siblings = self._make_links(
                self.list_children(self.context.__parent__))
            siblings = filter(lambda l: not l['is_context'], siblings)
        children = self._make_links(self.list_children(self.context))
        return siblings, children

    @reify
    def edit_links(self):
        return [l for l in self.context.type_info.edit_links
                if l.permitted(self.context, self.request)]

    def more_links(self, name):
        return [l for l in getattr(self, name)
                if l.permitted(self.context, self.request)]

    def get_paste_item(self):
        info = self.request.session.get('kotti.paste')
        if info:
            id, action = info
            item = DBSession().query(Node).get(id)
            if not item.type_info.addable(self.context, self.request):
                return
            if action == 'cut' and self.inside(self.context, item):
                return
            if self.context == item:
                return
            return item

def addable_types(context, request):
    all_types = get_settings()['kotti.available_types']

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
    okay = string.letters + string.digits + '-'
    name = u'-'.join(title.lower().split())
    name = u''.join(ch for ch in name if ch in okay)
    return name

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

def ensure_view_selector(func):
    def wrapper(context, request):
        path_els = request.path_info.split(u'/')
        if not path_els[-1].startswith('@@'):
            path_els[-1] = '@@' + path_els[-1]
            request.path_info = u'/'.join(path_els)
            return HTTPFound(location=request.url)
        return func(context, request)
    wrapper.__doc__ = func.__doc__
    return wrapper

class FormController(object):
    add = None
    post_key = 'save'
    edit_success_msg = u"Your changes have been saved."
    add_success_msg = u"Successfully added item."
    error_msg = (u"There was a problem with your submission.\n"
                 u"Errors have been highlighted.")
    success_path = '@@edit'

    def __init__(self, form, **kwargs):
        self.form = form
        for key, value in kwargs.items():
            if key in self.__class__.__dict__:
                setattr(self, key, value)
            else: # pragma: no coverage
                raise TypeError("Unknown argument %r" % key)

    def __call__(self, context, request):
        if self.post_key in request.POST:
            controls = request.POST.items()
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                request.session.flash(self.error_msg, 'error')
                return e.render()
            else:
                if self.add is None: # edit
                    return self.edit_item(context, request, appstruct)
                else: # add
                    return self.add_item(context, request, appstruct)
        else: # no post means less action
            if self.add is None:
                appstruct = self.appstruct(context)
                return self.form.render(appstruct)
            else:
                return self.form.render()

    def appstruct(self, item):
        return item.__dict__.copy()

    def edit_item(self, context, request, appstruct):
        for key, value in appstruct.items():
            setattr(context, key, value)
        request.session.flash(self.edit_success_msg, 'success')
        try:
            location = resource_url(context, request) + self.success_path
        except AttributeError:
            location = request.url
        return HTTPFound(location=location)
        
    def add_item(self, context, request, appstruct):
        name = title_to_name(appstruct['title'])
        while name in context.keys():
            name = disambiguate_name(name)
        item = context[name] = self.add(**appstruct)
        request.session.flash(self.add_success_msg, 'success')
        location = resource_url(item, request) + self.success_path
        return HTTPFound(location=location)

def is_root(context, request):
    return context is TemplateAPI(context, request).root
