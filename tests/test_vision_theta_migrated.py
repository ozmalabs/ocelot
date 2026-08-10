"""RUNG 8B — THETA IS NOT GCAL's THETA.

The gate for `seeds/vision_theta.json`. Pre-registered in
`VISION_RUNG8B_PREREG.md` BEFORE any run.

What these tests pin, in order of how much they would cost if they broke:

  1. **§9 — the seed is INERT by DEFAULT**, byte-identically. `theta_mode=0.0`
     ⇒ loading it changes NOTHING, so every result committed before rung 8B
     reproduces exactly. This is checked by running theta's trajectory WITH and
     WITHOUT the seed and comparing exactly, not by trusting the default.
  2. **The rules FIRE** in GCAL mode. *A rule that quietly does not fire* is this
     arc's recurring failure (`vf_temporal_diff never fired`), and §12's newest
     rule — an absence off a soft accessor is evidence of a LOOKUP, not of
     ABSENCE — applies to instruments, not just arms. So the reader is
     positive-controlled: it is shown to SEE a change it is known to have.
  3. **THE SETPOINT IS ACHIEVED** — `rbar -> mu`. This is the mechanism's
     defining property and the thing rung 6's rule structurally cannot do: a
     follower has no setpoint to reach.
  4. **The freeze is REAL** — weights do not move during adaptation
     (`max|dw| = 0`), and theta does not move during the probe (`dtheta = 0`).
     `oja=0 IS NOT A FREEZE` cost rung 5 three instrument bugs; this rung
     re-measures rather than trusts.
  5. **The two theta rules can NEVER both fire.**
  6. **The FIDELITY claim itself** is pinned as a source audit — because it is
     the whole hypothesis, and if someone "fixes" rung 6's rule to track `rate`
     the claim silently becomes vacuous.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

from domains.complex_cells import present
from domains.onoff_world import set_params
from scripts.rung8_lib import develop_retina, freeze_all
from scripts.rung8b_lib import (
    GCAL_BETA, GCAL_LAMBDA, GCAL_MU, build8b, grating_ensemble, rbar_of,
    set_theta_params, theta_of, weights_of,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "vision_theta.json")


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
#  1. PROTOCOL §9 — INERT BY DEFAULT, byte-identically
# --------------------------------------------------------------------------- #
def test_seed_ships_off_by_default():
    """`theta_mode=0` and `theta_adapt=0` in the manifest. PROTOCOL §9."""
    attrs = _seed()["nodes"][0]["attrs"]
    assert attrs["theta_mode"] == 0.0
    assert attrs["theta_adapt"] == 0.0


def test_gcal_constants_are_the_PUBLISHED_ones():
    """GCAL Eqs 7-8 (Stevens et al. 2013), LITERAL and UNMODIFIED. Moving these
    after seeing a score is the parameter search PREREG §4 forbids — so they are
    pinned HERE, where a change is loud."""
    attrs = _seed()["nodes"][0]["attrs"]
    assert attrs["theta_mu"] == 0.024 == GCAL_MU
    assert attrs["theta_beta"] == 0.991 == GCAL_BETA
    assert attrs["theta_lambda"] == 0.01 == GCAL_LAMBDA


@pytest.mark.slow
def test_loading_the_seed_at_default_changes_NOTHING_byte_identically():
    """The §9 claim, MEASURED rather than asserted: theta's whole trajectory is
    byte-identical with and without `vision_theta` loaded, so every result
    committed before rung 8B reproduces exactly."""
    def trace(theta_seed):
        if theta_seed:
            w, us, _a, _b = build8b(seed=0, n_units=4, channels="lateral",
                                    theta_mode=0.0)
        else:
            from scripts.rung8_lib import build as rung8_build
            w, us, _a, _b = rung8_build(seed=0, n_units=4, channels="lateral")
        develop_retina(w, 200)
        set_params(w, oo_eta=0.0, frozen=0.0)
        for i in range(60):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
        return theta_of(w)

    with_seed, without = trace(True), trace(False)
    assert np.array_equal(with_seed, without), (
        f"vision_theta is NOT inert at its default: {with_seed} != {without}")


# --------------------------------------------------------------------------- #
#  2 + 3. THE RULES FIRE, AND THE SETPOINT IS ACHIEVED
# --------------------------------------------------------------------------- #
def _adapt(w, us, *, ideal, steps=4000):
    from scripts.rung8_lib import ideal_split_gabor
    develop_retina(w, 1000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    th0 = theta_of(w)
    freeze_all(w)
    set_theta_params(w, theta_adapt=1.0)
    rng = np.random.default_rng(7)
    for _ in range(steps):
        present(w, grating_ensemble(w, rng))
    return th0, theta_of(w), rbar_of(w)


@pytest.mark.slow
def test_gcal_rules_fire_and_a_LOW_DRIVE_cell_reaches_the_setpoint():
    """THE MECHANISM'S DEFINING PROPERTY, on the cell where it WORKS: theta
    integrates until the cell's mean OUTPUT equals mu. A follower (rung 6's
    rule) has no setpoint to reach at all.

    This is also the instrument's positive control (§12): the reader is shown to
    SEE a change it is known to have, so a later null cannot be a dead reader.
    """
    w, us, _a, _b = build8b(seed=0, n_units=4, channels="lateral",
                            theta_mode=1.0)
    assert np.allclose(rbar_of(w), GCAL_MU), "GCAL Eq 7's init rbar(0)=mu"
    th0, th1, rb1 = _adapt(w, us, ideal=True)
    assert np.abs(th1 - th0).max() > 1e-6, "th_adapt_gcal NEVER FIRED"
    assert np.abs(rb1 - GCAL_MU).max() < 0.02, (
        f"the setpoint was NOT reached on a low-drive cell: {rb1} vs {GCAL_MU}")


@pytest.mark.slow
def test_a_HIGH_DRIVE_cell_WINDS_UP_AND_DIES_the_rungs_actual_finding():
    """**THE NEGATIVE, PINNED** — and this test's own history is the point: it
    was first written to assert that the setpoint is ALWAYS reached, and it
    FAILED (rbar 1.3e-14, not 0.024). The assertion was the agent's wrong
    prediction; the measurement was the finding.

    GCAL Eq 8 is ASYMMETRIC in unnormalised response units:

        UP-drive   = lambda * rbar   -- rbar is UNBOUNDED here (it reaches ~20)
        DOWN-drive = lambda * mu     = 0.00024/step, CONSTANT and TINY

    An untouched-init cell's drive is ~10x an ideal Gabor's (unstructured w0=1
    weights SUM; a zero-mean Gabor CANCELS). So theta winds up past the whole
    distribution, the cell goes SILENT, rbar collapses to ~0 -- NOT to mu -- and
    theta could only recover at 0.00024/step (~25k steps).

    GCAL cannot hit this: L1 weights (sum w = 1) and inputs in [0,1] put eta in
    [0,1], so rbar - mu <= 0.976 and the two drives are COMPARABLE.

    **An absolute setpoint cannot transfer into unnormalised response units:
    GCAL's A requires GCAL's GC.** If GC ever lands, THIS test should flip --
    and that flip is exactly the evidence GC would need to earn.
    """
    w, us, _a, _b = build8b(seed=0, n_units=4, channels="lateral",
                            theta_mode=1.0)
    th0, th1, rb1 = _adapt(w, us, ideal=False)
    assert np.abs(th1 - th0).max() > 1e-6, "th_adapt_gcal NEVER FIRED"
    assert float(np.abs(rb1).max()) < 1e-3, (
        "the high-drive cell no longer collapses to silence — the windup this "
        "rung measured has changed; re-read VISION_RUNG8B_PREREG.md §D")
    assert float(th1.min()) > 10.0, (
        f"theta no longer winds up on a high-drive cell: {th1}")


# --------------------------------------------------------------------------- #
#  4. THE FREEZE IS REAL, IN BOTH DIRECTIONS
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_adaptation_moves_theta_but_NOT_the_weights():
    """ADAPTATION IS NOT TRAINING, and the distinction is load-bearing: it is
    licensed ONLY because theta sits OUTSIDE the learning rule (GCAL's
    placement, which rung 6 chose and this rung keeps), so it cannot flip dw's
    sign. If weights moved here, the probe would be training what it measures —
    rung 5's freeze bug, and the whole protocol would be void."""
    w, us, _a, _b = build8b(seed=0, n_units=4, channels="lateral",
                            theta_mode=1.0)
    develop_retina(w, 1000)
    wt0, th0 = weights_of(w, us), theta_of(w)
    freeze_all(w)
    set_theta_params(w, theta_adapt=1.0)
    rng = np.random.default_rng(7)
    for _ in range(400):
        present(w, grating_ensemble(w, rng))
    assert float(np.abs(weights_of(w, us) - wt0).max()) == 0.0, (
        "WEIGHTS MOVED during theta adaptation — the probe is training what it "
        "measures (rung 5's `oja=0 IS NOT A FREEZE`, recurring)")
    assert np.abs(theta_of(w) - th0).max() > 1e-6, "theta did not adapt"


@pytest.mark.slow
def test_theta_is_PINNED_during_the_probe():
    """Rung 6's discipline, kept: *a probe must never let theta chase the
    probe*. Adapt -> FREEZE -> measure."""
    w, us, _a, _b = build8b(seed=0, n_units=4, channels="lateral",
                            theta_mode=1.0)
    develop_retina(w, 500)
    freeze_all(w)
    set_theta_params(w, theta_adapt=0.0)   # PINNED
    th0 = theta_of(w)
    rng = np.random.default_rng(11)
    for _ in range(300):
        present(w, grating_ensemble(w, rng))
    assert float(np.abs(theta_of(w) - th0).max()) == 0.0, (
        "theta MOVED while pinned — the probe is chasing theta")


# --------------------------------------------------------------------------- #
#  5. THE TWO THETA RULES CAN NEVER BOTH FIRE
# --------------------------------------------------------------------------- #
def test_the_two_theta_rules_are_mutually_exclusive():
    """`vision_onoff` is NOT edited (PROTOCOL §11.4; rung 8's *compose, don't
    modify*). The GCAL arm instead sets rung 6's OWN `homeo=0`, which pins its
    EMA rule — its documented meaning. `build8b` does this, so the exclusion is
    structural rather than a convention someone must remember."""
    w, _us, _a, _b = build8b(seed=0, n_units=2, channels="lateral",
                             theta_mode=1.0)
    oo = w.s.node(w.s.nodes("OnOffParams")[0])["attrs"]
    tp = w.s.node(w.s.nodes("ThetaParams")[0])["attrs"]
    assert oo["homeo"] == 0.0, "rung 6's EMA theta is NOT pinned in the GCAL arm"
    assert tp["theta_mode"] == 1.0

    w0, _us0, _a0, _b0 = build8b(seed=0, n_units=2, channels="lateral",
                                 theta_mode=0.0)
    oo0 = w0.s.node(w0.s.nodes("OnOffParams")[0])["attrs"]
    assert oo0["homeo"] == 1.0, "the default arm must leave rung 6 untouched"


def test_vision_onoff_and_vision_lateral_are_NOT_edited():
    """PROTOCOL §11.4 — do not edit another rung's seed. Rung 8's precedent:
    compose, don't modify. If this breaks, rung 6's and rung 7's committed
    results are no longer attributable to their own seeds.

    §12.3 (2026-07-17) — THIS GATE WAS MIS-SCOPED AND IT ROTTED THE SAME DAY.
    It asserted the BYTES never change against a hardcoded sha, which is a
    proxy for what it actually claims: that rung 6/7 stay ATTRIBUTABLE. The
    two-eyes rung then made a provably semantics-preserving change (`Pick` ->
    `PickUnique`, 25 sites, and NOTHING else -- verified by diffing the Term
    types) and this gate fired on it. `PickUnique` IS `Pick` for 0 or 1
    candidates and panics on >1, so every committed result is untouched: the
    rung re-verified §9 byte-identity two ways (bench 165/10 identical; the
    wave floats identical to the last digit).

    So the gate now checks its INTENT rather than its proxy: any edit to these
    seeds is still a failure EXCEPT the one mechanical rebind that is provably
    a no-op. Add nothing else to this allowlist without the same standard of
    proof -- a semantics-preserving argument AND a byte-identity re-run.
    """
    import subprocess
    d = subprocess.run(
        ["git", "diff", "-U0", "0580479857", "--",
         "seeds/vision_onoff.json", "seeds/vision_lateral.json"],
        cwd=ROOT, capture_output=True, text=True).stdout
    changed = [l for l in d.splitlines()
               if l[:1] in "+-" and l[:2] not in ("++", "--")]
    # The ONLY admissible change: the Pick -> PickUnique rebind (a no-op at
    # <=1 candidate). Anything else -- any other Term, attr, or rule -- fails.
    offenders = [l for l in changed
                 if not (('"Pick"' in l and l.startswith("-"))
                         or ('"PickUnique"' in l and l.startswith("+")))]
    assert not offenders, (
        "another rung's seed was edited beyond the admissible "
        f"Pick->PickUnique rebind:\n" + "\n".join(offenders[:10]))


# --------------------------------------------------------------------------- #
#  6. THE FIDELITY CLAIM — pinned as a source audit
# --------------------------------------------------------------------------- #
def test_rung6_theta_tracks_the_INPUT_and_GCAL_theta_tracks_the_OUTPUT():
    """THE ENTIRE HYPOTHESIS, pinned where a change is loud.

    Rung 6's `oo_sunit_adapt_theta` reads `act` — the PRE-threshold drive — so
    it is a low-pass FOLLOWER with no setpoint, scale-LOCKED to the ensemble it
    last saw. GCAL's Eq 7 reads the cell's OUTPUT (`rate`) and Eq 8 integrates
    the error against a SETPOINT `mu`.

    If someone later "fixes" rung 6's rule to read `rate`, this rung's premise
    silently evaporates — so the difference is asserted, not remembered.
    """
    with open(os.path.join(ROOT, "seeds", "vision_onoff.json")) as fh:
        onoff = json.load(fh)
    r6 = next(r for r in onoff["rules"] if r["name"] == "oo_sunit_adapt_theta")
    body = json.dumps(r6["effects"])
    assert '"key": "act"' in body, (
        "rung 6's theta no longer tracks `act` — rung 8B's premise has changed")
    assert '"key": "rate"' not in body, "rung 6's theta now tracks the OUTPUT?"

    th = _seed()
    track = next(r for r in th["rules"] if r["name"] == "th_track_rbar")
    adapt = next(r for r in th["rules"] if r["name"] == "th_adapt_gcal")
    assert '"key": "rate"' in json.dumps(track["effects"]), (
        "GCAL Eq 7 must track the cell's OUTPUT")
    assert '"key": "theta_mu"' in json.dumps(adapt["effects"]), (
        "GCAL Eq 8 must integrate the error against the SETPOINT mu")


def test_a_SILENT_cell_scores_a_PERFECT_floor_the_defect_that_faked_the_gate():
    """PROTOCOL §1.1, pinned as a TEST rather than remembered — the way the
    soft-accessor lesson was pinned after it cost a day.

    `complex_cells.osi()` ends `(a-b)/(a+b) if (a+b) > 1e-9 else 0.0`. So a cell
    that NEVER FIRES scores **0.0000 — a flawless floor** — and is
    indistinguishable from one that fires everywhere equally.

    THIS IS NOT HYPOTHETICAL: it is exactly how rung 8B's GCAL-theta arm passed
    all four of its pre-registered criteria (ideal 1.0000, floor 0.0000,
    separation 1.0000 on BOTH pathways) while its floor arm fired at **0 of 12**
    orientations. The "separation" was measuring FIRES vs DOES-NOT-FIRE.

    If someone makes `osi()` raise or return NaN on a silent cell, this test
    should be UPDATED, not deleted — the point is that the value 0.0 carries two
    incompatible meanings.
    """
    from domains.complex_cells import osi

    silent = np.zeros(12)
    flat = np.full(12, 0.7)
    selective = np.array([1.0] + [0.0] * 11)

    assert osi(silent) == 0.0, "a silent cell no longer returns 0.0"
    assert osi(flat) == 0.0, "an unselective-but-ALIVE cell also returns 0.0"
    # THE DEFECT, stated as an equality: the two are indistinguishable.
    assert osi(silent) == osi(flat), (
        "PROTOCOL §1.1's premise has changed — silence and unselectivity are no "
        "longer confused, and the fourth clause may be revisited")
    assert osi(selective) == 1.0
    # ...and this is why an arm must be shown ALIVE before its floor is read.
    assert (silent > 1e-9).sum() == 0
    assert (flat > 1e-9).sum() == 12


def test_this_rung_adds_NO_rust():
    """PREREG §7. Both rules are Plus/Times/Minus/Attr/Lit — the Terms rung 6's
    own rules already use. Expressibility is never a reason to reject a
    mechanism, but nor is it a reason to add a Term that is not needed.

    §12.3 (2026-07-17) — MIS-SCOPED, ROTTED THE SAME DAY, NOW PINNED TO ITS
    DIFF. This asserted the live tree has no Rust change since a hardcoded
    sha — but the claim it makes is about RUNG 8B's OWN COMMITS, not about
    every rung that ever follows. The two-eyes rung then added `PickUnique`
    (a legitimate Rust Term, gated and §9-verified) and this fired on it,
    which is a false accusation: rung 8B still added no Rust.

    A PROVENANCE CLAIM MUST BE PINNED TO THE DIFF IT DESCRIBES, NEVER TO A
    MUTABLE TREE — otherwise it does not test the claim, it tests whether
    anyone else has done any work since. Scoped to rung 8B's own range.
    """
    import subprocess
    # Rung 8B's own commits: its prereg (9ca3845985) through its result
    # (a5ab9b859c). THAT is the range its no-Rust claim is about.
    out = subprocess.run(
        ["git", "diff", "--name-only", "9ca3845985^", "a5ab9b859c", "--",
         "runners/dsl/src", "runners/dsl/Cargo.toml"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    assert out == "", f"rung 8B was not supposed to touch Rust: {out}"
