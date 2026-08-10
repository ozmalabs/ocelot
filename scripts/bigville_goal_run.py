#!/usr/bin/env python3
"""bigville R8 (block 256000) RUN -- the SOUL layer as a glass-box cast story.

Instantiates a tiny cast, exercises the four gates through the world adapter
(orient / audit / relief / collapse), reads the verdicts off the GRAPH, and
writes results/bigville_goal/summary.json. Everything is a seed-rule decision;
this script is mechanical I/O (a run harness, not agent logic).

  * Ada holds a become-wealthy LIFE-GOAL -> her decision_value Argmax orients
    toward SAVE; ablate it -> LEISURE (the long-horizon bias was load-bearing).
  * Bob's DREAM is audited onto the UNGROUNDED side of the boundary; his
    life-goal onto the grounded side.
  * Cara is foreclosed (R7) -> aversive; her DREAM regulates her affect
    (temporary relief, material state unchanged); a dreamless twin has no valve.
  * Dan's dream COLLAPSES into leaving when the present turns unbearable; Eve's
    when a recruiter grounds a path; Fay's stays LATENT (resignation).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_goal_world import (                              # noqa: E402
    BigvilleGoalWorld, SAVE, LEISURE, AIM_WEALTH)
from worlds.bigville_time_world import DAY                            # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _world():
    w = BigvilleGoalWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=100000, salary=0, fair_rate_bp=500)
    return w


def run():
    out = {}

    # --- Ada: the life-goal orients (and the ablation) --------------------
    w = _world()
    P = _pool(w)
    w.make_soul("ada", P[10], coin=1000)
    w.add_choicepoint("ada")
    w.add_suboption("ada", SAVE, base_appeal=1.0, serves_aim=AIM_WEALTH)
    w.add_suboption("ada", LEISURE, base_appeal=2.0, serves_aim=0.0)
    w.set_life_goal("ada", aim=AIM_WEALTH, orient_weight=3.0)
    w.orient("ada")
    with_lg = w.chosen_subgoal_of("ada")
    w.ablate_life_goal("ada")
    w.orient("ada")
    ablated = w.chosen_subgoal_of("ada")
    out["G_life_goal_orients"] = {
        "chosen_with_life_goal": with_lg, "chosen_ablated": ablated,
        "SAVE": SAVE, "LEISURE": LEISURE,
        "pass": with_lg == SAVE and ablated == LEISURE}

    # --- Bob: the ungrounded audit ----------------------------------------
    w = _world()
    P = _pool(w)
    w.make_soul("bob", P[10], coin=100)
    w.set_life_goal("bob", aim=AIM_WEALTH, orient_weight=3.0)
    w.set_dream("bob", kind="join_navy")
    w.audit("bob")
    ds = w.dream_state("bob")
    out["G_dream_is_ungrounded"] = {
        "lifegoal_grounded_flag": w.lifegoal_grounded_of("bob"),
        "lifegoal_has_path": w.lifegoal_has_path("bob"),
        "dream_ungrounded": ds["ungrounded"],
        "dream_has_grounded_path": ds["has_grounded_path"],
        "pass": (w.lifegoal_grounded_of("bob") == 1 and w.lifegoal_has_path("bob")
                 and ds["ungrounded"] == 1 and not ds["has_grounded_path"])}

    # --- Cara: the dream regulates affect (HEADLINE) + dreamless twin -----
    def distressed(name, with_dream):
        w = _world()
        P = _pool(w)
        w.make_soul(name, P[10], coin=1000)
        w.attach_affect(name, concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
        w.add_house("h_%s" % name, 200, apprec=0)
        w.mortgage(name, "h_%s" % name, principal=500, payment=30, term=3)
        w.set_char(name, coin=0)
        for _ in range(5):
            w.period()
        if with_dream:
            w.set_dream(name, relief_valence=3.0, relief_arousal=2.0,
                        aversive_threshold=5.0, collapse_threshold=-100.0)
        return w

    wd = distressed("cara", True)
    v0 = wd.affect_state("cara")["valence"]
    a0 = wd.affect_state("cara")["arousal"]
    hb, bb = wd.homeless_of("cara"), wd.balance_of("cara")
    wd.invoke_relief("cara")
    v1 = wd.affect_state("cara")["valence"]
    a1 = wd.affect_state("cara")["arousal"]
    wn = distressed("cara", False)
    wn.invoke_relief("cara")
    v_dreamless = wn.affect_state("cara")["valence"]
    out["G_dream_regulates_affect"] = {
        "valence_distressed": v0, "valence_after_relief": v1,
        "arousal_distressed": a0, "arousal_after_relief": a1,
        "homeless_before": hb, "homeless_after": wd.homeless_of("cara"),
        "balance_before": bb, "balance_after": wd.balance_of("cara"),
        "invoked": wd.dream_state("cara")["invoked"],
        "valence_dreamless_twin": v_dreamless,
        "pass": (v1 > v0 and a1 < a0 and wd.homeless_of("cara") == hb
                 and wd.balance_of("cara") == bb and v_dreamless == v0 and v1 > v_dreamless)}

    # --- Dan / Eve / Fay: collapse (threshold / path) + latent control ----
    def with_affect(name, valence):
        w = _world()
        P = _pool(w)
        w.make_soul(name, P[10], coin=1000)
        w.attach_affect(name, concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=float(valence))
        return w

    wdan = with_affect("dan", 2.0)
    wdan.set_dream("dan", collapse_threshold=3.0, aversive_threshold=5.0)
    wdan.try_collapse("dan")
    weve = with_affect("eve", 5.0)
    weve.set_dream("eve", collapse_threshold=-100.0, aversive_threshold=5.0)
    weve.recruiter_arrives("eve")
    weve.try_collapse("eve")
    wfay = with_affect("fay", 2.0)
    wfay.set_dream("fay", collapse_threshold=-100.0, aversive_threshold=5.0)
    wfay.try_collapse("fay")
    out["G_dream_collapses"] = {
        "threshold": {"collapsed": wdan.dream_state("dan")["collapsed"],
                      "left": wdan.left_of("dan"),
                      "goals": wdan.action_goal_kinds("dan")},
        "path": {"collapsed": weve.dream_state("eve")["collapsed"],
                 "left": weve.left_of("eve"),
                 "goals": weve.action_goal_kinds("eve")},
        "latent_control": {"collapsed": wfay.dream_state("fay")["collapsed"],
                           "left": wfay.left_of("fay"),
                           "latent": wfay.dream_state("fay")["latent"],
                           "resigned": wfay.resigned_of("fay"),
                           "goals": wfay.action_goal_kinds("fay")},
        "pass": (wdan.left_of("dan") == 1 and wdan.action_goal_kinds("dan") == ["leave"]
                 and weve.left_of("eve") == 1 and weve.action_goal_kinds("eve") == ["leave"]
                 and wfay.left_of("fay") == 0 and wfay.dream_state("fay")["latent"] == 1
                 and wfay.action_goal_kinds("fay") == [])}

    out["all_pass"] = all(v.get("pass") for v in out.values() if isinstance(v, dict))
    return out


def main():
    res = run()
    dst = os.path.join(ROOT, "results", "bigville_goal")
    os.makedirs(dst, exist_ok=True)
    path = os.path.join(dst, "summary.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=2)
    print("wrote", path)
    print("all_pass:", res["all_pass"])
    for k, v in res.items():
        if isinstance(v, dict):
            print(" ", k, "->", "PASS" if v.get("pass") else "FAIL")


if __name__ == "__main__":
    main()
