"""parallax_subpixel_measure — CONFIRMATORY measurement for rung 127000.

WHAT BINDS 126000's 0.12-rad rotation bound? Runs ONLY the arms in
VISION_PARALLAX_SUBPIXEL_PREREG.md on FRESH seeds 127000-127079: the six SENSOR
variants (default / subpix_sensor / finer_block / percol_remap[/_cont] / oracle),
the subpix_render diagnostic, the continuous-oracle flatness check, and the
default-arm byte-identity to 126000. Prints engine provenance FROM INSIDE the
process and aborts on divergence (§10). No wall-clock quantity is a verdict.

  python scripts/parallax_subpixel_measure.py pilot     # burned 116000-116029
  python scripts/parallax_subpixel_measure.py confirm    # fresh 127000-127079
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_subpixel_char import (ARMS, arm_int_int, arm_oracle,
                                    rebuild_scene_subpix_render,
                                    continuous_oracle_band_resid, efference_field)
from parallax_affine_char import scene, carve_full, vector_field_eff, GRID, BLOCK
from parallax_char import SQRT5
from parallax_real_char import bsds_paths
from parallax_motion_char import STAGE_A_BASE, STAGE_A_DEPTHS
from domains.engine_provenance import provenance_line, engine_preamble, engine_provenance
engine_preamble()

DEPTHS, BASE, REF = STAGE_A_DEPTHS, STAGE_A_BASE, 1
ROTS = [0.0, 0.04, 0.08, 0.12, 0.14, 0.16]
# Exploratory-only extension (burned seeds, pilot mode) to confirm the oracle holds:
ROTS_ORACLE_EXT = [0.20, 0.30, 0.50]


def _assert_engine(tag):
    line = provenance_line(); p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), f"[{tag}] source_match={p['source_match']}: {line}"
    return line


def _ci(x):
    x = np.asarray(x, float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return [float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def _rate_ci(oks):
    """Bootstrap CI of a proportion over seeds."""
    return _ci([1.0 if o else 0.0 for o in oks])


def sweep_arm(arm_name, seeds, rots, paths):
    """depth_order_rate + per-band mean residual, per rot, for one arm."""
    fn = ARMS[arm_name]
    out = {}
    for rot in rots:
        oks = []; brs = []
        for sd in seeds:
            sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
            ok, br = fn(sc)
            oks.append(ok); brs.append(br)
        m = np.nanmean(brs, axis=0)
        out[f"rot_{rot}"] = {
            "depth_order_rate": float(np.mean(oks)),
            "depth_order_ci": _rate_ci(oks),
            "band_resid": [float(v) for v in m],
        }
    return out


def sweep_subpix_render(seeds, rots, paths):
    """The INADMISSIBLE render diagnostic (arm builds its own scene)."""
    out = {}
    for rot in rots:
        oks = []; brs = []
        for sd in seeds:
            sc = rebuild_scene_subpix_render(sd, DEPTHS, BASE, REF, rot, paths)
            ok, br = arm_int_int(sc)
            oks.append(ok); brs.append(br)
        m = np.nanmean(brs, axis=0)
        out[f"rot_{rot}"] = {"depth_order_rate": float(np.mean(oks)),
                             "depth_order_ci": _rate_ci(oks),
                             "band_resid": [float(v) for v in m]}
    return out


def sweep_oracle_rounded(seeds, rots, paths):
    out = {}
    for rot in rots:
        oks = []
        for sd in seeds:
            sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
            ok, _ = arm_oracle(sc, pred_real=False)
            oks.append(ok)
        out[f"rot_{rot}"] = {"depth_order_rate": float(np.mean(oks)),
                             "depth_order_ci": _rate_ci(oks)}
    return out


def continuous_oracle_sweep(seeds, rots, paths):
    out = {}
    for rot in rots:
        brs = []
        for sd in seeds:
            sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
            brs.append(continuous_oracle_band_resid(sc))
        m = np.mean(brs, axis=0)
        out[f"rot_{rot}"] = {"band_resid": [float(v) for v in m],
                             "order_ok": bool(m[2] > m[1] > m[0])}
    return out


def bound_of(sweep):
    """First rot at which depth_order_rate drops below 0.5 (the bound), read off
    the swept curve. Returns the last rot >=0.5 as the tolerated bound."""
    last_ok = None
    for k, v in sweep.items():
        rot = float(k.split("_")[1])
        if v["depth_order_rate"] >= 0.5:
            last_ok = rot
    return last_ok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "confirm"
    if mode == "pilot":
        seeds = list(range(116000, 116030)); outname = "parallax_subpixel_pilot.json"
        rots = ROTS
    else:
        seeds = list(range(127000, 127080)); outname = "parallax_subpixel.json"
        rots = ROTS

    t0 = time.time(); prov = _assert_engine("start"); load0 = os.getloadavg()
    paths = bsds_paths()
    res = {"mode": mode, "provenance": prov, "seeds": [seeds[0], seeds[-1]], "n": len(seeds),
           "depths": DEPTHS, "base": BASE, "ref_idx": REF, "block": BLOCK, "grid": GRID,
           "rots": rots, "loadavg_start": load0, "sqrt5": SQRT5}

    # ---- BYTE-IDENTITY: default arm (int_int) == 126000 full_cf on the residual ----
    bi = []
    for sd in seeds:
        sc = scene(sd, DEPTHS, BASE, REF, rot=0.0, paths=paths)
        ok_new, br_new = arm_int_int(sc)
        r_126 = carve_full(sc, SQRT5)  # 126000's full_cf
        bi.append(abs(float(br_new[REF]) - float(np.asarray(r_126["band_resid"])[REF])) < 1e-9)
    res["byte_identity_default_vs_126000_full_cf"] = {"all_true": bool(all(bi)),
                                                      "n_true": int(sum(bi)), "n": len(seeds)}
    _assert_engine("mid")

    # ---- THE SIX ARMS on the rotation sweep ----
    res["arms"] = {}
    for arm in ARMS:
        res["arms"][arm] = sweep_arm(arm, seeds, rots, paths)

    # ---- subpix_render diagnostic + oracle-rounded ----
    res["subpix_render_diag"] = sweep_subpix_render(seeds, rots, paths)
    res["oracle_rounded"] = sweep_oracle_rounded(seeds, rots, paths)

    # ---- continuous oracle flatness (the entanglement refutation) ----
    res["continuous_oracle"] = continuous_oracle_sweep(seeds, rots, paths)

    _assert_engine("mid2")

    # ---- EXPLORATORY oracle extension (pilot/burned only, to confirm it holds) ----
    if mode == "pilot":
        res["oracle_ext_burned"] = sweep_arm("oracle", seeds, ROTS_ORACLE_EXT, paths)
        res["continuous_oracle_ext_burned"] = continuous_oracle_sweep(seeds, ROTS_ORACLE_EXT, paths)

    # ---- bounds per arm ----
    res["bounds"] = {arm: bound_of(res["arms"][arm]) for arm in ARMS}
    res["bounds"]["subpix_render_diag"] = bound_of(res["subpix_render_diag"])

    res["loadavg_end"] = os.getloadavg(); res["wall_s"] = time.time() - t0
    res["provenance_after"] = provenance_line()
    res["provenance_stable"] = (res["provenance_after"] == prov)
    res["source_match"] = engine_provenance()["source_match"]
    _assert_engine("end")

    outp = os.path.join(_ROOT, "results", outname)
    with open(outp, "w") as f:
        json.dump(res, f, indent=1)
    print("WROTE", outp, "| mode", mode)
    print("provenance:", prov, "stable:", res["provenance_stable"], "source_match:", res["source_match"])
    print("loadavg start/end:", load0, res["loadavg_end"], "wall_s:", round(res["wall_s"], 1))
    print("byte-identity default==126000 full_cf:", res["byte_identity_default_vs_126000_full_cf"])
    print("\ndepth_order_rate per arm per rot:")
    hdr = "  rot   " + "".join(f"{a[:12]:>14s}" for a in ARMS) + f"{'subpixREND':>14s}"
    print(hdr)
    for rot in rots:
        k = f"rot_{rot}"
        row = f"  {rot:.2f}  " + "".join(f"{res['arms'][a][k]['depth_order_rate']:>14.2f}" for a in ARMS)
        row += f"{res['subpix_render_diag'][k]['depth_order_rate']:>14.2f}"
        print(row)
    print("\nBOUNDS (last rot with depth_order_rate>=0.5):", res["bounds"])
    print("\ncontinuous oracle (should be FLAT in rot -> no entanglement):")
    for rot in rots:
        v = res["continuous_oracle"][f"rot_{rot}"]
        print(f"  rot={rot:.2f}: band_resid={['%+.2f'%x for x in v['band_resid']]} order_ok={v['order_ok']}")
    print("\noracle band_resid (single frame pair, true block-mean):")
    for rot in rots:
        v = res["arms"]["oracle"][f"rot_{rot}"]
        print(f"  rot={rot:.2f}: rate={v['depth_order_rate']:.2f} band_resid={['%+.2f'%x for x in v['band_resid']]}")


if __name__ == "__main__":
    main()
