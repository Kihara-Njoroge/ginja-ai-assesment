import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
import uuid

from app.models.user import User
from app.enums import UserStatus
from app.models.token import VerificationToken


@pytest.mark.asyncio
async def test_request_otp_nonexistent_user(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test requesting OTP for a username that does not exist in the DB.
    Should return a generic message to prevent user-enumeration attacks.
    """
    mocker.patch(
        "app.views.auth.verification.get_user_by_phone_or_email",
        new_callable=AsyncMock,
        return_value=None,
    )

    response = await client.post(
        "/auth/verify/request", json={"username": "nonexistent@example.com"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If the username exists, an OTP has been sent."
    }


@pytest.mark.asyncio
async def test_request_otp_existing_user(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test requesting OTP for an existing user.
    """
    mock_user = User(
        id=uuid.uuid4(), email="test@example.com", phone_number="1234567890"
    )
    mocker.patch(
        "app.views.auth.verification.get_user_by_phone_or_email",
        new_callable=AsyncMock,
        return_value=mock_user,
    )

    mock_create_otp = mocker.patch(
        "app.views.auth.verification.create_otp_for_user", new_callable=AsyncMock
    )
    mock_create_otp.return_value = (VerificationToken(), "123456")

    response = await client.post(
        "/auth/verify/request", json={"username": "test@example.com"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If the username exists, an OTP has been sent."
    }
    mock_create_otp.assert_called_once()


@pytest.mark.asyncio
async def test_validate_otp_success(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test successfully validating the OTP and receiving tokens.
    """
    mock_user = User(
        id=uuid.uuid4(), email="test@example.com", status=UserStatus.ACTIVE
    )

    # Mock the auth helper to successfully authenticate the user
    mock_authenticate = mocker.patch(
        "app.views.auth.verification.authenticate_user_via_otp",
        new_callable=AsyncMock,
        return_value=mock_user,
    )

    response = await client.post(
        "/auth/verify/validate", json={"username": "test@example.com", "otp": "123456"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    mock_authenticate.assert_called_once_with(
        mock_db_session, username="test@example.com", otp="123456"
    )


@pytest.mark.asyncio
async def test_validate_otp_invalid(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test validating an invalid OTP.
    """
    from fastapi import HTTPException

    # Mock authenticate to throw an HTTPException
    mock_authenticate = mocker.patch(
        "app.views.auth.verification.authenticate_user_via_otp",
        new_callable=AsyncMock,
    )
    mock_authenticate.side_effect = HTTPException(
        status_code=401, detail="Invalid or expired OTP"
    )

    response = await client.post(
        "/auth/verify/validate", json={"username": "test@example.com", "otp": "wrong"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired OTP"}


@pytest.mark.asyncio
async def test_resend_otp(client: AsyncClient, mock_db_session: AsyncMock, mocker):
    """
    Test resending an OTP for an existing user.
    """
    mock_user = User(id=uuid.uuid4(), email="test@example.com")
    mocker.patch(
        "app.views.auth.verification.get_user_by_phone_or_email",
        new_callable=AsyncMock,
        return_value=mock_user,
    )

    mock_create_otp = mocker.patch(
        "app.views.auth.verification.create_otp_for_user", new_callable=AsyncMock
    )
    mock_create_otp.return_value = (VerificationToken(), "654321")

    response = await client.post(
        "/auth/verify/resend", json={"username": "test@example.com"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If the username exists, an OTP has been sent."
    }
    mock_create_otp.assert_called_once()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, mock_db_session: AsyncMock, mocker):
    """
    Test successful username and password login.
    """
    mock_user = User(
        id=uuid.uuid4(), email="test@example.com", status=UserStatus.ACTIVE
    )

    # Mock authenticate_user to return mock_user
    mock_authenticate = mocker.patch(
        "app.views.auth.verification.authenticate_user",
        new_callable=AsyncMock,
        return_value=mock_user,
    )

    response = await client.post(
        "/auth/login",
        json={"username": "test@example.com", "password": "StrongPassword123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    mock_authenticate.assert_called_once_with(
        mock_db_session, username="test@example.com", password="StrongPassword123!"
    )


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient, mock_db_session: AsyncMock, mocker):
    """
    Test invalid login credentials.
    """
    from fastapi import HTTPException

    mock_authenticate = mocker.patch(
        "app.views.auth.verification.authenticate_user", new_callable=AsyncMock
    )
    mock_authenticate.side_effect = HTTPException(
        status_code=401, detail="Invalid credentials"
    )

    response = await client.post(
        "/auth/login",
        json={"username": "test@example.com", "password": "WrongPassword"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_refresh_token_success(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test refreshing token.
    """
    from app.utils.auth_helpers import create_refresh_token, get_session_id_for_user

    mock_user = User(
        id=uuid.uuid4(), email="test@example.com", status=UserStatus.ACTIVE
    )
    session_id = get_session_id_for_user(mock_user)

    # Create an actual refresh token for validation
    real_refresh_token = create_refresh_token(mock_user, session_id=session_id)

    mocker.patch(
        "app.crud.auth.user.get_user_by_id",
        new_callable=AsyncMock,
        return_value=mock_user,
    )

    response = await client.post(
        "/auth/refresh", json={"refresh_token": real_refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
