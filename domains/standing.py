"""standing — per-node standing weight: how much an impact on this entity counts.
The convergent term responsibility, moral-injury, and obligation all needed.

Entityness is a FLOAT — order.mantissa (the floating-point shape, again):
  · ORDER (integer) = the phase-boundary level — a jump in KIND:
        0 exists · 1 iterates-blindly · 2 purpose+awareness · 3 nomological
  · MANTISSA (fractional) = the smooth continuum WITHIN an order.
A fish and a great ape are both order-2; the ape's mantissa is higher. Order
boundaries are phase transitions (gaps between the ranges below); within an order
standing rises smoothly with the mantissa.

    standing(level) = range_lo[order] + mantissa·(range_hi-range_lo)[order],  × frame_reality

Stored ON graph nodes (entityness_level, frame_reality, standing). PRECAUTIONARY
DEFAULT: an UNASSESSED node reads HIGH (person-level) until assessed — the dangerous
failure is treating an unrecognised person as standing-zero.
"""
from __future__ import annotations

# per-order [lo, hi] standing ranges. GAPS between them = the phase jumps (order
# boundaries are transitions in kind: awareness appears at 2, self-understanding at 3).
ORDER_RANGE = {0: (0.00, 0.05), 1: (0.10, 0.25), 2: (0.50, 0.90), 3: (0.92, 1.00)}
PRECAUTIONARY = 0.70


def standing(level: float, frame_reality: float = 1.0) -> float:
    order = int(level)
    mantissa = max(0.0, min(0.999, float(level) - order))
    lo, hi = ORDER_RANGE.get(order, (0.0, 0.0))
    base = lo + mantissa * (hi - lo)
    return base * max(0.0, min(1.0, float(frame_reality)))


def tag_standing(substrate, node, level: float, frame_reality: float):
    """Write the float entityness level + standing onto a graph node."""
    substrate.set_attr(node, "entityness_level", float(level))
    substrate.set_attr(node, "frame_reality", float(frame_reality))
    substrate.set_attr(node, "standing", standing(level, frame_reality))


def node_standing(substrate, node) -> float:
    a = substrate.node(node)["attrs"]
    if "standing" in a:
        return float(a["standing"])
    if "entityness_level" in a and "frame_reality" in a:
        return standing(a["entityness_level"], a["frame_reality"])
    return PRECAUTIONARY  # unassessed ⇒ treat as a person until looked at, not free


def weighted_harm(base_harm: float, node_standing_value: float) -> float:
    return base_harm * node_standing_value
