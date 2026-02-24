#!/usr/bin/env bash
set -e

echo "Running Alembic Migrations..."
if [ -f "/app/.venv/bin/alembic" ]; then
    /app/.venv/bin/alembic upgrade head
elif command -v uv &> /dev/null; then
    uv run alembic upgrade head
else
    alembic upgrade head
fi
