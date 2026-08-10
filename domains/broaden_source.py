#!/usr/bin/env python3
"""broaden_source — EXTEND the theorem-RETRIEVE reading path BEYOND the local wiki
dump, GENERALLY and READ-FROM-SOURCE.

THE GAP THIS CLOSES (the user's framing). The RETRIEVE link (recognise_group_form.
retrieve_theorems -> ground_reductions._read_statement) read theorems from ONE fixed
local store: wiki_local.summary(title). The "nearest unreached" HLE theorems (the
Grigorchuk index-n subgroup count, the Orlik-Solomon arrangement Poincare polynomial)
were called "beyond the corpus" — but the SOURCE is not fixed. The project already
fetches + reads arXiv .tex (domains/arxiv_local, scripts/fetch_arxiv). This module
makes RETRIEVE read from that BROADER source GENERALLY:

  · SCAN the LOCAL arXiv statement corpus (data/arxiv/*, already-ingested .tex) for a
    statement carrying the applicability keywords — the same sentence-scan _read_
    statement does over wiki, now over the frontier-literature statements too.
  · when the LOCAL stores all miss AND fetching is permitted, run ONE keyword QUERY
    against the live arXiv API (the general reader, scripts/fetch_arxiv), INGEST the
    matching papers' .tex into data/arxiv, and re-scan. This is a BROAD read-path over
    a BROAD source keyed on (the retrieve query) — NOT one hand-fetched article per
    question, NOT a per-QID branch, NOT a baked answer. The query is built from the
    SAME title + keywords _read_statement is already given.

The retrieve COST is now near-zero-marginal: a new question whose theorem the wiki dump
lacks no longer needs a new hand-authored faculty — it needs the SAME read-path to scan
(and, if missing, fetch) the broad source. Only the per-FORM recognizer cost remains.

FAITHFUL (CLAUDE.md): a WORLD ADAPTER. It fetches external .tex and SEQUENCES the held
corpus readers (arxiv_local) + the held sentence-scan; it decides NO math, holds NO
agent state, runs NO rule engine, no LLM, no Rust. The harvested sentence is the
SOURCE's own words; whether a number comes back depends on what the source CONTAINS —
an HONEST miss (and the cited-prior fallback) when it does not.

Fetching is OPT-IN via the env flag OZMA_BROADEN_FETCH=1 (so the offline retest stays
deterministic + the polite arXiv delay is not paid unless asked). When fetching is off
or blocked, the LOCAL arXiv scan still broadens the source beyond wiki.
"""
from __future__ import annotations

import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional

_ROOT = Path(__file__).resolve().parent.parent
_ARXIV_DIR = _ROOT / "data" / "arxiv"

_UA = "ozma-research/0.1 (arxiv math ingest; mailto:hrdwrbob@gmail.com)"
_API = "http://export.arxiv.org/api/query"
_EPRINT = "https://arxiv.org/e-print/"
_DELAY = 3.0  # arXiv's polite delay between requests (seconds).

# fetching is opt-in (offline retest stays deterministic unless explicitly asked).
_FETCH_ENABLED = os.environ.get("OZMA_BROADEN_FETCH", "0") not in ("0", "", "false")
# a bounded fetch: how many papers a single retrieve query ingests (the broad-but-
# bounded read; full arXiv is the same path at a larger bound).
_FETCH_PER_QUERY = int(os.environ.get("OZMA_BROADEN_FETCH_N", "6"))


def _sentence_carries(sl: str, keywords: List[str],
                      require_pair: Optional[List[List[str]]]) -> bool:
    """The SAME applicability test _read_statement uses: when require_pair is set the
    sentence must carry BOTH terms of some pair; else any one keyword suffices."""
    if require_pair is not None:
        return any(all(t in sl for t in pair) for pair in require_pair)
    return any(k in sl for k in keywords)


def scan_arxiv_local(keywords: List[str], fallback_cite: str,
                     require_pair: Optional[List[List[str]]] = None) -> Optional[dict]:
    """SCAN the already-ingested arXiv statement corpus for a statement carrying the
    applicability keywords. Returns the {found, cite, where, when, source} dict of the
    FIRST qualifying statement (sentence-scanned, same shape as the wiki read), or None
    when nothing in the local arXiv matches. World-adapter read; no decision."""
    try:
        from domains import arxiv_local as _al
        if not _al.present():
            return None
        statements = _al.statements()
    except Exception:
        return None
    for e in statements:
        body = e.get("text") or e.get("statement") or ""
        if not body:
            continue
        for snt in re.split(r"(?<=[.])\s+", body):
            sl = snt.lower()
            if _sentence_carries(sl, keywords, require_pair):
                return {"found": True, "cite": snt.strip()[:600],
                        "where": f"arXiv:{e.get('paper','?')} [{e.get('kind','')}"
                                 f" {e.get('key','')}]",
                        "when": "", "source": "arxiv_local"}
    return None


def _build_query(title: str, keywords: List[str]) -> str:
    """Build ONE arXiv keyword query from the SAME title + keywords the retrieve gives.
    The TITLE phrase is the primary (broad) clause; ONE distinctive multi-word topic
    keyword narrows it with AND (broad enough to return candidate papers, then the
    sentence-scan does the precise filtering). Numeric / generic / connective keywords
    are NOT phrase-AND'd — '"index 4"' as an exact phrase over-narrows to zero hits. A
    mechanical surface->query translation, not a decision about meaning."""
    if not title:
        return 'all:"' + (keywords[0] if keywords else "") + '"'
    parts = [f'all:"{title}"']
    # a distinctive TOPIC keyword: multi-word, no digit, not a generic connective.
    generic = {"exact sequence", "long exact sequence", "deduce", "divided by",
               "index", "finite", "cd", "subgroup of index", "subgroups of index",
               "number of subgroups", "index 4"}
    topic = [k for k in keywords
             if " " in k and not any(c.isdigit() for c in k)
             and k.lower() not in generic]
    if topic:
        parts.append(f'all:"{topic[0]}"')
    return " AND ".join(parts)


def _get(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def _fetch_into_corpus(title: str, keywords: List[str]) -> int:
    """FETCH papers matching the retrieve query from the live arXiv API + INGEST their
    .tex into data/arxiv (the general arxiv reader's store). Returns the number of NEW
    papers ingested. Mechanical world-adapter I/O; honest 0 on any block. The query is
    the SAME title+keywords the retrieve already has — one query per (form,about), NOT
    per question."""
    if not _FETCH_ENABLED:
        return 0
    try:
        from scripts import fetch_arxiv as _fa  # the held ingest world-adapter
    except Exception:
        # scripts/ may not be a package on the path; import the file directly.
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "_fetch_arxiv", str(_ROOT / "scripts" / "fetch_arxiv.py"))
            _fa = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_fa)
        except Exception:
            _fa = None
    q = urllib.parse.quote(_build_query(title, keywords))
    url = (f"{_API}?search_query={q}&max_results={_FETCH_PER_QUERY}"
           f"&sortBy=relevance")
    try:
        xml = _get(url, timeout=40).decode("utf-8", "replace")
    except Exception:
        return 0
    ids = re.findall(r"<id>https?://arxiv\.org/abs/([^<]+)</id>", xml)
    ids = [i.rsplit("v", 1)[0] if re.search(r"v\d+$", i) else i for i in ids]
    _ARXIV_DIR.mkdir(parents=True, exist_ok=True)
    new = 0
    for aid in ids[:_FETCH_PER_QUERY]:
        safe = aid.replace("/", "_")
        pdir = _ARXIV_DIR / safe
        if pdir.exists() and any(pdir.glob("*.tex")):
            continue  # already on disk
        time.sleep(_DELAY)
        try:
            if _fa is not None:
                texs = _fa.fetch_source(aid)
            else:
                raw = _get(_EPRINT + aid, timeout=90)
                texs = {}
        except Exception:
            texs = {}
        if not texs:
            continue
        pdir.mkdir(parents=True, exist_ok=True)
        for fname, bdy in texs.items():
            (pdir / fname).write_text(bdy, encoding="utf-8")
        (pdir / "_cat.txt").write_text("broaden_source:fetched", encoding="utf-8")
        new += 1
    if new:
        # invalidate the arxiv_local cache so the new papers are seen on re-scan.
        try:
            from domains import arxiv_local as _al
            _al._entries = None
            _al._by_key = None
        except Exception:
            pass
    return new


def read_from_broad_source(title: str, keywords: List[str], fallback_cite: str,
                           require_pair: Optional[List[List[str]]] = None
                           ) -> Optional[dict]:
    """The BROADENED read: scan the local arXiv statement corpus; if it misses AND
    fetching is enabled, fetch the retrieve query's papers into the corpus and re-scan.
    Returns the {found, cite, where, when, source} dict of the first qualifying source
    sentence, or None when the broad source (local + any fetch) still does not carry it
    (the honest miss -> caller keeps the cited-prior fallback). General; no per-QID."""
    hit = scan_arxiv_local(keywords, fallback_cite, require_pair)
    if hit is not None:
        return hit
    if _fetch_into_corpus(title, keywords) > 0:
        hit = scan_arxiv_local(keywords, fallback_cite, require_pair)
        if hit is not None:
            return hit
    return None


__all__ = ["scan_arxiv_local", "read_from_broad_source"]
