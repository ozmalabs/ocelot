"""Gate for the SELF-DRIVING WALKING TOWN (block 285000,
worlds/bigville_walking_town_world.py) -- the hop clock (283000) + the graph-native
surprise gate (284000) + Bond-directed supergraph conduct (282000), end to end.

Residents WALK (one hop per master tick); co-presence EMERGES from positions (no
hand-fed scene); the surprise gate fires on the unpredicted; only surprised residents
run the conduct collapse; harm enacts on its target. ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.bigville_walking_town_world import BigvilleWalkingTownWorld as W


def _scene(a_predicts):
    res = [{"name": "A", "pos": (0, 0), "goal": (8, 0), "predicts": a_predicts},
           {"name": "B", "pos": (0, 1), "goal": (8, 1), "predicts": ["A"]},
           {"name": "E", "pos": (4, -3), "goal": (4, 3), "predicts": []}]
    bonds = {("A", "B"): {"affection": 3.0},
             ("A", "E"): {"resentment": 5.0, "affection": -4.0}}
    return W(res, bonds)


def _harms(w):
    return [d for d in w.decided if d[2] == "harm"]


def test_no_teleport():
    w = _scene(["B"])
    try:
        w.run(9)
        assert w.max_hop == 1
    finally:
        w.close()


def test_unpredicted_rival_crossing_a_route_triggers_directed_harm():
    """A walks a route; an UNPREDICTED rival crosses it -> surprise -> the collapse
    directs harm at the rival, and it ENACTS on the target's health. All derived
    from positions -- no hand-fed co-presence."""
    w = _scene(["B"])                      # A does NOT predict the rival E
    try:
        w.run(9)
        hs = _harms(w)
        assert len(hs) == 1                # violence is rare -- one act
        assert hs[0][1] == "A" and hs[0][3] == "E"   # A harmed E (the resented rival)
        assert w.health("E") == 75.0       # and it landed
    finally:
        w.close()


def test_predicting_the_rival_dissolves_the_violence():
    """CONTROL: identical geometry, but A PREDICTS the rival -> the crossing is
    unsurprising -> no deliberation -> NO harm. Violence is surprise-driven."""
    w = _scene(["B", "E"])                 # A predicts the rival too
    try:
        w.run(9)
        assert _harms(w) == []
        assert w.health("E") == 100.0
    finally:
        w.close()


def test_decisions_are_sparse_across_the_walk():
    w = _scene(["B"])
    try:
        w.run(9)
        assert w.decision_count() < 3 * 9 * 0.25   # << residents x ticks
    finally:
        w.close()


def test_no_python_agent_decision_in_the_walking_adapter():
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_walking_town_world.py")
    text = open(src).read()
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply",
                   "make_rule", "argmax", "argmin"):
        assert banned not in text
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
           and node.func.id in ("max", "min"):
            call = ast.get_source_segment(text, node) or ""
            assert not any(k in call for k in ("impulse", "value", "plan",
                                               "afford", "affect", "super")), call


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
