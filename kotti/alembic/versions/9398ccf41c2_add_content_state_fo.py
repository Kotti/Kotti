# -*- coding: utf-8 -*-
"""Add 'Content.state' for workflow

Revision ID: 9398ccf41c2
Revises: None
Create Date: 2012-07-27 12:36:32.463710

"""

# revision identifiers, used by Alembic.
revision = '9398ccf41c2'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('contents', sa.Column('state', sa.String(50)))


def downgrade():
    op.drop_column('contents', 'state')
