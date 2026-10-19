#!/usr/bin/env bash
# Verify the reconciled production database against a database built from scratch
# by `migrate`, plus the row-count and password-hash expectations from the plan.
#
# This is what proves the migration graph matches reality: --fake-initial only
# checks that a table *exists*, so a column that drifted between the production
# schema and the migrations would otherwise go unnoticed until it 500s at runtime.
set -euo pipefail

DB_NAME="${DB_NAME:-cloudy_scratch}"
FRESH_DB="${FRESH_DB:-cloudy_fromscratch}"
DB_USER="${DB_USER:-cloudy}"
BASELINE="${BASELINE:-scripts/baseline_row_counts_pre_migration.txt}"
POST="${POST:-scripts/baseline_row_counts_post_migration.txt}"

export DJANGO_SETTINGS_MODULE=cloudy.settings

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# Tables that intentionally survive without a Django model. The plan keeps these in
# place for a later cleanup pass, so they are expected to be absent from a
# from-scratch database and must not be reported as drift.
# urlshortener_link is included because urlshortener.Link is managed = False: every
# short URL lives in redis, so the empty id-only table production ended up with is
# vestigial and is deliberately not recreated from scratch.
LEGACY_ONLY_TABLES='^(auth_message|south_migrationhistory|my_cache_table|indexer_index|impostor_impostorlog|registration_registrationprofile|sentry_.*|webmachine_.*|easy_thumbnails_.*|notification_noticequeuebatch|urlshortener_link|DGAC_avion_logbook_optionalfilterchoices|FFP_logbook_optionalfilterchoices)$'

echo "==> Building $FRESH_DB from scratch with migrate"
psql -d postgres -q -o /dev/null -c "
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE datname = '$FRESH_DB' AND pid <> pg_backend_pid();"
dropdb --if-exists "$FRESH_DB"
createdb -O "$DB_USER" "$FRESH_DB"

PY=(uv run python)
command -v uv >/dev/null || PY=(.venv/bin/python)

DATABASE_URL="postgres://cloudy:cloudypwd@localhost:5432/${FRESH_DB}" \
POSTGRES_DB="$FRESH_DB" \
  "${PY[@]}" manage.py migrate --no-input > "$WORK/fresh_migrate.log" 2>&1 \
  || { echo "from-scratch migrate failed:"; tail -30 "$WORK/fresh_migrate.log"; exit 1; }

# --- column-level comparison -------------------------------------------------
column_signature() {
  psql -d "$1" -At -F '|' -c "
  SELECT c.table_name, c.column_name, c.data_type,
         coalesce(c.character_maximum_length::text, '-'), c.is_nullable
  FROM information_schema.columns c
  JOIN information_schema.tables t
    ON t.table_schema = c.table_schema AND t.table_name = c.table_name
  WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
  ORDER BY c.table_name, c.column_name;
  "
}

column_signature "$DB_NAME" | grep -Ev "^($(echo "$LEGACY_ONLY_TABLES" | sed 's/^\^(//; s/)\$$//'))\|" \
  | LC_ALL=C sort > "$WORK/reconciled.cols"
column_signature "$FRESH_DB" | LC_ALL=C sort > "$WORK/fresh.cols"

echo "==> Schema diff (reconciled vs from-scratch, legacy-only tables excluded)"
if diff -u "$WORK/fresh.cols" "$WORK/reconciled.cols" > "$WORK/cols.diff"; then
  echo "    Schemas match on every column of every migrated table."
  SCHEMA_OK=1
else
  echo "    DRIFT DETECTED (- = from-scratch, + = reconciled):"
  cat "$WORK/cols.diff"
  SCHEMA_OK=0
fi

# --- legacy table inventory --------------------------------------------------
echo "==> Legacy tables present only in the reconciled database"
comm -23 \
  <(psql -d "$DB_NAME" -At -c "SELECT tablename FROM pg_tables WHERE schemaname='public'" | LC_ALL=C sort) \
  <(psql -d "$FRESH_DB" -At -c "SELECT tablename FROM pg_tables WHERE schemaname='public'" | LC_ALL=C sort) \
  | sed 's/^/    /'

echo "==> Tables missing from the reconciled database (must be empty)"
MISSING=$(comm -13 \
  <(psql -d "$DB_NAME" -At -c "SELECT tablename FROM pg_tables WHERE schemaname='public'" | LC_ALL=C sort) \
  <(psql -d "$FRESH_DB" -At -c "SELECT tablename FROM pg_tables WHERE schemaname='public'" | LC_ALL=C sort))
if [[ -n "$MISSING" ]]; then
  echo "$MISSING" | sed 's/^/    MISSING: /'
  SCHEMA_OK=0
else
  echo "    none"
fi

# --- data expectations -------------------------------------------------------
echo "==> Password hashes (Django 5.1 removed SHA1PasswordHasher)"
psql -d "$DB_NAME" -At -F ' ' -c "
SELECT 'sha1 remaining:', count(*) FILTER (WHERE password LIKE 'sha1\$%'),
       'of total:', count(*)
FROM auth_user;" | sed 's/^/    /'

echo "==> Row-count deltas against the pre-migration baseline"
if [[ -f "$BASELINE" && -f "$POST" ]]; then
  join -t $'\t' \
    <(LC_ALL=C sort "$BASELINE") \
    <(awk -F'\t' '$2 > 0' "$POST" | LC_ALL=C sort) \
    | awk -F'\t' '$2 != $3 { printf "    %s: %s -> %s (%+d)\n", $1, $2, $3, $3 - $2 }'
else
  echo "    baseline or post-migration counts missing; skipped" >&2
fi

echo
if [[ "$SCHEMA_OK" == "1" ]]; then
  echo "VERIFY PASSED"
else
  echo "VERIFY FAILED: schema drift above must be resolved" >&2
  exit 1
fi
