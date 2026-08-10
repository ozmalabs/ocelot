#!/usr/bin/env python3
"""McCOLLOUGH CONTINGENT AFTEREFFECT — the confirmatory run (VISION_MCCOLLOUGH_PREREG.md).

THE decisive predictive-coding gate (VISION_VENTRAL_GROUNDING.md §FAILURE-MODE
GATES). This runner only CONSTRUCTS oriented colour-patch stimuli and READS the
percept / prior back (mechanical I/O, §0); the learned joint prior
E[colour|orientation], the render-from-prior + opponent-residual (predictive) and
the direct read (feedforward) are ALL seed rules (vision_mccollough).

Run from the gamma-substrate dir:
    PYTHONPATH=runners/dsl/python:. python scripts/mccollough_measure.py
"""
from __future__ import annotations
import json
import os
import random
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import mccollough_world as mw  # noqa: E402

# opponent-colour stimulus definitions (integer cone values, in-frame).
NEUTRAL = dict(cL=10, cM=10, cS=10)            # achromatic: rg=0
RED     = dict(cL=15, cM=5,  cS=10)            # rg=+10 on L-M
GREEN   = dict(cL=5,  cM=15, cS=10)            # rg=-10 on L-M
VERT, HORIZ = 90.0, 0.0                        # orientation labels (arbitrary, distinct)
FRAMES = 8


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_mccollough"])
    return s, ag


def _standard_adapt():
    return [dict(theta=VERT, is_adapt=1.0, **RED),
            dict(theta=HORIZ, is_adapt=1.0, **GREEN)]


# =========================================================================== #
#  H_contingency + swap flip (headline)  — PREDICTIVE readout
# =========================================================================== #
def arm_contingency():
    s, _ = _boot()
    test = [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
            dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)]
    h = mw.add_field(s, patches=_standard_adapt() + test)
    mw.set_flags(s, enabled=1.0, mode=0.0)     # predictive
    mw.adapt(s, h, frames=FRAMES)
    mw.test(s, h)
    pv = mw.cell_percept(s, h, 10, 0, "percept_rg")
    ph = mw.cell_percept(s, h, 11, 0, "percept_rg")
    pv_by = mw.cell_percept(s, h, 10, 0, "percept_by")
    ph_by = mw.cell_percept(s, h, 11, 0, "percept_by")
    C = pv - ph
    ok = (pv < 0.0) and (ph > 0.0) and (C < 0.0)
    return {"pass": bool(ok), "percept_rg_vert": pv, "percept_rg_horiz": ph,
            "contingency": C, "percept_by_vert": pv_by, "percept_by_horiz": ph_by,
            "prior_vert": mw.prior_of(s, h, VERT), "prior_horiz": mw.prior_of(s, h, HORIZ)}


def arm_swap_flip():
    """The SAME achromatic patch read under vertical vs horizontal labels — the
    aftereffect colour FLIPS with orientation (the joint-code claim)."""
    s, _ = _boot()
    # one achromatic test patch per label; the ONLY difference is theta.
    test = [dict(theta=VERT, rrow=20, is_adapt=0.0, **NEUTRAL),
            dict(theta=HORIZ, rrow=21, is_adapt=0.0, **NEUTRAL)]
    h = mw.add_field(s, patches=_standard_adapt() + test)
    mw.set_flags(s, enabled=1.0, mode=0.0)
    mw.adapt(s, h, frames=FRAMES)
    mw.test(s, h)
    a = mw.cell_percept(s, h, 20, 0, "percept_rg")   # same neutral, theta=vert
    b = mw.cell_percept(s, h, 21, 0, "percept_rg")   # same neutral, theta=horiz
    ok = (a < 0.0 < b) and (a == -b)
    return {"pass": bool(ok), "vert_label": a, "horiz_label": b,
            "flipped": bool(a * b < 0)}


# =========================================================================== #
#  H_crux — the FEEDFORWARD control (THE decisive test, §1.1)
# =========================================================================== #
def arm_crux():
    # predictive percept on achromatic test
    s, _ = _boot()
    test = [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
            dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)]
    h = mw.add_field(s, patches=_standard_adapt() + test)
    mw.set_flags(s, enabled=1.0, mode=0.0)
    mw.adapt(s, h, frames=FRAMES); mw.test(s, h)
    pred_v = mw.cell_percept(s, h, 10, 0, "percept_rg")
    pred_h = mw.cell_percept(s, h, 11, 0, "percept_rg")

    # FEEDFORWARD control: same adaptation, same achromatic test, mode=1
    s2, _ = _boot()
    h2 = mw.add_field(s2, patches=_standard_adapt() + test)
    mw.set_flags(s2, enabled=1.0, mode=1.0)     # feedforward
    mw.adapt(s2, h2, frames=FRAMES); mw.test(s2, h2)
    ff_v = mw.cell_percept(s2, h2, 10, 0, "percept_rg")
    ff_h = mw.cell_percept(s2, h2, 11, 0, "percept_rg")

    # FF-ALIVE positive control (§1.1): coloured test reports the real colour
    s3, _ = _boot()
    h3 = mw.add_field(s3, patches=_standard_adapt() +
                      [dict(theta=VERT, rrow=10, is_adapt=0.0, **RED)])
    mw.set_flags(s3, enabled=1.0, mode=1.0)
    mw.adapt(s3, h3, frames=FRAMES); mw.test(s3, h3)
    ff_alive = mw.cell_percept(s3, h3, 10, 0, "percept_rg")

    D_crux = abs(pred_v - ff_v)
    ff_null = (ff_v == 0.0) and (ff_h == 0.0)
    alive = (ff_alive != 0.0)
    ok = ff_null and (D_crux > 0.0) and alive
    return {"pass": bool(ok), "pred_vert": pred_v, "pred_horiz": pred_h,
            "ff_vert": ff_v, "ff_horiz": ff_h, "D_crux": D_crux,
            "ff_null": bool(ff_null), "ff_alive_coloured": ff_alive,
            "ff_arm_alive": bool(alive)}


# =========================================================================== #
#  H_persist — error-driven, STORED prior (not momentary fatigue)
# =========================================================================== #
def arm_persist(intervening_ticks: int = 50):
    s, _ = _boot()
    test = [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL)]
    h = mw.add_field(s, patches=_standard_adapt() + test)
    mw.set_flags(s, enabled=1.0, mode=0.0)
    mw.adapt(s, h, frames=FRAMES)
    prior_before = mw.prior_of(s, h, VERT)
    # INTERVENING no-adaptation tick block (still adapt phase, but no frame bump ->
    # mcc_learn cannot fire again; nothing accumulates). Fatigue would recover here.
    mw.set_phase(s, 0.0)
    for _ in range(intervening_ticks):
        mw.tick(s)
    prior_after = mw.prior_of(s, h, VERT)
    mw.test(s, h)
    percept = mw.cell_percept(s, h, 10, 0, "percept_rg")
    stored_identical = (prior_before == prior_after)
    # error-driven: prior magnitude grows with exposure (1 frame vs FRAMES frames)
    s1, _ = _boot()
    h1 = mw.add_field(s1, patches=[dict(theta=VERT, is_adapt=1.0, **RED)])
    mw.set_flags(s1, enabled=1.0, mode=0.0)
    mw.adapt(s1, h1, frames=1)
    n1 = mw.prior_of(s1, h1, VERT)["n"]
    ok = stored_identical and (percept < 0.0) and (prior_after["n"] == float(FRAMES)) and (n1 == 1.0)
    return {"pass": bool(ok), "prior_before": prior_before, "prior_after": prior_after,
            "stored_bit_identical": bool(stored_identical), "percept_after": percept,
            "n_after_1_frame": n1, "n_after_FRAMES": prior_after["n"]}


# =========================================================================== #
#  H_floor — (a) no adaptation  (b) colour alone (no orientation pairing)
# =========================================================================== #
def arm_floor_no_adapt():
    s, _ = _boot()
    h = mw.add_field(s, patches=[dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL)])
    mw.set_flags(s, enabled=1.0, mode=0.0)
    mw.test(s, h)   # NO adaptation
    p = mw.cell_percept(s, h, 10, 0, "percept_rg")
    return {"pass": bool(p == 0.0), "percept_rg": p, "prior": mw.prior_of(s, h, VERT)}


def arm_floor_colour_alone():
    s, _ = _boot()
    # RED adapted on BOTH orientations -> no CONTINGENCY (colour without pairing)
    adapt = [dict(theta=VERT, is_adapt=1.0, **RED),
             dict(theta=HORIZ, is_adapt=1.0, **RED)]
    test = [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
            dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)]
    h = mw.add_field(s, patches=adapt + test)
    mw.set_flags(s, enabled=1.0, mode=0.0)
    mw.adapt(s, h, frames=FRAMES); mw.test(s, h)
    pv = mw.cell_percept(s, h, 10, 0, "percept_rg")
    ph = mw.cell_percept(s, h, 11, 0, "percept_rg")
    C = pv - ph
    ok = (pv == ph) and (pv != 0.0) and (C == 0.0)
    return {"pass": bool(ok), "percept_rg_vert": pv, "percept_rg_horiz": ph,
            "contingency": C}


# =========================================================================== #
#  H_noise — iid colour-noise adaptation invents no coherent contingency
#            (confirmatory seeds 41000-41099)
# =========================================================================== #
def _noise_colour(rng):
    """A zero-mean random opponent colour on the rg axis: rg = cL-cM drawn
    symmetric about 0 (k in {-10,0,+10}); by = S-(L+M) held at -10 as the
    structured stimuli (equiluminant on by)."""
    k = rng.choice([-10, 0, 10])          # symmetric integer rg, mean 0
    cL = 10 + (k if k > 0 else 0)
    cM = 10 + (-k if k < 0 else 0)
    cS = cL + cM - 10                      # by = cS-(cL+cM) = -10
    return dict(cL=float(cL), cM=float(cM), cS=float(cS))


def arm_noise(n=100, seed0=41000, structured_C=-20.0):
    hits = 0
    Cs = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        s, _ = _boot()
        # ONE adapt patch per orientation (no RMW), re-coloured with fresh noise
        # each frame — the exact analog of the structured FRAMES-frame adaptation.
        av = dict(theta=VERT, rrow=0, is_adapt=1.0, **NEUTRAL)
        ah = dict(theta=HORIZ, rrow=1, is_adapt=1.0, **NEUTRAL)
        test = [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
                dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)]
        h = mw.add_field(s, patches=[av, ah] + test)
        mw.set_flags(s, enabled=1.0, mode=0.0)
        vid = h["index"][(0, 0)]; hid = h["index"][(1, 0)]
        mw.set_phase(s, 0.0)
        for f in range(1, FRAMES + 1):
            for nid, col in ((vid, _noise_colour(rng)), (hid, _noise_colour(rng))):
                for kk, vv in col.items():
                    s.set_attr(nid, kk, vv)     # mechanical: re-present the frame
            mw.set_frame(s, float(f))
            mw.tick(s)
        mw.test(s, h)
        pv = mw.cell_percept(s, h, 10, 0, "percept_rg")
        ph = mw.cell_percept(s, h, 11, 0, "percept_rg")
        C = pv - ph
        Cs.append(C)
        if abs(C) >= abs(structured_C):
            hits += 1
    mean_C = sum(Cs) / len(Cs)
    ok = (hits == 0)
    return {"pass": bool(ok), "n": n, "hits_ge_structured": hits,
            "structured_C": structured_C, "mean_C_noise": mean_C,
            "max_abs_C_noise": max(abs(c) for c in Cs),
            "seeds": [seed0, seed0 + n - 1]}


# =========================================================================== #
#  H_offday (§9) — flag OFF => inert
# =========================================================================== #
def arm_offday():
    s, _ = _boot()
    h = mw.add_field(s, patches=[dict(theta=VERT, rrow=10, is_adapt=1.0, **RED),
                                 dict(theta=VERT, rrow=11, is_adapt=0.0, **NEUTRAL)])
    mw.set_flags(s, enabled=0.0, mode=0.0)     # OFF (default)
    mw.adapt(s, h, frames=FRAMES); mw.test(s, h)
    p = mw.cell_percept(s, h, 11, 0, "percept_rg")
    pr = mw.prior_of(s, h, VERT)
    ok = (p == 0.0) and (pr["n"] == 0.0)
    return {"pass": bool(ok), "percept_rg": p, "prior": pr}


def main():
    t0 = time.time()
    prov = provenance_line()
    print(prov)
    results = {
        "provenance": prov,
        "contingency": arm_contingency(),
        "swap_flip": arm_swap_flip(),
        "crux": arm_crux(),
        "persist": arm_persist(),
        "floor_no_adapt": arm_floor_no_adapt(),
        "floor_colour_alone": arm_floor_colour_alone(),
        "offday": arm_offday(),
        "noise": arm_noise(),
    }
    results["all_pass"] = all(v.get("pass") for k, v in results.items()
                              if isinstance(v, dict) and "pass" in v)
    results["elapsed_s"] = time.time() - t0
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outp = os.path.join(here, "results", "mccollough_measure.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as f:
        json.dump(results, f, indent=2)
    for k, v in results.items():
        if isinstance(v, dict) and "pass" in v:
            print(f"  {'PASS' if v['pass'] else 'FAIL'}  {k}: "
                  f"{ {kk: vv for kk, vv in v.items() if kk != 'pass'} }")
    print(f"ALL_PASS={results['all_pass']}  ({results['elapsed_s']:.1f}s)  -> {outp}")


if __name__ == "__main__":
    main()
