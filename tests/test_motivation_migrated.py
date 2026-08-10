"""bigville cognitive C1 (block 325000): the motivational core -- drives + Psi modulators.
The dominant urge selects the pursued goal (an Argmax collapse over the agent's own drives);
modulators derive from arousal; the selection threshold gives goal-hysteresis; different
weight profiles diverge. Gates mirror BIGVILLE_MOTIVATION_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_motivation_world import BigvilleMotivationWorld   # noqa: E402


# ------------------------------------------------------ G-drive-profiles-diverge (headline)
def test_drive_profiles_diverge_on_the_same_world():
    w = BigvilleMotivationWorld()
    lv = dict(sustenance=(1.0, 0.6, 1.0))  # same kinds + levels; only the weights differ
    w.add_agent("Scholar", drives={"sustenance": (1.0, 0.6, 1.0), "competence": (1.0, 0.3, 2.0),
                                   "affiliation": (1.0, 0.5, 0.5), "certainty": (1.0, 0.4, 1.8)})
    w.add_agent("Socialite", drives={"sustenance": (1.0, 0.6, 1.0), "competence": (1.0, 0.3, 0.5),
                                     "affiliation": (1.0, 0.5, 2.5), "certainty": (1.0, 0.4, 0.4)})
    w.run()
    assert w.pursues("Scholar") == "competence", w.pursues("Scholar")
    assert w.pursues("Socialite") == "affiliation", w.pursues("Socialite")


# ------------------------------------------------------ G-dominant-selects + satisfy-flips
def test_the_dominant_urge_selects_and_satisfaction_flips_the_goal():
    w = BigvilleMotivationWorld()
    w.add_agent("A", drives={"competence": (1.0, 0.3, 2.0), "certainty": (1.0, 0.4, 1.8),
                             "affiliation": (1.0, 0.6, 0.5)})
    w.run()
    assert w.pursues("A") == "competence", "the max-weighted-urge drive is pursued"
    w.set_level("A", "competence", 1.0)   # satisfy it
    w.run()
    assert w.pursues("A") == "certainty", "pursuit flips to the next-most-urgent drive"


# ------------------------------------------------------ G-modulators-track-arousal
def test_modulators_track_arousal():
    w = BigvilleMotivationWorld()
    # big deficits -> high arousal; then satisfy everything -> low arousal.
    w.add_agent("A", drives={"competence": (1.0, 0.0, 1.0), "affiliation": (1.0, 0.0, 1.0)},
                res_gain=0.6, thr_gain=0.5)
    w.run()
    hi_ar, hi_res, hi_thr = w.arousal("A"), w.resolution("A"), w.selection_threshold("A")
    assert hi_ar > 0.5 and hi_res < 0.6 and hi_thr > 0.3, (hi_ar, hi_res, hi_thr)
    for k in ("competence", "affiliation"):
        w.set_level("A", k, 1.0)
    w.run()
    assert w.arousal("A") < hi_ar, "satisfying drives lowers arousal"
    assert w.resolution("A") > hi_res, "lower arousal -> higher resolution"
    assert w.selection_threshold("A") < hi_thr, "lower arousal -> lower selection threshold"


# ------------------------------------------------------ G-selection-threshold-is-load-bearing (headline)
def test_selection_threshold_gives_hysteresis():
    """Establish competence as the pursued goal, then make affiliation slightly out-urge it.
    A high-threshold agent perseveres; a zero-threshold agent switches immediately."""
    def _agent(thr_gain):
        w = BigvilleMotivationWorld()
        w.add_agent("A", drives={"competence": (1.0, 0.2, 1.0), "affiliation": (1.0, 0.3, 1.0)},
                    thr_gain=thr_gain)
        w.run()                                  # competence urge 0.8 > affiliation 0.7 -> pursues competence
        assert w.pursues("A") == "competence"
        w.set_level("A", "affiliation", 0.0)     # affiliation urge 1.0 now, 0.2 over competence's 0.8
        w.run()
        return w.pursues("A")
    assert _agent(thr_gain=0.5) == "competence", "high threshold -> perseveration"
    assert _agent(thr_gain=0.0) == "affiliation", "zero threshold -> immediate switch"


# ------------------------------------------------------ G-uniform-drives-collapse-divergence (falsifier)
def test_uniform_profiles_pursue_the_same_goal():
    w = BigvilleMotivationWorld()
    prof = {"competence": (1.0, 0.3, 1.5), "affiliation": (1.0, 0.3, 1.0), "certainty": (1.0, 0.3, 1.0)}
    for n in ("A", "B", "C"):
        w.add_agent(n, drives=dict(prof))
    w.run()
    assert len({w.pursues(n) for n in ("A", "B", "C")}) == 1, "identical profiles -> identical pursuit"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_motivation():
    src = open(os.path.join(_ROOT, "worlds", "bigville_motivation_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply", "argmax", "max("):
        assert forbidden not in src, f"adapter must not decide motivation: {forbidden!r}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_motivation.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"mv_urge", "mv_arousal", "mv_bootstrap", "mv_refresh", "mv_switch"} <= names, names
    assert "Argmax" in json.dumps(seed), "goal selection must be an Argmax collapse in the seed"
