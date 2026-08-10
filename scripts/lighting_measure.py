#!/usr/bin/env python3
"""LIGHTING / APPEARANCE INVARIANCE (FRONTIER T3) — the illuminant as a discovered,
factored low-D CROSS-FRAME map (confirmatory run).

Pre-registration: VISION_LIGHTING_PREREG.md (committed BEFORE this run at feb65a57,
§3). The anchor, the in-class discovery, the MDL-gated mint, the anchor-relative
invariant and the raw baseline are the vision_lighting RULES (li_frame_stats /
li_inclass / li_mint / li_recognize / li_raw_recognize). This runner only CONSTRUCTS
reflectance × illuminant frames and READS the discovered illuminant / minted
identities / per-surface recognitions back (mechanical I/O, §0), TALLYING metrics
over them. The ground-truth `material` is used ONLY here for scoring — NEVER read by
a seed rule.

Run from the gamma-substrate dir:
    python scripts/lighting_measure.py
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
from domains import lighting_world as lw  # noqa: E402

D_CONE = 3   # cone-coordinate dimensionality; m_min = 2 falls out of this (§13).
M_MIN = 2

# --- the six materials (reflectances). Two patches each => members = 2 = m_min. ---
MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
# A material present in BOTH frames but with only ONE patch, so members = 1 < m_min
# and NO identity is minted for it. Keeping it in both frames preserves the shared
# surface set (so the in-class test still holds) — it is the "different object" floor.
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}

REF_GAIN = (1, 1, 1)
TEST_GAINS = [(2, 2, 2), (3, 2, 4), (5, 7, 3)]   # integer diagonal illuminants


def _reflectances(include_novel: bool = True) -> list[dict]:
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting"])
    return s, ag


def _run_pair(gain, *, ref_gain=REF_GAIN, include_novel=True, flag=1.0,
              reflectances=None, link=True):
    """Boot, build a reference frame + a test frame under `gain`, tick. Mechanical."""
    refl = _reflectances(include_novel) if reflectances is None else reflectances
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=ref_gain, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=gain, start_sidx=1000)
    if link:
        lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.tick(s)
    return s, ref, test


def _expected_key(s, ref, material_name: str) -> int:
    """The sid_key the identity for `material_name` was minted with — read from the
    REFERENCE frame's own surfaces (mechanical bookkeeping, not a decision)."""
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        if meta["name"] == material_name:
            return int(lw.surf_attr(s, nid, "sidx"))
    return -1


# ---- A: INVARIANCE (entailed by the algebra — reported as consistency) --------
def arm_invariance():
    per_gain = {}
    correct = 0
    total = 0
    for gain in TEST_GAINS:
        s, ref, test = _run_pair(gain)
        rows = []
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] == NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            exp = _expected_key(s, ref, meta["name"])
            ok = (r["lit_recognized"] == 1 and r["lit_id"] == exp)
            correct += ok
            total += 1
            rows.append({"material": meta["name"], "lit_recognized":
                         r["lit_recognized"], "lit_id": r["lit_id"],
                         "expected_id": exp, "ok": ok})
        per_gain[str(gain)] = {"inclass": lw.frame_attr(s, test, "illum_inclass"),
                               "n_identities": lw.n_identities(s),
                               "surfaces": rows}
    # 6 materials x 2 patches x 3 gains = 36 presentations
    return {"per_gain": per_gain, "correct": correct, "total": total,
            "pass": correct == total and total == 2 * len(MATERIALS) * len(TEST_GAINS)}


# ---- B: DISCRIMINATION exact-0 (RISKED — the §1.1 universal-container crux) ----
def arm_discrimination():
    cross_false = 0
    detail = []
    for gain in TEST_GAINS:
        s, ref, test = _run_pair(gain)
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] == NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            exp = _expected_key(s, ref, meta["name"])
            if r["lit_recognized"] == 1 and r["lit_id"] != exp:
                cross_false += 1
                detail.append({"gain": list(gain), "material": meta["name"],
                               "got": r["lit_id"], "expected": exp})
    return {"cross_false": cross_false, "detail": detail, "pass": cross_false == 0}


# ---- C: ILLUMINANT-FACTORED vs the RAW baseline --------------------------------
def arm_factored_vs_raw():
    per_gain = {}
    raw_correct = lit_correct = total = 0
    for gain in TEST_GAINS:
        s, ref, test = _run_pair(gain)
        rc = lc = t = 0
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] == NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            exp = _expected_key(s, ref, meta["name"])
            rc += (r["raw_recognized"] == 1 and r["raw_id"] == exp)
            lc += (r["lit_recognized"] == 1 and r["lit_id"] == exp)
            t += 1
        per_gain[str(gain)] = {"raw_correct": rc, "lit_correct": lc, "n": t}
        raw_correct += rc; lit_correct += lc; total += t
    return {"per_gain": per_gain, "raw_correct": raw_correct,
            "lit_correct": lit_correct, "total": total,
            "pass": raw_correct < lit_correct and lit_correct == total}


# ---- D: OUT-OF-CLASS REFUSAL (RISKED) ------------------------------------------
def arm_out_of_class(n_scenes=20, base_seed=45200):
    """A SPATIALLY-VARYING illuminant (an independent gain per surface) is OUTSIDE
    the diagonal class. The mechanism must REFUSE, never force-match."""
    inclass_fired = 0
    false_ids = 0
    per = []
    refl = _reflectances(include_novel=False)
    for i in range(n_scenes):
        rng = random.Random(base_seed + i)
        gains = [(rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6))
                 for _ in refl]
        s, ag = _boot()
        ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                           start_sidx=0)
        test = lw.add_frame(s, reflectances=refl, gain=gains, start_sidx=1000)
        lw.link_reference(s, test, ref)
        lw.set_flag(s, lighting=1.0)
        lw.tick(s)
        ic = lw.frame_attr(s, test, "illum_inclass")
        fi = sum(int(lw.surf_attr(s, n, "lit_recognized"))
                 for n in test["surface_ids"])
        inclass_fired += int(ic > 0.5)
        false_ids += fi
        per.append({"seed": base_seed + i, "inclass": ic, "false_ids": fi})
    return {"n_scenes": n_scenes, "seed_range": [base_seed, base_seed + n_scenes - 1],
            "inclass_fired": inclass_fired, "false_identities": false_ids,
            "detail": per, "pass": inclass_fired == 0 and false_ids == 0}


# ---- E: DIFFERENT-OBJECT floor (RISKED) ----------------------------------------
def arm_floor_novel():
    """The NOVEL material (present in both frames, one patch => never minted) must be
    REFUSED under an in-class illuminant, not force-matched to a held identity."""
    per_gain = {}
    forced = 0
    for gain in TEST_GAINS:
        s, ref, test = _run_pair(gain)
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] != NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            forced += r["lit_recognized"]
            per_gain[str(gain)] = {"recognition": r,
                                   "inclass": lw.frame_attr(s, test,
                                                            "illum_inclass")}
    return {"per_gain": per_gain, "forced_matches": forced, "pass": forced == 0}


# ---- F: NOISE floor (RISKED, n=100, seeds 45000-45099) -------------------------
def arm_floor_noise(n_seeds=100, base_seed=45000):
    """iid random cone fields: no identity should mint and no cross-frame identity
    should be claimed."""
    bad = 0
    per = []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        refl = [{"name": f"n{j}", "rL": rng.randint(1, 99), "rM": rng.randint(1, 99),
                 "rS": rng.randint(1, 99)} for j in range(13)]
        s, ag = _boot()
        ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                           start_sidx=0)
        test = lw.add_frame(s, reflectances=refl, gain=(3, 2, 4), start_sidx=1000)
        lw.link_reference(s, test, ref)
        lw.set_flag(s, lighting=1.0)
        lw.tick(s)
        k = lw.n_identities(s)
        claims = sum(int(lw.surf_attr(s, n, "lit_recognized"))
                     for n in test["surface_ids"])
        if k > 0 or claims > 0:
            bad += 1
            per.append({"seed": seed, "n_identities": k, "claims": claims})
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "bad_fields": bad, "detail": per, "pass": bad == 0}


# ---- G: DOWNSTREAM / load-bearing (§13.2) --------------------------------------
def arm_downstream():
    on_s, on_ref, on_t = _run_pair((3, 2, 4), flag=1.0)
    off_s, off_ref, off_t = _run_pair((3, 2, 4), flag=0.0)
    on_rec = [lw.surf_attr(on_s, n, "lit_recognized") for n in on_t["surface_ids"]]
    off_rec = [lw.surf_attr(off_s, n, "lit_recognized") for n in off_t["surface_ids"]]
    d_rec = max(abs(a - b) for a, b in zip(on_rec, off_rec))
    d_ident = abs(lw.n_identities(on_s) - lw.n_identities(off_s))
    d_inclass = abs(lw.frame_attr(on_s, on_t, "illum_inclass")
                    - lw.frame_attr(off_s, off_t, "illum_inclass"))
    return {"on_identities": lw.n_identities(on_s),
            "off_identities": lw.n_identities(off_s),
            "d_identities": d_ident, "d_recognized_max": d_rec,
            "d_inclass": d_inclass,
            "pass": d_ident > 0 and d_rec > 0 and d_inclass > 0}


# ---- X: OFF-DAY (§9) -----------------------------------------------------------
def arm_offday():
    """Flag left at its DEFAULT (0) — the seed must be completely inert."""
    refl = _reflectances()
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=(3, 2, 4), start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.tick(s)   # flag NEVER written — default 0
    return {"n_identities": lw.n_identities(s), "n_illuminants": lw.n_illuminants(s),
            "max_lit_recognized": max(lw.surf_attr(s, n, "lit_recognized")
                                      for n in test["surface_ids"]),
            "max_inclass": lw.frame_attr(s, test, "illum_inclass"),
            "max_stats_done": lw.frame_attr(s, test, "stats_done"),
            "pass": (lw.n_identities(s) == 0 and lw.n_illuminants(s) == 0
                     and max(lw.surf_attr(s, n, "lit_recognized")
                             for n in test["surface_ids"]) == 0.0
                     and lw.frame_attr(s, test, "illum_inclass") == 0.0)}


# ---- L1: the INTRINSIC ill-posedness (REPORTED, not gated) ---------------------
def probe_global_scale_ambiguity():
    """Scaling EVERY reflectance by a constant is INDISTINGUISHABLE from a dimmer
    illuminant — the anchor scales with it. Predicted: identical identities. That is
    CORRECT for this class, and is the identifiability bound, not a failure."""
    refl = _reflectances(include_novel=False)
    scaled = [{**m, "rL": m["rL"] * 2, "rM": m["rM"] * 2, "rS": m["rS"] * 2}
              for m in refl]
    s1, ref1, t1 = _run_pair((3, 2, 4), reflectances=refl)
    s2, ref2, t2 = _run_pair((3, 2, 4), reflectances=scaled)
    rec1 = [lw.recognition(s1, n)["lit_recognized"] for n in t1["surface_ids"]]
    rec2 = [lw.recognition(s2, n)["lit_recognized"] for n in t2["surface_ids"]]
    return {"identities_unscaled": lw.n_identities(s1),
            "identities_scaled": lw.n_identities(s2),
            "recognition_unscaled": rec1, "recognition_scaled": rec2,
            "indistinguishable": rec1 == rec2,
            "note": ("a global reflectance scale and a global illuminant change are "
                     "the SAME observation — intrinsic ill-posedness of the class, "
                     "REPORTED not gated")}


# ---- L2: the RESOLUTION bound (REPORTED, not gated) ----------------------------
def probe_real_gain_resolution():
    """A REAL-valued gain renders through round(), so exact cross-multiplication can
    miss. Reported to show the bound FALLS OUT of the observation resolution — NO
    tolerance is added to rescue it (§5)."""
    refl = _reflectances(include_novel=False)
    rows = []
    for g in [1.5, 2.0, 2.5, 3.0, 3.3, 4.0, 7.5]:
        s, ag = _boot()
        ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                           start_sidx=0)
        # RENDER with a real gain, rounded to the integer lattice (world physics).
        frame = s.add_node("LightFrame", {
            "is_reference": 0.0, "stats_done": 0.0, "illum_inclass": 0.0,
            "aL": 0.0, "aM": 0.0, "aS": 0.0, "sL": 0.0, "sM": 0.0, "sS": 0.0})
        test = {"frame": frame, "surface_ids": [], "next_sidx": 1000, "meta": []}
        for m in refl:
            n = s.add_node("ObjSurface", {
                "cL": float(round(m["rL"] * g)), "cM": float(round(m["rM"] * g)),
                "cS": float(round(m["rS"] * g)), "sidx": float(test["next_sidx"]),
                "lit_recognized": 0.0, "lit_id": -1.0,
                "raw_recognized": 0.0, "raw_id": -1.0})
            test["next_sidx"] += 1
            s.add_edge_unchecked(frame, "has_surface", n)
            test["surface_ids"].append(n)
            test["meta"].append(dict(m))
        s.add_edge_unchecked(frame, "compares_to", ref["frame"])
        lw.set_flag(s, lighting=1.0)
        lw.tick(s)
        rows.append({"gain": g, "integer_gain": float(g).is_integer(),
                     "inclass": lw.frame_attr(s, test, "illum_inclass"),
                     "recognized": sum(int(lw.surf_attr(s, n, "lit_recognized"))
                                       for n in test["surface_ids"]),
                     "n": len(test["surface_ids"])})
    return {"rows": rows,
            "note": ("exact integer cross-multiplication + a rounded real gain: the "
                     "identifiability bound falls out of the observation RESOLUTION, "
                     "not from a tuned tolerance. No tolerance added (§5).")}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "d_cone": D_CONE, "m_min": M_MIN,
        "materials": MATERIALS, "novel": NOVEL,
        "ref_gain": list(REF_GAIN), "test_gains": [list(g) for g in TEST_GAINS],
        "A_invariance": arm_invariance(),
        "B_discrimination": arm_discrimination(),
        "C_factored_vs_raw": arm_factored_vs_raw(),
        "D_out_of_class": arm_out_of_class(),
        "E_floor_novel_material": arm_floor_novel(),
        "G_downstream": arm_downstream(),
        "X_offday": arm_offday(),
        "F_floor_noise": arm_floor_noise(),
        "L1_global_scale_ambiguity": probe_global_scale_ambiguity(),
        "L2_resolution_bound": probe_real_gain_resolution(),
    }
    arm_keys = [k for k in results
                if isinstance(results.get(k), dict) and "pass" in results[k]]
    all_pass = all(results[k]["pass"] for k in arm_keys)
    results["ALL_PASS"] = all_pass
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "lighting_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in arm_keys:
        print(f"  {k:28s} pass={results[k]['pass']}")
    print("ALL_PASS:", all_pass, "| wrote", out, "|", results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
