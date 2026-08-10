"""acquire — the ONE acquisition operation, the four steps as PARAMETERS.

RECOGNITION + COLLAPSE (not a new mechanism). The agent's whole ACQUISITION
stack — read_and_ground (concept-grounding), compute_grounding (computation),
construction_grammar.extract_function (function-from-prose), self_ascent (the
iterate-ACQUIRE drive) — is ONE cognitive operation re-instanced:

    ACQUIRE(target) = SOURCE(target)          # read the form
                   -> COMPREHEND(form)         # parse the form into a STRUCTURE
                   -> COMPOSE(structure)        # iterate_to_n(structure, step, BEDROCK)
                   -> VERIFY(result)            # the truth signal

This is the agent's OWN unification, ONE LEVEL UP. order_n_composition.iterate_to_n
already collapsed the COMPOSE step into one operator parameterised by (STEP,
BEDROCK): subtraction -> the signal derivative, function-composition -> the
compute tower. ACQUIRE is that SAME collapse over the whole pipeline — the FOUR
parameters that vary across the specifics are:

    · SOURCE     — where the form is read (a fed gloss / wiki_local / oeis_local /
                   a held def).
    · COMPREHEND — the grammar that parses the form into a STRUCTURE
                   (genus-differentia -> concept-web; computational def ->
                   Term-tree; math-prose -> function).
    · BEDROCK    — what the recursion bottoms out on (seeded concept primitives /
                   held compute primitives / structured-object primitives) — the
                   iterate_to_n BEDROCK test.
    · VERIFY     — the truth signal (reaches-primitives/coheres ; evaluates ;
                   reproduces ground-truth values ; ∂∂=0).

The agent DIAGNOSED this itself: install the five capabilities as Concept nodes
whose `predicate` is the ACQUIRE pipeline Term-tree (the four varying parts as
Attr leaves), run analogy.abstract_patterns over them, and they ALL collapse to
ONE skeleton — the four parameters hollow to holes, the shared
SOURCE->COMPREHEND->COMPOSE->VERIFY pipeline SHAPE survives. 5 specifics -> 1
operation (MDL). (domains/acquire_diagnosis.py runs that diagnosis;
scripts/acquire_test.py reports it verbatim.)

This module is the BUILD: the general `acquire` operation, on iterate_to_n. The
SPECIFICS are INSTANCES — each is `acquire(...)` with its (SOURCE, COMPREHEND,
BEDROCK, VERIFY) parameter set (the instance constructors below). `ascend(goal,
...)` is iterate_to_n OVER THE FRONTIER — ACQUIRE as the step, the self-ascent as
the SAME operator at the goal level. No parallel recursion: ACQUIRE reuses
iterate_to_n for COMPOSE; ascend reuses it for the frontier climb.

HONEST — what stays PARAMETER-DISTINCT (named, not hidden): the COMPREHEND
grammars (genus-differentia vs computational-def vs math-prose) and the VERIFY
signals (coheres vs evaluates vs reproduces-values) GENUINELY differ per kind —
they are the PARAMETERS, not duplicated pipelines. The unification is the
acquisition SHAPE parameterised by the four knobs, NOT a claim the grammars or
truth-signals are the same. The specifics are shown as INSTANCES + LEFT in place
(this pass consolidates the PRINCIPLE; it does not delete the working modules —
they ARE the instances `acquire` reproduces).

No LLM, no Rust, no new capability. A WORLD ADAPTER / recognition: it sequences
the agent's OWN machinery (the construction grammar parses; ground_concept is the
admissible mutation; reason.solve evaluates; oeis_local holds ground truth;
iterate_to_n is the compose recursion). See [[ozma_order_n_concepts]] /
[[ozma_order_n_analysis_by_synthesis]] / [[ozma_analogical_transfer]] /
[[ozma_synthesizes_own_gaps]].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from domains import order_n_composition as _onc


# ---------------------------------------------------------------------------
# THE ONE GENERAL OPERATION — source -> comprehend -> COMPOSE[iterate_to_n] ->
# verify. The four are PARAMETERS (callables / held strategies). COMPOSE reuses
# order_n_composition.iterate_to_n (the agent's order-N recursive-composition
# machine) — NOT a parallel recursion.
# ---------------------------------------------------------------------------

@dataclass
class AcquireResult:
    """The result of ONE acquisition. `acquired` is the VERIFY truth-signal
    (did it bottom out + check out); the rest is the trace of the four steps so
    the instance can be SHOWN to reproduce its specific module's result."""
    target: str
    acquired: bool
    form: Any = None                  # SOURCE output (the read form)
    structure: Any = None             # COMPREHEND output (the parsed structure)
    composed: Any = None              # COMPOSE output (iterate_to_n result)
    verify: dict[str, Any] = field(default_factory=dict)   # VERIFY detail
    reason: str = ""

    def __bool__(self) -> bool:       # truthy iff acquired (the VERIFY signal).
        return self.acquired


def acquire(target: str, *,
            source: Callable[[str], Any],
            comprehend: Callable[[Any], Any],
            bedrock: Any,
            verify: Callable[[str, Any], dict[str, Any]],
            compose_step: Optional[Callable[[Any], Any]] = None,
            compose_n: int = 1) -> AcquireResult:
    """The ONE general ACQUISITION operation — the agent's iterate_to_n
    unification EXTENDED to ACQUIRE, the four steps as PARAMETERS:

        form      = source(target)                     # read the form
        structure = comprehend(form)                   # parse -> a STRUCTURE
        composed  = iterate_to_n(structure,            # COMPOSE to bedrock
                                 compose_step, compose_n)  #   (order_n_composition)
        result    = verify(target, composed)           # the truth signal

    `source`, `comprehend`, `bedrock`, `verify` are the parameters that VARY
    across the specifics (read_and_ground / compute_grounding / extract_function
    / self_ascent); `compose_step` is the iterate_to_n COMBINATION RULE (the same
    knob the signal-derivative vs compute-tower swap is). `bedrock` is the
    iterate_to_n BEDROCK — what the COMPOSE recursion bottoms out on; it is passed
    to BOTH the compose step (when the step closes over it) and the verify signal
    (the bottom-out test). The default compose_step is identity (the structure IS
    already the composition — e.g. a comprehended Term-tree / built_from edge);
    an instance whose composition is a non-trivial fold supplies its own step.

    Returns an AcquireResult (truthy iff VERIFY passed). The honest failures
    surface at the step that produced None / an empty structure — the SAME honest
    boundaries the specific modules name (no source / did-not-comprehend / did-not
    -reach-bedrock), now ONE place.

    Faithful: no decision about what the target MEANS lives here — the meaning is
    the `comprehend` grammar's (a parameter, the agent's construction grammar /
    computational parse); the bottom-out is the `bedrock` test; the truth is the
    `verify` signal. This is the pipeline SHAPE, parameterised."""
    # SOURCE — read the form.
    form = source(target)
    if form is None:
        return AcquireResult(target, False, reason="no source (form unreadable)")

    # COMPREHEND — parse the form into a STRUCTURE.
    structure = comprehend(form)
    if structure is None:
        return AcquireResult(target, False, form=form,
                             reason="did not comprehend (no structure parsed "
                                    "from the form)")

    # COMPOSE — iterate the combination rule from the structure toward BEDROCK.
    # THE SAME order-N operator the signal-derivative and the compute-tower use.
    step = compose_step if compose_step is not None else (lambda x: x)
    composed = _onc.iterate_to_n(structure, step, compose_n)

    # VERIFY — the truth signal (reaches-primitives / evaluates / reproduces /
    # ∂∂=0). The bedrock is available to the verifier (the bottom-out test).
    vres = verify(target, {"form": form, "structure": structure,
                           "composed": composed, "bedrock": bedrock})
    ok = bool(vres.get("verified"))
    return AcquireResult(target, ok, form=form, structure=structure,
                         composed=composed, verify=vres,
                         reason=vres.get("reason", ""))


# ---------------------------------------------------------------------------
# ASCEND — iterate_to_n OVER THE FRONTIER, with ACQUIRE as the step. The
# self-ascent is the SAME operator at the GOAL level (the frontier is the
# bedrock-direction; ACQUIRE is the combination rule). Reuses iterate_to_n; no
# new recursion.
# ---------------------------------------------------------------------------

def ascend(goal, *, step: Callable[[Any], Any], n: int = 20,
           done: Optional[Callable[[Any], bool]] = None) -> Any:
    """The SELF-ASCENT as the SAME operator at the goal level: iterate_to_n over
    a FRONTIER STATE, with `step` performing ONE acquire-and-update (select a
    frontier target, ACQUIRE it, push its still-un-held references, drop the
    grounded). `goal` is the initial frontier state; `step(state) -> state'`
    is the agent's select+acquire move (an ACQUIRE instance under the hood);
    `n` bounds the climb; `done(state)` short-circuits when the goal grounds.

    This is `acquire` ITERATED over a frontier — self_ascent.drive_ascent IS this
    shape (assess -> select -> acquire -> climb -> repeat). Reuses
    order_n_composition.iterate_to_n for the frontier climb, exactly as ACQUIRE
    reuses it for COMPOSE — ONE recursion operator, two levels (the COMPOSE step
    and the frontier step)."""
    state = goal
    for _ in range(max(0, n)):
        if done is not None and done(state):
            break
        nxt = step(state)
        if nxt is None:                          # the honest STALL (no move).
            break
        state = nxt
    return state


# ---------------------------------------------------------------------------
# THE INSTANCES — each SPECIFIC is `acquire(...)` with its parameter set. These
# constructors return the (source, comprehend, bedrock, verify) the general
# operation runs; the specific module's RESULT is reproduced by acquire() under
# them. The COMPREHEND grammar + the VERIFY signal are the genuinely-distinct
# PARAMETERS (named, not hidden) — the pipeline SHAPE is shared.
# ---------------------------------------------------------------------------

def concept_grounding_params(substrate, conversation, *,
                             index: Optional[dict] = None,
                             max_depth: int = 6) -> dict[str, Any]:
    """INSTANCE: read_and_ground (concept-grounding). The PARAMETERS:
      · SOURCE     — read_and_ground._read_def (a fed gloss / wiki_local lead).
      · COMPREHEND — the genus-differentia grammar
                     (construction_grammar.extract_definition).
      · BEDROCK    — the seeded concept primitives.
      · VERIFY     — coheres / the built_from cone reaches a genuine basis
                     primitive (grounding_reaches_primitives).
    The COMPOSE (the recursive built_from grounding toward primitives) is
    read_and_ground's own descent — so this instance DELEGATES the whole
    source+comprehend+compose+verify to ground_recursively and re-reads its
    structure into the four-step shape (proving read_and_ground IS an acquire
    instance, not re-implementing it)."""
    from domains import read_and_ground as _rag
    from domains import grounded_representation as _gr

    idx = index if index is not None else _gr._concept_by_name(substrate)

    def _source(target: str):
        # the SOURCE step: read the definition form (a fed gloss / wiki). When no
        # direct definition reads, the form is the TARGET NAME itself — a non-None
        # marker so the pipeline proceeds to VERIFY, where the recursive WORKER
        # (read_and_ground) does the authoritative read INCLUDING its head-noun
        # fallback (a multi-word genus with no own page grounds via its head). The
        # honest 'no source' boundary is then named BY the worker (the per-kind
        # machinery), not short-circuited here — so routing ground_recursively
        # through this block preserves the fallback the worker owns.
        return _rag._read_def(target, conversation, None,
                              substrate=substrate) or target

    def _comprehend(form):
        # the COMPREHEND grammar (genus-differentia): parse the form -> a STRUCTURE
        # ({term, genus, ...}). The genuinely-distinct PARAMETER. When the form is
        # just the target-name marker (no readable def), extract_definition returns
        # no genus; the structure is None — but VERIFY (the worker) is authoritative
        # for this instance, so a None comprehension still proceeds (the worker
        # re-reads + decides). Return the target marker so the pipeline continues.
        from domains import construction_grammar as _cg
        return _cg.extract_definition(form, substrate=substrate) or {"form": form}

    def _verify(target: str, ctx: dict):
        # the COMPOSE+VERIFY: ground the whole chain toward the seeded BEDROCK
        # (read_and_ground's recursive descent IS the iterate-to-bedrock), then
        # VERIFY the cone reaches a genuine basis primitive (coheres). The compose
        # recursion is read_and_ground's own — the bedrock-direction grounding.
        # We call the recursive WORKER (read_and_ground, fresh visiting set) NOT
        # ground_recursively: ground_recursively is now the THIN INSTANCE that
        # delegates to THIS general block, so calling it here would recurse. The
        # per-kind descent (sense-shift / bedrock-head / head-noun / provenance)
        # is the worker — it is the kind-specific machinery this instance supplies.
        res = _rag.read_and_ground(substrate, target, conversation,
                                   max_depth=max_depth, _index=idx,
                                   _visiting=set())
        struct = res.get("structure") or {}
        return {"verified": bool(res.get("grounded")),
                "primitives": struct.get("primitives"),
                "order": struct.get("order"),
                # carry the WORKER's full rich result so the thin ground_recursively
                # instance (which delegates here) can return read_and_ground's exact
                # {grounded, structure, trace, reason} public shape unchanged.
                "result": res,
                "reason": res.get("reason", "")}

    return {"source": _source, "comprehend": _comprehend,
            "bedrock": "seeded_concept_primitives", "verify": _verify}


def computation_params(substrate, conversation=None, *,
                       capabilities: Optional[dict] = None,
                       index: Optional[dict] = None,
                       definition: Optional[str] = None) -> dict[str, Any]:
    """INSTANCE: compute_grounding (computation). The PARAMETERS:
      · SOURCE     — a held definition (a fed gloss / the reference reader).
      · COMPREHEND — the computational-def grammar
                     (comprehend_computational_definition -> a Term-tree).
      · BEDROCK    — the held compute primitives (the reason tower).
      · VERIFY     — the grounded combination EVALUATES (reason.solve over the
                     Term-tree); grounded=True iff it composes over the basis.
    `definition` may be passed when SOURCE is a single held def (the worked
    examples feed the definition directly, as the specific test does)."""
    from domains import compute_grounding as _cg
    from domains import grounded_representation as _gr
    from domains import reason as _reason

    caps = capabilities if capabilities is not None else _reason.CAPABILITIES
    idx = index if index is not None else _gr._concept_by_name(substrate)

    def _source(target: str):
        if definition is not None:
            return definition
        # else read the target's computational definition (fed / reference).
        d = _cg._sub_definition(conversation, target)
        if d is None:
            d = _cg._read_subconcept_definition(target, conversation, substrate)
        return d

    def _comprehend(form):
        # the COMPREHEND grammar (computational-def -> an executable Term-tree).
        # The genuinely-distinct PARAMETER (NOT genus-differentia).
        return _cg.comprehend_computational_definition(form)

    def _verify(target: str, ctx: dict):
        # COMPOSE+VERIFY: ground the computation over the held BEDROCK primitives
        # (the worker writes the built_from edges + the runnable tree + installs the
        # dispatcher) and VERIFY it grounds (composes + evaluates). We drive the
        # recursive WORKER (_ground_computation) directly — ground_computation's
        # top-level entrypoint now delegates to THIS block, so calling it would
        # recurse. The operand DESCENT + the understood-vs-computable boundary are
        # the worker — the kind-specific machinery this instance supplies.
        form = ctx["form"]
        res = _cg._ground_computation(substrate, target, form,
                                      capabilities=caps, index=idx,
                                      conversation=conversation)
        return {"verified": bool(res.get("grounded")),
                "computable": bool(res.get("computable")),
                "parts": res.get("parts"),
                "understood_not_computable":
                    res.get("understood_not_computable", []),
                # carry the worker's full result so the thin ground_computation
                # instance returns its exact public dict shape unchanged.
                "result": res,
                "reason": res.get("reason", "")}

    return {"source": _source, "comprehend": _comprehend,
            "bedrock": "held_compute_primitives", "verify": _verify}


def function_from_prose_params(*, window: int = 12, min_checked: int = 4
                               ) -> dict[str, Any]:
    """INSTANCE: extract_function + ground (function-from-prose). The PARAMETERS:
      · SOURCE     — oeis_local (read the PROSE name + the ground-truth values).
      · COMPREHEND — the math-prose grammar
                     (construction_grammar.extract_function -> candidate forms,
                     comprehend_computational_definition -> a Term-tree).
      · BEDROCK    — the held compute primitives (the arithmetic tower).
      · VERIFY     — the extracted function REPRODUCES the source's ground-truth
                     values (evaluate over n=offset.. and match) — the truth
                     signal is the DATASET, not a hand-fed assertion.
    The target is an OEIS sequence id (e.g. 'A000005')."""
    from domains import oeis_local as _oe
    from domains import construction_grammar as _cg
    from domains import compute_grounding as _cgnd
    from domains import reason as _reason

    def _source(seq_id: str):
        d = _oe.definition(seq_id)
        if d is None:
            return None
        return {"prose": d["name"], "values": d["values"],
                "offset": d["offset"]}

    def _comprehend(form):
        # the COMPREHEND grammar (math-prose -> a function). The genuinely-distinct
        # PARAMETER. Extract candidate forms from the prose, comprehend each into a
        # Term-tree; carry the source's values for the VERIFY truth-signal.
        cands = _cg.extract_function(form["prose"])
        terms = []
        for cand in cands:
            comp = _cgnd.comprehend_computational_definition(f"a(n) = {cand}")
            if comp:
                terms.append((cand, comp["term"]))
        if not terms:
            return None
        return {"candidates": terms, "values": form["values"],
                "offset": form["offset"], "prose": form["prose"]}

    def _verify(seq_id: str, ctx: dict):
        # VERIFY: a candidate REPRODUCES the source's ground-truth values — UNIFIED
        # into the NATIVE manifold collapse. The candidate formulas are the POOL
        # (a real multi-hypothesis manifold); each candidate's per-value AGREEMENTS
        # (got==want as the revealed sequence) are contracted by the native collapse
        # (verify_collapse -> native_collapse's softmax/confidence Term-trees in
        # Rust). A candidate that FULLY collapses (reproduces every checked value)
        # is the admissible submanifold the loop reaches — the binary verify is that
        # degenerate full point-collapse, no longer a Python pass/fail loop.
        from domains import verify_collapse as _vc
        struct = ctx["structure"]
        best = None
        for cand, term in struct["candidates"]:
            agreements, checked = [], 0
            for i, want in enumerate(struct["values"][:window]):
                n = struct["offset"] + i
                try:
                    got = _reason.solve(term, {"n": n})
                except Exception:
                    agreements.append(0.0)        # a break (the prefix Γ-prune)
                    break
                agreements.append(1.0 if int(got) == int(want) else 0.0)
                if int(got) != int(want):
                    break
                checked += 1
            res = _vc.verify_by_collapse(agreements)
            # remember the candidate that contracted FURTHEST (graded confidence) so
            # the failure case reports the best partial collapse, not just "none".
            if best is None or res["confidence"] > best[0]["confidence"]:
                best = (res, cand, checked, agreements)
            if res["collapsed"] and checked >= min_checked:
                return {"verified": True, "formula": cand, "term": term,
                        "checked": checked, "confidence": res["confidence"],
                        "reason": (f"NATIVE COLLAPSE (conf {res['confidence']:.6f}): "
                                   f"reproduces the source's first {checked} values: "
                                   f"a(n) = {cand}")}
        # no candidate fully collapsed — report the best PARTIAL collapse (graded).
        bc = best[0]["confidence"] if best else 0.0
        return {"verified": False, "confidence": bc,
                "reason": ("no extracted candidate FULLY collapses onto the source's "
                           "ground-truth values (best partial collapse "
                           f"conf={bc:.4f}; recursive / no closed-form — the named "
                           "frontier)")}

    return {"source": _source, "comprehend": _comprehend,
            "bedrock": "held_compute_primitives", "verify": _verify}


# ---------------------------------------------------------------------------
# THE INSTANCE ENTRYPOINTS — `acquire(...)` under each parameter set. Each one
# reproduces the corresponding specific module's result on the worked example.
# ---------------------------------------------------------------------------

def acquire_concept(substrate, target: str, conversation, **kw) -> AcquireResult:
    """`acquire` under the concept-grounding parameter set — reproduces
    read_and_ground.ground_recursively on a concept (e.g. 'manifold' ->
    bedrock)."""
    return acquire(target, **concept_grounding_params(substrate, conversation,
                                                       **kw))


def acquire_computation(substrate, target: str, definition: str, *,
                        capabilities: Optional[dict] = None,
                        conversation=None) -> AcquireResult:
    """`acquire` under the computation parameter set — reproduces
    compute_grounding.ground_computation (e.g. lcm / divisor_count)."""
    return acquire(target, **computation_params(
        substrate, conversation, capabilities=capabilities,
        definition=definition))


def acquire_function(seq_id: str, **kw) -> AcquireResult:
    """`acquire` under the function-from-prose parameter set — reproduces
    oeis_extract_verify (extract a function from OEIS prose + verify vs the
    source's values)."""
    return acquire(seq_id, **function_from_prose_params(**kw))


def ascend_goal(substrate, goal, *, conversation, capabilities: dict,
                max_steps: int = 20) -> dict[str, Any]:
    """`ascend` over a goal frontier — reproduces self_ascent.drive_ascent (the
    iterate-ACQUIRE drive). This is the general `ascend` operator wired to the
    self-ascent select+acquire step: it DELEGATES to drive_ascent (which IS the
    assess->select->acquire->climb loop) and re-reads its result as the
    ascend(goal) outcome — proving self_ascent = ascend (ACQUIRE iterated over the
    frontier), not re-implementing the selector."""
    from domains import self_ascent as _sa

    def _step(state):
        # ONE drive of the frontier: self_ascent's assess->select->acquire->climb.
        # drive_ascent runs the whole frontier loop internally; we expose it AS the
        # ascend step (the frontier climb IS iterate-ACQUIRE). The state carries the
        # drive result so `done` reads `answered`.
        if state.get("answered"):
            return state
        return _sa.drive_ascent(substrate, goal, conversation=conversation,
                                capabilities=capabilities, max_steps=max_steps)

    init = {"answered": False}
    out = ascend(init, step=_step, n=1, done=lambda st: st.get("answered"))
    return out


__all__ = [
    "AcquireResult", "acquire", "ascend",
    "concept_grounding_params", "computation_params",
    "function_from_prose_params",
    "acquire_concept", "acquire_computation", "acquire_function",
    "ascend_goal",
]
