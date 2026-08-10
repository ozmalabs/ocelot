"""solve_for_n_vowel — the SPEECH forward model plugged into the proven solve-for-N.

THE RUNG. The general solve-for-N machine (scripts/solve_for_n.py) is proven on the
clean synthetic domain (damped sinusoids = clocks) and composed hierarchically
(scripts/solve_for_n_recursive.py, melody = sum of notes). This file builds the LAST
HARD PLUG-IN: the SPEECH forward model, starting at the SIMPLEST unit by the
diagnostic-ladder discipline — the VOWEL.

THE VOWEL IS THE CLOCK MACHINE IN GENERATE MODE (memory:
ozma_clock_is_enough_cochlea_is_a_bank_of_clocks). A steady vowel = a glottal SOURCE
clock (pulse train at f0) driving a bank of vocal-tract RESONATOR clocks (formant
resonances F1,F2,F3). Production = the same oscillators run as a source. Recognition =
analysis-by-synthesis: hypothesise the vowel + speaker params, SYNTHESISE the vowel the
forward model would produce, MATCH against the input in a speaker-RELATIVE spectral
space, pick the lowest-error candidate. Cross-speaker because the speaker params (f0,
vocal-tract length / formant scale) are SOLVED FOR per utterance, not assumed.

DONKEY AUDIT.
  * FORWARD MODEL = owned source-filter DSP: a glottal pulse-train source + a cascade of
    three 2nd-order formant RESONATORS (the standard all-pole vocal-tract model), driven
    by a Peterson & Barney vowel formant table (STATED below). NO trained TTS net, NO
    .fit(), NO gradient descent. Pure numpy generative function f(params) -> waveform.
  * RECOGNITION = the agent's analysis-by-synthesis: a small owned search over the
    speaker params (f0, formant-scale) per candidate vowel + an L2 spectral match. NO
    classifier weights, NO training. The "fit" is a bounded coordinate search against the
    EXACT forward model (the AbS calculus), exactly as scripts/solve_for_n.py does for a
    sinusoid.
  * DATA = REAL human vowels: steady monophthong nuclei extracted from FSDD digit
    recordings (real speakers). Cross-speaker, held-out speakers NEVER banked.
  * The plug-in interface mirrors solve_for_n.py's forward-model boundary (synthesise /
    propose / refine). CortexLoop untouched. Research harness, owned numpy only.

PREDICTION (to be killed if false). The source-filter approximates the vowel's formant
structure -> the speaker-adjusted match discriminates vowels -> AbS recognises above
chance, possibly competitive with a plain exemplar 1-NN. KILL/HONEST: if the synthesis
is too poor (match doesn't discriminate, recognition ~chance), say so and PINPOINT the
limiter (source spectral tilt? missing higher formants? bandwidths? the speaker search?
the relative-match space?). That limiter is the next rung's fix.

Run:  python -m scripts.solve_for_n_vowel           (full acceptance)
      python -m scripts.solve_for_n_vowel --quick    (smoke)
"""
from __future__ import annotations

import sys
import time
import math
import glob
import os
import wave
import numpy as np


FS = 8000  # FSDD sample rate


# ===========================================================================
# DATA — real vowel nuclei from FSDD digits (real speakers, cross-speaker).
# ===========================================================================
# Each digit word has a dominant stressed-syllable monophthong nucleus. We keep only
# digits whose nucleus is a clear monophthong (skip strong diphthongs: five/ay, nine/ay,
# eight/ey, one/wuh-glide). The vowel identity is the recognition label. Peterson &
# Barney canonical American-English formants (Hz) drive the forward model.
#
# Digit -> nucleus vowel (IPA-ish key):
#   zero  -> 'iy'  (the "ee-r-oh"; the initial /iy/ region — actually "zihr"; we use the
#                   steady voiced nucleus, dominant vowel ~ /ih/->/iy/; label as 'ih')
#   two   -> 'uw'
#   three -> 'iy'
#   four  -> 'ao'
#   six   -> 'ih'
#   seven -> 'eh'
# To keep the vowels DISTINCT and unambiguous we use the subset below.
DIGIT_VOWEL = {
    2: "uw",   # "two"  -> /uw/  (high back rounded)
    3: "iy",   # "three"-> /iy/  (high front)
    4: "ao",   # "four" -> /ao/  (low back rounded)
    6: "ih",   # "six"  -> /ih/  (high-mid front)
    7: "eh",   # "seven"-> /eh/  (mid front)
}

# Peterson & Barney (1952) canonical American-English vowel formants (Hz), male-ish
# reference. F1, F2, F3. This is the formant TABLE the forward model reads (STATED).
VOWEL_FORMANTS = {
    "iy": (270, 2290, 3010),
    "ih": (390, 1990, 2550),
    "eh": (530, 1840, 2480),
    "ae": (660, 1720, 2410),
    "aa": (730, 1090, 2440),
    "ao": (570, 840, 2410),
    "uh": (440, 1020, 2240),
    "uw": (300, 870, 2240),
}

FSDD = "/tmp/fsdd/recordings"


def _read_wav(path):
    w = wave.open(path)
    fr = w.getframerate()
    raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    w.close()
    if fr != FS:
        # simple resample (rare; FSDD is 8k)
        n = int(len(raw) * FS / fr)
        raw = np.interp(np.linspace(0, len(raw), n, endpoint=False), np.arange(len(raw)), raw)
    return raw


def _extract_vowel_nucleus(sig, fs=FS, win_ms=40):
    """Extract a steady VOICED vowel nucleus: the highest-energy, low-zero-crossing
    (= voiced, periodic) window. Mechanical signal -> graph token (front-end ingest)."""
    win = int(win_ms * fs / 1000)
    if len(sig) < win:
        sig = np.pad(sig, (0, win - len(sig)))
    hop = win // 2
    best_i, best_score = 0, -1.0
    for i in range(0, len(sig) - win + 1, hop):
        seg = sig[i:i + win]
        energy = float(np.mean(seg ** 2))
        # zero-crossing rate: low for voiced vowels
        zc = float(np.mean(np.abs(np.diff(np.sign(seg))) > 0))
        score = energy * (1.0 - zc)  # prefer high-energy, low-ZCR (voiced)
        if score > best_score:
            best_score, best_i = score, i
    seg = sig[best_i:best_i + win].copy()
    seg = seg / (np.max(np.abs(seg)) + 1e-9)
    return seg


def load_vowel_dataset(max_per_class_per_speaker=None):
    """Load real vowel nuclei from FSDD, tagged (vowel_label, speaker). Returns list of
    dicts {vowel, speaker, sig}. Mechanical ingest — no decisions."""
    items = []
    files = sorted(glob.glob(os.path.join(FSDD, "*.wav")))
    counts = {}
    for f in files:
        base = os.path.basename(f)
        try:
            digit = int(base.split("_")[0])
            speaker = base.split("_")[1]
        except Exception:
            continue
        if digit not in DIGIT_VOWEL:
            continue
        vowel = DIGIT_VOWEL[digit]
        key = (vowel, speaker)
        if max_per_class_per_speaker is not None:
            counts[key] = counts.get(key, 0) + 1
            if counts[key] > max_per_class_per_speaker:
                continue
        sig = _read_wav(f)
        nucleus = _extract_vowel_nucleus(sig)
        items.append({"vowel": vowel, "speaker": speaker, "sig": nucleus})
    return items


# ===========================================================================
# THE FORWARD MODEL PLUG-IN — source-filter VOWEL (owned DSP, NO net/fit).
# Mirrors the solve_for_n.py forward-model boundary: synthesise / propose / refine.
# ===========================================================================

class VowelSourceFilterModel:
    """EXACT source-filter generator for a steady vowel. The clock machine in GENERATE
    mode: a glottal pulse-train SOURCE clock at f0 driving a cascade of three 2nd-order
    formant RESONATOR clocks (F1,F2,F3 with bandwidths). Speaker-adjustable by f0 and a
    formant-scale (vocal-tract-length factor). Carries ALL the domain knowledge; the
    recognition engine treats it as a black-box generator.

    params dict:
        vowel        : str (table key) OR explicit (f1,f2,f3) tuple
        f0           : glottal fundamental (Hz)        -- speaker
        scale        : formant scale (VTL factor)      -- speaker
        n            : number of samples
    """

    def __init__(self, fs=FS, bandwidths=(80.0, 100.0, 120.0), src_tilt=0.0):
        self.fs = float(fs)
        self.bandwidths = bandwidths
        self.src_tilt = src_tilt  # spectral tilt of source (-6 dB/oct ~ real glottis); 0 = flat impulse

    def formants_for(self, params):
        v = params["vowel"]
        if isinstance(v, tuple):
            base = v
        else:
            base = VOWEL_FORMANTS[v]
        s = params.get("scale", 1.0)
        return tuple(f * s for f in base)

    def synthesise(self, params):
        """source x filter -> vowel waveform. Owned DSP."""
        n = params["n"]
        f0 = params.get("f0", 120.0)
        fs = self.fs
        # SOURCE: glottal pulse train at f0 (relaxation/impulse oscillator).
        src = np.zeros(n)
        period = max(2, int(round(fs / f0)))
        src[::period] = 1.0
        # optional source spectral tilt: a 1-pole lowpass approximating glottal roll-off.
        if self.src_tilt > 0.0:
            a = math.exp(-2.0 * math.pi * self.src_tilt / fs)
            y = np.zeros(n)
            for i in range(n):
                y[i] = (1 - a) * src[i] + a * (y[i - 1] if i >= 1 else 0.0)
            src = y
        # FILTER: cascade of three 2nd-order resonators at F1,F2,F3.
        f1, f2, f3 = self.formants_for(params)
        sig = src
        for fc, bw in zip((f1, f2, f3), self.bandwidths):
            if fc <= 0 or fc >= fs / 2:
                continue
            r = math.exp(-math.pi * bw / fs)
            theta = 2.0 * math.pi * fc / fs
            a1 = -2.0 * r * math.cos(theta)
            a2 = r * r
            y = np.zeros(n)
            prev1 = prev2 = 0.0
            for i in range(n):
                cur = sig[i] - a1 * prev1 - a2 * prev2
                y[i] = cur
                prev2 = prev1
                prev1 = cur
            sig = y
        sig = sig / (np.max(np.abs(sig)) + 1e-9)
        return sig

    # ----- the AbS calculus: propose/refine the SPEAKER params for a vowel candidate ---
    def estimate_f0(self, signal):
        """Autocorrelation pitch estimate (the source clock's rate). Owned DSP."""
        x = signal - np.mean(signal)
        if np.sum(x ** 2) < 1e-12:
            return 120.0
        ac = np.correlate(x, x, mode="full")[len(x) - 1:]
        lo = int(self.fs / 350)   # 350 Hz max f0
        hi = int(self.fs / 70)    # 70 Hz min f0
        hi = min(hi, len(ac) - 1)
        if hi <= lo:
            return 120.0
        peak = lo + int(np.argmax(ac[lo:hi]))
        return float(self.fs / peak)


# ===========================================================================
# SPEAKER-RELATIVE SPECTRAL MATCH SPACE — the cross-speaker comparison.
# ===========================================================================

def log_mel_envelope(signal, fs=FS, n_mel=24, fmin=80, fmax=3800):
    """Smoothed log-magnitude spectral ENVELOPE on a mel grid. The match space: it
    captures the formant pattern (the WHAT) while the mel-smoothing washes out the
    pitch-harmonic comb (the source). Owned DSP."""
    n = len(signal)
    win = np.hanning(n)
    nfft = 1024
    spec = np.abs(np.fft.rfft(signal * win, n=nfft))
    freqs = np.fft.rfftfreq(nfft, d=1.0 / fs)

    def hz2mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def mel2hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    mlo, mhi = hz2mel(fmin), hz2mel(fmax)
    centers = mel2hz(np.linspace(mlo, mhi, n_mel + 2))
    out = np.zeros(n_mel)
    for i in range(n_mel):
        lo, c, hi = centers[i], centers[i + 1], centers[i + 2]
        w = np.zeros_like(freqs)
        left = (freqs >= lo) & (freqs <= c)
        right = (freqs > c) & (freqs <= hi)
        w[left] = (freqs[left] - lo) / max(1e-9, (c - lo))
        w[right] = (hi - freqs[right]) / max(1e-9, (hi - c))
        out[i] = np.sum(w * spec)
    out = np.log(out + 1e-6)
    return out


def relative_envelope(signal, fs=FS):
    """SPEAKER-RELATIVE match space: mean-subtracted (CMN) + range-normalised log-mel
    envelope. Subtracting the mean removes the per-speaker spectral-tilt/level; the SHAPE
    (formant pattern) that survives is what carries vowel identity cross-speaker."""
    env = log_mel_envelope(signal, fs)
    env = env - np.mean(env)
    env = env / (np.std(env) + 1e-9)
    return env


def match_error(synth, target, fs=FS):
    """L2 distance in the speaker-RELATIVE envelope space (NOT raw waveform L2 — the
    pitch/phase differ; we match the formant SHAPE)."""
    a = relative_envelope(synth, fs)
    b = relative_envelope(target, fs)
    return float(np.sqrt(np.sum((a - b) ** 2)))


# ===========================================================================
# F2-RESOLVING FORMANT-FRAME MATCH  (the named fix — replaces mel-envelope L2).
#
# The mel-L2 match UNDER-RESOLVES F2: the formant peaks are buried under the
# low-frequency spectral tilt, so front/back pairs that share F1 but differ in
# F2 (eh<->ao, ih<->iy, uw<->ih/iy) collapse. The fix resolves F1/F2/F3 EXPLICITLY
# and compares the three formant FRAMES with equal weight via WEIGHTED-ADMISSIBILITY
# (the framework's over-determination, memory: ozma_collapse_multiple_frames), NOT a
# positive-sum dot product. Each |F_i^cand - F_i^input| in a SPEAKER-RELATIVE space
# becomes a soft EXCLUDER; the match = intersection of the three soft exclusions
# (sum of log-admissibilities), abstaining at a floor where a frame is unsure. The
# answer is the candidate that survives all three formant frames' weighted exclusions.
# Owned DSP (LPC formant estimation) + owned weighted-admissibility (the agent's
# cognition). NO net, NO .fit(), NO dot-product scalar collapse.
# ===========================================================================

def lpc_coeffs(signal, order):
    """Linear-prediction coefficients via autocorrelation + Levinson-Durbin. Owned DSP.
    The all-pole vocal-tract model inverted: the LPC poles ARE the formant resonances.
    PRE-EMPHASIS (1 - 0.97 z^-1) flattens the -6 dB/oct glottal source tilt FIRST — without
    it the tilt plants a spurious low-frequency pole that pushes every formant down a slot
    (the off-by-one that buried F2 below 600 Hz in the first cut)."""
    x = signal - np.mean(signal)
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])   # pre-emphasis
    x = x * np.hanning(len(x))
    r = np.correlate(x, x, mode="full")[len(x) - 1:]
    r = r[: order + 1]
    if r[0] <= 0:
        return None
    # Levinson-Durbin recursion.
    a = np.zeros(order + 1)
    a[0] = 1.0
    e = r[0]
    for i in range(1, order + 1):
        acc = r[i] + np.sum(a[1:i] * r[i - 1:0:-1])
        k = -acc / e
        a_new = a.copy()
        for j in range(1, i):
            a_new[j] = a[j] + k * a[i - j]
        a_new[i] = k
        a = a_new
        e *= (1.0 - k * k)
        if e <= 0:
            break
    return a


def estimate_formants(signal, fs=FS, order=10, n_form=3):
    """Estimate F1,F2,F3 of a vowel as the lowest LPC-pole resonance frequencies.
    Owned DSP — inverts the same all-pole source-filter model the forward model uses
    (LPC ROOTS, stated). This is the F2-RESOLVING front end the mel-L2 lacked."""
    a = lpc_coeffs(signal, order)
    if a is None:
        return None
    roots = np.roots(a)
    roots = roots[np.imag(roots) > 1e-6]  # complex-conjugate upper half only
    if len(roots) == 0:
        return None
    ang = np.angle(roots)
    freqs = ang * (fs / (2.0 * math.pi))
    bw = -0.5 * (fs / math.pi) * np.log(np.abs(roots) + 1e-12)
    band = (freqs > 90.0) & (freqs < fs / 2 - 50.0)
    # prefer resonances with reasonable bandwidth; relax the bandwidth gate if too few.
    keep = band & (bw < 700.0)
    sel = np.sort(freqs[keep])
    if len(sel) < n_form:
        sel = np.sort(freqs[band])
    if len(sel) < n_form:
        return None
    return tuple(float(f) for f in sel[:n_form])


def relative_formants(formants):
    """SPEAKER-RELATIVE formant frame: log-formants minus their mean. The mean-subtraction
    in log-space cancels the per-speaker vocal-tract-length scale (a VTL change is a
    multiplicative shift on all formants = an additive shift in log = removed by the mean).
    What survives is the speaker-INVARIANT formant PATTERN — and F2 is resolved with equal
    weight to F1/F3 (no low-frequency tilt to bury it). Returns a 3-vector."""
    lf = np.log(np.array(formants) + 1e-9)
    return lf - np.mean(lf)


# per-formant tolerance (in log-formant, speaker-relative units): how far a frame can
# differ before it starts excluding. Roughly a quarter-octave on each formant.
_FORM_SIGMA = np.array([0.18, 0.18, 0.18])
# abstain floor: a frame that disagrees beyond ABSTAIN_K sigmas stops adding evidence
# (it is "unsure"/uninformative rather than asserting a huge magnitude) — keeps the
# collapse SOFT, not a magnitude that dominates the scalar.
_ABSTAIN_K = 3.0
# vector weights per formant contrast. F2 carries front/back; give it full weight
# (the whole point of the fix is F2 NOT buried). All equal here = equal resolution.
_FORM_W = np.array([1.0, 1.0, 1.0])


def formant_admissibility(cand_formants, input_rel):
    """WEIGHTED-ADMISSIBILITY of one candidate formant frame against the input.
    NOT a dot product. Each formant F_i contributes a SOFT EXCLUSION: the candidate is
    penalised by how far |F_i^cand - F_i^input| sits (in speaker-relative log-formant
    space), as a log-admissibility -0.5*(d/sigma)^2, CLAMPED at an abstain floor so a
    wildly-off frame stops asserting (abstain where unsure). The three frames combine by
    INTERSECTION = SUM of log-admissibilities (the joint weighted-admissible region), each
    vector-weighted. Returns log-admissibility (higher = more admissible). The answer is
    the candidate that survives all three formant frames' weighted exclusions at once."""
    cand_rel = relative_formants(cand_formants)
    d = (cand_rel - input_rel) / _FORM_SIGMA          # per-formant deviation in sigmas
    # soft excluder per frame: gaussian log-admissibility, FLOORED at the abstain level.
    log_adm = -0.5 * d * d
    floor = -0.5 * _ABSTAIN_K * _ABSTAIN_K
    log_adm = np.maximum(log_adm, floor)              # abstain, don't over-assert
    # intersection = vector-weighted SUM of the per-frame log-admissibilities.
    return float(np.sum(_FORM_W * log_adm))


# ===========================================================================
# ANALYSIS-BY-SYNTHESIS VOWEL RECOGNITION (the agent's cognition).
# For each candidate vowel: synthesise while ADJUSTING speaker params (f0, formant-scale)
# to best match the input; lowest match-error candidate = the recognition.
# ===========================================================================

def abs_recognise(target_sig, fm, candidate_vowels, scale_grid=None, return_all=False):
    """The order-N solve for the vowel: hypothesise vowel -> synthesise (adjusting the
    speaker params) -> match -> pick the best. The speaker f0 is read off the input
    (source clock); the formant-scale (VTL) is searched over a small grid per candidate
    (the bounded AbS coordinate search). Lowest relative-envelope error wins."""
    n = len(target_sig)
    f0 = fm.estimate_f0(target_sig)
    if scale_grid is None:
        scale_grid = np.linspace(0.75, 1.30, 12)  # VTL / formant-scale search
    best_v, best_err = None, np.inf
    errs = {}
    for v in candidate_vowels:
        v_best = np.inf
        for s in scale_grid:
            synth = fm.synthesise({"vowel": v, "f0": f0, "scale": float(s), "n": n})
            e = match_error(synth, target_sig)
            if e < v_best:
                v_best = e
        errs[v] = v_best
        if v_best < best_err:
            best_err, best_v = v_best, v
    if return_all:
        return best_v, best_err, errs, f0
    return best_v, best_err


def abs_recognise_formant(target_sig, fm, candidate_vowels, scale_grid=None, return_all=False):
    """The F2-RESOLVING AbS solve: estimate the input's formant frame (F1,F2,F3 via LPC
    roots, speaker-relative), then for each candidate vowel search the speaker VTL scale
    (same bounded speaker search as abs_recognise) over the candidate's KNOWN formants
    (Peterson-Barney table x scale) and score by WEIGHTED-ADMISSIBILITY over the three
    formant frames — abstain at floor, intersect (sum of log-adm), NO dot product. The
    candidate that survives all three formant frames' weighted exclusions wins (highest
    log-admissibility). Abstains entirely (returns None) if the input formants are
    unestimable."""
    if scale_grid is None:
        scale_grid = np.linspace(0.75, 1.30, 12)  # SAME VTL / formant-scale search
    in_form = estimate_formants(target_sig)
    f0 = fm.estimate_f0(target_sig)
    if in_form is None:
        if return_all:
            return None, -np.inf, {}, f0
        return None, -np.inf
    input_rel = relative_formants(in_form)
    best_v, best_adm = None, -np.inf
    adms = {}
    for v in candidate_vowels:
        v_best = -np.inf
        for s in scale_grid:
            cand_formants = fm.formants_for({"vowel": v, "scale": float(s)})
            a = formant_admissibility(cand_formants, input_rel)
            if a > v_best:
                v_best = a
        adms[v] = v_best
        if v_best > best_adm:
            best_adm, best_v = v_best, v
    if return_all:
        return best_v, best_adm, adms, f0, in_form
    return best_v, best_adm


# ===========================================================================
# BASELINE — plain exemplar 1-NN in the same relative-envelope space (no model).
# ===========================================================================

def nn_recognise(target_env, bank):
    """1-nearest-neighbour over banked exemplar envelopes (the linear read-off baseline
    AbS must be compared against). bank = list of (vowel, env)."""
    best_v, best_d = None, np.inf
    for v, env in bank:
        d = float(np.sqrt(np.sum((target_env - env) ** 2)))
        if d < best_d:
            best_d, best_v = d, v
    return best_v


# ===========================================================================
# (a) SYNTHESIS QUALITY — does the source-filter approximate REAL vowels?
# ===========================================================================

def test_synthesis_quality(items):
    """For each vowel identity: match-error of the BEST source-filter synthesis (speaker-
    adjusted) to REAL vowels of the SAME identity, vs to real vowels of OTHER identities.
    If same-identity error < cross-identity error, the synthesis approximates the real
    vowel's formant structure and the match DISCRIMINATES."""
    fm = VowelSourceFilterModel()
    vowels = sorted(set(it["vowel"] for it in items))
    rows = []
    same_all, diff_all = [], []
    for v in vowels:
        reals_same = [it for it in items if it["vowel"] == v]
        reals_diff = [it for it in items if it["vowel"] != v]
        # sample to keep it fast
        rng = np.random.default_rng(0)
        ss = [reals_same[i] for i in rng.choice(len(reals_same), min(40, len(reals_same)), replace=False)]
        ds = [reals_diff[i] for i in rng.choice(len(reals_diff), min(40, len(reals_diff)), replace=False)]
        same_errs, diff_errs = [], []
        for it in ss:
            f0 = fm.estimate_f0(it["sig"])
            best = min(match_error(fm.synthesise({"vowel": v, "f0": f0, "scale": float(s), "n": len(it["sig"])}), it["sig"])
                       for s in np.linspace(0.8, 1.25, 8))
            same_errs.append(best)
        for it in ds:
            f0 = fm.estimate_f0(it["sig"])
            best = min(match_error(fm.synthesise({"vowel": v, "f0": f0, "scale": float(s), "n": len(it["sig"])}), it["sig"])
                       for s in np.linspace(0.8, 1.25, 8))
            diff_errs.append(best)
        same_m, diff_m = float(np.mean(same_errs)), float(np.mean(diff_errs))
        same_all.extend(same_errs)
        diff_all.extend(diff_errs)
        rows.append((v, same_m, diff_m, diff_m - same_m))
    return rows, float(np.mean(same_all)), float(np.mean(diff_all))


# ===========================================================================
# (b) AbS VOWEL RECOGNITION — cross-speaker, HELD-OUT speakers never banked.
# ===========================================================================

def test_abs_recognition(items, quick=False):
    """Leave-one-speaker-out cross-speaker recognition. AbS = solve-for-vowel via the
    forward model (no exemplars at all). 1-NN baseline = exemplars from the OTHER
    speakers (held-out speaker never banked). Chance = 1/n_vowels."""
    fm = VowelSourceFilterModel()
    vowels = sorted(set(it["vowel"] for it in items))
    speakers = sorted(set(it["speaker"] for it in items))
    n_vowels = len(vowels)

    rng = np.random.default_rng(1)
    mel_correct = mel_total = 0          # mel-L2 AbS baseline
    fmt_correct = fmt_total = fmt_abstain = 0  # formant-frame AbS (the named fix)
    nn_correct = nn_total = 0
    per_speaker = {}
    confusion = {v: {u: 0 for u in vowels} for v in vowels}        # mel-L2 AbS
    confusion_fmt = {v: {u: 0 for u in vowels} for v in vowels}    # formant-frame AbS

    for held in speakers:
        test_items = [it for it in items if it["speaker"] == held]
        bank_items = [it for it in items if it["speaker"] != held]  # held-out NEVER banked
        if quick:
            # subsample the test set per speaker for the smoke run
            if len(test_items) > 40:
                idx = rng.choice(len(test_items), 40, replace=False)
                test_items = [test_items[i] for i in idx]
        # precompute the 1-NN bank envelopes (relative space)
        bank = [(it["vowel"], relative_envelope(it["sig"])) for it in bank_items]
        s_fmt_c = s_fmt_t = 0
        for it in test_items:
            # (baseline) mel-L2 AbS recognition (pure forward model, no exemplars)
            mel_pred, _err = abs_recognise(it["sig"], fm, vowels)
            mel_total += 1
            if mel_pred == it["vowel"]:
                mel_correct += 1
            confusion[it["vowel"]][mel_pred] += 1
            # (THE FIX) formant-frame weighted-admissibility AbS recognition
            fmt_pred, _adm = abs_recognise_formant(it["sig"], fm, vowels)
            fmt_total += 1
            s_fmt_t += 1
            if fmt_pred is None:
                fmt_abstain += 1
            else:
                if fmt_pred == it["vowel"]:
                    fmt_correct += 1
                    s_fmt_c += 1
                confusion_fmt[it["vowel"]][fmt_pred] += 1
            # 1-NN baseline
            tenv = relative_envelope(it["sig"])
            nn_pred = nn_recognise(tenv, bank)
            nn_total += 1
            if nn_pred == it["vowel"]:
                nn_correct += 1
        per_speaker[held] = s_fmt_c / max(1, s_fmt_t)

    return {
        "n_vowels": n_vowels,
        "vowels": vowels,
        "chance": 1.0 / n_vowels,
        "mel_acc": mel_correct / max(1, mel_total),
        "mel_n": mel_total,
        "abs_acc": fmt_correct / max(1, fmt_total),   # 'abs' = the active match (the fix)
        "abs_n": fmt_total,
        "abs_abstain": fmt_abstain,
        "nn_acc": nn_correct / max(1, nn_total),
        "nn_n": nn_total,
        "per_speaker": per_speaker,
        "confusion": confusion,           # mel-L2 AbS confusion (for reference)
        "confusion_fmt": confusion_fmt,   # formant-frame AbS confusion (the fix)
    }


# ===========================================================================
# RUN
# ===========================================================================

def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 74)
    print("solve_for_n_vowel — SPEECH forward model (source-filter VOWEL) plugged into")
    print("the proven solve-for-N. AbS vowel recognition, cross-speaker, real FSDD vowels.")
    print("=" * 74)

    print("\nLoading real vowel nuclei from FSDD ...")
    mppps = 8 if quick else None
    items = load_vowel_dataset(max_per_class_per_speaker=mppps)
    vowels = sorted(set(it["vowel"] for it in items))
    speakers = sorted(set(it["speaker"] for it in items))
    print(f"  {len(items)} vowel nuclei | vowels={vowels} | speakers={speakers}")
    by_v = {v: sum(1 for it in items if it['vowel'] == v) for v in vowels}
    print(f"  per-vowel counts: {by_v}")

    print("\n" + "=" * 74)
    print("(a) SYNTHESIS QUALITY — source-filter match-error to REAL vowels")
    print("    (speaker-adjusted; same-identity vs cross-identity in relative-env space)")
    print("=" * 74)
    rows, same_all, diff_all = test_synthesis_quality(items)
    print(f"    {'vowel':>6} {'same-id err':>12} {'cross-id err':>13} {'gap(cross-same)':>16}")
    for v, sm, dm, gap in rows:
        flag = "OK" if gap > 0 else "<-- no margin"
        print(f"    {v:>6} {sm:>12.3f} {dm:>13.3f} {gap:>16.3f}  {flag}")
    print(f"\n    overall: same-id {same_all:.3f}  cross-id {diff_all:.3f}  "
          f"margin {diff_all-same_all:+.3f}  "
          f"({'synthesis approximates the real formant structure' if diff_all>same_all else 'NO discrimination — synthesis too poor'})")

    print("\n" + "=" * 74)
    print("(b) AbS VOWEL RECOGNITION — cross-speaker (LOSO), held-out never banked")
    print("=" * 74)
    res = test_abs_recognition(items, quick=quick)
    vs = res["vowels"]
    print(f"    n_vowels={res['n_vowels']}  chance={res['chance']*100:.1f}%  n={res['abs_n']}")
    print(f"    AbS mel-L2   (baseline, envelope match)        : {res['mel_acc']*100:.1f}%")
    print(f"    AbS FORMANT  (F2-resolving weighted-admis. FIX): {res['abs_acc']*100:.1f}%"
          f"   (abstain {res['abs_abstain']}/{res['abs_n']})")
    print(f"    1-NN         (exemplar baseline, banked)       : {res['nn_acc']*100:.1f}%")
    print(f"\n    per-speaker AbS-formant acc:")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"      {sp:>10}: {a*100:.1f}%")
    print(f"\n    AbS mel-L2 confusion (row=true, col=pred):")
    print("        " + " ".join(f"{u:>5}" for u in vs))
    for v in vs:
        print(f"    {v:>4}: " + " ".join(f"{res['confusion'][v][u]:>5}" for u in vs))
    print(f"\n    AbS FORMANT-FRAME confusion (row=true, col=pred) [the FIX]:")
    print("        " + " ".join(f"{u:>5}" for u in vs))
    for v in vs:
        print(f"    {v:>4}: " + " ".join(f"{res['confusion_fmt'][v][u]:>5}" for u in vs))

    # ---- VERDICT
    print("\n" + "=" * 74)
    print("VERDICT")
    discriminates = diff_all > same_all
    above_chance = res["abs_acc"] > res["chance"]
    beats_mel = res["abs_acc"] > res["mel_acc"]
    competitive = res["abs_acc"] >= 0.85 * res["nn_acc"]
    beats_nn = res["abs_acc"] >= res["nn_acc"]
    print(f"  AbS above chance         : {'YES' if above_chance else 'NO'} "
          f"({res['abs_acc']*100:.1f}% vs chance {res['chance']*100:.1f}%)")
    print(f"  formant beats mel-L2     : {'YES' if beats_mel else 'NO'} "
          f"(formant {res['abs_acc']*100:.1f}% vs mel-L2 {res['mel_acc']*100:.1f}%)")
    print(f"  competitive w/ 1-NN      : {'YES' if competitive else 'NO'} "
          f"(formant {res['abs_acc']*100:.1f}% vs 1-NN {res['nn_acc']*100:.1f}%)")
    print(f"  beats/matches 1-NN       : {'YES' if beats_nn else 'NO'}")
    if beats_mel and above_chance:
        print("  => the F2-RESOLVING formant-frame weighted-admissibility match IMPROVES")
        print("     recognition over the mel-L2 envelope baseline: resolving F2 with equal")
        print("     weight clears (some of) the front/back F2-collapse confusions.")
    else:
        print("  => HONEST KILL: the formant-frame match does NOT improve over mel-L2.")
        print("     See the limiter analysis printed above (input formant estimation /")
        print("     speaker-relative space / admissibility weighting).")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("SOLVE_FOR_N_VOWEL_COMPLETED")


if __name__ == "__main__":
    main()
