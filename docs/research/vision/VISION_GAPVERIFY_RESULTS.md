# CHECKING THE ABDUCED INTERMEDIATES — RESULTS

Pre-registration `VISION_GAPVERIFY_PREREG.md`, committed **`5e2c34cb`** before
any implementation and any number; **addendum `1f4ca5a7`**, also before any
number (three design errors of my own, §11). Branch
**`worktree-agent-a5d492924e2f17364`** — the name I actually see; no
`gamma-substrate/gapverify` name exists. Base SHA
**`91e367f0c332ae29793609c6816f5ba42971d6eb`**.

Engine **`d657468d9e1f`** (`own` build, `scripts/engine_build.sh`) — **THIS RUNG
ADDS RUST.** Provenance gate as its **own step before any number**:
`tests/test_engine_provenance_migrated.py` **7 passed** (and again, 7 passed,
after every change) — and `provenance_line()` is ALSO printed **from inside the
measuring process** and compared against `EXPECT_ENGINE`, **aborting on
divergence**.

Oracle `scripts/rung7_vision_bench.sh`: **222 passed, 0 failed** — `data/`
symlinked (§10.2, the with-corpus case). **Baseline taken before any code:
222 / 0. Re-run after all changes: 222 / 0, unchanged.**
Rust: `cargo test --lib -- --test-threads=1` **622 passed, 0 failed, 4
ignored**, including **`variant_table_covers_the_enum`** — the gate that proves
the additive enum change is complete. *(It required a link flag, and that is a
finding, not a footnote — §11.4.)*

Gates: `tests/test_gapverify_ast_migrated.py` **10 passed**;
`tests/test_gapverify_mechanism_migrated.py` **8 passed**;
`tests/test_instrument_seams_migrated.py` (§3 clause 8) **22 passed**.

Seeds **105000–105999**, `check_claim` recorded verbatim in the
pre-registration **including its 497 unresolved sinks**. **Measured with
`scripts/seed_audit.py`: 800 resolved (105000–105799), `unknown_sinks: 0`,
`parse_errors: 0`, none outside the block.** `python3 -m domains.seed_record
--write` run; the block appears as an undeclared run pending the supervisor's
ledger merge (§10 of this file — `VISION_PROTOCOL.md` is not mine to edit).

---

## THE HEADLINE, IN SIX LINES

**INTERPOLATION IS NOW REFUSABLE, AND THE PREDECESSOR'S NAMED LEVER SPLITS IN
TWO — RIGHT ABOUT DISCRIMINATION, WRONG ABOUT THE CURVE, AND WRONG DERIVABLY.**

`GapAbduce` accepts independent random endpoints at `~1/steps` because
divisibility is its only constraint. With the intermediates CHECKED against what
was actually observed, the conditional acceptance
**`P(verified | abduced)` collapses 1.000 → 0.216 → 0.000** across `k = 0,1,2`
and stays 0 to `k = 7` — **every one of 16 noise cells within 1.29 SE of an
analytic expectation computed by exhaustive enumeration before the arm was
read.**

**The paired contrast is the mechanism's proof and it is not forced:** two
stimuli with **byte-identical banks**, differing ONLY in what the gap frames
show, receive different verdicts — while **every abduction field is provably
IDENTICAL** (`offset (0,8)`, `closes`, `correction 0`). The check moves the
verification attributes and **provably moves nothing else**.

**The tunnel cliff landed on the exact predicted integer.** Verification admits
`k ∈ {0,1,2,3,5}`; the abduction alone admits `{0,1,2,3,5,7,11}`; they part
company at **exactly `{7, 11}`** — both registered as set equalities before the
run. The cutoff `k_max = BW/DOT = 5` **falls OUT of the geometry**.

**The ISI curve is AMBIGUOUS (tie), `k* = 0`, tied with `k = 1,2,3,5` — and the
interior optimum was declared UNREACHABLE A PRIORI.**

---

## 0 — THE WIRING CONTROLS, RUN FIRST

*Three predecessors' traps, all built before any hypothesis arm.*

| control | result | |
|---|---|---|
| **A0-POS** covered passage, gap 2 | abduced, verified, `violations 0`, `predicted 32`, `status = gap_verified` | wiring **live** |
| **A0-NEG** stationary dot, same bar | refused, `reason = "identity"` | reader **discriminates** |
| **A0-FIELDS** a known refusal | `reason unverified`, `ticks 2 == gap 2`, `predicted 32`, `covered 0`, `violations 32` | **the refusal's fields are MEASURED, not constructor defaults** |
| **A0-CODEBOOK** | **0 violations across every measured call** | paired in-process POSITIVE probe |

**A0-FIELDS exists because of the predecessor's second recorded error:**
`refused()` calls `finish()`, **which SELECTS the field**, so its patch
restoring `total` on a refusal *silently did nothing* on every call that asked
for it — an output of the constructor masquerading as a measurement, caught by
a mechanism test rather than by inspection. Every field this rung reads off a
refusal is therefore asserted **independently, one Term evaluation per field**,
which is exactly the shape in which that bug surfaces.

**A0-CODEBOOK is the timephi rung's corrected design, not its broken one:** a
paired POSITIVE probe on a known-good abduction in the same booted substrate —
**never** a read of `coord_dims` off the measured call, since the refusal
constructor hardcodes that field empty and it therefore made **167 false
accusations**.

---

## 1 — A1: THE ABDUCTION IS UNCHANGED (P1)

The surface-set split GENERALISES `GapAbduce`'s empty-run split — an empty
frame's key set is `{}`, a strict subset of any non-empty set — so on the
classic blank-gap grid the two must agree. **This is different code and it could
have disagreed.**

**72 cells (`S_GRID × K_GRID`), fields `vabduced`/`vcloses`/`voffset`/
`vcorrection`/`vsteps`, compared against `GapAbduce` on the identical frames:
0 disagreeing cells. P1 confirmed 72/72.**

Verification is a strict ADDITION. Nothing the incumbent decided has moved.

---

## 2 — A2: IS INTERPOLATION REFUSABLE? (P2 — THE HEADLINE, NOT FORCED)

Identical banks; the gap frames differ only in where the occluder is.

| | `vabduced` | `voffset` | `vcorrection` | `verified` | `violations` | `covered/predicted` |
|---|---|---|---|---|---|---|
| **COVERED** | True | (0, 8) | 0 | **True** | **0** | 32/32 |
| **EXPOSED** | True | (0, 8) | 0 | **False** | **32** | 0/32 |

**P2 CONFIRMED. `A2_refusable = True`, `A2_abduction_unmoved = True`.**

**§1 clause 5 (the vacuity gate), measured rather than asserted:**
`D = max|on − off|` is **32.0** on `vviolations`, **32.0** on `vcovered`, and
**1.0** on `verified` — while every abduction field is byte-identical. **The
mechanism moves something downstream, and it moves ONLY what it claims to.**

That conjunction is what makes this a result rather than a separation: a
mechanism that separated these two stimuli by moving the *abduction* would be
some other quantity in disguise. **Here the abduction is provably frozen and
only the verification moves.**

**Where the incumbent stands, stated honestly:** `GapAbduce` cannot consume
this stimulus at all — it splits on an EMPTY run and an occupied gap has none
(prereg §9.2, corrected before the run). On the BLANK-gap encoding of the same
passage — its native input — it ACCEPTS with `correction = 0`. **The incumbent
accepts a passage whose intermediates are unverifiable, because it has no notion
of an occupied gap.**

---

## 3 — A3: THE TUNNEL CLIFF (P3) — A NUMBER THAT FELL OUT, PREDICTED EXACTLY

Fixed full passage (`ENTER = 64` → `EXIT = 88`, `D = BW + DOT = 24`), gap length
varying over `k = 0..11`. The arithmetic admits every `k` whose `steps` divides
24; the GEOMETRY admits only those where the object moves at least its own width
per step.

```
  k= 0 steps= 1 off=(0,24) abduced=True  verified=True   viol=  0/0    ok
  k= 1 steps= 2 off=(0,12) abduced=True  verified=True   viol=  0/16   ok
  k= 2 steps= 3 off= (0,8) abduced=True  verified=True   viol=  0/32   ok
  k= 3 steps= 4 off= (0,6) abduced=True  verified=True   viol=  0/48   ok
  k= 4 steps= 5 off=    () abduced=False verified=False  viol=  0/0    indivisible
  k= 5 steps= 6 off= (0,4) abduced=True  verified=True   viol=  0/80   ok
  k= 6 steps= 7 off=    () abduced=False verified=False  viol=  0/0    indivisible
  k= 7 steps= 8 off= (0,3) abduced=True  verified=FALSE  viol=  8/112  unverified
  k= 8 steps= 9 off=    () abduced=False verified=False  viol=  0/0    indivisible
  k= 9 steps=10 off=    () abduced=False verified=False  viol=  0/0    indivisible
  k=10 steps=11 off=    () abduced=False verified=False  viol=  0/0    indivisible
  k=11 steps=12 off= (0,2) abduced=True  verified=FALSE  viol= 16/176  unverified
```

| | admits |
|---|---|
| ABDUCTION (divisibility alone) | `k = (0, 1, 2, 3, 5, 7, 11)` |
| **VERIFICATION** | **`k = (0, 1, 2, 3, 5)`** — registered `(0,1,2,3,5)` |
| **they disagree at** | **`k = (7, 11)`** — registered `(7,11)` |

**P3 CONFIRMED and P3's paired form CONFIRMED, both by SET EQUALITY against a
prediction written into the pre-registration's addendum before the run.**

**§13 — THE CUTOFF FELL OUT.** `k_max = D/DOT − 1 = BW/DOT = 5` is the duration
an object of width `DOT` can be hidden by a bar of width `BW` while moving fast
enough to have vanished at all. It is **not tuned and not fitted**: it was
derived from the geometry, written down as an exact integer, and the measurement
landed on it. `k = 7` (`v = 3`) fails by **8 cells** and `k = 11` (`v = 2`) by
**16** — the object's own overhang past the bar's two edges, `2 × DOT × (DOT − v)`
at both ends. **A cliff anywhere else would have falsified my model of my own
mechanism; there was nowhere to slide it to.**

### THE REGISTERED ISI DISCRIMINATOR: **AMBIGUOUS (tie)**

`R(k) = 1` at `k ∈ {0,1,2,3,5}`, `0` elsewhere.

| branch | condition | outcome |
|---|---|---|
| INTERIOR OPTIMUM | `k* != 0` AND `R(k*) > R(0)` strictly | ❌ |
| FALSIFIES | `R(0) >= R(k)` for every k | ✅ (holds) |
| **AMBIGUOUS** | `R(0)` max but **TIED** with some `k >= 1` | ✅ **`ties = [1,2,3,5]`** |

**`k* = 0`. The reported verdict is AMBIGUOUS (tie), not FALSIFIED** — the
plateau case, spelled out in the pre-registration precisely so it could not be
reinterpreted afterwards.

**THE INHERITED TRAP, AND IT WOULD HAVE CAUGHT ME TOO.** The predecessor's curve
was a jagged divisor comb and it recorded that a rung asking only *"is it
monotone?"* would have scored non-monotonicity as CONFIRMING an interior optimum
and published the opposite of the truth. **My curve is non-monotone as well**
(`R(4) = 0 < R(5) = 1`) — and for a completely different reason (a divisibility
hole at `steps = 5`, not a coverage failure). **The maximum's LOCATION is the
discriminator; the jaggedness is arithmetic, twice over now.**

### §13.1 — THE INTERIOR BRANCH WAS UNREACHABLE, AND THAT REFUTES THE LEVER

Declared in the pre-registration **before the mechanism was built**:

1. **Verification is a MONOTONE FILTER.** It can only REMOVE acceptances:
   `R_verified(k) <= R_abduce(k)` for every `k`, by construction. Measured:
   `{0,1,2,3,5} ⊂ {0,1,2,3,5,7,11}`, a strict subset with nothing added.
2. **`R(0) = 1` is DOUBLY FORCED** — every integer divides by 1, AND at `gap = 0`
   there are ZERO intermediates so the check is vacuous. Measured: `predicted 0`,
   `ticks 0` at `k = 0`.
3. An interior optimum requires `R` to RISE above `R(0)`. **A filter cannot raise
   anything.**

> **So the predecessor's "the first mechanism here whose ISI curve COULD have an
> interior optimum, since a longer gap means MORE PREDICTIONS TO VIOLATE" is
> WRONG — and it is wrong DERIVABLY, before any measurement.** More predictions
> to violate LOWERS the curve at large `k`. It cannot raise it at small `k`.
> **This arm therefore carries ZERO evidential weight and is reported only as a
> derivation confirmed.**

**And the predecessor's intuition is RIGHT about a different quantity, which is
the useful half of the correction.** "More predictions to violate" is a claim
about DISCRIMINATION, and discrimination is exactly what grows with the gap
(§4). **The curve and the discrimination were never the same number, and only
one of them was ever going to move.**

**THE ISI CURVE IS STILL UNEXPLAINED, AND IT HAS NOW SURVIVED A FIFTH
MECHANISM.** Five mechanisms, one shape: maximal at ISI = 0. This one is the
first whose maximum at zero is *provable in advance* rather than measured.

---

## 4 — A4: THE NOISE ARM — THE DISCRIMINATION RATE (P5, THE DEEPEST ARM)

n = 100 per `k`, seeds **105000–105799**, endpoints drawn independently, the
FIXED scene present in every gap frame. **The analytic expectations were
computed by exhaustive enumeration over the sampling grid, inside the runner,
and printed BEFORE any arm was read.**

| k | steps | abduced | analytic | \|z\| | **verified** | **analytic** | \|z\| | **P(ver \| abd)** |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 69/100 | 72.1 | 0.70 | **69/100** | 72.1 | 0.70 | **1.000** *(forced — no intermediates)* |
| 1 | 2 | 37/100 | 35.8 | 0.25 | **8/100** | 8.1 | 0.03 | **0.216** |
| 2 | 3 | 25/100 | 23.7 | 0.31 | **0/100** | 0.3 | 0.52 | **0.000** |
| 3 | 4 | 16/100 | 17.6 | 0.43 | **0/100** | 0.0 | 0.20 | **0.000** |
| 4 | 5 | 13/100 | 14.0 | 0.29 | **0/100** | 0.0 | 0.14 | **0.000** |
| 5 | 6 | 15/100 | 11.6 | 1.07 | **0/100** | 0.0 | 0.10 | **0.000** |
| 6 | 7 | 6/100 | 9.8 | 1.29 | **0/100** | 0.0 | 0.00 | **0.000** |
| 7 | 8 | 9/100 | 8.6 | 0.16 | **0/100** | 0.0 | 0.00 | **0.000** |

**Every one of the 16 cells is within 1.29 SE of its analytic expectation.**

### THE RESULT

**THE CHECK SUPPLIES THE DISCRIMINATIVE POWER THE ABDUCTION LACKED.**

| | constraint | noise acceptance |
|---|---|---|
| `TimeInfer`, N ≥ 3 (**continuation**) | a THIRD frame must lie on the orbit | 0/100 |
| `GapAbduce` (**interpolation**) | divisibility, and nothing else | **~1/steps** (43/37/22/19% at k=1..4) |
| **`GapVerify`** (**verified interpolation**) | divisibility **AND every intermediate accounted** | **8, 0, 0, 0, 0, 0, 0 at k=1..7** |

**`P(verified | abduced)` DECREASES WITH THE GAP exactly as predicted** —
1.000 → 0.216 → 0.000, and it is at the floor from `k = 2` onward. A longer gap
means more intermediates, and each one is another chance for the scene to refuse
the story. **The predecessor's "two endpoints and one free generator always fit"
is now false as soon as there is anything else in the scene to fit AGAINST.**

**A REFUSAL IS A FAILURE AFTER A FULL CHECK, NOT A REFUSAL AT A GUARD.**
`A4_full_search = True`: every one of the 113 `unverified` verdicts across the
arm checked **every** gap tick (`ticks == gap`) and compared a **non-zero**
number of cells. A refusal that had predicted nothing would have been a guard
wearing a measurement's clothes, and would have been reported as a §13 negative.

**The refusal breakdown is reported per `k`** (`ok` / `unverified` /
`indivisible` / `not_rigid` / `identity`), so no null here is a shrug. At
`k = 2`, for instance: 25 `unverified`, 41 `indivisible`, 33 `not_rigid`,
1 `identity` — **the 25 that the incumbent would have ACCEPTED are exactly the
ones verification killed.**

### THE REGISTERED FORMULA WAS INCOMPLETE, AND THE GAP IS REPORTED (prereg §9.3)

The formula registered in §4 omitted a condition the mechanism genuinely
applies: a drawn endpoint whose dot overlaps the bar OCCLUDES it, so the bar's
own cell count differs between banks and per-surface rigidity refuses. **I did
not restrict the draw range post hoc** — that is forking paths — so all three
columns are reported:

| k | registered analytic | exact analytic (+rigidity) | measured |
|---|---|---|---|
| 0 | 0.9936 | 0.7214 | 0.690 |
| 1 | 0.4936 | 0.3580 | 0.370 |
| 2 | 0.3269 | 0.2369 | 0.250 |
| 3 | 0.2436 | 0.1763 | 0.160 |
| 4 | 0.1936 | 0.1400 | 0.130 |
| 5 | 0.1603 | 0.1157 | 0.150 |
| 6 | 0.1365 | 0.0985 | 0.060 |
| 7 | 0.1187 | 0.0856 | 0.090 |

**The registered formula overstates by 27–38% relative, uniformly. The
measurement tracks the EXACT formula.** That is the honest reading: my
registered model of my own stimulus was wrong in a way the mechanism was not,
and the discrepancy is a reported quantity rather than something explained
afterwards.

---

## 5 — A5: BLANK-GAP STRICTNESS (P6, FORCED) — **AND MY VERDICT OVER-REACHED**

**`A5_blank_forced = False`, and the failure is MY VERDICT FUNCTION, not the
mechanism.** It is reported as it stands.

| k | abduced | verified | violations/predicted | reason |
|---|---|---|---|---|
| 1 | True | False | **16/16** | unverified |
| 2 | True | False | **32/32** | unverified |
| 3 | True | False | **48/48** | unverified |
| **4** | **False** | False | **0/0** | **indivisible** |
| 5 | True | False | **80/80** | unverified |
| **6** | **False** | False | **0/0** | **indivisible** |
| 7 | True | False | **112/112** | unverified |

`v_a5_blank_forced` asserted `violations == predicted != 0` over **every** `k`.
At `k = 4` and `k = 6` the passage displacement 24 is not divisible by 5 or 7,
so **there is no abduction and therefore no intermediates to violate** — a
condition that has nothing to do with the proposition being tested.

**The registered proposition holds 5/5 in every cell where an interpolation
exists** and is silent in the two where none does. The as-registered `False`
is left standing because deleting it would hide the design error (the timephi
rung's precedent, applied to myself).

**And this arm was FORCED and declared so in advance**: with nothing observed in
the gap, every prediction is unaccounted and the verdict could not have been
anything else. It is run only to confirm the source reading against the REAL
ENGINE — the thing a doc comment failed at four times this week.

**IT IS ALSO A SCOPE STATEMENT, REGISTERED IN ADVANCE SO IT COULD NOT LATER BE
SOLD AS A FEATURE: under strict accountability the substrate is MORE REFUSING
THAN A HUMAN on classic phi.** A human sees motion across a blank ISI. This
mechanism refuses it, because a blank frame is an OBSERVATION that the figure
was not there. **Whatever human phi is doing, it is not strict accountability.**

---

## 6 — §13: NO NUMBER ENTERED THE MECHANISM, AND NONE WAS NEEDED

**§13 is satisfied BY CONSTRUCTION.** The coverage test is exact integer
coordinate equality; the verdict is `violations == 0`, an equality against the
sentinel `0`. **There is no tolerance in it and nowhere to put one** — the same
strongest-§13 outcome the predecessor reached: not a number that falls out, but
**no number at all**.

**THE BRIEF'S CLAUSE, ANSWERED: I did not need a tolerance at any point, so
there is nothing to report under "if checking intermediates forces one on you,
that is a finding".** The pre-registration said why in advance, and the reason
held: predicted cells and observed cells are both integer coordinate tuples **in
the same frame**, and the frame/continuum invariant says an in-frame comparison
MUST be integer. A "close enough" radius would have been a CROSS-frame quantity
smuggled in-frame — and it never became tempting, because the mechanism never
compares across frames at all. **`k_max = BW/DOT` is the one number this rung
produced, and it FELL OUT** (§3).

`tests/test_gapverify_ast_migrated.py` — **10 passed.** A Python AST walk, never
a substring selector. It carries the predecessor's earned machinery forward
rather than re-inventing it: verdicts bound as `ast.FunctionDef` by name **from
the runner's OWN `VERDICTS` tuple** (non-vacuity); **subscript indices PRUNED by
explicit descent** because `ast.walk` CANNOT PRUNE; **module-level name bindings
RESOLVED TO THEIR LITERALS**; **no ORDERING against a non-zero literal, inline
or named**, with orderings admitted only between two MEASURED quantities or
against `0`; swept axes iterated, never compared against; dead-instrument arms
ABORT (`return 2` / `return 3`).

**POSITIVE-CONTROLLED FOUR WAYS, and the new clause VACUITY-GATED against
itself:**

| injection | result |
|---|---|
| inline `len(violations) < 3` | **RED** — `ordering-threshold:v_a0_coord:3.0` |
| **named** `CHECK_TOL = 3` … `< CHECK_TOL` | **RED** — same finding, one indirection away |
| axis `len(violations) > max(K_GRID)` | **RED** — `axis-compared:v_a0_coord:K_GRID` |
| unmodified source | **GREEN**, asserted in the same test |
| **named injection, resolver BLINDED** | **scans to `[]`** — the clause is LOAD-BEARING, not decorative |

**WHY `CLIFF_VERIFIED` AND `CLIFF_DISAGREE` ARE NOT THRESHOLDS**, asserted
structurally by the gate rather than argued: they are compared by **SET
EQUALITY** against predictions written into the pre-registration before the run.
A set equality has no sensitivity to slide, and changing a member asserts a
different proposition rather than a weaker one. **That is §3 clause 7 (state
your prediction in advance), not §13 (do not tune a constant against the
answer).** `test_the_registered_predictions_are_SET_EQUALITIES_not_orderings`
walks both verdicts and fails if either decides by an ordering.

**Declared residuals, labelled CONFIGURATION and nothing stronger:** `DOT = 4`,
`FIELD_H/W`, `BG`, `FG`, `ROW` (inherited unchanged from the phi/timephi/
gapabduce rungs); **this rung's own `OCC = 128`, `B0 = 68`, `BW = 20`** —
stimulus construction; **`max_b = 8`**, a compute cap on the linear enumeration,
inherited unchanged. **The claim made about all of these is the weak one — bound
once, never a verdict threshold — not that they fell out.** `BW` in particular
is configuration; what fell out is the **RATIO** `BW/DOT`, which is what the
cliff is a function of.

---

## 7 — §9: DEFAULTS PRESERVE COMMITTED RESULTS

- The Rust is **ADDITIVE**: one new `TermNode` variant appended at the **END** of
  the enum (index **176**), so **`GapAbduce`'s 175 and every prior index are
  UNMOVED**. `NUM_TERM_VARIANTS` 176 → 177. No existing Term, evaluator, or seed
  is touched.
- `seeds/gap_verify.json` is **flag-gated on `gap_verify_enabled`, absent by
  default**, and additionally matches only `status == "gap_vseq"`.
- **Oracle 222/0 before AND after. `cargo test --lib` 622/0 including
  `variant_table_covers_the_enum`.**
- **The §9 gate is PAIRED, and that is not decoration — see §11.3.**

---

## 8 — WHAT IS NOT SHOWN (§8)

- **Nothing about human phi's mechanism.** No human data was measured. Indeed
  §5 shows this mechanism refuses classic phi, which a human does not.
- **EVERY POSITIVE RESULT IS CONDITIONAL ON A SUPPLIED FIGURE/GROUND SPLIT.**
  The timephi A1 bound is inherited UNCHANGED: the Term reuses
  `infer_translate_offset` and **cannot consume a bounded pixel field at all.**
  The segmentation is the adapter's, not the graph's. I did not attempt to fix
  ingestion.
- **OCCLUSION ORDER IS NOT INFERRED**, and this is the sharpest limit. The
  mechanism asks only whether SOMETHING was observed where the figure was
  predicted. **A figure predicted IN FRONT of an occluder would be wrongly
  accounted** — strict accountability is depth-blind, and it was declared so in
  advance rather than discovered.
- **The scene is what makes the check work, and a scene derived from the
  endpoints would not.** Measured incidentally while designing the arms: an
  occluder derived from the two sightings covers the abduced path by
  construction and discriminates almost nothing. **The constraint must be
  INDEPENDENT of the data being constrained.** *(Stated as a design finding, not
  as a measured arm — it was computed analytically and the arm was not run.)*
- **Multiple simultaneous motions are REFUSED, not handled** (`multi_motion`).
  That is `DepthInfer`'s question and this rung does not touch it.
- **One dot, one bar, one shape, one size, horizontal only, uniform background.**
  A textured background was **NOT** run. The figure split remains the
  load-bearing untested assumption of this rung and its three predecessors.
- **The linear class was searched only within `max_b = 8`.**
- **`R(k)` for A3 is a single stimulus family**, not a marginal over a grid; the
  full 12-row table is reported so it can be recomputed.
- **No timing claim of any kind.** Every quantity is exact or counted.

---

## 9 — WHAT I GOT WRONG

1. **MY PRE-REGISTRATION CONTAINED THREE DESIGN ERRORS, AND I FOUND THEM ONLY BY
   IMPLEMENTING THE STIMULUS** (addendum `1f4ca5a7`, committed before any
   number). (a) P3's "tunnel" was not a passage — with the speed fixed and the
   exit growing with `k`, the `k = 0` dot lands INSIDE the bar and refuses
   `not_rigid`, for a reason with nothing to do with the hypothesis. (b) P2's
   "`GapAbduce` returns the identical verdict on both" is **not well-posed** —
   the incumbent splits on an EMPTY run and cannot consume an occupied gap at
   all. (c) P5's analytic formula **omitted the rigidity condition** and
   overstates by 27–38% relative. **§3 protects the statistics; it does not
   protect the design** (§6, and it caught me three times in one document).
2. **MY A5 VERDICT OVER-REACHED AND RETURNS `False`.** It asserted
   `predicted != 0` at every `k`, including the two where the abduction itself
   refuses `indivisible` and therefore emits no intermediates. The registered
   proposition holds 5/5 where an interpolation exists. **Left standing, not
   edited** (§5 forbids rescuing a failure by changing the measure; the timephi
   rung's precedent is to report both readings).
3. **MY §9 GATE COULD HAVE PASSED VACUOUSLY, AND THE ACCIDENT THAT REVEALED IT
   WAS A SECOND ERROR.** I ran the positive control for the flag-off gate in a
   bare `python3 -` with `sys.path.insert(0, '.')` and **no `engine_preamble()`**
   — which resolved the CANONICAL engine via the `.pth` (§10 rule 1b's exact
   documented trap, "a green gate in a different process is not provenance").
   That engine does not know `GapVerify`, so the seed loader printed
   **`WARNING: skipping malformed rule 'gap_verify_intermediates': bad computed
   effect arg: UnknownTermType("GapVerify")`** and the rule never installed.
   **The flag-OFF assertions passed IDENTICALLY under a rule that could not run
   at all** — §1 clause 4 ("scores at the floor is satisfied by death") in
   seed-loader form. The gate is now **PAIRED**: flag ON must fire
   (`status = gap_verified`, `verified = 1.0`) or the OFF arm proves nothing.
   **I made a provenance error and it bought me a real vacuity find; I would not
   have looked otherwise.**
4. **I ASSUMED THE ENUM'S ARITY LIVED ONLY IN THE ENUM.** `NUM_TERM_VARIANTS`
   is a separate constant, and the build broke until I bumped it. **Caught by
   the compiler, not by me** — the only one of these four that a machine was
   guaranteed to find.
5. **I ADDED `--release` TO THE RUST TEST COMMAND AND MISREAD THE RESULT.**
   `cargo test --lib` fails to link (`undefined symbol: PyGILState_Release`) —
   and it does so **in the CANONICAL tree too, with none of my changes** (42
   warnings there vs 43 here), so it is a pre-existing tree-wide condition, not
   my diff. It runs with `RUSTFLAGS="-L native=/usr/lib -l dylib=python3.14"`,
   giving 622/0. **I verified the attribution against the other tree rather than
   assuming it** (§12.3: verify the fact, then fix the gate) — but my first
   instinct was to assume my own change had broken it.

---

## 10 — NAMED NEXT LEVERS, EACH NEEDING ITS OWN PRE-REGISTRATION

1. **OCCLUSION ORDER — the lever this rung earns.** Strict accountability is
   depth-blind: it cannot distinguish "hidden behind" from "should have been in
   front". The substrate already has `DepthInfer`, which reads depth off
   VELOCITY VARIATION across surfaces. **A verified interpolation whose figure
   is accounted by a surface the depth ordering puts BEHIND it should be
   REFUSED** — and that is a falsifiable prediction the current mechanism
   accepts. This is the next real constraint.
2. **A TEXTURED BACKGROUND, still unrun after four rungs.** The figure/ground
   split is the load-bearing assumption of this entire line and remains
   untested against texture. It is now more urgent, not less: verification reads
   the OBSERVED gap frame, so texture enters the coverage test directly — and a
   textured field would account for **every** prediction, making verification
   vacuous. **I expect that to be the failure mode, and it should be measured
   rather than predicted.**
3. **THE ISI CURVE IS UNEXPLAINED AFTER FIVE MECHANISMS.** Maximal at ISI = 0
   every time. This rung shows it is not fixable by adding constraints — a
   filter cannot move a maximum that sits at a vacuous point. **Whatever
   produces the human curve is not a constraint on interpolation; it is
   something that makes ISI = 0 WORSE**, and no mechanism in this tree does
   that. That is now a sharp, positive specification for the next attempt.
4. **The stale `BlinkBridge` doc comment in `term.rs`** — reported by two
   predecessors, **still unedited** (not this rung's file). A comment-vs-engine
   gate remains worth building; this rung adds no new instance.
5. **`cargo test --lib` does not link in either tree.** Reported, not fixed
   (`Cargo.toml` is not this rung's file). Every rung adding Rust hits it.

---

## 11 — LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **105000–105999 (800 seeds resolved 105000–105799, unknown_sinks 0, parse_errors 0, none outside block)** | **CHECKING THE ABDUCED INTERMEDIATES MAKES INTERPOLATION REFUSABLE — AND SPLITS THE PREDECESSOR'S NAMED LEVER IN TWO, RIGHT ABOUT DISCRIMINATION AND WRONG ABOUT THE CURVE, DERIVABLY.** New Rust Term **`GapVerify`** (ADDITIVE, appended at enum index 176 so `GapAbduce`'s 175 and every prior index are UNMOVED; `NUM_TERM_VARIANTS` 176→177; seed flag-gated OFF by default): where `GapAbduce` emits its intermediates and CHECKS THEM AGAINST NOTHING, this one requires the gap frames to be OBSERVED and makes `G^t(f_before)` a FALSIFIABLE PREDICTION at every tick — **STRICT ACCOUNTABILITY: every predicted cell must coincide with an observed cell, exact integer coordinates, `violations == 0`.** **P2 THE HEADLINE, NOT FORCED: two stimuli with BYTE-IDENTICAL BANKS differing ONLY in gap content separate (`verified` True vs False, `violations` 0 vs 32) WHILE EVERY ABDUCTION FIELD IS PROVABLY IDENTICAL (`offset (0,8)`, `closes`, `correction 0`) — 1's fifth clause measured, `D = 32.0` on violations and 1.0 on verified, moving ONLY what it claims to.** **P5 THE DEEPEST ARM — THE CHECK SUPPLIES THE DISCRIMINATIVE POWER THE ABDUCTION LACKED: `P(verified|abduced)` collapses 1.000 → 0.216 → 0.000 across k=0,1,2 and stays at the floor to k=7, against `GapAbduce`'s ~1/steps; EVERY ONE OF 16 NOISE CELLS WITHIN 1.29 SE of an analytic expectation computed by EXHAUSTIVE ENUMERATION BEFORE THE ARM WAS READ. Every one of 113 `unverified` verdicts is a FAILURE AFTER A FULL CHECK (`ticks == gap`, `predicted != 0`), never a guard.** **P3 THE TUNNEL CLIFF LANDED ON THE EXACT PREDICTED INTEGER: verification admits k ∈ {0,1,2,3,5}, the abduction alone admits {0,1,2,3,5,7,11}, they part company at EXACTLY {7,11} — both registered as SET EQUALITIES before the run; `k_max = BW/DOT = 5` FALLS OUT of the geometry (k=7 fails by 8 cells, k=11 by 16 — the object's own overhang).** **THE REGISTERED ISI DISCRIMINATOR RETURNS `AMBIGUOUS (tie)`: k*=0, tied with k=1,2,3,5 — and 13.1 DECLARED THE INTERIOR BRANCH UNREACHABLE A PRIORI: verification is a MONOTONE FILTER (measured: the verified set is a STRICT SUBSET with nothing added) and R(0)=1 is DOUBLY FORCED (divisible by 1; ZERO intermediates at gap 0), so a filter cannot raise anything. THE PREDECESSOR'S "the first mechanism whose ISI curve COULD have an interior optimum" IS REFUTED WITHOUT MEASUREMENT — its intuition was about DISCRIMINATION, which DID grow with the gap. FIFTH mechanism, same shape: maximal at ISI=0. The curve is not fixable by adding constraints; whatever makes the human curve must make ISI=0 WORSE, which nothing here does.** **P1: the surface-set split REDUCES to the incumbent's empty-run split, 72/72 abduction fields identical — verification is a strict ADDITION.** **13 SATISFIED BY CONSTRUCTION AND NO TOLERANCE WAS NEEDED (the brief's clause answered): coverage is exact integer coordinate equality IN-FRAME, so a "close enough" radius would be a CROSS-frame quantity smuggled in-frame; AST gate 10/10, POSITIVE-CONTROLLED FOUR WAYS with the name-resolver BLINDED scan proving the clause LOAD-BEARING, and the registered predictions asserted structurally to be SET EQUALITIES not orderings.** **SCOPE, DECLARED IN ADVANCE NOT DISCOVERED: strict accountability is DEPTH-BLIND (a figure predicted IN FRONT of an occluder is wrongly accounted), and on a BLANK gap it REFUSES classic phi — MORE REFUSING THAN A HUMAN. A constraint derived from the endpoints discriminates nothing; it must be INDEPENDENT of the data it constrains.** **WHAT IT GOT WRONG: (1) THE PRE-REGISTRATION CONTAINED THREE DESIGN ERRORS found only by implementing the stimulus (tunnel not a passage; the incumbent comparison not well-posed; the analytic formula omitted rigidity and overstates 27–38% relative — all three corrected in an addendum committed BEFORE any number, and all three columns reported rather than the range restricted post hoc); (2) MY A5 VERDICT OVER-REACHED AND RETURNS False — it asserted `predicted != 0` at k where the abduction itself refuses `indivisible` and emits no intermediates; the proposition holds 5/5 where an interpolation exists, and the as-registered False IS LEFT STANDING; (3) **MY 9 GATE COULD HAVE PASSED VACUOUSLY** — its positive control was run in a bare `python3 -` with no `engine_preamble()`, resolved the CANONICAL engine via the `.pth` (10 rule 1b's exact trap), which does not know the Term, so the loader SKIPPED the rule (`UnknownTermType`) and the flag-OFF assertions PASSED IDENTICALLY UNDER A RULE THAT COULD NOT RUN — 1 clause 4 in seed-loader form; the gate is now PAIRED (ON must fire or OFF proves nothing); (4) I assumed the enum's arity lived only in the enum (`NUM_TERM_VARIANTS`, caught by the compiler); (5) `cargo test --lib` FAILS TO LINK (`undefined symbol: PyGILState_Release`) — verified PRE-EXISTING IN THE CANONICAL TREE with none of my changes, runs 622/0 with an explicit libpython link flag.** Oracle **222/0 with `data/` before AND after**; `cargo test --lib --test-threads=1` **622/0** incl. `variant_table_covers_the_enum`; AST gate 10, mechanism gate 8, instrument-seams 22; provenance gate its OWN step (7 passed, before and after) AND re-verified from inside the measuring process with abort-on-divergence; engine `d657468d9e1f` **`own` — THIS RUNG ADDS RUST.** |
