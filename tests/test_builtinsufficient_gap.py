"""gap_prioritiser BUILT-BUT-INSUFFICIENT source — the meta-gap fix (iter-42).

Locks the load-bearing property: a capability that is BUILT but MEASURED below its
target (the agent's yardstick / do-contrast output) is RE-OPENED as a first-class gap,
ranked by the SHORTFALL (target - measured), so the selector prioritises the measured
bottleneck over the highest-compression-payoff pick. The decision is a graph Rule +
the score Term (shortfall*BOOST), not Python: a capability measured AT/ABOVE target
mints nothing (read as closed); one below target mints exactly one axis weighted by how
far it underperforms. This is the agent self-prioritising "already-built-but-insufficient"
— the frontier mechanism order-N synthesis alone could not provide.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate
from domains import gap_prioritiser as gp


def _axis(s, keys, n_unifies, order=1):
    """Mint a synthesised CapabilityAxis with n_unifies postulate concepts (= payoff),
    the way build_axis_env would. Mechanical."""
    lvl, rnk = gp.axis_pipeline_level(keys)
    ax = s.add_node(gp.AXIS_TYPE, {
        gp.AXIS_FLAG: 1.0, "axis_sig": sorted({k.lower() for k in keys}),
        "capability_keys": list(keys), "attempted_marginal": 0.0,
        gp.SHORTFALL_ATTR: 0.0, gp.ORDER_ATTR: float(order),
        "pipeline_level": lvl, gp.LEVEL_RANK_ATTR: float(rnk)})
    try:
        s.add_production({"src": {"type": gp.AXIS_TYPE, "var": "a"},
                          "edge_type": gp.UNIFIES_EDGE,
                          "tgt": {"type": "Concept", "var": "b"},
                          "provenance": "test"})
    except Exception:
        pass
    for i in range(n_unifies):
        c = s.add_node("Concept", {"name": f"{keys[0]}_{i}"})
        s.add_edge(ax, gp.UNIFIES_EDGE, c, {})
    return ax


def test_builtinsufficient_capability_outranks_the_compression_pick():
    # The post-iter-40 shape: the highest-compression capability is cross-speaker
    # clustering (82 postulates); the front-end is BUILT but measured below target.
    s = Substrate()
    clus = _axis(s, ["cross-speaker-clustering"], 82)   # recognition, highest payoff
    _axis(s, ["transitional probability"], 27)          # segmentation

    # BEFORE: the bare compression ranker picks clustering.
    before = gp.rank_gaps(s)
    assert before[0]["axis_id"] == clus

    # the agent MEASURES its built front-end below target (the yardstick shortfall).
    gp.record_measured_capability(
        s, ["all-pole", "levinson", "lpc-formant"], measured=0.18, target=0.50)
    minted = gp.synthesise_builtinsufficient_gaps(s)
    assert len(minted) == 1

    # AFTER: the re-opened front-end axis (shortfall 0.32) outranks clustering.
    after = gp.rank_gaps(s)
    assert gp.axis_pipeline_level(after[0]["capability_keys"])[0] == "feature_extraction"
    assert after[0]["axis_id"] == minted[0]
    # the pick (enacted by the graph Rule's Argmax) is the feature front-end.
    pick = gp.pick_frontier(s)
    assert gp.axis_pipeline_level(pick["capability_keys"])[0] == "feature_extraction"


def test_larger_shortfall_outranks_smaller_shortfall():
    # Among built-but-insufficient capabilities, the one furthest below its target wins.
    s = Substrate()
    gp.record_measured_capability(
        s, ["speaker normalization", "formant ratio"], measured=0.55, target=0.65)  # 0.10
    gp.record_measured_capability(
        s, ["all-pole", "levinson"], measured=0.18, target=0.50)                     # 0.32
    gp.synthesise_builtinsufficient_gaps(s)
    rows = gp.rank_gaps(s)
    assert "all-pole" in [str(k).lower() for k in rows[0]["capability_keys"]]
    assert "speaker normalization" in [str(k).lower() for k in rows[1]["capability_keys"]]


def test_at_or_above_target_capability_is_read_as_closed_no_axis():
    # A built capability measured AT/ABOVE its target is correctly read as closed:
    # the Rule mints NO axis (the meta-gap's correct other side — only INSUFFICIENT
    # built capabilities re-open).
    s = Substrate()
    gp.record_measured_capability(
        s, ["coarticulation predict-remove"], measured=0.70, target=0.50)
    minted = gp.synthesise_builtinsufficient_gaps(s)
    assert minted == []
    # exactly-at-target also mints nothing (strict below).
    gp.record_measured_capability(s, ["lpc-formant"], measured=0.50, target=0.50)
    assert gp.synthesise_builtinsufficient_gaps(s) == []


def test_synthesis_is_idempotent_per_reading():
    # A built-but-insufficient reading mints exactly one axis; re-running the synthesis
    # without a new measurement mints nothing more (the Rule clears its pending flag).
    s = Substrate()
    gp.record_measured_capability(s, ["all-pole", "levinson"], measured=0.2, target=0.6)
    assert len(gp.synthesise_builtinsufficient_gaps(s)) == 1
    assert gp.synthesise_builtinsufficient_gaps(s) == []
    # a NEW reading (still below target) updates in place and re-arms exactly one synth.
    gp.record_measured_capability(s, ["all-pole", "levinson"], measured=0.3, target=0.6)
    again = gp.synthesise_builtinsufficient_gaps(s)
    assert len(again) <= 1   # at most one (dedup by cap_sig in build_axis_env)


def test_reopened_axis_carries_provenance_to_the_measurement():
    # The re-opened axis is grounded in the measured shortfall (a re_opens edge from
    # the MeasuredCapability), not invented — it is measurement-derived, flagged.
    s = Substrate()
    mc = gp.record_measured_capability(
        s, ["all-pole", "levinson"], measured=0.2, target=0.6)
    minted = gp.synthesise_builtinsufficient_gaps(s)
    assert len(minted) == 1
    axis = minted[0]
    assert axis in list(s.neighbours(mc, "re_opens"))
    a = s.node(axis)["attrs"]
    assert a[gp.INSUFFICIENT_FLAG] == 1.0
    assert abs(a[gp.SHORTFALL_ATTR] - 0.4) < 1e-9


def test_decision_is_in_the_term_not_python():
    # The shortfall-boost is in the score Term: a synthesised axis (shortfall 0) is
    # unaffected; an axis with a positive shortfall gets boost*shortfall added. The
    # numbers come out of substrate.evaluate, not Python arithmetic.
    s = Substrate()
    syn = _axis(s, ["cross-speaker-clustering"], 5)
    base = int(s.evaluate(gp._Pred(gp.score_term("x")), {"x": syn}))
    assert base == 5 * gp.ORDER_K - 1            # payoff*K - order, no boost
    # set a shortfall on it and the same Term adds boost*shortfall natively.
    s.set_attr(syn, gp.SHORTFALL_ATTR, 0.25)
    boosted = int(s.evaluate(gp._Pred(gp.score_term("x")), {"x": syn}))
    assert boosted == base + int(0.25 * gp.SHORTFALL_BOOST)
