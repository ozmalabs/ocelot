#!/usr/bin/env python3
"""HOLD THE PROPOSAL FIXED, VARY ONLY THE VERDICT — the pre-registered analysis.

Reads the per-trial rows written by `verdict_comparator_measure.py` and applies
the decision rule of `VISION_VERDICT_PREREG.md` mechanically.

THE THREE RULES THIS FILE EXISTS TO OBEY:

  1. THE TWO MECHANISMS ARE NEVER POOLED, AND NEITHER ARE THE CORPORA.
     `true_achieves_max` (misidentification -- a wrong region outright BEATS the
     true one) and the tie rate (the true region is among the winners and the
     tie is broken arbitrarily) are different quantities measuring different
     failures. `VISION_INVARIANT_COMPARATOR_RESULTS.md` section 2.5 measured the
     two corpora taking OPPOSITE SIGNS on the discrimination cost, so a pooled
     number is an average of two opposite effects.
  2. THE CUT CONFOUND IS STRATIFIED, NOT IGNORED.
     `VISION_SALIENCE_RESCORE_RESULTS.md` section 4: at short delta the failure
     unit is the FRAME, not the region -- all 31 of one arm's errors in 2 base
     frames of 50, all 16 regions failing at once, per-frame error tracking
     per-frame motion at r = +0.987. The primary misidentification claim is
     therefore made OFF CUT FRAMES, with the cut stratum reported beside it.
  3. THE TIE STATISTIC IS NOT COMPUTED BY THE SELECTOR UNDER TEST.
     It is `v0_region_ties` -- the number of REGIONS tied at the maximum under
     the INCUMBENT's score, computed outside the graph, identical for all four
     arms. The seed of this rung computes no tie statistic at all.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

VERDICTS = ("hamming", "ssdq", "ssdg", "ncc")
BASE = "hamming"
T975 = {9: 2.2622, 23: 2.0687, 49: 2.0096}


def t_ci(xs, df=None):
    n = len(xs)
    if n < 2:
        return (float(xs[0]) if xs else 0.0, 0.0, 0.0)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    t = T975.get(df if df is not None else n - 1, 1.984)
    h = t * sd / math.sqrt(n)
    return (m, m - h, m + h)


def per_unit(rows, unit, value):
    d = {}
    for r in rows:
        d.setdefault(r[unit], []).append(value(r))
    return {u: sum(v) / len(v) for u, v in d.items()}


def paired(rows_a, rows_b, unit, value, df):
    """Paired per-unit difference (arm - base) with a 95% t-CI."""
    a, b = per_unit(rows_a, unit, value), per_unit(rows_b, unit, value)
    us = sorted(set(a) & set(b))
    if not us:
        return None
    diffs = [a[u] - b[u] for u in us]
    m, lo, hi = t_ci(diffs, df)
    return {"n_units": len(us), "delta": m, "lo": lo, "hi": hi,
            "excludes_zero": bool(lo > 0.0 or hi < 0.0),
            "improves": bool(lo > 0.0),
            "arm": sum(a[u] for u in us) / len(us),
            "base": sum(b[u] for u in us) / len(us)}


def load(kind, verdict):
    p = os.path.join(ROOT, "results", f"verdict_rows_{kind}_{verdict}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def norm_entropy(names, k=16):
    if not names:
        return 0.0
    counts = {}
    for x in names:
        counts[x] = counts.get(x, 0) + 1
    n = len(names)
    h = -sum((c / n) * math.log(c / n) for c in counts.values() if c)
    return h / math.log(k)


def instrument(rows):
    """Gates that are about the INSTRUMENT, not the hypothesis."""
    a1 = [r for r in rows if r["kind"] == "A1"]
    scored = [r for r in rows if r["graph_max"] is not None]
    agree = sum(1 for r in scored
                if abs(float(r["graph_max"]) - float(r["ref_max"])) < 1e-6)
    return {
        "n_rows": len(rows),
        "score_agreement": agree / len(scored) if scored else 0.0,
        "argmax_agreement": (sum(1 for r in rows if r["said_idx"] == r["ref_idx"])
                             / len(rows) if rows else 0.0),
        "answer_entropy": norm_entropy([r["said"] for r in a1]),
        "mean_nflat": (sum(r["probe_nflat"] for r in rows) / len(rows)
                       if rows else 0.0),
        "all_final": bool(all(r["status"] == "vd_final" for r in rows)),
    }


def refusal(rows, df):
    """THE REFUSAL ARM. `G2c` DEFINED the floor, so it is excluded from the
    control -- the honest test is `G2t`, an independent draw from the same
    distribution, against `G1`, the identical frame, which must be answered.
    An arm that refuses everything or nothing is a DEAD INSTRUMENT."""
    out = {}
    for kind in ("G1", "A1", "A2", "A3", "G2t", "G2c"):
        sel = [r for r in rows if r["kind"] == kind]
        if not sel:
            continue
        out[kind] = {
            "n": len(sel),
            "refusal_rate": sum(1 for r in sel if r["refused"]) / len(sel),
        }
    a1 = [r for r in rows if r["kind"] == "A1"]
    ans = [r for r in a1 if not r["refused"]]
    out["A1_answer_rate"] = len(ans) / len(a1) if a1 else 0.0
    out["A1_acc_all"] = (sum(1 for r in a1 if r["said_idx"] == r["truth"])
                         / len(a1) if a1 else 0.0)
    out["A1_acc_on_answered"] = (sum(1 for r in ans if r["answer_idx"] == r["truth"])
                                 / len(ans) if ans else 0.0)
    g1 = [r for r in rows if r["kind"] == "G1"]
    g2t = [r for r in rows if r["kind"] == "G2t"]
    if g1 and g2t:
        unit = "base" if "base" in g1[0] else "photo"
        out["G2t_minus_G1"] = paired(g2t, g1, unit, lambda r: 1.0 if r["refused"] else 0.0, df)
        out["alive"] = bool(0.0 < out["A1"]["refusal_rate"] < 1.0
                            or 0.0 < out["G2t"]["refusal_rate"] < 1.0)
    return out


def analyse_video(res, cid, out):
    unit, df = "base", 49
    cut = res.get("cut", {}).get(cid, {})
    rowsets = {v: load(cid, v) for v in VERDICTS}
    if any(r is None for r in rowsets.values()):
        return
    deltas = sorted({int(r["tag"].split("|")[1][1:])
                     for r in rowsets[BASE] if r["kind"] == "A1"})
    cell = {}
    for v in VERDICTS:
        rows = rowsets[v]
        cell[v] = {"instrument": instrument(rows), "refusal": refusal(rows, df)}
    # MISID, per delta, split by cut
    misid = {}
    for d in deltas:
        for stratum in ("noncut", "cut", "all"):
            def sel(rows, d=d, stratum=stratum):
                o = []
                for r in rows:
                    if r["kind"] != "A1":
                        continue
                    if int(r["tag"].split("|")[1][1:]) != d:
                        continue
                    isc = cut.get(f"{r['base']}|{d}", False)
                    if stratum == "noncut" and isc:
                        continue
                    if stratum == "cut" and not isc:
                        continue
                    o.append(r)
                return o
            base_rows = sel(rowsets[BASE])
            entry = {"n_trials": len(base_rows)}
            for v in VERDICTS:
                rv = sel(rowsets[v])
                if not rv:
                    continue
                entry[v] = {
                    "true_achieves_max": sum(1 for r in rv if r["true_is_max"]) / len(rv),
                    "acc": sum(1 for r in rv if r["said_idx"] == r["truth"]) / len(rv),
                }
                if v != BASE and base_rows:
                    entry[v]["vs_base_tam"] = paired(
                        rv, base_rows, unit, lambda r: 1.0 if r["true_is_max"] else 0.0, df)
                    entry[v]["vs_base_acc"] = paired(
                        rv, base_rows, unit,
                        lambda r: 1.0 if r["said_idx"] == r["truth"] else 0.0, df)
            misid[f"d{d}|{stratum}"] = entry
    out["video"][cid] = {"cells": cell, "misid": misid,
                         "motion": {k: val for k, val in
                                    res.get("motion", {}).get(cid, {}).items()
                                    if k != "step"},
                         "n_cut_trials": sum(1 for k, val in cut.items() if val),
                         "n_trials_total": len(cut)}


def analyse_c3(res, out):
    unit, df = "photo", 23
    rowsets = {v: load("C3", v) for v in VERDICTS}
    if any(r is None for r in rowsets.values()):
        return
    cell = {v: {"instrument": instrument(rowsets[v]),
                "refusal": refusal(rowsets[v], df)} for v in VERDICTS}
    tie = {}
    for d in (0, 1, 2):
        for subset in ("v0tied", "v0untied", "all"):
            def sel(rows, d=d, subset=subset):
                o = []
                for r in rows:
                    if r["kind"] != "A1":
                        continue
                    if int(r["tag"].split("|")[1][1:]) != d:
                        continue
                    if subset == "v0tied" and r["v0_region_ties"] < 2:
                        continue
                    if subset == "v0untied" and r["v0_region_ties"] >= 2:
                        continue
                    o.append(r)
                return o
            base_rows = sel(rowsets[BASE])
            entry = {"n_trials": len(base_rows)}
            for v in VERDICTS:
                rv = sel(rowsets[v])
                if not rv:
                    continue
                entry[v] = {
                    "acc": sum(1 for r in rv if r["said_idx"] == r["truth"]) / len(rv),
                    "true_achieves_max": sum(1 for r in rv if r["true_is_max"]) / len(rv),
                    "mean_own_ties": sum(r["ref_region_ties"] for r in rv) / len(rv),
                    "frac_own_tied": sum(1 for r in rv if r["ref_region_ties"] > 1) / len(rv),
                }
                if v != BASE and base_rows:
                    entry[v]["vs_base_acc"] = paired(
                        rv, base_rows, unit,
                        lambda r: 1.0 if r["said_idx"] == r["truth"] else 0.0, df)
            tie[f"d{d}|{subset}"] = entry
    out["c3"] = {"cells": cell, "tie": tie}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "video"
    res_path = os.path.join(ROOT, "results", f"verdict_comparator_{src}.json")
    with open(res_path) as fh:
        res = json.load(fh)
    out = {"source": res_path, "provenance": res.get("provenance"),
           "proposal_identical": res.get("proposal_identical"),
           "video": {}, "c3": {}}
    # Analyse ONLY the corpora THIS results file actually measured. Row files
    # are written per corpus as each arm finishes, so a concurrent run can leave
    # rows on disk for a corpus whose motion/cut map is not in this file -- and
    # analysing those would silently mix two runs.
    for cid in ("C1", "C2"):
        if cid in res.get("cut", {}) and load(cid, BASE):
            analyse_video(res, cid, out)
    if "C3" in res.get("corpora", {}) and load("C3", BASE):
        analyse_c3(res, out)
    path = os.path.join(ROOT, "results", f"verdict_analysis_{src}.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1)[:12000])
    print(f"[done] wrote {path}")


if __name__ == "__main__":
    main()
