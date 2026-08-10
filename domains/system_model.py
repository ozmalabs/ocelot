"""system_model — the generalisation of `domains/collapse_model.py`'s TIER 4
(the graph's model of its OWN total collapse) to an ARBITRARY TARGET SYSTEM.

THE CREATOR'S REFRAME: "it should also be able to model arbitrary other
systems." Tier 4 (`collapse_model.predict_collapse`) is coupled to `agent` —
it always measures the WHOLE graph it is called on. This module factors the
same three structural questions (where does the target CONVERGE, which of
its parts are FIXED POINTS, which are the VOLATILE FRONTIER) out to a
`target` parameter, so the same machinery can point at:

  1. SELF        — target="self" (default). The degenerate case: the target
                    IS the agent's own whole graph. `model_system` delegates
                    VERBATIM to `collapse_model.predict_collapse` here (not a
                    re-implementation) — see `test_system_model.py`'s parity
                    test: model_system(target="self") and predict_collapse
                    agree exactly on the same graph, by construction.

  2. SUBGRAPH     — target={"kind": "subgraph", "root"/"nodes"/"types": ...,
                    "hops": int}. A bounded piece of the agent's OWN live
                    graph, modelled as its own self-contained system (its
                    fixed/volatile classification is read off a GENERIC
                    forward-look, not the SELF-specific Observation/
                    CapabilityAxis/Impasse/Goal proxy vocabulary — a subgraph
                    need not carry that vocabulary at all).

  3. FOREIGN SNAPSHOT — target={"kind": "foreign_snapshot", "graph": {...}}.
                    `graph` is a `graph_to_dict()`-shaped dict describing a
                    system that is NOT part of the agent's own live graph at
                    all (a toy external process, a second agent's snapshot,
                    …). This is THE headline generalisation: the agent models
                    something other than itself. GROUNDING: the resulting
                    `SystemModel` is grounded in the agent's OWN OBSERVATION
                    of the foreign system (a `SensorAnchor`, via
                    `domains.grounding_reach`), never in the foreign system's
                    own internal state — "I observed this," not "this is
                    true on its own terms". This is exactly the AUDIENCE-MODEL
                    shape memory `ozma_two_model_communication` names:
                    modelling another agent/system is modelling FROM the
                    observer's vantage, anchored by the observer's sensor,
                    not by borrowing the target's own ground.

  4. META (TIER 5) — target="meta". The target IS the agent's own
                    collapse-modelling machinery — every `CollapseModel` node
                    (tier 4's own output) plus every prior `SystemModel{
                    target_kind:"meta"}` node (tier 5's own prior output) plus
                    any `RuleSummary` whose name references "collapse". This
                    is "model of the meta-model": the special case where the
                    target IS the modeller. See `test_system_model.py`'s tower
                    test for the termination proof (fixed points include the
                    frozen core; n_volatile does not grow across tier4 ->
                    tier5 -> tier6).

MACHINERY ONLY — no agent decision. Every function here is either (a) a
verbatim delegation to `collapse_model.predict_collapse` (SELF/META), or (b)
a mechanical structural read (GENERIC fixed/volatile classification: did a
node move under a bounded, reversible tier-3 `imagine()` forward-look, yes or
no), or (c) mechanical graph I/O (mint a `SystemModel` node + edges). A
follow-on task authors the RULES that read `SystemModel` nodes; this module
only produces the data those rules would read.

TRACTABILITY. Cost is bounded by the TARGET's own node-set size (a handful
of nodes for a subgraph/foreign snapshot, or the SAME O(tracked-types) proxy
`collapse_model` already uses for SELF/META), never by the live graph's total
size — see `runtime_s` on every minted node, and
`scripts/jabberwock_models_systems.py` section 4 for the empirical report.

FIXED POINTS INCLUDE THE FROZEN CORE for SELF and META (inherited verbatim
from `collapse_model.fixed_points`, which cross-checks
`domains.frozen_core.frozen_seed_ids_closed()`) — the SAME recursion anchor
`collapse_model.py`'s own module docstring proves the tier-4 tower terminates
at. SUBGRAPH and FOREIGN_SNAPSHOT targets have no frozen core of their own
(an arbitrary foreign system was never proven unreachable by this codebase's
mutation grammars — that would be a category error) — their fixed points are
read purely structurally (untouched under the forward-look) and this module
says so honestly rather than borrowing a frozen-core claim that does not
apply to them.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

import substrate_rs as srs

from domains.collapse_model import predict_collapse
from domains.grounding_reach import grounding_reach
from domains.imagination import imagine

SELF = "self"
META = "meta"

_SYS_MODEL_TYPE = "SystemModel"
_COLLAPSE_MODEL_TYPE = "CollapseModel"
_FIXED_EDGE = "fixed_point"          # same edge-type name collapse_model.py uses -- a follow-on
_VOLATILE_EDGE = "volatile_frontier"  # rule reads both CollapseModel and SystemModel with one vocabulary
_MODELS_EDGE = "models"              # SystemModel -models-> the thing(s) it is a model OF
_GROUNDED_IN_EDGE = "grounded_in"    # must match domains/grounding_reach.py's _EDGE


# ---------------------------------------------------------------------------
# duck-typed (substrate, native) resolution -- the SAME shape collapse_model.
# py / imagination.py / grounding_reach.py all use, duplicated locally (not
# imported) so this module carries no coupling to a file under concurrent
# edit -- the established precedent in this codebase.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid: Any) -> Any:
    return nid.value if hasattr(nid, "value") else nid


def _add_edge_unchecked(native, src, edge_type, tgt, attrs=None) -> None:
    try:
        native.add_edge_unchecked(src, edge_type, tgt, attrs or {})
    except TypeError:
        native.add_edge_unchecked(src, edge_type, tgt)


def _focus_closure(native, focus_nodes: list, hops: int) -> set:
    """BFS closure (both directions, any edge type) -- duplicated locally
    from `domains.imagination._focus_closure` (same shape, same reasoning as
    `_resolve` above)."""
    seen = {_v(n) for n in focus_nodes}
    frontier = list(seen)
    for _ in range(max(0, hops)):
        nxt = []
        for val in frontier:
            nid = srs.NodeID(val)
            if not native.has_node(nid):
                continue
            for nb in native.neighbours(nid, None):
                if nb.value not in seen:
                    seen.add(nb.value)
                    nxt.append(nb.value)
            for nb in native.in_neighbours(nid, None):
                if nb.value not in seen:
                    seen.add(nb.value)
                    nxt.append(nb.value)
        frontier = nxt
        if not frontier:
            break
    return seen


def _ensure_sensor_anchor(sub, native):
    """Idempotent SensorAnchor singleton -- same TYPE `domains.grounding_
    reach.ANCHOR_KINDS` recognises (that module's `_ensure_anchor` idiom,
    duplicated locally rather than importing its private helper). A model of
    a FOREIGN system is grounded in the fact that the agent OBSERVED it
    (built/ingested a `SystemModel` from its snapshot) -- this anchor stands
    for that observation, exactly the way `Agent -perceives-> VisionPercept`
    stands for a camera observation."""
    for n in sub.nodes("SensorAnchor"):
        return n
    return sub.add_node("SensorAnchor", {"kind": "SensorAnchor", "via": "system_model_observation"})


# ---------------------------------------------------------------------------
# THE RETURN VALUE -- same shape as collapse_model.CollapseModelResult, plus
# target_id/target_kind/grounded/grounding/node_count.
# ---------------------------------------------------------------------------
@dataclass
class SystemModelResult:
    model_node: Any
    target_id: str
    target_kind: str                    # "self" | "subgraph" | "foreign_snapshot" | "meta"
    converged: bool
    residual: float
    n_fixed: int
    n_volatile: int
    frontier_growth_rate: float
    horizon: int
    runtime_s: float
    fixed_points: dict = field(default_factory=dict)
    volatile_frontier: dict = field(default_factory=dict)
    fixed_sample: list = field(default_factory=list)
    volatile_sample: list = field(default_factory=list)
    forward_look_ran: bool = False
    imagine_steps_run: int = 0
    counts_trajectory: list = field(default_factory=list)
    grounded: bool = False
    grounding: dict = field(default_factory=dict)
    node_count: int = 0


# ---------------------------------------------------------------------------
# GENERIC (domain-general) chained forward-look -- the SUBGRAPH / FOREIGN_
# SNAPSHOT machinery. Unlike collapse_model._bounded_forward_look, this does
# NOT synthesise a domain-specific recurrence hypothesis (that hack is
# specific to shape_decode_loop's Observation vocabulary) -- it simply lets
# the TARGET's OWN graph-resident Rules (if any) run, unforced, and reads off
# what moved. "Fixed point" here means the LITERAL tier-4 definition ("does
# not move under collapse"), read empirically rather than off a status-attr
# proxy -- the correct fallback when the target carries no known status
# vocabulary at all.
# ---------------------------------------------------------------------------
def _chained_forward_look(base, focus_nodes: Optional[list], *, horizon: int,
                           imagine_steps: int, focus_hops: int) -> dict:
    """Run `horizon` rounds of tier-3 `imagine()` (no hypothesis injection --
    observing the target's OWN dynamics, not synthesising one), chaining each
    round's detached result into the next. `base` may be a live agent (for a
    SUBGRAPH of the live graph) or a bare, already-detached `srs.Substrate`
    (for a FOREIGN snapshot -- `imagine`'s own `_resolve` duck-types a bare
    Substrate exactly like an agent). Returns {"counts": [...], "steps_run":
    total, "rounds_run": n, "touched_sets": [set, ...]}."""
    cur = base
    counts: list = []
    touched_sets: list = []
    steps_run_total = 0
    rounds_run = 0
    for _ in range(max(1, horizon)):
        dc = imagine(cur, focus_nodes=list(focus_nodes) if focus_nodes else None,
                     hypothesis=None, steps=imagine_steps, cut_grounding=False,
                     focus_hops=focus_hops)
        steps_run_total += dc.steps_run
        touched = {n["id"] for n in dc.conclusions.get("nodes_added", [])}
        touched |= {n["id"] for n in dc.conclusions.get("nodes_changed", [])}
        touched_sets.append(touched)
        counts.append(len(touched))
        rounds_run += 1
        cur = dc.detached
    return {"counts": counts, "steps_run": steps_run_total, "rounds_run": rounds_run,
            "touched_sets": touched_sets}


def _finish_generic_target(sub, native, *, target_kind: str, target_id: str, node_set: list,
                            look: dict, horizon: int, mint_edges: int, t0: float, ground: bool,
                            agent=None, mint_node_edges: bool = True) -> SystemModelResult:
    touched_sets = look["touched_sets"]
    all_touched: set = set()
    for ts in touched_sets:
        all_touched |= ts
    node_id_values = {_v(n) for n in node_set} if node_set else set()
    touched_in_set = sorted(all_touched & node_id_values, key=str)
    new_ids = sorted(all_touched - node_id_values, key=str)   # minted DURING the look -- growth
    untouched = [n for n in node_set if _v(n) not in all_touched]

    counts = look["counts"]
    full_counts = [0] + counts
    deltas = [full_counts[i + 1] - full_counts[i] for i in range(len(full_counts) - 1)]
    frontier_growth_rate = (sum(deltas) / len(deltas)) if deltas else 0.0
    converged = frontier_growth_rate <= 0.0

    n_volatile = len(touched_in_set) + len(new_ids)
    n_fixed = len(untouched)
    denom = max(1, n_volatile + n_fixed)
    residual = 0.0 if n_volatile == 0 else min(1.0, n_volatile / denom)
    runtime_s = time.time() - t0

    volatile = {"touched": touched_in_set, "new": new_ids}
    fixed = {"untouched": untouched}

    method = (
        "GENERIC (domain-general): a bounded chained tier-3 imagine() forward-look over the "
        f"target's own node-set ({len(node_set)} nodes, horizon={horizon} rounds, <= imagine_steps "
        "collapse steps/round). A node is VOLATILE iff it (or a fresh node) was touched by the "
        "target's OWN rules during the look; FIXED iff it never moved -- the literal tier-4 "
        "definition, no type-specific status-attr proxy assumed (the target may carry no such "
        "vocabulary at all, unlike SELF/META which reuse collapse_model's cheaper proxy). Bounded "
        "by the TARGET's own node-set size, not the live graph's total size."
    )

    model = sub.add_node(_SYS_MODEL_TYPE, {
        "target_kind": target_kind, "target_id": target_id,
        "converged": bool(converged), "residual": float(residual),
        "n_fixed": int(n_fixed), "n_volatile": int(n_volatile),
        "frontier_growth_rate": float(frontier_growth_rate), "horizon": int(horizon),
        "forward_look_ran": bool(look["rounds_run"] > 0), "imagine_steps_run": int(look["steps_run"]),
        "counts_trajectory": list(full_counts),
        "node_count": int(len(node_set)),
        "grounded": False, "runtime_s": float(runtime_s), "method": method, "ts": time.time(),
    })

    fixed_sample: list = []
    volatile_sample: list = []
    if mint_node_edges:
        for n in untouched[:mint_edges]:
            _add_edge_unchecked(native, model, _FIXED_EDGE, n, {"category": "untouched"})
            fixed_sample.append(n)
        for val in (touched_in_set + new_ids)[:mint_edges]:
            nid = val if hasattr(val, "value") else srs.NodeID(val)
            if sub.has_node(nid):
                _add_edge_unchecked(native, model, _VOLATILE_EDGE, nid, {"category": "touched_or_new"})
                volatile_sample.append(nid)
    else:
        # the touched/untouched ids belong to a FOREIGN id-space -- not live
        # nodes, so they are reported as DATA on the model, never as edges
        # into the live graph (which would silently alias unrelated live ids).
        native.set_attr(model, "fixed_sample_foreign_ids", [_v(n) for n in untouched[:mint_edges]])
        native.set_attr(model, "volatile_sample_foreign_ids", (touched_in_set + new_ids)[:mint_edges])

    grounded = False
    grounding: dict = {}
    if ground and agent is not None:
        anchor = _ensure_sensor_anchor(sub, native)
        _add_edge_unchecked(native, model, _GROUNDED_IN_EDGE, anchor)
        native.set_attr(model, "grounded", True)
        grounding = grounding_reach(agent, model)
        grounded = bool(grounding.get("reached", False))

    return SystemModelResult(
        model_node=model, target_id=target_id, target_kind=target_kind,
        converged=converged, residual=residual, n_fixed=n_fixed, n_volatile=n_volatile,
        frontier_growth_rate=frontier_growth_rate, horizon=horizon, runtime_s=runtime_s,
        fixed_points=fixed, volatile_frontier=volatile,
        fixed_sample=fixed_sample, volatile_sample=volatile_sample,
        forward_look_ran=bool(look["rounds_run"] > 0), imagine_steps_run=look["steps_run"],
        counts_trajectory=full_counts, grounded=grounded, grounding=grounding,
        node_count=len(node_set),
    )


# ---------------------------------------------------------------------------
# 1. SELF -- verbatim delegation to collapse_model.predict_collapse.
# ---------------------------------------------------------------------------
def _model_self(agent, sub, native, *, horizon, frontier_sample, focus_hops, imagine_steps,
                 mint_edges, t0) -> SystemModelResult:
    cm = predict_collapse(agent, horizon=horizon, frontier_sample=frontier_sample,
                           focus_hops=focus_hops, imagine_steps=imagine_steps, mint_edges=mint_edges)
    runtime_s = time.time() - t0
    model = sub.add_node(_SYS_MODEL_TYPE, {
        "target_kind": "self", "target_id": "self",
        "converged": bool(cm.converged), "residual": float(cm.residual),
        "n_fixed": int(cm.n_fixed), "n_volatile": int(cm.n_volatile),
        "frontier_growth_rate": float(cm.frontier_growth_rate), "horizon": int(horizon),
        "forward_look_ran": bool(cm.forward_look_ran), "imagine_steps_run": int(cm.imagine_steps_run),
        "counts_trajectory": list(cm.counts_trajectory),
        "node_count": int(cm.n_fixed + cm.n_volatile),
        "grounded": False, "runtime_s": float(runtime_s), "ts": time.time(),
        "method": "SELF (degenerate case): delegates VERBATIM to domains.collapse_model."
                  "predict_collapse -- parity by construction, not re-derivation.",
    })
    _add_edge_unchecked(native, model, _MODELS_EDGE, cm.model_node, {"category": "collapse_model"})

    fixed_sample: list = []
    for k, v in cm.fixed_points.items():
        if k.startswith("_"):
            continue
        for n in v[:mint_edges]:
            _add_edge_unchecked(native, model, _FIXED_EDGE, n, {"category": k})
            fixed_sample.append(n)
    volatile_sample: list = []
    for k, v in cm.volatile_frontier.items():
        for n in v[:mint_edges]:
            _add_edge_unchecked(native, model, _VOLATILE_EDGE, n, {"category": k})
            volatile_sample.append(n)

    return SystemModelResult(
        model_node=model, target_id="self", target_kind="self",
        converged=cm.converged, residual=cm.residual, n_fixed=cm.n_fixed, n_volatile=cm.n_volatile,
        frontier_growth_rate=cm.frontier_growth_rate, horizon=horizon, runtime_s=runtime_s,
        fixed_points=cm.fixed_points, volatile_frontier=cm.volatile_frontier,
        fixed_sample=fixed_sample, volatile_sample=volatile_sample,
        forward_look_ran=cm.forward_look_ran, imagine_steps_run=cm.imagine_steps_run,
        counts_trajectory=list(cm.counts_trajectory), grounded=False, grounding={},
        node_count=cm.n_fixed + cm.n_volatile,
    )


# ---------------------------------------------------------------------------
# 2. META (TIER 5) -- target IS the agent's own modelling machinery. Reuses
# predict_collapse's whole-graph structural numbers VERBATIM (proves tier-5
# adds ZERO new tracked-volatile accounting) and adds a "settled_system_
# model" self-inclusion fixed-point category, one level up from collapse_
# model's own "settled_collapse_model" -- the SAME well-foundedness argument,
# recursed once.
# ---------------------------------------------------------------------------
def _meta_node_set(sub) -> tuple:
    collapse_models = list(sub.nodes(_COLLAPSE_MODEL_TYPE))
    prior_meta = [n for n in sub.nodes(_SYS_MODEL_TYPE)
                  if sub.node(n)["attrs"].get("target_kind") == "meta"]
    rule_summaries: list = []
    try:
        for n in sub.nodes("RuleSummary"):
            name = (sub.node(n)["attrs"].get("name") or "").lower()
            if "collapse" in name:
                rule_summaries.append(n)
    except Exception:  # noqa: BLE001 -- RuleSummary type not present in this seed set
        pass
    return collapse_models, prior_meta, rule_summaries


def _model_meta(agent, sub, native, *, horizon, frontier_sample, focus_hops, imagine_steps,
                 mint_edges, t0) -> SystemModelResult:
    collapse_models, prior_meta, rule_summaries = _meta_node_set(sub)
    cm = predict_collapse(agent, horizon=horizon, frontier_sample=frontier_sample,
                           focus_hops=focus_hops, imagine_steps=imagine_steps, mint_edges=mint_edges)
    runtime_s = time.time() - t0

    fixed = dict(cm.fixed_points)
    fixed["settled_system_model"] = list(prior_meta)  # self-inclusion, one tier up
    n_fixed = cm.n_fixed + len(prior_meta)

    method = (
        "TIER 5 (model of the meta-model): reuses domains.collapse_model.predict_collapse's "
        "whole-graph structural signals VERBATIM for n_volatile/frontier_growth_rate/fixed_points "
        "(proves tier-5 adds ZERO new tracked-volatile accounting vs tier-4/SELF) + adds a "
        "'settled_system_model' self-inclusion fixed-point category (mirrors CollapseModel's own "
        "settled_collapse_model one tier up: a SystemModel{target_kind:meta} node's attrs are never "
        "mutated again after this call mints it, so it becomes a fixed point of the very recursion "
        "it describes the instant it exists). The recursion (tier4 -> tier5 -> would-be tier6 -> ...) "
        "is well-founded for the SAME reason tier-4's is: fixed_points always includes the frozen "
        "core (domains.frozen_core.frozen_seed_ids_closed(), cross-checked inside predict_collapse), "
        "and every meta-level snapshot freezes itself the moment it is written."
    )
    model = sub.add_node(_SYS_MODEL_TYPE, {
        "target_kind": "meta", "target_id": "meta:collapse_modeling_machinery",
        "converged": bool(cm.converged), "residual": float(cm.residual),
        "n_fixed": int(n_fixed), "n_volatile": int(cm.n_volatile),
        "frontier_growth_rate": float(cm.frontier_growth_rate), "horizon": int(horizon),
        "forward_look_ran": bool(cm.forward_look_ran), "imagine_steps_run": int(cm.imagine_steps_run),
        "counts_trajectory": list(cm.counts_trajectory),
        "node_count": int(len(collapse_models) + len(prior_meta) + len(rule_summaries)),
        "n_modeled_collapse_models": int(len(collapse_models)),
        "n_modeled_prior_meta": int(len(prior_meta)),
        "grounded": False, "runtime_s": float(runtime_s), "method": method, "ts": time.time(),
    })
    for cmn in collapse_models[:mint_edges]:
        _add_edge_unchecked(native, model, _MODELS_EDGE, cmn, {"category": "collapse_model"})
    for pm in prior_meta[:mint_edges]:
        _add_edge_unchecked(native, model, _MODELS_EDGE, pm, {"category": "prior_system_model_meta"})
    for rs in rule_summaries[:mint_edges]:
        _add_edge_unchecked(native, model, _MODELS_EDGE, rs, {"category": "rule_summary"})

    fixed_sample: list = []
    for k, v in fixed.items():
        if k.startswith("_"):
            continue
        for n in v[:mint_edges]:
            _add_edge_unchecked(native, model, _FIXED_EDGE, n, {"category": k})
            fixed_sample.append(n)
    volatile_sample: list = []
    for k, v in cm.volatile_frontier.items():
        for n in v[:mint_edges]:
            _add_edge_unchecked(native, model, _VOLATILE_EDGE, n, {"category": k})
            volatile_sample.append(n)

    return SystemModelResult(
        model_node=model, target_id="meta:collapse_modeling_machinery", target_kind="meta",
        converged=cm.converged, residual=cm.residual, n_fixed=n_fixed, n_volatile=cm.n_volatile,
        frontier_growth_rate=cm.frontier_growth_rate, horizon=horizon, runtime_s=runtime_s,
        fixed_points=fixed, volatile_frontier=cm.volatile_frontier,
        fixed_sample=fixed_sample, volatile_sample=volatile_sample,
        forward_look_ran=cm.forward_look_ran, imagine_steps_run=cm.imagine_steps_run,
        counts_trajectory=list(cm.counts_trajectory), grounded=False, grounding={},
        node_count=len(collapse_models) + len(prior_meta) + len(rule_summaries),
    )


# ---------------------------------------------------------------------------
# 3. SUBGRAPH -- a bounded piece of the agent's OWN live graph, modelled
# generically (no SELF-specific status-attr proxy assumed).
# ---------------------------------------------------------------------------
def _resolve_subgraph_nodes(sub, native, target: dict, node_limit: int) -> list:
    if "nodes" in target:
        out = []
        for n in target["nodes"]:
            nid = n if hasattr(n, "value") else srs.NodeID(int(n))
            if sub.has_node(nid):
                out.append(nid)
        return out[:node_limit]
    if "root" in target:
        root = target["root"]
        root_id = root if hasattr(root, "value") else srs.NodeID(int(root))
        hops = int(target.get("hops", 1))
        closure = _focus_closure(native, [root_id], hops)
        return [srs.NodeID(v) for v in list(closure)[:node_limit]]
    if "types" in target:
        out = []
        for t in target["types"]:
            out.extend(sub.nodes(t))
            if len(out) >= node_limit:
                break
        return out[:node_limit]
    raise ValueError("subgraph target needs one of: 'nodes' / 'root' (+'hops') / 'types'")


def _model_subgraph(agent, sub, native, target: dict, *, horizon, focus_hops, imagine_steps,
                     mint_edges, node_limit, t0) -> SystemModelResult:
    node_set = _resolve_subgraph_nodes(sub, native, target, node_limit)
    target_id = target.get("id") or f"subgraph:{len(node_set)}n"
    look = _chained_forward_look(agent, node_set, horizon=horizon, imagine_steps=imagine_steps,
                                  focus_hops=focus_hops)
    return _finish_generic_target(sub, native, target_kind="subgraph", target_id=target_id,
                                   node_set=node_set, look=look, horizon=horizon,
                                   mint_edges=mint_edges, t0=t0, ground=False, mint_node_edges=True)


# ---------------------------------------------------------------------------
# 4. FOREIGN SNAPSHOT -- a system that is NOT part of the agent's live graph
# at all. THE headline generalisation: the agent models something other than
# itself, grounded in its own OBSERVATION of it.
# ---------------------------------------------------------------------------
def _model_foreign_snapshot(agent, sub, native, target: dict, *, horizon, imagine_steps,
                             mint_edges, t0) -> SystemModelResult:
    graph = target["graph"]
    foreign = srs.Substrate()
    foreign._inner.graph_from_dict(graph)
    node_set = list(foreign.nodes(None))
    target_id = target.get("id") or "foreign_snapshot"
    look = _chained_forward_look(foreign, None, horizon=horizon, imagine_steps=imagine_steps,
                                  focus_hops=0)
    return _finish_generic_target(sub, native, target_kind="foreign_snapshot", target_id=target_id,
                                   node_set=node_set, look=look, horizon=horizon,
                                   mint_edges=mint_edges, t0=t0, ground=True, agent=agent,
                                   mint_node_edges=False)


# ---------------------------------------------------------------------------
# THE ENTRY POINT
# ---------------------------------------------------------------------------
def model_system(agent, target: Any = SELF, *, horizon: int = 3, frontier_sample: int = 50,
                  focus_hops: int = 1, imagine_steps: int = 2, mint_edges: int = 15,
                  node_limit: int = 200) -> SystemModelResult:
    """Model an arbitrary TARGET system's collapse: fixed points, volatile
    frontier, and a CONVERGED/DIVERGENT call, minted as a `SystemModel` graph
    node (+ `fixed_point`/`volatile_frontier`/`models` edges to a bounded
    sample) so a follow-on agent-authored rule can read it -- the same
    contract `collapse_model.predict_collapse` gives for SELF, generalised.

    `target`:
      - `"self"` (default, or `domains.system_model.SELF`) -- the agent's own
        whole graph. Delegates verbatim to `collapse_model.predict_collapse`.
      - `"meta"` (or `domains.system_model.META`) -- TIER 5: the agent's own
        collapse-modelling machinery (every `CollapseModel` + prior meta
        `SystemModel` + collapse-referencing `RuleSummary`).
      - `{"kind": "subgraph", "root"|"nodes"|"types": ..., "hops": int}` -- a
        bounded piece of the agent's OWN live graph.
      - `{"kind": "foreign_snapshot", "graph": <graph_to_dict()-shaped dict>}`
        -- a system that is NOT part of the agent's live graph at all.
        Grounded in the agent's own SensorAnchor-mediated OBSERVATION of it
        (`domains.grounding_reach`), never in the foreign system's own
        internal ground.

    Mechanical measurement only -- no decision. See the module docstring for
    the tractability argument (cost bounded by the TARGET's own size).
    """
    sub, native = _resolve(agent)
    t0 = time.time()

    if target == SELF or target is None:
        return _model_self(agent, sub, native, horizon=horizon, frontier_sample=frontier_sample,
                            focus_hops=focus_hops, imagine_steps=imagine_steps,
                            mint_edges=mint_edges, t0=t0)
    if target == META:
        return _model_meta(agent, sub, native, horizon=horizon, frontier_sample=frontier_sample,
                            focus_hops=focus_hops, imagine_steps=imagine_steps,
                            mint_edges=mint_edges, t0=t0)
    if isinstance(target, dict) and target.get("kind") == "subgraph":
        return _model_subgraph(agent, sub, native, target, horizon=horizon, focus_hops=focus_hops,
                                imagine_steps=imagine_steps, mint_edges=mint_edges,
                                node_limit=node_limit, t0=t0)
    if isinstance(target, dict) and target.get("kind") == "foreign_snapshot":
        return _model_foreign_snapshot(agent, sub, native, target, horizon=horizon,
                                        imagine_steps=imagine_steps, mint_edges=mint_edges, t0=t0)
    raise ValueError(f"model_system: unrecognised target {target!r}")


__all__ = [
    "SELF",
    "META",
    "SystemModelResult",
    "model_system",
]
