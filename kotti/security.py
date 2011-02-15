from datetime import datetime
from UserDict import DictMixin

from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import DateTime
from sqlalchemy.orm import mapper
from sqlalchemy.orm.exc import NoResultFound
from pyramid.location import lineage
from pyramid.security import Allow
from pyramid.security import ALL_PERMISSIONS

from kotti import configuration
from kotti.resources import DBSession
from kotti.resources import metadata
from kotti.util import JsonType

ALL_PERMISSIONS_SERIALIZED = '__ALL_PERMISSIONS__'

class ACL(object):
    """Manages access to ``self._acl`` which is a JSON- serialized
    representation of ``self.__acl__``.
    """

    @staticmethod
    def _deserialize_ace(ace):
        ace = list(ace)
        if ace[2] == ALL_PERMISSIONS_SERIALIZED:
            ace[2] = ALL_PERMISSIONS
        return tuple(ace)

    @staticmethod
    def _serialize_ace(ace):
        ace = list(ace)
        if ace[2] == ALL_PERMISSIONS:
            ace[2] = ALL_PERMISSIONS_SERIALIZED
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
        # XXX Not sure this is a good idea.
        return [
            (Allow, 'group:admins', ALL_PERMISSIONS),
            ]

def list_groups_raw(userid, context):
    groups = getattr(context, '__groups__', None)
    if groups is not None:
        return groups.get(userid, set())
    else:
        return set()

def list_groups(userid, context, _seen=None):
    groups = set()
    if _seen is None:
        user = get_users().get(userid)
        if user is not None:
            groups.update(user.groups)
        _seen = set()

    for item in lineage(context):
        groups.update(list_groups_raw(userid, item))

    # Groups may be nested:
    new_groups = groups - _seen
    for groupid in new_groups:
        _seen.add(groupid)
        groups.update(list_groups(groupid, context, _seen))
    return list(groups)

def set_groups(userid, context, groups_to_set):
    groups = getattr(context, '__groups__', None)
    if groups is None:
        groups = {}
    groups[userid] = list(groups_to_set)
    context.__groups__ = groups

def list_groups_callback(userid, request):
    if userid in get_users():
        return list_groups(userid, request.context)

def get_users():
    return configuration['kotti.users'][0]

class Users(DictMixin):
    """Kotti's default user database.

    Promises dict-like access to user profiles, and a 'query' method
    for finding users.

    This is a default implementation that may be replaced by using the
    'kotti.users' configuration variable.
    """
    def __getitem__(self, key):
        key = unicode(key)
        session = DBSession()
        try:
            return session.query(User).filter(User.id==key).one()
        except NoResultFound:
            raise KeyError(key)

    def __setitem__(self, key, user):
        key = unicode(key)
        session = DBSession()
        if isinstance(user, dict):
            profile = User(**user)
        session.add(profile)

    def __delitem__(self, key):
        key = unicode(key)
        session = DBSession()
        try:
            user = session.query(User).filter(User.id==key).one()
            session.delete(user)
        except NoResultFound:
            raise KeyError(key)

    def keys(self):
        session = DBSession()
        for (userid,) in session.query(User.id):
            yield userid

    def query(self, **kwargs):
        session = DBSession()
        query = session.query(User)
        for key, value in kwargs.items():
            attr = getattr(User, key)
            query = query.filter(attr.like(value))
        return query

class User(object):
    def __init__(self, id, title=None, groups=()):
        self.id = id
        self.title = title
        self.groups = groups
        self.creation_date = datetime.now()

users = Users()

users_table = Table('users', metadata,
    Column('id', Unicode(100), primary_key=True),
    Column('title', Unicode(100)),
    Column('groups', JsonType(), nullable=False),
    Column('creation_date', DateTime(), nullable=False),
)

mapper(User, users_table)
