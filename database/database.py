from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Асинхронное подключение (для бота и FastAPI)
DATABASE_URL = os.getenv("DATABASE_URL")
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Синхронное подключение (для Alembic миграций)
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")
sync_engine = create_engine(DATABASE_URL_SYNC, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def get_async_session():
    """Dependency для получения асинхронной сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Dependency для получения синхронной сессии БД"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def init_db():
    """Инициализация базы данных (создание таблиц)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully")


async def close_db():
    """Закрытие соединения с БД"""
    await async_engine.dispose()
    print("✅ Database connection closed")
