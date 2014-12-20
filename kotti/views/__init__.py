# -*- coding: utf-8 -*-

from kotti.views.util import RootOnlyPredicate
from kotti.views.util import SettingHasValuePredicate


class BaseView(object):
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
    config.add_static_view('static-kotti', 'kotti:static')

    # deform stuff
    # config.include('deform_bootstrap')
    config.include('pyramid_deform')
    config.include('js.deform')
    # config.include('js.deform_bootstrap')

    # disable deform CSS autoneeding
    # from js.deform import resource_mapping
    # from js.deform import deform_js
    # resource_mapping['deform'] = deform_js

    config.add_view_predicate(
        'root_only', RootOnlyPredicate)
    config.add_view_predicate(
        'if_setting_has_value', SettingHasValuePredicate)
