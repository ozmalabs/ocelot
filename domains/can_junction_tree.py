"""can_junction_tree — EXACT junction-tree inference for low-treewidth CAN
networks (`docs/research/engine_substrate/CAN_JUNCTION_TREE_PREREG.md` /
`_RESULTS.md`).

A genuinely different, STRONGER tool than the existing CAN solving
strategies in `domains/can_native_orchestration.py`:

  - the native discrete-async update (`can_native_update_3state`/`_2state`)
    is proven CONVERGENT, but only to *a* stable state — coordinate-wise
    ICM on the Ising energy `can_ops.rs::mt_energy` defines
    (`H(sigma) = -sum_i h_i sigma_i - sum_{i<j} J_ij sigma_i sigma_j`);
  - `multi_start_settle_and_pick_best` widens the search across K random
    restarts and keeps the best (lowest-frustration) result found — a
    heuristic improvement, still not a proof of global optimality;
  - THIS module computes the PROVABLY GLOBAL minimum of the exact same
    `H(sigma)` via junction-tree message passing — exact, not
    approximate, whenever the network's treewidth is small enough
    (`CAN_SOLVER_TRACTABILITY_RESULTS.md` §2 measured Bigville's real
    per-resident template at treewidth 2; this module makes that number
    usable).

TOOLBOX DESIGN (registered in the PREREG §5, not automatic dispatch): this
is a SEPARATE, explicit opt-in entrypoint
(`junction_tree_exact_settle`), not a new function inside
`can_native_orchestration.py` and not a silent treewidth-gated swap inside
any existing call site. A caller who wants the exact guarantee asks for
it; every existing caller of the native update / multi-start is
unaffected.

PURE PYTHON, NO NEW RUST TERM (PREREG §4): treewidth computation and
junction-tree construction/message-passing are graph algorithms over a
plain, already-read `(nodes, edges, unary, pairwise)` snapshot — the same
class of "math over data already pulled out of the graph" as
`scripts/can_solver_tractability_measure.py::measure_low_rank`'s own SVD
call, not a decision over live agent/graph cognition. The two places this
DOES touch the live substrate are both mechanical, precedented shapes:
reading `external_field`/`identity_field`/edge `weight` via the SAME
`Term("Edges", ...)` + `Term("EdgeAttr", ...)` composition
`domains/can_counterfactual.py` already uses, and committing the
ALREADY-DECIDED winning state back via `set_attr` — the same mechanical
commit shape `multi_start_settle_and_pick_best`'s own final step uses. No
`if`/`else` here decides what the agent's graph should contain; the one
threshold check (`treewidth <= bound`) is a computational-feasibility
safety gate ("is exact work even attemptable"), not a decision over
cognitive/discourse state.
"""
from __future__ import annotations

import itertools
from typing import Any

from substrate_rs import Term, Lit

from domains.graph_treewidth import (
    treewidth_bound_check, build_elimination_triangulation,
)

DEFAULT_TREEWIDTH_BOUND = 4
"""Bags of size <=5 at 3-state vocab = 3^5=243 states/bag -- cheap. Chosen
generously above Bigville's real measured treewidth (2,
CAN_SOLVER_TRACTABILITY_RESULTS.md §2) while still refusing the N=16
stress case (treewidth 15) by a wide margin."""

DEFAULT_MAX_EXACT_TREEWIDTH_N = 10
"""Matches `graph_treewidth.exact_treewidth`'s own default — see that
module's docstring / CAN_JUNCTION_TREE_RESULTS.md for the measured timing
(complete-graph n=10, the worst case for the pruning heuristic, ~5s)."""

_DISCRETE_VOCAB = {
    "3state": (-1.0, 0.0, 1.0),
    "2state": (-1.0, 1.0),
}
"""Verbatim twin of `can_native_orchestration.py::_DISCRETE_VOCAB` --
duplicated rather than imported to keep this module's only dependency on
`can_native_orchestration.py` at zero (PREREG §0's collision-avoidance
decision: this rung adds files, it does not edit that one)."""


def can_network_from_mt(substrate, mt) -> dict:
    """Mechanical read of Mt's discrete CAN network into plain
    `(nodes, edges, unary, pairwise, vocab)` data. Pure read, no mutation.

    `unary[i] = external_field(i) + identity_field(i)` and
    `pairwise[frozenset({i,j})] = weight` are read via
    `Term("Edges", ...)`/`Term("EdgeAttr", ...)` evaluation — confirmed
    live (CAN_JUNCTION_TREE_PREREG.md §4) that `Edges` evaluates directly
    to `(src, edge_type, tgt)` tuples and `EdgeAttr` evaluates directly to
    the raw float, so no further Term construction is needed to extract
    either. Each undirected pair is stored once (first edge direction
    encountered wins) — `build_resident_can_mt` always mints both
    directions with the SAME weight (its own module docstring,
    `worlds/bigville_can_beliefs.py:180-194`), so this is a safe
    simplification for every real network this module targets, mirroring
    `enumerate_couplings`'s (`can_ops.rs:288-322`) own single-count-per-pair
    discipline.
    """
    concepts = list(substrate.neighbours(mt, "has_concept"))
    node_by_id: dict[int, Any] = {}
    for c in concepts:
        cid = c.value if hasattr(c, "value") else int(c)
        node_by_id[cid] = c
    nodes = list(node_by_id.keys())

    unary: dict[int, float] = {}
    for cid, c in node_by_id.items():
        attrs = substrate.node(c)["attrs"]
        unary[cid] = float(attrs.get("external_field", 0.0)) + float(attrs.get("identity_field", 0.0))

    pairwise: dict[frozenset, float] = {}
    edges: list[tuple[int, int]] = []
    for cid, c in node_by_id.items():
        for e in Term("Edges", node=Lit(c), edge_type="causal_influence").evaluate(None, substrate):
            tgt = e[2]
            tid = tgt.value if hasattr(tgt, "value") else int(tgt)
            if tid not in node_by_id or tid == cid:
                continue
            key = frozenset((cid, tid))
            if key in pairwise:
                continue
            w = float(Term("EdgeAttr", edge=Lit(e), key="weight").evaluate(None, substrate))
            pairwise[key] = w
            edges.append((cid, tid))

    discrete_mode = substrate.node(mt)["attrs"].get("discrete_mode", "3state")
    vocab = _DISCRETE_VOCAB.get(discrete_mode, _DISCRETE_VOCAB["3state"])

    return {
        "nodes": nodes, "edges": edges, "unary": unary, "pairwise": pairwise,
        "vocab": vocab, "node_by_id": node_by_id, "discrete_mode": discrete_mode,
    }


def energy_of_state(unary: dict, pairwise: dict, state: dict) -> float:
    """Verbatim mirror of `can_ops.rs::mt_energy`'s formula:
    `H(sigma) = -sum_i h_i sigma_i - sum_{i<j} J_ij sigma_i sigma_j`.
    Pure arithmetic, no graph access -- used both internally by
    `junction_tree_map`'s message passing and as the ground-truth
    objective `brute_force_map` enumerates against."""
    e = 0.0
    for i, h in unary.items():
        e -= h * state.get(i, 0.0)
    for pair, j in pairwise.items():
        i, k = tuple(pair)
        e -= j * state.get(i, 0.0) * state.get(k, 0.0)
    return e


def brute_force_map(nodes: list, unary: dict, pairwise: dict, vocab: tuple) -> dict:
    """Literal enumeration of ALL `|vocab|^|nodes|` states. Ground truth
    for the correctness proof (CAN_JUNCTION_TREE_RESULTS.md) -- NOT a
    production solving path (exponential; only ever called on genuinely
    small networks in tests/demonstrations, e.g. Bigville's real 5-node
    template: `3^5=243`)."""
    best_state = None
    best_energy = None
    for combo in itertools.product(vocab, repeat=len(nodes)):
        state = dict(zip(nodes, combo))
        e = energy_of_state(unary, pairwise, state)
        if best_energy is None or e < best_energy:
            best_energy = e
            best_state = state
    return {"state": best_state, "energy": best_energy}


def _local_energy(v, full_assign: dict, unary: dict, pairwise: dict, scope_v: frozenset) -> float:
    e = -unary.get(v, 0.0) * full_assign[v]
    for u in scope_v:
        if u == v:
            continue
        j = pairwise.get(frozenset((v, u)))
        if j is not None:
            e -= j * full_assign[v] * full_assign[u]
    return e


def junction_tree_map(nodes: list, edges: list, unary: dict, pairwise: dict,
                       vocab: tuple, order: list | None = None) -> dict:
    """Exact global-minimum-energy state via junction-tree message
    passing (min-sum) over the elimination tree built from `order`.

    NOT loopy belief propagation: this runs on a TREE (the elimination
    tree `graph_treewidth.build_elimination_triangulation` builds), so
    message passing is exact by construction -- one leaf-to-root sweep
    (computing, per bag, the minimum achievable energy for every possible
    assignment to its separator with its parent, folding in every
    child's already-computed message) followed by one root-to-leaf
    backtrack (reconstructing one globally-optimal full assignment).
    Standard textbook algorithm (Koller & Friedman shape); the guarantee
    this rung needs from it -- exactness, not approximation -- follows
    directly from the tree having no cycles, unlike a sibling rung's
    loopy-BP tool.

    Returns `{"state": {node: sigma}, "energy": float,
    "max_bag_size": int}`.
    """
    if not nodes:
        return {"state": {}, "energy": 0.0, "max_bag_size": 0}
    if order is None:
        order = list(nodes)
    tri = build_elimination_triangulation(nodes, edges, order)
    bags, parent = tri["bags"], tri["parent"]

    children: dict[Any, list] = {v: [] for v in nodes}
    roots = []
    for v in order:
        p = parent[v]
        if p is None:
            roots.append(v)
        else:
            children[p].append(v)

    # msg[v]: {sep_assignment_tuple: (min_energy_of_subtree, best_sigma_v)}
    msg: dict[Any, dict[tuple, tuple]] = {}
    sep_vars: dict[Any, tuple] = {}

    for v in order:  # children always precede their parent in `order`.
        scope_v = bags[v]
        sep = tuple(sorted(scope_v - {v}, key=repr))
        sep_vars[v] = sep
        child_list = children[v]
        table: dict[tuple, tuple] = {}
        for sep_assign in itertools.product(vocab, repeat=len(sep)):
            sep_map = dict(zip(sep, sep_assign))
            best_val = None
            best_sigma = None
            for sigma_v in vocab:
                full = dict(sep_map)
                full[v] = sigma_v
                val = _local_energy(v, full, unary, pairwise, scope_v)
                for c in child_list:
                    c_sep = sep_vars[c]
                    c_key = tuple(full[u] for u in c_sep)
                    child_val, _ = msg[c][c_key]
                    val += child_val
                if best_val is None or val < best_val:
                    best_val, best_sigma = val, sigma_v
            table[sep_assign] = (best_val, best_sigma)
        msg[v] = table

    total_energy = 0.0
    solution: dict[Any, float] = {}
    bag_sizes = [len(b) for b in bags.values()]
    for r in roots:
        best_val, best_sigma = msg[r][()]
        total_energy += best_val
        solution[r] = best_sigma
        stack = [r]
        while stack:
            v = stack.pop()
            for c in children[v]:
                c_sep = sep_vars[c]
                # Running-intersection guarantee (elimination-tree lemma,
                # PREREG §3): sep(c) subset of bag(parent(c))=bag(v), and
                # bag(v) = {v} | sep(v), both of which are fully decided
                # by the time v is popped -- so every var c_sep needs is
                # already in `solution`.
                c_key = tuple(solution[u] for u in c_sep)
                _, c_sigma = msg[c][c_key]
                solution[c] = c_sigma
                stack.append(c)

    return {"state": solution, "energy": total_energy,
            "max_bag_size": max(bag_sizes) if bag_sizes else 0}


def junction_tree_exact_settle(
    substrate, mt, treewidth_bound: int = DEFAULT_TREEWIDTH_BOUND,
    max_exact_n: int = DEFAULT_MAX_EXACT_TREEWIDTH_N, commit: bool = True,
) -> dict:
    """The toolbox entrypoint. Reads Mt's network, checks its treewidth
    against `treewidth_bound` (a computational-feasibility safety gate,
    not a cognitive decision -- see module docstring), and:

      - if the treewidth (exact if `n <= max_exact_n`, else a safe
        min-fill heuristic UPPER bound) exceeds `treewidth_bound`:
        REFUSES honestly. Returns `attempted=False, exact=False` and a
        `reason` string. No graph mutation, no exponential computation
        attempted.
      - else: computes the exact global-minimum-energy state via
        `junction_tree_map`, and (if `commit=True`, the default) writes
        it onto the real Concepts via `set_attr` -- mechanical
        translation of an already-fully-decided result, the same shape
        `multi_start_settle_and_pick_best`'s own final commit step uses.
        Also cross-checks the committed state's energy against the LIVE
        `substrate.mt_energy` (the Rust engine's own definition of this
        same quantity) and reports `mt_frustration_given_state` too, for
        direct comparability with `multi_start_settle_and_pick_best`'s
        own reported metric.

    Returns a dict; see the two branches above for the exact keys.
    """
    net = can_network_from_mt(substrate, mt)
    nodes, edges = net["nodes"], net["edges"]
    tw = treewidth_bound_check(nodes, edges, treewidth_bound, max_exact_n=max_exact_n)

    if not tw["within_bound"]:
        return {
            "attempted": False, "exact": False,
            "treewidth": tw["treewidth"], "treewidth_is_exact": tw["exact"],
            "treewidth_bound": treewidth_bound,
            "reason": (
                "treewidth %s (%s) exceeds bound %s -- refusing exponential "
                "exact inference, not attempting it blindly" % (
                    tw["treewidth"], "exact" if tw["exact"] else "heuristic upper bound",
                    treewidth_bound)
            ),
        }

    result = junction_tree_map(nodes, edges, net["unary"], net["pairwise"], net["vocab"],
                                order=tw["elimination_order"])
    out = {
        "attempted": True, "exact": True,
        "treewidth": tw["treewidth"], "treewidth_is_exact": tw["exact"],
        "treewidth_bound": treewidth_bound,
        "energy": result["energy"], "max_bag_size": result["max_bag_size"],
        "state": {cid: result["state"][cid] for cid in nodes},
    }
    if commit:
        for cid, c in net["node_by_id"].items():
            substrate.set_attr(c, "state", float(result["state"][cid]))
        live_state = {cid: float(result["state"][cid]) for cid in nodes}
        out["mt_energy_confirmed"] = float(substrate.mt_energy(mt, live_state))
        out["frustration"] = float(substrate.mt_frustration_given_state(mt, live_state))
    return out


__all__ = [
    "DEFAULT_TREEWIDTH_BOUND",
    "DEFAULT_MAX_EXACT_TREEWIDTH_N",
    "can_network_from_mt",
    "energy_of_state",
    "brute_force_map",
    "junction_tree_map",
    "junction_tree_exact_settle",
]
