"""self_correction — AUTONOMOUS SELF-CORRECTION: closing the predicted-
divergence loop tier 4 (`domains/collapse_model.py`) opens.

THE CAPSTONE. The 4-tier collapse-modeling stack already exists: tier 4
PREDICTS divergence (`predict_collapse` -> `CollapseModel{converged:False}`,
and the agent's OWN authored rule `predict_intervene_<tag>`
(`seeds/composer_collapse_watch_graph.json`) mints `Impasse{kind:
predicted_divergence}` from it); tier 3 IMAGINES a counterfactual, frame-free
(`domains/imagination.py`); tier 2/1 ACT. A live 10-min run once exposed a
real axis-mint runaway that a HUMAN then fixed by hand (a novelty/dedup
guard on `seeds/shape_decode_loop.json`'s `sd_mint_quantum`). This module
closes that loop AUTONOMOUSLY: given a predicted divergence, IMAGINE a
candidate fix, PREDICT whether the imagined graph converges, and — only if
the driving rule's provenance is NOT frozen — ADOPT the validated fix. A
frozen-provenance divergence can only ever be PROPOSED for human review,
never autonomously edited.

THIS IS MACHINERY, NOT (YET) THE AGENT'S OWN DECISION. Per the same
discipline `domains/collapse_model.py` and `domains/imagination.py` name in
their own module docstrings ("this module builds ONLY the mechanical
machinery... a follow-on task has the agent AUTHOR the engage/judge rules"),
`intervene_on_divergence`'s candidate-try-in-order loop is a Python
CONTROL-FLOW SCAFFOLD, not a permanent violation of CLAUDE.md's "no Python
agent decisions" rule — it is the STAND-IN a follow-on task replaces with
graph-resident decide/judge Rules once this machinery proves the primitives
compose. Every INDIVIDUAL step underneath the scaffold is either a pure
structural transform (candidate generation: mechanical JSON edits, the same
"structural substitution, no interpretation" discipline `domains/edit_ops.py`
already documents) or a call into an EXISTING gate (`domains.reflective_
faculty._rule_denylisted` — read, never re-implemented). See the module
docstring's final section, "WHAT THE FOLLOW-ON RULES SHOULD DECIDE", for the
exact seam a graph-resident Rule should replace.

THE TWO NEW PRIMITIVES
-----------------------

1. `imagine_and_check_convergence(agent, candidate) -> dict` — tier-3 (imagine
   the fix) COMPOSED WITH tier-4 (predict whether it converges), entirely
   reversible: build a DETACHED copy of the live graph (`domains.imagination.
   imagine`, the sanctioned snapshot primitive), replace the named rule(s) on
   THAT COPY ONLY with the candidate's variant JSON (or remove them, if
   `variant is None`), then run `domains.collapse_model.predict_collapse` on
   the intervened detached copy. Compares `model_before` (the real,
   live-graph prediction) against `model_after` (the imagined, intervened
   one). The live graph is never mutated beyond the two sanctioned traces
   both underlying calls already mint (`Imagination`/`ImaginedConclusion` +
   `CollapseModel`) — see `tests/test_self_correction.py::
   test_reversibility_imagine_and_check_convergence_leaves_live_graph_alone`.

2. `intervene_on_divergence(agent, ...) -> dict` — the loop: locate the
   diverging rule (an explicit `target_rule`, or a cheap structural
   inference — see `_infer_growth_rule`), generate a SMALL candidate space
   (`_default_candidates` — reuses `domains/edit_ops.py`'s appliers PLUS one
   domain-shaped candidate builder, `_dedup_identity_fix_candidate`, that
   mechanically constructs "the exact shape that fixed the axis runaway": a
   novelty/dedup identity check keyed on a ROUND-INVARIANT field
   (`signature`) instead of a per-instance one (`key`), paired with swapping
   the minting effect from `add_node` to `add_node_if_absent` so a same-tick
   duplicate match can't double-mint), try each via
   `imagine_and_check_convergence` until one CONVERGES, then — SAFETY
   BOUNDARY — check `domains.reflective_faculty._rule_denylisted` (the REAL,
   existing adoption veto `perform_adoptions` already enforces) on every rule
   the winning candidate touches: if ANY is denylisted (frozen-core
   provenance, or unknown provenance — the same "deny by default" `_rule_
   denylisted` itself documents), the fix is NEVER applied to the live
   graph; instead a `SelfCorrectionProposal` node (the human-review record,
   carrying the full variant JSON) is minted and a rung-5 `Impasse{kind:
   human}` is raised (the SAME idiom `domains.reflective_faculty.
   self_extend_ladder` already uses for its own last-resort escalation) —
   honest: the agent found a fix but is not ALLOWED to apply it itself. If
   NONE are denylisted, the fix is adopted directly on the live graph
   (mechanical `remove_rule`/`add_rule`, mirroring `perform_adoptions`'s own
   tombstone-and-replace shape without borrowing its Experiment/SeedDelta
   apparatus — this module doesn't have a dispatched, judged Experiment to
   fold back; it has a validated imagined fix, a different provenance for
   the SAME kind of act) and `predict_collapse` is run once more on the
   now-patched live graph to CONFIRM convergence.

WHY NOT ROUTE THROUGH `perform_adoptions` DIRECTLY. `domains.reflective_
faculty.perform_adoptions` folds back a SUPPORTED self-experiment's variant,
keyed on an `Experiment`+`SeedDelta` shape a DISPATCHED CHILD process
produced and a judge rule marked `adopt_ready` — a different, heavier
apparatus (`domains/experiment_dispatch.py`) built for a different
provenance (a child's own judged outcome). Self-correction's fix has its OWN
provenance: an in-process imagined validation, not a dispatched experiment.
Rather than fabricate a fake `Experiment`/`SeedDelta` pair just to satisfy
that function's shape (a more fragile coupling than reusing its GATE), this
module calls the SAME real veto (`_rule_denylisted`) `perform_adoptions`
itself calls, and performs the identical mechanical `remove_rule`/`add_rule`
tombstone-and-replace `perform_adoptions` performs — reusing the gate at its
own level, per CAUTIONS' explicit permission ("`perform_adoptions`... or
`commit_imagination`" — either existing gate qualifies).

SAFETY BOUNDARY IN ONE SENTENCE: the agent self-corrects what it's ALLOWED
to touch (denylist says no); it can only PROPOSE a fix to its frozen core,
never apply one — enforced by calling the real veto, never re-implementing
it, so a change to `_rule_denylisted` (or the frozen-seed closure it reads)
automatically tightens or loosens this module too.

WHAT THE FOLLOW-ON RULES SHOULD DECIDE (vs. what this machinery already
does): this module already does every MECHANICAL step (imagine, predict,
generate candidates, check the veto, adopt-or-propose). What remains a bare
Python control-flow scaffold, and should become graph-resident Rules in the
follow-on cognition task:
  - WHICH candidate is "best" when more than one converges (currently: first
    in list order — a Rule could instead Argmax over a genuine cost/risk
    Term, the same shape `domains.reflective_faculty._compose_structural_
    variant` already uses for structural-variant selection);
  - WHETHER to even ATTEMPT self-correction on a given predicted-divergence
    Impasse (currently: the daemon hook tries every unresolved one it sees
    — a Rule could gate this on drive/priority, the same arbitration
    `seeds/composer_escalation_gate_graph.json` already does for other
    tier-3/tier-4 hooks);
  - HOW MANY candidates are "enough" before escalating (currently: the
    fixed, small `_default_candidates` list) — a Rule could grow the search
    only when the standing budget allows it.
This module's contract (`imagine_and_check_convergence` returns a plain,
matchable-shape dict; `intervene_on_divergence`'s mechanical sub-steps are
each independently callable) is deliberately factored so a Rule can drive
the SAME primitives without this module's own orchestration loop once that
follow-on task lands.
"""
from __future__ import annotations

import copy as _copy
import hashlib as _hashlib
import json as _json
import time as _time
import uuid as _uuid
from typing import Any, Optional

from domains import edit_ops
from domains.collapse_model import CollapseModelResult, predict_collapse
from domains.imagination import imagine
from domains.reflective_faculty import _rule_denylisted

_PROPOSAL_TYPE = "SelfCorrectionProposal"
_ADOPTION_TYPE = "SelfCorrectionAdoption"
_MAX_DEFAULT_SWAP_VARIANTS = 4


# ---------------------------------------------------------------------------
# duck-typed (substrate, native) resolution -- the SAME shape domains/
# collapse_model.py / domains/imagination.py use, duplicated locally (not
# imported) so this module carries no coupling to a file under concurrent
# edit -- the established precedent both of those modules already set.
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
    from `domains.reflective_faculty._agent_root_node` / `domains.
    collapse_model._agent_root_node` (same shape, same reasoning). Returns
    None if absent."""
    for n in sub.nodes("Agent"):
        at = sub.node(n)["attrs"]
        if not at.get("is_class"):
            return n
    return None


def _tag() -> str:
    return _uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# (1) IMAGINE A FIX, PREDICT WHETHER IT CONVERGES -- tier-3 composed with
# tier-4, entirely reversible.
# ---------------------------------------------------------------------------
def imagine_and_check_convergence(agent, candidate: dict, *, model_before: Optional[CollapseModelResult] = None,
                                   horizon: int = 3, frontier_sample: int = 50,
                                   focus_hops: int = 1, imagine_steps: int = 2,
                                   experiment_focus_nodes: Optional[list] = None,
                                   snapshot_backend: str = "serialization",
                                   _force_full_noop_readout: bool = False,
                                   _force_full_graph_readout: bool = False,
                                   _process_forked: bool = False,
                                   _prediction_snapshot_backend: Optional[str] = None,
                                   _snapshot_handle=None,
                                   _measure_phases: bool = False,
                                   _native_rule_patch: bool = True,
                                   record_trace: bool = True) -> dict:
    """Apply `candidate` -- `{"label": str, "rules": {rule_name: variant_rule_
    dict_or_None, ...}}` -- IN TIER-3 IMAGINATION (a detached copy of the
    live graph via `domains.imagination.imagine`) and PREDICT (tier-4,
    `domains.collapse_model.predict_collapse`) whether the intervened,
    detached graph converges. `variant_rule_dict` replaces the named rule
    (mechanical `remove_rule` + `add_rule` on the DETACHED copy's own native
    object only); `None` removes it without replacement (a valid, if blunt,
    candidate shape).

    Returns `{"converges": bool, "model_before": CollapseModelResult (the
    REAL, live prediction), "model_after": CollapseModelResult (the
    IMAGINED, intervened prediction -- minted on the detached copy, which is
    discarded with it), "imagined": DetachedCollapse, "candidate": dict,
    "applied": {rule_name: variant_name_or_None, ...} (only the rules that
    were actually FOUND and swapped -- a `rules` entry naming a rule that
    isn't currently active is silently skipped, same "honest, never
    fabricate an edit that isn't there" discipline `domains/edit_ops.py`'s
    appliers document), "inert": bool (True if NOTHING in `candidate` was
    actually applicable -- a caller should treat an inert candidate as
    untried, not as "tried and failed")}.

    REVERSIBILITY: the only mutations this function makes to the LIVE graph
    are the two SANCTIONED traces its two underlying calls already mint --
    `predict_collapse(agent, ...)` for `model_before` (a `CollapseModel`
    node, the same durable-measurement trace `tests/test_collapse_model.py`
    already exercises) and `imagine(agent, ...)` for the detached snapshot
    (an `Imagination`/`ImaginedConclusion` trace, the same reversible trace
    `tests/test_imagination.py::test_reversibility_*` already proves). The
    candidate's rule swap touches ONLY the detached copy's own native
    object -- `imagine()` copies `agent`'s own rule store into the detached
    substrate; candidate edits never touch the live store."""
    sub, native = _resolve(agent)
    if snapshot_backend == "process_in_place" and not _process_forked:
        raise RuntimeError("process_in_place requires an isolated forked child")
    model_before = model_before or predict_collapse(
        agent, horizon=horizon, frontier_sample=frontier_sample,
        focus_hops=focus_hops, imagine_steps=imagine_steps,
        snapshot_backend=snapshot_backend, _process_forked=_process_forked,
        _force_full_graph_readout=_force_full_graph_readout,
        _measure_phases=_measure_phases,
        record_trace=record_trace)

    rules_patch = candidate.get("rules") or {}
    # (1) SNAPSHOT (real graph, real rules, zero collapse steps yet -- a
    # clean, reversible base to intervene on before predicting).
    import time
    phase_started = time.perf_counter_ns() if _measure_phases else 0
    dc0 = imagine(agent, hypothesis=None, steps=0, cut_grounding=False,
                  focus_nodes=experiment_focus_nodes, focus_hops=focus_hops,
                  snapshot_backend=snapshot_backend,
                  _force_full_noop_readout=_force_full_noop_readout,
                  _force_full_graph_readout=_force_full_graph_readout,
                  _process_forked=_process_forked,
                  _snapshot_handle=_snapshot_handle,
                  _measure_phases=_measure_phases,
                  record_trace=record_trace)
    snapshot_ms = ((time.perf_counter_ns() - phase_started) / 1_000_000
                   if _measure_phases else None)
    dnative = dc0.detached._inner

    # (2) APPLY THE CANDIDATE -- detached copy only.
    applied: dict = {}
    patch_started = time.perf_counter_ns() if _measure_phases else 0
    if _native_rule_patch:
        replace_by_name = getattr(dnative, "replace_active_rule_by_name", None)
        if replace_by_name is None:
            raise RuntimeError("native active-rule patch support is unavailable; rebuild the Rust engine")
        for name, variant in rules_patch.items():
            if replace_by_name(name, variant):
                applied[name] = variant.get("name") if isinstance(variant, dict) else None
    else:
        for name, variant in rules_patch.items():
            exported = dnative.export_rules()
            idx = next((i for i, r in enumerate(exported)
                        if isinstance(r, dict) and r.get("active", True) and r.get("name") == name), None)
            if idx is None:
                continue
            dnative.remove_rule(idx)
            if variant is not None:
                dnative.add_rule(variant)
            applied[name] = variant.get("name") if isinstance(variant, dict) else None
    candidate_patch_ms = ((time.perf_counter_ns() - patch_started) / 1_000_000
                          if _measure_phases else None)

    # (3) PREDICT on the intervened, detached copy.
    prediction_started = time.perf_counter_ns() if _measure_phases else 0
    model_after = predict_collapse(dc0.detached, horizon=horizon, frontier_sample=frontier_sample,
                                    focus_hops=focus_hops, imagine_steps=imagine_steps,
                                    snapshot_backend=(_prediction_snapshot_backend or snapshot_backend),
                                    _force_full_graph_readout=_force_full_graph_readout,
                                    _process_forked=_process_forked,
                                    _measure_phases=_measure_phases)
    model_after_ms = ((time.perf_counter_ns() - prediction_started) / 1_000_000
                      if _measure_phases else None)

    result = {
        "converges": bool(model_after.converged),
        "model_before": model_before,
        "model_after": model_after,
        "imagined": dc0,
        "candidate": candidate,
        "applied": applied,
        "inert": len(applied) == 0,
    }
    if _measure_phases:
        result["phase_timings_ms"] = {
            "branch_snapshot_and_setup": snapshot_ms,
            "candidate_rule_patch": candidate_patch_ms,
            "model_after_prediction": model_after_ms,
            "initial_branch_internal": dc0.phase_timings_ms,
            "prediction_internal": model_after.phase_timings_ms,
            "forward_look_branch_internal": model_after.forward_look_phase_records,
        }
    return result


def imagine_candidate_batch(agent, candidates: list[dict], *,
                            horizon: int = 3, frontier_sample: int = 50,
                            focus_hops: int = 1, imagine_steps: int = 2,
                            snapshot_backend: str = "native_full_copy",
                            experiment_focus_nodes: Optional[list] = None,
                            _force_full_graph_readout: bool = False,
                            _measure_phases: bool = False,
                            record_trace: bool = True) -> dict:
    """Evaluate candidates against one fixed primary revision.

    Compute the baseline once, suppress per-candidate primary traces, and
    reuse that baseline for every branch. A before/after native semantic
    revision verifies that the primary graph and rule store remained unchanged. This amortizes
    baseline prediction but does not remove the selected backend's branch
    copy cost.
    """
    import time

    _sub, native = _resolve(agent)
    revision = getattr(native, "experiment_graph_rule_revision", None)
    if revision is None:
        raise RuntimeError(
            "native graph/rule revision support is unavailable; rebuild the Rust engine")

    def state_revision() -> tuple[int, int, int]:
        graph_version, gamma_epoch, rule_slots = revision()
        return int(graph_version), int(gamma_epoch), int(rule_slots)

    baseline_started = time.perf_counter_ns()
    baseline = predict_collapse(
        agent, horizon=horizon, frontier_sample=frontier_sample,
        focus_hops=focus_hops, imagine_steps=imagine_steps,
        snapshot_backend=snapshot_backend,
        _force_full_graph_readout=_force_full_graph_readout,
        _measure_phases=_measure_phases,
        record_trace=record_trace)
    baseline_ms = (time.perf_counter_ns() - baseline_started) / 1_000_000
    revision_started = time.perf_counter_ns()
    baseline_revision = state_revision()
    baseline_revision_ms = (time.perf_counter_ns() - revision_started) / 1_000_000
    reusable_snapshot = None
    reusable_snapshot_ms = 0.0
    if snapshot_backend == "native_reusable_snapshot":
        snapshot_started = time.perf_counter_ns()
        reusable_snapshot = _sub.snapshot()
        reusable_snapshot_ms = (time.perf_counter_ns() - snapshot_started) / 1_000_000
        if tuple(reusable_snapshot.source_revision) != baseline_revision:
            raise RuntimeError("candidate batch snapshot does not match its fixed source revision")
    results = []
    candidate_ms = []
    for candidate in candidates:
        candidate_started = time.perf_counter_ns()
        results.append(imagine_and_check_convergence(
            agent, candidate, model_before=baseline, horizon=horizon,
            frontier_sample=frontier_sample, focus_hops=focus_hops,
            imagine_steps=imagine_steps, snapshot_backend=snapshot_backend,
            experiment_focus_nodes=experiment_focus_nodes,
            _force_full_graph_readout=_force_full_graph_readout,
            _snapshot_handle=reusable_snapshot,
            _measure_phases=_measure_phases,
            record_trace=False))
        candidate_ms.append((time.perf_counter_ns() - candidate_started) / 1_000_000)
    revision_started = time.perf_counter_ns()
    final_revision = state_revision()
    final_revision_ms = (time.perf_counter_ns() - revision_started) / 1_000_000
    if final_revision != baseline_revision:
        raise RuntimeError("candidate batch changed the primary graph or native rules")
    return {"model_before": baseline, "results": results,
            "primary_graph_and_rules_unchanged_during_batch": True,
            "candidate_count": len(results),
            "timing_components_ms": {
                "baseline_prediction": baseline_ms,
                "baseline_revision_check": baseline_revision_ms,
                "reusable_snapshot_capture": reusable_snapshot_ms,
                "candidate_rehearsals": candidate_ms,
                "final_revision_check": final_revision_ms,
            }}


# ---------------------------------------------------------------------------
# candidate generation -- mechanical, structural, small and honest.
# ---------------------------------------------------------------------------
def _swap_var_attr_key(tree: Any, var_name: str, old_key: str, new_key: str) -> None:
    """Mutate IN PLACE: every `{"type":"Attr","node":{"type":"Var","name":
    var_name},"key":old_key}` reachable inside `tree` becomes `key:new_key`.
    The SAME "structural substitution, no interpretation" discipline
    `domains/edit_ops.py`'s appliers document, scoped by (var, key) pair so
    it never touches an unrelated Attr read that happens to share a key
    name. Deliberately broader than `edit_ops.apply_swap_term_leaf`'s
    effects-only scope (this module's own candidate genuinely needs to swap
    a `where`-clause identity check too) -- kept HERE, not added to
    edit_ops.py, per this task's own file boundaries."""
    if isinstance(tree, dict):
        node = tree.get("node")
        if (tree.get("type") == "Attr" and tree.get("key") == old_key
                and isinstance(node, dict) and node.get("type") == "Var" and node.get("name") == var_name):
            tree["key"] = new_key
            return
        for v in tree.values():
            _swap_var_attr_key(v, var_name, old_key, new_key)
    elif isinstance(tree, list):
        for v in tree:
            _swap_var_attr_key(v, var_name, old_key, new_key)


def _find_identity_eq(tree: Any) -> Optional[dict]:
    """Find the first `{"type":"Eq","a":Attr(<existing>,'capability_keys'),
    "b":Attr(<var>,<key>)}` node reachable inside `tree` -- the SHAPE `seeds/
    shape_decode_loop.json`'s `sd_mint_quantum` novelty guard / `sd_dedup_
    existing` mirror both carry (an "is this residual already covered by an
    existing induced axis" identity check). Returns the Eq node itself (a
    reference INTO a deep-copied tree the caller owns) or None if the rule
    carries no such check at all -- the candidate this powers is simply
    inapplicable to a rule shaped differently, reported honestly via None,
    never fabricated."""
    if isinstance(tree, dict):
        if tree.get("type") == "Eq":
            a, b = tree.get("a"), tree.get("b")
            if (isinstance(a, dict) and a.get("type") == "Attr" and a.get("key") == "capability_keys"
                    and isinstance(b, dict) and b.get("type") == "Attr"
                    and isinstance(b.get("node"), dict) and b["node"].get("type") == "Var"):
                return tree
        for v in tree.values():
            found = _find_identity_eq(v)
            if found is not None:
                return found
    elif isinstance(tree, list):
        for v in tree:
            found = _find_identity_eq(v)
            if found is not None:
                return found
    return None


def _dedup_identity_fix_candidate(rule: dict, new_name: str) -> Optional[dict]:
    """THE CANDIDATE NAMED IN THE TASK: "an add-a-guard-shaped candidate --
    the exact shape that fixed the axis runaway: a novelty/dedup where-
    clause". `sd_mint_quantum`'s real novelty guard (added 2026-07-03,
    `seeds/shape_decode_loop.json`) already checks "does an induced axis
    already carry this observation's identity" -- but keys that identity on
    `Observation.key`, which `domains.collapse_model`'s own bounded forward-
    look mechanically re-tags FRESH every round (`_synthesize_recurrence_
    hypothesis`, simulating continuous per-frame perception re-observing a
    STRUCTURALLY similar residual under a nominally-new identity -- see that
    module's docstring). This candidate re-keys the SAME identity check onto
    `signature` (the field the forward-look copies VERBATIM every round,
    the genuinely round-invariant identity for "the same residual shape")
    and swaps the minting effect from `add_node` to `add_node_if_absent` (so
    two same-tick matches sharing that identity can't double-mint --
    verified empirically: without this swap, a live pending Observation and
    its own round-0 synthetic clone -- both unprocessed, both matching in
    the SAME fixpoint pass -- independently mint two axes for one shape
    before either sees the other's effect).

    Returns None (honest, inert) if `rule` carries no `capability_keys`
    identity check at all (see `_find_identity_eq`), if that check is
    ALREADY signature-keyed (nothing to fix), or if `rule` mints no
    CapabilityAxis carrying `capability_keys` at all (nothing for the
    effect-side swap to act on) -- this candidate is scoped to rules shaped
    like `sd_mint_quantum`, not a generic patch."""
    eq = _find_identity_eq(rule.get("where"))
    if eq is None:
        return None
    b = eq["b"]
    match_var, match_key = b["node"]["name"], b["key"]
    if match_key == "signature":
        return None
    has_mint_effect = any(
        isinstance(eff, list) and len(eff) >= 4 and eff[0] == "add_node"
        and isinstance(eff[3], dict) and "capability_keys" in eff[3]
        for eff in (rule.get("effects") or [])
    )
    if not has_mint_effect:
        return None
    variant = _copy.deepcopy(rule)
    variant["name"] = new_name
    variant.pop("active", None)
    _swap_var_attr_key(variant.get("where"), match_var, match_key, "signature")
    _swap_var_attr_key(variant.get("effects"), match_var, match_key, "signature")
    for eff in variant.get("effects") or []:
        if isinstance(eff, list) and len(eff) >= 4 and eff[0] == "add_node" \
                and isinstance(eff[3], dict) and "capability_keys" in eff[3]:
            eff[0] = "add_node_if_absent"
            eff[3] = {k: v for k, v in eff[3].items() if k in ("capability_keys", "induced")}
    return variant


def _dedup_mirror_fix_candidate(rule: dict, new_name: str) -> Optional[dict]:
    """The MIRROR half of `_dedup_identity_fix_candidate` -- a companion rule
    (like `sd_dedup_existing`) that carries the SAME identity check but no
    minting effect (it terminates a genuine duplicate instead of minting
    it). Only the `where`-side re-key is needed; there is no minting effect
    to touch. None (inert) under the same conditions as its mint-side twin."""
    eq = _find_identity_eq(rule.get("where"))
    if eq is None:
        return None
    b = eq["b"]
    match_var, match_key = b["node"]["name"], b["key"]
    if match_key == "signature":
        return None
    variant = _copy.deepcopy(rule)
    variant["name"] = new_name
    variant.pop("active", None)
    _swap_var_attr_key(variant.get("where"), match_var, match_key, "signature")
    return variant


def _recurrence_offer_idempotence_candidate(rule: dict, new_name: str) -> Optional[dict]:
    """Restore the recurrence ledger's authored one-offer invariant when its
    `mrl_offer_due_once` rule has lost the negative-existence guard. This is
    a second task-shaped repair family, scoped by exact rule identity and
    structural absence of `candidate.has_mint_offer`; it does not rewrite an
    already guarded rule or guess at other minting semantics."""
    if rule.get("name") != "mrl_offer_due_once":
        return None
    where = rule.get("where")
    if not isinstance(where, dict) or where.get("type") != "And":
        return None
    items = where.get("items")
    if not isinstance(items, list):
        return None
    def is_offer_guard(item: dict) -> bool:
        arg = item.get("arg") or {}
        source = arg.get("source") or {}
        node = source.get("node") or {}
        return (item.get("type") == "Not" and arg.get("type") == "Exists"
                and source.get("type") == "Neighbours"
                and source.get("edge_type") == "has_mint_offer"
                and node.get("type") == "Var" and node.get("name") == "candidate")
    if any(isinstance(item, dict) and is_offer_guard(item) for item in items):
        return None
    guard = {
        "type": "Not",
        "arg": {
            "type": "Exists",
            "source": {"type": "Neighbours",
                       "node": {"type": "Var", "name": "candidate"},
                       "edge_type": "has_mint_offer"},
            "var_name": "offer",
            "predicate": {"type": "Lit", "value": True},
        },
    }
    variant = _copy.deepcopy(rule)
    variant["name"] = new_name
    variant.pop("active", None)
    variant["where"]["items"].append(guard)
    return variant


def _recurrence_episode_scope_guard_candidate(rule: dict, new_name: str) -> Optional[dict]:
    """A plausible but narrower-cost alternative for recurrence minting:
    suppress every offer after the first offer in an episode. This is useful
    as a competing hypothesis, not as a known-good fix when an episode has
    multiple due candidates; its task utility must be judged by the caller."""
    if rule.get("name") != "mrl_offer_due_once":
        return None
    where = rule.get("where")
    if not isinstance(where, dict) or where.get("type") != "And":
        return None
    items = where.get("items")
    if not isinstance(items, list):
        return None
    def is_guard(item: dict, edge_type: str, var: str) -> bool:
        arg = item.get("arg") or {}
        source = arg.get("source") or {}
        node = source.get("node") or {}
        return (item.get("type") == "Not" and arg.get("type") == "Exists"
                and source.get("type") == "Neighbours"
                and source.get("edge_type") == edge_type
                and node.get("type") == "Var" and node.get("name") == var)
    if any(isinstance(item, dict) and is_guard(item,"has_mint_offer","episode") for item in items):
        return None
    variant = _copy.deepcopy(rule)
    variant["name"] = new_name
    variant.pop("active", None)
    variant["where"]["items"].append({
        "type":"Not","arg":{"type":"Exists",
            "source":{"type":"Neighbours","node":{"type":"Var","name":"episode"},
                      "edge_type":"has_mint_offer"},
            "var_name":"offer","predicate":{"type":"Lit","value":True}}})
    return variant


def _find_mirror_rule(native, target_name: str) -> Optional[dict]:
    """Heuristic companion-rule search: the first OTHER active rule whose
    `where` also carries the `_find_identity_eq` shape (a rule keying a
    decision off "does a matching induced axis already exist"). This finds
    `sd_dedup_existing` from `sd_mint_quantum` without hardcoding either
    name. Best-effort -- returns None if no companion is found, in which
    case `_dedup_identity_fix_candidate` alone (mint-side only) is still a
    coherent, if narrower, candidate."""
    for r in native.export_rules():
        if not (isinstance(r, dict) and r.get("active", True)):
            continue
        if r.get("name") == target_name:
            continue
        if _find_identity_eq(r.get("where")) is not None:
            return r
    return None


def _default_candidates(native, target_rule_name: str) -> list:
    """Build a SMALL, honest candidate space for `target_rule_name`: REUSE
    `domains/edit_ops.py`'s structural appliers (flip_comparison /
    drop_match_edge / add_match_guard -- each independently reported inert
    (excluded) when structurally inapplicable to this specific rule, never
    faked) PLUS the domain-shaped `_dedup_identity_fix_candidate` (+ its
    mirror-rule companion, when one is found). Every candidate is
    `{"label": str, "rules": {rule_name: variant_or_None, ...}}`, the exact
    shape `imagine_and_check_convergence` consumes."""
    exported = native.export_rules()
    rule = next((r for r in exported if isinstance(r, dict) and r.get("active", True)
                 and r.get("name") == target_rule_name), None)
    if rule is None:
        return []
    tag = _tag()
    candidates: list = []

    dedup_fix = _dedup_identity_fix_candidate(rule, f"{target_rule_name}_scfix_{tag}")
    if dedup_fix is not None:
        bundle = {target_rule_name: dedup_fix}
        mirror = _find_mirror_rule(native, target_rule_name)
        if mirror is not None:
            mirror_fix = _dedup_mirror_fix_candidate(mirror, f"{mirror['name']}_scfix_{tag}")
            if mirror_fix is not None:
                bundle[mirror["name"]] = mirror_fix
        candidates.append({"label": "dedup_identity_fix",
                           "outcome_class": "idempotent_mint_guard",
                           "rules": bundle})

    recurrence_fix = _recurrence_offer_idempotence_candidate(
        rule, f"{target_rule_name}_scoffer_{tag}")
    if recurrence_fix is not None:
        candidates.append({"label": "dedup_identity_fix",
                           "outcome_class": "idempotent_mint_guard",
                           "rules": {target_rule_name: recurrence_fix}})
    episode_guard = _recurrence_episode_scope_guard_candidate(
        rule, f"{target_rule_name}_scoffer_episode_{tag}")
    if episode_guard is not None:
        candidates.append({"label":"episode_scoped_offer_guard",
                           "outcome_class":"episode_scoped_idempotence",
                           "rules":{target_rule_name:episode_guard}})

    flip = edit_ops.apply_flip_comparison(rule, f"{target_rule_name}_scflip_{tag}")
    if flip is not None:
        candidates.append({"label": "flip_comparison", "rules": {target_rule_name: flip}})

    drop = edit_ops.apply_drop_match_edge(rule, 0, f"{target_rule_name}_scdrop_{tag}")
    if drop is not None:
        candidates.append({"label": "drop_match_edge", "rules": {target_rule_name: drop}})

    match = rule.get("match") or []
    if match and isinstance(match[0], (list, tuple)) and match[0]:
        node_var = match[0][0]
        guard = edit_ops.apply_add_match_guard(rule, node_var, "self_correction_probe_never_true", 1,
                                                f"{target_rule_name}_scguard_{tag}")
        candidates.append({"label": "add_match_guard(control)", "rules": {target_rule_name: guard}})

    # Explore a small deterministic set of substitutions among attribute
    # keys already read by the effect. Keep the default rehearsal budget
    # finite; broader pairwise search requires an explicit caller budget.
    effect_keys = [key for key, _count in edit_ops.find_attr_keys(rule.get("effects"))]
    n_swaps = 0
    for old_key in effect_keys:
        for new_key in effect_keys:
            if old_key == new_key:
                continue
            swap = edit_ops.apply_swap_term_leaf(
                rule, old_key, new_key,
                f"{target_rule_name}_scswap_{tag}_{n_swaps}")
            if swap is None:
                continue
            candidates.append({
                "label": f"swap_term_leaf:{old_key}->{new_key}",
                "rules": {target_rule_name: swap},
            })
            n_swaps += 1
            if n_swaps >= _MAX_DEFAULT_SWAP_VARIANTS:
                break
        if n_swaps >= _MAX_DEFAULT_SWAP_VARIANTS:
            break

    return candidates


# ---------------------------------------------------------------------------
# locate the diverging locus -- cheap, structural (mirrors domains/
# collapse_model.py's own tractability discipline: a handful of scans, no
# graph-size-proportional search).
# ---------------------------------------------------------------------------
def _rule_minting(native, node_type: str) -> Optional[str]:
    """First ACTIVE rule whose effects mint `node_type` (`add_node` /
    `add_node_if_absent`), or None."""
    for r in native.export_rules():
        if not (isinstance(r, dict) and r.get("active", True)):
            continue
        for eff in (r.get("effects") or []):
            if (isinstance(eff, (list, tuple)) and len(eff) >= 3
                    and eff[0] in ("add_node", "add_node_if_absent") and eff[2] == node_type):
                return r.get("name")
    return None


def _infer_growth_rule(native, model_before: CollapseModelResult) -> Optional[str]:
    """Which rule is driving the growth? A cheap, honest heuristic: rank the
    TRACKED categories in `model_before.volatile_frontier` by current count
    (most-volatile first -- `Observation` is nearly always the first to show
    a raw count, since a growth pathology usually starts as pending
    Observations arriving faster than they resolve, but the type that is
    actually EXPLODING under the forward-look, e.g. `CapabilityAxis`, may
    still read 0 on the live graph's pre-forward-look snapshot -- so this
    tries every tracked category, in severity order, not just the single
    largest one) and, for each, look for a MINTING rule (`_rule_minting`).
    Returns the first rule found across that ranked search, or None (never
    guesses) if no tracked category has a minting rule at all -- a caller
    without an inferred target should require an explicit `target_rule` or
    escalate honestly, never proceed on a fabricated guess."""
    vf = model_before.volatile_frontier
    ranked = sorted(vf.keys(), key=lambda k: -len(vf[k]))
    for node_type in ranked:
        name = _rule_minting(native, node_type)
        if name is not None:
            return name
    return None


# ---------------------------------------------------------------------------
# escalation (rung-5, the SAME idiom domains.reflective_faculty.self_extend_
# ladder already uses) + the human-review proposal record.
# ---------------------------------------------------------------------------
def _raise_human_impasse(agent, *, gap: str, note: str, extra: Optional[dict] = None) -> Any:
    sub, native = _resolve(agent)
    attrs = {"kind": "human", "to": "creator", "resolved": 0.0, "gap": gap, "note": note[:2000]}
    if extra:
        attrs.update(extra)
    imp = sub.add_node("Impasse", attrs)
    ag_node = _agent_root_node(sub)
    if ag_node is not None:
        _add_edge_unchecked(native, ag_node, "raises", imp)
    return imp


def _mint_proposal(agent, *, target_rule: str, candidate: dict, reasons: list,
                    model_before: CollapseModelResult, model_after: CollapseModelResult) -> Any:
    """Mint the human-review record: everything a human needs to see to
    approve or reject the SAME fix the agent already validated in
    imagination (variant rule JSON, which rule(s) it touches, why the
    denylist refused, and both collapse-model predictions). Never applied
    automatically -- `status` starts and stays `pending_human_approval`;
    nothing in this module transitions it."""
    sub, native = _resolve(agent)
    rules_patch = candidate.get("rules") or {}
    node = sub.add_node(_PROPOSAL_TYPE, {
        "kind": "self_correction_frozen_fix",
        "target_rule": target_rule,
        "candidate_label": candidate.get("label"),
        "rule_names": sorted(rules_patch.keys()),
        "variant_rule_json": _json.dumps(rules_patch),
        "denylist_reasons": _json.dumps([{"rule": n, "reason": r} for n, r in reasons]),
        "status": "pending_human_approval",
        "model_before": _v(model_before.model_node),
        "model_after_converges": bool(model_after.converged),
        "ts": _time.time(),
    })
    ag_node = _agent_root_node(sub)
    if ag_node is not None:
        _add_edge_unchecked(native, ag_node, "escalated_self_correction", node)
    if sub.has_node(model_before.model_node):
        _add_edge_unchecked(native, model_before.model_node, "proposes_fix", node)
    return node


# ---------------------------------------------------------------------------
# ADOPTION -- the mechanical fold-back, LIVE graph, gated by the veto ONLY
# (this module's own caller checks the veto BEFORE calling this; this
# function itself performs no gating, mirroring domains.reflective_faculty.
# perform_adoptions's own division: the veto is checked once, up front, not
# re-derived per mutation).
# ---------------------------------------------------------------------------
def _adopt_rule_bundle(agent, rules_patch: dict) -> list:
    """Mechanically fold every `{name: variant_or_None}` pair in
    `rules_patch` into the LIVE graph: `remove_rule` the named active rule
    (Rust tombstones it -- stable index, recoverable) + `add_rule` the
    variant (skipped if `variant is None` -- a bare removal), mint a
    `SelfCorrectionAdoption{rule_removed, rule_added, original_rule_json,
    ...}` record per pair (the SAME shape `domains.reflective_faculty.
    perform_adoptions`'s own `Adoption` record carries, so a human or a
    follow-on revert faculty can read either uniformly). Idempotent per call
    (a name not currently active is silently skipped, never invented)."""
    sub, native = _resolve(agent)
    out: list = []
    for name, variant in rules_patch.items():
        exported = native.export_rules()
        idx = next((i for i, r in enumerate(exported)
                    if isinstance(r, dict) and r.get("active", True) and r.get("name") == name), None)
        if idx is None:
            continue
        original_json = dict(exported[idx])
        original_json.pop("active", None)
        native.remove_rule(idx)
        new_idx = native.add_rule(variant) if variant is not None else None
        rec = sub.add_node(_ADOPTION_TYPE, {
            "rule_removed": name,
            "rule_added": (variant.get("name") if isinstance(variant, dict) else ""),
            "removed_idx": int(idx), "added_idx": (int(new_idx) if new_idx is not None else -1),
            "original_rule_json": _json.dumps(original_json), "ts": _time.time(),
        })
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# THE LOOP
# ---------------------------------------------------------------------------
def intervene_on_divergence(agent, *, target_rule: Optional[str] = None,
                             candidates: Optional[list] = None,
                             model_before: Optional[CollapseModelResult] = None,
                             horizon: int = 3, frontier_sample: int = 50,
                             focus_hops: int = 1, imagine_steps: int = 2) -> dict:
    """PREDICT (or accept a given) divergence -> GENERATE a small candidate
    space on the diverging rule -> IMAGINE each -> ADOPT the first validated
    (converging) one, UNLESS its provenance is frozen, in which case escalate
    with a human-review proposal and touch nothing live.

    Returns `{"chosen": label_or_None, "adopted": bool, "escalated": bool,
    "candidates_tried": [...], "target_rule": name_or_None, "model_before":
    CollapseModelResult, ...}` -- plus, depending on outcome: `"reason"`
    (already converged, nothing to do), `"impasse"` + `"proposal"` (frozen
    denial), or `"adoptions"` + `"model_after_candidate"` + `"model_final"`
    (autonomous success)."""
    sub, native = _resolve(agent)
    model_before = model_before or predict_collapse(
        agent, horizon=horizon, frontier_sample=frontier_sample,
        focus_hops=focus_hops, imagine_steps=imagine_steps)

    if model_before.converged:
        return {"chosen": None, "adopted": False, "escalated": False,
                "reason": "already converged -- nothing to intervene on",
                "candidates_tried": [], "model_before": model_before, "target_rule": None}

    resolved_target = target_rule or _infer_growth_rule(native, model_before)
    if resolved_target is None:
        node = _raise_human_impasse(
            agent, gap="self_correction_locate_rule",
            note="predicted divergence but could not structurally locate a driving rule "
                 "(no add_node/add_node_if_absent effect matches the dominant volatile category)")
        return {"chosen": None, "adopted": False, "escalated": True, "impasse": node,
                "candidates_tried": [], "model_before": model_before, "target_rule": None}

    cand_list = candidates if candidates is not None else _default_candidates(native, resolved_target)
    tried: list = []
    chosen: Optional[dict] = None
    for cand in cand_list:
        if not cand.get("rules"):
            tried.append({"label": cand.get("label"), "candidate_digest": _candidate_digest(cand),
                          "rank_trace": cand.get("_self_correction_rank_trace"),
                          "inert": True, "converges": False, "selected": False})
            continue
        check = imagine_and_check_convergence(
            agent, cand, model_before=model_before, horizon=horizon, frontier_sample=frontier_sample,
            focus_hops=focus_hops, imagine_steps=imagine_steps)
        tried.append({"label": cand.get("label"), "candidate_digest": _candidate_digest(cand),
                      "rank_trace": cand.get("_self_correction_rank_trace"),
                      "inert": check["inert"], "converges": check["converges"],
                      "selected": False, "model_after": check["model_after"]})
        if check["converges"] and not check["inert"] and chosen is None:
            tried[-1]["selected"] = True
            chosen = {"candidate": cand, "check": check}
            break

    if chosen is None:
        node = _raise_human_impasse(
            agent, gap="self_correction_no_converging_candidate",
            note=f"predicted divergence on rule {resolved_target!r} but none of "
                 f"{len(cand_list)} candidate interventions converged in imagination")
        return {"chosen": None, "adopted": False, "escalated": True, "impasse": node,
                "candidates_tried": tried, "model_before": model_before, "target_rule": resolved_target}

    rules_patch = chosen["candidate"]["rules"]
    denials = [(name, _rule_denylisted(sub, name)) for name in rules_patch]
    denied = [(name, reason) for name, (is_denied, reason) in denials if is_denied]

    if denied:
        # SAFETY BOUNDARY: a validated fix exists, but touches frozen-core
        # (or unknown) provenance -- propose for human review, adopt NOTHING.
        proposal = _mint_proposal(agent, target_rule=resolved_target, candidate=chosen["candidate"],
                                   reasons=denied, model_before=model_before,
                                   model_after=chosen["check"]["model_after"])
        impasse = _raise_human_impasse(
            agent, gap="self_correction_frozen_fix",
            note=f"a validated fix for {resolved_target!r} converges in imagination but touches "
                 f"frozen/unknown-provenance rule(s) {[n for n, _ in denied]!r} -- proposal raised "
                 f"for human review, no autonomous edit made",
            extra={"proposal": _v(proposal)})
        return {"chosen": chosen["candidate"].get("label"), "adopted": False, "escalated": True,
                "proposal": proposal, "impasse": impasse, "denied": denied,
                "candidates_tried": tried, "model_before": model_before,
                "model_after_candidate": chosen["check"]["model_after"], "target_rule": resolved_target}

    adoptions = _adopt_rule_bundle(agent, rules_patch)
    model_final = predict_collapse(agent, horizon=horizon, frontier_sample=frontier_sample,
                                    focus_hops=focus_hops, imagine_steps=imagine_steps)
    return {"chosen": chosen["candidate"].get("label"), "adopted": True, "escalated": False,
            "adoptions": adoptions, "model_before": model_before,
            "model_after_candidate": chosen["check"]["model_after"], "model_final": model_final,
            "candidates_tried": tried, "target_rule": resolved_target}


__all__ = [
    "imagine_and_check_convergence",
    "intervene_on_divergence",
]


def _candidate_digest(candidate: dict) -> str:
    payload = _json.dumps(candidate.get("rules") or {}, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + _hashlib.sha256(payload).hexdigest()
