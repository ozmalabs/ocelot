# RESEARCH: Math Capability Audit — what the jabberwock actually does in mathematics, and whether it can be aimed at the synthesis wall

Audit date: 2026-08-01. Scope: locate, characterise, and evidence-grade every
mathematical capability in this tree; answer the "HLE-level math" claim with
reproduced evidence; assess whether that capability can supply constraints to
the program-synthesis wall (`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md`,
`br_10_top_of_three`). This is an inventory audit, not a literature review.
Every capability below is evidence-graded: **[A]** gated test/script
reproduced live by this audit, **[B]** gated (pytest) but not independently
re-run here, **[C]** present in the tree but not exercised by any CI gate,
**[D]** aspirational / documentation only.

---

## Executive summary (read this first)

The math capability does **not** live in one place. Three disjoint code
paths, confirmed by direct import-graph inspection (zero cross-references
in either direction):

1. **`seeds/mathematics.json` (117 concepts + 22 rules)** — pure prose
   flashcards ("definition" / "why" / "category" strings) plus natural-
   language "if/then" heuristics, loaded into `domains/code_writing_cortex.py`
   for the agent's *self-modification / Rust-rewrite* work, not for solving
   math problems. **[B], recitation only ((a) in the brief's taxonomy).**
   Zero executable content — confirmed by reading the seed file directly.

2. **`domains/reason.py` + `domains/comprehend_theorem.py` +
   `domains/compute_grounding.py` + `domains/construct_compute_*.py` (9
   modules) + `domains/oeis_local.py`/`oeis_reference.py`** — a real,
   substantial hand-built computational-mathematics library (matrix rank
   over GF(2)/Q, Smith normal form, integral homology, Steenrod squares,
   spin bordism of BG₂, free-product Euler characteristics, hook-length
   S_n representation theory, exact enumeration) driven by a construction-
   grammar NL-to-Term-tree comprehender. **This is the faculty that
   produced every certified answer in `HLE_KEY_AUDIT.md`.** Genuinely does
   (c) *derive/compute* and, narrowly, (d) *prove-by-implication* (see
   `comprehend_theorem.py`). **[A], reproduced live three times below.**

3. **`domains/prog_synthesis.py` + `seeds/program_synthesis.json`** — the
   MBPP enumerate/retrieve/repair engine, ~28/257 (10.9%) live pass rate
   (`PROGRAM_SYNTHESIS_ARC4_SUMMARY.md:185`). **Imports nothing from (2) and
   nothing from (1)** — grep confirms zero references either direction.

**The reconciliation (Part 2) is therefore not a mystery: MBPP and "HLE
math" are answered by two pipelines that have never been wired together.**
The math pipeline succeeds by *deriving from held mathematical structure*
(a comprehended Term-tree evaluated over an interpreter of ~60 hand-coded
primitive operations); MBPP requires *search over candidate programs*
verified row-by-row. Neither pipeline calls the other's machinery.

**The HLE-level claim, honestly located:** a live, full, unassisted sweep
of the actual `data/hle_math.json` bank (n=1061, reproduced below) through
the "as-committed" pipeline reaches a **NUMBER on 22 questions and a
CORRECT answer on 20 (≈1.9%)**; 1021/1061 (96.2%) never even reach a typed
invariant. But on the narrow set of question-families it *does* reach, the
derivations are genuinely research-grade, self-verified, and — the sharpest
evidence — have caught **5 demonstrably wrong official answer keys**
(reproduced live for one below: HLE `6724eed8b60e`, Aztec-diamond tilings,
key 6 vs. certified-and-independently-confirmed 8). "HLE-level math" is
real but it is a spike, not a plateau: deep and rigorous on ~20-40 curated
question shapes out of 2370, silent everywhere else.

**Part 3 (synthesis wall):** the math faculty as built **cannot yet**
supply the `br_10_top_of_three` constraint, but the audit found the
concrete missing pieces are narrow and the general mechanism (a spec-read
structural fact gating `ps_accept`, exactly parallel to the existing
D1/D2/D3 detectors in `domains/prog_synthesis.py`) already exists in
skeleton form for a *different* purpose. Named gaps below.

---

## Part 1 — inventory, by mechanism

### 1.1 `seeds/mathematics.json` — prose knowledge, NOT problem-solving [B]

Read directly (`seeds/mathematics.json`): 117 `Concept` nodes, each
`{name, definition, why, category}`, e.g.:

```json
{"name": "equivalence_relation",
 "definition": "Reflexive, symmetric, transitive. Partitions set into equivalence classes.",
 "why": "Foundation of construction. Integers from naturals, rationals from integers, quotient structures.",
 "category": "foundations"}
```

22 `Rule` nodes are natural-language `if/then/why` heuristics tagged with a
`soundness_category` from **program-semantics** vocabulary (`referential_
transparency`, `denotational_equivalence`, `cost_equivalence`,
`extensional_equivalence`, `algebraic_law`) — not proof-theory categories.
This is the tell: **this seed is not math-problem-solving knowledge, it is
mathematical-soundness guidance for the agent's OWN code-authoring
faculty** (`domains/code_writing_cortex.py`, confirmed by grep — the only
non-test importer of the `mathematics` microtheory). It feeds
self-modification / Rust-rewrite work (`domains/rust_rewrite_world.py`,
`domains/python_migration.py`, `scripts/agent_self_improves.py`), never the
MBPP battery, never HLE.

`tests/test_mathematics.py` (18 tests, reproduced live, all green) checks
only that ≥175 concept names exist after decomposition packs load and
≥45 rules carry a `soundness_category` — a **name-existence and count
check**, not an execution check. There is no test anywhere that evaluates
one of these 117 definitions to answer a question. **Grade: [B] gated, but
the gate only proves the flashcards are present — 100% (a) recitation, 0%
(c)/(d).**

`seeds/math_foundations.json` (17 concepts), `seeds/logic_mathematical.json`,
`seeds/mathematics_microtheory.json` are siblings of the same shape
(`concept`/`rules` prose dicts under a microtheory) — not separately
audited line-by-line but structurally identical on inspection (same
`{microtheory, concepts, relations}` schema, no executable fields).

### 1.2 `domains/reason.py` — the actual math computation tower [A]

1638 lines. Not a toy: implements (among others) `_matrix_rank_gf2`,
`_matrix_rank_q`, `_smith_normal_form_factors`, `_integral_homology`,
`_partition_count`, `_bg2_integral_homology_rank` /
`_bg2_integral_torsion_2rank` (mod-2 cohomology of the classifying space of
the Lie group G₂), `_spin_bordism_free_rank`/`_spin_bordism_torsion_2rank`,
`_cup_product`/`_cup_i_product`/`_steenrod_square_cochain` (Steenrod
algebra machinery over cochains), `_hook_dim` (S_n irrep dimension via the
hook-length formula), and a general integer/prime tower (`_factorize`,
`_totient`, `_divisor_sum`, `_nth_fibonacci`).

**`answer_within`** (line 1428) is the dispatcher: comprehend NL question
→ Term-tree "meaning" (via `domains/language.comprehend` over a controlled
lexicon, or, when an `agent` is supplied, via the graph-native Frame
layer) → `solve_within` estimates the op-cost of the planned computation
against a budget *before* running it (a genuine self-cost-model:
`estimate_complexity` walks the Term-tree, sums per-node op estimates) →
on budget overrun, `reconsider` tries cheaper alternative strategies →
`solve` walks the Term-tree, dispatching each head concept to a Python
capability function, with `count_where`/`sum_where`/`chain_sum`/
`chain_bind` as genuine **binder evaluators** (free-variable iteration
over a collection, re-solving the body per binding — the same shape as
the Rust DSL's `Fold`/`Filter`).

**Important scope-limiting fact, confirmed by reading `HLEWorld.run_solve`**
(`domains/hle_world.py`): the numeric *objects* a question refers to
(matrices, group generators, factor orders) are supplied externally per
question via a `bindings_factory` callback — the pipeline does not itself
extract "G = Z/5 * Z/8 * Z/2" as a graph object from raw exam prose in the
general case; that extraction is done by a narrower reader
(`presupposition_derivation.comprehend_asked_invariant`, see §1.3) which
reaches only ~5% of the bank (measured below). **Grade: [A]** — this is
the real interpreter/compute layer; reproduced live via the OEIS chain and
the HLE conviction scripts (§Part 2).

### 1.3 `domains/comprehend_theorem.py` + `domains/ground_reductions.py` — theorem-statement → checkable implication [B live-reproduced, not pytest-gated]

This is the module closest to the brief's "can it produce a checkable
property a candidate must satisfy" question, and it is real but **narrowly
scoped to one family: group-invariant theorems of the form "[a group] with
[property P] has [invariant I] = [value V]."**

The pipeline (verified by reading + running `scripts/comprehend_theorem_
demo.py` live):

1. **PARSE** — seeded construction-grammar forms
   (`seeds/theorem_constructions.json`: 6 `statement_forms`, 10
   `property_modifiers`, 4 `invariant_atoms`, 6 `value_atoms` — small,
   hand-curated but genuinely a grammar, not a per-sentence lookup) bind
   `{subject, modifier, invariant, value, condition}` from prose.
2. **GROUND** — the modifier → a held Python predicate over a free-product
   object (`ground_reductions.py`'s `some_factor_finite_cyclic` etc.); the
   invariant → a canonical key; the value → a literal or a **symbolic
   compute** (`value == "n"` → "count of infinite-cyclic free factors",
   *not* a baked number).
3. **EMIT** — a `ground_reductions.ImplicationClause(antecedent: Callable,
   value)`: literally a Python predicate over an object plus the value the
   theorem asserts when the predicate holds. **This is exactly the shape
   the brief asks about** — a checkable property, not just a fact.
4. **SELF-VERIFY** (`self_verify_clause`) — every emitted clause is run
   against `ground_reductions.KNOWN_OBJECTS`/`KNOWN_VALUES` (textbook
   knowns, never a question's answer); a clause whose antecedent fires on
   a known object but predicts the wrong value **self-rejects**
   (`comprehended=False`) rather than asserting a false implication.

**Live reproduction** (`scripts/comprehend_theorem_demo.py`, run under this
audit): the parser correctly derives clauses for the cohomological-
dimension and ends theorems **and** a paraphrase **and** two held-out
theorems it was not tuned for (free-abelian rank→cd, nontrivial free
product→infinite ends), all self-verified `PASSED`. It also correctly
**self-rejects** an adversarially malformed clause ("property t" — an
unaccounted contentful word) and **honestly MISSes** six real group
properties it cannot express (`solvable`, `nilpotent`, `amenable`,
`residually finite`, `hyperbolic`, `virtually free` — named residuals, not
silently guessed). This module's output is called by `ground_reductions.py`'s
cd/ends builders and is load-bearing for HLE conviction 1 (Hurewicz kernel
rank), confirmed live in §Part 2.

**Honesty note on evidence grade:** there is **no dedicated pytest file**
for `comprehend_theorem.py` (grep found none; `tests/test_theorems_as_terms_
migrated.py` tests an unrelated Term-rewriting "theorem" concept). Its
only regression check is the demo script's own internal assertions
(printed `True`/`False`, not a pytest red/green gate). **This is a real,
working, self-verifying mechanism I ran and confirmed live, but it has no
CI regression protection — a future refactor could silently break it.**
Scope is exactly one theorem family (group invariants over free products);
it does not generalize to arbitrary "spec-shaped statements."

### 1.4 `domains/compute_grounding.py` + `domains/construction_grammar.py` (`extract_function`, `comprehend_recursive`) — prose → executable definition, verified against real ground truth [A]

`compute_grounding.py`'s `comprehend_computational_definition` composes a
definition ("the lcm of a and b is a\*b/gcd(a,b)") into a Term-tree over
**held primitives** (`gcd`, `times`, `div`, `mod`, `divisor_sum`, …) and
evaluates via `reason.solve`. Its own docstring is explicit about the
frontier: a definition whose operands are not themselves computational
(a bordism class's "manifolds whose disjoint union bounds…") does not
compose, and the agent **abstains** rather than fabricating.

`construction_grammar.extract_function` (line 922) reads an OEIS-style
prose definition and proposes candidate closed-form RHS expressions via
three routes: (a) flat clause match, (b) embedded `=` segment parse, (c)
**order-N recursive composition** (`comprehend_recursive`, line 1113) —
a genuine recursive descent over member-form/value-map/filter/aggregator
constructions (e.g. "sum of squares of divisors of n" is comprehended
compositionally: aggregator(sum) ∘ value-map(square) ∘ member-form
(divisors-of-n)), bottoming out at member-form "bedrock" leaves. This is
real compositional NL-to-formula machinery, not a lookup table.

**Live reproduction** (`scripts/oeis_extract_verify.py`, run under this
audit against the real downloaded OEIS parquet dump,
`data/oeis/*.parquet`, confirmed present):

```
[OK ] A000005  'd(n) ... the number of divisors of n' -> count{k in 1..n : k|n}   reproduces [1,2,2,3,2,4,2,4]
[OK ] A000010  'Euler totient function phi(n)...'      -> count{k in 1..n : gcd(k,n)=1}
[OK ] A000203  'sigma(n), sum of divisors'              -> divisor_sum(n)
[OK ] A000217  'Triangular numbers'                     -> n*(n+1)/2
[OK ] A000142  'Factorial numbers'                      -> factorial(n)
  -> 8/8 sequences EXTRACTED-FROM-PROSE and VERIFIED against the source's ground-truth values.
HONEST FRONTIER: A000045 (Fibonacci, recursive) and A000040 (primes, no closed form) -> None (named, not faked)
```

This is genuine propose-from-prose → verify-by-computation against real
external ground truth (a downloaded OEIS dump, not hand-typed values).
**Scope honesty: the 8 verified sequences are elementary number theory
(divisor count, totient, sigma, naturals, triangulars, evens, squares,
factorial) — undergraduate/high-school level, not "HLE-level."** The
mechanism (compositional grammar + real verification) is the valuable
part; the demonstrated vocabulary reach is small. **Grade: [A].**

### 1.5 `domains/construct_compute_*.py` (9 modules) — bounded exact enumeration, one family per module [A for the exercised ones]

`construct_compute_enumerations.py`, `_betti.py`, `_chain.py`,
`_gendef.py`, `_graphs.py`, `_group_orders.py`, `_homotopy.py`,
`_physchem.py`, `_pi1.py`, `_subgroups.py`. Each targets one *provably
finite, fully enumerable* invariant family (its own docstring's phrase):
S_n irrep dimensions via hook-length + partition enumeration, sum-of-squares
representation counts via bounded DP, Aztec-diamond domino tilings
(exhaustive perfect-matching enumeration **and** the closed-form
Elkies–Kuperberg–Larsen–Propp theorem, cross-checked against each other),
6-31G Gaussian basis-function counts, etc.

**Important honest caveat, found by reading the surface-reading regex
layer** (`construct_compute_enumerations.py` lines 90-120): the "read the
object's literal givens off the stem" step is implemented as **per-family
regexes** (`_IRREP_RE`, `_HOTEL_RE`, `_HOTEL_RESET`, `_HOTEL_TOGGLE`, …) —
each family's surface form was hand-authored after seeing that shape of
HLE question. This is not full open-domain NLU; it is a **family
recogniser**, one regex-family per invariant shape, honestly named as such
in the module's own docstring ("no per-question branch... a family
recogniser, the same enumeration on each"). The distinction that matters:
the *enumeration/count* is general and exact once the family is
recognised (real combinatorics, not answer-baking); the *recognition* of
which family a given stem belongs to is a hand-built regex catalogue, not
a general reader. **Grade: [A]** for the compute; **[C]/aspirational**
for "this generalises to open-domain problem recognition."

### 1.6 `domains/oeis_local.py` / `oeis_reference.py` — real external ground truth [A]

`oeis_local.py` reads a **real downloaded OEIS dump**
(`data/oeis/*.parquet`, the "christopher/oeis" dataset) — `present()`
returned `True` and the dump loaded successfully in the live run above.
Not a hand-curated toy set. This is the strongest "external, falsifiable
ground truth" artifact in the math stack.

### 1.7 `domains/math_hat.py` — analysis-by-synthesis object recognition from prose [C, not independently run]

A distinct mechanism: points the agent's generic `CortexLoop`
(coarse-match → adapt-style → order-N iterate → argmin readout) at the
"prose description → mathematical object" gap. `encode()` reads a prose
description's stated properties via construction grammar; `synth()`
derives a **candidate** object's properties via the held homology forward
model (Betti numbers over a small library of known spaces: S¹, S², disk,
point, two-points, torus); `compare()` uses the graph's own L2 metric.
This is a real, distinctively-designed recognition-by-generation loop, but
its object library is tiny (6 spaces) and it was not independently
executed under this audit (read only). **Grade: [C].**

### 1.8 `seeds/math_capability_shapes.json` — analogy bridge signatures, NOT problem constraints [B, misleading if taken at face value]

17 `ShapeSignature` nodes (6 `kind:"math"`, 11 `kind:"faculty"`), each a
small relation-tuple signature (e.g. `symmetry` / `balance_symmetry`:
`[["map","PART","to","PART"],["invariant","PART","under","TRANSFORM"],
["repeat","PART"]]`) consumed by the held order-N `AntiUnify` shape-matcher
to find a shared structural skeleton between two named concepts (e.g.
between a math concept and a perceptual/motor faculty, for cross-domain
analogy — "this feels like that"). **This is not a library of checkable
program/function properties.** The `symmetry` signature encodes "invariant
under transform" as a generic three-relation schema for ANALOGY MATCHING
across domains (e.g., relating bilateral body symmetry to `balance_
symmetry`), not "this function must be invariant under permutation of its
N arguments." It is structurally *adjacent* to what Part 3 would need
(see below) but is not wired to it and was not built for it. **Grade:
[B]** (the seed loads; no test exercises it as a synthesis-relevant
constraint source).

---

## Part 2 — the HLE-level question, with reproduced evidence

### 2.1 The benchmark artifact: `HLE_KEY_AUDIT.md` + the actual data files

`data/hle_math.json` (n=1061, confirmed by direct load) and
`data/hle_nonmath.json` (n=1309, confirmed) sum to **2370** — matching
`HLE_KEY_AUDIT.md`'s stated "2370 text-only questions, all subjects."
This is a real HLE split present in this worktree (confirmed one sample
question: `669402b41dcb3d5a1ef9e951`, "Compute the reduced 12-th
dimensional Spin bordism of the classifying space of the Lie group G2,"
answer `Z+Z+Z+Z+Z` — genuinely graduate/research-level).

`HLE_KEY_AUDIT.md` (dated running-dossier, read in full) reports **43
certified-and-checked, 36 confirmed, 5 convicted, 0 false accusations**.
The method: the system answers a question **only** under an independent
certificate (a second derivation route, a held-exact compute, or a
stem-forced limiting case); the key is read **after** derivation, purely
to score. A conviction requires (a) the system's answer certified sound,
(b) the key's error demonstrable, (c) no rescue reading survives
adversarial testing. **One prior flag was self-retracted** when
re-derivation found the system's own sign error — the dossier's own
self-correction discipline is evidenced in its text.

### 2.2 Live reproduction #1 — the OEIS chain (already shown in §1.4): 8/8 elementary sequences extracted-from-prose and verified.

### 2.3 Live reproduction #2 — CONVICTION 4 (Aztec diamond dominoes)

Ran `scripts/hle_conviction_aztec_dominoes.py` live:

```
CONVICTION 4 — HLE 6724eed8b60e (Mathematics): Aztec diamond size-2 domino tilings
CERTIFIED ANSWER (two independent routes): 8
  theorem 2^(2*3/2) = 8; exhaustive perfect-matching count over the 12-cell region = 8; agree
ADVERSARIAL RESCUE READINGS (none may equal the key 6):
  AD(2) total=8, up-to-D4=3, AD(1)=2, 2x2 rect=2, 2x3 rect=3, 3x4 rect=11
  AD(0..6) tiling counts = [1,2,8,64,1024,32768,2097152] (always a power of 2)
  6 is a power of two? False -> 6 cannot be the tiling count of ANY Aztec diamond
KEY: '6'.  VERDICT: CONVICT (certified 8 vs key 6; every rescue reading != 6)
```

This is genuinely airtight: the closed-form theorem (Elkies–Kuperberg–
Larsen–Propp) and brute-force exhaustive enumeration are **structurally
independent** and agree; the key (6) is provably not even a power of two,
which every Aztec-diamond tiling count must be. **Reproduced live,
matches the dossier exactly.**

**Caveat found while tracing provenance:** the enumeration used here
(`compute_aztec_domino_tilings`) *is* a committed, reusable function in
`domains/construct_compute_enumerations.py` — general in the sense that
it works for any `AD(n)`. But CONVICTION 5 (boolean expressions,
`scripts/hle_conviction_boolean_exprs.py`, inspected but not re-run) has
its recursive-descent parser and generative grammar written **inline in
the one-off script**, with no equivalent reusable module under
`domains/`. So the dossier's convictions are **not uniformly backed by
one general "faculty"** — some (Aztec) reuse a committed capability, some
(boolean exprs) are standalone verification scripts built for that one
question. Both are real, independent, non-answer-baked computations; the
distinction is about *reusability/integration*, not soundness.

### 2.4 Live reproduction #3 — the decisive measurement: full unassisted sweep of the real bank

Ran `scripts/retest_hle_math_cumulative.py` live over the full
`data/hle_math.json` (n=1061), using the pipeline **as committed** (no
per-question hand-holding, no bindings_factory shortcuts — this script
explicitly measures the "TYPE → GENERATE → ROUTE → COMPUTE → VALIDATE"
pipeline cold, reading the key only at the end to score):

```
INVARIANT ROUTE : TYPED 35 / NUMBERED 2 / CORRECT 1  (out of 1061)
STRUCT-FORM ROUTE: TYPED 20 / NUMBERED 20 / CORRECT 19
COMBINED (union) : TYPED 55 / NUMBERED 22 / CORRECT 20   (out of 1061)
invariant-route buckets: A(no-clause)=1021  B(clause-untyped)=5  C(typed-no-compute)=33  D(typed-compute-stall)=0
```

This is the single most important number in this audit. **1021/1061
(96.2%) of the real HLE math bank never reaches a typed invariant at
all** — the reader's "asked-invariant" openers (a specific catalogue of
phrasings for rank/euler-characteristic/homology/etc.) simply don't match
the stem. Of the 40 that do get typed, 33 have no matched compute faculty.
The pipeline reaches a **number on 22** and is **correct on 20** —
**≈1.9% of the full bank**, live, reproduced, honest.

This number is *lower* than the dossier's "43 certified" because the two
measure different things: the dossier's 43 draws on the **whole family
of hand-built scripts** across math, CS/AI, and physical-chemistry (each
targeting one curated question after a human/agent looked at it,
sometimes reusing a committed faculty, sometimes not — §2.3's caveat),
grown incrementally over many sessions and explicitly *not* claiming
uniform bank coverage (`HLE_KEY_AUDIT.md`'s own "Honestly LEFT OUT"
section lists ~15 more questions it could *not* certify). The 20/1061
figure is what happens when you run *only* the two currently-wired
general routes (invariant-typing + struct-form) over *every* question in
the bank without cherry-picking. **Both numbers are real and both are
honestly characterised in the source material; this audit's contribution
is running the uncherrypicked sweep live and confirming the 96% miss
rate is real, not rhetorical.**

### 2.5 The a/b/c/d distinction, applied

- **(a) Reciting held knowledge** — `seeds/mathematics.json`'s 117
  concepts (§1.1). Zero execution. This is the weakest and most
  over-claimable layer if quoted alone; it answers no HLE question.
- **(b) Recognising structure** — `math_capability_shapes.json`'s
  ShapeSignature/AntiUnify bridge (§1.8) and `presupposition_derivation
  .comprehend_asked_invariant`'s invariant-typing (reaches 55/1061 = 5.2%
  of the bank, per §2.4). Recognition is real but the catalogue of
  recognisable shapes is small.
- **(c) Deriving/computing** — `reason.py`'s Term-tree interpreter over
  ~60 held primitives (homology, Steenrod squares, hook-length dimensions,
  bounded enumeration), `compute_grounding.py`, `construct_compute_*.py`,
  the OEIS chain. **This is where the real, reproducible, research-grade
  work is**, verified live three times in this audit. It is also the
  layer with the narrowest reach (22/1061 numbered, live).
- **(d) Proving** — `comprehend_theorem.py`'s ImplicationClause +
  self-verify-vs-known (§1.3). Real but scoped to one theorem family
  (group invariants over free products), not pytest-gated, demonstrated
  live with correct self-rejection of a malformed clause and honest MISS
  on six group properties it cannot express.

**These four are genuinely different capabilities, confirmed by reading
the code, and the "HLE-level" claim is true only of (c) and narrowly (d),
on a small hand-grown island of question-shapes.**

### 2.6 The MBPP-vs-math reconciliation, tested against the code (not asserted)

Grepped both directions:

```
grep "^from domains" domains/prog_synthesis.py   → code_writing, prog_ir_signature, prog_ir_emit, prog_retrieval
grep "comprehend_theorem|compute_grounding|oeis_local|math_capability_shapes" \
     domains/prog_synthesis.py scripts/prog_synthesis_battery.py \
     tests/test_program_synthesis_migrated.py tests/test_prog_synthesis_battery_migrated.py
   → (no matches, either direction)
grep "code_writing_cortex" scripts/prog_synthesis_battery.py domains/prog_synthesis.py
   → (no matches)
```

**Confirmed, not inferred: the MBPP synthesis pipeline imports nothing
from the math faculty, the theorem faculty, the OEIS chain, or the
math-shape bridge, in either direction.** All three candidate
explanations named in the brief are true simultaneously, and the code
confirms which is *load-bearing*:

1. **Different faculties entirely** — literally true, zero shared code.
2. **Derivation-from-structure vs. search-over-programs** — true and
   explains *why* they were never merged: `reason.py`'s interpreter
   answers a question by composing held primitives into ONE Term-tree and
   evaluating it (no search — the "search" is a small alternative-strategy
   list in `reconsider`, bounded and declared per-concept); `prog_synthesis
   .py` answers by proposing, evaluating, and rejecting many candidate IR
   terms against revealed rows (`br_10_top_of_three`'s 28,989-candidate
   enumeration in `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §4 is the
   diagnostic example). These are different *algorithms*, not just
   different code files.
3. **MBPP never invokes the math faculty** — **directly confirmed by
   grep**, not merely likely.

MBPP's ~10.9% (28/257, `PROGRAM_SYNTHESIS_ARC4_SUMMARY.md:185`) and math's
~1.9% raw / spike-of-rigor-on-a-curated-island are **not comparable
numbers for the same capability** — they are two different systems that
happen to share a repository and a CLAUDE.md.

---

## Part 3 — can the math faculty be aimed at the synthesis wall?

### 3.1 The wall, restated precisely from the source

`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §4 (read in full): task
`br_10_top_of_three` — spec "top of three" — has 3 revealed rows,
`(1,9,3)→9, (7,2,5)→7, (4,4,4)→4`, **all already satisfied by the decoy
`max(a,b)`** (argument `c` never read). Probed directly against the Rust
synth engine: excluding `max(a,b)` and exhaustively re-searching every
term of size ≤5 over the SAME 3 rows finds **nothing** (`halt_reason:
'max_size'`, an exhaustive negative, not a budget cutoff) — proving the
3 revealed rows are **information-theoretically insufficient** to
distinguish the decoy from the correct `max(a, max(b,c))`. The correct
program is only found once a 4th, genuinely discriminating row is
supplied externally. This is the exact "knowing something is wrong is
not knowing what is right" wall the brief names.

### 3.2 Can `comprehend_theorem` supply the constraint?

**No, not as built, and the gap is not a small parameterisation — it is a
different domain of discourse.** `comprehend_theorem`'s grammar
(`seeds/theorem_constructions.json`) parses statements of the shape
"[a group] with [property] has [invariant] = [value]" about **algebraic
objects** (groups, via `ground_reductions.KNOWN_OBJECTS`, free-product
structures). It has no construction for "a function of N arguments that
returns [an extremum/aggregate] is invariant under permutation of its
arguments" — that is a statement about a **program's I/O relation**, not
about a group-theoretic object. Nothing in `theorem_constructions.json`'s
6 statement forms, 10 property modifiers, or 4 invariant atoms addresses
functions, arguments, or permutation. Building this would mean authoring
an entirely new statement-form family, a new "invariant atom" for
function properties (symmetry/monotonicity/idempotence), and a new
grounding target (a predicate over a candidate program's evaluated output
under permuted argument bindings, rather than over a `KNOWN_OBJECTS`
group). The *mechanism* (parse → ground → emit-callable-predicate →
self-verify) is directly reusable in spirit; the *content* is not there.

### 3.3 Can `extract_function` + `compute_grounding` supply it?

**No — different shape of problem.** `extract_function`'s grammar targets
single-argument sequence definitions `a(n) = f(n)` (OEIS-style: sums/counts
over a filtered set indexed by one variable `n`). "Top of three" is a
3-argument function with no index variable and no summation/filter
structure to compose — it does not fit the member-form/value-map/
aggregator recursion at all. The vocabulary would need to be extended with
an entirely new construction family ("extremum of a fixed tuple of named
slots") that nothing in `math_prose_constructions.json` currently
expresses. **Not a near-miss; a different grammar would be needed.**

### 3.4 Do the math ShapeSignatures encode symmetry/monotonicity/recurrence usably?

**Structurally adjacent, operationally no.** The `symmetry` ShapeSignature
(§1.8) *does* encode "invariant under transform" as an abstract relation
schema — closer in spirit to what's needed than anything else in the math
stack — but it exists to let the analogy engine (`AntiUnify`) find that
"balance" and "self-similarity" share a skeleton with other cross-domain
concepts, not to check a candidate program's IR. There is no rule
anywhere in the seed corpus (confirmed by grep across
`seeds/program_synthesis.json` and `domains/prog_synthesis.py` for
`symmetric|permutation|extremum|commutative`: **zero matches**) that reads
this signature and turns it into a check against `synth_enumerate.rs`'s
candidate terms. The bridge is unbuilt.

### 3.5 What would have to be true — concrete missing pieces, in order of leverage

Named precisely, cross-checked against the existing (and directly
relevant) precedent — `domains/prog_synthesis.py`'s `compute_structural_
facts` (line 1249), which already gates `ps_accept` on three detectors
(D1 `memo_lookup_table`, D2 `dead_code_free_vars`, D3 `unread_declared_
param`) that inspect a **candidate's IR** and reject it pre-accept when
it can be proven defective (`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md`). This
detector-gates-`ps_accept` pattern is the right home for a new detector —
but a genuinely new piece is needed first:

1. **A spec-shape recognizer that reads the REQUEST TEXT, not the
   candidate.** D1/D2/D3 all inspect the *candidate's* IR. Nothing in the
   pipeline currently reads a structural property **out of the spec**
   ("top of three" → "this is an N-ary symmetric extremum over named
   slots a,b,c"). This is the single largest missing piece: a
   construction-grammar family (parallel to `comprehend_theorem`'s
   parse-ground-emit shape, but targeting function specs rather than
   group theorems) that mints a `RequiredProperty{kind:'permutation_
   invariant', args:[a,b,c]}` fact on the synthesis Goal from the
   ingested `request_text`.
2. **A new structural detector (call it D4) that checks a candidate
   against that `RequiredProperty`** — mechanically simple once (1)
   exists: re-evaluate the candidate's term on the SAME revealed rows
   with arguments permuted, and require identical output. This needs no
   new held-out data.
3. **A rule wiring D4's verdict into `ps_accept`/reopen**, exactly
   following the D1-D4 dominance and routing pattern S6 already built.

**A concrete check that this would actually work, run by this audit (not
an artifact — a derivation, shown so it can be checked):** the decoy
`max(a,b)` evaluated on the 3 *revealed* rows permuted — no new data
needed — already falsifies itself under a permutation-invariance
requirement: row `(1,9,3)→9` permuted to `(1,3,9)` must also →9 (since
`top_of_three` is symmetric), but `max(a,b)` on `(a,b,c)=(1,3,9)` gives
`max(1,3)=3 ≠ 9`. **The permutation check catches the decoy using only
the 3 rows already revealed — it does not need the external 4th
counterexample row `run_task_p7` currently withholds until after
acceptance.** This directly validates the brief's structural conjecture
in this one case: structure (symmetry, once recognised) supplies the
missing constraint where row-data is exhausted. It is *not currently
built* — item (1) above is the blocker, and the run-permuted-rows check
in (2) does not exist in `domains/prog_synthesis.py` today (grep
confirms no `permut` token anywhere in the Python or Rust synthesis
code).

### 3.6 Honest limits of this conjecture

- It only helps for specs whose correctness condition **is** a checkable
  structural property (symmetry, monotonicity, idempotence, a stated
  recurrence). Many MBPP tasks have no such closed-form structural
  signature — the S0 null already measured in
  `PROGRAM_SYNTHESIS_ARC4_SUMMARY.md` ("MBPP's flat single-return
  solutions don't [carry such structure]") suggests the addressable
  fraction of the 257-task population may be small; this audit did not
  measure how many MBPP specs are extremum/symmetric-shaped.
  **Un-quantified — flagged, not estimated.**
  

- Building (1) is exactly as much new-construction-grammar work as
  `comprehend_theorem` or `extract_function` already represent (each
  took a dedicated module + seed family) — it is a real feature, not a
  wiring exercise.

---

## Evidence-grade summary table

| Capability | Module(s) | a/b/c/d | Grade | Live-reproduced this audit |
|---|---|---|---|---|
| 117 prose math concepts | `seeds/mathematics.json` | (a) | [B] | test_mathematics.py run, 18/18 green (name-existence only) |
| Analogy shape signatures | `seeds/math_capability_shapes.json` | (b) | [B] | not exercised beyond load |
| Invariant-type recognition | `presupposition_derivation.py` | (b) | [A] | yes — 55/1061 typed, in the full sweep |
| Term-tree math interpreter | `domains/reason.py` | (c) | [A] | yes — via OEIS chain + Aztec conviction |
| OEIS prose→formula→verify | `construction_grammar.extract_function`, `oeis_local.py` | (c) | [A] | yes — 8/8 live |
| Bounded exact enumeration | `domains/construct_compute_*.py` | (c) | [A] (per exercised family) | yes — Aztec conviction live |
| Theorem statement → checkable implication | `domains/comprehend_theorem.py` | (d), narrow | [C]→confirmed live, no pytest gate | yes — demo script run live |
| Prose→object recognition (analysis-by-synthesis) | `domains/math_hat.py` | (b)/(c) | [C] | not run |
| Full-bank HLE math sweep | `scripts/retest_hle_math_cumulative.py` | measurement | [A] | yes — 22/1061 numbered, 20 correct |
| MBPP synthesis engine | `domains/prog_synthesis.py` | separate system | [B] (per `PROGRAM_SYNTHESIS_ARC4_*` docs) | not re-run (out of scope; number cited from source docs) |

---

## Files referenced (all paths relative to repo root)

- `HLE_KEY_AUDIT.md` — the certified-conviction dossier (43/36/5/0).
- `data/hle_math.json` (n=1061), `data/hle_nonmath.json` (n=1309).
- `domains/reason.py`, `domains/comprehend_theorem.py`,
  `domains/ground_reductions.py`, `domains/compute_grounding.py`,
  `domains/construction_grammar.py` (`extract_function`,
  `comprehend_recursive`), `domains/oeis_local.py`, `domains/oeis_
  reference.py`, `domains/hle_world.py`, `domains/math_hat.py`,
  `domains/code_writing_cortex.py`.
- `domains/construct_compute_enumerations.py` (+ 8 sibling
  `construct_compute_*.py` modules).
- `seeds/mathematics.json`, `seeds/math_foundations.json`,
  `seeds/logic_mathematical.json`, `seeds/mathematics_microtheory.json`,
  `seeds/math_capability_shapes.json`, `seeds/theorem_constructions.json`,
  `seeds/theorem_core.json`, `seeds/math_prose_constructions.json`.
- `scripts/oeis_extract_verify.py`,
  `scripts/hle_conviction_aztec_dominoes.py`,
  `scripts/hle_conviction_boolean_exprs.py`,
  `scripts/retest_hle_math_cumulative.py`,
  `scripts/probe_fresh_hle_unassisted.py`,
  `scripts/comprehend_theorem_demo.py`.
- `tests/test_mathematics.py`, `tests/test_theorems_as_terms_migrated.py`.
- `domains/prog_synthesis.py`, `seeds/program_synthesis.json`,
  `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md`, `PROGRAM_SYNTHESIS_ARC4_SUMMARY.md`.

## Commands run live under this audit (for re-verification)

```bash
cd research/experiments/gamma-substrate
export PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1
python3 scripts/oeis_extract_verify.py                 # 8/8, reproduced above
python3 scripts/retest_hle_math_cumulative.py           # 22/1061 numbered, 20 correct, reproduced above
python3 scripts/hle_conviction_aztec_dominoes.py        # CONVICT (8 vs key 6), reproduced above
python3 scripts/comprehend_theorem_demo.py              # self-verify PASSED / self-reject correct, reproduced above
python3 -m pytest --confcutdir=. tests/test_theorems_as_terms_migrated.py tests/test_mathematics.py -q   # 18 passed
```
