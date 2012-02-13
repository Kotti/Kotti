from StringIO import StringIO
from UserDict import DictMixin

from colander import MappingSchema
from colander import SchemaNode
from colander import String
from colander import null
from deform import FileData
from deform.widget import FileUploadWidget
from deform.widget import TextAreaWidget
from pyramid.response import Response

from kotti.resources import File
from kotti.views.edit import ContentSchema
from kotti.views.util import EditFormView
from kotti.views.util import AddFormView

class FileUploadTempStore(DictMixin):
    def __init__(self, request):
        self.session = request.session

    def keys(self):
        return [k for k in self.session.keys() if not k.startswith('_')]

    def __setitem__(self, name, value):
        value = value.copy()
        fp = value.pop('fp')
        value['file_contents'] = fp.read()
        fp.seek(0)
        self.session[name] = value

    def __getitem__(self, name):
        value = self.session[name].copy()
        value['fp'] = StringIO(value.pop('file_contents'))
        return value

    def __delitem__(self, name):
        del self.session[name]

    def preview_url(self, name):
        return None

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
    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)
        class FileSchema(ContentSchema):
            file = SchemaNode(
                FileData(),
                missing=null,
                widget=FileUploadWidget(tmpstore),
                )
        return FileSchema()

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
    item_type = u"file"

    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)
        class FileSchema(MappingSchema):
            title = SchemaNode(String(), missing=u'')
            description = SchemaNode(
                String(),
                missing=u"",
                widget=TextAreaWidget(cols=40, rows=5),
                )
            file = SchemaNode(
                FileData(),
                widget=FileUploadWidget(tmpstore),
                )
        return FileSchema()
    
    def save_success(self, appstruct):
        if not appstruct['title']:
            appstruct['title'] = appstruct['file']['filename']
        return super(AddFileFormView, self).save_success(appstruct)

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
        context=File,
        name='view',
        permission='view',
        renderer='kotti:templates/view/file.pt',
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
