class BaseView:
    """ Very basic view class that can be subclassed.  Does nothing more than
    assignment of ``context`` and ``request`` to instance attributes on
    initialization. """

    def __init__(self, context, request):
        """ Constructor

        :param context: Context of the view
        :type context: :class:`kotti.resources.Node` or descendant for views on
                       content.

        :param request: Current request object
        :type request: :class:`kotti.request.Request`
        """

        self.context = context
        self.request = request


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.add_static_view("static-kotti", "kotti:static")

    config.include("pyramid_deform")
    config.include("js.deform")

    config.include("kotti.views.util")
