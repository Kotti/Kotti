from datetime import datetime

import sqlalchemy.event
from sqlalchemy.orm import mapper
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid

from kotti.resources import Node

def set_owner(mapper, connection, target):
    request = get_current_request()
    if (request is not None and
        isinstance(target, Node) and
        target.owner is None):
        userid = authenticated_userid(request)
        if userid is not None: # XXX testme
            target.owner = userid

def set_creation_date(mapper, connect, target):
    if target.creation_date is None:
        now = datetime.now()
        target.creation_date = now
        target.modification_date = now

def set_modification_date(mapper, connect, target):
    target.modification_date = datetime.now()

def includeme(config):
    sqlalchemy.event.listen(mapper, 'before_insert', set_owner)
    sqlalchemy.event.listen(mapper, 'before_insert', set_creation_date)
    sqlalchemy.event.listen(mapper, 'before_update', set_modification_date)
