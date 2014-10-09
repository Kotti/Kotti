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
	provider will be passed the complete URL upon initialization.  This
	can be used by implementations for their configuration

	For example::

		kotti.filestorage = kotti_filestore.filestore:///var/files

	will cause ``kotti_filestore.filestore`` to be instanciated with
	``kotti_filestore.filestore:///var/files`` being passed as the URL upon
	initialization.

	Because this option is parsed as an URL, your class name must be all
	lower case (scheme part of URLs is not case sensitive).

	See the ``kotti_filestore`` package's documentation for an example. """

    def __init__(url):
	""" The constructor is passed an already parsed URL containing the
	desired configuration options (see above).

	:param url: URL from the PasteDeploy config file
	:type url: :class:`yurl.URL`
	"""

    def read(id):
	""" Get the data for an object with the given ID.

	:param id: ID of the file object
	:type id: unicode

	:result: Data / value of the file object
	:rtype: bytes
	"""

    def write(data):
	""" Create an object with the given ``data`` as its contents.
	Delete all previous contents that might already have existed.

	:param data: Data / value to store
	:type data: unicode

	:result: ID of the data bucket that can be used for future calls to read
	:rtype: bytes
	"""

    def delete(id):
	""" Delete the object with the given ID.

	:param id: ID of the file object
	:type id: unicode

	:result: Success
	:rtype: bool
	"""
