#!/usr/bin/env python3
"""ARM B — PROSODIC-FELT PARSING LIFT on real RAVDESS wavs (speaker-independent).

Confirmatory measure for Arm B of the FELT-PROSODY x RAVDESS rung (prereg
`docs/research/psychology_affect/PROSODY_RAVDESS_PREREG.md`).

On the REAL RAVDESS wavs (NO synthesis) it extracts the prosodic-felt feature
vector via the SAME judge DSP, and classifies BINARY AROUSAL
(HIGH {angry, fearful, happy} vs LOW {calm, neutral}) with the felt-prosody vector
INCLUDED vs a BASELINE (the blind twin) that omits it. The pre-registered fixed
weight (lambda=1.0, both feature blocks standard-scaled), classifier (logistic
regression, C=1.0), and split (TRAIN actors 01-16, TEST actors 17-24) are used
exactly. Reports:

  * FELT model  = [energy_mean, f0_mean, contour]   (the judge's own outputs)
  * BLIND twin  = [duration_s, zcr]                 (the byte-identical control)
  * LIFT = accuracy(felt) - accuracy(blind) on held-out TEST actors, bootstrap CI.
  * secondary: fine-grained 8-way accuracy (expected LIMITED per the §0 caveat).

HONEST lift-or-null: the real number is reported even if ~0.

Logistic regression is implemented in numpy (frozen L2 C=1.0, gradient descent)
so this measure runs with ONLY stdlib `wave` + numpy — no sklearn / soundfile /
scipy dependency (those are absent in this env; that absence is NOT this rung's
failure). The model class / regularization / features / split / metric are the
pre-registered ones.

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term, no shaping.
Reads the judge features over vendored wavs and fits the frozen classifier. Writes
results/prosody_ravdess/parsing_lift.json.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import wave

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs.communication import (  # noqa: E402
    _energy_envelope, _estimate_f0_per_window, _zero_crossing_rate)

RAVDESS_DIR = os.path.join(_ROOT, "data", "ravdess")

# RAVDESS filename code 03-01-EE-II-SS-RR-AA.wav ; EE = emotion.
EMO_CODE = {1: "neutral", 2: "calm", 3: "happy", 4: "sad",
            5: "angry", 6: "fearful", 7: "disgust", 8: "surprised"}
HIGH_EMO = {"angry", "fearful", "happy"}
LOW_EMO = {"calm", "neutral"}
MID_EMO = {"sad", "disgust", "surprised"}
CONTOUR_CODE = {"flat": 0.0, "falling": -1.0, "rising": 1.0, "undulating": 2.0}

TRAIN_ACTORS = set(range(1, 17))     # 01-16
TEST_ACTORS = set(range(17, 25))     # 17-24

RNG_SEED = 295000
BOOT_REPS = 2000
LAMBDA = 1.0                          # fixed prior weight (== sklearn C=1.0)


# --------------------------------------------------------------------- IO
def _read_wav(path):
    with wave.open(path, "rb") as wf:
        fr = wf.getframerate()
        n = wf.getnframes()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        raw = wf.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        x = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) / 128.0 - 1.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x.astype(np.float32), fr


def _contour_of(f0_voiced):
    if len(f0_voiced) < 4:
        return "flat"
    x = np.arange(len(f0_voiced), dtype=np.float64)
    slope = float(np.polyfit(x, f0_voiced, 1)[0])
    if abs(slope) < 0.5:
        return "flat"
    return "rising" if slope > 0 else "falling"


def _features(path):
    """The judge-DSP features for one wav: (energy_mean, f0_mean, contour_code,
    duration_s, zcr). Returns None if unusable."""
    x, fr = _read_wav(path)
    if x is None or len(x) == 0 or fr == 0:
        return None
    en = _energy_envelope(x, fr)
    f0 = _estimate_f0_per_window(x, fr)
    v = f0[f0 > 0]
    energy_mean = float(en.mean()) if len(en) else 0.0
    f0_mean = float(v.mean()) if len(v) else 0.0
    contour = _contour_of(v)
    zcr = _zero_crossing_rate(x)
    duration_s = float(len(x)) / fr
    return dict(energy_mean=energy_mean, f0_mean=f0_mean,
                contour=CONTOUR_CODE.get(contour, 0.0),
                duration_s=duration_s, zcr=zcr)


def _parse(path):
    base = os.path.basename(path).replace(".wav", "")
    parts = base.split("-")
    if len(parts) != 7:
        return None, None
    emo = EMO_CODE.get(int(parts[2]))
    actor = int(parts[6])
    return emo, actor


def load_dataset():
    rows = []
    for actor_dir in sorted(glob.glob(os.path.join(RAVDESS_DIR, "Actor_*"))):
        for wav in sorted(glob.glob(os.path.join(actor_dir, "*.wav"))):
            emo, actor = _parse(wav)
            if emo is None:
                continue
            feat = _features(wav)
            if feat is None:
                continue
            feat["emotion"] = emo
            feat["actor"] = actor
            rows.append(feat)
    return rows


# ------------------------------------------------------ numpy logistic regression
def _standardize(train_X, X):
    mu = train_X.mean(axis=0)
    sd = train_X.std(axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd, mu, sd


def _fit_logreg(X, y, l2=1.0 / LAMBDA, iters=3000, lr=0.5):
    """Binary logistic regression by gradient descent with L2 penalty. l2 =
    1/C = 1/LAMBDA = 1.0 (matches the frozen C=1.0). Deterministic (no RNG in
    the fit; init at zeros)."""
    n, d = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])
    w = np.zeros(d + 1)
    for _ in range(iters):
        z = Xb @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        grad = Xb.T @ (p - y) / n
        grad[:-1] += l2 * w[:-1] / n          # L2 on weights, not bias
        w -= lr * grad
    return w


def _predict(w, X):
    Xb = np.hstack([X, np.ones((X.shape[0], 1))])
    return (1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))) >= 0.5


def _acc_with_features(rows, feat_names, label_fn, keep_fn):
    """Train on TRAIN actors, evaluate on TEST actors. Returns (test_acc,
    per-test-sample correct array, test_labels)."""
    tr = [r for r in rows if r["actor"] in TRAIN_ACTORS and keep_fn(r)]
    te = [r for r in rows if r["actor"] in TEST_ACTORS and keep_fn(r)]
    if not tr or not te:
        return None
    Xtr = np.array([[r[f] for f in feat_names] for r in tr], dtype=np.float64)
    Xte = np.array([[r[f] for f in feat_names] for r in te], dtype=np.float64)
    ytr = np.array([label_fn(r) for r in tr], dtype=np.float64)
    yte = np.array([label_fn(r) for r in te], dtype=np.float64)
    # standard-scale both blocks on TRAIN (so no block is implicitly privileged).
    Xtr_s, mu, sd = _standardize(Xtr, Xtr)
    Xte_s = (Xte - mu) / sd
    w = _fit_logreg(Xtr_s, ytr)
    pred = _predict(w, Xte_s)
    correct = (pred == (yte >= 0.5)).astype(np.float64)
    return float(correct.mean()), correct, yte


def _bootstrap_diff_ci(correct_a, correct_b, reps=BOOT_REPS, seed=RNG_SEED):
    """Bootstrap CI of the paired accuracy difference (felt - blind) over the SAME
    held-out test samples."""
    rng = np.random.default_rng(seed)
    n = len(correct_a)
    diffs = []
    for _ in range(reps):
        idx = rng.integers(0, n, size=n)
        diffs.append(correct_a[idx].mean() - correct_b[idx].mean())
    diffs = np.array(diffs)
    return (float(correct_a.mean() - correct_b.mean()),
            float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)))


# --------------------------------------------------------- multi-class (8-way)
def _fit_softmax(X, y, n_class, l2=1.0 / LAMBDA, iters=2000, lr=0.5):
    n, d = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])
    W = np.zeros((d + 1, n_class))
    Y = np.eye(n_class)[y.astype(int)]
    for _ in range(iters):
        Z = Xb @ W
        Z -= Z.max(axis=1, keepdims=True)
        P = np.exp(Z)
        P /= P.sum(axis=1, keepdims=True)
        grad = Xb.T @ (P - Y) / n
        grad[:-1] += l2 * W[:-1] / n
        W -= lr * grad
    return W


def _acc_8way(rows, feat_names):
    emos = sorted(EMO_CODE.values())
    emo_idx = {e: i for i, e in enumerate(emos)}
    tr = [r for r in rows if r["actor"] in TRAIN_ACTORS]
    te = [r for r in rows if r["actor"] in TEST_ACTORS]
    if not tr or not te:
        return None
    Xtr = np.array([[r[f] for f in feat_names] for r in tr], dtype=np.float64)
    Xte = np.array([[r[f] for f in feat_names] for r in te], dtype=np.float64)
    ytr = np.array([emo_idx[r["emotion"]] for r in tr])
    yte = np.array([emo_idx[r["emotion"]] for r in te])
    Xtr_s, mu, sd = _standardize(Xtr, Xtr)
    Xte_s = (Xte - mu) / sd
    W = _fit_softmax(Xtr_s, ytr, len(emos))
    Xb = np.hstack([Xte_s, np.ones((Xte_s.shape[0], 1))])
    pred = (Xb @ W).argmax(axis=1)
    return float((pred == yte).mean())


# ------------------------------------------------------------------- point-biserial
def _point_biserial(rows, feat, label_fn, keep_fn):
    sub = [r for r in rows if r["actor"] in TEST_ACTORS and keep_fn(r)]
    x = np.array([r[feat] for r in sub], dtype=np.float64)
    y = np.array([label_fn(r) for r in sub], dtype=np.float64)
    if x.std() == 0 or len(set(y.tolist())) < 2:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def run():
    rows = load_dataset()
    n_total = len(rows)

    def binary_keep(r):
        return r["emotion"] in HIGH_EMO or r["emotion"] in LOW_EMO

    def binary_label(r):
        return 1.0 if r["emotion"] in HIGH_EMO else 0.0

    felt_feats = ["energy_mean", "f0_mean", "contour"]
    blind_feats = ["duration_s", "zcr"]

    felt = _acc_with_features(rows, felt_feats, binary_label, binary_keep)
    blind = _acc_with_features(rows, blind_feats, binary_label, binary_keep)
    if felt is None or blind is None:
        raise RuntimeError("insufficient data for train/test split")
    felt_acc, felt_correct, _ = felt
    blind_acc, blind_correct, yte = blind

    lift, lift_lo, lift_hi = _bootstrap_diff_ci(felt_correct, blind_correct)

    # majority-class baseline on TEST (context for the accuracy numbers).
    maj = max(float(yte.mean()), 1.0 - float(yte.mean()))

    # point-biserial of the reliable axes with the HIGH/LOW label (sign check).
    pb_energy = _point_biserial(rows, "energy_mean", binary_label, binary_keep)
    pb_f0 = _point_biserial(rows, "f0_mean", binary_label, binary_keep)

    # secondary 8-way (expected LIMITED — valence not separated).
    acc8_felt = _acc_8way(rows, felt_feats)
    acc8_blind = _acc_8way(rows, blind_feats)

    # counts per split for transparency.
    n_train = sum(1 for r in rows if r["actor"] in TRAIN_ACTORS)
    n_test = sum(1 for r in rows if r["actor"] in TEST_ACTORS)
    n_test_binary = sum(1 for r in rows if r["actor"] in TEST_ACTORS and binary_keep(r))

    result = dict(
        block=295000, arm="B_parsing_lift",
        n_total=n_total, n_train=n_train, n_test=n_test,
        n_test_binary=n_test_binary,
        train_actors=sorted(TRAIN_ACTORS), test_actors=sorted(TEST_ACTORS),
        lambda_prior_weight=LAMBDA, classifier="logreg_numpy_C1.0_L2",
        boot_reps=BOOT_REPS,
        felt_features=felt_feats, blind_features=blind_feats,
        felt_accuracy=round(felt_acc, 4),
        blind_accuracy=round(blind_acc, 4),
        majority_class_baseline=round(maj, 4),
        lift=round(lift, 4),
        lift_ci=[round(lift_lo, 4), round(lift_hi, 4)],
        lift_sign=("positive" if lift > 0 else "null/zero" if lift == 0 else "negative"),
        lift_ci_excludes_zero=bool(lift_lo > 0 or lift_hi < 0),
        point_biserial_energy=round(pb_energy, 4),
        point_biserial_f0=round(pb_f0, 4),
        acc_8way_felt=round(acc8_felt, 4) if acc8_felt is not None else None,
        acc_8way_blind=round(acc8_blind, 4) if acc8_blind is not None else None,
        acc_8way_chance=round(1.0 / len(EMO_CODE), 4),
        # verdicts
        verdict_positive_lift=bool(lift > 0),
        verdict_lift_significant=bool(lift_lo > 0),
        verdict_reliable_axes_sign_correct=bool(pb_energy > 0 and pb_f0 > 0),
        honest_note=(
            "Lift-or-null reported straight. The felt vector carries energy+f0 "
            "(which discriminate arousal ~10x per the RAVDESS regions); the blind "
            "twin carries duration+zcr (arousal-uninformative by design). 8-way is "
            "the weak secondary (valence not separated)."),
    )

    out_dir = os.path.join(_ROOT, "results", "prosody_ravdess")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "parsing_lift.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result, out_path


def main():
    result, path = run()
    print(f"[arm B] wrote {path}")
    print(f"  n_total={result['n_total']} train={result['n_train']} "
          f"test={result['n_test']} test_binary={result['n_test_binary']}")
    print(f"  FELT  acc = {result['felt_accuracy']}  [{result['felt_features']}]")
    print(f"  BLIND acc = {result['blind_accuracy']}  [{result['blind_features']}]")
    print(f"  majority-class baseline = {result['majority_class_baseline']}")
    print(f"  LIFT = {result['lift']}  CI={result['lift_ci']}  "
          f"sign={result['lift_sign']}  sig={result['verdict_lift_significant']}")
    print(f"  point-biserial: energy={result['point_biserial_energy']} "
          f"f0={result['point_biserial_f0']}")
    print(f"  8-way: felt={result['acc_8way_felt']} blind={result['acc_8way_blind']} "
          f"chance={result['acc_8way_chance']}")


if __name__ == "__main__":
    main()
