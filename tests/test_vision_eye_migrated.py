"""THE EYE'S CALIBRATION FRONT END — the gates.

VISION_PROTOCOL.md §1 requires the MEASURE to be gated before the agent, so the
instruments (`diffusion_exponent`, `anisotropy`, the invariance statistic) are
tested here against a floor and an ideal exemplar alongside the mechanisms.

§9 requires defaults to preserve committed results: `eye=0` must fire NOTHING.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.eye_world import (EyeWorld, set_params, freeze, walk,  # noqa: E402
                               diffusion_exponent, anisotropy,
                               direction_hist, msd)

H = W = 8


def build(*, seed=0, gaze_l=21, **kw):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = EyeWorld(s, h=H, w=W, gaze_l=gaze_l, seed=seed)
    set_params(w, eye=1.0, **kw)
    return w


def scene(seed=99):
    rng = np.random.default_rng(seed)
    return (rng.random((H, W)) + 0.1).astype(np.float64)


# ===================================================================== §9
def test_default_off_fires_nothing():
    """PROTOCOL §9: every mechanism ships off by default so every committed
    result reproduces exactly. `eye=0` must leave the graph untouched."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    p = s.nodes("EyeParams")[0]
    assert float(s.node(p)["attrs"]["eye"]) == 0.0, "the master switch must default OFF"

    w = EyeWorld(s, h=H, w=W, gaze_l=11, seed=0)
    before_pos = w.gaze_pos()
    sc = scene()
    for _ in range(50):
        w.step(frame=sc)
    # Not one rule may have fired: no drive, no response, no reference, no drift.
    assert np.max(np.abs(w.drives())) == 0.0
    assert np.max(np.abs(w.responses())) == 0.0
    assert np.max(np.abs(w.thetas())) == 0.0
    assert w.gaze_pos() == before_pos, "the SAW must not walk with eye=0"


def test_defaults_are_byte_identical_to_no_seed():
    """The stronger form: booting WITH this seed at its defaults must leave the
    other vision seeds' graph state bit-identical to not loading it at all."""
    def waves_state(with_eye):
        s, ag = boot_core()
        seeds = ["vision_waves"] + (["vision_eye"] if with_eye else [])
        load_seeds_into(s, ag, seeds)
        from domains.wave_world import WaveWorld
        wp = s.nodes("WaveParams")[0]
        s.set_attr(wp, "propagate", 1.0)
        ww = WaveWorld(s, h=8, w=8, seed=3)
        for i in range(40):
            ww.step(ignite_k=1 if i % 5 == 0 else 0)
        return ww.frame()

    a = waves_state(False)
    b = waves_state(True)
    assert float(np.max(np.abs(a - b))) == 0.0, "defaults-off must be byte-identical"


def test_freeze_is_a_real_freeze():
    """Rung 5 lost three hand-set poolings to a fake freeze (`oja=0` still ran
    the rule and moved weights by 47.9 per probe). `frozen=1` must gate every
    learning AND adaptation rule — adaptation IS plasticity."""
    w = build(logr=1.0, saw=0.0, eye_open=1.0)
    sc = scene()
    for _ in range(200):
        w.step(frame=sc)
    us = w.add_units(2, rf=5, seed=0)
    for _ in range(50):
        w.step(frame=sc)

    freeze(w)
    th0 = w.thetas().copy()
    w0 = [w.weights(u).copy() for u in us]
    for _ in range(100):
        w.step(frame=sc)
    dth = float(np.max(np.abs(w.thetas() - th0)))
    dw = max(float(np.max(np.abs(w.weights(u) - a))) for u, a in zip(us, w0))
    assert dth == 0.0, f"frozen theta moved by {dth:.3e} — adaptation is plasticity"
    assert dw == 0.0, f"frozen weights moved by {dw:.3e}"


# ============================================== §1: gate the MEASURE first
def test_drift_measure_scores_brownian_motion_at_one():
    """CALIBRATION — the IDEAL EXEMPLAR for `diffusion_exponent`. An ordinary
    random walk is Brownian by construction: MSD ~ lag^1. If the instrument
    cannot read alpha=1 off a walk that IS alpha=1, no alpha it reports means
    anything."""
    rng = np.random.default_rng(7)
    steps = rng.choice([(0, 1), (0, -1), (1, 0), (-1, 0),
                        (1, 1), (1, -1), (-1, 1), (-1, -1)], size=20_000)
    traj = np.cumsum(steps, axis=0)
    a = diffusion_exponent(traj, 1, 50)
    assert abs(a - 1.0) < 0.10, f"Brownian walk must read alpha~1, got {a:.3f}"


def test_drift_measure_scores_ballistic_motion_at_two():
    """CALIBRATION — the other end of the instrument. Straight-line motion is
    perfectly persistent: MSD ~ lag^2."""
    traj = np.stack([np.arange(2000), np.arange(2000)], axis=1)
    a = diffusion_exponent(traj, 1, 50)
    assert abs(a - 2.0) < 0.05, f"ballistic motion must read alpha~2, got {a:.3f}"


def test_anisotropy_measure_floor_and_ideal():
    """CALIBRATION for the cardinal-axis instrument: it must score ~0 on an
    isotropic walk (the floor) and ~1 on a walk pinned to one direction (the
    ideal artifact it exists to catch)."""
    rng = np.random.default_rng(11)
    iso = np.cumsum(rng.choice([(0, 1), (0, -1), (1, 0), (-1, 0),
                                (1, 1), (1, -1), (-1, 1), (-1, -1)],
                               size=20_000), axis=0)
    assert anisotropy(iso) < 0.10, "an isotropic walk must score near 0"

    pinned = np.stack([np.arange(500), np.zeros(500, int)], axis=1)
    assert anisotropy(pinned) > 0.9, "a one-direction walk must score near 1"


# ============================================== the SAW's own behaviour
def test_saw_walks_and_avoids_its_own_trail():
    """The mechanism, minimally: the walk must MOVE, and it must not sit still
    or rattle between two cells. Self-avoidance means it covers ground."""
    w = build(saw=1.0, gaze_l=51)
    t = walk(w, 400)
    assert len(set(t)) > 100, f"the SAW barely explored: {len(set(t))} cells in 400 steps"


def test_saw_is_not_cardinal_axis_artifacted():
    """VISION_PRIOR_ART.md §3.2's explicit caution: the deterministic
    4-connected argmin only steps N/S/E/W — "a subtle way of telling the agent
    the answer". The stochastic variant on the 8-neighbourhood must be
    ISOTROPIC. This is the gate on that caution."""
    w = build(saw=1.0, gaze_l=51)
    t = walk(w, 1500)
    a = anisotropy(t)
    assert a < 0.25, f"step directions are anisotropic ({a:.3f}) — cardinal artifact"


def test_saw_reproduces_engberts_published_signature():
    """THE HEADLINE for the drift: Engbert 2011's signature is PERSISTENT at
    short lags (alpha 1.32, superdiffusive — self-avoidance) and ANTIPERSISTENT
    at long lags (alpha 0.71, subdiffusive — the quadratic potential pulling
    back). The two must straddle alpha=1, which is the memoryless Brownian null
    that `gaze_walk` produces across epochs."""
    w = build(saw=1.0, gaze_l=51)
    t = walk(w, 2000)
    a_s = diffusion_exponent(t, 1, 10)
    a_l = diffusion_exponent(t, 10, 50)
    assert a_s > 1.0, f"short lags must be PERSISTENT (alpha>1), got {a_s:.3f}"
    assert a_l < 1.0, f"long lags must be ANTIPERSISTENT (alpha<1), got {a_l:.3f}"
    assert a_s > a_l, "the crossover must run persistent -> antipersistent"


def test_the_potential_is_what_makes_the_antipersistence():
    """The mechanism claim, tested by ABLATION AS DATA (PROTOCOL §0): §3.2 says
    "self-avoidance makes the persistence; the potential makes the
    antipersistence". Remove the potential (saw_lam=0) and the long-lag
    antipersistence must go with it, while the walk still moves."""
    w = build(saw=1.0, saw_lam=0.0, gaze_l=51)
    t = walk(w, 2000)
    a_l = diffusion_exponent(t, 10, 50)
    assert a_l > 1.0, (
        f"with NO potential the walk must NOT be antipersistent, got {a_l:.3f} — "
        "if it is, the antipersistence is not coming from the potential")


# ============================================== the receptor
def test_log_receptor_is_weber_fechner_above_the_dark_light():
    """The receptor's defining property: response proportional to log I, over
    ≥3 orders of magnitude. Read off the DRIVE directly (no reference, no
    rectification) so this tests the receptor and nothing else.

    THE REGIME IS PART OF THE LAW, not an escape from it. The receptor is
    `x = ln(I + i0)`, which is exactly logarithmic only for `I >> i0` and
    LINEAR for `I << i0` — that is what a dark light IS, and it is why Weber's
    law fails at very low luminance in real eyes too. Measured: including k=1
    (i.e. I == i0, squarely in the linear regime) drags the fitted slope to
    0.9357. That is the law being read outside its domain, so the domain is
    stated — and the crossover is gated below rather than waved away.
    """
    w = build(logr=1.0, saw=0.0, homeo=0.0, eye_open=1.0)
    sc = np.full((H, W), 1.0)
    ks = [1e2, 1e3, 1e4, 1e5, 1e6]      # four decades, all >> i0 = 1
    xs = []
    for k in ks:
        w.step(frame=sc * k)
        xs.append(float(np.mean(w.drives())))
    slope = float(np.polyfit(np.log(np.array(ks)), np.array(xs), 1)[0])
    assert abs(slope - 1.0) < 0.05, f"log receptor slope vs ln I = {slope:.4f}, want 1"


def test_log_receptor_is_linear_below_the_dark_light():
    """The OTHER half of the same claim, and the reason the test above states a
    regime rather than dodging one: `ln(I + i0) ≈ I/i0` for `I << i0`, so the
    receptor must be LINEAR down there. This is a PREDICTED property of the dark
    light — gating it is what makes the regime restriction honest instead of
    convenient."""
    w = build(logr=1.0, saw=0.0, homeo=0.0, eye_open=1.0)
    sc = np.full((H, W), 1.0)
    ks = [1e-4, 1e-3, 1e-2]             # all << i0 = 1
    xs = []
    for k in ks:
        w.step(frame=sc * k)
        xs.append(float(np.mean(w.drives())))
    # Linear in I: x/I should be ~constant (== 1/i0), NOT ~constant per decade.
    ratios = np.array(xs) / np.array(ks)
    assert np.allclose(ratios, ratios[0], rtol=0.02), (
        f"below the dark light the receptor must be LINEAR, got x/I = {ratios}")


def test_linear_receptor_is_not_weber_fechner():
    """The control arm, and the ablation is DATA (`logr=0`), not a code path."""
    w = build(logr=0.0, saw=0.0, homeo=0.0, eye_open=1.0)
    sc = np.full((H, W), 1.0)
    xs = []
    for k in (1e0, 1e1, 1e2, 1e3):
        w.step(frame=sc * k)
        xs.append(float(np.mean(w.drives())))
    # A linear receptor's drive IS the illumination.
    assert abs(xs[-1] - 1e3) < 1e-6, "the linear arm must pass illumination through"


def test_saturating_transfer_function_bounds_the_response():
    """rmax is REQUIRED by mu, not chosen: mu=0.024 is GCAL's target average
    activity, and a target average only means anything as a fraction of a
    maximum. An unbounded f let one spike ratchet theta far above the drive and
    silenced the unit for ~13,500 steps (measured), which made a dead arm look
    stable. The response must never exceed rmax."""
    w = build(logr=1.0, saw=0.0, homeo=0.0, eye_open=1.0)
    w.step(frame=np.full((H, W), 1e6))
    assert float(np.max(w.responses())) <= 1.0 + 1e-9


def test_the_reference_converges_to_the_target_rate():
    """The homeostat's whole job, and the protocol's CONVERGENT+USEFUL: the
    reference must settle so the population's mean output sits at mu, and the
    drift must go to 0. Measured at k=1, where convergence is fast."""
    w = build(logr=1.0, saw=0.0, eye_open=1.0)
    rng = np.random.default_rng(5)
    for _ in range(6400):
        w.step(frame=(rng.random((H, W)) + 0.1))
    th0 = w.thetas().copy()
    # The input is a fresh scene every step, so the INSTANTANEOUS mean response
    # fluctuates (measured: 0.017-0.031 around mu) even at a perfect fixed
    # point. The homeostat's target is the mean OVER THE ENSEMBLE, so that is
    # what gets asserted — asserting on one frame would be reading noise.
    resp = []
    for _ in range(2000):
        w.step(frame=(rng.random((H, W)) + 0.1))
        resp.append(float(np.mean(w.responses())))
    # WHICH DRIFT STATISTIC IS THE RIGHT ONE, and it depends on the input. On a
    # STATIC scene theta reaches drift EXACTLY 0.00000 and holds it from 6.4k to
    # 40k (results/eye_convergence.log). On a STOCHASTIC STREAM it cannot: every
    # step is a different scene, so theta jitters around its fixed point forever
    # (measured 1.25e-2 per 2000 steps). That jitter is INPUT NOISE, not
    # non-convergence, and asserting on it would be measuring the ensemble's
    # variance and calling it instability. What converges on a stream is theta's
    # LEVEL — so that is what is asserted.
    assert abs(float(np.mean(resp)) - 0.024) < 0.005, (
        f"the reference must hold the ENSEMBLE mean at mu, got {np.mean(resp):.5f}")
    lvl0 = float(np.mean(th0))
    lvl1 = float(np.mean(w.thetas()))
    assert abs(lvl1 - lvl0) < 0.01 * abs(lvl0), (
        f"the reference's LEVEL must be settled: {lvl0:.4f} -> {lvl1:.4f}")


# ================================================ PHASE 0 / PHASE 1 separation
def _wave_world(seed=0, propagate=1.0, n_units=4):
    from domains.wave_world import WaveWorld
    from domains.eye_world import PreVisualWorld
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", propagate)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)   # rung 1's legacy Unit rules stay inert
    ww = WaveWorld(s, h=16, w=16, seed=seed)
    pv = PreVisualWorld(ww, n_units=n_units, seed=seed)
    return s, ww, pv


def test_a_closed_eye_still_transduces():
    """THE CREATOR'S CORRECTION, and it retracts a gate this rung shipped: A
    CLOSED EYE'S PHOTOMETRY STILL WORKS. The lid is translucent — photoreceptors
    transduce diffuse light long before eye opening — so "eye opening" does not
    switch phototransduction on, it delivers a PATTERNED IMAGE. An earlier
    version gated every photometric rule on `eye_open`, encoding the false claim
    that a closed eye is blind. THE LID IS OPTICS, NOT A NEURAL SWITCH.
    """
    from domains.eye_world import EyeWorld, lid_diffuse
    w = build(logr=1.0, homeo=1.0, saw=0.0, eye_open=0.0)   # lid CLOSED
    for _ in range(200):
        w.step(frame=lid_diffuse(scene()) * 100.0)
    assert float(np.max(np.abs(w.drives()))) > 0.0, (
        "a closed eye must still transduce — the lid is translucent, not opaque")
    assert float(np.max(np.abs(w.thetas()))) > 0.0, (
        "and its gain must still calibrate: that is what a closed eye is FOR")


def test_a_closed_lid_diffuses_rather_than_blanks_or_uniforms():
    """The second correction: A CLOSED LID DOES NOT GIVE UNIFORM ILLUMINATION,
    IT GIVES DIFFUSED ILLUMINATION. It is a scatterer — a spatial low-pass, like
    frosted glass. Coarse luminance structure survives (you can locate a window
    with your eyes shut); only the fine detail is lost. Modelling it as a
    constant field would be as wrong as modelling it as a blackout."""
    from domains.eye_world import lid_diffuse
    sc = scene()
    d = lid_diffuse(sc)
    assert d.std() > 0.0, "diffused is NOT uniform — coarse structure survives"
    assert d.std() < 0.25 * sc.std(), "diffused must lose the fine detail"
    assert abs(d.mean() - sc.mean()) < 0.05 * sc.mean(), (
        "a scatterer redistributes light; it must not swallow the level")


def test_waves_do_not_drive_the_photometric_path():
    """WHERE THE REAL SEPARATION LIVES. "Waves cannot calibrate photometric
    response" is TRUE, but it is not true because a rule forbids it — it is true
    STRUCTURALLY: the photometric rules read `EyeCell.lum` (light), waves live on
    `RetinaCell.bursting` (endogenous activity), and no edge joins them. So theta
    must evolve IDENTICALLY whether or not waves are running. That is the claim
    the retracted `eye_open` gate was redundantly restating."""
    from domains.wave_world import WaveWorld
    from domains.eye_world import EyeWorld, lid_diffuse

    def theta_after(waves_on):
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
        wp = s.nodes("WaveParams")[0]
        s.set_attr(wp, "propagate", 1.0 if waves_on else 0.0)
        s.set_attr(wp, "oja", 1.0)
        s.set_attr(wp, "oja_eta", 0.0)
        ww = WaveWorld(s, h=H, w=W, seed=3)
        w = EyeWorld(s, h=H, w=W, gaze_l=5, seed=0)
        set_params(w, eye=1.0, eye_open=0.0, logr=1.0, homeo=1.0, saw=0.0)
        f = lid_diffuse(scene()) * 100.0
        # TICK-MATCHED: both arms call ww.step() (which ticks internally), so the
        # arms differ ONLY in `propagate` — i.e. in whether waves exist, not in
        # how many fixpoint passes run. Skipping it in one arm gave that arm a
        # different schedule and the test failed on the harness, not the claim.
        for i in range(300):
            ww.step(ignite_k=1 if i % 5 == 0 else 0)
            w.step(frame=f)
        return w.thetas()

    a, b = theta_after(False), theta_after(True)
    assert float(np.max(np.abs(a - b))) == 0.0, (
        "waves moved theta — the photometric path is contaminated by endogenous "
        "activity, which is exactly the category error")


def test_phase0_retinotopy_positive_control_localises():
    """THE POSITIVE CONTROL, and rung 3's lesson: only its positive control
    revealed that eta was a NULL INSTRUMENT. Given bursts pinned to a fixed 5x5
    patch — the input a working retinotopy rule MUST be able to learn — the
    winning unit's RF must localise onto that patch. If this fails, every
    phase-0 null is uninterpretable rather than informative.

    It is also what caught the clock bug: the rules stamped against the Retina's
    clock, which WaveWorld ticks internally, so the patch never reached the units
    at all (spread 6.54 = untouched diffuse).
    """
    from domains.eye_world import rf_spread, rf_centre
    s, ww, pv = _wave_world(seed=0, propagate=0.0, n_units=4)
    set_params(pv, eye=1.0, phase0=1.0, eye_open=0.0, saw=0.0, ph0_eta=5e-4)
    patch = [rc for rc in ww.cells if 3 <= rc[0] <= 7 and 3 <= rc[1] <= 7]
    for _ in range(4000):
        ww.step(ignite_k=0)
        pv.present_bursts(patch)
        pv._advance()
    spreads = [rf_spread(pv.rf(i)) for i in range(4)]
    best = int(np.argmin(spreads))
    cy, cx = rf_centre(pv.rf(best))
    assert min(spreads) < 3.0, (
        f"the winner must LOCALISE (floor 6.52, ideal ~1.63), got {min(spreads):.2f}")
    assert abs(cy - 5.0) < 1.0 and abs(cx - 5.0) < 1.0, (
        f"the winner's RF must sit ON the patch (5,5), got ({cy:.1f},{cx:.1f})")


def test_phase0_wiring_is_diffuse_not_retinotopic():
    """The line the whole build turns on: retinal adjacency is PHYSICS and rung 1
    may wire it, but RETINOTOPY is KNOWLEDGE and must be earned. The adapter must
    therefore hand over a projection with NO locality — every retinal cell to
    every unit. This gates the thing rung 4 got wrong (it wired the map, then
    measured its own wiring back out: -13.25 of -20.16).
    """
    from domains.eye_world import rf_spread
    s, ww, pv = _wave_world(seed=0, n_units=3)
    for i in range(3):
        rf = pv.rf(i)
        assert float(np.min(rf)) > 0.0, (
            "every cell must connect to every unit — a zero would be a "
            "spatial prior the adapter smuggled in")
        assert rf_spread(rf) > 6.0, (
            f"the initial projection must be DIFFUSE (floor 6.52), got "
            f"{rf_spread(rf):.2f} — anything localised is handed-over retinotopy")
