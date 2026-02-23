import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
import uuid
from decimal import Decimal
from datetime import datetime, timezone

from app.models.claim import Claim
from app.enums import ClaimStatus


@pytest.mark.asyncio
async def test_submit_claim_success(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test successfully submitting a valid claim that sits within budget bounds.
    """
    claim_id = uuid.uuid4()
    mock_claim = Claim(
        id=claim_id,
        member_id="M123",
        provider_id="H456",
        diagnosis_code="D001",
        procedure_code="P001",
        claim_amount=Decimal("15000.00"),
        approved_amount=Decimal("15000.00"),
        status=ClaimStatus.APPROVED,
        fraud_flag=False,
        notes="All looks good",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock the internal CRUD call that parses validation rules
    mock_create_claim = mocker.patch(
        "app.views.claims.claims.create_claim",
        new_callable=AsyncMock,
        return_value=mock_claim,
    )

    response = await client.post(
        "/claims",
        json={
            "member_id": "M123",
            "provider_id": "H456",
            "diagnosis_code": "D001",
            "procedure_code": "P001",
            "claim_amount": 15000.00,
            "notes": "Emergency Outpatient Appendectomy",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == str(claim_id)
    assert data["status"] == "approved"
    assert data["fraud_flag"] is False
    assert data["approved_amount"] == "15000.00"
    mock_create_claim.assert_called_once()


@pytest.mark.asyncio
async def test_submit_claim_fraud_rejected(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Test submitting a suspicious claim exceeding 2x the standard deviation threshold.
    """
    claim_id = uuid.uuid4()
    mock_claim = Claim(
        id=claim_id,
        member_id="M123",
        provider_id="H456",
        diagnosis_code="D001",
        procedure_code="P001",
        claim_amount=Decimal("150000.00"),
        approved_amount=Decimal("0.00"),
        status=ClaimStatus.REJECTED,
        fraud_flag=True,
        fraud_reason="Claim amount (150000.00) exceeds 2.0x average procedure cost",
        notes="Immediate rejection",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_create_claim = mocker.patch(
        "app.views.claims.claims.create_claim",
        new_callable=AsyncMock,
        return_value=mock_claim,
    )

    response = await client.post(
        "/claims",
        json={
            "member_id": "M123",
            "provider_id": "H456",
            "diagnosis_code": "D001",
            "procedure_code": "P001",
            "claim_amount": 150000.00,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "rejected"
    assert data["fraud_flag"] is True
    assert data["approved_amount"] == "0.00"
    assert "exceeds" in data["fraud_reason"]
    mock_create_claim.assert_called_once()


@pytest.mark.asyncio
async def test_get_claim_by_id_found(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Retrieve an existing claim by matching ID
    """
    claim_id = uuid.uuid4()
    mock_claim = Claim(
        id=claim_id,
        member_id="M123",
        provider_id="H456",
        diagnosis_code="D001",
        procedure_code="P001",
        claim_amount=Decimal("15000.00"),
        approved_amount=Decimal("15000.00"),
        status=ClaimStatus.APPROVED,
        fraud_flag=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_get_claim = mocker.patch(
        "app.views.claims.claims.get_claim_by_id",
        new_callable=AsyncMock,
        return_value=mock_claim,
    )

    response = await client.get(f"/claims/{claim_id}")

    assert response.status_code == 200
    assert response.json()["claim_id"] == str(claim_id)
    assert response.json()["status"] == "approved"
    mock_get_claim.assert_called_once()


@pytest.mark.asyncio
async def test_get_claim_by_id_not_found(
    client: AsyncClient, mock_db_session: AsyncMock, mocker
):
    """
    Querying a nonexistent claim returns 404
    """
    claim_id = uuid.uuid4()
    mock_get_claim = mocker.patch(
        "app.views.claims.claims.get_claim_by_id",
        new_callable=AsyncMock,
        return_value=None,
    )

    response = await client.get(f"/claims/{claim_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_get_claim.assert_called_once()


@pytest.mark.asyncio
async def test_list_claims(client: AsyncClient, mock_db_session: AsyncMock, mocker):
    """
    Test bulk fetching claims with pagination schemas formatting correctly
    """
    claim_id = uuid.uuid4()
    mock_claims = [
        Claim(
            id=claim_id,
            member_id="M123",
            provider_id="H456",
            diagnosis_code="D001",
            procedure_code="P001",
            claim_amount=Decimal("15000.00"),
            approved_amount=Decimal("5000.00"),
            status=ClaimStatus.PARTIAL,
            fraud_flag=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    mock_list_claims = mocker.patch(
        "app.views.claims.claims.list_claims",
        new_callable=AsyncMock,
        return_value=(mock_claims, 1),
    )

    response = await client.get(
        "/claims?member_id=M123&status=partial&page=1&page_size=20"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["claims"]) == 1
    assert data["claims"][0]["status"] == "partial"
    mock_list_claims.assert_called_once()
