# RESULTS — block 178000-178999: TWO EYES, k0-DOMINANT WALL — THE PREDICTION IS **FALSIFIED**

Tests the supervisor's recorded Rung-5b prediction
(`VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6): *"the phase estimator reads δ
only from the CLEAN non-aliased bins {1,3} and is therefore IMMUNE to k0's
amplitude — a k0-DOMINANT wall would give BOTH accurate registration AND a large
gain … closing the 19.7× vs 683× gap."*

**Both parts FAIL against the pre-registered thresholds. The prediction is
FALSIFIED.** Registration is NOT amplitude-immune in the real nonlinear eye — it
breaks exactly at k0-dominance — and the estimated gain does NOT rise toward a
large ceiling: it PEAKS at modest-high A then FALLS, and the known-offset ceiling
ITSELF falls at high A. The controls all hold, so the falsification is
load-bearing. A separate finding dissolves the prediction's own premise: the 5b
"gap" is a registration-**precision** (rounding) artifact, not a k0-modesty one.

Pre-registered ALONE in `VISION_TWO_EYES_K0DOM_PREREG.md` (commit `c303c6cc3f`)
before any number. Measured by `scripts/two_eyes_k0dom_measure.py`, gated by
`tests/test_two_eyes_k0dom_migrated.py` (7/7). Raw: `results/two_eye_k0dom.json`.
NO Rust built; NO new Term — the Rung-5b `estimate_offset_phase` and the Rung-5
`multilook_superres` fusion are imported BYTE-UNCHANGED; only the texture's k0
amplitude A is swept.

## §1 — THE MEASURED CURVES (block seed 178000; anchor phases fixed across the sweep)

Flat wall, N=8, δ_true=0.5, fixed anchors k=1 A=55 / k=2 A=40 / k=3 A=30
(all < single-Nyquist 4), k0=6 (4 < 6 < fused-Nyquist 8), A swept. `δ_raw` is the
continuous clean-bin phase read; `δ_est = round(δ_raw·100)/100` is the stepped
observable fed to fusion; `est/ceil = gain_est/gain_known`.

| A | δ_est | δ_raw | reg_err | reg_err_raw | gain_est | gain_known | est/ceil | k0 relerr single→est | zero_gain | perturb (min×) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6   | 0.500 | 0.504 | 0.0000 | 0.0044 | 339.33 | 339.33 | 1.000 | 1.000 → 0.021 | 1.000 | 33253 |
| 12 (A_lo) | 0.500 | 0.504 | 0.0000 | 0.0038 | 565.22 | 565.22 | 1.000 | 1.000 → 0.006 | 1.000 | 15394 |
| 24  | 0.500 | 0.501 | 0.0000 | 0.0008 | **742.04** | **742.04** | 1.000 | 1.000 → 0.002 | 1.000 | 5306 |
| 48  | 0.500 | 0.498 | 0.0000 | 0.0022 | 599.62 | 599.62 | 1.000 | 1.000 → 0.002 | 1.000 | 1288 |
| 96  | 0.500 | 0.499 | 0.0000 | 0.0009 | 297.48 | 297.48 | 1.000 | 1.000 → 0.012 | 1.000 | 277 |
| 192 (A_hi) | 0.440 | 0.439 | **0.0600** | **0.0614** | **13.63** | 16.57 | 0.823 | 1.000 → 0.226 | 1.000 | 3.8 |

## §2 — VERDICT AGAINST THE PRE-REGISTERED THRESHOLDS

### Part 1 — IMMUNITY: **FALSIFIED**
- **P1a** (`reg_err(A) ≤ 0.05` ∀A): **FAIL** — reg_err = 0.060 at A=192 (> 0.05).
- **P1b** (`reg_err(A_hi) ≤ reg_err(A_lo)+0.02`): **FAIL** — 0.060 vs 0.000+0.02.

The continuous phase read (`reg_err_raw`) is amplitude-immune while k0 is
modest — < 0.007 for every A ≤ 96, exactly as the linear shift theorem predicts —
but DRIFTS to 0.061 once k0 dominates (A=192). In the REAL nonlinear eye the
clean bins {1,3} are NOT immune: k0's transduction/clipping distortion products
(frequencies k0±k1 = 5, 7 fold onto bins 3, 1 in the length-8 DFT) leak into the
very bins the estimator reads, and at k0-dominance the leak is large enough to
corrupt δ. The immunity is a property of the *linear* shift theorem the
supervisor invoked; it does not survive the nonlinear eye at the amplitude the
prediction actually targets.

### Part 2 — GAIN RISES TOWARD THE CEILING: **FALSIFIED**
- **P2a** (`gain_est(A_hi) ≥ 3·gain_est(A_lo)`): **FAIL** — 13.6× vs 3·565 = 1696×.
  The gain does the OPPOSITE of rising: it PEAKS at A=24 (742×) and FALLS to
  13.6× at A=192.
- **P2b** (`gain_est(A_hi) ≥ 0.10·gain_known(A_hi)`): PASS (0.823) — but part 2 is
  already falsified by P2a, and P2b passes only because the ceiling itself has
  collapsed to 16.6× (there is nothing left to fall short of).

The known-offset **ceiling is non-monotone**: 339 → 565 → **742** → 600 → 297 →
17 as A grows. Making k0 dominant does NOT open an ever-larger super-resolution
opportunity — it drives the wall into transduction compression and the
zero-photon clip, injecting harmonics ABOVE the fused Nyquist (8) that NEITHER
eye can resolve, so the best achievable fused reconstruction degrades. Both the
single-eye error and the fused error grow with A, and their ratio falls. The
premise "a k0-dominant wall would give a large gain" is wrong at both ends: the
gain does not rise, and the ceiling it would rise toward does not exist at high A.

### Controls — ALL HOLD (the falsification is load-bearing)
- **C_ceiling** (`gain_est ≤ 2·gain_known` ∀A): PASS. At A ≤ 96 the estimate is
  EXACT (δ_est = 0.500), so gain_est == gain_known (est/ceil = 1.000); at A=192 it
  is below the ceiling (0.823). The estimate never beats the known offset.
- **C_perturb** (min perturbed degradation ≥ 2× at A_hi): PASS — 3.8× at A=192
  (and 277×–33253× at lower A). A wrong offset still degrades; the estimate is
  load-bearing wherever it is accurate.
- **C_zero** (`0.8 ≤ zero_gain ≤ 1.25` ∀A): PASS — 1.000 at EVERY A. Two identical
  eyes give NO super-resolution regardless of k0. The Rung-5 falsifier holds.

## §3 — THE PREMISE ITSELF DISSOLVES: the 5b gap is a PRECISION artifact

The prediction was motivated by 5b's 19.7× (estimated) vs 683× (known) gap,
attributed to the "conservative" modest k0. On block seed 178000 that gap **does
not reproduce at all**: at the SAME modest A=12, gain_est == gain_known = 565×
(est/ceil = 1.000), because the estimate rounds to EXACTLY the true offset
(δ_est = 0.500, bt = 50). The 5b gap came from that run's δ_est = 0.49 (a 0.01
rounding penalty at the S=100 grid), not from k0 being modest. The estimated-vs-
known gap is a **registration-precision** effect (how δ_raw lands on the S grid),
and — as this rung shows — k0 amplitude only makes registration WORSE (breaking
it at dominance), never better. There was no k0-modesty gap to close.

## §4 — What is graph-native / what is Python (unchanged from Rung 5/5b)

- **Fusion graph-native and UNCHANGED:** the Rung-5 `multilook_superres` Rust
  CognitiveTask kernel + `retinal_mint_superres` rule via `domains/
  two_eye_superres.py`. NO new Term, NO new kind, NO Rust build.
- **Registration UNCHANGED:** the Rung-5b `estimate_offset_phase` cross-frame-
  phase sensor — imported, not edited.
- **Python is I/O + measurement only:** this rung builds the swept texture, drives
  the sensors, and SCORES. No agent decision, no graph-state conditional.

## §5 — Discipline

- **§9 NEW files only:** `VISION_TWO_EYES_K0DOM_PREREG.md` (committed alone),
  `scripts/two_eyes_k0dom_measure.py`, `tests/test_two_eyes_k0dom_migrated.py`,
  `results/two_eye_k0dom.json`, this doc. `git diff --stat` vs the base shows ONLY
  new files; no existing tracked file touched. The Rung-5/5b paths are
  byte-unchanged (imported).
- **Oracle** `bash scripts/rung7_vision_bench.sh`: **214 passed, 10 skipped, 0
  failed** BEFORE and AFTER — identical (additive; no Rust rebuilt).
- **Provenance (§10):** `source_match = shared` (this worktree carries no local
  `.so`; it resolves the canonical engine, whose Rust source is byte-identical to
  this tree at the base commit — NO Rust built). Canonical `_native.abi3.so` md5
  **417f667716d71ed7d98bae5df25fe9df** UNCHANGED BEFORE == AFTER.
- **NO TIMING CLAIM.**

## §6 — Honest residuals

- **The break lies between A=96 and A=192** (raw err 0.001 → 0.061). The
  pre-registered sweep did not sample inside that octave, so the exact
  amplitude at which immunity crosses 0.05 is not pinned — only that it is crossed
  by A=192 and not by A=96. A finer grid there would locate the knee (not run —
  it would be a post-hoc addition to the pre-registered sweep).
- **Seed-dependence of the exact numbers.** δ_est's rounding (hence the est-vs-
  known gap at modest A) depends on where δ_raw lands on the S=100 grid, which is
  seed-dependent. The QUALITATIVE result is not: immunity holds at modest k0 and
  breaks at dominance (a nonlinear leak that grows with A), and the ceiling is
  non-monotone (clipping is amplitude-driven), on any seed. Only the precise
  break amplitude and the modest-A gap magnitude are seed-specific.
- **Clipping vs pure spectral leakage.** At A=192 the wall clips at the zero-
  photon floor AND compresses through Naka-Rushton; both are k0-amplitude-driven
  nonlinearities and both contribute to the bin-{1,3} contamination and the
  ceiling collapse. This rung does not separate them — both are the real eye, and
  the prediction was about the real eye's response to k0 amplitude.
- **1-D azimuth strip**, as in Rung 5/5b — the separable per-row case; a 2-D wall
  is the same estimator per elevation row, noted not run.

## §7 — Proposed VISION_PROTOCOL.md ledger row

| **178000–178999 (two eyes, k0-DOMINANT wall — TEST the Rung-5b prediction that the phase estimator is IMMUNE to k0 amplitude and a k0-dominant wall closes the 19.7×-vs-683× gap; pure measurement, NO Rust / NO new Term, reuses `estimate_offset_phase` + `multilook_superres` byte-unchanged, sweeps only k0 amplitude A ∈ {6,12,24,48,96,192})** | **PREDICTION FALSIFIED on BOTH parts (pre-registered thresholds).** Part 1 IMMUNITY **FAILS**: the continuous clean-bin phase read is amplitude-immune while k0 is modest (raw δ err < 0.007 ∀ A ≤ 96) but DRIFTS to reg_err **0.060** at k0-dominance (A=192, > the 0.05 H1 bar) — k0's nonlinear distortion products (5,7 fold onto bins 3,1) leak into the estimator's own bins; the linear shift-theorem immunity does NOT survive the real nonlinear eye. Part 2 GAIN-RISES **FAILS**: gain_est does the opposite of rising — it PEAKS at A=24 (**742×**) and FALLS to **13.6×** at A=192; the known-offset CEILING is itself non-monotone (339→742→…→17), because k0-dominance drives clipping/Naka-Rushton compression that injects supra-fused-Nyquist harmonics neither eye resolves. Controls HOLD (load-bearing): C_ceiling gain_est ≤ gain_known ∀A (est==known at A≤96, estimate EXACT); C_perturb 3.8× degrade at A=192; C_zero **1.000×** ∀A (Rung-5 falsifier holds regardless of k0). SECONDARY: the 5b gap is a registration-PRECISION (S-grid rounding) artifact, NOT a k0-modesty one — on seed 178000 gain_est == gain_known = 565× at the modest A=12 (no gap to close). Fusion + estimator UNCHANGED (no Rust, no Term). §9 new files only; `source_match=shared`, canonical `.so` md5 **417f667716d7** untouched; oracle `rung7_vision_bench.sh` **214/10/0 BEFORE == AFTER**; gate `test_two_eyes_k0dom_migrated` **7/7**; `SEED CLAIM 178000-178999 CLEAN`; prereg committed ALONE `c303c6cc3f`. NO TIMING CLAIM. Raw: `results/two_eye_k0dom.json`; `VISION_TWO_EYES_K0DOM_RESULTS.md`. |
