"""Allow file to store contents externally

Revision ID: 395d64c75964
Revises: 57fecf5dbd62
Create Date: 2014-02-06 21:22:08.821598

"""

# revision identifiers, used by Alembic.
revision = '395d64c75964'
down_revision = '57fecf5dbd62'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('files', 'data', name='_data')
    op.add_column('files', sa.Column('storage', sa.String(100)))


def downgrade():
    op.drop_column('files', 'storage')
    op.alter_column('files', '_data', name='data')
