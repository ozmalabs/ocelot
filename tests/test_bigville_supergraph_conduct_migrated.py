"""Gate for the SUPERGRAPH CONDUCT VALUATION (block 282000-a,
seeds/bigville_supergraph_conduct.json).

The town is a supergraph: a directed action's value = plan_base +
(ep.w_supergraph * bond_w) * target_effect. ONE action-type-agnostic rule
replaces the three hand-tuned conduct_couple_* rules (281000), reproducing their
behaviour AND unlocking what the per-pair supergraph form adds: a per-agent
psychopathy knob (w_supergraph), the revived per-pair care prior (altruism_bias),
and spite as a signed per-pair weight. ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.bigville_conduct_world import BigvilleConductWorld


def _sup(**kw):
    return BigvilleConductWorld(valuation="supergraph", **kw)


def test_supergraph_reproduces_the_couple_harm_values_exactly():
    """The one supergraph rule reproduces the three 281000 coupling rules on the
    harm plan-values, side by side."""
    scen = dict(targets=[{"name": "Rival", "resentment": 3.0, "affection": -1.0},
                         {"name": "Friend", "affection": 3.0}], has_food=True)
    couple = BigvilleConductWorld(valuation="couple", **scen)
    sup = BigvilleConductWorld(valuation="supergraph", **scen)
    try:
        couple.provide(); sup.provide()
        for tgt in ("Rival", "Friend"):
            assert sup.plan_value("harm", tgt) == couple.plan_value("harm", tgt)
        # and the headline numbers are the 281000 fixtures.
        assert sup.plan_value("harm", "Rival") == 1.6
        assert sup.plan_value("harm", "Friend") == -1.9
    finally:
        couple.close(); sup.close()


def test_supergraph_reproduces_the_chosen_actions():
    """Every 281000 chosen-action signature holds under the supergraph valuation."""
    # care aimed at the friend, not harm
    w = _sup(targets=[{"name": "Rival", "resentment": 3.0, "affection": -1.0},
                      {"name": "Friend", "affection": 3.0}], has_food=True)
    r = w.decide(); w.close()
    assert r["chosen"] != "harm" and (r["target"] in (None, "Friend"))
    # provoked lone rival -> deliberated, directed harm
    w = _sup(targets=[{"name": "Foe", "resentment": 5.0, "affection": -4.0}])
    r = w.decide(); w.close()
    assert r["chosen"] == "harm" and r["target"] == "Foe" and r["deepened"] == 1
    # neutral acquaintance -> not harmed
    w = _sup(targets=[{"name": "Stranger"}])
    r = w.decide(); w.close()
    assert r["chosen"] != "harm"


def test_directedness_orderings():
    w = _sup(targets=[{"name": "Rival", "resentment": 3.0, "affection": -1.0},
                      {"name": "Friend", "affection": 3.0}])
    try:
        w.provide()
        assert w.plan_value("harm", "Rival") > w.plan_value("harm", "Friend")
        assert w.plan_value("help", "Friend") > w.plan_value("help", "Rival")
    finally:
        w.close()


def test_psychopathy_knob_weights_no_one():
    """NEW capability: the per-agent w_supergraph gate at 0 zeroes ALL per-pair
    care -- a global psychopath, regardless of any Bond (281000 had no such knob)."""
    w = _sup(targets=[{"name": "R", "resentment": 5.0}, {"name": "F", "affection": 5.0}],
             w_supergraph=0.0)
    try:
        w.provide()
        # every directed action falls back to its own stake (plan_base); no directedness.
        assert w.plan_value("harm", "R") == w.plan_value("harm", "F") == -0.40
        assert w.plan_value("help", "R") == w.plan_value("help", "F") == 0.60
    finally:
        w.close()


def test_altruism_bias_revives_kin_care_without_liking():
    """NEW: the previously-DEAD Bond slot altruism_bias now does work -- a per-pair
    care prior dissociable from affect ('you do not need to LIKE your kin')."""
    w = _sup(targets=[{"name": "Kin", "affection": 0.0, "resentment": 0.0}])
    try:
        for b in w.s.nodes("Bond"):
            w.s.set_attr(b, "altruism_bias", 0.3)   # blood-kin prior, zero affect
        w.provide()
        # helping kin scores above the bare stake even with no affection.
        assert w.plan_value("help", "Kin") > 0.60
    finally:
        w.close()


def test_spite_is_a_signed_per_pair_weight():
    """Spite has a principled per-pair form: resentment makes bond_w negative, so a
    negative target_effect (harm) times a negative weight scores harming UP."""
    w = _sup(targets=[{"name": "Foe", "resentment": 4.0, "affection": 0.0}])
    try:
        w.provide()
        assert w.plan_value("harm", "Foe") > -0.40    # harm scored above its base
    finally:
        w.close()


def test_falsifier_zero_weight_removes_directedness():
    w = _sup(targets=[{"name": "R", "resentment": 5.0}, {"name": "F", "affection": 5.0}],
             conduct_k=0.0)
    try:
        w.provide()
        assert w.plan_value("harm", "R") == w.plan_value("harm", "F") == -0.40
    finally:
        w.close()


def test_one_rule_not_three():
    """The supergraph seed collapses the three conduct_couple_* rules into one
    action-type-agnostic rule."""
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = json.load(open(os.path.join(root, "seeds", "bigville_supergraph_conduct.json")))
    names = [r["name"] for r in d["rules"]]
    assert names == ["conduct_supergraph_value"], names


def test_no_python_agent_decision_in_the_conduct_adapter():
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_conduct_world.py")
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
