# THE ENDOGENOUS SETPOINT — pre-registration

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Engine
`6fcc99edfa4a`, commit `19f8207b8e` + this branch. Every number below the "PILOT"
heading comes from **already-burned** seeds (0–5; ledger: 0–13 long burned).*

## 0. What this is

JOB 2 of the creator's directive: **"kill the constant. Do NOT tune it."**

`mu = 0.024` is GCAL's target average activity, imported into an unnormalised
frame. It has killed cells in TWO independent layers (rung 8B: θ wound to 26.9,
`rbar` exactly 0; the eye: min aliveness 10.5%, a 16.6× compression of a measured
drive of 0.398910). §13 forbids tuning it. The creator's ruling: **there should
never have been a constant**, and the setpoint must fall out of the endogenous
activity distribution the system measures in itself.

**Where the setpoint falls out of, in one sentence (§13's test):** *the mean
output the cell measured in itself during the pre-visual phase, when its only
input was its own spontaneous retinal waves.*

No fraction, no fudge. (FM-1b's arm B used `natural/2 = 0.1995` — the `/2` is a
free parameter inside something labelled "falls out", and it was measured by the
HOST off the VISUAL input, i.e. the very frame the setpoint is supposed to
precede.) The mechanism removes GCAL's `β = 0.991` from the setpoint path too:
`mu_endo` is a **cumulative mean**, not an EMA, so no constant of anyone's
remains in it.

## 1. The mechanism (all graph data — CLAUDE.md, §0)

* Production `RetinaCell -endo_drives-> EyeCell` — co-located 1:1. Positional
  geometry, the same licence `WaveWorld` takes for its 4-neighbourhood.
* `ey_endo_resp` — in the pre-visual phase the cell's OUTPUT IS its spontaneous
  burst. Deliberately **not** routed through `lum`: a wave is not light.
* `ey_endo_latch` — `mu_endo_n = mu_endo_{n-1} + (resp − mu_endo_{n-1})/n`.
* `ey_adapt_theta_endo` — GCAL Eq. 8 reading the cell's OWN `mu_endo`.
* Arms are DATA (`mu_mode`), OFF by default (`calib=0`, `mu_mode=0`, §9).

## 2. §2 — CONVERGENCE, measured FIRST (seed 0, burned)

`scripts/eye_setpoint_convergence.py`, 6400 steps.

| | first cut (EMA, `xbar`) | committed (cumulative mean) |
|---|---|---|
| final mean `mu_endo` | 0.143749 | **0.146175** |
| L2 drift at end | **0.078** (never approaches 0) | **0.0021** |
| verdict | **TRANSIENT — §2 STOP** | **CONVERGENT + NON-ZERO** |

**§2 caught a real defect and the fix was MECHANISM, not metric.** An EMA is a
*tracking filter*: its variance does not decay (steady-state SD ≈
√(p(1−p)(1−β)/(1+β)) ≈ 0.024 at p=0.146), so it has **no stable fixed point** —
precisely what §2 says cannot model development. A cumulative mean's variance
falls as 1/n and converges to E[resp].

**The estimator is unbiased:** final `mu_endo` **0.146175** vs the measured mean
burst rate **0.146197** — agreement to 0.015%.

**A reader error, found by positive-controlling it (§1, §12).** The first cut
read `ww.frame()` as "the endogenous input". `frame()` is `state=="active"`
(wave path only, sampled *after* the double-buffered commit) and reported
**0.0234**; the attribute the rule actually reads (`bursting`) was **0.1444**. A
6× error — *in the direction that would have made the setpoint look like GCAL's
0.024.* Read what the RULE reads.

## 3. Instrument check — arm A0 reproduces FM-1b EXACTLY (seed 0, burned)

FM-1b's protocol (no wave phase, `mu=0.024`), all four published statistics:

| statistic | FM-1b | reproduced |
|---|---|---|
| min aliveness | 10.5% at t=340 | **10.5% at t=340** |
| max θ (spatial **mean**) | 0.4603 | **0.4603** |
| final mean resp | 0.024958 | **0.024958** |
| t=0 mean resp | 0.398910 | **0.398910** |

*Recorded because it nearly produced a false alarm:* reading the spatial **max**
θ gives 0.8125 and would have been reported as a reproduction FAILURE. It is two
different statistics, not two different models. FM-1b's `run()` records
`thetas().mean()`.

## 4. Design (§6 — what each arm corresponds to IN THE ANIMAL)

* **Phase 0 (BOTH arms, identical):** eye closed; the only input is the eye's own
  spontaneous retinal waves. `calib=1`; θ **frozen** (a homeostat running during
  the measurement would regulate the quantity being measured). 3200 steps
  (converged; §2). Rung 1's committed wave protocol (`ignite_k=1`,
  `ignite_every=5`).
* **Phase 1 (BOTH arms, identical input):** eye opens on FM-1b's static frame,
  1200 steps. `calib=0`; θ adapts.
* **The arms differ in `mu_mode` AND NOTHING ELSE.** Same age, same wave history,
  same visual input, same RNG streams. Both even MEASURE `mu_endo`; arm A ignores
  it and uses GCAL's 0.024.

## 5. Hypothesis (two-sided)

**H1:** an eye whose homeostatic setpoint was measured from its own endogenous
activity **differs in aliveness** under visual input from an identical eye given
GCAL's imported `μ=0.024`.

Two-sided: predicted directions in this arc have been wrong four times.

## 6. The statistics, exactly

* **PRIMARY — min aliveness** (§1.1's own metric): per seed, per arm,
  `min over t∈[0,1200) of (fraction of cells with resp > 0)`.
* **SECONDARY — max θ (spatial mean)**: per seed, per arm,
  `max over t of thetas().mean()`.

Exactly these two. No others. `peak/base` is NOT read (unbounded; blown up in two
rungs). Both are reported regardless of outcome.

## 7. Unit of analysis, n, and the test (§3.3, §4)

**Unit = THE SEED** (one wave realisation + one eye). Never the cell: cells share
one wave field and one frame.

**PILOT (burned seeds 0–5), `scripts/eye_setpoint_pilot.py`:**

| arm | min aliveness | max θ(mean) | `mu_endo` |
|---|---|---|---|
| A (`mu=0.024`) | 0.0% on 6/6 seeds, sd 0.0000 | 0.4663–0.4697 | (measured, ignored) |
| B (endogenous) | 100.0% on 6/6 seeds, sd 0.0000 | 0.2990–0.3031 | 0.144134 ± 0.001151 |

> **CORRECTION, made AFTER the confirmatory run and flagged rather than silently
> fixed.** This table first carried **0.8161–0.8178 / 0.6217–0.6257** in the θ
> column. Those are the spatial **MAX** θ, from the pilot run *before* §3's
> instrument check made me read FM-1b's spatial **MEAN** — mislabelled `(mean)`.
> The values above are the re-run pilot's true θ(mean) and agree with the
> confirmatory arms (0.4684 / 0.2994). **What this cost:** §10's predicted θ
> VALUES ("B ≈ 0.62 < A ≈ 0.82") were quoted for the wrong statistic and are
> wrong as stated; the predicted DIRECTION (B < A) is right and CI-separated.
> **The primary statistic, the sign test and n are untouched** — none of them
> reads θ. Recorded because a mislabelled column is exactly how a forking-paths
> garden starts (§4).

**The separation is DETERMINISTIC (sd = 0 in both arms), so a paired t-test on
the primary is undefined.** Pre-registering the honest alternative:

* **PRIMARY test: exact paired SIGN TEST** across seeds. Under H0 the sign of
  (B−A) is equally likely ±; two-sided `p = 2·(1/2)^n`.
  **n = 8 ⇒ p = 0.0078 < 0.01.** n is FIXED AT 8 by this requirement, in advance.
* **SECONDARY test: paired t** on max θ(mean) (this statistic has variance).

**Confirmatory seeds: block 14000–14999, seeds 14000–14007.** Declared here,
before the run. Never used for anything (ledger: allocated to the failure-mode
battery, which burned none of it; this work IS its continuation — JOB 1 is FM-0's
own gate and JOB 2 is the μ pathology FM-1b found).

## 8. Decision rule, including what a null means

* **B > A on ≥ 8/8 seeds** (sign test p = 0.0078) ⇒ H1 supported: the setpoint's
  SOURCE changes whether the eye survives its own homeostat.
* **Any seed with B ≤ A** ⇒ p ≥ 0.07, H1 NOT supported at the declared level.
* **A NULL (B dies too, or B ≈ A)** is a RESULT and will be reported as such (§7):
  it would mean **the endogenous activity does not carry the scale the visual
  regime needs** — evidence AGAINST the creator's pre-visual thesis that "sight
  arrives as perturbation of an already grounded relational structure". It would
  NOT license adding a floor, a fraction, or a tuned `mu` (§13, §5).
* **No sweeps. No re-runs.** A further attempt needs a NEW pre-registration with a
  NEW mechanism-level hypothesis — never a parameter search.

## 9. §13.1 — COULD THIS MODEL HAVE PRODUCED THE OPPOSITE RESULT?

**Yes, and the quantity that decides it is not mine to set.** `mu_endo` is
whatever the waves say. It came out **0.144**; had rung 1's waves burst at ~0.02,
`mu_endo` would have landed on GCAL's value and arm B would die EXACTLY as arm A
does. Nothing in `ey_endo_latch` prevents that — it is an unbiased mean of an
input it does not control, and it agrees with that input to 0.015%.

The burst rate is fixed by **rung 1's committed wave rules** (`refractory_steps`,
`enhance_rate`, `depress_rate`, `propagate`), authored long before this question
existed and not touched here. **No rule in this mechanism is "solely responsible"
for the survival of arm B** — the wave physiology is, and it is not consulted
about the answer.

**Honest asymmetry:** the §2 pilot has *already told me* `mu_endo ≈ 0.144`, and
FM-1b already established that 0.1995 lives and 0.024 dies. So I can predict the
outcome. That is what a pilot on burned seeds is FOR (§3.3) — it is not the same
as the architecture forcing it. The falsifiable step was the measurement of the
burst rate, and it could have come out anywhere.

## 10. Prediction, stated in advance, with provisos (§3.7)

**I predict H1 supported: arm B min aliveness 100% on 8/8; arm A 0% on 8/8;
sign-test p = 0.0078. Arm B's max θ(mean) ≈ 0.62 < arm A's ≈ 0.82.**

I predicted earlier, from rung 1's headline "0.195", that the endogenous rate
would be ≈0.195 and near FM-1b's surviving 0.1995. **That was WRONG in value:
it is 0.144.** Proviso (a) below is the one that broke — 0.195 is a different
statistic (wave *structure*, not burst rate). Right in order of magnitude and
direction (≫ 0.024), wrong in value.

**Provisos — what would make this mean less than it looks:**

1. **`mu_endo` inherits rung 1's WAVE PROTOCOL** (`ignite_every=5`,
   `refractory_steps=4`). A sparser protocol lowers the burst rate and could kill
   arm B. The setpoint is free of a *constant*; it is **not** free of the wave
   physiology it is measured from. That is the pre-visual thesis, not a bug — but
   it means "no magic numbers" is a claim about THIS mechanism, not about the
   ladder beneath it.
2. **The drive scale is the frame's.** 0.024 is a 16.6× compression *of this
   scene's* 0.399. On a much dimmer scene both arms could die; the result is
   scoped to this drive scale (§8).
3. **THE COMMENSURABILITY ASSUMPTION, and it is the weakest link.** `mu_endo` is
   the mean of a **{0,1} burst** alphabet; `resp` under vision is **graded**. I
   claim both are "mean activity as a fraction of the cell's dynamic range" and
   are therefore the same quantity. If that is wrong, arm B's survival is luck —
   a number of the right magnitude arriving for the wrong reason. **Nothing in
   this experiment tests the assumption**; it would need a rung where the
   endogenous and visual alphabets are made commensurate on purpose (FM-2 found
   the retina binarises its own input, which is the same wound).
4. Arm A here dies HARDER than FM-1b's arm A (0% vs 10.5%) because it carries the
   wave phase: `xbar ≈ 0.144` at eye-opening is 6× above `μ=0.024`, so θ ramps
   harder. **Arm A is therefore NOT FM-1b's arm A** and its 0% is not FM-1b's
   10.5% re-measured. A0 is the reproduction control; A is the matched control.

---

# RESULTS — the pre-registered confirmatory run

`scripts/eye_setpoint_confirm.py`, engine **`6fcc99edfa4a`**, pre-registration
committed at **`88d23b68`** BEFORE the run. Seeds **14000–14007** (n=8, block
14000–14999, declared in advance). Exactly the two declared statistics, exactly
the declared test. No sweeps, no re-runs.

## H1 — SUPPORTED

| | arm A (GCAL's imported `μ=0.024`) | arm B (endogenous setpoint) |
|---|---|---|
| **min aliveness** (PRIMARY) | **0.0%** on 8/8, sd 0.0 | **100.0%** on 8/8, sd 0.0 |
| **max θ(mean)** (SECONDARY) | 0.4684 ± 0.0011 | **0.2994 ± 0.0017** |

* **PRIMARY: B > A on 8/8 seeds. Exact two-sided sign test p = 2·(1/2)⁸ =
  0.0078 < 0.01.** The decision rule's threshold, met exactly as declared.
* **SECONDARY: paired diff (B−A) = −0.1690 ± 0.0018, t(7) = −268.17.** Arm B's
  homeostat never has to wind θ as hard, because it is not chasing a target 6×
  below what the cell can deliver.

**Arm A dies completely: not one cell responds, at the deepest point, on any of
8 seeds.** Same eye, same waves, same visual input, same RNG streams — the ONLY
difference is where the setpoint came from.

## What fell out

**`mu_endo` = 0.145900 ± 0.001401** (range [0.143609, 0.147872]) — **6.08×**
GCAL's imported 0.024. Measured by the system in itself, from its own spontaneous
waves, before it saw anything. Nothing was tuned toward this number: the
estimator agrees with the input's own mean burst rate to **0.015%** (0.146175 vs
0.146197, §2 probe).

## The prediction (§3.7) — what I got right and what broke

**Right:** arm B 100% on 8/8, arm A 0% on 8/8, p = 0.0078, B's θ < A's. The
primary was predicted exactly.

**Broke — proviso 1, and it broke BEFORE the run:** I predicted `mu_endo ≈ 0.195`
from rung 1's headline "0.195 vs 0.000". It is **0.144–0.146**. That headline is
a *different statistic* (wave structure, not burst rate). Right in order of
magnitude and direction (≫ 0.024); wrong in value.

**Broke — the θ VALUES:** predicted "B ≈ 0.62 < A ≈ 0.82"; measured 0.2994 /
0.4684. Those predicted values were quoted off a **mislabelled pilot column**
(spatial max, not FM-1b's spatial mean) — see the correction in §7. Direction
right, values wrong, primary unaffected.

## Scope — what is NOT shown (§8)

* **Not shown: that a wave-derived setpoint is CORRECT, only that it is
  SURVIVABLE.** Arm B is alive and uniform; this experiment does not measure
  whether 0.146 is a *good* operating point for information transmission. "Alive"
  is a floor, not an optimum.
* **Not shown: the commensurability assumption** (proviso 3, and it remains the
  weakest link). `mu_endo` is the mean of a **{0,1} burst** alphabet; `resp` under
  vision is **graded**. The claim that both are "mean activity as a fraction of
  dynamic range" is an ASSUMPTION this experiment does not test. If it is wrong,
  arm B's survival is a number of the right magnitude arriving for the wrong
  reason. FM-2's finding (the retina binarises its own input) is the same wound.
* **Not shown: freedom from the wave physiology** (proviso 1). `mu_endo` inherits
  rung 1's `ignite_every=5` / `refractory_steps=4`. The setpoint is free of a
  *constant*; it is **not** free of the ladder beneath it. A sparser wave protocol
  would lower `mu_endo` and could kill arm B — which is the pre-visual thesis
  having empirical content, not a defect.
* **Not shown: anything about Troxler.** JOB 3 is not run.
* **Scoped to this drive scale.** 0.024 is a 16.6× compression *of this scene's*
  0.399 (proviso 2).
* Arm A is **not** FM-1b's arm A (it carries the wave phase, so it dies at 0% vs
  FM-1b's 10.5%). A0 is the reproduction control and reproduces all four of
  FM-1b's published statistics exactly.

## §13.1 — could this model have produced the opposite result?

**Yes.** `mu_endo` is an unbiased mean of an input the mechanism does not
control, agreeing with it to 0.015%. Had rung 1's waves burst at ~0.02, `mu_endo`
would have landed on GCAL's value and **arm B would have died exactly as arm A
does**. No rule here is "solely responsible" for arm B's survival — the wave
physiology is, it was authored long before this question existed, and it was not
consulted about the answer. The falsifiable step was the *measurement of the burst
rate*, and it could have come out anywhere.

---

## CORRECTION — "arm A DIES" OVERSTATES IT. It goes BLIND, then recovers.

*Made against myself after the confirmatory run, before reporting (§5 permits
only this direction; §8 demands it). Measured on **burned** seeds 0–2, so no
confirmatory seed is touched and no declared test is re-run.*

The primary statistic is **min** aliveness — a statistic about the **transient**.
It says nothing about where the arm ends up, and I did not report where it ends
up. Both arms do:

| seed | arm | min aliveness | **final aliveness** | final mean resp |
|---|---|---|---|---|
| 0 | A | 0.000 | **1.000** | 0.024860 |
| 0 | B | 1.000 | **1.000** | 0.143088 |
| 1 | A | 0.000 | **1.000** | 0.024916 |
| 1 | B | 1.000 | **1.000** | 0.141491 |
| 2 | A | 0.000 | **1.000** | 0.024894 |
| 2 | B | 1.000 | **1.000** | 0.144985 |

**Arm A RECOVERS to 100% aliveness at mean resp ≈ 0.0249 ≈ μ** — exactly FM-1b's
finding. **Both homeostats work.** They differ in the *target they are given* and
therefore in the *violence of the transient required to reach it*.

**The honest claim, and it is narrower than "dies":**

> An eye given GCAL's imported constant passes through a window in which **every
> single cell is silent** — it is completely blind, and §1.1 is explicit that a
> silent arm is a FAILED GATE, never a good floor. An eye using the setpoint it
> measured in itself **never has a single silent cell, at any timepoint, on any
> seed.** Both end alive.

**Why:** after the pre-visual phase `xbar ≈ 0.145`, which is **6× above μ=0.024**,
so θ overshoots hard to force the 16.6× compression the imported constant demands,
and the sheet blacks out until θ relaxes. Arm B's target is already the scale its
own activity lives on, so there is no overshoot to survive (max θ(mean) 0.2994 vs
0.4684).

**What this costs the result:** the effect is real, pre-registered, CI-separated
and 8/8 — but it is about the **transient cost of an imported scale**, not about
permanent death. `min_alive` was the right §1.1 statistic to pre-register and it
is not the whole picture; **`final_alive` should have been declared alongside it,
and was not.** That omission is mine. It does not change the primary (both arms'
`final_alive` are identical at 1.000, so no declared comparison moves), but a
reader of the headline alone would have believed something false.

---

## The literature — what it does and does not license (added post-hoc, and scoped)

**Hengen et al. 2016 (Cell 165:180–191):** *"neocortical neurons in vivo return
quite precisely to an **individual** FR set point."* **Individual — not a
universal constant.** That is the shape this mechanism has: `mu_endo` is a
**per-cell attribute**, each cell arriving at its own from its own history, and
nothing anywhere holds a population-wide target. GCAL's `μ` is the opposite shape
— one number for every cell in every frame — which is §13's "an absolute constant
IS a view from nowhere" stated in the biology's own terms.

**Its scoping, which is the paper's and not mine to drop:** Hengen frames the
contrast with Slomowitz et al. 2015 as **culture vs in vivo — a preparation-level
difference**. So it is **not** a refutation of an absolute setpoint; it is
evidence that *in vivo*, setpoints are individual. Cited for the SHAPE, and it
licenses nothing about which mechanism establishes it.

**AND THE HONEST HALF, MEASURED RATHER THAN ASSUMED (seed 0, burned, 1600
steps):** my setpoints are individual **by construction** and nearly uniform **in
fact** —

| per-cell `mu_endo` | value |
|---|---|
| mean | 0.142330 |
| sd | 0.000278 (**0.20% of the mean**) |
| range | [0.141162, 0.143036] |
| **distinct values** | **4 of 256 cells** |

**Four distinct values across 256 cells.** Every cell sees essentially the same
near-homogeneous wave field, so its "own history" is nearly its neighbour's. **So
this mechanism reproduces Hengen's SHAPE (per-cell, self-measured) and NOT its
CONTENT** — real cortical firing rates are famously heterogeneous, log-normally
distributed across orders of magnitude, and nothing here produces that. Claiming
"individual set points, as Hengen found" would be true of the wiring and false of
the result. **Not shown: setpoint heterogeneity.** What is shown is only that the
setpoint's SOURCE is the cell's own activity rather than an import.

**Still owed:** the Turrigiano / developmental-setpoint review this mechanism's
form should have been checked against BEFORE it was built. The form was decided by
§2 (a cumulative mean converges; an EMA does not) and §13 (zero free parameters) —
both stronger constraints than a citation, but neither is a literature check, and
whether biology establishes the setpoint by a *cumulative mean of early
spontaneous activity* specifically remains **unverified here**.
