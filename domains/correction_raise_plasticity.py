"""correction_raise_plasticity — first correction the substrate uses.

Per the agent's design from scripts/agent_designs_next.py (its first
choice after closing all 6 failure-mode detectors):

  Chosen item: correction_raise_plasticity
  Matches failure mode: fail_mode_frozen_should_adapt
  Definition from Mt:
    'For frozen-should-adapt: temporarily raise update rate η for
    that Mt. Or unfreeze if substrate-level approval.'

Mechanism:
  · When FrozenShouldAdaptEvent fires for a Mt, set a
    plasticity_override attr on that Mt with a small positive value.
  · The loop's maybe_hebbian respects the override: even on frozen Mts,
    if plasticity_override > 0, Hebbian runs with eta = override value.
  · The override DECAYS each step (slow return to fully frozen) AND
    resets to 0 immediately if distance drops back below the
    frozen_should_adapt threshold (the friction resolved on its own,
    no override needed).

The substrate now CLOSES THE LOOP for frozen_should_adapt:
  detection → correction → verify → metrics tracked → re-detect

User's principle 'frozen permanently? never' is now operational:
the substrate's frozen Mts CAN transiently unfreeze, evidence-driven,
with a slow decay back to identity protection. Never permanently
mutated, never permanently rigid.
"""
from __future__ import annotations

from typing import Any


PLASTICITY_OVERRIDE_INITIAL = 0.005
"""Initial eta granted when raise_plasticity fires. Small — about half
the baseline Hebbian eta. The substrate isn't fully unfreezing; it's
allowing a transient learning rate on a Mt that's normally rigid."""

PLASTICITY_OVERRIDE_DECAY = 0.05
"""Per-step multiplicative decay. Override fades over ~30 steps if
not refreshed."""

PLASTICITY_OVERRIDE_MIN = 1e-4
"""Below this, override resets to 0. Avoids accumulating tiny residue."""


def apply_raise_plasticity(substrate, mt) -> float:
    """Set or refresh the plasticity_override on this Mt. Returns the
    override value that's now in effect.

    If the override is already set (a previous detection raised it),
    refresh it to the initial value — substrate's noticing repeatedly
    that the friction persists, so it sustains the boost."""
    substrate.set_attr(mt, "plasticity_override",
                       PLASTICITY_OVERRIDE_INITIAL)
    return PLASTICITY_OVERRIDE_INITIAL


def decay_plasticity_override(substrate, mt) -> float:
    """Per-step decay of the plasticity_override. Returns the new
    value. Resets to 0 when below MIN."""
    attrs = substrate.node(mt)["attrs"]
    current = float(attrs.get("plasticity_override", 0.0))
    if current <= 0:
        return 0.0
    new_value = current * (1.0 - PLASTICITY_OVERRIDE_DECAY)
    if new_value < PLASTICITY_OVERRIDE_MIN:
        new_value = 0.0
    substrate.set_attr(mt, "plasticity_override", new_value)
    return new_value


def get_plasticity_override(substrate, mt) -> float:
    """Read current plasticity_override for the Mt. 0 if not set."""
    return float(substrate.node(mt)["attrs"].get(
        "plasticity_override", 0.0))


def record_correction_applied(
    substrate, mt, event_kind: str,
    correction_name: str = "raise_plasticity",
) -> Any | None:
    """Create a CorrectionAppliedEvent linking the Mt to the action
    taken. Lets us later audit 'what corrections has the substrate
    applied, and to what?'"""
    mt_id = mt.value if hasattr(mt, "value") else int(mt)
    attrs = {
        "mt_id": int(mt_id),
        "mt_name": str(substrate.node(mt)["attrs"].get("name", "")),
        "correction": correction_name,
        "triggered_by": event_kind,
    }
    try:
        node = substrate.add_node("CorrectionAppliedEvent", attrs)
    except Exception:
        return None
    return node


def list_corrections_applied(substrate) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("CorrectionAppliedEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_id": int(attrs.get("mt_id", -1)),
            "mt_name": str(attrs.get("mt_name", "")),
            "correction": str(attrs.get("correction", "")),
            "triggered_by": str(attrs.get("triggered_by", "")),
        })
    return out


__all__ = [
    "PLASTICITY_OVERRIDE_INITIAL",
    "PLASTICITY_OVERRIDE_DECAY",
    "PLASTICITY_OVERRIDE_MIN",
    "apply_raise_plasticity",
    "decay_plasticity_override",
    "get_plasticity_override",
    "record_correction_applied",
    "list_corrections_applied",
]
