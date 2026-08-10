"""RUNG 8C — THE DECISIVE §1 CALIBRATION: is rung 8's blindness ENTIRELY the
ENSEMBLE MISMATCH, with NO new mechanism required?

**§1 CALIBRATION on already-burned seeds (0 / 3000). NO confirmatory seed is
touched. No hypothesis is tested here.** If this gate passes, H1/H2 need their
OWN pre-registration before a single confirmatory seed is spent.

THE CHAIN THAT LEADS HERE, ALL OF IT MEASURED IN THIS RUNG
-----------------------------------------------------------
1. `rung8c_step1_probe_alive.py`: rung 8's gate REPRODUCES exactly on a third
   binary -- IDEAL 0.1290 composed / 1.0000 degenerate. And `mu_endo` is in
   **0** nodes of this pathway (0 EyeCell): it was never here to be "in place".

2. `rung8c_theta_operating_point.py`: with theta PINNED and swept, the composed
   pathway HAS a wide operating point (theta 1.9-3.0, ideal -> 1.0000). So the
   probe is **not structurally blind**. The positive control validates the sweep:
   the degenerate pathway's operating point is theta 5.0-7.0, peaking at
   **5.43** -- *exactly where rung 6's own rule lands theta (5.430)*, which
   independently re-derives WHY rung 6 scored 1.0000.

3. `rung8c_drive_audit.py`: **that sweep's separation is an ARTIFACT.** The floor
   arm's cells carry **9.5x** the ideal arm's drive (20.75 vs 2.18 composed;
   48.96 vs 5.16 degenerate; both stimuli). A GLOBAL theta placed for the ideal
   cell leaves the floor cell unsliced -- so it separates cells BY DRIVE, not by
   selectivity. No mechanism places a global theta: every homeostat is PER CELL.

4. **Therefore the only meaningful question is what a PER-CELL rule does** -- and
   the audit says a per-cell theta tracks each cell's own drive, slicing the
   floor cell's own noise too. That is precisely what rung 6's floor of
   0.3105/0.3168 IS: not a nuisance, but the SIGNATURE of a per-cell homeostat
   slicing a random cell's noise. Rung 6's instrument WORKS at separation
   1.0000 - 0.3105 = **0.69**.

THE HYPOTHESIS THIS GATE MEASURES -- AND IT ADDS NOTHING
---------------------------------------------------------
Rung 8's measured cause, restated exactly:

    degenerate   waves 5.317 vs gratings 5.120  ratio 0.96  -> theta 5.430
                 transfers -> ideal 1.0000
    lateral      waves 0.861 vs gratings 1.902  ratio 2.21  -> theta 0.774
                 does NOT transfer -> ideal 0.1290

**Rung 6's theta rule is not broken on the composed pathway. It is being
CALIBRATED ON THE WRONG ENSEMBLE.** `rung8_lib.adapt_theta` settles theta with
`run_waves` and then probes with GRATINGS. On rung 6's channels that was free
(ratio 0.96 -- the two ensembles drive the cell equally). On a PREDICTIVE CODER
it is not: waves are cheap BECAUSE the surround predicts them (that IS Atick &
Redlich, working), and the OOD grating is 2.21x more expensive.

So: run rung 6's OWN per-cell EMA theta -- **same rule, same seed, same
constants, no GC, no setpoint, nothing added** -- and settle it on the ensemble
being RESPONDED TO instead of the formative one.

Rung 8 §I.1 named EXACTLY this and required it be declared in advance:

    "The composed system needs a threshold whose reference is the ensemble being
     *responded to*, not only the one it developed on -- or a probe delivered at
     the formative input's drive magnitude. **State which, and why, in advance.**"

**I state it: the FORMER.** And the reason is not that it scores better (that
would be §5's metric surgery, choosing a rule after seeing which rescues the
number) -- it is that the LATTER is not a thing an animal has. A cortical cell's
threshold tracks the stimulus ensemble it is currently exposed to; contrast /
threshold adaptation is real physiology and is on the SAME activation function
rung 6 already placed theta on, *"where it cannot flip dw's sign"*. Delivering a
probe at the formative drive magnitude, by contrast, is an apparatus that adjusts
the STIMULUS to suit the instrument -- which is measuring the experimenter.

THE TWO-SIDED HAZARD, AND WHY THE ENSEMBLE IS INTERLEAVED
----------------------------------------------------------
A theta fast enough to track ONE orientation would cancel the very modulation OSI
measures. `grating_ensemble` interleaves orientation AND phase at random every
step (rung 8B's own construction, reused unchanged), so theta's timescale
averages over all 12 orientations BY CONSTRUCTION. theta is then PINNED for the
measurement (`|dtheta| = 0` verified) so the probe never chases it, and WEIGHTS
ARE FROZEN throughout (`max|dw| = 0` verified -- `oja=0` IS NOT A FREEZE).

MY PREDICTION, IN ADVANCE, WITH ITS PROVISOS (§3.7)
----------------------------------------------------
**I predict the gate PASSES**: ideal -> ~1.0, floor -> ~0.33 (rung 6's floor,
because the same per-cell rule slices a random cell's own noise identically on
either pathway), separation ~0.67, BOTH arms alive at 12/12 -- i.e. rung 8's
blindness dissolves with NO new mechanism, and GC is NOT needed to calibrate the
probe.

Provisos, each of which tells me what I did not understand if it breaks:
 1. **If the floor INFLATES past 0.50**, a per-cell theta on these channels
    sharpens noise more than it does on rung 6's, and the probe is not rescued --
    it is broken differently. That is rung 8B's predicted-and-unobserved failure
    finally arriving, and it would point at GC after all.
 2. **If the floor DIES (alive < 12)**, this is 8B's windup in a new costume and
    the gate FAILS -- a silent arm is never a good floor (§1.1).
 3. **If the IDEAL stays low**, the ensemble mismatch was NOT the whole cause and
    rung 8's diagnosis is incomplete -- the most interesting outcome, and it
    would mean something other than theta placement is blocking the readout.
 4. **This calibrates the PROBE ONLY. It says NOTHING about H1/H2** -- whether
    waves DEVELOP selectivity is a separate question this does not touch, and my
    rung-8 §8 prediction (H1 NULL, because the wave ensemble is
    orientation-ISOTROPIC and decorrelation removes a redundancy without
    installing an anisotropy) is UNAFFECTED by this gate either way.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PROTOCOL §10.1 rule 3: "Any non-pytest entrypoint (a rung script) must call
# `engine_preamble()` ITSELF." It must run BEFORE any `domains.*` import, because
# the FIRST import of `substrate_rs` binds the engine for the whole process — a
# preamble that runs afterwards is a no-op that LOOKS correct. Caught live: this
# rung's scripts imported `domains.complex_cells` first and silently loaded the
# CANONICAL tree's engine via the `.pth`, which went RED mid-session when a
# concurrent agent rebuilt it from ITS Rust source (§11.5: "long-running
# measurement is not a lock").
from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import cell_stats, present  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.lateral_world import set_lat_params  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, adapt_theta as adapt_theta_on_waves, build, develop_retina,
    freeze_all, ideal_split_gabor,
)
from scripts.rung8b_lib import (  # noqa: E402
    grating_ensemble, theta_of, weights_of,
)

N_UNITS = 6
ADAPT = 2000


def adapt_theta_on_probe(world, steps=ADAPT, *, seed=7):
    """Settle RUNG 6's OWN EMA theta on the PROBE ensemble.

    This is `rung8_lib.adapt_theta` with EXACTLY ONE thing changed: the ensemble.
    Rung 6's rule (`oo_sunit_adapt_theta`, gated by its own `homeo` knob) is
    untouched, its constants are untouched, its placement is untouched, and no
    seed is edited (PROTOCOL §11.4). `oo_eta=0` makes the learning rules exact
    identities while the theta rule still runs -- rung 6's own construction.
    """
    p = world.s.nodes("OnOffParams")[0]
    old = float(world.s.node(p)["attrs"]["oo_eta"])
    set_params(world, oo_eta=0.0, frozen=0.0, homeo=1.0)
    # The retina supplies the drive theta adapts to, but must not LEARN while
    # theta settles -- rung 8's own discipline in `adapt_theta`.
    if world.s.nodes("LatParams"):
        set_lat_params(world, frozen=1.0)
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        present(world, grating_ensemble(world, rng))
    set_params(world, oo_eta=old)


def prepare(chan, *, ideal, adapt, seed=0):
    w, us, _a, _b = build(seed=seed, n_units=N_UNITS, channels=chan)
    develop_retina(w, 3000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    wt0 = weights_of(w, us)
    if adapt == "waves":
        adapt_theta_on_waves(w, 400)          # rung 8's own arm, verbatim
    else:
        adapt_theta_on_probe(w, ADAPT)
    # PIN theta: the probe must never chase it (rung 6's discipline).
    set_params(w, homeo=0.0)
    freeze_all(w)
    dw = float(np.abs(weights_of(w, us) - wt0).max())
    return w, us, dw


def measure(w, us):
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    return {"osi": float(st["osi"].mean()),
            "alive": float((tc > 1e-9).sum(axis=1).mean())}


def main() -> int:
    print("=" * 78)
    print("RUNG 8C — §1 CALIBRATION: IS THE BLINDNESS *ONLY* THE ENSEMBLE MISMATCH?")
    print(provenance_line())
    print("  Rung 6's OWN theta rule. No GC. No setpoint. Nothing added.")
    print("  Seeds 0/3000 (already burned). NO confirmatory seed.")
    print("=" * 78)

    rows = {}
    for chan in ("lateral", "degenerate"):
        for adapt in ("waves", "probe"):
            wi, usi, dwi = prepare(chan, ideal=True, adapt=adapt)
            wf, usf, dwf = prepare(chan, ideal=False, adapt=adapt)
            mi, mf = measure(wi, usi), measure(wf, usf)
            sep = mi["osi"] - mf["osi"]
            rows[(chan, adapt)] = (mi, mf, sep, theta_of(wi).mean(),
                                   theta_of(wf).mean(), max(dwi, dwf))

    print(f"\n  {'pathway':<11s} {'theta on':<7s} | {'IDEAL':>7s} {'aliv':>5s} "
          f"{'th_i':>7s} | {'FLOOR':>7s} {'aliv':>5s} {'th_f':>7s} | {'sep':>7s}")
    print("  " + "-" * 76)
    for chan in ("lateral", "degenerate"):
        for adapt in ("waves", "probe"):
            mi, mf, sep, thi, thf, dw = rows[(chan, adapt)]
            print(f"  {chan:<11s} {adapt:<7s} | {mi['osi']:7.4f} "
                  f"{mi['alive']:5.2f} {thi:7.3f} | {mf['osi']:7.4f} "
                  f"{mf['alive']:5.2f} {thf:7.3f} | {sep:7.4f}")
        print("  " + "-" * 76)

    print("\n--- FREEZE AUDIT (weights must not move: `oja=0` IS NOT a freeze) ---")
    for k, v in rows.items():
        print(f"  {str(k):<28s} max|dw| = {v[5]:.3e}")

    # ---------------------------------------------------------------- #
    # THE GATE — rung 8B's criteria, PLUS §1's fourth clause (arms alive).
    # ---------------------------------------------------------------- #
    print("\n--- THE §1 GATE, on the COMPOSED pathway, theta settled on the PROBE ---")
    mi, mf, sep, thi, thf, _dw = rows[("lateral", "probe")]
    checks = [("G1 IDEAL >= 0.80", mi["osi"] >= 0.80, f"{mi['osi']:.4f}"),
              ("G2 FLOOR <= 0.50", mf["osi"] <= 0.50, f"{mf['osi']:.4f}"),
              ("G3 SEPARATION >= 0.30", sep >= 0.30, f"{sep:.4f}"),
              ("G0 IDEAL arm ALIVE (>0 of 12)", mi["alive"] > 0,
               f"{mi['alive']:.2f} of 12"),
              ("G0 FLOOR arm ALIVE (>0 of 12)", mf["alive"] > 0,
               f"{mf['alive']:.2f} of 12")]
    for name, ok, val in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<34s} {val}")
    ok = all(c[1] for c in checks)
    print(f"\n  GATE: {'PASS' if ok else 'FAIL'}")
    print(f"\n  Rung 8 reported IDEAL 0.1290 with theta settled on WAVES.")
    print(f"  Here, with theta settled on the ensemble being RESPONDED TO,")
    print(f"  the SAME rule on the SAME channels gives IDEAL {mi['osi']:.4f}.")
    print("""
  IF THIS PASSES, THE HONEST READING IS NARROW:
    * The PROBE is calibrated on the composed pathway -- nothing more.
    * NO new mechanism was needed. GC is NOT indicated by this result, and
      rung 8B's "GCAL's A requires GCAL's GC" is about GCAL's SETPOINT, which
      is not in play here: rung 6's rule has no setpoint to transfer.
    * H1/H2 remain UNTESTED and REQUIRE THEIR OWN PRE-REGISTRATION. Nothing
      here says waves DEVELOP anything -- my rung-8 §8 prediction (H1 NULL,
      the wave ensemble is orientation-ISOTROPIC) is untouched.
    * The 9.5x drive gap between a random cell and an ideal cell is NOT fixed
      by this and remains the deep hazard: the floor's ~0.33 is a per-cell
      homeostat slicing a random cell's OWN noise, on either pathway.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
