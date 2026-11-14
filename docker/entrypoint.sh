#!/bin/sh
set -e

# Wait for PostgreSQL before migrating (the database container may still be starting).
if [ "${DATABASE_URL#postgres}" != "$DATABASE_URL" ]; then
    python - <<'PY'
import os, sys, time

import psycopg

params = dict(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=os.environ.get("POSTGRES_PORT", "5432"),
    dbname=os.environ.get("POSTGRES_DB", "cloudy_scratch"),
    user=os.environ.get("POSTGRES_USER", "cloudy"),
    password=os.environ.get("POSTGRES_PASSWORD", ""),
)
for attempt in range(60):
    try:
        psycopg.connect(connect_timeout=3, **params).close()
        sys.exit(0)
    except psycopg.OperationalError:
        time.sleep(1)
sys.exit("PostgreSQL is not reachable")
PY
fi

python manage.py migrate --noinput
exec "$@"
