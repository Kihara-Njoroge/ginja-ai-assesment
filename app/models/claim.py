import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.provider import Provider

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import ClaimStatus


class Claim(Base):
    """Health insurance claim model."""

    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    member_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("members.id"), nullable=False, index=True
    )
    provider_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("providers.id"), nullable=False, index=True
    )
    diagnosis_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("diagnoses.code"), nullable=False
    )
    procedure_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("procedures.code"), nullable=False
    )

    # Claim details
    claim_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    approved_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    status: Mapped[ClaimStatus] = mapped_column(
        Enum(
            ClaimStatus,
            name="claim_status_enum",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=ClaimStatus.PENDING,
        nullable=False,
        server_default=ClaimStatus.PENDING.value,
        index=True,
    )

    # Fraud detection
    fraud_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    fraud_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="claims")
    provider: Mapped["Provider"] = relationship("Provider", back_populates="claims")

    def __repr__(self) -> str:
        return f"<Claim {self.id} - {self.status.value}>"
