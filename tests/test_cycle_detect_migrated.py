"""CYCLE DETECTION — the fixpoint predicate `run_rules` can actually satisfy.

THE FINDING THIS ACTS ON (`VISION_SETTLE8_RESULTS.md` §3.4, reproduced here on
this tree's own engine before anything was built): **the sheet SETTLES and
`run_rules` cannot SEE it.** Every cap-burning step is a ULP DITHER OF AN
ALREADY-SETTLED SHEET — `st_settle` writes `act_next` one ULP away, `st_commit`
copies it back, forever. `run_rules` offers exactly one termination semantics —
run to an EXACT fixed point — and **exact equality is unsatisfiable over float
arithmetic that dithers**, because a contraction's fixed point is generically
not representable in float64. This is a fact about exact-equality fixpoints over
floats, not about lattices, cortex or vision, and it afflicts any relaxation
this substrate ever runs.

WHY CYCLE DETECTION AND NOT A TOLERANCE (PROTOCOL §13)
------------------------------------------------------
The named route was "a fixpoint up to the arithmetic's own resolution"
(`np.spacing`/ULP). Its epsilon-FACTOR is open and was flagged as open: the
measured dithers span **1.0-4.0 ULP**, and "tune it to 4" is `mu = 0.024` all
over again.

**The obvious derivation is REFUTED BY THE DATA, and this rung re-measured it
rather than inheriting it (§12.4).** "Accumulated round-off of a sum over `d`
terms is ~`d`*ULP, and the graph supplies the degree" predicts MORE degree =>
MORE dither. Measured on this tree's engine: **c=4 (degree 4) dithers 4.0 ULP;
c=8 (degree 8) dithers 1.0 ULP.** More degree gave LESS dither, because rho<1
damps round-off (rho=1.000 at c=4 is MARGINAL — round-off in the checkerboard
mode never decays; rho=0.668 at c=8 damps it). The dither is set by the loop
GAIN ~1/(1-rho), not by the degree — and **rho is not something a rule can
know**, so a rule-side epsilon has nothing to fall out of either.

**A period-2 orbit IS a fixed point of the 2-step map.** Rule application is a
DETERMINISTIC map on graph state, so a REPEATED STATE proves the trajectory is
periodic and can never reach anything new — continuing to the cap cannot
discover anything. That test needs EXACT EQUALITY AGAINST HISTORY and NO
TOLERANCE: **it commits no float at all.** Not a tuned epsilon, not a knob —
there is no constant to name. That is why this route was taken over the
tolerance predicate (which needs an epsilon AND changes semantics for every
seed) and over don't-write-below-resolution (which relocates the same constant
into the rule).

WHAT IS AND IS NOT CLAIMED
--------------------------
* SOUNDNESS RESTS ON DETERMINISM, stated rather than assumed. The engine's only
  randomness is a seeded xorshift (`apc.rs`). An effect reading genuinely
  external mutable state between passes could revisit a graph state and still
  have somewhere new to go — which is why detection is **opt-in per call**,
  never global.
* The fingerprint is a 64-bit hash; a collision would end a run early
  (~2.7e-10 by birthday bound over the ~1e5 states a settling loop visits).
  The property is probabilistic, and that is stated rather than hidden.
* **This fixes TERMINATION, not the ceiling.** `rho(M) -> 1` as the sheet grows
  (0.45 -> 0.87 over n_side 3->6), so a GCAL-scale sheet settles arbitrarily
  slowly regardless of termination semantics. No tolerance and no cycle detector
  fixes that. See `test_rho_ceiling_is_not_fixed_by_this`.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

CAP = 200_000


def _sheet(c, *, seed=0, n_side=4):
    from scripts.settle_lib import build_sheet
    return build_sheet(seed=seed, n_side=n_side, connectivity=c,
                       settle=1.0, bubble=0.0)


def _act(w, us):
    return np.array([float(w.s.node(u)["attrs"].get("act", 0.0)) for u in us])


def _run(c, detect, steps=6, seed=0):
    w, us, _ = _sheet(c, seed=seed)
    apps = []
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        apps.append(int(w.s.tick(CAP, detect_cycles=detect)))
    return apps, _act(w, us)


# --- §9: the new semantics is OFF by default and cannot move a committed run ---

def test_detection_is_off_by_default():
    """PROTOCOL §9. The default MUST be off, or every committed result is
    exposed to a semantics change it never asked for.

    **THIS GATE IS SHARP ON PURPOSE, AND ITS FIRST DRAFT WAS NOT.** The obvious
    form — `s.tick(10) == s.tick(10, False)` on a fresh substrate — PASSES EVEN
    IF THE DEFAULT IS ON, because a graph with no cycle terminates identically
    either way. That is a gate that can only ever pass: §12's "a guard that runs
    the thing it guards is not a guard", in a new costume.

    So gate the DEFAULT where the default is observable: on a sheet that
    DITHERS. With detection off (the default) the committed loop MUST still burn
    the cap. If someone flips the default, this goes red immediately.
    POSITIVE-CONTROLLED: flipping the py.rs default to `true` and rebuilding
    turns this test RED (apps 200000 -> 4); reverting turns it GREEN."""
    w, us, _ = _sheet(4)
    w.step(ignite_k=1)
    apps_default = int(w.s.tick(CAP))          # Python-wrapper default
    assert apps_default >= CAP, (
        f"tick() with NO flag terminated in {apps_default} applications on a "
        f"dithering sheet. The committed semantics is to burn the cap here; a "
        f"default of detect_cycles=True would silently change EVERY seed's "
        f"termination (PROTOCOL §9)")

    # The observable default lives in TWO places — the Python wrapper (above)
    # AND the native pyo3 signature. Guard the native one directly, reached by
    # calling `_inner.tick` with a single positional arg. (Found the hard way:
    # a first gate flipped only the pyo3 default and stayed GREEN, because the
    # wrapper passes the flag explicitly and shadows it — §12.3.)
    w2, us2, _ = _sheet(4)
    w2.step(ignite_k=1)
    apps_native = int(w2.s._inner.tick(CAP))   # native default, no flag
    assert apps_native >= CAP, (
        f"the NATIVE tick default terminated in {apps_native} applications — "
        f"the pyo3 signature default flipped to true")


@pytest.mark.parametrize("c", [4, 8])
def test_a_true_fixed_point_is_byte_identical_with_detection_on(c):
    """The §9 property, and the reason the blast radius is not 'every seed'.

    A run that ends on NO-PROGRESS is a TRUE fixed point (period 1). The
    `!any_progress` exit fires BEFORE any fingerprint is compared, so such a run
    returns by the committed path untouched. Only a run that BURNS THE CAP can
    end anywhere new — and those are already returning an arbitrary phase of an
    orbit. This test pins that: on the steps that already terminate, ON and OFF
    agree exactly, including the application COUNT."""
    off, _ = _run(c, False)
    on, _ = _run(c, True)
    for a_off, a_on in zip(off, on):
        if a_off < CAP:
            assert a_off == a_on, (
                f"a step that already reached a true fixed point returned a "
                f"DIFFERENT application count under detection ({a_off} vs "
                f"{a_on}) — detection is not supposed to be reachable there")


# --- the mechanism, and its positive control ---------------------------------

@pytest.mark.parametrize("c", [4, 8])
def test_the_dither_terminates_under_detection(c):
    """The headline. The committed loop burns the 200000 cap on a sheet settled
    to 1e-16; detection ends it in single-digit applications."""
    off, _ = _run(c, False)
    on, _ = _run(c, True)
    assert max(off) >= CAP, (
        "the fixture no longer dithers — this test's premise is gone and the "
        "result below would be vacuous (PROTOCOL §1 clause 5)")
    assert max(on) < 1_000, f"detection failed to terminate the dither: {on}"


@pytest.mark.parametrize("c", [4, 8])
def test_detection_returns_THE_SAME_SHEET_not_an_approximation(c):
    """**The correctness claim, and it is exact.** Terminating at the first
    repeated state returns the SAME answer the cap does — not one within a
    tolerance of it. Measured bit-identical (`max|off-on| == 0.0` EXACTLY) at
    both connectivities. This is what distinguishes cycle detection from a
    tolerance predicate: a tolerance ACCEPTS a nearby state, detection proves
    there IS no other state to reach."""
    _, act_off = _run(c, False)
    _, act_on = _run(c, True)
    assert np.array_equal(act_off, act_on), (
        f"cycle detection changed the answer: "
        f"max|d| = {np.max(np.abs(act_off - act_on)):.3e}")


def test_the_detector_BITES_only_on_a_real_cycle():
    """§12.3 / §1 clause 4 pointed at the guard: a gate you have only seen pass
    is not a gate you have tested. A detector that fired unconditionally would
    pass every test above while being WRONG — it would truncate live dynamics.

    So: a loop with somewhere left to go must NOT be cut short. Detection ON
    must reach the SAME fixed point as OFF on a run that genuinely progresses,
    which is exactly the c=8 steps that terminate at apps=0 vs the c=4 steps
    that burn the cap — the detector must discriminate between them."""
    off4, _ = _run(4, False)
    on4, _ = _run(4, True)
    off8, _ = _run(8, False)
    on8, _ = _run(8, True)
    burned = [a for a in off4 if a >= CAP]
    settled = [a for a in off8 if a == 0]
    assert burned, "no cap-burning step — the detector has nothing to bite on"
    assert settled, "no already-settled step — cannot show the detector abstains"
    # It bites on the dither...
    assert max(on4) < 1_000
    # ...and abstains where the committed loop already terminated.
    for a_off, a_on in zip(off8, on8):
        if a_off == 0:
            assert a_on == 0, "the detector fired on a run that had already stopped"


def test_the_degree_based_epsilon_is_refuted_by_the_dither_data():
    """PROTOCOL §13, and the trap this rung was warned about by name.

    The plausible derivation — "round-off of a sum over `d` terms is ~`d`*ULP,
    and the graph supplies the degree" — predicts the c=8 dither >= the c=4
    dither. **The measurements kill it**: MORE degree gave LESS dither. Pinned
    here so nobody re-derives it. Recomputed live (§12.3), never a frozen
    digest."""
    from scripts.settle8_terminate import ulp_check
    amps = {}
    for c in (4, 8):
        u = ulp_check(c, find_capped=True)
        assert u is not None, f"c={c}: no cap-burning step to measure"
        amp = max(max(r[2], r[3]) for r in u["rows"])
        amps[c] = amp / u["ulp"]
    assert amps[4] > amps[8], (
        f"the degree-based epsilon's premise is that dither grows with degree; "
        f"measured c=4 -> {amps[4]:.1f} ULP, c=8 -> {amps[8]:.1f} ULP")
    # Both are dithers of a settled sheet, not dynamics.
    assert amps[4] <= 8 and amps[8] <= 8


def test_rho_ceiling_is_not_fixed_by_this():
    """SCOPE (§8) — state what is NOT shown, as a gate rather than a sentence.

    `rho(M) -> 1` as the sheet grows. A GCAL-scale sheet settles arbitrarily
    slowly REGARDLESS of termination semantics; cycle detection ends the dither,
    it does not make the sheet settle faster. If this ever fails, the ceiling
    moved and the claim above must be rewritten — it must not be discovered by a
    reader assuming the ceiling went away."""
    from scripts.settle8_spectrum import spectrum
    rhos = {n: spectrum(n, 8)["rho_M"] for n in (3, 6)}
    assert rhos[6] > rhos[3], "the rho growth trend inverted — re-derive the ceiling"
    assert rhos[6] > 0.8, (
        f"rho at n_side=6 is {rhos[6]:.4f}; the ceiling claim (0.45 -> 0.87 over "
        f"n_side 3->6) is what licenses 'a GCAL-scale sheet settles arbitrarily "
        f"slowly regardless of termination semantics'")
