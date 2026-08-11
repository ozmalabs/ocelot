# RUNG 3B — THE MEAN AS A REPELLER: bistable plasticity for direction selectivity

*Everything above the OUTCOME section was written and committed BEFORE the
confirmatory run. Binding: `VISION_PROTOCOL.md`. This is a NEW pre-registration
with a NEW mechanism-level hypothesis, as `VISION_RUNG3_PREREG.md` requires —
NOT a re-run and NOT a parameter search: η=2e-3, P1=P2=1600, `max_delay`=3 and
`delay_tol`=0 are inherited FROZEN from rung 3 and are not touched.*

## What rung 3 measured, and why no parameter of it is worth sweeping

Rung 3 was **NOT BUILT** (n=100, fresh seeds 4000-4099): H1a `normal − dark`
−0.0035 p=0.09 FAIL; every effect ≤2.3% of the 0.489 dynamic range; two of them
p=0.0001 and scientifically negligible. **Neither waves NOR moving visual
experience built direction selectivity.** The mechanism is not in doubt — a
positive control drove it 0.111 → 0.351 (49% of range) on a single-direction
stimulus — so the null is a fact about the rule's ATTRACTOR, not a broken
instrument.

The diagnosis rung 3 recorded, measured rather than inferred:

> **Oja's fixed point is the leading principal component of the TIME-AVERAGED
> input covariance. Natural motion is direction-ISOTROPIC on average, so a
> contraction to the mean of an isotropic distribution IS the mean, and the mean
> has no direction.** The stability that rescued rung 2 from nine
> transient-measured failures is exactly what forbids rung 3.

This is why η, P2, `max_delay` and `delay_tol` stay frozen: **no value of any of
them changes what the attractor IS.** The required property is *symmetry-breaking
faster than the averaging timescale* — a unit that locks onto a LOCALLY
consistent direction and keeps it.

## THE MECHANISM — and it is one sentence

`seeds/vision_dorsal.json` v1.1.0 adds ONE term to `dv_oja_learn`, gated on
`DorsalParams.bistable` (**0.0 by default**, `bi_eta` 0.0 by default):

```
Δw_bi  =  bi_eta · (w − m)(2m − w)·w / (2m)²        m = mean weight over THIS unit's synapses
```

Its zeros are `w=0`, `w=m`, `w=2m`; it is **negative for 0<w<m** and **positive
for m<w<2m**. So:

> **m — THE MEAN — IS AN UNSTABLE FIXED POINT. A REPELLER.** The stable points are
> 0 and 2m.

That is the most direct possible negation of the measured diagnosis. Oja's
attractor is the mean; this makes the mean the one place a weight cannot stay. A
synapse transiently above its unit's mean is **latched up** rather than averaged
back down, so a locally-consistent direction (a ~20-step drift epoch, a wave
sweep) is committed to before the isotropic average can erase it. Once latched,
the unit responds best to that direction → **wins** the winner-take-all on that
direction → learns it further. That positive feedback is precisely what the
diagnosis asked for.

**It is scale-free on purpose, and that is why it adds ONE knob, not four.** A
textbook bistable rule needs `w_min`, `theta_b`, `w_max` — three free parameters
begging to be swept, which is the parameter search this rung forbids. Here the
threshold IS the unit's own mean and the ceiling IS twice it, both recomputed from
the unit's own state at every update. The term has no absolute scale, so it cannot
be tuned by choosing one; and weights above 2m are pushed back down, so it is
bounded and cannot run away.

**Asserted biology, not convenience.** Single synapses express LTP in an
**all-or-none, bistable** fashion rather than by graded averaging (Petersen,
Malenka, Nicoll & Hopfield 1998); bistable synaptic switches are the standard
account of how a synapse retains a transient correlation against ongoing noise
(Lisman 1985; Fusi's cascade). **A purely graded synapse is the one that cannot
hold a memory of a passing event — which is exactly what rung 3 measured.**

### Why bistability and NOT the anti-Hebbian lateral — ONE reason, and it is mathematical

**Any rule LINEAR in x has an averaging attractor.** Lateral decorrelation changes
*which* average a unit converges to (which principal component); it does not make
an average directional. The local Földiák form `w ← w(1 − η·y_v²) − η·y_v·x` has
fixed point `w = −x̄/ȳ` — **minus the mean, still the mean.** Bistability is
**nonlinear in w**, which is the property the measured diagnosis actually demands:
it makes the mean a *repeller* instead of converging to a different one.

### RETRACTED: the engine-based half of that argument (2026-07-17)

An earlier draft of this pre-registration, and of the seed comment, **also**
rejected the lateral family on ENGINE grounds: Sanger's deflation is "not local"
(a synapse must read the winner's weight vector); Rubner-Tavan "races
`dv_burst_winner`'s Argmax over the same `dact`" inside the fixpoint. Both are
true statements about **today's engine**, and **neither is a valid reason to
discard a mechanism.**

The standing directive is that **any biologically plausible mechanism is allowed,
and the engine is EXTENDED to fit the biology.** This tree's own rule is *primitive
in Rust, composition in graph*: when the DSL genuinely cannot express something,
you add a Rust Term or change the evaluation semantics (`CLAUDE.md`, "When a new
primitive is needed → Rust"). **A missing primitive is a build task, never a veto
on the science.** Letting the engine's current shape decide which biology is
admissible is exactly backwards — it is how a model quietly becomes a model of its
own implementation. The error was mine and it is retracted here rather than
quietly dropped.

### The honest status of the alternatives

**The anti-Hebbian lateral family is UNBUILT AND UNREFUTED.** It is set aside on
the linearity argument alone — which bites the local Földiák form squarely, and
which **a genuine deflation may well escape**: eviction from the DC mode lands a
unit in what is plausibly a **degenerate direction-carrying multiplet** under
isotropy, where the tie is broken by the unit's own random delays rather than by
the average. That is symmetry-breaking by a different route, it is a real
candidate, and it is recorded as one.

What it would cost the engine is nameable, and under the directive that cost is a
**first-class deliverable, not a blocker**:

- a **Rust Term for a non-local read** (a synapse reaching the winner's
  corresponding weight) — Sanger/GHA deflation;
- **two-phase evaluation** so a lateral term can modify an output *before* the
  competition Argmax reads it — Rubner-Tavan;
- an **outer-product primitive**.

If the confirmatory run below fails, these are the first things the named next
hypothesis must consider.

## What is UNCHANGED, deliberately

The arms, the probe, the measure, the floor, the SESOI, the frozen parameters and
`gaze_walk` are **exactly rung 3's**. One thing changes: the plasticity rule. That
makes rung 3B a clean paired contrast against a committed result rather than a
second experiment with two moving parts. In particular **delays stay uniformly
random** (`test_the_adapter_hands_the_agent_no_direction_gradient`), the
paradigm-critical line: a delay gradient wired by the adapter would be
`preprocess_patches` at the motion grain.

**The `normal` arm's known limitation is INHERITED and is NOT fixed here.**
`gaze_walk`'s drift is direction-isotropic by construction, so — as rung 3 stated
— the experience-dependence of direction is **untested, not refuted**. Giving the
`normal` arm genuine directional statistics from the video's own object motion is a
real and separate question; changing the arm AND the rule in one step would
confound them, and a null would be uninterpretable. **Rung 3B tests the RULE
against rung 3's arms.** That is the scope, and it is stated in advance.

## ENGINE PROVENANCE — which binary produced every number here

**There are two `_native.abi3.so` on this box and a bare `python3 script.py` from
the repo root silently picks the STALE one.** Measured:

| | path | mtime | size | md5 |
|---|---|---|---|---|
| **stale** | `~/.local/lib/python3.14/site-packages/substrate_rs/_native.abi3.so` | 2026-07-13 10:55 | 7,265,112 | `6032f8a7…` |
| **fresh** | `runners/dsl/python/substrate_rs/_native.abi3.so` | 2026-07-16 16:43 | 6,748,040 | `57f3160c…` |

They are genuinely different builds. `PYTHONPATH=runners/dsl/python:.` selects the
fresh one; **a bare `python3` and a bare `pytest` both select the stale one.**
Every rung-3B instrument run (identity, positive control, convergence, pilot) was
launched bare and therefore **ran the STALE Jul-13 binary.**

**Checked rather than assumed — the two binaries are BIT-IDENTICAL on the dorsal
path:**

```
                        STALE                                FRESH
seed 0 untrained  OFF=+0.084545990398 BI=+0.084545990398  |  OFF=+0.084545990398 BI=+0.084545990398
seed 0 dark       OFF=+0.152737344628 BI=+0.157821041242  |  OFF=+0.152737344628 BI=+0.157821041242
seed 1 untrained  OFF=+0.099670482926 BI=+0.099670482926  |  OFF=+0.099670482926 BI=+0.099670482926
seed 1 dark       OFF=+0.096956106424 BI=+0.118267190447  |  OFF=+0.096956106424 BI=+0.118267190447
```

All 12 significant figures agree, armed and unarmed. **The instrument tables above
therefore stand.** That is a measured fact, not an assumption, and it was not
knowable in advance — reporting numbers from an unnamed engine was wrong even
though it happened to be harmless here.

**The `-k vision` SUITE is NOT binary-independent**, which is why this matters:

| binary | `pytest tests/ -k vision` |
|---|---|
| stale | **7 collection errors**, 14 skipped — cannot collect |
| fresh | **155 passed, 0 failed** (108 s) |

**THE CONFIRMATORY RUN BELOW IS EXECUTED WITH `PYTHONPATH=runners/dsl/python:.`
ON THE FRESH Jul-16 BINARY**, and its provenance is recorded in the OUTCOME.
Every future result in this ladder needs this stanza.

## Calibration inherited from rung 3 (burned seeds, no re-derivation)

| | value |
|---|---|
| **floor** (untrained, random delays) | **+0.111** — random wiring confers a real, REPLICATING direction bias |
| **ideal** hand-built DS unit | **+0.600** |
| **dynamic range** | **0.489** |
| **SESOI** | **0.049** (10% of range) |

**`DSI > 0` IS NEVER EVIDENCE.** Only paired comparisons count; arms share a seed
and therefore share their delays, so the innate bias cancels in the difference.
Every effect below is reported as a **fraction of the 0.489 dynamic range**.

## THE INSTRUMENT DEFECT THIS RUNG FOUND — the probe was training on its own stimulus

Found by the positive control BEFORE any arm was run, in the one place it could
not hide. **The step-0 column is taken before ANY training step, so it must equal
the 0.111 floor in every row.** It did not:

| bi_eta | **step 0** | 400 | 1600 | 3200 | NaN |
|---|---|---|---|---|---|
| OFF (rung 3) | **+0.111** | +0.124 | +0.217 | +0.297 | 0 |
| 1e-3 | **+0.112** | +0.125 | +0.240 | +0.331 | 0 |
| 1e-2 | **+0.118** | +0.147 | +0.213 | +0.219 | 0 |
| 3e-2 | **+0.136** | +0.187 | +0.188 | +0.188 | 0 |
| 1e-1 | **+0.339** | +0.335 | +0.300 | +0.217 | 0 |

**RETRACTED. Every armed number in that table is contaminated.** `probe_dsi`
froze plasticity by zeroing `oja_eta`, on the reasoning that Oja then degenerates
to the identity — correct for rung 3, and **false the moment the bistable term was
added**, because the term is scaled by `bi_eta`, not `oja_eta`. The probe went on
training each unit **on the probe stimulus**: training on the test set. The floor
jumped 3× at `bi_eta=1e-1` from zero training, and that manufactured jump *was*
the apparent "win" I would otherwise have selected `bi_eta` on.

**The gate that should have caught it passed the whole time.**
`test_the_probe_does_not_let_the_agent_learn` boots with `bistable=0`, so it
checked the freeze's CONSTANTS while being blind to the AXIS they parameterise —
verbatim the defect PROTOCOL §1 names. Fixed: the freeze zeroes **both** `oja_eta`
and `bi_eta` (restored after), and the gate now runs with the term **ARMED**
(`test_the_probe_does_not_let_the_agent_learn_WITH_THE_BISTABLE_TERM_ARMED`),
verified to FAIL on the defective freeze and PASS on the fixed one — a gate that
has never failed is not a gate.

This is not metric surgery (PROTOCOL §5): no gate had failed and no hypothesis had
been tested. The positive control is precisely the instrument built to catch this,
and it did — the same way rung 3's ideal exemplar caught the mean-readout defect.

**Both the positive control and the convergence check were re-run from scratch on
the fixed probe.** Only the clean tables below are used to fix `bi_eta`.

## CONVERGENCE (PROTOCOL §2) — run FIRST, before any arm, on the FIXED probe

Waves only (the formative input), n=8 burned seeds 0-7, drift = ‖w(t)−w(t−50)‖/‖w(t)‖.

**bi_eta = 1e-2 (the rate fixed below):**

| steps | mean DSI | weight std | drift | NaN |
|---|---|---|---|---|
| 0 | +0.1115 | 0.0495 | — | 0 |
| 50 | +0.1101 | 0.0325 | 1.2394 | 0 |
| 200 | +0.1175 | 0.0219 | 0.1355 | 0 |
| 800 | +0.1400 | 0.0514 | 0.0303 | 0 |
| 1600 | +0.1531 | 0.0943 | 0.0218 | 0 |
| 3200 | +0.1351 | 0.1062 | **0.0125** | 0 |

**CONVERGENT + non-zero structure. PASS.** Drift falls monotonically over two
orders of magnitude (1.2394 → 0.0125; rung 2's Oja scaffold was accepted at 0.107,
rung 3's at 0.0115). **0 NaN at every checkpoint.**

**And the weight std GROWS, 0.0219 → 0.1062 — that growth IS the mechanism.** The
bistable term's whole claim is that weights bifurcate away from the mean toward 0
and 2m; a widening spread while drift collapses is exactly what that predicts, and
it is the signature neither fixed-sign Butts (never settles, drift 0.49-0.75) nor
BCM (settles at 0.004 structure — annihilation) can produce.

**bi_eta = 1e-3**, for contrast — convergent but barely bifurcating (std 0.0444,
DSI flat at +0.1296), i.e. the term is present but not expressed:

| steps | mean DSI | weight std | drift | NaN |
|---|---|---|---|---|
| 0 | +0.1115 | 0.0495 | — | 0 |
| 200 | +0.1190 | 0.0156 | 0.1355 | 0 |
| 800 | +0.1274 | 0.0190 | 0.0194 | 0 |
| 1600 | +0.1291 | 0.0291 | 0.0128 | 0 |
| 3200 | +0.1296 | 0.0444 | 0.0122 | 0 |

**NOTED IN ADVANCE, because it is the H1b question:** at bi_eta=1e-2 waves alone
move DSI +0.042 by 1600 steps (8.6% of range) before relaxing to +0.024 by 3200
(4.9%). The arms give phase 1 (1600 waves) + phase 2 (1600), so `dark` sits near
the 3200 point. **That is close to the SESOI (0.049) and H1b's equivalence could
genuinely fail.** It is recorded here, before the run, as a live possibility rather
than explained after the fact.

## THE POSITIVE CONTROL — where bi_eta is FIXED, on a control with no arm

**The question a null cannot answer: can the rule produce direction selectivity AT
ALL?** Trained on the most direction-structured input that exists — bars drifting
in ONE consistent direction. Burned seeds 0-3. This is an INSTRUMENT check, never
an experimental arm: it trains on the probe stimulus, which is exactly why it can
only calibrate and never confirm.

**On the FIXED probe (step 0 = the 0.111 floor in every row, as it must be):**

| bi_eta | 0 | 400 | **1600** | 3200 | NaN |
|---|---|---|---|---|---|
| OFF (rung 3's rule) | +0.111 | +0.124 | +0.217 | +0.297 | 0 |
| 1e-3 | +0.111 | +0.125 | +0.229 | +0.307 | 0 |
| **1e-2** | +0.111 | +0.150 | **+0.278** | +0.269 | 0 |
| 3e-2 | +0.111 | +0.214 | +0.250 | +0.250 | 0 |
| 1e-1 | +0.111 | +0.161 | +0.156 | +0.159 | 0 |

**FIXED IN ADVANCE, on positive-control grounds only: `bi_eta = 1e-2`.** The
criterion, stated before looking at any arm: **the rate that maximises the positive
control at the FROZEN P2 = 1600 budget** — the budget the arms actually get (+0.278
= 34% of the dynamic range, vs the OFF rule's +0.217). It is also convergent there
(drift 0.0125, 0 NaN). 1e-1 over-latches and *destroys* the mechanism (+0.156,
below the OFF rule); 3e-2 breaks symmetry fastest early (+0.214 at 400) but
plateaus lower. This is instrument calibration on a control containing no arm and
no hypothesis, frozen here. **bi_eta is not swept again.**

**READ THIS TABLE NARROWLY.** The positive control is **not** where bistability is
expected to help, and its modest margin over the OFF rule (+0.061 at 1600) is
**not** evidence for the rung. A single-direction stimulus *has* a dominant
principal component, so Oja alone already works there — that is why the OFF row
reaches +0.217. The control's only job is to prove the instrument is not null, so
that a null on an arm means "the agent did not grow it" rather than "the rule
cannot". It passes. **Bistability's claim is about input that is isotropic ON
AVERAGE, and only the arms can test that.**

## Hypotheses — EXACTLY rung 3's, so the contrast is the RULE and nothing else

Per seed *i*, each arm's value is the mean cross-validated DSI over its 10 DUnits.
Arms, probe, floor, SESOI and frozen parameters are rung 3's, unchanged.

- **H1a (primary):** `d_normal = DSI(normal) − DSI(dark)`, two-sided.
  Predicted **> 0** — direction REQUIRES moving visual experience.
- **H1b (co-primary):** `d_dark = DSI(dark) − DSI(untrained)`, two-sided.
  Predicted **≈ 0** — direction is NOT innate and NOT built by waves (Li 2006).
  Tested as **EQUIVALENCE**: the 95% CI of `d_dark` must lie entirely inside
  ±0.049. A merely non-significant null is not evidence of absence.
- **H1c (co-primary):** `d_strobe = DSI(normal) − DSI(strobe)`, two-sided.
  Predicted **> 0** — it is MOTION, not spatial structure.

**Bonferroni α = 0.05/3 = 0.0167 each, fixed now. SESOI = 0.049** (10% of the 0.489
range), fixed from burned-seed calibration only.

### RUNG 3B IS BUILT iff ALL THREE hold

1. `d_normal > 0` ∧ `p < 0.0167`, **and**
2. `|d_dark|` 95% CI ⊂ (−0.049, +0.049), **and**
3. `d_strobe > 0` ∧ `p < 0.0167`.

H1a and H1c both require a POSITIVE effect, so the conjunction **cannot be passed
by making the mechanism inert**.

**Every effect is reported as a % of the 0.489 dynamic range.** Rung 3 returned two
effects at p=0.0001 that were 2.0% and 2.3% of range; a significant 0.009 is a lie
told with a correct p-value.

**The `untrained` arm is retained as the dissolution diagnostic.** Rung 3's H1c
"passed" while ~47% of it was `strobe` destroying the innate bias *below* the
floor. `strobe − untrained` is reported.

## n / seeds / statistic

- **Paired within seed. THE SEED IS THE UNIT OF ANALYSIS** (PROTOCOL §4).
- One-sample **two-sided sign-flip randomisation test**, 20,000 permutations, per
  hypothesis; bootstrap 95% CIs.
- **n = 100, FIXED IN ADVANCE**, matching rung 3 exactly so the two runs are
  directly comparable. Variance-only pilot on **burned seeds 0-13** (bit-identical
  engine, verified above) gave per-seed SD **0.0169 / 0.0448 / 0.0415** for
  d_normal / d_dark / d_strobe. At n=100: SE = 0.0017 / 0.0045 / 0.0042, so H1a and
  H1c have >99% power against the SESOI (0.049) at α=0.0167, and H1b's 95% CI
  half-width is ±0.0088 — narrow enough for an equivalence verdict to be possible,
  which is the condition H1b's test depends on.
- **DISCLOSED:** the hypotheses, SESOI, α and decision rule above were written and
  fixed BEFORE the pilot was launched. The pilot is variance-only by design, but I
  have now SEEN its means (burned seeds). Nothing below was changed in response to
  them, and they are reported in full HERE, before the run, rather than after:

```
BURNED-SEED PILOT (0-13, n=14, bi_eta=1e-2)   — VARIANCE ONLY; means disclosed, not used
  d_normal (normal-dark)     mean=+0.0041  SD=0.0169     ( +0.8% of range)
  d_dark   (dark-untrained)  mean=+0.0408  SD=0.0448     ( +8.3% of range)
  d_strobe (normal-strobe)   mean=+0.0632  SD=0.0415     (+12.9% of range)
  arms: untrained +0.1034 | dark +0.1442 | normal +0.1483 | strobe +0.0850
```

  **These sharpen the two risks already pre-registered above, and I let them stand
  rather than soften the prediction.** `d_dark` at +0.0408 is 83% of the way to the
  SESOI, so **H1b's equivalence is at serious risk of failing** — waves would be
  building direction selectivity, contradicting Li 2006. `d_normal` at +0.0041
  (0.8% of range) is the same near-null rung 3 got, so **H1a looks likely to fail
  again**. `d_strobe` at +0.0632 clears the SESOI for the first time in this
  ladder — but `strobe` sits at +0.0850, **BELOW the +0.1034 untrained floor**,
  so on burned seeds that effect is again substantially DISSOLUTION, exactly the
  wrong-reason pass rung 3 diagnosed. The `untrained` arm is what makes it
  visible, and it is why that arm is retained.
- **Confirmatory seeds: 6000+** — never used for anything. Ledger appended in
  `VISION_PROTOCOL.md`. Burned here: 0-7 (calibration, convergence, positive
  control), 0-13 (pilot).

**Exactly three hypothesis tests. No sweeps. No re-runs.**

## MY PREDICTION, STATED IN ADVANCE, WITH ITS PROVISOS

**I predict the conjunction FAILS, on H1a — but less confidently than rung 3's
author did, and for a reason that is now testable rather than rhetorical.**

The mechanism is real: the convergence table shows genuine bifurcation (weight std
0.022 → 0.106 while drift → 0.0125), which is symmetry-breaking, not averaging.
So the rule now *can* do the thing Oja structurally could not.

**The proviso that decides it, and I am genuinely uncertain:** bistability latches
a unit onto *whatever* is locally consistent. Nothing makes that a *direction*
rather than a spatial pattern. `gaze_walk` holds a drift direction for 20 steps and
then redraws it; a unit that latches during epoch 1 has, by epoch 5, been driven by
four other directions with the same statistics. **If the latch is deep enough to
survive them, DSI rises and H1a can pass; if the term merely re-latches on each
epoch, it is a slower averaging rule and H1a fails.** The convergence table hints at
the latter — DSI *relaxes* from +0.1531 at 1600 to +0.1351 at 3200 rather than
holding, which is what re-latching looks like.

**H1b is now at real risk of failing**, and that is a change from rung 3. Waves move
DSI +0.024 by 3200 steps (4.9% of range) — just inside the SESOI. If waves build
direction selectivity, the model contradicts Li 2006 and the rung fails *in the
interesting direction*: the mechanism works but is not developmentally selective.

**What would make me wrong in the interesting direction:** H1a passing would be the
first thing in this tree to reproduce Li 2006's positive half.

**A NEGATIVE IS A RESULT** and will be reported exactly as observed, with the
attractor diagnosed. **And the scope limit stands regardless of outcome:**
`gaze_walk`'s drift is isotropic by construction, so **a null on H1a leaves the
experience-dependence of direction UNTESTED, not refuted.** This run tests the
RULE, not the biology of natural motion.

---

# OUTCOME (run 2026-07-17, exactly as specified — n=100, seeds 6000-6099, bi_eta=1e-2)

**ENGINE:** `runners/dsl/python/substrate_rs/_native.abi3.so`, mtime **2026-07-16 16:43**
(the FRESH repo binary; `PYTHONPATH=runners/dsl/python:.`, printed as line 1 of
`results/r3b_confirm.log`).

```
H1a d_normal  (normal - dark)    +0.0018  95% CI [-0.0021, +0.0056]  p=0.3602   (+0.4% of range)
H1b d_dark    (dark - untrained) +0.0362  95% CI [+0.0283, +0.0442]  p=0.0000   (+7.4% of range)
H1c d_strobe  (normal - strobe)  +0.0482  95% CI [+0.0405, +0.0559]  p=0.0000   (+9.9% of range)

  H1a (experience produces direction)     : FAIL
  H1b (waves do NOT, equivalence +-0.049) : PASS
  H1c (motion, not spatial structure)     : PASS
```

# **DECISION: NOT BUILT** — the conjunction fails on H1a.

| arm | mean DSI | vs floor | % of range | reading |
|---|---|---|---|---|
| `dark` (waves continue) | +0.1411 | +0.0362 | +7.4% | **waves build real DS** |
| `normal` (video + drifting eye) | +0.1429 | +0.0380 | +7.8% | **experience builds the SAME amount** |
| `untrained` (the floor) | +0.1049 | — | — | random delays alone |
| `strobe` (same frames, permuted) | +0.0947 | **−0.0102** | −2.1% | **below the floor — dissolution** |

## THE MECHANISM WORKED. THAT IS WHAT MAKES THIS INFORMATIVE.

Rung 3B is **not** a repeat of rung 3's flat null. The bistable term did exactly
what it was built to do — **it broke the symmetry**:

| | rung 3 (Oja alone) | **rung 3B (mean as repeller)** |
|---|---|---|
| `normal` − floor | +0.0061 (1.2%) | **+0.0380 (7.8%)** — 6.2× |
| `dark` − floor | +0.0096 (2.0%) | **+0.0362 (7.4%)** — 3.8× |
| convergence | drift → 0.0115 | drift → 0.0125, **weight std 0.022 → 0.106** |

The weights bifurcated, the rule stayed convergent, and DSI rose to 4-6× rung 3's
effect. **Making the mean a repeller is a real symmetry-breaker and it is now
measured, not argued.** And it still does not build rung 3, because:

## MY PREDICTION HELD — including the proviso, which is the whole finding

The pre-registration said: **"I predict the conjunction FAILS, on H1a"**, and named
the proviso that would decide it:

> *"Bistability latches a unit onto whatever is locally consistent. **Nothing makes
> that a DIRECTION rather than a spatial pattern.** … If the latch is deep enough to
> survive [later epochs], DSI rises and H1a can pass; if the term merely re-latches
> on each epoch, it is a slower averaging rule and H1a fails."*

**Neither branch is what happened, and the truth is sharper than either.** The latch
is deep — DSI rose 6× — and H1a still failed, at +0.4% of range, p=0.36. `normal`
and `dark` are **statistically indistinguishable** (+0.0018, CI straddling zero)
despite their inputs having nothing in common.

## THE DIAGNOSIS — measured, and it REFUTED MY FIRST ANSWER

I first wrote, from the arm means alone: *"`normal ≈ dark`, so the direction cannot
come from the input; what is left is the unit's own random delays — the rule latches
the wiring's accident and amplifies it. Oja's attractor is the mean of the data; the
bistable rule's attractor is the INITIAL CONDITION."*

**That was inference, so I measured it, and it is WRONG.** Post-hoc diagnostic
(`scripts`/`scratchpad3/r3b_attractor.py`, burned seeds 0-7, n=80 units, NOT a
hypothesis test): agreement between each unit's preferred direction across
conditions. Chance = 1/8 = 0.125.

| comparison | agreement | what it kills |
|---|---|---|
| `untrained` → `dark` | **0.412** | **the initial-condition claim.** If the attractor were the innate delay bias this would be ~1.0. Training moves **59% of units OFF** their innate preference. |
| `untrained` → `normal` | **0.438** | same |
| `dark` → `normal` | **0.812** | **the actual finding — two UNRELATED phase-2 inputs, same direction** |

The innate bias is real but is *not* the attractor (0.412 vs 0.125 chance — an
anchor, not a fixed point). **The load-bearing number is 0.812.** `dark` and `normal`
share exactly one thing: **PHASE 1 — the 1600 steps of waves that are bit-identical
in every arm by design.** Phase 2 (`dark` = more waves; `normal` = video, waves
ceased, `propagate=0`) has nothing in common. Yet 81% of units keep the same
preferred direction across them.

> **The attractor is the FIRST COHERENT MOTION THE UNIT EVER SAW.** The latch closes
> during phase 1, on the waves — and phase 2 cannot reopen it. Bistability delivered
> exactly what was asked of it: *"a unit that locks onto a locally consistent
> direction and KEEPS it."* **It keeps it too well.** Hysteresis with no mechanism
> for revision is not development; it is a one-shot commitment made before eye
> opening.

**This is a DEVELOPMENTAL TIMING failure, not an averaging failure, and it is a
different defect from rung 3's.** Rung 3's rule could not build direction from
anything. Rung 3B's rule builds it fine (+7.4% from waves alone, p=0.0000) and then
**finishes before the experiment starts.** H1a asks "does moving experience add
anything over darkness?" — and by the time phase 2 begins, both arms are already
latched by their shared wave history. **H1a could not have passed.** `normal` and
`dark` are not indistinguishable because experience is powerless; they are
indistinguishable because **the decision was already made in a phase they share.**

That also explains `strobe` cleanly: it is the one arm whose phase 2 delivers no
coherent motion, so instead of re-latching it **dissolves** the phase-1 latch to
−0.0102 below the floor. Destruction is the only thing phase 2 could still do.

**The lesson generalises past this rule:** PROTOCOL §6 says controls must correspond
to the experiment. Phase 1 was made bit-identical *in order to* isolate phase 2 —
correct for a rule that keeps integrating, and **self-defeating for a rule that
latches**, because a shared formative phase pre-commits every arm. **Adding a
mechanism silently invalidated the design** (PROTOCOL §4, "adding a mechanism can
silently invalidate your control"). Rung 3B is that entry, in a new place: not the
control arm this time, but the *shared phase*.

## H1b PASSED, and the pass is worth less than it looks

`d_dark` = +0.0362, CI [+0.0283, +0.0442] ⊂ ±0.049 ⇒ **equivalence to the floor,
PASS as written.** But it is 7.4% of range and p=0.0000: **waves demonstrably DO
build direction selectivity here.** The equivalence verdict is an artefact of a
SESOI set at 10% — the effect is real, it is just smaller than the threshold I
committed to in advance. Reported as a PASS because that is what was written down,
and simultaneously as **evidence AGAINST the model**: Li 2006 says direction is
absent at eye opening; this model builds it from waves alone. The pre-registration
predicted this risk explicitly ("H1b is now at real risk of failing … the mechanism
works but is not developmentally selective") and the risk materialised in
substance while passing on the letter.

## H1c PASSED and is AGAIN a pass for the wrong reason

```
strobe - untrained = -0.0102   (BELOW the floor — strobe DISSOLVES the innate bias)
normal - untrained = +0.0380
                     -------
H1c = normal - strobe = +0.0482
```

**~21% of H1c is destruction, not construction** (0.0102 / 0.0482). Better than
rung 3's ~47%, but the same defect: without the `untrained` arm this would read as
"motion beats scrambled input" when part of it is scrambled input eating the
wiring's innate bias. **The `untrained` arm earned its place for the second rung
running.**

## What is CLAIMED

1. **Bistable plasticity is a working, convergent symmetry-breaker** — drift
   1.2394 → 0.0125, 0 NaN, weight std growing 0.022 → 0.106 (the bifurcation),
   DSI 4-6× rung 3's over the floor. **The mean as a repeller does what it says.**
2. **Its attractor is the FIRST coherent motion it saw — the shared phase-1 waves
   — and phase 2 cannot move it.** Measured, not inferred: `dark` → `normal`
   preferred-direction agreement **0.812** on unrelated inputs, while `untrained`
   → `dark` is only **0.412** (so the innate bias is an anchor, not the attractor —
   which REFUTES my own first reading of the arm means).
3. **An instrument defect was found and fixed before any arm ran**: the probe was
   training on its own stimulus through the un-frozen `bi_eta` (step-0 floor 0.111
   → 0.339 at bi_eta=1e-1). The contaminated table **inverted the bi_eta ranking**.

## What is NOT claimed

- **NOT that direction selectivity requires experience.** H1a FAILED (+0.4%).
  Unchanged from rung 3, and for a *different* reason.
- **NOT that the experience-dependence of direction was tested.** `gaze_walk`'s
  drift is **isotropic by construction**. This run tested the RULE against rung 3's
  arms. **Still UNTESTED, not refuted** — and it is now the single most valuable
  open question in this rung, because a rule that amplifies its initial condition
  would look identical under isotropic and anisotropic input *only if* the input
  never mattered. Genuine directional statistics from the video's own object motion
  would discriminate.
- **NOT that bistability is refuted as biology.** What is measured is that *this*
  bistable rule, on *this* isotropic input, latches its wiring rather than its
  world.
- **NOT anything about absolute DSI.** The floor is 0.1049, not 0.
- **NOT that H1b vindicates Li 2006.** It contradicts it in substance (waves build
  +7.4% of range) while passing the pre-registered equivalence on the letter.

## THE NAMED NEXT HYPOTHESES (NOT run, NOT built here)

The measured diagnosis reframes what is needed. Oja fails by converging to the
data's mean. Bistability does not fail by converging to its own accident (0.412
refutes that) — **it fails by converging too EARLY, on the first coherent motion it
meets, and never revising.** So the requirement is not "more symmetry-breaking"; it
is **symmetry-breaking that stays REVISABLE while the formative input changes** — a
latch with a key.

**The cheapest test of the diagnosis is a DESIGN change, not a rule change, and it
should come FIRST:** phase 1's waves are what pre-commit both arms. Run the arms with
phase 1 SHORTENED or with the dorsal population's plasticity gated off until eye
opening (biologically: direction selectivity is absent at eye opening — Li 2006 —
so the dorsal latch arguably should not be closing during the wave period at all).
If H1a moves, the rule was never the problem; the shared formative phase was. **That
is a new pre-registration and a mechanism-level hypothesis, not a sweep** — and it
is the single highest-value next run in this rung.

Then, if the latch is genuinely the wrong shape:

1. **A metaplastic / decaying latch** — the direct answer to the measured defect.
   The bistable term's stable points must be reachable *back out of* when the input
   distribution changes (a latch that reopens on sustained prediction error;
   Fusi's cascade has this by construction, and I used only its bottom rung).
   **This is now the leading candidate, and it is a small edit to a rule that
   already works.**
2. **The anti-Hebbian lateral family — UNBUILT AND UNREFUTED.** A unit's direction
   is chosen *against other units* rather than from its own history, so the
   population is forced to *cover* the input's directions.
   **Under the standing directive the engine gets extended to fit it**, and the
   cost is nameable: a **Rust Term for a non-local read** (a synapse reaching the
   winner's corresponding weight — Sanger/GHA); **two-phase evaluation** so a
   lateral term modifies an output *before* the competition Argmax reads it
   (Rubner-Tavan); an **outer-product primitive**. My linearity objection stands
   against the *local Földiák* form (fixed point `w = −x̄/ȳ`, minus the mean) —
   but it does **not** touch a genuine deflation, and my "degenerate multiplet"
   defence of it is now known to be a *liability*, not a rescue. That is a sharper
   starting point than it had before this run.
3. **A rule that is anti-Hebbian in TIME** — STDP-style, where the sign of the
   update depends on pre-before-post vs post-before-pre. Direction *is* temporal
   order; a rule whose sign flips with order cannot be satisfied by a static delay
   accident, because reversing the stimulus reverses the update. This is the only
   named candidate that reads the axis direction actually lives on.
4. **Real object motion in the `normal` arm** — still owed, and still the only way
   to test the experience-dependence of direction. Note the diagnosis DEMOTES this:
   with the latch closing in phase 1, `normal` would have been unable to show an
   effect **however anisotropic its input was**. Fixing the arm without fixing the
   timing would have produced another uninterpretable null — and I would have
   blamed the biology.

## Honest status

**Rung 3B: NOT BUILT.** The rule converges, breaks symmetry, and lifts DSI 4-6×
rung 3's effect over the floor — then commits during the shared wave phase and
never revises, so moving experience adds +0.4% of range over darkness.

**Rung 3's attractor was the average of the data. Rung 3B's is the first thing it
ever saw. Neither is the world** — but they fail in opposite directions, and the
second is the more tractable failure: rung 3 needed a new mechanism, rung 3B needs
a latch that can reopen, or a formative phase that does not pre-commit the arms.
**The measured claim that "the attractor is the initial condition" was my own, was
wrong, and was refuted by the diagnostic I ran to check it** — recorded here rather
than quietly dropped, because an inference that survives to publication because
nobody measured it is exactly what this PROTOCOL exists to prevent.

Rungs 1, 2 and 4 are untouched: `bistable=0`/`bi_eta=0` by default, defaults-off
verified **MAX DIFF = 0.000e+00** across 12 arm × seed runs, `vision_waves.json` and
`vision_maps.json` byte-unchanged.
