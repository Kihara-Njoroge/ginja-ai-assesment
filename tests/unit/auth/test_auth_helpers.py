import pytest
from datetime import datetime, timezone, timedelta
from app.utils.auth_helpers import (
    create_access_token,
    create_refresh_token,
    decode_token,
    update_access_token,
    get_session_id_for_user,
)
from app.models.user import User
from app.enums import UserRole
import uuid
from jose import jwt
from app.config import get_settings

settings = get_settings()


@pytest.fixture
def sample_user():
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        phone_number="1234567890",
        first_name="Test",
        last_name="User",
        role=UserRole.USER,
    )
    return user


def test_session_id_generation(sample_user):
    session_id = get_session_id_for_user(sample_user)
    assert isinstance(session_id, str)
    assert len(session_id) > 0


def test_create_access_token(sample_user):
    session_id = get_session_id_for_user(sample_user)
    token = create_access_token(sample_user, session_id=session_id)

    # Verify token payload
    payload = decode_token(token, force_access=True, force_refresh=False)
    assert payload["user_id"] == str(sample_user.id)
    assert payload["type"] == "access"
    assert payload["session_id"] == session_id
    assert "exp" in payload


def test_create_refresh_token(sample_user):
    session_id = get_session_id_for_user(sample_user)
    token = create_refresh_token(sample_user, session_id=session_id)

    # Verify token payload
    payload = decode_token(token, force_access=False, force_refresh=True)
    assert payload["user_id"] == str(sample_user.id)
    assert payload["type"] == "refresh"
    assert payload["session_id"] == session_id
    assert "exp" in payload


def test_update_access_token(sample_user):
    session_id = get_session_id_for_user(sample_user)
    token = create_access_token(sample_user, session_id=session_id)

    # Update token with custom claim
    updated_token = update_access_token(
        token, force_access=True, force_refresh=False, custom_claim="hello"
    )

    payload = decode_token(updated_token, force_access=True, force_refresh=False)
    assert payload["custom_claim"] == "hello"


def test_decode_token_invalid_type(sample_user):
    session_id = get_session_id_for_user(sample_user)
    access_token = create_access_token(sample_user, session_id=session_id)
    refresh_token = create_refresh_token(sample_user, session_id=session_id)

    from fastapi import HTTPException

    # Try decoding access token as refresh token
    with pytest.raises(HTTPException) as exc:
        decode_token(access_token, force_access=False, force_refresh=True)
    assert exc.value.status_code == 401

    # Try decoding refresh token as access token
    with pytest.raises(HTTPException) as exc:
        decode_token(refresh_token, force_access=True, force_refresh=False)
    assert exc.value.status_code == 401
