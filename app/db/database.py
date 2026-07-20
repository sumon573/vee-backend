from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.utils.db_url import normalize_database_url

engine: AsyncEngine = create_async_engine(
    normalize_database_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,   # verify connections before checkout
    pool_size=10,         # maintained pool connections
    max_overflow=20,      # extra connections allowed beyond pool_size
    pool_recycle=3600,    # recycle connections every hour
)
