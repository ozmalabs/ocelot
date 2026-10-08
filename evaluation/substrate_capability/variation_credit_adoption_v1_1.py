#!/usr/bin/env python3
"""Held-out adoption gate for the outcome-credited variation policy (WP2/WP4).

Protocol: docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_RECENCY_V1_1_PREREG_20261007.md
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_RECENCY_V1_1_PREREG_20261007.md"
OUT = ROOT / "evaluation/reports/variation_credit_adoption_v1_1_window4_20261007.json"
SEED = 20261006
TRAIN, HELD = 8, 30
FAMILIES = ["knob_edit", "datum_feedback_rule", "shape_mint", "rule_literal_edit", "reply_ablation",
            "structural_edit", "threshold_shift"]
DISTS = [
    (1, "reply_fix", {"threshold_shift": 0.8}), (2, "reply_fix", {"structural_edit": 0.8}),
    (3, "performance", {"reply_ablation": 0.9}), (4, "performance", {"rule_literal_edit": 0.7}),
    (5, "comprehension", {"shape_mint": 0.8}), (6, "comprehension", {"threshold_shift": 0.6}),
    (7, "instruction", {"knob_edit": 0.8}), (8, "instruction", {"structural_edit": 0.9}),
    (9, "reply_fix", {"threshold_shift": 0.5, "structural_edit": 0.5}), (10, "performance", {}),
    (11, "comprehension", {"knob_edit": 0.9}), (12, "instruction", {}),
]
SOURCES = ["seeds/variation_ops.json", "seeds/variation_credit.json", "domains/variation_credit_lab.py",
           "domains/reflective_faculty.py", "scripts/gen_variation_credit_seed.py",
           "evaluation/substrate_capability/variation_credit_adoption_v1_1.py",
           "runners/dsl/python/substrate_rs/_native.abi3.so", str(PREREG.relative_to(ROOT))]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def menu(kind):
    return FAMILIES + (["cue_set_edit"] if kind == "instruction" else [])


def draw(rng, kind, mass):
    fams = menu(kind)
    rest = [f for f in fams if f not in mass]
    p_rest = (1 - sum(mass.values())) / len(rest) if rest else 0
    probs = [mass.get(f, p_rest) for f in fams]
    return rng.choices(fams, probs)[0]


def lab_after(training, use_credit):
    from domains.variation_credit_lab import VariationLab
    lab = VariationLab(credit=True, use_credit=use_credit)
    for kind, fix in training:
        lab.episode(kind, fix, budget=len(menu(kind)))
    return lab


def history(training):
    """Training is run once under the ADOPT policy; the trial log it produced
    is what both arms then carry (the frozen arm credits the same outcomes,
    it just does not use them)."""
    lab = lab_after(training, True)
    trials = []
    for n in lab.s.nodes("SeedDelta"):
        a = lab.s.node(n)["attrs"]
        trials.append((a["concern_key"], a["variation_op"], a["judged_outcome"]))
    return trials


def replay(trials, kinds, use_credit):
    from domains.variation_credit_lab import VariationLab
    lab = VariationLab(credit=True, use_credit=use_credit)
    made = {}
    for key, op, out in trials:
        if key not in made:
            made[key] = lab.concern(kinds[key])
        lab.trial(made[key], op, out)
    return lab


def digest(lab):
    return hashlib.sha256(json.dumps(lab.s.graph_to_dict(), sort_keys=True, default=str).encode()).hexdigest()


def score(tried, fix, M):
    if not tried or tried[-1] != fix:
        return 0.0
    return 100.0 * (1 - (len(tried) - 1) / (M - 1))


def stats(diffs, rng_seed):
    d = np.asarray(diffs, float)
    rng = np.random.default_rng(rng_seed)
    boots = d[rng.integers(0, len(d), (10_000, len(d)))].mean(1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    signs = rng.choice([-1.0, 1.0], (100_000, len(d)))
    perm = (signs * np.abs(d)).mean(1)
    obs = d.mean()
    return {"delta": float(obs), "sd": float(d.std(ddof=1)), "ci": [float(lo), float(hi)],
            "p_improve": float((np.sum(perm >= obs) + 1) / (len(perm) + 1)),
            "p_harm": float((np.sum(perm <= obs) + 1) / (len(perm) + 1))}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def evaluate(d_id, kind, mass, trials, train_kinds):
    rng = random.Random(SEED * 100 + d_id)
    M = len(menu(kind))
    pre_digest = digest(replay(trials, train_kinds, False))
    rows = []
    for i in range(HELD):
        fix = draw(rng, kind, mass)
        res = {}
        for arm, uc in (("pre", False), ("adopt", True)):
            lab = replay(trials, train_kinds, uc)
            tried = lab.episode(kind, fix, budget=M)
            res[arm] = {"tried": tried, "score": score(tried, fix, M)}
        rows.append({"fix": fix, **res})
    # rollback: the candidate snapshot with use_credit restored is byte-identical to pre
    cand = replay(trials, train_kinds, True)
    for p in cand.s.nodes("VariationPolicy"):
        cand.s.set_attr(p, "use_credit", 0)
    return rows, pre_digest, digest(cand) == pre_digest


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    before = {p: sha(p) for p in SOURCES}
    t0 = time.time()
    dists = []
    for d_id, kind, mass in DISTS:
        rng = random.Random(SEED * 1000 + d_id)
        training = [(kind, draw(rng, kind, mass)) for _ in range(TRAIN)]
        trials = history(training)
        kinds = {f"concern_{i + 1}": kind for i in range(TRAIN)}
        rows, pre_digest, rollback_ok = evaluate(d_id, kind, mass, trials, kinds)
        diffs = [r["adopt"]["score"] - r["pre"]["score"] for r in rows]
        st = stats(diffs, SEED + d_id)
        dists.append({"d": d_id, "kind": kind, "mass": mass, "training": training, "trials": trials,
                      "rows": rows, "diffs": diffs, "pre_mean": float(np.mean([r["pre"]["score"] for r in rows])),
                      "adopt_mean": float(np.mean([r["adopt"]["score"] for r in rows])),
                      "rollback_byte_identical": rollback_ok, "pre_digest": pre_digest, **st})
        print(f"d{d_id} {kind:13s} pre={dists[-1]['pre_mean']:.1f} adopt={dists[-1]['adopt_mean']:.1f} delta={st['delta']:+.1f} ci=[{st['ci'][0]:.1f},{st['ci'][1]:.1f}]", flush=True)
    hi = holm([d["p_improve"] for d in dists])
    hh = holm([d["p_harm"] for d in dists])
    for d, a, b in zip(dists, hi, hh):
        d["p_improve_holm"], d["p_harm_holm"] = a, b
        if d["delta"] >= 5 and d["ci"][0] > 0 and a <= 0.05:
            d["class"] = "improve"
        elif d["delta"] <= -5 and d["ci"][1] < 0 and b <= 0.05:
            d["class"] = "harm"
        else:
            d["class"] = "inconclusive"
    # aggregate: resample distributions and their pairs
    rng = np.random.default_rng(SEED)
    D = np.array([d["diffs"] for d in dists])
    agg = []
    for _ in range(10_000):
        ds = rng.integers(0, len(D), len(D))
        agg.append(np.mean([D[j][rng.integers(0, HELD, HELD)].mean() for j in ds]))
    agg_mean = float(D.mean(1).mean())
    agg_lo = float(np.percentile(agg, 2.5))

    # descriptive interference / recovery (same kind reply_fix: d1 then d2)
    rng1, rng2 = random.Random(SEED * 1000 + 1), random.Random(SEED * 1000 + 2)
    tr1 = [("reply_fix", draw(rng1, "reply_fix", DISTS[0][2])) for _ in range(TRAIN)]
    tr2 = [("reply_fix", draw(rng2, "reply_fix", DISTS[1][2])) for _ in range(TRAIN)]
    trials12 = history(tr1 + tr2)
    kinds12 = {f"concern_{i + 1}": "reply_fix" for i in range(2 * TRAIN)}
    rows_after, _, _ = evaluate(1, "reply_fix", DISTS[0][2], trials12, kinds12)
    trials1 = history(tr1)
    rows_shift, _, _ = evaluate(2, "reply_fix", DISTS[1][2], trials1, {f"concern_{i + 1}": "reply_fix" for i in range(TRAIN)})
    extras = {"interference_d1_after_d1_then_d2": {
                  "adopt_mean": float(np.mean([r["adopt"]["score"] for r in rows_after])),
                  "pre_mean": float(np.mean([r["pre"]["score"] for r in rows_after]))},
              "recovery_d2_after_d1_only": {
                  "adopt_mean": float(np.mean([r["adopt"]["score"] for r in rows_shift])),
                  "pre_mean": float(np.mean([r["pre"]["score"] for r in rows_shift]))}}
    after = {p: sha(p) for p in SOURCES}
    classes = [d["class"] for d in dists]
    gates = {"improve_at_least_8": classes.count("improve") >= 8, "zero_harm": classes.count("harm") == 0,
             "aggregate_delta_ge_5": agg_mean >= 5, "aggregate_lower_ci_gt_0": agg_lo > 0,
             "non_improve_rollback_byte_identical": all(d["rollback_byte_identical"] for d in dists if d["class"] != "improve"),
             "sources_stable": before == after}
    rep = {"schema": "VariationCreditAdoptionV1_1Window4", "protocol_sha256": sha(str(PREREG.relative_to(ROOT))),
           "sources_sha256": before, "seed": SEED, "elapsed_seconds": time.time() - t0,
           "distributions": dists, "classes": classes, "aggregate": {"mean_delta": agg_mean, "lower_ci": agg_lo},
           "extras": extras, "gates": gates, "all_pass": all(gates.values())}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"classes": classes, "aggregate": rep["aggregate"], "gates": gates, "extras": extras}, indent=1))
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
