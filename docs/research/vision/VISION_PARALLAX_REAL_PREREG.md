# DOES THE PARALLAX CARVE SURVIVE REAL PHOTOMETRY? — PRE-REGISTRATION

*Rung 124000. Committed BEFORE any confirmatory number. The pilot numbers quoted
below are on ALREADY-BURNED seeds (116000–116019, the parallax rung's own
confirmatory seeds) and are the power analysis (§3 clause 3) — nothing here was
computed on the confirmatory seeds 124000–124079.*

## 0. THE ONE VARIABLE

The eye's parallax carve is CONFIRMED on SYNTHETIC input (`VISION_PARALLAX_RESULTS.md`):
a known self-shift Δ + efference-copy subtraction + common-fate grouping carves a
depth scene into 3 few-and-large surfaces where a byte-identical static frame gives
1 blob. It is **mechanism-proven, not capability-proven**, and the first named
condition to break is **SYNTHETIC input**. There is no real video with real 3D
motion in the tree, so real MOTION is deferred (a data problem). **The one variable
this rung changes, and the load-bearing one, is PHOTOMETRY: real natural BSDS300
texture instead of synthetic Fourier texture, at the SAME controlled depth/shift
geometry.**

Everything is reproduced EXACTLY from the parallax rung — shifts `[0,3,6]`, block 8,
grid 144, ref_idx 1, the efference-copy subtraction `R = V − Δ_ref` (exact integers),
`group_common_fate` at τ∈{0, √5}, the participation-ratio + largest_frac
speck-robust statistics, the byte-identical-static-frame control — and ONLY the
source of `a` changes (`scripts/parallax_real_char.py`).

**The honest real analog of the toroidal roll (no fabrication).** The synthetic
texture wraps exactly, so `np.roll(a,s)` is a rigid translation with no border
fabrication: `b[:,x] = a[:,x−s]`. A real photo does not wrap; rolling it toroidally
would inject a FALSE wrap-seam that is not "photometry" but a new confound. The
faithful analog reproduces `b[:,x] = a[:,x−s]` EXACTLY without wrap, by sourcing the
displaced pixels from a crop wider than the grid (`off0 = max(shifts)`):
`a = src[:,off0:off0+grid]`, `b_depth[:,x∈band i] = src[:,x+off0−s_i]`,
`b_flat[:,x] = src[:,x+off0−s_ref]`. Every displaced pixel is a real scene neighbour
(genuine parallax reveals adjacent texture), never fabricated, never wrapped. `a` is
byte-identical DEPTH-vs-FLAT; ground truth / owner / edges / Δ_ref are identical to
the synthetic geometry. An exact toroidal roll ↦ an exact windowed slide; the only
difference is Fourier ↦ BSDS pixels.

## 1. HYPOTHESIS (two-sided)

Does the eye still carve a real-textured depth scene into ≈N=3 few-and-large surfaces
(DEPTH), with a real-textured FLAT control giving one blob, the same knee as
synthetic — or does real image statistics (low-contrast regions, real edges) inject
spurious surfaces / merge surfaces where the SAD sensor confabulates? Both directions
are live.

## 2. THE ANTAGONIST, PRE-STATED (the sensor's real-texture error, rung 94000)

The SAD sensor confabulates ~10.67% at its operating point and falls off a **cliff
where mean block std < 0.4** (below one 8-bit step): silent miss 0.0003→0.0641,
confidently wrong 0.0166→0.0544; and it silent-misses 50–75% on a straight edge
(aperture problem). Real BSDS crops have low-contrast regions and long edges that
Fourier noise does not. Prediction: the carve degrades where local band contrast is
low; the participation ratio (speck-robust) absorbs isolated confab, so a DEGRADE
needs SPATIALLY-COHERENT band confab, not specks.

**Pre-measured (corpus scan, burned): the cliff is nearly unreachable in BSDS at
48-px band width — 1/200 train images has a band < 0.4, 35/200 below 1.0, 70/200
below 2.0.** So the confirmatory RANDOM arm samples the natural rate; a SECONDARY
adversarial low-contrast arm hunts the corpus-wide flat tail (down to ~0.4) to
exhibit the bound.

## 3. STATISTICS (exactly these)

Unit of analysis = the SEED (scene). 95% bootstrap CI (`default_rng(0..999)`
resampling — deterministic, the parallax rung's exact `_ci`). For each condition
(DEPTH, FLAT) at each τ∈{0, √5}:

- **eff_surfaces** = `1/Σpᵢ²` (participation ratio — speck-robust; the parallax
  primary), and **largest_frac** = biggest surface / frame. Reported also: raw count,
  raw median, top-5 fractions.
- **confab_rate** = fraction of cells where sensed V ≠ ground-truth t (the inherited
  sensor error made visible on the carve's own field).
- **space constancy**: sensed reference-band residual max `|R_se|` (the parallax rung
  found ground-truth 0 but sensed ≤3 on synthetic — this rung asks what real texture
  does to it).
- **field discontinuity of the FLAT residual** (null-exposure guard).
- **min_band_std** per crop, and **corr(|eff−3|, min_band_std)** + **corr(confab,
  min_band_std)** (WHERE it degrades vs local contrast).
- **static-frame control**: band-boundary-column gradient vs within-frame gradient in
  real `a` (ratio ≈ 1 ⇒ the depth bands leave no special static trace; and `a` is
  byte-identical DEPTH-vs-FLAT regardless).

Arms (no sweeps): **synthetic** (the re-earned floor, same seeds), **real_random**
(PRIMARY, natural rate), **real_lowcon** (SECONDARY probe, corpus-flat tail).

## 4. n, FIXED IN ADVANCE = 80 (seeds 124000–124079)

Power analysis on burned pilot seeds 116000–116019 (n=20): DEPTH eff (real, τ=√5)
mean **3.11**, per-seed SD ≈ 0.27; DEPTH-vs-FLAT gap ≈ 3.11 vs 1.01 (power ≈ 1.0). At
n=80, eff CI half-width ≈ 0.06; a real-vs-synthetic eff difference ≥ ~0.1 detectable
at 80% power. **n=80 fixed to MATCH the parallax rung exactly**, so the real-vs-
synthetic comparison is on matched n, and to sample the low-contrast tail. No
interim-look stopping; all three arms run once.

Pilot readout (burned, informative — NOT confirmatory): synthetic reproduces the
floor (DEPTH eff 3.10–3.11, largest 0.36, FLAT eff 1.00); real_random DEPTH eff
3.11–3.20, FLAT 1.01, **sensed reference residual 3→11px**, confab 7.7%; real_lowcon
reaches min_band_std 0.43, confab 9.8%, FLAT eff 1.06, **corr(|eff−3|, min_band_std)
= −0.41** (degradation concentrates at low contrast).

## 5. DECISION RULE (registered before any confirmatory number)

Primary = **real_random**, DEPTH eff_surfaces + largest_frac, both τ, n=80.

- **CONFIRM** — the carve survives real photometry: real DEPTH eff CI ⊂ **[2.5, 3.5]**
  AND largest_frac < 0.5 AND FLAT eff CI ⊂ [0.9, 1.2] with largest > 0.9 AND
  DEPTH-vs-FLAT CI-separated on both statistics at both τ AND real DEPTH eff within
  **0.25** of the synthetic floor on the same seeds (same knee). The size
  distribution is the headline.
- **DEGRADE** (a real, valuable finding) — the knee SURVIVES (DEPTH still few-and-
  large, DEPTH-vs-FLAT still CI-separated) but real texture measurably moves a
  registered quantity away from synthetic: any of (a) real DEPTH eff CI excludes the
  synthetic eff (spurious surfaces if higher, merges if lower); (b) real largest_frac
  CI above synthetic; (c) sensed space-constancy residual materially worse than
  synthetic's ≤3px; (d) the low-contrast probe drives the carve out of the object
  band / fragments FLAT where random crops do not. **Quantify HOW MUCH and WHERE, tie
  to min_band_std / the 0.4 cliff.** "The mechanism works on real texture down to
  local contrast X" is the result.
- **FALSIFY** — real photometry breaks the carve: real DEPTH eff CI NOT in [2.5,3.5]
  (ground stays one blob eff→1, OR shatters eff≫3.5 even under the participation
  ratio), OR DEPTH-vs-FLAT NOT CI-separated. Then real photometry (not just real
  motion) is a blocker and the SAD/common-fate sensor OBJECTIVE is the thing to fix
  (a null here redirects to "improve the sensor means change the objective").

A DEGRADE that co-occurs with a surviving primary knee is reported as **CONFIRM on
the size-distribution knee + DEGRADE on the named inherited-sensor quantity**, both
stated, per §7/§8.

## 6. PREDICTION (§3 clause 7), with provisos

~55% **DEGRADE-leaning-CONFIRM**: the primary few-and-large knee SURVIVES real
photometry (real DEPTH eff ≈ 3.0–3.2 in the object band, largest ≈ 0.35, FLAT ≈ 1.0,
CI-separated — the size distribution holds), because BSDS crops carry ample structure
and the participation ratio absorbs the extra confab. ~35% clean CONFIRM (real ≈
synthetic within 0.25). ~10% DEGRADE-past-knee / FALSIFY if real edges coherently
merge or shatter a band.

Named provisos, each falsifiable: (i) **space constancy degrades** — sensed reference
residual rises from ~3px (synthetic) toward ~11px (real), because real texture gives
the SAD sensor more chances to confabulate on the reference band; (ii) **the
catastrophic cliff is nearly unreachable** in BSDS at this band width, so the carve
inherits only the MILD confab bound (~8–10% confab), not the >99% regime; (iii) the
low-contrast probe shows a NEGATIVE corr(|eff−3|, min_band_std) — degradation
concentrates at low local contrast, exactly where the sensor cliff predicts. If
proviso (i) breaks (residual stays ≤3), I misunderstood how real texture loads the
SAD reference match; if (ii) breaks (a random crop hits <0.4), BSDS is flatter than
the corpus scan said.

## 7. SEED LEDGER + §13

- **Block 124000–124999** `check_claim` at prereg time (verbatim, §3 clause 8):
  ```
  SEED CLAIM 124000-124999: CLEAN -- no collision DETECTED.
    Scope: 826 files with seed sinks; 515 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```
- Confirmatory seeds **124000–124079** (never used for anything). Pilot on burned
  **116000–116019**. `seed_audit` reports **2 unknown sinks** for
  `parallax_real_measure.py` — the `default_rng(sd)` / `default_rng(k)` CLI blind
  spot (the parallax rung's exact disclosure): `sd` ranges over the hardcoded seed
  lists, `k` over the fixed bootstrap 0..999 (resampling generators, not scene
  seeds). Disclosed, not resolved-away.
- **§13:** every threshold falls out or is stimulus config. τ = exact 0 (no number) /
  √5 (the sensor gate's Otsu-within-aperture tolerance, rung 94000). The object band
  [2.5,3.5] and 0.25 same-knee tolerance are DECISION-RULE brackets around the
  synthetic floor (3.1), not measure thresholds — the discriminators are a
  participation ratio and a fraction. The 0.4 cliff is INHERITED from rung 94000
  (measured, not chosen) and used only as a REPORTING split for the WHERE analysis,
  never as a verdict. The shifts / block / grid are STIMULUS/SENSOR config (the
  parallax rung's standing). **NO NEW RUST, NO NEW SEED** (a measurement reusing the
  parallax carve machinery); Term enum index 180 remains unused.

## 8. WHAT THIS CANNOT SHOW (scope, §8)

Real MOTION is still not tested (no real 3D-motion video in the tree — a flat photo
under self-motion gives uniform shift = the FLAT case). Only PHOTOMETRY changes.
Fronto-parallel bands, horizontal parallax, N=3, one SAD aperture family, no
occlusion, no colour, no shape — all inherited from the parallax rung. The low-
contrast probe reuses ~60 flat source images across 80 seeds (image reuse disclosed;
it is a SECONDARY probe, not the primary confirmatory statistic).
