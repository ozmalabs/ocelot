#!/usr/bin/env python3
"""ADVANCED LIGHTING RUNG L2 — SPATIALLY-VARYING ILLUMINANT / RETINEX
(confirmatory run).

Pre-registration: VISION_LIGHTING_L2_PREREG.md (committed BEFORE this run at
f0417465; AMENDMENT 1 committed BEFORE this run at 97eda7f5 — §3). Every
decision — the local anchor, the locale pairing, the field-slowness discovery,
the rendered continuous verdict, the refusal, the candidate count and the
global-anchor ablation — is a `vision_lighting_l2` RULE. The SurfaceIdentity
codebook is T3's integer `li_mint`, unmodified.

This runner only CONSTRUCTS reflectance × illuminant-FIELD frames and READS
attrs back (mechanical I/O, §0), TALLYING metrics over them. The ground-truth
`material` is used ONLY here for scoring — NEVER read by a seed rule.

FOUR arms are read from the SAME graph in the SAME run: T3's exact `lit_*`,
L1's global-continuous `l1_*`, L2's local `l2_*`, and L2's global-anchor
ABLATION `l2g_*`. That is what makes the local-vs-global contrast one
measurement rather than four experiments.

Run from the gamma-substrate dir:
    python scripts/lighting_l2_measure.py
"""
from __future__ import annotations
import json
import os
import random
import sys
import time

# The gamma-substrate ROOT — so `domains` / `substrate` resolve regardless of the
# cwd the runner is invoked from. `engine_preamble()` then handles the ENGINE
# path (§10.1) separately; this insert is only about the Python packages.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402
from domains import lighting_l2_world as l2w  # noqa: E402

CH = ("L", "M", "S")
LATTICE_STEP = 1.0          # the INHERITED falls-out bound (L1's one lattice step)

# T3/L1's SIX materials, two patches each => members = 2 = m_min => minted.
MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
# ONE patch => members = 1 < m_min => NO identity minted. The novel-material floor.
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}

REF_GAIN = (1.0, 1.0, 1.0)

# THE FIVE PRE-REGISTERED HEADLINE FIELDS (prereg §3), as per-channel rho.
HEADLINE = [(1.006, 1.006, 1.006), (1.008, 1.008, 1.008), (1.010, 1.010, 1.010),
            (1.012, 1.012, 1.012), (1.006, 1.008, 1.010)]
# The UNIFORM gains T3 and L1 already landed — the NO-REGRESSION conjunction.
UNIFORM = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
           (1.5, 2.5, 3.3), (2.0, 2.0, 2.0), (3.0, 3.0, 3.0), (4.0, 4.0, 4.0)]
# REPORTED-ONLY probes, named in the prereg.
SLOPE_SWEEP = [1.002, 1.004, 1.006, 1.008, 1.010, 1.012, 1.014, 1.015,
               1.018, 1.020, 1.030, 1.050]
RADIUS_SWEEP = [1, 2, 3]
SHADOW_JUMPS = [1.5, 2.0, 3.0]

NOISE_BASE, NOISE_N = 45440, 100        # ledger block consumed
OUTCLASS_BASE, OUTCLASS_N = 45540, 20   # ledger block consumed
OUTCLASS_AMP = 1.10                     # per-adjacency alternation (prereg §3)


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


def _step(n: int, jump: float, g0: float = 2.0) -> list[tuple]:
    """A DISCONTINUOUS field — a shadow EDGE at the midpoint."""
    return [tuple([g0 * (jump if x >= n // 2 else 1.0)] * 3) for x in range(n)]


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1",
                            "vision_lighting_l2"])
    return s, ag


def _run(gains, *, reflectances=None, radius=1, flag=1.0, flag_l1=1.0,
         flag_l2=1.0, link=True):
    """Boot, build reference + test frames, tick to a fixpoint. Mechanical."""
    refl = _reflectances() if reflectances is None else reflectances
    s, ag = _boot()
    ref = l2w.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                        start_sidx=0, radius=radius)
    test = l2w.add_frame(s, reflectances=refl, gain=gains, start_sidx=1000,
                         radius=radius)
    if link:
        l2w.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.set_flag_l1(s, lighting_l1=flag_l1)
    l2w.set_flag(s, lighting_l2=flag_l2)
    sweeps = l2w.tick(s)
    return s, ref, test, sweeps


def _expected(s, ref) -> dict:
    """material name -> the sid_key T3's li_mint minted it with. Bookkeeping.

    The FIRST surface of a material is the canonical representative li_mint's
    min-sidx guard selects, so its sidx IS the identity's sid_key.
    """
    exp = {}
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        exp.setdefault(meta["name"], int(lw.surf_attr(s, nid, "sidx")))
    return exp


def _score(s, ref, test) -> dict:
    """Per-surface scoring of ALL FOUR arms over the non-NOVEL surfaces."""
    exp = _expected(s, ref)
    rows = []
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        r = l2w.recognition(s, nid)
        e = exp.get(meta["name"], -1)
        rows.append({
            "material": meta["name"], "pos": r["pos"], "expected_id": e,
            "l2_recognized": r["l2_recognized"], "l2_id": r["l2_id"],
            "l2_resid": round(r["l2_resid"], 6), "l2_ncand": r["l2_ncand"],
            "l2_status": r["l2_status"],
            "l2g_recognized": r["l2g_recognized"], "l2g_id": r["l2g_id"],
            "lit_recognized": r["lit_recognized"], "lit_id": r["lit_id"],
            "l1_recognized": r["l1_recognized"], "l1_id": r["l1_id"],
        })
    scored = [r for r in rows if r["material"] != NOVEL["name"]]
    novel = [r for r in rows if r["material"] == NOVEL["name"]]

    def tally(pfx):
        c = sum(1 for r in scored
                if r[pfx + "recognized"] == 1 and r[pfx + "id"] == r["expected_id"])
        f = sum(1 for r in scored
                if r[pfx + "recognized"] == 1 and r[pfx + "id"] != r["expected_id"])
        return c, f, len(scored) - c - f

    l2c, l2f, l2r = tally("l2_")
    gc, gf, gr = tally("l2g_")
    tc, tf, _ = tally("lit_")
    o1c, o1f, _ = tally("l1_")
    nin = [r["l2_ncand"] for r in scored if r["l2_recognized"] == 1]
    res = [r["l2_resid"] for r in scored if r["l2_recognized"] == 1]
    return {
        "n": len(scored),
        "l2": {"correct": l2c, "false": l2f, "refused": l2r},
        "ablation_global_anchor": {"correct": gc, "false": gf, "refused": gr},
        "t3": {"correct": tc, "false": tf},
        "l1": {"correct": o1c, "false": o1f},
        "ncand": {"min": min(nin) if nin else None,
                  "median": sorted(nin)[len(nin) // 2] if nin else None,
                  "max": max(nin) if nin else None},
        "resid": {"min": round(min(res), 6) if res else None,
                  "max": round(max(res), 6) if res else None},
        "slowvar_locales": l2w.n_slowvar_locales(s, test),
        "paired_locales": l2w.n_paired_locales(s, test),
        "novel_claimed": sum(1 for r in novel if r["l2_recognized"] == 1),
        "novel_status": novel[0]["l2_status"] if novel else "",
        "rows": rows,
    }


# ---------------------------------------------------------------------------
def arm_A_and_S():
    """A: spatially-varying invariance. A': where T3/L1 refused. S: slowvar."""
    out, tot_c, tot_f, t3_tot, l1_tot = [], 0, 0, 0, 0
    n = len(_reflectances())
    for rhos in HEADLINE:
        s, ref, test, sweeps = _run(_field(n, rhos))
        sc = _score(s, ref, test)
        tot_c += sc["l2"]["correct"]; tot_f += sc["l2"]["false"]
        t3_tot += sc["t3"]["correct"]; l1_tot += sc["l1"]["correct"]
        out.append({"rhos": list(rhos), "range": round(rhos[0] ** (n - 1), 4),
                    "sweeps": sweeps, **{k: v for k, v in sc.items() if k != "rows"}})
    return {"conditions": out, "total_correct": tot_c, "total_false": tot_f,
            "n": 60, "T3_total_correct": t3_tot, "L1_total_correct": l1_tot}


def arm_C_D():
    """C: ratios load-bearing (ablation ALIVE at uniform gain). D: no regression."""
    n = len(_reflectances())
    uni = []
    tot_c = tot_f = abl_c = 0
    for g in UNIFORM:
        s, ref, test, _ = _run([g] * n)
        sc = _score(s, ref, test)
        tot_c += sc["l2"]["correct"]; tot_f += sc["l2"]["false"]
        abl_c += sc["ablation_global_anchor"]["correct"]
        uni.append({"gain": list(g), **{k: v for k, v in sc.items() if k != "rows"}})
    return {"uniform_conditions": uni, "total_correct": tot_c,
            "total_false": tot_f, "n": 96, "ablation_alive_correct": abl_c}


def arm_E_noise():
    """E: NOISE floor — FRESH seeds 45440-45539, measured TWO ways.

    E1 (the OBVIOUS version) builds BOTH frames from noise. It is reported and
    then DISCOUNTED: 13 random cone triples are all distinct, so no material
    reaches `m_min`=2, `li_mint` mints NOTHING, and every surface is refused
    against an EMPTY codebook. **That is a DEAD-ARM floor (§1.1 clause 4) — a
    perfect score bought by an absent population, not by the mechanism.**

    E2 (the arm that counts) keeps the REFERENCE frame as the six real materials
    — so the codebook is LIVE, six identities minted, and the recognizer is the
    same one scoring 60/60 elsewhere — and makes only the TEST frame noise. Every
    noise surface then faces a live 6-entry codebook and must be refused ON THE
    MERITS. `codebook_size` is recorded on both so the distinction is auditable
    from the results file rather than taken on trust.
    """
    e1_claimed = e1_tot = e1_minted = 0
    e2_claimed = e2_tot = e2_minted = 0
    for sd in range(NOISE_BASE, NOISE_BASE + NOISE_N):
        rng = random.Random(sd)
        noise = [{"name": f"n{i}", "rL": rng.randint(0, 120),
                  "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
                 for i in range(13)]
        n = len(noise)
        s1, _r1, t1, _ = _run(_field(n, (1.008,) * 3), reflectances=noise)
        for nid in t1["surface_ids"]:
            e1_claimed += l2w.recognition(s1, nid)["l2_recognized"]
            e1_tot += 1
        e1_minted += l2w.n_identities(s1)

        # E2 — the LIVE-CODEBOOK version: reference = the real materials.
        s2, ag2 = _boot()
        ref2 = l2w.add_frame(s2, reflectances=_reflectances(), gain=REF_GAIN,
                             is_reference=True, start_sidx=0)
        test2 = l2w.add_frame(s2, reflectances=noise,
                              gain=_field(n, (1.008,) * 3), start_sidx=1000)
        l2w.link_reference(s2, test2, ref2)
        lw.set_flag(s2, lighting=1.0)
        lw.set_flag_l1(s2, lighting_l1=1.0)
        l2w.set_flag(s2, lighting_l2=1.0)
        l2w.tick(s2)
        for nid in test2["surface_ids"]:
            e2_claimed += l2w.recognition(s2, nid)["l2_recognized"]
            e2_tot += 1
        e2_minted += l2w.n_identities(s2)
    return {"seeds": [NOISE_BASE, NOISE_BASE + NOISE_N - 1],
            "E1_both_frames_noise": {
                "surfaces": e1_tot, "claimed": e1_claimed,
                "codebook_size": e1_minted,
                "DEAD_ARM": e1_minted == 0,
                "note": ("DISCOUNTED — the codebook is EMPTY, so this floor is "
                         "bought by an absent population (§1.1 clause 4)")},
            "E2_live_codebook": {
                "surfaces": e2_tot, "claimed": e2_claimed,
                "codebook_size": e2_minted,
                "note": ("THE ARM THAT COUNTS — reference frame is the six real "
                         "materials, so every noise surface faces a LIVE 6-entry "
                         "codebook and is refused on the merits")}}


def arm_F_outclass():
    """F: OUT-OF-CLASS floor — FAST-VARYING fields, FRESH seeds 45540-45559."""
    rows = []
    tot_c = tot_f = tot_n = 0
    for k, sd in enumerate(range(OUTCLASS_BASE, OUTCLASS_BASE + OUTCLASS_N)):
        rng = random.Random(sd)
        refl = _reflectances()
        rng.shuffle(refl)          # the scene LAYOUT is what the seed randomises
        n = len(refl)
        # NOTE: `reflectances=refl` is LOAD-BEARING. The first version of this
        # arm shuffled `refl` and then never passed it, so all 20 seeds ran the
        # IDENTICAL scene and the seed block did nothing — an arm that cannot
        # vary (§1). Caught by the gate disagreeing with the runner.
        s, ref, test, _ = _run(_alternating(n, OUTCLASS_AMP), reflectances=refl)
        sc = _score(s, ref, test)
        tot_c += sc["l2"]["correct"]; tot_f += sc["l2"]["false"]; tot_n += sc["n"]
        rows.append({"seed": sd, "correct": sc["l2"]["correct"],
                     "false": sc["l2"]["false"], "refused": sc["l2"]["refused"],
                     "slowvar_locales": sc["slowvar_locales"],
                     "codebook_size": l2w.n_identities(s)})
    return {"seeds": [OUTCLASS_BASE, OUTCLASS_BASE + OUTCLASS_N - 1],
            "amp": OUTCLASS_AMP, "surfaces": tot_n, "correct": tot_c,
            "false": tot_f, "recognized_frac": round(tot_c / max(tot_n, 1), 4),
            "per_seed": rows}


def arm_X_offday():
    """X: the flag at its default 0 — L2 fully inert, T3 and L1 unmoved."""
    n = len(_reflectances())
    s, ref, test, _ = _run(_field(n, (1.008,) * 3), flag_l2=0.0)
    wrote = []
    for nid in test["surface_ids"]:
        a = s.node(nid)["attrs"]
        for k in a:
            if k.startswith("l2_") or k.startswith("l2g_"):
                if k in ("l2_id", "l2_resid", "l2g_id", "l2g_resid"):
                    if float(a[k]) != -1.0:
                        wrote.append(k)
                elif float(a.get(k, 0.0)) != 0.0:
                    wrote.append(k)
    s2, ref2, test2, _ = _run([(3.0, 3.0, 3.0)] * n, flag_l2=0.0)
    sc2 = _score(s2, ref2, test2)
    return {"l2_attrs_written_when_off": sorted(set(wrote)),
            "identities": l2w.n_identities(s),
            "T3_correct_at_gain3_flag_off": sc2["t3"]["correct"],
            "L1_correct_at_gain3_flag_off": sc2["l1"]["correct"]}


def probes():
    """REPORTED-ONLY probes named in the prereg §3."""
    n = len(_reflectances())
    slope = []
    for rho in SLOPE_SWEEP:
        s, ref, test, _ = _run(_field(n, (rho,) * 3))
        sc = _score(s, ref, test)
        slope.append({"rho": rho, "range": round(rho ** (n - 1), 4),
                      "correct": sc["l2"]["correct"], "false": sc["l2"]["false"],
                      "refused": sc["l2"]["refused"],
                      "slowvar_locales": sc["slowvar_locales"],
                      "ncand_max": sc["ncand"]["max"],
                      "ablation_correct": sc["ablation_global_anchor"]["correct"]})
    radius = []
    for rad in RADIUS_SWEEP:
        for rho in (1.006, 1.010, 1.020):
            s, ref, test, _ = _run(_field(n, (rho,) * 3), radius=rad)
            sc = _score(s, ref, test)
            radius.append({"radius": rad, "rho": rho,
                           "correct": sc["l2"]["correct"],
                           "false": sc["l2"]["false"],
                           "refused": sc["l2"]["refused"]})
    shadow = []
    for j in SHADOW_JUMPS:
        s, ref, test, _ = _run(_step(n, j))
        sc = _score(s, ref, test)
        edge = [r for r in sc["rows"] if abs(r["pos"] - n // 2) <= 1]
        shadow.append({"jump": j, "correct": sc["l2"]["correct"],
                       "false": sc["l2"]["false"], "refused": sc["l2"]["refused"],
                       "slowvar_locales": sc["slowvar_locales"],
                       "near_edge": [{"pos": r["pos"], "rec": r["l2_recognized"],
                                      "resid": r["l2_resid"]} for r in edge]})
    return {"slope_sweep": slope, "radius_sweep": radius, "shadow_edge": shadow}


def main():
    t0 = time.time()
    res = {
        "rung": "L2 — SPATIALLY-VARYING ILLUMINANT (RETINEX)",
        "prereg": "VISION_LIGHTING_L2_PREREG.md (f0417465; AMENDMENT 1 97eda7f5)",
        "engine": provenance_line(),
        "lattice_step_bound": LATTICE_STEP,
        "A_spatially_varying_invariance": arm_A_and_S(),
        "C_D_ablation_and_no_regression": arm_C_D(),
        "E_noise_floor": arm_E_noise(),
        "F_outclass_fast_varying": arm_F_outclass(),
        "X_off_day": arm_X_offday(),
        "probes": probes(),
        "elapsed_s": None,
    }
    res["elapsed_s"] = round(time.time() - t0, 1)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "lighting_l2_measure.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")

    A = res["A_spatially_varying_invariance"]
    CD = res["C_D_ablation_and_no_regression"]
    print(res["engine"])
    print(f"A  headline   : {A['total_correct']}/60 correct, "
          f"{A['total_false']} false   (T3 {A['T3_total_correct']}/60, "
          f"L1 {A['L1_total_correct']}/60 on the SAME graph)")
    for c in A["conditions"]:
        print(f"     rho={c['rhos']} range x{c['range']}: "
              f"correct={c['l2']['correct']} false={c['l2']['false']} "
              f"refused={c['l2']['refused']}  ablation={c['ablation_global_anchor']['correct']}"
              f"  ncand={c['ncand']['min']}/{c['ncand']['median']}/{c['ncand']['max']}"
              f"  resid<= {c['resid']['max']}  slowvar={c['slowvar_locales']}/13")
    print(f"C  ablation   : {sum(c['ablation_global_anchor']['correct'] for c in A['conditions'])}/60 "
          f"under the fields;  ALIVE at uniform gains: {CD['ablation_alive_correct']}/96")
    print(f"D  no-regress : {CD['total_correct']}/96 correct, {CD['total_false']} false")
    E = res["E_noise_floor"]
    print(f"E1 noise(dead): {E['E1_both_frames_noise']['claimed']}/"
          f"{E['E1_both_frames_noise']['surfaces']} claimed, codebook="
          f"{E['E1_both_frames_noise']['codebook_size']}  <- DISCOUNTED, dead arm")
    print(f"E2 noise(LIVE): {E['E2_live_codebook']['claimed']}/"
          f"{E['E2_live_codebook']['surfaces']} claimed, codebook="
          f"{E['E2_live_codebook']['codebook_size']}")
    F = res["F_outclass_fast_varying"]
    print(f"F  out-of-cls : {F['correct']}/{F['surfaces']} recognized, "
          f"{F['false']} false, codebook="
          f"{F['per_seed'][0]['codebook_size']} (LIVE)")
    print(f"X  off-day    : wrote {res['X_off_day']['l2_attrs_written_when_off']}")
    print("wrote", out, f"({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
