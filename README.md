# Ginja AI

## Prerequisites

| Tool   | Version | Install                                                   |
| ------ | ------- | --------------------------------------------------------- |
| Python | ≥ 3.13  | [python.org](https://www.python.org/downloads/)           |
| uv     | latest  | `curl -LsSf https://astral.sh/uv/install.sh \| sh`       |
| Docker | latest  | *(optional)* [docker.com](https://docs.docker.com/get-docker/) |

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

### 4. Run the server

```bash
uv run python main.py
```

The API will be available at **http://localhost:8000**.

**Alternative** — run with uvicorn directly:

```bash
uv run uvicorn app.main:create_app --factory --reload
```

### 5. Explore the API

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

## Project Structure

```
ginja-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Settings (env-based via pydantic-settings)
│   ├── middleware.py         # Request logging middleware
│   └── routers/
│       ├── __init__.py
│       └── health.py        # GET /health
├── main.py                  # Entrypoint (uvicorn runner)
├── pyproject.toml            # Project metadata & dependencies
├── uv.lock                  # Locked dependency versions
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Container orchestration
├── .env.example             # Environment variable template
└── README.md
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

## License

Private — All rights reserved.
