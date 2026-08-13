"""graph_treewidth — reusable exact/heuristic treewidth computation and
elimination-ordering (triangulation) construction for small-to-medium
undirected graphs.

Extracted and generalized from `scripts/can_solver_tractability_measure.py`
::exact_treewidth (a one-off, script-local function — confirmed by grep:
not imported by anything else in the tree) per
`docs/research/engine_substrate/CAN_JUNCTION_TREE_PREREG.md` §2. This module
is PURE GRAPH-ALGORITHM CODE operating on plain `(nodes, edges)` data a
caller has already read out of a live substrate — no graph-state decision,
no rule engine, no agent cognition, no Rust needed (design reasoning in the
PREREG §4, mirroring `can_solver_tractability_measure.py::measure_low_rank`'s
own pure-Python SVD call for the same class of "math over already-read
data" work).

Two treewidth queries, composed by a third:

  - `exact_treewidth(nodes, edges, max_exact_n=10)` — brute-force minimum
    induced width over ALL elimination orderings, with branch-and-bound
    pruning (same pruning shape as the original script). CORRECT, not
    heuristic. Gated to `n <= max_exact_n` — returns `None` above that
    (never silently runs for hours; see the timing measurement in
    CAN_JUNCTION_TREE_RESULTS.md for why n=10 is the default cap).
  - `min_fill_upper_bound(nodes, edges)` — greedy min-fill heuristic
    elimination ordering. Always runs, any graph size. Returns a VALID
    (not necessarily minimum) elimination ordering and its induced width —
    a safe upper bound: the TRUE treewidth is never larger than this
    number, so "upper bound already too big" is sufficient reason to
    refuse expensive exact work without ever computing the true minimum.
  - `treewidth_bound_check(nodes, edges, bound, max_exact_n=10)` — the
    caller-facing gate: try exact if small enough (authoritative, exact
    answer), else fall back to the heuristic upper bound (conservative —
    may over-refuse a graph whose true treewidth is smaller than the
    heuristic ordering found, but never under-refuses, which is the safe
    direction for "should I attempt exponential exact inference").

`build_elimination_triangulation(nodes, edges, order)` turns nodes + edges
+ a chosen elimination order into the per-node "bag" (this node plus its
still-live neighbours at the moment it is eliminated) any caller building a
junction tree needs — one bag per node, parent-pointer tree structure via
"first later-eliminated neighbour", the standard elimination-tree
construction (Koller & Friedman shape; no novelty claimed here). Consumed
by `domains/can_junction_tree.py` for CAN-specific exact inference, but
this function itself is CAN-agnostic (works on any undirected graph).
"""
from __future__ import annotations

import itertools
from typing import Any, Hashable, Sequence


def _adjacency(nodes: Sequence[Any], edges: Sequence[tuple]) -> dict:
    adj = {n: set() for n in nodes}
    for a, b in edges:
        if a == b:
            continue
        adj[a].add(b)
        adj[b].add(a)
    return adj


def exact_treewidth(nodes: Sequence[Any], edges: Sequence[tuple],
                     max_exact_n: int = 10) -> dict | None:
    """Brute-force minimum induced width over ALL elimination orderings.
    Correct (not heuristic) for graphs with `len(nodes) <= max_exact_n`.
    Returns `None` (not an approximation, not a hang) for larger graphs —
    the caller should use `min_fill_upper_bound` instead. Returns
    `{"treewidth": int, "elimination_order": [...], "exact": True}`."""
    nodes = list(nodes)
    if len(nodes) > max_exact_n:
        return None
    if not nodes:
        return {"treewidth": 0, "elimination_order": [], "exact": True}
    adj = _adjacency(nodes, edges)
    best = None
    best_order = None
    for order in itertools.permutations(nodes):
        g = {n: set(adj[n]) for n in nodes}
        width = 0
        pruned = False
        for v in order:
            nbrs = g[v]
            width = max(width, len(nbrs))
            if best is not None and width >= best:
                pruned = True
                break
            for a in nbrs:
                for b in nbrs:
                    if a != b:
                        g[a].add(b)
                g[a].discard(v)
            del g[v]
        if not pruned and (best is None or width < best):
            best = width
            best_order = order
    return {"treewidth": best, "elimination_order": list(best_order), "exact": True}


def min_fill_upper_bound(nodes: Sequence[Any], edges: Sequence[tuple]) -> dict:
    """Greedy min-fill heuristic elimination ordering — always runs,
    regardless of graph size. NOT guaranteed minimal, but always a VALID
    elimination ordering (a correct triangulation), so its width is an
    honest upper bound on the true treewidth. Returns
    `{"treewidth": int, "elimination_order": [...], "exact": False}`."""
    nodes = list(nodes)
    if not nodes:
        return {"treewidth": 0, "elimination_order": [], "exact": False}
    adj = _adjacency(nodes, edges)
    g = {n: set(adj[n]) for n in nodes}
    remaining = set(nodes)
    order: list[Any] = []
    width = 0
    while remaining:
        best_v = None
        best_fill = None
        best_deg = None
        # Deterministic iteration order (stable tie-break) — sort by repr
        # since NodeID/int/str all support it, and this is a heuristic
        # tie-break only, not a correctness requirement.
        for v in sorted(remaining, key=repr):
            nbrs = g[v] & remaining
            deg = len(nbrs)
            nbrs_list = list(nbrs)
            fill = 0
            for i in range(len(nbrs_list)):
                for j in range(i + 1, len(nbrs_list)):
                    a, b = nbrs_list[i], nbrs_list[j]
                    if b not in g[a]:
                        fill += 1
            if (best_fill is None or fill < best_fill or
                    (fill == best_fill and deg < best_deg)):
                best_v, best_fill, best_deg = v, fill, deg
        v = best_v
        nbrs = g[v] & remaining
        width = max(width, len(nbrs))
        nbrs_list = list(nbrs)
        for i in range(len(nbrs_list)):
            for j in range(i + 1, len(nbrs_list)):
                a, b = nbrs_list[i], nbrs_list[j]
                g[a].add(b)
                g[b].add(a)
        order.append(v)
        remaining.discard(v)
    return {"treewidth": width, "elimination_order": order, "exact": False}


def treewidth_bound_check(nodes: Sequence[Any], edges: Sequence[tuple],
                           bound: int, max_exact_n: int = 10) -> dict:
    """The caller-facing gate. Tries exact computation when cheap
    (`n <= max_exact_n`); otherwise falls back to the conservative
    min-fill upper bound. Returns
    `{"treewidth": int, "exact": bool, "within_bound": bool,
    "elimination_order": [...]}`. `within_bound` is the honest
    safety-refusal signal a caller should check before attempting
    exponential exact work."""
    result = exact_treewidth(nodes, edges, max_exact_n=max_exact_n)
    if result is None:
        result = min_fill_upper_bound(nodes, edges)
    result = dict(result)
    result["within_bound"] = result["treewidth"] <= bound
    return result


def build_elimination_triangulation(nodes: Sequence[Any], edges: Sequence[tuple],
                                     order: Sequence[Any]) -> dict:
    """Simulate elimination along `order`. Returns:
      - `bags`: {node: frozenset} — bag(v) = {v} | v's still-live
        neighbours at the moment v is eliminated (one bag per node).
      - `parent`: {node: node_or_None} — the first later-eliminated
        neighbour of v (standard elimination-tree parent pointer); `None`
        for a root (last-eliminated node of its connected component — a
        graph with >1 connected component yields a forest, one root per
        component).
      - `elim_index`: {node: int} — position of each node in `order`.
    This is the classical elimination-tree / clique-tree construction
    (Koller & Friedman shape) — the running-intersection property (every
    child's bag-minus-itself is a subset of its parent's bag) is a
    textbook guarantee of this exact construction, not re-derived here."""
    nodes = list(nodes)
    order = list(order)
    assert set(order) == set(nodes), "order must be a permutation of nodes"
    adj = _adjacency(nodes, edges)
    g = {n: set(adj[n]) for n in nodes}
    elim_index = {v: i for i, v in enumerate(order)}
    bags: dict[Any, frozenset] = {}
    parent: dict[Any, Any] = {}
    for v in order:
        nbrs = set(g[v])
        bags[v] = frozenset({v}) | nbrs
        if nbrs:
            # First later-eliminated neighbour = parent.
            parent[v] = min(nbrs, key=lambda u: elim_index[u])
        else:
            parent[v] = None
        nbrs_list = list(nbrs)
        for i in range(len(nbrs_list)):
            for j in range(i + 1, len(nbrs_list)):
                a, b = nbrs_list[i], nbrs_list[j]
                if b not in g[a]:
                    g[a].add(b)
                    g[b].add(a)
        for n in nbrs:
            g[n].discard(v)
        del g[v]
    return {"bags": bags, "parent": parent, "elim_index": elim_index, "order": order}


__all__ = [
    "exact_treewidth",
    "min_fill_upper_bound",
    "treewidth_bound_check",
    "build_elimination_triangulation",
]
