"""WINDOW-AS-A-KNOB gate (block 241000).

Deepens block 239000's arousal/window-of-tolerance/co-regulation dyad into its
genuine prior-art delta: the window of tolerance as a FORMAL, settable,
inspectable window-WIDTH knob with a measured onset-vs-width dose-response
(G-knob, HEADLINE), and a BIDIRECTIONAL dyad in which the caregiver's OWN window
WIDTH governs co-regulation capacity (G-bidirectional). Rides the REAL
AffectiveState.arousal (seeds/affective_state_core.json) + 239000's
WindowOfTolerance node; reuses the same sd_blend leaky-EMA pull form.

Pre-registration: WINDOW_KNOB_PREREG.md. Full-power result (N=60):
results/window_knob.json. This gate re-runs a modest N for CI-separation +
mechanism, plus the failable controls (the placebo k_self axis; a wide-window
caregiver NOT pulled in), glass-box, source audit and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.window_knob_run import (            # noqa: E402
    SEED_BASE, WIDTH_LEVELS, CAREGIVER_ARMS, PLACEBO_KSELF,
    width_arm, placebo_arm, caregiver_arm, separated, overlap,
    glass_box_reconstruct, source_audit, discipline)

N_GATE = 20  # modest N for the test; the headline N=60 lives in results/


@pytest.fixture(scope="module")
def knob():
    widths = {int(mu): width_arm(mu, SEED_BASE + 100 * i, n=N_GATE)
              for i, mu in enumerate(WIDTH_LEVELS)}
    placebo = [placebo_arm(k, SEED_BASE + 400 + 100 * i, n=N_GATE)
               for i, k in enumerate(PLACEBO_KSELF)]
    return {"widths": widths, "placebo": placebo}


@pytest.fixture(scope="module")
def dyad():
    return {name: caregiver_arm(hw, SEED_BASE + 1000 + 100 * i, n=N_GATE)
            for i, (name, hw) in enumerate(CAREGIVER_ARMS.items())}


# ------------------------------------------------------ G-knob (HEADLINE)
def test_g_knob_onset_threshold_monotone_in_width_ci_separated(knob):
    """HEADLINE: the stressor MAGNITUDE at which the infant dysregulates is a
    MONOTONIC function of window WIDTH, CI-separated across >=3 widths -- the
    formal, measurable window of tolerance the clinical models never had."""
    w = knob["widths"]
    lvls = sorted(w)
    assert len(lvls) >= 3
    for j in range(len(lvls) - 1):
        hi, lo = w[lvls[j + 1]], w[lvls[j]]
        assert separated(hi, lo), (
            f"onset threshold must rise with width: {lvls[j+1]}->{hi} not "
            f"CI-above {lvls[j]}->{lo} (a flat/non-monotone relation = fake knob)")
    # the threshold tracks the width itself (threshold ~= half-width = hi).
    for mu in lvls:
        assert abs(w[mu]["mean"] - mu) < 3.0, (
            f"onset threshold {w[mu]['mean']} should track the width knob {mu}")


def test_g_knob_placebo_axis_is_flat_failable_control(knob):
    """FAILABLE CONTROL: sweeping the self-reg gain k_self at FIXED width leaves
    the onset threshold FLAT (CIs overlap) -- the knob is the WIDTH, not just any
    parameter. If this axis were monotone, the width result would be an artefact."""
    p = knob["placebo"]
    for i in range(len(p) - 1):
        assert overlap(p[i], p[i + 1]), (
            f"placebo k_self axis must be FLAT (overlapping CIs), got {p[i]} vs "
            f"{p[i+1]} -- a monotone placebo would mean the knob is not the width")


# ------------------------------------------------------ G-bidirectional
def test_g_bidirectional_mutual_entrainment_both_arms(dyad):
    """The infant's distress PULLS the caregiver's arousal (bidirectional) in
    BOTH arms -- the caregiver is moved by the infant, not held fixed (239000's
    residual)."""
    assert dyad["wide"]["cg_peak_arousal"]["ci_lo"] > 8.0
    assert dyad["narrow"]["cg_peak_arousal"]["ci_lo"] > 8.0


def test_g_bidirectional_narrow_caregiver_pulled_into_codysregulation(dyad):
    """A NARROW-window caregiver is pulled OUT of its own window (co-dysregulation)
    -- its regulated flag flips, almost always."""
    assert dyad["narrow"]["cg_dysreg_frac"]["mean"] >= 0.9, dyad["narrow"]["cg_dysreg_frac"]


def test_g_bidirectional_wide_caregiver_not_pulled_in_failable_control(dyad):
    """FAILABLE CONTROL: a WIDE-window (well-regulated) caregiver is NOT pulled
    into co-dysregulation -- CI-separated below the narrow arm. If a wide
    caregiver dysregulated as often as a narrow one, the width->capacity link is
    false."""
    assert dyad["wide"]["cg_dysreg_frac"]["mean"] <= 0.1
    assert separated(dyad["narrow"]["cg_dysreg_frac"], dyad["wide"]["cg_dysreg_frac"])


def test_g_bidirectional_narrow_fails_to_coregulate_ci_separated(dyad):
    """The UNIFICATION: the caregiver's window WIDTH governs co-regulation
    capacity -- a wide caregiver co-regulates FAST, a narrow one FAILS (returns
    CI-slower, reduced to the infant's self-regulation)."""
    assert separated(dyad["narrow"]["return_ticks"], dyad["wide"]["return_ticks"]), (
        f"narrow-caregiver return {dyad['narrow']['return_ticks']} must sit "
        f"CI-above wide {dyad['wide']['return_ticks']} (co-regulation capacity lost)")


# ------------------------------------------------------ G-glass-box
def test_g_glass_box_reconstructs_both_agents_from_graph():
    """Both arousals, both window bands [lo,hi] (WIDTHs), the caregiver's
    regulated/dysregulated flags, and the co-regulation coupling edge are all
    readable graph state (graph_to_dict)."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["coupling_edges"] == 1, "the attended_by coupling edge must be present"
    assert gb["infant_window"]["width"] == 60.0
    assert gb["caregiver_window"]["width"] == 20.0   # the NARROW caregiver knob
    assert gb["caregiver_pulled_in"], "the narrow caregiver was pulled into co-dysreg"
    assert isinstance(gb["caregiver_arousal"], float)


# ------------------------------------------------------ G-discipline
def test_g_discipline_no_python_decides_and_no_reward():
    """Source audit: no Python rule-engine call, and NO reward/punishment token
    (dysregulation is a STATE, never a badness -- Greene)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_reward_hits"] == []


def test_g_discipline_own_engine_and_default_off():
    """Own engine (source_match == own), seed self_load_only (default-OFF),
    depends only on the real affective_state_core, eleven named rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["affective_state_core"]
    assert len(d["rule_names"]) == 11
