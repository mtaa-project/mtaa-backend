"""add offer type and listing status to listing model

Revision ID: 871a2281b45f
Revises: 97d473aeaa20
Create Date: 2025-03-17 21:58:07.179793

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "871a2281b45f"
down_revision: Union[str, None] = "97d473aeaa20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    offertype = sa.Enum("LEND", "SELL", "BOTH", name="offertype")
    offertype.create(
        op.get_bind(), checkfirst=True
    )  # Ak už existuje, nevytvorí sa znova

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "listings",
        sa.Column(
            "offer_type",
            sa.Enum("LEND", "SELL", "BOTH", name="offertype"),
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("listings", "offer_type")
    # ### end Alembic commands ###
    sa.Enum(name="offertype").drop(op.get_bind(), checkfirst=True)
