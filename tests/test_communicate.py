"""Objective-driven production — speaking as goal-directed action selection.

The entity picks the utterance whose predicted effect across the participation
framework best achieves THE OBJECTIVE. Third-party targeting, whether-to-speak,
and efficiency all fall out of the one argmax — they are instrumental, not the
objective.
"""
from __future__ import annotations

from domains import audience as aud
from domains import communicate as com

_CANDS = [{"C"}, {"D"}, {"C", "D"}]


def _scene(parties):
    g = com.new_graph()
    s = aud.make_scene(g)
    ps = {n: aud.add_party(g, s, n, knows, role=role)
          for n, (knows, role) in parties.items()}
    return g, s, ps


def test_objective_can_target_a_third_party():
    # addressed to expert A (already knows C), but the goal is that overhearer B
    # — a third party — comes to know C
    g, s, ps = _scene({"A": ({"C"}, "addressee"), "B": (set(), "overhearer")})
    obj = com.set_objective(g, ps["B"], "C")
    assert com.choose(g, s, obj, _CANDS)[0] == frozenset({"C"})


def test_silence_when_goal_already_met():
    g, s, ps = _scene({"A": ({"C"}, "addressee")})
    obj = com.set_objective(g, ps["A"], "C")
    assert com.choose(g, s, obj, _CANDS)[0] == frozenset()      # say nothing


def test_efficiency_conveys_only_the_new():
    # B already holds C; goal is B learns D → convey only D, not redundant C
    g, s, ps = _scene({"B": ({"C"}, "addressee")})
    obj = com.set_objective(g, ps["B"], "D")
    assert com.choose(g, s, obj, _CANDS)[0] == frozenset({"D"})
