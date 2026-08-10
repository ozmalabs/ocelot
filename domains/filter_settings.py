"""filter_settings — iter-33: the agent's OWN filters/transforms instantiated at
MANY SETTINGS, each a node feeding the combinatorial product.

The uncertainty principle caps ANY ONE time-frequency setting of the cochlear
front-end: sharpen time and you blur frequency, sharpen frequency and you blur
time. A graph is not stuck with one setting — it can instantiate the SAME filter
at MANY tradeoffs, each a node, and combine ALL of them (the two-ears result
generalised to N ears: scripts/two_ears_demo.py, ozma_wall_is_self_imposed).

Two filter families are instantiated at many settings here:

  · the COCHLEAR FRONT-END (the gammatone cochleagram, scripts.mine_whisper
    .gammatone_env + the duration LPF in band_trajectory_matrix) at MANY
    time-frequency tradeoffs. The tradeoff is governed by:
      - env_cut  : the hair-cell envelope LPF cutoff (Hz). HIGH = the envelope
                   follows fast amplitude change = SHARP TIME; LOW = smooth = the
                   envelope blurs time but the per-frame spectrum is cleaner.
      - dur_cut  : the sustained duration LPF cutoff (Hz) applied per band. Same
                   axis: HIGH = sharp time, LOW = smooth.
      - n_frames : the number of temporal frames the trajectory is resampled to.
                   MANY frames = fine temporal grid; FEW = coarse (more frequency
                   averaging per frame).
    SHARP-TIME, MIDDLE, and SHARP-FREQ settings are three points on this tradeoff
    (generalising the two-ears sharp-freq / gammatone pair to a spread of N).

  · the TRANSITION CHANNEL (grown_representation.transition_channel, the agent's
    order-1-over-time operator) at MANY TEMPORAL WINDOWS: the early/late split is
    the simplest window; finer N-way splits read the transition at SHORT / MEDIUM /
    LONG temporal scales (a short window catches the fast formant onset, a long
    window the slow sweep).

NO-DONKEY + THE ONE HARD RULE: these are SETTINGS of the agent's own filters,
authored from the same formulas the front-end already uses (no new fitted filter,
no optimiser). ALL of them are instantiated and ALL combined by the product — we
do NOT sweep them and keep the best (the forbidden negative-space search). The
combinatorial recognizer sorts them out.
"""
from __future__ import annotations

import math

import numpy as np

from scripts.mine_whisper import gammatone_env, BANDS


# ---------------------------------------------------------------------------
# The parametrised cochleagram — one (env_cut, dur_cut, n_frames) SETTING.
# Mirrors scripts.invariant_units_accept.band_trajectory_matrix exactly, but with
# the time-frequency tradeoff knobs exposed instead of baked.
# ---------------------------------------------------------------------------

def cochleagram(x, fs, env_cut: float = 50.0, dur_cut: float = 80.0,
                n_frames: int = 32) -> np.ndarray:
    """frames x bands gammatone cochleagram at ONE time-frequency setting.

      env_cut : hair-cell envelope LPF cutoff (Hz). Higher -> sharper time.
      dur_cut : sustained duration LPF cutoff (Hz). Higher -> sharper time.
      n_frames: temporal frames the trajectory is resampled to.

    Same front-end as band_trajectory_matrix (32 log-bands, 80..7500 Hz); the
    knobs move it along the uncertainty tradeoff. No global normalisation here.

    Transduction runs in RUST (substrate_rs._native.cochleagram); the Python here is the
    affordance handoff, with a numpy fallback if the native layer is unavailable."""
    try:
        from substrate_rs import _native
        flat = _native.cochleagram(np.asarray(x, dtype=np.float32).tolist(), int(fs),
                                   float(env_cut), float(dur_cut), int(n_frames))
        return np.asarray(flat, dtype=np.float32).reshape(int(n_frames), len(BANDS))
    except Exception:
        pass
    envs = [gammatone_env(x, fs, fc, env_cut=env_cut) for fc in BANDS]
    # sustained duration LPF per band (the same one-pole the patch path uses).
    cut = 1000.0 / (2 * math.pi * dur_cut)
    tau = 1.0 / (2 * math.pi * cut)
    a = math.exp(-1.0 / (tau * fs))
    smoothed = []
    for env in envs:
        sm = np.empty_like(env)
        acc = 0.0
        for i in range(len(env)):
            acc = a * acc + (1 - a) * env[i]
            sm[i] = acc
        smoothed.append(sm)
    n_src = len(smoothed[0])
    rows = []
    for tf in range(n_frames):
        sp = tf * n_src / n_frames
        i0 = int(sp); i1 = min(i0 + 1, n_src - 1); frac = sp - i0
        rows.append([buf[i0] * (1 - frac) + buf[i1] * frac for buf in smoothed])
    return np.array(rows, dtype=np.float32)


# ---------------------------------------------------------------------------
# The COCHLEAR SETTINGS BANK — many points on the time-frequency tradeoff.
# Each is a NODE; ALL are combined. NOT swept-and-kept-best.
#
# The middle setting (env_cut=50, dur_cut=80, n_frames=32) is exactly the
# baked-in band_trajectory_matrix — so the existing flat/trans readouts are one
# node in the bank, and the bank STRICTLY ADDS settings around it.
# ---------------------------------------------------------------------------

# (name, env_cut, dur_cut, n_frames). Spread across the uncertainty tradeoff:
#   sharp-time  : fast envelope + light duration smoothing + fine temporal grid
#   middle      : the agent's existing baked-in setting
#   sharp-freq  : slow envelope + heavy smoothing + coarse grid (cleaner spectrum)
COCHLEAR_SETTINGS: list[tuple[str, float, float, int]] = [
    ("sharp_time", 120.0, 200.0, 48),
    ("mid_time",    80.0, 120.0, 40),
    ("middle",      50.0,  80.0, 32),
    ("mid_freq",    30.0,  50.0, 24),
    ("sharp_freq",  20.0,  30.0, 16),
]


# ---------------------------------------------------------------------------
# The TRANSITION-WINDOW SETTINGS — the agent's order-1-over-time operator read at
# many temporal scales. n_windows = how many equal temporal segments the
# trajectory is split into; the transition descriptor is the segment-to-segment
# order-1 difference (n_windows=2 = the existing early/late split).
# ---------------------------------------------------------------------------

TRANSITION_WINDOWS: list[tuple[str, int]] = [
    ("trans_w2", 2),   # early/late — the existing split
    ("trans_w3", 3),   # short/medium/long thirds
    ("trans_w4", 4),   # finer temporal scale
]


def transition_multiwindow(R: np.ndarray, patches, n_windows: int = 2
                           ) -> np.ndarray:
    """The agent's order-1-over-time transition descriptor at ONE temporal-window
    setting: split the (frequency-ordered) patch-response trajectory into
    `n_windows` equal segments and take the order-1 differences between successive
    segment means (n_windows=2 reproduces grown_representation.transition_channel's
    per-channel late-early term). A short window (large n_windows) catches the fast
    formant onset; a long window (n_windows=2) the slow sweep. No fit — the agent's
    owned operator at a chosen granularity."""
    n_frames, n_patch = R.shape
    if n_frames < n_windows or n_patch < 1 or n_windows < 2:
        return np.zeros(n_patch, dtype=np.float64)
    order = np.argsort([c for c, _ in patches])
    Ro = R[:, order]
    edges = np.linspace(0, n_frames, n_windows + 1).astype(int)
    seg_means = []
    for k in range(n_windows):
        lo, hi = edges[k], max(edges[k] + 1, edges[k + 1])
        seg_means.append(Ro[lo:hi].mean(axis=0))
    # order-1 differences between successive segments, stacked -> a descriptor
    # whose length is (n_windows-1)*n_patch.
    diffs = [seg_means[k + 1] - seg_means[k] for k in range(n_windows - 1)]
    return np.concatenate(diffs).astype(np.float64)


# ---------------------------------------------------------------------------
# iter-34: the FREQ-SHARP FFT EAR — orthogonal to the gammatone BY CONSTRUCTION.
#
# The gammatone front-end (cochleagram above) is a bank of broad, ERB-spaced,
# overlapping filters with a fast hair-cell envelope — its operating point favours
# TIME resolution and blurs FREQUENCY (the uncertainty wall the iter-33 cochlear
# settings spread across). A large-window FFT is the COMPLEMENTARY operating point:
# a long analysis window over the (quasi-stationary) vowel nucleus gives FINE
# frequency resolution at coarse time. This is the two-ears result
# (scripts/two_ears_demo.py, ozma_wall_is_self_imposed) wired as a node: a second
# EAR at a different time-frequency point, not another gammatone tradeoff. Its errors
# are different in kind from the gammatone's, so it ADDS to the product rather than
# duplicating a channel already in it.
#
# Adapter-math DSP at the I/O boundary (np.fft), the SAME category as the gammatone
# front-end. No fit, no learned filter — a fixed log-frequency pooling of the FFT
# magnitude over a few temporal windows so the readout carries word identity (the
# spectral shape AND its coarse time course), not a single static spectrum.
# ---------------------------------------------------------------------------

# log-spaced frequency edges for pooling the high-resolution FFT into fixed bands.
FFT_EAR_NFFT = 4096
FFT_EAR_NBANDS = 40
FFT_EAR_LO = 150.0
FFT_EAR_HI = 3800.0
FFT_EAR_NWIN = 3          # coarse temporal windows over the utterance


def _fft_log_edges(nbands: int = FFT_EAR_NBANDS) -> np.ndarray:
    return np.exp(np.linspace(math.log(FFT_EAR_LO), math.log(FFT_EAR_HI),
                              nbands + 1))


def fft_ear(x, fs: int, nbands: int = FFT_EAR_NBANDS, nwin: int = FFT_EAR_NWIN,
            nfft: int = FFT_EAR_NFFT) -> np.ndarray:
    """The freq-sharp FFT ear's per-utterance readout: for each of `nwin` equal
    temporal windows, a long-window FFT magnitude log-pooled into `nbands`
    log-spaced frequency bands (fine frequency, coarse time — the complementary
    operating point to the gammatone). Returns a flat (nwin*nbands,) descriptor.

    Mechanical DSP (np.fft + fixed log pooling); no fit, no learned filter. Runs in RUST
    (substrate_rs._native.fft_ear); the Python is the affordance handoff + numpy fallback."""
    x = np.asarray(x, dtype=np.float64)
    try:
        from substrate_rs import _native
        return np.asarray(_native.fft_ear(x.tolist(), int(fs), int(nbands), int(nwin), int(nfft)),
                          dtype=np.float64)
    except Exception:
        pass
    edges = _fft_log_edges(nbands)
    fr = np.fft.rfftfreq(nfft, 1.0 / fs)
    bin_idx = [np.where((fr >= edges[b]) & (fr < edges[b + 1]))[0]
               for b in range(nbands)]
    n = len(x)
    out = np.zeros((nwin, nbands), dtype=np.float64)
    if n < 32:
        return out.flatten()
    bounds = np.linspace(0, n, nwin + 1).astype(int)
    for wi in range(nwin):
        lo, hi = bounds[wi], max(bounds[wi] + 1, bounds[wi + 1])
        seg = x[lo:hi]
        if seg.size < 16:
            continue
        win = np.hanning(seg.size)
        mag = np.abs(np.fft.rfft(seg * win, n=nfft))
        for b in range(nbands):
            idx = bin_idx[b]
            out[wi, b] = np.log(mag[idx].mean() + 1e-8) if idx.size else -18.0
    return out.flatten()


__all__ = ["cochleagram", "COCHLEAR_SETTINGS", "TRANSITION_WINDOWS",
           "transition_multiwindow", "fft_ear", "FFT_EAR_NBANDS",
           "FFT_EAR_NWIN"]
