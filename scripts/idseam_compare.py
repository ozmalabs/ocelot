#!/usr/bin/env python3
"""Deterministic field-by-field diff of two identity_seam arm directories.

Not an agent decision — a mechanical comparator. Reports every leaf that
differs between arm A and arm B, excluding wall-clock / provenance noise
(load-dependent, per the prereg), and separately tallies the per-observation
STATUS distribution from the rows files.
"""
import json
import sys
from collections import Counter
from pathlib import Path

# leaf keys excluded from the VERDICT (load-dependent or provenance)
NOISE_SUBSTR = ("ms", "wall_s", "main_ms", "provenance", "log", "_ms",
                "seconds", "elapsed")


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def is_noise(path):
    p = path.lower()
    return any(s in p for s in NOISE_SUBSTR)


def diff_json(a_path, b_path):
    a = json.loads(Path(a_path).read_text())
    b = json.loads(Path(b_path).read_text())
    la = dict(leaves(a))
    lb = dict(leaves(b))
    keys = sorted(set(la) | set(lb))
    movers = []
    noise_moved = 0
    for k in keys:
        va, vb = la.get(k, "<MISSING>"), lb.get(k, "<MISSING>")
        if va != vb:
            if is_noise(k):
                noise_moved += 1
            else:
                movers.append((k, va, vb))
    return movers, noise_moved


def status_dist(rows_path):
    rows = json.loads(Path(rows_path).read_text())
    return Counter(r["status"] for r in rows), len(rows)


def main():
    armA, armB = sys.argv[1], sys.argv[2]  # e.g. results/idseam_arm/fix revert
    labelA = Path(armA).name
    labelB = Path(armB).name
    print(f"### SUMMARY DOCUMENT DIFF  ({labelA} vs {labelB})")
    for cid in ("C1", "C2"):
        fa = f"{armA}/identity_seam_{cid}.json"
        fb = f"{armB}/identity_seam_{cid}.json"
        if not (Path(fa).exists() and Path(fb).exists()):
            print(f"  {cid}: MISSING ({fa} or {fb})")
            continue
        movers, noise = diff_json(fa, fb)
        print(f"\n  {cid}: {len(movers)} NON-NOISE movers, {noise} noise leaves moved")
        for k, va, vb in movers:
            print(f"    {k}: {labelA}={va!r}  {labelB}={vb!r}")

    print(f"\n### PER-OBSERVATION STATUS DISTRIBUTION (main trajectory, n=1600)")
    for cid in ("C1", "C2"):
        for arm_name in ("stock", "ncc"):
            pa = f"{armA}/identity_seam_rows_{cid}_{arm_name}.json"
            pb = f"{armB}/identity_seam_rows_{cid}_{arm_name}.json"
            if not (Path(pa).exists() and Path(pb).exists()):
                print(f"  {cid}/{arm_name}: MISSING")
                continue
            da, na = status_dist(pa)
            db, nb = status_dist(pb)
            same = da == db
            # count per-row status flips
            ra = json.loads(Path(pa).read_text())
            rb = json.loads(Path(pb).read_text())
            flips = sum(1 for x, y in zip(ra, rb) if x["status"] != y["status"])
            print(f"  {cid}/{arm_name}: {labelA}={dict(da)}  {labelB}={dict(db)}"
                  f"  | row-status flips={flips}  identical={same}")


if __name__ == "__main__":
    main()
