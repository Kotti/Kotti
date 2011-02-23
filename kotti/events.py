import sqlalchemy.event
from sqlalchemy.orm import mapper
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid

from kotti.resources import Node
from kotti.security import list_groups
from kotti.security import set_groups

def set_owner(mapper, connection, target):
    request = get_current_request()
    if (request is not None and
        isinstance(target, Node) and
        target.owner is None):
        userid = authenticated_userid(request)
        if userid is not None:
            target.owner = userid
            if u'role:owner' not in list_groups(u'bob', target):
                set_groups(userid, target, [u'role:owner'])

def includeme(config):
    sqlalchemy.event.listen(mapper, 'before_insert', set_owner)
