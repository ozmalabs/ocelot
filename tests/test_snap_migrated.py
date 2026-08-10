"""FRUSTRATED / ANGRY SNAPPING gate (block 242000).

The explosive episode of the developmental-emotion line (Ross Greene's explosive
child: "kids do well if they can"). A "snap" is an accumulating FRUSTRATION
RESIDUAL crossing the window of tolerance's UPPER bound, riding the REAL
AffectiveState.arousal (seeds/affective_state_core.json) + 239000's
WindowOfTolerance node, with the frustration accumulator reusing sd_blend's
leaky-EMA form. Three signatures, each a named rule: ABRUPT (all-or-none at
threshold), DISPROPORTIONATE (magnitude from the ACCUMULATED residual, NOT the
trigger), DISCHARGING (build->snap->drop->recover).

Pre-registration: SNAP_PREREG.md. Full-power result (N=60): results/snap.json.
This gate re-runs a modest N for the disproportion TEETH (same small trigger, no
snap at LOW residual but a SNAP at HIGH residual -- the "last straw"), the window
dose-response and its failable control, anger-by-attribution and its failable
control, co-regulation interrupting and its failable control, glass-box, source
audit and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.snap_run import (            # noqa: E402
    SEED_BASE, WIDTH_LEVELS, LOW_PRIOR, HIGH_PRIOR, TRIGGER_MAG,
    teeth_arm, abruptness_probe, width_arm, control_arm, anger_arm, coreg_arm,
    separated, overlap, glass_box_reconstruct, source_audit, discipline)

N_GATE = 20  # modest N for the test; the headline N=60 lives in results/


@pytest.fixture(scope="module")
def teeth():
    return {"low": teeth_arm(LOW_PRIOR, SEED_BASE + 10, n=N_GATE),
            "high": teeth_arm(HIGH_PRIOR, SEED_BASE + 20, n=N_GATE),
            "abrupt": abruptness_probe()}


@pytest.fixture(scope="module")
def window():
    return {"widths": {int(mu): width_arm(mu, SEED_BASE + 100 * (i + 1), n=N_GATE)
                       for i, mu in enumerate(WIDTH_LEVELS)},
            "control": control_arm(SEED_BASE + 900, n=N_GATE)}


@pytest.fixture(scope="module")
def anger():
    return {"blocker": anger_arm(True, SEED_BASE + 2000, n=N_GATE),
            "obstacle": anger_arm(False, SEED_BASE + 2100, n=N_GATE)}


@pytest.fixture(scope="module")
def coreg():
    return {"alone": coreg_arm(False, 1.0, SEED_BASE + 3000, n=N_GATE),
            "dysreg": coreg_arm(True, 0.0, SEED_BASE + 3100, n=N_GATE),
            "regulated": coreg_arm(True, 1.0, SEED_BASE + 3200, n=N_GATE)}


# ------------------------------------------------ G-snap-is-threshold (HEADLINE)
def test_g_snap_disproportion_teeth_same_trigger_low_vs_high_residual(teeth):
    """HEADLINE (the "last straw"): the SAME small trigger fires NO snap at LOW
    accumulated residual but a SNAP at HIGH residual -- proving it is the
    ACCUMULATION, not the trigger, that snaps. CI-separated (0 vs 1)."""
    low, high = teeth["low"]["snapped_on_trigger"], teeth["high"]["snapped_on_trigger"]
    assert low["mean"] == 0.0, f"low-residual arm must NOT snap on the trigger: {low}"
    assert high["mean"] >= 0.95, f"high-residual arm must snap on the IDENTICAL trigger: {high}"
    assert separated(high, low), (
        "the disproportion teeth must be CI-separated: same trigger, no snap at "
        f"low residual ({low}) vs snap at high residual ({high})")


def test_g_snap_magnitude_from_residual_not_trigger(teeth):
    """The snap MAGNITUDE is read from the accumulated residual (~105), NOT the
    small trigger (10) -- the disproportion. Ratio > 5x."""
    mag = teeth["high"]["snap_magnitude"]["mean"]
    trig = teeth["high"]["last_trigger_mag"]["mean"]
    assert trig == pytest.approx(TRIGGER_MAG), trig
    assert mag > 5.0 * trig, f"snap magnitude {mag} must be >5x the trigger {trig}"


def test_g_snap_gradual_build_abrupt_output(teeth):
    """Arousal/frustration builds GRADUALLY (max per-tick increment <= the trigger
    magnitude, a continuous ramp) while the snap OUTPUT is ABRUPT (all-or-none):
    snap_count steps in integer units and the snap magnitude exceeds the window's
    hi (arousal crossed the upper bound)."""
    a = teeth["abrupt"]
    assert a["snapped"], a
    assert a["max_ramp_increment"] <= TRIGGER_MAG + 1e-9, (
        f"the build must be gradual (increment <= {TRIGGER_MAG}), got "
        f"{a['max_ramp_increment']}")
    assert a["snap_count_integer_steps"], "the snap output must be all-or-none (integer)"
    assert a["magnitude_exceeds_hi"], "the snap magnitude must exceed the window's hi"
    assert a["gradual_build_abrupt_output"]


# ------------------------------------------------------ G-window-gates-snapping
def test_g_window_gates_snapping_monotone_ci_separated(window):
    """A NARROW window snaps SOONER (fewer blocks to threshold): blocks_to_snap is
    MONOTONE increasing in window WIDTH across >=3 widths, CI-separated -- the
    trauma profile (narrow window -> snaps on smaller triggers)."""
    w = window["widths"]
    lvls = sorted(w)
    assert len(lvls) >= 3
    for j in range(len(lvls) - 1):
        hi, lo = w[lvls[j + 1]]["blocks_to_snap"], w[lvls[j]]["blocks_to_snap"]
        assert separated(hi, lo), (
            f"blocks_to_snap must rise with width: {lvls[j+1]}->{hi} not CI-above "
            f"{lvls[j]}->{lo} (a flat relation = the window does not gate)")


def test_g_window_failable_control_max_width_never_snaps(window):
    """FAILABLE CONTROL: at MAX width the SAME block sequence never reaches
    threshold (snap_frac == 0). If the widest window still snaps, the window does
    not gate."""
    assert window["control"]["snap_frac"] == 0.0, window["control"]


# ------------------------------------------------------ G-anger-is-directed
def test_g_anger_attributable_blocker_directs_the_snap(anger):
    """With an attributable blocking AGENT the snap is DIRECTED at it (anger): a
    directed_at edge is minted at (essentially) every snap."""
    b = anger["blocker"]
    assert b["directed_frac"]["mean"] >= 0.95, b["directed_frac"]
    assert b["directed_at_edge_frac"]["mean"] >= 0.95, b["directed_at_edge_frac"]


def test_g_anger_failable_control_obstacle_is_undirected(anger):
    """FAILABLE CONTROL: with only an impersonal obstacle (no attributable
    blocker) the snap is UNDIRECTED distress -- NO directed_at edge. CI-separated
    below the blocker arm. If the obstacle arm also directs the snap, the
    attribution mechanism is fake."""
    b, o = anger["blocker"]["directed_frac"], anger["obstacle"]["directed_frac"]
    assert o["mean"] <= 0.05, f"obstacle arm must NOT direct the snap: {o}"
    assert anger["obstacle"]["undirected_frac"]["mean"] >= 0.95
    assert separated(b, o), f"directed(blocker)={b} must be CI-above obstacle={o}"


# ------------------------------------------------------ G-coreg-interrupts
def test_g_coreg_regulated_caregiver_interrupts_the_snap(coreg):
    """A regulated caregiver holds arousal below threshold -> FEWER/NO snaps vs
    alone. CI-separated (ties to the 239000 developmental line)."""
    alone, reg = coreg["alone"]["snap_frac"], coreg["regulated"]["snap_frac"]
    assert alone["mean"] >= 0.95, f"alone must snap: {alone}"
    assert reg["mean"] <= 0.10, f"a regulated caregiver must interrupt: {reg}"
    assert separated(alone, reg), f"alone={alone} must be CI-above regulated={reg}"


def test_g_coreg_failable_control_dysregulated_caregiver_still_snaps(coreg):
    """FAILABLE CONTROL: an absent/dysregulated caregiver does NOT interrupt -- it
    snaps like alone (overlaps alone, CI-separated ABOVE the regulated arm). If a
    dysregulated caregiver interrupted, co-regulation would not be the mechanism."""
    alone = coreg["alone"]["snap_frac"]
    dys = coreg["dysreg"]["snap_frac"]
    reg = coreg["regulated"]["snap_frac"]
    assert overlap(dys, alone), f"dysregulated {dys} must snap like alone {alone}"
    assert separated(dys, reg), f"dysregulated {dys} must be CI-above regulated {reg}"


# ------------------------------------------------------ G-glass-box
def test_g_glass_box_disproportion_readable_from_graph():
    """The accumulated residual, arousal, window bounds, the small trigger
    magnitude, the snap magnitude (residual, NOT trigger), and the attribution
    target (directed_at edge) all reconstruct from graph_to_dict -- the
    disproportion is READABLE (trigger small, residual at threshold)."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["last_trigger_mag"] == pytest.approx(TRIGGER_MAG)
    assert gb["snap_magnitude"] > gb["window_hi"], "the residual crossed the upper bound"
    assert gb["disproportion_readable"]
    assert gb["magnitude_from_residual_not_trigger"]
    assert gb["directed_at_target_edges"] == 1, "the attribution target is a graph edge"
    assert gb["snap_count"] >= 1.0


# ------------------------------------------------------ G-discipline
def test_g_discipline_no_python_decides_and_no_reward():
    """Source audit: no Python rule-engine call, and NO reward/punishment token
    (the snap is a STATE, never a badness -- Greene)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_reward_hits"] == []


def test_g_discipline_own_engine_and_default_off():
    """Own engine (source_match == own), seed self_load_only (default-OFF), depends
    only on the real affective_state_core, nine named snap_ rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["affective_state_core"]
    assert len(d["rule_names"]) == 9
    assert all(name.startswith("snap_") for name in d["rule_names"])
