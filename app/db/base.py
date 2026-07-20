from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Declarative base class for all ORM models.

    All models must inherit from this class so that Alembic can
    auto-detect them during migration generation.
    """

    pass
