"""phase_6_add_deleted_at_to_users

Revision ID: a8f3d1c90e2b
Revises: cfeccaac3dc7
Create Date: 2026-07-20 18:00:00.000000

Phase 6 — Extended User Profile & Follow System
Changes:
    - Add `deleted_at` (TIMESTAMP WITH TIME ZONE, nullable) column to `users`
    - Add index `ix_users_deleted_at` on `users.deleted_at`
    - Reduce `username` column size from VARCHAR(50) to VARCHAR(30) to match
      the new 3–30 char validation rule (existing data is safe — auto-generated
      usernames are at most 20 chars: vee_ + 16 chars)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8f3d1c90e2b"
down_revision: Union[str, Sequence[str], None] = "cfeccaac3dc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add soft-delete timestamp column
    op.add_column(
        "users",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment=(
                "UTC timestamp of user-initiated account deletion. "
                "NULL = active. Non-null = soft-deleted."
            ),
        ),
    )

    # Add index for efficient filtering of deleted accounts
    op.create_index(
        "ix_users_deleted_at",
        "users",
        ["deleted_at"],
        unique=False,
    )

    # Shrink username column to match schema validation (3–30 chars).
    # Auto-generated usernames (vee_<uid[:16]>) are max 20 chars — safe.
    op.alter_column(
        "users",
        "username",
        type_=sa.String(length=30),
        existing_type=sa.String(length=50),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Restore username column width
    op.alter_column(
        "users",
        "username",
        type_=sa.String(length=50),
        existing_type=sa.String(length=30),
        existing_nullable=False,
    )

    # Drop deleted_at index and column
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_column("users", "deleted_at")
