# -*- coding: utf-8 -*-

"""
This module contains navigation related views.
"""

from pyramid.view import view_config

from kotti.interfaces import INavigationRoot
from kotti.interfaces import INode
from kotti.resources import get_root
from kotti.views.util import nodes_tree


@view_config(name='render_tree_navigation', permission='view',
             renderer='kotti:templates/edit/nav-tree.pt')
@view_config(name='navigate', permission='view',
             renderer='kotti:templates/edit/nav-tree-view.pt')
def render_tree_navigation(context, request):
    """ Renders the navigation view.

    :result: Dictionary passed to the template for rendering.
    :rtype: dict
    """
    tree = nodes_tree(request)
    return {
        'tree': {
            'children': [tree],
        },
    }


@view_config(name='local-navigation',
             context=INode,
             renderer='kotti:templates/view/nav-local.pt')
def local_navigation(context, request):

    def ch(node):
        return [child for child in node.values()
                if child.in_navigation and
                request.has_permission('view', child)]

    parent = context
    children = ch(context)
    if not children and getattr(context, '__parent__', None) is not None:
        parent = context.__parent__
        children = ch(parent)
    if children and parent != get_root() and not \
       INavigationRoot.providedBy(parent):
        return dict(parent=parent, children=children)
    return dict(parent=None)


def includeme_local_navigation(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    # Import is needed in function scope to resolve circular imports caused by
    # compatibility imports in slots.py.
    from kotti.views.slots import assign_slot
    config.scan(__name__)
    assign_slot('local-navigation', 'right')


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.scan(__name__)
