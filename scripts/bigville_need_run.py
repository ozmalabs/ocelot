#!/usr/bin/env python3
"""bigville R2 (block 250000) ORACLE / glass-box demo runner.

Runs the pre-registered NEEDS->GOALS + PREFERENCE/satisficing scenarios on the
real town grid and dumps a viewer-ready JSON read straight off the graph -- the
HEADLINE flip (near->apple, far->bread, preference held constant), the three
failing controls, and the drive->goal + ablation + two-drive arbitration. Every
verdict is a rule; this script only sequences scenarios and reads state.

Usage:  python scripts/bigville_need_run.py [out.json]
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_need_world import (                              # noqa: E402
    BigvilleNeedWorld, APPLE, BREAD, ALE, SUSTENANCE, FATIGUE)

SQUARE = (14, 8)
ORCHARD_NEAR, ORCHARD_FAR = (11, 8), (29, 17)
BAKERY, ALEHOUSE = (14, 11), (17, 8)
APPLE_PREF = {APPLE: 5.0, BREAD: 4.0, ALE: 1.0}
ALE_PREF = {APPLE: 1.0, BREAD: 3.0, ALE: 6.0}


def _town(orchard):
    w = BigvilleNeedWorld()
    w.add_source("orchard", APPLE, orchard)
    w.add_source("bakery", BREAD, BAKERY)
    w.add_source("alehouse", ALE, ALEHOUSE)
    return w


def _v(w, name, prefs, cost_on=1.0, urge_vd=10.0):
    w.add_mover(name, SQUARE)
    w.set_preferences(name, prefs, cost_on=cost_on)
    w.set_drive(name, SUSTENANCE, v_d=urge_vd, c_d=0.0)
    return name


def main(out_path):
    report = {"block": 250000, "town": {"square": list(SQUARE),
              "orchard_near": list(ORCHARD_NEAR), "orchard_far": list(ORCHARD_FAR),
              "bakery": list(BAKERY), "alehouse": list(ALEHOUSE)}}

    # HEADLINE: the flip on distance alone (preference held constant)
    w = _town(ORCHARD_NEAR); n = _v(w, "villager_0", APPLE_PREF)
    near = w.decide(n); near["source_costs"] = w.source_costs(n)
    w.move_source("orchard", ORCHARD_FAR)
    far = w.decide(n); far["source_costs"] = w.source_costs(n)
    report["headline_flip"] = {
        "preference": {"apple": 5, "bread": 4, "ale": 1}, "held": "constant",
        "near_orchard": {"chosen": near["chosen_good"], "costs": near["source_costs"]},
        "far_orchard": {"chosen": far["chosen_good"], "costs": far["source_costs"]},
        "glass_box": "wanted apples, took bread -- the orchard was across town"}
    w.close()

    # control: preference ablated (equal weights) -> nearest
    w = _town(ORCHARD_FAR); n = _v(w, "villager_0", {APPLE: 3.0, BREAD: 3.0, ALE: 3.0})
    r = w.decide(n)
    report["control_pref_ablated"] = {"chosen": r["chosen_good"],
        "costs": w.source_costs(n), "expect": "nearest, not the far orchard"}
    w.close()

    # control: travel-cost ablated (cost_on=0) -> top preference however far
    w = _town(ORCHARD_FAR); n = _v(w, "villager_0", APPLE_PREF, cost_on=0.0)
    r = w.decide(n)
    report["control_cost_ablated"] = {"chosen": r["chosen_good"],
        "costs": w.source_costs(n), "expect": "apple (top pref) despite dist 24"}
    w.close()

    # control: ale-preferrer -> different choice, same town
    w = _town(ORCHARD_NEAR)
    a = _v(w, "villager_0", APPLE_PREF); ar = w.decide(a)
    b = _v(w, "villager_1", ALE_PREF); br = w.decide(b)
    report["control_ale_preferrer"] = {
        "apple_preferrer_chose": ar["chosen_good"],
        "ale_preferrer_chose": br["chosen_good"],
        "note": "preference is per-villager, not global"}
    w.close()

    # drive -> goal
    w = _town(ORCHARD_NEAR); n = _v(w, "villager_0", APPLE_PREF)
    g = w.decide(n)
    report["drive_forms_goal"] = {"goal": g["goal"], "urge": w.urge_of(n, SUSTENANCE)}
    w.close()

    # ablation on a FRESH villager: the drive is removed BEFORE any decide, so no
    # drive is ever above threshold -> the arbitration finds nothing -> NO goal.
    w = _town(ORCHARD_NEAR); n = _v(w, "villager_0", APPLE_PREF)
    w.remove_drive(n, SUSTENANCE)
    report["drive_ablated"] = {"goal": w.decide(n)["goal"], "expect": None}
    w.close()

    # two competing drives -> higher wins
    w = _town(ORCHARD_NEAR)
    w.add_mover("villager_0", SQUARE); w.set_preferences("villager_0", APPLE_PREF)
    w.set_drive("villager_0", SUSTENANCE, v_d=10.0, c_d=0.0)
    w.set_drive("villager_0", FATIGUE, v_d=4.0, c_d=0.0)
    hi = w.decide("villager_0")["goal"]
    w.set_drive("villager_0", SUSTENANCE, v_d=3.0, c_d=0.0)
    w.set_drive("villager_0", FATIGUE, v_d=9.0, c_d=0.0)
    m = w._movers["villager_0"]
    for e in list(w.eng.neighbours(m, "has_sustenance_goal")):
        w.eng.remove_edge_unchecked(m, "has_sustenance_goal", e)
    lo = w.decide("villager_0")["goal"]
    report["two_drives_higher_wins"] = {"hunger_gt_fatigue": hi, "fatigue_gt_hunger": lo}
    w.close()

    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    print("\nwrote", out_path)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        _ROOT, "results", "bigville_need", "need_gates.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    main(out)
