"""bigville R61 (block 374000): the trades train APPRENTICES. An apprentice learns the craft skill
under a master (composing with bigville_craft: skill = tool quality, so their tools improve),
graduates to journeyman near the master's competence, and inherits the trade when the master dies.
Gates mirror the ap_* rules.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_apprentice_world import BigvilleApprenticeWorld as Appr   # noqa: E402


# ------------------------------------------------------ G-taking-on-is-the-masters-decision (headline)
def test_taking_on_an_apprentice_is_the_masters_decision():
    generous = Appr(); generous.add_master("Wayland", skill=0.8, mentoring=0.8, reluctance=0.1)
    assert generous.seek_apprenticeship("Tam", "Wayland"), "a generous master takes the apprentice on"
    assert generous.verdict("Tam") == "accept" and generous.role("Tam") == "apprentice"

    curmudgeon = Appr(); curmudgeon.add_master("Grump", skill=0.8, mentoring=0.1, reluctance=0.8)
    assert not curmudgeon.seek_apprenticeship("Tam", "Grump"), "a curmudgeon turns the SAME candidate away"
    assert curmudgeon.verdict("Tam") == "decline" and curmudgeon.role("Tam") == "turned_away", "agents diverge"


# ------------------------------------------------------ G-a-full-master-declines
def test_a_master_at_capacity_declines_a_second_apprentice():
    w = Appr(); w.add_master("Busy", skill=0.8, mentoring=0.5, reluctance=0.1)
    assert w.seek_apprenticeship("First", "Busy"), "a willing master takes the first"
    assert not w.seek_apprenticeship("Second", "Busy"), "but is now at capacity -- the second is turned away"


# ------------------------------------------------------ G-learns-the-trade (headline)
def test_the_apprentice_learns_the_trade_under_the_master():
    w = Appr(); w.add_master("Wayland", trade="smith", skill=0.8)
    w.take_apprentice("Wayland", "Tam", skill=0.1)
    assert w.skill("Tam") == 0.1, "the apprentice starts unskilled"
    w.train("Wayland", 1); s1 = w.skill("Tam")
    w.train("Wayland", 8); s9 = w.skill("Tam")
    assert s1 > 0.1, "one period of training raises the apprentice's skill"
    assert s9 > s1 and s9 < 0.8, "skill rises over training, converging toward (never past) the master's"


# ------------------------------------------------------ G-graduates-to-journeyman (headline)
def test_the_apprentice_graduates_when_competent():
    w = Appr(); w.add_master("Wayland", trade="smith", skill=0.8)
    w.take_apprentice("Wayland", "Tam", skill=0.1)
    w.train("Wayland", 2)
    assert not w.graduated("Tam") and w.role("Tam") == "apprentice", "a little training is not yet enough"
    w.train("Wayland", 7)
    assert w.graduated("Tam") and w.role("Tam") == "journeyman", "near the master's competence -> a journeyman"


# ------------------------------------------------------ G-trained-tools-improve (headline, craft compose)
def test_a_trained_apprentices_tools_are_better_than_an_unskilled_makers():
    w = Appr()
    w.add_master("Klutz", trade="smith", skill=0.1)             # a raw, unskilled smith (contrast)
    raw = w.forge_head("Klutz")
    w.add_master("Wayland", trade="smith", skill=0.8)
    w.take_apprentice("Wayland", "Tam", skill=0.1); w.train("Wayland", 9)
    trained = w.forge_head("Tam")                               # the graduated journeyman forges
    assert raw == 0.1, "an unskilled maker's tool is poor (quality = skill)"
    assert trained is not None and trained > 0.6, "the trained apprentice's tool is good -- training improved it"
    assert trained == w.skill("Tam"), "the tool's quality IS the apprentice's learned skill (bigville_craft)"


# ------------------------------------------------------ G-succession (headline)
def test_the_trade_survives_the_masters_death():
    w = Appr(); w.add_master("Wayland", trade="smith", skill=0.8)
    w.take_apprentice("Wayland", "Tam", skill=0.1); w.train("Wayland", 9)
    assert w.is_town_maker("Wayland", "smith"), "the master holds the trade while alive"
    assert w.is_town_maker("Tam", "smith"), "the graduated journeyman also practises it"
    w.die("Wayland")
    assert w.role("Tam") == "master", "the graduated apprentice inherits the trade -- becomes the master"
    assert w.is_town_maker("Tam", "smith"), "and is now the town's smith"
    assert not w.is_town_maker("Wayland", "smith"), "the dead master no longer holds the trade"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_apprenticeship():
    src = open(os.path.join(_ROOT, "worlds", "bigville_apprentice_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_apprentice.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ap_decide", "ap_accept", "ap_learn", "ap_graduate", "ap_succeed"} <= names, names
    learn = json.dumps([r for r in seed["rules"] if r["name"] == "ap_learn"][0])
    assert "skill" in learn and "has_apprentice" in learn, "learning nudges the apprentice's skill toward the master's"
    dec = json.dumps([r for r in seed["rules"] if r["name"] == "ap_decide"][0])
    assert "Argmax" in dec and "ApprenticeStance" in dec and "mentoring" in dec, \
        "taking on an apprentice is a collapse valued by the master's own disposition"
