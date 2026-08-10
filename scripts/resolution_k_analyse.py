"""THE K ARM — the pre-registered read-outs, applied.

`VISION_RESOLUTION_SCALE_PREREG.md` section 4. Input resolution is FIXED; K
varies over NESTED PREFIXES of one growth run.

TWO CRITERIA, REPORTED SIDE BY SIDE (prereg 4.2, confound 2):

  OWN FLOOR   the graph's own `is_held` status at that K, whose noise floor
              was re-measured for that codebook. This is the graph's decision.
  FIXED FLOOR the SAME recorded raw scores re-thresholded, outside the graph,
              against ONE criterion held constant across every K (the floor
              measured at K_max). This is a RECOMPUTATION on recorded numbers,
              not a second graph run, and it is labelled as such wherever it
              is printed.

**The hypothesis is credited only if the effect survives the FIXED criterion.**

THE FIREWALL (prereg 4.3): nothing here licenses any change to the
effective-n verdict.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def entropy_norm(counts):
    """Normalized Shannon entropy of a per-frame usage distribution. 1.0 = the
    frame's regions spread evenly over the entries it used."""
    tot = sum(counts)
    if tot <= 0 or len(counts) <= 1:
        return float("nan")
    ps = [c / tot for c in counts if c > 0]
    h = -sum(p * math.log(p) for p in ps)
    return h / math.log(len(counts)) if len(counts) > 1 else float("nan")


def main():
    path = os.path.join(RES, "resolution_k_arm.json")
    d = json.load(open(path))
    out = {"prereg": "VISION_RESOLUTION_SCALE_PREREG.md",
           "prereg_commit": d.get("prereg_commit"),
           "provenance": d.get("provenance"),
           "grid": d["grid"], "region": d["region"],
           "n_regions": d["n_regions"], "corpora": {}}

    print("=" * 84)
    print("THE K ARM — INPUT RESOLUTION FIXED "
          f"(GRID={d['grid']}, REGION={d['region']}, "
          f"{d['n_regions']} regions/frame), K VARIES")
    print("  codebooks are NESTED PREFIXES of ONE growth run at ONE seed")
    print("  (so K is not re-drawn; which entries are present varies only by")
    print("   the mint order the growth itself produced)")
    print("=" * 84)

    for cid, R in d["corpora"].items():
        rungs = R.get("rungs", {})
        if not rungs:
            continue
        ks = sorted(rungs, key=lambda s: int(s))
        # THE FIXED CRITERION: the floor measured at the LARGEST K.
        kmax_key = ks[-1]
        fixed_floor = rungs[kmax_key]["floor"]
        print(f"\n--- {cid} ({R['meta'].get('name','?')}) ---")
        print(f"  fixed criterion = the floor measured at K_max "
              f"(prefix {kmax_key}): {fixed_floor}")
        print(f"  {'prefix':>7s} {'K':>5s} {'own floor':>10s} "
              f"{'decoded@own':>12s} {'decoded@FIXED':>14s} "
              f"{'distinct/frame':>15s} {'entropy':>8s}")
        rows = {}
        for k in ks:
            r = rungs[k]
            pf = r["per_frame"]
            dec_own = float(np.mean([np.mean(p["held_ok"]) for p in pf]))
            # RECOMPUTED outside the graph on the recorded raw scores.
            dec_fix = float(np.mean([
                np.mean([1.0 if (s == s and fixed_floor is not None
                                 and s > fixed_floor) else 0.0
                         for s in p["scores"]]) for p in pf]))
            dist, ents = [], []
            for p in pf:
                used = {}
                for i in p["ids"]:
                    if i:
                        used[i] = used.get(i, 0) + 1
                dist.append(len(used))
                ents.append(entropy_norm(list(used.values())))
            dm = float(np.mean(dist))
            em = float(np.nanmean(ents)) if ents else float("nan")
            rows[k] = {"K": r["K"], "own_floor": r["floor"],
                       "decoded_own": dec_own, "decoded_fixed": dec_fix,
                       "distinct_per_frame": dm, "usage_entropy": em,
                       "n_train_prefix": r["n_train_prefix"]}
            print(f"  {k:>7s} {r['K']:5d} "
                  f"{(r['floor'] if r['floor'] is not None else float('nan')):10.4f} "
                  f"{dec_own:12.4f} {dec_fix:14.4f} {dm:15.2f} {em:8.4f}")

        # the pre-registered verdicts
        seq_k = [rows[k]["K"] for k in ks]
        v = {
            "K_rises": bool(all(a < b for a, b in zip(seq_k, seq_k[1:]))),
            "decoded_own_rises": bool(all(
                rows[a]["decoded_own"] <= rows[b]["decoded_own"] + 1e-12
                for a, b in zip(ks, ks[1:]))),
            "decoded_fixed_rises": bool(all(
                rows[a]["decoded_fixed"] <= rows[b]["decoded_fixed"] + 1e-12
                for a, b in zip(ks, ks[1:]))),
            "distinct_rises": bool(all(
                rows[a]["distinct_per_frame"] <= rows[b]["distinct_per_frame"] + 1e-12
                for a, b in zip(ks, ks[1:]))),
            "decoded_own_first_to_last":
                rows[ks[-1]]["decoded_own"] - rows[ks[0]]["decoded_own"],
            "decoded_fixed_first_to_last":
                rows[ks[-1]]["decoded_fixed"] - rows[ks[0]]["decoded_fixed"],
            "distinct_first_to_last":
                rows[ks[-1]]["distinct_per_frame"] - rows[ks[0]]["distinct_per_frame"],
            "floor_first": rows[ks[0]]["own_floor"],
            "floor_last": rows[ks[-1]]["own_floor"],
        }
        print(f"\n  monotone in K:  decoded@own={v['decoded_own_rises']}  "
              f"decoded@FIXED={v['decoded_fixed_rises']}  "
              f"distinct/frame={v['distinct_rises']}")
        print(f"  first->last:    decoded@own {v['decoded_own_first_to_last']:+.4f}  "
              f"decoded@FIXED {v['decoded_fixed_first_to_last']:+.4f}  "
              f"distinct/frame {v['distinct_first_to_last']:+.2f}")
        print(f"  the floor MOVED with K: {v['floor_first']} -> {v['floor_last']}"
              "   (this is exactly confound 2; the FIXED column is the control)")
        out["corpora"][cid] = {"rows": rows, "verdicts": v,
                               "fixed_floor": fixed_floor,
                               "K_final": R.get("K_final"),
                               "n_train": len(R.get("train", [])),
                               "n_held": len(R.get("held", []))}

    print("\n" + "=" * 84)
    print("FIREWALL (prereg 4.3): this arm licenses NO change to the")
    print("effective-n verdict. It is a different variable.")
    print("=" * 84)
    op = os.path.join(RES, "resolution_k_analysis.json")
    with open(op, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {op}")


if __name__ == "__main__":
    main()
