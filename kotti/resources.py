"""
The :mod:`~kotti.resources` module contains all the classes for Kotti's
persistence layer, which is based on SQLAlchemy.

Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.resources
"""
import datetime
from cgi import FieldStorage
from collections import MutableMapping
from typing import Any
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

import abc
import os
import warnings
from copy import copy
from depot.fields.sqlalchemy import UploadedFileField
from depot.fields.sqlalchemy import _SQLAMutationTracker
from depot.fields.upload import UploadedFile
from fnmatch import fnmatch
from io import BufferedReader
from io import BytesIO
from pyramid.decorator import reify
from pyramid.traversal import resource_path
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import UniqueConstraint
from sqlalchemy import bindparam
from sqlalchemy import event
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.orderinglist import OrderingList
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relation
from sqlalchemy.orm.attributes import Event
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.sql import and_
from sqlalchemy.sql import select
from sqlalchemy.util import classproperty
from sqlalchemy.util.langhelpers import _symbol
from transaction import commit
from zope.interface import implementer

from kotti import Base
from kotti import DBSession
from kotti import TRUE_VALUES
from kotti import _resolve_dotted
from kotti import get_settings
from kotti import metadata
from kotti.interfaces import IContent
from kotti.interfaces import IDefaultWorkflow
from kotti.interfaces import IDocument
from kotti.interfaces import IFile
from kotti.interfaces import INode
from kotti.migrate import stamp_heads
from kotti.request import Request
from kotti.security import PersistentACLMixin
from kotti.security import view_permitted
from kotti.sqla import ACLType
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from kotti.sqla import NestedMutationDict
from kotti.sqla import bakery
from kotti.util import Link
from kotti.util import LinkParent
from kotti.util import LinkRenderer
from kotti.util import _
from kotti.util import _to_fieldstorage
from kotti.util import camel_case_to_name
from kotti.util import get_paste_items


class ContainerMixin(MutableMapping):
    """ Containers form the API of a Node that's used for subitem
    access and in traversal.
    """

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.keys())

    def __setitem__(self, key: str, node: 'Node') -> None:
        node.name = key
        self.children.append(node)
        self.children.reorder()

    def __delitem__(self, key: str) -> None:
        node = self[key]
        self.children.remove(node)
        DBSession.delete(node)

    def keys(self) -> List[str]:
        """
        :result: children names
        :rtype: list
        """

        return [child.name for child in self.children]

    def values(self) -> OrderingList:
        return self.children

    def __getitem__(self, path: Union[str, Iterable[str]]) -> 'Node':
        db_session = DBSession()
        db_session._autoflush()

        # if not hasattr(path, '__iter__'):
        if isinstance(path, str):
            path = (path,)
        path = [p for p in path]

        # Optimization: don't query children if self._children already there:
        if '_children' in self.__dict__:
            rest = path[1:]
            try:
                [child] = filter(lambda ch: ch.name == path[0], self._children)
            except ValueError:
                raise KeyError(path)
            if rest:
                return child[rest]
            else:
                return child

        baked_query = bakery(lambda session: session.query(Node))

        if len(path) == 1:
            try:
                baked_query += lambda q: q.filter(
                    Node.name == bindparam('name'),
                    Node.parent_id == bindparam('parent_id')
                )
                return baked_query(db_session).params(
                    name=path[0], parent_id=self.id).one()
            except NoResultFound:
                raise KeyError(path)

        # We have a path with more than one element, so let's be a
        # little clever about fetching the requested node:
        nodes = Node.__table__
        conditions = [nodes.c.id == self.id]
        alias = nodes
        for name in path:
            alias, old_alias = nodes.alias(), alias
            conditions.append(alias.c.parent_id == old_alias.c.id)
            conditions.append(alias.c.name == name)
        expr = select([alias.c.id], and_(*conditions))
        row = db_session.execute(expr).fetchone()
        if row is None:
            raise KeyError(path)
        return baked_query(db_session).get(row.id)

    @hybrid_property
    def children(self):
        """
        :result: *all* child nodes without considering permissions.
        :rtype: list
        """

        return self._children

    def children_with_permission(self,
                                 request: Request,
                                 permission: str = 'view') -> 'List[Node]':
        """ Return only those children for which the user initiating the
        request has the asked permission.

        :param request: current request
        :type request: :class:`kotti.request.Request`

        :param permission: The permission for which you want the allowed
                           children
        :type permission: str

        :result: List of child nodes
        :rtype: list
        """

        return [
            c for c in self.children
            if request.has_permission(permission, c)
        ]


class LocalGroup(Base):
    """ Local groups allow the assignment of groups or roles to principals
    (users or groups) **for a certain context** (i.e. a :class:`Node` in the
    content tree).
    """

    __tablename__ = 'local_groups'
    __table_args__ = (
        UniqueConstraint('node_id', 'principal_name', 'group_name'),
        )

    #: Primary key for the node in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), primary_key=True)
    #: ID of the node for this assignment
    #: (:class:`sqlalchemy.types.Integer`)
    node_id = Column(ForeignKey('nodes.id'), index=True)
    #: Name of the principal (user or group)
    #: (:class:`sqlalchemy.types.Unicode`)
    principal_name = Column(Unicode(100), index=True)
    #: Name of the assigned group or role
    #: (:class:`sqlalchemy.types.Unicode`)
    group_name = Column(Unicode(100))

    def __init__(self, node: 'Node', principal_name: str, group_name: str):
        self.node = node
        self.principal_name = principal_name
        self.group_name = group_name

    def copy(self, **kwargs) -> 'LocalGroup':
        kwargs.setdefault('node', self.node)
        kwargs.setdefault('principal_name', self.principal_name)
        kwargs.setdefault('group_name', self.group_name)

        return self.__class__(**kwargs)

    def __repr__(self):
        return '<{0} {1} => {2} at {3}>'.format(
            self.__class__.__name__, self.principal_name, self.group_name,
            resource_path(self.node))


class NodeMeta(DeclarativeMeta, abc.ABCMeta):
    """ """


@implementer(INode)
class Node(Base, ContainerMixin, PersistentACLMixin, metaclass=NodeMeta):
    """Basic node in the persistance hierarchy.
    """

    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
        )
    __mapper_args__ = dict(
        polymorphic_on='type',
        polymorphic_identity='node',
        with_polymorphic='*',
        )

    #: Primary key for the node in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), primary_key=True)
    #: Lowercase class name of the node instance
    #: (:class:`sqlalchemy.types.String`)
    type = Column(String(30), nullable=False)
    #: ID of the node's parent
    #: (:class:`sqlalchemy.types.Integer`)
    parent_id = Column(ForeignKey('nodes.id'), index=True)
    #: Position of the node within its container / parent
    #: (:class:`sqlalchemy.types.Integer`)
    position = Column(Integer())
    _acl = Column(MutationList.as_mutable(ACLType))
    #: Name of the node as used in the URL
    #: (:class:`sqlalchemy.types.Unicode`)
    name = Column(Unicode(250), nullable=False)
    #: Title of the node, e.g. as shown in search results
    #: (:class:`sqlalchemy.types.Unicode`)
    title = Column(Unicode(250))
    #: Annotations can be used to store arbitrary data in a nested dictionary
    #: (:class:`kotti.sqla.NestedMustationDict`)
    annotations = Column(NestedMutationDict.as_mutable(JsonType))
    #: The path can be used to efficiently filter for child objects
    #: (:class:`sqlalchemy.types.Unicode`).
    path = Column(Unicode(2000), index=True)

    parent = relation(
        'Node',
        remote_side=[id],
        backref=backref(
            '_children',
            collection_class=ordering_list('position', reorder_on_append=True),
            order_by=[position],
            cascade='all',
        )
    )

    local_groups = relation(
        LocalGroup,
        backref=backref('node'),
        cascade='all',
        lazy='joined',
    )

    __hash__ = Base.__hash__

    def __init__(self,
                 name: str = None,
                 parent: 'Node' = None,
                 title: str = '',
                 annotations: dict = None,
                 **kwargs):
        """Constructor"""

        super(Node, self).__init__(**kwargs)

        if annotations is None:
            annotations = {}
        self.parent = parent
        self.name = name
        self.title = title
        self.annotations = annotations

    @property
    def __name__(self):
        return self.name

    @property
    def __parent__(self):
        return self.parent

    @__parent__.setter
    def __parent__(self, value):
        self.parent = value

    def __repr__(self) -> str:
        return '<{0} {1} at {2}>'.format(
            self.__class__.__name__, self.id, resource_path(self))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Node) and self.id == other.id

    def __ne__(self, other: Any) -> bool:
        return not self == other

    copy_properties_blacklist = (
        'id', 'parent', 'parent_id', '_children', 'local_groups', '_tags')

    def clear(self) -> None:

        DBSession.query(Node).filter(Node.parent == self).delete()

    def copy(self, **kwargs) -> 'Node':
        """
        :result: A copy of the current instance
        :rtype: :class:`~kotti.resources.Node`
        """

        children = list(self.children)
        copy = self.__class__()
        for prop in object_mapper(self).iterate_properties:
            if prop.key not in self.copy_properties_blacklist:
                setattr(copy, prop.key, getattr(self, prop.key))
        for key, value in kwargs.items():
            setattr(copy, key, value)
        for child in children:
            copy.children.append(child.copy())

        return copy


class TypeInfo(object):
    """TypeInfo instances contain information about the type of a node.

       You can pass arbitrary keyword arguments in the constructor, they
       will become instance attributes.  The most common are:

            -   name
            -   title
            -   add_view
            -   addable_to
            -   edit_links
            -   selectable_default_views
            -   uploadable_mimetypes
            -   add_permission
    """

    addable_to = ()
    selectable_default_views = ()
    uploadable_mimetypes = ()
    edit_links = ()
    action_links = ()  # BBB

    def __init__(self, **kwargs) -> None:
        if 'action_links' in kwargs:
            msg = ("'action_links' is deprecated as of Kotti 1.0.0.  "
                   "'edit_links' includes 'action_links' and should "
                   "be used instead.")

            edit_links = kwargs.get('edit_links')
            last_link = edit_links[-1] if edit_links else None
            if isinstance(last_link, LinkParent):
                last_link.children.extend(kwargs['action_links'])
                warnings.warn(msg, DeprecationWarning)
            else:
                raise ValueError(msg)

        # default value for add_permission should be 'add'
        if 'add_permission' not in kwargs:
            kwargs['add_permission'] = 'add'

        self.__dict__.update(kwargs)

    def copy(self, **kwargs) -> 'TypeInfo':
        """

        :result: a copy of the current TypeInfo instance
        :rtype: :class:`~kotti.resources.TypeInfo`
        """

        d = self.__dict__.copy()
        d['selectable_default_views'] = copy(self.selectable_default_views)
        d.update(kwargs)

        return TypeInfo(**d)

    def addable(self,
                context: 'Content',
                request: Optional[Request]) -> bool:
        """

        :param context:
        :type context: Content or subclass thereof (or anything that has a
                       type_info attribute of type
                       :class:`~kotti.resources.TypeInfo`)

        :param request: current request
        :type request: :class:`kotti.request.Request`

        :result: True if the type described in 'self' may be added to 'context',
                 False otherwise.
        :rtype: Boolean
        """

        if self.add_view is None:
            return False
        if context.type_info.name in self.addable_to:
            return bool(view_permitted(context, request, self.add_view))
        else:
            return False

    def add_selectable_default_view(self, name: str, title: str) -> None:
        """Add a view to the list of default views selectable by the
        user in the UI.

        :param name: Name the view is registered with
        :type name: str

        :param title: Title for the view for display in the UI.
        :type title: str or TranslationString
        """
        self.selectable_default_views.append((name, title))

    def is_uploadable_mimetype(self, mimetype: str) -> int:
        """ Check if uploads of the given MIME type are allowed.

        :param mimetype: MIME type
        :type mimetype: str

        :result: Upload allowed (>0) or forbidden (0).  The greater the result,
                 the better is the match.  E.g. ``image/*`` (6) is a better
                 match for ``image/png`` than `*` (1).
        :rtype: int
        """

        match_score = 0

        for mt in self.uploadable_mimetypes:
            if fnmatch(mimetype, mt) and len(mt) > match_score:
                match_score = len(mt)

        return match_score


class Tag(Base):
    """Basic tag implementation.  Instances of this class are just the tag
    itself and can be mapped to instances of :class:`~kotti.resources.Content`
    (or any of its descendants) via instances of
    :class:`~kotti.resources.TagsToContents`.
    """

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer, primary_key=True)

    #: Title of the tag
    #: :class:`sqlalchemy.types.Unicode`
    title = Column(Unicode(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return "<Tag ('{0}')>".format(self.title)

    @property
    def items(self) -> List[Node]:
        """

        :result:
        :rtype: list
        """

        return [rel.item for rel in self.content_tags]


class TagsToContents(Base):
    """Tags to contents mapping
    """

    __tablename__ = 'tags_to_contents'

    #: Foreign key referencing :attr:`Tag.id`
    #: (:class:`sqlalchemy.types.Integer`)
    tag_id = Column(ForeignKey('tags.id'), primary_key=True, index=True)
    #: Foreign key referencing :attr:`Content.id`
    #: (:class:`sqlalchemy.types.Integer`)
    content_id = Column(ForeignKey('contents.id'), primary_key=True, index=True)
    #: Relation that adds a ``content_tags`` :func:`sqlalchemy.orm.backref`
    #: to :class:`~kotti.resources.Tag` instances to allow easy access to all
    #: content tagged with that tag.
    #: (:func:`sqlalchemy.orm.relationship`)
    tag = relation(Tag, backref=backref('content_tags', cascade='all'),
                   lazy='joined',)
    #: Ordering position of the tag
    #: :class:`sqlalchemy.types.Integer`
    position = Column(Integer, nullable=False)
    #: title of the associated :class:`~kotti.resources.Tag` instance
    #: (:class:`sqlalchemy.ext.associationproxy.association_proxy`)
    title = association_proxy('tag', 'title')

    @classmethod
    def _tag_find_or_create(cls, title: str) -> 'TagsToContents':
        """
        Find or create a tag with the given title.

        :param title: Title of the tag to find or create.
        :type title: str
        :result:
        :rtype: :class:`~kotti.resources.TagsToContents`
        """

        with DBSession.no_autoflush:
            tag = DBSession.query(Tag).filter_by(title=title).first()
        if tag is None:
            tag = Tag(title=title)
        return cls(tag=tag)


# noinspection PyUnusedLocal
def _not_root(context: Node, request: Request) -> bool:
    return context is not get_root()


default_actions = [
    Link('copy', title=_('Copy')),
    Link('cut', title=_('Cut'), predicate=_not_root),
    Link('paste', title=_('Paste'), predicate=get_paste_items),
    Link('rename', title=_('Rename'), predicate=_not_root),
    Link('delete', title=_('Delete'), predicate=_not_root),
    LinkRenderer('default-view-selector'),
]


default_type_info = TypeInfo(
    name='Content',
    title='type_info title missing',   # BBB
    add_view=None,
    addable_to=[],
    edit_links=[
        Link('contents', title=_('Contents')),
        Link('edit', title=_('Edit')),
        Link('share', title=_('Share')),
        LinkParent(title=_('Actions'), children=default_actions),
        ],
    selectable_default_views=[
        ("folder_view", _("Folder view")),
        ],
    )


@implementer(IContent)
class Content(Node):
    """Content adds some attributes to :class:`~kotti.resources.Node` that are
       useful for content objects in a CMS.
    """

    @classproperty
    def __mapper_args__(cls):
        return dict(polymorphic_identity=camel_case_to_name(cls.__name__))

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(ForeignKey(Node.id), primary_key=True)
    #: Name of the view that should be displayed to the user when
    #: visiting an URL without a explicit view name appended
    #: (:class:`sqlalchemy.types.String`)
    default_view = Column(String(50))
    #: Description of the content object.  In default Kotti this is
    #: used e.g. in the description tag in the HTML, in the search results
    #: and rendered below the title in most views.
    #: (:class:`sqlalchemy.types.Unicode`)
    description = Column(UnicodeText())
    #: Language code (ISO 639) of the content object
    #: (:class:`sqlalchemy.types.Unicode`)
    language = Column(Unicode(10))
    #: Owner (username) of the content object
    #: (:class:`sqlalchemy.types.Unicode`)
    owner = Column(Unicode(100))
    #: Workflow state of the content object
    #: (:class:`sqlalchemy.types.String`)
    state = Column(String(50))
    #: Date / time the content was created
    #: (:class:`sqlalchemy.types.DateTime`)
    creation_date = Column(DateTime())
    #: Date / time the content was last modified
    #: (:class:`sqlalchemy.types.DateTime`)
    modification_date = Column(DateTime())
    #: Shall the content be visible in the navigation?
    #: (:class:`sqlalchemy.types.Boolean`)
    in_navigation = Column(Boolean())
    _tags = relation(
        TagsToContents,
        backref=backref('item'),
        lazy='joined',
        order_by=[TagsToContents.position],
        collection_class=ordering_list("position"),
        cascade='all, delete-orphan',
        )
    #: Tags assigned to the content object (list of str)
    tags = association_proxy(
        '_tags',
        'title',
        creator=TagsToContents._tag_find_or_create,
        )
    #: type_info is a class attribute (:class:`TypeInfo`)
    type_info = default_type_info

    def __init__(self,
                 name: Optional[str] = None,
                 parent: Optional[Node] = None,
                 title: Optional[str] = '',
                 annotations: Optional[dict] = None,
                 default_view: Optional[str] = None,
                 description: Optional[str] = '',
                 language: Optional[str] = None,
                 owner: Optional[str] = None,
                 creation_date: Optional[datetime.datetime] = None,
                 modification_date: Optional[datetime.datetime] = None,
                 in_navigation: Optional[bool] = True,
                 tags: Optional[List[str]] = None,
                 **kwargs):

        super(Content, self).__init__(
            name, parent, title, annotations, **kwargs)

        self.default_view = default_view
        self.description = description
        self.language = language
        self.owner = owner
        self.in_navigation = in_navigation
        # These are set by events if not defined at this point:
        self.creation_date = creation_date
        self.modification_date = modification_date
        self.tags = tags or []

    def copy(self, **kwargs) -> 'Content':
        # Same as `Node.copy` with additional tag support.
        kwargs['tags'] = self.tags
        return super(Content, self).copy(**kwargs)


@implementer(IDocument, IDefaultWorkflow)
class Document(Content):
    """Document extends :class:`~kotti.resources.Content` with a body and its
       mime_type.  In addition Document and its descendants implement
       :class:`~kotti.interfaces.IDefaultWorkflow` and therefore
       are associated with the default workflow (at least in
       unmodified Kotti installations).
    """

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(ForeignKey(Content.id), primary_key=True)
    #: Body text of the Document
    #: (:class:`sqlalchemy.types.Unicode`)
    body = Column(UnicodeText())
    #: MIME type of the Document
    #: (:class:`sqlalchemy.types.String`)
    mime_type = Column(String(30))

    #: type_info is a class attribute
    #: (:class:`~kotti.resources.TypeInfo`)
    type_info = Content.type_info.copy(
        name='Document',
        title=_('Document'),
        add_view='add_document',
        addable_to=['Document'],
        )

    def __init__(self,
                 body: Optional[str] = '',
                 mime_type: Optional[str] = 'text/html',
                 **kwargs):

        super(Document, self).__init__(**kwargs)

        self.body = body
        self.mime_type = mime_type


# noinspection PyMethodParameters
class SaveDataMixin(object):
    """ The classmethods must not be implemented on a class that inherits
        from ``Base`` with ``SQLAlchemy>=1.0``, otherwise that class cannot be
        subclassed further.

        See http://stackoverflow.com/questions/30433960/how-to-use-declare-last-in-sqlalchemy-1-0  # noqa
    """

    #: The filename is used in the attachment view to give downloads
    #: the original filename it had when it was uploaded.
    #: (:class:`sqlalchemy.types.Unicode`)
    filename = Column(Unicode(100))
    #: MIME type of the file
    #: (:class:`sqlalchemy.types.String`)
    mimetype = Column(String(100))
    #: Size of the file in bytes
    #: (:class:`sqlalchemy.types.Integer`)
    size = Column(Integer())

    #: Filedepot mapped blob
    #: (:class:`depot.fileds.sqlalchemy.UploadedFileField`)
    @declared_attr
    def data(cls) -> Column:
        return cls.__table__.c.get('data',
                                   Column(UploadedFileField(cls.data_filters)))
    data_filters = ()

    @classmethod
    def __declare_last__(cls) -> None:
        """ Unconfigure the event set in _SQLAMutationTracker,
        we have _save_data """

        mapper = cls._sa_class_manager.mapper
        args = (mapper.attrs['data'], 'set', _SQLAMutationTracker._field_set)
        if event.contains(*args):
            event.remove(*args)

        # Declaring the event on the class attribute instead of mapper property
        # enables proper registration on its subclasses
        event.listen(cls.data, 'set', cls._save_data, retval=True)

    @staticmethod
    def _save_data(target: 'File',
                   value: Optional[Union[FieldStorage, bytes, UploadedFile, BufferedReader]],  # noqa
                   oldvalue: Optional[Union[UploadedFile, _symbol]],
                   initiator: Event) -> Optional[UploadedFile]:
        """ Refresh metadata and save the binary data to the data field.

        :param target: The File instance
        :type target: :class:`kotti.resources.File` or subclass

        :param value: The container for binary data
        :type value: A :class:`cgi.FieldStorage` instance
        """

        if isinstance(value, bytes):
            fp = BytesIO(value)
            value = _to_fieldstorage(fp=fp,
                                     filename=target.filename,
                                     mimetype=target.mimetype,
                                     size=len(value))

        newvalue = _SQLAMutationTracker._field_set(
            target, value, oldvalue, initiator)

        if newvalue is None:
            return

        target.filename = newvalue.filename
        target.mimetype = newvalue.content_type
        target.size = newvalue.file.content_length

        return newvalue

    @classmethod
    def from_field_storage(cls, fs):
        """ Create and return an instance of this class from a file upload
            through a webbrowser.

        :param fs: FieldStorage instance as found in a
                   :class:`kotti.request.Request`'s ``POST`` MultiDict.
        :type fs: :class:`cgi.FieldStorage`

        :result: The created instance.
        :rtype: :class:`kotti.resources.File`
        """

        if not cls.type_info.is_uploadable_mimetype(fs.type):
            raise ValueError("Unsupported MIME type: {0}".format(fs.type))

        return cls(data=fs)

    def __init__(self,
                 data: Optional[Union[bytes, BufferedReader, FieldStorage]]=None,  # noqa
                 filename: Optional[str] = None,
                 mimetype: Optional[str] = None,
                 size: Optional[int] = None,
                 **kwargs) -> None:

        super(SaveDataMixin, self).__init__(**kwargs)

        self.filename = filename
        self.mimetype = mimetype
        self.size = size
        self.data = data

    def copy(self, **kwargs) -> 'File':
        """ Same as `Content.copy` with additional data support.  ``data`` needs
        some special attention, because we don't want the same depot file to be
        assigned to multiple content nodes.
        """
        _copy = super(SaveDataMixin, self).copy(**kwargs)
        _copy.data = self.data.file.read()
        return _copy


@implementer(IFile)
class File(SaveDataMixin, Content):
    """File adds some attributes to :class:`~kotti.resources.Content` that are
       useful for storing binary data.
    """

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(ForeignKey(Content.id), primary_key=True)

    type_info = Content.type_info.copy(
        name='File',
        title=_('File'),
        add_view='add_file',
        addable_to=['Document'],
        selectable_default_views=[],
        uploadable_mimetypes=['*', ],
        )


def get_root(request: Optional[Request] = None) -> Node:
    """Call the function defined by the ``kotti.root_factory`` setting and
       return its result.

    :param request: current request (optional)
    :type request: :class:`kotti.request.Request`

    :result: a node in the node tree
    :rtype: :class:`~kotti.resources.Node` or descendant;
    """
    return get_settings()['kotti.root_factory'][0](request)


class DefaultRootCache(object):
    """ Default implementation for :func:`~kotti.resources.get_root` """
    _id = None

    # noinspection PyComparisonWithNone,PyPep8
    @reify
    def root_id(self) -> int:
        """ Query for the one node without a parent and return its id.
        :result: The root node's id.
        :rtype: int
        """

        query = bakery(lambda session: session.query(Node)
                       .with_polymorphic(Node).add_columns(Node.id)
                       .enable_eagerloads(False).filter(Node.parent_id == None))

        return query(DBSession()).one().id

    def get_root(self) -> Node:
        """ Query for the root node by its id.  This enables SQLAlchemy's
        session cache (query is executed only once per session).
        :result: The root node.
        :rtype: :class:`Node`.
        """

        return Node.query.get(self.root_id)

    def __call__(self, request: Optional[Request] = None) -> Node:
        """ Default implementation for :func:`~kotti.resources.get_root`
        :param request: Current request (optional)
        :type request: :class:`kotti.request.Request`
        :result: Node in the object tree that has no parent.
        :rtype: :class:`~kotti.resources.Node` or descendant;
                in a fresh Kotti site with Kotti's
                :func:`default populator <kotti.populate.populate>` this will
                be an instance of :class:`~kotti.resources.Document`.
        """

        return self.get_root()


default_get_root = DefaultRootCache()


def _adjust_for_engine(engine: Engine) -> None:
    if engine.dialect.name == 'mysql':  # pragma: no cover
        # We disable the Node.path index for Mysql; in some conditions
        # the index can't be created for columns even with 767 bytes,
        # the maximum default size for column indexes
        Node.__table__.indexes = set(
            index for index in Node.__table__.indexes
            if index.name != "ix_nodes_path")


def initialize_sql(engine: Engine, drop_all: bool = False) -> scoped_session:
    DBSession.registry.clear()
    DBSession.configure(bind=engine)
    metadata.bind = engine

    if drop_all or os.environ.get('KOTTI_TEST_DB_STRING'):
        metadata.reflect()
        metadata.drop_all(engine)

    # Allow users of Kotti to cherry pick the tables that they want to use:
    settings = _resolve_dotted(get_settings())
    tables = settings['kotti.use_tables'].strip() or None
    if tables:
        tables = [metadata.tables[name] for name in tables.split()]

    _adjust_for_engine(engine)

    # Allow migrations to set the 'head' stamp in case the database is
    # initialized freshly:
    if not engine.table_names():
        stamp_heads()

    metadata.create_all(engine, tables=tables)
    if os.environ.get('KOTTI_DISABLE_POPULATORS', '0') not in TRUE_VALUES:
        for populate in settings['kotti.populators']:
            populate()
    commit()

    return DBSession
