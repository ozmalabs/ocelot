#!/usr/bin/env python3
"""COLOUR IDENTITY — categorical colour as a MINTED, MDL-GATED SIGN (confirmatory run).

Pre-registration: VISION_COLOUR_IDENTITY_PREREG.md (committed BEFORE this run, §3).
Downstream of colour-salience (WHERE to look), this rung answers WHAT COLOUR IT IS:
a colour CATEGORY is a quantum minted from the opponent-colour VALUE subspace by the
sd loop's DYNAMIC-QUANTIZATION pattern, MDL-gated (mint where a colour value CLUSTERS
and compresses; refuse where it doesn't). The opponent recombination, the MDL-gated
minting and the nearest-quantum assignment are the vision_colour_identity RULES
(ci_opponent / ci_mint_category / ci_assign). This runner only CONSTRUCTS cone-cell
fields and READS the minted categories / per-cell signs back (mechanical I/O, §0),
and TALLIES metrics (incl. MDL) OVER them.

Run from the gamma-substrate dir:
    python scripts/colour_identity_measure.py
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
from domains import colour_identity_world as ciw  # noqa: E402

D_DIMS = 2  # chromatic opponent dims (rg, by); m_min = 3 falls out of this.


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_colour_identity"])
    return s, ag


def _grid(pat):
    """Lay a flat list of cone-specs onto a 6x6 grid with rrow,rcol."""
    cells = []
    for i, spec in enumerate(pat):
        d = dict(spec)
        d["rrow"], d["rcol"] = divmod(i, 6)
        cells.append(d)
    return cells


# Three clustered colours (exact opponent coords): A(10,0) B(-10,0) C(0,12)
A = dict(cL=15, cM=5, cS=20)
B = dict(cL=5, cM=15, cS=20)
C = dict(cL=10, cM=10, cS=32)


def _all_signs_correct(s, handle) -> bool:
    """Every cell's sign == its own colour at dist 0 (recognized as own category)."""
    for n in handle["region_ids"]:
        a = s.node(n)["attrs"]
        crg = round(float(a.get("crg", 0.0)))
        cby = round(float(a.get("cby", 0.0)))
        sr = round(float(a.get("sign_rg", 0.0)))
        sb = round(float(a.get("sign_by", 0.0)))
        sd = float(a.get("sign_dist", -1.0))
        if not (sr == crg and sb == cby and abs(sd) < 1e-9):
            return False
    return True


# ---- E: EMERGENCE / MDL --------------------------------------------------------
def arm_E():
    s, ag = _boot()
    cells = _grid([A] * 12 + [B] * 12 + [C] * 12)
    h = ciw.add_field(s, cells=cells)
    ciw.set_flag(s, identity=1.0)
    ciw.tick(s)
    cats = ciw.categories(s)
    n = len(cells)
    k = len(cats)
    n_assigned = sum(1 for sd in ciw.read_attr(s, h, "sign_dist") if sd >= 0.0)
    mdl_raw = n * D_DIMS
    mdl_cat = k * D_DIMS + n_assigned  # k prototypes (d ints each) + N labels
    expect = [{"crg": -10, "cby": 0, "members": 12},
              {"crg": 0, "cby": 12, "members": 12},
              {"crg": 10, "cby": 0, "members": 12}]
    passed = (k == 3 and cats == expect
              and _all_signs_correct(s, h) and mdl_cat < mdl_raw)
    return {"n_categories": k, "categories": cats, "n_assigned": n_assigned,
            "mdl_raw": mdl_raw, "mdl_categorized": mdl_cat,
            "mdl_ratio": round(mdl_raw / mdl_cat, 4),
            "all_signs_correct": _all_signs_correct(s, h), "pass": passed}


# ---- A: ASSIGNMENT (correct + nearest + recognize-not-remint) ------------------
def arm_A():
    # (a) already covered by arm_E all_signs_correct; re-confirm here.
    s, ag = _boot()
    h = ciw.add_field(s, cells=_grid([A] * 12 + [B] * 12 + [C] * 12))
    ciw.set_flag(s, identity=1.0); ciw.tick(s)
    a_correct = _all_signs_correct(s, h)

    # (b) NEAREST off-prototype: A x12, B x12, probe (6,0) closer to A.
    s, ag = _boot()
    h = ciw.add_field(s, cells=_grid([A] * 12 + [B] * 12))
    probe = ciw.add_region(s, h, dict(cL=13, cM=7, cS=20, rrow=5, rcol=0))  # rg=6
    ciw.set_flag(s, identity=1.0); ciw.tick(s)
    pa = s.node(probe)["attrs"]
    probe_sign = (round(float(pa["sign_rg"])), round(float(pa["sign_by"])))
    probe_dist = round(float(pa["sign_dist"]), 4)
    b_n_cats = ciw.n_categories(s)
    b_pass = (b_n_cats == 2 and probe_sign == (10, 0)
              and abs(probe_dist - 4.0) < 1e-6)

    # (c) RECOGNIZE not re-mint: 5xA -> 1 cat; add 6th A -> still 1 cat, recognized.
    s, ag = _boot()
    h = ciw.add_field(s, cells=[dict(cL=15, cM=5, cS=20, rrow=0, rcol=k)
                                for k in range(5)])
    ciw.set_flag(s, identity=1.0); ciw.tick(s)
    n_before = ciw.n_categories(s)
    new = ciw.add_region(s, h, dict(cL=15, cM=5, cS=20, rrow=1, rcol=0))
    ciw.tick(s)
    n_after = ciw.n_categories(s)
    na = s.node(new)["attrs"]
    new_sign = (round(float(na["sign_rg"])), round(float(na["sign_by"])))
    new_dist = float(na["sign_dist"])
    c_pass = (n_before == 1 and n_after == 1 and new_sign == (10, 0)
              and abs(new_dist) < 1e-9)

    return {"a_all_signs_correct": a_correct,
            "b_probe_sign": probe_sign, "b_probe_dist": probe_dist,
            "b_n_categories": b_n_cats, "b_pass": b_pass,
            "c_n_before": n_before, "c_n_after": n_after,
            "c_new_sign": new_sign, "c_new_dist": new_dist, "c_pass": c_pass,
            "pass": a_correct and b_pass and c_pass}


# ---- G: SMOOTH-GRADIENT FLOOR --------------------------------------------------
def arm_G():
    s, ag = _boot()
    cells = []
    for r in range(6):
        for c in range(6):
            cL = 10 + 3 * (6 * r + c)  # rg = 3*(6r+c), all 36 distinct; by=0
            cells.append(dict(cL=cL, cM=10, cS=10 + cL + 10, rrow=r, rcol=c))
    h = ciw.add_field(s, cells=cells)
    ciw.set_flag(s, identity=1.0); ciw.tick(s)
    k = ciw.n_categories(s)
    n_assigned = sum(1 for sd in ciw.read_attr(s, h, "sign_dist") if sd >= 0.0)
    distinct = len({(round(float(s.node(n)["attrs"]["crg"])),
                     round(float(s.node(n)["attrs"]["cby"]))) for n in h["region_ids"]})
    return {"n_categories": k, "n_assigned": n_assigned,
            "distinct_colours": distinct, "pass": (k == 0 and n_assigned == 0)}


# ---- N: COLOUR-NOISE FLOOR (n=100, seeds 35000-35099) --------------------------
def arm_N(n_seeds=100, base_seed=35000):
    false_mints = 0
    per_seed = []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        cells = []
        for r in range(6):
            for c in range(6):
                cells.append(dict(cL=rng.randint(0, 99), cM=rng.randint(0, 99),
                                  cS=rng.randint(0, 99), rrow=r, rcol=c))
        s, ag = _boot()
        h = ciw.add_field(s, cells=cells)
        ciw.set_flag(s, identity=1.0); ciw.tick(s)
        k = ciw.n_categories(s)
        if k > 0:
            false_mints += 1
            per_seed.append({"seed": seed, "n_categories": k,
                             "categories": ciw.categories(s)})
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "false_mint_fields": false_mints,
            "detail": per_seed, "pass": (false_mints == 0)}


# ---- D: DOWNSTREAM / LOAD-BEARING ----------------------------------------------
def arm_D():
    cells = _grid([A] * 12 + [B] * 12 + [C] * 12)
    # ON
    s, ag = _boot(); h = ciw.add_field(s, cells=cells)
    ciw.set_flag(s, identity=1.0); ciw.tick(s)
    on_cats = ciw.n_categories(s)
    on_sign = ciw.read_attr(s, h, "sign_rg")
    on_op = ciw.read_attr(s, h, "op_done")
    # OFF
    s, ag = _boot(); h = ciw.add_field(s, cells=cells)
    ciw.set_flag(s, identity=0.0); ciw.tick(s)
    off_cats = ciw.n_categories(s)
    off_sign = ciw.read_attr(s, h, "sign_rg")
    off_op = ciw.read_attr(s, h, "op_done")
    d_cats = abs(on_cats - off_cats)
    d_sign = max(abs(a - b) for a, b in zip(on_sign, off_sign))
    d_op = max(abs(a - b) for a, b in zip(on_op, off_op))
    return {"on_categories": on_cats, "off_categories": off_cats,
            "d_categories": d_cats, "d_sign_max": d_sign, "d_op_done_max": d_op,
            "pass": (d_cats > 0 and d_sign > 0 and d_op > 0)}


# ---- X: OFF-DAY ----------------------------------------------------------------
def arm_X():
    s, ag = _boot()
    h = ciw.add_field(s, cells=_grid([A] * 12 + [B] * 12 + [C] * 12))
    ciw.tick(s)  # flag left at default (identity=0)
    k = ciw.n_categories(s)
    max_op = max(ciw.read_attr(s, h, "op_done"))
    max_sign = max(abs(x) for x in ciw.read_attr(s, h, "sign_rg"))
    return {"n_categories": k, "max_op_done": max_op, "max_sign_rg": max_sign,
            "pass": (k == 0 and max_op == 0.0 and max_sign == 0.0)}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "d_dims": D_DIMS, "m_min": 3,
        "E_emergence": arm_E(),
        "A_assignment": arm_A(),
        "G_gradient_floor": arm_G(),
        "D_downstream": arm_D(),
        "X_offday": arm_X(),
        "N_noise_floor": arm_N(),
    }
    all_pass = all(results[k]["pass"] for k in results
                   if isinstance(results.get(k), dict) and "pass" in results[k])
    results["ALL_PASS"] = all_pass
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "colour_identity_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in ("E_emergence", "A_assignment", "G_gradient_floor", "D_downstream",
              "X_offday", "N_noise_floor"):
        print(f"  {k:20s} pass={results[k]['pass']}")
    print("ALL_PASS:", all_pass, "| wrote", out, "|", results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
