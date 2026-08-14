# Question-driver solver dispatch — Rung 3 (`ProblemShape` codebook) — PREREG

Base `main @ c4c781f` ("Merge qd-solver-rung2: solve_* failures self-file as
gaps, GO"), verified via `git log --oneline -1 main` before writing this
document. Worktree: `/home/matt/ozmadev/ocelot-worktrees/qd-solver-rung3`,
branch `qd-solver-rung3`. `data/` was absent in the fresh worktree (not a
partial real directory); symlinked and confirmed `data/wiktionary/en.jsonl.gz`
resolves to the real 492,560,156-byte file.

This document implements §6.3 of
`docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`
("Rung 3 — the `ProblemShape` recognizer... large, genuinely uncertain, defer
to its own prereg... it needs real observed cases"), now that Rung 1
(`QUESTION_DRIVER_RUNG1_RESULTS.md`, seven `solve_*` resolvers) and Rung 2
(`QUESTION_DRIVER_RUNG2_RESULTS.md`, `note_solve_exhausted_gap`) are both
merged to `main` and have produced real test populations to draw from. It
does not re-derive Rung 1/2's own design; see those documents for the
dispatch mechanism and gap-filing this document builds on top of, unedited.

---

## 1. Data-sufficiency investigation (the task's own first question)

### 1.1 The real population, counted directly from the two rungs' own test files

Every `mint_solve_*_goal` call site in `tests/test_solver_dispatch_migrated.py`
and `tests/test_solve_gap_awareness_migrated.py` was enumerated by direct
read (not grepped and assumed) — see the parent chat transcript for the
line-by-line count; totals:

| `kind` | real instances (both test files) | representative statements/targets |
|---|---|---|
| `solve_deduction` | **10** | `"if X is a fish, X can swim"`, `"All philosophers are mortal"` (universal), `"Some bird is a penguin"` (existential), `"purple elephants dream sideways"` (×2, honest wall), `"if X is a fish, X is aquatic"`, `"if X is a mammal, X is warm blooded"`, `"if X is a cat, X can purr"`, `"if X is a cat, X is furry"`, `"if X is a dog, X can bark"` |
| `solve_can_relax` / `solve_can_exact` / `solve_can_bp` | **5** | a real Bigville resident CAN belief network (`worlds/bigville_can_beliefs.py`), targeted via `targets_mt`, at `k_starts=1`, `k_starts=5`, exact (×2, one a genuine too-tight-bound wall), loopy BP |
| `solve_decompose` | **2** | two real coupling-graph candidate races over real `knowledge_logical` schemas (`project_deduction_shared_attr`/`project_deduction_complete`), one succeeding at `bound=1`, one genuinely intractable at `bound=0` |
| `solve_reasoning_bridge` (`can_to_deduction`) | **1** | real CAN state → deduction predications |
| `solve_analogical_promote` | **1** | a real `DirectionalCorrespondence` promoted to a `knowledge_logical` schema |

**19 real dispatch instances total**, zero synthetic/fabricated cases —
every one is a live toolbox call against real Bigville data or real minted
schemas, per Rung 1/2's own no-stubs discipline.

### 1.2 What is genuinely NOT in this population — named precisely, not glossed

Every one of the 19 instances above was minted by a TEST AUTHOR who already
knew which `kind` to mint — `mint_solve_deduction_goal(agent, statement)` is
called because the test already decided "this is a deduction case." **There
is no real corpus, anywhere in this codebase today, of a genuinely raw,
unclassified problem being routed by a recognizer rather than by caller
choice.** This is not a gap this rung can close by minting harder — it is a
fact about what data exists. Building a "raw NL problem → auto-decide
kind → mint the right Goal" pipeline now would mean inventing the raw-problem
corpus from scratch, which is exactly the "hypothesised taxonomy... not
grounded in real observed cases" risk the Rung 1 prereg (§2.3) warned against
and the Rung 3 sizing note (§6.3) named as the reason to wait.

### 1.3 What IS real and gradable, found by reading `domains/solver_dispatch.py`
   directly (not inferred)

Every `mint_solve_*_goal` function writes a DIFFERENT, mutually exclusive set
of graph-visible facts onto the Goal it mints, independent of the Goal's own
`kind` string (`domains/solver_dispatch.py:136-233`, read in full):

| kind | `statement` attr | `targets_mt` edge | `targets_correspondence` edge | `direction` attr | `bound` attr |
|---|:-:|:-:|:-:|:-:|:-:|
| `solve_deduction` | **yes** | no | no | no | no |
| `solve_can_relax`/`solve_can_exact`/`solve_can_bp` | no | **yes** | no | no | no |
| `solve_reasoning_bridge` (`can_to_deduction`) | no | yes | no | **`"can_to_deduction"`** | no |
| `solve_reasoning_bridge` (`deduction_to_can`) | no | no | no | **`"deduction_to_can"`** | no |
| `solve_analogical_promote` | no | no | **yes** | no | no |
| `solve_decompose` | no | no | no | no | **yes** |

This is a real, already-present, structurally discriminating signal — not
invented for this document. **This is the actual grounding fact this rung
builds on**: a `ProblemShape`'s signature does not need to guess at an
unclassified raw problem's meaning (no data exists for that); it can be
extracted, mechanically, from what a solve_* Goal's own attrs/edges already
record about the artifact it targets — exactly the same category of
extraction `_ingest_target`'s `op`/`params`/`concept` writes already are
(CLAUDE.md's own "mechanical extraction of structural attrs... is PURE
EXTRACTION, legitimate" carve-out, quoted at
`QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md` §5.2).

### 1.4 The verdict: GO, for a *retrospective structural recognizer*, NOT for
   a pre-mint auto-dispatcher

Reading the population honestly: **19 real instances, discriminated into 3
clearly-recurring groups (deduction: 10, CAN: 5, decompose: 2) plus 2 genuine
singletons (reasoning-bridge-can_to_deduction: 1, analogical-promote: 1) by a
real structural signal already present on real Goals.** This is comparable
in scale to `META_SHAPE_FIRST_CLASS_RESULTS.md`'s own growth-loop
demonstration (which minted from as few as 2-3 real observations, support=2
being "the smallest cardinality at which 'recurs' is defined, not a swept
knob" — §4.1 there) and is a real, non-fabricated population, not a
hypothesised taxonomy.

**What is NOT yet grounded, and what this document does NOT attempt to
build**: a pre-mint recognizer that decides `kind` for a genuinely raw,
unclassified problem BEFORE any `solve_*` Goal exists. §1.2 already
established no real corpus of that shape exists. Building it now would mean
either (a) fabricating synthetic "raw problem" cases (forbidden by this
task's own instruction and by the standing house discipline every prior
rung this session has followed), or (b) reaching back into
`comprehend_question.py` to add new solve-kind branches — explicitly
rejected by the Rung 1 prereg §5.3 as "a fresh violation dressed as
consistency."

**Therefore: GO on the smallest real slice — a `ProblemShape` codebook that
recognizes the STRUCTURAL SHAPE of an already-minted `solve_*` Goal from its
own real attrs/edges (never from its `kind` string, which would be
circular), with mint-on-residual demonstrated live on the real recurring
`solve_decompose` population, and genuine non-mint on the real singleton
cases. The pre-mint auto-dispatch layer (deciding kind for a raw problem
before it exists as a Goal) is named as an explicit follow-on (§5 below),
deferred until a real raw-problem corpus exists to ground it — not designed
here from hypothesis.**

This mirrors the task's own explicit permission: *"build the SMALLEST real,
demonstrable first slice... WITHOUT the hold-open multi-candidate layer if
that proves too large for one rung."* The hold-open/multi-candidate layer
(§2 of the task) is deferred for the same reason: with no genuine input
ambiguity in the real population (every real Goal's structural facts point
at exactly one shape, unambiguously — see §1.3's table, whose rows are
mutually exclusive by construction of `mint_solve_*_goal`'s own attr/edge
choices), there is no real case demonstrating two candidates GENUINELY
competing for one problem. Building the hold-open collapse-on-confidence
machinery against zero real competing-candidate cases would be exactly the
same "codebook from hypothesis" risk this section exists to avoid.

---

## 2. `ProblemShape`'s signature — grounded in §1.3, not invented

### 2.1 Vocabulary (five axes, fixed order, each an existing real fact)

Following `_pair_witness`/`_concept_shape_vector`'s idiom
(`domains/analogical_thinking.py:430-457`, read in full): a signature is a
sorted list of `[predicate, value]` pairs, one `is_a` type tag plus one
relation per axis, absence marked by a fixed sentinel (mirroring `_ABSENT`)
rather than the relation being omitted — so every signature has the SAME
arity, which is what lets `AntiUnify`/`FixedCount`/literal `ShapeDecode`
treat them uniformly (`analogical_thinking.py:439-442`'s own stated reason
for fixed arity).

| axis (relation predicate) | source fact (from §1.3's table) |
|---|---|
| `has_statement` | Goal carries a `statement` attr (`solve_deduction`) |
| `has_targets_mt` | Goal carries a `targets_mt` edge (CAN kinds, `reasoning_bridge` can_to_deduction) |
| `has_targets_correspondence` | Goal carries a `targets_correspondence` edge (`solve_analogical_promote`) |
| `has_direction` | Goal carries a `direction` attr, VALUE preserved (not just presence) — `solve_reasoning_bridge`'s two directions are real, distinct problem shapes, not one |
| `has_bound` | Goal carries a `bound` attr (`solve_decompose`) |

`is_a: "problem"` is the fixed type tag (mirrors `meta_shape.py::item_signature`'s
own `is_a` relation).

### 2.2 Extraction is mechanical, not a decision — the `_ingest_target` carve-out

`domains/problem_shape.py::goal_signature(sub, goal_node)` reads exactly
these five facts off the Goal node's own attrs and edges (`sub.node(...)`,
`native.neighbours(goal, "targets_mt")`, etc.) and returns the fixed-arity
relation list. **No branch decides what KIND the problem is** — this differs
from a `comprehend_question.py` classifier in exactly the way CLAUDE.md's
carve-out requires: it converts an opaque external form (the Goal's own
already-written attrs/edges) into the smallest graph token (a signature
relation), and does not choose between competing interpretations. The
`kind` attr itself is DELIBERATELY EXCLUDED from the signature — including
it would make recognition trivially circular (the Goal already says what it
is; a recognizer that reads `kind` back out is not doing structural
recognition, and would give the WRONG answer once the pre-mint auto-dispatch
follow-on (§5) exists, at which point no `kind` would be set yet).

### 2.3 The three real shapes: two seeded (support ≥5 each), one grown live

`deduction_shape` (`has_statement:"yes"`, all other axes `_ABSENT`) and
`can_shape` (`has_targets_mt:"yes"`, all other axes `_ABSENT`) are seeded
directly in `seeds/problem_shape_growth.json`, mirroring how
`shape_vocabulary.json` seeds the eleven known `MetaShape` entries — a
DIFFERENT precedent from meta-shape's mint (which grows from residual
because it had NO seeded signature-bearing entries at all): here, both
seeded entries are grounded in ≥5 real recurring instances each (§1.1),
comparable to or larger than the meta-shape rung's own curated
demonstration set (10 cases). `decompose_shape` (`has_bound:"yes"`, all
other axes `_ABSENT`) is DELIBERATELY NOT seeded — it is left to mint live
from its own real recurring population (2 real decompose instances, exactly
meeting the house's own established support=2 floor), so this rung
demonstrates BOTH halves of the sd-loop discipline: recognizing an
already-known shape (rung 1) and growing a new one from real recurrence
(rung 4), on real data, not by assertion.

---

## 3. `ProblemShape` as its own node type — the Q2 finding applied directly

Per `QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md` §2.2 (confirmed there by
direct read of `runners/dsl/src/shape_decode.rs::load_parts`, re-confirmed
here, not re-litigated): `kind` does not partition the live `ShapeDecode`
pool — `load_parts` loads every node carrying `name`+`signature` under
whatever `codebook_type` a Term names, regardless of any `kind` attr on the
node. Tagging `ProblemShape` entries as `ShapeSignature{kind:"problem_shape"}`
would silently enter the SAME decode pool `inference_generation.
resolve_implication_gap` and `math_capability_shapes.json` already
populate, competing for a live decode slot the moment a signature happened
to match. **`ProblemShape` is therefore a genuinely new node type**, mirroring
the `DirectionalCorrespondence` precedent (`analogical_thinking.py:672-687`)
exactly: `ShapeDecode`/`TransformDecode`/`DimInfer` are pointed at
`codebook_type: "ProblemShape"`, which `load_parts`'s grain-agnostic read
(confirmed at the Rust source, and independently re-confirmed by
`META_SHAPE_FIRST_CLASS_RESULTS.md` §3 for `codebook_type:"MetaShape"`)
serves with **zero new Rust**.

New node types: `ProblemShape{name, signature, support, minted, source}`
(field names mirror `MetaShape` exactly) and `ProblemShapeObservation
{signature, status, key, source_goal}` (mirrors `ShapeObservation`). New
edge types (Γ productions, declared not omitted — per CLAUDE.md's own
"SHAPES, NOT NUMBERS" finding that 454/634 manifests wrongly ship
`"productions": []`): `Agent -observed_problem-> ProblemShapeObservation`,
`ProblemShapeObservation -minted_problem_shape-> ProblemShape`,
`ProblemShapeObservation -about_goal-> Goal` (the real solve_* Goal this
observation was extracted from — for traceability, mirroring
`gap_awareness.json`'s own `sc -about_goal-> g` edge).

---

## 4. The recognizer as a direct `ShapeDecode` extension — no bespoke classifier

### 4.1 Rung 1 only — rungs 2/3 named as a graceful, honest no-op (mirroring
   the meta-shape precedent's own rung 3)

`seeds/problem_shape_growth.json` wires exactly `ps_decode`/`ps_recognize`
(rung 1: literal `ShapeDecode`, `wild_objects:false`, verdict = `Count(residual)
== 0`, mirroring `shape_decode_loop.json::sd_decode`/`sd_recognize`'s own
SIMPLER literal-cover shape — not `meta_shape_growth.json`'s `Covers`-based
rung 1, because `META_SHAPE_FIRST_CLASS_RESULTS.md` §3b's own reason for
needing `Covers` (a WILD-bearing anti-unified lgg pattern in the codebook)
does not apply here: every `ProblemShape` signature in this rung, seeded or
minted, is fully concrete — no WILD anywhere, confirmed in §2.3/§6 below).
Rungs 2 (`TransformDecode`) and 3 (`DimInfer`) are NOT wired this rung, for
the SAME reason `META_SHAPE_FIRST_CLASS_RESULTS.md` §3 names its own rung 3
a graceful no-op: every axis here is a categorical presence/value string
(`"yes"`/a direction literal/`_ABSENT`), never an integer coordinate —
`DimInfer`'s generators (rotation90/reflections/scale2/modular) have
nothing to act on, and a "transform" of a presence-relation is not a
meaningful concept at this grain (there is no consistent per-dimension
delta between "has a statement" and "has a targets_mt edge" — they are
different FACTS, not the same fact shifted). Named here as an explicit,
deliberate scope cut, not an oversight — a genuine future need (e.g. a
numeric-valued axis, such as a treewidth-bound threshold) would light these
rungs up for free, exactly as the meta-shape precedent's own note says.

### 4.2 Mint (rung 4) via existing Terms only — no `ProblemShapeMint` Rust Term

`META_SHAPE_FIRST_CLASS_RESULTS.md` built a bespoke `MetaShapeMint` Rust Term
because its own recurrence-grouping needed predicate-SET equality (order-
independent, arity-independent) over signatures that could differ in which
predicates were present. This rung's minted candidate (`decompose_shape`)
does not need that: **every real `solve_decompose` observation in the corpus
produces the IDENTICAL literal signature** (`has_bound:"yes"`, all other
axes `_ABSENT` — confirmed directly from §1.3's table, since
`mint_solve_decompose_goal` never writes `statement`/`targets_mt`/
`targets_correspondence`/`direction`). Recurrence is therefore exact
signature/`key` equality, expressible with the SAME `Eq`/`Exists`/`Argmin`
idiom `retire_duplicate_gap` already uses for its own canonical-survivor
pick (`seeds/gap_awareness.json`, read in full at
`QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md` §4.3's own citation) — no
`AntiUnifyWitness` generalisation is even needed, because anti-unifying two
IDENTICAL relation sets returns the same relation set unchanged, so minting
directly from the observation's own signature is correct and simpler. **Zero
new Rust Term variants.** A key string (`obs.key`, a deterministic function
of the signature computed in `domains/problem_shape.py`, mirroring
`sd_mint_quantum`'s own `capability_keys` idiom exactly — "mechanical,
stable... set... from the observation's own predicate structure") stands in
for `MetaShapeMint`'s `name`/`field` outputs.

`ps_mint`'s guard: `status=="residual"` (i.e. rung 1 did not recognize it)
AND at least 2 observations (this one plus another) share the same `key`
AND this observation is the group's canonical minter (`Eq(Var(obs),
Argmin(Filter(NodesOfType(ProblemShapeObservation), same key AND
status=="residual"), value=Var(z)))` — the exact `retire_duplicate_gap`
idiom) AND no `ProblemShape` already carries this `key` as its `name`
(mint-once guard). Effects: `add_node ProblemShape{name:obs.key,
signature:obs.signature, support:<count>, minted:1}`, edge
`obs -minted_problem_shape-> ps`, `status:"minted"`, bump
`ag.problem_codebook_epoch` (the `Plus` idiom, exact copy of
`msg_mint_shape`'s own effect).

### 4.3 `ps_redecode` closes the loop

Any `recognized`/`minted`/`residual` observation decoded under an older
`problem_codebook_epoch` re-arms to `pending`, mirroring `sd_redecode`/
`msg_redecode` exactly (minus the transform/dim flag resets, since those
rungs are not wired here — §4.1).

---

## 5. The hold-open/confidence layer and pre-mint auto-dispatch — deferred,
   named precisely

Per §1.4's data-sufficiency verdict: **not built this rung.** Two genuinely
separable follow-ons, sized honestly:

- **Rung 3.5 — wire the recognizer INTO the mint path.** Once a real raw-
  problem corpus exists (e.g. once a future adapter surfaces genuinely
  unclassified problems — a question-answering path that does not already
  know which toolbox facility applies), `ps_decode`/`ps_recognize` could run
  BEFORE `mint_solve_*_goal` is called, informing (not yet deciding) which
  kind to mint. Blocked on: a real corpus of that shape, which does not
  exist today (§1.2).
- **Rung 4 — the hold-open multi-candidate layer.** Representing several
  concurrently-plausible `solve_*` kinds for one incoming problem (multiple
  candidate edges with confidence scores, collapsing via a Rule once one
  dominates — mirroring the SEER hold-open criterion CLAUDE.md's "SHAPE IS
  ACQUISITION" section already names: *"hold open is right only when there
  is genuinely no fact of the matter yet decidable, and wrong... otherwise"*).
  Blocked on: a real case where two candidate shapes GENUINELY compete for
  one real problem — none exists in the current 19-instance population
  (§1.3's table rows are mutually exclusive by construction). Building this
  against zero real competing-candidate cases would be building a hold-open
  mechanism with nothing to hold open — the same "codebook from hypothesis"
  risk register.

---

## 6. Live demonstration plan (registered before code, per house discipline)

`tests/test_problem_shape_migrated.py`, against the same
`WorldAdapter(seeds=()) + load_all_seeds` boot fixture Rung 1/2's own test
files use (real toolbox calls throughout, no stubs):

1. Mint a real `solve_deduction` Goal (`"if X is a fish, X can swim"`, the
   SAME statement Rung 1's own test uses), observe it, run rules, assert
   `status=="recognized"` and `covered_by=="deduction_shape"`.
2. Mint a real `solve_can_exact` Goal over the real Bigville CAN network
   (same fixture Rung 1/2 already use), observe it, assert `status==
   "recognized"` and `covered_by=="can_shape"`.
3. Mint two real `solve_decompose` Goals (mirroring Rung 2's own two real
   decompose cases — one attempted-success, one genuinely intractable),
   observe both: first stays `"residual"` (support=1, no recurrence yet);
   second recurrence triggers `ps_mint` — assert exactly ONE `ProblemShape`
   named `decompose_shape`'s key is minted (not two), `problem_codebook_epoch`
   bumps, and the FIRST observation re-decodes (`ps_redecode`) to
   `"recognized"` against the newly minted entry — the exact recognize →
   residual → recurrence → mint → re-decode → recognized loop
   `META_SHAPE_FIRST_CLASS_RESULTS.md` §4 demonstrated, on real data.
4. Mint a real `solve_reasoning_bridge` (`can_to_deduction`) Goal (the SAME
   real CAN-to-deduction case Rung 1's own test uses) and a real
   `solve_analogical_promote` Goal — both genuine singletons (§1.3): assert
   BOTH stay `status=="residual"` (not force-matched into `can_shape`/
   anything else, and not minted, since support=1 for each) — the
   discriminating "does not fabricate a match" proof.
5. A negative/discrimination check: assert `deduction_shape`'s signature does
   NOT fully cover the CAN observation's signature and vice versa (residual
   non-empty both ways) — the structural discrimination claim, checked
   directly, not merely inferred from the status field.

---

## 7. What this document does NOT establish (registered in advance)

1. **No pre-mint auto-dispatch.** §5 names it, does not build it — blocked
   on a real raw-problem corpus this codebase does not yet have.
2. **No hold-open/multi-candidate layer.** §5 names it, does not build it —
   blocked on a real case of genuine competing candidates, which the
   current 19-instance population does not contain.
3. **Rungs 2/3 of the sd ladder (`TransformDecode`/`DimInfer`) are not
   wired at this grain.** §4.1 explains why (categorical axes, no
   meaningful per-dimension delta) — a graceful, deliberate no-op, not an
   oversight, mirroring the meta-shape precedent's own rung 3.
4. **The five-axis vocabulary (§2.1) is grounded in the CURRENT seven
   `solve_*` resolvers only.** An eighth toolbox facility with a genuinely
   new attr/edge shape would need a sixth axis — not designed here,
   flagged as the natural place this codebook grows next (via its own
   recognize/residual/mint loop, not by hand-editing the axis list).
5. **`decompose_shape`'s support=2 threshold is the same un-validated
   choice `META_SHAPE_FIRST_CLASS_RESULTS.md` §4.1 already named** ("the
   smallest cardinality at which 'recurs' is defined... not swept against
   real taught data") — inherited, not re-litigated or re-justified here.
6. **No code, seed JSON, or tests exist yet at the time this document is
   registered.** This is the checkpoint written before implementation, per
   house discipline.
