# CHECKING THE ABDUCED INTERMEDIATES — PRE-REGISTRATION

*Written and committed BEFORE any implementation and before any number (§3).*

Branch **`worktree-agent-a5d492924e2f17364`** — the name I actually see; no
`gamma-substrate/gapverify` name exists. Base SHA
**`91e367f0c332ae29793609c6816f5ba42971d6eb`**.

**SEED BLOCK: 105000–105999.**

---

## §3 CLAUSE 8 — THE VERBATIM `check_claim` OUTPUT

```
SEED CLAIM 105000-105999: CLEAN -- no collision DETECTED.
  Scope: 807 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**497 unresolved sink sites tree-wide.** The claim is "no collision DETECTED",
never "no collision exists", and the silence is priced here rather than
paraphrased away.

---

## 1 — THE LEVER, AS THE PREDECESSOR NAMED IT

`VISION_GAPABDUCE_RESULTS.md` §9.1:

> The abduced intermediates are **emitted (`bridged`) and CHECKED AGAINST
> NOTHING.** In a scene with any other content they make a **falsifiable
> prediction at every gap tick** — that would make interpolation
> **REFUSABLE**, and it is **the first mechanism here whose ISI curve COULD
> have an interior optimum**, since a longer gap means MORE PREDICTIONS TO
> VIOLATE.

`GapAbduce`'s measured deficit: independent random endpoints accept at
`~1/steps` (43/37/22/19% at k=1..4) **because any two same-shape figures ARE
rigid translates**. Divisibility is its only constraint.

**This rung builds the check.**

---

## 2 — THE MECHANISM: `GapVerify` (new Rust Term, ADDITIVE)

`GapAbduce` consumes `[visible.. , EMPTY.. , visible..]` and abduces
`G` with `G^steps(f_before) = f_after`. It emits `bridged` — the intermediates
`G^t(f_before)` — **and never compares them to anything.**

`GapVerify` consumes the SAME shape of sequence except that **the gap frames
are OBSERVED, not blank**: the moving figure is absent, the rest of the scene
is present. It then does the thing the predecessor named:

**STRICT ACCOUNTABILITY.** For each gap tick `t = 1..gap`, every predicted
cell of `G^t(f_before)` must COINCIDE (exact integer coordinate equality, all
coordinate slots) with some cell actually OBSERVED in gap frame `t`.
`violations` counts predicted cells with no observed cell at their
coordinates. `verified` iff `violations == 0`.

The semantics is occlusion accountability: *if the figure is predicted
somewhere it would have been visible, and nothing was observed there, the
interpolation is FALSIFIED.* This is the tunnel effect's admissibility
condition, and it is what makes interpolation REFUSABLE.

### The structure split, generalised — and it REDUCES to the incumbent's

`GapAbduce` splits on an EMPTY run. `GapVerify` splits on **surface
disappearance**: cells are partitioned by `surface_key` (their non-coordinate
slots — the criterion `infer_translate_offset` and `DepthInfer` already use),
and a gap frame is one whose surface-key set is a STRICT SUBSET of the banks'.
**An empty frame's key set is `{}`, a strict subset of any non-empty set — so
on a blank-gap stimulus the split is IDENTICAL to `GapAbduce`'s.** That
reduction is arm A1, and it can fail: it is different code.

### The abduction, per surface

Every surface shared by the two banks must be RIGID (`infer_translate_offset`,
unmodified). `MOVING` = the surfaces with non-zero displacement; **exactly one
is admitted** (`multi_motion` otherwise — multiple velocities are `DepthInfer`'s
territory, not this rung's). `HIDDEN` = surfaces present at both banks and
absent in every gap frame. When `gap >= 1`, `HIDDEN` must equal `MOVING`
(`hidden_mismatch` otherwise — *what vanished must be what moved*). When
`gap == 0` there are no intermediates and verification is VACUOUS, on the same
code path — **no mechanism is spliced in at one end of the curve** (the
predecessor's error #4, inherited as a constraint).

Admissibility of the abduction is UNCHANGED: `D[i] % steps == 0`, exact integer
arithmetic, plus the same `steps`-th-root linear fallback within `max_b`.

### §13 — NO NUMBER ENTERS THE MECHANISM

Coverage is exact coordinate equality; the verdict is `violations == 0`, an
equality against the sentinel `0`. **There is no tolerance and nowhere to put
one** — the same strongest-§13 outcome the predecessor reached: not a number
that falls out, but NO NUMBER AT ALL.

**REGISTERED IN ADVANCE (the brief's clause):** *if checking intermediates
forces a tolerance on me, I will REPORT THAT AS A FINDING rather than pick a
number.* I claim now that it will not, because the predicted cells and the
observed cells are both integer coordinate tuples in the SAME frame — an
in-frame comparison, which the frame/continuum invariant says MUST be integer.
**If I find myself wanting a "close enough" radius, that is evidence the
comparison has become CROSS-frame, and I will report it as such.**

---

## 3 — THE STIMULUS

Inherited configuration, declared as CONFIGURATION and nothing stronger
(§13, weak claim: bound once, never a verdict threshold): `DOT = 4`,
`FIELD_H = 24`, `FIELD_W = 160`, `BG = 0`, `FG = 255`, `ROW = 8`,
`DT = ["pred","coord:r","coord:c","val"]`.

**NEW configuration, this rung's:** the OCCLUDER — a static full-height bar of
luminance `OCC = 128` occupying columns `[B0, B0+BW)` with `B0 = 68`,
`BW = 20`. It is a distinct SURFACE (its non-coord slots differ from the dot's),
so the graph separates it from the figure without being told which is which.

`v` = the per-step displacement = `D / steps`.

---

## 4 — HYPOTHESES AND PREDICTIONS (two-sided, stated in advance)

### P1 — EQUIVALENCE (low weight, mechanical, but able to fail)

On the classic BLANK-gap phi grid (`S_GRID × K_GRID`, 72 cells), `GapVerify`'s
ABDUCTION fields (`abduced`, `offset`, `closes`, `correction`) are **identical
cell-for-cell to `GapAbduce`'s**. Verification is a strict ADDITION.

**Prediction: 72/72 identical.**

### P2 — THE PAIRED CONTRAST: IS INTERPOLATION REFUSABLE? *(the headline; NOT forced)*

Two stimuli with **IDENTICAL ENDPOINTS** — same `f_before`, same `f_after`,
same gap length, same abduced `G`, same `closes`, same `correction = 0` —
differing ONLY in the observed gap content:

* **COVERED**: the bar spans the predicted path ⇒ `violations = 0`, `verified`.
* **EXPOSED**: the same bar displaced off the predicted path ⇒
  `violations > 0`, REFUSED.

**Prediction: `GapAbduce` returns the IDENTICAL verdict on both (it never
looks); `GapVerify` separates them.** This is also the §1 clause-5 vacuity
gate: `D = max|on − off|` on the downstream attributes must be non-zero.

**A NULL HERE KILLS THE RUNG**: if `GapVerify` cannot separate two stimuli that
differ only in the gap content, the check is decorative and I stop.

### P3 — THE TUNNEL CLIFF: A NUMBER THAT FALLS OUT *(the risky quantitative one)*

Hold the SPEED fixed (`v = 4`) and the bar fixed (`BW = 20`); vary `k`. The dot
enters flush with the bar's left edge (`c1 = B0 − DOT`) and exits at
`c1 + v·(k+1)`, so `D = v·steps` is **divisible at every k** — the arithmetic is
neutralised and only the GEOMETRY decides.

Coverage of tick `t` requires `t·v >= DOT` and `t·v <= BW`. Both bind at the
extremes, giving **`verified` iff `v >= DOT` AND `k <= BW / v`**.

**Prediction, with `v = DOT = 4` and `BW = 20`: `k_max = BW/v = 5` EXACTLY.
Verified for `k = 0..5`; REFUSED for `k = 6..11`. `GapAbduce` accepts all
12/12.**

**This cutoff is a §13 number that FALLS OUT of the geometry** — the duration
an object of width `DOT` moving at `v` can be hidden by a bar of width `BW`. It
is not tuned; it is predicted to the exact integer before the run, and **a
cliff at any other k falsifies my model of my own mechanism.**

### P4 — THE ISI DISCRIMINATOR, AND WHY I REGISTER IT AS UNREACHABLE

**THE TRAP, INHERITED AND EXPLICIT: the discriminator is the LOCATION of the
maximum, NOT non-monotonicity.** The predecessor's curve was a non-monotone
divisor comb (1.000, 0.889, 0.222, 0.667, …) and a rung asking only "is it
monotone?" would have scored it as CONFIRMING an interior optimum and published
the opposite of the truth. The three branches, fixed here:

| branch | condition |
|---|---|
| **INTERIOR OPTIMUM** | `k* != 0` AND `R(k*) > R(0)` **strictly** |
| **FALSIFIES** | `R(0) >= R(k)` for every `k` |
| **AMBIGUOUS** | `R(0)` is a maximum but **TIED** with some `k >= 1` |

**AN AMBIGUOUS CURVE, SPELLED OUT SO I CANNOT REINTERPRET IT LATER:** a
plateau — `R(0) = R(1) = … = R(j) > R(j+1)` — reads **AMBIGUOUS**, not
FALSIFIED and not INTERIOR. P3 predicts exactly that shape (`R = 1` for
`k = 0..5`, `0` after), so **I expect AMBIGUOUS on the tunnel stimulus.**

**§13.1 DECLARED IN ADVANCE — THE INTERIOR BRANCH IS UNREACHABLE FOR THIS
MECHANISM, AND THAT REFUTES THE PREDECESSOR'S NAMED LEVER A PRIORI:**

1. **Verification is a MONOTONE FILTER.** It can only REMOVE acceptances:
   `R_verified(k) <= R_abduce(k)` for every `k`, by construction.
2. **`R(0) = 1` is DOUBLY FORCED** — every integer is divisible by 1 (the
   predecessor's forcing), AND at `gap = 0` there are ZERO intermediates, so
   verification is vacuous.
3. An interior optimum requires `R` to RISE above `R(0)`. **A filter cannot
   raise anything.** Therefore no amount of "more predictions to violate" can
   produce one.

**So the predecessor's intuition — "the first mechanism whose ISI curve COULD
have an interior optimum" — is WRONG, and it is wrong DERIVABLY, before the
measurement.** More predictions to violate lowers the curve at large `k`; it
cannot raise it at small `k`. **The ISI arm therefore carries ZERO evidential
weight and is run only to confirm the implementation matches the derivation** —
the posture the predecessor took on `R(0) = 1`, applied to the whole arm.

**Where the predecessor's intuition IS right, and it is a different
quantity:** DISCRIMINATION (P5) should GROW with the gap, because more
intermediates means more chances for noise to be refused. **The curve and the
discrimination are different quantities, and only one of them was ever going to
move.**

### P5 — THE NOISE ARM: DISCRIMINATION AGAINST AN ANALYTIC EXPECTATION *(deepest arm)*

n = 100 per `k`, `k = 0..7`, **seeds 105000–105799**, endpoints drawn
independently and uniformly from `[0, FIELD_W − DOT)`, with the FIXED bar
present in every gap frame.

**THE ANALYTIC EXPECTATION IS COMPUTED BY EXHAUSTIVE ENUMERATION OVER THE
SAMPLING GRID, INSIDE THE RUNNER, BEFORE THE ARM IS READ** — a FORMULA, never a
remembered approximation (the predecessor's method; the timephi rung's lesson
about a "noise" control that was not one):

```
E_abduced(k)  = mean over (c1,c2) of [ D != 0  and  D % steps == 0 ]
E_verified(k) = mean over (c1,c2) of [ D != 0  and  D % steps == 0
                                       and  for all t in 1..k:
                                            B0 <= c1 + t*v  and  c1 + t*v + DOT <= B0+BW ]
```

**Predictions:**

* `E_abduced` reproduces the predecessor's `~1/steps` (a replication check).
* **`E_verified(k) << E_abduced(k)` for every `k >= 1`**, and every measured
  cell within **2 SE** of its analytic expectation.
* **The CONDITIONAL discrimination `P(verified | abduced)` DECREASES with `k`**
  — more intermediates, more chances to refuse.
* At `k = 0`: **FORCED equal** (no intermediates), declared in advance.

**A refusal must be a FAILURE AFTER A FULL SEARCH, not a refusal at a guard**
(the brief's constraint). Every refusal reports `ticks` (intermediates actually
generated) and `predicted` (cells actually compared). **A refusal with
`ticks == gap` and `predicted > 0` is a measured failure; a refusal with
`predicted == 0` is a guard and I will report it as a §13 negative.**

### P6 — BLANK-GAP STRICTNESS *(FORCED, declared, zero weight)*

On the classic blank-gap phi stimulus there is NOTHING observed in the gap, so
every predicted cell is unaccounted: `violations = predicted > 0`, refused, at
every `k >= 1`. **FORCED by construction** — run only to confirm the source
reading against the REAL ENGINE, which is the thing a doc comment failed at
four times this week.

**And it is a SCOPE STATEMENT, not a win:** under strict accountability the
substrate becomes **MORE REFUSING THAN A HUMAN** on classic phi. A human sees
motion across a blank ISI; this mechanism refuses it. I register that in
advance so it cannot be presented later as a feature.

---

## 5 — CONTROLS, RUN FIRST (§1 clauses 4 and 5; §10.2)

* **A0-POS** — a covered tunnel passage: abduced AND verified, `violations = 0`.
* **A0-NEG** — a stationary dot: REFUSED as `identity`. The reader discriminates.
* **A0-CODEBOOK** — the in-process paired POSITIVE probe on a known-good
  abduction (the predecessor's corrected design). **NOT** a read of `coord_dims`
  off the measured call: that field is hardcoded empty by the refusal
  constructor, so it is an OUTPUT of the verdict and made 167 false accusations
  for the timephi rung.
* **A0-FIELD** — `refused()` calls `finish()`, **which SELECTS the field**. The
  predecessor's patch restoring `total` on a refusal SILENTLY DID NOTHING and
  was caught by a mechanism test, not by inspection. **Every field this rung
  reads off a REFUSAL (`violations`, `ticks`, `predicted`, `total`, `reason`)
  is asserted non-degenerate on a known refusal, in a test.**

**If A0 fails, no arm is interpretable and the run ABORTS (`return 3`).**
Engine divergence inside the measuring process ABORTS (`return 2`).

---

## 6 — DECISION RULE

| P2 (paired contrast) | P3 (cliff at `BW/v`) | reading |
|---|---|---|
| separates | at 5 exactly | **INTERPOLATION IS REFUSABLE, and its horizon falls out of the geometry** |
| separates | elsewhere | refusable, but my model of my own mechanism is wrong — report the measured cliff and diagnose |
| does not separate | — | **the check is DECORATIVE (§13.2). The rung is a negative and I say so.** |

**What a null means:** if P2 nulls, `GapVerify` is decoration and the honest
report is that checking the intermediates does NOT make interpolation
refusable. If P5 shows `E_verified ≈ E_abduced`, the check runs but buys no
discrimination — also a negative, and a more interesting one, because it would
mean the scene content does not constrain the abduction.

**No sweeps. No re-runs. Exactly the arms above.** A further attempt needs a new
pre-registration with a new mechanism-level hypothesis.

---

## 7 — §9, §10, §11 COMPLIANCE, DECLARED IN ADVANCE

* **Rust is ADDITIVE.** `GapVerify` is appended at the END of the enum
  (index **176**); `GapAbduce`'s 175 and every prior index are UNMOVED. No
  existing Term, evaluator or seed is touched.
* **The seed is flag-gated OFF by default** (`gap_verify_enabled` absent) and
  additionally matches only `status == "gap_vseq"`.
* **The oracle must be 222/0 with `data/` BEFORE and AFTER.** Baseline taken
  before any code: **222 passed / 0 failed**, provenance gate **7 passed**.
* **THIS RUNG ADDS RUST, so it MUST build its own engine**
  (`scripts/engine_build.sh`) — a worktree that does not is refused, not
  trusted. The provenance verdict is taken as **its own step before any
  number**, AND `provenance_line()` is re-read from inside the measuring
  process and compared against `EXPECT_ENGINE`, aborting on divergence.
* **I own only my own files.** `term.rs`'s stale `BlinkBridge` doc comment
  (reported by two predecessors, still unedited) is NOT mine to fix and I will
  not touch it.

---

## 8 — WHAT THIS RUNG WILL NOT SHOW (§8, in advance)

* **Nothing about human phi's mechanism.** No human data is measured.
* **Every result is CONDITIONAL on a figure/ground split the ADAPTER supplied.**
  The timephi A1 bound is inherited UNCHANGED: `infer_translate_offset` cannot
  consume a bounded pixel field at all.
* **Occlusion ORDER is not inferred.** The mechanism cannot tell "behind the
  bar" from "in front of it"; it only asks whether SOMETHING was observed where
  the figure was predicted. A figure predicted in front of an occluder would be
  wrongly accounted. **That is a real limit of strict accountability and it is
  declared here, not discovered later.**
* **One dot, one bar, one shape, one size, horizontal only, uniform
  background.** A textured background is NOT run.
* **Multiple simultaneous motions are REFUSED, not handled** (`multi_motion`).
* **No timing claim of any kind.** Every quantity is exact or counted.

---

## 9 — ADDENDUM, WRITTEN AND COMMITTED BEFORE ANY NUMBER

*Two design errors in §4 above, found while implementing the stimulus and
BEFORE any measurement was taken. Corrected here rather than silently, and
carried into the results as "what I got wrong". Nothing below is a
reinterpretation of data — no arm has been run.*

### 9.1 — P3's TUNNEL WAS NOT A PASSAGE

§4's P3 held the SPEED fixed and let the exit position grow with `k`. That is
not a tunnel: for `k < 5` the dot never reaches the far side of the bar, and at
`k = 0` its exit position lands INSIDE the bar, where the dot occludes the bar
and breaks the bar surface's own rigidity. **The `k = 0` point would have
refused for a reason that has nothing to do with the hypothesis.**

**CORRECTED STIMULUS — a genuine full passage, fixed at both ends:** the dot
enters flush at `c1 = B0 − DOT = 64` and exits flush at `c2 = B0 + BW = 88`, so
**`D = BW + DOT = 24` is FIXED** and `v = D/steps` varies with `k`. Both banks
have the dot DISJOINT from the bar, at every `k`.

Coverage still requires `v >= DOT`; divisibility still requires `steps | D`.

**CORRECTED PREDICTION, stated before the run:**

> **`GapVerify` verifies iff `(k+1) | 24` AND `24/(k+1) >= 4`, i.e. exactly
> `k ∈ {0, 1, 2, 3, 5}` over `k = 0..11`.**
> **`GapAbduce`'s divisibility alone admits `k ∈ {0, 1, 2, 3, 5, 7, 11}`.**
> **The two disagree at EXACTLY `k = 7` and `k = 11`** — the cells where the
> arithmetic is fine but the object could not have been hidden.

`k_max = D/DOT − 1 = BW/DOT = 5` — **the same cutoff, still falling OUT of the
geometry**, now on a stimulus where it is the only thing that can bite.

### 9.2 — P2's "IDENTICAL VERDICT FROM `GapAbduce`" WAS NOT WELL-POSED

§4's P2 asserted `GapAbduce` returns the identical verdict on COVERED and
EXPOSED. It cannot: `GapAbduce` splits on an EMPTY run, so on a stimulus whose
gap frames are OCCUPIED it finds no gap at all and falls into its degenerate
last-two-frames branch — and those last two frames DIFFER between COVERED and
EXPOSED. **The comparison I registered is not the comparison the incumbent can
make.**

**CORRECTED, and it is strictly cleaner:**

1. **The paired contrast is WITHIN `GapVerify`.** COVERED and EXPOSED share
   BYTE-IDENTICAL bank frames and differ ONLY in the observed gap content
   (EXPOSED shows the bar displaced 40 columns left, off the predicted path).
   **Every abduction field (`abduced`, `offset`, `closes`, `correction`) must
   be IDENTICAL across the pair; only `verified`/`violations` may move.** That
   is a sharper §1-clause-5 vacuity demonstration than the original: the
   mechanism is shown to move the verification attributes *while provably
   moving nothing else*.
2. **The incumbent's role is stated where it is honest:** on the BLANK-gap
   encoding of the SAME passage — its native input — `GapAbduce` ACCEPTS
   (`correction = 0`). **The incumbent accepts a passage whose intermediates
   are unverifiable, because it has no notion of an occupied gap.**

### 9.3 — P5's REGISTERED ANALYTIC FORMULA IS INCOMPLETE

§4's formulas omit a condition the mechanism genuinely applies: **every shared
surface must be RIGID**, and a drawn endpoint whose dot OVERLAPS the bar
occludes it, changing the bar's cell count between banks ⇒ `not_rigid`. The
registered `E_abduced` therefore OVERSTATES the acceptance rate on the drawn
grid, and it does so by an amount I did not foresee at registration.

**I will NOT restrict the draw range post hoc** — that is forking paths (§4).
The seeds and the range stand exactly as registered. Instead **three analytic
columns are reported**: the REGISTERED formula verbatim, an EXACT formula that
additionally requires bank rigidity, and the verified rate; plus the measured
**refusal breakdown by `reason`**, so the gap between the registered formula
and the mechanism is a reported quantity rather than a discrepancy to explain
later.
