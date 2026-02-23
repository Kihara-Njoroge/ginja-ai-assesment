import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from app.main import create_app
from app.config import get_settings
from app.database import get_db
from app.utils.auth_helpers import get_auth_user
from app.models.user import User
import uuid


@pytest.fixture
def app():
    app_instance = create_app()
    return app_instance


@pytest_asyncio.fixture
async def client(app):
    settings = get_settings()
    prefix = getattr(settings, "APP_PREFIX", "")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{prefix}"
    ) as c:
        yield c


@pytest.fixture
def mock_db_session(app):
    session = AsyncMock()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_auth_user_override(app):
    mock_user = User(id=uuid.uuid4(), email="authtest@example.com", status="ACTIVE")
    app.dependency_overrides[get_auth_user] = lambda: mock_user
    yield mock_user
    if get_auth_user in app.dependency_overrides:
        del app.dependency_overrides[get_auth_user]
