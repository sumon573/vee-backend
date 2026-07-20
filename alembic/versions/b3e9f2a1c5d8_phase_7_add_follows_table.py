"""phase_7_add_follows_table

Revision ID: b3e9f2a1c5d8
Revises: a8f3d1c90e2b
Create Date: 2026-07-20 20:00:00.000000

Phase 7 — Social Graph Foundation
Changes:
    - Create `follows` table with columns:
        id           (UUID v4, primary key)
        follower_id  (UUID, FK → users.id ON DELETE CASCADE, NOT NULL)
        following_id (UUID, FK → users.id ON DELETE CASCADE, NOT NULL)
        created_at   (TIMESTAMP WITH TIME ZONE, server default NOW(), NOT NULL)
    - UNIQUE constraint uq_follows_follower_following (follower_id, following_id)
    - CHECK  constraint ck_follows_no_self_follow   (follower_id != following_id)
    - Indexes:
        ix_follows_follower_id   — accelerates "who does user X follow?"
        ix_follows_following_id  — accelerates "who follows user X?"
        ix_follows_created_at    — accelerates chronological list queries
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b3e9f2a1c5d8"
down_revision: Union[str, Sequence[str], None] = "a8f3d1c90e2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the follows table and its indexes/constraints."""

    op.create_table(
        "follows",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key — generated client-side by Python.",
        ),
        # Participants
        sa.Column(
            "follower_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="UUID of the user who is following (the initiator).",
        ),
        sa.Column(
            "following_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="UUID of the user being followed (the target).",
        ),
        # Audit
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="UTC timestamp when the follow relationship was created.",
        ),
        # Constraints
        sa.UniqueConstraint(
            "follower_id",
            "following_id",
            name="uq_follows_follower_following",
        ),
        sa.CheckConstraint(
            "follower_id != following_id",
            name="ck_follows_no_self_follow",
        ),
    )

    # Indexes for query performance
    op.create_index(
        "ix_follows_follower_id",
        "follows",
        ["follower_id"],
        unique=False,
    )
    op.create_index(
        "ix_follows_following_id",
        "follows",
        ["following_id"],
        unique=False,
    )
    op.create_index(
        "ix_follows_created_at",
        "follows",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the follows table and all associated indexes/constraints."""

    op.drop_index("ix_follows_created_at", table_name="follows")
    op.drop_index("ix_follows_following_id", table_name="follows")
    op.drop_index("ix_follows_follower_id", table_name="follows")
    op.drop_table("follows")
