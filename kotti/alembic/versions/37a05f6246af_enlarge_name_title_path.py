# -*- coding: utf-8 -*-
"""Enlarged name title

Revision ID: 37a05f6246af
Revises: 413fa5fcc581
Create Date: 2015-05-15 17:12:07.631190

"""

# revision identifiers, used by Alembic.
revision = '37a05f6246af'
down_revision = '413fa5fcc581'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('nodes',
                    'title',
                    type_=sa.Unicode(250),
                    )
    op.alter_column('nodes',
                    'name',
                    type_=sa.Unicode(250),
                    )
    op.alter_column('nodes',
                    'path',
                    type_=sa.Unicode(2000),
                    )


def downgrade():
    op.alter_column('nodes',
                    'title',
                    type_=sa.Unicode(100),
                    )
    op.alter_column('nodes',
                    'name',
                    type_=sa.Unicode(50),
                    )
    op.alter_column('nodes',
                    'path',
                    type_=sa.Unicode(1000),
                    )
