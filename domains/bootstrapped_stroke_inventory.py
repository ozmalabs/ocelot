"""bootstrapped_stroke_inventory — pay the data-bound PARSE floor the EARNED way: TEACHER-BOOTSTRAP a
stable identity-bearing STROKE INVENTORY with Gemma (strong teacher), DISTILL the cluster STRUCTURE
into HELD shape-math signatures, parse + recognize STANDALONE (no Gemma at recognition). The arc's
synthesis (parse data-bound 0891e99c + strong-teacher conversion 8e29d42a). graph-native, donkey=0.

THE IDEA: from-scratch turn-profile clustering gave only 0.19 parse stability (0891e99c) — the
sub-part inventory is DATA-BOUND. Gemma's crystallized data makes the sub-stroke clusters MEANINGFUL.
So: cluster background sub-strokes in GEMMA's vision-feature space (teacher, read-only) -> each
cluster = a stroke-IDENTITY -> DISTILL each cluster into a HELD representation: the cluster's MEDOID
sub-stroke POINT-SET (held geometry, NOT Gemma's features). Recognition parses a char by assigning
each segment to its nearest held medoid (held ShapeContextDist) -> identity sequence -> per-stroke AbS.

EARN-NOT-BORROW: Gemma is the read-only TEACHER for the INVENTORY clustering ONLY. The distilled
inventory is HELD geometry (medoid point-sets) + the recognition is held shape-math — NO Gemma at
recognition (standalone, savant-3b provable). Gemma's weights are never copied in; only the cluster
STRUCTURE (which sub-strokes group together) is earned, then re-represented in held geometry.

torch (Gemma) is used ONLY in the inventory bootstrap (build_inventory). Recognition (parse_identities,
recognize) is Gemma-free + torch-free. numpy adapter-only. No LLM.

Superseded (2026-07-02) as the source of truth by the graph-resident stroke codebook
(domains/stroke_codebook.py migrates this module's `.bigtmp/gemma_stroke_inventory.pkl` medoids
INTO the graph); domains/ink_decode.py does the decode (design
scratchpad/HANDWRITING_DESIGN.md). No behavior change here; this module is unmodified otherwise.
"""
from __future__ import annotations
import os
import pickle
import numpy as _np                 # ADAPTER: clustering + point-set geometry
import substrate_rs as _srs
import domains.omniglot_world as _ow
import domains.per_stroke_abs as _ps

_NS = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     ".bigtmp", "gemma_stroke_inventory.pkl")


# ---- Gemma sub-stroke embedding (TEACHER, read-only; torch here only) ----

def _render_ps(point_set, canvas=180):
    """Render a normalized sub-stroke point-set as a Gemma image (ADAPTER, numpy/PIL)."""
    from PIL import Image
    a = _np.asarray(point_set, float)
    img = _np.full((canvas, canvas, 3), 255, _np.uint8)
    if len(a) < 2:
        return Image.fromarray(img)
    mn, mx = a.min(0), a.max(0); span = _np.maximum(mx - mn, 1e-6)
    g = (a - mn) / span * (canvas - 24) + 12
    for i in range(len(g) - 1):
        for t in _np.linspace(0, 1, 30):
            x, y = (g[i] * (1 - t) + g[i + 1] * t).astype(int)
            img[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4] = 0
    return Image.fromarray(img)


def _gemma_embed_ps(point_set):
    """Gemma vision feature of a sub-stroke (TEACHER, read-only). torch here only."""
    import torch
    import domains.gemma_teacher_adapter as gta
    model, ip = gta._load()
    pil = _render_ps(point_set)
    with torch.no_grad():
        proc = ip(images=pil, return_tensors="pt")
        out = model(pixel_values=proc["pixel_values"], pixel_position_ids=proc["image_position_ids"])
        lh = out.last_hidden_state if hasattr(out, "last_hidden_state") else out[0]
        v = lh.reshape(-1, lh.shape[-1]).mean(0).cpu().numpy()
    return v / (_np.linalg.norm(v) + 1e-9)


# ---- BUILD the inventory: Gemma-cluster background sub-strokes -> held medoid point-sets ----

def build_inventory(n_alphabets=10, per_alpha=8, K=40, N=16, seed=0, use_cache=True, teacher="gemma"):
    """Teacher-bootstrap the inventory: collect background sub-stroke point-sets, embed with the
    TEACHER (Gemma), cluster (k-means in teacher space), DISTILL each cluster -> its MEDOID held
    point-set (the held stroke-identity geometry). Returns a list of K held medoid point-sets.
    teacher='gemma' (strong) | 'scratch' (turn-profile, the from-scratch control) | 'random'."""
    if use_cache and teacher == "gemma" and os.path.exists(CACHE):
        c = pickle.load(open(CACHE, "rb"))
        if c.get("K") == K and c.get("n_alphabets") == n_alphabets:
            return c["medoids"]
    strokes = []
    for al in _ow.alphabets("background")[:n_alphabets]:
        for c in _ow.characters(al, split="background")[:per_alpha]:
            for s in _ps.stroke_point_sets(_ow.drawings(c)[0], N=N):
                strokes.append(s)
    # teacher embeddings (the clustering space)
    if teacher == "gemma":
        emb = _np.array([_gemma_embed_ps(s) for s in strokes])
    elif teacher == "scratch":
        import domains.stroke_library as sl
        emb = _np.array([sl.stroke_descriptor(s) if sl.stroke_descriptor(s) is not None
                         else _np.zeros(15) for s in strokes])
    else:                                   # random teacher (control)
        rng = _np.random.RandomState(seed); emb = rng.randn(len(strokes), 32)
    # k-means in teacher space
    rng = _np.random.RandomState(seed)
    cent = emb[rng.choice(len(emb), min(K, len(emb)), replace=False)].copy()
    lab = _np.zeros(len(emb), int)
    for _ in range(15):
        lab = ((emb[:, None] - cent[None]) ** 2).sum(2).argmin(1)
        for k in range(len(cent)):
            m = emb[lab == k]
            if len(m):
                cent[k] = m.mean(0)
    # DISTILL: each cluster -> its MEDOID sub-stroke point-set (held geometry, teacher dropped)
    medoids = []
    for k in range(len(cent)):
        idx = _np.where(lab == k)[0]
        if len(idx) == 0:
            continue
        d = ((emb[idx] - cent[k]) ** 2).sum(1)
        medoids.append(strokes[idx[int(d.argmin())]])      # the held point-set nearest the centroid
    if use_cache and teacher == "gemma":
        try:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            pickle.dump({"K": K, "n_alphabets": n_alphabets, "medoids": medoids}, open(CACHE, "wb"))
        except Exception:
            pass
    return medoids


# ---- STANDALONE recognition over the HELD inventory (NO Gemma) ----

def _scd(a, b):
    return float(_NS.evaluate({"type": "ShapeContextDist", "a": _L(a), "b": _L(b)}, {}))


def parse_identities(path, medoids, N=16):
    """Parse a char into a stroke-IDENTITY histogram over the HELD medoid inventory (nearest medoid by
    held ShapeContextDist). NO Gemma — pure held shape-math. Count-stable (a fixed-K vector)."""
    h = _np.zeros(len(medoids))
    for s in _ps.stroke_point_sets(path, N=N):
        d = [_scd(s, m) for m in medoids]
        h[int(_np.argmin(d))] += 1
    n = _np.linalg.norm(h)
    return h / n if n > 0 else h
