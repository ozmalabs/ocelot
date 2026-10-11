"""Null-candidate census (argmin_tie instrument, 2026-10-10).

`cmp_value` orders `Value::None` below every number, so a candidate whose cost
attr is MISSING silently wins `Argmin` (and loses `Argmax`). Paper 02c's finite
comparison specification requires an undefined cost to make the minimum
undefined. Before changing behaviour, the census measures exposure. Pinned:

  * the ordering fact the census exists for (a missing cost wins Argmin);
  * the census counts a mixed firing, a null win, and an all-null firing,
    and attributes them to the selector site;
  * a fully-defined comparison counts nothing (both directions);
  * `count` mode changes no result.
"""
from __future__ import annotations

import json

import pytest

srs = pytest.importorskip("substrate_rs")
native = srs._native


def _sub(values):
    s = srs.Substrate()
    for i, v in enumerate(values):
        attrs = {"idx": i}
        if v is not None:
            attrs["score"] = float(v)
        s.add_node("Cand", attrs)
    return s


def _sel(kind):
    return srs.Term(kind, source=srs.Term("NodesOfType", node_type="Cand"), var_name="c",
                    value=srs.Attr(srs.Var("c"), "score"), default=None)


def _eval(values, kind, mode="count"):
    native.argmin_tie_reset()
    native.argmin_tie_enable(mode)
    try:
        s = _sub(values)
        out = s.evaluate(_sel(kind))
        return s, out, native.argmin_tie_stats(), native.argmin_null_sites()
    finally:
        native.argmin_tie_enable("off")


def _idx(s, node):
    return s.node(node)["attrs"]["idx"]


MIXED = [5.0, None, 3.0]


def test_a_missing_cost_silently_wins_argmin():
    s, out, _, _ = _eval(MIXED, "Argmin", mode="off")
    assert _idx(s, out) == 1, "the candidate with NO score is picked over 3.0"


def test_census_counts_the_null_win_and_names_the_site():
    s, out, st, sites = _eval(MIXED, "Argmin")
    assert _idx(s, out) == 1                       # count mode: behaviour unchanged
    assert (st["null_mixed"], st["null_wins"], st["null_all"]) == (1, 1, 0)
    assert len(sites) == 1 and sites[0]["selector"] == "Argmin"
    assert json.loads(sites[0]["value_term"])["key"] == "score"
    assert (sites[0]["mixed"], sites[0]["wins"]) == (1, 1)


def test_argmax_mixed_firing_is_counted_without_a_null_win():
    s, out, st, _ = _eval(MIXED, "Argmax")
    assert _idx(s, out) == 0
    assert (st["null_mixed"], st["null_wins"], st["null_all"]) == (1, 0, 0)


def test_all_null_comparison_is_counted_separately():
    _, out, st, _ = _eval([None, None], "Argmin")
    assert out is not None                         # the fold still returns the first element
    assert (st["null_mixed"], st["null_wins"], st["null_all"]) == (0, 0, 1)


def test_defined_costs_and_empty_sources_count_nothing():
    s, out, st, sites = _eval([5.0, 3.0], "Argmin")
    assert _idx(s, out) == 1
    assert (st["null_mixed"], st["null_wins"], st["null_all"]) == (0, 0, 0) and sites == []
    _, out, st, _ = _eval([], "Argmin")
    assert out is None and st["empties"] == 1 and st["null_all"] == 0


def test_off_mode_counts_nothing():
    _, _, st, _ = _eval(MIXED, "Argmin", mode="off")
    assert (st["null_mixed"], st["null_wins"], st["null_all"]) == (0, 0, 0)
