# VISION — THE PHOTON EYE SEES DOOM (pre-registration)

**Seed block: 181000–181999.** `python3 scripts/seed_claim.py 181000 181999`
verbatim:

```
SEED CLAIM 181000-181999: CLEAN -- no collision DETECTED.
  Scope: 880 files with seed sinks; 596 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

Provenance: `source_match == "own"` (never a pinned hash). Canonical `.so`
md5 `417f667716d71ed7d98bae5df25fe9df` must be UNCHANGED (no Rust built).

## What this rung does

The proven event-native photon eye (blocks 171–180: `photon_transduce` →
`retinal_onset_2d` onset events → `held_surface` EMA accumulation) has only ever
been measured on SYNTHETIC clean scenes (flat textured blocks). This rung feeds
its FIRST REAL input — VizDoom E1M1 frames — and measures what it BUILDS. The
honest synthetic→real midpoint.

**Architecture (unchanged, additive):** a Doom frame's per-cell LUMINANCE
becomes PHOTON FLUX per receptor — mechanical world-adapter I/O
(`frame → per-receptor Poisson photon count → submit_photons_2d`), exactly as the
eye ingests any light. **NO RGB node, NO `native.segment` on pixels, NO agent
decision in Python.** The eye does its graph-native thing (transduce → onset
events → held-surface EMA) under `run_rules()`. VizDoom's per-pixel DEPTH/LABELS
are GROUND TRUTH for the MEASUREMENT HARNESS ONLY — an oracle, never fed into
cognition.

This reuses the **existing** `held_surface` seed (block 180000) and `GraphEye`
photon eye byte-for-byte. No Rust, no new Term, no new seed. New files only: a
frame→flux world adapter, a measure script, a self-contained gate + committed
fixture.

## Fixed configuration (declared apertures — residuals, NOT tuned to score)

- **Retina:** `N_EL=15 × N_AZ=20 = 300` cells (4:3, an exact 16× area-mean
  downsample of Doom's 320×240). Low-res is EXPECTED and honest; scale past
  ~18×18 is a SEPARATE frontier, not this rung.
- **Luminance→flux:** `count = round(luma)` — the 8-bit ITU-R 601 luminance value
  IS the per-receptor photon-count MEAN (the most literal "luminance is photon
  flux" mapping, no invented gain); **Poisson shot noise** drawn per tick around
  that mean (photon arrival IS Poisson — the physically-correct denoising story,
  exactly as block 180000). Rod half-saturation 1024 keeps 0–255 in the
  near-linear regime.
- **Eye regime (matches block 180000):** `ADAPT_RATE = 0.15`, `SURFACE_LR = 0.15`,
  `onset_threshold_db = 6.0`, `onset_refractory_epochs = 0.0`, `retina_2d`,
  synchronous, `worker_capacity = 1`.
- **Doom source:** E1M1 from the full `DOOM.WAD` (rich geometry — walls,
  corridors, doorways), `seed = 181000`, HUD + weapon render OFF (clean optic
  field), motion action = `turn_right`, `skip = 4` tics per captured frame.
- **Sequence (H1):** STATIC-A = real frame `f0` held for `T1 = 20` ticks (a
  paused view — the actual rendered frame, held); MOTION = the real turning frames
  `f1..fM` (`M = 13` distinct frames, one tick each); STATIC-B = the last motion
  frame `fM` held for `T3 = 10` ticks. Total 43 ticks.
- **Held reconstruction** = `HeldSurfaceCell.value` (the eye's own EMA). **Stateless
  single-tick** = `HeldSurfaceCell.obs` (raw `caught_quanta`, re-derived each tick,
  never integrated). **Per-tick work C(t)** = # `RetinalOnsetEvent` nodes minted at
  epoch t (WORK UNITS — no wall-clock claim). **True luminance field** = the
  NOISELESS caught field of the held frame (Poisson mean per cell).

## HEADLINE 1 — the eye BUILDS a Doom scene (PRIMARY, frames alone)

### H1: on the static stretch the held reconstruction converges (denoising)

- **H1a build_drop:** `asymptote` (mean accumulating error over the last 3
  STATIC-A ticks vs true `f0`) `< 0.15 × acc_error[tick 1]`.
- **H1b asymptote:** `asymptote < 0.12` (looser than synthetic's achieved 0.06 —
  real Doom is a richer, noisier field; the mechanism is identical).
- **H1c monotone:** number of static-A ticks where error rises by `> 0.03` is
  `≤ 3`.
- **H1d stateless_noisy_flat:** stateless single-tick error CV `< 0.20` AND
  stateless mean `E_sl > 2 × asymptote` (a real denoising gain exists).
- **H1e accumulation_gap:** `asymptote < 0.5 × E_sl` (accumulating beats
  stateless — the build).

### H2: per-tick cost BENDS with real motion (compute ∝ surprise)

- **H2a cost_drain:** cost plateau (mean onsets last 3 STATIC-A ticks)
  `≤ 0.15 × C[tick 1]`.
- **H2b motion_spike:** MAX motion-phase onset `≥ 20` (a clear multi-cell real
  event) AND mean motion onset `≥ 2.5 × max(plateau, 1)`.
- **H2c redrain:** STATIC-B plateau (mean onsets last 3 ticks) `≤ 0.5 ×` max
  motion onset (cost re-drains once motion stops).
- **H2d ratio:** `mean(motion onsets) / max(plateau, 1) ≥ 3` — the headline
  static-vs-motion compute ratio.

### CONTROL (must fail) — a temporally-SCRAMBLED frame order kills the build

A persistent accumulating eye is fed the M distinct motion frames in a SHUFFLED
order (seed 181000, cycled to length T1). No coherent held scene ⇒ no build,
compute stays high.

- **C1 no_build:** scramble `asymptote_scr ≥ 0.5 × scramble_start` (NO drop),
  equivalently `asymptote_scr > 2 ×` ordered asymptote.
- **C2 gap_killed:** scramble accumulation gap `(E_sl_scr − asymptote_scr) ≤
  0.5 ×` the ordered accumulation gap `(E_sl − asymptote)`.
- **C3 cost_high:** scramble mean onset count `≥ 3 ×` ordered plateau (compute
  does not drain).

## HEADLINE 2 — the reconstruction recovers REAL structure (SECONDARY, GT in scope)

VizDoom per-pixel DEPTH/LABELS are reachable in this environment (confirmed
headless: depth 0–167, labels list), so this headline is IN SCOPE. Oracle only —
never fed to the eye.

- **S1 depth_edge_corr:** Pearson correlation between the gradient-magnitude
  (edge) map of the held reconstruction (end of STATIC-A) and the edge map of the
  downsampled true DEPTH buffer `> 0.15`.
- **S2 above_null:** `depth_edge_corr > 3 × |null_corr|` AND `> null_corr`, where
  `null_corr` is the same correlation with the held field spatially SHUFFLED
  (structure destroyed).
- **(Reported, not gated):** carve-vs-labels IoU of the eye's 2-D common-fate
  carve over the motion phase vs the VizDoom labels grid, compared to the
  documented sub-grid wall baseline (~IoU 0.24) WITH its provenance caveat — that
  baseline is the OLD RGB `native.segment` path, a DIFFERENT carve; the number is
  reported for context, not as a matched comparison.

## PASS DEFINITION

- **H1 (primary) passes** iff all of {H1a,H1b,H1c,H1d,H1e, H2a,H2b,H2c,H2d, C1,C2,C3}.
- **H2 (secondary) passes** iff {S1,S2}.

Each criterion is a boolean over MEASURED values. The gate
(`tests/test_doom_eye_migrated.py`) reads them from a self-contained committed
frame fixture (a handful of real E1M1 frames + their depth/labels, downsampled)
so it runs without VizDoom in CI, and is able to fail on a flat build (the
mechanism grain: build drop, stateless gap, cost static-vs-motion ratio, scramble
death).

## DISCIPLINE

- Separate prereg commit BEFORE any number (this file alone).
- New files only; existing seeds/adapters + `.so` byte-identical (§9). Existing
  vision gates stay green; `bash scripts/rung7_vision_bench.sh` = 0 failed,
  BEFORE == AFTER.
- Cost is WORK UNITS (onset counts), never wall-clock.
- Honest residual up front: this is LOW-RES Doom (15×20); real-time-at-scale is a
  separate frontier. Synthetic-vs-real magnitude reported honestly.
