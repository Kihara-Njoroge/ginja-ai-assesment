from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.claim import Claim

from sqlalchemy import DateTime, Enum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import MemberStatus


class Member(Base):
    """Insurance member model."""

    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    status: Mapped[MemberStatus] = mapped_column(
        Enum(
            MemberStatus,
            name="member_status_enum",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=MemberStatus.ACTIVE,
        nullable=False,
        server_default=MemberStatus.ACTIVE.value,
    )

    # Benefit limits
    benefit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("100000.00")
    )
    used_benefit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="member", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Member {self.id} - {self.name}>"

    @property
    def remaining_benefit(self) -> Decimal:
        """Calculate remaining benefit amount."""
        return self.benefit_limit - self.used_benefit

    @property
    def is_eligible(self) -> bool:
        """Check if member is eligible for claims."""
        return self.status == MemberStatus.ACTIVE and self.remaining_benefit > 0
