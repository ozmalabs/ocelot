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
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
CACHE_VERSION = 2
DEFAULT_CACHE = ROOT / "var" / "ocelot_dev_tags.json"
try:
    from scripts.ocelot_tag_languages import LANGUAGES as _TAG_LANGUAGES
    LANGUAGES = {suffix: entry["module"]
                 for suffix, entry in _TAG_LANGUAGES.items()
                 if entry.get("module")}
except Exception:  # pragma: no cover - registry is part of the tree
    LANGUAGES = {
        ".py": "tree_sitter_python",
        ".rs": "tree_sitter_rust",
        ".lua": "tree_sitter_lua",
    }
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


def _python_tags(source: str) -> list[dict[str, Any]]:
    """Python tags via the stdlib AST: much faster than a tree-sitter query
    across thousands of files, and precise enough for a definition/reference
    graph."""
    import ast
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    out: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            out.append({"name": node.name, "kind": "def",
                        "detail": ("definition.class"
                                   if isinstance(node, ast.ClassDef)
                                   else "definition.function"),
                        "line": int(getattr(node, "lineno", 1))})
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            out.append({"name": node.id, "kind": "ref",
                        "detail": "reference.name",
                        "line": int(getattr(node, "lineno", 1))})
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            out.append({"name": node.attr, "kind": "ref",
                        "detail": "reference.attribute",
                        "line": int(getattr(node, "lineno", 1))})
    return out


def extract_tags(path: str | Path, source: str) -> list[dict[str, Any]]:
    """Definition/reference tags via the shared multi-language registry.

    The registry keeps Python on the stdlib-AST fast path and uses each
    grammar's own `queries/tags.scm` for Rust/Lua/TypeScript/Go/Java/C/C++.
    A missing grammar yields an empty list for that file, never an exception.
    """
    try:
        from scripts.ocelot_tag_languages import extract_tags as _extract
        return _extract(path, source)
    except Exception:
        # The registry is the supported path; this fallback keeps a damaged
        # optional dependency from killing the whole map.
        if Path(path).suffix.lower() == ".py":
            return _python_tags(source)
        return []


def _load_cache(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("version") == CACHE_VERSION:
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"version": CACHE_VERSION, "files": {}}


def _save_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def update_tag_cache(root: str | Path = ROOT, *,
                     cache_path: str | Path = DEFAULT_CACHE,
                     files: Iterable[str] | None = None,
                     force: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Content-hash incremental tag cache. Returns (cache, stats)."""
    root = Path(root).resolve()
    cache_path = Path(cache_path)
    cache = _load_cache(cache_path)
    entries: dict[str, Any] = cache.setdefault("files", {})
    paths = list(files) if files is not None else _source_files(root)
    stats = {"files": len(paths), "parsed": 0, "reused": 0, "failed": 0}
    for rel in paths:
        p = root / rel
        try:
            st = p.stat()
        except OSError:
            stats["failed"] += 1
            continue
        old = entries.get(rel)
        # Cursor-style fast path: mtime+size match means reuse without reading
        # or hashing. On a real edit, read + hash and reuse the tags if the
        # content hash is unchanged (mtime-only touches stay cheap).
        if (not force and isinstance(old, dict)
                and old.get("mtime") == int(st.st_mtime)
                and old.get("size") == st.st_size):
            stats["reused"] += 1
            continue
        try:
            source = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            stats["failed"] += 1
            continue
        digest = _sha256(source)
        if (not force and isinstance(old, dict)
                and old.get("sha256") == digest):
            old["mtime"] = int(st.st_mtime)
            old["size"] = st.st_size
            stats["reused"] += 1
            continue
        tags = extract_tags(rel, source)
        entries[rel] = {
            "sha256": digest,
            "mtime": int(st.st_mtime),
            "size": st.st_size,
            "tags": tags,
        }
        stats["parsed"] += 1
    # Drop entries for files that no longer exist in the scanned set.
    known = set(paths)
    for rel in list(entries):
        if rel not in known:
            entries.pop(rel, None)
    cache["root_hash"] = _sha256("|".join(
        f"{rel}:{entries[rel].get('sha256', '')}" for rel in sorted(entries)))
    cache["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if stats["parsed"] or force or not cache_path.exists():
        _save_cache(cache_path, cache)
    stats["root_hash"] = cache["root_hash"]
    stats["cached_files"] = len(entries)
    return cache, stats


def build_reference_graph(cache: dict[str, Any]) -> dict[str, Any]:
    """defines[name] -> files; references[name] -> files; edges referencer->definer."""
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
    for name in set(defines) & set(references):
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
    for name, files in defines.items():
        if name in references:
            continue
        for f in files:
            edges[(f, f)] = max(edges.get((f, f), 0.0), 0.1)
    return {"defines": defines, "references": references,
            "definitions": definitions,
            "edges": [{"src": s, "tgt": t, "weight": w}
                      for (s, t), w in edges.items()]}


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
    candidates = set(top)
    for e in graph.get("edges") or []:
        src, tgt = str(e["src"]), str(e["tgt"])
        if src not in top:
            continue
        candidates.add(src)
        candidates.add(tgt)
        if len(candidates) >= 300:
            break
    return scores, candidates


def personalized_pagerank(graph: dict[str, Any], *,
                          task: str = "",
                          focus_files: Iterable[str] = (),
                          damping: float | None = None,
                          iterations: int = 30) -> dict[str, float]:
    relevance, candidates = _task_relevance(graph, task, focus_files)
    edges = [e for e in (graph.get("edges") or [])
             if str(e["src"]) in candidates and str(e["tgt"]) in candidates]
    nodes = set(candidates)
    if not nodes:
        return {}
    d = 0.30 if task.strip() else 0.85
    if damping is not None:
        d = float(damping)
    terms = _task_terms(task)
    file_defs, _file_refs = _file_names(graph)
    personal: dict[str, float] = {}
    for n in nodes:
        w = 1.0 + 20.0 * relevance.get(n, 0.0)
        for t in terms:
            if t in n.lower():
                w += 2.0
        if n.startswith("tests/") and task.strip():
            w *= 0.5
        personal[n] = w
    total = sum(personal.values()) or 1.0
    rank = {n: personal[n] / total for n in nodes}
    out_weight: dict[str, float] = defaultdict(float)
    for e in edges:
        out_weight[str(e["src"])] += float(e.get("weight", 1.0))
    for _ in range(iterations):
        new = {n: (1.0 - d) * personal[n] / total for n in nodes}
        for e in edges:
            src, tgt = str(e["src"]), str(e["tgt"])
            w = float(e.get("weight", 1.0))
            if out_weight.get(src, 0.0) > 0:
                new[tgt] += d * rank.get(src, 0.0) * w / out_weight[src]
        rank = new
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
