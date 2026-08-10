"""RUN 60 -- CONSTRUCTION-RECOVERY FROM DYNAMICS. The creator's vision (verbatim): "we should be
able to get SIGNAL from those changes and be able to recover all manner of things about the way
which the ink was constructed."

The confounds run 59 tried to explain away are a RICH SIGNAL about the construction process
(writer, instrument, state, posture, teaching). A faithful forward model INVERTS to recover the
construction factors. This run tests the inversion DIRECTLY: do the DYNAMIC/CONFOUND features
recover KNOWN construction facts DigiLeTs ships in its filenames (WRITER_ID, GENDER, AGE, HAND)?

PURE MEASUREMENT. donkey=0 (no trained classifier). The measurement instrument is REUSED:
  * domains.discrimination.fisher_ratio  -- run 57's Fisher discriminability (the faculty).
  * A held-Argmin nearest-fact-mean classifier -- no learned weights, just class means +
    Euclidean argmin (the SAME held-Argmin verdict shape the arc already uses).
  * domains.ink_dynamics.speed_profile   -- run 33's kinematics.
  * domains.pen_world.load_digilets_samples -- run 48's loader (already exposes gender/age/hand).

CONSTRUCTION FEATURES are the "how it was made" channels, NOT the SC+TPS character shape -- we are
recovering CONSTRUCTION, not content. Five channels: pressure, timing/velocity, pen-lift, geometric
extension, stroke-order/count.

PROTOCOL (the run-58 lesson: demographic facts MUST transfer to HELD-OUT WRITERS):
  * Demographics (handedness/gender/age): features aggregated PER WRITER (removes the character
    confound -- an 'A' has more strokes than a '1'; averaging over a writer's 62 characters leaves
    the writer's own construction style). Leave-writers-out K-fold CV: every writer tested once,
    class-means from TRAIN writers only, nearest-fact-mean over standardized Fisher-weighted
    features. Report held-out accuracy vs base-rate (majority class) vs shuffled-label null.
  * Writer-identity: the biometric protocol -- features PER INSTANCE, split by CHARACTER (train on
    one character set, test on the DISJOINT set: "different characters, same writer"). Nearest-
    writer-mean, 77-way, base-rate 1/77.

A fact is RECOVERABLE iff held-out accuracy is materially above base-rate AND above the shuffled
null.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pickle
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import discrimination as disc
from domains import ink_dynamics as idyn
from domains import pen_world as pw

CKPT_DIR = "results/run60_checkpoints"
SEED_FILE = "seeds/stroke_shapes.json"
EPS = 1e-9

# ----- feature channels (pre-registered, documented before any number is computed) ------------ #
FEATURE_NAMES = [
    # PRESSURE (ink/grip/initiation)
    "press_mean", "press_std", "press_init", "press_trend",
    # TIMING / VELOCITY (tempo/fluency/attention)
    "speed_mean", "speed_cv", "dwell_frac", "pause_rate", "total_dur", "tempo",
    # PEN-LIFT / REPOSITION (biomechanics/posture)
    "n_penlifts", "inter_gap_mean",
    # EXTENSION / geometry (workspace)
    "bbox_aspect", "reach", "spread_x", "spread_y",
    # STROKE-ORDER / count (motor program)
    "n_strokes", "first_stroke_frac",
]
CHANNELS = {
    "pressure": ["press_mean", "press_std", "press_init", "press_trend"],
    "timing":   ["speed_mean", "speed_cv", "dwell_frac", "pause_rate", "total_dur", "tempo"],
    "penlift":  ["n_penlifts", "inter_gap_mean"],
    "extension": ["bbox_aspect", "reach", "spread_x", "spread_y"],
    "order":    ["n_strokes", "first_stroke_frac"],
}
FIDX = {n: i for i, n in enumerate(FEATURE_NAMES)}


# ============================================================================================== #
#  SEED GUARD
# ============================================================================================== #
def seed_md5() -> str:
    with open(SEED_FILE, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ============================================================================================== #
#  CONSTRUCTION FEATURE EXTRACTION  (mechanical, fixed formulas over raw pen samples -- the same
#  world-adapter measurement class as ink_dynamics / adaptive_bins; no decision, no graph state).
# ============================================================================================== #
def _stroke_xyts(sample) -> list:
    """(x,y,t) arrays per stroke, sliced at pen-touch-down events (same boundaries pen_world uses)."""
    pos, t, pd = sample["pos_xy"], sample["t_ms"], sample["pen_down"]
    starts = [i for i, v in enumerate(pd) if v == 1]
    if not starts or starts[0] != 0:
        starts = [0] + starts
    out = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(pos)
        if e - s >= 1:
            out.append(np.column_stack([pos[s:e, 0], pos[s:e, 1], t[s:e]]))
    return out, starts


def construction_features(sample) -> np.ndarray:
    """The construction signal for one instance -> a fixed-length float vector (FEATURE_NAMES
    order). Robust to short/degenerate strokes (finite everywhere)."""
    pos = np.asarray(sample["pos_xy"], dtype=float)
    press = np.asarray(sample["pressure"], dtype=float)
    t = np.asarray(sample["t_ms"], dtype=float)
    n = pos.shape[0]
    xyts, starts = _stroke_xyts(sample)
    n_strokes = len(xyts)

    # -- PRESSURE --
    press_mean = float(press.mean()) if press.size else 0.0
    press_std = float(press.std()) if press.size else 0.0
    press_init = float(press[:3].mean()) if press.size else 0.0
    if press.size >= 3:
        xi = np.linspace(0.0, 1.0, press.size)
        press_trend = float(np.polyfit(xi, press, 1)[0])
    else:
        press_trend = 0.0

    # -- TIMING / VELOCITY -- concat per-stroke smoothed speed (reuse run 33) --
    speeds = []
    path_len = 0.0
    for xyt in xyts:
        if xyt.shape[0] >= 2:
            speeds.append(idyn.speed_profile(xyt))
            path_len += float(np.sqrt((np.diff(xyt[:, :2], axis=0) ** 2).sum(axis=1)).sum())
    sp = np.concatenate(speeds) if speeds else np.zeros(1)
    speed_mean = float(sp.mean())
    speed_cv = float(sp.std() / (abs(sp.mean()) + EPS))
    smax = float(sp.max()) if sp.size else 0.0
    dwell_frac = float((sp < 0.15 * smax).mean()) if smax > EPS else 0.0
    total_dur = float(t.max() - t.min()) if n >= 2 else 0.0    # ms, includes pen-lift gaps
    # within-stroke speed minima below 0.4*peak = pauses; rate per second of writing
    n_pauses = 0
    for s in speeds:
        if s.size >= 3 and s.max() > EPS:
            thr = 0.4 * s.max()
            n_pauses += sum(1 for i in idyn._local_minima_indices(s) if s[i] <= thr)
    pause_rate = float(n_pauses / (total_dur / 1000.0)) if total_dur > EPS else 0.0
    tempo = float(path_len / (total_dur / 1000.0)) if total_dur > EPS else 0.0

    # -- PEN-LIFT / REPOSITION -- gap = dt across each stroke boundary (pen-up duration) --
    n_penlifts = float(n_strokes - 1)
    gaps = []
    for k in range(1, len(starts)):
        b = starts[k]
        if 0 < b < n:
            gaps.append(float(t[b] - t[b - 1]))
    inter_gap_mean = float(np.mean(gaps)) if gaps else 0.0

    # -- EXTENSION / geometry (raw digitizer units -> physical workspace) --
    if n >= 2:
        mn, mx = pos.min(0), pos.max(0)
        w = float(mx[0] - mn[0]); h = float(mx[1] - mn[1])
        bbox_aspect = float(h / (w + EPS))
        reach = float(np.hypot(w, h))
        spread_x = float(pos[:, 0].std()); spread_y = float(pos[:, 1].std())
    else:
        bbox_aspect = reach = spread_x = spread_y = 0.0

    # -- STROKE-ORDER / count --
    first_stroke_frac = float(xyts[0].shape[0] / n) if (xyts and n) else 1.0

    vec = np.array([press_mean, press_std, press_init, press_trend,
                    speed_mean, speed_cv, dwell_frac, pause_rate, total_dur, tempo,
                    float(n_penlifts), inter_gap_mean,
                    bbox_aspect, reach, spread_x, spread_y,
                    float(n_strokes), first_stroke_frac], dtype=float)
    vec[~np.isfinite(vec)] = 0.0
    return vec


# ============================================================================================== #
#  HELD-ARGMIN NEAREST-FACT CLASSIFIER  (donkey=0: class means + Euclidean argmin, no learned
#  weights). Features standardized by TRAIN stats, weighted by sqrt(TRAIN Fisher) -> the
#  "discriminative feature space" (the faculty's discriminability IS the metric).
# ============================================================================================== #
def _fisher_per_feature(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-column Fisher discriminability (run 57's faculty), grouped by label y."""
    labels = sorted(set(y.tolist()))
    out = np.zeros(X.shape[1])
    for j in range(X.shape[1]):
        groups = [X[y == c, j].tolist() for c in labels]
        out[j] = disc.fisher_ratio(groups)
    return out


def nearest_fact_fit_predict(Xtr, ytr, Xte, *, use_cols=None):
    """donkey=0 held-Argmin. Standardize by train mean/std, weight each feature by sqrt(train
    Fisher), class-mean per fact from train, predict test by nearest class-mean (Euclidean argmin
    in the discriminative space). `use_cols` restricts to a channel's columns."""
    cols = np.arange(Xtr.shape[1]) if use_cols is None else np.asarray(use_cols)
    Xtr, Xte = Xtr[:, cols], Xte[:, cols]
    mu = Xtr.mean(0); sd = Xtr.std(0)
    sd = np.where(sd < EPS, 1.0, sd)
    Ztr = (Xtr - mu) / sd
    Zte = (Xte - mu) / sd
    fish = _fisher_per_feature(Ztr, ytr)
    w = np.sqrt(np.maximum(fish, 0.0))
    if w.sum() < EPS:
        w = np.ones_like(w)
    Ztr *= w; Zte *= w
    labels = sorted(set(ytr.tolist()))
    means = np.array([Ztr[ytr == c].mean(0) for c in labels])
    d = ((Zte[:, None, :] - means[None, :, :]) ** 2).sum(2)
    pred_idx = d.argmin(1)
    return np.array([labels[i] for i in pred_idx])


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - hw) / d, (c + hw) / d)


# ============================================================================================== #
#  STAGE 1 -- load + extract features (the long pole; cached).
# ============================================================================================== #
def stage_features(limit_writers=None):
    t0 = time.time()
    print(f"[stage1] loading DigiLeTs (limit_writers={limit_writers}) ...", flush=True)
    samples = pw.load_digilets_samples(limit_writers=limit_writers)
    print(f"[stage1] {len(samples)} instances loaded in {time.time()-t0:.1f}s; extracting features ...",
          flush=True)
    X = np.zeros((len(samples), len(FEATURE_NAMES)))
    writer = []; gender = []; age = []; hand = []; klass = []
    for i, s in enumerate(samples):
        X[i] = construction_features(s)
        writer.append(s["writer_id"]); gender.append(s["gender"])
        age.append(int(s["age"])); hand.append(s["hand"]); klass.append(int(s["class"]))
        if (i + 1) % 3000 == 0:
            print(f"[stage1]   {i+1}/{len(samples)} feats @ {time.time()-t0:.1f}s", flush=True)
    data = {"X": X, "writer": np.array(writer), "gender": np.array(gender),
            "age": np.array(age), "hand": np.array(hand), "klass": np.array(klass),
            "feature_names": FEATURE_NAMES}
    os.makedirs(CKPT_DIR, exist_ok=True)
    with open(os.path.join(CKPT_DIR, "features.pkl"), "wb") as f:
        pickle.dump(data, f)
    print(f"[stage1] DONE {X.shape} in {time.time()-t0:.1f}s -> {CKPT_DIR}/features.pkl", flush=True)
    return data


def load_features():
    with open(os.path.join(CKPT_DIR, "features.pkl"), "rb") as f:
        return pickle.load(f)


# ============================================================================================== #
#  STAGE 2 -- demographic recovery, leave-writers-out CV (writer-aggregated features).
# ============================================================================================== #
def _writer_aggregate(data):
    """Per-writer mean feature vector + the writer's fact labels."""
    writers = sorted(set(data["writer"].tolist()))
    Xw = np.zeros((len(writers), data["X"].shape[1]))
    facts = {"gender": [], "hand": [], "age": []}
    for i, w in enumerate(writers):
        m = data["writer"] == w
        Xw[i] = data["X"][m].mean(0)
        facts["gender"].append(data["gender"][m][0])
        facts["hand"].append(data["hand"][m][0])
        facts["age"].append(int(data["age"][m][0]))
    return writers, Xw, facts


def _age_bin(ages):
    """Pre-registered age bin: young (<=22) vs old (>=23), the median-ish split of DigiLeTs'
    narrow 17-33 student range. Documented, not tuned after seeing results."""
    return np.array(["old" if a >= 23 else "young" for a in ages])


def _kfold_cv(Xw, y, n_folds, seed):
    """Leave-writers-out K-fold: every writer tested exactly once. Returns pooled (pred, true)."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(y))
    folds = np.array_split(order, n_folds)
    preds = np.empty(len(y), dtype=object)
    for te in folds:
        tr = np.setdiff1d(order, te)
        # need >=2 classes in train
        if len(set(y[tr].tolist())) < 2:
            preds[te] = y[tr][0] if len(tr) else y[te[0]]
            continue
        preds[te] = nearest_fact_fit_predict(Xw[tr], y[tr], Xw[te])
    return preds, y


def _channel_fisher(Xw, y):
    """Descriptive Fisher per channel (max over the channel's features) + best feature, all writers."""
    fish = _fisher_per_feature((Xw - Xw.mean(0)) / np.where(Xw.std(0) < EPS, 1.0, Xw.std(0)), y)
    out = {}
    for ch, feats in CHANNELS.items():
        cols = [FIDX[f] for f in feats]
        j = cols[int(np.argmax([fish[c] for c in cols]))]
        out[ch] = (float(max(fish[c] for c in cols)), FEATURE_NAMES[j])
    return out, fish


def stage_demographics(n_folds=7, n_null=200, seed=20260706):
    data = load_features()
    writers, Xw, facts = _writer_aggregate(data)
    Xw = np.asarray(Xw)
    results = {}
    fact_labels = {"handedness": np.array(facts["hand"]),
                   "gender": np.array(facts["gender"]),
                   "age": _age_bin(facts["age"])}
    for fact, y in fact_labels.items():
        t0 = time.time()
        # base rate = majority class
        vals, cnts = np.unique(y, return_counts=True)
        base = float(cnts.max() / cnts.sum())
        # CV accuracy
        preds, true = _kfold_cv(Xw, y, n_folds, seed)
        acc_k = int((preds == true).sum()); n = len(true)
        p, lo, hi = wilson(acc_k, n)
        # shuffled-label null
        rng = np.random.default_rng(seed + 1)
        null_accs = []
        for _ in range(n_null):
            yp = rng.permutation(y)
            pr, tr = _kfold_cv(Xw, yp, n_folds, seed)
            null_accs.append(float((pr == tr).mean()))
        null_accs = np.array(null_accs)
        # per-channel CV accuracy (which channel drives it)
        ch_acc = {}
        for ch, feats in CHANNELS.items():
            cols = [FIDX[f] for f in feats]
            rng2 = np.random.default_rng(seed)
            order = rng2.permutation(n)
            folds = np.array_split(order, n_folds)
            pr = np.empty(n, dtype=object)
            for te in folds:
                trr = np.setdiff1d(order, te)
                if len(set(y[trr].tolist())) < 2:
                    pr[te] = y[trr][0]; continue
                pr[te] = nearest_fact_fit_predict(Xw[trr], y[trr], Xw[te], use_cols=cols)
            ch_acc[ch] = float((pr == y).mean())
        ch_fisher, _ = _channel_fisher(Xw, y)
        results[fact] = {
            "n_writers": n, "base_rate": base, "classes": dict(zip(vals.tolist(), cnts.tolist())),
            "cv_acc": p, "cv_ci": (lo, hi), "cv_correct": acc_k,
            "null_mean": float(null_accs.mean()), "null_p95": float(np.percentile(null_accs, 95)),
            "null_max": float(null_accs.max()),
            "channel_acc": ch_acc, "channel_fisher": ch_fisher,
            "recoverable": bool(lo > base and p > np.percentile(null_accs, 95)),
        }
        print(f"[stage2] {fact}: acc={p:.3f} [{lo:.3f},{hi:.3f}] base={base:.3f} "
              f"null={null_accs.mean():.3f}(p95={np.percentile(null_accs,95):.3f}) "
              f"recoverable={results[fact]['recoverable']} ({time.time()-t0:.1f}s)", flush=True)
        best_ch = max(ch_acc.items(), key=lambda kv: kv[1])
        print(f"[stage2]   channels acc={ {k: round(v,3) for k,v in ch_acc.items()} } "
              f"best={best_ch[0]}", flush=True)
    with open(os.path.join(CKPT_DIR, "demographics.pkl"), "wb") as f:
        pickle.dump(results, f)
    return results


# ============================================================================================== #
#  STAGE 3 -- writer-identity, biometric character-split (per-instance features).
# ============================================================================================== #
def stage_identity(seed=20260706, n_null=100):
    data = load_features()
    X, writer, klass = data["X"], data["writer"], data["klass"]
    writers = sorted(set(writer.tolist()))
    classes = sorted(set(klass.tolist()))
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(classes))
    train_cls = set(np.array(classes)[perm[: len(classes) // 2]].tolist())
    tr_mask = np.array([c in train_cls for c in klass])
    te_mask = ~tr_mask
    print(f"[stage3] identity: {len(writers)} writers, split {tr_mask.sum()} train-inst / "
          f"{te_mask.sum()} test-inst by DISJOINT character sets", flush=True)
    Xtr, ytr = X[tr_mask], writer[tr_mask]
    Xte, yte = X[te_mask], writer[te_mask]
    pred = nearest_fact_fit_predict(Xtr, ytr, Xte)
    k = int((pred == yte).sum()); n = len(yte)
    p, lo, hi = wilson(k, n)
    # base rate = largest writer's share of test instances
    vals, cnts = np.unique(yte, return_counts=True)
    base = float(cnts.max() / cnts.sum())
    # descriptive Fisher over 77 writer groups, per feature, per channel
    Z = (X - X.mean(0)) / np.where(X.std(0) < EPS, 1.0, X.std(0))
    fish = _fisher_per_feature(Z, writer)
    ch_fisher = {}
    for ch, feats in CHANNELS.items():
        cols = [FIDX[f] for f in feats]
        j = cols[int(np.argmax([fish[c] for c in cols]))]
        ch_fisher[ch] = (float(max(fish[c] for c in cols)), FEATURE_NAMES[j])
    # per-channel identity accuracy
    ch_acc = {}
    for ch, feats in CHANNELS.items():
        cols = [FIDX[f] for f in feats]
        pr = nearest_fact_fit_predict(Xtr, ytr, Xte, use_cols=cols)
        ch_acc[ch] = float((pr == yte).mean())
    # shuffled-writer null
    rngn = np.random.default_rng(seed + 7)
    null_accs = []
    for _ in range(n_null):
        yp = rngn.permutation(ytr)
        pr = nearest_fact_fit_predict(Xtr, yp, Xte)
        null_accs.append(float((pr == yte).mean()))
    null_accs = np.array(null_accs)
    res = {"n_test": n, "acc": p, "ci": (lo, hi), "base_rate": base, "n_way": len(writers),
           "null_mean": float(null_accs.mean()), "null_p95": float(np.percentile(null_accs, 95)),
           "channel_acc": ch_acc, "channel_fisher": ch_fisher,
           "recoverable": bool(lo > base and p > np.percentile(null_accs, 95))}
    print(f"[stage3] identity: acc={p:.3f} [{lo:.3f},{hi:.3f}] base={base:.4f} "
          f"({len(writers)}-way) null={null_accs.mean():.4f} recoverable={res['recoverable']}",
          flush=True)
    print(f"[stage3]   channels acc={ {k2: round(v,3) for k2,v in ch_acc.items()} }", flush=True)
    with open(os.path.join(CKPT_DIR, "identity.pkl"), "wb") as f:
        pickle.dump(res, f)
    return res


# ============================================================================================== #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["features", "demographics", "identity", "report"])
    ap.add_argument("--limit-writers", type=int, default=None)
    ap.add_argument("--n-null", type=int, default=200)
    args = ap.parse_args()

    md5_before = seed_md5()
    print(f"[seed-guard] {SEED_FILE} md5={md5_before}", flush=True)

    if args.stage == "features":
        stage_features(limit_writers=args.limit_writers)
    elif args.stage == "demographics":
        stage_demographics(n_null=args.n_null)
    elif args.stage == "identity":
        stage_identity(n_null=min(args.n_null, 100))
    elif args.stage == "report":
        print_report()

    md5_after = seed_md5()
    assert md5_after == md5_before, f"SEED MUTATED! {md5_before} -> {md5_after}"
    print(f"[seed-guard] OK unchanged md5={md5_after}", flush=True)


def print_report():
    with open(os.path.join(CKPT_DIR, "demographics.pkl"), "rb") as f:
        demo = pickle.load(f)
    with open(os.path.join(CKPT_DIR, "identity.pkl"), "rb") as f:
        ident = pickle.load(f)
    print("\n==================== RUN 60 RECOVERABILITY TABLE ====================", flush=True)
    print(f"{'FACT':<12}{'held-acc':>10}{'95% CI':>18}{'base':>8}{'null_p95':>10}"
          f"{'recov':>7}  driver-channel", flush=True)
    for fact in ("handedness", "gender", "age"):
        r = demo[fact]
        best = max(r["channel_acc"].items(), key=lambda kv: kv[1])
        print(f"{fact:<12}{r['cv_acc']:>10.3f}{'['+format(r['cv_ci'][0],'.3f')+','+format(r['cv_ci'][1],'.3f')+']':>18}"
              f"{r['base_rate']:>8.3f}{r['null_p95']:>10.3f}{str(r['recoverable']):>7}  "
              f"{best[0]}({best[1]:.3f})", flush=True)
    r = ident
    best = max(r["channel_acc"].items(), key=lambda kv: kv[1])
    print(f"{'identity':<12}{r['acc']:>10.3f}{'['+format(r['ci'][0],'.3f')+','+format(r['ci'][1],'.3f')+']':>18}"
          f"{r['base_rate']:>8.4f}{r['null_p95']:>10.4f}{str(r['recoverable']):>7}  "
          f"{best[0]}({best[1]:.3f})", flush=True)
    print("=====================================================================\n", flush=True)


if __name__ == "__main__":
    main()
