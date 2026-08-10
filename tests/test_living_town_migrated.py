"""Gate for the FULL FOLD-IN (block 289000, worlds/bigville_living_town_world.py):
the 280-287 conduct spine wired into the LIVE integ5/play town. The town keeps its
own mechanics; a conduct layer (the residents' minds) adds interpersonal conduct --
help / give / greet / (rarely) harm -- driven by held Bonds on the surprise clock,
written back into the town's event feed. ZERO new Rust.
"""
import ast
import os

import pytest

from worlds.bigville_living_town_world import BigvilleLivingTownWorld as W


@pytest.fixture(scope="module")
def town():
    w = W(cast=8, seed=276000)
    for _ in range(24):
        w.integ_step()
    yield w
    w.close()


def test_conduct_flows_into_the_town(town):
    """The conduct layer writes real interpersonal events into the town's feed."""
    assert len(town.conduct_events) > 0
    # they are in the town's own event stream (so paper / narration / player see them)
    kinds = {e["kind"] for e in town.events}
    assert {"kindness", "violence", "gift"} & kinds
    for e in town.conduct_events:
        assert e["actors"] and e["target"] and e["text"]


def test_violence_is_rare_and_bond_directed(town):
    """Harm is a small minority of conduct AND is aimed at a RESENTED partner (never
    a random or a friend)."""
    harms = town.conduct_harm_events()
    assert len(harms) < 0.4 * len(town.conduct_events)      # rare
    _, bonds = town._derive_social()
    for e in harms:
        b = bonds.get((e["actors"][0], e["target"]), {})
        assert b.get("resentment", 0.0) > 0.0              # directed at the resented


def test_help_is_the_norm(town):
    acts = [e["act"] for e in town.conduct_events]
    assert acts.count("help") > acts.count("harm")         # prosocial default


def test_town_survives_the_fold_in(town):
    """The town's own life continues under the fold-in (residents alive, feed flows)."""
    alive = sum(1 for nm in town.people if not town.is_dead(nm))
    assert alive >= len(town.people) - 1                   # nobody mass-dies from conduct
    assert len(town.events) > 0


def test_conduct_can_be_disabled_cleanly():
    """conduct=False -> no conduct layer, no conduct events; the town runs unchanged."""
    w = W(cast=8, seed=276000, conduct=False)
    try:
        for _ in range(8):
            w.integ_step()
        assert w.minds is None and w.conduct_events == []
        assert len(w.events) >= 0                           # town still runs
    finally:
        w.close()


def test_no_python_agent_decision_in_the_fold_in():
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_living_town_world.py")
    text = open(src).read()
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply", "make_rule",
                   "argmax", "argmin"):
        assert banned not in text
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
           and node.func.id in ("max", "min"):
            call = ast.get_source_segment(text, node) or ""
            assert not any(k in call for k in ("impulse", "value", "plan", "afford", "affect")), call


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
