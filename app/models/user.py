import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from fastapi import HTTPException

from app.database import Base
from app.enums import UserRole, UserStatus


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Contact info
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )

    # Profile
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Auth
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status & Roles
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_type=False),
        default=UserRole.USER,
        nullable=False,
        server_default=UserRole.USER.value,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status_enum", create_type=False),
        default=UserStatus.INACTIVE,
        nullable=False,
        server_default=UserStatus.INACTIVE.value,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="user", cascade="all, delete-orphan"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

    @property
    def is_active(self) -> bool:
        """Helper property to check if user can log in."""
        return self.status == UserStatus.ACTIVE

    @property
    def password(self):
        raise ValueError("Cannot access this value directly")

    @password.setter
    def password(self, value):
        raise ValueError("Cannot set password value directly. Use cls.set_password")

    def set_password(self, password: str) -> "User":
        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail={"error": "Password must be at least 8 characters long."},
            )

        if not (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
        ):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Password must contain one uppercase letter (A-Z), one lowercase letter (a-z) and at least one digit (0-9)."
                },
            )

        from passlib.hash import bcrypt

        self.hashed_password = bcrypt.hash(password)
        return self

    def check_password(self, password: str) -> bool:
        """Returns true if the password matches."""
        if not self.hashed_password:
            return False

        from passlib.hash import bcrypt

        return bcrypt.verify(password, self.hashed_password)

    @property
    def name(self):
        """Returns the full capitalized name or None."""
        if not self.first_name and not self.last_name:
            return None

        name = " ".join(
            n.capitalize() for n in [self.first_name or "", self.last_name or ""] if n
        ).strip()

        return name if name else None


# Custom exception for business logic validation
class EmailAlreadyExistsError(Exception):
    """Raised when attempting to register with an email that already exists"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} is already registered")


class PhoneAlreadyExistsError(Exception):
    """Raised when attempting to register with a phone number that already exists"""

    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        super().__init__(f"Phone Number {phone_number} already exists")


# Service layer validation function
async def validate_email_unique(db, email: str, exclude_user_id: Optional[str] = None):
    """
    Validate that email is unique in the database

    Args:
        db: AsyncSession database connection
        email: Email to validate
        exclude_user_id: Optional user ID to exclude from uniqueness check (for updates)

    Raises:
        EmailAlreadyExistsError: If email already exists
    """
    from sqlalchemy.future import select

    query = select(User).where(User.email == email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user and (
        not exclude_user_id or str(existing_user.id) != exclude_user_id
    ):
        raise EmailAlreadyExistsError(email)


async def validate_phone_unique(
    db, phone_number: str, exclude_user_id: Optional[str] = None
):
    """
    Validate that phone_number is unique in the database

    Args:
        db: AsyncSession database connection
        phone_number: Phone Number to validate
        exclude_user_id: Optional user ID to exclude from uniqueness check (for updates)

    Raises:
        PhoneAlreadyExistsError: If phone already exists
    """
    from sqlalchemy.future import select

    query = select(User).where(User.phone_number == phone_number)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user and (
        not exclude_user_id or str(existing_user.id) != exclude_user_id
    ):
        raise PhoneAlreadyExistsError(phone_number)
