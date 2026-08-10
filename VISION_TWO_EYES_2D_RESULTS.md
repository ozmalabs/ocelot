# RESULTS — block 177000-177999: TWO EYES SUPER-RESOLVE ON THE REAL 2-D az×el RETINA (offset ESTIMATED, per-row SEPARABLE)

Closes Rung 5's largest remaining caveat. Rung 5 (175000) and Rung 5b (176000)
proved two-eye super-resolution — and offset ESTIMATION from the eyes' own data —
on the photon eye's **1-D azimuth strip**. `VISION_TWO_EYES_REGISTRATION_RESULTS.
md` §6 named the open item verbatim: *"a 2-D flat wall is the same estimator per
elevation row (separable), noted not run."* **Now run, on the real 2-D az×el
retina.** All 12 pre-registered criteria PASS.

Pre-registered ALONE before any number in `VISION_TWO_EYES_2D_PREREG.md`
(`SEED CLAIM 177000-177999: CLEAN`). Measured by
`scripts/two_eye_superres_2d_measure.py`, gated by
`tests/test_two_eyes_2d_migrated.py` (9/9). Raw:
`results/two_eye_superres_2d.json`. Engine `source_match = shared` (no Rust
built; canonical `.so` byte-unchanged).

## §1 — THE SETUP

Two REAL 2-D `GraphEye`s (`retina_2d=True`, the az×el receptor SHEET, tasks
186/188) view ONE flat 2-D textured wall: N=8 azimuth receptors (period P=8), 6
textured elevation rows + 1 flat row. Each textured row carries well-sampled
anchors k=1,2,3 (below single-Nyquist 4) that DOMINATE plus a MODEST supra-Nyquist
target k0=6 (single-Nyquist 4 < 6 < fused-Nyquist 8) that ALIASES in one eye — and
each row has its OWN random phases (⇒ 6 genuinely independent registration
problems). Eye B sits at a real sub-receptor AZIMUTH offset δ_true=0.5 the kernel
is NOT told (one rigid displacement, same every row). Per elevation row: register
via the UNCHANGED Rung-5b cross-frame-phase estimator, fuse via the UNCHANGED
Rung-5 `multilook_superres` kernel.

## §2 — THE HEADLINE RESULTS

### Per elevation row (the SAME 1-D estimator + fuser, independently)

| row | δ_est | reg err | gain fused/single | k0 relerr single→fused |
|---|---|---|---|---|
| 0 | +0.5000 | 0.0000 | **805.3×** | 1.000 → 0.010 |
| 1 | +0.4800 | 0.0200 | **4.44×** | 1.000 → 0.020 |
| 2 | +0.4900 | 0.0100 | **14.27×** | 1.000 → 0.027 |
| 3 | +0.5000 | 0.0000 | **569.0×** | 1.000 → 0.019 |
| 4 | +0.4900 | 0.0100 | **21.98×** | 1.000 → 0.019 |
| 5 | +0.5100 | 0.0100 | **18.77×** | 1.000 → 0.008 |
| 6 (FLAT) | +0.0000 | — | — | AC std **0.00e+00** |

### HEADLINE 2 — SEPARABILITY (the real claim)

Per-row δ_est = **[0.50, 0.48, 0.49, 0.50, 0.49, 0.51]**. Six independent 1-D
estimates of one rigid 2-D offset:

- **Row-to-row spread (max−min) = 0.0300** (≤ 0.05). ✅
- **Row-to-row std = 0.0096** (≤ 0.03). ✅
- **Max per-row registration error = 0.0200** (≤ 0.05, H1). ✅

The per-row estimates AGREE with the single true offset (0.5) and with each other.
**The 2-D registration genuinely decomposes into independent per-row 1-D
estimates — separability, measured, not a fluke of one row.**

### HEADLINE 1 — super-res HOLDS in 2-D under the estimate (H2)

- **Aggregate 2-D field gain = 15.26×** (Σ err_single / Σ err_fused, > 4). ✅
- **Every textured row beats single by > 4×** (min 4.44×). ✅
- **k0 resolved fused (max relerr 0.027 < 0.25) vs aliased single (1.000 >
  0.60)** — a single 2-D eye literally cannot represent the supra-Nyquist
  harmonic; two offset eyes de-alias it. ✅

## §3 — THE CONTROLS (all able-to-fail, all held)

- **C1 — perturbed offset degrades (load-bearing):** feeding δ_est ± 0.25 to the
  fusion degrades EVERY row by **≥ 105.7×** (min over rows/signs; ≥ 2×). ✅ The
  win is NOT offset-agnostic — the estimate carries it, in 2-D.
- **C2 — zero-offset falsifier (2-D):** two IDENTICAL 2-D eyes (δ_true=0) → every
  row |δ_est| = **0.0000** (≤ 0.02), per-row gain ∈ **[1.000, 1.000]** (⊂
  [0.8, 1.25]). ✅ No new distinct positions ⇒ no super-resolution, exactly as
  Rung 5 — now shown row-by-row in 2-D.
- **C3 — single-eye 2-D baseline:** the reference arm in every row above.
- **C4 — no-texture (flat) row fabricates no detail:** the flat row's fused
  reconstruction has AC std **0.00e+00** (≤ 1e-4) and δ_est **exactly 0** (dead
  DFT bins ⇒ no phase to read). ✅ Honest null — the fusion does not hallucinate
  texture where there is none, even sitting beside 6 super-resolving rows in the
  SAME 2-D field.

## §4 — What is graph-native / what is Python (architecture rule)

- **The 2-D retina + fusion are graph-native and UNCHANGED.** The 2-D az×el
  receptor sheet runs the SAME `photon_transduce_onset` kernel Rungs 1-4 use; the
  gate proves its transduced activation is **byte-identical** to the 1-D
  `transduce` model (`test_2d_retina_transduction_byte_matches_1d_model`, max err
  0.0). The fusion is the Rung-5 `multilook_superres` Rust CognitiveTask +
  `retinal_mint_superres` rule (`seeds/retinal_superres.json`), UNCHANGED. NO new
  DSL Term, NO new CognitiveTask kind, NO Rust build.
- **Registration is the blessed mechanical numpy SENSOR** (`two_eye_register.
  estimate_offset_phase`, UNCHANGED) — reads only the two rows' activations, emits
  an integer finer-unit offset. NO agent decision, NO graph-state conditional.
- **The new adapter `domains/two_eye_superres_2d.py` is mechanical I/O ONLY:**
  build two 2-D `GraphEye`s, sample the wall, read per-cell activations, LOOP the
  proven 1-D estimator + fuser over rows, read the fields. It is a loop over
  proven pieces — no `if` over graph state, no decision.

## §5 — The frame/continuum invariant (BASE-AS-DIMENSION), audited clean

Each row's emitted `bt` is a FINER-UNIT INTEGER (the stepped observable). δ_est =
bt/S (S=100) is a cross-frame quantity — a spectral PHASE, the map
`Hom(frame_A, frame_B)` — so it MAY be non-integer, and is never written into any
in-frame coordinate. The 2-D case adds no new floats-in-a-frame: elevation is a
pure integer row INDEX (the separable dimension), azimuth in-frame coordinates
stay integer, and the only continuum quantity is the per-row cross-frame phase.
Separability is itself an instance of the invariant: the 2-D between-frames map
FACTORS through independent per-row 1-D maps.

## §6 — Discipline

- **§9 default-OFF / new files only:** additive — NEW files only
  (`domains/two_eye_superres_2d.py`, `scripts/two_eye_superres_2d_measure.py`, the
  gate, the prereg, this doc, the results JSON). `git diff --stat` against base
  `44fe391510` touches NO existing tracked file (collision-free with the parallel
  block-178000 rung). Rung-5 gate `test_vision_two_eyes_migrated.py` STAYS 7/7;
  Rung-5b gate `test_two_eyes_registration_migrated.py` STAYS 10/10; the Rung-5
  fuser OFF gate is still silent (`test_rung5_fuser_off_gate_still_silent`).
- **Oracle** `bash scripts/rung7_vision_bench.sh`: **0 failed, BEFORE == AFTER**
  (additive / no Rust rebuilt; my new gate is not in the bench list).
- **Provenance (§10):** `source_match = shared` (this worktree carries no local
  `.so`; the engine resolves to the canonical source-identical `.so`, whose Rust
  is byte-identical to this tree at the base commit — no Rust was built). The gate
  asserts `source_match in ("own","shared")`, never a pinned hash. Canonical
  `_native.abi3.so` md5 `417f667716d71ed7d98bae5df25fe9df` UNCHANGED before/after.
- **NO TIMING CLAIM.**

## §7 — Honest residuals

- **Azimuth-only offset by design.** The rigid displacement is in azimuth; the
  elevation offset is zero. This is EXACTLY the separability claim — the 1-D
  azimuth estimator run independently per elevation row. A full 2-D (az+el)
  displacement would additionally need a per-COLUMN elevation estimate (the same
  estimator, transposed); that is a separate, symmetric measurement, not bolted on
  here.
- **Modest MSE magnitudes on the conservative texture.** As in Rung 5b, k0 is kept
  MODEST (A=12) so the well-sampled anchors dominate; the phase estimator reads δ
  from the clean bins {1,3} ONLY and is therefore immune to k0's amplitude — a
  k0-dominant wall would give a larger gain with equally accurate registration
  (a new measurement, own prereg). The per-row gains that vary 4.4×–805× track the
  per-row registration error (rows landing δ_est exactly on 0.50 super-resolve
  near-perfectly), NOT any change in the mechanism.
- **Synthetic-clean magnitudes.** The mechanism (2-D super-res under an estimated,
  separable offset), not the headline number, is the result; a benchmark on real
  2-D textures is a separate measurement.
- **Sub-receptor offset assumed** (no phase unwrapping), inherited from Rung 5b.

## §8 — Proposed VISION_PROTOCOL.md ledger row

| **177000–177999 (two eyes super-resolve on the REAL 2-D az×el retina, offset ESTIMATED, per-row SEPARABLE; NO Rust — a mechanical adapter `domains/two_eye_superres_2d.py` that LOOPS the proven Rung-5b estimator + Rung-5 fuser over elevation rows, DEFAULT OFF / new files only)** | **THE 2-D PROBLEM DECOMPOSES INTO INDEPENDENT ROWS — closes Rung 5's last caveat (1-D strip → real 2-D retina).** Two low-res 2-D photon eyes offset by a real sub-receptor AZIMUTH amount the kernel is NOT told, viewing ONE flat 2-D textured wall. Per elevation row: estimate the offset (cross-frame phase, non-aliased bins {1,3}) → fuse (`multilook_superres`). **SEPARABILITY (the real claim):** per-row δ_est = [0.50,0.48,0.49,0.50,0.49,0.51], spread **0.030** / std **0.0096** (both bounded), max reg err **0.020** — six independent 1-D estimates of one rigid offset AGREE. **H2 super-res holds in 2-D:** aggregate field gain **15.26×** (>4), every row >4× (min **4.44×**), k0 relerr fused **0.027** vs single **1.000**. **C1** perturbed offset degrades every row **≥105.7×**; **C2** zero-offset → every row δ_est **0.0000**, gain **1.000×** (Rung-5 falsifier holds in 2-D); **C4** a flat row fabricates NO detail (fused AC std **0.00e+00**, δ_est 0) beside 6 super-resolving rows in ONE field. 2-D retina transduction byte-identical to the 1-D model (max err 0.0); fusion + registration graph-native/UNCHANGED (no Rust, no new Term/kind). §9 byte-identity — new files only, Rung-5 gate 7/7, Rung-5b gate 10/10, OFF gate silent. `source_match=shared` (no Rust built; canonical `.so` md5 unchanged); oracle `rung7_vision_bench.sh` **0 failed BEFORE == AFTER**; gate `test_two_eyes_2d_migrated` **9/9**; `SEED CLAIM 177000-177999 CLEAN`. NO TIMING CLAIM. Raw: `results/two_eye_superres_2d.json`; `VISION_TWO_EYES_2D_RESULTS.md`. |
