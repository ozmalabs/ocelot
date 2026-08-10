#!/usr/bin/env python3
"""ADVANCED LIGHTING RUNG L3b — THE ANCHOR OF THE ANCHOR (confirmatory run).

Pre-registration: VISION_LIGHTING_L3B_PREREG.md (committed BEFORE this run at
6842c2cd — §3). Every decision — the LEAVE-ONE-OUT pool, the two recorded
deviations, the corroboration, the verdict and the two refusals — is a
`vision_lighting_l3b` RULE. The SurfaceIdentity codebook is T3's integer
`li_mint`, unmodified, reused through L2 and L3.

This runner only CONSTRUCTS reflectance × illuminant-FIELD frames and READS
attrs back (mechanical I/O, §0), TALLYING metrics over them. The ground-truth
`material` is used ONLY here for scoring — NEVER read by a seed rule.

SEVEN arms are read from the SAME graph in the SAME run: T3's `lit_*`, L1's
`l1_*`, L2's `l2_*`, L2's global-anchor `l2g_*`, L3's `l3_*` — which IS L3b's
LEAVE-ONE-OUT ABLATION, being `l3b_recognize` with the corroboration conjunct
swapped back — L3's V4-lesioned `l3l_*`, and L3b's `l3b_*`.

Run from the gamma-substrate dir:
    python scripts/lighting_l3b_measure.py
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
from domains import lighting_l3b_world as l3bw  # noqa: E402

CH = ("L", "M", "S")
LATTICE_STEP = 1.0

# T3/L1/L2/L3's SIX materials, two patches each => members = 2 = m_min => minted.
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

# L2/L3's FIVE pre-registered headline fields, as per-channel rho.
HEADLINE = [(1.006, 1.006, 1.006), (1.008, 1.008, 1.008), (1.010, 1.010, 1.010),
            (1.012, 1.012, 1.012), (1.006, 1.008, 1.010)]
# The UNIFORM gains T3 and L1 landed — the NO-REGRESSION conjunction.
UNIFORM = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
           (1.5, 2.5, 3.3), (2.0, 2.0, 2.0), (3.0, 3.0, 3.0), (4.0, 4.0, 4.0)]

# THE SEED BLOCKS THIS RUNG CONSUMES (prereg §3). 52000-52999 verified CLEAN.
NOISE_BASE, NOISE_N = 52000, 100        # 100 x 13 = 1300, matching L3's arm A
OUTCLASS_BASE, OUTCLASS_N = 52100, 20
OUTCLASS_AMP = 1.10
# The REGRESS exhibition (R2). Deterministic scenes; the block is reserved so no
# later rung can reuse it.
REGRESS_BASE = 52200
REGRESS_KAPPAS = (0.5, 2.0, 3.0, 4.0)
REGRESS_HEADLINE_KAPPA = 2.0            # the PRE-REGISTERED decision point


def _reflectances(include_novel: bool = True) -> list[dict]:
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _scaled(kappa: float) -> list[dict]:
    """The SAME materials with every reflectance scaled by kappa. World physics:
    a DIFFERENT physical scene (reflectances kappa x, illuminant g) that is
    INDISTINGUISHABLE from (reflectances 1 x, illuminant kappa g)."""
    return [{"name": m["name"],
             **{("r" + ch): int(round(m["r" + ch] * kappa)) for ch in CH}}
            for m in _reflectances()]


def _field(n: int, rhos, g0: float = 2.0) -> list[tuple]:
    """A geometric illuminant FIELD: g_ch(x) = g0 · rho_ch^x. World physics."""
    return [tuple(g0 * (rhos[k] ** x) for k in range(3)) for x in range(n)]


def _alternating(n: int, amp: float, g0: float = 2.0) -> list[tuple]:
    """A FAST-VARYING field: it changes by `amp` at EVERY adjacency."""
    return [tuple([g0 * (amp if x % 2 else 1.0)] * 3) for x in range(n)]


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1",
                            "vision_lighting_l2", "vision_lighting_l3",
                            "vision_lighting_l3b"])
    return s, ag


def _build(s, *, test_refl, ref_refl, gains, flag=1.0, flag_l1=1.0, flag_l2=1.0,
           flag_l3=1.0, flag_l3b=1.0):
    """Build reference + test frames and tick to a fixpoint. Mechanical."""
    ref = l3bw.add_frame(s, reflectances=ref_refl, gain=REF_GAIN,
                         is_reference=True, start_sidx=0)
    test = l3bw.add_frame(s, reflectances=test_refl, gain=gains, start_sidx=1000)
    l3bw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.set_flag_l1(s, lighting_l1=flag_l1)
    l2w.set_flag(s, lighting_l2=flag_l2)
    l3w.set_flag(s, lighting_l3=flag_l3)
    l3bw.set_flag(s, lighting_l3b=flag_l3b)
    sweeps = l3bw.tick(s)
    return ref, test, sweeps


def _run(gains, *, reflectances=None, ref_reflectances=None, **flags):
    refl = _reflectances() if reflectances is None else reflectances
    rrefl = refl if ref_reflectances is None else ref_reflectances
    s, _ag = _boot()
    ref, test, sweeps = _build(s, test_refl=refl, ref_refl=rrefl, gains=gains,
                               **flags)
    return s, ref, test, sweeps


def _expected(s, ref) -> dict:
    exp = {}
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        exp.setdefault(meta["name"], int(lw.surf_attr(s, nid, "sidx")))
    return exp


def _score(s, ref, test) -> dict:
    """Per-surface scoring of ALL SEVEN arms over the non-NOVEL surfaces."""
    exp = _expected(s, ref)
    rows = []
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        r = l3bw.recognition(s, nid)
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

    nin = [r["l3b_ncand"] for r in scored if r["l3b_recognized"] == 1]
    res = [r["l3b_resid"] for r in scored if r["l3b_recognized"] == 1]
    # THE DISAGREEMENT SET (prereg arm B'): rows L3 admits and L3b refuses.
    disagree = [r for r in scored
                if r["l3_recognized"] == 1 and r["l3b_recognized"] == 0]
    locs = [l3bw.locale_readout(s, test, i)
            for i in range(len(test["locale_ids"]))]
    return {
        "n": len(scored),
        "l3b": tally("l3b_"), "l3": tally("l3_"), "l2": tally("l2_"),
        "t3": tally("lit_"), "l1": tally("l1_"),
        "disagree_l3_admits_l3b_refuses": len(disagree),
        "disagree_were_correct": sum(1 for r in disagree
                                     if r["l3_id"] == r["expected_id"]),
        "ncand": {"min": min(nin) if nin else None,
                  "median": sorted(nin)[len(nin) // 2] if nin else None,
                  "max": max(nin) if nin else None},
        "resid": {"min": round(min(res), 6) if res else None,
                  "max": round(max(res), 6) if res else None},
        "corroborated_l3b": l3bw.n_corroborated_locales(s, test),
        "corroborated_l3": l3w.n_corroborated_locales(s, test),
        # THE CIRCULARITY, READ OFF THE GRAPH (arm R1) and leave-one-out's own
        # TWIN residual (arm R3).
        "n_dev_cheb_exactly_zero": sum(1 for L in locs if L["dev_cheb"] == 0.0),
        "n_dev_loo_exactly_zero": sum(1 for L in locs if L["dev_loo"] == 0.0),
        "n_corroborated_with_dev_loo_zero": sum(
            1 for L in locs if L["corr_loo"] > 0.5 and L["dev_loo"] == 0.0),
        "max_dev_loo": round(max((L["dev_loo"] for L in locs), default=-1.0), 4),
        "scene_estimate_l3": {k: round(v, 5)
                              for k, v in l3w.scene_estimate(s, test).items()},
        "novel_claimed_l3b": sum(1 for r in novel if r["l3b_recognized"] == 1),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
def arm_B_no_regression():
    """B: L3's crossing and the uniform gains must SURVIVE leave-one-out."""
    n = len(_reflectances())
    fields, uni = [], []
    f_l3b = f_l3 = f_l2 = f_false = 0
    u_l3b = u_l3 = u_false = t3_u = l1_u = 0
    d_head = 0
    for rhos in HEADLINE:
        s, ref, test, sweeps = _run(_field(n, rhos))
        sc = _score(s, ref, test)
        f_l3b += sc["l3b"]["correct"]; f_l3 += sc["l3"]["correct"]
        f_l2 += sc["l2"]["correct"]; f_false += sc["l3b"]["false"]
        d_head += sc["disagree_l3_admits_l3b_refuses"]
        fields.append({"rhos": list(rhos), "range": round(rhos[0] ** (n - 1), 4),
                       "sweeps": sweeps,
                       **{k: v for k, v in sc.items() if k != "rows"}})
    for g in UNIFORM:
        s, ref, test, _ = _run([g] * n)
        sc = _score(s, ref, test)
        u_l3b += sc["l3b"]["correct"]; u_l3 += sc["l3"]["correct"]
        u_false += sc["l3b"]["false"]
        t3_u += sc["t3"]["correct"]; l1_u += sc["l1"]["correct"]
        uni.append({"gain": list(g), **{k: v for k, v in sc.items() if k != "rows"}})
    return {"headline_fields": fields, "uniform_gains": uni,
            "L3b_correct_under_fields": f_l3b, "L3_correct_under_fields": f_l3,
            "L2_correct_under_fields": f_l2,
            "n_fields": 60, "false_under_fields": f_false,
            "L3b_correct_uniform": u_l3b, "L3_correct_uniform": u_l3,
            "n_uniform": 96, "false_uniform": u_false,
            "T3_correct_uniform": t3_u, "L1_correct_uniform": l1_u,
            "B_prime_disagreement_on_headline": d_head}


def arm_A_leak():
    """A: THE LEAK under LEAVE-ONE-OUT. A': the SAME leak with L3's own
    self-including pool — the ABLATION, read off the SAME graph in the SAME tick
    (`l3b_recognize` is `l3_recognize` with the corroboration conjunct swapped,
    so `l3_*` IS this rule with self-membership restored and nothing else
    changed — §13.2).

    The setup is L3's arm A VERBATIM except for the seed block: the REFERENCE
    frame is the six real materials, so the codebook is LIVE with six identities
    and the recognizer is the same one scoring the headline; only the TEST frame
    is noise. `codebook_size` is recorded so the DEAD-ARM distinction (§1.1
    clause 4) is auditable from this file rather than taken on trust.
    """
    l3b_claimed = l3_claimed = tot = minted = 0
    per_seed, leak_rows = [], []
    zero_resid_l3 = zero_resid_l3b = 0
    r1_scenes_with_a_zero_cheb = 0
    r3_corr_with_zero_loo = 0
    disagree_noise = 0
    for sd in range(NOISE_BASE, NOISE_BASE + NOISE_N):
        rng = random.Random(sd)
        noise = [{"name": f"n{i}", "rL": rng.randint(0, 120),
                  "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
                 for i in range(13)]
        s, _ag = _boot()
        ref, test, _ = _build(s, test_refl=noise, ref_refl=_reflectances(),
                              gains=_field(len(noise), (1.008,) * 3))
        c3b = c3 = 0
        for nid in test["surface_ids"]:
            r = l3bw.recognition(s, nid)
            c3b += r["l3b_recognized"]; c3 += r["l3_recognized"]
            tot += 1
            if r["l3_recognized"] == 1 and abs(r["l3_resid"]) < 1e-9:
                zero_resid_l3 += 1
            if r["l3_recognized"] == 1 and r["l3b_recognized"] == 0:
                disagree_noise += 1
            if r["l3b_recognized"] == 1:
                if abs(r["l3b_resid"]) < 1e-9:
                    zero_resid_l3b += 1
                leak_rows.append({"seed": sd, "pos": r["pos"],
                                  "l3b_resid": round(r["l3b_resid"], 6),
                                  "l3b_ncand": r["l3b_ncand"]})
        locs = [l3bw.locale_readout(s, test, i)
                for i in range(len(test["locale_ids"]))]
        if any(L["dev_cheb"] == 0.0 for L in locs):
            r1_scenes_with_a_zero_cheb += 1
        r3_corr_with_zero_loo += sum(1 for L in locs
                                     if L["corr_loo"] > 0.5 and L["dev_loo"] == 0.0)
        l3b_claimed += c3b; l3_claimed += c3
        minted += l3bw.n_identities(s)
        per_seed.append({"seed": sd, "l3b": c3b, "l3": c3,
                         "corr_l3b": l3bw.n_corroborated_locales(s, test),
                         "corr_l3": l3w.n_corroborated_locales(s, test)})
    return {"seeds": [NOISE_BASE, NOISE_BASE + NOISE_N - 1],
            "surfaces": tot, "codebook_size": minted // NOISE_N,
            "DEAD_ARM": (minted // NOISE_N) == 0,
            "A_leak_LEAVE_ONE_OUT": l3b_claimed,
            "A_prime_leak_SELF_INCLUDING_pool_ABLATION": l3_claimed,
            "A_rate": round(l3b_claimed / max(tot, 1), 5),
            "A_prime_rate": round(l3_claimed / max(tot, 1), 5),
            "l3_leaks_at_residual_exactly_zero": zero_resid_l3,
            "l3b_leaks_at_residual_exactly_zero": zero_resid_l3b,
            "B_prime_disagreement_on_noise": disagree_noise,
            "R1_scenes_with_a_zero_dev_cheb_locale": r1_scenes_with_a_zero_cheb,
            "R1_of_scenes": NOISE_N,
            "R3_corroborated_locales_with_dev_loo_exactly_zero": r3_corr_with_zero_loo,
            "leak_rows": leak_rows[:60],
            "corroborated_l3b_mean": round(
                sum(p["corr_l3b"] for p in per_seed) / max(len(per_seed), 1), 3),
            "corroborated_l3_mean": round(
                sum(p["corr_l3"] for p in per_seed) / max(len(per_seed), 1), 3),
            "per_seed_nonzero": [p for p in per_seed if p["l3b"] or p["l3"]][:40]}


def arm_R2_regress():
    """R2: THE REGRESS EXHIBITED — mutual corroboration cannot certify the SET.

    The test frame's reflectances are scaled by kappa with the illuminant left
    alone. That is a DIFFERENT PHYSICAL SCENE which is INDISTINGUISHABLE from
    the unscaled one under a kappa-times illuminant. Every locale's anchor is
    wrong IN THE SAME WAY, so every locale AGREES — and leave-one-out, which
    only ever compares locales to EACH OTHER, is blind to it by construction.

    Measured per kappa: how many locales corroborate, what Ghat the graph
    recovered (against a TRUE gain of 2.0), and whether any identity is false.
    """
    n = len(_reflectances())
    out = []
    for kappa in REGRESS_KAPPAS:
        s, ref, test, _ = _run(_field(n, (1.008,) * 3),
                               reflectances=_scaled(kappa),
                               ref_reflectances=_reflectances())
        sc = _score(s, ref, test)
        locs = [l3bw.locale_readout(s, test, i)
                for i in range(len(test["locale_ids"]))]
        out.append({
            "kappa": kappa,
            "corroborated_l3b": sc["corroborated_l3b"],
            "n_locales": len(locs),
            "max_dev_loo": sc["max_dev_loo"],
            "envelope": len(locs) * LATTICE_STEP + 0.5 + 0.5,
            "ghat_locale0": {("g" + ch): round(locs[0]["g" + ch], 4) for ch in CH},
            "TRUE_gain_at_locale0": 2.0,
            "l3b_correct": sc["l3b"]["correct"], "l3b_false": sc["l3b"]["false"],
            "l3b_refused": sc["l3b"]["refused"], "n": sc["n"],
        })
    head = [o for o in out if o["kappa"] == REGRESS_HEADLINE_KAPPA][0]
    return {"seeds_reserved": [REGRESS_BASE, REGRESS_BASE + len(REGRESS_KAPPAS) - 1],
            "per_kappa": out,
            "HEADLINE_kappa": REGRESS_HEADLINE_KAPPA,
            "HEADLINE_corroborated": head["corroborated_l3b"],
            "HEADLINE_n_locales": head["n_locales"],
            "HEADLINE_false": head["l3b_false"],
            "HEADLINE_ghat_vs_true": [head["ghat_locale0"]["gL"],
                                      head["TRUE_gain_at_locale0"]]}


def arm_F_floor():
    """F: OUT-OF-CLASS floor — FAST-VARYING fields, FRESH seeds 52100-52119."""
    rows = []
    tot_c = tot_f = tot_n = 0
    for sd in range(OUTCLASS_BASE, OUTCLASS_BASE + OUTCLASS_N):
        rng = random.Random(sd)
        refl = _reflectances()
        rng.shuffle(refl)     # LOAD-BEARING: it must be PASSED (L2's arm-F defect)
        n = len(refl)
        s, ref, test, _ = _run(_alternating(n, OUTCLASS_AMP), reflectances=refl)
        sc = _score(s, ref, test)
        tot_c += sc["l3b"]["correct"]; tot_f += sc["l3b"]["false"]; tot_n += sc["n"]
        rows.append({"seed": sd, "correct": sc["l3b"]["correct"],
                     "false": sc["l3b"]["false"], "refused": sc["l3b"]["refused"],
                     "l3_correct": sc["l3"]["correct"],
                     "corroborated_l3b": sc["corroborated_l3b"],
                     "codebook_size": l3bw.n_identities(s)})
    return {"seeds": [OUTCLASS_BASE, OUTCLASS_BASE + OUTCLASS_N - 1],
            "amp": OUTCLASS_AMP, "surfaces": tot_n, "correct": tot_c,
            "false": tot_f, "recognized_frac": round(tot_c / max(tot_n, 1), 4),
            "per_seed": rows}


def arm_X_offday():
    """X: the flag at its default 0 — L3b fully inert, T3/L1/L2/L3 unmoved."""
    n = len(_reflectances())
    s, ref, test, _ = _run(_field(n, (1.008,) * 3), flag_l3b=0.0)
    wrote = []
    for nid in test["surface_ids"]:
        a = s.node(nid)["attrs"]
        for k in a:
            if k.startswith("l3b_"):
                if k in ("l3b_id", "l3b_resid"):
                    if float(a[k]) != -1.0:
                        wrote.append(k)
                elif isinstance(a[k], str):
                    if a[k]:
                        wrote.append(k)
                elif float(a.get(k, 0.0)) != 0.0:
                    wrote.append(k)
    for loc in test["locale_ids"]:
        a = s.node(loc)["attrs"]
        for k in a:
            if k.startswith("l3b_"):
                if k in ("l3b_dev_cheb", "l3b_dev_loo"):
                    if float(a[k]) != -1.0:
                        wrote.append(k)
                elif float(a.get(k, 0.0)) != 0.0:
                    wrote.append(k)
    sc = _score(s, ref, test)
    s2, ref2, test2, _ = _run([(3.0, 3.0, 3.0)] * n, flag_l3b=0.0)
    sc2 = _score(s2, ref2, test2)
    return {"l3b_attrs_written_when_off": sorted(set(wrote)),
            "L3_correct_under_field_flag_off": sc["l3"]["correct"],
            "L2_correct_under_field_flag_off": sc["l2"]["correct"],
            "T3_correct_at_gain3_flag_off": sc2["t3"]["correct"],
            "L1_correct_at_gain3_flag_off": sc2["l1"]["correct"],
            "L2_correct_at_gain3_flag_off": sc2["l2"]["correct"],
            "L3_correct_at_gain3_flag_off": sc2["l3"]["correct"],
            "identities": l3bw.n_identities(s)}


def main():
    t0 = time.time()
    res = {
        "rung": "L3b — THE ANCHOR OF THE ANCHOR (leave-one-out mutual corroboration)",
        "prereg": "VISION_LIGHTING_L3B_PREREG.md (6842c2cd)",
        "engine": provenance_line(),
        "lattice_step_bound": LATTICE_STEP,
        "B_no_regression": arm_B_no_regression(),
        "A_leak_and_ablation": arm_A_leak(),
        "R2_regress_exhibited": arm_R2_regress(),
        "F_outclass_floor": arm_F_floor(),
        "X_off_day": arm_X_offday(),
        "elapsed_s": None,
    }
    res["elapsed_s"] = round(time.time() - t0, 1)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "lighting_l3b_measure.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")

    B = res["B_no_regression"]; A = res["A_leak_and_ablation"]
    R = res["R2_regress_exhibited"]; F = res["F_outclass_floor"]
    print(res["engine"])
    print(f"A  LEAK (LOO)  : {A['A_leak_LEAVE_ONE_OUT']}/{A['surfaces']} "
          f"({A['A_rate']*100:.3f}%)  <- headline")
    print(f"A' ABLATION    : {A['A_prime_leak_SELF_INCLUDING_pool_ABLATION']}/"
          f"{A['surfaces']} ({A['A_prime_rate']*100:.3f}%) self-including pool "
          f"(= L3, same graph), codebook={A['codebook_size']}")
    print(f"R1 CIRCULARITY : {A['R1_scenes_with_a_zero_dev_cheb_locale']}/"
          f"{A['R1_of_scenes']} scenes have a locale at dev_cheb EXACTLY 0")
    print(f"R3 TWIN RESID  : {A['R3_corroborated_locales_with_dev_loo_exactly_zero']} "
          f"corroborated locales at dev_loo EXACTLY 0")
    print(f"B  NO-REGRESS  : fields L3b {B['L3b_correct_under_fields']}/60 "
          f"(L3 {B['L3_correct_under_fields']}/60), false {B['false_under_fields']}; "
          f"uniform L3b {B['L3b_correct_uniform']}/96, "
          f"T3 {B['T3_correct_uniform']}/96 L1 {B['L1_correct_uniform']}/96")
    print(f"B' DISAGREE    : noise {A['B_prime_disagreement_on_noise']} (want >0), "
          f"headline {B['B_prime_disagreement_on_headline']} (want 0)")
    for c in B["headline_fields"]:
        print(f"     rho={c['rhos']} x{c['range']}: L3b={c['l3b']['correct']} "
              f"L3={c['l3']['correct']} false={c['l3b']['false']} "
              f"corr={c['corroborated_l3b']}/13 "
              f"ncand={c['ncand']['min']}/{c['ncand']['median']}/{c['ncand']['max']} "
              f"maxdev_loo={c['max_dev_loo']} zero_cheb={c['n_dev_cheb_exactly_zero']}")
    print("R2 REGRESS     : mutual corroboration cannot certify the SET")
    for o in R["per_kappa"]:
        print(f"     kappa={o['kappa']}: corr={o['corroborated_l3b']}/{o['n_locales']} "
              f"maxdev={o['max_dev_loo']}/{o['envelope']} "
              f"ghat_L={o['ghat_locale0']['gL']} (TRUE {o['TRUE_gain_at_locale0']}) "
              f"correct={o['l3b_correct']} false={o['l3b_false']}")
    print(f"F  out-of-cls  : {F['correct']}/{F['surfaces']} recognized, "
          f"{F['false']} false")
    print(f"X  off-day     : wrote {res['X_off_day']['l3b_attrs_written_when_off']}")
    print("wrote", out, f"({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
