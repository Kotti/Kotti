# -*- coding: utf-8 -*-
"""
"""

from zope.interface import Interface
from pyramid.interfaces import ILocation


class INode(ILocation):
    """Marker interface for all nodes (and subclasses)"""


class IContent(INode):
    """Marker interface for all nodes of type Content
       (and subclasses thereof)"""


class IDocument(IContent):
    """Marker interface for all nodes of type Document
       (and subclasses thereof)"""


class IFile(IContent):
    """Marker interface for all nodes of type File
       (and subclasses thereof)"""


class IDefaultWorkflow(Interface):
    """Marker interface for content classes that want to use the
       default workflow"""


class INavigationRoot(Interface):
    """Marker interface for content nodes / classes that want to be the root
       for the navigation.

       Considering a content tree like this::

        - /a
          - /a/a
          - /a/b (provides INavigationRoot)
            - /a/b/a
            - /a/b/b
            - /a/b/c
          - a/c

        The root item for the navigation will be ``/a/b`` for everey context in
        or below ``/a/b`` and ``/a`` for every other item.
        """


# DEPRECATED

from kotti_image.interfaces import IImage
from zope.deprecation.deprecation import deprecated
__ = IImage  # pyflakes
deprecated('IImage',
           'Image was outfactored to the kotti_image package.  '
           'Please import from there.')
