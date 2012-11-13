from kotti.resources import File

from pyramid.response import Response
from pyramid.view import view_config
from zope.deprecation.deprecation import deprecated


@view_config(name='view', context=File, permission='view',
             renderer='kotti:templates/view/file.pt')
def view(context, request):
    return {}


@view_config(name='inline-view', context=File,
             permission='view')
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


@view_config(name='attachment-view', context=File,
             permission='view')
def attachment_view(context, request):
    return inline_view(context, request, 'attachment')


def includeme(config):
    config.scan(__name__)


# BBB
from .edit.content import FileAddForm as AddFileFormView
from .edit.content import ImageAddForm as AddImageFormView
from .edit.content import FileEditForm as EditFileFormView
from .edit.content import ImageEditForm as EditImageFormView

for cls in (
    AddFileFormView, AddImageFormView, EditFileFormView, EditImageFormView,
    ):
    deprecated(cls, """\
%s has been renamed (e.g. 'FileAddForm' became 'AddFileFormView') and moved to
kottiv.views.edit.content as of Kotti 0.8.""" % cls.__name__)
