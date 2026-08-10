"""gap_prioritiser BELOW_FRONTIER guidance — the assessor's signal REDIRECTS the pick.

Locks the load-bearing property iteration 6 adds: the process-meta-assessor's
BELOW_FRONTIER signal is WIRED INTO THE RANKER (not observe-only). When the live
frontier is upstream of a high-payoff downstream axis, the guided ranking penalises the
downstream axis by how far below the frontier it is, so the Argmax RE-PICKS the
axis closest to the frontier — the pick CHANGES because of the assessor.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate
from domains import gap_prioritiser as gp


def _axis(s, keys, n_unifies, order=1):
    """Mint a CapabilityAxis with `n_unifies` distinct postulate concepts (= payoff)
    and its pipeline level-rank, the way build_axis_env would. Mechanical."""
    lvl, rnk = gp.axis_pipeline_level(keys)
    ax = s.add_node(gp.AXIS_TYPE, {
        gp.AXIS_FLAG: 1.0,
        "axis_sig": sorted({k.lower() for k in keys}),
        "capability_keys": list(keys),
        "attempted_marginal": 0.0,
        gp.ORDER_ATTR: float(order),
        "pipeline_level": lvl,
        gp.LEVEL_RANK_ATTR: float(rnk),
    })
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


def test_below_frontier_signal_redirects_the_pick():
    s = Substrate()
    # the high-payoff DOWNSTREAM gap (what the unguided ranker prefers) ...
    rec = _axis(s, ["cross-speaker-clustering"], 8)        # recognition, rank 5
    # ... and a lower-payoff gap CLOSER to the frontier.
    seg = _axis(s, ["transitional probability"], 3)        # segmentation, rank 2

    # UNGUIDED: payoff dominates -> the downstream recognition gap wins.
    base = gp.rank_gaps(s)
    assert base[0]["axis_id"] == rec

    # GUIDED at the perception frontier (rank 1.0): the assessor's BELOW_FRONTIER
    # penalty, scaled by distance, sinks the far-downstream recognition axis below the
    # closer segmentation axis -> the pick CHANGES to the closer-to-frontier gap.
    guided = gp.pick_with_guidance(s, frontier_rank=1.0)
    assert guided["pick_changed"] is True
    assert guided["axis_id"] == seg
    assert "recognition" in guided["unguided_pick_level"]
    assert guided["pipeline_level"] == "segmentation"


def test_guidance_is_a_noop_when_frontier_is_downstream():
    # When the frontier is at/below every axis (rank 999 = flag 'none'), NO axis is
    # below it, so the guidance is a no-op and the base pick stands. Proves the signal
    # only fires when the units actually fail the yardstick.
    s = Substrate()
    rec = _axis(s, ["cross-speaker-clustering"], 8)
    _axis(s, ["transitional probability"], 3)
    guided = gp.pick_with_guidance(s, frontier_rank=999.0)
    assert guided["pick_changed"] is False
    assert guided["axis_id"] == rec


def test_at_or_above_frontier_axis_is_not_penalised():
    # An axis AT the frontier rank gets penalty 0; one strictly downstream is penalised.
    s = Substrate()
    seg = _axis(s, ["transitional probability"], 3)        # rank 2
    rows = gp.rank_with_guidance(s, frontier_rank=2.0)      # frontier AT segmentation
    seg_row = next(r for r in rows if r["axis_id"] == seg)
    assert seg_row["below_frontier"] == 0
    rows2 = gp.rank_with_guidance(s, frontier_rank=1.0)     # frontier upstream
    seg_row2 = next(r for r in rows2 if r["axis_id"] == seg)
    assert seg_row2["below_frontier"] == 1
