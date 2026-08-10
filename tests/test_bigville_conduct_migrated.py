"""Gate for DIRECTED, BOND-COUPLED CONDUCT (block 281000,
seeds/bigville_conduct.json + worlds/bigville_conduct_world.py).

The payoff of the arc: the affordance vocabulary (280000) offers agent-directed
actions; the decision core (279000) collapses over them; and the held Bond (277000)
decides WHOM. Conduct is directed by relationships -- you help/give to those you
care for, and if you ever harm, it is the resented rival, never the loved friend.
Violence stays rare (a low prior that needs deliberation), but is representable and
correctly aimed. ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.bigville_conduct_world import BigvilleConductWorld


def test_bond_directs_the_plan_values():
    """The held Bond shapes each directed action's deep value: harm rises toward a
    resented rival + falls toward a loved friend; help rises toward the loved."""
    w = BigvilleConductWorld(targets=[
        {"name": "Rival", "resentment": 3.0, "affection": -1.0},
        {"name": "Friend", "affection": 3.0, "resentment": 0.0}])
    try:
        w.provide()
        assert w.plan_value("harm", "Rival") > w.plan_value("harm", "Friend")
        assert w.plan_value("help", "Friend") > w.plan_value("help", "Rival")
        # you do not harm whom you love: harm->Friend is driven below its base.
        assert w.plan_value("harm", "Friend") < -0.40
    finally:
        w.close()


def test_collapse_directs_care_at_the_cared_for_not_violence():
    """With a rival AND a friend present and no provocation strong enough to
    deliberate into violence, the collapse chooses a pro-social act aimed at the
    friend -- not harm, and not aimed at the rival."""
    w = BigvilleConductWorld(
        targets=[{"name": "Rival", "resentment": 3.0, "affection": -1.0},
                 {"name": "Friend", "affection": 3.0}],
        has_food=True)
    try:
        r = w.decide()
        assert r["chosen"] != "harm"
        if r["target"] is not None:            # a directed choice targets the friend
            assert r["target"] == "Friend"
    finally:
        w.close()


def test_harm_is_never_aimed_at_the_loved():
    """No scene makes the collapse harm a loved friend: harm->friend sits far below
    every alternative once affection is held."""
    w = BigvilleConductWorld(
        targets=[{"name": "Friend", "affection": 4.0, "resentment": 0.0}])
    try:
        r = w.decide()
        assert not (r["chosen"] == "harm" and r["target"] == "Friend")
        # and its plan value is strongly negative (help/greet dominate).
        assert w.plan_value("harm", "Friend") < 0.0
    finally:
        w.close()


def test_provoked_deliberate_harm_is_directed_at_the_rival():
    """Violence is RARE but representable: a deeply resented + disliked lone rival,
    with no better option, makes the fast pro-social response mis-fit (high
    residual) -> the collapse DEEPENS -> harm, directed at that rival."""
    w = BigvilleConductWorld(
        targets=[{"name": "Foe", "resentment": 5.0, "affection": -4.0}])
    try:
        r = w.decide()
        assert r["chosen"] == "harm"
        assert r["target"] == "Foe"
        assert r["deepened"] == 1        # it required deliberation, not an impulse
    finally:
        w.close()


def test_neutral_acquaintance_is_not_harmed():
    w = BigvilleConductWorld(
        targets=[{"name": "Stranger", "resentment": 0.0, "affection": 0.0}])
    try:
        assert w.decide()["chosen"] != "harm"
    finally:
        w.close()


def test_falsifier_zero_coupling_removes_all_directedness():
    """CONTROL: with the coupling gains at 0, plan_value collapses to plan_base for
    every directed action -- the collapse cannot tell a rival from a friend."""
    w = BigvilleConductWorld(
        targets=[{"name": "R", "resentment": 5.0}, {"name": "F", "affection": 5.0}],
        resent_gain=0.0, affection_gain=0.0)
    try:
        w.provide()
        assert w.plan_value("harm", "R") == w.plan_value("harm", "F") == -0.40
        assert w.plan_value("help", "R") == w.plan_value("help", "F") == 0.60
    finally:
        w.close()


def test_no_python_agent_decision_in_the_conduct_adapter():
    """Source audit: provision, the Bond coupling, and the choice are seed RULES;
    the adapter mints the scene and reads back. No rule engine, no argmax/min/max
    over a valuation."""
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_conduct_world.py")
    text = open(src).read()
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply",
                   "make_rule", "argmax", "argmin"):
        assert banned not in text, f"conduct adapter must not use {banned}"
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
           and node.func.id in ("max", "min"):
            call = ast.get_source_segment(text, node) or ""
            assert not any(k in call for k in ("impulse", "value", "appeal",
                                               "plan", "afford", "affect")), call


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
