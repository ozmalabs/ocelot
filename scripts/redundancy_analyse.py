"""Analyse the redundancy sweep against VISION_REDUNDANCY_PREREG.md.

Produces, in order: the Arm 0 determinism gate, the Arm 1 LIVE/DEAD rule census,
the Arm 2 cross-capability matrix split into DIAGONAL (files that install the
ablated seed -- the positive control) and OFF-DIAGONAL (the actual redundancy
question), the Arm 3 shape statistics against their analytic endpoints, and the
crash list.

No thresholds. `maxfrac` and the normalised increment entropy are reported
against endpoints that fall out of each seed's own rule count n (PREREG §4).
"""
from __future__ import annotations

import collections
import glob
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "redundancy")
SEEDMAP = json.load(open(os.path.join(ROOT, "results", "redundancy_seed_map.json")))

# file -> seeds it installs; inverted to seed -> files (the DIAGONAL).
DIAG: dict[str, set[str]] = collections.defaultdict(set)
for _f, _seeds in SEEDMAP.items():
    for _s in _seeds:
        DIAG[_s].add(_f)


def load(tag: str):
    p = os.path.join(RES, tag + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def rules_of(sid: str) -> list[str]:
    with open(os.path.join(ROOT, "seeds", f"{sid}.json")) as fh:
        return [r.get("name", "") for r in json.load(fh).get("rules", [])]


def per_file_passed(rec) -> dict[str, int]:
    return {f: v.get("passed", 0) for f, v in (rec.get("per_file") or {}).items()}


def main() -> None:
    base = load("baseline_0")
    baseline_files = per_file_passed(base)
    BASE_TOTAL = base["passed"]
    out: dict = {"baseline_total": BASE_TOTAL}

    print("=" * 78)
    print("ARM 0 -- baseline determinism + concurrency gate")
    print("=" * 78)
    bl = [load(f"baseline_{i}") for i in range(3)]
    for i, b in enumerate(bl):
        print(f"  baseline_{i}: passed={b['passed']} failed={b['failed']} exit={b['exitstatus']}")
    gate_ok = len({b["passed"] for b in bl}) == 1 and bl[0]["passed"] == 200
    print(f"  GATE: {'PASS' if gate_ok else 'FAIL'}")
    out["arm0_pass"] = gate_ok

    print()
    print("=" * 78)
    print("ARM 1 -- rule-firing census (the dead-arm gate). progress>0 == LIVE")
    print("=" * 78)
    cen = load("census")
    census = (cen or {}).get("census_progress", {})
    out["census_available"] = bool(census)
    targets = sorted({os.path.basename(p)[len("whole__"):-5]
                      for p in glob.glob(os.path.join(RES, "whole__*.json"))})
    live_tbl = []
    for sid in targets:
        rs = rules_of(sid)
        live = [r for r in rs if census.get(r, 0) > 0]
        dead = [r for r in rs if census.get(r, 0) == 0]
        live_tbl.append({"seed": sid, "n": len(rs), "live": len(live), "dead": len(dead),
                         "dead_names": dead, "fires": sum(census.get(r, 0) for r in rs)})
    for row in sorted(live_tbl, key=lambda r: -r["fires"]):
        print(f"  {row['seed']:24s} n={row['n']:3d} LIVE={row['live']:3d} DEAD={row['dead']:3d} "
              f"total_fires={row['fires']}")
    out["census"] = live_tbl

    print()
    print("=" * 78)
    print("ARM 2 -- cross-capability matrix. DIAGONAL = files installing the seed")
    print("          (positive control). OFF-DIAGONAL = the redundancy question.")
    print("=" * 78)
    print(f"  {'seed':24s} {'tot':>5s} {'d_tot':>6s} {'diag_loss':>10s} {'OFFDIAG':>8s}  files_off")
    matrix = []
    for sid in targets:
        rec = load(f"whole__{sid}")
        if rec is None:
            continue
        if rec.get("crashed_before_report"):
            print(f"  {sid:24s}  *** CRASHED BEFORE REPORT (exit {rec['exitstatus']}) ***")
            matrix.append({"seed": sid, "crashed": True})
            continue
        pf = per_file_passed(rec)
        diag_files = DIAG.get(sid, set())
        diag_loss = off_loss = 0
        off_files = []
        for f, b in baseline_files.items():
            d = b - pf.get(f, 0)
            if d <= 0:
                continue
            if f in diag_files:
                diag_loss += d
            else:
                off_loss += d
                off_files.append(f"{f}(-{d})")
        row = {"seed": sid, "total": rec["passed"], "delta": rec["passed"] - BASE_TOTAL,
               "diag_loss": diag_loss, "off_loss": off_loss, "off_files": off_files,
               "n_rules": len(rules_of(sid)),
               "live_rules": sum(1 for r in rules_of(sid) if census.get(r, 0) > 0)}
        matrix.append(row)
        print(f"  {sid:24s} {rec['passed']:5d} {row['delta']:6d} {diag_loss:10d} "
              f"{off_loss:8d}  {' '.join(off_files) if off_files else '-'}")
    out["matrix"] = matrix

    print()
    print("=" * 78)
    print("ARM 3 -- severity curves. Endpoints are ANALYTIC (step: maxfrac=1, H=0;")
    print("          graded: maxfrac=1/n, H=1). No threshold is applied.")
    print("=" * 78)
    shapes = []
    for sid in targets:
        n = len(rules_of(sid))
        if not (2 <= n <= 15):
            continue
        for ps in (59000, 59001):
            curve = [BASE_TOTAL]
            ok = True
            for k in range(1, n):
                r = load(f"sev__{sid}__p{ps}__k{k}")
                if r is None:
                    ok = False
                    break
                curve.append(r["passed"])
            whole = load(f"whole__{sid}")
            if not ok or whole is None:
                continue
            curve.append(whole["passed"])
            L = curve[0] - curve[-1]
            d = [curve[i - 1] - curve[i] for i in range(1, len(curve))]
            if L <= 0:
                shapes.append({"seed": sid, "perm": ps, "curve": curve, "L": L,
                               "maxfrac": None, "H": None, "note": "L<=0: no loss; Arm 1 question"})
                continue
            pos = [max(x, 0) for x in d]
            tot = sum(pos) or 1
            p = [x / tot for x in pos if x > 0]
            H = -sum(q * math.log(q) for q in p) / math.log(n) if n > 1 else 0.0
            shapes.append({"seed": sid, "perm": ps, "curve": curve, "L": L, "n": n,
                           "maxfrac": max(pos) / L, "graded_floor": 1.0 / n, "H": H})
    for s in shapes:
        if s.get("maxfrac") is None:
            print(f"  {s['seed']:22s} p{s['perm']} L={s['L']:4d}  {s['note']}")
        else:
            print(f"  {s['seed']:22s} p{s['perm']} n={s['n']:2d} L={s['L']:4d} "
                  f"maxfrac={s['maxfrac']:.3f} (graded floor {s['graded_floor']:.3f}) "
                  f"H={s['H']:.3f}  curve={s['curve']}")
    out["shapes"] = shapes

    print()
    print("=" * 78)
    print("CRASH LIST (a crash is a result, not a harness bug)")
    print("=" * 78)
    crashes = []
    for p in sorted(glob.glob(os.path.join(RES, "*.json"))):
        r = json.load(open(p))
        tag = os.path.basename(p)[:-5]
        if r.get("crashed_before_report"):
            crashes.append({"tag": tag, "kind": "process_died", "exit": r["exitstatus"],
                            "tail": (r.get("stderr_tail") or "")[-1200:]})
        else:
            for e in (r.get("errors") or []):
                if e.get("phase") in ("collect", "setup"):
                    crashes.append({"tag": tag, "kind": e["phase"], "nodeid": e.get("nodeid"),
                                    "repr": (e.get("repr") or "")[:600]})
    for c in crashes:
        print(f"  {c['tag']:44s} {c['kind']}")
    if not crashes:
        print("  (none)")
    out["crashes"] = crashes

    with open(os.path.join(ROOT, "results", "redundancy_analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(f"\n[written] results/redundancy_analysis.json")


if __name__ == "__main__":
    main()
