from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import Base
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    Движок для тестов — создаётся один раз.

    NullPool: каждое соединение живёт только для одной сессии
    и не переиспользуется. Это исключает конфликты между
    тестовой сессией и сессией внутри приложения.
    """
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine):
    """
    Фабрика сессий для подготовки данных.

    Каждый вызов session_factory() открывает новую сессию
    на новом соединении и закрывает её при выходе из контекста.
    """
    factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield factory


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент к приложению (in-process)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac