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


class IBlobStorage(Interface):
    """ This is the minimal interface that needs to be implemented by file
	storage providers.

	The provider lookup is performed by a "dotted name lookup" from the
	protocol part of the URL in the ``kotti.filestorage`` option.  The
	provider's configuration is taken from the path segment of that URL.

	For example::

		kotti.filestorage = kotti_filestore.filestore:///var/files

	will cause ``kotti_filestore.filestore`` to be instanciated with
	``/var/files`` being passed as its ``config`` upon initialization.

	Because this option is parsed as an URL, your class name must be all
	lower case (scheme part of URLs is not case sensitive).

	See the ``kotti_filestore`` package's documentation for an example. """

    def __init__(config):
	""" The constructor is (optionally) passed a string containing the
	desired configuration options (see above).

	:param config: Configuration string
	:type config: str
	"""

    def read(id):
	""" Get the data for an object with the given ID.

	:param id: ID of the file object
	:type id: unicode

	:result: Data / value of the file object
	:rtype:
	"""

    def write(id, data):
	""" Create or update an object with the given ``id`` and write ``data``
	to its contents.

	:param id: ID of the file object
	:type id: unicode

	:param data: success
	:type data: bool
	"""

    def delete(id):
	""" Delete the object with the given ID.

	:param id: ID of the file object
	:type id: unicode

	:result: Success
	:rtype: bool
	"""
