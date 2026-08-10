"""self_ascent — the agent DRIVES ITS OWN ASCENT.

A closed autonomous loop where the AGENT picks what to learn next (from its own
gap-synthesis / order-N selector), ACQUIRES it (read -> ground -> compute, the
unified order-N descent), CLIMBS (order N -> N+1), and repeats toward a GOAL,
WITHOUT a human feeding the intermediate targets. The agent already holds every
piece; this module is the LOOP SHELL ONLY — every DECISION (which target, why) is
the agent's own machinery:

  · ASSESS  — the FRONTIER is the agent's set of un-grounded encountered concepts
              (the goal's content fillers via the coherence gap-finder
              domains/coherence_graph.content_fillers, plus the un-held references
              of every definition it reads as it descends).
  · SELECT  — the agent picks the NEXT target by its OWN selector: it reads each
              frontier concept's definition, comprehends its REFERENCES
              (compute_grounding.comprehend_computational_definition), and ranks by
              GROUNDABILITY — the concept whose references are ALL already held is
              CLOSEST TO BEDROCK, so the chain can bottom out there first (the same
              order-N "ground the lower-order / closer-to-bedrock pieces first"
              principle synthesize_gaps / the order-N generator encode). The WHY of
              each pick is produced by this machinery, NOT a hand-coded priority.
  · ACQUIRE — the unified order-N descent: compute_grounding.ground_computation
              with a SINGLE-STEP budget (_max_depth=0) so the loop — not an
              opaque inner recursion — drives every hop. A concept grounds iff its
              references are held; a still-un-held reference is ADDED to the
              frontier (the descent the agent itself sequences).
  · CLIMB+REPEAT — the order grows (order_n_composition records N -> N+1 on each
              grounded concept); loop until the GOAL's concept grounds (ANSWERED)
              OR no frontier concept is acquirable (the honest named BOUNDARY,
              stalled_at).

The loop SHELL is mechanical (call selector -> call acquire -> update frontier);
it is a WORLD ADAPTER (CLAUDE.md): no `if` decides what a concept MEANS, no LLM
chooses, no per-target Python. The meaning is the construction grammar / the
computational parse (graph data); the ground is an admissible mutation; the order
is order_n_composition; the SELECTION is the order-N / groundability machinery.

HONEST / COARSE (named, not hidden):
  · the FRONTIER is the encountered-references set (the goal seeds a small one);
  · the SELECTOR is the EXISTING order-N / groundability machinery (rank by
    how-close-to-bedrock = how-many-references-already-held), NOT a learned policy;
  · the descent climbs a few number-theory tiers, NOT research math — at the
    research boundary (cobordism -> boundary_operator, an op with no computable
    realization) it stalls and NAMES the wall (stalled_at). HLE is unchanged.

See [[ozma_order_n_concepts]] / [[ozma_order_n_analysis_by_synthesis]] /
[[ozma_synthesizes_own_gaps]] / [[ozma_meta_abilities_are_leverage]].
"""
from __future__ import annotations

from typing import Any, Optional

from domains import compute_grounding as _cg
from domains import grounded_representation as _gr
from domains import order_n_composition as _onc
from domains import read_and_ground as _rag
from domains import coherence_graph as _cohg


# ---------------------------------------------------------------------------
# ASSESS — read a frontier concept's definition + comprehend its REFERENCES.
# Pure graph/IO read of the agent's own machinery; no decision about meaning.
# ---------------------------------------------------------------------------

def _name_norm(s: str) -> str:
    return _rag._name_norm(s)


def _read_definition(substrate, name: str, conversation) -> Optional[str]:
    """READ a frontier concept's COMPUTATIONAL definition through the SAME reader
    the descent uses (the in-process feed / reference reader). Mechanical I/O."""
    t = _cg._sub_definition(conversation, name)
    if t is None:
        t = _cg._read_subconcept_definition(name, conversation, substrate)
    return t


def _references_of(definition: str) -> Optional[list[str]]:
    """COMPREHEND a definition and return the OPERAND concepts it composes over
    (its references). None if the definition does not comprehend as a computation
    over the held basis (so the selector treats it as not-yet-groundable). The
    comprehension is compute_grounding's parse — graph data, not a decision."""
    comp = _cg.comprehend_computational_definition(definition)
    if comp is None:
        return None
    return list(comp.get("parts", []))


def _unheld_refs(substrate, refs: list[str], caps: dict) -> list[str]:
    """The references that are NOT already held (neither a held computable
    primitive nor a grounded concept) — the deeper-frontier this concept depends
    on. A reference held as a computable primitive OR grounded as a concept is
    NOT a gap. Pure graph read."""
    out = []
    for r in refs:
        if _cg._is_held_primitive(r, caps):
            continue
        cid = _gr._find_concept(substrate, _name_norm(r))
        if cid is not None and _rag._is_held(substrate, _name_norm(r)):
            continue
        out.append(r)
    return out


def _is_grounded(substrate, name: str, caps: dict) -> bool:
    """Is `name` grounded — a held computable primitive OR a grounded concept the
    agent already holds (its cone reaches bedrock)? The loop's bottom-out test."""
    if _cg._is_held_primitive(name, caps):
        return True
    n = _name_norm(name)
    cid = _gr._find_concept(substrate, n)
    return cid is not None and _rag._is_held(substrate, n)


def _is_acquirable(substrate, name: str, conversation, caps: dict) -> bool:
    """Is `name` something the agent CAN acquire as a computation — already
    grounded, OR its definition READS and COMPREHENDS as a computation over the
    held basis? A reference that is unreadable, or readable but does NOT
    comprehend as a computation (a prose/research definition with no equation),
    is NOT acquirable — it is the wall. Pure machinery read."""
    if _is_grounded(substrate, name, caps):
        return True
    definition = _read_definition(substrate, name, conversation)
    if definition is None:
        return False
    return _references_of(definition) is not None


# ---------------------------------------------------------------------------
# SELECT — the agent's OWN selector ranks the frontier.
#
# The principle is order-N / synthesize_gaps': ground the CLOSER-TO-BEDROCK pieces
# first so the chain can bottom out. A concept's distance-to-bedrock is read off
# its definition: the count of references it depends on that are NOT yet held. A
# concept with ZERO un-held references is directly groundable NOW (order-1 over the
# held basis); one with un-held references must wait for those to ground first
# (a higher tier). So the selector picks the frontier concept with the FEWEST
# un-held references — the same "ground the lower-order pieces first" move the
# order-N machinery encodes, applied live. The WHY is this count.
# ---------------------------------------------------------------------------

def _assess_frontier(substrate, frontier: list[str], conversation,
                     caps: dict) -> list[dict[str, Any]]:
    """For each frontier concept, READ its definition and COMPREHEND its
    references, returning an assessment the selector ranks:
        {target, definition, refs, unheld_refs, n_unheld, readable, comprehends}.
    Pure machinery read — the agent assessing its own un-grounded frontier."""
    out = []
    for name in frontier:
        definition = _read_definition(substrate, name, conversation)
        refs = _references_of(definition) if definition else None
        unheld = (_unheld_refs(substrate, refs, caps)
                  if refs is not None else [])
        out.append({
            "target": name,
            "definition": definition,
            "refs": refs,
            "unheld_refs": unheld,
            "n_unheld": (len(unheld) if refs is not None else None),
            "readable": definition is not None,
            "comprehends": refs is not None,
        })
    return out


def _select(assessments: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The AGENT'S selector: pick the next target = the readable, comprehensible
    frontier concept CLOSEST TO BEDROCK (the fewest un-held references), so the
    chain bottoms out. Among equals, a stable order. Returns the chosen assessment
    augmented with `why` (the machinery's reason), or None if nothing is
    acquirable (every frontier concept is unreadable / un-comprehensible — the
    stall). This IS the order-N "ground the closer-to-bedrock / lower-order pieces
    first" principle, read live off each concept's reference count."""
    groundable = [a for a in assessments if a["readable"] and a["comprehends"]]
    if not groundable:
        return None
    # rank: fewest un-held references first (closest to bedrock), then by name for
    # determinism. n_unheld == 0 -> directly groundable now (the bottom of the
    # chain); n_unheld > 0 -> a higher tier, deferred until its refs ground.
    groundable.sort(key=lambda a: (a["n_unheld"], a["target"]))
    chosen = dict(groundable[0])
    n = chosen["n_unheld"]
    if n == 0:
        chosen["why"] = ("closest-to-bedrock: ALL references already held "
                         "-> directly groundable now (order-N: ground the "
                         "lower-order pieces first so the chain bottoms out)")
    else:
        chosen["why"] = (
            f"fewest un-held references ({n}) among the frontier -> the agent's "
            f"order-N selector defers it until its references "
            f"{chosen['unheld_refs']} ground (closer-to-bedrock first)")
    return chosen


# ---------------------------------------------------------------------------
# ACQUIRE — the unified order-N descent, ONE STEP (the loop drives the recursion).
# ---------------------------------------------------------------------------

def _acquire(substrate, target: str, definition: str, conversation,
             caps: dict) -> dict[str, Any]:
    """ACQUIRE a target by the unified order-N descent — compute_grounding.
    ground_computation with a SINGLE-STEP budget (_max_depth=0) so the LOOP, not
    an opaque inner recursion, drives every hop. Grounds iff the references are
    held; records the ORDER (N -> N+1) via order_n_composition. Returns
    {grounded, order, parts, reason, understood, unheld_after}."""
    res = _cg.ground_computation(substrate, target, definition,
                                 capabilities=caps, conversation=conversation,
                                 _depth=0, _max_depth=0)
    order = None
    if res.get("grounded"):
        cid = _gr._find_concept(substrate, _name_norm(target))
        if cid is not None:
            try:
                order = _onc.order_from_cone(substrate, cid)
            except Exception:
                order = None
    return {
        "grounded": bool(res.get("grounded")),
        "computable": bool(res.get("computable")),
        "understood": bool(res.get("understood")),
        "order": order,
        "parts": res.get("parts", []),
        "reason": res.get("reason", ""),
        "understood_not_computable": res.get("understood_not_computable", []),
    }


# ---------------------------------------------------------------------------
# THE DRIVE LOOP — assess -> SELECT (agent) -> acquire -> climb -> repeat.
# ---------------------------------------------------------------------------

def seed_frontier(frame: dict[str, Any]) -> list[str]:
    """Seed the FRONTIER from the GOAL: the goal frame's content fillers (the
    coherence gap-finder's un-grounded concepts). A pure read of the frame — the
    same fillers coherence_graph judges grounded/ungrounded."""
    return [_name_norm(f) for f in _cohg.content_fillers(frame)]


def drive_ascent(substrate, goal, *, conversation, capabilities: dict,
                 max_steps: int = 20) -> dict[str, Any]:
    """The AGENT DRIVES its own ascent toward `goal`.

    `goal` is either a comprehended frame (dict) whose content fillers seed the
    frontier, or a concept-name (str) / list of concept-names to ground. The loop:

      1. ASSESS  — seed the frontier from the goal; assess each frontier concept
                   (read its definition, comprehend its references).
      2. SELECT  — the agent's selector picks the next target (closest-to-bedrock).
      3. ACQUIRE — the unified order-N descent grounds it (single step); record
                   the order; add the definition's still-un-held references to the
                   frontier; drop the now-grounded target.
      4. CLIMB+REPEAT — until every goal concept grounds (ANSWERED) OR no frontier
                   concept is acquirable (STALLED — the honest named boundary).

    Returns {steps, acquired, answered, frontier, stalled_at, orders, goal_concepts}.
    Every SELECTION + ACQUISITION is the agent's machinery; the shell is mechanical.

    The FRONTIER ITERATE is acquire.ascend (iterate_to_n OVER the frontier, with
    ACQUIRE as the step) — the ONE bounded-iteration operator, NOT a private
    while-loop. `_ascent_step` is the agent's per-hop machinery (assess -> SELECT ->
    ACQUIRE -> update the frontier / name the boundary); ascend drives it, bounds it
    at `max_steps`, and short-circuits when the goal grounds or the climb stalls.
    The duplicated iteration shell is GONE; what stays is the genuinely per-kind
    step (the order-N selector + the unified descent + the named walls).
    """
    from domains import acquire as _acq
    caps = capabilities

    # Seed the goal's concepts + the initial frontier (the agent's own gap-finder).
    if isinstance(goal, dict):
        goal_concepts = seed_frontier(goal)
    elif isinstance(goal, str):
        goal_concepts = [_name_norm(goal)]
    else:
        goal_concepts = [_name_norm(g) for g in goal]

    def _goal_done(state) -> bool:
        return all(_is_grounded(substrate, g, caps) for g in goal_concepts)

    # the ASCENT STATE the frontier-iterate carries: the live frontier + the trace
    # the loop accumulates. ascend mutates it one hop per step.
    init = {"frontier": list(dict.fromkeys(goal_concepts)),
            "steps": [], "acquired": [], "orders": [], "stalled_at": None,
            "step_no": 0, "stalled": False}

    def _ascent_step(state):
        """ONE frontier hop (the genuinely per-kind machinery): drop the grounded,
        ASSESS, the agent SELECTS, ACQUIRE, update the frontier / name the wall.
        Returns the updated state, or None to halt the climb (frontier emptied or a
        named boundary) — ascend reads None as the honest STALL."""
        # drop any frontier concept that became grounded (e.g. by a prior acquire
        # that grounded a shared reference) — a pure bottom-out read.
        frontier = [f for f in state["frontier"]
                    if not _is_grounded(substrate, f, caps)]
        state["frontier"] = frontier
        if not frontier:
            return None
        n = state["step_no"] + 1
        state["step_no"] = n
        steps = state["steps"]

        # ASSESS the frontier, then the agent SELECTS via its own machinery.
        assessments = _assess_frontier(substrate, frontier, conversation, caps)
        chosen = _select(assessments)
        if chosen is None:
            # nothing on the frontier is readable/comprehensible -> STALL. Name the
            # boundary: the (closest-to-goal) frontier concept the agent cannot
            # acquire. This is the honest wall — it drove as far as it could.
            state["stalled_at"] = frontier[0]
            state["stalled"] = True
            steps.append({"step": n, "target": frontier[0], "order": None,
                          "why_selected": ("STALL: no frontier concept is "
                                           "readable + comprehensible as a "
                                           "computation over the held basis"),
                          "grounded": False,
                          "frontier_after": list(frontier),
                          "reason": "boundary: not acquirable"})
            return None

        target = chosen["target"]
        # ACQUIRE via the unified order-N descent (single step).
        acq = _acquire(substrate, target, chosen["definition"], conversation,
                       caps)

        if acq["grounded"]:
            state["acquired"].append(target)
            if acq["order"] is not None:
                state["orders"].append(acq["order"])
            frontier = [f for f in frontier if f != target]
            state["frontier"] = frontier
        else:
            # not grounded this step: its still-un-held references must ground
            # first -> ADD them to the frontier (the descent the agent sequences).
            # If it is understood-but-not-computable (a coherent concept with no
            # computable realization), name it as the boundary and stop.
            if acq.get("understood") and acq.get("understood_not_computable"):
                state["stalled_at"] = (acq["understood_not_computable"][0]
                                       if acq["understood_not_computable"]
                                       else target)
                state["stalled"] = True
                steps.append({
                    "step": n, "target": target, "order": None,
                    "why_selected": chosen["why"], "grounded": False,
                    "frontier_after": list(frontier),
                    "reason": (f"understood, not computable -> boundary at "
                               f"{state['stalled_at']!r} ({acq['reason'][:80]})")})
                return None
            # BOUNDARY DETECTION: the target failed because a reference is un-held.
            # If EVERY un-held reference is itself NOT acquirable (unreadable, or a
            # prose/research definition that does not comprehend as a computation),
            # the chain cannot bottom out -> name the un-acquirable reference as the
            # wall and stall honestly. The agent drove as far as it could.
            unheld = chosen.get("unheld_refs", [])
            unacquirable = [r for r in unheld
                            if not _is_acquirable(substrate, r, conversation,
                                                  caps)]
            if unheld and len(unacquirable) == len(unheld):
                state["stalled_at"] = unacquirable[0]
                state["stalled"] = True
                steps.append({
                    "step": n, "target": target, "order": None,
                    "why_selected": chosen["why"], "grounded": False,
                    "frontier_after": list(frontier),
                    "reason": (f"boundary: reference {state['stalled_at']!r} has "
                               f"no computable definition (research-tier op with "
                               f"no computable realization)")})
                return None
            new_refs = [r for r in unheld
                        if r not in frontier and r != target]
            for r in new_refs:
                frontier.append(r)
            state["frontier"] = frontier
            # guard: a target that neither grounds nor exposes new refs is a wall.
            if not new_refs:
                state["stalled_at"] = target
                state["stalled"] = True
                steps.append({
                    "step": n, "target": target, "order": None,
                    "why_selected": chosen["why"], "grounded": False,
                    "frontier_after": list(frontier),
                    "reason": f"not acquirable, no new references ({acq['reason'][:60]})"})
                return None

        steps.append({
            "step": n,
            "target": target,
            "order": acq["order"],
            "why_selected": chosen["why"],
            "grounded": acq["grounded"],
            "parts": acq["parts"],
            "frontier_after": list(frontier),
            "reason": acq["reason"][:90],
        })
        return state

    # the FRONTIER ITERATE: ascend bounds the climb at max_steps, short-circuits
    # when the goal grounds, and halts on the step's None (frontier empty / named
    # boundary). The ONE iteration operator — no private while-loop.
    final = _acq.ascend(init, step=_ascent_step, n=max_steps, done=_goal_done)

    answered = _goal_done(final)
    return {
        "steps": final["steps"],
        "acquired": final["acquired"],
        "answered": answered,
        "frontier": list(final["frontier"]),
        "stalled_at": final["stalled_at"],
        "orders": final["orders"],
        "goal_concepts": goal_concepts,
    }


__all__ = ["seed_frontier", "drive_ascent"]
