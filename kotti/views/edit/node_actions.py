from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.view import view_defaults

from kotti import DBSession
from kotti.resources import Node
from kotti.util import _
from kotti.util import title_to_name
from kotti.views.edit import _all_children
from kotti.views.edit import _selected_children
from kotti.views.edit import _states
from kotti.views.form import EditFormView
from kotti.workflow import get_workflow


@view_defaults(permission='edit')
class NodeActions(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def back(self):
        """
        :summary: Redirect to the referrer or the default_view of the context.
        :rtype: pyramid.httpexceptions.HTTPFound
        """
        url = self.request.referrer or self.request.resource_url(self.context)
        return HTTPFound(location=url)

    @view_config(name='workflow-change',
                 permission='state-change')
    def workflow_change(self):
        """Handle workflow change requests from workflow dropdown.
        """
        new_state = self.request.params['new_state']
        wf = get_workflow(self.context)
        wf.transition_to_state(self.context, self.request, new_state)
        self.request.session.flash(EditFormView.success_message, 'success')
        return self.back()

    @view_config(name='copy')
    def copy_node(self):
        ids = _selected_children(self.context, self.request)
        self.request.session['kotti.paste'] = (ids, 'copy')
        for id in ids:
            item = DBSession.query(Node).get(id)
            self.request.session.flash(_(u'${title} copied.',
                                    mapping=dict(title=item.title)), 'success')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='cut')
    def cut_node(self):
        ids = _selected_children(self.context, self.request)
        self.request.session['kotti.paste'] = (ids, 'cut')
        for id in ids:
            item = DBSession.query(Node).get(id)
            self.request.session.flash(_(u'${title} cut.',
                                mapping=dict(title=item.title)), 'success')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='paste')
    def paste_node(self):
        ids, action = self.request.session['kotti.paste']
        for count, id in enumerate(ids):
            item = DBSession.query(Node).get(id)
            if item is not None:
                if action == 'cut':
                    if not has_permission('edit', item, self.request):
                        raise Forbidden()
                    item.__parent__.children.remove(item)
                    self.context.children.append(item)
                    if count is len(ids) - 1:
                        del self.request.session['kotti.paste']
                elif action == 'copy':
                    copy = item.copy()
                    name = copy.name
                    if not name:  # for root
                        name = copy.title
                    name = title_to_name(name, blacklist=self.context.keys())
                    copy.name = name
                    self.context.children.append(copy)
                self.request.session.flash(_(u'${title} pasted.',
                                    mapping=dict(title=item.title)), 'success')
            else:
                self.request.session.flash(
                    _(u'Could not paste node. It does not exist anymore.'),
                    'error')
        if not self.request.is_xhr:
            return self.back()

    @view_config(name='order',
                 renderer='kotti:templates/edit/order.pt')
    def order_node(self):
        P = self.request.POST

        if 'order-up' in P or 'order-down' in P:
            up, down = P.get('order-up'), P.get('order-down')
            child = DBSession.query(Node).get(int(down or up))
            if up is not None:
                mod = -1
            else:  # pragma: no cover
                mod = 1
            index = self.context.children.index(child)
            self.context.children.pop(index)
            self.context.children.insert(index + mod, child)
            self.request.session.flash(_(u'${title} moved.',
                                    mapping=dict(title=child.title)), 'success')
            if not self.request.is_xhr:
                return HTTPFound(location=self.request.url)

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
            self.request.session.flash(msg, 'success')
            if not self.request.is_xhr:
                return HTTPFound(location=self.request.url)

        return {}

    @view_config(name='delete',
                 renderer='kotti:templates/edit/delete.pt')
    def delete_node(self):
        if 'delete' in self.request.POST:
            parent = self.context.__parent__
            self.request.session.flash(_(u'${title} deleted.',
                            mapping=dict(title=self.context.title)), 'success')
            del parent[self.context.name]
            location = resource_url(parent, self.request)
            return HTTPFound(location=location)
        return {}

    @view_config(name='delete_nodes',
                 renderer='kotti:templates/edit/delete-nodes.pt')
    def delete_nodes(self):
        if 'delete_nodes' in self.request.POST:
            ids = self.request.POST.getall('children-to-delete')
            if not ids:
                self.request.session.flash(_(u"Nothing deleted."), 'info')
            for id in ids:
                item = DBSession.query(Node).get(id)
                self.request.session.flash(_(u'${title} deleted.',
                                mapping=dict(title=item.title)), 'success')
                del self.context[item.name]
            return self.back()

        if 'cancel' in self.request.POST:
            self.request.session.flash(_(u'No changes made.'), 'info')
            return self.back()

        ids = _selected_children(self.context, self.request, add_context=False)
        if ids is not None:
            items = DBSession.query(Node).filter(Node.id.in_(ids)).\
                order_by(Node.position).all()
            return {'items': items,
                    'states': _states(self.context, self.request)}
        return {}

    @view_config(name='rename',
                 renderer='kotti:templates/edit/rename.pt')
    def rename_node(self):
        if 'rename' in self.request.POST:
            name = self.request.POST['name']
            title = self.request.POST['title']
            if not name or not title:
                self.request.session.flash(
                    _(u'Name and title are required.'), 'error')
            else:
                self.context.name = name.replace('/', '')
                self.context.title = title
                self.request.session.flash(_(u'Item renamed'), 'success')
                location = resource_url(self.context, self.request)
                return HTTPFound(location=location)
        return {}

    @view_config(name='rename_nodes',
                 renderer='kotti:templates/edit/rename-nodes.pt')
    def rename_nodes(self):
        if 'rename_nodes' in self.request.POST:
            if 'rename_nodes-children' in self.request.session:
                del self.request.session['rename_nodes-children']
            ids = self.request.POST.getall('children-to-rename')
            for id in ids:
                item = DBSession.query(Node).get(id)
                name = self.request.POST[id + '-name']
                title = self.request.POST[id + '-title']
                if not name or not title:
                    self.request.session.flash(
                        _(u'Name and title are required.'), 'error')
                    location = resource_url(self.context,
                                            self.request) + '@@rename_nodes'
                    return HTTPFound(location=location)
                else:
                    item.name = title_to_name(name,
                                              blacklist=self.context.keys())
                    item.title = title
            if not ids:
                self.request.session.flash(_(u'No changes made.'), 'info')
            else:
                self.request.session.flash(
                    _(u'Your changes have been saved.'), 'success')
            return self.back()

        if 'cancel' in self.request.POST:
            self.request.session.flash(_(u'No changes made.'), 'info')
            return self.back()

        ids = _selected_children(self.context, self.request, add_context=False)
        if ids is not None:
            items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
            return {'items': items}
        return {}

    @view_config(name='change_state',
                 renderer='kotti:templates/edit/change-state.pt')
    def change_state(self):
        if 'change_state' in self.request.POST:
            if 'change_state-children' in self.request.session:
                del self.request.session['change_state-children']
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
                        childs = _all_children(item,
                                               self.request,
                                               'state_change')
                        for child in childs:
                            wf = get_workflow(child)
                            if wf is not None:
                                wf.transition_to_state(child,
                                                       self.request,
                                                       to_state, )
                self.request.session.flash(
                    _(u'Your changes have been saved.'), 'success')
            else:
                self.request.session.flash(_(u'No changes made.'), 'info')
            return self.back()

        if 'cancel' in self.request.POST:
            self.request.session.flash(_(u'No changes made.'), 'info')
            return self.back()

        ids = _selected_children(self.context, self.request, add_context=False)
        if ids is not None:
            wf = get_workflow(self.context)
            if wf is not None:
                items = DBSession.query(Node).filter(Node.id.in_(ids)).all()
                transitions = []
                for item in items:
                        trans_info = wf.get_transitions(item, self.request)
                        for tran_info in trans_info:
                            if tran_info not in transitions:
                                transitions.append(tran_info)
                return {'items': items,
                        'states': _states(self.context, self.request),
                        'transitions': transitions, }
        return {}
