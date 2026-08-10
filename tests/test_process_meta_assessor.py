"""process_meta_assessor — the PROCESS-LEVEL meta-assessor over a research loop.

Locks the load-bearing properties the brief requires:
  • on THIS session's loop it AUTOMATICALLY flags domain_spinning (probe never
    crossed target — the thing the OLD single-process meta_monitor missed),
    below_frontier on the recognition-picked iterations while perception was the
    frontier, and fix_the_outcome on the +0-fixer gate that did not move its source;
  • the rules are GENERAL predicates with ZERO session-specific constants — proven
    on an efficient control (flags nothing) and an all-spinning control (flags
    domain_spinning).
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate
from domains import process_meta_assessor as pma
from domains import meta_monitor as mm


# THIS session's loop (matches scripts/process_meta_assessor_demo.py).
SESSION = [
    # (label, effort, probe, fixer, pick_level, pick_rank, moved_source)
    ("iter-1", 1.0, -8.0, 1.0, "perception_units", 1.0, 1),
    ("iter-2", 2.0, -6.0, 2.0, "feature_extraction", 4.0, 1),
    ("iter-3", 3.0, -6.0, 3.0, "recognition", 5.0, 1),
    ("iter-4", 4.0, -4.0, 3.0, "recognition", 5.0, 1),
    ("iter-5-gate", 4.5, -4.0, 3.0, "recognition", 5.0, 0),
    ("iter-5", 5.0, -4.0, 4.0, "recognition", 5.0, 1),
]


def _build(iters, frontier_level="perception_units", frontier_rank=1.0):
    s = Substrate()
    rules = pma.install_all_rules(s)
    pma.set_frontier(s, frontier_level, frontier_rank)
    for label, eff, probe, fix, lvl, rank, moved in iters:
        pma.record_iteration(s, label, eff, probe, fix,
                             pick_level=lvl, pick_rank=rank, moved_source=moved)
    return s, rules


def test_session_loop_flags_what_old_meta_monitor_missed():
    s, rules = _build(SESSION)
    rep = pma.agent_assess(s, rules)
    # (a) probe spinning — never crossed target. OLD meta_monitor missed this.
    assert rep["loop_issue"] == "domain_spinning"
    # (b) below-frontier on recognition picks (perception was the frontier), and
    #     NOT on iter-1 which picked AT the frontier.
    bf = set(rep["flagged_iterations"]["below_frontier"])
    assert {"iter-3", "iter-4"}.issubset(bf)
    assert "iter-1" not in bf
    # (c) fix-the-outcome ONLY on the +0-fixer gate that did not move its source;
    #     iter-4 also added +0 fixer but MOVED its source, so must NOT fire.
    assert set(rep["flagged_iterations"]["fix_the_outcome"]) == {"iter-5-gate"}
    # (+) fixer progress is recognised as REAL (a separate channel): not flagged.
    assert rep["fixer_progressing"] == 1


def test_old_meta_monitor_misses_the_session_loop():
    # The OLD detector, fed the same probe channel, returns [] — the regression we
    # are fixing (effort_rise=4 << effort_min_rise=20 and one conflated channel).
    s = Substrate()
    iss = mm.install_meta_issue_rule(s)["rule_index"]
    mm.register_process(s, "research_loop")
    # The 5 iterations as the single-process detector saw them (probe series).
    for eff, probe in [(1.0, -8.0), (2.0, -6.0), (3.0, -6.0), (4.0, -4.0),
                       (5.0, -4.0)]:
        mm.report(s, "research_loop", eff, probe)
    assert mm.agent_check_meta(s, iss) == []


def test_efficient_control_flags_nothing():
    eff_loop = [
        ("e1", 1.0, -2.0, 1.0, "perception_units", 1.0, 1),
        ("e2", 2.0,  0.5, 2.0, "perception_units", 1.0, 1),
        ("e3", 3.0,  2.0, 3.0, "perception_units", 1.0, 1),
        ("e4", 4.0,  4.0, 4.0, "perception_units", 1.0, 1),
        ("e5", 5.0,  6.0, 5.0, "perception_units", 1.0, 1),
    ]
    s, rules = _build(eff_loop)
    rep = pma.agent_assess(s, rules)
    assert rep["loop_issue"] == "none"
    assert not rep["flagged_iterations"]["below_frontier"]
    assert not rep["flagged_iterations"]["fix_the_outcome"]
    assert rep["fixer_progressing"] == 1


def test_all_spinning_control_flags_domain_spinning():
    spin_loop = [(f"s{i}", float(i), -5.0, 0.0, "perception_units", 1.0, 1)
                 for i in range(1, 6)]
    s, rules = _build(spin_loop)
    rep = pma.agent_assess(s, rules)
    assert rep["loop_issue"] == "domain_spinning"
    assert rep["fixer_progressing"] == 0


def test_below_frontier_is_general_over_the_rank_ordering():
    # Move the frontier DOWNSTREAM (to recognition); now the SAME recognition picks
    # are AT the frontier and must NOT be flagged — proving the rule reads the rank,
    # not a hard-coded level.
    s, rules = _build(SESSION, frontier_level="recognition", frontier_rank=5.0)
    rep = pma.agent_assess(s, rules)
    assert not rep["flagged_iterations"]["below_frontier"]


# --------------------------------------------------------------------------
# Step 1 — AUTO-WIRED FEEDS (the completed stub: live state, not hand-set).
# --------------------------------------------------------------------------

def test_pick_rank_feed_reuses_the_ranker_level_map():
    # pick_rank <- the ranker's OWN capability->level map, so the assessor's notion of
    # 'where the pick sits' is exactly the ranker's. Recognition picks rank downstream.
    assert pma.pick_rank_from_axis(["cross-speaker-clustering"]) == ("recognition", 5.0)
    assert pma.pick_rank_from_axis(["transitional probability"])[0] == "segmentation"


def test_moved_source_feed_reads_the_measurement_outcome():
    # moved_source <- measurement_feedback's empirical record: 1 if it beat baseline.
    from domains import measurement_feedback as mf
    s = Substrate()
    s.add_node(mf.OUTCOME_TYPE, {"attempted_key": "lpc", "beats_baseline": True})
    assert pma.moved_source_from_feedback(s, "lpc") == 1
    s.add_node(mf.OUTCOME_TYPE, {"attempted_key": "clust", "beats_baseline": False})
    assert pma.moved_source_from_feedback(s, "clust") == 0
    # no record for a key -> assume the build moved its source (1).
    assert pma.moved_source_from_feedback(s, "unseen") == 1


def test_frontier_feed_is_live_not_constant():
    # frontier_rank <- the LIVE perception flag: 'perception' -> upstream rank 1.0,
    # 'none' -> a far-downstream default (so nothing is below it). NOT a constant.
    from domains import perception_self_assessment as psa
    # good (structured) units -> flag none -> default rank
    s = Substrate()
    psa.record_perception_quality(
        s, psa.measure_unit_predictability([["a", "b", "c"] * 3] * 8))
    frr = psa.install_perception_frontier_rule(s)
    root = next(n for n in s.nodes("PerceptionSelfRoot"))
    s.set_attr(root, "perception_quality_pending", 1)
    psa.agent_flag_perception(s, frr["rule_index"])
    assert pma.frontier_rank_from_perception(s)[0] == "none"
    # bad (frequency-artifact) units -> flag perception -> upstream rank 1.0
    import random
    rng = random.Random(0)
    bad = [["SIL" if rng.random() < 0.6 else rng.choice(["x", "y", "z", "w"])
            for _ in range(8)] for _ in range(20)]
    s2 = Substrate()
    psa.record_perception_quality(s2, psa.measure_unit_predictability(bad))
    frr2 = psa.install_perception_frontier_rule(s2)
    root2 = next(n for n in s2.nodes("PerceptionSelfRoot"))
    s2.set_attr(root2, "perception_quality_pending", 1)
    psa.agent_flag_perception(s2, frr2["rule_index"])
    assert pma.frontier_rank_from_perception(s2) == ("perception_units", 1.0)
