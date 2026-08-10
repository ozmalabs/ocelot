"""TERM-EVAL COUNTER + G5 RESPONSIVENESS — the gate.

Pre-registration: `VISION_TERM_EVAL_COUNTER_PREREG.md` (committed `7c382089`,
BEFORE any implementation). Results: `VISION_TERM_EVAL_COUNTER_RESULTS.md`.

WHY THESE RUN HERE AND NOT UNDER `cargo test`. `runners/dsl/Cargo.toml` sets
pyo3's `extension-module` UNCONDITIONALLY, so `cargo test` cannot link this
crate — **PRE-EXISTING**, recorded in `VISION_SCALE_SPLIT_RESULTS.md` §1.2 and
`VISION_INK_VENTRAL_RESULTS.md`. The `#[cfg(test)]` tests in `g5.rs` and
`scale_audit.rs` are unrunnable in this tree, so the gates run against the
**SHIPPED ENGINE** — which is the stronger place for them anyway: it tests the
binary that actually produced the numbers, and the §10 two-binary hazard is
exactly a case where source and artifact disagreed while both agents reported
green. The series below are the SAME series the Rust unit tests assert on, so
the two cannot silently diverge.

WHAT IS BEING GATED, and why it is not the usual liveness suite:

`VISION_VIDEO_PROBE_RERUN_RESULTS.md` §3.1 recorded a counter that was ALIVE,
DETERMINISTIC, CONSERVED — and INSENSITIVE. Every gate this arc had asks "is it
non-zero?"; none asked "does it MOVE WITH the thing being varied?" These tests
gate that question, and they gate G5's own ability to go red.
"""
from __future__ import annotations

import gc
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from substrate_rs import _native  # noqa: E402

AUDIT = _native.Substrate


@pytest.fixture(autouse=True)
def _audit_off():
    """Leave the audit OFF around every test. A test that leaves it on would
    contaminate every later test's counters AND every committed result measured
    in the same process (PROTOCOL §9)."""
    AUDIT.scale_audit_set_enabled(False)
    AUDIT.scale_audit_reset()
    yield
    AUDIT.scale_audit_set_enabled(False)
    AUDIT.scale_audit_reset()


# --------------------------------------------------------------------------- #
# G5 — the gate itself, positive-controlled BOTH WAYS.
#
# A gate that has never been shown to fail has not been tested. This arc has
# paid for that lesson repeatedly, so the red control comes first.
# --------------------------------------------------------------------------- #

def test_g5_goes_RED_on_the_actual_A8_signature():
    """THE RED CONTROL, and it is not synthetic: these are A8's own numbers.

    253 counted ops at every one of seven points across an 11.8x range of N,
    while wall-clock grew 13x. Alive (non-zero), deterministic (control span 0),
    conserved — and constant. If G5 does not flag THIS, G5 is decorative."""
    a8_sweep = [253, 253, 253, 253, 253, 253, 253]
    a8_control = [253] * 7
    assert AUDIT.scale_audit_g5_verdict(a8_sweep, a8_control) == "BLIND"


def test_g5_goes_GREEN_on_a_responsive_counter():
    assert AUDIT.scale_audit_g5_verdict([10, 20, 40, 80, 160, 320, 640],
                                        [10] * 7) == "RESPONSIVE"


def test_g5_never_passes_an_unexercised_counter():
    """INERT is explicitly NOT a pass. It is a statement that the counter
    remains unvalidated — pre-registered as a distinct verdict precisely so
    that 'it was never exercised' cannot afterwards be argued as a pass."""
    assert AUDIT.scale_audit_g5_verdict([0] * 7, [0] * 7) == "INERT"
    assert AUDIT.scale_audit_g5_verdict([0] * 7, [0] * 7) != "RESPONSIVE"


def test_g5_never_passes_on_no_data():
    assert AUDIT.scale_audit_g5_verdict([], []) == "INERT"


def test_g5_criterion_is_the_MEASURED_control_not_an_assumed_zero():
    """The threshold is not chosen and not assumed — it is the control's own
    span (PROTOCOL §13: the number falls out).

    Movement EQUAL to the noise fails; movement BEYOND a NON-ZERO noise floor
    passes. Both directions are asserted, because a criterion that only ever
    sees a zero control has not been shown to be using the control at all."""
    noisy_ctrl = [10, 11, 12, 10, 11, 12, 10]
    assert AUDIT.scale_audit_g5_verdict([10, 11, 10, 11, 10, 11, 10],
                                        [10, 11, 11, 10, 10, 11, 10]) == "BLIND"
    assert AUDIT.scale_audit_g5_verdict([10, 30, 50, 70, 90, 110, 130],
                                        noisy_ctrl) == "RESPONSIVE"


def test_rho_is_undefined_rather_than_fabricated():
    """rho is REPORTED, NEVER GATED. When it cannot be computed it must return
    None, not 0.0 — a fabricated 0.0 would read as 'measured and blind', which
    is the precise misreading this whole rung exists to prevent."""
    axis = [1.0, 2.0, 4.0, 8.0]
    assert abs(AUDIT.scale_audit_g5_rho([10, 20, 40, 80], axis) - 1.0) < 1e-12
    assert abs(AUDIT.scale_audit_g5_rho([10, 10, 10, 10], axis) - 0.0) < 1e-12
    assert AUDIT.scale_audit_g5_rho([0, 20, 40, 80], axis) is None
    assert AUDIT.scale_audit_g5_rho([10, 20, 40, 80], [2.0, 2.0, 2.0, 2.0]) is None


# --------------------------------------------------------------------------- #
# The counter itself.
# --------------------------------------------------------------------------- #

def _snapshot() -> dict:
    return dict(AUDIT.scale_audit_snapshot())


def test_the_term_family_is_present_in_the_shipped_engine():
    """The totals are emitted UNCONDITIONALLY, so 'the family is there and
    everything is zero' stays distinguishable from 'the family is missing'.

    That distinction is load-bearing: a missing instrument reading as a clean
    result is how eleven inert instruments survived in this arc."""
    snap = _snapshot()
    assert "term_evals_total" in snap
    assert "term_units_total" in snap
    assert "term_units_unattributed" in snap


def test_zero_when_off_on_a_LIVE_workload():
    """PROTOCOL §9 — the default preserves committed results.

    LIVE, deliberately: a zero-when-off gate on a dead workload proves only that
    nothing ran (§1.1 — 'scores at the floor' is satisfied by DEATH). Liveness
    is established by re-running the SAME workload with the audit ON."""
    from domains import reflective_faculty as rf
    from substrate.boot_core import boot_core
    import domains.seed_registry  # noqa: F401

    def workload():
        gc.collect()
        s, ag = boot_core()
        native = rf._native_eval2(s)
        rf._ensure_shape_decode_loop(s, native, ag)
        cells = [["cell", r, c, "v1"] for r in range(6) for c in range(6)]
        s.add_node("ShapeSignature",
                   {"name": "held0", "signature": json.dumps(cells),
                    "kind": "faculty", "faculty": "held0",
                    "dim_types": ["pred", "coord:r", "coord:c", "val"]})
        ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
        obs = s.add_node("Observation",
                         {"signature": cells, "key": ["probe"], "status": "decoded",
                          "residual": cells, "decoded_epoch": ep,
                          "dim_types": ["pred", "coord:r", "coord:c", "val"]})
        s.add_edge(ag, "observed", obs)
        native.run_rules()

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(False)
    workload()
    off = _snapshot()
    assert all(v == 0 for v in off.values()), \
        f"a counter moved while the audit was OFF: {[k for k, v in off.items() if v]}"

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    workload()
    AUDIT.scale_audit_set_enabled(False)
    on = _snapshot()
    assert on["term_evals_total"] > 0, "the OFF arm was measuring a DEAD workload"
    assert on["term_units_total"] > 0, "the sd interior sites did not fire"


def test_units_attribute_to_a_variant_and_none_are_orphaned():
    """`term_units_unattributed` must stay 0: a unit charged with no Term
    evaluation in progress is REPORTED, never silently dropped and never
    misfiled onto whichever variant happened to run last."""
    from domains import reflective_faculty as rf
    from substrate.boot_core import boot_core
    import domains.seed_registry  # noqa: F401

    gc.collect()
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    cells = [["cell", r, c, "v1"] for r in range(6) for c in range(6)]
    s.add_node("ShapeSignature",
               {"name": "held0", "signature": json.dumps(cells), "kind": "faculty",
                "faculty": "held0", "dim_types": ["pred", "coord:r", "coord:c", "val"]})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": cells, "key": ["probe"], "status": "decoded",
                      "residual": cells, "decoded_epoch": ep,
                      "dim_types": ["pred", "coord:r", "coord:c", "val"]})
    s.add_edge(ag, "observed", obs)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    native.run_rules()
    AUDIT.scale_audit_set_enabled(False)
    snap = _snapshot()

    assert snap["term_units_unattributed"] == 0
    per_variant = {k: v for k, v in snap.items() if k.startswith("term_unit:")}
    assert per_variant, "units were counted but attributed to no variant"
    assert sum(per_variant.values()) == snap["term_units_total"]


def test_per_variant_counts_are_not_pre_aggregated():
    """A Plus and a ShapeDecode are not the same cost. A single total would have
    told A8 'the number went up' without telling it WHERE — which is the
    question the next rung has to answer."""
    from domains import reflective_faculty as rf
    from substrate.boot_core import boot_core
    import domains.seed_registry  # noqa: F401

    gc.collect()
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    native.run_rules()
    AUDIT.scale_audit_set_enabled(False)
    snap = _snapshot()

    cells = {k: v for k, v in snap.items() if k.startswith("term_eval:")}
    assert len(cells) > 1, "the per-variant profile collapsed to a single row"
    assert sum(cells.values()) == snap["term_evals_total"], \
        "the per-variant cells do not conserve to the total"


# --------------------------------------------------------------------------- #
# The pinned result. PROTOCOL §12.3 — pinned to values, not to a mutable tree.
# --------------------------------------------------------------------------- #

RESULTS = os.path.join(ROOT, "results", "g5_responsiveness.json")


@pytest.mark.skipif(not os.path.exists(RESULTS), reason="raw rows not present")
def test_the_committed_sweep_reproduces_its_headline_verdicts():
    """The rung's headline, pinned to the committed raw rows.

    Pins the SHAPE of the finding, not every integer: the two new families'
    verdicts (term_eval BLIND / term_unit RESPONSIVE — P1 confirmed and the
    reason both families exist), G5's own two positive controls, and the
    retroactive counts."""
    d = json.load(open(RESULTS))
    v = d["g5_on_claimed_axis"]

    # P1: invocation counts are BLIND on the sd axis, exactly as designed.
    assert v["term_evals_total"]["verdict"] == "BLIND"
    assert v["term_eval:TransformDecode"]["verdict"] == "BLIND"
    # The interior-unit family sees it.
    assert v["term_units_total"]["verdict"] == "RESPONSIVE"
    assert v["term_unit:TransformDecode"]["verdict"] == "RESPONSIVE"
    assert v["term_unit:DimInfer"]["verdict"] == "RESPONSIVE"

    # G5's own controls, both directions.
    assert d["g5_self_controls_all_ok"] is True
    assert d["g5_self_controls"]["RED_must_go_BLIND"]["got"] == "BLIND"
    assert d["g5_self_controls"]["GREEN_must_go_RESPONSIVE"]["got"] == "RESPONSIVE"

    # The retroactive finding: the two enumeration counters are BLIND to graph
    # size and proportional to epochs. Both halves pinned, because the second
    # is what makes the first a claim-table error rather than a broken counter.
    assert v["rule_enumerations"]["verdict"] == "BLIND"
    cross = d["cross_table_all_counters_all_sweeps"]
    assert cross["rule_enumerations"]["E"] == "RESPONSIVE"
    assert cross["rule_enumerations"]["G"] == "BLIND"

    # The three never-exercised counters.
    for n in ("cand_enum_hinted", "cand_reject_bound", "var_collisions"):
        assert v[n]["verdict"] == "INERT"

    # Liveness of the sd sweep: a sweep that recognises nothing would be a
    # sweep of an empty loop (PROTOCOL §1.1).
    assert all(r["liveness"] == "recognized_transformed"
               for r in d["sweeps"]["S"]["rows"])

    # The gates.
    assert d["G1_zero_when_off"]["all_zero_while_off"] is True
    assert d["G1_zero_when_off"]["workload_was_live"] is True
    assert d["G3_determinism"]["byte_identical"] is True


PREFIX = os.path.join(ROOT, "results", "g5_responsiveness_PREFIX_inert.json")


@pytest.mark.skipif(not (os.path.exists(RESULTS) and os.path.exists(PREFIX)),
                    reason="raw rows not present")
def test_the_dead_instrument_fix_changed_ONLY_the_unit_cells():
    """§4 — the fix added charging sites and touched nothing else.

    Asserted rather than asserted-in-prose: if the fix had perturbed any other
    counter, the pre-fix and post-fix runs would not be comparable, and the
    'G5 caught my dead instrument' story would be resting on two different
    measurements dressed as one."""
    a = json.load(open(PREFIX))
    b = json.load(open(RESULTS))
    differing = []
    for ax in ("G", "B", "E", "S"):
        for ra, rb in zip(a["sweeps"][ax]["rows"], b["sweeps"][ax]["rows"]):
            for k in set(ra["counters"]) | set(rb["counters"]):
                if ra["counters"].get(k, 0) != rb["counters"].get(k, 0):
                    differing.append((ax, k))
    non_unit = [d for d in differing if not d[1].startswith("term_unit")]
    assert not non_unit, f"the fix perturbed counters it should not have: {non_unit}"
    assert differing, "the fix changed nothing at all — the wrong file is pinned"

    # And the pre-fix run really was the INERT reading.
    assert all(r["counters"].get("term_units_total", 0) == 0
               for r in a["sweeps"]["S"]["rows"])


@pytest.mark.skipif(not os.path.exists(RESULTS), reason="raw rows not present")
def test_every_counter_was_judged_on_its_PRE_REGISTERED_axis():
    """The claim table is the prereg's, unedited.

    A counter allowed to pick its axis after seeing its verdict would pass
    unfairly, and `rule_enumerations` is exactly the counter that temptation
    applies to. This asserts the axis assignments still match the ones fixed
    before measurement."""
    d = json.load(open(RESULTS))
    claimed = d["claimed_axis"]
    assert claimed["rule_enumerations"] == "G", \
        "the claim table was edited after the result — see prereg §4.1"
    assert claimed["rule_enumerations_repeat"] == "G"
    assert claimed["cand_enum"] == "G"
    assert claimed["epochs"] == "E"
    assert claimed["ffi_calls"] == "B"
    for name, ax in claimed.items():
        assert d["g5_on_claimed_axis"][name]["axis"] == ax
