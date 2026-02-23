# Ginja AI: Claims Management System

## Overview
The Claims Management System is the core engine behind Ginja AI's embedded health intelligence platform. It processes medical claims in real-time, executing eligibility verifications, parsing diagnostic codes, enforcing benefit caps, and proactively detecting anomalous signals through heuristic fraud analysis.

## Core Validation Workflow
Every claim submitted to the engine undergoes a strict multi-tier validation gateway:

1. **Member Eligibility Verification**: Resolves the Member record (e.g., `M123`) ensuring their profile is marked `ACTIVE` and they possess a strictly positive `remaining_benefit` limit.
2. **Provider Validation**: Evaluates the Provider entity (e.g., Hospital `H456`) strictly asserting its operational state is active.
3. **Medical Logic Mapping**: Cross-references the submitted `diagnosis_code` and `procedure_code` against registered medical vocabularies ensuring legitimate medical pathways.
4. **Automated Fraud Detection**: Applies actuarial heuristics evaluating the `claim_amount` against the baseline `average_cost` of the procedure. Flag boundaries trigger automatically at `2x` standard deviation thresholds.
5. **Dynamic Processing Resolution**: Yields a deterministic computation granting `APPROVED` (fully under budget), `PARTIAL` (deducted remainder), or `REJECTED` (fraud triggered or fundamentally exhausted limits).

---

## API Documentation

> **Note**: This environment securely gates administrative paths. Bearer Tokens (`Authorization: Bearer <jwt>`) are required for the `/claims` router context to ensure only registered Providers and internal interfaces alter computational records.

### 1. Submit a New Claim (`POST /claims`)
Evaluates and processes a health medical claim computing immediate fraud metrics and approval ceilings.

#### Request
```bash
curl -X POST http://localhost:8000/claims \
  -H "Authorization: Bearer <your_jwt_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 15000,
    "notes": "Emergency Outpatient Appendectomy"
  }'
```

#### Successful Response (201 Created)
```json
{
  "claim_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "member_id": "M123",
  "provider_id": "H456",
  "diagnosis_code": "D001",
  "procedure_code": "P001",
  "claim_amount": 15000.00,
  "approved_amount": 15000.00,
  "status": "APPROVED",
  "fraud_flag": false,
  "fraud_reason": null,
  "notes": "Emergency Outpatient Appendectomy",
  "created_at": "2026-02-23T21:00:00Z",
  "updated_at": "2026-02-23T21:00:00Z",
  "processed_at": null
}
```

#### Failed Fraud Evaluation Response (201 Created)
Transactions violating actuarial thresholds natively inject `fraug_flag` tracking while restricting output scopes.
```json
{
  "claim_id": "...",
  "status": "REJECTED",
  "fraud_flag": true,
  "fraud_reason": "Claim amount (150000.00) exceeds 2.0x average procedure cost (10000.00)",
  "approved_amount": 0.00
}
```

---

### 2. Retrieve a Claim Status (`GET /claims/{id}`)
Fetches an exact point-in-time calculation summary of an existing claim transaction.

#### Request
```bash
curl -X GET http://localhost:8000/claims/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer <your_jwt_token_here>"
```

#### Success Response (200 OK)
Yields the identical structured format representing the specific underlying SQL schema mapped object. (See standard payload format above).

#### Disconnected Response (404 Not Found)
```json
{
  "detail": "Claim 3fa85f64-5717-4562-b3fc-2c963f66afa6 not found"
}
```

---

### 3. List Bulk Claims (`GET /claims`)
Renders an array of claims structurally flattened matching strict query filtering criteria allowing granular monitoring dashboards.

#### Request (Filters applied)
```bash
curl -X GET "http://localhost:8000/claims?member_id=M123&status=PARTIAL&page=1&page_size=20" \
  -H "Authorization: Bearer <your_jwt_token_here>"
```

#### Success Response (200 OK)
Includes embedded pagination arrays alongside native generic representations.
```json
{
  "claims": [
    {
      "claim_id": "1be55c88-12ab-...",
      "member_id": "M123",
      "status": "PARTIAL",
      "approved_amount": 5000.00,
      "claim_amount": 15000.00,
      ...
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```
