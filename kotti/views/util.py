from collections import defaultdict
from datetime import datetime
import hashlib
import urllib

from babel.dates import format_date
from babel.dates import format_datetime
from babel.dates import format_time
import colander
import deform
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_locale_name
from pyramid.location import inside
from pyramid.location import lineage
from pyramid.renderers import get_renderer
from pyramid.renderers import render
from pyramid.url import resource_url
from pyramid.view import render_view_to_response
from pyramid_deform import FormView
from pyramid_deform import CSRFSchema

from kotti import get_settings
from kotti import DBSession
from kotti.util import title_to_name
from kotti.events import objectevent_listeners
from kotti.resources import Node
from kotti.resources import Content
from kotti.security import get_user
from kotti.security import has_permission
from kotti.security import view_permitted
from kotti.views.slots import slot_events

def template_api(context, request, **kwargs):
    return get_settings()['kotti.templates.api'][0](
        context, request, **kwargs)

def render_view(context, request, name='', secure=True):
    response = render_view_to_response(context, request, name, secure)
    return response.ubody

def add_renderer_globals(event):
    if event['renderer_name'] != 'json':
        api = getattr(event['request'], 'template_api', None)
        if api is None:
            api = template_api(event['context'], event['request'])
        event['api'] = api

def is_root(context, request):
    return context is TemplateAPI(context, request).root

class TemplateStructure(object):
    def __init__(self, html):
        self.html = html

    def __html__(self):
        return self.html
    __unicode__ = __html__

    def __getattr__(self, key):
        return getattr(self.html, key)

class Slots(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def __getattr__(self, name):
        for event_type in slot_events:
            if event_type.name == name:
                break
        else:
            raise AttributeError(name)
        value = []
        event = event_type(self.context, self.request)
        for snippet in objectevent_listeners(event):
            if snippet is not None:
                if isinstance(snippet, list):
                    value.extend(snippet)
                else:
                    value.append(snippet)
        setattr(self, name, value)
        return value

class TemplateAPI(object):
    """This implements the 'api' object that's passed to all
    templates.

    Use dict-access as a shortcut to retrieve template macros from
    templates.
    """
    # Instead of overriding these, consider using the
    # 'kotti.overrides' variable.
    BARE_MASTER = 'kotti:templates/master-bare.pt'
    VIEW_MASTER = 'kotti:templates/view/master.pt'
    EDIT_MASTER = 'kotti:templates/edit/master.pt'
    SITE_SETUP_MASTER = 'kotti:templates/site-setup/master.pt'

    body_css_class = ''

    def __init__(self, context, request, bare=None, **kwargs):
        self.context, self.request = context, request

        if getattr(request, 'template_api', None) is None:
            request.template_api = self

        self.S = get_settings()
        if request.is_xhr and bare is None:
            bare = True  # use bare template that renders just the content area
        self.bare = bare
        self.slots = Slots(context, request)
        self.__dict__.update(kwargs)

    def macro(self, asset_spec, macro_name='main'):
        if self.bare and asset_spec in (
            self.VIEW_MASTER, self.EDIT_MASTER, self.SITE_SETUP_MASTER):
            asset_spec = self.BARE_MASTER
        return get_renderer(asset_spec).implementation().macros[macro_name]

    @reify
    def site_title(self):
        value = get_settings().get('kotti.site_title')
        if not value:
            value = self.root.title
        return value

    @reify
    def page_title(self):
        view_title = self.request.view_name.replace('_', ' ').title()
        if view_title:
            view_title += u' '
        view_title += self.context.title
        return u'%s - %s' % (view_title, self.site_title)

    @reify
    def first_heading(self):
        return u'<h1>%s</h1>' % self.page_title

    def url(self, context=None, *elements, **kwargs):
        if context is None:
            context = self.context
        return self.request.resource_url(context, *elements, **kwargs)

    @reify
    def root(self):
        return self.lineage[-1]

    @reify
    def lineage(self):
        return list(lineage(self.context))

    @reify
    def breadcrumbs(self):
        return reversed(self.lineage)

    @reify
    def user(self):
        return get_user(self.request)
    
    def has_permission(self, permission, context=None):
        if context is None:
            context = self.context
        return has_permission(permission, context, self.request)

    def render_view(self, name='', context=None, request=None, secure=True):
        if context is None:
            context = self.context
        if request is None:
            request = self.request
        return TemplateStructure(render_view(context, request, name, secure))

    def render_template(self, renderer, **kwargs):
        return TemplateStructure(render(renderer, kwargs, self.request))

    def list_children(self, context=None, permission='view'):
        if context is None:
            context = self.context
        children = []
        if hasattr(context, 'values'):
            for child in context.values():
                if (not permission or
                    has_permission(permission, child, self.request)):
                    children.append(child)
        return children

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
    def locale_name(self):
        return get_locale_name(self.request)

    def format_date(self, d, format=None):
        if format is None:
            format = self.S['kotti.date_format']
        return format_date(d, format=format, locale=self.locale_name)

    def format_datetime(self, dt, format=None):
        if format is None:
            format = self.S['kotti.datetime_format']
        if not isinstance(dt, datetime):
            dt = datetime.fromtimestamp(dt)
        return format_datetime(dt, format=format, locale=self.locale_name)

    def format_time(self, t, format=None):
        if format is None:
            format = self.S['kotti.time_format']
        return format_time(t, format=format, locale=self.locale_name)

    def get_type(self, name):
        for class_ in get_settings()['kotti.available_types']:
            if class_.type_info.name == name:
                return class_

    def find_edit_view(self, item):
        view_name = self.request.view_name
        if not view_permitted(item, self.request, view_name):
            view_name = u'edit'
        if not view_permitted(item, self.request, view_name):
            view_name = u''
        return view_name

    @reify
    def edit_links(self):
        if not hasattr(self.context, 'type_info'):
            return []
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

class NavigationNodeWrapper(object):
    def __init__(self, node, request, item_mapping, item_to_children):
        self._node = node
        self._request = request
        self._item_mapping = item_mapping
        self._item_to_children = item_to_children

    @property
    def __parent__(self):
        if self.parent_id:
            return self._item_mapping[self.parent_id]

    @property
    def children(self):
        return [NavigationNodeWrapper(
            child, self._request, self._item_mapping, self._item_to_children)
                for child in self._item_to_children[self.id]
                if has_permission('view', child, self._request)]

    def __getattr__(self, name):
        return getattr(self._node, name)

def nodes_tree(request):
    item_mapping = {}
    item_to_children = defaultdict(lambda: [])
    for node in DBSession.query(Content).with_polymorphic(Content):
        item_mapping[node.id] = node
        if has_permission('view', node, request):
            item_to_children[node.parent_id].append(node)

    for children in item_to_children.values():
        children.sort(key=lambda ch:ch.position)

    return NavigationNodeWrapper(
        item_to_children[None][0],
        request,
        item_mapping,
        item_to_children,
        )

class Form(deform.Form):
    """A Form that allows 'appstruct' to be set on the instance.
    """
    def render(self, appstruct=None, readonly=False):
        if appstruct is None:
            appstruct = getattr(self, 'appstruct', colander.null)
        return super(Form, self).render(appstruct, readonly)

class BaseFormView(FormView):
    form_class = Form
    buttons = ('save', 'cancel')
    success_message = u"Your changes have been saved."
    success_url = None
    schema_factory = None
    use_csrf_token = True

    def __init__(self, context, request, **kwargs):
        self.context = context
        self.request = request
        self.__dict__.update(kwargs)

    def __call__(self):
        if self.schema_factory is not None:
            self.schema = self.schema_factory()
        if self.use_csrf_token and 'csrf_token' not in self.schema:
            self.schema.children.append(CSRFSchema()['csrf_token'])
        return super(BaseFormView, self).__call__()

class EditFormView(BaseFormView):
    def before(self, form):
        form.appstruct = self.context.__dict__.copy()

    def save_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        self.edit(**appstruct)
        self.request.session.flash(self.success_message, 'success')
        location = self.success_url or self.request.url
        return HTTPFound(location=location)

    def edit(self, **appstruct):
        for key, value in appstruct.items():
            setattr(self.context, key, value)

class AddFormView(BaseFormView):
    success_message = u"Successfully added item."

    def save_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        name = self.find_name(appstruct)
        new_item = self.context[name] = self.add(**appstruct)
        self.request.session.flash(self.success_message, 'success')
        location = self.success_url or resource_url(
            new_item, self.request, '@@edit')
        return HTTPFound(location=location)

    def find_name(self, appstruct):
        name = appstruct.get('name')
        if name is None:
            name = title_to_name(appstruct['title'])
            while name in self.context.keys():
                name = disambiguate_name(name)
        return name
