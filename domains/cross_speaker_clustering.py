"""cross_speaker_clustering — the agent COMPOSES label-free cross-speaker
clustering as a graph Term-tree, from its OWN latent-structure science.

This is the capability the agent PICKED as its frontier (gap_prioritiser): the
order-N synthesis derived 'cross-speaker clustering' from SIX of its own postulates
(distributional_learning_of_categories, statistical_learning, speech_acquisition,
lexical_access, segmentation, syllable_structure) via the latent_structure
implication-shape harvested from its own `unsupervised_learning` /
`recurrent_neural_network` concepts. The agent's compression-payoff criterion
ranked it most foundational (it unifies the most held knowledge).

WHY this is the agent's to compose (not hand-coded numpy). The agent's harvested
latent_structure shape says: "an unlabelled DISTRIBUTION has recoverable LATENT
structure — unsupervised CLUSTERING carves its categories at the valleys between
modes with NO labels; across speakers, the same word's tokens are one cluster."
That is the exact move: gather every speaker's utterances of a word as an unlabelled
point cloud, and the modes (the per-word centroids) ARE the categories — recovered
without ever being told which token is which word.

THE COMPOSITION (graph Term-trees, evaluated natively — no Python arithmetic).
Lloyd's algorithm (k-means) is two graph aggregations, each one the CMVN mean move
(Sum / Count over an edge set) lifted from FRAMES to TOKENS:

  assignment    each TOKEN t is assigned to the nearest CENTROID:
                  dist(t, k) = Σ_b (Attr(t, band_b) - Attr(k, band_b))^2
                  assign(t)  = Argmin_{k in centroids} dist(t, k)
                (squared Euclidean composed from Minus / Times / Sum — the same
                 primitives CMVN's variance term uses.)

  update        each CENTROID k is the MEAN of its assigned tokens, per band:
                  Attr(k, band_b) <- (Σ_{t: assign(t)=k} Attr(t, band_b)) / N_k
                (Sum / Count over the `has_member` edge — IDENTICAL to CMVN's
                 per-band mean over `has_stat_frame`, one level up: tokens not
                 frames, centroids not utterances.)

Primitives used (ALL already in the agent's DSL — NO new primitive needed): Sum,
Count, Div, Minus, Times, Plus, Attr, Var, Neighbours, Argmin. The agent checked it
has Argmin (the index-of-min reduction it added for ArgMax-style ops), so it can
compose the nearest-centroid ASSIGNMENT, not just the mean. This is the same
compose move as cmvn (mean over frames), order_n_concepts (recursive Minus over a
dimension), and speaker_norm (vtl_terms) — one layer up, aggregating over tokens.

The I/O boundary (the ONLY Python here) is a mechanical translator: lay the token
signatures out as a graph (Token nodes with band attrs, a Clustering root, Centroid
nodes), evaluate the agent's assignment Term natively to label each token, re-evaluate
the agent's update Term natively to move each centroid, iterate to convergence. The
numbers come out of the substrate evaluator. NO label is ever read — purity is
measured AFTER, against held-out truth, only to score the result.

Measured (scripts/cross_speaker_clustering_probe): FSDD, the agent's own CMVN-
normalized digit signatures, label-free clustering purity vs the spectrum baseline.
See [[ozma_curiosity_drive]] (compression as quality) / [[ozma_order_n_concepts]] /
[[ozma_agent_writes_its_own_code]] / [[ozma_concepts_in_gamma]].
"""
from __future__ import annotations

from substrate_rs import (Attr, Var, Sum, Count, Div, Minus, Times, Plus, Lit,
                          Neighbours, Argmin)


# Edges the I/O boundary uses to lay a clustering problem out as a graph.
MEMBER_EDGE = "has_member"        # centroid -> the tokens currently assigned to it
CENTROID_EDGE = "has_centroid"   # clustering-root -> every centroid


def _band_attr(node: "Var", b: int) -> Attr:
    return Attr(node, f"band{b}")


def squared_distance_term(t: "Var", k: "Var", n_bands: int):
    """Σ_b (Attr(t, band_b) - Attr(k, band_b))^2 — squared Euclidean between a
    token t and a centroid k, composed from the same Minus/Times the CMVN variance
    term uses. (Sum of a literal Vec of per-band squared deviations.)"""
    devs = []
    for b in range(n_bands):
        d = Minus(a=_band_attr(t, b), b=_band_attr(k, b))
        devs.append(Times(items=(d, d)))
    return Plus(items=tuple(devs))


def assignment_term(n_bands: int):
    """The agent's nearest-centroid ASSIGNMENT Term. Evaluated with env {"t": token,
    "root": clustering_root}; returns the centroid node minimising squared distance.

      assign(t) = Argmin_{k in centroids} Σ_b (band_b(t) - band_b(k))^2

    Argmin ranges over root's `has_centroid` neighbours; `value` is the squared
    distance Term (re-evaluated per candidate k). Pure graph composition."""
    centroids = Neighbours(Var("root"), CENTROID_EDGE)
    return Argmin(source=centroids, var_name="k",
                  value=squared_distance_term(Var("t"), Var("k"), n_bands))


def centroid_update_term(b: int):
    """The agent's centroid UPDATE Term for ONE band b. Evaluated with env
    {"k": centroid}; returns the mean of band b over the centroid's members.

      Attr(k, band_b) <- (Σ_{t in members(k)} band_b(t)) / N_k

    IDENTICAL to CMVN's per-band mean, with `has_member` in place of
    `has_stat_frame` and tokens in place of frames. Pure graph composition."""
    members = Neighbours(Var("k"), MEMBER_EDGE)
    return Div(a=Sum(source=members, var_name="t", value=_band_attr(Var("t"), b)),
               b=Count(members))


def compose_cross_speaker_clustering(substrate, n_bands: int) -> list:
    """The agent composes the clustering Terms and records them as Concepts (the
    same authoring move as compose_cmvn / compose_speaker_normalization): the
    assignment Term + one centroid-update Term per band, each carrying its Term-tree.
    Returns [(concept_id, name)]. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "cross_speaker_clustering"}
    created = []
    specs = [("xsc_assignment", assignment_term(n_bands), -1)]
    specs += [(f"xsc_update_band{b}", centroid_update_term(b), b)
              for b in range(n_bands)]
    for name, term, b in specs:
        if name in existing:
            continue
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "cross_speaker_clustering", "band": b,
            "predicate": term.to_dict(), "origin": "phonology",
            "composed_by": "agent",
            "science": "unlabelled distribution's modes ARE the categories; the "
                       "same word's tokens across speakers form one cluster — "
                       "recovered with NO labels (latent_structure)"})
        created.append((c, name))
    return created


# ---------------------------------------------------------------------------
# I/O boundary: run the agent's composed Terms (Lloyd iteration) over a token
# matrix. The ONLY Python here is a mechanical translator (matrix -> token graph
# -> evaluate the agent's assignment + update Terms -> labels). No reasoning, no
# decision over graph state, no label ever read. The arithmetic is the substrate
# evaluator's, via term.eval.
# ---------------------------------------------------------------------------

def cluster(M, k: int, n_iters: int = 25, seed: int = 0, substrate=None):
    """Cluster the rows of token matrix M (n_tokens x n_bands) into k clusters by
    running the agent's composed assignment + update Terms to convergence. Returns
    a list of cluster labels (one int per row). LABEL-FREE: M carries no truth.

    Mechanical I/O: build a Clustering root with k Centroid nodes (seeded
    k-means++-style from the data) and one Token node per row (band attrs); then
    iterate — evaluate the agent's assignment Term natively to (re)wire each token
    under its nearest centroid, evaluate the agent's per-band update Term natively to
    move each centroid to its members' mean — until assignments stop changing."""
    import numpy as np
    from substrate_rs import Substrate

    M = np.asarray(M, dtype=np.float64)
    n_tokens, n_bands = M.shape
    rng = np.random.default_rng(seed)
    k = min(k, n_tokens)

    s = substrate if substrate is not None else Substrate()
    root = s.add_node("Clustering", {})
    # Token nodes (the unlabelled point cloud).
    tok_ids = []
    for r in range(n_tokens):
        attrs = {f"band{b}": float(M[r, b]) for b in range(n_bands)}
        tok_ids.append(s.add_node("Token", attrs))

    # k-means++ seeding (mechanical init — distance arithmetic only, no labels).
    idx0 = int(rng.integers(n_tokens))
    seeds = [idx0]
    d2 = ((M - M[idx0]) ** 2).sum(axis=1)
    for _ in range(1, k):
        probs = d2 / d2.sum() if d2.sum() > 0 else None
        nxt = int(rng.choice(n_tokens, p=probs)) if probs is not None \
            else int(rng.integers(n_tokens))
        seeds.append(nxt)
        d2 = np.minimum(d2, ((M - M[nxt]) ** 2).sum(axis=1))
    cen_ids = []
    for si in seeds:
        attrs = {f"band{b}": float(M[si, b]) for b in range(n_bands)}
        c = s.add_node("Centroid", attrs)
        s.add_edge_unchecked(root, CENTROID_EDGE, c)
        cen_ids.append(c)

    assign_term = assignment_term(n_bands)
    update_terms = [centroid_update_term(b) for b in range(n_bands)]
    cid_index = {c: i for i, c in enumerate(cen_ids)}

    labels = [-1] * n_tokens
    for _ in range(n_iters):
        # --- assignment: evaluate the agent's Argmin Term for every token. ---
        new_members = {c: [] for c in cen_ids}
        new_labels = []
        for r, t in enumerate(tok_ids):
            chosen = s.evaluate(assign_term, {"t": t, "root": root})
            ci = chosen if chosen in cid_index else cen_ids[0]
            new_members[ci].append(t)
            new_labels.append(cid_index[ci])
        # rewire has_member edges so the update Term sees the new assignment.
        for c in cen_ids:
            for old in list(s.neighbours(c, MEMBER_EDGE)):
                s.remove_edge(c, MEMBER_EDGE, old)
            for t in new_members[c]:
                s.add_edge_unchecked(c, MEMBER_EDGE, t)
        # --- update: evaluate the agent's mean Term per band per centroid. ---
        for c in cen_ids:
            if not new_members[c]:
                continue   # empty cluster keeps its position (standard Lloyd)
            for b in range(n_bands):
                mu = s.evaluate(update_terms[b], {"k": c})
                s.set_attr(c, f"band{b}", float(mu))
        if new_labels == labels:
            break
        labels = new_labels
    return labels


__all__ = ["squared_distance_term", "assignment_term", "centroid_update_term",
           "compose_cross_speaker_clustering", "cluster", "MEMBER_EDGE",
           "CENTROID_EDGE"]
