"""solver_dispatch -- Rung 1 of docs/research/engine_substrate/
QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md: wires the seven-item reasoning/
solving toolbox landed 2026-08-14 (propositional_deduction.py,
can_native_orchestration.py, can_junction_tree.py, can_native_bp.py,
reasoning_can_bridge.py, analogical_thinking.py +
propositional_deduction.mint_logical_schema_from_analogy, and
problem_decomposition.py) as candidate `Resolver`s for `question_driver`'s
EXISTING dispatch machinery (`qd_bind_resolver`, `seeds/question_driving.json`
-- a kind-string JOIN between `Agent -has_goal-> Goal` and
`Agent -has_resolver-> Resolver`, unchanged by this module, per the prereg's
own headline finding that the JOIN is already generic over kind).

SHAPE, mirrored verbatim from `question_driver.py`'s own five live resolvers
(`question_driver.py:290-514`, cited in the prereg Sec1.2 item 2): each
`solve_*` function below is a MODULE-LEVEL callable
`fn(adapter, goal_node) -> None` -- a THIN boundary invocation of one
existing toolbox facility, plus a MECHANICAL write-back of that facility's
own result onto the Goal node's attrs (`answer`/`status`/`note`, plus a few
resolver-specific diagnostic attrs, exactly the free-form pattern
`elevator_compute` already uses for `wall_kind`/`missing`). No decision is
made here about WHICH resolver runs (that is `qd_bind_resolver`, unchanged)
or about the MEANING of a result (every verdict --minted/applied/attempted/
direction-- is read verbatim off the toolbox function's own return dict).

NAMESPACING (the prereg's own Sec1.3 risk, addressed here). Every
`resolves_kind` below is `solve_`-prefixed. Verified by direct grep (see
QUESTION_DRIVER_RUNG1_RESULTS.md) that no existing `Goal.kind` value anywhere
in `domains/*.py`/`scripts/*.py`/`seeds/*.json` starts with `solve_` --
`question_driving.json`'s own six kinds (world/know/meta/contrast/gap/
compound/compare), `reflective_faculty.py`'s (find/describe_scene/
produce_utterance), `reading_drive.py`'s (produce_analysis/comprehend),
`conversation_action.py`'s caller-supplied kind, and every one-off script's
own ad hoc Goal.kind (build/compose/verdict/option/concern/synth_program/...)
are all disjoint from this namespace.

NODE-REFERENCE DISCIPLINE (a judgment call, documented in the RESULTS doc):
a solve_* Goal that needs to operate on a specific Microtheory or
DirectionalCorrespondence node references it via a GRAPH EDGE
(`targets_mt`/`targets_correspondence`, two new Gamma productions in
`seeds/solver_dispatch.json`) -- mirroring `has_subgoal`/`has_goal`'s own
edge-reference discipline -- rather than smuggling a raw NodeID into a Goal
ATTR (no existing precedent in this codebase stores a bare NodeID as a node
attr value; every existing example that looks similar,
e.g. `propositional_deduction.mint_logical_schema`'s return dict, is a
PYTHON-side return value, never a `set_attr` write). Any RESULT payload that
itself carries raw NodeIDs (can_junction_tree's `state` dict when a
projection's nodes are ShapeSignature ids rather than plain CAN concept ids,
`reasoning_can_bridge`'s `concept` field, `mint_logical_schema_from_analogy`'s
`node`) is kept in the adapter's own `solve_caps` Python-side cache
(mirroring `question_driver.py`'s existing `pack_caps` pattern for
non-graph-primitive data) rather than written onto the Goal node; only plain
scalars/strings/flat-numeric-dicts are written as Goal attrs.

RUNG 2 ADDITION (QUESTION_DRIVER_RUNG2_PREREG.md): every wall branch now
ALSO writes a `gap_key` attr via the `_wall` helper -- a stable identity for
THIS attempt (statement text / targeted node id / direction / candidate set
+ bound, whichever the call site has on hand), alongside the `status:
"walled"` + `note` write Rung 1 already made at every failure point. This is
the SAME mechanical-fact-recording precedent `_answer_topic_reply` already
uses for `outcome` (`substrate/world_adapter.py`) -- never a decision about
whether a wall IS a gap. `seeds/gap_awareness.json::note_solve_exhausted_gap`
is the Rule that reads `status=="walled"` + `gap_key` and decides to file a
`SelfConcern{kind:"solve_failure"}`, content-deduped on `gap_key`.
"""
from __future__ import annotations

from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  Mechanical adapter I/O -- the same idiom every domains/*.py module in this
#  toolbox already duplicates locally (propositional_deduction._resolve,
#  reasoning_can_bridge._resolve).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    return sub, native, ag_node


def _solve_caps(adapter) -> dict:
    """The `pack_caps` precedent (`question_driver.py::_pack_caps`),
    generalised from ONE active pack to per-goal keying (this dispatcher can
    have several concurrently-live solve_* Goals, unlike QuestionDriver's one
    active QuestionPack per `drive()` call). Holds whatever a solve_* Goal's
    resolver needs that is NOT graph-attr-safe (a candidate-projection list
    carrying raw NodeIDs, a full result dict with node references) --
    mechanical caller-staged I/O, never a decision."""
    return adapter._master.setdefault("solve_caps", {})


def _stash_result(adapter, goal_node, result: Any) -> None:
    _solve_caps(adapter).setdefault(goal_node, {})["result"] = result


def _at_num(at: dict, key: str, default):
    """Mechanical attr read: distinguishes "not supplied" (attr absent /
    None -- use `default`) from "supplied, including an explicit falsy
    numeric value such as 0 or 0.0" (honour it). Every numeric Goal attr
    read in this module that has a real, meaningful zero value (a
    treewidth bound of 0 is a genuine -- if degenerate -- request for a
    single-node/edgeless decomposition; an alpha/epsilon of 0.0 is a
    genuine zero-weight/zero-tolerance request) must go through this, not
    a bare `at.get(key) or default` -- Python's `or` treats 0/0.0 as
    "missing" and would silently substitute `default`, indistinguishable
    from the caller never having supplied the attr at all. Found live as a
    real footgun on `treewidth_bound` while building
    QUESTION_DRIVER_RUNG2_RESULTS.md's own can_exact wall test (documented
    there, fixed here); this is the swept fix for every other numeric attr
    read in this module that shares the same shape. Sites where the
    default itself already equals the falsy value (e.g. `t` defaulting to
    0, `refine_budget` defaulting to 0) are intentionally left on the
    plain `or` form -- there is no observable difference between "absent"
    and "explicit 0" there, so converting them would be a no-op churn, not
    a fix; this helper exists for sites where the distinction is real."""
    v = at.get(key)
    return default if v is None else v


def _wall(sub, goal_node, gap_key: str, note, **extra) -> None:
    """Rung 2 (QUESTION_DRIVER_RUNG2_PREREG.md Sec2/Sec3): the SAME mechanical
    write-back every resolver's wall branch already did in Rung 1
    (`status:"walled"` + `note`), plus ONE new datum -- `gap_key`, a stable
    identity for THIS attempt (statement text / targeted node id / direction
    / candidate+bound, whichever this call site actually has on hand), never
    a re-derivation of the note text. This is a fact write, not a decision:
    seeds/gap_awareness.json::note_solve_exhausted_gap is the Rule that reads
    `status=="walled"` + `gap_key` and DECIDES a gap should be filed (with
    its own content-dedup guard on `gap_key`) -- this helper never touches
    SelfConcern, gap_noted, or any gap-awareness node."""
    sub.set_attr(goal_node, "status", "walled")
    sub.set_attr(goal_node, "note", note)
    sub.set_attr(goal_node, "gap_key", gap_key)
    for k, v in extra.items():
        sub.set_attr(goal_node, k, v)


# =============================================================================
#  INGEST HELPERS -- mint a solve_* Goal directly (Rung 1's own scope, per the
#  prereg Sec6.1: "a caller/test mints Goal{kind:'solve_deduction', ...}
#  directly, the way `_ingest_target` already does for world/know kinds" --
#  no comprehension/recognition step exists yet, deliberately (Rung 3)).
#  Mechanical translation of caller intent into a graph-resident Goal, the
#  SAME shape `question_driver._ingest_target` already is.
# =============================================================================
def _mint_base(adapter, kind: str, raw: str, attrs: dict):
    sub, native, ag = _resolve(adapter)
    full = {"kind": kind, "raw": (raw or "")[:160], "status": "pending"}
    full.update(attrs)
    goal = sub.add_node("Goal", full)
    sub.add_edge(ag, "has_goal", goal)
    from domains import interlocutor_model as _im
    _im.wanted_by(adapter, goal)
    return goal


def mint_solve_deduction_goal(adapter, statement: str, *, mode: str = "auto"):
    """`mode` in {"conditional","universal","existential","auto"} --
    "auto" (default) tries all three parsers in a FIXED priority order
    (universal -> existential -> conditional, see `solve_deduction`'s own
    docstring for why quantifier-aware goes first, 2026-08-15 bugfix) and
    keeps the first that parses; an explicit mode skips straight to one
    parser. Mirrors `_split_leading_quantifier`'s own honest-residual
    discipline: the ladder is a fixed, inspectable order over EXISTING
    independent parsers (propositional_deduction.py's own three mint_*
    entry points), not a semantic decision about the statement's meaning."""
    return _mint_base(adapter, "solve_deduction", statement,
                       {"statement": statement, "mode": mode})


def mint_solve_can_relax_goal(adapter, mt, *, k_starts: int = 1, max_steps: Optional[int] = None):
    """`k_starts<=1` -> a single `scoped_settle` (can_native_orchestration.py);
    `k_starts>1` -> `multi_start_settle_and_pick_best` over that many random
    restarts. `mt` is wired via a `targets_mt` edge, not a Goal attr."""
    sub, native, ag = _resolve(adapter)
    attrs = {"k_starts": float(k_starts)}
    if max_steps is not None:
        attrs["max_steps"] = float(max_steps)
    goal = _mint_base(adapter, "solve_can_relax", "solve_can_relax", attrs)
    sub.add_edge(goal, "targets_mt", mt)
    return goal


def mint_solve_can_exact_goal(adapter, mt, *, treewidth_bound: Optional[int] = None,
                              max_exact_n: Optional[int] = None, commit: bool = True):
    sub, native, ag = _resolve(adapter)
    attrs = {"commit": bool(commit)}
    if treewidth_bound is not None:
        attrs["treewidth_bound"] = float(treewidth_bound)
    if max_exact_n is not None:
        attrs["max_exact_n"] = float(max_exact_n)
    goal = _mint_base(adapter, "solve_can_exact", "solve_can_exact", attrs)
    sub.add_edge(goal, "targets_mt", mt)
    return goal


def mint_solve_can_bp_goal(adapter, mt, *, combine: str = "max_product",
                           max_rounds: Optional[int] = None, epsilon: Optional[float] = None,
                           commit: bool = False):
    sub, native, ag = _resolve(adapter)
    attrs = {"combine": combine, "commit": bool(commit)}
    if max_rounds is not None:
        attrs["max_rounds"] = float(max_rounds)
    if epsilon is not None:
        attrs["epsilon"] = float(epsilon)
    goal = _mint_base(adapter, "solve_can_bp", "solve_can_bp", attrs)
    sub.add_edge(goal, "targets_mt", mt)
    return goal


# =============================================================================
#  CAN NETWORK GROWTH FROM TEXT (docs/research/engine_substrate/SOLVER_CAN_
#  ADAPTER_PREREG.md/_RESULTS.md) -- the fourth NL-adapter rung in this arc,
#  and the ONLY one of the four that does NOT mint a solve_* Goal itself.
#  `solve_can_relax`/`solve_can_exact`/`solve_can_bp` all need a `targets_mt`
#  edge to an ALREADY-POPULATED CAN Microtheory (Concept nodes + weighted
#  causal_influence edges) -- `worlds/bigville_can_beliefs.build_resident_
#  can_mt` remains the ONLY network-from-scratch builder, and it is a
#  mechanical translation of an ALREADY-DRAWN numeric params dict, not text
#  (unchanged finding, PREREG Sec2 -- there is still no NL path to a brand
#  new Concept or to a weight read off a sentence).
#
#  What DOES compose, confirmed live before this was written (PREREG Sec4-6):
#  seeds/can_native_reimplementation.json's Hebbian mint-on-recurrence
#  mechanism (can_native_note_coactivation / can_native_hebbian_mint, BOTH
#  UNCHANGED) mints a genuinely NEW causal_influence edge (fixed +1.0 weight
#  -- never read from language) between two Concepts of an ALREADY-BUILT
#  Mt once they persistently co-activate to the SAME NONZERO sign across
#  >=2 distinct external ticks. `Concept.state` (the sign it keys on) is
#  computed by that SAME seed's can_native_update_3state rule from
#  `external_field` -- exactly the attr `reasoning_can_bridge.apply_
#  derived_fact_as_can_evidence` (UNCHANGED) already writes from a real
#  declarative sentence. Chaining these (apply real NL evidence -> let the
#  discrete relaxation settle -> tick the Hebbian mechanism forward) grows
#  real network STRUCTURE from real text -- narrower than "build a network
#  from a description" (no new Concept, no weight-from-language), but a
#  real, live-verified composition, not a reweighting of something the
#  hand-authored STRUCTURAL_EDGES template already declared (PREREG Sec6's
#  own control: the SAME tick schedule with no evidence applied never grows
#  the pair, ruling out "would have happened anyway").
# =============================================================================
_CAN_NATIVE_SEED_PATH = None  # resolved lazily, see ensure_can_native_engine_loaded


def _can_native_seed_path() -> str:
    global _CAN_NATIVE_SEED_PATH
    if _CAN_NATIVE_SEED_PATH is None:
        import os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _CAN_NATIVE_SEED_PATH = os.path.join(_root, "seeds", "can_native_reimplementation.json")
    return _CAN_NATIVE_SEED_PATH


def ensure_can_native_engine_loaded(adapter) -> bool:
    """Idempotently install `seeds/can_native_reimplementation.json`'s
    engine rules (can_native_update_3state/_2state, can_native_note_
    coactivation, can_native_hebbian_mint/_reweight, ...) onto `adapter`'s
    live substrate -- the file declares `"self_load_only": true`
    (`substrate/boot_all.py:39`), so a normal `load_all_seeds()` boot does
    NOT install it (by design, matching this codebase's own on-demand-seed
    convention). `tests/test_bigville_can_native_migration.py::_run_native`
    is the EXISTING precedent for this exact `engine_rules_only` +
    `load_seed_manifest` load path -- this function is that same call,
    reused, guarded for idempotency.

    The guard matters: confirmed live (PREREG Sec8) that calling
    `load_seed_manifest` on this manifest TWICE on one substrate DOUBLES
    the rule count and would double-fire every effect (a second, redundant
    `evidence_confirm` bump per tick; a real risk of corrupting the
    Coactivation ledger). The sentinel is `can_native_hebbian_mint`'s own
    presence in `export_rules()` by name -- the SAME `_has_concept`-sentinel
    idempotency idiom `reasoning_can_bridge._ensure_correspondence_seed`
    already uses for a structurally identical problem (installed-already
    check before a `load_seed_manifest` call), applied here to a rule name
    instead of a Concept name because this seed's own sentinel is a rule,
    not a Concept.

    Returns `True` if this call actually installed the rules, `False` if
    they were already present (a pure informational read, not a decision
    anything downstream branches on)."""
    sub, native, ag = _resolve(adapter)
    already = any(r.get("name") == "can_native_hebbian_mint" for r in native.export_rules())
    if already:
        return False
    import json
    from substrate.seed_loader import engine_rules_only
    manifest = json.load(open(_can_native_seed_path()))
    native.load_seed_manifest(engine_rules_only(manifest))
    return True


def _extract_property_fact(adapter, statement: str):
    """Pure, zero-mutation parse: `statement` -> `(entity, attr)` or `None`.
    A local, "own copy" duplicate of the SAME three gates `mint_solve_
    reasoning_bridge_goal_from_text` already established (speech_act,
    property-predication, non-empty extraction) -- not a shared import,
    mirroring the house convention `_would_parse_as_deduction` already
    follows for the identical reason (this rung must not touch that prior
    rung's own function)."""
    from domains import reading_collapse as rc
    from domains import propositional_deduction as pd
    from domains import situation_model_reader as smr
    if not statement or not str(statement).strip():
        return None
    whole = rc.read_clause(adapter, statement, write=False, learn=False)
    if whole.get("speech_act") == "question":
        return None
    preds = whole.get("predications") or []
    if not preds or len(preds[0]) < 3:
        return None
    rel, subj, obj = preds[0][0], preds[0][1], preds[0][2]
    if not smr._is_property_pred(str(rel)):
        return None
    entity = str(subj).strip()
    attr = pd._norm_attr(obj)
    if not entity or entity == "_" or not attr:
        return None
    return (entity, attr)


def grow_can_network_from_text(adapter, mt, statements: list, *, alpha: float = 1.0,
                               extra_ticks: int = 2) -> Optional[dict]:
    """Grows real `causal_influence` EDGE structure on an ALREADY-BUILT CAN
    Microtheory `mt` (e.g. `worlds.bigville_can_beliefs.build_resident_
    can_mt`'s own output, UNCHANGED) from a list of real declarative
    sentences -- narrower than "build a network from a description" (see
    the module comment above and PREREG Sec11): no new Concept is ever
    minted, and a minted edge's weight is ALWAYS the Hebbian mechanism's own
    fixed +1.0 constant, never read from language. What genuinely grows is
    which PAIRS of the Mt's own already-existing Concepts become newly
    coupled, driven by real NL evidence feeding the discrete relaxation +
    Hebbian mint-on-recurrence mechanism (`ensure_can_native_engine_loaded`
    must have been called on `adapter` already, or this Mt's `discrete_mode`
    must already be configured -- see step 1).

    PRECONDITION (step 1, honest decline, not silently patched): `mt.
    discrete_mode` must already be `"3state"`/`"2state"` (mechanically
    defaulted to `"3state"`+`can_tick=0` if entirely absent -- matching
    every existing test/demo's own default) or this call declines (`None`)
    -- a Mt deliberately configured to something else (e.g. `"static"`,
    used elsewhere in this codebase to isolate the Hebbian rules from the
    relaxation rules) has opted out, and this function must not override
    that caller choice.

    PURE PRE-CHECK (step 2, zero mutation, mirrors `_would_parse_as_
    deduction`'s own precedent): each statement is parsed via
    `_extract_property_fact` (read-only). Declines (`None`, zero graph
    mutation) if fewer than 2 statements survive -- cannot demonstrate
    co-occurrence-driven growth from 0-1 facts, the same "at least 2" floor
    `solve_decompose`'s own adapter uses for the identical structural reason.

    REAL APPLICATION (step 3, a documented, honest departure from a
    zero-mutation-on-ANY-decline guarantee -- the SAME departure `SOLVER_
    DECOMPOSE_ADAPTER_RESULTS.md` Sec4 already made and justified for the
    identical reason: the suitability signal, "does this Concept exist in
    THIS Mt", is only knowable by actually calling `apply_derived_fact_as_
    can_evidence`, UNCHANGED): each pre-checked `(entity, attr)` pair is
    applied via that existing function; a hit is counted only if it BOTH
    reports `applied: True` AND resolves to a Concept that is actually a
    `has_concept` member of the CALLER's own `mt` (a defensive re-check
    against `apply_derived_fact_as_can_evidence`'s own name-based ambiguity
    residual, PREREG Sec11 item 5 -- not fixed here, only guarded against
    for this function's own accounting). If fewer than 2 pairs actually
    applied to THIS Mt, returns `{"grown": False, "reason": ..., "applied":
    [...]}"` -- real evidence may already be sitting in the graph for
    whichever pairs DID succeed; this is reported, not hidden.

    DRIVE (step 4): `native.force_all_dirty()` (a host-side PyO3 write --
    `concept_apply_evidence` -- does not mark a Concept dirty for `run_
    rules()`'s incremental matching, confirmed live, PREREG Sec6 step 3;
    this is the SAME established idiom 20+ existing call sites in this
    codebase already use after a host-side attribute write) + `run_rules()`
    to settle discrete state, then `extra_ticks` (default 2, the measured-
    live-necessary minimum for genuine cross-tick recurrence, PREREG Sec4)
    more distinct `can_tick` epochs, each mechanically bumped + ticked -- a
    FIXED, bounded schedule, never a data-dependent decision, mirroring
    `solve_decompose`'s own `_drive_to_resolution` bounded-loop precedent.

    REPORT (step 5): before/after edge sets read via `can_junction_tree.
    can_network_from_mt` (UNCHANGED, pure read) bracket the drive step --
    `{"grown": bool, "new_edges": [(id_a, id_b), ...], "applied": [(entity,
    attr), ...], "before_edge_count": int, "after_edge_count": int}` --
    reports what a real before/after diff shows, never a claim about what
    "should" have grown."""
    from domains import reasoning_can_bridge as rcb
    from domains import can_junction_tree as cjt
    sub, native, ag = _resolve(adapter)

    # --- step 1: precondition ------------------------------------------------
    mt_attrs = sub.node(mt)["attrs"]
    mode = mt_attrs.get("discrete_mode")
    if mode is None:
        sub.set_attr(mt, "discrete_mode", "3state")
        if mt_attrs.get("can_tick") is None:
            sub.set_attr(mt, "can_tick", 0.0)
        mode = "3state"
    elif mode not in ("3state", "2state"):
        return None
    if sub.node(mt)["attrs"].get("can_tick") is None:
        sub.set_attr(mt, "can_tick", 0.0)

    # --- step 2: pure pre-check, zero mutation -------------------------------
    if not isinstance(statements, (list, tuple)):
        return None
    candidates = []
    for stmt in statements:
        got = _extract_property_fact(adapter, stmt)
        if got is not None:
            candidates.append(got)
    if len(candidates) < 2:
        return None

    # --- step 3: real application, tracked, defensively re-verified ---------
    mt_concepts = set(native.neighbours(mt, "has_concept"))
    applied = []
    for entity, attr in candidates:
        r = rcb.apply_derived_fact_as_can_evidence(adapter, entity, attr,
                                                     positive=True, alpha=alpha)
        if r.get("applied") and r.get("concept") in mt_concepts:
            applied.append((entity, attr))
    if len(applied) < 2:
        return {"grown": False, "applied": applied,
                "reason": "fewer than 2 statements resolved to a Concept "
                          "actually inside the target Mt"}

    # --- step 4: drive the growth loop ---------------------------------------
    before = cjt.can_network_from_mt(native, mt)
    before_edges = set(before["edges"])

    native.force_all_dirty()
    native.run_rules()
    base_tick = float(sub.node(mt)["attrs"].get("can_tick") or 0.0)
    for i in range(1, max(2, int(extra_ticks)) + 1):
        sub.set_attr(mt, "can_tick", base_tick + i)
        native.run_rules()

    sub.add_node("NativeSolverDispatchReceipt", {
        "schema": "native_solver_dispatch_receipt_v1",
        "cluster": "solver_dispatch.can_network_settlement",
        "provenance": "native_rule_readback:solver_can_network",
        "native_rule": "solver_can_native_rules",
        "native_steps": ["force_all_dirty", "run_rules", "set_can_tick", "run_rules"],
        "tick_count": max(2, int(extra_ticks)),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })

    # --- step 5: report, measured not assumed --------------------------------
    after = cjt.can_network_from_mt(native, mt)
    after_edges = set(after["edges"])
    new_edges = sorted(after_edges - before_edges)
    return {"grown": bool(new_edges), "new_edges": new_edges, "applied": applied,
            "before_edge_count": len(before_edges), "after_edge_count": len(after_edges)}


def mint_solve_reasoning_bridge_goal(adapter, direction: str, *, entity: Optional[str] = None,
                                     attr: Optional[str] = None, positive: bool = True,
                                     alpha: float = 1.0, mt=None, t: int = 0):
    """`direction` in {"deduction_to_can","can_to_deduction"}. The
    deduction_to_can direction needs `entity`+`attr` (plain strings, exactly
    `apply_derived_fact_as_can_evidence`'s own signature); the
    can_to_deduction direction needs `mt` (wired via `targets_mt`)."""
    sub, native, ag = _resolve(adapter)
    attrs: dict = {"direction": direction, "positive": bool(positive), "alpha": float(alpha),
                   "t": float(t)}
    if entity is not None:
        attrs["entity"] = entity
    if attr is not None:
        attrs["attr"] = attr
    goal = _mint_base(adapter, "solve_reasoning_bridge", "solve_reasoning_bridge", attrs)
    if mt is not None:
        sub.add_edge(goal, "targets_mt", mt)
    return goal


def mint_solve_reasoning_bridge_goal_from_text(adapter, statement: str, *,
                                               alpha: float = 1.0):
    """The FIRST NL-to-structure adapter for the six previously-unwired
    `solve_*` resolvers (docs/research/engine_substrate/SOLVER_NL_ADAPTER_
    PREREG.md/_RESULTS.md) -- a front door onto `solve_reasoning_bridge`'s
    `deduction_to_can` direction, which needed only two bare strings
    (`entity`, `attr`) to begin with, unlike the other five resolvers' own
    graph-object prerequisites (a CAN Microtheory, a DirectionalCorrespondence,
    a candidate-projection list -- see the PREREG's ranking).

    PARSE: reads `statement` through the SAME general reading pipeline
    `propositional_deduction.parse_conditional`'s `bare_universal` branch
    already uses (`reading_collapse.read_clause`, unmodified) -- one
    declarative copular/property predication `[rel, subject, object]` ->
    `entity = subject`, `attr = propositional_deduction._norm_attr(object)`.
    Both extraction primitives are pure reuse, not new parsing: `_norm_attr`
    is `solve_deduction`'s own normaliser; `situation_model_reader.
    _is_property_pred` is the SAME property-predication gate a dozen other
    modules already import (coref_entities.py/inference_generation.py/
    character_tom.py/global_monitoring.py/reading_drive.py -- confirmed by
    grep before reuse, see PREREG Sec2).

    HONEST DECLINE (returns `None`, mints NOTHING -- mirrors the Bug 1 fix
    precedent in SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md: an adapter that
    silently mints garbage from unsuitable input repeats the exact mistake
    that rung spent itself fixing):
      * empty/whitespace-only statement;
      * `speech_act == "question"` (the reader's OWN verdict, already
        computed -- a question's honest fallback grounding can still surface
        an is_a-shaped predication, e.g. "Is Verity trustworthy?", that would
        otherwise pass every downstream check; SAME gate `parse_conditional`
        already added for the identical reason);
      * no predication at all, or the leading predication's relation is not
        a property predication (`_is_property_pred` -- an ordinary
        transitive event like "Verity likes apples" grounds fine but is NOT
        a held attribute this direction's signature means);
      * an empty/degenerate subject or attr after extraction.

    `positive` is always `True` -- no negation-detection machinery exists
    anywhere in the reading pipeline for a plain declarative sentence's
    polarity (checked: `reading_collapse.py` carries no NEG/negator markup
    that reaches a grounded predication's relation), so this adapter
    honestly never attempts a negated fact; wiring negation detection is a
    named, separate follow-on, not attempted here.

    Dispatches through the UNCHANGED `mint_solve_reasoning_bridge_goal` ->
    `qd_bind_resolver` -> `solve_reasoning_bridge` machinery exactly as
    every other caller already does -- this function only adds the missing
    front door; `solve_reasoning_bridge`'s own internals are untouched."""
    from domains import reading_collapse as rc
    from domains import propositional_deduction as pd
    from domains import situation_model_reader as smr
    if not statement or not str(statement).strip():
        return None
    whole = rc.read_clause(adapter, statement, write=False, learn=False)
    if whole.get("speech_act") == "question":
        return None
    preds = whole.get("predications") or []
    if not preds or len(preds[0]) < 3:
        return None
    rel, subj, obj = preds[0][0], preds[0][1], preds[0][2]
    if not smr._is_property_pred(str(rel)):
        return None
    entity = str(subj).strip()
    attr = pd._norm_attr(obj)
    if not entity or entity == "_" or not attr:
        return None
    return mint_solve_reasoning_bridge_goal(
        adapter, "deduction_to_can", entity=entity, attr=attr,
        positive=True, alpha=alpha)


def mint_solve_analogical_promote_goal(adapter, corr_node):
    """`corr_node`: a `DirectionalCorrespondence` node already recorded via
    `analogical_thinking.record_directional_correspondence` (mechanical
    ingest, unchanged, called by the caller BEFORE minting this Goal -- this
    module does not compute correspondences, only promotes an
    already-decided one, exactly like `mint_logical_schema_from_analogy`
    itself never computes a correspondence)."""
    sub, native, ag = _resolve(adapter)
    goal = _mint_base(adapter, "solve_analogical_promote", "solve_analogical_promote", {})
    sub.add_edge(goal, "targets_correspondence", corr_node)
    return goal


def _find_concepts_by_name(sub, name: str) -> list:
    """A local copy of the SAME mechanical global-scan-by-name idiom
    `domains/neuroscience_tagging.py::_find_concept_by_name` /
    `domains/reasoning_can_bridge.py::_find_concept_by_name` /
    `domains/propositional_deduction.py::_schema_by_name` already are
    (unedited elsewhere) -- "same pattern, own cache -- no cross-import",
    the house convention `analogical_thinking.py`'s own module comment
    documents for `_agent_node_id`/`_resolve_blob_edge`. Returns EVERY
    Concept node named `name`, not just the first (the caller, not this
    lookup, decides what to do about more than one -- see
    `mint_solve_analogical_promote_goal_from_text`'s ambiguity gate,
    SOLVER_ANALOGY_ADAPTER_PREREG.md Sec3)."""
    return [c for c in sub.nodes("Concept") if sub.node(c)["attrs"].get("name") == name]


def mint_solve_analogical_promote_goal_from_text(adapter, statement: str):
    """The SECOND NL-to-structure adapter for the six previously-unwired
    `solve_*` resolvers (docs/research/engine_substrate/SOLVER_ANALOGY_
    ADAPTER_PREREG.md/_RESULTS.md) -- a front door onto `solve_analogical_
    promote`, which the predecessor rung (SOLVER_NL_ADAPTER_RESULTS.md)
    ranked #2 and left unbuilt on the belief that "no analogy-shaped
    sentence parser exists anywhere in the tree." That belief does not
    survive a broader grep: `seeds/reading_constructions.json` already
    seeds a `LIKE` MarkerClass (`like`/`resembles`/`resemble`) plus
    `comparative_like`/`comparative_like_cop` constructions that ground
    "X is like Y"/"X resembles Y" to exactly `["similar", subject, object]`
    via the UNMODIFIED general reading pipeline -- confirmed live on real
    corpus vocabulary before this function was written, see the PREREG.

    PARSE: `reading_collapse.read_clause` (unmodified) -> leading
    predication must be `["similar", subj, obj]` (the relation label the
    seeded construction already emits for a genuine analogy cue; `contrast`
    -- "X is unlike Y" -- is the honest opposite signal and is correctly
    NOT accepted here).

    RESOLVE: `subj`/`obj` -> real `Concept` graph nodes via
    `_find_concepts_by_name` (the SAME mechanical exact-name-match idiom
    `neuroscience_tagging._find_concept_by_name` already is, unedited
    elsewhere), each REQUIRED to resolve to EXACTLY ONE Concept node.
    `Concept` is a heavily-overloaded node type (CAN belief-network
    propositions AND domain-vocabulary corpus terms share it,
    `ENTITY_RESOLUTION_RESULTS.md` Sec1) -- 507 real duplicate Concept
    names exist in a full `load_all_seeds()` boot, so this is a REAL,
    reachable ambiguity, not a defensive hypothetical (PREREG Sec3 confirms
    live: "The agent is like the patient." hits a 3-way-ambiguous
    "agent"). Mirrors `ENTITY_RESOLUTION_RESULTS.md`'s own no-over-merge
    discipline: REFUSE rather than guess which Concept was meant.

    COMPOSE: `analogical_thinking._concept_shape_vector`/`_pair_witness`/
    `record_directional_correspondence` -- all three UNEDITED, all three
    already mechanical, already load-bearing-tested
    (`tests/test_directional_correspondence.py`) -- turn the two resolved
    Concept nodes into a real `DirectionalCorrespondence` node, then
    dispatches through the UNCHANGED `mint_solve_analogical_promote_goal` ->
    `qd_bind_resolver` -> `solve_analogical_promote` machinery exactly as
    every other caller already does. `solve_analogical_promote`'s own
    internals are untouched; this function only adds the missing front
    door, the SAME shape `mint_solve_reasoning_bridge_goal_from_text`
    already established for its own resolver.

    HONEST DECLINE (returns `None`, mints NOTHING -- mirrors the Bug 1 fix
    precedent both prior NL-adapter rungs already established: an adapter
    that silently mints garbage from unsuitable input repeats the exact
    mistake those rungs spent themselves fixing):
      * empty/whitespace-only statement;
      * `speech_act == "question"` (a comparative question, "Is X like Y?",
        still grounds a `similar` predication -- the SAME risk class as the
        arithmetic-question bug fixed for `solve_deduction`, gated
        defensively rather than assumed safe);
      * no predication at all, or the leading predication's relation is not
        exactly `"similar"` (excludes `"contrast"` -- dissimilarity is not
        an analogy -- and every ordinary property/event predication);
      * `subj`/`obj` does not resolve to EXACTLY ONE Concept node each (zero
        matches -- unknown vocabulary; more than one match -- a genuine,
        measured, reachable ambiguity, see above);
      * the two resolved Concept nodes are IDENTICAL (mirrors
        `_compute_analogy`'s own `if sn == tn: return None` guard,
        `analogical_thinking.py:1000` -- "same concept; not an analogy");
      * `record_directional_correspondence` itself returns `None` (its own
        documented honest no-op -- defensive, matches that function's own
        contract).

    Only a single leading predication is read (mirrors `mint_solve_
    reasoning_bridge_goal_from_text`'s own single-predication scope, itself
    mirroring `parse_conditional`'s). Only the seeded `LIKE`-marker-class
    surface forms (`like`/`resembles`/`resemble`, copular and verbal) are
    covered -- "X is similar to Y" (adjective+"to") does not ground via this
    construction today (checked live, PREREG Sec2) and is a named, separate
    follow-on, not attempted here."""
    from domains import reading_collapse as rc
    from domains import analogical_thinking as at_mod
    if not statement or not str(statement).strip():
        return None
    sub, native, ag = _resolve(adapter)
    whole = rc.read_clause(adapter, statement, write=False, learn=False)
    if whole.get("speech_act") == "question":
        return None
    preds = whole.get("predications") or []
    if not preds or len(preds[0]) < 3:
        return None
    rel, subj, obj = preds[0][0], preds[0][1], preds[0][2]
    if rel != "similar":
        return None
    subj, obj = str(subj).strip(), str(obj).strip()
    if not subj or not obj:
        return None
    hits_a = _find_concepts_by_name(sub, subj)
    hits_b = _find_concepts_by_name(sub, obj)
    if len(hits_a) != 1 or len(hits_b) != 1:
        return None
    node_a, node_b = hits_a[0], hits_b[0]
    if node_a == node_b:
        return None
    vec_a = at_mod._concept_shape_vector(sub, node_a)
    vec_b = at_mod._concept_shape_vector(sub, node_b)
    witness = at_mod._pair_witness(sub, vec_a, vec_b)
    corr_node = at_mod.record_directional_correspondence(
        sub, node_a, node_b, vec_a, vec_b, witness)
    if corr_node is None:
        return None
    return mint_solve_analogical_promote_goal(adapter, corr_node)


def mint_solve_decompose_goal(adapter, candidates: list, bound: int, *,
                              max_exact_n: int = 10, refine_budget: int = 0):
    """`candidates`: the plain `{"name","nodes","edges",["edge_reason"]}`
    dict list `problem_decomposition.py`'s own `project_*` functions
    produce -- staged into `solve_caps` (may carry raw NodeIDs inside
    `nodes`/`edges`, e.g. `project_deduction_shared_attr`'s ShapeSignature
    node ids), never written as a Goal attr (see module docstring)."""
    goal = _mint_base(adapter, "solve_decompose", "solve_decompose",
                       {"bound": float(bound), "max_exact_n": float(max_exact_n),
                        "refine_budget": float(refine_budget)})
    _solve_caps(adapter).setdefault(goal, {})["candidates"] = candidates
    return goal


def _would_parse_as_deduction(adapter, statement: str) -> bool:
    """Pure, ZERO-MUTATION pre-check mirroring `solve_deduction`'s own fixed
    universal -> existential -> conditional ladder order (see `solve_
    deduction`'s docstring, the 2026-08-15 bugfix) -- calls ONLY the pure
    `parse_universal`/`parse_existential`/`parse_conditional` functions
    (`domains/propositional_deduction.py`, all UNEDITED), never their
    `mint_*` installer siblings. Every one of the three delegates to
    `reading_collapse.read_clause`/`decompose_sentence` with `write=False,
    learn=False` throughout (confirmed by direct read,
    SOLVER_DECOMPOSE_ADAPTER_PREREG.md Sec4) -- no `add_node`/`mint_*` call
    is reachable from any of the three. Used ONLY to decide, before minting
    anything at all, whether a statement is worth actually resolving via the
    real `solve_deduction` Goal/resolver machinery -- so a total decline
    (fewer than 2 usable statements) leaves ZERO graph mutation, matching
    the SAME "mints nothing on decline" guarantee `mint_solve_reasoning_
    bridge_goal_from_text`/`mint_solve_analogical_promote_goal_from_text`
    already established."""
    from domains import propositional_deduction as pd
    if pd.parse_universal(adapter, statement) is not None:
        return True
    if pd.parse_existential(adapter, statement) is not None:
        return True
    if pd.parse_conditional(adapter, statement) is not None:
        return True
    return False


def _drive_to_resolution(adapter, goal_node, max_iters: int = 32) -> None:
    """A same-shape, OWN-COPY mirror of `question_driver.py::_pump`'s own
    bounded tick loop (`domains/question_driver.py:652` -- production code,
    already called by `QuestionDriver.drive()`, not test-only) and `tests/
    test_solver_dispatch_migrated.py::_pump`'s identical inline copy: fire
    the `question_pursue` reflex, run the seeded rules to fixpoint, stop
    once the goal resolves or walls. "Same pattern, own cache -- no
    cross-import" -- the house convention `analogical_thinking.py`'s own
    module comment documents, already followed by this module's own
    `_find_concepts_by_name` (a local copy of `neuroscience_tagging._find_
    concept_by_name`'s idiom). This is the SAME already-existing Rust
    rule-engine invocation (`native.run_rules()`) every other driver in this
    codebase already performs -- sequencing an existing loop, never a NEW
    Python decision about what a goal's result means."""
    sub = getattr(adapter, "s", adapter)
    native = getattr(adapter, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    for iteration in range(max_iters):
        adapter.fire_reflexes()
        native.run_rules()
        if sub.node(goal_node)["attrs"].get("status") in ("resolved", "walled"):
            sub.add_node("NativeSolverDispatchReceipt", {
                "schema": "native_solver_dispatch_receipt_v1",
                "cluster": "solver_dispatch.goal_resolution_settlement",
                "provenance": "native_rule_readback:solver_dispatch_resolution",
                "native_rule": "solver_dispatch_native_resolution_rules",
                "native_steps": ["fire_reflexes", "run_rules"],
                "iterations": iteration + 1,
                "outcome_source": "native_rule_readback",
                "python_outcome_selection": False,
            })
            return
    sub.add_node("NativeSolverDispatchReceipt", {
        "schema": "native_solver_dispatch_receipt_v1",
        "cluster": "solver_dispatch.goal_resolution_settlement",
        "provenance": "native_rule_readback:solver_dispatch_resolution",
        "native_rule": "solver_dispatch_native_resolution_rules",
        "native_steps": ["fire_reflexes", "run_rules"],
        "iterations": max_iters,
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })


def mint_solve_decompose_goal_from_text(adapter, statements: list, bound: int, *,
                                        max_exact_n: int = 10, refine_budget: int = 0,
                                        mode: str = "auto"):
    """The THIRD NL-to-structure adapter for the six previously-unwired
    `solve_*` resolvers (docs/research/engine_substrate/SOLVER_DECOMPOSE_
    ADAPTER_PREREG.md/_RESULTS.md) -- a front door onto `solve_decompose`,
    which prior rungs ranked #3 ("expensive, non-independent -- inherits
    whichever upstream object it projects over"). That ranking does not
    survive investigation: `mint_solve_deduction_goal` (`solver_dispatch.py`
    above) has taken a bare statement string since Rung 1 -- it was NEVER
    gated behind a pre-built graph object, unlike `solve_reasoning_bridge`/
    `solve_analogical_promote`/the three CAN resolvers -- and `problem_
    decomposition.project_deduction_shared_attr`/`project_deduction_complete`
    (UNEDITED) are mechanical, node-source-AGNOSTIC shape extraction over
    whatever `ShapeSignature` nodes they are handed. Building a candidate
    projection from real deduction schema nodes was therefore ALREADY pure
    composition, not new capability -- confirmed live before writing this
    function (PREREG Sec2-3): three genuine Bigville-styled conditional
    statements ("If X is a resident, X can vote."/"... X is world safe."/
    "If X is a mayor, X can govern.") drive three real `solve_deduction`
    sub-goals to resolution, and racing `project_deduction_shared_attr`
    (treewidth=1, the real shared 'resident' antecedent) against `project_
    deduction_complete` (treewidth=2, K3) over those SAME 3 real schema
    nodes reproduces the exact discrimination shape `QUESTION_DRIVER_RUNG1_
    RESULTS.md`'s own hand-built chain test already measured, on
    independent statement text.

    SCOPE (a deliberate, named boundary, mirroring both prior `_from_text`
    rungs' own narrow scoping -- PREREG Sec5): this adapter covers ONLY
    deduction-schema candidates (`project_deduction_shared_attr`/
    `project_deduction_complete`) built from a LIST of deduction-shaped
    statements. `project_can_*` (needs an already-built CAN Microtheory --
    no NL-to-CAN-network path exists anywhere in this codebase, unchanged
    finding from `SOLVER_NL_ADAPTER_PREREG.md`) and `project_situation_
    model_shared_event` (needs already-minted `SmEvent` nodes -- situation-
    model ingestion is a separate, never-`solve_*`-wired facility) are named,
    separate follow-ons, NOT attempted here.

    PARSE + DRIVE (the one genuinely new piece is a DRIVER, not a parser --
    PREREG Sec3): each statement is dispatched through the ALREADY-EXISTING
    `mint_solve_deduction_goal` (an NL adapter since day one) and driven to
    resolution via `_drive_to_resolution` (a same-shape, own-copy mirror of
    `question_driver.py::_pump`'s own bounded tick loop -- production code,
    not test-only). This is unavoidable, not a design choice: `solve_
    decompose`'s own prerequisite (`mint_solve_decompose_goal`'s contract)
    is an ALREADY-RESOLVED node list staged in `solve_caps` at mint time --
    there is no way to defer resolving the sub-goals the way the two prior
    `_from_text` adapters deferred their own resolver dispatch to the
    caller.

    HONEST DECLINE (returns `None`; mirrors the Bug 1 fix precedent every
    rung in this arc has established -- an adapter that silently mints
    garbage from unsuitable input repeats the exact mistake those rungs
    spent themselves fixing):
      * `statements` is not a non-empty list/tuple, or `bound is None`;
      * fewer than 2 non-empty statements pass the PURE, zero-mutation
        `_would_parse_as_deduction` pre-check -- a genuine total decline
        leaves ZERO graph mutation, matching the prior two `_from_text`
        adapters' own "mints nothing" guarantee EXACTLY (PREREG Sec4);
      * fewer than 2 real `ShapeSignature` schema nodes are actually
        collected after driving the surviving statements' sub-goals (an
        honest defensive re-check -- the pure pre-check and the resolver's
        own ladder are not byte-identical code paths, so the ACTUAL outcome
        is re-verified rather than trusted from the pre-check's prediction).

    **A real, honestly-documented departure from the prior two `_from_text`
    adapters (PREREG Sec4), not silently glossed over**: a PARTIAL success
    (>=2 statements pass the pre-check, their sub-goals then driven for
    real) DOES leave real, inspectable `solve_deduction` Goal + `Shape
    Signature` nodes in the graph for the statements actually used, even if
    this function's own `solve_decompose` Goal is ultimately minted and
    returned. This is the unavoidable cost of `solve_decompose`'s
    prerequisite being an already-resolved node, not a bare string -- a
    total decline (the case that matters for "never silently mint garbage")
    remains a genuine zero-mutation refusal.

    Dispatches through the UNCHANGED `mint_solve_decompose_goal` ->
    `qd_bind_resolver` -> `solve_decompose` machinery exactly as every other
    caller already does -- this function only adds the missing front door;
    `solve_decompose`'s own internals, `solve_deduction`'s own internals,
    and `problem_decomposition.py` are all untouched."""
    if not statements or not isinstance(statements, (list, tuple)) or bound is None:
        return None
    candidates_text = [str(s).strip() for s in statements if s and str(s).strip()]
    usable = [s for s in candidates_text if _would_parse_as_deduction(adapter, s)]
    if len(usable) < 2:
        return None
    sub = getattr(adapter, "s", adapter)
    schema_nodes = []
    for statement in usable:
        g = mint_solve_deduction_goal(adapter, statement, mode=mode)
        _drive_to_resolution(adapter, g)
        at = sub.node(g)["attrs"]
        if at.get("status") != "resolved":
            continue
        result = _solve_caps(adapter).get(g, {}).get("result") or {}
        node = result.get("node")
        if node is not None:
            schema_nodes.append(node)
    if len(schema_nodes) < 2:
        return None
    from domains import problem_decomposition as pdec
    cand_shared = pdec.project_deduction_shared_attr(sub, schema_nodes)
    cand_complete = pdec.project_deduction_complete(sub, schema_nodes)
    return mint_solve_decompose_goal(adapter, [cand_shared, cand_complete], bound,
                                     max_exact_n=max_exact_n, refine_budget=refine_budget)


# =============================================================================
#  THE SEVEN RESOLVER CALLABLES
# =============================================================================
def solve_deduction(adapter, goal_node) -> None:
    """Thin invocation of `propositional_deduction.py`'s three mint_*
    entrypoints -- see `mint_solve_deduction_goal`'s docstring for the
    fixed-order "auto" ladder. Writes `form_used`/`schema_name`/`answer`/
    `note`/`status`; the full parsed dict (may include node-bearing fields)
    is stashed via `_stash_result`.

    AUTO-MODE LADDER ORDER (2026-08-15 bugfix -- see
    SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md Sec2). Previously the ladder tried
    `mint_logical_schema` (plain conditional/bare-universal, NO quantifier
    stripping) FIRST. Because "All X are Y"/"Some X is Y" are also
    grammatically valid bare-universal clauses on their own (subject = "All
    X"/"Some X"), the plain parser ALWAYS succeeded first on a
    leading-quantifier sentence, so `mint_universal_schema`/`mint_
    existential_premise` -- which correctly STRIP the quantifier word -- were
    never reached under mode="auto", silently degrading schema quality
    (`logical_all_philosophers_mortal`, unstripped, instead of `logical_
    universal_philosopher_mortal`, singularised) versus what an explicit
    `mode="universal"` call already produced.

    Fixed by trying the quantifier-aware parsers FIRST: universal ->
    existential -> conditional. This is provably safe for every
    NON-quantified statement, not merely a reordering gamble: `mint_
    universal_schema`/`mint_existential_premise` both delegate immediately to
    `_split_leading_quantifier` (propositional_deduction.py), which returns
    the honest `None` residual in O(1) -- one lowercase string comparison of
    the FIRST WORD against the held QuantifierLexicon, no reading-pipeline
    call at all -- whenever the statement has no recognised leading
    universal/existential quantifier word. A plain conditional ("If X is a
    fish, X can swim.") or an indefinite bare-universal ("A bird can fly.",
    "a"/"an" are deliberately NOT quantifier-lexicon members, see
    `_split_leading_quantifier`'s own docstring) therefore refuses BOTH
    quantifier-aware parsers immediately and falls through to
    `mint_logical_schema` exactly as before -- same function, same input,
    same result, byte-identical schema. Only a statement that genuinely
    starts with a recognised quantifier word takes a different path than
    before, and that path is the intentionally BETTER one."""
    from domains import propositional_deduction as pd
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    statement = at.get("statement") or at.get("raw") or ""
    mode = at.get("mode") or "auto"
    ladder = {
        "conditional": [("conditional", pd.mint_logical_schema)],
        "universal": [("universal", pd.mint_universal_schema)],
        "existential": [("existential", pd.mint_existential_premise)],
    }.get(mode, [("universal", pd.mint_universal_schema),
                 ("existential", pd.mint_existential_premise),
                 ("conditional", pd.mint_logical_schema)])
    last_reason = None
    for form_name, fn in ladder:
        result = fn(adapter, statement)
        if result.get("minted") or result.get("already"):
            sub.set_attr(goal_node, "form_used", form_name)
            sub.set_attr(goal_node, "schema_name", result.get("name"))
            sub.set_attr(goal_node, "answer", result.get("name"))
            chain = (result.get("parsed") or {}).get("chain")
            sub.set_attr(goal_node, "note", chain or
                         ("schema %r already held" % result.get("name")))
            sub.set_attr(goal_node, "status", "resolved")
            _stash_result(adapter, goal_node, result)
            return
        last_reason = result.get("reason")
    _wall(sub, goal_node, "solve_deduction:%s" % statement,
          last_reason or "no supported deduction form parsed this statement (honest residual)")


def solve_can_relax(adapter, goal_node) -> None:
    """Thin invocation of `can_native_orchestration.py` --
    `scoped_settle`(single start) or `multi_start_settle_and_pick_best`
    (k_starts>1), per the Goal's own `k_starts` attr (an explicit caller
    parameter, not a resolver decision -- see module docstring)."""
    from domains import can_native_orchestration as cno
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    mts = native.neighbours(goal_node, "targets_mt")
    if not mts:
        _wall(sub, goal_node, "solve_can_relax:no_targets_mt",
              "no targets_mt edge -- no Microtheory to relax")
        return
    mt = mts[0]
    k_starts = int(_at_num(at, "k_starts", 1))
    kwargs: dict = {}
    if at.get("max_steps") is not None:
        kwargs["max_steps"] = int(at["max_steps"])
    # can_native_orchestration.py calls native-only ops (run_rules_scoped,
    # mt_energy, mt_frustration_given_state) directly on whatever "substrate"
    # it is handed -- those exist only on the raw native handle (`native`),
    # not the thinner `substrate_rs.Substrate` wrapper (`sub`); see the
    # module docstring's node-reference-discipline note / RESULTS doc.
    if k_starts > 1:
        result = cno.multi_start_settle_and_pick_best(native, mt, k_starts=k_starts, **kwargs)
        basin = cno.native_audit_basin(native, mt)
        sub.set_attr(goal_node, "answer", {"frustration": float(result["frustration"]),
                                            "energy": float(basin["energy"]),
                                            "k_starts": k_starts})
        sub.set_attr(goal_node, "note",
                     "multi_start_settle_and_pick_best over %d restarts, "
                     "winning frustration=%r" % (k_starts, result["frustration"]))
        _stash_result(adapter, goal_node, result)
    else:
        steps = cno.scoped_settle(native, mt, **kwargs)
        basin = cno.native_audit_basin(native, mt)
        sub.set_attr(goal_node, "answer", {"steps": int(steps), "energy": float(basin["energy"]),
                                            "frustration": float(basin["frustration"])})
        sub.set_attr(goal_node, "note",
                     "scoped_settle (single start), %d progressing steps" % steps)
        _stash_result(adapter, goal_node, basin)
    sub.set_attr(goal_node, "status", "resolved")


def solve_can_exact(adapter, goal_node) -> None:
    """Thin invocation of `can_junction_tree.junction_tree_exact_settle` --
    an honest treewidth-bound refusal becomes a wall (`wall_kind:
    'treewidth_exceeds_bound'`), never a fabricated answer."""
    from domains import can_junction_tree as cjt
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    mts = native.neighbours(goal_node, "targets_mt")
    if not mts:
        _wall(sub, goal_node, "solve_can_exact:no_targets_mt",
              "no targets_mt edge -- no Microtheory to solve exactly")
        return
    mt = mts[0]
    bound = int(_at_num(at, "treewidth_bound", cjt.DEFAULT_TREEWIDTH_BOUND))
    max_exact_n = int(_at_num(at, "max_exact_n", cjt.DEFAULT_MAX_EXACT_TREEWIDTH_N))
    commit = True if at.get("commit") is None else bool(at.get("commit"))
    # native-only ops again (mt_energy/mt_frustration_given_state on commit) --
    # pass the raw native handle, not the wrapper.
    result = cjt.junction_tree_exact_settle(native, mt, treewidth_bound=bound,
                                            max_exact_n=max_exact_n, commit=commit)
    _stash_result(adapter, goal_node, result)
    if not result.get("attempted"):
        _wall(sub, goal_node,
              "solve_can_exact:mt=%r:tw=%r" % (mt, result.get("treewidth")),
              result.get("reason"), wall_kind="treewidth_exceeds_bound",
              treewidth=float(result.get("treewidth") or 0.0))
        return
    sub.set_attr(goal_node, "answer", {"energy": float(result["energy"]),
                                        "state": {int(k): float(v) for k, v in result["state"].items()}})
    sub.set_attr(goal_node, "treewidth", float(result["treewidth"]))
    sub.set_attr(goal_node, "note",
                 "junction_tree_exact_settle: EXACT global-minimum energy=%r, treewidth=%r"
                 % (result["energy"], result["treewidth"]))
    sub.set_attr(goal_node, "status", "resolved")


def solve_can_bp(adapter, goal_node) -> None:
    """Thin invocation of `can_native_bp.run_loopy_bp`. Always resolves
    (BP always returns a final belief/state, converged or not); `converged`
    is reported honestly in `note`, never silently dropped."""
    from domains import can_native_bp as cbp
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    mts = native.neighbours(goal_node, "targets_mt")
    if not mts:
        _wall(sub, goal_node, "solve_can_bp:no_targets_mt",
              "no targets_mt edge -- no Microtheory to run BP over")
        return
    mt = mts[0]
    combine = at.get("combine") or "max_product"
    max_rounds = int(_at_num(at, "max_rounds", cbp.DEFAULT_MAX_ROUNDS))
    epsilon = float(_at_num(at, "epsilon", cbp.DEFAULT_EPSILON))
    commit = bool(at.get("commit") or False)
    # can_native_bp.py reads external_field/identity_field/weight/temperature
    # via Term.evaluate (handle-agnostic) but this module's docstring commits
    # to reading LIVE graph state through the same handle throughout its own
    # sweep -- pass the raw native handle for consistency with the other two
    # CAN resolvers (no native-only call is strictly required here today, but
    # this keeps all three CAN resolvers on one uniform, always-safe handle).
    result = cbp.run_loopy_bp(native, mt, combine=combine, max_rounds=max_rounds,
                              epsilon=epsilon, commit=commit)
    _stash_result(adapter, goal_node, result)
    sub.set_attr(goal_node, "answer", {"final_state": {int(k): float(v)
                                        for k, v in result["final_state"].items()},
                                        "converged": bool(result["converged"])})
    sub.set_attr(goal_node, "note",
                 "run_loopy_bp(combine=%r): converged=%r after %d round(s)"
                 % (combine, result["converged"], result["rounds"]))
    sub.set_attr(goal_node, "status", "resolved")


def solve_reasoning_bridge(adapter, goal_node) -> None:
    """Thin invocation of `reasoning_can_bridge.py`'s two directions, chosen
    by the Goal's own explicit `direction` attr (a caller parameter, exactly
    the same shape `elevator_compute` reads `op`)."""
    from domains import reasoning_can_bridge as rcb
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    direction = at.get("direction")
    if direction == "deduction_to_can":
        entity, attr = at.get("entity"), at.get("attr")
        if not entity or not attr:
            _wall(sub, goal_node, "solve_reasoning_bridge:deduction_to_can:missing_entity_attr",
                  "deduction_to_can needs entity+attr")
            return
        result = rcb.apply_derived_fact_as_can_evidence(
            adapter, entity, attr, positive=bool(at.get("positive", True)),
            alpha=float(_at_num(at, "alpha", 1.0)))
        _stash_result(adapter, goal_node, result)
        sub.set_attr(goal_node, "answer", {"applied": bool(result.get("applied")),
                                            "entity": entity, "attr": attr})
        if result.get("applied"):
            sub.set_attr(goal_node, "note", "applied derived fact as CAN evidence "
                                             "(alpha=%r)" % result.get("alpha"))
            sub.set_attr(goal_node, "status", "resolved")
        else:
            _wall(sub, goal_node,
                  "solve_reasoning_bridge:deduction_to_can:%s:%s" % (entity, attr),
                  result.get("reason"))
    elif direction == "can_to_deduction":
        mts = native.neighbours(goal_node, "targets_mt")
        if not mts:
            _wall(sub, goal_node, "solve_reasoning_bridge:can_to_deduction:no_targets_mt",
                  "can_to_deduction needs a targets_mt edge")
            return
        results = rcb.can_state_as_predications(adapter, mts[0], t=int(at.get("t") or 0))
        _stash_result(adapter, goal_node, results)
        sub.set_attr(goal_node, "answer", {"n_predications": len(results)})
        sub.set_attr(goal_node, "note",
                     "ingested %d CAN-state predication(s) into deduction" % len(results))
        sub.set_attr(goal_node, "status", "resolved")
    else:
        _wall(sub, goal_node, "solve_reasoning_bridge:bad_direction:%r" % direction,
              "no recognised direction (%r) -- expected "
              "'deduction_to_can'/'can_to_deduction'" % direction)


def solve_analogical_promote(adapter, goal_node) -> None:
    """Thin invocation of `analogical_thinking.directional_hypothesis_for`
    (read-back of an ALREADY-DECIDED direction) +
    `propositional_deduction.mint_logical_schema_from_analogy` (the
    promotion). Neither function is edited; this resolver only sequences
    the read-then-promote and writes back the verdict."""
    from domains import analogical_thinking as at_mod
    from domains import propositional_deduction as pd
    sub, native, ag = _resolve(adapter)
    corrs = native.neighbours(goal_node, "targets_correspondence")
    if not corrs:
        _wall(sub, goal_node, "solve_analogical_promote:no_targets_correspondence",
              "no targets_correspondence edge")
        return
    corr = corrs[0]
    direction = at_mod.directional_hypothesis_for(sub, corr)
    result = pd.mint_logical_schema_from_analogy(adapter, direction)
    _stash_result(adapter, goal_node, {"direction": direction, "promotion": result})
    sub.set_attr(goal_node, "direction_verdict", direction.get("direction"))
    if result.get("minted") or result.get("already"):
        sub.set_attr(goal_node, "answer", result.get("name"))
        sub.set_attr(goal_node, "schema_name", result.get("name"))
        sub.set_attr(goal_node, "note",
                     "promoted DirectionalCorrespondence (direction=%s) into "
                     "knowledge_logical schema %r"
                     % (direction.get("direction"), result.get("name")))
        sub.set_attr(goal_node, "status", "resolved")
    else:
        _wall(sub, goal_node, "solve_analogical_promote:corr=%r" % corr, result.get("reason"))


def solve_decompose(adapter, goal_node) -> None:
    """Thin invocation of `problem_decomposition.decompose_problem` (race +
    decompose-or-refuse + optional bounded refinement). Candidates are read
    from the `solve_caps` stash (`mint_solve_decompose_goal`), never a Goal
    attr (they may carry raw NodeIDs, see module docstring)."""
    from domains import problem_decomposition as pdec
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    caps = _solve_caps(adapter).get(goal_node) or {}
    candidates = caps.get("candidates")
    if not candidates:
        _wall(sub, goal_node, "solve_decompose:no_candidates",
              "no candidate projections staged for this goal "
              "(solve_caps[goal]['candidates'] missing -- honest wall, "
              "not a fabricated decomposition)")
        return
    if at.get("bound") is None:
        _wall(sub, goal_node, "solve_decompose:no_bound",
              "no treewidth bound supplied for this decompose goal (honest wall)")
        return
    bound = int(at.get("bound"))
    max_exact_n = int(_at_num(at, "max_exact_n", 10))
    refine_budget = int(at.get("refine_budget") or 0)
    result = pdec.decompose_problem(sub, candidates, bound, max_exact_n=max_exact_n,
                                    refine_budget=refine_budget)
    _stash_result(adapter, goal_node, result)
    sub.set_attr(goal_node, "winner_projection", result.get("winner_projection"))
    sub.set_attr(goal_node, "treewidth", float(result.get("treewidth") or 0.0))
    if result.get("attempted"):
        sub.set_attr(goal_node, "answer", {"winner_projection": result.get("winner_projection"),
                                            "treewidth": float(result["treewidth"]),
                                            "n_bags": len(result.get("bags") or {})})
        sub.set_attr(goal_node, "note",
                     "decomposed via projection %r, treewidth=%r, %d bag(s)"
                     % (result.get("winner_projection"), result.get("treewidth"),
                        len(result.get("bags") or {})))
        sub.set_attr(goal_node, "status", "resolved")
    else:
        cand_names = ",".join(sorted(c.get("name", "?") for c in candidates))
        _wall(sub, goal_node,
              "solve_decompose:candidates=%s:bound=%d" % (cand_names, bound),
              result.get("reason"), wall_kind="treewidth_exceeds_bound")


SOLVE_RESOLVER_FUNCTIONS = {
    "solve_deduction": solve_deduction,
    "solve_can_relax": solve_can_relax,
    "solve_can_exact": solve_can_exact,
    "solve_can_bp": solve_can_bp,
    "solve_reasoning_bridge": solve_reasoning_bridge,
    "solve_analogical_promote": solve_analogical_promote,
    "solve_decompose": solve_decompose,
}

SOLVER_DISPATCH_SEED_ID = "solver_dispatch"


__all__ = [
    "SOLVE_RESOLVER_FUNCTIONS", "SOLVER_DISPATCH_SEED_ID",
    "mint_solve_deduction_goal", "mint_solve_can_relax_goal",
    "mint_solve_can_exact_goal", "mint_solve_can_bp_goal",
    "ensure_can_native_engine_loaded", "grow_can_network_from_text",
    "mint_solve_reasoning_bridge_goal", "mint_solve_reasoning_bridge_goal_from_text",
    "mint_solve_analogical_promote_goal", "mint_solve_analogical_promote_goal_from_text",
    "mint_solve_decompose_goal", "mint_solve_decompose_goal_from_text",
    "solve_deduction", "solve_can_relax", "solve_can_exact", "solve_can_bp",
    "solve_reasoning_bridge", "solve_analogical_promote", "solve_decompose",
]
