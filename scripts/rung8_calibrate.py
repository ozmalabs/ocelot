"""RUNG 8 — MEASURE CALIBRATION + THE POSITIVE CONTROL (PROTOCOL §1).

*A gate whose measure passes noise is not a gate.* Before any arm:

  1. the measure on RANDOM input           -> must score at the floor;
  2. the measure on an IDEAL exemplar      -> must score high;
  3. the measure against LEARNING DURATION -> if the score moves with how long
     you trained on the SAME input, the measure is duration-confounded.

Plus the two things this rung's supervisor named explicitly:

  4. **THE UNTRAINED FLOOR, MEASURED PER-INIT, IN THIS RUN.** OSI's random floor
     is INIT-DEPENDENT — 0.0044 (DC init) vs 0.3899 (signed init), 89x, same
     probe (the w0 ablation); rung 6's 0.3168 is a third value. **A floor is not
     inheritable.** So `untrained` is an ARM here, at the exact init the arms
     use, through the same frozen probe. A "lift" below its own untrained floor
     is not a lift — that is how rung 5's zero-mean arm's apparent 0.3665
     evaporated.
  5. **THE POSITIVE CONTROL.** Given a PERFECTLY BIASED ensemble (one
     orientation, over and over) can the rule grow an orientation-selective cell
     AT ALL, on THESE channels? Rung 3's eta was a null instrument and only its
     positive control revealed it. The eye agent's three positive controls caught
     three false positives (an inert arm looking stable; a clock bug starving
     input; a reference erasing the image it measured).

Seeds 0-2 / 3000, ALREADY BURNED. No confirmatory seed is touched here.

THE `w0` QUESTION, ANSWERED BY MEASUREMENT (part 6)
---------------------------------------------------
The supervisor asked that a rung minting Units be run at `w0=1.0` and `w0=0.0`.
This rung mints `SUnit`s — rung 6's layer — and the w0-ablation agent already
established, on that IDENTICAL layer, that the ablation is ARCHITECTURALLY EMPTY:

  * the cells read the EFFECTIVE RF `w+ - w-`, and ON/OFF start at the SAME `w0`
    with INDEPENDENT jitter, so the effective RF is ALREADY zero-mean at step 0
    — there is no DC prior to ablate in the quantity the rules and the probe both
    read;
  * a zero-mean/signed init is forbidden by the ARCHITECTURE, not by taste:
    `oo_learn_sub` clips every weight to `[0, oo_wmax]` (Dale's law, a rule the
    agent holds). A negative initial weight is not an arm — it is a state the
    first rule firing deletes.

That is inherited reasoning, so this part MEASURES it in THIS composed world
rather than trusting it, with the ablation's own statistic — and runs the OSI
floor at BOTH `w0` values anyway, since both are Dale-legal.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.complex_cells import binarize, grating, present  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.lateral_world import set_lat_params  # noqa: E402
from domains.onoff_world import segregation, set_params, signed_rf  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, RF, adapt_theta, build, develop_retina, ideal_split_gabor, osi_of,
    run_waves,
)
from scripts.w0_ablation_lib import dc_power_fraction, frac_negative  # noqa: E402


def line(k, v):
    print(f"  {k:<52s} {v}")


def train_on_orientation(world, theta_deg, steps, *, seed=0, period=PERIOD):
    """Show ONE orientation at random phases. Rung 6's positive-control
    stimulus, unchanged. Mechanical ingest."""
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        ph = float(rng.uniform(0, 2 * np.pi))
        present(world, binarize(grating((world.h, world.w), theta_deg, ph,
                                        period)))


def main():
    print("=" * 78)
    print("RUNG 8 CALIBRATION — the measure, the floor PER INIT, the control")
    print(provenance_line())
    print("=" * 78)

    # ----------------------------------------------------------------- #
    # 1 + 2. THE MEASURE: random weights -> floor; ideal split Gabor -> high.
    #        Through the composed (lateral) pathway, frozen.
    # ----------------------------------------------------------------- #
    print("\n--- 1+2. THE MEASURE on the COMPOSED pathway (frozen probe) ---")
    for chan in ("lateral", "degenerate"):
        w, us, _a, _b = build(seed=0, n_units=6, channels=chan)
        develop_retina(w, 3000)            # the retina reaches ITS fixed point
        adapt_theta(w, 400)
        o_rand, _ = osi_of(w, us)          # untouched init = the random floor

        w2, us2, _a2, _b2 = build(seed=0, n_units=6, channels=chan)
        develop_retina(w2, 3000)
        for u in us2:
            ideal_split_gabor(w2, u, theta=0.0, phase=0.0)
        adapt_theta(w2, 400)
        o_ideal, st_i = osi_of(w2, us2)
        pk = st_i["tuning"].max(axis=1)
        bs = np.maximum(st_i["baseline"], 1e-9)
        line(f"[{chan}] untouched-init OSI (the FLOOR)",
             f"{o_rand.mean():.4f}")
        line(f"[{chan}] IDEAL split-Gabor OSI (the TARGET)",
             f"{o_ideal.mean():.4f}  peak/base {(pk / bs).mean():.2f}")

    # ----------------------------------------------------------------- #
    # 3. DURATION CONFOUND: does OSI move with training length on the SAME
    #    input while the rule is FROZEN? It must not.
    # ----------------------------------------------------------------- #
    print("\n--- 3. DURATION CONFOUND (frozen rule, same input) ---")
    w, us, _a, _b = build(seed=0, n_units=6, channels="lateral")
    develop_retina(w, 3000)
    adapt_theta(w, 400)
    for steps in (0, 400, 1600):
        o, _ = osi_of(w, us)
        line(f"frozen, after {steps:5d} probe-steps  OSI", f"{o.mean():.4f}")
        set_params(w, frozen=1.0)   # stay frozen; only the clock advances
        set_lat_params(w, frozen=1.0)
        run_waves(w, 400 if steps == 0 else 1200 if steps == 400 else 0)

    # ----------------------------------------------------------------- #
    # 4. THE UNTRAINED FLOOR, PER INIT, IN THIS RUN — an ARM, not an
    #    inheritance. Both w0 values; both Dale-legal.
    # ----------------------------------------------------------------- #
    print("\n--- 4. UNTRAINED FLOOR per init (n=8 burned seeds, THIS run) ---")
    for chan in ("lateral", "degenerate"):
        for w0 in (1.0, 0.0):
            vals = []
            for sd in range(8):
                w, us, _a, _b = build(seed=sd, n_units=6, channels=chan, w0=w0)
                develop_retina(w, 3000)
                adapt_theta(w, 400)
                o, _ = osi_of(w, us)
                vals.append(o.mean())
            v = np.array(vals)
            line(f"[{chan}] w0={w0:g}  untrained OSI",
                 f"{v.mean():.4f} +/- {v.std(ddof=1):.4f}  "
                 f"[{v.min():.4f}, {v.max():.4f}]")

    # ----------------------------------------------------------------- #
    # 5. THE POSITIVE CONTROL — is the rule a NULL INSTRUMENT on THESE
    #    channels? A perfectly biased ensemble: ONE orientation, ever.
    # ----------------------------------------------------------------- #
    print("\n--- 5. POSITIVE CONTROL: biased ensemble (0 deg only) ---")
    for chan in ("lateral", "degenerate"):
        for eta in (5e-4, 1e-4):
            w, us, _a, _b = build(seed=0, n_units=6, channels=chan, eta=eta)
            develop_retina(w, 3000)
            adapt_theta(w, 400)
            set_params(w, oo_eta=eta, frozen=0.0)
            if w.s.nodes("LatParams"):
                set_lat_params(w, frozen=0.0)
            train_on_orientation(w, 0.0, 1500, seed=0)
            o, st = osi_of(w, us)
            pk = st["tuning"].max(axis=1)
            bs = np.maximum(st["baseline"], 1e-9)
            prefs = [float(np.argmax(st["tuning"][i])) for i in range(len(us))]
            clump = float(np.mean([segregation(w, u)["clumpiness"] for u in us]))
            line(f"[{chan}] eta={eta:g}  OSI",
                 f"{o.mean():.4f} (max {o.max():.4f})  "
                 f"peak/base {(pk / bs).mean():7.2f}  clump {clump:.3f}  "
                 f"prefs {prefs}")

    # ----------------------------------------------------------------- #
    # 6. THE w0 AUDIT — measured here, not inherited.
    # ----------------------------------------------------------------- #
    print("\n--- 6. w0 AUDIT: is there a DC prior in the EFFECTIVE RF? ---")
    for w0 in (1.0, 0.0):
        w, us, _a, _b = build(seed=0, n_units=6, channels="lateral", w0=w0)
        rfs = [signed_rf(w, u) for u in us]
        dcf = float(np.mean([dc_power_fraction(r) for r in rfs]))
        fneg = float(np.mean([frac_negative(r) for r in rfs]))
        line(f"w0={w0:g}  effective RF (w+ - w-) DC power fraction",
             f"{dcf:.6f}")
        line(f"w0={w0:g}  effective RF frac(w<0)", f"{fneg:.4f}")


if __name__ == "__main__":
    main()
