"""Update Node.path column

Revision ID: 559ce6eb0949
Revises: 1063d7178fa
Create Date: 2014-12-10 13:20:29.374951

"""

# revision identifiers, used by Alembic.
revision = '559ce6eb0949'
down_revision = '1063d7178fa'


def upgrade():

    from kotti.resources import DBSession

    from alembic.context import get_bind

    conn = get_bind()

    if conn.engine.dialect.name == 'mysql':
        update = "UPDATE nodes " \
                 "SET path = concat(path, '/') " \
                 "WHERE path NOT LIKE '%/'"
    else:
        update = "UPDATE nodes " \
                 "SET path = path || '/' " \
                 "WHERE path NOT LIKE '%/'"
    DBSession.execute(update)


def downgrade():
    from kotti import DBSession
    from kotti.resources import Node

    for node in DBSession.query(Node).with_polymorphic([Node]):
        # remove trailing '/' from all nodes but root
        if node.path != '/':
            node.path = node.path[:-1]
