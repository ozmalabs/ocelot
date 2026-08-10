"""rung7_poscontrol — PROTOCOL §1's POSITIVE CONTROL, asked separately from the
hypothesis.

*Rung 3's eta was a NULL INSTRUMENT and only its positive control revealed it.*

Two questions, both asked of a PERFECT case, both answerable independently of
whether waves do anything:

  A. **CAN the measure see a broken degeneracy AT ALL?** Given a hand-installed
     IDEAL centre-surround (`g` set to a textbook DoG-like balance, NOT learned
     — a calibration reference, never a claim), does `SD` leave its analytic
     floor of 0? If a perfect DoG cannot move this statistic, the statistic is a
     null instrument and every arm below it is meaningless. **This also supplies
     the TARGET that the SESOI is 10% of.**

  B. **CAN the rule LEARN a surround at all?** Given input where the surround is
     a PERFECT predictor of the centre (a fully-correlated field), does
     `lat_learn_gain` drive `g` to the analytic optimum? This is the sharpest
     form: it is exactly where an anti-Hebbian decorrelation rule MUST succeed
     if it is capable. The analytic target is derivable, so the rule is scored
     against a NUMBER rather than against "more than nothing".

Both are CAPABILITY checks. Neither is evidence about waves, and neither is a
fixed point unless the convergence gate says so.
"""
from __future__ import annotations

import numpy as np

from domains.engine_provenance import provenance_line
from domains.lateral_world import freeze_lateral, install_gains, thaw_lateral
from scripts.rung7_lib import (
    build, corr_by_distance, cs_index, effective_rf, gains, record_channels,
    run_waves, shape_departure, space_constant, complementary_channels,
    raw_burst_movie, surround_suppression,
)

np.set_printoptions(precision=4, suppress=True)


def _sd_of(w, anat, *, steps=400, seed=7):
    freeze_lateral(w)
    on, off = record_channels(w, anat, steps)
    thaw_lateral(w)
    ds, Cnn = corr_by_distance(on, on)
    _, Cnf = corr_by_distance(on, off)
    return shape_departure(Cnn, Cnf), space_constant(ds, Cnn), \
        space_constant(ds, Cnf), on, off


def part_a():
    """THE MEASURE'S TARGET: a hand-installed ideal centre-surround."""
    print("=" * 76)
    print("A. POSITIVE CONTROL FOR THE MEASURE — can SD see a broken degeneracy?")
    print("   (gains HAND-INSTALLED: a calibration reference, NOT a claim)")
    print("=" * 76)
    print(f"{'reference':<44}{'SD':>9}{'sig_nn':>9}{'sig_nf':>9}{'OFF':>8}")
    rows = {}
    # The rung-6 reference recomputed here on the SAME frames: the analytic floor.
    w0, anat0 = build(seed=0, lateral=1.0)
    burst = raw_burst_movie(w0, 400)
    on_c, off_c = complementary_channels(burst)
    ds, Cnn = corr_by_distance(on_c, on_c)
    _, Cnf = corr_by_distance(on_c, off_c)
    sd0 = shape_departure(Cnn, Cnf)
    print(f"{'RUNG-6 complementary split (ANALYTIC FLOOR)':<44}{sd0:>9.4f}"
          f"{space_constant(ds, Cnn):>9.3f}{space_constant(ds, Cnf):>9.3f}"
          f"{off_c.mean():>8.3f}")
    rows["floor"] = sd0
    # Hand-installed surrounds of increasing strength. g1=g2=g is a balanced
    # (DC-cancelling) centre-surround when g1*1 + g2*1 == 1, i.e. g = 0.5 each.
    for label, g1, g2 in [("pure centre (g=0) — no surround", 0.0, 0.0),
                          ("weak surround   (g1=g2=0.25)", 0.25, 0.25),
                          ("BALANCED DoG    (g1=g2=0.5, DC-cancelling)", 0.5, 0.5),
                          ("strong surround (g1=g2=0.75)", 0.75, 0.75),
                          ("near-only       (g1=1.0, g2=0)", 1.0, 0.0)]:
        w, anat = build(seed=0, lateral=1.0, learn_gain=0.0)
        install_gains(w, anat["hcells"], g1, g2)
        sd, snn, snf, on, off = _sd_of(w, anat)
        print(f"{label:<44}{sd:>9.4f}{snn:>9.3f}{snf:>9.3f}{off.mean():>8.3f}")
        rows[label] = sd
    return rows


def part_b():
    """THE RULE'S CAPABILITY: can anti-Hebbian decorrelation find the optimum?

    A PERFECTLY PREDICTABLE field: every cell of the retina bursts together, so
    the surround predicts the centre exactly (c = h1 = h2 = 1). The analytic
    fixed point of dg_k = eta*resid*h_k on this input is the set where
    resid = 0, i.e. g1 + g2 = 1 (the DC-cancelling balance) — the rule should
    drive the TOTAL gain to 1.0 and then stop, because the residual it feeds on
    has been explained away. That is redundancy reduction, scored against a
    derived number.
    """
    print()
    print("=" * 76)
    print("B. POSITIVE CONTROL FOR THE RULE — can it LEARN a surround at all?")
    print("   Perfectly-predictable field (whole retina co-bursts).")
    print("   ANALYTIC fixed point: resid=0 <=> g1+g2 = 1.0")
    print("=" * 76)
    for eta in (2e-3, 5e-4):
        w, anat = build(seed=0, lateral=1.0, eta=eta)
        for t in range(1500):
            st = float(w.s.node(w.retina)["attrs"]["step"]) + 1.0
            w.s.set_attr(w.retina, "step", st)
            for n in w.cells.values():
                w.s.set_attr(n, "bursting", 1.0)
                w.s.set_attr(n, "last_burst", st)
            w.s.tick(200_000)
        g = gains(w, anat["hcells"])
        tot = g.sum(axis=1)
        print(f"  eta={eta:<8g} g1={g[:,0].mean():.4f}  g2={g[:,1].mean():.4f}  "
              f"TOTAL g1+g2={tot.mean():.4f} (target 1.0)  "
              f"max|resid| after={abs(1.0-tot.mean()):.4f}")


def part_c():
    """THE RF: does a learned surround READ OUT as centre-surround?"""
    print()
    print("=" * 76)
    print("C. THE EFFECTIVE RF — CS index calibration (CS = g1+g2 by construction)")
    print("=" * 76)
    for label, g1, g2 in [("pure centre (g=0) — THE FLOOR", 0.0, 0.0),
                          ("BALANCED DoG (g1=g2=0.5)", 0.5, 0.5),
                          ("strong (g1=g2=0.75)", 0.75, 0.75)]:
        w, anat = build(seed=0, lateral=1.0, learn_gain=0.0)
        install_gains(w, anat["hcells"], g1, g2)
        rf = effective_rf(w, anat)
        cs = cs_index(rf)
        sup = surround_suppression(w, anat)
        print(f"  {label:<34} CS={cs:>7.4f} (expect {g1+g2:.2f})  "
              f"surround_suppression={sup:.4f}")
        if g1 == 0.5:
            print("    effective RF (residual field):")
            for row in rf:
                print("      ", " ".join(f"{v:+.3f}" for v in row))


if __name__ == "__main__":
    print(provenance_line())
    part_a()
    part_b()
    part_c()
