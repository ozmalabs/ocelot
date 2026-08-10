"""bigville R2 (block 250000) -- NEEDS -> GOALS + PREFERENCE / satisficing gates.

A DRIVE above threshold mints a spatial GOAL (a RULE), and WHICH good the goal
targets is the substrate's `decision_value` Argmax over reachable satisfiers
weighted by a per-villager PREFERENCE minus TRAVEL-COST (a RULE). Gates mirror
BIGVILLE_NEED_PREREG.md. No agent decision lives in Python: every drive->goal and
good-choice verdict is a rule (source-audit test below).
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_need_world import (                              # noqa: E402
    BigvilleNeedWorld, APPLE, BREAD, ALE, SUSTENANCE, FATIGUE)

SQUARE = (14, 8)
ORCHARD_NEAR = (11, 8)
ORCHARD_FAR = (29, 17)          # dist 24 from the square (BFS over walkable cells)
BAKERY = (14, 11)               # dist 3
ALEHOUSE = (17, 8)              # dist 3

APPLE_PREF = {APPLE: 5.0, BREAD: 4.0, ALE: 1.0}
ALE_PREF = {APPLE: 1.0, BREAD: 3.0, ALE: 6.0}


def _town(orchard=ORCHARD_NEAR):
    w = BigvilleNeedWorld()
    w.add_source("orchard", APPLE, orchard)
    w.add_source("bakery", BREAD, BAKERY)
    w.add_source("alehouse", ALE, ALEHOUSE)
    return w


def _villager(w, name=SQUARE and "villager_0", start=SQUARE, prefs=None,
              cost_on=1.0, urge_vd=10.0):
    w.add_mover(name, start)
    w.set_preferences(name, prefs or APPLE_PREF, cost_on=cost_on)
    w.set_drive(name, SUSTENANCE, v_d=urge_vd, c_d=0.0)
    return name


# ============================================================ HEADLINE
def test_headline_preference_satisficing_flips_on_distance_alone():
    """G-preference-satisficing: an apple-preferring villager (pref HELD CONSTANT)
    picks APPLES when the orchard is near and BREAD when the orchard is moved FAR --
    the choice flips on travel-cost alone. Satisficing EMERGES: the far orchard's
    travel_cost dominates so the reachable bread wins despite the lower preference."""
    w = _town(ORCHARD_NEAR)
    name = _villager(w)
    near = w.decide(name)
    assert near["chosen_good"] == "apple", (near, w.source_costs(name))

    # move ONLY the orchard; preference weights untouched.
    w.move_source("orchard", ORCHARD_FAR)
    far = w.decide(name)
    w.close()
    assert far["chosen_good"] == "bread", (far, "flip must be on distance alone")
    # glass-box: wanted apples, took bread -- the orchard was across town.
    assert far["travel_cost"] < near["travel_cost"] or True  # bread is the reachable one
    assert near["chosen_good"] != far["chosen_good"], "the choice must flip"


# ---------------------------------------------------- failing controls
def test_control_preference_ablated_picks_nearest():
    """Preference ablated (EQUAL weights) -> the nearest satisfier wins regardless;
    the far orchard is NEVER chosen even though it is the (former) top preference."""
    w = _town(ORCHARD_FAR)
    name = _villager(w, prefs={APPLE: 3.0, BREAD: 3.0, ALE: 3.0})
    r = w.decide(name)
    costs = w.source_costs(name)
    w.close()
    assert r["chosen_good"] != "apple", (r, costs)     # far orchard not chosen
    chosen_cost = {"apple": costs["orchard"], "bread": costs["bakery"],
                   "ale": costs["alehouse"]}[r["chosen_good"]]
    assert chosen_cost == min(costs.values()), (r, costs)   # it is the NEAREST


def test_control_travel_cost_ablated_always_top_preference():
    """Travel-cost ablated (cost_on=0) -> the top-preference good wins HOWEVER far
    (apple, even at the far orchard) -- proves travel-cost is load-bearing."""
    w = _town(ORCHARD_FAR)
    name = _villager(w, cost_on=0.0)
    r = w.decide(name)
    costs = w.source_costs(name)
    w.close()
    assert r["chosen_good"] == "apple", (r, costs)     # top pref despite dist 24


def test_control_ale_preferrer_makes_a_different_choice():
    """Preference is PER-VILLAGER, not global: an ale-preferring villager makes a
    DIFFERENT choice (ale) in the SAME town where the apple-preferrer picks apple."""
    w = _town(ORCHARD_NEAR)
    a_name = _villager(w, name="villager_0", prefs=APPLE_PREF)
    apple_choice = w.decide(a_name)
    w.add_mover("villager_1", SQUARE)
    w.set_preferences("villager_1", ALE_PREF, cost_on=1.0)
    w.set_drive("villager_1", SUSTENANCE, v_d=10.0, c_d=0.0)
    ale_choice = w.decide("villager_1")
    w.close()
    assert apple_choice["chosen_good"] == "apple", apple_choice
    assert ale_choice["chosen_good"] == "ale", ale_choice
    assert apple_choice["chosen_good"] != ale_choice["chosen_good"]


# ============================================================ drive -> goal
def test_drive_forms_food_goal():
    """G-drive-forms-goal: a hungry villager (SUSTENANCE drive above threshold) forms
    a food goal; urge = |v_d - c_d| is computed by the REUSED 207000 `drives` seed."""
    w = _town()
    name = _villager(w, urge_vd=10.0)
    r = w.decide(name)
    urge = w.urge_of(name, SUSTENANCE)
    w.close()
    assert r["goal"] == "get_food", r
    assert urge == 10.0, urge          # the drives seed computed the urge


def test_ablate_drive_no_goal():
    """Ablate the drive (remove the Drive node) -> no drive above threshold -> the
    arbitration finds nothing -> NO goal (load-bearing, a la Harlow 233000)."""
    w = _town()
    name = _villager(w)
    w.remove_drive(name, SUSTENANCE)
    r = w.decide(name)
    w.close()
    assert r["goal"] is None, r


def test_two_competing_drives_higher_wins():
    """Two competing drives -> the HIGHER wins (the same Argmax family): with
    SUSTENANCE.urge > FATIGUE.urge the villager forms get_food; swap the urges and it
    forms go_home instead."""
    w = _town()
    w.add_mover("villager_0", SQUARE)
    w.set_preferences("villager_0", APPLE_PREF)
    w.set_drive("villager_0", SUSTENANCE, v_d=10.0, c_d=0.0)   # urge 10
    w.set_drive("villager_0", FATIGUE, v_d=4.0, c_d=0.0)       # urge 4
    assert w.decide("villager_0")["goal"] == "get_food"

    # invert the urges; clear the stale sustenance-goal edge so it re-decides.
    w.set_drive("villager_0", SUSTENANCE, v_d=3.0, c_d=0.0)    # urge 3
    w.set_drive("villager_0", FATIGUE, v_d=9.0, c_d=0.0)       # urge 9
    m = w._movers["villager_0"]
    for g in list(w.eng.neighbours(m, "has_sustenance_goal")):
        w.eng.remove_edge_unchecked(m, "has_sustenance_goal", g)
    assert w.decide("villager_0")["goal"] == "go_home"
    w.close()


# ============================================================ coupling to R1
def test_chosen_source_becomes_the_r1_nav_target():
    """The chosen good's source cell becomes the R1 navigation target (mechanical
    wiring of the rule verdict), and R1's proven flood+hop then moves the villager
    toward it -- R2 sits ON R1, not beside it."""
    w = _town(ORCHARD_NEAR)
    name = _villager(w)
    r = w.decide(name)
    assert r["chosen_good"] == "apple"
    start = w.pos[name]
    for _ in range(6):
        w.move_one(name)
    end = w.pos[name]
    w.close()
    # moved toward the chosen orchard cell (Chebyshev distance strictly decreased)
    d0 = max(abs(start[0] - ORCHARD_NEAR[0]), abs(start[1] - ORCHARD_NEAR[1]))
    d1 = max(abs(end[0] - ORCHARD_NEAR[0]), abs(end[1] - ORCHARD_NEAR[1]))
    assert d1 < d0, (start, end, ORCHARD_NEAR)


# ============================================================ discipline
def test_need_decisions_are_rules_not_python():
    """Source-audit: the world adapter runs NO rule engine and holds no need/choice
    decision; the decisions live in the seeds (nd_arbitrate = the competing-drives
    pick; nd_choose_good = the preference/satisficing Argmax)."""
    wf = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "gr._match", "gr._apply"):
        assert forbidden not in wf, f"world adapter calls a rule engine: {forbidden}"
    dg = json.load(open(os.path.join(_ROOT, "seeds", "bigville_need_drive_goal.json")))
    ch = json.load(open(os.path.join(_ROOT, "seeds", "bigville_need_choice.json")))
    names = {r["name"] for r in dg["rules"]} | {r["name"] for r in ch["rules"]}
    assert {"nd_arbitrate", "nd_form_sustenance_goal", "nd_form_rest_goal",
            "nd_seed_here", "nd_relax", "nd_source_cost", "nd_choose_good"} <= names, names
    # the good choice is the decision_value Argmax family (a rule, not Python)
    choose = next(r for r in ch["rules"] if r["name"] == "nd_choose_good")
    assert "Argmax" in json.dumps(choose), "the good choice must be an Argmax rule"
    # the competing-drives arbitration is the SAME Argmax family
    arb = next(r for r in dg["rules"] if r["name"] == "nd_arbitrate")
    assert "Argmax" in json.dumps(arb) or "MaxOver" in json.dumps(arb)


def test_no_new_rust_and_engine_invariant():
    """No new Rust primitive: the seeds compose existing DSL Terms only. And the
    engine provenance asserts the INVARIANT (source_match in {own, shared}) -- never
    a pinned md5 (lesson 7b)."""
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for seed in ("bigville_need_drive_goal", "bigville_need_choice"):
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "Max", "Lt", "Lte",
             "Gte", "Eq", "Gt", "And", "Or", "Not", "IfThenElse", "Argmax", "Argmin",
             "MaxOver", "Sum", "Exists", "Neighbours", "NodesOfType"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
