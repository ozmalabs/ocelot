#!/usr/bin/env python
"""FM-0b: THE VACUITY GATE, RE-RUN ON THE WIRED DRIFT.

FM-0 measured `D = max|saw1 - saw0| == 0.000000e+00 EXACTLY` on lum, x, theta
and resp: the Engbert walk was LIVE and drove NOTHING (PROTOCOL §13.2). This is
FM-0's gate, unchanged in statistic, run against the JOB-1 wiring:

  * Γ gained the `Eye -has_gaze-> Gaze` production (the coupling FM-0 found
    INADMISSIBLE -- verified: `Γ rejects: type 'has_gaze' not in vocabulary`);
  * `ey_sample_at_gaze` (a SEED RULE) samples world(gaze + receptor);
  * the adapter states photons at world locations and nothing else.

FM-0's own script is NOT edited (PROTOCOL §11.4 -- it is the failure-mode
agent's file). It is run unmodified for the BEFORE reading; this is the AFTER.
The statistic, the steps, the seed and the positive control are identical.

**This gate is PLUMBING, NOT A FINDING.** `D > 0` is guaranteed by construction
once sampling reads the gaze -- that is what "wire it" MEANS, and §13.1 is
satisfied by saying so rather than by dressing a tautology as a result. The
falsifiable claim this ENABLES (does stabilising the image make the response
fade?) is a separate pre-registered experiment and is NOT run here.

Adapter-only: presents a world, advances the clock, reads attributes back.
`world_sample` and `saw` are graph DATA on EyeParams (PROTOCOL §0).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

import domains.seed_registry  # noqa: F401
from domains import eye_world
from substrate.boot_core import boot_core, load_seeds_into


def build(seed: int, saw: float, world: np.ndarray, h: int = 16, w: int = 16):
    """Boot an eye with `saw` set as graph data. Identical in every other
    respect -- both arms get the SAME world."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    wo = eye_world.EyeWorld(s, h=h, w=w, gaze_l=21, seed=seed)
    wo.add_world(world)
    eye_world.set_params(wo, eye=1.0, saw=saw, world_sample=1.0)
    return wo


def static_world(seed: int, wh: int, ww: int) -> np.ndarray:
    """A fixed structured scene -- identical across arms. Same generator as
    FM-0's `static_frame`, sized to the world rather than the retina."""
    yy, xx = np.mgrid[0:wh, 0:ww]
    f = 0.5 + 0.35 * np.sin(2 * np.pi * (xx + yy) / 8.0)
    f += 0.15 * np.exp(-(((yy - 5) ** 2 + (xx - 11) ** 2) / 6.0))
    return np.clip(f, 0.0, 1.0)


def read_maps(world):
    return {
        "resp": world.responses(),
        "x": world.drives(),
        "theta": world.thetas(),
        "lum": np.array([[float(world.s.node(world.cells[(r, c)])["attrs"]["lum"])
                          for c in range(world.w)] for r in range(world.h)]),
    }


def main():
    STEPS = int(os.environ.get("FM0B_STEPS", "400"))
    SEED = 0  # already-burned calibration seed; no confirmatory seed consumed

    print(ep.provenance_line())
    print(f"FM-0b DRIFT-WIRED AUDIT — steps={STEPS} seed={SEED}")
    print()

    wh, ww = 21 + 16 - 1, 21 + 16 - 1
    scene = static_world(SEED, wh, ww)
    print(f"world: {wh}x{ww}, range [{scene.min():.4f}, {scene.max():.4f}], "
          f"SD {scene.std():.4f}")

    arms, trajs = {}, {}
    for saw in (1.0, 0.0):
        world = build(SEED, saw, scene)
        traj = [world.gaze_pos()]
        hist = []
        for t in range(STEPS):
            world.step(frame=None)   # the GRAPH samples; the adapter presents no frame
            traj.append(world.gaze_pos())
            hist.append(read_maps(world))
        arms[saw] = hist
        trajs[saw] = traj

    # ---- POSITIVE CONTROL ON THE MANIPULATION (FM-0's, verbatim) -----------
    def n_distinct(traj):
        return len(set(traj))

    def path_len(traj):
        return sum(abs(a[0] - b[0]) + abs(a[1] - b[1])
                   for a, b in zip(traj[:-1], traj[1:]))

    print()
    print("POSITIVE CONTROL ON THE MANIPULATION (is `saw` live?)")
    for saw in (1.0, 0.0):
        t = trajs[saw]
        print(f"  saw={saw}: gaze visited {n_distinct(t):4d} distinct cells, "
              f"path length {path_len(t):5d}, start {t[0]} end {t[-1]}")
    live = path_len(trajs[1.0]) > 0 and path_len(trajs[0.0]) == 0
    print(f"  => manipulation LIVE (saw=1 moves, saw=0 frozen): {live}")

    # ---- POSITIVE CONTROL ON THE READER -----------------------------------
    # An absence must never be read off a soft accessor. If the sheet is blank
    # in BOTH arms, D==0 would mean "no image", not "no coupling".
    print()
    print("POSITIVE CONTROL ON THE READER (is there an image to move at all?)")
    for saw in (1.0, 0.0):
        lum = arms[saw][-1]["lum"]
        print(f"  saw={saw}: lum range [{lum.min():.4f}, {lum.max():.4f}] "
            f"SD {lum.std():.4f}; nonzero cells {int((lum > 0).sum())}/{lum.size}")

    # ---- THE GATE (FM-0's statistic, unchanged) ---------------------------
    print()
    print("D(t) = max over cells |arm_saw1 - arm_saw0|, reported as max over t")
    maxD = {}
    for key in ("lum", "x", "theta", "resp"):
        d, argt = 0.0, -1
        for t in range(STEPS):
            v = float(np.max(np.abs(arms[1.0][t][key] - arms[0.0][t][key])))
            if v > d:
                d, argt = v, t
        maxD[key] = d
        print(f"  max_t D_{key:6s} = {d:.6e}   (at step {argt})")

    print()
    allzero = all(v == 0.0 for v in maxD.values())
    if live and allzero:
        print("VERDICT: **STILL VACUOUS** — the wiring did not take. D == 0.0")
        print("EXACTLY despite a live walk. STOP; burn no confirmatory seed.")
    elif not live:
        print("VERDICT: INERT MANIPULATION — the audit is uninterpretable.")
    else:
        moved = [k for k, v in maxD.items() if v > 0.0]
        print("VERDICT: **LOAD-BEARING**. The drift moves: " + ", ".join(moved))
        print("FM-0's D == 0.0 is inverted on these attributes. This is the")
        print("PLUMBING proved, not a scientific finding — D > 0 is guaranteed")
        print("once sampling reads the gaze. It is the ENTRY GATE (§1 clause 5)")
        print("that Troxler now has, and did not have before.")


if __name__ == "__main__":
    main()
