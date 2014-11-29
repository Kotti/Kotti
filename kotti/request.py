# -*- coding: utf-8 -*-

import pyramid.request
from pyramid.decorator import reify


class Request(pyramid.request.Request):
    """docstring for Request"""

    @reify
    def user(self):
        """ Add the authenticated user to the request object.

        :result: the currently authenticated user
        :rtype: :class:`kotti.security.Principal` or whatever is returned by
                the custom principals database defined in the
                ``kotti.principals_factory`` setting
        """

        from kotti.security import get_user
        return get_user(self)

    # def has_permission(self, permission, context=None):
    #     """ Check if the current request has the given permission on the
    #     current or explicitly passed context.  This is different from
    #     :meth:`pyramid.request.Request.has_permission`` in that a context other
    #     than the one bound to the request can be passed.  This allows to
    #     consider local roles for the check.

    #     :param permission: name of the permission to check
    #     :type permission: str

    #     :param context: context for which the permission is checked.
    #                     Defaults to the context on which the request invoked.
    #     :type context: :class:`kotti.resources.Node`

    #     :result: True if has_permission, False else
    #     :rtype: bool
    #     """

    #     from kotti.security import authz_context

    #     with authz_context(context, self):
    #         return super(pyramid.request.Request, self).has_permission(
    #             permission)