"""Gate for the GENERAL BASE AFFORDANCE VOCABULARY (block 280000,
seeds/world_affordances.json + worlds/affordance_world.py).

The claim: a world PROVIDES affordances (admissible actions) computed from the
scene; the agent's decision COLLAPSES over the afforded set; violence (`harm`) is
a member of the basis OFFERED ONLY WHEN a target is in range (precondition-gated,
not permanently on the menu) at a LOW prior, and rarely selected. Grounded in
AFFORDANCE_VOCABULARY_SCIENCE.md. Purely additive over the block-279000 decision
core (impulse channel); ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.affordance_world import AffordanceWorld

ALL_TYPES = {"move", "extract_resource", "transform", "transfer",
             "communicate", "ingest", "rest", "harm", "help"}


def test_provision_computes_afforded_set_from_scene():
    """The afforded set = exactly the actions whose precondition the scene meets."""
    # Alone in a field with a fishing spot + bread + an open cell.
    w = AffordanceWorld(sees=[], sources=[("fish", 5.0)],
                        holds=[{"kind": "bread", "consumable": 1.0}], adjacent=True)
    try:
        got = set(w.provide())
        # extract (source w/ stock), ingest (consumable), move (cell), rest (null)
        assert got == {"extract_resource", "ingest", "move", "rest"}, got
        # NO social actions -- nobody is present.
        assert not ({"harm", "communicate", "transfer"} & got)
        # NO transform -- bread is consumable, not an input good.
        assert "transform" not in got
    finally:
        w.close()


def test_empty_scene_affords_only_the_null_action():
    w = AffordanceWorld()
    try:
        assert w.provide() == ["rest"]
    finally:
        w.close()


def test_scene_change_changes_afforded_set():
    """Bringing an agent into the scene lights up the agent-directed affordances."""
    alone = AffordanceWorld(sources=[("fish", 5.0)])
    withbob = AffordanceWorld(sees=["Bob"], sources=[("fish", 5.0)])
    try:
        a, b = set(alone.provide()), set(withbob.provide())
        new = b - a
        # co-presence adds exactly the agent-directed / communicative affordances.
        assert new == {"harm", "help", "communicate"}, new  # transfer needs a held good
        assert "harm" not in a and "harm" in b
    finally:
        alone.close(); withbob.close()


def test_harm_is_precondition_gated_and_low_weight():
    """`harm` is offered ONLY when a target is in range, and at a LOW prior --
    representable (so a norm against it is representable), not always-on."""
    alone = AffordanceWorld(sources=[("fish", 5.0)],
                            holds=[{"kind": "bread", "consumable": 1.0}])
    withbob = AffordanceWorld(sees=["Bob"],
                              holds=[{"kind": "bread", "consumable": 1.0}])
    try:
        # No target -> harm not afforded, impulse 0 (you can't strike an empty field).
        assert "harm" not in alone.provide()
        assert alone.impulse("harm") == 0.0
        # Target present -> harm afforded, but its prior is LOW vs ordinary actions.
        aff = withbob.provide()
        assert "harm" in aff
        assert 0.0 < withbob.impulse("harm") < withbob.impulse("ingest")
        assert withbob.impulse("harm") < withbob.impulse("communicate")
    finally:
        alone.close(); withbob.close()


def test_effects_rewrite_the_graph():
    """Committing to an action fires its STRIPS effect (the world rewrite)."""
    # extract: decrement source stock + mint a raw good.
    w = AffordanceWorld(sources=[("fish", 5.0)])
    w.provide()
    before = w.s.node(w._sources[0])["attrs"]["stock"]
    w.commit("extract_resource")
    after = w.s.node(w._sources[0])["attrs"]["stock"]
    assert after == before - 1.0
    assert "fish" in w.holds_kinds()
    w.close()
    # harm: reduce the target's vital state.
    w2 = AffordanceWorld(sees=["Bob"])
    w2.provide()
    h0 = w2.target("Bob")["health"]
    w2.commit("harm")
    assert w2.target("Bob")["health"] == h0 - 25.0
    assert w2.target("Bob")["harmed"] == 1.0
    w2.close()
    # communicate: mint a Sign.
    w3 = AffordanceWorld(sees=["Bob"])
    w3.provide(); w3.commit("communicate")
    assert len(w3.signs()) == 1
    w3.close()
    # ingest: consume + raise energy.
    w4 = AffordanceWorld(holds=[{"kind": "bread", "consumable": 1.0}], energy=40.0)
    w4.provide(); w4.commit("ingest")
    assert w4.actor()["energy"] == 48.0
    w4.close()


def test_effect_fires_once_not_in_a_fixpoint_loop():
    """The enacted guard makes an effect fire exactly once (no runaway rewrite)."""
    w = AffordanceWorld(sources=[("fish", 9.0)])
    w.provide()
    w.commit("extract_resource")
    # run the fixpoint again -- the guard must prevent a second decrement.
    w.inner.run_rules()
    assert w.s.node(w._sources[0])["attrs"]["stock"] == 8.0
    w.close()


def test_falsifier_ignore_preconditions_affords_harm_with_no_target():
    """CONTROL: without the precondition gate, `harm` is afforded in an empty
    room -- proving the preconditions do real work (this is the BROKEN behaviour)."""
    real = AffordanceWorld()                       # empty scene
    broken = AffordanceWorld(ignore_preconditions=True)  # empty, gate bypassed
    try:
        assert real.provide() == ["rest"]          # only the null action
        assert set(broken.provide()) == ALL_TYPES       # everything, ungrounded
        assert broken.impulse("harm") > 0.0        # violence with nobody present
    finally:
        real.close(); broken.close()


def test_decision_collapses_over_afforded_set_and_declines_violence():
    """The decision core collapses over the afforded set; `harm` is afforded (a
    body is present) yet NOT selected -- afforded != selected."""
    w = AffordanceWorld(sees=["Bob"], sources=[("fish", 5.0)],
                        holds=[{"kind": "bread", "consumable": 1.0}], adjacent=True)
    try:
        w.provide()
        w.attach_decision_core()
        r = w.decide()
        assert "harm" in r["considered"]           # violence is on the menu
        assert r["chosen"] != "harm"               # ...but the collapse declines it
        assert r["chosen"] in ALL_TYPES
    finally:
        w.close()


def test_decision_in_empty_scene_can_only_rest():
    w = AffordanceWorld()
    try:
        w.provide(); w.attach_decision_core()
        assert w.decide()["chosen"] == "rest"
    finally:
        w.close()


def test_no_python_agent_decision_in_the_world_adapter():
    """Source audit: the world adapter holds no rule engine and no argmax/min/max
    over an agent valuation -- which actions are afforded, and what each does, are
    seed RULES. (Same discipline as the decision core.)"""
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "affordance_world.py")
    text = open(src).read()
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply",
                   "make_rule", "argmax", "argmin"):
        assert banned not in text, f"world adapter must not use {banned}"
    # no max()/min() over a comprehension of graph valuations (a hidden decision)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
           and node.func.id in ("max", "min"):
            # sorting/keying by a static index attr is mechanical layout, allowed;
            # a max/min over impulse/value/appeal would be a decision -- forbid it.
            call = ast.get_source_segment(text, node) or ""
            assert not any(k in call for k in ("impulse", "value", "appeal",
                                               "plan", "afford")), call


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
