import pytest
import uuid
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


async def test_register_user_success(client, mock_db_session, mocker):
    mocker.patch("app.views.auth.users.validate_email_unique", return_value=None)
    mocker.patch("app.views.auth.users.validate_phone_unique", return_value=None)

    mock_user = AsyncMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "test@example.com"
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.username = None
    mock_user.phone_number = "+254712345678"
    mock_user.status = "inactive"
    mock_user.role = "user"
    mock_user.is_superuser = False
    mock_user.identifier = None

    mocker.patch("app.views.auth.users.create_user", return_value=mock_user)

    response = await client.post(
        "/users",
        json={
            "email": "test@example.com",
            "password": "Password123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+254712345678",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"


async def test_register_user_email_exists(client, mock_db_session, mocker):
    from app.models.user import EmailAlreadyExistsError

    mocker.patch(
        "app.views.auth.users.validate_email_unique",
        side_effect=EmailAlreadyExistsError("test@example.com"),
    )

    response = await client.post(
        "/users",
        json={
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 400
    assert "test@example.com is already registered" in response.json()["detail"]


async def test_get_users(client, mock_db_session, mocker):
    mock_user = AsyncMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "test@example.com"
    mock_user.status = "inactive"
    mock_user.role = "user"
    mock_user.is_superuser = False
    mock_user.identifier = None
    mock_user.username = None
    mock_user.first_name = None
    mock_user.last_name = None
    mock_user.phone_number = None

    mocker.patch("app.views.auth.users.get_users", return_value=[mock_user])

    response = await client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["email"] == "test@example.com"
    assert data["page_info"]["total"] == 1


async def test_get_user_not_found(client, mock_db_session, mocker):
    mocker.patch("app.views.auth.users.get_user_by_id", return_value=None)

    response = await client.get(f"/users/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
