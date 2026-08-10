# AN APPEARANCE-TOLERANT PAIRING FOR `TimeInfer` — PRE-REGISTRATION

**Written and committed BEFORE any number, before any Rust, and before the
runner exists.** Successor to the pixel-seam rung (104000–104999), which
isolated the deficit to R6 alone.

- **branch (as observed):** `worktree-agent-a69514c5ba054289e` — the name I
  actually see; no `gamma-substrate/appearance` name exists.
- **base SHA (as observed):** `8f41cc2ab277e6be4265ccf7d0dc632e2575f4cd`
- **engine:** `d657468d9e1f` (`own` build via `scripts/engine_build.sh`, run in
  THIS worktree). Provenance gate as its **own step before any number:**
  `tests/test_engine_provenance_migrated.py` **7 passed.**
- **oracle baseline, taken before any code:** `bash scripts/rung7_vision_bench.sh`
  → **222 passed, 0 failed**, exit 0, `data/` symlinked (§10.2, the with-corpus
  case). Load average at the oracle: **3.76 / 4.25 / 4.91**.
- **seeds:** 109000–109999.

## §0 — `check_claim`, VERBATIM (§3 clause 8)

```
SEED CLAIM 109000-109999: CLEAN -- no collision DETECTED.
  Scope: 811 files with seed sinks; 506 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**The 506 unresolved sinks are PRICED, not waved past:** a CLEAN verdict here
means *no collision detected*, never *no collision exists*. `scripts/seed_audit.py`
will be run on this rung's own runner after it is written, and its
`unknown_sinks` count reported in the results. **Every seed this rung draws is a
DIRECT ELEMENT of an explicit `range` inside the declared block — never
`sd + K`** (the refusal-capacity rung consumed 1000 seeds outside its block
through offset expressions the static ledger structurally cannot resolve).

---

## §1 — THE PRIOR QUESTION, ANSWERED FIRST AND REGISTERED AS A TEST

The brief requires this be settled before R6 is made tolerant:

> **A DENSE BOUNDED RASTER CANNOT EXPRESS TRANSLATION IN THE CHANNEL
> `TimeInfer` READS IT FROM.** An exact toroidal roll fails R6 64/64, not R5,
> because a full raster's coordinate set is translation-invariant — the offset
> reads `(0,0)` and all the motion moves into the slot R6 forbids to change.

**MY ANSWER, REGISTERED IN ADVANCE: NO — the input must not be a dense bounded
raster, AND THE REASON IS NOT R6.** The argument, which A3 below TESTS rather
than asserts:

A full raster's coordinate set is the whole grid in every frame. Sorted pairing
therefore matches `(r,c) → (r,c)`; the offset reads `(0,0)`. **`TimeInfer`
excludes the identity** (`off.iter().all(|&x| x == 0) ⇒ None`, read from
`eval_time_infer`, to be VERIFIED against the engine and never against the
comment). So with R6 made tolerant the raster does **not** become explainable —
**it refuses at the IDENTITY exclusion instead, and refusing because you see no
motion is worse than refusing because the appearance changed.**

**⇒ The two deficits are INDEPENDENT and R6-tolerance does not touch the raster
one.** This does *not* make the build unnecessary; it SCOPES it. The build is
well-posed exactly where the pixel-seam rung isolated R6: a **SPARSE support
that moves with the scene** (its E4t / E4g arms), where the coordinate channel
carries the translation and R6 is provably the sole blocker (600/600 refusals,
no other requirement firing). It is **ill-posed on a raster**, and A3 measures
that rather than assuming it.

---

## §2 — THE MECHANISM

**NOT a tolerance. A PARTITION.** §13 would refuse a slack parameter, and there
is nowhere to put one that is not a magic number. Instead the non-coord slots
are SPLIT along a line the substrate already draws:

| slot class | example (`dim_types = ["pred","coord:r","coord:c","val"]`) | role |
|---|---|---|
| predicate | slot 0, `"px"` | **still required byte-identical** — the arc's standing rule that the predicate slot is never transformable |
| coordinate | slots 1,2 (`coord:`) | the rigidity channel, exact integer offset, unchanged |
| **appearance** | slot 3, `val` | **REMOVED FROM THE VERDICT**, and its per-cell disagreement COUNTED and REPORTED as a separate field |

**`P_tol`, stated exactly** (implemented INDEPENDENTLY in the runner, and — at
Stage 2 — in Rust; the two must agree condition-by-condition):

1. ≥ 2 frames, none empty, equal cardinality across frames;
2. each frame sorted by **(predicate, coord slots)** — appearance excluded from
   the sort key, because an appearance change would otherwise scramble the
   pairing;
3. one uniform integer offset on the coord slots, holding for EVERY paired cell
   of EVERY consecutive pair;
4. predicate slot byte-identical on every paired cell;
5. offset non-zero (identity excluded — unchanged);
6. **`appearance_residual`** = the number of paired cells whose appearance slots
   differ, summed over pairs. **REPORTED, NEVER COMPARED AGAINST ANYTHING.**

**There is no tolerance in this and nowhere to put one.** Every clause is exact
integer arithmetic or exact equality. This is §13's strongest available shape —
**not a number that falls out, but no number at all** — and it is the form the
pixel-seam rung named ("carry appearance outside the signature") rather than the
form it warned against.

**Why this is not the move that turns a refuser into a selector.** The standing
law is *a comparison can be false, a selection cannot*. `P_tol` remains a
COMPARISON — *does the translated support EQUAL the observed support?* — with a
false case reachable on every input. It does not select a best δ from a set: δ
is READ from the first paired cell and then VERIFIED, so a wrong δ is a refusal,
not a lower-scoring winner. **`GapAbduce`'s disease was that two endpoints and
one free generator always fit; here the support of every frame must fit ONE
offset EXACTLY, and a third frame constrains it further.** A3/A4 test that this
survives contact with the engine instead of resting on the argument.

---

## §3 — THE STAGED DESIGN, AND WHY STAGE 1 CARRIES NO RUST

**Stage 1 measures `P_tol` THROUGH THE EXISTING ENGINE, with no Rust at all**,
by evaluating the unmodified `TimeInfer` on the SLOT-STRIPPED stimulus
(`dim_types = ["pred","coord:r","coord:c"]`). With no appearance slot present,
R6 is vacuous and both of the engine's exactness checks (`infer_translate_offset`
AND the `frames_equal` verification of every consecutive pair) reduce to
predicate + coordinates. **That is `P_tol` exactly.**

**Registered as a CLAIM TO CHECK, not an assumption — instrument check E:**
for every condition, `engine(stripped) explained == P_tol(full, computed in the
runner)`. **`n_disagree` must be 0.** A disagreement means my source reading of
the engine is wrong and **blocks Stage 2** (this tree has had four
comment-vs-engine divergences in a week; the pixel-seam rung's 6 592-fold
agreement check is the template, and its scope caveat is inherited: this
validates the ok/not-ok VERDICT, not any label ordering).

**Stage 2 builds the Rust Term `SupportInfer`** — ADDITIVE, appended at enum
index **177** (`GapAbduce` 175, `GapVerify` 176 are UNMOVED) — **IFF Stage 1's
ceilings pass.** It exists to deliver what slot-stripping cannot: the
`appearance_residual` field, i.e. the second half of the partition, so the
appearance verdict is available to the graph instead of being destroyed at
ingestion. **If a ceiling fails, the Term is NOT built and the rung reports a
negative. That is a legitimate outcome and it is registered as one.**

---

## §4 — THE PRE-REGISTERED FALSE-ACCEPT CEILINGS

*Registered BEFORE the Term is written, as the brief requires, and with the
retraction action stated for each. **No ceiling below is a chosen constant.***

**C1 — THE PARTITION DOES NOT LEAK. `fa_silent == 0`, EXACTLY.**
`fa_silent` = the number of conditions where `P_tol` ACCEPTS, the strict
operator REFUSES, and `appearance_residual == 0`. **Ceiling: 0.**
*Non-zero ⇒ the tolerance is silently swallowing a discrimination the strict
operator made ⇒ the Term is not shipped.*
**§13.1 DECLARATION, MADE IN ADVANCE: C1 IS LOGICALLY FORCED.** If coordinates
and predicate agree and the strict operator still refused, the disagreement can
only be in appearance, so the residual cannot be zero. **It therefore carries NO
evidential weight as a finding.** It is retained as an INSTRUMENT CHECK on the
Rust field, for one specific reason: `GapAbduce`'s `refused()` calls `finish()`,
which SELECTS the field, so a patch restoring a measurement on a refusal
**silently did nothing** — an output of the constructor masquerading as a
measurement. C1 measured non-zero-where-it-must-be-non-zero certifies
`appearance_residual` is MEASURED. Reported as an instrument check, never as a
result.

**C2 — THE NOISE CEILING IS ANALYTIC, NOT CHOSEN.** On stimulus families where
NO rigid support motion is present, `P_tol`'s accept rate must lie **within the
Wilson CI of an expectation computed by exhaustive enumeration inside the
runner, before the arm is read** (GapAbduce's template, applied prospectively).
*Measured above that expectation ⇒ the implementation is WEAKER than the
predicate it claims ⇒ retract, do not tune.*

**C3 — THE OPERATOR MUST STILL DISCRIMINATE MOTION FROM NON-MOTION.**
`P_tol`'s accept rate on the no-rigid-motion families must be **CI-separated
strictly below** its accept rate on the rigid-motion family.
*CI overlap ⇒ the operator cannot tell motion from its absence on the support
channel alone ⇒ it is a selector in a comparison's clothing ⇒ THE TERM IS NOT
SHIPPED and the rung reports the negative.*

**C4 — NOTHING THE STRICT OPERATOR EXPLAINED MAY BE LOST.** Every condition the
strict operator explains, `P_tol` must also explain. **Ceiling: 0 regressions.**
*(Forced by the predicate being strictly weaker — declared, retained as an
instrument check.)*

**AND THE STANDING REFUSAL, REGISTERED:** if C2 or C3 fails, the response is a
NEW pre-registration with a NEW mechanism-level hypothesis — **never a parameter
search, never a slack term, never a re-run** (§3.6, §5).

---

## §5 — ARMS, STATISTICS, AND n

`N_DRAW = 200` per arm. Seeds are DIRECT elements of explicit ranges:

| arm | seeds |
|---|---|
| A1 capability | **109000–109199** |
| A2-SWAP | **109200–109399** |
| A2-NOISE | **109400–109599** |
| A2-RECT | **109600–109799** |
| A2-RAGGED | **109800–109999** |

A2 arms are additionally run at **N = 2 and N = 3 on the SAME draws** — a
PAIRED contrast, not two samples.

Stimuli, corpus and construction constants are INHERITED UNCHANGED from the
pixel-seam rung (`results/gapseam_starts.npz`, `DOT=4`, `PATCH=8`,
`FIELD_H=24`, `FIELD_W=48`, `CROP=24`, `S=4`, `BG`, `FG`, `ROW`, `MAX_B=8`,
`Q_GRID = [2,4,8,16,32,64,128,256]`, `START_GRID`). **All are declared
CONFIGURATION — bound once, never a verdict threshold.** `q` and `N` are AXES:
iterated, never compared against.

**A0 — WIRING CONTROLS, RUN FIRST, AND THE RUN ABORTS ON EITHER.**
POS: moving dot, N=3, stripped ⇒ `time_inferred`, offset `(0,4)`.
NEG: stationary dot ⇒ `time_none`.
PROBE: a paired IN-PROCESS positive codebook probe on a KNOWN ORBIT in the same
booted substrate — **never** a read of `coord_dims` off a measured call, which
is hardcoded empty by the refusal constructor and made **167 false accusations**
for the timephi rung.
**A0-FIELDS (Stage 2 only):** every field read off a refusal is asserted by an
INDEPENDENT Term evaluation, one per field — the shape in which the `finish()`
selection bug surfaces.

**A1 — THE CAPABILITY.** Pixel-seam E4t / E4g stimuli, N=3, real photometry,
200 draws × 8 q, **stratified by LIVENESS** (the quantized patch content is not
identical across the three frames — exact array inequality, no tolerance).
Statistic: `live & explained` under strict vs under `P_tol`.
**§13.1: LARGELY FORCED** — E4s already explained 1 600/1 600 with the slot
absent. Retained as a REPLICATION on the full-slot stimulus and for the liveness
stratification, which is the arm that caught a dead pilot. **Low weight,
declared in advance.**

**A2 — THE FALSE-ACCEPT ARMS. THE HEADLINE, AND WHERE THE WEIGHT SITS.**

- **A2-SWAP** — ground-truth rectangular support translating rigidly by `S`;
  the CONTENT inside drawn from INDEPENDENT video times per frame. The strict
  operator refuses (appearance differs); `P_tol` accepts. **This is exactly the
  discrimination the tolerance gives up.** Feeds C1.
- **A2-NOISE** — supports drawn INDEPENDENTLY per frame (equal cardinality,
  random cells). No rigid relation exists. Feeds C2 and C3.
- **A2-RECT** — a CONGRUENT solid `PATCH × PATCH` support placed at three
  INDEPENDENTLY drawn positions, content independent. No object moves. Because
  the supports are congruent by construction, `P_tol` accepts iff the positions
  are equally spaced and non-degenerate. Feeds C2 (analytic expectation
  enumerated exactly over the position grid) and C3.
- **A2-RAGGED** — identical protocol, but the support is the **threshold
  silhouette** of the real patch (not congruent in general). Feeds C2/C3.

**THE OPEN CONTRAST, AND IT IS THE REAL MEASUREMENT:** RECT vs RAGGED, and
N=2 vs N=3. What an appearance-tolerant acceptance MEANS is bounded by how much
information the SUPPORT carries — a convex congruent blob carries almost none, a
ragged silhouette carries a lot. **Nothing forces the magnitudes.**

**A3 — THE RASTER ARM. THE PRIOR QUESTION, TESTED.** Pixel-seam E0 (real video,
every cell) and E2 (EXACT toroidal roll), 8 starts × 8 q = 64 each, under
`P_tol`. Statistic: accept count, and the runner's INDEPENDENT diagnosis.

**A4 — THE RETAINED REFUSAL.** `P_tol` on: unequal cardinality; a dot moving
with an ACCELERATING step (breaks the uniform offset at N=3); a SHUFFLED orbit.
**§13.1: FORCED** — each breaks a clause `P_tol` KEEPS. Declared, run only to
confirm the source reading against the real engine, which is the thing a doc
comment failed at this week. **No evidential weight.**

**Every refusal reported must be a FAILURE AFTER A FULL SEARCH, not a refusal at
a guard** — `checked` is reported on every refusing condition (the `GapVerify`
precedent), and the runner's independent predicate enumerates rather than
guards.

---

## §6 — PREDICTIONS, STATED IN ADVANCE, WITH PROVISOS

| | prediction | forced? |
|---|---|---|
| **P0** | **A3: `P_tol` refuses the raster 64/64 on BOTH E0 and E2**, and the runner's independent diagnosis says **IDENTITY (zero offset)**, not appearance. **⇒ R6-tolerance does not rescue a raster.** *Proviso: if instead it ACCEPTS with a non-zero offset, my reading of the identity exclusion is wrong and the raster question reopens.* | **no** — the mechanism is derivable but the diagnosis is not, and my predecessor's identically-shaped proviso BROKE |
| **P1** | A1: `live & explained` under `P_tol` = every live condition at q ≥ 4; under strict = 0 (reproducing the predecessor) | largely **yes** (declared, §5) |
| **P2** | C1: `fa_silent = 0`, and `appearance_residual > 0` on every SWAP acceptance | **YES — logically forced** (declared, §4) |
| **P3** | A2-NOISE: 0/200 accepts at N=3, matching an enumerated expectation indistinguishable from 0 | **no** |
| **P4** | A2-RECT at **N=2**: accept rate **1.000** — any two congruent supports are translates | **YES — forced** (declared) |
| **P5** | A2-RECT at **N=3**: within CI of the exactly-enumerated equally-spaced-position rate, and **CI-separated below N=2**. **THE THIRD FRAME CONSTRAINS — the arc's law, tested on the tolerant operator.** | **no** |
| **P6** | A2-RAGGED CI-separated **below** A2-RECT at N=3. *Two-sided: if it is NOT, support shape carries no discrimination beyond congruence and the tolerant operator's acceptance means less than I think.* | **no — the most open arm** |
| **P7** | C3 passes: rigid-motion accept rate CI-separated above every no-motion arm | **no** |
| **P8** | A4: refuses all three | **YES — forced** (declared) |
| **P9** | Instrument check E: `n_disagree = 0` | **no** (it is a claim about my source reading) |

**Where the evidential weight actually sits, declared in advance (§13.1):**
**P0, P3, P5, P6, P7, P9.** P1/P2/P4/P8 are forced or near-forced and are
reported as controls and instrument checks, not as findings.

---

## §7 — DECISION RULE, INCLUDING WHAT A NULL MEANS

| observed | reading |
|---|---|
| C1 ✅ C2 ✅ C3 ✅ C4 ✅, P0 refuses | **THE PARTITION IS SOUND AND SCOPED.** Ship `SupportInfer` (Stage 2), OFF by default, no seed armed. The R6 deficit is purchasable on a sparse moving support and NOT on a raster. |
| **C3 ✗** (no-motion CI overlaps motion CI) | **THE TOLERANCE BUYS NOTHING.** The operator that cannot refuse. **Do not ship. Report the negative.** |
| **C2 ✗** (accepts above the enumerated chance rate) | **THE IMPLEMENTATION IS WEAKER THAN ITS OWN PREDICATE.** A bug, or a predicate I have mis-stated. Do not ship; diagnose; new pre-registration. |
| **C1 ✗** | **THE PARTITION LEAKS.** Do not ship. |
| **P0 ✗** (raster accepted) | The prior question REOPENS and this rung's scoping is wrong; report it as the headline and do not ship on the strength of the other arms. |
| P6 null (RAGGED ≈ RECT) | Support shape entropy does not discriminate beyond congruence. **This does not block the ship** — it BOUNDS what an acceptance means, and that bound is reported as the scope limit on the capability. |

**A null in C3 is the most informative outcome available and is registered as
publishable.** The pixel-seam rung earned this lever; it did not earn the
assumption that the lever works.

---

## §8 — §13 COMPLIANCE, DECLARED BEFORE THE CODE

- **No tolerance parameter exists anywhere in the mechanism.** Every clause of
  `P_tol` is exact integer equality. There is nothing to slide.
- **Every verdict function decides by an exact equality on a logical or integer
  quantity, a count `== 0`, or a CI comparison between two MEASURED
  quantities.** No ordering against a non-zero literal decides anything.
- `q`, `N`, `START_GRID`, `S_GRID` are **AXES** — iterated, never compared
  against.
- The figure/ground split uses the frame's **own modal value** (data-derived).
- Liveness is an **exact array inequality**; there is no tolerance in it.
- **`tests/test_appearance_ast_migrated.py`** will enforce this by a Python
  **AST walk** — never a substring selector (this arc's record on those is 0–5)
  — with module-level name bindings RESOLVED TO THEIR LITERALS (a name bound to
  a literal is a literal), subscript indices PRUNED BY EXPLICIT RECURSIVE
  DESCENT (`ast.walk` CANNOT prune), and **POSITIVE-CONTROLLED by injection with
  the injection site asserted present first**, including the named-literal
  clause **VACUITY-GATED against itself** (blinded resolver ⇒ the injection must
  scan to `[]`).
- **Declared CONFIGURATION residuals, bound once and never a verdict
  threshold:** `DOT`, `PATCH`, `FIELD_H/W`, `CROP`, `S`, `BG`, `FG`, `ROW`,
  `MAX_B`, `N_DRAW`. Inherited unchanged from the pixel-seam rung.

## §9 — §9 COMPLIANCE (DEFAULTS PRESERVE COMMITTED RESULTS)

The Rust is **ADDITIVE**: one new `TermNode` variant appended at the END of the
enum (index **177**); every existing variant index UNMOVED; no existing Term,
evaluator or seed touched. **No seed manifest ships. No default moves.** Oracle
`222/0` before and after; `cargo test --lib -- --test-threads=1` before and
after; `variant_table_covers_the_enum` must pass.

## §10 — CPU DISCIPLINE

At most **2 concurrent workers**. `os.getloadavg()` is recorded **alongside
every measurement written to an artifact**. **No wall-clock cutoff is a
verdict** — every quantity in this rung is exact, counted, or a proportion, so
contention moves the wall clock and nothing else. Timing rungs are not run here.
