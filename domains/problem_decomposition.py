"""problem_decomposition — projection-racing + decompose-or-refuse for an
UNSEEN problem, over `domains/graph_treewidth.py`'s existing treewidth
machinery (`min_fill_upper_bound`, `treewidth_bound_check`,
`build_elimination_triangulation`), all reused COMPLETELY UNCHANGED. See
`docs/research/engine_substrate/PROBLEM_DECOMPOSITION_PREREG.md` for the
full design record (agreed live with the user in conversation, then
registered before building, per house discipline) and `_RESULTS.md` for the
measurements. Seventh item of the reasoning/solving toolbox arc started
2026-08-14 (after `can_junction_tree.py`, `can_native_bp.py`, entity-concept
correspondence, quantified deduction, directional correspondence,
SHAPE_AUDIT sweep 2).

THE PROBLEM THIS SOLVES. Given an unseen problem, you cannot know upfront
which "what's coupled to what" projection into a graph is the right one for
exact treewidth-bounded decomposition. The fix is not to get the projection
right — it's to make each guess cheap enough that being wrong doesn't
matter, and to reuse `min_fill_upper_bound`'s own output AS the
verification signal: a wrong/bad coupling-graph guess produces a bad (high)
induced width for free, because a wrong projection genuinely under- or
over-couples the true problem structure. Propose and verify collapse into
one cheap pass — there is no separate check to build.

THREE PIECES:

  1. CANDIDATE PROJECTIONS (`project_can_identity`, `project_can_complete`,
     `project_deduction_shared_attr`, `project_deduction_complete`,
     `project_situation_model_shared_event`) — each a plain
     `{"name", "nodes", "edges"}` dict (optionally `"edge_reason"`, see
     below), reading a REAL representation already resident in this
     codebase. Building a candidate is never a decision about which one is
     right; that's the race's job.

  2. RACING (`race_projections`) — `min_fill_upper_bound` (unchanged) on
     each candidate; one `ProjectionCandidate` node per candidate minted
     (Γ-production-generated, not a raw write); the winner (lowest
     treewidth) selected via the graph-native `Argmin` Term — the SAME
     selection idiom `can_native_orchestration.multi_start_settle_and_
     pick_best` already uses for its own K-restart winner, never a Python
     `min()`.

  3. DECOMPOSE-OR-REFUSE (`decompose_or_refuse`) — `treewidth_bound_check`
     + `build_elimination_triangulation` (both unchanged) on the winning
     projection. Within bound: bags/parent structure for a caller to solve
     per-clique (NOT built here — the per-clique solver dispatcher is the
     shape-decode-based meta-selection work discussed live but explicitly
     out of scope, the natural follow-on this rung's output feeds). Above
     bound: honest refusal, mirroring `can_junction_tree.py`'s own refusal
     shape exactly (`attempted: False`, zero mutation — this module never
     touches a live substrate for its pure-graph functions, so there is
     nothing TO mutate; only `race_projections` touches the substrate, and
     only to mint the race's own bookkeeping nodes).

BOUNDED ITERATIVE REFINEMENT (`refine_projection`, PREREG §7 — a live
amendment, registered before implementing). When round 0 fails for every
candidate, the honest move is not "refuse, full stop" (round 1 never had to
be a complete search) but ALSO not an open-ended retry loop (a hardcoded
round count is exactly the scalar-knob mistake CLAUDE.md's SHAPES-NOT-
NUMBERS section warns against). So: a caller-supplied `refine_budget`
(effort knob, default 0 = off, preserving the single-round path byte-for-
byte), a real residual signal (`gap = width - bound`, tracked round over
round — `min_fill_upper_bound` already computes this for free), and a
DECISION with three honest stop reasons (`bound_met` / `budget_exhausted`
/ `no_improvement`), never a loop that just runs out the clock. This module
never decides to try a DIFFERENT projection FAMILY on `no_improvement` —
that is real agent-level judgment (which facility to invoke next), out of
scope for pure graph-algorithm-over-a-snapshot code; it only reports an
honest, inspectable stop reason a future dispatcher could act on.

Python-vs-Rust (registered, PREREG §5): pure Python, no new Rust Term.
`Argmin` (`term.rs:382`) already does everything the racing step's
selection needs. Building candidate `(nodes, edges)` lists and reading
`edge_reason` provenance is mechanical read-out of already-resident graph
data — the SAME class of computation `can_junction_tree.can_network_from_mt`
already does in Python, not a decision over live agent/graph cognition.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from substrate_rs import Term, Var, Lit, Attr

from domains.graph_treewidth import (
    min_fill_upper_bound, treewidth_bound_check, build_elimination_triangulation,
)
from domains.can_junction_tree import can_network_from_mt


# --------------------------------------------------------------------------- #
#  CANDIDATE PROJECTIONS -- each a plain {"name","nodes","edges"} dict, the
#  exact (nodes, edges) shape graph_treewidth.py's own functions already
#  take. A candidate that has a natural notion of WHY an edge was added
#  (a shared token, a shared event) also carries "edge_reason":
#  {(a,b): reason}, consumed only by refine_projection's perturbation step
#  below -- never required, never inspected by race_projections/decompose_
#  or_refuse themselves.
# --------------------------------------------------------------------------- #

def project_can_identity(substrate, mt) -> dict:
    """The CAN belief network's own `causal_influence` edges ARE a coupling
    graph already -- the trivial/identity projection, and this rung's
    CORRECTNESS ANCHOR. Reuses `can_junction_tree.can_network_from_mt`
    UNCHANGED -- the exact same extraction `can_junction_tree.py`'s own
    direct path uses, so running the general race+decompose path on this
    candidate must reproduce that module's own decomposition exactly (see
    PROBLEM_DECOMPOSITION_RESULTS.md)."""
    net = can_network_from_mt(substrate, mt)
    return {"name": "can_identity", "nodes": list(net["nodes"]), "edges": list(net["edges"])}


def project_can_complete(substrate, mt) -> dict:
    """DELIBERATELY-BAD alternative CAN projection: every pair of concepts
    in the Mt treated as coupled, regardless of whether a real
    `causal_influence` edge exists -- a genuinely wrong "everything is
    related" guess over the SAME real node set `project_can_identity`
    reads, used to prove the racing step discriminates on this domain too
    (not just the deduction one)."""
    net = can_network_from_mt(substrate, mt)
    nodes = list(net["nodes"])
    edges = [(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]]
    return {"name": "can_complete_overcoupled", "nodes": nodes, "edges": edges}


def _schema_attrs(substrate, node) -> tuple:
    """Mechanical read of ONE knowledge_logical schema's antecedent_attr /
    consequent_attr off its `signature`/`supplies` JSON -- the SAME two
    fields `propositional_deduction.py` itself parses/writes when it
    mints/derives a schema (`signature: [["holds", antecedent_attr]]`,
    `supplies: {"relation":..., "attr": consequent_attr}`, confirmed by
    direct read, `propositional_deduction.py:276-286`); this only reads
    them back, never re-derives them."""
    at = substrate.node(node)["attrs"]
    try:
        sig = json.loads(at.get("signature") or "null")
    except Exception:
        sig = None
    try:
        supplies = json.loads(at.get("supplies") or "null")
    except Exception:
        supplies = None
    ante = None
    if sig and isinstance(sig, list) and sig and isinstance(sig[0], (list, tuple)) and len(sig[0]) >= 2:
        ante = str(sig[0][1])
    cons = None
    if supplies and isinstance(supplies, dict) and supplies.get("attr"):
        cons = str(supplies["attr"])
    return ante, cons


def project_deduction_shared_attr(substrate, schema_nodes: Sequence) -> dict:
    """Two `knowledge_logical` schemas are COUPLED iff they share an
    antecedent_attr or consequent_attr (the same variable appears in both)
    -- the natural coupling notion for a held implication set: a schema
    whose consequent feeds another's antecedent (a chain), or two schemas
    about the SAME variable, are genuinely entangled for joint inference;
    two schemas about disjoint predicates are not. Carries `edge_reason`
    (the shared attr token, deterministically the alphabetically-first one
    when a pair shares more than one) for `refine_projection`'s
    perturbation step."""
    nodes = list(schema_nodes)
    attrs = {n: set(a for a in _schema_attrs(substrate, n) if a) for n in nodes}
    edges: list[tuple] = []
    edge_reason: dict[tuple, str] = {}
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            shared = attrs[a] & attrs[b]
            if shared:
                edges.append((a, b))
                edge_reason[(a, b)] = sorted(shared)[0]
    return {"name": "deduction_shared_attr", "nodes": nodes, "edges": edges,
            "edge_reason": edge_reason}


def project_deduction_complete(substrate, schema_nodes: Sequence) -> dict:
    """DELIBERATELY-BAD alternative: every pair of schemas coupled
    regardless of shared attrs -- the "everything is related" null
    hypothesis, used to prove the racing step does real discriminating
    work, not just always pick the one obviously-good candidate handed to
    it. No `edge_reason` (there is no real "reason" for any of these edges
    -- they are the deliberately-uninformative guess)."""
    nodes = list(schema_nodes)
    edges = [(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]]
    return {"name": "deduction_complete_overcoupled", "nodes": nodes, "edges": edges}


def project_situation_model_shared_event(substrate, sm_event_nodes: Sequence) -> dict:
    """Third candidate, grounded in a real facility (used for generality,
    a judgment call per the task's own "use your judgment" allowance): two
    `SmEntity` nodes are COUPLED iff they co-occur as `agent`/`theme`/`goal`
    roles of the SAME `SmEvent` -- `situation_model_reader.py`'s own
    event-role structure already IS a coupling graph over entities
    (confirmed by direct read, `situation_model_reader.py:394-435`), read
    here mechanically (no new decision -- those are the role edge types
    that module already installs). Carries `edge_reason` (the SmEvent node
    that caused the coupling)."""
    nodes_seen: list = []
    seen_set = set()
    edges: list[tuple] = []
    edge_reason: dict[tuple, Any] = {}
    for ev in sm_event_nodes:
        roles: list = []
        for et in ("agent", "theme", "goal"):
            roles.extend(substrate.neighbours(ev, et))
        for r in roles:
            key = r.value if hasattr(r, "value") else r
            if key not in seen_set:
                seen_set.add(key)
                nodes_seen.append(r)
        for i, a in enumerate(roles):
            for b in roles[i + 1:]:
                ka = a.value if hasattr(a, "value") else a
                kb = b.value if hasattr(b, "value") else b
                if ka == kb:
                    continue
                pair = tuple(sorted((a, b), key=lambda x: repr(x.value if hasattr(x, "value") else x)))
                if pair not in edge_reason:
                    edges.append(pair)
                    edge_reason[pair] = ev
    return {"name": "situation_model_shared_event", "nodes": nodes_seen, "edges": edges,
            "edge_reason": edge_reason}


# --------------------------------------------------------------------------- #
#  RACING -- min_fill_upper_bound (unchanged) on each candidate, Argmin Term
#  decides the winner. Mirrors can_native_orchestration.multi_start_settle_
#  and_pick_best's own session/candidate/Argmin idiom exactly.
# --------------------------------------------------------------------------- #

def install_projection_race_productions(substrate) -> None:
    """Γ production for the race's own session/candidate scaffold --
    mirrors `can_native_orchestration.install_multi_start_productions`
    exactly (a GENERATED edge type, not a filter -- CLAUDE.md's
    SHAPES-NOT-NUMBERS admissibility discipline). Idempotent (`add_production`
    on an already-installed production is a no-op, the same assumption
    every other seed-adjacent `install_productions` helper in this codebase
    already makes)."""
    substrate.add_production({
        "src": {"type": "ProjectionRaceSession", "var": "src"},
        "edge_type": "pr_candidate",
        "tgt": {"type": "ProjectionCandidate", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "problem_decomposition:race",
    })


def race_projections(substrate, candidates: list) -> dict:
    """Race a SMALL SET of cheap candidate "what's coupled to what" guesses:
    `min_fill_upper_bound` (unchanged) on each, one `ProjectionCandidate`
    node minted per candidate holding its name + treewidth, and the winner
    (lowest treewidth) decided by the `Argmin` Term over those candidates --
    the SAME graph-native selection idiom `multi_start_settle_and_pick_best`
    already uses for its own K-restart winner, not a Python `min()`. A
    wrong/bad coupling-graph guess genuinely under- or over-couples the true
    problem structure, which shows up directly as a HIGH induced width in
    `min_fill_upper_bound`'s own output -- propose and verify collapse into
    one cheap pass, no separate check needed.

    Returns `{"session": NodeID, "winner": NodeID, "winner_name": str,
    "winner_nodes": [...], "winner_edges": [...],
    "candidates": [{"name","treewidth","node"}, ...]}`."""
    if not candidates:
        raise ValueError("race_projections needs at least one candidate")
    install_projection_race_productions(substrate)
    session = substrate.add_node("ProjectionRaceSession", {"n_candidates": len(candidates)})

    by_node: dict = {}
    cand_reports = []
    for cand in candidates:
        mf = min_fill_upper_bound(cand["nodes"], cand["edges"])
        node = substrate.add_node("ProjectionCandidate", {
            "proj_name": cand["name"], "treewidth": float(mf["treewidth"]),
            "n_nodes": len(cand["nodes"]), "n_edges": len(cand["edges"]),
        })
        substrate.add_edge(session, "pr_candidate", node, {})
        by_node[node] = cand
        cand_reports.append({"name": cand["name"], "treewidth": mf["treewidth"], "node": node})

    winner_term = Term(
        "Argmin",
        source=Term("Neighbours", node=Lit(session), edge_type="pr_candidate", any_type=False),
        var_name="cand",
        value=Attr(Var("cand"), "treewidth"),
    )
    winner = winner_term.evaluate(None, substrate)
    winner_cand = by_node[winner]

    return {
        "session": session, "winner": winner, "winner_name": winner_cand["name"],
        "winner_nodes": winner_cand["nodes"], "winner_edges": winner_cand["edges"],
        "candidates": cand_reports,
    }


# --------------------------------------------------------------------------- #
#  DECOMPOSE-OR-REFUSE -- treewidth_bound_check + build_elimination_
#  triangulation, both UNCHANGED. Pure function of (nodes, edges); touches
#  no substrate, so a refusal is trivially zero-mutation.
# --------------------------------------------------------------------------- #

def decompose_or_refuse(nodes: Sequence, edges: Sequence, bound: int,
                         max_exact_n: int = 10) -> dict:
    """The decompose-or-refuse gate on a SINGLE (already-chosen) projection.
    Mirrors `can_junction_tree.junction_tree_exact_settle`'s own refusal
    shape exactly: within bound -> bags/parent structure for a caller to
    solve per-clique (NOT built here, out of scope -- the natural
    follow-on); above bound -> honest refusal, `attempted: False`, zero
    mutation (this function never touches a substrate at all)."""
    tw = treewidth_bound_check(nodes, edges, bound, max_exact_n=max_exact_n)
    if not tw["within_bound"]:
        return {
            "attempted": False, "exact": tw["exact"],
            "treewidth": tw["treewidth"], "treewidth_bound": bound,
            "reason": ("treewidth %s (%s) exceeds bound %s -- refusing "
                       "decomposition, not attempting it blindly" % (
                           tw["treewidth"], "exact" if tw["exact"] else
                           "heuristic upper bound", bound)),
        }
    tri = build_elimination_triangulation(nodes, edges, tw["elimination_order"])
    return {
        "attempted": True, "exact": tw["exact"],
        "treewidth": tw["treewidth"], "treewidth_bound": bound,
        "bags": tri["bags"], "parent": tri["parent"],
        "elim_index": tri["elim_index"], "order": tri["order"],
    }


# --------------------------------------------------------------------------- #
#  BOUNDED ITERATIVE REFINEMENT (PREREG sec7, live amendment) -- an effort
#  knob + a residual signal + a decision, NOT a hardcoded round count.
# --------------------------------------------------------------------------- #

def perturb_worst_shared_reason(candidate: dict) -> dict | None:
    """ONE cheap, bounded perturbation step: if `candidate` carries
    `edge_reason` data (a real notion of WHY each edge was added -- a
    shared attr token, a shared SmEvent), find the SINGLE reason
    responsible for the MOST edges (the worst clique's projection cause --
    e.g. a widely-shared, over-generic consequent like "animal" that
    spuriously over-couples many otherwise-unrelated schemas into a
    clique) and drop exactly those edges, re-guessing that one piece as
    uncoupled. Mirrors `exact_treewidth`'s own branch-and-bound pruning
    discipline one level up: eliminate the worst-scoring cause cheaply, do
    not exhaustively re-search every possible edge subset.

    Returns `None` (no perturbation available -- the honest "nothing cheap
    to trim" signal, distinct from "tried and it didn't help") when the
    candidate carries no `edge_reason` (e.g. the CAN identity/complete
    projections: a real `causal_influence` edge has no "reason" to blame)
    or when the single worst reason covers fewer than 2 edges (not a hub,
    nothing to gain by dropping it)."""
    reason = candidate.get("edge_reason")
    if not reason:
        return None
    counts: dict = {}
    for r in reason.values():
        key = repr(r)
        counts[key] = counts.get(key, 0) + 1
    worst_key = max(counts, key=lambda k: (counts[k], k))
    if counts[worst_key] < 2:
        return None
    new_edges = [e for e in candidate["edges"] if repr(reason.get(e)) != worst_key]
    new_reason = {e: r for e, r in reason.items() if repr(r) != worst_key}
    return {"name": candidate["name"] + ("_trim[%s]" % worst_key),
            "nodes": candidate["nodes"], "edges": new_edges, "edge_reason": new_reason}


def refine_projection(candidate: dict, bound: int, budget: int) -> dict:
    """Effort-budgeted, residual-driven refinement of ONE candidate whose
    initial `min_fill_upper_bound` width exceeds `bound` -- NOT a fixed
    round count. Each round: perturb the CURRENT candidate
    (`perturb_worst_shared_reason`), re-measure its width, and track the
    REAL residual `gap = width - bound`. Stops on exactly one of three
    honest, named conditions -- never an open-ended search:

      - `"bound_met"`: `gap <= 0` -- decompose-ready.
      - `"budget_exhausted"`: `budget` rounds spent, still above bound.
      - `"no_improvement"`: the gap did not shrink from the previous round
        (or there was nothing left to perturb) -- diminishing returns;
        stop even with budget remaining, mirroring `exact_treewidth`'s own
        `if best is not None and width >= best: pruned = True; break`
        pruning one level up. This function does NOT decide to try a
        DIFFERENT projection family when this fires -- that is a real
        agent-level decision, out of scope here; it only reports the stop
        reason for a future caller/dispatcher to act on.

    Returns `{"stop_reason", "rounds_used", "final_candidate",
    "final_treewidth", "log"}` -- `log` records EVERY round tried (never
    silent, per house discipline's "no silent caps" rule)."""
    mf = min_fill_upper_bound(candidate["nodes"], candidate["edges"])
    gap = mf["treewidth"] - bound
    log = [{"round": 0, "candidate": candidate["name"], "treewidth": mf["treewidth"], "gap": gap}]
    if gap <= 0:
        return {"stop_reason": "bound_met", "rounds_used": 0,
                "final_candidate": candidate, "final_treewidth": mf["treewidth"], "log": log}

    current = candidate
    rounds_used = 0
    while rounds_used < budget:
        perturbed = perturb_worst_shared_reason(current)
        if perturbed is None:
            log.append({"round": rounds_used + 1, "candidate": None, "perturbed": False,
                        "note": "no edge_reason data (or nothing left to trim) on the "
                                "current candidate -- nothing cheap left to try"})
            return {"stop_reason": "no_improvement", "rounds_used": rounds_used,
                    "final_candidate": current, "final_treewidth": mf["treewidth"], "log": log}
        rounds_used += 1
        mf2 = min_fill_upper_bound(perturbed["nodes"], perturbed["edges"])
        new_gap = mf2["treewidth"] - bound
        log.append({"round": rounds_used, "candidate": perturbed["name"],
                    "treewidth": mf2["treewidth"], "gap": new_gap})
        if new_gap <= 0:
            return {"stop_reason": "bound_met", "rounds_used": rounds_used,
                    "final_candidate": perturbed, "final_treewidth": mf2["treewidth"], "log": log}
        if new_gap >= gap:
            return {"stop_reason": "no_improvement", "rounds_used": rounds_used,
                    "final_candidate": perturbed, "final_treewidth": mf2["treewidth"], "log": log}
        gap = new_gap
        current = perturbed
        mf = mf2

    return {"stop_reason": "budget_exhausted", "rounds_used": rounds_used,
            "final_candidate": current, "final_treewidth": mf["treewidth"], "log": log}


# --------------------------------------------------------------------------- #
#  THE FULL PIPELINE
# --------------------------------------------------------------------------- #

def decompose_problem(substrate, candidates: list, bound: int, max_exact_n: int = 10,
                       refine_budget: int = 0) -> dict:
    """The full pipeline: race the candidate projections
    (`race_projections`), then decompose-or-refuse on the winner
    (`decompose_or_refuse`). If the winner fails AND `refine_budget > 0`
    (the effort knob -- default 0 means OFF, the single-round path is
    byte-identical to calling `race_projections`+`decompose_or_refuse`
    directly), bounded residual-driven refinement
    (`refine_projection`) is attempted on the winning candidate; on
    `"bound_met"`, the refined candidate is decomposed and returned.

    Returns the `decompose_or_refuse` result plus `"winner_projection"`
    (the name of whichever candidate was ultimately decomposed, pre- or
    post-refinement), `"race"` (the full round-0 race report), and
    `"refinement"` (the `refine_projection` report, or `None` if refinement
    was off or never needed)."""
    race = race_projections(substrate, candidates)
    out = decompose_or_refuse(race["winner_nodes"], race["winner_edges"], bound,
                               max_exact_n=max_exact_n)
    out["winner_projection"] = race["winner_name"]
    out["race"] = race
    out["refinement"] = None
    if out["attempted"] or refine_budget <= 0:
        return out

    by_name = {c["name"]: c for c in candidates}
    base = by_name.get(race["winner_name"])
    if base is None:
        return out
    refine = refine_projection(base, bound, refine_budget)
    out["refinement"] = refine
    if refine["stop_reason"] == "bound_met":
        final = refine["final_candidate"]
        retry = decompose_or_refuse(final["nodes"], final["edges"], bound, max_exact_n=max_exact_n)
        retry["winner_projection"] = final["name"]
        retry["race"] = race
        retry["refinement"] = refine
        return retry
    return out


__all__ = [
    "project_can_identity",
    "project_can_complete",
    "project_deduction_shared_attr",
    "project_deduction_complete",
    "project_situation_model_shared_event",
    "install_projection_race_productions",
    "race_projections",
    "decompose_or_refuse",
    "perturb_worst_shared_reason",
    "refine_projection",
    "decompose_problem",
]
