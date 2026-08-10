"""BACK TO HANDWRITING — feasibility measurement: does a GRADIENT-TRAINED metric embedding clear the human
one-shot bar on real Omniglot, the climb the two rules demand?

The two-rules re-decision picked a small learned metric net (~95%, efficient) over the ~81% geometric ceiling
(disqualified: 81 < human 95). The agent now holds the trainer (graph-native delta-rule LMS + multi-layer
backprop, proven). Before committing to the graph-native/Rust scale-up of that trainer to Omniglot, this
MEASURES the path in numpy -- exactly as the XOR hyperparameters were locked in numpy before the graph build.
The gradient-descent ALGORITHM here is the agent's (validated graph-native); numpy is the scaled execution to
decide if the learned-metric path actually clears the bar and warrants the build.

A prototypical metric net (Snell et al.): a small conv embedding trained episodically on the BACKGROUND
alphabets so same-character images cluster; one-shot = nearest class-prototype in the embedding, tested on the
held-out EVALUATION alphabets (never-seen characters). 20-way 1-shot, the standard protocol.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_handwriting_feasibility.py [train_episodes]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
from domains import omniglot_world as ow

SEP = "=" * 100
GRID = 28
GEOMETRIC_CEILING = 81.0
HUMAN = 95.0


def raster(path) -> np.ndarray:
    """Render a character's strokes to a GRID x GRID image by drawing CONNECTED lines between consecutive
    stroke points (proper character rendering, not a dot-cloud). Mechanical I/O: external form -> array."""
    strokes = ow.load_strokes(path)
    allpts = np.concatenate([s for s in strokes if len(s)], 0) if strokes else np.zeros((0, 2))
    if len(allpts) == 0:
        return np.zeros((GRID, GRID), np.float64)
    mn, mx = allpts.min(0), allpts.max(0)
    span = np.maximum(mx - mn, 1e-6)
    img = np.zeros((GRID, GRID), np.float64)

    def put(x, y):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < GRID and 0 <= yi < GRID:
            img[yi, xi] = 1.0

    for s in strokes:
        if len(s) == 0:
            continue
        q = (s - mn) / span * (GRID - 3) + 1          # to pixel coords, 1px margin
        for a in range(len(q)):
            put(q[a, 0], q[a, 1])
            if a + 1 < len(q):                        # draw the segment to the next point
                steps = int(max(abs(q[a + 1, 0] - q[a, 0]), abs(q[a + 1, 1] - q[a, 1])) * 2) + 1
                for t in np.linspace(0, 1, steps):
                    put(q[a, 0] + t * (q[a + 1, 0] - q[a, 0]), q[a, 1] + t * (q[a + 1, 1] - q[a, 1]))
    return img


# ---- a tiny conv embedding (4 conv blocks -> 64-d), the standard Omniglot protonet backbone, in numpy ----
def he(shape, rng):
    fan = np.prod(shape[1:])
    return rng.normal(0, np.sqrt(2.0 / fan), shape)


def conv2d(x, w, b):                                 # x:(N,Ci,H,W) w:(Co,Ci,3,3) valid, stride1, pad1
    N, Ci, H, W = x.shape
    Co = w.shape[0]
    xp = np.zeros((N, Ci, H + 2, W + 2)); xp[:, :, 1:-1, 1:-1] = x
    cols = np.stack([xp[:, :, i:i + H, j:j + W] for i in range(3) for j in range(3)], 1)  # (N,9,Ci,H,W)
    cols = cols.reshape(N, 9 * Ci, H * W)
    wm = w.reshape(Co, Ci, 9).transpose(0, 2, 1).reshape(Co, 9 * Ci)
    out = (wm @ cols).reshape(N, Co, H, W) + b[None, :, None, None]
    return out, cols


BN_EPS = 1e-5


def forward(params, x):
    """conv -> BATCHNORM (transductive: batch stats) -> relu -> 2x2 maxpool, x4 blocks -> 64-d embedding."""
    cache = []
    h = x
    for li in range(4):
        w = params[f"w{li}"]
        z, _ = conv2d(h, w, np.zeros(w.shape[0]))     # no conv bias; BN beta handles offset
        mu = z.mean(axis=(0, 2, 3), keepdims=True)
        ve = z.var(axis=(0, 2, 3), keepdims=True) + BN_EPS
        zhat = (z - mu) / np.sqrt(ve)
        y = params[f"g{li}"][None, :, None, None] * zhat + params[f"be{li}"][None, :, None, None]
        a = np.maximum(y, 0)
        N, C, H, W = a.shape
        He, We = H // 2 * 2, W // 2 * 2                # crop to even before 2x2 maxpool (handles odd dims)
        p = a[:, :, :He, :We].reshape(N, C, He // 2, 2, We // 2, 2).max(axis=(3, 5))
        cache.append((h, a, zhat, ve, p.shape))
        h = p
    emb = h.reshape(h.shape[0], -1)
    return emb, cache


def main():
    train_eps = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    print(SEP)
    print("BACK TO HANDWRITING — feasibility: gradient-trained metric embedding vs the geometric ceiling on Omniglot.")
    print(SEP)
    if not (ow.have_data("background") and ow.have_data("evaluation")):
        print("\n  data missing."); return 1

    rng = np.random.default_rng(0)

    # index characters per split (one drawing list per character).
    def index(split):
        out = []
        for al in ow.alphabets(split):
            for ch in ow.characters(al, split):
                dr = ow.drawings(ch)
                if len(dr) >= 5:
                    out.append(dr)
        return out
    bg = index("background")
    ev = index("evaluation")
    print(f"\n  background characters: {len(bg)}   evaluation characters: {len(ev)}   (grid {GRID}x{GRID})")

    cache_img: dict = {}

    def img_of(path, k=0):
        key = (path, k)
        if key not in cache_img:
            im = raster(path)
            cache_img[key] = np.rot90(im, k).copy() if k else im
        return cache_img[key]

    params = {}
    ch_in = 1
    for li in range(4):
        params[f"w{li}"] = he((32, ch_in, 3, 3), rng)        # 32 filters (batchnorm makes the bigger net trainable)
        params[f"g{li}"] = np.ones(32); params[f"be{li}"] = np.zeros(32); ch_in = 32
    lr = 2e-3
    CLIP = 5.0
    mom = {k: np.zeros_like(v) for k, v in params.items()}

    # checkpoint resume (the harness caps a run at ~600s; chain rounds to reach the plateau).
    CKPT = "/tmp/hwfeas_ckpt.npz"
    start_ep = 0
    if os.path.exists(CKPT):
        d = np.load(CKPT)
        for k in params:
            params[k] = d[k]; mom[k] = d["m_" + k]
        start_ep = int(d["ep"])
        print(f"  resumed from checkpoint at episode {start_ep}")
    ep_rng = np.random.default_rng(100003 + start_ep)            # fresh episodes each resume

    def embed(items):                                # items: list of (path, rotation_k)
        x = np.stack([img_of(p, k) for (p, k) in items])[:, None, :, :]
        emb, cache = forward(params, x)
        return emb, cache, x

    # rotation augmentation: each (character, 90deg-rotation) is a DISTINCT training class (the standard
    # Omniglot trick -- 4x classes, the key to one-shot transfer).
    aug = [(c, k) for c in range(len(bg)) for k in range(4)]

    # episodic prototypical training on BACKGROUND with full analytic backprop through the conv net.
    print(f"  training prototypical metric (20-way, 5-shot support) for {train_eps} episodes...", flush=True)

    # ---- full backprop helpers (relu + maxpool + conv) ----
    def backward(params, cache, demb):
        grads = {k: np.zeros_like(v) for k, v in params.items()}
        dh = demb.reshape(cache[-1][4])
        for li in reversed(range(4)):
            h, a, zhat, ve, pshape = cache[li]
            N, C, H, W = a.shape
            He, We = H // 2 * 2, W // 2 * 2
            # maxpool backward (over the even-cropped region; border that was cropped gets zero grad)
            ar = a[:, :, :He, :We].reshape(N, C, He // 2, 2, We // 2, 2)
            mx = ar.max(axis=(3, 5), keepdims=True)
            mask = (ar == mx)
            dac = (mask * dh[:, :, :, None, :, None]).reshape(N, C, He, We)
            da = np.zeros((N, C, H, W)); da[:, :, :He, :We] = dac
            dy = da * (a > 0)                                  # relu backward (a>0 <=> y>0)
            # batchnorm backward (per channel, over M = N*H*W)
            grads[f"g{li}"] += (dy * zhat).sum(axis=(0, 2, 3))
            grads[f"be{li}"] += dy.sum(axis=(0, 2, 3))
            dzhat = dy * params[f"g{li}"][None, :, None, None]
            M = N * H * W
            std = np.sqrt(ve)
            dz = (1.0 / M) * (1.0 / std) * (
                M * dzhat - dzhat.sum(axis=(0, 2, 3), keepdims=True)
                - zhat * (dzhat * zhat).sum(axis=(0, 2, 3), keepdims=True))
            # conv backward
            Ci = h.shape[1]
            xp = np.zeros((N, Ci, H + 2, W + 2)); xp[:, :, 1:-1, 1:-1] = h
            cols = np.stack([xp[:, :, i:i + H, j:j + W] for i in range(3) for j in range(3)], 1).reshape(N, 9 * Ci, H * W)
            dzf = dz.reshape(N, C, H * W)
            grads[f"w{li}"] += (dzf @ cols.transpose(0, 2, 1)).sum(0).reshape(C, 9, Ci).transpose(0, 2, 1).reshape(C, Ci, 3, 3)
            wm = params[f"w{li}"].reshape(C, Ci, 9).transpose(0, 2, 1).reshape(C, 9 * Ci)
            dcols = (wm.T @ dzf).reshape(N, 9, Ci, H, W)
            dxp = np.zeros((N, Ci, H + 2, W + 2))
            k = 0
            for i in range(3):
                for j in range(3):
                    dxp[:, :, i:i + H, j:j + W] += dcols[:, k]; k += 1
            dh = dxp[:, :, 1:-1, 1:-1]
        return grads

    NW, NS, NQ = 20, 5, 3
    for ep in range(start_ep, start_ep + train_eps):
        cls = ep_rng.choice(len(aug), NW, replace=False)
        sup_paths, qry_paths, qry_lab = [], [], []
        for ci, ai in enumerate(cls):
            c, k = aug[ai]
            idx = ep_rng.choice(len(bg[c]), NS + NQ, replace=False)
            sup_paths += [(bg[c][i], k) for i in idx[:NS]]
            qry_paths += [(bg[c][i], k) for i in idx[NS:]]
            qry_lab += [ci] * NQ
        all_paths = sup_paths + qry_paths
        emb, cache, x = embed(all_paths)
        S = emb[:NW * NS].reshape(NW, NS, -1).mean(1)          # prototypes (NW, D)
        Q = emb[NW * NS:]                                       # (NW*NQ, D)
        qlab = np.array(qry_lab)
        # squared euclidean to prototypes; protoloss = CE over -dist
        d2 = ((Q[:, None, :] - S[None, :, :]) ** 2).sum(-1)    # (NQ_total, NW)
        logits = -d2
        logits -= logits.max(1, keepdims=True)
        pr = np.exp(logits); pr /= pr.sum(1, keepdims=True)
        # grad of CE wrt Q and S
        dlogits = pr.copy(); dlogits[np.arange(len(qlab)), qlab] -= 1.0; dlogits /= len(qlab)
        dd2 = -dlogits                                          # logits = -d2
        # d2 = |Q-S|^2 -> dQ = 2(Q-S)*dd2 summed over protos; dS = -2 sum_q (Q-S)*dd2
        diff = Q[:, None, :] - S[None, :, :]
        dQ = (2 * diff * dd2[:, :, None]).sum(1)
        dS = -(2 * diff * dd2[:, :, None]).sum(0)
        demb = np.zeros_like(emb)
        demb[NW * NS:] = dQ
        # prototype grad flows back to its support members equally
        for ci in range(NW):
            demb[ci * NS:(ci + 1) * NS] += dS[ci] / NS
        grads = backward(params, cache, demb)
        # global-norm gradient clipping (the tail blew up without it) + lr decay for stability.
        gn = np.sqrt(sum(float((grads[k] ** 2).sum()) for k in grads))
        if not np.isfinite(gn):
            continue                                  # skip a numerically bad step rather than poison the net
        scale = min(1.0, CLIP / (gn + 1e-8))
        lrt = lr * (0.5 ** (ep // 500))
        for k in params:
            mom[k] = 0.9 * mom[k] - lrt * scale * grads[k]
            params[k] += mom[k]
        if ep % 200 == 0 or ep == start_ep + train_eps - 1:
            acc = (pr.argmax(1) == qlab).mean()
            print(f"    episode {ep:5d}  train-batch 20-way acc {acc*100:5.1f}%  (|g|={gn:.1f}, lr={lrt:.1e})", flush=True)
        if (ep + 1) % 100 == 0:                          # periodic save: progress survives a timeout kill
            np.savez(CKPT, ep=ep + 1, **params, **{"m_" + k: v for k, v in mom.items()})
    np.savez(CKPT, ep=start_ep + train_eps, **params, **{"m_" + k: v for k, v in mom.items()})
    print(f"  saved checkpoint at episode {start_ep + train_eps}")

    # ---- evaluation: 20-way 1-shot on held-out EVALUATION alphabets ----
    print(f"\n  evaluating 20-way 1-shot on {len(ev)} held-out evaluation characters...", flush=True)
    correct = total = 0
    raw_correct = 0
    for _ in range(200):
        cls = ep_rng.choice(len(ev), 20, replace=False)
        sup_paths, q_path, q_lab = [], None, None
        qi = ep_rng.integers(20)
        for ci, c in enumerate(cls):
            idx = ep_rng.choice(len(ev[c]), 2, replace=False)
            sup_paths.append(ev[c][idx[0]])
            if ci == qi:
                q_path, q_lab = ev[c][idx[1]], ci
        emb, _, _ = embed([(p, 0) for p in sup_paths] + [(q_path, 0)])     # eval: real chars, no rotation
        S, qv = emb[:20], emb[20]
        pred = int(((S - qv) ** 2).sum(1).argmin())
        correct += (pred == q_lab); total += 1
        # raw-pixel NN baseline (no learning) for reference
        raws = np.stack([img_of(p, 0).ravel() for p in sup_paths]); rq = img_of(q_path, 0).ravel()
        raw_correct += (int(((raws - rq) ** 2).sum(1).argmin()) == q_lab)
    learned = 100 * correct / total
    rawnn = 100 * raw_correct / total

    print("\n" + SEP)
    print(f"  20-way 1-shot on held-out Omniglot characters:")
    print(f"    raw-pixel 1-NN (no learning)          : {rawnn:5.1f}%")
    print(f"    geometric ceiling (arc, hand-crafted) : ~{GEOMETRIC_CEILING:.0f}%   (the two-rules-DISQUALIFIED ceiling)")
    print(f"    gradient-trained metric embedding     : {learned:5.1f}%   <-- the learned-metric path")
    print(f"    human one-shot bar (rule 2)           : ~{HUMAN:.0f}%")
    verdict = ("CLEARS the human bar" if learned >= HUMAN else
               "beats the geometric ceiling but trails the human bar" if learned > GEOMETRIC_CEILING else
               "does not beat the geometric ceiling")
    print(f"\n  FEASIBILITY VERDICT: the gradient-trained embedding {verdict} ({learned:.1f}%).")
    print(f"  The learning algorithm is the agent's (graph-native delta-rule + backprop, proven); this numpy run")
    print(f"  measures whether the path the two rules picked actually pays before the graph-native/Rust scale-up.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
