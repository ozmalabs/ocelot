"""LOCAL Wikipedia store — replaces the laggy per-query HTTP fetch with a local
read of the HF `wikimedia/wikipedia` 20231101.en parquet dump.

A one-time index (sqlite: normalized title -> parquet file / row-group / offset)
makes a title lookup O(1) + lazy: only the row group holding the article is read
(a few MB), the rest stays on disk. This is the same world-adapter role as
web_world (external store -> graph), just local + fast. No network at query time.

  build_index()           one-time: scan the dump's TITLE column -> sqlite index.
  summary(title) -> dict  {title, extract(lead), text, source, kind} or None.
  search(query)  -> [title]  exact/normalised title match (+ a few variants).
  present()               True if the dump + index are ready.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
# wikimedia/structured-wikipedia enwiki — clean `name`(title) + `abstract`(lead)
# + `sections`. Newer + more complete than the old wikimedia/wikipedia dump.
_DUMP = _ROOT / "data" / "wiki" / "structured" / "enwiki" / "data"
_INDEX = _ROOT / "data" / "wiki" / "structured" / "title_index.sqlite"

_parquet_files: Optional[list[Path]] = None
_conn: Optional[sqlite3.Connection] = None

# The SNAPSHOT this store IS — provenance has a TIME (WHEN). This is the
# structured-wikipedia enwiki dump's snapshot, a fact ABOUT this store (which
# dump is on disk), not an epistemic judgement. The grounding step reads the
# agent's HELD understanding of what Wikipedia IS (reliability/conventions) off
# the graph; this only stamps the time + location of THIS read.
_SNAPSHOT = "2024-09 structured-wikipedia enwiki snapshot"


def _files() -> list[Path]:
    global _parquet_files
    if _parquet_files is None:
        _parquet_files = sorted(_DUMP.glob("*.parquet"))
    return _parquet_files


def _norm(title: str) -> str:
    """Normalise a title/query for matching: lowercase, underscores->spaces,
    collapse whitespace, strip. (Wikipedia titles are space-separated.)"""
    t = (title or "").replace("_", " ").strip().lower()
    return re.sub(r"\s+", " ", t)


def _dash_variants(nt: str) -> list[str]:
    """Title-key variants that differ ONLY in dash style. Wikipedia titles use a
    typographic en-dash (U+2013) in named-pair titles ('Mayer–Vietoris sequence',
    'Bass–Serre theory') where a reader naturally types an ASCII hyphen '-'. The
    index stores the dump's literal (en-dash) key, so a hyphen query misses a real
    article. Return the query as-is plus hyphen<->en-dash<->em-dash<->minus swaps
    (deduped, order-preserving). A mechanical surface normalisation — no meaning."""
    DASHES = ["-", "–", "—", "−"]  # hyphen, en, em, minus
    cands = [nt]
    # collapse every dash kind to a single hyphen, then re-emit each dash style.
    import re as _re
    collapsed = _re.sub("[%s]" % "".join(DASHES), "-", nt)
    for d in DASHES:
        v = collapsed.replace("-", d)
        if v not in cands:
            cands.append(v)
    return cands


def _lookup_row(title: str) -> Optional[tuple]:
    """The (fi,rg,off) index row for a title, trying dash-style variants. Returns
    the first matching row or None. Centralises the dash-tolerant title match so
    both summary() and search() resolve 'Mayer-Vietoris sequence' to the real
    en-dash article."""
    con = _index_conn()
    if con is None:
        return None
    for cand in _dash_variants(_norm(title)):
        row = con.execute(
            "SELECT fi,rg,off FROM t WHERE nt=? LIMIT 1", (cand,)).fetchone()
        if row is not None:
            return row
    return None


def present() -> bool:
    return _INDEX.exists() and bool(_files())


def _index_conn() -> Optional[sqlite3.Connection]:
    global _conn
    if _conn is None:
        if not _INDEX.exists():
            return None
        _conn = sqlite3.connect(f"file:{_INDEX}?mode=ro", uri=True,
                                check_same_thread=False)
    return _conn


# ---------------------------------------------------------------------------
# one-time index build
# ---------------------------------------------------------------------------

def build_index(progress: bool = True) -> int:
    """Scan the TITLE column of every parquet shard and write the sqlite index
    (norm_title -> file_idx, row_group, offset). Idempotent (rebuilds). Returns
    the number of titles indexed."""
    import pyarrow.parquet as pq
    files = _files()
    if not files:
        raise RuntimeError(f"no parquet shards under {_DUMP}")
    tmp = _INDEX.with_suffix(".building")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("CREATE TABLE t (nt TEXT, fi INT, rg INT, off INT)")
    n = 0
    for fi, path in enumerate(files):
        pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            titles = pf.read_row_group(rg, columns=["name"]).column(
                "name").to_pylist()
            con.executemany(
                "INSERT INTO t VALUES (?,?,?,?)",
                [(_norm(t), fi, rg, off) for off, t in enumerate(titles)])
            n += len(titles)
        if progress:
            print(f"  indexed shard {fi+1}/{len(files)}  ({n} titles)",
                  flush=True)
    con.commit()
    # an index on the normalised title for O(log n) lookup; keep the FIRST row
    # for a duplicate normalised title (dedup via a covering index is enough).
    con.execute("CREATE INDEX ix_nt ON t (nt)")
    con.commit()
    con.close()
    tmp.replace(_INDEX)
    global _conn
    _conn = None
    return n


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------

def _lead(text: str, max_chars: int = 600) -> str:
    text = (text or "").strip()
    # first paragraph, trimmed to a couple sentences.
    para = text.split("\n\n", 1)[0].strip() if "\n\n" in text else text
    m = list(re.finditer(r"[.!?](?:\s|$)", para))
    if len(m) >= 2:
        return para[: m[1].end()].strip()[:max_chars]
    return para[:max_chars].strip()


def _section_text(sections: Any) -> str:
    """Flatten the structured `sections` (list of {name, value, has_parts, ...})
    into plain text, depth-first. Defensive about the exact shape.

    The structured-wikipedia dump stores `sections` as a JSON *string* (not a
    parsed list), so a raw walk over the str collects nothing and the whole
    article body is silently dropped — only the abstract survives. Parse it
    first when it arrives as text; this is the read-faculty fix that unlocks the
    full body (e.g. the Mayer-Vietoris-for-amalgams sequence lives in the body of
    'Group cohomology', not its lead)."""
    if isinstance(sections, str):
        import json as _json
        try:
            sections = _json.loads(sections)
        except Exception:
            return sections.strip()
    out: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            v = node.get("value")
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
            for k in ("has_parts", "parts", "content"):
                walk(node.get(k))
        elif isinstance(node, (list, tuple)):
            for x in node:
                walk(x)

    walk(sections)
    return "\n\n".join(out)


def _read_row(fi: int, rg: int, off: int) -> Optional[dict]:
    import pyarrow.parquet as pq
    files = _files()
    if fi >= len(files):
        return None
    pf = pq.ParquetFile(files[fi])
    tbl = pf.read_row_group(rg, columns=["name", "abstract", "sections"])
    if off >= tbl.num_rows:
        return None
    abstract = tbl.column("abstract")[off].as_py() or ""
    sections = tbl.column("sections")[off].as_py()
    body = _section_text(sections)
    text = (abstract + ("\n\n" + body if body else "")).strip()
    return {"title": tbl.column("name")[off].as_py(),
            "abstract": abstract, "text": text}


def summary(title: str) -> Optional[dict[str, Any]]:
    """Local Wikipedia summary for a title (or None). Mirrors web_world.
    `kind="definition"` — the article lead is the ENTITY's definition (the
    reference-route's queried-property check reads this)."""
    if _index_conn() is None:
        return None
    row = _lookup_row(title)
    if row is None:
        return None
    art = _read_row(*row)
    if art is None or not art.get("text"):
        return None
    # the structured `abstract` IS the clean lead (no regex needed); fall back to
    # the first sentences of the body if a row has no abstract.
    extract = (art.get("abstract") or "").strip() or _lead(art["text"])
    # PROVENANCE the store KNOWS about itself: WHERE (this article — the location
    # of the knowledge), WHEN (this dump's snapshot), and the genre tags that say
    # WHAT this source is (an encyclopedia, crowd-edited consensus, encyclopedic
    # register). A competent reader knows what it read — the source is part of
    # the meaning. The EPISTEMIC WEIGHT (reliability) is NOT stamped here; the
    # grounding step reads that off the agent's HELD `wikipedia` concept (not a
    # Python constant). These fields are facts about the store; provenance has a
    # WHERE and a WHEN.
    provenance = {
        "source": "wikipedia",
        "genre": "encyclopedia",
        "who": "editorial_consensus",
        "how": "encyclopedic",
        "where": art["title"],
        "when": _SNAPSHOT,
    }
    return {"title": art["title"], "extract": extract[:600],
            "text": art["text"], "source": "local_wiki", "kind": "definition",
            "provenance": provenance}


# A DISAMBIGUATION lead is NOT a definition — it is a list of senses ('X may
# refer to:'). A Wikipedia disambiguation page's lead is shaped 'X may refer to:'
# / 'X or Y may refer to:' / 'X, ... may refer to the following:' followed by a
# bulleted list, with no copula-definition. The recursive descent must NOT
# comprehend a genus from it (a near-miss disambiguation poisons the chain). This
# is a cheap LEAD-SHAPE heuristic (the permitted thin boundary surface detector,
# CLAUDE.md) — not a meaning decision, no LLM. HONEST: it is a surface heuristic
# (the 'may refer to' phrasing); a disambiguation page that does not use it would
# slip through (then the normal comprehension stop catches it).
_DISAMBIG_LEAD = re.compile(
    r"\bmay\s+(?:also\s+)?refer\s+to\b"
    r"|\bmay\s+(?:also\s+)?mean\b"
    r"|\bcan\s+refer\s+to\b"
    r"|\bis\s+the\s+name\s+of\s+(?:several|various|multiple)\b",
    re.IGNORECASE)


def is_disambiguation(extract: str) -> bool:
    """True iff the lead `extract` is a DISAMBIGUATION lead ('X may refer to:') —
    a list of senses, NOT a definition. A cheap lead-shape heuristic on the first
    ~120 chars (the 'may refer to' phrasing is near the start). The descent treats
    a disambiguation lead as un-comprehended (it does not ground a bogus genus
    from it). Surface detector, no decision about meaning."""
    head = (extract or "").strip()[:160]
    return bool(_DISAMBIG_LEAD.search(head))


def search(query: str, limit: int = 5) -> list[str]:
    """Title candidates for a query (exact normalised match + simple variants).
    Returns a list of real titles (best first)."""
    con = _index_conn()
    if con is None:
        return []
    nq = _norm(query)
    out: list[str] = []
    seen = set()
    for cand in (nq, nq.rstrip("s"), nq + "s"):
        for (fi, rg, off) in con.execute(
                "SELECT fi,rg,off FROM t WHERE nt=? LIMIT ?", (cand, limit)):
            art = _read_row(fi, rg, off)
            if art and art["title"] not in seen:
                seen.add(art["title"])
                out.append(art["title"])
            if len(out) >= limit:
                return out
    return out
