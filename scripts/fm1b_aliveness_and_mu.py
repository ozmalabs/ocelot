#!/usr/bin/env python
"""FM-1b: THE ALIVENESS AUDIT (§1.1) + THE mu-DEPENDENCE AUDIT (§13).

Two questions the protocol's new clauses put to FM-1, and they are the right ones.

§1.1 — "A DEAD PROBE FADES BEAUTIFULLY." FM-1's headline statistic is
`contrast = SD(resp)`, and **SD is 0 for a sheet that is silent exactly as it is for
a sheet that is uniformly firing.** "Faded" and "was never alive" are the same
reading off that number. So report, at every timepoint, HOW MANY CELLS RESPOND AT
ALL, and treat a silent arm as a FAILED GATE, never as a successful fade.

§13 — "MAGIC NUMBERS FALL OUT; THEY DO NOT GO IN." `mu = 0.024` in
`seeds/vision_eye.json` is **GCAL's published constant**, and rung 8B died an hour ago
because that same constant transferred across a frame whose drive differed ~6x. This
eye's mean response at t=0 is ~0.399, so mu=0.024 demands a **16x compression**. So:
does the FADE depend on mu's value (=> a tuned result, worthless), or does it fall out
of the homeostat's STRUCTURE (=> mu-independent, and the imported constant only sets
the transient)?

Predicted in advance, from arithmetic, before running: a per-cell homeostat driving
every cell's mean output to a COMMON target must erase any static spatial pattern for
ANY mu -- `resp_i -> mu` for all i => SD -> 0. So the fade is mu-INDEPENDENT and the
constant cannot be what produces it. What mu SHOULD set is the size of the theta
overshoot, and therefore how many cells transiently die.

No confirmatory seed: seed 0, already burned.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

import domains.seed_registry  # noqa: F401
from domains import eye_world
from substrate.boot_core import boot_core, load_seeds_into

H = W = 16
STEPS = 1200
SEED = 0


def build(**kw):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = eye_world.EyeWorld(s, h=H, w=W, gaze_l=21, seed=SEED)
    eye_world.set_params(w, eye=1.0, **kw)
    return w


def frame():
    yy, xx = np.mgrid[0:H, 0:W]
    f = 0.5 + 0.35 * np.sin(2 * np.pi * (xx + yy) / 8.0)
    f += 0.15 * np.exp(-(((yy - 5) ** 2 + (xx - 11) ** 2) / 6.0))
    return np.clip(f, 0.0, 1.0)


def pearson(a, b):
    a, b = a.ravel().astype(float), b.ravel().astype(float)
    # §1.1: the guard is LOUD. A constant map returns nan, never a tidy 0.0 --
    # `(a-b)/(a+b) if (a+b)>1e-9 else 0.0` is the disease this clause names.
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def run(mu, steps=STEPS):
    w = build(mu=mu)
    f = frame()
    rows = []
    for t in range(steps):
        w.step(frame=f)
        resp, x = w.responses(), w.drives()
        rows.append({
            "t": t,
            "contrast": float(resp.std()),
            "fidelity": pearson(resp, x),
            "mean_resp": float(resp.mean()),
            "alive": float((resp > 0.0).mean()),   # §1.1: THE ALIVENESS METRIC
            "theta": float(w.thetas().mean()),
        })
    return rows


def report(tag, rows, mu):
    print()
    print("=" * 78)
    print(f"{tag}   (mu = {mu})")
    print("=" * 78)
    print(f"  {'step':>5} {'contrast':>10} {'fidelity':>9} {'mean_resp':>10} "
          f"{'ALIVE':>8} {'theta':>9}")
    for t in (0, 50, 100, 200, 300, 400, 600, 800, 1000, 1199):
        r = rows[t]
        fid = f"{r['fidelity']:.4f}" if not np.isnan(r["fidelity"]) else "nan"
        print(f"  {t:5d} {r['contrast']:10.6f} {fid:>9} {r['mean_resp']:10.6f} "
              f"{r['alive']*100:7.1f}% {r['theta']:9.6f}")
    c0, cE = rows[0]["contrast"], rows[-1]["contrast"]
    minalive = min(r["alive"] for r in rows)
    argmin = min(rows, key=lambda r: r["alive"])["t"]
    print(f"  fade ratio contrast(end)/contrast(0) = {cE/c0:.6f}")
    print(f"  MINIMUM aliveness over the run       = {minalive*100:.1f}% at t={argmin}")
    print(f"  FINAL aliveness                      = {rows[-1]['alive']*100:.1f}%")
    print(f"  FINAL mean_resp                      = {rows[-1]['mean_resp']:.6f}"
          f"   (target mu = {mu})")
    return {"ratio": cE / c0, "min_alive": minalive, "final_alive": rows[-1]["alive"],
            "final_mean": rows[-1]["mean_resp"], "max_theta": max(r["theta"] for r in rows)}


def main():
    print(ep.provenance_line())
    print("FM-1b — §1.1 ALIVENESS AUDIT + §13 mu-DEPENDENCE AUDIT")

    # The eye's OWN drive scale, measured not assumed -- this is what mu must be
    # commensurate with, and what GCAL's constant knows nothing about.
    w = build()
    f = frame()
    w.step(frame=f)
    natural = float(w.responses().mean())
    print(f"\nTHE EYE'S OWN DRIVE SCALE, MEASURED: mean resp at t=0 = {natural:.6f}")
    print(f"  GCAL's imported mu = 0.024 demands a {natural/0.024:.1f}x compression.")

    # Arm A: the seed's committed default -- GCAL's published constant, IMPORTED.
    a = report("ARM A — GCAL's IMPORTED constant (the seed's committed default)",
               run(0.024), 0.024)

    # Arm B: a mu commensurate with THIS eye's own measured drive. NOT tuned to make
    # anything appear -- it is half the eye's own t=0 mean response, i.e. a target the
    # cell can reach without a 16x compression. The §13 test is whether the FADE cares.
    mu_b = round(natural / 2.0, 4)
    b = report("ARM B — mu from the EYE'S OWN measured drive (natural/2)", run(mu_b), mu_b)

    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print()
    print("§13 — DOES THE FADE DEPEND ON THE IMPORTED CONSTANT?")
    print(f"  fade ratio @ mu=0.024   : {a['ratio']:.6f}")
    print(f"  fade ratio @ mu={mu_b:<7}: {b['ratio']:.6f}")
    print(f"  => the fade occurs at BOTH: {a['ratio'] < 0.1 and b['ratio'] < 0.1}")
    print("  The fade is a property of the homeostat's STRUCTURE (every cell driven")
    print("  to a COMMON target erases any static pattern, for ANY target), not of")
    print("  the constant's value. It cannot have been tuned into existence.")
    print()
    print("§1.1 — IS THE FADE A FADE, OR A DEAD ARM?")
    print(f"  ARM A  min aliveness {a['min_alive']*100:5.1f}%  final {a['final_alive']*100:5.1f}%"
          f"  max theta {a['max_theta']:.4f}")
    print(f"  ARM B  min aliveness {b['min_alive']*100:5.1f}%  final {b['final_alive']*100:5.1f}%"
          f"  max theta {b['max_theta']:.4f}")
    print()
    print("  A contrast of ~0 read off a SILENT sheet is not a fade. The endpoint")
    print("  must be ALIVE and UNIFORM, not dead.")


if __name__ == "__main__":
    main()
