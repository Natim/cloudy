#!/usr/bin/env bash
# Reset the scratch database from the pristine snapshot taken right after restore.
#
# Restoring the dump takes ~2 minutes; cloning the snapshot takes ~1 second, which
# makes it practical to rehearse the migration repeatedly as the plan requires.
# Create the snapshot once after a successful restore with:
#   createdb -T cloudy_scratch -O cloudy cloudy_pristine
set -euo pipefail

DB_NAME="${DB_NAME:-cloudy_scratch}"
TEMPLATE="${TEMPLATE:-cloudy_pristine}"
DB_USER="${DB_USER:-cloudy}"

# CREATE DATABASE ... TEMPLATE refuses to run while anything is connected to either
# database, so drop existing connections first.
psql -d postgres -q -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname IN ('$DB_NAME', '$TEMPLATE') AND pid <> pg_backend_pid();
" -o /dev/null

dropdb --if-exists "$DB_NAME"
createdb -T "$TEMPLATE" -O "$DB_USER" "$DB_NAME"

# A restored dump may grant privileges only to its owning role. Set DUMP_OWNER_ROLE
# locally so the Django user inherits that role; the name is not stored in git.
if [[ -n "${DUMP_OWNER_ROLE:-}" ]]; then
  psql -d "$DB_NAME" -q -c "GRANT \"${DUMP_OWNER_ROLE}\" TO \"$DB_USER\";"
fi

echo "Reset $DB_NAME from template $TEMPLATE"
