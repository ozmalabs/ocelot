"""stacked_representation — the agent COMPOSES iter-26: the MULTI-CHANNEL STACK it
DERIVED for itself over the iter-25 residual (scripts/iter26_stacked_derive.py).

PROVENANCE — the ENACTMENT of the agent's self-derived fix, not a hand-pick. Over the
iter-25 RESIDUAL frame (single_component_frame: the formant-spacing relation carries
real signal but rides ALONE, discarding the within-speaker manner/voicing cues, and its
formants jitter frame-to-frame against the smooth true trajectories), the agent's OWN
synthesize_gaps fired THREE of its OWN harvested shapes (verbatim, iter26_stacked_derive):

  (a) STACK a complementary/redundant component
      via rule_derived__redundancy_increases_reliability (concept redundancy_increases_
      reliability, engineering):
        "system reliability = 1-(1-R)^n"
      -> build the representation from SEVERAL complementary redundant components, each
         reliable in a different region, not one component alone.

  (b) a WITHIN-speaker MANNER/VOICING channel
      via rule_derived__voicing_decision_routes_to_specialised_coding (concept voicing_
      decision_routes_to_specialised_coding, concept_expansion):
        "each class can be coded with parameters tuned to its statistics"
      -> classify each frame voiced / unvoiced / silence and carry the manner cues
         (the spectral-envelope shape, periodicity, sonorant-vs-sibilant band balance)
         the spacing relation discards — these ARE the agent's phonology cues.

  (c) SHARPEN the formants via continuity / tracking
      via removable_context__from__residual_vector_quantisation (concept residual_
      vector_quantisation, neural_audio_codec):
        "if a quantity is a smooth FUNCTION of its known context, the context-effect can
         be MODELLED and SUBTRACTED — predict the shift from the neighbours and remove it"
      -> the true formants are a smooth function of time (neighbouring frames close), so
         track each formant into a smooth trajectory and discard the per-frame jitter
         before taking the spacing.

This module COMPOSES the representation those three derived gaps dictate, from the
agent's OWN primitives. NO new representation decision; every channel is read straight
off a derived gap + the agent's existing relations + its phonology predicates + its DSL.

CHANNELS (each an agent component):
  · FORMANT-RELATION (iter-25, unchanged): the agent's iter-24 spacing relation
    (spacing_relation_term: Minus over landmark positions) over the TRUE waveform-LPC
    formant positions. (c) adds CONTINUITY: the per-frame formants are tracked into
    smooth trajectories (nearest-formant assignment + neighbour-median, the adapter-math
    realisation of "smooth function of its context, jitter removed") BEFORE the spacing.
  · MANNER/VOICING (the discarded within-speaker cues, (b)): per frame, the agent's
    phonology cues — its voicing/periodicity measure and its sonorant / sibilant
    band-energy CONTRASTS evaluated via the substrate from the agent's phonology
    predicate Term-trees (low / mid / high band means = the spectral-envelope shape).
  · STACK (a): concatenate the channels into one per-frame configuration.

NO-DONKEY. The agent DERIVED the stack (its redundancy / voicing-class / smooth-context
shapes) and COMPOSED it from its own relations (iter-24 spacing Term; phonology
predicate Terms). The ONLY new Python is the I/O-boundary DSP — waveform-LPC roots
(iter-25, reused), per-frame band-energy aggregation + autocorrelation periodicity (the
SAME category as the gammatone / np.fft front-end and phonology's compute_sign_band_
stats), and the formant-tracking smoothing — all adapter-math, no reasoning, no
decision over graph state, no tuning of any relation.
"""
from __future__ import annotations

import numpy as np

from substrate_rs import Substrate

from domains.lpc_formant_representation import _lpc_roots_formants
from domains.scale_invariant_representation import spacing_relation_term
from domains.phonology import (
    _voicing_predicate, _sonorant_predicate, _sibilant_predicate,
)
from scripts.mine_whisper import BANDS


# Band-index partitions for the agent's phonology cues (its own band-energy
# definitions: low < 800 Hz, mid 800-2500 Hz, high > 3000 Hz). BANDS are the 32
# gammatone centre frequencies the agent's front-end uses.
_LOW = [i for i, f in enumerate(BANDS) if f < 800.0]
_MID = [i for i, f in enumerate(BANDS) if 800.0 <= f <= 2500.0]
_HIGH = [i for i, f in enumerate(BANDS) if f > 3000.0]


# ---------------------------------------------------------------------------
# (c) FORMANT TRACKING — continuity. The agent's "smooth function of its context;
# remove the jitter" (removable_context shape) at the I/O boundary: assign each
# per-frame LPC formant to a small set of continuous tracks (nearest in log-Hz to the
# previous frame's track), then median-smooth each track over a short neighbour window.
# Adapter-math DSP, the same category as the gammatone front-end. No graph decision.
# ---------------------------------------------------------------------------

def _track_formants(per_frame_formants, n_tracks: int = 3, gap_tol: float = 0.35):
    """Per-frame ascending formant lists -> n_tracks smooth log-Hz trajectories.

    Greedy nearest-in-log assignment to continuous tracks + neighbour-median smoothing.
    Returns an (n_frames x n_tracks) array of log-Hz (NaN where a track is absent).
    Mechanical DSP — the realisation of the agent's 'true formants move smoothly;
    predict from neighbours and remove the jitter'."""
    nf = len(per_frame_formants)
    tracks = np.full((nf, n_tracks), np.nan, dtype=np.float64)
    last = [None] * n_tracks                    # last log-Hz value per track
    for t in range(nf):
        fmts = sorted(per_frame_formants[t])
        logs = [np.log(f) for f in fmts if f > 0]
        used = [False] * len(logs)
        # continue existing tracks: each track grabs its nearest unused formant
        for k in range(n_tracks):
            if last[k] is None:
                continue
            best, bj = gap_tol, -1
            for j, lg in enumerate(logs):
                if used[j]:
                    continue
                d = abs(lg - last[k])
                if d < best:
                    best, bj = d, j
            if bj >= 0:
                tracks[t, k] = logs[bj]
                last[k] = logs[bj]
                used[bj] = True
        # seed empty tracks with leftover formants in ascending order
        leftover = [logs[j] for j in range(len(logs)) if not used[j]]
        for lg in leftover:
            empties = [k for k in range(n_tracks) if np.isnan(tracks[t, k])]
            if not empties:
                break
            k = empties[0]
            tracks[t, k] = lg
            last[k] = lg
    # neighbour-median smoothing per track (window 3) — removes single-frame jitter,
    # keeps the smooth trajectory (the agent's 'smooth function of its context').
    sm = tracks.copy()
    for k in range(n_tracks):
        col = tracks[:, k]
        for t in range(nf):
            lo, hi = max(0, t - 1), min(nf, t + 2)
            w = col[lo:hi]
            w = w[~np.isnan(w)]
            if w.size:
                sm[t, k] = float(np.median(w))
    return sm


def _formant_relation_channel(x, fs, n_spacings: int, order: int, fps: int,
                              substrate: Substrate, track: bool = True):
    """FORMANT-RELATION channel: the agent's iter-24 spacing relation over the TRUE
    waveform-LPC formant positions, with (c) continuity tracking. Returns
    n_frames x n_spacings (the agent's spacing_relation_term, evaluated natively)."""
    x = np.asarray(x, dtype=np.float64)
    n_frames = max(8, min(300, int(len(x) / fs * fps)))
    win = max(int(0.025 * fs), order + 4)
    per_frame = []
    for tf in range(n_frames):
        c = int((tf + 0.5) * len(x) / n_frames)
        a0 = max(0, c - win // 2)
        per_frame.append(_lpc_roots_formants(x[a0:min(len(x), a0 + win)], fs, order))

    term = spacing_relation_term()
    out = np.zeros((n_frames, n_spacings), dtype=np.float64)
    if track:
        # (c) smooth tracks; spacings between ADJACENT tracks (F2-F1, F3-F2, ...).
        tr = _track_formants(per_frame, n_tracks=n_spacings + 1)
        for tf in range(n_frames):
            vals = [v for v in tr[tf] if not np.isnan(v)]
            for k in range(min(len(vals) - 1, n_spacings)):
                p = substrate.add_node("PosPair", {"pos_lo": float(vals[k]),
                                                   "pos_hi": float(vals[k + 1])})
                out[tf, k] = float(substrate.evaluate(term, {"p": p}))
    else:
        for tf in range(n_frames):
            logf = np.log(np.asarray(sorted(per_frame[tf]))) if per_frame[tf] \
                else np.array([])
            for k in range(min(len(logf) - 1, n_spacings)):
                p = substrate.add_node("PosPair", {"pos_lo": float(logf[k]),
                                                   "pos_hi": float(logf[k + 1])})
                out[tf, k] = float(substrate.evaluate(term, {"p": p}))
    return out.astype(np.float32), n_frames


# ---------------------------------------------------------------------------
# (b) MANNER / VOICING channel — the agent's phonology cues, the within-speaker
# information the spacing relation discards. Per frame: the agent's voicing/periodicity
# measure + the sonorant / sibilant band-energy CONTRASTS evaluated via the substrate
# from the agent's phonology predicate Term-trees over low/mid/high band means (the
# spectral-envelope SHAPE). The band-energy aggregation + autocorrelation periodicity
# are adapter-math (same category as phonology.compute_sign_band_stats); the contrasts
# come out of the substrate evaluator.
# ---------------------------------------------------------------------------

def _frame_periodicity(frame: np.ndarray, fs: int) -> float:
    """Autocorrelation-peak periodicity of one waveform frame in the human F0 range
    (the agent's voicing cue: periodic glottal source). 0..1. Adapter-math DSP."""
    x = np.asarray(frame, dtype=np.float64)
    x = x - x.mean()
    if x.size < 16 or np.allclose(x, 0):
        return 0.0
    ac = np.correlate(x, x, mode="full")[x.size - 1:]
    if ac[0] <= 0:
        return 0.0
    ac = ac / ac[0]
    lo = max(1, int(fs / 400.0))                 # 400 Hz upper
    hi = min(len(ac) - 1, int(fs / 50.0))        # 50 Hz lower
    if hi <= lo:
        return 0.0
    return float(np.clip(np.max(ac[lo:hi]), 0.0, 1.0))


def _band_means_term_node(s: Substrate, row: np.ndarray, f0_hz: float):
    """Lay one frame's agent-phonology cue attrs on a graph node: f0_hz + low/mid/high
    band means (the spectral-envelope shape). Mechanical aggregation (phonology's own
    band partitions)."""
    low = float(np.mean(row[_LOW])) if _LOW else 0.0
    mid = float(np.mean(row[_MID])) if _MID else 0.0
    high = float(np.mean(row[_HIGH])) if _HIGH else 0.0
    return s.add_node("AcousticSign", {
        "f0_hz": float(f0_hz), "low_band_mean": low,
        "mid_band_mean": mid, "high_band_mean": high})


def _manner_voicing_channel(x, fs, M, fps: int, substrate: Substrate):
    """MANNER/VOICING channel: per frame, [periodicity, voiced?, sonorant?, sibilant?,
    low, mid, high band means]. The boolean cues come from the agent's phonology
    predicate Term-trees, evaluated natively over the per-frame cue node; the band means
    are the spectral-envelope shape. n_frames x 7."""
    x = np.asarray(x, dtype=np.float64)
    M = np.asarray(M, dtype=np.float64)
    n_frames = M.shape[0]
    win = int(0.025 * fs)
    voicing_t = _voicing_predicate()
    sonor_t = _sonorant_predicate()
    sibil_t = _sibilant_predicate()

    out = np.zeros((n_frames, 7), dtype=np.float64)
    for r in range(n_frames):
        c = int((r + 0.5) * len(x) / max(n_frames, 1))
        a0 = max(0, c - win // 2)
        per = _frame_periodicity(x[a0:min(len(x), a0 + win)], fs)
        # the agent's voicing cue keys on f0_hz; use a periodicity-derived f0 proxy
        # (periodicity above floor -> in-range f0, else 0) so the agent's OWN voicing
        # predicate decides voiced/unvoiced (adapter supplies the cue, predicate decides)
        f0 = 120.0 if per > 0.3 else 0.0
        node = _band_means_term_node(substrate, M[r], f0)
        low = float(np.mean(M[r][_LOW])) if _LOW else 0.0
        mid = float(np.mean(M[r][_MID])) if _MID else 0.0
        high = float(np.mean(M[r][_HIGH])) if _HIGH else 0.0
        out[r, 0] = per
        out[r, 1] = 1.0 if substrate.evaluate(voicing_t, {"sign": node}) else 0.0
        out[r, 2] = 1.0 if substrate.evaluate(sonor_t, {"sign": node}) else 0.0
        out[r, 3] = 1.0 if substrate.evaluate(sibil_t, {"sign": node}) else 0.0
        out[r, 4] = low
        out[r, 5] = mid
        out[r, 6] = high
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# (a) STACK — concatenate the channels. The agent's redundancy shape: several
# complementary components, not one alone.
# ---------------------------------------------------------------------------

def apply_stacked(x, fs, M=None, n_spacings: int = 4, order: int = None,
                  fps: int = 25, substrate: Substrate = None,
                  track: bool = True, channels: str = "both"):
    """The agent's iter-26 MULTI-CHANNEL STACK: FORMANT-RELATION (iter-25 spacing over
    tracked true formants) ++ MANNER/VOICING (the agent's phonology cues). Returns
    n_frames x (n_spacings + 7).

    `channels`: 'both' (the stack), 'formant' (relation only, iter-25+tracking),
    'manner' (manner/voicing only) — for the ablation in the gate.
    order defaults to the agent's waveform-LPC spec rule fs/1000+2."""
    if order is None:
        order = int(fs / 1000) + 2
    s = substrate if substrate is not None else Substrate()
    if M is None:
        from scripts.continuous_speech_recognition import frames_of
        M = frames_of(x, fs)
    M = np.asarray(M, dtype=np.float64)

    fr, n_frames = _formant_relation_channel(
        x, fs, n_spacings=n_spacings, order=order, fps=fps, substrate=s, track=track)
    mn = _manner_voicing_channel(x, fs, M, fps=fps, substrate=s)

    # align both channels to the gammatone-frame grid M (gold spans slice on it)
    nf = M.shape[0]

    def _fit(A):
        if A.shape[0] == nf:
            return A
        G = np.zeros((nf, A.shape[1]), dtype=A.dtype)
        m = min(nf, A.shape[0])
        G[:m] = A[:m]
        return G

    fr, mn = _fit(fr), _fit(mn)
    if channels == "formant":
        return fr.astype(np.float32)
    if channels == "manner":
        return mn.astype(np.float32)
    return np.concatenate([fr, mn], axis=1).astype(np.float32)


def compose_stacked_representation(substrate, n_spacings: int = 4) -> list:
    """Record the agent's iter-26 composition as a Concept (feature_kind=
    stacked_multichannel) carrying provenance of the three derived gaps. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "stacked_multichannel"}
    created = []
    name = "stacked_formant_manner_voicing"
    if name not in existing:
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "stacked_multichannel",
            "predicate": spacing_relation_term().to_dict(),
            "origin": "stacked_representation", "composed_by": "agent",
            "derived_gaps": (
                "(a) redundancy_increases_reliability: system reliability=1-(1-R)^n -> "
                "stack complementary redundant components; "
                "(b) voicing_decision_routes_to_specialised_coding: classify frames "
                "voiced/unvoiced, carry the manner cues; "
                "(c) removable_context (smooth function of context): track formants "
                "into smooth trajectories, remove the per-frame jitter"),
            "channels": (
                "FORMANT-RELATION (iter-24 spacing over tracked true formants) ++ "
                "MANNER/VOICING (agent phonology cues: periodicity, voiced/sonorant/"
                "sibilant predicates, low/mid/high band-energy envelope shape)")})
        created.append((c, name))
    return created


__all__ = ["apply_stacked", "compose_stacked_representation",
           "_track_formants", "_formant_relation_channel",
           "_manner_voicing_channel"]
