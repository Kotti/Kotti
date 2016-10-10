# -*- coding: utf-8 -*-
"""Add file columns  to images table.

Revision ID: 814c4ec72f1
Revises: 4a3de0d0804a
Create Date: 2015-12-14 17:37:36.723844

"""

# revision identifiers, used by Alembic.
from depot.fields.sqlalchemy import UploadedFileField

revision = '814c4ec72f1'
down_revision = '4a3de0d0804a'

from alembic import op
import sqlalchemy as sa

from kotti import DBSession


def upgrade():

    op.drop_table('images')
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), sa.ForeignKey('contents.id'),
                  primary_key=True),
        sa.Column('filename', sa.Unicode(100)),
        sa.Column('mimetype', sa.String(100)),
        sa.Column('size', sa.Integer()),
        sa.Column('data', UploadedFileField()))

    DBSession.execute("""
        INSERT INTO images (id, filename, mimetype, size, data)
        SELECT f.id, f.filename, f.mimetype, f.size, f.data
        FROM files f INNER JOIN nodes n ON f.id = n.id
        WHERE n.type = 'image'""")

    DBSession.execute("""
        DELETE FROM files
        WHERE id IN (SELECT id FROM images)""")


def downgrade():
    from kotti.resources import Image
    DBSession.execute("""
        INSERT INTO files (id, filename, mimetype, size, data)
        SELECT id, filename, mimetype, size, data
        FROM images""")
    op.drop_table('images')
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), sa.ForeignKey('files.id'),
                  primary_key=True))
    DBSession.execute("""
        INSERT INTO images (id)
        SELECT id
        FROM nodes
        WHERE type = 'image'""")
