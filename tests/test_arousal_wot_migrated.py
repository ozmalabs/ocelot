"""AROUSAL / WINDOW-OF-TOLERANCE + CO-REGULATION gate (block 239000).

Window of tolerance (Siegel; Porges polyvagal; van der Kolk) + the altricial
co-regulation bond (Harlow, block 233000) as graph rules riding the REAL emotion
framework's AffectiveState.arousal (seeds/affective_state_core.json).

Pre-registration: AROUSAL_WOT_PREREG.md. Full-power result (N=60):
results/arousal_wot.json. This gate re-runs a modest N for CI-separation +
mechanism, plus the failable controls (absent caregiver, dysregulated
caregiver), glass-box, source audit and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.arousal_wot_run import (            # noqa: E402
    coreg_arm, plasticity_arm, separated, glass_box_reconstruct,
    source_audit, discipline)

N_GATE = 25  # modest N for the test; the headline N=60 lives in results/


@pytest.fixture(scope="module")
def coreg():
    return {
        "coreg": coreg_arm(caregiver_present=True, regulated_caregiver=True),
        "alone": coreg_arm(caregiver_present=False, regulated_caregiver=True),
        "dysreg": coreg_arm(caregiver_present=True, regulated_caregiver=False),
    }


@pytest.fixture(scope="module")
def plastic():
    return {
        "healed": plasticity_arm(caregiver_present=True, regulated_caregiver=True),
        "trauma": plasticity_arm(caregiver_present=False, regulated_caregiver=True),
    }


# ------------------------------------------------------ G-co-regulation (HEADLINE)
def test_g_coregulation_returns_faster_than_alone_ci_separated(coreg):
    """HEADLINE: a dysregulated infant returns to its window FASTER with a
    REGULATED caregiver present than ALONE, CI-separated."""
    c, a = coreg["coreg"]["return_ticks"], coreg["alone"]["return_ticks"]
    assert separated(a, c), (
        f"co-reg return {c} must sit CI-below alone {a} (faster with caregiver)")
    assert c["ci_hi"] < a["ci_lo"]


def test_g_coregulation_failable_control_absent_caregiver(coreg):
    """FAILABLE CONTROL: alone (caregiver absent) returns SLOWER -- the co-reg
    advantage is not an artefact of the protocol."""
    c, a = coreg["coreg"]["return_ticks"], coreg["alone"]["return_ticks"]
    assert a["mean"] > c["mean"]
    assert coreg["alone"]["censored_frac"] < 0.5, "alone must still recover (self-reg)"


def test_g_coregulation_failable_control_dysregulated_caregiver(coreg):
    """FAILABLE CONTROL: a DYSREGULATED caregiver (high own-arousal) does NOT
    co-regulate -- it pulls the infant the WRONG way and fails to return it to
    the window (censored), worse than being alone."""
    a, d = coreg["alone"]["return_ticks"], coreg["dysreg"]["return_ticks"]
    assert coreg["dysreg"]["censored_frac"] > 0.5, (
        f"a dysregulated caregiver must mostly FAIL to return the infant, "
        f"got censored_frac={coreg['dysreg']['censored_frac']}")
    assert d["mean"] > a["mean"], "dysregulated caregiver no better than alone"


# ------------------------------------------------------ G-window-widens (healing)
def test_g_window_widens_with_repeated_coregulation(plastic):
    """DEVELOPMENT: repeated co-regulation WIDENS the window, CI-separated above
    its initial band."""
    h = plastic["healed"]
    assert separated(h["hw_final"], h["hw_initial"]), (
        f"window must widen: final {h['hw_final']} vs initial {h['hw_initial']}")


def test_g_window_widen_failable_control_no_coregulation(plastic):
    """FAILABLE CONTROL: repeated stress WITHOUT co-regulation does NOT widen --
    it narrows (the trauma direction)."""
    t = plastic["trauma"]
    assert t["hw_final"]["ci_hi"] < t["hw_initial"]["ci_lo"], (
        "unsupported stress must NOT widen the window (it narrows)")


# ------------------------------------------------------ G-trauma-narrows (pathology)
def test_g_trauma_narrows_window_below_healed(plastic):
    """PATHOLOGY: repeated stress without co-regulation NARROWS the window,
    CI-separated BELOW the co-regulated arm."""
    h, t = plastic["healed"], plastic["trauma"]
    assert separated(h["hw_final"], t["hw_final"]), (
        f"traumatised window {t['hw_final']} must sit CI-below healed {h['hw_final']}")


def test_g_trauma_lowers_safety_prior_below_healed(plastic):
    """PATHOLOGY: trauma mis-sets the safety prior LOWER than the healed arm,
    CI-separated (the safety axis of the three foundational priors)."""
    h, t = plastic["healed"], plastic["trauma"]
    assert separated(h["safety_final"], t["safety_final"]), (
        f"traumatised safety_prior {t['safety_final']} must sit CI-below "
        f"healed {h['safety_final']}")


# ------------------------------------------------------ G-glass-box
def test_g_glass_box_reconstructs_from_graph():
    """Arousal, the window band, the caregiver's arousal, and the co-regulation
    coupling are all readable graph state (graph_to_dict)."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["coupling_edges"] == 1, "the attended_by co-regulation edge must be present"
    assert gb["returned_to_window"], "the co-regulated infant returned to its window"
    assert "hi" in gb["infant_window"] and "lo" in gb["infant_window"]
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
    depends only on the real affective_state_core, nine named rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["affective_state_core"]
    assert len(d["rule_names"]) == 9
