from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

# Detect if using async SQLite or sync PostgreSQL
if "sqlite" in settings.database_url and "aiosqlite" in settings.database_url:
    # Async SQLite for testing
    engine = create_async_engine(settings.database_url.replace("sqlite+aiosqlite", "sqlite+aiosqlite"), echo=False)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)
    
    async def get_db():
        async with SessionLocal() as session:
            yield session
else:
    # Sync PostgreSQL for production
    engine = create_engine(settings.database_url.replace("+asyncpg", "").replace("+psycopg", ""), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    
    def get_db():
        with SessionLocal() as session:
            yield session
