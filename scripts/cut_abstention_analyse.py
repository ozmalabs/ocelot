#!/usr/bin/env python3
"""GRAPH-RESIDENT ABSTENTION — the pre-registered decision rule, applied
mechanically.

`VISION_CUT_ABSTENTION_PREREG.md` §4. Reads the per-trial rows this rung wrote
and computes exactly the declared arms. It chooses nothing: every population,
statistic and comparison below is the one named in the pre-registration, and
anything computed here that was NOT pre-registered is printed under a
`post_hoc` key and is labelled as such in the results file.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/cut_abstention_analyse.py
"""
from __future__ import annotations

import collections
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DELTAS = (1, 5, 25)
ARMINGS = ("inert", "mag", "xcorr")
VERDICTS = ("ncc", "ssdg")
T975 = {49: 2.0096}


def t_ci(xs, df=49):
    n = len(xs)
    if n < 2:
        return (float(xs[0]) if xs else 0.0, 0.0, 0.0)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = T975.get(df, 1.984) * sd / math.sqrt(n)
    return (m, m - h, m + h)


def paired(per_base_a, per_base_b, bases):
    """Paired per-base-frame difference a - b, with a 95% t-CI. The UNIT IS THE
    BASE FRAME, never the trial -- the 16 regions of a frame share content and
    are not independent. Held identical to the incumbent's."""
    d = [per_base_a.get(t, 0.0) - per_base_b.get(t, 0.0) for t in bases]
    return t_ci(d)


def load(cid, verdict, armed):
    p = os.path.join(ROOT, "results", f"cut_rows_{cid}_{verdict}_{armed}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def delta_of(tag):
    # tag looks like "A1|d5|3"
    return int(tag.split("|")[1][1:])


def by_base(rows, pred, value):
    """Mean of `value` over the rows satisfying `pred`, grouped by base frame.
    Frames contributing no matching row are ABSENT rather than zero, so an
    empty stratum cannot masquerade as a measured zero."""
    num: dict = collections.defaultdict(float)
    den: dict = collections.defaultdict(int)
    for r in rows:
        if not pred(r):
            continue
        num[r["base"]] += float(value(r))
        den[r["base"]] += 1
    return {t: num[t] / den[t] for t in den if den[t]}, dict(den)


def main():
    meas = json.load(open(os.path.join(ROOT, "results",
                                       "cut_abstention_video.json")))
    out = {"provenance": meas["provenance"],
           "prereg": "VISION_CUT_ABSTENTION_PREREG.md",
           "note": ("Every arm below is the one declared in the "
                    "pre-registration. Keys under `post_hoc` were not."),
           "arms": {}, "post_hoc": {}, "instrument": {}}

    for cid in ("C1", "C2"):
        ref = meas["reference"].get(cid)
        if ref is None:
            continue
        step = ref["step"]
        numpy_cuts = set(ref["numpy_cut_steps"])
        # THE TOP MOTION DECILE AMONG NON-CUT STEPS -- arm 2a's population.
        noncut = sorted((x, t) for t, x in enumerate(step) if t not in numpy_cuts)
        k = max(1, len(noncut) // 10)
        hard_steps = {t for _x, t in noncut[-k:]}
        out["instrument"].setdefault(cid, {})["hard_steps"] = sorted(hard_steps)
        out["instrument"][cid]["hard_step_motion_range"] = [
            noncut[-k][0], noncut[-1][0]]
        out["instrument"][cid]["numpy_cut_steps"] = sorted(numpy_cuts)

        for verdict in VERDICTS:
            base_rows = load(cid, verdict, "inert")
            if base_rows is None:
                continue
            # `true_is_max` is a property of the COMPARATOR and must not move
            # with the arming. Checked, not assumed.
            for armed in ("mag", "xcorr"):
                arm_rows = load(cid, verdict, armed)
                if arm_rows is None:
                    continue
                same = all(a["true_is_max"] == b["true_is_max"]
                           and a["said"] == b["said"]
                           and a["graph_max"] == b["graph_max"]
                           for a, b in zip(base_rows, arm_rows))
                out["instrument"][cid][f"{verdict}|{armed}|comparator_unmoved"] = same

            # which spans the graph marked, per (base, delta), from the rows
            for armed in ("mag", "xcorr"):
                arm_rows = load(cid, verdict, armed)
                if arm_rows is None:
                    continue
                key = f"{cid}|{verdict}|{armed}"
                bases = sorted({r["base"] for r in base_rows})

                def a1(r, d=None):
                    return r["kind"] == "A1" and (d is None or delta_of(r["tag"]) == d)

                res: dict = {}

                # --- ARM 1: ABSTAINS ON CUTS ------------------------------ #
                # Population: A1 probes where the comparator is WRONG.
                # Ground truth is the comparator's REALISED ERROR, not the
                # motion label -- the rule must not be graded against its own
                # statistic.
                wrong = lambda r: a1(r) and not r["true_is_max"]          # noqa: E731
                b_wrong, n_wrong = by_base(base_rows, wrong, lambda r: r["refused"])
                a_wrong, _ = by_base(arm_rows, wrong, lambda r: r["refused"])
                res["arm1_recall_over_errors"] = {
                    "baseline": t_ci([b_wrong.get(t, 0.0) for t in b_wrong]),
                    "armed": t_ci([a_wrong.get(t, 0.0) for t in a_wrong]),
                    "paired_increment": paired(a_wrong, b_wrong, sorted(b_wrong)),
                    "n_base_frames": len(b_wrong),
                    "n_trials": sum(n_wrong.values())}
                for d in DELTAS:
                    wd = lambda r, d=d: a1(r, d) and not r["true_is_max"]  # noqa: E731
                    bw, nw = by_base(base_rows, wd, lambda r: r["refused"])
                    aw, _ = by_base(arm_rows, wd, lambda r: r["refused"])
                    res[f"arm1_d{d}"] = {
                        "baseline": t_ci([bw.get(t, 0.0) for t in bw]),
                        "armed": t_ci([aw.get(t, 0.0) for t in aw]),
                        "paired_increment": paired(aw, bw, sorted(bw)),
                        "n_base_frames": len(bw), "n_trials": sum(nw.values())}

                # ARM 1 HEADLINE, PARAMETER-FREE: the (base, delta) cells in
                # which ALL 16 REGIONS FAILED AT ONCE -- the salience rung's
                # own criterion for the frame-level failure, which needs no
                # threshold to state.
                cells = collections.defaultdict(list)
                for r in base_rows:
                    if r["kind"] == "A1":
                        cells[(r["base"], delta_of(r["tag"]))].append(r)
                catastrophic = {c for c, rs in cells.items()
                                if len(rs) == 16 and not any(x["true_is_max"] for x in rs)}
                cat = lambda r: (a1(r) and                                # noqa: E731
                                 (r["base"], delta_of(r["tag"])) in catastrophic)
                bc, nc = by_base(base_rows, cat, lambda r: r["refused"])
                ac, _ = by_base(arm_rows, cat, lambda r: r["refused"])
                res["arm1_all16_failed"] = {
                    "n_cells": len(catastrophic),
                    "cells": sorted(catastrophic),
                    "baseline": t_ci([bc.get(t, 0.0) for t in bc]),
                    "armed": t_ci([ac.get(t, 0.0) for t in ac]),
                    "paired_increment": paired(ac, bc, sorted(bc)),
                    "n_base_frames": len(bc), "n_trials": sum(nc.values())}

                # --- ARM 2a: DOES NOT ABSTAIN ON HARD-BUT-CONTINUOUS ------ #
                # Population: A1 probes the comparator got RIGHT, whose span
                # lies in the TOP MOTION DECILE among non-cut steps.
                def hard_right(r):
                    if not (a1(r) and r["true_is_max"]):
                        return False
                    d = delta_of(r["tag"])
                    span = range(r["base"], min(r["base"] + d, len(step)))
                    return (any(t in hard_steps for t in span)
                            and not any(t in numpy_cuts for t in span))
                bh, nh = by_base(base_rows, hard_right, lambda r: r["refused"])
                ah, _ = by_base(arm_rows, hard_right, lambda r: r["refused"])
                res["arm2a_false_refusal_hard"] = {
                    "baseline": t_ci([bh.get(t, 0.0) for t in bh]),
                    "armed": t_ci([ah.get(t, 0.0) for t in ah]),
                    "paired_increment": paired(ah, bh, sorted(bh)),
                    "n_base_frames": len(bh), "n_trials": sum(nh.values())}

                # The same on EVERY correct answer, cut-free span -- the total
                # cost of the abstention on work the comparator could do.
                def easy_right(r):
                    if not (a1(r) and r["true_is_max"]):
                        return False
                    d = delta_of(r["tag"])
                    span = range(r["base"], min(r["base"] + d, len(step)))
                    return not any(t in numpy_cuts for t in span)
                be, ne = by_base(base_rows, easy_right, lambda r: r["refused"])
                ae, _ = by_base(arm_rows, easy_right, lambda r: r["refused"])
                res["arm2a_false_refusal_all_noncut_correct"] = {
                    "baseline": t_ci([be.get(t, 0.0) for t in be]),
                    "armed": t_ci([ae.get(t, 0.0) for t in ae]),
                    "paired_increment": paired(ae, be, sorted(be)),
                    "n_base_frames": len(be), "n_trials": sum(ne.values())}

                # --- ARM 3: BYTE-IDENTITY OFF THE CUT FRAMES -------------- #
                # Every row whose span contains no step THE GRAPH MARKED must
                # be field-identical between the inert and armed runs.
                fields = ("tag", "kind", "truth", "said", "said_idx", "answer",
                          "answer_idx", "refused", "n_orbit", "graph_max",
                          "noise_floor", "status", "ref_idx", "ref_max",
                          "ref_region_ties", "v0_region_ties", "true_score",
                          "true_is_max", "probe_nflat", "base")
                n_off, n_diff, diffs = 0, 0, []
                for a, b in zip(arm_rows, base_rows):
                    if a.get("spans_marked", 0):
                        continue
                    n_off += 1
                    bad = [f for f in fields if a.get(f) != b.get(f)]
                    if bad:
                        n_diff += 1
                        if len(diffs) < 5:
                            diffs.append({"tag": a["tag"], "base": a["base"],
                                          "fields": bad})
                res["arm3_byte_identity_off_cuts"] = {
                    "n_rows_off_cut": n_off, "n_rows_differing": n_diff,
                    "identical": n_diff == 0, "examples": diffs}

                # --- THE INCREMENT OVER V3's EXISTING REFUSAL ------------- #
                # Refusal rate on A1 probes, split by whether the graph marked
                # the probe's span. This is the headline increment.
                for name, pred in (
                        ("marked", lambda r: a1(r) and r.get("spans_marked", 0) > 0),
                        ("unmarked", lambda r: a1(r) and not r.get("spans_marked", 0))):
                    # `spans_marked` exists only on the armed rows, so the
                    # baseline is selected by the ARMED run's marks, matched
                    # row for row (the row order is identical by construction
                    # and arm 3 checks that).
                    idx = {i for i, r in enumerate(arm_rows) if pred(r)}
                    bsel = [r for i, r in enumerate(base_rows) if i in idx]
                    asel = [r for i, r in enumerate(arm_rows) if i in idx]
                    bb, nn = by_base(bsel, lambda r: True, lambda r: r["refused"])
                    aa, _ = by_base(asel, lambda r: True, lambda r: r["refused"])
                    ba, _ = by_base(bsel, lambda r: True,
                                    lambda r: r["true_is_max"])
                    res[f"increment_{name}"] = {
                        "baseline_refusal": t_ci([bb.get(t, 0.0) for t in bb]),
                        "armed_refusal": t_ci([aa.get(t, 0.0) for t in aa]),
                        "paired_increment": paired(aa, bb, sorted(bb)),
                        "baseline_accuracy": t_ci([ba.get(t, 0.0) for t in ba]),
                        "n_base_frames": len(bb), "n_trials": sum(nn.values())}

                out["arms"][key] = res

    # The graph's own threshold and marks, against the numpy reference.
    for key, run in meas["runs"].items():
        cid = key.split("|")[0]
        ref = meas["reference"].get(cid)
        if ref is None or "|inert" in key:
            continue
        out["instrument"].setdefault(cid, {})[f"{key}|graph_cut_steps"] = \
            run["graph_cut_steps"]
        out["instrument"][cid][f"{key}|threshold"] = run["graph_threshold"]
        if key.endswith("|mag"):
            g = run["graph_mag"]
            out["instrument"][cid][f"{key}|mag_matches_numpy"] = all(
                abs(a - b) < 1e-9 for a, b in zip(g, ref["step"]))
            out["instrument"][cid][f"{key}|partition_matches_numpy"] = (
                run["graph_cut_steps"] == ref["numpy_cut_steps"])
        out["instrument"][cid][f"{key}|markers"] = run["markers"]

    out["arm2b"] = meas.get("arm2b", {})
    out["arm4"] = meas.get("arm4", {})

    path = os.path.join(ROOT, "results", "cut_abstention_analysis.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path}")

    # --- human-readable summary --------------------------------------------- #
    for key, res in out["arms"].items():
        print(f"\n=== {key} ===")
        for name in ("arm1_all16_failed", "arm1_recall_over_errors",
                     "arm1_d1", "arm1_d5", "arm1_d25",
                     "arm2a_false_refusal_hard",
                     "arm2a_false_refusal_all_noncut_correct",
                     "increment_marked", "increment_unmarked"):
            r = res.get(name)
            if not r:
                continue
            b = r.get("baseline") or r.get("baseline_refusal")
            a = r.get("armed") or r.get("armed_refusal")
            p = r["paired_increment"]
            print(f"  {name:42s} base {b[0]:.4f}  armed {a[0]:.4f}  "
                  f"delta {p[0]:+.4f} [{p[1]:+.4f}, {p[2]:+.4f}]  "
                  f"n_frames {r.get('n_base_frames')} n_trials {r.get('n_trials')}")
        a3 = res["arm3_byte_identity_off_cuts"]
        print(f"  arm3 byte-identity off cuts: {a3['identical']} "
              f"({a3['n_rows_differing']}/{a3['n_rows_off_cut']} differ)")


if __name__ == "__main__":
    main()
