"""
Database connection — supports both PostgreSQL (production) and SQLite (development/free tier).
SQLite requires no external service and works immediately.
Switch to PostgreSQL by setting DB_HOST in .env.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import structlog

from backend.utils.config import settings

log = structlog.get_logger()

engine = None
AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass


def _build_database_url() -> str:
    """
    Build the database URL based on configuration.
    - If DB_HOST is set → use PostgreSQL (production)
    - Otherwise → use SQLite (development / free tier)
    """
    if settings.DB_HOST and settings.DB_HOST not in ("localhost", "your_postgres_host", ""):
        # PostgreSQL
        ssl_suffix = "?ssl=require" if settings.DB_SSL_MODE == "require" else ""
        url = (
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}{ssl_suffix}"
        )
        log.info("Using PostgreSQL database", host=settings.DB_HOST)
        return url
    else:
        # SQLite — works with no external service
        import pathlib
        db_path = pathlib.Path("./data/migrant_welfare.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        log.info("Using SQLite database (development mode)", path=str(db_path))
        return f"sqlite+aiosqlite:///{db_path}"


async def init_db():
    global engine, AsyncSessionLocal

    db_url = _build_database_url()
    is_sqlite = db_url.startswith("sqlite")

    engine = create_async_engine(
        db_url,
        echo=settings.BACKEND_DEBUG,
        # SQLite does not support pool_size/max_overflow
        **({} if is_sqlite else {"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True})
    )
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Auto-create tables in SQLite (dev mode)
    if is_sqlite:
        from backend.database.models import Base as ModelBase
        async with engine.begin() as conn:
            await conn.run_sync(ModelBase.metadata.create_all)
        log.info("SQLite tables created/verified")


async def close_db():
    global engine
    if engine:
        await engine.dispose()
        log.info("Database connection pool closed")


async def get_db():
    """FastAPI dependency — yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
