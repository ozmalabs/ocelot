"""radio_telescope_frontend — STAGE 1 of the continuous-speech machine.

THE MOVE (ears-are-literally-a-radio-telescope): apply the radio-astronomy
signal-recovery toolkit to the single-channel speech waveform to produce a
CLEANER spectro-temporal read and a SHARPER onset function for the relaxation
oscillator (Stage 2) and the collapse (Stage 3).

OWNED DSP. Pure numpy, FROZEN constants, NO net, NO fit, NO sweep-and-keep. This
is the SENSE / world-adapter TRANSDUCTION: mechanical audio -> a cleaned read +
a sharpened onset envelope. No graph state, no agent decisions.

The three radio-astronomy tools, applied to the cochleagram (frames x bands):

  1. MATCHED FILTERING. A radio telescope correlates the received voltage against
     the EXPECTED pulse shape to lift a signal out of noise (the matched filter
     maximises output SNR for a known template). The "expected structure" of a
     syllable onset is a sharp ENERGY RISE: a half-wave step/ramp. We correlate
     each band's energy track against a fixed onset-template (a normalised rising
     ramp followed by a fall) -> a matched-filter onset response per band that
     peaks AT the onset and suppresses noise that doesn't look like an onset.

  2. INTEGRATION (coherent / incoherent averaging over independent looks). A radio
     telescope integrates many independent samples/antennas to lift SNR ~sqrt(N):
     incoherent integration averages power across independent "looks." Our
     independent looks are the COCHLEAR BANDS within a frequency GROUP (neighbouring
     bands see the same syllabic energy but independent fine-structure noise) and a
     short TEMPORAL window. Incoherently averaging the band-group power lifts the
     syllabic-rate envelope SNR while averaging away band-local noise. The cleaned
     read keeps full band resolution but each band is denoised by its group.

  3. CLEAN deconvolution (Hogbom CLEAN). Radio imaging iteratively finds the
     BRIGHTEST point in the dirty map, subtracts a scaled copy of the instrument's
     point-spread-function (PSF) at that location, records it in a clean component
     list, and repeats — separating overlapping sources and sharpening the map. We
     CLEAN the per-frame spectrum: the PSF is the cochlear filter's spectral
     leakage (a band's energy bleeds into neighbours) PLUS, for the onset envelope,
     the syllable's broad temporal smear. Iteratively subtracting the brightest
     spectral component's PSF de-blurs overlapping harmonics/formants (separating
     sources) and, on the onset track, subtracting the temporal PSF SHARPENS each
     onset into a near-impulse (the brightest-rise-first deconvolution).

OUTPUT (for Stages 2 + 3):
  · clean_read(x)  -> (frames x bands) CLEANED cochleagram (integrated + CLEANed),
    the sharper spectro-temporal read the collapse reads its acoustic frame over.
  · sharp_onset(x) -> (frames,) SHARPENED broadband onset envelope (matched-filtered
    + CLEAN-deconvolved), the drive the relaxation oscillator integrates.

DONKEY BOUNDARY: every operation is a fixed linear/threshold DSP primitive from
radio astronomy (matched filter = correlation, integration = averaging, CLEAN =
iterative PSF subtraction). No learned weight, no fitted parameter, no template
estimated from the test set. The templates/PSFs are fixed analytic shapes.
"""
from __future__ import annotations

import numpy as np

from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS

# the shared cochlear operating point (same "middle" ear the rest of the system uses)
_MIDDLE = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
_FS = 8000

# ---- FROZEN radio-astronomy constants (shapes/orders, NOT fit on any test) ----

# matched-filter onset template: a syllable onset is a sharp RISE then a slower
# fall (the energy ramps up to the vowel nucleus). The matched filter is the
# time-reversed template; correlating the band-energy track with it peaks at the
# onset. Length ~ the rise time of a syllable onset (~50-80 ms). At a 10 ms hop
# (the cochleagram frame rate is set by n_frames; we resample onset to ~100 fps).
_MF_RISE = 4          # frames of rising ramp (the leading edge — the matched part)
_MF_FALL = 3          # frames of trailing fall (so the template is onset-shaped)

# incoherent integration: average each band over a GROUP of neighbouring bands
# (independent looks at the same syllabic energy) and a short temporal window.
_INT_BAND_GROUP = 3   # +/- this many neighbouring bands averaged (incoherent)
_INT_TIME_WIN = 2     # +/- this many frames averaged (short temporal look)

# Hogbom CLEAN:
_CLEAN_GAIN = 0.2     # loop gain (fraction of the peak PSF subtracted per iter) —
#                       the standard conservative CLEAN gamma (0.1-0.3)
_CLEAN_ITERS = 30     # number of CLEAN components extracted per spectrum / track
_CLEAN_THRESH = 0.02  # stop when the residual peak falls below this frac of the
#                       original peak (the CLEAN stopping threshold)
# the spectral PSF = the cochlear filter leakage = a narrow triangular kernel over
# bands (a band's energy bleeds +/-1-2 neighbours). Fixed analytic shape.
_PSF_SPECTRAL = np.array([0.15, 0.5, 1.0, 0.5, 0.15])
# the temporal PSF = the syllable's onset smear = a one-sided decaying kernel (an
# onset's energy persists into following frames). Fixed analytic shape.
_PSF_TEMPORAL = np.array([1.0, 0.6, 0.35, 0.2, 0.1])


def _coch(x, fs=_FS):
    _, env_cut, dur_cut, nf = _MIDDLE
    # use MORE frames than the seed middle so the onset track has temporal detail
    # for the oscillator (a continuous utterance is long); ~100 fps target.
    n = len(x)
    n_frames = max(int(nf), int(round(n / fs * 100)))
    return cochleagram(x, fs, env_cut, dur_cut, n_frames)


# ===========================================================================
# 1. MATCHED FILTER — correlate each band-energy track against the fixed onset
#    template. Owned DSP (a fixed-template correlation, the radio matched filter).
# ===========================================================================

def _onset_template():
    """The expected onset shape: a linear RISE then a linear FALL, zero-mean (so the
    matched filter responds to the RISE STRUCTURE, not the DC level). Fixed shape."""
    rise = np.linspace(0.0, 1.0, _MF_RISE)
    fall = np.linspace(1.0, 0.0, _MF_FALL + 1)[1:]
    t = np.concatenate([rise, fall])
    t = t - t.mean()                     # zero-mean: respond to the rise, not level
    n = np.linalg.norm(t)
    return t / n if n > 1e-9 else t


_ONSET_MF = _onset_template()


def matched_filter_onset(M):
    """Matched-filter onset response of a (frames x bands) cochleagram. For each
    band, correlate its energy track with the (time-reversed) onset template; the
    response peaks AT each onset and rejects energy that doesn't look like a rise.
    Sum over bands -> a broadband matched-filter onset function. Owned DSP."""
    if M.size == 0:
        return np.zeros(0)
    F, B = M.shape
    # correlation with the matched filter = convolution with the time-reversed
    # template (np.convolve with the template gives the matched-filter output).
    mf = _ONSET_MF[::-1]
    resp = np.zeros(F)
    for b in range(B):
        track = M[:, b]
        c = np.convolve(track, mf, mode="same")
        resp += np.clip(c, 0.0, None)    # half-wave: keep onsets (positive corr)
    return resp


# ===========================================================================
# 2. INTEGRATION — incoherent averaging over independent looks (band groups +
#    a short temporal window) to lift the syllabic-rate SNR. Owned DSP.
# ===========================================================================

def integrate(M, band_group=_INT_BAND_GROUP, time_win=_INT_TIME_WIN):
    """Incoherent integration of the cochleagram: each (frame, band) is replaced by
    the average power over its band GROUP (+/-band_group neighbouring bands = the
    independent looks at the same syllabic energy) and a short temporal window
    (+/-time_win frames). Lifts the syllabic envelope SNR ~sqrt(N_looks) while
    averaging away band-local / frame-local noise. Reflect-padded box averages
    (separable) — owned DSP, no fit. Keeps full band resolution (each band is the
    centre of its own group)."""
    if M.size == 0:
        return M
    M = np.asarray(M, dtype=np.float64)
    F, B = M.shape
    out = M.copy()
    # temporal box average (independent temporal looks)
    if time_win > 0:
        k = np.ones(2 * time_win + 1) / (2 * time_win + 1)
        padded = np.pad(out, ((time_win, time_win), (0, 0)), mode="reflect")
        for b in range(B):
            out[:, b] = np.convolve(padded[:, b], k, mode="valid")
    # band-group box average (independent frequency looks at the same syllabic energy)
    if band_group > 0:
        k = np.ones(2 * band_group + 1) / (2 * band_group + 1)
        padded = np.pad(out, ((0, 0), (band_group, band_group)), mode="reflect")
        for f in range(F):
            out[f, :] = np.convolve(padded[f, :], k, mode="valid")
    return out


# ===========================================================================
# 3. CLEAN — Hogbom iterative PSF-subtraction deconvolution. Two uses:
#    (a) SPECTRAL CLEAN per frame: deconvolve the cochlear leakage PSF -> separate
#        overlapping harmonics/formants (sharper spectral read = cleaner sources).
#    (b) TEMPORAL CLEAN of the onset track: deconvolve the onset smear PSF ->
#        sharpen each onset into a near-impulse (the brightest-rise-first move).
#    Owned DSP: find brightest, subtract scaled PSF, accumulate clean component.
# ===========================================================================

def _hogbom_clean(dirty, psf, gain=_CLEAN_GAIN, iters=_CLEAN_ITERS,
                  thresh=_CLEAN_THRESH):
    """Hogbom CLEAN of a 1-D non-negative `dirty` signal convolved with `psf`
    (centred). Iteratively: find the brightest residual sample, record gain*peak as
    a clean component at that location, subtract gain*peak*PSF (shifted to that
    location) from the residual; stop after `iters` or when the residual peak falls
    below thresh*original_peak. Returns the clean-component map (sharpened: each true
    source is a near-impulse). Owned DSP (the standard radio deconvolution)."""
    d = np.asarray(dirty, dtype=np.float64).copy()
    n = d.size
    if n == 0:
        return d
    d = np.clip(d, 0.0, None)
    orig_peak = float(d.max())
    if orig_peak <= 1e-12:
        return d
    psf = np.asarray(psf, dtype=np.float64)
    pc = psf.argmax()                    # PSF centre (peak) index
    clean = np.zeros(n, dtype=np.float64)
    for _ in range(iters):
        pk = int(d.argmax())
        pv = float(d[pk])
        if pv < thresh * orig_peak:
            break
        amp = gain * pv
        clean[pk] += amp
        # subtract amp * PSF centred at pk
        for j, w in enumerate(psf):
            idx = pk + (j - pc)
            if 0 <= idx < n:
                d[idx] -= amp * w
        d = np.clip(d, 0.0, None)
    # add back the residual (what CLEAN couldn't attribute) so no energy is lost,
    # but the SOURCES are now sharp clean components.
    return clean + d


def clean_spectrum(M, psf=_PSF_SPECTRAL):
    """SPECTRAL CLEAN: deconvolve each frame's band spectrum against the cochlear
    leakage PSF -> separate overlapping spectral components (harmonics/formants),
    sharpening the spectral read. Per-frame Hogbom CLEAN over bands. Owned DSP."""
    if M.size == 0:
        return M
    out = np.empty_like(M, dtype=np.float64)
    for f in range(M.shape[0]):
        out[f, :] = _hogbom_clean(M[f, :], psf)
    return out


def clean_onset(onset, psf=_PSF_TEMPORAL):
    """TEMPORAL CLEAN of the onset track: deconvolve the onset smear PSF -> each
    onset becomes a near-impulse (brightest-rise-first), sharpening the drive the
    relaxation oscillator integrates. 1-D Hogbom CLEAN over time. Owned DSP."""
    return _hogbom_clean(onset, psf)


# ===========================================================================
# THE STAGE-1 INTERFACE — the cleaned read + sharpened onset for Stages 2 & 3.
# ===========================================================================

def clean_read(x, fs=_FS):
    """STAGE-1 CLEANED READ: integrate (incoherent averaging over band/time looks)
    then SPECTRAL CLEAN (deconvolve cochlear leakage) the cochleagram. The sharper,
    denoised spectro-temporal read the collapse (Stage 3) reads its acoustic frame
    over. (frames x bands). Owned DSP."""
    M = _coch(x, fs)
    if M.size == 0:
        return M
    Mi = integrate(M)
    Mc = clean_spectrum(Mi)
    return Mc


def sharp_onset(x, fs=_FS, M_clean=None):
    """STAGE-1 SHARPENED ONSET: matched-filter the (integrated) cochleagram for the
    onset response, then TEMPORAL CLEAN it into sharp near-impulse onsets. The drive
    the relaxation oscillator (Stage 2) integrates to threshold. (frames,) >= 0.
    Owned DSP. If M_clean is given (the cleaned read), reuse its integration."""
    if M_clean is not None and M_clean.size:
        Mi = M_clean
    else:
        M = _coch(x, fs)
        if M.size == 0:
            return np.zeros(0)
        Mi = integrate(M)
    mf = matched_filter_onset(Mi)        # matched-filter onset response
    if mf.size == 0:
        return mf
    sharp = clean_onset(mf)              # CLEAN-deconvolve the onset smear
    pk = float(sharp.max())
    return sharp / pk if pk > 1e-12 else sharp


# ---- the RAW cochleagram + RAW onset (for the Stage-1 ablation: cleaned vs raw) ----

def raw_read(x, fs=_FS):
    """The RAW cochleagram (no integration, no CLEAN) — the Stage-1 ablation
    baseline against clean_read. (frames x bands). Owned DSP."""
    return _coch(x, fs)


def raw_onset(x, fs=_FS, M_raw=None):
    """The RAW broadband onset (half-wave-rectified envelope derivative, the prior
    onset function) — the Stage-1 ablation baseline against sharp_onset. (frames,).
    NO matched filter, NO CLEAN. Owned DSP."""
    if M_raw is not None and M_raw.size:
        M = M_raw
    else:
        M = _coch(x, fs)
    if M.size == 0:
        return np.zeros(0)
    env = M.sum(axis=1)                  # broadband energy envelope
    d = np.diff(env, prepend=env[0])
    onset = np.clip(d, 0.0, None)
    pk = float(onset.max())
    return onset / pk if pk > 1e-12 else onset


__all__ = [
    "clean_read", "sharp_onset", "raw_read", "raw_onset",
    "matched_filter_onset", "integrate", "clean_spectrum", "clean_onset",
]
