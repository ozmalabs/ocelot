#!/usr/bin/env python3
"""WP3 measurement: substrate-chosen grain and MDL witness on real handwriting.

Inputs: Omniglot strokes_background, first 10 alphabets x first 2 characters,
drawer 1 (deterministic). Each drawing is rendered to a 16x16 cell lattice
(`["cell", r, c]`, the production ARC/vision form).

Conditions per drawing A (20 drawings) and planted map M in
{rotation [0,1,-1,0], reflection [-1,0,0,1], shear [1,1,0,1]}:
  exact    goal = M . A                          (control: grain 0)
  jitter   goal = M . A', A' = A's stroke points displaced by uniform
           +-0.35 cell before rasterization       (sub-cell rendering noise)
  outlier  goal = M . A with 2 cells displaced by 3 cells (MDL target)
  cross    goal = M . B, B a different character  (false-explain control)

Arms (one native binary built with geninfer_linear_exact_prefilter +
geninfer_grain_mdl; runtime flags select arms):
  g0     gen_grain_levels absent, MDL off  -- current behaviour
  ladder gen_grain_levels = 3              -- substrate picks the grain
  mdl    MDL witness at grain 0 (Term level)

Outcomes: recovered M exactly (matrix equal to planted), explained with a
wrong matrix, refused. The sd loop is run for g0/ladder (full seed rules);
MDL is evaluated as a GenInfer Term with mdl_enabled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OMNI = ROOT / "data/omniglot/strokes_background"
OUT = ROOT / "evaluation/reports/geninfer_grain_ladder_omniglot_v1_20261006.json"
GRID = 16
DT = ["pred", "coord:r", "coord:c"]
MAPS = {"shear_a": [1, 1, 0, 1], "shear_b": [1, 0, 1, 1], "unimodular": [2, 1, 1, 1]}  # outside the held D4/scale codebook
SEED = 20261006


def strokes(path):
    out, cur = [], []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line == "START":
            cur = []
        elif line == "BREAK":
            if cur:
                out.append(cur)
            cur = []
        elif line:
            x, y, _ = line.split(",")
            cur.append((float(x), -float(y)))
    if cur:
        out.append(cur)
    return out


def raster(st, jitter=0.0, rng=None):
    pts = [p for s in st for p in s]
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    span = max(max(p[0] for p in pts) - x0, max(p[1] for p in pts) - y0, 1e-9)
    cells = set()
    for s in st:
        dense = []
        for a, b in zip(s, s[1:] or s):
            n = max(2, int(math.dist(a, b) / span * GRID * 3))
            dense += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(n + 1)]
        for x, y in dense:
            fx, fy = (x - x0) / span * (GRID - 1), (y - y0) / span * (GRID - 1)
            if jitter:
                fx += rng.uniform(-jitter, jitter)
                fy += rng.uniform(-jitter, jitter)
            cells.add((min(GRID - 1, max(0, round(fy))), min(GRID - 1, max(0, round(fx)))))
    return sorted(cells)


def apply(m, cells):
    mr, mc = min(r for r, _ in cells), min(c for _, c in cells)
    out = sorted({(m[0] * (r - mr) + m[1] * (c - mc), m[2] * (r - mr) + m[3] * (c - mc)) for r, c in cells})
    nr, nc = min(r for r, _ in out), min(c for _, c in out)
    return [(r - nr, c - nc) for r, c in out]


def sig(cells):
    return [["cell", r, c] for r, c in cells]


def drawings():
    out = []
    for a in sorted(p for p in OMNI.iterdir() if p.is_dir())[:10]:
        for c in sorted(p for p in a.iterdir() if p.is_dir())[:2]:
            out.append((f"{a.name}/{c.name}", sorted(c.glob("*.txt"))[0]))
    return out


def install(native_path):
    tmp = tempfile.TemporaryDirectory(prefix="wp3-")
    pkg = Path(tmp.name) / "substrate_rs"
    shutil.copytree(ROOT / "runners/dsl/python/substrate_rs", pkg, ignore=shutil.ignore_patterns("_native*.so", "__pycache__"))
    shutil.copy2(native_path, pkg / "_native.abi3.so")
    sys.path[:0] = [tmp.name, str(ROOT), str(ROOT / "runners/dsl/python")]
    return tmp


def sd_run(base, goal, levels):
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    s, ag = boot_core()
    n = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, n, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.set_attr(ag, "gen_linear_exact_enabled", 1.0)
    if levels:
        s.set_attr(ag, "gen_grains", list(range(levels + 1)))
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base), "kind": "faculty",
                                  "faculty": "base", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o = s.add_node("Observation", {"signature": goal, "key": ["wp3"], "status": "decoded", "residual": goal,
                                   "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", o)
    t0 = time.perf_counter()
    n.run_rules()
    dt = time.perf_counter() - t0
    a = s.node(o)["attrs"]
    gens = [s.node(g)["attrs"] for g in s.nodes("DimensionGenerator") if s.node(g)["attrs"].get("kind") == "linear"]
    m = list(gens[0]["matrix"]) if gens else None
    return {"status": a.get("status"), "grain": a.get("gen_grain"), "matrix": m,
            "minted_map_grain": gens[0].get("minted_map_grain") if gens else None, "seconds": dt}


def mdl_run(base, goal):
    from substrate.boot_core import boot_core
    s, ag = boot_core()
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base), "kind": "faculty",
                                  "faculty": "base", "dim_types": DT})
    t = {"type": "GenInfer", "goal": {"type": "Lit", "value": goal}, "max_dims": 2,
         "linear_prefilter_enabled": {"type": "Lit", "value": True}, "mdl_enabled": {"type": "Lit", "value": True}}
    t0 = time.perf_counter()
    ex = s._inner.evaluate(dict(t, field="explained"), {})
    m = list(s._inner.evaluate(dict(t, field="matrix"), {}) or ())
    w = s._inner.evaluate(dict(t, field="witness"), {})
    out = len(s._inner.evaluate(dict(t, field="outliers"), {}) or ())
    return {"explained": ex, "matrix": m if ex else None, "witness": w, "outliers": out,
            "seconds": time.perf_counter() - t0}


def classify(matrix, planted):
    if matrix is None:
        return "refused"
    return "recovered" if list(matrix) == planted else "wrong_map"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--native", type=Path, required=True)
    args = ap.parse_args()
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    tmp = install(args.native.resolve())
    rng = random.Random(SEED)
    ds = drawings()
    rows = []
    for i, (label, path) in enumerate(ds):
        st = strokes(path)
        A = raster(st)
        B = raster(strokes(ds[(i + 7) % len(ds)][1]))
        for mname, M in MAPS.items():
            goals = {"exact": apply(M, A), "jitter": apply(M, raster(st, 0.35, rng)),
                     "cross": apply(M, B)}
            mov = list(apply(M, A))
            for j in rng.sample(range(len(mov)), 2):
                mov[j] = (mov[j][0] + 3, mov[j][1] + 3)
            goals["outlier"] = sorted(set(mov))
            for cond, g in goals.items():
                base, goal = sig(A), sig(g)
                if len(goal) != len(base) and cond != "cross":
                    note = "relation_count_changed"
                else:
                    note = ""
                r = {"drawing": label, "map": mname, "cond": cond, "n_base": len(base), "n_goal": len(goal), "note": note}
                r["g0"] = sd_run(base, goal, 0)
                r["ladder"] = sd_run(base, goal, 3)
                r["mdl"] = mdl_run(base, goal)
                for arm in ("g0", "ladder", "mdl"):
                    r[arm]["class"] = classify(r[arm]["matrix"], M)
                rows.append(r)
        print(i, label, flush=True)
    summ = {}
    for cond in ("exact", "jitter", "outlier", "cross"):
        for arm in ("g0", "ladder", "mdl"):
            rs = [r for r in rows if r["cond"] == cond]
            c = {k: sum(r[arm]["class"] == k for r in rs) for k in ("recovered", "wrong_map", "refused")}
            if arm == "ladder":
                c["grains"] = sorted({r[arm]["grain"] for r in rs if r[arm]["grain"] is not None})
            summ[f"{cond}:{arm}"] = c
    rep = {"schema": "GenInferGrainLadderOmniglotV1", "native_sha256": hashlib.sha256(args.native.read_bytes()).hexdigest(),
           "seed_sha256": hashlib.sha256((ROOT / "seeds/shape_decode_loop.json").read_bytes()).hexdigest(),
           "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "rows": rows, "summary": summ}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
    for k, v in summ.items():
        print(k, v)
    tmp.cleanup()


if __name__ == "__main__":
    main()
