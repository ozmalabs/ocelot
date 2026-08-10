"""parallax_motion_pilot — POWER ANALYSIS on BURNED seeds 116000-116039.

Restricted to already-burned seeds (PROTOCOL §3 clause 3). Produces the CI
widths + effect sizes that fix n and the pre-registered predictions, for BOTH
stages and BOTH tolerances. NO confirmatory seed touched.
"""
from __future__ import annotations
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_motion_char import (make_projected_scene, carve, SQRT5,
                                  STAGE_A_BASE, STAGE_A_DEPTHS, STAGE_A_REF)
from parallax_real_char import make_real_scene, bsds_paths
from domains.motion_group_world import vector_field
from parallax_char import group_common_fate

PILOT = list(range(116000, 116040))   # BURNED


def ci(x):
    x = np.asarray(x, float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def carve_windowed(sc, tau):
    """The windowed-slide baseline carve (make_real_scene dict), reused verbatim."""
    delta = np.array([0.0, float(sc["shifts"][sc["ref_idx"]])])
    V = vector_field(sc["a"], sc["b_depth"], sc["block"])
    R = V - delta
    lab, nl = group_common_fate(R, tau)
    sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
    p = np.asarray(sizes, float); p = p / p.sum()
    return float(1.0 / np.sum(p * p)), sizes[0] / lab.size


def main():
    paths = bsds_paths()
    base, depths = STAGE_A_BASE, STAGE_A_DEPTHS

    print("== BASELINE floor re-earn: windowed slide [0,3,6] vs Stage-A projected ==")
    for tau, tn in ((0.0, "t0"), (SQRT5, "s5")):
        we, pe, dok = [], [], []
        for sd in PILOT:
            sw = make_real_scene(np.random.default_rng(sd), [0, 3, 6], 8, 144, 1, paths, select="random")
            we.append(carve_windowed(sw, tau)[0])
            sp = make_projected_scene(np.random.default_rng(sd), depths, base, 8, 144, 1, paths)
            r = carve(sp, tau); pe.append(r["eff"]); dok.append(r["depth_order_correct"])
        print(f"  {tn}: windowed eff={ci(we)}  projected eff={ci(pe)}  depth_order_ok={np.mean(dok):.3f}")

    print("== STAGE A static control (base=0) ==")
    for tau, tn in ((0.0, "t0"), (SQRT5, "s5")):
        st = [carve(make_projected_scene(np.random.default_rng(sd), depths, 0.0, 8, 144, 1, paths), tau)["eff"]
              for sd in PILOT]
        print(f"  {tn}: static eff={ci(st)}")

    print("== STAGE B(i) single slanted plane (Z0=7.5, d0=4), sweep tilt ==")
    Z0 = 7.5
    for tilt in (0.0, 0.2, 0.4, 0.6, 0.8):
        e0, e5, steps = [], [], []
        for sd in PILOT:
            sc = make_projected_scene(np.random.default_rng(sd), [Z0], base, 8, 144, 0, paths,
                                      tilt=tilt, tilt_bands=(0,))
            e0.append(carve(sc, 0.0)["eff"]); e5.append(carve(sc, SQRT5)["eff"])
            steps.append(float(np.abs(np.diff(sc["s_col"][::8])).max()))
        print(f"  tilt={tilt:.1f} per_block_step_max={max(steps):.0f}: "
              f"eff(t0)={ci(e0)}  eff(s5)={ci(e5)}")

    print("== STAGE B(ii) 3 planes, MIDDLE slanted, sweep tilt (merge-wrongly?) ==")
    for tilt in (0.0, 0.2, 0.4, 0.6):
        e5, dok = [], []
        for sd in PILOT:
            sc = make_projected_scene(np.random.default_rng(sd), depths, base, 8, 144, 1, paths,
                                      tilt=tilt, tilt_bands=(1,))
            r = carve(sc, SQRT5); e5.append(r["eff"]); dok.append(r["depth_order_correct"])
        print(f"  tilt={tilt:.1f}: eff(s5)={ci(e5)}  depth_order_ok={np.mean(dok):.3f}")

    print("== STAGE B(iii) translation + camera ROTATION, sweep rot (rad) ==")
    for rot in (0.0, 0.02, 0.04, 0.08):
        e5, dok, steps = [], [], []
        for sd in PILOT:
            sc = make_projected_scene(np.random.default_rng(sd), depths, base, 8, 144, 1, paths, rot=rot)
            r = carve(sc, SQRT5); e5.append(r["eff"]); dok.append(r["depth_order_correct"])
            steps.append(float(np.abs(np.diff(sc["s_col"][::8])).max()))
        print(f"  rot={rot:.02f} per_block_step_max={max(steps):.0f}: "
              f"eff(s5)={ci(e5)}  depth_order_ok={np.mean(dok):.3f}")

    print("== STAGE B(iv) PURE rotation (base=0), sweep rot — no depth, spurious surfaces? ==")
    for rot in (0.0, 0.02, 0.04, 0.08):
        e0, e5 = [], []
        for sd in PILOT:
            sc = make_projected_scene(np.random.default_rng(sd), depths, 0.0, 8, 144, 1, paths, rot=rot)
            e0.append(carve(sc, 0.0)["eff"]); e5.append(carve(sc, SQRT5)["eff"])
        print(f"  rot={rot:.02f}: eff(t0)={ci(e0)}  eff(s5)={ci(e5)}")


if __name__ == "__main__":
    main()
