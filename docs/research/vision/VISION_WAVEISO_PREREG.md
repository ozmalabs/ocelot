# WAVE ISOTROPY — pre-registration

**Committed BEFORE the confirmatory run.** Engine `74fc035c8595` @ the canonical
`runners/dsl/python/substrate_rs/_native.abi3.so`, **`shared` build — Rust source
byte-identical to this tree** (this rung adds NO Rust, so a shared build is
legitimate under §10.1 rule 4; `provenance_line()` is pasted into every result).
Base commit `d9300ccc`.

## 0. The question, and what it is NOT

Rungs 8C and 8E explain this arc's cortical negatives with ONE mechanism claim:

> *"the wave ensemble is orientation-**ISOTROPIC**; decorrelation removes a
> redundancy without installing an anisotropy."*

**That claim has been asserted by three rungs in a row and NEVER MEASURED.** It
is load-bearing: Oja converges to the leading eigenvector of `E[xx^T]`, so if
that ensemble carries no orientation, **no rule of that class can produce
orientation selectivity — that is arithmetic, not a bug**, and nine rungs would
have been asking the cortex to extract structure the input does not contain.

**This rung measures the STIMULUS. It changes nothing, touches no cortex, fixes
nothing.** A defect found is reported, not repaired (§9). It is linear algebra on
the wave ensemble: no learning rule, no probe, no arm.

## 1. The two hypotheses, and that I hold no stake in either (§7)

- **H_A — the input is the problem.** Real Stage II waves are travelling FRONTS;
  a wavefront has a LOCAL orientation. If our waves lack that, the input carries
  no orientation and the cortex was never at fault.
- **H_B — the input is fine and isotropy is a red herring.** GCAL/LISSOM produce
  orientation maps FROM ISOTROPIC INPUT; the anisotropy comes from symmetry
  breaking in the weights under lateral competition, not from the stimulus.

**Either answer is a result.** *"The waves are isotropic"* reopens the paradigm
question; *"the waves carry orientation and the cortex genuinely failed"* closes
it harder. **I will not tune toward either.**

## 2. What `x` is — and the two constants that are READ, not chosen (§13)

`oja_learn`'s x term is, verbatim from `seeds/vision_waves.json`:

```
IfThenElse(Lte(Minus(r.step, c.last_burst), WaveParams.window_steps), 1, 0)
```

so **x_i(t) = 1 iff cell i burst within `window_steps` of t**, and
`window_steps = 2.0` in the committed `WaveParams` node. **We measure what the
rule reads.** Measuring the INSTANTANEOUS frame instead would rebuild §12.2's
blind zero-lag measure exactly (a travelling wave reaches a cell and its
neighbour at different times; refractoriness makes them mutually exclusive at any
instant, so zero-lag reads ~0 for a PERFECT wave).

**VERIFIED, not assumed:** the OR-window reconstruction equals the graph's own
`(step - last_burst) <= 2` on **27,648 / 27,648 cell-steps, 0 mismatches**.

| constant | falls out of |
|---|---|
| `window_steps = 2` | the committed `WaveParams` node — read from the seed |
| `rf = 7` | `add_units`' committed default |
| displacements `0 < \|d\| <= 3` | `rf//2` — the RF's own half-width |
| `R` computed to `\|d\| <= 6` | `rf-1`: `M[a,b]=R(d_a-d_b)` and the extreme RF offsets differ by 6 |
| `ignite_k=1`, `ignite_every=6` | `wave_world.record`'s committed defaults |
| disk control radius | the waves' OWN measured half-height correlation length |
| `H=W=64` | see §2.1 |
| `n = 16` | §3.3's power analysis on the burned-seed pilot |

### 2.1 The one size choice, stated plainly

`H=W=64`, with `STEPS=200` after `BURN_IN=20`. **This is a choice, not a
derivation**, and it is the weakest constant here. Its justification: the RF is
7x7, and PRIOR_ART §3.4 records that at 16x16 *"one wave covers ~half our grid"*,
which would confound wave-scale with grid-scale. 64x64 is ~9 grid-widths per RF
and leaves the wave small relative to the field. **A grid-size sensitivity check
at 128x128 is declared here as a SECONDARY descriptive** (one seed, reported
whatever it shows) — not a sweep to pick a winner.

## 3. The measurements

### 3.1 PRIMARY — DECISIVE: the eigenspectrum of `E[xx^T]`

**The leading eigenvector IS what Oja converges to.** By translation invariance
(ignition is uniform over the grid), `M[a,b] = E_p[x(p+d_a)x(p+d_b)] =
R(d_a-d_b)`, so the 49x49 `M` an Oja unit sees is the block-Toeplitz matrix built
from the autocorrelation `R(d)`.

Reported: top-10 eigenvalues of **`M = E[xx^T]`** (what Oja actually sees — the
seed's rule runs on RAW non-negative x with no mean subtraction anywhere) **and**
of **`Sigma = M - mu mu^T`** (the covariance; reported because DC dominance and
orientation are different questions, and this arc has already been bitten by a DC
prior — `w0`, 431:1). Per eigenvector:

- **`OI`** = `|sum_{k!=0} P(k) e^{2i phi_k}| / sum_{k!=0} P(k)` on its 2D power
  spectrum, DC excluded. Grating at one orientation -> ~1; rotationally
  symmetric blob -> ~0. **Bounded in [0,1]** by the triangle inequality.
- **`DC`** = `P(0,0)/sum P(k)` — how much of it is a constant blob.
- **degeneracy** `lambda_1/lambda_2` and `lambda_2/lambda_3`. **A degenerate
  leading eigenspace means the "preferred" orientation is a COIN FLIP** — which
  is its own answer, and is not the same finding as "no orientation exists".

### 3.2 SECONDARY: `C(d, theta)`, global frame vs LOCAL WAVEFRONT frame

`A_m = |sum_d rho(d) e^{i m theta_d}| / sum_d |rho(d)|` over the RF's
displacements. **Bounded in [0,1] deliberately**: the obvious alternative
(normalising by `sum_d rho(d)`, a modulation depth) is an UNBOUNDED ratio that
blows up as the mean correlation crosses zero — the `peak/base` disease that has
already blown up in two independent rungs (§1.1). `A_2` = the orientation
harmonic; **`A_4` is reported too**, see §5.

**The local frame is the RF, and it is measured with a STRUCTURE TENSOR** —
`coherence = |(J_xx - J_yy, 2 J_xy)| / (J_xx + J_yy)` summed over a 7x7 window,
which is the second angular harmonic of the local gradient distribution (the same
currency as `A_2`, bounded the same way), and which aligns to each window's own
front normal automatically with no estimate of any wave's centre.

- `coh_local` = `E_window[coherence]` — per-RF, magnitudes averaged.
- `coh_global` = coherence of the SUMMED tensor — opposite orientations cancel.

**THE SUBTLETY THAT MATTERS, and it is why a per-FRAME harmonic is NOT the local
measure:** an ensemble of anisotropic waves with RANDOM propagation directions
averages to an ISOTROPIC ensemble covariance. So (3.1) and (3.2) CAN disagree,
and **that disagreement is itself the finding** — it would mean the structure
exists per-wave but is destroyed by ensemble averaging, which is a statement
about what the RULE can use, not about what the STIMULUS contains. A harmonic
computed per 64x64 frame is *not* local: one frame holds many independently
oriented wavefronts, so it cancels for the same reason the ensemble does.

### 3.3 n, FIXED IN ADVANCE

Pilot on **burned seeds 0-13** (`scripts/waveiso_pilot.py`, variance only, no arm):

| statistic | mean | sd |
|---|---|---|
| `coh_local_RF` | 0.7743 | 0.0211 |
| `coh_global` | 0.0530 | 0.0476 |
| `M_leading_OI` | 0.0936 | 0.0422 |
| `M_leading_DC` | 0.9825 | 0.0014 |
| `M_l1_over_l2` | 3.5059 | 0.2002 |
| `M_l2_over_l3` | 1.0948 | 0.0468 |
| `A2_global` | 0.0213 | 0.0190 |
| `front_nb_raw` | 1.9919 | 0.0048 |

**`n = 16`.** This is a DESCRIPTIVE measurement of a stimulus ensemble, not an
arm comparison — there is no treatment effect to power. n is fixed so the CI is
tight against the floor->ideal range: at n=16 the 95% CI half-width is `0.53*sd`,
so the **largest** pilot sd (`coh_global`, 0.0476) gives **±0.025** — 2.5% of the
[floor, ideal] range and ~20x smaller than the smallest separation §4 will claim.
**Every statistic is over-powered (all `dz > 9`), which I record as a fact rather
than a virtue: it is cheap here (~10 s/seed).**

**Confirmatory seeds: 20000-20015** (n=16), declared here, never used for
anything. Block **20000-20999** claimed. **12000-19999 untouched.**

## 4. The decision rule, INCLUDING what a null means

**Both arms of every gate must be ALIVE (§1 clause 4) — "scores at the floor" is
satisfied by DEATH.** Every arm reports density and dead-frame count.

For each statistic the two CONTROL arms fix a floor and an ideal, and the verdict
is declared against their **midpoint**:

- **ISOTROPIC** iff the waves' 95% CI lies **below** the floor->ideal midpoint
  and excludes it.
- **ANISOTROPIC** iff it lies **above** and excludes it.
- Anything else is **INDETERMINATE** and will be reported as such.

**What each outcome MEANS:**

| outcome | reading |
|---|---|
| `M`'s leading eigenvector is a **DC blob** (`OI` at floor, `DC`~1) | **No Oja-class rule can produce orientation from this ensemble. Arithmetic.** The arc's cortical negatives are a fact about the STIMULUS ensemble. |
| leading eigenvector **oriented** (`OI` near ideal) | The input carries orientation and **the cortex genuinely failed** — the arc's negatives are about the cortex, and H_A dies. |
| leading eigenspace **DEGENERATE** (`l1/l2`~1, both oriented) | Orientation exists but its sign is a **coin flip** — a third answer, neither H_A nor H_B, and the ARGMAX LOTTERY rung 8D found INDEPENDENTLY. |
| `coh_local` >> `coh_global` | Structure exists **per-wave**, destroyed by **averaging**. The blocker is the RULE CLASS, not the stimulus. |

**A NULL** (the ensemble reads isotropic) does **NOT** by itself vindicate H_A:
it must be read against `coh_local` and against the disks control, because **an
ensemble-isotropic input is not an obstacle to a model that does not merely
average** — which is exactly H_B's claim and is testable here (see §5's disks
arm).

## 5. §1 CALIBRATION — BOTH ARMS ALIVE, and the floor that had to be REPLACED

**Run on burned seeds 0-2 + a burned RNG. This is the highest-risk part of the
task: this arc has caught FIFTEEN inert instruments today.**

1. **FLOOR — `CONTROL_disks_ISO_FLOOR`**: randomly placed filled disks, density
   matched to the waves, radius from the waves' OWN measured correlation length.
   Isotropic AND correlated. Must read `A_2 ~ 0`, `coh_global ~ 0`, leading
   eigenvector NOT oriented.
2. **IDEAL — `CONTROL_bars_fixed_0` / `_45`**: bars at ONE orientation. Must read
   `A_2` high and its leading eigenvector ORIENTED.
3. **THE DISCRIMINATOR — `CONTROL_bars_random_theta`**: bars whose orientation is
   drawn per frame. Anisotropic in every frame, isotropic in the ensemble. **Must
   read `coh_global` ~ floor AND `coh_local` ~ ideal.** This is the ONLY control
   that tests the local-vs-global claim itself; without it, "structure exists
   per-frame but averages away" is an untested property of the INSTRUMENT rather
   than a finding.
4. **ANALYTIC — the eigen path against ARITHMETIC, not against my expectations.**
   For iid Bernoulli(p), `M = p^2 11^T + p(1-p) I` exactly, so
   `l1 = p^2 rf^2 + p(1-p)`, `l2 = p(1-p)`. A closed form the code cannot fit.

**WHITE NOISE IS NOT THE FLOOR, AND FINDING THAT OUT IS WHY THE GATE EXISTS.**
The first cut used white noise as the isotropic arm and it read **`A2_global =
0.5312`, not ~0**. Diagnosis: white noise has `rho(d) ~ 0` at every `d != 0`, so
`A_m` is a **ratio of sampling noise to sampling noise** — undefined, O(1), the
`peak/base` disease in a third costume. **White noise is OUTSIDE this statistic's
domain, not at its floor.** It is retained as `CONTROL_white_noise_OOD` and
reported, not hidden. The honest floor must be isotropic **AND correlated** —
which is why it is disks.

**And the disks arm is not merely a control: it is GCAL's OWN input** ("noisy
disk-shaped patterns", PRIOR_ART §2.6). **So it reads directly on H_B**: whatever
GCAL gets orientation from, if this ensemble reads isotropic then it is not this
ensemble's second-order statistics.

### 5.1 §13.1 — could this measurement have produced the opposite?

**Yes, and that is demonstrated rather than asserted:** the same code path reads
`OI = 1.0000` / `coh_local = 1.0000` on `bars_fixed_0` and `coh_local = 0.198` on
white noise. The instrument spans its own range.

**The lattice hazard, stated before the run.** The retina's `neighbour` edges are
a **4-NEIGHBOURHOOD on a square lattice** (`wave_world.__init__`), and this arc
has already found that *"the 4-connected argmin is a cardinal-axis artifact"*. A
diamond front is **4-fold symmetric**, and a 4-fold-symmetric `rho` has **`A_2 =
0` IDENTICALLY** (`e^{2i(theta+pi/2)} = -e^{2i theta}`, so the four
lattice-equivalent displacements cancel in pairs). **So `A_2` alone CANNOT see a
lattice diamond, and an `A_2` at the floor would be exactly what a lattice
artifact looks like.** `A_4` is therefore reported alongside it at every arm —
not to rescue anything, but so the artifact is visible instead of built in.

## 6. MY PREDICTION, with its provisos (§3.7)

**Stated in advance, and the pilot on burned seeds 0-13 has ALREADY been run —
so I record honestly that this prediction is INFORMED BY THE PILOT and is
therefore weak evidence** (§3.7's standard is being right in advance; a
pilot-informed prediction is a much cheaper claim). The confirmatory run tests
whether it holds on **fresh seeds never used for anything**.

**I predict NEITHER H_A NOR H_B, and a third answer:**

1. **The waves DO form fronts** — `front_nb_raw ~ 2.0` (a thin curve; a blob
   approaches 4, scatter 0). **H_A's premise fails.**
2. **The waves ARE locally oriented** — `coh_local ~ 0.77`, near
   `bars_random_theta`'s and far above the disk floor. **H_A's premise fails
   again: the stimulus DOES contain orientation.**
3. **The ensemble IS isotropic** — `coh_global ~ 0.05`, `A_2 ~ 0.02`, at the disk
   floor. **Rung 8C's premise is CONFIRMED at the ensemble level.**
4. **`M`'s leading eigenvector is a DC BLOB** — `DC ~ 0.98`, `OI ~ 0.09`,
   `l1/l2 ~ 3.5`. **So Oja converges to a blob and no Oja-class rule can produce
   orientation here. That is arithmetic — H_A's CONCLUSION survives even though
   its PREMISE fails.**
5. **The oriented modes exist but are DEGENERATE** — `l2/l3 ~ 1.09`, with
   `OI ~ 0.54-0.57` on both. **So even removing DC (which is what rung 7's
   decorrelation and rung 8E's H1 DID) hands the cortex a degenerate eigenspace —
   an ARGMAX LOTTERY, which is what rung 8D found independently.**

**Therefore: the blocker is the RULE CLASS, not the stimulus and not the cortex.**
Orientation lives per-wavefront with a phase that cancels under ensemble
averaging; Oja averages; GCAL's lateral competition acts WITHIN a pattern, before
averaging, which is why an ensemble-isotropic disk stimulus still yields maps.

**PROVISOS — the things that would tell me I did not understand the model:**

- **The window may be making the DC.** `window_steps=2` ORs 3 frames, thickening
  a 1-cell front into a ~3-cell band and raising density to ~12%. If DC dominance
  is an artifact of the window rather than of the waves, `window=0` will show it.
  **Declared as a secondary descriptive, reported whatever it shows.**
- **`coh_local` is a MAGNITUDE and is positively biased** by finite sampling; it
  does NOT go to 0 on an isotropic ensemble (white noise reads 0.198, disks
  0.473 — a disk's EDGE is locally oriented too). If the waves land near the disk
  floor rather than near `bars_random`, my claim (2) is wrong.
- **The disk floor may be too high** to separate: disks read `coh_local = 0.473`
  because a curved boundary is locally straight at RF scale. If waves read within
  noise of that, "locally oriented" is not established by this instrument.
- **64x64 may be too small** for the ensemble to be translation-invariant in
  practice; the 128x128 descriptive checks it.

## 7. Scope — what this rung does NOT show (§8)

- It says **nothing about which biological mechanism is correct**, and nothing
  about whether GCAL's mechanism would work HERE. The disks arm shows GCAL's
  INPUT is ensemble-isotropic; it does **not** run GCAL.
- It measures the **stimulus**, not any cortex. No cell is trained.
- `coh_local` establishes that orientation is present **at the RF grain**; it does
  **not** establish that any rule could extract it.
- The claim "no Oja-class rule can produce orientation" is about the **leading
  eigenvector of the measured ensemble** — it is arithmetic about THIS ensemble,
  not a theorem about Hebbian learning in general.
- **`n=16` fresh seeds of ONE wave model at ONE grid size.** Nothing here
  generalises to real retinal waves, whose directional bias (Ge 2021) our model
  does not implement at all.

## 8. §9 — this rung changes nothing

No seed edited, no Rust, no default moved, no constant introduced into any
mechanism. Only new files: `scripts/waveiso_{lib,calibrate,pilot,confirm}.py`,
this file, and `VISION_WAVEISO_RESULTS.md`. The `rung7_vision_bench.sh` baseline
is re-run and quoted **with its condition** (§10.2: `190/10 without data/`,
`200/0 with`).
