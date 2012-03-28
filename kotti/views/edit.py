from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.location import inside
from pyramid.security import has_permission
from pyramid.url import resource_url
import colander
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti import get_settings
from kotti import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.resources import get_root
from kotti.util import _
from kotti.util import ViewLink
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
    """Drop down menu for Add button in editor bar.
    """
    all_types = get_settings()['kotti.available_types']
    factories = []
    for factory in all_types:
        if factory.type_info.addable(context, request):
            factories.append(factory)
    return {'factories': factories}


def get_paste_item(context, request):
    info = request.session.get('kotti.paste')
    if info:
        id, action = info
        item = DBSession().query(Node).get(id)
        if not item.type_info.addable(context, request):
            return
        if action == 'cut' and inside(context, item):
            return
        if context == item:
            return
        return item


def actions(context, request):
    """Drop down menu for Actions button in editor bar.
    """
    root = get_root()
    actions = [ViewLink('copy', title=_(u'Copy'))]
    is_root = context is root
    if not is_root:
        actions.append(ViewLink('cut', title=_(u'Cut')))
    if get_paste_item(context, request) is not None:
        actions.append(ViewLink('paste', title=_(u'Paste')))
    if not is_root:
        actions.append(ViewLink('rename', title=_(u'Rename')))
        actions.append(ViewLink('delete', title=_(u'Delete')))
    if len(context.children) >= 1:
        actions.append(ViewLink('order', title=_(u'Order')))
    return {'actions': [action for action in actions
                        if action.permitted(context, request)]}


def copy_node(context, request):
    request.session['kotti.paste'] = (context.id, 'copy')
    request.session.flash(_(u'${title} copied.',
                            mapping=dict(title=context.title)), 'success')
    if not request.is_xhr:
        location = resource_url(context, request)
        return HTTPFound(location=location)


def cut_node(context, request):
    request.session['kotti.paste'] = (context.id, 'cut')
    request.session.flash(_(u'${title} cut.',
                            mapping=dict(title=context.title)), 'success')
    if not request.is_xhr:
        location = resource_url(context, request)
        return HTTPFound(location=location)


def paste_node(context, request):
    session = DBSession()
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
        if not name:  # for root
            name = title_to_name(copy.title)
        while name in context.keys():
            name = disambiguate_name(name)
        copy.name = name
        context.children.append(copy)
    request.session.flash(_(u'${title} pasted.',
                            mapping=dict(title=item.title)), 'success')
    if not request.is_xhr:
        location = resource_url(context, request)
        return HTTPFound(location=location)


def order_node(context, request):
    P = request.POST

    if 'order-up' in P or 'order-down' in P:
        up, down = P.get('order-up'), P.get('order-down')
        child = DBSession.query(Node).get(int(down or up))
        if up is not None:
            mod = -1
        else:  # pragma: no cover
            mod = 1
        index = context.children.index(child)
        context.children.pop(index)
        context.children.insert(index + mod, child)
        request.session.flash(_(u'${title} moved.',
                                mapping=dict(title=child.title)), 'success')
        if not request.is_xhr:
            return HTTPFound(location=request.url)

    elif 'toggle-visibility' in P:
        child = DBSession.query(Node).get(int(P['toggle-visibility']))
        child.in_navigation ^= True
        mapping = dict(title=child.title)
        if child.in_navigation:
            msg = _(u'${title} is now visible in the navigation.',
                    mapping=mapping)
        else:
            msg = _(u'${title} is no longer visible in the navigation.',
                    mapping=mapping)
        request.session.flash(msg, 'success')
        if not request.is_xhr:
            return HTTPFound(location=request.url)

    return {}


def delete_node(context, request):
    if 'delete-confirm' in request.POST:
        parent = context.__parent__
        request.session.flash(_(u'${title} deleted.',
                                mapping=dict(title=context.title)), 'success')
        del parent[context.name]
        location = resource_url(parent, request)
        return HTTPFound(location=location)
    return {}


def rename_node(context, request):
    if 'rename' in request.POST:
        name = request.POST['name']
        title = request.POST['title']
        if not name or not title:
            request.session.flash(_(u'Name and title are required.'), 'error')
        else:
            context.name = name.replace('/','')
            context.title = title
            request.session.flash(_(u'Item renamed'),'success')
            location = resource_url(context, request)
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

def make_generic_add(schema, add, title=None, **kwargs):
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
        make_generic_add(DocumentSchema(), Document),
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

    config.add_view(
        actions,
        name='actions-dropdown',
        permission='view',
        renderer='kotti:templates/actions-dropdown.pt',
        )


def nodes_includeme(config):
    config.add_view(
        copy_node,
        name='copy',
        permission='edit',
        )

    config.add_view(
        cut_node,
        name='cut',
        permission='edit',
        )

    config.add_view(
        paste_node,
        name='paste',
        permission='edit',
        )

    config.add_view(
        order_node,
        name='order',
        permission='edit',
        renderer='kotti:templates/edit/order.pt',
        )

    config.add_view(
        delete_node,
        name='delete',
        permission='edit',
        renderer='kotti:templates/edit/delete.pt',
        )

    config.add_view(
        rename_node,
        name='rename',
        permission='edit',
        renderer='kotti:templates/edit/rename.pt',
        )
