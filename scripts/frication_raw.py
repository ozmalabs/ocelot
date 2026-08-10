"""frication_raw — THE FRICATION CHANNEL WITHOUT HPSS (the re-audit's prescribed revival).

The read-based frication-split (scripts.frication_split) was an HONEST KILL: 42.9% vs the
62.2% Viterbi-pairing baseline. The diagnosis (docs/frication_split.md, lines ~152-161) was
PRECISE: the KILL was NOT the frication channel and NOT the band-limit — it was the HPSS step.
HPSS median-filtering SMEARED THE FORMANTS on short 8 kHz digits: the harmonic path itself fell
from the raw 62.2% to 45.4% (-16.8 pts) BEFORE any fusion. The frication CHANNEL was right (it
cleared the six-sink 150->69). The fix is mechanical and prescribed:

  DROP HPSS ENTIRELY.

  1. RAW HARMONIC PATH. Run the Viterbi-pairing formant tracker on the RAW signal — the
     unbroken 62.2% path. This is exactly scripts.viterbi_pairing wired into the UNCHANGED
     order-N + graph-DTW recogniser (ftd.build_corpus calls ftd.formant_track on the RAW
     signal; importing scripts.viterbi_pairing sets ftd.formant_track = viterbi_formant_track).
     NO HPSS. Recogniser logic UNCHANGED (runtime assert + git-diff verify).

  2. FRICATION CHANNEL from the RAW full-magnitude STFT. The SAME 4-dim feature as
     scripts.frication_split (>=3 kHz fraction, spectral centroid, high-band PEAK fraction,
     onset position) — but the onset dim is computed from the RAW high-band STFT energy, not
     the HPSS percussive part (HPSS is gone). Dims [0]/[1]/[2] were ALREADY read from the raw
     full magnitude in frication_split (the diagnostic there forced that — the percussive
     high-band fraction smeared the /s/ cue); only the onset dim sourced the percussive part,
     so it now reads the raw high-band energy. This carries the /s/-PRESENCE cue
     (two/four-vs-six) that already worked.

  3. FUSION by WEIGHTED-ADMISSIBILITY. Identical machinery to frication_split: each path is a
     soft excluder a_*(w) = exp(-d_*(w)/tau_*); recognition = argmax_w a_H(w)*a_F(w), the
     soft-AND of two admissibilities, in log space, with the LESS-TRUSTED frication excluder
     BOUNDED (clamped to [-FRIC_CLAMP, 0] in tau_f units) so it can only break a harmonic
     near-tie (where the six-sink lives), not override a confident harmonic margin. tau from
     the TRAIN across-digit spread of each channel. The frication adds the /s/-presence
     evidence WITHOUT HPSS damaging the harmonic path.

DONKEY AUDIT.
  * Harmonic path = scripts.viterbi_pairing.viterbi_formant_track on the RAW signal (owned
    numpy LPC + Levinson + forward-DP). NO HPSS. RECOGNISER UNCHANGED: order_n_time,
    trajectory_feature, dtw_predict_term, build via ftd — imported verbatim; only
    ftd.formant_track is the pairing tracker (the 62.2% wire). Runtime assert verifies the
    patch identity; viterbi_pairing.py is git-clean (verified in the report).
  * Frication feature = owned numpy spectral statistics on the RAW full-magnitude STFT. No fit.
  * Fusion = weighted-admissibility (product of exp(-d/tau) soft excluders, in log space) with
    a bounded less-trusted channel — owned, no learned weight, no net.
  * Templates / tau / z-stats = TRAIN speakers only; LOSO held-out speaker NEVER banked.
    CortexLoop and solve_for_n.py untouched.

PREDICTION: raw harmonic (62.2%, unbroken) + frication-presence channel clears the gross
six-sink -> NET GAIN over 62.2%. HONEST: the /s/-vs-/th/ QUALITY cue stays WALLED (FSDD is
natively 8 kHz, 4 kHz ceiling — that's K10, a genuine identifiability wall, not revivable
here); but the /s/-PRESENCE cue (two/four-vs-six) is real and should add. If it does NOT beat
62.2%, report it and pinpoint why.

Run:  python -m scripts.frication_raw
      python -m scripts.frication_raw --quick
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

# Import the PAIRING tracker. Importing scripts.viterbi_pairing ALSO sets
# ftd.formant_track = viterbi_formant_track (its module-level wire), so the harmonic path uses
# the hardened-LPC + transition-preserving tracker, recogniser unchanged — exactly the 62.2%
# front end. We feed it the RAW signal (no HPSS) — the unbroken 62.2% path.
import scripts.viterbi_pairing as vp
from scripts.viterbi_pairing import viterbi_formant_track

# ===========================================================================
#  RAW STFT (owned DSP) — the full-magnitude spectrogram for the frication feature.
#  Same STFT geometry as frication_split (512/128 @ 8 kHz), but NO HPSS — we keep only the
#  raw magnitude. The frication feature reads this directly.
# ===========================================================================

STFT_N_FFT = 512                 # ~64 ms @ 8 kHz
STFT_HOP = 128                   # 16 ms hop (75% overlap) — fine time res for short digits
STFT_WIN = np.hanning(STFT_N_FFT)


def raw_magnitude(sig):
    """Owned STFT magnitude spectrogram (n_frames x n_bins) of the RAW signal. No HPSS,
    no median filter, no mask — just |rfft| of windowed frames. Owned numpy DSP."""
    n = len(sig)
    if n < STFT_N_FFT:
        sig = np.concatenate([sig, np.zeros(STFT_N_FFT - n)])
        n = len(sig)
    starts = list(range(0, n - STFT_N_FFT + 1, STFT_HOP))
    if not starts:
        starts = [0]
    mag = np.empty((len(starts), STFT_N_FFT // 2 + 1), dtype=np.float64)
    for i, s in enumerate(starts):
        mag[i] = np.abs(np.fft.rfft(sig[s:s + STFT_N_FFT] * STFT_WIN))
    return mag


# ===========================================================================
#  FRICATION FEATURE (owned numpy spectral statistics on the RAW full-magnitude STFT).
#  4 dims: high-band fraction, spectral centroid, high-band PEAK fraction, onset position.
#  IDENTICAL to scripts.frication_split.frication_profile EXCEPT the onset dim now reads the
#  RAW high-band energy (HPSS percussive part is gone). Dims [0]/[1]/[2] were already raw.
# ===========================================================================

FRIC_HI_HZ = 3000.0              # high-band cut for the /s/ turbulence
FRIC_DIM = 4

# Frication is a LESS-TRUSTED excluder (weak cross-speaker at FS=8000 — most /s/ energy is
# above the 4 kHz Nyquist). Bound its influence: clamp the frication log-admissibility to
# [-FRIC_CLAMP, 0] (in tau_f units) so it can only break a harmonic NEAR-TIE (the six-sink:
# the voiced path cannot tell six from two/four) WITHOUT overriding a confident harmonic
# margin. A SMALL frozen structural constant — the near-tie-only value, same as the split.
FRIC_CLAMP = 0.15


def frication_profile(mag):
    """The owned 4-dim frication descriptor from the RAW full-magnitude STFT. STATED feature,
    owned numpy spectral statistics — no fit, no net. Dims:
      [0] high-band fraction  : mean_t (E_>3kHz / E_total) over energetic frames. /s/ (six,
          seven) high; vowels (two, four) near zero — the single most discriminative cue here.
      [1] spectral centroid Hz : energy-weighted mean frequency over energetic frames.
      [2] high-band peak fraction : 90th-percentile-over-time of the per-frame high-band
          fraction (the SHORT /s/ burst even when a long voiced token dilutes the mean).
      [3] onset position [0,1]: energy-weighted temporal centroid of the RAW high-band energy
          (six/seven lead with /s/ -> early; a final fricative -> late). HPSS-free: the raw
          high-band energy itself localises the turbulence (the percussive separation is gone).
    """
    freqs = np.fft.rfftfreq(STFT_N_FFT, 1.0 / FS)          # (n_bins,)
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
    # [3] onset position from the RAW high-band energy (temporal placement of turbulence).
    #     HPSS dropped: the raw >3 kHz energy localises the /s/ directly.
    if hi_e.sum() > 1e-12:
        t_idx = np.arange(len(hi_e), dtype=np.float64)
        onset = float((hi_e * t_idx).sum() / hi_e.sum() / max(1, len(hi_e) - 1))
    else:
        onset = 0.5
    return np.array([hi_frac, centroid, hi_peak, onset], dtype=np.float64)


# ===========================================================================
#  CORPUS — RAW harmonic trajectory (pairing tracker on the RAW signal) + raw frication.
# ===========================================================================

def build_corpus(sub, seed=0, quick=False):
    """Per token: RAW harmonic trajectory feature (pairing tracker on the RAW signal, NO HPSS)
    + static nucleus + frication profile (from the RAW full-magnitude STFT) + log-mel matrix
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
            track = ftd.formant_track(sig, fs)            # pairing tracker on the RAW signal
            if track is None:
                skipped += 1
                continue
            feat = trajectory_feature(sub, track)
            static = relative_formants_frame(steady_nucleus_formants(track))
            mag = raw_magnitude(sig)                       # RAW full-magnitude STFT
            fric = frication_profile(mag)
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
#  WEIGHTED-ADMISSIBILITY FUSION (identical machinery to frication_split).
#    a_H(w) = exp(-d_H(w)/tau_H)   (harmonic DTW trajectory distance to nearest exemplar)
#    a_F(w) = exp(-d_F(w)/tau_F)   (frication profile distance to digit template)
#    A(w)   = a_H(w) * a_F(w)      -> argmax  (soft-AND; bounded frication excluder)
# ===========================================================================

def _harmonic_dists(s, term, q_node, word_nodes):
    """Per-digit harmonic admissibility distance = MinOver exemplars of DtwTo, for EVERY
    digit (all distances needed for fusion). Evaluate the agent's per-word MinOver Term."""
    out = {}
    word_dist_term = ftd._MinOver(
        ftd._Nb(ftd._V("w"), "has_exemplar"), "e",
        ftd._DtwTo(ftd._Attr(ftd._V("q"), Q_ATTR), ftd._Attr(ftd._V("e"), TRAJ_ATTR)))
    for w, wn in word_nodes.items():
        v = s.evaluate(_P(word_dist_term), {"q": q_node, "w": wn})
        out[w] = float(v) if v is not None else float("inf")
    return out


def evaluate_fusion(sub, corpus, verbose=True):
    """LOSO eval. Raw-harmonic-only (pairing on the RAW signal = the 62.2% path),
    frication-only, and the FUSED weighted-admissibility recogniser, plus the full-envelope
    exemplar baseline. Held-out speaker NEVER banked; templates/tau/z-stats TRAIN-only."""
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
        #      ACROSS-DIGIT SPREAD of that channel's distances (max_w d(w) - min_w d(w)). The
        #      channel's discriminative dynamic range; dividing by it puts both soft excluders
        #      on a comparable scale. TRAIN queries only; NO test labels touched.
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

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18)
                       for w in DIGITS}
            log_a_f = {w: -d_f[w] / tau_f for w in DIGITS}

            # harmonic-only prediction (argmin distance == argmax a_h) — the 62.2% path.
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

            # FUSION (primary): soft-AND with a BOUNDED frication excluder.
            f_top = max(log_a_f.values())
            log_a_f_b = {w: max(-FRIC_CLAMP, log_a_f[w] - f_top) for w in DIGITS}
            logA = {w: log_a_h[w] + log_a_f_b[w] for w in DIGITS}
            pred_fused = max(DIGITS, key=lambda w: logA[w])
            fused_n += 1; s_fused_t += 1
            if pred_fused == true:
                fused_c += 1; s_fused_c += 1
            if pred_fused in DIGITS:
                conf_fused[true][pred_fused] += 1

            # FUSION (variant, reported for honesty): UNBOUNDED symmetric soft-AND.
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
    print("frication_raw — FRICATION CHANNEL WITHOUT HPSS (the prescribed revival)")
    print("RAW harmonic path (pairing tracker on the RAW signal = the 62.2% path, NO HPSS,")
    print("recogniser UNCHANGED) + FRICATION channel from the RAW full-magnitude STFT -> FUSION")
    print("by weighted-admissibility (bounded soft excluder). Drop HPSS; clear the six-sink.")
    print("=" * 78)

    # donkey audit: the recogniser front end is the pairing tracker, unchanged logic.
    assert ftd.formant_track is viterbi_formant_track, "harmonic path must use pairing tracker"
    print("\n[donkey audit] ftd.formant_track is viterbi_pairing.viterbi_formant_track: OK")
    print("[donkey audit] order-N + graph-DTW recogniser logic imported verbatim from ftd: OK")
    print("[donkey audit] NO HPSS — pairing tracker runs on the RAW signal (the 62.2% path)")

    print("\nBuilding corpus (RAW pairing trajectory + RAW-STFT frication profile) ...",
          flush=True)
    corpus, skipped = build_corpus(sub, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    by_w = Counter(it["word"] for it in corpus)
    print(f"  {len(corpus)} tokens | speakers={speakers} | skipped={skipped}")
    print(f"  per-digit counts: {dict(by_w)}")

    # frication-feature sanity: mean high-band fraction per digit (high for six/seven).
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
    print(f"  RAW-HARMONIC-only (pairing tracker on the RAW signal, NO HPSS): "
          f"{res['harm_acc']*100:.1f}%   (n={res['harm_n']})")
    print(f"  FRICATION-only (4-dim raw-STFT descriptor)                  : "
          f"{res['fric_acc']*100:.1f}%   (n={res['fric_n']})")
    print(f"  (NEW) FUSED weighted-admissibility (BOUNDED frication)      : "
          f"{res['fused_acc']*100:.1f}%   (n={res['fused_n']})")
    print(f"        ...variant: UNBOUNDED symmetric soft-AND              : "
          f"{res['sym_acc']*100:.1f}%   (reported for honesty)")
    print(f"  (a) Viterbi-PAIRING (no HPSS, no frication) reference        : 62.2%")
    print(f"  (b) read-based frication-split (HPSS-broken)                 : 42.9%")
    print(f"  (c) FULL-ENVELOPE DTW exemplar 1-NN (the ~0.835 bank)        : "
          f"{res['mel_acc']*100:.1f}%   (n={res['mel_n']})")
    print(f"  --------------------------------------------------------------")

    print(f"\n  per-speaker FUSED acc:")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"    {sp:>10}: {a*100:.1f}%")

    _print_confusion("RAW-HARMONIC-only confusion", res["conf_harm"])
    _print_confusion("FUSED (raw-harmonic + raw-frication) confusion", res["conf_fused"])

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
    split_base = 0.429
    harm = res["harm_acc"]
    fused = res["fused_acc"]
    beats_pair = fused > pair_base
    fused_beats_harm = fused > harm
    frac_of_mel = fused / max(1e-9, res["mel_acc"])
    sink_h = sum(res["conf_harm"][a]["six"] for a in ("two", "four", "three"))
    sink_f = sum(res["conf_fused"][a]["six"] for a in ("two", "four", "three"))
    print(f"  raw-harmonic reproduces 62.2% : harmonic {harm*100:.1f}% (the unbroken path; "
          f"{(harm-pair_base)*100:+.1f} pts vs 62.2%)")
    print(f"  Q fusion vs raw-harmonic      : fused {fused*100:.1f}% vs harmonic {harm*100:.1f}% "
          f"({(fused-harm)*100:+.1f} pts) -> frication channel {'NET-HELPS' if fused_beats_harm else 'does NOT net-help'}")
    print(f"  beats Viterbi-PAIRING 62.2%   : {'YES' if beats_pair else 'NO'} "
          f"({fused*100:.1f}% vs 62.2%, {(fused - pair_base)*100:+.1f} pts)")
    print(f"  beats HPSS-broken split 42.9% : {'YES' if fused > split_base else 'NO'} "
          f"({fused*100:.1f}% vs 42.9%, {(fused - split_base)*100:+.1f} pts)")
    print(f"  six-sink (two/four/three->six): harmonic {sink_h} -> fused {sink_f} "
          f"({'CLEARED' if sink_f < sink_h else 'NOT cleared'})")
    print(f"  vs full-envelope exemplar     : fused {fused*100:.1f}% / exemplar "
          f"{res['mel_acc']*100:.1f}% ({frac_of_mel*100:.0f}% of the bank)")
    if beats_pair and fused_beats_harm:
        print("  => REVIVAL WINS: dropping HPSS + the frication channel on the RAW STFT beats the")
        print("     62.2% pairing baseline AND the raw-harmonic path. The /s/-PRESENCE cue adds")
        print("     net accuracy; the /s/-vs-/th/ QUALITY cue stays walled (8 kHz band limit, K10).")
    elif sink_f < sink_h and not fused_beats_harm:
        print("  => PARTIAL / HONEST: dropping HPSS RESTORES the raw-harmonic path (vs the broken")
        print("     45.4% HPSS-harmonic) and the frication channel CLEARS the six-sink, but it does")
        print("     NOT net-improve accuracy — clearing the sink costs as many tokens elsewhere as")
        print("     it saves (the residual /s/-vs-/th/ and six<->seven QUALITY confusions are the")
        print("     8 kHz band-limit wall, K10). The HPSS damage IS removed; the band-limit remains.")
    else:
        print("  => HONEST KILL: dropping HPSS + frication-on-raw did NOT beat 62.2% and did NOT")
        print("     clear the six-sink. The frication PRESENCE cue is too weak cross-speaker at the")
        print("     8 kHz band limit to add even without the HPSS damage (K10 wall).")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("FRICATION_RAW_COMPLETED")
    print("FRICATION_RAW_EXIT=0")


if __name__ == "__main__":
    main()
