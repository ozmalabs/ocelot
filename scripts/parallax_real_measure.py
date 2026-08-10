"""parallax_real_measure — does the parallax carve survive REAL PHOTOMETRY?

Reproduces the parallax rung's carve (116000) EXACTLY, changing ONLY the pixel
source: synthetic Fourier texture (the re-earned floor) vs real BSDS300 crops
(the new variable). Same shifts [0,3,6], block 8, grid 144, ref_idx 1, same
efference-copy subtraction, same common-fate grouping, same τ (exact 0 AND
sensor √5), same speck-robust statistics (participation ratio + largest_frac).

Prints engine provenance FROM INSIDE the process and aborts on divergence
(§10). No wall-clock quantity is a verdict; loadavg recorded.

Usage:
  python scripts/parallax_real_measure.py pilot     # burned seeds 116000-116019
  python scripts/parallax_real_measure.py confirm    # fresh seeds 124000-124079
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_char import make_scene, group_common_fate, field_discontinuity, SQRT5
from parallax_real_char import make_real_scene, bsds_paths
from domains.motion_group_world import vector_field
from domains.engine_provenance import provenance_line, engine_preamble
engine_preamble()

EXPECT_ENGINE = "7041d2e6a7dd"
SHIFTS = [0, 3, 6]; BLOCK = 8; GRID = 144; REF = 1     # the parallax PRIMARY arm
CLIFF = 0.4        # rung 94000's measured block-std cliff (below one 8-bit step); a
                   # REPORTING split inherited from the sensor gate, NOT a verdict threshold.


def _assert_engine(tag):
    line = provenance_line()
    assert EXPECT_ENGINE in line, f"[{tag}] engine mismatch: {line}"
    return line


def eff_count(sizes):
    p = np.asarray(sizes, float); p = p / p.sum()
    return float(1.0 / np.sum(p * p))


def _ci(x):
    x = np.asarray(x, float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return [float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def carve_one(sc, tau):
    """The eye's carve on one scene: efference-copy subtraction + common-fate
    grouping of the SENSED field, at tolerance tau. Returns per-condition dicts."""
    delta = np.array([0.0, float(SHIFTS[REF])])
    rec = {}
    for cond, bk, tk in (("DEPTH", "b_depth", "t_depth"), ("FLAT", "b_flat", "t_flat")):
        V = vector_field(sc["a"], sc[bk], BLOCK)
        t = sc[tk]
        R_se = V - delta
        R_gt = t - delta
        lab, nl = group_common_fate(R_se, tau)
        sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
        refmask = (sc["owner"] == REF) if cond == "DEPTH" else np.ones_like(sc["owner"], bool)
        # sensor error classes vs ground truth (the antagonist), per cell
        gt_lab, gt_nl = group_common_fate(R_gt, tau)
        confab = float(np.mean(np.abs(V - t).sum(axis=-1) > 0))       # sensed != gt
        rec[cond] = dict(
            eff=eff_count(sizes), largest=sizes[0] / lab.size, count=nl,
            median=float(np.median(sizes)),
            top5=[s / lab.size for s in sizes[:5]] + [0.0] * max(0, 5 - len(sizes)),
            ref_resid_se=float(np.abs(R_se[refmask]).max()),
            ref_resid_gt=float(np.abs(R_gt[refmask]).max()),
            sensor_err_max=float(np.abs(V - t).max()),
            confab_rate=confab, disc_gt=field_discontinuity(R_gt),
            gt_eff=eff_count(sorted([(gt_lab == k).sum() for k in range(gt_nl)], reverse=True)),
        )
    return rec


def arm(kind, seeds, paths=None):
    """kind in {'synthetic','real','real_lowcon'}. Returns per-seed records + aggregates."""
    per = []
    for sd in seeds:
        rng = np.random.default_rng(sd)
        if kind == "synthetic":
            sc = make_scene(rng, SHIFTS, BLOCK, grid=GRID, ref_idx=REF)
            meta = {"min_band_std": None, "mean_block_std": None, "img": None}
        else:
            sel = "lowcon" if kind == "real_lowcon" else "random"
            sc = make_real_scene(rng, SHIFTS, BLOCK, GRID, REF, paths, select=sel)
            # STATIC-FRAME CONTROL: are the depth-band boundaries visible in `a`?
            # `a` is byte-identical DEPTH-vs-FLAT (shared crop), so any static
            # structure carves both equally; but the band boundaries sit at fixed
            # columns unrelated to image content, so they should carry no special
            # gradient. Report boundary-column gradient vs overall.
            a = sc["a"]; gx = np.abs(np.diff(a, axis=1))
            bcols = [sc["edges"][i] - 1 for i in range(1, sc["N"])]
            bnd = float(np.mean([gx[:, c] for c in bcols])); within = float(np.mean(gx))
            meta = {"min_band_std": sc["min_band_std"],
                    "mean_block_std": sc["mean_block_std"], "img": sc["img"],
                    "band_block_std": sc["band_block_std"].tolist(),
                    "bnd_grad": bnd, "within_grad": within}
        row = {"seed": sd, **meta}
        for tau, tn in ((0.0, "t0"), (SQRT5, "tsqrt5")):
            row[tn] = carve_one(sc, tau)
        per.append(row)
    agg = {}
    for tn in ("t0", "tsqrt5"):
        agg[tn] = {}
        for cond in ("DEPTH", "FLAT"):
            agg[tn][cond] = {
                "eff": _ci([r[tn][cond]["eff"] for r in per]),
                "largest": _ci([r[tn][cond]["largest"] for r in per]),
                "count": _ci([r[tn][cond]["count"] for r in per]),
                "median": _ci([r[tn][cond]["median"] for r in per]),
                "top5_mean": np.round(np.mean([r[tn][cond]["top5"] for r in per], 0), 4).tolist(),
                "confab_rate": _ci([r[tn][cond]["confab_rate"] for r in per]),
                "ref_resid_se_max": float(np.max([r[tn][cond]["ref_resid_se"] for r in per])),
                "disc_gt_mean": float(np.mean([r[tn][cond]["disc_gt"] for r in per])),
                "sensor_err_max": float(np.max([r[tn][cond]["sensor_err_max"] for r in per])),
            }
    if kind != "synthetic":
        agg["static_frame_control"] = {
            "band_boundary_grad_mean": float(np.mean([r["bnd_grad"] for r in per])),
            "within_frame_grad_mean": float(np.mean([r["within_grad"] for r in per])),
            "note": "a is byte-identical DEPTH-vs-FLAT; band boundaries at fixed cols "
                    "unrelated to image content carry no special gradient (ratio ~1).",
        }
    return {"per_seed": per, "agg": agg}


def cliff_analysis(real_per):
    """WHERE the carve degrades vs local contrast — tie to the rung-94000 cliff.
    Split real crops by whether ANY band's mean block std is below the cliff."""
    out = {}
    for tn in ("t0", "tsqrt5"):
        below = [r for r in real_per if r["min_band_std"] < CLIFF]
        above = [r for r in real_per if r["min_band_std"] >= CLIFF]
        def summ(rs):
            if not rs:
                return None
            eff = [r[tn]["DEPTH"]["eff"] for r in rs]
            lgst = [r[tn]["DEPTH"]["largest"] for r in rs]
            return {"n": len(rs), "eff": _ci(eff), "largest": _ci(lgst)}
        # correlation of DEPTH eff-error |eff-3| with min_band_std
        x = np.array([r["min_band_std"] for r in real_per])
        y = np.array([abs(r[tn]["DEPTH"]["eff"] - 3.0) for r in real_per])
        conf = np.array([r[tn]["DEPTH"]["confab_rate"] for r in real_per])
        r_effstd = float(np.corrcoef(x, y)[0, 1]) if len(x) > 2 else None
        r_confstd = float(np.corrcoef(x, conf)[0, 1]) if len(x) > 2 else None
        out[tn] = {"below_cliff": summ(below), "above_cliff": summ(above),
                   "n_below": len(below), "n_above": len(above),
                   "corr_effError_vs_minBandStd": r_effstd,
                   "corr_confabRate_vs_minBandStd": r_confstd,
                   "min_band_std_range": [float(x.min()), float(x.max())]}
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "confirm"
    if mode == "pilot":
        seeds = list(range(116000, 116020)); tag = "PILOT (burned seeds 116000-116019)"
        outname = "parallax_real_pilot.json"
    else:
        seeds = list(range(124000, 124080)); tag = "CONFIRM (fresh seeds 124000-124079)"
        outname = "parallax_real.json"

    t0 = time.time()
    prov = _assert_engine("start"); load0 = os.getloadavg()
    paths = bsds_paths()
    res = {"mode": mode, "tag": tag, "provenance": prov, "expect_engine": EXPECT_ENGINE,
           "seeds": [seeds[0], seeds[-1]], "n": len(seeds), "cliff": CLIFF,
           "n_bsds_train": len(paths), "loadavg_start": load0,
           "shifts": SHIFTS, "block": BLOCK, "grid": GRID, "ref_idx": REF}

    res["synthetic"] = arm("synthetic", seeds)
    _assert_engine("mid")
    res["real"] = arm("real", seeds, paths)
    res["real"]["cliff_analysis"] = cliff_analysis(res["real"]["per_seed"])
    # SECONDARY: adversarial low-contrast probe — hunt toward the <0.4 cliff.
    res["real_lowcon"] = arm("real_lowcon", seeds, paths)
    res["real_lowcon"]["cliff_analysis"] = cliff_analysis(res["real_lowcon"]["per_seed"])

    res["loadavg_end"] = os.getloadavg(); res["wall_s"] = time.time() - t0
    res["provenance_after"] = provenance_line()
    res["provenance_stable"] = (res["provenance_after"] == prov)
    _assert_engine("end")

    outp = os.path.join(_ROOT, "results", outname)
    with open(outp, "w") as f:
        json.dump(res, f, indent=1)
    print("WROTE", outp, "|", tag)
    print("provenance:", prov, "stable:", res["provenance_stable"])
    print("loadavg start/end:", load0, res["loadavg_end"], "wall_s:", round(res["wall_s"], 1))
    for src in ("synthetic", "real", "real_lowcon"):
        for tn in ("t0", "tsqrt5"):
            d = res[src]["agg"][tn]["DEPTH"]; f = res[src]["agg"][tn]["FLAT"]
            print(f"  {src:9s}/{tn:6s} DEPTH eff={d['eff'][0]:.2f}{d['eff'][1:3]} "
                  f"lgst={d['largest'][0]:.3f} top5={d['top5_mean']} "
                  f"confab={d['confab_rate'][0]:.3f} || FLAT eff={f['eff'][0]:.2f} "
                  f"lgst={f['largest'][0]:.3f} disc_gt={f['disc_gt_mean']:.2f} "
                  f"refres={d['ref_resid_se_max']:.1f} serr={d['sensor_err_max']:.0f}")
    for nm in ("real", "real_lowcon"):
        ca = res[nm]["cliff_analysis"]["tsqrt5"]
        below = ca["below_cliff"]
        print(f"  CLIFF {nm}(tsqrt5): n_below={ca['n_below']} n_above={ca['n_above']} "
              f"corr(effErr,minStd)={ca['corr_effError_vs_minBandStd']} "
              f"minStd_range={[round(v,2) for v in ca['min_band_std_range']]} "
              f"below_eff={(round(below['eff'][0],2) if below else None)}")


if __name__ == "__main__":
    main()
