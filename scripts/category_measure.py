#!/usr/bin/env python3
"""CATEGORY-LEVEL RECOGNITION (FRONTIER T2) — a category as an MDL-minted
AXIS-CODEBOOK region (confirmatory run).

Pre-registration: VISION_CATEGORY_PREREG.md (committed BEFORE this run, §3).
Category recognition is generalization to a KIND: a NEW instance never seen before,
recognized as a member of a known category by its PROJECTION falling into a held
category subspace. The MDL-gated minting, the region box, the containment
recognition and the memorization control are the vision_category RULES (cat_mint /
cat_recognize / cat_memorize). This runner only CONSTRUCTS ObjItem axis-coordinate
fields, builds a real TRAIN/TEST split, and READS the minted categories / per-item
recognitions back (mechanical I/O, §0), TALLYING metrics OVER them. The ground-truth
`kind` is used ONLY here for the split and scoring — NEVER read by a seed rule.

Run from the gamma-substrate dir:
    python scripts/category_measure.py
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
from domains import category_world as cw  # noqa: E402

D_DISC = 2   # discrete-signature dims; m_min = 3 falls out of this.
M_MIN = 3

# --- the three kinds: (d0,d1) signature + a box of TRAINING corners ------------
#   A chair/table/stool analogue: a shared discrete part-signature, continuous
#   proportions that VARY within a kind. Training members are the box CORNERS; the
#   held-out test instance is a box INTERIOR point (never a training coordinate).
KINDS = {
    "A": {"sig": (1, 1), "v0": (10, 20), "v1": (30, 40), "held": (15, 35)},
    "B": {"sig": (2, 1), "v0": (50, 60), "v1": (30, 40), "held": (55, 35)},
    "C": {"sig": (1, 2), "v0": (10, 20), "v1": (70, 80), "held": (15, 75)},
}


def _train_items() -> list[dict]:
    """The box-corner training members of every kind (4 per kind)."""
    items = []
    for name, k in KINDS.items():
        (d0, d1) = k["sig"]
        for a in k["v0"]:
            for b in k["v1"]:
                items.append(dict(d0=d0, d1=d1, v0=a, v1=b, kind=name))
    return items


def _train_coords(kind: str) -> set:
    k = KINDS[kind]
    return {(a, b) for a in k["v0"] for b in k["v1"]}


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_category"])
    return s, ag


def _mint_scene():
    """Boot, add TRAINING items, tick to mint the categories. Returns (s, handle)."""
    s, ag = _boot()
    h = cw.add_field(s, items=_train_items())
    cw.set_flag(s, identity=1.0)
    cw.tick(s)
    return s, h


# ---- G: GENERALIZATION (headline) ---------------------------------------------
def arm_generalization():
    s, h = _mint_scene()
    held = {}
    for name, k in KINDS.items():
        nid = cw.add_obj(s, h, dict(d0=k["sig"][0], d1=k["sig"][1],
                                    v0=k["held"][0], v1=k["held"][1], kind=name))
        held[name] = nid
    cw.tick(s)
    per = {}
    gen_correct = 0
    for name, nid in held.items():
        r = cw.recognition(s, nid)
        coord_unseen = (r["v0"], r["v1"]) not in _train_coords(name)
        correct = (r["cat_recognized"] == 1
                   and (r["cat_sig0"], r["cat_sig1"]) == KINDS[name]["sig"]
                   and coord_unseen)
        if correct:
            gen_correct += 1
        per[name] = {**r, "coord_unseen": coord_unseen, "correct": correct}
    passed = gen_correct == len(KINDS)
    return {"held_out": per, "gen_correct": gen_correct, "K": len(KINDS),
            "pass": passed}


# ---- B: DISCRIMINATION exact-0 ------------------------------------------------
def arm_discrimination():
    s, h = _mint_scene()
    held = {name: cw.add_obj(s, h, dict(d0=k["sig"][0], d1=k["sig"][1],
                                        v0=k["held"][0], v1=k["held"][1], kind=name))
            for name, k in KINDS.items()}
    cw.tick(s)
    # A held-out is recognized as its OWN kind's signature only. Count any held-out
    # whose recognized signature belongs to a DIFFERENT kind.
    cross_false = 0
    detail = {}
    for name, nid in held.items():
        r = cw.recognition(s, nid)
        rec_sig = (r["cat_sig0"], r["cat_sig1"])
        wrong = (r["cat_recognized"] == 1 and rec_sig != KINDS[name]["sig"])
        if wrong:
            cross_false += 1
        detail[name] = {"recognized_sig": rec_sig, "own_sig": list(KINDS[name]["sig"]),
                        "cross_false": wrong}
    return {"detail": detail, "cross_false": cross_false, "pass": cross_false == 0}


# ---- C: THE CRUX — generalization vs memorization -----------------------------
def arm_crux():
    s, h = _mint_scene()
    held = {name: cw.add_obj(s, h, dict(d0=k["sig"][0], d1=k["sig"][1],
                                        v0=k["held"][0], v1=k["held"][1], kind=name))
            for name, k in KINDS.items()}
    cw.tick(s)
    sum_mem = 0
    sum_cat = 0
    per = {}
    for name, nid in held.items():
        r = cw.recognition(s, nid)
        sum_mem += r["mem_recognized"]
        sum_cat += r["cat_recognized"]
        per[name] = {"mem_recognized": r["mem_recognized"],
                     "cat_recognized": r["cat_recognized"]}
    # Region GENERALIZES (all held-out recognized) while exact-match MEMORIZATION
    # REFUSES all held-out (never-seen coords): (sum_mem, sum_cat) == (0, K).
    passed = (sum_mem == 0 and sum_cat == len(KINDS))
    return {"per_kind": per, "sum_mem_recognized": sum_mem,
            "sum_cat_recognized": sum_cat, "K": len(KINDS), "pass": passed}


# ---- D: MDL -------------------------------------------------------------------
def arm_mdl():
    s, h = _mint_scene()
    k = cw.n_categories(s)
    n = len(_train_items())
    mdl_raw = D_DISC * n                 # each member carries its d_disc signature
    mdl_categorized = D_DISC * k + n     # signature stored once/category + 1 label/member
    passed = (k == len(KINDS) and mdl_categorized < mdl_raw)
    return {"n_categories": k, "n_train": n, "mdl_raw": mdl_raw,
            "mdl_categorized": mdl_categorized,
            "mdl_ratio": round(mdl_raw / mdl_categorized, 4),
            "m_min": M_MIN, "d_disc": D_DISC, "pass": passed}


# ---- E: FLOORS ----------------------------------------------------------------
def arm_floor_noise(n_seeds=100, base_seed=44000):
    """(a) iid-noise fields (no shared signature) mint ZERO categories."""
    false_mints = 0
    per_seed = []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        items = []
        for _ in range(36):
            items.append(dict(d0=rng.randint(0, 99), d1=rng.randint(0, 99),
                              v0=rng.randint(0, 99), v1=rng.randint(0, 99)))
        s, ag = _boot()
        cw.add_field(s, items=items)
        cw.set_flag(s, identity=1.0)
        cw.tick(s)
        kk = cw.n_categories(s)
        if kk > 0:
            false_mints += 1
            per_seed.append({"seed": seed, "n_categories": kk,
                             "categories": cw.categories(s)})
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "false_mint_fields": false_mints, "detail": per_seed,
            "pass": false_mints == 0}


def arm_floor_novel():
    """(b) a held-out with a NOVEL discrete signature is REFUSED."""
    s, h = _mint_scene()
    nid = cw.add_obj(s, h, dict(d0=9, d1=9, v0=15, v1=35))  # signature never trained
    cw.tick(s)
    r = cw.recognition(s, nid)
    return {"recognition": r, "pass": r["cat_recognized"] == 0}


def arm_floor_extrapolation():
    """(c) a held-out with a matching signature but OUT-OF-BOX proportions is
    REFUSED — the box is LOAD-BEARING (§13.2)."""
    s, h = _mint_scene()
    # kind A signature, coords far outside A's box [10,20]x[30,40]:
    nid = cw.add_obj(s, h, dict(d0=1, d1=1, v0=100, v1=100))
    cw.tick(s)
    r = cw.recognition(s, nid)
    return {"recognition": r, "pass": r["cat_recognized"] == 0}


# ---- F: DOWNSTREAM / LOAD-BEARING ---------------------------------------------
def arm_downstream():
    train = _train_items()
    # ON
    s, ag = _boot(); h = cw.add_field(s, items=train)
    cw.set_flag(s, identity=1.0); cw.tick(s)
    on_cats = cw.n_categories(s)
    on_rec = [cw.obj_attr(s, n, "cat_recognized") for n in h["item_ids"]]
    # OFF
    s, ag = _boot(); h = cw.add_field(s, items=train)
    cw.set_flag(s, identity=0.0); cw.tick(s)
    off_cats = cw.n_categories(s)
    off_rec = [cw.obj_attr(s, n, "cat_recognized") for n in h["item_ids"]]
    d_categories = abs(on_cats - off_cats)
    d_recognized = max(abs(a - b) for a, b in zip(on_rec, off_rec))
    return {"on_categories": on_cats, "off_categories": off_cats,
            "d_categories": d_categories, "d_recognized_max": d_recognized,
            "pass": d_categories > 0 and d_recognized > 0}


# ---- X: OFF-DAY ---------------------------------------------------------------
def arm_offday():
    s, ag = _boot()
    h = cw.add_field(s, items=_train_items())
    cw.tick(s)  # flag left at default (identity=0)
    k = cw.n_categories(s)
    max_rec = max(cw.obj_attr(s, n, "cat_recognized") for n in h["item_ids"])
    max_mem = max(cw.obj_attr(s, n, "mem_recognized") for n in h["item_ids"])
    return {"n_categories": k, "max_cat_recognized": max_rec,
            "max_mem_recognized": max_mem,
            "pass": k == 0 and max_rec == 0.0 and max_mem == 0.0}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "d_disc": D_DISC, "m_min": M_MIN,
        "G_generalization": arm_generalization(),
        "B_discrimination": arm_discrimination(),
        "C_crux_memorization": arm_crux(),
        "D_mdl": arm_mdl(),
        "E_floor_novel_signature": arm_floor_novel(),
        "E_floor_extrapolation": arm_floor_extrapolation(),
        "F_downstream": arm_downstream(),
        "X_offday": arm_offday(),
        "E_floor_noise": arm_floor_noise(),
    }
    arm_keys = [k for k in results
                if isinstance(results.get(k), dict) and "pass" in results[k]]
    all_pass = all(results[k]["pass"] for k in arm_keys)
    results["ALL_PASS"] = all_pass
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "category_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in arm_keys:
        print(f"  {k:26s} pass={results[k]['pass']}")
    print("ALL_PASS:", all_pass, "| wrote", out, "|", results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
