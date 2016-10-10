# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import contextmanager
from datetime import datetime
from UserDict import DictMixin

import bcrypt
from pyramid.location import lineage
from pyramid.security import view_execution_permitted
from six import string_types
from sqlalchemy import Boolean, bindparam
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.expression import or_
from zope.deprecation.deprecation import deprecated

from kotti import Base
from kotti import DBSession
from kotti import get_settings
from kotti.sqla import bakery
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from kotti.util import _
from kotti.util import request_cache
from kotti.util import DontCache


def get_principals():
    return get_settings()['kotti.principals_factory'][0]()


@request_cache(lambda request: None)
def get_user(request):
    userid = request.unauthenticated_userid
    return get_principals().get(userid)


def has_permission(permission, context, request):
    """ Check if the current request has a permission on the given context.

    .. deprecated:: 0.9

    :param permission: permission to check for
    :type permission: str

    :param context: context that should be checked for the given permission
    :type context: :class:``kotti.resources.Node``

    :param request: current request
    :type request: :class:`kotti.request.Request`

    :result: ``True`` if request has the permission, ``False`` else
    :rtype: bool
    """

    return request.has_permission(permission, context)


deprecated(u'has_permission',
           u"kotti.security.has_permission is deprecated as of Kotti 1.0 and "
           u"will be no longer available starting with Kotti 2.0.  "
           u"Please use the has_permission method of request instead.")


class Principal(Base):
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

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True)
    password = Column(Unicode(100))
    active = Column(Boolean)
    confirm_token = Column(Unicode(100))
    title = Column(Unicode(100), nullable=False)
    email = Column(Unicode(100), unique=True)
    groups = Column(MutationList.as_mutable(JsonType), nullable=False)
    creation_date = Column(DateTime(), nullable=False)
    last_login_date = Column(DateTime())

    __tablename__ = 'principals'
    __mapper_args__ = dict(
        order_by=name,
        )

    def __init__(self, name, password=None, active=True, confirm_token=None,
                 title=u"", email=None, groups=None):
        self.name = name
        if password is not None:
            password = get_principals().hash_password(password)
        self.password = password
        self.active = active
        self.confirm_token = confirm_token
        self.title = title
        self.email = email
        if groups is None:
            groups = []
        self.groups = groups
        self.creation_date = datetime.now()
        self.last_login_date = None

    def __repr__(self):  # pragma: no cover
        return u'<Principal {0!r}>'.format(self.name)


class AbstractPrincipals(object):
    """This class serves as documentation and defines what methods are
    expected from a Principals database.

    Principals mostly provides dict-like access to the principal
    objects in the database.  In addition, there's the 'search' method
    which allows searching users and groups.

    'hash_password' is for initial hashing of a clear text password,
    while 'validate_password' is used by the login to see if the
    entered password matches the hashed password that's already in the
    database.

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
        """Return an iterable with principal objects that correspond
        to the search arguments passed in.

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

    def validate_password(self, clear, hashed):
        """Returns True if the clear text password matches the hash.
        """

ROLES = {
    u'role:viewer': Principal(u'role:viewer', title=_(u'Viewer')),
    u'role:editor': Principal(u'role:editor', title=_(u'Editor')),
    u'role:owner': Principal(u'role:owner', title=_(u'Owner')),
    u'role:admin': Principal(u'role:admin', title=_(u'Admin')),
    }
_DEFAULT_ROLES = ROLES.copy()

# These roles are visible in the sharing tab
SHARING_ROLES = [u'role:viewer', u'role:editor', u'role:owner']
USER_MANAGEMENT_ROLES = SHARING_ROLES + ['role:admin']
_DEFAULT_SHARING_ROLES = SHARING_ROLES[:]
_DEFAULT_USER_MANAGEMENT_ROLES = USER_MANAGEMENT_ROLES[:]

# This is the ACL that gets set on the site root on creation.  Note
# that this is only really useful if you're _not_ using workflow.  If
# you are, then you should look at the permissions in workflow.zcml.
SITE_ACL = [
    ['Allow', 'system.Everyone', ['view']],
    ['Allow', 'role:viewer', ['view']],
    ['Allow', 'role:editor', ['view', 'add', 'edit', 'state_change']],
    ['Allow', 'role:owner', ['view', 'add', 'edit', 'manage', 'state_change']],
    ]


def set_roles(roles_dict):
    ROLES.clear()
    ROLES.update(roles_dict)


def set_sharing_roles(role_names):
    SHARING_ROLES[:] = role_names


def set_user_management_roles(role_names):
    USER_MANAGEMENT_ROLES[:] = role_names


def reset_roles():
    ROLES.clear()
    ROLES.update(_DEFAULT_ROLES)


def reset_sharing_roles():
    SHARING_ROLES[:] = _DEFAULT_SHARING_ROLES


def reset_user_management_roles():
    USER_MANAGEMENT_ROLES[:] = _DEFAULT_USER_MANAGEMENT_ROLES


def reset():
    reset_roles()
    reset_sharing_roles()
    reset_user_management_roles()


class PersistentACLMixin(object):
    def _get_acl(self):
        if self._acl is None:
            raise AttributeError('__acl__')
        return self._acl

    def _set_acl(self, value):
        self._acl = value

    def _del_acl(self):
        self._acl = None

    __acl__ = property(_get_acl, _set_acl, _del_acl)


def _cachekey_list_groups_raw(name, context):
    context_id = context is not None and getattr(context, 'id', id(context))
    return name, context_id


@request_cache(_cachekey_list_groups_raw)
def list_groups_raw(name, context):
    """A set of group names in given ``context`` for ``name``.

    Only groups defined in context will be considered, therefore no
    global or inherited groups are returned.
    """

    from kotti.resources import Node

    if isinstance(context, Node):
        return set(
            r.group_name for r in context.local_groups
            if r.principal_name == name
        )
    return set()


def list_groups(name, context=None):
    """List groups for principal with a given ``name``.

    The optional ``context`` argument may be passed to check the list
    of groups in a given context.
    """
    return list_groups_ext(name, context)[0]


def _cachekey_list_groups_ext(name, context=None, _seen=None, _inherited=None):
    if _seen is not None or _inherited is not None:
        raise DontCache
    else:
        context_id = getattr(context, 'id', id(context))
        return unicode(name), context_id


@request_cache(_cachekey_list_groups_ext)
def list_groups_ext(name, context=None, _seen=None, _inherited=None):
    name = unicode(name)
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
        _seen = {name}

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


def set_groups(name, context, groups_to_set=()):
    """Set the list of groups for principal with given ``name`` and in
    given ``context``.
    """

    from kotti.resources import LocalGroup

    name = unicode(name)
    context.local_groups = [
        # keep groups for "other" principals
        lg for lg in context.local_groups
        if lg.principal_name != name
    ] + [
        # reset groups for given principal
        LocalGroup(context, name, unicode(group_name))
        for group_name in groups_to_set
    ]


def list_groups_callback(name, request):
    """ List the groups for the principal identified by ``name``.  Consider
    ``authz_context`` to support assigment of local roles to groups. """
    if not is_user(name):
        return None  # Disallow logging in with groups
    if name in get_principals():
        context = request.environ.get(
            'authz_context', getattr(request, 'context', None))
        if context is None:
            # SA events don't have request.context available
            from kotti.resources import get_root
            context = get_root(request)
        return list_groups(name, context)


@contextmanager
def authz_context(context, request):
    before = request.environ.pop('authz_context', None)
    request.environ['authz_context'] = context
    try:
        yield
    finally:
        del request.environ['authz_context']
        if before is not None:
            request.environ['authz_context'] = before


@contextmanager
def request_method(request, method):
    before = request.method
    request.method = method
    try:
        yield
    finally:
        request.method = before


def view_permitted(context, request, name='', method='GET'):
    with authz_context(context, request):
        with request_method(request, method):
            return view_execution_permitted(context, request, name)


def principals_with_local_roles(context, inherit=True):
    """Return a list of principal names that have local roles in the
    context.
    """

    principals = set()
    items = [context]

    if inherit:
        items = lineage(context)

    for item in items:
        principals.update(
            r.principal_name for r in item.local_groups
            if not r.principal_name.startswith('role:')
        )

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
            all, inherited = list_groups_ext(principal_name, context)
            value.append((principal, (all, inherited)))
    return sorted(value, key=lambda t: t[0].name)


def is_user(principal):
    if not isinstance(principal, string_types):
        principal = principal.name
    return ':' not in principal


class Principals(DictMixin):
    """Kotti's default principal database.

    Look at 'AbstractPrincipals' for documentation.

    This is a default implementation that may be replaced by using the
    'kotti.principals' settings variable.
    """
    factory = Principal

    @classmethod
    def _principal_by_name(cls, name):
        query = bakery(lambda session: session.query(cls.factory).filter(
            cls.factory.name == bindparam('name')))
        return query(DBSession()).params(name=name).one()

    @request_cache(lambda self, name: unicode(name))
    def __getitem__(self, name):
        name = unicode(name)
        # avoid calls to the DB for roles
        # (they're not stored in the ``principals`` table)
        if name.startswith('role:'):
            raise KeyError(name)
        try:
            return self._principal_by_name(name)
            # return DBSession.query(
            #     self.factory).filter(self.factory.name == name).one()
        except NoResultFound:
            raise KeyError(name)

    def __setitem__(self, name, principal):
        name = unicode(name)
        if isinstance(principal, dict):
            principal = self.factory(**principal)
        DBSession.add(principal)

    def __delitem__(self, name):
        name = unicode(name)
        try:
            principal = self._principal_by_name(name)
            DBSession.delete(principal)
        except NoResultFound:
            raise KeyError(name)

    def iterkeys(self):
        for (principal_name,) in DBSession.query(self.factory.name):
            yield principal_name

    def keys(self):
        return list(self.iterkeys())

    def search(self, match='any', **kwargs):
        """ Search the principal database.

        :param match: ``any`` to return all principals matching any search
                      param, ``all`` to return only principals matching
                      all params
        :type match: str

        :param kwargs: Search conditions, e.g. ``name='bob', active=True``.
        :type kwargs: varying.

        :result: SQLAlchemy query object
        :rtype: :class:`sqlalchemy.orm.query.Query``
        """

        if not kwargs:
            return []

        filters = []

        for key, value in kwargs.items():
            col = getattr(self.factory, key)
            if isinstance(value, string_types) and '*' in value:
                value = value.replace('*', '%').lower()
                filters.append(func.lower(col).like(value))
            else:
                filters.append(col == value)

        query = DBSession.query(self.factory)

        if match == 'any':
            query = query.filter(or_(*filters))
        elif match == 'all':
            query = query.filter(and_(*filters))
        else:
            raise ValueError('match must be either "any" or "all".')

        return query

    log_rounds = 10

    def hash_password(self, password, hashed=None):
        if hashed is None:
            hashed = bcrypt.gensalt(self.log_rounds)
        return unicode(
            bcrypt.hashpw(password.encode('utf-8'), hashed.encode('utf-8')))

    def validate_password(self, clear, hashed):
        try:
            return self.hash_password(clear, hashed) == hashed
        except ValueError:
            return False


def principals_factory():
    return Principals()
