"""perception_self_assessment — the agent's own quality signal on its UNITS.

Locks the load-bearing property: the self-monitor judges segmentation by whether
the agent's own unit-sequence carries structure BEYOND its own frequency baseline
(the frequency-artifact control), and the graph-resident flagging rule sets the
frontier to 'perception' exactly when the units are poor — with NO external label.
"""
from __future__ import annotations

import random

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate
from domains.perception_self_assessment import (
    measure_unit_predictability, record_perception_quality,
    install_perception_frontier_rule, agent_flag_perception, get_frontier,
    get_reliability,
    register_with_meta_monitor, report_to_meta_monitor,
    install_frontier_rank_rule, agent_set_frontier_rank,
    install_perception_gap_rule, agent_synthesise_perception_gap)
from domains import gap_prioritiser as gp


def _flag(signal):
    sub = Substrate()
    record_perception_quality(sub, signal)
    fr = install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    return agent_flag_perception(sub, fr["rule_index"])


def _flag_and_reliability(signal):
    sub = Substrate()
    record_perception_quality(sub, signal)
    fr = install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    flag = agent_flag_perception(sub, fr["rule_index"])
    return flag, get_reliability(sub)


def test_structured_units_beat_frequency_and_are_not_flagged():
    # Genuinely ordered units: the next unit IS determined by the current one.
    struct = [["a", "b", "c", "a", "b", "c"]] * 8
    sig = measure_unit_predictability(struct)
    assert sig["predict_over_freq"] > 1.25          # beats its own freq baseline
    assert sig["compress_ratio"] < 0.85
    assert _flag(sig) == "none"


def test_frequency_artifact_is_flagged():
    # A dominant filler unit inflates recurrence + over-chance, but the sequence
    # carries NO order beyond raw frequency — the exact trap to catch.
    rng = random.Random(0)
    filler = []
    for _ in range(20):
        s = ["SIL" if rng.random() < 0.6 else rng.choice(["x", "y", "z", "w"])
             for _ in range(8)]
        filler.append(s)
    sig = measure_unit_predictability(filler)
    # the misleading number looks fine, the honest one does not
    assert sig["predict_over_chance"] > 1.5
    assert sig["predict_over_freq"] < 1.25
    assert _flag(sig) == "perception"


def test_noise_units_are_flagged():
    # i.i.d. units drawn from a realistic skewed unit distribution (real perceived
    # units are never uniform): NO order, so the bigram cannot beat the frequency
    # baseline. Over many tokens predict_over_freq collapses toward 1.0.
    rng = random.Random(1)
    pool = ["a"] * 8 + ["b"] * 4 + ["c"] * 2 + ["d", "e"]   # skewed, like real
    noise = [[rng.choice(pool) for _ in range(12)] for _ in range(60)]
    sig = measure_unit_predictability(noise)
    assert sig["predict_over_freq"] < 1.25
    assert _flag(sig) == "perception"


def test_flagging_is_graph_resident_and_clears_pending():
    bad = {"predict_top1": 0.1, "predict_chance": 0.1, "predict_over_chance": 1.0,
           "predict_freq_baseline": 0.1, "predict_over_freq": 1.0,
           "shuffled_over_freq": 1.0, "tokens_per_lexicon": 10.0,
           "info_gain_bits": 0.0, "compress_ratio": 1.0, "recurrence": 0.1,
           "lexicon_size": 20, "n_tokens": 200}
    sub = Substrate()
    record_perception_quality(sub, bad)
    fr = install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    assert agent_flag_perception(sub, fr["rule_index"]) == "perception"
    # the rule cleared its own pending flag and the verdict is readable from state
    assert sub.node(root)["attrs"]["perception_quality_pending"] == 0
    assert get_frontier(sub) == "perception"


def test_meta_monitor_watches_perception_payoff():
    # The unit_segmentation process exists with a payoff that is perception
    # quality (predict_over_freq), not recognition.
    sub = Substrate()
    p = register_with_meta_monitor(sub)
    assert p is not None
    sig = {"lexicon_size": 80, "predict_over_freq": 1.1}
    report_to_meta_monitor(sub, sig)
    a = sub.node(p)["attrs"]
    assert a["name"] == "unit_segmentation"
    assert a["payoff_current"] == pytest.approx(1.1)
    assert a["effort_history"][-1] == pytest.approx(80.0)


# --------------------------------------------------------------------------
# THE RELIABILITY GATE (Step 1 of the fix): the frontier='perception' flag fires
# ONLY when the reading is trustworthy. The gate is a general predicate (adequate
# sample + shuffle-collapse), not a hard-coded "ignore the 108-utt sample".
# --------------------------------------------------------------------------

def test_starved_singleton_dominated_sample_is_gated_not_flagged():
    # The exact artifact: lexicon ~= tokens (singleton-dominated), so pof is 1.0 with
    # no statistical power, and the shuffle control cannot bite (shuf == pof). The
    # gate must SUPPRESS the false 'perception' -> 'inconclusive', reliability low.
    starved = {"predict_top1": 0.0, "predict_chance": 0.03,
               "predict_over_chance": 0.0, "predict_freq_baseline": 0.0,
               "predict_over_freq": 1.0, "shuffled_over_freq": 1.0,
               "tokens_per_lexicon": 1.97,            # lex 31 ~= tok 61 (the 108-utt case)
               "info_gain_bits": 0.0, "compress_ratio": 0.19, "recurrence": 0.5,
               "lexicon_size": 31, "n_tokens": 61}
    flag, rel = _flag_and_reliability(starved)
    assert flag == "inconclusive"        # NOT a false 'perception'
    assert rel == "low"


def test_starved_sample_does_not_arm_the_downstream_rank_or_gap():
    # A gated (inconclusive) reading must NOT pull the rank to the perception/units
    # rank, and must NOT synthesise a perception/units gap — the artifact must not
    # propagate into the ranker.
    starved = {"predict_top1": 0.0, "predict_chance": 0.03,
               "predict_over_chance": 0.0, "predict_freq_baseline": 0.0,
               "predict_over_freq": 1.0, "shuffled_over_freq": 1.0,
               "tokens_per_lexicon": 1.97,
               "info_gain_bits": 0.0, "compress_ratio": 0.19, "recurrence": 0.5,
               "lexicon_size": 31, "n_tokens": 61}
    sub = Substrate()
    record_perception_quality(sub, starved)
    fr = install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    assert agent_flag_perception(sub, fr["rule_index"]) == "inconclusive"
    # the gate left both downstream-arming flags at 0 (not re-armed on a low reading).
    assert sub.node(root)["attrs"]["frontier_rank_pending"] == 0
    assert sub.node(root)["attrs"]["perception_gap_pending"] == 0
    # the flag->rank Rule, fired, yields the far-downstream default (NOT rank 1.0).
    ri = install_frontier_rank_rule(sub)
    sub.set_attr(root, "frontier_rank_pending", 1)   # drive it once to read the map
    assert agent_set_frontier_rank(sub, ri["rule_index"]) == 999.0
    # no perception/units gap is synthesised from an inconclusive reading.
    pg = install_perception_gap_rule(sub)
    sub.set_attr(root, "perception_gap_pending", 1)
    assert agent_synthesise_perception_gap(sub, pg["rule_index"]) is None


def test_reliable_failing_sample_still_flags_perception():
    # Well-sampled but genuinely structureless units (adequate tok/lex, pof at floor):
    # the gate trusts the FAIL -> 'perception', reliability high. The gate suppresses
    # only STARVED readings, not real failures (it is not "ignore small N" blindly —
    # a large structureless N is still flagged).
    bad = {"predict_top1": 0.05, "predict_chance": 0.05,
           "predict_over_chance": 1.0, "predict_freq_baseline": 0.05,
           "predict_over_freq": 1.0, "shuffled_over_freq": 1.0,
           "tokens_per_lexicon": 20.0,            # adequate sample, power to assert no-order
           "info_gain_bits": 0.0, "compress_ratio": 1.0, "recurrence": 0.4,
           "lexicon_size": 30, "n_tokens": 600}
    flag, rel = _flag_and_reliability(bad)
    assert flag == "perception"
    assert rel == "high"


def test_reliable_passing_sample_reads_none_when_shuffle_bites():
    # Units that pass the floor AND survive the shuffle control (real pof well above
    # the shuffled pof): a RELIABLE pass -> frontier 'none', reliability high. This is
    # the at-scale FSDD case (pof clears the floor, order is real).
    good = {"predict_top1": 0.6, "predict_chance": 0.05,
            "predict_over_chance": 12.0, "predict_freq_baseline": 0.2,
            "predict_over_freq": 3.0, "shuffled_over_freq": 1.0,
            "tokens_per_lexicon": 7.4,             # the at-scale FSDD adequacy
            "info_gain_bits": 1.2, "compress_ratio": 0.3, "recurrence": 0.7,
            "lexicon_size": 100, "n_tokens": 741}
    flag, rel = _flag_and_reliability(good)
    assert flag == "none"
    assert rel == "high"


def test_apparent_pass_without_shuffle_collapse_is_inconclusive_not_none():
    # An apparent pass (pof above floor) whose shuffle does NOT bite (shuf ~= real) is
    # a small-sample fluke, not real order: the gate refuses to call it a reliable
    # 'none' -> 'inconclusive'. The shuffle witness is load-bearing in BOTH directions.
    fluke = {"predict_top1": 0.3, "predict_chance": 0.1,
             "predict_over_chance": 3.0, "predict_freq_baseline": 0.2,
             "predict_over_freq": 1.5, "shuffled_over_freq": 1.5,   # shuffle does NOT bite
             "tokens_per_lexicon": 6.0,
             "info_gain_bits": 0.1, "compress_ratio": 0.6, "recurrence": 0.5,
             "lexicon_size": 20, "n_tokens": 120}
    flag, rel = _flag_and_reliability(fluke)
    assert flag == "inconclusive"
    assert rel == "low"


def test_gate_is_general_over_measured_streams_not_a_hardcoded_subset():
    # End-to-end through measure_unit_predictability (real maths, no hand-set fields):
    # a singleton-dominated stream (each unit appears ~once) is gated; a well-sampled
    # ordered stream is a reliable pass. Proves the gate keys off the GENERAL sample /
    # shuffle predicates the maths produces, not a constant.
    singleton = [[f"u{i}_{j}" for j in range(2)] for i in range(40)]   # every unit unique
    sig_s = measure_unit_predictability(singleton)
    assert sig_s["tokens_per_lexicon"] < 4.0          # singleton-dominated
    assert _flag(sig_s) == "inconclusive"
    ordered = [["a", "b", "c", "a", "b", "c", "a", "b", "c"]] * 12     # well-sampled order
    sig_o = measure_unit_predictability(ordered)
    assert sig_o["tokens_per_lexicon"] >= 4.0
    assert _flag(sig_o) == "none"


# --------------------------------------------------------------------------
# Step-1 migration: the flag->RANK decision is now a graph RULE, not Python.
# --------------------------------------------------------------------------

def _root_with_flag(flag):
    s = Substrate()
    bad = {"predict_top1": 0.1, "predict_chance": 0.1, "predict_over_chance": 1.0,
           "predict_freq_baseline": 0.1, "predict_over_freq": 1.0,
           "shuffled_over_freq": 1.0, "tokens_per_lexicon": 10.0,
           "info_gain_bits": 0.0, "compress_ratio": 1.0, "recurrence": 0.1,
           "lexicon_size": 20, "n_tokens": 200}
    record_perception_quality(s, bad)
    root = next(n for n in s.nodes("PerceptionSelfRoot"))
    s.set_attr(root, "frontier", flag)
    s.set_attr(root, "frontier_rank_pending", 1)
    return s, root


def test_frontier_rank_is_set_by_a_graph_rule_not_python():
    # flag 'perception' -> the Rule writes the perception/units rank (1.0); 'none'
    # -> the unknown default (999.0). The DECISION is native (IfThenElse/Eq/Attr).
    s, _ = _root_with_flag("perception")
    info = install_frontier_rank_rule(s)
    assert agent_set_frontier_rank(s, info["rule_index"]) == 1.0
    s2, root2 = _root_with_flag("none")
    info2 = install_frontier_rank_rule(s2)
    assert agent_set_frontier_rank(s2, info2["rule_index"]) == 999.0
    # the rule cleared its own pending flag (graph-resident, self-clearing).
    assert s.node(next(n for n in s.nodes("PerceptionSelfRoot")))["attrs"][
        "frontier_rank_pending"] == 0


# --------------------------------------------------------------------------
# Step-2 fixer: units-failing -> SYNTHESISE a perception/units gap (a Rule),
# which the GUIDED ranker then LANDS on (the iter-6 residual, closed).
# --------------------------------------------------------------------------

def _seg_and_rec(s):
    """Mint the downstream gaps the unguided ranker prefers (high payoff)."""
    def axis(keys, n):
        lvl, rnk = gp.axis_pipeline_level(keys)
        ax = s.add_node(gp.AXIS_TYPE, {
            gp.AXIS_FLAG: 1.0, "capability_keys": list(keys),
            "attempted_marginal": 0.0, gp.ORDER_ATTR: 1.0,
            "pipeline_level": lvl, gp.LEVEL_RANK_ATTR: float(rnk)})
        try:
            s.add_production({"src": {"type": gp.AXIS_TYPE, "var": "a"},
                              "edge_type": gp.UNIFIES_EDGE,
                              "tgt": {"type": "Concept", "var": "b"},
                              "provenance": "test"})
        except Exception:
            pass
        for i in range(n):
            c = s.add_node("Concept", {"name": f"{keys[0]}_{i}"})
            s.add_edge(ax, gp.UNIFIES_EDGE, c, {})
        return ax
    return (axis(["cross-speaker-clustering"], 82),
            axis(["transitional probability"], 27))


def test_units_failing_synthesises_a_perception_gap_the_guided_ranker_lands_on():
    s = Substrate()
    rec, seg = _seg_and_rec(s)

    # the yardstick flags the units failing -> frontier 'perception'.
    s_bad = {"predict_top1": 0.1, "predict_chance": 0.1, "predict_over_chance": 1.0,
             "predict_freq_baseline": 0.1, "predict_over_freq": 1.0,
             "shuffled_over_freq": 1.0, "tokens_per_lexicon": 10.0,
             "info_gain_bits": 0.0, "compress_ratio": 1.0, "recurrence": 0.1,
             "lexicon_size": 20, "n_tokens": 200}
    record_perception_quality(s, s_bad)
    fr = install_perception_frontier_rule(s)
    root = next(n for n in s.nodes("PerceptionSelfRoot"))
    s.set_attr(root, "perception_quality_pending", 1)
    assert agent_flag_perception(s, fr["rule_index"]) == "perception"

    # UNGUIDED: the high-payoff recognition gap wins (no perception axis yet).
    base = gp.rank_gaps(s)
    assert base[0]["axis_id"] == rec

    # the NEW FIXER (a graph Rule): synthesise a perception/units axis AT rank 1.
    pg = install_perception_gap_rule(s)
    s.set_attr(root, "perception_gap_pending", 1)
    units = agent_synthesise_perception_gap(s, pg["rule_index"])
    assert units is not None
    a = s.node(units)["attrs"]
    assert a["pipeline_level"] == "perception_units"
    assert a[gp.LEVEL_RANK_ATTR] == 1.0
    # provenance: the gap is grounded in the yardstick shortfall (root edge).
    assert units in list(s.neighbours(root, "synthesised_gap"))

    # GUIDED at the perception frontier (rank 1.0): the pick now LANDS on the
    # synthesised perception/units gap — pick_rank == frontier_rank — NOT segmentation.
    guided = gp.pick_with_guidance(s, frontier_rank=1.0)
    assert guided["pick_changed"] is True
    assert guided["axis_id"] == units
    assert guided["pipeline_level"] == "perception_units"
    assert guided["axis_id"] != seg     # the iter-6 residual (segmentation) is gone


def test_synthesis_is_idempotent_and_only_fires_when_units_fail():
    # good units -> flag 'none' -> the Rule mints NO gap (it only fires on failure).
    s = Substrate()
    record_perception_quality(
        s, measure_unit_predictability([["a", "b", "c"] * 3] * 8))
    fr = install_perception_frontier_rule(s)
    root = next(n for n in s.nodes("PerceptionSelfRoot"))
    s.set_attr(root, "perception_quality_pending", 1)
    assert agent_flag_perception(s, fr["rule_index"]) == "none"
    pg = install_perception_gap_rule(s)
    s.set_attr(root, "perception_gap_pending", 1)
    assert agent_synthesise_perception_gap(s, pg["rule_index"]) is None
    assert not list(s.neighbours(root, "synthesised_gap"))

    # failing units -> exactly ONE gap, even if the synthesis is driven twice.
    s2 = Substrate()
    bad = {"predict_top1": 0.1, "predict_chance": 0.1, "predict_over_chance": 1.0,
           "predict_freq_baseline": 0.1, "predict_over_freq": 1.0,
           "shuffled_over_freq": 1.0, "tokens_per_lexicon": 10.0,
           "info_gain_bits": 0.0, "compress_ratio": 1.0, "recurrence": 0.1,
           "lexicon_size": 20, "n_tokens": 200}
    record_perception_quality(s2, bad)
    fr2 = install_perception_frontier_rule(s2)
    root2 = next(n for n in s2.nodes("PerceptionSelfRoot"))
    s2.set_attr(root2, "perception_quality_pending", 1)
    agent_flag_perception(s2, fr2["rule_index"])
    pg2 = install_perception_gap_rule(s2)
    s2.set_attr(root2, "perception_gap_pending", 1)
    agent_synthesise_perception_gap(s2, pg2["rule_index"])
    # second drive without re-arming -> no new node.
    agent_synthesise_perception_gap(s2, pg2["rule_index"])
    assert len(list(s2.neighbours(root2, "synthesised_gap"))) == 1
