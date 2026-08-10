#!/usr/bin/env python3
"""MEASUREMENT (block 265000, R17) -- runs each gate's arm + its pre-registered
control on the SEED-BOOTED BigvilleAffectWorld and writes the glass-box readout to
results/bigville_affect/summary.json. Deterministic (no RNG). Mechanical I/O only.

  python scripts/bigville_affect_measure.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from worlds.bigville_affect_world import BigvilleAffectWorld           # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402


def _world(day_range=28):
    w = BigvilleAffectWorld(day_range=day_range)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


def measure():
    out = {}

    # ---- G-affect-modulates-decision + falsifier + graded escalation ----
    w = _world(); P = _pool(w)
    w.make_villager("content", P[10])
    w.make_villager("griever", P[11]); w.set_affect("griever", grief_distress=8.0)
    w.make_villager("ab_content", P[12], affect_gain=0.0)
    w.make_villager("ab_griever", P[13], affect_gain=0.0); w.set_affect("ab_griever", grief_distress=8.0)
    graded = {}
    for i, d in enumerate((0.0, 2.0, 4.0, 6.0, 8.0)):
        nm = "gr%d" % i
        w.make_villager(nm, P[20 + i]); w.set_affect(nm, grief_distress=d)
        graded[str(d)] = {"code": w.decide(nm), "action": w.chosen_label_of(nm)}
    out["headline"] = {
        "coupled": {"content": w.decide("content"), "griever": w.decide("griever"),
                    "content_action": w.chosen_label_of("content"),
                    "griever_action": w.chosen_label_of("griever")},
        "affect_blind_ablation": {"content": w.decide("ab_content"),
                                  "griever": w.decide("ab_griever"),
                                  "note": "affect_gain=0 -> identical (work) = DIORAMA"},
        "graded_escalation": graded,
    }

    # ---- three grief sources ----
    w = _world(); P = _pool(w)
    w.make_villager("mourner", P[10]); w.make_villager("kin", P[11])
    w.endow_health("kin", health=50.0)
    w.bereave_by_death("mourner", "kin", 8.0)
    w.make_villager("dreamer", P[12]); w.suffer_failed_dream("dreamer", 6.0)
    w.make_villager("evicted", P[13]); w.suffer_foreclosure("evicted", 4.0)
    out["grief_sources"] = {
        "bereavement_R14": {"kin_dead": w.is_dead("kin"), "grief": w.grief_of("mourner"),
                            "action": w.chosen_label_of("mourner") if w.decide("mourner") else None},
        "failed_dream_R8": {"grief": w.grief_of("dreamer"), "action": w.chosen_label_of("dreamer") if w.decide("dreamer") else None},
        "foreclosure_R7": {"grief": w.grief_of("evicted"), "action": w.chosen_label_of("evicted") if w.decide("evicted") else None},
    }

    # ---- negative spiral (coupled) vs control (affect-blind) ----
    w = _world(); P = _pool(w)
    w.make_villager("coupled", P[10], coin=3.0); w.suffer_failed_dream("coupled", 6.0)
    w.make_villager("blind", P[40], coin=3.0, affect_gain=0.0); w.suffer_failed_dream("blind", 6.0)
    traj_c, traj_b = [], []
    for _ in range(6):
        w.live_period("coupled"); w.live_period("blind")
        traj_c.append([w.chosen_label_of("coupled"), round(w.grief_of("coupled"), 1), round(w.coin_of("coupled"), 1)])
        traj_b.append([w.chosen_label_of("blind"), round(w.grief_of("blind"), 1), round(w.coin_of("blind"), 1)])
    out["negative_spiral"] = {
        "coupled_trajectory": traj_c, "affect_blind_trajectory": traj_b,
        "coupled_conflict": w.conflict_of("coupled"),
        "note": "coupled spirals up to snap+conflict; ablated works, recovers, no spiral",
    }

    # ---- escapable by co-regulation vs breakdown ----
    w = _world(); P = _pool(w)
    for nm, cell in (("sup", P[10]), ("alone", P[60])):
        w.make_villager(nm, cell, coin=3.0); w.suffer_failed_dream(nm, 6.0); w.live_period(nm)
    reg_sup = w.support("sup", episodes=10)
    reg_alone = w.stress_alone("alone", episodes=10)
    for _ in range(5):
        w.live_period("sup"); w.live_period("alone")
    out["coregulation"] = {
        "regulation_supported": round(reg_sup, 3), "regulation_alone": round(reg_alone, 3),
        "final_grief_supported": round(w.grief_of("sup"), 1),
        "final_grief_alone": round(w.grief_of("alone"), 1),
        "final_action_supported": w.chosen_label_of("sup"),
        "final_action_alone": w.chosen_label_of("alone"),
        "note": "breakdown vs recovery = MEASURED function of support presence",
    }

    # ---- generational propagation vs ablation ----
    w = _world(); P = _pool(w)
    nat = dict(nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5)
    w.make_villager("gp_c", P[5]); w.suffer_failed_dream("gp_c", 8.0)
    w.make_villager("gp_a", P[6], gen_gain=0.0); w.suffer_failed_dream("gp_a", 8.0)
    pc = w.rear_child_of("gp_c", "child_c", P[50], episodes=8, **nat)
    pa = w.rear_child_of("gp_a", "child_a", P[70], episodes=8, **nat)
    out["generational"] = {
        "child_of_grieving_parent_priors": {k: round(v, 3) for k, v in pc.items()},
        "child_ablated_coupling_priors": {k: round(v, 3) for k, v in pa.items()},
        "child_of_grieving_window": w.window_of("child_c"),
        "child_ablated_window": w.window_of("child_a"),
        "note": "grieving parent -> child NARROWS + priors DOWN; gen_gain=0 -> no transfer",
    }

    return out


def main():
    res = measure()
    dst = os.path.join(ROOT, "results", "bigville_affect")
    os.makedirs(dst, exist_ok=True)
    path = os.path.join(dst, "summary.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    print("wrote", os.path.relpath(path, ROOT))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
