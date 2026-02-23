
# ── Stage 1: Build ──────────────────────────────────────────────
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code and install project WITH dev dependencies for testing
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Run the test suite and verify coverage during the build
# Note: Docker caches this step. If the code in `COPY . .` hasn't changed, 
# Docker will instantly pass this step because it knows the tests already passed for this specific code state.
RUN uv run coverage run -m pytest -v && uv run coverage xml

# Strip dev dependencies before transferring the virtual environment to the runtime image
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── Stage 2: Runtime ───────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy virtual environment and application from builder
COPY --from=builder /app /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Run the application
CMD ["/app/.venv/bin/uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
