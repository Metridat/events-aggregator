"""increase name length to 200

Revision ID: 6ec4804eef14
Revises: b3f6421921d2
Create Date: 2026-04-05 12:47:56.653960

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6ec4804eef14"
down_revision: Union[str, Sequence[str], None] = "b3f6421921d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "events",
        "name",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.VARCHAR(length=200),
        nullable=False,
    )

    op.alter_column(
        "places",
        "name",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.VARCHAR(length=200),
        nullable=False,
    )
    op.alter_column(
        "places",
        "city",
        existing_type=sa.VARCHAR(length=30),
        type_=sa.VARCHAR(length=100),
        nullable=False,
    )
    op.alter_column(
        "places",
        "address",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.VARCHAR(length=200),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "events",
        "name",
        existing_type=sa.VARCHAR(length=200),
        type_=sa.VARCHAR(length=50),
        nullable=False,
    )

    op.alter_column(
        "places",
        "name",
        existing_type=sa.VARCHAR(length=200),
        type_=sa.VARCHAR(length=50),
        nullable=False,
    )
    op.alter_column(
        "places",
        "city",
        existing_type=sa.VARCHAR(length=100),
        type_=sa.VARCHAR(length=30),
        nullable=False,
    )
    op.alter_column(
        "places",
        "address",
        existing_type=sa.VARCHAR(length=200),
        type_=sa.VARCHAR(length=50),
        nullable=False,
    )
