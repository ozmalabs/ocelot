"""RUNG 5 — COMPLEX CELLS: gates.

Gates the MEASURE as hard as the mechanism (PROTOCOL 1: a gate whose measure
passes noise is not a gate), and PINS the honest known gaps (PROTOCOL 8) so a
later change cannot quietly turn a NOT-BUILT into a claim.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.cortex_sheet import add_cortex, orientation_selectivity
from domains.complex_cells import (add_complex_layer, pool_weights, freeze,
                                   grating, binarize, present, cell_stats,
                                   f1f0, osi, gabor, install_weights, THETAS)

H = W = 16
RF = 7
PERIOD = 4.0


def _world(seed=0, steps=0, eta=5e-4):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps", "vision_complex"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", eta)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, 6, 6, rf=RF)
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    return w, us


# --------------------------------------------------------------------------- #
#  THE MEASURE (PROTOCOL 1)
# --------------------------------------------------------------------------- #
def test_f1f0_separates_ideal_simple_from_ideal_complex():
    """The instrument's whole job: simple > 1, complex < 1 (Skottun 1991)."""
    K = 16
    ph = 2 * np.pi * np.arange(K) / K
    simple = np.maximum(np.cos(ph), 0.0)          # half-wave rectified
    complex_ = np.ones(K)                          # responds throughout
    assert f1f0(simple) > 1.0
    assert f1f0(complex_) < 1.0


def test_f1f0_is_nan_on_a_silent_cell():
    assert np.isnan(f1f0(np.zeros(16)))


def test_osi_is_axial_and_bounded():
    tc = np.zeros(len(THETAS))
    tc[0] = 1.0
    assert osi(tc) == pytest.approx(1.0)
    assert osi(np.ones(len(THETAS))) == pytest.approx(0.0)


def test_ideal_gabor_scores_as_a_SIMPLE_cell_through_the_graph_probe():
    """THE INSTRUMENT'S POSITIVE CONTROL. A textbook Gabor installed into a real
    Unit and probed through the real pathway must be orientation-selective AND
    phase-modulated. This is the test that caught the missing rectification
    (without it the instrument reported OSI=0.0000 for this exact cell)."""
    w, us = _world()
    freeze(w)
    install_weights(w, us[14], gabor(RF, 90.0, 0.0, PERIOD))
    st = cell_stats(w, [us[14]], key="act", period=PERIOD)
    assert st["osi"][0] > 0.5, "an ideal Gabor must be orientation-selective"
    assert st["f1f0"][0] > 1.0, "an ideal Gabor must score SIMPLE"


def test_positive_weights_alone_destroy_response_selectivity():
    """THE DIAGNOSIS, pinned. The same Gabor shifted to be strictly positive has
    IDENTICAL weight anisotropy (the statistic mean-subtracts) and ZERO response
    selectivity. This is why rung 5's precondition fails."""
    w, us = _world()
    freeze(w)
    g = gabor(RF, 90.0, 0.0, PERIOD)
    install_weights(w, us[14], g)
    install_weights(w, us[21], g - g.min() + 0.05)
    a_gab = orientation_selectivity(w.receptive_field(us[14]))
    a_dc = orientation_selectivity(w.receptive_field(us[21]))
    assert a_gab == pytest.approx(a_dc, abs=1e-6), "anisotropy must be identical"
    st = cell_stats(w, [us[14], us[21]], key="act", period=PERIOD)
    assert st["osi"][0] > 0.5      # the Gabor
    assert st["osi"][1] < 0.05     # the same Gabor, made positive


# --------------------------------------------------------------------------- #
#  THE FREEZE — the instrument bug that invalidated the first measurements
# --------------------------------------------------------------------------- #
def test_freeze_actually_freezes_both_layers():
    """`oja=0` is NOT "learning off" — bh_potentiate/bh_depress/bh_scale are each
    gated on `oja == 0.0`, so it switches the OTHER learning rule ON and the probe
    rewrites what it measures (measured: max |dw| = 47.9 across one probe).
    `freeze()` keeps oja SELECTED and zeroes the rates."""
    w, us = _world(steps=200)
    cus = add_complex_layer(w, [us[:4]])
    w.s.set_attr(w.s.nodes("ComplexParams")[0], "complex", 1.0)
    freeze(w)
    rf0 = np.stack([w.receptive_field(u) for u in us])
    pw0 = pool_weights(w, cus[0], us[:4])
    cell_stats(w, [cus[0]], key="cact", period=PERIOD)
    rf1 = np.stack([w.receptive_field(u) for u in us])
    pw1 = pool_weights(w, cus[0], us[:4])
    assert np.abs(rf1 - rf0).max() == pytest.approx(0.0, abs=1e-9)
    assert np.abs(pw1 - pw0).max() == pytest.approx(0.0, abs=1e-9)


def test_oja_zero_is_not_a_freeze_which_is_why_freeze_exists():
    """Pins the trap itself, so nobody re-introduces `oja=0` as a freeze."""
    w, us = _world(steps=200)
    w.s.set_attr(w.s.nodes("WaveParams")[0], "oja", 0.0)   # the WRONG "freeze"
    rf0 = np.stack([w.receptive_field(u) for u in us])
    for k in range(8):
        present(w, binarize(grating((H, W), 0.0, k * 0.7, PERIOD)))
    rf1 = np.stack([w.receptive_field(u) for u in us])
    assert np.abs(rf1 - rf0).max() > 1e-6, \
        "oja=0 enables bh_* — if this ever passes as a freeze, the gate is wrong"


# --------------------------------------------------------------------------- #
#  DEFAULTS OFF (PROTOCOL 9)
# --------------------------------------------------------------------------- #
def test_complex_layer_is_off_by_default():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_complex"])
    cp = s.nodes("ComplexParams")[0]
    assert float(s.node(cp)["attrs"]["complex"]) == 0.0
    assert float(s.node(cp)["attrs"]["trace_delta"]) == 1.0, \
        "trace_delta=1 (no memory) is the ABLATED default"


def test_defaults_off_leaves_the_simple_layer_byte_identical():
    """Loading vision_complex must not perturb any committed result."""
    def rf_of(seeds):
        s, ag = boot_core()
        load_seeds_into(s, ag, seeds)
        wp = s.nodes("WaveParams")[0]
        s.set_attr(wp, "propagate", 1.0)
        s.set_attr(wp, "oja", 1.0)
        s.set_attr(wp, "oja_eta", 5e-4)
        w = WaveWorld(s, h=H, w=W, seed=3)
        us = add_cortex(w, 6, 6, rf=RF)
        for i in range(200):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
        return np.stack([w.receptive_field(u) for u in us])

    base = rf_of(["vision_waves", "vision_maps"])
    with_cx = rf_of(["vision_waves", "vision_maps", "vision_complex"])
    assert np.abs(with_cx - base).max() == pytest.approx(0.0, abs=0.0)


# --------------------------------------------------------------------------- #
#  KNOWN GAPS, PINNED (PROTOCOL 8)
# --------------------------------------------------------------------------- #
def test_known_gaps_are_pinned_the_model_has_no_simple_cells():
    """RUNG 5 IS NOT BUILT and this is why: the model's own Units have no
    orientation-selective RESPONSE, so there is nothing to pool. If this ever
    fails, the precondition has changed and rung 5 is newly testable — which
    requires its own pre-registration, not a quiet edit."""
    w, us = _world(seed=0, steps=1600)
    freeze(w)
    st = cell_stats(w, us, key="act", period=PERIOD)
    assert st["osi"].mean() < 0.05, (
        "the model's Units are NOT orientation-selective in their response "
        f"(measured {st['osi'].mean():.4f}); an ideal Gabor scores >0.5 through "
        "the identical probe")
    wts = np.concatenate([w.receptive_field(u).flatten() for u in us])
    assert (wts < 0).mean() == 0.0, \
        "Oja on nonneg input yields strictly-positive weights — the root cause"
