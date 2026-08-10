# THE EYE'S CALIBRATION FRONT END — pre-registration

> ## AMENDMENT 1 (post-commit, pre-outcome) — the lid is OPTICS, not a neural switch
>
> *Recorded here rather than edited in silently: the pre-registration was
> committed at `26cb7c6be3`, and this amendment lands after it. Two corrections
> from the creator, in sequence, both of which I had wrong.*
>
> **(1) "A closed eye's photometry still works."** The version committed at
> `26cb7c6be3` gated every photometric rule on `eye_open`, on the reasoning that
> phase 0 must have "NO phototransduction". **That is biologically false.** The
> eyelid is translucent — photoreceptors transduce diffuse light long before eye
> opening. Eye opening does not switch phototransduction on; it delivers a
> **patterned image**.
>
> **The gate is REMOVED from all 5 photometric rules.** The claim it was
> enforcing — *waves do not calibrate the gain* — is TRUE and SURVIVES, but it
> was never the gate that made it true: it is **structural**. The photometric
> rules read `EyeCell.lum` (light); waves live on `RetinaCell.bursting`
> (endogenous activity); **no edge joins them**. Now gated as the real claim, and
> it passes: `test_waves_do_not_drive_the_photometric_path` runs tick-matched
> arms and waves move θ by **exactly 0.0**. `eye_open` is retained as DATA
> recording which regime the adapter presents; it gates nothing.
>
> **(2) "A closed lid does not give uniform illumination. It gives DIFFUSED
> illumination."** My first fix over-corrected into a second error — modelling
> the closed lid as a *constant field*. A lid is a **scatterer**: a spatial
> low-pass, like frosted glass. Coarse luminance structure survives (you can
> locate a window with your eyes shut); only fine detail is lost. Now modelled as
> `eye_world.lid_diffuse()` (separable Gaussian, reflecting edges) — mechanical
> optics, the adapter's business, exactly as `WaveWorld` states the retina's
> geometry. Gated: diffused is **not** uniform (sd > 0), **not** a blackout (the
> level survives), and loses the detail (sd 0.2946 → 0.0205).
>
> **This is not cosmetic — it dissolves this rung's worst null instrument (§3.3).**
> A per-cell reference adapted to a *static scene* memorises and cancels it
> (every cell → `resp = μ` exactly; the image is ERASED). Light through a closed
> lid is **diffused**, so θ calibrates against a COARSE field it can never
> memorise the detail of. Measured, on burned seeds, with θ calibrated behind the
> lid and never having seen a sharp image:
>
> | arm | probe response | patdiff k=100→1000 | k=100→10000 | floor |
> |---|---|---|---|---|
> | **LOG** | mean 0.1600, max 0.5960, sd 0.1950 | **0.005982** | **0.006587** | 0.582486 |
> | **LINEAR** | max 1.0000 (saturated) | **1.000000** | **1.000000** | 1.000000 |
>
> The log arm reads a held-out sharp image **invariantly across two decades at
> 1.1% of floor**, having calibrated only on diffused light. And the probe
> response is *richly structured* (sd 0.1950) precisely because θ absorbed the
> coarse field and the DETAIL is what remains — **"sight arrives as a
> perturbation of an already grounded structure", measured, not asserted.**
>
> **Status of these numbers: CALIBRATION-grade (burned seeds 0/1/7), NOT
> confirmatory.** The pre-registered confirmatory below runs the
> adapt-to-ensemble protocol as specified and is reported as run — changing the
> protocol after commit would be exactly the metric surgery §5 forbids. **The
> closed-lid protocol is the better one and is named here as the design for the
> NEXT pre-registration**, not retrofitted into this one.

*Written and committed BEFORE the confirmatory run (VISION_PROTOCOL.md §3). Every
number in the CALIBRATION sections below was measured on already-burned seeds
(0–13, the ledger) before this file was written; the confirmatory block
(11000–11999) is untouched at the time of writing.*

**Engine:** `95167c01b7b3 @ runners/dsl/python/substrate_rs/_native.abi3.so`
(§10; resolved via the `substrate_rs.pth` pointer — this worktree symlinks the
one artifact rather than copying it).
**Commit:** `28dd46e2dc` (worktree branch off `gamma-substrate/developmental-vision`).
**Bench baseline in this worktree:** `pytest tests/ -k vision -q` →
**155 passed, 0 failed, 1 skipped**.

> Reconciliation with the protocol's stated 156/0: a fresh worktree lacks the
> **gitignored `data/`** slab, which is not a code fact. Without it, 5 tests
> ERROR (`vision_corpus.bsds_crops` → empty array) and 2 more FAIL — the latter
> being `test_meaning_inference_migrated::…_provisional_…`, which `-k vision`
> collects only because "pro**vision**al" contains the substring, and which are
> not vision tests at all. With `data/` symlinked, all 7 resolve: 155 passed +
> 1 skipped = the 156 collected. **No committed claim moves.**

---

## 0. What this is, and the correction that reshaped it

This is not a rung. It is a standalone artifact: `VISION_PRIOR_ART.md` establishes
there is **no live, open-source, Python, structure-growing eye** (ISETBio is
MATLAB-only and stops at photocurrent; open-retina is a CNN with no structure to
grow; COREM/convis/deep-retina are dead or unbuildable). The circuits exist as
equations. This builds the graph-resident one.

**The creator's correction, received before any confirmatory run and folded in
whole:**

> *Waves cannot calibrate photometric response to external illumination before
> phototransduction works. They primarily establish TOPOLOGY, CORRELATION,
> TIMING and PATHWAY RELATIONSHIPS. Later visual input calibrates GAINS and
> ENVIRONMENTAL STATISTICS.*

So the eye has **two phases, calibrating different things at different times**:

| | phase 0 — pre-visual (lid closed) | phase 1 — the lid opens |
|---|---|---|
| input | endogenous waves **+ diffused light through the lid** | the patterned image |
| calibrates | **relational**: topology, correlation, timing, shared sources | **photometric**: gains, environmental statistics |

**SUPERSEDED BY AMENDMENT 1 (above), and the amendment is the correct text.**
As committed at `26cb7c6be3` this section said `eye_open=0` gates every
photometric rule so that phase 0 has "no phototransduction". **That is
biologically false — a closed eye's photometry still works** (the lid is a
translucent scatterer, not a blackout), and the gate has been REMOVED. The
claim it was reaching for — *waves do not calibrate the gain* — is true and
survives **structurally**: the photometric rules read `EyeCell.lum`, waves live
on `RetinaCell.bursting`, and no edge joins them (gated:
`test_waves_do_not_drive_the_photometric_path`, waves move θ by exactly 0.0).
The stale claim is left visible here rather than rewritten, because the
correction is part of the record.

**Which edges are PHYSICS and which are KNOWLEDGE** — the line the whole build
turns on, stated as required:

- **PHYSICS (legitimately wired by the adapter):** the retina's cells and its
  4-neighbourhood (rung 1's). Photoreceptors *are* physically adjacent; that is
  the sheet's geometry, not something the agent could know or fail to know.
- **KNOWLEDGE (must be EARNED):** **which retinal cells a downstream unit listens
  to — retinotopy.** This is what rung 4 hand-wired (`domains/cortex_sheet.py`)
  and then measured back out of its own result ("retinotopic RF overlap —
  **anatomy the adapter wires** — accounts for most of the raw smoothness";
  ablated arm −13.25 of −20.16). Phase 0's `w_pre` is therefore wired
  **deliberately diffuse**: every retinal cell to every unit, small random
  weights, no locality, no spatial prior. If a map appears, the graph made it.

---

## 1. CONVERGENCE (PROTOCOL §2) — run first, and it decided the scope

### 1.1 Phase 1 — the receptor + the adaptive reference: **CONVERGENT + USEFUL**

Static scene, mean response target μ=0.024, out to 40 000 steps
(`scripts/eye_convergence.py`, `results/eye_convergence.log`):

| arm | mean resp @40k | θ @40k | drift @40k | verdict |
|---|---|---|---|---|
| LOG, k=1 | **0.024000** | 0.4359 | **0.00000** (from 6.4k) | converged |
| LOG, k=1000 | **0.024000** | 6.2690 | **0.00000** (from 12.8k) | converged |
| LINEAR, k=1 | **0.024000** | 0.5805 | **0.00000** | converged |
| LINEAR, k=1000 | 0.738877 | 361.03 ↗ | **0.23933** | **NOT converged** |

**This is itself a result, and it is the deepest one here.** The log receptor
converges at *every* illumination; the linear receptor **fails to converge at
high illumination** within 40k. The reason is exactly the theory: in log space an
×1000 change is an *additive* ln(1000)=6.91 the reference reaches quickly; in
linear space it is a *multiplicative* 1000× and θ must travel ~1000× further at a
rate bounded by λ(rmax−μ). **Weber–Fechner is not only about dynamic range — it
is what makes the calibration TRACTABLE.**

### 1.2 Phase 1 — the learning layer: convergent, and ALIVE only after ~20k

`||w||/||w0||` with `meanrate` and `max|dw|` reported at every checkpoint
**precisely so an inert arm cannot masquerade as a stable one** (§4). See §3.

### 1.3 Phase 0 — retinotopic refinement: **DOES NOT CONVERGE** (measured)

Waves, 4 units, out to 32k (`results/eye_phase0_convergence.log`):

| step | mean spread | drift |
|---|---|---|
| 4 000 | 6.3986 | 0.235 |
| 8 000 | 6.3553 | 0.226 |
| 16 000 | 6.3546 | 0.276 |
| 24 000 | 6.3425 | 0.238 |
| 32 000 | 6.3515 | 0.244 |

**Drift does not decrease** (~0.24 throughout) and spread sits at the diffuse
floor (6.52). Under PROTOCOL §2 that is *"never converges ⇒ the scaffold is a
TRANSIENT and every arm is measured at an arbitrary point on a decay curve"* —
**so phase 0 runs NO confirmatory arms and burns NO confirmatory seed**, exactly
as rungs 5 and 6 correctly did.

**The activity-matched comparison, for the record and NOT as a result**
(`results/eye_phase0_main.log`, 6 units, 32k, clock fixed):

| arm | mean spread @32k | drift @32k |
|---|---|---|
| WAVES (spatially correlated) | 6.3464 | 0.257 |
| SHUFFLED (same burst COUNT, correlation destroyed) | 6.5192 | 0.188 |

The waves arm does sit slightly off the floor where the activity-matched control
sits exactly on it (6.35 vs 6.52) — but **this is measured inside a transient and
is not reported as a result**. Scale it honestly: 0.17 against a 6.52 dynamic
range is **2.6%**, while the positive control reaches 2.00, i.e. **69%** of the
range. This is rung 3's situation restated — *"every effect is ≤2.3% of the
dynamic range and none is meaningful"*.

> **The shuffled control had to be built, because rung 1's `propagate=0` is
> confounded FOR THIS CLAIM.** Measured: with the wave circuit off, the same
> ignition leaves ~1 cell bursting per step against a wave's ~30 — so the arms
> differ in the QUANTITY of activity as well as its correlation, and a difference
> between them would not isolate co-firing-carries-WHERE. Rung 1's control was
> right for rung 1's claim ("structure from entropy") and is wrong for this one
> (§6: controls must correspond to the actual experiment; §4: re-derive what each
> arm MEANS after every change).

**Diagnosis, and it is the ladder's own root cause a fourth time.** A fixed patch
is learned (positive control: spread 2.00, centre exact) because the *same* cells
fire every step, so the winner reliably re-wins and its RF commits. Waves ignite
at **uniformly random locations**, so the ensemble over wave positions is
**isotropic** — and Oja's attractor is the mean of that ensemble, which is
uniform over the sheet, i.e. **diffuse**. WTA breaks the symmetry between units
*momentarily*, but at fixed η the winner is dragged to wherever it last won and
never commits: hence drift ~0.24 that never settles. *"A contraction to the mean
of an isotropic distribution is the mean"* — rungs 3 and 5's result, now at the
retinotopy layer. **The named next step is a mechanism, not a sweep:** η
annealing (Kohonen converges precisely by η→0) or a neighbourhood function
(rung 4's `vm_burst_lateral` is the precedent). Either needs its own
pre-registration.

The non-convergence has a named mechanism, not a mystery: **WTA at a fixed
learning rate has no fixed point.** One unit's weights jump on each step it wins,
so the population perpetually jitters around the attractor. Kohonen anneals η→0
to converge; this rule does not. That is a mechanism-level fact about the rule as
built, and a fix is a NEW pre-registration, not a parameter search.

---

## 2. CALIBRATION (PROTOCOL §1) — every measure, on floor + ideal + duration

### 2.1 RF localisation (`rf_spread`), the phase-0 statistic

| input | spread | role |
|---|---|---|
| uniform diffuse 16×16 | **6.5192** | FLOOR |
| uniform random weights | **6.4676** | FLOOR (random *is* diffuse) |
| σ=1.5 Gaussian blob | 2.1213 | ideal, localised |
| single cell | **0.0000** | ideal, maximal |

Dynamic range [0, 6.52]. **POSITIVE CONTROL** — bursts pinned to a fixed 5×5
patch, the input a working retinotopy rule *must* learn
(`results/eye_phase0_poscontrol.log`): the winning unit reaches spread **2.00**
(ideal for that patch ≈1.63) with centre **(5.0, 5.0)** = the patch centre
exactly, stable from 2k to 12k. **The mechanism is NOT a null instrument.** The
three losing units stay diffuse, which is correct WTA behaviour for a single
fixed stimulus location.

> The positive control also **caught a fatal harness bug**: the phase-0 rules
> originally stamped against the *Retina's* clock, but `WaveWorld.step()` ticks
> internally, so `act_step` was already stamped before the adapter could present
> any input and `ph0_wunit_act` never re-fired. The fixed patch never reached the
> units at all (spread 6.54, untouched). The `shuffle` control was silently inert
> for the same reason. Rules now stamp against the **Eye's own clock**, and the
> adapter presents input *before* advancing it. **Every phase-0 number predating
> that fix is void and is not reported as a result.**

### 2.2 Drift statistics (`diffusion_exponent`), the SAW's measure

| input | α | role |
|---|---|---|
| ordinary random walk (20k steps) | **≈1.0** (gate: \|α−1\|<0.10) | IDEAL — Brownian by construction |
| straight line | **≈2.0** (gate: \|α−2\|<0.05) | IDEAL — perfectly persistent |

Both gated in `tests/test_vision_eye_migrated.py`. An instrument that cannot read
α=1 off a walk that *is* α=1 could not be trusted with α=1.32.

### 2.3 Anisotropy — the cardinal-axis instrument

| input | anisotropy | role |
|---|---|---|
| isotropic 8-direction walk | <0.10 | FLOOR |
| walk pinned to one direction | >0.90 | IDEAL artifact it exists to catch |

### 2.4 Duration confound

Phase 1's reference reaches drift **exactly 0.00000** and holds it from 6.4k to
40k (§1.1), so the phase-1 statistics are read at a true fixed point and are not
duration-confounded. Phase 0 **is** duration-confounded (drift ~0.24, never
settling) — which is why it is stopped rather than measured.

---

## 3. Two mechanism-level corrections the measurements forced

Both are recorded because each was a measured failure, not a preference, and each
would have produced a false positive.

**(a) The activation function must SATURATE — and it is required by μ, not chosen.**
μ=0.024 is GCAL's *target average activity*, and a target average is only
meaningful as a fraction of a maximum; taking their target rate while leaving the
rate scale unbounded is an incoherent transcription of one equation. `rmax`=1.0
*is* that scale. **Measured cost of omitting it:** θ rises ∝ a response that can
spike arbitrarily (5.93) but falls at only λμ=2.4e-4/step, so one early spike
ratchets θ far above the drive and silences the cell for ~13 500 steps. At the
unit this silenced the **θ-OUTSIDE arm completely** — meanrate 0.000000,
max|dw| 0.000e+00 — and it then looked *stable* (||w||/||w0|| pinned at 0.6188
out to 6400) while merely being **INERT**. I nearly reported a 33× stability win
over BCM's 0.0187. **That is exactly PROTOCOL §4's "a mechanism could pass by
making itself inert", and it is retracted.**

**(b) Phase 0 needs GCAL's L1 normalisation (Σᵢwᵢⱼ = 1), which is part of GCAL,
not an addition to it** (§2.4; §2.5 records it is in all four of their models
including the baseline). **Measured cost of omitting it:** units compete on TOTAL
WEIGHT rather than on MATCH — the unit holding the most weight won 79/200
regardless of *where* the wave was, and every RF stayed at the diffuse floor
(6.52 vs 6.52). With Σw=1 the drive is a weighted average, so a unit can only win
by its weight pattern matching the wave's location. It removes the saturation for
free (act ≤ 1 = rmax by construction).

---

## 4. THE CONFIRMATORY RUN — phase 1 only

**Seeds: 11000–11999** (fresh, appended to the ledger, never used for anything).
Phase 0 burns none: it stopped at the convergence gate (§1.3).

n is fixed in advance at **n=20 seeds per arm** by a variance pilot on burned
seeds 0–13. Unit of analysis is **the SEED**, never the unit (§4) — units within
a run share input and compete under WTA, so they are not independent; per-seed
values are the mean over that seed's units.

### H1 — ILLUMINATION INVARIANCE (the decisive one)

#### The protocol, and the design error the calibration caught

**A per-cell reference on a STATIC scene erases the image.** Measured: adapt to
one fixed scene for 20 000 steps and every cell converges to `resp = 0.024`
*exactly* — `mean_resp = max_resp = 0.024000`, sd 0. The homeostat drives each
cell to μ individually, so at the fixed point the response carries **no
information about the scene at all**. Both `patdiff` and the floor came back
**0.00000**: perfect "invariance" by total information destruction — the purest
null instrument in this rung, and it would have passed a naive gate.

GCAL never meets this because its input is a **stream**: η̄ is a long-run average
over many patterns, not a memorised copy of one. And the creator's correction
names the fix exactly — phase 1 calibrates **gains and ENVIRONMENTAL
STATISTICS**, and light then arrives as a **perturbation**. So the protocol is:

1. **ADAPT** to the environment's statistics at illumination k — a *stream* of
   scenes, 20 000 steps (fixed by §1.1, not tuned per arm);
2. **FREEZE** — `frozen=1` gates every learning AND adaptation rule (verified
   max|dθ| = max|dw| = 0.000e+00; rung 5 lost three poolings to a fake freeze);
3. **PROBE** with one held-out test scene at k;
4. read the response **pattern**.

**Statistic:** `patdiff(k) = max_i |resp_i(k) − resp_i(k=100)|` over the sheet.

**Two arms, selected as DATA** (`logr`), everything else identical:
`logr=1` (Weber–Fechner) vs `logr=0` (linear control).

**Range:** k ∈ {100, 1000, 10000} — two decades, **all above the dark light
`i0`=1**, per the regime restriction declared below.

**FLOOR:** `patdiff` between two *different* probe scenes at the same k. This is
what "the response changed" looks like when the input really did change, and it
is the scale everything is measured against.

**SESOI = 10% of the floor**, fixed in advance.

**Pilot (burned seeds 0/1/7, `results/eye_pilot.log` + the adapt-freeze-probe
calibration):** LOG patdiff 0.00093 (k=1000) / 0.00103 (k=10000) against a floor
of 0.21804 → SESOI = 0.0218. LINEAR patdiff 1.00000 / 1.00000 against a floor of
1.00000. The effect is ~970×, so **n is not variance-limited**; n is fixed at
**12 seeds per arm**, which is comfortably powered for an effect this size and is
set here, before the confirmatory run.

**Decision rule:** invariance is claimed for the log arm only if
`patdiff < SESOI` on **every** k, **AND** the linear arm's patdiff exceeds SESOI
(a conjunctive gate — §4 — so the log arm cannot pass by the measure being
insensitive). A null in either direction is reported as measured. **Two-sided:**
if the linear arm were also invariant, the log receptor buys nothing and the
theory's central claim is wrong at this scale.

**Regime restriction, declared in advance:** the receptor is `x = ln(I + i0)`,
exactly logarithmic only for `I >> i0`, and *linear by construction* for
`I << i0` — that is what a dark light IS. Invariance is predicted **only above
`i0`** and is tested there. This is a property of the mechanism stated before the
run, not a regime chosen after seeing a result.

**Restriction, stated in advance:** the receptor is `x = ln(I + i0)`, exactly
logarithmic only for `I >> i0`. Invariance is tested **across decades above the
dark light** (k ∈ {100, 1000, 10000}); at `I ≈ i0` the receptor is *linear by
construction* and invariance is NOT predicted there. This is a property of the
mechanism, declared before the run — not a regime chosen after seeing a result.

### H2 — WEBER–FECHNER

**Statistic:** slope of mean drive vs ln I over ≥3 orders of magnitude
(k ∈ {1e2…1e6}, four decades, all above `i0`), with `homeo=0` so the receptor is
measured and nothing else. **Prediction: slope = 1.000 ± 0.05** for `logr=1`;
the `logr=0` arm passes illumination through unchanged. Deterministic given the
receptor — no seeds consumed. The crossover to the linear regime below `i0` is
gated as a *predicted* property, not an excuse.

### H3 — ENGBERT DRIFT STATISTICS

**Statistic:** α_short (lags 1–10) and α_long (lags 10–50), vs Engbert 2011's
model α_s=1.32±0.02 / α_l=0.71±0.06 (experiment 1.38±0.05 / 0.79±0.11).

**CONJUNCTIVE gate** (§4 — a mechanism must not pass by making itself inert):
**α_short > 1 AND α_long < 1 AND α_short > α_long.** Straddling α=1 is the whole
signature; α=1 is the memoryless Brownian null that `gaze_walk` produces across
epochs. Plus **anisotropy < 0.25** — §3.2's explicit caution that a deterministic
4-connected argmin is a cardinal-axis artifact.

**Ablation as DATA:** `saw_lam=0` removes the potential. §3.2 says
*"self-avoidance makes the persistence; the potential makes the antipersistence"*,
so the prediction is that α_long rises above 1 with the potential gone while the
walk still moves. **Verifying the ablated control is actually null**, as required.

### H4 — θ OUTSIDE (GCAL) vs θ INSIDE (BCM)

**Statistic:** `||w||/||w0||` at 40 000 steps (burn-in ≥20k fixed by §1.2 —
inside the measured inert window the comparison is meaningless).

**CONJUNCTIVE gate, and this is the lesson of §3(a):** an arm counts as stable
only if it is **ALIVE** — `meanrate > 0` **AND** `max|dw| > 0`. A frozen arm is
not a stable one. Both arms carry the **identical** transfer function (same
rectification, same `rmax`); they differ in exactly one respect: where θ sits.

**Prediction:** θ-outside retains structure while θ-inside (BCM) annihilates,
because θ-outside cannot flip dw's sign (§2.3). **Proviso that would break it:**
if θ-outside is stable *only* by being inert, the prediction is not confirmed but
refuted — which is precisely how the first attempt failed.

### NOT TESTED — declared

**Atick & Redlich's SNR surround shift is NOT attempted.** It needs a
centre-surround, i.e. lateral inhibition, which is **rung 7's file**
(`seeds/vision_lateral.json`). Building a second one here would duplicate a
concurrent agent's work and violate §11.4. Named, not claimed.

---

## 5. Predictions, in advance, with provisos

1. **H1 will HOLD, and I predict it decisively:** the log arm's patdiff stays
   under ~1% of the floor across two decades; the linear arm's runs at ~100% of
   it. *Provisos that would break it:* (a) if the ADAPT stream's statistics
   differ enough between k levels that θ lands somewhere non-corresponding, the
   log arm's patdiff would rise — I predict it does not, because ln shifts the
   whole ensemble by exactly ln k and θ tracks that shift additively; (b) if the
   probe scene drives cells into `rmax` saturation the pattern clips and
   invariance breaks at the top of the range — the pilot's max response was
   0.2180, well below 1.0, so I predict no clipping in the log arm. **The linear
   arm's max response is 1.0000 = saturated**, which is itself part of why it
   fails.
2. **H2 will hold**, slope 1.000 above `i0`. This is close to an identity given
   `x = ln(I + i0)`; it is a gate on the implementation, not a discovery, and is
   reported as such.
3. **H3 will hold** — already observed on burned seeds (α_s 1.099, α_l 0.785,
   anisotropy 0.021). *Proviso:* α_short 1.099 is **well below** the paper's 1.32.
   I do **not** predict quantitative agreement; I predict only the sign structure
   (straddling 1). The shortfall is likely the Gumbel temperature adding
   diffusive randomness, and `temp` is **frozen** — tuning it to reach 1.32 would
   be exactly the parameter search this protocol forbids.
4. **H4 will hold** — but this is the prediction I hold most loosely, because its
   first version was an artifact (§3a). The honest statement: I predict BCM
   annihilates; I am *not* confident θ-outside retains *useful* structure rather
   than merely surviving.

## 6. What this does NOT claim

- **No biology is licensed.** That a mechanism reproduces a statistic does not
  make it the mechanism biology uses (§8; the verified research refuted the
  Hebbian-vs-sparsity question 0–3).
- **Oja and normalisation are REDISCOVERIES**, cited, not claimed: GCAL/LISSOM
  have used the L1 form since the 1990s (§2.4).
- **Phase 0 is NOT BUILT.** Retinotopic refinement from waves does not converge.
  The mechanism is proven capable by its positive control (spread 2.00 at the
  right centre) — that is CAPABILITY, not a fixed point, exactly the distinction
  rung 6 drew.
- **No map topography, no ON/OFF, no lateral inhibition, no complex cells.**
- The SAW is a drift model. **It is not a claim about what the drift is FOR** —
  Rucci's whitening claim is untested here.

---

# OUTCOME — appended verbatim after the ONE confirmatory run

**All four pre-registered hypotheses CONFIRMED (H1, H2, H3, H4). Phase 0 NOT
BUILT and stopped at the convergence gate, burning no confirmatory seed.** Every
number below is verbatim from `results/eye_confirm.log`. No test was added, no
test was dropped, nothing was re-run, and no measure was changed after seeing a
result.

**Engine `95167c01b7b3`. Pre-registration committed `26cb7c6be3` BEFORE the run.
Confirmatory seeds 11000–11999, n=12, `scripts/eye_confirm.py`,
`results/eye_confirm.log`. Worktree bench: `pytest tests/ -k vision -q` →
175 passed / 0 failed / 1 skipped (baseline 155+1; +20 = exactly the new eye
gates, zero regressions).**

## H1 — ILLUMINATION INVARIANCE: **CONFIRMED**, and it is the decisive one

```
  --- LOG: FLOOR mean=0.20788 sd=0.01024 -> SESOI=0.02079
  --- LOG: patdiff(k=1000)  mean=0.00092 sd=0.00008 CI95=[0.00087, 0.00096] = 0.44% of floor
  --- LOG: patdiff(k=10000) mean=0.00101 sd=0.00009 CI95=[0.00096, 0.00106] = 0.48% of floor
  --- LINEAR: FLOOR mean=1.00000 sd=0.00000 -> SESOI=0.10000
  --- LINEAR: patdiff(k=1000)  mean=1.00000 sd=0.00000 CI95=[1.00000, 1.00000] = 100.00% of floor
  --- LINEAR: patdiff(k=10000) mean=1.00000 sd=0.00000 CI95=[1.00000, 1.00000] = 100.00% of floor
```

**Both halves of the conjunctive gate pass.** The log arm is ~20× below SESOI at
every k (0.44%/0.48% of its own floor); the linear arm is at **100% of floor** —
it shifts by its ENTIRE dynamic range — which is what proves the measure is not
merely insensitive. **~1000× separation, CIs nowhere near overlapping.**

**The creator's theory, measured:** `log(a) − log(b) = log(a/b)`. An illumination
change is an additive constant in log space, the reference subtracts it, and the
RATIOS survive. In linear space the same reference cannot undo a multiplicative
gain. *There is no view from nowhere — and the eye is what establishes the
reference the view is taken from.*

## H2 — WEBER–FECHNER: **CONFIRMED**, prediction held exactly

```
     LOG: drive vs ln(I) slope = 0.9991   drives=[ 4.615  6.909  9.21  11.513 13.816]
  LINEAR: drive vs ln(I) slope = 91149.7259   drives=[1.e+02 1.e+03 1.e+04 1.e+05 1.e+06]
```

Predicted in advance: **1.000 ± 0.05**. Measured **0.9991** over four decades.
The per-decade step is **ln(10) = 2.303** to three decimals (2.294, 2.301, 2.303,
2.303). As pre-registered, this is a **gate on the implementation, not a
discovery** — it is close to an identity given `x = ln(I + i0)` — and it is
reported as such. The declared regime restriction held: the receptor is linear
below `i0` (gated), logarithmic above it.

## H3 — ENGBERT DRIFT STATISTICS: **CONFIRMED**, all four conjunctive conditions

```
  SAW (full)                         alpha_short: mean=1.1553 CI95=[1.1445, 1.1662]
  SAW (full)                          alpha_long: mean=0.7590 CI95=[0.7244, 0.7935]
  SAW (full)                          anisotropy: mean=0.0116 CI95=[0.0100, 0.0131]
  ABLATED (saw_lam=0, no potential)  alpha_short: mean=1.1944 CI95=[1.1837, 1.2052]
  ABLATED (saw_lam=0, no potential)   alpha_long: mean=1.1301 CI95=[1.0855, 1.1747]
  ABLATED (saw_lam=0, no potential)   anisotropy: mean=0.0169 CI95=[0.0149, 0.0188]
```

**α_short > 1** ✓ (persistent) **AND α_long < 1** ✓ (antipersistent) **AND
α_short > α_long** ✓ **AND anisotropy < 0.25** ✓ (0.0116 — twenty times under the
gate; the cardinal-axis artifact §3.2 warns about is absent).

| | measured | Engbert model | Engbert experiment |
|---|---|---|---|
| α_short | 1.1553 [1.1445, 1.1662] | 1.32±0.02 | 1.38±0.05 |
| α_long | **0.7590** [0.7244, 0.7935] | 0.71±0.06 | **0.79±0.11** |

**α_long lands inside the published experimental range.** α_short is **below**
the paper's 1.32 — **exactly the proviso registered in advance**: I predicted the
sign structure (straddling α=1), *not* quantitative agreement, and named the
Gumbel temperature as the likely cause. `temp` was **frozen**; tuning it to reach
1.32 would be the parameter search the protocol forbids.

**THE ABLATION CONFIRMS THE MECHANISM, and the control is non-null in the
PREDICTED direction.** §3.2: *"self-avoidance makes the persistence; the
potential makes the antipersistence."* Remove the potential and **the
antipersistence dies** (α_long 0.7590 → 1.1301, CIs entirely disjoint) while
**the persistence survives** (α_short 1.1553 → 1.1944, still > 1). The two halves
of the signature have two different causes, and each was ablated onto its own.

## H4 — θ OUTSIDE (GCAL) vs θ INSIDE (BCM): **CONFIRMED**, and BOTH ARMS ALIVE

*(This section supersedes the "INCOMPLETE at commit time" entry: the BCM arm
landed after that commit and the run is now complete. It is appended, not
rewritten, and no number changed — only arms that had not yet finished.)*

```
  --- theta OUTSIDE (GCAL)    ||w||/||w0||: mean=0.924483 CI95=[0.921541, 0.927426]
  --- theta OUTSIDE (GCAL)        meanrate: mean=0.023974 CI95=[0.023944, 0.024004]
  --- theta OUTSIDE (GCAL)         max|dw|: mean=0.021177 CI95=[0.020423, 0.021931]
  --- theta OUTSIDE (GCAL)   ALIVE (rate>0 AND dw>0 on every seed): True
  --- theta INSIDE (BCM)      ||w||/||w0||: mean=0.025071 CI95=[0.023151, 0.026992]
  --- theta INSIDE (BCM)          meanrate: mean=0.042995 CI95=[0.041984, 0.044005]
  --- theta INSIDE (BCM)           max|dw|: mean=0.012529 CI95=[0.009420, 0.015637]
  --- theta INSIDE (BCM)     ALIVE (rate>0 AND dw>0 on every seed): True
```

**θ-outside retains 0.924483; θ-inside annihilates to 0.025071. A 36.9×
separation, CIs nowhere near overlapping.** BCM's 0.025 is the same annihilation
this tree measured before (0.004, same order); θ-outside sits at μ=0.024 to four
decimals — homeostatically regulated, exactly as designed.

**THE CONJUNCTIVE GATE IS WHAT MAKES THIS A RESULT RATHER THAN A REPEAT OF THE
RETRACTED ARTIFACT.** `ALIVE = True` **on both arms, on every seed**: both are
firing and both are still moving weight (max|dw| 2.1e-2 and 1.3e-2). This is a
comparison between two **live** rules. The first attempt's 33× "win" was an
inert arm's frozen weights (meanrate 0.000000, max|dw| 0.000e+00) and was
retracted; the ≥20k burn-in §1.2 forced, and the `rmax` saturation §3(a) forced,
are jointly why the same comparison is now interpretable.

**VISION_PRIOR_ART.md §2.3's structural prediction is confirmed:** θ on the
activation function cannot flip Δw's sign and does not annihilate; θ inside the
rule gates the sign and does. **Same variable, opposite placement, opposite
outcome** — and the arms are otherwise identical, including the transfer
function (§3(a): if only one arm saturated, the contrast would confound
placement with the presence of a bound).

**The prediction held, and so did its proviso.** §5.4 predicted BCM annihilates
while holding the θ-outside half *loosely*, with the explicit proviso: *"if
θ-outside is stable only by being inert, the prediction is not confirmed but
refuted."* That proviso was tested rather than assumed — and did not fire.

## The headline that was not in the design

**Weber–Fechner is what makes the calibration TRACTABLE, not merely what widens
the range.** The log receptor converges at every illumination (drift EXACTLY
0.00000, held 6.4k→40k, at k=1 AND k=1000); the linear receptor **never
converges at high illumination** (θ still climbing at 40k, drift 0.239). In log
space an ×1000 change is an additive ln(1000)=6.91 the reference reaches; in
linear space θ must travel 1000× further at a rate bounded by λ(rmax−μ). The
linear arm's failure is not that it is non-invariant — it is that **it cannot be
calibrated at all**.

## What this does NOT claim

- **Phase 0 is NOT BUILT.** Retinotopic refinement from waves does not converge
  (drift ~0.24 flat; spread 6.35 vs a 6.52 floor). Its positive control reaches
  spread 2.00 at the exact patch centre, so the mechanism is CAPABLE — that is
  capability, not a fixed point, exactly the distinction rung 6 drew.
- **No biology is licensed.** Reproducing a statistic does not make this the
  mechanism biology uses.
- **Oja and L1 normalisation are REDISCOVERIES**, cited (GCAL/LISSOM, 1990s).
- **H2 is an identity check**, not a finding.
- **No lateral inhibition, no ON/OFF, no map topography, no complex cells.**
  Atick & Redlich's SNR surround was declared out of scope (rung 7's file).
- **The SAW is a drift model, not a claim about what drift is FOR** — Rucci's
  whitening claim is untested here.
- **H1 was measured with the adapt-to-ensemble protocol.** The closed-lid
  (diffused) protocol of Amendment 1 is better and is named for the next
  pre-registration, not retrofitted into this one.
