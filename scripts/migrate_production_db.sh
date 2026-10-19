#!/usr/bin/env bash
# Migrate a restored production database to the Django 6.1 schema.
#
# Idempotent: safe to re-run against an already-migrated database. Rehearse against
# a fresh copy with scripts/reset_scratch_db.sh before each run.
set -euo pipefail

DB_NAME="${DB_NAME:-cloudy_scratch}"
PURGE_BEFORE="${PURGE_BEFORE:-2016-09-08}"

export DJANGO_SETTINGS_MODULE=cloudy.settings
export DATABASE_URL="postgres://cloudy:cloudypwd@localhost:5432/${DB_NAME}"
export POSTGRES_DB="$DB_NAME"

PY=(uv run python)
if [[ ! -x "$(command -v uv)" ]]; then
  PY=(.venv/bin/python)
fi

echo "==> Drop South migration history"
# South's table is meaningless to Django's migration executor and its presence only
# invites confusion about which system is authoritative.
psql -d "$DB_NAME" -q -c "DROP TABLE IF EXISTS south_migrationhistory;"

echo "==> Django migrate (--fake-initial adopts the tables that already exist)"
"${PY[@]}" manage.py migrate --fake-initial --no-input

echo "==> Flush legacy sessions"
# Every pre-upgrade session cookie is unusable after the switch (different secret
# and serializer), so clear them outright rather than leaving dead rows behind.
psql -d "$DB_NAME" -q -c "TRUNCATE TABLE django_session;"

echo "==> Purge dormant accounts (last_login before ${PURGE_BEFORE})"
"${PY[@]}" manage.py purge_dormant_accounts --before="$PURGE_BEFORE"

echo "==> Record post-migration row counts"
bash scripts/record_baseline_counts.sh "$DB_NAME" scripts/baseline_row_counts_post_migration.txt

echo "Migration script complete."
