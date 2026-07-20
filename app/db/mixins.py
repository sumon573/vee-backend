"""
Reusable SQLAlchemy 2.x declarative mixins.

Usage:
    class MyModel(UUIDMixin, TimestampMixin, Base):
        __tablename__ = "my_table"
        ...

Rules:
- Mixins must come before Base in the MRO.
- Never add business logic here; mixins are pure schema helpers.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Adds a UUID v4 primary key column `id` to any model."""

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="UUID v4 primary key — generated client-side by Python.",
    )


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` audit timestamp columns.

    - `created_at` is set once by the database server on INSERT.
    - `updated_at` is refreshed by the ORM on every UPDATE via `onupdate`.
      For server-side refresh, add a DB trigger in a future migration if needed.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of row creation (set by DB server).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update (refreshed by ORM on UPDATE).",
    )
