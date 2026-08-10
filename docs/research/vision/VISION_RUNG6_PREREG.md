# RUNG 6 — THE SIGNED SIMPLE LAYER (ON/OFF split): pre-registration + outcome

*Binding order (PROTOCOL): fix the freeze → convergence → calibrate the measure +
positive control → pre-register and COMMIT → ONE confirmatory run → report verbatim.*

**This rung stopped at the convergence gate, and this document records why.** The layer is
built, the measure calibrates, the mechanism is demonstrably CAPABLE — but the rule does
not settle on its own input distribution, and where it is stable it produces nothing above
the untrained floor. **No confirmatory arms were run. Seeds 8000–8999 are allocated to
rung 6 and remain UNUSED and clean.** That is the call PROTOCOL §2 mandates, and the same
one rung 5 made one layer up.

---

## The rung, and the design

Rung 5 measured the blocker: **Oja on non-negative binary input from `w0>0` keeps weights
strictly positive** (`frac(w<0)=0.0000`) ⇒ a DC-dominated response ⇒ **the oriented
structure that IS in the weights never reaches the RESPONSE** (OSI 0.004 vs an ideal
Gabor's 1.000), isolated by GABOR vs GABOR+DC (identical anisotropy 0.8672, OSI 1.0000 vs
0.0000). Its named next step: **a SIGNED simple layer — the highest-value step in the
ladder, since nothing above V1 is testable until a Unit has an orientation-selective
RESPONSE.**

**Biology does not force the sign into the weight.** Real retinas split into **ON** and
**OFF** pathways; **Dale's law** keeps a neuron's synapses sign-constant. The sign
inversion happens in the RETINA (ON bipolars invert via mGluR6; OFF bipolars are
sign-conserving), so **both** pathways arrive EXCITATORY on the cortical cell and the
EFFECTIVE RF is signed while every weight stays ≥ 0:

```
act = SUM_i w+_i x_i  +  SUM_i w-_i (1 - x_i)
    = SUM_i (w+_i - w-_i) x_i  +  SUM_i w-_i
      \___________________/       \________/
       SIGNED effective RF        a constant
```

**The mechanism, shipped as graph data** (`seeds/vision_onoff.json`, `onoff=0` default;
adapter `domains/onoff_world.py`; emitter `tools/build_vision_onoff_seed.py`):

| rule | what it does |
|---|---|
| `oo_bipolar_burst` | ON bursts iff its RetinaCell burst within `window_steps`; OFF iff it did NOT. **ONE wave field drives BOTH channels** |
| `oo_sunit_activate` | `act` = Σ non-negative `weight` × pre-Bipolar burst, over both channels |
| `oo_sunit_rate` | `rate = max(act − theta, 0)` — the spike threshold |
| `oo_sunit_adapt_theta` | `theta ← theta + theta_rate·(act − theta)` — homeostasis on the ACTIVATION function |
| `oo_sunit_burst_winner` | WTA over SUnits by `rate` |
| `oo_sunit_xbar` | per-channel means `xbar_on` / `xbar_off` |
| `oo_learn_sub` | `dw = eta·y·(x − xbar_pol)`, clipped to `[0, wmax]` (Miller & MacKay) |
| `oo_learn_oja` | `w ← w(1 − eta·y²) + eta·y·x` — the `subnorm=0` arm |

**Ablations are DATA** (PROTOCOL §0): `split=0` collapses OFF onto ON (`x_OFF = x`) — a
single non-negative channel, i.e. rung 5's condition, with **identical anatomy, identical
synapse count, identical rules**, so the ablation isolates the SIGN and nothing else
(rung 4's lesson: an ablation that also removes anatomy is not null). `subnorm=0` runs
plain Oja. `frozen=1` is a real freeze. `onoff=0` (default) makes the layer inert.

**Waves are never hand-segregated.** Stage II cholinergic waves drive ON and OFF alike;
ON/OFF segregation is an OUTCOME the Units must grow (Gjorgjieva et al. 2009 has
burst-timing-dependent plasticity guiding it). Both channels read the SAME `RetinaCell`.

---

## 0. THE FREEZE BUG — FIXED, AND GATED

**`oja=0` IS NOT A FREEZE.** `bh_potentiate` / `bh_depress` / `bh_scale` are each gated on
`WaveParams.oja == 0.0`, so setting `oja=0` to "switch learning off" **switches the OTHER
learning rule ON**. Rung 5 measured 47.9 max |dw| per probe from this.

The fix is `OnOffParams.frozen`: **one flag every learning rule in this seed carries in its
`where`**, so no rule can learn while it is set, *regardless of which other rule is
selected*. It also gates `oo_sunit_adapt_theta` — **adaptation is plasticity**, and a probe
that let `theta` chase the probe stimulus would be the instrument training itself, the same
class of bug.

```
REAL freeze       max |dw| across a full probe : 0.000e+00
DEFECTIVE (oja=0) max |dw| across a full probe : 2.281e-02   <- the trap, still live
```

**The gate FAILS on the defective freeze and PASSES on the fixed one**
(`test_oja_zero_is_NOT_a_freeze_which_is_why_the_real_freeze_exists` asserts the defect is
real; `test_the_real_freeze_is_exact` and `test_the_real_freeze_also_freezes_the_threshold`
assert the fix).

**Does it change any committed result? NO — checked, not assumed.** Rungs 1/2/4 report
statistics of the WEIGHTS (anisotropy; the spectral phase of the weight matrix), read
directly out of the graph with no stimulus presented, so no rule fires during their
read-out and there is nothing for a freeze to protect. The bug only bites a **probe that
presents stimuli** — which is rung 5's instrument and this one. Rung 5 already discarded
its pre-fix numbers.

---

## 1. THE MEASURE, AND ITS CALIBRATION (PROTOCOL §1)

**The statistic: OSI** = (R_pref − R_orth)/(R_pref + R_orth) on the F0 tuning curve —
**rung 5's instrument, unchanged** (rectified read-out; each phase presented in isolation;
probe period 4.0, the calibrated anti-aliased regime; frozen probe). The only change is
that it reads the cell's OUTPUT (`rate`) rather than its raw drive, because a firing rate
is what OSI is defined on.

### THE INSTRUMENT FINDING THAT CHANGED THE MODEL — the split alone is not enough

**Measured at calibration, before any gate, on the ideal exemplar:**

| ideal split-Gabor | OSI |
|---|---|
| **without a threshold** (`homeo=0`, theta pinned at 0) | **0.0006** |
| **with the threshold** | **0.9115** |

A *perfect* signed simple cell read as **unoriented**. Cause, isolated analytically and
confirmed in the graph: the OFF channel's **tonic drive** `Σw⁻ = 5.613` sits **above** the
signal (~±2.3), so `act` never reaches 0 at any orientation, **rectification never bites**,
and F0 is flat (0° 5.120 vs 90° 5.055). With a threshold cancelling the tonic drive:
F0(0°) 2.314 vs F0(90°) 0.000 ⇒ OSI 1.0000.

**So the split makes the FILTER signed, but only a THRESHOLD makes the RESPONSE signed.**
The missing component is the spike threshold — the "iceberg effect" (Priebe & Ferster 2008):
a simple cell's orientation selectivity in the FIRING RATE comes from thresholding a signed
membrane potential. `theta` is an EMA of the cell's own drive (`rate = max(act − theta, 0)`),
so it adapts to whatever the tonic drive is rather than being hand-set.

**Placement is the point** (VISION_PRIOR_ART.md's GCAL lesson, followed deliberately):
`theta` lives on the **activation function**, entirely **outside** the learning rule, where
it **cannot flip the sign of `dw`** — structurally unable to annihilate the way our BCM did
(BCM's threshold flips `dw`'s sign and converged to 0.004 = death).

**THIS IS A MODEL FIX, NOT METRIC SURGERY (PROTOCOL §5).** The MEASURE is untouched. What
changed is the AGENT: it grew a threshold, because a cell without one cannot be
orientation-selective *in principle*. The discovery came from PROTOCOL §1's ideal-exemplar
test **before any hypothesis was gated**, which is exactly what that test is for.

### THE CALIBRATION TABLE (probe period 4.0, FROZEN probe, through the graph)

| reference | **response OSI** | peak/baseline |
|---|---|---|
| **ideal split-Gabor** (w+ = [G]+, w− = [−G]+) = **the TARGET** | **0.9115** | **6.44** |
| ideal split-Gabor, NO threshold (`homeo=0`) | 0.0006 | — |
| ideal Gabor, **split ABLATED** (`split=0`) | 0.0173 | — |
| **untrained SUnits (seeds 0/1/2)** = **the FLOOR** | **0.3168** | **1.96** |

**THE FLOOR, STATED: 0.3168** (seeds 0/1/2: 0.311 / 0.457 / 0.183; untrained max **0.81**).

**The floor is HIGH, and that is a real property, not an artifact.** OSI is scale-free, so
once the response pathway WORKS a random 7×7 RF has genuine chance orientation structure and
scores ~0.32. Rung 5's floor was 0.0044 only because its cells were *blind* (DC-swamped),
not because they were unoriented. Rung 3's lesson applies verbatim — *"the floor is 0.103,
not 0 — `>0` was never evidence"*. **This is why the pre-registered design below is an
INTERACTION** (PROTOCOL §4: test the interaction, not the simple effect, when the
no-mechanism control is non-null) and why the gate is **CONJUNCTIVE** with responsiveness
(PROTOCOL §4: a mechanism must not pass by making itself inert — a cell that is
"selective" but silent is noise amplification, not a cell).

### SESOI, stated in advance

**10% of the measure's dynamic range**, matching rungs 3 and 5: floor 0.3168 → target
0.9115 ⇒ **SESOI = 0.0595 OSI**.

---

## 2. CONVERGENCE (PROTOCOL §2) — **THE GATE THAT STOPPED THE RUNG**

*"Before any experience/ablation arm is run, measure: does the rule settle? This single
check explains nine failed attempts. Run it FIRST."*

Formative input ONLY (the agent's own waves), seed 3000, drift = ‖Δw‖/‖w‖, 6 SUnits.

| Miller subtractive | 400 | 800 | 1600 | 3200 | 6400 |
|---|---|---|---|---|---|
| **η=5e-4** OSI | 0.2891 | 0.3080 | 0.2247 | 0.2776 | **0.2396** |
| drift | 0.0042 | 0.0049 | 0.0138 | 0.0642 | **0.4612** |
| clumpiness | 0.490 | 0.548 | 0.597 | 0.750 | **0.849** |
| peak/base | 1.54 | 1.54 | 1.50 | 1.56 | **1.43** |
| **η=1e-4** OSI | 0.2832 | 0.2990 | 0.2630 | 0.3249 | **0.3287** |
| drift | 0.0008 | 0.0007 | 0.0015 | 0.0035 | **0.0088** |
| clumpiness | 0.470 | 0.474 | 0.478 | 0.524 | **0.562** |
| peak/base | 1.55 | 1.57 | 1.54 | 1.63 | **1.54** |

| plain Oja | 400 | 800 | 1600 | 3200 | 6400 |
|---|---|---|---|---|---|
| **η=5e-4** OSI / drift / clump | 0.3433 / 0.0050 / 0.508 | 0.4133 / 0.0060 / 0.522 | 0.3961 / 0.0253 / 0.655 | 0.3760 / **0.6857** / 0.913 | **0.1667** / **1.9389** / **1.000** |
| **η=1e-4** OSI / drift / clump | 0.2897 / 0.0009 / 0.470 | 0.3095 / 0.0009 / 0.474 | 0.2959 / 0.0019 / 0.482 | 0.4150 / 0.0044 / 0.520 | 0.4488 / 0.0133 / 0.565 |

0 NaN everywhere.

### **BOTH of PROTOCOL §2's stop conditions fire at once**

1. **η=5e-4 NEVER CONVERGES.** Drift rises ~100× (0.004 → 0.461 for Miller; 0.005 → 1.94
   for Oja) and clumpiness runs to 0.85–1.00 — **clumpiness 1.000 means the entire RF has
   collapsed to ONE polarity: a uniform blob, not adjacent ON/OFF subregions.** OSI DECAYS
   (0.41 → 0.17). Any arm run here is measured at an arbitrary point on a runaway.
2. **η=1e-4 CONVERGES TO NOTHING.** Drift stays ≤ 0.009, but **OSI never leaves the
   untrained floor** (0.283 → 0.329, floor 0.3168, SESOI 0.0595) and **peak/base stays
   ~1.5 against the ideal's 6.44** — the cells never become responsive. That is "converges
   to death" in the only sense that matters here.

**No arm may be run on either. STOP.**

### The one thing per-channel centering DID fix (recorded, because it was measured)

The first cut used a single pooled `xbar`. Because ON and OFF are complementary
(`x_OFF = 1 − x_ON`), that pooled mean is **exactly 0.5 whatever the input** — but the wave
field is **sparse** (ON ~19.5% / OFF ~80.5% active), so every OFF synapse saw
`(x − 0.5) = +0.3` on average and every ON synapse `−0.3`. The rule had a **systematic
drift with nothing to oppose it**: every OFF weight saturated to `wmax`, every ON weight to
0, RF → uniform blob (clumpiness **1.000**, OSI decaying 0.40 → **0.167**). Miller & MacKay's
model never meets this because its ON/OFF layers are **symmetric by construction**; sparse
waves are not. Centering each pathway on its own mean (`Σ_ON dw = 0` and `Σ_OFF dw = 0`
independently) removed the systematic drift — clumpiness at η=5e-4 fell 1.000 → 0.849 and
the RF stopped collapsing (`test_the_effective_rf_is_signed_...` caught this independently
and now passes). **It did not rescue convergence**, and the rung still stops.

---

## 3. POSITIVE CONTROL (PROTOCOL §1) — the rule is **NOT** a null instrument

Rung 3's η was a null instrument and **only its positive control revealed it**. The
question, asked separately from the hypothesis: *given a PERFECTLY BIASED ensemble — ONE
orientation, shown over and over — can the rule grow an orientation-selective cell at all?*

This is the sharpest form of the test, because of VISION_PRIOR_ART.md's correction: *"the
average has no direction" is imprecise; the real argument is **ENSEMBLE DEGENERACY**, and
**on a biased ensemble, Oja works**.* A single-orientation ensemble is exactly where the
rule MUST succeed if it is capable.

**POSITIVE CONTROL — OUTCOME (seed 0, 1500 presentations at 0°, random phases):**

```
                          OSI      peak/base   pref bins (0 == 0 deg)          clumpiness
MILLER  eta=5e-4        0.8781      20.62      [0, 0, 0, 0, 0, 0]                0.718
MILLER  eta=1e-4        0.5262       2.90      [6, 6, 3, 0, 0, 0]                0.524
OJA     eta=5e-4        0.9455      3.2e+08    [0, 0, 0, 0, 0, 0]                0.720
OJA     eta=1e-4        0.5363       2.94      [6, 6, 3, 0, 0, 0]                0.524

references:  FLOOR 0.3168 (peak/base 1.96)   TARGET 0.9115 (peak/base 6.44)
```

**THE POSITIVE CONTROL PASSES.** At η=5e-4 both rules clear the floor by ~0.56 OSI (≈9×
the SESOI), become genuinely responsive (peak/base 20.6 vs the ideal's 6.44), segregate
ON/OFF (clumpiness 0.718 vs 0.5 intermixed), and — the conjunctive check that matters —
**every cell prefers the orientation it was actually shown**. So the machinery works: the
split + threshold + subtractive rule CAN build a signed, responsive, orientation-selective,
ON/OFF-segregated simple cell.

**Two honest provisos on this number, both load-bearing:**

1. **It is measured INSIDE the transient.** η=5e-4 at 1500 steps is before the runaway the
   convergence table shows at 3200–6400. So the positive control demonstrates **capability,
   not a stable fixed point** — exactly the distinction PROTOCOL §2 exists to enforce, and
   it is reported as capability only.
2. **Oja's `peak/base = 3.2e+08` is numerical divergence**, not a better result — the same
   `η·y² < 1` bound as rung 2's L0 failure and rung 5's NaNs.

### A PREDICTION OF MINE THAT BROKE — and the proviso is the informative part

I predicted **in advance** (recorded in `tools/build_vision_onoff_seed.py` before the run)
that **plain Oja would collapse to the uniform mode** and fail where Miller succeeded,
because Oja maximises the UNCENTERED second moment `E[(w·z)²] = Var(w·z) + (E[w·z])²`, and
the `(E[w·z])²` term (~24.5 at ‖w‖=1 for a 7×7 RF) swamps `λ_max` of the centered
covariance (~3–6).

**It did not hold: Oja also learned the shown orientation (0.9455).** The proviso that
broke: **my argument was correct for `y = act`, and the threshold invalidated its premise.**
Once `y = rate = max(act − theta, 0)`, `theta` has ALREADY removed the DC before Oja ever
sees it — so there is no mean term left for Oja to chase. **The threshold does not merely
enable the readout; it changes what the learning rule optimises.** That is a real
architectural fact I did not anticipate, and it means the Miller-vs-Oja contrast this seed
was designed around is **not established** — both rules behave alike here, and their
difference is untested.

### THE BUG THIS FOUND — a null arm that looked like a result

The first run of the positive control reported plain Oja at OSI 0.558 with **identical
numbers at η=5e-4 and η=1e-4**. That identity was the tell: **`oo_learn_oja` NEVER FIRED**
(`max |dw| = 0.000000`, `frac moved 0.000`) — its `where` guarded on `rate_step == r.step`
while `r` was **UNBOUND** in its `match`. The `subnorm=0` arm was silently **"no learning at
all"** dressed as "plain Oja", and its 0.558 was untrained chance structure.

This is the `vf_temporal_diff never fired` failure mode: **a rule that cannot fire fails
SILENTLY and reads as a result.** It is pinned by
`test_both_learning_rules_actually_fire`, and it is why every number above is accompanied by
a `max |dw|`.

---

# OUTCOME / DECISION

# **DECISION: the LAYER is BUILT; the DEVELOPMENT is *** NOT BUILT ***.**

**No confirmatory arms were run, and no confirmatory seeds were consumed.** Seeds
**8000–8999** are allocated to rung 6 in the ledger and remain **UNUSED and clean**. All
work above used seeds 0–2, 3000 and 7 — already burned. Running arms would have measured a
rule that either runs away (η=5e-4) or produces nothing (η=1e-4) on the very input the arms
would use: the error PROTOCOL §2 exists to prevent.

### What IS established (measured, gated, reproducible)

1. **THE SIGNED SIMPLE LAYER EXISTS, AND RUNG 5'S BLOCKER IS GONE.** Every weight stays
   non-negative (Dale holds, gated) **yet the effective RF `w⁺ − w⁻` takes both signs** —
   the thing rung 5 measured as impossible (`frac(w<0) = 0.0000`). The sign comes from the
   PATHWAY, exactly as in biology.
2. **A UNIT CAN NOW HAVE AN ORIENTATION-SELECTIVE RESPONSE: 0.004 → 0.9115.** Through the
   *identical* frozen probe on which rung 5's units scored 0.004, an ideal split cell scores
   **0.9115**. **The precondition that blocked rung 5 is removed** — this is the one thing
   rung 5 named as gating everything above V1.
3. **THE THRESHOLD, NOT THE SPLIT, IS WHAT MAKES THE RESPONSE SIGNED** (0.0006 → 0.9115,
   same weights). Measured, with the tonic-drive cause isolated (`Σw⁻ = 5.613` vs a ±2.3
   signal). This was **not** in the brief's design and is the rung's main architectural
   finding.
4. **THE MECHANISM IS CAPABLE** (positive control): from a biased ensemble it grows a
   responsive, ON/OFF-segregated cell preferring the orientation actually shown — inside a
   transient.
5. **THE FREEZE BUG IS FIXED AND GATED**, and it changes no committed result (rungs 1/2/4
   read weights with no stimulus presented, so no rule fires during their read-out).

### What is NOT established — the rung's negative

**Waves do not develop orientation selectivity in this layer.** On the formative input, OSI
never leaves the untrained floor (0.283 → 0.329 vs floor 0.3168, SESOI 0.0595) and the cells
never become responsive (peak/base ~1.5 vs the ideal's 6.44), while the larger η runs away
(drift → 0.46, clumpiness → 0.85). **The mechanism works on a biased ensemble and does
nothing on waves.**

### THE DIAGNOSIS — why, and it is NOT "the average has no direction"

Per VISION_PRIOR_ART.md's correction, the argument is **ensemble degeneracy**, and the
positive control isolates it: **the identical rule, at the identical η, on a BIASED ensemble
scores 0.878 and on waves scores 0.32.** The rule is not weak; **the wave ensemble is
degenerate for this readout.**

The structural reason, and it is specific to what was built here: **the complementary split
`x_OFF = 1 − x_ON` is itself degenerate.** Knowing the ON channel determines the OFF channel
*exactly*, so `C_ON,OFF(d) = −C_ON,ON(d)` identically at every distance — the two channels
carry **no independent correlation structure**. In Miller's model the ON/OFF segregation and
the oriented RF come precisely from the ON/OFF correlation functions having **different
spatial dependence** (from centre-surround RFs of different sizes), which is what breaks the
orientation symmetry. Our split has no such freedom: it is a sign flip, not a second
pathway with its own receptive field.

**That is the honest boundary of this rung: the ON/OFF *sign* is necessary (it removes rung
5's blocker) but not sufficient (it adds no correlation structure for waves to sculpt).**

## WHAT IS **NOT** CLAIMED (PROTOCOL §8)

- **NOT that rungs 1, 2 or 4 are wrong**, and **NOT** that the freeze bug touches them —
  their statistics are read off the WEIGHTS with no stimulus presented, checked above.
- **NOT that waves cannot develop orientation.** What is measured is that *this* split, with
  *these* rules, does not. The named next hypothesis (below) is untested.
- **NOT the Miller-vs-Oja contrast this seed was designed around.** Both rules behaved alike
  on the positive control, because the threshold removes the DC before either sees it. My
  in-advance prediction that Oja would collapse to the uniform mode **broke**, and the
  premise that broke it is reported above. `subnorm` remains an untested axis.
- **NOT anything from n>1 seeds.** The positive control and convergence are single-seed
  diagnostics (seeds 0, 3000), like rung 2's and rung 5's — dynamics checks, not hypothesis
  tests. **No inferential statistic is reported anywhere in this document, because no
  confirmatory arm was run.**
- **NOT that the positive control is a stable result.** It is measured inside the transient
  and demonstrates capability only.
- **NOT that `clumpiness` is a validated segregation statistic.** It is a model-free
  descriptive (fraction of 4-neighbour pairs sharing the sign of `w⁺ − w⁻`; 0.5 =
  intermixed) reported alongside OSI, never gated on.

## THE NAMED NEXT HYPOTHESES (NOT run, NOT built here)

Each needs its own pre-registration with its own mechanism-level hypothesis — **not a
parameter sweep**. η, `theta_rate`, `wmax`, the probe period and the RF are frozen.

1. **GIVE THE TWO CHANNELS INDEPENDENT CORRELATION STRUCTURE — the direct consequence of
   the diagnosis.** `x_OFF = 1 − x_ON` is a sign flip with no spatial freedom, so waves have
   no ON/OFF correlation structure to sculpt. Real ON and OFF cells have **centre-surround
   RFs of different sizes**, which is exactly what makes `C_ON,ON(d) ≠ −C_ON,OFF(d)` and
   what drives segregation in Miller 1994. **The trap to avoid: a hand-built DoG is the
   bolt-on error** (`substrate_rs/vision.py::lgn_pair` is exactly that, and is rejected —
   see below). The honest version is **retinal lateral inhibition as a RULE** over the
   `neighbour` edges the adapter already wires, so the centre-surround *emerges* and the
   correlation structure is grown, not handed over. This is the highest-value next step.
2. **LATERAL INTERACTIONS BETWEEN SUnits** — rung 4's `vm_burst_lateral` is the precedent in
   this tree, and VISION_PRIOR_ART.md notes LISSOM/GCAL get maps from **lateral interactions
   + WTA**, not from deflation. The simple layer has hard global WTA and nothing else.
3. **A stability regime for the subtractive rule.** η=5e-4 runs away and η=1e-4 is inert;
   the fix is a mechanism (bounded/decaying update, or GCAL's divisive normalisation *with*
   the threshold), **not** a search between 1e-4 and 5e-4.

## APPENDIX — `substrate_rs/vision.py`: evaluated, REJECTED for the mechanism

VISION_PRIOR_ART.md flagged it as "the top duplication risk" and asked for an explicit
verdict rather than a silent third implementation. It ships `lgn_pair(sigma_on, sigma_off)`,
`dog`, `v1_bank`, `complex_cell`, `hebbian_update`, `oja_update`. **None is fit for this
rung:**

- **`lgn_pair` / `dog`** are HAND-DESIGNED difference-of-Gaussian convolution kernels
  computed in numpy (`origin="dog"`). That is **a hand-built retina** — precisely the
  bolt-on error PROTOCOL §0 names and that Stage 1's six `designed:1.0` kernels were
  retracted for.
- **They are not an ON/OFF split at all.** A DoG's OUTPUT is *signed*. Feeding a signed
  channel in would **assume away the very thing rung 5 identified** (our channel is
  non-negative) and would break Dale's law rather than model it. The point is two
  NON-NEGATIVE channels whose DIFFERENCE is signed.
- **`oja_update`** is numpy over Image/Kernel nodes — a **learning rule in Python**
  (forbidden by CLAUDE.md), batch-averaged over patches, with no Synapse, no per-connection
  plasticity and no WTA. The graph-native Oja already exists twice (`oja_learn`,
  `vg_learn_kernel_oja`).

**Reused instead:** rung 5's calibrated probe (`domains/complex_cells.py`) **unchanged** —
its Gabor reference, rectification and period-4 anti-aliasing were themselves calibrated
against three instrument bugs, and swapping in `vision.py`'s second Gabor implementation
would silently re-open that calibration. **No third Oja and no third Gabor were written.**

`lgn_pair`'s *existence* is, however, evidence for named-next #1: the field builds ON/OFF
with centre-surround because the **sign flip alone is not enough** — which is what this rung
measured independently.

## APPENDIX — the vision Terms are NOT missing; the wheel diagnosis was wrong

VISION_PRIOR_ART.md §1.1 calls the stale wheel a **BLOCKER** and says `maturin develop` is
"a prerequisite before the vision floor can be evaluated at all". **Checked, and that is not
the situation.** There are **two** native binaries:

```
runners/dsl/python/substrate_rs/_native.abi3.so    Jul 16   <- FRESH, has ChangeDetect
/home/matt/.local/.../substrate_rs/_native.abi3.so Jul 13   <- STALE, raises UnknownTermType
```

Which one a test loads depends **purely on whether that test file prepends
`runners/dsl/python` to `sys.path`**. `test_vision_floor_migrated.py` does not, so it got the
stale one; `test_vision_complex_migrated.py` and `test_vision_waves_migrated.py` do, so they
got the fresh one. **`PYTHONPATH=runners/dsl/python pytest tests/test_vision_floor_migrated.py`
→ 7 passed.** The Terms are implemented and working; **no rebuild is needed**, and the 3
"ChangeDetect" failures are a path/packaging bug, not a missing implementation.

**This rung prepends the repo path** (rung 5's convention), so every number in this document
was measured on the fresh Jul-16 native. **The two-binary split is a live hazard worth
fixing centrally** — two agents can measure two different engines depending on import order
— but it is a shared-tree change while another agent is mid-run, so it is reported here
rather than made unilaterally.

**Vision bench baseline (pre-existing, on clean HEAD `b9b0bf9fd9`): 10 failed / 122 passed
under `pytest tests/ -k vision`.** This rung neither fixes nor breaks any of them; it adds
`tests/test_vision_onoff_migrated.py` (17 gates).
