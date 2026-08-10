"""GATE for the `w0` initialisation ablation (`W0_ABLATION.md`).

Pins the facts the ablation established, so neither can silently rot:

  1. The committed default init IS a large DC prior (the review's charge, upheld)
     — and the default is UNCHANGED, so every committed result reproduces (§9).
  2. Rung 6 is ARCHITECTURALLY IMMUNE to it (the effective RF starts DC-free).
  3. The harness cannot have changed a number (pool == serial).

Run explicitly by file — NOT via `-k vision`, which is a substring match that
also collects "pro**vision**al" (PROTOCOL §12).
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

from scripts.w0_ablation_lib import (INITS, build, dc_power_fraction,  # noqa: E402
                                     frac_negative, rf_stats, pmap)

NO_DC_FLOOR = 1.0 / 49.0          # a 7x7 RF with no constant component


# --------------------------------------------------------------------------- #
#  1. THE DEFAULT IS UNCHANGED (PROTOCOL 9 — defaults preserve committed results)
# --------------------------------------------------------------------------- #
def test_the_default_init_is_the_committed_expression_byte_for_byte():
    """`init="multiplicative"` must reproduce `max(w0*(1+jitter*N), 1e-3)` on the
    identical RNG stream. If this drifts, every committed rung number is void."""
    from domains.wave_world import WaveWorld
    from substrate.boot_core import boot_core, load_seeds_into
    import domains.seed_registry  # noqa: F401

    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    w = WaveWorld(s, h=16, w=16, seed=3)
    us = w.add_units(2, rf=7)                       # DEFAULTS, as committed

    # Re-derive the same draws: add_units consumes 2 integers (the centre) then
    # one normal() per synapse, per unit, in RF-scan order.
    rng = np.random.default_rng(3)
    for u in us:
        rng.integers(0, 10)
        rng.integers(0, 10)
        got = w.receptive_field(u)
        exp = np.array([[max(1.0 * (1.0 + 0.05 * rng.normal()), 1e-3)
                         for _ in range(7)] for _ in range(7)], np.float32)
        # Only cells inside the retina were wired; the rest stay 0.
        m = got > 0
        assert np.allclose(got[m], exp[m], atol=1e-6)


def test_every_committed_rung_ran_through_the_dc_init():
    """The DC arm IS the default: `add_cortex()` with no `init=` must equal
    `add_cortex(**INITS["DC"])`."""
    from domains.cortex_sheet import add_cortex
    a, us_a = build(0, "DC")
    from domains.wave_world import WaveWorld
    from substrate.boot_core import boot_core, load_seeds_into
    import domains.seed_registry  # noqa: F401
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps"])
    b = WaveWorld(s, h=16, w=16, seed=0)
    us_b = add_cortex(b, 6, 6, rf=7)                # no init= : the default
    for ua, ub in zip(us_a, us_b):
        assert np.array_equal(a.receptive_field(ua), b.receptive_field(ub))


# --------------------------------------------------------------------------- #
#  2. THE CHARGE, UPHELD (the review's numbers)
# --------------------------------------------------------------------------- #
def test_the_committed_init_is_a_large_dc_prior_not_a_tie_break():
    """The comment said "NOT structure, just a tie-break". It was FALSE: the
    init puts ~99.8% of the RF's power in its constant component and makes every
    weight strictly positive — rung 5's root-cause mode, before any rule fires."""
    w, us = build(0, "DC")
    st = rf_stats(w, us)
    assert st["dc_frac"] > 0.99, st["dc_frac"]
    assert st["dc_ratio"] > 100.0, st["dc_ratio"]      # the review said ~494:1
    assert st["frac_neg"] == 0.0


def test_the_zero_mean_init_is_actually_dc_free_and_signed():
    """The ablation arm must be what it claims — otherwise it tests nothing."""
    for arm in ("ZERO", "ZEROM"):
        w, us = build(0, arm)
        st = rf_stats(w, us)
        assert st["dc_frac"] < 3.0 * NO_DC_FLOOR, (arm, st["dc_frac"])
        assert 0.4 < st["frac_neg"] < 0.6, (arm, st["frac_neg"])


def test_the_norm_matched_arm_matches_the_dc_arms_norm():
    """ZEROM exists to rule out "it only failed because it started 20x too
    small". If its norm does not match DC's, it cannot do that job."""
    dc = rf_stats(*build(0, "DC"))
    zm = rf_stats(*build(0, "ZEROM"))
    zs = rf_stats(*build(0, "ZERO"))
    assert abs(zm["norm"] - dc["norm"]) / dc["norm"] < 0.05
    assert zs["norm"] < 0.1 * dc["norm"]              # and ZERO does NOT


def test_the_anisotropy_measure_is_blind_to_the_dc_prior_by_construction():
    """Rung 1/2/4's statistic is a spectral moment that ignores the DC bin, so
    all three inits score IDENTICALLY at step 0. This is why the prior cannot
    move those rungs — a fact about the measure, not evidence about the prior."""
    vals = [rf_stats(*build(0, a))["anis"] for a in INITS]
    assert max(vals) - min(vals) < 1e-6, vals


# --------------------------------------------------------------------------- #
#  3. RUNG 6 IS ARCHITECTURALLY IMMUNE
# --------------------------------------------------------------------------- #
def test_rung6_effective_rf_starts_at_the_no_dc_floor():
    """Rung 6's cells read `w+ - w-`, and ON/OFF start at the same w0 with
    INDEPENDENT jitter, so the read quantity has NO DC prior — there is nothing
    to ablate, and rung 6's convergence failure cannot be an init artifact."""
    from scripts.rung6_lib import build as build6
    from domains.onoff_world import signed_rf
    w, us, bip = build6(seed=0, n_units=4)
    er = np.stack([signed_rf(w, u) for u in us])
    # PER UNIT — averaging RFs across units first would average away the very
    # variance the statistic is a ratio against, and inflate the DC fraction.
    # The cell reads its OWN effective RF; that is the quantity with the prior
    # or without it.
    per_unit = np.array([dc_power_fraction(r) for r in er])
    assert per_unit.mean() < 3.0 * NO_DC_FLOOR, per_unit.mean()
    assert 0.4 < frac_negative(er) < 0.6


def test_dale_clipping_is_a_rule_so_a_signed_init_is_not_expressible_in_rung6():
    """`oo_learn_sub` clips to [0, wmax] — a negative weight is not a different
    arm, it is a state the first rule firing deletes."""
    import json
    d = json.load(open(os.path.join(ROOT, "seeds", "vision_onoff.json")))
    r = next(r for r in d["rules"] if r["name"] == "oo_learn_sub")
    body = json.dumps(r["effects"])
    assert '"Max"' in body and '"Min"' in body


# --------------------------------------------------------------------------- #
#  4. THE HARNESS CANNOT HAVE CHANGED A NUMBER
# --------------------------------------------------------------------------- #
def _anis(seed_and_arm):
    from scripts.w0_ablation_lib import build as _b, run_waves, rf_stats as _rs
    w, us = _b(seed_and_arm[0], seed_and_arm[1])
    run_waves(w, 20)
    return _rs(w, us)["anis"]


def test_pmap_is_identical_to_serial():
    """The pool is a scheduling detail: same seeds, same values, same order."""
    args = [(0, "DC"), (1, "DC"), (2, "ZERO")]
    assert pmap(_anis, args, procs=3) == [_anis(a) for a in args]
