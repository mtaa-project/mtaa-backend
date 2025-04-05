"""merge heads after branch merge

Revision ID: c97829557c85
Revises: 3091bbcdeb92, 95ae1008acef
Create Date: 2025-04-05 12:30:02.842922

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c97829557c85'
down_revision: Union[str, None] = ('3091bbcdeb92', '95ae1008acef')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
