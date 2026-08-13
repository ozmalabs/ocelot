"""Native-CAN orchestration bridge — the drop-in composition
`CAN_FINAL_MIGRATION_RESULTS.md` Sec0 named as buildable-but-not-built
("`mt_audit_basin`/`mt_distance_to_target` ... USING it correctly still
needs `state` to already be at a native fixed point, which collapses into
the exact same `run_rules()`-orchestration question") — now buildable
because `Substrate.run_rules_scoped` (CAN_MT_SCOPED_RULES_PREREG/
RESULTS.md) removes exactly that hazard: a per-Mt Python loop can call it
directly, for its own Mt only, without touching any other Mt's state.

Every function here is either:
  (a) a pure, non-mutating READ composed entirely from the substrate's own
      representation-agnostic primitives (`mt_energy`,
      `mt_frustration_given_state`, `mt_target`/`distance_to_target`'s own
      math — all already reused this way by `can_counterfactual.py` and
      `insight_seeking.py`'s native branch, CAN_FINAL_MIGRATION_RESULTS.md
      Sec2.2), reading `state` directly instead of relaxing it; or
  (b) a single mechanical call to `run_rules_scoped(max_steps, False, mt)`,
      letting the ALREADY-SEEDED native rules (can_native_update_3state/
      _2state, can_native_hebbian_mint/_reweight, can_native_evidence_decay)
      decide everything — this module makes no decision about WHICH rule
      fires; the graph's own `where`-clause policy gates (already proven in
      CAN_HEBBIAN_MATERIALIZATION_RESULTS.md) do that; or
  (c) `multi_start_settle_and_pick_best` (CAN_SOLVER_TRACTABILITY_RESULTS.md
      §1/§5): a mechanical composition of K independent calls to (b), each
      run from a mechanically-drawn random initial `state` (world-adapter-
      shaped I/O, the same class of random re-draw
      `scripts/bigville_can_integration_demo.py::multi_start_basin_count`
      already performs) — the DISCRETE UPDATE RULE ITSELF
      (`can_native_update_3state`/`_2state`) IS NEVER TOUCHED, so its
      proven Lyapunov/empirical convergence guarantee is preserved exactly;
      this only widens the search by trying several already-guaranteed-
      convergent runs and keeping the best. WHICH of the K converged
      candidates is kept is decided by the `Argmin` Term over graph-resident
      candidate nodes, not by a Python `if`/`min()` — matching CLAUDE.md's
      standing rule precisely.

No `if`/`else` here branches on graph state to decide a mutation — the only
mutation surfaces are "run the scoped fixpoint" (mechanical) and "commit the
Argmin-decided winner's stored state onto the real Concepts" (mechanical
translation of an already-made graph-native decision). Callers
(self_improvement_loop.py etc.) own the `discrete_mode`-gated dispatch
between this module's native path and the continuous can_ops path, matching
the existing precedent (`insight_seeking.py::seek_insights`'s own
discrete_mode guard).
"""
from __future__ import annotations

import random
from typing import Any

from substrate_rs import Term, Var, Lit, Attr

# How many scoped-fixpoint steps one orchestration call is allowed. Mirrors
# the existing native convergence tests' own cap
# (test_can_native_reimplementation.py uses 3000 for an N=8 complete graph);
# generous relative to any Mt size this arc has built so far.
DEFAULT_SCOPED_MAX_STEPS = 3000


def native_marginal_from_state(substrate, mt) -> dict[int, float]:
    """The native equivalent of a relaxed marginal: `state` is ALREADY the
    fixed point for a discrete_mode Mt once `run_rules_scoped` has settled
    it (no mean-field iteration needed — that's the whole point of the
    discrete-async mechanism). Pure read, {concept_id: sigma}."""
    out: dict[int, float] = {}
    for c in substrate.neighbours(mt, "has_concept"):
        cid = c.value if hasattr(c, "value") else int(c)
        out[cid] = float(substrate.node(c)["attrs"].get("state", 0.0))
    return out


def native_audit_basin(substrate, mt) -> dict[str, Any]:
    """Native analog of `substrate.mt_audit_basin(mt)`. Same return shape
    (energy, frustration, coverage, concept_count, marginal) computed from
    the SAME representation-agnostic primitives `audit_basin`
    (`can_ops.rs:422-463`) itself calls internally, but fed a DIRECT state
    read instead of `mt_mean_field_marginal`'s continuous relaxation — the
    "small, real composition" CAN_FINAL_MIGRATION_RESULTS.md Sec0 named and
    did not build. `coupling_count` is intentionally omitted: no real
    consumer in this codebase reads it (confirmed by grep across
    `domains/`), so it is not reproduced here rather than faked."""
    marginal = native_marginal_from_state(substrate, mt)
    if not marginal:
        return {
            "mt_id": mt.value if hasattr(mt, "value") else int(mt),
            "concept_count": 0, "marginal": {}, "energy": 0.0,
            "coverage": 0, "frustration": 0.0,
        }
    energy = substrate.mt_energy(mt, marginal)
    frustration = substrate.mt_frustration_given_state(mt, marginal)
    coverage = sum(1 for v in marginal.values() if abs(v) > 0.05)
    return {
        "mt_id": mt.value if hasattr(mt, "value") else int(mt),
        "concept_count": len(marginal),
        "marginal": marginal,
        "energy": energy,
        "coverage": coverage,
        "frustration": frustration,
    }


def native_distance_to_target(substrate, mt) -> dict[str, Any]:
    """Native analog of `substrate.mt_distance_to_target(mt)` — same
    {"magnitude", "per_node", "max_dev_node", "max_dev_value"} shape,
    computed from `mt_target`'s existing representation-agnostic target
    read against a DIRECT state read instead of a relaxed marginal."""
    target = substrate.mt_target(mt)
    current = native_marginal_from_state(substrate, mt)
    per_node: list[tuple[int, float]] = []
    sq_sum = 0.0
    max_dev_node = None
    max_dev_value = None
    for nid, t in target.items():
        c = current.get(nid, 0.0)
        d = c - t
        per_node.append((nid, d))
        sq_sum += d * d
        if max_dev_value is None or abs(d) > abs(max_dev_value):
            max_dev_node, max_dev_value = nid, d
    return {
        "magnitude": sq_sum ** 0.5,
        "per_node": per_node,
        "max_dev_node": max_dev_node,
        "max_dev_value": max_dev_value,
    }


def scoped_settle(substrate, mt, max_steps: int = DEFAULT_SCOPED_MAX_STEPS) -> int:
    """Let this Mt's own native rules run to a fixed point, ISOLATED from
    every other Mt in the graph — the mechanical composition this whole
    rung exists to enable. Returns the progressing-step count (same
    convention as `run_rules`/`run_rules_scoped`). Which rule fires (the
    discrete update, Hebbian mint/reweight, evidence decay — whatever is
    dirty and gated-open for this Mt) is entirely the graph's own decision,
    made by each rule's own `where`-clause; this function makes none."""
    return substrate.run_rules_scoped(max_steps, False, mt)


DEFAULT_MULTI_START_K = 20
"""Matches this arc's own established N_RESTARTS/N_DRAWS convention
(`scripts/bigville_can_integration_demo.py:38`,
`tests/test_can_native_reimplementation.py:115`,
`CAN_SOLVER_TRACTABILITY_PREREG.md` §1.2's own registered `K`)."""

_DISCRETE_VOCAB = {
    "3state": (-1.0, 0.0, 1.0),
    "2state": (-1.0, 1.0),
}


def install_multi_start_productions(substrate) -> None:
    """Admissibility-grammar productions for the candidate-session bookkeeping
    `multi_start_settle_and_pick_best` mints (Γ, not a filter — the same
    "generated absence" discipline `CLAUDE.md`'s SHAPES-NOT-NUMBERS section
    asks new subsystems to use). Mechanical registration, mirroring
    `worlds/bigville_can_beliefs.py::install_productions`'s own precedent —
    idempotent to call more than once (`add_production` on an
    already-installed production is a no-op at the grammar level, the same
    assumption every other seed-adjacent `install_productions` helper in
    this codebase already makes)."""
    for src_t, et, tgt_t in (
        ("Microtheory", "ms_session", "CanMultiStartSession"),
        ("CanMultiStartSession", "ms_candidate", "CanMultiStartCandidate"),
    ):
        substrate.add_production({
            "src": {"type": src_t, "var": "src"},
            "edge_type": et,
            "tgt": {"type": tgt_t, "var": "tgt"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "can_native_orchestration:multi_start",
        })


def multi_start_settle_and_pick_best(
    substrate, mt, k_starts: int = DEFAULT_MULTI_START_K,
    max_steps: int = DEFAULT_SCOPED_MAX_STEPS, rng: "random.Random | None" = None,
) -> dict[str, Any]:
    """Widen the search around the existing, UNMODIFIED, already-proven-
    convergent discrete-async update by trying `k_starts` independent random
    initial conditions on the SAME network and keeping the best-scoring
    stable state found — the correctness-preserving fix
    `CAN_SOLVER_TRACTABILITY_RESULTS.md` §1 measured a real need for
    (median relative spread 25.9%, median frac_at_best 30% on frustrated
    dense networks; real, if less frequent, spread on ~47% of real Bigville
    residents too).

    `can_native_update_3state`/`_2state`'s own rule body is NEVER touched —
    each of the `k_starts` calls to `scoped_settle` is an independent,
    ordinary run of the exact same mechanism `CAN_NATIVE_REIMPLEMENTATION_
    RESULTS.md`/`CAN_IDENTITY_FEEDBACK_RESULTS.md` already proved/measured
    convergent. This function only ADDS an outer selection layer: mint one
    `CanMultiStartCandidate` node per start (holding its converged
    `frustration` and per-Concept final `state`, all mechanically copied
    from existing reads, never decided), then let the `Argmin` Term
    (`term.rs:382`, already used across ~10 seeds) pick the winner by
    `frustration` — the DECISION lives in the Term evaluator, not in a
    Python `if`/`min()`. Committing the winner's stored state back onto the
    real Concepts is mechanical translation of that already-made decision.

    Returns `{"session": NodeID, "winner": NodeID, "frustration": float,
    "k_starts": int, "candidates": [NodeID, ...]}`. Non-deterministic across
    calls unless `rng` is seeded by the caller (mirrors every other
    multi-start helper in this codebase, e.g. `_basin_sweep`/
    `multi_start_basin_count`, which take the RNG as an explicit argument
    rather than owning one)."""
    if rng is None:
        rng = random.Random()
    install_multi_start_productions(substrate)
    concepts = list(substrate.neighbours(mt, "has_concept"))
    discrete_mode = substrate.node(mt)["attrs"].get("discrete_mode", "3state")
    vocab = _DISCRETE_VOCAB.get(discrete_mode, _DISCRETE_VOCAB["3state"])

    session = substrate.add_node("CanMultiStartSession", {"k_starts": k_starts})
    substrate.add_edge(mt, "ms_session", session, {})

    candidate_ids: list[Any] = []
    for _ in range(k_starts):
        # Mechanical random re-draw -- the same class of world-adapter I/O
        # `multi_start_basin_count`'s own `rng.choice(...)` re-seed already
        # performs for the continuous mechanism; no decision over graph
        # state here, only a fresh trial's starting point.
        for c in concepts:
            substrate.set_attr(c, "state", float(rng.choice(vocab)))
        scoped_settle(substrate, mt, max_steps=max_steps)
        state = native_marginal_from_state(substrate, mt)
        frustration = substrate.mt_frustration_given_state(mt, state)

        cand = substrate.add_node("CanMultiStartCandidate",
                                   {"frustration": float(frustration)})
        substrate.add_edge(session, "ms_candidate", cand, {})
        for c in concepts:
            cid = c.value if hasattr(c, "value") else int(c)
            substrate.set_attr(cand, "cand_state_%d" % cid, state.get(cid, 0.0))
        candidate_ids.append(cand)

    # The decision: which of the k_starts stable states is kept. Made by
    # the Argmin Term over the graph-resident candidates just minted, not
    # by Python.
    winner_term = Term(
        "Argmin",
        source=Term("Neighbours", node=Lit(session), edge_type="ms_candidate",
                     any_type=False),
        var_name="cand",
        value=Attr(Var("cand"), "frustration"),
    )
    winner = winner_term.evaluate(None, substrate)

    # Mechanical translation of the already-decided winner's stored state
    # back onto the real Concepts -- no decision left here.
    winner_attrs = substrate.node(winner)["attrs"]
    for c in concepts:
        cid = c.value if hasattr(c, "value") else int(c)
        val = winner_attrs.get("cand_state_%d" % cid)
        if val is not None:
            substrate.set_attr(c, "state", float(val))

    return {
        "session": session, "winner": winner,
        "frustration": float(winner_attrs["frustration"]),
        "k_starts": k_starts, "candidates": candidate_ids,
    }


__all__ = [
    "DEFAULT_SCOPED_MAX_STEPS",
    "DEFAULT_MULTI_START_K",
    "native_marginal_from_state",
    "native_audit_basin",
    "native_distance_to_target",
    "scoped_settle",
    "install_multi_start_productions",
    "multi_start_settle_and_pick_best",
]
