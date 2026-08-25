"""STRESS COMPRESSES APERTURE — gate for `seeds/stress_aperture.json`.

Prereg `STRESS_COMPRESSES_APERTURE_PREREG.md` (block 366000), results
`STRESS_COMPRESSES_APERTURE_RESULTS.md`.

`arousal_window_coreg` narrows the WINDOW OF TOLERANCE under dysregulation. This
narrows a second thing on a different axis — what the agent can RESOLVE — and the
manifold audit counts an unresolved dimension as UNASSESSED (`information_loss`),
never as failed (`loss`). So a dysregulated agent is measurably STUPID in the
technical sense: not wrong, unable to tell.

The test that carries the claim is `test_evidence_is_inert_at_any_strength`. If
stress merely lowered a gain, more evidence would compensate — that is what a gain
IS. It does not, at 42x the horizon, because the distinction is not resolvable at
any exposure.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import stress_aperture_measure as m  # noqa: E402


def _cell(dysregulated, strength=8.0):
    a, ep, pol, cands = m._bench(dysregulated, evidence_strength=strength)
    return (a, pol, m._read(a, ep, pol, cands[1]), m._selection(a, ep, pol, cands))


def test_a_regulated_agent_sees_the_escape():
    """Control. Without it every result below is consistent with a fixture that
    was never assessable in the first place."""
    _a, _pol, esc, sel = _cell(False)
    assert esc["loss"] == 1.0, "the regulated agent did not see the escape"
    assert esc["information_loss"] == 0.0
    assert esc["resolved"] == 1.0
    assert len(sel["feasible"]) == 1 and len(sel["selected"]) == 1


def test_stress_makes_the_agent_unable_to_tell_NOT_wrong():
    """The headline. Compression must register as unassessed, never as failure —
    an agent that believed it saw a failure it could not see would be a worse bug
    than the one this fixes."""
    _a, pol, esc, _sel = _cell(True)
    assert pytest.approx(1.0) == _a_compressed(_a, pol)
    assert esc["loss"] == 0.0, (
        "an unresolvable dimension was reported as a failure")
    assert esc["information_loss"] > 0.0
    assert esc["resolved"] == 0.0


def _a_compressed(a, pol):
    return a.s.node(pol)["attrs"].get("sa_compressed")


def test_the_signature_is_stupid_not_stubborn_or_ignorant():
    """All three present identically from outside — nothing gets selected. The
    record must separate them."""
    _a, _pol, _esc, sel = _cell(True)
    assert len(sel["unestablished"]) == 2, "compression did not read as stupid"
    assert sel["feasible"] == [], "feasibility claimed without assessment"
    assert sel["selected"] == []
    assert sel["withheld_minimal"] == [], (
        "compression is reading as stubbornness — nothing was withheld")


@pytest.mark.parametrize("strength", [1.0, 3.0, 8.0, 32.0, 128.0])
def test_evidence_is_inert_at_any_strength(strength):
    """THE TEST THE CLAIM LIVES OR DIES ON.

    A gain is a thing more evidence overcomes. An aperture is not. At 128 — 42x
    the horizon — the stressed agent still cannot resolve the dimension the
    escape lives in, and never will."""
    _a, _pol, esc, _sel = _cell(True, strength=strength)
    assert esc["resolved"] == 0.0, f"evidence at {strength} resolved the projection"
    assert esc["loss"] == 0.0, f"evidence at {strength} turned blindness into failure"
    assert esc["information_loss"] > 0.0


def test_regulation_restores_what_stress_removed():
    """Positive control for the above. Without it, 'nothing helps' passes
    trivially for an agent that is simply broken."""
    _a, _pol, stressed, _s = _cell(True)
    _b, _pol2, calm, sel = _cell(False)
    assert stressed["resolved"] == 0.0 and calm["resolved"] == 1.0
    assert stressed["loss"] == 0.0 and calm["loss"] == 1.0
    assert len(sel["feasible"]) == 1


def test_both_ways_of_going_unassessed_compose():
    """Not registered, and worth pinning because it shows the two limitations are
    one quantity rather than two bolted together.

    Two dimensions, horizon 3. At budget 1 the agent loses 2 ticks x 1 resolvable
    dimension = 2 cells to the budget, plus 3 ticks x 1 blind dimension = 3 cells
    to the aperture: 5. At budget >= 3 only the aperture's 3 remain."""
    _a, _p, starved, _s = _cell(True, strength=1.0)
    _b, _q, fed, _t = _cell(True, strength=8.0)
    assert starved["information_loss"] == 5.0, starved
    assert fed["information_loss"] == 3.0, fed
