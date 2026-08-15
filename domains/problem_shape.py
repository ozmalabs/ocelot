"""problem_shape -- Rung 3 of docs/research/engine_substrate/
QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md
(QUESTION_DRIVER_RUNG3_PREREG.md is the design doc for THIS module):
a `ProblemShape` codebook that recognizes the STRUCTURAL SHAPE of an
already-minted `solve_*` Goal (`domains/solver_dispatch.py`, Rung 1) from
its own real attrs/edges -- never from its `kind` string, which would be
circular -- via the existing `ShapeDecode` sd-loop machinery, extended per
the `DirectionalCorrespondence` precedent (a NEW node type, not a `kind` tag
on `ShapeSignature` -- `ShapeDecode`'s live decode pool does not partition
on `kind`, confirmed at `runners/dsl/src/shape_decode.rs::load_parts`).

ARCHITECTURE (CLAUDE.md's rule; the same discipline
`domains/meta_shape.py` already follows for the MetaShape grain): every
DECISION lives in graph rules (`seeds/problem_shape_growth.json`). This
module does exactly two mechanical things:

  1. `goal_signature(sub, native, goal_node)` -- read the FIVE real,
     already-written facts a `solve_*` Goal carries (statement / targets_mt
     / targets_correspondence / direction / bound -- see
     QUESTION_DRIVER_RUNG3_PREREG.md Sec1.3's table, grounded in
     `domains/solver_dispatch.py`'s own `mint_solve_*_goal` functions) into
     a fixed-arity relation-set signature, mirroring
     `analogical_thinking._pair_witness`/`_concept_shape_vector`'s idiom
     (fixed axis order, `_ABSENT` sentinel, sorted by predicate). Pure
     destructuring -- no branch decides what KIND the problem is.
  2. `observe(agent, goal_node)` -- write that signature into the graph as a
     `ProblemShapeObservation` and hand off to
     `seeds/problem_shape_growth.json`'s rules. Pure ingest, the same shape
     `meta_shape.observe`/`induce_concern` already are.

The recognise / mint decisions are `ps_decode`/`ps_recognize`/`ps_mint`/
`ps_redecode` (all built from EXISTING generic Terms -- `ShapeDecode`,
`Eq`, `Exists`, `Argmin`, `Count`, `Plus` -- zero new Rust; see
QUESTION_DRIVER_RUNG3_PREREG.md Sec4.2 for why no bespoke mint Term is
needed here, unlike `MetaShapeMint`). Nothing in this file decides
anything.
"""
from __future__ import annotations

from typing import Any, Optional

#: The node type the `ps_*` rules match on, and the edge that hangs it off
#: the agent hub -- mirrors `meta_shape.py`'s `OBSERVATION_TYPE`/`OBSERVED_EDGE`.
OBSERVATION_TYPE = "ProblemShapeObservation"
OBSERVED_EDGE = "observed_problem"
#: This grain's OWN codebook epoch (deliberately not the sd loop's shared
#: `codebook_epoch`, nor meta-shape's `meta_codebook_epoch` -- minting a
#: ProblemShape grows neither of those other pools).
EPOCH_ATTR = "problem_codebook_epoch"

#: Fixed sentinel for "this axis is absent on this Goal" -- mirrors
#: `analogical_thinking._ABSENT` (a bare string, so every signature has the
#: SAME arity regardless of which facts a given Goal actually carries; see
#: that module's own comment on why fixed arity matters for `AntiUnify`/
#: `FixedCount`/literal `ShapeDecode`).
_ABSENT = "-"

#: Fixed axis order (QUESTION_DRIVER_RUNG3_PREREG.md Sec2.1) -- sorted by
#: predicate name so the representation is order-independent, the same
#: discipline `meta_shape.item_signature` documents.
#:
#: `has_combine`/`has_k_starts` (PROBLEM_SHAPE_CAN_AXES_PREREG.md/_RESULTS.md)
#: added to discriminate the three CAN solver kinds
#: (`solve_can_relax`/`solve_can_exact`/`solve_can_bp`), which previously all
#: collapsed to the same signature -- none of the original 5 axes reads
#: anything a CAN Goal carries. Both are presence-checks on attrs each
#: `mint_solve_can_*_goal` function (`domains/solver_dispatch.py:174-211`)
#: writes UNCONDITIONALLY (every call, regardless of caller kwargs), never on
#: a caller-optional attr like `treewidth_bound`/`max_rounds` -- an axis keyed
#: on an optional attr would silently re-collapse real no-kwargs call sites
#: back to indistinguishable (PREREG Sec2). `k_starts` is written only by
#: `mint_solve_can_relax_goal`; `combine` is written only by `mint_solve_can_
#: bp_goal`; `mint_solve_can_exact_goal` writes neither -- so the two axes
#: jointly separate all three kinds (relax: k_starts yes/combine no; bp:
#: k_starts no/combine yes; exact: neither), with `solve_can_exact` staying
#: on the SAME `ps_has_targets_mt=yes` key it always had (PREREG Sec3).
_AXES = ("has_bound", "has_combine", "has_direction", "has_k_starts",
         "has_statement", "has_targets_correspondence", "has_targets_mt")


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    return sub, native, ag_node


def goal_signature(sub, native, goal_node) -> list:
    """A `solve_*` Goal's own real attrs/edges -> a fixed-arity relation-set
    signature. Mechanical extraction only (CLAUDE.md's "mechanical
    extraction of structural attrs... is PURE EXTRACTION, legitimate"
    carve-out, the same class `_ingest_target`'s `op`/`params`/`concept`
    writes already are) -- `kind` is DELIBERATELY never read here (reading
    it back out would make recognition circular, and would give the wrong
    answer once a future pre-mint dispatch caller needs this signature
    BEFORE `kind` exists at all -- see QUESTION_DRIVER_RUNG3_PREREG.md
    Sec2.2)."""
    at = sub.node(goal_node)["attrs"]
    facts = {
        "has_bound": "yes" if at.get("bound") is not None else _ABSENT,
        "has_combine": "yes" if at.get("combine") else _ABSENT,
        "has_direction": at.get("direction") if at.get("direction") else _ABSENT,
        "has_k_starts": "yes" if at.get("k_starts") is not None else _ABSENT,
        "has_statement": "yes" if at.get("statement") else _ABSENT,
        "has_targets_correspondence": "yes" if native.neighbours(
            goal_node, "targets_correspondence") else _ABSENT,
        "has_targets_mt": "yes" if native.neighbours(
            goal_node, "targets_mt") else _ABSENT,
    }
    rels = [["is_a", "problem"]]
    for axis in _AXES:
        rels.append([axis, str(facts[axis]).lower()])
    rels.sort(key=lambda r: r[0])
    return rels


def signature_key(signature: list) -> str:
    """A deterministic, human-legible identity string for a signature --
    mirrors `sd_mint_quantum`'s own `capability_keys` idiom exactly
    ("mechanical, stable... set... from the observation's own predicate
    structure", `seeds/shape_decode_loop.json::sd_mint_quantum`'s comment):
    the sorted list of `predicate=value` pairs for every axis that is NOT
    `_ABSENT`, joined -- pure destructuring of an already-computed
    signature, never a decision. Two observations with the SAME real facts
    (e.g. every real `solve_decompose` Goal, which only ever sets `bound`)
    get the SAME key, which is exactly the recurrence signal
    `ps_mint`'s guard reads (Eq(obs.key, other.key))."""
    parts = []
    for pred, val in signature:
        if pred == "is_a" or val == _ABSENT:
            continue
        parts.append("%s=%s" % (pred, val))
    parts.sort()
    return "ps_" + ("_".join(parts) if parts else "empty")


def _agent_node(agent):
    for name in ("agent", "agent_node", "_agent"):
        n = getattr(agent, name, None)
        if n is not None:
            return n
    return None


def observe(agent, goal_node, *, run: bool = True) -> Optional[Any]:
    """Write one `ProblemShapeObservation` for a real, already-minted
    `solve_*` Goal and let the rules decide about it. Mechanical ingest
    only -- mirrors `meta_shape.observe` exactly, plus an `about_goal` edge
    for traceability back to the real Goal this observation was extracted
    from (mirrors `gap_awareness.json`'s own `sc -about_goal-> g`)."""
    sub, native, ag = _resolve(agent)
    if sub is None or not hasattr(sub, "add_node"):
        return None
    try:
        if ag is not None and sub.node(ag)["attrs"].get(EPOCH_ATTR) is None:
            sub.set_attr(ag, EPOCH_ATTR, 0)
        sig = goal_signature(sub, native, goal_node)
        oid = sub.add_node(OBSERVATION_TYPE, {
            "signature": sig,
            "key": signature_key(sig),
            "status": "pending",
        })
        if ag is not None:
            sub.add_edge(ag, OBSERVED_EDGE, oid)
        sub.add_edge(oid, "about_goal", goal_node)
        if run:
            native.run_rules()
        return oid
    except Exception:
        return None


__all__ = ["OBSERVATION_TYPE", "OBSERVED_EDGE", "EPOCH_ATTR",
           "goal_signature", "signature_key", "observe"]
