"""empty message

Revision ID: b85cd508eff7
Revises: 14b57e5cef21
Create Date: 2021-02-23 11:45:24.348423

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b85cd508eff7'
down_revision = '14b57e5cef21'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('project_database',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('database_host', sa.String(length=256), nullable=True),
    sa.Column('database_name', sa.String(length=256), nullable=False),
    sa.Column('database_user', sa.String(length=256), nullable=False),
    sa.Column('database_password', sa.String(length=256), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('date_created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('project_database')
    # ### end Alembic commands ###
