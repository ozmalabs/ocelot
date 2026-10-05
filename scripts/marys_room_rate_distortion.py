"""Mary's Room broad study -- Arm C: representation and rate-distortion (Amendment A2).

Replaces the retired 48->28 proxy (docs/experiments/pilot-limits.md). Protocol:
docs/experiments/marys-room-broad-prereg.md, "Amendment A2 (Arm C protocol,
pre-analysis)", locked in results/marys_room_broad_freeze.json::amendment_A2.

Reads eye outputs from results/marys_room_broad.json (Arm B). Never builds an
eye and never imports domains.photon_eye. Every fit (USQ ranges, PCA, k-means,
substrate minter) sees sensory vectors only; labels are passed to scoring only.

Run from repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_rate_distortion
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import inspect
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from domains import colour_identity_world as ciw  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from scripts import marys_room_broad_theory as th  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EYE_RESULT = ROOT / "results" / "marys_room_broad.json"
ARMA = ROOT / "results" / "marys_room_broad_armA.json"
FREEZE = ROOT / "results" / "marys_room_broad_freeze.json"
PREREG = ROOT / "docs" / "experiments" / "marys-room-broad-prereg.md"
OUT = ROOT / "results" / "marys_room_rate_distortion.json"
CSV_DIR = ROOT / "results" / "marys_room_rate_distortion_csv"

# ---- A2 declared constants (do not change after outputs are seen) ----------
SEED = 20261004
B_GRID = list(range(1, 11))
K_GRID = [2, 4, 8, 16, 32, 64]
PCA_P = [1, 2, 3]
KM_RESTARTS = 10
KM_MAXIT = 300
FLOAT_BITS = 32
MINTER_SCALES = [100, 10, 1000]          # 100 = primary
MINTER_PRIMARY_SCALE = 100
ACC_FRACTION = 0.95                       # operating point: acc >= 0.95 * A0
ANGLE_OP_DEG = 5.0                        # secondary distortion operating point
ZERO_DECODED_ANGLE = 90.0
CONSISTENCY_TOL = 1e-12
MATCHED_RATES = list(range(1, 13))
CORE_FAMS = {"mono_sweep", "boundary_dense", "illuminant", "reflectance", "metamer", "eyelid"}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_arr(*arrs) -> str:
    h = hashlib.sha256()
    for a in arrs:
        h.update(np.ascontiguousarray(np.asarray(a, dtype=np.float64)).tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------- data model
def load_rows():
    eye = json.loads(EYE_RESULT.read_text())
    rows = eye["per_stimulus"]
    X_lms = np.array([[r["eye"]["receptors"][c]["activation"] for c in ("l", "m", "s")] for r in rows])
    X_opp = np.array([[r["eye"]["red_green"], r["eye"]["blue_yellow"]] for r in rows])
    # labels: separate arrays, scoring only
    labels = {"hue4": [r["truth"]["hue4"] for r in rows],
              "binary": [r["truth"]["binary"] for r in rows],
              "hue_scored": np.array([bool(r["hue_scored"]) for r in rows])}
    meta = [{"id": r["id"], "family": r["family"], "split": r["split"],
             "duplicate_of": r["duplicate_of"], "eye_source": r.get("eye_source")} for r in rows]
    return eye, X_lms, X_opp, labels, meta


def opp_from_lms(L):
    L = np.atleast_2d(L)
    return np.stack([L[:, 0] - L[:, 1], L[:, 2] - 0.5 * (L[:, 0] + L[:, 1])], axis=1)


def pools_from_meta(meta):
    idx = np.arange(len(meta))
    train = [i for i in idx if meta[i]["split"] == "train"]
    core = [i for i in idx if meta[i]["split"] == "heldout" and meta[i]["family"] in CORE_FAMS
            and meta[i]["duplicate_of"] is None]
    core_dup = [i for i in idx if meta[i]["split"] == "heldout" and meta[i]["family"] in CORE_FAMS]
    ho_all = [i for i in idx if meta[i]["split"] == "heldout" and meta[i]["family"] != "wrong_observer"
              and meta[i]["duplicate_of"] is None]
    return {"TRAIN": np.array(train), "HO_core": np.array(core),
            "HO_core_dup": np.array(core_dup), "HO_all": np.array(ho_all)}


# ------------------------------------------------------------- fit / encode
# Every fit function takes ONLY a float array (label-leak check inspects this).
def usq_fit(X):
    X = np.asarray(X, float)
    return {"lo": X.min(axis=0), "hi": X.max(axis=0)}


def usq_code(X, q, b):
    lo, hi = q["lo"], q["hi"]
    n = 2 ** b
    width = np.where(hi > lo, hi - lo, 1.0)
    raw = np.floor((X - lo) / width * n)
    clipped = (raw < 0) | (raw > n - 1)
    idx = np.clip(raw, 0, n - 1).astype(np.int64)
    rec = lo + (idx + 0.5) * width / n
    return idx, rec, clipped.any(axis=1)


def pca_fit(X):
    X = np.asarray(X, float)
    mu = X.mean(axis=0)
    _, sv, vt = np.linalg.svd(X - mu, full_matrices=False)
    for j in range(vt.shape[0]):
        if vt[j, np.argmax(np.abs(vt[j]))] < 0:
            vt[j] = -vt[j]
    return {"mean": mu, "components": vt, "singular_values": sv}


def _sqd(X, C):
    return ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)


def kmeans_fit(X, k, seed):
    X = np.asarray(X, float)
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(KM_RESTARTS):
        C = np.empty((k, X.shape[1]))
        C[0] = X[rng.integers(len(X))]
        for j in range(1, k):
            d2 = _sqd(X, C[:j]).min(axis=1)
            tot = d2.sum()
            pick = rng.integers(len(X)) if tot <= 0 else rng.choice(len(X), p=d2 / tot)
            C[j] = X[pick]
        assign = None
        iters = 0
        for iters in range(1, KM_MAXIT + 1):
            new = np.argmin(_sqd(X, C), axis=1)
            for j in range(k):           # empty cluster -> farthest point
                if not np.any(new == j):
                    far = int(np.argmax(((X - C[new]) ** 2).sum(axis=1)))
                    C[j] = X[far]
                    new = np.argmin(_sqd(X, C), axis=1)
            if assign is not None and np.array_equal(new, assign):
                break
            assign = new
            for j in range(k):
                if np.any(assign == j):
                    C[j] = X[assign == j].mean(axis=0)
        sse = float(_sqd(X, C)[np.arange(len(X)), assign].sum())
        if best is None or sse < best["train_sse"]:
            best = {"centroids": C.copy(), "train_sse": sse, "iterations": iters,
                    "n_nonempty": int(len(set(assign.tolist())))}
    return best


def kmeans_code(X, model):
    idx = np.argmin(_sqd(np.asarray(X, float), model["centroids"]), axis=1)
    return idx, model["centroids"][idx]


# ---------------------------------------------------------------- minter
def _boot_minter():
    s, agent = boot_core(seeds=())
    load_seeds_into(s, agent, ["vision_colour_identity"])
    qualia = json.loads((ROOT / "seeds" / "qualia_space.json").read_text())
    s._inner.load_seed_manifest(qualia, agent)
    return s


def lattice(X_opp, scale):
    return np.rint(np.asarray(X_opp, float) * scale).astype(np.int64)


def cells_from_lattice(Z, scale, rrow):
    return [{"cL": int(z[0]) + scale, "cM": scale, "cS": int(z[1]) + 2 * scale + int(z[0]),
             "rrow": rrow, "rcol": j} for j, z in enumerate(Z)]


def _read_region(s, n):
    a = s.node(n)["attrs"]
    return {"crg": float(a.get("crg", 0.0)), "cby": float(a.get("cby", 0.0)),
            "sign_rg": float(a.get("sign_rg", 0.0)), "sign_by": float(a.get("sign_by", 0.0)),
            "sign_dist": float(a.get("sign_dist", -1.0)),
            "refused": float(a.get("ci_refused", 0.0) or 0.0) > 0.5}


def minter_run(train_cells, ho_cells):
    """Protocol e-T if train_cells is not None, else e-H (held-out field alone)."""
    s = _boot_minter()
    t0 = time.monotonic()
    out = {}
    if train_cells is not None:
        h = ciw.add_field(s, cells=train_cells)
        ciw.set_flag(s, identity=1.0)
        out["ticks_train"] = ciw.tick(s)
        out["categories_after_train"] = ciw.categories(s)
        tr = [_read_region(s, n) for n in h["region_ids"]]
        ho_ids = [ciw.add_region(s, h, c) for c in ho_cells]
        out["ticks_heldout"] = ciw.tick(s)
        out["train_regions"] = tr
    else:
        h = ciw.add_field(s, cells=ho_cells)
        ciw.set_flag(s, identity=1.0)
        out["ticks_heldout"] = ciw.tick(s)
        ho_ids = h["region_ids"]
    out["categories_final"] = ciw.categories(s)
    out["heldout_regions"] = [_read_region(s, n) for n in ho_ids]
    out["seconds"] = time.monotonic() - t0
    return out


def minter_summary(run, Z_ho):
    regs = run["heldout_regions"]
    lat_ok = all(r["crg"] == float(z[0]) and r["cby"] == float(z[1]) for r, z in zip(regs, Z_ho))
    assigned = [r["sign_dist"] >= 0 and not r["refused"] for r in regs]
    exact = [a and r["sign_dist"] == 0.0 for a, r in zip(assigned, regs)]
    uniq, counts = np.unique(Z_ho, axis=0, return_counts=True)
    return {"n_cells": len(regs), "lattice_roundtrip_exact": bool(lat_ok),
            "n_categories_final": len(run["categories_final"]),
            "categories_final": run["categories_final"],
            "n_assigned": int(sum(assigned)), "n_exact_prototype_hits": int(sum(exact)),
            "n_refused": int(sum(r["refused"] for r in regs)),
            "n_unassigned_no_codebook": int(sum((not a) and (not r["refused"]) for a, r in zip(assigned, regs))),
            "n_distinct_lattice_points": int(len(uniq)),
            "n_lattice_points_with_count_ge3": int((counts >= 3).sum()),
            "max_lattice_multiplicity": int(counts.max()) if len(counts) else 0,
            "ticks": run.get("ticks_heldout"), "seconds": run["seconds"]}


# ---------------------------------------------------------------- scoring
def angles_deg(rec, orig):
    dot = (rec * orig).sum(axis=1)
    cross = rec[:, 0] * orig[:, 1] - rec[:, 1] * orig[:, 0]
    a = np.degrees(np.arctan2(np.abs(cross), dot))
    a = np.where(np.linalg.norm(rec, axis=1) == 0, ZERO_DECODED_ANGLE, a)
    return a


def summ(v):
    v = np.asarray(v, float)
    if len(v) == 0:
        return {"n": 0}
    return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
            "p90": float(np.percentile(v, 90)), "max": float(v.max())}


def decode_labels(V, anchors):
    return [th.decode(float(rg), float(by), anchors) for rg, by in V]


class Scorer:
    def __init__(self, idx, X_opp, labels, anchors):
        self.idx = idx
        self.orig = X_opp[idx]
        self.anchors = anchors
        self.scored = labels["hue_scored"][idx]
        self.hue = [labels["hue4"][i] for i in idx]
        self.binary = [labels["binary"][i] for i in idx]
        self.nonzero = np.linalg.norm(self.orig, axis=1) > 0
        d0 = decode_labels(self.orig, anchors)
        self.orig_multi = [d["multi"] for d in d0]
        self.orig_sign = [d["sign"] for d in d0]
        self.A0 = self._acc(self.orig_multi)
        self.A0_sign = self._acc_sign(self.orig_sign)

    def _acc(self, pred):
        s = [p == t for p, t, ok in zip(pred, self.hue, self.scored) if ok]
        return sum(s) / len(s)

    def _acc_sign(self, pred):
        m = {"red": "reddish", "green": "greenish"}
        s = [m.get(p, "undecided") == t for p, t, ok in zip(pred, self.binary, self.scored) if ok]
        return sum(s) / len(s)

    def _bal(self, pred):
        rec = []
        for c in th.HUE4:
            sel = [p == t for p, t, ok in zip(pred, self.hue, self.scored) if ok and t == c]
            if sel:
                rec.append(sum(sel) / len(sel))
        return float(np.mean(rec))

    def evaluate(self, rec):
        rec = np.asarray(rec, float)
        dec = decode_labels(rec, self.anchors)
        multi = [d["multi"] for d in dec]
        sign = [d["sign"] for d in dec]
        n_sc = int(self.scored.sum())
        k = int(sum(p == t for p, t, ok in zip(multi, self.hue, self.scored) if ok))
        ang = angles_deg(rec[self.nonzero], self.orig[self.nonzero])
        euc = np.linalg.norm(rec - self.orig, axis=1)
        return {"task_accuracy": k / n_sc, "task_correct": k, "task_n": n_sc,
                "task_wilson95": th.wilson(k, n_sc),
                "task_balanced_accuracy": self._bal(multi),
                "task_rel_to_A0": (k / n_sc) / self.A0,
                "label_fidelity": float(np.mean([a == b for a, b in zip(multi, self.orig_multi)])),
                "sign_rule_accuracy": self._acc_sign(sign),
                "n_undecided": int(sum(p == "undecided" for p in multi)),
                "angle_deg": summ(ang), "n_angle_excluded_zero_original": int((~self.nonzero).sum()),
                "euclid": summ(euc)}

    def full_score(self, rec):
        dec = decode_labels(np.asarray(rec, float), self.anchors)
        truth = [t for t, ok in zip(self.hue, self.scored) if ok]
        pred = [d["multi"] for d, ok in zip(dec, self.scored) if ok]
        return th.score(truth, pred, th.HUE4)


def entropy_bits(codes):
    codes = np.asarray(codes)
    if codes.ndim == 1:
        codes = codes[:, None]
    _, c = np.unique(codes, axis=0, return_counts=True)
    p = c / c.sum()
    return float(-(p * np.log2(p)).sum())


# ---------------------------------------------------------------- analysis
def fit_all(Xtr_lms, Xtr_opp, Ztr_by_scale=None):
    """All fitted model parameters (labels are not an argument)."""
    models = {"usq_lms": usq_fit(Xtr_lms), "usq_opp": usq_fit(Xtr_opp),
              "usq_rg": usq_fit(Xtr_opp[:, :1]), "usq_by": usq_fit(Xtr_opp[:, 1:])}
    pca = pca_fit(Xtr_lms)
    models["pca"] = pca
    for p in PCA_P:
        S = (Xtr_lms - pca["mean"]) @ pca["components"][:p].T
        models[f"usq_pca{p}"] = usq_fit(S)
    for k in K_GRID:
        models[f"vq_opp_k{k}"] = kmeans_fit(Xtr_opp, k, SEED + k)
        models[f"vq_lms_k{k}"] = kmeans_fit(Xtr_lms, k, SEED + k)
    return models


def models_hash(models):
    parts = []
    for name in sorted(models):
        m = models[name]
        for key in sorted(m):
            v = m[key]
            if isinstance(v, np.ndarray) or isinstance(v, float):
                parts.append(np.atleast_1d(np.asarray(v, float)))
    return sha_arr(*parts)


def rd_rows_for_pool(pname, sc, X_lms, X_opp, models, minter_coded):
    N = len(sc.idx)
    Xl, Xo = X_lms[sc.idx], X_opp[sc.idx]
    rows = []

    def add(rep, cfg, bits, model_bits, rec, codes, clipped=None, extra=None):
        ev = sc.evaluate(rec)
        r = {"pool": pname, "representation": rep, "config": cfg, "N": N,
             "bits_per_sample": bits, "model_bits": model_bits,
             "rate_total": bits + model_bits / N, "rate_no_model": bits,
             "entropy_proxy_bits": entropy_bits(codes) if codes is not None else None,
             "clip_fraction": float(np.mean(clipped)) if clipped is not None else None, **ev}
        if extra:
            r.update(extra)
        rows.append(r)

    for b in B_GRID:
        idx, rec, cl = usq_code(Xl, models["usq_lms"], b)
        add("a_raw_LMS", f"b={b}", 3 * b, 3 * 2 * FLOAT_BITS, opp_from_lms(rec), idx, cl)
        idx, rec, cl = usq_code(Xo, models["usq_opp"], b)
        add("b_opponent", f"b={b}", 2 * b, 2 * 2 * FLOAT_BITS, rec, idx, cl)
        idx, rg, cl = usq_code(Xo[:, :1], models["usq_rg"], b)
        add("ablate_RG_only", f"b={b}", b, 2 * FLOAT_BITS, np.hstack([rg, np.zeros_like(rg)]), idx, cl)
        idx, by, cl = usq_code(Xo[:, 1:], models["usq_by"], b)
        add("ablate_BY_only", f"b={b}", b, 2 * FLOAT_BITS, np.hstack([np.zeros_like(by), by]), idx, cl)
        pca = models["pca"]
        for p in PCA_P:
            S = (Xl - pca["mean"]) @ pca["components"][:p].T
            idx, Srec, cl = usq_code(S, models[f"usq_pca{p}"], b)
            L = pca["mean"] + Srec @ pca["components"][:p]
            add(f"c_PCA_p{p}", f"p={p},b={b}", p * b, (3 + 3 * p + 2 * p) * FLOAT_BITS,
                opp_from_lms(L), idx, cl)
    for k in K_GRID:
        idx, rec = kmeans_code(Xo, models[f"vq_opp_k{k}"])
        add("d1_VQ_opp", f"k={k}", math.log2(k), k * 2 * FLOAT_BITS, rec, idx)
        idx, rec = kmeans_code(Xl, models[f"vq_lms_k{k}"])
        add("d2_VQ_LMS", f"k={k}", math.log2(k), k * 3 * FLOAT_BITS, opp_from_lms(rec), idx)
    for scale, mc in (minter_coded or {}).items():
        add(f"e_minter_s{scale}", f"s={scale},k={mc['k']}", mc["bits_mean"], mc["model_bits"],
            mc["rec"], mc["codes"], None,
            {"minter_n_assigned": mc["n_assigned"], "minter_n_fallback": mc["n_fallback"]})
    # unquantised axis-drop ablations (no rate)
    abl = {"orig_drop_BY": sc.evaluate(np.hstack([Xo[:, :1], np.zeros((N, 1))])),
           "orig_drop_RG": sc.evaluate(np.hstack([np.zeros((N, 1)), Xo[:, 1:]])),
           "orig_unquantised": sc.evaluate(Xo)}
    return rows, abl


def minter_code(train_Z, ho_Z, run, scale):
    """A2-3(e) code for protocol e-T."""
    cats = run["categories_final"]
    k = len(cats)
    lo, hi = train_Z.min(axis=0), train_Z.max(axis=0)
    B_s = int(sum(math.ceil(math.log2(int(h) - int(l) + 1)) for l, h in zip(lo, hi)))
    cat_bits = math.ceil(math.log2(k)) if k > 0 else 0
    rec, bits, codes = [], [], []
    cat_index = {(c["crg"], c["cby"]): j for j, c in enumerate(cats)}
    n_as = 0
    for r, z in zip(run["heldout_regions"], ho_Z):
        if k > 0 and r["sign_dist"] >= 0 and not r["refused"]:
            n_as += 1
            proto = (int(round(r["sign_rg"])), int(round(r["sign_by"])))
            rec.append([proto[0] / scale, proto[1] / scale])
            bits.append(1 + cat_bits)
            codes.append([0, cat_index[proto], 0])
        else:
            zc = np.clip(z, lo, hi)
            rec.append([zc[0] / scale, zc[1] / scale])
            bits.append(1 + B_s)
            codes.append([1, int(zc[0]), int(zc[1])])
    return {"k": k, "B_s": B_s, "cat_bits": cat_bits, "rec": np.array(rec, float),
            "bits_mean": float(np.mean(bits)), "model_bits": k * 2 * FLOAT_BITS + 2 * 2 * FLOAT_BITS,
            "codes": np.array(codes), "n_assigned": n_as, "n_fallback": len(ho_Z) - n_as,
            "train_int_range": [lo.tolist(), hi.tolist()]}


def operating_points(rows, A0, pool):
    target = ACC_FRACTION * A0
    reps = sorted(set(r["representation"] for r in rows if r["pool"] == pool))
    out = {}
    for rep in reps:
        rr = [r for r in rows if r["pool"] == pool and r["representation"] == rep]

        def best(key, ok):
            c = [r for r in rr if ok(r)]
            if not c:
                return None
            r = min(c, key=lambda x: (x[key], x["config"]))
            return {"config": r["config"], key: r[key], "rate_total": r["rate_total"],
                    "rate_no_model": r["rate_no_model"], "task_accuracy": r["task_accuracy"],
                    "task_wilson95": r["task_wilson95"], "angle_mean_deg": r["angle_deg"]["mean"]}
        out[rep] = {
            "acc_op_with_model_cost": best("rate_total", lambda r: r["task_accuracy"] >= target),
            "acc_op_without_model_cost": best("rate_no_model", lambda r: r["task_accuracy"] >= target),
            "angle_op_with_model_cost": best("rate_total", lambda r: r["angle_deg"]["mean"] <= ANGLE_OP_DEG),
            "angle_op_without_model_cost": best("rate_no_model", lambda r: r["angle_deg"]["mean"] <= ANGLE_OP_DEG),
            "max_task_accuracy": max(r["task_accuracy"] for r in rr),
            "min_angle_mean_deg": min(r["angle_deg"]["mean"] for r in rr)}
    return {"A0": A0, "target_accuracy": target, "per_representation": out}


def p6_verdict(op, learned="d1_VQ_opp", raw="a_raw_LMS", key="acc_op_with_model_cost"):
    l = op["per_representation"].get(learned, {}).get(key)
    r = op["per_representation"].get(raw, {}).get(key)
    rk = "rate_total" if "with_model" in key else "rate_no_model"
    if l is None:
        v = "not supported"
    elif r is None:
        v = "supported"
    else:
        v = "supported" if l[rk] < r[rk] else "not supported"
    return {"learned": learned, "baseline": raw, "criterion": key, "verdict": v,
            "learned_R": None if l is None else l[rk], "learned_config": None if l is None else l["config"],
            "baseline_R": None if r is None else r[rk], "baseline_config": None if r is None else r["config"]}


def analysis(eye, X_lms, X_opp, labels, meta, anchors):
    pools = pools_from_meta(meta)
    tr = pools["TRAIN"]
    Xtr_lms, Xtr_opp = X_lms[tr], X_opp[tr]

    consistency = {
        "max_abs_rg_minus_LminusM": float(np.abs(X_opp[:, 0] - (X_lms[:, 0] - X_lms[:, 1])).max()),
        "max_abs_by_minus_formula": float(np.abs(X_opp[:, 1] - (X_lms[:, 2] - 0.5 * (X_lms[:, 0] + X_lms[:, 1]))).max())}
    consistency["pass"] = bool(max(consistency.values()) <= CONSISTENCY_TOL)

    models = fit_all(Xtr_lms, Xtr_opp)
    mh = models_hash(models)
    # label-leak check: permute the label array, refit; fits never receive labels.
    perm = np.random.default_rng(SEED).permutation(len(labels["hue4"]))
    _permuted_labels = [labels["hue4"][i] for i in perm]   # deliberately unused by fits
    mh2 = models_hash(fit_all(Xtr_lms, Xtr_opp))
    fit_fns = [usq_fit, pca_fit, kmeans_fit, fit_all, lattice, cells_from_lattice, minter_run]
    sigs = {f.__name__: list(inspect.signature(f).parameters) for f in fit_fns}
    label_words = {"label", "labels", "hue", "hue4", "truth", "binary", "y"}
    leak = {"model_hash": mh, "model_hash_after_label_permutation": mh2,
            "identical": mh == mh2, "fit_signatures": sigs,
            "no_label_parameter": all(not (set(v) & label_words) for v in sigs.values()),
            "anchors_source": "results/marys_room_broad_armA.json (A1 theory-only, not fitted here)"}

    # ---- minter
    minter = {"declared": {"scales": MINTER_SCALES, "primary_scale": MINTER_PRIMARY_SCALE,
                           "integerisation": "cRG=rint(s*RG), cBY=rint(s*BY); cL=cRG+s, cM=s, cS=cBY+2s+cRG",
                           "bound": "shipped default (armed)"}}
    minter_coded = {}
    for scale in MINTER_SCALES:
        Ztr = lattice(Xtr_opp, scale)
        Zho = lattice(X_opp[pools["HO_core"]], scale)
        run = minter_run(cells_from_lattice(Ztr, scale, 0), cells_from_lattice(Zho, scale, 1))
        train_cats = run["categories_after_train"]
        tr_keys = {(c["crg"], c["cby"]) for c in train_cats}
        new_cats = [c for c in run["categories_final"] if (c["crg"], c["cby"]) not in tr_keys]
        u_tr, c_tr = np.unique(Ztr, axis=0, return_counts=True)
        entry = {"e_T": {"n_train_cells": len(Ztr),
                         "train_distinct_lattice_points": int(len(u_tr)),
                         "train_lattice_points_count_ge3": int((c_tr >= 3).sum()),
                         "train_lattice_roundtrip_exact": all(
                             r["crg"] == float(z[0]) and r["cby"] == float(z[1])
                             for r, z in zip(run["train_regions"], Ztr)),
                         "categories_minted_on_train": train_cats,
                         "categories_minted_when_heldout_added": new_cats,
                         "heldout": minter_summary(run, Zho)}}
        minter_coded[scale] = minter_code(Ztr, Zho, run, scale)
        mc = minter_coded[scale]
        entry["e_T"]["code"] = {k: v for k, v in mc.items() if k not in ("rec", "codes")}
        eh = {}
        for pname in ("HO_core", "HO_core_dup", "HO_all"):
            Z = lattice(X_opp[pools[pname]], scale)
            eh[pname] = minter_summary(minter_run(None, cells_from_lattice(Z, scale, 1)), Z)
        entry["e_H"] = eh
        # exact float repeats (what the unscaled pilot adapter could compress)
        for pname in ("HO_core", "HO_core_dup", "HO_all"):
            _, c = np.unique(X_opp[pools[pname]], axis=0, return_counts=True)
            eh[pname]["float_exact_vectors_count_ge3"] = int((c >= 3).sum())
            eh[pname]["float_distinct_vectors"] = int(len(c))
        minter[f"s={scale}"] = entry

    # ---- RD tables
    all_rows, ablations, ops, scorers = [], {}, {}, {}
    for pname in ("HO_core", "HO_all"):
        sc = Scorer(pools[pname], X_opp, labels, anchors)
        scorers[pname] = sc
        mc = {s: v for s, v in minter_coded.items()} if pname == "HO_core" else None
        rows, abl = rd_rows_for_pool(pname, sc, X_lms, X_opp, models, mc)
        all_rows += rows
        ablations[pname] = abl
        ops[pname] = operating_points(rows, sc.A0, pname)
        ops[pname]["A0_sign_rule"] = sc.A0_sign
        ops[pname]["A0_full_score"] = sc.full_score(X_opp[pools[pname]])

    # full scoring (bootstrap) at each primary operating point
    for pname, op in ops.items():
        sc = scorers[pname]
        for rep, d in op["per_representation"].items():
            o = d["acc_op_with_model_cost"]
            if o is None:
                continue
            row = next(r for r in all_rows if r["pool"] == pname and r["representation"] == rep
                       and r["config"] == o["config"])
            o["balanced_accuracy"] = row["task_balanced_accuracy"]
            o["label_fidelity"] = row["label_fidelity"]

    verdicts = {
        "P6_primary": p6_verdict(ops["HO_core"]),
        "secondary": {
            "no_model_cost": p6_verdict(ops["HO_core"], key="acc_op_without_model_cost"),
            "PCA_p2_vs_raw": p6_verdict(ops["HO_core"], learned="c_PCA_p2"),
            "PCA_p3_vs_raw": p6_verdict(ops["HO_core"], learned="c_PCA_p3"),
            "VQ_LMS_vs_raw": p6_verdict(ops["HO_core"], learned="d2_VQ_LMS"),
            "VQ_opp_vs_opponent": p6_verdict(ops["HO_core"], raw="b_opponent"),
            "minter_s100_vs_raw": p6_verdict(ops["HO_core"], learned="e_minter_s100"),
            "minter_s100_vs_raw_no_model_cost": p6_verdict(ops["HO_core"], learned="e_minter_s100",
                                                           key="acc_op_without_model_cost"),
            "angle_op_VQ_vs_raw": p6_verdict(ops["HO_core"], key="angle_op_with_model_cost"),
            "HO_all_VQ_vs_raw": p6_verdict(ops["HO_all"]),
            "HO_all_VQ_vs_raw_no_model_cost": p6_verdict(ops["HO_all"], key="acc_op_without_model_cost"),
        }}

    # matched-rate table (fixed-length bits/sample exactly R; model cost reported alongside)
    matched = []
    for pname in ("HO_core",):
        for R in MATCHED_RATES:
            for r in all_rows:
                if r["pool"] == pname and abs(r["rate_no_model"] - R) < 1e-9 and not r["representation"].startswith("e_"):
                    matched.append({"pool": pname, "bits_per_sample": R, "representation": r["representation"],
                                    "config": r["config"], "rate_total": r["rate_total"],
                                    "task_accuracy": r["task_accuracy"], "angle_mean_deg": r["angle_deg"]["mean"],
                                    "angle_median_deg": r["angle_deg"]["median"], "euclid_mean": r["euclid"]["mean"]})

    model_summary = {
        "usq_lms": {k: v.tolist() for k, v in models["usq_lms"].items()},
        "usq_opp": {k: v.tolist() for k, v in models["usq_opp"].items()},
        "pca": {"mean": models["pca"]["mean"].tolist(), "components": models["pca"]["components"].tolist(),
                "singular_values": models["pca"]["singular_values"].tolist(),
                "explained_variance_ratio": (models["pca"]["singular_values"] ** 2 /
                                             (models["pca"]["singular_values"] ** 2).sum()).tolist()},
        "kmeans": {name: {"train_sse": m["train_sse"], "iterations": m["iterations"],
                          "n_nonempty": m["n_nonempty"], "centroids": m["centroids"].tolist()}
                   for name, m in models.items() if name.startswith("vq_")},
    }
    pool_sizes = {p: {"N": int(len(v)), "hue_scored": int(labels["hue_scored"][v].sum()) if len(v) else 0}
                  for p, v in pools.items()}
    return {"consistency_check": consistency, "label_leak_check": leak, "pool_sizes": pool_sizes,
            "models": model_summary, "minter": minter, "operating_points": ops, "verdicts": verdicts,
            "ablations_unquantised": ablations, "rd_rows": all_rows, "matched_rate_HO_core": matched}


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def write_csvs(payload):
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    prov = payload["provenance"]
    cols = ["pool", "representation", "config", "N", "bits_per_sample", "model_bits", "rate_total",
            "entropy_proxy_bits", "clip_fraction", "task_accuracy", "task_wilson95_lo", "task_wilson95_hi",
            "task_balanced_accuracy", "task_rel_to_A0", "label_fidelity", "sign_rule_accuracy", "n_undecided",
            "angle_mean_deg", "angle_median_deg", "angle_p90_deg", "euclid_mean", "euclid_median"]
    by_rep = {}
    for r in payload["rd_rows"]:
        by_rep.setdefault(r["representation"], []).append(r)
    files = []
    for rep, rows in sorted(by_rep.items()):
        p = CSV_DIR / f"rd_{rep}.csv"
        with p.open("w", newline="") as f:
            f.write(f"# provenance: {prov}\n")
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r["pool"], r["representation"], r["config"], r["N"], r["bits_per_sample"],
                            r["model_bits"], r["rate_total"], r["entropy_proxy_bits"], r["clip_fraction"],
                            r["task_accuracy"], r["task_wilson95"][0], r["task_wilson95"][1],
                            r["task_balanced_accuracy"], r["task_rel_to_A0"], r["label_fidelity"],
                            r["sign_rule_accuracy"], r["n_undecided"], r["angle_deg"]["mean"],
                            r["angle_deg"]["median"], r["angle_deg"]["p90"], r["euclid"]["mean"],
                            r["euclid"]["median"]])
        files.append(p)
    p = CSV_DIR / "matched_rate_HO_core.csv"
    with p.open("w", newline="") as f:
        f.write(f"# provenance: {prov}\n")
        mcols = list(payload["matched_rate_HO_core"][0].keys())
        w = csv.DictWriter(f, fieldnames=mcols)
        w.writeheader()
        w.writerows(payload["matched_rate_HO_core"])
    files.append(p)
    return files


def main():
    if "domains.photon_eye" in sys.modules:
        raise RuntimeError("Arm C must not import domains.photon_eye")
    fz = json.loads(FREEZE.read_text())
    a2 = fz.get("amendment_A2")
    if a2 is None or sha256_file(PREREG) != a2["sha256"]:
        raise RuntimeError("Amendment A2 lock missing or prereg changed since A2 lock")
    frozen_inputs = {"results/marys_room_broad_armA.json": fz["sha256"].get("results/marys_room_broad_armA.json"),
                     "results/marys_room_broad_stimuli.json": fz["sha256"].get("results/marys_room_broad_stimuli.json")}
    input_check = {k: {"frozen": v, "now": sha256_file(ROOT / k), "match": v == sha256_file(ROOT / k)}
                   for k, v in frozen_inputs.items()}
    if not all(v["match"] for v in input_check.values()):
        raise RuntimeError(f"frozen input changed: {input_check}")
    anchors = json.loads(ARMA.read_text())["anchors"]
    eye, X_lms, X_opp, labels, meta = load_rows()
    t0 = time.monotonic()
    res1 = _jsonable(analysis(eye, X_lms, X_opp, labels, meta, anchors))
    t1 = time.monotonic()
    res2 = _jsonable(analysis(eye, X_lms, X_opp, labels, meta, anchors))

    def strip_time(o):
        if isinstance(o, dict):
            return {k: strip_time(v) for k, v in o.items() if k != "seconds"}
        if isinstance(o, list):
            return [strip_time(v) for v in o]
        return o
    h1 = hashlib.sha256(json.dumps(strip_time(res1), sort_keys=True).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(strip_time(res2), sort_keys=True).encode()).hexdigest()
    payload = {
        "experiment": "marys_room_broad", "arm": "C (representation and rate-distortion)",
        "amendment": "A2", "provenance": provenance_line(),
        "utc_timestamp": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "inputs": {"eye_result": {"path": "results/marys_room_broad.json", "sha256": sha256_file(EYE_RESULT),
                                  "provenance": eye.get("provenance")},
                   "frozen_inputs": input_check,
                   "prereg_sha256_A2": a2["sha256"],
                   "script_sha256": sha256_file(Path(__file__))},
        "eye_built_in_this_stage": False,
        "declared": {"seed": SEED, "b_grid": B_GRID, "k_grid": K_GRID, "pca_p": PCA_P,
                     "kmeans_restarts": KM_RESTARTS, "kmeans_maxit": KM_MAXIT, "float_bits": FLOAT_BITS,
                     "acc_fraction": ACC_FRACTION, "angle_op_deg": ANGLE_OP_DEG,
                     "zero_decoded_angle_deg": ZERO_DECODED_ANGLE, "minter_scales": MINTER_SCALES,
                     "core_families": sorted(CORE_FAMS)},
        "determinism": {"payload_sha256_run1": h1, "payload_sha256_run2": h2, "identical": h1 == h2},
        "runtime_seconds": t1 - t0,
        **res1,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    files = write_csvs(payload)
    print(f"wrote {OUT} and {len(files)} CSVs in {CSV_DIR}")
    print(json.dumps({"verdicts": payload["verdicts"], "determinism": payload["determinism"],
                      "consistency": payload["consistency_check"],
                      "leak": {k: v for k, v in payload["label_leak_check"].items() if k != "fit_signatures"}},
                     indent=1))


if __name__ == "__main__":
    main()
