"""Gate for the SUPERGRAPH TOWN WIRING (block 282000-c,
worlds/bigville_conduct_town_world.py).

Many residents, ONE shared substrate = the supergraph. Each resident is a
subgraph deciding at its own reference frame; because the decision core (v1.1.0)
scopes its Argmax to Neighbours(m,"in_scene"), the WHOLE town settles in one
run_rules pass. What this gate asserts (the robust claims) and what it does NOT
(the honest targeting limitation, documented in BIGVILLE_CONDUCT_TOWN_RESULTS.md):
  ASSERTS: one-pass settle; a prosocial default with ZERO violence when no strong
  resentment exists; a feud drives a DELIBERATED, DIRECTED harm at the resented
  target and ONLY there; every act stays within the actor's own co-present scene.
  DOES NOT assert fine-grained prosocial targeting (help your friend over a
  neutral) -- the residual-driven collapse settles the first-tie prosocial act on
  a single un-internalized pass; see the results doc.
"""
import ast
import os

import pytest

from worlds.bigville_conduct_town_world import BigvilleConductTownWorld


def _square(names):
    return [{"name": n, "place": "square"} for n in names]


def test_whole_town_settles_in_one_pass():
    """Every resident gets a chosen action from a single decide_town() -- the
    supergraph settles all subgraphs in one pass."""
    t = BigvilleConductTownWorld(_square("ABCDE"),
                                 {("A", "B"): {"affection": 3.0}})
    try:
        out = t.decide_town()
        assert len(out) == 5
        assert all(r["act"] is not None for r in out)
    finally:
        t.close()


def test_peaceful_town_has_no_violence():
    """No strong resentment anywhere -> the prosocial default holds, ZERO harm."""
    t = BigvilleConductTownWorld(
        _square("ABCD"),
        {("A", "B"): {"affection": 3.0}, ("B", "A"): {"affection": 3.0},
         ("C", "D"): {"affection": 3.0}, ("D", "C"): {"affection": 3.0}})
    try:
        t.decide_town()
        assert t.harm_events() == []
    finally:
        t.close()


def test_a_feud_drives_directed_deliberated_harm_and_only_there():
    """One resident deeply resents another -> that resident (and only it) harms,
    directed at the resented target, and only after deliberating (deepened)."""
    t = BigvilleConductTownWorld(
        _square("ABCDE"),
        {("A", "B"): {"affection": 3.0}, ("C", "D"): {"affection": 2.0},
         ("A", "E"): {"resentment": 5.0, "affection": -4.0}})
    try:
        out = t.decide_town()
        harms = t.harm_events()
        assert len(harms) == 1                       # violence is rare
        assert harms[0]["actor"] == "A" and harms[0]["target"] == "E"
        a = next(r for r in out if r["actor"] == "A")
        assert a["act"] == "harm" and a["deepened"] == 1   # deliberated, not impulse
        assert t.health("E") == 75.0                 # the effect landed
    finally:
        t.close()


def test_every_act_stays_within_the_actors_own_scene():
    """Scoping: each resident's chosen target is someone co-present with it (it
    never acts on a resident it cannot see)."""
    residents = [{"name": "A", "place": "market"}, {"name": "B", "place": "market"},
                 {"name": "C", "place": "field"}]
    t = BigvilleConductTownWorld(residents, {("A", "B"): {"affection": 2.0}})
    try:
        out = t.decide_town()
        by = {r["actor"]: r for r in out}
        # A and B are together in the market; C is alone in the field.
        assert by["A"]["target"] in (None, "B")      # A can only act on B
        assert by["C"]["target"] is None             # C is alone -> rest, no target
        assert by["C"]["act"] == "rest"
    finally:
        t.close()


def test_no_python_agent_decision_in_the_town_adapter():
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_conduct_town_world.py")
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
