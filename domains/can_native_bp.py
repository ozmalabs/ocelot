"""can_native_bp — loopy belief propagation (max-product / min-sum, log
domain; sum-product / log-sum-exp as a measured comparison variant) as a
genuinely DIFFERENT, complementary discrete solving strategy alongside
`seeds/can_native_reimplementation.json`'s discrete-async update and
`domains/can_native_orchestration.py::multi_start_settle_and_pick_best`.
Toolbox work, not a replacement — see
`docs/research/engine_substrate/CAN_LOOPY_BP_PREREG.md` /
`CAN_LOOPY_BP_RESULTS.md` for the design decision and the measured
convergence/quality comparison this module exists to support.

THIS MODULE NEVER TOUCHES `seeds/can_native_reimplementation.json` or
`domains/can_native_orchestration.py` — it is purely additive. It mints
NO new node or edge types (zero new Gamma productions needed), NO new
Rust Terms, and calls `run_rules()`/`run_rules_scoped()` NOWHERE — the
task's own explicit instruction was to reuse
`domains/can_counterfactual.py`'s own established shape, not to build
installed graph Rules for this. Every function here is either:

  (a) a Term builder that is a verbatim-twin adaptation of
      `can_counterfactual.py`'s own `local_field_term`/
      `_neighbour_state_term` idiom — a real graph-structural traversal
      (`Sum` over `Edges`, `EdgeAttr`, `Nth`, `Attr`) with a small set of
      Python-known override values spliced in via a node-identity-keyed
      `IfThenElse` ladder, applied here to MESSAGE components instead of
      neighbour STATES; or
  (b) mechanical orchestration — Python decides WHICH directed edge's
      message to recompute next and WHEN to stop a bounded round-robin
      sweep, the SAME shape `can_counterfactual.py::predict_ripple`
      already uses for its own bounded Gauss-Seidel sweep. Messages live
      ONLY in an in-memory Python dict across rounds, exactly like
      `predict_ripple`'s own `hyp` dict — never a graph node or edge
      attr, and never persisted mid-sweep.

Why messages are NOT graph-resident (a design point worth stating up
front, not discovered mid-build): this engine has no `set_edge_attr`
rule effect (confirmed by grep, and independently documented at
`seeds/can_native_reimplementation.json`'s own
`can_native_hebbian_reweight` comment — edges cannot carry live-updated
attrs). Building this as installed graph Rules would therefore have
forced minting one `BpMessage` NODE per directed edge just to hold three
mutable scalars, plus new Gamma productions for that bookkeeping
(mirroring what `can_native_orchestration.py::install_multi_start_
productions` had to do for ITS bookkeeping nodes) — real, avoidable
weight the task's own explicit "reuse can_counterfactual's orchestration
pattern" instruction sidesteps entirely: an in-memory Python dict is the
correct, lighter-weight home for a quantity (BP messages) that is
recomputed every round and never needs to survive past this one
bounded call.

Where a value is PYTHON ARITHMETIC on already-Term-evaluated floats
(the max-product/log-sum-exp combine over 2-3 known candidate scores;
the final per-node argmax over 2-3 known belief scores) rather than a
fresh Term evaluation, that is a deliberate choice, not an oversight —
see the module-level "ON PYTHON VS TERM ARITHMETIC" note below the
imports. `can_counterfactual.py::predict_ripple`/`predicted_info_gain`
already establish this exact precedent (`if change > max_node_change:`,
`total_change += change` — plain Python comparison/accumulation of
already-Term-derived scalars is not a "decision over graph state" in
`CLAUDE.md`'s sense; it has no graph state left to read).
"""
from __future__ import annotations

import math
from typing import Any

from substrate_rs import (
    Term, Var, Lit, Attr, Eq, Plus, Times, IfThenElse, Sum, Filter, Pick,
)

# ---------------------------------------------------------------------
# ON PYTHON VS TERM ARITHMETIC (read this before editing the combine
# step or the final decision below):
#
# Every quantity that reads LIVE graph state (external_field,
# identity_field, temperature, an edge's weight, and — every round — the
# CURRENT held messages spliced in via an override ladder) is computed by
# evaluating a Term tree via `Term.evaluate(env, substrate)`. Once those
# evaluations return plain Python floats, this module composes them with
# ordinary Python arithmetic (max(), math.exp/log, +) exactly like
# `can_counterfactual.py::predict_ripple`'s own `if changed:` bookkeeping
# and `predicted_info_gain`'s own `total_change += change` accumulation
# already do. This is NOT the same class of operation as
# `multi_start_settle_and_pick_best`'s `Argmin` Term, which decides among
# GRAPH-RESIDENT CANDIDATE NODES by reading a LIVE attr off each one —
# there is real graph traversal inside that decision. Wrapping 2-3
# already-known Python floats in `Lit(...)` and running them through an
# `IfThenElse`/`Max` Term would be definitionally identical arithmetic to
# comparing them directly in Python, with an extra FFI hop and no
# graph-native content — so this module does not perform that
# theatre. Every place graph structure or a live attr genuinely
# determines the outcome, a Term does the work; every place the outcome
# is pure math over numbers Python already holds, Python does the work.
# ---------------------------------------------------------------------

_VOCAB = {
    "3state": (-1.0, 0.0, 1.0),
    "2state": (-1.0, 1.0),
}
"""Verbatim twin of `can_native_orchestration.py::_DISCRETE_VOCAB` — kept
local (not imported) so this module has zero import-time coupling to
`can_native_orchestration.py`'s internals, matching its own "purely
additive, never touches" guarantee."""

DEFAULT_MAX_ROUNDS = 40
"""Bounded iteration cap — loopy BP is NOT guaranteed to converge on a
general (looped) graph, unlike the discrete-async update's own proven
Lyapunov guarantee (`seeds/can_native_reimplementation.json`'s own module
description). Mirrors `can_counterfactual.py::predict_ripple`'s own
`max_rounds` pattern (there: 12, for a single-hop ripple prediction;
here: higher, because loopy BP on a DENSE N=16 graph needs materially
more rounds than a single counterfactual ripple to have a chance at
stabilising — sized empirically in CAN_LOOPY_BP_RESULTS.md, not guessed)."""

DEFAULT_EPSILON = 1e-3
"""Convergence threshold on the largest single message-component change
in one round. See CAN_LOOPY_BP_RESULTS.md for the measured convergence
behaviour this default was checked against."""


# ---------------------------------------------------------------------
# Term builders — verbatim-twin idiom of can_counterfactual.py's own
# _edges/_edge_attr/_nth helpers (small, generic, safe to re-derive
# locally rather than import a private, underscore-prefixed helper
# across modules).
# ---------------------------------------------------------------------

def _edges(node_term: Term, edge_type: str = "causal_influence") -> Term:
    return Term("Edges", node=node_term, edge_type=edge_type)


def _edge_attr(edge_term: Term, key: str) -> Term:
    return Term("EdgeAttr", edge=edge_term, key=key)


def _nth(items_term: Term, index: int) -> Term:
    return Term("Nth", items=items_term, index=index)


def edge_weight(substrate, i_node, j_node) -> float:
    """ONE Term evaluation reading the real i->j `causal_influence`
    edge's weight — `Filter`+`Edges`+`Nth`+`Eq` to select the edge, `Pick`
    to take its single match (this codebase's own edge-population
    convention is exactly one `causal_influence` edge per ordered pair —
    confirmed by every existing CAN test helper's `add_edge` call),
    `EdgeAttr` to read `weight`. Callers cache this ONCE per directed
    edge at setup (`_directed_edges_and_weights` below) — the weight is
    static for the whole BP sweep, matching `CLAUDE.md`'s "Python may
    cache for performance, but the substrate is the source of truth"
    allowance exactly (re-reading an unchanging value every round would
    be a correct but wasteful re-derivation, not a correctness
    requirement)."""
    matched = Filter(_edges(Lit(i_node)), "e", Eq(_nth(Var("e"), 2), Lit(j_node)))
    picked = Pick(matched)
    return float(_edge_attr(picked, "weight").evaluate(None, substrate))


def unary_score_term(concept_lit: Term, mt_var: str, x_val: float) -> Term:
    """u_i(x_i) = temperature * (external_field + identity_field) * x_i —
    the SAME external_field+identity_field sub-expression
    `can_counterfactual.py::local_field_term` and
    `can_native_update_3state` both read
    (`seeds/can_native_reimplementation.json:143-499`), scaled by
    `temperature` exactly as the seed's own threshold rule scales its
    local field before thresholding, multiplied by the CANDIDATE state
    value `x_val` (baked in as a `Lit` — the vocab is small, fixed, and
    enumerated in PYTHON, never iterated as a graph-Term collection, so
    this module never needs the "Sum over a literal list" composition
    `CAN_SOLVER_TRACTABILITY_RESULTS.md` Sec4 point 3 flagged as
    "very likely, not confirmed" — that open question is sidestepped
    entirely, not resolved, and CAN_LOOPY_BP_RESULTS.md says so)."""
    return Times([
        Attr(Var(mt_var), "temperature"),
        Plus([Attr(concept_lit, "external_field"), Attr(concept_lit, "identity_field")]),
        Lit(x_val),
    ])


def pairwise_score_term(weight: float, mt_var: str, xi_val: float, xj_val: float) -> Term:
    """psi_ij(x_i,x_j) = temperature * J_ij * x_i * x_j — the SAME
    coupling term `can_native_update_3state`'s own `Sum`-over-`Edges`
    reads (`EdgeAttr(e,'weight') * state(target(e))`), generalised from
    "target's CURRENTLY COMMITTED state" to "a candidate joint
    assignment", scaled by the SAME `temperature` the seed's own
    threshold ladder multiplies its local field by. `weight` is the
    Python float `edge_weight()` already read live off the graph."""
    return Times([Attr(Var(mt_var), "temperature"), Lit(weight), Lit(xi_val), Lit(xj_val)])


def incoming_sum_term(
    concept_i_lit: Term, exclude_j_id, xi_val: float, incoming_by_k: dict,
) -> Term:
    """Sum_{k in N(i)} m_{k->i}(x_i=xi_val), with k=exclude_j_id's own
    contribution forced to 0.0 (the log-domain identity for "no
    message") when `exclude_j_id` is not None — the "leave-one-out"
    exclusion `CAN_SOLVER_TRACTABILITY_RESULTS.md` Sec4 point 2 confirmed
    composable via `Filter`+`Edges`+`Nth`+`Eq`. Built here via the SAME
    node-identity-keyed `IfThenElse`-ladder-of-overrides idiom
    `can_counterfactual.py::_neighbour_state_term` already establishes
    (there: override a neighbour's STATE; here: override/zero a
    neighbour's MESSAGE contribution) — one fewer Term than a separate
    Filter+Not+Eq predicate, same result, because the override dict
    already special-cases every node a Filter predicate would otherwise
    have to exclude. `exclude_j_id=None` (used for the final BELIEF
    read-off, where there is no leave-one-out neighbour) simply omits the
    zero-override, summing every neighbour's message unmodified.

    `incoming_by_k` keys and `exclude_j_id` MUST be `NodeID` objects, not
    raw ints — this is the exact requirement
    `can_counterfactual.py::_neighbour_state_term`'s own
    `node_state_overrides` docstring states (`{NodeID: float}`) and for
    the identical reason: `target` (read off a live `Edges` tuple) is a
    `Value::Node`, and `Lit(some_int)` serialises to `Value::Int` —
    `Eq(Value::Node, Value::Int)` is never true, so a raw-int key here
    would silently zero every ladder branch (every neighbour's
    contribution would read as the `Lit(0.0)` default, never matching).
    CONFIRMED LIVE DURING THIS BUILD: an earlier version of this function
    took `NodeID.value` (a plain int) as the override key, and the whole
    incoming-message sum silently evaluated to 0.0 on every round for
    every node — BP looked like it "converged in 2 rounds" because it was
    never actually summing any neighbour's message at all, only ever
    running one real (message-free) unary+pairwise pass. Caught by
    manually tracing `incoming_by_xi` round over round and finding it
    identically zero when the fed-in Python dict held real nonzero
    values — see CAN_LOOPY_BP_RESULTS.md for the full account."""
    e = Var("e_in")
    target = _nth(e, 2)
    expr = Lit(0.0)  # default: an untracked/absent neighbour contributes nothing
    overrides = {k: float(v) for k, v in incoming_by_k.items()}
    if exclude_j_id is not None:
        overrides[exclude_j_id] = 0.0
    for k, val in overrides.items():
        expr = IfThenElse(Eq(target, Lit(k)), Lit(val), expr)
    return Sum(_edges(concept_i_lit), "e_in", expr)


# ---------------------------------------------------------------------
# Orchestration — the bounded, Gauss-Seidel round-robin sweep, mirroring
# can_counterfactual.py::predict_ripple's own orchestration shape exactly
# (Python decides WHICH directed edge's message to recompute next and
# WHEN to stop; every value change lives only in the in-memory
# `messages` dict until the final, explicit commit step).
# ---------------------------------------------------------------------

def _directed_edges_and_weights(substrate, concepts):
    """Mechanical graph read: every (i,j) `causal_influence` directed
    pair among these concepts, and each edge's weight (`edge_weight()`,
    read once — see its own docstring for why once is correct, not a
    shortcut)."""
    ids = [c.value for c in concepts]
    idset = set(ids)
    directed: list[tuple[int, int]] = []
    weight_of: dict[tuple[int, int], float] = {}
    for c in concepts:
        i = c.value
        for k in substrate.neighbours(c, "causal_influence"):
            j = k.value if hasattr(k, "value") else int(k)
            if j not in idset:
                continue
            directed.append((i, j))
            weight_of[(i, j)] = edge_weight(substrate, c, k)
    return directed, weight_of


def run_loopy_bp(
    substrate, mt, combine: str = "max_product",
    max_rounds: int = DEFAULT_MAX_ROUNDS, epsilon: float = DEFAULT_EPSILON,
    discrete_mode: str | None = None, commit: bool = False,
) -> dict[str, Any]:
    """Run a bounded, non-mutating (unless `commit=True`) loopy
    belief-propagation sweep over `mt`'s `causal_influence` network.

    `combine`: `"max_product"` (min-sum in this module's additive log
    domain — the PRIMARY, chosen variant, see CAN_LOOPY_BP_PREREG.md for
    the full justification: `can_native_update_3state`'s own threshold
    decision is a per-node MAP/mode decision under the SAME Ising/
    Boltzmann Hamiltonian `causal_attitude_networks.json` declares, not a
    marginal-probability computation, so max-product is the direct
    generalisation of what this mechanism already computes locally) or
    `"sum_product"` (log-sum-exp combine — the measured COMPARISON
    variant this investigation's own theory predicts should lose
    specifically on frustrated/multistable networks, since a per-node
    argmax of a MARGINAL can select an inconsistent joint configuration —
    precisely `causal_attitude_networks.json`'s own "multiple
    inconsistent views = multistable network" framing).

    Returns `{"final_state": {node_id:int -> float}, "beliefs":
    {node_id:int -> {value:float -> score:float}}, "rounds": int,
    "converged": bool, "max_delta_history": [float,...], "combine": str}`.
    NEVER calls `run_rules()`. Mutates no node/edge attr unless
    `commit=True`, in which case the final decided state is written onto
    the real Concepts — mechanical translation of an already-made
    decision, matching `multi_start_settle_and_pick_best`'s own commit
    step exactly (same shape: decide first, in-memory; translate onto the
    graph second, unconditionally, no decision left in that step)."""
    if combine not in ("max_product", "sum_product"):
        raise ValueError("combine must be 'max_product' or 'sum_product', got %r" % (combine,))

    concepts = list(substrate.neighbours(mt, "has_concept"))
    id_to_node = {c.value: c for c in concepts}
    ids = list(id_to_node.keys())
    mode = discrete_mode or substrate.node(mt)["attrs"].get("discrete_mode", "3state")
    vocab = _VOCAB.get(mode, _VOCAB["3state"])
    mt_var = "mt"

    directed, weight_of = _directed_edges_and_weights(substrate, concepts)
    neighbours_of: dict[int, list[int]] = {i: [] for i in ids}
    for (i, j) in directed:
        neighbours_of[i].append(j)

    if not directed:
        # No causal_influence edges at all -- belief is external field
        # alone, no message passing needed. Still route the decision
        # through the same unary-score + argmax path below for a single
        # (degenerate) "round".
        pass

    # Static (message-independent) potentials, cached ONCE -- see the
    # module-level docstring's "ON PYTHON VS TERM ARITHMETIC" note: these
    # DO read live graph state (external_field/identity_field/
    # temperature/weight), so each is a genuine Term evaluation; they do
    # NOT depend on the round-varying messages, so caching them once
    # (rather than re-deriving the identical value every round) is
    # mechanical performance caching, not a correctness shortcut.
    unary_cache: dict[int, dict[float, float]] = {}
    for i in ids:
        concept_lit = Lit(id_to_node[i])
        unary_cache[i] = {
            xi: float(unary_score_term(concept_lit, mt_var, xi).evaluate({mt_var: mt}, substrate))
            for xi in vocab
        }

    pairwise_cache: dict[tuple[int, int], dict[tuple[float, float], float]] = {}
    for (i, j), w in weight_of.items():
        pairwise_cache[(i, j)] = {
            (xi, xj): float(pairwise_score_term(w, mt_var, xi, xj).evaluate({mt_var: mt}, substrate))
            for xi in vocab for xj in vocab
        }

    # Messages: {(i,j): {x_j_value -> log-score}}. In-memory only, never
    # a graph node/edge attr (see module docstring). Uniform (0.0 =
    # no-information) prior.
    messages: dict[tuple[int, int], dict[float, float]] = {
        (i, j): {v: 0.0 for v in vocab} for (i, j) in directed
    }

    converged = False
    rounds_run = 0
    max_delta_history: list[float] = []

    for rnd in range(max_rounds):
        rounds_run = rnd + 1
        max_delta = 0.0
        # GAUSS-SEIDEL (asynchronous, commit-in-place), deliberately NOT
        # a synchronous (Jacobi) sweep -- `messages` is updated IN PLACE
        # as this loop visits every directed edge (Python list order), so
        # a LATER edge processed this same round already sees an EARLIER
        # edge's freshly-recomputed message, exactly mirroring
        # `can_counterfactual.py::predict_ripple`'s own explicit choice
        # and for the SAME documented reason: a synchronous update is
        # exactly the pathology `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.
        # md` Sec7 item 1 (Murphy/Weiss/Jordan 1999) names as a known,
        # specifically-studied cause of persistent loopy-BP oscillation
        # (period-2 cycles) -- confirmed live during this build: an
        # earlier Jacobi (batch-then-swap) version of this exact loop
        # converged suspiciously fast (2 rounds, delta exactly 0.0) on
        # the N=16 stress case, an artefact of every message updating
        # from the SAME stale round-0 snapshot simultaneously rather than
        # genuinely propagating; switching to in-place Gauss-Seidel below
        # is the fix, not a stylistic choice -- see CAN_LOOPY_BP_RESULTS.
        # md for the before/after numbers.
        for (i, j) in directed:
            concept_i_lit = Lit(id_to_node[i])
            # incoming_sum(i, exclude=j, xi) -- the ONLY message-round-
            # dependent Term evaluation in this whole sweep; everything
            # else this round is plain Python arithmetic on cached
            # floats (see module docstring).
            incoming_sum_by_xi = {}
            for xi in vocab:
                # NodeID-keyed, NOT int-keyed -- see incoming_sum_term's
                # own docstring for exactly why this distinction is
                # load-bearing (a raw-int key silently zeros the ladder).
                incoming_by_k = {id_to_node[k]: messages[(k, i)][xi] for k in neighbours_of[i]}
                term = incoming_sum_term(concept_i_lit, id_to_node[j], xi, incoming_by_k)
                incoming_sum_by_xi[xi] = float(term.evaluate(None, substrate))

            comp: dict[float, float] = {}
            for xj in vocab:
                scores = [
                    unary_cache[i][xi] + pairwise_cache[(i, j)][(xi, xj)] + incoming_sum_by_xi[xi]
                    for xi in vocab
                ]
                if combine == "max_product":
                    comp[xj] = max(scores)
                else:
                    shift = max(scores)
                    comp[xj] = shift + math.log(sum(math.exp(s - shift) for s in scores))

            # Normalise: subtract the message's own max component --
            # standard max-product/min-sum numerical stabilisation, a
            # constant per-message shift that changes no downstream
            # comparison/argmax. Plain Python arithmetic on
            # already-computed floats (see module docstring).
            shift = max(comp.values())
            comp = {v: s - shift for v, s in comp.items()}

            for v in vocab:
                d = abs(comp[v] - messages[(i, j)][v])
                if d > max_delta:
                    max_delta = d
            messages[(i, j)] = comp  # commit in place -- Gauss-Seidel
        max_delta_history.append(max_delta)
        if max_delta < epsilon:
            converged = True
            break

    # Belief / final-state read-off. Sum ALL incoming messages (no
    # exclusion -- exclude_j_id=None), add the node's own unary score,
    # decide the winning candidate by plain Python argmax over the (2-3)
    # already-Term-evaluated belief scores -- see the module docstring's
    # "ON PYTHON VS TERM ARITHMETIC" note for why this is not routed
    # through an extra Lit-wrapped Term.
    beliefs: dict[int, dict[float, float]] = {}
    final_state: dict[int, float] = {}
    for i in ids:
        concept_lit = Lit(id_to_node[i])
        scored: dict[float, float] = {}
        for xi in vocab:
            incoming_by_k = {id_to_node[k]: messages[(k, i)][xi] for k in neighbours_of[i]}
            inc_term = incoming_sum_term(concept_lit, None, xi, incoming_by_k)
            inc = float(inc_term.evaluate(None, substrate))
            scored[xi] = unary_cache[i][xi] + inc
        beliefs[i] = scored
        final_state[i] = max(scored.items(), key=lambda kv: kv[1])[0]

    if commit:
        for i, c in id_to_node.items():
            substrate.set_attr(c, "state", float(final_state[i]))

    return {
        "final_state": final_state,
        "beliefs": beliefs,
        "rounds": rounds_run,
        "converged": converged,
        "max_delta_history": max_delta_history,
        "combine": combine,
        "mt_id": mt.value if hasattr(mt, "value") else int(mt),
    }


__all__ = [
    "DEFAULT_MAX_ROUNDS",
    "DEFAULT_EPSILON",
    "edge_weight",
    "unary_score_term",
    "pairwise_score_term",
    "incoming_sum_term",
    "run_loopy_bp",
]
