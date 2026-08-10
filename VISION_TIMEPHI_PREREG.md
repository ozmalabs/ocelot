# DOES `TimeInfer` ON ≥3 FRAMES RECOVER THE CORRESPONDENCE TWO FRAMES CANNOT? — PRE-REGISTRATION

*Written and committed BEFORE any number. Successor to `VISION_PHI_RESULTS.md`
(ledger 86000–86999), which named this lever and registered its reason in
advance.*

**Branch** `worktree-agent-aa916e5bf789dffcd` — the name I actually see.
**Base SHA** `ee0a1af25ef5dea0e9bc8919f85ebe7e8e19f463`.
**Engine** `a1d350bbd23b` (`own` build, `scripts/engine_build.sh`), **no Rust
change planned**. Provenance gate as its **own step before any number**:
`tests/test_engine_provenance_migrated.py` **7 passed**.
**Oracle** `scripts/rung7_vision_bench.sh` **212 passed / 10 skipped / exit 0** —
this tree has no `data/`, the documented no-corpus case (§10.2).

**Seed block 93000–93999.** `check_claim(93000, 93999)`:

```
SEED CLAIM 93000-93999: CLEAN -- no collision DETECTED.
  Scope: 798 files with seed sinks; 482 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0 — WHAT `TimeInfer` ACTUALLY IS, READ FROM SOURCE BEFORE PREDICTING ANYTHING

*The project's own recorded lesson from the identity seam is "it was never broken
— nobody had handed it pixels." §12.1's lesson is that a claim about what code
does is not established by counting tokens. So this section is read off
`runners/dsl/src/shape_decode.rs::eval_time_infer` and `::eval_blink_bridge`,
line by line, before a single prediction is written.*

`TimeInfer(sequence, codebook_type, max_b, field)`:

1. `coord_dims` come from the **first `codebook_type` part that declares
   `dim_types`** — the slots tagged `coord:`. **If no part declares them,
   `coord_dims` is EMPTY and the Term returns `unexplained(0)` at EVERY
   condition.** *This is the exact shape of the phi rung's `has_region` fake
   null. It is trap #1 and the wiring control below exists for it.*
2. The sequence is a list of **frames**; each frame is a list of **relation
   tuples** (signature cells) — **not a pixel array.**
3. **Guard: `if frames.len() < 2 || coord_dims.is_empty() || frames.iter().any(|f| f.is_empty()) { return unexplained(0) }`.**
   **A sequence containing ANY empty frame is REFUSED, before any inference.**
4. `G` is inferred from the FIRST pair only: `infer_translate_offset(f0, f1)`
   preferred, else an integer 2×2 linear enumerate-and-test bounded by
   `min(data_extent, max_b)`. **Identity is excluded** (a still sequence is not
   a motion).
5. `infer_translate_offset` requires **`f0.len() == f1.len()`**, sorts both
   frames, and demands **every** paired cell differ by the **same** offset in
   the coord slots and be **byte-identical** in every non-coord slot.
6. `G` is then **VERIFIED by exact equality across every remaining consecutive
   pair** (`frames_equal`, a multiset comparison). No residual slack.

**Three consequences follow from the source, and they are stated here as
predictions, not assumptions:**

- **The translate path has NO APERTURE.** The offset is read off the data by
  subtraction; nothing bounds its magnitude. `max_b` bounds only the *linear*
  fallback's enumeration. **So `TimeInfer` is the first correspondence
  mechanism in this arc whose limit is not a pixel length** — which is exactly
  why the phi rung named it.
- **On TWO frames it is a tautology** for any rigid figure: two equal-cardinality
  cell sets related by a uniform shift always admit that shift as `G`, and there
  is no second pair to falsify it. **This is the vacuity claim, and §3 requires
  it be MEASURED rather than assumed — arm A2.**
- **On a sequence containing an empty frame it REFUSES.** Not "fails to find" —
  refuses, at guard 3, with `checked == 0`. **Refusal and failure are
  distinguishable in the output, and that distinction is the point of arm A5.**

`BlinkBridge(sequence, ...)` — the mechanism built for gaps:

7. It splits `[prefix(visible) | gap(EMPTY) | resumed(visible)]` structurally.
8. **`if prefix_len >= 2 && !coord_dims.is_empty()`** — a generator is inferred
   and verified across the prefix, `confirm_run` counts confirming transitions.
   **With `prefix_len == 1` this block is SKIPPED ENTIRELY**: `explained=false`,
   `kind="freeze"`, and the belief across the gap is the **last frame repeated**.
9. "CONFABULATE BY DEFAULT" — it always emits a `bridged` belief; when
   unconstrained that belief is the **freeze** (persistence).
10. `confidence = support / (support + gap)`, `support = confirm_run if explained
    else 0`.

**So the substrate DOES ship a gap-crossing mechanism.** Whether it crosses
*this* gap depends on `prefix_len`, and **phi supplies `prefix_len == 1`.** That
observation is what makes the null-reading in §5 decidable rather than a shrug.

---

## 1 — HYPOTHESIS, TWO-SIDED

**H1.** `TimeInfer` at N ≥ 3 frames recovers a correspondence that is **not
bounded by a pixel aperture** — i.e. it returns `explained` at separations `S`
far beyond the 4/6/`radius` apertures at which all three phi-rung mechanisms
stopped exactly.

**H2 (the phi question proper).** That recovered correspondence **crosses a
temporal gap** — i.e. it survives ISI ≥ 1, the regime in which human phi is
*strongest* and in which all 30 phi-rung conditions were *identically dead*.

**H1 and H2 are independent and are scored separately.** The phi rung's finding
was an *inverted* ISI dependence; H2 asks whether the one aperture-free
mechanism inverts it too.

**Two-sided, explicitly.** H1 could fail (the figure representation might not
reach the Term at all — arm A0/R-FIELD). H2 could *succeed* (arm A6a is a real
possible surprise: if a single pre-gap sample bridges, the substrate does phi and
the phi rung's negative is aperture-specific rather than architectural).

---

## 2 — THE STIMULUS, AND THE REPRESENTATION QUESTION IS ITSELF AN ARM

Inherited from the phi rung so the two are comparable: a **4×4 dot** on a
**uniform field**, displaced **horizontally** by `S` px per flash.

**`TimeInfer` consumes signature cells, not a pixel array.** Any pixel→cell
conversion is a choice, and the project's lesson ("nobody had handed it pixels")
makes that choice a measurement rather than a setup detail. **Both
representations are run and both are reported:**

| arm | representation | supplied structure |
|---|---|---|
| **R-FIELD** | **every** pixel of the frame as `["px", r, c, lum]` | **NONE** — the raw bounded field |
| **R-FIG** | only cells whose `lum != ` the frame's modal luminance | **A FIGURE/GROUND SPLIT, DECLARED** |

**Registered prediction P0: R-FIELD is `unexplained` at every S, structurally**,
because a translate applied to a *bounded* field moves edge cells off the lattice
and `frames_equal` is exact — `infer_translate_offset` will pair the sorted
frames, read offset `(0,0)` from the first background cell, and fail on the dot
cells. **If P0 holds, the honest statement is that `TimeInfer` is a SHAPE-level
operator that cannot consume a bounded pixel field at all**, and every positive
result in this rung is conditional on a figure/ground split the adapter supplied.
**That conditionality is a limitation of the result and will be reported as
one**, not buried.

Fields: `FIELD_H = 24`, `FIELD_W = 160` (wide enough that `S = 32` at `N = 5`
stays on the lattice). R-FIELD uses a `48×48` field (its verdict does not depend
on width, and the raw-field arm is 5–9k cells per frame).

---

## 3 — THE ARMS, THE GRID FIXED IN ADVANCE, AND THE STATISTIC

**Every arm is DETERMINISTIC and every verdict is a LOGICAL EQUALITY. No arm is
stochastic, so no p-value is computed and none will be reported.** "n fixed in
advance" is discharged by the exhaustive condition grid below. **Exactly these
conditions. No sweeps. No re-runs.**

`S_GRID = [1, 2, 4, 6, 8, 12, 16, 20, 32]` — spans the phi rung's three
apertures (L1 `4`, L2 `6`, L3 `radius`) and reaches **8× the largest**.

### A0 — WIRING CONTROL. RUN FIRST, BEFORE ANY HYPOTHESIS ARM.

*§10.2 rule 1 and the phi rung's near-miss: a mechanism whose output is "no
correspondence" is indistinguishable from a mechanism that cannot express
correspondence. Positive-control the WIRING, not the hypothesis.*

- **A0-POS.** R-FIG, N = 3, S = 4, constant velocity. **MUST** return
  `status == 'time_inferred'`, `time_kind == 'translate'`, `offset == (0, 4)`.
- **A0-NEG.** R-FIG, N = 3, **stationary** dot. **MUST** return
  `status == 'time_none'` (identity is excluded at source). This proves the
  reader *discriminates* rather than always saying yes.
- **A0-COORD (the trap #1 gate).** On **every single call** in this rung, the
  raw Term dict's `coord_dims` **must be non-empty**. `coord_dims == ()`
  anywhere ⇒ **ABORT THE RUN AND PUBLISH NOTHING.** This is the phi rung's
  silent-refusal trap in this Term's form.
- **A0-PROV.** `provenance_line()` printed **from inside the measuring
  process** and compared against the gate's engine hash; **divergence ⇒ abort**.

**If A0-POS or A0-NEG fails, no other arm is interpreted.**

### A1 — R-FIELD: can the Term consume a bounded pixel field?

N = 3, S = 4, R-FIELD. **Statistic:** `explained`. **Prediction P0: false.**

### A2 — VACUITY, MEASURED NOT ASSUMED (N = 2)

R-FIG, N = 2, every `S` in `S_GRID`.
**Statistic:** `explained` per S. **Prediction P1: TRUE at every S (9/9).**
**If any S returns false, the group-closure vacuity argument this rung inherited
is FALSE, and that is the finding.**

### A3 — APERTURE-FREENESS AT N ≥ 3 (H1)

R-FIG, N ∈ {3, 5}, constant velocity, every `S` in `S_GRID`.
**Statistic:** the **maximum S with correspondence**, per N.
**Prediction P2: `explained` at every S in both N — no maximum within the tested
range.** The phi rung's three mechanisms stopped at 4, 6 and `radius` exactly;
**P2 predicts no cutoff at all**, and that is H1's whole content.

### A4 — DISCRIMINATION: what makes A3 non-vacuous

R-FIG, N = 3, every `S` in `S_GRID`, two non-orbits:
- **ACCEL** — positions `0, S, 3S` (velocity changes).
- **SHUFFLE** — a constant-velocity orbit presented out of order.

**Statistic:** `explained`. **Prediction P3: FALSE in all 18 conditions.**
**Without A4, A3 is a tautology** (a mechanism that says "explained" to
everything has no aperture in the way a broken clock has no error).

### A5 — THE ISI CURVE (H2) — AND ITS EVIDENTIAL WEIGHT IS DECLARED IN ADVANCE AS ZERO

R-FIG, `N_flash ∈ {2, 3, 5}` flashes at constant spacing, `S ∈ {4, 16}`,
`k ∈ {0, 1, 2, 3, 4}` blank frames between flashes. Blank encoded two ways:
- **BLANK-EMPTY** — the blank frame is the empty cell set.
- **BLANK-BG** — the blank frame carries background cells only (non-empty, but a
  different cardinality from a dot frame).

**Statistic:** `explained` and `checked`, per (N_flash, S, k, encoding).
**Prediction P4: FALSE at every k ≥ 1 in all 60 conditions; TRUE at k = 0 for
N_flash ≥ 2.** The human curve is an interior optimum in ISI; this predicts the
**inverted** curve the phi rung measured, now at the aperture-free mechanism.

> **§13.1 DECLARATION, MADE BEFORE THE RUN: A5 CANNOT PRODUCE A POSITIVE, AND
> THEREFORE CARRIES NO EVIDENTIAL WEIGHT ON ITS OWN.** I read the guard at
> source (§0.3): BLANK-EMPTY is refused by `frames.iter().any(|f| f.is_empty())`
> and BLANK-BG by `infer_translate_offset`'s `f0.len() != f1.len()`. **Both nulls
> are FORCED BY ARCHITECTURE — §13.1's third category, "a mechanism whose
> architecture forces the signature you are measuring."** A5 is run anyway for
> exactly two reasons, both narrow: (a) to confirm the source reading is correct
> on the real engine — *a rung this week found its own seed comment about the
> engine was FALSE on the current engine, so a source reading is a hypothesis
> too*; (b) because `checked == 0` distinguishes **REFUSAL** from **FAILURE**,
> and that distinction is what makes §5's null-reading decidable.
> **The real empirical content of this rung is A6.**

### A6 — THE ARM THAT IS NOT FORCED: `BlinkBridge`, PREFIX LENGTH AS THE IV

*This is the decisive arm. It is not forced by any guard: both outcomes are
reachable, and the mechanism was built for precisely this stimulus.*

Sequence `[P visible frames of a dot translating by S | k EMPTY frames | 1
resumed frame at the correctly-continued position]`.
Grid: `P ∈ {1, 2, 3, 4}`, `k ∈ {1, 2, 3, 4}`, `S ∈ {4, 16}` — **32 conditions.**

- **A6a — `P = 1`, THE PHI TOPOLOGY** (one pre-gap sample, one post-gap sample,
  which is what a phi stimulus *is*).
  **Prediction P5:** `explained == false`, `kind == "freeze"`,
  `confidence == 0.0`, `bridged` = the last frame **repeated**,
  `diverged_at` = the resume tick, `correction == 2 × 16 == 32` (the dot's 16
  cells absent from A **and** present at B).
  **`correction = 32` is the substrate COMPUTING "one vanished, another
  appeared" and giving it a magnitude** — the phi rung's null, quantified.
- **A6b — `P ∈ {2, 3, 4}`, AN ESTABLISHED ORBIT**, same gap, same displacement.
  **Prediction P6:** `explained == true`, `kind == "translate"`,
  `offset == (0, S)`, and for `k <= confirm_run`: `resume_ok == true`,
  `diverged_at == -1`, `correction == 0`.

**P5 and P6 are the two-sided pair.** If A6a bridges, H2 is CONFIRMED and the
substrate does phi. If A6b fails to bridge, `BlinkBridge` is decorative on this
stimulus and that is a §13.2 vacuity finding about a shipped mechanism.

---

## 4 — PREDICTIONS, STATED IN ADVANCE, WITH PROVISOS

| | prediction | proviso that would break it |
|---|---|---|
| **P0** | R-FIELD `explained = false` at every S | a wrapped/toroidal field would make it true; I am not using one |
| **P1** | N = 2 `explained` at **all 9** S — vacuous | fails if `infer_translate_offset`'s non-coord byte-identity check rejects the pixel-derived `lum` slot (it should not: the dot's luminance is constant) |
| **P2** | N ∈ {3,5} `explained` at **all 9** S — **no cutoff** | fails if `max_b` reaches the translate path (it does not, per §0) or if a wide `S` pushes the dot off the lattice (the field is sized against this) |
| **P3** | ACCEL and SHUFFLE `explained = false`, **18/18** | a SHUFFLE that happens to re-order into an orbit — excluded by construction (N = 3 reversal is not a constant-offset orbit) |
| **P4** | ISI: TRUE at k = 0, FALSE at every k ≥ 1, **60 conditions** | **FORCED — see the §13.1 declaration. No evidential weight.** |
| **P5** | A6a (P=1): freeze, `confidence 0.0`, `correction = 32` | if `BlinkBridge` abduced `G` from the gap's endpoints it would bridge — it does not, per §0.8 |
| **P6** | A6b (P≥2): bridges, `correction = 0` for `k <= confirm_run` | `confirm_run = P − 1`, so `P = 2, k = 4` should **not** satisfy `k <= confirm_run`; the seed rule's decay is relative and I predict divergence there, **not** a bridge |

**P6's proviso is deliberately sharp**: it predicts a *boundary inside the arm*,
so A6b cannot pass by the mechanism simply saying yes to everything.

---

## 5 — THE DECISION RULE, AND WHAT A NULL MEANS — DECIDED BEFORE THE RUN

*The brief required this to be settled in advance, because "the substrate cannot
do phi" and "the substrate has no gap-crossing mechanism at all" license very
different next steps.*

**Neither of those is my registered null-reading, and §0 is why.** `BlinkBridge`
exists, crosses gaps by construction, and its behaviour is conditioned on
`prefix_len`. So the reading I register is a third, sharper one:

> **REGISTERED NULL-READING — CONTINUATION, NEVER INTERPOLATION.**
> Every temporal mechanism in this tree (`TimeInfer`, `BlinkBridge`,
> `DepthInfer`) infers its generator `G` from a **consecutive VISIBLE pair** and
> then **extrapolates** it. **A phi stimulus supplies exactly ONE pre-gap
> sample**, so there is no consecutive visible pair from which to infer `G`. The
> generator that would explain phi must be **ABDUCED FROM THE GAP'S TWO
> ENDPOINTS** — solve `G^(k+1)(f_before) = f_after` for `G` — which is
> **INTERPOLATION**. The substrate has no operator of that shape.
> **The deficit is therefore not aperture, not resolution, not gap-crossing, and
> not motion sensing (C-RIGID already ruled that out). It is the absence of an
> ENDPOINT-ABDUCED generator.**

**Which reading applies is decided by A6, mechanically:**

| A6a (P=1) | A6b (P≥2) | reading |
|---|---|---|
| does not bridge | **bridges** | **CONTINUATION-ONLY** — the registered null-reading. Deficit localised to interpolation. Next lever: a Term abducing `G` from `(f_before, f_after, gap)`, which is a well-posed integer problem. |
| does not bridge | does not bridge | **STRONGER**: no gap-crossing at all on this stimulus; `BlinkBridge` is decorative here (§13.2 vacuity), and the next step is to fix the mechanism before proposing a new one. |
| **bridges** | bridges | **H2 CONFIRMED** — the substrate does phi; the phi rung's negative is aperture-specific, not architectural. Retract the architectural reading. |

**And what a null does NOT license, stated now:**
- **Nothing about human phi's mechanism.** Human phi enters only as the
  parameter dependence being compared against. No human data is measured.
- **Nothing about the pixel sensor.** The ~11% per-block sensor error
  (`VISION_MOTION_OBJECTS_RESULTS.md` §0.2) is **inherited and bounds every
  count in this arc** — but **this rung does not consume the block-match sensor
  at all**: `TimeInfer` reads cell signatures the adapter derives from pixels by
  an exact modal-luminance comparison. **So the sensor bound does not propagate
  into A2–A6. It does bound any comparison I draw to the phi rung's numbers, and
  I will mark such comparisons where they occur.** A concurrent rung is gating
  the sensor; I assume nothing about its outcome.
- **Nothing about C1/C2 corpora.** No corpus is touched.
- **One dot, one shape, one size, horizontal only** — the phi rung's scope
  limits are inherited unchanged.
- **A5's null is architectural, not empirical** (declared above).

---

## 6 — §13: NO MAGIC NUMBER ENTERS

**Every verdict in this rung is an EXACT EQUALITY on a logical or integer
quantity** — `status == 'time_inferred'`, `explained is True/False`,
`offset == (0, S)`, `correction == 0`, `diverged_at == -1`, `kind == 'freeze'`.
**No ordering comparison against a tuned constant decides anything.**

**Declared residuals, inherited and labelled as CONFIGURATION, not thresholds:**

| symbol | what it is | status |
|---|---|---|
| `DOT = 4` | the phi rung's dot size (`DOT = BLOCK`) | **inherited residual**, stimulus construction |
| `FIELD_H/W`, `BG`, `FG` | stimulus geometry and luminances | stimulus construction |
| `max_b = 8` | the seed's cap on the **linear fallback's** enumeration | **a compute cap on an enumerative search, not a threshold on a measured quantity** — and the translate path, which decides every arm here, never reads it |
| `S_GRID`, `k`, `P`, `N` | the **independent variables** | iterated, never compared against |

**The AST gate (`tests/test_timephi_ast_migrated.py`) locates verdict sites BY
SHAPE, never by substring** — it resolves the verdict functions as AST
`FunctionDef` nodes by name, walks their bodies with an explicit parent-pruning
visitor (**`ast.walk` cannot prune** — the phi rung's second gate failed on
exactly this), **prunes `ast.Subscript` indices** (the phi rung's first gate
counted array indices as thresholds, 3 of 6 sites), and admits a non-zero
constant **only** against a cardinality (`len(...)`). It asserts: no non-zero
constant is compared against a measured quantity; verdicts decide by equality;
the declared residuals are bound once and never appear in a verdict comparison;
the swept axes are iterated, never compared. **It will be POSITIVE-CONTROLLED
(§12.3)** by injecting a real threshold and asserting the gate goes RED, and
**non-vacuity asserted** — the scan must match the verdict functions *by name*,
so a rename cannot make it pass by scanning nothing.

---

## 7 — SEEDS

Declared **93000–93999**. The stimulus construction is **fully deterministic**;
the only RNG is the **NOISE control** (independent random dot positions, the phi
rung's arm, drawn from **93000–93099**). `scripts/seed_audit.py` will be run on
this rung's own runner and its output pasted verbatim into the results —
**resolved seeds, `unknown_sinks`, and whether any fell outside the block**. *A
`--check` that passes while leaving sinks UNKNOWN has verified nothing.*

---

## 8 — WHAT I EXPECT TO GET WRONG

Registered so the correction is legible rather than retrofitted:

- **P1/P2's non-coord byte-identity clause** is the most likely proviso to
  break: `infer_translate_offset` demands every non-coord slot be
  byte-identical, and my cells carry a `lum` slot derived from pixels. A
  rendered dot with any anti-aliasing would break it. **I render hard-edged, so
  I predict it holds — but this is the clause I expect to be surprised by.**
- **P5's `correction == 32`** assumes the dot is 16 cells in **both** frames and
  that they share no position. At `S = 4` with a 4-wide dot, source and target
  are **adjacent, not overlapping** — so 32 is right. **At `S < 4` they would
  overlap and the count would be smaller; `S ∈ {4, 16}` avoids it by
  construction, and I am recording that I checked rather than assuming it.**
- **A5 may return `checked > 0` somewhere**, which would mean my source reading
  of the guard order is wrong. That is why `checked` is recorded per condition
  and not merely `explained`.
