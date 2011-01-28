import colander
from deform import Form
from deform import ValidationFailure
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

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

def document_edit(context, request):
    form = Form(DocumentSchema(), buttons=('save',))
    appstruct = None
    rendered_form = None

    if 'save' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            rendered_form = e.render()

    if appstruct:
        for key, value in appstruct.items():
            setattr(context, key, value)
        if u'mime_type' not in appstruct:
            context.mime_type = u'text/html'

    if rendered_form is None:
        rendered_form = form.render(context.__dict__)

    return {
        'context': context,
        'api': TemplateAPI(context, request),
        'form': rendered_form,
        }

def includeme(config):
    config.add_view(
        document_edit,
        context=Document,
        name='edit',
        permission='edit',
        renderer='../templates/document_edit.pt',
        )
