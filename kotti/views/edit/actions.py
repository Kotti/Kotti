"""
Action views
"""

from pyramid.httpexceptions import HTTPFound
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from pyramid.security import has_permission
from pyramid.view import view_defaults
from zope.deprecation import deprecated

from kotti import DBSession
from kotti import get_settings
from kotti.fanstatic import contents_view_js
from kotti.interfaces import IContent
from kotti.resources import Node
from kotti.util import _
from kotti.util import ActionButton
from kotti.util import get_paste_items
from kotti.util import title_to_name
from kotti.views.edit import _state_info
from kotti.views.edit import _states
from kotti.views.form import EditFormView
from kotti.views.navigation import render_tree_navigation
from kotti.views.util import nodes_tree
from kotti.workflow import get_workflow


@view_defaults(permission='edit')
class NodeActions(object):
    """Actions related to content nodes."""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.flash = self.request.session.flash

    def _selected_children(self, add_context=True):
        """
        Get the selected children of the given context. This are either
        the selected nodes of the contents view or the context itself.

        :result: List with select children.
        :rtype: list
        """
        ids = self.request.session.pop('kotti.selected-children')
        if ids is None and add_context:
            ids = [self.context.id]
        return ids

    def _all_children(self, context, permission='view'):
        """
        Get recursive all children of the given context.

        :result: List with all children of a given context.
        :rtype: list
        """
        tree = nodes_tree(self.request,
                          context=context,
                          permission=permission)
        return tree.tolist()[1:]

    def back(self, view=None):
        """
        Redirect to the given view of the context, the referrer of the request
        or the default_view of the context.

        :rtype: pyramid.httpexceptions.HTTPFound
        """
        url = self.request.resource_url(self.context)
        if view is not None:
            url += view
        elif self.request.referrer:
            url = self.request.referrer
        return HTTPFound(location=url)

    @view_config(name='workflow-change',
                 permission='state_change')
    def workflow_change(self):
        """
        Handle workflow change requests from workflow dropdown.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        new_state = self.request.params['new_state']
        wf = get_workflow(self.context)
        wf.transition_to_state(self.context, self.request, new_state)
        self.flash(EditFormView.success_message, 'success')
        return self.back()

    @view_config(name='copy')
    def copy_node(self):
        """
        Copy nodes view. Copy the current node or the selected nodes in the
        contents view and save the result in the session of the request.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        ids = self._selected_children()
        self.request.session['kotti.paste'] = (ids, 'copy')
        for id in ids:
            item = DBSession.query(Node).get(id)
            self.flash(_(u'${title} was copied.',
                         mapping=dict(title=item.title)), 'success')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='cut')
    def cut_nodes(self):
        """
        Cut nodes view. Cut the current node or the selected nodes in the
        contents view and save the result in the session of the request.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        ids = self._selected_children()
        self.request.session['kotti.paste'] = (ids, 'cut')
        for id in ids:
            item = DBSession.query(Node).get(id)
            self.flash(_(u'${title} was cut.', mapping=dict(title=item.title)),
                       'success')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='paste')
    def paste_nodes(self):
        """
        Paste nodes view. Paste formerly copied or cutted nodes into the
        current context. Note that a cutted node can not be pasted into itself.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        ids, action = self.request.session['kotti.paste']
        for count, id in enumerate(ids):
            item = DBSession.query(Node).get(id)
            if item is not None:
                if action == 'cut':
                    if not has_permission('edit', item, self.request):
                        raise Forbidden()
                    item.__parent__.children.remove(item)
                    item.name = title_to_name(item.name,
                                              blacklist=self.context.keys())
                    self.context[item.name] = item
                    if count is len(ids) - 1:
                        del self.request.session['kotti.paste']
                elif action == 'copy':
                    copy = item.copy()
                    name = copy.name
                    if not name:  # for root
                        name = copy.title
                    name = title_to_name(name, blacklist=self.context.keys())
                    copy.name = name
                    self.context[name] = copy
                self.flash(_(u'${title} was pasted.',
                             mapping=dict(title=item.title)), 'success')
            else:
                self.flash(_(u'Could not paste node. It no longer exists.'),
                           'error')
        if not self.request.is_xhr:
            return self.back()

    def move(self, move):
        """
        Do the real work to move the selected nodes up or down. Called
        by the up and the down view.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        ids = self._selected_children()
        if move == 1:
            ids.reverse()
        for id in ids:
            child = DBSession.query(Node).get(id)
            index = self.context.children.index(child)
            self.context.children.pop(index)
            self.context.children.insert(index + move, child)
            self.flash(_(u'${title} was moved.',
                         mapping=dict(title=child.title)), 'success')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='up')
    def up(self):
        """
        Move up nodes view. Move the selected nodes up by 1 position
        and get back to the referrer of the request.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        return self.move(-1)

    @view_config(name='down')
    def down(self):
        """
        Move down nodes view. Move the selected nodes down by 1 position
        and get back to the referrer of the request.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        return self.move(1)

    def set_visibility(self, show):
        """
        Do the real work to set the visibility of nodes in the menu. Called
        by the show and the hide view.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        ids = self._selected_children()
        for id in ids:
            child = DBSession.query(Node).get(id)
            if child.in_navigation != show:
                child.in_navigation = show
                mapping = dict(title=child.title)
                if show:
                    msg = _(u'${title} is now visible in the navigation.',
                            mapping=mapping)
                else:
                    msg = _(u'${title} is no longer visible in the navigation.',
                            mapping=mapping)
                self.flash(msg, 'success')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='show')
    def show(self):
        """
        Show nodes view.  Switch the in_navigation attribute of selected nodes
        to ``True`` and get back to the referrer of the request.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        return self.set_visibility(True)

    @view_config(name='hide')
    def hide(self):
        """
        Hide nodes view. Switch the in_navigation attribute of selected nodes
        to ``False`` and get back to the referrer of the request.

        :result: Redirect response to the referrer of the request.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        return self.set_visibility(False)

    @view_config(name='delete',
                 permission='delete',
                 renderer='kotti:templates/edit/delete.pt')
    def delete_node(self):
        """
        Delete node view. Renders either a view to delete the current node
        or handle the deletion of the current node and get back to the
        default view of the node.

        :result: Either a redirect response or a dictionary passed to the
                 template for rendering.
        :rtype: pyramid.httpexceptions.HTTPFound or dict
        """

        action = self.request.POST.get(u'delete', None)
        if action is not None:

            parent = self.context.__parent__

            if action == u'delete':
                location = resource_url(parent, self.request)
                self.flash(_(u'${title} was deleted.',
                             mapping=dict(title=self.context.title)),
                           u'success')
                del parent[self.context.name]
            else:
                location = resource_url(self.context, self.request)

            return HTTPFound(location=location)

        return {}

    @view_config(name='delete_nodes',
                 permission='delete',
                 renderer='kotti:templates/edit/delete-nodes.pt')
    def delete_nodes(self):
        """
        Delete nodes view. Renders either a view to delete multiple nodes or
        delete the selected nodes and get back to the referrer of the request.

        :result: Either a redirect response or a dictionary passed to the
                 template for rendering.
        :rtype: pyramid.httpexceptions.HTTPFound or dict
        """
        if 'delete_nodes' in self.request.POST:
            ids = self.request.POST.getall('children-to-delete')
            if not ids:
                self.flash(_(u"Nothing was deleted."), 'info')
            for id in ids:
                item = DBSession.query(Node).get(id)
                self.flash(_(u'${title} was deleted.',
                             mapping=dict(title=item.title)), 'success')
                del self.context[item.name]
            return self.back('@@contents')

        if 'cancel' in self.request.POST:
            self.flash(_(u'No changes were made.'), 'info')
            return self.back('@@contents')

        ids = self._selected_children(add_context=False)
        items = []
        if ids is not None:
            items = DBSession.query(Node).filter(Node.id.in_(ids)).\
                order_by(Node.position).all()
        return {'items': items,
                'states': _states(self.context, self.request)}

    @view_config(name='rename',
                 renderer='kotti:templates/edit/rename.pt')
    def rename_node(self):
        """
        Rename node view. Renders either a view to change the title and
        name for the current node or handle the changes and get back to the
        default view of the node.

        :result: Either a redirect response or a dictionary passed to the
                 template for rendering.
        :rtype: pyramid.httpexceptions.HTTPFound or dict
        """
        if 'rename' in self.request.POST:
            name = self.request.POST['name']
            title = self.request.POST['title']
            if not name or not title:
                self.flash(_(u'Name and title are required.'), 'error')
            else:
                self.context.name = name.replace('/', '')
                self.context.title = title
                self.flash(_(u'Item was renamed.'), 'success')
                return self.back('')
        return {}

    @view_config(name='rename_nodes',
                 renderer='kotti:templates/edit/rename-nodes.pt')
    def rename_nodes(self):
        """
        Rename nodes view. Renders either a view to change the titles and
        names for multiple nodes or handle the changes and get back to the
        referrer of the request.

        :result: Either a redirect response or a dictionary passed to the
                 template for rendering.
        :rtype: pyramid.httpexceptions.HTTPFound or dict
        """
        if 'rename_nodes' in self.request.POST:
            ids = self.request.POST.getall('children-to-rename')
            for id in ids:
                item = DBSession.query(Node).get(id)
                name = self.request.POST[id + '-name']
                title = self.request.POST[id + '-title']
                if not name or not title:
                    self.flash(_(u'Name and title are required.'), 'error')
                    location = resource_url(self.context, self.request,
                                            '@@rename_nodes')
                    return HTTPFound(location=location)
                else:
                    item.name = title_to_name(name,
                                              blacklist=self.context.keys())
                    item.title = title
            self.flash(_(u'Your changes have been saved.'), 'success')
            return self.back('@@contents')

        if 'cancel' in self.request.POST:
            self.flash(_(u'No changes were made.'), 'info')
            return self.back('@@contents')

        ids = self._selected_children(add_context=False)
        items = []
        if ids is not None:
            items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
        return {'items': items}

    @view_config(name='change_state',
                 renderer='kotti:templates/edit/change-state.pt')
    def change_state(self):
        """
        Change state view. Renders either a view to handle workflow changes
        for multiple nodes or handle the selected workflow changes and get
        back to the referrer of the request.

        :result: Either a redirect response or a dictionary passed to the
                 template for rendering.
        :rtype: pyramid.httpexceptions.HTTPFound or dict
        """
        if 'change_state' in self.request.POST:
            ids = self.request.POST.getall('children-to-change-state')
            to_state = self.request.POST.get('to-state', u'no-change')
            include_children = self.request.POST.get('include-children', None)
            if to_state != u'no-change':
                items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
                for item in items:
                    wf = get_workflow(item)
                    if wf is not None:
                        wf.transition_to_state(item, self.request, to_state)
                    if include_children:
                        childs = self._all_children(item,
                                                    permission='state_change')
                        for child in childs:
                            wf = get_workflow(child)
                            if wf is not None:
                                wf.transition_to_state(child,
                                                       self.request,
                                                       to_state, )
                self.flash(_(u'Your changes have been saved.'), 'success')
            else:
                self.flash(_(u'No changes were made.'), 'info')
            return self.back('@@contents')

        if 'cancel' in self.request.POST:
            self.flash(_(u'No changes were made.'), 'info')
            return self.back('@@contents')

        ids = self._selected_children(add_context=False)
        items = transitions = []
        if ids is not None:
            wf = get_workflow(self.context)
            if wf is not None:
                items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
                for item in items:
                        trans_info = wf.get_transitions(item, self.request)
                        for tran_info in trans_info:
                            if tran_info not in transitions:
                                transitions.append(tran_info)
        return {'items': items,
                'states': _states(self.context, self.request),
                'transitions': transitions, }


def contents_buttons(context, request):
    """
    Build the action buttons for the contents view based on the current
    state and the persmissions of the user.

    :result: List of ActionButtons.
    :rtype: list
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
        buttons.append(ActionButton('up', title=_(u'Move up')))
        buttons.append(ActionButton('down', title=_(u'Move down')))
        buttons.append(ActionButton('show', title=_(u'Show')))
        buttons.append(ActionButton('hide', title=_(u'Hide')))
    return [button for button in buttons if button.permitted(context, request)]


@view_config(name='add-dropdown',
             renderer='kotti:templates/add-dropdown.pt')
def content_type_factories(context, request):
    """
    Renders the drop down menu for Add button in editor bar.

    :result: Dictionary passed to the template for rendering.
    :rtype: pyramid.httpexceptions.HTTPFound or dict
    """
    all_types = get_settings()['kotti.available_types']
    factories = []
    for factory in all_types:
        if factory.type_info.addable(context, request):
            factories.append(factory)
    return {'factories': factories}


@view_config(context=IContent, name='contents', permission='view',
             renderer='kotti:templates/edit/contents.pt')
def contents(context, request):
    """
    Contents view. Renders either the contents view or handle the action
    button actions of the view.

    :result: Either a redirect response or a dictionary passed to the
             template for rendering.
    :rtype: pyramid.httpexceptions.HTTPFound or dict
    """
    contents_view_js.need()
    buttons = contents_buttons(context, request)
    for button in buttons:
        if button.name in request.POST:
            children = request.POST.getall('children')
            if not children and button.name != u'paste':
                request.session.flash(
                    _(u'You have to select items to perform an action.'),
                    'info')
                location = resource_url(context, request) + '@@contents'
                return HTTPFound(location=location)
            request.session['kotti.selected-children'] = children
            location = button.url(context, request)
            return HTTPFound(location, request=request)

    return {'children': context.children_with_permission(request),
            'buttons': buttons,
            }


@view_config(name='move-child-position', permission='edit',
             request_method="POST", renderer="json")
def move_child_position(context, request):
    """ Move the child from one position to another.

    :param context: "Container" node in which the child changes its position.
    :type context: :class:kotti.resources.Node or descendant

    :param request: Current request (of method POST).  Must contain either
                    "from" and "to" params or a json_body that contain(s) the
                    0-based old (i.e. the current index of the child to be
                    moved) and new position (its new index) values.
    :type request:
    :result: JSON serializable object with a single attribute ("result") that is
             either "success" or "error".
    :rtype: dict
    """

    data = request.POST or request.json_body

    if ('from' in data) and ('to' in data):

        max_pos = len(context.children) - 1
        try:
            oldPosition = int(data['from'])
            newPosition = int(data['to'])
            if not ((0 <= oldPosition <= max_pos) and
                    (0 <= newPosition <= max_pos)):
                raise ValueError
        except ValueError:
            return {'result': 'error'}

        # sqlalchemy.ext.orderinglist takes care of the "right" sequence
        # numbers (immediately consecutive, starting with 0) for us.
        context.children.insert(newPosition,
                                context.children.pop(oldPosition))
        result = 'success'
    else:
        result = 'error'

    return {'result': result}


@view_config(name='workflow-dropdown', permission='view',
             renderer='kotti:templates/workflow-dropdown.pt')
def workflow(context, request):
    """
    Renders the drop down menu for workflow actions.

    :result: Dictionary passed to the template for rendering.
    :rtype: dict
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


@view_config(name='actions-dropdown', permission='edit',
             renderer='kotti:templates/actions-dropdown.pt')
def actions(context, request):
    """
    Renders the drop down menu for Actions button in editor bar.

    :result: Dictionary passed to the template for rendering.
    :rtype: dict
    """
    actions = []
    if hasattr(context, 'type_info'):
        actions = [a for a in context.type_info.action_links
                   if a.visible(context, request)]
    return {'actions': actions}


def includeme(config):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        config.scan(__name__)


# BBB starts here --- --- --- --- --- ---

render_tree_navigation = render_tree_navigation

deprecated(
    'render_tree_navigation',
    'render_tree_navigation has been moved to kotti.views.navigation as of '
    'Kotti 0.9.  Import from there instead.'
)
