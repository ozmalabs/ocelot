"""STAGE 2 — segmentation-coherence gate, RE-RUN on VOICING EDGES (landmarks).

The precise next from commit f98e7206. The two prior runs of THIS gate
(scripts/stage2_segmentation_gate.py on total-energy, scripts/stage2_periodicity_gate.py
on the TFS periodicity track) both ran the ACTUAL Stage-2 gate the curriculum names —

    "the sonority-valley segmenter's depth-threshold self-tunes to a stable
     lexicon grain." (docs/toolbox_and_curriculum.md:345-347)

— by COUNTING MINIMA (`detect_sonority_valleys`) on a per-frame envelope, and both
found NO self-tuning: a monotone exponential decay (no shelf), cross-speaker grain
sd 0.44 (energy) / 0.64 (periodicity) of grain, not coherent. The DEEPER diagnosis
(commit f98e7206 / docs/stage2_periodicity_gate.md): the blocker is the OPERATION,
not the signal. VALLEY-COUNTING on any per-frame envelope of a short isolated digit
has no speaker-invariant shelf — the NUMBER and DEPTH of interior minima is itself
speaker-dependent (lucas carves 2-3x coarser). The periodicity track is a superb
voiced/unvoiced classifier (d'=6.0, PART 1) but a poor segmentation-by-valley-count
source.

THE FIX IS THE OPERATION: stop counting valleys; detect voicing ONSET/OFFSET
LANDMARKS (EDGES) — the rising/falling TRANSITIONS of the graded TFS periodicity
(voicing) track. An edge is a HYSTERESIS crossing of the d'=6.0 voiced<->unvoiced
axis: cross a HIGH threshold going up = a voicing ONSET landmark, cross a LOW
threshold going down = a voicing OFFSET landmark; the hysteresis band (the gap
between the two thresholds) rejects chatter on shallow interior dips. A crossing of
a graded high-margin axis is a zero-derivative-SIGN event whose LOCATION is stable
even when the NUMBER of shallow interior minima is not. The GRAIN = the number of
voicing transitions per word (the sonority skeleton: six unv-v-unv ~2-3 edges,
two unv-v ~1 edge).

THIS SCRIPT REUSES the corrected interior-shelf plateau detector + grain-relative
coherence + syllable-match + verdict logic VERBATIM from
scripts/stage2_periodicity_gate.py (the detector the agent fixed after it caught its
own instrument printing two false-positive Trues). The ONLY changes from that run:
  (i)  the GRAIN op is the voicing-EDGE count, not the valley count
       (`edge_count` replaces `valley_count`), and
  (ii) the SWEPT parameter is the HYSTERESIS BAND WIDTH (the gap between the onset
       and offset thresholds about the per-token voicing operating level), not the
       valley `depth_threshold`.
READ THE NUMBERS, not the boolean.

THE EDGE RULE (the agent's chosen landmark rule, audited below as the only non-native
step — a deterministic mechanical hysteresis STATE MACHINE, NOT DSP, NOT a fit, NOT a
net, NOT a decision over graph state):
  * Input = the native TFS periodicity track p[t] in [0,1] (the d'=6.0 voicing axis,
    VERBATIM from scripts/stage2_sonority_check.py:tfs_voicing_track — native
    gammatone_band -> band_autocorr -> summary_autocorrelogram -> periodicity_track).
  * The voicing operating LEVEL is the per-token median of p (self-referencing — the
    landmark is relative to THIS token's own voicing range, the speaker-robust move,
    NOT an absolute global threshold). The hysteresis band of width `h` straddles it:
        thr_hi = level + h/2   (onset: must rise above this to enter voicing)
        thr_lo = level - h/2   (offset: must fall below this to leave voicing)
  * State machine: walk p[t]; when UNVOICED and p crosses thr_hi -> emit an ONSET
    landmark, go VOICED; when VOICED and p crosses thr_lo -> emit an OFFSET landmark,
    go UNVOICED. The grain = the total number of landmarks (onsets + offsets) = the
    voicing transitions per word. Wider `h` -> only the big sonorant<->obstruent
    swings cross -> fewer, more speaker-robust edges (the hysteresis rejects chatter).
  * This is the SAME hysteresis idea already native in audio_primitives.rs:378
    `schmitt_peaks` (a Schmitt trigger with a 0.7 release ratio), here applied to
    TRANSITIONS rather than peaks. No statistical fit; the only swept quantity is `h`.

WHAT THIS MEASURES (identical STRUCTURAL gate as the prior two runs):
  * grain = voicing EDGE count per token (the sonority skeleton).
  * self-tuning = an INTERIOR relative-flat shelf at a non-trivial grain as the
    hysteresis band `h` is swept across its range.
  * coherence  = within the plateau, same-word -> same edge-count across speakers
    (cross-speaker grain sd, grain-relative — compare to energy 0.44, periodicity
    0.64; edges should be LOWER/tighter if the landmark is speaker-robust).
  * manner/syllable match: seven~2-3 edges, two~1 edge.
  * NO recognition score. NO .fit. NO net. NO gradient. NO loss. The sweep FINDS the
    plateau, it is NOT an accuracy fit. CortexLoop / solve_for_n UNTOUCHED. No Rust
    touched (TFS chain already bound; the edge rule is a thin mechanical landmark
    transducer over the native track, per "no Rust needed").

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_edges_gate`
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
# VERBATIM from scripts/stage2_periodicity_gate.py / stage2_sonority_check.py — the
# SAME owned native chain that gives the d'=6.0 voiced<->unvoiced axis in PART 1.
# NOT a knob: these framing constants are fixed; the ONLY swept quantity is the
# hysteresis band width `h`.
FRAME_MS = 32.0
HOP_MS = 12.0
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = int(FS * FRAME_MS / 1000)     # 256 samples (32 ms @ 8 kHz)
TFS_HOP = int(FS * HOP_MS / 1000)       # 96 samples (12 ms)
TFS_MINLAG, TFS_MAXLAG = 25, 100        # F0 80-320 Hz -> lag 25..100 @ 8 kHz
TFS_NLAGS = TFS_MAXLAG + 1

PERIOD_FS = FS / TFS_HOP                 # ~83.3 Hz frame rate (for reference)

# The hysteresis-band sweep — the edge rule's ONE free parameter, sweeping the whole
# admissible range (0 .. nearly the full [0,1] periodicity span). h=0 -> bare
# median crossing (max chatter); large h -> only the biggest sonorant<->obstruent
# swings cross (coarsest skeleton). We LOOK FOR a self-tuning plateau, exactly as
# the prior runs looked for one over the depth_threshold.
HYST_SWEEP = [round(0.02 * k, 3) for k in range(1, 41)]   # 0.02 .. 0.80


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
    """The graded TFS PERIODICITY/voicing track = the edge rule's input signal.
    VERBATIM from scripts/stage2_periodicity_gate.py:periodicity_envelope (the
    agent's owned native T4 chain, d'=6.0 in PART 1): native gammatone_band ->
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


# ---------------------------------------------------------------------------
# THE EDGE RULE — voicing ONSET/OFFSET LANDMARKS via a HYSTERESIS state machine.
# The ONLY non-native step (audited): a deterministic mechanical landmark
# transducer over the native d'=6.0 periodicity track. NOT DSP (no filter/FFT/fit),
# NOT a net, NOT a decision over graph state — a Schmitt-trigger crossing counter,
# the same hysteresis idea already native in audio_primitives.rs:378 schmitt_peaks,
# applied to TRANSITIONS (voicing edges) instead of peaks. The agent's chosen edge
# rule (slope-sign / hysteresis-band crossings). The grain = number of landmarks.
# ---------------------------------------------------------------------------

def edge_count(env, hyst):
    """The voicing-EDGE grain at a hysteresis band width `hyst` = number of voicing
    onset/offset landmarks. The operating LEVEL is the per-token median of the
    periodicity track (self-referencing -> speaker-robust); the band [level-h/2,
    level+h/2] straddles it. Walk the track: UNVOICED + cross thr_hi -> ONSET (->
    VOICED); VOICED + cross thr_lo -> OFFSET (-> UNVOICED). Returns the total count
    of landmarks (the sonority transitions per word)."""
    if env is None or len(env) < 3:
        return 0
    p = np.asarray(env, dtype=np.float64)
    level = float(np.median(p))
    thr_hi = level + hyst / 2.0
    thr_lo = level - hyst / 2.0
    # start in whichever state the first frame is unambiguously in; if it is inside
    # the band, seed from whether it is above/below the median (no landmark emitted
    # for the seed — only true crossings count).
    voiced = p[0] >= level
    edges = 0
    for v in p[1:]:
        if not voiced:
            if v >= thr_hi:          # voicing ONSET landmark
                voiced = True
                edges += 1
        else:
            if v <= thr_lo:          # voicing OFFSET landmark
                voiced = False
                edges += 1
    return edges


# Expected natural lexicon grain (manner/syllable structure) — IDENTICAL to the
# prior runs. For EDGES the natural unit is the number of voicing transitions
# (sonorant<->obstruent/silence boundaries), which tracks but is not identical to
# syllable count; we keep the syllable map for the SAME rank/ordinal test the prior
# runs used (bisyllabic words have more sonorant excursions -> more edges).
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
    print("STAGE 2 — SEGMENTATION-COHERENCE / SELF-TUNING GATE on VOICING EDGES")
    print("  precise next from commit f98e7206: the FIX IS THE OPERATION — detect")
    print("  voicing ONSET/OFFSET LANDMARKS (hysteresis crossings of the d'=6.0 TFS")
    print("  periodicity axis), NOT count minima. Native TFS chain + edge rule ONLY.")
    print("  NOT a recognition accuracy.")
    print("=" * 74)

    files = gather_files()
    if not files:
        print(f"!! no FSDD wavs under {DATA_DIR}")
        return
    print(f"tokens: {len(files)}  (real FSDD, isolated single-talker digits)")
    print(f"signal: TFS periodicity track (band_autocorr -> SACF -> periodicity_track)")
    print(f"        periodicity frame rate = FS/{TFS_HOP} = {PERIOD_FS:.2f} Hz")
    print(f"edge rule: hysteresis crossings about the per-token median voicing level")
    print(f"hysteresis-band sweep: {HYST_SWEEP[0]} .. {HYST_SWEEP[-1]} "
          f"({len(HYST_SWEEP)} steps)\n")

    speakers = sorted({sp for _, _, sp, _ in files})
    print(f"speakers: {speakers}\n")

    grains = {h: {dig: [] for dig in range(10)} for h in HYST_SWEEP}
    sp_grain = {h: {dig: {sp: [] for sp in speakers} for dig in range(10)}
                for h in HYST_SWEEP}

    n_ok = 0
    for path, digit, sp, _ in files:
        env = periodicity_envelope(load_wav(path))
        if env is None:
            continue
        n_ok += 1
        for h in HYST_SWEEP:
            c = edge_count(env, h)
            grains[h][digit].append(c)
            sp_grain[h][digit][sp].append(c)
    print(f"tokens with a usable periodicity track: {n_ok}/{len(files)}\n")

    # --- (A) the GRAIN curve: mean edges/token vs hysteresis band --------------
    print("--- (A) GRAIN vs hysteresis-band width (mean voicing edges/token, all digits) ---")
    mean_grain = {}
    for h in HYST_SWEEP:
        allc = [c for dig in range(10) for c in grains[h][dig]]
        mean_grain[h] = float(np.mean(allc)) if allc else 0.0
    for h in HYST_SWEEP:
        bar = "#" * int(round(mean_grain[h] * 6))
        print(f"  hyst {h:<5}  grain {mean_grain[h]:5.3f}  {bar}")

    # --- (B) SELF-TUNING PLATEAU (corrected interior-shelf detector, VERBATIM) --
    print("\n--- (B) SELF-TUNING PLATEAU (relative-flat shelf at a non-trivial grain) ---")
    ds = HYST_SWEEP
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
        print(f"  longest stable run: hyst [{plateau_lo:.3f} .. {plateau_hi:.3f}]"
              f"  width {width:.3f}  ({best_run[0]} steps)")
        print(f"  plateau mean grain : {pg:.3f} edges/token (stable)")
        print(f"  |Δgrain|/grain in plateau: < {REL_TOL} per 0.02 step (relative-flat)")
    else:
        print("  NO stable, non-trivial plateau found (grain never flattens at a "
              "sane grain) — the edge rule does not self-tune.")

    # --- (C) CROSS-SPEAKER COHERENCE -------------------------------------------
    print("\n--- (C) CROSS-SPEAKER GRAIN COHERENCE (at the operating point) ---")
    if plateau_lo is not None:
        d_star = round((plateau_lo + plateau_hi) / 2.0, 3)
        d_star = min(ds, key=lambda d: abs(d - d_star))
        print(f"  operating point h* = {d_star} (plateau centre)\n")
    else:
        d_star = min(ds, key=lambda d: abs(mean_grain[d] - 2.0))
        print(f"  NO plateau — diagnostic operating point h* = {d_star} "
              f"(grain closest to 2 edges; NOT a self-tuned point)\n")
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
    print(f"\n  operating-point mean grain  : {op_mean_grain:.3f} edges/token")
    print(f"  mean cross-speaker grain sd : {mean_cross_sd:.3f} "
          f"= {rel_cross:.2f} of the grain (0 = identical across speakers)")
    print(f"  mean within-token grain sd  : {mean_tok_sd:.3f} "
          f"= {rel_tok:.2f} of the grain")
    print(f"  (prior ENERGY valley run: cross-speaker sd = 0.44 of grain; "
          f"PERIODICITY valley run: 0.64 of grain — EDGES should be LOWER/tighter)")

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
                  f"edges {word_grain[dig]:.2f}")
        print(f"\n  bi-syllabic words mean grain : {bisyl_mean:.3f} "
              f"(zero, four, seven)")
        print(f"  mono-syllabic words mean grain: {monosyl_mean:.3f}")
        print(f"  grain-vs-syllable rank corr   : {rank_corr:+.3f} "
              f"(>0 = grain tracks syllable structure)")
        # specific manner targets named in the task (seven~2-3, two~1)
        print(f"\n  named manner targets (read the NUMBERS):")
        print(f"    seven (unv-v-unv, expect ~2-3 edges): {word_grain[7]:.2f}")
        print(f"    two   (unv-v,     expect ~1 edge)   : {word_grain[2]:.2f}")
        print(f"    six   (unv-v-unv, expect ~2-3 edges): {word_grain[6]:.2f}")

    # --- VERDICT ----------------------------------------------------------------
    print("\n" + "=" * 74)
    print("=== READINESS GATE — SEGMENTATION SELF-TUNING on VOICING EDGES (structural) ===")
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
          f"(voicing edges): {fires}")
    print("=" * 74)
    print("===MARKER_STAGE2_EDGES_GATE_COMPLETE===")


if __name__ == "__main__":
    main()
