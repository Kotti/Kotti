"""Update Node.path column

Revision ID: 559ce6eb0949
Revises: 1063d7178fa
Create Date: 2014-12-10 13:20:29.374951

"""

# revision identifiers, used by Alembic.
revision = '559ce6eb0949'
down_revision = '1063d7178fa'


def upgrade():

    from kotti.resources import metadata, DBSession
    from sqlalchemy import Table, select, bindparam
    from sqlalchemy.sql.expression import not_

    nodes = Table('nodes', metadata)

    to_change = [dict(nodepath=r[0], nodeid=r[1]) for r in
                 select([nodes.c.path + '/', nodes.c.id]).
                 where(not_(nodes.c.path == u'/')).execute()]

    updater = nodes.update().\
        where(nodes.c.id == bindparam('nodeid')).\
        values({nodes.c.path:bindparam('nodepath')})

    DBSession.execute(updater, to_change)


def downgrade():
    from kotti import DBSession
    from kotti.resources import Node

    for node in DBSession.query(Node).with_polymorphic([Node]):
        # remove trailing '/' from all nodes but root
        if node.path != u'/':
            node.path = node.path[:-1]
