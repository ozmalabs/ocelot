"""enriched_hvpt_accept — iter-34: ENRICH the iter-33 many-settings graph with
genuinely ORTHOGONAL cues, ALL combined via the SAME variadic Bayes product.

THE COMPASS (user): "polyglots have a richer graph" — richer is better, monotone.
iter-33's win over the single flat channel was real but MODEST (+0.029) because its
20 channels were all GAMMATONE tradeoffs (partly redundant — every flat readout is a
spectral-detail view of the same cochleagram). The fix is GENUINELY ORTHOGONAL nodes
that catch DIFFERENT errors:

  · FFT EAR (two_ears_demo / ozma_wall_is_self_imposed): a freq-sharp long-window FFT
    readout — the COMPLEMENTARY time-frequency operating point to the gammatone, so
    orthogonal BY CONSTRUCTION (domains/filter_settings.fft_ear).
  · FORMANT-RELATION (iter-25): the agent's VTL-invariant spacing relation over the
    TRUE waveform-LPC formant positions (domains/lpc_formant_representation
    .formant_spacings_from_audio) — a relational, speaker-robust cue the gammatone
    spectral-detail channels discard.
  · MANNER/VOICING (iter-26): the agent's phonology cues — periodicity + voiced /
    sonorant / sibilant predicates + low/mid/high envelope shape
    (domains/stacked_representation._manner_voicing_channel) — the within-speaker
    manner information the spacing relation discards.

THE ONE HARD RULE (no-donkey, auditable): COMBINE ALL nodes via the iter-33 variadic
Argmax-of-product (domains/many_settings_recognizer). NO select-best (the forbidden
negative-space search), NO fit, NO global weight. Every node — the 20 iter-33
gammatone channels AND the 3 orthogonal cues — enters the SAME product symmetrically;
each node's likelihood is softmaxed by its OWN median candidate distance (read from
the data). iter-25/26 FAILED by DTW-over-CONCATENATION (which diluted the strong
channel); here each orthogonal cue is its OWN node in the product (its own 1-NN
exemplar evidence, its own temperature), which CANNOT dilute the others.

NOT WIRED (stated plainly): the AxS forward-model node (iters 16-22) inverts speak()
and needs a synthesis forward model + a convergence threshold = a fit; a lexical /
top-down prior is degenerate on the BALANCED FSDD digit set (uniform word frequency).
Both would need a fit / a non-uniform prior, so they are SKIPPED per the no-fit rule.

COMPARATORS (multi-metric LOSO over 6 FSDD speakers + persona, with SHUFFLE):
  · ENRICHED graph (iter-34)   — iter-33's 20 channels + 3 orthogonal cues, all combined
  · MANY-SETTINGS (iter-33)    — the 20 gammatone channels, all combined
  · SINGLE-SETTING FLAT (iter-31) — the middle setting's flat readout alone
  · FROZEN (cohort-warped)     — the baked-in regression baseline

Run: python -m scripts.enriched_hvpt_accept [n_per_speaker_per_digit] [rounds]
"""
import sys
import random

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from scripts.mine_whisper import gather, load_wav
from domains.invariant_units import canonical_log_centroid
from domains.grown_representation import (
    seed_patches, bands_to_patches, grow_representation,
)
from domains.filter_settings import (
    cochleagram, COCHLEAR_SETTINGS, TRANSITION_WINDOWS, fft_ear,
)
from domains.invariant_units import invariant_transform
from domains.lpc_formant_representation import (
    formant_spacings_from_audio, _autocorr, _levinson,
)
from domains.stacked_representation import (
    _manner_voicing_channel, _frame_periodicity, _LOW, _MID, _HIGH,
)
from domains.allpole_spectral_envelope import allpole_ear
import domains.many_settings_recognizer as MS
from domains import recognition_graph as RG
from domains.stt_pipeline import STTPipeline, STTParams
from substrate_rs import Substrate

# Reuse iter-33 harness machinery (the gammatone channels + the product recogniser).
from scripts.many_settings_hvpt_accept import (
    l2, flat_readout, trans_window_readout, grown_repr, frozen_repr,
    heldout_1nn, heldout_many_settings, heldout_two_node_combo,
    _grow_for_setting,
)


# ---------------------------------------------------------------------------
# The ORTHOGONAL per-utterance readouts (each its OWN node in the product).
# All adapter-math at the I/O boundary; no fit, no learned filter, no tuning.
# ---------------------------------------------------------------------------

def fft_ear_readout(x, fs):
    """The freq-sharp FFT ear — complementary time-frequency operating point."""
    return l2(fft_ear(x, fs))


def allpole_ear_readout(x, fs):
    """iter-43: the SHARP all-pole spectral ENVELOPE ear (the triply-validated
    feature front-end). The agent's OWNED _autocorr->_levinson all-pole fit evaluated
    on a log-frequency grid over a few temporal windows — the FULL sharp resonance
    structure (not just the formant-RELATION spacing), at full waveform frequency
    resolution, bypassing the BLURRY gammatone band-mean wall. Its own node in the
    product, the SAME shape as fft_ear: a fixed-length L2 descriptor. No fit."""
    return l2(allpole_ear(x, fs))


FMT_FRAMES = 24   # fixed temporal grid for the formant-relation readout


def _resample_frames(M, n):
    """Linear-resample a (frames x d) matrix to n frames (fixed-length readout)."""
    M = np.asarray(M, dtype=np.float64)
    src = M.shape[0]
    if src == n:
        return M
    if src == 0:
        return np.zeros((n, M.shape[1]), dtype=np.float64)
    out = np.zeros((n, M.shape[1]), dtype=np.float64)
    for t in range(n):
        sp = t * src / n
        i0 = int(sp); i1 = min(i0 + 1, src - 1); frac = sp - i0
        out[t] = M[i0] * (1 - frac) + M[i1] * frac
    return out


def formant_relation_readout(x, fs, n_spacings=4):
    """The agent's VTL-invariant spacing relation over the TRUE waveform-LPC
    formants, resampled to a FIXED temporal grid and flattened (the iter-25
    channel, its own node — fixed length so the product's 1-NN can compare it)."""
    fsp = formant_spacings_from_audio(x, fs, n_spacings=n_spacings)
    return l2(_resample_frames(fsp, FMT_FRAMES).flatten())


_MV_SUB = Substrate()   # one scratch substrate for the phonology predicate evals


def manner_voicing_readout(x, fs, M):
    """The agent's phonology cues (periodicity + voiced/sonorant/sibilant predicates
    + low/mid/high envelope shape), flattened over frames (the iter-26 channel)."""
    mv = _manner_voicing_channel(x, fs, M, 25, _MV_SUB)
    return l2(mv.flatten())


# ---------------------------------------------------------------------------
# iter-37: the two ORTHOGONAL nodes the re-mine harvest ranked #1 and #2
# (docs/research_remine_methods_as_nodes.md) — the SOURCE and TEMPORAL-RATE axes
# the agent LACKS. Every existing cue reads the vocal-tract FILTER (spectral
# envelope / its derivatives); these two read a different channel entirely.
#
# Both are PURE-DSP composable nodes, ZERO FIT: a fixed-length per-utterance
# descriptor -> the SAME cosine 1-NN exemplar evidence -> softmax by the node's
# OWN median distance -> one more item in the variadic product. Same node shape as
# fft_ear. NO select, NO weight, NO tuning of any relation.
# ---------------------------------------------------------------------------

F0_FRAMES = 24            # fixed temporal grid for the pitch-contour readout
F0_MIN_HZ = 70.0          # human-speech F0 floor
F0_MAX_HZ = 400.0         # human-speech F0 ceiling


def f0_contour_readout(x, fs):
    """F0 / PITCH-CONTOUR node (harvest rank #1, the SOURCE channel).

    The argmax-lag track of the per-frame autocorrelation — the SAME autocorrelation
    domains/stacked_representation._frame_periodicity already runs, promoted from its
    periodicity SCALAR to the full lag (= pitch) TRAJECTORY, plus the voiced-confidence
    (the autocorrelation-peak height). Per frame: [log-F0-or-0, voiced-confidence];
    resampled to a fixed grid and flattened -> an L2-normalised per-utterance vector.

    Orthogonal BY CONSTRUCTION: every other cue reads the vocal-tract FILTER; F0 is the
    glottal SOURCE (phonagnosia <-> word-deafness — a separable channel). Pure DSP, no
    fit, the same node shape as fft_ear."""
    x = np.asarray(x, dtype=np.float64)
    if x.size < 16:
        return l2(np.zeros(F0_FRAMES * 2, dtype=np.float64))
    win = int(0.030 * fs)                       # 30 ms analysis window
    hop = max(1, int(0.010 * fs))               # 10 ms hop
    lo = max(1, int(fs / F0_MAX_HZ))            # min lag (highest F0)
    hi = min(win - 1, int(fs / F0_MIN_HZ))      # max lag (lowest F0)
    rows = []
    for a0 in range(0, max(1, len(x) - win + 1), hop):
        fr = x[a0:a0 + win]
        fr = fr - fr.mean()
        if fr.size < 16 or np.allclose(fr, 0.0):
            rows.append((0.0, 0.0)); continue
        ac = np.correlate(fr, fr, mode="full")[fr.size - 1:]
        if ac[0] <= 0 or hi <= lo:
            rows.append((0.0, 0.0)); continue
        ac = ac / ac[0]
        seg = ac[lo:hi]
        if seg.size == 0:
            rows.append((0.0, 0.0)); continue
        k = int(np.argmax(seg)) + lo            # argmax-lag = the pitch period
        conf = float(np.clip(seg.max(), 0.0, 1.0))
        f0 = fs / k if k > 0 else 0.0
        # voiced only if the periodicity is convincing; else F0 = 0 (unvoiced).
        logf0 = float(np.log(f0)) if (conf > 0.3 and f0 > 0) else 0.0
        rows.append((logf0, conf))
    if not rows:
        return l2(np.zeros(F0_FRAMES * 2, dtype=np.float64))
    M = np.asarray(rows, dtype=np.float64)
    M = _resample_frames(M, F0_FRAMES)
    return l2(M.flatten())


MODSPEC_NF = 32           # envelope frames the temporal FFT runs over
MODSPEC_BANDS = [(2.0, 4.0), (4.0, 6.0), (6.0, 8.0)]   # syllabic-rate mod bands (Hz)


def modspec_readout(x, fs, M):
    """MODULATION-SPECTRUM node (harvest rank #2, the TEMPORAL-RATE channel).

    The temporal FFT of each gammatone band-energy ENVELOPE, pooled into the
    linguistically-dominant 2-8 Hz modulation bands (peak ~4 Hz = the syllabic rate).
    M is the middle-setting cochleagram (frames x bands); the per-band envelope frame
    rate is derived from the clip duration. Result: per band x per mod-band modulation
    energy, flattened -> an L2-normalised per-utterance vector.

    Orthogonal: the transition node is a POINT derivative (order-1 between windows);
    the modulation spectrum is the RATE DISTRIBUTION of the envelope — a temporal-rate
    axis, neither spectral nor order-1. Speaker/condition-invariant by design. Pure
    DSP, no fit."""
    M = np.asarray(M, dtype=np.float64)
    if M.shape[0] < 4 or M.shape[1] < 1:
        return l2(np.zeros(M.shape[1] * len(MODSPEC_BANDS) if M.ndim == 2 else 1,
                           dtype=np.float64))
    nbands = M.shape[1]
    # the envelope frame rate: M's frames span the clip duration (len(x)/fs seconds).
    dur = max(len(np.asarray(x)) / float(fs), 1e-6)
    frame_rate = M.shape[0] / dur               # envelope-frame sampling rate (Hz)
    # resample each band envelope to a fixed frame count so the mod-FFT bins are
    # comparable across clips of different length (fixed-length descriptor).
    env = _resample_frames(M, MODSPEC_NF)       # MODSPEC_NF x nbands
    # the resample changes the effective frame rate to MODSPEC_NF / dur.
    fr_res = MODSPEC_NF / dur
    feats = np.zeros((nbands, len(MODSPEC_BANDS)), dtype=np.float64)
    freqs = np.fft.rfftfreq(MODSPEC_NF, d=1.0 / fr_res)
    for b in range(nbands):
        e = env[:, b]
        e = e - e.mean()                        # remove DC (the steady-state level)
        mag = np.abs(np.fft.rfft(e))
        for mi, (flo, fhi) in enumerate(MODSPEC_BANDS):
            sel = (freqs >= flo) & (freqs < fhi)
            feats[b, mi] = float(mag[sel].sum()) if sel.any() else 0.0
    return l2(feats.flatten())


# ---------------------------------------------------------------------------
# iter-38: the phoneme-CLASS LANDMARK node (harvest rank #1, the TRANSIENT
# PHONETIC-EVENT axis — the LAST of the four acoustic axes: filter + source +
# temporal-rate + TRANSIENT). docs/research_dismissed_ideas_as_specialists.md §4.
#
# THE TARGET: within-manner confusions (b/d/g, p/t/k, s/f) that survive every
# speaker-invariant FILTER cue. The landmark fires on a DEFINITE acoustic event
# (burst, VOT, fricative onset, nasal murmur) so it is SHARP and RELIABLE — the
# test of whether a sharp reliable cue converts where the diffuse noisy F0 didn't.
#
# NO-DONKEY — "the detector is the donkey, the cue is the harvest": the published
# landmark/VOT detectors are TRAINED (SVM/RNN); they are NOT ported. The landmark
# CUE is RE-DERIVED as composable DSP from the agent's OWNED operators:
#   · burst   = onset spike (order-1-over-time energy jump) in HIGH bands
#               (the cochleagram high-band partition + a positive time-difference)
#   · VOT     = lag from the burst onset to the VOICING onset (the periodicity the
#               manner channel already computes: _frame_periodicity per frame)
#   · fricative = sustained HIGH-frequency APERIODIC energy (high-band energy with
#               LOW periodicity — the sibilant-band predicate, time-resolved)
#   · nasal   = low-frequency murmur + a spectral-FLATNESS dip / anti-formant via the
#               LPC residual (the Levinson gain e = residual energy, the agent's own
#               all-pole fit — a flat anti-formant region lowers the all-pole peakiness)
# Assembled into a per-segment landmark SIGNATURE vector. ZERO-FIT, no trained
# detector, no weight. Same node shape as fft_ear: a fixed-length L2 vector -> the
# SAME cosine 1-NN exemplar evidence -> softmax by its OWN median distance -> one
# more item in the variadic product. NO select, NO weight, NO fit.
# ---------------------------------------------------------------------------

LM_FRAMES = 24            # fixed temporal grid for the landmark contour readout
LM_PERIODIC_THRESH = 0.3  # the manner channel's voicing periodicity floor (reused)


def _lpc_residual_flatness(frame, fs, order=None):
    """Spectral FLATNESS proxy from the agent's OWN LPC residual (Levinson gain e).

    Fit the all-pole model by linear prediction (the agent's _autocorr + _levinson),
    and read the residual energy ratio e/r[0]: a peaky resonant spectrum (formants /
    nasal anti-formant absent) leaves SMALL residual; a FLAT spectrum leaves LARGE
    residual. The nasal murmur + anti-formant flattens the high-band envelope, raising
    flatness. Pure DSP from owned operators, no fit. Returns flatness in [0,1]."""
    x = np.asarray(frame, dtype=np.float64)
    x = x - x.mean()
    if x.size < 16 or np.allclose(x, 0.0):
        return 0.0
    if order is None:
        order = int(fs / 1000) + 2
    r = _autocorr(x, min(order, x.size - 1))
    if r[0] <= 0.0:
        return 0.0
    _a, e = _levinson(r, min(order, len(r) - 1))
    # e is the residual (prediction-error) energy; e/r[0] in (0,1]; high = flat.
    return float(np.clip(e / r[0], 0.0, 1.0))


def landmark_readout(x, fs, M):
    """Phoneme-CLASS LANDMARK node (harvest rank #1, the TRANSIENT-event axis).

    Per frame, a landmark SIGNATURE composed entirely from the agent's OWNED operators
    — the cue NOT the detector, zero-fit:
      [burst, voicing, fricative, nasal_flatness, hi_energy, lo_energy]
    plus three SCALAR per-utterance landmark-TIMING summaries appended at the end:
      [burst_time, voicing_onset_time, burst_to_voicing_LAG (= VOT)].
    The per-frame contour is resampled to a fixed grid; the whole vector is L2-normed.
    M is the middle-setting cochleagram (frames x bands)."""
    x = np.asarray(x, dtype=np.float64)
    M = np.asarray(M, dtype=np.float64)
    nf = M.shape[0]
    if nf < 2 or M.shape[1] < max(_HIGH + _LOW) + 1:
        return l2(np.zeros(LM_FRAMES * 6 + 3, dtype=np.float64))
    win = int(0.025 * fs)
    # high / low band energy per frame (owned cochleagram partitions).
    hi = M[:, _HIGH].mean(axis=1) if _HIGH else np.zeros(nf)
    lo = M[:, _LOW].mean(axis=1) if _LOW else np.zeros(nf)
    # BURST = positive order-1-over-time jump in high-band energy (onset spike).
    dhi = np.diff(hi, prepend=hi[:1])
    burst = np.clip(dhi, 0.0, None)
    # per-frame VOICING (periodicity) + fricative-noise + nasal-flatness, all from
    # owned operators evaluated on the time-aligned waveform window.
    voicing = np.zeros(nf); fric = np.zeros(nf); flat = np.zeros(nf)
    for r in range(nf):
        c = int((r + 0.5) * len(x) / max(nf, 1))
        a0 = max(0, c - win // 2)
        fr = x[a0:min(len(x), a0 + win)]
        per = _frame_periodicity(fr, fs)
        voicing[r] = per
        # FRICATIVE = sustained high-band energy that is APERIODIC (low periodicity).
        fric[r] = hi[r] * (1.0 - per)
        # NASAL = low-band murmur AND a spectral-flatness dip (anti-formant) from LPC.
        flat[r] = lo[r] * _lpc_residual_flatness(fr, fs)
    # per-utterance landmark TIMING (the VOT geometry): the first strong burst frame,
    # the first voiced frame after it, and their lag (= VOT). Normalised by clip length.
    bthr = burst.mean() + burst.std() if burst.std() > 0 else burst.max()
    burst_frames = np.where(burst >= bthr)[0]
    burst_t = float(burst_frames[0]) / nf if burst_frames.size else 0.0
    voiced_frames = np.where(voicing > LM_PERIODIC_THRESH)[0]
    if burst_frames.size and voiced_frames.size:
        after = voiced_frames[voiced_frames >= burst_frames[0]]
        v_t = float(after[0]) / nf if after.size else 0.0
        vot = max(0.0, v_t - burst_t)
    else:
        v_t = float(voiced_frames[0]) / nf if voiced_frames.size else 0.0
        vot = 0.0
    # assemble: the 6 per-frame contours (resampled to a fixed grid) ++ 3 timing scalars.
    contour = np.stack([burst, voicing, fric, flat, hi, lo], axis=1)  # nf x 6
    contour = _resample_frames(contour, LM_FRAMES)                    # LM_FRAMES x 6
    vec = np.concatenate([contour.flatten(),
                          np.array([burst_t, v_t, vot], dtype=np.float64)])
    return l2(vec)


ORTHO_NAMES = ["fft_ear", "formant_relation", "manner_voicing",
               "f0_contour", "modspec", "landmark", "allpole_envelope"]


# ---------------------------------------------------------------------------
# iter-35: the SINGLE-PASS AxS (analysis-by-synthesis) node — top-down, no fit.
#
# For sign s and candidate word w: the agent's OWNED forward model (the per-word
# mean A1-patch trajectory of the TRAIN-speaker exemplars — LOSO-clean, the held
# voice never enters its own model) gives synth(w). The graph DtwTo Term computes
# synth_error(s,w) = DtwTo(features(s), synth(w)); softmax the NEGATIVE synth-errors
# over candidates BY THE NODE'S OWN MEDIAN distance (likelihood_from_distances, the
# IDENTICAL softmax every other channel uses) -> P_axs(w|s). NO convergence loop,
# NO threshold, NO global weight, NO select-best — a single-pass likelihood node,
# orthogonal BY CONSTRUCTION (top-down/generative vs every other node's bottom-up
# 1-NN). It enters the SAME variadic product as the 24th channel.
#
# This is the faithful instance<->model A1-space comparison the iter-16 AxS accept
# script found best (no natural/synthetic resynthesis domain gap; the brain inverts
# the internal forward model, it does not literally replay sound).
# ---------------------------------------------------------------------------

_N_PATCHES = 25                       # A1 patch count (matches the ingest pipeline)
_AXS_SUB = None                       # the substrate the DtwTo Term evaluates on
_AXS_WC: dict = {}                    # candidate word -> Concept node
_AXS_SIGN = None                      # the heard-sign node (carries features(s))
_AXS_ERR_TERM = None                  # the graph DtwTo synth-error Term (per s,w)


def _as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in M)


def utterance_a1_trajectory(x, fs):
    """One utterance's A1-patch trajectory (frames x patches), extracted by ingesting
    into a FRESH substrate (so the lexical matcher can't collapse it). The word-
    distinct building block of the agent's word->sound forward model — the same
    extraction the iter-16 AxS accept uses (fresh pipeline per call: the pipeline
    caches node IDs bound to one substrate)."""
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    pipe.ingest(sub, x)
    sub.tick(50000)
    best = None
    for s in sub.nodes("AcousticSign"):
        t = sub.node(s)["attrs"].get("trajectory")
        if t and (best is None or len(t) > len(best)):
            best = t
    if not best:
        return None
    t = np.array([float(v) for v in best], dtype=np.float32)
    spp = len(t) // _N_PATCHES
    if spp == 0:
        return None
    return t[:spp * _N_PATCHES].reshape(spp, _N_PATCHES)


def _axs_word_model(train_trajs, train_words):
    """The agent's owned forward model: per-word mean A1 trajectory over the TRAIN
    exemplars (exemplar average — no fit, no convergence, no threshold). Returns
    {word: frames x patches np.ndarray}. LOSO is enforced by the caller (the held
    voice's utterances are not in train_trajs)."""
    by_word = {}
    for t, w in zip(train_trajs, train_words):
        if t is not None:
            by_word.setdefault(w, []).append(t)
    model = {}
    for w, ts in by_word.items():
        L = min(t.shape[0] for t in ts)
        model[w] = np.mean([t[:L] for t in ts], axis=0)
    return model


def _axs_machinery(candidate_words):
    """A tiny substrate with one Concept per candidate + one sign node, and the graph
    DtwTo synth-error Term. Reused across queries; only the attrs change per query."""
    global _AXS_SUB, _AXS_SIGN, _AXS_ERR_TERM
    if _AXS_SUB is None:
        _AXS_SUB = Substrate()
        _AXS_SIGN = _AXS_SUB.add_node("AcousticSign", {"axs_probe": 1.0})
        _AXS_ERR_TERM = MS._Pred(
            RG._DtwTo(RG._Attr(RG._V("s"), RG.SIGN_FEAT_ATTR),
                      RG._Attr(RG._V("w"), RG.WORD_FEAT_ATTR)))
        _AXS_WC.clear()
    for w in candidate_words:
        if w not in _AXS_WC:
            c = _AXS_SUB.add_node("Concept", {"name": w})
            _AXS_SUB.set_attr(c, RG.WORD_ATTR, 1.0)
            _AXS_WC[w] = c
    return _AXS_SUB


def axs_query_likelihood(heard_traj, word_model, candidate_words):
    """SINGLE-PASS AxS likelihood for one heard utterance: per candidate w,
    synth_error = DtwTo(features(s), synth(w)) via the GRAPH Term; softmax the
    negative errors by the node's OWN median distance. {word: likelihood}. No fit."""
    sub = _axs_machinery(candidate_words)
    if heard_traj is None:
        return {w: 1.0 / len(candidate_words) for w in candidate_words}
    sub.set_attr(_AXS_SIGN, RG.SIGN_FEAT_ATTR, _as_tuple(heard_traj))
    dists = {}
    for w in candidate_words:
        m = word_model.get(w)
        if m is None:
            dists[w] = float("inf")
            continue
        c = _AXS_WC[w]
        sub.set_attr(c, RG.WORD_FEAT_ATTR, _as_tuple(m))
        dists[w] = float(sub.evaluate(_AXS_ERR_TERM, {"s": _AXS_SIGN, "w": c}))
    return MS.likelihood_from_distances(dists)


def axs_channel(train_trajs, train_words, held_trajs, candidate_words):
    """The AxS node as a precomputed per-query likelihood channel (so it slots into
    the product exactly like the 1-NN channels' likelihoods). Builds the forward
    model from the TRAIN trajectories, then for each HELD query returns its AxS
    likelihood dict. Returns (held_likelihoods, alone_pred, label_shuffle_lik) —
    alone_pred is the AxS node's standalone argmax prediction; label_shuffle_lik is
    the AxS node's OWN structural control (word<->forward-model permuted, so the
    synth-error points at the wrong word — AxS must collapse to chance). DIAGNOSTIC."""
    model = _axs_word_model(train_trajs, train_words)
    held_lik = [axs_query_likelihood(t, model, candidate_words) for t in held_trajs]
    alone_pred = [max(d, key=d.get) for d in held_lik]
    # AxS-specific control: mis-point the forward model (permute word -> model).
    rng = random.Random(0)
    perm = list(candidate_words)
    rng.shuffle(perm)
    label_map = dict(zip(candidate_words, perm))
    shuf_model = {w: model.get(label_map[w]) for w in candidate_words}
    label_shuffle_lik = [axs_query_likelihood(t, shuf_model, candidate_words)
                         for t in held_trajs]
    return held_lik, alone_pred, label_shuffle_lik


# ---------------------------------------------------------------------------
# Combine VECTOR channels (own 1-NN cosine likelihood) AND precomputed-likelihood
# channels (e.g. the AxS node) in the SAME variadic product. Mirrors
# many_settings_hvpt_accept.heldout_many_settings but lets a channel supply its
# likelihood directly (the AxS DTW-synth-error node is not a cosine 1-NN).
# ---------------------------------------------------------------------------

_ENR_SUB = None
_ENR_WC: dict = {}
_ENR_TERM = None
_ENR_NCH = None
_ENR_CANDS = None


def _enr_substrate(candidate_words, n_channels):
    # Rebuild the scratch substrate whenever the channel count OR the candidate set
    # changes. FSDD's vocab is constant (10 digits), but continuous folds (iter-36)
    # have DIFFERENT shared vocabularies per held-out speaker; a stale concept set
    # from a prior fold would pollute the Argmax (the Argmax ranges over every
    # is_word Concept in the substrate) and carry stale p_ch attrs, collapsing every
    # channel count to the same degenerate prediction. Keying on the candidate set
    # makes the cache correct for both; constant-vocab FSDD is unaffected.
    global _ENR_SUB, _ENR_TERM, _ENR_NCH, _ENR_CANDS
    cand_key = frozenset(candidate_words)
    if _ENR_SUB is None or _ENR_NCH != n_channels or _ENR_CANDS != cand_key:
        _ENR_SUB = Substrate()
        _ENR_TERM = MS._Pred(MS.predict_many_settings_term(n_channels))
        _ENR_NCH = n_channels
        _ENR_CANDS = cand_key
        _ENR_WC.clear()
    for w in candidate_words:
        if w not in _ENR_WC:
            c = _ENR_SUB.add_node("Concept", {"name": w})
            _ENR_SUB.set_attr(c, MS.WORD_ATTR, 1.0)
            _ENR_WC[w] = c
    return _ENR_SUB


def heldout_combined(vec_train, vec_test, train_words, test_words,
                     extra_lik_channels=(), return_preds=False):
    """Variadic-product recognition over n_vec cosine-1-NN channels PLUS
    len(extra_lik_channels) precomputed-likelihood channels (each a list, one
    {word: likelihood} per test query). ALL channels enter the SAME product
    symmetrically (combine-all, no weight, no select). Returns accuracy (or the
    per-query predictions when return_preds=True — for the error-overlap diagnostic)."""
    n_vec = len(vec_train)
    n_extra = len(extra_lik_channels)
    n_ch = n_vec + n_extra
    Xs = [np.asarray(ct) for ct in vec_train]
    candidates = sorted(set(train_words))
    sub = _enr_substrate(candidates, n_ch)
    correct = 0
    n_test = len(test_words)
    preds = []
    for qi in range(n_test):
        for ci in range(n_vec):
            p = MS.channel_likelihood(np.asarray(vec_test[ci][qi]),
                                      Xs[ci], train_words, candidates)
            for w in candidates:
                sub.set_attr(_ENR_WC[w], MS.channel_attr(ci), p[w])
        for ei, chan in enumerate(extra_lik_channels):
            p = chan[qi]
            for w in candidates:
                sub.set_attr(_ENR_WC[w], MS.channel_attr(n_vec + ei),
                             float(p.get(w, 1.0 / len(candidates))))
        pred = sub.evaluate(_ENR_TERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        preds.append(pw)
        correct += int(pw == test_words[qi])
    if return_preds:
        return preds
    return correct / max(n_test, 1)


# ---------------------------------------------------------------------------
# Build one LOSO fold: the iter-33 gammatone channels PLUS the orthogonal cues.
# ---------------------------------------------------------------------------

def build_fold(voice_audio, held_voice, rounds=2, shuffle=False, skip_axs=False):
    """One LOSO fold. Returns the iter-33 channel lists (many_train/held) AND the
    orthogonal channel lists (ortho_train/held), plus the single-flat and frozen
    comparators, plus the train/test words. Combine-all happens at scoring time.

    skip_axs=True omits the slow per-utterance AxS A1-trajectory extraction (the AxS
    node is a diagnostic top-down channel, irrelevant to the bottom-up feature-front-
    end verdict); the AxS likelihoods then default to uniform, so any combine-all that
    includes them is unaffected in ranking by that node. Used by the iter-43 sharp-
    front-end acceptance, which scores the bottom-up cue-graph only."""
    train_voices = [v for v in voice_audio if v != held_voice]
    settings = COCHLEAR_SETTINGS

    # Per cochlear setting: band matrices for train (to grow) + held.
    setting_train_bands = []
    setting_held_bands = []
    for (_, env_cut, dur_cut, nf) in settings:
        tr = {}
        for v in train_voices:
            tr[v] = [(w, cochleagram(x, fs, env_cut, dur_cut, nf))
                     for (x, fs, w) in voice_audio[v]]
        held = [(w, cochleagram(x, fs, env_cut, dur_cut, nf))
                for (x, fs, w) in voice_audio[held_voice]]
        setting_train_bands.append(tr)
        setting_held_bands.append(held)

    # Raw audio aligned to the SAME train/held order (for the orthogonal cues, which
    # work on the waveform, not the band matrix).
    train_audio = [(w, x, fs) for v in train_voices
                   for (x, fs, w) in voice_audio[v]]
    held_audio = [(w, x, fs) for (x, fs, w) in voice_audio[held_voice]]

    # SHUFFLE control: randomise the voice partition (words stay attached) so the
    # cross-voice survival selector sees no real voice structure. The SAME shuffle
    # order is applied to the band matrices AND the raw audio (so the orthogonal
    # cues are shuffled identically — the control bites the whole enriched graph).
    slot_order = None
    if shuffle:
        rng = random.Random(1234)
        k = len(train_voices)
        new_setting_train = []
        for tr in setting_train_bands:
            flat = [(w, M) for v in train_voices for (w, M) in tr[v]]
            if slot_order is None:
                slot_order = list(range(len(flat)))
                rng.shuffle(slot_order)
            flat = [flat[i] for i in slot_order]
            shuf = {f"shuf{i}": [] for i in range(k)}
            for idx, (w, M) in enumerate(flat):
                shuf[f"shuf{idx % k}"].append((w, M))
            new_setting_train.append(shuf)
        setting_train_bands = new_setting_train
        # reorder the raw train audio by the SAME slot order.
        train_audio = [train_audio[i] for i in slot_order]
        train_voices = [f"shuf{i}" for i in range(k)]

    # Grow a patch bank per cochlear setting (selector decides; no sweep).
    setting_patches = []
    grown_counts = []
    for tr in setting_train_bands:
        patches, grown = _grow_for_setting(tr, rounds)
        setting_patches.append(patches)
        grown_counts.append(len(grown))

    # The iter-33 gammatone channels (flat + multi-window transition per setting).
    many_train, many_held, many_names = [], [], []
    train_words = held_words = None
    middle_idx = next(i for i, s in enumerate(settings) if s[0] == "middle")
    single_flat_train = single_flat_held = None
    for si, (sname, *_rest) in enumerate(settings):
        patches = setting_patches[si]
        tr = setting_train_bands[si]
        held = setting_held_bands[si]
        tr_items = [(w, M) for v in train_voices for (w, M) in tr[v]]
        if train_words is None:
            train_words = [w for (w, _) in tr_items]
            held_words = [w for (w, _) in held]
        tr_flat = [flat_readout(grown_repr(M, patches)) for (_, M) in tr_items]
        he_flat = [flat_readout(grown_repr(M, patches)) for (_, M) in held]
        many_train.append(tr_flat); many_held.append(he_flat)
        many_names.append(f"{sname}:flat")
        for (wname, nwin) in TRANSITION_WINDOWS:
            tr_t = [trans_window_readout(grown_repr(M, patches), patches, nwin)
                    for (_, M) in tr_items]
            he_t = [trans_window_readout(grown_repr(M, patches), patches, nwin)
                    for (_, M) in held]
            many_train.append(tr_t); many_held.append(he_t)
            many_names.append(f"{sname}:{wname}")
        if si == middle_idx:
            single_flat_train, single_flat_held = tr_flat, he_flat

    # The ORTHOGONAL channels (each its own node). Computed on the waveform, in the
    # SAME train/held order (and shuffle-reordered identically).
    mid_train_M = [M for v in train_voices for (_, M) in setting_train_bands[middle_idx][v]]
    mid_held_M = [M for (_, M) in setting_held_bands[middle_idx]]

    ortho_train, ortho_held = [], []
    # FFT ear
    ortho_train.append([fft_ear_readout(x, fs) for (_, x, fs) in train_audio])
    ortho_held.append([fft_ear_readout(x, fs) for (_, x, fs) in held_audio])
    # formant relation
    ortho_train.append([formant_relation_readout(x, fs) for (_, x, fs) in train_audio])
    ortho_held.append([formant_relation_readout(x, fs) for (_, x, fs) in held_audio])
    # manner / voicing (needs the middle-setting band matrix)
    ortho_train.append([manner_voicing_readout(x, fs, M)
                        for (_, x, fs), M in zip(train_audio, mid_train_M)])
    ortho_held.append([manner_voicing_readout(x, fs, M)
                       for (_, x, fs), M in zip(held_audio, mid_held_M)])
    # iter-37: F0 / pitch-contour (the SOURCE channel) — on the raw waveform.
    ortho_train.append([f0_contour_readout(x, fs) for (_, x, fs) in train_audio])
    ortho_held.append([f0_contour_readout(x, fs) for (_, x, fs) in held_audio])
    # iter-37: modulation spectrum (the temporal-RATE channel) — needs the middle band matrix.
    ortho_train.append([modspec_readout(x, fs, M)
                        for (_, x, fs), M in zip(train_audio, mid_train_M)])
    ortho_held.append([modspec_readout(x, fs, M)
                       for (_, x, fs), M in zip(held_audio, mid_held_M)])
    # iter-38: LANDMARK (the TRANSIENT phonetic-event channel) — needs the middle band matrix.
    ortho_train.append([landmark_readout(x, fs, M)
                        for (_, x, fs), M in zip(train_audio, mid_train_M)])
    ortho_held.append([landmark_readout(x, fs, M)
                       for (_, x, fs), M in zip(held_audio, mid_held_M)])
    # iter-43: SHARP ALL-POLE SPECTRAL ENVELOPE (the feature front-end) — raw waveform,
    # the agent's owned Levinson all-pole fit on a log-freq grid, bypassing the band wall.
    ortho_train.append([allpole_ear_readout(x, fs) for (_, x, fs) in train_audio])
    ortho_held.append([allpole_ear_readout(x, fs) for (_, x, fs) in held_audio])

    # FROZEN comparator (middle setting, cohort-warped front-end, seed bank).
    seed = seed_patches()
    tr_items_m = [(w, M) for v in train_voices
                  for (w, M) in setting_train_bands[middle_idx][v]]
    canonical = canonical_log_centroid([M for (_, M) in tr_items_m])
    frozen_train = [flat_readout(frozen_repr(M, canonical, seed))
                    for (_, M) in tr_items_m]
    frozen_held = [flat_readout(frozen_repr(M, canonical, seed))
                   for (_, M) in setting_held_bands[middle_idx]]

    # iter-35 AxS node: extract each utterance's A1 trajectory (train + held, in the
    # SAME shuffle-respecting order), build the per-word forward model from TRAIN
    # trajectories, and compute the single-pass AxS likelihood for each HELD query.
    axs_train_words = [w for (w, _, _) in train_audio]
    candidates = sorted(set(axs_train_words))
    if skip_axs:
        # AxS omitted (the bottom-up front-end verdict does not use it): uniform
        # likelihoods + no standalone predictions.
        unif = {w: 1.0 / max(len(candidates), 1) for w in candidates}
        axs_held_lik = [dict(unif) for _ in held_audio]
        axs_alone_pred = []
        axs_label_shuf_lik = [dict(unif) for _ in held_audio]
    else:
        train_axs_trajs = [utterance_a1_trajectory(x, fs) for (_, x, fs) in train_audio]
        held_axs_trajs = [utterance_a1_trajectory(x, fs) for (_, x, fs) in held_audio]
        axs_held_lik, axs_alone_pred, axs_label_shuf_lik = axs_channel(
            train_axs_trajs, axs_train_words, held_axs_trajs, candidates)

    return {
        "many_train": many_train, "many_held": many_held, "many_names": many_names,
        "ortho_train": ortho_train, "ortho_held": ortho_held,
        "ortho_names": list(ORTHO_NAMES),
        "single_flat_train": single_flat_train, "single_flat_held": single_flat_held,
        "frozen_train": frozen_train, "frozen_held": frozen_held,
        "train_words": train_words, "held_words": held_words,
        "axs_held_lik": axs_held_lik, "axs_alone_pred": axs_alone_pred,
        "axs_label_shuf_lik": axs_label_shuf_lik,
        "n_many": len(many_train), "n_ortho": len(ortho_train),
        "grown_counts": grown_counts, "held_voice": held_voice, "shuffle": shuffle,
        "n_held": len(held_words), "n_train": len(train_words),
    }


def score_fold(f):
    """All metrics for one built fold. ENRICHED = iter-33 channels + orthogonal cues,
    ALL combined via the variadic product. Plus per-orthogonal-cue contribution
    (leave-one-orthogonal-out + each orthogonal cue alone — DIAGNOSTIC, not selection:
    the accepted graph is always the full combine-all)."""
    tw, hw = f["train_words"], f["held_words"]
    many_tr, many_he = f["many_train"], f["many_held"]
    ot_tr, ot_he = f["ortho_train"], f["ortho_held"]
    axs_lik = f["axs_held_lik"]                       # the AxS precomputed-likelihood channel

    vec_tr = many_tr + ot_tr                          # 23 cosine-1-NN vector channels
    vec_he = many_he + ot_he

    # iter-34 = the vector channels combined (NO AxS). enriched+AxS = + the AxS node.
    iter34 = heldout_combined(vec_tr, vec_he, tw, hw)
    enriched = heldout_combined(vec_tr, vec_he, tw, hw, extra_lik_channels=[axs_lik])
    iter33 = heldout_combined(many_tr, many_he, tw, hw)   # 20 gammatone, no orthogonal
    single_flat = heldout_1nn(f["single_flat_train"], tw, f["single_flat_held"], hw)
    frozen = heldout_1nn(f["frozen_train"], tw, f["frozen_held"], hw)

    # Reconstruct the prior-iteration baselines by NAME (robust to ortho ordering),
    # each = the SAME variadic product with the later nodes removed:
    #   iter36 = gammatone + 3 orthos (fft_ear, formant_relation, manner_voicing) + AxS
    #   iter37 = iter36 + f0_contour + modspec
    #   enriched (this iter, the full graph) = iter37 + landmark
    # The decisive comparison is graph+landmark vs iter37 = enriched - iter37.
    def _combo_without(drop_names):
        keep = [i for i, n in enumerate(f["ortho_names"]) if n not in drop_names]
        return heldout_combined(many_tr + [ot_tr[i] for i in keep],
                                many_he + [ot_he[i] for i in keep], tw, hw,
                                extra_lik_channels=[axs_lik])
    iter36 = _combo_without({"f0_contour", "modspec", "landmark"})
    iter37 = _combo_without({"landmark"})

    # AxS node diagnostics: alone (its own argmax) + drop-it (enriched - iter34) +
    # the AxS-specific structural control (forward model mis-pointed -> chance).
    axs_alone = float(np.mean([int(p == w)
                               for p, w in zip(f["axs_alone_pred"], hw)])) \
        if hw else 0.0
    axs_label_shuf = float(np.mean(
        [int(max(d, key=d.get) == w) for d, w in zip(f["axs_label_shuf_lik"], hw)])) \
        if hw else 0.0
    axs_drop = enriched - iter34

    # per-orthogonal-cue diagnostics (against the full enriched+AxS product).
    ortho_alone = {}       # each orthogonal cue as a single-node recogniser
    leave_one_out = {}     # enriched+AxS with that one orthogonal cue removed
    for i, name in enumerate(f["ortho_names"]):
        ortho_alone[name] = heldout_1nn(ot_tr[i], tw, ot_he[i], hw)
        keep = [j for j in range(len(ot_tr)) if j != i]
        loo_tr = many_tr + [ot_tr[j] for j in keep]
        loo_he = many_he + [ot_he[j] for j in keep]
        leave_one_out[name] = heldout_combined(loo_tr, loo_he, tw, hw,
                                               extra_lik_channels=[axs_lik])

    return {"held_voice": f["held_voice"], "shuffle": f["shuffle"],
            "n_many": f["n_many"], "n_ortho": f["n_ortho"],
            "grown_counts": f["grown_counts"],
            "enriched": enriched, "iter34": iter34, "iter33": iter33,
            "iter36": iter36, "iter37": iter37,
            "single_flat": single_flat, "frozen": frozen,
            "axs_alone": axs_alone, "axs_label_shuf": axs_label_shuf,
            "axs_drop": axs_drop,
            "ortho_alone": ortho_alone, "leave_one_out": leave_one_out,
            "ortho_names": f["ortho_names"],
            "n_held": f["n_held"], "n_train": f["n_train"]}


def _report_fold(r):
    print(f"\n--- held-out {r['held_voice']}"
          f"{' [SHUFFLE]' if r['shuffle'] else ''} ---", flush=True)
    print(f"  channels: {r['n_many']} gammatone + {r['n_ortho']} orthogonal "
          f"= {r['n_many'] + r['n_ortho']}  (grown counts {r['grown_counts']})",
          flush=True)
    print(f"  held {r['n_held']}  train {r['n_train']}", flush=True)
    print(f"  ENRICHED+AxS {r['enriched']:.3f}   iter-34 {r['iter34']:.3f}   "
          f"iter-33 {r['iter33']:.3f}   single-flat {r['single_flat']:.3f}   "
          f"frozen {r['frozen']:.3f}", flush=True)
    print(f"     Δ(enr+AxS - iter34) {r['enriched'] - r['iter34']:+.3f}   "
          f"Δ(enr+AxS - iter33) {r['enriched'] - r['iter33']:+.3f}   "
          f"Δ(enr+AxS - single-flat) {r['enriched'] - r['single_flat']:+.3f}",
          flush=True)
    print(f"     AxS node: alone {r['axs_alone']:.3f}   "
          f"label-shuf {r['axs_label_shuf']:.3f}   "
          f"drop-it Δ {r['axs_drop']:+.3f}", flush=True)
    print("     per-orthogonal-cue: " + "  ".join(
        f"{n}[alone {r['ortho_alone'][n]:.3f}, "
        f"drop-it {r['enriched'] - r['leave_one_out'][n]:+.3f}]"
        for n in r['ortho_names']), flush=True)


def real_speaker_hvpt(n_per, rounds=2):
    items = gather(n_per_class_per_speaker=n_per)
    voice_audio = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        voice_audio.setdefault(s, []).append((x, fs, str(d)))
    speakers = sorted(voice_audio)
    print(f"FSDD: {sum(len(v) for v in voice_audio.values())} recordings, "
          f"{len(speakers)} speakers {speakers}", flush=True)
    print(f"gammatone channels = {len(COCHLEAR_SETTINGS)} settings x "
          f"(1 flat + {len(TRANSITION_WINDOWS)} trans) = "
          f"{len(COCHLEAR_SETTINGS)*(1+len(TRANSITION_WINDOWS))}", flush=True)
    print(f"orthogonal cues = {ORTHO_NAMES}", flush=True)
    real, shuf = [], []
    for held in speakers:
        r = score_fold(build_fold(voice_audio, held, rounds, shuffle=False))
        _report_fold(r); real.append(r)
        sr = score_fold(build_fold(voice_audio, held, rounds, shuffle=True))
        _report_fold(sr); shuf.append(sr)
    return real, shuf


def _repitch_retract(x, fs, vtl):
    if vtl == 1.0 or x.size == 0:
        return x
    n = max(1, int(round(x.size / vtl)))
    idx = np.clip((np.arange(n) * vtl).astype(int), 0, x.size - 1)
    return np.ascontiguousarray(x[idx])


def persona_hvpt(n_per, rounds=2):
    from domains.persona_speech_world import DEFAULT_PERSONAS
    held_persona = ("quinn", 150.0, 4.5, 1.25)
    personas = list(DEFAULT_PERSONAS) + [held_persona]
    items = gather(n_per_class_per_speaker=n_per)
    base = [(load_wav(p)[0], load_wav(p)[1], str(d))
            for p, d, s in items if s == "george"]
    print(f"\nPERSONA source george, {len(base)} base; personas "
          f"{[p[0] for p in personas]} (held {held_persona[0]})", flush=True)
    voice_audio = {}
    for name, f0, q, vtl in personas:
        for x, fs, word in base:
            voice_audio.setdefault(name, []).append(
                (_repitch_retract(x, fs, vtl), fs, word))
    r = score_fold(build_fold(voice_audio, held_persona[0], rounds, shuffle=False))
    _report_fold(r)
    sr = score_fold(build_fold(voice_audio, held_persona[0], rounds, shuffle=True))
    _report_fold(sr)
    return r, sr


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    print("=" * 72, flush=True)
    print("ITER-35 AxS NODE HVPT — iter-34's 23 channels + the single-pass AxS node",
          flush=True)
    print("=" * 72, flush=True)

    real, shuf = real_speaker_hvpt(n_per, rounds=rounds)
    persona, persona_shuf = persona_hvpt(n_per, rounds=rounds)

    def mean(rs, k):
        return float(np.mean([r[k] for r in rs]))

    print("\n" + "=" * 72, flush=True)
    print("VERDICT (mean over held-out voices)", flush=True)
    print("=" * 72, flush=True)

    em = mean(real, "enriched"); i34 = mean(real, "iter34"); i33 = mean(real, "iter33")
    i36 = mean(real, "iter36"); i37 = mean(real, "iter37")
    sf = mean(real, "single_flat"); fr = mean(real, "frozen")
    sem = mean(shuf, "enriched"); si34 = mean(shuf, "iter34")
    si33 = mean(shuf, "iter33"); ssf = mean(shuf, "single_flat")

    print("\nREAL-SPEAKER HVPT (LOSO over 6 FSDD speakers):", flush=True)
    print(f"  GRAPH+landmark+AxS  {em:.3f}   ({real[0]['n_many']} gammatone + "
          f"{real[0]['n_ortho']} orthogonal + 1 AxS = "
          f"{real[0]['n_many'] + real[0]['n_ortho'] + 1} channels)", flush=True)
    print(f"  iter-37 (F0+modspec, no landmark) {i37:.3f}  "
          f"=> GRAPH+landmark vs iter-37 Δ {em-i37:+.3f} "
          f"({'WIDENS' if em > i37 else 'does NOT widen'} on DIGITS)", flush=True)
    print(f"  iter-36 (3-ortho+AxS, no new) {i36:.3f}", flush=True)
    print(f"  iter-34 (no AxS)    {i34:.3f}", flush=True)
    print(f"  MANY-SETTINGS (i33) {i33:.3f}", flush=True)
    print(f"  single-setting flat {sf:.3f}", flush=True)
    print(f"  frozen              {fr:.3f}", flush=True)
    print(f"  *** GRAPH+new vs iter-36   Δ {em-i36:+.3f}  "
          f"=> {'WIDENS' if em > i36 else 'does NOT widen'} on DIGITS "
          f"(does the new richness help digits?)", flush=True)
    print(f"  *** enr+AxS vs iter-34      Δ {em-i34:+.3f}  "
          f"=> {'WIDENS' if em > i34 else 'does NOT widen'} the win", flush=True)
    print(f"  *** enr+AxS vs iter-33      Δ {em-i33:+.3f}", flush=True)
    print(f"  *** enr+AxS vs single-flat  Δ {em-sf:+.3f}  "
          f"(iter-34 was {i34-sf:+.3f})  "
          f"=> {'WIDER' if (em-sf) > (i34-sf) else 'not wider'}", flush=True)
    print(f"  *** enr+AxS vs frozen       Δ {em-fr:+.3f}", flush=True)

    print("\n  SHUFFLE control:", flush=True)
    print(f"  ENRICHED+AxS REAL {em:.3f}  SHUFFLE {sem:.3f}  "
          f"=> margin {em-sem:+.3f}  ({'CLEAN' if em > sem else 'NOT CLEAN'})",
          flush=True)
    print(f"  iter-34      REAL {i34:.3f}  SHUFFLE {si34:.3f}  "
          f"=> margin {i34-si34:+.3f}", flush=True)
    print(f"  iter-33      REAL {i33:.3f}  SHUFFLE {si33:.3f}  "
          f"=> margin {i33-si33:+.3f}", flush=True)
    print(f"  => enr+AxS shuffle margin {'WIDER' if (em-sem) > (i34-si34) else 'not wider'} "
          f"than iter-34 ({em-sem:+.3f} vs {i34-si34:+.3f})", flush=True)

    print("\n  AxS NODE (top-down, single-pass; diagnostic, not selection):",
          flush=True)
    axs_alone = float(np.mean([r["axs_alone"] for r in real]))
    axs_drop = float(np.mean([r["axs_drop"] for r in real]))
    axs_label = float(np.mean([r["axs_label_shuf"] for r in real]))
    print(f"    AxS  alone {axs_alone:.3f} (chance 0.100)   "
          f"label-shuf {axs_label:.3f} (mis-pointed forward model -> must collapse)   "
          f"drop-it Δ {axs_drop:+.3f}  "
          f"=> {'widens (orthogonal headroom)' if axs_drop > 0 else 'redundant/neutral'}",
          flush=True)
    print(f"    (the voice-partition shuffle does NOT bite AxS by construction — it "
          f"scrambles voice-grouping, not word identity; the AxS node's OWN control "
          f"is the label-shuffle above)", flush=True)

    print("\n  PER-ORTHOGONAL-CUE (mean over folds; diagnostic, not selection):",
          flush=True)
    for n in ORTHO_NAMES:
        alone = float(np.mean([r["ortho_alone"][n] for r in real]))
        drop = float(np.mean([r["enriched"] - r["leave_one_out"][n] for r in real]))
        print(f"    {n:18s}  alone {alone:.3f}   drop-it Δ {drop:+.3f}  "
              f"=> {'widens' if drop > 0 else 'redundant/hurts'}", flush=True)

    print("\nPERSONA HVPT (held-out persona; flat saturates, NOT authoritative):",
          flush=True)
    print(f"  ENRICHED+AxS {persona['enriched']:.3f}  iter-34 {persona['iter34']:.3f}  "
          f"iter-33 {persona['iter33']:.3f}  single-flat {persona['single_flat']:.3f}  "
          f"frozen {persona['frozen']:.3f}  (AxS alone {persona['axs_alone']:.3f})",
          flush=True)

    print("\n(enriched+AxS = iter-34's 23 channels + the single-pass AxS synth-error "
          "node, ALL combined via the agent's Argmax-of-product; the AxS node is the "
          "agent's OWNED forward model + graph DtwTo softmaxed by its own median; "
          "combine-all NOT select-best, NO convergence-fit, NO weight)", flush=True)


if __name__ == "__main__":
    main()
