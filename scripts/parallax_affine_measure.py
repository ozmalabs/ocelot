"""parallax_affine_measure — CONFIRMATORY measurement for rung 126000.

Do AFFINE-FLOW grouping and/or FULL-FIELD efference RESCUE 125000's rotation
FALSIFY? Runs ONLY the arms in VISION_PARALLAX_AFFINE_PREREG.md on FRESH seeds
126000-126079 (2x2 ablation × Stage A / rotation sweep / slant sweep + the
post-hoc diagnostic). Prints engine provenance FROM INSIDE the process and
aborts on divergence (§10). No wall-clock quantity is a verdict; loadavg recorded.

  python scripts/parallax_affine_measure.py pilot     # burned 116000-116029
  python scripts/parallax_affine_measure.py confirm    # fresh 126000-126079
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_affine_char import (scene, carve_single, carve_full, COMMON_FATE, AFFINE,
                                  efference_field, vector_field_eff, eff_count,
                                  BLOCK, GRID)
from parallax_char import group_common_fate, SQRT5
from parallax_motion_char import carve as carve125, STAGE_A_BASE, STAGE_A_DEPTHS
from parallax_real_char import bsds_paths
from domains.motion_group_world import vector_field
from domains.engine_provenance import provenance_line, engine_preamble, engine_provenance
engine_preamble()

DEPTHS, BASE, REF = STAGE_A_DEPTHS, STAGE_A_BASE, 1
Z0_SLANT = 7.5
ROTS = [0.0, 0.02, 0.04, 0.08, 0.12, 0.16]
TILTS = [0.0, 0.4, 0.6, 0.8]
CARVES = {"single": carve_single, "full": carve_full}
GROUPERS = {"cf": COMMON_FATE, "affine": AFFINE}


def _assert_engine(tag):
    line = provenance_line(); p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), f"[{tag}] source_match={p['source_match']}: {line}"
    return line


def _ci(x):
    x = np.asarray(x, float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return [float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def twobytwo(scene_fn, seeds, tau=SQRT5):
    """Return {arm: {eff CI, depth_order rate, rho mean, ref_resid max}} for the
    four arms efference×grouping."""
    acc = {f"{e}_{g}": {"eff": [], "dok": [], "rho": [], "ref": []}
           for e in CARVES for g in GROUPERS}
    for sd in seeds:
        sc = scene_fn(sd)
        for en, cf in CARVES.items():
            for gn, grp in GROUPERS.items():
                r = cf(sc, tau, grp)
                a = acc[f"{en}_{gn}"]
                a["eff"].append(r["eff"]); a["dok"].append(1.0 if r["depth_order_correct"] else 0.0)
                a["rho"].append(r["depth_rank_rho"]); a["ref"].append(r["ref_resid_se"])
    out = {}
    for k, a in acc.items():
        out[k] = {"eff": _ci(a["eff"]), "depth_order_rate": float(np.mean(a["dok"])),
                  "rho_mean": float(np.mean(a["rho"])), "ref_resid_max": float(np.max(a["ref"]))}
    return out


def carve_full_posthoc(sc, tau, grouper=COMMON_FATE):
    """DIAGNOSTIC: full predicted field subtracted POST-HOC (V - field), NOT as a
    search-centre remap — shows whether the field's VALUE or its APPLICATION is
    what rescues rotation."""
    V = vector_field(sc["a"], sc["b"], sc["block"])
    ex = efference_field(sc, True)
    R = V.copy(); R[..., 1] = R[..., 1] - ex[None, :]
    lab, nl = grouper(R, tau)
    depths = np.asarray(sc["depths"], float)
    band_resid = np.array([float(R[sc["owner"] == i][..., 1].mean())
                           if (sc["owner"] == i).any() else np.nan for i in range(sc["N"])])
    inv_Z = 1.0 / depths
    dok = list(np.argsort(-band_resid)) == list(np.argsort(-inv_Z))
    sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
    return eff_count(sizes), dok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "confirm"
    if mode == "pilot":
        seeds = list(range(116000, 116030)); outname = "parallax_affine_pilot.json"
    else:
        seeds = list(range(126000, 126080)); outname = "parallax_affine.json"

    t0 = time.time(); prov = _assert_engine("start"); load0 = os.getloadavg()
    paths = bsds_paths()
    res = {"mode": mode, "provenance": prov, "seeds": [seeds[0], seeds[-1]], "n": len(seeds),
           "depths": DEPTHS, "base": BASE, "ref_idx": REF, "block": BLOCK, "grid": GRID,
           "rots": ROTS, "tilts": TILTS, "loadavg_start": load0, "sqrt5": SQRT5}

    A = lambda sd: scene(sd, DEPTHS, BASE, REF, paths=paths)

    # ---- BYTE-IDENTITY: (single,cf) == 125000 carve; affine==cf on residual ----
    bi125, biaf = [], []
    for sd in seeds:
        sc = A(sd)
        r_new = carve_single(sc, SQRT5, COMMON_FATE); r_125 = carve125(sc, SQRT5)
        bi125.append(abs(r_new["eff"] - r_125["eff"]) < 1e-12
                     and r_new["depth_order_correct"] == r_125["depth_order_correct"])
        V = vector_field(sc["a"], sc["b"], sc["block"])
        R = V - np.array([0.0, float(int(round(BASE / DEPTHS[REF])))])
        lcf, _ = group_common_fate(R, SQRT5); laf, _ = AFFINE(R, SQRT5)
        biaf.append(bool(np.array_equal(lcf, laf)))
    res["byte_identity_single_cf_vs_125000"] = {"all_true": bool(all(bi125)), "n_true": int(sum(bi125)), "n": len(seeds)}
    res["byte_identity_affine_vs_cf_stageA"] = {"n_true": int(sum(biaf)), "n": len(seeds)}

    _assert_engine("mid")

    # ---- STAGE A (translation) 2x2 ----
    res["stageA_2x2"] = twobytwo(A, seeds)

    # ---- STAGE B rotation 2x2 sweep ----
    res["stageB_rot_2x2"] = {}
    for rot in ROTS:
        res["stageB_rot_2x2"][f"rot_{rot}"] = twobytwo(
            lambda sd, rt=rot: scene(sd, DEPTHS, BASE, REF, rot=rt, paths=paths), seeds)

    # ---- STAGE B slant 2x2 sweep (single full-frame plane) ----
    res["stageB_slant_2x2"] = {}
    for tilt in TILTS:
        res["stageB_slant_2x2"][f"tilt_{tilt}"] = twobytwo(
            lambda sd, tl=tilt: scene(sd, [Z0_SLANT], BASE, 0, tilt=tl, tilt_bands=(0,), paths=paths), seeds)

    _assert_engine("mid2")

    # ---- DIAGNOSTIC: full-field POST-HOC (not search-centre) on rotation ----
    res["diag_full_posthoc_rot"] = {}
    for rot in [0.02, 0.04, 0.08]:
        dok = []
        for sd in seeds:
            sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
            dok.append(1.0 if carve_full_posthoc(sc, SQRT5)[1] else 0.0)
        res["diag_full_posthoc_rot"][f"rot_{rot}"] = float(np.mean(dok))

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
    print("byte-identity (single,cf)==125000:", res["byte_identity_single_cf_vs_125000"])
    print("byte-identity affine==cf StageA:", res["byte_identity_affine_vs_cf_stageA"])
    print("STAGE A 2x2 (eff / depth_order):")
    for k, v in res["stageA_2x2"].items():
        print(f"  {k:12s} eff={v['eff'][0]:.3f}{v['eff'][1:3]} depth_order={v['depth_order_rate']:.2f}")
    print("STAGE B rotation 2x2 (depth_order rate per arm):")
    print("  rot     single_cf single_af  full_cf  full_af   eff(full_cf)")
    for rot in ROTS:
        d = res["stageB_rot_2x2"][f"rot_{rot}"]
        print(f"  {rot:.2f}    {d['single_cf']['depth_order_rate']:.2f}      "
              f"{d['single_affine']['depth_order_rate']:.2f}       {d['full_cf']['depth_order_rate']:.2f}     "
              f"{d['full_affine']['depth_order_rate']:.2f}      {d['full_cf']['eff'][0]:.2f}")
    print("STAGE B slant 2x2 (eff per arm):")
    for tilt in TILTS:
        d = res["stageB_slant_2x2"][f"tilt_{tilt}"]
        print(f"  tilt={tilt}: single_cf={d['single_cf']['eff'][0]:.2f} single_af={d['single_affine']['eff'][0]:.2f} "
              f"full_cf={d['full_cf']['eff'][0]:.2f} full_af={d['full_affine']['eff'][0]:.2f}")
    print("DIAGNOSTIC full-field POST-HOC (depth_order — should FAIL, proving search-centre is the mechanism):")
    print(" ", res["diag_full_posthoc_rot"])


if __name__ == "__main__":
    main()
