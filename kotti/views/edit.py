from pyramid.view import is_response
from pyramid.view import render_view_to_response
from pyramid.renderers import render_to_response
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPFound
import colander
from deform import Form
from deform import ValidationFailure
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti import configuration
from kotti.resources import Document
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
    renderer = '../templates/node_edit.pt'
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
            value = {'context': context,
                     'form': result,
                     'api': TemplateAPI(context, request)}
            return render_to_response(
                self.renderer, value, request=request)

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
    return render_view_to_response(context, request, 'document_add')
    possible_types = []
    parent_info = context.type_info
    for t in configuration['kotti.available_types']:
        child_info = t.type_info
        if parent_info.name in child_info.addable_to:
            possible_types.append(t)

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
        )

    config.add_view(
        document_add,
        name=Document.type_info.add_view,
        permission=Document.type_info.add_permission,
        )
