"""can_counterfactual — a native, non-mutating "what if" predictor for the
discrete-asynchronous CAN mechanism (`seeds/can_native_reimplementation.
json::can_native_update_3state`/`_2state`), unblocking Blocker A named in
`CAN_CONSUMER_MIGRATION_RESULTS.md` §1 (rows 1, 3).

See `docs/research/engine_substrate/CAN_COUNTERFACTUAL_PREDICTOR_PREREG.md`
/ `_RESULTS.md` for the design and the live demonstration this module is
built to support.

THIS MODULE IS A TERM BUILDER + THIN ORCHESTRATION DRIVER, NOT THE
MECHANISM. Every quantity a caller reads back is the output of evaluating
`can_native_update_3state`/`_2state`'s own local-field/threshold Term
formula (verbatim structural twin, not reimplemented arithmetic) via
`Substrate.evaluate()` — the discrete Hopfield-style threshold DECISION is
made entirely by the Rust Term evaluator's `IfThenElse`, never by a Python
`if`/`else` over graph state. Python only:

  (a) assembles the Term tree (which node's local field, which override
      values are baked in as `Lit`s) — the same "codebook_scope
      parametrises the decode" shape `ShapeDecode` callers already use;
  (b) orchestrates WHICH node's term to evaluate next and WHEN to stop a
      bounded round-robin sweep — the same shape `domains/drive_curiosity.
      py::run_curiosity_all_mts` and `domains/insight_seeking.py::
      seek_insights` already use to loop over Mts / hot nodes / h-deltas
      without holding agent state.

Nothing in this module calls `run_rules()` or writes to any node/edge
attr — every function here is a pure read of the (real, uncounterfactual)
graph, composed with in-memory (never persisted) override values.
"""
from __future__ import annotations

import math
from typing import Any

from substrate_rs import (
    Term, Var, Lit, Attr, Eq, Gt, Lt, Gte, Plus, Times, IfThenElse, Sum,
)

ATANH_HALF = math.atanh(0.5)
"""Verbatim twin of `seeds/can_native_reimplementation.json`'s hard-coded
3-state threshold constant (`math.atanh(0.5)`, no `Tanh` Term exists)."""


# ---------------------------------------------------------------------
# Term builders — verbatim structural twins of can_native_update_3state/
# _2state's own `where`/`effects` sub-expressions
# (seeds/can_native_reimplementation.json:102-710).
# ---------------------------------------------------------------------

def _edges(node_term: Term, edge_type: str = "causal_influence") -> Term:
    return Term("Edges", node=node_term, edge_type=edge_type)


def _edge_attr(edge_term: Term, key: str) -> Term:
    return Term("EdgeAttr", edge=edge_term, key=key)


def _nth(items_term: Term, index: int) -> Term:
    return Term("Nth", items=items_term, index=index)


def _neighbour_state_term(edge_var: Term, node_state_overrides: dict) -> Term:
    """`Attr(Nth(edge_var,2),'state')`, with any node present in
    `node_state_overrides` ({NodeID: float}) substituted as a `Lit`
    baked in at TERM-BUILD time (the override set is known to the caller
    before the term is built — it is not resolved via `env`) instead of a
    live graph read. Chained `IfThenElse` over `Eq(target, Lit(node))` for
    each override, falling back to the real, live `Attr` read when no
    override applies to that edge's target."""
    target = _nth(edge_var, 2)
    expr = Attr(target, "state")
    for node, val in node_state_overrides.items():
        expr = IfThenElse(Eq(target, Lit(node)), Lit(float(val)), expr)
    return expr


def local_field_term(
    node_var: str = "c",
    external_field_var: str | None = None,
    node_state_overrides: dict | None = None,
) -> Term:
    """`local(c) = external_field(c) [or Var(external_field_var) if given]
    + identity_field(c) + Sum_{e in Edges(c,'causal_influence')}
    EdgeAttr(e,'weight') * state(target(e))` [target's state substituted
    per `node_state_overrides` where present] — the exact local-field
    sub-expression `can_native_update_3state`/`_2state` compute inline in
    their own `where`/`effects` (seeds/can_native_reimplementation.json:
    112-121 in the module's own PREREG-doc paraphrase; the live JSON is
    the ground truth this mirrors). Built once so both a CURRENT (no
    override) and a HYPOTHETICAL (override bound) evaluation share the
    identical formula, differing only in which env/literal values are
    substituted.
    """
    node_state_overrides = node_state_overrides or {}
    c = Var(node_var)
    own_field = Var(external_field_var) if external_field_var else Attr(c, "external_field")
    e_name = "e_%s" % node_var
    e = Var(e_name)
    edge_sum = Sum(
        _edges(c), e_name,
        Times([_edge_attr(e, "weight"), _neighbour_state_term(e, node_state_overrides)]),
    )
    return Plus([own_field, Attr(c, "identity_field"), edge_sum])


def target_state_term(local_term: Term, mt_var: str = "mt", mode: str = "3state") -> Term:
    """Discrete Hopfield-style threshold, verbatim twin of
    `can_native_update_3state`'s (mode='3state') or `can_native_update_
    2state`'s (mode='2state') own `IfThenElse` ladder. 3-state scales the
    local field by `Attr(mt,'temperature')` and compares to
    +/-ATANH_HALF (matching seed local_id... :102); 2-state compares the
    UNSCALED local field to 0 (matching the seed's own `:505` rule, which
    does NOT multiply by temperature) — this asymmetry is in the seed
    itself, not introduced here.
    """
    if mode == "2state":
        return IfThenElse(Gte(local_term, Lit(0.0)), Lit(1), Lit(-1))
    if mode != "3state":
        raise ValueError("mode must be '2state' or '3state', got %r" % (mode,))
    scaled = Times([local_term, Attr(Var(mt_var), "temperature")])
    return IfThenElse(
        Gt(scaled, Lit(ATANH_HALF)), Lit(1),
        IfThenElse(Lt(scaled, Lit(-ATANH_HALF)), Lit(-1), Lit(0)),
    )


# ---------------------------------------------------------------------
# Predictors — zero-hop (exact, single evaluation) and bounded multi-round
# ripple (Gauss-Seidel, non-mutating).
# ---------------------------------------------------------------------

def predict_single_step_target(
    substrate, mt, concept, new_external_field: float, mode: str = "3state",
) -> float:
    """The discrete-async mechanism's own next state for `concept` under a
    HYPOTHETICAL `external_field` override, holding every other node's
    CURRENT (real, committed) state fixed — an exact, zero-hop prediction:
    the SAME formula `can_native_update_3state`/`_2state` compute, with
    `external_field` bound to the hypothetical value via `env` instead of
    read live off the graph. Never writes to any node."""
    local = local_field_term(node_var="c", external_field_var="h_ovr")
    target = target_state_term(local, mt_var="mt", mode=mode)
    return float(substrate.evaluate(target, {"c": concept, "mt": mt, "h_ovr": float(new_external_field)}))


def predict_current_target(substrate, mt, concept, mode: str = "3state") -> float:
    """Same formula, no override — the real current `external_field` is
    read live. The baseline `predict_single_step_target` is compared
    against."""
    local = local_field_term(node_var="c")
    target = target_state_term(local, mt_var="mt", mode=mode)
    return float(substrate.evaluate(target, {"c": concept, "mt": mt}))


def predict_ripple(
    substrate, mt, concept, new_external_field: float, mode: str = "3state",
    max_rounds: int = 12,
) -> dict[str, Any]:
    """Bounded, non-mutating, GAUSS-SEIDEL (asynchronous, commit-in-place)
    simulation of how a hypothetical `external_field` override on
    `concept` propagates through the network, via repeated evaluation of
    the SAME `target_state_term` formula per Concept, deliberately NOT a
    synchronous (Jacobi) sweep — synchronous updates are exactly the
    pathology `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2 built the
    discrete-async mechanism to avoid, so a Jacobi predictor would risk
    reproducing the oscillation the real mechanism does not have. Each
    round updates an in-memory dict IN PLACE as it visits every Concept
    under `mt` (Python list order — the substrate's own internal
    `run_rules()` binding order is not reproduced exactly; see PREREG
    registered prediction 2 for why this is an open empirical question,
    not assumed correct), so later nodes in the SAME round already see
    earlier nodes' freshly-predicted state — the same "commit immediately,
    next read sees the update" semantics `run_rules()`'s own cold path has
    (`rewrite.rs:2183-2214`). Stops when a full round makes no change, or
    at `max_rounds`. NEVER calls `run_rules()`, NEVER writes any node
    attr — every value change lives only in the returned dict.

    Returns {"predicted_state": {node_id:int -> float}, "rounds": int,
    "converged": bool}.
    """
    concepts = list(substrate.neighbours(mt, "has_concept"))
    by_id = {c.value: c for c in concepts}
    hyp: dict[int, float] = {
        c.value: float(substrate.node(c)["attrs"].get("state", 0.0)) for c in concepts
    }
    probed_id = concept.value

    converged = False
    rounds_run = 0
    for rnd in range(max_rounds):
        rounds_run = rnd + 1
        changed = False
        for c in concepts:
            overrides = {by_id[k]: v for k, v in hyp.items() if k != c.value}
            is_probed = (c.value == probed_id)
            local = local_field_term(
                node_var="cx",
                external_field_var="h_ovr" if is_probed else None,
                node_state_overrides=overrides,
            )
            target = target_state_term(local, mt_var="mt", mode=mode)
            env = {"cx": c, "mt": mt}
            if is_probed:
                env["h_ovr"] = float(new_external_field)
            val = float(substrate.evaluate(target, env))
            if hyp[c.value] != val:
                changed = True
            hyp[c.value] = val
        if not changed:
            converged = True
            break

    return {"predicted_state": hyp, "rounds": rounds_run, "converged": converged}


def predicted_info_gain(substrate, mt, concept, new_external_field: float, mode: str = "3state") -> dict[str, Any]:
    """The counterfactual twin of `drive_curiosity.py::probe_via_what_if`'s
    return shape, computed via `predict_ripple` instead of
    `mt_mean_field_marginal`/`mt_mean_field_with_h_override` — total
    |delta-sigma| across the network, max single-node change, flip count.
    Never mutates the graph."""
    current = {c.value: float(substrate.node(c)["attrs"].get("state", 0.0))
               for c in substrate.neighbours(mt, "has_concept")}
    ripple = predict_ripple(substrate, mt, concept, new_external_field, mode=mode)
    predicted = ripple["predicted_state"]

    total_change = 0.0
    max_node_change = 0.0
    flipped_count = 0
    for nid, predicted_sig in predicted.items():
        current_sig = current.get(nid, 0.0)
        change = abs(predicted_sig - current_sig)
        total_change += change
        if change > max_node_change:
            max_node_change = change
        if change > 0.5:
            flipped_count += 1

    return {
        "concept_id": concept.value,
        "new_external_field": new_external_field,
        "predicted_state": predicted,
        "rounds": ripple["rounds"],
        "converged": ripple["converged"],
        "info_gain_total_change": total_change,
        "info_gain_max_node_change": max_node_change,
        "predicted_flipped_count": flipped_count,
    }


def predicted_frustration(substrate, mt, concept, new_external_field: float, mode: str = "3state") -> float:
    """`mt_frustration_given_state` (can_ops.rs, a pure, non-iterative,
    O(edges) closed-form scoring utility — reused unmodified, the same
    reuse the Bigville migration already established as legitimate,
    `CAN_CONSUMER_MIGRATION_RESULTS.md` §2.2) evaluated on this module's
    OWN predicted marginal, instead of on `mt_mean_field_with_h_override`'s
    continuous marginal. Never mutates the graph."""
    ripple = predict_ripple(substrate, mt, concept, new_external_field, mode=mode)
    inner = getattr(substrate, "_inner", substrate)
    return float(inner.mt_frustration_given_state(mt, ripple["predicted_state"]))


__all__ = [
    "ATANH_HALF",
    "local_field_term",
    "target_state_term",
    "predict_single_step_target",
    "predict_current_target",
    "predict_ripple",
    "predicted_info_gain",
    "predicted_frustration",
]
