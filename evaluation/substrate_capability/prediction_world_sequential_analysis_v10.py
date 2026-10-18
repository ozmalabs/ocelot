#!/usr/bin/env python3
"""The pre-declared sequential analysis for the v10 protocol (2026-10-10):
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_V10_20261010.md.

Two looks (set A = draws 0-5; A+B pooled = draws 0-11), Pocock boundary
p < 0.0294 per look. Cost per run = final surprise + retention harm + 0.001 x
experiments. Two tests per comparison, both pre-declared:
  sign   two-sided exact sign test on per-pair cost (ties dropped)
  mean   two-sided paired sign-flip permutation test on the mean per-pair cost
         difference (200,000 random flips, fixed RNG seed 20261010)
Magnitudes are part of the decision, not only counts.

Usage: <this> <report A> [<report B>]
"""
import json
import math
import random
import sys

BOUNDARY = 0.0294
COST = lambda r: r["final_surprise"] + r["retention_harm"] + 0.001 * r["experiments"]


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def perm_test(diffs, n=200_000, seed=20261010):
    obs = abs(sum(diffs))
    if obs == 0:
        return 1.0
    rnd = random.Random(seed)
    hits = 0
    for _ in range(n):
        if abs(sum(d if rnd.random() < 0.5 else -d for d in diffs)) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (n + 1)


def compare(rows, a, b, key=COST):
    idx = {(r["draw"], r["seed_base"], r["level"]): r for r in rows if r["arm"] == b}
    d = [key(r) - key(idx[(r["draw"], r["seed_base"], r["level"])]) for r in rows if r["arm"] == a]
    w = sum(1 for x in d if x < -1e-9)
    l = sum(1 for x in d if x > 1e-9)
    return {"a": a, "b": b, "pairs": len(d), "a_better": w, "b_better": l, "ties": len(d) - w - l,
            "mean_diff": round(sum(d) / len(d), 5), "big_losses_gt_0.1": sum(1 for x in d if x > 0.1),
            "sign_p": round(sign_test(w, l), 6), "mean_p": round(perm_test(d), 6)}


FS = lambda r: r["final_surprise"]
RH = lambda r: r["retention_harm"]


ALL = lambda r: r["all_levels_mean"]


BLOWN = lambda r: r["retention_harm"] >= 1.0 or r["final_surprise"] >= 2.0


def hypotheses(rows):
    h15 = compare(rows, "on_trained_robust", "on_trained_plain", ALL)
    robust_rows = [r for r in rows if r["arm"] == "on_trained_robust"]
    h15["blowups_robust"] = sum(1 for r in robust_rows if BLOWN(r))
    h15["blowups_plain"] = sum(1 for r in rows if r["arm"] == "on_trained_plain" and BLOWN(r))
    idx = {(r["draw"], r["seed_base"], r["level"]): r for r in rows if r["arm"] == "on_trained_plain"}
    clean = [(r, idx[(r["draw"], r["seed_base"], r["level"])]) for r in robust_rows
             if not BLOWN(r) and not BLOWN(idx[(r["draw"], r["seed_base"], r["level"])])]
    h15["clean_pairs"] = len(clean)
    h15["clean_mean_final_diff"] = round(sum(x["final_surprise"] - y["final_surprise"] for x, y in clean) / len(clean), 5)
    h15["decided"] = (h15["mean_diff"] < 0 and h15["mean_p"] < BOUNDARY
                      and h15["blowups_robust"] <= len(robust_rows) // 100
                      and h15["clean_mean_final_diff"] <= 0.005)
    h3 = compare(rows, "on_trained_old", "on_naive_old", FS)
    h3["decided"] = (h3["mean_diff"] < 0 and h3["mean_p"] < BOUNDARY and h3["sign_p"] < BOUNDARY
                     and h3["a_better"] > h3["b_better"])
    h13 = compare(rows, "on_escalated_robust", "on_naive_robust", FS)
    h13["decided"] = (h13["mean_diff"] < 0 and h13["mean_p"] < BOUNDARY and h13["sign_p"] < BOUNDARY
                      and h13["a_better"] > h13["b_better"])
    return {"H15_robustness_view_removes_offsample_blowups": h15,
            "H3r_trained_beats_newborn_replication": h3,
            "H13r_escalated_robust_beats_newborn": h13,
            "reference_trained_robust_vs_old_final": compare(rows, "on_trained_robust", "on_trained_old", FS),
            "reference_trained_robust_vs_old_all_levels": compare(rows, "on_trained_robust", "on_trained_old", ALL),
            "reference_trained_robust_vs_newborn": compare(rows, "on_trained_robust", "on_naive_robust", FS),
            "reference_escalated_vs_trained_robust": compare(rows, "on_escalated_robust", "on_trained_robust", FS)}


def main():
    sets = [json.load(open(p)) for p in sys.argv[1:]]
    looks = []
    for n in range(1, len(sets) + 1):
        rows = [r for s in sets[:n] for r in s["rows"]]
        looks.append({"look": n, "hypotheses": hypotheses(rows)})
    per_set = [hypotheses(s["rows"]) for s in sets]
    verdict = {}
    for h in ("H15_robustness_view_removes_offsample_blowups", "H3r_trained_beats_newborn_replication",
              "H13r_escalated_robust_beats_newborn"):
        at = next((lk["look"] for lk in looks if lk["hypotheses"][h]["decided"]), None)
        verdict[h] = f"supported at look {at}" if at else ("not supported" if len(looks) == 2 else "undecided")
    print(json.dumps({"boundary": BOUNDARY, "looks": looks, "per_set": per_set, "verdict": verdict}, indent=1))


if __name__ == "__main__":
    main()
