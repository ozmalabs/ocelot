# VISION — RUNG 5 RESULTS: TWO EYES → SUPER-RESOLUTION by MULTI-LOOK DE-ALIASING

Prereg: `VISION_TWO_EYES_PREREG.md` (block **175000**, committed alone at
`0c655a7f6a` before any number). Engine: this tree's own build
(`source_match = own`, sha `aa8df3753f3b`). Measured by
`scripts/two_eye_superres_measure.py`, gated by `tests/test_two_eyes_migrated.py`
(7/7). Results JSON: `results/two_eye_superres.json`.

## Headline — the six pre-registered criteria ALL PASS

### SPATIAL (flat textured wall, N=8 receptors, k0=6; single-Nyquist 4 < 6 < fused-Nyquist 8)

| reconstruction MSE vs dense true field | value |
|---|---|
| single eye | 1.268e-03 |
| **fused, sub-receptor offset δ=0.5** | **5.597e-07** |
| naive 2× (single eye + interp midpoints) | 6.362e-04 |
| fused, ZERO offset (two identical eyes) | 1.268e-03 |

- **Criterion 1 — fusion beats a single eye:** `err_single/err_fused(0.5)` =
  **2266×** (> 4). ✅
- **Criterion 2 — fusion beats naive 2× stacking:** `err_naive2x/err_fused(0.5)`
  = **1137×** (> 2). More pixels without a second real look does not de-alias. ✅
- **Criterion 3 — THE FALSIFIER, zero-offset shows NO gain:**
  `err_single/err_fused(0.0)` = **1.000** (∈ [0.8, 1.25]). Two identical eyes add
  no new distinct sample positions → no super-resolution. The win is the OFFSET,
  not the sensor count. ✅
- **Criterion 4 — a target only the fused pair resolves:** the supra-Nyquist
  harmonic k0=6 has relative reconstruction error **1.000** for the single eye
  (band-limited below k0 — it literally cannot represent it) and **0.007** for
  the fused pair. ✅

### TEMPORAL (space-offset ≡ time-offset — the async win, M=8, k0=6)

The IDENTICAL Rust kernel with sample positions reinterpreted as TIMES. Two eyes
on INDEPENDENT async clocks (clock A ticks {0,1,…,7}, clock B ticks
{0.5,1.5,…,7.5}) — they share **ZERO** ticks — sample the union of their event
times.

| temporal-reconstruction MSE | value |
|---|---|
| single clock | 1.248e-03 |
| **fused, async offset 0.5** | **1.322e-06** |
| fused, clocks in phase (offset 0) | 1.248e-03 |

- **Criterion 5 — async union beats one clock:** **944×** (> 4). ✅
- **Criterion 6 — temporal falsifier, clocks in phase → no gain:** **1.000**
  (∈ [0.8, 1.25]). ✅

## What is graph-native / what is Python

- **The FUSION is the Rust `multilook_superres` CognitiveTask kernel** (no new DSL
  Term enum — a pure kernel kind, plus a small `gauss_solve` linear solver) +
  the `retinal_mint_superres` graph rule (`seeds/retinal_superres.json`), which
  mints a `SuperResolvedField` from the completed task. The kernel does a
  band-limited least-squares reconstruction from samples at known nonuniform
  positions through ONE fixed operator; a small ridge damps modes the samples do
  not constrain. The offset is load-bearing: it turns N distinct sample positions
  into 2N (the band-limit the DISTINCT samples support, counted mechanically),
  which is what lets the high harmonics be recovered.
- **Python (`domains/two_eye_superres.py`) is mechanical I/O only:** build two
  `GraphEye`s, sample the textured surface at each eye's receptor positions
  (offset by a KNOWN sub-receptor amount), read each receptor's transduced
  `activation`, pack the two eyes' sample cloud into the fusion task, read the
  minted field back out. No agent decision, no graph-state conditional.

## Discipline

- **Default OFF / byte-identity (§9):** the kernel, seed, and adapter are
  ADDITIVE. No existing kernel, seed, or `GraphEye` build path was edited. The
  mint rule cannot fire without an opted-in `SuperresParams` node
  (`test_two_eyes_migrated.py::…off_gate_is_silent`,
  `…default_graph_eye_loads_no_superres_machinery`).
- **Oracle** `bash scripts/rung7_vision_bench.sh`: **214 passed, 10 skipped, 0
  failed** BEFORE and AFTER — identical (flag off / additive).
- **Provenance:** `source_match = own`; canonical tree's `_native.abi3.so` md5
  `e2b72b940bed9e0d8a29a3bac5780e04` UNCHANGED across the whole rung (built only
  in this worktree via `scripts/engine_build.sh`, safe `cp --remove-destination`).
- **NO TIMING CLAIM.**

## Honest residuals

- The sub-receptor offset is **KNOWN** (a controlled displacement), not estimated
  from the images. Registration-from-data (the tree's proven `subcell_register`,
  block 149000) is a separate, additional problem; here the offset is a given,
  isolating the de-aliasing win. This is the largest caveat.
- The SPATIAL headline runs on the photon eye's native **1-D azimuth strip** (the
  eye's documented foundation). The 2-D flat-wall case is the SAME kernel applied
  per elevation row (separable, azimuth-only offset) — a noted follow-on, not run
  here.
- The band-limit is set to the Nyquist the DISTINCT samples support (counted from
  the known positions). Fitting more harmonics than distinct samples support is
  ill-posed; keying the band-limit to the count is what makes the zero-offset
  falsifier fall out of the data (N distinct → single's Nyquist) rather than a
  hand-set knob.
- The gain SATURATES and is bounded by photon quantisation + the ridge floor; the
  claim is a large, sign-definite, control-separated gain, not infinite
  resolution. Magnitudes (thousands×) are synthetic-clean; the mechanism, not the
  headline number, is the result (a benchmark on real textures is a separate
  measurement).
