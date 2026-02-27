"""Add 'Content.state' for workflow

Revision ID: 9398ccf41c2
Revises: None
Create Date: 2012-07-27 12:36:32.463710

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9398ccf41c2'
down_revision = None


def upgrade():
    op.add_column('contents', sa.Column('state', sa.String(50)))


def downgrade():
    op.drop_column('contents', 'state')
