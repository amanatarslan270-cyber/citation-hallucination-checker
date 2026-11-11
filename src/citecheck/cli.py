"""citecheck references.txt [--json out.json]"""
from __future__ import annotations

import argparse
import json
import sys

from .verify import CitationChecker

ICON = {"verified": "✅", "suspicious": "⚠️ ", "not_found": "❌", "unparseable": "❔"}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="citecheck", description="Detect hallucinated or fabricated citations")
    ap.add_argument("file", help="text file with a reference list ('-' for stdin)")
    ap.add_argument("--json", help="also write results to this JSON file")
    a = ap.parse_args(argv)

    text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
    results = CitationChecker().check_text(text)

    for i, v in enumerate(results, 1):
        print(f"{ICON[v.status]} [{i}] {v.status.upper()}: {v.reason}")
        print(f"     {v.reference[:110]}{'…' if len(v.reference) > 110 else ''}")
        if v.matched_title and v.status != "verified":
            print(f"     closest record: {v.matched_title} (doi:{v.matched_doi})")
    counts = {s: sum(v.status == s for v in results) for s in ICON}
    print("\nSummary:", ", ".join(f"{k}={n}" for k, n in counts.items()))
    if a.json:
        json.dump([v.to_dict() for v in results], open(a.json, "w"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
