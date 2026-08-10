"""STAGE 2 — the ACTUAL readiness gate: SEGMENTATION COHERENCE / SELF-TUNING.

The agent's own Stage-2 success signal (docs/toolbox_and_curriculum.md:345-347,
docs/stage2_sonority.md:33): *"the sonority-valley segmenter's depth-threshold
self-tunes to a stable lexicon grain."*

The two prior attempts (commit eb335974, docs/stage2_sonority.md) measured the
WRONG gate — sonority as a WORD-DISCRIMINATION fusion prong (the "sharpening"
PART 2). The deeper diagnosis: the sonority's role is SEGMENTATION, not a
word-vote. The gate is whether the SEGMENTER self-tunes to a stable, coherent
lexicon grain — a STRUCTURAL / (G,Γ)-binary coherence signal, NOT a held-out
LOSO recognition accuracy.

WHAT THIS MEASURES (and what it does NOT):
  * It runs ONLY the native segmenter `substrate_rs._native.detect_sonority_valleys`
    (audio_primitives.rs:1217, bound at py.rs:6079) on the FSDD digit words,
    SWEEPING the depth_threshold across its range.
  * The grain = number of sonority-valley boundaries -> spans (manner/syllable
    units) per token.
  * Self-tuning  = is there a depth_threshold PLATEAU where the grain is STABLE
    (insensitive to threshold: dGrain/dThreshold ~ 0)?
  * Coherence    = within that plateau, is the grain COHERENT — consistent for a
    word ACROSS speakers, and matching the lexicon's natural manner/syllable
    structure?
  * NO recognition score. NO .fit. NO net. NO gradient. The threshold sweep is to
    FIND the self-tuning plateau, NOT to fit an accuracy. CortexLoop / solve_for_n
    UNTOUCHED. No Rust touched (segmenter already bound).

DONKEY AUDIT:
  * The ONLY agent operation is the native segmenter (Rust). The envelope it reads
    is the SAME owned native cochlear pathway as the skeleton check
    (gammatone_band -> hair_cell_envelope -> sum -> decimate to a 1 kHz grid;
    stage2_skeleton_check.py:176). Mechanical world-adapter, no Python DSP decision.
  * The verdict is the grain's STABILITY (plateau) + CROSS-SPEAKER COHERENCE +
    MANNER/SYLLABLE MATCH — all structural, read off the segmenter alone. No
    held-out accuracy is computed or banked.
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

# --- the broadband total envelope the segmenter reads (full time resolution) --
# VERBATIM from stage2_skeleton_check.py:95-105 — the SAME owned native cochlear
# pathway. A perception front-end choice (give the segmenter an envelope it can
# resolve), the same for every word. NOT a knob — these are fixed; the ONLY swept
# quantity is depth_threshold (the gate is whether the GRAIN self-tunes over it).
SEG_FCS = (200.0, 350.0, 550.0, 800.0, 1200.0, 1800.0, 2600.0, 3600.0)
SEG_ENV_CUTOFF_HZ = 200.0    # hair-cell LPF — syllable/manner-rate envelope
SEG_DECIM = 8                # 8 kHz -> 1 kHz envelope grid
SEG_ENV_FS = FS // SEG_DECIM
SEG_SMOOTH_MS = 25.0         # suppress intra-phoneme jitter (word-rate digits)
SEG_MIN_SEP_MS = 50.0        # syllable/manner-scale min gap between valleys

# The depth_threshold sweep — the WHOLE admissible range of the segmenter's one
# free parameter. We are LOOKING FOR a self-tuning plateau in here, not fitting.
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


def total_envelope(x):
    """The broadband sonority envelope at full time resolution = sum of native
    hair-cell envelopes across a cochlear bank, decimated to a 1 kHz grid — the
    total-energy track the native sonority-valley segmenter reads its minima off.
    VERBATIM owned native pathway (stage2_skeleton_check.py:176). No Python DSP."""
    s = np.asarray(x, dtype=np.float32).tolist()
    acc = None
    for fc in SEG_FCS:
        band = _n.gammatone_band(s, FS, float(fc), 4)               # native band
        env = np.array(_n.hair_cell_envelope(band, SEG_ENV_CUTOFF_HZ, FS),
                       dtype=np.float32)                            # native IHC env
        if acc is None:
            acc = env
        else:
            m = min(len(acc), len(env))
            acc = acc[:m] + env[:m]
    if acc is None or len(acc) < 8:
        return None
    return acc[::SEG_DECIM]                                         # 1 kHz grid


def valley_count(env, depth):
    """The native segmenter's grain at a depth_threshold = number of sonority
    valleys (consonant-boundary landmarks). The ONLY agent op in this gate."""
    if env is None:
        return 0
    flat = _n.detect_sonority_valleys(env.tolist(), SEG_ENV_FS,
                                      SEG_SMOOTH_MS, SEG_MIN_SEP_MS, float(depth))
    return len(flat) // 4


# Expected natural lexicon grain (manner/syllable structure of the spoken digit).
# Number of sonorant nuclei = syllable count; valley boundaries between them ~
# (nuclei - 1) for the internal manner breaks, plus obstruent-flanked breaks.
# This is the LINGUISTIC ground-truth structure (not fitted, not from the data):
# the count of SYLLABLES (sonorant nuclei) the word carves into.
SYLLABLES = {0: 2,  # ze-ro
             1: 1,  # one
             2: 1,  # two
             3: 1,  # three
             4: 2,  # four (fo-ur, diphthong/r -> often 1-2)
             5: 1,  # five
             6: 1,  # six
             7: 2,  # se-ven
             8: 1,  # eight
             9: 1}  # nine
# Internal sonority VALLEYS expected ~ (syllables - 1) for poly-syllables, and
# for mono-syllables with a medial obstruent (six: /k-s/, eight: medial stop) a
# medial valley can appear. We test the segmenter's grain against the *ordinal*
# structure (bi-syllabic words carve coarser/deeper than mono), not an exact int.


def main():
    print("=" * 74)
    print("STAGE 2 — SEGMENTATION-COHERENCE / SELF-TUNING GATE (the ACTUAL gate)")
    print("  signal: 'the sonority-valley segmenter's depth-threshold self-tunes")
    print("           to a stable lexicon grain'  (curriculum :345-347)")
    print("  NOT a recognition accuracy. Native segmenter ONLY.")
    print("=" * 74)

    files = gather_files()
    if not files:
        print(f"!! no FSDD wavs under {DATA_DIR}")
        return
    print(f"tokens: {len(files)}  (real FSDD, isolated single-talker digits)")
    print(f"depth_threshold sweep: {DEPTH_SWEEP[0]} .. {DEPTH_SWEEP[-1]} "
          f"({len(DEPTH_SWEEP)} steps)")
    print(f"segmenter: native detect_sonority_valleys (py.rs:6079) on the owned "
          f"native cochlear total-envelope (1 kHz grid)\n")

    speakers = sorted({sp for _, _, sp, _ in files})
    print(f"speakers: {speakers}\n")

    # --- pass 1: build the grain curve (valley-count) per token over the sweep --
    # grains[depth][digit] = list of per-token valley counts (across speakers/idx)
    grains = {d: {dig: [] for dig in range(10)} for d in DEPTH_SWEEP}
    # per-(digit,speaker) mean grain, for cross-speaker coherence at each depth
    sp_grain = {d: {dig: {sp: [] for sp in speakers} for dig in range(10)}
                for d in DEPTH_SWEEP}

    for path, digit, sp, _ in files:
        env = total_envelope(load_wav(path))
        if env is None:
            continue
        for d in DEPTH_SWEEP:
            c = valley_count(env, d)
            grains[d][digit].append(c)
            sp_grain[d][digit][sp].append(c)

    # --- the GRAIN curve: mean valleys-per-token vs depth_threshold ------------
    print("--- (A) GRAIN vs depth_threshold (mean valleys/token, all digits) ---")
    mean_grain = {}
    for d in DEPTH_SWEEP:
        allc = [c for dig in range(10) for c in grains[d][dig]]
        mean_grain[d] = float(np.mean(allc)) if allc else 0.0
    # print a compact curve
    for d in DEPTH_SWEEP:
        bar = "#" * int(round(mean_grain[d] * 12))
        print(f"  depth {d:<5}  grain {mean_grain[d]:5.3f}  {bar}")

    # --- self-tuning PLATEAU: where is the grain STABLE *relative to its level*? -
    # CRITICAL: a true self-tuning plateau is a SHELF — the grain holds steady at a
    # NON-TRIVIAL value over a threshold band. The diagnostic must be RELATIVE
    # (|Δgrain|/grain ~ 0), NOT absolute: a pure exponential decay trivially passes
    # an absolute |Δgrain|<tol test once it nears its floor (the grain is ~0, so the
    # step is small) — that is the asymptotic TAIL, not a stable lexicon grain. The
    # relative-slope test rejects that tail (the decay keeps the same fractional
    # slope all the way down) and only fires on a genuine shelf.
    print("\n--- (B) SELF-TUNING PLATEAU (relative-flat shelf at a non-trivial grain) ---")
    ds = DEPTH_SWEEP
    deriv = []
    for i in range(1, len(ds)):
        dg = mean_grain[ds[i]] - mean_grain[ds[i - 1]]
        deriv.append((ds[i], dg))
    # RELATIVE stability: fractional grain change per 0.02 step < 4% AND the grain
    # is a genuine lexicon grain (>= ~1 valley: the word actually carves). A pure
    # exp decay has a ~constant fractional slope (~7-14% here) and never qualifies.
    # per-step relative slope over the whole sweep (the exp-decay signature).
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
    # A genuine self-tuning shelf = a relative-flat run that is (1) at a non-trivial
    # grain, (2) markedly flatter than the curve's own median slope, AND (3) an
    # INTERIOR feature — bracketed by steeper descent BEFORE and AFTER, so it is a
    # true shelf, not the saturated top (first ~3 steps) or the collapsed tail.
    REL_TOL = min(0.04, 0.5 * median_slope)   # flatter than half the median slope
    GRAIN_FLOOR = 1.0
    EDGE_GUARD = 3                            # ignore the first/last 3 sweep steps
    stable_flags = []
    for i, (_, dg) in enumerate(deriv):
        gi = mean_grain[ds[i + 1]]
        rel = abs(dg) / max(gi, 1e-6)
        interior = EDGE_GUARD <= (i + 1) <= (len(ds) - 1 - EDGE_GUARD)
        stable_flags.append(rel < REL_TOL and GRAIN_FLOOR <= gi <= 4.0 and interior)
    best_run = (0, -1, -1)   # (length, start_idx, end_idx) into ds
    i = 0
    while i < len(stable_flags):
        if stable_flags[i]:
            j = i
            while j < len(stable_flags) and stable_flags[j]:
                j += 1
            length = j - i + 1
            if length > best_run[0]:
                best_run = (length, i + 1, j + 1)   # +1: deriv idx -> ds idx
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

    # --- (C) CROSS-SPEAKER COHERENCE: within a word, is the grain the SAME ------
    # across speakers? Measure at the plateau centre (the self-tuned operating
    # point). Coherence = low cross-speaker dispersion of the per-word grain.
    print("\n--- (C) CROSS-SPEAKER GRAIN COHERENCE (at the operating point) ---")
    # If a true plateau exists, operate at its centre. If not, still report the
    # cross-speaker / lexicon picture at the depth whose grain is closest to ~1
    # valley (the most lexicon-like operating point the segmenter can offer) — so
    # the structural diagnosis is honest even on a NOT-FIRE verdict.
    if plateau_lo is not None:
        d_star = round((plateau_lo + plateau_hi) / 2.0, 3)
        d_star = min(ds, key=lambda d: abs(d - d_star))   # snap to swept depth
        print(f"  operating point d* = {d_star} (plateau centre)\n")
    else:
        d_star = min(ds, key=lambda d: abs(mean_grain[d] - 1.0))
        print(f"  NO plateau — diagnostic operating point d* = {d_star} "
              f"(grain closest to 1 valley; NOT a self-tuned point)\n")
    if True:
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
        # coherence RELATIVE to the grain level: cross-speaker dispersion as a
        # fraction of the grain. A coherent same-word->same-grain segmenter needs
        # this small (<< 1); ~0.4 means the per-speaker grain swings ~40% of its
        # own value — not coherent.
        rel_cross = mean_cross_sd / max(op_mean_grain, 1e-6)
        rel_tok = mean_tok_sd / max(op_mean_grain, 1e-6)
        print(f"\n  operating-point mean grain  : {op_mean_grain:.3f} valleys/token")
        print(f"  mean cross-speaker grain sd : {mean_cross_sd:.3f} "
              f"= {rel_cross:.2f} of the grain (0 = identical across speakers)")
        print(f"  mean within-token grain sd  : {mean_tok_sd:.3f} "
              f"= {rel_tok:.2f} of the grain")
    else:
        d_star = None
        word_grain = {}
        mean_cross_sd = mean_tok_sd = float("nan")
        op_mean_grain = rel_cross = rel_tok = float("nan")

    # --- (D) MANNER/SYLLABLE MATCH: does the grain track the lexicon structure --
    # Coherence-to-lexicon: do bi-syllabic words (zero, seven, four) carve into a
    # COARSER grain (more nuclei -> a medial sonority valley) than mono-syllables?
    # We test the ORDINAL structure (rank correlation of grain to syllable count),
    # not an exact integer fit.
    print("\n--- (D) MATCH TO EXPECTED MANNER/SYLLABLE STRUCTURE ---")
    rank_corr = float("nan")
    bisyl_mean = monosyl_mean = float("nan")
    if d_star is not None and word_grain:
        syl = np.array([SYLLABLES[dig] for dig in range(10)], dtype=float)
        gr = np.array([word_grain[dig] for dig in range(10)], dtype=float)
        # spearman-ish: pearson on ranks
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

    # --- VERDICT --------------------------------------------------------------
    print("\n" + "=" * 74)
    print("=== READINESS GATE — SEGMENTATION SELF-TUNING (structural) ===")
    has_plateau = plateau_lo is not None and best_run[0] >= 3   # >=3 steps wide
    # coherence: cross-speaker grain dispersion small RELATIVE to the grain
    # (< 0.25 of it) AND tokens of a word agree (within-token sd < 0.5 of grain).
    # An absolute "< 1 valley" bar is too lax for a ~2-valley grain whose own
    # spread is ~1.7 — that is INCOHERENT, not coherent.
    coherent_speakers = ((not np.isnan(rel_cross)) and rel_cross < 0.25
                         and rel_tok < 0.5)
    # manner/syllable match: grain tracks syllable structure (positive rank corr)
    # AND bi-syllabic words carve coarser than mono-syllabic.
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
    print(f"  >>> STAGE-2 SEGMENTER SELF-TUNES TO A STABLE LEXICON GRAIN : "
          f"{fires}")
    print("=" * 74)
    print("===MARKER_STAGE2_SEGMENTATION_GATE_COMPLETE===")


if __name__ == "__main__":
    main()
