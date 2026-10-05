"""EXPLORATORY, POST-HOC (not preregistered): aperture-relative minting and
"link vs compress" for the Mary's Room broad study.

Written after Arm C (rate-distortion, P6 not supported) was seen. It changes no
frozen file and no confirmatory verdict. Every analysis grid below is declared
in this file before it is run; nothing is fitted on labels.

Questions
---------
A. APERTURE. Arm C's substrate minter saw one aperture: Cartesian (RG, BY),
   uniform grain 1/s, every dimension resolved (magnitude included). In this
   substrate fuzzy matching IS an aperture quotient (seeds/observer_aperture.json:
   project unresolved dimensions to a constant, quantise resolved ones at grain
   rho, then match literally). Does a colour-science aperture that resolves only
   hue DIRECTION (magnitude quotiented away) let the same exact-match minter
   compress while keeping the task? Is any gain due to minting or to the aperture?

B. LINK. Mary already holds four concept prototypes (the frozen theory anchors,
   built from TRAIN theory before exposure). Code each experienced vector as an
   edge to a held concept plus a residual relative to her own prediction. How many
   bits does exposure add given what she knew, and is the remainder structured
   (calibratable with a few parameters) or unstructured?

Run from repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_aperture_link
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import marys_room_rate_distortion as rd  # runs engine_preamble()

th = rd.th
ROOT = rd.ROOT
OUT = ROOT / "results" / "marys_room_aperture_link_exploratory.json"

# ---- declared grids (fixed before running) ---------------------------------
CART_SCALES = [1, 2, 3, 5, 10, 20, 30, 50, 100, 200]
DIR_GRAINS_DEG = [90, 60, 45, 30, 22.5, 15, 10, 7.5, 5, 3, 2, 1]
DIR_R = 10_000                     # lattice radius for direction prototypes
ANGLE_GRAINS_DEG = [16, 8, 4, 2, 1, 0.5]
FOURIER_K = [0, 1, 2, 3]
FLOAT_BITS = rd.FLOAT_BITS


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wrap(a):
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


def theta(V):
    V = np.asarray(V, float)
    return np.arctan2(V[:, 1], V[:, 0])


def unit_from_theta(t):
    return np.stack([np.cos(t), np.sin(t)], axis=1)


def offset_cells(Z, rrow):
    off = int(np.abs(Z).max()) + 1 if len(Z) else 1
    return rd.cells_from_lattice(Z, off, rrow)


def plug_in_entropy(codes):
    c = Counter(map(tuple, np.atleast_2d(np.asarray(codes)).reshape(len(codes), -1).tolist()))
    p = np.array(list(c.values()), float) / len(codes)
    return float(-(p * np.log2(p)).sum())


def row_summary(r, sc):
    ev = r.pop("_eval")
    return {**r, "task_accuracy": ev["task_accuracy"], "task_wilson95": ev["task_wilson95"],
            "label_fidelity": ev["label_fidelity"], "angle_mean_deg": ev["angle_deg"]["mean"],
            "angle_median_deg": ev["angle_deg"]["median"]}


# ---------------------------------------------------------------- A. aperture
def dir_bins(X, grain_deg):
    nb = int(round(360.0 / grain_deg))
    t = theta(X)
    zero = np.linalg.norm(X, axis=1) == 0
    j = np.floor((t + np.pi) / (2 * np.pi) * nb).astype(int) % nb
    centre = -np.pi + (j + 0.5) * 2 * np.pi / nb
    Z = np.rint(DIR_R * unit_from_theta(centre)).astype(np.int64)
    Z[zero] = 0
    j[zero] = -1
    return nb, j, centre, Z


def aperture_sweep(X_opp, tr, ho, sc):
    N = len(ho)
    rows = []
    # A1 Cartesian, uniform grain, all dimensions resolved (Arm C's aperture family)
    for s in CART_SCALES:
        Ztr, Zho = rd.lattice(X_opp[tr], s), rd.lattice(X_opp[ho], s)
        run = rd.minter_run(offset_cells(Ztr, 0), offset_cells(Zho, 1))
        mc = rd.minter_code(Ztr, Zho, run, s)
        ev = sc.evaluate(mc["rec"])
        rows.append({"aperture": "cartesian", "mint": True, "config": f"s={s}",
                     "k_minted": mc["k"], "n_assigned": mc["n_assigned"],
                     "rate_total": mc["bits_mean"] + mc["model_bits"] / N,
                     "rate_no_model": mc["bits_mean"], "_eval": ev})
    # A2 direction-only aperture: magnitude quotiented to a constant
    for g in DIR_GRAINS_DEG:
        nb, jtr, _, Ztr = dir_bins(X_opp[tr], g)
        _, jho, centre_ho, Zho = dir_bins(X_opp[ho], g)
        run = rd.minter_run(offset_cells(Ztr, 0), offset_cells(Zho, 1))
        cats = run["categories_final"]
        k = len(cats)
        cat_bits = math.ceil(math.log2(k)) if k > 1 else (1 if k == 1 else 0)
        idx_bits = math.ceil(math.log2(nb))
        rec, bits, n_as = [], [], 0
        for reg, c in zip(run["heldout_regions"], centre_ho):
            if k > 0 and reg["sign_dist"] >= 0 and not reg["refused"]:
                n_as += 1
                p = np.array([reg["sign_rg"], reg["sign_by"]], float)
                rec.append(p / max(np.linalg.norm(p), 1.0))
                bits.append(1 + cat_bits)
            else:
                rec.append([math.cos(c), math.sin(c)])
                bits.append(1 + idx_bits)
        ev = sc.evaluate(np.array(rec))
        model_bits = k * idx_bits          # a prototype IS a bin index here
        rows.append({"aperture": "direction", "mint": True, "config": f"grain={g}deg",
                     "k_minted": k, "n_assigned": n_as, "n_bins": nb,
                     "rate_total": float(np.mean(bits)) + model_bits / N,
                     "rate_no_model": float(np.mean(bits)),
                     "model_bits_if_float_prototypes": k * 2 * FLOAT_BITS, "_eval": ev})
        # same aperture, no minting: plain fixed-length bin index
        rec0 = unit_from_theta(centre_ho)
        rows.append({"aperture": "direction", "mint": False, "config": f"grain={g}deg",
                     "rate_total": float(idx_bits), "rate_no_model": float(idx_bits),
                     "_eval": sc.evaluate(rec0)})
    return [row_summary(r, sc) for r in rows]


def op_point(rows, target, key="task_accuracy"):
    out = {}
    for fam in sorted({(r["aperture"], r["mint"]) for r in rows}):
        rr = [r for r in rows if (r["aperture"], r["mint"]) == fam]
        ok = [r for r in rr if r["task_accuracy"] >= target]
        ang = [r for r in rr if r["angle_mean_deg"] <= rd.ANGLE_OP_DEG]
        out[f"{fam[0]}{'+mint' if fam[1] else ''}"] = {
            "acc_op": min(ok, key=lambda r: r["rate_total"]) if ok else None,
            "angle_op": min(ang, key=lambda r: r["rate_total"]) if ang else None,
            "max_task_accuracy": max(r["task_accuracy"] for r in rr)}
    return out


# ---------------------------------------------------------------- B. link
def fourier_design(t, logtd, K):
    cols = [np.ones_like(t)]
    for k in range(1, K + 1):
        cols += [np.cos(k * t), np.sin(k * t)]
    F = np.stack(cols, axis=1)
    return np.hstack([F, F * logtd[:, None]])


def code_angles(resid_tr, resid_ho, g_deg):
    """Fixed-length and plug-in entropy rate for coding an angle residual at grain g."""
    g = math.radians(g_deg)
    lo, hi = resid_tr.min(), resid_tr.max()
    span = max(hi - lo, g)
    nb = max(1, math.ceil(span / g))
    q = np.floor((resid_ho - lo) / g)
    clipped = (q < 0) | (q > nb - 1)
    qc = np.clip(q, 0, nb - 1)
    rec = lo + (qc + 0.5) * g
    err = np.degrees(np.abs(wrap(rec - resid_ho)))
    return {"bits_fixed": math.log2(nb) if nb > 1 else 0.0,
            "bits_entropy_heldout": plug_in_entropy(qc.astype(int)[:, None]),
            "clip_fraction": float(clipped.mean()),
            "angle_err_mean_deg": float(err.mean()), "angle_err_median_deg": float(np.median(err))}


def link_analysis(eye, X_opp, tr, ho, sc, labels):
    rows = eye["per_stimulus"]
    T = np.array([[r["theory"]["rg"], r["theory"]["by"]] for r in rows])
    td = np.array([max(float(r["td"]), 1e-9) for r in rows])
    lnk_T = [r["theory"]["multi"] for r in rows]
    lnk_E = [r["eye"]["multi"] for r in rows]
    truth = labels["hue4"]
    scored = labels["hue_scored"]

    # B1: edge to a held concept
    agree = np.array([lnk_T[i] == lnk_E[i] for i in ho])
    pairs = [(lnk_T[i], lnk_E[i]) for i in ho]
    H_E = plug_in_entropy(np.array([[th.HUE4.index(e) if e in th.HUE4 else 4] for _, e in pairs]))
    H_TE = plug_in_entropy(np.array([[th.HUE4.index(t) if t in th.HUE4 else 4,
                                      th.HUE4.index(e) if e in th.HUE4 else 4] for t, e in pairs]))
    H_T = plug_in_entropy(np.array([[th.HUE4.index(t) if t in th.HUE4 else 4] for t, _ in pairs]))
    sc_idx = [i for i in ho if scored[i]]
    trans = Counter((lnk_T[i] == truth[i], lnk_E[i] == truth[i]) for i in sc_idx)
    pointer_rec = np.array([th.decode(*X_opp[i], sc.anchors) for i in ho], dtype=object)
    anchor_vec = {k: np.array(v["unit_direction"], float) for k, v in sc.anchors.items()}
    rec_ptr = np.array([anchor_vec[d["multi"]] if d["multi"] in anchor_vec else [0.0, 0.0]
                        for d in pointer_rec])
    ev_ptr = sc.evaluate(rec_ptr)
    edge = {
        "codebook": "four frozen theory anchors, built from TRAIN theory before exposure",
        "pointer_bits": 2.0, "codebook_bits_paid_before_exposure": 4 * 2 * FLOAT_BITS,
        "pointer_task_accuracy": ev_ptr["task_accuracy"],
        "pointer_task_accuracy_note": "equals A0 by construction (decoder = nearest anchor)",
        "pointer_angle_mean_deg": ev_ptr["angle_deg"]["mean"],
        "link_agreement_theory_vs_eye": float(agree.mean()), "n": int(len(ho)),
        "H_eye_link_bits": H_E, "H_theory_link_bits": H_T,
        "H_eye_link_given_theory_link_bits": H_TE - H_T,
        "relinks_scored": {"n": len(sc_idx),
                           "T_right_E_right": trans[(True, True)], "T_wrong_E_right": trans[(False, True)],
                           "T_right_E_wrong": trans[(True, False)], "T_wrong_E_wrong": trans[(False, False)]},
        "theory_link_accuracy_rows": sum(lnk_T[i] == truth[i] for i in sc_idx) / len(sc_idx),
        "eye_link_accuracy_rows": sum(lnk_E[i] == truth[i] for i in sc_idx) / len(sc_idx),
    }

    # B2: residual relative to Mary's own prediction, with and without calibration
    ok_tr = [i for i in tr if np.linalg.norm(X_opp[i]) > 0]
    ok_ho = [i for i in ho if np.linalg.norm(X_opp[i]) > 0]
    tE_tr, tE_ho = theta(X_opp[ok_tr]), theta(X_opp[ok_ho])
    tT_tr, tT_ho = theta(T[ok_tr]), theta(T[ok_ho])
    d_tr, d_ho = wrap(tE_tr - tT_tr), wrap(tE_ho - tT_ho)
    Nho = len(ok_ho)
    alone, given, calib = [], [], []
    for g in ANGLE_GRAINS_DEG:
        nb = math.ceil(360 / g)
        qa = np.floor((tE_ho + np.pi) / math.radians(g)).astype(int)
        alone.append({"grain_deg": g, "bits_fixed": math.log2(nb),
                      "bits_entropy_heldout": plug_in_entropy(qa[:, None])})
        given.append({"grain_deg": g, **code_angles(d_tr, d_ho, g)})
    for K in FOURIER_K:
        Ftr = fourier_design(tT_tr, np.log10(td[ok_tr]), K)
        Fho = fourier_design(tT_ho, np.log10(td[ok_ho]), K)
        w, *_ = np.linalg.lstsq(Ftr, d_tr, rcond=None)
        r_tr, r_ho = wrap(d_tr - Ftr @ w), wrap(d_ho - Fho @ w)
        P = Ftr.shape[1]
        per = []
        for g in ANGLE_GRAINS_DEG:
            c = code_angles(r_tr, r_ho, g)
            per.append({"grain_deg": g, **c, "rate_total_fixed": c["bits_fixed"] + P * FLOAT_BITS / Nho})
        calib.append({"K": K, "n_params": P, "param_bits": P * FLOAT_BITS,
                      "residual_heldout_median_deg": float(np.degrees(np.median(np.abs(r_ho)))),
                      "residual_heldout_mean_deg": float(np.degrees(np.mean(np.abs(r_ho)))),
                      "residual_heldout_p90_deg": float(np.degrees(np.percentile(np.abs(r_ho), 90))),
                      "coding": per})
    resid = {
        "n_train": len(ok_tr), "n_heldout": Nho,
        "uncalibrated_residual_heldout_median_deg": float(np.degrees(np.median(np.abs(d_ho)))),
        "uncalibrated_residual_heldout_mean_deg": float(np.degrees(np.mean(np.abs(d_ho)))),
        "code_eye_angle_alone": alone, "code_residual_given_theory": given,
        "code_residual_given_theory_plus_calibration": calib,
        "own_eye_research_bound": {
            "residual": "0 to 7.2e-16 (the documented capture+saturation replica reproduces every unadapted eye output; results/marys_room_broad.json)",
            "parameters": "4 receptors x (centre, bandwidth, half_saturation, dark_current) = 16, plus adapt_rate; opponent weights already in the theory"},
    }
    return edge, resid


# ------------------------------------------------- B3. learn this eye from exposure
# Mary knows the published model CLASS (Gaussian-band capture, Naka-Rushton
# saturation, the opponent transform) but not this eye's parameters. She sees
# only the TRAIN monochromatic exposures' (RG, BY) and fits 7 numbers.
INIT_PARAMS = [566.0, 40.0, 541.0, 40.0, 441.0, 40.0, 500.0]   # CIE 2006 peaks; generic bw / half
NM_ITERS = 4000


def predict_opp(params, packets_list):
    cL, bL, cM, bM, cS, bS, half = params
    out = np.empty((len(packets_list), 2))
    for j, pk in enumerate(packets_list):
        wl = np.array([p[0] for p in pk], float)
        n = np.array([p[1] for p in pk], float)
        act = []
        for c, b in ((cL, bL), (cM, bM), (cS, bS)):
            caught = float((n * np.exp(-0.5 * ((wl - c) / abs(b)) ** 2)).sum())
            act.append(caught / (caught + abs(half)))
        L, M, S = act
        out[j] = (L - M, S - 0.5 * (L + M))
    return out


def nelder_mead(f, x0, iters, step=0.08):
    x0 = np.asarray(x0, float)
    n = len(x0)
    S = [x0] + [x0 * (1 + step * np.eye(n)[i]) for i in range(n)]
    F = [f(x) for x in S]
    for _ in range(iters):
        o = np.argsort(F)
        S, F = [S[i] for i in o], [F[i] for i in o]
        c = np.mean(S[:-1], axis=0)
        xr = c + (c - S[-1]); fr = f(xr)
        if fr < F[0]:
            xe = c + 2 * (c - S[-1]); fe = f(xe)
            S[-1], F[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < F[-2]:
            S[-1], F[-1] = xr, fr
        else:
            xc = c + 0.5 * (S[-1] - c); fc = f(xc)
            if fc < F[-1]:
                S[-1], F[-1] = xc, fc
            else:
                S = [S[0]] + [S[0] + 0.5 * (s - S[0]) for s in S[1:]]
                F = [F[0]] + [f(s) for s in S[1:]]
    i = int(np.argmin(F))
    return S[i], F[i]


def learn_eye(eye, X_opp, tr, ho):
    manifest = json.loads((ROOT / "results" / "marys_room_broad_stimuli.json").read_text())
    by_id = {s["id"]: s for s in manifest["stimuli"]}
    rows = eye["per_stimulus"]

    def packets(i):
        e = by_id[rows[i]["id"]]["eye_input"]
        while "packets" not in e:
            e = by_id[e["identical_to"]]["eye_input"]
        return e["packets"]
    P_tr, P_ho = [packets(i) for i in tr], [packets(i) for i in ho]
    Y_tr, Y_ho = X_opp[tr], X_opp[ho]
    scale = np.abs(Y_tr).max()

    def loss(p):
        return float(((predict_opp(p, P_tr) - Y_tr) ** 2).sum()) / scale ** 2
    p_hat, l_hat = nelder_mead(loss, INIT_PARAMS, NM_ITERS)
    p_hat, l_hat = nelder_mead(loss, p_hat, NM_ITERS)          # one restart from the optimum
    Yh = predict_opp(p_hat, P_ho)
    ok = np.linalg.norm(Y_ho, axis=1) > 0
    ang = np.degrees(np.abs(wrap(theta(Yh[ok]) - theta(Y_ho[ok]))))
    from domains import spectral_forward as sf
    rg = np.linspace(400, 700, 30001)
    tot = predict_opp(p_hat, [[[w, 1000]] for w in rg])[:, 0]
    sgn = np.where(np.diff(np.sign(tot)) != 0)[0]
    zero_pred = [float(rg[i]) for i in sgn]
    return {
        "model_class": "Gaussian-band capture + Naka-Rushton (shared half-saturation) + fixed opponent transform; dark current ignored",
        "fit_on": "TRAIN eye (RG, BY) only: 93 monochromatic exposures; no labels, no receptor activations",
        "init": INIT_PARAMS, "params_hat": {"L": p_hat[0:2].tolist(), "M": p_hat[2:4].tolist(),
                                            "S": p_hat[4:6].tolist(), "half_saturation": float(p_hat[6])},
        "eye_true": {k: list(sf.EYE_RECEPTORS[k][:3]) for k in ("l", "m", "s")},
        "train_loss": l_hat, "n_params": 7, "param_bits": 7 * FLOAT_BITS,
        "heldout_angle_median_deg": float(np.median(ang)), "heldout_angle_mean_deg": float(ang.mean()),
        "heldout_angle_p90_deg": float(np.percentile(ang, 90)), "heldout_angle_max_deg": float(ang.max()),
        "heldout_rel_euclid_median": float(np.median(np.linalg.norm(Yh - Y_ho, axis=1)
                                                     / np.maximum(np.linalg.norm(Y_ho, axis=1), 1e-12))),
        "predicted_rg_zero_nm": zero_pred,
    }


def main():
    eye, X_lms, X_opp, labels, meta = rd.load_rows()
    anchors = json.loads(rd.ARMA.read_text())["anchors"]
    pools = rd.pools_from_meta(meta)
    tr, ho = pools["TRAIN"], pools["HO_core"]
    sc = rd.Scorer(ho, X_opp, labels, anchors)
    target = rd.ACC_FRACTION * sc.A0

    ap_rows = aperture_sweep(X_opp, tr, ho, sc)
    arm_c = json.loads((ROOT / "results" / "marys_room_rate_distortion.json").read_text())
    baselines = {k: v["acc_op_with_model_cost"] for k, v in
                 arm_c["operating_points"]["HO_core"]["per_representation"].items()
                 if k in ("a_raw_LMS", "b_opponent", "d1_VQ_opp")}
    edge, resid = link_analysis(eye, X_opp, tr, ho, sc, labels)
    resid["learned_eye_from_train_exposures"] = learn_eye(eye, X_opp, tr, ho)
    out = {
        "status": "EXPLORATORY, POST-HOC; not preregistered; no frozen file changed",
        "provenance": rd.provenance_line(),
        "utc_timestamp": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "inputs": {p: sha256_file(ROOT / p) for p in (
            "results/marys_room_broad.json", "results/marys_room_broad_armA.json",
            "results/marys_room_rate_distortion.json")},
        "script_sha256": sha256_file(Path(__file__)),
        "pool": "HO_core", "N": int(len(ho)), "A0": sc.A0, "target_accuracy": target,
        "declared": {"cart_scales": CART_SCALES, "dir_grains_deg": DIR_GRAINS_DEG,
                     "angle_grains_deg": ANGLE_GRAINS_DEG, "fourier_K": FOURIER_K},
        "A_aperture": {"rows": ap_rows, "operating_points": op_point(ap_rows, target),
                       "arm_c_baselines_with_model_cost": baselines},
        "B_link": {"edge": edge, "residual": resid},
    }
    OUT.write_text(json.dumps(rd._jsonable(out), indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
