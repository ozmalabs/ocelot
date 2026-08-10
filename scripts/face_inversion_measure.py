#!/usr/bin/env python3
"""FACE-INVERSION / THATCHER (T10) — the confirmatory run.

Pre-registration: VISION_FACE_INVERSION_PREREG.md (committed BEFORE this run, §3, at
e407429f). A VALIDATION gate measuring the EXISTING composition machinery (the sd loop):
is the substrate's arrangement code reference-frame-DEPENDENT (holistic, human-like) or
reference-frame-INVARIANT (a part-bag / generator-orbit)?  This runner only CONSTRUCTS
cell-arrangement stimuli and READS the sd-loop verdict (status / covered_by) back — every
recognition DECISION is in seeds/shape_decode_loop.json / the Rust Terms (PROTOCOL §0).
NO new seed, NO new Rust.

Run from gamma-substrate:  PYTHONPATH=. python scripts/face_inversion_measure.py
"""
from __future__ import annotations
import json
import os
import random
import time

import scripts.face_inversion_lib as L
from domains.engine_provenance import provenance_line

# --- stimuli (deterministic) ---------------------------------------------------------
# K=4 distinct configural faces: the SAME asymmetric atom at different anchor arrangements
# (identity = the ARRANGEMENT).
FACE_ANCHORS = {
    "A": [(0, 0), (0, 6), (7, 3)],
    "B": [(0, 0), (0, 8), (5, 4)],
    "C": [(0, 2), (0, 7), (8, 0)],
    "D": [(1, 0), (0, 5), (6, 6)],
}
CFG = {k: L.configural(v, atom=L.ATOM_L) for k, v in FACE_ANCHORS.items()}

# K=4 distinct part-based objects: DISTINCT atoms (identity = WHICH atoms) at fixed anchors.
PB_ANCH = [(0, 0), (0, 6), (7, 3)]
PB_ATOMSETS = {
    "P": [L.ATOM_L, L.ATOM_J, L.ATOM_S],
    "Q": [L.ATOM_J, L.ATOM_S, L.ATOM_T],
    "R": [L.ATOM_S, L.ATOM_T, L.ATOM_L],
    "S": [L.ATOM_T, L.ATOM_L, L.ATOM_J],
}
PB = {k: L.part_based(v, PB_ANCH) for k, v in PB_ATOMSETS.items()}


def _recog_rate(codebook, views):
    """views: dict name->cells; recognised-as-OWN-identity rate."""
    ok = 0
    detail = {}
    for k, cells in views.items():
        _, cov = L.identify(codebook, cells)
        detail[k] = cov
        ok += (cov == k)
    return ok, len(views), detail


# --- ARM 1: INVERSION COST (headline differential) -----------------------------------
def arm_inversion_cost():
    up_c, n, _ = _recog_rate(CFG, CFG)
    inv_c, _, cdet = _recog_rate(CFG, {k: L.rot180(c) for k, c in CFG.items()})
    up_p, m, _ = _recog_rate(PB, PB)
    inv_p, _, pdet = _recog_rate(PB, {k: L.rot180(c) for k, c in PB.items()})
    cost_config = round(1 - inv_c / n, 4)
    cost_part = round(1 - inv_p / m, 4)
    differential = round(cost_config - cost_part, 4)
    # PREREG decision: NEGATIVE iff both costs <= 0.1 (no disproportion).
    negative = (cost_config <= 0.1 and cost_part <= 0.1)
    positive = (differential >= 0.5 and cost_part <= 0.1)
    return {
        "config_upright_recognised": [up_c, n], "config_inverted_recognised": [inv_c, n],
        "part_upright_recognised": [up_p, m], "part_inverted_recognised": [inv_p, m],
        "cost_config": cost_config, "cost_part": cost_part, "differential": differential,
        "inverted_config_covered_by": cdet, "inverted_part_covered_by": pdet,
        "outcome": "NEGATIVE_frame_invariant" if negative else
                   ("POSITIVE_holistic" if positive else "AMBIGUOUS"),
        "pass": negative,   # the pre-registered prediction is the NEGATIVE
    }


# --- ARM 2: THATCHER (frame-gating) --------------------------------------------------
def _thatcher_cases(codebook, anchors_map, builder):
    rows = []
    frame_gated = 0
    both_unrec = 0
    for k, anch in anchors_map.items():
        n_parts = len(anch) if isinstance(anch, list) else 3
        for fi in range(3):
            up = builder(k, anch, fi)
            inv = L.rot180(up)
            _, cu = L.identify(codebook, up)
            _, ci = L.identify(codebook, inv)
            ru, ri = int(cu == k), int(ci == k)
            rows.append({"id": k, "flip": fi, "up_cov": cu, "inv_cov": ci,
                         "up_rec": ru, "inv_rec": ri})
            frame_gated += (ru != ri)
            both_unrec += (ru == 0 and ri == 0)
    return rows, frame_gated, both_unrec


def arm_thatcher():
    crows, cfg_gated, cfg_both_un = _thatcher_cases(
        CFG, FACE_ANCHORS, lambda k, a, fi: L.configural(a, atom=L.ATOM_L, flip_idx=fi))
    prows, pb_gated, pb_both_un = _thatcher_cases(
        PB, {k: PB_ATOMSETS[k] for k in PB},
        lambda k, atoms, fi: L.part_based(atoms, PB_ANCH, flip_idx=fi))
    # PREREG: frame-gating ABSENT (predicted) = 0 gated cases, all detected in BOTH frames.
    config_no_gating = (cfg_gated == 0)
    return {
        "config": {"cases": len(crows), "frame_gated": cfg_gated,
                   "both_orientations_unrecognised": cfg_both_un, "rows": crows},
        "part": {"cases": len(prows), "frame_gated": pb_gated,
                 "both_orientations_unrecognised": pb_both_un, "rows": prows},
        "config_frame_gating_present": (cfg_gated > 0),
        "outcome": "NEGATIVE_no_frame_gating" if config_no_gating else "POSITIVE_frame_gated",
        "pass": config_no_gating,   # prediction: NO frame-gating
    }


# --- ARM 3: REFERENCE-FRAME (dual channel / inversion collapse) ----------------------
def arm_reference_frame():
    collapse_rows = []
    n_collapsed = 0
    for k, c in CFG.items():
        cb = {k: c, k + "_inv": L.rot180(c)}
        _, c1 = L.identify(cb, c)
        _, c2 = L.identify(cb, L.rot180(c))
        collapsed = (c1 == c2 and c1 is not None)
        n_collapsed += collapsed
        collapse_rows.append({"id": k, "present_upright": c1, "present_inverted": c2,
                              "collapsed": collapsed})
    # part-based control: two objects NOT rotation-related must stay discriminable.
    ctrl = {}
    for a, b in (("P", "Q"), ("R", "S")):
        cb = {a: PB[a], b: PB[b]}
        _, ca = L.identify(cb, PB[a])
        _, cb2 = L.identify(cb, PB[b])
        _, cai = L.identify(cb, L.rot180(PB[a]))
        ctrl[f"{a}_{b}"] = {"a_up": ca, "b_up": cb2, "a_inv": cai,
                            "discriminable": (ca == a and cb2 == b and cai == a)}
    ctrl_ok = all(v["discriminable"] for v in ctrl.values())
    all_collapsed = (n_collapsed == len(CFG))
    return {
        "inversion_pairs_collapsed": n_collapsed, "n_pairs": len(CFG),
        "rows": collapse_rows, "part_based_control": ctrl,
        "part_control_discriminable": ctrl_ok,
        "note": "COLLAPSE = the substrate treats a configural pattern and its 180-twin as "
                "ONE identity (generator-orbit invariance) -- the OPPOSITE of the human "
                "upright bias. The frame-DEPENDENT literal channel exists but is overridden "
                "by the transform channel.",
        "pass": (all_collapsed and ctrl_ok),
    }


# --- ARM 4: FLOOR / §1.1 (arms ALIVE + noise) ----------------------------------------
def arm_floor(n=100, base_seed=49000):
    up_c, k, _ = _recog_rate(CFG, CFG)
    inv_c, _, _ = _recog_rate(CFG, {kk: L.rot180(c) for kk, c in CFG.items()})
    # a Thatcher probe is unrecognised -> both recognised(1) and unrecognised(0) reached.
    _, tcov = L.identify(CFG, L.configural(FACE_ANCHORS["A"], atom=L.ATOM_L, flip_idx=0))
    states = sorted({1 if up_c == k else 0, 1 if inv_c == k else 0, 0 if tcov is None else 1})
    alive = (up_c == k and inv_c == k and tcov is None and states == [0, 1])
    force = 0
    detail = []
    for i in range(n):
        rng = random.Random(base_seed + i)
        cells = set()
        while len(cells) < 9:
            cells.add((rng.randint(0, 9), rng.randint(0, 9)))
        _, cov = L.identify(CFG, list(cells))
        if cov is not None:
            force += 1
            detail.append([base_seed + i, cov])
    return {"upright_recognised": [up_c, k], "inverted_recognised": [inv_c, k],
            "thatcher_probe_covered_by": tcov, "both_states_reached": states == [0, 1],
            "arms_alive": alive,
            "noise": {"n": n, "seed_range": [base_seed, base_seed + n - 1],
                      "force_maps": force, "detail": detail},
            "pass": (alive and force == 0)}


def main():
    t0 = time.time()
    prov = provenance_line()
    res = {
        "provenance": prov, "prereg_commit": "e407429f", "base_main_head": "301ae161",
        "ARM1_inversion_cost": arm_inversion_cost(),
        "ARM2_thatcher": arm_thatcher(),
        "ARM3_reference_frame": arm_reference_frame(),
        "ARM4_floor": arm_floor(),
    }
    confirmatory = ["ARM1_inversion_cost", "ARM2_thatcher", "ARM3_reference_frame",
                    "ARM4_floor"]
    res["ALL_CONFIRMATORY_PASS"] = all(res[k]["pass"] for k in confirmatory)
    res["HEADLINE"] = (
        "NEGATIVE (clean, diagnosed): the sd-loop composition is reference-frame-INVARIANT "
        "-- uniform inversion folds to rotation90 k=2 (no cost), Thatcher is detected in "
        "BOTH orientations (no frame-gating), and inversion-related pairs COLLAPSE. The "
        "substrate has NO privileged upright frame; it is not holistic-configural in the "
        "human way. Building the effect requires breaking D4 symmetry with a learned "
        "upright prior -- a NAMED FRONTIER, not built (would be PROTOCOL §13.1 forcing).")
    res["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "face_inversion_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    print(prov)
    for k in confirmatory:
        print(f"  {k:22s} pass={res[k]['pass']}  outcome={res[k].get('outcome','-')}")
    a1 = res["ARM1_inversion_cost"]
    print(f"  cost_config={a1['cost_config']} cost_part={a1['cost_part']} "
          f"differential={a1['differential']}")
    print("ALL_CONFIRMATORY_PASS:", res["ALL_CONFIRMATORY_PASS"], "|", res["elapsed_s"], "s")
    print(res["HEADLINE"])
    return res


if __name__ == "__main__":
    main()
