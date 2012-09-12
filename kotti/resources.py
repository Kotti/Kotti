import os
from UserDict import DictMixin

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path
from sqlalchemy.sql import and_
from sqlalchemy.sql import select
from sqlalchemy.orm import backref
from sqlalchemy.orm import deferred
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relation
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.util import classproperty
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Column
from sqlalchemy import UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from transaction import commit
from zope.interface import implements
from zope.interface import Interface

from kotti import get_settings
from kotti import metadata
from kotti import DBSession
from kotti import Base
from kotti.migrate import stamp_heads
from kotti.security import PersistentACLMixin
from kotti.security import view_permitted
from kotti.sqla import ACLType
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from kotti.sqla import NestedMutationDict
from kotti.util import _
from kotti.util import camel_case_to_name
from kotti.util import ViewLink


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
        return self._children


class INode(Interface):
    pass


class IContent(Interface):
    pass


class IDocument(Interface):
    pass


class IFile(Interface):
    pass


class IImage(IFile):
    pass


class IDefaultWorkflow(Interface):
    pass


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
    implements(INode)

    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
        )
    __mapper_args__ = dict(
        polymorphic_on='type',
        polymorphic_identity='node',
        with_polymorphic='*',
        )

    id = Column(Integer(), primary_key=True)
    type = Column(String(30), nullable=False)
    parent_id = Column(ForeignKey('nodes.id'))
    position = Column(Integer())
    _acl = Column(MutationList.as_mutable(ACLType))
    name = Column(Unicode(50), nullable=False)
    title = Column(Unicode(100))
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
    addable_to = ()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def copy(self, **kwargs):
        d = self.__dict__.copy()
        d.update(kwargs)
        return TypeInfo(**d)

    def addable(self, context, request):
        """Return True if the type described in 'self' may be added to
        'context'.
        """
        if view_permitted(context, request, self.add_view):
            return context.type_info.name in self.addable_to
        else:
            return False


class Tag(Base):
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(100), unique=True, nullable=False)

    def __repr__(self):
        return "<Tag ('%s')>" % self.title

    @property
    def items(self):
        return [rel.item for rel in self.content_tags]


class TagsToContents(Base):
    __tablename__ = 'tags_to_contents'

    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    content_id = Column(Integer, ForeignKey('contents.id'), primary_key=True)
    tag = relation(Tag, backref=backref('content_tags', cascade='all'))
    position = Column(Integer, nullable=False)
    title = association_proxy('tag', 'title')

    @classmethod
    def _tag_find_or_create(self, title):
        with DBSession.no_autoflush:
            tag = DBSession.query(Tag).filter_by(title=title).first()
        if tag is None:
            tag = Tag(title=title)
        return self(tag=tag)


class Content(Node):
    implements(IContent)

    @classproperty
    def __mapper_args__(cls):
        return dict(polymorphic_identity=camel_case_to_name(cls.__name__))

    id = Column(Integer, ForeignKey('nodes.id'), primary_key=True)
    default_view = Column(String(50))
    description = Column(UnicodeText())
    language = Column(Unicode(10))
    owner = Column(Unicode(100))
    state = Column(String(50))
    creation_date = Column(DateTime())
    modification_date = Column(DateTime())
    in_navigation = Column(Boolean())
    _tags = relation(
        TagsToContents,
        backref=backref('item'),
        order_by=[TagsToContents.position],
        collection_class=ordering_list("position"),
        cascade='all, delete-orphan',
        )
    tags = association_proxy(
        '_tags',
        'title',
        creator=TagsToContents._tag_find_or_create,
        )

    type_info = TypeInfo(
        name=u'Content',
        title=u'type_info title missing',   # BBB
        add_view=None,
        addable_to=[],
        edit_links=[
            ViewLink('edit', title=_(u'Edit')),
            ViewLink('share', title=_(u'Share')),
            ],
        )

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
        tags = getattr(self, 'tags', None)
        kwargs['tags'] = tags
        return super(Content, self).copy(**kwargs)


class Document(Content):
    implements(IDocument, IDefaultWorkflow)

    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    body = Column(UnicodeText())
    mime_type = Column(String(30))

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

    implements(IFile)

    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    data = deferred(Column(LargeBinary()))
    filename = Column(Unicode(100))
    mimetype = Column(String(100))
    size = Column(Integer())

    type_info = Content.type_info.copy(
        name=u'File',
        title=_(u'File'),
        add_view=u'add_file',
        addable_to=[u'Document'],
        )

    def __init__(self, data=None, filename=None, mimetype=None, size=None,
                 **kwargs):
        super(File, self).__init__(**kwargs)
        self.data = data
        self.filename = filename
        self.mimetype = mimetype
        self.size = size


class Image(File):

    implements(IImage)

    id = Column(Integer(), ForeignKey('files.id'), primary_key=True)

    type_info = File.type_info.copy(
        name=u'Image',
        title=_(u'Image'),
        add_view=u'add_image',
        addable_to=[u'Document', ], )


def get_root(request=None):
    return get_settings()['kotti.root_factory'][0](request)


def default_get_root(request=None):
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


def appmaker(engine):
    initialize_sql(engine)
    return get_root
