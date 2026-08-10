"""viterbi_formant_tracker — THE CONTINUITY FIX (the named top fix, commit 767d61f2).

The formant-trajectory + order-N dynamics recogniser
(scripts.formant_trajectory_dynamics) is stuck at ~58.9% (vs 83.5% full-envelope
exemplar). The cross-field survey (767d61f2) named the DOMINANT defect: it is NOT
sharpness, it is CONTINUITY. Per-frame LPC-root formants are estimated INDEPENDENTLY,
so the F1/F2/F3 assignment jumps and swaps frame-to-frame; the order-N operator
(velocity/curvature) then DIFFERENCES that jumpy track and AMPLIFIES the assignment
noise into the signal it is supposed to read. A clean order-2 curvature on a track
that swapped F2<->F3 between frames is pure artefact.

THE FIX = a GLOBAL min-cost path that assigns one pole per formant slot across the
WHOLE token with a frame-to-frame jump penalty (the continuity constraint). This is
the SENSE / world-adapter TRANSDUCTION — how the formant tracks are PRODUCED. The
RECOGNITION (order-N dynamics + speaker-relative + graph-resident DTW Argmin) is the
agent's cognition and is UNCHANGED: this module imports it VERBATIM from
scripts.formant_trajectory_dynamics and only swaps the track-production front end.

WHAT CHANGES (the ONLY change): formant_track().
  OLD (formant_trajectory_dynamics.formant_track): per voiced frame call
       estimate_formants() -> the 3 lowest in-band LPC-root frequencies, INDEPENDENTLY.
       No cross-frame coupling. F1/F2/F3 are "whichever three sorted lowest THIS frame"
       -> swaps when a pole drops out / a spurious pole appears.
  NEW (this module's viterbi_formant_track): per voiced frame extract ALL candidate
       LPC-root poles (frequency + bandwidth/Q), then a VITERBI-DP tracker assigns one
       pole to each of F1/F2/F3 across all frames as the GLOBAL minimum-cost path:
         * EMISSION cost = candidate fit: distance to a nominal formant centre (in
           log-Hz) + a bandwidth/Q penalty (narrow high-Q poles preferred, wide/spurious
           poles penalised). A formant slot with no in-range candidate pays a miss cost
           and re-uses the nearest pole (kept, the slot is never empty).
         * TRANSITION cost = lambda * |log f_t - log f_{t-1}| per slot (the CONTINUITY
           penalty on a frame-to-frame frequency jump) PLUS a hard ordering constraint
           F1 < F2 < F3 (any frame state violating the ordering is inadmissible = +inf).
         * Viterbi forward (cumulative min-cost per state) + backtrace = the global
           smooth continuous F1/F2/F3 tracks.

DONKEY AUDIT.
  * The Viterbi-DP tracker is OWNED world-adapter TRANSDUCTION (formant estimation =
    a SENSE), implemented in owned numpy. The Viterbi min-cost-path IS the same
    min-cost-path object as the agent's DtwTo Term; but a forward-DP-with-backtrace over
    a per-frame product trellis (states = ordered candidate-triples) is a stateful DP
    whose cumulative-cost table + backpointers are not cleanly expressible as a single
    MinOver/Argmin reduction over a flat node set without materialising every trellis
    cell as a graph node and a fixed-point rule. Per the build rule ("native IF cleanly
    expressible; else owned numpy, STATE which") it is owned numpy. STATED.
  * The RECOGNITION is the agent's, UNCHANGED: order_n_time (the agent's nth_order_terms
    native-evaluated), trajectory_feature, the graph-resident dtw_predict_term
    (DtwTo/MinOver/Argmin native eval), evaluate_clean — ALL imported verbatim from
    scripts.formant_trajectory_dynamics. NO recogniser logic is altered here.
  * Exemplars are TRAIN speakers only; LOSO held-out speaker NEVER banked. CortexLoop and
    the flat solve_for_n.py are untouched.

PREDICTION: continuity gives smooth tracks -> order-N (velocity/curvature) becomes clean
signal not amplified assignment noise -> accuracy climbs from 58.9% toward the 83.5%
exemplar. KILL/HONEST: if it does NOT improve (candidates too poor through frication /
Nyquist so Viterbi confidently interpolates a wrong path; OR continuity over-smooths the
fast formant transitions that ARE the discriminative order-N signal) report it and
pinpoint the next limiter (better candidates = QCP-FB; HPSS frication split).

Run:  python -m scripts.viterbi_formant_tracker
      python -m scripts.viterbi_formant_tracker --quick
"""
from __future__ import annotations

import math
import os
import sys
import time
import wave
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

# Reuse the LPC machinery (owned all-pole inversion) from the vowel rung.
from scripts.solve_for_n_vowel import lpc_coeffs

# Import the RECOGNITION machinery VERBATIM (the agent's cognition — UNCHANGED).
# These are the order-N dynamics + the graph-resident DTW recogniser + the LOSO
# evaluator + the corpus builder + the printing helpers. We monkey-patch ONLY the
# track-production function (formant_track) that build_corpus calls.
import scripts.formant_trajectory_dynamics as ftd
from scripts.formant_trajectory_dynamics import (
    DIGITS, FS, FRAME_MS, HOP_MS, VOICED_FLOOR,
    load_wav, gather_files, evaluate_clean, _print_confusion,
)

# LPC order for the candidate poles. Survey called for order 12-14 (more poles =>
# better candidate coverage of the upper formants); the per-frame baseline used 10.
LPC_ORDER = 12

# ===========================================================================
#  STEP 1 — PER-FRAME CANDIDATE POLES (the candidate set).
#  Per frame, the candidate formant poles = the LPC roots: each in-band complex
#  pole gives a (frequency, bandwidth) candidate. We HARDEN the candidate set by
#  pruning on bandwidth/Q (drop very-wide, spurious, near-Nyquist poles), but keep
#  ALL surviving narrow high-Q poles (NOT just the 3 lowest — the Viterbi tracker
#  needs the full candidate set to choose continuously from).
# ===========================================================================

# bandwidth gate for a candidate pole to survive (Hz). A formant resonance is a
# narrow high-Q pole; very wide poles are source tilt / spurious. 700 Hz matches the
# vowel rung's estimate_formants gate; we keep it as the candidate admission bound.
CAND_BW_MAX = 700.0
# frequency band: above the f0/glottal region, below Nyquist margin (FSDD = 8 kHz).
CAND_F_LO = 90.0
CAND_F_HI = FS / 2 - 50.0     # 3950 Hz


def candidate_poles(signal, fs=FS, order=LPC_ORDER):
    """The candidate formant poles for ONE frame: every in-band, bandwidth-admissible
    LPC root as a (freq_Hz, bandwidth_Hz) pair. Owned DSP (LPC roots). Returns a list
    of (f, bw) sorted by frequency, or [] if the frame yields no LPC model."""
    a = lpc_coeffs(signal, order)
    if a is None:
        return []
    roots = np.roots(a)
    roots = roots[np.imag(roots) > 1e-6]            # upper-half complex conjugates
    if len(roots) == 0:
        return []
    ang = np.angle(roots)
    freqs = ang * (fs / (2.0 * math.pi))
    bw = -0.5 * (fs / math.pi) * np.log(np.abs(roots) + 1e-12)
    cands = []
    for f, b in zip(freqs, bw):
        if not (CAND_F_LO < f < CAND_F_HI):
            continue
        if b <= 0 or b > CAND_BW_MAX:               # bandwidth/Q hardening
            continue
        cands.append((float(f), float(b)))
    cands.sort(key=lambda c: c[0])
    return cands


# ===========================================================================
#  STEP 2 — VITERBI-DP TRACKER (the continuity).
#  Trellis: each frame state = an ORDERED triple of candidate poles assigned to
#  (F1,F2,F3). EMISSION cost = sum over slots of [log-Hz distance to the slot's
#  nominal centre + a bandwidth/Q penalty]. TRANSITION cost = lambda * sum over
#  slots of |log f_t - log f_{t-1}| (the continuity jump penalty). Ordering F1<F2<F3
#  is enforced by only enumerating increasing triples. Global min-cost path via
#  Viterbi forward (cumulative min cost per state) + backtrace.
#  Owned numpy world-adapter transduction (STATED in the donkey audit).
# ===========================================================================

# Nominal formant slot CENTRES (Hz) for the emission cost — broad anchors, NOT a
# per-vowel table: just "F1 is low, F2 is mid, F3 is high" so the emission cost gives
# each slot a sensible home and breaks ties. These are the standard adult-speaker
# formant-range centres (geometric-mean of the usual F1/F2/F3 spans); they are speaker-
# GENERIC anchors, and the recognition downstream is speaker-RELATIVE (log minus mean),
# so a per-token VTL scale does not leak through. NOT fitted.
NOMINAL_HZ = np.array([500.0, 1500.0, 2700.0])
LOG_NOMINAL = np.log(NOMINAL_HZ)
# emission: weight on the log-Hz distance to the nominal slot centre.
W_NOMINAL = 1.0
# emission: weight on the bandwidth penalty (narrow high-Q poles preferred). Bandwidth
# normalised by CAND_BW_MAX so it is O(1) like the log-distance term.
W_BW = 0.5
# transition (continuity): weight on the frame-to-frame log-frequency jump per slot.
# This is THE knob that converts independent per-frame estimates into a continuous
# track: lambda=0 recovers the per-frame greedy assignment; large lambda over-smooths.
LAMBDA_JUMP = 4.0
# cost of a slot having NO admissible candidate in range (the slot still gets the
# nearest available pole, but pays this miss so the path prefers frames with real poles).
MISS_COST = 3.0


def _frame_states(cands):
    """Enumerate the admissible ORDERED frame states (one pole per F1<F2<F3 slot) for a
    frame's candidate pole list. A state is a triple of indices (i1,i2,i3) into `cands`
    with i1<i2<i3 (the F1<F2<F3 ordering constraint built in). If fewer than 3 candidate
    poles survive, we SYNTHESISE missing slots by re-using poles (the nearest pole fills
    the empty slot, flagged with a miss cost) so the track is never broken — a frame is
    never dropped, which is what let the old per-frame track lose/swap formants."""
    n = len(cands)
    if n == 0:
        return []
    if n >= 3:
        states = []
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    states.append(((i, j, k), 0))   # (indices, n_missing)
        return states
    # n == 1 or 2: pad by re-using the highest pole(s); slots beyond available pay a miss.
    if n == 1:
        return [(((0, 0, 0)), 2)]
    # n == 2: assign the two poles to the two best-fitting consecutive slots, pad the 3rd.
    return [(((0, 1, 1)), 1), (((0, 0, 1)), 1)]


def _state_freqs_bws(cands, idx):
    fs_ = np.array([cands[i][0] for i in idx], dtype=np.float64)
    bw_ = np.array([cands[i][1] for i in idx], dtype=np.float64)
    return fs_, bw_


def _emission_cost(cands, idx, n_missing):
    """Emission cost of assigning candidate poles `idx` to (F1,F2,F3): log-Hz distance
    to the nominal slot centres + a bandwidth/Q penalty (narrow preferred). Plus the
    miss penalty for any synthesised/padded slot."""
    fs_, bw_ = _state_freqs_bws(cands, idx)
    log_f = np.log(fs_ + 1e-9)
    dist = np.sum((log_f - LOG_NOMINAL) ** 2)               # to nominal centres
    bw_pen = np.sum(bw_ / CAND_BW_MAX)                       # narrow high-Q preferred
    return W_NOMINAL * dist + W_BW * bw_pen + MISS_COST * n_missing


def viterbi_formant_track(sig, fs):
    """F1,F2,F3 per VOICED frame across the WHOLE token, as the GLOBAL Viterbi
    minimum-cost path over per-frame candidate LPC poles with a continuity (jump)
    penalty and an F1<F2<F3 ordering constraint. Replaces the per-frame-independent
    formant_track. Owned numpy transduction. Returns an (n_frames x 3) array of raw Hz
    formants (one continuous pole per slot per frame), or None.

    Same voiced-frame gating as the per-frame baseline (so the ONLY difference vs the
    58.9% run is per-frame-independent -> Viterbi-tracked assignment)."""
    flen = int(fs * FRAME_MS / 1000)
    hop = int(fs * HOP_MS / 1000)
    if len(sig) < flen:
        return None
    starts = list(range(0, len(sig) - flen + 1, hop))
    energies = np.array([np.sqrt(np.mean(sig[s:s + flen] ** 2)) for s in starts])
    if energies.max() <= 1e-9:
        return None
    thr = VOICED_FLOOR * energies.max()

    # --- per-frame candidate poles (only over voiced frames) ---
    frame_cands = []
    for s, e in zip(starts, energies):
        if e < thr:
            continue
        c = candidate_poles(sig[s:s + flen], fs)
        if c:
            frame_cands.append(c)
    if len(frame_cands) < 3:
        return None

    # --- per-frame enumerated states + their emission costs ---
    frame_states = []     # list per frame of (idx_triple, freqs(3,), emission_cost)
    for cands in frame_cands:
        states = _frame_states(cands)
        if not states:
            frame_states.append(None)
            continue
        rows = []
        for idx, nmiss in states:
            fs_, _ = _state_freqs_bws(cands, idx)
            rows.append((idx, fs_, _emission_cost(cands, idx, nmiss)))
        frame_states.append(rows)
    # drop any frame that produced no states (shouldn't happen given the >=1 pole guard)
    frame_states = [r for r in frame_states if r]
    if len(frame_states) < 3:
        return None

    # --- Viterbi forward: cumulative min cost per state + backpointers ---
    T = len(frame_states)
    # init t=0 with emission only
    prev_cost = np.array([row[2] for row in frame_states[0]], dtype=np.float64)
    prev_logf = [np.log(row[1] + 1e-9) for row in frame_states[0]]
    backptr = []          # backptr[t][s] = best previous-state index
    cost_tables = [prev_cost]

    for t in range(1, T):
        states = frame_states[t]
        ns = len(states)
        cur_cost = np.full(ns, np.inf)
        cur_bp = np.full(ns, -1, dtype=int)
        cur_logf = [np.log(row[1] + 1e-9) for row in states]
        for s in range(ns):
            emit = states[s][2]
            lf_s = cur_logf[s]
            # transition cost from each previous state = lambda * sum |dlog f| per slot
            best_p, best_c = -1, np.inf
            for p in range(len(prev_cost)):
                jump = LAMBDA_JUMP * float(np.sum(np.abs(lf_s - prev_logf[p])))
                c = prev_cost[p] + jump
                if c < best_c:
                    best_c, best_p = c, p
            cur_cost[s] = best_c + emit
            cur_bp[s] = best_p
        backptr.append(cur_bp)
        cost_tables.append(cur_cost)
        prev_cost = cur_cost
        prev_logf = cur_logf

    # --- backtrace from the min-cost final state ---
    s = int(np.argmin(prev_cost))
    path = [s]
    for t in range(T - 1, 0, -1):
        s = int(backptr[t - 1][s])
        path.append(s)
    path.reverse()

    track = np.array([frame_states[t][path[t]][1] for t in range(T)], dtype=np.float64)
    return track


# ===========================================================================
#  WIRE: swap ONLY the track-production front end into the (unchanged) recogniser.
#  build_corpus, trajectory_feature, order_n_time, dtw_predict_term, evaluate_clean
#  all live in scripts.formant_trajectory_dynamics and call ftd.formant_track. We
#  replace that one symbol with the Viterbi tracker. Nothing in the recognition path
#  is edited.
# ===========================================================================

ftd.formant_track = viterbi_formant_track
ftd.LPC_ORDER = LPC_ORDER          # candidates use order-12 (survey 12-14)


# ===========================================================================
#  TRACK-CONTINUITY DIAGNOSTIC (audit only — proves the tracks got smoother).
#  Mean per-slot log-frequency jump |dlog f| over a corpus of tracks: the SMALLER
#  it is, the more continuous the track. This is the quantity the order-N operator
#  differences; the per-frame baseline's jumpiness is exactly the amplified noise.
# ===========================================================================

def mean_track_jump(tracks):
    js = []
    for tr in tracks:
        if tr is None or tr.shape[0] < 2:
            continue
        lf = np.log(tr + 1e-9)
        js.append(float(np.mean(np.abs(np.diff(lf, axis=0)))))
    return float(np.mean(js)) if js else float("nan")


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()
    print("=" * 76)
    print("viterbi_formant_tracker — THE CONTINUITY FIX (commit 767d61f2 top fix)")
    print("FSDD digits, full token, cross-speaker LOSO. Per-frame-INDEPENDENT LPC-root")
    print("formants -> VITERBI-DP min-cost path (continuity + F1<F2<F3) -> smooth tracks")
    print("-> the SAME order-N dynamics + graph-resident DTW recogniser, UNCHANGED.")
    print("=" * 76)

    # ---- quick A/B continuity audit on a sample of tokens (per-frame vs Viterbi) ----
    print("\nTrack-continuity audit (mean per-slot |dlog f| frame-to-frame; "
          "lower = smoother) ...", flush=True)
    files = gather_files()
    import random
    rng = random.Random(0)
    sample = rng.sample(files, min(120, len(files)))
    pf_tracks, vt_tracks = [], []
    # the OLD per-frame-independent track (re-derived here, baseline reference only)
    from scripts.solve_for_n_vowel import estimate_formants

    def per_frame_track(sig, fs):
        flen = int(fs * FRAME_MS / 1000); hop = int(fs * HOP_MS / 1000)
        if len(sig) < flen:
            return None
        starts = list(range(0, len(sig) - flen + 1, hop))
        en = np.array([np.sqrt(np.mean(sig[s:s + flen] ** 2)) for s in starts])
        if en.max() <= 1e-9:
            return None
        thr = VOICED_FLOOR * en.max()
        rows = []
        for s, e in zip(starts, en):
            if e < thr:
                continue
            f = estimate_formants(sig[s:s + flen], fs=fs, order=10, n_form=3)
            if f is not None:
                rows.append(f)
        return np.asarray(rows) if len(rows) >= 3 else None

    for path, d, spk, idx in sample:
        sig, fs = load_wav(path)
        pf_tracks.append(per_frame_track(sig, fs))
        vt_tracks.append(viterbi_formant_track(sig, fs))
    pf_jump = mean_track_jump(pf_tracks)
    vt_jump = mean_track_jump(vt_tracks)
    print(f"  per-frame-independent track jump : {pf_jump:.4f}")
    print(f"  VITERBI-tracked track jump       : {vt_jump:.4f}")
    print(f"  => continuity {'IMPROVED' if vt_jump < pf_jump else 'NOT improved'} "
          f"({(1 - vt_jump / pf_jump) * 100:+.1f}% jump reduction)")

    print("\nBuilding corpus (VITERBI-tracked formant trajectories + order-N dynamics; "
          "native order-N audit per token) ...", flush=True)
    corpus, skipped = ftd.build_corpus(sub, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    by_w = Counter(it["word"] for it in corpus)
    print(f"  {len(corpus)} tokens | speakers={speakers} | skipped={skipped}")
    print(f"  per-digit counts: {dict(by_w)}")
    fdim = corpus[0]["traj"].shape[1] if corpus else 0
    print(f"  trajectory feature dim = {fdim} "
          f"([F1,F2,F3 | dF1,dF2,dF3 | ddF1,ddF2,ddF3], speaker-relative)")
    print(f"  native order-N audit: PASSED (native nth_order_terms == numpy diff "
          f"for every token, else build would have raised)")

    print("\n" + "=" * 76)
    print("LOSO RECOGNITION (held-out speaker NEVER banked, chance 0.100)")
    print("Recogniser = UNCHANGED scripts.formant_trajectory_dynamics (order-N + DTW)")
    print("=" * 76)
    res = evaluate_clean(sub, corpus, verbose=True)

    print("\n  --------------------------------------------------------------")
    print(f"  (a) STATIC single-nucleus formant 1-NN (order-0 snapshot) : "
          f"{res['stat_acc']*100:.1f}%   (n={res['stat_n']})")
    print(f"  PER-FRAME baseline (independent LPC formants, prior run)   : "
          f"58.9%   (the thing the continuity fix must beat)")
    print(f"  (NEW) VITERBI-TRACKED formants + order-N dynamics, DTW     : "
          f"{res['dyn_acc']*100:.1f}%   (n={res['dyn_n']})")
    print(f"  (b) FULL-ENVELOPE DTW exemplar 1-NN (the ~0.835 bank)      : "
          f"{res['mel_acc']*100:.1f}%   (n={res['mel_n']})")
    print(f"  --------------------------------------------------------------")

    print(f"\n  per-speaker VITERBI-dynamics acc:")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"    {sp:>10}: {a*100:.1f}%")

    _print_confusion("VITERBI-tracked (trajectory+order-N) confusion", res["conf_dyn"])

    # ---- residual-confusion audit: did three<->eight / the sibilant cluster change? ----
    print("\n  Residual-confusion audit (did the named residuals change?):")
    watch = [("three", "eight"), ("eight", "three"),
             ("six", "seven"), ("seven", "six"),
             ("six", "two"), ("two", "six")]
    for a, b in watch:
        off = res["conf_dyn"][a][b]
        tot = sum(res["conf_dyn"][a].values())
        print(f"    {a:>6}->{b:<6}: {off}/{tot}")

    print("\n" + "=" * 76)
    print("VERDICT")
    pf_base = 0.589
    dyn = res["dyn_acc"]
    beats_pf = dyn > pf_base
    frac_of_mel = dyn / max(1e-9, res["mel_acc"])
    print(f"  continuity (jump) reduced : {'YES' if vt_jump < pf_jump else 'NO'} "
          f"({pf_jump:.4f} -> {vt_jump:.4f})")
    print(f"  beats per-frame 58.9%     : {'YES' if beats_pf else 'NO'} "
          f"({dyn*100:.1f}% vs 58.9%, {(dyn - pf_base)*100:+.1f} pts)")
    print(f"  vs full-envelope exemplar : viterbi {dyn*100:.1f}% / exemplar "
          f"{res['mel_acc']*100:.1f}% ({frac_of_mel*100:.0f}% of the exemplar bank)")
    if beats_pf and dyn >= 0.95 * res["mel_acc"]:
        print("  => CONTINUITY WINS BIG: Viterbi-smooth tracks make order-N clean signal;")
        print("     recognition clears the per-frame ceiling and reaches the exemplar bank.")
    elif beats_pf:
        print("  => CONTINUITY IMPROVES recognition: smooth tracks beat per-frame-independent.")
        print("     Order-N dynamics on continuous formants is cleaner signal. Not yet at the")
        print("     exemplar bank — next limiter is candidate quality (QCP-FB) / frication.")
    else:
        print("  => HONEST KILL: Viterbi continuity did NOT beat the per-frame 58.9% baseline.")
        print("     Either the LPC candidates are too poor through frication / near-Nyquist")
        print("     (Viterbi confidently interpolates a wrong path), or the continuity penalty")
        print("     OVER-SMOOTHS the fast formant transitions that ARE the discriminative")
        print("     order-N signal. See the jump audit + confusion above. Next limiter:")
        print("     better candidates (QCP-FB) and HPSS frication split, per survey 767d61f2.")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("VITERBI_FORMANT_TRACKER_COMPLETED")


if __name__ == "__main__":
    main()
