# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.response import _BLOCK_SIZE
from pyramid.response import FileIter
from pyramid.response import Response
from pyramid.view import view_config

from kotti.resources import File

import mimetypes


class UploadedFileResponse(Response):
    """
    A Response object that can be used to serve an UploadedFile instance.

    ``data`` is the ``UploadedFile`` file field value.

    ``request`` must be a Pyramid :term:`request` object.  Note
    that a request *must* be passed if the response is meant to attempt to
    use the ``wsgi.file_wrapper`` feature of the web server that you're using
    to serve your Pyramid application.

    ``cache_max_age`` is the number of seconds that should be used
    to HTTP cache this response.

    ``content_type`` is the content_type of the response.

    ``content_encoding`` is the content_encoding of the response.
    It's generally safe to leave this set to ``None`` if you're serving a
    binary file.  This argument will be ignored if you also leave
    ``content-type`` as ``None``.

    Code adapted from pyramid.response.FileResponse
    """
    def __init__(self, data, request=None, disposition='attachment',
                 cache_max_age=None, content_type=None,
                 content_encoding=None):

        if data._public_url:
            raise HTTPMovedPermanently(data._public_url)

        filename = data.filename

        content_type = content_type or getattr(data, 'content_type', None)
        if content_type is None:
            content_type, content_encoding = \
                mimetypes.guess_type(filename, strict=False)

        if content_type is None:
            content_type = 'application/octet-stream'
        # str-ifying content_type is a workaround for a bug in Python 2.7.7
        # on Windows where mimetypes.guess_type returns unicode for the
        # content_type.
        content_type = str(content_type)

        super(UploadedFileResponse, self).__init__(
            conditional_response=True,
            content_type=content_type,
            content_encoding=content_encoding
        )

        self.app_iter = FileIter(data.file, _BLOCK_SIZE)
        # assignment of content_length must come after assignment of app_iter
        self.content_length = data.file.content_length
        self.last_modified = data.file.last_modified
        if cache_max_age is not None:
            self.cache_expires = cache_max_age

        disp = '{0};filename="{1}"'.format(
            disposition, data.filename.encode('ascii', 'ignore'))
        self.headerlist.append(('Content-Disposition', disp))


@view_config(name='view', context=File, permission='view',
             renderer='kotti:templates/view/file.pt')
def view(context, request):
    return {}


@view_config(name='inline-view', context=File, permission='view')
def inline_view(context, request):
    return UploadedFileResponse(context.data, request, disposition='inline')


@view_config(name='attachment-view', context=File, permission='view')
def attachment_view(context, request):
    return UploadedFileResponse(context.data, request, disposition='attachment')


def includeme(config):
    config.scan(__name__)
