import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.models import Base, Project
from app.database import get_db
from app.main import create_app

import os

TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://gaming_audio:gaming_audio_dev@localhost:5433/gaming_audio_test",
)

test_engine = create_async_engine(TEST_DB_URL, echo=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    """
    Provide a test DB session wrapped in a transaction that is always rolled back.
    Service-level commit() calls are replaced with flush() so no data escapes
    the outer transaction, giving full test isolation without hitting the DB more
    than needed.
    """
    async with test_engine.connect() as conn:
        # Begin a real transaction — we will roll it back at the end
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        # Replace commit with flush so service code "commits" but the outer
        # transaction is never actually committed
        original_commit = session.commit
        async def nested_commit():
            try:
                await session.flush()
            except Exception:
                await session.rollback()
                raise
        session.commit = nested_commit

        yield session

        # Restore original and tear down
        session.commit = original_commit
        await session.close()
        await trans.rollback()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    app = create_app()
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession) -> Project:
    project = Project(name="Test Action Game")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project
