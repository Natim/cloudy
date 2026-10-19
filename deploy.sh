#!/bin/sh
set -e
cd "$(dirname "$0")"
uv sync
uv run python manage.py collectstatic --noinput
uv run python manage.py compress --force
kill -HUP "$(cat ../var/pid 2>/dev/null)" 2>/dev/null || echo "Reload gunicorn manually"
