from pkg_resources import resource_filename
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission
from pyramid.security import view_execution_permitted
from pyramid.url import resource_url
from pyramid.view import is_response
import colander
from deform import Form
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti import configuration
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.security import get_principals
from kotti.security import map_principals_with_local_roles
from kotti.security import set_groups
from kotti.security import list_groups_raw
from kotti.security import list_groups_ext
from kotti.security import ROLES
from kotti.security import SHARING_ROLES
from kotti.views.util import TemplateAPIEdit
from kotti.views.util import addable_types
from kotti.views.util import title_to_name
from kotti.views.util import disambiguate_name
from kotti.views.util import FormController

deform_templates = resource_filename('deform', 'templates')
kotti_templates = resource_filename('kotti', 'templates/edit/widgets')
search_path = (kotti_templates, deform_templates)
Form.set_zpt_renderer(search_path)

class NodeSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(
        colander.String(),
        widget=TextAreaWidget(cols=40, rows=5),
        missing=u"",
        )

class DocumentSchema(NodeSchema):
    body = colander.SchemaNode(
        colander.String(),
        widget=RichTextWidget(theme='advanced'),
        missing=u"",
        )

def add_node(context, request):
    """This view's responsibility is to present the user with a form
    where they can choose between locations to add to, and types of
    nodes to add, and redirect to the actual add form based on this
    information.
    """
    all_types = configuration['kotti.available_types']
    
    if request.POST:
        what, where = request.POST['what'], request.POST['where']
        session = DBSession()
        what = [t for t in all_types if t.type_info.name == what][0]
        where = session.query(Node).get(int(where))
        location = resource_url(where, request) + '@@' + what.type_info.add_view
        return HTTPFound(location=location)

    possible_parents, possible_types = addable_types(context, request)
    if len(possible_parents) == 1 and len(possible_parents[0]['factories']) == 1:
        # Redirect to the add form straight away if there's only one
        # choice of parents and addable types:
        parent = possible_parents[0]
        add_view = parent['factories'][0].type_info.add_view
        location = resource_url(parent['node'], request) + '@@' + add_view
        return HTTPFound(location=location)

    # Swap first and second possible parents if there's no content in
    # 'possible_parents[0]' yet.  This makes the parent then the
    # default choice in the form:
    api = TemplateAPIEdit(context, request)
    if not api.list_children() and len(possible_parents) > 1:
        possible_parents[0], possible_parents[1] = (
            possible_parents[1], possible_parents[0])

    return {
        'api': api,
        'possible_parents': possible_parents,
        'possible_types': possible_types,
        }

def move_node(context, request):
    """This view allows copying, cutting, pasting, deleting of
    'context' and reordering of children of 'context'.
    """
    P = request.POST
    session = DBSession()
    
    if 'copy' in P:
        request.session['kotti.paste'] = (context.id, 'copy')
        request.session.flash(u'%s copied.' % context.title, 'success')
        return HTTPFound(location=request.url)

    if 'cut' in P:
        request.session['kotti.paste'] = (context.id, 'cut')
        request.session.flash(u'%s cut.' % context.title, 'success')
        return HTTPFound(location=request.url)

    if 'paste' in P:
        id, action = request.session['kotti.paste']
        item = session.query(Node).get(id)
        if action == 'cut':
            if not has_permission('edit', item, request):
                raise Forbidden() # XXX testme
            item.__parent__.children.remove(item)
            context.children.append(item)
            del request.session['kotti.paste']
        elif action == 'copy':
            copy = item.copy()
            name = copy.name
            if not name: # for root
                name = title_to_name(copy.title)
            while name in context.keys():
                name = disambiguate_name(name)
            copy.name = name
            context.children.append(copy)
        request.session.flash(u'%s pasted.' % item.title, 'success')
        return HTTPFound(location=request.url)

    if 'order-up' in P or 'order-down' in P:
        up, down = P.get('order-up'), P.get('order-down')
        id = int(down or up)
        if up is not None: # pragma: no cover
            mod = -1
        else:
            mod = +1

        child = session.query(Node).get(id)
        index = context.children.index(child)
        context.children.pop(index)
        context.children.insert(index+mod, child)
        request.session.flash(u'%s reordered.' % child.title, 'success')

    if 'delete' in P and 'delete-confirm' in P:
        parent = context.__parent__
        redirect_elements = []
        if view_execution_permitted(parent, request, 'edit'):
            redirect_elements.append('edit')
        location = resource_url(parent, request, *redirect_elements)
        request.session.flash(u'%s deleted.' % context.title, 'success')
        parent.children.remove(context)
        return HTTPFound(location=location)

    if 'rename' in P:
        name = P['name']
        title = P['title']
        context.name = name
        context.title = title
        request.session.flash(u'Item renamed', 'success')
        location = resource_url(context, request, 'move')        
        return HTTPFound(location=location)

    return {
        'api': TemplateAPIEdit(context, request),
        }

def share_node(context, request):
    flash = request.session.flash
    principals = get_principals()
    available_roles = [ROLES[role_name] for role_name in SHARING_ROLES]

    if 'apply' in request.params:
        changed = False
        p_to_r = {}
        for name in request.params:
            if name.startswith('orig-role::'):
                # orig-role::* is hidden checkboxes that allow us to
                # see what checkboxes were in the form originally
                token, principal_name, role_name = name.split('::')
                if role_name not in SHARING_ROLES:
                    raise Forbidden()
                new_value = bool(request.params.get(
                    'role::%s::%s' % (principal_name, role_name)))
                if principal_name not in p_to_r:
                    p_to_r[principal_name] = set()
                if new_value:
                    p_to_r[principal_name].add(role_name)

        for principal_name, new_role_names in p_to_r.items():
            # We have to be careful with roles that aren't mutable here:
            orig_role_names = set(list_groups_raw(principal_name, context))
            orig_sharing_role_names = set(
                r for r in orig_role_names if r in SHARING_ROLES)
            if new_role_names != orig_sharing_role_names:
                changed = True
                final_role_names = orig_role_names - set(SHARING_ROLES)
                final_role_names |= new_role_names
                set_groups(principal_name, context, final_role_names)

        if changed:
            flash(u'Your changes have been applied.', 'success')
        else:
            flash(u'No changes made.', 'info')
        return HTTPFound(location=request.url)

    existing = map_principals_with_local_roles(context)
    def with_roles(entry):
        all_groups = entry[1][0]
        return [g for g in all_groups if g.startswith('role:')]
    existing = filter(with_roles, existing)
    seen = set([entry[0].name for entry in existing])

    entries = []

    if 'search' in request.params:
        query = '*%s*' % request.params['query']
        found = False
        for p in principals.search(name=query, title=query, email=query):
            found = True
            if p.name not in seen:
                entries.append((p, list_groups_ext(p.name, context)))
        if not found:
            flash(u'No users or groups found.', 'info')

    entries = existing + entries

    return {
        'api': TemplateAPIEdit(context, request),
        'entries': entries,
        'available_roles': available_roles,
        'principals_to_roles': map_principals_with_local_roles(context),
        }

def edit_document(context, request):
    form = Form(DocumentSchema(), buttons=('save', 'cancel'))
    rendered = FormController(form)(context, request)
    if is_response(rendered):
        return rendered
    return {
        'api': TemplateAPIEdit(context, request),
        'form': rendered,
        }

def add_document(context, request):
    api = TemplateAPIEdit(
        context, request,
        first_heading=u'<h1>Add document to <em>%s</em></h1>' % context.title)
    form = Form(DocumentSchema(), buttons=('save', 'cancel'))
    rendered = FormController(form, add=Document)(context, request)
    if is_response(rendered):
        return rendered
    return {
        'api': api,
        'form': rendered,
        }

def includeme(config):
    config.add_view(
        edit_document,
        context=Document,
        name='edit',
        permission='edit',
        renderer='../templates/edit/node.pt',
        )

    config.add_view(
        add_document,
        name=Document.type_info.add_view,
        permission='add',
        renderer='../templates/edit/node.pt',
        )
