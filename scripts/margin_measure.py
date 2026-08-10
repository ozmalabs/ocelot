"""RUNG L1c — THE MARGIN INSTRUMENT (a DERIVED NEGATIVE) and the T1 RECORD CORRECTION.

Confirmatory runner for VISION_MARGIN_PREREG.md (committed BEFORE this run at
`ebb3daec`). Writes results/margin_measure.json.

PART A audits SIX rival margin bounds and rejects each BY MEASUREMENT, then measures
the bound that DOES fall out (`eta`, the codebook's own self-rounding residual).
PART B measures the corrected attribution of T1's landed result.
PART C runs the instrument's arms.

Every DECISION lives in the `vision_margin` seed rules (mg_eta / mg_admit /
mg_ambiguous / mg_none) and the held Rust Terms. The measurement code below reads
residuals back through `native.evaluate` of HELD terms — that is instrumentation, the
same idiom `uniqueness_measure.py` uses for its audit — and never decides anything the
graph is responsible for. NO new Rust.
"""
from __future__ import annotations
import sys, os, json, math, random

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
_PROV = provenance_line()

from substrate.seed_loader import manifest_for
from domains import margin_world as mw
import continuous_pose_measure as cpm

BOUND = math.sqrt(2) / 2          # T1's own bound — INHERITED, never re-derived
FLOOR_BASE, FLOOR_N = 51000, 100  # pre-registered, never previously used
DISAGREE_BASE, DISAGREE_N = 51100, 100

# The per-candidate residual, free in `cpts`/`opts`/`angles` — the SAME term shape
# `cp_recognize` scores (uniqueness_measure.py uses this idiom for its own audit).
RESID = {"type": "MinOver", "source": {"type": "Var", "name": "angles"}, "var_name": "t",
         "value": {"type": "PointSetDist",
                   "a": {"type": "MapList", "source": {"type": "Var", "name": "cpts"},
                         "var_name": "p",
                         "value": {"type": "Rotate", "vec": {"type": "Var", "name": "p"},
                                   "angle": {"type": "Var", "name": "t"}}},
                   "b": {"type": "Var", "name": "opts"}}, "default": None}


def _resid(native, cpts, opts, angles=None):
    return float(native.evaluate(RESID, {"angles": angles or cpm.GRID,
                                         "cpts": cpts, "opts": opts}))


def _selfviews(scale):
    """The rounded self-renders — STIMULUS GENERATION, the same `observe()` path every
    observation uses, at the agent's own cp_angles. The MAX over these is taken by the
    `mg_eta` SEED RULE, not here."""
    return {nm: [cpm.observe(cpm.OBJ[nm], scale, d) for d in range(0, 360, 2)]
            for nm in cpm.NAMES}


def _boot(scale, *, margin=1.0):
    """T1's own boot, plus the vision_margin seed, the codebook self-renders and the flag."""
    s, ag, native = cpm._boot(scale)
    native.load_seed_manifest(manifest_for("vision_margin"), ag)
    s.add_node("Seed", {"id": "vision_margin", "version": "1.0.0"})
    mw.install_codebook(s, ag, _selfviews(scale))
    mw.set_flag(s, margin=margin)
    native.run_rules()      # lets mg_eta derive eta once, before any observation
    return s, ag, native


def _ranked(native, scale, obs):
    return sorted((_resid(native, cpm.dense(cpm.OBJ[c], scale), obs), c) for c in cpm.NAMES)


def _rows(native, scale):
    """T1's 63 headline rows at this resolution."""
    out = []
    for nm in cpm.NAMES:
        for deg in range(5, 90, 10):
            obs = cpm.observe(cpm.OBJ[nm], scale, deg)
            out.append({"true": nm, "deg": deg, "obs": obs,
                        "ranked": _ranked(native, scale, obs)})
    return out


def _med(v):
    return sorted(v)[len(v) // 2]


# ------------------------------- PART A — the derivation -------------------------------
def part_A():
    out = {}
    for scale in (1, 2, 4):
        s, ag, native = _boot(scale)
        R = _rows(native, scale)
        margins = [r["ranked"][1][0] - r["ranked"][0][0] for r in R]
        ratios = [r["ranked"][0][0] / r["ranked"][1][0] for r in R]
        eta = {c: mw.eta_of(s, c) for c in cpm.NAMES}       # READ BACK from the graph

        # M5 — the codebook's packing radius (the colour rung's derivation transplanted)
        D = {(a, b): _resid(native, cpm.dense(cpm.OBJ[a], scale), cpm.dense(cpm.OBJ[b], scale))
             for a in cpm.NAMES for b in cpm.NAMES if a != b}
        rad = {c: 0.5 * min(D[(c, o)] for o in cpm.NAMES if o != c) for c in cpm.NAMES}
        cert = [(r["ranked"][0][0] <= rad[r["ranked"][0][1]], r["ranked"][0][1] == r["true"])
                for r in R]

        # M4 — the residual's own angle-grid jitter (2 deg vs 0.125 deg)
        fine = [math.radians(d / 8.0) for d in range(0, 360 * 8)]
        jit = [abs(_resid(native, cpm.dense(cpm.OBJ[c], scale), r["obs"])
                   - _resid(native, cpm.dense(cpm.OBJ[c], scale), r["obs"], fine))
               for r in R[::7] for c in cpm.NAMES]

        # A7 — candidate counts inside sqrt(2)/2 vs inside the DERIVED eta
        n_b = [sum(1 for d, _ in r["ranked"] if d <= BOUND) for r in R]
        n_e = [sum(1 for d, c in r["ranked"] if d <= eta[c]) for r in R]

        out[f"s={scale}"] = {
            "n": len(R),
            "wrong_ids": sum(1 for r in R if r["ranked"][0][1] != r["true"]),
            "M1_rows_surviving_margin_sqrt2_2": sum(1 for m in margins if m >= BOUND),
            "M2_median_margin": round(_med(margins), 4),
            "M3_exact_ties": sum(1 for m in margins if m == 0.0),
            "M4_median_anglegrid_jitter": round(_med(jit), 6),
            "M4_max_anglegrid_jitter": round(max(jit), 6),
            "M5_packing_radius_min_max": [round(min(rad.values()), 4), round(max(rad.values()), 4)],
            "M5_rows_certified": sum(1 for c, _ in cert if c),
            "M5_certified_AND_WRONG": sum(1 for c, ok in cert if c and not ok),
            "M6_max_ratio_d1_d2": round(max(ratios), 4),
            "A7_eta_per_shape": {c: round(eta[c], 4) for c in sorted(eta)},
            "A7_eta_max_overall": round(max(eta.values()), 4),
            "A7_eta_le_sqrt2_2_for_every_shape": all(v <= BOUND + 1e-12 for v in eta.values()),
            "A7_ncand_in_sqrt2_2_min_med_max": [min(n_b), _med(n_b), max(n_b)],
            "A7_ncand_in_eta_min_med_max": [min(n_e), _med(n_e), max(n_e)],
        }
    return out


# --------------------------- PART B — the T1 record correction ---------------------------
def part_B():
    out = {}
    for scale in (1, 4):
        s, ag, native = _boot(scale)
        R = _rows(native, scale)
        eta = {c: mw.eta_of(s, c) for c in cpm.NAMES}
        uniq_in_bound = sum(1 for r in R
                            if sum(1 for d, _ in r["ranked"] if d <= BOUND) == 1)
        n_e = [sum(1 for d, c in r["ranked"] if d <= eta[c]) for r in R]
        out[f"s={scale}"] = {
            "n": len(R),
            "B1_rows_bound_determined_under_T1s_OWN_sqrt2_2": uniq_in_bound,
            "B2_bound_determined_under_derived_eta": sum(1 for k in n_e if k == 1),
            "B2_ranking_only_under_derived_eta": sum(1 for k in n_e if k >= 2),
            "B2_none_under_derived_eta": sum(1 for k in n_e if k == 0),
        }
    return out


# ------------------------------ PART C — the instrument ------------------------------
def _drive(s, ag, native, obs):
    o = s.add_node("Observation", {"points": obs, "status": "cp_decoded"})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return at.get("status"), at.get("covered_by"), mw.verdict(s, o)


def part_C():
    out = {}
    for scale in (1, 4):
        s, ag, native = _boot(scale)
        adm_wrong = amb = adm = none = 0
        ident = mismatch = 0
        for nm in cpm.NAMES:
            for deg in range(5, 90, 10):
                st, cov, v = _drive(s, ag, native, cpm.observe(cpm.OBJ[nm], scale, deg))
                adm += int(v["mg_status"] == "mg_admitted")
                amb += int(v["mg_status"] == "mg_ambiguous")
                none += int(v["mg_status"] == "mg_none")
                adm_wrong += int(v["mg_status"] == "mg_admitted" and v["mg_covered_by"] != nm)
                ident += int(v["mg_status"] == "mg_admitted" and v["mg_covered_by"] == cov)
                mismatch += int(v["mg_status"] == "mg_admitted" and v["mg_covered_by"] != cov)
        out[f"C1_C2_C3_s={scale}"] = {
            "admitted": adm, "ambiguous": amb, "none": none,
            "C1_admitted_AND_WRONG": adm_wrong,
            "C2_admitted_id_byte_identical_to_T1": ident,
            "C2_admitted_id_MISMATCH_vs_T1": mismatch,
        }

    # C3 — untransformed objects at s=4
    s, ag, native = _boot(4)
    unt = sum(1 for nm in cpm.NAMES
              if _drive(s, ag, native, cpm.dense(cpm.OBJ[nm], 4))[2]["mg_status"] == "mg_admitted")
    out["C3_untransformed_admitted"] = {"admitted": unt, "total": len(cpm.NAMES)}

    # C4 — FLOOR, fresh seeds 51000-51099 (ENTAILED: eta <= sqrt(2)/2 => admission subset)
    s, ag, native = _boot(4)
    f_adm = 0
    for i in range(FLOOR_N):
        rng = random.Random(FLOOR_BASE + i)
        cells = set()
        while len(cells) < 5:
            cells.add((rng.randint(0, 7), rng.randint(0, 7)))
        _, _, v = _drive(s, ag, native, cpm.observe(list(cells), 4, 0))
        f_adm += int(v["mg_status"] == "mg_admitted")
    out["C4_floor"] = {"seeds": [FLOOR_BASE, FLOOR_BASE + FLOOR_N - 1],
                       "admitted": f_adm, "total": FLOOR_N}

    # C5 — DISAGREEMENT, fresh seeds 51100-51199: the GRAPH's mg_ncand vs an
    # independently re-derived count on the same rows.
    s, ag, native = _boot(4)
    eta = {c: mw.eta_of(s, c) for c in cpm.NAMES}
    dis = 0
    hist = {}
    for i in range(DISAGREE_N):
        rng = random.Random(DISAGREE_BASE + i)
        cells = set()
        while len(cells) < 5:
            cells.add((rng.randint(0, 7), rng.randint(0, 7)))
        obs = cpm.observe(list(cells), 4, 0)
        _, _, v = _drive(s, ag, native, obs)
        k = sum(1 for d, c in _ranked(native, 4, obs) if d <= eta[c])
        hist[v["mg_status"]] = hist.get(v["mg_status"], 0) + 1
        dis += int(v["mg_status"] != "" and v["mg_ncand"] != k)
    out["C5_disagreement"] = {"seeds": [DISAGREE_BASE, DISAGREE_BASE + DISAGREE_N - 1],
                              "disagreements": dis, "total": DISAGREE_N,
                              "status_histogram": hist}
    return out


# ------------------------------- X — the OFF day (§9) -------------------------------
def arm_X():
    s, ag, native = cpm._boot(4)
    native.load_seed_manifest(manifest_for("vision_margin"), ag)
    mw.install_codebook(s, ag, _selfviews(4))       # data present, flag NOT set (default 0)
    native.run_rules()
    st, cov, v = _drive(s, ag, native, cpm.observe(cpm.OBJ["F"], 4, 35))
    etas = [mw.eta_of(s, c) for c in cpm.NAMES]
    return {"T1_status": st, "T1_covered_by": cov,
            "mg_attributes_written": [k for k, val in v.items() if val not in ("", 0)],
            "mg_eta_derived_anywhere": [e for e in etas if e >= 0.0],
            "OFF_DAY_CLEAN": v["mg_status"] == "" and all(e < 0.0 for e in etas)
                             and st == "recognized_continuous" and cov == "F"}


def run():
    return {"provenance": _PROV, "bound_sqrt2_2": round(BOUND, 6),
            "PART_A_derivation": part_A(),
            "PART_B_T1_attribution": part_B(),
            "PART_C_instrument": part_C(),
            "X_off_day": arm_X()}


def main():
    res = run()
    outp = os.path.join(_ROOT, "results", "margin_measure.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as f:
        json.dump(res, f, indent=2)
    print(_PROV)
    print("== PART A — the derivation (rivals REJECTED by measurement) ==")
    for k, a in res["PART_A_derivation"].items():
        print(f"  {k}: M1 survive={a['M1_rows_surviving_margin_sqrt2_2']}/{a['n']}  "
              f"M2 med margin={a['M2_median_margin']}  M3 ties={a['M3_exact_ties']}  "
              f"M4 jitter med={a['M4_median_anglegrid_jitter']}  "
              f"M5 cert={a['M5_rows_certified']} (WRONG {a['M5_certified_AND_WRONG']})  "
              f"M6 max ratio={a['M6_max_ratio_d1_d2']}")
        print(f"       A7 ncand in sqrt2/2 {a['A7_ncand_in_sqrt2_2_min_med_max']} "
              f"-> in eta {a['A7_ncand_in_eta_min_med_max']}   eta<=sqrt2/2: "
              f"{a['A7_eta_le_sqrt2_2_for_every_shape']}")
    print("== PART B — the T1 record correction ==")
    for k, b in res["PART_B_T1_attribution"].items():
        print(f"  {k}: bound-determined under T1's OWN bound = "
              f"{b['B1_rows_bound_determined_under_T1s_OWN_sqrt2_2']}/{b['n']}   "
              f"under derived eta = {b['B2_bound_determined_under_derived_eta']} "
              f"(ranking-only {b['B2_ranking_only_under_derived_eta']}, "
              f"none {b['B2_none_under_derived_eta']})")
    print("== PART C — the instrument ==")
    for k, c in res["PART_C_instrument"].items():
        print(f"  {k}: {c}")
    print("== X off-day:", res["X_off_day"]["OFF_DAY_CLEAN"])
    print("wrote", outp)
    return res


if __name__ == "__main__":
    main()
