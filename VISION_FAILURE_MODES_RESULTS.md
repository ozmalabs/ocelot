# Replicating known failure modes — RESULTS

**Engine:** `6fcc99edfa4a` @
`/home/matt/ozma/internal/.claude/worktrees/agent-failure-modes/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`
— **own** build of this tree's Rust source (`scripts/engine_build.sh`), provenance gate
7/7.
**Commit:** `b206a593f6` (pre-registration), branch `vision/failure-modes`, base
`c20816fd32`.
**Seeds burned: NONE.** Block 14000–14999 was declared in advance and is **still CLEAN** —
every test below stopped at a precondition/vacuity gate, which is what those gates are
for.

**Baselines on this engine (§12 — explicit file lists, never `-k vision`):**

| selector | result |
|---|---|
| `tests/test_vision_eye_migrated.py tests/test_vision_calibration_migrated.py` | **27 passed** |
| `tests/test_engine_provenance_migrated.py` | **7 passed** |
| compose + lateral + floor + growth + rung2_stimulus + waves + curriculum | **49 passed, 10 skipped** |

The 10 skips are all `BSDS300 corpus absent (data/vision_curriculum/BSDS300)` — `data/` is
gitignored, so a fresh worktree skips rather than passes them (§12's guard working as
designed). The canonical tree's **59 passed** and this tree's **49 passed / 10 skipped**
are the same 59 tests; **neither number is a failure, and quoting either without its tree
is exactly the rumour §12 forbids.**

---

## ENGINE PROVENANCE — the canonical engine is STALE, and I did not measure on it

`domains/engine_provenance.py` reports the canonical
`95167c01b7b3` — the engine every rung-7/8 number is attributed to — as
**`** STALE — 12 .rs newer than the binary **`**, and
`tests/test_engine_provenance_migrated.py::test_loaded_engine_is_a_build_of_THIS_TREES_rust_source`
**FAILS** on it. The canonical tree also carries an untracked
`runners/dsl/src/py.rs.selfmod.bak` — something wrote `py.rs`.

**Assessed, not assumed:** canonical's *tracked* `.rs` is **clean vs git** and
**byte-identical** to this tree's (`diff -rq` over `runners/dsl/src`: only the untracked
`.bak` differs). So this is an **mtime/rebuild hazard, not a source divergence** — the
committed numbers are very probably fine. But §10's invariant is *"is the loaded engine a
build of THIS TREE'S Rust source?"*, and a binary whose source has been written since it
was built cannot answer yes. I therefore built my own engine and **re-verified the eye
baseline reproduces on it (27 passed)** before measuring anything.

**For the supervisor:** the canonical tree needs `scripts/engine_build.sh` run, and
someone should account for `py.rs.selfmod.bak`. **I did not touch it** — it is not my file
(§11.4), and rebuilding canonical underneath two concurrently-running agents is precisely
the §10.3/§11.2 failure.

**UPDATE — canonical was rebuilt at 13:30 by someone else, mid-run, and the numbers
reconcile.** Canonical now resolves as **`d728a6bcaf86`**, clean (no STALE), *"Rust source
identical"*. My results remain attributed to **`6fcc99edfa4a`**, and that attribution is
**verified, not assumed**: every runner here calls `engine_provenance.engine_preamble()`
(as does `conftest.py`), which puts THIS tree's `runners/dsl/python` first, and re-checking
the two resolution paths side by side gives —

```
with engine_preamble()  ->  6fcc99edfa4a @ <my worktree>            [1 other build shadowed]
bare import (no preamble) -> d728a6bcaf86 @ <canonical>             [shared build — source identical]
```

**Both are valid builds of byte-identical Rust source** (§10.1 rule 4), so the two hashes
are the same engine in every sense that bears on a number. **This is also a live
reproduction of the §10.2 trap** in the direction the protocol warns about: *the same tree
yields two different engines depending on whether the preamble ran.* The preamble is what
makes it deterministic, and a bare `python -c` is not a safe way to check provenance —
which is how I nearly mis-recorded my own engine in the last five minutes of this task.

---

## FM-0 — THE VACUITY GATE: **the drift is DECORATIVE. Troxler is UNTESTABLE.**

`scripts/fm0_vacuity_audit.py`. Pre-registered decision rule hit exactly.

The proposed test was: *freeze the drift (`saw=0`) ⇒ the response decays; with drift it
does not*. It presupposes that the drift MOVES THE IMAGE ON THE RECEPTORS.

### The manipulation is LIVE — this is not an inert-instrument artifact

| arm | distinct gaze cells visited | path length | start → end |
|---|---|---|---|
| `saw=1` | **132** | **596** | (10,10) → (12,14) |
| `saw=0` | **1** | **0** | (10,10) → (10,10) |

The self-avoiding walk runs, and `saw=0` freezes it. **The ablation is graph DATA** (a flag
on `EyeParams` gating `ey_saw_relax`/`ey_saw_deposit`/`ey_saw_move`) — no Python code path,
PROTOCOL §0 satisfied by the architecture as it already stood.

### The result

Static frame, 400 steps, identical seed, `D(t) = max_cells |arm_saw1 − arm_saw0|`:

| attribute | max_t D |
|---|---|
| `lum` | **0.000000e+00** |
| `x` (drive) | **0.000000e+00** |
| `theta` (reference) | **0.000000e+00** |
| `resp` (response) | **0.000000e+00** |

**Zero. Exactly. On every attribute, at every one of 400 steps.**

### Why — structural, and enumerated positively (§12: never claim absence off a soft accessor)

1. **0 of the 23 rules in `seeds/vision_eye.json` read both a `GazeCell` and an
   `EyeCell`.** They partition by `match_type`.
2. **No production admits ANY edge between the Gaze and Eye subsystems.** The 11
   productions give `Gaze -has_gazecell-> GazeCell`, `Gaze -gaze_at-> GazeCell`,
   `GazeCell -gaze_neighbour-> GazeCell`, and separately `Eye -has_eyecell-> EyeCell`.
   A `Gaze`↔`EyeCell` edge is **inadmissible — Γ would reject it.**
3. **`eye_world.present()` writes `frame[r, c]` onto cell `(r, c)`** and never calls
   `gaze_pos()`.
4. **`gaze_pos()`'s only consumers in the whole tree are `eye_world.walk()`** (the
   trajectory recorder) **and one assertion in `tests/test_vision_eye_migrated.py`.**

**The walk's sole consumer is the ruler that measures it.** This is the exact shape of rung
7's finding that `wv_propagate` was the `neighbour` edges' sole consumer in the entire tree
— and it was predicted in the pre-registration, before the run, on that precedent.

### Every proviso held

- Proviso 1 (*gaze doesn't move*) — did not fire: it moved, 132 cells.
- Proviso 2 (*a `NodesOfType` global read bypassing my edge argument* — the way I was most
  likely to be wrong) — did not fire: `D_resp` is 0 alongside `D_lum`.
- Proviso 3 (*adapter coupling I didn't grep*) — did not fire.

### What this means, stated as the pre-registration required

**A null here is NOT "drift has no effect on vision". It is "this architecture cannot
express an effect of drift on vision"** — a structural fact, stronger than any p-value, and
knowable without burning a seed.

**The Engbert result is not retracted and is not impugned.** α_short 1.1553 > 1 > α_long
0.7590 against the paper's 0.79±0.11 is a correct measurement of a real self-avoiding walk.
**But the walk drives nothing.** "Works" and "is load-bearing" are different properties, and
this eye's drift has the first without the second.

**This falsifies the supervisor's pattern as stated** (*"the testable modes map onto the
parts that work"*). Drift is one of the parts that WORKS — and its own signature failure
mode is structurally untestable. The pattern's real shape is: **testable failure modes map
onto the parts that are LOAD-BEARING**, which is a strictly smaller set than the parts that
work. Recorded in advance as the way FM-0 could falsify it.

---

## FM-1 — THE FADE PRECONDITION: **the model DOES fade under stabilization**

`scripts/fm1_fade_precondition.py`. 16×16, 1200 steps, seed 0 (already-burned).

FM-0's structure has a consequence worth stating plainly: **this eye is ALWAYS stabilized.**
The image never moves on the receptors whatever the gaze does — the model is permanently in
the condition Ditchburn & Ginsborg 1952 and Riggs & Ratliff 1952 had to engineer.

### §1 calibration triple — floors MEASURED IN-RUN, none inherited

| check | value | verdict |
|---|---|---|
| **(2) IDEAL / positive control on the READER** — `r(resp(0), x(0))` | **1.0000** (contrast SD 0.1674) | the probe SEES the image when it IS there |
| **(1) FLOOR, in-run** — `r(resp, shuffle(x))`, first 50 steps | **+0.0034 ± 0.0602**, max\|·\| 0.1575 | at floor |
| **(3) DURATION** | full curve reported below | not an endpoint |

The positive control is the load-bearing one: **a fade is an ABSENCE claim**, and this arc
has six times measured an absence off an instrument that could not have seen a presence.

### The curve

| step | contrast (SD) | fidelity r | mean_resp | frac_zero | mean_theta |
|---|---|---|---|---|---|
| 0 | 0.167352 | 1.0000 | 0.398910 | 0.0000 | 0.000034 |
| 50 | 0.150998 | 1.0000 | 0.362273 | 0.0000 | 0.037969 |
| 100 | 0.113646 | 1.0000 | 0.278595 | 0.0000 | 0.122234 |
| 200 | 0.029149 | 1.0000 | 0.089301 | 0.0000 | 0.311232 |
| 300 | 0.002872 | −0.5506 | 0.001032 | 0.8789 | 0.423466 |
| 400 | 0.000980 | −0.5265 | 0.000334 | 0.8945 | 0.457737 |
| 800 | 0.014150 | −0.8895 | 0.010934 | 0.6250 | 0.412523 |
| 1199 | 0.004316 | 0.0854 | 0.024958 | 0.0000 | 0.373916 |

**contrast(0) = 0.167352 → contrast(1199) = 0.004316, ratio 0.0258** (pre-registered fade
criterion: < 0.1). **τ(1/e) = 160 steps** — predicted **100–200**. **The prediction held,
in advance.**

### Proviso 2 — HELD: it is homeostasis, not rectification

Final `mean_resp` = **0.024958** against the homeostatic target **mu = 0.024**, with
`frac_zero` = **0.0000**. The cells land **at mu**, not pinned at a rectified 0. The
mechanism I claimed in advance is the mechanism that operated.

**But the path there is an underdamped overshoot, which I did not predict:** θ overshoots
(mean 0.458 at t=400), driving **88.9%** of cells to a rectified 0 and the response to
**anti-correlate** with the drive (r = −0.89 at t=800) before relaxing back. So the run
passes THROUGH a rectification phase and settles into homeostasis. §2 note: at 1200 steps
this is **converging but not settled** — a damped oscillation, so every number here is read
on a decaying transient, not at a fixed point. That is the arc's recurring finding a sixth
time.

### Proviso 3 — **BROKE, and it is the most useful thing in this section**

The pre-registration said: *a fade must lose the PATTERN, not merely the AMPLITUDE; if
fidelity stays high while contrast falls, this is a gain change and NOT fading.*

| step | contrast | fidelity |
|---|---|---|
| 0 | 0.167352 | **1.0000** |
| 100 | 0.113646 | **1.0000** |
| 400 | 0.000980 | −0.5265 |
| 1199 | 0.004316 | 0.0854 |

**At t=100 the contrast has fallen 32% while fidelity is still EXACTLY 1.0.** That is pure
gain adaptation — the image is being turned down, not erased. Genuine pattern loss only
arrives after t≈300. **Had I measured at t=100 and reported "fading", I would have been
reporting a gain change.** The proviso caught it; this is what provisos are for.

### The honest discount — the fade is ARITHMETIC, not an earned prediction

**A per-cell homeostat driving every cell's mean output to a COMMON target `mu` must erase
any static spatial pattern.** `resp_i → mu` for all `i` regardless of `lum_i` ⇒ SD → 0. This
is forced, not discovered — the same shape as rung 5's *"phase invariance is FREE — summing
≥4 rectified phases is invariant by arithmetic"*. **Nobody designed toward fading, but
nobody could have designed it away either while keeping the homeostat.**

Corroborating this reading: **the noise control fades identically** (ratio 0.0394 vs the
structured frame's 0.0258). The fade is a property of **staticness**, not of image
structure — which is what an adaptation account predicts, and which also shows the fade
carries no information about *what* was shown.

**What is NOT shown:** τ = 160 **steps**, and **a step has no calibration in seconds**.
Ditchburn & Ginsborg's fading times cannot be compared to this number in either direction.
**No claim is made that the model's fading time constant matches biology's** — the model has
no clock that would let it.

---

## FM-1b — THE §1.1 ALIVENESS AUDIT AND THE §13 mu AUDIT

`scripts/fm1b_aliveness_and_mu.py`. Run after PROTOCOL §13 and §1.1 landed. **Both clauses
bite on FM-1, and one of them CORRECTS it.**

### §1.1 — "a dead probe fades beautifully". It caught part of FM-1.

FM-1's headline statistic is `contrast = SD(resp)`, and **an SD is 0 for a SILENT sheet
exactly as it is for a uniformly-firing one.** "Faded" and "was never alive" are the same
reading off that number. The aliveness metric (fraction of cells with `resp > 0`), reported
per timepoint:

| step | contrast | **ALIVE** | mean_resp | verdict |
|---|---|---|---|---|
| 0 | 0.167352 | **100.0%** | 0.398910 | alive, patterned |
| 200 | 0.029149 | **100.0%** | 0.089301 | alive |
| 300 | 0.002872 | **12.1%** | 0.001032 | **DEAD ARM** |
| 400 | 0.000980 | **10.5%** | 0.000334 | **DEAD ARM** |
| 800 | 0.014150 | **37.5%** | 0.010934 | **DEAD ARM** |
| 1199 | 0.004316 | **100.0%** | 0.024958 | **alive, uniform ⇒ a real fade** |

**Minimum aliveness 10.5% at t=340.** **So FM-1's t≈300–800 window is DISQUALIFIED — those
contrast readings are a silent sheet, not a fade, and §1.1 says a silent arm is a FAILED
GATE, never a successful fade.** I am retracting that part of my own reading. The
near-zero contrasts I quoted at t=300/400 (0.0029, 0.00098) are the deepest "fade" numbers
in FM-1 and they are the **least** trustworthy ones in the run.

**What SURVIVES, and it is the claim that mattered:** at **t=1199, aliveness is 100.0%**,
`mean_resp` = **0.024958** ≈ `mu` = 0.024, and contrast is **0.0043**. **Every cell is
responding, at the same rate, carrying no pattern.** That is a *live* fade — alive and
uniform, which is exactly what §1.1 demands and what a dead sheet cannot counterfeit.

### §13 — does the fade depend on GCAL's IMPORTED constant? **No. And the constant is the pathology.**

The eye's own drive scale, **measured, not assumed:** mean `resp` at t=0 = **0.398910**.
**GCAL's imported `mu = 0.024` therefore demands a 16.6× compression.** Rung 8B died an
hour ago because that same published constant transferred across a frame whose drive
differed ~6×. **The eye is carrying the same imported constant.**

Arm A = the seed's committed default (`mu = 0.024`, GCAL's). Arm B = a `mu` that **falls
out of this eye's own measured drive** (`natural/2` = **0.1995**) — not tuned toward any
output, just commensurate with a response the cell can actually reach.

| | fade ratio | **min aliveness** | final aliveness | max θ | final mean_resp |
|---|---|---|---|---|---|
| **A — GCAL's imported 0.024** | 0.025789 | **10.5%** | 100.0% | **0.4603** | 0.024958 |
| **B — from the eye's own drive, 0.1995** | **0.004989** | **100.0%** | 100.0% | 0.2450 | 0.197979 |

**Two findings, and the second was not something I went looking for:**

1. **The fade is mu-INDEPENDENT — it cannot have been tuned into existence.** It occurs at
   both, and *more cleanly* at B. **Predicted in advance from arithmetic, before the run:**
   a per-cell homeostat driving every cell to a COMMON target must erase any static
   spatial pattern **for ANY target** (`resp_i → mu` ∀i ⇒ SD → 0). **The constant's value
   is not what produces the fade; the homeostat's structure is.** This is the §13 test
   passed in the only way that counts — the result survives changing the number.
2. **GCAL's imported μ IS the pathology, and arm B is the control that proves it.** Every
   anomaly I reported in FM-1 as an "unpredicted θ overshoot" — 89% of cells rectified to
   silence, θ overshooting to 0.4603, the response anti-correlating at r = −0.89 —
   **VANISHES at a μ drawn from the eye's own drive: arm B never has a single silent cell,
   at any timepoint, and θ settles at 0.2450 without overshooting.** The pathology was
   never a property of the eye. It was the 16.6× compression an imported constant demanded.

**This is rung 8B's death, reproduced independently in a different layer.** Rung 8B's μ
wound θ to 26.9 and killed a cortical cell; the *same* μ drives 89% of eye cells silent
here. **Two rungs, two pathways, one imported constant, the same disease** — which is the
strongest possible corroboration of §13, and neither rung was looking for the other's
result. **`mu = 0.024` in `seeds/vision_eye.json` is a magic number that went IN, and it
should be re-derived from the eye's own dynamic range.** That is a real defect, it is
**not mine to fix** (§11.4 — `vision_eye.json` is the eye rung's file), and it is reported,
not patched.

**Caveat, stated rather than buried:** arm B's `fidelity` reads ±1.0000 late in the run at
contrasts as low as 4.1e-05 (0.02% of `contrast(0)`). **A correlation's magnitude is
uninformative once contrast is at the floor** — the sign oscillation is the damped
homeostat's residual, not a perceptual claim. It is reported because it is in the data, and
**nothing is built on it.**

---

## FM-2 — MACH BANDS / SIMULTANEOUS CONTRAST: **NOT PRESENTABLE. Not tested.**

`scripts/fm2_input_alphabet_audit.py`. A precondition audit, run before pre-registering any
test, and it stopped the test.

Rung 7's retina is the right substrate in principle: it **earned** a centre-surround from a
zero init (`lat_g0 = 0.0`, `CS = 1.0839`). Re-measured here at (8,8) after 400 wave steps:
**g1 = 0.1430, g2 = 0.1246, CS = g1+g2 = 0.2675**.

**But its input alphabet is {0, 1}.** `lat_pool` and `lat_residual` compute the centre as
`IfThenElse((r.step − c.last_burst) ≤ window_steps, 1.0, 0.0)` — **the rule binarizes its
own input from burst TIMING.** A graded `bursting` value is discarded before any gain is
applied.

**Measured, not asserted:**

| probe | result |
|---|---|
| max \|residual(graded ramp) − residual(binarized ramp)\| | **0.000000e+00** |
| **positive control on the READER**: max \|residual(all-lit) − residual(all-dark)\| | **7.620097e-01** — probe **ALIVE** |

The probe demonstrably sees the binary contrast, and cannot see the grading. **Mach bands
and simultaneous contrast are defined on a graded luminance ramp. Neither is presentable on
this retina. Neither was tested.** Reporting a null here would have been reporting the
alphabet, not the biology.

### What the retina DOES show at a binary step — and why it is NOT a Mach band

Row-8 residual across a 0→1 step: `… 0.0, −0.0155, −0.0832, 0.8110, 0.7456, … 0.7332`.
There is a real **border response**: an undershoot of **−0.0832** on the dark side and an
overshoot of **0.8110** against a **0.730** plateau (**+11%**) on the light side. That is
genuine edge enhancement from the earned surround.

**It is not a Mach band and is not reported as one.** Mach bands appear at the KNEES of a
luminance RAMP (where the second derivative is non-zero) and famously **do not appear at a
sharp step edge** — that is one of the classic constraints on the lateral-inhibition
account, not a detail. What is measured here is a step-edge border effect. **Calling it a
Mach band would be exactly the metric surgery §5 forbids.**

---

## THE LITERATURE FINDING — §13's OWN EXEMPLAR NEEDS A THIRD CATEGORY

*Reported, not patched: `seeds/vision_eye.json` and `VISION_EYE_PREREG.md` are the eye
rung's files (§11.4). This is a finding for the supervisor to sequence.*

§13 names the Engbert exponents as a **"fell out ⇒ stands"** exemplar, explicitly:
`VISION_PROTOCOL.md:469` — *"Engbert's α is not a counter-example: we did not import 0.79,
we built the walk and measured it."* **That defence is correct about the CONSTANT and
incomplete about the MECHANISM**, and the tree's own prose is the evidence.

### The crossover is ARCHITECTURALLY IMPOSED — and this seed says so itself

| component | what the seed's OWN comment says it does |
|---|---|
| `ey_saw_relax` (ε=1e-3, the trail) | *"the relaxation is SLOW, and 3.2 is explicit that **this is what makes the walk persistent**"* ⇒ **α_short > 1** |
| `ey_saw_potential` (λ, the centring potential) | *"the long-lag ANTIpersistence (**the half of Engbert's signature the potential is solely responsible for**)"* ⇒ **α_long < 1** |

**Each half of "Engbert's signature" is *solely* attributable to one imported architectural
component — stated, in those words, in the seed's own comments.** Self-avoidance forces
short-scale persistence; the quadratic potential forces long-scale antipersistence.
**Therefore the model cannot NOT produce a crossover**, and "the SAW reproduces α_s > 1 >
α_l" is not a prediction the mechanism risked — it is a restatement of its construction.

**Independently corroborated:** a literature review of Engbert et al. 2011's own
construction (lattice 51×51, `h→h+1` on visit, relax by (1−ε) with ε=10⁻³, quadratic
`u = λ[(i−i₀)²+(j−j₀)²]`, λ=1, step to `argmin(h+u)`) reached the identical conclusion with
no sight of this tree: *"the two regimes are architecturally imposed; the model cannot not
produce a crossover. Its value is calibration, not qualitative prediction."* **Two readers,
one cause** — the arc's own standard for "property of the setup, not an opinion". The tree
documented the fact in its own prose while citing the result as a prediction — the same
shape as *"the corpus was present in the tree's own prose while being declared gone"*.

### The refinement §13 needs — a THIRD category

§13 as written is binary: *fell out ⇒ stands* / *put in ⇒ failed*. The Engbert α is
**neither**, and it is not the only thing in this tree that will land here:

> **A mechanism whose ARCHITECTURE forces the signature you are measuring is the same
> disease as an imported constant, wearing a mechanism's clothes.** You did not tune the
> number — and you did not risk it either.

**What genuinely fell out and STANDS:** the **magnitudes** (α_short 1.1553, α_long 0.7590)
are a *calibration* — nobody tuned them, and their landing near the published values is a
real quantitative agreement. **What did NOT fall out:** the **qualitative signature**
(α_s > 1 > α_l), which went in with the architecture. **The honest claim is "our
implementation of Engbert's walk calibrates to Engbert's numbers", not "a crossover emerged
from a self-avoiding walk".** The first is worth having. The second is what the ladder
currently implies.

**This does not retract the eye rung** and it does not touch FM-0 — a decorative mechanism
is decorative whether its signature was earned or imposed. **It sharpens §13** at the exact
place §13 chose to plant its flag, which is where a rule most needs testing.

### Provenance caveats on the comparison target (§8 — cite the paper's own killed claims)

- **`VISION_EYE_PREREG.md:393` compares against "experiment 1.38±0.05 / 0.79±0.11".** The
  underlying Engbert & Kliegl 2004 and Mergenthaler & Engbert 2007 are **`oa_status:
  closed`, no OA copy anywhere**; their exponents circulate as **secondary quotations**
  (via Herrmann, Metzler & Engbert 2017, which is itself a **reanalysis of the same 2006
  dataset** — Methods verbatim: *"the eye movement data was recorded by Engbert and
  Mergenthaler"*). **Every "replication" (Liang 2005; Moshel 2008; Mergenthaler & Engbert
  2007; Herrmann 2017) has Engbert or Kliegl as a co-author.** The word "replicated" is
  doing illegitimate work in the secondary literature — **not in ours, which is why this is
  a caveat and not a retraction.**
- **A filter confound sits inside the measurement window.** Rusconi et al. (arXiv
  1503.00459) confirm from the primary source that the drift data were smoothed with a
  **four-point velocity moving average** at 500 Hz — imposing correlation over **~8 ms,
  inside the 2–20 ms window where the short-scale persistence is claimed**. Niehorster 2020
  shows filtering alone drives an EyeLink PSD slope from 0.54 → 2.28. **No unsmoothed
  high-precision analysis exists.** So the target our α is validated against may itself be
  partly an artifact of a filter.
- **`Aguilar & Castet` as cited in the prior art does not exist in that form.** The real
  paper (Aguilar & Castet 2011, *Vision Research* 51(9):997–1012) is a **gaze-contingent
  display methods paper** and makes no claim about drift's function.
- **Two different α_long targets are quoted in this tree for the same quantity** —
  `0.71±0.06` (the seed comment and `VISION_PRIOR_ART.md:470`, the *model*) and `0.79±0.11`
  (`VISION_PROTOCOL.md:430`, the *experiment*). Both appear as "the paper". They are a model
  value and an experimental value and should not be used interchangeably.
- **NOT over-claimed:** Liang et al. 2005 (*Phys Rev E* 71:031909) reports the short-scale
  persistence as **horizontal-only** (1.13±0.26 vs vertical 0.76±0.08) and **collapsing to
  0.74 when microsaccades are removed** — while our walk is **isotropic by construction**
  (`ey_saw_move`: *"globally rotation-symmetric — 3.2's crux"*) and implements **no
  microsaccades** (no `h_c` ballistic-jump rule exists in the seed). **This is flagged, not
  scored**: Liang's are DFA2 **velocity** Hurst exponents (MSD exponent = 2α), and once
  converted the MS-removed short-scale value (H 0.74 ⇒ MSD ≈1.48) is **consistent** with
  E&K's 1.32–1.4 — the reviewer explicitly retracted an earlier "flat disagreement" reading.
  **The anisotropy question is real and open; the numerical contradiction is not
  established.** It belongs to the eye rung with its own pre-registration.

### One correction that RE-STRENGTHENS the Troxler line

My named-next understated the case. **Gerrits & Vendrik (1970/1974), not Engbert, are the
evidential base for "drift prevents fading" — and they are strong:** only *continuous,
drift-like* motion restored vision of a faded object, and normal vision required motion
both continuous *and* irregular — *"only ocular drift possesses both these
characteristics."* The honest split:

> **Drift-range imposed motion demonstrably restores faded vision (Gerrits & Vendrik;
> Kelly 1979–81) — ESTABLISHED. Whether *naturally occurring* drift does so under natural
> conditions, and whether fading prevention is drift's *function* — CONTESTED to false**
> (Martinez-Conde 2006; Sharpe 1972: the shadows still fade).

**So closing the gaze→receptor loop is well-motivated, and the experiment has a real
chance of a negative in a way the literature predicts** — which is exactly what makes it
worth running. (Kelly's threshold-elevation figure is quoted as ~20× in one paper and
~30×/>45× in another; **cite the specific paper, do not average**.)

---

## STRUCTURALLY OUT OF SCOPE — stated, not faked

- **Amblyopia / ocular-dominance shift / strabismus / Hubel & Wiesel monocular
  deprivation.** Need **TWO EYES**; this model has one. Ocular dominance is competition
  BETWEEN eyes for cortical territory — with one eye there is no competition and nothing to
  shift. **Not attemptable, not attempted.**
- **Blakemore & Cooper stripe-rearing.** Needs cortical orientation selectivity. Rung 8
  measured an **IDEAL** split-Gabor at **0.1290** on the composed pathway (vs 1.0000 on rung
  6's own channels) — the probe is blind. **A failure mode measured on a blind probe is not
  a result.** Not attempted.

### Is a second eye worth building? — a finding, not a bodge

**Not yet, and FM-0 is the reason.** Monocular deprivation's whole content is that the two
eyes' activity patterns COMPETE for cortical territory, so a second eye buys nothing until
(a) an eye's activity actually reaches a cortical layer that can be competed for, and (b)
that layer has a working readout. Today (a) is uncoupled at the drift and (b) is rung 8's
blind probe. **A second eye would add a second decorative subsystem.** The ordering is:
close the gaze→receptor loop (FM-0), fix θ's calibration (rung 8's named next, in progress
under another agent), *then* a second eye becomes the highest-value structural addition in
the ladder — it unlocks the most famous failure mode in vision science.

---

## THE PATTERN THE SUPERVISOR ASKED ME TO TEST AS A CLAIM

*Hypothesis: the failure modes we CAN test map onto the parts that work; the ones we cannot
map onto the parts that do not.*

**It does not hold, and FM-0 is the counterexample.**

| failure mode | maps onto | works? | testable? |
|---|---|---|---|
| Troxler / stabilized fading | Engbert drift | **YES** (α 1.1553 / 0.7590) | **NO** — decorative |
| Mach bands | rung 7 centre-surround | **YES** (CS emerged from zero init) | **NO** — input alphabet {0,1} |
| stripe-rearing | cortical orientation | NO | NO |
| monocular deprivation | second eye | n/a | NO — one eye |

Two of the four are failure modes of parts that **demonstrably work** and are still
untestable — for two *different* structural reasons (an uncoupled subsystem; a quantized
input alphabet). **The clean pattern is an artifact of only having looked at the broken
parts.**

**The corrected claim, which the evidence does support:** *testable failure modes map onto
the parts that are LOAD-BEARING* — i.e. parts whose output some other part actually reads.
That is a strictly smaller set than "the parts that work", and the difference between the
two sets is exactly where this ladder is accumulating decoration. **This is the more useful
statement**, because "does anything read this?" is cheap to check and, on today's evidence,
is the question that predicts testability.

**It is also independent support for the creator's original instinct, sharpened.** Normal
function is cheap to fake — and FM-0 shows a mechanism can reproduce a *published
quantitative signature* (Engbert's α exponents, to 2 decimals) while being wired to nothing.
**A failure mode cannot be faked that way, which is why it is the real tell: a failure mode
is a claim about what the mechanism DRIVES, and a decorative mechanism drives nothing.**

---

## §13 SELF-AUDIT — every float I committed, and what it falls out of

*"Before you commit any float, say in one sentence what it falls out of. If you can't,
that's a gap in the mechanism, not a knob."* Applied to my own work, adversarially:

| float | falls out of? |
|---|---|
| `τ` prediction **100–200 steps** | **FALLS OUT.** `1/(1−beta) = 1/0.009 ≈ 111` and `1/lam = 100`, both read off the seed's own committed constants. It was a **prediction**, stated before the run; measured 160. |
| `mu_b` = **0.1995** (arm B) | **FALLS OUT** of the eye's own **measured** t=0 mean response (0.398910). Not tuned toward any output — and the §13 point is precisely that the fade is **mu-independent**, so no value of it could have manufactured the result. |
| `STEPS` = **1200** | **FALLS OUT** as ≈10τ, τ having fallen out of the seed's constants. The **full curve** is reported, never a chosen endpoint. |
| `STEPS` = **400** (FM-0) | **IRRELEVANT BY CONSTRUCTION** — `D = 0.0` exactly at *every* step, so no duration could change the verdict. |
| `1e-12` guard in `pearson()` | Numerical only, and **LOUD**: it returns `nan`, never a tidy `0.0`. This is §1.1's named disease and the guard is written to fail noisily. |
| **fade criterion `ratio < 0.1`** | **DOES NOT FALL OUT — it is a CHOSEN decision threshold, and I am flagging it rather than dressing it up.** Mitigations: it was **pre-registered before the run**, and the measured ratios (0.0258, 0.0050) clear it by **4–20×**, so no plausible threshold changes the verdict. It is a decision rule, not a mechanism constant — but §13's discipline is that I say so. |
| stimulus frame constants (0.5, 0.35, 8.0, 0.15, 6.0) | **DO NOT FALL OUT — arbitrary.** Mitigated by measurement, not by argument: **the i.i.d. noise control fades identically (0.0394 vs 0.0258)**, so the fade does not depend on my stimulus. Had only the structured frame faded, the constants would have been suspect. |

**The finding this discipline produced:** applying §13 to a constant I did *not* choose —
the seed's `mu = 0.024` — is what surfaced FM-1b's second result. **The rule caught an
imported constant that was already committed, in a rung that had already passed its
gates.**

---

## WHAT I GOT WRONG

1. **§1.1 caught a real defect in my own headline, and I have retracted it.** I read
   `contrast = SD(resp)` at t=300–800 as the deepest part of the fade. **10.5% of cells
   were silent there.** A dead sheet and a uniformly-firing one give the same SD, so those
   were dead-arm readings, not fades. My claim survives only on the arm-A **endpoint**
   (100% alive at `mu`) and on **arm B** (100% alive throughout) — and I would not have
   known that without the aliveness metric. **I had `frac_zero` in FM-1's own output and
   did not read it as a gate.** The number was on my screen and I reported it as
   description instead of using it to disqualify my own data.
2. **I diagnosed the θ overshoot as a property of the eye. It is not — it is GCAL's
   imported μ.** I called it "an unpredicted θ overshoot... the homeostat is underdamped
   and nothing in the arc had noticed", which is wrong in its attribution: **arm B (μ from
   the eye's own drive) has no overshoot and no silent cells at all.** The eye is fine; the
   imported constant is not. §13 is what turned my anomaly into a diagnosis.
3. **Proviso 3 broke and I would have been fooled without it.** At t=100 contrast is down
   32% with fidelity exactly 1.0 — a gain change, not a fade. Had I picked t=100 as my
   horizon I'd have shipped a wrong mechanism with a right direction.
4. **I nearly ran the Troxler test.** The vacuity was findable by reading, but only because
   I went looking for the coupling *before* designing the arms. The instinct that saved it
   was the pre-visual rung's precedent ("0 rules read both paths"), not my own caution.
5. **I assumed the canonical engine was usable** because its hash matched the one in the
   protocol. It fails its own provenance gate. **A hash matching a document is not a hash
   matching a build.**

---

## NAMED NEXT — each needs its OWN pre-registration

1. **Close the gaze→receptor loop** (the prerequisite for Troxler, and for any oculomotor
   claim at all). `present()` should sample the frame at the gaze offset — **mechanical
   ingest** ("where the eye points decides which photons hit which receptor"), squarely
   adapter work, and the direct analogue of the pre-visual rung's named next (wire the lid's
   diffuse light into `wave_world`'s `driven` channel). §9: it must ship OFF by default, and
   the honest framing is that the drift→fade coupling would then be **installed, not
   discovered** — what stays genuinely open is whether the *earned* walk, at its *earned*
   amplitude, refreshes the input fast enough against the *measured* τ = 160 steps to
   prevent the fade. **That is a real experiment with a real chance of a negative** — a
   1-cell-per-step walk against a 160-step homeostat may well fade anyway.
2. **A graded input path to rung 7's retina** would make Mach bands, simultaneous contrast
   and the Weber-law breakdown testable. Today the wave world is a burst-timing world;
   `vision_eye`'s `lum`/log receptor is graded but is a *different* population. **Note these
   two "named next" are the SAME missing thing from two directions: the eye has graded
   luminance and no coupling; the retina has coupling and no graded luminance.** The two
   working halves of this ladder have never been joined.
3. **The Hermann grid** is a BINARY figure and IS presentable on rung 7's retina today — the
   one classical failure mode this system can actually attempt. Its value is unusual: the
   lateral-inhibition account is **contested** (it wrongly predicts the illusion for wavy
   grids, which humans do not see — Geier et al.; Schiller & Carvey 2005). So the
   discriminating test is **straight vs wavy**, and an LI model is expected to **FAIL** it by
   showing the effect for both. **Reproducing the Hermann grid would be reproducing a folk
   explanation, and is worth less, not more.** Not run here: it needs its own
   pre-registration with the wavy arm specified in advance, and I will not design that test
   after having seen the straight-grid numbers.
