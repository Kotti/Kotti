from pyramid.view import view_config

from kotti.interfaces import IFile


@view_config(
    name="view",
    context=IFile,
    permission="view",
    renderer="kotti:templates/view/file.pt",
)
def view(context, request):
    return {}


@view_config(name="inline-view", context=IFile, permission="view")
def inline_view(context, request):
    return request.uploaded_file_response(context.data)


@view_config(name="attachment-view", context=IFile, permission="view")
def attachment_view(context, request):
    return request.uploaded_file_response(context.data, "attachment")


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.scan(__name__)
