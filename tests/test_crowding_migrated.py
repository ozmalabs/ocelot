"""CROWDING (T8) — the migrated gate. VISION_CROWDING_PREREG.md (committed 8703131e).

Eccentricity-scaled statistical pooling validates the eye's foveation / eccentricity-decay
prior. Recognition READS a pooled summary over R=bouma·ecc from the fixation: an isolated
peripheral target survives (pool={target}); flanked it is JUMBLED (pool mixes); a foveal
target is SPARED by the same flankers; critical spacing grows with eccentricity (Bouma).
Every decision is in seeds/vision_crowding.json (cr_ecc / cr_pool); the test only builds
item fields and reads attrs back.
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import crowding_world as cw  # noqa: E402

BOUMA = 0.6
T_IDENT, F_IDENT = 5.0, 9.0


def _run(items, *, gaze=(0, 0), crowd=1.0, bouma=BOUMA):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_crowding"])
    h = cw.add_field(s, items, gaze=gaze)
    cw.set_flag(s, crowd=crowd, bouma=bouma)
    cw.tick(s)
    return s, h


def _t(ecc, ident=T_IDENT):
    return {"irow": ecc, "icol": 0, "ident": ident, "is_target": True}


def _f(ecc, sF, ident=F_IDENT):
    return {"irow": ecc + sF, "icol": 0, "ident": ident}


# ---- ARM A: CROWDING ----------------------------------------------------------
def test_A_peripheral_flanked_is_crowded_isolated_is_not():
    sF, hF = _run([_t(10), _f(10, 3)])
    sI, hI = _run([_t(10)])
    rF, rI = cw.target_readout(sF, hF), cw.target_readout(sI, hI)
    # flanked: identity LOST to the mixed pooled summary
    assert rF["recognized"] == 0 and rF["pool_n"] == 2 and rF["pooled_ident"] == 7.0
    # isolated: pool = {target}, identity survives
    assert rI["recognized"] == 1 and rI["pool_n"] == 1 and rI["pooled_ident"] == T_IDENT


# ---- ARM B: FOVEAL SPARING (the risked dissociation) --------------------------
def test_B_foveal_target_is_spared_by_the_same_flankers():
    sB1, hB1 = _run([_t(2), _f(2, 3)])     # foveal, sF=3
    sB2, hB2 = _run([_t(10), _f(10, 3)])   # peripheral, SAME sF=3
    assert cw.recognized(sB1, hB1) == 1    # spared (R=1.2 < 3)
    assert cw.recognized(sB2, hB2) == 0    # crowded (R=6.0 >= 3)


# ---- ARM C: ECCENTRICITY-SCALING (ENTAILED — consistency check) ---------------
def _crit(ecc, bouma=BOUMA, smax=15):
    last = 0
    for sF in range(1, smax + 1):
        s, h = _run([_t(ecc), _f(ecc, sF)], bouma=bouma)
        if cw.crowded(s, h) == 1:
            last = sF
    return last


def test_C_critical_spacing_grows_with_eccentricity():
    sstar = {e: _crit(e) for e in (4, 8, 12)}
    assert sstar == {4: 2, 8: 4, 12: 7}          # floor(0.6·ecc)
    assert sstar[4] < sstar[8] < sstar[12]       # strictly monotone (Bouma)


# ---- ARM D: FLOOR / §1.1 (controls valid + recognizer ALIVE) ------------------
def test_D_isolated_targets_recognized_and_recognizer_alive():
    assert cw.recognized(*_run([_t(10)])) == 1          # isolated peripheral
    assert cw.recognized(*_run([_t(2)])) == 1           # isolated foveal
    # ALIVE: both recognized states reachable (not a constant reader / dead arm §1.1)
    assert cw.recognized(*_run([_t(10), _f(10, 3)])) == 0


# ---- ARM E: NOISE FLOOR (n=100 fixed, seeds 43100-43199) ----------------------
def test_E_isolated_noise_never_false_crowds():
    false_crowd = 0
    for i in range(100):
        rng = random.Random(43100 + i)
        ecc = rng.randint(1, 14)
        s, h = _run([{"irow": ecc, "icol": rng.randint(-3, 3),
                      "ident": float(rng.randint(0, 20)), "is_target": True}])
        if cw.recognized(s, h) != 1:
            false_crowd += 1
    assert false_crowd == 0


# ---- ARM F: §9 OFF-DAY --------------------------------------------------------
def test_F_flag_off_is_inert():
    s, h = _run([_t(10), _f(10, 3)], crowd=0.0)   # OFF (also the default)
    r = cw.target_readout(s, h)
    assert (r["pool_n"] == 0.0 and r["crowded"] == 0.0 and r["recognized"] == 0.0
            and r["pool_radius2"] == 0.0 and r["ecc2"] == 0.0)


def test_F_default_flag_is_off():
    # the seed ships crowd=0.0 — a fresh boot is inert without any flag write.
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_crowding"])
    p = list(s.nodes("CrowdParams"))[0]
    assert float(s.node(p)["attrs"]["crowd"]) == 0.0


# ---- b-invariance (the magnitude is a free scale, §13) ------------------------
def test_b_invariance_qualitative_arms_hold_for_any_bouma():
    for b in (0.4, 0.6, 0.8):
        # crowding + foveal sparing hold; crit spacing scales with b but stays monotone
        assert cw.recognized(*_run([_t(10), _f(10, 3)], bouma=b)) == 0
        assert cw.recognized(*_run([_t(2), _f(2, 3)], bouma=b)) == 1
        sstar = {e: _crit(e, bouma=b) for e in (4, 8, 12)}
        assert sstar[4] < sstar[8] < sstar[12]
