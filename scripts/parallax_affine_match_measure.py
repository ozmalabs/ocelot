"""parallax_affine_match_measure — CONFIRMATORY measurement for rung 128000.

DOES IMAGE-ONLY WITHIN-BLOCK AFFINE MATCHING RECOVER 127000's ORACLE? Runs ONLY
the arms in VISION_PARALLAX_AFFINE_MATCH_PREREG.md on FRESH seeds 128000-128079:
rigid (=127000 int_int default) vs affine_match, block-size ablation {6,8,12,16},
the oracle upper bound, the est-err + oracle-init-drift + identifiability
diagnostics, the compute cost (rigid vs affine_match), and the default byte-
identity to 126000. Prints engine provenance FROM INSIDE the process and aborts on
divergence (§10). No wall-clock quantity is a verdict (compute cost is DATA).

  python scripts/parallax_affine_match_measure.py pilot    # burned 116000-116029
  python scripts/parallax_affine_match_measure.py confirm   # fresh 128000-128079
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_affine_match_char import (arm_rigid, arm_affine_match, est_err_diag,
                                        drift_from_truth_diag)
from parallax_subpixel_char import arm_oracle
from parallax_affine_char import scene, carve_full, efference_field, vector_field_eff, GRID, BLOCK
from parallax_subpixel_char import arm_int_int, efference_field_block
from parallax_char import SQRT5
from parallax_real_char import bsds_paths
from parallax_motion_char import STAGE_A_BASE, STAGE_A_DEPTHS
from domains.engine_provenance import provenance_line, engine_preamble, engine_provenance
engine_preamble()

DEPTHS, BASE, REF = STAGE_A_DEPTHS, STAGE_A_BASE, 1
ROTS = [0.0, 0.08, 0.12, 0.16, 0.20]
ROTS_ORACLE_EXT = [0.30, 0.50]     # burned/pilot only — the 0.5 bracket
BLOCKS = [6, 8, 12, 16]


def _assert_engine(tag):
    line = provenance_line(); p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), f"[{tag}] source_match={p['source_match']}: {line}"
    return line


def _rate_ci(oks):
    x = np.asarray([1.0 if o else 0.0 for o in oks], float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return [float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def sweep_arm(arm_fn, seeds, rots, paths, block=None):
    out = {}
    for rot in rots:
        oks = []
        for sd in seeds:
            sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
            res = arm_fn(sc, block=block) if block else arm_fn(sc)
            oks.append(res[0])
        out[f"rot_{rot}"] = {"depth_order_rate": float(np.mean(oks)), "depth_order_ci": _rate_ci(oks)}
    return out


def sweep_oracle(seeds, rots, paths):
    out = {}
    for rot in rots:
        oks = [arm_oracle(scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths))[0] for sd in seeds]
        out[f"rot_{rot}"] = {"depth_order_rate": float(np.mean(oks)), "depth_order_ci": _rate_ci(oks)}
    return out


def bound_of(sweep):
    last_ok = None
    for k, v in sweep.items():
        rot = float(k.split("_")[1])
        if v["depth_order_rate"] >= 0.5:
            last_ok = rot if last_ok is None else max(last_ok, rot)
    return last_ok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "confirm"
    if mode == "pilot":
        seeds = list(range(116000, 116030)); outname = "parallax_affine_match_pilot.json"
    else:
        seeds = list(range(128000, 128080)); outname = "parallax_affine_match.json"

    t0 = time.time(); prov = _assert_engine("start"); load0 = os.getloadavg()
    paths = bsds_paths()
    res = {"mode": mode, "provenance": prov, "seeds": [seeds[0], seeds[-1]], "n": len(seeds),
           "depths": DEPTHS, "base": BASE, "ref_idx": REF, "block": BLOCK, "grid": GRID,
           "rots": ROTS, "blocks": BLOCKS, "loadavg_start": load0, "sqrt5": SQRT5}

    # ---- BYTE-IDENTITY: rigid(block8) == 127000 int_int == 126000 full_cf ----
    bi_127 = []; bi_126 = []
    for sd in seeds:
        sc = scene(sd, DEPTHS, BASE, REF, rot=0.0, paths=paths)
        _, br_rig, _ = arm_rigid(sc)
        _, br_127 = arm_int_int(sc)
        r126 = carve_full(sc, SQRT5)
        bi_127.append(abs(float(br_rig[REF]) - float(br_127[REF])) < 1e-12)
        bi_126.append(abs(float(br_rig[REF]) - float(np.asarray(r126["band_resid"])[REF])) < 1e-9)
    res["byte_identity_rigid_vs_127000_int_int"] = {"all_true": bool(all(bi_127)), "n_true": int(sum(bi_127)), "n": len(seeds)}
    res["byte_identity_rigid_vs_126000_full_cf"] = {"all_true": bool(all(bi_126)), "n_true": int(sum(bi_126)), "n": len(seeds)}
    _assert_engine("mid")

    # ---- THE HEADLINE: rigid vs affine_match vs oracle at block 8 ----
    res["arms"] = {
        "rigid": sweep_arm(arm_rigid, seeds, ROTS, paths),
        "affine_match": sweep_arm(arm_affine_match, seeds, ROTS, paths),
        "oracle": sweep_oracle(seeds, ROTS, paths),
    }

    # ---- BLOCK-SIZE ABLATION: rigid & affine_match at each block ----
    res["block_ablation"] = {}
    for blk in BLOCKS:
        res["block_ablation"][f"rigid_b{blk}"] = sweep_arm(arm_rigid, seeds, ROTS, paths, block=blk)
        res["block_ablation"][f"affine_b{blk}"] = sweep_arm(arm_affine_match, seeds, ROTS, paths, block=blk)
    _assert_engine("mid2")

    # ---- DIAGNOSTICS (read GROUND TRUTH t — validation/upper-bound, NOT sensor) ----
    res["diagnostics"] = {}
    for rot in ROTS:
        er = []; ea = []; dt = []; da = []; tt = []; uf = []
        for sd in seeds:
            sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
            e1, e2 = est_err_diag(sc); er.append(e1); ea.append(e2)
            d1, d2 = drift_from_truth_diag(sc); dt.append(d1); da.append(d2)
            _, _, diag = arm_affine_match(sc); tt.append(diag["tt_eigmin_med"]); uf.append(diag["used_affine"])
        res["diagnostics"][f"rot_{rot}"] = {
            "est_err_rigid": float(np.mean(er)), "est_err_affine": float(np.mean(ea)),
            "drift_translation": float(np.mean(dt)), "drift_affine": float(np.mean(da)),
            "tt_eigmin_med": float(np.median(tt)), "used_affine": float(np.mean(uf))}

    # ---- COMPUTE COST (DATA, not a verdict): per-frame time rigid vs affine ----
    sc0 = scene(seeds[0], DEPTHS, BASE, REF, rot=0.12, paths=paths)
    NREP = 20
    tr0 = time.time()
    for _ in range(NREP):
        arm_rigid(sc0)
    t_rigid = (time.time() - tr0) / NREP
    ta0 = time.time()
    for _ in range(NREP):
        arm_affine_match(sc0)
    t_affine = (time.time() - ta0) / NREP
    res["compute_cost"] = {"rigid_s_per_frame": t_rigid, "affine_s_per_frame": t_affine,
                           "ratio_affine_over_rigid": (t_affine / t_rigid if t_rigid > 0 else None),
                           "n_rep": NREP}

    # ---- ORACLE 0.5 BRACKET (pilot/burned only) ----
    if mode == "pilot":
        res["oracle_ext_burned"] = sweep_oracle(seeds, ROTS_ORACLE_EXT, paths)

    # ---- bounds ----
    res["bounds"] = {a: bound_of(res["arms"][a]) for a in res["arms"]}
    res["bounds_block"] = {k: bound_of(v) for k, v in res["block_ablation"].items()}

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
    print("byte-identity rigid==127000 int_int:", res["byte_identity_rigid_vs_127000_int_int"])
    print("byte-identity rigid==126000 full_cf:", res["byte_identity_rigid_vs_126000_full_cf"])
    print("\ndepth_order_rate  (rigid / affine_match / oracle) per rot:")
    for rot in ROTS:
        k = f"rot_{rot}"
        print(f"  rot={rot:.2f}: rigid={res['arms']['rigid'][k]['depth_order_rate']:.2f} "
              f"affine={res['arms']['affine_match'][k]['depth_order_rate']:.2f} "
              f"oracle={res['arms']['oracle'][k]['depth_order_rate']:.2f}")
    print("\nBOUNDS (last rot with rate>=0.5):", res["bounds"])
    print("block-size bounds:", res["bounds_block"])
    print("\nDIAGNOSTICS per rot (est_err rig/aff | drift trans/aff | tt_eigmin | used_aff):")
    for rot in ROTS:
        d = res["diagnostics"][f"rot_{rot}"]
        print(f"  rot={rot:.2f}: est {d['est_err_rigid']:.2f}/{d['est_err_affine']:.2f} | "
              f"drift {d['drift_translation']:.2f}/{d['drift_affine']:.2f} | "
              f"tt_eigmin {d['tt_eigmin_med']:.0f} | used_aff {d['used_affine']:.2f}")
    print("\nCOMPUTE COST:", res["compute_cost"])


if __name__ == "__main__":
    main()
