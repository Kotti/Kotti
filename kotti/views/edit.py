from pyramid.view import is_response
from pyramid.renderers import render_to_response
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPFound
import colander
from deform import Form
from deform import ValidationFailure
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti import configuration
from kotti.resources import DBSession
from kotti.resources import Document
from kotti.resources import Node
from kotti.views import TemplateAPI

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

    def __init__(self, form, **kwargs):
        self.form = form
        for key, value in kwargs.items():
            if key in self.__class__.__dict__:
                setattr(self, key, value)
            else:
                raise TypeError("Unknown argument %r" % key)

    def __call__(self, context, request):
        result = self._handle_form(context, request)
        if is_response(result):
            return result
        else:
            return render_to_response(
                self.renderer,
                {'form': result, 'api': TemplateAPI(context, request)},
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
                    name = self._title_to_name(appstruct['title'])
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

    def _title_to_name(self, title):
        return title

def node_add(context, request):
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
        location = resource_url(where, request, what.type_info.add_view)
        return HTTPFound(location=location)

    # 'possible_parents' is a list of dicts with 'node' and 'factories',
    # where 'node' is the context to add to and 'factories' is the list
    # of factories that can be applied in the contetx:
    possible_parents = []
    parent = context
    while parent is not None:
        possible_parents.append({'node': parent, 'factories': []})
        parent = parent.__parent__

    for entry in possible_parents:
        parent_info = entry['node'].type_info
        for factory in all_types:
            if parent_info.name in factory.type_info.addable_to:
                # XXX Check for permission for factory.type_info.add_view
                entry['factories'].append(factory)

    possible_parents = filter(lambda e: e['factories'], possible_parents)

    _possible_types = {}
    for entry in possible_parents:
        for factory in entry['factories']:
            name = factory.type_info.name
            pt = _possible_types.get(name, {'factory': factory, 'nodes': []})
            pt['nodes'].append(entry['node'])
            _possible_types[name] = pt

    possible_types = []
    for t in all_types:
        entry = _possible_types.get(t.type_info.name)
        if entry:
            possible_types.append(entry)

    if len(possible_parents) == 1 and len(possible_parents[0]['factories']) == 1:
        # Redirect to the add form straight away if there's only one
        # choice of parents and addable types:
        parent = possible_parents[0]
        add_view = parent['factories'][0].type_info.add_view
        location = resource_url(parent['node'], request, add_view)
        return HTTPFound(location=location)

    return {
        'api': TemplateAPI(context, request),
        'possible_parents': possible_parents,
        'possible_types': possible_types,
        }

def document_edit(context, request):
    form = Form(DocumentSchema(), buttons=('save',))
    return FormView(form)(context, request)

def document_add(context, request):
    form = Form(DocumentSchema(), buttons=('save',))
    return FormView(form, add=Document)(context, request)

def includeme(config):
    config.add_view(
        document_edit,
        context=Document,
        name='edit',
        permission='edit',
        )

    config.add_view(
        node_add,
        name='add',
        permission='add',
        renderer='../templates/edit/add.pt',
        )

    config.add_view(
        document_add,
        name=Document.type_info.add_view,
        permission='add',
        )
