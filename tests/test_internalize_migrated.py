"""Gate for CONDUCT INTERNALIZATION (block 286000,
worlds/bigville_internalize_world.py).

A deliberated response becomes a habit: over repeated encounters, replay
(net_collapse, 279000) writes the deep choice into the order-0 net, so the collapse
stops deliberating (deepened 1->0) and the response fires from the fast path -- even
on a PREDICTED encounter (shallow-only). Closes the fast-path-should-be-LEARNED
thread (282000-c / 283000 / 285000). ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.bigville_internalize_world import BigvilleInternalizeWorld as W


def test_conduct_automation_curve():
    """Repeated deliberate encounters with a resented rival: harm is chosen
    throughout, but it goes from DELIBERATE (deepened=1) to HABITUAL (deepened=0)
    as its cached fast-path value rises toward its model value (self-terminating)."""
    w = W("Foe", resentment=5.0, affection=-4.0, replay_gain=1.0)
    try:
        v0 = w.cached_value("harm")
        curve = [w.encounter(deepen=True) for _ in range(8)]
        vN = w.cached_value("harm")
        assert all(r["chosen"] == "harm" for r in curve)     # directed at the rival throughout
        assert curve[0]["deepened"] == 1                      # first time: deliberated
        assert curve[-1]["deepened"] == 0                     # later: habitual
        assert vN > v0 + 1.0                                  # the fast path learned it
        # monotone non-decreasing cached value (replay only pushes up)
        assert vN >= v0
    finally:
        w.close()


def test_internalized_response_fires_habitually_on_a_predicted_encounter():
    """After internalization, a PREDICTED encounter (shallow-only, deepen=False)
    fires the learned response with NO deliberation -- a foreseen threat now carries
    a habitual response instead of being a no-op (the 285000 gap)."""
    w = W("Foe", resentment=5.0, affection=-4.0, replay_gain=1.0)
    try:
        for _ in range(8):
            w.encounter(deepen=True)                          # internalize
        hab = w.encounter(deepen=False)                       # shallow-only / predicted
        assert hab["chosen"] == "harm" and hab["deepened"] == 0
    finally:
        w.close()


def test_control_no_replay_no_internalization():
    """FALSIFIER: replay_gain=0 -> nothing is written back -> the collapse deliberates
    EVERY time (deepened stays 1) and the un-learned fast path stays prosocial: a
    shallow-only encounter picks help, not harm. The grudge never becomes a reflex."""
    w = W("Foe", resentment=5.0, affection=-4.0, replay_gain=0.0)
    try:
        first = w.encounter(deepen=True)
        for _ in range(6):
            w.encounter(deepen=True)
        last = w.encounter(deepen=True)
        assert first["deepened"] == 1 and last["deepened"] == 1   # never automates
        hab = w.encounter(deepen=False)
        assert hab["chosen"] != "harm"                            # no habit formed
    finally:
        w.close()


def test_prosocial_internalizes_too():
    """The mechanism is valence-neutral: helping a loved friend also internalizes
    (deliberate -> habitual), so care becomes automatic."""
    w = W("Friend", affection=5.0, resentment=0.0, replay_gain=1.0)
    try:
        curve = [w.encounter(deepen=True) for _ in range(8)]
        assert all(r["chosen"] == "help" for r in curve)
        assert curve[0]["deepened"] == 1 and curve[-1]["deepened"] == 0
    finally:
        w.close()


def test_no_python_agent_decision_in_the_internalize_adapter():
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_internalize_world.py")
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
