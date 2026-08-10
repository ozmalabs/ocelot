"""timing_objective_head — a from-scratch learned head trained with a TIMING-SENSITIVE objective
so the recognizer USES the timing the spatio-temporal feature exposes. earn-not-borrow, donkey=0.

THE LAST RUNG: the spatio-temporal feature (2041a833) SEES timing, but cosine 1-NN LEANS ON SHAPE,
so motor realism did not convert (physics-aug ~tied unconstrained). Make the RECOGNIZER use timing:
train a from-scratch head with HARD-NEGATIVE CONTRASTIVE where the hard negatives are SAME-SHAPE-
DIFFERENT-TIMING (reversed motion). To push a same-shape hard negative AWAY, the embedding MUST
encode timing — it cannot collapse to shape.

  positive  = the SAME drawing (anchor) — its embedding pulled to itself across the batch's other
              same-char views (supervised-contrastive over background CLASS labels).
  hard neg  = the anchor's REVERSED-MOTION variant (same spatial shape, opposite dynamics) — pushed
              AWAY. A shape-only embedding would place it ON TOP of the anchor; the timing objective
              forces them apart.

A SHAPE-objective control = the same architecture trained with ordinary class-contrastive and NO
timing hard-negatives — it collapses same-shape-different-timing pairs.

EARN-NOT-BORROW: random init (proof printed), trained ONLY on the held BACKGROUND set's spatio-
temporal features; NO pretrained net, NO downloaded weights. torch = from-scratch trainer; numpy =
feature adapter. The embedding feeds the HELD recognizer (cosine 1-NN).
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: feature batching math
import torch                        # FROM-SCRATCH TRAINER (random init; NO pretrained models)
import torch.nn as _nn
import torch.nn.functional as _F
import domains.omniglot_world as _ow
import domains.spatiotemporal_feature as _stf
import domains.earned_augmentation as _ea


class _Head(_nn.Module):
    """A small MLP, RANDOM INIT (no pretrained weights). Output = the L2-normalised embedding."""
    def __init__(self, in_dim, emb=64):
        super().__init__()
        self.net = _nn.Sequential(_nn.Linear(in_dim, 256), _nn.ReLU(), _nn.Linear(256, emb))

    def forward(self, x):
        return _F.normalize(self.net(x), dim=-1)


def _build_features(n_alphabets=None, max_per=None, aug_mode=None, n_aug=0, seed=0):
    """Build the held-background spatio-temporal feature set with anchors, their class ids, and
    each anchor's REVERSED-MOTION hard-negative feature. Held data; eval excluded.
    Returns (X anchors, y classes, Xrev hard-negs, mu, sd)."""
    rng = _np.random.RandomState(seed)
    bg = _ow.alphabets("background")
    if n_alphabets:
        bg = bg[:n_alphabets]
    X, y, Xrev, cid = [], [], [], 0
    for al in bg:
        for c in _ow.characters(al, split="background"):
            ds = _ow.drawings(c)
            if max_per:
                ds = ds[:max_per]
            took = False
            for d in ds:
                st = _ow.load_strokes(d)
                f = _stf.spatiotemporal_scatter(st)
                if f is None:
                    continue
                rev = [_np.asarray(s, float)[::-1] for s in st[::-1]]   # same shape, reversed motion
                fr = _stf.spatiotemporal_scatter(rev)
                if fr is None:
                    continue
                X.append(f); y.append(cid); Xrev.append(fr); took = True
                for _ in range(n_aug):                                  # optional earned aug positives
                    v = (_ea.generate_physical_variant(st, rng) if aug_mode == "physical"
                         else _ea.generate_variant(st, rng))
                    fv = _stf.spatiotemporal_scatter(v)
                    if fv is not None:
                        X.append(fv); y.append(cid)
                        rv = [_np.asarray(s, float)[::-1] for s in v[::-1]]
                        frv = _stf.spatiotemporal_scatter(rv)
                        Xrev.append(frv if frv is not None else fr)
            if took:
                cid += 1
    X = _np.array(X, dtype=_np.float32); Xrev = _np.array(Xrev, dtype=_np.float32)
    mu = X.mean(0); sd = X.std(0) + 1e-6
    return (X - mu) / sd, _np.array(y), (Xrev - mu) / sd, mu, sd


def train(*, n_alphabets=None, max_per=None, timing=True, aug_mode=None, n_aug=0,
          epochs=30, bs=256, lr=1e-3, emb=64, tau=0.1, hard_w=1.0, seed=0, log=print):
    """Train the head FROM SCRATCH. timing=True adds the SAME-SHAPE-REVERSED-MOTION HARD NEGATIVE
    term (the timing objective); timing=False = the SHAPE-objective control (class-contrastive only).
    Returns (model, mu, sd). NO borrowed weights — random init + held-background-only training."""
    torch.manual_seed(seed); _np.random.seed(seed)
    X, y, Xrev, mu, sd = _build_features(n_alphabets, max_per, aug_mode, n_aug, seed)
    log(f"  background ST-feature set: {len(X)} feats / {len(set(y))} classes "
        f"(held; eval excluded). timing-objective={timing}. FROM-SCRATCH random init.")
    Xt = torch.tensor(X); yt = torch.tensor(y); Xr = torch.tensor(Xrev)
    model = _Head(X.shape[1], emb)
    log(f"  random-init proof: layer-0 weight std = {float(model.net[0].weight.detach().std()):.4f} "
        f"(initialised, NOT loaded)")
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(Xt); model.train()
    for ep in range(epochs):
        perm = torch.randperm(n); tot = 0.0
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            za = model(Xt[idx])                       # anchor embeddings (normalised)
            lab = yt[idx]
            # SUPERVISED-CONTRASTIVE over class labels (positives = same class in the batch)
            sim = za @ za.t() / tau
            m = lab.unsqueeze(0) == lab.unsqueeze(1)
            eye = torch.eye(len(idx), dtype=torch.bool)
            m = m & ~eye
            logits = sim.masked_fill(eye, -1e9)
            logp = _F.log_softmax(logits, dim=1)
            pos = (logp * m).sum(1) / m.sum(1).clamp(min=1)
            loss = -pos.mean()
            if timing:
                # TIMING HARD NEGATIVE: each anchor's reversed-motion variant must be FAR (low cos).
                zr = model(Xr[idx])
                hard = (za * zr).sum(1)               # cos(anchor, same-shape-reversed-timing)
                loss = loss + hard_w * hard.clamp(min=0).mean()   # penalise being close to it
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss) * len(idx)
        if (ep + 1) % max(1, epochs // 4) == 0:
            log(f"    epoch {ep + 1}/{epochs}  loss {tot / n:.3f}")
    model.eval()
    return model, mu, sd


def embed(model, mu, sd, path):
    """The EARNED embedding of a trace = the timing-objective head over its spatio-temporal feature."""
    f = _stf.st_feature(path)
    if f is None:
        return None
    with torch.no_grad():
        return model(torch.tensor(((f - mu) / sd).astype(_np.float32))[None]).numpy()[0]


def embed_feature(model, mu, sd, f):
    """Embed a precomputed spatio-temporal feature vector (for reversed-motion controls)."""
    if f is None:
        return None
    with torch.no_grad():
        return model(torch.tensor(((f - mu) / sd).astype(_np.float32))[None]).numpy()[0]
