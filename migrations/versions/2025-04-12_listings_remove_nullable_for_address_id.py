"""Listings: remove nullable for address_id

Revision ID: 054e8dcaaa92
Revises: b7eac4a52d3c
Create Date: 2025-04-12 01:57:44.747485

"""

from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "054e8dcaaa92"
down_revision: Union[str, None] = "b7eac4a52d3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "listings", "address_id", existing_type=sa.INTEGER(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("listings", "address_id", existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###
