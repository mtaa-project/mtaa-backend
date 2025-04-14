"""merge heads

Revision ID: 7b0384b476dd
Revises: 54808d2d6bac, 24916feca6d7
Create Date: 2025-04-13 16:39:23.483959

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7b0384b476dd'
down_revision: Union[str, None] = ('54808d2d6bac', '24916feca6d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
