"""Migrate binary file storage to filedepot

Revision ID: 413fa5fcc581
Revises: 1063d7178fa
Create Date: 2014-12-07 05:10:04.294222

"""

# revision identifiers, used by Alembic.
revision = '413fa5fcc581'
down_revision = '559ce6eb0949'

from alembic import op
import logging
import sqlalchemy as sa
import sys
import time

log = logging.getLogger('kotti')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.INFO)


def upgrade():
    from depot.manager import DepotManager
    from depot.fields.upload import UploadedFile
    from sqlalchemy import bindparam, Unicode, Column

    from kotti import DBSession, metadata

    files = sa.Table('files', metadata)
    files.c.data.type = sa.LargeBinary()    # this restores to old column type
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

    query = DBSession.query(
        files.c.id, files.c.data, files.c.filename, files.c.mimetype
    ).order_by(files.c.id).yield_per(10)

    window_size = 10
    window_idx = 0

    log.info("Starting migration of blob data")

    now = time.time()
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

    op.drop_column('files', 'data')
    op.add_column('files', Column('data', Unicode(4096)))
    files.c.data.type = Unicode(4096)

    update = files.update().where(files.c.id == bindparam('nodeid')).\
        values({files.c.data: bindparam('data')})

    def chunks(l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i + n]

    for cdata in chunks(_saved, 10):
        DBSession.execute(update, cdata)

    log.info("Blob migration completed in {} seconds".format(
        int(time.time() - now)))


def downgrade():
    pass
