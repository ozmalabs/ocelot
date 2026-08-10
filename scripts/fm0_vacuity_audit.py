#!/usr/bin/env python
"""FM-0: THE VACUITY GATE — can `saw` reach the receptor sheet at all?

Pre-registered in VISION_FAILURE_MODES_PREREG.md §FM-0, committed before this ran.

The proposed Troxler test ("freeze the drift => the response decays") presupposes that
the drift MOVES THE IMAGE ON THE RECEPTORS. This audit measures whether it can, before
any confirmatory seed is burned.

Adapter-only: presents frames, advances the clock, reads attributes back. Every
decision is a seed rule; `saw` is graph DATA on EyeParams (PROTOCOL §0) -- the
ablation is the agent's own configuration, not a fork in the host.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

import domains.seed_registry  # noqa: F401
from domains import eye_world
from substrate.boot_core import boot_core, load_seeds_into


def build(seed: int, saw: float, h: int = 16, w: int = 16):
    """Boot an eye with `saw` set as graph data. Identical in every other respect."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    world = eye_world.EyeWorld(s, h=h, w=w, gaze_l=21, seed=seed)
    eye_world.set_params(world, eye=1.0, saw=saw)
    return world


def static_frame(seed: int, h: int = 16, w: int = 16) -> np.ndarray:
    """A fixed structured frame -- identical across arms."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    # a smooth oriented grating + a blob: structured, not noise
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
    STEPS = 400
    SEED = 0  # already-burned calibration seed; no confirmatory seed consumed

    print(ep.provenance_line())
    print(f"FM-0 VACUITY AUDIT — steps={STEPS} seed={SEED}")
    print()

    frame = static_frame(SEED)
    print(f"stimulus: static frame, range [{frame.min():.4f}, {frame.max():.4f}], "
          f"SD {frame.std():.4f}")

    arms = {}
    trajs = {}
    for saw in (1.0, 0.0):
        world = build(SEED, saw)
        traj = [world.gaze_pos()]
        hist = []
        for t in range(STEPS):
            world.step(frame=frame)
            traj.append(world.gaze_pos())
            hist.append(read_maps(world))
        arms[saw] = hist
        trajs[saw] = traj

    # ---- POSITIVE CONTROL ON THE MANIPULATION -------------------------------
    # If the saw=1 gaze does not move, the audit says nothing (inert manipulation).
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

    # ---- THE GATE -----------------------------------------------------------
    print()
    print("D(t) = max over cells |arm_saw1 - arm_saw0|, reported as max over t")
    maxD = {}
    for key in ("lum", "x", "theta", "resp"):
        d = 0.0
        argt = -1
        for t in range(STEPS):
            v = float(np.max(np.abs(arms[1.0][t][key] - arms[0.0][t][key])))
            if v > d:
                d, argt = v, t
        maxD[key] = d
        print(f"  max_t D_{key:6s} = {d:.6e}   (at step {argt})")

    print()
    allzero = all(v == 0.0 for v in maxD.values())
    if live and allzero:
        print("VERDICT: **VACUOUS**. `saw` is LIVE (the walk moves) but reaches NO")
        print("EyeCell attribute -- D == 0.0 EXACTLY on lum, x, theta and resp at")
        print("every one of %d steps. The drift cannot move the image." % STEPS)
        print("=> The Troxler test as specified CANNOT be run. STOP; burn no")
        print("   confirmatory seed. Per the pre-registered decision rule.")
    elif not live:
        print("VERDICT: INERT MANIPULATION — the audit is uninterpretable.")
    else:
        print("VERDICT: coupling EXISTS (some D > 0) — the edge-based reading was")
        print("wrong; FM-0's proviso 2 (a NodesOfType global read) is the candidate.")


if __name__ == "__main__":
    main()
