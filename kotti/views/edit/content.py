import colander
from deform.widget import RichTextWidget

from kotti.resources import Document
from kotti.util import _
from kotti.views.form import AddFormView
from kotti.views.form import ContentSchema
from kotti.views.form import EditFormView


class DocumentSchema(ContentSchema):
    body = colander.SchemaNode(
        colander.String(),
        title=_(u'Body'),
        widget=RichTextWidget(theme='advanced', width=790, height=500),
        missing=u"",
        )


class DocumentEditForm(EditFormView):
    schema_factory = DocumentSchema


class DocumentAddForm(AddFormView):
    add = Document
    schema_factory = DocumentSchema


def includeme(config):
    config.add_view(
        DocumentEditForm,
        context=Document,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        DocumentAddForm,
        name=Document.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )
