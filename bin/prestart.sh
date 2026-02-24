#!/usr/bin/env bash
set -e

echo "Running Database Migrations..."
# Execute migration script safely determining environment
bash ./bin/migrate.sh

echo "Seeding Initial Database Config..."
# Execute seed data script securely mapping to docker runtime `.venv`
if [ -f "/app/.venv/bin/python" ]; then
    /app/.venv/bin/python bin/seed_data.py
elif command -v uv &> /dev/null; then
    uv run python bin/seed_data.py
else
    python bin/seed_data.py
fi

echo "Pre-start bootstrap complete! Starting the application wrapper..."
# Pass execution off to the provided CMD (uvicorn)
exec "$@"
