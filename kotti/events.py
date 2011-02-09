from datetime import datetime

import sqlalchemy.event
from sqlalchemy.orm import mapper

def set_creation_date(mapper, connect, target):
    if target.creation_date is None:
        now = datetime.now()
        target.creation_date = now
        target.modification_date = now

def set_modification_date(mapper, connect, target):
    target.modification_date = datetime.now()

def includeme(config):
    sqlalchemy.event.listen(mapper, 'before_insert', set_creation_date)
    sqlalchemy.event.listen(mapper, 'before_update', set_modification_date)
