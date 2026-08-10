# RUNG 8D — PRE-REGISTRATION: THE CALIBRATION 8C OWES, RUN PROSPECTIVELY

*Written and **COMMITTED BEFORE THE CONFIRMATION RUN**. §3 says COMMITTED, and
rung 8C's own disclosure — "**'written before' is not 'committed before'**" — is
the defect this file exists to repair. The git timestamp of this commit precedes
the confirmation run's log; both are in the results file.*

**Engine `a06584eaa362`** @ `<this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`
— **`own` build**, built by `scripts/engine_build.sh` in THIS worktree (§11.5).
**Base commit `de5f96b8`** (rebased onto the tip; 8C's `d4bb1781` is an ancestor).
**This rung adds NO Rust.** `tests/test_engine_provenance_migrated.py` 7/7 green.

---

## 0. WHAT IS ALREADY DONE, AND WHY IT IS NOT THIS PRE-REGISTRATION

The §1/§2 **calibration and instrument diagnosis** below ran FIRST, by design
(the protocol's own order: the gates decide whether a confirmatory run may
happen at all), on **already-burned seeds only (0–13, 3000)**. They test no
hypothesis and burn nothing:

| script | what it establishes | seeds |
|---|---|---|
| `rung8d_percell_audit.py` | per-CELL aliveness + OSI; `n_dead` | 0 (burned) |
| `rung8d_drive_match_pilot.py` | the DRIVE-MATCHED control | 0 (burned) |
| `rung8d_theta_convergence.py` | §2: does theta settle? | 0 (burned) |
| `rung8d_scale_invariance.py` | is the readout scale-invariant? | 0 (burned) |
| `rung8d_pilot_variance.py` | §3.3 pilot -> fixes `n` | 0–13 (burned) |

**Their findings are inputs to this pre-registration and are stated in §5 as
provisos, not as results to be re-confirmed.**

---

## 1. HYPOTHESIS (two-sided)

**H_CAL — the ensemble-transfer readout fix.** Settling rung 6's OWN per-cell
EMA theta (`oo_sunit_adapt_theta`, unchanged rule, unchanged constants,
unchanged placement) on the **ensemble being RESPONDED TO** (the probe's
interleaved gratings) rather than the **formative** ensemble (waves) makes the
**composed** (rung 7 retina + rung 6 cortex) probe pass PROTOCOL §1's
calibration on **fresh seeds it has never seen**.

**Two-sided, and the negative direction is live:** rung 8C measured this on
**ONE seed (0)**. §4 is explicit that the **unit of analysis is the SEED**, so
8C's result is `n = 1` and its across-seed behaviour is **unknown**. This rung's
own pilot has since measured the FLOOR's per-seed **sd = 0.1091** — **1.8× the
SESOI (0.0595)** — so a single seed is a draw from a wide distribution and
**8C's 0.2304 could have been a lucky one.**

**This is §5-compliant.** §5 forbids changing a measure to **rescue** a failure.
Rung 8 §H named this exact step in advance and required precisely this file:

> *"Fixing theta (e.g. **adapting it to the probe ensemble**...) is a **new
> hypothesis requiring its own prospective pre-registration** (PROTOCOL §5)."*

**The ordering hazard 8C disclosed against itself is REAL and I inherit it.** 8C
ran its theta sweep first, saw the window at ~2.1, and only then measured the
rule landing at 2.168 — it knew the target before measuring the rule reach it.
**I cannot un-know that.** What I can do, and what this file is, is state the
prediction on **seeds nobody has measured** before looking. That is the only
form of prospectivity still available here, and it is weaker than if 8C had
written this file first. **Recorded as a limitation, not argued away.**

## 2. THE STATISTIC, EXACTLY

Per **seed** (the unit of analysis, §4), on the **composed/lateral** pathway,
theta settled on the probe for **2000 steps** (declared here in advance; see
§5 proviso 3), weights frozen, theta then PINNED:

    IDEAL_s = mean over the seed's 6 cells of osi(tuning curve), ideal split-Gabor
    FLOOR_s = mean over the seed's 6 cells of osi(tuning curve), untrained w0=1.0
    SEP_s   = IDEAL_s - FLOOR_s

Reported as mean ± **95% CI over SEEDS** (t-interval, n−1 df). **Per-arm,
per-cell, per-orientation aliveness is reported for every arm** (§1 clause 4;
`n_dead` = cells alive at 0 of 12 is reported explicitly and separately).

**`peak/base` is NOT read** (§1.1: unbounded, blew up at 1.6×10⁶ and 7.1×10⁷).

## 3. THE GATE (rung 8B's criteria, unchanged, plus §1's fourth clause)

| id | criterion | on the statistic |
|---|---|---|
| **G1** | IDEAL ≥ 0.80 | lower bound of the 95% CI |
| **G2** | FLOOR ≤ 0.50 | **upper** bound of the 95% CI |
| **G3** | SEPARATION ≥ 0.30 | lower bound of the 95% CI |
| **G0** | BOTH arms ALIVE | `n_dead == 0` on every arm, every seed |
| **G4** | weights frozen | `max|dw| == 0.0` exactly, every arm |

**The CI, not the point estimate, must clear each threshold.** That is stricter
than 8C (which read point estimates at n=1) and is the direction §5 permits
without a new pre-registration: **stricter against myself is always allowed.**

## 4. n, FIXED IN ADVANCE BY THE PILOT

Pilot: `rung8d_pilot_variance.py`, **burned seeds 0–13** (rung 8 §5's own pilot
block), n = 14.

| arm | mean | sd (per seed) | min | max |
|---|---|---|---|---|
| IDEAL | 0.9999 | **0.0005** | 0.9980 | 1.0000 |
| FLOOR | 0.2754 | **0.1091** | 0.0620 | 0.4618 |
| SEPARATION | 0.7244 | 0.1092 | 0.5382 | 0.9380 |

The binding criterion is **G2** (the only one with real variance). Margin to
0.50 = 0.2246; sd = 0.1091 ⇒ n ≥ 3 for a 95% CI excluding 0.50.
**I DECLARE n = 8** — above the power requirement, for a usable CI on a
distribution the pilot shows is wide and skewed.

**CONFIRMATORY SEEDS, DECLARED IN ADVANCE: `6100–6107`** (8 seeds), taken from
the ledger's **FREE** list (`6100+`), **never used for anything**, and appended
to the burned-seed ledger in `VISION_PROTOCOL.md` **in the same commit as this
file**. **Seeds 13000–13999 are NOT touched** and remain CLEAN for H1/H2.

*Deviation, declared: §3.3 says the pilot uses already-burned seeds — it does
(0–13). The CONFIRMATION needs seeds never used for anything; 13000–13999 is
H1/H2's block and must not be spent on a calibration, so this rung takes a fresh
block from the FREE list and records it. The confirmatory block for H1/H2 stays
clean, which is the rule's purpose.*

## 5. MY PREDICTION, IN ADVANCE, WITH PROVISOS (§3.7)

**I predict the GATE PASSES on the fresh seeds**: IDEAL CI ≥ 0.99, FLOOR CI
upper bound ≈ 0.35 (well under 0.50), SEPARATION CI ≈ [0.62, 0.82], `n_dead = 0`
everywhere, `max|dw| = 0`. **Rung 8C's headline reproduces prospectively, as a
DISTRIBUTION rather than as its point value 1.0000/0.2304/0.7696.**

**I explicitly do NOT predict 8C's exact floor 0.2304 reproduces**, and it
should not be expected to: the pilot shows FLOOR has sd 0.1091 across seeds.
**8C's specific numbers are a draw, not a constant.** What must reproduce is the
**GATE**, not the digits.

Provisos — each tells me what I did not understand if it breaks:
1. **If any fresh seed's FLOOR > 0.50**, G2 is not robust and 8C's PASS was a
   property of seed 0. (Pilot: 0 of 14 exceeded it; max 0.4618 — **close**.)
2. **If IDEAL varies**, my "exact reference" claim is wrong. (Pilot sd 0.0005.)
3. **Settling duration.** `rung8d_theta_convergence.py` measured that theta
   **never stops fluctuating** (max|dtheta| 0.10–0.54 out to 6400 steps) and the
   FLOOR's OSI wobbles over a range of 0.0630 at steps ≥ 2000, while the IDEAL is
   flat (range 0.0082). **The gate's VERDICT is duration-robust — it passes at
   every checkpoint 400→6400 — but the floor's VALUE is not.** I therefore
   **declare 2000 steps in advance** (8C's, for comparability) and treat the
   floor as a random variable, never as a constant. Duration is NOT my
   independent variable (§1.2), and both arms span it identically.
4. **This calibrates the PROBE ONLY.** It says NOTHING about H1/H2. **My
   prediction there remains H1 NULL** (the wave ensemble is orientation-
   ISOTROPIC; decorrelation removes a redundancy without installing an
   anisotropy), and it is UNAFFECTED by this gate either way.

## 6. DECISION RULE, INCLUDING WHAT A NULL MEANS

- **PASS (all of G0–G4 on the CI)** ⇒ the composed probe is calibrated **as an
  instrument whose floor is a wide random variable**. H1/H2 become askable, and
  their pre-registration MUST power against **FLOOR sd = 0.1091**, not against
  8C's point value.
- **FAIL of G2** ⇒ 8C's calibration was a seed-0 artifact, the composed probe is
  **not** calibrated, **and H1/H2 MUST NOT RUN.** That is a finding: it would
  mean the ensemble-transfer fix is real but insufficient, and it would restore
  rung 8B's "GC after all" as the live option.
- **FAIL of G0** (any dead arm) ⇒ §1.1's trap; gate fails outright.
- **A NULL HERE IS A RESULT, NOT A FAILURE.** It would say: the probe cannot be
  calibrated by ensemble transfer alone, and the arc's blocker is upstream of the
  readout. **No rescue, no tuning, no re-run** (§5, §7). A further attempt needs
  a NEW pre-registration with a NEW mechanism-level hypothesis.
- **Exactly the listed tests. No sweeps. No re-runs.**

## 7. §13 — WHAT FALLS OUT, AND WHAT GOES IN

**This rung introduces NO constant.** No float is chosen: rung 6's `theta_rate`,
`eta`, `oo_wmax` and placement are untouched; no seed is edited; no Rust is
added. The one number that matters — **theta ≈ 2.17** — **FALLS OUT** of the
cell's own EMA of its own drive under the ensemble it responds to.

`n = 8` and the seed block are **procedural declarations**, not model constants;
`n` falls out of the pilot's measured sd, and the 2000-step duration is 8C's,
adopted for comparability and declared in advance.

### §13.1 — COULD THIS DESIGN HAVE PRODUCED THE OPPOSITE RESULT?

**Yes, and the pilot shows exactly how close it came.** G2 requires FLOOR ≤ 0.50;
the pilot's worst seed hit **0.4618**. A block of fresh seeds drawing from the
upper tail would fail G2 outright. Nothing in the design prevents that — the
floor is a **lottery** (§8) and I am declaring the seeds before I see them.

**And the mechanism could have failed at the previous step:** the drive-matched
control (`rung8d_drive_match_pilot.py`) was designed so that a drive-carried
separation would COLLAPSE at matched drive. It did not collapse — but the arm
that would have shown it (A2, ideal scaled UP) **VOIDED ITSELF** by hitting
`oo_wmax` clipping (`max|dw| = 7.5`), exactly as its proviso 2 predicted it
might. **The design's own proviso fired against the design.**

## 8. THE INSTRUMENT DEFECT THIS RUNG FOUND, DECLARED BEFORE THE RUN

*Recorded here so the confirmation cannot be read as if this were unknown.*

**`osi()` reads `argmax` of the tuning curve. On the FLOOR arm that argmax is
decided by FLOAT ROUNDING**, because the tuning curve contains **EXACT TIES
between distinct orientations**:

    cell 0:  tc[30 deg] == tc[150 deg] == 1.057486   (top1-top2 rel. gap 4.2e-16)
             tc[60 deg] == tc[120 deg] == 0.598743

**Measured cause** (`rung8d_scale_invariance.py` + the argmax audit): the
tuning curve is `F0` — a **mean over the 16 probe phases**. At exactly those
orientations where `cos(theta)` or `sin(theta) = ±0.5` (i.e. 30/150 and 60/120),
the per-pixel phase increment is **exactly `2*pi*0.5/4 = pi/4` = 2 of the 16
phase samples**, so a unit translation on the integer grid **IS** a phase shift,
and a phase-AVERAGED statistic is exactly translation-invariant there. The
mirror orientations then tie **exactly**. It is an **ALIASING degeneracy of the
probe's own discretisation** (period 4 × K=16 phases × integer grid × 15° steps)
— not a property of the cortex.

**Consequences, all measured:**
* The readout's algebra is **EXACTLY scale-invariant** (tuning curves scale to
  **5.55e-16** at settle=0, **1.005e-13** at settle=2000 under a 9.51× weight
  scaling) — yet OSI still moves, **because a 1e-13 perturbation flips which
  tied orientation wins**, and the winner's ORTHOGONAL is a different
  orientation with a different value.
* **The IDEAL arm is IMMUNE**: its tuning curve has real gaps (top1−top2
  relative gap 0.15–0.28), so no tie, no lottery — which is why it is 0.9999 ±
  0.0005 across 14 seeds.
* **This is §1.1's disease in a THIRD costume.** §1.1: *"an absence off a
  GUARDED DIVISION is evidence of a LOOKUP, not of a measurement."* Here: **an
  OSI off an ARGMAX over EXACT TIES is evidence of a LOTTERY, not of a
  measurement.**

**I am NOT fixing the measure.** §5 forbids changing a readout to rescue a
number, and the gate PASSES with the current one. A tie-aware OSI (circular
variance; averaging over tied argmaxes; an orientation step co-prime with the
grid) is a **NEW MEASURE requiring its OWN prospective pre-registration**, and it
would change every committed OSI in this arc. **It is named here as the next
rung's business and deliberately not done in this one.**

**What it means for H1/H2, and this is the operative consequence:** the FLOOR is
a **wide random variable (sd 0.1091 ≈ 1.8× SESOI)**, not the point value 8C
reported. Any H1 design that compares a trained arm against an **inherited**
floor, or against a floor measured on **one seed**, is measuring the lottery.
H1 must (a) measure its floor **in-run, per arm, per seed**, (b) use the SEED as
the unit, and (c) be powered against **sd = 0.1091**.
