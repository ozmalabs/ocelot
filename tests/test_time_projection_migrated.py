"""THE FORWARD-PROJECTION READING OF THE TIME FIT — the migrated gate.

`time_axis` v1.2.0 adds a second, domain-neutral reading of the SAME `TimeInfer`
fit the orbit rules already compute: `order_fit` (the order the stream's own
generator was measured at) and `crossing` (how many steps that generator takes
to carry the stream to its frame origin).

The load-bearing claim: `crossing` forced to order 1 IS `margin / rate` — the
commonest quantity in any control loop, wearing no clock — and read at the
MEASURED order it is a different number, the difference being the curvature the
linear reading throws away.  Both readings come out of one rule, so no rule
ordering can separate them, and the floor is a reading rather than an absence.

Nothing here is domain-specific: the stream is anonymous integer coordinates.
"""
import json

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]


def _cells(r, c=5):
    """A fixed shape parked at row `r`; `c` stays clear of the origin so only
    the row coordinate closes on it."""
    return [["cell", r, c, "red"], ["cell", r + 1, c, "red"],
            ["cell", r + 2, c, "red"], ["cell", r + 2, c + 1, "red"]]


def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    s.set_attr(ag, "time_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(_cells(0)),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _run(frames, status="motion_seq"):
    s, ag, native = _boot()
    obs = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                                     "status": status, "key": ["motion"]})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    attrs = s.node(obs)["attrs"]
    projections = [s.node(n)["attrs"] for n in s.nodes("TemporalProjection")]
    return attrs, projections


# r = 100 - 6t: constant closing rate, last observed row 64.
LINEAR = [_cells(100 - 6 * t) for t in range(7)]
# r = 100 - (t^2 + 3t): accelerating, last observed row 46.
CURVED = [_cells(100 - (t * t + 3 * t)) for t in range(7)]
# No single generator carries every pair.
SHUFFLED = [_cells(r) for r in (100, 3, 71, 5, 44, 2, 61)]


def test_order_one_crossing_is_exactly_margin_over_rate():
    attrs, _ = _run(LINEAR)
    assert attrs["time_order_fit"] == 1
    # 64 remaining at 6 per step -> 11 steps (10.67 rounded up to a whole step).
    assert attrs["time_crossing"] == 11


def test_measured_order_reads_a_different_number_than_the_linear_one():
    attrs, _ = _run(CURVED)
    assert attrs["time_order_fit"] == 2
    # Read at order 2 the accelerating stream reaches the origin in 3 steps.
    # The order-1 reading of the same stream cannot produce this number: it
    # has no term for the curvature.
    assert attrs["time_crossing"] == 3
    linear_only, _ = _run(LINEAR)
    assert attrs["time_crossing"] != linear_only["time_crossing"]


def test_no_measured_structure_is_a_reading_not_an_absence():
    attrs, projections = _run(SHUFFLED)
    assert attrs["status"] == "time_none"
    assert attrs["time_order_fit"] == 0
    # The declared horizon itself: no measured structure => no measured
    # deadline. An honest floor, still materialised.
    assert attrs["time_crossing"] == 1024
    assert len(projections) == 1


def test_projection_is_materialised_on_every_path_exactly_once():
    for frames in (LINEAR, CURVED, SHUFFLED):
        attrs, projections = _run(frames)
        assert len(projections) == 1, frames[0]
        projection = projections[0]
        assert projection["source"] == "time_infer"
        assert projection["integer_native"] == 1
        assert projection["output_authority"] == 0
        # The node carries the same numbers the rule read — one fit, two
        # readings, never able to disagree.
        assert projection["order_fit"] == attrs["time_order_fit"]
        assert projection["crossing"] == attrs["time_crossing"]


def test_flag_off_is_inert():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    obs = s.add_node("Observation", {"frames": LINEAR, "dim_types": DT,
                                     "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    assert "time_crossing" not in s.node(obs)["attrs"]
    assert not list(s.nodes("TemporalProjection"))
