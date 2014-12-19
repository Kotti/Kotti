# -*- coding: utf-8 -*-

from pyramid.response import Response
from pyramid.view import view_config

from kotti.resources import File


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
