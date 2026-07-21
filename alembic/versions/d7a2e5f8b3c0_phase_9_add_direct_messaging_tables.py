"""phase_9_add_direct_messaging_tables

Revision ID: d7a2e5f8b3c0
Revises: c4f8e3b2d9a1
Create Date: 2026-07-21 00:00:00.000000

Phase 9 — Direct Messaging Foundation.

Creates:
    - message_type_enum   — PostgreSQL ENUM for message content types
    - conversations       — one-to-one messaging channels
    - conversation_participants — junction table (composite PK: conversation_id, user_id)
    - messages            — individual messages within a conversation

Constraints:
    - conversation_participants: both FK columns CASCADE DELETE
    - messages: both FK columns CASCADE DELETE
    - messages.is_deleted defaults to false (soft-delete flag)
    - messages.content is nullable (NULLed on soft-delete)

Indexes:
    - ix_conversation_participants_user_id  — list conversations for a user
    - ix_messages_conversation_id           — list messages in a conversation
    - ix_messages_sender_id                 — messages sent by a user
    - ix_messages_created_at                — chronological ordering
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d7a2e5f8b3c0"
down_revision: str | None = "c4f8e3b2d9a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# PostgreSQL native ENUM types managed by this migration
message_type_enum = postgresql.ENUM(
    "text",
    name="message_type_enum",
    create_type=False,
)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create message_type_enum PostgreSQL native ENUM
    # ------------------------------------------------------------------
    message_type_enum.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # 2. conversations table
    # ------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="UTC timestamp of conversation creation (set by DB server).",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment="UTC timestamp of last conversation update (set by DB server).",
        ),
    )

    # ------------------------------------------------------------------
    # 3. conversation_participants junction table
    #    Composite PK: (conversation_id, user_id) — no separate UUID needed.
    # ------------------------------------------------------------------
    op.create_table(
        "conversation_participants",
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
            comment="FK → conversations.id; part of composite PK.",
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
            comment="FK → users.id; part of composite PK.",
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="UTC timestamp when the participant joined the conversation.",
        ),
    )

    op.create_index(
        "ix_conversation_participants_user_id",
        "conversation_participants",
        ["user_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # 4. messages table
    # ------------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key.",
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            comment="FK → conversations.id.",
        ),
        sa.Column(
            "sender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="FK → users.id; the message author.",
        ),
        sa.Column(
            "content",
            sa.Text,
            nullable=True,
            comment="Message body. Nullable — set to NULL on soft-delete.",
        ),
        sa.Column(
            "message_type",
            message_type_enum,
            nullable=False,
            server_default="text",
            comment="Message content type (text, future: audio, image).",
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean,
            nullable=False,
            server_default="false",
            comment="Soft-delete flag; content is NULLed when True.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="UTC timestamp of message creation (set by DB server).",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment="UTC timestamp of last message update (set by DB server).",
        ),
    )

    op.create_index(
        "ix_messages_conversation_id",
        "messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_messages_sender_id",
        "messages",
        ["sender_id"],
        unique=False,
    )
    op.create_index(
        "ix_messages_created_at",
        "messages",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index(
        "ix_conversation_participants_user_id",
        table_name="conversation_participants",
    )
    op.drop_table("conversation_participants")

    op.drop_table("conversations")

    message_type_enum.drop(op.get_bind(), checkfirst=True)
