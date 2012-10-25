from pyramid.httpexceptions import HTTPFound
from pyramid.location import inside
from pyramid.url import resource_url
from zope.deprecation.deprecation import deprecate

from kotti import DBSession
from kotti import get_settings
from kotti.resources import IContent
from kotti.resources import Node
from kotti.resources import get_root
from kotti.util import _
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
    """Choose the current action for our contents view. Gets called when
       you click on the "Contents" Tab, or when you do an action in the
       "Contents" view.
    """
    buttons = contents_buttons(context, request)
    for button in buttons:
        if button.path in request.POST:
            children = request.POST.getall('children')
            if not children and button.path != u'paste':
                request.session.flash(_(u'You have to choose items to \
                                        perform an action.'), 'info')
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
        workflow,
        name='workflow-dropdown',
        permission='edit',
        renderer='kotti:templates/workflow-dropdown.pt',
        )

    config.add_view(
        contents,
        context=IContent,
        name='contents',
        permission='view',
        renderer='kotti:templates/edit/contents.pt',
        )


def nodes_includeme(config):

    config.scan("kotti.views.edit.default_view_selection")
    config.scan("kotti.views.edit.node_actions")

    config.include('kotti.views.edit.content')
