"""Phase 5 boundary / failure analysis (RQ5).  POST-HOC, EXPLANATORY ONLY.

Run from the repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_broad_boundary

Every quantity here was chosen AFTER the Arm B eye outputs were seen.  None of it
changes a stimulus, decoder, anchor, threshold, split or verdict; it only
explains the frozen results.  No eye is built: counterfactual "eyes" are
computed from the forward model and the documented eye parameters (Gaussian
capture + Naka-Rushton + first-order adaptation, mechanism table stages 1-3),
whose replica matches the real eye to <= 7.2e-16 on all unadapted inputs
(Arm B, re-checked by scripts/marys_room_broad_audit.py).

Sections
  1. 2x2 factorial decomposition of the theory->eye angle:
       sensitivity {CIE 2006 2deg, eye Gaussians} x transduction {linear, Naka-Rushton}.
  2. Metamer breaking attributed to sensitivity (CIE+NR keeps CIE metamers).
  3. Sign rule vs perceptual truth along the spectrum (cone-opponent zero vs unique hues).
  4. Adaptation: mechanism replay and whether an adapted CIE model anticipates the flips.
  5. Quantisation-method / photon-conversion sensitivity (replica, not eye runs).
  6. Summary of wrong-observer / wrong-optics / Poisson from the frozen results.
Writes results/marys_room_broad_boundary.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from domains import spectral_forward as sf
from scripts.marys_room_broad_theory import spd_from_recipe

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUT = R / "marys_room_broad_boundary.json"
CORE = {"mono_sweep", "boundary_dense", "illuminant", "reflectance", "metamer", "eyelid"}
GAUSS = {"l": (564.0, 42.0), "m": (534.0, 36.0), "s": (420.0, 28.0)}
HALF = 512.0
ADAPT_RATE = 0.12
WL = sf.grid(1)
LMS_CIE = sf.load_lms("2deg", step=1)          # energy-based, peak-normalised CVRL 2deg (Arm A)
POSTHOC_POISSON_SEED0 = 77_000_000             # post-hoc seeds, disjoint from A1 seeds


def ang(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu == 0 or nv == 0:
        return None
    c = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def opp(c):
    return (c[0] - c[1], c[2] - 0.5 * (c[0] + c[1]))


def nr(c, a=(0.0, 0.0, 0.0)):
    return tuple(x / (x + HALF + ai) for x, ai in zip(c, a))


def gauss_caught_from_packets(pk):
    return tuple(sum(n * math.exp(-0.5 * ((w - cc) / bw) ** 2) for w, n in pk) for cc, bw in GAUSS.values())


def gauss_caught_expected(spd):
    q = sf.expected_quanta(spd)
    return tuple(float(np.sum(q * np.exp(-0.5 * ((WL - cc) / bw) ** 2))) for cc, bw in GAUSS.values())


def cie_caught_expected(spd, quantal_peak=False):
    """CIE cone catch in eye-quanta units.  Default: QUANTA_SCALE * (Arm A LMS),
    i.e. sum_i q_i * lbar(l_i) * 560/l_i -- the energy-peak-normalised fundamentals
    read as a per-quantum sensitivity referenced at 560 nm.  Variant
    quantal_peak=True: per-quantum sensitivity lbar/l renormalised to peak 1 per
    cone (a per-cone constant rescale)."""
    q = sf.expected_quanta(spd)
    out = []
    for k in range(3):
        sens = LMS_CIE[:, k] * sf.LAMBDA_REF_NM / WL
        if quantal_peak:
            sens = sens / sens.max()
        out.append(float(np.sum(q * sens)))
    return tuple(out)


def summ(v):
    v = [x for x in v if x is not None]
    if not v:
        return {"n": 0}
    a = np.asarray(v)
    return {"n": len(v), "median": float(np.median(a)), "mean": float(a.mean()),
            "p90": float(np.percentile(a, 90)), "max": float(a.max())}


def decode(v, anchors):
    if v[0] == 0 and v[1] == 0:
        return "undecided"
    return min(anchors, key=lambda k: (ang(v, anchors[k]), k))


def sgn(rg):
    return "reddish" if rg > 0 else ("greenish" if rg < 0 else "undecided")


def main():
    man = json.loads((R / "marys_room_broad_stimuli.json").read_text())
    arma = json.loads((R / "marys_room_broad_armA.json").read_text())
    armb = json.loads((R / "marys_room_broad.json").read_text())
    anchors = {k: tuple(v["unit_direction"]) for k, v in arma["anchors"].items()}
    mstim = {e["id"]: e for e in man["stimuli"]}
    rows = armb["per_stimulus"]
    out = {"experiment": "marys_room_broad_boundary", "status": "POST-HOC explanatory analysis; "
           "chosen after Arm B outputs were seen; changes no frozen quantity or verdict",
           "provenance_of_audited_eye_data": armb["provenance"], "eye_built": False}

    # ----------------------------------------------------------- 1. factorial decomposition
    def four(e, spd, eye_row, quantal_peak=False):
        cc = cie_caught_expected(spd, quantal_peak)
        gc = gauss_caught_expected(spd)
        T = opp(cc)                       # CIE linear  (== Arm A direction up to scale)
        CN = opp(nr(cc))                  # CIE + Naka-Rushton
        GL = opp(gc)                      # Gaussian linear
        EY = (eye_row["eye"]["red_green"], eye_row["eye"]["blue_yellow"])
        return T, CN, GL, EY

    pools = {
        "HELDOUT_core_distinct": [r for r in rows if r["split"] == "heldout" and r["family"] in CORE
                                  and r["duplicate_of"] is None],
        "mono+boundary_near_pm20nm": [r for r in rows if r["family"] in ("mono_sweep", "boundary_dense")
                                      and r["dist_from_rg_zero_nm"] is not None
                                      and abs(r["dist_from_rg_zero_nm"]) <= 20],
        "mono+boundary_far": [r for r in rows if r["family"] in ("mono_sweep", "boundary_dense")
                              and r["dist_from_rg_zero_nm"] is not None and abs(r["dist_from_rg_zero_nm"]) > 20],
    }
    for q in (100, 1000, 10000):
        pools[f"mono+boundary_q{q}"] = [r for r in rows if r["family"] in ("mono_sweep", "boundary_dense")
                                        and r["quanta"] == q]
    dec = {}
    spd_cache = {}
    per_row = {}
    for variant in ("energy_peak", "quantal_peak"):
        dec[variant] = {}
        for pname, prs in pools.items():
            legs = {k: [] for k in ("T_CN_nonlin_on_CIE", "GL_EY_nonlin_on_gauss", "T_GL_sens_linear",
                                    "CN_EY_sens_under_NR", "T_EY_total", "T_CN_GL_triangle_check")}
            lab = {"CN_vs_T_multi_agree": 0, "GL_vs_EY_multi_agree": 0, "n": 0,
                   "CN_sign_eq_T": 0, "GL_sign_eq_EY": 0}
            for r in prs:
                e = mstim[r["id"]]
                if r["id"] not in spd_cache:
                    spd_cache[r["id"]] = spd_from_recipe(e["eye_input"]["recipe"])
                T, CN, GL, EY = four(e, spd_cache[r["id"]], r, variant == "quantal_peak")
                legs["T_CN_nonlin_on_CIE"].append(ang(T, CN))
                legs["GL_EY_nonlin_on_gauss"].append(ang(GL, EY))
                legs["T_GL_sens_linear"].append(ang(T, GL))
                legs["CN_EY_sens_under_NR"].append(ang(CN, EY))
                legs["T_EY_total"].append(ang(T, EY))
                lab["n"] += 1
                lab["CN_vs_T_multi_agree"] += decode(CN, anchors) == decode(T, anchors)
                lab["GL_vs_EY_multi_agree"] += decode(GL, anchors) == decode(EY, anchors)
                lab["CN_sign_eq_T"] += sgn(CN[0]) == sgn(T[0])
                lab["GL_sign_eq_EY"] += sgn(GL[0]) == sgn(EY[0])
                if variant == "energy_peak" and pname == "HELDOUT_core_distinct":
                    per_row[r["id"]] = {"T": T, "CN": CN, "GL": GL, "EY": EY}
            s = {k: summ(v) for k, v in legs.items() if k != "T_CN_GL_triangle_check"}
            med = {k: s[k].get("median") for k in s}
            # Shapley-style attribution on median angles (angles are not additive; descriptive only)
            s["attribution_median_deg"] = {
                "sensitivity": 0.5 * (med["T_GL_sens_linear"] + med["CN_EY_sens_under_NR"]),
                "nonlinearity": 0.5 * (med["T_CN_nonlin_on_CIE"] + med["GL_EY_nonlin_on_gauss"]),
                "total_median": med["T_EY_total"],
            }
            s["labels"] = lab
            dec[variant][pname] = s
    out["factorial_decomposition"] = {
        "definition": "T = CIE 2deg linear catch (Arm A direction); CN = Naka-Rushton(half_sat 512, "
                      "adaptation 0) applied to CIE catch in eye-quanta units; GL = eye Gaussian catch, "
                      "linear, expected quanta; EY = real eye output. Angles in deg between (RG,BY) "
                      "2-vectors. energy_peak: CIE catch = QUANTA_SCALE*ArmA LMS; quantal_peak: per-quantum "
                      "CIE sensitivity renormalised to peak 1 per cone.",
        "variants": dec,
    }

    # RG zero-crossing under each factor (1 nm, 1000 q monochromatic, analytic)
    def zero(fn):
        vals = np.array([fn(w) for w in np.arange(440, 600.001, 0.01)])
        idx = np.where(np.diff(np.sign(vals)) != 0)[0]
        xs = np.arange(440, 600.001, 0.01)
        return [float(xs[i] - vals[i] * (xs[i + 1] - xs[i]) / (vals[i + 1] - vals[i])) for i in idx]
    lms_i = lambda w, k: float(np.interp(w, WL, LMS_CIE[:, k]))
    def cie_c(w, q):
        return tuple(q * lms_i(w, k) * 560.0 / w for k in range(3))
    def g_c(w, q):
        return tuple(q * math.exp(-0.5 * ((w - cc) / bw) ** 2) for cc, bw in GAUSS.values())
    zc = {}
    for q in (100, 1000, 10000):
        zc[f"q{q}"] = {"CIE_linear": zero(lambda w: opp(cie_c(w, q))[0]),
                       "CIE_NR": zero(lambda w: opp(nr(cie_c(w, q)))[0]),
                       "Gauss_linear": zero(lambda w: opp(g_c(w, q))[0]),
                       "Gauss_NR_eye": zero(lambda w: opp(nr(g_c(w, q)))[0]),
                       "BY_CIE_linear": zero(lambda w: opp(cie_c(w, q))[1]),
                       "BY_CIE_NR": zero(lambda w: opp(nr(cie_c(w, q)))[1]),
                       "BY_Gauss_linear": zero(lambda w: opp(g_c(w, q))[1]),
                       "BY_Gauss_NR_eye": zero(lambda w: opp(nr(g_c(w, q)))[1])}
    out["zero_crossings_440_600nm"] = {"note": "L and M share half_sat 512 and adaptation 0, so NR "
                                       "cannot move the RG zero; any RG-zero shift is sensitivity.",
                                       "by_intensity": zc}

    # ----------------------------------------------------------- 2. metamers
    met = []
    by_pair = {}
    for r in rows:
        if r["family"] == "metamer":
            p = mstim[r["id"]]["params"]
            by_pair.setdefault(p["pair_id"], {})[p["member"][0]] = r
    for pid, m in sorted(by_pair.items()):
        res = {"pair_id": pid}
        sp = {k: spd_from_recipe(mstim[m[k]["id"]]["eye_input"]["recipe"]) for k in "ab"}
        vecs = {k: four(None, sp[k], m[k]) for k in "ab"}
        for i, nm in enumerate(("CIE_linear", "CIE_NR", "Gauss_linear", "eye")):
            va, vb = vecs["a"][i], vecs["b"][i]
            res[nm + "_gap_rel"] = math.hypot(va[0] - vb[0], va[1] - vb[1]) / max(math.hypot(*va), 1e-300)
            res[nm + "_gap_angle_deg"] = ang(va, vb)
        res["eye_gap_abs"] = math.hypot(vecs["a"][3][0] - vecs["b"][3][0], vecs["a"][3][1] - vecs["b"][3][1])
        met.append(res)
    out["metamers_attribution"] = {
        "note": "CIE+NR keeps CIE metamers (per-cone monotone map of identical catches); the "
                "Gaussian-linear catch already breaks them, so breaking is a sensitivity effect.",
        "pairs": met}

    # ----------------------------------------------------------- 3. sign rule vs perceptual truth
    def wrong_ranges(sel, key):
        ws = sorted((r["wavelength_nm"], r[key]) for r in sel)
        rngs, cur = [], None
        for w, ok in ws:
            if not ok:
                cur = [w, w] if cur is None else [cur[0], w]
            elif cur is not None:
                rngs.append(cur); cur = None
        if cur is not None:
            rngs.append(cur)
        return rngs
    sp_out = {}
    for q in (100, 1000, 10000):
        sel = [r for r in rows if r["family"] in ("mono_sweep", "boundary_dense") and r["quanta"] == q]
        sp_out[f"q{q}"] = {"n": len(sel),
                           "theory_sign_wrong_nm": wrong_ranges(sel, "theory_sign_correct"),
                           "eye_sign_wrong_nm": wrong_ranges(sel, "eye_sign_correct"),
                           "theory_anchor_wrong_nm": wrong_ranges(sel, "theory_multi_correct"),
                           "eye_anchor_wrong_nm": wrong_ranges(sel, "eye_multi_correct"),
                           "theory_sign_acc": float(np.mean([r["theory_sign_correct"] for r in sel])),
                           "eye_sign_acc": float(np.mean([r["eye_sign_correct"] for r in sel]))}
    out["sign_rule_vs_unique_hues"] = {
        "loci_nm": {"CIE_2deg_LM_zero": [409.16, 554.08], "eye_LM_zero": 547.85,
                    "unique_blue": 478.0, "unique_yellow": 576.3},
        "sampled_wavelengths": "400-700 nm at 5 nm plus 1 nm in 535-574 nm",
        "by_intensity": sp_out}

    # ----------------------------------------------------------- 4. adaptation
    ad = []
    for r in rows:
        if r["family"] != "adaptation":
            continue
        e = mstim[r["id"]]
        af = e["protocol"]["adapting_field"]
        apk = af["packets"]
        a_spd = spd_from_recipe(af["recipe"])
        t_spd = spd_from_recipe(e["eye_input"]["recipe"])
        # replay eye adaptation (Gaussian, integer packets) for 20 epochs
        gc_a = gauss_caught_from_packets(apk)
        a = [0.0, 0.0, 0.0]
        for _ in range(e["protocol"]["adapt_epochs"]):
            a = [ai + ADAPT_RATE * (ci - ai) for ai, ci in zip(a, gc_a)]
        rep_before = r["eye"].get("adaptation_before_test") or r.get("adaptation_before_test")
        gc_t = gauss_caught_from_packets(e["eye_input"]["packets"])
        replay = opp(nr(gc_t, a))
        eye_v = (r["eye"]["red_green"], r["eye"]["blue_yellow"])
        # adapted CIE model (same gain-control mechanism, CIE sensitivities)
        cc_a = cie_caught_expected(a_spd)
        ac = [0.0, 0.0, 0.0]
        for _ in range(e["protocol"]["adapt_epochs"]):
            ac = [ai + ADAPT_RATE * (ci - ai) for ai, ci in zip(ac, cc_a)]
        cie_ad = opp(nr(cie_caught_expected(t_spd), ac))
        cie_lin = opp(cie_caught_expected(t_spd))
        truth = e["truth"]
        ad.append({"id": r["id"], "truth_binary": truth["binary"] if truth["excitation_purity"] >= 0.05 else "achromatic",
                   "replay_max_abs_diff": max(abs(replay[0] - eye_v[0]), abs(replay[1] - eye_v[1])),
                   "adaptation_replay_max_abs_diff": max(abs(x - rep_before[k]) for x, k in zip(a, "lms")),
                   "eye_sign": sgn(eye_v[0]), "theory_unadapted_sign": sgn(cie_lin[0]),
                   "cie_adapted_sign": sgn(cie_ad[0]),
                   "angle_theory_unadapted_eye": ang(cie_lin, eye_v),
                   "angle_cie_adapted_eye": ang(cie_ad, eye_v)})
    scored = [x for x in ad if x["truth_binary"] != "achromatic"]
    out["adaptation"] = {
        "rows": ad,
        "replay_max_abs_diff_eye": max(x["replay_max_abs_diff"] for x in ad),
        "adaptation_state_replay_max_abs_diff": max(x["adaptation_replay_max_abs_diff"] for x in ad),
        "sign_agreement_with_eye": {
            "theory_unadapted": float(np.mean([x["eye_sign"] == x["theory_unadapted_sign"] for x in ad])),
            "cie_adapted_posthoc": float(np.mean([x["eye_sign"] == x["cie_adapted_sign"] for x in ad]))},
        "median_angle_to_eye": {"theory_unadapted": summ([x["angle_theory_unadapted_eye"] for x in ad]),
                                "cie_adapted_posthoc": summ([x["angle_cie_adapted_eye"] for x in ad])},
        "sign_accuracy_vs_truth_scored": {
            "n": len(scored),
            "eye": float(np.mean([x["eye_sign"] == x["truth_binary"] for x in scored])),
            "theory_unadapted": float(np.mean([x["theory_unadapted_sign"] == x["truth_binary"] for x in scored])),
            "cie_adapted_posthoc": float(np.mean([x["cie_adapted_sign"] == x["truth_binary"] for x in scored]))},
    }

    # ----------------------------------------------------------- 5. quantisation method sensitivity
    core = pools["HELDOUT_core_distinct"]
    qs = {}
    methods = [("per_bin", "quantal", None), ("cumulative", "energy", None)] + \
              [("poisson", "quantal", POSTHOC_POISSON_SEED0 + 1000 * s) for s in range(5)]
    base_lab = {r["id"]: decode((r["eye"]["red_green"], r["eye"]["blue_yellow"]), anchors) for r in core}
    for meth, conv, seed in methods:
        tag = f"{meth}/{conv}" + (f"/seed{seed}" if seed is not None else "")
        flips_m = flips_s = zero_out = 0
        angs = []
        corr = n_sc = 0
        for i, r in enumerate(core):
            e = mstim[r["id"]]
            sd = None if seed is None else seed + i      # independent stream per stimulus
            pk = sf.quantize(spd_cache[r["id"]], method=meth, seed=sd, photon_conversion=conv)
            v = opp(nr(gauss_caught_from_packets([(p["wavelength_nm"], p["count"]) for p in pk])))
            ev = (r["eye"]["red_green"], r["eye"]["blue_yellow"])
            zero_out += v == (0.0, 0.0)
            flips_m += decode(v, anchors) != base_lab[r["id"]]
            flips_s += sgn(v[0]) != sgn(ev[0])
            angs.append(ang(v, ev))
            t = e["truth"]
            if t["excitation_purity"] >= 0.05:
                n_sc += 1
                corr += decode(v, anchors) == t["hue4"]
        qs[tag] = {"n": len(core), "zero_vectors": zero_out, "anchor_label_changes": flips_m,
                   "sign_changes": flips_s, "angle_to_cumulative_eye_deg": summ(angs),
                   "anchor_accuracy_HO_core": corr / n_sc, "n_scored": n_sc}
    out["quantisation_sensitivity"] = {
        "note": "replica outputs (exact to 7.2e-16 vs the eye on unadapted inputs) for alternative "
                "packetisations of the same SPDs; reference = frozen cumulative/quantal eye output "
                "(anchor accuracy 0.768). Poisson seeds are post-hoc and disjoint from A1 seeds.",
        "methods": qs}

    # ----------------------------------------------------------- 6. frozen summaries
    out["frozen_summaries"] = {
        "wrong_observer": armb["wrong_observer"]["summary"],
        "wrong_optics": {k: {kk: v for kk, v in armb["wrong_optics"][k].items() if kk != "pairs"}
                         for k in ("lens", "macular")},
        "poisson": [{k: p[k] for k in ("subset", "n_trials", "rg_mean", "rg_sd", "rg_det_z",
                                       "eye_sign_counts", "eye_multi_counts", "angle_to_det_median_deg")}
                    for p in armb["poisson"]],
        "error_vs_distance_pooled": armb["error_vs_distance_from_rg_zero"]["pooled"],
    }
    assert "domains.photon_eye" not in sys.modules
    OUT.write_text(json.dumps(out, indent=1))
    # concise console report
    for v in ("energy_peak", "quantal_peak"):
        for p, s in dec[v].items():
            print(v, p, {k: round(s[k]["median"], 2) for k in s if isinstance(s[k], dict) and "median" in s[k]},
                  {k: round(x, 2) for k, x in s["attribution_median_deg"].items()}, s["labels"])
    print("zero crossings q1000:", zc["q1000"])
    for m_ in met:
        print(m_["pair_id"], {k: (round(x, 4) if x is not None else None) for k, x in m_.items() if k != "pair_id"})
    print("sign ranges:", json.dumps(sp_out["q1000"]))
    print("adaptation:", json.dumps({k: v for k, v in out["adaptation"].items() if k != "rows"}))
    print("quantisation:", json.dumps(qs, indent=0))


if __name__ == "__main__":
    main()
