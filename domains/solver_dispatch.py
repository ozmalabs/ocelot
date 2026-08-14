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
    (conditional -> universal -> existential) and keeps the first that
    parses; an explicit mode skips straight to one parser. Mirrors
    `_split_leading_quantifier`'s own honest-residual discipline: the
    ladder is a fixed, inspectable order over EXISTING independent parsers
    (propositional_deduction.py's own three mint_* entry points), not a
    semantic decision about the statement's meaning."""
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


# =============================================================================
#  THE SEVEN RESOLVER CALLABLES
# =============================================================================
def solve_deduction(adapter, goal_node) -> None:
    """Thin invocation of `propositional_deduction.py`'s three mint_*
    entrypoints -- see `mint_solve_deduction_goal`'s docstring for the
    fixed-order "auto" ladder. Writes `form_used`/`schema_name`/`answer`/
    `note`/`status`; the full parsed dict (may include node-bearing fields)
    is stashed via `_stash_result`."""
    from domains import propositional_deduction as pd
    sub, native, ag = _resolve(adapter)
    at = sub.node(goal_node)["attrs"]
    statement = at.get("statement") or at.get("raw") or ""
    mode = at.get("mode") or "auto"
    ladder = {
        "conditional": [("conditional", pd.mint_logical_schema)],
        "universal": [("universal", pd.mint_universal_schema)],
        "existential": [("existential", pd.mint_existential_premise)],
    }.get(mode, [("conditional", pd.mint_logical_schema),
                 ("universal", pd.mint_universal_schema),
                 ("existential", pd.mint_existential_premise)])
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
    k_starts = int(at.get("k_starts") or 1)
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
    bound = int(at.get("treewidth_bound") or cjt.DEFAULT_TREEWIDTH_BOUND)
    max_exact_n = int(at.get("max_exact_n") or cjt.DEFAULT_MAX_EXACT_TREEWIDTH_N)
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
    max_rounds = int(at.get("max_rounds") or cbp.DEFAULT_MAX_ROUNDS)
    epsilon = float(at.get("epsilon") or cbp.DEFAULT_EPSILON)
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
            alpha=float(at.get("alpha") or 1.0))
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
    max_exact_n = int(at.get("max_exact_n") or 10)
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
    "mint_solve_reasoning_bridge_goal", "mint_solve_analogical_promote_goal",
    "mint_solve_decompose_goal",
    "solve_deduction", "solve_can_relax", "solve_can_exact", "solve_can_bp",
    "solve_reasoning_bridge", "solve_analogical_promote", "solve_decompose",
]
