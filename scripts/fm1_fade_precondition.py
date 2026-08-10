#!/usr/bin/env python
"""FM-1: THE FADE PRECONDITION — does a static image fade AT ALL?

Pre-registered in VISION_FAILURE_MODES_PREREG.md §FM-1, committed before this ran.

FM-0 established that the drift cannot move the image (D == 0.0 exactly on every
EyeCell attribute). The consequence: **this eye is ALWAYS stabilized** -- it is
permanently in the condition Ditchburn & Ginsborg 1952 and Riggs & Ratliff 1952
created artificially. So the fading question is measurable today, with no drift
involved and no confirmatory seed burned.

§1 CALIBRATION TRIPLE, floors MEASURED IN-RUN (never inherited -- the arc's own OSI
floor is init-dependent by 89x on the identical probe):
  (1) FLOOR:  r(resp, SHUFFLED x) must sit at ~0 -- the probe reports absence when
      the correspondence is destroyed.
  (2) IDEAL:  r(resp(0), x(0)) must be ~1 -- THE POSITIVE CONTROL ON THE READER.
      A fade is an ABSENCE claim; an absence measured off a probe that never saw
      anything is the trap that has caught this arc six times.
  (3) DURATION: the full curve, not an endpoint.

Adapter-only: present, tick, read back.
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
SEED = 0  # already-burned calibration seed


def build(seed=SEED, **kw):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = eye_world.EyeWorld(s, h=H, w=W, gaze_l=21, seed=seed)
    eye_world.set_params(w, eye=1.0, **kw)
    return w


def structured_frame():
    yy, xx = np.mgrid[0:H, 0:W]
    f = 0.5 + 0.35 * np.sin(2 * np.pi * (xx + yy) / 8.0)
    f += 0.15 * np.exp(-(((yy - 5) ** 2 + (xx - 11) ** 2) / 6.0))
    return np.clip(f, 0.0, 1.0)


def noise_frame(seed):
    return np.random.default_rng(seed).random((H, W))


def pearson(a, b):
    a = a.ravel().astype(np.float64)
    b = b.ravel().astype(np.float64)
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")  # a constant map has no correlation -- report it honestly
    return float(np.corrcoef(a, b)[0, 1])


def run(frame, steps=STEPS, seed=SEED):
    w = build(seed=seed)
    rows = []
    rng = np.random.default_rng(12345)
    for t in range(steps):
        w.step(frame=frame)
        resp, x = w.responses(), w.drives()
        shuf = x.ravel().copy()
        rng.shuffle(shuf)
        rows.append({
            "t": t,
            "contrast": float(resp.std()),
            "fidelity": pearson(resp, x),
            "floor": pearson(resp, shuf.reshape(x.shape)),
            "mean_resp": float(resp.mean()),
            "frac_zero": float((resp <= 0.0).mean()),
            "mean_theta": float(w.thetas().mean()),
            "x_sd": float(x.std()),
        })
    return rows


def main():
    print(ep.provenance_line())
    print(f"FM-1 FADE PRECONDITION — H=W={H} steps={STEPS} seed={SEED}")
    mu = 0.024
    print(f"EyeParams: mu={mu} (homeostatic target), beta=0.991 "
          f"(=> EMA tau ~ {1/(1-0.991):.0f} steps), lam=0.01 (theta rate)")
    print()

    frame = structured_frame()
    rows = run(frame)

    # ---- §1 (2) THE POSITIVE CONTROL ON THE READER ------------------------
    r0 = rows[0]
    print("§1 (2) IDEAL EXEMPLAR / POSITIVE CONTROL ON THE READER")
    print(f"  t=0: fidelity r(resp, x) = {r0['fidelity']:.4f}   "
          f"contrast SD = {r0['contrast']:.4f}   x_sd = {r0['x_sd']:.4f}")
    print("  (the probe must SEE the image when it IS there, or every later")
    print("   absence is uninterpretable)")

    # ---- §1 (1) THE FLOOR, MEASURED IN-RUN --------------------------------
    floors = [r["floor"] for r in rows[:50] if not np.isnan(r["floor"])]
    print()
    print("§1 (1) FLOOR, MEASURED IN-RUN (shuffled correspondence)")
    print(f"  r(resp, shuffle(x)) over first 50 steps: "
          f"mean {np.mean(floors):+.4f}  SD {np.std(floors):.4f}  "
          f"max|.| {np.max(np.abs(floors)):.4f}")

    # ---- §1 (3) DURATION: the curve ---------------------------------------
    print()
    print("§1 (3) DURATION — the full curve")
    print(f"  {'step':>5} {'contrast':>10} {'fidelity':>10} {'mean_resp':>10} "
          f"{'frac_zero':>10} {'mean_theta':>11}")
    for t in (0, 1, 2, 5, 10, 25, 50, 100, 150, 200, 300, 400, 600, 800, 1000, 1199):
        r = rows[t]
        fid = f"{r['fidelity']:.4f}" if not np.isnan(r["fidelity"]) else "   nan"
        print(f"  {t:5d} {r['contrast']:10.6f} {fid:>10} {r['mean_resp']:10.6f} "
              f"{r['frac_zero']:10.4f} {r['mean_theta']:11.6f}")

    c0, cE = rows[0]["contrast"], rows[-1]["contrast"]
    print()
    print(f"contrast(0)    = {c0:.6f}")
    print(f"contrast({STEPS-1}) = {cE:.6f}")
    print(f"ratio          = {cE/c0:.6f}   (pre-registered fade criterion: < 0.1)")

    # tau: first step where contrast falls below c0/e
    tau = next((r["t"] for r in rows if r["contrast"] <= c0 / np.e), None)
    print(f"tau (1/e)      = {tau} steps   (predicted 100-200)")

    # ---- PROVISO 2: WHERE do the cells land? mu, or 0? ---------------------
    print()
    print("PRE-REGISTERED PROVISO 2 — WHERE do the cells land? (mu, or rectified 0?)")
    print("  This distinguishes homeostasis (the mechanism I claimed) from")
    print("  rectification (a fade in the right direction for the WRONG reason).")
    rE = rows[-1]
    print(f"  final mean_resp = {rE['mean_resp']:.6f}   vs mu = {mu}")
    print(f"  final frac_zero = {rE['frac_zero']:.4f}   "
          f"(1.0 => every cell pinned at 0 => RECTIFICATION, not homeostasis)")

    # ---- PROVISO 3: pattern loss vs amplitude loss -------------------------
    print()
    print("PRE-REGISTERED PROVISO 3 — pattern loss, or mere amplitude loss?")
    print("  A fade must lose the PATTERN, not just the SCALE. If fidelity stays")
    print("  high while contrast falls, this is a gain change and NOT fading.")
    for t in (0, 100, 400, 1199):
        r = rows[t]
        fid = f"{r['fidelity']:.4f}" if not np.isnan(r["fidelity"]) else "nan (resp is CONSTANT)"
        print(f"  t={t:5d}: contrast {r['contrast']:.6f}   fidelity {fid}")

    # ---- the noise arm ----------------------------------------------------
    print()
    print("CONTROL — the same measure on i.i.d. NOISE input (structure-free)")
    nrows = run(noise_frame(1))
    print(f"  noise: contrast(0) {nrows[0]['contrast']:.6f} -> "
          f"contrast({STEPS-1}) {nrows[-1]['contrast']:.6f}  "
          f"ratio {nrows[-1]['contrast']/nrows[0]['contrast']:.6f}")


if __name__ == "__main__":
    main()
