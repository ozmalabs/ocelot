#!/usr/bin/env python3
"""The pre-declared sequential analysis for the v5 protocol (2026-10-10):
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_V5_20261010.md.

Two looks over draw sets from one draw hash: look 1 = draws 0-5, look 2 =
draws 0-11 (pooled). Pocock boundary: a hypothesis is decided at a look when
its pooled two-sided exact sign test has p < 0.0294 (overall alpha 0.05 over
two looks), together with its non-inferiority conditions. A hypothesis
decided at look 1 stays decided; one not decided at look 2 is not supported.
Also reported per draw set, so a pooled result carried by one set shows.

Usage: <this> <report_d0-6.json> [<report_d6-12.json>]
"""
import json
import math
import sys

BOUNDARY = 0.0294


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def pairs(rows, a, b):
    idx = {(r["draw"], r["seed_base"], r["level"]): r for r in rows if r["arm"] == b}
    return [(r, idx[(r["draw"], r["seed_base"], r["level"])]) for r in rows if r["arm"] == a]


def compare(ps, key):
    w = sum(1 for x, y in ps if key(x) < key(y) - 1e-9)
    l = sum(1 for x, y in ps if key(x) > key(y) + 1e-9)
    d = sum(key(x) - key(y) for x, y in ps) / len(ps)
    return {"a_better": w, "b_better": l, "ties": len(ps) - w - l, "mean_diff": round(d, 4),
            "p": round(sign_test(w, l), 6)}


FS = lambda r: r["final_surprise"]
RH = lambda r: r["retention_harm"]
EX = lambda r: r["experiments"]
COST = lambda r: r["final_surprise"] + r["retention_harm"] + 0.001 * r["experiments"]


def hypotheses(rows):
    out = {}
    c = compare(pairs(rows, "on_trained", "on_naive"), FS)
    out["H3_trained_beats_newborn"] = {"primary": c, "decided": c["p"] < BOUNDARY and c["a_better"] > c["b_better"]}
    ps = pairs(rows, "on_trained", "on_trained_reset")
    c, ni = compare(ps, EX), compare(ps, FS)
    big = sum(1 for x, y in ps if x["final_surprise"] > y["final_surprise"] + 0.1)
    out["H4_kind_aware_record_cheaper_and_safe"] = {
        "primary": c, "noninferiority_final_surprise": ni, "big_losses": big, "big_losses_allowed": len(ps) // 100,
        "decided": (c["p"] < BOUNDARY and c["a_better"] > c["b_better"] and ni["mean_diff"] <= 0.005
                    and big <= len(ps) // 100)}
    c = compare(pairs(rows, "on_trained_meta", "on_trained"), COST)
    out["H5_own_policy_rounds_pay"] = {"primary": c, "decided": c["p"] < BOUNDARY and c["a_better"] > c["b_better"]}
    ps = pairs(rows, "on_trained", "on_trained_noexperts")
    c, rh = compare(ps, FS), compare(ps, RH)
    out["H6_experts_help"] = {"primary": c, "retention_harm": rh,
                              "decided": c["p"] < BOUNDARY and c["a_better"] > c["b_better"] and rh["mean_diff"] <= 0.01}
    return out


def main():
    sets = [json.load(open(p)) for p in sys.argv[1:]]
    looks = []
    for n in range(1, len(sets) + 1):
        rows = [r for s in sets[:n] for r in s["rows"]]
        looks.append({"look": n, "draws": sorted({r["draw"] for r in rows}), "hypotheses": hypotheses(rows)})
    per_set = [{"draws": sorted({r["draw"] for r in s["rows"]}), "hypotheses": hypotheses(s["rows"])} for s in sets]
    verdict = {}
    for h in looks[0]["hypotheses"]:
        at = next((lk["look"] for lk in looks if lk["hypotheses"][h]["decided"]), None)
        verdict[h] = f"supported at look {at}" if at else ("not supported" if len(looks) == 2 else "undecided")
    print(json.dumps({"boundary": BOUNDARY, "looks": looks, "per_set": per_set, "verdict": verdict}, indent=1))


if __name__ == "__main__":
    main()
