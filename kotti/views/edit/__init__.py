from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.location import inside
from pyramid.security import has_permission
from pyramid.url import resource_url
from zope.deprecation.deprecation import deprecate

from kotti import DBSession
from kotti import get_settings
from kotti.resources import IContent
from kotti.resources import Node
from kotti.resources import get_root
from kotti.util import _
from kotti.util import title_to_name
from kotti.util import ActionButton
from kotti.util import ViewLink
from kotti.views.form import AddFormView
from kotti.views.form import EditFormView
from kotti.views.util import ensure_view_selector
from kotti.views.util import nodes_tree
from kotti.workflow import get_workflow


def content_type_factories(context, request):
    """Drop down menu for Add button in editor bar.
    """
    all_types = get_settings()['kotti.available_types']
    factories = []
    for factory in all_types:
        if factory.type_info.addable(context, request):
            factories.append(factory)
    return {'factories': factories}


def get_paste_items(context, request):
    items = []
    info = request.session.get('kotti.paste')
    if info:
        ids, action = info
        for id in ids:
            item = DBSession.query(Node).get(id)
            if item is None or not item.type_info.addable(context, request):
                continue
            if action == 'cut' and inside(context, item):
                continue
            if context == item:
                continue
            items.append(item)
    return items


def actions(context, request):
    """Drop down menu for Actions button in editor bar.
    """
    root = get_root()
    actions = [ViewLink('copy', title=_(u'Copy'))]
    is_root = context is root
    if not is_root:
        actions.append(ViewLink('cut', title=_(u'Cut')))
    if get_paste_items(context, request):
        actions.append(ViewLink('paste', title=_(u'Paste')))
    if not is_root:
        actions.append(ViewLink('rename', title=_(u'Rename')))
        actions.append(ViewLink('delete', title=_(u'Delete')))
    if len(context.children) >= 1:
        actions.append(ViewLink('order', title=_(u'Order')))
    return {'actions': [action for action in actions
                        if action.permitted(context, request)]}


def contents_buttons(context, request):
    """Buttons for the actions of the contents view.
    """
    buttons = []
    if get_paste_items(context, request):
        buttons.append(ActionButton('paste', title=_(u'Paste'),
                                    no_children=True))
    if context.children:
        buttons.append(ActionButton('copy', title=_(u'Copy')))
        buttons.append(ActionButton('cut', title=_(u'Cut')))
        buttons.append(ActionButton('rename_nodes', title=_(u'Rename'),
                                    css_class=u'btn btn-warning'))
        buttons.append(ActionButton('delete_nodes', title=_(u'Delete'),
                                    css_class=u'btn btn-danger'))
        if get_workflow(context) is not None:
            buttons.append(ActionButton('change_state',
                                        title=_(u'Change State')))
    return [button for button in buttons
        if button.permitted(context, request)]


def contents(context, request):
    """Choose the current action for our contents view. Gets called when you
       click on the "Contents" Tab, or when you do an action in the "Contents" view.
    """
    buttons = contents_buttons(context, request)
    for button in buttons:
        if button.path in request.POST:
            children = request.POST.getall('children')
            if not children and button.path != u'paste':
                request.session.flash(_(u'You have to choose items to perform an action.'), 'info')
                location = resource_url(context, request) + '@@contents'
                return HTTPFound(location=location)
            request.session['kotti.selected-children'] = children
            location = button.url(context, request)
            return HTTPFound(location, request=request)

    return {'children': context.children_with_permission(request),
            'buttons': buttons,
            }


def _eval_titles(info):
    result = []
    for d in info:
        d = d.copy()
        d['title'] = eval(d['title']) if 'title' in d else d['name']
        result.append(d)
    return result


def _state_info(context, request):
    wf = get_workflow(context)
    state_info = []
    if wf is not None:
        state_info = _eval_titles(wf.state_info(context, request))
        return state_info


def _states(context, request):
    state_info = _state_info(context, request)
    return dict([(i['name'], i) for i in state_info])


def workflow(context, request):
    """Drop down menu for workflow actions.
    """
    wf = get_workflow(context)
    if wf is not None:
        state_info = _state_info(context, request)
        curr_state = [i for i in state_info if i['current']][0]
        trans_info = wf.get_transitions(context, request)
        return {
            'states': _states(context, request),
            'transitions': trans_info,
            'current_state': curr_state,
            }

    return {
        'current_state': None
        }


def workflow_change(context, request):
    """Handle workflow change requests from workflow dropdown
    """
    new_state = request.params['new_state']
    wf = get_workflow(context)
    wf.transition_to_state(context, request, new_state)
    request.session.flash(EditFormView.success_message, 'success')
    url = request.referrer or request.resource_url(context)
    return HTTPFound(location=url)


def _selected_children(context, request, add_context=True):
    ids = request.session.pop('kotti.selected-children')
    if ids is None and add_context:
        ids = [context.id]
    return ids


def copy_node(context, request):
    ids = _selected_children(context, request)
    request.session['kotti.paste'] = (ids, 'copy')
    for id in ids:
        item = DBSession.query(Node).get(id)
        request.session.flash(_(u'${title} copied.',
                                mapping=dict(title=item.title)), 'success')
    if not request.is_xhr:
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)


def cut_node(context, request):
    ids = _selected_children(context, request)
    request.session['kotti.paste'] = (ids, 'cut')
    for id in ids:
        item = DBSession.query(Node).get(id)
        request.session.flash(_(u'${title} cut.',
                                mapping=dict(title=item.title)), 'success')
    if not request.is_xhr:
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)


def paste_node(context, request):
    ids, action = request.session['kotti.paste']
    for count, id in enumerate(ids):
        item = DBSession.query(Node).get(id)
        if item is not None:
            if action == 'cut':
                if not has_permission('edit', item, request):
                    raise Forbidden()
                item.__parent__.children.remove(item)
                context.children.append(item)
                if count is len(ids) - 1:
                    del request.session['kotti.paste']
            elif action == 'copy':
                copy = item.copy()
                name = copy.name
                if not name:  # for root
                    name = copy.title
                name = title_to_name(name, blacklist=context.keys())
                copy.name = name
                context.children.append(copy)
            request.session.flash(_(u'${title} pasted.',
                                    mapping=dict(title=item.title)), 'success')
        else:
            request.session.flash(
                _(u'Could not paste node. It does not exist anymore.'), 'error')
    if not request.is_xhr:
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)


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
    if 'delete' in request.POST:
        parent = context.__parent__
        request.session.flash(_(u'${title} deleted.',
                                mapping=dict(title=context.title)), 'success')
        del parent[context.name]
        location = resource_url(parent, request)
        return HTTPFound(location=location)
    return {}


def delete_nodes(context, request):
    if 'delete_nodes' in request.POST:
        ids = request.POST.getall('children-to-delete')
        if not ids:
            request.session.flash(_(u"Nothing deleted."), 'info')
        for id in ids:
            item = DBSession.query(Node).get(id)
            request.session.flash(_(u'${title} deleted.',
                                    mapping=dict(title=item.title)), 'success')
            del context[item.name]
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)

    if 'cancel' in request.POST:
        request.session.flash(_(u'No changes made.'), 'info')
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)

    ids = _selected_children(context, request, add_context=False)
    if ids is not None:
        items = DBSession.query(Node).filter(Node.id.in_(ids)).order_by(Node.position).all()
        return {'items': items,
                'states': _states(context, request)}
    return {}


def rename_node(context, request):
    if 'rename' in request.POST:
        name = request.POST['name']
        title = request.POST['title']
        if not name or not title:
            request.session.flash(_(u'Name and title are required.'), 'error')
        else:
            context.name = name.replace('/', '')
            context.title = title
            request.session.flash(_(u'Item renamed'), 'success')
            location = resource_url(context, request)
            return HTTPFound(location=location)
    return {}


def rename_nodes(context, request):
    if 'rename_nodes' in request.POST:
        if 'rename_nodes-children' in request.session:
            del request.session['rename_nodes-children']
        ids = request.POST.getall('children-to-rename')
        for id in ids:
            item = DBSession.query(Node).get(id)
            name = request.POST[id + '-name']
            title = request.POST[id + '-title']
            if not name or not title:
                request.session.flash(_(u'Name and title are required.'), 'error')
                location = resource_url(context, request) + '@@rename_nodes'
                return HTTPFound(location=location)
            else:
                item.name = title_to_name(name, blacklist=context.keys())
                item.title = title
        if not ids:
            request.session.flash(_(u'No changes made.'), 'info')
        else:
            request.session.flash(_(u'Your changes have been saved.'), 'success')
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)

    if 'cancel' in request.POST:
        request.session.flash(_(u'No changes made.'), 'info')
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)

    ids = _selected_children(context, request, add_context=False)
    if ids is not None:
        items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
        return {'items': items}
    return {}


def _all_children(item, request, permission='view'):
    """Get recursive all children of the given item.
    """
    tree = nodes_tree(request, context=item, permission='state_change')
    return tree.tolist()[1:]


def change_state(context, request):
    if 'change_state' in request.POST:
        if 'change_state-children' in request.session:
            del request.session['change_state-children']
        ids = request.POST.getall('children-to-change-state')
        to_state = request.POST.get('to-state', u'no-change')
        include_children = request.POST.get('include-children', None)
        if to_state != u'no-change':
            items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
            for item in items:
                wf = get_workflow(item)
                if wf is not None:
                    wf.transition_to_state(item, request, to_state)
                if include_children:
                    childs = _all_children(item, request, 'state_change')
                    for child in childs:
                        wf = get_workflow(child)
                        if wf is not None:
                            wf.transition_to_state(child, request, to_state, )
            request.session.flash(_(u'Your changes have been saved.'), 'success')
        else:
            request.session.flash(_(u'No changes made.'), 'info')
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)

    if 'cancel' in request.POST:
        request.session.flash(_(u'No changes made.'), 'info')
        url = request.referrer or request.resource_url(context)
        return HTTPFound(location=url)

    ids = _selected_children(context, request, add_context=False)
    if ids is not None:
        wf = get_workflow(context)
        if wf is not None:
            items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
            transitions = []
            for item in items:
                    trans_info = wf.get_transitions(item, request)
                    for tran_info in trans_info:
                        if tran_info not in transitions:
                            transitions.append(tran_info)
            return {'items': items,
                    'states': _states(context, request),
                    'transitions': transitions, }
    return {}


@deprecate(
"""'generic_edit' is deprecated as of Kotti 0.8.0.  Use a form class
derived from 'kotti.views.form.EditFormView' instead.  See
'kotti.views.edit.content' for an example.
""")
def generic_edit(context, request, schema, **kwargs):
    return EditFormView(
        context,
        request,
        schema=schema,
        **kwargs
        )()


@deprecate(
"""'generic_edit' is deprecated as of Kotti 0.8.0.  Use a form class
derived from 'kotti.views.form.AddFormView' instead.  See
'kotti.views.edit.content' for an example.
""")
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

    config.add_view(
        workflow_change,
        name='workflow-change',
        permission='state_change',
        )

    config.add_view(
        workflow,
        name='workflow-dropdown',
        permission='edit',
        renderer='kotti:templates/workflow-dropdown.pt',
        )


def nodes_includeme(config):
    config.add_view(
        contents,
        context=IContent,
        name='contents',
        permission='view',
        renderer='kotti:templates/edit/contents.pt',
        )

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
        delete_nodes,
        name='delete_nodes',
        permission='edit',
        renderer='kotti:templates/edit/delete-nodes.pt',
        )

    config.add_view(
        rename_node,
        name='rename',
        permission='edit',
        renderer='kotti:templates/edit/rename.pt',
        )

    config.add_view(
        rename_nodes,
        name='rename_nodes',
        permission='edit',
        renderer='kotti:templates/edit/rename-nodes.pt',
        )

    config.add_view(
        change_state,
        name='change_state',
        permission='edit',
        renderer='kotti:templates/edit/change-state.pt',
        )

    config.scan("kotti.views.edit.default_view_selection")

    config.include('kotti.views.edit.content')
