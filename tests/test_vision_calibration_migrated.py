"""THE CALIBRATION REFRAME — the gates for what this rung actually established.

The rung STOPPED at the measure-calibration gate (VISION_CALIBRATION_PREREG.md
§12). These tests pin the facts that stopped it, so the stop cannot silently
rot into a different claim later:

  1. The measure is a HALF-MEASURE: sound at the low end (an ideal Gabor with
     no reference is useless), DEGENERATE at the high end (base -> 0 => RPI
     unbounded). A gate whose measure ranks "no input at all" above a perfect
     Gabor is not a gate (PROTOCOL §1).
  2. The reference is placed by the ARCHITECTURE'S TONIC DRIVE, not by the
     input: waves and blank put theta in the same place.
  3. The theta channel HAS a genuine fixed point (PROTOCOL §2).

A test that has never failed is not a test, so each asserts the DEFECT is real,
not merely that the good path works.

Engine: these numbers are from `95167c01b7b3` @ commit `0561e70976`. Tolerances
are wide enough to be engine-robust and narrow enough to catch a real change.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.calib_lib import build, run_waves, rpi_of, ideal_split_gabor  # noqa: E402
from domains.onoff_world import set_params, freeze  # noqa: E402
from domains.complex_cells import present, cell_stats  # noqa: E402


def _theta(w, us):
    return np.array([float(w.s.node(u)["attrs"]["theta"]) for u in us])


def _blank(w, n=400):
    for _ in range(n):
        present(w, np.zeros((16, 16), np.float32))


# ------------------------------------------------------------------ #
#  1. THE REFRAME'S BEST EVIDENCE, AND IT IS REAL
# ------------------------------------------------------------------ #
def test_a_perfect_gabor_with_no_reference_is_useless():
    """CONTENT WITHOUT CALIBRATION IS NOTHING — the one thing the reframe got
    unambiguously right, and rung 6's 0.0006 -> 0.9115 on a new measure."""
    w, us, _ = build(seed=0, eta=5e-4)
    for u in us:
        ideal_split_gabor(w, u)
    set_params(w, homeo=0.0)          # NO reference: theta pinned at 0
    run_waves(w, 400)
    rpi, st = rpi_of(w, us)
    assert rpi.mean() < 1.05, f"expected ~1.001 (useless), got {rpi.mean():.3f}"
    assert st["osi"].mean() < 0.01, f"expected ~0.0007, got {st['osi'].mean():.4f}"


def test_the_same_gabor_with_a_reference_works():
    """The contrast that makes the above meaningful: same weights, reference on."""
    from scripts.calib_lib import adapt_theta
    w, us, _ = build(seed=0, eta=5e-4)
    for u in us:
        ideal_split_gabor(w, u)
    adapt_theta(w, steps=400)
    rpi, st = rpi_of(w, us)
    assert rpi.mean() > 5.0, f"expected ~6.94, got {rpi.mean():.3f}"
    assert st["osi"].mean() > 0.95, f"expected ~1.0, got {st['osi'].mean():.4f}"


# ------------------------------------------------------------------ #
#  2. THE DEFECT THAT STOPPED THE RUNG — asserted as a DEFECT
# ------------------------------------------------------------------ #
def test_RPI_is_unbounded_which_is_why_this_rung_stopped():
    """THE STOP. `base` -> 0 for some unit => RPI explodes. This asserts the
    degeneracy is REAL: if someone repairs the measure, this test must fail and
    be replaced by a new pre-registration (PROTOCOL §5), not deleted."""
    worst = 0.0
    for sd in range(14):
        w, us, _ = build(seed=sd, eta=5e-4)
        set_params(w, homeo=1.0, oo_eta=0.0, frozen=0.0)
        _blank(w)
        freeze(w)
        st = cell_stats(w, us, key="rate", period=4.0)
        rpi = st["tuning"].max(axis=1) / np.maximum(st["baseline"], 1e-9)
        worst = max(worst, float(rpi.max()))
    assert worst > 100.0, (
        f"RPI's unbounded regime did not reproduce (max {worst:.2f}). The "
        "measure-calibration STOP in VISION_CALIBRATION_PREREG.md §12.1 rests "
        "on it; if this no longer holds the STOP must be revisited.")


# ------------------------------------------------------------------ #
#  3. THE FINDING THAT SURVIVES — the reference is the ANATOMY's
# ------------------------------------------------------------------ #
def test_blank_input_places_the_reference_where_waves_do():
    """§12.3 — waves and NO INPUT AT ALL put theta in the same place, because
    the complementary split (x_OFF = 1 - x_ON) pins E[act] to the tonic drive
    Sum(w-) whatever the input. The operating point is set by the architecture,
    not by the waves. This is the sharpest thing the rung found and it points
    AGAINST the reframe's central claim."""
    w, us, _ = build(seed=0, eta=5e-4)
    set_params(w, homeo=1.0, oo_eta=0.0, frozen=0.0)
    run_waves(w, 400)
    th_waves = _theta(w, us)

    w, us, _ = build(seed=0, eta=5e-4)
    set_params(w, homeo=1.0, oo_eta=0.0, frozen=0.0)
    _blank(w)
    th_blank = _theta(w, us)

    rel = np.abs(th_waves - th_blank) / np.abs(th_waves)
    assert rel.max() < 0.05, (
        f"waves theta {np.round(th_waves,2)} vs blank theta "
        f"{np.round(th_blank,2)}: max rel diff {rel.max():.3f}")


def test_blank_is_not_a_zero_drive_control_which_broke_the_design():
    """§12.5 — the proviso that broke. Under the complementary split a blank
    field is MAXIMAL OFF drive, not an absence of input. The drive-IQR
    classifier scores it 0.0000 because it measures VARIANCE, not DRIVE."""
    w, us, _ = build(seed=0, eta=5e-4)
    set_params(w, homeo=0.0, oo_eta=0.0, frozen=1.0)
    present(w, np.zeros((16, 16), np.float32))
    act = np.array([float(w.s.node(u)["attrs"]["act"]) for u in us])
    assert act.min() > 10.0, (
        f"blank should be MAXIMAL OFF drive, got act={np.round(act,2)}")


# ------------------------------------------------------------------ #
#  4. PROTOCOL §2 — the theta channel converges
# ------------------------------------------------------------------ #
def test_the_theta_channel_has_a_genuine_fixed_point():
    """PROTOCOL §2 on the channel this rung's measure reads."""
    w, us, _ = build(seed=0, eta=5e-4)
    set_params(w, homeo=1.0, oo_eta=0.0, frozen=0.0)
    run_waves(w, 200)
    prev = _theta(w, us)
    run_waves(w, 400)
    th = _theta(w, us)
    drift = np.abs(th - prev).sum() / max(np.abs(th).sum(), 1e-9)
    assert drift < 0.01, f"theta did not settle: drift {drift:.4f}"
    assert th.mean() > 40.0, f"theta collapsed: {th.mean():.2f}"


# ------------------------------------------------------------------ #
#  5. DEFAULTS PRESERVE COMMITTED RESULTS (PROTOCOL §9)
# ------------------------------------------------------------------ #
def test_this_rung_ships_no_new_seed_and_changes_no_default():
    """Nothing here is a new mechanism: calib_lib is a mechanical composition
    over rung 6's world. The rung added NO seed, NO rule and NO default."""
    import json
    p = os.path.join(ROOT, "seeds", "vision_onoff.json")
    with open(p) as f:
        m = json.load(f)
    params = [n for n in m.get("nodes", []) if n.get("type") == "OnOffParams"]
    assert params, "OnOffParams not found"
    a = params[0]["attrs"]
    assert a["onoff"] == 0.0, "vision_onoff must remain INERT by default"
    assert a["homeo"] == 1.0 and a["frozen"] == 0.0, "rung 6 defaults moved"
