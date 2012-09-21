from colander import Invalid
from colander import null
from colander import SchemaNode
from deform import FileData
from deform.widget import FileUploadWidget
from kotti import get_settings
from kotti.resources import File
from kotti.util import _
from kotti.views.form import AddFormView
from kotti.views.form import ContentSchema
from kotti.views.form import EditFormView
from pyramid.response import Response
from StringIO import StringIO
from UserDict import DictMixin


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
                disposition, context.filename.encode('ascii', 'ignore'))),
            ('Content-Type', str(context.mimetype)),
            ]
        )
    res.body = context.data
    return res


def attachment_view(context, request):
    return inline_view(context, request, 'attachment')


def validate_file_size_limit(node, value):
    value['fp'].seek(0, 2)
    size = value['fp'].tell()
    value['fp'].seek(0)
    max_size = get_settings()['kotti.max_file_size']
    if size > int(max_size) * 1024 * 1024:
        msg = _('Maximum file size: ${size}MB', mapping={'size': max_size})
        raise Invalid(node, msg)


class EditFileFormView(EditFormView):
    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)

        class FileSchema(ContentSchema):
            file = SchemaNode(
                FileData(),
                title=_(u'File'),
                missing=null,
                widget=FileUploadWidget(tmpstore),
                validator=validate_file_size_limit,
                )
        return FileSchema()

    def edit(self, **appstruct):
        self.context.title = appstruct['title']
        self.context.description = appstruct['description']
        self.context.tags = appstruct['tags']
        if appstruct['file']:
            buf = appstruct['file']['fp'].read()
            self.context.data = buf
            self.context.filename = appstruct['file']['filename']
            self.context.mimetype = appstruct['file']['mimetype']
            self.context.size = len(buf)


def set_title_missing(node, kw):
    if 'title_missing' in kw:
        node['title'].missing = kw['title_missing']


class AddFileFormView(AddFormView):
    item_type = _(u"File")
    item_class = File

    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)

        class FileSchema(ContentSchema):
            file = SchemaNode(
                FileData(),
                title=_(u'File'),
                widget=FileUploadWidget(tmpstore),
                validator=validate_file_size_limit,
                )
        file_schema = FileSchema(after_bind=set_title_missing)
        return file_schema.bind(title_missing=u'')

    def save_success(self, appstruct):
        if not appstruct['title']:
            appstruct['title'] = appstruct['file']['filename']
        return super(AddFileFormView, self).save_success(appstruct)

    def add(self, **appstruct):
        buf = appstruct['file']['fp'].read()
        return self.item_class(
            title=appstruct['title'],
            description=appstruct['description'],
            tags=appstruct['tags'],
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
