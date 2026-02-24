"""Unit tests for Claims CRUD operations."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.crud.claims.claim import create_claim, get_claim_by_id, list_claims
from app.models.claim import Claim
from app.models.member import Member
from app.enums import ClaimStatus
from app.utils.claim_validator import ClaimValidationError


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Mock async database session with flush/refresh/execute support."""
    db = AsyncMock()
    db.add = MagicMock()
    return db


def _mock_scalar_result(entity):
    """Helper: simulate result.scalars().first() or .all()."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = entity
    mock_result.scalars.return_value.all.return_value = [entity] if entity else []
    mock_result.scalar.return_value = 1 if entity else 0
    return mock_result


# ── create_claim Tests ────────────────────────────────────────────


class TestCreateClaim:
    """Tests for the create_claim CRUD function."""

    @pytest.mark.asyncio
    @patch("app.crud.claims.claim.ClaimValidator")
    async def test_approved_claim_updates_member_benefit(self, MockValidator, mock_db):
        """When claim is APPROVED, member.used_benefit should increase."""
        # Setup validator mock
        validator_instance = AsyncMock()
        validator_instance.validate_and_process_claim.return_value = (
            ClaimStatus.APPROVED,
            Decimal("15000.00"),
            False,
            None,
        )
        MockValidator.return_value = validator_instance

        # Mock the member lookup for benefit update
        mock_member = MagicMock(spec=Member)
        mock_member.id = "M123"
        mock_member.used_benefit = Decimal("10000.00")
        mock_db.execute.return_value = _mock_scalar_result(mock_member)

        await create_claim(
            db=mock_db,
            member_id="M123",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("15000.00"),
            notes="Test claim",
        )

        # Verify claim was added to session
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called()

        # Verify member benefit was updated
        assert mock_member.used_benefit == Decimal("25000.00")

    @pytest.mark.asyncio
    @patch("app.crud.claims.claim.ClaimValidator")
    async def test_partial_claim_updates_member_benefit(self, MockValidator, mock_db):
        """When claim is PARTIAL, member.used_benefit increases by approved_amount."""
        validator_instance = AsyncMock()
        validator_instance.validate_and_process_claim.return_value = (
            ClaimStatus.PARTIAL,
            Decimal("5000.00"),
            False,
            None,
        )
        MockValidator.return_value = validator_instance

        mock_member = MagicMock(spec=Member)
        mock_member.id = "M130"
        mock_member.used_benefit = Decimal("45000.00")
        mock_db.execute.return_value = _mock_scalar_result(mock_member)

        await create_claim(
            db=mock_db,
            member_id="M130",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("10000.00"),
        )

        assert mock_member.used_benefit == Decimal("50000.00")

    @pytest.mark.asyncio
    @patch("app.crud.claims.claim.ClaimValidator")
    async def test_rejected_fraud_claim_no_benefit_deduction(
        self, MockValidator, mock_db
    ):
        """REJECTED fraud claim should NOT update member benefit."""
        validator_instance = AsyncMock()
        validator_instance.validate_and_process_claim.return_value = (
            ClaimStatus.REJECTED,
            Decimal("0.00"),
            True,
            "Claim amount exceeds 2.0x average procedure cost",
        )
        MockValidator.return_value = validator_instance

        await create_claim(
            db=mock_db,
            member_id="M123",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("150000.00"),
        )

        mock_db.add.assert_called_once()
        added_claim = mock_db.add.call_args[0][0]
        assert added_claim.status == ClaimStatus.REJECTED
        assert added_claim.fraud_flag is True
        assert added_claim.approved_amount == Decimal("0.00")

    @pytest.mark.asyncio
    @patch("app.crud.claims.claim.ClaimValidator")
    async def test_validation_error_creates_rejected_claim(
        self, MockValidator, mock_db
    ):
        """ClaimValidationError should create a REJECTED claim with error message."""
        validator_instance = AsyncMock()
        validator_instance.validate_and_process_claim.side_effect = (
            ClaimValidationError("Member M999 not found")
        )
        MockValidator.return_value = validator_instance

        await create_claim(
            db=mock_db,
            member_id="M999",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("5000.00"),
        )

        mock_db.add.assert_called_once()
        added_claim = mock_db.add.call_args[0][0]
        assert added_claim.status == ClaimStatus.REJECTED
        assert added_claim.fraud_flag is False
        assert added_claim.approved_amount == Decimal("0.00")
        assert "not found" in added_claim.fraud_reason

    @pytest.mark.asyncio
    @patch("app.crud.claims.claim.ClaimValidator")
    async def test_notes_persisted(self, MockValidator, mock_db):
        """Notes field should be saved on the claim."""
        validator_instance = AsyncMock()
        validator_instance.validate_and_process_claim.return_value = (
            ClaimStatus.APPROVED,
            Decimal("5000.00"),
            False,
            None,
        )
        MockValidator.return_value = validator_instance

        mock_member = MagicMock(spec=Member)
        mock_member.used_benefit = Decimal("0.00")
        mock_db.execute.return_value = _mock_scalar_result(mock_member)

        await create_claim(
            db=mock_db,
            member_id="M123",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("5000.00"),
            notes="Emergency appendectomy",
        )

        added_claim = mock_db.add.call_args[0][0]
        assert added_claim.notes == "Emergency appendectomy"


# ── get_claim_by_id Tests ─────────────────────────────────────────


class TestGetClaimById:
    """Tests for the get_claim_by_id CRUD function."""

    @pytest.mark.asyncio
    async def test_returns_claim_when_found(self, mock_db):
        """Should return the claim when it exists."""
        claim_id = uuid4()
        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = claim_id
        mock_db.execute.return_value = _mock_scalar_result(mock_claim)

        result = await get_claim_by_id(mock_db, claim_id)

        assert result == mock_claim
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_db):
        """Should return None for nonexistent claim ID."""
        mock_db.execute.return_value = _mock_scalar_result(None)

        result = await get_claim_by_id(mock_db, uuid4())

        assert result is None


# ── list_claims Tests ─────────────────────────────────────────────


class TestListClaims:
    """Tests for the list_claims CRUD function."""

    @pytest.mark.asyncio
    async def test_returns_claims_and_count(self, mock_db):
        """Should return list of claims and total count."""
        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = uuid4()

        # First execute returns claims, second returns count
        claims_result = MagicMock()
        claims_result.scalars.return_value.all.return_value = [mock_claim]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [count_result, claims_result]

        claims, total = await list_claims(mock_db)

        assert total == 1
        assert len(claims) == 1
        assert claims[0] == mock_claim

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_db):
        """Should return empty list and zero count when no claims match."""
        claims_result = MagicMock()
        claims_result.scalars.return_value.all.return_value = []

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [count_result, claims_result]

        claims, total = await list_claims(mock_db)

        assert total == 0
        assert len(claims) == 0

    @pytest.mark.asyncio
    async def test_filters_passed_to_query(self, mock_db):
        """Verify that filter parameters are accepted without error."""
        claims_result = MagicMock()
        claims_result.scalars.return_value.all.return_value = []

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [count_result, claims_result]

        claims, total = await list_claims(
            mock_db,
            member_id="M123",
            provider_id="H456",
            status=ClaimStatus.APPROVED,
            skip=0,
            limit=20,
        )

        assert total == 0
        assert mock_db.execute.call_count == 2
