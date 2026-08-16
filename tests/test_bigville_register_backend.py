"""Regression for domains/bigville_register_backend.py -- the ocelot-side
half of the CAN register wiring named in
CAN_REGISTER_QUANTIZATION_RESULTS.md Sec8 item 2: "an ocelot-side backend
... that calls this rung's can_register_decode_band rule per encounter."
The bigville-side half (tie_strength/band_code on ActorContext) already
landed, bigville commit 1b79a0f.
"""
from __future__ import annotations

import pytest

from domains.bigville_register_backend import (
    DEFAULT_RESOLUTION_BINS,
    DEFAULT_RESOLUTION_LEVEL,
    RegisterDecisionEngine,
)


@pytest.fixture(scope="module")
def engine():
    return RegisterDecisionEngine()


# ---------------------------------------------------------------------
# 1. decode_band matches the engine's own decision for a known composition
#    (same formula/anchors as tests/test_can_register_quantization.py --
#    coarsest resident, resolution_bins=2, structurally never 'neutral').
# ---------------------------------------------------------------------
def test_decode_band_matches_registered_effective_bins_formula(engine):
    result = engine.decode_band(resolution_bins=8, resolution_level=0.5, band_code=0)
    assert result["effective_bins"] == pytest.approx(4)  # round(8*0.5)


def test_decode_band_coarsest_resident_never_neutral(engine):
    labels = {engine.decode_band(2, 1.0, band)["register_label"] for band in range(6)}
    assert "neutral" not in labels
    assert labels <= {"formal", "casual"}


def test_decode_band_label_direction_is_convergent_with_closeness(engine):
    stranger = engine.decode_band(6, 1.0, 0)["register_label"]
    family = engine.decode_band(6, 1.0, 5)["register_label"]
    assert stranger == "formal"
    assert family == "casual"


# ---------------------------------------------------------------------
# 2. Out-of-codebook band_code (the un-built -1 rival/feud divergence
#    mechanism, RESULTS.md Sec8 item 3) is skipped, not approximated.
# ---------------------------------------------------------------------
def test_decode_band_returns_none_for_rival_band(engine):
    assert engine.decode_band(6, 1.0, -1) is None


# ---------------------------------------------------------------------
# 3. No graph growth across repeated calls -- the scratch RegisterProfile/
#    RegisterObservation nodes minted per decode must be retired.
# ---------------------------------------------------------------------
def test_decode_band_does_not_grow_the_graph(engine):
    inner = engine._inner
    before = len(inner.nodes("RegisterProfile")) + len(inner.nodes("RegisterObservation"))
    for i in range(20):
        engine.decode_band(6, 1.0, i % 6)
    after = len(inner.nodes("RegisterProfile")) + len(inner.nodes("RegisterObservation"))
    assert after == before == 0


# ---------------------------------------------------------------------
# 4. decide_registers -- the ActorContext-shaped entry point, mirroring
#    bigville's real observations["nearby_residents"] dict shape
#    (bigville commit 1b79a0f: id/name/role/position/distance/tie_strength/
#    band_code).
# ---------------------------------------------------------------------
def test_decide_registers_over_actorcontext_shaped_input(engine):
    nearby = [
        {"id": "Ben", "name": "Ben", "role": "hand", "position": (1, 1),
         "distance": 0, "tie_strength": 2.5, "band_code": 3.0},
        {"id": "Cora", "name": "Cora", "role": "hand", "position": (1, 2),
         "distance": 1, "tie_strength": 0.0, "band_code": 0.0},
    ]
    decisions = engine.decide_registers({}, nearby)
    assert set(decisions) == {"Ben", "Cora"}
    assert decisions["Ben"]["register_label"] in {"formal", "neutral", "casual"}
    assert decisions["Ben"]["band_code"] == 3
    assert decisions["Cora"]["band_code"] == 0


def test_decide_registers_uses_documented_fixed_defaults_when_trait_absent(engine):
    """No real bigville actor exposes resolution_bins/resolution_level via
    ActorContext.personality today (Sec8 item 1, not yet built) -- confirm
    the honest, documented fallback fires rather than crashing or silently
    fabricating precision."""
    nearby = [{"id": "Ben", "band_code": 3.0}]
    via_absence = engine.decide_registers({}, nearby)
    via_explicit_default = engine.decide_registers(
        {"resolution_bins": DEFAULT_RESOLUTION_BINS,
         "resolution_level": DEFAULT_RESOLUTION_LEVEL}, nearby)
    assert via_absence["Ben"] == via_explicit_default["Ben"]


def test_decide_registers_respects_a_carried_resolution_bins_trait(engine):
    nearby = [{"id": "Ben", "band_code": 0.0}]
    coarse = engine.decide_registers({"resolution_bins": 2}, nearby)
    fine = engine.decide_registers({"resolution_bins": 12}, nearby)
    assert coarse["Ben"]["effective_bins"] != fine["Ben"]["effective_bins"]


def test_decide_registers_skips_residents_with_no_band_code(engine):
    nearby = [{"id": "Stranger"}]
    assert engine.decide_registers({}, nearby) == {}


def test_decide_registers_skips_rival_band_residents(engine):
    nearby = [{"id": "Rival", "band_code": -1.0}]
    assert engine.decide_registers({}, nearby) == {}
