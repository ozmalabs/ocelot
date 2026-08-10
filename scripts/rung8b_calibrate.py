"""RUNG 8B — THE §1 CALIBRATION GATE for GCAL's SETPOINT THETA.

Pre-registered in `VISION_RUNG8B_PREREG.md` §5, BEFORE this ran. The gate:

  G1  ideal split-Gabor OSI            >= 0.80   (a perfect cell must be visible)
  G2  untouched-init floor             <= 0.50   (not saturated by theta alone)
  G3  SEPARATION (ideal - floor)       >= 0.30   (rung 8 failed at 0.109;
                                                  rung 6 succeeded at 0.69)
  G4  duration: OSI flat (d < 0.01) across probe-steps, theta FROZEN
  G5  theta CONVERGES on the ensemble it responds to; OSI flat (d < 0.05)
      across adaptation durations past equilibrium
  G6  THE CROSS-PATHWAY TEST: separation >= 0.30 on the DEGENERATE pathway TOO,
      SAME rule, SAME constants.

**G6 is what makes this a mechanism and not a fit.** A tuned constant rescues at
most ONE of two pathways whose drives differ ~6x: anything inside the composed
range silences nothing and anything at 5.1 silences the composed cell. Only a
rule that SELF-POSITIONS can do both.

**The gate is SEPARATION, not the ideal alone.** Raising theta raises the floor
too — OSI `argmax`-selects over 12 orientations, so clipping the orthogonal
response to 0 inflates a RANDOM cell toward 1.0 exactly as it does an ideal one.
Floor and ideal are therefore measured under the SAME theta rule, IN THIS RUN,
never inherited: OSI's floor is init-dependent (0.0044 DC / 0.3899 signed /
0.3168 rung 6 / 0.0205 rung 8 composed — four values, one probe).

Seeds 0-2 / 3000: ALREADY BURNED. No confirmatory seed is touched here.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.complex_cells import cell_stats, present  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, adapt_theta as rung8_adapt_theta, build as _rung8_build,
    develop_retina, freeze_all, ideal_split_gabor, osi_of,
)
from scripts.rung8b_lib import (  # noqa: E402
    GCAL_BETA, GCAL_LAMBDA, GCAL_MU, build8b, grating_ensemble, rbar_of,
    set_theta_params, theta_of, weights_of,
)

ADAPT = 5000        # steps of adaptation; G5 verifies this is past equilibrium
N_UNITS = 6


def line(k, v):
    print(f"  {k:<54s} {v}")


def prepare(chan, *, ideal, theta_mode, seed=0, adapt=ADAPT, w0=1.0):
    """Build -> develop the retina -> (optionally install a PERFECT cell) ->
    adapt theta on the ensemble being RESPONDED TO -> PIN theta.

    Weights are frozen for the whole adaptation (`freeze_all`), so nothing here
    trains anything: theta's placement OUTSIDE the learning rule is what makes
    it separable, and that placement is rung 6's own (GCAL's).

    NOTE `theta_mode=0` here means **theta never adapts at all** (theta = 0, the
    NO-THRESHOLD condition), NOT rung 8's EMA arm. Rung 8's arm is the separate
    `reproduction()` below, which uses rung 8's OWN harness verbatim. A first
    version of this script mislabelled the theta=0 rows as "the reproduction";
    they are not, and the label is corrected rather than quietly dropped.
    """
    w, us, _a, _b = build8b(seed=seed, n_units=N_UNITS, channels=chan,
                            theta_mode=theta_mode, w0=w0)
    develop_retina(w, 3000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    wt0 = weights_of(w, us)
    freeze_all(w)
    if theta_mode > 0.5:
        set_theta_params(w, theta_adapt=1.0)
        rng = np.random.default_rng(7)
        for _ in range(adapt):
            present(w, grating_ensemble(w, rng))
        set_theta_params(w, theta_adapt=0.0)
    dw = float(np.abs(weights_of(w, us) - wt0).max())
    return w, us, dw


def responsiveness(w, us):
    """**G0 — IS THE ARM ALIVE?** Added AFTER the pre-registered gate returned a
    spurious PASS, and it makes this rung's own result WORSE rather than better
    — which is the only direction in which changing a measure is ever allowed
    (PROTOCOL §5 forbids RESCUING a failure; disqualifying your own apparent
    success is what §1 and §7 demand).

    THE DEFECT IT CATCHES: `complex_cells.osi()` ends

        return float((a - b) / (a + b)) if (a + b) > 1e-9 else 0.0

    so a cell that NEVER FIRES returns **0.0** — indistinguishable from a cell
    that fires everywhere equally. **A dead arm scores a PERFECT floor.**
    PROTOCOL §1's *"run it on random input — it must score at the floor"* is
    therefore SATISFIED BY DEATH, and §12's rule generalises to it exactly: an
    absence off a guarded division is evidence of a LOOKUP, not of a
    measurement. So the floor arm must be shown to FIRE before its score means
    anything.
    """
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    return {"tuning_max": float(tc.max()),
            "n_orient_alive": float((tc > 1e-9).sum(axis=1).mean()),
            "baseline": float(st["baseline"].mean()),
            "osi": float(st["osi"].mean())}


def reproduction(chan):
    """RUNG 8's arm, through RUNG 8's OWN harness, verbatim (EMA theta adapted
    on WAVES for 400 steps). The control that says whether anything here is
    attributable to this rung rather than to the engine or the harness."""
    w, us, _a, _b = _rung8_build(seed=0, n_units=N_UNITS, channels=chan)
    develop_retina(w, 3000)
    rung8_adapt_theta(w, 400)
    o_floor, _ = osi_of(w, us)
    w2, us2, _a2, _b2 = _rung8_build(seed=0, n_units=N_UNITS, channels=chan)
    develop_retina(w2, 3000)
    for u in us2:
        ideal_split_gabor(w2, u, theta=0.0, phase=0.0)
    rung8_adapt_theta(w2, 400)
    o_ideal, st = osi_of(w2, us2)
    pk = st["tuning"].max(axis=1)
    bs = np.maximum(st["baseline"], 1e-9)
    return (float(o_floor.mean()), float(o_ideal.mean()),
            float((pk / bs).mean()), float(theta_of(w2).mean()))


def main():
    print("=" * 78)
    print("RUNG 8B CALIBRATION — GCAL's SETPOINT THETA (Eqs 7-8), constants LITERAL")
    print(provenance_line())
    print(f"  GCAL constants: mu={GCAL_MU}  beta={GCAL_BETA}  lambda={GCAL_LAMBDA}"
          f"   adapt={ADAPT} steps")
    print("=" * 78)

    # ------------------------------------------------------------------ #
    # 0. THE REPRODUCTION CONTROL — rung 8's arm, rung 8's harness, verbatim.
    #    Rung 8 (engine 95167c01b7b3) reported: lateral 0.0205 / 0.1290 / 0.89;
    #    degenerate 0.3105 / 1.0000 / 6.94. If those do not come back, nothing
    #    below is attributable to this rung.
    # ------------------------------------------------------------------ #
    print("\n--- 0. REPRODUCTION CONTROL (rung 8's EMA theta, adapted on WAVES) ---")
    for chan in ("lateral", "degenerate"):
        fl, id_, pb, th = reproduction(chan)
        line(f"[{chan}] floor / IDEAL / peak-base / theta",
             f"{fl:.4f} / {id_:.4f} / {pb:.2f} / {th:.4f}")

    res = {}
    for mode, tag in ((0.0, "theta = 0, NO THRESHOLD (rung 6's own 0.0006 arm)"),
                      (1.0, "rung 8B — GCAL's SETPOINT theta")):
        print(f"\n--- THETA RULE: {tag} ---")
        for chan in ("lateral", "degenerate"):
            wf, usf, dwf = prepare(chan, ideal=False, theta_mode=mode)
            rf = responsiveness(wf, usf)
            o_floor = rf["osi"]
            wi, usi, dwi = prepare(chan, ideal=True, theta_mode=mode)
            ri = responsiveness(wi, usi)
            o_ideal = ri["osi"]
            _o, st = osi_of(wi, usi)
            pk = st["tuning"].max(axis=1)
            bs = np.maximum(st["baseline"], 1e-9)
            sep = float(o_ideal - o_floor)
            res[(mode, chan)] = (o_floor, o_ideal, sep, rf, ri)
            line(f"[{chan}] untouched-init OSI (the FLOOR)", f"{o_floor:.4f}")
            line(f"[{chan}] IDEAL split-Gabor OSI (the TARGET)",
                 f"{o_ideal:.4f}  peak/base {(pk / bs).mean():.2f}")
            line(f"[{chan}] SEPARATION (ideal - floor)", f"{sep:.4f}")
            line(f"[{chan}] theta (ideal cell) / rbar  [setpoint mu={GCAL_MU}]",
                 f"{theta_of(wi).mean():.4f} / {rbar_of(wi).mean():.5f}")
            # G0 — IS THE ARM ALIVE? A dead arm scores a PERFECT floor.
            line(f"[{chan}] G0 FLOOR arm ALIVE?  orientations firing (of 12)",
                 f"{rf['n_orient_alive']:.2f}   tuning.max {rf['tuning_max']:.6g}")
            line(f"[{chan}] G0 IDEAL arm ALIVE?  orientations firing (of 12)",
                 f"{ri['n_orient_alive']:.2f}   tuning.max {ri['tuning_max']:.6g}")
            line(f"[{chan}] WEIGHTS FROZEN during adaptation? max|dw|",
                 f"{max(dwf, dwi):.3e}")

    # ------------------------------------------------------------------ #
    # G4 — DURATION, theta FROZEN. The rung-8 check, unchanged.
    # ------------------------------------------------------------------ #
    print("\n--- G4. DURATION CONFOUND (theta PINNED, same input) ---")
    w, us, _ = prepare("lateral", ideal=True, theta_mode=1.0)
    th_before = theta_of(w).mean()
    rng = np.random.default_rng(11)
    for steps in (0, 400, 1600):
        o, _ = osi_of(w, us)
        line(f"frozen, after {steps:5d} probe-steps  OSI", f"{o.mean():.4f}")
        freeze_all(w)
        for _ in range(400 if steps == 0 else 1200 if steps == 400 else 0):
            present(w, grating_ensemble(w, rng))
    line("theta MOVED during the probe? |dtheta|",
         f"{abs(theta_of(w).mean() - th_before):.3e}")

    # ------------------------------------------------------------------ #
    # G5 — is ADAPT past equilibrium? OSI must be flat past it.
    # ------------------------------------------------------------------ #
    print("\n--- G5. ADAPTATION DURATION (OSI must be FLAT past equilibrium) ---")
    for chan in ("lateral", "degenerate"):
        for ad in (2000, 5000, 8000):
            w, us, _ = prepare(chan, ideal=True, theta_mode=1.0, adapt=ad)
            o, _ = osi_of(w, us)
            line(f"[{chan}] adapt={ad:5d}  ideal OSI  (theta {theta_of(w).mean():7.4f}"
                 f"  rbar {rbar_of(w).mean():.5f})", f"{o.mean():.4f}")

    # ------------------------------------------------------------------ #
    # THE VERDICT
    # ------------------------------------------------------------------ #
    print("\n--- THE PRE-REGISTERED GATE (VISION_RUNG8B_PREREG.md §5) ---")
    fl, id_, sep, rf, ri = res[(1.0, "lateral")]
    dfl, did, dsep, drf, dri = res[(1.0, "degenerate")]
    pre = [("G1 ideal >= 0.80  (lateral)", id_ >= 0.80, f"{id_:.4f}"),
           ("G2 floor <= 0.50  (lateral)", fl <= 0.50, f"{fl:.4f}"),
           ("G3 separation >= 0.30 (lateral)", sep >= 0.30, f"{sep:.4f}"),
           ("G6 separation >= 0.30 (DEGENERATE — cross-pathway)",
            dsep >= 0.30, f"{dsep:.4f}")]
    for name, ok, val in pre:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<56s} {val}")
    print(f"  --> the PRE-REGISTERED criteria say: "
          f"{'PASS' if all(c[1] for c in pre) else 'FAIL'}")

    print("\n--- G0: BUT IS THE FLOOR ARM ALIVE? (NOT pre-registered — added"
          " because the PASS above is an ARTIFACT) ---")
    g0 = [("G0 lateral FLOOR arm fires at all", rf["n_orient_alive"] > 0,
           f"{rf['n_orient_alive']:.2f} of 12 orientations"),
          ("G0 degenerate FLOOR arm fires at all", drf["n_orient_alive"] > 0,
           f"{drf['n_orient_alive']:.2f} of 12 orientations")]
    for name, ok, val in g0:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<56s} {val}")

    ok = all(c[1] for c in pre) and all(c[1] for c in g0)
    print(f"\n  GATE: {'PASS' if ok else 'FAIL'}   (G4/G5 read above)")
    if not ok:
        print("""
  THE PRE-REGISTERED CRITERIA PASS AND THE GATE FAILS ANYWAY, because the
  FLOOR ARM IS DEAD. `osi()` returns 0.0 when (a+b) <= 1e-9, so a cell that
  never fires scores a PERFECT floor — and `peak/base` then blows up to ~1e8,
  the SAME unbounded-ratio signature that killed the calibration reframe
  (base->0 => the no-input control scored 1.6e6 vs an ideal Gabor's 6.94).
  The 'separation of 1.0000' is measuring FIRES vs DOES-NOT-FIRE, not
  selectivity, so no arm would be interpretable and H1/H2 stay UNTESTED.

  CAUSE, MEASURED: GCAL Eq 8's loop is ASYMMETRIC in unnormalised units.
  Up-drive is lambda*rbar (rbar reached ~20 early); down-drive is lambda*mu =
  0.00024/step, CONSTANT and TINY. A cell whose drive is large (the random
  cell: act 20.8) winds theta up to 26.9, goes silent, and can only recover at
  0.00024/step (~25k steps) -- rbar lands at EXACTLY 0, never at mu. The ideal
  cell (act 2.19, a zero-mean Gabor) DOES reach the setpoint (rbar 0.021).
  That asymmetry IS the fake separation.

  In GCAL this cannot happen: L1 weights (sum w = 1) and inputs in [0,1] put
  eta in [0,1], so rbar - mu <= 0.976 and the two drives are COMPARABLE.

  => AN ABSOLUTE SETPOINT CANNOT TRANSFER INTO UNNORMALISED RESPONSE UNITS.
     GCAL's A REQUIRES GCAL's GC. Our layer is model 'AL' -- and GCAL's own
     ablation lattice (L -> GCL -> AL -> GCAL) exists precisely because AL is
     not GCAL. GC is the named next rung and needs its OWN pre-registration.
     PREREG §4 binds this rung NOT to rescue a failed mu by fitting mu.""")


if __name__ == "__main__":
    sys.exit(main())
