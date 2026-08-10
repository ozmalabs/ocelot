"""bigville cognitive C2 (block 327000): attention as a bounded, arousal-modulated
resource. focus follows the Yerkes-Dodson inverted-U, multiplies outcomes, and gates
capacity. Gates mirror BIGVILLE_ATTENTION_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_attention_world import BigvilleAttentionWorld   # noqa: E402


def _focus_at(w, name, arousal):
    w.set_arousal(name, arousal); w.run()
    return w.focus(name)


# ------------------------------------------------------ G-Yerkes-Dodson-inverted-U (headline)
def test_focus_follows_the_yerkes_dodson_inverted_u():
    w = BigvilleAttentionWorld()
    w.add_agent("X", arousal_opt=0.5, overload_gain=2.0)
    xs = [0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0]
    ys = [_focus_at(w, "X", a) for a in xs]
    peak = ys.index(max(ys))
    assert xs[peak] == 0.5, f"focus should peak near the optimum: peak at arousal {xs[peak]}"
    assert all(ys[k + 1] > ys[k] for k in range(peak)), f"rises to the peak: {ys}"
    assert all(ys[k + 1] < ys[k] for k in range(peak, len(ys) - 1)), f"falls after the peak: {ys}"
    assert ys[peak] > ys[0] and ys[peak] > ys[-1], "under- and over-arousal both below optimum"


# ------------------------------------------------------ G-focus-multiplies-outcome
def test_focus_multiplies_task_outcome():
    w = BigvilleAttentionWorld()
    w.add_agent("Focused", baseline_arousal=0.5)     # at the optimum -> focus 1
    w.add_agent("Frazzled", baseline_arousal=1.0)    # over-aroused -> focus 0.5
    fi = w.give_task("Focused", base_skill=1.0, demand=0.0)
    gi = w.give_task("Frazzled", base_skill=1.0, demand=0.0)
    w.run()
    assert w.task_outcome("Focused", fi) > w.task_outcome("Frazzled", gi), \
        "same skill, better focus -> better outcome"


# ------------------------------------------------------ G-drives-degrade-focus (ties to C1)
def test_unmet_drive_pressure_degrades_focus():
    w = BigvilleAttentionWorld()
    w.add_agent("X", baseline_arousal=0.5, unmet_pressure=0.0)   # optimal
    w.run(); calm = w.focus("X")
    w.set_pressure("X", 0.4)                                     # unmet drives push arousal past optimum
    w.run(); pressed = w.focus("X")
    assert pressed < calm, f"unmet-drive pressure lowers focus: {calm} -> {pressed}"


# ------------------------------------------------------ G-capacity-is-bounded
def test_a_demanding_task_needs_focus():
    w = BigvilleAttentionWorld()
    w.add_agent("X", arousal_opt=0.5, overload_gain=2.0)
    w.set_arousal("X", 1.0); w.run()                            # over-aroused -> focus 0.5
    lo = w.give_task("X", base_skill=1.0, demand=0.7); w.run()
    assert not w.task_done("X", lo), "a demanding task fails under low focus"
    w.set_arousal("X", 0.5); w.run()                            # optimal -> focus 1.0
    hi = w.give_task("X", base_skill=1.0, demand=0.7); w.run()
    assert w.task_done("X", hi), "the same task completes under good focus"


# ------------------------------------------------------ G-unbounded-falsifier
def test_without_the_overload_term_the_curve_disappears():
    w = BigvilleAttentionWorld()
    w.add_agent("Flat", arousal_opt=0.5, overload_gain=0.0)     # no inverted-U
    ys = [_focus_at(w, "Flat", a) for a in (0.0, 0.5, 1.0)]
    assert ys == [1.0, 1.0, 1.0], f"overload_gain=0 -> flat focus, no curve: {ys}"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_attention():
    src = open(os.path.join(_ROOT, "worlds", "bigville_attention_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_attention.json")))
    assert {"at_focus", "at_complete"} <= {r["name"] for r in seed["rules"]}
