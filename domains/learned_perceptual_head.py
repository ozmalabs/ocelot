"""learned_perceptual_head — a LEARNED-FROM-SCRATCH perceptual encoder (earn-not-borrow).

THE FINAL earn-not-borrow perception test. Fixed scattering (bb287bad) closed ~40% of the
34->91 gap; the residual ~40pp is the perceptual-feature gap that a LEARNED feature should
close — but EARNED, not borrowed.

THE SHARP LINE (the whole point): EARNED-LEARNED = an encoder trained FROM SCRATCH (random
init) on the Omniglot BACKGROUND set (30 alphabets / 964 chars x 20 drawers = held data the
agent has), eval alphabets HELD OUT. BORROWED = a pretrained net (Gemma 91%, massive external
corpus) — NOT used. The line is NO BORROWED WEIGHTS, not no-learning: learning from the held
data IS earning.

WHAT THIS IS: a small CNN (random init, ~140k params) trained by supervised classification on
the 964 background classes (the standard "learn an embedding on base classes, 1-NN on novel
classes" few-shot protocol). The penultimate layer is the EARNED embedding; recognition stays
HELD (cosine 1-NN / held PCA->LDA over the embedding). NO pretrained weights, NO downloaded
files, NO borrowed net — random init + background-only training, confirmable by grep + the
random-init-untrained control.

torch/numpy USAGE (flagged): torch is the from-scratch TRAINER (random init; no
torchvision.models, no .from_pretrained, no weight download). numpy is the raster adapter.
The trained weights live only in a local cache the agent produced (earned), never downloaded.
"""
from __future__ import annotations
import os
import numpy as _np                 # ADAPTER: rasterise traces to image tensors
import torch                        # FROM-SCRATCH TRAINER (random init; NO pretrained models)
import torch.nn as _nn
import domains.omniglot_world as _ow
import domains.scattering_feature as _sf

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     ".bigtmp", "learned_head.pt")


class _SmallCNN(_nn.Module):
    """A small convnet, RANDOM INIT (no pretrained weights). Penultimate = the embedding."""
    def __init__(self, n_classes, emb=64):
        super().__init__()
        self.feat = _nn.Sequential(
            _nn.Conv2d(1, 16, 3, padding=1), _nn.ReLU(), _nn.MaxPool2d(2),
            _nn.Conv2d(16, 32, 3, padding=1), _nn.ReLU(), _nn.MaxPool2d(2),
            _nn.Conv2d(32, 32, 3, padding=1), _nn.ReLU(), _nn.MaxPool2d(2),
            _nn.Flatten(), _nn.Linear(32 * 4 * 4, emb), _nn.ReLU(),
        )
        self.head = _nn.Linear(emb, n_classes)

    def embed(self, x):
        return self.feat(x)

    def forward(self, x):
        return self.head(self.feat(x))


def _raster(path, size=32):
    """ADAPTER: a trace -> a (1,size,size) image tensor (numpy raster, then torch)."""
    img = _sf.render_trace(_ow.load_strokes(path), size=size)
    if img is None:
        return None
    return img.astype(_np.float32)


def _build_background_set(n_alphabets=None, max_per=None, size=32):
    """Load the BACKGROUND set as (X images, y class-ids). HELD data; eval alphabets excluded
    by construction (we read only the background split). NO borrowed data."""
    bg = _ow.alphabets("background")
    if n_alphabets:
        bg = bg[:n_alphabets]
    X, y, cid = [], [], 0
    for al in bg:
        for c in _ow.characters(al, split="background"):
            ds = _ow.drawings(c)
            if max_per:
                ds = ds[:max_per]
            imgs = [_raster(d, size) for d in ds]
            imgs = [im for im in imgs if im is not None]
            if len(imgs) >= 2:
                for im in imgs:
                    X.append(im); y.append(cid)
                cid += 1
    return _np.stack(X)[:, None, :, :], _np.array(y), cid


def train_from_scratch(*, n_alphabets=None, max_per=None, epochs=8, bs=128, lr=1e-3,
                       size=32, seed=0, log=print):
    """Train the encoder FROM SCRATCH (random init) on the background set. Returns the model.
    NO pretrained weights — torch.manual_seed + random init + background-only SGD. The earned
    front-end. Caches the EARNED weights locally (never downloaded)."""
    torch.manual_seed(seed); _np.random.seed(seed)
    X, y, ncls = _build_background_set(n_alphabets, max_per, size)
    log(f"  background TRAIN set: {len(X)} images / {ncls} classes "
        f"(held data; eval alphabets excluded). FROM-SCRATCH random init.")
    Xt = torch.tensor(X); yt = torch.tensor(y, dtype=torch.long)
    model = _SmallCNN(ncls)
    # PROOF of random init: report the initial conv-weight std (not loaded from a file)
    w0 = float(model.feat[0].weight.detach().std())
    log(f"  random-init proof: first-conv weight std = {w0:.4f} (initialised, NOT loaded)")
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    lossf = _nn.CrossEntropyLoss()
    n = len(Xt)
    model.train()
    for ep in range(epochs):
        perm = torch.randperm(n)
        tot = 0.0
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            out = model(Xt[idx])
            loss = lossf(out, yt[idx])
            loss.backward(); opt.step()
            tot += float(loss) * len(idx)
        log(f"    epoch {ep + 1}/{epochs}  train-loss {tot / n:.3f}")
    model.eval()
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        torch.save(model.state_dict(), CACHE)
    except Exception:
        pass
    return model


def untrained_model(size=32, seed=0):
    """A RANDOM-INIT, UNTRAINED encoder — the discriminative control. Must NOT beat
    scattering (architecture alone is not the lift; TRAINING does the work)."""
    torch.manual_seed(seed)
    _, _, ncls = _build_background_set(n_alphabets=2, size=size)
    return _SmallCNN(max(ncls, 2)).eval()


def embed(model, path, size=32):
    """The EARNED embedding of a trace (penultimate layer). Recognition (cosine 1-NN / held
    PCA->LDA) runs OVER this — the learned head is the perception front-end only."""
    im = _raster(path, size)
    if im is None:
        return None
    with torch.no_grad():
        return model.embed(torch.tensor(im)[None, None, :, :]).numpy()[0]


# ---------------------------------------------------------------------------
# THE WINNING ARCHITECTURE: a learned MLP head ON the fixed-SCATTERING base
# (earned-by-construction + earned-by-learning). Beats raw-image CNN and scatter-only.
# ---------------------------------------------------------------------------
class _ScatterHead(_nn.Module):
    """A small MLP, RANDOM INIT, on top of the fixed scattering feature. Penultimate = embedding."""
    def __init__(self, in_dim, n_classes, emb=64):
        super().__init__()
        self.feat = _nn.Sequential(_nn.Linear(in_dim, 256), _nn.ReLU(), _nn.Linear(256, emb))
        self.head = _nn.Linear(emb, n_classes)

    def embed(self, x):
        return self.feat(x)

    def forward(self, x):
        return self.head(self.feat(x))


def _scatter_background(n_alphabets=None, max_per=None):
    """Build the BACKGROUND scattering-feature set (X, y). Held data; eval excluded."""
    bg = _ow.alphabets("background")
    if n_alphabets:
        bg = bg[:n_alphabets]
    X, y, cid = [], [], 0
    for al in bg:
        for c in _ow.characters(al, split="background"):
            ds = _ow.drawings(c)
            if max_per:
                ds = ds[:max_per]
            fs = [_sf.scatter_trace_image(_ow.load_strokes(d)) for d in ds]
            fs = [f for f in fs if f is not None]
            if len(fs) >= 2:
                for f in fs:
                    X.append(f); y.append(cid)
                cid += 1
    return _np.array(X, dtype=_np.float32), _np.array(y), cid


def train_scatter_head(*, n_alphabets=None, max_per=None, epochs=20, bs=256, lr=1e-3,
                       seed=0, log=print, _cache=None):
    """Train an MLP head FROM SCRATCH (random init) on the fixed-scattering background features
    (supervised on background classes; eval held out). Returns (model, mu, sd) — the EARNED
    perception head. NO borrowed weights. `_cache` (optional) reuses precomputed (X,y,ncls)."""
    torch.manual_seed(seed); _np.random.seed(seed)
    if _cache is not None:
        X, y, ncls = _cache
    else:
        X, y, ncls = _scatter_background(n_alphabets, max_per)
    log(f"  background scatter TRAIN set: {len(X)} feats / {ncls} classes (held data; eval excluded). "
        f"FROM-SCRATCH random init.")
    mu = X.mean(0); sd = X.std(0) + 1e-6
    Xt = torch.tensor((X - mu) / sd); yt = torch.tensor(y, dtype=torch.long)
    model = _ScatterHead(X.shape[1], ncls)
    log(f"  random-init proof: head layer-0 weight std = {float(model.feat[0].weight.detach().std()):.4f} "
        f"(initialised, NOT loaded)")
    opt = torch.optim.Adam(model.parameters(), lr=lr); lossf = _nn.CrossEntropyLoss()
    n = len(Xt); model.train()
    for ep in range(epochs):
        perm = torch.randperm(n); tot = 0.0
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            opt.zero_grad(); loss = lossf(model(Xt[idx]), yt[idx]); loss.backward(); opt.step()
            tot += float(loss) * len(idx)
        if (ep + 1) % max(1, epochs // 4) == 0:
            log(f"    epoch {ep + 1}/{epochs}  train-loss {tot / n:.3f}")
    model.eval()
    return model, mu, sd


def embed_scatter(model, mu, sd, path):
    """The EARNED embedding of a trace = MLP head over its fixed-scattering feature."""
    f = _sf.scatter_trace_image(_ow.load_strokes(path))
    if f is None:
        return None
    with torch.no_grad():
        return model.embed(torch.tensor(((f - mu) / sd).astype(_np.float32))[None]).numpy()[0]


def untrained_scatter_head(in_dim, seed=0):
    """A RANDOM-INIT, UNTRAINED MLP head on scattering — the discriminative control. Must NOT
    beat fixed scattering (architecture alone is not the lift; TRAINING does the work)."""
    torch.manual_seed(seed)
    return _ScatterHead(in_dim, 2).eval()
