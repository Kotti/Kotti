# -*- coding: utf-8 -*-
"""
"""

from zope.interface import Interface


class INode(Interface):
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


class IImage(IFile):
    """Marker interface for all nodes of type Image
       (and subclasses thereof)"""


class IDefaultWorkflow(Interface):
    """Marker interface for content classes that want to use the
       default workflow"""
