# -*- coding: utf-8 -*-
"""

Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.interfaces
"""

from zope.interface import Interface


class INode(Interface):
    """Marker interface for all nodes (and subclasses)"""

    pass


class IContent(INode):
    """Marker interface for all nodes of type Content
       (and subclasses thereof)"""

    pass


class IDocument(IContent):
    """Marker interface for all nodes of type Document
       (and subclasses thereof)"""

    pass


class IFile(IContent):
    """Marker interface for all nodes of type File
       (and subclasses thereof)"""

    pass


class IImage(IFile):
    """Marker interface for all nodes of type Image
       (and subclasses thereof)"""

    pass


class IDefaultWorkflow(Interface):
    """Marker interface for content classes that want to use the
       default workflow"""

    pass
