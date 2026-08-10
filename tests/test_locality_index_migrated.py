"""DURABLE GATE for the LOCALITY-INDEX STOP verdict.

`VISION_LOCALITY_INDEX_RESULTS.md` retired the scale-split rung's second
recommendation on ONE structural fact: **every hot edge type is a PERFECT
STAR**, so a locality restriction (`neighbours(hub, t)` in place of
`edges_by_type(t)`) cannot skip a single candidate and its payoff is exactly
zero.

A STOP verdict needs a gate as much as a build does -- more, arguably, because
nothing else in the tree will notice when it stops being true. If a future
change mints `has_cell` from more than one `Retina` (a tiled retina, a second
eye -- and `ozma_cardinality_is_a_magic_number` says a second eye is a
DESIRABLE direction), then hub purity drops below 1.0, the locality saving
becomes non-zero, and **the verdict this rung recorded must be re-derived
rather than inherited.** This test is what makes that re-derivation happen
loudly instead of silently.

It asserts the CLAIM, not the number: purity == 1.0 and saving == 0, at a small
grid. It does not re-run the sweep.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from scripts.locality_index_measure import HUB_EDGE_TYPES, hub_purity  # noqa: E402
from scripts.scale_split_measure import _boot_eye  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina  # noqa: E402


@pytest.fixture(scope="module")
def purity():
    g = 8
    s, ag, _ = _boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0)
    add_lateral_retina(world)
    return hub_purity(s)


def test_every_hot_edge_type_is_a_perfect_star(purity):
    """ONE node owns every edge of every hot type.

    This is the fact the STOP verdict rests on. `distinct_srcs == 1` is the
    strong form: not merely that one hub dominates, but that there is no other
    source at all."""
    live = {et: p for et, p in purity.items() if p["edges"]}
    assert live, "no hot edge types present — the fixture is not building a retina"
    for et, p in live.items():
        assert p["distinct_srcs"] == 1, (
            f"{et} has {p['distinct_srcs']} distinct sources — the star is no "
            f"longer perfect, so VISION_LOCALITY_INDEX_RESULTS.md's zero-payoff "
            f"finding MUST be re-derived, not inherited")
        assert p["purity"] == 1.0, (et, p)


def test_locality_saving_is_exactly_zero(purity):
    """The pre-registered H2 statistic, at its committed value.

    Exact integer equality, no tolerance: the claim is that the scan set and
    the hub's neighbourhood are THE SAME SET, and a tolerance here would be
    metric surgery on the one number that retires the recommendation."""
    total = sum(p["locality_saving"] for p in purity.values())
    assert total == 0, (
        f"locality saving is {total}, not 0 — a locality index would now skip "
        f"candidates the scan enumerates, and the STOP verdict is stale")


def test_hot_edge_type_list_still_matches_the_adapters(purity):
    """The hot list FALLS OUT of the world builders (PROTOCOL §13); if an
    adapter starts minting a new hub edge type, this list is silently
    incomplete and the purity result is silently partial."""
    assert set(purity) == set(HUB_EDGE_TYPES)
    assert purity["has_cell"]["edges"] > 0, "has_cell absent — fixture is dead"
