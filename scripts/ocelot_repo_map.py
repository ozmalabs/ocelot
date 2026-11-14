"""ocelot_repo_map — ranked, token-budgeted repo maps and impact queries.

This is the graph/tree enhancement distilled from the current coding-agent
landscape (Aider's repo map, RepoGraph, CodexGraph, Codebase-Memory, arbor,
context-link, Sourcegraph/SCIP):

  * tree-sitter `tags.scm` extracts definitions and references per file;
  * files are nodes in a weighted reference graph (referencer -> definer);
  * personalized PageRank ranks files for the current task;
  * a token budget selects a three-tier map: full outlines for the hottest
    files, public symbols for the middle, a file listing for the tail;
  * the tag cache is content-hash incremental (Merkle-like file sync), so
    unchanged files are never re-parsed.

DEV TOOLING, NOT AGENT RUNTIME. The map is a reading aid; it never edits.
The canonical edit path remains the op list in `ocelot_edit.py`.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
CACHE_VERSION = 3
# A file whose mtime is within this window of the moment it was hashed may
# change again without a visible size or mtime change at the same second
# (racy-git rule). Such entries are re-hashed instead of trusted by mtime.
RACY_NS = 2_000_000_000
DEFAULT_CACHE = ROOT / "var" / "ocelot_dev_tags.json"
from scripts.ocelot_tag_languages import (  # noqa: E402
    LANGUAGES as _TAG_LANGUAGES,
    extract_tags as _registry_extract_tags,
    extract_tags_status,
    extractor_fingerprint,
)
LANGUAGES = {suffix: entry["module"]
             for suffix, entry in _TAG_LANGUAGES.items()
             if entry.get("module")}
SOURCE_DIRS = (
    "runners/dsl/src",
    "runners/dsl/tests",
    "domains",
    "domains_rs",
    "worlds",
    "substrate",
    "scripts",
    "tools",
    "tests",
)
SKIP_PARTS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", "node_modules",
    "target", "build", ".worktrees", ".claude", "data", "var", "runs",
    "recordings", "scratch_rr", "scratchpad3", ".bigtmp",
}
MAX_FILE_BYTES = 2 * 1024 * 1024


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _skipped(rel: str) -> bool:
    return any(part in SKIP_PARTS for part in rel.split("/"))


def _source_files(root: Path) -> list[str]:
    out: list[str] = []
    for d in SOURCE_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix not in LANGUAGES:
                continue
            try:
                rel = _rel(root, p)
            except ValueError:
                continue
            if _skipped(rel):
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            out.append(rel)
    return out


def _grammar(language: str):
    import importlib
    return importlib.import_module(LANGUAGES[language])


def _tag_query_path(grammar_module) -> Path | None:
    p = Path(grammar_module.__file__).resolve().parent / "queries" / "tags.scm"
    return p if p.exists() else None


_GENERIC_SYMBOLS = {
    "new", "default", "eq", "ne", "hash", "fmt", "drop", "clone", "from",
    "into", "as_ref", "as_mut", "deref", "index", "next", "add", "sub",
    "mul", "div", "shl", "shr", "bitand", "bitor", "bitxor", "not", "neg",
}

_GENERIC_IDENTS = {
    "get", "set", "data", "name", "value", "self", "init", "main", "run",
    "test", "read", "write", "load", "save", "open", "close", "update",
    "create", "delete", "true", "false", "none", "str", "int", "list",
    "dict", "set", "len", "type", "object", "result", "args", "kwargs",
    "item", "items", "key", "keys", "path", "file", "node", "nodes", "id",
}


def extract_tags(path: str | Path, source: str) -> list[dict[str, Any]]:
    """Definition/reference tags via the shared multi-language registry.

    The registry (`ocelot_tag_languages`) is the only extractor: Python on the
    stdlib-AST fast path, other languages on each grammar's `queries/tags.scm`.
    A missing grammar yields an empty list for that file, never an exception.
    """
    return _registry_extract_tags(path, source)


def _load_cache(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if (isinstance(data, dict) and data.get("version") == CACHE_VERSION
                and isinstance(data.get("files"), dict)):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"version": CACHE_VERSION, "files": {}}


def _save_cache(path: Path, data: dict[str, Any]) -> None:
    """Atomic write: a unique temp file in the target directory, then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent),
                               prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(data, separators=(",", ":")))
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _root_hash(entries: dict[str, Any], rels: Iterable[str]) -> str:
    text = "|".join(f"{rel}:{entries[rel].get('sha256', '')}"
                    for rel in sorted(rels))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _entry_is_fresh(old: Any, st: os.stat_result, fingerprint: str) -> bool:
    """True when mtime and size match and the entry is outside the racy window."""
    if not isinstance(old, dict) or old.get("fp") != fingerprint:
        return False
    if old.get("mtime_ns") != st.st_mtime_ns or old.get("size") != st.st_size:
        return False
    try:
        return int(old["checked_ns"]) - int(old["mtime_ns"]) >= RACY_NS
    except (KeyError, TypeError, ValueError):
        return False


def update_tag_cache(root: str | Path = ROOT, *,
                     cache_path: str | Path = DEFAULT_CACHE,
                     files: Iterable[str] | None = None,
                     force: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Content-hash incremental tag cache. Returns (cache, stats).

    The on-disk document holds every entry. A full scan (``files`` is None)
    also prunes entries for files that no longer exist; a subset call never
    removes entries outside its subset. The returned ``cache`` is a view
    restricted to the requested or scanned paths, with its own ``root_hash``.
    """
    root = Path(root).resolve()
    cache_path = Path(cache_path)
    existed = cache_path.exists()
    cache = _load_cache(cache_path)
    entries: dict[str, Any] = cache["files"]
    full_scan = files is None
    if full_scan:
        paths = _source_files(root)
    else:
        paths = list(dict.fromkeys(
            str(f).replace("\\", "/") for f in files))
    stats: dict[str, Any] = {"files": len(paths), "parsed": 0, "reused": 0,
                             "failed": 0, "errors": []}
    dirty = False

    def _fail(rel: str, message: str) -> None:
        nonlocal dirty
        stats["failed"] += 1
        if len(stats["errors"]) < 5:
            stats["errors"].append(f"{rel}: {message}")
        if entries.pop(rel, None) is not None:
            dirty = True

    for rel in paths:
        p = root / rel
        try:
            st = p.stat()
        except OSError:
            _fail(rel, "file not found")
            continue
        fingerprint = extractor_fingerprint(rel)
        old = entries.get(rel)
        if not force and _entry_is_fresh(old, st, fingerprint):
            stats["reused"] += 1
            continue
        try:
            source = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            _fail(rel, f"read failed: {exc}")
            continue
        digest = _sha256(source)
        now = time.time_ns()
        if (not force and isinstance(old, dict)
                and old.get("sha256") == digest
                and old.get("fp") == fingerprint):
            old.update(mtime_ns=st.st_mtime_ns, size=st.st_size,
                       checked_ns=now)
            stats["reused"] += 1
            dirty = True
            continue
        tags, error = extract_tags_status(rel, source)
        if error is not None:
            # Failures are never cached: the next call tries the file again.
            _fail(rel, error)
            continue
        entries[rel] = {
            "sha256": digest,
            "mtime_ns": st.st_mtime_ns,
            "size": st.st_size,
            "checked_ns": now,
            "fp": fingerprint,
            "tags": tags,
        }
        stats["parsed"] += 1
        dirty = True
    if full_scan:
        known = set(paths)
        for rel in list(entries):
            if rel not in known:
                entries.pop(rel, None)
                dirty = True
    view_rels = [rel for rel in dict.fromkeys(paths) if rel in entries]
    view = {rel: entries[rel] for rel in view_rels}
    view_hash = _root_hash(entries, view_rels)
    stored_hash = _root_hash(entries, entries)
    cache["root_hash"] = stored_hash
    cache["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if stats["parsed"] or dirty or force or not existed:
        _save_cache(cache_path, cache)
    stats["root_hash"] = view_hash
    stats["cached_files"] = len(entries)
    result = {"version": CACHE_VERSION, "files": view,
              "root_hash": view_hash}
    return result, stats


def build_reference_graph(cache: dict[str, Any]) -> dict[str, Any]:
    """defines[name] -> files; references[name] -> files; edges referencer->definer.

    Iteration is over sorted names and files, and the returned edges are sorted
    by (src, tgt), so the caps and the output do not depend on set order.
    """
    defines: dict[str, set[str]] = defaultdict(set)
    references: dict[str, set[str]] = defaultdict(set)
    definitions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for rel, entry in (cache.get("files") or {}).items():
        for tag in entry.get("tags") or []:
            name = str(tag.get("name") or "")
            if not name:
                continue
            if tag.get("kind") == "def":
                defines[name].add(rel)
                definitions[(rel, name)].append(tag)
            elif tag.get("kind") == "ref":
                references[name].add(rel)
    edges: dict[tuple[str, str], float] = defaultdict(float)
    MAX_DEFINERS = 12
    MAX_REFERENCERS = 120
    MAX_EDGES = 250_000
    for name in sorted(set(defines) & set(references)):
        if (name in _GENERIC_IDENTS or len(name) < 4
                or len(defines[name]) > MAX_DEFINERS
                or len(references[name]) > MAX_REFERENCERS):
            continue
        for src in sorted(references[name])[:MAX_REFERENCERS]:
            for dst in sorted(defines[name])[:MAX_DEFINERS]:
                if src == dst:
                    continue
                edges[(src, dst)] += 1.0
                if len(edges) >= MAX_EDGES:
                    break
            if len(edges) >= MAX_EDGES:
                break
        if len(edges) >= MAX_EDGES:
            break
    # Self-edge for definitions with no references keeps isolated files alive.
    for name in sorted(defines):
        if name in references:
            continue
        for f in sorted(defines[name]):
            edges[(f, f)] = max(edges.get((f, f), 0.0), 0.1)
    ordered = sorted(edges.items())
    return {"defines": defines, "references": references,
            "definitions": definitions,
            "edges": [{"src": s, "tgt": t, "weight": w}
                      for (s, t), w in ordered]}



def _task_terms(task: str) -> list[str]:
    import re
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", (task or "").lower())
    stop = {"the", "and", "for", "with", "from", "into", "this", "that",
            "add", "fix", "use", "make", "new", "code", "file", "test"}
    return [t for t in raw if t not in stop]


def _file_names(graph: dict[str, Any]) -> tuple[dict[str, set[str]],
                                                dict[str, set[str]]]:
    file_defs: dict[str, set[str]] = defaultdict(set)
    file_refs: dict[str, set[str]] = defaultdict(set)
    for name, files in (graph.get("defines") or {}).items():
        low = str(name).lower()
        for f in files:
            file_defs[f].add(low)
    for name, files in (graph.get("references") or {}).items():
        low = str(name).lower()
        for f in files:
            file_refs[f].add(low)
    return file_defs, file_refs


def _task_relevance(graph: dict[str, Any], task: str,
                    focus_files: Iterable[str]) -> tuple[dict[str, float],
                                                          set[str]]:
    """Term-weighted relevance + a candidate subgraph.

    The candidate restriction is what stops a globally central file (e.g. a
    py.rs with hundreds of references) from dominating every task. Terms are
    weighted by inverse file frequency; the candidates are the top matching
    files plus their one-hop reference neighbours.
    """
    terms = _task_terms(task)
    file_defs, file_refs = _file_names(graph)
    nodes = set(file_defs) | set(file_refs)
    for e in graph.get("edges") or []:
        nodes.add(str(e["src"]))
        nodes.add(str(e["tgt"]))
    if not nodes:
        return {}, set()
    scores: dict[str, float] = {}
    if terms:
        n = max(1, len(nodes))
        df = {t: 0 for t in terms}
        for f in nodes:
            names = file_defs.get(f, set()) | file_refs.get(f, set())
            lowpath = f.lower()
            for t in terms:
                if t in lowpath or any(t in name for name in names):
                    df[t] += 1
        weight = {t: math.log((n + 1) / (df[t] + 1)) + 1.0 for t in terms}
        for f in nodes:
            lowpath = f.lower()
            names = file_defs.get(f, set()) | file_refs.get(f, set())
            score = 0.0
            for t in terms:
                if t in lowpath:
                    score += 3.0 * weight[t]
                if any(t in name for name in file_defs.get(f, ())):
                    score += 4.0 * weight[t]
                if any(t in name for name in file_refs.get(f, ())):
                    score += 1.5 * weight[t]
            if score > 0:
                if f.startswith("tests/"):
                    score *= 0.35
                scores[f] = score
    for f in focus_files:
        scores[str(f)] = scores.get(str(f), 0.0) + 100.0
    if not scores:
        return {f: 1.0 for f in nodes}, nodes
    top = sorted(scores, key=lambda f: (-scores[f], f))[:30]
    top_set = set(top)
    candidates = set(top)
    for e in sorted(graph.get("edges") or [],
                    key=lambda e: (str(e["src"]), str(e["tgt"]))):
        src, tgt = str(e["src"]), str(e["tgt"])
        if src not in top_set:
            continue
        candidates.add(src)
        candidates.add(tgt)
        if len(candidates) >= 300:
            break
    return scores, candidates


PPR_TOLERANCE = 1e-10
PPR_MAX_ITERATIONS = 100


def personalized_pagerank(graph: dict[str, Any], *,
                          task: str = "",
                          focus_files: Iterable[str] = (),
                          damping: float | None = None,
                          iterations: int = PPR_MAX_ITERATIONS) -> dict[str, float]:
    """Personalized PageRank over the candidate subgraph.

    Mass at dangling nodes (no out-weight inside the subgraph) is handed back
    through the personalization vector, so the ranks sum to 1. Iteration stops
    when the L1 change drops below PPR_TOLERANCE or after `iterations` rounds.
    """
    relevance, candidates = _task_relevance(graph, task, focus_files)
    nodes = sorted(candidates)
    if not nodes:
        return {}
    edges = sorted(
        (e for e in (graph.get("edges") or [])
         if str(e["src"]) in candidates and str(e["tgt"]) in candidates),
        key=lambda e: (str(e["src"]), str(e["tgt"])))
    d = 0.30 if task.strip() else 0.85
    if damping is not None:
        d = float(damping)
    terms = _task_terms(task)
    personal: dict[str, float] = {}
    for n in nodes:
        w = 1.0 + 20.0 * relevance.get(n, 0.0)
        for t in terms:
            if t in n.lower():
                w += 2.0
        if n.startswith("tests/") and task.strip():
            w *= 0.5
        personal[n] = w
    total = sum(personal[n] for n in nodes) or 1.0
    teleport = {n: personal[n] / total for n in nodes}
    rank = dict(teleport)
    out_weight: dict[str, float] = defaultdict(float)
    for e in edges:
        out_weight[str(e["src"])] += float(e.get("weight", 1.0))
    dangling = [n for n in nodes if out_weight.get(n, 0.0) <= 0.0]
    for _ in range(max(1, int(iterations))):
        dangling_mass = sum(rank[n] for n in dangling)
        new = {n: (1.0 - d) * teleport[n] + d * dangling_mass * teleport[n]
               for n in nodes}
        for e in edges:
            src, tgt = str(e["src"]), str(e["tgt"])
            w = float(e.get("weight", 1.0))
            if out_weight.get(src, 0.0) > 0:
                new[tgt] += d * rank[src] * w / out_weight[src]
        delta = sum(abs(new[n] - rank[n]) for n in nodes)
        rank = new
        if delta < PPR_TOLERANCE:
            break
    return dict(sorted(rank.items(), key=lambda kv: (-kv[1], kv[0])))



def _line_text(root: Path, rel: str, line: int) -> str:
    return _line_text_cached(root, rel, line, {})


def _line_text_cached(root: Path, rel: str, line: int,
                      cache: dict[str, list[str]]) -> str:
    if rel not in cache:
        try:
            cache[rel] = (root / rel).read_text(
                encoding="utf-8", errors="replace").splitlines()
        except OSError:
            cache[rel] = []
    lines = cache[rel]
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""


def _symbols_for(graph: dict[str, Any], rel: str) -> list[dict[str, Any]]:
    out = []
    for (f, name), tags in (graph.get("definitions") or {}).items():
        if f != rel:
            continue
        for tag in tags:
            out.append({"name": name, "line": tag.get("line", 0),
                        "detail": tag.get("detail", "")})
    out.sort(key=lambda x: (x["line"], x["name"]))
    return out


def _scip_edges(root: Path, scip_path: str | Path | None) -> list[dict[str, Any]]:
    if not scip_path:
        return []
    try:
        from scripts.ocelot_scip_import import scip_import
        payload = scip_import(scip_path, root=root)
        return list(payload.get("edges") or [])
    except Exception:
        return []


def repo_map(root: str | Path = ROOT, *, task: str = "",
             budget_tokens: int = 1500,
             cache_path: str | Path = DEFAULT_CACHE,
             focus_files: Iterable[str] = (),
             full_tier: int = 3, outline_tier: int = 12,
             force_refresh: bool = False,
             files: Iterable[str] | None = None,
             scip_path: str | Path | None = None) -> dict[str, Any]:
    """Ranked, token-budgeted repo map (Aider-style, graph-native)."""
    root = Path(root).resolve()
    cache, stats = update_tag_cache(root, cache_path=cache_path,
                                    files=files,
                                    force=force_refresh)
    known_files = set((cache.get("files") or {}))
    focus_files = [str(f) for f in focus_files if str(f) in known_files]
    graph = build_reference_graph(cache)
    scip_edges = _scip_edges(root, scip_path)
    if scip_edges:
        graph["edges"] = list(graph.get("edges") or []) + scip_edges
    ranked = personalized_pagerank(graph, task=task,
                                   focus_files=focus_files)
    if task.strip() and ranked:
        # PageRank supplies centrality; the term-weighted relevance supplies
        # task fit. The map is for a task, so relevance leads (0.7/0.3).
        relevance, _candidates = _task_relevance(graph, task, focus_files)
        max_rel = max(relevance.values()) or 1.0
        max_rank = max(ranked.values()) or 1.0
        ranked = dict(sorted(
            ranked.items(),
            key=lambda kv: (-(0.7 * relevance.get(kv[0], 0.0) / max_rel
                              + 0.3 * kv[1] / max_rank),
                            kv[0])))
    budget = max(200, int(budget_tokens))
    full_tier = max(1, min(int(full_tier), max(1, budget // 300)))
    outline_tier = max(full_tier, min(int(outline_tier),
                                      max(2, budget // 80)))
    symbols_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (f, name), tags in (graph.get("definitions") or {}).items():
        for tag in tags:
            symbols_by_file[f].append({"name": name,
                                        "line": tag.get("line", 0),
                                        "detail": tag.get("detail", "")})
    for f in symbols_by_file:
        seen = set()
        unique = []
        for sym in symbols_by_file[f]:
            key = (sym["name"], sym["line"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(sym)
        symbols_by_file[f] = sorted(unique, key=lambda x: (x["line"], x["name"]))
    line_cache: dict[str, list[str]] = {}
    lines: list[str] = []
    used_files: list[dict[str, Any]] = []
    if task:
        lines.append(f"# Repo map: {task}")
    else:
        lines.append("# Repo map")
    lines.append(f"# files: {len(ranked)}  cache: {stats['cached_files']} "
                 f"(parsed {stats['parsed']}, reused {stats['reused']})")
    lines.append("")
    for i, (rel, score) in enumerate(ranked.items()):
        syms = symbols_by_file.get(rel, [])
        if i < full_tier:
            tier = "full"
            body = [f"{rel}  score={score:.4f}"]
            shown = 0
            for s in syms:
                if shown >= 16:
                    break
                if (s["name"].lower() in _GENERIC_SYMBOLS
                        and len(syms) > 8):
                    continue
                line = f"  L{s['line']} {s['name']}"
                src = _line_text_cached(root, rel, int(s["line"]), line_cache)
                if src:
                    line += f"  | {src[:120]}"
                body.append(line)
                shown += 1
        elif i < outline_tier:
            tier = "outline"
            public = [s for s in syms
                      if not s["name"].startswith("_")
                      and s["name"].lower() not in _GENERIC_SYMBOLS]
            if not public:
                public = syms
            names = ", ".join(f"{s['name']}@L{s['line']}"
                              for s in public[:12])
            body = [f"{rel}  score={score:.4f}  {names}"]
        else:
            tier = "listing"
            body = [f"{rel}  ({len(syms)} symbols)"]
        if not used_files:
            # Always return at least one file: trim a too-large first body
            # rather than returning an empty map.
            while body and len("\n".join(lines + body + [""])) // 4 > budget:
                body = body[:-1] or [body[0]]
                if len(body) == 1:
                    break
            lines.extend(body)
            lines.append("")
            used_files.append({"path": rel, "score": round(score, 6),
                               "tier": tier, "symbols": len(syms)})
            continue
        candidate = "\n".join(lines + body + [""])
        if len(candidate) // 4 > budget:
            break
        lines.extend(body)
        lines.append("")
        used_files.append({"path": rel, "score": round(score, 6),
                           "tier": tier, "symbols": len(syms)})
    markdown = "\n".join(lines).strip() + "\n"
    return {
        "ok": True,
        "task": task,
        "budget_tokens": budget,
        "estimated_tokens": max(1, len(markdown) // 4),
        "markdown": markdown,
        "files": used_files,
        "cache": stats,
        "graph": {"files": len(ranked),
                  "edges": len(graph["edges"]),
                  "scip_edges": len(scip_edges),
                  "definitions": sum(len(v) for v in graph["defines"].values())},
    }


def impact(root: str | Path = ROOT, *, file: str, depth: int = 2,
           cache_path: str | Path = DEFAULT_CACHE,
           files: Iterable[str] | None = None,
           scip_path: str | Path | None = None) -> dict[str, Any]:
    """Transitive dependents of a file over the reference graph."""
    root = Path(root).resolve()
    cache, stats = update_tag_cache(root, cache_path=cache_path, files=files)
    graph = build_reference_graph(cache)
    scip_edges = _scip_edges(root, scip_path)
    if scip_edges:
        graph["edges"] = list(graph.get("edges") or []) + scip_edges
    reverse: dict[str, set[str]] = defaultdict(set)
    forward: dict[str, set[str]] = defaultdict(set)
    for e in graph["edges"]:
        src, tgt = str(e["src"]), str(e["tgt"])
        if src != tgt:
            reverse[tgt].add(src)
            forward[src].add(tgt)
    target = str(file).replace("\\", "/")
    if target not in (cache.get("files") or {}):
        return {"ok": False, "error": f"no indexed file {file!r}"}
    seen = {target}
    frontier = [(target, 0)]
    impacted = []
    while frontier:
        cur, d = frontier.pop(0)
        if d >= max(1, int(depth)):
            continue
        for nxt in sorted(reverse.get(cur, ())):
            if nxt in seen:
                continue
            seen.add(nxt)
            impacted.append({"path": nxt, "depth": d + 1})
            frontier.append((nxt, d + 1))
    return {"ok": True, "file": target, "depth": int(depth),
            "impacted": impacted, "n": len(impacted),
            "direct_dependencies": sorted(forward.get(target, ())),
            "scip_edges": len(scip_edges), "cache": stats}
