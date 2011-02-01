from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
from pyramid.security import has_permission
from pyramid.security import view_execution_permitted
from pyramid.url import resource_url
from pyramid.view import is_response
import colander
from deform import Form
from deform import ValidationFailure
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti import configuration
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.views.util import TemplateAPIEdit
from kotti.views.util import addable_types
from kotti.views.util import title_to_name
from kotti.views.util import disambiguate_name

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
        widget=RichTextWidget(),
        missing=u"",
        )

class FormView(object):
    renderer = '../templates/edit/node.pt'
    add = None
    post_key = 'save'
    edit_success_msg = u"Your changes have been saved."
    add_success_msg = u"Successfully added item."
    error_msg = (u"There was a problem with your submission.\n"
                 u"Errors have been highlighted below.")
    success_path = 'edit'

    def __init__(self, form, api=None, **kwargs):
        self.form = form
        self.api = api
        for key, value in kwargs.items():
            if key in self.__class__.__dict__:
                setattr(self, key, value)
            else: # pragma: no coverage
                raise TypeError("Unknown argument %r" % key)

    def __call__(self, context, request):
        if self.api is None:
            self.api = TemplateAPIEdit(context, request)

        result = self._handle_form(context, request)
        if is_response(result):
            return result
        else:
            return render_to_response(
                self.renderer,
                {'form': result, 'api': self.api},
                request=request,
                )

    def _handle_form(self, context, request):
        if self.post_key in request.POST:
            controls = request.POST.items()
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                request.session.flash(self.error_msg, 'error')
                return e.render()
            else:
                if self.add is None: # edit
                    for key, value in appstruct.items():
                        setattr(context, key, value)
                    request.session.flash(self.edit_success_msg, 'success')
                    location = resource_url(context, request, self.success_path)
                    return HTTPFound(location=location)
                else: # add
                    name = title_to_name(appstruct['title'])
                    while name in context.keys():
                        name = disambiguate_name(name)
                    item = context[name] = self.add(**appstruct)
                    request.session.flash(self.add_success_msg, 'success')
                    location = resource_url(item, request, self.success_path)
                    return HTTPFound(location=location)
        else: # no post means less action
            if self.add is None:
                return self.form.render(context.__dict__)
            else:
                return self.form.render()
    render = __call__

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
        location = resource_url(
            where, request, what.type_info.add_view)
        return HTTPFound(location=location)

    possible_parents, possible_types = addable_types(context, request)
    if len(possible_parents) == 1 and len(possible_parents[0]['factories']) == 1:
        # Redirect to the add form straight away if there's only one
        # choice of parents and addable types:
        parent = possible_parents[0]
        add_view = parent['factories'][0].type_info.add_view
        location = resource_url(parent['node'], request, add_view)
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
        parent.children.remove(context)

        elements = []
        if view_execution_permitted(parent, request, 'edit'):
            elements.append('edit')
        location = resource_url(parent, request, *elements)
        request.session.flash(u'%s deleted.' % context.title, 'success')
        return HTTPFound(location=location)

    return {
        'api': TemplateAPIEdit(context, request),
        }

def edit_document(context, request):
    form = Form(DocumentSchema(), buttons=('save',))
    return FormView(form)(context, request)

def add_document(context, request):
    api = TemplateAPIEdit(
        context, request,
        first_heading=u'<h1>Add document to <em>%s</em></h1>' % context.title)
    form = Form(DocumentSchema(), buttons=('save',))
    return FormView(form, add=Document, api=api)(context, request)

def includeme(config):
    config.add_view(
        edit_document,
        context=Document,
        name='edit',
        permission='edit',
        )

    config.add_view(
        add_document,
        name=Document.type_info.add_view,
        permission='add',
        )
