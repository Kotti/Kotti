"""
The :mod:`~kotti.resources` module contains all the classes for Kotti's
persistance layer, which is based on SQLAlchemy.

Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.resources
"""

import os
from UserDict import DictMixin
from fnmatch import fnmatch

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import backref
from sqlalchemy.orm import deferred
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relation
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from sqlalchemy.sql import select
from sqlalchemy.util import classproperty
from transaction import commit
from zope.deprecation.deprecation import deprecated
from zope.interface import implements

from kotti import Base
from kotti import DBSession
from kotti import get_settings
from kotti import metadata
from kotti.interfaces import INode
from kotti.interfaces import IContent
from kotti.interfaces import IDocument
from kotti.interfaces import IFile
from kotti.interfaces import IImage
from kotti.interfaces import IDefaultWorkflow
from kotti.migrate import stamp_heads
from kotti.security import PersistentACLMixin
from kotti.security import has_permission
from kotti.security import view_permitted
from kotti.sqla import ACLType
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from kotti.sqla import NestedMutationDict
from kotti.util import ViewLink
from kotti.util import _
from kotti.util import camel_case_to_name
from kotti.util import get_paste_items


class ContainerMixin(object, DictMixin):
    """Containers form the API of a Node that's used for subitem
    access and in traversal.
    """

    def __setitem__(self, key, node):
        key = node.name = unicode(key)
        self.children.append(node)

    def __delitem__(self, key):
        node = self[unicode(key)]
        self.children.remove(node)
        DBSession.delete(node)

    def keys(self):
        """
        :result: A list of children names.
        :rtype: list
        """

        return [child.name for child in self.children]

    def __getitem__(self, path):
        DBSession()._autoflush()

        if not hasattr(path, '__iter__'):
            path = (path,)
        path = [unicode(p) for p in path]

        # Optimization: don't query children if self._children already there:
        if '_children' in self.__dict__:
            first, rest = path[0], path[1:]
            try:
                [child] = filter(lambda ch: ch.name == path[0], self._children)
            except ValueError:
                raise KeyError(path)
            if rest:
                return child[rest]
            else:
                return child

        if len(path) == 1:
            try:
                return DBSession.query(Node).filter_by(
                    name=path[0], parent=self).one()
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
        row = DBSession.execute(expr).fetchone()
        if row is None:
            raise KeyError(path)
        return DBSession.query(Node).get(row.id)

    @hybrid_property
    def children(self):
        """Return *all* child nodes without considering permissions."""

        return self._children

    def children_with_permission(self, request, permission='view'):
        """
        Return only those children for which the user initiating
        the request has the asked permission.

        :param request: current request
        :type request: :class:`pyramid.request.Request`
        :param permission: The permission for which you want the allowed
                           children
        :type permission: str
        :result: List of child nodes
        :rtype: list
        """

        return [
            c for c in self.children
            if has_permission(permission, c, request)
        ]


class LocalGroup(Base):

    __tablename__ = 'local_groups'
    __table_args__ = (
        UniqueConstraint('node_id', 'principal_name', 'group_name'),
        )

    id = Column(Integer(), primary_key=True)
    node_id = Column(ForeignKey('nodes.id'))
    principal_name = Column(Unicode(100))
    group_name = Column(Unicode(100))

    def __init__(self, node, principal_name, group_name):
        self.node = node
        self.principal_name = principal_name
        self.group_name = group_name

    def copy(self, **kwargs):
        kwargs.setdefault('node', self.node)
        kwargs.setdefault('principal_name', self.principal_name)
        kwargs.setdefault('group_name', self.group_name)

        return self.__class__(**kwargs)


class Node(Base, ContainerMixin, PersistentACLMixin):
    """Basic node in the persistance hierarchy.
    """

    implements(INode)

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
    parent_id = Column(ForeignKey('nodes.id'))
    #: Position of the node within its container / parent
    #: (:class:`sqlalchemy.types.Integer`)
    position = Column(Integer())
    _acl = Column(MutationList.as_mutable(ACLType))
    #: Name of the node as used in the URL
    #: (:class:`sqlalchemy.types.Unicode`)
    name = Column(Unicode(50), nullable=False)
    #: Title of the node, e.g. as shown in serach results
    #: (:class:`sqlalchemy.types.Unicode`)
    title = Column(Unicode(100))
    #: Annotations can be used to store arbitray data in a nested dictionary
    #: (:class:`kotti.sqla.NestedMustationDict`)
    annotations = Column(NestedMutationDict.as_mutable(JsonType))

    _children = relation(
        'Node',
        collection_class=ordering_list('position'),
        order_by=[position],
        backref=backref('parent', remote_side=[id]),
        cascade='all',
        )

    local_groups = relation(
        LocalGroup,
        backref=backref('node'),
        cascade='all',
        )

    def __init__(self, name=None, parent=None, title=u"", annotations=None):
        """Constructor"""

        if annotations is None:
            annotations = {}
        self.name = name
        self.parent = parent
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

    def __repr__(self):
        return '<%s %s at %s>' % (
            self.__class__.__name__, self.id, resource_path(self))

    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id

    def __ne__(self, other):
        return not self == other

    copy_properties_blacklist = (
        'id', 'parent', 'parent_id', '_children', 'local_groups', '_tags')

    def copy(self, **kwargs):
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
    """

    addable_to = ()
    selectable_default_views = ()
    uploadable_mimetypes = ()
    edit_links = ()
    action_links = ()

    def __init__(self, **kwargs):
        """
        Constructor
        """

        self.__dict__.update(kwargs)

    def copy(self, **kwargs):
        """

        :result: a copy of the current TypeInfo instance
        :rtype: :class:`~kotti.resources.TypeInfo`
        """

        d = self.__dict__.copy()
        d.update(kwargs)

        return TypeInfo(**d)

    def addable(self, context, request):
        """

        :param context:
        :type context: Content or subclass thereof (or anything that has a
                       type_info attribute of type
                       :class:`~kotti.resources.TypeInfo`)

        :param request: current request
        :type request: :class:`pyramid.request.Request`

        :result: True if the type described in 'self' may be added to 'context',
                 False otherwise.
        :rtype: Boolean
        """

        if view_permitted(context, request, self.add_view):
            return context.type_info.name in self.addable_to
        else:
            return False

    def add_selectable_default_view(self, name, title):
        """Add a view to the list of default views selectable by the
        user in the UI.

        :param name: Name the view is registered with
        :type name: str

        :param title: Title for the view for display in the UI.
        :type title: unicode or TranslationString
        """
        self.selectable_default_views.append((name, title))

    def is_uploadable_mimetype(self, mimetype):
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
            if fnmatch(mimetype, mt):
                if len(mt) > match_score:
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

    def __repr__(self):
        return "<Tag ('%s')>" % self.title

    @property
    def items(self):
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
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    #: Foreign key referencing :attr:`Content.id`
    #: (:class:`sqlalchemy.types.Integer`)
    content_id = Column(Integer, ForeignKey('contents.id'), primary_key=True)
    #: Relation that adds a ``content_tags`` :func:`sqlalchemy.orm.backref`
    #: to :class:`~kotti.resources.Tag` instances to allow easy access to all
    #: content tagged with that tag.
    #: (:func:`sqlalchemy.orm.relationship`)
    tag = relation(Tag, backref=backref('content_tags', cascade='all'))
    #: Ordering position of the tag
    #: :class:`sqlalchemy.types.Integer`
    position = Column(Integer, nullable=False)
    #: title of the associated :class:`~kotti.resources.Tag` instance
    #: (:class:`sqlalchemy.ext.associationproxy.association_proxy`)
    title = association_proxy('tag', 'title')

    @classmethod
    def _tag_find_or_create(cls, title):
        """
        Find or create a tag with the given title.

        :param title: Title of the tag to find or create.
        :type title: unicode
        :result:
        :rtype: :class:`~kotti.resources.TagsToContents`
        """

        with DBSession.no_autoflush:
            tag = DBSession.query(Tag).filter_by(title=title).first()
        if tag is None:
            tag = Tag(title=title)
        return cls(tag=tag)


def _not_root(context, request):
    return not context is get_root()


default_type_info = TypeInfo(
    name=u'Content',
    title=u'type_info title missing',   # BBB
    add_view=None,
    addable_to=[],
    edit_links=[
        ViewLink('contents', title=_(u'Contents')),
        ViewLink('edit', title=_(u'Edit')),
        ViewLink('share', title=_(u'Share')),
        ],
    action_links=[
        ViewLink('copy', title=_(u'Copy')),
        ViewLink('cut', title=_(u'Cut'), predicate=_not_root),
        ViewLink('paste', title=_(u'Paste'), predicate=get_paste_items),
        ViewLink('rename', title=_(u'Rename'), predicate=_not_root),
        ViewLink('delete', title=_(u'Delete'), predicate=_not_root),
        ],
    selectable_default_views=[
        ("folder_view", _(u"Folder view")),
        ],
    )


class Content(Node):
    """Content adds some attributes to :class:`~kotti.resources.Node` that are
       useful for content objects in a CMS.
    """

    implements(IContent)

    @classproperty
    def __mapper_args__(cls):
        return dict(polymorphic_identity=camel_case_to_name(cls.__name__))

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer, ForeignKey('nodes.id'), primary_key=True)
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

    def __init__(self, name=None, parent=None, title=u"", annotations=None,
                 default_view=None, description=u"", language=None,
                 owner=None, creation_date=None, modification_date=None,
                 in_navigation=True, tags=None):

        super(Content, self).__init__(name, parent, title, annotations)

        self.default_view = default_view
        self.description = description
        self.language = language
        self.owner = owner
        self.in_navigation = in_navigation
        # These are set by events if not defined at this point:
        self.creation_date = creation_date
        self.modification_date = modification_date
        self.tags = tags or []

    def copy(self, **kwargs):
        # Same as `Node.copy` with additional tag support.
        kwargs['tags'] = self.tags
        return super(Content, self).copy(**kwargs)


class Document(Content):
    """Document extends :class:`~kotti.resources.Content` with a body and its
       mime_type.  In addition Document and its descendants implement
       :class:`~kotti.interfaces.IDefaultWorkflow` and therefore
       are associated with the default workflow (at least in
       unmodified Kotti installations).
    """

    implements(IDocument, IDefaultWorkflow)

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    #: Body text of the Document
    #: (:class:`sqlalchemy.types.Unicode`)
    body = Column(UnicodeText())
    #: MIME type of the Document
    #: (:class:`sqlalchemy.types.String`)
    mime_type = Column(String(30))

    #: type_info is a class attribute
    #: (:class:`~kotti.resources.TypeInfo`)
    type_info = Content.type_info.copy(
        name=u'Document',
        title=_(u'Document'),
        add_view=u'add_document',
        addable_to=[u'Document'],
        )

    def __init__(self, body=u"", mime_type='text/html', **kwargs):

        super(Document, self).__init__(**kwargs)

        self.body = body
        self.mime_type = mime_type


class File(Content):
    """File adds some attributes to :class:`~kotti.resources.Content` that are
       useful for storing binary data.
    """

    implements(IFile)

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    #: The binary data itself
    #: (:class:`sqlalchemy.types.LargeBinary`)
    data = deferred(Column(LargeBinary()))
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

    type_info = Content.type_info.copy(
        name=u'File',
        title=_(u'File'),
        add_view=u'add_file',
        addable_to=[u'Document'],
        selectable_default_views=[],
        uploadable_mimetypes=['*', ],
        )

    def __init__(self, data=None, filename=None, mimetype=None, size=None,
                 **kwargs):

        super(File, self).__init__(**kwargs)

        self.data = data
        self.filename = filename
        self.mimetype = mimetype
        self.size = size

    @classmethod
    def from_field_storage(cls, fs):
        """ Create and return an instance of this class from a file upload
            through a webbrowser.

        :param fs: FieldStorage instance as found in a
                   :class:`pyramid.request.Request`'s ``POST`` MultiDict.
        :type fs: :class:`cgi.FieldStorage`

        :result: The created instance.
        :rtype: :class:`kotti.resources.File`
        """

        data = fs.file.read()
        filename = fs.filename
        mimetype = fs.type
        size = len(data)

        if not cls.type_info.is_uploadable_mimetype(mimetype):
            raise ValueError("Unsupported MIME type: %s" % mimetype)

        return cls(data=data, filename=filename, mimetype=mimetype, size=size)


class Image(File):
    """Image doesn't add anything to :class:`~kotti.resources.File`, but images
       have different views, that e.g. support on the fly scaling.
    """

    implements(IImage)

    id = Column(Integer(), ForeignKey('files.id'), primary_key=True)

    type_info = File.type_info.copy(
        name=u'Image',
        title=_(u'Image'),
        add_view=u'add_image',
        addable_to=[u'Document'],
        selectable_default_views=[],
        uploadable_mimetypes=['image/*', ],
        )


def get_root(request=None):
    """Call the function defined by the ``kotti.root_factory`` setting and
       return its result.

    :param request: current request (optional)
    :type request: :class:`pyramid.request.Request`

    :result: a node in the node tree
    :rtype: :class:`~kotti.resources.Node` or descendant;
    """
    return get_settings()['kotti.root_factory'][0](request)


def default_get_root(request=None):
    """Default implementation for :func:`~kotti.resources.get_root`.

    :param request: Current request (optional)
    :type request: :class:`pyramid.request.Request`

    :result: Node in the object tree that has no parent.
    :rtype: :class:`~kotti.resources.Node` or descendant; in a fresh Kotti site
            with Kotti's :func:`default populator <kotti.populate.populate>`
            this will be an instance of :class:`~kotti.resources.Document`.
    """
    return DBSession.query(Node).filter(Node.parent_id == None).one()


def initialize_sql(engine, drop_all=False):
    DBSession.registry.clear()
    DBSession.configure(bind=engine)
    metadata.bind = engine

    if drop_all or os.environ.get('KOTTI_TEST_DB_STRING'):
        metadata.reflect()
        metadata.drop_all(engine)

    # Allow users of Kotti to cherry pick the tables that they want to use:
    settings = get_current_registry().settings
    tables = settings['kotti.use_tables'].strip() or None
    if tables:
        tables = [metadata.tables[name] for name in tables.split()]

    if engine.dialect.name == 'mysql':  # pragma: no cover
        from sqlalchemy.dialects.mysql.base import LONGBLOB
        File.__table__.c.data.type = LONGBLOB()

    # Allow migrations to set the 'head' stamp in case the database is
    # initialized freshly:
    if not engine.table_names():
        stamp_heads()

    metadata.create_all(engine, tables=tables)
    if os.environ.get('KOTTI_DISABLE_POPULATORS', '0') not in ('1', 'y'):
        for populate in get_settings()['kotti.populators']:
            populate()
    commit()

    return DBSession


# BBB
for iface in ("INode", "IContent", "IDocument", "IFile", "IImage",
              "IDefaultWorkflow"):
    deprecated(iface,
               "%s has been moved to kotti.interfaces as of Kotti 0.8. "
               "Import from there instead." % iface)
