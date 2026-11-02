"""Seed the local dev database from the generated synthetic corpus.

The corpus must be generated first:
    python scripts/generate_synthetic_corpus.py

The database schema arrives in M1; until then this script validates the corpus
and reports what it would seed, so the generator stays testable in CI without a
running Postgres. Once the M1 migrations exist, the insert path lands here.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx

DEFAULT_CORPUS = Path(__file__).resolve().parent / "generated" / "corpus.jsonl"


def load_corpus(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"corpus not found: {path}\nrun generate_synthetic_corpus.py first")
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSON on line {line_no}: {exc}") from exc
    return rows


def validate(rows: list[dict]) -> None:
    required = {"id", "tenant_id", "role_id", "candidate_name", "extracted_text", "match_band"}
    for i, row in enumerate(rows):
        missing = required - row.keys()
        if missing:
            raise SystemExit(f"row {i} missing fields: {sorted(missing)}")
    tenants = {r["tenant_id"] for r in rows}
    if len(tenants) < 2:
        raise SystemExit("corpus must contain at least two tenants")
    bands = {r["match_band"] for r in rows}
    if not {"strong", "moderate", "weak", "insufficient"} <= bands:
        raise SystemExit("corpus must contain all four match bands")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()

    rows = load_corpus(args.corpus)
    validate(rows)

    tenants: dict[str, int] = {}
    for row in rows:
        tenants[row["tenant_id"]] = tenants.get(row["tenant_id"], 0) + 1

    print(f"Validated {len(rows)} synthetic documents across {len(tenants)} tenants:")
    for tenant, n in sorted(tenants.items()):
        print(f"  {tenant}: {n} documents")

    if args.dry_run:
        print("dry-run: no database writes. Insert path lands with the M1 schema.")
        return

    database_url = os.environ.get("VETHARBOR_DATABASE_URL")
    if not database_url:
        raise SystemExit("VETHARBOR_DATABASE_URL is required for a real seed")
    # Insert path is intentionally a stub: the documents/org_memberships tables
    # arrive with the first M1 migration (docs/DATA_MODEL.md §3).
    raise SystemExit("real seed not implemented yet — waiting on the M1 schema")


if __name__ == "__main__":
    main()
