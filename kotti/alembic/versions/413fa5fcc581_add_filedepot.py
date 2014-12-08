"""Migrate binary file storage to filedepot

Revision ID: 413fa5fcc581
Revises: 1063d7178fa
Create Date: 2014-12-07 05:10:04.294222

"""

# revision identifiers, used by Alembic.
revision = '413fa5fcc581'
down_revision = '1063d7178fa'

import logging
import sqlalchemy as sa
from alembic import op

log = logging.getLogger('kotti')


def upgrade():
    sa.orm.events.MapperEvents._clear()     # avoids filedepot magic

    from depot.manager import DepotManager
    from depot.fields.upload import UploadedFile
    from depot.fields.sqlalchemy import UploadedFileField

    from kotti import DBSession, metadata
    from kotti.resources import File

    t = sa.Table('files', metadata)
    t.c.data.type = sa.LargeBinary()
    dn = DepotManager.get_default()

    for obj in DBSession.query(File):
        uploaded_file = UploadedFile({'depot_name': dn, 'files': []})
        uploaded_file._thaw()
        uploaded_file.process_content(
            obj.data, filename=obj.filename, content_type=obj.mimetype)
        stored_file = DepotManager.get().get(uploaded_file['file_id'])
        stored_file.last_modified = obj.modification_date
        obj.data = uploaded_file.encode()

        log.info("Migrated {} bytes for File with pk {} to {}/{}".
                    format(len(obj.data), obj.id, dn, uploaded_file['file_id']))

    DBSession.flush()
    if DBSession.get_bind().name != 'sqlite':   # not supported by sqlite
        op.alter_column('files', 'data', type_=UploadedFileField())


def downgrade():
    pass
