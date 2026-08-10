"""bigville cognitive C5 (block 329000): intrinsic motivation -> flow -> generativity
(SDT + Csikszentmihalyi). Gates mirror BIGVILLE_FLOW_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_flow_world import BigvilleFlowWorld   # noqa: E402


def _flow_at(w, name, ch):
    w.set_challenge(name, ch); w.step()
    return w.flow(name)


# ------------------------------------------------------ G-flow-at-challenge-equals-skill (headline)
def test_flow_peaks_when_challenge_matches_skill():
    w = BigvilleFlowWorld()
    w.add_agent("M", skill=0.5)
    xs = [0.1, 0.3, 0.45, 0.5, 0.55, 0.7, 0.9]
    ys = [_flow_at(w, "M", c) for c in xs]
    peak = ys.index(max(ys))
    assert xs[peak] == 0.5, f"flow should peak at challenge=skill: peak at {xs[peak]}"
    assert all(ys[k + 1] > ys[k] for k in range(peak)), f"rises to the match: {ys}"
    assert all(ys[k + 1] < ys[k] for k in range(peak, len(ys) - 1)), f"falls past the match: {ys}"


# ------------------------------------------------------ G-boredom-vs-anxiety
def test_the_three_channels():
    w = BigvilleFlowWorld()
    w.add_agent("M", skill=0.5)
    w.set_challenge("M", 0.1); w.step()
    assert w.flow_state("M") == "boredom", "too easy -> boredom"
    w.set_challenge("M", 0.5); w.step()
    assert w.flow_state("M") == "flow", "matched -> flow"
    w.set_challenge("M", 0.9); w.step()
    assert w.flow_state("M") == "anxiety", "too hard -> anxiety"


# ------------------------------------------------------ G-generativity-under-sustained-flow (headline)
def test_sustained_flow_produces_a_creation():
    w = BigvilleFlowWorld()
    w.add_agent("M", skill=0.5, flow_needed=3)
    w.set_challenge("M", 0.5)
    w.step(2)
    assert w.n_creations("M") == 0, "not enough sustained flow yet"
    w.step()                          # third flow step
    assert w.n_creations("M") == 1, "sustained flow produces a creation"


# ------------------------------------------------------ G-value-is-recognized
def test_a_creations_worth_is_its_recognition():
    w = BigvilleFlowWorld()
    w.add_agent("M", skill=0.6, flow_needed=3)
    w.set_challenge("M", 0.6)
    w.step(3)
    assert w.n_creations("M") == 1
    assert w.creation_worth("M", 0) == 0, "an unrecognized creation is worth nothing"
    w.appreciate("M", 0, 4)
    assert w.creation_worth("M", 0) == 4, "worth = the count of agents who recognize it"


# ------------------------------------------------------ G-off-flow-no-creation (falsifier)
def test_off_flow_produces_nothing():
    # sustained anxiety (challenge >> skill)
    anx = BigvilleFlowWorld(); anx.add_agent("A", skill=0.3, flow_needed=3)
    anx.set_challenge("A", 0.9); anx.step(6)
    assert anx.n_creations("A") == 0, "sustained anxiety -> no creation"
    # sustained boredom (challenge << skill)
    bor = BigvilleFlowWorld(); bor.add_agent("B", skill=0.8, flow_needed=3)
    bor.set_challenge("B", 0.1); bor.step(6)
    assert bor.n_creations("B") == 0, "sustained boredom -> no creation"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_flow():
    src = open(os.path.join(_ROOT, "worlds", "bigville_flow_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_flow.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"fl_state", "fl_streak", "fl_generate", "fl_worth"} <= names, names
