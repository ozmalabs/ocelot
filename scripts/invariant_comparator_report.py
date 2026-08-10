#!/usr/bin/env python3
"""INVARIANT COMPARATOR — presentation only. Renders the pinned results JSON as
the tables the write-up quotes. Computes NO new statistic and applies NO
decision: everything here is already in `results/invariant_comparator_*.json`,
put there by the confirmatory runner under the pre-registered rules.

USAGE: python scripts/invariant_comparator_report.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def load(name):
    p = os.path.join(RES, f"invariant_comparator_{name}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def fmt(s, key="unit"):
    if not s:
        return "     --      "
    return (f"{s[key + '_acc']:.4f} [{s[key + '_lo']:.4f},{s[key + '_hi']:.4f}]")


def c3_tables(d):
    print("\n=== C3  THE TRADE-OFF CURVE (photo-level, n=24, 95% t-CI) ===")
    print(f"{'cmp':4s} {'T axis':>7s} {'T diag':>7s} "
          f"{'M (margin) [95% CI]':>30s} {'excl 0':>7s} "
          f"{'d0 acc':>8s} {'A3 d0':>8s} {'entropy':>8s} {'ntied':>7s} "
          f"{'G2':>7s} {'R2 score':>9s}")
    for c in d["constants"]["comparators"]:
        cid = c[0]
        v = d["c3"].get(cid)
        if not v:
            continue
        m = v.get("MARGIN|axis") or {}
        a0 = v.get("A1|axis|d0")
        f0 = v.get("A3|axis|d0")
        g2 = v.get("G2_noise")
        print(f"{cid:4s} {str(v.get('HORIZON|axis')):>7s} "
              f"{str(v.get('HORIZON|diag')):>7s} "
              f"{m.get('margin', 0):>10.4f} [{m.get('lo', 0):.4f},{m.get('hi', 0):.4f}]"
              f" {str(m.get('excludes_zero')):>7s} "
              f"{a0['unit_acc']:>8.4f} {f0['unit_acc']:>8.4f} "
              f"{a0['answer_entropy']:>8.4f} {a0['mean_ntied']:>7.2f} "
              f"{g2['unit_acc']:>7.4f} {a0['score_agreement_with_R2']:>9.4f}")

    for mode in ("axis", "diag"):
        print(f"\n=== C3 {mode.upper()}: accuracy vs displacement "
              f"(A1 / A3 floor, photo-level) ===")
        ds = (d["constants"]["displacements"] if mode == "axis"
              else d["constants"]["diag_displacements"])
        head = "cmp  " + " ".join(f"{'d=' + str(x):>21s}" for x in ds)
        print(head)
        for c in d["constants"]["comparators"]:
            cid = c[0]
            v = d["c3"].get(cid)
            if not v or f"A1|{mode}|d{ds[0]}" not in v:
                continue
            row = f"{cid:4s} "
            for x in ds:
                a = v.get(f"A1|{mode}|d{x}")
                f = v.get(f"A3|{mode}|d{x}")
                row += (f"{a['unit_acc']:.3f}/{f['unit_acc']:.3f}"
                        f"{'*' if a['unit_lo'] > f['unit_hi'] else ' '}").rjust(22)
            print(row)
        print("  (* = A1 CI-separated from its own A3 floor at that displacement)")


def video_tables(d):
    for cid, arms in d.get("video", {}).items():
        print(f"\n=== {cid} REAL MOTION (base-frame level, n=50, 95% t-CI) ===")
        mot = d.get("motion", {}).get(cid, {})
        print(f"  inter-frame |diff| mean={mot.get('mean', 0):.3f} "
              f"sd={mot.get('sd', 0):.3f} max={mot.get('max', 0):.3f}")
        print(f"{'cmp':4s} {'horizon':>8s} " +
              " ".join(f"{'A1 d=' + str(x):>22s}" for x in d["constants"]["deltas"]) +
              f" {'G1':>8s} {'G2':>8s} {'ntied':>7s}")
        for name, v in arms.items():
            row = f"{name:4s} {str(v.get('HORIZON|delta')):>8s} "
            for x in d["constants"]["deltas"]:
                a = v.get(f"A1|d{x}")
                row += fmt(a).rjust(23) if a else " " * 23
            g1, g2 = v.get("G1"), v.get("G2")
            row += (f" {g1['unit_acc']:>8.4f} {g2['unit_acc']:>8.4f} "
                    f"{v['A1|d1']['mean_ntied']:>7.2f}")
            print(row)
        print(f"\n  floors ({cid}):")
        for name, v in arms.items():
            print(f"  {name:4s} " + " ".join(
                f"d{x}: A2 {v[f'A2|d{x}']['unit_acc']:.3f} "
                f"A3 {v[f'A3|d{x}']['unit_acc']:.3f}  "
                for x in d["constants"]["deltas"]))


def main():
    c3 = load("c3")
    if c3:
        print(f"[provenance] {c3['provenance']}")
        print(f"[machine at start] {c3['machine_state_at_start']['loadavg']}")
        c3_tables(c3)
    vid = load("video")
    if vid:
        print(f"\n[provenance] {vid['provenance']}")
        video_tables(vid)
    rp = load("replay")
    if rp:
        print(f"\n[replay] {rp['replay']}")


if __name__ == "__main__":
    main()
