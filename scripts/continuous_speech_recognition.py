"""continuous_speech_recognition — assemble the agent's OWN forward chain into an
end-to-end CONTINUOUS-SPEECH recognizer and score it honestly on LibriSpeech.

This is the pivot off FSDD (isolated digits, saturated ~61%, can show no
structure) to the task the whole forward chain was built for. NOTHING new is
invented here: this script is a WORLD ADAPTER that wires together pieces the
agent already built and reports numbers. No tuning to manufacture a result.

THE CHAIN (all the agent's own builds, all DEFAULT now):
  1. perception      : gammatone band trajectory (band_trajectory_matrix),
                       frames x 32 log-bands, ~50 fps.
  2. invariance      : invariant_transform — VTLN -> CMVN -> predict-remove
                       (domains/invariant_units, the agent's DEFAULT). Speaker-
                       and coarticulation-normalised frame features.
  3. unit formation  : k-means codebook over invariant frames (the unsupervised
                       unit inventory, HuBERT-style) -> per-frame discrete units.
  4. forward chunker : domains/forward_segmentation — TP-trough segmenter turns
                       the unit stream into CHUNKS (word-units). On invariant
                       units chunk->word purity is ~0.84 (chunks are word-like).
  5. grounding       : on a TRAIN split, align each utterance's chunk sequence to
                       its transcript words; build a chunk-prototype -> word
                       LEXICON (chunk prototypes merged by DTW so the same word's
                       chunks map together; each cluster takes its most-frequent
                       aligned word). The transcripts are the teacher — the
                       language-bootstrap step.
  6. recognise       : held-out utterance -> chunks -> nearest chunk-prototype by
                       DTW -> its word -> predicted word sequence.

SCORING: WER + word accuracy vs the transcript, with baselines (chance, unigram =
always the most-frequent word) and the train chunk->word alignment quality.

HONEST: this is NOT a trained ASR. WER will be high in absolute terms. The
question is whether the agent's chain recognises CONTINUOUS speech MEANINGFULLY
above the unigram baseline — i.e. whether the structure-strength the chain was
built for actually shows on the task FSDD could not measure.

Held-out = held-out SPEAKERS (the real speaker-independent test).

Run: python -m scripts.continuous_speech_recognition [n_train] [n_test] \
        [n_speakers] [K]
"""
import os
import re
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import invariant_transform, canonical_log_centroid
from domains.forward_segmentation import forward_segment, estimate_tp, _median
from substrate_rs import Substrate


# --------------------------------------------------------------------------
# I/O + perception helpers (mechanical world-adapter translation).
# --------------------------------------------------------------------------

def words_of(transcript: str):
    return [w for w in re.findall(r"[\w']+", transcript.lower()) if w]


def frames_of(x, fs, fps=25):
    """Per-frame invariant-ready band matrix at ~fps frames/sec (continuous
    speech needs a finer time grid than the 32-frame FSDD path). Returns
    frames x bands. fps=25 keeps utterances tractable for the DTW lexicon while
    staying above the ~10-15 Hz phone rate."""
    n = max(8, min(300, int(len(x) / fs * fps)))
    return band_trajectory_matrix(x, fs, n_frames=n)


def quantize(M, C):
    """Nearest-centroid unit per frame. Returns a list of unit ids."""
    d = ((M[:, None, :] - C[None, :, :]) ** 2).sum(2)
    return list(d.argmin(1))


def kmeans(X, K, iters=20, seed=0):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=min(K, len(X)), replace=False)
    C = X[idx].copy()
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(2)
        a = d.argmin(1)
        newC = np.array([X[a == k].mean(0) if (a == k).any() else C[k]
                         for k in range(len(C))])
        if np.allclose(newC, C):
            C = newC
            break
        C = newC
    return C


# --------------------------------------------------------------------------
# Variable-length DTW over frame matrices — the agent's compare path, but
# allowing chunks of DIFFERENT frame lengths (chunks are word-units, not the
# fixed-length FSDD whole-word path). Banded for speed.
# --------------------------------------------------------------------------

def dtw(A, B, band_frac=0.25):
    na, nb = A.shape[0], B.shape[0]
    if na == 0 or nb == 0:
        return 1e18
    band = max(4, int(band_frac * max(na, nb)))
    INF = 1e18
    prev = [INF] * (nb + 1)
    prev[0] = 0.0
    # standard DTW init: only (0,0) is 0; first row stays INF except via path
    for i in range(1, na + 1):
        cur = [INF] * (nb + 1)
        jl = max(1, i - band)
        jh = min(nb, i + band)
        ai = A[i - 1]
        for j in range(jl, jh + 1):
            d = float(np.linalg.norm(ai - B[j - 1]))
            best = min(prev[j], cur[j - 1], prev[j - 1])
            if best >= INF:
                continue
            cur[j] = d + best
        prev = cur
    return prev[nb] / (na + nb)


# --------------------------------------------------------------------------
# Chunking: invariant frames -> units -> forward chunker -> chunk frame-spans.
# Each chunk's PROTOTYPE is the contiguous block of invariant frames it covers.
# --------------------------------------------------------------------------

def _flat_len(chunk):
    """Number of leaf per-frame units a (possibly nested) chunk spans = frames."""
    if isinstance(chunk, tuple):
        return sum(_flat_len(c) for c in chunk)
    return 1


# Iteration-4: optionally COARSEN the per-frame unit grain (run-length collapse,
# the agent's forward-built fix for the ~7.5 units/word grain iter-3 located) BEFORE
# the TP chunker. Selected by COLLAPSE_MODE env: "none" (default, iter-3 behaviour;
# keeps existing results/tests untouched), "raw_id", or "stability". The collapse
# DECISION is the agent's graph-resident run-start Term (domains/run_length_collapse);
# this is the same mode-threading world-adapter role iter-3's boundary_mode plays.
COLLAPSE_MODE = os.environ.get("COLLAPSE_MODE", "none")
# Use the sharper local-min boundary when coarsening (iter-3's forward-built rule).
_BOUNDARY_MODE = os.environ.get("BOUNDARY_MODE",
                                "local_min" if COLLAPSE_MODE != "none" else "median")

# Iteration-9 (constraint b — over-segmentation): estimate the transitional-
# probability structure across the WHOLE TRAIN CORPUS rather than per-utterance.
# The agent's statistical_learning science (Saffran et al.) reads word boundaries
# off recurrence ACROSS the corpus — a single short utterance has almost no
# recurrence, so per-utterance TP troughs are noise and the chunker over-segments
# (~3.2 chunks/word). With corpus-scale TP the troughs are real word boundaries and
# the SAME forward_segment / local_min boundary Term collapses to ~1.4 chunks/word
# (measured, scripts/iter9_chunkscale_probe). Default off (per-utterance, iter-4
# behaviour) so existing results/tests are untouched.
CORPUS_TP = os.environ.get("CORPUS_TP", "0") == "1"


def coarse_stream_of(sub, M, C):
    """One utterance's invariant frames -> (coarse_unit_ids, per-coarse-unit frame
    lengths). Mechanical: quantise to codebook units, then (if COLLAPSE_MODE set)
    run-length collapse to coarse units. When COLLAPSE_MODE=='none' each frame IS a
    coarse unit (length 1). This is the stream the corpus-TP chunker reads."""
    units = quantize(M, C)
    if COLLAPSE_MODE != "none":
        from domains.run_length_collapse import collapse_stream
        tag = f"csr_{COLLAPSE_MODE}_{id(M) & 0xffffff}"
        col = collapse_stream(sub, units, tag, mode=COLLAPSE_MODE, M=M)
        return col["coarse_ids"], col["lengths"]
    return list(units), [1] * len(units)


def _blocks_from_chunk_lengths(M, frame_lengths, chunk_unit_lengths):
    """Map a chunking expressed in COARSE-UNIT lengths back to contiguous real-frame
    blocks of M. frame_lengths[i] = #frames coarse-unit i spans; chunk_unit_lengths =
    #coarse-units per chunk. Mechanical span assembly (same as chunk_an_utterance)."""
    n_frames = M.shape[0]
    blocks, ui, fi = [], 0, 0
    for cu in chunk_unit_lengths:
        if cu <= 0:
            continue
        fl = max(1, sum(frame_lengths[ui:ui + cu]))
        blocks.append((M[fi:fi + fl], fl))
        ui += cu
        fi += fl
    if fi < n_frames and blocks:
        last_M, last_L = blocks[-1]
        blocks[-1] = (M[fi - last_L:], n_frames - (fi - last_L))
    return blocks if blocks else [(M, n_frames)]


def chunk_with_corpus_tp(sub, M, coarse_ids, frame_lengths, corpus_tp, level, tag):
    """Chunk ONE utterance's coarse-unit stream against a SHARED corpus-scale TP.
    The boundary DECISION stays the agent's graph-resident Term (local_min trough)
    evaluated natively via find_boundaries_via_graph — only the TP it reads is the
    corpus-wide distribution, not this one utterance's. Returns real-frame blocks."""
    from domains.forward_segmentation import find_boundaries_via_graph, chunk_sequence
    if len(coarse_ids) < 2:
        return [(M, M.shape[0])]
    cuts = find_boundaries_via_graph(sub, coarse_ids, corpus_tp, level, tag,
                                     boundary_mode=_BOUNDARY_MODE)
    chunks = chunk_sequence(coarse_ids, cuts)
    cu_lengths = [_flat_len(c) for c in chunks]
    return _blocks_from_chunk_lengths(M, frame_lengths, cu_lengths)


def chunk_an_utterance(sub, M, C):
    """One utterance's invariant frame matrix M -> list of (frame_block, n_frames).
    The frame_block is the contiguous slice of M the chunk spans (its prototype).

    If COLLAPSE_MODE != "none", the per-frame unit stream is first coarsened by the
    agent's run-length collapse (domains/run_length_collapse) and the TP chunker runs
    on the coarse units; each coarse unit's frame span is mapped back so prototypes
    stay real audio frames."""
    units = quantize(M, C)
    n_frames = len(units)

    if COLLAPSE_MODE != "none":
        from domains.run_length_collapse import collapse_stream
        tag = f"csr_{COLLAPSE_MODE}_{id(M) & 0xffffff}"
        col = collapse_stream(sub, units, tag, mode=COLLAPSE_MODE, M=M)
        coarse_units = col["coarse_ids"]
        frame_lengths = col["lengths"]
        res = forward_segment(sub, [coarse_units], n_passes=1,
                              boundary_mode=_BOUNDARY_MODE)
        chunked = res["chunked"]
        if not chunked or chunked[0] is None:
            return [(M, n_frames)]
        cu_lengths = [_flat_len(c) for c in chunked[0]]
        blocks, ui, fi = [], 0, 0
        for cu in cu_lengths:
            if cu <= 0:
                continue
            fl = max(1, sum(frame_lengths[ui:ui + cu]))
            blocks.append((M[fi:fi + fl], fl))
            ui += cu
            fi += fl
        if fi < n_frames and blocks:
            last_M, last_L = blocks[-1]
            blocks[-1] = (M[fi - last_L:], n_frames - (fi - last_L))
        return blocks if blocks else [(M, n_frames)]

    res = forward_segment(sub, [units], n_passes=1, boundary_mode=_BOUNDARY_MODE)
    chunked = res["chunked"]
    if not chunked or chunked[0] is None:
        # degenerate TP (no trough structure) -> whole utterance is one chunk
        return [(M, M.shape[0])]
    lengths = [_flat_len(c) for c in chunked[0]]
    blocks = []
    idx = 0
    for L in lengths:
        if L <= 0:
            continue
        blocks.append((M[idx:idx + L], L))
        idx += L
    if idx < M.shape[0]:                       # trailing frames -> last chunk
        if blocks:
            last_M, last_L = blocks[-1]
            blocks[-1] = (M[idx - last_L:], M.shape[0] - (idx - last_L))
        else:
            blocks.append((M, M.shape[0]))
    return blocks if blocks else [(M, M.shape[0])]


# --------------------------------------------------------------------------
# Train alignment: chunk sequence <-> transcript words. Chunks are word-like
# (~0.84 pure), so a near-1:1 alignment is feasible. We use a proportional
# duration alignment over the FRAME counts (each chunk's frame span as a slice
# of the utterance), which needs no word timestamps and applies identically to
# every utterance. A chunk's aligned word = the transcript word whose
# proportional time-span the chunk's CENTRE falls in.
# --------------------------------------------------------------------------

def align_chunks_to_words(chunk_lengths, words):
    """Return one transcript-word per chunk by proportional frame alignment.
    chunk_lengths = frames per chunk; words = transcript words. The chunk centre's
    fraction of total frames picks the word whose char-proportional span it lands
    in. (LibriSpeech ships no word timestamps; char-length is the standard rough
    proxy, used identically everywhere.)"""
    if not words or not chunk_lengths:
        return []
    total_frames = sum(chunk_lengths)
    wlens = [len(w) + 1 for w in words]
    wtot = sum(wlens)
    ends, acc = [], 0
    for L in wlens:
        acc += L
        ends.append(acc / wtot)               # cumulative word end-fraction
    out = []
    fidx = 0
    for L in chunk_lengths:
        centre = (fidx + L / 2.0) / total_frames
        wi = 0
        while wi < len(ends) - 1 and centre > ends[wi]:
            wi += 1
        out.append(words[wi])
        fidx += L
    return out


# --------------------------------------------------------------------------
# WER (Levenshtein over word tokens) — the standard ASR metric.
# --------------------------------------------------------------------------

def wer(ref, hyp):
    """Word error rate = (S + D + I) / len(ref) via edit distance."""
    R, H = len(ref), len(hyp)
    if R == 0:
        return 0.0 if H == 0 else 1.0
    dp = [[0] * (H + 1) for _ in range(R + 1)]
    for i in range(R + 1):
        dp[i][0] = i
    for j in range(H + 1):
        dp[0][j] = j
    for i in range(1, R + 1):
        for j in range(1, H + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1,
                           dp[i - 1][j - 1] + cost)
    return dp[R][H] / R


# --------------------------------------------------------------------------
# CHUNK TRAJECTORY EMBEDDING — the bridge that lets the agent's OWN composed
# cross-speaker clusterer (domains/cross_speaker_clustering: Argmin assignment +
# Sum/Count centroid mean, the CMVN move lifted frames->tokens) operate at the
# CHUNK level.
#
# The agent's clusterer clusters FIXED-LENGTH token vectors (band attrs, Euclidean
# distance). A chunk is a VARIABLE-LENGTH invariant frame matrix. The agent's own
# science already supplies the bridge: a word's identity is its TRAJECTORY SHAPE
# (spectrum_signature_traj / the _traj_flatten move in cross_speaker_clustering_probe)
# — resample the chunk's frame matrix to a fixed number of time-slots and flatten.
# Same word from different speakers -> same trajectory shape (features are already
# speaker-normalised by the invariant transform), so the modes of the pooled chunk
# cloud ARE the words. This is exactly the latent_structure shape the agent harvested:
# "the same word's tokens across speakers form one cluster."
#
# Greedy single-pass DTW-merge (iter-4) is ORDER-DEPENDENT and never pooled across
# speakers -> purity 0.179. Pooling every train chunk into ONE cloud and running the
# agent's composed clusterer is the forward-built fix the loop picked.
# --------------------------------------------------------------------------

CHUNK_SLOTS = int(os.environ.get("CHUNK_SLOTS", "5"))   # trajectory time-slots
# iter-9 (constraint a): the chunk embedding for the agent's Euclidean clusterer.
#   "traj"     (iter-8 default) — raw resampled trajectory (rate-fragile: absolute
#              positions move with speaking rate, which DTW tolerated and this did not).
#   "rate_inv" (iter-9)         — the agent's order_n_concepts move: describe the
#              chunk by the SHAPE of its trajectory over NORMALISED time (order-0 the
#              normalised path + order-1 velocity between the fixed slots), not its
#              absolute timing. Order-N finite differences over normalised-time slots
#              are intrinsically rate-invariant (they describe the path, not the clock),
#              so the same word at different speaking rates lands at the same point —
#              the rate-invariance DTW gave, recovered as a fixed-length embedding the
#              Euclidean clusterer can use.
CHUNK_EMBED = os.environ.get("CHUNK_EMBED", "traj")


def _resample_traj(block, n_slots):
    """Resample a chunk's (T x bands) frame matrix to n_slots time points along
    NORMALISED time (0..1). Duration-normalised path — the order_n samples."""
    arr = np.asarray(block, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[None, :]
    T, B = arr.shape
    if T == 0:
        return np.zeros((n_slots, 1))
    if T == 1:
        return np.repeat(arr, n_slots, axis=0)
    xs = np.linspace(0, T - 1, n_slots)
    return np.stack([np.interp(xs, np.arange(T), arr[:, c])
                     for c in range(B)], axis=1)


def chunk_traj_vector(block, n_slots=CHUNK_SLOTS, embed=None):
    """Fixed-length embedding of a chunk for the agent's Euclidean clusterer.

    embed="traj"     — resample to n_slots time points, flatten, mean-centre +
                       unit-norm (iter-8 representation).
    embed="rate_inv" — the agent's order_n_concepts move: stack the normalised-time
                       path (order 0) with its order-1 velocity (finite difference
                       between adjacent normalised-time slots). The order-N
                       differences over normalised time describe the trajectory SHAPE
                       independent of the speaking rate, so the same word at different
                       rates embeds to the same point (the rate-invariance DTW gave,
                       as a fixed-length vector). Mean-centre + unit-norm.
    embed="rich"     — the agent's iter-11 forward build: trajectory + order-2
                       curvature + per-slot formant-RATIO (VTL-invariant) +
                       band-vs-band contrasts. See descriptor_components().
    """
    embed = embed or CHUNK_EMBED
    if embed == "rich":
        return rich_chunk_vector(block, n_slots=n_slots)
    out = _resample_traj(block, n_slots)
    if embed == "rate_inv":
        # order-0 (the normalised-time path) + order-1 (velocity = finite difference
        # over the normalised-time slots). nth_order over normalised time = the agent's
        # rate-invariant trajectory-shape descriptor.
        vel = np.diff(out, axis=0) if out.shape[0] >= 2 else np.zeros((1, out.shape[1]))
        v = np.concatenate([out.flatten(), vel.flatten()])
    else:
        v = out.flatten()
    v = v - v.mean()
    n = np.linalg.norm(v)
    return v / (n + 1e-9)


# --------------------------------------------------------------------------
# iter-11 — the RICHER cross-speaker chunk descriptor (forward-built from the
# agent's own invented features). The resampled trajectory throws away word
# identity beyond its absolute path-shape; the agent enriches it from the tools
# IT invented for FSDD:
#
#  - order-2 CURVATURE  (order_n_concepts): the 2nd finite difference of the
#    normalised-time path = trajectory acceleration / bend, a shape cue the
#    order-0 path + order-1 velocity discard. Rate-invariant by construction
#    (differences over NORMALISED time describe the path, not the clock).
#
#  - formant-RATIO       (analogy / invariant_units VTL science): a vocal-tract
#    scale α is a CONSTANT SHIFT on the log-frequency band axis (log(α·f) =
#    log α + log f). The per-slot spectral centre-of-mass (formant centroid) MINUS
#    its trajectory mean cancels that additive constant — a speaker-INVARIANT
#    formant-position cue. This is the analogical transfer the agent invented:
#    physics scale-invariant ratio -> formant ratio (ratios cancel VTL).
#
#  - band-vs-band        (feature_generator): pairwise log-band DIFFERENCES per
#    slot. On the log-energy axis a band difference IS a ratio; the spectral-SLOPE
#    / tilt contrasts the agent generated for FSDD, carried to the chunk level.
#    Band differences also cancel any per-slot additive level (loudness) term.
#
# All components are over NORMALISED time (rate-invariant) and the formant-ratio /
# band-vs-band components are VTL-invariant by construction — the prize the task
# names. Vector assembly + normalisation is the I/O boundary; the CHOICE of
# features and WHY is the agent's science. Each component is independently
# toggleable so the oracle probe can ablate which one actually lifts the ceiling.
# --------------------------------------------------------------------------

# which components are ON (set by the oracle probe for the per-feature ablation).
RICH_COMPONENTS = {
    "traj": True,        # order-0 normalised-time path (the iter-8/9 base)
    "velocity": True,    # order-1 velocity over normalised time
    "curvature": True,   # order-2 curvature (the agent's order_n move)
    "formant_ratio": True,  # per-slot formant centroid minus its mean (VTL-invariant)
    "band_vs_band": True,   # pairwise band differences per slot (band-vs-band)
}

# band-vs-band: contrast each band against a small set of reference bands (octave
# steps) — the spectral-tilt/slope contrasts, kept sparse so the descriptor stays
# compact (not all O(B^2) pairs).
_BVB_STRIDE = 4


def _formant_centroid_per_slot(out):
    """Per-slot energy-weighted mean log-frequency (formant centre-of-mass), MINUS
    its trajectory mean — the VTL-invariant formant-position cue. `out` is the
    resampled (n_slots x bands) path. Energy = exp of the log-band values (the
    front-end is log-energy), so the centroid is over actual band energy."""
    from domains.invariant_units import band_centres
    B = out.shape[1]
    log_lc = np.log(band_centres(B))
    e = np.exp(out - out.max(axis=1, keepdims=True))  # back to (relative) energy
    s = e.sum(axis=1, keepdims=True)
    cen = (e * log_lc[None, :]).sum(axis=1, keepdims=True) / (s + 1e-12)
    cen = cen[:, 0]
    return cen - cen.mean()   # subtract the trajectory mean -> cancels VTL shift


def _band_vs_band_per_slot(out):
    """Per-slot pairwise band DIFFERENCES (log-energy axis -> ratios), strided so
    the descriptor stays compact. Cancels per-slot loudness (additive level)."""
    B = out.shape[1]
    cols = []
    for i in range(0, B - _BVB_STRIDE, _BVB_STRIDE):
        cols.append(out[:, i + _BVB_STRIDE] - out[:, i])
    if not cols:
        return np.zeros((out.shape[0], 1))
    return np.stack(cols, axis=1)


def descriptor_components(block, n_slots=CHUNK_SLOTS, components=None):
    """Return the rich descriptor's component vectors as a dict {name: 1-D array}.
    Each is computed over NORMALISED time (rate-invariant); formant_ratio and
    band_vs_band are VTL-invariant by construction. The oracle probe assembles +
    ablates from this dict."""
    comp = RICH_COMPONENTS if components is None else components
    out = _resample_traj(block, n_slots)
    parts = {}
    if comp.get("traj"):
        parts["traj"] = out.flatten()
    if comp.get("velocity"):
        vel = np.diff(out, axis=0) if out.shape[0] >= 2 else np.zeros((1, out.shape[1]))
        parts["velocity"] = vel.flatten()
    if comp.get("curvature"):
        # order-2 finite difference over normalised-time slots = curvature.
        acc = (np.diff(out, n=2, axis=0) if out.shape[0] >= 3
               else np.zeros((1, out.shape[1])))
        parts["curvature"] = acc.flatten()
    if comp.get("formant_ratio"):
        parts["formant_ratio"] = _formant_centroid_per_slot(out)
    if comp.get("band_vs_band"):
        parts["band_vs_band"] = _band_vs_band_per_slot(out).flatten()
    return parts


def assemble_descriptor(parts):
    """Per-component mean-centre + unit-norm, then concatenate (so each cue
    contributes on its own scale, not dominated by the raw trajectory's energy),
    then a final unit-norm. The I/O boundary's vector assembly."""
    blocks = []
    for v in parts.values():
        v = np.asarray(v, dtype=np.float64)
        v = v - v.mean()
        nrm = np.linalg.norm(v)
        blocks.append(v / (nrm + 1e-9))
    if not blocks:
        return np.zeros(1)
    v = np.concatenate(blocks)
    return v / (np.linalg.norm(v) + 1e-9)


def rich_chunk_vector(block, n_slots=CHUNK_SLOTS, components=None):
    """The agent's iter-11 richer chunk descriptor (default = all components on)."""
    return assemble_descriptor(descriptor_components(block, n_slots, components))


class ClusterLexicon:
    """Cross-speaker CHUNK clustering lexicon — the agent's composed clusterer
    (domains/cross_speaker_clustering.cluster) run over the POOLED trajectory vectors
    of every train chunk across all speakers, LABEL-FREE. Each resulting cluster's
    word = its majority aligned-transcript word; each cluster's centroid = the mean of
    its members' trajectory vectors. Recognition = nearest centroid (Euclidean over the
    same trajectory embedding) -> the cluster's word.

    Replaces the greedy sequential DTW-merge with one global clustering pass, so the
    same word's chunks from different speakers can land in one cluster regardless of
    presentation order (the iter-4 failure mode)."""

    def __init__(self, n_clusters, n_iters=25, seed=0):
        self.n_clusters = n_clusters
        self.n_iters = n_iters
        self.seed = seed
        self._vecs = []        # pooled train chunk trajectory vectors
        self._words = []       # parallel aligned word per chunk
        self.centroids = None  # (k x dim) cluster centroids
        self.labels = None     # per-cluster majority word
        self._cluster_assign = None

    def add_train_chunk(self, block, word):
        self._vecs.append(chunk_traj_vector(block))
        self._words.append(word)

    def finalize(self):
        from domains.cross_speaker_clustering import cluster as agent_cluster
        if not self._vecs:
            self.centroids = np.zeros((0, 1))
            self.labels = []
            return
        X = np.asarray(self._vecs, dtype=np.float64)
        k = min(self.n_clusters, len(X))
        # The agent's OWN composed clusterer (graph Term-trees, evaluated natively).
        assign = agent_cluster(X, k=k, seed=self.seed, n_iters=self.n_iters)
        self._cluster_assign = assign
        # centroid = mean of members (for nearest-centroid recognition); label =
        # majority aligned word among members.
        from collections import Counter
        groups = defaultdict(list)
        for i, a in enumerate(assign):
            groups[a].append(i)
        cen, lab = [], []
        self._cluster_ids = sorted(groups)
        for c in self._cluster_ids:
            idxs = groups[c]
            cen.append(X[idxs].mean(0))
            votes = Counter(self._words[i] for i in idxs)
            lab.append(votes.most_common(1)[0][0])
        self.centroids = np.asarray(cen)
        self.labels = lab

    def lookup(self, block):
        if self.centroids is None or len(self.centroids) == 0:
            return None
        v = chunk_traj_vector(block)
        d = ((self.centroids - v[None, :]) ** 2).sum(1)
        return self.labels[int(d.argmin())]

    def purity(self):
        """Cross-speaker chunk-cluster purity: weighted fraction of train chunks
        agreeing with their cluster's majority word. multi_purity over non-singleton
        clusters is the honest number (singletons are trivially pure)."""
        from collections import Counter
        if self._cluster_assign is None:
            return {"purity": 0.0, "singleton_frac": 1.0,
                    "multi_purity": float("nan"), "multi_chunks": 0}
        groups = defaultdict(list)
        for i, a in enumerate(self._cluster_assign):
            groups[a].append(i)
        agree = total = singletons = m_agree = m_total = 0
        for idxs in groups.values():
            votes = Counter(self._words[i] for i in idxs)
            top = votes.most_common(1)[0][1]
            n = len(idxs)
            agree += top
            total += n
            if n <= 1:
                singletons += 1
            else:
                m_agree += top
                m_total += n
        return {
            "purity": agree / max(total, 1),
            "singleton_frac": singletons / max(len(groups), 1),
            "multi_purity": m_agree / m_total if m_total else float("nan"),
            "multi_chunks": m_total,
        }

    @property
    def protos(self):
        # parity with the greedy Lexicon's reporting (#clusters as "prototypes")
        return self.centroids if self.centroids is not None else []


# --------------------------------------------------------------------------
# Lexicon (greedy DTW-merge, iter-4 default): chunk-prototype clusters merged by
# DTW; each cluster -> majority word.
# --------------------------------------------------------------------------

def _len_bucket(n):
    """Length bucket for a chunk's frame count. DTW is only meaningful (and only
    cheap) between chunks of similar length, so prototypes are indexed by bucket
    and a chunk only ever DTW-compares within its own +-1 neighbouring buckets.
    This is a speed AND quality measure, not a tuned parameter."""
    return n // 3


class Lexicon:
    def __init__(self, merge_thr=0.7, max_protos=2000):
        self.merge_thr = merge_thr
        self.max_protos = max_protos
        self.protos = []         # list of frame-matrices (cluster prototypes)
        self.word_votes = []     # parallel: dict word->count for each proto
        self.buckets = defaultdict(list)   # len-bucket -> [proto indices]
        self._frozen = False

    def _candidates(self, n):
        b = _len_bucket(n)
        out = []
        for bb in (b - 1, b, b + 1):
            out.extend(self.buckets.get(bb, ()))
        return out

    def _nearest(self, block, cap):
        best, bd = -1, cap
        for k in self._candidates(block.shape[0]):
            d = dtw(block, self.protos[k])
            if d < bd:
                bd, best = d, k
        return best, bd

    def add_train_chunk(self, block, word):
        """Merge a labelled train chunk into the nearest prototype within
        merge_thr (DTW, within neighbouring length buckets), else start a new
        prototype. Accumulate the word vote."""
        best, _ = self._nearest(block, self.merge_thr)
        if best >= 0:
            self.word_votes[best][word] += 1
        elif len(self.protos) < self.max_protos:
            idx = len(self.protos)
            self.protos.append(block)
            self.word_votes.append(defaultdict(int, {word: 1}))
            self.buckets[_len_bucket(block.shape[0])].append(idx)
        else:
            # at capacity: fold into nearest in-bucket prototype regardless
            nb, nk = 1e18, -1
            for k in self._candidates(block.shape[0]):
                d = dtw(block, self.protos[k])
                if d < nb:
                    nb, nk = d, k
            if nk >= 0:
                self.word_votes[nk][word] += 1

    def finalize(self):
        """Each prototype's label = its most-voted train word."""
        self.labels = []
        for votes in self.word_votes:
            self.labels.append(max(votes.items(), key=lambda kv: kv[1])[0])
        self._frozen = True

    def lookup(self, block):
        """Nearest prototype by DTW (within neighbouring length buckets) -> its
        word (the recognition step)."""
        best, _ = self._nearest(block, 1e18)
        return self.labels[best] if best >= 0 else None

    def purity(self):
        """Train cluster purity: weighted fraction of chunks landing in a
        prototype whose majority word they agree with. Also returns the honest
        caveats: singleton fraction (single-chunk prototypes are trivially pure)
        and the purity restricted to MULTI-member prototypes (the real number)."""
        agree = total = 0
        singletons = 0
        m_agree = m_total = 0
        for votes in self.word_votes:
            n = sum(votes.values())
            top = max(votes.values())
            agree += top
            total += n
            if n <= 1:
                singletons += 1
            else:
                m_agree += top
                m_total += n
        return {
            "purity": agree / max(total, 1),
            "singleton_frac": singletons / max(len(self.word_votes), 1),
            "multi_purity": m_agree / m_total if m_total else float("nan"),
            "multi_chunks": m_total,
        }


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    n_speakers = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    K = int(sys.argv[4]) if len(sys.argv) > 4 else 48
    random.seed(1)

    pairs = SL.gather_pairs()
    all_speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    # hold out whole SPEAKERS for test (speaker-independent recognition)
    n_held = max(2, len(all_speakers) // 5)
    test_spk = set(all_speakers[:n_held])
    train_spk = set(all_speakers[n_held:])
    train_pairs = [p for p in pairs if p[1] in train_spk]
    test_pairs = [p for p in pairs if p[1] in test_spk]
    random.shuffle(train_pairs)
    random.shuffle(test_pairs)
    train_pairs = train_pairs[:n_train]
    test_pairs = test_pairs[:n_test]
    print(f"LibriSpeech dev-clean: {len(pairs)} utts, "
          f"{len(all_speakers)} speakers used")
    print(f"TRAIN: {len(train_pairs)} utts / {len(train_spk)} speakers   "
          f"TEST: {len(test_pairs)} utts / {len(test_spk)} HELD-OUT speakers")
    print(f"codebook K={K} units")

    sub = Substrate()

    # ---- perception + invariance over the TRAIN set ----------------------
    def frame_utts(pairlist, tag):
        out = []
        t0 = time.time()
        for i, (path, sp, ch, ut, transcript) in enumerate(pairlist):
            words = words_of(transcript)
            if not words:
                continue
            try:
                x, fs = SL.load_flac_8k(path)
            except Exception:
                continue
            M = frames_of(x, fs)
            if M.shape[0] < 4:
                continue
            out.append((M, words))
            if (i + 1) % 50 == 0:
                print(f"  [{tag}] framed {i+1}/{len(pairlist)} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        return out

    print("\nPerception + framing...")
    train_raw = frame_utts(train_pairs, "train")
    test_raw = frame_utts(test_pairs, "test")
    if len(train_raw) < 5 or len(test_raw) < 2:
        print("Too few usable utterances — aborting.")
        return

    # canonical tract from TRAIN only (no test leakage)
    canonical = canonical_log_centroid([M for M, _ in train_raw])
    print(f"canonical log-centroid (train) = {canonical:.4f}")

    print("Invariant transform (VTLN -> CMVN -> predict-remove, the default)...")
    train_inv = [(invariant_transform(M, canonical), w) for M, w in train_raw]
    test_inv = [(invariant_transform(M, canonical), w) for M, w in test_raw]

    # ---- codebook on TRAIN invariant frames ------------------------------
    pool = np.concatenate([M for M, _ in train_inv], axis=0)
    if len(pool) > 12000:
        pool = pool[np.random.default_rng(0).choice(len(pool), 12000,
                                                    replace=False)]
    print(f"k-means codebook over {len(pool)} train frames, K={K}...")
    C = kmeans(pool, K, seed=0)

    # ---- iter-9: corpus-scale TP for word-scale chunking (constraint b) ----
    # If CORPUS_TP, estimate the transitional-probability structure ONCE over the
    # whole train corpus (the statistical_learning science: word boundaries are read
    # off corpus recurrence, not one short utterance). Each utterance is then chunked
    # against this SHARED TP by the agent's graph boundary Term -> word-scale chunks.
    corpus_tp = corpus_level = None
    coarse_cache = {}     # id(M) -> (coarse_ids, frame_lengths) so we stream once
    if CORPUS_TP:
        from domains.forward_segmentation import estimate_tp, _median
        all_streams = []
        for M, _w in train_inv:
            cids, flens = coarse_stream_of(sub, M, C)
            coarse_cache[id(M)] = (cids, flens)
            all_streams.append(cids)
        corpus_tp = estimate_tp(all_streams)
        corpus_level = _median(corpus_tp.values())
        upw = sum(len(s) for s in all_streams) / max(
            sum(len(w) for _, w in train_inv), 1)
        print(f"corpus-TP: estimated over {len(all_streams)} train streams "
              f"({len(corpus_tp)} bigrams), median level={corpus_level:.3f}, "
              f"coarse-units/word={upw:.2f}")

    def chunk_dispatch(M, tag_prefix):
        """Chunk one utterance -> real-frame blocks, via corpus-TP (iter-9) when
        CORPUS_TP else per-utterance chunk_an_utterance (iter-4)."""
        if CORPUS_TP:
            cached = coarse_cache.get(id(M))
            if cached is None:
                cids, flens = coarse_stream_of(sub, M, C)
            else:
                cids, flens = cached
            return chunk_with_corpus_tp(sub, M, cids, flens, corpus_tp,
                                        corpus_level,
                                        f"{tag_prefix}_{id(M) & 0xffffff}")
        return chunk_an_utterance(sub, M, C)

    # ---- TRAIN: chunk + align + build lexicon ----------------------------
    # LEXICON_MODE selects the chunk->word lexicon builder:
    #   "greedy"  (iter-4 default) — sequential DTW-merge prototypes.
    #   "cluster" (iter-8)         — the agent's composed cross-speaker CHUNK
    #                                clustering over pooled trajectory vectors.
    LEXICON_MODE = os.environ.get("LEXICON_MODE", "greedy")
    print(f"\nChunking + grounding TRAIN chunks to transcript words "
          f"(LEXICON_MODE={LEXICON_MODE})...")
    if LEXICON_MODE == "cluster":
        # k = a generous multiple of the vocabulary so distinct words can separate;
        # bounded by chunk count. NOT tuned to a score — set to the distinct-train-word
        # count (one cluster per word, the natural target), capped for tractability.
        n_clusters = int(os.environ.get("N_CLUSTERS", "0"))
        n_iters = int(os.environ.get("CLUSTER_ITERS", "25"))
        lex = ClusterLexicon(n_clusters=n_clusters or 1, n_iters=n_iters, seed=0)
        _defer_cluster_k = (n_clusters == 0)
    else:
        lex = Lexicon()
        _defer_cluster_k = False
    align_pos_hits = align_pos_total = 0      # chunk word vs proportional truth
    chunk_counts = []
    word_counts = []
    t0 = time.time()
    for ci, (M, words) in enumerate(train_inv):
        blocks = chunk_dispatch(M, "train")
        lengths = [L for _, L in blocks]
        aligned = align_chunks_to_words(lengths, words)
        chunk_counts.append(len(blocks))
        word_counts.append(len(words))
        for (block, _L), w in zip(blocks, aligned):
            lex.add_train_chunk(block, w)
        # alignment-quality probe: how near-1:1 is chunks<->words?
        align_pos_total += 1
        if (ci + 1) % 50 == 0:
            print(f"  grounded {ci+1}/{len(train_inv)} utts  "
                  f"chunks={len(chunk_counts) and sum(chunk_counts)}  "
                  f"({time.time()-t0:.0f}s)",
                  flush=True)
    if _defer_cluster_k:
        # one cluster per distinct train word is the natural target (a usable
        # chunk->word lexicon needs at least the vocabulary's worth of clusters).
        distinct = len({w for _, ws in train_inv for w in ws})
        lex.n_clusters = max(2, distinct)
        print(f"  cluster k set to distinct train words = {lex.n_clusters}")
    print(f"  running the agent's composed clusterer over pooled chunks..."
          if LEXICON_MODE == "cluster" else "", flush=True)
    lex.finalize()

    # chunk/word count ratio = how close to 1:1 the chunking is
    tot_chunks = sum(chunk_counts)
    tot_words = sum(word_counts)
    ratio = tot_chunks / max(tot_words, 1)
    pstats = lex.purity()
    purity = pstats["purity"]

    print("\n==================================================")
    print("(1) CHUNK->WORD ALIGNMENT / LEXICON QUALITY (the crux)")
    print("==================================================")
    print(f"train utts grounded        : {len(train_inv)}")
    print(f"total chunks / total words : {tot_chunks} / {tot_words}  "
          f"(chunks-per-word ratio {ratio:.2f}, 1.0 = perfect 1:1)")
    print(f"chunk prototypes (DTW-merged): {len(lex.protos)}")
    print(f"lexicon words covered      : {len(set(lex.labels))} distinct words")
    print(f"train cluster PURITY        : {purity:.3f}  "
          f"(fraction of chunks agreeing with their cluster's majority word)")
    print(f"  singleton-prototype frac  : {pstats['singleton_frac']:.3f}  "
          f"(single-chunk clusters are trivially pure — caveat)")
    print(f"  MULTI-member purity       : {pstats['multi_purity']:.3f}  "
          f"(over {pstats['multi_chunks']} chunks in shared clusters — "
          f"the honest number)")

    # ---- TEST: recognise held-out speakers -------------------------------
    print("\n==================================================")
    print("(2) RECOGNITION on HELD-OUT speakers (WER + word accuracy)")
    print("==================================================")

    # unigram baseline = always the single most-frequent TRAIN transcript word
    train_word_freq = defaultdict(int)
    for _, words in train_inv:
        for w in words:
            train_word_freq[w] += 1
    unigram_word = max(train_word_freq.items(), key=lambda kv: kv[1])[0]
    distinct_train_words = len(train_word_freq)

    sum_wer = sum_wer_uni = sum_wer_chance = 0.0
    word_hits = word_total = 0
    uni_word_hits = 0
    # iter-9 diagnostic: content-word RECALL (position-free). word-acc is
    # position-aligned, which the unigram baseline games (always-'the' scores on every
    # 'the' position) and which a chunker that's off-by-one in length cannot win even
    # when it retrieves the right words. Set recall = |hyp_words ∩ ref_words| / |ref|
    # isolates whether the LEXICON retrieves the correct words at all, separate from
    # the alignment. Matched baseline: a unigram set ('the') and a frequency-matched
    # random-set draw (same #distinct words as the hyp, drawn by train frequency).
    recall_hits = recall_total = 0
    uni_recall_hits = freq_recall_hits = 0
    n_eval = 0
    rng = random.Random(7)
    all_train_words = list(train_word_freq.keys())
    freq_weights = [train_word_freq[w] for w in all_train_words]
    t0 = time.time()
    for ti, (M, words) in enumerate(test_inv):
        blocks = chunk_dispatch(M, "test")
        hyp = []
        for block, _L in blocks:
            w = lex.lookup(block)
            if w is not None:
                hyp.append(w)
        # collapse immediate duplicates (one word voiced over several chunks)
        collapsed = []
        for w in hyp:
            if not collapsed or collapsed[-1] != w:
                collapsed.append(w)
        hyp = collapsed

        sum_wer += wer(words, hyp)
        # unigram hyp: same length as ref, all the most-frequent word
        sum_wer_uni += wer(words, [unigram_word] * len(words))
        # chance hyp: random train words, same length as ref
        chance_hyp = [rng.choice(all_train_words) for _ in words]
        sum_wer_chance += wer(words, chance_hyp)

        # position word accuracy (truncate/align by position, honest rough proxy)
        for j, tw in enumerate(words):
            word_total += 1
            if j < len(hyp) and hyp[j] == tw:
                word_hits += 1
            if tw == unigram_word:
                uni_word_hits += 1

        # content-word RECALL (position-free, the honest "does the lexicon retrieve
        # the right words" measure). Baselines drawn to the SAME #distinct words the
        # agent's hyp proposed, so the comparison is fair (a longer guess trivially
        # recalls more).
        ref_set = set(words)
        hyp_set = set(hyp)
        n_distinct_hyp = max(1, len(hyp_set))
        uni_set = {unigram_word}
        # average the frequency-matched random control over several draws so the
        # baseline is a stable expectation, not one noisy sample.
        FREQ_DRAWS = 20
        freq_sets = [set(rng.choices(all_train_words, weights=freq_weights,
                                     k=n_distinct_hyp)) for _ in range(FREQ_DRAWS)]
        for tw in ref_set:
            recall_total += 1
            if tw in hyp_set:
                recall_hits += 1
            if tw in uni_set:
                uni_recall_hits += 1
            freq_recall_hits += sum(tw in fs for fs in freq_sets) / FREQ_DRAWS
        n_eval += 1
        if (ti + 1) % 20 == 0:
            print(f"  recognised {ti+1}/{len(test_inv)} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    mean_wer = sum_wer / max(n_eval, 1)
    mean_wer_uni = sum_wer_uni / max(n_eval, 1)
    mean_wer_chance = sum_wer_chance / max(n_eval, 1)
    word_acc = word_hits / max(word_total, 1)
    uni_word_acc = uni_word_hits / max(word_total, 1)
    chance_word_acc = 1.0 / max(distinct_train_words, 1)

    print(f"\nheld-out utts scored : {n_eval}")
    print(f"distinct train words : {distinct_train_words} "
          f"(chance word acc {chance_word_acc:.4f})")
    print(f"unigram word         : '{unigram_word}' "
          f"(most-frequent train word)")
    print("\nWORD ERROR RATE (lower = better):")
    print(f"  agent chain        : {mean_wer:.3f}")
    print(f"  unigram baseline   : {mean_wer_uni:.3f}  "
          f"(all-'{unigram_word}', same length as ref)")
    print(f"  chance baseline    : {mean_wer_chance:.3f}  (random train words)")
    print("\nWORD ACCURACY (position-aligned, higher = better):")
    print(f"  agent chain        : {word_acc:.3f}  ({word_hits}/{word_total})")
    print(f"  unigram baseline   : {uni_word_acc:.3f}")
    print(f"  chance baseline    : {chance_word_acc:.4f}")

    content_recall = recall_hits / max(recall_total, 1)
    uni_recall = uni_recall_hits / max(recall_total, 1)
    freq_recall = freq_recall_hits / max(recall_total, 1)
    print("\nCONTENT-WORD RECALL (position-free, higher = better; "
          "isolates lexicon retrieval from alignment):")
    print(f"  agent chain        : {content_recall:.3f}  "
          f"({recall_hits}/{recall_total})")
    print(f"  unigram set         : {uni_recall:.3f}  (just '{unigram_word}')")
    print(f"  freq-matched random : {freq_recall:.3f}  "
          f"(same #distinct words as hyp, drawn by train frequency)")

    # ---- VERDICT ---------------------------------------------------------
    print("\n==================================================")
    print("VERDICT")
    print("==================================================")
    usable_lexicon = purity > 0.30 and len(lex.protos) > 10
    beats_unigram_wer = mean_wer < mean_wer_uni - 0.02
    beats_unigram_acc = word_acc > uni_word_acc * 1.15 and word_acc > 0.02
    beats_chance = word_acc > chance_word_acc * 2.0
    print(f"(i)   usable lexicon (purity>0.30)      : "
          f"{'YES' if usable_lexicon else 'NO'} "
          f"(purity {purity:.3f}, {len(lex.protos)} prototypes)")
    print(f"(ii)  WER below unigram                 : "
          f"{'YES' if beats_unigram_wer else 'NO'} "
          f"(agent {mean_wer:.3f} vs unigram {mean_wer_uni:.3f})")
    print(f"(iii) word acc above unigram            : "
          f"{'YES' if beats_unigram_acc else 'NO'} "
          f"(agent {word_acc:.3f} vs unigram {uni_word_acc:.3f})")
    print(f"(iv)  word acc well above chance        : "
          f"{'YES' if beats_chance else 'NO'} "
          f"(agent {word_acc:.3f} vs chance {chance_word_acc:.4f})")
    meaningful = usable_lexicon and (beats_unigram_wer or beats_unigram_acc) \
        and beats_chance
    print(f"\n>>> {'MEANINGFUL RECOGNITION' if meaningful else 'AT/BELOW BASELINE'}"
          f": the agent's forward chain "
          f"{'DOES' if meaningful else 'does NOT clearly'} recognise continuous "
          f"speech above the baselines.")
    print("\nHONEST NOTE: this is NOT a trained ASR; absolute WER is high by "
          "construction. The test is whether recognition is MEANINGFUL (well "
          "above unigram/chance), not whether it beats Whisper. If recognition "
          "sits at the unigram baseline, the loss re-locates to the "
          "lexicon/decoder (chunk-prototype DTW grounding), not the perception "
          "or chunker upstream.")


if __name__ == "__main__":
    main()
