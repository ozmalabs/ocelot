"""SCALE THE EYE'S RESOLUTION — the pre-registered decision rule, applied.

`VISION_RESOLUTION_SCALE_PREREG.md` section 3, committed at `1fa4fe6d` before
any headline. This script DECIDES nothing that was not fixed in advance: the
primary is `true_is_max`, the effective-n rule is "n_eff rises along the SCALE
axis on BOTH corpora or the statistical motivation is refuted", and the grain
axis is where the degrade verdict is binding.

Every published value is printed from here rather than re-typed from a log.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

CONFIGS = ["B", "S48", "S72", "G48", "G72"]
SCALE_AXIS = ["B", "S48", "S72"]
GRAIN_AXIS = ["B", "G48", "G72"]
BLOCK = 10
T975 = {4: 2.7764, 9: 2.2622, 49: 2.0096}


def t_ci(xs, df=None):
    a = np.asarray(list(xs), float)
    n = len(a)
    if n < 2:
        return float(a[0]) if n else float("nan"), float("nan"), float("nan")
    m = float(a.mean())
    se = float(a.std(ddof=1) / np.sqrt(n))
    t = T975.get(df if df is not None else n - 1, 2.0096)
    return m, m - t * se, m + t * se


def icc_decompose(per_frame, block_of, m=BLOCK):
    """One-way random-effects decomposition. Returns ICC, n_eff, and the
    K-scope 'spread ratio' -- the observed variance of block means over what
    independent frames of the same within-block variance would produce."""
    blocks = sorted(set(block_of))
    k = len(blocks)
    n = len(per_frame)
    groups = [np.asarray([v for v, b in zip(per_frame, block_of) if b == g], float)
              for g in blocks]
    gm = np.asarray([g.mean() for g in groups], float)
    grand = float(np.mean(per_frame))
    msb = float(m * np.sum((gm - grand) ** 2) / (k - 1)) if k > 1 else float("nan")
    within = float(np.sum([np.sum((g - g.mean()) ** 2) for g in groups]))
    dfw = sum(len(g) - 1 for g in groups)
    msw = within / dfw if dfw > 0 else float("nan")
    if not np.isfinite(msb) or not np.isfinite(msw) or (msb + (m - 1) * msw) == 0:
        icc = float("nan")
    else:
        icc = (msb - msw) / (msb + (m - 1) * msw)
    n_eff = n / (1.0 + (m - 1) * icc) if np.isfinite(icc) and (1 + (m - 1) * icc) > 0 else float("nan")
    # spread ratio: var(block means) vs msw/m (the independent-frames null)
    var_gm = float(np.var(gm, ddof=1)) if k > 1 else float("nan")
    null = msw / m if np.isfinite(msw) and msw > 0 else float("nan")
    ratio = var_gm / null if np.isfinite(null) and null > 0 else float("inf")
    return {"icc": icc, "n_eff": n_eff, "k_blocks": k, "n": n,
            "msb": msb, "msw": msw, "var_block_means": var_gm,
            "spread_ratio": ratio, "block_means": [float(x) for x in gm]}


def per_frame_primary(rows, kind="A1", tagpat="A1|d1", noncut=True):
    """PRIMARY: the per-frame mean of `true_is_max` over that frame's regions,
    on the named probe. Parser-independent (prereg 2.4)."""
    by = {}
    for r in rows:
        if r["kind"] != kind:
            continue
        if tagpat and not r["tag"].startswith(tagpat):
            continue
        if noncut and r.get("cut"):
            continue
        by.setdefault(r["base"], []).append(float(r["true_is_max"]))
    frames = sorted(by)
    return frames, [float(np.mean(by[t])) for t in frames]


def per_frame_acc(rows, tagpat="A1|d1", noncut=True):
    by = {}
    for r in rows:
        if not r["tag"].startswith(tagpat):
            continue
        if noncut and r.get("cut"):
            continue
        by.setdefault(r["base"], []).append(
            1.0 if r["answer_idx"] == r["truth"] else 0.0)
    frames = sorted(by)
    return frames, [float(np.mean(by[t])) for t in frames]


def rate(rows, kind, field):
    v = [float(r[field]) for r in rows if r["kind"] == kind]
    return float(np.mean(v)) if v else float("nan")


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "all"
    meta = json.load(open(os.path.join(RES, f"resolution_scale_{tag}.json")))
    out = {"prereg": "VISION_RESOLUTION_SCALE_PREREG.md",
           "prereg_commit": meta.get("prereg_commit"),
           "provenance": meta.get("provenance"), "cells": {}, "gates": {}}

    print("=" * 78)
    print("G1 — THE PIPELINE RUNS.  graph/reference agreement must be 1.0000")
    print("=" * 78)
    g1 = {}
    for cid in ("C1", "C2"):
        for cfg in CONFIGS:
            p = os.path.join(RES, f"resscale_rows_{cid}_{cfg}.json")
            if not os.path.exists(p):
                continue
            rows = json.load(open(p))
            agree = float(np.mean([r["said_idx"] == r["ref_idx"] for r in rows]))
            g1[f"{cid}|{cfg}"] = agree
            print(f"  {cid} {cfg:4s}  agreement {agree:.4f}  n_rows {len(rows)}")
    out["gates"]["G1_agreement"] = g1
    out["gates"]["G1_pass"] = bool(all(abs(v - 1.0) < 1e-12 for v in g1.values()))
    print(f"  G1: {'PASS' if out['gates']['G1_pass'] else 'FAIL'}")

    print()
    print("=" * 78)
    print("PRIMARY — true_achieves_max, A1|d1, NON-CUT.  per corpus, never pooled")
    print("=" * 78)
    prim = {}
    for cid in ("C1", "C2"):
        print(f"\n  --- {cid} ---")
        print(f"  {'cfg':5s} {'nreg':>5s} {'cells':>6s} {'chance':>7s} "
              f"{'primary':>8s} {'lo':>8s} {'hi':>8s} {'above-chance':>13s} "
              f"{'acc':>7s} {'n_fr':>5s}")
        for cfg in CONFIGS:
            p = os.path.join(RES, f"resscale_rows_{cid}_{cfg}.json")
            if not os.path.exists(p):
                continue
            rows = json.load(open(p))
            cell = meta["cells"][f"{cid}|{cfg}"]
            fr, vals = per_frame_primary(rows)
            m, lo, hi = t_ci(vals)
            _fa, accv = per_frame_acc(rows)
            am = float(np.mean(accv)) if accv else float("nan")
            ch = cell["chance"]
            corr = (m - ch) / (1.0 - ch)
            prim[f"{cid}|{cfg}"] = {
                "primary": m, "lo": lo, "hi": hi, "n_frames": len(fr),
                "chance": ch, "chance_corrected": corr, "accuracy": am,
                "per_frame": vals, "frames": fr,
                "n_regions": cell["n_regions"],
                "cells_per_region": cell["cells_per_region"]}
            print(f"  {cfg:5s} {cell['n_regions']:5d} "
                  f"{cell['cells_per_region']:6d} {ch:7.4f} "
                  f"{m:8.4f} {lo:8.4f} {hi:8.4f} {corr:13.4f} "
                  f"{am:7.4f} {len(fr):5d}")
    out["cells"] = prim

    print()
    print("=" * 78)
    print("G2 — THE EFFECTIVE-N GATE (the primary).  n_eff = n / (1 + (m-1)ICC)")
    print("=" * 78)
    eff = {}
    for cid in ("C1", "C2"):
        print(f"\n  --- {cid} ---")
        print(f"  {'cfg':5s} {'nreg':>5s} {'ICC':>8s} {'n_eff':>7s} "
              f"{'spread_ratio':>13s} {'sd':>8s} {'@ceil':>7s}"
              "   (K-scope: 20.3x C1 / 8.4x C2)")
        for cfg in CONFIGS:
            p = os.path.join(RES, f"resscale_rows_{cid}_{cfg}.json")
            if not os.path.exists(p):
                continue
            rows = json.load(open(p))
            fr, vals = per_frame_primary(rows)
            blk = [t // BLOCK for t in fr]
            d = icc_decompose(vals, blk)
            # SATURATION DIAGNOSTIC (added in analysis, and it does NOT touch
            # the pre-registered decision rule). If a configuration sits on its
            # ceiling its per-frame variance is ~0, ICC is undefined-or-noise,
            # and its n_eff is NOT a statement about independence. Without this
            # column a ceiling artifact would be indistinguishable from a real
            # independence gain, which is exactly what G2 claims to measure.
            d["sd"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else float("nan")
            d["frac_at_ceiling"] = float(np.mean([v >= 1.0 - 1e-12 for v in vals]))
            d["saturated"] = bool(d["sd"] < 1e-6 or d["frac_at_ceiling"] > 0.95)
            eff[f"{cid}|{cfg}"] = d
            flag = "  <-- SATURATED: n_eff NOT interpretable" if d["saturated"] else ""
            print(f"  {cfg:5s} {meta['cells'][f'{cid}|{cfg}']['n_regions']:5d} "
                  f"{d['icc']:8.4f} {d['n_eff']:7.2f} {d['spread_ratio']:13.2f} "
                  f"{d['sd']:8.4f} {d['frac_at_ceiling']:7.3f}{flag}")
    out["gates"]["G2_effective_n"] = eff

    # THE DECISION RULE, FIXED IN ADVANCE (prereg 3, G2)
    verdicts = {}
    for cid in ("C1", "C2"):
        seq = [eff.get(f"{cid}|{c}", {}).get("n_eff") for c in SCALE_AXIS]
        if any(v is None or not np.isfinite(v) for v in seq):
            verdicts[cid] = None
            continue
        verdicts[cid] = bool(seq[0] < seq[1] < seq[2])
    out["gates"]["G2_rises_per_corpus"] = verdicts
    supported = bool(all(v is True for v in verdicts.values()))
    out["gates"]["G2_supported"] = supported
    print(f"\n  SCALE-axis n_eff monotone rise:  "
          + "  ".join(f"{c}={verdicts[c]}" for c in ("C1", "C2")))
    print(f"  G2 (as pre-registered): statistical motivation "
          f"{'SUPPORTED' if supported else 'REFUTED'}")

    # The verdict is reported as the rule says, AND the caveat that could make
    # it uninterpretable is reported beside it rather than folded into it.
    sat = {k: v for k, v in eff.items() if v.get("saturated")}
    out["gates"]["G2_saturated_configs"] = sorted(sat)
    if sat:
        print(f"\n  !! SATURATION CAVEAT — these configurations sit on the "
              f"ceiling: {', '.join(sorted(sat))}")
        print("     Their per-frame variance is ~0, so their ICC is "
              "undefined-or-noise and their n_eff is NOT a statement about")
        print("     independence. Where the SCALE-axis comparison rests on a "
              "saturated configuration, the G2 verdict above is a CEILING")
        print("     ARTIFACT and must not be read as evidence either way. "
              "The pre-registered rule is left exactly as written.")
        scale_sat = [c for c in SCALE_AXIS
                     if any(k.endswith(f"|{c}") and eff[k].get("saturated")
                            for k in eff)]
        out["gates"]["G2_scale_axis_saturated"] = scale_sat
        if scale_sat:
            print(f"     Affected on the SCALE axis: {scale_sat}")

    print()
    print("=" * 78)
    print("THE MECHANISM — REGION-LEVEL INDEPENDENCE (cluster = the FRAME)")
    print("  The motivating hypothesis is about REGIONS, so it is tested at the")
    print("  region level: does adding regions add INDEPENDENT samples, or more")
    print("  samples that share their frame's content?")
    print("=" * 78)
    reg = {}
    for cid in ("C1", "C2"):
        print(f"\n  --- {cid} ---")
        print(f"  {'cfg':5s} {'reg/fr':>7s} {'N_obs':>7s} {'ICC_region':>11s} "
              f"{'n_eff_total':>12s} {'n_eff PER FRAME':>16s}")
        for cfg in CONFIGS:
            p = os.path.join(RES, f"resscale_rows_{cid}_{cfg}.json")
            if not os.path.exists(p):
                continue
            rows = json.load(open(p))
            a = [r for r in rows if r["kind"] == "A1"
                 and r["tag"].startswith("A1|d1") and not r.get("cut")]
            byf = {}
            for r in a:
                byf.setdefault(r["base"], []).append(float(r["true_is_max"]))
            gs = [np.asarray(v, float) for v in byf.values()]
            if len(gs) < 2:
                continue
            m = float(np.mean([len(g) for g in gs]))
            k = len(gs)
            N = int(sum(len(g) for g in gs))
            grand = float(np.mean(np.concatenate(gs)))
            msb = float(sum(len(g) * (g.mean() - grand) ** 2 for g in gs) / (k - 1))
            dfw = sum(len(g) - 1 for g in gs)
            msw = float(sum(((g - g.mean()) ** 2).sum() for g in gs) / dfw) if dfw else float("nan")
            den = msb + (m - 1) * msw
            icc = (msb - msw) / den if den > 0 else float("nan")
            neff = N / (1 + (m - 1) * icc) if np.isfinite(icc) and (1 + (m - 1) * icc) > 0 else float("nan")
            reg[f"{cid}|{cfg}"] = {"m_regions_per_frame": m, "N_obs": N,
                                   "icc_region": icc, "n_eff_total": neff,
                                   "n_eff_per_frame": neff / k if np.isfinite(neff) else float("nan")}
            print(f"  {cfg:5s} {m:7.0f} {N:7d} {icc:11.4f} {neff:12.1f} "
                  f"{(neff / k if np.isfinite(neff) else float('nan')):16.2f}")
    out["gates"]["region_level"] = reg

    print()
    print("=" * 78)
    print("G3 — RECOGNITION vs the RE-EARNED B BASELINE")
    print("  GRAIN axis: n_regions fixed at 16 -> raw is comparable, BINDING")
    print("  SCALE axis: candidate set grows -> raw NOT apples-to-apples")
    print("=" * 78)
    g3 = {}
    for cid in ("C1", "C2"):
        base = prim.get(f"{cid}|B")
        if not base:
            continue
        print(f"\n  --- {cid} ---   B = {base['primary']:.4f}")
        for axis, cfgs in (("GRAIN (binding)", GRAIN_AXIS),
                           ("SCALE (not apples-to-apples)", SCALE_AXIS)):
            print(f"   {axis}")
            for cfg in cfgs[1:]:
                c = prim.get(f"{cid}|{cfg}")
                if not c:
                    continue
                # paired by frame where both exist
                common = sorted(set(base["frames"]) & set(c["frames"]))
                bi = {t: v for t, v in zip(base["frames"], base["per_frame"])}
                ci = {t: v for t, v in zip(c["frames"], c["per_frame"])}
                dl = [ci[t] - bi[t] for t in common]
                dm, dlo, dhi = t_ci(dl)
                g3[f"{cid}|{cfg}"] = {"delta": dm, "lo": dlo, "hi": dhi,
                                      "n_paired": len(common),
                                      "axis": "grain" if cfg in GRAIN_AXIS else "scale"}
                flag = "DEGRADES" if dhi < 0 else ("no degrade" if dlo > 0 else "not separated")
                print(f"    {cfg:5s} {c['primary']:.4f}  paired delta "
                      f"{dm:+.4f} [{dlo:+.4f}, {dhi:+.4f}]  n={len(common)}  {flag}")
    out["gates"]["G3_paired"] = g3

    print()
    print("=" * 78)
    print("REFUSAL — floor RE-MEASURED at every configuration, never inherited")
    print("=" * 78)
    ref = {}
    for cid in ("C1", "C2"):
        print(f"\n  --- {cid} ---")
        print(f"  {'cfg':5s} {'floor':>9s} {'G2t refuse':>11s} "
              f"{'A1 refuse':>10s} {'A3 refuse':>10s} {'nflat':>7s}")
        for cfg in CONFIGS:
            p = os.path.join(RES, f"resscale_rows_{cid}_{cfg}.json")
            if not os.path.exists(p):
                continue
            rows = json.load(open(p))
            fl = [r["noise_floor"] for r in rows if r["noise_floor"] is not None]
            d = {"floor": float(np.mean(fl)) if fl else float("nan"),
                 "g2t_refuse": rate(rows, "G2t", "refused"),
                 "a1_refuse": rate(rows, "A1", "refused"),
                 "a3_refuse": rate(rows, "A3", "refused"),
                 "nflat": float(np.mean([r["probe_nflat"] for r in rows]))}
            ref[f"{cid}|{cfg}"] = d
            print(f"  {cfg:5s} {d['floor']:9.4f} {d['g2t_refuse']:11.4f} "
                  f"{d['a1_refuse']:10.4f} {d['a3_refuse']:10.4f} "
                  f"{d['nflat']:7.4f}")
    out["gates"]["refusal"] = ref

    print()
    print("=" * 78)
    print("G4 — COST PER CONFIGURATION.  counted quantity is load-independent")
    print("=" * 78)
    cost = {}
    for cid in ("C1", "C2"):
        print(f"\n  --- {cid} ---")
        print(f"  {'cfg':5s} {'nreg':>5s} {'cells':>6s} {'cellcmp/probe':>14s} "
              f"{'graph ms/fr':>12s} {'x B':>7s} {'ref-read s':>11s} {'load':>6s}")
        for cfg in CONFIGS:
            k = f"{cid}|{cfg}"
            if k not in meta["cells"]:
                continue
            c = meta["cells"][k]
            b = meta["cells"].get(f"{cid}|B", c)
            xb = c["graph_run_ms_mean"] / b["graph_run_ms_mean"] if b["graph_run_ms_mean"] else float("nan")
            cost[k] = {"n_regions": c["n_regions"],
                       "cells_per_region": c["cells_per_region"],
                       "cell_comparisons_per_probe": c["cell_comparisons_per_probe"],
                       "graph_run_ms_mean": c["graph_run_ms_mean"],
                       "graph_x_baseline": xb,
                       "ref_read_s_total": c["ref_read_s_total"],
                       "wall_s": c["wall_s"], "loadavg": c["loadavg"]}
            print(f"  {cfg:5s} {c['n_regions']:5d} {c['cells_per_region']:6d} "
                  f"{c['cell_comparisons_per_probe']:14d} "
                  f"{c['graph_run_ms_mean']:12.1f} {xb:7.1f} "
                  f"{c['ref_read_s_total']:11.1f} {c['loadavg'][0]:6.2f}")
    out["gates"]["G4_cost"] = cost

    op = os.path.join(RES, f"resolution_scale_analysis_{tag}.json")
    with open(op, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"\n[done] wrote {op}")


if __name__ == "__main__":
    main()
