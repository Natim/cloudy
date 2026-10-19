#!/usr/bin/env bash
# Record exact per-table row counts from a PostgreSQL database (for migration verification).
#
# Uses COUNT(*) rather than pg_stat_user_tables.n_live_tup, because the latter is a
# planner estimate that stays at 0 until ANALYZE runs and so cannot be compared
# against the counts extracted from the dump file.
set -euo pipefail

DB_NAME="${1:-cloudy_scratch}"
OUT="${2:-scripts/baseline_row_counts.txt}"

QUERY=$(psql -d "$DB_NAME" -At -c "
SELECT string_agg(
         format(
           'SELECT %L AS t, count(*) AS n FROM %I.%I',
           schemaname || '.' || quote_ident(tablename),
           schemaname,
           tablename
         ),
         ' UNION ALL '
       )
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
")

if [[ -z "$QUERY" ]]; then
  echo "No user tables found in $DB_NAME" >&2
  exit 1
fi

# Tab-separated to match the format produced by baseline_from_dump.py, so the two
# can be compared with a plain diff.
psql -d "$DB_NAME" -At -F $'\t' -c "SELECT t, n FROM ($QUERY) AS counts ORDER BY t;" > "$OUT"

echo "Wrote exact row counts to $OUT ($(wc -l < "$OUT") tables)"
