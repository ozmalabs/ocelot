"""collapse_model — TIER 4 of the collapse-modeling stack: THE META-COLLAPSE
MODEL OF THE WHOLE GRAPH, the graph modeling its OWN total collapse as one
object.

THE TIER LAW (creator's structure, continued from `domains/imagination.py`'s
tier 3): tier 1 is collapse itself (`tick()` / `run_rules()` — rule matching
+ effect application IS the collapse); tier 2 is residual-feedback,
model-layer cognition, frame-LOCKED (`seeds/residual_salience.json`); tier 3
is running the SAME collapse machinery DETACHED from the external frame
(imagination/counterfactual, `domains/imagination.py`); tier 4 — this module
— models the WHOLE graph's collapse: where does it converge, which nodes are
FIXED POINTS (don't move under collapse — the stable self, including the
frozen core), which are the VOLATILE FRONTIER (still changing — unresolved
residual / pending rule matches), does it CONVERGE or DIVERGE, what is the
total residual. This is the graph's model of its own becoming.

This module builds ONLY the mechanical MACHINERY (host: predict the
whole-graph collapse and mint it as inspectable graph data) — a follow-on
task has the agent AUTHOR rules that USE the resulting `CollapseModel` node.
Nothing here is an agent decision: `predict_collapse` is a structural
measurement (cheap enumeration over a handful of already-existing resolution
signals the agent's OWN rules already write) plus, when it sharpens the
estimate, a BOUNDED, reversible tier-3 forward-look — never a Python
if/else over graph state deciding what the agent should do next.

TRACTABILITY (the creator's standing law, memory `ozma_tractable_not_
impractical`): this does NOT brute-force-simulate the whole graph K steps
forward. Two structural shortcuts keep it cheap regardless of total graph
size:

  1. FIXED POINTS / VOLATILE FRONTIER are read off a SMALL, FIXED set of
     already-existing per-node-type resolution signals the agent's own rule
     families already maintain (`Observation.status`, `CapabilityAxis.
     saturation`, `Impasse.resolved`, `Goal.status`, plus the frozen core
     from `domains/frozen_core.py`) — one `sub.nodes(<type>)` scan per
     TRACKED TYPE (a handful), never a scan of every node of every type in
     the graph. Cost is O(count of the handful of tracked types), not
     O(total graph size).

  2. The optional forward-look (when there IS a volatile frontier to look
     from) reuses `domains.imagination.imagine` with `focus_nodes` set to
     the (bounded) frontier SAMPLE and a small `focus_hops` — `imagine`'s
     own snapshot preserves every live node's IDENTITY (a correctness
     requirement of that module, not a size choice) but restricts the
     EDGE SET to the focus closure, so the detached collapse's rule
     matching can only reach the sampled neighbourhood — the per-step
     matching cost is bounded by the frontier sample's own neighbourhood,
     not by the graph's total edge count. `steps` is capped small
     (`imagine_steps`, default 2) and the number of forward-look ROUNDS is
     capped small (`horizon`, default 3) — this is a FEW bounded, reversible
     collapse steps on a small snapshot, not a full re-simulation.

  `predict_collapse` reports its own measured wall-clock runtime
  (`runtime_s`) on the minted `CollapseModel` node so a caller (or this
  module's own test/gate) can verify the tractability claim empirically,
  not just by reading this docstring.

FIXED POINTS INCLUDE THE FROZEN CORE — the recursion anchor. `fixed_points`
always includes (when present in the given agent's graph) the frozen `Drive`
nodes, `Seed` nodes whose id is in `domains.frozen_core.
frozen_seed_ids_closed()`, and `RuleSummary` nodes whose provenance
(`from_seed`) is in that same closed set — the exact frozen core
`domains/frozen_core.py` proves UNREACHABLE from every self-modification
mutation grammar. This is "the another tier inside" made rigorous, not an
infinite tower: tier 4 models the graph's own becoming, tier 4's model is
itself graph data (a `CollapseModel` node — see SELF-INCLUSION below), and
the recursion this invites (a model of a graph containing a model of that
graph...) is WELL-FOUNDED precisely because it bottoms out at the frozen
core — nodes that, by construction (`domains/frozen_core.py`'s
`assert_core_unreachable`), NO mutation grammar can ever move. A model that
includes the frozen core among its own fixed points is a model that knows
where recursion terminates.

SELF-INCLUSION. The `CollapseModel` node `predict_collapse` mints is ITSELF
part of the live graph a SUBSEQUENT `predict_collapse` call measures. Two
things keep this from adding unbounded volatility on re-run: (a)
`CollapseModel` is not one of the tracked VOLATILE types (`Observation` /
`CapabilityAxis` / `Impasse` / `Goal`), so its mere existence never inflates
`n_volatile`; (b) `fixed_points` explicitly counts every PRIOR
`CollapseModel` node as a `settled_collapse_model` fixed point — a
`CollapseModel` node's own attrs are never mutated again after minting (this
module writes each one exactly once), so the instant one is minted it BECOMES
a fixed point of the very collapse it describes. The model of the model
converges by construction — each meta-level snapshot freezes itself the
moment it is written, so the tower never has to be climbed to know it
terminates.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

import substrate_rs as srs

from domains.frozen_core import frozen_seed_ids_closed
from domains.imagination import imagine

_MODEL_TYPE = "CollapseModel"
_FIXED_EDGE = "fixed_point"
_VOLATILE_EDGE = "volatile_frontier"

# Terminal statuses for the tracked non-axis types -- ONE definition, reused
# everywhere volatility is judged (the live graph AND every detached copy a
# bounded forward-look produces), so "what counts as settled" never drifts
# between the structural read and the forward-look's own re-measurement.
_OBS_TERMINAL = {"recognized", "recognized_transformed", "recognized_duplicate", "minted"}
_GOAL_TERMINAL = {"resolved", "walled", "satisfied", "done", "achieved", "completed", "failed"}


# ---------------------------------------------------------------------------
# duck-typed (substrate, native) resolution -- the SAME shape domains/
# imagination.py._resolve uses, duplicated locally (not imported) so this
# module carries no coupling to a file under concurrent edit -- the same
# precedent imagination.py itself set relative to domains/grounding_reach.py.
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


def _agent_root_node(sub):
    """Mechanical graph read: the substrate's own Agent ROOT node (as opposed
    to the `Agent{is_class:True}` class-marker node) -- duplicated locally
    from `domains.reflective_faculty._agent_root_node` (same shape, same
    reasoning as `_resolve` above: no coupling to a file under concurrent
    edit by the follow-on cognition task). Returns None if absent."""
    for n in sub.nodes("Agent"):
        at = sub.node(n)["attrs"]
        if not at.get("is_class"):
            return n
    return None


# ---------------------------------------------------------------------------
# VOLATILE FRONTIER -- cheap, O(tracked-types) structural query. Every signal
# reused here is one the agent's OWN rule families already write as part of
# their ordinary terminal/non-terminal bookkeeping -- never a new decision,
# never a new field:
#   Observation.status         -- seeds/shape_decode_loop.json's sd_* rules
#   CapabilityAxis.saturation  -- domains/gap_prioritiser.py (0=open,1=done;
#                                 the SAME belief seeds/autonomy.json's
#                                 `understand` Drive's own frontier_pick_term
#                                 weights by (1-saturation))
#   Impasse.resolved           -- domains/reflective_faculty.py rung-5 /
#                                 belief_revision.py / phonology.py
#   Goal.status                -- domains/question_driver.py / reflective_
#                                 faculty.py's composed comprehension rules
# ---------------------------------------------------------------------------
def volatile_frontier(agent) -> dict[str, list]:
    """{"Observation": [...], "CapabilityAxis": [...], "Impasse": [...],
    "Goal": [...]} -- node ids whose own tracked field says "not yet
    settled". One `sub.nodes(<type>)` scan per tracked type; missing/absent
    fields default to the OPEN reading (a node that has never been touched
    by its owning rule family is volatile, not silently assumed settled)."""
    sub, _ = _resolve(agent)
    out: dict[str, list] = {"Observation": [], "CapabilityAxis": [], "Impasse": [], "Goal": []}
    for n in sub.nodes("Observation"):
        at = sub.node(n)["attrs"]
        if at.get("status") not in _OBS_TERMINAL:
            out["Observation"].append(n)
    for n in sub.nodes("CapabilityAxis"):
        at = sub.node(n)["attrs"]
        if at.get("is_axis") != 1.0 and not at.get("induced"):
            continue
        try:
            sat = float(at.get("saturation", 0.0) or 0.0)
        except (TypeError, ValueError):
            sat = 0.0
        if sat < 1.0:
            out["CapabilityAxis"].append(n)
    for n in sub.nodes("Impasse"):
        at = sub.node(n)["attrs"]
        try:
            resolved = float(at.get("resolved", 0.0) or 0.0)
        except (TypeError, ValueError):
            resolved = 0.0
        if resolved < 1.0:
            out["Impasse"].append(n)
    for n in sub.nodes("Goal"):
        at = sub.node(n)["attrs"]
        if at.get("status") not in _GOAL_TERMINAL:
            out["Goal"].append(n)
    return out


def _volatile_count(agent) -> int:
    vf = volatile_frontier(agent)
    return sum(len(v) for v in vf.values())


# ---------------------------------------------------------------------------
# FIXED POINTS -- the frozen core (the recursion anchor) + every currently
# SETTLED instance of a tracked type (not frozen, but not currently moving)
# + every PRIOR CollapseModel node (self-inclusion, see module docstring).
# ---------------------------------------------------------------------------
def fixed_points(agent) -> dict[str, list]:
    """{"frozen_drive": [...], "frozen_seed": [...], "frozen_rule": [...],
    "settled_observation": [...], "settled_capability_axis": [...],
    "settled_impasse": [...], "settled_goal": [...],
    "settled_collapse_model": [...]}. The first three are the frozen core,
    cross-checked against `domains.frozen_core.frozen_seed_ids_closed()`
    (the dependency-closed frozen set `domains/frozen_core.py` proves
    unreachable from every mutation grammar) -- never re-derived, only read
    against the SAME closure that module already computes. The remaining
    four are structurally stable: not frozen, but not currently volatile
    either (see `volatile_frontier`). `frozen_closure_error` is non-None
    (and the frozen_* categories empty) only if `frozen_seed_ids_closed()`
    itself raised -- reported, never silently swallowed into an empty-but-
    looks-fine result (mirrors `domains/frozen_core.py:frozen_core_set`'s
    own honesty convention for a closure failure)."""
    sub, _ = _resolve(agent)
    out: dict[str, list] = {
        "frozen_drive": [], "frozen_seed": [], "frozen_rule": [],
        "settled_observation": [], "settled_capability_axis": [],
        "settled_impasse": [], "settled_goal": [], "settled_collapse_model": [],
    }
    frozen_seeds: set = set()
    closure_error: Optional[str] = None
    try:
        frozen_seeds = set(frozen_seed_ids_closed())
    except Exception as e:  # noqa: BLE001 -- reported via the return, not raised
        closure_error = f"{type(e).__name__}: {e}"

    if closure_error is None:
        for n in sub.nodes("Drive"):
            if sub.node(n)["attrs"].get("frozen"):
                out["frozen_drive"].append(n)
        for n in sub.nodes("Seed"):
            if sub.node(n)["attrs"].get("id") in frozen_seeds:
                out["frozen_seed"].append(n)
        for n in sub.nodes("RuleSummary"):
            if sub.node(n)["attrs"].get("from_seed") in frozen_seeds:
                out["frozen_rule"].append(n)

    volatile_ids = {n for lst in volatile_frontier(sub).values() for n in lst}
    for n in sub.nodes("Observation"):
        if n not in volatile_ids:
            out["settled_observation"].append(n)
    for n in sub.nodes("CapabilityAxis"):
        at = sub.node(n)["attrs"]
        if (at.get("is_axis") == 1.0 or at.get("induced")) and n not in volatile_ids:
            out["settled_capability_axis"].append(n)
    for n in sub.nodes("Impasse"):
        if n not in volatile_ids:
            out["settled_impasse"].append(n)
    for n in sub.nodes("Goal"):
        if n not in volatile_ids:
            out["settled_goal"].append(n)
    # SELF-INCLUSION: a prior CollapseModel node's attrs are never mutated
    # again after `predict_collapse` mints it -- it is, by construction, a
    # fixed point of the collapse it describes the instant it exists.
    out["settled_collapse_model"] = list(sub.nodes(_MODEL_TYPE))
    out["_closure_error"] = closure_error  # type: ignore[assignment]
    return out


# ---------------------------------------------------------------------------
# BOUNDED, REVERSIBLE FORWARD-LOOK -- reuses tier-3 `imagine` with
# `cut_grounding=False` (this is a look at what the REAL, grounded collapse
# would do next -- not a counterfactual/hypothesis exploration, tier-3's
# usual `cut_grounding=True` role) chained over a SMALL number of ROUNDS,
# each round mechanically re-injecting "the same shape of unresolved
# Observation recurs once more" -- continuous per-frame perception
# re-observing a structurally similar residual is EXACTLY the mechanism that
# drove the live axis-runaway incident this module's own test reconstructs
# (seeds/shape_decode_loop.json's `sd_mint_quantum` comment, 2026-07-03,
# "creator directive 'salience for axes'"). This is a mechanical COPY+RETAG
# of data the graph already holds (the sampled Observation's own
# `signature`, under a fresh round-tagged `key`) -- not a decision; the REAL
# rules already installed on the graph (`sd_decode` / `sd_mint_quantum` /
# `sd_dedup_existing` / ...) decide, each round, whether it mints or dedups.
# Nothing here is ever written to the LIVE graph except via `imagine`'s own
# sanctioned durable trace (`Imagination`/`ImaginedConclusion` on the
# substrate the round was RUN AGAINST -- for round 0 that is the live agent;
# every later round chains onto the PRIOR round's DETACHED copy, so its
# trace lands there and is discarded with it, never touching the live
# graph). `Imagination`/`ImaginedConclusion` are not tracked volatile types
# either, for the same self-inclusion reason `CollapseModel` isn't: the
# measuring apparatus's own bookkeeping is excluded from what it measures.
# ---------------------------------------------------------------------------
def _synthesize_recurrence_hypothesis(sub, obs_sample: list, round_idx: int) -> dict:
    ag_node = _agent_root_node(sub)
    nodes: list = []
    edges: list = []
    for i, on in enumerate(obs_sample):
        at = sub.node(on)["attrs"]
        sig = at.get("signature") or []
        fresh_key = [f"__fwdlook_r{round_idx}_{i}_{_v(on)}"]
        local_key = f"obs_r{round_idx}_{i}"
        nodes.append({"key": local_key, "type": "Observation",
                      "attrs": {"signature": sig, "key": fresh_key, "status": "pending"}})
        if ag_node is not None:
            edges.append({"src": _v(ag_node), "type": "observed", "tgt": local_key})
    return {"nodes": nodes, "edges": edges}


def _bounded_forward_look(agent, obs_sample: list, *, horizon: int, imagine_steps: int,
                           focus_hops: int) -> dict:
    """Run up to `horizon` bounded, reversible collapse rounds, chaining each
    round's DETACHED result into the next (never touching the live graph
    beyond round 0's sanctioned `imagine` trace). Returns
    {"counts": [before, after_round1, ...], "steps_run": total,
     "rounds_run": n}. `counts[0]` is the pre-look volatile total; a caller
    derives the growth-rate sign from the trajectory of `counts`.

    SEED-RULE REPLAY (the one place this module reaches past `imagine`'s own
    contract): `imagine`'s detached copy is built via `graph_to_dict`/
    `graph_from_dict`, which -- by that module's own documented design --
    carries graph-resident `Rule` NODES but never the separate `add_rule`
    rewrite-rule store a seed manifest's `rules` section installs into (see
    `domains/imagination.py`'s module docstring, "install such logic on the
    detached copy directly if that shape is ever needed" -- this is that
    case: `seeds/shape_decode_loop.json`'s `sd_*` rules, like every seed-
    loaded rule in this codebase, live ONLY in that store). Without a
    replay, the detached copy's `tick()` would be a rule-less no-op and
    every forward-look round would trivially "grow" by however many fresh
    Observation nodes it injects, regardless of what the REAL collapse would
    actually do -- a meaningless prediction. `export_rules`/`import_rules`
    are the sanctioned Rust primitives for exactly this (PyO3, `runners/dsl/
    src/py.rs`): export the CURRENT round's rule store, import it onto the
    fresh (rule-store-empty) detached copy, then re-tick so the REAL rules
    get a real look at the injected hypothesis. Still bounded/cheap: export/
    import is a linear copy of the (small, fixed) rule count, not graph-
    sized."""
    sub0, native0 = _resolve(agent)
    counts = [_volatile_count(sub0)]
    steps_run_total = 0
    rounds_run = 0
    cur = agent
    for r in range(max(1, horizon)):
        cur_sub, cur_native = _resolve(cur)
        hyp = _synthesize_recurrence_hypothesis(cur_sub, obs_sample, r)
        if not hyp["nodes"]:
            break
        dc = imagine(cur, focus_nodes=list(obs_sample), hypothesis=hyp,
                     steps=imagine_steps, cut_grounding=False, focus_hops=focus_hops)
        steps_run_total += dc.steps_run
        dnative = dc.detached._inner
        try:
            rules = cur_native.export_rules()
        except AttributeError:
            rules = []
        if rules and not dnative.export_rules():
            dnative.import_rules(rules)
            steps_run_total += dc.detached.tick(imagine_steps)
        counts.append(_volatile_count(dc.detached))
        rounds_run += 1
        cur = dc.detached
    return {"counts": counts, "steps_run": steps_run_total, "rounds_run": rounds_run}


# ---------------------------------------------------------------------------
# THE RETURN VALUE
# ---------------------------------------------------------------------------
@dataclass
class CollapseModelResult:
    model_node: Any                     # the minted CollapseModel NodeID (LIVE graph)
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


# ---------------------------------------------------------------------------
# THE ENTRY POINT
# ---------------------------------------------------------------------------
def predict_collapse(agent, *, horizon: int = 3, frontier_sample: int = 50,
                      focus_hops: int = 1, imagine_steps: int = 2,
                      mint_edges: int = 15) -> CollapseModelResult:
    """Predict the WHOLE graph's collapse trajectory: fixed points, volatile
    frontier, and a CONVERGED/DIVERGENT call, minted as a `CollapseModel`
    graph node (+ `fixed_point`/`volatile_frontier` edges to a bounded
    sample of each) so a follow-on agent-authored rule can read it.

    Mechanical measurement only -- no decision. Structural counts are always
    computed (cheap, O(tracked types)); the bounded forward-look
    (`_bounded_forward_look`, reusing tier-3 `imagine`) additionally runs
    ONLY if there is a non-empty volatile-Observation sample to extrapolate
    from -- on an already-settled graph (no pending Observations) the
    forward-look is skipped entirely (frontier_growth_rate stays 0.0,
    converged=True) rather than paying for a collapse round that has
    nothing to look forward from.

    `frontier_growth_rate` is the mean per-round change in the total
    volatile-frontier count across the forward-look's `counts_trajectory`
    (or 0.0 if the look did not run). `converged = frontier_growth_rate <=
    0.0` -- the frontier is predicted to shrink or hold steady vs. predicted
    to grow without bound.
    """
    sub, native = _resolve(agent)
    t0 = time.time()

    volatile = volatile_frontier(sub)
    fixed = fixed_points(agent)
    n_volatile = sum(len(v) for v in volatile.values())
    n_fixed = sum(len(v) for k, v in fixed.items() if not k.startswith("_"))

    obs_sample = volatile["Observation"][:frontier_sample]
    forward_look_ran = False
    steps_run = 0
    counts = [n_volatile]
    frontier_growth_rate = 0.0
    if obs_sample:
        look = _bounded_forward_look(agent, obs_sample, horizon=horizon,
                                      imagine_steps=imagine_steps, focus_hops=focus_hops)
        counts = look["counts"]
        steps_run = look["steps_run"]
        forward_look_ran = look["rounds_run"] > 0
        if forward_look_ran and len(counts) > 1:
            deltas = [counts[i + 1] - counts[i] for i in range(len(counts) - 1)]
            frontier_growth_rate = sum(deltas) / len(deltas)

    converged = frontier_growth_rate <= 0.0
    denom = max(1, n_volatile + n_fixed)
    residual = 0.0 if n_volatile == 0 else min(1.0, n_volatile / denom)
    runtime_s = time.time() - t0

    method = (
        "structural: one sub.nodes(<type>) scan per tracked type "
        "(Observation/CapabilityAxis/Impasse/Goal for volatility; "
        "Drive/Seed/RuleSummary for the frozen core via frozen_seed_ids_closed()) "
        "-- O(count of a handful of tracked types), not O(total graph size); "
        + (f"bounded frame-free forward-look: {len(counts) - 1} round(s) of tier-3 "
           f"imagine() on a {focus_hops}-hop closure around a {len(obs_sample)}-node "
           f"frontier sample, <= {imagine_steps} collapse steps/round"
           if forward_look_ran else
           "no forward-look run (no pending Observation to extrapolate from -- "
           "already-settled graph)")
    )

    model = sub.add_node(_MODEL_TYPE, {
        "converged": bool(converged),
        "residual": float(residual),
        "n_fixed": int(n_fixed),
        "n_volatile": int(n_volatile),
        "frontier_growth_rate": float(frontier_growth_rate),
        "horizon": int(horizon),
        "imagine_steps_budget": int(imagine_steps),
        "imagine_steps_run": int(steps_run),
        "forward_look_ran": bool(forward_look_ran),
        "counts_trajectory": list(counts),
        "runtime_s": float(runtime_s),
        "method": method,
        "ts": time.time(),
    })

    fixed_sample: list = []
    for k, v in fixed.items():
        if k.startswith("_"):
            continue
        for n in v[:mint_edges]:
            _add_edge_unchecked(native, model, _FIXED_EDGE, n, {"category": k})
            fixed_sample.append(n)

    volatile_sample: list = []
    for k, v in volatile.items():
        for n in v[:mint_edges]:
            _add_edge_unchecked(native, model, _VOLATILE_EDGE, n, {"category": k})
            volatile_sample.append(n)

    return CollapseModelResult(
        model_node=model, converged=converged, residual=residual,
        n_fixed=n_fixed, n_volatile=n_volatile,
        frontier_growth_rate=frontier_growth_rate, horizon=horizon,
        runtime_s=runtime_s, fixed_points=fixed, volatile_frontier=volatile,
        fixed_sample=fixed_sample, volatile_sample=volatile_sample,
        forward_look_ran=forward_look_ran, imagine_steps_run=steps_run,
        counts_trajectory=counts,
    )


__all__ = [
    "CollapseModelResult",
    "predict_collapse",
    "fixed_points",
    "volatile_frontier",
]
