"""Lightweight question-to-subject normalization shared by lookup teachers.

This module intentionally has no corpus, dataframe, parquet, or teacher imports
so fast dictionary/grammar lookups do not load the optional Wikipedia stack.
"""
from __future__ import annotations

import re


_PREFIX_PATTERNS = [
    r"^what\s+(?:is|are|was|were)\s+(?:the|a|an)\s+",
    r"^what\s+(?:is|are|was|were)\s+",
    r"^tell\s+me\s+about\s+(?:the\s+)?",
    r"^who\s+(?:is|was|are|were)\s+",
    r"^describe\s+(?:the\s+)?",
    r"^explain\s+(?:the\s+)?",
    r"^define\s+(?:the\s+)?",
    r"^how\s+does\s+(?:a\s+|an\s+|the\s+)?",
]
_PREFIX_RE = re.compile("|".join(_PREFIX_PATTERNS), re.IGNORECASE)
_TRAILING_RE = re.compile(r"[?.,!;:]+\s*$")


def extract_subject(question: str) -> str:
    """Strip a small set of lookup prefixes and trailing punctuation."""
    query = str(question or "").strip()
    query = _PREFIX_RE.sub("", query)
    query = _TRAILING_RE.sub("", query)
    return query.strip()
