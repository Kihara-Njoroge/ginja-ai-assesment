import pytest
from fastapi import HTTPException
from app.models.user import User


def test_user_initialization():
    user = User(email="test@example.com", first_name="john", last_name="doe")
    assert user.email == "test@example.com"
    assert user.name == "John Doe"
    # SQLAlchemy defaults are normally applied upon session flush, not instantiation.
    # Therefore, they will be None here unless explicitly passed.
    assert user.status is None
    assert user.is_active is False


def test_user_password_setter_getter_disabled():
    user = User(email="test@example.com")

    with pytest.raises(ValueError, match="Cannot access this value directly"):
        _ = user.password

    with pytest.raises(ValueError, match="Cannot set password value directly"):
        user.password = "newpass"


def test_user_set_check_password_valid():
    user = User(email="test@example.com")
    user.set_password("Valid123!")

    assert user.check_password("Valid123!") is True
    assert user.check_password("invalid") is False


def test_user_set_password_invalid_length():
    user = User(email="test@example.com")
    with pytest.raises(HTTPException) as exc:
        user.set_password("short1A")
    assert exc.value.status_code == 400
    assert "least 8 characters" in exc.value.detail["error"]


def test_user_set_password_missing_complexity():
    user = User(email="test@example.com")
    with pytest.raises(HTTPException) as exc:
        user.set_password("alllowercase123")
    assert exc.value.status_code == 400
    assert "contain one uppercase" in exc.value.detail["error"]


def test_user_name_capitalization_handling():
    user = User(email="test@example.com")
    assert user.name is None

    user.first_name = "jane"
    assert user.name == "Jane"

    user.last_name = "SMITH"
    assert user.name == "Jane Smith"
