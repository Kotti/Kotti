"""Migrate binary file storage to filedepot

Revision ID: 413fa5fcc581
Revises: 1063d7178fa
Create Date: 2014-12-07 05:10:04.294222

"""

# revision identifiers, used by Alembic.
revision = '413fa5fcc581'
down_revision = '1063d7178fa'

#from alembic import op
import sqlalchemy as sa


def upgrade():
    sa.orm.events.MapperEvents._clear() # avoids filedepot magic

    from depot.manager import DepotManager
    from depot.fields.upload import UploadedFile

    from kotti import DBSession, metadata
    from kotti.resources import File

    t = sa.Table('files', metadata)
    t.c.data.type = sa.LargeBinary()

    class UF(UploadedFile):
        _frozen = False

        def __init__(self):
            self.depot_name = DepotManager.get_default()
            self.files = []

    for o in DBSession.query(File):
        print o.id, len(o.data), o.filename, o.mimetype, o.modification_date

        s = UF()
        s.process_content(o.data, filename=o.filename, content_type=o.mimetype)
        f = DepotManager.get().get(s['file_id'])
        f.last_modified = o.modification_date   # not ok for LocalStore
        o.data = s.encode()

    DBSession.flush()
    raise ValueError


def downgrade():
    pass
