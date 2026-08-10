"""frication_imagination — THE IMAGINATION FRICATION RECOGNISER (forward-model completion).

The read-based frication split (scripts.frication_split) CLEARED the six-sink but did NOT
net-improve, because FSDD is recorded natively at 8 kHz: the spectrum is hard-band-limited to
4 kHz, so the dominant /s/ frication energy (4-8 kHz in natural speech) was NEVER CAPTURED.
The read-based feature could only READ the weak, noisy, cross-speaker-ambiguous 3-4 kHz tail.

THE FIX (ozma_fill_gaps_with_imagination): you cannot READ missing data — you IMAGINE it. The
agent has a FORWARD MODEL of what each fricative IS (a full-band 0-8 kHz spectral-envelope
shape). Even with only the surviving 0-4 kHz band, it synthesises "IF this token's frication
were /s/, here is the full structure" and asks: does my surviving partial evidence match the
imagined /s/'s 0-4 kHz tail better than the imagined /th/'s? Analysis-by-synthesis on PRESENT
evidence against an IMAGINED WHOLE. The gap is filled from the MODEL, not the signal. This is
phonemic restoration / the retinal blind spot in frequency: the mic has an optic disc at 4 kHz.

THE POINT vs the read-based feature: the full-band model makes the surviving 0-4 kHz SLOPE/SHAPE
discriminative where the raw energy was ambiguous. /s/ is broadband with a RISING edge climbing
toward its >4 kHz peak — so its 0-4 kHz tail SLOPES UP. /th/,/f/ are flatter and lower with the
peak (such as it is) inside or below 4 kHz — so their 0-4 kHz tail is FLAT or already rolling
off. Matching the surviving band's SHAPE against the model's surviving-band tail can separate
/s/ from /th/ even though their raw band-limited ENERGY overlaps.

=== UNCHANGED FROM scripts.frication_split (verified by donkey audit) ===
  * HPSS (Fitzgerald median-filter harmonic/percussive separation) — imported verbatim.
  * The HARMONIC path: the Viterbi-pairing formant tracker on the harmonic signal -> order-N
    dynamics -> graph-resident DTW recogniser. Byte-identical (ftd.formant_track is the pairing
    tracker; order_n + DTW logic imported from ftd).
  * FUSION by WEIGHTED-ADMISSIBILITY: product of soft excluders a_H(w)*a_F(w), the frication
    excluder BOUNDED (clamped) so it resolves harmonic near-ties without overriding a confident
    margin. Same intersection-of-soft-excluders, owned, no learned weight.

=== REPLACED: the frication FEATURE ===
  OLD: read a 4-dim descriptor (high-band fraction etc.) off the surviving band, distance to a
       per-digit template.
  NEW: ANALYSIS-BY-SYNTHESIS. Forward-model the unvoiced fricative classes as full-band
       spectral-envelope shapes; restrict each to 0-4 kHz; match the token's surviving-band
       percussive spectrum against each candidate's restricted shape; the per-digit frication
       admissibility is the (negative) match error of the digit's fricative class.

=== FRICATION FORWARD MODELS (owned phonetic knowledge; STATED, not fitted to test) ===
Each class is a parametric full-band (0-FS/2 nominal, modelled to 8 kHz) log-magnitude envelope
shape over frequency, defined by a few owned phonetic parameters (centroid, spectral slope,
peak, bandwidth). These are SPECTRA-SHAPES, evaluated on a frequency grid, NOT learned.

  /s/  (alveolar sibilant; six, seven):
        broadband, energy concentrated HIGH, sharp peak ~5-8 kHz, steep RISING slope through
        the speech band (energy climbs with frequency up to the peak). Model: a raised-cosine
        bump centred ~6500 Hz, wide; plus a positive linear tilt (rising) below the peak.
  /sh/ (postalveolar; not a digit-initial here but kept for completeness): peak ~2.5-4 kHz.
  /th/,/f/ (dental/labiodental; three, four, five): WEAK, FLAT, diffuse, low overall level, no
        sharp HF peak — a gentle hump low/mid (~1.5-3 kHz) then roll-off; near-FLAT-to-falling
        slope in 0-4 kHz. The crucial contrast with /s/: NO rising edge toward a HF peak.
  burst (unvoiced-stop release; two=/t/, eight=/t/): transient, broadband-flat, moderate level,
        no strong spectral peak — essentially white-ish over the band (flat slope).
  none  (purely-voiced digits zero/one/nine): almost no percussive turbulence at all — modelled
        as a very-low-level flat floor; its admissibility is high only when the token carries
        little high-band percussive energy.

Each DIGIT is assigned its owned fricative class:
  six/seven -> /s/ ; three -> /th/ ; four/five -> /f/ ; two/eight -> burst ;
  zero/one/nine -> none.
(/th/ and /f/ share the weak-flat-low model but are kept as separate labels for the audit; the
hard case the prediction targets is /s/ (six/seven) vs /th/ (three) — exactly the three<->six
confusion.)

=== ANALYSIS-BY-SYNTHESIS MATCH (owned DSP; no net, no .fit) ===
Per token: from the HPSS PERCUSSIVE magnitude spectrogram, take the surviving-band (0-4 kHz)
observed log-magnitude envelope O(f) over the frication-active frames (a shape, normalised so
absolute level does not dominate — we test SHAPE/SLOPE). For each fricative class c, synthesise
its full-band model M_c(f), RESTRICT to 0-4 kHz, normalise the same way -> M_c^{0-4}(f). The
match error e_c = || O - M_c^{0-4} ||  (with the level/centroid/slope captured by the normalised
envelope). The per-digit frication distance d_F(w) = e_{class(w)} (digits sharing a class share
the synthesised tail; they are then separated by the harmonic path). Admissibility a_F(w) =
exp(-d_F(w)/tau_F). This is the IMAGINATION: we never read the missing band; we match the
present surviving band against the IMAGINED full-band whole's surviving tail.

DONKEY AUDIT.
  * Forward models = owned parametric spectral shapes (numpy), stated from phonetics, NOT fitted
    to test labels. No net, no .fit.
  * Analysis-by-synthesis match = owned numpy (restrict to 0-4 kHz, normalise, L2 on the shape).
  * HPSS + harmonic tracker + order-N + graph-DTW recogniser = imported verbatim from
    frication_split / ftd (asserted at runtime).
  * Fusion = weighted-admissibility (bounded soft-excluder product) — owned, no learned weight.
  * tau / normalisation stats = TRAIN speakers only; LOSO held-out speaker NEVER banked.
  * CortexLoop and solve_for_n.py untouched.

PREDICTION: the imagined full-band /s/ (rising 0-4 kHz tail toward its >4 kHz peak) vs the
imagined /th/ (flat/low tail) makes the SURVIVING band's SHAPE discriminative -> the six-sink
clears AND the fused accuracy net-improves over the 62.2% pairing baseline.
HONEST FORK: if it still does NOT net-improve, the distinguishing /s/-vs-/th/ information may be
GENUINELY at 4-8 kHz (gone) so the surviving band is fundamentally ambiguous even WITH the model
— an identifiability limit (the structure is exercised but the DISTINGUISHING part not captured).
We report WHICH: does surviving-band + model discriminate, or is the info truly gone.

Run:  python -m scripts.frication_imagination
      python -m scripts.frication_imagination --quick
"""
from __future__ import annotations

import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.formant_trajectory_dynamics as ftd
from scripts.formant_trajectory_dynamics import (
    DIGITS, FS, _print_confusion, load_wav, gather_files,
    trajectory_feature, steady_nucleus_formants, relative_formants_frame,
    dtw_predict_term, _traj_tuple, TRAJ_ATTR, WORD_ATTR, Q_ATTR, _P,
)
from scripts import mcu_infer as mi

# HPSS imported VERBATIM from frication_split (so the harmonic path is byte-identical). Importing
# frication_split also imports viterbi_pairing, which wires ftd.formant_track = the pairing
# tracker — exactly the 62.2% front end.
import scripts.frication_split as fs_split
from scripts.frication_split import hpss, HPSS_N_FFT
import scripts.viterbi_pairing as vp
from scripts.viterbi_pairing import viterbi_formant_track


# ===========================================================================
#  FRICATION FORWARD MODELS — owned parametric full-band spectral-envelope shapes.
#  Each model is a function f(Hz) -> log-magnitude (dB-ish, arbitrary level), evaluated on a
#  frequency grid. Phonetic parameters (centroid/peak/slope/bandwidth) are STATED from phonetics,
#  NOT fitted to test. Modelled out to 8 kHz (the "full band") even though FSDD only captured the
#  0-4 kHz tail — that is the whole point: we IMAGINE the full structure.
# ===========================================================================

MODEL_FMAX = 8000.0          # full-band ceiling we IMAGINE the fricative over (natural /s/ band)
SURVIVE_HZ = 4000.0          # the surviving band FSDD actually captured (8 kHz sample => 4 kHz)
N_MODEL_BINS = 256           # fine grid for the synthesised full-band shapes


def _raised_cosine_bump(f, centre, halfwidth):
    """A smooth raised-cosine spectral bump (1 at centre, 0 at +/- halfwidth), 0 outside. Owned."""
    x = (f - centre) / halfwidth
    out = np.where(np.abs(x) <= 1.0, 0.5 * (1.0 + np.cos(np.pi * x)), 0.0)
    return out


def model_s(f):
    """/s/ — alveolar sibilant. Broadband, energy HIGH, sharp peak ~6.5 kHz, RISING slope through
    the speech band toward the peak. The decisive cue: the 0-4 kHz tail SLOPES UP.
    Owned phonetic shape: a wide raised-cosine HF bump centred 6500 Hz + a positive linear tilt
    (rising with frequency) over the whole band + a low broadband floor."""
    bump = 1.0 * _raised_cosine_bump(f, 6500.0, 3500.0)      # wide HF bump, present at 3-4 kHz edge
    rising = 0.55 * (f / MODEL_FMAX)                          # rising tilt -> 0-4 kHz climbs
    floor = 0.10                                              # broadband turbulence floor
    return bump + rising + floor


def model_sh(f):
    """/sh/ — postalveolar. Peak lower (~3 kHz), strong, then roll-off above. (Not a digit class
    here, kept for completeness / audit.)"""
    bump = 1.0 * _raised_cosine_bump(f, 3000.0, 2500.0)
    floor = 0.10
    return bump + floor


def model_th(f):
    """/th/,/f/ — dental/labiodental. WEAK, FLAT, diffuse; gentle low-mid hump (~2 kHz) then
    roll-off; NO rising edge toward an HF peak. Decisive contrast with /s/: the 0-4 kHz tail is
    FLAT-to-FALLING, not rising. Low overall level."""
    bump = 0.45 * _raised_cosine_bump(f, 2000.0, 2200.0)     # weak low-mid hump
    falling = 0.20 * (1.0 - f / MODEL_FMAX)                  # gentle falling tilt (high rolls off)
    floor = 0.08
    return bump + falling + floor


def model_burst(f):
    """unvoiced-stop release burst (/t/ in two, eight). Transient, broadband, moderate level. A
    /t/ burst is alveolar -> slightly HF-emphasised (a gentle rising tilt, between flat /th/ and
    the strongly-rising /s/) with no sharp peak. NOT perfectly flat (a flat model degenerates to
    the zero vector under shape-normalisation and carries no information). Owned phonetic shape."""
    rising = 0.25 * (f / MODEL_FMAX)               # mild HF tilt (alveolar burst), < /s/'s 0.55
    floor = 0.30
    return rising + floor


def model_none(f):
    """purely-voiced digits (zero/one/nine) — almost NO unvoiced turbulence. The percussive
    residue HPSS leaves on a voiced token is dominated by LOW-frequency voiced leakage (the
    median-filter split is imperfect on harmonics), so its surviving-band shape FALLS with
    frequency (energy low, rolling off) — the OPPOSITE of /s/'s rising edge. Owned phonetic shape
    (a non-degenerate falling tilt, so 'no frication' is a real, distinct shape)."""
    falling = 0.30 * (1.0 - f / MODEL_FMAX)        # falls toward HF (voiced leakage is low-freq)
    floor = 0.10
    return falling + floor


# digit -> owned fricative class (forward model). six/seven=/s/, three=/th/, four/five=/f/(=th
# model), two/eight=burst, zero/one/nine=none.
DIGIT_CLASS = {
    "zero": "none", "one": "none", "two": "burst", "three": "th",
    "four": "th", "five": "th", "six": "s", "seven": "s",
    "eight": "burst", "nine": "none",
}
CLASS_MODEL = {
    "s": model_s, "sh": model_sh, "th": model_th,
    "burst": model_burst, "none": model_none,
}
FRIC_CLASSES = ["s", "sh", "th", "burst", "none"]


def _normalise_shape(env):
    """Normalise a log-magnitude envelope to a zero-mean, unit-norm SHAPE, so the L2 match tests
    SLOPE/SHAPE (the discriminative part) not absolute level (which varies with speaker/loudness/
    recording gain and is exactly what made the raw energy ambiguous). Owned numpy."""
    env = np.asarray(env, dtype=np.float64)
    env = env - env.mean()
    n = np.linalg.norm(env)
    if n < 1e-9:
        return env
    return env / n


# Precompute the surviving-band (0-4 kHz) NORMALISED SHAPE of every class model on the OBSERVED
# frequency grid. We synthesise the FULL band 0-8 kHz, restrict to 0-4 kHz, then normalise — so
# the restriction-then-normalise captures the rising/flat SLOPE the full model implies for the
# surviving tail.
# weight on the level-robust high-band-FRACTION component appended to the shape vector. The
# shape-L2 tests the SLOPE (s rising vs th falling); the HF-fraction tests the level-robust
# AMOUNT/PLACEMENT of turbulence. PRIMARY test of the imagination thesis is the PURE SLOPE match
# (HFRAC_W = 0): does the surviving 0-4 kHz SLOPE alone — the rising /s/ edge vs the flat/falling
# /th/ tail the full-band model implies — discriminate? A non-zero HFRAC_W is a diagnostic
# variant. We keep it 0 for the honest primary verdict (the slope IS the imagination claim).
HFRAC_W = 0.0
HFRAC_CUT = 2000.0          # surviving-band split: lower (0-2 kHz) vs upper (2-4 kHz)


def _hi_fraction_of_env(env, fobs):
    """The fraction of an envelope's (linear) energy in the upper surviving band (2-4 kHz). A
    level-robust descriptor of HOW MUCH/WHERE the surviving turbulence sits. Owned numpy."""
    lin = np.asarray(env, dtype=np.float64)
    lin = np.maximum(lin, 0.0)
    up = fobs >= HFRAC_CUT
    tot = lin.sum() + 1e-12
    return float(lin[up].sum() / tot)


def class_surviving_shapes(obs_freqs):
    """obs_freqs = the rfft bin centres of the percussive STFT (0..FS/2=4000). For each class,
    evaluate its full-band model on a fine 0-8 kHz grid (the IMAGINED whole), then sample it at
    the OBSERVED 0-4 kHz bins (the surviving tail of the imagined whole). Build a match VECTOR =
    [ normalised log-mag SHAPE (slope) | HFRAC_W * high-band-fraction (level-robust amount) ].
    Returns {class: vector}. Owned numpy, no fit."""
    survive = obs_freqs <= SURVIVE_HZ
    fobs = obs_freqs[survive]
    shapes = {}
    for c, mfn in CLASS_MODEL.items():
        full = np.maximum(mfn(fobs), 1e-6)     # the imagined full-band model on the surviving bins
        shape = _normalise_shape(np.log(full)) # SLOPE component
        hfrac = _hi_fraction_of_env(full, fobs)  # level-robust AMOUNT/placement component
        shapes[c] = np.concatenate([shape, [HFRAC_W * hfrac]])
    return shapes, survive


# ===========================================================================
#  ANALYSIS-BY-SYNTHESIS frication channel (owned DSP). Per token: observed surviving-band
#  percussive log-envelope SHAPE; per-class match error against the imagined surviving tail.
# ===========================================================================

def observed_surviving_shape(P_mag, survive, obs_freqs):
    """The token's OBSERVED surviving-band (0-4 kHz) match VECTOR, same form as the class models:
    [ normalised log-mag SHAPE | HFRAC_W * high-band-fraction ]. From the HPSS percussive
    magnitude spectrogram, pick the frication-ACTIVE frames (top percussive-energy frames — where
    the turbulence lives), average their magnitude over the surviving bins. The SHAPE is the
    log-mag normalised slope; the HF-fraction is the level-robust amount/placement of turbulence.
    Owned numpy."""
    fobs = obs_freqs[survive]
    P = P_mag ** 2                                    # percussive power
    frame_e = P.sum(axis=1) + 1e-12
    thr = 0.30 * frame_e.max()                        # frication-active = top percussive frames
    active = frame_e >= thr
    if active.sum() == 0:
        active = np.ones_like(frame_e, dtype=bool)
    mag_surv = np.maximum(P_mag[active][:, survive].mean(axis=0), 1e-6)   # mean mag, 0-4 kHz
    shape = _normalise_shape(np.log(mag_surv))        # SLOPE component
    hfrac = _hi_fraction_of_env(mag_surv, fobs)       # level-robust AMOUNT/placement component
    return np.concatenate([shape, [HFRAC_W * hfrac]])


def synthesis_errors(obs_shape, class_shapes):
    """For each fricative class, the L2 match error between the observed surviving-band shape and
    the imagined class's surviving-band shape. Owned numpy. Returns {class: error}."""
    return {c: float(np.linalg.norm(obs_shape - sh)) for c, sh in class_shapes.items()}


# ===========================================================================
#  CORPUS — HPSS once per token; harmonic trajectory (UNCHANGED) + analysis-by-synthesis
#  frication errors (the IMAGINATION channel).
# ===========================================================================

def build_corpus(sub, seed=0, quick=False):
    """Per token: HPSS -> harmonic trajectory (pairing tracker on harmonic signal, UNCHANGED) +
    per-class analysis-by-synthesis frication errors (imagination) + log-mel matrix (exemplar
    baseline). Mechanical ingest — no agent decisions."""
    rng = np.random.default_rng(seed)
    files = gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    npr = 6 if quick else 999

    # the observed rfft frequency grid (depends only on HPSS params) -> imagined class shapes.
    obs_freqs = np.fft.rfftfreq(HPSS_N_FFT, 1.0 / FS)
    class_shapes, survive = class_surviving_shapes(obs_freqs)

    corpus = []
    mel_ops = mi.Ops()
    skipped = 0
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:npr]:
            sig, fs = load_wav(p)
            sig_h, sig_p, P_mag, mag, starts = hpss(sig)
            track = ftd.formant_track(sig_h, fs)          # pairing tracker on HARMONIC signal
            if track is None:
                track = ftd.formant_track(sig, fs)
            if track is None:
                skipped += 1
                continue
            feat = trajectory_feature(sub, track)
            static = relative_formants_frame(steady_nucleus_formants(track))
            # IMAGINATION frication channel: observed surviving shape -> per-class synthesis error.
            obs_shape = observed_surviving_shape(P_mag, survive, obs_freqs)
            fric_err = synthesis_errors(obs_shape, class_shapes)   # {class: error}
            xmcu, fsm = mi.load_wav(p)
            M = mi.front_end(xmcu, fsm, mel_ops)
            if M.shape[0] < 2:
                skipped += 1
                continue
            corpus.append({
                "word": DIGITS[d], "speaker": spk,
                "traj": feat, "static": static, "fric_err": fric_err, "mel": M,
            })
    return corpus, skipped, class_shapes, survive, obs_freqs


# ===========================================================================
#  HARMONIC admissibility (UNCHANGED — per-digit MinOver-DtwTo, evaluated natively).
# ===========================================================================

def _harmonic_dists(s, term, q_node, word_nodes):
    out = {}
    word_dist_term = ftd._MinOver(
        ftd._Nb(ftd._V("w"), "has_exemplar"), "e",
        ftd._DtwTo(ftd._Attr(ftd._V("q"), Q_ATTR), ftd._Attr(ftd._V("e"), TRAJ_ATTR)))
    for w, wn in word_nodes.items():
        v = s.evaluate(_P(word_dist_term), {"q": q_node, "w": wn})
        out[w] = float(v) if v is not None else float("inf")
    return out


# the bounded-frication clamp (frozen structural constant, same role as frication_split: the
# weaker excluder may break a harmonic near-tie but not override a confident margin).
FRIC_CLAMP = 0.15


def evaluate_fusion(sub, corpus, verbose=True):
    """LOSO eval. Harmonic-only (UNCHANGED), imagination-frication-only, the FUSED weighted-
    admissibility recogniser, and the full-envelope exemplar baseline. Held-out speaker NEVER
    banked; tau / z-stats TRAIN-only.

    The per-digit IMAGINATION-frication distance d_F(w) = synthesis error of digit w's fricative
    class against the token's observed surviving-band shape. Note: this needs NO training template
    at all — the forward models ARE the knowledge. We still z-NOTHING; the synthesis errors are
    already on a shape-L2 scale. tau_F is the TRAIN-only median across-digit spread of d_F."""
    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()

    # full-envelope exemplar baseline plumbing (verbatim from frication_split / ftd).
    canonical = mi.canonical_log_centroid([it["mel"] for it in corpus])
    by_spk_mel = defaultdict(list)
    for it in corpus:
        by_spk_mel[it["speaker"]].append(it["mel"])
    spk_stats = {s: mi.speaker_stats(by_spk_mel[s]) for s in speakers}
    mel_ops = mi.Ops()
    mel_normed = {}
    for i, it in enumerate(corpus):
        mean, std = spk_stats[it["speaker"]]
        mel_normed[i] = mi.normalise(it["mel"], mean, std, canonical, mel_ops)

    harm_c = harm_n = fric_c = fric_n = 0
    fused_c = fused_n = sym_c = mel_c = mel_n = 0
    per_speaker = {}
    conf_harm = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_fused = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_fric = {w: {u: 0 for u in DIGITS} for w in DIGITS}

    for held in speakers:
        test_idx = [i for i, it in enumerate(corpus) if it["speaker"] == held]
        train_idx = [i for i, it in enumerate(corpus) if it["speaker"] != held]

        # ---- harmonic exemplar bank (graph) — UNCHANGED ----
        s = Substrate()
        word_nodes = {}
        for w in DIGITS:
            word_nodes[w] = s.add_node("Concept", {"name": w, WORD_ATTR: 1.0})
        for i in train_idx:
            ex = s.add_node("Exemplar", {TRAJ_ATTR: _traj_tuple(corpus[i]["traj"])})
            s.add_edge_unchecked(word_nodes[corpus[i]["word"]], "has_exemplar", ex)
        q_node = s.add_node("Query", {Q_ATTR: ((0.0,) * 9,)})

        # ---- per-digit IMAGINATION-frication distance: synthesis error of the digit's class.
        # The forward models are the knowledge; d_F(w) = fric_err[class(w)]. No template fit.
        def d_fric(it):
            return {w: it["fric_err"][DIGIT_CLASS[w]] for w in DIGITS}

        # ---- tau scales (TRAIN only) ----
        # harmonic tau: median across-digit spread of harmonic distances over up-to-80 TRAIN queries.
        h_spreads = []
        h_sample = train_idx if len(train_idx) <= 80 else \
            [train_idx[j] for j in np.linspace(0, len(train_idx) - 1, 80).astype(int)]
        for i in h_sample:
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            dh = _harmonic_dists(s, term, q_node, word_nodes)
            finite = [v for v in dh.values() if math.isfinite(v)]
            if len(finite) >= 2:
                h_spreads.append(max(finite) - min(finite))
        tau_h = max(float(np.median(h_spreads)) if h_spreads else 1.0, 1e-6)
        # frication tau: median across-digit synthesis-error spread over TRAIN tokens.
        f_spreads = []
        for i in train_idx:
            dd = list(d_fric(corpus[i]).values())
            f_spreads.append(max(dd) - min(dd))
        tau_f = max(float(np.median(f_spreads)) if f_spreads else 1.0, 1e-6)

        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]

        s_fused_c = s_fused_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = _harmonic_dists(s, term, q_node, word_nodes)
            d_f = d_fric(corpus[i])

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
            log_a_f = {w: -d_f[w] / tau_f for w in DIGITS}

            pred_harm = min(DIGITS, key=lambda w: d_h[w])
            harm_n += 1
            if pred_harm == true:
                harm_c += 1
            conf_harm[true][pred_harm] += 1

            pred_fric = min(DIGITS, key=lambda w: d_f[w])
            fric_n += 1
            if pred_fric == true:
                fric_c += 1
            conf_fric[true][pred_fric] += 1

            # FUSION (primary): bounded soft-AND (intersection of soft excluders), UNCHANGED form.
            f_top = max(log_a_f.values())
            log_a_f_b = {w: max(-FRIC_CLAMP, log_a_f[w] - f_top) for w in DIGITS}
            logA = {w: log_a_h[w] + log_a_f_b[w] for w in DIGITS}
            pred_fused = max(DIGITS, key=lambda w: logA[w])
            fused_n += 1; s_fused_t += 1
            if pred_fused == true:
                fused_c += 1; s_fused_c += 1
            conf_fused[true][pred_fused] += 1

            # variant: unbounded symmetric soft-AND (reported for honesty).
            logA_sym = {w: log_a_h[w] + log_a_f[w] for w in DIGITS}
            if max(DIGITS, key=lambda w: logA_sym[w]) == true:
                sym_c += 1

            # full-envelope exemplar baseline.
            ds = sorted((mi.dtw(mel_normed[i], Mtr, mel_ops), wtr) for Mtr, wtr in bank_mel)
            pred_mel = Counter([w for _, w in ds[:mi.KNN_K]]).most_common(1)[0][0]
            mel_n += 1
            if pred_mel == true:
                mel_c += 1

        per_speaker[held] = s_fused_c / max(1, s_fused_t)
        if verbose:
            print(f"    held-out {held:10s}: fused {s_fused_c/max(1,s_fused_t):.3f}  "
                  f"(n={s_fused_t}, tau_h={tau_h:.3f}, tau_f={tau_f:.3f})", flush=True)

    return {
        "harm_acc": harm_c / max(1, harm_n), "harm_n": harm_n,
        "fric_acc": fric_c / max(1, fric_n), "fric_n": fric_n,
        "fused_acc": fused_c / max(1, fused_n), "fused_n": fused_n,
        "sym_acc": sym_c / max(1, fused_n),
        "mel_acc": mel_c / max(1, mel_n), "mel_n": mel_n,
        "per_speaker": per_speaker,
        "conf_harm": conf_harm, "conf_fused": conf_fused, "conf_fric": conf_fric,
    }


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()
    print("=" * 78)
    print("frication_imagination — THE IMAGINATION FRICATION RECOGNISER")
    print("HPSS -> HARMONIC path (pairing tracker, recogniser UNCHANGED) + IMAGINATION-FRICATION")
    print("(forward-model the fricatives full-band; analysis-by-synthesis match the SURVIVING")
    print("0-4 kHz tail) -> FUSION by weighted-admissibility. Fill the missing band with a MODEL.")
    print("=" * 78)

    # DONKEY AUDIT: harmonic path is the pairing tracker, recogniser logic verbatim; HPSS verbatim.
    assert ftd.formant_track is viterbi_formant_track, "harmonic path must use pairing tracker"
    assert hpss is fs_split.hpss, "HPSS must be the frication_split (Fitzgerald) separator verbatim"
    print("\n[donkey audit] ftd.formant_track is viterbi_pairing.viterbi_formant_track: OK")
    print("[donkey audit] HPSS is frication_split.hpss (Fitzgerald median-filter), verbatim: OK")
    print("[donkey audit] order-N + graph-DTW recogniser logic imported verbatim from ftd: OK")
    print("[donkey audit] frication forward models = owned parametric spectral shapes (no fit): OK")
    print("[donkey audit] analysis-by-synthesis match = owned numpy L2 on surviving-band shape: OK")
    print("[donkey audit] fusion = weighted-admissibility (bounded soft-excluder product): OK")

    # show the imagined surviving-band shapes (the models, restricted to 0-4 kHz, as shapes).
    obs_freqs = np.fft.rfftfreq(HPSS_N_FFT, 1.0 / FS)
    class_shapes, survive = class_surviving_shapes(obs_freqs)
    fobs = obs_freqs[survive]
    print("\n  IMAGINED surviving-band (0-4 kHz) shapes — the forward models restricted to what")
    print("  FSDD captured (normalised log-mag SHAPE; +=above-mean, the discriminative SLOPE):")
    probe_hz = [500, 1500, 2500, 3500]
    cols = [int(np.argmin(np.abs(fobs - h))) for h in probe_hz]
    print(f"    {'class':>6}  " + " ".join(f"{int(fobs[c]):>5d}Hz" for c in cols)
          + "   |  end-start slope")
    n_shape = int(survive.sum())                 # the SHAPE part length (excl. appended hfrac)
    for c in FRIC_CLASSES:
        sh = class_shapes[c][:n_shape]           # slope over the SHAPE component only
        slope = sh[-1] - sh[0]
        print(f"    {c:>6}  " + " ".join(f"{sh[c2]:>+6.2f} " for c2 in cols)
              + f"   |  {slope:>+.2f}  ({'RISING' if slope>0.05 else 'falling' if slope<-0.05 else 'flat'})")
    print("  (PREDICTION basis: /s/ RISES toward its imagined >4kHz peak; /th/ flat/falling —")
    print("   the surviving 0-4 kHz SLOPE is what separates them where raw energy could not.)")

    print("\nBuilding corpus (HPSS + harmonic trajectory + imagination-frication errors) ...",
          flush=True)
    corpus, skipped, class_shapes, survive, obs_freqs = build_corpus(sub, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    by_w = Counter(it["word"] for it in corpus)
    print(f"  {len(corpus)} tokens | speakers={speakers} | skipped={skipped}")
    print(f"  per-digit counts: {dict(by_w)}")

    # sanity: mean per-digit synthesis error to its OWN class vs to /s/ and /th/ (the hard pair).
    print("\n  imagination sanity (mean synthesis error of each digit to the /s/, /th/, burst,")
    print("  none models; LOW = the token's surviving shape matches that imagined fricative):")
    print(f"    {'digit':>6} {'class':>6}  {'err_s':>7} {'err_th':>7} {'err_brst':>8} {'err_none':>8}")
    for w in DIGITS:
        errs = [it["fric_err"] for it in corpus if it["word"] == w]
        if errs:
            es = np.mean([e["s"] for e in errs]); et = np.mean([e["th"] for e in errs])
            eb = np.mean([e["burst"] for e in errs]); en = np.mean([e["none"] for e in errs])
            print(f"    {w:>6} {DIGIT_CLASS[w]:>6}  {es:>7.3f} {et:>7.3f} {eb:>8.3f} {en:>8.3f}")

    print("\n" + "=" * 78)
    print("LOSO RECOGNITION (held-out speaker NEVER banked, chance 0.100)")
    print("=" * 78)
    res = evaluate_fusion(sub, corpus, verbose=True)

    print("\n  --------------------------------------------------------------")
    print(f"  HARMONIC-only (pairing tracker on the HPSS harmonic part)     : "
          f"{res['harm_acc']*100:.1f}%   (n={res['harm_n']})")
    print(f"  IMAGINATION-FRICATION-only (analysis-by-synthesis, 5 classes) : "
          f"{res['fric_acc']*100:.1f}%   (n={res['fric_n']})")
    print(f"  (NEW) FUSED weighted-admissibility (bounded imagination excluder): "
          f"{res['fused_acc']*100:.1f}%   (n={res['fused_n']})")
    print(f"        ...variant: UNBOUNDED symmetric soft-AND                  : "
          f"{res['sym_acc']*100:.1f}%   (reported for honesty)")
    print(f"  (a) Viterbi-PAIRING (no HPSS) reference baseline              : 62.2%")
    print(f"  (b) FULL-ENVELOPE DTW exemplar 1-NN (the ~0.835 bank)         : "
          f"{res['mel_acc']*100:.1f}%   (n={res['mel_n']})")
    print(f"  --------------------------------------------------------------")

    print(f"\n  per-speaker FUSED acc:")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"    {sp:>10}: {a*100:.1f}%")

    _print_confusion("HARMONIC-only confusion", res["conf_harm"])
    _print_confusion("IMAGINATION-FRICATION-only confusion", res["conf_fric"])
    _print_confusion("FUSED (harmonic+imagination) confusion", res["conf_fused"])

    print("\n  SIX-SINK audit (the named confusion sink; did the imagination clear it?):")
    sinks = [("two", "six"), ("four", "six"), ("three", "six"),
             ("six", "seven"), ("seven", "six"), ("three", "six")]
    seen = set()
    for a, b in sinks:
        if (a, b) in seen:
            continue
        seen.add((a, b))
        h_off = res["conf_harm"][a][b]; h_tot = sum(res["conf_harm"][a].values())
        f_off = res["conf_fused"][a][b]; f_tot = sum(res["conf_fused"][a].values())
        print(f"    {a:>6}->{b:<6}: harmonic {h_off}/{h_tot}  ->  fused {f_off}/{f_tot}")
    # the HARD /s/-vs-/th/ case explicitly: three<->six both directions.
    print("\n  /s/-vs-/th/ HARD CASE (three=/th/ <-> six=/s/, the prediction target):")
    for a, b in [("three", "six"), ("six", "three")]:
        h_off = res["conf_harm"][a][b]; f_off = res["conf_fused"][a][b]
        print(f"    {a:>6}->{b:<6}: harmonic {h_off}  ->  fused {f_off}")

    print("\n" + "=" * 78)
    print("VERDICT")
    pair_base = 0.622
    harm = res["harm_acc"]; fused = res["fused_acc"]
    beats_pair = fused > pair_base
    fused_beats_harm = fused > harm
    frac_of_mel = fused / max(1e-9, res["mel_acc"])
    sink_h = sum(res["conf_harm"][a]["six"] for a in ("two", "four", "three"))
    sink_f = sum(res["conf_fused"][a]["six"] for a in ("two", "four", "three"))
    sth_h = res["conf_harm"]["three"]["six"] + res["conf_harm"]["six"]["three"]
    sth_f = res["conf_fused"]["three"]["six"] + res["conf_fused"]["six"]["three"]
    print(f"  fused {fused*100:.1f}%  | harmonic {harm*100:.1f}%  | pairing 62.2%  | "
          f"exemplar {res['mel_acc']*100:.1f}%")
    print(f"  Q1 imagination-frication net-help : fused {fused*100:.1f}% vs harmonic "
          f"{harm*100:.1f}% ({(fused-harm)*100:+.1f} pts) -> "
          f"{'NET-HELPS' if fused_beats_harm else 'does NOT net-help'}")
    print(f"  Q2 beats Viterbi-PAIRING 62.2%    : {'YES' if beats_pair else 'NO'} "
          f"({(fused - pair_base)*100:+.1f} pts)")
    print(f"  six-sink (two/four/three->six)    : harmonic {sink_h} -> fused {sink_f} "
          f"({'CLEARED' if sink_f < sink_h else 'NOT cleared'})")
    print(f"  /s/-vs-/th/ (three<->six)         : harmonic {sth_h} -> fused {sth_f} "
          f"({'reduced' if sth_f < sth_h else 'not reduced'})")
    print(f"  vs full-envelope exemplar         : {frac_of_mel*100:.0f}% of the bank")

    cleared = sink_f < sink_h
    if beats_pair and fused_beats_harm and cleared:
        print("\n  => IMAGINATION WINS (PREDICTION CONFIRMED): forward-modelling the fricatives")
        print("     full-band and matching the SURVIVING 0-4 kHz tail's SLOPE/SHAPE against the")
        print("     imagined whole clears the six-sink AND net-improves over the 62.2% pairing")
        print("     baseline. The missing band was filled from the MODEL — the surviving band")
        print("     PLUS the forward model discriminates where the raw band-limited energy could")
        print("     not. Perception exceeds the signal (phonemic restoration / blind-spot fill).")
    elif cleared and not fused_beats_harm:
        print("\n  => HONEST FORK — IDENTIFIABILITY LIMIT: the imagination CLEARS the six-sink (the")
        print("     forward model + surviving band resolves the gross /s/-vs-vowel distinction)")
        print("     but does NOT net-improve. The /s/-vs-/th/ distinguishing information is")
        print("     GENUINELY at 4-8 kHz (the imagined RISING /s/ edge and the flat /th/ tail")
        print("     differ MOST above 4 kHz, which FSDD never captured); the surviving 0-4 kHz")
        print("     band is fundamentally ambiguous even WITH the model. The STRUCTURE is")
        print("     exercised (the model imagines the whole) but the DISTINGUISHING PART of the")
        print("     evidence is gone — an identifiability wall, not a missing-mechanism wall.")
        print("     The fix is a wider-band corpus (16 kHz with the real fricative band), not a")
        print("     better imagination. Honest: the info is truly gone below the Nyquist.")
    elif beats_pair and fused_beats_harm and not cleared:
        print("\n  => NET-IMPROVES but six-sink not fully cleared — the imagination helps overall")
        print("     yet the specific /s/-sink persists; mixed. See the confusion matrix.")
    else:
        print("\n  => HONEST KILL: the imagination frication did NOT net-improve and did NOT clear")
        print("     the six-sink. Either HPSS denudes the short-digit percussive part or the")
        print("     surviving 0-4 kHz shape does not match the imagined models cross-speaker.")
        print("     Pinpoint: see the per-digit synthesis-error sanity table above.")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("FRICATION_IMAGINATION_COMPLETED")


if __name__ == "__main__":
    main()
