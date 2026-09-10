"""Block 328000 — extract an LLM's CONCEPT identity as a reusable CAN operator.

Tier 2 of the extraction direction (after knowledge, block 327). A CONCEPT is
not a node with fixed neighbours; it is a RELATION AS A REUSABLE OPERATOR — a
signature that applies to entities it never co-occurred with. The test bar rises
from held-out ENTAILMENT (327) to held-out TRANSFER: extract the concept from
context A, apply it in context B it never saw, and check the substrate produces
the right answer BY THE CONCEPT'S STRUCTURE, not by stored B-instances.

Concept studied: `opposite-of` (antonymy). Its identity has two parts:
  GEOMETRIC signature — in the LLM's own representation, "opposite" is a linear
    operator W (fit on A antonym pairs) that maps a word's vector to its
    opposite's neighbourhood. This is WHICH entities are opposites, recognised
    without a labelled edge.
  SUBSTRATE signature — two opposite Concept nodes couple with a NEGATIVE Ising
    weight (block 321's frustration): clamp one, the substrate settles the other
    to the opposite state. This is the concept's DYNAMICS on the graph.

TRANSFER: for a held-out B word, apply W to its vector, retrieve the nearest B
candidate as a graph operation (the concept picks the opposite it was never
told), wire that pair with the negative-coupling signature, and let the
substrate settle — reproducing the opposite relation in a context the concept
never co-occurred with. No LLM at query time (W and the coupling sign are frozen
recovered structure; retrieval + settle are substrate ops).

Protected CAN internals + seed grammar are READ-ONLY (built-to). torch/model
appear only at fit time (offline).
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# EXTRACT (model side): word vectors + the antonym operator W (fit on A).
# ---------------------------------------------------------------------------

def word_vectors(model, tokenizer, words):
    """A single vector per word = the model's input embedding of its first
    token (a stable, query-time-free representation). Returns {word: vec[d]}."""
    E = model._t("model.embed_tokens.weight")
    out = {}
    for w in words:
        ids = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
        if not ids:
            ids = tokenizer(w, add_special_tokens=False)["input_ids"]
        out[w] = E[ids[0]].astype(np.float32)
    return out


def fit_opposite_operator(vecs, pairs_A, *, ridge=1.0):
    """Fit the antonym operator W on context-A pairs: W maps a word's vector to
    its opposite's vector (ridge regression over the A pairs, both directions —
    opposite is symmetric). W is the extracted CONCEPT IDENTITY (geometric
    signature); it is frozen and applied to unseen B words. Returns W [d, d]."""
    X, Y = [], []
    for a, b in pairs_A:
        if a in vecs and b in vecs:
            X.append(vecs[a]); Y.append(vecs[b])   # a -> b
            X.append(vecs[b]); Y.append(vecs[a])   # b -> a (symmetric)
    X = np.stack(X).astype(np.float32)
    Y = np.stack(Y).astype(np.float32)
    d = X.shape[1]
    A = X.T @ X + ridge * np.eye(d, dtype=np.float32)
    W = np.linalg.solve(A, X.T @ Y).T.astype(np.float32)   # [d, d]
    return W


def apply_operator_retrieve(W, vecs, query_word, candidates):
    """Apply the concept operator to a held-out word and RETRIEVE the nearest
    candidate (cosine) — the substrate-style graph operation that picks the
    opposite the concept was never told. Returns the retrieved word."""
    q = vecs[query_word]
    pred = W @ q
    pred = pred / (np.linalg.norm(pred) + 1e-9)
    best, bestsim = None, -2.0
    for c in candidates:
        if c == query_word:
            continue
        v = vecs[c]; v = v / (np.linalg.norm(v) + 1e-9)
        sim = float(pred @ v)
        if sim > bestsim:
            bestsim, best = sim, c
    return best


# ---------------------------------------------------------------------------
# SUBSTRATE signature: opposite = negative Ising coupling. Build a Microtheory
# for a recovered opposite pair and settle (dynamics of the concept).
# ---------------------------------------------------------------------------

def opposite_settle(substrate, seed_paths, word_a, word_b, *, coupling=-2.0,
                    clamp_a=1.0, temperature=1.0):
    """Wire two Concept nodes with the concept's SUBSTRATE signature (a negative
    coupling), clamp `word_a` (external_field = clamp_a), and settle on the
    substrate's own BP. Returns the settled state of `word_b` — which should be
    the OPPOSITE of the clamped `word_a` if the negative-coupling signature is
    the concept's dynamics. `coupling` < 0 is the extracted concept sign."""
    import json
    from substrate.seed_loader import engine_rules_only
    from domains.can_native_bp import run_loopy_bp
    for path in seed_paths:
        substrate.load_seed_manifest(engine_rules_only(json.load(open(path))))
    mt = substrate.add_node("Microtheory",
                            {"temperature": float(temperature),
                             "discrete_mode": "2state"})
    ca = substrate.add_node("Concept", {"name": word_a, "state": 0.0,
                                        "external_field": float(clamp_a),
                                        "identity_field": 0.0})
    cb = substrate.add_node("Concept", {"name": word_b, "state": 0.0,
                                        "external_field": 0.0,
                                        "identity_field": 0.0})
    substrate.add_edge(mt, "has_concept", ca, {})
    substrate.add_edge(mt, "has_concept", cb, {})
    substrate.add_edge(ca, "causal_influence", cb, {"weight": float(coupling)})
    substrate.add_edge(cb, "causal_influence", ca, {"weight": float(coupling)})
    bp = run_loopy_bp(substrate, mt, combine="max_product")
    fs = bp["final_state"]
    return float(fs.get(cb.value if hasattr(cb, "value") else int(cb), 0.0))
