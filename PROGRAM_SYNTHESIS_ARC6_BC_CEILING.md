# ARC 6 — SEAMS B AND C, THE TWO REMAINING M0 CEILINGS, MEASURED

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC6_PLAN.md` §1 (Seams B
and C) and §3 (M0), and to `PROGRAM_SYNTHESIS_ARC6_A_CEILING.md`, whose
honest-vs-cherry-picked discipline is reproduced here for both ceilings.
Completes M0's four probes (A and D landed earlier today).

**Status: MEASUREMENT. Nothing was built.** No file under `seeds/`, `runners/`,
`domains/`, `substrate/` or any adapter was modified or read-for-edit. No
`git add`/`commit`/`stash`. Artefacts created: `scripts/arc6_bc_ceiling.py`,
`results/arc6_bc_ceiling.json`, this document.

**Engine provenance** — part of a measurement's identity, not a footnote.
`engine_preamble()` is called before `substrate_rs` is importable, and the
stamp is written into the artifact:

> `engine 5c1b472fe674 @ …/program-synthesis-plan/…/runners/dsl/python/substrate_rs/_native.abi3.so`
> `source_match = own`, `[1 other tree build shadowed]`

The canonical tree's `.so` is a **different binary** (`7dd9af13a038…`), and the
`.pth` resolves there by default. Every number below is from `5c1b472f…`.

**Determinism.** The script computes the full result twice per invocation and
asserts a SHA-256 match; two independent full runs were byte-identical modulo
the timestamp. `id_hash = 48270ea65125159a`.

**Input state.** Every input file was verified byte-identical to committed HEAD
(`f93dc5e5f5`) *before and after* the run — `construction_grammar.py`,
`compute_grounding.py`, `reason.py`, `mbpp_spec.py`,
`math_prose_constructions.json`, `math_capability_shapes.json`,
`shape_vocabulary.json`, `sanitized-mbpp.json`. Their sha256s are in the
artifact (`input_file_sha256`). *A separate worktree was deliberately NOT used:
the engine `.so` is gitignored, so a fresh worktree would have had to rebuild
Rust or silently borrow the canonical binary — the exact hazard being guarded
against. Hashing the inputs at HEAD gives the same guarantee at no risk.*

**Contamination.** MBPP test-split `code` is never read by the driver at all
(`q0_split_tasks` strips it; it was read once, by hand, only to check five
in-language matches during analysis, and is quoted nowhere in any vocabulary).
Prompt text and example rows are used for VERIFICATION ONLY; nothing enters a
codebook, cue vocabulary, or taught shape. Ceiling C's three keyword variants
are derived **mechanically from the seed file** and are printed in full in the
artifact so this can be checked rather than trusted.

---

## 0. The one-paragraph answer

**Seam B:** `extract_function`'s grammar is not narrow — it is *finite and
tiny*. Its complete language is **39 distinct functions**, enumerated
exhaustively here and every one of them run. Against the 257 MBPP test prompts:
**0 tasks parse-and-verify today**, **1 (`96`) after a blind mechanical
retarget**, **3 (`96, 295, 453`) after two blind seed additions**, and **4
(`+89`) is the absolute language ceiling** — the most any retargeting of any
kind could reach, because the other 253 tasks compute functions the grammar
cannot express at all. A cue-word cherry-pick would report **83**, and the
reductio reports **257**. The dominant fact is structural and bounds
everything: **only 39 of 257 tasks even have the `f(int) -> int` signature the
grammar's output form can hold; 218 (85%) are excluded before semantics is
consulted.**

**Seam C: NULL — the sixth content null, and it should be recorded as cleanly
as a win.** **0 genuine recognitions out of 252 hits**, across three keyword
variants and one literal load, with a positive control proving the instrument
fires. The codebook holds **6** `ShapeSignature{kind:"math"}` (not 17 — the
plan's figure is wrong and the earlier correction to 6 is independently
confirmed), it carries **no `MetaShape` node, no `keywords` field and no
edges**, so `RecogniseShape` recognises **0/257** when the file is loaded as it
actually is. Even the deliberately cherry-picked reading — hand-authored
algorithmic keywords, audited by hand — yields **1** genuinely-shaped task
(`100`, palindrome = invariance under reversal), which no variant fires on and
which the codebook could not act on anyway: its nodes carry
`name/kind/concept/faculty/signature` and **no payload of any kind**.

---

## 1. Null conditions, stated before M2/M3 is built

Fixed here so the answers cannot be renegotiated once a build exists.

**Seam B is a null if any of these hold.**

1. **The blind-retarget ceiling does not survive the pipeline.** Exactly one id
   (`96`) converts under a retarget nobody had to author per-task. If a built
   M2 does not convert `96`, retargeting `extract_function` to hub IR converts
   nothing at all.
2. **The conversions arrive only via authored vocabulary.** If M2's grammar
   diff cannot be written from §5's two named additions alone — if it needs a
   construction whose *only* consumer is one task — the number produced is the
   83 or the 257, not the 3.
3. **A conversion has no constructed witness.** Task `224` is already on the
   record as a row-matching formula that is wrong on 40 of 60 sweep points.
4. **The parser reaches nothing the language does not.** The language ceiling
   is 4; if a built M2 reports more than 4 conversions, the extra ones did not
   come from this grammar and are mis-attributed.

**Seam C is a null if — and it already is.** Registered in advance in the
plan's own §2 ("If HM3 nulls, the acquisition line ends with the proposal
line"): a non-zero **genuine** recognition rate was the bar. Measured: **0**.
Three further conditions, all also met, are recorded so the null is
un-renegotiable: the mechanism does not read the file (0 `MetaShape` nodes);
the hits that exist are substring collisions (252/252); and a hit would carry
no payload even if genuine (no constraint, no relaxation, no IR template).

---

## 2. CEILING B — what the grammar can actually read, and what it can mean

### 2.1 The vocabulary, verified against the source

The plan quotes "10 clauses, 5 member forms, 4 aggregators, 4 filters."
**Read directly from `seeds/math_prose_constructions.json`: all four numbers
are correct.** Two things the plan does not say, both material:

| family | raw entries | **distinct semantics** | note |
|---|---|---|---|
| clauses | 10 | **7** | `sum of divisors`/`sum of the divisors` are one formula; so are `positive`/`natural integers` and `factorial numbers`/`factorial of n` |
| member forms | 5 | **2** | `divisors of n` (pred `k|n`) and everything-else (pred `1`) — `integers`/`the integers`/`numbers` are the *same* form |
| value maps | 2 | **1** | `squares_of` only; `cubes_of` is deliberately unseeded (`_doc_no_cubes`) |
| filters | 4 | **3** | `less_than_n`/`smaller_than_n` are one mask `(k<n)` |
| aggregators | 4 | **2** | `sum` and `count` |
| operators | 27 | **0 usable** | **every one carries `held_runnable: false`** — verified, not quoted |

`_ACQUIRED` is empty at import, so nothing is silently widening the grammar.

### 2.2 The complete language — enumerated, not estimated

The grammar is finite, so it was enumerated: every
`aggregator × [value-map] × [pre-filter] × member-form × [post-filter]`
surface plus the 10 flat clause surfaces = **550 sentences**. Each was fed
through the **real** `extract_function`; **all 550 parse** (a self-check that
this enumeration *is* the language and not a reconstruction of it). They emit
**47 distinct formulas**, which ground and evaluate to **39 distinct
functions** (deduplicated by their value signature over n = 1..24; the full
list is in the artifact).

Thirty-nine functions. That is the whole reach of the compositional and flat
routes. The third route — the embedded-`=` arithmetic segment — is the only
unbounded one, and **3 of 257 prompts contain an `=` at all** (`160, 162, 392`),
of which 2 have an arithmetic-looking RHS.

### 2.3 The structural gate, stated first because it bounds everything

The grammar emits a unary function of an integer index. **Only 39 of the 257
test tasks have that signature shape** (every example row: one non-bool int in,
one non-bool int out):

`17, 59, 67, 80, 84, 86, 89, 96, 100, 123, 135, 162, 167, 171, 224, 234, 235,
244, 256, 260, 264, 266, 267, 268, 271, 274, 279, 287, 295, 311, 388, 389, 392,
420, 435, 441, 448, 453, 479`

**218/257 (85%) are excluded by signature shape alone** — lists, strings,
tuples, dicts, multi-argument. This is the same shape of finding as the
A-ceiling's 42/53 structural block, arrived at independently: *the population,
not the instrument, is what bounds this seam.*

### 2.4 The ladder — honest and cherry-picked, side by side

| level | n | ids | what it means |
|---|---|---|---|
| **0 — parses today AND verified** | **0** | — | 3 prompts return a non-empty parse (`160, 267, 270`); **all 3 are wrong**, verified by executing the extracted formula on the task's own rows (e.g. 267 yields `n*n` → `[4,9,16]` vs expected `[10,35,84]`) |
| **1 — after a BLIND mechanical retarget, verified** | **1** | `96` | boilerplate strip + argument-phrase → `n`, with two grammar-derived guards; the whole rule is 11 phrases and is printed in the artifact |
| **1b — after TWO blind seed additions, verified** | **3** | `96, 295, 453` | see §5; each addition nameable without reading any task's answer |
| **2 — LANGUAGE ceiling, row-matched** | **5** | `89, 96, 224, 295, 453` | some sentence of the 39 reproduces **every** example row |
| **2b — LANGUAGE ceiling, witness-verified** | **4** | `89, 96, 295, 453` | `224` **refuted**: it diverges from popcount at **40 of 60** sweep points |
| **2c — witness-verified AND conceptually matching** | **3** | `96, 295, 453` | `89` is extensionally exact but conceptually unrelated (§4) |
| **3 — CHERRY-PICKED, cue word in the prompt** | **83** | (full list in the artifact) | "sum of"/"number of"/"divisors"/… appears in the prose |
| **4 — CHERRY-PICKED, reductio** | **257** | all | add one clause per task: `{clause: <the prompt>, formula: <its answer>}` — the grammar is a JSON list, so this is one line each |

**The inflation is 1 → 3 → 4 → 83 → 257, available for free from the same
measurement by changing nothing but what counts as an addition.** Level 3 is
the trap the A-ceiling names: 83 prompts *say* "sum of", and the grammar can
mean **four** of them. A cue word in prose is not a capability; level 2 is the
same population screened by execution.

The rule that keeps 3 from becoming 83 is the A-ceiling's, reused unchanged:
**the addition must be nameable before the population is read, and its yield
must be a consequence of it rather than the reason for it.**

---

## 3. What blocks the four, precisely — the import list for Seam B

Every claim below is verified **in both directions by live invocation**: the
blocked surface is shown NOT to parse, and the repaired surface is shown TO
parse.

| id | prompt | blocked surface (does **not** parse) | repaired surface (**does** parse) | unit of work | cross-task reach of that unit |
|---|---|---|---|---|---|
| **96** | "number of divisors of a given integer" | — | `find the number of divisors of n` | **retarget only** — nothing added | n/a |
| **295** | "sum of all divisors of a number" | `return the sum of all divisors of n` | `the sum of divisors of n that are less than n` | tolerate a **leading quantifier** in the `{set}` slot | **23 prompts** contain " all " |
| **453** | "sum of even factors of a number" | `find the sum of even factors of n` | `find the sum of even divisors of n` | **ONE `member_form` entry**: `factors` ≡ `divisors` | **2 prompts** contain "factor" — and one of them (`308`, "selecting one factor from each list") is ordinary English. **Effective reach 1: this addition is close to a key.** |
| **89** | "the closest smaller number than n" | `find the closest smaller number than n` | `number of integers smaller than n` | **a per-task clause** — CHERRY-PICK | 1 |

**The `factors` synonym is honest but thin, and the key test says so.** Seam
D's leave-one-out null established the test: *a cue that fires on exactly one
task is a lookup key, not a vocabulary item.* `factors` reaches 2 prompts and
converts 1. It survives the test only barely, and that is worth stating in the
same breath as the number it produces.

**The leading-quantifier tolerance is the better of the two** by exactly that
measure — 23 prompts carry the cue — but its measured *conversion* is 1,
because the other 22 fail the signature gate or the language gate anyway. **A
unit with wide surface reach and narrow semantic reach is still worth more than
one with neither**, because it cannot encode an answer.

---

## 4. Task 89 — extensionally exact, conceptually unrelated

`89` ("find the closest smaller number than n") is matched by
`sum{k in 1..n : (1)*(k<n)}` — *the number of integers smaller than n*. That is
`n-1` for every `n ≥ 1`, so it is **exact on the whole domain**, not a
coincidence: 0 divergences over the sweep.

It is nonetheless not a parser conversion and must not be counted as one. No
retarget routes "the closest smaller number" to "the number of integers smaller
than n"; only a hand-written clause does. It is recorded as **language reach,
never parser reach**, which is why level 2c (3) is reported beside level 2b (4)
rather than instead of it.

The converse error is on the record too, and the same instrument catches it:
**task `224` matched all three rows and is wrong.** "Count the set bits" versus
"the number of odd divisors of n smaller than n" agree at n = 2, 4, 6 — the
task's entire revealed set — and disagree at 40 of the 60 swept values, first
at n = 1. Three rows is a small sample; **a formula verified on the rows alone
would have been a fifth coincidental fit produced by under-sampling**, exactly
the failure the A-ceiling caught on task 87.

---

## 5. CEILING C — the math shape codebook

### 5.1 The codebook, re-derived

`seeds/math_capability_shapes.json` holds **17 `ShapeSignature` nodes**, of
which:

- **`kind: "math"` — 6:** `curvature, fractal, phi_bounded_recursion,
  self_similarity, symmetry, topology`
- `kind: "faculty"` — 11: `allographic_store, compression_selector,
  junction_perception, library_growth, order_invariant_binding,
  position_binding, residual_recurrence, sequence_buffer, spatial_attention,
  teacher_bootstrap, turtle_generation`

**The plan's "17 `ShapeSignature{kind:"math"}`" is wrong** — it is the file's
total node count. The correction to "6 of 17" is independently confirmed here
by reading the file, not by quoting the correction.

### 5.2 The mechanism does not read this file — measured, then controlled

`RecogniseShape` (Rust `shape_decode.rs::recognise_meta_shape`, the *same*
scorer `domains/teach.py::categorise_by_shape` and `TransferDecode` use) scores
**`MetaShape` nodes by their `has_principle` neighbours' `keywords`**, by
substring. `math_capability_shapes.json` contains:

| requirement | present |
|---|---|
| `MetaShape` nodes | **0** |
| any node with a `keywords` attr | **0** |
| edges of any kind | **0** |
| `signature` strings of relation tuples | 17 |

So the literal reading of "point `RecogniseShape` at the math codebook" —
load the file, run the Term — gives **0 recognitions over 257 prompts**.

**A null-returning harness proves nothing on its own.** In the same process, a
**positive control** — a synthetic `MetaShape` whose principle carries the
keywords `divisor` and `string` — fires on **43/257**, and the recognised id
list is **exactly** the set of prompts containing those substrings. The
instrument works; the file is the wrong shape for it.

### 5.3 Three keyword variants, all derived from the seed's own content

Because the file carries no keywords, one must decide what a keyword *is* for a
node type never built to have one. Three variants, each read **mechanically**
off content already in the file (nothing authored — which is what makes the key
test below meaningful):

| variant | keyword source | recognised / 257 | shapes hit |
|---|---|---|---|
| `name_concept` | the shape's own `name` + `concept`, word-split | **1** (0.4%) | `self_similarity` ×1 |
| `relation_all` | every lowercase token in the `signature` tuples | **245** (95.3%) | `fractal` ×202, `curvature` ×31, `topology` ×12 |
| `relation_content` | (ii) minus a standard closed-class stopword list | **6** (2.3%) | `symmetry` ×3, `topology` ×2, `fractal` ×1 |

The 245 is not a capability: the relation grammar contains **to / from / by /
is / under / into / between**, which occur in almost any English sentence.
There is no middle setting that finds something *and* means something, because
the file carries no domain lexicon to find.

### 5.4 Every hit classified — 252 hits, **0 genuine**

The bar is arc 5's, reused verbatim: a hit is genuine only if the causing word
is concept-specific **and** the task's own structure independently exhibits
that concept. All 7 hits from the two informative variants were inspected by
hand; the 245 `relation_all` hits were classified by a mechanical glue rule
(caused only by closed-class connectives carried in the signature), with its
**one exception enumerated and hand-inspected rather than waved through**.

| variant | task | shape | causing word | why it fired | verdict |
|---|---|---|---|---|---|
| name_concept | 283 | self_similarity | `self` | "the digit it**self**" | **spurious** — no self-reference at smaller scale |
| relation_content | 101 | fractal | `base` | "1-**base**d indexing" | **spurious** — indexing convention, not a recursion base case |
| relation_content | 222 | topology | `type` | "same data **type**" | **spurious** — a Python type check |
| relation_content | 237 | symmetry | `map` | "**map**ping each tuple to its count" | **spurious** — dict construction, not permutation invariance. *The closest thing to a genuine hit in the entire sweep, and it still fails the second half of the bar.* |
| relation_content | 286 | symmetry | `repeat` | "formed by **repeat**ing the array k times" | **spurious** — literal repetition |
| relation_content | 395 | symmetry | `repeat` | "first non-**repeat**ed character" | **spurious** — and the word is *negated* |
| relation_content | 470 | topology | `pairwise` | "**pairwise** addition of neighboring elements" | **spurious** — arithmetic over adjacent pairs |
| relation_all | 101 | fractal | `base`, `to` | the single glue-rule exception | **spurious** — same "1-based indexing" collision |
| relation_all | 244 others | fractal/curvature/topology | glue only | to/from/by/is/into/under/between | **spurious** |

**`genuine_recognition_ids = []`. 0 of 252.**

### 5.5 The key test — and what it says here

Seam D's leave-one-out just established that 35 of its 36 "properties" were
lookup keys: a single verbatim prompt substring that cue-matched only its own
task. Applied to C's seven informative hits: **5 of the 7 causing keywords fire
on exactly one prompt in 257** (`self`, `base`, `type`, `map`, `pairwise`).

The honest reading cuts both ways and is worth stating precisely. Because
C's keywords are **derived mechanically from the seed**, a per-task key is
*structurally impossible* — nobody wrote `self` in order to hit task 283. So
these are not keys in D's sense. But they are the same thing in effect: **a cue
whose entire population reach is one task is not recognising a class, it is
naming an accident.** The failure mode differs in provenance and is identical
in consequence.

### 5.6 The cherry-picked ceiling — and my own instrument failing the same way

If one hand-authors an algorithmic keyword list per math shape **after** reading
the population — the cherry-pick, stated as such — the naive pass claims **36**
tasks.

**29 of those 36 came from my own cue `turn` matching "re-TURN-s".** The
repaired cue set drops to **9** hits, of which one — task `458`, "the area of a
**rect-ANGLE**" — is a second self-inflicted collision, in the repaired set, on
the second attempt. This is recorded rather than quietly fixed, because it is
the strongest available evidence for the finding: **substring recognition
against algorithmic prose collides by default, and it collides even when the
person building the instrument knows that is the thing being measured.**

Hand-audited, the nine repaired hits yield **exactly one** task whose structure
genuinely instantiates a math shape's *signature*:

| id | shape | why genuine |
|---|---|---|
| **100** | `symmetry` | "the next smallest **palindrome**" — a palindrome *is* invariance under the reversal transform; the signature's `["invariant","PART","under","TRANSFORM"]` holds literally |

The other eight are named and refuted in the artifact (`56`/`131`/`456` apply a
reversal rather than assert an invariance; `124`/`293` mention an angle without
accumulating a heading; `291`/`470` are adjacency without an invariant contact
type; `458` is the substring bug).

### 5.7 Actionability — even the one genuine case converts nothing

Task `100` is not reached by any measured variant (no keyword set contains
"palindrome"), and if it were, the codebook would supply **a label and nothing
else**. Measured directly: the attribute keys across all 17 nodes are
`concept, faculty, kind, name, signature` — **no constraint, no relaxation
family, no IR template, no mechanism steps**. These are `AntiUnify` anchors for
bridging a math concept to one of the agent's own faculties; they were never
built as synthesis payloads, and no live caller feeds this file to
`RecogniseShape`, `TransferDecode`, or any synthesis-facing consumer.

### 5.8 Verdict — Seam C is a NULL

**The sixth content null, and it is a perfectly good result.** It is reported
without softening: 0 genuine recognitions out of 252 hits; 0 recognitions from
the file as it actually is; 1 genuinely-shaped task in the whole population
under the most generous hand-authored reading, unreachable and unactionable.

Per the plan's own registered null reading, this ends the acquisition line with
the proposal line — **structures must be supplied, and the ceiling is set by
how many a person writes.** Note what would be required to make Seam C
contribute: a new hand-authored program-synthesis keyword vocabulary **and** a
payload attached to each shape. At that point the recognition step is redundant
with authoring the constraint directly, which arc 5 already did more cheaply,
straight against the IR.

---

## 6. What broke while measuring

Breakage is signal, so it is recorded rather than smoothed over.

1. **A bug in the REFUTING direction, which spuriously nulled task 96.** The
   first version of the mechanical retarget rewrote every argument-denoting
   noun phrase, including "the number". So *"find the number of divisors of a
   given integer"* became **"find n of divisors of n"** — the retarget
   destroyed the very `number_of` aggregator it was meant to feed, and level 1
   read **0** instead of **1**. A refuting-direction bug is indistinguishable
   from an honest null. It was found by reading the retargeted **text**, not
   the aggregate. Fixed with two guards derived from the grammar itself, not
   from the population: never rewrite a phrase followed by "of" (that is the
   aggregator), and delete rather than substitute a phrase already followed by
   the index variable (*"an integer n"* → *"n n"*).

2. **A row-matching formula that is wrong — caught only by a witness sweep.**
   Task `224` matched all three revealed rows and diverges from popcount at 40
   of 60 swept inputs. Had the language ceiling been reported at row-matching
   alone it would have read 5. **Every ceiling in §2.4 above level 2 exists
   because of this one task.**

3. **My own cherry-picked cue set reproduced the exact failure it was built to
   expose** — twice (`turn` → "returns", 29 ids; then `angle` → "rectangle" in
   the *repaired* set). Left visible in the artifact.

4. **Task 295's reference implementation and its own prompt disagree.** The
   prompt says "the sum of **all** divisors"; the asserts (`8→7, 12→16, 7→1`)
   define the **proper**-divisor (aliquot) sum. The grammar's matching sentence
   is the aliquot sum and agrees with the asserts everywhere on the sweep —
   but it disagrees with the reference *code* at n = 1 (the code returns 1,
   both the aliquot reading and the formula return 0). Recorded because the
   conversion is real under the task's own specification and would have looked
   like a bug under the reference's.

5. **The engine hazard is live in this tree.** The canonical tree's `.so`
   (`7dd9af13…`) differs from this worktree's (`5c1b472f…`), and a bare
   `import substrate_rs` resolves to the canonical one through the `.pth`. Any
   probe here that skipped `engine_preamble()` would have measured a different
   binary while believing it measured HEAD.

6. **Not broken, worth naming:** all 550 generated grammar surfaces parse, and
   `_ACQUIRED` is empty at import — so the enumerated language is the real one,
   with nothing silently widening it.

---

## 7. Recommendation

**Seam B — do not build M2 as scoped; the finding is a two-line grammar diff,
not a retarget.** The measured conversion of retargeting `extract_function`'s
*output* to hub IR is **1 task**, and the language it would be emitting from
tops out at **4** on this corpus at any effort. Two blind seed additions
(quantifier tolerance, `factors` synonym) take it to **3**; both are one-line
JSON edits and neither requires touching `extract_function`, hub IR, or
`ProgEval`. **The cheap 90% of Seam B's value is available without Seam B.**

If the retarget is built anyway, it must be for the *mechanism* rather than the
score: `extract_function` is a working NL→formal→verify-by-execution loop, and
that shape is worth having on the hub IR path even at n = 1 — but that is an
architectural argument, not a conversion argument, and it should be made as
one. Prerequisite in either case: `extract_function` returns *candidates* (up
to 2 per prompt, sometimes wrong-first — task 295 returns `divisor_sum(n)`
before the correct aliquot form), so the verdict layer must select, exactly as
OEIS's ground-truth values do today.

**Seam C — do not build M3.** Null on every measured reading, with the
mechanism, the vocabulary, and the payload each independently sufficient to
produce it.

**The M0 picture, now complete.** A = 5 ids (SymPy at module granularity, 79%
of the population blocked by structural primitives no import supplies). B = 1–4
ids (85% of the population blocked by signature shape before semantics is
consulted). C = 0. D = 0/36 as scoped, and a total null under leave-one-out.
**Four probes, four small numbers, and the same cause under three of them: the
unreached MBPP population is blocked by lists, strings, tuples, dicts and
multi-argument structure — not by mathematics.** The arc's own question ("does
an embodied mathematics compound when its parts are connected?") is not
answered negatively by this; it is answered *"not on this corpus"*, which is
the plan's own registered null reading, and it is a statement about MBPP.

---

## 8. Files

`scripts/arc6_bc_ceiling.py` — the driver. Ceiling B: vocabulary verification
against the seed; exhaustive 550-surface language enumeration through the real
`extract_function`; grounding + evaluation of every formula via
`comprehend_computational_definition` / `reason.solve`; the signature-shape
gate; the five-level honest/cherry-picked ladder; the witness sweep; the
both-directions missing-construction probe. Ceiling C: codebook re-derivation;
literal seed load; the positive control; three mechanically-derived keyword
variants driven through the real `RecogniseShape` Rust Term; per-hit
classification; the key test; the two-pass cherry-picked semantic ceiling with
its hand audit. Engine preamble + provenance stamp, twin-run determinism,
input-file hashing.

`results/arc6_bc_ceiling.json` — the artifact: per-task rows for all 257 tasks
in both ceilings, all 39 canonical language functions with signatures, every
hit with its causing keyword and verdict, the witness sweep with divergence
points, engine provenance, input hashes, determinism hash.

This file.

**Reproduce with:** `OZMA_NO_LLM=1 python scripts/arc6_bc_ceiling.py`
(deterministic; two consecutive full runs byte-identical modulo the timestamp;
`id_hash = 48270ea65125159a`, engine `5c1b472fe674`).
