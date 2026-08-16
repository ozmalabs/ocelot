# Ceiling reassessment 5 — a modulus/parity `FilterList` predicate template — PREREG

**Date:** 2026-08-16. Base `main @ 84cd082` ("Merge progsyn-zipwith-followon:
D2 binder-recognition bugfix + scoped max_candidates raise -- +8/+8/+8,
complete ZipWith cluster converted"), verified fresh via `git log --oneline
-1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-5`, branch
`progsyn-ceiling-reassessment-5`.

**Headline finding, stated up front: a single, zero-new-`TermNode`,
live-verified fix exists — widen `filter_templates_by_size` (the fixed,
hand-authored predicate-template pool `FilterList`'s third argument is
drawn from) with a new `item % c == r` / `item % c != r` family, composed
entirely from already-shipped Terms (`Mod`, `Eq`, `Not`, `Var`, `Lit` — the
exact same "expose an existing capability as a composable predicate shape"
class as every prior `tmpl:*` family in this same function). This is not a
guess — it is the exact, precisely-scoped, already-priced candidate named
by `PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md` (a same-day
predecessor rung, `main @ 371475d`, which investigated and correctly
declined to build a third `SynthesisOperatorShape` for task 412, but along
the way diagnosed task 412's REAL blocker to its exact mechanism and named
the fix that would actually convert it) and reconfirmed live in this
worktree against the CURRENT baseline before building anything.**

Both target witnesses (tasks 412 "remove odd numbers", 426 "filter odd
numbers") are independently hand-evaluated end-to-end against ALL THREE
rows each (revealed AND held-out), 100% exact match, using nothing but the
engine's own `evaluate()` binding on already-shipped Terms — no speculative
design, no untested primitive. This matches this arc's own repeated
methodology (`IntersectAll`/`UnionAll`, `DictFromPairs`, `ZipWith` were all
verified the same way before being built).

---

## 1. Real baseline, confirmed live

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run fresh in this worktree on the
unmodified build (gitignored fixture dependencies — `mbpp_zero_shot_
baseline.json`, `prog_construction_scan.json`, `prog_ir_histogram.json`,
`prog_ir_python_coverage.json`, `prog_chunk_mine.json`,
`mbpp_train_diet.json`, `prog_synthesis_battery.json`,
`mbpp_arc3_endgame.json`, `mbpp_blocker_histogram.json` — copied from the
canonical tree's `results/` first, per every predecessor rung's own
documented prerequisite):

```
full:              84/257  p=0.326848  ci=[0.272418, 0.386379]  det_identical=True
content_stripped:  83/257  p=0.322957  ci=[0.268758, 0.382371]  det_identical=True
official:         109/257  p=0.424125  ci=[0.365256, 0.485227]  det_identical=True
```

`head` in the resulting `results/mbpp_endgame.json` reads `84cd0826b52...`,
byte-identical to `git log --oneline -1 main` — a genuine fresh
measurement on the current tip, matching the task brief's own cited
baseline (84/83/109) exactly. Saved as `results/mbpp_endgame_BEFORE_
this_rung.json`.

## 2. Failure-cause grouping — the real 173 currently-failing runnable tasks

Every one of the 173 non-passing `full`-arm runnable tasks (257 − 84) was
individually re-run through `domains.prog_synthesis.synthesize_from_
request`, via `scripts/ceiling3_diag_sweep.py` (already on `main`, reused
verbatim, no edits) — output `results/ceiling3_diag_sweep.json`, 173 rows.

| outcome | n |
|---|---|
| `gapped:enumerate_failed` | **71** |
| `accepted_holdout_fail` | **60** |
| `gapped:property_verdict_reject` | **17** |
| `gapped:structural_verdict_reject` | **14** |
| `gapped:exhausted` | **5** |
| `gapped:no_shape` | **3** |
| `not_recognized` | **1** |
| `runner_exception:ValueError` | **1** |
| `runner_exception:TypeError` | **1** |

**Reconciles exactly against the immediate predecessor's own re-derivation**
(`PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md §3`, measured at
the pre-ZipWith baseline of 76/257): that document found `gapped:enumerate_
failed=79`, `accepted_holdout_fail=60`, `property_verdict_reject=17`,
`structural_verdict_reject=14`, `exhausted=5`, `no_shape=3`,
`not_recognized=1`, plus 2 runner exceptions — **every bucket is
byte-identical except `enumerate_failed`, which shrank by exactly 8** (79
→ 71), matching the ZipWith-followon rung's own +8 conversion exactly (all
8 were `enumerate_failed` before converting). This is strong independent
confirmation that the population is stable and well-understood between
rungs — no bucket churned unexpectedly.

`gapped:enumerate_failed` (71) splits the same way every prior rung in this
arc has split it:

```
budget-exhausted (tested == 200,000 exactly): 58
saturated (tested < 200,000):                 13
```

Saturated task ids: `97, 117, 277, 299, 305, 308, 391, 408, 412, 417, 462,
465, 470` (three of these — 308, 391, 408 — read `tested=300000`, the
ZipWith-followon rung's own scoped `ZIP_MAX_CANDIDATES` raise, not the
default 200,000 cap; still architecturally a budget-style halt, not a
`max_size` exhaustion, and unrelated to this rung's own target).

The `accepted_holdout_fail`/`*_verdict_reject` population (91 = 60+17+14)
is the same population `PROGRAM_SYNTHESIS_RETRIEVAL_FALLTHROUGH_RESULTS.md`
and `PROGRAM_SYNTHESIS_STRUCTURAL_REJECT_SURVEY_PREREG.md`/
`PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY_RESULTS.md` already sized and
decisively NO-GO'd (an information-theoretic floor on what 1-3 revealed
rows can determine, plus a 93.3% false-accept rate under a naive
retrieval-fallthrough widening) — not re-investigated here, per the task
brief's own instruction not to re-litigate settled NO-GOs.

## 3. Target: task 412's real blocker, diagnosed by the immediate
   predecessor rung, re-verified fresh here

**`PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md`** (same-day
predecessor, un-merged investigation-only rung, `main @ 371475d`,
`git log` confirms it is an ancestor of the current tip `84cd082`) set out
to check whether task 412 justified a third `SynthesisOperatorShape` and
found: **no** — but along the way it traced task 412's real blocker to its
exact mechanism, live, via a `sub._inner` logging proxy:

```
call 1: max_size=9, max_candidates≈19175-cap  -> found=False, tested=19175,  halt=max_size
call 2: max_size=1                             -> found=True,  tested=1,     halt=solved   (trivial zero-term probe, unrelated)
call 3: max_size=9, max_candidates=200000      -> found=False, tested=140575, halt=max_size
```

`halt_reason: 'max_size'` on the real terminal call — the search exhausted
the ENTIRE candidate tree at `max_size=9` (140,575 distinct terms) and
never found the target, because **the target predicate was never in that
tree to find**. Both `FilterList` and `Mod` are individually shipped,
working `TermNode`s and both names already appear in `OP_TABLE` — but
`FilterList`'s third argument (the predicate) is NOT filled in by
composing `OP_TABLE` ops recursively. It is filled in from a SEPARATE,
fixed template pool, `filter_templates_by_size`
(`synth_enumerate.rs:2717-2870` pre-this-rung), consulted only at the
`OpKind::ListFilter` match arm. That predecessor rung read the pool's
construction in full and found **none of its six existing template
families constructs a modulus/parity predicate of any kind** — confirmed
by the module's own pre-existing source comment inside family 5
(`tmpl:nested_reduction`): *"the pool has {+, -, *} and no `Mod`, so a
DIVISIBILITY quantifier is not reachable here."*

That predecessor rung also empirically proved `SynthesisOperatorShape`
CANNOT fix this (§5 of that document: even the most favorable possible
`ops` narrowing, `["FilterList","Mod","Eq"]`, still returns `found: False`
against task 412 — because `spec["ops"]` and `filter_templates_by_size`
are two entirely disjoint code paths that never communicate) — and named
the correct fix precisely: *"a widened `filter_templates_by_size` (a new
`item % const CMP const` template), which is a missing-primitive/
template-pool-shape addition... named here, precisely scoped, for a
FUTURE, separately-regression-priced rung — not built in this one."*
**This rung is that future rung.**

### 3.1 Re-verified fresh, this worktree, before any code change

```
task 412: FilterList(a, item, Eq(Mod(item, 2), 0))
  {'a': [1, 2, 3]}    -> [2]        == expected  (revealed)
  {'a': [2, 4, 6]}    -> [2, 4, 6]  == expected  (revealed)
  {'a': [10, 20, 3]}  -> [10, 20]   == expected  (HELD-OUT)

task 426: FilterList(nums, item, Not(Eq(Mod(item, 2), 0)))
  {'nums': [1,2,3,4,5,6,7,8,9,10]} -> [1,3,5,7,9]   == expected  (revealed)
  {'nums': [10,20,45,67,84,93]}    -> [45,67,93]    == expected  (revealed)
  {'nums': [5,7,9,8,6,4,3]}        -> [5,7,9,3]     == expected  (HELD-OUT)
```

**6/6 exact matches, including both held-out rows**, via
`substrate_rs.Substrate()._inner.evaluate()` on hand-built term-JSON —
independently re-run in this worktree, not copied from the predecessor
document.

### 3.2 The full witness population, from the predecessor's own
   exhaustive (not sampled) sweep of every currently-failing task

The predecessor rung read every one of the 65 (its own, slightly earlier
baseline's) Group-B "never finds any real candidate" tasks' ground-truth
reference code and classified each one's true op-need. Result: **exactly
one exact witness pair** (412, 426 — identical op-set `FilterList`+`Eq`/
`Not`+`Mod`, identical template family, near-identical prompt: "remove odd
numbers" / "filter odd numbers"), **one weaker, different-family witness**
(75, "divisible by k" — needs `Mod` inside family 5's nested-reduction
inner grammar, a different code location, NOT this rung's target), and
**two near-misses** (226, 437 — index-parity on a STRING, which needs
`FilterList` exposed to string-shaped specs at all, a strictly larger
2-part gap, NOT this rung's target). No other task among the 65 needs a
modulus/parity predicate inside a `FilterList`-style construct — confirmed
by that document's own full-population read of every task's ground-truth
`code` field (not sampled, not guessed from prompt text).

**This rung targets only 412/426** (the exact, cleanest witness pair) —
matching this arc's own single-variable-rung discipline and the
predecessor's own explicit scoping recommendation. 75/226/437 are named,
not built, exactly as the predecessor rung left them.

## 4. The exact mechanical fix

`runners/dsl/src/synth_enumerate.rs`, inside the existing `if filter_wanted
{ ... }` block (`synth_enumerate.rs:2936` region) that already builds
`filter_templates_by_size`'s families 1-5, immediately after family 1's
`scalar_vars` loop and before `tmpl:item_in_listvar`: a new family,
`tmpl:item_mod_eq`.

**Design, mirroring family 1's own construction exactly:**

- `c`/`r` are BOTH drawn from `numeric_consts` — the exact same
  spec-derived constant pool every other template family in this block
  already uses (defaults `{0,1,2,-1}` plus every Int-valued example
  input/output value, deduped) — never a benchmark-specific literal.
- Restricted to the mathematically well-formed range: modulus `c > 1`
  (mod-by-0/1 is degenerate — mod 1 is always 0, and this engine's own
  `Mod` treats `b == 0` as a `0` short-circuit, `term.rs`'s `rem_euclid`
  arm), remainder `0 <= r < c` — the EXACT range `Mod`'s own `rem_euclid`
  semantics can ever produce for a positive modulus (confirmed by reading
  `term.rs:7716-7723`: `Value::Int(av.as_i64().rem_euclid(bi))`). This is
  a semantic constraint, not a benchmark-fitted one — it applies to ANY
  spec-derived modulus/remainder pair, not specifically 2/0 or 2/1.
- Only `Eq`/`Not(Eq(...))` offered (NOT the full 5-way `CMPS` crossing
  family 1 uses) — a modulus compared via `Gt`/`Lt` is not a predicate
  shape any surveyed MBPP task needs (confirmed by the predecessor rung's
  own full-population read), and omitting it keeps this addition's own
  blast radius to exactly the two forms 412/426 require — the same
  "only build what's witnessed" discipline `ZIP_ELEMENTWISE_OP_NAMES`'s
  own fixed 7-op inventory already uses (rather than crossing all of
  `DEFAULT_OPS`).
- `item % c == r` — size 5 (`Eq`+`Mod`+`Var`+`Lit`+`Lit`), pushed to
  `filter_templates_by_size[5]`.
- `item % c != r` — size 6 (`Not` wrapping the above), pushed to
  `filter_templates_by_size[6]` — the same "+1 for the negated form" idiom
  the immediately-following `tmpl:item_in_listvar`/`not in` family already
  uses for its own negation.

**Zero new `TermNode` variant.** `Mod`, `Eq`, `Not`, `Var`, `Lit` are all
pre-existing, fully-wired Terms, all already rendered by this module's own
local `term_json` (confirmed by grep before writing any code — unlike the
`DictFromPairs` rung, which found and had to fix a real `MkDict` gap in
this exact renderer, no such gap exists here: `TermNode::Eq`, `TermNode::
Not`, and `TermNode::Mod` all already have `term_json` match arms at
`synth_enumerate.rs:1490/1495/1735`).

**Sizing check, done before writing code**: for the DEFAULT const pool
`{0,1,2,-1}` (task 412/426 have no scalar-Int outputs contributing
additional consts), only `c=2` satisfies `c > 1`; `r ∈ {0,1}` both satisfy
`0 <= r < 2`. **This generates exactly 4 new template entries** (2 at size
5, 2 at size 6) for this pool — a tiny, bounded addition, not a
combinatorial one, because the semantic `0 <= r < c` guard prunes the vast
majority of the naive `|consts|²` cross product before it is ever built.

## 5. Regression risk, priced before building

**Architectural argument, not just canary-counting.** The search
(`synth_enumerate.rs`'s `OpKind::ListFilter` arm) explores `FilterList`
candidates in increasing TOTAL size order (`source_size + predicate_size +
1`), and the `reg!` macro short-circuits on the FIRST solved candidate at
whatever size it is found (`Reg::Solved` returns immediately, per every
prior rung in this arc's own documented search semantics). This rung's new
templates occupy predicate-size slots 5 and 6 exclusively — they cannot
appear at ANY total `FilterList` size below `1(min source)+5(min
predicate)+1 = 7`. **Any currently-passing task whose real `FilterList`
solution has total size < 7 is therefore PROVABLY unaffected** — the
search reaches and halts on its own existing solution before ever
exploring predicate-size 5/6.

**Checked directly against the real population, not just argued.** Of the
84 currently-passing `full`-arm tasks, exactly 2 are both (a) sourced via
`SynthEnumerate` itself (`rungs.enumerate == 1`, not a retrieved-exemplar
copy that merely happens to contain a `FilterList` node) and (b) use
`FilterList` in their accepted `ir`: **task 161** ("remove all elements
present in another list", `FilterList(a, item, Not(In(item,b)))`,
predicate size 4, total size 6) and **task 436** ("return the negative
numbers in a list", `FilterList(a, item, Lt(item, 0))`, predicate size 3,
total size 5). **Both are strictly below size 7** — the architectural
argument above applies to both directly, not just by analogy.

Task 132 (this arc's own standing string-shaped canary, never reaches
`FilterList` at all) is expected unaffected, checked anyway per house
discipline.

## 6. The plan

Build the `tmpl:item_mod_eq` family exactly as specified in §4. Rebuild
from source, run the full paired MBPP battery (exact task-id set diff
against the 84/83/109 baseline established in §1), run the Rust suite
(778/778 expected — this fix touches no Term evaluator, only search-loop
template-pool registration code), run the named 9-file Python regression
suite (3 pre-existing failures expected), run `test_retrieval_migrated.py`
and `test_reject_informs_repair_migrated.py` (since this rung touches
`FilterList`-adjacent template-pool machinery, matching the task brief's
own "retrieval-adjacent" trigger), then write the RESULTS document.

**What this rung does NOT attempt:** task 75 (needs `Mod` inside family
5's nested-reduction inner grammar, a different code location); tasks
226/437 (need `FilterList` exposed to string-shaped specs at all, a
strictly larger 2-part gap); the `SynthesisOperatorShape` mechanism
(already conclusively disqualified by the predecessor rung for this exact
population); the `accepted_holdout_fail`/`*_verdict_reject` population (91
tasks, already NO-GO'd); the `no_shape`/`exhausted` buckets (8 tasks
total, small, no shared single-cause pattern identified in this rung's own
brief look).

## What this document does NOT establish

1. Whether the automatic typed default (after this widening lands) reaches
   the same witness within the real pipeline's actual budget, via the REAL
   search loop end-to-end (not a hand-built term) — checked in §3.1 against
   the hand-built term only; the RESULTS document checks the real pipeline
   before claiming conversion.
2. Whether tasks 161/436 (or any other currently-passing task) regress is
   unmeasured until the build lands — priced as provably low-risk above
   (§5's architectural argument), not dismissed without checking.
3. This document does not re-litigate the retrieval-fallthrough,
   structural-reject, or property-reject NO-GOs — all re-confirmed present
   and unchanged in §2's population count, not re-investigated further.
4. Whether 75/226/437 are worth their own future rungs is not priced here
   beyond what the predecessor document already established — named, not
   sized, not built.
5. The `gapped:no_shape` bucket (3 tasks: 77, 164, 256 — all interestingly
   divisor/primality-flavored, but a DIFFERENT failure shape: `enumerate_
   outcome: "ok"` with a populated `solution_size`, meaning `SynthEnumerate`
   itself found something but a downstream shape/cover-parts gate rejected
   it) was noticed but not investigated — it is orthogonal to this rung's
   own `FilterList`-template-pool target (none of the 3 uses `FilterList`)
   and not established here as a real or fixable cluster.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-5
git log --oneline -1   # 84cd082 pre-this-rung's-own-commit, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

Live witness re-check (hand-built term JSON, no code change needed to
reproduce):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
t412 = {'type':'FilterList','source':{'type':'Var','name':'a'},'var_name':'item',
        'predicate':{'type':'Eq','a':{'type':'Mod','a':{'type':'Var','name':'item'},'b':{'type':'Lit','value':2}},'b':{'type':'Lit','value':0}}}
rows = [({'a':[1,2,3]}, [2]), ({'a':[2,4,6]}, [2,4,6]), ({'a':[10,20,3]}, [10,20])]
for env, expected in rows:
    print(env, '->', s._inner.evaluate(t412, env), 'expected', expected)
"
```
