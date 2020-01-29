from collections.abc import MutableMapping
from contextlib import contextmanager
from datetime import datetime
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import bcrypt
from pyramid.location import lineage
from pyramid.security import PermitsResult
from pyramid.security import view_execution_permitted
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import bindparam
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.expression import or_

from kotti import Base
from kotti import DBSession
from kotti import get_settings
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from kotti.sqla import bakery
from kotti.util import DontCache
from kotti.util import _
from kotti.util import request_cache


def has_permission(
    permission: str, context: "Node", request: "Request"
) -> PermitsResult:
    """ Default permission checker """
    return request.has_permission(permission, context=context)


def get_principals() -> "Principals":
    return get_settings()["kotti.principals_factory"][0]()


# @request_cache(lambda request: None)
def get_user(request: "Request") -> Optional["Principal"]:
    userid = request.unauthenticated_userid
    return get_principals().get(userid)


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

    __tablename__ = "principals"
    # __mapper_args__ = dict(order_by=name)

    def __init__(
        self,
        name: str,
        password: Optional[str] = None,
        active: Optional[bool] = True,
        confirm_token: Optional[str] = None,
        title: Optional[str] = "",
        email: Optional[str] = None,
        groups: Optional[List[str]] = None,
    ):
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
        return f"<Principal {self.name!r}>"


class AbstractPrincipals:
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

    def __getitem__(self, name: str):
        """Return the Principal object with the id 'name'.
        """

    def __setitem__(self, name: str, principal: Union[Principal, dict]):
        """Add a given Principal object to the database.

        'name' is expected to the the same as 'principal.name'.

        'principal' may also be a dict of attributes.
        """

    def __delitem__(self, name: str) -> None:
        """Remove the principal with the given name from the database.
        """

    def keys(self) -> List[str]:
        """Return a list of principal ids that are in the database.
        """

    def search(self, **kwargs) -> List[Principal]:
        """Return an iterable with principal objects that correspond
        to the search arguments passed in.

        This example would return all principals with the id 'bob':

          get_principals().search(name='bob')

        Here, we ask for all principals that have 'bob' in either
        their 'name' or their 'title'.  We pass '*bob*' instead of
        'bob' to indicate that we want case-insensitive substring
        matching:

          get_principals().search(name='*bob*', title='*bob*')

        This call should fail with AttributeError unless there's a
        'foo' attribute on principal objects that supports search:

          get_principals().search(name='bob', foo='bar')
        """

    def hash_password(self, password: str) -> str:
        """Return a hash of the given password.

        This is what's stored in the database as 'principal.password'.
        """

    def validate_password(self, clear: str, hashed: str) -> bool:
        """Returns True if the clear text password matches the hash.
        """


ROLES = {
    "role:viewer": Principal("role:viewer", title=_("Viewer")),
    "role:editor": Principal("role:editor", title=_("Editor")),
    "role:owner": Principal("role:owner", title=_("Owner")),
    "role:admin": Principal("role:admin", title=_("Admin")),
}
_DEFAULT_ROLES = ROLES.copy()

# These roles are visible in the sharing tab
SHARING_ROLES = ["role:viewer", "role:editor", "role:owner"]
USER_MANAGEMENT_ROLES = SHARING_ROLES + ["role:admin"]
_DEFAULT_SHARING_ROLES = SHARING_ROLES[:]
_DEFAULT_USER_MANAGEMENT_ROLES = USER_MANAGEMENT_ROLES[:]

# This is the ACL that gets set on the site root on creation.  Note
# that this is only really useful if you're _not_ using workflow.  If
# you are, then you should look at the permissions in workflow.zcml.
SITE_ACL = [
    ["Allow", "system.Everyone", ["view"]],
    ["Allow", "role:viewer", ["view"]],
    ["Allow", "role:editor", ["view", "add", "edit", "state_change"]],
    ["Allow", "role:owner", ["view", "add", "edit", "manage", "state_change"]],
]


def set_roles(roles_dict: Dict[str, Principal]) -> None:
    ROLES.clear()
    ROLES.update(roles_dict)


def set_sharing_roles(role_names: List[str]) -> None:
    SHARING_ROLES[:] = role_names


def set_user_management_roles(role_names: List[str]) -> None:
    USER_MANAGEMENT_ROLES[:] = role_names


def reset_roles() -> None:
    ROLES.clear()
    ROLES.update(_DEFAULT_ROLES)


def reset_sharing_roles() -> None:
    SHARING_ROLES[:] = _DEFAULT_SHARING_ROLES


def reset_user_management_roles() -> None:
    USER_MANAGEMENT_ROLES[:] = _DEFAULT_USER_MANAGEMENT_ROLES


def reset() -> None:
    reset_roles()
    reset_sharing_roles()
    reset_user_management_roles()


class PersistentACLMixin:
    def _get_acl(self) -> MutationList:
        if self._acl is None:
            raise AttributeError("__acl__")
        return self._acl

    def _set_acl(self, value) -> None:
        self._acl = value

    def _del_acl(self) -> None:
        self._acl = None

    __acl__ = property(_get_acl, _set_acl, _del_acl)


def _cachekey_list_groups_raw(
    name: str, context: "Node"
) -> Tuple[str, Union[int, "NoneType"]]:  # noqa
    context_id = context is not None and getattr(context, "id", id(context))
    return name, context_id


@request_cache(_cachekey_list_groups_raw)
def list_groups_raw(name, context):
    """A set of group names in given ``context`` for ``name``.

    Only groups defined in context will be considered, therefore no
    global or inherited groups are returned.
    """

    from kotti.resources import Node

    if isinstance(context, Node):
        return {
            r.group_name for r in context.local_groups if r.principal_name == name
        }
    return set()


def list_groups(name: str, context: Optional["Node"] = None) -> List[str]:
    """List groups for principal with a given ``name``.

    The optional ``context`` argument may be passed to check the list
    of groups in a given context.
    """
    return list_groups_ext(name, context)[0]


def _cachekey_list_groups_ext(
    name: str,
    context: Optional["Node"] = None,
    _seen: Optional[Set[str]] = None,
    _inherited: Optional[Set[str]] = None,
) -> Tuple[str, Union[int, "NoneType"]]:  # noqa
    if _seen is not None or _inherited is not None:
        raise DontCache
    else:
        context_id = getattr(context, "id", id(context))
        return name, context_id


@request_cache(_cachekey_list_groups_ext)
def list_groups_ext(name, context=None, _seen=None, _inherited=None):
    name = name
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
            group_names = [i for i in list_groups_raw(name, item) if i not in _seen]
            groups.update(group_names)
            if recursing or idx != 0:
                _inherited.update(group_names)

    new_groups = groups - _seen
    _seen.update(new_groups)
    for group_name in new_groups:
        g, i = list_groups_ext(group_name, context, _seen=_seen, _inherited=_inherited)
        groups.update(g)
        _inherited.update(i)

    return list(groups), list(_inherited)


def set_groups(name: str, context: "Node", groups_to_set: Iterable[str] = ()) -> None:
    """Set the list of groups for principal with given ``name`` and in
    given ``context``.
    """

    from kotti.resources import LocalGroup

    context.local_groups = [
        # keep groups for "other" principals
        lg
        for lg in context.local_groups
        if lg.principal_name != name
    ] + [
        # reset groups for given principal
        LocalGroup(context, name, group_name)
        for group_name in groups_to_set
    ]


def list_groups_callback(name: str, request: "Request") -> Optional[List[str]]:
    """ List the groups for the principal identified by ``name``.  Consider
    ``authz_context`` to support assignment of local roles to groups. """
    if not is_user(name):
        return None  # Disallow logging in with groups
    if name in get_principals():
        context = request.environ.get(
            "authz_context", getattr(request, "context", None)
        )
        if context is None:
            # SA events don't have request.context available
            from kotti.resources import get_root

            context = get_root(request)
        return list_groups(name, context)


@contextmanager
def authz_context(context: object, request: "Request"):
    before = request.environ.pop("authz_context", None)
    request.environ["authz_context"] = context
    try:
        yield
    finally:
        del request.environ["authz_context"]
        if before is not None:
            request.environ["authz_context"] = before


@contextmanager
def request_method(request: "Request", method: str):
    before = request.method
    request.method = method
    try:
        yield
    finally:
        request.method = before


def view_permitted(
    context: object,
    request: "Request",
    name: Optional[str] = "",
    method: Optional[str] = "GET",
) -> PermitsResult:
    with authz_context(context, request):
        with request_method(request, method):
            return view_execution_permitted(context, request, name)


def principals_with_local_roles(
    context: "Node", inherit: Optional[bool] = True
) -> List[str]:
    """Return a list of principal names that have local roles in the
    context.
    """

    principals = set()
    items = [context]

    if inherit:
        items = lineage(context)

    for item in items:
        principals.update(
            r.principal_name
            for r in item.local_groups
            if not r.principal_name.startswith("role:")
        )

    return list(principals)


def map_principals_with_local_roles(context: "Node"):
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


def is_user(principal: Union[Principal, str]) -> bool:
    if not isinstance(principal, str):
        principal = principal.name
    return ":" not in principal


class Principals(MutableMapping):
    """Kotti's default principal database.

    Look at 'AbstractPrincipals' for documentation.

    This is a default implementation that may be replaced by using the
    'kotti.principals' settings variable.
    """

    factory = Principal

    @classmethod
    def _principal_by_name(cls, name: str) -> Principal:
        query = bakery(
            lambda session: session.query(cls.factory).filter(
                cls.factory.name == bindparam("name")
            )
        )
        return query(DBSession()).params(name=name).one()

    @request_cache(lambda self, name: name)
    def __getitem__(self, name):
        if name is None or not isinstance(name, str):
            raise KeyError(name)
        # avoid calls to the DB for roles
        # (they're not stored in the ``principals`` table)
        if name.startswith("role:"):
            raise KeyError(name)
        try:
            return self._principal_by_name(name)
            # return DBSession.query(
            #     self.factory).filter(self.factory.name == name).one()
        except NoResultFound:
            raise KeyError(name)

    def __setitem__(self, name: str, principal: Union[Principal, dict]) -> None:
        name = name
        if isinstance(principal, dict):
            principal = self.factory(**principal)
        DBSession.add(principal)

    def __delitem__(self, name: str) -> None:
        name = name
        try:
            principal = self._principal_by_name(name)
            DBSession.delete(principal)
        except NoResultFound:
            raise KeyError(name)

    def __iter__(self) -> Iterator[str]:
        yield from self.keys()

    def __len__(self):
        return len(self.keys())

    def iterkeys(self) -> Iterator[str]:
        for (principal_name,) in DBSession.query(self.factory.name):
            yield principal_name

    def keys(self) -> List[str]:
        return list(self.iterkeys())

    def search(self, match: Optional[str] = "any", **kwargs) -> Query:
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
            if isinstance(value, str) and "*" in value:
                value = value.replace("*", "%").lower()
                filters.append(func.lower(col).like(value))
            else:
                filters.append(col == value)

        query = DBSession.query(self.factory)

        if match == "any":
            query = query.filter(or_(*filters))
        elif match == "all":
            query = query.filter(and_(*filters))
        else:
            raise ValueError('match must be either "any" or "all".')

        return query

    log_rounds = 10

    def hash_password(self, password: str, hashed: Optional[str] = None) -> str:
        if hashed is None:
            hashed = bcrypt.gensalt(self.log_rounds)
        return bcrypt.hashpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def validate_password(self, clear: str, hashed: str) -> bool:
        try:
            return self.hash_password(clear, hashed) == hashed
        except ValueError:
            return False


def principals_factory() -> Principals:
    return Principals()
