"""fix event datetime timezone

Revision ID: 19b49ce16ad9
Revises: 31cc6f6b93be
Create Date: 2026-04-02 10:45:04.074495

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "19b49ce16ad9"
down_revision: Union[str, Sequence[str], None] = "31cc6f6b93be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "events",
        "event_time",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        postgresql_using="event_time AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "events",
        "registration_deadline",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        postgresql_using="registration_deadline AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "events",
        "event_time",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
    )
    op.alter_column(
        "events",
        "registration_deadline",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
    )

    op.alter_column("places", "name", type_=sa.String(200))
    op.alter_column("places", "city", type_=sa.String(100))
    op.alter_column("places", "address", type_=sa.String(200))
    op.alter_column("events", "name", type_=sa.String(200))
