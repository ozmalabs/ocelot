# PREREG — block 177000-177999: TWO EYES SUPER-RESOLVE ON THE REAL 2-D az×el RETINA (offset ESTIMATED, per-row SEPARABLE)

Pre-registered BEFORE any measurement. Committed ALONE (this file only).
`SEED CLAIM 177000-177999: CLEAN -- no collision DETECTED.`

## The claim

Rung 5 (block 175000, `multilook_superres` fusion) and Rung 5b (block 176000,
the CROSS-FRAME-PHASE offset estimator `domains/two_eye_register.py`) both proved
two-eye super-resolution on the photon eye's **1-D azimuth strip**. The 2-D az×el
retina already LANDED (`GraphEye(context={"retina_2d": True})`, tasks 186/188,
`seeds/retinal_*_2d.json`). This rung closes Rung 5's largest remaining caveat —
noted verbatim in `VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6: *"a 2-D flat wall
is the same estimator per elevation row (separable), noted not run."* Now run.

Two low-res 2-D photon eyes, eye B offset from eye A by a real sub-receptor
azimuth amount **δ_true = 0.5 receptor** that the fusion/registration kernels are
NOT told, both viewing ONE flat 2-D textured wall. For EACH elevation row
independently: estimate the row's azimuth offset via the PROVEN Rung-5b
`estimate_offset_phase` (cross-frame phase on the non-aliased bins {1,3}), then
fuse that row via the UNCHANGED Rung-5 `multilook_superres` kernel. Assemble the
2-D fused field.

**HEADLINE 1 (super-res holds in 2-D under the ESTIMATE):** the 2-D fused field
recovers a supra-Nyquist azimuth harmonic k0=6 (single-eye Nyquist 4 < 6 <
fused-Nyquist 8) that NEITHER 2-D eye represents alone.

**HEADLINE 2 (SEPARABILITY — the real claim):** the per-row ESTIMATED offsets
all agree with the single true 2-D offset. The 2-D registration genuinely
decomposes into independent per-row 1-D estimates — not a fluke of one row.

## Fixed setup (locked before running)

- Engine: reuse the canonical `substrate_rs`; **NO Rust built, NO new Term/kind**
  (aim). Registration = the UNCHANGED `estimate_offset_phase`; fusion = the
  UNCHANGED `SuperResFuser`/`multilook_superres`. Only NEW files, DEFAULT OFF.
- 2-D wall texture, period P = N = 8 azimuth receptors, `n_el = 6` textured rows.
  Per row r, luminance `T(x, r) = 120 + 55·cos(2π·1·x/P + φ₁ᵣ) + 40·cos(2π·2·x/P
  + φ₂ᵣ) + 30·cos(2π·3·x/P + φ₃ᵣ) + 12·cos(2π·6·x/P + φ₆ᵣ)`, with per-row random
  phases φₖᵣ drawn from `np.random.default_rng(177000)`. The k=1,2,3 anchors are
  well-sampled (below single-Nyquist 4); k0=6 is the supra-Nyquist target that
  ALIASES onto bin 2 in one eye. DIFFERENT phases per row ⇒ 6 genuinely
  independent registration problems.
- Two REAL 2-D `GraphEye`s (`retina_2d=True`, `adapt_rate=0.0`); eye A samples
  column i at azimuth position i, eye B at i + δ_true (same δ_true every row — one
  rigid azimuth displacement). Photon counts `round(T(x, r))`, transduced by the
  graph kernel. The kernel is handed only eye B's ACTIVATIONS, never its true
  positions. n_fine = 64, ridge = 1e-6, S = 100 (declared §13 residual).
- Per-row `k_max = supported_nyquist(positions)` (the existing mechanical count).

## Pre-registered PASS criteria (frozen)

**H1 — registration accurate (per row):**
- Every textured row: `|δ_est[r] − 0.5| ≤ 0.05`.

**SEPARABILITY (headline 2 — the load-bearing claim):**
- Row-to-row spread `max(δ_est) − min(δ_est) ≤ 0.05` receptor.
- Row-to-row `std(δ_est) ≤ 0.03` receptor.
  (The per-row estimates agree ⇒ the 2-D problem decomposes into independent
  rows.)

**H2 — 2-D super-res holds under the estimated offset:**
- Aggregate 2-D field gain `Σᵣ err_single[r] / Σᵣ err_fused[r] > 4.0`.
- Every textured row: per-row gain `err_single[r] / err_fused[r] > 4.0`.
- Every textured row: k0 relerr `fused[r] < 0.25` AND `single[r] > 0.60`
  (a single 2-D eye literally cannot represent k0 — it aliases).

**C1 — perturbed offset degrades (load-bearing, per row):**
- Every textured row, both signs: `err_fused(δ_est ± 0.25)[r] ≥ 2.0 ×
  err_fused(δ_est)[r]`.

**C2 — zero-offset falsifier in 2-D (per row):**
- Eye B at TRUE offset 0 (two identical 2-D eyes): every row `|δ_est[r]| ≤ 0.02`
  AND per-row gain `∈ [0.8, 1.25]` (no new distinct positions ⇒ no super-res —
  the Rung-5 falsifier holds in 2-D).

**C3 — single-eye 2-D baseline:** reported (the reference arm above).

**C4 — no-texture (flat) row must not fabricate detail:**
- A perfectly flat row (all harmonic amplitudes 0, constant luminance): the fused
  2-D reconstruction for that row has AC standard deviation ≤ 1e-4 (essentially
  constant — no fabricated texture), and its estimated offset is exactly 0 (no
  phase to read from dead bins). Honest null.

**ALL of H1 + SEPARABILITY + H2 + C1 + C2 + C4 must pass.**

## Architecture / discipline (frozen)

- NO agent decisions in Python. The registration is the blessed mechanical numpy
  SENSOR (`two_eye_register`, unchanged); the fusion is the graph-native
  `multilook_superres` kernel + rule (unchanged). The new adapter
  (`domains/two_eye_superres_2d.py`) does mechanical I/O ONLY: build two 2-D
  `GraphEye`s, sample the wall, read per-cell activations, loop the PROVEN 1-D
  estimator + fuser over rows, read the fields, score. No `if` over graph state.
- Frame/continuum invariant: the emitted per-row `bt` is a FINER-UNIT INTEGER
  (stepped observable); `δ_est = bt/S` is a cross-frame map (allowed non-integer,
  never written as an in-frame coordinate). Same as Rung 5b.
- §9 default-OFF / byte-identity: NEW FILES ONLY. `git diff --stat` against base
  `44fe391510` touches NO existing tracked file. Rung-5 gate
  `test_vision_two_eyes_migrated.py` 7/7 and Rung-5b
  `test_two_eyes_registration_migrated.py` 10/10 STAY green.
- Oracle `bash scripts/rung7_vision_bench.sh`: 0 failed, BEFORE == AFTER.
- Provenance §10: `source_match ∈ ("own","shared")`, never a pinned hash. NO Rust
  built ⇒ canonical `.so` md5 unchanged (reported before/after).
- NO TIMING CLAIM.
- Gate: `tests/test_two_eyes_2d_migrated.py`.

## What would falsify

- Per-row offsets that DISAGREE (spread > 0.05) ⇒ the 2-D problem does NOT
  decompose per row (separability false).
- Any textured row where fusion does NOT beat single by > 4× ⇒ super-res does not
  hold in 2-D under the estimate.
- The flat row fabricating AC energy ⇒ the fusion hallucinates detail from no
  texture.
- Perturbing the estimate NOT degrading ⇒ the win is offset-agnostic (the
  estimate is not carrying it).
