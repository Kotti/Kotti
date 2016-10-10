# -*- coding: utf-8 -*-
"""Initialize workflow and publish all items.

Revision ID: 57fecf5dbd62
Revises: 9398ccf41c2
Create Date: 2012-08-06 17:53:55.352478

"""

# revision identifiers, used by Alembic.
revision = '57fecf5dbd62'
down_revision = '9398ccf41c2'


def upgrade():
    from kotti import DBSession
    from kotti import get_settings
    from kotti.resources import Document
    from kotti.workflow import get_workflow
    from kotti.workflow import reset_workflow

    is_default = get_settings()['kotti.use_workflow'] == 'kotti:workflow.zcml'
    if not is_default:
        return

    reset_workflow()
    for obj in DBSession.query(Document):
        workflow = get_workflow(obj)
        workflow.transition_to_state(obj, None, 'public')


def downgrade():
    pass
