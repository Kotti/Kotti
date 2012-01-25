from colander import MappingSchema
from colander import SchemaNode
from colander import String
from colander import null
from colander import required
from deform import FileData
from pyramid.response import Response

from kotti.resources import File
from kotti.views.util import EditFormView
from kotti.views.util import AddFormView

def FileSchema():
    class FileSchema(MappingSchema):
        title = SchemaNode(String(), missing=u'')
        description = SchemaNode(String(), missing=u'')
        file = SchemaNode(FileData())
    return FileSchema()

def inline_view(context, request, disposition='inline'):
    res = Response(
        headerlist=[
            ('Content-Disposition', '%s;filename="%s"' % (
                disposition, context.filename)),
            ('Content-Length', context.size),
            ('Content-Type', context.mimetype),
            ],
        app_iter=context.data,
        )
    return res

def attachment_view(context, request):
    return inline_view(context, request, 'attachment')

class EditFileFormView(EditFormView):
    schema = FileSchema()
    schema['title'].missing = required
    schema['file'].missing = null

    def edit(self, **appstruct):
        self.context.title = appstruct['title']
        self.context.description = appstruct['description']
        if appstruct['file']:
            buf = appstruct['file']['fp'].read()
            self.context.data = buf
            self.context.filename = appstruct['file']['filename']
            self.context.mimetype = appstruct['file']['mimetype']
            self.context.size = len(buf)

class AddFileFormView(AddFormView):
    schema = FileSchema()
    
    def save_success(self, appstruct):
        if not appstruct['title']:
            appstruct['title'] = appstruct['file']['filename']
        super(AddFileFormView, self).save_success(appstruct)

    def add(self, **appstruct):
        buf = appstruct['file']['fp'].read()
        return File(
            title=appstruct['title'],
            description=appstruct['description'],
            data=buf,
            filename=appstruct['file']['filename'],
            mimetype=appstruct['file']['mimetype'],
            size=len(buf),
            )

def includeme(config):
    config.add_view(
        inline_view,
        context=File,
        name='inline-view',
        permission='view',
        )

    config.add_view(
        attachment_view,
        context=File,
        name='attachment-view',
        permission='view',
        )

    config.add_view(
        EditFileFormView,
        context=File,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        AddFileFormView,
        name=File.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )
