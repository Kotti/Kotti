"""
:summary: Default view selctor views
"""

import warnings

from pyramid.compat import map_
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.threadlocal import get_current_registry
from pyramid.view import view_config
from pyramid.view import view_defaults
from zope.interface import providedBy

from kotti.util import _


@view_defaults(permission='edit')
class DefaultViewSelection(object):

    def __init__(self, context, request):

        self.context = context
        self.request = request

    def _get_view(self, view_name):  # pragma: no cover
        """This code is copied from pyramid.view.
           We trust it and don't test.

           Returns True if a view with name view_name is registered for context.
        """
        provides = [IViewClassifier] + map_(
            providedBy,
            (self.request, self.context)
        )

        try:
            reg = self.request.registry
        except AttributeError:
            reg = get_current_registry()

        return reg.adapters.lookup(provides, IView, name=view_name)

    def _is_valid_view(self, view_name):
        """Return True if a view with name view_name is registered for context.
        """

        return self._get_view(view_name) is not None

    @view_config(name='default-view-selector',
                 renderer='kotti:templates/default-view-selector.pt')
    def default_view_selector(self):
        """
        :summary: Submenu for selection of the node's default view.
        :result: Dictionary with a selectable_default_views list.
        :rtype: dict
        """

        sviews = []

        for v in self.context.type_info.selectable_default_views:
            name, title = v
            if self._is_valid_view(name):
                sviews.append({
                    "name": name,
                    "title": title,
                    "is_current": name == self.context.default_view,
                })
            else:
                warnings.warn(
                    u"No view called '{0}' is registered for {1!r}.".format(
                        name, self.context))

        return {
            "selectable_default_views": [
                {
                    "name": "default",
                    "title": _("Default view"),
                    "is_current": self.context.default_view is None,
                }
            ] + sviews,
        }

    @view_config(name='set-default-view')
    def set_default_view(self):
        """
        :summary: Set the node's default view and redirect to it.
        :result: Redirect to the context URL.
        :rtype: pyramid.httpexceptions.HTTPFound
        """

        if 'view_name' in self.request.GET:

            view_name = self.request.GET['view_name']

            if view_name == "default":
                self.context.default_view = None
                self.request.session.flash(
                    _("Default view has been reset to default."),
                    'success'
                )
            else:
                if self._is_valid_view(view_name):
                    self.context.default_view = view_name
                    self.request.session.flash(
                        _("Default view has been set."),
                        'success'
                    )
                else:
                    self.request.session.flash(
                        _("Default view could not be set."),
                        'error'
                    )

        return HTTPFound(
            location=self.request.resource_url(self.context)
        )


def includeme(config):
    config.scan('.default_views')
