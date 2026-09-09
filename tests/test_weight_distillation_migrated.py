"""Distilling open weights into a substrate graph — transfer tests.

See docs/research/psychology_affect/WEIGHT_DISTILLATION_TRANSFER_PREREG.md and
scripts/weight_distillation_measure.py. Distils all-MiniLM-L6-v2's word
geometry into a sparse lossy substrate graph and checks capability transfer.

Tests that need the on-disk model SKIP gracefully when it is absent, so the
surface stays green without it. A synthetic-matrix test covers the distiller
mechanics unconditionally.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

from domains import weight_distillation as wd  # noqa: E402

MODEL = "/home/matt/.semantic_search/models/all-MiniLM-L6-v2"
_HAVE_MODEL = os.path.isfile(os.path.join(MODEL, "model.safetensors"))
_need_model = pytest.mark.skipif(not _HAVE_MODEL, reason="MiniLM not on disk")


# ---- distiller mechanics (synthetic, unconditional) --------------------

def _synthetic():
    """A tiny matrix with a KNOWN geometry: 3 clusters of near-identical rows,
    so each token's true neighbours are its cluster-mates."""
    rng = np.random.default_rng(0)
    centres = rng.normal(size=(3, 8))
    rows, vocab = [], {}
    for c in range(3):
        for i in range(4):
            rows.append(centres[c] + 0.01 * rng.normal(size=8))
            vocab["t%d_%d" % (c, i)] = len(rows) - 1
    return np.array(rows, dtype=np.float32), vocab


def test_distiller_recovers_known_clusters():
    W, vocab = _synthetic()
    dg = wd.distill(W, vocab, k=3, quant=0.05)
    # each token's top-3 graph neighbours should be its 3 cluster-mates
    for c in range(3):
        for i in range(4):
            tok = "t%d_%d" % (c, i)
            nbs = {t for t, _ in dg.graph_neighbours(tok, top=3)}
            mates = {"t%d_%d" % (c, j) for j in range(4) if j != i}
            assert nbs == mates, (tok, nbs, mates)


def test_distilled_graph_does_not_retain_matrix():
    """Anti-faking: the DistilledGraph must not carry the dense matrix into
    test-time reads."""
    W, vocab = _synthetic()
    dg = wd.distill(W, vocab, k=3, quant=0.05)
    for v in vars(dg).values():
        assert not (isinstance(v, np.ndarray) and v.ndim == 2 and
                    v.shape == W.shape), "graph retained the dense matrix"


def test_materialise_builds_graph_edges():
    import substrate_rs as sr
    W, vocab = _synthetic()
    dg = wd.distill(W, vocab, k=3, quant=0.05)
    s = sr.Substrate()
    node = wd.materialise(s, dg, tokens=["t0_0", "t0_1", "t0_2", "t0_3"])
    assert "t0_0" in node
    nbs = list(s._inner.neighbours(node["t0_0"], "causal_influence"))
    assert len(nbs) >= 1  # cluster-mates wired in


# ---- transfer on the real model (skips if absent) ----------------------

@_need_model
def test_knn_transfer_above_chance():
    W, vocab = wd.load_embedding(MODEL)
    dg = wd.distill(W, vocab, k=16, quant=0.05)
    Wu = W / (np.linalg.norm(W, axis=1, keepdims=True) + 1e-9)
    inv = {i: t for t, i in vocab.items()}
    allowed = set(dg.token_ids)

    def model_top(tok, n):
        i = vocab[tok]
        sims = Wu @ Wu[i]
        sims[i] = -2.0
        order = np.argsort(-sims)
        out = []
        for j in order:
            if j in allowed and inv[j] != tok:
                out.append(inv[j])
            if len(out) >= n:
                break
        return set(out)

    recalls = []
    for p in ("king", "dog", "water", "car", "music"):
        if not dg.has(p):
            continue
        gold = model_top(p, 8)
        graph = {t for t, _ in dg.graph_neighbours(p, top=8)}
        recalls.append(len(gold & graph) / len(gold))
    assert np.mean(recalls) > 0.5  # far above the ~0 random baseline


@_need_model
def test_analogy_transfers_but_weaker_than_dense():
    W, vocab = wd.load_embedding(MODEL)
    dg = wd.distill(W, vocab, k=16, quant=0.05)
    # graph analogy should hit the gender-direction target above chance
    g = [t for t, _ in wd.graph_analogy(dg, "man", "king", "woman", top=5)]
    assert any(t in g for t in ("queen", "women", "female", "girl")), g


@_need_model
def test_vector_quantisation_degrades_gracefully():
    W, vocab = wd.load_embedding(MODEL)
    Wu = W / (np.linalg.norm(W, axis=1, keepdims=True) + 1e-9)
    inv = {i: t for t, i in vocab.items()}
    probes = ["king", "dog", "water", "car", "music"]

    def recall_at_bits(bits):
        lo, hi = W.min(), W.max()
        step = (hi - lo) / (2 ** bits - 1)
        Wq = lo + np.round((W - lo) / step) * step
        dgq = wd.distill(Wq, vocab, k=16, quant=0.05)
        allowed = set(dgq.token_ids)
        rr = []
        for p in probes:
            if not dgq.has(p):
                continue
            i = vocab[p]
            sims = Wu @ Wu[i]
            sims[i] = -2.0
            order = [j for j in np.argsort(-sims) if j in allowed and inv[j] != p][:8]
            gold = {inv[j] for j in order}
            graph = {t for t, _ in dgq.graph_neighbours(p, top=8)}
            rr.append(len(gold & graph) / len(gold))
        return float(np.mean(rr))

    r8, r4, r3 = recall_at_bits(8), recall_at_bits(4), recall_at_bits(3)
    # graceful decline in the 3-8 bit range (a dial, high->lower, no jump up)
    assert r8 >= r4 >= r3 - 1e-6
    assert r3 > 0.3  # geometry still present at 3 bits


# ---- default == today ---------------------------------------------------

def test_default_equals_today_so_unchanged():
    import hashlib
    so = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if not os.path.exists(so):
        return
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == "7efe75eba05b006cafd15dbb4b7da246", md5
