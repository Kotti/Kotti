from pyramid.location import lineage
from pyramid.security import Allow
from pyramid.security import ALL_PERMISSIONS

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

def list_groups_raw(context, userid):
    groups = getattr(context, '__groups__', None)
    if groups is not None:
        return groups.get(userid, set())
    else:
        return set()

def list_groups(context, userid, _seen=None):
    if _seen is None:
        _seen = set()
    groups = set()
    for item in lineage(context):
        groups.update(list_groups_raw(item, userid))

    # Groups may be nested:
    new_groups = groups - _seen
    for groupid in new_groups:
        _seen.add(groupid)
        groups.update(list_groups(context, groupid, _seen))
    return list(groups)

def set_groups(context, userid, groups_to_set):
    groups = getattr(context, '__groups__', None)
    if groups is None:
        groups = {}
    groups[userid] = list(groups_to_set)
    context.__groups__ = groups
