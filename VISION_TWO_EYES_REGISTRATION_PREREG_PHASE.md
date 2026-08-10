# PRE-REGISTRATION (corrected mechanism) — block 176000-176999: OFFSET IS A CROSS-FRAME PHASE

**Committed ALONE, before the corrected mechanism's numbers are measured.** Same
seed block **176000-176999** (already drawn CLEAN; this is the SAME rung, a
revised estimator — §3 rule 6: a new mechanism gets its own pre-registration).

## WHY A SECOND PREREG

The first prereg (`VISION_TWO_EYES_REGISTRATION_PREREG.md`) proposed reusing
149000's `subcell_register.bilinear_upsample` in an amplitude-SAD shift search.
It was committed, then MEASURED as **FAIL** (see `VISION_TWO_EYES_REGISTRATION_
RESULTS.md` §1): registration error **0.09** (> 0.05), and the fused-with-estimate
reconstruction was WORSE than a single eye (gain 0.23×). Diagnosis (control
sweep, 10 seeds):

| registration content | mean bias | std | range |
|---|---|---|---|
| full texture (k1,2,3 + aliased k0) | −0.015 | **0.165** | [−0.21, +0.25] |
| texture WITHOUT the k0 target (a0=0) | +0.014 | 0.025 | [−0.02, +0.05] |
| only k1 (a0=0) | +0.000 | 0.009 | [−0.02, +0.01] |

**NAMED CONSTRAINT (the real finding):** you cannot register two ALIASED
single-eye views by an amplitude/SAD metric — the aliased supra-Nyquist target's
energy is INDISTINGUISHABLE from real in-band energy to a shift metric, so the
very harmonic super-resolution targets is what corrupts the registration. Remove
k0 and the SAD reuse is accurate to ~0.025; add it and the estimate swings ±0.25
by phase. This is a genuine limitation of the reused primitive in the aliased
regime, not a resolution bug.

## THE CORRECTED MECHANISM — THE OFFSET IS A CROSS-FRAME PHASE

The frame/continuum invariant (BASE-AS-DIMENSION, `CLAUDE.md`) says non-integer
structure is CROSS-FRAME and names the map explicitly: *"Fourier
(spatial↔spectral) … lives in the MAP between frames."* The sub-receptor offset
δ is exactly such a cross-frame quantity — it is a PHASE in the spectral map, not
an amplitude feature. So read it there:

- For each WELL-SAMPLED harmonic bin k (below the single-eye Nyquist N/2), the
  two eyes' DFT bins satisfy `B_k / A_k = exp(+i·2π·k·δ/N)` (the shift theorem),
  so `δ = angle(B_k/A_k) · N / (2π·k)` — EXACT for that bin, no interpolation.
- The aliased target k0 folds onto bin `|k0 − N|` (for k0=6, N=8 → **bin 2**).
  **That bin is EXCLUDED by construction** — it is the one bin the aliased energy
  contaminates. The estimate uses the NON-ALIASED bins (k=1, k=3), which the
  target cannot reach. This exclusion is pure arithmetic from the known (N, k0)
  band structure — NOT fit to data.
- δ is amplitude-weighted-averaged over the clean bins, then emitted as a
  FINER-UNIT INTEGER `bt = round(δ·S)` (S=100) — the invariant-clean STEPPED
  observable; δ_est = bt/S is the cross-frame map (allowed non-integer).

The sensor is `domains.two_eye_register.estimate_offset_phase` (a NEW mechanical
numpy sensor; no agent decision, no graph state). Fusion is UNCHANGED
(`multilook_superres` kernel). Calibration over 30 seeds (bins {1,3}): mean bias
+0.003, std 0.015, maxabs 0.031 — the basis for the H1 bound below.

## PRE-REGISTERED PASS CRITERIA (all must hold) — SAME criteria as v1

Same texture (k=1 A=55, k=2 A=40, k=3 A=30, k0=6 A=12; N=8, δ_true=0.5) and same
graph-native fusion; ONLY the offset estimator changes.

**H1 — Registration accuracy:** **|δ_est − δ_true| ≤ 0.05** (δ_true=0.5).

**H2 — Super-res holds under the ESTIMATED offset:**
> **err_single / err_fused(δ_est) > 4**, AND
> **k0_relerr_fused(δ_est) < 0.25**, WHILE **k0_relerr_single > 0.60**.

**C1 — Perturbed offset degrades (load-bearing):**
> **err_fused(δ_est + 0.25) ≥ 2 × err_fused(δ_est)** AND
> **err_fused(δ_est − 0.25) ≥ 2 × err_fused(δ_est)**.

**C2 — Zero-offset falsifier on the estimate:** δ_true=0 →
> **|δ_est| ≤ 0.02** AND **err_single / err_fused(δ_est=~0) ∈ [0.8, 1.25]**.

**C3 — Single-eye baseline** reported.

## DISCIPLINE (pre-committed)

Identical to v1: additive NEW files only; Rung-5 known-offset path + single-eye
pipeline BYTE-UNCHANGED; oracle `bash scripts/rung7_vision_bench.sh` 0 failed,
BEFORE == AFTER; provenance gate asserts `source_match in ("own","shared")`, never
a pinned hash; NO Rust built (canonical `_native.abi3.so` untouched); NO TIMING
CLAIM. Gate: `tests/test_two_eyes_registration_migrated.py`.

Read the corrected mechanism's MEASURED values only after this file is committed
alone.
