"""distributional_categories — the agent composes LABEL-FREE, TOLD-k-FREE category
formation from the SHAPE of a cue distribution: categories are the MODES, carved at
the VALLEYS between modes. Number AND location emerge from the data (bimodal -> 2,
unimodal -> 1). NO told-k.

WHY this is the agent's to compose, and why it is NEW over cross_speaker_clustering.
The agent PICKED unsupervised clustering as its frontier (gap_prioritiser: it unifies
82 of the agent's own held postulates — the most of any gap). The keystone postulate
it unified, distributional_learning_of_categories, states it verbatim:

    "The SHAPE of the input distribution along a phonetic cue determines categories:
     a bimodal distribution yields two categories, a unimodal one yields one ...
     carved at the VALLEYS between modes in the ambient distribution."

The agent's prior clustering (domains/cross_speaker_clustering) is k-means: it is
TOLD k (= #digits) and only finds centroids. It cannot say HOW MANY categories the
distribution has. This capability removes the told-k: the count of categories is the
count of density MODES the data exhibits — exactly the postulate's claim.

THE COMPOSITION (graph Term-trees, evaluated natively — NO Python arithmetic). This
is the agent's OWN order-N peak (order_n_concepts: a peak = a local maximum, the
order-2 curvature<0 point) lifted from "spectral envelope over FREQUENCY" to
"DENSITY over the cue space":

  density(t)   = Count( Neighbours(t, "near") )
                 the local data density at token t = how many tokens lie within the
                 kernel radius (the same Count-over-an-edge-set the clusterer's
                 centroid mean uses, here counting the local point cloud).

  climb(t)     = Argmax_{u in near(t)+{t}} density(u)
                 ONE mean-shift / hill-climb step: move t to its DENSEST neighbour.
                 Iterated to a fixed point, every token flows UP to a density MODE;
                 the distinct fixed points ARE the categories (their COUNT emergent,
                 their location at the modes, valleys between them left unvisited).

Primitives used (ALL already held — NO new primitive): Count, Neighbours, Argmax,
Attr, Var, Plus, Minus, Times. The "near" edge set is a mechanical I/O translation
(connect tokens within radius r); the climb + density are the agent's composed Terms,
run on the substrate evaluator. The radius r is the data's OWN scale (median nearest-
neighbour distance) — derived, not swept; compression is the selector, never a search.

VERIFICATION is the agent's own controls (the probe): the recovered #modes vs the
true #categories; purity vs the random floor; and the SHUFFLE control — destroy the
distribution's structure (shuffle each cue dimension independently across tokens,
keeping the marginals) and the mode-count / purity collapses, proving the categories
live in the JOINT distribution's modes, not in the marginals.

See [[ozma_order_n_concepts]] (the peak lifted to density) / [[ozma_agent_builds_pairwise]]
/ [[ozma_speaker_normalization]] / domains/cross_speaker_clustering (the told-k sibling).
"""
from __future__ import annotations

from substrate_rs import Attr, Var, Count, Neighbours, Argmax

NEAR_EDGE = "near"     # token -> tokens within the kernel radius (incl. a self-loop)


def density_term():
    """density(t) = Count(Neighbours(t, "near")). Evaluated with env {"t": token};
    the local data density (kernel count) at t. A graph Term-tree — the agent's
    own Count-over-an-edge-set, here over the local point cloud."""
    return Count(Neighbours(Var("t"), NEAR_EDGE))


def climb_term():
    """climb(t) = Argmax_{u in near(t)} density(u). Evaluated with env {"t": token};
    returns the densest token in t's neighbourhood — ONE mean-shift step toward a
    mode. (near(t) includes a self-loop, so a token already at a local max maps to
    itself = a fixed point = a recovered category.) Pure graph composition: Argmax
    over Neighbours of the Count-density Term, the agent's order-N peak as a flow."""
    nbrs = Neighbours(Var("t"), NEAR_EDGE)
    return Argmax(source=nbrs, var_name="t",
                  value=Count(Neighbours(Var("t"), NEAR_EDGE)),
                  default=Var("t"))


def compose_distributional_categories(substrate) -> list:
    """Record the agent's composed Terms (density + climb) as Concepts it owns — the
    same authoring move as compose_cross_speaker_clustering. Returns [(id, name)]."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "distributional_categories"}
    created = []
    specs = [("dc_density", density_term()), ("dc_climb", climb_term())]
    for name, term in specs:
        if name in existing:
            continue
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "distributional_categories",
            "predicate": term.to_dict(), "origin": "phonology",
            "composed_by": "agent",
            "science": "categories are the MODES of the cue distribution, carved at "
                       "the valleys between modes; number+location emergent, NO "
                       "told-k (distributional_learning_of_categories)"})
        created.append((c, name))
    return created


# ---------------------------------------------------------------------------
# I/O boundary: lay the token cloud out as a graph, wire the radius-r "near"
# edges (mechanical), then RUN the agent's composed density + climb Terms to a
# fixed point. The ONLY Python is the mechanical translation + the radius (the
# data's own median nearest-neighbour scale). No label read; no decision over
# graph state. The arithmetic is the substrate evaluator's.
# ---------------------------------------------------------------------------

def _kernel_radius(M, pctile=20.0, sample=300, seed=0):
    """The data's OWN scale for the density kernel: the `pctile`-th percentile of the
    pairwise-distance distribution over a sample. This is the distance at which the
    distribution starts to look smooth/connected — derived from the data's geometry,
    NOT a swept hyperparameter. (The 20th percentile spans a mode's own width while
    leaving the valleys between modes empty, so the modes stay distinct.)"""
    import numpy as np
    M = np.asarray(M, dtype=np.float64)
    n = M.shape[0]
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=min(sample, n), replace=False)
    S = M[idx]
    D = np.sqrt(((S[:, None, :] - S[None, :, :]) ** 2).sum(-1))
    pos = D[D > 0]
    return float(np.percentile(pos, pctile)) if pos.size else 1.0


def cluster_by_modes(M, pctile=10.0, n_iters=60, seed=0, substrate=None, dist=None):
    """Form categories by mode-seeking, TOLD-k-FREE. Returns (labels, n_modes):
    one integer label per row (the mode it flowed to) and the EMERGENT number of
    modes. LABEL-FREE: M carries no truth.

    Mechanical I/O: build a Token node per row; wire `near` edges between tokens
    within radius = the `pctile`-th percentile of the data's own pairwise-distance
    distribution (its native scale — see _kernel_radius), plus a self-loop per token.
    Then iterate the agent's composed climb Term natively: each token's pointer moves
    to the densest token in its neighbourhood; repeat until pointers stop moving
    (fixed points = modes). The density at every step is the agent's composed Count
    Term, evaluated. NO told-k: n_modes is whatever the distribution's modes give."""
    import numpy as np
    from substrate_rs import Substrate

    M = np.asarray(M, dtype=np.float64)
    n_tokens, n_bands = M.shape
    # `dist`: an optional precomputed n×n distance matrix (e.g. DTW over trajectories) — the same
    # mean-shift mode-seeking with a non-Euclidean kernel, the agent's operator distance-agnostic.
    if dist is not None:
        D = np.asarray(dist, dtype=np.float64)
        pos = D[np.triu_indices(n_tokens, 1)]
        r = float(np.percentile(pos[pos > 0], pctile)) if pos.size and (pos > 0).any() else 1.0
    else:
        r = _kernel_radius(M, pctile=pctile, seed=seed)

    s = substrate if substrate is not None else Substrate()
    tok_ids = []
    for i in range(n_tokens):
        attrs = {f"band{b}": float(M[i, b]) for b in range(n_bands)}
        tok_ids.append(s.add_node("Token", attrs))

    # Wire radius-r "near" edges (mechanical translation of the kernel) + self-loop.
    # Vectorised distance; only the edge wiring touches the graph.
    for i in range(n_tokens):
        d = D[i] if dist is not None else np.sqrt(((M - M[i]) ** 2).sum(axis=1))
        s.add_edge_unchecked(tok_ids[i], NEAR_EDGE, tok_ids[i])   # self-loop
        for j in np.where(d <= r)[0]:
            if j != i:
                s.add_edge_unchecked(tok_ids[i], NEAR_EDGE, tok_ids[int(j)])

    climb = climb_term()
    # pointer[i] = the token row i currently flows to. Iterate the agent's climb.
    pointer = list(range(n_tokens))
    id_to_row = {t: i for i, t in enumerate(tok_ids)}
    for _ in range(n_iters):
        moved = False
        new_pointer = list(pointer)
        for i in range(n_tokens):
            cur = tok_ids[pointer[i]]
            nxt = s.evaluate(climb, {"t": cur})
            nxt_row = id_to_row.get(nxt, pointer[i])
            if nxt_row != pointer[i]:
                new_pointer[i] = nxt_row
                moved = True
        pointer = new_pointer
        if not moved:
            break

    # Path-compress: follow each pointer to its fixed point (its mode).
    def root(i):
        seen = set()
        while pointer[i] != i and i not in seen:
            seen.add(i)
            i = pointer[i]
        return i
    modes = [root(i) for i in range(n_tokens)]
    uniq = {m: k for k, m in enumerate(sorted(set(modes)))}
    labels = [uniq[m] for m in modes]
    return labels, len(uniq)


__all__ = ["density_term", "climb_term", "compose_distributional_categories",
           "cluster_by_modes", "NEAR_EDGE"]
