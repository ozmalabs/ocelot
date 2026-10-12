#!/usr/bin/env python3
"""Panel A of SUBSTRATE_VARIATION_CREDIT_RECENCY_V1_1_PREREG_20261007.md: sequential shift."""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(Path(__file__).resolve().parent)]
from variation_credit_adoption_v1 import DISTS, menu, draw, score  # noqa: E402

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_RECENCY_V1_1_PREREG_20261007.md"
OUT = ROOT / "evaluation/reports/variation_credit_shift_v1_1_20261007.json"
SEED, REPS = 20261007, 30
PAIRS = [(1, 2), (3, 4), (5, 6), (7, 8)]
PHASES = [("A", 8), ("B", 8), ("A2", 4)]
ARMS = {"frozen": dict(use_credit=False), "unbounded": dict(use_credit=True, window=None),
        "window4": dict(use_credit=True)}
SOURCES = ["seeds/variation_ops.json", "seeds/variation_credit.json", "domains/variation_credit_lab.py",
           "scripts/gen_variation_credit_seed.py", "evaluation/substrate_capability/variation_credit_shift_v1_1.py",
           "evaluation/substrate_capability/variation_credit_adoption_v1.py",
           "runners/dsl/python/substrate_rs/_native.abi3.so", str(PREREG.relative_to(ROOT))]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def boot(d1, d2):
    return lambda: None


def ci(x, seed):
    x = np.asarray(x, float)
    b = x[np.random.default_rng(seed).integers(0, len(x), (10_000, len(x)))].mean(1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {"mean": float(x.mean()), "ci": [float(lo), float(hi)], "n": len(x)}


def main():
    from domains.variation_credit_lab import VariationLab
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    before = {p: sha(p) for p in SOURCES}
    dist = {d: (k, m) for d, k, m in DISTS}
    t0 = time.time()
    rows = []
    for a, b in PAIRS:
        kind = dist[a][0]
        assert kind == dist[b][0]
        M = len(menu(kind))
        for rep in range(REPS):
            rng = random.Random(SEED * 1000 + a * 100 + rep)
            seq = []
            for ph, n in PHASES:
                d = a if ph != "B" else b
                seq += [(ph, draw(rng, kind, dist[d][1])) for _ in range(n)]
            row = {"pair": [a, b], "rep": rep, "fixes": [f for _, f in seq]}
            for arm, kw in ARMS.items():
                lab = VariationLab(credit=True, **kw)
                scores = {ph: [] for ph, _ in PHASES}
                for ph, fix in seq:
                    scores[ph].append(score(lab.episode(kind, fix, budget=M), fix, M))
                row[arm] = {ph: float(np.mean(v)) for ph, v in scores.items()}
                row[arm]["all"] = float(np.mean([s for v in scores.values() for s in v]))
            rows.append(row)
        print(f"pair d{a}->d{b}", {arm: round(np.mean([r[arm]["B"] for r in rows if r["pair"] == [a, b]]), 1) for arm in ARMS}, flush=True)
    def delta(x, y, ph, sub=None):
        rs = [r for r in rows if sub is None or r["pair"] == sub]
        return [r[x][ph] - r[y][ph] for r in rs]
    g1 = ci(delta("window4", "unbounded", "B"), SEED + 1)
    g2 = ci(delta("window4", "frozen", "B"), SEED + 2)
    g3 = ci(delta("window4", "frozen", "all"), SEED + 3)
    gates = {"G1_adaptation_window_beats_unbounded": g1["mean"] > 0 and g1["ci"][0] > 0,
             "G2_no_shift_harm_vs_frozen": g2["ci"][1] > 0,
             "G3_whole_sequence_benefit_vs_frozen": g3["ci"][0] > 0,
             "sources_stable": before == {p: sha(p) for p in SOURCES}}
    per_pair = {}
    for a, b in PAIRS:
        per_pair[f"d{a}->d{b}"] = {ph: {arm: float(np.mean([r[arm][ph] for r in rows if r["pair"] == [a, b]])) for arm in ARMS}
                                    for ph in ("A", "B", "A2", "all")}
    rep = {"schema": "VariationCreditShiftV1_1", "protocol_sha256": sha(str(PREREG.relative_to(ROOT))),
           "sources_sha256": before, "elapsed_seconds": time.time() - t0, "rows": rows,
           "G1": g1, "G2": g2, "G3": g3, "per_pair": per_pair, "gates": gates, "all_pass": all(gates.values())}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"G1": g1, "G2": g2, "G3": g3, "gates": gates}, indent=1))
    print(json.dumps(per_pair, indent=1))
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
