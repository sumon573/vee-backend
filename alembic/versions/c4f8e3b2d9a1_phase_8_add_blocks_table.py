"""phase_8_add_blocks_table

Revision ID: c4f8e3b2d9a1
Revises: b3e9f2a1c5d8
Create Date: 2026-07-20

Creates the `blocks` table for Phase 8 — Privacy & Safety Foundation.

Schema:
    blocks (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        blocker_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        blocked_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (blocker_id, blocked_id),
        CHECK  (blocker_id <> blocked_id)
    )

Indexes:
    ix_blocks_blocker_id  — accelerates "list blocks by blocker"
    ix_blocks_blocked_id  — accelerates "list who has blocked user X"
    ix_blocks_created_at  — accelerates chronological ordering
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4f8e3b2d9a1"
down_revision: Union[str, Sequence[str], None] = "b3e9f2a1c5d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key — generated client-side by Python.",
        ),
        sa.Column(
            "blocker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="UUID of the user who initiated the block.",
        ),
        sa.Column(
            "blocked_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="UUID of the user who is blocked.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="UTC timestamp when the block was created (set by DB server).",
        ),
        sa.UniqueConstraint(
            "blocker_id",
            "blocked_id",
            name="uq_blocks_blocker_blocked",
        ),
        sa.CheckConstraint(
            "blocker_id != blocked_id",
            name="ck_blocks_no_self_block",
        ),
    )

    # Indexes for common access patterns
    op.create_index("ix_blocks_blocker_id", "blocks", ["blocker_id"])
    op.create_index("ix_blocks_blocked_id", "blocks", ["blocked_id"])
    op.create_index("ix_blocks_created_at", "blocks", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_blocks_created_at", table_name="blocks")
    op.drop_index("ix_blocks_blocked_id", table_name="blocks")
    op.drop_index("ix_blocks_blocker_id", table_name="blocks")
    op.drop_table("blocks")
