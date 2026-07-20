from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_database_url(url: str) -> str:
    """
    Normalize a PostgreSQL connection URL for use with asyncpg.

    1. Replaces ``postgres://`` / ``postgresql://`` scheme with
       ``postgresql+asyncpg://`` (required by SQLAlchemy async engine).
    2. Strips ``sslmode`` from the query string — asyncpg does not accept
       psycopg2-style ``sslmode`` parameters and raises TypeError if present.
       Use ``connect_args={"ssl": ...}`` on the engine if SSL control is
       needed at the driver level.
    """
    # Normalise scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Strip asyncpg-incompatible query parameters
    parsed = urlparse(url)
    _UNSUPPORTED = {"sslmode", "sslcert", "sslkey", "sslrootcert"}
    params = {
        k: v[0]
        for k, v in parse_qs(parsed.query).items()
        if k not in _UNSUPPORTED
    }
    return urlunparse(parsed._replace(query=urlencode(params)))
