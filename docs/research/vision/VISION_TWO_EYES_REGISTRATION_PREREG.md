# PRE-REGISTRATION — block 176000-176999: TWO EYES, ESTIMATED OFFSET → SUPER-RESOLUTION

**Committed ALONE, before any number is measured.** Seed block **176000-176999**
(`python3 scripts/seed_claim.py 176000 176999` → CLEAN; the highest ledger block
is 175000-175999; 176000 is the next free block, not any block in
`VISION_PROTOCOL.md`).

## THE CAVEAT THIS RUNG CLOSES

Rung 5 (block 175000, `VISION_TWO_EYES_RESULTS.md`) proved two-eye
super-resolution by multi-look de-aliasing — but the sub-receptor offset δ was
**KNOWN** (handed to the fusion). Its own "Honest residuals" names this the
LARGEST caveat: *"Registration-from-data (the tree's proven `subcell_register`,
block 149000) is a separate, additional problem."*

This rung closes it: **ESTIMATE the offset from the two eyes' OWN overlapping
data, feed the estimate into the super-resolution kernel, and show the win STILL
HOLDS** — the eye super-resolves WITHOUT being told the offset.

## MACHINERY REUSED (no new engine)

- **Registration** reuses the PROVEN sub-cell cross-frame primitive
  `domains.subcell_register.bilinear_upsample` (block 149000 — "sub-cell
  cross-frame registration proven"), in a thin NEW mechanical numpy SENSOR
  `domains/two_eye_register.py` (the 1-D periodic analog of the 2-D
  `register_residual_offset`, exactly as `subcell_register` is "the ink twin of
  `motion_group_world.vector_field`"). It READS ONLY the two eyes' activation
  arrays, upsamples both by an integer factor S (the declared §13 finer unit),
  and returns the sub-receptor offset as a **FINER-UNIT INTEGER** (`bt`, the
  cross-frame observable); δ_est = bt / S. No agent decision, no graph state.
- **Fusion** reuses Rung 5's `multilook_superres` CognitiveTask kernel +
  `retinal_mint_superres` rule (`seeds/retinal_superres.json`), driven through
  `domains/two_eye_superres.py` UNCHANGED. **NO new DSL Term enum variant, NO new
  CognitiveTask kind, NO Rust build.**
- Python is mechanical I/O only: build two `GraphEye`s, sample the wall at the
  TRUE (unknown-to-the-kernel) offset, register → δ_est, build eye-B positions
  from δ_est, fuse, read the minted field, score.

## FRAME/CONTINUUM INVARIANT (BASE-AS-DIMENSION)

The registration output `bt` is an INTEGER (finer units of 1/S receptor) — the
STEPPED observable. δ_est = bt/S is a CROSS-FRAME quantity (the map
`Hom(frame_A, frame_B)` between the two eyes), so it MAY be non-integer: it is a
map, never an in-frame coordinate. The fusion's reconstruction grid is already
continuous (the kernel's cross-frame rendering). No float is written into any
in-frame coordinate. `S = 100` and the ±1-receptor search window are DECLARED
§13 resolution residuals (like `block` / `k`), not tuned tolerances.

## THE TEXTURE (one flat textured wall)

A flat-wall luminance texture, period P = N receptors (N = 8), carrying
WELL-SAMPLED low harmonics that DOMINATE (the registration anchors: k=1 A=55,
k=2 A=40, k=3 A=30 — all below the single-eye Nyquist N/2 = 4) plus a MODEST
supra-Nyquist harmonic **k0 = 6** (A=12) with single-eye-Nyquist (4) < k0 < fused
Nyquist (8) — the de-aliasing target that ALIASES in one eye. Registration locks
on the dominant well-sampled structure; the modest aliased contamination gives a
small, bounded bias. Amplitudes/phases drawn from the block seed. Eyes transduce
via Naka-Rushton (same as Rung 5). Sampled at the TRUE offset δ_true = 0.5.

## PRE-REGISTERED PASS CRITERIA (all must hold)

**H1 — Registration accuracy (headline 1).** The offset ESTIMATED from the two
eyes' data matches the true offset:
> **|δ_est − δ_true| ≤ 0.05 receptors** (δ_true = 0.5).

**H2 — Super-res holds under the ESTIMATED offset (headline 2).** Fusion using
δ_est still beats a single eye and recovers k0:
> **err_single / err_fused(δ_est) > 4** (single-eye MSE over the fused-with-estimate MSE), AND
> **k0_relerr_fused(δ_est) < 0.25** (the supra-Nyquist harmonic is resolved) WHILE
> **k0_relerr_single > 0.60** (a single eye cannot represent k0 — it aliases).

**C1 — Perturbed offset degrades (able-to-fail; proves the estimate is
load-bearing).** A deliberately-wrong offset fed to the SAME fusion degrades:
> **err_fused(δ_est + 0.25) ≥ 2 × err_fused(δ_est)** AND
> **err_fused(δ_est − 0.25) ≥ 2 × err_fused(δ_est)**.
The win is NOT offset-agnostic.

**C2 — Zero-offset control (the Rung-5 falsifier, now on the ESTIMATE).** With
δ_true = 0 (two identical eyes), the estimate collapses and there is no gain:
> **|δ_est(δ_true = 0)| ≤ 0.02 receptors** AND
> **err_single / err_fused(δ_est=~0) ∈ [0.8, 1.25]** (no super-resolution: two
> identical eyes add no new distinct sample positions).

**C3 — Single-eye baseline** is measured and reported (the reference arm).

## DISCIPLINE (pre-committed)

- **§9 default-OFF / byte-identity:** additive — NEW files only
  (`domains/two_eye_register.py`, `scripts/two_eye_registration_measure.py`, the
  gate, this prereg, the results doc, the results JSON). The Rung-5 known-offset
  path (`domains/two_eye_superres.py`, `seeds/retinal_superres.json`, the
  `multilook_superres` kernel) and the single-eye pipeline are BYTE-UNCHANGED
  (proven by git-diff scope + the Rung-5 gate re-run green).
- **Oracle** `bash scripts/rung7_vision_bench.sh`: **0 failed, BEFORE == AFTER**
  (flag off / additive; no Rust rebuilt).
- **Provenance (§10):** the gate asserts `source_match in ("own","shared")` —
  never a pinned hash. NO Rust is built (registration is pure Python, fusion is
  the existing kernel), so the canonical `_native.abi3.so` is untouched.
- **NO TIMING CLAIM.**
- **Gate:** `tests/test_two_eyes_registration_migrated.py`.

Read MEASURED values only after this file is committed alone.
