# PREREG — block 178000-178999: TWO EYES, k0-DOMINANT WALL — DOES THE ESTIMATED-OFFSET GAIN APPROACH THE KNOWN-OFFSET CEILING?

**Committed ALONE, before any number.** Seed block **178000–178999**
(`python3 scripts/seed_claim.py 178000 178999` → `SEED CLAIM 178000-178999:
CLEAN -- no collision DETECTED`). NO Rust, NO new Term — a pure measurement
rung reusing the UNCHANGED Rung-5b estimator (`domains/two_eye_register.
estimate_offset_phase`) and the UNCHANGED Rung-5 `multilook_superres` fusion.
Only the TEXTURE (the k0 amplitude A) is varied, and the results are MEASURED.

## The claim under test (the supervisor's recorded prediction)

Rung 5b (block 176000, `VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6) super-
resolved two eyes at an ESTIMATED sub-receptor offset, but the MSE gain was only
**19.7×** vs a **683×** known-offset reference on the SAME texture — because the
prereg texture kept the supra-Nyquist harmonic k0 MODEST (amplitude A≈12). The
supervisor put on the record:

> *"the phase estimator reads δ only from the CLEAN non-aliased bins {1,3} and
> is therefore IMMUNE to k0's amplitude — a k0-DOMINANT wall would give BOTH
> accurate registration AND a large gain … closing the 19.7× vs 683× gap."*

This rung TESTS that prediction and IS ABLE TO FALSIFY IT.

## The measurement

Flat textured wall, N=8, δ_true=0.5, WELL-SAMPLED anchors **k=1 A=55 / k=2 A=40
/ k=3 A=30** (the registration anchors, all below single-Nyquist N/2=4, phases
fixed from seed 178000), plus the supra-Nyquist target **k0=6** (single-Nyquist
4 < 6 < fused-Nyquist 8) whose amplitude **A is SWEPT**:

    A ∈ { 6, 12, 24, 48, 96, 192 }

spanning below the modest 176000 case (A=12) up to k0-DOMINANT (A=192 ≫ the
anchor sum 125). The eye is the REAL nonlinear eye — Naka-Rushton transduction,
integer photon quantisation, and the physical floor at zero photons — exactly as
Rung 5/5b (no linearisation). Anchor phases are drawn ONCE from seed 178000 and
held FIXED across the whole sweep, so only A varies (the amplitude effect is
isolated).

For each A: build the texture; sample eye A at offset 0 and eye B at the TRUE
offset 0.5 (DISCARDING eye B's true positions, keeping only its activations);
register with the UNCHANGED `estimate_offset_phase` (clean bins {1,3}, k0=6 folds
onto excluded bin 2); build eye-B positions from δ_est; fuse (estimated, known,
perturbed ±0.25) through the UNCHANGED `multilook_superres`; score MSE vs the
dense true field. Anchor A_lo=12 (the 5b modest point), A_hi=192 (k0-dominant).

## PRE-REGISTERED PASS / FAIL THRESHOLDS (fixed here, before running)

The overall PREDICTION is **CONFIRMED** iff BOTH parts pass; **FALSIFIED**
otherwise, with the failing clause named.

### Part 1 — IMMUNITY: registration accuracy does NOT degrade as k0 grows
- **P1a:** `reg_err(A) ≤ 0.05` for **ALL** A in the sweep (the Rung-5b H1 bar).
- **P1b:** `reg_err(A_hi) ≤ reg_err(A_lo) + 0.02` (no systematic growth with A).

FALSIFIED (part 1) if P1a or P1b fails — i.e. registration error GROWS with A.

### Part 2 — GAIN RISES TOWARD THE CEILING: estimated gain closes the gap
- **P2a:** `gain_est(A_hi) ≥ 3 × gain_est(A_lo)` (a real rise off the modest
  ~19.7× — the estimated-offset gain is not pinned).
- **P2b:** `gain_est(A_hi) ≥ 0.10 × gain_known(A_hi)` (the estimated gain reaches
  within one order of magnitude of the known-offset ceiling — the 176000 point
  was 19.7/683 = **0.029** of the ceiling; the gap must close to ≥ 0.10).

FALSIFIED (part 2) if P2a fails (gain stays pinned near 19.7× and does NOT rise
with A) OR P2b fails (estimated gain stays far below the ceiling at high A).

### Controls (must hold regardless — else the measurement is not load-bearing)
- **C_ceiling:** `gain_est(A) ≤ 2 × gain_known(A)` for all A. The known-offset
  gain is the CEILING; the estimate must approach it, never exceed it.
- **C_perturb:** at A_hi, `min(pert_hi, pert_lo) / fused_est ≥ 2.0`. A
  deliberately-wrong offset (±0.25) still degrades the fusion at high A — the
  estimate stays load-bearing.
- **C_zero:** `0.8 ≤ zero_gain(A) ≤ 1.25` for **ALL** A. Two identical eyes
  (δ_true=0) give NO super-resolution at every A — the Rung-5 falsifier holds
  regardless of k0.

## Reporting commitment

Report the FULL curves — `reg_err(A)`, `gain_est(A)`, `gain_known(A)`,
`zero_gain(A)`, and the perturbed degradation at each A — not just the endpoints.
State CONFIRMED or FALSIFIED against these exact thresholds, naming the clause.

## Discipline

NEW files only (additive; `git diff --stat` vs the base shows only new files).
The Rung-5/5b estimator and the `multilook_superres` fusion are BYTE-UNCHANGED —
this rung imports them, it edits nothing. NO Rust built (`source_match ∈
{own,shared}`; canonical `.so` md5 unchanged BEFORE==AFTER). Oracle
`bash scripts/rung7_vision_bench.sh` = 0 failed, BEFORE==AFTER. NO TIMING CLAIM.
Gate: `tests/test_two_eyes_k0dom_migrated.py`, reading the measured curves and
asserting the pre-registered verdict at the grain the mechanism decides.
