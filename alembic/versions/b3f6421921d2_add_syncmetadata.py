"""add SyncMetadata

Revision ID: b3f6421921d2
Revises: 19b49ce16ad9
Create Date: 2026-04-04 10:22:58.924229

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f6421921d2"
down_revision: Union[str, Sequence[str], None] = "19b49ce16ad9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sync_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_sync_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_changed_at", sa.String(length=128), nullable=True),
        sa.Column("sync_status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        text(
            "INSERT INTO sync_metadata "
            "(id, last_sync_time, last_changed_at, sync_status) "
            "VALUES (1, NULL, NULL, 'idle')"
        )
    )


def downgrade() -> None:
    op.drop_table("sync_metadata")
