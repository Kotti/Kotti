from kotti.resources import File

from pyramid.response import Response


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
