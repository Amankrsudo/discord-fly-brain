"""Regenerate research/evidence_ledger.csv from research/evidence_ledger.md.

The CSV is DERIVED, never hand-edited, so the two cannot drift. Run:
    python research/scripts/generate_evidence_ledger_csv.py
"""
from __future__ import annotations

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.normpath(os.path.join(HERE, ".."))
MD = os.path.join(RESEARCH, "evidence_ledger.md")
CSV_PATH = os.path.join(RESEARCH, "evidence_ledger.csv")

HEADER = ["ID", "Claim", "Exact value", "Unit", "Biological object",
          "Source", "Source type", "Provenance", "Evidence strength",
          "Direct/indirect", "Measured/modelled", "Reproducible",
          "Conflicts", "Dependency", "Status", "Notes"]


def parse(md_path: str):
    rows = []
    in_ledger = False
    with open(md_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("| ID | Claim |"):
                in_ledger = True
                continue
            if not in_ledger:
                continue
            if line.startswith("| ---") or line.startswith("|--"):
                continue
            if not line.strip():
                continue          # tolerate blank lines inside the table
            if not line.startswith("|"):
                if rows:
                    break
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == len(HEADER) and re.match(r"^E-\d+$", cells[0]):
                rows.append(cells)
    return rows


def main() -> int:
    rows = parse(MD)
    if not rows:
        print("no ledger rows parsed from", MD, file=sys.stderr)
        return 1
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        w.writerows(rows)
    ids = [r[0] for r in rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    print(f"wrote {CSV_PATH}: {len(rows)} rows x {len(HEADER)} columns")
    if dupes:
        print("ERROR duplicate ids:", sorted(dupes), file=sys.stderr)
        return 1
    print(f"first={ids[0]} last={ids[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
