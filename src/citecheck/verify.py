"""Verify references against the Crossref public API."""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Callable, List, Optional

import requests

from .parser import Reference, parse_reference, split_references

CROSSREF = "https://api.crossref.org/works"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def crossref_get(url: str, params: Optional[dict] = None) -> Optional[dict]:
    """Default HTTP fetcher. Set CROSSREF_MAILTO to join Crossref's polite pool."""
    params = dict(params or {})
    if os.getenv("CROSSREF_MAILTO"):
        params["mailto"] = os.environ["CROSSREF_MAILTO"]
    r = requests.get(url, params=params, timeout=20, headers={"User-Agent": "citecheck/0.1"})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("message")


@dataclass
class Verdict:
    reference: str
    status: str                 # verified | suspicious | not_found | unparseable
    reason: str
    matched_title: Optional[str] = None
    matched_doi: Optional[str] = None
    similarity: Optional[float] = None

    def to_dict(self):
        return asdict(self)


class CitationChecker:
    def __init__(self, fetch: Callable = crossref_get, verified_at: float = 0.90, suspicious_at: float = 0.60):
        self.fetch = fetch
        self.verified_at = verified_at
        self.suspicious_at = suspicious_at

    def _judge(self, ref: Reference, item: dict, via: str) -> Verdict:
        title = (item.get("title") or [""])[0]
        sim = round(title_similarity(ref.title or ref.raw, title), 3) if ref.title else None
        year = (item.get("issued", {}).get("date-parts") or [[None]])[0][0]
        issues = []
        if sim is not None and sim < self.verified_at:
            issues.append(f"title similarity {sim}")
        if ref.year and year and abs(ref.year - year) > 1:
            issues.append(f"year {ref.year} vs registered {year}")
        if via == "search" and sim is not None and sim < self.suspicious_at:
            return Verdict(ref.raw, "not_found", "no Crossref record with a similar title", title, item.get("DOI"), sim)
        status = "verified" if not issues else "suspicious"
        reason = f"matched via {via}" if not issues else "; ".join(issues)
        return Verdict(ref.raw, status, reason, title, item.get("DOI"), sim)

    def check(self, raw: str) -> Verdict:
        ref = parse_reference(raw)
        if ref.doi:
            item = self.fetch(f"{CROSSREF}/{ref.doi}")
            if item is None:
                return Verdict(raw, "not_found", f"DOI {ref.doi} is not registered")
            return self._judge(ref, item, "DOI")
        if not ref.title:
            return Verdict(raw, "unparseable", "could not find a DOI or title")
        res = self.fetch(CROSSREF, {"query.bibliographic": ref.title, "rows": 5})
        items = (res or {}).get("items", [])
        if not items:
            return Verdict(raw, "not_found", "Crossref search returned nothing")
        best = max(items, key=lambda it: title_similarity(ref.title, (it.get("title") or [""])[0]))
        return self._judge(ref, best, "search")

    def check_text(self, text: str) -> List[Verdict]:
        return [self.check(r) for r in split_references(text)]
