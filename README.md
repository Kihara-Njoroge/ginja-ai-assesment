# Ginja AI

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

| URL                           | Description           |
| ----------------------------- | --------------------- |
| http://localhost:8000/docs    | Swagger UI            |
| http://localhost:8000/redoc   | ReDoc                 |
| http://localhost:8000/health  | Health check endpoint |

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

## License

Private — All rights reserved.
