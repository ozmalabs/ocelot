"""Gate for the GRAPH-NATIVE SURPRISE-GATED SUPERGRAPH TOWN (block 284000,
seeds/bigville_surprise_gate.json + worlds/bigville_surprise_town_world.py).

The graph-native realization of the 283000 clock: a decision fires on SURPRISE
(observation != held prediction) as RULES, and only a surprised resident runs its
conduct collapse. Composes surprise (284000) + supergraph conduct (282000) + scoped
decision core (279000 v1.1.0). ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.bigville_surprise_town_world import BigvilleSurpriseTownWorld as W


def _mk():
    res = [{"name": "A", "predicts": ["B"]}, {"name": "B", "predicts": ["A"]},
           {"name": "E"}]
    bonds = {("A", "B"): {"affection": 3.0},
             ("A", "E"): {"resentment": 5.0, "affection": -4.0}}
    return W(res, bonds)


def test_a_predicted_meeting_fires_no_decision():
    """A predicted B; meeting B is unsurprising -> the surprise rule does not fire
    -> no collapse runs (a no-op continuation)."""
    w = _mk()
    try:
        out = {o["resident"]: o for o in w.tick({"A": ["B"], "B": ["A"]})}
        assert out["A"]["surprised"] is False and out["A"]["chosen"] is None
        assert out["B"]["surprised"] is False
        assert w.decision_count() == 0
    finally:
        w.close()


def test_unpredicted_encounter_fires_surprise_and_directed_conduct():
    """An UNPREDICTED rival appears -> the surprise rule flags A -> A's supergraph
    collapse runs and directs harm at the resented rival."""
    w = _mk()
    try:
        w.tick({"A": ["B"], "B": ["A"]})                        # settle the predicted pair
        out = {o["resident"]: o for o in
               w.tick({"A": ["B", "E"], "B": ["A"], "E": ["A"]})}
        assert out["A"]["surprised"] is True                    # surprise (rule) fired
        assert out["A"]["chosen"] == "harm" and out["A"]["target"] == "E"
        assert out["B"]["surprised"] is False                   # B predicted A -> no-op
    finally:
        w.close()


def test_prediction_absorbs_no_re_surprise():
    """After the surprise, the prediction absorbs the new other -> re-seeing it is
    no longer surprising (held-prediction update)."""
    w = _mk()
    try:
        w.tick({"A": ["B"], "B": ["A"]})
        w.tick({"A": ["B", "E"], "B": ["A"], "E": ["A"]})       # E surprises A, absorbed
        assert "E" in w.predicts("A")
        out = {o["resident"]: o for o in
               w.tick({"A": ["B", "E"], "B": ["A"], "E": ["A"]})}
        assert out["A"]["surprised"] is False                   # no re-surprise
    finally:
        w.close()


def test_decisions_are_sparse_only_surprises():
    """Across many ticks of a stable, fully-predicted scene, decisions are just the
    initial surprises -- O(surprise), not O(residents x ticks)."""
    w = _mk()
    try:
        for _ in range(6):
            w.tick({"A": ["B", "E"], "B": ["A"], "E": ["A"]})
        # A surprised once (E), E surprised once (A,B unpredicted). Then stable.
        assert w.decision_count() <= 3
    finally:
        w.close()


def test_surprise_gate_seed_rules():
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = json.load(open(os.path.join(root, "seeds", "bigville_surprise_gate.json")))
    names = {r["name"] for r in d["rules"]}
    assert {"sg_surprise", "sg_absorb", "sg_provide_directed"} <= names


def test_surprise_is_a_rule_not_a_python_decision():
    """Source audit: the adapter mints observation + reads the rule-computed
    surprise flag; it holds no rule engine and no argmax over a valuation. Surprise
    itself is the seed rule sg_surprise, not a Python conditional over graph state."""
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_surprise_town_world.py")
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
