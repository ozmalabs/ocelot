#!/usr/bin/env python3
"""IS THE REPRESENTABLE REFUSAL WORTH ANYTHING? — the first useful-wedge number.

Pre-registration: VISION_REFUSAL_USEFULNESS_PREREG.md (committed before any number).

A selective-prediction / OOD-detection comparison on Omniglot online stroke
recognition. Four arms, the net given its BEST honest refusal:

  net_answer         softmax argmax, MUST answer (structurally cannot refuse)
  net_msp            SAME net + max-softmax-probability threshold (Hendrycks 2017)
  net_energy         SAME net + energy score -logsumexp(logits)   (Liu 2020)
  substrate_residual reconstruction-residual: PointSetDist(query, held-codebook
                     argmax winner) = the mismatch; refuse if > tolerance. The
                     EXISTING AbS machinery in domains/recognition_graph.py.

FAIRNESS (§13): every threshold is the alpha-quantile of the arm's own signal on
an in-dist VALIDATION set (matched in-dist false-refuse rate), chosen on in-dist
data ONLY, never on OOD. AUROC/AUPR are threshold-free.

Architecture: the substrate residual is graph-native (held PointSetDist Term +
argmax + residual read). The net is a measured BASELINE (host-side comparison
model — admissible). The harness is mechanical host I/O; no agent decision here.

Run:  PYTHONPATH=.:runners/dsl/python OMP_NUM_THREADS=2 \
      python scripts/refusal_usefulness_measure.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

# CPU discipline: <= 2 workers.
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

from domains import engine_provenance  # noqa: E402
engine_provenance.engine_preamble()

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from sklearn.metrics import roc_auc_score, average_precision_score  # noqa: E402

import substrate_rs as srs  # noqa: E402
from domains import glyph_motor_world as gm  # noqa: E402
from domains import omniglot_world as ow  # noqa: E402
from domains.recognition_graph import predict_pointset_term, pointset_error_term  # noqa: E402

torch.set_num_threads(2)

EXPECT_ENGINE = os.environ.get("EXPECT_ENGINE", "")
PROV = engine_provenance.provenance_line()
if EXPECT_ENGINE and EXPECT_ENGINE not in PROV:
    raise SystemExit(f"ENGINE MISMATCH: expected {EXPECT_ENGINE!r} in {PROV!r}")

# ---- fixed hyperparameters (registered) ------------------------------------
N = gm.N_POINTS                     # 48 arc-length-resampled trajectory points
K = 30                              # in-dist classes
N_KNOWN_ALPH = 15                   # first 15 background alphabets -> KNOWN
TRAIN_DR = list(range(0, 12))       # net train + codebook exemplars
VAL_DR = list(range(12, 15))        # in-dist val (threshold only)
TEST_DR = list(range(15, 20))       # in-dist test
N_OOD_EACH = 150                    # per OOD kind
IMG = 28                            # raster size for the CNN
ALPHAS = [0.05, 0.10, 0.20]         # matched in-dist FPR operating points
COST_RATIOS = [2, 5, 10, 20, 50]    # C_wrong / C_refuse
RHO_GRID = [round(x, 3) for x in np.linspace(0.0, 1.0, 21)]
BOOT = 1000
BOOT_SEED = 129100


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------
def _raster_from_strokes(strokes, size=IMG, pad=2):
    """Rasterize a list of (k,2) stroke point arrays into a size x size float image
    (0/1), normalized to a padded bounding box. Mechanical I/O for the CNN net."""
    pts = [s[:, :2].astype(float) for s in strokes if s.shape[0] >= 1]
    if not pts:
        return np.zeros((size, size), np.float32)
    allp = np.concatenate(pts, 0)
    lo = allp.min(0); hi = allp.max(0)
    span = np.maximum(hi - lo, 1e-6)
    scale = (size - 1 - 2 * pad) / span.max()
    img = np.zeros((size, size), np.float32)
    for s in pts:
        q = (s - lo) * scale + pad
        if q.shape[0] == 1:
            xi = int(round(q[0, 0])); yi = int(round(q[0, 1]))
            if 0 <= yi < size and 0 <= xi < size:
                img[yi, xi] = 1.0
            continue
        for i in range(len(q) - 1):
            a = q[i]; b = q[i + 1]
            steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
            for t in np.linspace(0, 1, steps):
                p = a + t * (b - a)
                xi = int(round(p[0])); yi = int(round(p[1]))
                if 0 <= yi < size and 0 <= xi < size:
                    img[yi, xi] = 1.0
    return img


def _noise_traj(rng):
    """A pen-like but meaningless trajectory: a random walk (cumulative Gaussian
    steps) resampled + normalized by the SAME pipeline as a real drawing."""
    k = int(rng.integers(30, 80))
    steps = rng.standard_normal((k, 2))
    walk = np.cumsum(steps, 0)
    return gm.to_trajectory(walk, N)


def _noise_strokes(rng):
    k = int(rng.integers(30, 80))
    walk = np.cumsum(rng.standard_normal((k, 2)), 0)
    # spread over a plausible box for rasterization
    return [walk * 20.0 + 50.0]


def build_data(split_seed):
    """Deterministic construction of in-dist classes, drawer splits, and the three
    OOD kinds. Returns a dict of trajectory arrays + raster images + labels."""
    rng = np.random.default_rng(split_seed)
    alphs = sorted(ow.alphabets("background"))
    known_alphs = alphs[:N_KNOWN_ALPH]
    ood_alphs = alphs[N_KNOWN_ALPH:]

    # pool of (alphabet, char_dir) from KNOWN alphabets with 20 drawings
    known_chars = []
    for a in known_alphs:
        for cd in ow.characters(a, "background"):
            if len(ow.drawings(cd)) >= 20:
                known_chars.append(cd)
    idx = rng.permutation(len(known_chars))[:K]
    classes = [known_chars[i] for i in idx]

    def traj(path):
        # whole-trajectory arc-length resample -> fixed (N,2); identical input for
        # BOTH arms (substrate PointSetDist and the net MLP).
        return ow.trajectory(path, N, per_stroke=False)

    def raster(path):
        return _raster_from_strokes(ow.load_strokes(path), IMG)

    data = {"classes": [os.path.basename(c) for c in classes]}
    # in-dist train / val / test
    for split_name, drs in (("train", TRAIN_DR), ("val", VAL_DR), ("test", TEST_DR)):
        T, X, Y = [], [], []
        for ci, cd in enumerate(classes):
            drw = ow.drawings(cd)
            for d in drs:
                T.append(traj(drw[d]))
                X.append(raster(drw[d]))
                Y.append(ci)
        data[split_name] = dict(traj=np.array(T, np.float32),
                                img=np.array(X, np.float32),
                                y=np.array(Y, np.int64))

    # OOD novel-class: drawings from OOD alphabets (disjoint classes)
    ood_chars = []
    for a in ood_alphs:
        for cd in ow.characters(a, "background"):
            if len(ow.drawings(cd)) >= 1:
                ood_chars.append(cd)
    rng2 = np.random.default_rng(split_seed + 1)
    pick = rng2.permutation(len(ood_chars))
    novel_T, novel_X = [], []
    ci = 0
    while len(novel_T) < N_OOD_EACH and ci < len(pick):
        cd = ood_chars[pick[ci]]; ci += 1
        drw = ow.drawings(cd)
        d = int(rng2.integers(len(drw)))
        novel_T.append(traj(drw[d])); novel_X.append(raster(drw[d]))
    # OOD noise
    rng3 = np.random.default_rng(split_seed + 2)
    noise_T = [_noise_traj(rng3) for _ in range(N_OOD_EACH)]
    rng3b = np.random.default_rng(split_seed + 2)
    noise_X = [_raster_from_strokes(_noise_strokes(rng3b), IMG) for _ in range(N_OOD_EACH)]
    # OOD ambiguous: two distinct in-dist-test drawings' strokes concatenated
    rng4 = np.random.default_rng(split_seed + 3)
    amb_T, amb_X = [], []
    for _ in range(N_OOD_EACH):
        a, b = rng4.permutation(len(classes))[:2]
        da = ow.drawings(classes[a])[int(rng4.integers(15, 20))]
        db = ow.drawings(classes[b])[int(rng4.integers(15, 20))]
        sa = ow.load_strokes(da); sb = ow.load_strokes(db)
        amb_X.append(_raster_from_strokes(sa + sb, IMG))
        allp = np.concatenate([s[:, :2] for s in (sa + sb) if s.shape[0] >= 1], 0)
        amb_T.append(gm.to_trajectory(allp, N))
    data["ood"] = {
        "novel": dict(traj=np.array(novel_T, np.float32), img=np.array(novel_X, np.float32)),
        "noise": dict(traj=np.array(noise_T, np.float32), img=np.array(noise_X, np.float32)),
        "ambiguous": dict(traj=np.array(amb_T, np.float32), img=np.array(amb_X, np.float32)),
    }
    return data


# ---------------------------------------------------------------------------
# SUBSTRATE RESIDUAL ARM  (graph-native: held PointSetDist + argmax + residual)
# ---------------------------------------------------------------------------
def substrate_residuals(data):
    """For every query return (residual, predicted_class). residual = min mismatch
    to the held codebook = PointSetDist(query, argmax winner). The codebook holds
    the in-dist TRAIN drawings (same data the net trains on)."""
    s = srs.Substrate()
    cls_of = {}
    for ci in range(K):
        pass
    tr = data["train"]
    for t, y in zip(tr["traj"], tr["y"]):
        c = s.add_node("Concept", {"name": f"c{int(y)}", gm.WORD_ATTR: 1.0})
        s.set_attr(c, gm.SYNTH_ATTR, t.tolist())
        cls_of[c] = int(y)
    pterm = predict_pointset_term()
    eterm = pointset_error_term()

    def one(traj):
        m = s.add_node("Mark", {gm.MARK_ATTR: traj.tolist()})
        w = s.evaluate(_Pred(pterm), {"s": m})
        if w is None:
            return float("inf"), -1
        resid = s.evaluate(_Pred(eterm), {"s": m, "w": w})
        pred = cls_of.get(int(w) if hasattr(w, "__int__") else w, -1)
        # robust class read from the winner node name
        nm = s.node(w)["attrs"].get("name")
        if isinstance(nm, str) and nm.startswith("c"):
            pred = int(nm[1:])
        return float(resid), pred

    out = {}
    for name, drs in (("val", data["val"]), ("test", data["test"])):
        rs = []; ps = []
        for t in drs["traj"]:
            r, p = one(t); rs.append(r); ps.append(p)
        out[name] = dict(resid=np.array(rs), pred=np.array(ps))
    ood = {}
    for k, dd in data["ood"].items():
        rs = [one(t)[0] for t in dd["traj"]]
        ood[k] = np.array(rs)
    out["ood"] = ood
    return out


# ---------------------------------------------------------------------------
# NET ARMS  (measured baseline; MLP on the SAME trajectory + CNN on raster)
# ---------------------------------------------------------------------------
class MLP(nn.Module):
    def __init__(self, d_in, k):
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(d_in, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 256), nn.ReLU(), nn.Dropout(0.3))
        self.head = nn.Linear(256, k)

    def features(self, x):
        return self.body(x)

    def forward(self, x):
        return self.head(self.body(x))


class CNN(nn.Module):
    def __init__(self, k):
        super().__init__()
        self.c = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2))
        self.body = nn.Sequential(nn.Flatten(), nn.Dropout(0.3),
                                  nn.Linear(32 * 7 * 7, 128), nn.ReLU())
        self.head = nn.Linear(128, k)

    def features(self, x):
        return self.body(self.c(x))

    def forward(self, x):
        return self.head(self.features(x))


def _train(model, Xtr, Ytr, seed, epochs=120, lr=1e-3):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    lossf = nn.CrossEntropyLoss()
    Xtr = torch.tensor(Xtr); Ytr = torch.tensor(Ytr)
    n = len(Xtr)
    g = torch.Generator().manual_seed(seed)
    model.train()
    t0 = time.time()
    for _ in range(epochs):
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, 64):
            b = perm[i:i + 64]
            opt.zero_grad()
            out = model(Xtr[b])
            loss = lossf(out, Ytr[b])
            loss.backward(); opt.step()
    return time.time() - t0


def _logits(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(X)).numpy()


def _features(model, X):
    model.eval()
    with torch.no_grad():
        return model.features(torch.tensor(X)).numpy()


def net_signals(data, seed, kind):
    """Train a net (kind='mlp' on trajectory, 'cnn' on raster) and return the net's
    refusal signals: MSP-refuse (1-maxsoftmax), energy (-logsumexp), AND the net's
    STRONGEST honest post-hoc detectors on penultimate features -- Mahalanobis
    (Lee 2018) and kNN-distance (Sun 2022), both fit on TRAIN (in-dist) ONLY. These
    give the net a distance-based refusal comparable to the substrate's mechanism,
    so the comparison is not a strawman."""
    if kind == "mlp":
        def feat(a):
            return a.reshape(len(a), -1).astype(np.float32)
        Xtr = feat(data["train"]["traj"]); model = MLP(2 * N, K)
    else:
        def feat(a):
            return a.reshape(len(a), 1, IMG, IMG).astype(np.float32)
        Xtr = feat(data["train"]["img"]); model = CNN(K)
    train_s = _train(model, Xtr, data["train"]["y"], seed)

    # ---- fit the feature-space detectors on TRAIN features (in-dist only) ----
    ytr = data["train"]["y"]
    Ftr = _features(model, Xtr)
    mus = np.stack([Ftr[ytr == c].mean(0) for c in range(K)])           # class means
    cov = np.cov((Ftr - mus[ytr]).T) + 1e-6 * np.eye(Ftr.shape[1])       # shared cov
    prec = np.linalg.pinv(cov)
    Ftr_n = Ftr / (np.linalg.norm(Ftr, axis=1, keepdims=True) + 1e-9)     # for kNN

    def maha(F):
        d = F[:, None, :] - mus[None, :, :]                              # (n,K,D)
        m = np.einsum("nkd,de,nke->nk", d, prec, d)                      # sq dist per class
        return m.min(1)                                                  # min over classes

    def knn(F, kk=5):
        Fn = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)
        dist = np.sqrt(np.maximum(0.0,
                       (Fn ** 2).sum(1)[:, None] + (Ftr_n ** 2).sum(1)[None, :]
                       - 2 * Fn @ Ftr_n.T))
        part = np.partition(dist, kk, axis=1)[:, :kk + 1]
        return part[:, kk]                                              # kth-NN distance

    def sig(a):
        X = feat(a)
        lg = _logits(model, X)
        sm = torch.softmax(torch.tensor(lg), 1).numpy()
        msp = sm.max(1)
        energy = -np.log(np.exp(lg).sum(1) + 1e-12)  # -logsumexp; higher = OOD
        pred = lg.argmax(1)
        F = _features(model, X)
        return dict(msp_refuse=1.0 - msp, energy=energy, pred=pred,
                    maha=maha(F), knn=knn(F))

    out = {"train_secs": train_s}
    for nm, src in (("val", "val"), ("test", "test")):
        arr = data[src]["traj"] if kind == "mlp" else data[src]["img"]
        out[nm] = sig(arr)
    ood = {}
    for k, dd in data["ood"].items():
        arr = dd["traj"] if kind == "mlp" else dd["img"]
        ood[k] = sig(arr)
    out["ood"] = ood
    return out


# ---------------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------------
def _ood_concat(sig_ood):
    return np.concatenate([sig_ood[k] for k in ("novel", "noise", "ambiguous")])


def auroc_ci(in_scores, ood_scores, seed):
    """AUROC of a refusal signal (higher = refuse) for is-OOD, with a bootstrap CI."""
    y = np.concatenate([np.zeros(len(in_scores)), np.ones(len(ood_scores))])
    s = np.concatenate([in_scores, ood_scores])
    finite = np.isfinite(s)
    y = y[finite]; s = s[finite]
    au = roc_auc_score(y, s)
    ap = average_precision_score(y, s)
    rng = np.random.default_rng(seed)
    n = len(s); boots = []
    for _ in range(BOOT):
        idx = rng.integers(0, n, n)
        if len(np.unique(y[idx])) < 2:
            continue
        boots.append(roc_auc_score(y[idx], s[idx]))
    lo, hi = np.percentile(boots, [2.5, 97.5]) if boots else (au, au)
    return dict(auroc=float(au), aupr=float(ap), ci=[float(lo), float(hi)])


def matched_threshold(val_scores, alpha):
    """tau = the (1-alpha) quantile of the in-dist VAL signal -> refuses alpha of
    in-dist. Chosen on in-dist data ONLY."""
    v = val_scores[np.isfinite(val_scores)]
    return float(np.quantile(v, 1.0 - alpha))


def cost_surface(arm, C_ratio, refuses_test, wrong_test, refuses_ood):
    """Expected cost over rho for one (arm, C_wrong/C_refuse). C_refuse=1, C_wrong=r.
    in-dist: refuse->1 ; answer & wrong->r ; answer & right->0.
    OOD:     refuse->1 ; answer->r (always wrong)."""
    r = C_ratio
    cost_in = np.mean(np.where(refuses_test, 1.0, np.where(wrong_test, r, 0.0)))
    cost_ood = np.mean(np.where(refuses_ood, 1.0, r))
    return {rho: float((1 - rho) * cost_in + rho * cost_ood) for rho in RHO_GRID}


# ---------------------------------------------------------------------------
# ONE SPLIT
# ---------------------------------------------------------------------------
def run_split(split_seed, net_seeds, verbose=True):
    if verbose:
        print(f"  [split {split_seed}] building data ...", flush=True)
    data = build_data(split_seed)
    n_ood = sum(len(data["ood"][k]["traj"]) for k in data["ood"])
    if verbose:
        print(f"    K={K} classes, test={len(data['test']['y'])}, "
              f"val={len(data['val']['y'])}, OOD={n_ood}", flush=True)

    sub = substrate_residuals(data)
    sub_test = sub["test"]["resid"]
    sub_val = sub["val"]["resid"]
    sub_ood = sub["ood"]
    sub_pred = sub["test"]["pred"]
    sub_acc = float(np.mean(sub_pred == data["test"]["y"]))

    res = {"split_seed": split_seed, "classes": data["classes"],
           "n_test": int(len(data["test"]["y"])), "n_val": int(len(data["val"]["y"])),
           "n_ood": {k: int(len(sub_ood[k])) for k in sub_ood},
           "indist_acc": {"substrate_residual": sub_acc},
           "arms": {}, "net_train_secs": {}}

    # ---- substrate AUROC (deterministic; net-seed-independent) ----
    sub_ood_all = _ood_concat(sub_ood)
    res["arms"]["substrate_residual"] = {
        "auroc_overall": auroc_ci(sub_test, sub_ood_all, BOOT_SEED),
        "auroc_by_kind": {k: auroc_ci(sub_test, sub_ood[k], BOOT_SEED + 1 + i)
                          for i, k in enumerate(sub_ood)},
        "signal": "residual",
    }

    # ---- nets: over seeds, both representations ----
    NET_ARMS = (("msp", "msp_refuse"), ("energy", "energy"),
                ("maha", "maha"), ("knn", "knn"))
    for kind in ("mlp", "cnn"):
        for arm_base in [a for a, _ in NET_ARMS] + ["answer"]:
            res["arms"][f"net_{arm_base}_{kind}"] = {"per_seed": [], "signal": arm_base}
        accs = []
        for seed in net_seeds:
            ns = net_signals(data, seed, kind)
            res["net_train_secs"][f"{kind}_{seed}"] = round(ns["train_secs"], 2)
            acc = float(np.mean(ns["test"]["pred"] == data["test"]["y"]))
            accs.append(acc)
            for arm_base, sigkey in NET_ARMS:
                in_test = ns["test"][sigkey]
                in_val = ns["val"][sigkey]
                ood_all = _ood_concat({k: ns["ood"][k][sigkey] for k in ns["ood"]})
                entry = {
                    "seed": seed,
                    "auroc_overall": auroc_ci(in_test, ood_all, BOOT_SEED + seed),
                    "auroc_by_kind": {k: auroc_ci(in_test, ns["ood"][k][sigkey],
                                                  BOOT_SEED + seed + 10 * (i + 1))
                                      for i, k in enumerate(ns["ood"])},
                }
                res["arms"][f"net_{arm_base}_{kind}"]["per_seed"].append(entry)
            # stash raw for cost surface (msp arm carries pred/logits)
            res["arms"][f"net_answer_{kind}"]["per_seed"].append({"seed": seed, "acc": acc})
        res["indist_acc"][f"net_{kind}"] = {
            "mean": float(np.mean(accs)), "std": float(np.std(accs)), "per_seed": accs}

    # ---- matched-FPR operating points + cost surfaces + confident-wrong ----
    # Use the FIRST net seed for the cost surface's per-input decisions (report
    # net-seed variance of AUROC separately); recompute its signals once.
    cost = {}; confab = {}
    for kind in ("mlp", "cnn"):
        ns = net_signals(data, net_seeds[0], kind)
        net_wrong_test = ns["test"]["pred"] != data["test"]["y"]
        net_ood_all_msp = _ood_concat({k: ns["ood"][k]["msp_refuse"] for k in ns["ood"]})
        net_ood_all_en = _ood_concat({k: ns["ood"][k]["energy"] for k in ns["ood"]})
        for alpha in ALPHAS:
            tag = f"{kind}_a{alpha}"
            # substrate (deterministic, kind-independent but recorded per alpha)
            tau_s = matched_threshold(sub_val, alpha)
            ref_test_s = sub_test >= tau_s
            ref_ood_s = sub_ood_all >= tau_s
            sub_wrong_test = sub_pred != data["test"]["y"]
            # net msp
            tau_m = matched_threshold(ns["val"]["msp_refuse"], alpha)
            ref_test_m = ns["test"]["msp_refuse"] >= tau_m
            ref_ood_m = net_ood_all_msp >= tau_m
            # net energy / maha / knn (feature-space distance detectors)
            arms_dec = {
                "substrate_residual": (ref_test_s, sub_wrong_test, ref_ood_s),
                f"net_msp_{kind}": (ref_test_m, net_wrong_test, ref_ood_m),
                f"net_answer_{kind}": (np.zeros(len(sub_test), bool), net_wrong_test,
                                       np.zeros(len(sub_ood_all), bool)),
            }
            for ab, sk in (("energy", "energy"), ("maha", "maha"), ("knn", "knn")):
                tau = matched_threshold(ns["val"][sk], alpha)
                ood_all = _ood_concat({k: ns["ood"][k][sk] for k in ns["ood"]})
                arms_dec[f"net_{ab}_{kind}"] = (
                    ns["test"][sk] >= tau, net_wrong_test, ood_all >= tau)
            surf = {}
            for arm, (rt, wt, ro) in arms_dec.items():
                surf[arm] = {str(r): cost_surface(arm, r, rt, wt, ro)
                             for r in COST_RATIOS}
                surf[arm]["_indist_refuse_rate"] = float(np.mean(rt))
                surf[arm]["_ood_refuse_rate"] = float(np.mean(ro))
            cost[tag] = surf
            # confident-wrong on OOD for net_answer at this alpha (matched op-pts).
            # "misses" = OOD inputs whose signal falls below the arm's matched
            # threshold, so the arm ANSWERS them (a confident wrong answer).
            tau_e = matched_threshold(ns["val"]["energy"], alpha)
            tau_ma = matched_threshold(ns["val"]["maha"], alpha)
            tau_kn = matched_threshold(ns["val"]["knn"], alpha)
            net_ood_all_ma = _ood_concat({k: ns["ood"][k]["maha"] for k in ns["ood"]})
            net_ood_all_kn = _ood_concat({k: ns["ood"][k]["knn"] for k in ns["ood"]})
            confab[tag] = {
                "net_answer_confident_wrong_frac_OOD_at_msp_oppt": float(np.mean(net_ood_all_msp < tau_m)),
                "net_energy_misses_OOD_frac": float(np.mean(net_ood_all_en < tau_e)),
                "net_maha_misses_OOD_frac": float(np.mean(net_ood_all_ma < tau_ma)),
                "net_knn_misses_OOD_frac": float(np.mean(net_ood_all_kn < tau_kn)),
                "substrate_misses_OOD_frac": float(np.mean(sub_ood_all < tau_s)),
                "ood_median_msp": float(np.median(1.0 - net_ood_all_msp)),
                "ood_frac_msp_gt_0.9": float(np.mean((1.0 - net_ood_all_msp) > 0.9)),
            }
    res["cost_surface"] = cost
    res["confabulation"] = confab

    # ---- crossover summary at primary alpha=0.10, kind=mlp ----
    res["crossover"] = crossover_summary(cost, "mlp", 0.10)
    res["crossover_cnn"] = crossover_summary(cost, "cnn", 0.10)
    return res


def crossover_summary(cost, kind, alpha):
    """For each (C_ratio, rho): which arm has minimum expected cost; and the region
    where substrate_residual beats the BEST net arm."""
    tag = f"{kind}_a{alpha}"
    surf = cost[tag]
    arms = [a for a in surf if a.endswith(kind) or a == "substrate_residual"]
    net_arms = [a for a in arms if a.startswith("net_")]
    out = {"winner_grid": {}, "substrate_beats_best_net": {}}
    for r in COST_RATIOS:
        rs = str(r)
        wg = {}; sbn = {}
        for rho in RHO_GRID:
            costs = {a: surf[a][rs][rho] for a in arms}
            win = min(costs, key=costs.get)
            wg[rho] = win
            best_net = min(surf[a][rs][rho] for a in net_arms)
            sbn[rho] = bool(surf["substrate_residual"][rs][rho] < best_net - 1e-9)
        out["winner_grid"][rs] = wg
        out["substrate_beats_best_net"][rs] = sbn
    return out


def main():
    t0 = time.time()
    print("=" * 92)
    print("IS THE REPRESENTABLE REFUSAL WORTH ANYTHING? — OOD selective prediction")
    print(PROV)
    print(f"loadavg at start: {os.getloadavg()}  torch_threads={torch.get_num_threads()}")
    print("=" * 92)

    result = {
        "provenance": PROV,
        "loadavg_start": os.getloadavg(),
        "torch_threads": torch.get_num_threads(),
        "params": dict(N=N, K=K, N_KNOWN_ALPH=N_KNOWN_ALPH, TRAIN_DR=TRAIN_DR,
                       VAL_DR=VAL_DR, TEST_DR=TEST_DR, N_OOD_EACH=N_OOD_EACH,
                       IMG=IMG, ALPHAS=ALPHAS, COST_RATIOS=COST_RATIOS,
                       BOOT=BOOT, BOOT_SEED=BOOT_SEED),
        "splits": [],
    }
    # main split with 5 net seeds
    result["splits"].append(run_split(129000, [129001, 129002, 129003, 129004, 129005]))
    # robustness splits with 2 net seeds each
    for ss in (129020, 129021, 129022):
        result["splits"].append(run_split(ss, [129001, 129002]))

    result["loadavg_end"] = os.getloadavg()
    result["elapsed_secs"] = round(time.time() - t0, 1)
    # re-verify engine after measurement
    result["provenance_after"] = engine_provenance.provenance_line()

    outp = ROOT / "results" / "refusal_usefulness.json"
    outp.parent.mkdir(exist_ok=True)
    outp.write_text(json.dumps(result, indent=2))
    print(f"\n  wrote {outp}")
    print(f"  elapsed {result['elapsed_secs']}s  loadavg_end {result['loadavg_end']}")
    print(f"  provenance_after: {result['provenance_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
