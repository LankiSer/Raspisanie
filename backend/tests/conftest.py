"""Test configuration and fixtures."""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.auth import get_password_hash
from app.models import Organization, User, UserRole


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create test session factory."""
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(test_session_factory):
    """Create test database session."""
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def test_organization(db_session: AsyncSession):
    """Create test organization."""
    org = Organization(
        name="Test University",
        locale="ru",
        tz="Europe/Moscow"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_admin_user(db_session: AsyncSession, test_organization):
    """Create test admin user."""
    user = User(
        org_id=test_organization.org_id,
        email="admin@test.edu",
        password_hash=get_password_hash("testpass"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_methodist_user(db_session: AsyncSession, test_organization):
    """Create test methodist user."""
    user = User(
        org_id=test_organization.org_id,
        email="methodist@test.edu",
        password_hash=get_password_hash("testpass"),
        role=UserRole.METHODIST,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client(db_session):
    """Create test client with database override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_auth_headers(client: AsyncClient, test_admin_user):
    """Get authentication headers for admin user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": test_admin_user.email,
        "password": "testpass"
    })
    assert response.status_code == 200
    
    data = response.json()
    token = data["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def methodist_auth_headers(client: AsyncClient, test_methodist_user):
    """Get authentication headers for methodist user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": test_methodist_user.email,
        "password": "testpass"
    })
    assert response.status_code == 200
    
    data = response.json()
    token = data["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
