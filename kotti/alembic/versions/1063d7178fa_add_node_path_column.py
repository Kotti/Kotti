"""Add Node.path column

Revision ID: 1063d7178fa
Revises: 57fecf5dbd62
Create Date: 2014-05-26 15:34:31.050983

"""

from alembic import op
import sqlalchemy as sa
from pyramid.location import lineage


# revision identifiers, used by Alembic.
revision = '1063d7178fa'
down_revision = '57fecf5dbd62'


def upgrade():
    from alembic.context import get_bind

    conn = get_bind()
    if conn.engine.dialect.name == 'mysql':
        op.add_column('nodes', sa.Column('path', sa.Unicode(1000)))
    else:
        op.add_column('nodes', sa.Column('path', sa.Unicode(1000), index=True))

    from kotti import DBSession
    from kotti.resources import Node

    for node in DBSession.query(Node).with_polymorphic([Node]):
        reversed_lineage = reversed(tuple(lineage(node)))
        node.path = u'/'.join(
            node.__name__ for node in reversed_lineage) or u'/'


def downgrade():
    op.drop_column('nodes', 'path')
