import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import VerificationTypeEnum

if TYPE_CHECKING:
    from app.models.user import User


class VerificationToken(Base):
    """Token model for authentication and verification workflows."""

    __tablename__ = "verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False, index=True
    )
    token_type: Mapped[VerificationTypeEnum] = mapped_column(
        Enum(VerificationTypeEnum, name="verification_type_enum", create_type=False),
        nullable=False,
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="verification_tokens")

    def __repr__(self) -> str:
        return f"<VerificationToken {self.token_type} for User {self.user_id}>"

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired based on current UTC time."""
        from datetime import timezone

        return datetime.now(timezone.utc) > self.expires_at
