"""add_authorization

Revision ID: d417c8ca8c52
Revises: b98819997377
Create Date: 2019-05-24 18:59:19.055469

"""

# revision identifiers, used by Alembic.
revision = 'd417c8ca8c52'
down_revision = 'b98819997377'

from alembic import op
import iotronic.db.sqlalchemy.models
import sqlalchemy as sa


def upgrade():
    role = op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('permissions',
                  iotronic.db.sqlalchemy.models.JSONEncodedList(),
                  nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_roles0name')
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('base_role', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['base_role'], ['roles.name'],),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_users0name'),
        sa.UniqueConstraint('uuid', name='uniq_users0uuid')
    )
    operation = op.create_table(
        'operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_operations0name')
    )
    op.create_table(
        'delegations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=True),
        sa.Column('delegated', sa.String(length=32), nullable=True),
        sa.Column('delegator', sa.String(length=32), nullable=True),
        sa.Column('parent', sa.String(length=36), nullable=True),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('node', sa.String(length=36), nullable=True),
        sa.Column('type', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['delegated'], ['users.uuid'],),
        sa.ForeignKeyConstraint(['delegator'], ['users.uuid'],),
        sa.ForeignKeyConstraint(
            ['parent'], ['delegations.uuid'], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(['role'], ['roles.name'],),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uniq_delegations0uuid'),
        sa.UniqueConstraint('delegated', 'node',
                            name='uniq_delegations0delegated_node')
    )
    op.bulk_insert(
        operation, [
            {"name": "all:all", },
            {"name": "all:get", },
            {"name": "all:get_one", },
            {"name": "all:create", },
            {"name": "all:delete", },
            {"name": "all:update", },
            {"name": "all:delegate", },
            {"name": "all:undelegate", },
            {"name": "all:delegation_get", },
            {"name": "all:delegation_get_one", },
            {"name": "all:delegation_update", },
            {"name": "board:all", },
            {"name": "board:get", },
            {"name": "board:get_one", },
            {"name": "board:create", },
            {"name": "board:delete", },
            {"name": "board:update", },
            {"name": "board:plugin_get", },
            {"name": "board:plugin_post", },
            {"name": "board:plugin_put", },
            {"name": "board:plugin_delete", },
            {"name": "board:service_get", },
            {"name": "board:service_action", },
            {"name": "board:service_restore", },
            {"name": "board:webservice_get", },
            {"name": "board:webservice_create", },
            {"name": "board:webservice_enable", },
            {"name": "board:webservice_disable", },
            {"name": "board:port_get", },
            {"name": "board:port_get_one", },
            {"name": "board:delegation_get", },
            {"name": "board:delegation_get_one", },
            {"name": "board:delegation_update", },
            {"name": "board:delegate", },
            {"name": "board:undelegate", },
            {"name": "plugin:all", },
            {"name": "plugin:get", },
            {"name": "plugin:get_one", },
            {"name": "plugin:create", },
            {"name": "plugin:delete", },
            {"name": "plugin:update", },
            {"name": "plugin:put", },
            {"name": "plugin:post", },
            {"name": "plugin:delegation_get", },
            {"name": "plugin:delegation_get_one", },
            {"name": "plugin:delegation_update", },
            {"name": "plugin:delegate", },
            {"name": "plugin:undelegate", },
            {"name": "service:all", },
            {"name": "service:get", },
            {"name": "service:get_one", },
            {"name": "service:create", },
            {"name": "service:delete", },
            {"name": "service:update", },
            {"name": "service:delegation_get", },
            {"name": "service:delegation_get_one", },
            {"name": "service:delegation_update", },
            {"name": "service:delegate", },
            {"name": "service:undelegate", },
            {"name": "fleet:all", },
            {"name": "fleet:get", },
            {"name": "fleet:get_one", },
            {"name": "fleet:create", },
            {"name": "fleet:delete", },
            {"name": "fleet:update", },
            {"name": "fleet:delegation_get", },
            {"name": "fleet:delegation_get_one", },
            {"name": "fleet:delegation_update", },
            {"name": "fleet:delegate", },
            {"name": "fleet:undelegate", },
            {"name": "webservice:all", },
            {"name": "webservice:get", },
            {"name": "webservice:get_one", },
            {"name": "webservice:delete", },
            {"name": "webservice:update", },
            {"name": "webservice:delegation_get", },
            {"name": "webservice:delegation_get_one", },
            {"name": "webservice:delegation_update", },
            {"name": "webservice:delegate", },
            {"name": "webservice:undelegate", },
            {"name": "port:all", },
            {"name": "port:get", },
            {"name": "port:get_one", },
            {"name": "user:all", },
            {"name": "user:get", },
            {"name": "user:get_one", },
            {"name": "user:create", },
            {"name": "user:delete", },
            {"name": "user:update", },
            {"name": "role:all", },
            {"name": "role:get", },
            {"name": "role:get_one", },
            {"name": "role:create", },
            {"name": "role:delete", },
            {"name": "role:update", },
            {"name": "role:op_get", },
        ])
    op.bulk_insert(
        role, [
            {"name": "iot_admin", "permissions": ["all:all"], },
            {"name": "iot_manager",
             "permissions": ["all:get", "all:get_one", "all:update",
                             "all:delegate", "all:undelegate",
                             "all:delegation_get", "all:delegation_get_one",
                             "board:plugin_get", "board:plugin_post",
                             "board:plugin_put", "board:plugin_delete",
                             "board:service_get", "board:service_action",
                             "board:service_restore", "board:webservice_get",
                             "board:webservice_create",
                             "board:webservice_enable",
                             "board:webservice_disable", "board:port_get",
                             "board:port_get_one", "plugin:put",
                             "plugin:post"], },
            {"name": "iot_user",
             "permissions": ["all:get", "all:get_one", "all:delegation_get",
                             "all:delegation_get_one", "board:plugin_get",
                             "board:service_get", "board:webservice_get",
                             "board:port_get"], },
            {"name": "owner", "permissions": None, }
        ])


def downgrade():
    op.drop_table('delegations')
    op.drop_table('operations')
    op.drop_table('users')
    op.drop_table('roles')
