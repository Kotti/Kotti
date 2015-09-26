"""Add ForeignKey indices

Revision ID: 4a3de0d0804a
Revises: 37a05f6246af
Create Date: 2015-08-31 12:37:26.493958

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '4a3de0d0804a'
down_revision = '37a05f6246af'


def upgrade():
    op.create_index(
        'ix_nodes_parent_id', 'nodes', ['parent_id', ])
    op.create_index(
        'ix_local_groups_node_id', 'local_groups', ['node_id', ])
    op.create_index(
        'ix_local_groups_principal_name', 'local_groups', ['principal_name', ])
    op.create_index(
        'ix_tags_to_contents_tag_id', 'tags_to_contents', ['tag_id', ])
    op.create_index(
        'ix_tags_to_contents_content_id', 'tags_to_contents', ['content_id', ])


def downgrade():
    op.drop_index('ix_nodes_parent_id', 'nodes')
    op.drop_index('ix_local_groups_node_id', 'local_groups')
    op.drop_index('ix_local_groups_principal_name', 'local_groups')
