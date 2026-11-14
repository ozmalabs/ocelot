"""ocelot_architecture — deterministic architecture summaries of a checkout.

This module turns the existing repo-map reference graph into a compact,
repeatable architecture report:

  * **hubs** — files ranked by weighted PageRank, with in/out degree;
  * **cycles** — strongly connected components of size > 1 (Tarjan), i.e.
    groups of files that reference each other;
  * **coupling** — per-file in/out degree, plus the most coupled files;
  * **modules** — top-level directory file counts and cross-module edges;
  * **dead-code candidates** — files with no inbound *external* reference,
    excluding tests, dev scripts and conventional entrypoints. This is a
    heuristic, not proof that code is unused;
  * **test-to-source ratio** — indexed test files vs non-test source files.

The analysis is deliberately file-level and syntactic. It reuses
:func:`ocelot_repo_map.update_tag_cache` (content-hash incremental tags) and
:func:`ocelot_repo_map.build_reference_graph` (referencer -> definer edges),
then normalizes the graph before measuring it.

Determinism contract: every list is sorted, every mapping is serialized with
sorted keys, no timestamp/absolute path is included, and all floating point
values are rounded before they enter the report. Calling
``architecture_report(root)`` twice on unchanged files yields byte-identical
``markdown`` and ``json`` strings.

DEV TOOLING, NOT AGENT RUNTIME. The report is read-only; it never edits.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from scripts.ocelot_repo_map import build_reference_graph, update_tag_cache

DEFAULT_TOP = 15
DEFAULT_DAMPING = 0.85
DEFAULT_ITERATIONS = 50
_RANK_TOLERANCE = 1e-12
_ROOT_MODULE = "(root)"

# File extensions the repo map can tag today; unknown suffixes are counted as
# "other" so the language histogram never silently drops files.
_LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".rs": "rust",
    ".lua": "lua",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
}

_ENTRYPOINT_NAMES = {
    "__main__.py",
    "main.py",
    "main.rs",
    "main.lua",
    "main.go",
    "app.py",
    "manage.py",
    "setup.py",
    "conftest.py",
    "wsgi.py",
    "asgi.py",
}
# Dev tooling and command entrypoints: useful, but "nothing imports it" is
# expected for them, so they are not dead-code candidates.
_ENTRYPOINT_PREFIXES = ("scripts/", "tools/", "bin/", "runners/dsl/src/bin/")


def _language(path: str) -> str:
    return _LANGUAGE_BY_SUFFIX.get(Path(path).suffix.lower(), "other")


def _module(path: str) -> str:
    """Top-level directory, or ``(root)`` for a file at the repo root."""
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else _ROOT_MODULE


def _is_test_file(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    # ``tests/`` anywhere in the path (top-level tests/, runners/dsl/tests/).
    if "tests" in parts[:-1]:
        return True
    return (name.startswith("test_") or name.endswith("_test.py")
            or name == "conftest.py")


def _excluded_from_dead_code(path: str) -> bool:
    """Tests, dev scripts, package markers and conventional entrypoints.

    The exclusion list is intentionally conservative: a file here could still
    contain unused code, but its lack of inbound references is expected.
    """
    if _is_test_file(path):
        return True
    if path.startswith(_ENTRYPOINT_PREFIXES):
        return True
    name = path.split("/")[-1]
    if name in _ENTRYPOINT_NAMES:
        return True
    if name in {"__init__.py", "__init__.rs", "__init__.lua"}:
        return True
    return False


def _clean_edges(graph: dict[str, Any],
                 nodes: set[str]) -> list[tuple[str, str, float]]:
    """Non-self dependency edges as sorted ``(src, tgt, weight)`` tuples.

    ``build_reference_graph`` emits ``referencer -> definer`` edges and adds
    weak self-edges for definitions nobody references. Self-edges are dropped:
    they say nothing about cross-file dependencies, and keeping them would
    inflate both in-degree and PageRank. Duplicate pairs are summed (different
    symbol names can produce the same file pair), then sorted so every
    downstream calculation has a stable iteration order.
    """
    weights: dict[tuple[str, str], float] = defaultdict(float)
    for edge in graph.get("edges") or []:
        src = str(edge.get("src") or "")
        tgt = str(edge.get("tgt") or "")
        if not src or not tgt or src == tgt:
            continue
        if src not in nodes or tgt not in nodes:
            continue
        try:
            weight = float(edge.get("weight", 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        if not math.isfinite(weight) or weight <= 0.0:
            weight = 1.0
        weights[(src, tgt)] += weight
    return [(src, tgt, weights[(src, tgt)])
            for src, tgt in sorted(weights)]


def _pagerank(nodes: list[str],
              edges: list[tuple[str, str, float]], *,
              damping: float = DEFAULT_DAMPING,
              iterations: int = DEFAULT_ITERATIONS) -> dict[str, float]:
    """Weighted, uniform-restart PageRank over the file dependency graph.

    Nodes are the indexed files (including isolated ones); edges are
    non-self. Dangling nodes redistribute their mass uniformly, so a file
    with no outgoing references does not leak rank. The iteration order is
    the sorted node/edge order supplied by the caller, which makes the
    floating-point result reproducible for a given graph.
    """
    if not nodes:
        return {}
    count = len(nodes)
    rank = {node: 1.0 / count for node in nodes}
    out_weight: dict[str, float] = {node: 0.0 for node in nodes}
    for src, _tgt, weight in edges:
        out_weight[src] = out_weight.get(src, 0.0) + weight
    for _ in range(max(1, int(iterations))):
        dangling = sum(rank[node] for node in nodes
                       if out_weight.get(node, 0.0) <= 0.0)
        base = (1.0 - damping) / count + damping * dangling / count
        new = {node: base for node in nodes}
        for src, tgt, weight in edges:
            total = out_weight.get(src, 0.0)
            if total > 0.0:
                new[tgt] += damping * rank[src] * weight / total
        delta = sum(abs(new[node] - rank[node]) for node in nodes)
        rank = new
        if delta < _RANK_TOLERANCE:
            break
    total_rank = sum(rank.values()) or 1.0
    return {node: rank[node] / total_rank for node in nodes}


def _tarjan_sccs(nodes: list[str],
                 edges: list[tuple[str, str, float]]) -> list[list[str]]:
    """Iterative Tarjan SCCs, returning components of size > 1 only.

    Iterative rather than recursive so a large file graph cannot hit Python's
    recursion limit. Each component is sorted internally; components are
    ordered by size descending, then lexicographically, so the output is
    stable.
    """
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for src, tgt, _weight in edges:
        adjacency[src].append(tgt)
    for node in adjacency:
        adjacency[node] = sorted(set(adjacency[node]))

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    counter = 0
    components: list[list[str]] = []

    for root in nodes:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        # (vertex, next-neighbour index)
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, offset = work[-1]
            neighbours = adjacency.get(node, [])
            if offset < len(neighbours):
                neighbour = neighbours[offset]
                work[-1] = (node, offset + 1)
                if neighbour not in index:
                    index[neighbour] = low[neighbour] = counter
                    counter += 1
                    stack.append(neighbour)
                    on_stack.add(neighbour)
                    work.append((neighbour, 0))
                elif neighbour in on_stack:
                    low[node] = min(low[node], index[neighbour])
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    components.append(sorted(component))

    components.sort(key=lambda comp: (-len(comp), comp))
    return components


def _ratio(tests: int, source: int) -> float | None:
    if source <= 0:
        return None
    return round(tests / source, 4)


def _summary(root: Path, cache_path: Path | None,
             files: Iterable[str] | None, top: int) -> dict[str, Any]:
    if cache_path is None:
        # Root-relative default: a report about a fixture should not read or
        # prune the canonical checkout's cache.
        cache_path = root / "var" / "ocelot_dev_tags.json"
    paths = None
    if files is not None:
        if isinstance(files, (str, Path)):
            files = [files]
        paths = sorted({str(path).replace("\\", "/") for path in files})
    cache, _stats = update_tag_cache(root, cache_path=cache_path,
                                     files=paths)
    nodes = sorted(cache.get("files") or {})
    graph = build_reference_graph(cache)
    edges = _clean_edges(graph, set(nodes))

    in_degree: dict[str, int] = {node: 0 for node in nodes}
    out_degree: dict[str, int] = {node: 0 for node in nodes}
    for src, tgt, _weight in edges:
        out_degree[src] += 1
        in_degree[tgt] += 1

    rank = _pagerank(nodes, edges)
    hub_order = sorted(
        nodes,
        key=lambda node: (-rank.get(node, 0.0), -in_degree[node], node))
    hubs = [
        {"rank": position, "path": node,
         "pagerank": round(rank.get(node, 0.0), 8),
         "in_degree": in_degree[node],
         "out_degree": out_degree[node]}
        for position, node in enumerate(hub_order[:top], start=1)
    ]

    cycles = [
        {"size": len(component),
         "files": component[:top],
         "truncated": len(component) > top}
        for component in _tarjan_sccs(nodes, edges)
    ]

    coupling_order = sorted(
        nodes,
        key=lambda node: (-(in_degree[node] + out_degree[node]),
                          -in_degree[node], -out_degree[node], node))
    coupling = {
        "top": [
            {"path": node,
             "in_degree": in_degree[node],
             "out_degree": out_degree[node],
             "total_degree": in_degree[node] + out_degree[node]}
            for node in coupling_order[:top]
        ],
        "files_with_inbound": sum(1 for node in nodes if in_degree[node]),
        "files_with_outbound": sum(1 for node in nodes if out_degree[node]),
        "max_in_degree": max(in_degree.values(), default=0),
        "max_out_degree": max(out_degree.values(), default=0),
    }

    module_counts = Counter(_module(node) for node in nodes)
    cross_edges: Counter[tuple[str, str]] = Counter()
    intra_module_edges = 0
    for src, tgt, _weight in edges:
        source_module, target_module = _module(src), _module(tgt)
        if source_module == target_module:
            intra_module_edges += 1
        else:
            cross_edges[(source_module, target_module)] += 1
    modules = {
        "count": len(module_counts),
        "by_module": [
            {"module": module, "files": count}
            for module, count in sorted(
                module_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "cross_edges": [
            {"src": src, "tgt": tgt, "edges": count}
            for (src, tgt), count in sorted(
                cross_edges.items(), key=lambda item: (-item[1], item[0]))
        ],
        "cross_edge_count": sum(cross_edges.values()),
        "intra_module_edge_count": intra_module_edges,
    }

    dead_code_candidates = [
        node for node in nodes
        if in_degree[node] == 0 and not _excluded_from_dead_code(node)
    ]

    test_files = sum(1 for node in nodes if _is_test_file(node))
    source_files = len(nodes) - test_files
    languages = Counter(_language(node) for node in nodes)

    return {
        "files": len(nodes),
        "edges": len(edges),
        "languages": {name: count
                      for name, count in sorted(languages.items())},
        "hubs": hubs,
        "cycles": cycles,
        "coupling": coupling,
        "modules": modules,
        "dead_code_candidates": dead_code_candidates,
        "test_source_ratio": {
            "tests": test_files,
            "source": source_files,
            "ratio": _ratio(test_files, source_files),
        },
    }


def _md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|")


def _render_markdown(summary: dict[str, Any], top: int) -> str:
    lines: list[str] = ["# Architecture summary", ""]
    languages = summary["languages"]
    language_text = ", ".join(f"{name} {count}"
                              for name, count in languages.items()) or "none"
    lines.append(f"- files: {summary['files']}")
    lines.append(f"- dependency edges: {summary['edges']}")
    lines.append(f"- languages: {language_text}")
    lines.append("")

    lines.append("## Hubs")
    lines.append("")
    lines.append("Ranking: weighted file-level PageRank (damping 0.85, "
                 "uniform restart, self-edges excluded); ties broken by "
                 "in-degree, then path.")
    lines.append("")
    if summary["hubs"]:
        lines.append("| rank | file | PageRank | in | out |")
        lines.append("|---:|---|---:|---:|---:|")
        for hub in summary["hubs"]:
            lines.append(
                f"| {hub['rank']} | `{_md_cell(hub['path'])}` "
                f"| {hub['pagerank']:.8f} | {hub['in_degree']} "
                f"| {hub['out_degree']} |")
    else:
        lines.append("_No files indexed._")
    lines.append("")

    lines.append("## Cycles (Tarjan SCC > 1)")
    lines.append("")
    cycles = summary["cycles"]
    if cycles:
        for cycle in cycles[:top]:
            # A syntactic name collision can merge thousands of files into one
            # SCC. ``files`` is already capped to ``top`` in the summary;
            # ``size`` still carries the true membership count.
            shown = cycle["files"][:top]
            members = ", ".join(f"`{_md_cell(path)}`" for path in shown)
            hidden = cycle["size"] - len(shown)
            suffix = f" _... and {hidden} more in this component_" \
                if hidden else ""
            lines.append(f"- {cycle['size']} files: {members}{suffix}")
        if len(cycles) > top:
            lines.append(f"- _... and {len(cycles) - top} more cycles "
                         f"(see JSON)._")
    else:
        lines.append("_No file-level reference cycles detected._")
    lines.append("")

    lines.append("## Coupling")
    lines.append("")
    lines.append("Top files by distinct non-self dependency edges; the JSON "
                 "report keeps the same top list plus aggregate degree "
                 "counts.")
    lines.append("")
    if summary["coupling"]["top"]:
        lines.append("| file | in | out | total |")
        lines.append("|---|---:|---:|---:|")
        for item in summary["coupling"]["top"]:
            lines.append(
                f"| `{_md_cell(item['path'])}` | {item['in_degree']} "
                f"| {item['out_degree']} | {item['total_degree']} |")
    else:
        lines.append("_No dependency edges._")
    lines.append("")

    lines.append("## Modules")
    lines.append("")
    lines.append("Top-level directories; cross-module edges are dependency "
                 "edges whose endpoints live in different top-level "
                 "directories.")
    lines.append("")
    if summary["modules"]["by_module"]:
        lines.append("| module | files |")
        lines.append("|---|---:|")
        for item in summary["modules"]["by_module"]:
            lines.append(f"| `{_md_cell(item['module'])}` "
                         f"| {item['files']} |")
    else:
        lines.append("_No files indexed._")
    lines.append("")
    cross_edges = summary["modules"]["cross_edges"]
    if cross_edges:
        lines.append(
            f"Cross-module edges: {summary['modules']['cross_edge_count']}")
        lines.append("")
        lines.append("| from | to | edges |")
        lines.append("|---|---|---:|")
        shown_cross = cross_edges[:top]
        for item in shown_cross:
            lines.append(f"| `{_md_cell(item['src'])}` "
                         f"| `{_md_cell(item['tgt'])}` "
                         f"| {item['edges']} |")
        if len(cross_edges) > len(shown_cross):
            lines.append(f"\n_... and {len(cross_edges) - len(shown_cross)} "
                         f"more module pairs (see JSON)._")
    else:
        lines.append("_No cross-module dependency edges._")
    lines.append("")

    lines.append("## Dead-code candidates (heuristic)")
    lines.append("")
    candidates = summary["dead_code_candidates"]
    if candidates:
        for path in candidates[:top]:
            lines.append(f"- `{_md_cell(path)}`")
        if len(candidates) > top:
            lines.append(f"- _... and {len(candidates) - top} more "
                         f"(see JSON)._")
    else:
        lines.append("_None outside tests, dev scripts and entrypoints._")
    lines.append("")
    lines.append("A candidate has zero inbound non-self reference edges. "
                 "Tests, `scripts/`, `tools/`, package markers and "
                 "conventional entrypoints are excluded. This is a reading "
                 "hint, not proof of dead code.")
    lines.append("")

    ratio = summary["test_source_ratio"]
    lines.append("## Test-to-source ratio")
    lines.append("")
    if ratio["ratio"] is None:
        lines.append(f"- tests: {ratio['tests']}; source: {ratio['source']}; "
                     "ratio: n/a (no source files)")
    else:
        lines.append(f"- tests: {ratio['tests']}; source: {ratio['source']}; "
                     f"ratio: {ratio['ratio']:.4f}")
    lines.append("")

    lines.append("## Method and limits")
    lines.append("")
    lines.append("- File-level and syntactic: edges mean \"a name defined in "
                 "the target file is used here\"; there is no scope, type or "
                 "call resolution, and imports alone are not followed.")
    lines.append("- PageRank is computed on non-self dependency edges with "
                 "dangling-mass redistribution; it is a centrality aid, not "
                 "a quality or ownership signal.")
    lines.append("- Tarjan SCCs report only components larger than one file; "
                 "self-recursion is not reported as a cycle.")
    lines.append("- External libraries and generated/vendored code are out of "
                 "scope; the tag cache only covers the repo map's source "
                 "roots.")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def architecture_report(root: str | Path = ".", *,
                        cache_path: str | Path | None = None,
                        files: Iterable[str] | None = None,
                        top: int = DEFAULT_TOP) -> dict[str, Any]:
    """Deterministic architecture report for the checkout at ``root``.

    Parameters
    ----------
    root:
        Repository root. The tag cache/graph are built relative to it.
    cache_path:
        Tag-cache path. Defaults to ``<root>/var/ocelot_dev_tags.json``.
        Pass a dedicated path when analyzing a subset: the tag cache prunes
        entries outside the scanned ``files`` set.
    files:
        Optional explicit repo-relative file list. ``None`` scans the repo
        map's source roots.
    top:
        Maximum number of hubs, coupling rows, cycle members per component
        and markdown rows (clamped to 1..200). JSON keeps every cycle
        component and every dead-code candidate, but each component's member
        list is capped to ``top`` (``truncated`` marks that).

    Returns
    -------
    ``{ok, summary, markdown, json}`` where ``summary`` contains ``files``
    (count), ``edges`` (count), ``languages``, ``hubs``, ``cycles``,
    ``coupling``, ``modules``, ``dead_code_candidates`` and
    ``test_source_ratio``. ``json`` is the pretty-printed, key-sorted JSON
    of ``summary``; ``markdown`` is the human report.

    Determinism: all collections are sorted and floats are rounded; no
    timestamps or absolute paths are included.
    """
    root_path = Path(root).resolve()
    top = max(1, min(int(top), 200))
    cache = Path(cache_path) if cache_path is not None else None
    summary = _summary(root_path, cache, files, top)
    markdown = _render_markdown(summary, top)
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    return {"ok": True, "summary": summary, "markdown": markdown,
            "json": payload}
