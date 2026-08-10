#!/usr/bin/env python3
"""DOES THE REPRESENTABLE REFUSAL SURVIVE THE NET'S HOME TURF? — block 130000.

Pre-registration: VISION_REFUSAL_NATURAL_PREREG.md (committed before any number).

The honest boundary test 129000 (VISION_REFUSAL_USEFULNESS) named for itself.
129000 CONFIRMED, on Omniglot (raw-distance-friendly), that the substrate's
reconstruction-residual refusal (a COMPARISON) beats a net's best OOD detectors.
This rung runs it in the HOSTILE regime — natural images (CIFAR-10), where raw
pixel distance is WEAK and a net's learned features dominate — and separates
MECHANISM from REPRESENTATION with two comparisons:

  END-TO-END           substrate_residual_raw (nearest-held-exemplar L2 in RAW
                       pixels) vs the net's full OOD pipeline.
  REPRESENTATION-      substrate_residual_feat (nearest-held-prototype L2 in the
    CONTROLLED         NET'S OWN penultimate features) vs net MSP/energy in the
                       SAME features. The decisive number.

The substrate COMPARISON mechanism = nearest-prototype reconstruction residual
r(x)=min_p ||x-p||: the SAME analysis-by-synthesis the arc built (PointSetDist is
its trajectory realization; the L2 leaf is term.rs::feature_distance), realized
host-side IDENTICALLY across raw and feature representations so the ONLY thing
that varies is the representation. The net + detectors are measured BASELINES.

FAIRNESS (§13): every threshold = the alpha-quantile of the arm's own signal on
in-dist VAL (matched in-dist false-refuse rate), on in-dist data ONLY. AUROC/AUPR
threshold-free. PAIRED bootstrap on the AUROC difference is the powered test.

Run:  PYTHONPATH=.:runners/dsl/python OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
      python scripts/refusal_natural_measure.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

from domains import engine_provenance  # noqa: E402
engine_provenance.engine_preamble()

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
import scipy.io as sio  # noqa: E402
from sklearn.metrics import roc_auc_score, average_precision_score  # noqa: E402

import substrate_rs as srs  # noqa: E402  (engine import + provenance; mechanism note in prereg §6)

torch.set_num_threads(2)

EXPECT_ENGINE = os.environ.get("EXPECT_ENGINE", "")
PROV = engine_provenance.provenance_line()
if EXPECT_ENGINE and EXPECT_ENGINE not in PROV:
    raise SystemExit(f"ENGINE MISMATCH: expected {EXPECT_ENGINE!r} in {PROV!r}")
# assert we are measuring THIS tree's engine (own/shared), never a foreign build.
_prov_rec = engine_provenance.assert_measuring_engine()
assert _prov_rec["source_match"] in ("own", "shared"), _prov_rec["source_match"]

DATA = ROOT / "var" / "ood_data"

# ---- fixed hyperparameters (registered) ------------------------------------
IN_CLASSES = [0, 1, 2, 3, 4, 5]      # CIFAR-10 in-dist (airplane..dog)
OOD_CLASSES = [6, 7, 8, 9]           # CIFAR-10 held-out (frog,horse,ship,truck) = NEAR-OOD
K = len(IN_CLASSES)
M_TRAIN = 1500                       # per-class net-train + substrate-codebook exemplars
M_VAL = 200                          # per-class in-dist validation (threshold only)
M_TEST = 500                         # per-class in-dist test
N_NEAR = 500                         # per held-out class (near-OOD)
N_FAR = 2000                         # per far-OOD sub-kind
EPOCHS = 25
BATCH = 128
LR = 1e-3
KNN_K = 5                            # Sun 2022
ALPHAS = [0.05, 0.10, 0.20]
COST_RATIOS = [2, 5, 10, 20, 50]
RHO_GRID = [round(x, 3) for x in np.linspace(0.0, 1.0, 21)]
BOOT = 1000
PAIRED_BOOT = 2000
BOOT_SEED = 130100


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------
def _load_cifar():
    """uint8 NxHxWx3 images + int labels for train and test."""
    tr = np.load(DATA / "cifar_train.npz")
    te = np.load(DATA / "cifar_test.npz")
    return (tr["img"], tr["label"]), (te["img"], te["label"])


def _load_svhn(n, rng):
    m = sio.loadmat(DATA / "svhn_test_32x32.mat")
    X = m["X"].transpose(3, 0, 1, 2)  # (N,32,32,3) uint8
    idx = rng.permutation(len(X))[:n]
    return X[idx].astype(np.uint8)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def _corrupt(imgs, rng, block=4):
    """Severe corruption: shuffle 4x4 pixel blocks within each image. Same marginal
    pixel statistics, no coherent object."""
    out = imgs.copy()
    H = imgs.shape[1]
    nb = H // block
    for i in range(len(out)):
        order = rng.permutation(nb * nb)
        blocks = out[i].reshape(nb, block, nb, block, 3).transpose(0, 2, 1, 3, 4).reshape(nb * nb, block, block, 3)
        blocks = blocks[order]
        out[i] = blocks.reshape(nb, nb, block, block, 3).transpose(0, 2, 1, 3, 4).reshape(H, H, 3)
    return out


def build_data(split_seed):
    rng = np.random.default_rng(split_seed)
    (Xtr, ytr), (Xte, yte) = _load_cifar()

    # in-dist train/val from CIFAR TRAIN (disjoint slices), test from CIFAR TEST.
    train_img, train_y, val_img, val_y = [], [], [], []
    for new_c, c in enumerate(IN_CLASSES):
        pool = np.where(ytr == c)[0]
        pool = pool[rng.permutation(len(pool))]
        tr_idx = pool[:M_TRAIN]
        val_idx = pool[M_TRAIN:M_TRAIN + M_VAL]
        train_img.append(Xtr[tr_idx]); train_y.append(np.full(len(tr_idx), new_c))
        val_img.append(Xtr[val_idx]); val_y.append(np.full(len(val_idx), new_c))
    test_img, test_y = [], []
    for new_c, c in enumerate(IN_CLASSES):
        pool = np.where(yte == c)[0]
        pool = pool[rng.permutation(len(pool))][:M_TEST]
        test_img.append(Xte[pool]); test_y.append(np.full(len(pool), new_c))

    train_img = np.concatenate(train_img); train_y = np.concatenate(train_y)
    val_img = np.concatenate(val_img); val_y = np.concatenate(val_y)
    test_img = np.concatenate(test_img); test_y = np.concatenate(test_y)

    # NEAR-OOD: held-out CIFAR classes from the TEST split.
    near = []
    for c in OOD_CLASSES:
        pool = np.where(yte == c)[0]
        pool = pool[rng.permutation(len(pool))][:N_NEAR]
        near.append(Xte[pool])
    near = np.concatenate(near)

    # FAR-OOD sub-kinds.
    rsv = np.random.default_rng(split_seed + 1)
    far_svhn = _load_svhn(N_FAR, rsv)
    rgs = np.random.default_rng(split_seed + 2)
    far_gauss = np.clip(rgs.normal(0.5, 0.25, (N_FAR, 32, 32, 3)) * 255, 0, 255).astype(np.uint8)
    rco = np.random.default_rng(130002)
    corrupt_src = Xte[np.where(np.isin(yte, IN_CLASSES))[0]]
    corrupt_src = corrupt_src[rco.permutation(len(corrupt_src))][:N_FAR]
    far_corrupt = _corrupt(corrupt_src, rco)

    return dict(
        train=(train_img, train_y), val=(val_img, val_y), test=(test_img, test_y),
        near=near,
        far={"svhn": far_svhn, "gauss": far_gauss, "corrupt": far_corrupt},
        classes=[f"cifar{c}" for c in IN_CLASSES],
    )


# ---------------------------------------------------------------------------
# NORMALIZATION (per-channel, fit on in-dist TRAIN only)
# ---------------------------------------------------------------------------
def _fit_norm(train_img):
    x = train_img.astype(np.float32) / 255.0
    mean = x.reshape(-1, 3).mean(0)
    std = x.reshape(-1, 3).std(0) + 1e-6
    return mean.astype(np.float32), std.astype(np.float32)


def _to_chw(img, mean, std):
    x = img.astype(np.float32) / 255.0
    x = (x - mean) / std
    return x.transpose(0, 3, 1, 2).astype(np.float32)  # NCHW


# ---------------------------------------------------------------------------
# NET (a real CNN with BN; the net's home turf — do not strawman)
# ---------------------------------------------------------------------------
class CNN(nn.Module):
    def __init__(self, k):
        super().__init__()
        self.c = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2))
        self.body = nn.Sequential(nn.Flatten(), nn.Dropout(0.3),
                                  nn.Linear(128 * 4 * 4, 256), nn.ReLU())
        self.head = nn.Linear(256, k)

    def features(self, x):
        return self.body(self.c(x))

    def forward(self, x):
        return self.head(self.features(x))


def _train(model, Xtr, Ytr, seed):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, EPOCHS)
    lossf = nn.CrossEntropyLoss()
    Xt = torch.tensor(Xtr); Yt = torch.tensor(Ytr)
    n = len(Xt)
    g = torch.Generator().manual_seed(seed)
    t0 = time.time()
    for _ in range(EPOCHS):
        model.train()
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, BATCH):
            b = perm[i:i + BATCH]
            xb = Xt[b]
            # cheap augmentation: random horizontal flip (strengthens features)
            flip = torch.rand(len(b), generator=g) < 0.5
            xb = xb.clone()
            xb[flip] = torch.flip(xb[flip], dims=[3])
            opt.zero_grad()
            loss = lossf(model(xb), Yt[b])
            loss.backward(); opt.step()
        sched.step()
    return time.time() - t0


def _batched(fn, X, bs=512):
    outs = []
    for i in range(0, len(X), bs):
        outs.append(fn(torch.tensor(X[i:i + bs])))
    return np.concatenate(outs, 0)


def _logits(model, X):
    model.eval()
    with torch.no_grad():
        return _batched(lambda t: model(t).numpy(), X)


def _features(model, X):
    model.eval()
    with torch.no_grad():
        return _batched(lambda t: model.features(t).numpy(), X)


# ---------------------------------------------------------------------------
# THE COMPARISON MECHANISM — nearest-prototype reconstruction residual
# (identical code for RAW pixels and NET features; only the representation varies)
# ---------------------------------------------------------------------------
def nn_residual(held, queries, chunk=1000):
    """r(x) = min over held prototypes p of ||x - p|| (Euclidean 1-NN residual).
    The AbS reconstruction residual: reconstruct x by its nearest held exemplar,
    residual = the mismatch. Chunked over queries for memory."""
    held = held.astype(np.float32)
    hn = (held ** 2).sum(1)
    out = np.empty(len(queries), np.float32)
    for i in range(0, len(queries), chunk):
        q = queries[i:i + chunk].astype(np.float32)
        d2 = (q ** 2).sum(1)[:, None] + hn[None, :] - 2.0 * q @ held.T
        out[i:i + chunk] = np.sqrt(np.maximum(d2, 0.0)).min(1)
    return out


def nn_predict(held, held_y, queries, chunk=1000):
    """1-NN class prediction (for in-dist accuracy of the substrate arm)."""
    held = held.astype(np.float32)
    hn = (held ** 2).sum(1)
    pred = np.empty(len(queries), np.int64)
    for i in range(0, len(queries), chunk):
        q = queries[i:i + chunk].astype(np.float32)
        d2 = (q ** 2).sum(1)[:, None] + hn[None, :] - 2.0 * q @ held.T
        pred[i:i + chunk] = held_y[np.argmin(d2, 1)]
    return pred


def centroid_residual(held, held_y, queries):
    """nearest-class-centroid residual (the prototype-set = class means check)."""
    mus = np.stack([held[held_y == c].mean(0) for c in range(K)]).astype(np.float32)
    hn = (mus ** 2).sum(1)
    q = queries.astype(np.float32)
    d2 = (q ** 2).sum(1)[:, None] + hn[None, :] - 2.0 * q @ mus.T
    return np.sqrt(np.maximum(d2, 0.0)).min(1)


# ---------------------------------------------------------------------------
# NET SELECTION + FEATURE-DISTANCE DETECTORS
# ---------------------------------------------------------------------------
def maha_fit(Ftr, ytr):
    mus = np.stack([Ftr[ytr == c].mean(0) for c in range(K)])
    cov = np.cov((Ftr - mus[ytr]).T) + 1e-6 * np.eye(Ftr.shape[1])
    prec = np.linalg.pinv(cov)
    return mus, prec


def maha_score(F, mus, prec):
    d = F[:, None, :] - mus[None, :, :]
    m = np.einsum("nkd,de,nke->nk", d, prec, d)
    return m.min(1)


def knn_score(F, Ftr, kk=KNN_K):
    Fn = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)
    Ftn = Ftr / (np.linalg.norm(Ftr, axis=1, keepdims=True) + 1e-9)
    out = np.empty(len(F), np.float32)
    for i in range(0, len(F), 1000):
        d = np.sqrt(np.maximum(0.0,
            (Fn[i:i + 1000] ** 2).sum(1)[:, None] + (Ftn ** 2).sum(1)[None, :]
            - 2 * Fn[i:i + 1000] @ Ftn.T))
        part = np.partition(d, kk, axis=1)[:, :kk + 1]
        out[i:i + 1000] = part[:, kk]
    return out


# ---------------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------------
def auroc_ci(in_scores, ood_scores, seed):
    y = np.concatenate([np.zeros(len(in_scores)), np.ones(len(ood_scores))])
    s = np.concatenate([in_scores, ood_scores])
    fin = np.isfinite(s); y = y[fin]; s = s[fin]
    au = roc_auc_score(y, s); ap = average_precision_score(y, s)
    rng = np.random.default_rng(seed)
    n = len(s); boots = []
    for _ in range(BOOT):
        idx = rng.integers(0, n, n)
        if len(np.unique(y[idx])) < 2:
            continue
        boots.append(roc_auc_score(y[idx], s[idx]))
    lo, hi = np.percentile(boots, [2.5, 97.5]) if boots else (au, au)
    return dict(auroc=float(au), aupr=float(ap), ci=[float(lo), float(hi)])


def paired_auroc_diff(in_a, ood_a, in_b, ood_b, seed):
    """PAIRED bootstrap on AUROC(a) - AUROC(b), SAME resampled inputs (powered)."""
    ni, no = len(in_a), len(ood_a)
    y = np.concatenate([np.zeros(ni), np.ones(no)])
    sa = np.concatenate([in_a, ood_a]); sb = np.concatenate([in_b, ood_b])
    fin = np.isfinite(sa) & np.isfinite(sb)
    y = y[fin]; sa = sa[fin]; sb = sb[fin]
    d0 = roc_auc_score(y, sa) - roc_auc_score(y, sb)
    rng = np.random.default_rng(seed)
    n = len(y); diffs = []
    for _ in range(PAIRED_BOOT):
        idx = rng.integers(0, n, n)
        if len(np.unique(y[idx])) < 2:
            continue
        diffs.append(roc_auc_score(y[idx], sa[idx]) - roc_auc_score(y[idx], sb[idx]))
    lo, hi = np.percentile(diffs, [2.5, 97.5]) if diffs else (d0, d0)
    return dict(diff=float(d0), ci=[float(lo), float(hi)], sep_pos=bool(lo > 0), sep_neg=bool(hi < 0))


def matched_threshold(val_scores, alpha):
    v = val_scores[np.isfinite(val_scores)]
    return float(np.quantile(v, 1.0 - alpha))


def cost_surface(refuses_test, wrong_test, refuses_ood, r):
    cost_in = np.mean(np.where(refuses_test, 1.0, np.where(wrong_test, r, 0.0)))
    cost_ood = np.mean(np.where(refuses_ood, 1.0, r))
    return {rho: float((1 - rho) * cost_in + rho * cost_ood) for rho in RHO_GRID}


# ---------------------------------------------------------------------------
# ONE SPLIT
# ---------------------------------------------------------------------------
def run_split(split_seed, net_seeds, verbose=True):
    if verbose:
        print(f"  [split {split_seed}] building CIFAR data ...", flush=True)
    data = build_data(split_seed)
    mean, std = _fit_norm(data["train"][0])

    tr_img, tr_y = data["train"]
    va_img, va_y = data["val"]
    te_img, te_y = data["test"]
    near_img = data["near"]

    Xtr = _to_chw(tr_img, mean, std)
    Xva = _to_chw(va_img, mean, std)
    Xte = _to_chw(te_img, mean, std)
    Xnear = _to_chw(near_img, mean, std)
    Xfar = {k: _to_chw(v, mean, std) for k, v in data["far"].items()}

    ood_pools = {"near": Xnear}
    ood_pools.update({f"far_{k}": v for k, v in Xfar.items()})
    far_all = np.concatenate([Xfar[k] for k in ("svhn", "gauss", "corrupt")], 0)

    n_far = {k: int(len(v)) for k, v in Xfar.items()}
    res = {"split_seed": split_seed, "classes": data["classes"],
           "n_test": int(len(te_y)), "n_val": int(len(va_y)),
           "n_near": int(len(Xnear)), "n_far": n_far,
           "indist_acc": {}, "arms": {}, "net_train_secs": {}}

    # ---- SUBSTRATE RAW arm (representation = raw pixels; deterministic) ----
    flat = lambda a: a.reshape(len(a), -1)
    held_raw = flat(Xtr)
    raw_test = nn_residual(held_raw, flat(Xte))
    raw_val = nn_residual(held_raw, flat(Xva))
    raw_near = nn_residual(held_raw, flat(Xnear))
    raw_far = {k: nn_residual(held_raw, flat(v)) for k, v in Xfar.items()}
    raw_far_all = np.concatenate([raw_far[k] for k in ("svhn", "gauss", "corrupt")])
    raw_pred = nn_predict(held_raw, tr_y, flat(Xte))
    res["indist_acc"]["substrate_residual_raw"] = float(np.mean(raw_pred == te_y))

    res["arms"]["substrate_residual_raw"] = {
        "auroc_near": auroc_ci(raw_test, raw_near, BOOT_SEED),
        "auroc_far": auroc_ci(raw_test, raw_far_all, BOOT_SEED + 1),
        "auroc_far_by_kind": {k: auroc_ci(raw_test, raw_far[k], BOOT_SEED + 5 + i)
                              for i, k in enumerate(raw_far)},
        "signal": "residual_raw_pixels", "representation": "raw",
    }

    # ---- NET arms over seeds (representation = learned features) ----
    NET_FEAT_ARMS = ("maha", "knn")
    NET_SEL_ARMS = ("msp", "energy")
    for arm in ["net_msp", "net_energy", "net_maha", "net_knn",
                "substrate_residual_feat", "substrate_residual_feat_centroid",
                "net_answer"]:
        res["arms"][arm] = {"per_seed": []}
    accs = []
    # keep per-seed raw signals of the FIRST seed for the cost surface + paired boot
    first_pack = {}
    for si, seed in enumerate(net_seeds):
        model = CNN(K)
        tsec = _train(model, Xtr, tr_y, seed)
        res["net_train_secs"][str(seed)] = round(tsec, 1)

        lg_te = _logits(model, Xte); lg_va = _logits(model, Xva)
        Fte = _features(model, Xte); Fva = _features(model, Xva)
        Ftr = _features(model, Xtr)
        mus, prec = maha_fit(Ftr, tr_y)

        def net_sig(lg, F):
            sm = torch.softmax(torch.tensor(lg), 1).numpy()
            return dict(msp=1.0 - sm.max(1),
                        energy=-np.log(np.exp(lg).sum(1) + 1e-12),
                        pred=lg.argmax(1),
                        maha=maha_score(F, mus, prec),
                        knn=knn_score(F, Ftr))

        s_te = net_sig(lg_te, Fte)
        s_va = net_sig(lg_va, Fva)
        acc = float(np.mean(s_te["pred"] == te_y)); accs.append(acc)

        # OOD signals per pool
        def sig_pool(X):
            return net_sig(_logits(model, X), _features(model, X))
        near_s = sig_pool(Xnear)
        far_s = {k: sig_pool(v) for k, v in Xfar.items()}
        far_all_s = {key: np.concatenate([far_s[k][key] for k in ("svhn", "gauss", "corrupt")])
                     for key in ("msp", "energy", "maha", "knn")}

        # substrate mechanism IN NET FEATURES (the representation-controlled arm)
        feat_test = nn_residual(Ftr, Fte)
        feat_val = nn_residual(Ftr, Fva)
        feat_near = nn_residual(Ftr, _features(model, Xnear))
        feat_far = {k: nn_residual(Ftr, _features(model, v)) for k, v in Xfar.items()}
        feat_far_all = np.concatenate([feat_far[k] for k in ("svhn", "gauss", "corrupt")])
        feat_pred = nn_predict(Ftr, tr_y, Fte)
        feat_acc = float(np.mean(feat_pred == te_y))
        # centroid variant
        Fnear = _features(model, Xnear)
        cen_test = centroid_residual(Ftr, tr_y, Fte)
        cen_val = centroid_residual(Ftr, tr_y, Fva)
        cen_near = centroid_residual(Ftr, tr_y, Fnear)
        cen_far_all = centroid_residual(Ftr, tr_y,
                        np.concatenate([_features(model, Xfar[k]) for k in ("svhn", "gauss", "corrupt")]))

        for arm, sk in (("net_msp", "msp"), ("net_energy", "energy"),
                        ("net_maha", "maha"), ("net_knn", "knn")):
            res["arms"][arm]["per_seed"].append({
                "seed": seed,
                "auroc_near": auroc_ci(s_te[sk], near_s[sk], BOOT_SEED + seed),
                "auroc_far": auroc_ci(s_te[sk], far_all_s[sk], BOOT_SEED + seed + 1),
                "auroc_far_by_kind": {k: auroc_ci(s_te[sk], far_s[k][sk], BOOT_SEED + seed + 5 + i)
                                      for i, k in enumerate(far_s)},
            })
        res["arms"]["substrate_residual_feat"]["per_seed"].append({
            "seed": seed, "indist_acc": feat_acc,
            "auroc_near": auroc_ci(feat_test, feat_near, BOOT_SEED + seed + 100),
            "auroc_far": auroc_ci(feat_test, feat_far_all, BOOT_SEED + seed + 101),
            "auroc_far_by_kind": {k: auroc_ci(feat_test, feat_far[k], BOOT_SEED + seed + 105 + i)
                                  for i, k in enumerate(feat_far)},
        })
        res["arms"]["substrate_residual_feat_centroid"]["per_seed"].append({
            "seed": seed,
            "auroc_near": auroc_ci(cen_test, cen_near, BOOT_SEED + seed + 200),
            "auroc_far": auroc_ci(cen_test, cen_far_all, BOOT_SEED + seed + 201),
        })
        res["arms"]["net_answer"]["per_seed"].append({"seed": seed, "acc": acc})

        if si == 0:
            first_pack = dict(
                s_te=s_te, s_va=s_va, near_s=near_s, far_all_s=far_all_s,
                wrong_test=(s_te["pred"] != te_y),
                feat_test=feat_test, feat_val=feat_val, feat_near=feat_near,
                feat_far_all=feat_far_all, feat_wrong=(feat_pred != te_y),
            )

    res["indist_acc"]["net"] = {"mean": float(np.mean(accs)), "std": float(np.std(accs)),
                                "per_seed": accs}
    res["indist_acc"]["substrate_residual_feat"] = {
        "per_seed": [e["indist_acc"] for e in res["arms"]["substrate_residual_feat"]["per_seed"]]}

    # ---- PAIRED bootstrap (the powered test), first net seed ----
    fp = first_pack
    paired = {}
    for pool_name, ood_key in (("near", "near_s"), ("far", "far_all_s")):
        if pool_name == "near":
            net_ood = fp["near_s"]; sub_feat_ood = fp["feat_near"]; sub_raw_ood = raw_near
        else:
            net_ood = fp["far_all_s"]; sub_feat_ood = fp["feat_far_all"]; sub_raw_ood = raw_far_all
        pp = {}
        # DECISIVE: comparison-in-features vs selection-in-features (SAME net features)
        for tgt in ("msp", "energy", "maha", "knn"):
            pp[f"feat_minus_{tgt}"] = paired_auroc_diff(
                fp["feat_test"], sub_feat_ood, fp["s_te"][tgt], net_ood[tgt],
                BOOT_SEED + hash(pool_name + tgt) % 1000)
        # END-TO-END: substrate raw vs the net's best-AUROC arm on this pool
        best_arm = max(("msp", "energy", "maha", "knn"),
                       key=lambda t: roc_auc_score(
                           np.concatenate([np.zeros(len(fp["s_te"][t])), np.ones(len(net_ood[t]))]),
                           np.concatenate([fp["s_te"][t], net_ood[t]])))
        pp["raw_minus_bestnet"] = {"best_net_arm": best_arm, **paired_auroc_diff(
            raw_test, sub_raw_ood, fp["s_te"][best_arm], net_ood[best_arm],
            BOOT_SEED + hash(pool_name + "raw") % 1000)}
        # also raw vs feat (does the substrate NEED the net's features?)
        pp["feat_minus_raw"] = paired_auroc_diff(
            fp["feat_test"], sub_feat_ood, raw_test, sub_raw_ood,
            BOOT_SEED + hash(pool_name + "fr") % 1000)
        paired[pool_name] = pp
    res["paired_bootstrap"] = paired

    # ---- cost surface + confident-wrong at matched op-points (first net seed) ----
    cost = {}; confab = {}
    for alpha in ALPHAS:
        arms_dec = {}
        # substrate raw
        tau = matched_threshold(raw_val, alpha)
        arms_dec["substrate_residual_raw"] = dict(
            rt=raw_test >= tau, wt=(raw_pred != te_y),
            near=raw_near >= tau, far=raw_far_all >= tau)
        # substrate feat
        tau = matched_threshold(fp["feat_val"], alpha)
        arms_dec["substrate_residual_feat"] = dict(
            rt=fp["feat_test"] >= tau, wt=fp["feat_wrong"],
            near=fp["feat_near"] >= tau, far=fp["feat_far_all"] >= tau)
        # net arms
        for arm, sk in (("net_msp", "msp"), ("net_energy", "energy"),
                        ("net_maha", "maha"), ("net_knn", "knn")):
            tau = matched_threshold(fp["s_va"][sk], alpha)
            arms_dec[arm] = dict(rt=fp["s_te"][sk] >= tau, wt=fp["wrong_test"],
                                 near=fp["near_s"][sk] >= tau, far=fp["far_all_s"][sk] >= tau)
        arms_dec["net_answer"] = dict(
            rt=np.zeros(len(te_y), bool), wt=fp["wrong_test"],
            near=np.zeros(len(Xnear), bool), far=np.zeros(len(far_all), bool))

        surf = {}
        for pool in ("near", "far"):
            surf[pool] = {}
            for arm, d in arms_dec.items():
                surf[pool][arm] = {str(r): cost_surface(d["rt"], d["wt"], d[pool], r)
                                   for r in COST_RATIOS}
                surf[pool][arm]["_indist_refuse"] = float(np.mean(d["rt"]))
                surf[pool][arm]["_ood_refuse"] = float(np.mean(d[pool]))
        cost[f"a{alpha}"] = surf

        # confident-wrong on NEAR-OOD (the discriminating pool)
        tau_m = matched_threshold(fp["s_va"]["msp"], alpha)
        near_msp = fp["near_s"]["msp"]
        confab[f"a{alpha}"] = {
            "net_answer_confident_wrong_frac_near": float(np.mean(near_msp < tau_m)),
            "near_median_msp": float(np.median(1.0 - near_msp)),
            "near_frac_msp_gt_0.9": float(np.mean((1.0 - near_msp) > 0.9)),
            "substrate_feat_misses_near": float(np.mean(arms_dec["substrate_residual_feat"]["near"] == False)),
            "substrate_raw_misses_near": float(np.mean(arms_dec["substrate_residual_raw"]["near"] == False)),
            "net_maha_misses_near": float(np.mean(arms_dec["net_maha"]["near"] == False)),
        }
    res["cost_surface"] = cost
    res["confabulation"] = confab
    res["crossover"] = crossover_summary(cost, "0.1")
    return res


def crossover_summary(cost, alpha_tag):
    surf = cost[f"a{float(alpha_tag)}"]
    out = {}
    for pool in ("near", "far"):
        sp = surf[pool]
        net_arms = [a for a in sp if a.startswith("net_")]
        po = {"winner_grid": {}, "sub_feat_beats_best_net": {}, "sub_raw_beats_best_net": {}}
        for r in COST_RATIOS:
            rs = str(r); wg = {}; fb = {}; rb = {}
            for rho in RHO_GRID:
                costs = {a: sp[a][rs][rho] for a in sp if not a.startswith("_")
                         and isinstance(sp[a], dict) and rs in sp[a]}
                wg[rho] = min(costs, key=costs.get)
                best_net = min(sp[a][rs][rho] for a in net_arms)
                fb[rho] = bool(sp["substrate_residual_feat"][rs][rho] < best_net - 1e-9)
                rb[rho] = bool(sp["substrate_residual_raw"][rs][rho] < best_net - 1e-9)
            po["winner_grid"][rs] = wg
            po["sub_feat_beats_best_net"][rs] = fb
            po["sub_raw_beats_best_net"][rs] = rb
        out[pool] = po
    return out


def main():
    t0 = time.time()
    print("=" * 92)
    print("DOES THE REPRESENTABLE REFUSAL SURVIVE THE NET'S HOME TURF? — CIFAR-10 OOD")
    print(PROV)
    print(f"loadavg start: {os.getloadavg()}  torch_threads={torch.get_num_threads()}")
    print("=" * 92)

    result = {
        "provenance": PROV,
        "engine_source_match": _prov_rec["source_match"],
        "loadavg_start": os.getloadavg(),
        "torch_threads": torch.get_num_threads(),
        "data_sha": {"cifar_train": _sha(DATA / "cifar_train.npz"),
                     "cifar_test": _sha(DATA / "cifar_test.npz"),
                     "svhn": _sha(DATA / "svhn_test_32x32.mat")},
        "params": dict(IN_CLASSES=IN_CLASSES, OOD_CLASSES=OOD_CLASSES, K=K,
                       M_TRAIN=M_TRAIN, M_VAL=M_VAL, M_TEST=M_TEST, N_NEAR=N_NEAR,
                       N_FAR=N_FAR, EPOCHS=EPOCHS, BATCH=BATCH, LR=LR, KNN_K=KNN_K,
                       ALPHAS=ALPHAS, COST_RATIOS=COST_RATIOS, BOOT=BOOT,
                       PAIRED_BOOT=PAIRED_BOOT, BOOT_SEED=BOOT_SEED),
        "splits": [],
    }
    result["splits"].append(run_split(130000, [130001, 130002, 130003]))
    for ss in (130020, 130021):
        result["splits"].append(run_split(ss, [130001, 130002]))

    result["loadavg_end"] = os.getloadavg()
    result["elapsed_secs"] = round(time.time() - t0, 1)
    result["provenance_after"] = engine_provenance.provenance_line()

    outp = ROOT / "results" / "refusal_natural.json"
    outp.parent.mkdir(exist_ok=True)
    outp.write_text(json.dumps(result, indent=2))
    print(f"\n  wrote {outp}")
    print(f"  elapsed {result['elapsed_secs']}s  loadavg_end {result['loadavg_end']}")
    print(f"  provenance_after: {result['provenance_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
