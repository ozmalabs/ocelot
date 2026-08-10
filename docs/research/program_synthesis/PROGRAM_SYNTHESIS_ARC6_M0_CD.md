# PROGRAM SYNTHESIS ARC 6 — M0, CEILINGS C AND D: two more nulls, precisely measured

**Date:** 2026-08-01. Answers, before anything is built: **C** — does the
MATH `ShapeSignature` codebook (`seeds/math_capability_shapes.json`) give
GENUINE algorithmic recognition over MBPP, where the systems codebook gave
zero? **D** — of the 36-task honest structural residual
(`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`), how many admit a
theorem-derived property that reaches them? Driver:
`scripts/arc6_ceiling_cd.py`. Artifact: `results/arc6_ceiling_cd.json`. No
synthesis/engine/seed/adapter code touched anywhere — measurement only.

**Headline: Ceiling C is a clean, sharper null than the arc-5 probe found.
Ceiling D is NOT a null on its own terms, but it is not the seam it looks
like either** — every one of the 36 traps admits a real, execution-verified
violated property (36/36 in category **b**), and **zero** of the 36 are
expressible in `comprehend_theorem`'s existing form (category **a** is
empty, confirmed live, not assumed). The ceiling for Seam D as currently
scoped is **0**; the entire 36 sits in the import list.

---

## 0. A correction to the plan document, made before anything else

`PROGRAM_SYNTHESIS_ARC6_PLAN.md` §1 (Seam C) states *"`seeds/
math_capability_shapes.json` holds **17** `ShapeSignature{kind:"math"}` with
real relational signatures."* Reading the seed file directly
(`results/arc6_ceiling_cd.json::ceiling_c_math_shape_recognition.
shape_codebook`): the file holds **17 `ShapeSignature` nodes in total**, of
which only **6** carry `kind:"math"` (`fractal`, `phi_bounded_recursion`,
`self_similarity`, `symmetry`, `curvature`, `topology`); the other 11 carry
`kind:"faculty"` (`spatial_attention`, `teacher_bootstrap`,
`library_growth`, …). The plan's "17" conflates the seed's total node count
with its math-kind subset. Ceiling C below measures the real 6.

---

## 1. CEILING C — does the math codebook give genuine recognition?

### 1.1 The mechanism doesn't fit the data, and that is the first finding

`RecogniseShape` (the Rust Term `domains/teach.py::categorise_by_shape` and
`TransferDecode` both share, confirmed by reading `runners/dsl/src/
shape_decode.rs::recognise_meta_shape`) mechanically requires a `MetaShape`
node with `has_principle` edges to nodes carrying an explicit `keywords`
list — a substring-of-keyword scorer, nothing else. `math_capability_
shapes.json`'s `ShapeSignature` nodes carry **neither** a `MetaShape` type
**nor** a `keywords` field — they carry a `signature` string of RELATION
TUPLES (`[["build","NEW","from","PRIOR"], ["refers","NEW","to","SELF"], ...]`),
built for the `AntiUnify` structure-mapping bridge (confirmed: grep across
`domains/*.py` and `runners/dsl/src/*.rs` finds **zero** live callers that
feed `math_capability_shapes.json` into `RecogniseShape`, `TransferDecode`,
or any synthesis-facing consumer — it is read only by the arc-5 probe script
and this one, as a citation).

So *literally* "pointing `RecogniseShape` at the math codebook" first
requires deciding what a "keyword" even is for a node type that was never
built to have one. Three variants were measured, each mechanically read off
content **already present in the seed file** (no new vocabulary authored):

| variant | keyword source | example (`fractal`) |
|---|---|---|
| `name_concept` | the shape's own `name`+`concept` fields, snake-split | `fractal`, `dimension` |
| `relation_all` | every lowercase token in the `signature` tuples, unfiltered | `build`, `by`, `from`, `to`, `refers`, `base`, `bound` |
| `relation_content` | (ii) minus a standard closed-class English stopword list | `build`, `refers`, `base`, `bound` |

### 1.2 Recognition coverage — three very different numbers, one lesson

| variant | n recognised / 257 | rate | shapes hit |
|---|---|---|---|
| `name_concept` | 1 | 0.4% | `self_similarity` ×1 |
| `relation_all` | **245** | **95.3%** | `fractal` ×202, `curvature` ×31, `topology` ×12 |
| `relation_content` | 6 | 2.3% | `fractal` ×1, `symmetry` ×3, `topology` ×2 |

The `relation_all` number is not a capability — it is the seed's relation
grammar containing the English words **to/from/by/is/under/into/between**,
which appear in almost any sentence. This is a sharper version of arc5's own
finding, not a different one: **the codebook is not lexical at all**, so any
attempt to run it through a substring-based recognizer either finds nothing
(`name_concept`) or finds everything via grammatical glue
(`relation_all`) — there is no middle setting that finds something *and*
means something, because the seed carries no domain keyword list to find.

### 1.3 Genuine vs spurious — every hit traced, 0/7 genuine

All 7 hits across the two informative variants (`name_concept`'s 1 +
`relation_content`'s 6) were traced to their causing keyword and classified
by the same bar arc5 used — a hit is genuine only if the causing word is
concept-specific AND the task's own structure independently exhibits that
concept:

| variant | task | shape | causing keyword | prompt (excerpt) | verdict |
|---|---|---|---|---|---|
| name_concept | 283 | self_similarity | `self` | "…is less than or equal to the digit **itself**" | **spurious** — "itself" contains "self"; no recursive self-reference at smaller scale in the task |
| relation_content | 101 | fractal / phi_bounded_recursion | `base` | "kth element…using 1-**base**d indexing" | **spurious** — "base" here means indexing convention, not a scale-bound recursion base case |
| relation_content | 222 | topology | `type` | "…have same data **type** or not" | **spurious** — "type" is a Python type-check, not topological open-set/contact structure |
| relation_content | 237 | symmetry | `map` | "returns a dictionary **map**ping each…tuple to…count" | **spurious** — "mapping" is a dict construction, not permutation-invariance |
| relation_content | 286 | symmetry | `repeat` | "array…formed by **repeat**ing the given array k times" | **spurious** — literal array repetition, not an invariance claim |
| relation_content | 395 | symmetry | `repeat` | "first non-**repeat**ed character" | **spurious** — "non-repeated" is a frequency check, not symmetry |
| relation_content | 470 | topology | `pairwise` | "**pairwise** addition of…neighboring elements" | **spurious** — arithmetic over adjacent pairs, not topological contact/invariant-type reasoning |

**0/7 genuine.** No task in the 257-prompt test population contains the
literal words "symmetric"/"symmetry"/"balance" recognised via the concept
word itself (the one branch the classifier reserves for a possible genuine
hit never fired), and every other hit is a textbook substring collision —
structurally the identical failure mode arc5 found ("remove"→"move",
"opposite"→"posit"), now against a different, relation-shaped vocabulary
that collides even more indiscriminately once its grammatical glue words are
included.

### 1.4 Actionability — even a genuine hit would carry nothing

The decisive point, stated once because it generalizes: **even in the
counterfactual where a prompt literally says "symmetric" and that word
alone caused the hit, the codebook supplies nothing beyond a label.**
`math_capability_shapes.json`'s `ShapeSignature` nodes carry no attached
constraint, relaxation family, or IR template — they are analogy anchors for
`AntiUnify` cross-domain structure-mapping (bridging a math CONCEPT to one
of the agent's own FACULTIES), not synthesis-facing payloads. Meanwhile
`PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md` (Q2) and `PROGRAM_SYNTHESIS_ARC5_
WIDEST_GAP.md` already measured the actual, useful version of "symmetry" —
checking the accepted program's own IR under argument permutation — directly
against the IR, with **no seed dependency at all**, and found it applicable
to only 3/76 traps with zero mass beyond the existing D3/D4 detectors.
Recognising the *word* "symmetric" in a prompt is strictly weaker than and
downstream of that direct IR check. A recognition step that, even at its
best, reproduces a weaker version of a check the pipeline can already do
for free is not a capability.

### 1.5 Verdict — Seam C

**Null, and sharper than arc5's.** 0 genuine recognitions across three
honestly-constructed keyword variants (1/257, 245/257, 6/257 — none
informative), 0 actionable even under the most charitable hypothetical.
**Seam C is not worth building.** The seed itself would need an entirely new,
hand-authored, program-synthesis-specific keyword vocabulary AND a payload
(constraint/relaxation/template) attached to each shape before this seam
could contribute anything — at which point the "recognition" step is
redundant with directly authoring the constraint, which is what arc5 already
did more cheaply, directly against the IR.

---

## 2. CEILING D — can theorem-derived properties reach the 36 residual?

### 2.1 Method

For each of the 36 residual traps (`results/arc4_structural_verdicts.json::
new_honest_residual_ids`): (1) read the prompt, name a property implied by
its ordinary mathematical/domain meaning (elementary geometry, number
theory, string/collection semantics — external knowledge, never read from
the task's held-out row); (2) execute the REAL accepted (wrong) IR
(`domains.mbpp_arc3_battery.prog_eval`, unmodified) at 2–3 hand-constructed
witness inputs (never the dataset's own held-out row — that is read
**only afterward**, in one isolated confirmation function, per the
discipline); (3) attempt to phrase the property in `comprehend_theorem`'s
`{subject, modifier, invariant, value, condition}` form and run it live.

**Held-out isolation, concretely.** Two of the 36 needed extra care: task 56
("one less than twice its reverse") and task 67 (Bell numbers) both had an
initial witness pick that happened to *agree* with the trap by coincidence.
Both were resolved by *widening the witness search itself* (more small
values, or a plain brute-force search over the stated **relation**, never
over the dataset) — task 56's witnesses (`a=1,793,7993`) are the first three
positive integers satisfying the relation itself, found independently of
which row the dataset withholds; task 67's witness (`a=26`) is the smallest
divergence found by a forward sweep from 0, well short of the task's own
(much larger) held-out input. Neither search consulted the held-out file.

### 2.2 Result: 36/36 land in category (b); (a) is empty; (c) is empty

| category | n | meaning |
|---|---|---|
| **(a)** property exists, expressible in `comprehend_theorem`'s current form, and refutes | **0** |
| **(b)** property exists, execution-verified genuinely violated, but inexpressible in the current form | **36** |
| **(c)** no property in the prose reaches it | **0** |

Every one of the 36 has a real, prompt-entailed, execution-confirmed
violated property — this is itself informative: **the 36 is not an
"arithmetic bugs with no general shape" bucket.** A sample, with the
witness that refutes the trap (full table with all witness checks and the
after-the-fact held-out confirmation is in the artifact's `per_task`):

| id | property | witness | trap output | correct |
|---|---|---|---|---|
| 17 | perimeter of a square = 4×side | a=1 | `True` (a bool!) | 4 |
| 105 | count of `True` elements in a list | `[True,True,False]` | 0 | 2 |
| 235 | set the 1-indexed-even bits of a, within its own width | a=1 | −8 | 1 |
| 300 | central binomial coefficient C(2n,n) | (per artifact) | wrong | correct |
| 392 | `f(n)=max(f(n//2)+f(n//3)+f(n//4)+f(n//5), n)` | (per artifact) | wrong | correct |
| 444 | trim each tuple by k from both ends: `t[k:len(t)-k]` | b=0 (no trim) | wrong constant string | full tuple unchanged |
| 452 | loss = max(0, selling−cost) | a=100,b=150 | 100 | 50 (coincided with truth only when b=2a) |
| 67 | Bell number via the Bell triangle | a=26 | −5708985697509898574 (i64 wraparound) | 49631246523618756274 |
| 455 | month has 31 days iff in {1,3,5,7,8,10,12} | a=4 | `True` | `False` |

### 2.3 The live theorem-grounding probes — (a)=0 confirmed, not assumed

`RESEARCH_MATH_CAPABILITY_AUDIT.md` §3.2 already concluded from static
reading that `comprehend_theorem`'s grammar is closed over group-theoretic
statements. This measurement **reproduces that conclusion live**, per the
brief's explicit instruction not to assume it:

| probe | statement | comprehended? |
|---|---|---|
| positive control | "a group with torsion has cohomological dimension infinite" | **True** |
| task 17 | "a square with side length has perimeter 4 times the side" | False |
| task 79 | "a string with odd length has odd_length true" | False |
| task 105 | "a list with all elements false has count 0" | False |
| task 224 | "a number with k set bits has popcount k" | False |
| task 292 | "a pair with numerator and denominator has quotient the floor division" | False |
| task 455 | "a number with membership in the 31 day months has days 31" | False |
| generic | "a function with permutation symmetry has output invariant under argument order" | False |

The positive control **grounds successfully**, proving the mechanism works
when aimed at its own domain. Every one of the 7 program-property phrasings
fails at the identical point — `ground_modifier` reports an "unaccounted
contentful word," because `property_modifiers` (`seeds/theorem_
constructions.json`) is a closed vocabulary of GROUP properties
(torsion/splits/free/…) composed over `ground_reductions.KNOWN_OBJECTS`
(free-product algebraic structures). There is no antecedent atom and no
grounding target for a property of a number, string, list, or program,
**regardless of how the property is phrased.** This is a domain-of-discourse
mismatch, not a wording problem — it generalizes to the full 36 without
needing 36 separate live calls, exactly as the audit's static reading
predicted, now empirically confirmed.

### 2.4 What form (b) would need

Named once, since it is the same answer for all 36: a new
statement-construction family whose *subject* is a function/collection/
number (not a group), a new `property_modifiers` table over program-shaped
antecedents (homogeneity/scaling, boolean-relation satisfiability,
element-count, bit-position, string-length parity, closed-set membership,
floor-division, divisor-sum identities, linear-recurrence identities), and —
critically — a new grounding **target**: a predicate over a *candidate
program's evaluated output at a witness input*, not a predicate over a
`KNOWN_OBJECTS` group object. This is exactly the `RequiredProperty`-on-the-
Goal shape `RESEARCH_MATH_CAPABILITY_AUDIT.md` §3.5 already named as the
missing piece for the narrower symmetry-only case — this measurement shows
the need generalizes to essentially every property type found here, not
just symmetry.

### 2.5 Verdict — Seam D

**Not a null on the measured population — the 36 genuinely all have
reachable properties — but the ceiling for the seam AS SCOPED (wiring
`comprehend_theorem`'s *existing* form) is 0/36.** The entire population is
import list, not conversion list. Building Seam D for real means building a
**second, differently-scoped comprehension module** (program-spec grammar +
program-shaped property atoms + a program-evaluation grounding target) that
happens to share `comprehend_theorem`'s parse→ground→emit→self-verify
*shape*, not its content or its seed. That is a real, scoped, bounded
engineering task (comparable in size to building `comprehend_theorem` or
`extract_function` in the first place, per the audit's own estimate) — worth
doing only if the caller is prepared to build that second module, not to
reuse the first one.

---

## 3. Cross-cutting notes

- **Discipline.** Every SEARCH-side function in `scripts/arc6_ceiling_cd.py`
  (`_witness_check`, the reference relations, `q_ceiling_c`'s recognition
  path) takes only the accepted IR / revealed structure / hand-constructed
  witnesses; the one function that reads a task's own held-out row
  (`_confirm_against_held_out`) is called strictly after a witness violation
  is already found, for confirmation only, mirroring the sanctioned pattern
  in `PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md`/`PROGRAM_SYNTHESIS_ARC4_
  STRUCTURAL_NOTES.md`.
- **Twin-run determinism.** The script computes the full result twice and
  asserts a SHA-256 match before writing the artifact (`results/arc6_
  ceiling_cd.json::determinism`).
- **The 36 is re-derived, not hand-carried.** `load_residual_36_from_source`
  reads `results/arc4_structural_verdicts.json::new_honest_residual_ids`
  live and asserts it matches the id list quoted in this document.
- **Estimates labelled as estimates.** Ceiling C's classification and
  Ceiling D's property identification involved researcher judgment (naming
  a property from a prompt, choosing witnesses); every judgment call is
  recorded with its reasoning in the artifact (`per_task`, `classified_hits`)
  so it can be checked, not merely asserted.

---

## 4. Files

`scripts/arc6_ceiling_cd.py` (driver — Ceiling C's three keyword-variant
recognition sweeps + per-hit classification; Ceiling D's 36-task property
table, live witness execution against the real `prog_eval`, held-out-isolated
confirmation, and the live `comprehend_theorem` probes; twin-run
determinism). `results/arc6_ceiling_cd.json` (the artifact — full per-task
and per-hit detail for both ceilings, determinism hash, environment). This
file.
