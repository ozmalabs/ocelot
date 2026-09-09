"""Distill an open-weight model's token-embedding geometry into a substrate
Concept graph — no torch, no inference, mechanical I/O + numpy only.

The user's question: *"given this, could we distill open weights into a graph?
— at least partially."* This is the falsifiable test. See
docs/research/psychology_affect/WEIGHT_DISTILLATION_TRANSFER_PREREG.md.

WHAT IS DISTILLED (honest): the model's token EMBEDDING matrix
(`domains.model_reader`) is its native word geometry — each row a token's
vector, the geometry IS its language knowledge. We turn that dense geometry
into a SPARSE, LOSSY graph: for each token, its top-K cosine neighbours become
`causal_influence` edges weighted by a QUANTISED cosine. The dense matrix is
then DISCARDED — the graph is all that remains.

The claim under test: the SUBSTRATE'S OWN read over this DISTILLED GRAPH (not
a re-query of the raw matrix) reproduces the model's native behaviour —
nearest-neighbour and vector analogy — above chance, and degrades GRACEFULLY
(degree, not cliff) as K shrinks. That would show capability, not just
structure, transfers weight → graph.

ANTI-FAKING: the graph is sparsified + quantised, so it is strictly LESS
information than the matrix — transfer is a real test, not an identity. The
raw matrix is not retained on the `DistilledGraph` for test-time reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from . import model_reader as mr


def load_embedding(model_dir: str,
                   tensor: str = "embeddings.word_embeddings.weight"):
    """Return (W [vocab, dim] float32, vocab token->id) read straight from the
    safetensors file — no torch, no inference. Falls back to the first
    embedding-like tensor if the named one is absent."""
    import os
    path = os.path.join(model_dir, "model.safetensors")
    names = mr.tensor_names(path)
    if tensor not in names:
        cand = [n for n in names if "word_embeddings" in n] or \
               [n for n in names if "embed" in n.lower()
                and "position" not in n and "token_type" not in n
                and "LayerNorm" not in n]
        if not cand:
            raise ValueError("no token-embedding tensor in %s" % path)
        tensor = cand[0]
    W = mr.read_tensor(path, tensor)
    vocab = mr.read_vocab(model_dir)
    return W, vocab


def _unit_rows(W: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(W, axis=1, keepdims=True)
    return W / (n + 1e-9)


@dataclass
class DistilledGraph:
    """A sparse, lossy graph distilled from an embedding matrix.

    `neighbours[i]` -> list of (j, quantised_cosine) for token id i's top-K.
    `vocab` / `inv` -> token<->id maps. The dense matrix is NOT stored.
    `k`, `quant` -> the sparsification degree + weight quantum used (the lossy
    knobs). `token_ids` -> the subset of vocab ids distilled (a frequency /
    sample window; the graph covers only these).
    """

    neighbours: dict
    vocab: dict
    inv: dict
    k: int
    quant: float
    token_ids: list

    def has(self, token: str) -> bool:
        return self.vocab.get(token) in self.neighbours

    def graph_neighbours(self, token: str, top: int = 8):
        """Token -> [(neighbour_token, weight)] from the GRAPH edges only."""
        i = self.vocab.get(token)
        if i is None or i not in self.neighbours:
            return []
        out = [(self.inv[j], w) for j, w in self.neighbours[i]]
        return out[:top]


def distill(W: np.ndarray, vocab: dict, *, token_ids=None, k: int = 16,
            quant: float = 0.05, batch: int = 512) -> DistilledGraph:
    """Distill the embedding matrix into a `DistilledGraph`.

    For each distilled token, keep its top-`k` cosine neighbours (within the
    distilled set), each weighted by cosine ROUNDED to `quant` (the lossy
    quantisation). `token_ids` restricts the distilled vocabulary (default: a
    frequency-proxy window = the first 8000 ids, which for a BERT/MiniLM
    WordPiece vocab are the special+most-common tokens). The dense matrix is
    used HERE (distillation time) and then dropped — the returned graph does
    not retain it.
    """
    inv = {i: t for t, i in vocab.items()}
    if token_ids is None:
        token_ids = list(range(min(8000, W.shape[0])))
    token_ids = [i for i in token_ids if 0 <= i < W.shape[0]]
    sub = _unit_rows(W[token_ids])            # [n, dim] unit rows
    idpos = {tid: pos for pos, tid in enumerate(token_ids)}
    n = len(token_ids)
    neighbours: dict = {}
    for start in range(0, n, batch):
        end = min(start + batch, n)
        sims = sub[start:end] @ sub.T          # [b, n] cosine
        for r in range(end - start):
            row = sims[r]
            gi = start + r
            row[gi] = -2.0                      # exclude self
            top = np.argpartition(-row, k)[:k]
            top = top[np.argsort(-row[top])]
            tid = token_ids[gi]
            neighbours[tid] = [
                (token_ids[j], round(float(row[j]) / quant) * quant)
                for j in top if row[j] > 0.0
            ]
    return DistilledGraph(neighbours=neighbours, vocab=vocab, inv=inv,
                          k=k, quant=quant, token_ids=token_ids)


# ---------------------------------------------------------------------------
# Substrate materialisation — build the distilled graph as real Concept nodes
# + causal_influence edges the substrate's own read operates over.
# ---------------------------------------------------------------------------

def materialise(substrate, dg: DistilledGraph, *, tokens=None):
    """Build (a subset of) the distilled graph as substrate Concept nodes +
    weighted `causal_influence` edges. Returns {token: node}. `tokens`
    restricts which tokens are materialised (default: all distilled). The
    substrate then reads coherence/analogy over THIS graph — never the matrix.
    """
    inner = substrate._inner if hasattr(substrate, "_inner") else substrate
    if tokens is None:
        tokens = [dg.inv[i] for i in dg.neighbours]
    tokset = set(tokens)
    node = {}

    def _mk(tok):
        if tok in node:
            return node[tok]
        c = inner.add_node("Concept", {"name": tok, "state": 0.0,
                                       "external_field": 0.0,
                                       "identity_field": 0.0})
        node[tok] = c
        return c

    for tok in tokens:
        _mk(tok)
    for tok in tokens:
        for nb_tok, w in dg.graph_neighbours(tok, top=dg.k):
            if nb_tok not in tokset:
                continue
            src, dst = node[tok], _mk(nb_tok)
            try:
                inner.add_edge(src, "causal_influence", dst, {"weight": float(w)})
            except Exception:
                inner.add_edge_unchecked(src, "causal_influence", dst)
    return node


# ---------------------------------------------------------------------------
# Graph-only reads (the substrate's behaviour over the DISTILLED graph).
# These use ONLY the graph edges — never the dense matrix.
# ---------------------------------------------------------------------------

def graph_knn(dg: DistilledGraph, token: str, top: int = 8):
    """Nearest neighbours of `token` from the graph edges only."""
    return dg.graph_neighbours(token, top=top)


def graph_analogy(dg: DistilledGraph, a: str, b: str, c: str, top: int = 5):
    """Analogy a:b :: c:? over the GRAPH — a spreading read, no matrix.

    Interpretation: the b-neighbourhood shifted onto c. We take c's neighbours
    and the b-neighbours, and score candidates by graph proximity to c that
    also resemble the a→b relation's neighbourhood — a purely structural,
    two-hop graph read (the substrate's convergent-field style), NOT a vector
    subtraction on the dense matrix. Returns [(token, score)].

    Concretely: candidates = 2-hop neighbourhood of c; score(x) = weight(c→x
    or c→·→x) boosted if x is also in b's neighbourhood but NOT in a's
    (the "b-minus-a" direction rendered as set structure). This is a lossy
    graph analogue of b - a + c; it is EXPECTED to be weaker than the dense
    vector analogy — that gap is the honest transfer measurement.
    """
    def nbset(t):
        return {n for n, _ in dg.graph_neighbours(t, top=dg.k)}

    if not (dg.has(a) and dg.has(b) and dg.has(c)):
        return []
    a_nb, b_nb = nbset(a), nbset(b)
    direction = b_nb - a_nb                     # b-ish, not a-ish
    # 2-hop neighbourhood of c
    cand: dict = {}
    for x, w1 in dg.graph_neighbours(c, top=dg.k):
        cand[x] = cand.get(x, 0.0) + w1
        for y, w2 in dg.graph_neighbours(x, top=dg.k):
            cand[y] = cand.get(y, 0.0) + 0.5 * w1 * w2
    for x in list(cand):
        if x in direction:
            cand[x] += 1.0                      # aligned with b-minus-a
        if x in (a, b, c):
            cand.pop(x, None)
    ranked = sorted(cand.items(), key=lambda kv: -kv[1])
    return ranked[:top]
