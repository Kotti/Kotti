import os
from UserDict import DictMixin

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path
from sqlalchemy.sql import and_
from sqlalchemy.sql import select
from sqlalchemy.orm import backref
from sqlalchemy.orm import mapper
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relation
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy import Table
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
from zope.interface import implements
from zope.interface import Interface

from kotti import get_settings
from kotti import DBSession
from kotti import metadata
from kotti.util import _
from kotti.util import ViewLink
from kotti.util import JsonType
from kotti.util import MutationList
from kotti.util import NestedMutationDict
from kotti.security import PersistentACLMixin
from kotti.security import view_permitted

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
        DBSession().delete(node)

    def keys(self):
        return [child.name for child in self.children]

    def __getitem__(self, path):
        session = DBSession()
        session._autoflush()

        if not hasattr(path, '__iter__'):
            path = (path,)

        if 'children' in self.__dict__:
            # If children are already in memory, don't query the database:
            first, rest = path[0], path[1:]
            try:
                [v] = [child for child in self.children if child.name == path[0]]
            except ValueError:
                raise KeyError(path)
            if rest:
                return v[rest]
            else:
                return v

        # Using the ORM interface here in a loop would join over all
        # polymorphic tables, so we'll use a 'handmade' select instead:
        conditions = [nodes.c.id==self.id]
        alias = nodes
        for name in path:
            alias, old_alias = nodes.alias(), alias
            conditions.append(alias.c.parent_id==old_alias.c.id)
            conditions.append(alias.c.name==unicode(name))
        expr = select([alias.c.id], and_(*conditions))
        row = session.execute(expr).fetchone()
        if row is None:
            raise KeyError(path)
        return session.query(Node).get(row.id)

class INode(Interface):
    pass

class IContent(Interface):
    pass

class Node(ContainerMixin, PersistentACLMixin):
    implements(INode)

    id = None
    in_navigation = False
    
    def __init__(self, name=None, parent=None, title=u"", annotations=None):
        if annotations is None:
            annotations = {}
        self.name = name
        self.parent = parent
        self.title = title
        self.annotations = annotations

    # Provide location-awareness through __name__ and __parent__
    @property
    def __name__(self):
        return self.name

    @property
    def __parent__(self):
        return self.parent

    def __repr__(self): # pragma: no cover
        return '<%s %s at %s>' % (
            self.__class__.__name__, self.id, resource_path(self))

    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id

    def __ne__(self, other):
        return not self == other

    copy_properties_blacklist = (
        'id', 'parent', 'parent_id', 'children', 'local_groups')
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

class LocalGroup(object):
    def __init__(self, node, principal_name, group_name):
        self.node = node
        self.principal_name = principal_name
        self.group_name = group_name

    def copy(self, **kwargs):
        kwargs.setdefault('node', self.node)
        kwargs.setdefault('principal_name', self.principal_name)
        kwargs.setdefault('group_name', self.group_name)
        return self.__class__(**kwargs)

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

class Content(Node):
    implements(IContent)

    type_info = TypeInfo(
        name=u'Content',
        add_view=None,
        addable_to=[],
        edit_links=[
            ViewLink('edit', title=_(u'Edit')),
            ViewLink('move', title=_(u'Move')),
            ViewLink('share', title=_(u'Share')),
            ],
        )

    def __init__(self, name=None, parent=None, title=u"", annotations=None,
                 default_view=None, description=u"", language=None,
                 owner=None, creation_date=None, modification_date=None,
                 in_navigation=True):
        super(Content, self).__init__(name, parent, title, annotations)
        self.default_view = default_view
        self.description = description
        self.language = language
        self.owner = owner
        self.in_navigation = in_navigation
        # These are set by events if not defined at this point:
        self.creation_date = creation_date
        self.modification_date = modification_date

class Document(Content):
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

nodes = Table('nodes', metadata,
    Column('id', Integer, primary_key=True),
    Column('type', String(30), nullable=False),
    Column('parent_id', ForeignKey('nodes.id')),
    Column('position', Integer),
    Column('_acl', MutationList.as_mutable(JsonType)),

    Column('name', Unicode(50), nullable=False),
    Column('title', Unicode(100)),
    Column('annotations', NestedMutationDict.as_mutable(JsonType)),

    UniqueConstraint('parent_id', 'name'),
)

local_groups_table = Table('local_groups', metadata,
    Column('id', Integer, primary_key=True),
    Column('node_id', ForeignKey('nodes.id')),
    Column('principal_name', Unicode(100)),
    Column('group_name', Unicode(100)),

    UniqueConstraint('node_id', 'principal_name', 'group_name'),
)

contents = Table('contents', metadata,
    Column('id', Integer, ForeignKey('nodes.id'), primary_key=True),
    Column('default_view', String(50)),
    Column('description', UnicodeText()),
    Column('language', Unicode(10)),
    Column('owner', Unicode(100)),
    Column('creation_date', DateTime()),
    Column('modification_date', DateTime()),
    Column('in_navigation', Boolean()),
)

documents = Table('documents', metadata,
    Column('id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('body', UnicodeText()),
    Column('mime_type', String(30)),
)

files = Table('files', metadata,
    Column('id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('data', LargeBinary()),
    Column('filename', Unicode(100)),
    Column('mimetype', String(100)),
    Column('size', Integer()),
    )

mapper(
    Node,
    nodes,
    polymorphic_on=nodes.c.type,
    polymorphic_identity='node',
    with_polymorphic='*',
    properties={
        'children': relation(
            Node,
            collection_class=ordering_list('position'),
            order_by=[nodes.c.position],
            backref=backref('parent', remote_side=[nodes.c.id]),
            cascade='all',
            ),
        'local_groups': relation(
            LocalGroup,
            backref=backref('node'),
            cascade='all',
            )
        },
    )

mapper(LocalGroup, local_groups_table)

mapper(Content, contents, inherits=Node, polymorphic_identity='content')
mapper(Document, documents, inherits=Content, polymorphic_identity='document')
mapper(File, files, inherits=Content, polymorphic_identity='file')

class Settings(object):
    def __init__(self, data):
        self.data = data

    def copy(self, newdata):
        data = self.data.copy()
        data.update(newdata)
        copy = self.__class__(data)
        return copy

settings = Table('settings', metadata,
    Column('id', Integer, primary_key=True),
    Column('data', JsonType()),
    )

mapper(Settings, settings)

def get_root(request=None):
    return get_settings()['kotti.root_factory'][0](request)

def default_get_root(request=None):
    return DBSession.query(Node).filter(Node.parent_id==None).first()

def initialize_sql(engine, drop_all=False):
    DBSession.registry.clear()
    DBSession.configure(bind=engine)
    metadata.bind = engine

    if drop_all or os.environ.get('KOTTI_TEST_DB_STRING'):
        metadata.drop_all(engine)

    # Allow users of Kotti to cherry pick the tables that they want to use:
    settings = get_current_registry().settings
    tables = settings['kotti.use_tables'].strip() or None
    if tables:
        if 'settings' not in tables:
            tables += ' settings'
        tables = [metadata.tables[name] for name in tables.split()]

    metadata.create_all(engine, tables=tables)
    for populate in get_settings()['kotti.populators']:
        populate()

    return DBSession()

def appmaker(engine):
    initialize_sql(engine)
    return get_root
