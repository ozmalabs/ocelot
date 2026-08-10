"""correction_prune_Mt — substrate's 3rd correction.

Per the agent's pick from scripts/agent_designs_next.py:

  Chosen item: correction_prune_Mt
  Matches failure mode: fail_mode_sparse_Mt
  Definition from Mt:
    'For sparse Mt: lower β to 0 (no longer participating in
    effective H). Optionally remove entirely.'

Mechanism: when a SparseMtEvent fires for a Mt, lower its β to the
substrate-level minimum (BETA_MIN). The Mt remains in the graph (its
concepts, couplings, identity, target — all preserved) but its
effective influence on equilibria drops to near zero. β = BETA_MIN
makes tanh(β·field) ≈ β·field — nearly linear, near-zero σ.

The Mt isn't deleted because:
  · Pruning permanently would lose graph-resident history
  · Per the user's principle 'frozen permanently? never', removal
    should be a separate explicit decision
  · The Mt can be 'unpruned' by raising β back if a future event
    surfaces the need

This is the substrate's structural analogue of 'I'll stop attending
to this for now.'
"""
from __future__ import annotations

from typing import Any

from domains.correction_beta_reweight import BETA_MIN


def apply_prune_mt(substrate, mt) -> float:
    """Lower this Mt's β to BETA_MIN. Returns the new value."""
    substrate.set_attr(mt, "temperature", BETA_MIN)
    return BETA_MIN


def record_prune_applied(substrate, mt) -> Any | None:
    """Audit record of the prune."""
    mt_id = mt.value if hasattr(mt, "value") else int(mt)
    attrs = {
        "correction": "prune_Mt",
        "triggered_by": "sparse_Mt",
        "mt_id": int(mt_id),
        "mt_name": str(substrate.node(mt)["attrs"].get("name", "")),
        "new_beta": BETA_MIN,
    }
    try:
        node = substrate.add_node("CorrectionAppliedEvent", attrs)
    except Exception:
        return None
    return node


__all__ = ["apply_prune_mt", "record_prune_applied"]
