"""RICHER FEATURES — push Gemma's warm-start one-shot past 91 toward the human bar.

Cheap statistical adaptations capped at ~91 (centering +2; WCCN/PCA hurt). The remaining lever is the FEATURE
itself: mean-pooling 64 vision tokens drowns the few discriminative STROKE patches in mostly-blank background.
This re-embeds with richer pooling -- mean, MAX (focuses on the stroke patches), and mean+max concat -- and
tests each (centered) one-shot, then a REGULARISED residual head (identity-init, so it can only gently refine,
never destroy the borrowed features -- the lesson from the overfit learned head).

Resumable 2-phase within the harness ~600s cap (PHASE1 caches [mean|max] per image; PHASE2 fast eval/train).
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_gemma_richer.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
from domains import omniglot_world as ow

SEP = "=" * 100
HF = "/home/matt/.cache/huggingface/hub/models--google--gemma-4-E4B-it/snapshots/fee6332c1abaafb77f6f9624236c63aa2f1d0187"
VLLM = "/var/lib/vllm-models/gemma4-text"
CACHE = "/tmp/gemma_rich.npz"
CANVAS = 180
N_BG, BG_DRAW, N_EV, EV_DRAW = 150, 5, 200, 2
TIME_BUDGET = 500.0
GEOMETRIC, HUMAN = 81.0, 95.0


def build_items():
    bg, ev = [], []
    for al in ow.alphabets("background"):
        for ch in ow.characters(al, "background"):
            if len(ow.drawings(ch)) >= BG_DRAW:
                bg.append(ow.drawings(ch))
    for al in ow.alphabets("evaluation"):
        for ch in ow.characters(al, "evaluation"):
            if len(ow.drawings(ch)) >= EV_DRAW:
                ev.append(ow.drawings(ch))
    rb = np.random.default_rng(1); re = np.random.default_rng(0)
    bg = [bg[i] for i in rb.permutation(len(bg))[:N_BG]]
    ev = [ev[i] for i in re.permutation(len(ev))[:N_EV]]
    items = []
    for ci, dr in enumerate(bg):
        for jj, j in enumerate(rb.permutation(len(dr))[:BG_DRAW]):
            items.append((f"bg_{ci}_{jj}", dr[j]))
    for ci, dr in enumerate(ev):
        for jj, j in enumerate(re.permutation(len(dr))[:EV_DRAW]):
            items.append((f"ev_{ci}_{jj}", dr[j]))
    return items


def render(path):
    from PIL import Image
    strokes = ow.load_strokes(path)
    allpts = np.concatenate([s for s in strokes if len(s)], 0) if strokes else np.zeros((0, 2))
    a = np.full((CANVAS, CANVAS, 3), 255, np.uint8)
    if len(allpts) == 0:
        return Image.fromarray(a)
    mn, mx = allpts.min(0), allpts.max(0); span = np.maximum(mx - mn, 1e-6)
    for s in strokes:
        if len(s) == 0:
            continue
        q = (s - mn) / span * (CANVAS - 24) + 12
        for i in range(len(q) - 1):
            for t in np.linspace(0, 1, 40):
                x, y = (q[i] * (1 - t) + q[i + 1] * t).astype(int)
                a[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4] = 0
    return Image.fromarray(a)


def load_cache():
    if not os.path.exists(CACHE):
        return {}
    d = np.load(CACHE, allow_pickle=True)
    return {k: v for k, v in zip(d["keys"], d["feats"])}


def save_cache(feat):
    keys = list(feat)
    np.savez(CACHE + ".tmp.npz", keys=np.array(keys), feats=np.stack([feat[k] for k in keys]))
    os.replace(CACHE + ".tmp.npz", CACHE)


def phase1(items):
    import torch
    from safetensors import safe_open
    from transformers import Gemma4VisionModel, Gemma4VisionConfig, Gemma4ImageProcessorPil
    feat = load_cache()
    todo = [(k, p) for k, p in items if k not in feat]
    if not todo:
        print(f"  cache complete: {len(feat)}"); return feat, True
    print(f"  PHASE 1: embedding {len(todo)}/{len(items)} (mean|max pooling)...", flush=True)
    vc = Gemma4VisionConfig(**json.load(open(HF + "/config.json"))["vision_config"])
    model = Gemma4VisionModel(vc)
    sd = {}
    for s in sorted(glob.glob(VLLM + "/*.safetensors")):
        with safe_open(s, framework="pt") as f:
            for k in f.keys():
                if k.startswith("model.vision_tower."):
                    sd[k[len("model.vision_tower."):]] = f.get_tensor(k).float()
    model.load_state_dict(sd, strict=False); model.eval(); torch.set_num_threads(8)
    ip = Gemma4ImageProcessorPil(max_soft_tokens=70)
    t0 = time.time()
    for i in range(0, len(todo), 16):
        chunk = todo[i:i + 16]
        procs = [ip(images=render(p), return_tensors="pt") for _, p in chunk]
        pv = torch.cat([p["pixel_values"] for p in procs], 0)
        pid = torch.cat([p["image_position_ids"] for p in procs], 0)
        with torch.no_grad():
            out = model(pixel_values=pv, pixel_position_ids=pid)
        lh = out.last_hidden_state if hasattr(out, "last_hidden_state") else out[0]
        B = len(chunk); lh = lh.reshape(B, lh.shape[0] // B, lh.shape[-1])
        mean = lh.mean(1).cpu().numpy(); mx = lh.max(1).values.cpu().numpy()
        for (k, _), m, x in zip(chunk, mean, mx):
            feat[k] = np.concatenate([m, x]).astype(np.float32)       # [mean(768) | max(768)]
        if (i // 16) % 4 == 0:
            save_cache(feat)
        print(f"    {len(feat)}/{len(items)}", end="\r", flush=True)
        if time.time() - t0 > TIME_BUDGET:
            save_cache(feat); print(f"\n  budget hit; {len(feat)}/{len(items)}. RE-RUN."); return feat, False
    save_cache(feat); print(f"\n  cache complete: {len(feat)}"); return feat, True


def osh(S, Q, n_ev, seed=123, n=3000):
    S = S / (np.linalg.norm(S, axis=1, keepdims=True) + 1e-9)
    Q = Q / (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
    rng = np.random.default_rng(seed); cor = 0
    for _ in range(n):
        cl = rng.choice(n_ev, 20, replace=False); qi = int(rng.integers(20))
        cor += int((S[cl] @ Q[cl[qi]]).argmax() == qi)
    return 100 * cor / n


def relu(x): return np.maximum(x, 0)


def residual_head(bgX, rng, epochs=1500, lr=0.02, H=512, alpha=0.3):
    """z = x + alpha*W2 relu(W1 x); identity-init (W2=0) so it starts as the raw feature and only refines."""
    din = bgX.shape[2]
    W1 = rng.normal(0, np.sqrt(2 / din), (din, H)); b1 = np.zeros(H)
    W2 = np.zeros((H, din)); b2 = np.zeros(din)
    mom = [np.zeros_like(p) for p in (W1, b1, W2, b2)]
    NW, NS, NQ = 20, 3, 2
    for ep in range(epochs):
        cls = rng.choice(bgX.shape[0], NW, replace=False)
        Xs, Xq, ql = [], [], []
        for ci, c in enumerate(cls):
            idx = rng.choice(bgX.shape[1], NS + NQ, replace=False)
            Xs.append(bgX[c, idx[:NS]]); Xq.append(bgX[c, idx[NS:]]); ql += [ci] * NQ
        Xs = np.concatenate(Xs, 0); Xq = np.concatenate(Xq, 0); ql = np.array(ql)

        def fwd(X):
            z1 = X @ W1 + b1; h = relu(z1); z = X + alpha * (h @ W2 + b2)
            return z1, h, z
        z1s, hs, zs = fwd(Xs); z1q, hq, zq = fwd(Xq)
        proto = zs.reshape(NW, NS, -1).mean(1)
        d2 = ((zq[:, None, :] - proto[None, :, :]) ** 2).sum(-1)
        lo = -d2; lo -= lo.max(1, keepdims=True); pr = np.exp(lo); pr /= pr.sum(1, keepdims=True)
        dl = pr.copy(); dl[np.arange(len(ql)), ql] -= 1; dl /= len(ql)
        diff = zq[:, None, :] - proto[None, :, :]
        dzq = (2 * diff * (-dl)[:, :, None]).sum(1)
        dproto = -(2 * diff * (-dl)[:, :, None]).sum(0)
        dzs = np.zeros_like(zs)
        for ci in range(NW):
            dzs[ci * NS:(ci + 1) * NS] += dproto[ci] / NS

        def bwd(X, z1, h, dz):
            dres = alpha * dz
            gW2 = h.T @ dres; gb2 = dres.sum(0)
            dh = dres @ W2.T; dz1 = dh * (z1 > 0)
            gW1 = X.T @ dz1; gb1 = dz1.sum(0)
            return gW1, gb1, gW2, gb2
        g = [a + b for a, b in zip(bwd(Xq, z1q, hq, dzq), bwd(Xs, z1s, hs, dzs))]
        gn = np.sqrt(sum(float((x ** 2).sum()) for x in g)); sc = min(1.0, 5.0 / (gn + 1e-8))
        lrt = lr * (0.5 ** (ep // 700))
        for k, (p, gg) in enumerate(zip((W1, b1, W2, b2), g)):
            mom[k] = 0.9 * mom[k] - lrt * sc * gg; p += mom[k]
    return (W1, b1, W2, b2, alpha)


def apply_head(X, head):
    W1, b1, W2, b2, alpha = head
    return X + alpha * (relu(X @ W1 + b1) @ W2 + b2)


def main():
    print(SEP)
    print("RICHER FEATURES — Gemma warm-start: pooling variants + regularised residual head (push 91 -> the bar).")
    print(SEP)
    items = build_items()
    feat, done = phase1(items)
    if not done:
        return 0
    M = {k: feat[k] for k in feat}
    sup_mm = np.stack([M[f"ev_{c}_0"] for c in range(N_EV)])
    qry_mm = np.stack([M[f"ev_{c}_1"] for c in range(N_EV)])
    bg_mm = np.stack([np.stack([M[f"bg_{c}_{j}"] for j in range(BG_DRAW)]) for c in range(N_BG)])

    def variant(name, sl):
        s, q = sup_mm[:, sl], qry_mm[:, sl]
        mu = bg_mm[:, :, sl].reshape(-1, q.shape[1]).mean(0)
        return name, osh(s, q, N_EV), osh(s - mu, q - mu, N_EV)
    print("\n  pooling variant (raw / centered):")
    for nm, r, c in [variant("mean      ", slice(0, 768)),
                     variant("max       ", slice(768, 1536)),
                     variant("mean+max  ", slice(0, 1536))]:
        print(f"    {nm}: {r:5.1f} / {c:5.1f}")

    # best base = mean+max centered; train a regularised residual head on it
    sl = slice(0, 1536)
    mu = bg_mm[:, :, sl].reshape(-1, 1536).mean(0)
    bgX = (bg_mm[:, :, sl] - mu)
    base = osh(sup_mm[:, sl] - mu, qry_mm[:, sl] - mu, N_EV)
    head = residual_head(bgX, np.random.default_rng(7))
    s2 = apply_head(sup_mm[:, sl] - mu, head); q2 = apply_head(qry_mm[:, sl] - mu, head)
    headed = osh(s2, q2, N_EV)
    best = max(base, headed)
    print("\n" + SEP)
    print(f"  20-way 1-shot ({N_EV}-char pool), best feature path:")
    print(f"    mean+max, centered            : {base:5.1f}%")
    print(f"    + regularised residual head    : {headed:5.1f}%   ({headed-base:+.1f})")
    print(f"    geometric ~{GEOMETRIC:.0f}   human bar ~{HUMAN:.0f}")
    verdict = ("CLEARS the human bar" if best >= HUMAN else
               "beats geometric, below human" if best > GEOMETRIC else "below geometric")
    print(f"\n  VERDICT: {verdict} ({best:.1f}%).")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
