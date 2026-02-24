# Ginja AI - Health Claims Intelligence Platform

[![codecov](https://codecov.io/github/Kihara-Njoroge/ginja-ai-assesment/branch/master/graph/badge.svg?token=5BVJM7JVAX)](https://codecov.io/github/Kihara-Njoroge/ginja-ai-assesment)


## Features

- **Real-time Claim Validation**: Instant eligibility and benefit verification
- **Fraud Detection**: Automated fraud signal detection using cost analysis
- **RESTful API**: Clean, well-documented API endpoints
- **Scalable Architecture**: Built with FastAPI and PostgreSQL for high performance
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## Prerequisites

| Tool       | Version | Install                                                   |
| ---------- | ------- | --------------------------------------------------------- |
| Python     | ≥ 3.13  | [python.org](https://www.python.org/downloads/)           |
| uv         | latest  | `curl -LsSf https://astral.sh/uv/install.sh \| sh`       |
| PostgreSQL | ≥ 15    | [postgresql.org](https://www.postgresql.org/download/) or use Docker |
| Docker     | latest  | *(optional)* [docker.com](https://docs.docker.com/get-docker/) |

## Local Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd ginja-ai
```

### 2. Install dependencies

```bash
uv sync
```

This creates a `.venv` virtual environment and installs all dependencies from the lockfile.

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` to set your own values. All variables have sensible defaults.

### 4. Set up the database

Start PostgreSQL (via Docker or locally), then run migrations:

```bash
# Start PostgreSQL with Docker (if not running locally)
docker compose up db -d

# Run migrations (generates and applies)
./bin/migrate.sh

# Seed test data for claims system
uv run python bin/seed_data.py
```

### 5. Run the server

```bash
uv run python main.py
```

The API will be available at **http://localhost:8000**.

**Alternative** — run with uvicorn directly:

```bash
uv run uvicorn app.main:create_app --factory --reload
```

### 6. Explore the API

| URL                           | Description                    |
| ----------------------------- | ------------------------------ |
| http://localhost:8000/docs    | API Docs (RapiDoc)             |
| http://localhost:8000/health  | Health check endpoint          |
| http://localhost:8000/claims  | Claims management endpoints    |

## Quick Start - Claims API

> **Note:** Claims endpoints are protected by JWT authentication. Obtain an access token first by registering a user and logging in via the `/auth` endpoints (see [Authentication](#authentication) below), then pass it as a Bearer token.

### 1. Register & authenticate

```bash
# Register a user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email": "doctor@ginja.ai", "phone_number": "+254712345678", "first_name": "Test", "last_name": "Doctor", "password": "StrongPass_123!"}'

# Login (returns access_token + refresh_token)
curl -X POST http://localhost:8000/auth/login \
  -d 'username=doctor@ginja.ai&password=StrongPass_123!'
```

### 2. Submit a claim

```bash
curl -X POST http://localhost:8000/claims \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 15000
  }'
```

### 3. Get claim status

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/claims/{claim_id}
```

### 4. List claims (with filters)

```bash
curl -H "Authorization: Bearer <access_token>" \
  "http://localhost:8000/claims?member_id=M123&status=APPROVED"
```

For detailed API documentation, see [CLAIMS_SYSTEM.md](./guides/CLAIMS_SYSTEM.md).

## Docker

### Build and run

```bash
docker compose up --build
```

### Production

```bash
docker compose up --build -d
```

## Database Migrations

Use the provided bash script to automatically generate and apply migrations when you change the models:

```bash
./bin/migrate.sh
```

**Manual commands (if needed)**:

```bash
# Create a new migration after changing models
uv run alembic revision --autogenerate -m "description"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Development

Install dev dependencies:

```bash
uv sync --group dev
```

Run tests:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=app --cov-report=html
```

## Project Structure

```
ginja-ai/
├── app/
│   ├── models/          # Database models (User, Claim, Member, Provider, etc.)
│   ├── schemas/         # Pydantic schemas for API validation
│   ├── crud/            # Database operations
│   ├── utils/           # Business logic (claim validation, fraud detection)
│   ├── views/           # API route handlers
│   ├── config.py        # Application configuration
│   ├── database.py      # Database connection setup
│   └── main.py          # FastAPI application factory
├── tests/
│   ├── integration/     # Integration tests
│   └── unit/            # Unit tests
├── alembic/             # Database migrations
├── bin/                 # Utility scripts
│   ├── migrate.sh       # Migration helper
│   └── seed_data.py     # Seed test data
└── CLAIMS_SYSTEM.md     # Detailed claims system documentation
```

## Architecture & Technology Decisions

The application follows **Clean Architecture** principles to ensure separation of concerns, scalability, and maintainability:

- **Models**: Domain entities mapping directly to the database.
- **Schemas**: Pydantic models for strict API request/response validation contracts.
- **CRUD**: Dedicated Data Access Layer isolating database queries from business logic.
- **Utils**: Core business logic, actuarial rules, and validation pipelines.
- **Views**: FastAPI routing endpoints handling HTTP protocols and dependency injection.

### API Framework: FastAPI
I chose **FastAPI** for its native async/await support, automatic OpenAPI documentation generation, and Pydantic-based request validation. In a real-time claims processing context, these characteristics are critical the API must handle high-throughput hospital integrations while maintaining strict type-safety on financial data. FastAPI's dependency injection system also cleanly separates cross-cutting concerns (authentication, database sessions) from business logic.

### Database Choice: PostgreSQL
I chose **PostgreSQL** as the primary datastore, paired with **SQLAlchemy 2.0 (`asyncpg`)** for asynchronous operations.
- **Why PostgreSQL?**: Health claims data requires strict ACID compliance, absolute data integrity, and complex relational querying algorithms (e.g., locking balances during concurrent claim evaluations).
- **Asynchronous Driver**: Using `asyncpg` alongside FastAPI's asynchronous event loop allows the API to handle thousands of concurrent I/O-bound requests (database reads/writes) without blocking the thread pool, maximizing concurrency.
- **Schema Design**: The relational model enforces foreign key constraints between Claims → Members, Providers, Diagnoses, and Procedures, ensuring referential integrity across the claims pipeline. Indexes on `member_id`, `provider_id`, `status`, and `created_at` optimize the most common query patterns.

### Authentication: JWT + OTP
The API implements a stateless JWT authentication scheme with access/refresh token pairs. OTP-based login is supported as an alternative to password authentication, which enables secure passwordless flows for hospital staff. Token validation uses FastAPI's `Depends()` injection to cleanly gate protected routes without polluting business logic.

### Testing Strategy
Tests are organized into **unit tests** (isolated business logic with mocked dependencies) and **integration tests** (HTTP-level endpoint validation). The `ClaimValidator` unit tests cover every branch of the validation pipeline  member eligibility, provider status, medical code verification, fraud thresholds, and approval determination  ensuring the core decisioning engine is fully regression-tested. Pre-commit hooks enforce linting (`ruff`) and test execution before every commit.

### Claims Validation Workflow

1. **Member Eligibility**: Verify member is active with available benefits
2. **Provider Validation**: Ensure provider is registered and active
3. **Medical Codes**: Validate diagnosis and procedure codes
4. **Fraud Detection**: Flag claims exceeding 2x average procedure cost
5. **Approval Decision**:
   - APPROVED: Full amount within limits
   - PARTIAL: Approved up to remaining benefit
   - REJECTED: Failed validation or fraud + over limit

## Improvements for Production

While this application implements a robust Clean Architecture and FastAPI best-practices, the following improvements are recommended for a true enterprise production environment:

1. **Robust Authentication & Authorization (IAM)**: Implement an advanced Identity and Access Management module supporting **Organizations** (e.g., "Mombasa General Hospital"). This includes Role-Based Access Control (RBAC) allowing granular permissions where "Admin" roles can manage underlying users, but "Billing Provider" roles can only execute and submit claims. This multi-tenant logic is vital for B2B SaaS architecture.
2. **Caching**: Implement a Redis caching layer for high-volume static reads (e.g., retrieving `Procedures`, `Diagnoses`, or verifying active `Members`) to reduce database query loads.
3. **Event-Driven Architecture & Async Processing**: Migrate the claim validation pipeline to an event-driven model using **Apache Kafka** or **RabbitMQ**. When a hospital submits a claim, the API publishes a `claim.submitted` event and immediately returns `202 Accepted` with a tracking ID. Downstream consumers handle validation, fraud analysis, and approval asynchronously. This decouples the ingestion layer from processing, enables horizontal scaling of fraud detection workers, and supports audit event sourcing — critical for compliance in the health insurance domain.
4. **Rate Limiting**: Implement API rate-limiting algorithms (e.g., Token Bucket via Redis) to prevent Hospital nodes from inadvertently (or maliciously) DDoSing the claims validation engine.
5. **Advanced Fraud ML Models**: Replace the simplistic `2x Average Cost` heuristic with sophisticated Machine Learning predictive models (e.g., Isolation Forests) assessing historical patterns, provider anomalies, and multidimensional claim features.
6. **Observability & Structured Logging**: Integrate OpenTelemetry for distributed tracing and adopt JSON-structured logging (e.g., `python-json-logger`) with correlation IDs per claim. This enables seamless integration with **ELK stack** or **Grafana Loki** for centralized log aggregation, and **Prometheus** metrics for real-time dashboards monitoring claim throughput, fraud detection rates, and validation latencies.
7. **Webhooks & External Notifications**: Implement webhook callbacks to notify hospitals and insurers when claim status changes (e.g., from `PENDING` → `APPROVED`). This enables real-time integration with hospital billing systems without requiring polling.

## API Endpoints

### Health
- `GET /health` - Health check

### Authentication
- `POST /auth/request-otp` - Request OTP for login
- `POST /auth/validate-otp` - Validate OTP and get tokens
- `POST /auth/refresh` - Refresh access token

### Users
- `POST /users` - Register new user
- `GET /users` - List users
- `GET /users/{id}` - Get user details

### Claims
- `POST /claims` - Submit new claim
- `GET /claims/{id}` - Get claim details
- `GET /claims` - List claims (with filters)


## Environment Variables

| Variable          | Default     | Description                        |
| ----------------- | ----------- | ---------------------------------- |
| `APP_NAME`        | `Ginja AI`  | Application display name           |
| `APP_VERSION`     | `0.1.0`     | Application version                |
| `DEBUG`           | `false`     | Enable debug mode and hot reload   |
| `HOST`            | `0.0.0.0`   | Server bind address                |
| `PORT`            | `8000`      | Server port                        |
| `ALLOWED_ORIGINS` | `["*"]`     | CORS allowed origins (JSON array)  |
| `LOG_LEVEL`       | `INFO`      | Python logging level               |
| `DATABASE_URL`    | `postgresql+asyncpg://...` | Async PostgreSQL connection URL |

## CI/CD Deployment Pipeline (Azure)

This repository includes a production-grade automated deployment pipeline utilizing GitHub Actions `.github/workflows/deploy.yml`.

The pipeline executes the following sequential steps on any push to the `main` branch:
1. **Test & Lint**: Validates the codebase using `ruff` and executes the full `pytest` suite simulating database connectivity.
2. **Trivy Vulnerability Scan**: Scans Python dependencies natively looking for CVEs.
3. **Dockerize**: Builds the API container resolving the `Dockerfile`.
4. **Trivy Image Scan**: Validates the built container OS for vulnerabilities.
5. **Azure Container Registry (ACR)**: Pushes the highly secure image up to the Registry storage.
6. **Azure Container Apps**: Instructs the cloud environment to spin down the active containers and spin up the new image.

### Azure Secret Configuration
To enable the pipeline, the following secrets must be added to your GitHub repository under **Settings > Secrets and variables > Actions**:

| Secret Name | Description |
|---|---|
| `AZURE_CREDENTIALS` | Your Azure Service Principal credentials (JSON form) for auth. |
| `REGISTRY_LOGIN_SERVER` | Target Azure Container Registry URL (e.g. `youracr.azurecr.io`). |
| `REGISTRY_USERNAME` | Service Principal / Admin User of the ACR. |
| `REGISTRY_PASSWORD` | Access key for the ACR. |
| `AZURE_RESOURCE_GROUP` | The Resource Group holding your Container Apps. |
| `CONTAINER_APP_NAME` | The exact name of your deployed Azure Container App. |

### Post-Deployment: Database Initialization

After the CI/CD pipeline successfully deploys the image, the Azure Container App automatically runs database migrations (`alembic upgrade head`) and seeds initial data (`seed_data.py`) automatically on startup.

**Refer to `guides/AZURE_GUIDE.md` (Steps 7–8)** for direct Azure CLI commands demonstrating how to:
1. Provision a native Azure PostgreSQL Flexible Server.
2. Inject the resulting `DATABASE_URL` connection string securely into the Container App environment.

Once injected, the database configuring and seeding sequence handles itself autonomously!
