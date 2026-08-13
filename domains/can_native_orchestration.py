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
      CAN_HEBBIAN_MATERIALIZATION_RESULTS.md) do that.

No `if`/`else` here branches on graph state to decide a mutation — the only
mutation surface is "run the scoped fixpoint," a mechanical composition, not
a decision. Callers (self_improvement_loop.py etc.) own the
`discrete_mode`-gated dispatch between this module's native path and the
continuous can_ops path, matching the existing precedent
(`insight_seeking.py::seek_insights`'s own discrete_mode guard).
"""
from __future__ import annotations

from typing import Any

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


__all__ = [
    "DEFAULT_SCOPED_MAX_STEPS",
    "native_marginal_from_state",
    "native_audit_basin",
    "native_distance_to_target",
    "scoped_settle",
]
