#!/usr/bin/env python3
"""RUNG L1b — THE UNIQUENESS GATE for the SILENT-ARGMIN HAZARD (confirmatory run).

Pre-registration: VISION_UNIQUENESS_PREREG.md (committed BEFORE this run at
8015d690, §3). Two parts:

  PART A — THE AUDIT. Across the already-merged codebook rungs, does a regime exist
  where ≥2 candidates fall inside the verdict bound and the Argmin picks silently?
  The exposing stimulus is CONSTRUCTED per rung (dimming / native-resolution /
  degenerate / equidistant). Reported even if part B fails.

  PART B — THE GATE. Recognition REFUSES when ≥2 candidates lie within the bound.
  Every DECISION is a `vision_uniqueness` seed RULE (uq_admit / uq_refuse_ambiguous);
  this runner only CONSTRUCTS scenes, sets the flag, and READS attrs back, TALLYING
  over them (mechanical I/O, §0). The ground-truth material name is used ONLY here
  for scoring — NEVER read by a seed rule.

Both verdicts are read from the SAME graph in the SAME run — L1's ungated `l1_*` and
the gated `uq_*` — which is what makes the comparison a measurement.

Run from the gamma-substrate dir:
    python scripts/uniqueness_measure.py
"""
from __future__ import annotations
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402
from domains import uniqueness_world as uw  # noqa: E402
from tools.term_ast_audit import audit_seed_file  # noqa: E402

LATTICE_STEP = 1.0     # L1's falls-out bound, INHERITED (not a new number)

MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}
REF_GAIN = (1.0, 1.0, 1.0)

# The 5 REAL gains L1 recognized 60/60 — the UNAMBIGUOUS regime (arm C).
REAL_GAINS = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
              (1.5, 2.5, 3.3)]
# The dimming gains at/below L1's measured resolution floor — the AMBIGUOUS regime.
FLOOR_GAINS = [0.06, 0.05, 0.04]
# Gains ABOVE the floor, where L1 was correct — the control half of arm A.
CLEAN_DIM_GAINS = [0.2, 0.1, 0.08]

NOISE_BASE, NOISE_N = 45340, 100          # ledger block consumed by this rung


def _reflectances(include_novel: bool = True) -> list[dict]:
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _run_pair(gain, *, reflectances=None, include_novel=True, uniqueness=1.0):
    """Boot L1 + the gate, build reference + test frames, tick. Mechanical."""
    refl = _reflectances(include_novel) if reflectances is None else reflectances
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1",
                            "vision_uniqueness"])
    ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=gain, start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=1.0)
    lw.set_flag_l1(s, lighting_l1=1.0)
    uw.set_flag(s, uniqueness=uniqueness)
    lw.tick(s)
    return s, ref, test


def _expected_key(s, ref, material_name: str) -> int:
    """The sid_key the identity for `material_name` was minted with. Bookkeeping."""
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        if meta["name"] == material_name:
            return int(lw.surf_attr(s, nid, "sidx"))
    return -1


def _score(s, ref, test):
    """Per-surface scoring of BOTH arms — L1's ungated `l1_*` and the gated `uq_*` —
    off the SAME nodes in the SAME graph. Mechanical tally, no decision."""
    rows = dict(n=0, l1_correct=0, l1_false=0, l1_refused=0,
                uq_correct=0, uq_false=0, uq_ambiguous=0, detail=[])
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        r = lw.recognition(s, nid)
        v = uw.verdict(s, nid)
        exp = _expected_key(s, ref, meta["name"])
        rows["n"] += 1
        rows["l1_correct"] += int(r["l1_recognized"] == 1 and r["l1_id"] == exp)
        rows["l1_false"] += int(r["l1_recognized"] == 1 and r["l1_id"] != exp)
        rows["l1_refused"] += int(r["l1_recognized"] != 1)
        rows["uq_correct"] += int(v["uq_recognized"] == 1 and v["uq_id"] == exp)
        rows["uq_false"] += int(v["uq_recognized"] == 1 and v["uq_id"] != exp)
        rows["uq_ambiguous"] += int(v["uq_status"] == "uq_ambiguous")
        rows["detail"].append({
            "material": meta["name"], "expected_id": exp,
            "l1_recognized": r["l1_recognized"], "l1_id": r["l1_id"],
            "l1_resid": round(r["l1_resid"], 6), "l1_status": r["l1_status"],
            "uq_recognized": v["uq_recognized"], "uq_id": v["uq_id"],
            "uq_status": v["uq_status"], "uq_ncand": v["uq_ncand"]})
    return rows


# ================================================================================
# PART A — THE AUDIT
# ================================================================================

def audit_l1():
    """L1 lighting: Argmin over Neighbours(ref,'has_identity') under an Lte bound.
    The exposing stimulus is DIMMING, where the lattice loses resolution."""
    per = {}
    for g in CLEAN_DIM_GAINS + FLOOR_GAINS:
        s, ref, test = _run_pair((g, g, g), uniqueness=0.0)   # PRE-GATE reading
        sc = _score(s, ref, test)
        multi = sum(1 for d in sc["detail"]
                    if _count_in_bound(s, ref, test, d["material"]) >= 2)
        maxc = max((_count_in_bound(s, ref, test, d["material"])
                    for d in sc["detail"]), default=0)
        per[str(g)] = {"n": sc["n"], "correct": sc["l1_correct"],
                       "false_ids": sc["l1_false"], "refused": sc["l1_refused"],
                       "rows_with_ge2_candidates": multi, "max_candidates": maxc}
    exposed = any(v["false_ids"] > 0 and v["rows_with_ge2_candidates"] > 0
                  for v in per.values())
    return {"rung": "L1 lighting (l1_recognize)", "per_gain": per,
            "EXPOSED": exposed}


def _count_in_bound(s, ref, test, material_name: str) -> int:
    """How many held identities render to within ONE LATTICE STEP of this surface.

    A mechanical re-read of graph values for the AUDIT tally (the gate itself
    computes this in the seed rule, via Count(Filter(...))). Arithmetic over read
    attrs is scoring, not a percept decision."""
    ids = lw.identities(s)
    a = {k: float(s.node(test["frame"])["attrs"].get(k, 0.0))
         for k in ("l1_aL", "l1_aM", "l1_aS")}
    n = 0
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] != material_name:
            continue
        r = lw.recognition(s, nid)
        n = sum(1 for c in ids
                if max(abs(r["c" + ch] - c["p" + ch] * (a["l1_a" + ch] / c["pa" + ch]))
                       for ch in "LMS") <= LATTICE_STEP)
        break
    return n


def audit_continuous_pose():
    """T1 continuous pose: Argmin over NodesOfType(ShapeSignature) under Lte(√2/2).
    The exposing stimulus is the NATIVE 5-cell resolution (s=1), where T1 itself
    reported 22/63 wrong-merges; s=4 is its clean headline regime."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import continuous_pose_measure as cpm
    bound = math.sqrt(2) / 2
    resid = {"type": "MinOver", "source": {"type": "Var", "name": "angles"},
             "var_name": "t",
             "value": {"type": "PointSetDist",
                       "a": {"type": "MapList", "source": {"type": "Var", "name": "cpts"},
                             "var_name": "p",
                             "value": {"type": "Rotate", "vec": {"type": "Var", "name": "p"},
                                       "angle": {"type": "Var", "name": "t"}}},
                       "b": {"type": "Var", "name": "opts"}},
             "default": None}
    per = {}
    for scale in (1, 2, 4):
        s, ag, native = cpm._boot(scale)
        n = wrong = multi = wrong_multi = 0
        wins, runs, counts = [], [], []
        for nm in cpm.NAMES:
            for deg in range(5, 90, 10):
                obs = cpm.observe(cpm.OBJ[nm], scale, deg)
                st, cov = cpm.cp_identify(s, ag, native, obs)
                rs = sorted((float(native.evaluate(
                    resid, {"angles": cpm.GRID,
                            "cpts": cpm.dense(cpm.OBJ[c], scale), "opts": obs})), c)
                    for c in cpm.NAMES)
                k = sum(1 for r, _ in rs if r <= bound)
                w = int(st == "recognized_continuous" and cov != nm)
                n += 1
                wrong += w
                multi += int(k >= 2)
                wrong_multi += int(w and k >= 2)
                wins.append(rs[0][0])
                runs.append(rs[1][0])
                counts.append(k)
        per[f"s={scale}"] = {
            "n": n, "wrong_ids": wrong, "rows_with_ge2_candidates": multi,
            "wrong_AND_ge2": wrong_multi,
            "min_candidates_in_bound": min(counts),
            "median_candidates_in_bound": sorted(counts)[len(counts) // 2],
            "max_candidates_in_bound": max(counts),
            "winner_median": round(sorted(wins)[len(wins) // 2], 4),
            "runnerup_median": round(sorted(runs)[len(runs) // 2], 4),
            "margin_median": round(sorted(runs)[len(runs) // 2]
                                   - sorted(wins)[len(wins) // 2], 4)}
    return {"rung": "T1 continuous pose (cp_recognize)", "bound": round(bound, 6),
            "per_resolution": per, "EXPOSED": per["s=1"]["wrong_AND_ge2"] > 0,
            "COUNT_GATE_TRANSFERS": per["s=4"]["min_candidates_in_bound"] < 2}


def audit_category():
    """T2 category: `cat_recognize` is an Exists over an ObjCategory REGION BOX with
    an EXACT discrete-signature equality — there is NO Argmin and NO identity is
    assigned from the codebook. The exposing stimulus attempted here is DEGENERATE:
    two kinds SHARING a signature with OVERLAPPING boxes."""
    from domains import category_world as cw

    def run(items, probe):
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_category"])
        h = cw.add_field(s, items=items)
        cw.set_flag(s, identity=1.0)
        cw.tick(s)
        cats = [{k: float(s.node(c)["attrs"].get(k, 0.0))
                 for k in ("d0", "d1", "v0lo", "v0hi", "v1lo", "v1hi", "members")}
                for c in s.nodes("ObjCategory")]
        h2 = cw.add_field(s, items=[probe])
        cw.tick(s)
        rec = float(s.node(h2["item_ids"][0])["attrs"].get("cat_recognized", 0.0))
        matching = [c for c in cats
                    if c["d0"] == probe["d0"] and c["d1"] == probe["d1"]
                    and c["v0lo"] <= probe["v0"] <= c["v0hi"]
                    and c["v1lo"] <= probe["v1"] <= c["v1hi"]]
        return {"n_categories": len(cats), "cat_recognized": rec,
                "matching_categories": len(matching)}

    base = [dict(d0=sg[0], d1=sg[1], v0=a, v1=b, kind=nm)
            for sg, v0s, v1s, nm in [((1, 1), (10, 20), (30, 40), "A"),
                                     ((2, 1), (50, 60), (30, 40), "B"),
                                     ((1, 2), (10, 20), (70, 80), "C")]
            for a in v0s for b in v1s]
    deg = [dict(d0=1, d1=1, v0=a, v1=b, kind=nm)
           for v0s, v1s, nm in [((10, 20), (30, 40), "P"), ((15, 25), (35, 45), "Q")]
           for a in v0s for b in v1s]
    baseline = run(base, dict(d0=1, d1=1, v0=15, v1=35, kind="A"))
    degenerate = run(deg, dict(d0=1, d1=1, v0=18, v1=38, kind="?"))
    return {"rung": "T2 category (cat_recognize)", "baseline": baseline,
            "degenerate_shared_signature": degenerate,
            "EXPOSED": max(baseline["matching_categories"],
                           degenerate["matching_categories"]) >= 2}


def audit_colour_identity():
    """COLOUR IDENTITY (`ci_assign`): Argmin over NodesOfType(ColourCategory) with
    NO admission bound in force. Two exposing stimuli: an EXACTLY EQUIDISTANT probe,
    and a FAR out-of-gamut probe.

    THE `bound` FLAG IS PINNED TO 0.0 HERE, EXPLICITLY (added by the k=1 rung,
    VISION_COLOUR_BOUND_K1_PREREG.md, enumerated in its §6). This audit is a RECORD
    OF THE DEFECT: its claim is "with NO admission bound in force, ci_assign does
    THIS". That claim must stay true regardless of what the seed later ships as its
    default -- and as of vision_colour_identity v1.3.0 the default is ARMED
    (bound=1.0). Pinning makes an always-implicit assumption EXPLICIT; it does not
    weaken the finding, and it keeps results/uniqueness_measure.json reproducible.

    NOTE, recorded rather than quietly worked around: this docstring used to say
    "zero `Lte` nodes in the seed", and the sibling gate
    `test_AUDIT_colour_identity_has_NO_admission_bound_at_all` still asserts exactly
    that, with the instruction "if a bound was added, re-run the audit". A bound WAS
    added -- composed as `Not(Exists(o != winner: dist < 2*d))`, i.e. with `Lt`, not
    `Lte` -- so that tripwire does NOT trip: it is blind to the very fix that
    answered it. NAMED as a residual for the supervisor; NOT repaired here (another
    rung's assertion, outside this rung's charter)."""
    import colour_identity_measure as cim
    from domains import colour_identity_world as ciw
    from domains import colour_bound_world as cbw
    s, ag = cim._boot()
    h = ciw.add_field(s, cells=cim._grid([cim.A] * 4 + [cim.B] * 4 + [cim.C] * 4))
    cbw.set_flags(s, identity=1.0, bound=0.0)      # the defect record, pinned
    ciw.tick(s)
    cats = ciw.categories(s)
    out = {}
    for spec, label in [(dict(cL=10, cM=10, cS=20), "equidistant"),
                        (dict(cL=200, cM=5, cS=9), "far_out_of_gamut")]:
        n = ciw.add_region(s, h, dict(**spec, rrow=5, rcol=0))
        cbw.set_flags(s, identity=1.0, bound=0.0)  # the defect record, pinned
        ciw.tick(s)
        a = s.node(n)["attrs"]
        crg, cby = float(a.get("crg", 0.0)), float(a.get("cby", 0.0))
        d = sorted((math.hypot(crg - c["crg"], cby - c["cby"]), (c["crg"], c["cby"]))
                   for c in cats)
        out[label] = {"observation": [crg, cby],
                      "assigned": [float(a.get("sign_rg", 0.0)),
                                   float(a.get("sign_by", 0.0))],
                      "sign_dist": round(float(a.get("sign_dist", -1.0)), 4),
                      "winner_dist": round(d[0][0], 4),
                      "runnerup_dist": round(d[1][0], 4),
                      "margin": round(d[1][0] - d[0][0], 6),
                      "refused": int(float(a.get("sign_dist", -1.0)) < 0)}
    return {"rung": "colour identity (ci_assign)", "categories": cats,
            "has_admission_bound": False, "probes": out,
            "EXPOSED": out["equidistant"]["margin"] == 0.0
            or out["far_out_of_gamut"]["refused"] == 0}


def audit_similarity_untangling():
    """SIMILARITY / IDENTITY-UNTANGLING (`shape_decode_loop`): admission is EXACT
    EQUALITY (Count(residual)==0 / *_explained==1) — the seed contains ZERO Lte/Gte
    nodes, so there is NO verdict bound and therefore NO 'candidates within the
    bound' set to count. STRUCTURAL verdict, verified by parsing the seed."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "seeds", "shape_decode_loop.json")
    blob = json.dumps(json.load(open(p)))
    _ast = audit_seed_file(p)
    return {"rung": "similarity / identity untangling (shape_decode_loop)",
            "Lte_nodes": blob.count('"type": "Lte"'),
            "Gte_nodes": blob.count('"type": "Gte"'),
            "Argmax_nodes": blob.count('"type": "Argmax"'),
            # ADDITIVE (tripwire repair, inventory S4). The three counts above are
            # substring scans and read 0/0 while the seed contains 19 comparators
            # spelled Lt/Gt. The AST fields are the load-bearing ones; the verdict
            # HOLDS because all 19 are cardinality or flag/epoch reads, not bounds.
            "AST_T0_any_comparator": _ast["T0_any_comparator"],
            "AST_T1_bound_like": _ast["T1_bound_like"],
            "AST_has_bound": _ast["has_bound"],
            "admission": "exact equality (Count(residual)==0 / *_explained==1)",
            "EXPOSED": False,
            "NOT_APPLICABLE_REASON":
                "no verdict bound exists, so 'two candidates inside the bound' is "
                "undefined; the residual hazard on this path is an EXACT Argmax tie "
                "in post-verdict label recovery, a different mechanism"}


def audit_deformation():
    """DEFORMATION (`df_recognize`): Argmin over NodesOfType(ShapeSignature) under a
    THREE-CLAUSE Lte bound, with ZERO Count/Filter — structurally the SAME shape as
    T1/L1. STRUCTURAL verdict only; NOT measured by this rung (declared, §8)."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "seeds", "vision_deformation.json")
    seed = json.load(open(p))
    rule = [r for r in seed["rules"] if r["name"] == "df_recognize"][0]
    blob = json.dumps(rule)
    _ast = audit_seed_file(p, "df_recognize")
    return {"rung": "deformation (df_recognize)",
            "Argmin_nodes": blob.count('"type": "Argmin"'),
            "Lte_nodes": blob.count('"type": "Lte"'),
            "Count_nodes": blob.count('"type": "Count"'),
            "Filter_nodes": blob.count('"type": "Filter"'),
            # ADDITIVE (tripwire repair, inventory S5). This row happens to be
            # correct because the bound is spelled `Lte`; re-spelling it to `Lt`
            # would silently zero the substring count. The AST fields do not care.
            "AST_T0_any_comparator": _ast["T0_any_comparator"],
            "AST_T1_bound_like": _ast["T1_bound_like"],
            "AST_has_bound": _ast["has_bound"],
            "EXPOSED": "STRUCTURALLY (Argmin + bound + zero tie-check) — NOT MEASURED"}


# ================================================================================
# PART B — THE GATE
# ================================================================================

def arm_A_hazard_reproduced():
    """The PREMISE: with the gate OFF, the floor returns confident WRONG identities."""
    per = {}
    for g in FLOOR_GAINS:
        s, ref, test = _run_pair((g, g, g), uniqueness=0.0)
        sc = _score(s, ref, test)
        per[str(g)] = {"n": sc["n"], "correct": sc["l1_correct"],
                       "false_ids": sc["l1_false"], "refused": sc["l1_refused"]}
    ok = all(v["false_ids"] > 0 and v["refused"] == 0 for v in per.values())
    return {"per_gain": per, "pass": ok,
            "note": "predicted 2/2/4 false, 0 refused at 0.06/0.05/0.04"}


def arm_B_gate_refuses():
    """With the gate ON, the ambiguous regime REFUSES instead of mis-identifying."""
    per = {}
    for g in FLOOR_GAINS:
        s, ref, test = _run_pair((g, g, g), uniqueness=1.0)
        sc = _score(s, ref, test)
        per[str(g)] = {"n": sc["n"], "uq_false_ids": sc["uq_false"],
                       "uq_ambiguous": sc["uq_ambiguous"],
                       "uq_correct": sc["uq_correct"],
                       "l1_false_ids_same_graph": sc["l1_false"],
                       "detail": sc["detail"]}
    return {"per_gain": per, "pass": all(v["uq_false_ids"] == 0 for v in per.values())}


def arm_C_no_regression():
    """THE §1.1 CONJUNCTION: in the UNAMBIGUOUS regime the gate still RECOGNIZES at
    the prior rate. A BUILD THAT REFUSES EVERYTHING FAILS HERE — that is the point."""
    per, correct, refused, total = {}, 0, 0, 0
    for g in REAL_GAINS:
        s, ref, test = _run_pair(g, uniqueness=1.0)
        sc = _score(s, ref, test)
        per[str(g)] = {"n": sc["n"], "uq_correct": sc["uq_correct"],
                       "uq_false": sc["uq_false"], "uq_ambiguous": sc["uq_ambiguous"],
                       "l1_correct_same_graph": sc["l1_correct"]}
        correct += sc["uq_correct"]
        refused += sc["uq_ambiguous"]
        total += sc["n"]
    return {"per_gain": per, "uq_correct": correct, "uq_refused": refused,
            "n": total, "pass": correct == total and refused == 0,
            "note": "L1's committed headline is 60/60; the gate must not move it"}


def arm_D_discrimination():
    """Cross-material false identities with the gate ON, at the real gains."""
    false_ids = 0
    for g in REAL_GAINS:
        s, ref, test = _run_pair(g, uniqueness=1.0)
        false_ids += _score(s, ref, test)["uq_false"]
    return {"false_identities": false_ids, "exact_zero": false_ids == 0,
            "pass": false_ids == 0,
            "caveat": "§1.1: a refuse-everything build also scores 0 here — arm C is "
                      "what makes the conjunction a gate"}


def arm_E_noise_floor(n_seeds=NOISE_N, base_seed=NOISE_BASE):
    """iid random cone fields, gate ON: nothing mints, nothing is claimed."""
    bad, per = 0, []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        refl = [{"name": f"n{j}", "rL": rng.randint(1, 99), "rM": rng.randint(1, 99),
                 "rS": rng.randint(1, 99)} for j in range(13)]
        s, ref, test = _run_pair((3.3, 2.5, 4.5), reflectances=refl, uniqueness=1.0)
        k = lw.n_identities(s)
        claims = sum(uw.verdict(s, n)["uq_recognized"] for n in test["surface_ids"])
        if k > 0 or claims > 0:
            bad += 1
            per.append({"seed": seed, "n_identities": k, "claims": claims})
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "bad_fields": bad, "detail": per, "pass": bad == 0}


def arm_F_novel_floor():
    """A never-minted material must stay refused with the gate ON."""
    per, forced = {}, 0
    for gain in REAL_GAINS:
        s, ref, test = _run_pair(gain, uniqueness=1.0)
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] != NOVEL["name"]:
                continue
            v = uw.verdict(s, nid)
            forced += v["uq_recognized"]
            per[str(gain)] = {"uq_recognized": v["uq_recognized"],
                              "uq_status": v["uq_status"],
                              "l1_status": lw.recognition(s, nid)["l1_status"]}
    return {"per_gain": per, "forced_matches": forced, "pass": forced == 0}


def arm_G_ambiguity_cost():
    """THE DECLARED COST (predicted in the prereg, NOT a discovery): at the floor the
    gate refuses EVERY row, not only the wrong ones."""
    per = {}
    for g in FLOOR_GAINS:
        s, ref, test = _run_pair((g, g, g), uniqueness=1.0)
        sc = _score(s, ref, test)
        per[str(g)] = {"n": sc["n"], "l1_correct_ungated": sc["l1_correct"],
                       "l1_false_ungated": sc["l1_false"],
                       "uq_correct_gated": sc["uq_correct"],
                       "uq_ambiguous": sc["uq_ambiguous"]}
    return {"per_gain": per,
            "note": "predicted in advance: 0/12 retained at each floor gain — the "
                    "gate trades confident answers for honest refusals"}


def arm_X_offday():
    """§9: with the flag at its default 0, the gate is INERT — no uq_* attribute is
    written anywhere, and L1's own verdict is untouched."""
    out = {}
    for g in REAL_GAINS[:1] + [(0.04, 0.04, 0.04)]:
        s, ref, test = _run_pair(g, uniqueness=0.0)
        sc = _score(s, ref, test)
        wrote = sum(1 for d in sc["detail"]
                    if d["uq_status"] != "" or d["uq_recognized"] != 0)
        out[str(g)] = {"uq_attrs_written": wrote, "l1_correct": sc["l1_correct"],
                       "l1_false": sc["l1_false"]}
    return {"per_gain": out,
            "pass": all(v["uq_attrs_written"] == 0 for v in out.values())}


def main():
    t0 = time.time()
    res = {
        "rung": "L1b — THE UNIQUENESS GATE for the SILENT-ARGMIN HAZARD",
        "prereg": "VISION_UNIQUENESS_PREREG.md (committed 8015d690)",
        "provenance": provenance_line(),
        "lattice_step_bound": LATTICE_STEP,
        "seed_blocks_consumed": {"noise": [NOISE_BASE, NOISE_BASE + NOISE_N - 1]},
        "PART_A_AUDIT": {
            "L1_lighting": audit_l1(),
            "T1_continuous_pose": audit_continuous_pose(),
            "T2_category": audit_category(),
            "similarity_untangling": audit_similarity_untangling(),
            "colour_identity": audit_colour_identity(),
            "deformation": audit_deformation(),
        },
        "PART_B_GATE": {
            "A_hazard_reproduced": arm_A_hazard_reproduced(),
            "B_gate_refuses": arm_B_gate_refuses(),
            "C_no_regression": arm_C_no_regression(),
            "D_discrimination": arm_D_discrimination(),
            "E_noise_floor": arm_E_noise_floor(),
            "F_novel_floor": arm_F_novel_floor(),
            "G_ambiguity_cost": arm_G_ambiguity_cost(),
            "X_offday": arm_X_offday(),
        },
        "elapsed_s": round(time.time() - t0, 1),
    }
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "uniqueness_measure.json")
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: v for k, v in res.items() if k != "PART_B_GATE"}, indent=1)[:4000])
    for name, arm in res["PART_B_GATE"].items():
        print(f"  {name}: pass={arm.get('pass')} "
              f"{ {k: v for k, v in arm.items() if k not in ('detail', 'per_gain')} }")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
