"""GATE for `VISION_PREVISUAL_PREREG.md` — H3's double dissociation is VACUOUS.

Pins the fact that stopped the pre-visual rung before it burned a seed: the
photometric and relational paths in `seeds/vision_eye.json` are DISJOINT — no
rule reads both, so "waves do not calibrate the gain" and "light does not build
the relational structure" are both TRUE BY CONSTRUCTION, not findings.

WHY A TEST AND NOT JUST A DOCUMENT: if someone later wires the two paths
together — which `VISION_PREVISUAL_PREREG.md` §7 argues they SHOULD, via
`wave_world`'s existing "two pathways, one output" (`bursting = active OR
driven`) — then H3 becomes genuinely measurable and this rung is worth running.
**This test failing is GOOD NEWS.** It means the vacuity that stopped the rung is
gone. Read the pre-registration before "fixing" it.

Run explicitly by file (§12 — `-k vision` is a substring match).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.previsual_vacuity_audit import static_audit, cell  # noqa: E402


def test_no_rule_reads_both_the_photometric_and_the_relational_path():
    """THE VACUITY, statically. A rule reading both `lum`-family and `bursting`
    is the ONLY thing that could couple waves to the gain or light to the
    relational structure. There are none, so H3 cannot fail."""
    a = static_audit()
    assert a["coupling_rules"] == [], (
        "A rule now reads BOTH paths — H3's double dissociation may no longer "
        "be vacuous. See VISION_PREVISUAL_PREREG.md §3 and §7 before changing "
        "this test: the rung may now be worth running.")
    assert len(a["photometric"]) > 0 and len(a["relational"]) > 0


def test_the_audit_instrument_is_alive_before_it_reports_a_zero():
    """THE POSITIVE CONTROL, and it is the point. `eye=0` is the master
    default-off, so an audit that forgets to set it scores a PERFECT all-zero
    double dissociation off a corpse — which is what my first run did. Diffuse
    light MUST move theta, or no zero in that table means anything."""
    r = cell(0, waves=False, light=True, steps=200)
    assert r["dtheta"] > 1e-6, "photometric path INERT — every zero is a corpse"


def test_waves_move_the_gain_by_exactly_the_null_amount():
    """H3(a): waves' effect on theta is EXACTLY the no-input effect — i.e.
    exactly zero — because no edge joins them. Measured against the NULL arm,
    not against zero: theta drifts on its own (adapting to darkness), and
    without the null control that drift reads as a small wave effect."""
    waves = cell(0, waves=True, light=False, steps=200)
    null = cell(0, waves=False, light=False, steps=200)
    assert abs(waves["dtheta"] - null["dtheta"]) < 1e-9


def test_light_moves_the_relational_path_by_exactly_the_null_amount():
    """H3(b) — the half the eye rung never checked, and it is structural TOO.
    This is what makes the whole test vacuous rather than half-real."""
    light = cell(0, waves=False, light=True, steps=200)
    null = cell(0, waves=False, light=False, steps=200)
    assert abs(light["dw_rel"] - null["dw_rel"]) < 1e-9


def test_the_two_paths_are_perfectly_additive_which_is_the_tell():
    """`both` equals each single arm to machine precision, with zero
    interaction. Real coupled effects do not cancel like this; an architecture
    restating itself does."""
    both = cell(0, waves=True, light=True, steps=200)
    waves = cell(0, waves=True, light=False, steps=200)
    light = cell(0, waves=False, light=True, steps=200)
    assert abs(both["dtheta"] - light["dtheta"]) < 1e-9
    assert abs(both["dw_rel"] - waves["dw_rel"]) < 1e-9
