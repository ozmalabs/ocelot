#!/usr/bin/env python3
"""ADVANCED LIGHTING RUNG L1 — REAL-VALUED ILLUMINANT GAINS (confirmatory run).

Pre-registration: VISION_LIGHTING_L1_PREREG.md (committed BEFORE this run at
0cec9c38, §3). Every decision — the frame statistics, the rounding-envelope
in-class discovery, the continuous rendered verdict and the refusal — is a
`vision_lighting_l1` RULE (l1_frame_stats / l1_inclass / l1_recognize /
l1_refuse); the SurfaceIdentity codebook is T3's integer `li_mint`, unmodified.
This runner only CONSTRUCTS reflectance × illuminant frames and READS the
discovered gain / minted identities / per-surface recognitions back (mechanical
I/O, §0), TALLYING metrics over them. The ground-truth `material` is used ONLY
here for scoring — NEVER read by a seed rule.

Both arms are read from the SAME graph in the SAME run: T3's exact `lit_*` and
L1's continuous `l1_*`. That is what makes CONTINUOUS-DECIDES a measurement.

Run from the gamma-substrate dir:
    python scripts/lighting_l1_measure.py
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

D_CONE = 3
M_MIN = 2
LATTICE_STEP = 1.0   # the falls-out bound — ONE lattice step (prereg §2.1)

# T3's six materials (reflectances), two patches each => members = 2 = m_min.
MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
# Present in BOTH frames but with only ONE patch => members = 1 < m_min => NO
# identity minted. The "different object" floor.
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}

REF_GAIN = (1.0, 1.0, 1.0)

# THE FOUR REAL GAINS T3 MEASURED AND REFUSED (VISION_LIGHTING_RESULTS.md, bound
# L2: 0/12 at each), plus a PER-CHANNEL real gain. 5 conditions x 12 = 60.
REAL_GAINS = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
              (1.5, 2.5, 3.3)]
# The INTEGER gains T3 accepted (12/12 at each) — the DEAD-ARM FLOOR (§1.1 cl. 4).
INTEGER_GAINS = [(2.0, 2.0, 2.0), (3.0, 3.0, 3.0), (4.0, 4.0, 4.0)]
# The identifiability sweep — DIMMING included, where the lattice loses resolution.
SWEEP_GAINS = [0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.5, 3.3, 7.5, 20.0]

NOISE_BASE, NOISE_N = 45220, 100          # ledger block consumed
OUTCLASS_BASE, OUTCLASS_N = 45320, 20     # ledger block consumed


def _reflectances(include_novel: bool = True) -> list[dict]:
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1"])
    return s, ag


def _run_pair(gain, *, ref_gain=REF_GAIN, include_novel=True,
              flag=1.0, flag_l1=1.0, reflectances=None, link=True):
    """Boot, build a reference frame + a test frame under `gain`, tick. Mechanical."""
    refl = _reflectances(include_novel) if reflectances is None else reflectances
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=ref_gain, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=gain, start_sidx=1000)
    if link:
        lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.set_flag_l1(s, lighting_l1=flag_l1)
    lw.tick(s)
    return s, ref, test


def _expected_key(s, ref, material_name: str) -> int:
    """The sid_key the identity for `material_name` was minted with — read from the
    REFERENCE frame's own surfaces (mechanical bookkeeping, not a decision)."""
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        if meta["name"] == material_name:
            return int(lw.surf_attr(s, nid, "sidx"))
    return -1


def _score(s, ref, test):
    """Per-surface scoring of BOTH arms over the non-NOVEL surfaces. Mechanical."""
    rows, l1_correct, l1_false, t3_correct, n = [], 0, 0, 0, 0
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        r = lw.recognition(s, nid)
        exp = _expected_key(s, ref, meta["name"])
        ok = (r["l1_recognized"] == 1 and r["l1_id"] == exp)
        false_id = (r["l1_recognized"] == 1 and r["l1_id"] != exp)
        l1_correct += ok
        l1_false += false_id
        t3_correct += (r["lit_recognized"] == 1 and r["lit_id"] == exp)
        n += 1
        rows.append({"material": meta["name"], "expected_id": exp,
                     "l1_recognized": r["l1_recognized"], "l1_id": r["l1_id"],
                     "l1_resid": round(r["l1_resid"], 6),
                     "l1_status": r["l1_status"],
                     "lit_recognized": r["lit_recognized"],
                     "ok": ok, "false_id": false_id})
    return {"rows": rows, "l1_correct": l1_correct, "l1_false": l1_false,
            "t3_correct": t3_correct, "n": n}


# ---- A: REAL-GAIN INVARIANCE (the headline) ------------------------------------
def arm_real_gain_invariance():
    per_gain, correct, total, false_ids = {}, 0, 0, 0
    for gain in REAL_GAINS:
        s, ref, test = _run_pair(gain)
        sc = _score(s, ref, test)
        per_gain[str(gain)] = {
            "l1_inclass": lw.frame_attr(s, test, "l1_inclass"),
            "t3_inclass": lw.frame_attr(s, test, "illum_inclass"),
            "n_identities": lw.n_identities(s),
            "discovered_gain_real": lw.illuminants_l1(s),
            "l1_correct": sc["l1_correct"], "t3_correct": sc["t3_correct"],
            "surfaces": sc["rows"]}
        correct += sc["l1_correct"]; total += sc["n"]; false_ids += sc["l1_false"]
    return {"per_gain": per_gain, "correct": correct, "total": total,
            "false_identities": false_ids,
            "pass": correct >= 58 and total == 60}


# ---- B: DISCRIMINATION exact-0 (RISKED — the §1.1 universal-container crux) -----
def arm_discrimination():
    false_ids, detail = 0, []
    for gain in REAL_GAINS:
        s, ref, test = _run_pair(gain)
        sc = _score(s, ref, test)
        false_ids += sc["l1_false"]
        detail.append({"gain": str(gain), "false_ids": sc["l1_false"],
                       "n": sc["n"]})
    return {"cross_false": false_ids, "detail": detail, "pass": false_ids == 0}


# ---- C: CONTINUOUS-DECIDES (the rung's reason to exist) ------------------------
def arm_continuous_decides():
    """On the SAME graph: T3's exact integer-ratio path vs L1's continuous verdict,
    at the real gains T3 REFUSED. And — §1.1 clause 4 — T3's arm must be shown
    ALIVE at integer gains, so its 0 is a refusal and not an inert rule."""
    disc, cont, total = 0, 0, 0
    per = {}
    for gain in REAL_GAINS:
        s, ref, test = _run_pair(gain)
        sc = _score(s, ref, test)
        disc += sc["t3_correct"]; cont += sc["l1_correct"]; total += sc["n"]
        per[str(gain)] = {"discrete_correct": sc["t3_correct"],
                          "continuous_correct": sc["l1_correct"], "n": sc["n"]}
    # THE DEAD-ARM FLOOR: the discrete path at the gains it DOES accept.
    alive, alive_total, per_int = 0, 0, {}
    for gain in INTEGER_GAINS:
        s, ref, test = _run_pair(gain)
        sc = _score(s, ref, test)
        alive += sc["t3_correct"]; alive_total += sc["n"]
        per_int[str(gain)] = {"discrete_correct": sc["t3_correct"],
                              "continuous_correct": sc["l1_correct"],
                              "n": sc["n"]}
    return {"per_gain": per, "discrete_correct": disc, "continuous_correct": cont,
            "total": total,
            "discrete_alive_integer_gains": per_int,
            "discrete_alive_correct": alive, "discrete_alive_total": alive_total,
            "pass": (disc == 0 and cont >= 58 and alive == alive_total
                     and alive_total == 36)}


# ---- D: IDENTIFIABILITY / RESOLUTION curve -------------------------------------
def arm_identifiability():
    """The bound is pinned to observational RESOLUTION and to nothing else, so it
    MUST degrade where the lattice cannot record the difference. The break point is
    the measurement (§8). GATED only on: g >= 1 clean, and discrimination 0
    EVERYWHERE — a resolution failure must be a REFUSAL, never a false identity."""
    rows = []
    ok_high, false_any = True, 0
    for g in SWEEP_GAINS:
        s, ref, test = _run_pair((g, g, g))
        sc = _score(s, ref, test)
        refused = sum(1 for r in sc["rows"] if r["l1_status"] == "l1_refused")
        # how many DISTINCT lattice points the 12 surfaces occupy — the direct
        # read of the resolution the observation actually has.
        pts = {(r0["cL"], r0["cM"], r0["cS"]) for r0 in
               [lw.recognition(s, n) for n, m in zip(test["surface_ids"],
                                                     test["meta"])
                if m["name"] != NOVEL["name"]]}
        rows.append({"gain": g, "l1_inclass": lw.frame_attr(s, test, "l1_inclass"),
                     "correct": sc["l1_correct"], "false_ids": sc["l1_false"],
                     "refused": refused, "n": sc["n"],
                     "distinct_lattice_points": len(pts),
                     "n_identities": lw.n_identities(s)})
        false_any += sc["l1_false"]
        if g >= 1.0 and sc["l1_correct"] != sc["n"]:
            ok_high = False
    return {"rows": rows, "false_identities_total": false_any,
            "high_gain_clean": ok_high,
            "UNDERPOWERED": (
                "THIS ARM PASSED BUT COULD NOT HAVE FAILED. Its declared minimum "
                "gain (0.2) sits entirely ABOVE the true resolution floor (~0.06 "
                "for these six materials — they stay on distinct lattice points "
                "all the way down to 0.08), so the predicted degradation was out "
                "of range by construction. §13.1's test — 'could this model have "
                "produced the opposite result?' — is answered NO for this arm as "
                "written. The real measurement is P_true_resolution_floor. "
                "Reported here rather than quietly rescoped."),
            "pass": ok_high and false_any == 0}


# ---- E: NOISE floor (RISKED, n=100, seeds 45220–45319) -------------------------
def arm_floor_noise(n_seeds=NOISE_N, base_seed=NOISE_BASE):
    """iid random cone fields: no identity should mint and no cross-frame identity
    should be claimed by the CONTINUOUS arm."""
    bad, per = 0, []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        refl = [{"name": f"n{j}", "rL": rng.randint(1, 99), "rM": rng.randint(1, 99),
                 "rS": rng.randint(1, 99)} for j in range(13)]
        s, ref, test = _run_pair((3.3, 2.5, 4.5), reflectances=refl)
        k = lw.n_identities(s)
        claims = sum(int(lw.surf_attr(s, n, "l1_recognized"))
                     for n in test["surface_ids"])
        if k > 0 or claims > 0:
            bad += 1
            per.append({"seed": seed, "n_identities": k, "claims": claims})
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "bad_fields": bad, "detail": per, "pass": bad == 0}


# ---- F: OUT-OF-CLASS floor (RISKED, n=20, seeds 45320–45339) -------------------
def arm_out_of_class(n_scenes=OUTCLASS_N, base_seed=OUTCLASS_BASE):
    """A SPATIALLY-VARYING illuminant (an independent gain per surface) is OUTSIDE
    the diagonal class and must be REFUSED, never force-matched. L1's envelope is
    DELIBERATELY looser than T3's exact test, so `inclass_fired` is RISKED and is
    REPORTED; the GATE is on false identities, which must be 0 either way."""
    inclass_fired, false_ids, per = 0, 0, []
    refl = _reflectances(include_novel=False)
    for i in range(n_scenes):
        rng = random.Random(base_seed + i)
        gains = [(rng.uniform(2.0, 6.0), rng.uniform(2.0, 6.0),
                  rng.uniform(2.0, 6.0)) for _ in refl]
        s, ref, test = _run_pair(gains, reflectances=refl, include_novel=False)
        ic = lw.frame_attr(s, test, "l1_inclass")
        fi = sum(int(lw.surf_attr(s, n, "l1_recognized"))
                 for n in test["surface_ids"])
        inclass_fired += int(ic > 0.5)
        false_ids += fi
        per.append({"seed": base_seed + i, "l1_inclass": ic, "claims": fi})
    return {"n_scenes": n_scenes,
            "seed_range": [base_seed, base_seed + n_scenes - 1],
            "inclass_fired": inclass_fired, "false_identities": false_ids,
            "detail": per, "pass": false_ids == 0}


# ---- G: NOVEL-material floor ---------------------------------------------------
def arm_floor_novel():
    """The NOVEL material (one patch => never minted) must be REFUSED under a REAL
    in-class gain, not force-matched to a held identity."""
    per_gain, forced = {}, 0
    for gain in REAL_GAINS:
        s, ref, test = _run_pair(gain)
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] != NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            forced += r["l1_recognized"]
            per_gain[str(gain)] = {"l1_recognized": r["l1_recognized"],
                                   "l1_status": r["l1_status"],
                                   "l1_resid": round(r["l1_resid"], 6),
                                   "l1_inclass": lw.frame_attr(s, test,
                                                               "l1_inclass")}
    return {"per_gain": per_gain, "forced_matches": forced, "pass": forced == 0}


# ---- H: DOWNSTREAM / load-bearing (§13.2) --------------------------------------
def arm_downstream():
    g = (3.3, 3.3, 3.3)
    on_s, on_ref, on_t = _run_pair(g, flag_l1=1.0)
    off_s, off_ref, off_t = _run_pair(g, flag_l1=0.0)
    on_rec = sum(int(lw.surf_attr(on_s, n, "l1_recognized"))
                 for n in on_t["surface_ids"])
    off_rec = sum(int(lw.surf_attr(off_s, n, "l1_recognized"))
                  for n in off_t["surface_ids"])
    # T3's arm on the SAME graph at the SAME real gain — it must be 0 both ways.
    on_t3 = sum(int(lw.surf_attr(on_s, n, "lit_recognized"))
                for n in on_t["surface_ids"])
    return {"l1_on": on_rec, "l1_off": off_rec, "d_recognized": abs(on_rec - off_rec),
            "t3_same_graph": on_t3,
            "n_illuminants_l1_on": lw.n_illuminants_l1(on_s),
            "n_illuminants_l1_off": lw.n_illuminants_l1(off_s),
            "pass": on_rec == 12 and off_rec == 0 and on_t3 == 0}


# ---- X: OFF-DAY (§9) -----------------------------------------------------------
def arm_offday():
    """L1's flag left at its DEFAULT (0). L1 must be completely inert — AND T3 must
    be EXACTLY as committed (its own flag on), which is the byte-identity claim."""
    refl = _reflectances()
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=(3.0, 2.0, 4.0), start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=1.0)      # T3 ON
    lw.tick(s)                        # L1 flag NEVER written — default 0
    l1_rec = max(lw.surf_attr(s, n, "l1_recognized") for n in test["surface_ids"])
    t3_rec = sum(int(lw.surf_attr(s, n, "lit_recognized"))
                 for n in test["surface_ids"])
    return {"n_illuminants_l1": lw.n_illuminants_l1(s),
            "max_l1_recognized": l1_rec,
            "l1_inclass": lw.frame_attr(s, test, "l1_inclass"),
            "l1_stats_done": lw.frame_attr(s, test, "l1_stats_done"),
            "t3_recognized_unchanged": t3_rec,
            "t3_identities": lw.n_identities(s),
            "pass": (lw.n_illuminants_l1(s) == 0 and l1_rec == 0.0
                     and lw.frame_attr(s, test, "l1_inclass") == 0.0
                     and lw.frame_attr(s, test, "l1_stats_done") == 0.0
                     and t3_rec == 12 and lw.n_identities(s) == 6)}


# ---- probe: the RESIDUAL MARGIN (reported — is the bound doing work?) ----------
def probe_residual_margins():
    """The true-match residual vs the bound, and the runner-up gap. If the true
    residual sat at ~0 the bound would be decorative; if it hugged 1.0 the bound
    would be the only thing standing between this and a universal container.
    REPORTED so the bound's actual role is visible (§13.2)."""
    rows = []
    for g in [1.5, 2.5, 3.3, 7.5, 0.5]:
        s, ref, test = _run_pair((g, g, g))
        res = [lw.recognition(s, n)["l1_resid"]
               for n, m in zip(test["surface_ids"], test["meta"])
               if m["name"] != NOVEL["name"]]
        res = [r for r in res if r >= 0]
        rows.append({"gain": g, "max_true_residual": round(max(res), 6) if res else None,
                     "mean_residual": round(sum(res) / len(res), 6) if res else None,
                     "bound": LATTICE_STEP})
    return {"rows": rows,
            "note": ("the bound is ONE LATTICE STEP and falls out of two half-step "
                     "roundings; these are the residuals it is actually "
                     "adjudicating.")}


# ---- probe: THE TRUE RESOLUTION FLOOR (post-hoc, BEYOND the pre-registration) --
# The pre-registered sweep (arm D) bottomed out at g=0.2 and was FLAT at 12/12.
# That is not a clean result — it means the DECLARED RANGE SAT ENTIRELY ABOVE THE
# FLOOR, so the arm COULD NOT HAVE FAILED (§13.1: "could this model have produced
# the opposite result?" — for arm D as written, NO). This probe extends the sweep
# until the materials actually collide on the lattice, and reports what the
# mechanism does there. It is REPORTED, NOT GATED, and is flagged in the results
# file as beyond the pre-registration. Reporting it makes the claim STRICTER
# against itself, which §1.1 explicitly permits and §7 demands.
DEEP_SWEEP = [0.2, 0.1, 0.08, 0.06, 0.05, 0.04, 0.03, 0.02]


def probe_true_resolution_floor():
    rows = []
    for g in DEEP_SWEEP:
        s, ref, test = _run_pair((g, g, g))
        sc = _score(s, ref, test)
        refused = sum(1 for r in sc["rows"] if r["l1_status"] == "l1_refused")
        pts = {}
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] == NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            pts.setdefault((r["cL"], r["cM"], r["cS"]), set()).add(meta["name"])
        collisions = {str(k): sorted(v) for k, v in pts.items() if len(v) > 1}
        rows.append({"gain": g, "correct": sc["l1_correct"],
                     "FALSE_IDENTITIES": sc["l1_false"], "refused": refused,
                     "n": sc["n"], "distinct_lattice_points": len(pts),
                     "lattice_collisions": collisions})
    first_break = next((r["gain"] for r in rows if r["FALSE_IDENTITIES"] > 0), None)
    return {
        "rows": rows,
        "first_gain_with_false_identity": first_break,
        "prereg_sweep_min": min(SWEEP_GAINS),
        "VERDICT": (
            "THE PRE-REGISTERED ARM D WAS UNDER-POWERED: its minimum gain (0.2) "
            "sits entirely ABOVE the true resolution floor (~0.06 for these six "
            "materials), so it could not have failed. Extended here. AT THE FLOOR "
            "THE MECHANISM RETURNS A CONFIDENT WRONG IDENTITY RATHER THAN "
            "REFUSING — see probe_ambiguity_is_detectable for why that is a real, "
            "nameable gap and not merely intrinsic ill-posedness."),
    }


def probe_ambiguity_is_detectable():
    """AT THE RESOLUTION FLOOR, IS THE AMBIGUITY VISIBLE FROM INSIDE THE GRAPH?

    THE DECISIVE QUESTION for how to read the floor. If only ONE candidate were
    within the bound, a wrong identity would be pure intrinsic ill-posedness — the
    observation simply does not carry the distinction, and no mechanism could do
    better (T3's global-scale ambiguity is of that kind). If TWO OR MORE are within
    the bound, the ambiguity IS present in the graph, the Argmin is resolving it
    SILENTLY, and a refusal was available and not taken.

    That second case is exactly the failure mode T3's own results file names:
    "a plain Pick would have written a SILENT WRONG ANSWER ... and the rung would
    have shipped." Here `Argmin` does it at the resolution floor.
    """
    rows = []
    for g in [0.05, 0.06, 0.04]:
        s, ref, test = _run_pair((g, g, g))
        a_test = {ch: lw.frame_attr(s, test, "l1_a" + ch) for ch in ("L", "M", "S")}
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] == NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            exp = _expected_key(s, ref, meta["name"])
            if r["l1_id"] == exp:
                continue
            within = []
            for ident in lw.identities(s):
                resid = max(
                    abs(r["c" + ch] - ident["p" + ch]
                        * (a_test[ch] / ident["pa" + ch]))
                    for ch in ("L", "M", "S"))
                if resid <= LATTICE_STEP:
                    within.append({"sid_key": ident["sid_key"],
                                   "resid": round(resid, 6)})
            rows.append({"gain": g, "material": meta["name"],
                         "observation": [r["cL"], r["cM"], r["cS"]],
                         "reported_id": r["l1_id"], "expected_id": exp,
                         "candidates_within_bound": sorted(
                             within, key=lambda d: d["resid"]),
                         "n_within_bound": len(within)})
            break   # one exemplar per gain is enough to establish the structure
    detectable = all(r["n_within_bound"] >= 2 for r in rows) and bool(rows)
    return {
        "rows": rows, "ambiguity_is_detectable": detectable,
        "VERDICT": (
            "TWO OR MORE candidates lie within the falls-out bound at the "
            "resolution floor, so the ambiguity IS detectable from inside the "
            "graph and the Argmin resolves it SILENTLY. The wrong identity is "
            "therefore NOT pure intrinsic ill-posedness — a REFUSAL was available "
            "and was not taken. NAMED NEXT MECHANISM (rung L1b, needs its OWN "
            "pre-registration, §3.6 — deliberately NOT bolted on here, because "
            "adding a mechanism after seeing the failure and reporting the "
            "improved number is exactly what §5 forbids): refuse when the "
            "runner-up is also within the bound, i.e. make the verdict's "
            "UNIQUENESS a gate, the continuous analogue of the PickUnique lesson "
            "T3 learned."
            if detectable else
            "Only ONE candidate lies within the bound — the wrong identity is "
            "intrinsic ill-posedness, not an unchecked ambiguity."),
    }


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "prereg_commit": "0cec9c38",
        "base_main_head": "7cbf1962",
        "d_cone": D_CONE, "m_min": M_MIN, "lattice_step_bound": LATTICE_STEP,
        "materials": MATERIALS, "novel": NOVEL,
        "real_gains": [list(g) for g in REAL_GAINS],
        "integer_gains": [list(g) for g in INTEGER_GAINS],
        "sweep_gains": SWEEP_GAINS,
        "seed_blocks_consumed": {"noise": [NOISE_BASE, NOISE_BASE + NOISE_N - 1],
                                 "out_of_class": [OUTCLASS_BASE,
                                                  OUTCLASS_BASE + OUTCLASS_N - 1]},
        "A_real_gain_invariance": arm_real_gain_invariance(),
        "B_discrimination": arm_discrimination(),
        "C_continuous_decides": arm_continuous_decides(),
        "D_identifiability": arm_identifiability(),
        "E_floor_noise": arm_floor_noise(),
        "F_out_of_class": arm_out_of_class(),
        "G_floor_novel": arm_floor_novel(),
        "H_downstream": arm_downstream(),
        "X_offday": arm_offday(),
        "P_residual_margins": probe_residual_margins(),
        "P_true_resolution_floor": probe_true_resolution_floor(),
        "P_ambiguity_is_detectable": probe_ambiguity_is_detectable(),
    }
    arm_keys = [k for k in results
                if isinstance(results.get(k), dict) and "pass" in results[k]]
    results["ALL_PASS"] = all(results[k]["pass"] for k in arm_keys)
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "lighting_l1_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in arm_keys:
        print(f"  {k:28s} pass={results[k]['pass']}")
    print("ALL_PASS:", results["ALL_PASS"], "| wrote", out, "|",
          results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
