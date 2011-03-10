from datetime import datetime
import hashlib
from UserDict import DictMixin

from sqlalchemy import Column
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import mapper
from sqlalchemy.orm.exc import NoResultFound
from pyramid.location import lineage
from pyramid.security import Allow
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import view_execution_permitted

from kotti import get_settings
from kotti import DBSession
from kotti import metadata
from kotti.util import JsonType
from kotti.util import request_cache
from kotti.util import DontCache

class Principal(object):
    """A minimal 'Principal' implementation.

    The attributes on this object correspond to what one ought to
    implement to get full support by the system.  You're free to add
    additional attributes.

      - As convenience, when passing 'password' in the initializer, it
        is hashed using 'get_principals().hash_password'

      - The boolean 'active' attribute defines whether a principal may
        log in.  This allows the deactivation of accounts without
        deleting them.

      - The 'confirm_token' attribute is set whenever a user has
        forgotten their password.  This token is used to identify the
        receiver of the email.  This attribute should be set to
        'None' once confirmation has succeeded.
    """
    def __init__(self, name, password=None, active=True, confirm_token=None,
                 title=u"", email=None, groups=()):
        self.name = name
        if password is not None:
            password = get_principals().hash_password(password)
        self.password = password
        self.active = active
        self.confirm_token = confirm_token
        self.title = title
        self.email = email
        self.groups = groups
        self.creation_date = datetime.now()

    def __repr__(self): # pragma: no cover
        return '<Principal %r>' % self.name

class AbstractPrincipals(object):
    """This class serves as documentation and defines what methods are
    expected from a Principals database.

    Principals mostly provides dict-like access to the principal
    objects in the database.  In addition, there's the 'search' method
    which allows searching users and groups, and the 'hash_password'
    method that implements user password hashing.

    Use the 'kotti.principals' settings variable to override Kotti's
    default Principals implementation with your own.
    """
    def __getitem__(self, name):
        """Return the Principal object with the id 'name'.
        """

    def __setitem__(self, name, principal):
        """Add a given Principal object to the database.

        'name' is expected to the the same as 'principal.name'.

        'principal' may also be a dict of attributes.
        """

    def __delitem__(self, name):
        """Remove the principal with the given name from the database.
        """

    def keys(self):
        """Return a list of principal ids that are in the database.
        """

    def search(self, **kwargs):
        """Return a list of principal objects that correspond to the
        search arguments passed in.

        This example would return all principals with the id 'bob':

          get_principals().search(name=u'bob')

        Here, we ask for all principals that have 'bob' in either
        their 'name' or their 'title'.  We pass '*bob*' instead of
        'bob' to indicate that we want case-insensitive substring
        matching:

          get_principals().search(name=u'*bob*', title=u'*bob*')

        This call should fail with AttributeError unless there's a
        'foo' attribute on principal objects that supports search:

          get_principals().search(name=u'bob', foo=u'bar')
        """

    def hash_password(self, password):
        """Return a hash of the given password.

        This is what's stored in the database as 'principal.password'.
        """

ROLES = {
    u'role:viewer': Principal(u'role:viewer', title=u'Viewer'),
    u'role:editor': Principal(u'role:editor', title=u'Editor'),
    u'role:owner': Principal(u'role:owner', title=u'Owner'),
    u'role:admin': Principal(u'role:admin', title=u'Admin'),
    }

# These roles are visible in the sharing tab
SHARING_ROLES = [u'role:viewer', u'role:editor', u'role:owner']
USER_MANAGEMENT_ROLES = SHARING_ROLES + ['role:admin']

# This is the ACL that gets set on the site root on creation.
SITE_ACL = [
    ['Allow', 'system.Everyone', ['view']],
    ['Allow', 'role:viewer', ['view']],
    ['Allow', 'role:editor', ['view', 'add', 'edit']],
    ['Allow', 'role:owner', ['view', 'add', 'edit', 'manage']],
    ]

class PersistentACL(object):
    """Manages access to ``self._acl`` which is a JSON- serialized
    representation of ``self.__acl__``.
    """
    ALL_PERMISSIONS_SERIALIZED = '__ALL_PERMISSIONS__'

    @staticmethod
    def _deserialize_ace(ace):
        ace = list(ace)
        if ace[2] == PersistentACL.ALL_PERMISSIONS_SERIALIZED:
            ace[2] = ALL_PERMISSIONS
        return tuple(ace)

    @staticmethod
    def _serialize_ace(ace):
        ace = list(ace)
        if ace[2] == ALL_PERMISSIONS:
            ace[2] = PersistentACL.ALL_PERMISSIONS_SERIALIZED
        return ace

    def _get_acl(self):
        if self._acl is not None:
            acl = self._default_acl() + self._acl
            return [self._deserialize_ace(ace) for ace in acl]
        else:
            raise AttributeError('__acl__')

    def _set_acl(self, acl):
        self._acl = [self._serialize_ace(ace) for ace in acl]

    def _del_acl(self):
        if self._acl is not None:
            self._acl = None
        else:
            raise AttributeError('__acl__')

    __acl__ = property(_get_acl, _set_acl, _del_acl)

    def _default_acl(self):
        # ACEs that will be put on top, no matter what
        return [
            (Allow, 'role:admin', ALL_PERMISSIONS),
            ]

def all_groups_raw(context):
    return getattr(context, '__roles__', None)

def list_groups_raw(name, context):
    groups = all_groups_raw(context)
    if groups is not None:
        return groups.get(name, set())
    else:
        return set()

def list_groups(name, context=None):
    return list_groups_ext(name, context)[0]

def _cachekey_list_groups_ext(name, context=None, _seen=None, _inherited=None):
    if _seen is not None or _inherited is not None:
        raise DontCache
    else:
        context_id = context is not None and context.id
        return (name, context_id)

@request_cache(_cachekey_list_groups_ext)
def list_groups_ext(name, context=None, _seen=None, _inherited=None):
    groups = set()
    recursing = _inherited is not None
    _inherited = _inherited or set()

    # Add groups from principal db:
    principal = get_principals().get(name)
    if principal is not None:
        groups.update(principal.groups)
        if context is not None or (context is None and _seen is not None):
            _inherited.update(principal.groups)

    if _seen is None:
        _seen = set([name])

    # Add local groups:
    if context is not None:
        items = lineage(context)
        for idx, item in enumerate(items):
            group_names = [i for i in list_groups_raw(name, item)
                           if i not in _seen]
            groups.update(group_names)
            if recursing or idx != 0:
                _inherited.update(group_names)
    
    new_groups = groups - _seen
    _seen.update(new_groups)
    for group_name in new_groups:
        g, i = list_groups_ext(
            group_name, context, _seen=_seen, _inherited=_inherited)
        groups.update(g)
        _inherited.update(i)

    return list(groups), list(_inherited)

def set_groups_raw(context, groups):
    context.__roles__ = groups

def set_groups(name, context, groups_to_set):
    groups = all_groups_raw(context)
    if groups is None:
        groups = {}
    else:
        groups = dict(groups)
    if groups_to_set:
        groups[name] = list(groups_to_set)
    else:
        groups.pop(name, None)
    set_groups_raw(context, groups)

def list_groups_callback(name, request):
    if not is_user(name):
        return None # Disallow logging in with groups
    if name in get_principals():
        context = request.environ.get(
            'authz_context', getattr(request, 'context', None))
        if context is None:
            # SA events don't have request.context available
            from kotti.resources import get_root
            context = get_root(request)
        return list_groups(name, context)

def view_permitted(context, request, name=''):
    try:
        request.environ['authz_context'] = context
        return view_execution_permitted(context, request, name)
    finally:
        del request.environ['authz_context']

def principals_with_local_roles(context):
    """Return a list of principal names that have local roles
    (inherited or not) in the context.
    """
    principals = set()
    for item in lineage(context):
        agr = all_groups_raw(item)
        if agr is not None:
            ap = [p for p in agr.keys() if not p.startswith('role:')]
            principals.update(ap)
    return list(principals)

def map_principals_with_local_roles(context):
    principals = get_principals()
    value = []
    for principal_name in principals_with_local_roles(context):
        try:
            principal = principals[principal_name]
        except KeyError:
            continue
        else:
            all, inherited = list_groups_ext(
                principal_name, context)
            value.append((principal, (all, inherited)))
    return sorted(value, key=lambda t: t[0].name)

def get_principals():
    return get_settings()['kotti.principals'][0]

def is_user(principal):
    if not isinstance(principal, basestring):
        principal = principal.name
    return ':' not in principal

class Principals(DictMixin):
    """Kotti's default principal database.

    Look at 'AbstractPrincipals' for documentation.

    This is a default implementation that may be replaced by using the
    'kotti.principals' settings variable.
    """
    factory = Principal

    @request_cache(lambda self, name: name)
    def __getitem__(self, name):
        name = unicode(name)
        session = DBSession()
        try:
            return session.query(
                self.factory).filter(self.factory.name==name).one()
        except NoResultFound:
            raise KeyError(name)

    def __setitem__(self, name, principal):
        name = unicode(name)
        session = DBSession()
        if isinstance(principal, dict):
            principal = self.factory(**principal)
        session.add(principal)

    def __delitem__(self, name):
        name = unicode(name)
        session = DBSession()
        try:
            principal = session.query(
                self.factory).filter(self.factory.name==name).one()
            session.delete(principal)
        except NoResultFound:
            raise KeyError(name)

    def iterkeys(self):
        session = DBSession()
        for (principal_name,) in session.query(self.factory.name):
            yield principal_name

    def keys(self):
        return list(self.iterkeys())

    def search(self, **kwargs):
        if not kwargs:
            return []

        filters = []
        for key, value in kwargs.items():
            col = getattr(self.factory, key)
            if '*' in value:
                filters.append(col.like(value.replace('*', '%')))
            else:
                filters.append(col == value)

        session = DBSession()
        query = session.query(self.factory)
        query = query.filter(or_(*filters))
        return query

    def hash_password(self, password):
        salt = get_settings()['kotti.secret']
        return unicode(hashlib.sha224(salt + password).hexdigest())

principals = Principals()

principals_table = Table('principals', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', Unicode(100), unique=True),
    Column('password', Unicode(100)),
    Column('active', Boolean),
    Column('confirm_token', Unicode(100)),
    Column('title', Unicode(100), nullable=False),
    Column('email', Unicode(100), unique=True),
    Column('groups', JsonType(), nullable=False),
    Column('creation_date', DateTime(), nullable=False),
)

mapper(Principal, principals_table, order_by=principals_table.c.name)
