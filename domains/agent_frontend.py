"""agent_frontend — the agent's FRONT END as a GRAPH-RESIDENT, AGENT-MODIFIABLE
structure (the audio hat the agent owns and self-designs).

THE MOVE (ozma_wall_is_self_imposed): the feature extraction is not a fixed Python
function — it is a graph the agent READS and MODIFIES. A FrontEnd node OWNS a set of
Cue nodes; each Cue carries `active` (gated in / out) and its DSP parameters. The
agent's perception of a clip is the L2 feature-space readout of EVERY active cue,
in graph order — so changing the graph changes what the agent hears.

The agent can do three things to its own front end, all GRAPH-RESIDENT decisions and
all COMPOSABLE DSP (no fit, no trained net, no donkey):

  · ADD a cue / ear  — flip an inactive Cue's `active` to 1 (gate in a banked cue:
    formant_relation / manner_voicing / f0_contour / modspec / landmark; or a new
    cochlear EAR at a different time-frequency tradeoff — the two-ears -> many-ears
    move). The cue's extractor is owned DSP already proven in enriched_hvpt_accept.
  · TUNE a parameter — change a Cue's param attr (e.g. a cochlear ear's env_cut /
    n_frames, the all-pole order, an FFT window). The extractor reads the attr.
  · INVENT a cue     — compose a NOVEL band-combination Term over the cochleagram
    (feature_generator's generative grammar), mint it as a Cue with a stored
    predicate, gate it in. Its readout is the per-frame Term value trajectory.

Each cue is ONE node in the agent's many-settings Argmax-of-product recognizer
(many_settings_recognizer): a fixed-length L2 descriptor -> cosine 1-NN exemplar
evidence -> softmax by its own median -> one item in the combine-all product. The
recognition decision Term is UNCHANGED; adding a cue adds a factor to the product.

ARCHITECTURE (CLAUDE.md): the EXTRACTORS are I/O-boundary DSP (np.fft / gammatone /
Levinson — the same category as the existing front end). The CONFIG is graph data;
WHICH cues fire + their params live in the substrate, read by the adapter. The
WHAT-TO-MODIFY decision is a graph Term (pick_frontend_mod, an Argmax), not a Python
branch. The adapter only enacts the chosen modification (flip an attr / mint a node).
"""
from __future__ import annotations

import numpy as np

from domains.filter_settings import (cochleagram, COCHLEAR_SETTINGS, fft_ear,
                                      TRANSITION_WINDOWS, transition_multiwindow)
from domains.allpole_spectral_envelope import allpole_ear
from domains.grown_representation import seed_patches, bands_to_patches
import scripts.enriched_hvpt_accept as ENR
from substrate_rs import (Attr, Lit, Var, Argmax, Plus, Minus, Max, Div)
import domains.feature_generator as FG


# ---------------------------------------------------------------------------
# The CUE REGISTRY — every front-end element the agent can gate in. Each entry is
# pure I/O-boundary DSP the agent already OWNS (proven in enriched_hvpt_accept).
# The registry maps a cue's `extractor` attr to the function; the cue's params are
# read off the graph node so the agent can TUNE them.
#
# A cue extractor takes (x, fs, M, attrs) and returns an L2-normalised vector:
#   x    : the waveform
#   fs   : sample rate
#   M    : the middle-setting cochleagram (frames x bands), shared (cheap reuse)
#   attrs: the Cue node's attrs (its tunable parameters)
# ---------------------------------------------------------------------------

_MIDDLE = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
_SEED_PATCHES = seed_patches()


def _l2(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


# ---------------------------------------------------------------------------
# Stage-0 hand-off (docs/stage0_transduction.md (3)): the standing recognition
# cue extractors must read the agent's OWN NATIVE all-pole formant chain
# (Stage-0 / W1 / Gap 2: substrate_rs._native.lpc_roots_formants — autocorr ->
# Levinson-Durbin -> roots of A(z) -> pole-angle Hz, owned in Rust), NOT the
# Python DSP that lived in domains/lpc_formant_representation. The native chain
# was proven bit-faithful to the Python oracle (Stage-0 gate: 0.005 Hz max drift
# over 274 real FSDD frames). This is a MECHANICAL re-point — same formant
# structure, now owned in-substrate, composable/gateable. No new capability.
# ---------------------------------------------------------------------------

def _native_lpc_roots_formants(seg, fs, order, pre_emph=0.97,
                               f_lo=150.0, f_hi=3600.0, bw_max=500.0):
    """One raw-waveform frame -> ascending formant Hz, via the agent's OWNED
    NATIVE all-pole chain (the Stage-0 hand-off). Thin one-line boundary call
    into Rust; the native primitive does pre-emphasis + window + autocorr +
    Levinson-Durbin + Durand-Kerner root-find + pole->Hz internally (so we feed
    the RAW frame, matching scripts/stage0_native_formant_check.py)."""
    import substrate_rs
    seg = np.asarray(seg, dtype=np.float64)
    if len(seg) < int(order) + 2:
        return []
    return list(substrate_rs._native.lpc_roots_formants(
        seg.astype(np.float32).tolist(), int(fs), int(order),
        float(pre_emph), float(f_lo), float(f_hi), float(bw_max)))


# ---------------------------------------------------------------------------
# CENTER-SURROUND SALIENCE on the cochleagram (the analogical transfer of the
# retina/LGN center-surround into the auditory front end — ozma_analogical_transfer:
# vision center-surround "x minus its surround" -> speech spectro-temporal contrast).
#
# Each time-frequency point is re-expressed RELATIVE to a local SURROUND: a
# difference-of-Gaussians (center blur minus a wider surround blur) over the
# spectro-temporal neighbourhood of the (frames x bands) cochleagram. The output is
# the SIGNED contrast/salience map, NOT the absolute energy:
#
#   (a) LOCAL CONTRAST NORMALIZER — subtracting the local surround mean cancels the
#       slowly-varying speaker-common offsets (global spectral tilt, level, the slow
#       envelope the VTL shift rides on), which are LOW spatial frequency in the
#       cochleagram and so live in the surround blur. The contrast survives.
#   (b) SALIENCE filter — it amplifies what STANDS OUT against its neighbourhood
#       (formant peaks, spectral edges, onsets — the phonetic information) and zeroes
#       the flat speaker-specific background (blurred away by both Gaussians).
#
# Pure composable boundary DSP — separable Gaussian smoothing (a convolution the
# agent owns, the SAME center-surround DoG the vision front end uses) and a
# subtraction. NO fit, NO trained net, NO searched param: the surround width is a
# small fixed set reported in the ablation; sigma_center is fixed at 1 cell.
# ---------------------------------------------------------------------------

def _gauss1d(sigma):
    """A normalised 1-D Gaussian kernel (radius 3 sigma) — the agent's owned blur."""
    if sigma <= 1e-6:
        return np.array([1.0], dtype=np.float64)
    r = max(1, int(round(3.0 * sigma)))
    t = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-(t * t) / (2.0 * sigma * sigma))
    return k / k.sum()


def _smooth_axis(M, sigma, axis):
    """Separable Gaussian smoothing of M along one axis (reflect padding so edges
    are not darkened). A 1-D convolution per line — owned DSP."""
    k = _gauss1d(sigma)
    if k.size == 1:
        return M.astype(np.float64)
    r = k.size // 2
    M = np.asarray(M, dtype=np.float64)
    Mt = M if axis == 0 else M.T
    pad = np.pad(Mt, ((r, r), (0, 0)), mode="reflect")
    out = np.empty_like(Mt)
    for j in range(Mt.shape[1]):
        out[:, j] = np.convolve(pad[:, j], k, mode="valid")
    return out if axis == 0 else out.T


def center_surround(M, sigma_t_c=0.0, sigma_f_c=1.0,
                    sigma_t_s=0.0, sigma_f_s=4.0):
    """Center-surround (difference-of-Gaussians) contrast on a frames x bands
    cochleagram. center = M blurred at the (small) center sigmas; surround = M blurred
    at the (wider) surround sigmas; output = center - surround (the SIGNED salience).

      sigma_*_c : center blur sigma (time / frequency). 0 = no center blur (the raw
                  point is the center — the sharpest center-surround).
      sigma_*_s : surround blur sigma (time / frequency). The neighbourhood the point
                  is normalised AGAINST. Larger = wider surround.

    FREQUENCY-ONLY surround: sigma_t_s = 0 (contrast across bands at each frame —
    the spectral-edge / formant-peak detector). SPECTRO-TEMPORAL: sigma_t_s > 0 too
    (also normalises against the temporal neighbourhood — onsets/offsets). Separable
    Gaussian convolutions + a subtraction; the agent's owned DSP, no fit."""
    M = np.asarray(M, dtype=np.float64)
    if M.size == 0:
        return M
    center = M
    if sigma_t_c > 0:
        center = _smooth_axis(center, sigma_t_c, axis=0)
    if sigma_f_c > 0:
        center = _smooth_axis(center, sigma_f_c, axis=1)
    surround = M
    if sigma_t_s > 0:
        surround = _smooth_axis(surround, sigma_t_s, axis=0)
    if sigma_f_s > 0:
        surround = _smooth_axis(surround, sigma_f_s, axis=1)
    return center - surround


def _cochlear_ear(x, fs, M, attrs):
    """A gammatone EAR at a chosen time-frequency tradeoff (env_cut / dur_cut /
    n_frames). The flat patch readout of the cochleagram at THIS ear's setting —
    the two-ears -> many-ears move (each ear a different uncertainty operating
    point). Params read off the graph node so the agent can TUNE the tradeoff."""
    env_cut = float(attrs.get("env_cut", _MIDDLE[1]))
    dur_cut = float(attrs.get("dur_cut", _MIDDLE[2]))
    n_frames = int(attrs.get("n_frames", _MIDDLE[3]))
    Me = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    mu = Me.mean(axis=0, keepdims=True)
    return _l2(bands_to_patches(Me - mu, _SEED_PATCHES).flatten())


def _fft_ear(x, fs, M, attrs):
    """The freq-sharp FFT ear (complementary time-frequency operating point)."""
    nwin = int(attrs.get("nwin", 3))
    nbands = int(attrs.get("nbands", 40))
    return _l2(fft_ear(x, fs, nbands=nbands, nwin=nwin))


def _cmvn_ear(x, fs, M, attrs):
    """SOURCE-NORMALIZED cochlear ear — per-utterance CMVN (Cepstral/cochleagram
    Mean-Variance Normalization). The seed gammatone ear subtracts the per-band MEAN
    only (channel/loudness term); CMVN additionally divides by the per-band STD, so a
    speaker's per-band gain/level offsets cancel. This is the front-end source
    normalization the physics-model LOSO run isolated as the cross-speaker lever
    ("CMVN over the cochleagram"): make a clip's representation depend on its SHAPE,
    not its source-dependent per-band level. Composable boundary DSP, NO fit."""
    env_cut = float(attrs.get("env_cut", _MIDDLE[1]))
    dur_cut = float(attrs.get("dur_cut", _MIDDLE[2]))
    n_frames = int(attrs.get("n_frames", _MIDDLE[3]))
    Me = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    mu = Me.mean(axis=0, keepdims=True)
    sd = Me.std(axis=0, keepdims=True)
    Mn = (Me - mu) / (sd + 1e-6)              # per-band mean AND variance normalised
    return _l2(bands_to_patches(Mn, _SEED_PATCHES).flatten())


def _cs_ear(x, fs, M, attrs):
    """CENTER-SURROUND SALIENCE ear — the analogical-transfer cue (vision DoG ->
    auditory contrast). The cochleagram re-expressed as its signed center-surround
    contrast map (each time-freq point minus its local spectro-temporal surround),
    then read out through the SAME A1 patch bank as the gammatone ear so it drops into
    the recognizer with the identical descriptor shape. The local-contrast cancels the
    slow speaker-common offsets (tilt/level/VTL envelope) and amplifies the salient
    phonetic structure (formant peaks, edges). Surround widths read off the node attrs
    so the agent can TUNE / ablate (frequency-only vs spectro-temporal). Owned DSP
    (separable Gaussian convolution + subtract), NO fit, NO net."""
    env_cut = float(attrs.get("env_cut", _MIDDLE[1]))
    dur_cut = float(attrs.get("dur_cut", _MIDDLE[2]))
    n_frames = int(attrs.get("n_frames", _MIDDLE[3]))
    sft_s = float(attrs.get("sigma_t_s", 0.0))      # default frequency-only surround
    sff_s = float(attrs.get("sigma_f_s", 4.0))
    sft_c = float(attrs.get("sigma_t_c", 0.0))
    sff_c = float(attrs.get("sigma_f_c", 1.0))
    Me = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    Cs = center_surround(Me, sigma_t_c=sft_c, sigma_f_c=sff_c,
                         sigma_t_s=sft_s, sigma_f_s=sff_s)
    return _l2(bands_to_patches(Cs, _SEED_PATCHES).flatten())


def cs_track(x, fs, attrs=None):
    """The CENTER-SURROUND contrast cochleagram as an ORDERED per-frame trajectory
    (frames x bands), the analogue of cmvn_track for the DTW recognizer. The same
    signed center-surround salience map, kept as an ordered sequence of per-frame band
    vectors (each L2-normalised so the DTW frame-distance is on the contrast SHAPE) so
    a DTW alignment matches the salient spectral GESTURE as a path. Owned DSP; NO fit."""
    attrs = attrs or {}
    x = np.asarray(x, dtype=np.float64)
    env_cut = float(attrs.get("env_cut", _MIDDLE[1]))
    dur_cut = float(attrs.get("dur_cut", _MIDDLE[2]))
    n_frames = int(attrs.get("n_frames", _MIDDLE[3]))
    sft_s = float(attrs.get("sigma_t_s", 0.0))
    sff_s = float(attrs.get("sigma_f_s", 4.0))
    sft_c = float(attrs.get("sigma_t_c", 0.0))
    sff_c = float(attrs.get("sigma_f_c", 1.0))
    Me = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    if Me.size == 0:
        return []
    Cs = center_surround(Me, sigma_t_c=sft_c, sigma_f_c=sff_c,
                         sigma_t_s=sft_s, sigma_f_s=sff_s)
    out = []
    for r in range(Cs.shape[0]):
        v = Cs[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


def _vtl_formant(x, fs, M, attrs):
    """The agent's VTL-INVARIANT formant readout (domains/speaker_norm): the formant
    bins F1..F3 estimated per frame as ArgMax over log-ordered cochlear bands, each
    re-expressed as F_i - mean(F1,F2,F3). A speaker's vocal-tract-length scales all
    formants by a factor; on the log-band axis that is a constant SHIFT, so subtracting
    the per-frame mean formant cancels the speaker term, leaving the VTL-invariant
    pattern (ozma_speaker_normalization). The vtl_terms are the agent's OWN composed
    graph Term-trees; here we evaluate them per frame over the cochleagram band attrs
    and flatten to a fixed-length descriptor. Boundary evaluation of the agent's Term;
    NO fit, NO trained net."""
    import domains.speaker_norm as SN
    res = M.shape[1]
    terms = [SN._Pred(t) for t in SN.vtl_terms(res)]
    sub, sign = _band_substrate()
    n_out = int(attrs.get("n_out", 24))
    rows = []
    step = max(1, M.shape[0] // n_out)
    for r in range(0, M.shape[0], step):
        for j in range(res):
            sub.set_attr(sign, f"band{res}_{j}", float(M[r, j]))
        vals = []
        for t in terms:
            try:
                v = sub.evaluate(t, {"s": sign})
                vals.append(float(v) if isinstance(v, (int, float)) else 0.0)
            except Exception:
                vals.append(0.0)
        rows.append(vals)
    if not rows:
        return _l2(np.zeros(3 * n_out, dtype=np.float64))
    arr = np.asarray(rows, dtype=np.float64)              # frames x 3
    # resample each formant track to n_out and flatten -> fixed-length descriptor.
    out = []
    for k in range(arr.shape[1]):
        col = arr[:, k]
        idx = np.linspace(0, col.size - 1, n_out)
        out.append(np.interp(idx, np.arange(col.size), col))
    return _l2(np.concatenate(out))


def _vtl_formant_allpole(x, fs, M, attrs):
    """The VTL-INVARIANT formant readout over the agent's SHARP ALL-POLE formants.

    Same VTL normalization as `_vtl_formant` (F_i - mean(F1..F3) cancels the
    vocal-tract-length shift), but the formant positions come from the agent's SHARP
    estimate — the LPC pole-angle frequencies of the raw waveform
    (lpc_formant_representation._lpc_roots_formants: autocorr -> Levinson-Durbin ->
    roots of A(z) -> pole angles*fs/2pi = formant Hz, the agent's own spec) — NOT the
    coarse gammatone ArgMax-over-log-bands the _vtl_formant cue uses. The gammatone
    formant is quantised to one of ~24-32 ERB bands (the gammatone wall) — too blurry
    for the F_i - mean ratio to be a sharp speaker-invariant. The all-pole roots
    resolve the formants at FULL waveform frequency resolution (continuous Hz), so the
    VTL ratio becomes a real cross-speaker invariant. The normalization is done in
    LOG-Hz: VTL scales formant Hz multiplicatively (F_i -> alpha*F_i), an ADDITIVE
    shift in log-Hz, which subtracting the per-frame mean log-formant cancels by
    construction (the Hz analogue of the band-index mean subtraction). Composable
    boundary DSP (the agent's owned Levinson-Durbin + root-finding); NO fit, NO net."""
    _lpc_roots_formants = _native_lpc_roots_formants   # Stage-0 hand-off: native chain
    x = np.asarray(x, dtype=np.float64)
    n_out = int(attrs.get("n_out", 24))
    n_fmt = int(attrs.get("n_formants", 3))           # F1..F3 (the vtl_terms layout)
    fps = int(attrs.get("fps", 25))
    order = attrs.get("order")
    order = int(order) if order else int(fs / 1000) + 2   # agent's spec rule (~10@8k)
    n = len(x)
    if n < 32:
        return _l2(np.zeros(n_fmt * n_out, dtype=np.float64))
    n_frames = max(8, min(300, int(n / fs * fps)))
    win = max(int(0.025 * fs), order + 4)              # 25 ms analysis window
    rows = []
    for tf in range(n_frames):
        c = int((tf + 0.5) * n / n_frames)
        a0 = max(0, c - win // 2)
        seg = x[a0:min(n, a0 + win)]
        fmts = _lpc_roots_formants(seg, fs, order)     # ascending sharp formant Hz
        if len(fmts) < 2:
            rows.append([0.0] * n_fmt)
            continue
        logf = np.log(np.asarray(fmts[:max(n_fmt, len(fmts))], dtype=np.float64))
        mean = float(logf[:n_fmt].mean()) if logf[:n_fmt].size else 0.0
        # VTL-invariant: F_i - mean(F1..F3) in log-Hz (cancels the VTL log-shift).
        vtl = [float(logf[i] - mean) if i < logf.size else 0.0 for i in range(n_fmt)]
        rows.append(vtl)
    if not rows:
        return _l2(np.zeros(n_fmt * n_out, dtype=np.float64))
    arr = np.asarray(rows, dtype=np.float64)            # frames x n_fmt
    # resample each formant track to n_out and flatten -> fixed-length descriptor
    # (the SAME fixed-length readout shape as _vtl_formant).
    out = []
    for k in range(arr.shape[1]):
        col = arr[:, k]
        idx = np.linspace(0, col.size - 1, n_out)
        out.append(np.interp(idx, np.arange(col.size), col))
    return _l2(np.concatenate(out))


def _vtl_formant_dynamic(x, fs, M, attrs):
    """The agent's DYNAMIC speaker-invariant: the ORDER-N OVER TIME of the
    VTL-normalized sharp formant track — how the formants MOVE (the coarticulation /
    transitions), not where they statically sit.

    The static VTL formant (_vtl_formant_allpole) is now exhausted on the cross-speaker
    wall (LOSO 0.410; a residual seen-vs-cross gap of +0.040 persists that is DYNAMIC —
    coarticulation / register / the WAY formants move — which no static feature can
    cancel). The articulatory GESTURE is shared across speakers even when the absolute
    formants differ by vocal-tract length: the way F2 sweeps up into a vowel is the same
    motion in every mouth, only scaled. So the order-N over time of the (already
    VTL-normalized) formant track is a RICHER, more speaker-invariant descriptor than
    the static formant level.

    Construction (graph-resident composable DSP):
      1. per-frame SHARP formants F1..F3 (Hz) from the agent's LPC pole angles
         (_lpc_roots_formants — autocorr -> Levinson-Durbin -> roots of A(z)), the SAME
         sharp estimate _vtl_formant_allpole uses;
      2. VTL-normalize in LOG-Hz: F_i - mean(F1..F3) (cancels the vocal-tract-length
         multiplicative scaling -> additive log shift), giving a per-frame log-formant
         track that is already speaker-(VTL)-invariant in level;
      3. apply the agent's OWN order-N-over-time operator (domains/order_n_concepts:
         nth_order_terms = recursive Minus over the per-frame samples) to EACH formant's
         time track. order-1 = transition velocity (the formant MOTION); order-2 =
         curvature (acceleration of the gesture). The differencing is evaluated NATIVELY
         by the substrate (the agent's order-N Term-tree runs in Rust), not numpy. Note
         the order-1 difference ALSO removes any residual per-utterance constant offset
         in the log-formant track, so the TRANSITION SHAPE is the cross-speaker
         invariant by construction.

    The order-N tracks are resampled to a fixed length and flattened to an L2 descriptor
    (the same readout shape as the other cues). `order` (1 or 2) and `n_out` are tunable
    Cue params. Composable boundary DSP (the agent's Levinson-Durbin + its order-N
    Minus-tree); NO fit, NO trained net, NO learned weight."""
    _lpc_roots_formants = _native_lpc_roots_formants   # Stage-0 hand-off: native chain
    from domains.order_n_concepts import nth_order_terms
    from substrate_rs import Attr, Var
    x = np.asarray(x, dtype=np.float64)
    n_out = int(attrs.get("n_out", 24))
    n_fmt = int(attrs.get("n_formants", 3))           # F1..F3 (vtl layout)
    order = int(attrs.get("order", 1))                # 1 = velocity, 2 = curvature
    fps = int(attrs.get("fps", 25))
    o = attrs.get("lpc_order")
    o = int(o) if o else int(fs / 1000) + 2           # agent's spec rule (~10@8k)
    n = len(x)
    if n < 32:
        return _l2(np.zeros(n_fmt * n_out, dtype=np.float64))
    n_frames = max(8, min(300, int(n / fs * fps)))
    win = max(int(0.025 * fs), o + 4)                 # 25 ms analysis window
    # ---- step 1+2: per-frame VTL-normalized log-Hz formant track (frames x n_fmt) ----
    rows = []
    for tf in range(n_frames):
        c = int((tf + 0.5) * n / n_frames)
        a0 = max(0, c - win // 2)
        seg = x[a0:min(n, a0 + win)]
        fmts = _lpc_roots_formants(seg, fs, o)        # ascending sharp formant Hz
        if len(fmts) < 2:
            rows.append([np.nan] * n_fmt)
            continue
        logf = np.log(np.asarray(fmts[:max(n_fmt, len(fmts))], dtype=np.float64))
        mean = float(logf[:n_fmt].mean()) if logf[:n_fmt].size else 0.0
        rows.append([float(logf[i] - mean) if i < logf.size else np.nan
                     for i in range(n_fmt)])
    arr = np.asarray(rows, dtype=np.float64)          # frames x n_fmt (NaN where unvoiced)
    # fill unvoiced frames so the time track is continuous for differencing (carry the
    # last voiced value forward, then backward; the order-N difference of a held value
    # is zero there — no spurious motion injected). Mechanical track conditioning.
    for k in range(arr.shape[1]):
        col = arr[:, k]
        good = ~np.isnan(col)
        if good.sum() == 0:
            arr[:, k] = 0.0
            continue
        idx = np.arange(col.size)
        arr[:, k] = np.interp(idx, idx[good], col[good])
    # ---- step 3: the agent's ORDER-N OVER TIME operator on each formant's track ----
    # build the order-N Term-tree ONCE over symbolic per-frame samples, then evaluate it
    # natively per formant by writing that formant's track into the frame attrs.
    sub, sign = _band_substrate()
    sv = Var("s")
    samples = [Attr(sv, f"ft_{t}") for t in range(arr.shape[0])]
    diff_terms = [FG._Pred(d.to_dict())
                  for d in nth_order_terms(samples, order)]   # the order-N differences
    out = []
    for k in range(arr.shape[1]):
        col = arr[:, k]
        for t in range(col.size):
            sub.set_attr(sign, f"ft_{t}", float(col[t]))
        dvals = []
        for dt in diff_terms:
            try:
                v = sub.evaluate(dt, {"s": sign})
                dvals.append(float(v) if isinstance(v, (int, float)) else 0.0)
            except Exception:
                dvals.append(0.0)
        dvals = np.asarray(dvals, dtype=np.float64)
        if dvals.size == 0:
            dvals = np.zeros(1, dtype=np.float64)
        # resample the order-N track to n_out -> fixed-length descriptor per formant
        idx = np.linspace(0, dvals.size - 1, n_out)
        out.append(np.interp(idx, np.arange(dvals.size), dvals))
    return _l2(np.concatenate(out))


def vtl_formant_track(x, fs, attrs=None):
    """The VTL-normalized sharp formant TRACK as an ORDERED per-frame sequence
    (frames x channels), NOT the L2-flattened bag the cues return.

    This is the TRAJECTORY the DTW temporal-alignment recognizer aligns: each frame
    is the VTL-normalized log-Hz formant vector [F1-mean .. F3-mean], optionally with
    order-1 velocity channels appended (the formant MOTION per frame). It reuses the
    EXACT step 1+2 of `_vtl_formant_dynamic` (the agent's sharp LPC-root formant
    estimate + the F_i - mean(F1..F3) VTL invariant in log-Hz), but keeps the frames
    ORDERED as a path instead of resampling+flattening+L2 into a per-frame bag — so a
    DTW alignment over the trajectory can match the speaker-invariant GESTURE as a
    sequence, which the bag readout destroys.

    Returns a list of frames, each a list of channel floats; unvoiced frames are
    filled by interpolation (the same mechanical track conditioning the dynamic cue
    uses). `with_velocity` (default True) appends the per-frame order-1 difference of
    each formant track as extra channels (the trajectory carries level + motion).
    Pure I/O-boundary DSP — the agent's owned Levinson-Durbin + the VTL invariant; NO
    fit, NO trained net. This is the agent's FEATURE; the recognizer that aligns it is
    the agent's graph-resident DtwTo decision."""
    _lpc_roots_formants = _native_lpc_roots_formants   # Stage-0 hand-off: native chain
    attrs = attrs or {}
    x = np.asarray(x, dtype=np.float64)
    n_fmt = int(attrs.get("n_formants", 3))
    fps = int(attrs.get("fps", 25))
    with_velocity = bool(attrs.get("with_velocity", True))
    o = attrs.get("lpc_order")
    o = int(o) if o else int(fs / 1000) + 2           # agent's spec rule (~10@8k)
    n = len(x)
    if n < 32:
        return []
    n_frames = max(8, min(300, int(n / fs * fps)))
    win = max(int(0.025 * fs), o + 4)                 # 25 ms analysis window
    rows = []
    for tf in range(n_frames):
        c = int((tf + 0.5) * n / n_frames)
        a0 = max(0, c - win // 2)
        seg = x[a0:min(n, a0 + win)]
        fmts = _lpc_roots_formants(seg, fs, o)        # ascending sharp formant Hz
        if len(fmts) < 2:
            rows.append([np.nan] * n_fmt)
            continue
        logf = np.log(np.asarray(fmts[:max(n_fmt, len(fmts))], dtype=np.float64))
        mean = float(logf[:n_fmt].mean()) if logf[:n_fmt].size else 0.0
        rows.append([float(logf[i] - mean) if i < logf.size else np.nan
                     for i in range(n_fmt)])
    arr = np.asarray(rows, dtype=np.float64)          # frames x n_fmt (NaN unvoiced)
    if arr.size == 0:
        return []
    # fill unvoiced frames so the time track is continuous (same conditioning the
    # dynamic cue uses; the difference of a held value is zero — no spurious motion).
    for k in range(arr.shape[1]):
        col = arr[:, k]
        good = ~np.isnan(col)
        if good.sum() == 0:
            arr[:, k] = 0.0
            continue
        idx = np.arange(col.size)
        arr[:, k] = np.interp(idx, idx[good], col[good])
    if with_velocity and arr.shape[0] >= 2:
        vel = np.diff(arr, axis=0)                     # order-1 over time (motion)
        vel = np.vstack([vel, vel[-1:]])               # pad to same length
        arr = np.concatenate([arr, vel], axis=1)       # [level | motion] per frame
    return [[float(v) for v in frame] for frame in arr]


def cmvn_track(x, fs, attrs=None):
    """The CMVN cochleagram as an ORDERED per-frame trajectory (frames x bands), NOT
    the L2-flattened patch bag the cmvn_ear cue returns.

    This is the RICH trajectory the DTW recognizer aligns: the SAME per-utterance
    mean-and-variance-normalized cochleagram the dominant cmvn_ear cue is built from
    (the +0.043 cross-speaker lever), but kept as an ordered sequence of per-frame
    band vectors so a DTW alignment can match the spectral GESTURE as a path. Where
    vtl_formant_track gives a thin 3-formant trajectory, this gives the full
    source-normalized spectral trajectory — the trajectory the per-frame bag already
    wins on, now aligned. Pure I/O-boundary DSP (the agent's cochleagram + CMVN); NO
    fit, NO trained net. The recognizer that aligns it is the agent's DtwTo decision."""
    attrs = attrs or {}
    x = np.asarray(x, dtype=np.float64)
    env_cut = float(attrs.get("env_cut", _MIDDLE[1]))
    dur_cut = float(attrs.get("dur_cut", _MIDDLE[2]))
    n_frames = int(attrs.get("n_frames", _MIDDLE[3]))
    Me = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    if Me.size == 0:
        return []
    mu = Me.mean(axis=0, keepdims=True)
    sd = Me.std(axis=0, keepdims=True)
    Mn = (Me - mu) / (sd + 1e-6)              # per-band mean AND variance normalised
    # per-frame L2 so the DTW frame-distance is on the spectral SHAPE, not level.
    out = []
    for r in range(Mn.shape[0]):
        v = Mn[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


def speaker_residual_track(x, fs, attrs=None):
    """The synthesize_gaps OPERATION run one scale down on the signal: OPEN A HOLE AT
    THE SPEAKER, READ THE RESIDUAL = THE WORD.

    This is the audio-state analogue of order_n_postulates.synthesize_gaps' core move
    ("open a hole in Gamma = subtract the admitted/expected, read the residual"), and
    specifically of the `context_dependence_is_a_removable_function` implication-shape:
    a quantity that is a smooth FUNCTION of its known context can be MODELLED and
    SUBTRACTED to recover the context-free target. Here the CONTEXT/admitted is the
    SPEAKER (the part of the cochleagram that is CONSTANT/consistent ACROSS the frames
    of one utterance), the TARGET/residual is the WORD (the per-frame deviation).

    The COGNITION-DRIVEN FIND (the diagnostic fix over the failed LPC peel,
    docs/order_n_peel_loso.md): the speaker is what is CONSTANT-OVER-TIME, NOT what is
    per-frame predictable. The LPC peel whitened per-frame all-pole structure and so
    peeled the word's own vowel resonances along with the speaker. Here the FIND is
    aimed instead at the WITHIN-UTTERANCE CONSISTENT structure: the low-rank spectral
    subspace shared by EVERY frame of the utterance (its mean + dominant principal
    directions over the frame matrix). That subspace is exactly "what the cognition
    predicts is the speaker" — the per-utterance constant. Subtract it from each frame;
    the residual is the per-frame deviation = the articulatory word motion.

    Owned linear algebra ONLY (the donkey boundary): per-utterance MEAN + a top-k SVD
    over the (frames x bands) cochleagram, projection-subtract. No fit, no net, no
    learned weight, NO speaker labels — the SVD is the closed-form principal subspace
    of THIS utterance's own frames, computed per-utterance and applied per-utterance,
    so there is NO cross-utterance leakage. k = number of consistent components removed
    (k>=1 includes the mean direction; the hole's WIDTH). Returns the residual as an
    ORDERED per-frame trajectory (frames x bands), the same shape cmvn_track returns,
    so the agent's graph-resident DtwTo recognizer aligns it unchanged."""
    attrs = attrs or {}
    x = np.asarray(x, dtype=np.float64)
    env_cut = float(attrs.get("env_cut", _MIDDLE[1]))
    dur_cut = float(attrs.get("dur_cut", _MIDDLE[2]))
    n_frames = int(attrs.get("n_frames", _MIDDLE[3]))
    k = int(attrs.get("k", 1))                 # width of the hole (consistent comps)
    Me = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    if Me.size == 0:
        return []
    # per-band variance normalise first (level/gain per band is itself speaker scale),
    # the SAME source-normalisation cmvn_track applies — so the residual is read on the
    # source-normalised cochleagram, not raw band energy.
    sd = Me.std(axis=0, keepdims=True)
    Mz = Me / (sd + 1e-6)                        # frames x bands, per-band unit-var
    # OPEN THE HOLE AT THE SPEAKER = the within-utterance CONSTANT subspace.
    #   • the per-utterance MEAN frame (the rank-0 constant: what every frame shares).
    mu = Mz.mean(axis=0, keepdims=True)
    C = Mz - mu                                 # frames x bands, centred
    #   • the top-(k-1) PRINCIPAL DIRECTIONS of the centred frame matrix = the
    #     remaining structure that is CONSISTENT across the utterance (a speaker
    #     formant-space basis), via the utterance's OWN SVD. k=1 => mean only.
    R = C
    n_pc = max(0, k - 1)
    if n_pc > 0 and C.shape[0] > 1 and C.shape[1] > 1:
        try:
            # right singular vectors V: band-space directions consistent over frames.
            _U, _S, Vt = np.linalg.svd(C, full_matrices=False)
            V = Vt[:n_pc].T                      # bands x n_pc speaker subspace
            proj = (C @ V) @ V.T                 # each frame's component in that subspace
            R = C - proj                         # SUBTRACT the speaker subspace
        except np.linalg.LinAlgError:
            R = C
    # READ THE RESIDUAL = the per-frame deviation (the word). Per-frame L2 so the DTW
    # frame-distance is on the residual SHAPE, the same readout cmvn_track uses.
    out = []
    for r in range(R.shape[0]):
        v = R[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


def _allpole_ear(x, fs, M, attrs):
    """The sharp all-pole spectral-envelope ear. order tunable (the agent's own
    waveform-LPC order rule default)."""
    order = attrs.get("order")
    order = int(order) if order else None
    return _l2(allpole_ear(x, fs, order=order))


def _formant_relation(x, fs, M, attrs):
    """The VTL-invariant formant-spacing relation (waveform-LPC formants)."""
    return _l2(ENR.formant_relation_readout(x, fs))


def _manner_voicing(x, fs, M, attrs):
    """The phonology manner/voicing cue (periodicity + voiced/sonorant/sibilant)."""
    return _l2(ENR.manner_voicing_readout(x, fs, M))


def _f0_contour(x, fs, M, attrs):
    """The F0 / pitch-contour SOURCE channel."""
    return _l2(ENR.f0_contour_readout(x, fs))


def _modspec(x, fs, M, attrs):
    """The modulation-spectrum TEMPORAL-RATE channel (syllabic-rate bands)."""
    return _l2(ENR.modspec_readout(x, fs, M))


def _landmark(x, fs, M, attrs):
    """The phoneme-class LANDMARK transient-event channel (burst/VOT/fricative/nasal)."""
    return _l2(ENR.landmark_readout(x, fs, M))


def _transition(x, fs, M, attrs):
    """The agent's order-1-over-time transition descriptor at a chosen temporal
    window count (the multi-window transition channel). n_windows tunable."""
    n_windows = int(attrs.get("n_windows", 2))
    mu = M.mean(axis=0, keepdims=True)
    return _l2(transition_multiwindow(M - mu, _SEED_PATCHES, n_windows))


# ---------------------------------------------------------------------------
# THE REBUILT COCHLEA — a FINE-STRUCTURE-PRESERVING ear (Licklider correlogram).
#
# The seed gammatone ear is an ENERGY-ENVELOPE caricature: per band it half-wave
# rectifies then LOW-PASSES the envelope at ~50 Hz, which DESTROYS the phase-locked
# temporal fine structure (the discrete glottal pulses live there at 70-400 Hz, far
# above the 50 Hz envelope cutoff). The agent's diagnosis: the "blurry cochlea" we
# blamed for the cross-speaker nulls is OUR envelope LPF, not the ear — the real
# cochlea PHASE-LOCKS and preserves periodicity.
#
# The rebuilt ear keeps that fine structure. Per gammatone channel it half-wave
# rectifies the band signal but does NOT envelope-LPF it; instead it takes the
# SHORT-TIME AUTOCORRELATION of each channel (the agent's OWN native primitive
# `band_autocorr`), whose LAG axis preserves the phase-locked periodicity the
# envelope discards. The per-channel autocorrelations are pooled across bands into a
# SUMMARY AUTOCORRELOGRAM (native `summary_autocorrelogram`) — a per-frame lag
# profile. This is NOT another energy variant: the readout is the PERIODICITY-by-LAG
# structure (the glottal-pulse fine timing), which the band-energy trajectory throws
# away. Composition of the agent's OWNED native operators; the extractor is the thin
# I/O hand-off (the autocorrelation itself runs in Rust).
# ---------------------------------------------------------------------------

def _gammatone_band_signal(x, fs, fc):
    """One gammatone channel's HALF-WAVE-RECTIFIED band signal — WITHOUT the
    envelope LPF. This is the signal that still carries the phase-locked temporal
    fine structure (the rectifier folds the carrier into a periodicity the
    autocorrelation can read); the seed ear's one-pole LPF at env_cut would erase
    it. Same gammatone impulse as scripts.mine_whisper.gammatone_env, minus the LPF.
    Pure I/O-boundary DSP."""
    import math
    dur = 0.025
    L = int(dur * fs)
    t = np.arange(L) / fs
    b = 2.0 * math.pi * 1.019 * (24.7 + 0.108 * fc)
    g = t ** 3 * np.exp(-b * t) * np.cos(2 * math.pi * fc * t)
    e = np.sqrt(np.sum(g * g))
    if e > 0:
        g = g / e
    y = np.convolve(x, g, mode="same")
    return np.maximum(y, 0.0)            # half-wave rectify; NO envelope LPF


def _correlogram_ear(x, fs, M, attrs):
    """THE REBUILT COCHLEA: a fine-structure-preserving correlogram ear. Per
    gammatone band, take the short-time autocorrelation of the rectified band signal
    (native `band_autocorr` — the LAG axis keeps the phase-locked periodicity the
    energy envelope destroys), pool across bands into a per-frame summary
    autocorrelogram (native `summary_autocorrelogram`), and read out a compact
    per-frame periodicity profile. The agent's OWNED native operators do the work;
    this is the thin I/O hand-off. Params: f0_lo/f0_hi (the voicing lag window),
    n_frames_out (temporal downsample). Returns an L2 vector."""
    import substrate_rs
    from scripts.mine_whisper import BANDS
    N = substrate_rs._native
    x = np.asarray(x, dtype=np.float64)
    f0_lo = float(attrs.get("f0_lo", 70.0))
    f0_hi = float(attrs.get("f0_hi", 400.0))
    n_out = int(attrs.get("n_frames_out", 12))
    win = max(8, int(0.025 * fs))
    hop = max(4, int(0.010 * fs))
    max_lag = int(fs / f0_lo)            # longest lag = lowest pitch
    n_lags = max_lag + 1
    band_acs = []
    for fc in BANDS:
        bs = _gammatone_band_signal(x, fs, fc).astype(np.float32)
        ac = N.band_autocorr(bs.tolist(), win, hop, max_lag)
        band_acs.append(list(ac))
    if not band_acs or len(band_acs[0]) < n_lags:
        return _l2(np.zeros(n_out * 2 + 1, dtype=np.float64))
    n_frames = len(band_acs[0]) // n_lags
    sacf = N.summary_autocorrelogram(band_acs, n_lags)   # pooled lag profile / frame
    min_lag = max(1, int(fs / f0_hi))
    pt = N.periodicity_track(sacf, n_lags, min_lag, max_lag)
    strengths = np.asarray(pt[0::2], dtype=np.float64)   # voicing/periodicity per frame
    lags = np.asarray(pt[1::2], dtype=np.float64)
    # normalised period (lag / max_lag) — VTL/speaker-robust pitch CONTOUR shape, and
    # the periodicity STRENGTH contour (voiced/unvoiced fine-structure timing). Both
    # are fine-structure quantities the energy envelope cannot express. Resample each
    # contour to n_out frames + carry the mean periodicity as a global voicing scalar.
    def _resample(v, n):
        if len(v) == 0:
            return np.zeros(n)
        idx = np.linspace(0, len(v) - 1, n)
        return np.interp(idx, np.arange(len(v)), v)
    per_norm = _resample(np.where(lags > 0, lags / max_lag, 0.0), n_out)
    str_norm = _resample(strengths, n_out)
    feat = np.concatenate([per_norm, str_norm, [float(strengths.mean())]])
    return _l2(feat)


def _invented(x, fs, M, attrs):
    """An INVENTED cue: a novel band-combination Term (feature_generator grammar)
    evaluated per frame over the cochleagram -> a fixed-length value trajectory.
    The Term is stored on the Cue node (the agent's OWN composition, no seed)."""
    pred = attrs.get("predicate")
    if not pred:
        return _l2(np.zeros(24, dtype=np.float64))
    return _l2(_eval_band_term_trajectory(M, pred, n_out=24))


# extractor name -> function. The graph Cue's `extractor` attr selects the function.
CUE_EXTRACTORS = {
    "cochlear_ear": _cochlear_ear,
    "cmvn_ear": _cmvn_ear,
    "cs_ear": _cs_ear,
    "vtl_formant": _vtl_formant,
    "vtl_formant_allpole": _vtl_formant_allpole,
    "vtl_formant_dynamic": _vtl_formant_dynamic,
    "fft_ear": _fft_ear,
    "allpole_ear": _allpole_ear,
    "formant_relation": _formant_relation,
    "manner_voicing": _manner_voicing,
    "f0_contour": _f0_contour,
    "modspec": _modspec,
    "landmark": _landmark,
    "transition": _transition,
    "correlogram_ear": _correlogram_ear,   # THE REBUILT (fine-structure) COCHLEA
    "invented": _invented,
}


# The agent's STARTING front end (the three robust channels the current SpeechWorld
# uses). Active from boot; the rest of the registry is the agent's REPERTOIRE to gate
# in when it plateaus. (name, extractor, active, params)
SEED_CUES = [
    ("gammatone_flat", "cochlear_ear", 1, {"env_cut": _MIDDLE[1],
                                           "dur_cut": _MIDDLE[2],
                                           "n_frames": _MIDDLE[3]}),
    ("fft_ear", "fft_ear", 1, {"nwin": 3, "nbands": 40}),
    ("allpole_envelope", "allpole_ear", 1, {}),
]

# The agent's REPERTOIRE — inactive cues it can ADD when it hits the front-end wall.
# Each is owned, composable DSP proven orthogonal in enriched_hvpt_accept. Ordered by
# the harvest's measured orthogonality so the plateau-driven Argmax adds them in a
# sensible default order (the agent's pick can still reorder via param-derived value).
REPERTOIRE_CUES = [
    # extra EARS at new cochlear tradeoffs (the two-ears -> many-ears move)
    ("ear_sharp_freq", "cochlear_ear", 0, {"env_cut": 20.0, "dur_cut": 30.0,
                                           "n_frames": 16, "add_rank": 6}),
    ("ear_sharp_time", "cochlear_ear", 0, {"env_cut": 120.0, "dur_cut": 200.0,
                                           "n_frames": 48, "add_rank": 7}),
    # SOURCE-NORMALIZED cues (the cross-speaker lever the physics-model LOSO run
    # isolated): CMVN over the cochleagram + the VTL-invariant formant pattern.
    ("cmvn_ear", "cmvn_ear", 0, {"env_cut": _MIDDLE[1], "dur_cut": _MIDDLE[2],
                                 "n_frames": _MIDDLE[3], "add_rank": 0}),
    ("vtl_formant", "vtl_formant", 0, {"n_out": 24, "add_rank": 1}),
    # the CENTER-SURROUND SALIENCE ear (the analogical transfer of the vision
    # retina/LGN center-surround into the cochleagram): each time-freq point minus its
    # local spectro-temporal surround — a LOCAL CONTRAST NORMALIZER (cancels the slow
    # speaker-common tilt/level/VTL envelope) AND a SALIENCE filter (amplifies formant
    # peaks/edges where the phonetic info lives). frequency-only surround by default.
    ("cs_ear", "cs_ear", 0, {"sigma_f_s": 4.0, "sigma_t_s": 0.0,
                             "sigma_f_c": 1.0, "sigma_t_c": 0.0, "add_rank": 1}),
    # the SHARP all-pole VTL formant: the SAME F_i - mean(F1..F3) invariant, but over
    # the agent's full-resolution LPC-root formants instead of the coarse gammatone
    # ArgMax-over-bands (the next front-end move the SC LOSO run named — make the VTL
    # lever bite by sharpening the formant, not a new normalization).
    ("vtl_formant_allpole", "vtl_formant_allpole", 0,
     {"n_out": 24, "n_formants": 3, "add_rank": 1}),
    # the DYNAMIC speaker-invariant: the agent's ORDER-N OVER TIME operator on the
    # VTL-normalized sharp formant track (how the formants MOVE — the coarticulation /
    # transition GESTURE, which is shared across speakers even when the absolute
    # formants differ by VTL). The next move the static VTL run named: the residual
    # cross-speaker gap is DYNAMIC, so difference the formant track over time. order=1
    # = transition velocity (order=2 = curvature, ablatable).
    ("vtl_formant_dynamic", "vtl_formant_dynamic", 0,
     {"n_out": 24, "n_formants": 3, "order": 1, "add_rank": 1}),
    # banked orthogonal cues (the dismissed/harvested ideas)
    ("formant_relation", "formant_relation", 0, {"add_rank": 1}),
    ("manner_voicing", "manner_voicing", 0, {"add_rank": 2}),
    ("f0_contour", "f0_contour", 0, {"add_rank": 3}),
    ("modspec", "modspec", 0, {"add_rank": 4}),
    ("landmark", "landmark", 0, {"add_rank": 5}),
    ("transition_w3", "transition", 0, {"n_windows": 3, "add_rank": 8}),
]


# ---------------------------------------------------------------------------
# The graph-resident FRONT END: a FrontEnd node owning Cue nodes. The adapter
# READS the active cues to perceive a clip; the agent MODIFIES the graph to change
# what it hears.
# ---------------------------------------------------------------------------

def _ensure_productions(substrate):
    for src_t, et, tgt_t, prov in (
        ("FrontEnd", "has_cue", "Cue", "frontend:has_cue"),
        ("FrontEnd", "repertoire", "Cue", "frontend:repertoire"),
    ):
        try:
            substrate.add_production({"src": {"type": src_t, "var": "a"},
                                      "edge_type": et,
                                      "tgt": {"type": tgt_t, "var": "b"},
                                      "provenance": prov})
        except Exception:
            pass


def install_frontend(substrate) -> int:
    """Install (idempotently) the agent's graph-resident front end: a FrontEnd node
    owning the SEED_CUES (active) via has_cue and the REPERTOIRE_CUES (inactive) via
    repertoire. Returns the FrontEnd node id. World-adapter graph construction (no
    decision over graph state)."""
    _ensure_productions(substrate)
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is None:
        fe = substrate.add_node("FrontEnd", {"origin": "agent_frontend",
                                             "n_active": float(len(SEED_CUES)),
                                             "n_mods": 0.0})
    have = {substrate.node(c)["attrs"].get("name")
            for c in substrate.neighbours(fe, "has_cue")} | \
           {substrate.node(c)["attrs"].get("name")
            for c in substrate.neighbours(fe, "repertoire")}
    for name, extractor, active, params in SEED_CUES:
        if name in have:
            continue
        c = substrate.add_node("Cue", {"name": name, "extractor": extractor,
                                       "active": float(active),
                                       "origin": "agent_frontend", **params})
        substrate.add_edge(fe, "has_cue", c)
    for name, extractor, active, params in REPERTOIRE_CUES:
        if name in have:
            continue
        c = substrate.add_node("Cue", {"name": name, "extractor": extractor,
                                       "active": float(active),
                                       "origin": "agent_frontend", **params})
        substrate.add_edge(fe, "repertoire", c)
    return fe


# The CURATED, LOCKED front end (greedy forward selection under the rank product, maximising mean top-6
# recall across the cross-speaker AND same-speaker conditions — scripts/jabberwock_curate_channels.py).
# Beats the full repertoire in both conditions: cross 61/53, same 54/47 (top-6). The four that earned their
# place are the speaker-NORMALISED ears (cmvn / VTL-formant) + the base ear + the MODULATION spectrum (the
# dynamic/gesture axis in cosine form). Piling on the rest of the repertoire HURT (confidently-wrong cues);
# curation + the rank product is the recogniser, not channel-count + gating.
CURATED_CUES = ["cmvn_ear", "vtl_formant_allpole", "gammatone_flat", "modspec"]


def install_curated_frontend(substrate) -> int:
    """Install the FrontEnd and activate EXACTLY the CURATED_CUES (deactivating every other cue). This is
    THE locked recogniser front end: feature_channels then reads only these four, and the combine-all rank
    product over them is the recogniser. World-adapter graph mutation (flip cue.active); no decision."""
    fe = install_frontend(substrate)
    for et in ("has_cue", "repertoire"):
        for c in substrate.neighbours(fe, et):
            nm = substrate.node(c)["attrs"].get("name")
            substrate.set_attr(c, "active", 1.0 if nm in CURATED_CUES else 0.0)
    substrate.set_attr(fe, "n_active", float(len(CURATED_CUES)))
    substrate.set_attr(fe, "curated", 1.0)
    return fe


def activate_correlogram_ear(substrate) -> int:
    """Wire THE REBUILT COCHLEA (the fine-structure correlogram ear) into the agent's
    front end as an ACTIVE cue. Idempotent. The cue runs the agent's OWNED native
    autocorrelation primitives (band_autocorr + summary_autocorrelogram) — it is the
    agent's fine-structure ear, added alongside the seed energy ears so the do-contrast
    is the SAME world with vs without the rebuilt cochlea. World-adapter graph mutation
    (mint a Cue node + has_cue edge / flip active); no decision over graph state.
    Returns the Cue node id."""
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is None:
        fe = install_frontend(substrate)
    for c in substrate.neighbours(fe, "has_cue"):
        if substrate.node(c)["attrs"].get("extractor") == "correlogram_ear":
            substrate.set_attr(c, "active", 1.0)
            return c
    c = substrate.add_node("Cue", {"name": "correlogram_ear",
                                   "extractor": "correlogram_ear", "active": 1.0,
                                   "origin": "agent_frontend", "rebuilt_cochlea": 1.0,
                                   "f0_lo": 70.0, "f0_hi": 400.0, "n_frames_out": 12})
    substrate.add_edge(fe, "has_cue", c)
    return c


def active_cues(substrate) -> list:
    """The agent's CURRENT front end: the active Cue nodes, in graph order. Read by
    the adapter to perceive a clip. (cue_id, attrs) pairs."""
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is None:
        return []
    out = []
    for et in ("has_cue", "repertoire"):
        for c in substrate.neighbours(fe, et):
            a = substrate.node(c)["attrs"]
            if float(a.get("active", 0.0)) >= 1.0:
                out.append((c, a))
    return out


def n_active(substrate) -> int:
    return len(active_cues(substrate))


def feature_channels(substrate, x, fs) -> list:
    """The agent's perception of one clip THROUGH ITS CURRENT GRAPH front end: the
    L2 readout of every ACTIVE cue, in graph order. Pure I/O-boundary DSP dispatched
    by each cue's `extractor` attr; the SET and PARAMS come from the graph. This is
    the agent-modifiable replacement for the fixed feature_channels."""
    x = np.asarray(x, dtype=np.float64)
    _, env_cut, dur_cut, nf = _MIDDLE
    M = cochleagram(x, fs, env_cut, dur_cut, nf)   # shared middle cochleagram
    out = []
    for _cid, a in active_cues(substrate):
        fn = CUE_EXTRACTORS.get(a.get("extractor"))
        if fn is None:
            continue
        try:
            out.append(np.asarray(fn(x, fs, M, a), dtype=np.float64))
        except Exception:
            out.append(np.zeros(8, dtype=np.float64))
    return out


# ---------------------------------------------------------------------------
# Per-frame band-Term evaluation for INVENTED cues. The agent composes a scalar
# Term over band attrs (feature_generator grammar); we evaluate it per frame on the
# cochleagram via the substrate, giving a value trajectory. I/O-boundary evaluation
# of the agent's OWN composed Term (no decision; the Term is the agent's).
# ---------------------------------------------------------------------------

_BAND_SUB = None
_BAND_SIGN = None


def _band_substrate():
    global _BAND_SUB, _BAND_SIGN
    if _BAND_SUB is None:
        from substrate_rs import Substrate
        _BAND_SUB = Substrate()
        _BAND_SIGN = _BAND_SUB.add_node("BandFrame", {"probe": 1.0})
    return _BAND_SUB, _BAND_SIGN


def _eval_band_term_trajectory(M, pred, n_out=24):
    """Evaluate the agent's composed band-Term per frame over M (frames x bands),
    resampled to n_out, giving a value trajectory. The Term reads attrs b0..b{n-1}."""
    sub, sign = _band_substrate()
    nb = M.shape[1]
    vals = []
    for r in range(M.shape[0]):
        for j in range(nb):
            sub.set_attr(sign, f"b{j}", float(M[r, j]))
        try:
            v = sub.evaluate(FG._Pred(pred), {"s": sign})
            vals.append(float(v) if isinstance(v, (int, float)) else 0.0)
        except Exception:
            vals.append(0.0)
    v = np.asarray(vals, dtype=np.float64)
    if v.size == 0:
        return np.zeros(n_out)
    # resample to fixed length
    idx = np.linspace(0, v.size - 1, n_out)
    return np.interp(idx, np.arange(v.size), v)


# ---------------------------------------------------------------------------
# The MODIFICATION DECISION — graph-resident. When the agent plateaus, it must pick
# WHICH front-end modification to make. The choice is an Argmax over the inactive
# REPERTOIRE cues of a priority Term (the harvest-rank-derived add order, so the most
# orthogonal cue is added first); the adapter only ENACTS the chosen flip. NO Python
# conditional chooses the cue — the decision is the graph Term.
# ---------------------------------------------------------------------------

def _pick_mod_term():
    """Argmax over inactive repertoire Cues of priority = -add_rank (lower rank =
    added first), so the agent adds the most-orthogonal banked cue / next ear first.
    The decision is this graph Term; the adapter reads its value."""
    C = Var("C")
    # priority = 1000 - add_rank (so smaller rank -> larger priority). add_rank
    # defaults high (999) so an un-ranked cue is added last.
    priority = Minus(a=Lit(1000.0), b=Attr(C, "add_rank"))
    return FG._Pred(Argmax(
        source={"type": "NodesWhere", "node_type": "Cue",
                "attr_key": "addable", "value": Lit(1.0).to_dict()},
        var_name="C", value=priority.to_dict(), default=None).to_dict())


PICK_MOD_TERM = _pick_mod_term()


def _mark_addable(substrate, fe):
    """Tag every INACTIVE repertoire cue `addable=1` and every other cue `addable=0`
    so PICK_MOD_TERM's Argmax ranges only over the addable ones. Mechanical graph
    annotation (no decision)."""
    for et in ("has_cue", "repertoire"):
        for c in substrate.neighbours(fe, et):
            a = substrate.node(c)["attrs"]
            addable = 1.0 if (float(a.get("active", 0.0)) < 1.0 and
                              et == "repertoire") else 0.0
            substrate.set_attr(c, "addable", addable)
            if "add_rank" not in a:
                substrate.set_attr(c, "add_rank", 999.0)


def modify_frontend(substrate) -> dict | None:
    """The agent MODIFIES its own front end (called when it plateaus). The WHICH is
    the graph Argmax PICK_MOD_TERM over the addable repertoire cues; the adapter
    enacts the chosen flip (active 0 -> 1). Returns {cue, name, kind} or None if the
    repertoire is exhausted. The decision is the graph Term; this only enacts it."""
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is None:
        return None
    _mark_addable(substrate, fe)
    chosen = substrate.evaluate(PICK_MOD_TERM, {})
    if chosen is None:
        return None
    a = substrate.node(chosen)["attrs"]
    substrate.set_attr(chosen, "active", 1.0)
    substrate.set_attr(fe, "n_active", float(n_active(substrate)))
    substrate.set_attr(fe, "n_mods",
                       float(substrate.node(fe)["attrs"].get("n_mods", 0.0)) + 1.0)
    kind = "add_ear" if a.get("extractor") == "cochlear_ear" else "add_cue"
    return {"cue": chosen, "name": a.get("name"),
            "extractor": a.get("extractor"), "kind": kind}


def invent_cue(substrate, by_label, bands, seed=0) -> dict | None:
    """The agent INVENTS a new cue: generate-and-select a novel band-combination
    feature (feature_generator grammar), mint it as an active Cue with the composed
    Term stored, and gate it in. Used when the repertoire is exhausted but the wall
    holds — the open-ended novelty move. The composition + selection are the agent's
    generative grammar + compression selector; the adapter mints the node.

    by_label: {label: [BandFrame signs]} on a scratch substrate for the selector;
    bands: the band attr names (b0..b{n-1}). Returns {cue, name} or None."""
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is None:
        return None
    # generate-and-select by MDL on two halves (the compression selector).
    half = max(1, len(next(iter(by_label.values()))) // 2) if by_label else 0
    a_half = {k: v[:half] for k, v in by_label.items()}
    b_half = {k: v[half:] for k, v in by_label.items()}
    # we need a scratch substrate carrying the band frames for the selector eval
    winners = FG.discover_features_mdl(_band_substrate()[0] if False else
                                       _SEL_SUB_HOLDER.get("sub"),
                                       a_half, b_half, bands, n=300, keep=1, seed=seed)
    if not winners:
        return None
    _score, _gen, _size, term = winners[0]
    name = f"invented_{int(substrate.node(fe)['attrs'].get('n_mods', 0.0))}"
    c = substrate.add_node("Cue", {"name": name, "extractor": "invented",
                                   "active": 1.0, "predicate": term.to_dict(),
                                   "origin": "agent_frontend",
                                   "composed_by": "agent_generate_select",
                                   "add_rank": 999.0})
    substrate.add_edge(fe, "has_cue", c)
    substrate.set_attr(fe, "n_active", float(n_active(substrate)))
    substrate.set_attr(fe, "n_mods",
                       float(substrate.node(fe)["attrs"].get("n_mods", 0.0)) + 1.0)
    return {"cue": c, "name": name, "kind": "invent"}


# holder so invent_cue can be handed the scratch substrate carrying band frames
_SEL_SUB_HOLDER: dict = {}


def prune_invented_cues(substrate) -> int:
    """RESUME repair (the treadmill fix): drop every INVENTED cue from the front end.
    The pre-fix run accumulated ~20 invented cues with NO record of which lifted the
    held-out (the effect-gate that would keep only the lifting ones did not exist
    yet), so on resume they are all treated as the non-lifting treadmill artifacts
    they were and removed. The SEED cues, the REPERTOIRE cues, and the lexicon +
    banks are all kept; from here every NEW invention is effect-gated, so the front
    end stays bounded. Returns the number pruned. Mechanical graph repair (honest:
    we cannot tell which old inventions lifted, so none are assumed to)."""
    invented = [c for c in substrate.nodes("Cue")
                if substrate.node(c)["attrs"].get("extractor") == "invented"]
    for c in invented:
        try:
            substrate.remove_node(c)
        except Exception:
            pass
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is not None:
        substrate.set_attr(fe, "n_active", float(n_active(substrate)))
    return len(invented)


def revert_cue(substrate, cue) -> bool:
    """REVERT a front-end modification the EFFECT-GATE judged non-lifting (the
    held-out cookie-rate did not climb after it was added). An INVENTED cue (its
    own minted node, not in the seed/repertoire) is REMOVED entirely so the front
    end does not balloon with non-lifting inventions; a gated-in REPERTOIRE cue is
    returned to inactive (back in the repertoire for a later, possibly-lifting cell).
    Mechanical graph repair — the KEEP/DROP decision is the effect-gate Rule's; this
    only enacts the drop. Returns True if a cue was reverted."""
    fe = next((n for n in substrate.nodes("FrontEnd")), None)
    if fe is None or cue is None:
        return False
    a = substrate.node(cue)["attrs"]
    if a.get("extractor") == "invented":
        # a minted invention — remove the node entirely (don't accumulate it).
        try:
            substrate.remove_node(cue)
        except Exception:
            return False
    else:
        # a repertoire cue gated in — return it to inactive (re-addable later).
        substrate.set_attr(cue, "active", 0.0)
    substrate.set_attr(fe, "n_active", float(n_active(substrate)))
    return True


__all__ = ["install_frontend", "active_cues", "n_active", "feature_channels",
           "modify_frontend", "invent_cue", "revert_cue", "prune_invented_cues",
           "PICK_MOD_TERM", "center_surround", "cs_track",
           "CUE_EXTRACTORS", "SEED_CUES", "REPERTOIRE_CUES"]
