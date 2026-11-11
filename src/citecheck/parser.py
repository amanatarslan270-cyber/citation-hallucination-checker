"""Split a reference list into entries and pull out DOI, year and title."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.I)
YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
QUOTED_RE = re.compile(r"[\"“”]([^\"“”]{10,300})[\"“”]")
ENTRY_START_RE = re.compile(r"^\s*(\[\d+\]|\d+\.|\(\d+\))\s*")


@dataclass
class Reference:
    raw: str
    doi: Optional[str] = None
    year: Optional[int] = None
    title: Optional[str] = None


def split_references(text: str) -> List[str]:
    """Split a block of references. Supports `[1] ...`, `1. ...`, or one reference per blank-line paragraph."""
    lines = [l.rstrip() for l in text.strip().splitlines()]
    if any(ENTRY_START_RE.match(l) for l in lines):
        entries, cur = [], []
        for l in lines:
            if ENTRY_START_RE.match(l) and cur:
                entries.append(" ".join(cur)); cur = []
            if l.strip():
                cur.append(ENTRY_START_RE.sub("", l).strip() if not cur else l.strip())
        if cur:
            entries.append(" ".join(cur))
        return entries
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paras if len(paras) > 1 else [l.strip() for l in lines if l.strip()]


def _guess_title(ref: str) -> Optional[str]:
    m = QUOTED_RE.search(ref)
    if m:
        return m.group(1).strip(" ,.")
    # APA style: Authors (2020). Title. Venue.
    m = re.search(r"\((?:19|20)\d\d[a-z]?\)\.\s*(.+?)\.\s", ref + " ")
    if m:
        return m.group(1).strip()
    # Fallback: longest sentence-like chunk that isn't the author list
    parts = [p.strip() for p in re.split(r"\.\s", ref) if len(p.split()) >= 4]
    parts = [p for p in parts if not re.match(r"^[A-Z][a-z]+,\s*[A-Z]\.", p)]
    return max(parts, key=len) if parts else None


def parse_reference(ref: str) -> Reference:
    doi = DOI_RE.search(ref)
    year = YEAR_RE.search(ref)
    return Reference(
        raw=ref,
        doi=doi.group(1).rstrip(".,;") if doi else None,
        year=int(year.group(1)) if year else None,
        title=_guess_title(ref),
    )
