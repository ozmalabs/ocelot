"""correction_beta_reweight — second correction implemented.

Per the agent's design from scripts/agent_designs_next.py (2nd pick
after raise_plasticity):

  Chosen item: correction_beta_reweight
  Matches failure mode: fail_mode_conflicting_reflexes
  Definition from Mt:
    'For conflicting reflexes: explicit substrate-level decision
    raises β of one Mt, lowers the other. Frame choice made
    deliberate.'

Mechanism: when a ConflictEvent fires (two Mts disagree on a shared
node's σ), the substrate raises β on the Mt with the LARGER |σ| on
the conflicted node (= the Mt with stronger commitment in its own
basin) and reduces β on the other Mt. This makes the dominant-side
frame more decisive while the yielding side weakens its pull.

Substrate-level frame-choice — a deliberate action triggered by
detection. Per the Mt's own definition: 'Frame choice made
deliberate.'

The change is small per event (BETA_REWEIGHT_DELTA) so a single
conflict doesn't lock-in a frame. Sustained conflict gradually
shifts dominance toward the more-confident Mt.
"""
from __future__ import annotations

from typing import Any


BETA_REWEIGHT_DELTA = 0.05
"""Per-event β change. Small enough that one event doesn't dominate;
repeated conflict over the same node accumulates the shift."""

BETA_MIN = 0.05
"""Floor for β. Below this the Mt is effectively asleep (mean-field
flat). We don't go below."""

BETA_MAX = 5.0
"""Ceiling. Above this, marginals saturate at ±1 anyway."""


def apply_beta_reweight(
    substrate, mt_a, mt_b,
    sigma_a: float, sigma_b: float,
    delta: float = BETA_REWEIGHT_DELTA,
) -> dict[str, float]:
    """Raise β on the more-decisive Mt, lower β on the other.

    'More-decisive' = larger |σ| on the conflicted node. Returns dict
    of new (mt_a, mt_b) β values.

    If |σ_a| > |σ_b|: mt_a wins the frame; β_a += δ, β_b -= δ.
    Else:           mt_b wins; β_b += δ, β_a -= δ.
    Tie (within ε): both unchanged."""
    mt_a_attrs = substrate.node(mt_a)["attrs"]
    mt_b_attrs = substrate.node(mt_b)["attrs"]
    beta_a = float(mt_a_attrs.get("temperature", 1.0))
    beta_b = float(mt_b_attrs.get("temperature", 1.0))

    if abs(sigma_a) > abs(sigma_b) + 1e-3:
        new_a = max(BETA_MIN, min(BETA_MAX, beta_a + delta))
        new_b = max(BETA_MIN, min(BETA_MAX, beta_b - delta))
    elif abs(sigma_b) > abs(sigma_a) + 1e-3:
        new_a = max(BETA_MIN, min(BETA_MAX, beta_a - delta))
        new_b = max(BETA_MIN, min(BETA_MAX, beta_b + delta))
    else:
        new_a, new_b = beta_a, beta_b

    substrate.set_attr(mt_a, "temperature", new_a)
    substrate.set_attr(mt_b, "temperature", new_b)
    return {"mt_a_beta": new_a, "mt_b_beta": new_b}


def record_beta_reweight_applied(
    substrate, mt_a, mt_b, conflicted_node_id: int,
    new_betas: dict[str, float],
) -> Any | None:
    """Audit record of the substrate's frame-choice."""
    mt_a_id = mt_a.value if hasattr(mt_a, "value") else int(mt_a)
    mt_b_id = mt_b.value if hasattr(mt_b, "value") else int(mt_b)
    attrs = {
        "correction": "beta_reweight",
        "triggered_by": "conflicting_reflexes",
        "mt_a_id": int(mt_a_id),
        "mt_b_id": int(mt_b_id),
        "conflicted_node_id": int(conflicted_node_id),
        "new_beta_a": float(new_betas["mt_a_beta"]),
        "new_beta_b": float(new_betas["mt_b_beta"]),
    }
    try:
        node = substrate.add_node("CorrectionAppliedEvent", attrs)
    except Exception:
        return None
    return node


__all__ = [
    "BETA_REWEIGHT_DELTA",
    "BETA_MIN",
    "BETA_MAX",
    "apply_beta_reweight",
    "record_beta_reweight_applied",
]
