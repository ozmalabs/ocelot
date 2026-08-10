#!/usr/bin/env python3
"""CROWDING (T8) — the confirmatory run.

Pre-registration: VISION_CROWDING_PREREG.md (committed BEFORE this run, §3, at 8703131e).
Recognition READS a pooled summary over an eccentricity-scaled region (R=bouma·ecc from
the fixation): an isolated peripheral target survives (pool={target}); a flanked one is
JUMBLED (pool=target+flankers, the mean ident mixes); a FOVEAL target is SPARED by the
SAME flankers; critical spacing grows with eccentricity (Bouma). The eccentricity, radius,
pool membership, summary statistic and verdict are ALL in seeds/vision_crowding.json's
rules; this runner only CONSTRUCTS item fields and READS pool_n/recognized/crowded/
pooled_ident back (mechanical I/O, §0), and tallies the arms.

Run from the gamma-substrate dir:  PYTHONPATH=runners/dsl/python python scripts/crowding_measure.py
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
from domains import crowding_world as cw  # noqa: E402

BOUMA = 0.6
T_IDENT, F_IDENT = 5.0, 9.0   # chosen so a pooled mean can NEVER equal the target ident


def _run(items, *, gaze=(0, 0), crowd=1.0, bouma=BOUMA):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_crowding"])
    h = cw.add_field(s, items, gaze=gaze)
    cw.set_flag(s, crowd=crowd, bouma=bouma)
    cw.tick(s)
    return s, h


def _target(ecc, ident=T_IDENT):
    return {"irow": ecc, "icol": 0, "ident": ident, "is_target": True}


def _flanker(ecc, sF, ident=F_IDENT):
    # radially outward from the target at spacing sF (distance from target = sF).
    return {"irow": ecc + sF, "icol": 0, "ident": ident}


# ---- ARM A: CROWDING (headline) -----------------------------------------------
def arm_crowding(bouma=BOUMA):
    s1, h1 = _run([_target(10), _flanker(10, 3)], bouma=bouma)   # A1 flanked
    r1 = cw.target_readout(s1, h1)
    s2, h2 = _run([_target(10)], bouma=bouma)                    # A2 isolated
    r2 = cw.target_readout(s2, h2)
    passed = (r1["recognized"] == 0 and r2["recognized"] == 1
              and r1["pooled_ident"] != T_IDENT and r2["pooled_ident"] == T_IDENT)
    return {"flanked": r1, "isolated": r2,
            "flanked_jumbled_to": r1["pooled_ident"], "isolated_ident": r2["pooled_ident"],
            "pass": passed}


# ---- ARM B: FOVEAL SPARING (the risked dissociation) --------------------------
def arm_foveal_sparing(bouma=BOUMA):
    sB1, hB1 = _run([_target(2), _flanker(2, 3)], bouma=bouma)    # foveal, sF=3
    b1 = cw.target_readout(sB1, hB1)
    sB2, hB2 = _run([_target(10), _flanker(10, 3)], bouma=bouma)  # peripheral, sF=3
    b2 = cw.target_readout(sB2, hB2)
    passed = (b1["recognized"] == 1 and b2["recognized"] == 0)   # SAME spacing, opposite
    return {"foveal_ecc2": 2, "peripheral_ecc2": 10, "same_spacing": 3,
            "foveal": b1, "peripheral": b2,
            "dissociation_at_matched_spacing": passed, "pass": passed}


# ---- ARM C: ECCENTRICITY-SCALING / Bouma (ENTAILED, reported not banked) ------
def _crit_spacing(ecc, bouma=BOUMA, smax=15):
    """Largest integer flanker spacing that still crowds the target at `ecc`."""
    last = 0
    for sF in range(1, smax + 1):
        s, h = _run([_target(ecc), _flanker(ecc, sF)], bouma=bouma)
        if cw.crowded(s, h) == 1:
            last = sF
    return last


def arm_eccentricity_scaling(bouma=BOUMA):
    eccs = [4, 8, 12]
    sstar = {e: _crit_spacing(e, bouma=bouma) for e in eccs}
    predicted = {e: int(bouma * e) for e in eccs}   # floor(bouma·ecc)
    monotone = sstar[4] < sstar[8] < sstar[12]
    matches = (sstar == predicted)
    ratio = {e: round(sstar[e] / e, 3) for e in eccs}
    return {"crit_spacing": sstar, "predicted_floor_bouma_ecc": predicted,
            "matches_prediction": matches, "monotone_increasing": monotone,
            "sstar_over_ecc": ratio,
            "note": "ENTAILED by R=bouma·ecc (§13.1) — a consistency check, not "
                    "discovery evidence. s*/ecc ~= bouma is Bouma's constant-fraction law.",
            "pass": monotone}


# ---- ARM D: FLOOR / §1.1 (controls valid + recognizer ALIVE) ------------------
def arm_floor(bouma=BOUMA):
    sP, hP = _run([_target(10)], bouma=bouma)   # isolated peripheral
    sF_, hF = _run([_target(2)], bouma=bouma)   # isolated foveal
    d1 = cw.recognized(sP, hP) == 1
    d2 = cw.recognized(sF_, hF) == 1
    # ALIVE: both recognized states are reachable across arms (not a constant reader).
    sC, hC = _run([_target(10), _flanker(10, 3)], bouma=bouma)   # a crowded case → 0
    reached_1 = d1
    reached_0 = cw.recognized(sC, hC) == 0
    alive = reached_1 and reached_0
    return {"isolated_peripheral_recognized": d1, "isolated_foveal_recognized": d2,
            "both_states_reached": alive,
            "recognized_states_seen": sorted({int(reached_1), 0 if reached_0 else 1}),
            "pass": (d1 and d2 and alive)}


# ---- ARM E: NOISE FLOOR (§1.1 dead-arm positive control; n=100 fixed) ---------
def arm_noise_floor(n=100, base_seed=43100, bouma=BOUMA):
    false_crowd = 0
    detail = []
    for i in range(n):
        rng = random.Random(base_seed + i)
        ecc = rng.randint(1, 14)
        ident = float(rng.randint(0, 20))
        s, h = _run([{"irow": ecc, "icol": rng.randint(-3, 3),
                      "ident": ident, "is_target": True}], bouma=bouma)
        if cw.recognized(s, h) != 1:   # an isolated item MUST be recognized
            false_crowd += 1
            detail.append({"seed": base_seed + i, "ecc": ecc,
                           "readout": cw.target_readout(s, h)})
    return {"n": n, "seed_range": [base_seed, base_seed + n - 1],
            "false_crowded_isolated": false_crowd, "detail": detail,
            "pass": (false_crowd == 0)}


# ---- ARM F: §9 OFF-DAY --------------------------------------------------------
def arm_offday():
    s, h = _run([_target(10), _flanker(10, 3)], crowd=0.0)   # flag OFF (also default)
    r = cw.target_readout(s, h)
    inert = (r["pool_n"] == 0.0 and r["crowded"] == 0.0 and r["recognized"] == 0.0
             and r["pool_radius2"] == 0.0 and r["ecc2"] == 0.0)
    return {"readout_off": r, "inert": inert, "pass": inert}


# ---- NON-GATED: b-invariance (every qualitative arm holds for any b>0) ---------
def report_b_invariance():
    out = {}
    for b in (0.4, 0.6, 0.8):
        A = arm_crowding(bouma=b)
        B = arm_foveal_sparing(bouma=b)
        C = arm_eccentricity_scaling(bouma=b)
        out[str(b)] = {"crowding_pass": A["pass"], "foveal_sparing_pass": B["pass"],
                       "monotone_pass": C["pass"], "crit_spacing": C["crit_spacing"]}
    all_hold = all(v["crowding_pass"] and v["foveal_sparing_pass"] and v["monotone_pass"]
                   for v in out.values())
    return {"per_bouma": out, "qualitative_arms_hold_for_all_b": all_hold,
            "note": "bouma is a free scale (graph data), NOT a biological constant; only "
                    "the numeric crit-spacing values depend on it (§13)."}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov, "prereg_commit": "8703131e", "bouma": BOUMA,
        "target_ident": T_IDENT, "flanker_ident": F_IDENT,
        "A_crowding": arm_crowding(),
        "B_foveal_sparing": arm_foveal_sparing(),
        "C_eccentricity_scaling": arm_eccentricity_scaling(),
        "D_floor": arm_floor(),
        "E_noise_floor": arm_noise_floor(),
        "F_offday": arm_offday(),
        "b_invariance_NONGATED": report_b_invariance(),
    }
    confirmatory = ["A_crowding", "B_foveal_sparing", "C_eccentricity_scaling",
                    "D_floor", "E_noise_floor", "F_offday"]
    results["ALL_CONFIRMATORY_PASS"] = all(results[k]["pass"] for k in confirmatory)
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "crowding_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in confirmatory:
        print(f"  {k:24s} pass={results[k]['pass']}")
    print(f"  {'b_invariance(nongated)':24s} hold="
          f"{results['b_invariance_NONGATED']['qualitative_arms_hold_for_all_b']}")
    print("ALL_CONFIRMATORY_PASS:", results["ALL_CONFIRMATORY_PASS"],
          "| wrote", out, "|", results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
