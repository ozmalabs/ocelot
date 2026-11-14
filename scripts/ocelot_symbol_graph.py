"""ocelot_symbol_graph — symbol-level callers, callees and impact.

Builds a graph of symbols (definitions) and the references between them from
the tag cache that ``ocelot_repo_map`` maintains. Each node is one definition,
id ``"<rel path>::<qualname>"``. Each edge is "caller symbol references callee
symbol", where the caller is the innermost enclosing definition of the
reference (``"<rel path>::<module>"`` for module-level code).

Resolution is syntactic, in three levels with descending confidence:

* ``local``: a reference names a definition in the same file. A call on
  ``self``/``cls`` inside class ``A`` prefers ``A.<name>``.
* ``import``: the file binds the name with ``from X import name``, where ``X``
  resolves to an indexed Python file. The edge goes to that file's definition.
* ``name``: a global definition with that name exists, there are at most
  ``MAX_NAME_CANDIDATES`` of them, and the name is not a generic identifier.

There is no type inference. ``obj.method()`` resolves by name, and dynamic
dispatch, ``getattr`` and star re-exports are not followed. The precise layer is
LSP (``ocelot_lsp``); see ``docs/features/SYMBOL_GRAPH.md``.

DEV TOOLING, NOT AGENT RUNTIME. Read-only: nothing here edits code.

CLI::

    python -m scripts.ocelot_symbol_graph {callers,callees,impact,resolve} SYMBOL
        [--depth N] [--root R] [--cache C] [--min-confidence X]
"""
from __future__ import annotations

import argparse
import json
import posixpath
import time
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any

from scripts.ocelot_repo_map import _GENERIC_IDENTS, ROOT, update_tag_cache

# A name with more global definitions than this is too ambiguous to link.
MAX_NAME_CANDIDATES = 5
MIN_NAME_LENGTH = 3
# In-process memo of built graphs, keyed by the tag view's root_hash.
MEMO_SIZE = 4
DEFAULT_DEPTH = {"callers": 1, "callees": 1, "impact": 3}
OPS = ("callers", "callees", "impact", "resolve")
_RESOLUTION_RANK = {"local": 3, "import": 2, "name": 1}
_PY_ROOTS = ("", "runners/dsl/python")

_GRAPH_MEMO: OrderedDict[str, dict[str, Any]] = OrderedDict()
_ADJ_MEMO: OrderedDict[int, tuple[dict[str, Any], dict, dict]] = OrderedDict()


def _module_path_candidates(module: str, level: int, rel: str,
                            roots: tuple[str, ...]) -> list[str]:
    """Candidate file paths for a dotted module, relative to each root.

    Relative imports (``level`` > 0) resolve from the importing file's package
    directory: level 1 is that directory, each extra level goes one up.
    """
    parts = [part for part in module.split(".") if part] if module else []
    if level:
        base = posixpath.dirname(rel)
        for _ in range(level - 1):
            base = posixpath.dirname(base)
        stems = ["/".join([p for p in (base, *parts) if p])]
    else:
        tail = "/".join(parts)
        stems = [("/".join([p for p in (root, tail) if p])) for root in roots]
    out: list[str] = []
    for stem in stems:
        if not stem:
            continue
        out.append(f"{stem}.py")
        out.append(f"{stem}/__init__.py")
    return out


def _resolve_module(module: str, level: int, rel: str,
                    py_files: set[str]) -> str | None:
    """Indexed file for an import, or None if it is outside the index."""
    for candidate in _module_path_candidates(module, level, rel, _PY_ROOTS):
        if candidate in py_files:
            return candidate
    return None


def _resolve_ref(rel: str, name: str, scope: str,
                 file_defs: dict[str, dict[str, list[str]]],
                 imports: dict[str, list[dict[str, Any]]],
                 py_files: set[str],
                 defs_by_name: dict[str, list[str]],
                 nodes: dict[str, dict[str, Any]],
                 ) -> tuple[str | None, list[str], float]:
    """(resolution, target ids, per-target confidence) for one reference.

    ``resolution`` is None when the reference is unresolved. Targets are
    sorted ids. Confidence is ``1 / len(targets)``, so a unique target gets 1.0.
    """
    local = file_defs.get(rel, {}).get(name, [])
    if local:
        prefix = scope.rsplit(".", 1)[0] if "." in scope else ""
        if prefix:
            owner = nodes.get(f"{rel}::{prefix}")
            if owner is not None and owner["kind_detail"] == "definition.class":
                own = [sid for sid in local
                       if nodes[sid]["qualname"] == f"{prefix}.{name}"]
                if own:
                    return "local", own, 1.0 / len(own)
        return "local", list(local), 1.0 / len(local)

    bindings = [tag for tag in imports.get(rel, [])
                if tag.get("name") == name
                and tag.get("detail") == "import.from"]
    if bindings:
        targets: set[str] = set()
        for tag in bindings:
            target_file = _resolve_module(str(tag.get("module") or ""),
                                          int(tag.get("level") or 0), rel,
                                          py_files)
            if target_file is None:
                continue
            targets.update(file_defs.get(target_file, {}).get(
                str(tag.get("imported") or ""), []))
        if targets:
            ordered = sorted(targets)
            return "import", ordered, 1.0 / len(ordered)
        # The name is bound by an import, but the module or definition is not
        # in the index (for example a third-party package). Do not guess a
        # repo-wide name match for it.
        return None, [], 0.0

    if name in _GENERIC_IDENTS or len(name) < MIN_NAME_LENGTH:
        return None, [], 0.0
    candidates = defs_by_name.get(name, [])
    if 1 <= len(candidates) <= MAX_NAME_CANDIDATES:
        return "name", list(candidates), 1.0 / len(candidates)
    return None, [], 0.0


def _build(cache: dict[str, Any]) -> dict[str, Any]:
    files = cache.get("files") or {}
    py_files = {rel for rel in files if rel.endswith(".py")}
    nodes: dict[str, dict[str, Any]] = {}
    defs_by_name: dict[str, list[str]] = defaultdict(list)
    file_defs: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list))
    imports: dict[str, list[dict[str, Any]]] = defaultdict(list)
    refs: list[tuple[str, dict[str, Any]]] = []
    duplicate_defs = 0
    for rel in sorted(files):
        for tag in (files[rel] or {}).get("tags") or []:
            name = str(tag.get("name") or "")
            if not name:
                continue
            kind = tag.get("kind")
            if kind == "def":
                qualname = str(tag.get("qualname") or name)
                sid = f"{rel}::{qualname}"
                if sid in nodes:
                    duplicate_defs += 1
                    continue
                line = int(tag.get("line") or 1)
                nodes[sid] = {
                    "file": rel,
                    "qualname": qualname,
                    "name": name,
                    "line": line,
                    "end_line": int(tag.get("end_line") or line),
                    "kind_detail": str(tag.get("detail") or ""),
                }
                defs_by_name[name].append(sid)
                file_defs[rel][name].append(sid)
            elif kind == "ref":
                refs.append((rel, tag))
            elif kind == "import":
                imports[rel].append(tag)
    for name in defs_by_name:
        defs_by_name[name].sort()

    stats: dict[str, Any] = {
        "files": len(files),
        "defs": len(nodes),
        "refs": len(refs),
        "resolved_local": 0,
        "resolved_import": 0,
        "resolved_name": 0,
        "unresolved": 0,
        "duplicate_defs": duplicate_defs,
    }
    edges: dict[tuple[str, str], dict[str, Any]] = {}
    for rel, tag in refs:
        name = str(tag["name"])
        scope = str(tag.get("scope") or "")
        caller = f"{rel}::{scope or '<module>'}"
        if not scope and caller not in nodes:
            nodes[caller] = {"file": rel, "qualname": "<module>",
                             "name": "<module>", "line": 1, "end_line": 1,
                             "kind_detail": "module"}
        resolution, targets, confidence = _resolve_ref(
            rel, name, scope, file_defs, imports, py_files, defs_by_name,
            nodes)
        if resolution is None:
            stats["unresolved"] += 1
            continue
        stats[f"resolved_{resolution}"] += 1
        for target in targets:
            if target == caller:
                continue
            key = (caller, target)
            current = edges.get(key)
            if current is None:
                edges[key] = {"src": caller, "tgt": target,
                              "resolution": resolution,
                              "confidence": confidence, "count": 1}
                continue
            current["count"] += 1
            if ((confidence, _RESOLUTION_RANK[resolution])
                    > (current["confidence"],
                       _RESOLUTION_RANK[current["resolution"]])):
                current["resolution"] = resolution
                current["confidence"] = confidence
    edge_list = [edges[key] for key in sorted(edges)]
    stats["edges"] = len(edge_list)
    return {"root_hash": cache.get("root_hash"), "nodes": nodes,
            "edges": edge_list, "stats": stats}


def build_symbol_graph(cache: dict[str, Any]) -> dict[str, Any]:
    """Symbol graph for a tag-cache view (``update_tag_cache`` output).

    Returns ``{root_hash, nodes, edges, stats}``. Results are memoised in
    process by the view's ``root_hash`` (the last ``MEMO_SIZE`` graphs). A view
    without a root_hash is built every time.
    """
    root_hash = cache.get("root_hash")
    if root_hash is not None and root_hash in _GRAPH_MEMO:
        _GRAPH_MEMO.move_to_end(root_hash)
        return _GRAPH_MEMO[root_hash]
    graph = _build(cache)
    if root_hash is not None:
        _GRAPH_MEMO[root_hash] = graph
        while len(_GRAPH_MEMO) > MEMO_SIZE:
            _GRAPH_MEMO.popitem(last=False)
    return graph


def _adjacency(graph: dict[str, Any]) -> tuple[dict, dict]:
    """(forward, reverse) adjacency: id -> [(other id, resolution, confidence)]."""
    key = id(graph)
    hit = _ADJ_MEMO.get(key)
    if hit is not None and hit[0] is graph:
        _ADJ_MEMO.move_to_end(key)
        return hit[1], hit[2]
    forward: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    reverse: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for edge in graph["edges"]:
        forward[edge["src"]].append(
            (edge["tgt"], edge["resolution"], edge["confidence"]))
        reverse[edge["tgt"]].append(
            (edge["src"], edge["resolution"], edge["confidence"]))
    _ADJ_MEMO[key] = (graph, forward, reverse)
    while len(_ADJ_MEMO) > MEMO_SIZE:
        _ADJ_MEMO.popitem(last=False)
    return forward, reverse


def resolve_symbol(graph: dict[str, Any], query: str) -> list[str]:
    """Sorted symbol ids matching a query.

    ``"path::qualname"`` must name an exact id. A dotted query matches qualnames
    exactly (``"A.run"``). A bare name matches every definition with that name,
    so ``"run"`` can return several methods.
    """
    text = str(query).strip()
    nodes = graph["nodes"]
    if "::" in text:
        return [text] if text in nodes else []
    if "." in text:
        return sorted(sid for sid, node in nodes.items()
                      if node["qualname"] == text)
    return sorted(sid for sid, node in nodes.items() if node["name"] == text)


def _lookup(graph: dict[str, Any], symbol: str) -> tuple[str | None, dict[str, Any] | None]:
    ids = resolve_symbol(graph, symbol)
    if not ids:
        return None, {"ok": False, "error": f"unknown symbol: {symbol}"}
    if len(ids) > 1:
        return None, {"ok": False, "ambiguous": ids}
    return ids[0], None


def _walk(graph: dict[str, Any], start: str, depth: int, direction: str,
          min_confidence: float) -> list[dict[str, Any]]:
    """Reachable symbols within ``depth`` hops, one best path per symbol.

    The path confidence is the product of edge confidences. Per symbol, the
    path with the highest confidence wins, and ``depth`` is that path's hop
    count. Paths whose product drops below ``min_confidence`` are pruned.
    """
    forward, reverse = _adjacency(graph)
    adjacency = reverse if direction == "callers" else forward
    best: dict[str, tuple[float, int, str]] = {}
    frontier: dict[str, float] = {start: 1.0}
    for hop in range(1, depth + 1):
        nxt: dict[str, tuple[float, str]] = {}
        for node_id in sorted(frontier):
            base = frontier[node_id]
            for other, resolution, confidence in adjacency.get(node_id, ()):
                if other == start:
                    continue
                value = base * confidence
                if value < min_confidence:
                    continue
                current = nxt.get(other)
                if current is None or ((value, _RESOLUTION_RANK[resolution])
                                       > (current[0],
                                          _RESOLUTION_RANK[current[1]])):
                    nxt[other] = (value, resolution)
        if not nxt:
            break
        for other, (value, resolution) in nxt.items():
            prior = best.get(other)
            if prior is None or value > prior[0]:
                best[other] = (value, hop, resolution)
        frontier = {other: value for other, (value, _res) in nxt.items()}
    out = []
    for node_id, (value, hop, resolution) in best.items():
        node = graph["nodes"][node_id]
        out.append({"id": node_id, "file": node["file"],
                    "qualname": node["qualname"], "depth": hop,
                    "resolution": resolution, "confidence": value})
    out.sort(key=lambda row: (row["depth"], -row["confidence"], row["id"]))
    return out


def _check_depth(depth: int) -> dict[str, Any] | None:
    if depth < 1:
        return {"ok": False, "error": f"depth must be >= 1, got {depth}"}
    return None


def callers(graph: dict[str, Any], symbol: str, depth: int = 1,
            min_confidence: float = 0.0) -> dict[str, Any]:
    """Symbols that reference ``symbol``, transitively up to ``depth`` hops."""
    bad = _check_depth(depth)
    if bad:
        return bad
    sid, error = _lookup(graph, symbol)
    if error:
        return error
    return {"ok": True, "op": "callers", "symbol": sid, "depth": depth,
            "results": _walk(graph, sid, depth, "callers", min_confidence)}


def callees(graph: dict[str, Any], symbol: str, depth: int = 1,
            min_confidence: float = 0.0) -> dict[str, Any]:
    """Symbols that ``symbol`` references, transitively up to ``depth`` hops."""
    bad = _check_depth(depth)
    if bad:
        return bad
    sid, error = _lookup(graph, symbol)
    if error:
        return error
    return {"ok": True, "op": "callees", "symbol": sid, "depth": depth,
            "results": _walk(graph, sid, depth, "callees", min_confidence)}


def symbol_impact(graph: dict[str, Any], symbol: str, depth: int = 3,
                  min_confidence: float = 0.0) -> dict[str, Any]:
    """Transitive callers, plus a per-file summary of the minimum depth."""
    bad = _check_depth(depth)
    if bad:
        return bad
    sid, error = _lookup(graph, symbol)
    if error:
        return error
    results = _walk(graph, sid, depth, "callers", min_confidence)
    by_file: dict[str, dict[str, Any]] = {}
    for row in results:
        entry = by_file.setdefault(row["file"], {"file": row["file"],
                                                 "min_depth": row["depth"],
                                                 "symbols": 0})
        entry["min_depth"] = min(entry["min_depth"], row["depth"])
        entry["symbols"] += 1
    return {"ok": True, "op": "impact", "symbol": sid, "depth": depth,
            "min_confidence": min_confidence, "results": results,
            "files": [by_file[f] for f in sorted(by_file)]}


def _run_op(graph: dict[str, Any], op: str, symbol: str, depth: int | None,
            min_confidence: float) -> dict[str, Any]:
    if op == "resolve":
        matches = resolve_symbol(graph, symbol)
        if not matches:
            return {"ok": False, "error": f"unknown symbol: {symbol}"}
        return {"ok": True, "op": "resolve", "symbol": symbol,
                "matches": matches}
    if op not in DEFAULT_DEPTH:
        return {"ok": False, "error": f"unknown op: {op}"}
    hops = DEFAULT_DEPTH[op] if depth is None else depth
    if op == "callers":
        return callers(graph, symbol, hops, min_confidence)
    if op == "callees":
        return callees(graph, symbol, hops, min_confidence)
    return symbol_impact(graph, symbol, hops, min_confidence)


def symbol_query(root: str | Path = ROOT, op: str = "callers", symbol: str = "", *,
                 depth: int | None = None, cache_path: str | Path | None = None,
                 min_confidence: float = 0.0) -> dict[str, Any]:
    """Refresh the tag cache for ``root``, build (or reuse) the graph, run ``op``.

    ``op`` is one of ``callers``, ``callees``, ``impact`` or ``resolve``. The
    default cache is ``<root>/var/ocelot_dev_tags.json``. Returns a JSON-safe
    dict with ``ok``, the op result, graph ``stats`` and ``timings`` in seconds.
    """
    if op not in OPS:
        return {"ok": False, "error": f"unknown op: {op}"}
    root = Path(root).resolve()
    cache_file = (Path(cache_path) if cache_path is not None
                  else root / "var" / "ocelot_dev_tags.json")
    t0 = time.perf_counter()
    cache, tag_stats = update_tag_cache(root, cache_path=cache_file)
    t1 = time.perf_counter()
    graph = build_symbol_graph(cache)
    t2 = time.perf_counter()
    result = _run_op(graph, op, symbol, depth, min_confidence)
    t3 = time.perf_counter()
    result.update({
        "root": str(root),
        "cache": str(cache_file),
        "stats": graph["stats"],
        "tag_cache": {key: tag_stats[key] for key in
                      ("files", "parsed", "reused", "failed", "errors",
                       "cached_files")},
        "timings": {"update_seconds": round(t1 - t0, 4),
                    "build_seconds": round(t2 - t1, 4),
                    "query_seconds": round(t3 - t2, 4)},
    })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.ocelot_symbol_graph",
        description="Symbol-level callers, callees, impact and resolve.")
    parser.add_argument("op", choices=OPS)
    parser.add_argument("symbol", help='"path::qualname", a qualname, or a name')
    parser.add_argument("--depth", type=int, default=None,
                        help="hops (callers/callees 1, impact 3 by default)")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--cache", default=None,
                        help="tag cache path (default <root>/var/ocelot_dev_tags.json)")
    parser.add_argument("--min-confidence", type=float, default=0.0)
    args = parser.parse_args(argv)
    result = symbol_query(args.root, args.op, args.symbol, depth=args.depth,
                          cache_path=args.cache,
                          min_confidence=args.min_confidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
