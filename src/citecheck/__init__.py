"""Detect hallucinated / fabricated citations by verifying them against Crossref."""
from .parser import Reference, parse_reference, split_references
from .verify import CitationChecker, Verdict, title_similarity

__all__ = ["CitationChecker", "Verdict", "Reference", "parse_reference", "split_references", "title_similarity"]
__version__ = "0.1.0"
