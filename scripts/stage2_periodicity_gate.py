"""STAGE 2 — segmentation-coherence gate, RE-RUN on the TFS PERIODICITY signal.

The precise next from commit 1a2f9460. The prior run (scripts/stage2_segmentation_gate.py,
docs/stage2_segmentation_gate.md) ran the ACTUAL Stage-2 gate ("the sonority-valley
segmenter's depth-threshold self-tunes to a stable lexicon grain") on the native
TOTAL-ENERGY envelope and found NO self-tuning: a smooth monotone exponential
decay (no shelf), cross-speaker grain sd 0.44 of grain, not coherent.

The diagnosed fix is the SIGNAL, not the threshold (ozma_fix_the_fixer): feed the
segmenter the graded TFS PERIODICITY / voicing track (native band_autocorr ->
summary_autocorrelogram -> periodicity_track — the SAME d'=6.0 voiced<->unvoiced
axis from PART 1, validated commit 90b799c9) instead of total energy. Periodicity
valleys mark voiced<->unvoiced (sonority) boundaries that should be far more
speaker-stable than energy minima.

THIS SCRIPT REUSES the corrected interior-shelf plateau detector + grain-relative
coherence VERBATIM from scripts/stage2_segmentation_gate.py (the detector the agent
fixed after it caught its own instrument printing two false-positive Trues). The
ONLY change is `total_env` <- the TFS periodicity track instead of the native
total-energy envelope. READ THE NUMBERS, not the boolean.

WHAT THIS MEASURES (identical structural gate as the prior run):
  * Runs ONLY the native segmenter `substrate_rs._native.detect_sonority_valleys`
    on the FSDD digit words, SWEEPING depth_threshold across its range, now reading
    the graded TFS PERIODICITY track as its input signal.
  * grain = number of sonority valleys -> spans (manner/syllable units) per token.
  * self-tuning = an INTERIOR relative-flat shelf at a non-trivial grain.
  * coherence  = within the plateau, same-word -> same-grain across speakers.
  * NO recognition score. NO .fit. NO net. NO gradient. The sweep FINDS the plateau,
    it is NOT an accuracy fit. CortexLoop / solve_for_n UNTOUCHED. No Rust touched
    (segmenter + TFS chain already bound).

DONKEY AUDIT:
  * The only agent operations are the native TFS periodicity chain
    (gammatone_band -> band_autocorr -> summary_autocorrelogram ->
    periodicity_track, the agent's owned T4 voicing channel, VERBATIM from
    scripts/stage2_sonority_check.py:tfs_voicing_track) and the native segmenter
    (detect_sonority_valleys). No Python DSP decision; the periodicity frame rate
    (FS/TFS_HOP) is passed as the segmenter's `fs` so its ms->sample windows are
    correct on the periodicity grid.
  * The verdict is grain STABILITY (interior shelf) + CROSS-SPEAKER coherence
    (grain-relative) + MANNER/SYLLABLE match — all structural, no held-out accuracy.
"""

from __future__ import annotations

import os
import re
import wave

import numpy as np

import substrate_rs._native as _n


DATA_DIR = "/tmp/fsdd/recordings"
_DIGITS = ["zero", "one", "two", "three", "four", "five",
           "six", "seven", "eight", "nine"]
_FN_RE = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")

FS = 8000

# --- the TFS periodicity/voicing chain (T4, validated 90b799c9) ----------------
# VERBATIM from scripts/stage2_sonority_check.py:tfs_voicing_track — the SAME owned
# native chain that gives the d'=6.0 voiced<->unvoiced axis in PART 1. NOT a knob:
# these framing constants are fixed; the ONLY swept quantity is depth_threshold.
FRAME_MS = 32.0
HOP_MS = 12.0
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = int(FS * FRAME_MS / 1000)     # 256 samples (32 ms @ 8 kHz)
TFS_HOP = int(FS * HOP_MS / 1000)       # 96 samples (12 ms)
TFS_MINLAG, TFS_MAXLAG = 25, 100        # F0 80-320 Hz -> lag 25..100 @ 8 kHz
TFS_NLAGS = TFS_MAXLAG + 1

# The periodicity track is one value per HOP -> an effective frame rate. The
# segmenter's ms->sample windows (smoothing, min-separation) must be computed on
# THIS grid, so we pass it as the segmenter's `fs`.
PERIOD_FS = FS / TFS_HOP                 # ~83.3 Hz frame rate

# Segmenter time-scale windows (same syllable/manner scale as the prior run; in ms,
# converted to periodicity-frame samples by PERIOD_FS inside the native segmenter).
SEG_SMOOTH_MS = 25.0         # suppress intra-phoneme jitter
SEG_MIN_SEP_MS = 50.0        # syllable/manner-scale min gap between valleys

# The depth_threshold sweep — IDENTICAL to the prior run (the whole admissible
# range of the segmenter's one free parameter). We LOOK FOR a self-tuning plateau.
DEPTH_SWEEP = [round(0.02 * k, 3) for k in range(1, 41)]   # 0.02 .. 0.80


def load_wav(path):
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float64) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float64)


def gather_files():
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = _FN_RE.match(fn)
        if not m:
            continue
        digit, speaker, idx = m.groups()
        out.append((os.path.join(DATA_DIR, fn), int(digit), speaker, int(idx)))
    return out


def periodicity_envelope(x):
    """The graded TFS PERIODICITY/voicing track = the segmenter's NEW input signal.
    VERBATIM from scripts/stage2_sonority_check.py:tfs_voicing_track (the agent's
    owned native T4 chain, d'=6.0 in PART 1): native gammatone_band ->
    band_autocorr -> summary_autocorrelogram -> periodicity_track. Per-frame
    periodicity strength in [0,1]; voiced/sonorant -> ~1, frication/burst/silence
    -> low. No Python DSP. Returns one value per TFS_HOP (periodicity-frame grid)."""
    s = np.asarray(x, dtype=np.float32)
    if len(s) < TFS_WIN:
        return None
    s_list = s.tolist()
    band_acs = []
    for fc in TFS_FCS:
        band = _n.gammatone_band(s_list, FS, float(fc), 4)          # native band
        ac = _n.band_autocorr(band, TFS_WIN, TFS_HOP, TFS_MAXLAG)   # native TFS autocorr
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return None
    sacf = _n.summary_autocorrelogram(band_acs, TFS_NLAGS)          # native pooled SACF
    if not sacf:
        return None
    pt = _n.periodicity_track(sacf, TFS_NLAGS, TFS_MINLAG, TFS_MAXLAG)  # native readout
    if not pt:
        return None
    strengths = np.array(pt[0::2], dtype=np.float32)               # [s0,l0,s1,l1,...]
    if len(strengths) < 8:
        return None
    return strengths


def valley_count(env, depth):
    """The native segmenter's grain at a depth_threshold = number of sonority
    valleys. The ONLY segmenter op. fs = PERIOD_FS so ms->sample windows are right
    on the periodicity-frame grid."""
    if env is None:
        return 0
    flat = _n.detect_sonority_valleys(env.tolist(), int(round(PERIOD_FS)),
                                      SEG_SMOOTH_MS, SEG_MIN_SEP_MS, float(depth))
    return len(flat) // 4


# Expected natural lexicon grain (manner/syllable structure) — IDENTICAL to the
# prior run. Number of sonorant nuclei = syllable count.
SYLLABLES = {0: 2,  # ze-ro
             1: 1,  # one
             2: 1,  # two
             3: 1,  # three
             4: 2,  # four
             5: 1,  # five
             6: 1,  # six
             7: 2,  # se-ven
             8: 1,  # eight
             9: 1}  # nine


def main():
    print("=" * 74)
    print("STAGE 2 — SEGMENTATION-COHERENCE / SELF-TUNING GATE on TFS PERIODICITY")
    print("  precise next from commit 1a2f9460: feed the segmenter the graded TFS")
    print("  periodicity (voiced<->unvoiced, d'=6.0) instead of TOTAL ENERGY.")
    print("  NOT a recognition accuracy. Native TFS chain + native segmenter ONLY.")
    print("=" * 74)

    files = gather_files()
    if not files:
        print(f"!! no FSDD wavs under {DATA_DIR}")
        return
    print(f"tokens: {len(files)}  (real FSDD, isolated single-talker digits)")
    print(f"signal: TFS periodicity track (band_autocorr -> SACF -> periodicity_track)")
    print(f"        periodicity frame rate = FS/{TFS_HOP} = {PERIOD_FS:.2f} Hz "
          f"(passed as segmenter fs)")
    print(f"depth_threshold sweep: {DEPTH_SWEEP[0]} .. {DEPTH_SWEEP[-1]} "
          f"({len(DEPTH_SWEEP)} steps)")
    print(f"segmenter: native detect_sonority_valleys (py.rs:6079)\n")

    speakers = sorted({sp for _, _, sp, _ in files})
    print(f"speakers: {speakers}\n")

    grains = {d: {dig: [] for dig in range(10)} for d in DEPTH_SWEEP}
    sp_grain = {d: {dig: {sp: [] for sp in speakers} for dig in range(10)}
                for d in DEPTH_SWEEP}

    n_ok = 0
    for path, digit, sp, _ in files:
        env = periodicity_envelope(load_wav(path))
        if env is None:
            continue
        n_ok += 1
        for d in DEPTH_SWEEP:
            c = valley_count(env, d)
            grains[d][digit].append(c)
            sp_grain[d][digit][sp].append(c)
    print(f"tokens with a usable periodicity track: {n_ok}/{len(files)}\n")

    # --- (A) the GRAIN curve: mean valleys/token vs depth_threshold ------------
    print("--- (A) GRAIN vs depth_threshold (mean valleys/token, all digits) ---")
    mean_grain = {}
    for d in DEPTH_SWEEP:
        allc = [c for dig in range(10) for c in grains[d][dig]]
        mean_grain[d] = float(np.mean(allc)) if allc else 0.0
    for d in DEPTH_SWEEP:
        bar = "#" * int(round(mean_grain[d] * 12))
        print(f"  depth {d:<5}  grain {mean_grain[d]:5.3f}  {bar}")

    # --- (B) SELF-TUNING PLATEAU (corrected interior-shelf detector, VERBATIM) --
    print("\n--- (B) SELF-TUNING PLATEAU (relative-flat shelf at a non-trivial grain) ---")
    ds = DEPTH_SWEEP
    deriv = []
    for i in range(1, len(ds)):
        dg = mean_grain[ds[i]] - mean_grain[ds[i - 1]]
        deriv.append((ds[i], dg))
    rel_slopes = [abs(dg) / max(mean_grain[ds[i + 1]], 1e-6)
                  for i, (_, dg) in enumerate(deriv)]
    median_slope = float(np.median(rel_slopes))
    print(f"  per-step |Δgrain|/grain over the whole sweep: "
          f"min {min(rel_slopes):.3f}  median {median_slope:.3f}  "
          f"max {max(rel_slopes):.3f}")
    print(f"  (a SHELF needs this near 0 over a band, AND bracketed by STEEPER "
          f"descent on both sides — an INTERIOR local-derivative minimum, not the\n"
          f"   flat TOP or the collapsed TAIL of a monotone decay. A pure exp decay "
          f"keeps the relative slope ~constant — NO shelf.)")
    REL_TOL = min(0.04, 0.5 * median_slope)   # flatter than half the median slope
    GRAIN_FLOOR = 1.0
    EDGE_GUARD = 3                            # ignore the first/last 3 sweep steps
    stable_flags = []
    for i, (_, dg) in enumerate(deriv):
        gi = mean_grain[ds[i + 1]]
        rel = abs(dg) / max(gi, 1e-6)
        interior = EDGE_GUARD <= (i + 1) <= (len(ds) - 1 - EDGE_GUARD)
        stable_flags.append(rel < REL_TOL and GRAIN_FLOOR <= gi <= 4.0 and interior)
    best_run = (0, -1, -1)
    i = 0
    while i < len(stable_flags):
        if stable_flags[i]:
            j = i
            while j < len(stable_flags) and stable_flags[j]:
                j += 1
            length = j - i + 1
            if length > best_run[0]:
                best_run = (length, i + 1, j + 1)
            i = j + 1
        else:
            i += 1

    plateau_lo = plateau_hi = None
    if best_run[0] > 0:
        plateau_lo = ds[best_run[1]]
        plateau_hi = ds[best_run[2]]
        width = plateau_hi - plateau_lo
        pg = np.mean([mean_grain[d] for d in ds
                      if plateau_lo <= d <= plateau_hi])
        print(f"  longest stable run: depth [{plateau_lo:.3f} .. {plateau_hi:.3f}]"
              f"  width {width:.3f}  ({best_run[0]} steps)")
        print(f"  plateau mean grain : {pg:.3f} valleys/token (stable)")
        print(f"  |Δgrain|/grain in plateau: < {REL_TOL} per 0.02 step (relative-flat)")
    else:
        print("  NO stable, non-trivial plateau found (grain never flattens at a "
              "sane grain) — the segmenter does not self-tune.")

    # --- (C) CROSS-SPEAKER COHERENCE -------------------------------------------
    print("\n--- (C) CROSS-SPEAKER GRAIN COHERENCE (at the operating point) ---")
    if plateau_lo is not None:
        d_star = round((plateau_lo + plateau_hi) / 2.0, 3)
        d_star = min(ds, key=lambda d: abs(d - d_star))
        print(f"  operating point d* = {d_star} (plateau centre)\n")
    else:
        d_star = min(ds, key=lambda d: abs(mean_grain[d] - 1.0))
        print(f"  NO plateau — diagnostic operating point d* = {d_star} "
              f"(grain closest to 1 valley; NOT a self-tuned point)\n")
    print(f"  {'digit':<7} {'mean':>5} {'sd':>5} {'cross-spkr sd':>14}  "
          f"per-speaker mean grain")
    word_grain = {}
    cross_sds = []
    within_token_sds = []
    for dig in range(10):
        per_sp_means = []
        for sp in speakers:
            cs = sp_grain[d_star][dig][sp]
            if cs:
                per_sp_means.append(float(np.mean(cs)))
        allc = grains[d_star][dig]
        mean_c = float(np.mean(allc)) if allc else 0.0
        sd_c = float(np.std(allc)) if allc else 0.0
        cross_sd = float(np.std(per_sp_means)) if per_sp_means else 0.0
        word_grain[dig] = mean_c
        cross_sds.append(cross_sd)
        within_token_sds.append(sd_c)
        psm = " ".join(f"{m:.1f}" for m in per_sp_means)
        print(f"  {_DIGITS[dig]:<7} {mean_c:>5.2f} {sd_c:>5.2f} "
              f"{cross_sd:>14.3f}  [{psm}]")
    mean_cross_sd = float(np.mean(cross_sds))
    mean_tok_sd = float(np.mean(within_token_sds))
    op_mean_grain = float(np.mean([word_grain[dig] for dig in range(10)]))
    rel_cross = mean_cross_sd / max(op_mean_grain, 1e-6)
    rel_tok = mean_tok_sd / max(op_mean_grain, 1e-6)
    print(f"\n  operating-point mean grain  : {op_mean_grain:.3f} valleys/token")
    print(f"  mean cross-speaker grain sd : {mean_cross_sd:.3f} "
          f"= {rel_cross:.2f} of the grain (0 = identical across speakers)")
    print(f"  mean within-token grain sd  : {mean_tok_sd:.3f} "
          f"= {rel_tok:.2f} of the grain")
    print(f"  (prior ENERGY run: cross-speaker sd = 0.44 of grain, "
          f"within-token = 0.97 of grain)")

    # --- (D) MANNER/SYLLABLE MATCH ---------------------------------------------
    print("\n--- (D) MATCH TO EXPECTED MANNER/SYLLABLE STRUCTURE ---")
    rank_corr = float("nan")
    bisyl_mean = monosyl_mean = float("nan")
    if word_grain:
        syl = np.array([SYLLABLES[dig] for dig in range(10)], dtype=float)
        gr = np.array([word_grain[dig] for dig in range(10)], dtype=float)

        def _rank(a):
            order = np.argsort(a, kind="stable")
            r = np.empty_like(order, dtype=float)
            r[order] = np.arange(len(a))
            return r
        rs, rg = _rank(syl), _rank(gr)
        if np.std(rs) > 0 and np.std(rg) > 0:
            rank_corr = float(np.corrcoef(rs, rg)[0, 1])
        bisyl = [word_grain[dig] for dig in range(10) if SYLLABLES[dig] == 2]
        mono = [word_grain[dig] for dig in range(10) if SYLLABLES[dig] == 1]
        bisyl_mean = float(np.mean(bisyl)) if bisyl else float("nan")
        monosyl_mean = float(np.mean(mono)) if mono else float("nan")
        print(f"  syllable count vs grain (per digit):")
        for dig in range(10):
            print(f"    {_DIGITS[dig]:<7} syllables {SYLLABLES[dig]}  "
                  f"grain {word_grain[dig]:.2f}")
        print(f"\n  bi-syllabic words mean grain : {bisyl_mean:.3f} "
              f"(zero, four, seven)")
        print(f"  mono-syllabic words mean grain: {monosyl_mean:.3f}")
        print(f"  grain-vs-syllable rank corr   : {rank_corr:+.3f} "
              f"(>0 = grain tracks syllable structure)")

    # --- VERDICT ----------------------------------------------------------------
    print("\n" + "=" * 74)
    print("=== READINESS GATE — SEGMENTATION SELF-TUNING on PERIODICITY (structural) ===")
    has_plateau = plateau_lo is not None and best_run[0] >= 3
    coherent_speakers = ((not np.isnan(rel_cross)) and rel_cross < 0.25
                         and rel_tok < 0.5)
    matches_lexicon = ((not np.isnan(rank_corr)) and rank_corr > 0.0
                       and (bisyl_mean > monosyl_mean))
    nontrivial = (plateau_lo is not None
                  and 1.0 <= np.mean([mean_grain[d] for d in ds
                                      if plateau_lo <= d <= plateau_hi]) <= 4.0)

    print(f"  SELF-TUNES (a stable grain PLATEAU exists)         : {has_plateau}"
          + (f"  [{plateau_lo:.2f}..{plateau_hi:.2f}]" if plateau_lo else ""))
    print(f"  PLATEAU grain is non-trivial (word actually carves): {nontrivial}")
    print(f"  CROSS-SPEAKER coherent (same word -> same grain)   : "
          f"{coherent_speakers}"
          + (f"  [cross-spkr sd {mean_cross_sd:.2f} = {rel_cross:.2f} of grain; "
             f"within-token {rel_tok:.2f} of grain]"
             if not np.isnan(rel_cross) else ""))
    print(f"  MATCHES lexicon manner/syllable structure          : "
          f"{matches_lexicon}"
          + (f"  [rank corr {rank_corr:+.2f}, bi {bisyl_mean:.2f} > "
             f"mono {monosyl_mean:.2f}]" if not np.isnan(rank_corr) else ""))
    fires = has_plateau and nontrivial and coherent_speakers and matches_lexicon
    print("  " + "-" * 60)
    print(f"  >>> STAGE-2 SEGMENTER SELF-TUNES TO A STABLE LEXICON GRAIN "
          f"(periodicity): {fires}")
    print("=" * 74)
    print("===MARKER_STAGE2_PERIODICITY_GATE_COMPLETE===")


if __name__ == "__main__":
    main()
