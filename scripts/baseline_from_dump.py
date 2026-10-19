#!/usr/bin/env python3
"""Extract per-table INSERT counts from a pg_dump SQL file (baseline for verification)."""

from __future__ import annotations

import gzip
import re
import sys
from collections import Counter
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: baseline_from_dump.py DUMP [OUT]")

DUMP = Path(sys.argv[1])
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "scripts/baseline_row_counts_pre_migration.txt")

pat = re.compile(r"^INSERT INTO (public\.(?:\"?[A-Za-z0-9_]+\"?))")

counts: Counter[str] = Counter()
opener = gzip.open if DUMP.suffix == ".gz" else open
with opener(DUMP, "rt", errors="replace") as fh:  # type: ignore[arg-type]
    for line in fh:
        m = pat.match(line)
        if m:
            counts[m.group(1)] += 1

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w") as out:
    for table in sorted(counts):
        out.write(f"{table}\t{counts[table]}\n")

print(f"Wrote {len(counts)} table counts to {OUT} (total rows {sum(counts.values())})")
