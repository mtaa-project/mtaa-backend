"""add firebase cloud token table and relationships

Revision ID: 7e62c3d20f2c
Revises: 139101757380
Create Date: 2025-04-12 01:12:07.726929

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7e62c3d20f2c'
down_revision: Union[str, None] = '139101757380'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('firebaseCloudTokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_firebaseCloudTokens_token'), 'firebaseCloudTokens', ['token'], unique=False)
    op.add_column('userSearchAlerts', sa.Column('last_notified_at', sa.DateTime(), nullable=True))
    op.alter_column('userSearchAlerts', 'product_filters',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.drop_column('userSearchAlerts', 'updated_at')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('userSearchAlerts', sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.alter_column('userSearchAlerts', 'product_filters',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSON(astext_type=sa.Text()),
               existing_nullable=False)
    op.drop_column('userSearchAlerts', 'last_notified_at')
    op.drop_index(op.f('ix_firebaseCloudTokens_token'), table_name='firebaseCloudTokens')
    op.drop_table('firebaseCloudTokens')
    # ### end Alembic commands ###
