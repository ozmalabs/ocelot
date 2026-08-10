"""frication_split — THE FRICATION SPLIT (the named next limiter after commit 104a75bf).

The Viterbi-pairing recogniser (scripts.viterbi_pairing) hit 62.2% LOSO but the gap to the
83.5% full-envelope exemplar is dominated by FRICATION. The voiced-frame LPC formant tracker
has no good candidate at broadband / unvoiced /s/ bursts, so `six` is the confusion sink
(two->six, four->six, three->six). The voiced path is structurally BLIND to the unvoiced
evidence (/s/ in six/seven, /th/ in three, the stop bursts) because it only reads frames the
energy gate calls voiced, and even there the LPC poles through frication are garbage.

THE FIX — separate the two physically-distinct kinds of structure with HPSS, handle each with
the apparatus it suits, and FUSE by weighted-admissibility.

  1. HPSS (Fitzgerald median-filter, owned numpy/scipy DSP, NO net). Median-filter the
     magnitude spectrogram:
       * along TIME  -> HARMONIC estimate (stable horizontal ridges = voiced formants).
       * along FREQ  -> PERCUSSIVE estimate (vertical transients = frication / bursts /
         unvoiced energy).
     Soft Wiener masks H = h^p/(h^p+pp^p), P = pp^p/(...). Reconstruct each component by
     applying its mask to the COMPLEX STFT and inverse-STFT (owned overlap-add).

  2. HARMONIC PATH. Run the Viterbi-pairing formant tracker (hardened-LPC + transition-
     preserving pseudo-Huber penalty) on the HARMONIC component (cleaner formants — the
     frication energy that planted spurious high poles is gone) -> order-N dynamics ->
     graph-resident DTW. The recogniser logic is UNCHANGED — imported verbatim from
     scripts.formant_trajectory_dynamics; we monkey-patch ONLY ftd.formant_track to the
     pairing tracker (same as scripts.viterbi_pairing), and feed it the harmonic signal.

  3. FRICATION PATH (owned feature, NO net/fit). From the PERCUSSIVE component, a per-token
     FRICATION PROFILE — a short fixed-length descriptor that characterises the unvoiced
     turbulence the voiced path cannot see. STATED feature (4 dims, all from the percussive
     STFT, owned numpy):
       (i)  high-band fraction  = mean over time of (energy above 3 kHz)/(total energy).
            /s/ (six, seven) dumps most of its energy >3-4 kHz; vowels almost none. This is
            the single most discriminative frication cue.
       (ii) spectral centroid (Hz) of the percussive part, mean over the percussive-active
            frames (the centre of gravity of the turbulence; /s/ high, /th/ lower-broadband,
            vowels low).
       (iii) percussive energy fraction = total percussive energy / total signal energy
            (how MUCH unvoiced turbulence the token carries at all — separates the fricative
            digits from the purely-voiced ones).
       (iv) onset position = the energy-weighted temporal centroid of the high-band
            percussive energy, in [0,1] of token duration (six/seven lead with /s/ -> early;
            a final fricative -> late; a stop burst -> a sharp spike). Captures WHERE the
            frication sits, which separates same-amount-of-frication digits.
     The frication TEMPLATE per digit = the mean frication profile over TRAIN speakers only
     (held-out speaker never banked). The frication channel is z-scored per-dim by the TRAIN
     pooled std so the 4 heterogeneous dims combine on a common scale.

  4. FUSION by WEIGHTED-ADMISSIBILITY (owned; NOT a dot product). The harmonic path gives,
     per candidate digit w, a soft admissibility a_H(w) from its DTW trajectory distance; the
     frication path gives a_F(w) from its frication-profile distance to the digit template.
     We INTERSECT the two soft excluders (a product of admissibilities — a candidate must be
     admitted by BOTH the voiced gesture AND the unvoiced evidence):
         A(w) = a_H(w) * a_F(w),   a_*(w) = exp(-d_*(w)/tau_*)
     and pick argmax A(w). This is the soft-AND of two excluders, not a weighted sum: the
     frication channel can VETO a digit the harmonic path liked (e.g. it pulls admissibility
     toward `two` away from `six` when there is no /s/ turbulence), and ADMIT on evidence the
     harmonic path is blind to. tau_H, tau_F are fixed scale constants (the median within-corpus
     distance of each channel, computed on TRAIN only) so neither channel's raw distance scale
     dominates; they are NOT tuned on the held-out test labels.

DONKEY AUDIT.
  * HPSS = owned numpy/scipy (scipy.ndimage.median_filter + np.fft rfft/irfft overlap-add).
    No net, no .fit().
  * Harmonic formant tracking = scripts.viterbi_pairing.viterbi_formant_track (owned numpy LPC
    + Levinson + forward-DP). RECOGNISER UNCHANGED: order_n_time, trajectory_feature,
    dtw_predict_term, build via ftd — the order-N + graph-DTW logic is byte-identical (we set
    ftd.formant_track to the pairing tracker, exactly as scripts.viterbi_pairing does).
  * Frication feature = owned numpy spectral statistics on the percussive STFT. No fit.
  * Fusion = weighted-admissibility (product of exp(-d/tau) soft excluders) — owned, no learned
    weight, no net.
  * Templates / tau / z-score stats = TRAIN speakers only; LOSO held-out speaker NEVER banked.
    CortexLoop and solve_for_n.py untouched.

PREDICTION: HPSS cleans the harmonic formants (less spurious-pole garbage through frication) AND
the frication feature handles the /s/ bursts the voiced path was blind to -> the six-sink clears
(two->six, four->six, three->six drop) -> accuracy beats 62.2% and climbs toward the 83.5%
exemplar. KILL/HONEST: if HPSS does not help (median-filter split imperfect on short ~0.4 s
digits; frication feature doesn't discriminate cross-speaker; fusion doesn't combine) report it
and pinpoint the next limiter (a better frication feature; QCP-FB candidates).

Run:  python -m scripts.frication_split
      python -m scripts.frication_split --quick
"""
from __future__ import annotations

import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np
from scipy.ndimage import median_filter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.formant_trajectory_dynamics as ftd
from scripts.formant_trajectory_dynamics import (
    DIGITS, FS, _print_confusion, load_wav, gather_files,
    trajectory_feature, steady_nucleus_formants, relative_formants_frame,
    dtw_predict_term, _traj_tuple, TRAJ_ATTR, WORD_ATTR, Q_ATTR, _P,
)
from scripts import mcu_infer as mi

# Import the PAIRING tracker. Importing scripts.viterbi_pairing ALSO sets
# ftd.formant_track = viterbi_formant_track (its module-level wire), so the harmonic path uses
# the hardened-LPC + transition-preserving tracker, recogniser unchanged — exactly the 62.2%
# front end. We then feed it the HARMONIC signal (below).
import scripts.viterbi_pairing as vp
from scripts.viterbi_pairing import viterbi_formant_track

# ===========================================================================
#  HPSS — Fitzgerald median-filter harmonic/percussive separation (owned DSP).
# ===========================================================================

HPSS_N_FFT = 512                 # ~64 ms @ 8 kHz; enough freq res for the harmonic ridges
HPSS_HOP = 128                   # 75% overlap (16 ms hop) — fine time res for short digits
HPSS_WIN = np.hanning(HPSS_N_FFT)
HPSS_KH = 17                     # median-filter length along TIME (harmonic) — odd
HPSS_KP = 17                     # median-filter length along FREQ (percussive) — odd
HPSS_POWER = 2.0                 # soft-mask exponent (Wiener-like)


def _stft(sig):
    """Owned STFT. Returns complex (n_frames x n_bins) and the frame starts."""
    n = len(sig)
    if n < HPSS_N_FFT:
        sig = np.concatenate([sig, np.zeros(HPSS_N_FFT - n)])
        n = len(sig)
    starts = list(range(0, n - HPSS_N_FFT + 1, HPSS_HOP))
    if not starts:
        starts = [0]
    S = np.empty((len(starts), HPSS_N_FFT // 2 + 1), dtype=np.complex128)
    for i, s in enumerate(starts):
        S[i] = np.fft.rfft(sig[s:s + HPSS_N_FFT] * HPSS_WIN)
    return S, starts, n


def _istft(S, starts, n):
    """Owned inverse STFT (overlap-add with window normalisation)."""
    out = np.zeros(n + HPSS_N_FFT)
    wsum = np.zeros(n + HPSS_N_FFT)
    for i, s in enumerate(starts):
        frame = np.fft.irfft(S[i], n=HPSS_N_FFT) * HPSS_WIN
        out[s:s + HPSS_N_FFT] += frame
        wsum[s:s + HPSS_N_FFT] += HPSS_WIN ** 2
    nz = wsum > 1e-9
    out[nz] /= wsum[nz]
    return out[:n]


def hpss(sig):
    """Fitzgerald median-filter HPSS. Returns (harmonic_signal, percussive_signal, P_mag,
    starts) where P_mag is the percussive MAGNITUDE spectrogram (n_frames x n_bins) used by
    the frication feature. Owned numpy/scipy DSP — median_filter + rfft/irfft. No net."""
    S, starts, n = _stft(sig)
    mag = np.abs(S)
    # harmonic estimate: median filter along TIME (axis 0) — smooths horizontal ridges.
    H = median_filter(mag, size=(HPSS_KH, 1), mode="reflect")
    # percussive estimate: median filter along FREQ (axis 1) — smooths vertical transients.
    Pp = median_filter(mag, size=(1, HPSS_KP), mode="reflect")
    # soft Wiener masks.
    Hp = H ** HPSS_POWER
    Ppp = Pp ** HPSS_POWER
    denom = Hp + Ppp + 1e-12
    mask_h = Hp / denom
    mask_p = Ppp / denom
    Sh = S * mask_h
    Sp = S * mask_p
    sig_h = _istft(Sh, starts, n)
    sig_p = _istft(Sp, starts, n)
    P_mag = mag * mask_p           # percussive magnitude spectrogram (onset/temporal feature)
    return sig_h, sig_p, P_mag, mag, starts


# ===========================================================================
#  FRICATION FEATURE (owned numpy spectral statistics on the percussive part).
#  4 dims: high-band fraction, spectral centroid, percussive-energy fraction, onset position.
# ===========================================================================

FRIC_HI_HZ = 3000.0              # high-band cut for the /s/ turbulence
FRIC_DIM = 4

# Frication is a LESS-TRUSTED excluder (weak cross-speaker at FS=8000 — most /s/ energy is
# above the 4 kHz Nyquist). A symmetric soft-AND lets it corrupt confident harmonic decisions.
# The principled weighted-admissibility treatment of a less-trusted excluder is to BOUND its
# influence: clamp the frication log-admissibility to [-FRIC_CLAMP, 0] (in tau_f units) so it
# can only break harmonic NEAR-TIES (where the six-sink confusions live: the voiced path cannot
# tell six from two) WITHOUT overriding a confident harmonic margin. It remains a soft excluder
# (an intersection, not a sum); it is just a bounded one. FRIC_CLAMP is a frozen structural
# constant: a SMALL fraction of a channel-spread, so the frication excluder only ever resolves a
# near-tie. NOTE (honest): the verdict is INSENSITIVE to this value — a diagnostic clamp sweep
# {0.15, 0.3, 0.5} all leave the FUSED accuracy BELOW the harmonic-only ceiling (the tighter the
# clamp, the closer fused -> harmonic-only; the looser, the closer fused -> the worse symmetric
# soft-AND). The frication channel clears the six-sink but cannot net-improve accuracy at any
# bound — so FRIC_CLAMP is NOT a tuned knob, it is frozen at the small "near-tie-only" value.
FRIC_CLAMP = 0.15


def frication_profile(sig, P_mag, mag, starts):
    """The owned 4-dim frication descriptor. STATED feature, owned numpy spectral statistics —
    no fit, no net. A direct diagnostic (raw 3-4 kHz high-band fraction per digit) showed the
    HPSS-PERCUSSIVE high-band fraction SMEARS the /s/ cue (six vs two/four), whereas the RAW
    full-spectrogram high-band fraction separates them cleanly — so the spectral-shape dims are
    read from the FULL magnitude (the discriminative band, 3-4 kHz, is what survives below the
    4 kHz Nyquist); the PERCUSSIVE part is used only for the temporal ONSET dim (it isolates the
    transient turbulence WHERE it sits). Dims:
      [0] high-band fraction  : mean_t (E_>3kHz / E_total) of the FULL spectrogram. /s/ (six,
          seven) high; vowels (two, four) near zero — the single most discriminative cue here.
      [1] spectral centroid Hz : energy-weighted mean frequency of the FULL spectrogram.
      [2] high-band peak fraction : the 90th-percentile-over-time of the per-frame high-band
          fraction (captures the SHORT /s/ burst even when averaged over a long voiced token
          dilutes the mean — the fricative is brief but intense).
      [3] onset position [0,1]: energy-weighted temporal centroid of high-band PERCUSSIVE energy
          (six/seven lead with /s/ -> early; a final fricative -> late).
    """
    freqs = np.fft.rfftfreq(HPSS_N_FFT, 1.0 / FS)          # (n_bins,)
    hi = freqs >= FRIC_HI_HZ
    me = mag ** 2                                           # FULL power per (frame,bin)
    frame_e = me.sum(axis=1) + 1e-12                       # (n_frames,)
    hi_e = me[:, hi].sum(axis=1)                           # (n_frames,)
    per_frame_hifrac = hi_e / frame_e                      # (n_frames,)
    active = frame_e > (0.05 * frame_e.max() + 1e-12)
    if active.sum() == 0:
        active = np.ones_like(frame_e, dtype=bool)
    # [0] high-band fraction over the energetic frames.
    hi_frac = float(np.mean(per_frame_hifrac[active]))
    # [1] spectral centroid (Hz), energy-weighted over active frames.
    num = (me[active] * freqs[None, :]).sum()
    den = me[active].sum() + 1e-12
    centroid = float(num / den)
    # [2] high-band PEAK fraction: 90th pct over time — the brief intense /s/ burst.
    hi_peak = float(np.percentile(per_frame_hifrac[active], 90)) if active.sum() else 0.0
    # [3] onset position from the PERCUSSIVE high-band energy (temporal placement of turbulence).
    pe = P_mag ** 2
    phi_e = pe[:, hi].sum(axis=1)
    if phi_e.sum() > 1e-12:
        t_idx = np.arange(len(phi_e), dtype=np.float64)
        onset = float((phi_e * t_idx).sum() / phi_e.sum() / max(1, len(phi_e) - 1))
    else:
        onset = 0.5
    return np.array([hi_frac, centroid, hi_peak, onset], dtype=np.float64)


# ===========================================================================
#  CORPUS — HPSS once per token; harmonic trajectory + frication profile.
# ===========================================================================

def build_corpus(sub, seed=0, quick=False):
    """Per token: HPSS -> harmonic trajectory feature (pairing tracker on the harmonic
    signal) + static nucleus + frication profile (from the percussive part) + log-mel matrix
    (for the full-envelope exemplar baseline). Mechanical ingest — no agent decisions."""
    rng = np.random.default_rng(seed)
    files = gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    npr = 6 if quick else 999
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
                # fall back to the raw signal if the harmonic part is too denuded to track
                track = ftd.formant_track(sig, fs)
            if track is None:
                skipped += 1
                continue
            feat = trajectory_feature(sub, track)
            static = relative_formants_frame(steady_nucleus_formants(track))
            fric = frication_profile(sig, P_mag, mag, starts)
            xmcu, fsm = mi.load_wav(p)
            M = mi.front_end(xmcu, fsm, mel_ops)
            if M.shape[0] < 2:
                skipped += 1
                continue
            corpus.append({
                "word": DIGITS[d], "speaker": spk,
                "traj": feat, "static": static, "fric": fric, "mel": M,
            })
    return corpus, skipped


# ===========================================================================
#  WEIGHTED-ADMISSIBILITY FUSION.
#    a_H(w) = exp(-d_H(w)/tau_H)   (harmonic DTW trajectory distance to nearest exemplar)
#    a_F(w) = exp(-d_F(w)/tau_F)   (frication profile distance to digit template)
#    A(w)   = a_H(w) * a_F(w)      -> argmax  (soft-AND of two excluders)
# ===========================================================================

def _harmonic_dists(s, term, q_node, word_nodes):
    """Per-digit harmonic admissibility distance = MinOver exemplars of DtwTo, for EVERY
    digit (we need all distances for fusion, not just the argmin). We evaluate the agent's
    per-word MinOver Term directly for each word."""
    out = {}
    word_dist_term = ftd._MinOver(
        ftd._Nb(ftd._V("w"), "has_exemplar"), "e",
        ftd._DtwTo(ftd._Attr(ftd._V("q"), Q_ATTR), ftd._Attr(ftd._V("e"), TRAJ_ATTR)))
    for w, wn in word_nodes.items():
        v = s.evaluate(_P(word_dist_term), {"q": q_node, "w": wn})
        out[w] = float(v) if v is not None else float("inf")
    return out


def evaluate_fusion(sub, corpus, verbose=True):
    """LOSO eval. Harmonic-only (pairing on the harmonic part), frication-only, and the FUSED
    weighted-admissibility recogniser, plus the full-envelope exemplar baseline. Held-out
    speaker NEVER banked; templates/tau/z-stats TRAIN-only."""
    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()

    # full-envelope exemplar baseline plumbing (verbatim from ftd).
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

    for held in speakers:
        test_idx = [i for i, it in enumerate(corpus) if it["speaker"] == held]
        train_idx = [i for i, it in enumerate(corpus) if it["speaker"] != held]

        # ---- harmonic exemplar bank (graph) ----
        s = Substrate()
        word_nodes = {}
        for w in DIGITS:
            word_nodes[w] = s.add_node("Concept", {"name": w, WORD_ATTR: 1.0})
        for i in train_idx:
            ex = s.add_node("Exemplar", {TRAJ_ATTR: _traj_tuple(corpus[i]["traj"])})
            s.add_edge_unchecked(word_nodes[corpus[i]["word"]], "has_exemplar", ex)
        q_node = s.add_node("Query", {Q_ATTR: ((0.0,) * 9,)})

        # ---- frication: z-score stats + per-digit template (TRAIN only) ----
        fr_train = np.array([corpus[i]["fric"] for i in train_idx])      # (n_tr x 4)
        fr_mean = fr_train.mean(axis=0)
        fr_std = fr_train.std(axis=0) + 1e-9
        fr_train_z = (fr_train - fr_mean) / fr_std
        templ = {}
        for w in DIGITS:
            rows = [fr_train_z[k] for k, i in enumerate(train_idx)
                    if corpus[i]["word"] == w]
            templ[w] = np.mean(rows, axis=0) if rows else np.zeros(FRIC_DIM)

        # ---- tau scales: each channel's tau = the median over TRAIN tokens of the per-token
        #      ACROSS-DIGIT SPREAD of that channel's distances (max_w d(w) - min_w d(w)). This
        #      is the channel's discriminative dynamic range; dividing by it puts both soft
        #      excluders on a comparable scale so NEITHER swamps the other. (The earlier
        #      median-NEAREST-distance is wrong: the nearest harmonic exemplar distance is ~0
        #      for the correct class, so tau_h collapsed to 0 and the harmonic excluder
        #      saturated — the channel-dominance bug.) Computed on TRAIN queries only; NO test
        #      labels touched. To bound cost, sample up to 80 TRAIN queries for the harmonic
        #      tau (each requires 10 native DTW MinOver evals).
        h_spreads = []
        h_sample = train_idx if len(train_idx) <= 80 else \
            [train_idx[j] for j in np.linspace(0, len(train_idx) - 1, 80).astype(int)]
        for i in h_sample:
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            dh = _harmonic_dists(s, term, q_node, word_nodes)
            finite = [v for v in dh.values() if math.isfinite(v)]
            if len(finite) >= 2:
                h_spreads.append(max(finite) - min(finite))
        tau_h = float(np.median(h_spreads)) if h_spreads else 1.0
        tau_h = max(tau_h, 1e-6)
        # frication tau: median across-digit template-distance spread over TRAIN tokens.
        f_spreads = []
        for k, i in enumerate(train_idx):
            z = fr_train_z[k]
            dd = [float(np.linalg.norm(z - templ[w])) for w in DIGITS]
            f_spreads.append(max(dd) - min(dd))
        tau_f = float(np.median(f_spreads)) if f_spreads else 1.0
        tau_f = max(tau_f, 1e-6)

        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]

        s_fused_c = s_fused_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            # harmonic distances for ALL digits.
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = _harmonic_dists(s, term, q_node, word_nodes)
            # frication distances for ALL digits (z-score the query by TRAIN stats).
            z = (corpus[i]["fric"] - fr_mean) / fr_std
            d_f = {w: float(np.linalg.norm(z - templ[w])) for w in DIGITS}

            # SOFT EXCLUDERS in LOG space (numerically stable; argmax of the product of
            # exp(-d/tau) excluders == argmin of the SUM of the scaled distances, since
            # a_h(w)*a_f(w) = exp(-(d_h/tau_h + d_f/tau_f)). Computing exp directly underflows
            # to 0 for every digit when distances >> tau, collapsing argmax to the first key;
            # the log form is the exact same soft-AND of two excluders without the underflow).
            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18)
                       for w in DIGITS}
            log_a_f = {w: -d_f[w] / tau_f for w in DIGITS}

            # harmonic-only prediction (argmin distance == argmax a_h).
            pred_harm = min(DIGITS, key=lambda w: d_h[w])
            harm_n += 1
            if pred_harm == true:
                harm_c += 1
            if pred_harm in DIGITS:
                conf_harm[true][pred_harm] += 1

            # frication-only prediction.
            pred_fric = min(DIGITS, key=lambda w: d_f[w])
            fric_n += 1
            if pred_fric == true:
                fric_c += 1

            # FUSION (primary): soft-AND with a BOUNDED frication excluder. The frication
            # log-admissibility is shifted to its own max (so the best digit contributes 0) and
            # CLAMPED to [-FRIC_CLAMP, 0]: it can only pull DOWN the admissibility of digits the
            # frication evidence excludes, by at most FRIC_CLAMP tau_f — enough to break a
            # harmonic near-tie (the six-sink), not enough to override a confident harmonic
            # margin. Still an intersection of soft excluders, not a sum; the weaker excluder is
            # bounded. log A(w) = log a_h(w) + clamp(log a_f(w) - max_v log a_f(v), -CLAMP, 0).
            f_top = max(log_a_f.values())
            log_a_f_b = {w: max(-FRIC_CLAMP, log_a_f[w] - f_top) for w in DIGITS}
            logA = {w: log_a_h[w] + log_a_f_b[w] for w in DIGITS}
            pred_fused = max(DIGITS, key=lambda w: logA[w])
            fused_n += 1; s_fused_t += 1
            if pred_fused == true:
                fused_c += 1; s_fused_c += 1
            if pred_fused in DIGITS:
                conf_fused[true][pred_fused] += 1

            # FUSION (variant, reported for honesty): the UNBOUNDED symmetric soft-AND.
            logA_sym = {w: log_a_h[w] + log_a_f[w] for w in DIGITS}
            if max(DIGITS, key=lambda w: logA_sym[w]) == true:
                sym_c += 1

            # full-envelope exemplar baseline.
            ds = sorted((mi.dtw(mel_normed[i], Mtr, mel_ops), wtr)
                        for Mtr, wtr in bank_mel)
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
        "conf_harm": conf_harm, "conf_fused": conf_fused,
    }


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()
    print("=" * 78)
    print("frication_split — THE FRICATION SPLIT (named next after 104a75bf, 62.2%)")
    print("HPSS (median-filter) -> HARMONIC path (pairing formant tracker, recogniser")
    print("UNCHANGED) + FRICATION path (owned 4-dim percussive descriptor) -> FUSION by")
    print("weighted-admissibility (product of soft excluders). Target: clear the six-sink.")
    print("=" * 78)

    # donkey audit: confirm the recogniser front end is the pairing tracker, unchanged logic.
    assert ftd.formant_track is viterbi_formant_track, "harmonic path must use pairing tracker"
    print("\n[donkey audit] ftd.formant_track is viterbi_pairing.viterbi_formant_track: OK")
    print("[donkey audit] order-N + graph-DTW recogniser logic imported verbatim from ftd: OK")

    print("\nBuilding corpus (HPSS + harmonic trajectory + frication profile) ...", flush=True)
    corpus, skipped = build_corpus(sub, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    by_w = Counter(it["word"] for it in corpus)
    print(f"  {len(corpus)} tokens | speakers={speakers} | skipped={skipped}")
    print(f"  per-digit counts: {dict(by_w)}")

    # frication-feature sanity: mean high-band fraction per digit (should be high for six/seven).
    print("\n  frication-feature sanity (mean per digit; raw, not z-scored):")
    print(f"    {'digit':>6}  {'hi_frac':>8} {'centroidHz':>10} {'hi_peak':>9} {'onset':>6}")
    for w in DIGITS:
        fr = np.array([it["fric"] for it in corpus if it["word"] == w])
        if len(fr):
            m = fr.mean(axis=0)
            print(f"    {w:>6}  {m[0]:>8.3f} {m[1]:>10.0f} {m[2]:>9.3f} {m[3]:>6.3f}")

    print("\n" + "=" * 78)
    print("LOSO RECOGNITION (held-out speaker NEVER banked, chance 0.100)")
    print("=" * 78)
    res = evaluate_fusion(sub, corpus, verbose=True)

    print("\n  --------------------------------------------------------------")
    print(f"  HARMONIC-only (pairing tracker on the HPSS harmonic part)  : "
          f"{res['harm_acc']*100:.1f}%   (n={res['harm_n']})")
    print(f"  FRICATION-only (4-dim percussive descriptor)               : "
          f"{res['fric_acc']*100:.1f}%   (n={res['fric_n']})")
    print(f"  (NEW) FUSED weighted-admissibility (BOUNDED frication excluder): "
          f"{res['fused_acc']*100:.1f}%   (n={res['fused_n']})")
    print(f"        ...variant: UNBOUNDED symmetric soft-AND               : "
          f"{res['sym_acc']*100:.1f}%   (reported for honesty)")
    print(f"  Viterbi-PAIRING (no HPSS, no frication) reference baseline : 62.2%")
    print(f"  (b) FULL-ENVELOPE DTW exemplar 1-NN (the ~0.835 bank)      : "
          f"{res['mel_acc']*100:.1f}%   (n={res['mel_n']})")
    print(f"  --------------------------------------------------------------")

    print(f"\n  per-speaker FUSED acc:")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"    {sp:>10}: {a*100:.1f}%")

    _print_confusion("HARMONIC-only confusion", res["conf_harm"])
    _print_confusion("FUSED (harmonic+frication) confusion", res["conf_fused"])

    print("\n  SIX-SINK audit (the named confusion sink; did fusion clear it?):")
    sinks = [("two", "six"), ("four", "six"), ("three", "six"),
             ("six", "seven"), ("seven", "six")]
    for a, b in sinks:
        h_off = res["conf_harm"][a][b]; h_tot = sum(res["conf_harm"][a].values())
        f_off = res["conf_fused"][a][b]; f_tot = sum(res["conf_fused"][a].values())
        print(f"    {a:>6}->{b:<6}: harmonic {h_off}/{h_tot}  ->  fused {f_off}/{f_tot}")

    print("\n" + "=" * 78)
    print("VERDICT")
    pair_base = 0.622
    harm = res["harm_acc"]
    fused = res["fused_acc"]
    beats_pair = fused > pair_base
    fused_beats_harm = fused > harm
    harm_beats_pair = harm > pair_base
    frac_of_mel = fused / max(1e-9, res["mel_acc"])
    # six-sink cleared? sum the three named into->six offsets, harmonic vs fused.
    sink_h = sum(res["conf_harm"][a]["six"] for a in ("two", "four", "three"))
    sink_f = sum(res["conf_fused"][a]["six"] for a in ("two", "four", "three"))
    print(f"  Q1 HPSS-harmonic vs pairing  : harmonic {harm*100:.1f}% vs 62.2% "
          f"({(harm-pair_base)*100:+.1f} pts) -> HPSS {'HELPS' if harm_beats_pair else 'does NOT help'} the harmonic path")
    print(f"  Q2 fusion vs HPSS-harmonic   : fused {fused*100:.1f}% vs harmonic {harm*100:.1f}% "
          f"({(fused-harm)*100:+.1f} pts) -> frication channel {'NET-HELPS' if fused_beats_harm else 'does NOT net-help'}")
    print(f"  beats Viterbi-PAIRING 62.2%  : {'YES' if beats_pair else 'NO'} "
          f"({fused*100:.1f}% vs 62.2%, {(fused - pair_base)*100:+.1f} pts)")
    print(f"  six-sink (two/four/three->six): harmonic {sink_h} -> fused {sink_f} "
          f"({'CLEARED' if sink_f < sink_h else 'NOT cleared'})")
    print(f"  vs full-envelope exemplar    : fused {fused*100:.1f}% / exemplar "
          f"{res['mel_acc']*100:.1f}% ({frac_of_mel*100:.0f}% of the exemplar bank)")
    if beats_pair and fused >= 0.95 * res["mel_acc"]:
        print("  => FRICATION SPLIT WINS BIG: HPSS + frication fusion clears the six-sink and")
        print("     reaches the full-envelope exemplar bank.")
    elif beats_pair and fused_beats_harm:
        print("  => FRICATION SPLIT WINS: HPSS-clean harmonic + the frication channel (the /s/")
        print("     evidence the voiced path was blind to) beat the 62.2% pairing baseline AND")
        print("     the HPSS-harmonic path. Not yet at the exemplar bank — next limiter below.")
    elif sink_f < sink_h and not fused_beats_harm:
        print("  => PARTIAL / HONEST: the frication split CLEARS the six-sink (the named goal) but")
        print("     the frication channel does NOT net-improve accuracy — clearing the sink costs")
        print("     as many tokens elsewhere as it saves. ROOT LIMITER: FSDD is recorded NATIVELY")
        print("     at 8 kHz, so the spectrum is hard-band-limited to 4 kHz — the dominant /s/")
        print("     frication energy (4-8 kHz in natural speech) was NEVER CAPTURED. Only the weak")
        print("     3-4 kHz tail survives; it separates two/four-vs-six but not three (/th/ is also")
        print("     3-4 kHz broadband) and is too noisy cross-speaker to net-help. HPSS+frication")
        print("     is the right STRUCTURE; the band-limited corpus is the wall. Next limiter: a")
        print("     wider-band digit corpus (16 kHz source with the real fricative band), or QCP-FB")
        print("     candidates to sharpen the harmonic path on what IS present.")
    else:
        print("  => HONEST KILL: the frication split did NOT beat the 62.2% pairing baseline and")
        print("     did NOT clear the six-sink. HPSS over short digits denudes the harmonic")
        print("     formants and/or the frication feature does not discriminate cross-speaker.")
        print("     ROOT LIMITER: FSDD is natively 8 kHz (4 kHz band limit) — the /s/ frication")
        print("     band (4-8 kHz) was never recorded. Next limiter: a 16 kHz source / QCP-FB.")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("FRICATION_SPLIT_COMPLETED")


if __name__ == "__main__":
    main()
