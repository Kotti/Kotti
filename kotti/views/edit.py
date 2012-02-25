from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission
from pyramid.url import resource_url
import colander
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti import get_settings
from kotti import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.security import view_permitted
from kotti.util import _
from kotti.views.util import EditFormView
from kotti.views.util import AddFormView
from kotti.views.util import disambiguate_name
from kotti.views.util import ensure_view_selector
from kotti.views.util import nodes_tree
from kotti.util import title_to_name


class ContentSchema(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Title'))
    description = colander.SchemaNode(
        colander.String(),
        title=_('Description'),
        widget=TextAreaWidget(cols=40, rows=5),
        missing=u"",
        )


class DocumentSchema(ContentSchema):
    body = colander.SchemaNode(
        colander.String(),
        title=_(u'Body'),
        widget=RichTextWidget(theme='advanced', width=790, height=500),
        missing=u"",
        )

def content_type_factories(context, request):
    """ Drop down menu for Add button.
    """
    all_types = get_settings()['kotti.available_types']
    factories = []
    for factory in all_types:
        if factory.type_info.addable(context, request):
            factories.append(factory)
    return {'factories': factories}


def move_node(context, request):
    """This view allows copying, cutting, pasting, deleting of
    'context' and reordering of children of 'context'.
    """
    P = request.POST
    session = DBSession()

    if 'copy' in P:
        request.session['kotti.paste'] = (context.id, 'copy')
        request.session.flash(_(u'${title} copied.',
                                mapping=dict(title=context.title)), 'success')
        if not request.is_xhr:
            return HTTPFound(location=request.url)

    if 'cut' in P:
        request.session['kotti.paste'] = (context.id, 'cut')
        request.session.flash(_(u'${title} cut.',
                                mapping=dict(title=context.title)), 'success')
        if not request.is_xhr:
            return HTTPFound(location=request.url)

    if 'paste' in P:
        id, action = request.session['kotti.paste']
        item = session.query(Node).get(id)
        if action == 'cut':
            if not has_permission('edit', item, request):
                raise Forbidden()
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
        request.session.flash(_(u'${title} pasted.',
                                mapping=dict(title=item.title)), 'success')
        if not request.is_xhr:
            return HTTPFound(location=request.url)

    if 'order-up' in P or 'order-down' in P:
        up, down = P.get('order-up'), P.get('order-down')
        id = int(down or up)
        if up is not None:
            mod = -1
        else: # pragma: no cover
            mod = 1

        child = session.query(Node).get(id)
        index = context.children.index(child)
        context.children.pop(index)
        context.children.insert(index + mod, child)
        request.session.flash(_(u'${title} moved.',
                                mapping=dict(title=child.title)), 'success')
        if not request.is_xhr:
            return HTTPFound(location=request.url)

    if 'delete' in P and 'delete-confirm' in P:
        parent = context.__parent__
        request.session.flash(_(u'${title} deleted.',
                                mapping=dict(title=context.title)), 'success')
        parent.children.remove(context)
        location = resource_url(parent, request)
        if view_permitted(parent, request, 'edit'):
            location += '@@edit'
        return HTTPFound(location=location)

    if 'rename' in P:
        name = P['name']
        title = P['title']
        if not name or not title:
            request.session.flash(_(u'Name and title are required.'), 'error')
        else:
            context.name = name
            context.title = title
            request.session.flash(_(u'Item renamed'), 'success')
            location = resource_url(context, request) + '@@move'
            return HTTPFound(location=location)

    return {}

# XXX These and the make_generic_edit functions below can probably be
# simplified quite a bit.
def generic_edit(context, request, schema, **kwargs):
    return EditFormView(
        context,
        request,
        schema=schema,
        **kwargs
        )()

def generic_add(context, request, schema, add, title, **kwargs):
    return AddFormView(
        context,
        request,
        schema=schema,
        add=add,
        item_type=title,
        **kwargs
        )()

def make_generic_edit(schema, **kwargs):
    @ensure_view_selector
    def view(context, request):
        return generic_edit(context, request, schema, **kwargs)
    return view

def make_generic_add(schema, add, title, **kwargs):
    def view(context, request):
        return generic_add(context, request, schema, add, title, **kwargs)
    return view

def render_tree_navigation(context, request):
    tree = nodes_tree(request)
    return {
        'tree': {
            'children': [tree],
            },
        }

def includeme(config):
    nodes_includeme(config)

    config.add_view(
        make_generic_edit(DocumentSchema()),
        context=Document,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        make_generic_add(DocumentSchema(), Document, u'document'),
        name=Document.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        render_tree_navigation,
        name='render_tree_navigation',
        permission='view',
        renderer='kotti:templates/edit/nav-tree.pt',
        )

    config.add_view(
        render_tree_navigation,
        name='navigate',
        permission='view',
        renderer='kotti:templates/edit/nav-tree-view.pt',
        )

    config.add_view(
        content_type_factories,
        name='add-dropdown',
        permission='add',
        renderer='kotti:templates/add-dropdown.pt',
        )


def nodes_includeme(config):
    config.add_view(
        'kotti.views.edit.move_node',
        name='move',
        permission='edit',
        renderer='kotti:templates/edit/move.pt',
        )
