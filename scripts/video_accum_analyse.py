"""VIDEO ACCUMULATION — the pre-registered decision rule, applied mechanically,
plus the two labelled POST-HOC checks (D1, D2).

Reads `results/video_accum.json`. Computes nothing the run did not already
record except the stratifications section 3.4/3.5 pre-registered and the two
diagnostics, which are labelled POST-HOC wherever they appear.
"""
from __future__ import annotations

import importlib.util as iu
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains import video_accumulation_world as aw  # noqa: E402


def ci95(xs):
    a = np.asarray([x for x in xs if x is not None], float)
    n = a.size
    if n < 2:
        return {"n": int(n), "mean": float(a.mean()) if n else None,
                "lo": None, "hi": None}
    from scipy import stats
    m, se = float(a.mean()), float(a.std(ddof=1) / np.sqrt(n))
    t = float(stats.t.ppf(0.975, n - 1))
    return {"n": int(n), "mean": m, "lo": m - t * se, "hi": m + t * se,
            "sd": float(a.std(ddof=1))}


def paired(xs, ys):
    return ci95([a - b for a, b in zip(xs, ys)])


def fmt(c):
    if c["lo"] is None:
        return f"n={c['n']} mean={c['mean']}"
    return (f"n={c['n']:3d} {c['mean']:+.4f} [{c['lo']:+.4f},{c['hi']:+.4f}]")


def main():
    print(ep.provenance_line())
    d = json.load(open(ROOT / "results/video_accum.json"))
    out = {"provenance": ep.provenance_line()}

    vpspec = iu.spec_from_file_location(
        "vp", str(HERE / "video_probe_measure.py"))
    vp = iu.module_from_spec(vpspec)
    vpspec.loader.exec_module(vp)

    for cid, R in d["corpora"].items():
        print("=" * 74)
        print(f"{cid}  K_final={R['K_final']}  cuts@{R['cut_steps']}")
        C = {}

        # ---- section 3.4 CUT STRATIFICATION, with CIs -----------------
        ent = R["entries"]
        near = [e for e in ent if e["near_cut"]]
        far = [e for e in ent if not e["near_cut"]]
        C["usage_near"] = ci95([float(e["usage"]) for e in near])
        C["usage_far"] = ci95([float(e["usage"]) for e in far])
        C["dead_near"] = ci95([e["dead"] for e in near])
        C["dead_far"] = ci95([e["dead"] for e in far])
        print(f"  usage near(W<=3) {fmt(C['usage_near'])}")
        print(f"  usage far        {fmt(C['usage_far'])}")
        print(f"  dead  near       {fmt(C['dead_near'])}")
        print(f"  dead  far        {fmt(C['dead_far'])}")
        C["usage_sep_far_above_near"] = bool(
            C["usage_far"]["lo"] is not None
            and C["usage_far"]["lo"] > C["usage_near"]["hi"])
        print(f"  far USED MORE than near, CI-separated: "
              f"{C['usage_sep_far_above_near']}")

        # continuous form -- no chosen window
        ds = np.asarray([e["dist_to_cut"] for e in ent], float)
        us = np.asarray([e["usage"] for e in ent], float)
        from scipy import stats
        r, _ = stats.pearsonr(ds, us)
        rs, _ = stats.spearmanr(ds, us)
        C["usage_vs_dist_pearson"] = float(r)
        C["usage_vs_dist_spearman"] = float(rs)
        print(f"  usage vs frames-to-cut: pearson r={r:+.4f} "
              f"spearman={rs:+.4f}  (continuous, no window)")
        C["n_dead_total"] = int(sum(e["dead"] for e in ent))
        print(f"  DEAD entries overall: {C['n_dead_total']}/{len(ent)}")

        # ---- section 3.6 refusal, BSDS separation quality -------------
        ref = R["refusal"]
        for k in ("BSDS", "NOISE", "SHUFFLE", "CONTROL"):
            print(f"  refusal {k:8s} {fmt(ref[k])}"
                  + ("  <-- ZERO VARIANCE (point interval)"
                     if ref[k].get("sd") == 0.0 else ""))
        C["refusal_control_zero_variance"] = bool(ref["CONTROL"].get("sd")
                                                  == 0.0)

        # ---- section 3.5 ORDER ----------------------------------------
        fin = R["checkpoints"][str(d["checkpoints"][-1])]["arms"]["GROWN"]
        sh = R["shuffled"]["eval"]
        C["order_is_max_shuffled_minus_inorder"] = paired(
            sh["max_rows"], fin["max_rows"])
        C["order_K"] = [R["K_final"], R["shuffled"]["K_final"]]
        print(f"  ORDER  K in-order={R['K_final']} shuffled="
              f"{R['shuffled']['K_final']}  is_max delta "
              f"{fmt(C['order_is_max_shuffled_minus_inorder'])}"
              f"   (NOT size-matched -- K differs)")

        # ---- D1 (POST-HOC): the identical-array smell -----------------
        cps = d["checkpoints"]
        same = []
        for a, b in zip(cps, cps[1:]):
            ga = R["checkpoints"].get(str(a), {}).get("arms", {}).get("GROWN")
            gb = R["checkpoints"].get(str(b), {}).get("arms", {}).get("GROWN")
            if ga and gb and ga["max_rows"] == gb["max_rows"]:
                same.append([a, b, ga["K"], gb["K"]])
        C["D1_identical_checkpoints_POSTHOC"] = same
        print(f"  D1 POST-HOC identical GROWN read-outs across "
              f"checkpoints: {same}")

        out[cid] = C

    # ---- D2 (POST-HOC): independent numpy re-derivation of C1's -------
    # cp65 == cp90 identity. NOT computed by the graph.
    R = d["corpora"]["C1"]
    frames, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=aw.GRID,
                                      episode_index=0)
    assert meta["episode_id"] == "08630d4b7b215c469df19b9c42d7b617"
    q = [aw.quantize(f) for f in frames]
    qr = [aw.regions_of(x) for x in q]
    gr = [aw.grey_regions_of(f) for f in frames]

    def uc(t, i):
        v, _ = aw.encode(qr[t][i], gr[t][i])["nvals"], None
        return np.asarray(v, float)

    mints = R["mints"]
    late = [m for m in mints if m["n_train"] > 65]
    early = [m for m in mints if m["n_train"] <= 65]
    E = np.stack([uc(m["frame"], m["region"]) for m in early])
    L = np.stack([uc(m["frame"], m["region"]) for m in late])
    heldv = np.stack([uc(t, i) for t in d["held"] for i in range(16)])
    be = (heldv @ E.T).max(axis=1)
    bl = (heldv @ np.vstack([E, L]).T).max(axis=1)
    n_improved = int((bl > be + 1e-12).sum())
    print("=" * 74)
    print(f"D2 POST-HOC (numpy, outside the graph): C1 late mints "
          f"n={len(late)}; held-out observations whose best NCC IMPROVES "
          f"when they are added: {n_improved}/{len(heldv)}; "
          f"max improvement={float((bl-be).max()):.3e}")
    out["D2_C1_late_mint_improves_POSTHOC"] = {
        "n_late": len(late), "n_improved": n_improved,
        "n_heldout_obs": int(len(heldv)),
        "max_improvement": float((bl - be).max()),
        "graph_mean_cp65": float(np.mean(
            R["checkpoints"]["65"]["arms"]["GROWN"]["max_rows"])),
        "numpy_mean_cp65": float(be.mean()),
        "numpy_mean_cp90": float(bl.mean())}
    print(f"   graph mean(is_max)@cp65 = "
          f"{out['D2_C1_late_mint_improves_POSTHOC']['graph_mean_cp65']:.6f}"
          f"  numpy = {be.mean():.6f}  (independent agreement check)")

    p = ROOT / "results/video_accum_analysis.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
