# RESULTS — block 176000-176999: TWO EYES, ESTIMATED OFFSET → SUPER-RESOLUTION

Closes Rung 5's largest caveat. Rung 5 (block 175000) proved two-eye
super-resolution by multi-look de-aliasing but with a **KNOWN** sub-receptor
offset handed to the fusion. Here the offset is **ESTIMATED from the two eyes'
OWN overlapping data**, fed into the UNCHANGED Rung-5 `multilook_superres`
kernel, and the super-resolution win is shown to STILL HOLD — the eye
super-resolves WITHOUT being told the offset.

Two preregs, committed alone before their numbers, ONE rung:
`VISION_TWO_EYES_REGISTRATION_PREREG.md` (v1) and
`VISION_TWO_EYES_REGISTRATION_PREREG_PHASE.md` (corrected). Measured by
`scripts/two_eye_registration_measure.py`, gated by
`tests/test_two_eyes_registration_migrated.py` (10/10). Raw:
`results/two_eye_registration.json`. Engine `source_match = shared`
(source-identical to this tree; NO Rust built).

## §1 — THE v1 REUSE (amplitude-SAD) FAILED, and WHY (the named constraint)

The mission's instruction was to reuse the proven 149000 `subcell_register`
machinery. v1 did exactly that: `domains.two_eye_register.estimate_offset`
reuses `subcell_register.bilinear_upsample` and searches for the fine shift that
minimises SAD between the two eyes' upsampled activation sequences (the 1-D
periodic analog of `register_residual_offset`). It was committed, then MEASURED:

| v1 amplitude-SAD (block 176000 texture, δ_true=0.5) | value |
|---|---|
| estimated offset δ_est | **0.59** |
| registration error | **0.09** (> 0.05 — FAIL H1) |
| gain fused(δ_est)/single | **0.23×** (WORSE than one eye — FAIL H2) |

Diagnosis (control sweep over 10 seeds, isolating the cause):

| registration content | mean bias | std | range |
|---|---|---|---|
| full texture (k1,2,3 + aliased k0) | −0.015 | **0.165** | [−0.21, +0.25] |
| texture WITHOUT the k0 target (a0=0) | +0.014 | 0.025 | [−0.02, +0.05] |
| only k1 (a0=0) | +0.000 | 0.009 | [−0.02, +0.01] |

**NAMED CONSTRAINT:** *you cannot register two ALIASED single-eye views by an
amplitude/SAD shift metric — the aliased supra-Nyquist target's energy is
INDISTINGUISHABLE from real in-band energy to a shift metric, so the very
harmonic super-resolution targets is what corrupts the registration.* Remove k0
and the SAD reuse is accurate to ~0.025; add it and the estimate swings ±0.25 by
phase. This is a genuine limitation of the reused primitive in the aliased
regime — not a resolution bug. It is the real finding that motivated the
correction, and it is gated
(`test_v1_amplitude_sad_is_corrupted_by_the_aliased_target`).

## §2 — THE CORRECTED MECHANISM: THE OFFSET IS A CROSS-FRAME PHASE

The frame/continuum invariant (`CLAUDE.md`, BASE-AS-DIMENSION) names the map
explicitly: *"Fourier (spatial↔spectral) … lives in the MAP between frames."*
The sub-receptor offset δ is a cross-frame PHASE, not an amplitude feature. For
each WELL-SAMPLED bin k, `B_k / A_k = exp(+i·2π·k·δ/N)` (shift theorem), so
`δ = angle(B_k/A_k)·N/(2π·k)` — EXACT, no interpolation, AMPLITUDE-INDEPENDENT.
The aliased target k0=6 folds onto **bin 2** (`|6−8|`), which is EXCLUDED by
arithmetic; the estimate uses the non-aliased bins **{1, 3}** the target cannot
reach (`domains.two_eye_register.estimate_offset_phase` / `clean_bins`). δ is
emitted as a FINER-UNIT INTEGER `bt = round(δ·S)` (S=100) — the invariant-clean
STEPPED observable; δ_est = bt/S is the cross-frame map (allowed non-integer).

### The six pre-registered criteria ALL PASS (same texture, same graph fusion)

Flat textured wall, N=8, k=1 A=55 / k=2 A=40 / k=3 A=30 (well-sampled anchors) +
k0=6 A=12 (supra-Nyquist target; single-Nyquist 4 < 6 < fused-Nyquist 8),
δ_true=0.5.

| reconstruction MSE vs dense true field | value |
|---|---|
| single eye | 9.576e-05 |
| **fused, ESTIMATED offset δ_est=0.49** | **4.855e-06** |
| fused, KNOWN offset δ=0.5 (Rung-5 reference) | 1.400e-07 |
| fused, PERTURBED δ_est+0.25 | 2.345e-03 |
| fused, PERTURBED δ_est−0.25 | 2.721e-03 |

- **H1 — registration accurate:** δ_est = **0.49**, |δ_est − 0.5| = **0.01**
  (≤ 0.05). ✅ The offset estimated from the two eyes' own data ≈ the true offset.
- **H2 — super-res holds under the estimate:** `err_single/err_fused(δ_est)` =
  **19.7×** (> 4); k0 relative error **0.009** fused (< 0.25) vs **1.000** single
  (> 0.60 — a single eye literally cannot represent k0, it aliases). ✅ The
  supra-Nyquist harmonic is de-aliased using the ESTIMATED offset.
- **C1 — perturbed offset degrades (load-bearing):** a wrong offset degrades the
  fusion by **483×** (+0.25) / **560×** (−0.25) — both ≥ 2×. ✅ The win is NOT
  offset-agnostic; the estimate carries it.
- **C2 — zero-offset falsifier on the estimate:** two IDENTICAL eyes (δ_true=0)
  → δ_est = **0.0000** (≤ 0.02), gain **1.000×** (∈ [0.8, 1.25]). ✅ No new
  distinct positions → no super-resolution, exactly as Rung 5.
- **C3 — single-eye baseline** = 9.576e-05 (the reference arm).

## §3 — What is graph-native / what is Python

- **Fusion is graph-native and UNCHANGED:** the Rung-5 `multilook_superres` Rust
  CognitiveTask kernel + `retinal_mint_superres` rule (`seeds/retinal_superres.
  json`), driven through `domains/two_eye_superres.py`. NO new DSL Term enum, NO
  new CognitiveTask kind, NO Rust build.
- **Registration is a mechanical numpy SENSOR** (`domains/two_eye_register.py`) —
  the blessed `subcell_register` / `vector_field` class: it READS ONLY the two
  eyes' activation arrays and emits an integer finer-unit offset. NO agent
  decision, NO graph-state conditional. Which bins are clean is arithmetic from
  the known (N, k0) band structure, not a data-fit.
- **Python is I/O only:** build two `GraphEye`s, sample the wall at the TRUE
  (kernel-unknown) offset — DISCARDING eye B's true positions, keeping only its
  activations — register → δ_est, build eye-B positions from δ_est, fuse, read
  the minted `SuperResolvedField`, score.

## §4 — The frame/continuum invariant (BASE-AS-DIMENSION), audited clean

The registration output `bt` is an INTEGER (finer units of 1/S receptor) — the
STEPPED observable (gate `test_offset_observable_is_a_finer_unit_integer`).
δ_est = bt/S is a CROSS-FRAME quantity (the map `Hom(frame_A, frame_B)` — a
spectral PHASE), so it MAY be non-integer: a map, never an in-frame coordinate.
No float is written into any in-frame coordinate. S=100 and the clean-bin set
are DECLARED §13 residuals, not tuned tolerances. This rung is a second, clean
instance of the invariant: *the base/continuum lives between frames* — here the
between-frames continuum is the Fourier phase that carries the offset.

## §5 — Discipline

- **§9 default-OFF / byte-identity:** additive — NEW files only
  (`domains/two_eye_register.py`, `scripts/two_eye_registration_measure.py`, the
  gate, the two preregs, this doc, the results JSON). The Rung-5 known-offset
  path and the single-eye pipeline are BYTE-UNCHANGED (`git diff` shows no
  existing tracked file touched; the Rung-5 gate `test_two_eyes_migrated.py` is
  7/7 green; the OFF gate is still silent —
  `test_rung5_fuser_off_gate_still_silent`,
  `test_default_graph_eye_loads_no_superres_machinery`).
- **Oracle** `bash scripts/rung7_vision_bench.sh`: **214 passed, 10 skipped, 0
  failed** BEFORE and AFTER — identical (flag off / additive; no Rust rebuilt).
- **Provenance (§10):** `source_match = shared` (this worktree carries no local
  `.so`; the `.pth` resolves the canonical engine, whose Rust source is
  byte-identical to this tree at the base commit — no Rust was built). The gate
  asserts `source_match in ("own","shared")`, never a pinned hash. The canonical
  `_native.abi3.so` is UNTOUCHED (verified md5 unchanged across the rung).
- **NO TIMING CLAIM.**

## §6 — Honest residuals

- **The registration-vs-super-res tension the phase estimator DISSOLVES.** The
  prereg texture keeps k0 MODEST (A=12) so the well-sampled harmonics dominate —
  chosen conservatively while v1's amplitude-SAD needed them to. But the phase
  estimator reads δ from the clean bins {1,3} ONLY and is therefore COMPLETELY
  IMMUNE to k0's amplitude: k0 could be made dominant (huge single-eye MSE miss →
  huge fused gain) with EQUALLY accurate registration. The modest-but-passing
  MSE gain here (19.7×, vs Rung-5's 683× known-offset reference on this texture)
  is an artifact of the conservative texture, not of the estimator. A follow-on
  with a k0-dominant wall is a NEW measurement and needs its own prereg (not
  bolted on here).
- **1-D azimuth strip.** As in Rung 5, the SPATIAL headline runs on the photon
  eye's native 1-D azimuth strip; a 2-D flat wall is the same estimator per
  elevation row (separable), noted not run.
- **Sub-receptor offset assumed** (no phase unwrapping): the wall's offset is
  sub-receptor, so the clean-bin phases are unambiguous. A supra-receptor
  displacement would need unwrapping (a coarse integer anchor + the phase
  residual — the 149000 pattern), out of scope here.
- **Synthetic-clean magnitudes.** The mechanism, not the headline number, is the
  result; a benchmark on real textures is a separate measurement.

## §7 — Proposed VISION_PROTOCOL.md ledger row

| **176000–176999 (two eyes, ESTIMATED offset → super-resolution; NO Rust — a mechanical numpy registration SENSOR `domains/two_eye_register.py`, DEFAULT OFF / new files only; feeds the UNCHANGED Rung-5 `multilook_superres` kernel)** | **THE OFFSET IS A CROSS-FRAME PHASE — closes Rung 5's largest caveat (the KNOWN offset).** Estimate the sub-receptor offset from the two eyes' OWN overlapping data, feed it to the unchanged fusion, and the super-res win HOLDS. **v1 (committed) FAILED honestly:** reusing 149000's `subcell_register.bilinear_upsample` in an amplitude-SAD shift search gives δ_est=0.59 (err 0.09) and fused-WORSE-than-single (0.23×) — NAMED CONSTRAINT: the aliased supra-Nyquist target's energy is indistinguishable from real in-band energy to a shift metric (accurate to 0.025 without k0; ±0.25 swing with it). **v2 (corrected, prereg'd alone before measurement) PASSES all 6:** the offset is a cross-frame PHASE ("Fourier lives in the MAP between frames"), read from the NON-ALIASED bins {1,3} (k0=6 folds onto bin 2, excluded by arithmetic). H1 δ_est=0.49 (err **0.01** ≤ 0.05); H2 gain **19.7×** (>4), k0 relerr **0.009** fused vs **1.000** single; C1 perturbed offset degrades **483×/560×** (load-bearing); C2 zero-offset → δ_est **0.0000**, gain **1.000×** (Rung-5 falsifier holds on the estimate). Invariant-clean: the emitted offset observable is a FINER-UNIT INTEGER, δ_est=bt/S a cross-frame map. Fusion graph-native/UNCHANGED (no Rust, no new Term/kind). §9 byte-identity — new files only, Rung-5 gate 7/7 green, OFF gate silent. `source_match=shared` (no Rust built; canonical `.so` untouched); oracle `rung7_vision_bench.sh` **214/10/0 BEFORE == AFTER**; gate `test_two_eyes_registration_migrated` **10/10**; `SEED CLAIM 176000-176999 CLEAN`. NO TIMING CLAIM. Raw: `results/two_eye_registration.json`; `VISION_TWO_EYES_REGISTRATION_RESULTS.md`. |
