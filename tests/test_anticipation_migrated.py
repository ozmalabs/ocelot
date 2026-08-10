"""anticipation reflex, migrated — order-2-time of frustration flags incipient
insights, run in the WorldAdapter (no CuriousAgent). Covers tests/test_anticipation.

The split, per the burn discipline:
  • WINDOW BOOKKEEPING is mechanical — the adapter stamps the rolling 3-sample
    frustration window (`previous_frustration` / `previous_previous_frustration`)
    on an AnticipationWindow node and rolls it each step.
  • THE DERIVATIVES are the agent computing its own metrics — order-N finite
    differences via the SUBSTRATE'S native evaluator over the shared
    windowed-filter kernel (`order_time_of_f`), the adapter only binds samples.
  • THE DECISION (the anticipation signature: F high, dropping, drop accelerating,
    no insight) is a DSL Term the SUBSTRATE evaluates over a stamped candidate —
    no Python if-else over the signal.

So: stamp the window -> the substrate computes the derivatives + decides ->
the adapter records/reads the AnticipationEvent history.
"""
from __future__ import annotations

from domains.windowed_filter import attr_sample, order_n_kernel, var_sample
from substrate.world_adapter import WorldAdapter


# --- Term-tree composition + native evaluation ---------------------------

def test_order_1_kernel_composes_a_minus_term():
    """The order-1 frustration kernel is the agent's own windowed-filter
    Term — it .to_dict()s into the Minus the evaluator expects."""
    term = order_n_kernel(
        [attr_sample("mt", "previous_frustration"), var_sample("current_F")], 1)
    assert term is not None
    assert term.to_dict()["type"] == "Minus"


def test_evaluate_order_1_matches_manual_diff():
    """Native eval of order-1-time-of-F equals current - previous."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=3.0, previous=2.5)
    # order-1 = 1.8 - 2.5 = -0.7
    assert abs(wa.order_time_of_f("m", 1, 1.8) - (-0.7)) < 1e-5


def test_evaluate_order_2_matches_closed_form():
    """order-2-time-of-F = F[t] - 2*F[t-1] + F[t-2]."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=4.0, previous=3.0)
    # order-2 = 1.5 - 2*3.0 + 4.0 = -0.5
    assert abs(wa.order_time_of_f("m", 2, 1.5) - (-0.5)) < 1e-5


def test_window_evaluation_returns_none_without_window():
    wa = WorldAdapter()
    assert wa.order_time_of_f("nope", 1, 1.0) is None
    assert wa.order_time_of_f("nope", 2, 1.0) is None


# --- detect_anticipation: the substrate evaluates the signature ----------

def test_anticipation_fires_on_high_F_with_accelerating_drop():
    """F high, order-1 < drop_threshold, order-2 < curvature_threshold,
    no insight: anticipation fires."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=3.0, previous=2.5)
    # current F = 1.7. order-1 = -0.8 (< -0.05). order-2 = 1.7 - 5.0 + 3.0 = -0.3 (< -0.02).
    event = wa.detect_anticipation("m", 1.7, insight_detected=False)
    assert event is not None
    assert event["current_frustration"] == 1.7
    assert event["order_1_time"] < 0
    assert event["order_2_time"] < 0


def test_anticipation_suppressed_if_insight_already_detected():
    """Insight already fired this step -> no anticipation (the basin already
    landed; observation, not anticipation)."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=3.0, previous=2.5)
    assert wa.detect_anticipation("m", 1.7, insight_detected=True) is None


def test_anticipation_suppressed_when_F_low():
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=0.4, previous=0.3)
    # F below threshold even though derivatives are negative.
    assert wa.detect_anticipation("m", 0.1, insight_detected=False) is None


def test_anticipation_suppressed_when_drop_too_small():
    """order-1 not below threshold."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=2.0, previous=2.0)
    # current F = 1.99 -> order-1 = -0.01 (above -0.05)
    assert wa.detect_anticipation("m", 1.99, insight_detected=False) is None


def test_anticipation_suppressed_when_curvature_wrong_sign():
    """order-1 negative but order-2 POSITIVE (drop decelerating)."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=4.0, previous=2.5)
    # current F = 1.9: order-1 = -0.6 (drop), order-2 = 1.9 - 5.0 + 4.0 = +0.9.
    assert wa.detect_anticipation("m", 1.9, insight_detected=False) is None


def test_anticipation_suppressed_without_window():
    wa = WorldAdapter()
    assert wa.detect_anticipation("never", 3.0, insight_detected=False) is None


# --- end-to-end: a gradual accelerating drop fires anticipation ----------

def test_gradual_drop_records_anticipation():
    """Drive a gradually-dropping frustration trace (accelerating descent)
    through the window. Anticipation should fire somewhere during the ramp,
    before F bottoms out — and be recorded as AnticipationEvent history."""
    wa = WorldAdapter()
    # Frustration dropping with an accelerating (negative-curvature) descent.
    trace = [3.0, 2.9, 2.7, 2.4, 2.0, 1.5, 0.9]
    wa.set_frustration_window("ramp", previous_previous=trace[0],
                              previous=trace[1])
    saw = False
    for f in trace[2:]:
        event = wa.detect_anticipation("ramp", f, insight_detected=False)
        if event is not None:
            wa.record_anticipation("ramp", event)
            saw = True
        wa.roll_frustration("ramp", f)
    assert saw, "expected anticipation to fire during the accelerating drop"
    assert len(wa.anticipations("ramp")) > 0


def test_anticipation_not_recorded_when_insight_fires():
    """Even on a perfect anticipation signature, an insight this step
    suppresses it (already landed; observation, not anticipation)."""
    wa = WorldAdapter()
    wa.set_frustration_window("m", previous_previous=3.0, previous=2.5)
    assert wa.detect_anticipation("m", 1.7, insight_detected=True) is None
    assert wa.anticipations("m") == []


def test_list_anticipations_round_trip():
    wa = WorldAdapter()
    wa.set_frustration_window("r", previous_previous=3.0, previous=2.5)
    event = wa.detect_anticipation("r", 1.7, insight_detected=False)
    assert event is not None
    recorded = wa.record_anticipation("r", event)
    assert recorded is not None
    listed = wa.anticipations("r")
    assert len(listed) == 1
    assert abs(listed[0]["current_frustration"] - 1.7) < 1e-5
    assert listed[0]["order_2_time"] < 0
