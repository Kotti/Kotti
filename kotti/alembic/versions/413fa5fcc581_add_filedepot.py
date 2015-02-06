"""Migrate binary file storage to filedepot

Revision ID: 413fa5fcc581
Revises: 1063d7178fa
Create Date: 2014-12-07 05:10:04.294222

"""

# revision identifiers, used by Alembic.
revision = '413fa5fcc581'
down_revision = '559ce6eb0949'

import logging
import sqlalchemy as sa
import sys

log = logging.getLogger('kotti')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.INFO)


def upgrade():
    from depot.manager import DepotManager
    from depot.fields.upload import UploadedFile
    from sqlalchemy import bindparam

    from kotti import DBSession, metadata

    files = sa.Table('files', metadata)
    files.c.data.type = sa.LargeBinary()
    dn = DepotManager.get_default()

    _saved = []

    def process(thing):
        id, data, filename, mimetype = thing
        uploaded_file = UploadedFile({'depot_name': dn, 'files': []})
        uploaded_file._thaw()
        uploaded_file.process_content(
            data, filename=filename, content_type=mimetype)
        _saved.append({'nodeid': id, 'data': uploaded_file.encode()})
        log.info("Saved data for node id {}".format(id))

    query =  DBSession.query(
        files.c.id, files.c.data, files.c.filename, files.c.mimetype
    ).order_by(files.c.id).yield_per(10)

    window_size = 10  # or whatever limit you like
    window_idx = 0

    log.info("Starting migration of blob data")

    while True:
        start, stop = window_size * window_idx, window_size * (window_idx + 1)
        things = query.slice(start, stop).all()
        if things is None:
            break
        for thing in things:
            process(thing)
        if len(things) < window_size:
            break
        window_idx += 1

    log.info("Files written on disk, saving information to DB")

    update = files.update().where(files.c.id == bindparam('nodeid')).\
        values({files.c.data: bindparam('data')})

    DBSession.execute(update, _saved)

    log.info("Blob migration completed")


def downgrade():
    pass
