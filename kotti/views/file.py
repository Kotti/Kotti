# -*- coding: utf-8 -*-

from pyramid.view import view_config

from kotti.interfaces import IFile


@view_config(name='view', context=IFile, permission='view',
             renderer='kotti:templates/view/file.pt')
def view(context, request):
    return {}


@view_config(name='inline-view', context=IFile, permission='view')
def inline_view(context, request):
    return request.uploaded_file_response(context.data)


@view_config(name='attachment-view', context=IFile, permission='view')
def attachment_view(context, request):
    return request.uploaded_file_response(context.data, 'attachment')


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.scan(__name__)


# DEPRECATED

# noinspection PyPep8
from zope.deprecation.deprecation import deprecated
# noinspection PyPep8
from kotti.filedepot import StoredFileResponse


class UploadedFileResponse(StoredFileResponse):
    def __init__(self, data, request, disposition='attachment',
                 cache_max_age=None, content_type=None,
                 content_encoding=None):
        super(UploadedFileResponse, self).__init__(
            data.file, request, disposition=disposition,
            cache_max_age=cache_max_age, content_type=content_type,
            content_encoding=content_encoding)

deprecated('UploadedFileResponse',
           'UploadedFileResponse is deprecated and will be removed in '
           'Kotti 2.0.0.  Use "request.uploaded_file_response(context.data)" '
           'instead.')
