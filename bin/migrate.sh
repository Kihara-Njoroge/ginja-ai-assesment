#! /usr/bin/env bash

# Gene
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
