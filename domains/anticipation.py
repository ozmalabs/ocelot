"""Anticipation reflex — order-2-time of frustration signals incipient insights.

The substrate's insight detection is reactive (fires AFTER the basin
transition). Anticipation is predictive: when frustration is high but
dropping AND that drop is accelerating, an insight is about to land.
The substrate can flag the incipient event before it crystallises.

Mechanism: compose the order-2-time Term-tree of frustration over a
3-sample window via the order_n_concepts machinery, evaluate via the
substrate's native evaluator, fire the reflex when:
  · F > MIN_FRUSTRATION_FOR_ANTICIPATION (must be in a frustrated state)
  · order-1-time-of-F < ANTICIPATION_DROP_THRESHOLD (F is dropping)
  · order-2-time-of-F < ANTICIPATION_CURVATURE_THRESHOLD (drop accelerating)
  · no insight already detected this step

Record AnticipationEvent nodes linked from the Mt via has_anticipation.
The substrate accumulates a history of 'I noticed this was coming'.
"""
from __future__ import annotations

from typing import Any

from domains.windowed_filter import (
    all_attrs_present,
    attr_sample,
    compose_and_evaluate,
    order_n_kernel,
    var_sample,
)


# Conservative defaults — must be in a frustrated state, with measurable
# drop and curvature.
MIN_FRUSTRATION_FOR_ANTICIPATION = 0.5
ANTICIPATION_DROP_THRESHOLD = -0.05
ANTICIPATION_CURVATURE_THRESHOLD = -0.02


def _f_window_samples():
    """Sample window for ∂²F: [prev_prev_F, prev_F (Attrs), current_F (Var)]."""
    return [
        attr_sample("mt", "previous_previous_frustration"),
        attr_sample("mt", "previous_frustration"),
        var_sample("current_F"),
    ]


_F_WINDOW_REQUIRED_ATTRS = [
    "previous_frustration",
    "previous_previous_frustration",
]


def compose_frustration_window_term(order: int):
    """Compose the order-N-time Term-tree over the substrate's 3-sample
    F window. Built via the shared windowed_filter primitive."""
    return order_n_kernel(_f_window_samples(), order)


def has_frustration_window(substrate, mt) -> bool:
    """True iff the Mt has both prior F values stashed (window ready)."""
    return all_attrs_present(substrate, mt, _F_WINDOW_REQUIRED_ATTRS)


def evaluate_order_time_of_f(
    substrate, mt, order: int, current_f: float,
) -> float | None:
    """Evaluate order-N-time of F via the substrate's evaluator over
    the shared 3-sample window. Returns None if window not ready."""
    return compose_and_evaluate(
        substrate, mt, _f_window_samples(), order=order,
        env={"mt": mt, "current_F": current_f},
        required_attrs=_F_WINDOW_REQUIRED_ATTRS,
    )


def detect_anticipation(
    substrate,
    mt,
    current_frustration: float,
    insight_already_detected: bool,
    min_frustration: float = MIN_FRUSTRATION_FOR_ANTICIPATION,
    drop_threshold: float = ANTICIPATION_DROP_THRESHOLD,
    curvature_threshold: float = ANTICIPATION_CURVATURE_THRESHOLD,
) -> dict[str, Any] | None:
    """Pattern-match the anticipation signature:

      · F[t] above min_frustration (we're still meaningfully frustrated)
      · order-1-time-of-F < drop_threshold (negative, dropping)
      · order-2-time-of-F < curvature_threshold (negative, accelerating)
      · no insight detected this step (otherwise the basin already
        landed — no anticipation, just observation)

    Returns an anticipation event dict if all conditions hold; None
    otherwise. The Term-trees are evaluated through the substrate's
    own evaluator — the agent's computation of its own derivatives."""
    if insight_already_detected:
        return None
    if current_frustration < min_frustration:
        return None
    if not has_frustration_window(substrate, mt):
        return None

    order_1 = evaluate_order_time_of_f(substrate, mt, 1, current_frustration)
    order_2 = evaluate_order_time_of_f(substrate, mt, 2, current_frustration)
    if order_1 is None or order_2 is None:
        return None

    if order_1 >= drop_threshold:
        return None
    if order_2 >= curvature_threshold:
        return None

    attrs = substrate.node(mt)["attrs"]
    return {
        "mt_id": mt.value if hasattr(mt, "value") else int(mt),
        "current_frustration": current_frustration,
        "previous_frustration": float(attrs["previous_frustration"]),
        "previous_previous_frustration": float(
            attrs["previous_previous_frustration"]),
        "order_1_time": order_1,
        "order_2_time": order_2,
    }


def record_anticipation(
    substrate,
    mt,
    event: dict[str, Any],
) -> Any | None:
    """Create an AnticipationEvent node linked from Mt via
    has_anticipation. Returns the new node or None if the production
    isn't configured."""
    attrs = {
        "current_frustration": float(event["current_frustration"]),
        "previous_frustration": float(event["previous_frustration"]),
        "previous_previous_frustration": float(
            event["previous_previous_frustration"]),
        "order_1_time": float(event["order_1_time"]),
        "order_2_time": float(event["order_2_time"]),
    }
    try:
        node = substrate.add_node("AnticipationEvent", attrs)
    except Exception:
        return None
    try:
        substrate.add_edge(mt, "has_anticipation", node, {})
    except Exception:
        pass
    return node


def list_anticipations(substrate, mt) -> list[dict[str, Any]]:
    """Walk Mt → has_anticipation → AnticipationEvent. Returns a
    summary list."""
    out: list[dict[str, Any]] = []
    for node in substrate.neighbours(mt, "has_anticipation"):
        attrs = substrate.node(node)["attrs"]
        nid = node.value if hasattr(node, "value") else int(node)
        out.append({
            "node_id": nid,
            "current_frustration": float(attrs.get("current_frustration", 0.0)),
            "order_1_time": float(attrs.get("order_1_time", 0.0)),
            "order_2_time": float(attrs.get("order_2_time", 0.0)),
        })
    return out


__all__ = [
    "MIN_FRUSTRATION_FOR_ANTICIPATION",
    "ANTICIPATION_DROP_THRESHOLD",
    "ANTICIPATION_CURVATURE_THRESHOLD",
    "compose_frustration_window_term",
    "has_frustration_window",
    "evaluate_order_time_of_f",
    "detect_anticipation",
    "record_anticipation",
    "list_anticipations",
]
