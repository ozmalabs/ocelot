"""Gates for JOB 1 (the drift moves the image) and JOB 2 (the setpoint falls out).

PROTOCOL §12: this file is named explicitly in `scripts/rung7_vision_bench.sh`.
Never selected by `-k vision` (which substring-matches "pro-VISION-al").
"""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.seed_registry  # noqa: F401,E402
from domains import eye_world  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "seeds", "vision_eye.json")


def _seed_json():
    with open(SEED_PATH) as f:
        return json.load(f)


def _build(saw=1.0, **params):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = eye_world.EyeWorld(s, h=8, w=8, gaze_l=11, seed=0)
    eye_world.set_params(w, eye=1.0, saw=saw, **params)
    return w


def _scene(wh, ww):
    yy, xx = np.mgrid[0:wh, 0:ww]
    return np.clip(0.5 + 0.35 * np.sin(2 * np.pi * (xx + yy) / 8.0), 0.0, 1.0)


# --------------------------------------------------------------- §9 defaults
def test_defaults_are_off_so_committed_results_reproduce():
    """PROTOCOL §9. Every new arm ships off."""
    p = _seed_json()["nodes"][0]["attrs"]
    assert p["world_sample"] == 0.0
    assert p["calib"] == 0.0
    assert p["mu_mode"] == 0.0
    assert p["mu"] == 0.024      # the imported constant is still the DEFAULT


def test_drift_is_still_vacuous_at_the_defaults():
    """FM-0's finding must REPRODUCE with the mechanism off: D == 0.0 exactly.

    This is the §9 gate in its sharpest form -- the wiring is present in the seed
    and changes NOTHING until the agent's own configuration turns it on.

    THE WORLD SHEET IS LAID OUT ON PURPOSE, and that is what makes this a gate
    (§12.3: positive-control it, don't just watch it pass). The first cut used
    FM-0's own configuration, which lays out NO world -- so the Filter matched
    nothing, `PickUnique` returned None, and `lum` never moved REGARDLESS of
    `world_sample`. Flipping the default 0->1 left it GREEN: it was gating "is
    there a world?", not "is the mechanism off?". Found by injecting exactly that
    violation. With a world present, flipping the default now turns it RED.
    """
    out = {}
    scene = _scene(11 + 8 - 1, 11 + 8 - 1)
    for saw in (1.0, 0.0):
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_eye"])
        w = eye_world.EyeWorld(s, h=8, w=8, gaze_l=11, seed=0)
        w.add_world(scene)                       # a world EXISTS to be sampled
        eye_world.set_params(w, eye=1.0, saw=saw)   # world_sample left at DEFAULT
        hist = []
        for _ in range(40):
            w.step(frame=None)
            hist.append(w.responses().copy())
        out[saw] = hist
    d = max(float(np.max(np.abs(out[1.0][t] - out[0.0][t]))) for t in range(40))
    assert d == 0.0, f"expected FM-0's exact vacuity at the defaults, got D={d}"


# --------------------------------------------------------------- JOB 1
def test_gamma_admits_the_gaze_eye_coupling():
    """FM-0: 'NO production admits a Gaze<->Eye edge -- Γ would reject it.'

    Verified before the fix: `Γ rejects: type 'has_gaze' not in vocabulary`.
    The production is the fix, and it is graph data.
    """
    prods = {(p["src"]["type"], p["edge_type"], p["tgt"]["type"])
             for p in _seed_json()["productions"]}
    assert ("Eye", "has_gaze", "Gaze") in prods
    assert ("World", "has_worldcell", "WorldCell") in prods


def test_the_drift_moves_the_image_when_the_agent_turns_it_on():
    """JOB 1, and it is FM-0's own gate inverted: D must become > 0.

    NOT a scientific finding -- D > 0 is guaranteed once sampling reads the gaze.
    This gate exists so the wiring cannot silently rot back to decorative.
    """
    wh = ww_ = 11 + 8 - 1
    scene = _scene(wh, ww_)
    out, trajs = {}, {}
    for saw in (1.0, 0.0):
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_eye"])
        w = eye_world.EyeWorld(s, h=8, w=8, gaze_l=11, seed=0)
        w.add_world(scene)
        eye_world.set_params(w, eye=1.0, saw=saw, world_sample=1.0)
        hist, tr = [], [w.gaze_pos()]
        for _ in range(60):
            w.step(frame=None)
            hist.append({"lum": np.array(
                [[float(w.s.node(w.cells[(r, c)])["attrs"]["lum"])
                  for c in range(8)] for r in range(8)]),
                "resp": w.responses().copy()})
            tr.append(w.gaze_pos())
        out[saw] = hist
        trajs[saw] = tr

    # POSITIVE CONTROL ON THE MANIPULATION: saw=1 must actually walk.
    assert len(set(trajs[1.0])) > 1, "the walk did not move — audit is inert"
    assert len(set(trajs[0.0])) == 1, "saw=0 must be frozen"
    # POSITIVE CONTROL ON THE READER: there must be an image to move.
    assert out[1.0][-1]["lum"].std() > 0.05, "no image on the sheet"

    for key in ("lum", "resp"):
        d = max(float(np.max(np.abs(out[1.0][t][key] - out[0.0][t][key])))
                for t in range(60))
        assert d > 0.0, f"{key} still does not move with the drift (D={d})"


# --------------------------------------------------------------- JOB 2
def test_setpoint_falls_out_of_the_eyes_own_endogenous_activity():
    """`mu_endo` must equal the mean of what the cell actually emitted.

    The estimator is UNBIASED by construction (a cumulative mean), so this gate
    is a tautology-check on the WIRING, not on the biology: it fails if the
    endogenous path is not reaching the cell at all.
    """
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ww = WaveWorld(s, h=8, w=8, seed=0)
    ey = eye_world.EyeWorld(s, h=8, w=8, gaze_l=11, seed=0)
    assert ey.couple_waves(ww) == 64
    eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0)

    # THE OFF-BY-ONE, DOCUMENTED RATHER THAN HIDDEN. `resp_step` starts at the
    # -1 sentinel, so on the FIRST wave tick `Eye.step`(0) > -1 already holds and
    # `ey_endo_resp` fires DURING `ww.step()` -- the eye takes one legitimate
    # endogenous sample before its own clock ever advances. So N samples of the
    # eye's clock produce N+1 samples of the cell. Benign (the extra reading is a
    # real sample of the endogenous activity, and it is identical in both arms --
    # 1/3200 = 0.03% of the confirmatory calibration), but the gate must assert
    # the ARITHMETIC, not my bookkeeping. Found by this test failing: measured
    # mu_endo 78/401 = 0.194514 where the test assumed 78/400 = 0.195.
    emitted = []
    ww.step(ignite_k=1)
    emitted.append(ey.responses().copy())      # the step-0 sample
    for t in range(1, 401):
        if t > 1:
            ww.step(ignite_k=1 if (t - 1) % 5 == 0 else 0)
        ey.step(frame=None)
        emitted.append(ey.responses().copy())

    # POSITIVE CONTROL ON THE INPUT: the eye must HAVE endogenous activity.
    # (The convergence probe's first cut read `frame()` here and got 0.0234 vs
    # the true 0.1444 -- a 6x error off the wrong attribute, IN THE DIRECTION
    # THAT WOULD HAVE CONFIRMED GCAL's 0.024. Read what the rule reads.)
    em = np.stack(emitted)
    assert em.mean() > 0.0, "no endogenous activity — the probe says nothing"

    mu = ey.mu_endos()
    mu_n = float(ey.s.node(ey.cells[(0, 0)])["attrs"]["mu_n"])
    assert mu_n == len(emitted), (
        f"the cell counted {mu_n} samples; the probe saw {len(emitted)}")
    # THE INVARIANT: mu_endo * n == the running SUM of the cell's own output.
    assert np.allclose(mu * mu_n, em.sum(axis=0), atol=1e-9), (
        "mu_endo is not the cumulative mean of the cell's own output")
    assert mu.mean() > 0.0


def test_endogenous_setpoint_keeps_the_eye_alive_where_the_constant_kills_it():
    """The headline, on a burned seed: same eye, same waves, same input, and the
    ONLY difference is where the setpoint came from.

    Short calibration (400 steps) -- this is a wiring gate, not the confirmatory
    run (seeds 14000-14007, `scripts/eye_setpoint_confirm.py`).
    """
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from eye_setpoint_lib import run_arm

    a = run_arm(0, mu_mode=0.0, calib_steps=400, vis_steps=400)
    b = run_arm(0, mu_mode=1.0, calib_steps=400, vis_steps=400)

    # §1.1: a DEAD arm scores a perfect floor. Report aliveness, not just a score.
    assert b["min_alive"] > a["min_alive"], (
        f"endogenous setpoint did not outlive the constant: "
        f"A={a['min_alive']}, B={b['min_alive']}")
    assert b["min_alive"] == 1.0, "arm B should never have a silent cell"
    # The setpoint is nowhere near GCAL's -- that is WHY the arms differ.
    assert b["mu_endo"] > 5 * 0.024


def test_theta_is_frozen_during_the_calibration_phase():
    """A homeostat running during the measurement would regulate the very
    quantity being measured. Both adapt rules carry the `calib<0.5` guard."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ww = WaveWorld(s, h=8, w=8, seed=0)
    ey = eye_world.EyeWorld(s, h=8, w=8, gaze_l=11, seed=0)
    ey.couple_waves(ww)
    eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0, mu_mode=1.0)
    for t in range(1, 201):
        ww.step(ignite_k=1 if (t - 1) % 5 == 0 else 0)
        ey.step(frame=None)
        assert float(np.abs(ey.thetas()).max()) == 0.0, (
            f"theta moved during calibration at t={t}")


@pytest.mark.parametrize("rule", ["ey_sample_at_gaze", "ey_endo_resp",
                                  "ey_endo_latch", "ey_adapt_theta_endo"])
def test_every_new_decision_is_a_seed_rule(rule):
    """CLAUDE.md: the agent is a graph in Rust; Python is only a world adapter.
    The sampling decision, the coupling and the setpoint are all seed rules."""
    names = [r["name"] for r in _seed_json()["rules"]]
    assert rule in names


def test_adapter_states_no_setpoint_and_no_statistic():
    """A source audit, positive rather than off a soft accessor.

    `couple_waves` may state WHERE the endogenous activity is (geometry); it must
    never compute WHAT the setpoint is. No mean/sum/statistic in the adapter's
    coupling path, and no literal 0.024 anywhere in it.
    """
    src = open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "domains", "eye_world.py")).read()
    i = src.index("def couple_waves")
    j = src.index("def mu_endos")
    body = src[i:j]
    for bad in (".mean(", ".sum(", "0.024", "np.average"):
        assert bad not in body, f"adapter computes {bad!r} in the coupling path"
