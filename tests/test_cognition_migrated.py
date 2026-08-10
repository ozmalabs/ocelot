"""bigville INTEGRATION (block 331000): the cognitive agent loop -- C1-C6 wired live.
Gates the EMERGENT loop, not the individual signatures (those are C1-C6's own tests):
homeostasis vs starvation, drive-selects-action, arousal->focus, outcome->mood/load.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_cognition_world import BigvilleCognitionWorld   # noqa: E402


def _trace(w, name, n):
    rows = []
    for _ in range(n):
        w.tick()
        rows.append(dict(energy=w.energy(name), pursues=w.pursues(name), focus=w.focus(name),
                         arousal=w.arousal(name), mood=w.mood(name), load=w.load(name),
                         broken=w.broken(name)))
    return rows


# ------------------------------------------------------ G-homeostasis (headline)
def test_a_resourced_agent_self_maintains():
    w = BigvilleCognitionWorld(deposit_stock=1000.0)
    w.add_agent("Ada")
    rows = _trace(w, "Ada", 20)
    assert all(r["energy"] > 0 for r in rows), "the agent never starves when resourced -- the loop closes"
    assert not rows[-1]["broken"], "and is not left broken"
    kinds = {r["pursues"] for r in rows}
    assert "sustenance" in kinds and "competence" in kinds, "it both works and eats (drive-driven action)"
    assert w.store_stock() > 0, "it produces a food surplus (work has impact)"
    assert rows[-1]["load"] < rows[2]["load"], "load recovers once the loop stabilises"


# ------------------------------------------------------ G-starvation-declines (headline)
def test_a_starved_agent_declines_and_breaks():
    w = BigvilleCognitionWorld(deposit_stock=0.0)   # nothing to produce food from
    w.add_agent("Bob", energy=5.0)
    rows = _trace(w, "Bob", 10)
    assert w.energy("Bob") == 0.0, "no resource -> cannot produce food -> energy runs to zero"
    assert w.broken("Bob"), "chronic frustration accrues allostatic load past the window -> breakdown"
    assert rows[-1]["load"] > rows[0]["load"], "load climbs under sustained frustration"


# ------------------------------------------------------ G-drive-selects-the-action
def test_the_dominant_drive_selects_the_action():
    # gate on the ACTION taken (the post-action `pursues` flips once the drive is satisfied
    # within the tick, so read the outcome). Isolated worlds so the shared store doesn't couple.
    hungry = BigvilleCognitionWorld(deposit_stock=1000.0)
    hungry.add_agent("Hungry", energy=1.0, max_energy=10.0)   # starving -> sustenance dominant
    hungry.tick()
    assert hungry.store_stock() == 0.0, "a starving agent pursues sustenance (tries to eat), it does not work"
    assert hungry.load("Hungry") > 0.0, "and with no food, the hunger is frustrated -> load"

    sated = BigvilleCognitionWorld(deposit_stock=1000.0)
    sated.add_agent("Sated", energy=10.0, max_energy=10.0, comp_decay=0.5)  # fed, stale competence
    sated.tick()
    assert sated.store_stock() > 0.0, "a fed agent with stale competence pursues mastery -> it works and produces"


# ------------------------------------------------------ G-arousal-lowers-focus
def test_arousal_modulates_focus_across_the_loop():
    w = BigvilleCognitionWorld(deposit_stock=1000.0)
    w.add_agent("Ada")
    rows = _trace(w, "Ada", 20)
    lo_focus = min(r["focus"] for r in rows)
    hi_focus = max(r["focus"] for r in rows)
    # when unmet drives spike arousal off the optimum, focus drops; when calm it recovers.
    assert lo_focus < 0.8, f"high arousal degrades focus at some point: min {lo_focus}"
    assert hi_focus > 0.95, f"and focus recovers when calm: max {hi_focus}"


# ------------------------------------------------------ G-outcome-to-mood-and-load
def test_outcomes_become_mood_and_frustration_becomes_load():
    good = BigvilleCognitionWorld(deposit_stock=1000.0)
    good.add_agent("Ada")
    _trace(good, "Ada", 12)
    assert good.mood("Ada") > 0, "a self-maintaining agent's recent memories are positive -> positive mood"
    bad = BigvilleCognitionWorld(deposit_stock=0.0)
    bad.add_agent("Bob", energy=5.0)
    r = _trace(bad, "Bob", 5)
    assert bad.mood("Bob") < 0, "sustained failure -> negative mood"
    assert r[-1]["load"] > r[0]["load"], "and frustration accrues as allostatic load"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_loop():
    src = open(os.path.join(_ROOT, "worlds", "bigville_cognition_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_cognition.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"cg_metabolize", "cg_state", "cg_eat", "cg_work", "cg_hunger_frustrated",
            "cg_work_frustrated", "cg_break", "cg_recover"} <= names, names
