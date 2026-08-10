# RUNG 8E — PRE-REGISTRATION: H1 AND H2, AT LAST. THE FOURTH RUNG'S CLEAN BLOCK.

*Written and **COMMITTED BEFORE THE RUN**. Seeds **13000–13015** have been
ALLOCATED, UNUSED and CLEAN through rungs 8, 8B, 8C and 8D. This rung spends
them.*

**Engine `a06584eaa362`** @ `<this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`
— **`own` build** (`scripts/engine_build.sh`, this worktree, §11.5). **Base
commit `de5f96b8`**. **NO Rust. NO seed edited. NO new constant.** Provenance
gate `tests/test_engine_provenance_migrated.py` 7/7.

**THE GATE THAT LICENSES THIS RUN IS CLOSED.** `VISION_RUNG8D_PREREG.md` was
committed before its run (`fd0c2107`, 10:32:00Z; run 10:32:06Z) and the
calibration **PASSED PROSPECTIVELY** on fresh seeds 6100–6107: IDEAL 0.9989
[0.9975, 1.0003], FLOOR 0.2691 [0.1933, 0.3450], SEPARATION 0.7298 [0.6530,
0.8065], `n_dead = 0` everywhere, `max|dw| = 0`. **Rung 8C's 1.0000 reproduces.**

---

## 1. HYPOTHESES (two-sided)

- **H1** — SUnits on rung 7's **decorrelated** channels become orientation-
  selective in RESPONSE: **Δ_lateral > SESOI**, i.e. OSI rises above the
  **lateral untrained floor measured IN THIS RUN, per seed**.
- **H2 (the ablation that makes it a test)** — on the **degenerate** split
  (`x_OFF = 1 − x_ON`), **Δ_degenerate ≈ 0**: the arm stays at its own floor.

**Both two-sided.** Predicted directions in this arc were wrong four times.

## 2. THE STATISTIC, EXACTLY

Per **SEED** (the unit of analysis, §4 — units share input and compete under
WTA, so they are not independent):

    Delta_arm   = OSI(trained, arm) - OSI(untrained, arm)      [paired, per seed]
    INTERACTION = Delta_lateral - Delta_degenerate

- **The floor is measured IN-RUN, per arm, per seed, at the same init** — never
  inherited. OSI's floor is init-dependent (0.0044 vs 0.3899, **89×**), rung 6's
  0.3168 is a third value, and rung 8D measured a **fourth** distribution
  (0.2754, sd 0.1091). **A floor is not inheritable.**
- **PRIMARY: Δ_lateral** (see §4 — it is the only statistic this rung can afford
  to power, and the decision rule below is built so that it decides H1 alone).
- **SECONDARY: the INTERACTION**, reported with its honest CI and **declared
  UNDERPOWERED in advance** (§4).
- Reported as mean ± **95% CI over SEEDS** (t-interval). **Per-arm, per-cell,
  per-orientation aliveness and `n_dead` reported for every arm** (§1 clause 4).
- **`peak/base` is NOT read** (§1.1: blew up at 1.6×10⁶ and 7.1×10⁷).

**SESOI = 0.0595** — rung 6's, adopted unchanged (same layer, same probe).

## 3. THE ARMS, AND WHAT EACH CORRESPONDS TO (§6)

| arm | retina | corresponds to |
|---|---|---|
| lateral, trained | rung 7's decorrelated ON/OFF | the composed system developing on its own waves |
| lateral, untrained | rung 7's, `w0=1.0`, no learning | **H1's own floor**, same init, same probe |
| degenerate, trained | rung 6's `x_OFF = 1−x_ON` | rung 6's negative, reproduced |
| degenerate, untrained | rung 6's, `w0=1.0` | **H2's own floor** |

Identical SUnit anatomy, synapse count, RF geometry, probe, learning rule and
η in every arm. **The ONLY difference is which retina is upstream** — the
difference rung 6 diagnosed and rung 7 removed.

**TRAINING: η = 5e-4, 6400 steps.** This is **rung 8's prereg's own FROZEN
choice** ("η, RF, period, `lat_eta`, `gmax` are FROZEN" = rung 6's values), NOT
selected by me after seeing an outcome.

**§1 CLAUSE 5 — TRAINING IS LOAD-BEARING, MEASURED BEFORE THE RUN, NOT ASSUMED:**

| pathway | η | mean relative weight change over 6400 steps | verdict |
|---|---|---|---|
| lateral | **5e-4** | **4.49%** (max|dw| 0.23–0.36) | **LOAD-BEARING** |
| lateral | 1e-4 | 0.86% (sd 0.0497→0.0517 vs the init jitter) | **near-VACUOUS** |
| degenerate | **5e-4** | **57.98%** (max|dw| 1.10–1.20) | LOAD-BEARING (rung 6's runaway) |
| degenerate | 1e-4 | 1.15% | near-VACUOUS |

**So the frozen η is also the only NON-VACUOUS one**, and this disposes of the
brief's demand that H2's control "not be null for a trivial reason": the
degenerate arm's weights move **57.98%** — it is emphatically not inert. If it
nonetheless shows Δ ≈ 0, that is a substantive null, not an unplugged cable.

**DECLARED §2 LIMITATION, not argued away.** Rung 8's own convergence table:
lateral at η=5e-4 is **bounded but RISING** (drift 0.0063 → 0.0300 at 6400) —
"bounded" is the claim, not "converged"; the degenerate at 5e-4 **runs away**
(0.0042 → 0.4612, clump 0.849 — rung 6's own result). **At η=1e-4 both are
stable but near-vacuous.** There is no η at which this rule is both convergent
AND load-bearing, and **that is a finding about the rule, not a choice I get to
make silently.** I run the frozen η, report the drift, and **treat any positive
Δ as provisional pending a convergent rule** — a rising drift means a positive
could be a point on a curve (§1 clause 3). **A NULL is not threatened by this**:
a rule that is still rising and has produced nothing by 6400 steps has produced
nothing.

## 4. n, FIXED IN ADVANCE BY THE PILOT — AND WHAT IT COSTS

Pilot: `rung8d_h1_power_pilot.py`, **burned seeds 0–7**, n = 8, identical
protocol.

| statistic | mean | **sd (per seed)** | n for 80% power at SESOI = 0.0595 |
|---|---|---|---|
| Δ_lateral | +0.0106 | **0.0737** | **n ≥ 13** |
| Δ_degenerate | −0.0169 | 0.1394 | — |
| INTERACTION | +0.0275 | **0.1625** | **n ≥ 59** |

**I DECLARE n = 16**, confirmatory seeds **13000–13015**, appended to the ledger
in this same commit.

**THE HONEST CONSEQUENCE, DECLARED IN ADVANCE:** n = 16 **POWERS Δ_lateral**
(SE ≈ 0.018, 95% CI ≈ ±0.039 — enough to exclude the SESOI) and **DOES NOT
POWER THE INTERACTION** (SE ≈ 0.041, CI ≈ ±0.087, which straddles the SESOI).
**n ≥ 59 would be needed for the interaction and this rung does not spend it.**
The interaction is therefore reported as a **secondary, underpowered** statistic
and **cannot confirm anything** — only Δ_lateral can.

**Why that is legitimate rather than a dodge:** the interaction exists (§4) to
protect against a *generic* training effect masquerading as a lateral-specific
one. **That protection is only needed if Δ_lateral is POSITIVE.** If Δ_lateral's
CI excludes the SESOI, there is no lateral effect for the interaction to
attribute, and H1 is null on the primary statistic alone. **This asymmetry is
declared here, before the run, precisely so it cannot be invented afterwards.**

**Why the required n is so large — and it is THIS rung's own finding:** rung 8D
measured that `osi()`'s `argmax` is a **LOTTERY over EXACT ties** on a nearly-
flat curve (an aliasing degeneracy of the probe's discretisation:
`tc[30°] == tc[150°]` to 1e-16), giving the FLOOR a per-seed **sd = 0.1091 ≈
1.8× the SESOI**. Pairing helps (sd(Δ_lateral) = 0.0737 < √2·0.1091 = 0.154) but
does **not** cancel it — training re-rolls the lottery. **The measure, not the
mechanism, is what makes H1 expensive.**

## 5. MY PREDICTION, IN ADVANCE, WITH PROVISOS (§3.7)

**I PREDICT H1 IS NULL**: Δ_lateral ≈ 0, CI excluding the SESOI. **The wave
ensemble is orientation-ISOTROPIC; decorrelation removes a REDUNDANCY without
installing an ANISOTROPY.** That is the cause rungs 3 and 5 both died on, it is
rung 8's §8 prediction and rung 8C's §5 prediction, and I inherit it unchanged.

**I PREDICT H2 IS NULL**: Δ_degenerate ≈ 0 — and *not* because the arm is inert
(its weights move 58%), but because the same isotropy applies.

**Independent convergent evidence, from a different mechanism** (the sd/dynamic-
quantization rung, `ee0d8fe4`): `mints(N)` = the number of ORBITS of the
presented orientations under the group generated by the **HELD**
`DimensionGenerator`s — 8/8, zero variance, prospective. Its verdict: **"the loop
composes what it holds; it does not discover what it lacks"**, and **"the limit
is REPRESENTATIONAL, not statistical — whitening cannot conjure a generator you
don't hold."** **A NULL here would agree with that from a different direction**,
which is the paradigm answer this line of work was commissioned to produce, not
a disappointment.

Provisos — each tells me what I did not understand if it breaks:
1. **If H1 CONFIRMS**, my "isotropic ⇒ no orientation" model is wrong, and
   decorrelation **is** sufficient — the strongest possible result and the one
   that would overturn rungs 3/5/6's shared diagnosis. **It must then survive
   the §2 caveat** (§3): a rising drift means it could be a point on a curve, and
   I would report it as provisional pending a convergent rule, NOT as earned.
2. **If H2 is NOT null**, the control is invalid and **neither hypothesis is
   interpretable** — a generic training effect is inflating both arms.
3. **If any arm has `n_dead > 0`**, §1.1's trap; the run fails its gate.
4. **If Δ_lateral's CI is wide enough to include BOTH 0 and the SESOI**, the run
   is **INCONCLUSIVE, not null** — and I will report it as such rather than
   claiming a negative I did not earn. (The pilot says this is unlikely at
   n = 16, but the pilot is n = 8.)

## 6. DECISION RULE, INCLUDING WHAT A NULL MEANS

- **H1 CONFIRMED** iff **Δ_lateral > SESOI with a 95% CI excluding 0** *and*
  `n_dead = 0` on both lateral arms. (The interaction is reported but, being
  underpowered by declaration, cannot be required — see §4.)
- **H1 NULL** iff **Δ_lateral's 95% CI EXCLUDES the SESOI (0.0595)**.
  ⇒ **decorrelated input is NOT sufficient**, and **rung 6's negative deepens**:
  the blocker is *not* the channels' correlation structure. **That is a FINDING,
  not a failure** — it would locate the blocker elsewhere and would **converge
  with the sd loop's representational bound** from an independent mechanism.
- **INCONCLUSIVE** iff the CI includes both 0 and the SESOI. Reported as such.
  **No re-run. No extra seeds. No sweep.**
- **H2 must be null.** If Δ_degenerate's CI excludes 0 *in either direction*,
  the control is invalid and neither hypothesis is interpretable.
- **Exactly the listed tests. No sweeps. No re-runs.** A further attempt needs a
  NEW pre-registration with a NEW **mechanism-level** hypothesis — never a
  parameter search. **η, RF, period, `lat_eta`, `gmax`, the probe and the
  settling duration (2000) are FROZEN.**
- **§7: NO RESCUE.** If H1 is null I will not tune toward a positive. Four
  results have been retracted in this arc; **a diagnosed negative beats an
  un-understood positive.**

## 7. §13 — WHAT FALLS OUT, AND WHAT GOES IN

**This rung introduces NO constant.** η, RF, period, `theta_rate`, `oo_wmax`,
`lat_eta` and `gmax` are all rung 6's/rung 7's, frozen and untouched; no seed is
edited; no Rust is added; `theta ≈ 2.17` **falls out** of the cell's own EMA of
its own drive. `n = 16` and the seed block are **procedural declarations**, and
`n` **falls out** of the pilot's measured sd.

### §13.1 — COULD THIS DESIGN HAVE PRODUCED THE OPPOSITE RESULT?

**Yes, and every piece of it is built so it could.**
- The probe **PASSES** on an ideal split-Gabor at **0.9989 ± 0.0016 across 8
  fresh seeds** — so a cell that *did* develop orientation selectivity **would be
  seen**. That is exactly what rungs 8 and 8B could NOT say (their probe scored
  an ideal cell at 0.1290, and 8B's floor arm was DEAD), and it is why this run
  is licensed at all.
- The separation is **proven to be by SELECTIVITY, not drive**: the readout is
  exactly scale-invariant (tuning curves scale to 1e-13 under a 9.51× weight
  scaling) and at **matched drive** the separation is 0.8000.
- Training is **proven load-bearing** (4.49% / 57.98%), so a null cannot be an
  unplugged cable.
- The floor is measured **in-run, per seed**, so a "lift" cannot be an artifact
  of an inherited floor — which is exactly how rung 5's apparent 0.3665
  evaporated.

**What a null CANNOT be blamed on, by construction:** a blind probe, a dead arm,
an inherited floor, an inert manipulation, or a drive artifact. **Those were the
five ways this arc has failed before, and each is closed by a measurement rather
than an argument.** What it *can* still be blamed on, and I say so in advance:
the **§2 non-convergence** at the frozen η (proviso in §3), and the **argmax
lottery** in the measure (§4) — which is why n = 16 and not 8.
