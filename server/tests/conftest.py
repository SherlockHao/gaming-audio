import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.models import Base, Project
from app.database import get_db
from app.main import create_app

TEST_DB_URL = "postgresql+asyncpg://gaming_audio:gaming_audio_dev@localhost:5433/gaming_audio_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

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
    async with test_session_factory() as session:
        yield session
        await session.rollback()

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
