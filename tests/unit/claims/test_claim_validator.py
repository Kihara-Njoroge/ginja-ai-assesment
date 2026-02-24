"""Unit tests for ClaimValidator business logic."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.utils.claim_validator import ClaimValidator, ClaimValidationError
from app.models.member import Member
from app.models.provider import Provider
from app.models.procedure import Procedure
from app.models.diagnosis import Diagnosis
from app.enums import ClaimStatus, MemberStatus


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    return AsyncMock()


@pytest.fixture
def validator(mock_db):
    """Create a ClaimValidator with mocked session."""
    return ClaimValidator(mock_db)


@pytest.fixture
def active_member():
    """Member who is active with remaining benefits."""
    member = MagicMock(spec=Member)
    member.id = "M123"
    member.status = MemberStatus.ACTIVE
    member.benefit_limit = Decimal("100000.00")
    member.used_benefit = Decimal("20000.00")
    member.remaining_benefit = Decimal("80000.00")
    return member


@pytest.fixture
def inactive_member():
    """Member who is inactive."""
    member = MagicMock(spec=Member)
    member.id = "M125"
    member.status = MemberStatus.INACTIVE
    member.benefit_limit = Decimal("75000.00")
    member.used_benefit = Decimal("0.00")
    member.remaining_benefit = Decimal("75000.00")
    return member


@pytest.fixture
def exhausted_member():
    """Member who has exhausted their benefit limit."""
    member = MagicMock(spec=Member)
    member.id = "M126"
    member.status = MemberStatus.ACTIVE
    member.benefit_limit = Decimal("50000.00")
    member.used_benefit = Decimal("50000.00")
    member.remaining_benefit = Decimal("0.00")
    return member


@pytest.fixture
def active_provider():
    """Active healthcare provider."""
    provider = MagicMock(spec=Provider)
    provider.id = "H456"
    provider.is_active = True
    return provider


@pytest.fixture
def inactive_provider():
    """Inactive healthcare provider."""
    provider = MagicMock(spec=Provider)
    provider.id = "H458"
    provider.is_active = False
    return provider


@pytest.fixture
def sample_diagnosis():
    """Sample diagnosis record."""
    diagnosis = MagicMock(spec=Diagnosis)
    diagnosis.code = "D001"
    diagnosis.name = "Malaria"
    return diagnosis


@pytest.fixture
def sample_procedure():
    """Sample procedure with known average cost."""
    procedure = MagicMock(spec=Procedure)
    procedure.code = "P001"
    procedure.name = "General Consultation"
    procedure.average_cost = Decimal("5000.00")
    return procedure


def _mock_scalar_result(entity):
    """Helper: build a mock that simulates `result.scalars().first()` returning entity."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = entity
    return mock_result


# ── Member Validation Tests ───────────────────────────────────────


class TestValidateMember:
    """Tests for ClaimValidator._validate_member."""

    @pytest.mark.asyncio
    async def test_active_member_passes(self, validator, mock_db, active_member):
        mock_db.execute.return_value = _mock_scalar_result(active_member)

        result = await validator._validate_member("M123")

        assert result == active_member
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_member_not_found_raises(self, validator, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(ClaimValidationError, match="not found"):
            await validator._validate_member("M999")

    @pytest.mark.asyncio
    async def test_inactive_member_raises(self, validator, mock_db, inactive_member):
        mock_db.execute.return_value = _mock_scalar_result(inactive_member)

        with pytest.raises(ClaimValidationError, match="not active"):
            await validator._validate_member("M125")

    @pytest.mark.asyncio
    async def test_exhausted_benefit_raises(self, validator, mock_db, exhausted_member):
        mock_db.execute.return_value = _mock_scalar_result(exhausted_member)

        with pytest.raises(ClaimValidationError, match="exhausted"):
            await validator._validate_member("M126")


# ── Provider Validation Tests ─────────────────────────────────────


class TestValidateProvider:
    """Tests for ClaimValidator._validate_provider."""

    @pytest.mark.asyncio
    async def test_active_provider_passes(self, validator, mock_db, active_provider):
        mock_db.execute.return_value = _mock_scalar_result(active_provider)

        result = await validator._validate_provider("H456")

        assert result == active_provider

    @pytest.mark.asyncio
    async def test_provider_not_found_raises(self, validator, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(ClaimValidationError, match="not found"):
            await validator._validate_provider("H999")

    @pytest.mark.asyncio
    async def test_inactive_provider_raises(
        self, validator, mock_db, inactive_provider
    ):
        mock_db.execute.return_value = _mock_scalar_result(inactive_provider)

        with pytest.raises(ClaimValidationError, match="not active"):
            await validator._validate_provider("H458")


# ── Diagnosis Validation Tests ────────────────────────────────────


class TestValidateDiagnosis:
    """Tests for ClaimValidator._validate_diagnosis."""

    @pytest.mark.asyncio
    async def test_valid_diagnosis_passes(self, validator, mock_db, sample_diagnosis):
        mock_db.execute.return_value = _mock_scalar_result(sample_diagnosis)

        result = await validator._validate_diagnosis("D001")

        assert result == sample_diagnosis

    @pytest.mark.asyncio
    async def test_unknown_diagnosis_raises(self, validator, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(ClaimValidationError, match="not found"):
            await validator._validate_diagnosis("D999")


# ── Procedure Validation Tests ────────────────────────────────────


class TestValidateProcedure:
    """Tests for ClaimValidator._validate_procedure."""

    @pytest.mark.asyncio
    async def test_valid_procedure_passes(self, validator, mock_db, sample_procedure):
        mock_db.execute.return_value = _mock_scalar_result(sample_procedure)

        result = await validator._validate_procedure("P001")

        assert result == sample_procedure

    @pytest.mark.asyncio
    async def test_unknown_procedure_raises(self, validator, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(ClaimValidationError, match="not found"):
            await validator._validate_procedure("P999")


# ── Fraud Detection Tests ─────────────────────────────────────────


class TestCheckFraud:
    """Tests for ClaimValidator._check_fraud."""

    @pytest.mark.asyncio
    async def test_below_threshold_no_flag(self, validator, sample_procedure):
        """Claim at 1.5x average cost should NOT be flagged."""
        flag, reason = await validator._check_fraud(
            Decimal("7500.00"),
            sample_procedure,  # 1.5x of 5000
        )

        assert flag is False
        assert reason is None

    @pytest.mark.asyncio
    async def test_at_threshold_no_flag(self, validator, sample_procedure):
        """Claim at exactly 2x average cost should NOT be flagged (not > 2x)."""
        flag, reason = await validator._check_fraud(
            Decimal("10000.00"),
            sample_procedure,  # exactly 2x of 5000
        )

        assert flag is False
        assert reason is None

    @pytest.mark.asyncio
    async def test_above_threshold_flags_fraud(self, validator, sample_procedure):
        """Claim exceeding 2x average cost should be flagged."""
        flag, reason = await validator._check_fraud(
            Decimal("10001.00"),
            sample_procedure,  # just above 2x of 5000
        )

        assert flag is True
        assert "exceeds" in reason
        assert "2.0x" in reason

    @pytest.mark.asyncio
    async def test_extreme_fraud_flagged(self, validator, sample_procedure):
        """Massively inflated claim clearly flagged."""
        flag, reason = await validator._check_fraud(
            Decimal("150000.00"),
            sample_procedure,  # 30x average
        )

        assert flag is True
        assert reason is not None


# ── Approval Determination Tests ──────────────────────────────────


class TestDetermineApproval:
    """Tests for ClaimValidator._determine_approval (synchronous)."""

    def test_approved_full_amount(self, validator):
        """Within benefit limit, no fraud → APPROVED full amount."""
        status, amount = validator._determine_approval(
            claim_amount=Decimal("15000.00"),
            remaining_benefit=Decimal("80000.00"),
            fraud_flag=False,
        )

        assert status == ClaimStatus.APPROVED
        assert amount == Decimal("15000.00")

    def test_partial_over_remaining_benefit(self, validator):
        """Claim exceeds remaining benefit → PARTIAL with capped amount."""
        status, amount = validator._determine_approval(
            claim_amount=Decimal("50000.00"),
            remaining_benefit=Decimal("30000.00"),
            fraud_flag=False,
        )

        assert status == ClaimStatus.PARTIAL
        assert amount == Decimal("30000.00")

    def test_rejected_when_fraud_flagged(self, validator):
        """Fraud detected → REJECTED with zero approved."""
        status, amount = validator._determine_approval(
            claim_amount=Decimal("15000.00"),
            remaining_benefit=Decimal("80000.00"),
            fraud_flag=True,
        )

        assert status == ClaimStatus.REJECTED
        assert amount == Decimal("0.00")

    def test_rejected_fraud_even_within_limits(self, validator):
        """Fraud flag causes rejection regardless of benefit availability."""
        status, amount = validator._determine_approval(
            claim_amount=Decimal("1000.00"),
            remaining_benefit=Decimal("100000.00"),
            fraud_flag=True,
        )

        assert status == ClaimStatus.REJECTED
        assert amount == Decimal("0.00")

    def test_exact_remaining_benefit_approved(self, validator):
        """Claim exactly equal to remaining benefit → APPROVED."""
        status, amount = validator._determine_approval(
            claim_amount=Decimal("30000.00"),
            remaining_benefit=Decimal("30000.00"),
            fraud_flag=False,
        )

        assert status == ClaimStatus.APPROVED
        assert amount == Decimal("30000.00")


# ── End-to-End Pipeline Tests ─────────────────────────────────────


class TestValidateAndProcessClaim:
    """Integration-style tests for the full validation pipeline."""

    @pytest.mark.asyncio
    async def test_fully_approved_claim(
        self,
        validator,
        mock_db,
        active_member,
        active_provider,
        sample_diagnosis,
        sample_procedure,
    ):
        """Happy path: valid member, provider, codes, no fraud → APPROVED."""
        # Each call to db.execute returns a different mock based on call order
        mock_db.execute.side_effect = [
            _mock_scalar_result(active_member),
            _mock_scalar_result(active_provider),
            _mock_scalar_result(sample_diagnosis),
            _mock_scalar_result(sample_procedure),
        ]

        (
            status,
            approved,
            fraud_flag,
            fraud_reason,
        ) = await validator.validate_and_process_claim(
            member_id="M123",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("5000.00"),
        )

        assert status == ClaimStatus.APPROVED
        assert approved == Decimal("5000.00")
        assert fraud_flag is False
        assert fraud_reason is None

    @pytest.mark.asyncio
    async def test_partial_claim_over_benefit(
        self,
        validator,
        mock_db,
        active_provider,
        sample_diagnosis,
        sample_procedure,
    ):
        """Claim exceeds remaining benefit but no fraud → PARTIAL."""
        low_benefit_member = MagicMock(spec=Member)
        low_benefit_member.id = "M130"
        low_benefit_member.status = MemberStatus.ACTIVE
        low_benefit_member.remaining_benefit = Decimal("3000.00")

        mock_db.execute.side_effect = [
            _mock_scalar_result(low_benefit_member),
            _mock_scalar_result(active_provider),
            _mock_scalar_result(sample_diagnosis),
            _mock_scalar_result(sample_procedure),
        ]

        (
            status,
            approved,
            fraud_flag,
            fraud_reason,
        ) = await validator.validate_and_process_claim(
            member_id="M130",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("5000.00"),
        )

        assert status == ClaimStatus.PARTIAL
        assert approved == Decimal("3000.00")
        assert fraud_flag is False

    @pytest.mark.asyncio
    async def test_rejected_fraud_claim(
        self,
        validator,
        mock_db,
        active_member,
        active_provider,
        sample_diagnosis,
        sample_procedure,
    ):
        """Claim amount > 2x average cost → fraud flagged → REJECTED."""
        mock_db.execute.side_effect = [
            _mock_scalar_result(active_member),
            _mock_scalar_result(active_provider),
            _mock_scalar_result(sample_diagnosis),
            _mock_scalar_result(sample_procedure),
        ]

        (
            status,
            approved,
            fraud_flag,
            fraud_reason,
        ) = await validator.validate_and_process_claim(
            member_id="M123",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("50000.00"),  # 10x the 5000 avg
        )

        assert status == ClaimStatus.REJECTED
        assert approved == Decimal("0.00")
        assert fraud_flag is True
        assert "exceeds" in fraud_reason

    @pytest.mark.asyncio
    async def test_rejected_inactive_member(self, validator, mock_db, inactive_member):
        """Inactive member → ClaimValidationError raised early."""
        mock_db.execute.return_value = _mock_scalar_result(inactive_member)

        with pytest.raises(ClaimValidationError, match="not active"):
            await validator.validate_and_process_claim(
                member_id="M125",
                provider_id="H456",
                diagnosis_code="D001",
                procedure_code="P001",
                claim_amount=Decimal("5000.00"),
            )

    @pytest.mark.asyncio
    async def test_rejected_inactive_provider(
        self, validator, mock_db, active_member, inactive_provider
    ):
        """Inactive provider → ClaimValidationError raised at step 2."""
        mock_db.execute.side_effect = [
            _mock_scalar_result(active_member),
            _mock_scalar_result(inactive_provider),
        ]

        with pytest.raises(ClaimValidationError, match="not active"):
            await validator.validate_and_process_claim(
                member_id="M123",
                provider_id="H458",
                diagnosis_code="D001",
                procedure_code="P001",
                claim_amount=Decimal("5000.00"),
            )

    @pytest.mark.asyncio
    async def test_rejected_invalid_diagnosis(
        self, validator, mock_db, active_member, active_provider
    ):
        """Unknown diagnosis code → ClaimValidationError."""
        mock_db.execute.side_effect = [
            _mock_scalar_result(active_member),
            _mock_scalar_result(active_provider),
            _mock_scalar_result(None),  # diagnosis not found
        ]

        with pytest.raises(ClaimValidationError, match="not found"):
            await validator.validate_and_process_claim(
                member_id="M123",
                provider_id="H456",
                diagnosis_code="D999",
                procedure_code="P001",
                claim_amount=Decimal("5000.00"),
            )
