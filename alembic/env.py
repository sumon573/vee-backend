import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Load .env so DATABASE_URL is available when running locally
load_dotenv()

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import Base and all models so Alembic can detect schema changes.
# Add model imports here as new models are created in future phases:
#
#   from app.models.room import Room       # Phase 6
#
# ---------------------------------------------------------------------------
from app.db.base import Base  # noqa: E402
from app.models.user import User  # noqa: F401 — Phase 4: registers users table
from app.models.follow import Follow  # noqa: F401 — Phase 7: registers follows table
from app.models.block import Block  # noqa: F401 — Phase 8: registers blocks table
from app.utils.db_url import normalize_database_url  # noqa: E402

target_metadata = Base.metadata


def get_url() -> str:
    """Resolve and normalize the database URL."""
    raw = os.environ.get(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url", ""),
    )
    return normalize_database_url(raw)


# ---------------------------------------------------------------------------
# Offline mode — generates SQL without connecting to the database
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — connects to the database and applies migrations
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = get_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
