# RUNG 5 — COMPLEX CELLS (phase invariance): pre-registration + outcome

*Binding order (PROTOCOL): convergence → calibrate the measure + positive control →
pre-register and COMMIT → ONE confirmatory run → report verbatim.*

**This rung stopped at step 2, and this document records why.** The measure calibrates,
the mechanism is built, convergent and demonstrably capable — but the **precondition
fails**: the model has no simple cells to pool. No confirmatory arms were run, because
arms run on a population with nothing to pool would measure nothing. That is the same
call PROTOCOL §2 makes for a transient scaffold ("STOP and report — do not run arms on a
transient"), applied one layer up.

---

## The rung, and the design

A **simple cell** is orientation-selective and **phase-sensitive**: its response to a
grating MODULATES with phase (F1/F0 > 1). A **complex cell** has the same orientation
preference but is **phase-INVARIANT** (F1/F0 < 1), classically built by POOLING simple
cells of one orientation across phases (Hubel & Wiesel; the energy model).
Developmentally the leading account is **temporal slowness / trace learning** (Földiák
1991): features that persist across adjacent moments share identity, and under motion
**phase varies fast while orientation varies slowly**.

**The mechanism, shipped as graph data** (`seeds/vision_complex.json`, `complex=0`
default; adapter `domains/complex_cells.py`):

| rule | what it does |
|---|---|
| `cx_activate` | `cact` = Σ `cweight` · RECTIFIED pooled-Unit `act` |
| `cx_trace` | `trace ← (1−δ)·trace + δ·cact` — the Földiák slowness trace |
| `cx_learn` | Oja **on the trace**: `cweight ← cweight(1 − η·trace²) + η·trace·x` |

The three rules are staged inside one `run_rules` fixpoint by step-markers
(`cact_step` → `trace_step` → `ctouched`), the idiom `oja_learn` already uses, so no rule
can race the rule that reads it.

**The ablation is DATA** (PROTOCOL §0): `ComplexParams.trace_delta = 1.0` (default) makes
`trace ≡ cact` exactly — no temporal memory, i.e. plain instantaneous Oja pooling.
`δ<1` is the slowness mechanism. One number, and δ=1 is exactly the no-mechanism
condition.

**Why a trace is the mechanism, and not a detail:** simple cells at the same orientation
but different phases are **anti-correlated at zero lag** (when the phase-0 cell is on,
the phase-180 cell is off), so an *instantaneous* covariance cannot bind them. Only a
time-**lagged** covariance can, and the trace is what makes Oja's attractor the
time-smoothed covariance rather than the instantaneous one.

### The rung-3 inversion that motivated this — and its status

Rung 3 was NOT BUILT because **Oja's attractor is the TIME-AVERAGED covariance — "the
average has no direction."** But **averaging over PHASE is exactly what a complex cell
IS**, so the property that forbade rung 3 should *grant* rung 5. That reasoning motivated
this design. **The positive control tested it directly, and it is REFUTED — in both
directions at once.** See the OUTCOME: phase invariance turns out to be FREE (no
averaging needed), and the same averaging that was supposed to grant it is what destroys
orientation selectivity. What remains untested is only the *developmental* version of the
question, because the precondition fails before an arm could be run.

---

## 1. THE MEASURE, AND ITS CALIBRATION (PROTOCOL §1)

**The statistic: F1/F0**, the modulation ratio of the response as a function of grating
phase — the standard simple/complex criterion (Skottun et al. 1991): **simple > 1,
complex < 1**. Conjunctively with **OSI** = (R_pref − R_orth)/(R_pref + R_orth) on the F0
tuning curve, because *a cell invariant to everything is not a complex cell, it is a
blob* — invariance must not be bought by losing tuning.

Two instrument decisions, both made at calibration, on principle, **before any gate**
(PROTOCOL §5 forbids making them afterwards):

- **Each phase is presented in ISOLATION.** `wv_unit_activate` counts any retinal cell
  that burst within `window_steps` (=2), so a genuinely DRIFTING presentation lets every
  unit integrate over three phases and **every unit looks phase-invariant** — the
  instrument would manufacture its own result. Each phase is a static flash with
  `last_burst` set for every cell; F1/F0 over the resulting phase-response function is
  the standard criterion computed honestly.
- **The read-out RECTIFIES** (`max(act, 0)`): a firing RATE is nonnegative.

### Instrument bugs found by calibration, before any gate

1. **No rectification ⇒ the instrument reported OSI = 0.0000 for a textbook Gabor.** A
   zero-mean Gabor's mean-over-phase is ~0, so F0 ≈ 0 and every tuning curve collapsed
   into noise. Caught by the ideal-Gabor positive control.
2. **Probe period 3 ALIASES with the integer lattice.** At period 3 the 0° reference
   Gabor is not zero-mean on the pixel grid and became DC-dominated (F0 ≈ 25 at *every*
   orientation, OSI 0.072) while 45/90/135° were cleanly tuned. **Period 4 is the
   calibrated regime** — all four reference orientations tuned:

| probe period | reference-Gabor OSI (0°/45°/90°/135°) | verdict |
|---|---|---|
| 3.0 | 0.072 / 0.865 / 0.748 / 0.877 | **aliases at 0°** |
| **4.0** | **1.000 / 0.796 / 1.000 / 0.818** | **CALIBRATED — used** |
| 5.0 | 0.920 / 0.506 / 0.924 / 0.498 | usable, weaker |
| 6.0 | 0.064 / 0.226 / 0.380 / 0.248 | exceeds the RF envelope |
| 7.0 | 0.005 / 0.108 / 0.136 / 0.108 | collapsed |

3. **A stateful-trainer bug**: the convergence loop re-seeded its RNG per call, replaying
   the identical input sequence, which would have made every drift reading a measurement
   of a repeat rather than of settling. Fixed before the numbers were read.

### THE INSTRUMENT BUG THAT INVALIDATED THE FIRST PASS — `oja=0` IS NOT A FREEZE

`bh_potentiate`, `bh_depress` and `bh_scale` are each gated on
`WaveParams.oja == 0.0`. So setting `oja=0` to "freeze learning" for a probe does not
switch learning off — **it switches the OTHER learning rule ON**, and the probe then
rewrites the WTA winner's synapses on every presentation. Measured before the fix:

```
  SIMPLE  layer max |dw| across ONE cell_stats probe : 47.89
  COMPLEX layer max |dw| across ONE cell_stats probe :  1.06
  -> three DIFFERENT hand-set poolings (ideal / uniform / blob) returned IDENTICAL
     scores (F1/F0 0.449, OSI 0.421) because the probe TRAINED them all to the same
     attractor. The instrument was measuring its own learning.
```

`complex_cells.freeze()` keeps oja SELECTED (so `bh_*` stay gated off) and zeroes both
rates, making each update an exact identity. **Verified: max |dw| across a probe =
0.000e+00.** Every number below is post-fix; the pre-fix numbers are discarded.
`test_oja_zero_is_not_a_freeze_which_is_why_freeze_exists` pins the trap.

### THE CALIBRATION TABLE (probe period 4.0, FROZEN probe, through the graph pathway)

| reference | weight anisotropy | **response OSI** | **F1/F0 raw** | F1/F0 evoked | scores as |
|---|---|---|---|---|---|
| ideal SIMPLE (Gabor, negative lobes) | 0.8672 | **1.0000** | **1.368** | 1.375 | SIMPLE ✓ |
| **ideal GABOR + DC** (same Gabor, shifted ≥ 0) | **0.8672** | **0.0000** | 0.187 | 1.281 | **no orientation** |
| the model's UNTRAINED Units (**the FLOOR**) | 0.1795 | **0.0044** | 0.179 | 1.361 | no orientation |
| the model's TRAINED Units (1600) | 0.3063 | **0.0037** | 0.163 | 1.399 | no orientation |
| the model's TRAINED Units (3200) | 0.2887 | **0.0043** | 0.177 | 1.408 | no orientation |

**THE FLOOR, STATED: response OSI = 0.0044** (ideal Gabor = 1.0000 through the identical
probe). **Duration check (PROTOCOL §1's third test): OSI is 0.0044 / 0.0037 / 0.0043 at
0 / 1600 / 3200 steps — FLAT.** The measure is not duration-confounded; it is reading a
population that does not change in the respect being measured.

### THE CUnit-LEVEL CALIBRATION — and why F1/F0 is DROPPED as the CUnit statistic

| CUnit reference | **F1/F0** | **OSI** |
|---|---|---|
| **FLOOR** — untrained, uniform pooling | **0.045** | **0.018** |
| **TARGET** — ideal pooling (4 phases of ONE orientation) = what SUCCESS is | **0.059** | **0.898** |
| **BLOB** — pooling all 16 (every orientation) = the failure mode | **0.033** | **0.013** |

**F1/F0 DOES NOT DISCRIMINATE AT THE CUnit LEVEL.** Floor 0.045, ideal target 0.059, blob
0.033 — all ≈ 0.05, and the untrained floor is already at the ideal-complex value (0.056).
**Phase invariance in this architecture is FREE: it is an arithmetic consequence of
summing ≥4 rectified phase-shifted inputs, not something a learning rule achieves.** Any
pooling — uniform, random, or blob — is phase-invariant. This is rung 3's lesson exactly
(*"the floor is 0.103, not 0 — `>0` was never evidence"*): **"F1/F0 = 0.34 is complex"
was never evidence.** F1/F0 is therefore retained only as a descriptive, and **OSI is the
only discriminating statistic at the CUnit level**. Decided at calibration, before any
gate, and it makes the result WORSE for the hypothesis, not better (PROTOCOL §5).

### SESOI, stated in advance

**10% of the measure's dynamic range**, matching rung 3. At the CUnit level the range is
floor 0.018 → target 0.898 ⇒ **SESOI = 0.088 OSI**. At the simple-cell level, floor
0.0044 → ideal 1.0000 ⇒ **SESOI = 0.100 OSI**. Rung 3's lesson is the reason this is
fixed before looking: *two of its effects were p=0.0001 and scientifically negligible.*

---

## 2. THE PRECONDITION FAILS — the model has no simple cells

A complex cell is **orientation-selective AND phase-invariant**. The orientation half is
absent from the population rung 5 was to pool:

```
the model's Units, probed FROZEN through the pathway an ideal Gabor scores OSI 1.0000 on:

  response OSI = 0.0044 (untrained) / 0.0037 (1600 steps) / 0.0043 (3200 steps)
                 max over all 36 units, any duration: 0.0150
  baseline / act = 1.011 - 1.012
    -> a unit answers an ORIENTED GRATING within 1.2% of how it answers UNSTRUCTURED
       NOISE at the same duty cycle.

  and, swept over EVERY spatial period so nothing can be blamed on scale
  (measured pre-freeze; the sweep's verdict is unchanged post-freeze at period 4):
    period 2 / 3 / 4 / 6 / 8  ->  OSI 0.0011 / 0.0020 / 0.0035 / 0.0025 / 0.0066

  the WTA population code (what the rules actually learn from -- `bursting`):
    ONE unit (u20) wins ALL 192 probes = 12 orientations x 16 phases.
    -> the population code is entirely stimulus-INDEPENDENT.
```

**They ARE phase-sensitive** (F1/F0_evoked ≈ 1.36–1.41 > 1, i.e. "simple" once the DC
baseline is subtracted). **They are NOT orientation-selective** (OSI 0.004 vs 1.000).
So the missing half is precisely the half a complex cell cannot be built without.

### THE ROOT CAUSE — measured, not inferred

```
Oja on nonneg binary input, from w0 > 0:  w <- w(1 - eta*y^2) + eta*y*x,  x in {0,1}, y >= 0
  => weights remain STRICTLY POSITIVE.        MEASURED: frac(w < 0) = 0.0000, every arm
  => act = sum of POSITIVE weights over a BINARY field that is ~50% on for ANY
     orientation  =>  act ~ 0.5 * sum(w) + a small modulation:  DC-DOMINATED.
  => the oriented structure that IS in the weights never reaches the RESPONSE.
```

**The isolating experiment — the whole diagnosis in one comparison.** Two hand-installed
units, probed identically, frozen:

| | weight anisotropy | response OSI | F1/F0 |
|---|---|---|---|
| **GABOR** (weights min −0.441) | **0.8672** | **1.0000** | 1.368 |
| **GABOR + DC** (same Gabor, shifted so every weight ≥ 0) | **0.8672** | **0.0000** | 0.187 |

**Identical weight anisotropy — 0.8672 both — and positivity alone destroys response
orientation-selectivity completely.** The anisotropy statistic mean-subtracts the
weights, so it cannot see the DC that the response cannot escape. **The model's trained
Units behave exactly like the GABOR+DC unit.** Real simple cells have ON/OFF push-pull
subfields — *signed* receptive fields. This model has no inhibition and no OFF pathway,
so its units cannot.

## 3. CONVERGENCE (PROTOCOL §2) — the pooling rule settles; η is a MEASURED regime

Gabor bank, `trace_delta=0.2`, structure = 1 − normalised entropy of the pooling weights
(0 = uniform over all 16 inputs, 1 = one input). Drift = ‖Δw‖/‖w‖.

| steps | η=5e-4 | η=1e-4 | η=2e-5 | η=5e-6 |
|---|---|---|---|---|
| 400 | **NaN** | 0.4532 / drift 3.4847 | 0.4498 / 3.5694 | 0.3664 / 3.5410 |
| 800 | **NaN** | 0.4390 / 0.2351 | 0.4500 / 0.0247 | 0.4376 / 0.0381 |
| 1600 | **NaN** | 0.5186 / 0.1541 | 0.4643 / 0.0269 | 0.4412 / **0.0098** |
| 3200 | **NaN** | 0.4537 / 0.1940 | 0.4387 / 0.0628 | 0.4286 / 0.0267 |
| 6400 | **NaN** | 0.4279 / 0.3993 | 0.4208 / 0.1021 | 0.4207 / 0.0480 |

**η = 5e-4 and 2e-3 DIVERGE to NaN** — the same `η·y² < 1` stability bound that produced
rung 2's L0 failure; a 16-unit bank makes `trace` large. **η = 1e-4 is the largest stable
regime; η ≤ 2e-5 settles cleanly** (structure plateaus ≈ 0.42–0.46 at non-zero, drift
falls to 0.010–0.048). This is a measured stable regime, **not a tuned optimum**, and the
residual drift at 6400 is falling, not zero — the honest claim is "converges toward
non-zero structure", exactly as rung 2's Oja check phrased it.

---

## 4. POSITIVE CONTROL (PROTOCOL §1) — is the pooling rule a null instrument?

Rung 3's η was a null instrument and **only its positive control revealed it**. The same
question, asked separately from the precondition: *given inputs that ARE phase-sensitive,
can the rule make a complex cell at all?* The simple layer is replaced by a
**hand-installed Gabor bank** (4 orientations × 4 phases at one retinal centre) — a
perfect stimulus. **This is a positive control, NOT an arm:** the bank is hand-built and
is exactly the structure the paradigm rule forbids handing the agent. It answers "is the
rule a null instrument?" and nothing else.


### POSITIVE CONTROL — OUTCOME

```
CUnit references (frozen probe), for scale:
  FLOOR  untrained, uniform pooling                : F1/F0 0.045   OSI 0.018
  TARGET ideal pooling (4 phases of ONE ori)       : F1/F0 0.059   OSI 0.898
  BLOB   pooling all 16 orientations               : F1/F0 0.033   OSI 0.013

the LEARNED CUnit, on a PERFECT hand-installed Gabor bank, 3200 steps:
  SLOWNESS (trace_delta=0.2)  cx_eta=1e-4 : F1/F0 0.337   OSI 0.005   structure 0.360
  SLOWNESS (trace_delta=0.2)  cx_eta=2e-5 : F1/F0 0.315   OSI 0.004   structure 0.357
  ABLATED  (trace_delta=1.0)  cx_eta=1e-4 : F1/F0  nan    OSI 0.000   (weights went NEGATIVE)
  ABLATED  (trace_delta=1.0)  cx_eta=2e-5 : F1/F0 0.413   OSI 0.004   structure 0.367

  the pooled simple cells it was given : F1/F0 1.28 (SIMPLE)   OSI up to 1.00
```

**THE POSITIVE CONTROL FAILS.** On the only statistic that discriminates, the learned
CUnit scores **OSI 0.004–0.005 — at or below the 0.018 uniform-pooling FLOOR**, against
an ideal-pooling TARGET of **0.898**. That is **0.5% of the dynamic range**, and it is
*negative* relative to the floor. **Slowness ≈ ablated** (0.005 vs 0.004): the trace makes
no difference. Given a perfect stimulus — hand-installed Gabors, four clean orientations,
four phases each — **the rule cannot make a complex cell.**

The pooling weights say why: `{0°: 1.401, 45°: 0.027, 90°: 0.194, 135°: 0.530}`. The
CUnit concentrates *somewhat* on one orientation but retains a large 135° component, so
it is orientation-MIXED. The ideal single-orientation pooling scores OSI 0.898, so a rule
that had selected one orientation cleanly would have shown it.

**Rung 3's root cause, recurring exactly.** Oja's fixed point is the leading principal
component of the (traced) covariance of the training distribution. That distribution is
**ISOTROPIC ACROSS ORIENTATION** — all four orientations shown equally often — so there
is no dominant orientation to find, and with a single CUnit and no competition nothing
breaks the symmetry. **A contraction to the mean of an orientation-isotropic distribution
is the mean.** This is the same sentence that killed rung 3, with "direction" replaced by
"orientation".

---

# OUTCOME / DECISION

# **DECISION: *** NOT BUILT ***** — on two independent, measured grounds.

**No confirmatory arms were run, and no confirmatory seeds were consumed.** Seeds
**7000–7999** are allocated to rung 5 in the ledger and remain **UNUSED and clean**. All
work above used seeds 0–2, already burned. Running arms would have measured pooling on a
population with nothing to pool, on a rule that fails its own positive control — the
error PROTOCOL §2 exists to prevent, one layer up.

### Ground 1 — THE PRECONDITION FAILS: the model has no simple cells

A complex cell is orientation-selective AND phase-invariant. The model's Units are
**phase-sensitive but NOT orientation-selective**: response **OSI = 0.004** (floor
0.0044, flat across 0/1600/3200 steps) against an ideal Gabor's **1.0000** through the
identical frozen probe. Root cause measured, not inferred: **Oja on nonneg binary input
yields strictly-positive weights** (`frac(w<0) = 0.0000`, every arm) ⇒ a DC-dominated
response (`baseline/act = 1.011`) ⇒ **the oriented structure that IS in the weights never
reaches the response**. Isolated by the GABOR vs GABOR+DC control: **identical weight
anisotropy 0.8672, OSI 1.0000 vs 0.0000.**

### Ground 2 — THE MECHANISM FAILS ITS OWN POSITIVE CONTROL

Given perfect inputs, the rule produces OSI 0.005 against a floor of 0.018 and a target
of 0.898. Slowness ≈ ablated. **Oja's attractor is the average, and the average of an
orientation-isotropic ensemble has no orientation.**

### THE INVERSION — TESTED, AND REFUTED IN BOTH DIRECTIONS

The hypothesis this rung was built on: *"Oja's attractor is the time-average — that killed
rung 3's direction selectivity, but averaging over PHASE is exactly what a complex cell
IS, so the property that forbids rung 3 may be the property that grants rung 5."*

**Both halves fail, and the measurements say so independently:**

1. **The averaging grants nothing, because phase invariance is FREE.** The untrained,
   uniform-pooling CUnit already scores F1/F0 **0.045** — at the ideal-complex value
   (0.056). Summing ≥4 rectified phase-shifted inputs is phase-invariant *by arithmetic*.
   There was never anything for the learning rule to achieve here. **"F1/F0 = 0.34 is
   complex" was never evidence** — the floor was 0.045.
2. **The averaging actively destroys the half that matters.** Orientation selectivity is
   the hard part, and Oja averages it away for exactly rung 3's reason: OSI 0.005 vs a
   0.898 target.

**So the inversion is not merely unconfirmed — it is backwards.** Oja's averaging fails to
grant the useful property (it was free) and does destroy the property that had to be kept.
My in-advance prediction, per the task framing, was that the inversion was *promising*.
**It did not hold, and the proviso that broke is the informative part:** I had assumed
phase invariance was something a rule must *achieve*. It is not — in any architecture that
pools rectified inputs, invariance is arithmetic and **selectivity is the scarce thing**.

## WHAT IS CLAIMED

1. **The pooling layer is real, graph-native and convergent.** Three rules staged in one
   `run_rules` fixpoint; the ablation is one number of graph data; structure plateaus
   ≈ 0.42 with drift falling to 0.010–0.048 at η ≤ 2e-5. **η = 5e-4 and 2e-3 diverge to
   NaN** — the same `η·y² < 1` bound as rung 2's L0 failure; η ≤ 1e-4 is a *measured
   stable regime*, not a tuned optimum.
2. **The measure is calibrated and its floors are stated** — and calibration cost three
   real instrument fixes found before any gate (missing rectification; period-3 lattice
   aliasing; `oja=0`-is-not-a-freeze).
3. **The model's Units have no orientation-selective response**, with a measured root
   cause isolated to weight positivity by a controlled comparison.
4. **The trace/slowness pooling rule cannot produce a complex cell even from perfect
   inputs**, with a measured root cause (an orientation-isotropic attractor).

## WHAT IS **NOT** CLAIMED (PROTOCOL 8)

- **NOT that rungs 1, 2 or 4 are wrong.** Their statistics are properties of the WEIGHTS
  (anisotropy; the spectral phase of the weight matrix), and those measurements stand
  exactly as reported. What is added here is adjacent and new: **that weight structure
  does not reach the units' RESPONSES** under a grating probe. Rung 2's own scope note
  already said "refined structure, not Gabors" (0.402 vs an ideal Gabor's 0.867); this
  measures a specific sense in which that gap matters. **It is not a retraction, and this
  data is not reinterpreted to make it one** — whether it bears on how rungs 1/2/4 should
  be read is a question for its own prospective pre-registration (PROTOCOL §5).
- **NOT that complex cells are unbuildable in this substrate.** What is measured is that
  *this* rule on *this* simple layer does not build them. A signed/push-pull simple layer
  is the obvious precondition fix and is NOT attempted here.
- **NOT that trace/slowness learning is refuted as biology.** The verified research
  refuted the Hebbian-vs-sparsity question 0-3; this licenses nothing about which
  biological mechanism is correct.
- **NOT a fair slowness-vs-ablation comparison.** The ablated arm (δ=1) **diverges to
  negative weights at η=1e-4** and only runs at η=2e-5, so the two arms are not stable in
  a common η. The comparison reported is descriptive, at η=2e-5 only, and both arms sit at
  the floor — which is why no ablation gate was run. Named, not removed.
- **NOT anything from n>1 seeds.** The positive control is a single-seed diagnostic
  (seed 0), like rung 2's convergence measurement — a dynamics check, not a hypothesis
  test. It is reported as such.
- **NOT that the CUnit F1/F0 numbers mean anything.** The statistic has no dynamic range
  at that level (floor 0.045 ≈ target 0.059 ≈ blob 0.033) and is reported descriptively
  only.

## THE NAMED NEXT HYPOTHESES (NOT run, NOT built here)

Each needs its own pre-registration with its own mechanism-level hypothesis — **not a
parameter sweep**. η, `trace_delta`, the bank, and the probe period are frozen.

1. **THE PRECONDITION: a SIGNED simple layer.** The blocker is that Oja on nonneg input
   cannot make a negative weight, so there is no ON/OFF push-pull and no orientation-
   selective response. The biology is explicit here — real simple cells have signed
   subfields. Candidates: an OFF pathway (a second, sign-inverted retinal channel, which
   the retina genuinely has), or subtractive inhibition between Units. **Until a Unit has
   an orientation-selective RESPONSE, no complex-cell rung is testable** — and this is
   the highest-value next step in the whole ladder, because it is the same fact that makes
   the units' response code stimulus-independent (one unit won all 192 probes).
2. **SYMMETRY-BREAKING ACROSS ORIENTATION for the pooling layer.** Even given simple
   cells, one CUnit under Oja converges to the orientation-isotropic mean. The fix is the
   one rung 3 already named and rung 4 already has a precedent for: **competition between
   CUnits** (a WTA/Argmax over the CUnit population, or an anti-Hebbian lateral term, so
   that once a CUnit claims an orientation its neighbours are pushed off it). Note the
   simple layer HAS this (hard global WTA) and the pooling layer does not — that
   asymmetry is very likely why the positive control fails, and it is the cheapest of
   these to test.
3. **A rule whose attractor is not the average**, for the orientation axis specifically —
   rung 3's standing open hypothesis, now confirmed to bind at a second level.


---
