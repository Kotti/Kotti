from pyramid import security

class ACE(object):
    def __init__(self, action, principal, permissions):
        self.action = action
        self.principal = principal
        self.permissions = permissions

    def tuple(self):
        return (self.action, self.principal, self.permissions)

    def __repr__(self): # pragma: no cover
        return 'ACE%r' % ((self.action, self.principal, self.permissions),)

class ACL(object):
    def _get_acl(self):
        if self.aces:
            acl = self._default_acl()
            for entry in self.aces:
                acl.append(entry.tuple())
            return acl
        else:
            raise AttributeError()

    def _set_acl(self, acl):
        aces = []
        for entry in acl:
            if not isinstance(entry, ACE):
                entry = ACE(*entry)
            aces.append(entry)
        self.aces[:] = aces

    def _del_acl(self):
        if self.aces:
            self.aces = []
        else:
            raise AttributeError()

    __acl__ = property(_get_acl, _set_acl, _del_acl)

    def _default_acl(self):
        # ACEs that will be put on top, no matter what
        # XXX Not sure this is a good idea.
        return [
            (security.Allow, 'group:managers', security.ALL_PERMISSIONS),
            ]
    
