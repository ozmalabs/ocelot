#!/usr/bin/env python3
"""Tranche 5: what did the degenerate-collapse guard remove?

Pure set analysis on the preregistered held-out panel (tranche 3/4 data).
For each drawer-condition pair recognised WITHOUT the guard and lost WITH it,
record the coarse goal's shape at the recognising grain: cell count, bbox
area, and whether it fills its bbox. Then the RISK of dropping the guard: over
all ordered pairs of DIFFERENT held-out characters x held maps x grains 1-2,
how often does M.q_g(A) == q_g(M.B) hold when q_g(goal) is degenerate,
versus when it is not.
"""
import json, sys, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geninfer_grain_ladder_omniglot_v1 import strokes, raster  # noqa: E402
OUT = ROOT / "evaluation/reports/degenerate_guard_analysis_v1_20261007.json"
EVAL = ROOT / "data/omniglot/strokes_evaluation"
MAPS = {"rot90": lambda r, c: (c, -r), "rot180": lambda r, c: (-r, -c), "rot270": lambda r, c: (-c, r),
        "refl_r": lambda r, c: (-r, c), "refl_c": lambda r, c: (r, -c)}
norm = lambda cs: frozenset((r - min(x for x, _ in cs), c - min(y for _, y in cs)) for r, c in cs)
M = lambda f, cs: norm([f(r, c) for r, c in cs])
q = lambda cs, g: norm([(r >> g, c >> g) for r, c in norm(cs)])
def degen(cs):
    if len(cs) < 3: return True
    h = max(r for r, _ in cs) + 1; w = max(c for _, c in cs) + 1
    return len(cs) >= h * w
chars = []
for a in sorted(p for p in EVAL.iterdir() if p.is_dir())[:20]:
    c = sorted(p for p in a.iterdir() if p.is_dir())[0]; d = sorted(c.glob("*.txt"))
    chars.append((raster(strokes(d[0])), raster(strokes(d[1]))))
pre = json.load(open(ROOT / "evaluation/reports/diminfer_grain_heldout_v1_20261007.json"))
post = json.load(open(ROOT / "evaluation/reports/diminfer_grain_heldout_v1_1_degenerate_guard_20261007.json"))
lost = []
for r0, r1 in zip(pre["rows"], post["rows"]):
    if r0["cond"] == "drawer" and r0["ladder"]["recognized"] and not r1["ladder"]["recognized"]:
        i = [x for x in pre["chars"]].index(r0["char"]); g = r0["ladder"]["grain"]
        goal = q(M(MAPS[r0["map"]], chars[i][1]), g)
        h = max(r for r, _ in goal) + 1; w = max(c for _, c in goal) + 1
        lost.append({"char": r0["char"], "map": r0["map"], "grain": g, "cells": len(goal), "bbox": [h, w], "degenerate": degen(goal)})
risk = {"degenerate": [0, 0], "nondegenerate": [0, 0]}
for i, (A, _) in enumerate(chars):
    for j, (B, _) in enumerate(chars):
        if i == j: continue
        for f in MAPS.values():
            for g in (1, 2):
                goal = q(M(f, B), g); target = M(f, q(A, g))
                k = "degenerate" if degen(goal) else "nondegenerate"
                risk[k][1] += 1; risk[k][0] += goal == target
rep = {"lost_drawer_recognitions": lost, "n_lost": len(lost), "lost_all_degenerate": all(x["degenerate"] for x in lost),
       "cross_character_false_match": {k: {"matches": v[0], "pairs": v[1], "rate": v[0] / max(v[1], 1)} for k, v in risk.items()}}
OUT.write_text(json.dumps(rep, indent=1) + "\n")
print(json.dumps({k: rep[k] for k in ("n_lost", "lost_all_degenerate", "cross_character_false_match")}, indent=1))
print([(x["grain"], x["cells"], x["bbox"]) for x in lost])
