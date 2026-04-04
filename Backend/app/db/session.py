from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine_kwargs = {}

if not str(settings.database_url).lower().startswith("sqlite"):
    engine_kwargs = {
        "pool_size": max(1, int(settings.db_pool_size)),
        "max_overflow": max(0, int(settings.db_max_overflow)),
        "pool_timeout": max(1, int(settings.db_pool_timeout_seconds)),
        "pool_recycle": max(60, int(settings.db_pool_recycle_seconds)),
        "pool_pre_ping": bool(settings.db_pool_pre_ping),
        "pool_use_lifo": True,
    }

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)