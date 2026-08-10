# THE CALIBRATION REFRAME — do the waves place a REFERENCE, or teach CONTENT?

*Binding: `VISION_PROTOCOL.md`. This is a NEW pre-registration with a NEW
mechanism-level hypothesis — NOT a re-run of rung 6 and NOT a parameter search. η,
`theta_rate`, `wmax`, the probe period and the RF are inherited FROZEN from rung 6.*

> # **THIS RUNG STOPPED AT THE MEASURE-CALIBRATION GATE (PROTOCOL §1).**
> **No confirmatory arms were run. Seeds 10000–10999 are allocated and remain UNUSED and
> CLEAN.** The measure (`RPI = peak/base`) **failed its own calibration** — it is
> unbounded, and the non-exercising control scores **1.6×10⁶** against an ideal Gabor's
> **6.94**. *A gate whose measure passes noise is not a gate* (PROTOCOL §1); a gate whose
> measure ranks "no input at all" 240,000× above a perfect Gabor is not one either.
> **See §12 — OUTCOME / DECISION.** The design, the hypotheses and the falsifiers below
> were written before the pilot and are preserved verbatim, because the reason they could
> not be run is the result.

**ENGINE PROVENANCE (PROTOCOL §10).** Every number in this document:
`engine 95167c01b7b3 @ <worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`,
commit `0561e70976`. The engine is a **private copy** of the canonical artifact,
verified byte-identical by sha256, resolved per-process via `PYTHONPATH`
(PROTOCOL §11.2 — no global install state was touched).

**Vision bench baseline in this worktree at `0561e70976`:** `pytest tests/ -k vision`
→ **153 passed, 0 failed, 1 skipped** (156 collected). See §0.3 — the brief's "156/0"
is not reachable at this commit, and the reason is recorded rather than papered over.

---

## THE CLAIM UNDER TEST

> *"There is no view from nowhere. Things only exist in definition of each other. This
> would mean that the fundamental purpose of the waves is CALIBRATION OF A FIXED POINT
> in vision space to start from."*

Retinal waves are **not training data that teach content** (orientation, direction).
They are a **calibration signal** that establishes the reference against which all later
input is *defined*. Nothing has an absolute value; a feature exists only relative to a
fixed point, so the fixed point must be established FIRST.

**This document treats that as a hypothesis to test, not a premise to confirm.**

---

## 0. THREE CORRECTIONS TO THE RECORD, MADE BEFORE THE RUN

The reframe arrived with six supporting retrodictions. **Retrodiction is not evidence**,
and a story that fits everything already measured is exactly the dangerous kind. Three
things had to be fixed before a forward test could mean anything.

### 0.1 RETRACTED (2026-07-17, at merge) — the numbers were real; rung 3B landed WHILE I worked

**The correction below is WRONG and is retracted in place rather than deleted.** It was
accurate at my base commit `0561e70976`, where `VISION_RUNG3B_PREREG.md` genuinely had no
OUTCOME section and neither number appeared anywhere in the tree. **Rung 3B's confirmatory
run was committed concurrently** (`28dd46e2dc`), and its OUTCOME contains exactly the cited
figures:

```
H1a d_normal (normal - dark)  +0.0018  95% CI [-0.0021, +0.0056]  p=0.3602   (+0.4% of range)
strobe - untrained            -0.0102                                        (-2.1% of range)
```

**PROTOCOL §11.5, demonstrated on me:** *"Long-running measurement is not a lock. Another
agent may commit, merge, or rebase under you. Record the commit SHA and engine hash your
numbers came from, or they are unattributable."* I recorded the SHA, which is the only
reason this is a clean retraction rather than a contradiction — but I asserted a **negative
about the tree** ("these numbers do not exist") from a **snapshot**, and a negative from a
snapshot is not a fact about a moving branch. **The error is mine.** The right form was
"absent at `0561e70976`", not "does not exist".

**And the substance now runs the other way — for the reframe.** At n=100 on fresh seeds,
`normal − dark = +0.0018, p=0.3602`: **waves and real moving video build the SAME amount of
direction selectivity, and the difference is indistinguishable from zero.** Two inputs with
no shared direction statistics, interchangeable. `strobe` (no coherent motion) sits
**−0.0102 BELOW the untrained floor** — it decalibrates. **That IS the double dissociation
this document set out to test, it is now measured at power, and it landed in the dorsal
layer while this rung was stopping in the simple layer.** It does not rescue the measure
defect (§12.1) and it is not mine to claim — it is recorded here because §0.1 would
otherwise mislead, and because **it makes the interchangeability question live rather than
withdrawn.**

**The caution that still stands, and rung 3B's own OUTCOME states it:** H1b PASSED its
equivalence test (`d_dark = +0.0362`, CI ⊂ ±0.049), i.e. **waves' effect is statistically
equivalent to the untrained floor at the pre-registered SESOI**. Interchangeability between
two arms that are both near the floor is the vacuity of §1.1 in the dorsal layer. Whether
rung 3B's numbers escape that is **rung 3B's call to make, not this document's.**

### 0.1-original (RETRACTED — preserved verbatim; read §0.1 above first)

#### Two of the cited numbers DO NOT EXIST in this tree

The brief states rung 3B "has already accidentally run" and cites **`dark` = `normal`,
+0.0018, p=0.36** and **`strobe` −0.0102**. Checked, not assumed:

- **`VISION_RUNG3B_PREREG.md` has no OUTCOME section.** Its confirmatory run was never
  executed; seeds 6000–6099 are pre-allocated in the ledger, not consumed. The only 3B
  numbers in the tree are its **burned-seed pilot** (`results/r3b_pilot.log`) and its
  positive control.
- **A tree-wide grep for `0.0018` and `0.0102` returns nothing.**
- The numbers that DO exist are **rung 3's** (`VISION_RUNG3_PREREG.md`, n=100, seeds
  4000–4099): `d_normal = −0.0035, p=0.0922`; `strobe − untrained = −0.0054`.

**The qualitative shape the reframe leans on survives** (`normal ≈ dark`; `strobe` sits
below the untrained floor) — but it is rung 3's, at different magnitudes, and rung 3B's
pilot points the *other* way (`d_dark = +0.0408`, 83% of the way to its SESOI). **The
"interchangeability has already half-run" premise is withdrawn.** It has not run.

### 0.2 An in-tree retrodiction that goes AGAINST the reframe, and was not cited

The reframe nominates the operating point as its success criterion. **Rung 6 measured
that criterion, and waves made it WORSE than no training at all:**

| | peak/base |
|---|---|
| untrained floor (θ adapted) | **1.96** |
| waves, η=1e-4 (stable regime) | **1.54** |
| waves, η=5e-4 (runaway regime) | **1.43** |

**Waves DECALIBRATE.** On the very measure the reframe elects, the formative input moves
the model *away* from a well-placed operating point. That is a direct counter-retrodiction,
it was in the tree the whole time, and it is why H1 below is the primary test.

### 0.3 The "156/0" baseline does not reproduce, for two separate reasons

Measured, same engine hash, this commit: **2 failed, 143 passed, 6 skipped, 5 errors**.
Diagnosed rather than accepted:

1. **5 errors** = `test_vision_growth_migrated.py` — the **BSDS300 corpus is absent from a
   fresh worktree** (`data/` is gitignored). The test *has* a skip-guard for exactly this,
   but it is **defective**: it calls `vc.preprocess_patches(vc.bsds_crops(...))` and *then*
   checks emptiness, so `preprocess_patches` raises on the empty array before the skip can
   fire. **This is a real (if minor) in-tree bug, reported not fixed** (not my file —
   PROTOCOL §11.4). Linking the corpus read-only clears all 5.
2. **2 failures** = `test_meaning_inference_migrated.py` — **not vision tests at all.**
   `-k vision` matches them on the substring inside "**provision**al". They fail at
   `0561e70976` independently of anything here.

**Corrected baseline: 153 vision passed / 0 vision failed / 1 skipped**, + 2 pre-existing
non-vision failures. A number without a reproduction is not a baseline (PROTOCOL §10).

---

## 1. THE VACUITY AUDIT — three of the four proposed tests cannot discriminate

The brief's warning ("do not let it become unfalsifiable") is the live risk, and it bites
harder than it looks. Each test below was proposed as decisive; each is vacuous **as
posed**, for a reason that is arithmetic rather than empirical. This section exists so
that the one surviving test is known to be the surviving one.

### 1.1 Interchangeability passes VACUOUSLY when nothing calibrates

`theta` in this layer is an **EMA of the cell's own drive**
(`oo_sunit_adapt_theta`: `theta ← theta + theta_rate·(act − theta)`). It therefore
**chases the mean of whatever it is given**. The reference self-places on *any* input
with a non-degenerate drive — **by construction, not by wave statistics.**

So "waves are interchangeable with other range-exercising inputs" is **guaranteed by the
adaptation mechanism** and is not evidence for the reframe. Worse, a bare equivalence
test **passes when every arm is equally dead** — PROTOCOL §4's "a mechanism must not pass
by making itself inert", in its purest form. **Interchangeability is only informative
conjunctively with calibration actually happening**, which is why the gate below is
conjunctive and why H1 is primary.

### 1.2 Global illumination invariance is TRUE BY ARITHMETIC in BOTH frames

The brief calls this "the decisive, cheap test — run it even if everything else fails."
**It cannot discriminate.** Present `k·I`:

- **Log frame:** `log(k·I) = log k + log I`. An additive constant. The θ-EMA absorbs it
  (`θ → θ + log k·Σw`); `rate = max(act − θ, 0)` is unchanged. **Invariant.**
- **Linear frame:** `act = Σw·(k·I) = k·act₀`. The θ-EMA is **homogeneous of degree 1**,
  so `θ → k·θ₀` and `rate = k·max(act₀ − θ₀, 0)`. The rate scales by `k` — and **RPI and
  OSI are both RATIOS, so `k` cancels exactly. Also invariant.**

**Both frames are invariant, for different reasons, and neither result bears on the
reframe.** Invariance here is a property of *having an adaptive reference at all* — in
either space — not of the log transform. A test whose outcome is fixed by arithmetic
before any agent runs is not a test.

**The non-vacuous version, named for the record and NOT run here:** a **spatially
non-uniform** illumination field `k(x)` (a shadow/gradient). A global adaptation absorbs
a global `k`; it **cannot** absorb a spatial gradient. Log turns `k(x)` into an additive
field that a **local surround subtraction** removes locally; linear cannot. That is a
real double dissociation — **but it requires a surround, which this layer does not have**
(rung 6 has no lateral inhibition; that is rung 7's build, owned by another agent). It is
recorded as the correct future test, not smuggled in.

### 1.3 The GCAL θ-outside-vs-inside contrast is REAL but NOT DIAGNOSTIC — and it is already run

Both accounts — calibration and teaching — predict that BCM's θ (inside the rule, gating
the **sign** of `Δw` via `bcm_potentiate`/`bcm_depress`) can annihilate, and that GCAL's θ
(on the activation function, outside the rule) cannot. **It does not separate the
theories.**

And **rung 6 already ran it.** `oo_sunit_adapt_theta` **is** the GCAL placement, adopted
deliberately (`VISION_RUNG6_PREREG.md`: *"placed on the ACTIVATION function as GCAL does,
where it cannot flip `dw`'s sign"*). Its measured effect is large and is **reproduced in
§2 below**: an ideal split-Gabor scores **OSI 0.0007 / RPI 1.001 without the reference and
OSI 1.0000 / RPI 6.940 with it.** Moving θ out of the learning rule has *already* rescued
what BCM's placement destroyed. **The prediction is confirmed and it is not news, so it is
not spent as this rung's confirmatory test.**

### 1.4 What survives

One question is both non-vacuous and decisive, and the instrument for it already exists
(`rung6_lib.adapt_theta` — θ adapts while `oo_eta=0` holds every weight exactly still):

> **Does the waves' CONTENT do anything beyond placing the REFERENCE?**

- **CALIBRATION account:** `full ≈ theta_only`. The reference is the point; the content is
  not. Waves are a calibration signal.
- **TEACHING account:** `full > theta_only`. The statistics are the point.
- **NEITHER:** `full < theta_only` — waves actively decalibrate (rung 6's hint, §0.2).

This is the reframe's own claim, stated so that all three outcomes are distinguishable.

---

## 2. THE CRITERION, FORMALISED (PROTOCOL §1)

The reframe says the success criterion is **NOT "structure emerged"** but **"a stable,
well-placed operating point exists."** Made precise:

> **RPI (Reference Placement Index) = peak / base**
> = `max_θ F0(θ)` ÷ `baseline`, where `baseline` is the response to **unstructured fields
> at the same duty cycle** (`complex_cells.baseline` — the model's spontaneous rate).

**RPI = 1 means the cell cannot tell structure from noise** — the operating point is
outside the signal (θ too low ⇒ DC-swamped; θ too high ⇒ silent). RPI is a **ratio of two
rates**, hence invariant to overall gain: it measures **placement**, not scale. This is
rung 6's own `peak/base`, unchanged — **not a new measure invented to rescue anything**
(PROTOCOL §5).

### THE CALIBRATION TABLE (measured, `results/calib_measure.log`, burned seeds 0–2)

| reference | **RPI** | OSI |
|---|---|---|
| **IDEAL split-Gabor, θ adapted** = the TARGET | **6.940** | 1.0000 |
| **IDEAL split-Gabor, NO reference** (`homeo=0`) | **1.001** | 0.0007 |
| **untrained random weights, θ adapted** = the FLOOR | **1.9534** | 0.3168 |

**The floor reproduces rung 6's 1.96 / 0.3168 exactly** — the instrument is the same one,
and it is not drifting.

**PROTOCOL §1's three checks:**
1. **Random input scores at a floor** — untrained random weights: **1.9534**. ✔
2. **Ideal exemplar scores high** — **6.940**. ✔
3. **Not duration-confounded** — see the θ fixed point below. ✔

**SESOI, fixed now: 10% of the dynamic range** (floor 1.9534 → target 6.940 ⇒ range
4.987) ⇒ **SESOI = 0.499 RPI**, matching the 10%-of-range convention rungs 3/5/6 used.

### THE HEADLINE OF THE CALIBRATION, AND IT IS THE REFRAME'S BEST EVIDENCE

**A PERFECT Gabor with no reference is USELESS: RPI 1.001, OSI 0.0007.** Content without
calibration is nothing. The reference is not a detail of the readout — it is what makes
held structure functional at all. **The reframe is right about this much, it is measured
here, and it is stated before the run so that it cannot later be claimed as the
confirmatory result.** (It is also rung 6's 0.0006 → 0.9115 finding, on the new measure.)

---

## 3. CONVERGENCE (PROTOCOL §2) — run FIRST, on the formative input alone

**The θ channel — the thing the reframe says is the point — CONVERGES.** Waves only,
weights held exactly still (`oo_eta=0`), seed 0, drift = `Σ|Δθ|/Σ|θ|`:

| steps | RPI | OSI | mean θ | **drift** |
|---|---|---|---|---|
| 25 | 1.001 | 0.0002 | 35.30 | 1.0000 |
| 50 | 1.004 | 0.0007 | 45.11 | 0.2175 |
| 100 | 1.135 | 0.0451 | 48.59 | 0.0716 |
| 200 | 2.024 | 0.4075 | 48.89 | 0.0060 |
| 400 | 1.870 | 0.3145 | 48.86 | 0.0007 |
| 800 | 1.917 | 0.3130 | 48.85 | 0.0003 |
| 1600 | 1.921 | 0.3299 | 48.86 | 0.0002 |
| 3200 | 1.961 | 0.3747 | 48.88 | **0.0005** |

**CONVERGENT + non-zero structure. PASS.** Drift falls ~2000× and θ settles at 48.86.
**RPI plateaus from 200 steps on (1.87–1.96) — the measure is NOT duration-confounded**
in the regime every arm is read at (400 steps). *This is a real fixed point, and it is
the one the reframe names.*

**It also shows the reference doing the work it is credited with:** RPI **1.001 → 1.96**
purely from θ settling, with **every weight held still**. Calibration alone takes a cell
from "cannot tell structure from noise" to the floor.

### The weight channel, and the honest disclosure

**Rung 6 measured the weight channel's convergence and STOPPED the rung on it:** η=5e-4
runs away (drift 0.004 → 0.461); η=1e-4 is stable (drift ≤ 0.009 at 6400) but leaves OSI
at the floor. **The `full` arm below therefore runs at η=1e-4 — rung 6's stable regime —
and η=5e-4 is BARRED** by rung 6's gate. It is not swept; it is excluded.

**Stated plainly, because it is the sharp edge of this design:** rung 6 called η=1e-4
"converges to death" *for its question* ("does content develop?"). **For THIS question,
"the content converges to nothing" is the ANSWER H1 measures, not a confound** — H1 asks
precisely whether wave content adds anything over the reference. PROTOCOL §2's gate is
satisfied on the channel this rung's measure reads (θ: drift → 0.0002 at non-zero
structure). **A null on H1 must NOT be reported as "waves teach nothing in general" — it
is measured in the one stable regime rung 6 left open.** That scope limit is fixed here,
in advance, and it binds the OUTCOME regardless of result.

---

## 4. THE POSITIVE CONTROL (PROTOCOL §1) — is the measure a null instrument?

**The question a null cannot answer: can RPI register calibration at all?** Answered by
the table in §2/§3 and re-stated as the control: the identical probe reads **1.001** for a
cell with no reference and **6.940** for an ideal cell with one, and **1.001 → 1.96** for
an untrained cell as θ settles on waves. **The measure is not null**: it has a ~5× working
range and it moves for the right reason.

**Read narrowly** (rung 3B's lesson): this is instrument calibration containing **no arm
and no hypothesis**. It proves RPI can see a reference being placed. It says nothing about
whether *waves* are what place it — only the arms can test that.

---

## 5. THE ARMS — ablations are DATA (PROTOCOL §0)

No Python branch decides anything about the graph; each arm name selects params the
adapter writes and how many mechanical clock steps it advances.

| arm | params | what it is |
|---|---|---|
| `nocal` | `homeo=0`, `oo_eta=0` | θ pinned at 0. **NO reference.** |
| `theta_only` | `homeo=1`, `oo_eta=0` | θ adapts on the input; **no weight moves.** CALIBRATION, ISOLATED. |
| `full` | `homeo=1`, `oo_eta=1e-4` | θ adapts, then learning armed. Reference **+** content. |

**Inputs**, each a mechanical 16×16 binary field generator (the adapter supplies
unstructured entropy and a clock; **no input carries an orientation the agent is supposed
to grow**):

| input | what it is | range-exercising? |
|---|---|---|
| `waves` | the agent's OWN spontaneous waves — the formative input | *classified, §6* |
| `noise` | unstructured 50%-duty random fields | *classified, §6* |
| `video` | real natural images (BSDS300), median-thresholded | *classified, §6* |
| `static` | ONE random field, held for the whole run | *classified, §6* |
| `blank` | no input at all | *classified, §6* |

**`blank` corresponds to a real condition and it is NOT "dark".** PROTOCOL §6 exists
because "dark = no input" was a design error twice: **dark-reared animals keep their
waves.** `blank` is not a rearing condition — it is the **non-range-exercising** limb of
the dissociation, i.e. an input that cannot drive the operating range. It is labelled as
such and no biological claim is attached to it.

---

## 6. RANGE-EXERCISING IS CLASSIFIED FROM THE INPUT, IN ADVANCE — the anti-circularity gate

**This is the single most important design decision in the document.** "Any input that
exercises the range calibrates equally well" is **unfalsifiable** if "range-exercising" is
read off the outcome. So it is classified **before** the run, from a property of the
**input × anatomy**, measured with **frozen random weights, no learning, θ pinned** — i.e.
a quantity that cannot see any calibration outcome:

> **Drive spread `S` = mean IQR of the unit's `act` over the input ensemble.**
> An input that does not move `act` cannot place a threshold inside it.

**The threshold is fixed now, before the arms:** an input is **RANGE-EXERCISING iff
`S ≥ 0.5`** (in the units `act` is measured in; the ideal-Gabor signal is ±2.3 and Σw⁻ is
~5.6, so 0.5 is a fifth of the signal — an input moving the drive less than that cannot
place a reference in it). The measured `S` per input is reported in §7 **before** the
hypotheses are evaluated, and **the classification is whatever that rule returns** — it is
not adjusted afterwards.

---

## 7. HYPOTHESES

Per seed *i*, each arm's value is the mean RPI over its 6 SUnits. **THE SEED IS THE UNIT
OF ANALYSIS** (PROTOCOL §4).

- **H1 (PRIMARY) — does wave CONTENT add anything beyond the REFERENCE?**
  `d_content = RPI(full, waves) − RPI(theta_only, waves)`, **two-sided**.
  - CALIBRATION account predicts **≈ 0**, tested as **EQUIVALENCE**: the 95% CI must lie
    entirely inside **±0.499**. *A merely non-significant null is not evidence of absence*
    (rung 3's H1b is why).
  - TEACHING account predicts **> 0**.
  - **DECALIBRATION** (rung 6's hint) predicts **< 0**.

- **H2 (co-primary) — does the REFERENCE do the work?**
  `d_ref = RPI(theta_only, waves) − RPI(nocal, waves)`, **two-sided**. Predicted **> 0**.
  **This is the conjunctive guard**: it makes the gate impossible to pass by inertness
  (§1.1). If calibration does not happen, interchangeability means nothing.

- **H3 (co-primary) — INTERCHANGEABILITY among range-exercisers.**
  For each range-exercising input `X ≠ waves` (as classified in §6):
  `d_X = RPI(theta_only, waves) − RPI(theta_only, X)`, tested as **EQUIVALENCE** against
  **±0.499**.

- **H4 (co-primary) — DISSOCIATION from non-exercisers.**
  For each non-range-exercising input `Z`:
  `d_Z = RPI(theta_only, waves) − RPI(theta_only, Z)`, **two-sided**, predicted **> 0**
  and **|d_Z| > SESOI**.

**Bonferroni α = 0.05/4 = 0.0125** per hypothesis family, fixed now.
**SESOI = 0.499 RPI** (10% of the 4.987 range), fixed from burned-seed calibration only.
**Every effect is reported as a % of the 4.987 dynamic range.** *A significant 0.01 is a
lie told with a correct p-value* (rung 3 returned two p=0.0001 effects at 2% of range).

### THE REFRAME IS SUPPORTED iff ALL FOUR hold

1. `|d_content|` 95% CI ⊂ (−0.499, +0.499) — content adds nothing, **and**
2. `d_ref > 0` ∧ `p < 0.0125` ∧ `d_ref > SESOI` — calibration is real and non-inert, **and**
3. every `|d_X|` 95% CI ⊂ (−0.499, +0.499) — range-exercisers interchangeable, **and**
4. every `d_Z > 0` ∧ `p < 0.0125` ∧ `d_Z > SESOI` — non-exercisers dissociate.

H2 and H4 both require a **POSITIVE, above-SESOI** effect, so **the conjunction cannot be
passed by making the mechanism inert** (PROTOCOL §4).

---

## 8. WHAT WOULD FALSIFY THE REFRAME — stated in advance, and meant

The reframe is **REFUTED** by any of:

- **`d_content` > 0 above SESOI** — wave statistics build something the reference does
  not. Waves would be teaching. *(The teaching account's own prediction.)*
- **`d_content` < 0 below −SESOI** — waves actively **decalibrate**. This would refute the
  reframe **in its central claim**: an input whose "fundamental purpose is calibration"
  cannot make the operating point worse than not running it at all. **Rung 6's peak/base
  1.96 → 1.54 predicts exactly this**, and it is the outcome I consider most likely (§9).
- **Any `d_X` outside ±SESOI among range-exercisers** — the statistics matter after all;
  interchangeability fails.
- **Any `d_Z` ≤ SESOI for a non-exerciser** — a mis-placed operating point still yields
  selectivity, so the reference is not what is doing the work.
- **`d_ref` ≤ SESOI** — calibration does nothing measurable, and the whole frame is idle.

**And the standing anti-unfalsifiability rule:** if the conjunction passes ONLY because
every arm is equally dead, that is **not** a pass — H2 and H4 are the guards, and a pass
with `d_ref` at the floor is reported as **vacuous, not supportive**. *"Everything is
calibration" explains nothing.*

---

## 9. MY PREDICTION, STATED IN ADVANCE, WITH ITS PROVISOS

**I predict the conjunction FAILS on H1, in the DECALIBRATION direction: `d_content < 0`.**

Grounds, and they are measured rather than rhetorical: rung 6's peak/base falls from the
untrained floor **1.96 to 1.54** under exactly the arm H1 runs. Under Miller's subtractive
rule on a **sparse, complementary** wave field (ON ~19.5% / OFF ~80.5% active, and
`x_OFF = 1 − x_ON` exactly), the weights drift toward `wmax`/0 and the RF clumps
(clumpiness 0.47 → 0.56 even at η=1e-4). **A clumping RF is a worse-placed operating point
than a random one**, because it raises the response to unstructured fields — which is
precisely `base`, RPI's denominator.

**I predict H2 PASSES, large.** The §3 table already shows 1.001 → 1.96 from θ alone; that
is 19% of the range and ~2× the SESOI. This is close to a foregone conclusion and **is not
where the information is** — it is the guard.

**I predict H3 PASSES (interchangeability holds) — AND I PREDICT IT IS VACUOUS.** The
θ-EMA chases the mean of whatever it is given (§1.1), so waves, noise and video should all
place θ at ~the same point. **This will look like a striking confirmation of the reframe
and it is not one**: it is a property of the EMA, not of the waves, and I am recording
that *before* seeing it so it cannot be sold afterwards. The reframe's interesting content
would be that waves are *special*; interchangeability says the opposite — **the waves are
not doing anything a random field could not do.**

**The proviso that decides H4, and I am genuinely uncertain:** `static` is the sharp case.
It is a single held field, so its drive spread `S` may be ~0 (nothing varies) — in which
case it is a non-exerciser and should fail — **or** the WTA + phase structure of the probe
may still give it spread. **If `static` classifies as range-exercising and calibrates fine,
"exercising the range" is a weaker requirement than the reframe needs.** If `blank` fails
to calibrate, that is the one prediction the reframe makes that the EMA does not make for
free — and even then it is nearly arithmetic (no drive ⇒ no EMA movement).

**What would make me wrong in the interesting direction:** `d_content` landing cleanly
inside ±SESOI *while* `d_ref` is large. That would say waves place a reference and
genuinely teach nothing — the reframe's actual claim, cleanly separated from both the
teaching account and the decalibration hint.

**A NEGATIVE IS THE DELIVERABLE** and will be reported exactly as observed.

---

## 10. n / seeds / statistic

- **Paired within seed. THE SEED IS THE UNIT OF ANALYSIS** (PROTOCOL §4). Units within a
  run share input and compete under WTA ⇒ not independent.
- One-sample **two-sided sign-flip randomisation test**, 20,000 permutations, per
  hypothesis; bootstrap 95% CIs (`scripts/rung4_lib.py`'s `sign_flip_p` / `boot_ci`,
  reused unchanged).
- **n FIXED IN ADVANCE by the variance-only pilot on BURNED seeds 0–13**
  (`results/calib_pilot.log`) — see §7 of the OUTCOME for the realised power.
- **Confirmatory seeds: 10000–10999**, never used for anything. Ledger appended in
  `VISION_PROTOCOL.md`. Burned here: **0–2** (measure calibration, convergence, positive
  control), **0–13** (pilot).
- **Exactly the four hypothesis families listed. No sweeps. No re-runs.** A further attempt
  needs a NEW pre-registration with a NEW mechanism-level hypothesis.

## 11. SCOPE — what this run CANNOT show, whatever it returns (PROTOCOL §8)

- **NOT that the reframe is right or wrong in general.** It is one layer (rung 6's signed
  simple layer), one measure (RPI), one stable η (1e-4 — the only regime rung 6 left open).
- **NOT the log-space claim.** §1.2: global illumination invariance is arithmetic in both
  frames. The non-vacuous test needs a **spatial** illumination gradient and a **surround**,
  which this layer does not have. **Untested, not refuted.**
- **NOT the GCAL θ placement claim.** §1.3: already confirmed by rung 6, not diagnostic
  between the accounts, and not spent as this rung's test.
- **NOT direction, maps, or anything above V1.**
- **NOT a retraction of rungs 1/2/4** — their statistics are properties of the WEIGHTS,
  read with no stimulus presented.
- **NOT that `blank` models a rearing condition.** It is the non-exerciser limb (§5).

---

# 12. OUTCOME / DECISION

# **DECISION: STOPPED AT THE MEASURE-CALIBRATION GATE. The reframe is NOT TESTED.**

**No confirmatory arm was run. No confirmatory seed was consumed. Seeds 10000–10999 are
allocated in the ledger and remain UNUSED and CLEAN.** All work used seeds **0–2**
(measure calibration, convergence, positive control) and **0–13** (variance pilot) — all
already burned. This is the call rungs 5 and 6 made, for the same class of reason.

`engine 95167c01b7b3`, commit `0561e70976`. Logs: `results/calib_measure.log`,
`results/calib_pilot.log`.

## 12.1 THE MEASURE FAILED ITS OWN CALIBRATION — RPI is UNBOUNDED

The variance-only pilot (burned seeds 0–13) was run to fix `n`. It returned this:

```
theta_only RPI per input (burned seeds 0-13)
   input     RPI mean            SD      OSI
   waves        2.1436       0.6682   0.3593
   noise        1.8995       0.2295   0.3473
   video        1.9202       0.2796   0.3437
  static   458642.1464 1044714.4011   0.4160
   blank  1666767.0561 3999039.8076   0.3950
```

**`blank` — the no-input control — scores 1.6×10⁶ against the ideal split-Gabor's 6.94.**

**Diagnosed, not guessed** (per-unit read-out, seed 0):

```
 blank: theta=[48.96 49.04 48.19 48.63 48.60 48.91]
        peak =[0.306 0.103 0.533 0.258 0.511 0.237]
        base =[0.292 0.0125 0.465 0.279 0.496 0.175]
        RPI  =[1.05  8.23   1.15  0.93  1.03  1.35]
```

`RPI = peak/base` has **`base` in the denominator, and `base` → 0** for any unit whose
threshold sits above the unstructured-field drive. Guarded at `1e-9`, so a near-silent
unit scores `≈ peak/1e-9`. Across 14 seeds one such unit produces a mean of 1.6×10⁶ and
an **SD of 4×10⁶**. **No randomisation test can be run on that**, and no SESOI expressed
in RPI units means anything against it.

**The §2 claim that RPI catches BOTH failure modes is WRONG, and it is my error.** I wrote
that "θ too high ⇒ silent ⇒ RPI → 1". **It does not: θ too high ⇒ RPI → ∞.** RPI punishes
a DC-swamped cell and *rewards* a silent one. It is a **half-measure**: sound at the low
end (the ideal-vs-no-reference contrast 6.94 vs 1.001 is real and reproduces rung 6), and
degenerate at the high end.

**This is PROTOCOL §1 working exactly as designed.** The defect was found by the
pre-registered instrument checks, on burned seeds, **before any hypothesis was gated and
before any confirmatory seed was spent** — the same way rung 3B's positive control caught
its probe training on its own stimulus, and rung 5's ideal exemplar caught its missing
rectification. **It is not metric surgery (PROTOCOL §5): no gate had failed and no
hypothesis had been tested.** Repairing RPI and re-running would be a NEW
pre-registration; it is **not** done here, because the repair is not obvious (see §12.4).

## 12.2 THE RANGE-EXERCISE THRESHOLD I FIXED IN ADVANCE WAS MIS-SET — disclosed, not adjusted

§6 fixed **`S ≥ 0.5`** as range-exercising, reasoned from the ideal-Gabor signal (±2.3).
Measured (frozen random weights, no learning, θ pinned — the classifier is blind to
outcome, as designed):

```
RANGE-EXERCISE CLASSIFIER
   input   drive IQR
   waves      0.2549
   noise      0.3192
   video      0.3518
  static      0.0000
   blank      0.0000
```

**By my own pre-registered rule, NOTHING is range-exercising** — waves included. The
threshold was set from the wrong scale. **The classifier itself works, and works well:**
the separation is **totally bimodal** — `{waves, noise, video}` at 0.25–0.35 versus
`{static, blank}` at **exactly 0.0000**, a gap of 0.25 with no intermediate case. Any
threshold in (0, 0.25) gives the same partition.

**It is recorded as mis-set rather than quietly re-thresholded.** Since the rung stops
anyway, nothing rides on it — but a future attempt must fix the threshold from a **burned-
seed pilot of the drive scale**, not from an a-priori guess about it. That is the honest
version of PROTOCOL §3.3, and my in-advance number was wrong by ~2×.

## 12.3 THE FINDING THAT SURVIVES THE STOP — the reference is placed by the ANATOMY, not the waves

**Measured, seed 0, `theta_only` (θ adapts, no weight moves):**

```
 waves: theta = [49.10 48.97 48.40 48.72 48.83 49.00]
 blank: theta = [48.96 49.04 48.19 48.63 48.60 48.91]
```

**The waves and NO INPUT AT ALL place the reference in the same place, to ~0.5%.**

The mechanism is structural: with a blank field `x_ON = 0`, so `x_OFF = 1 − x_ON = 1`
identically, and `act = Σw⁻` — the **tonic drive**. The θ-EMA converges to it. With waves,
`act` fluctuates *around* the same tonic drive. **θ lands on `Σw⁻` either way.**

> **The operating point is set by the ARCHITECTURE'S TONIC DRIVE, not by the input's
> statistics.** The θ-EMA chases the mean of whatever it is given, and — because the
> complementary split `x_OFF = 1 − x_ON` pins that mean to the tonic drive — *what it is
> given barely matters.*

**This is §1.1's vacuity, confirmed by measurement rather than argued:** interchangeability
in this layer is a property of the EMA and the complementary split, **not** a discovery
about waves. Had the confirmatory run gone ahead on a working measure, H3 would very
likely have "passed" — and it would have been **vacuous**, exactly as predicted in §9.
**H4 (dissociation from non-exercisers) would have FAILED**: `blank` calibrates θ to the
same point as waves.

**Stated with its scope:** this is n=1 seed, one layer, and it is a **diagnostic, not a
hypothesis test** (rung 6's convention). It is reported because it is the mechanism behind
the pilot's numbers, not as a result. **It is, however, the sharpest thing this rung found,
and it points AGAINST the reframe's central claim** — an input whose "fundamental purpose
is calibration of a fixed point" should not be replaceable by *no input at all*.

**And it is the same degeneracy rung 6 diagnosed, one level down.** Rung 6: `x_OFF = 1−x_ON`
is a ONE-WAY definition, so `C_ON,OFF(d) = −C_ON,ON(d)` identically and the channels carry
no independent correlation structure. Here the same identity pins `E[act]` to `Σw⁻`
regardless of input. **The complementary split does not merely fail to give waves anything
to sculpt — it also makes the reference input-independent.** One structural fact, two
consequences.

## 12.4 WHY THE OBVIOUS REPAIR IS NOT MADE HERE

A bounded index (`(peak−base)/(peak+base)`) still → 1 as `base` → 0: it re-scales the
degeneracy, it does not remove it. A conjunctive gate (`base` low **AND** `peak` above an
absolute floor) needs an **absolute** responsiveness scale — and RPI was chosen as a ratio
*precisely because* it is gain-invariant. **Fixing the measure means deciding what
"responsive" means in absolute units, which is a modelling decision, not a metric tweak.**
Per PROTOCOL §5 that is a **new pre-registration with its own mechanism-level hypothesis**,
and it is named here, not smuggled in.

## 12.5 MY PREDICTION — partly held, and the proviso that broke is the informative part

§9 predicted: **H1 fails in the decalibration direction; H2 passes large; H3 passes and is
VACUOUS; H4 uncertain, `static` the sharp case.**

- **H3's vacuity prediction HELD, and was confirmed by mechanism** (§12.3): θ lands on the
  tonic drive whatever the input. Recording it in advance is what stops it being sold as a
  confirmation.
- **H2's direction HELD** in calibration: 1.001 → 1.96 from θ alone (§3), 19% of range.
- **H1 and H4 are UNTESTED.** The measure died first.
- **THE PROVISO THAT BROKE, and it broke my whole design:** I predicted `static` was the
  sharp case for H4. **It is `blank` that is sharp, and for a reason I did not anticipate —
  not that it fails to calibrate, but that it calibrates *identically to waves*, and then
  breaks the measure by doing so.** I had reasoned that a non-exerciser would leave θ
  unplaced. The complementary split means a blank field is **maximal drive on the OFF
  channel** — it is not an absence of input, it is a *saturating* one. **`blank` is not the
  non-exerciser I designed it to be**, and the drive-IQR classifier scoring it 0.0000
  (zero *variance*, not zero *drive*) is what concealed that. **A zero-spread input is not
  a zero-drive input, and my classifier cannot tell them apart.** That is a real design
  error, it is mine, and it would have invalidated H4 even on a working measure.

## 12.6 WHAT IS AND IS NOT ESTABLISHED

**Established (measured, reproducible, engine-stamped):**
1. **A perfect Gabor with no reference is USELESS: RPI 1.001, OSI 0.0007** — against 6.940
   / 1.0000 with one. **Content without calibration is nothing.** This is the reframe's
   best evidence, it is real, and it reproduces rung 6's 0.0006 → 0.9115 on a new measure.
2. **The θ channel has a genuine fixed point:** drift 1.0 → **0.0002**, θ → 48.86, RPI
   plateaus from 200 steps. Not duration-confounded (PROTOCOL §1.3, §2). ✔
3. **Calibration alone lifts an untrained cell 1.001 → 1.96** with every weight held still.
4. **The floor reproduces rung 6 exactly** (1.9534 / 0.3168 vs 1.96 / 0.3168).
5. **The drive-spread classifier separates inputs bimodally** (0.0000 vs ≥0.2549) — but
   measures *variance*, not *drive*, and §12.5 is why that matters.

**NOT established — and this is the deliverable:**
- **The reframe is NOT TESTED, in either direction.** It is neither supported nor refuted
  here. The forward test did not run.
- **Interchangeability is NOT shown**, and §12.3 predicts that if it were shown it would be
  an artifact of the θ-EMA + the complementary split.
- **Nothing about log-space, illumination invariance, or the GCAL θ placement** — §1.2 and
  §1.3 give the arithmetic reasons those tests cannot discriminate as posed.
- **Retrodiction remains not-evidence.** The six retrodictions the reframe arrived with are
  unchanged in status by this document, and §0.2 adds a **seventh that points the other
  way**.

## 12.7 THE NAMED NEXT HYPOTHESES (NOT run, NOT built here)

Each needs its own pre-registration with its own mechanism-level hypothesis — **not a
parameter sweep, and not a metric tweak.**

1. **An ABSOLUTE responsiveness scale**, so a silent cell and a discriminating cell are
   distinguishable (§12.4). Until that exists, "well-placed operating point" has no
   two-sided measure in this tree, and **the reframe's own success criterion cannot be
   scored.** This is the blocker.
2. **A non-exerciser that is genuinely a non-exerciser** (§12.5). Under the complementary
   split, `blank` is maximal OFF drive. A true zero-drive control needs `x_ON = x_OFF = 0`
   — which the split forbids. **The dissociation limb of the reframe's signature may not be
   constructible in this layer at all.**
3. **Break the complementary split** — rung 6's named-next #1 (independent correlation
   structure via retinal lateral inhibition **as a rule**), now doubly motivated: it is
   what pins the reference to the tonic drive (§12.3) as well as what starves the weights.
   **Owned by another agent (rung 7); not touched here** (PROTOCOL §11.4).
4. **The spatial illumination GRADIENT test** (§1.2) — the non-vacuous form of the log-space
   claim. Needs a surround, i.e. rung 7.
