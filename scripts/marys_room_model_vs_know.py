"""EXPLORATORY, POST-HOC (not preregistered): "Mary can MODEL her eye; she cannot
KNOW it" — prior predictive, information gained per exposure, and what the
black-and-white room already identifies.

Mary's research gives her the eye's model CLASS (Gaussian-band capture,
Naka-Rushton saturation with a shared half-saturation, the opponent transform)
and population knowledge of human photopigments. It does not give her the seven
numbers of her own eye. This script asks, with everything declared below before
any result is computed:

  T1  MODELLING WITHOUT KNOWING. Under a population prior over her eye's
      parameters, what does Mary predict before any exposure, and where does her
      actual eye fall in that prior?
  T2  KNOWING AS INFORMATION. How many bits does each release exposure add about
      her own eye, and how many exposures until her eye is pinned down?
  T3  WHAT THE ROOM ALREADY GIVES HER. Using only room-legal light (neutral
      surfaces and bare illuminants, plus light through her closed eyelids), how
      much of her eye is identified, and which parameter directions stay
      unknowable until release?

Assumption made explicit: Mary has access to her own experienced state, i.e. the
eye's (RG, BY) output, with Gaussian read-out noise SIGMA per axis. Without some
read-out of her own states nothing about her eye could be learned from exposure.

Nothing here changes a frozen file or a confirmatory verdict. The eye is not
built: the documented capture + saturation replica reproduces every unadapted eye
output to 7.2e-16 (results/marys_room_broad.json), and the observations below are
that replica evaluated at the eye's true parameters.

Run from repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_model_vs_know
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from domains import spectral_forward as sf
from scripts import marys_room_broad_theory as th
from scripts import marys_room_rate_distortion as rd
from scripts.marys_room_aperture_link import nelder_mead

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "marys_room_model_vs_know_exploratory.json"
GRID = sf.grid(1)

# ======================= DECLARATIONS (fixed before running) =================
# Population means of photopigment peaks: Dartnall, Bowmaker & Mollon (1983),
# Proc R Soc B 220:115-130, microspectrophotometry of seven persons.
POP_LMAX = {"l": 558.4, "m": 530.8, "s": 419.0}
# Inter-observer SD of spectral position, Webster & MacLeod (1988) JOSA A
# 5:1722-1735, in wavenumber (cm^-1); converted to nm at the mean peak.
WM_SD_CM1 = {"l": 50.3, "m": 31.9, "s": 45.3}
# Broad alternative: the cell-to-cell MSP spreads of Dartnall et al. (1983).
MSP_SD_NM = {"l": 5.2, "m": 3.5, "s": 3.6}
BW_REL_SD = 0.10            # declared; no literature value for a Gaussian width
HALF_LOG10_MEDIAN = 3.0     # 1000 model quanta ~ the 100 td photopic anchor (A0-b)
HALF_LOG10_SD = 0.5         # declared: half a decade
SIGMAS = [0.005, 0.001, 0.02]   # read-out noise per axis; 0.005 primary (~max Poisson SD 4.4e-3)
PRIMARY_SIGMA = 0.005
N_PRIOR_SAMPLES = 4000
SEED = 20261005
FD_STEP = 1e-5              # relative central-difference step for the Jacobian
NM_ITERS = 6000
ROOM_TD = [10, 30, 100, 300, 1000, 3000]
ROOM_NEUTRALS = list(range(19, 25))           # ColorChecker 19-24, white..black
ROOM_ILLUMINANTS_STRICT = ["E"]
ROOM_ILLUMINANTS_ALL = ["E", "D65", "A"]
EYELID_AMBIENT_TD = [100, 1000, 10000]
EYELID_OD = (sf.EYELID_OD_SHORT, sf.EYELID_OD_LONG)
KNOW_ANGLE_DEG = 0.5        # "knows her eye": held-out predictive median angle below this
KNOW_ZERO_SD_NM = 0.5       # ...and RG-zero posterior SD below this
PARAM_NAMES = ["cL", "bL", "cM", "bM", "cS", "bS", "log10_half"]
# ============================================================================

TRUE_THETA = np.array([sf.EYE_RECEPTORS["l"][0], sf.EYE_RECEPTORS["l"][1],
                       sf.EYE_RECEPTORS["m"][0], sf.EYE_RECEPTORS["m"][1],
                       sf.EYE_RECEPTORS["s"][0], sf.EYE_RECEPTORS["s"][1],
                       math.log10(sf.EYE_RECEPTORS["l"][2])])
assert sf.EYE_RECEPTORS["l"][2] == sf.EYE_RECEPTORS["m"][2] == sf.EYE_RECEPTORS["s"][2]
assert all(sf.EYE_RECEPTORS[k][3] == 0.0 for k in ("l", "m", "s"))


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------- prior
def govardovskii(lmax, lam):
    """A1 visual-pigment template, alpha + beta bands (Govardovskii et al. 2000)."""
    x = lmax / lam
    a = 0.8795 + 0.0459 * math.exp(-((lmax - 300.0) ** 2) / 11940.0)
    alpha = 1.0 / (np.exp(69.7 * (a - x)) + np.exp(28.0 * (0.922 - x))
                   + np.exp(-14.9 * (1.104 - x)) + 0.674)
    lmb = 189.0 + 0.315 * lmax
    bb = -40.5 + 0.195 * lmax
    return alpha + 0.26 * np.exp(-(((lam - lmb) / bb) ** 2))


def gaussian_fit_to_template(lmax):
    t = govardovskii(lmax, GRID)
    t = t / t.max()

    def loss(p):
        return float(((np.exp(-0.5 * ((GRID - p[0]) / abs(p[1])) ** 2) - t) ** 2).sum())
    p, _ = nelder_mead(loss, [lmax, 40.0], 2000)
    return float(p[0]), float(abs(p[1]))


def build_prior(kind):
    mean, sd = [], []
    for k in ("l", "m", "s"):
        c, b = gaussian_fit_to_template(POP_LMAX[k])
        if kind == "population":
            s_c = POP_LMAX[k] ** 2 * 1e-7 * WM_SD_CM1[k]      # nm = lambda^2 * dnu
        else:
            s_c = MSP_SD_NM[k]
        mean += [c, b]
        sd += [s_c, BW_REL_SD * b]
    mean.append(HALF_LOG10_MEDIAN)
    sd.append(HALF_LOG10_SD)
    return np.array(mean), np.array(sd)


# ------------------------------------------------------------- forward model
def count_matrix(packet_lists):
    C = np.zeros((len(packet_lists), len(GRID)))
    for i, pk in enumerate(packet_lists):
        for w, n in pk:
            j = int(round(float(w) - GRID[0]))
            assert abs(GRID[j] - float(w)) < 1e-9, w
            C[i, j] += float(n)
    return C


def forward(C, Theta):
    """(RG, BY) for stimuli C (n x grid) and parameter rows Theta (S x 7) -> (S, n, 2)."""
    Theta = np.atleast_2d(Theta)
    h = 10.0 ** Theta[:, 6]
    act = []
    for r in range(3):
        c, b = Theta[:, 2 * r], np.abs(Theta[:, 2 * r + 1])
        G = np.exp(-0.5 * ((GRID[None, :] - c[:, None]) / b[:, None]) ** 2)
        caught = (C @ G.T).T                                 # S x n
        act.append(caught / (caught + h[:, None]))
    L, M, S = act
    return np.stack([L - M, S - 0.5 * (L + M)], axis=2)


def jacobian(C, theta):
    J = np.empty((C.shape[0] * 2, 7))
    for j in range(7):
        d = FD_STEP * max(abs(theta[j]), 1.0)
        tp, tm = theta.copy(), theta.copy()
        tp[j] += d
        tm[j] -= d
        J[:, j] = (forward(C, tp)[0].ravel() - forward(C, tm)[0].ravel()) / (2 * d)
    return J


def rg_zero(Theta):
    """Monochromatic RG zero (intensity-independent: shared half-saturation)."""
    lam = np.arange(470.0, 620.0, 0.01)
    Theta = np.atleast_2d(Theta)
    out = []
    for t in Theta:
        gL = -0.5 * ((lam - t[0]) / t[1]) ** 2
        gM = -0.5 * ((lam - t[2]) / t[3]) ** 2
        s = np.sign(gL - gM)
        k = np.where(np.diff(s) != 0)[0]
        out.append(float(lam[k[0]]) if len(k) else float("nan"))
    return np.array(out)


def angles(A, B):
    dot = (A * B).sum(-1)
    cr = A[..., 0] * B[..., 1] - A[..., 1] * B[..., 0]
    return np.degrees(np.arctan2(np.abs(cr), dot))


# ------------------------------------------------------------- stimuli
def room_stimuli(illuminants, eyelid):
    recipes = []
    for ill in illuminants:
        for td in ROOM_TD:
            recipes.append(("bare", ill, td, {"kind": "scene", "illuminant": ill, "scene_td": td,
                                              "reflectance": None, "filter": None, "step": 1}))
            for p in ROOM_NEUTRALS:
                recipes.append(("neutral", ill, td, {"kind": "scene", "illuminant": ill, "scene_td": td,
                                                     "reflectance": sf.reflectance_names()[p - 1],
                                                     "filter": None, "step": 1}))
        if eyelid:
            for td in EYELID_AMBIENT_TD:
                recipes.append(("eyelid", ill, td, {
                    "kind": "scene", "illuminant": ill, "scene_td": td, "reflectance": None,
                    "filter": {"kind": "eyelid", "od_short": EYELID_OD[0], "od_long": EYELID_OD[1]},
                    "step": 1}))
    pk = []
    for _, _, _, r in recipes:
        packets = sf.quantize(th.spd_from_recipe(r))
        pk.append([(p["wavelength_nm"], p["count"]) for p in packets])
    return [x[:3] for x in recipes], count_matrix(pk)


def manifest_stimuli():
    eye, X_lms, X_opp, labels, meta = rd.load_rows()
    man = th.load_manifest()
    idx = {s["id"]: s for s in man["stimuli"]}
    pools = rd.pools_from_meta(meta)

    def cm(ids):
        return count_matrix([[(p["wavelength_nm"], p["count"]) for p in th.eye_packets(idx[eye["per_stimulus"][i]["id"]], 0, idx)]
                             for i in ids])
    tr, ho = pools["TRAIN"], pools["HO_core"]
    anchors = json.loads(rd.ARMA.read_text())["anchors"]
    return {"C_train": cm(tr), "C_ho": cm(ho), "X_train": X_opp[tr], "X_ho": X_opp[ho],
            "train_ids": [eye["per_stimulus"][i]["id"] for i in tr],
            "ho_truth": [labels["hue4"][i] for i in ho], "ho_scored": labels["hue_scored"][ho],
            "anchors": anchors}


def decode_multi(V, anchors):
    return [th.decode(float(a), float(b), anchors)["multi"] for a, b in V]


# ------------------------------------------------------------- inference
def gauss_info(J, sigma, prior_sd):
    P0 = np.diag(1.0 / prior_sd ** 2)
    Pd = J.T @ J / sigma ** 2
    Ppost = P0 + Pd
    sign, logdet_post = np.linalg.slogdet(Ppost)
    bits = 0.5 * (logdet_post - np.log(np.diag(P0)).sum()) / math.log(2)
    cov = np.linalg.inv(Ppost)
    # directions in prior-whitened space the data leave least constrained
    W = np.diag(prior_sd)
    evals, evecs = np.linalg.eigh(W @ Pd @ W)
    return {"bits": float(bits), "post_sd": np.sqrt(np.diag(cov)), "cov": cov,
            "whitened_data_eigs": evals, "whitened_eigvecs": evecs}


def zero_sd_from_cov(theta, cov):
    g = np.empty(7)
    for j in range(7):
        d = 1e-4 * max(abs(theta[j]), 1.0)
        tp, tm = theta.copy(), theta.copy()
        tp[j] += d
        tm[j] -= d
        g[j] = (rg_zero(tp)[0] - rg_zero(tm)[0]) / (2 * d)
    return float(math.sqrt(max(g @ cov @ g, 0.0)))


def map_fit(C, Y, sigma, mu, sd):
    def nlp(t):
        r = (forward(C, t)[0] - Y) / sigma
        z = (t - mu) / sd
        return 0.5 * float((r ** 2).sum() + (z ** 2).sum())
    t, f = nelder_mead(nlp, mu, NM_ITERS)
    t, f = nelder_mead(nlp, t, NM_ITERS)
    return t, f


def predictive_report(theta, M, label):
    Yh = forward(M["C_ho"], theta)[0]
    ang = angles(Yh, M["X_ho"])
    lab_h = decode_multi(Yh, M["anchors"])
    lab_e = decode_multi(M["X_ho"], M["anchors"])
    sc = M["ho_scored"]
    acc = np.mean([a == t for a, t, s in zip(lab_h, M["ho_truth"], sc) if s])
    return {"which": label, "theta": theta.tolist(),
            "abs_error_vs_true": (theta - TRUE_THETA).tolist(),
            "heldout_angle_median_deg": float(np.median(ang)), "heldout_angle_mean_deg": float(ang.mean()),
            "heldout_angle_p90_deg": float(np.percentile(ang, 90)),
            "label_agreement_with_eye": float(np.mean([a == b for a, b in zip(lab_h, lab_e)])),
            "predicted_hue_accuracy": float(acc), "rg_zero_nm": float(rg_zero(theta)[0])}


def main():
    M = manifest_stimuli()
    obs_check = float(np.abs(forward(M["C_train"], TRUE_THETA)[0] - M["X_train"]).max())
    obs_check_ho = float(np.abs(forward(M["C_ho"], TRUE_THETA)[0] - M["X_ho"]).max())
    priors = {k: build_prior(k) for k in ("population", "broad")}
    out = {"status": "EXPLORATORY, POST-HOC; not preregistered; no frozen file changed; eye not built",
           "provenance": rd.provenance_line(),
           "utc_timestamp": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
           "script_sha256": sha256_file(Path(__file__)),
           "replica_vs_eye_max_abs": {"train": obs_check, "heldout": obs_check_ho},
           "true_theta": dict(zip(PARAM_NAMES, TRUE_THETA.tolist())),
           "true_rg_zero_nm": float(rg_zero(TRUE_THETA)[0]),
           "declared": {"pop_lmax": POP_LMAX, "wm_sd_cm1": WM_SD_CM1, "msp_sd_nm": MSP_SD_NM,
                        "bw_rel_sd": BW_REL_SD, "half_log10": [HALF_LOG10_MEDIAN, HALF_LOG10_SD],
                        "sigmas": SIGMAS, "primary_sigma": PRIMARY_SIGMA,
                        "room_td": ROOM_TD, "room_neutrals": ROOM_NEUTRALS,
                        "eyelid_ambient_td": EYELID_AMBIENT_TD, "eyelid_od": EYELID_OD,
                        "know_criteria": {"angle_deg": KNOW_ANGLE_DEG, "zero_sd_nm": KNOW_ZERO_SD_NM}},
           "priors": {}}
    rng = np.random.default_rng(SEED)

    # ---------------- T1 prior predictive
    T1 = {}
    for name, (mu, sd) in priors.items():
        z = (TRUE_THETA - mu) / sd
        chi2 = float((z ** 2).sum())
        draws = mu + sd * rng.standard_normal((N_PRIOR_SAMPLES, 7))
        Yh = forward(M["C_ho"], draws)                       # S x n x 2
        med_ang = np.median(angles(Yh, M["X_ho"][None]), axis=1)
        zeros = rg_zero(draws)
        lab_e = decode_multi(M["X_ho"], M["anchors"])
        agree = []
        for s in range(0, N_PRIOR_SAMPLES, 10):              # every 10th draw for label agreement
            lh = decode_multi(Yh[s], M["anchors"])
            agree.append(np.mean([a == b for a, b in zip(lh, lab_e)]))
        q = lambda v: [float(np.percentile(v, p)) for p in (5, 50, 95)]
        out["priors"][name] = {"mean": dict(zip(PARAM_NAMES, mu.tolist())),
                               "sd": dict(zip(PARAM_NAMES, sd.tolist()))}
        T1[name] = {
            "true_eye_z_scores": dict(zip(PARAM_NAMES, z.tolist())),
            "true_eye_mahalanobis_chi2_7df": chi2,
            "true_eye_prior_tail_prob": float(np.mean(((draws - mu) / sd) ** 2 @ np.ones(7) >= chi2)),
            "prior_mean_predictor": predictive_report(mu, M, "prior mean"),
            "draws_heldout_median_angle_deg_p5_p50_p95": q(med_ang),
            "draws_rg_zero_nm_p5_p50_p95": q(zeros[np.isfinite(zeros)]),
            "true_rg_zero_percentile_in_prior": float(np.mean(zeros < rg_zero(TRUE_THETA)[0]) * 100),
            "draws_label_agreement_with_eye_p5_p50_p95": q(agree),
        }
    out["T1_modelling_without_knowing"] = T1

    # ---------------- T2 / T3 information and identifiability
    rooms = {}
    for rname, ills, lid in (("room_E", ROOM_ILLUMINANTS_STRICT, False),
                             ("room_E_eyelid", ROOM_ILLUMINANTS_STRICT, True),
                             ("room_all", ROOM_ILLUMINANTS_ALL, False),
                             ("room_all_eyelid", ROOM_ILLUMINANTS_ALL, True)):
        meta, C = room_stimuli(ills, lid)
        rooms[rname] = {"meta": meta, "C": C, "Y": forward(C, TRUE_THETA)[0]}
    release_C, release_Y = M["C_train"], M["X_train"]

    def condition(C, Y, mu, sd, sigma, fit=True):
        J = jacobian(C, TRUE_THETA)
        gi = gauss_info(J, sigma, sd)
        res = {"n_exposures": int(C.shape[0]), "bits_gained": gi["bits"],
               "posterior_sd": dict(zip(PARAM_NAMES, gi["post_sd"].tolist())),
               "posterior_sd_over_prior_sd": dict(zip(PARAM_NAMES, (gi["post_sd"] / sd).tolist())),
               "rg_zero_posterior_sd_nm": zero_sd_from_cov(TRUE_THETA, gi["cov"]),
               "least_constrained_direction_whitened": dict(zip(PARAM_NAMES, gi["whitened_eigvecs"][:, 0].tolist())),
               "least_constrained_data_eig": float(gi["whitened_data_eigs"][0])}
        if fit:
            t, f = map_fit(C, Y, sigma, mu, sd)
            res["map"] = predictive_report(t, M, "MAP")
        return res

    T23 = {}
    for name, (mu, sd) in priors.items():
        T23[name] = {}
        for sigma in SIGMAS:
            fit = sigma == PRIMARY_SIGMA
            row = {}
            for rname, R in rooms.items():
                row[rname] = condition(R["C"], R["Y"], mu, sd, sigma, fit=fit and name == "population")
            row["release_mono_only"] = condition(release_C, release_Y, mu, sd, sigma, fit=fit and name == "population")
            Rall = rooms["room_all_eyelid"]
            row["room_all_eyelid_plus_release"] = condition(
                np.vstack([Rall["C"], release_C]), np.vstack([Rall["Y"], release_Y]), mu, sd, sigma,
                fit=fit and name == "population")
            T23[name][f"sigma={sigma}"] = row
    out["T3_room_and_release"] = T23

    # ---------------- T2 sequential: bits per release exposure, after the room
    mu, sd = priors["population"]
    Rall = rooms["room_all_eyelid"]
    J_room = jacobian(Rall["C"], TRUE_THETA)
    J_rel = jacobian(release_C, TRUE_THETA).reshape(release_C.shape[0], 2, 7)
    seq = {}
    for sigma in SIGMAS:
        P0 = np.diag(1.0 / sd ** 2)
        base = P0 + J_room.T @ J_room / sigma ** 2
        orders = {"random": list(rng.permutation(release_C.shape[0]))}
        # greedy: most informative next exposure
        P, remaining, greedy = base.copy(), list(range(release_C.shape[0])), []
        while remaining:
            gains = [np.linalg.slogdet(P + J_rel[i].T @ J_rel[i] / sigma ** 2)[1] for i in remaining]
            b = remaining[int(np.argmax(gains))]
            greedy.append(b)
            P = P + J_rel[b].T @ J_rel[b] / sigma ** 2
            remaining.remove(b)
        orders["greedy"] = greedy
        logdet0 = np.log(np.diag(P0)).sum()
        res = {}
        for oname, order in orders.items():
            P = base.copy()
            curve, n_know = [], None
            room_bits = 0.5 * (np.linalg.slogdet(P)[1] - logdet0) / math.log(2)
            for n, i in enumerate(order, 1):
                P = P + J_rel[i].T @ J_rel[i] / sigma ** 2
                cov = np.linalg.inv(P)
                bits = 0.5 * (np.linalg.slogdet(P)[1] - logdet0) / math.log(2)
                zsd = zero_sd_from_cov(TRUE_THETA, cov)
                psd = np.sqrt(np.diag(cov))
                curve.append({"n": n, "stimulus": M["train_ids"][i], "bits_total": float(bits),
                              "rg_zero_sd_nm": zsd, "max_centre_sd_nm": float(max(psd[0], psd[2], psd[4]))})
                if n_know is None and zsd < KNOW_ZERO_SD_NM and max(psd[0], psd[2], psd[4]) < KNOW_ZERO_SD_NM:
                    n_know = n
            res[oname] = {"room_bits": float(room_bits), "final_bits": curve[-1]["bits_total"],
                          "first10": curve[:10], "n_to_know_criteria": n_know,
                          "curve_bits": [c["bits_total"] for c in curve],
                          "curve_zero_sd": [c["rg_zero_sd_nm"] for c in curve]}
        seq[f"sigma={sigma}"] = res
    out["T2_bits_per_release_exposure"] = seq

    # ---------------- nonlinear check of the linearised claims (MAP fits)
    checks = {}
    greedy6 = seq[f"sigma={PRIMARY_SIGMA}"]["greedy"]["first10"][:6]
    g6 = [M["train_ids"].index(c["stimulus"]) for c in greedy6]
    for sigma in (0.001, PRIMARY_SIGMA):
        for rname in ("room_E_eyelid", "room_all_eyelid"):
            R = rooms[rname]
            t, _ = map_fit(R["C"], R["Y"], sigma, mu, sd)
            checks[f"{rname}|sigma={sigma}"] = predictive_report(t, M, "MAP")
        C6 = np.vstack([Rall["C"], release_C[g6]])
        Y6 = np.vstack([Rall["Y"], release_Y[g6]])
        t, _ = map_fit(C6, Y6, sigma, mu, sd)
        checks[f"room_all_eyelid+greedy6|sigma={sigma}"] = predictive_report(t, M, "MAP")
    out["map_checks_population_prior"] = checks
    OUT.write_text(json.dumps(rd._jsonable(out), indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
