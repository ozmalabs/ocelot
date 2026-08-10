"""dissimilarity_segmentation — the agent forward-builds the SOTA unsupervised
boundary cue from its OWN order_n_concepts primitive: a word boundary is where the
REPRESENTATION CHANGES FASTEST.

THE PRINCIPLE (Kamper 2024-25, unsupervised segmentation). The strongest
unsupervised word/phone boundary cue is the prominence PEAK of the frame-to-frame
DISSIMILARITY curve: between two adjacent frames inside a steady phone the feature
vector barely moves (low dissimilarity); at a boundary the vector changes fast
(high dissimilarity). A boundary is a LOCAL MAXIMUM of that change-rate.

THIS IS THE AGENT'S OWN order_n_concepts, READ FORWARD. The frame-to-frame
dissimilarity d[t] = dist(M[t], M[t-1]) is the order-1-time FINITE DIFFERENCE of
the feature trajectory (its magnitude). A prominence peak of d is a LOCAL MAXIMUM
— an order-1 SIGN-CHANGE of d itself (d stops rising and starts falling):
d[t] > d[t-1] AND d[t] > d[t+1]. The agent already holds order-N finite differences
(domains/order_n_concepts: nth_order_terms) and the order-1 sign-change boundary
move (forward_segmentation.local_min_boundary_term on TP troughs;
landmark_segmentation.syllable_boundary_term on energy valleys). This is the SAME
move applied to the right carrier — the CHANGE-RATE of the invariant features —
which the SOTA literature identifies as the best unsupervised boundary cue.

WHY IT BEATS TP-TROUGHS / ENERGY-VALLEYS. TP troughs read off a jittery codebook
stream (move with coarticulation). Energy valleys catch sonority constrictions but
MISS boundaries between two voiced segments at similar energy (vowel-vowel, liaison)
and FIRE on intra-word sonority dips. The dissimilarity peak fires exactly where the
SPECTRUM RECONFIGURES — the acoustic definition of a segment boundary — regardless
of absolute energy or which codebook unit a frame lands in.

GRAPH-RESIDENT BOUNDARY RULE (architecture rule). The boundary DECISION is a Term
the agent owns and evaluates natively, mirroring forward_segmentation /
landmark_segmentation. Each inter-frame transition becomes a DissimFrame node
carrying its dissimilarity `d` and its order-adjacent neighbours `prev_d` / `next_d`;
the boundary set is

    Filter(DissimFrame[seq], f,
           And( Gt(f.d, f.prev_d),       # rising into f ...
                Gt(f.d, f.next_d),       # ... then falling out of f  (a PEAK)
                Gt(f.d, mean_d) ))       # prominent (above the utterance's mean)

— "the frames where the representation's change-rate is a LOCAL MAXIMUM and is
above this utterance's mean change-rate (a prominent peak, not change ripple)". The
mean-d gate is a statistic OF the dissimilarity curve (derived, never swept), the
direct dual of landmark_segmentation's mean-energy regime split.

Optional DURATION PENALTY (DPDP, Kamper): prefer word-scale spans by dropping the
SHALLOWER of two peaks closer than `min_sep` frames — a structural minimum-duration
constraint (the same min-separation merge the landmark chunker uses), not a tuned
score.

World-adapter + the agent's segmenter: translates the frame matrix into the
DissimFrame structure and evaluates the agent's boundary Term; chunk assembly is
mechanical. No agent reasoning in Python beyond that translation. No tuning; the
probe reports within-speaker consistency before/after, shuffle-controlled.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# (0) The agent specifies the dissimilarity-peak segmenter by reasoning FROM its
# order_n_concepts (order-1 finite difference = change-rate) to the SOTA boundary
# cue. Records a graph-resident spec (the same move as agent_specify_segmenter /
# agent_specify_landmark_segmenter).
# ---------------------------------------------------------------------------

def agent_specify_dissimilarity_segmenter(substrate) -> dict:
    """The agent reasons from order_n_concepts (the order-1-time finite difference
    of its feature trajectory IS the frame-to-frame change-rate) to the SOTA
    unsupervised boundary cue: a boundary is a prominence PEAK of that change-rate
    (an order-1 sign-change of the dissimilarity curve). Records a graph-resident
    DissimilaritySegmenterSpec. Names WHAT determines a boundary, not a knob."""
    has_order_n = any(
        substrate.node(n)["attrs"].get("name") in
        ("order_n_concepts", "finite_difference", "order_1_time")
        for n in substrate.nodes("Concept"))
    spec = {
        "name": "DissimilarityPeakSegmenter",
        "principle": "frame_to_frame_dissimilarity_prominence_peak",
        "boundary_rule": (
            "place a boundary at frame f iff d[f] (the frame-to-frame "
            "dissimilarity = magnitude of the order-1-time finite difference of "
            "the invariant features) is a LOCAL MAXIMUM (d[f] > d[f-1] and "
            "d[f] > d[f+1]) AND is above this utterance's mean dissimilarity"),
        "carrier": "order_1_time_finite_difference_of_invariant_features",
        "is_order1_sign_change_of_changerate": True,
        "level_source": "mean_dissimilarity_over_this_utterance",
        "level_is_searched": False,
        "why": (
            "inside a steady segment adjacent frames barely move (low change-"
            "rate); at a boundary the spectrum reconfigures (high change-rate). "
            "A boundary is therefore a prominence PEAK of the change-rate curve. "
            "This is my own order-1-time finite difference (order_n_concepts) read "
            "forward — the SOTA unsupervised boundary cue (Kamper) — applied to the "
            "change-rate of my invariant features rather than to a jittery codebook "
            "TP stream or to absolute energy."),
        "grounded_in_order_n": bool(has_order_n),
        "duration_penalty": "drop shallower of two peaks closer than min_sep (DPDP)",
        "is_forward_construction": True,
        "is_search": False,
    }
    try:
        substrate.add_node("DissimilaritySegmenterSpec",
                           {**{k: v for k, v in spec.items()
                               if isinstance(v, (str, bool, int, float))},
                            "origin": "agent_dissimilarity_segmentation"})
    except Exception:
        pass
    return spec


# ---------------------------------------------------------------------------
# (1) The structure: the frame-to-frame dissimilarity curve = the magnitude of the
# order-1-time finite difference of the feature trajectory. Pure mechanical
# translation of the perceived features into a 1-D change-rate curve.
# ---------------------------------------------------------------------------

def dissimilarity_curve(M, metric="cosine", smooth=1) -> np.ndarray:
    """Frame-to-frame dissimilarity d[t] = dist(M[t], M[t-1]) for t=1..T-1; d[0] is
    set to 0 (no preceding frame). d is the magnitude of the agent's order-1-time
    finite difference of the feature trajectory. metric in {cosine, euclidean}.
    A light moving average (smooth frames each side) removes single-frame ripple so
    a genuine boundary peak is not split — the front-end's own frame grain, not a
    tuned knob."""
    arr = np.asarray(M, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[None, :]
    T = arr.shape[0]
    d = np.zeros(T, dtype=np.float64)
    if T < 2:
        return d
    diff = arr[1:] - arr[:-1]                      # order-1-time finite difference
    if metric == "cosine":
        a = arr[1:]
        b = arr[:-1]
        na = np.linalg.norm(a, axis=1)
        nb = np.linalg.norm(b, axis=1)
        dot = np.sum(a * b, axis=1)
        cos = dot / np.maximum(na * nb, 1e-9)
        d[1:] = 1.0 - cos                          # cosine distance of adjacent frames
    else:
        d[1:] = np.linalg.norm(diff, axis=1)       # euclidean magnitude
    if smooth > 0 and T > 2 * smooth + 1:
        k = 2 * smooth + 1
        pad = np.pad(d, (smooth, smooth), mode="edge")
        d = np.convolve(pad, np.ones(k) / k, mode="valid")
    return d


# ---------------------------------------------------------------------------
# (2) The boundary DECISION as a graph-resident Term the agent OWNS. Each frame
# becomes a DissimFrame node carrying d / prev_d / next_d; the boundary set is a
# Filter Term the agent evaluates natively. Mirrors landmark_segmentation's
# valley_boundary_term, with PEAKS (Gt) instead of valleys (Lt).
# ---------------------------------------------------------------------------

def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _And(items): return {"type": "And", "items": list(items)}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _Filter(src, var, pred): return {"type": "Filter", "source": src,
                                     "var_name": var, "predicate": pred}


class _Pred:
    """Tiny Term wrapper so substrate.evaluate (which unwraps `._json`) accepts a
    raw JSON Term dict — the same shim recognition_graph / forward_segmentation /
    landmark_segmentation use."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def peak_boundary_term(seq_tag: str) -> dict:
    """The graph-resident PEAK boundary RULE: EVERY local maximum of the
    dissimilarity (change-rate) curve (no prominence gate). The agent's order-1
    sign-change concept on the change-rate curve.

        Filter(DissimFrame[seq], f, And( Gt(f.d, f.prev_d), Gt(f.d, f.next_d) ))
    """
    f = _V("f")
    return _Filter(
        _NodesWhere("DissimFrame", "seq", _Lit(seq_tag)),
        "f",
        _And([_Gt(_Attr(f, "d"), _Attr(f, "prev_d")),
              _Gt(_Attr(f, "d"), _Attr(f, "next_d"))]))


def prominent_peak_boundary_term(seq_tag: str, mean_d: float) -> dict:
    """The graph-resident PROMINENT-PEAK boundary RULE: the DissimFrame nodes that
    are LOCAL MAXIMA of the change-rate curve AND sit ABOVE this utterance's mean
    change-rate (a prominent peak, not change ripple).

        Filter(DissimFrame[seq], f,
               And( Gt(f.d, f.prev_d), Gt(f.d, f.next_d),    # order-1 peak
                    Gt(f.d, mean_d) ))                       # prominent

    `mean_d` is the mean dissimilarity over this utterance — a statistic OF the
    change-rate curve, derived, not searched (the direct dual of landmark_
    segmentation's mean-energy regime split). A genuine boundary reconfigures the
    spectrum (change-rate above the mean); ripple inside a steady segment does not."""
    f = _V("f")
    return _Filter(
        _NodesWhere("DissimFrame", "seq", _Lit(seq_tag)),
        "f",
        _And([_Gt(_Attr(f, "d"), _Attr(f, "prev_d")),
              _Gt(_Attr(f, "d"), _Attr(f, "next_d")),
              _Gt(_Attr(f, "d"), _Lit(float(mean_d)))]))


def _install_dissim_frames(substrate, d, seq_tag: str) -> list:
    """Translate one utterance's dissimilarity curve into graph DissimFrame nodes
    carrying the peak structure the boundary Term reads (mechanical I/O->graph). For
    each frame: its change-rate `d` and its order-adjacent neighbours
    `prev_d`/`next_d` (endpoints get a sentinel LOW so an endpoint never reads as a
    local maximum). Returns the ordered DissimFrame NodeIDs."""
    n = len(d)
    SENTINEL = -1e9
    nodes = []
    for i in range(n):
        t = substrate.add_node("DissimFrame", {
            "seq": seq_tag, "pos": i,
            "d": float(d[i]),
            "prev_d": float(d[i - 1]) if i > 0 else SENTINEL,
            "next_d": float(d[i + 1]) if i + 1 < n else SENTINEL,
            "origin": "dissimilarity_segmentation"})
        nodes.append(t)
    return nodes


def find_peak_boundaries(substrate, M, seq_tag: str,
                         min_sep: int = 3, smooth: int = 1,
                         metric: str = "cosine", gate: str = "prominent") -> tuple:
    """The agent finds this utterance's boundaries by EVALUATING its dissimilarity-
    peak boundary Term over the DissimFrame structure — natively, in the substrate.
    Returns (cut_positions, dissimilarity_curve). A cut at position i places a
    boundary BEFORE frame i (the spectrum reconfigures entering frame i), so frame i
    starts a new chunk.

    gate="prominent" keeps only peaks above the utterance's mean change-rate (the
    derived prominence gate); gate="all" cuts at every change-rate local maximum.
    `min_sep` (DPDP duration penalty) drops the SHALLOWER of two peaks closer than
    min_sep frames — a structural minimum-duration constraint, not a tuned score."""
    d = dissimilarity_curve(M, metric=metric, smooth=smooth)
    n = len(d)
    if n < 5:
        return set(), d
    frame_ids = _install_dissim_frames(substrate, d, seq_tag)
    if gate == "all":
        term = peak_boundary_term(seq_tag)
    else:
        term = prominent_peak_boundary_term(seq_tag, float(d.mean()))
    peak_nodes = substrate.evaluate(_Pred(term), None)
    cuts = sorted(int(substrate.node(t)["attrs"].get("pos", -1))
                  for t in peak_nodes)
    cuts = [c for c in cuts if 0 < c < n]
    # Per-clip scratch is transient: the DissimFrame nodes exist ONLY to carry the
    # peak structure for this one evaluate; their `pos` values are now read out into
    # `cuts`. Free them so a caller-reused substrate does not accumulate one clip's
    # frames forever (the unbounded node growth that OOM-killed the long runs). This
    # does not change the computed result — the nodes are dead after this point.
    for fid in frame_ids:
        substrate.remove_node(fid)
    # min-separation (DPDP): keep the DEEPER (higher-d) peak when two are too close.
    if min_sep > 1 and cuts:
        kept = []
        for c in cuts:
            if kept and c - kept[-1] < min_sep:
                if d[c] > d[kept[-1]]:        # keep the more prominent peak
                    kept[-1] = c
            else:
                kept.append(c)
        cuts = kept
    return set(cuts), d


# ---------------------------------------------------------------------------
# (3) Assemble real-frame chunk blocks from the peak boundaries (mechanical). A cut
# at position i starts a new chunk at frame i (the boundary is BEFORE the high-
# change frame). Returns [(frame_block, n_frames)] like the other chunkers.
# ---------------------------------------------------------------------------

def chunk_by_peaks(M, cuts) -> list:
    n = M.shape[0]
    if not cuts:
        return [(M, n)]
    blocks = []
    start = 0
    for c in sorted(cuts):
        if c - start >= 1:
            blocks.append((M[start:c], c - start))
            start = c
    if start < n:
        blocks.append((M[start:], n - start))
    return blocks if blocks else [(M, n)]


def dissimilarity_chunk_utterance(substrate, M, seq_tag: str,
                                  min_sep: int = 3, smooth: int = 1,
                                  metric: str = "cosine",
                                  gate: str = "prominent") -> list:
    """One utterance's frame matrix -> list of (frame_block, n_frames), with chunk
    boundaries anchored to the agent's dissimilarity-peak landmarks (found by the
    graph-resident boundary Term). Drop-in replacement for chunk_with_corpus_tp /
    landmark_chunk_utterance."""
    cuts, _d = find_peak_boundaries(substrate, M, seq_tag, min_sep=min_sep,
                                    smooth=smooth, metric=metric, gate=gate)
    return chunk_by_peaks(M, cuts)


__all__ = [
    "agent_specify_dissimilarity_segmenter",
    "dissimilarity_curve",
    "peak_boundary_term",
    "prominent_peak_boundary_term",
    "find_peak_boundaries",
    "chunk_by_peaks",
    "dissimilarity_chunk_utterance",
]
