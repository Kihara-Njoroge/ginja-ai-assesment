# Claims Management System Documentation

## Overview

The Claims Management System is a real-time health insurance claims validation platform that integrates with hospitals and insurers to validate claims instantly. The system validates member eligibility, benefit coverage, and detects potential fraud signals before returning an approval decision.

## Architecture

### Clean Architecture Principles

The system follows clean architecture with clear separation of concerns:

```
app/
├── models/          # Domain entities (Member, Provider, Claim, etc.)
├── schemas/         # API request/response schemas (Pydantic)
├── crud/            # Data access layer
├── utils/           # Business logic (ClaimValidator, fraud detection)
├── views/           # API endpoints (FastAPI routes)
└── enums.py         # Shared enumerations
```

### Key Components

1. **Models** (`app/models/`):
   - `Member`: Insurance members with benefit limits
   - `Provider`: Healthcare providers (hospitals/clinics)
   - `Claim`: Insurance claims with validation results
   - `Procedure`: Medical procedures with average costs
   - `Diagnosis`: Medical diagnosis codes

2. **Business Logic** (`app/utils/claim_validator.py`):
   - `ClaimValidator`: Orchestrates validation workflow
   - Member eligibility validation
   - Benefit limit checking
   - Fraud detection (2x average cost threshold)
   - Approval decision logic

3. **API Layer** (`app/views/claims/`):
   - POST `/claims` - Submit new claim
   - GET `/claims/{id}` - Retrieve claim details
   - GET `/claims` - List claims with filters

## Database Schema

### Members Table
```sql
CREATE TABLE members (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    status VARCHAR(20) NOT NULL,  -- ACTIVE, INACTIVE, SUSPENDED
    benefit_limit NUMERIC(12,2) NOT NULL,
    used_benefit NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Providers Table
```sql
CREATE TABLE providers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    phone_number VARCHAR(20),
    email VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Claims Table
```sql
CREATE TABLE claims (
    id UUID PRIMARY KEY,
    member_id VARCHAR(50) REFERENCES members(id),
    provider_id VARCHAR(50) REFERENCES providers(id),
    diagnosis_code VARCHAR(50) REFERENCES diagnoses(code),
    procedure_code VARCHAR(50) REFERENCES procedures(code),
    claim_amount NUMERIC(12,2) NOT NULL,
    approved_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,  -- PENDING, APPROVED, PARTIAL, REJECTED
    fraud_flag BOOLEAN NOT NULL DEFAULT FALSE,
    fraud_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE
);
```

## Business Logic

### Claim Validation Workflow

1. **Member Eligibility Check**
   - Verify member exists
   - Check member status is ACTIVE
   - Ensure remaining benefit > 0

2. **Provider Validation**
   - Verify provider exists
   - Check provider is active

3. **Medical Code Validation**
   - Verify diagnosis code exists
   - Verify procedure code exists

4. **Fraud Detection**
   - Compare claim amount to procedure average cost
   - Flag if claim > 2x average cost
   - Record fraud reason

5. **Approval Decision**
   - If fraud flagged AND claim > remaining benefit → REJECTED
   - If claim > remaining benefit → PARTIAL (approve up to remaining)
   - Otherwise → APPROVED (full amount)

6. **Update Member Benefits**
   - Increment used_benefit by approved_amount
   - Only for APPROVED or PARTIAL claims

### Fraud Detection Rules

Current implementation uses a simple threshold-based approach:

```python
FRAUD_MULTIPLIER = 2.0

if claim_amount > (procedure.average_cost * FRAUD_MULTIPLIER):
    fraud_flag = True
    fraud_reason = f"Claim amount ({claim_amount}) exceeds 2x average procedure cost ({procedure.average_cost})"
```

**Production Enhancements:**
- Machine learning models for pattern detection
- Historical claim analysis per provider/member
- Geographic cost variations
- Procedure combination validation
- Time-based anomaly detection

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the system uses a mock authentication for development. In production, implement JWT-based authentication with role-based access control (RBAC).

### Endpoints

#### 1. Submit Claim

**POST** `/claims`

Submit a new health insurance claim for validation and processing.

**Request Body:**
```json
{
  "member_id": "M123",
  "provider_id": "H456",
  "diagnosis_code": "D001",
  "procedure_code": "P001",
  "claim_amount": 50000,
  "notes": "Optional notes"
}
```

**Response (201 Created):**
```json
{
  "claim_id": "c789e123-e89b-12d3-a456-426614174000",
  "member_id": "M123",
  "provider_id": "H456",
  "diagnosis_code": "D001",
  "procedure_code": "P001",
  "claim_amount": 50000.00,
  "approved_amount": 40000.00,
  "status": "PARTIAL",
  "fraud_flag": true,
  "fraud_reason": "Claim amount (50000.00) exceeds 2x average procedure cost (20000.00)",
  "notes": "Optional notes",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:05Z",
  "processed_at": "2024-01-15T10:30:05Z"
}
```

**Status Codes:**
- `201`: Claim processed successfully
- `400`: Invalid request data
- `500`: Server error

#### 2. Get Claim by ID

**GET** `/claims/{claim_id}`

Retrieve detailed information about a specific claim.

**Response (200 OK):**
```json
{
  "claim_id": "c789e123-e89b-12d3-a456-426614174000",
  "member_id": "M123",
  "provider_id": "H456",
  "diagnosis_code": "D001",
  "procedure_code": "P001",
  "claim_amount": 50000.00,
  "approved_amount": 40000.00,
  "status": "APPROVED",
  "fraud_flag": false,
  "fraud_reason": null,
  "notes": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:05Z",
  "processed_at": "2024-01-15T10:30:05Z"
}
```

**Status Codes:**
- `200`: Success
- `404`: Claim not found

#### 3. List Claims

**GET** `/claims`

List claims with optional filtering and pagination.

**Query Parameters:**
- `member_id` (optional): Filter by member ID
- `provider_id` (optional): Filter by provider ID
- `status` (optional): Filter by status (PENDING, APPROVED, PARTIAL, REJECTED)
- `page` (optional, default=1): Page number
- `page_size` (optional, default=20, max=100): Items per page

**Response (200 OK):**
```json
{
  "claims": [
    {
      "claim_id": "c789e123-e89b-12d3-a456-426614174000",
      "member_id": "M123",
      "provider_id": "H456",
      "diagnosis_code": "D001",
      "procedure_code": "P001",
      "claim_amount": 50000.00,
      "approved_amount": 40000.00,
      "status": "APPROVED",
      "fraud_flag": false,
      "fraud_reason": null,
      "notes": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:05Z",
      "processed_at": "2024-01-15T10:30:05Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Sample API Requests

### Using cURL

#### 1. Submit a Claim (Approved)
```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 5000
  }'
```

#### 2. Submit a Claim (Fraud Flagged)
```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 50000
  }'
```

#### 3. Get Claim by ID
```bash
curl -X GET http://localhost:8000/claims/{claim_id}
```

#### 4. List All Claims
```bash
curl -X GET http://localhost:8000/claims
```

#### 5. Filter Claims by Member
```bash
curl -X GET "http://localhost:8000/claims?member_id=M123"
```

#### 6. Filter Claims by Status
```bash
curl -X GET "http://localhost:8000/claims?status=APPROVED"
```

#### 7. Paginated Claims
```bash
curl -X GET "http://localhost:8000/claims?page=1&page_size=10"
```

### Using HTTPie

```bash
# Submit claim
http POST localhost:8000/claims \
  member_id=M123 \
  provider_id=H456 \
  diagnosis_code=D001 \
  procedure_code=P001 \
  claim_amount:=5000

# Get claim
http GET localhost:8000/claims/{claim_id}

# List claims
http GET localhost:8000/claims member_id==M123
```

## Running the Application

### Prerequisites
- Python ≥ 3.13
- PostgreSQL ≥ 15
- uv package manager

### Setup

1. **Clone and install dependencies:**
```bash
git clone <repo-url>
cd ginja-ai
uv sync
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Start PostgreSQL:**
```bash
docker compose up db -d
```

4. **Run migrations:**
```bash
uv run alembic upgrade head
```

5. **Seed test data:**
```bash
uv run python bin/seed_data.py
```

6. **Start the server:**
```bash
uv run python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation (RapiDoc UI).

## Testing

### Run All Tests
```bash
uv run pytest
```

### Run with Coverage
```bash
uv run pytest --cov=app --cov-report=html
```

### Test Specific Module
```bash
uv run pytest tests/integration/claims/
```

## Production Considerations

### Security
1. **Authentication & Authorization**
   - Implement JWT-based authentication
   - Role-based access control (RBAC)
   - API rate limiting
   - Request signing for provider integrations

2. **Data Protection**
   - Encrypt sensitive data at rest
   - Use HTTPS/TLS for all communications
   - Implement audit logging
   - PII data masking in logs

3. **Input Validation**
   - Strict schema validation (already implemented with Pydantic)
   - SQL injection prevention (using SQLAlchemy ORM)
   - XSS protection

### Scalability
1. **Database**
   - Connection pooling (configured)
   - Read replicas for queries
   - Partitioning for large tables
   - Caching layer (Redis) for frequent queries

2. **Application**
   - Horizontal scaling with load balancer
   - Async processing for heavy operations
   - Message queue for claim processing (Celery/RabbitMQ)
   - CDN for static assets

3. **Monitoring**
   - Application Performance Monitoring (APM)
   - Error tracking (Sentry)
   - Metrics collection (Prometheus)
   - Centralized logging (ELK stack)

### Reliability
1. **High Availability**
   - Multi-region deployment
   - Database replication
   - Automated failover
   - Health checks and circuit breakers

2. **Data Integrity**
   - Database transactions (implemented)
   - Idempotency keys for claim submission
   - Event sourcing for audit trail
   - Regular backups

3. **Error Handling**
   - Graceful degradation
   - Retry mechanisms with exponential backoff
   - Dead letter queues
   - Comprehensive error logging

### Performance Optimization
1. **Database Queries**
   - Index optimization (already indexed key fields)
   - Query optimization
   - Batch processing for bulk operations
   - Database query caching

2. **API Response**
   - Response compression
   - Pagination (implemented)
   - Field filtering
   - ETags for caching

### Compliance
1. **Healthcare Regulations**
   - HIPAA compliance for US
   - GDPR for EU data
   - Local healthcare regulations
   - Data retention policies

2. **Audit Requirements**
   - Complete audit trail
   - Immutable logs
   - Access logs
   - Change tracking

## Future Enhancements

### Short Term
1. **Enhanced Fraud Detection**
   - Machine learning models
   - Historical pattern analysis
   - Provider risk scoring
   - Real-time anomaly detection

2. **Workflow Management**
   - Manual review queue for flagged claims
   - Approval workflows
   - Notification system
   - SLA tracking

3. **Reporting & Analytics**
   - Claims dashboard
   - Fraud analytics
   - Provider performance metrics
   - Member utilization reports

### Long Term
1. **AI/ML Integration**
   - Predictive fraud detection
   - Cost estimation models
   - Automated coding suggestions
   - Risk stratification

2. **Integration Ecosystem**
   - HL7/FHIR standards support
   - EHR integrations
   - Payment gateway integration
   - Third-party verification services

3. **Advanced Features**
   - Real-time eligibility verification
   - Pre-authorization workflows
   - Claims adjudication automation
   - Provider network management

## Technical Decisions

### Why FastAPI?
- High performance (async/await support)
- Automatic API documentation
- Type safety with Pydantic
- Modern Python features
- Large ecosystem

### Why PostgreSQL?
- ACID compliance for financial data
- JSON support for flexible schemas
- Excellent performance
- Mature ecosystem
- Strong consistency guarantees

### Why SQLAlchemy?
- ORM abstraction
- Database migration support (Alembic)
- Query optimization
- Connection pooling
- Type safety with modern Python

### Why Async?
- Better resource utilization
- Higher concurrency
- Non-blocking I/O
- Scalability for real-time processing

## Support & Maintenance

### Logging
All operations are logged with appropriate levels:
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failures requiring attention

### Monitoring Endpoints
- `GET /health` - Health check endpoint
- Database connection status
- Application metrics

### Database Migrations
```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## License
[Your License Here]

## Contact
[Your Contact Information]
