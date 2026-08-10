"""bigville cognitive C4 (block 328000): allostatic load + coping (McEwen + Lazarus +
window of tolerance). Gates mirror BIGVILLE_STRESS_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_stress_world import BigvilleStressWorld   # noqa: E402


# ------------------------------------------------------ G-chronic-load-breaks (headline)
def test_chronic_load_breaks_the_agent():
    w = BigvilleStressWorld()
    w.add_agent("Ada", window=1.0)
    # each stressor (0.3) is well within the window; no single one could break her.
    for _ in range(3):
        w.stress("Ada", 0.3)
        assert not w.broken("Ada"), "no single sub-window stressor breaks the agent"
    w.stress("Ada", 0.3)   # cumulative 1.2 > 1.0
    assert w.broken("Ada"), "chronic accumulation crosses the window and breaks her"


# ------------------------------------------------------ G-window-is-load-bearing
def test_a_wider_window_absorbs_more():
    def _run(window):
        w = BigvilleStressWorld()
        w.add_agent("B", window=window)
        for _ in range(4):
            w.stress("B", 0.3)
        return w.broken("B")
    assert _run(1.0) is True, "a narrow window breaks under the load"
    assert _run(3.0) is False, "a wide window absorbs the same load"


# ------------------------------------------------------ G-coping-restores (headline)
def test_coping_restores_the_agent():
    w = BigvilleStressWorld()
    w.add_agent("Ada", window=1.0, coping_relief=0.5)
    for _ in range(4):
        w.stress("Ada", 0.3)
    assert w.broken("Ada"), "over-loaded and broken"
    w.cope("Ada")
    assert not w.broken("Ada"), "co-regulation drops the load back within the window -> recovery"
    assert w.load("Ada") <= 1.0


# ------------------------------------------------------ G-chronic-vs-reset (falsifier)
def test_reset_between_stressors_never_accumulates():
    w = BigvilleStressWorld()
    w.add_agent("C", window=1.0, recovery=0.0)   # each rest wipes the load
    for _ in range(6):
        w.stress("C", 0.3)
        w.rest()
    assert not w.broken("C"), "reset between stressors -> no chronic accumulation -> no breakdown"
    assert w.load("C") == 0.0


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_stress():
    src = open(os.path.join(_ROOT, "worlds", "bigville_stress_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_stress.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"al_accumulate", "al_break", "al_cope", "al_recover", "al_rest"} <= names, names
