"""discriminable_units — the agent builds a CROSS-SPEAKER DISCRIMINABLE sub-word
INVENTORY (the broken alphabet), composed ENTIRELY from its OWNED pieces.

THE PROBLEM (measured: sublexical_composition tied/lost vs shuffle). Sub-lexical
composition (words as unit-SEQUENCE spellings over a 32-unit inventory) scored at
SHUFFLE level — permuting the spellings barely changed the score, so the recovered
spellings DO NOT carry word identity. The composition IDEA is sound (small shared
inventory -> unbounded vocab); the ALPHABET is broken: the sub-word UNITS are too
confusable cross-speaker, so a test chunk lands on the WRONG unit and the spelling
degrades into noise.

THE FIX — three principled levers the agent resolves with its COMPRESSION/COHERENCE
selector (each composed from owned pieces, NOTHING rebuilt):

  LEVER 1 — CONTEXT / GRANULARITY (the compression tradeoff).
    Short ~3-frame chunks carry too little context to be invariant cross-speaker.
    The agent's OWNED dissimilarity segmenter already has a DURATION PENALTY (DPDP,
    min_sep): raising min_sep MERGES the shallower of two nearby change-rate peaks,
    yielding fewer, LONGER, syllable/diphone-scale spans that carry more context ->
    more discriminable. BUT longer = fewer-per-word = less shareable. The right
    granularity is the COMPRESSION point: units DISCRIMINABLE enough to read AND
    RECURRING enough to share. The agent SELECTS min_sep by its selector (below),
    not by sweeping accuracy.

  LEVER 2 — CLUSTER ON THE DECISION SPACE (coherent quantization).
    The OLD path clustered on mean(rs, axis=0) — a single mean-pooled point — yet the
    recognition DECISION is native DtwTo over the FULL relational TRAJECTORY. Cluster
    space != decision space: two chunks the DtwTo decision calls different get merged
    into one unit (and vice-versa), so the quantizer is incoherent with the reader.
    The agent's coherent quantizer clusters on a PHASE-ANCHORED summary that PRESERVES
    the trajectory's temporal shape (the relational shape sampled at K fixed
    proportional phases, flattened) — the same phase-anchor structure relational_shape
    already uses for its self-similarity row. Now the cluster carves where DtwTo reads.

  LEVER 3 — CATEGORICAL INVENTORY BY CROSS-SPEAKER CONSISTENCY (sharp boundaries).
    Raw k-means medoids keep ALL k units regardless of whether they QUANTIZE CLEANLY
    cross-speaker. The agent's OWNED categorical_perception says a real category has a
    SHARP, RELIABLE boundary. So the agent SELECTS the inventory by cross-speaker
    CONSISTENCY: split the TRAIN speakers into two disjoint halves, quantize each
    half's chunks, and KEEP only the units that are reliably hit from BOTH halves
    (a unit that only one speaker-half ever lands on is a speaker artefact, not a
    shared category). Confusable / speaker-private units are DROPPED; their chunks
    re-quantize onto the surviving discriminable units. This is categorical
    sharpening lifted to the INVENTORY level — keep the categories that close
    cross-speaker, discard the blurry ones.

THE SELECTOR (compression + coherence, NOT accuracy — donkey-clean). For a candidate
inventory the agent scores, with NO label and NO accuracy:
    coherence = mean over held-half chunks of the quantization MARGIN
                (gap between nearest-unit DtwTo distance and 2nd-nearest), normalised
                — high margin = each token lands CLEANLY in one unit (the quantizer
                CLOSES), the same coherence that made the relational whole-word rank
                win.  A blurry inventory has tokens equidistant to several units
                (margin ~ 0); a discriminable one has each token decisively in one.
The agent picks the (granularity, inventory) with the best coherence selector. This is
the compression objective (clean quantization = short codes), never a tuned gain.

DISCIPLINE (CLAUDE.md): world adapter only — it SEQUENCES the agent's owned graph-
resident machinery (segmenter Term / relational decoder Terms / k-means-as-graph-Term /
native DtwTo) and lays signals out at the I/O boundary. NO .fit/net/sweep/loss. The
recognition / quantization DECISIONS are native substrate.evaluate. Inventory is
label-free; consistency uses only the train-speaker SPLIT, never the word label.
"""
from __future__ import annotations

import numpy as np

from substrate_rs import Substrate
import domains.recognition_graph as RG
from domains.relational_shape import relational_shape
from domains.dissimilarity_segmentation import find_peak_boundaries, chunk_by_peaks
from domains.cross_speaker_clustering import cluster


# ---------------------------------------------------------------------------
# I/O helpers.
# ---------------------------------------------------------------------------

def _clean2d(M):
    """Coerce a trajectory to a rectangular frames x D float32 array, or None if it
    cannot be made rectangular (degenerate/ragged chunk to be skipped)."""
    A = np.asarray(M, dtype=object) if not isinstance(M, np.ndarray) else M
    try:
        A = np.asarray(M, dtype=np.float32)
    except (ValueError, TypeError):
        return None
    if A.dtype == object:
        return None
    if A.ndim == 1:
        A = A[:, None]
    if A.ndim != 2 or A.shape[0] < 1 or A.shape[1] < 1:
        return None
    return A


def _as_tuple(M):
    A = _clean2d(M)
    if A is None:
        return ((0.0,),)
    return tuple(tuple(float(v) for v in row) for row in A)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ---------------------------------------------------------------------------
# LEVER 1+2 — chunk a word into syllable-scale spans (owned segmenter, larger
# min_sep) and represent each by the owned coherent decoder. Returns the list of
# (full relational trajectory, phase-anchored cluster summary) per chunk.
# ---------------------------------------------------------------------------

def _phase_anchored_summary(rs, n_phase: int):
    """Fixed-D cluster summary that PRESERVES the trajectory's temporal shape:
    sample the relational-shape trajectory at n_phase fixed proportional phases and
    flatten. Same phase-anchor structure relational_shape's self-similarity row uses.
    This is the coherent quantizer's point — the cluster space now matches the
    native-DtwTo decision space (a trajectory, not a single mean)."""
    A = _clean2d(rs)
    if A is None:
        return None
    T = A.shape[0]
    if T == 1:
        idx = [0] * n_phase
    else:
        idx = [min(T - 1, int(round(k * (T - 1) / (n_phase - 1))))
               for k in range(n_phase)] if n_phase > 1 else [T // 2]
    return A[idx].reshape(-1)


def word_chunks(seg_sub, M_band, seq_tag, n_anchors, min_sep, n_phase):
    """One word's band trajectory -> syllable-scale sub-word chunks (owned
    dissimilarity-peak segmenter at the given min_sep granularity), each as
    (full relational trajectory, phase-anchored cluster summary). Native segmenter,
    native relational decoder."""
    cuts, _d = find_peak_boundaries(seg_sub, M_band, seq_tag, min_sep=min_sep,
                                    smooth=1, metric="cosine", gate="prominent")
    blocks = chunk_by_peaks(M_band, cuts)
    out = []
    for block, n in blocks:
        if n < 2:
            continue
        rs = relational_shape(block, n_anchors=n_anchors)
        if rs is not None and len(rs) >= 2:
            rsc = _clean2d(rs)
            su = _phase_anchored_summary(rs, n_phase) if rsc is not None else None
            if rsc is not None and su is not None:
                out.append((rsc, su))
    if not out:                                   # degenerate: whole word as one chunk
        rs = relational_shape(M_band, n_anchors=n_anchors)
        rsc = _clean2d(rs) if rs is not None else None
        if rsc is not None and len(rsc) >= 2:
            su = _phase_anchored_summary(rsc, n_phase)
            if su is not None:
                out = [(rsc, su)]
    return out


# ---------------------------------------------------------------------------
# Native chunk -> nearest-unit quantizer (DtwTo over the relational trajectory),
# returning (unit_id, margin). Margin = (d2 - d1) / (d2 + eps): how DECISIVELY the
# chunk lands in its nearest unit vs the 2nd-nearest. High = clean quantization.
# ---------------------------------------------------------------------------

class Quantizer:
    """Native sub-chunk -> nearest-unit DtwTo quantizer over an inventory of unit
    exemplar trajectories. The DECISION is substrate.evaluate (native DtwTo)."""

    def __init__(self, unit_ids, unit_traj):
        self.sub = Substrate()
        self.sign = self.sub.add_node("ChunkSign", {})
        self.unit_ids = list(unit_ids)
        self.unit_nodes = []
        for u, traj in zip(unit_ids, unit_traj):
            un = self.sub.add_node("Unit", {"uid": int(u)})
            self.sub.set_attr(un, "rep", _as_tuple(traj))
            self.unit_nodes.append((int(u), un))
        self.dtw = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                                   RG._Attr(RG._V("w"), "rep")))

    def quantize(self, rs):
        """-> (best_unit_id, margin). margin in [0,1]: decisiveness of the assignment
        (gap to 2nd-nearest, normalised). A clean quantizer has high margin."""
        self.sub.set_attr(self.sign, "rep", _as_tuple(rs))
        ds = []
        for u, un in self.unit_nodes:
            d = self.sub.evaluate(self.dtw, {"s": self.sign, "w": un})
            ds.append((d, u))
        ds.sort()
        if len(ds) == 1:
            return ds[0][1], 1.0
        d1, u1 = ds[0]
        d2, _ = ds[1]
        margin = (d2 - d1) / (d2 + 1e-9) if d2 > 0 else 0.0
        return u1, float(margin)

    def teardown(self):
        # let GC reclaim the substrate
        self.sub = None


# ---------------------------------------------------------------------------
# Inventory construction with the three levers + the coherence selector.
# ---------------------------------------------------------------------------

def _kmeans_inventory(train_chunks, k_units, seed=0):
    """Raw k-means inventory over the PHASE-ANCHORED summaries (lever 2). Returns
    (unit_ids, unit_traj) where each unit's exemplar is the medoid's FULL relational
    trajectory. Owned k-means-as-graph-Term, label-free."""
    flat_traj = [rs for chs in train_chunks for (rs, _su) in chs]
    flat_sum = np.stack([su for chs in train_chunks for (_rs, su) in chs])
    clu = Substrate()
    labels = cluster(flat_sum, k_units, n_iters=25, seed=seed, substrate=clu)
    del clu
    unit_ids, unit_traj = [], []
    for lab in sorted(set(labels)):
        idx = [i for i, l in enumerate(labels) if l == lab]
        cen = flat_sum[idx].mean(axis=0)
        d = [((flat_sum[i] - cen) ** 2).sum() for i in idx]
        medoid_i = idx[int(np.argmin(d))]
        unit_ids.append(lab)
        unit_traj.append(flat_traj[medoid_i])
    return unit_ids, unit_traj


def _consistency_select(unit_ids, unit_traj, chunks_a, chunks_b, min_margin=0.0):
    """LEVER 3 — keep only units that are RELIABLY HIT from BOTH disjoint train-speaker
    halves (a unit only one half ever lands on is a speaker artefact, not a shared
    category). chunks_a / chunks_b are the two halves' chunk lists. A unit survives if
    it is the nearest unit for at least one chunk in EACH half (with margin >=
    min_margin — a clean, not blurry, hit). Returns the surviving (unit_ids,
    unit_traj). Label-free: uses only the speaker split, never the word."""
    q = Quantizer(unit_ids, unit_traj)
    hit_a, hit_b = set(), set()
    for chs in chunks_a:
        for (rs, _su) in chs:
            u, m = q.quantize(rs)
            if m >= min_margin:
                hit_a.add(u)
    for chs in chunks_b:
        for (rs, _su) in chs:
            u, m = q.quantize(rs)
            if m >= min_margin:
                hit_b.add(u)
    q.teardown()
    survivors = hit_a & hit_b
    keep = [(u, t) for u, t in zip(unit_ids, unit_traj) if u in survivors]
    if not keep:                                  # never empty the inventory
        keep = list(zip(unit_ids, unit_traj))
    ids = [u for u, _ in keep]
    traj = [t for _, t in keep]
    return ids, traj


def coherence_score(unit_ids, unit_traj, held_chunks):
    """THE SELECTOR (compression/coherence, NO label, NO accuracy). Mean quantization
    MARGIN over held-out-half chunks: how cleanly each token lands in one unit. High =
    the quantizer CLOSES (each token decisively in one unit) = discriminable inventory.
    A blurry inventory has tokens equidistant to several units (margin ~ 0)."""
    q = Quantizer(unit_ids, unit_traj)
    margins = []
    for chs in held_chunks:
        for (rs, _su) in chs:
            _u, m = q.quantize(rs)
            margins.append(m)
    q.teardown()
    return float(np.mean(margins)) if margins else 0.0


def build_discriminable_inventory(train_chunks_by_half, k_units, seed=0,
                                  consistency=True, log=lambda *a: None):
    """The agent builds the discriminable inventory: k-means over the phase-anchored
    summaries (lever 1+2 already applied in chunking), then categorical consistency
    selection (lever 3) across the two disjoint train-speaker halves. Returns
    (unit_ids, unit_traj, coherence) — coherence is the selector value on the held
    half (B), for the agent to compare granularities. Label-free throughout."""
    chunks_a, chunks_b = train_chunks_by_half
    all_chunks = chunks_a + chunks_b
    unit_ids, unit_traj = _kmeans_inventory(all_chunks, k_units, seed=seed)
    log(f"    raw k-means: {len(unit_ids)} units")
    if consistency:
        unit_ids, unit_traj = _consistency_select(unit_ids, unit_traj,
                                                  chunks_a, chunks_b)
        log(f"    cross-speaker-consistent: {len(unit_ids)} units survive")
    coh = coherence_score(unit_ids, unit_traj, chunks_b)
    log(f"    coherence (held-half mean margin): {coh:.4f}")
    return unit_ids, unit_traj, coh


__all__ = [
    "word_chunks", "Quantizer", "coherence_score",
    "build_discriminable_inventory", "_phase_anchored_summary",
    "_kmeans_inventory", "_consistency_select",
]
