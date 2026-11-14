"""ocelot_code_search — lexical hybrid code search (BM25 + graph RRF).

This is the no-embedding half of hybrid retrieval:

  * the existing repo-map tag cache supplies definitions and a file reference
    graph (``update_tag_cache`` / ``build_reference_graph``);
  * an in-memory inverted index covers three fields per file: the repo-relative
    path, definition symbol names, and source lines;
  * BM25 ranks files lexically (k1=1.5, b=0.75 by default);
  * repo-map PageRank supplies a query-independent structural prior;
  * the two rankings are fused with Reciprocal Rank Fusion (k=60), with the
    graph term weighted by GRAPH_WEIGHT so it breaks ties and cannot
    overturn a clear lexical lead;
  * results carry the fused score, both component scores, matching symbols,
    and a bounded source snippet.

No network, no embeddings, no model, and no dependencies beyond the stdlib
plus what ``ocelot_repo_map`` already uses. The index lives in process memory,
cached under the tag cache's root hash so repeated searches do not re-tokenize
the tree; the tag cache itself keeps re-parsing incremental. DEV TOOLING, NOT
AGENT RUNTIME.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import marshal
import math
import os
import re
import sys
import tempfile
from array import array
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from scripts.ocelot_repo_map import (
    LANGUAGES,
    MAX_FILE_BYTES,
    SKIP_PARTS,
    _index_workers,
    graph_prior,
    update_tag_cache,
)

# BM25 defaults; both are keyword arguments on code_search().
BM25_K1 = 1.5
BM25_B = 0.75

# Reciprocal Rank Fusion constant (the standard value from the RRF paper).
RRF_K = 60

# Weight of the graph (PageRank) rank term in the fused score. The BM25 term
# always has weight 1. The graph term is a tie-breaker and a weak prior, so a
# hub cannot outrank a file that leads clearly on lexical match.
GRAPH_WEIGHT = 0.25

# Field weights in the single concatenated BM25 document per file. A symbol
# name hit is a stronger signal than the same term in a comment or string.
FIELD_WEIGHTS = {"path": 3.0, "symbol": 4.0, "line": 1.0}

# Persisted per-file term rows (see _term_rows). Bump SEARCH_CACHE_VERSION on
# a layout change and TOKENIZER_VERSION on any change to _terms,
# _identifier_terms, _definitions or the field weights. FIELD_WEIGHTS is also
# part of the side file's key.
SEARCH_CACHE_VERSION = 1
TOKENIZER_VERSION = 1
SEARCH_SIDE_SUFFIX = ".search.marshal"
# Cold tokenization runs in a process pool once this many files need it.
SEARCH_PARALLEL_MIN_FILES = 64
SEARCH_PARALLEL_CHUNK = 64

# Build facts from the most recent _build_index call, for the bench.
LAST_BUILD: dict[str, Any] = {}

# A snippet is one source line, trimmed to this many characters.
MAX_SNIPPET_CHARS = 240
MAX_SYMBOLS = 8

_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "in", "into", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "with",
})

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_CAMEL_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def _identifier_terms(raw: str) -> list[str]:
    """Whole identifier plus camel/snake parts, lower-cased and filtered."""
    forms = {raw.lower()}
    forms.update(part.lower() for part in _CAMEL_RE.findall(raw))
    return sorted(t for t in forms
                  if len(t) >= 2 and t not in _STOPWORDS)


def _terms(text: str) -> list[str]:
    """Tokenize text into searchable terms, preserving occurrence counts."""
    out: list[str] = []
    for raw in _WORD_RE.findall(text or ""):
        out.extend(_identifier_terms(raw))
    return out


def _query_terms(query: str) -> list[str]:
    """Unique, sorted query terms (a term set, not a phrase)."""
    return sorted(set(_terms(query)))


def _definitions(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Deduplicated definition tags for one cache entry, source-ordered."""
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for tag in entry.get("tags") or []:
        if tag.get("kind") != "def":
            continue
        name = str(tag.get("name") or "")
        if not name:
            continue
        line = int(tag.get("line") or 0)
        key = (name, line)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, "line": line,
                    "detail": str(tag.get("detail") or "")})
    out.sort(key=lambda s: (s["line"], s["name"]))
    return out


def _tokenize_file(root: str, rel: str,
                   defs: list[dict[str, Any]]) -> tuple[str, float,
                                                        tuple[str, ...],
                                                        tuple[float, ...]]:
    """Term frequencies for one file: (rel, length, terms, weights).

    Terms and weights are in the order the first occurrence is seen, the same
    order the old in-line code used, so the length sum is unchanged. Top-level
    so a process pool can run it.
    """
    tf: dict[str, float] = defaultdict(float)
    for term in _terms(rel):
        tf[term] += FIELD_WEIGHTS["path"]
    for sym in defs:
        for term in _terms(sym["name"]):
            tf[term] += FIELD_WEIGHTS["symbol"]
    source = ""
    try:
        path = Path(root) / rel
        if path.stat().st_size <= MAX_FILE_BYTES:
            source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        source = ""
    for line in source.splitlines():
        for term, count in Counter(_terms(line)).items():
            tf[term] += count * FIELD_WEIGHTS["line"]
    length = float(sum(tf.values()))
    terms = tuple(term for term, weight in tf.items() if weight > 0)
    weights = tuple(tf[term] for term in terms)
    return rel, length, terms, weights


def _tokenize_chunk(root: str, items: list[tuple[str, list[dict[str, Any]]]]
                    ) -> list[tuple[str, float, tuple[str, ...],
                                    tuple[float, ...]]]:
    return [_tokenize_file(root, rel, defs) for rel, defs in items]


def _side_key() -> str:
    return hashlib.sha256(json.dumps(
        [TOKENIZER_VERSION, FIELD_WEIGHTS],
        sort_keys=True).encode("utf-8")).hexdigest()


def search_side_cache_path(cache_path: str | Path) -> Path:
    """Side file that holds the per-file term rows, next to the tag cache."""
    return Path(f"{cache_path}{SEARCH_SIDE_SUFFIX}")


def _load_side(path: Path) -> dict[str, tuple[Any, ...]]:
    """Well-formed side rows, or {} on any version, key or load problem."""
    try:
        data = marshal.loads(path.read_bytes())
    except Exception:  # missing, unreadable or corrupt: rebuild instead
        LAST_BUILD["side_cache"] = "ignored: unreadable"
        return {}
    if (not isinstance(data, dict)
            or data.get("version") != SEARCH_CACHE_VERSION
            or data.get("key") != _side_key()
            or not isinstance(data.get("files"), dict)):
        LAST_BUILD["side_cache"] = "ignored: version or key mismatch"
        return {}
    rows: dict[str, tuple[Any, ...]] = {}
    for rel, row in data["files"].items():
        if (isinstance(rel, str) and isinstance(row, tuple) and len(row) == 5
                and isinstance(row[2], float)
                and isinstance(row[3], tuple) and isinstance(row[4], tuple)):
            rows[rel] = row
    LAST_BUILD["side_cache"] = "loaded"
    return rows


def _save_side(path: Path, rows: dict[str, tuple[Any, ...]]) -> None:
    """Atomic write (temp file, then os.replace). A failure only costs a rebuild."""
    doc = {"version": SEARCH_CACHE_VERSION, "key": _side_key(),
           "files": rows}
    try:
        payload = marshal.dumps(doc)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent),
                                   prefix=path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(payload)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        LAST_BUILD["side_written"] = len(payload)
    except (OSError, ValueError, TypeError) as exc:
        LAST_BUILD["side_written"] = f"failed: {type(exc).__name__}: {exc}"


def _term_rows(root: Path, cache: dict[str, Any], rels: list[str],
               cache_path: Path | None, prune: bool
               ) -> dict[str, tuple[float, tuple[str, ...], tuple[float, ...]]]:
    """Term rows for every rel in the view, from the side file where valid.

    A side row is valid when its tag sha256 and extractor fingerprint equal
    the current tag entry's. Only missing or stale rows are tokenized. Rows
    for files outside a full-scan view are dropped; subset calls keep them.
    """
    tag_files = cache.get("files") or {}
    side_path = search_side_cache_path(cache_path) if cache_path else None
    if side_path is None:
        side = {}
        LAST_BUILD["side_cache"] = "disabled"
    elif not side_path.exists():
        side = {}
        LAST_BUILD["side_cache"] = "absent"
    else:
        side = _load_side(side_path)
    rows: dict[str, tuple[float, tuple[str, ...], tuple[float, ...]]] = {}
    todo: list[str] = []
    for rel in rels:
        entry = tag_files.get(rel) or {}
        hit = side.get(rel)
        if (hit is not None and hit[0] == entry.get("sha256")
                and hit[1] == entry.get("fp")):
            rows[rel] = (hit[2], hit[3], hit[4])
        else:
            todo.append(rel)

    LAST_BUILD.update({"rows": len(rels), "reused": len(rels) - len(todo),
                       "tokenized": len(todo), "parallel": 1})
    results = None
    workers = _index_workers()
    if workers > 1 and len(todo) >= SEARCH_PARALLEL_MIN_FILES:
        try:
            items = [(rel, _definitions(tag_files.get(rel) or {}))
                     for rel in todo]
            chunks = [items[i:i + SEARCH_PARALLEL_CHUNK]
                      for i in range(0, len(items), SEARCH_PARALLEL_CHUNK)]
            with concurrent.futures.ProcessPoolExecutor(
                    max_workers=workers) as pool:
                futures = [pool.submit(_tokenize_chunk, str(root), chunk)
                           for chunk in chunks]
                results = [row for fut in futures for row in fut.result()]
            LAST_BUILD["parallel"] = workers
        except (OSError, concurrent.futures.BrokenExecutor) as exc:
            LAST_BUILD["parallel"] = f"fallback: {type(exc).__name__}: {exc}"
            results = None
    if results is None:
        results = [_tokenize_file(str(root), rel,
                                  _definitions(tag_files.get(rel) or {}))
                   for rel in todo]

    side_rows = dict(side)
    for rel, length, terms, weights in results:
        entry = tag_files.get(rel) or {}
        terms = tuple(sys.intern(t) for t in terms)
        rows[rel] = (length, terms, weights)
        side_rows[rel] = (entry.get("sha256"), entry.get("fp"),
                          length, terms, weights)
    if prune:
        view = set(rels)
        for stale in [r for r in side_rows if r not in view]:
            side_rows.pop(stale, None)
    dropped = set(side) - set(side_rows)
    if side_path is not None and rels and (todo or dropped):
        _save_side(side_path, side_rows)
    return rows


def _build_index(root: Path, cache: dict[str, Any],
                 cache_path: Path | None = None,
                 prune: bool = False) -> dict[str, Any]:
    """Build the in-memory inverted index from the tag cache + source files.

    Each file is one BM25 document. Its weighted term frequencies combine the
    path (3x), definition names (4x), and source lines (1x). Postings are
    parallel ``array`` objects (file-id, weight) rather than nested dicts; on
    this tree that is ~12 bytes per posting instead of a tuple plus dict
    entry. Snippets are found by scanning the source of the few returned
    files, so the index does not retain a line posting for every term.
    """
    rels = sorted(cache.get("files") or {})
    LAST_BUILD.clear()
    postings_ids: dict[str, array] = {}
    postings_tf: dict[str, array] = {}
    lengths = array("d")
    symbols: dict[str, list[dict[str, Any]]] = {}
    tag_files = cache.get("files") or {}
    for rel in rels:
        symbols[rel] = _definitions(tag_files.get(rel) or {})

    rows = _term_rows(root, cache, rels, cache_path, prune)

    for file_id, rel in enumerate(rels):
        length, terms, weights = rows[rel]
        lengths.append(length)
        for term, weight in zip(terms, weights):
            ids = postings_ids.get(term)
            if ids is None:
                postings_ids[term] = array("I", [file_id])
                postings_tf[term] = array("d", [weight])
            else:
                ids.append(file_id)
                postings_tf[term].append(weight)

    n_files = len(rels)
    avgdl = (sum(lengths) / n_files) if n_files else 0.0
    return {
        "files": rels,
        "postings_ids": postings_ids,
        "postings_tf": postings_tf,
        "lengths": lengths,
        "avgdl": avgdl,
        "symbols": symbols,
        "n_files": n_files,
    }


def _bm25_scores(index: dict[str, Any], terms: list[str],
                 k1: float, b: float) -> tuple[dict[str, float],
                                                dict[str, float]]:
    """BM25 over the concatenated field-weighted documents."""
    rels = index["files"]
    scores = [0.0] * len(rels)
    idf: dict[str, float] = {}
    n = max(1, int(index["n_files"]))
    avgdl = float(index["avgdl"]) or 1.0
    lengths = index["lengths"]
    for term in terms:
        ids = index["postings_ids"].get(term)
        if not ids:
            continue
        weights = index["postings_tf"][term]
        df = len(ids)
        idf[term] = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
        for file_id, tf in zip(ids, weights):
            dl = float(lengths[file_id])
            denom = tf + k1 * (1.0 - b + b * dl / avgdl)
            if denom <= 0:
                continue
            scores[file_id] += idf[term] * tf * (k1 + 1.0) / denom
    return {rels[i]: score for i, score in enumerate(scores) if score > 0}, idf


def _pagerank(cache: dict[str, Any]) -> dict[str, float]:
    """Query-independent repo-map reference centrality (memoised per view)."""
    return graph_prior(cache)


def _competition_ranks(scores: dict[str, float]) -> dict[str, int]:
    """1-based standard competition ranks: ties share the first position.

    Scores are compared after rounding to 12 places, so float noise in equal
    scores does not split a tie. Equal scores 3, 2, 2, 1 give ranks 1, 2, 2, 4.
    """
    ordered = sorted(scores, key=lambda rel: (-scores[rel], rel))
    ranks: dict[str, int] = {}
    previous: float | None = None
    rank = 0
    for position, rel in enumerate(ordered, 1):
        key = round(scores[rel], 12)
        if key != previous:
            rank = position
            previous = key
        ranks[rel] = rank
    return ranks


def _matched_symbols(symbols: list[dict[str, Any]], terms: list[str],
                     idf: dict[str, float]) -> list[dict[str, Any]]:
    wanted = set(terms)
    out: list[dict[str, Any]] = []
    for sym in symbols:
        matched = sorted(set(_terms(sym["name"])) & wanted)
        if not matched:
            continue
        score = sum(idf.get(t, 0.0) for t in matched)
        out.append({"name": sym["name"], "line": sym["line"],
                    "detail": sym["detail"],
                    "score": round(score, 6)})
    out.sort(key=lambda s: (-s["score"], s["line"], s["name"]))
    return out[:MAX_SYMBOLS]


def _snippet_for(root: Path, rel: str, terms: list[str],
                 line_cache: dict[str, list[str]]) -> tuple[int, str] | None:
    """Scan one result file for its best query line and bound the snippet."""
    if rel not in line_cache:
        try:
            line_cache[rel] = (root / rel).read_text(
                encoding="utf-8", errors="replace").splitlines()
        except OSError:
            line_cache[rel] = []
    lines = line_cache[rel]

    choice: tuple[int, str] | None = None
    best_key: tuple[int, int, int] | None = None
    for lineno, raw in enumerate(lines, 1):
        text = raw.strip()
        if not text:
            continue
        counts = Counter(_terms(text))
        distinct = sum(1 for t in terms if counts.get(t))
        if distinct == 0:
            continue
        total = sum(counts.get(t, 0) for t in terms)
        key = (distinct, total, -lineno)  # earlier line wins an exact tie
        if best_key is None or key > best_key:
            best_key = key
            choice = (lineno, text)

    if choice is None:
        return None
    lineno, text = choice
    if len(text) > MAX_SNIPPET_CHARS:
        text = text[:MAX_SNIPPET_CHARS - 3].rstrip() + "..."
    return lineno, text


# A one-entry process cache: search is a read tool and the tag cache's root
# hash changes whenever any indexed file's content changes. Rebuilding the
# inverted index is the expensive part on a full tree (~20-60 s); retaining
# one index makes repeated MCP searches cheap without unbounded memory.
_INDEX_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}


def _get_index(root: Path, cache_path: Path,
               cache: dict[str, Any], prune: bool = False) -> dict[str, Any]:
    key = (str(root), str(cache_path), str(cache.get("root_hash") or ""))
    index = _INDEX_CACHE.get(key)
    if index is None:
        index = _build_index(root, cache, cache_path, prune)
        _INDEX_CACHE.clear()
        _INDEX_CACHE[key] = index
    return index


def _discover_source_files(root: Path) -> list[str]:
    """Best-effort flat-fixture fallback for an empty repo-map scan.

    ``update_tag_cache`` defaults to repo-map SOURCE_DIRS. A temporary fixture
    with ``a.py`` at its root has none of those dirs, so when the default scan
    yields no files we walk the root with the same extension and skip rules.
    The real repository is never affected: its default cache is non-empty.
    """
    out: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in LANGUAGES:
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in SKIP_PARTS for part in rel.split("/")):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        out.append(rel)
    return out


def code_search(root: str | Path, query: str, *, limit: int = 20,
                cache_path: str | Path | None = None,
                files: Iterable[str] | None = None,
                include_snippet: bool = True,
                k1: float = BM25_K1, b: float = BM25_B,
                rrf_k: int = RRF_K) -> dict[str, Any]:
    """Search the repo with BM25, reranked by repo-map PageRank via RRF.

    Args:
        root: repository root.
        query: natural-language or identifier query; empty is not an error.
        limit: maximum file results to return (0 returns no results).
        cache_path: tag-cache path. ``None`` means
            ``<root>/var/ocelot_dev_tags.json`` so a search in a fixture or a
            second checkout cannot clobber the main tree's cache.
        files: optional repo-relative file subset to index.
        include_snippet: include ``line`` and ``snippet`` for each result.
        k1, b: BM25 parameters. Defaults 1.5 and 0.75.
        rrf_k: RRF constant. Default 60.

    Returns:
        ``{ok, query, results, n, bm25, rrf_k, fusion, index}``. Each result is
        ``{path, score, bm25, bm25_rank, graph, graph_rank, symbols,
        line?, snippet?}``. ``score`` is the fused score
        ``1/(rrf_k+bm25_rank) + GRAPH_WEIGHT/(rrf_k+graph_rank)``; the graph
        term is omitted when the file has no PageRank value. Equal BM25 scores
        share a rank, and so do equal PageRank values. ``graph`` is the
        PageRank score, and ``symbols`` the matched definitions.
        ``line``/``snippet`` appear only when a matching source line exists
        and ``include_snippet`` is true.
    """
    raw_query = "" if query is None else str(query)
    k1 = max(0.0, float(k1))
    b = min(1.0, max(0.0, float(b)))
    rrf_k = max(1, int(rrf_k))
    limit = max(0, int(limit))
    meta = {"bm25": {"k1": k1, "b": b}, "rrf_k": rrf_k,
            "fusion": {"rrf_k": rrf_k, "graph_weight": GRAPH_WEIGHT}}

    terms = _query_terms(raw_query)
    if not raw_query.strip():
        return {"ok": True, "query": raw_query, "results": [], "n": 0,
                "empty": True, "note": "empty query; nothing to search",
                **meta}
    if not terms:
        return {"ok": True, "query": raw_query, "results": [], "n": 0,
                "empty": False,
                "note": "query has no searchable terms (stopwords or too "
                        "short)", **meta}

    root = Path(root).resolve()
    if not root.is_dir():
        return {"ok": False, "query": raw_query, "results": [], "n": 0,
                "error": f"not a directory: {root}", **meta}
    if cache_path is None:
        cache_path = root / "var" / "ocelot_dev_tags.json"

    cache, _stats = update_tag_cache(root, cache_path=Path(cache_path),
                                     files=files)
    prune = files is None
    if files is None and not cache.get("files"):
        discovered = _discover_source_files(root)
        if discovered:
            cache, _stats = update_tag_cache(root,
                                             cache_path=Path(cache_path),
                                             files=discovered)
            prune = False
    index = _get_index(root, Path(cache_path), cache, prune)
    if limit == 0 or index["n_files"] == 0:
        return {"ok": True, "query": raw_query, "results": [], "n": 0,
                "index": {"files": index["n_files"],
                          "terms": len(index["postings_ids"])}, **meta}

    bm25, idf = _bm25_scores(index, terms, k1, b)
    pagerank = _pagerank(cache)

    bm25_rank = _competition_ranks(bm25)
    graph_rank = _competition_ranks(pagerank)

    fused: list[tuple[float, float, str]] = []
    for rel in bm25:
        score = 1.0 / (rrf_k + bm25_rank[rel])
        if rel in graph_rank:
            score += GRAPH_WEIGHT / (rrf_k + graph_rank[rel])
        fused.append((score, bm25[rel], rel))
    fused.sort(key=lambda item: (-item[0], -item[1], item[2]))

    line_cache: dict[str, list[str]] = {}
    results: list[dict[str, Any]] = []
    for score, lexical, rel in fused[:limit]:
        item: dict[str, Any] = {
            "path": rel,
            "score": round(score, 6),
            "bm25": round(lexical, 6),
            "bm25_rank": bm25_rank[rel],
            "graph": round(pagerank.get(rel, 0.0), 6),
            "graph_rank": graph_rank.get(rel),
            "symbols": _matched_symbols(index["symbols"].get(rel, []),
                                        terms, idf),
        }
        if include_snippet:
            picked = _snippet_for(root, rel, terms, line_cache)
            if picked is not None:
                item["line"], item["snippet"] = picked
        results.append(item)

    return {
        "ok": True,
        "query": raw_query,
        "results": results,
        "n": len(results),
        "index": {"files": index["n_files"],
                  "terms": len(index["postings_ids"])},
        **meta,
    }
