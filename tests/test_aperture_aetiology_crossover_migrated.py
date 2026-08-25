"""THE CROSSOVER — gate for the registered two-aetiologies result.

Prereg `APERTURE_AETIOLOGY_CROSSOVER_PREREG.md` (block 365000), results
`APERTURE_AETIOLOGY_CROSSOVER_RESULTS.md`. Two mechanically distinct ways for two
agents to share a delusion, responding to OPPOSITE interventions:

  CONFIRMER  each the other's confirmer, apertures full  -> cured by GROUNDING
  FRAME      one shared negotiated aperture, no confirmer -> cured by REFRAMING

The two off-diagonal cells are what make it a claim rather than two anecdotes, and
`test_the_gate_is_not_a_second_precision_gate` is the one that would actually kill
it: if enough grounding strength ever moved a frame-locked belief, aperture
narrowing would be attenuation rather than a distinct mechanism.

Slow-ish (each cell runs 70 engine ticks over two dyads), so the cells are shared
via a module-scoped fixture.
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import aperture_aetiology_measure as m  # noqa: E402

BASIN_W = m.P.basin_w


@pytest.fixture(scope="module")
def cells():
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    got = {}
    for aet in ("CONFIRMER", "FRAME"):
        for iv in ("NONE", "GROUNDING", "REFRAMING"):
            got[f"{aet}/{iv}"] = m.cell(aet, iv)
    return got


def _verdict(c):
    return tuple(c["members"][n]["committed_final"] for n in ("a", "b"))


def test_both_aetiologies_are_delusional_without_intervention(cells):
    """The controls. Without these the cures below prove nothing — an arm that was
    never in the wrong basin cannot be corrected out of it."""
    assert _verdict(cells["CONFIRMER/NONE"]) == ("W", "W")
    assert _verdict(cells["FRAME/NONE"]) == ("W", "W")


def test_grounding_cures_the_CONFIRMER_aetiology(cells):
    """Replication of PSYCHOSIS_DEMO_RESULTS.md P8/P6, declared as a replication
    in prereg §1 rather than presented as a discovery."""
    assert _verdict(cells["CONFIRMER/GROUNDING"]) == ("R", "R")


def test_grounding_does_NOT_cure_the_FRAME_aetiology(cells):
    """The first off-diagonal. Truthful evidence at nearly 4x the standing level,
    delivered every tick, changes nothing — because it is not perceived as
    evidence. The channel flag says so in the graph."""
    c = cells["FRAME/GROUNDING"]
    assert _verdict(c) == ("W", "W")
    assert c["channel"]["a"]["channel_open"] == 0.0, (
        "the reality channel is open in the frame arm — the bridge is not gating")


def test_reframing_cures_the_FRAME_aetiology(cells):
    """THE CONFIRMATORY CELL. Never measured before this rung, and only reachable
    because `af_retract_when_every_party_accepts` was built for it: the rule the
    machinery was missing turned out to be the treatment the mechanism implies.

    Note the standing evidence is UNCHANGED at 0.4 — nothing new is supplied.
    Removing the frame lets what was already there land."""
    c = cells["FRAME/REFRAMING"]
    assert _verdict(c) == ("R", "R")
    assert c["channel"]["a"]["channel_open"] == 1.0, (
        "the channel did not open after retraction")
    assert c["channel"]["a"]["resolves"] == sorted(m.FULL), (
        f"the aperture did not widen back: {c['channel']['a']['resolves']}")


def test_reframing_does_NOT_cure_the_CONFIRMER_aetiology(cells):
    """The second off-diagonal — and the weakest cell in the table, pinned here
    for completeness rather than as evidence. There is no frame in the CONFIRMER
    arm, so retraction is a no-op by construction; this only shows the harness
    does not cure that arm by some unintended route."""
    assert _verdict(cells["CONFIRMER/REFRAMING"]) == ("W", "W")


def test_the_gate_is_not_a_second_precision_gate():
    """THE TEST THAT WOULD KILL THE CLAIM.

    A precision gate DIVIDES a non-zero pull, so enough strength always wins. The
    aperture gate ZEROES it, so no strength ever does. At 3.0 — 7.5x the standing
    evidence and double the strength P8 measured escaping in five ticks — a
    frame-locked belief must not move off its basin centre.

    If this ever passes with R, aperture narrowing is attenuation, the second
    folie-a-deux row in SUBSTRATE_DISORDER_MAP.md is wrong, and the results
    document says so is the headline."""
    c = m.cell("FRAME", "GROUNDING", w_ground=3.0)
    assert _verdict(c) == ("W", "W"), (
        "strong enough grounding moved a frame-locked belief — the aperture gate "
        "is attenuating, not zeroing, and the two aetiologies are one")
    assert c["members"]["a"]["belief_final"] == pytest.approx(BASIN_W, abs=1e-6), (
        f"the belief moved off the basin centre: {c['members']['a']['belief_final']}")


def test_removing_the_bridge_dissolves_the_delusion_entirely():
    """G-gate-is-load-bearing, in its measured (stronger) form. Same fixture, same
    standing evidence, one seed absent — and the arm corrects with NO intervention
    at all, because weak friction alone suffices when nothing is confirming and
    nothing is blocking. Isolates the gate as the cause rather than any incidental
    property of the fixture."""
    assert _verdict(m.cell("FRAME", "NONE", gate=False)) == ("R", "R")
