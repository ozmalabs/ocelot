#!/usr/bin/env python3
"""ADVANCED LIGHTING RUNG L3 — GLOBAL ILLUMINANT INFERENCE (confirmatory run).

Pre-registration: VISION_LIGHTING_L3_PREREG.md (committed BEFORE this run at
d6c35a1f — §3). Every decision — the per-locale estimate, the SCENE-LEVEL POOL,
the anchor CORROBORATION, the verdict, the two refusals and the V4 lesion — is a
`vision_lighting_l3` RULE. The SurfaceIdentity codebook is T3's integer
`li_mint`, unmodified, reused through L2.

This runner only CONSTRUCTS reflectance × illuminant-FIELD frames and READS
attrs back (mechanical I/O, §0), TALLYING metrics over them. The ground-truth
`material` is used ONLY here for scoring — NEVER read by a seed rule.

SIX arms are read from the SAME graph in the SAME run: T3's `lit_*`, L1's
`l1_*`, L2's `l2_*` — which IS L3's POOLING ABLATION, being `l3_recognize`
minus the corroboration conjunct — L2's global-anchor `l2g_*`, L3's
corroborated `l3_*`, and L3's V4-LESIONED `l3l_*`.

Run from the gamma-substrate dir:
    python scripts/lighting_l3_measure.py
"""
from __future__ import annotations
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402
from domains import lighting_l2_world as l2w  # noqa: E402
from domains import lighting_l3_world as l3w  # noqa: E402

CH = ("L", "M", "S")
LATTICE_STEP = 1.0

# T3/L1/L2's SIX materials, two patches each => members = 2 = m_min => minted.
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

# L2's FIVE pre-registered headline fields, as per-channel rho.
HEADLINE = [(1.006, 1.006, 1.006), (1.008, 1.008, 1.008), (1.010, 1.010, 1.010),
            (1.012, 1.012, 1.012), (1.006, 1.008, 1.010)]
# The UNIFORM gains T3 and L1 landed — the NO-REGRESSION conjunction.
UNIFORM = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
           (1.5, 2.5, 3.3), (2.0, 2.0, 2.0), (3.0, 3.0, 3.0), (4.0, 4.0, 4.0)]

# THE SEED BLOCKS THIS RUNG CONSUMES (prereg §0).
NOISE_BASE, NOISE_N = 45560, 100        # 100 x 13 = 1300, matching L2's E2
OUTCLASS_BASE, OUTCLASS_N = 45660, 20
OUTCLASS_AMP = 1.10


def _reflectances(include_novel: bool = True) -> list[dict]:
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _field(n: int, rhos, g0: float = 2.0) -> list[tuple]:
    """A geometric illuminant FIELD: g_ch(x) = g0 · rho_ch^x. World physics."""
    return [tuple(g0 * (rhos[k] ** x) for k in range(3)) for x in range(n)]


def _alternating(n: int, amp: float, g0: float = 2.0) -> list[tuple]:
    """A FAST-VARYING field: it changes by `amp` at EVERY adjacency."""
    return [tuple([g0 * (amp if x % 2 else 1.0)] * 3) for x in range(n)]


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1",
                            "vision_lighting_l2", "vision_lighting_l3"])
    return s, ag


def _build(s, *, test_refl, ref_refl, gains, radius=l2w.RADIUS,
           flag=1.0, flag_l1=1.0, flag_l2=1.0, flag_l3=1.0):
    """Build reference + test frames and tick to a fixpoint. Mechanical."""
    ref = l3w.add_frame(s, reflectances=ref_refl, gain=REF_GAIN,
                        is_reference=True, start_sidx=0, radius=radius)
    test = l3w.add_frame(s, reflectances=test_refl, gain=gains,
                         start_sidx=1000, radius=radius)
    l3w.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.set_flag_l1(s, lighting_l1=flag_l1)
    l2w.set_flag(s, lighting_l2=flag_l2)
    l3w.set_flag(s, lighting_l3=flag_l3)
    sweeps = l3w.tick(s)
    return ref, test, sweeps


def _run(gains, *, reflectances=None, radius=l2w.RADIUS, **flags):
    refl = _reflectances() if reflectances is None else reflectances
    s, _ag = _boot()
    ref, test, sweeps = _build(s, test_refl=refl, ref_refl=refl, gains=gains,
                               radius=radius, **flags)
    return s, ref, test, sweeps


def _expected(s, ref) -> dict:
    exp = {}
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        exp.setdefault(meta["name"], int(lw.surf_attr(s, nid, "sidx")))
    return exp


def _score(s, ref, test) -> dict:
    """Per-surface scoring of ALL SIX arms over the non-NOVEL surfaces."""
    exp = _expected(s, ref)
    rows = []
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        r = l3w.recognition(s, nid)
        rows.append({"material": meta["name"], "pos": r["pos"],
                     "expected_id": exp.get(meta["name"], -1), **r})
    scored = [r for r in rows if r["material"] != NOVEL["name"]]
    novel = [r for r in rows if r["material"] == NOVEL["name"]]

    def tally(pfx):
        c = sum(1 for r in scored
                if r[pfx + "recognized"] == 1 and r[pfx + "id"] == r["expected_id"])
        f = sum(1 for r in scored
                if r[pfx + "recognized"] == 1 and r[pfx + "id"] != r["expected_id"])
        return {"correct": c, "false": f, "refused": len(scored) - c - f}

    nin = [r["l3_ncand"] for r in scored if r["l3_recognized"] == 1]
    res = [r["l3_resid"] for r in scored if r["l3_recognized"] == 1]
    # THE DISAGREEMENT SET (prereg arm B'): rows L2 admits and L3 refuses.
    disagree = [r for r in scored
                if r["l2_recognized"] == 1 and r["l3_recognized"] == 0]
    return {
        "n": len(scored),
        "l3": tally("l3_"), "l2": tally("l2_"), "l3_lesioned": tally("l3l_"),
        "ablation_global_anchor": tally("l2g_"),
        "t3": tally("lit_"), "l1": tally("l1_"),
        "disagree_l2_admits_l3_refuses": len(disagree),
        "disagree_were_correct": sum(1 for r in disagree
                                     if r["l2_id"] == r["expected_id"]),
        "ncand": {"min": min(nin) if nin else None,
                  "median": sorted(nin)[len(nin) // 2] if nin else None,
                  "max": max(nin) if nin else None},
        "resid": {"min": round(min(res), 6) if res else None,
                  "max": round(max(res), 6) if res else None},
        "corroborated_locales": l3w.n_corroborated_locales(s, test),
        "scene_estimate": {k: round(v, 5)
                           for k, v in l3w.scene_estimate(s, test).items()},
        "novel_claimed_l3": sum(1 for r in novel if r["l3_recognized"] == 1),
        "novel_claimed_l2": sum(1 for r in novel if r["l2_recognized"] == 1),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
def arm_B_no_regression():
    """B: L2's crossing and the uniform gains must SURVIVE corroboration."""
    n = len(_reflectances())
    fields, uni = [], []
    f_l3 = f_l2 = f_false = 0
    u_l3 = u_l2 = u_false = 0
    t3_u = l1_u = 0
    les_field_correct = 0
    for rhos in HEADLINE:
        s, ref, test, sweeps = _run(_field(n, rhos))
        sc = _score(s, ref, test)
        f_l3 += sc["l3"]["correct"]; f_l2 += sc["l2"]["correct"]
        f_false += sc["l3"]["false"]
        les_field_correct += sc["l3_lesioned"]["correct"]
        fields.append({"rhos": list(rhos), "range": round(rhos[0] ** (n - 1), 4),
                       "sweeps": sweeps,
                       **{k: v for k, v in sc.items() if k != "rows"}})
    for g in UNIFORM:
        s, ref, test, _ = _run([g] * n)
        sc = _score(s, ref, test)
        u_l3 += sc["l3"]["correct"]; u_l2 += sc["l2"]["correct"]
        u_false += sc["l3"]["false"]
        t3_u += sc["t3"]["correct"]; l1_u += sc["l1"]["correct"]
        uni.append({"gain": list(g), **{k: v for k, v in sc.items() if k != "rows"}})
    return {"headline_fields": fields, "uniform_gains": uni,
            "L3_correct_under_fields": f_l3, "L2_correct_under_fields": f_l2,
            "n_fields": 60, "false_under_fields": f_false,
            "L3_correct_uniform": u_l3, "L2_correct_uniform": u_l2,
            "n_uniform": 96, "false_uniform": u_false,
            "T3_correct_uniform": t3_u, "L1_correct_uniform": l1_u,
            "LESIONED_correct_under_fields": les_field_correct}


def arm_A_D_leak():
    """A: THE LEAK, with pooling. D: the SAME leak with pooling ABLATED.

    The ablation is L2's OWN arm read off the SAME graph in the SAME tick —
    `l3_recognize` is `l2_recognize` plus exactly one conjunct, so `l2_*` IS
    this rule with the corroboration removed and nothing else changed (§13.2).

    The setup is L2's E2 VERBATIM (the arm that counts): the REFERENCE frame is
    the six real materials, so the codebook is LIVE with six identities and the
    recognizer is the same one scoring the headline; only the TEST frame is
    noise. `codebook_size` is recorded so the DEAD-ARM distinction L2 had to
    make (§1.1 clause 4) is auditable from this file rather than taken on trust.
    """
    l3_claimed = l2_claimed = tot = minted = 0
    l3_correctish = 0
    per_seed, leak_rows = [], []
    zero_resid_l2 = zero_resid_l3 = 0
    for sd in range(NOISE_BASE, NOISE_BASE + NOISE_N):
        rng = random.Random(sd)
        noise = [{"name": f"n{i}", "rL": rng.randint(0, 120),
                  "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
                 for i in range(13)]
        s, _ag = _boot()
        ref, test, _ = _build(s, test_refl=noise, ref_refl=_reflectances(),
                              gains=_field(len(noise), (1.008,) * 3))
        c3 = c2 = 0
        for nid in test["surface_ids"]:
            r = l3w.recognition(s, nid)
            c3 += r["l3_recognized"]; c2 += r["l2_recognized"]
            tot += 1
            if r["l2_recognized"] == 1 and abs(r["l2_resid"]) < 1e-9:
                zero_resid_l2 += 1
            if r["l3_recognized"] == 1:
                if abs(r["l3_resid"]) < 1e-9:
                    zero_resid_l3 += 1
                leak_rows.append({"seed": sd, "pos": r["pos"],
                                  "l3_resid": round(r["l3_resid"], 6),
                                  "l3_ncand": r["l3_ncand"]})
        l3_claimed += c3; l2_claimed += c2
        minted += l3w.n_identities(s)
        per_seed.append({"seed": sd, "l3": c3, "l2": c2,
                         "corroborated": l3w.n_corroborated_locales(s, test)})
    del l3_correctish
    return {"seeds": [NOISE_BASE, NOISE_BASE + NOISE_N - 1],
            "surfaces": tot, "codebook_size": minted // NOISE_N,
            "DEAD_ARM": (minted // NOISE_N) == 0,
            "A_leak_WITH_pooling": l3_claimed,
            "D_leak_POOLING_ABLATED": l2_claimed,
            "A_rate": round(l3_claimed / max(tot, 1), 5),
            "D_rate": round(l2_claimed / max(tot, 1), 5),
            "l2_leaks_at_residual_exactly_zero": zero_resid_l2,
            "l3_leaks_at_residual_exactly_zero": zero_resid_l3,
            "leak_rows": leak_rows[:60],
            "corroborated_locales_mean": round(
                sum(p["corroborated"] for p in per_seed) / max(len(per_seed), 1), 3),
            "per_seed_nonzero": [p for p in per_seed if p["l3"] or p["l2"]][:40]}


def arm_E_v4_dissociation():
    """E: THE V4 DISSOCIATION — constancy ABOLISHED, discrimination INTACT.

    The lesioned arm (`l3l_*`) removes the constancy stage entirely (ghat == 1)
    and is ALWAYS computed on the SAME graph. Two halves, BOTH required:

      * CONSTANCY ABOLISHED — under the illuminant FIELDS the lesioned arm must
        fail where the intact arm holds.
      * DISCRIMINATION INTACT — at the REFERENCE illuminant it must still tell
        the distinct materials apart. Without this half a merely DEAD arm would
        score a perfect "abolition" and the dissociation would be worthless
        (§1.1 clause 4).
    """
    n = len(_reflectances())
    fields = []
    les_c = int_c = 0
    for rhos in HEADLINE:
        s, ref, test, _ = _run(_field(n, rhos))
        sc = _score(s, ref, test)
        les_c += sc["l3_lesioned"]["correct"]; int_c += sc["l3"]["correct"]
        fields.append({"rhos": list(rhos),
                       "intact_correct": sc["l3"]["correct"],
                       "lesioned_correct": sc["l3_lesioned"]["correct"],
                       "lesioned_false": sc["l3_lesioned"]["false"]})
    # DISCRIMINATION at the REFERENCE illuminant — the lesion's ALIVE check.
    s, ref, test, _ = _run([REF_GAIN] * n)
    sc = _score(s, ref, test)
    return {"CONSTANCY_lesioned_correct_under_fields": les_c,
            "CONSTANCY_intact_correct_under_fields": int_c, "n_fields": 60,
            "per_field": fields,
            "DISCRIMINATION_lesioned_correct_at_reference": sc["l3_lesioned"]["correct"],
            "DISCRIMINATION_lesioned_false_at_reference": sc["l3_lesioned"]["false"],
            "DISCRIMINATION_intact_correct_at_reference": sc["l3"]["correct"],
            "n_reference": sc["n"]}


def arm_F_floor():
    """F: OUT-OF-CLASS floor — FAST-VARYING fields, FRESH seeds 45660-45679."""
    rows = []
    tot_c = tot_f = tot_n = 0
    for sd in range(OUTCLASS_BASE, OUTCLASS_BASE + OUTCLASS_N):
        rng = random.Random(sd)
        refl = _reflectances()
        rng.shuffle(refl)     # LOAD-BEARING: it must be PASSED (L2's arm-F defect)
        n = len(refl)
        s, ref, test, _ = _run(_alternating(n, OUTCLASS_AMP), reflectances=refl)
        sc = _score(s, ref, test)
        tot_c += sc["l3"]["correct"]; tot_f += sc["l3"]["false"]; tot_n += sc["n"]
        rows.append({"seed": sd, "correct": sc["l3"]["correct"],
                     "false": sc["l3"]["false"], "refused": sc["l3"]["refused"],
                     "l2_correct": sc["l2"]["correct"],
                     "corroborated": sc["corroborated_locales"],
                     "codebook_size": l3w.n_identities(s)})
    return {"seeds": [OUTCLASS_BASE, OUTCLASS_BASE + OUTCLASS_N - 1],
            "amp": OUTCLASS_AMP, "surfaces": tot_n, "correct": tot_c,
            "false": tot_f, "recognized_frac": round(tot_c / max(tot_n, 1), 4),
            "per_seed": rows}


def arm_H_cost():
    """H: THE COST — correct rows corroboration ALSO refuses. Reported."""
    n = len(_reflectances())
    out = []
    for rhos in HEADLINE:
        s, ref, test, _ = _run(_field(n, rhos))
        sc = _score(s, ref, test)
        out.append({"rhos": list(rhos),
                    "l2_correct": sc["l2"]["correct"],
                    "l3_correct": sc["l3"]["correct"],
                    "correct_rows_lost": sc["disagree_were_correct"],
                    "rows_l2_admits_l3_refuses": sc["disagree_l2_admits_l3_refuses"]})
    return {"per_field": out,
            "total_correct_rows_lost": sum(o["correct_rows_lost"] for o in out)}


def arm_X_offday():
    """X: the flag at its default 0 — L3 fully inert, T3/L1/L2 unmoved."""
    n = len(_reflectances())
    s, ref, test, _ = _run(_field(n, (1.008,) * 3), flag_l3=0.0)
    wrote = []
    for nid in test["surface_ids"]:
        a = s.node(nid)["attrs"]
        for k in a:
            if k.startswith("l3_") or k.startswith("l3l_"):
                if k in ("l3_id", "l3_resid", "l3l_id", "l3l_resid"):
                    if float(a[k]) != -1.0:
                        wrote.append(k)
                elif isinstance(a[k], str):
                    if a[k]:
                        wrote.append(k)
                elif float(a.get(k, 0.0)) != 0.0:
                    wrote.append(k)
    sc = _score(s, ref, test)
    s2, ref2, test2, _ = _run([(3.0, 3.0, 3.0)] * n, flag_l3=0.0)
    sc2 = _score(s2, ref2, test2)
    return {"l3_attrs_written_when_off": sorted(set(wrote)),
            "L2_correct_under_field_flag_off": sc["l2"]["correct"],
            "T3_correct_at_gain3_flag_off": sc2["t3"]["correct"],
            "L1_correct_at_gain3_flag_off": sc2["l1"]["correct"],
            "L2_correct_at_gain3_flag_off": sc2["l2"]["correct"],
            "identities": l3w.n_identities(s)}


def main():
    t0 = time.time()
    res = {
        "rung": "L3 — GLOBAL ILLUMINANT INFERENCE (pool + corroborate the anchor)",
        "prereg": "VISION_LIGHTING_L3_PREREG.md (d6c35a1f)",
        "engine": provenance_line(),
        "lattice_step_bound": LATTICE_STEP,
        "B_no_regression": arm_B_no_regression(),
        "A_D_leak_and_pooling_ablation": arm_A_D_leak(),
        "E_v4_dissociation": arm_E_v4_dissociation(),
        "F_outclass_floor": arm_F_floor(),
        "H_cost": arm_H_cost(),
        "X_off_day": arm_X_offday(),
        "elapsed_s": None,
    }
    res["elapsed_s"] = round(time.time() - t0, 1)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "lighting_l3_measure.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")

    B = res["B_no_regression"]; AD = res["A_D_leak_and_pooling_ablation"]
    E = res["E_v4_dissociation"]; F = res["F_outclass_floor"]
    print(res["engine"])
    print(f"A  LEAK        : {AD['A_leak_WITH_pooling']}/{AD['surfaces']} "
          f"({AD['A_rate']*100:.2f}%) WITH pooling   <- headline")
    print(f"D  ABLATED     : {AD['D_leak_POOLING_ABLATED']}/{AD['surfaces']} "
          f"({AD['D_rate']*100:.2f}%) pooling REMOVED (= L2, same graph), "
          f"codebook={AD['codebook_size']}")
    print(f"   at resid==0 : L2 {AD['l2_leaks_at_residual_exactly_zero']}, "
          f"L3 {AD['l3_leaks_at_residual_exactly_zero']}")
    print(f"B  NO-REGRESS  : fields L3 {B['L3_correct_under_fields']}/60 "
          f"(L2 {B['L2_correct_under_fields']}/60), false {B['false_under_fields']}; "
          f"uniform L3 {B['L3_correct_uniform']}/96 (L2 {B['L2_correct_uniform']}/96), "
          f"T3 {B['T3_correct_uniform']}/96 L1 {B['L1_correct_uniform']}/96")
    for c in B["headline_fields"]:
        print(f"     rho={c['rhos']} x{c['range']}: L3={c['l3']['correct']} "
              f"L2={c['l2']['correct']} false={c['l3']['false']} "
              f"corr={c['corroborated_locales']}/13 "
              f"ncand={c['ncand']['min']}/{c['ncand']['median']}/{c['ncand']['max']} "
              f"resid<={c['resid']['max']} G={c['scene_estimate'].get('GL')}")
    print(f"E  V4 LESION   : CONSTANCY lesioned {E['CONSTANCY_lesioned_correct_under_fields']}/60 "
          f"vs intact {E['CONSTANCY_intact_correct_under_fields']}/60;  "
          f"DISCRIMINATION at reference lesioned "
          f"{E['DISCRIMINATION_lesioned_correct_at_reference']}/{E['n_reference']} "
          f"false {E['DISCRIMINATION_lesioned_false_at_reference']}")
    print(f"F  out-of-cls  : {F['correct']}/{F['surfaces']} recognized, "
          f"{F['false']} false")
    print(f"H  cost        : {res['H_cost']['total_correct_rows_lost']} correct rows lost")
    print(f"X  off-day     : wrote {res['X_off_day']['l3_attrs_written_when_off']}")
    print("wrote", out, f"({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
