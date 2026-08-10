"""STAGE 2 — the DECISIVE clean-16k A/B of the voicing-EDGES segmentation gate.

The 4th-attempt voicing-edges gate (scripts/stage2_edges_gate.py, commit b699d215)
returned an HONEST NO on 8 kHz FSDD — no self-tuning shelf, cross-speaker grain
sd 0.34 of grain. But 8 kHz had ALREADY DELETED the frication band (4-8 kHz) —
half the sonority evidence (/s/ /f/ unvoiced obstruents) thrown away before the
agent saw it (memory ozma_train_on_clean_test_on_degraded). THIS run re-runs the
EXACT SAME gate on CLEAN 16 kHz audio (intact frication) — the decisive A/B:

  * clean PASSES  -> 8 kHz was the corpus artifact, base solid, frication band
                     was starving the segmenter.
  * clean ALSO FAILS -> a REAL isolated-digit limit; the lever is continuous
                     speech (TP-troughs across word boundaries).

REUSED VERBATIM from scripts/stage2_edges_gate.py (commit b699d215):
  * periodicity_envelope (the native T4 TFS chain: gammatone_band -> band_autocorr
    -> summary_autocorrelogram -> periodicity_track), the d'=6.0 voicing axis;
  * edge_count (the hysteresis voicing onset/offset landmark state machine);
  * the corrected INTERIOR-SHELF plateau detector + grain-relative coherence +
    syllable/manner match + verdict logic.

THE ONLY CHANGES vs the 8 kHz run (audited, file:line below):
  (i)  the CORPUS = clean 16 kHz Speech Commands digits (scripts/clean16k_corpus),
       NOT downsampled — the whole point (intact 4-8 kHz frication band);
  (ii) the RATE-DEPENDENT framing constants are set for 16 kHz so the SAME
       physical analysis is performed: FRAME_MS/HOP_MS unchanged (same ms window),
       so the sample counts double; the F0 lag range (80-320 Hz) doubles in
       samples (lag = FS / f0). These are NOT knobs — they are the SAME physical
       quantities expressed at the new sample rate. The ONLY swept quantity is
       still the hysteresis band `h`.

DONKEY (audited): native TFS chain + a deterministic hysteresis landmark
transducer ONLY. NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit (the
sweep FINDS a plateau, it is not an accuracy fit). CortexLoop / solve_for_n
UNTOUCHED. No Rust touched (the TFS chain is already bound; the edge rule is a
thin mechanical landmark transducer over the native track). Readiness = the
STRUCTURAL plateau/coherence/manner signal, NOT a held-out accuracy.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_edges_gate_clean16k`
"""
from __future__ import annotations

import numpy as np

import substrate_rs._native as _n
from scripts.clean16k_corpus import DIGITS as _DIGITS, FS, load_wav, select_corpus

# --- the TFS periodicity/voicing chain, set for 16 kHz ------------------------
# SAME physical framing as the 8 kHz run (FRAME_MS/HOP_MS identical); the sample
# counts follow from FS. F0 80-320 Hz -> lag = FS/f0 -> 50..200 samples @ 16 kHz
# (was 25..100 @ 8 kHz). The TFS channel centre freqs are physical Hz (unchanged).
FRAME_MS = 32.0
HOP_MS = 12.0
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = int(FS * FRAME_MS / 1000)     # 512 samples (32 ms @ 16 kHz)
TFS_HOP = int(FS * HOP_MS / 1000)       # 192 samples (12 ms)
TFS_MINLAG, TFS_MAXLAG = 50, 200        # F0 80-320 Hz -> lag 50..200 @ 16 kHz
TFS_NLAGS = TFS_MAXLAG + 1

PERIOD_FS = FS / TFS_HOP                 # ~83.3 Hz frame rate (same as 8 kHz run)

# The hysteresis-band sweep — VERBATIM from the 8 kHz run (the edge rule's ONE
# free parameter; the periodicity track is in [0,1] independent of rate).
HYST_SWEEP = [round(0.02 * k, 3) for k in range(1, 41)]   # 0.02 .. 0.80


def periodicity_envelope(x):
    """The graded TFS PERIODICITY/voicing track. VERBATIM from
    scripts/stage2_edges_gate.py:periodicity_envelope (native T4 chain). Per-frame
    periodicity strength in [0,1]; voiced/sonorant ~1, frication/burst/silence low."""
    s = np.asarray(x, dtype=np.float32)
    if len(s) < TFS_WIN:
        return None
    s_list = s.tolist()
    band_acs = []
    for fc in TFS_FCS:
        band = _n.gammatone_band(s_list, FS, float(fc), 4)
        ac = _n.band_autocorr(band, TFS_WIN, TFS_HOP, TFS_MAXLAG)
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return None
    sacf = _n.summary_autocorrelogram(band_acs, TFS_NLAGS)
    if not sacf:
        return None
    pt = _n.periodicity_track(sacf, TFS_NLAGS, TFS_MINLAG, TFS_MAXLAG)
    if not pt:
        return None
    strengths = np.array(pt[0::2], dtype=np.float32)
    if len(strengths) < 8:
        return None
    return strengths


def edge_count(env, hyst):
    """The voicing-EDGE grain at a hysteresis band width `hyst`. VERBATIM from
    scripts/stage2_edges_gate.py:edge_count — the hysteresis state machine over the
    per-token median voicing level (self-referencing -> speaker-robust)."""
    if env is None or len(env) < 3:
        return 0
    p = np.asarray(env, dtype=np.float64)
    level = float(np.median(p))
    thr_hi = level + hyst / 2.0
    thr_lo = level - hyst / 2.0
    voiced = p[0] >= level
    edges = 0
    for v in p[1:]:
        if not voiced:
            if v >= thr_hi:
                voiced = True
                edges += 1
        else:
            if v <= thr_lo:
                voiced = False
                edges += 1
    return edges


# Expected natural lexicon grain — IDENTICAL to the 8 kHz run.
SYLLABLES = {0: 2, 1: 1, 2: 1, 3: 1, 4: 2, 5: 1, 6: 1, 7: 2, 8: 1, 9: 1}


def main():
    print("=" * 74)
    print("STAGE 2 — SEGMENTATION SELF-TUNING GATE on VOICING EDGES — CLEAN 16 kHz A/B")
    print("  the decisive re-grounding: re-run the EXACT 8 kHz voicing-edges gate")
    print("  (commit b699d215) on CLEAN 16 kHz Speech-Commands digits (intact 4-8 kHz")
    print("  frication band, NOT downsampled). Native TFS chain + edge rule ONLY.")
    print("  NOT a recognition accuracy.")
    print("=" * 74)

    files, speakers = select_corpus()
    if not files:
        print("!! no clean-16k Speech Commands wavs found under /tmp/sc")
        return
    print(f"tokens: {len(files)}  (clean isolated single-talker digits, 16 kHz native)")
    print(f"corpus: Google Speech Commands digits zero..nine, {len(speakers)} speakers")
    print(f"signal: TFS periodicity track (band_autocorr -> SACF -> periodicity_track)")
    print(f"        FS={FS}  TFS_WIN={TFS_WIN}  TFS_HOP={TFS_HOP}  lag {TFS_MINLAG}..{TFS_MAXLAG}")
    print(f"        periodicity frame rate = FS/{TFS_HOP} = {PERIOD_FS:.2f} Hz")
    print(f"edge rule: hysteresis crossings about the per-token median voicing level")
    print(f"hysteresis-band sweep: {HYST_SWEEP[0]} .. {HYST_SWEEP[-1]} "
          f"({len(HYST_SWEEP)} steps)\n")
    print(f"speakers ({len(speakers)}): {speakers}\n")

    grains = {h: {dig: [] for dig in range(10)} for h in HYST_SWEEP}
    sp_grain = {h: {dig: {sp: [] for sp in speakers} for dig in range(10)}
                for h in HYST_SWEEP}

    n_ok = 0
    for path, digit, sp, _ in files:
        x, _fs = load_wav(path)
        env = periodicity_envelope(x)
        if env is None:
            continue
        n_ok += 1
        for h in HYST_SWEEP:
            c = edge_count(env, h)
            grains[h][digit].append(c)
            sp_grain[h][digit][sp].append(c)
    print(f"tokens with a usable periodicity track: {n_ok}/{len(files)}\n")

    # --- (A) the GRAIN curve ---------------------------------------------------
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
          f"   flat TOP or the collapsed TAIL of a monotone decay.)")
    REL_TOL = min(0.04, 0.5 * median_slope)
    GRAIN_FLOOR = 1.0
    EDGE_GUARD = 3
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
    print(f"  {'digit':<7} {'mean':>5} {'sd':>5} {'cross-spkr sd':>14}")
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
        print(f"  {_DIGITS[dig]:<7} {mean_c:>5.2f} {sd_c:>5.2f} {cross_sd:>14.3f}")
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
    print(f"  (8 kHz voicing-EDGES run: cross-speaker sd = 0.34 of grain — "
          f"CLEAN 16 kHz must be LOWER/tighter to be a corpus artifact)")

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
        print(f"\n  named manner targets (read the NUMBERS):")
        print(f"    seven (unv-v-unv, expect ~2-3 edges): {word_grain[7]:.2f}")
        print(f"    two   (unv-v,     expect ~1 edge)   : {word_grain[2]:.2f}")
        print(f"    six   (unv-v-unv, expect ~2-3 edges): {word_grain[6]:.2f}")

    # --- VERDICT ----------------------------------------------------------------
    print("\n" + "=" * 74)
    print("=== READINESS GATE — SEGMENTATION SELF-TUNING on VOICING EDGES (CLEAN 16 kHz) ===")
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
          f"(clean 16k voicing edges): {fires}")
    print("=" * 74)
    print("===MARKER_STAGE2_EDGES_GATE_CLEAN16K_COMPLETE===")


if __name__ == "__main__":
    main()
