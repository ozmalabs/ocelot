#!/usr/bin/env python3
"""bigville R6 (block 254000) -- GLASS-BOX demonstration of DYNAMIC SKILL.

Runs the four pre-registered gates end to end on the bigville grid and dumps every
number to results/bigville_skill/summary.json (read straight off the graph -- no
narration). Story: a FARMER breaks the FISHERMAN's fish-supply monopoly by LEARNING
to fish -- solo (slow), taught (fast, if the fisherman is WILLING), or -- when the
fisherman REFUSES to train a rival -- only if a powerful John COERCES him, and even
then the coerced lesson is SABOTAGED (degraded, stated!=held).

Every learn/teach/coerce/sabotage decision is a seed RULE; this script only arms
one-shots, wires edges, co-locates, ticks and reads.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_skill_world import BigvilleSkillWorld, FISHING, FISH, BAIT  # noqa: E402
from worlds.bigville_time_world import DAY                                       # noqa: E402

FARM_CELL, FISH_CELL = (2, 2), (2, 4)
OUT = os.path.join(_ROOT, "results", "bigville_skill")


def yield_gap(farmer_skill, fisher_skill):
    w = BigvilleSkillWorld(day_range=16)
    w.set_phase(DAY)
    w.make_learner("farmer", FARM_CELL)
    w.make_learner("fisher", FISH_CELL)
    if farmer_skill is not None:
        w.set_learnable_skill("farmer", FISHING, farmer_skill)
    w.set_learnable_skill("fisher", FISHING, fisher_skill)
    w.add_shop("fs_farm", good=FISH, price=3, cell=FARM_CELL, keeper="farmer",
               activity=FISHING, input_good=BAIT, stock=0, input_qty=9)
    w.add_shop("fs_fish", good=FISH, price=3, cell=FISH_CELL, keeper="fisher",
               activity=FISHING, input_good=BAIT, stock=0, input_qty=9)
    w.set_hours(1)
    w.refresh_open()
    return w.yield_of("fs_farm"), w.yield_of("fs_fish")


def practice_curve(learn_rate, steps=6):
    w = BigvilleSkillWorld(day_range=16)
    w.set_phase(DAY)
    w.make_learner("farmer", FARM_CELL)
    w.set_learnable_skill("farmer", FISHING, 1.0)
    w.set_skill_attr("farmer", learn_rate=learn_rate)
    curve = [round(w.skill_level("farmer", FISHING), 4)]
    for _ in range(steps):
        w.practice("farmer", FISHING)
        curve.append(round(w.skill_level("farmer", FISHING), 4))
    return curve


def teach_curve(is_rival, coercer_power=None, steps=6):
    w = BigvilleSkillWorld(day_range=16)
    w.set_phase(DAY)
    w.make_learner("farmer", FARM_CELL)
    w.make_learner("fisher", FISH_CELL)
    w.set_learnable_skill("farmer", FISHING, 1.0)
    w.set_learnable_skill("fisher", FISHING, 8.0)
    w.set_skill_attr("farmer", learn_rate=0.3, is_rival=float(is_rival))
    w.set_skill_attr("fisher", teach_benevolence=2.0, rival_weight=5.0,
                     teach_rate=0.5, sabotage_rate=0.12, power=1.0)
    w.arrange_teaching("fisher", "farmer", FISHING)
    if coercer_power is not None:
        w.make_learner("john", FARM_CELL)
        w.set_skill_attr("john", power=coercer_power)
        w.wire_coercion("john", "fisher")
        w.coerce("john", "fisher")
    curve = [round(w.skill_level("farmer", FISHING), 4)]
    for _ in range(steps):
        w.teach("farmer")
        curve.append(round(w.skill_level("farmer", FISHING), 4))
    return w, curve


def main():
    os.makedirs(OUT, exist_ok=True)
    R = {}

    # --- G-skill-scales-yield -------------------------------------------------
    yf, yF = yield_gap(1.0, 5.0)
    ea, eb = yield_gap(3.0, 3.0)        # ablation: equalized skill
    oa, ob = yield_gap(None, 5.0)       # off-specialty: farmer has no skill
    R["G_skill_scales_yield"] = dict(
        farmer_yield=yf, fisher_yield=yF, gap=yF - yf,
        ablation_equalized=dict(farmer=ea, fisher=eb, equal=(ea == eb)),
        off_specialty_farmer_yield=oa)

    # --- G-learning-by-doing --------------------------------------------------
    solo = practice_curve(0.3, steps=6)
    flat = practice_curve(0.0, steps=6)
    gains = [round(solo[i + 1] - solo[i], 4) for i in range(len(solo) - 1)]
    R["G_learning_by_doing"] = dict(
        solo_curve=solo, per_step_gains=gains,
        strictly_diminishing=all(gains[i] > gains[i + 1] for i in range(len(gains) - 1)),
        ablation_flat_curve=flat, ablation_is_flat=(len(set(flat)) == 1))

    # --- G-teaching -----------------------------------------------------------
    _wt, taught = teach_curve(is_rival=0, steps=6)                 # willing
    wr, refused = teach_curve(is_rival=1, steps=6)                 # rival, refused
    wc, coerced = teach_curve(is_rival=1, coercer_power=9.0, steps=6)   # coerced
    ww, weak = teach_curve(is_rival=1, coercer_power=0.5, steps=6)      # weak coercer
    R["G_teaching"] = dict(
        solo_curve=solo,
        willing_curve=taught,
        taught_dominates_solo=all(taught[i] >= solo[i] for i in range(len(solo)))
        and taught[-1] > solo[-1],
        willing_single_gain=round(taught[1] - taught[0], 4),
        solo_single_gain=round(solo[1] - solo[0], 4),
        rival_refused_curve=refused,
        rival_refused_outcome=wr.teach_outcome_of("farmer"),
        rival_no_transfer=(refused[0] == refused[-1]),
        coerced_curve=coerced,
        coerced_flag=wc.coerced_of("farmer"),
        coerced_outcome=wc.teach_outcome_of("farmer"),
        coerced_single_gain=round(coerced[1] - coerced[0], 4),
        sabotage_stated_rate=wc.stated_rate_of("farmer"),
        sabotage_held_rate=wc.held_rate_of("farmer"),
        sabotage_stated_minus_held=wc.stated_minus_held("farmer"),
        coerced_degraded_vs_willing=(round(coerced[1] - coerced[0], 4)
                                     < round(taught[1] - taught[0], 4)),
        weak_coercer_curve=weak,
        weak_coercer_flag=ww.coerced_of("farmer"),
        weak_coercer_no_transfer=(weak[0] == weak[-1]))

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(R, f, indent=2)

    # glass-box console read-off
    print("=== BIGVILLE R6 — DYNAMIC SKILL (glass-box) ===")
    g = R["G_skill_scales_yield"]
    print("HEADLINE  farmer fishing yield=%.1f  fisherman=%.1f  gap=%.1f"
          % (g["farmer_yield"], g["fisher_yield"], g["gap"]))
    print("  ablate skill (equalized): %.1f == %.1f -> %s"
          % (g["ablation_equalized"]["farmer"], g["ablation_equalized"]["fisher"],
             g["ablation_equalized"]["equal"]))
    print("  off-specialty (no skill) farmer yield: %.1f" % g["off_specialty_farmer_yield"])
    l = R["G_learning_by_doing"]
    print("LEARN     solo curve:", l["solo_curve"])
    print("          per-step gains (diminishing=%s):" % l["strictly_diminishing"],
          l["per_step_gains"])
    print("          ablate learning -> flat:", l["ablation_is_flat"], l["ablation_flat_curve"])
    t = R["G_teaching"]
    print("TEACH     solo   :", t["solo_curve"])
    print("          taught :", t["willing_curve"], "(dominates solo=%s)"
          % t["taught_dominates_solo"])
    print("          willing single gain=%.3f vs solo single gain=%.3f"
          % (t["willing_single_gain"], t["solo_single_gain"]))
    print("REFUSE    rival learner -> outcome=%d, no transfer=%s, curve=%s"
          % (t["rival_refused_outcome"], t["rival_no_transfer"], t["rival_refused_curve"]))
    print("COERCE    John power 9 > teacher 1 -> coerced=%d, outcome=%d"
          % (t["coerced_flag"], t["coerced_outcome"]))
    print("          coerced curve:", t["coerced_curve"],
          "(degraded vs willing=%s)" % t["coerced_degraded_vs_willing"])
    print("SABOTAGE  stated_rate=%.2f held_rate=%.2f  stated-held gap=%.2f (234 stated!=held)"
          % (t["sabotage_stated_rate"], t["sabotage_held_rate"],
             t["sabotage_stated_minus_held"]))
    print("          weak coercer (power 0.5 < 1) -> coerced=%d, no transfer=%s"
          % (t["weak_coercer_flag"], t["weak_coercer_no_transfer"]))
    print("\nwrote", os.path.join(OUT, "summary.json"))
    return R


if __name__ == "__main__":
    main()
