"""Gate for the TARGET-SENSITIVE FAST PATH (block 287000,
seeds/bigville_fast_bond.json + worlds/bigville_fast_bond_world.py).

A cheap bond signal in the shallow impulse makes the fast collapse bond-directed --
resolving the 282000-c weak-bond targeting finding WITHOUT a first deliberation. The
harness decides SHALLOW-ONLY to isolate the fast path. ZERO new Rust.
"""
import ast, os
import pytest
from worlds.bigville_fast_bond_world import BigvilleFastBondWorld as W

# Neutral listed FIRST -> a bare impulse tie would pick it (the 282000-c failure).
_TG = [{"name": "Neutral", "affection": 0.0}, {"name": "Friend", "affection": 3.0}]


def test_fast_path_prefers_the_friend():
    w = W(_TG, fast_gain=0.1)
    try:
        r = w.decide()
        assert r["chosen"] == "help" and r["target"] == "Friend"
    finally:
        w.close()


def test_falsifier_no_fast_gain_reproduces_the_targeting_failure():
    w = W(_TG, fast_gain=0.0)
    try:
        r = w.decide()
        assert r["target"] == "Neutral"          # the first-tie failure returns
    finally:
        w.close()


def test_fast_pull_is_bond_directed_and_cheap():
    w = W(_TG, fast_gain=0.1)
    try:
        w.provide()
        i_friend = w.impulse("help", "Friend")
        i_neutral = w.impulse("help", "Neutral")
        assert i_friend > i_neutral               # bond-directed fast pull
        assert i_neutral == 0.70                   # neutral = base_weight, no nudge
        # the fast nudge (0.30) is SMALL vs the deep supergraph plan coupling (~1.5)
        assert 0.0 < (i_friend - i_neutral) < 0.6
    finally:
        w.close()


def test_resentment_lowers_the_fast_pull():
    w = W([{"name": "Rival", "resentment": 3.0}], fast_gain=0.1)
    try:
        w.provide()
        assert w.impulse("help", "Rival") < 0.70   # a resented target repels the fast pull
    finally:
        w.close()


def test_no_python_agent_decision():
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "worlds", "bigville_fast_bond_world.py")
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
