# Task 412 witness check for a third `SynthesisOperatorShape` — investigation only, no build; NO-GO, mechanism-level, not just population-level

**Date:** 2026-08-16. Base `main @ 371475d`, verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/tmp/progsyn-operator-shape-witness-check`, branch
`progsyn-operator-shape-witness-check` — **not merged to `main`, not
pushed**, left for the orchestrator's independent re-verification. Zero
tracked files changed (`git status --short` shows no modified tracked
file — confirmed after the investigation, before writing this document).

---

**HEADLINE: a witness pair for task 412 DOES exist by the exact
textual+op-set test the orchestrator specified — task 426 ("filter odd
numbers") shares both task 412's trigger phrase and its true op-need,
support=2 — but it does NOT justify building a third
`SynthesisOperatorShape`, because the finding is disqualified one layer
down, at the MECHANISM itself, not at the population-count level. Read
directly from source (`runners/dsl/src/synth_enumerate.rs`) and confirmed
live (both by hand-built-term evaluation and by an empirical
narrowed-`ops` re-run of the real search): `SynthesisOperatorShape` can only
ever narrow `spec["ops"]`, the operand list offered to the GENERAL
op-composition grid (`OP_TABLE`); `FilterList`'s predicate argument is
NEVER drawn from that grid at all — it is built exclusively from a
separate, fixed, hand-authored template pool
(`filter_templates_by_size`), which has no modulus/parity template of any
kind, a gap already named (for two sibling tasks, not 412) by
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_RESULTS.md` §5.2 and still
completely unbuilt today. Because `spec["ops"]` and
`filter_templates_by_size` are two entirely disjoint code paths, no
`SynthesisOperatorShape`, however precisely triggered, can ever make task
412 (or 426, or 75) solvable — proven empirically below (§5), not just
inferred from reading the source. The correct fix for this 3-task cluster
is a widened `filter_templates_by_size` (a new `item % const CMP const`
template), which is a missing-primitive/template-pool-shape addition —
the SAME class of deferred, higher-blast-radius candidate
`DICTFROMPAIRS_RESULTS.md` and `BUDGET_EXHAUSTED_SURVEY_RESULTS.md` both
already named and declined to build in a single-variable rung — not a
`SynthesisOperatorShape` (Rung 4) candidate at all. `PROGRAM_SYNTHESIS_
META_SKILL_ASSESSMENT_PREREG.md`'s "no data anywhere to justify Rung 4"
verdict therefore stands, but for a sharper, mechanism-checked reason than
that document had available: the one population that superficially LOOKS
like a witness pair is witnessing a completely different, disjoint
mechanism.**

---

## 1. Method

1. Re-derived the current budget-exhausted/saturated "genuine
   first-attempt zero-recall" population against the LIVE baseline (not
   the task brief's cited figures, re-measured fresh in this worktree).
2. Read task 412's real prompt/tests from
   `tests/fixtures/mbpp/sanitized-mbpp.json`, hand-built the correct
   program, and verified it against revealed AND held-out rows via
   `substrate_rs.Substrate()._inner.evaluate()`.
3. Traced task 412's real search calls (a `sub._inner` logging proxy,
   the same substitution method
   `PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md` §4 used) to
   confirm the true blocker mechanism directly, not by re-quoting the
   older `CEILING_REASSESSMENT_4` characterization.
4. Read `runners/dsl/src/synth_enumerate.rs` end-to-end for the exact
   code path `FilterList` predicates are built from, and for the exact
   code path `SynthesisOperatorShape`'s `ops` verdict is consumed by.
5. Extracted trigger-word candidates from task 412's prompt in the same
   style as the two shipped `SynthesisOperatorShape` nodes
   (`seeds/program_synthesis_grounding.json`).
6. Read every one of the 65 currently-re-derived zero-recall tasks'
   ground-truth reference implementation (`sanitized-mbpp.json`'s own
   `code` field — the actual Python solution, not a guess from the
   prompt) and classified each one's true required op-combination,
   checking specifically for (a) the same op-combination as 412
   (`FilterList` + a modulus/parity predicate) and (b) matching or
   related trigger words.
7. Empirically confirmed the mechanism-level disqualification (§5) by
   calling the real `SynthEnumerate` Term directly with an `ops` list
   narrowed to EXACTLY what a favorable `SynthesisOperatorShape` would
   offer (`FilterList`, `Mod`, `Eq`) and observing the outcome.

No code or seed file was modified at any point. Everything below is
either a direct source-code citation, a live `evaluate()` call, or a live
`ceiling3_diag_sweep.py`/`mbpp_endgame_battery.py` re-run in this
worktree.

---

## 2. Live baseline, re-confirmed fresh

```
full:              76/257  p=0.29572   ci=[0.243264, 0.354192]  det_identical=True
content_stripped:  75/257  p=0.291829  ci=[0.239641, 0.350148]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

Byte-identical to the task brief's cited baseline, `results/mbpp_endgame.json`
(re-run fresh in this worktree — the eight gitignored fixture dependencies
named in `MODSQRT_SCOPED_FIX_RESULTS.md` §5.2 were copied from the
canonical tree first, matching that document's own documented
prerequisite).

---

## 3. Re-derivation of the "genuine zero-recall" population against the
   CURRENT baseline — and a correction to the task brief's own framing

`scripts/ceiling3_diag_sweep.py`, re-run fresh (181 non-passing runnable
`full`-arm rows, `257 − 76`):

```
gapped:enumerate_failed           79   (was 96/94 in earlier docs; population churns as ops widen)
accepted_holdout_fail             60
gapped:property_verdict_reject    17
gapped:structural_verdict_reject  14
gapped:exhausted                   5
gapped:no_shape                    3
not_recognized                     1
runner_exception:ValueError        1
runner_exception:TypeError         1
                                 -----
total                            181
```

Splitting `gapped:enumerate_failed` (79) by `enumerate.tested`, mirroring
`BUDGET_EXHAUSTED_SURVEY_PREREG.md` §1's own method exactly:

```
budget-exhausted (tested == 200,000 exactly): 69
saturated (tested < 200,000):                 10
```

**Budget-exhausted (69):** `14, 18, 75, 99, 102, 103, 108, 123, 128, 137,
160, 163, 165, 172, 226, 229, 238, 240, 242, 248, 251, 252, 255, 259, 261,
262, 265, 273, 280, 282, 293, 297, 300, 301, 304, 307, 308, 310, 389, 390,
391, 392, 395, 396, 397, 399, 401, 408, 411, 414, 415, 419, 421, 422, 426,
427, 429, 430, 432, 437, 439, 440, 442, 445, 447, 453, 459, 468, 478`.

**Saturated (10):** `97, 117, 277, 299, 305, 412, 417, 462, 465, 470`.

**Correction to the task brief's own framing**: task 412 is, and has ALWAYS
been (`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_4_PREREG.md` line ~108
already listed it in the "genuinely saturated under budget" set, before
the budget-exhausted survey's 82/62-task population existed at all), a
member of the **saturated** bucket, not the 82-task budget-exhausted
bucket the "62-task genuine-zero-recall population" was drawn from in
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md` §4 (`412` does not
appear anywhere in that document's own 82-task-id list). This is not a
demotion of the population's relevance — saturated is architecturally the
SAME "no candidate ever proposed, at any budget" finding, just reached by
running out of the search TREE at the given `max_size` rather than
running out of `max_candidates` — but it means task 412 was never
literally "one of the 62," and the honest population to check task 412's
witness against is the UNION of the re-derived budget-exhausted zero-recall
tasks and the saturated bucket, not the 62-task list read as a closed set.
This union is derived and checked in full in §6/§7 below.

**Re-derived Group A / Group B split** (mirroring
`BUDGET_EXHAUSTED_SURVEY_PREREG.md` §4's own method, adapted because the
literal `exclude` JSON field that method keyed on no longer appears on any
`SynthEnumerate` term in the current engine — confirmed by direct
inspection, §4 below — so the classification predicate used here is the
method's own underlying intent, not its literal implementation: a task is
"Group A" iff some `SynthEnumerate` call in its real trace shows
`found=True` at `tested>1` — i.e., a REAL search attempt proposes SOME
candidate that fits the revealed rows, excluding the unrelated
`max_size=1`/trivial-zero-term probe lane — yet the task's final status is
still `gapped`; "Group B" iff no call, at any point, at any budget, ever
proposes a real candidate):

```
Group A (finds-a-real-candidate-somewhere-but-still-gapped): 14
  14, 103, 165, 238, 300, 304, 389, 392, 396, 397, 414, 430, 432, 453

Group B (never finds ANY real candidate, at any budget):     65
  18, 75, 97, 99, 102, 108, 117, 123, 128, 137, 160, 163, 172, 226, 229,
  240, 242, 248, 251, 252, 255, 259, 261, 262, 265, 273, 277, 280, 282,
  293, 297, 299, 301, 305, 307, 308, 310, 390, 391, 395, 399, 401, 408,
  411, 412, 415, 417, 419, 421, 422, 426, 427, 429, 437, 439, 440, 442,
  445, 447, 459, 462, 465, 468, 470, 478
```

Task 412 sits in Group B (confirmed both by this population-wide sweep
and by its own dedicated trace in §4). This 65-task list — budget-exhausted
∪ saturated, minus the 14-task Group A — is the population checked
exhaustively in §7 for a witness. It supersedes the original document's
62-task list (which was drawn only from the budget-exhausted-only 82-task
population, at an earlier baseline, before `Mod`/`Sqrt` exposure moved
tasks 77, 92, 126, 171, 228, 246, 256, 295, 435 out of that population
entirely and 99, 238, 301 into it — an 8-task net churn, not a stable
count).

---

## 4. Task 412's precise diagnosis — traced, not guessed

**Prompt** (`tests/fixtures/mbpp/sanitized-mbpp.json`, task_id 412):
*"Write a python function to remove odd numbers from a given list."*
Reference solution: `[i for i in l if i % 2 == 0]`-equivalent (the
fixture's own `code` field literally mutates via `l.remove(i)` inside a
loop, but the observable input/output behavior — confirmed against every
row — is exactly "keep the even numbers").

**Rows** (`domains.mbpp_spec.split_rows(parsed['rows'], 'primary')`):

```
revealed: a=[1,2,3] -> [2];  a=[2,4,6] -> [2,4,6]
held_out: a=[10,20,3] -> [10,20]
```

**The correct program, hand-built and verified against ALL THREE rows
(revealed AND held-out) via `substrate_rs.Substrate()._inner.evaluate()`:**

```python
FilterList(a, item, Eq(Mod(item, 2), 0))
```

```
{'a': [1, 2, 3]}    -> [2]        == expected  (revealed)
{'a': [2, 4, 6]}    -> [2, 4, 6]  == expected  (revealed)
{'a': [10, 20, 3]}  -> [10, 20]   == expected  (HELD-OUT)
```

Both `FilterList` and `Mod` are shipped, working `TermNode`s
(`term.rs`), and both names DO appear in `OP_TABLE`
(`synth_enumerate.rs:328` `FilterList`, `:411` `Mod`) — so on the surface
this looks like a pure op-composition, both ops already offered. **This is
exactly the surface reading `CEILING_REASSESSMENT_4_PREREG.md` §3.4 gave
it** ("both `FilterList` and modulo arithmetic are already offered under
`DEFAULT_OPS ∪ LIST_EXTRA_OPS`... a search/pruning-cost question").

**That surface reading is checked here and found WRONG, at the mechanism
level — this is the primary diagnostic finding of this document.**
`FilterList`'s third argument (the predicate) is not filled in by
composing `OP_TABLE` ops recursively. It is filled in from a SEPARATE,
fixed template pool, `filter_templates_by_size`
(`synth_enumerate.rs:2669-2870+`), built once per search and consulted
only at `synth_enumerate.rs:3150-3154` (`filter_templates_by_size[st]`).
Reading that pool's construction in full (`:2717-2870`): it contains
exactly six template families —

1. `item OP const` (size 3) and `len(item) OP const` (size 4), for each
   of 5 comparisons (`Gt/Lt/Gte/Lte/Eq`, a hardcoded `CMPS` array,
   `:2718-2719`) crossed with every numeric constant in the spec's
   constant pool;
2. `item OP <scalar spec variable>` (size 3);
3. `item in <list-valued spec variable>` / `not in` (Arc6 tier-0
   `tmpl:item_in_listvar`);
4. `len(item) OP <scalar spec variable>` (Arc6 tier-0
   `tmpl:len_item_vs_var`);
5. a one-level-nested `MaxOver/MinOver/Sum(<inner> for x in item) OP rhs`
   quantifier (`tmpl:nested_reduction`), whose own inner-value grammar is
   `{+, -, *}` over the SAME numeric-constant/scalar-variable operand set.

**None of the six constructs a modulus/parity predicate of ANY kind.**
This is not a new observation — the module's own source comment,
literally inside template family 5, says so directly and unprompted
(`synth_enumerate.rs:2796-2798`): *"the pool has {+, -, *} and no `Mod`,
so a DIVISIBILITY quantifier is not reachable here."* What IS new here:
**`Mod`'s presence in `OP_TABLE` (added by `PROGRAM_SYNTHESIS_
MODSQRT_SCOPED_FIX`, merged since that comment was written) changes
NOTHING about this** — the comment is still exactly true today, because
`filter_templates_by_size`'s template construction never reads `OP_TABLE`
or `op_list` content at all beyond the single boolean gate `filter_wanted
= op_list.iter().any(|(n,_)| n == "FilterList")` (`:2654`), which only
decides WHETHER to build the pool, never WHAT to put in it.

**Live trace, confirming this diagnosis against the real pipeline (not a
hand-built term)** — a logging proxy substituted for `sub._inner`
(same method as `BUDGET_EXHAUSTED_SURVEY_PREREG.md` §4):

```
call 1: max_size=9, max_candidates≈19175-cap  -> found=False, tested=19175,  halt=max_size
call 2: max_size=1                             -> found=True,  tested=1,     halt=solved   (trivial zero-term probe, unrelated)
call 3: max_size=9, max_candidates=200000      -> found=False, tested=140575, halt=max_size
```

**`halt_reason: 'max_size'`, not `'budget'`, on the real terminal
call — the search EXHAUSTED THE ENTIRE CANDIDATE TREE at `max_size=9`
(140,575 distinct terms explored) and never found the target, because the
target predicate was never IN that tree to find.** This is stronger
evidence than a `halt=budget` outcome would have been: a budget cap
leaves open the possibility that a bigger budget finds it; an exhausted
tree at the given size proves definitively that no amount of additional
budget would ever find it, because the search space itself does not
contain the needed shape. `140575` matches the `tested` figure
`CEILING_REASSESSMENT_4_PREREG.md` §3.4 originally cited ("140575 tested
under budget") — confirming the population and the exact number are
stable across this whole arc, because nothing that shipped in the
interim (`Sqrt`/`Mod` op-table exposure, the `exclude_ops` call-site
scoping) ever touches `filter_templates_by_size` at all.

**Verdict**: task 412's blocker is a **template-pool shape gap**,
identical in kind to `DictFromPairs`'s own `filter_templates_by_size`
residual and to the SAME gap `BUDGET_EXHAUSTED_SURVEY_RESULTS.md` §5.2
already named (for tasks 75/426, at the earlier baseline) and explicitly
declined to build in that rung ("a materially higher-blast-radius touch
point... deliberately deferred"). It is **NOT** a search-cost/pruning
question — the `CEILING_REASSESSMENT_4` characterization is corrected
here, with the `halt_reason:'max_size'` trace as the direct evidence a
bigger search budget could never have helped.

---

## 5. Mechanism-level disqualification of `SynthesisOperatorShape` for
   this whole cluster — proven by source AND empirically

**What `SynthesisOperatorShape` actually controls.** Read in full:
`ps_select_synthesis_operator_shape`
(`seeds/program_synthesis_grounding.json:482-...`) matches a message,
scores held `SynthesisOperatorShape` nodes by `trigger_tokens` overlap
against `minimum_trigger_matches`, and on a win sets `ps_enum_ops` on the
message. `domains/prog_synthesis.py:1352-1358` (comment: *"The operator
inventory is a graph verdict produced by
`ps_select_synthesis_operator_shape`. This adapter merely transcribes the
held list into the existing Term contract."*) transcribes that verdict
into `spec["ops"]` on the `SynthEnumerate` Term. **This is the ENTIRE
causal chain** — a `SynthesisOperatorShape` can only ever change what
`spec["ops"]` contains.

**What `spec["ops"]` actually does.** It selects/narrows the operand
inventory offered to the GENERAL op-composition grid the search builds
recursively over `OP_TABLE` names. Confirmed by both shipped shapes
themselves: `thresholded_greater_branch`/`thresholded_lower_branch` narrow
to `{Times, Gt, IfThenElse}` / `{Times, Lt, IfThenElse}` — and all three
of those names are ALREADY members of the unconditional `DEFAULT_OPS`
constant (`synth_enumerate.rs:247-249`, `"Plus", "Times", "Minus", "Div",
"Min", "Max", "Abs", "Neg", "Gt", "Lt", "Eq", "IfThenElse"`). The shape's
entire function, by its own two existing instances' design, is reducing
search NOISE within an ALREADY-reachable composition — never granting
reachability to something the typed default couldn't already build.

**Why this cannot touch task 412's (or 75's, or 426's) blocker.**
`filter_templates_by_size`'s template CONTENT (§4 above) is fixed Rust
code, entirely independent of `op_list`'s contents beyond the single
`filter_wanted` boolean gate. `spec["ops"]` and `filter_templates_by_size`
are two disjoint code paths that never communicate. **No possible
`SynthesisOperatorShape` — including one whose `ops` list is EXACTLY
`{FilterList, Mod, Eq}`, the minimal, maximally-favorable narrowing
imaginable for this task — can inject a modulus/parity predicate into the
template pool, because the pool does not consult that list when deciding
what predicates to build.**

**Empirical confirmation, not just source-reading** — the real
`SynthEnumerate` Term, called directly with `ops` narrowed to exactly
`["FilterList", "Mod", "Eq"]` (the most favorable possible mimic of a
`SynthesisOperatorShape` verdict for this task) against task 412's own
revealed rows, `max_size=9`, `max_candidates=200000`:

```python
{'distinct': 16, 'found': False, 'halt_reason': 'max_size',
 'inadmissible': 0, 'pruned_equiv': 1703, 'saturated': False,
 'size': None, 'term': None, 'term_str': None, 'tested': 1719}
```

**`found: False`, exhausting the (now much smaller, 16-distinct-candidate)
tree at `max_size=9` — the narrowed op list makes the search cheaper, not
more capable.** This directly, empirically settles the question: even
the best-case `SynthesisOperatorShape` a human or a mint mechanism could
ever author for this task would ship, fire correctly, narrow the ops
exactly as designed — and STILL leave task 412 exactly as gapped as it is
today, because the fix this task needs lives one layer below where the
shape mechanism operates.

---

## 6. Trigger-word extraction from task 412's prompt

Task 412's prompt: *"Write a python function to remove odd numbers from a
given list."* Following the two shipped shapes' own style (uppercase
content words, filler like "write"/"a"/"to"/"from" excluded — matching
`thresholded_greater_branch`'s own choice to include only semantically
load-bearing tokens):

```
candidate trigger_tokens: REMOVE, ODD, NUMBERS, LIST
```

(`EVEN` is a plausible fifth candidate — the task's own semantics are
"keep the even ones," even though the word never appears in the prompt —
but per the two shipped shapes' own discipline, trigger tokens are drawn
from the PROSE actually present, not from a paraphrase of the task's
semantics, so it is named here but not included in the candidate list
used for the population check below.)

---

## 7. Exhaustive witness check across the full 65-task re-derived Group B
   population — every task checked, not sampled

**Keyword scan** (`odd`, `even`, `remov`, `filter`, `divisibl`, `modulo`,
`parity`, `index` — a superset of task 412's own extracted trigger words
plus every synonym/adjacent concept a modulus-predicate task could
plausibly use) against all 65 prompts, full population, zero sampling:

| task | hits | prompt |
|---|---|---|
| 18 | remov | remove characters from the first string which are present in the second string |
| 75 | divisibl | find tuples which have all elements divisible by k |
| 226 | odd, remov, index | remove the characters which have odd index values of a given string |
| 273 | index | subtracts elements of two tuples with the same index |
| 277 | filter | filters the dictionary to only include entries with values >= n |
| 280 | index | returns index position of element (linear search) |
| 401 | index | index wise addition of tuple elements |
| **412** | **odd, remov** | **(target)** |
| **426** | **odd, filter** | **filter odd numbers** |
| 437 | odd, remov | remove odd characters in a string |
| 445 | index | index wise multiplication of tuple elements |
| 459 | remov | remove uppercase substrings |
| 478 | remov | remove lowercase substrings |

**Every one of these 13 candidates' true op-need, read from its own
ground-truth reference implementation
(`sanitized-mbpp.json`'s own `code` field), not guessed from the prompt:**

| task | true op-need | matches 412's `FilterList`+`Mod`-predicate need? |
|---|---|---|
| 18 | membership filter of one STRING's chars against a second string's char-count table — pure-string spec, `FilterList` isn't even offered (`DEFAULT_STR_OPS` has no `FilterList`, §7.1) | **NO** — different, string-membership shaped, no `Mod` anywhere |
| **75** | `all(ele % K == 0 for ele in sub)` — a nested nested-reduction nested-reduction over TUPLE elements, needs `Mod` inside `tmpl:nested_reduction`'s inner grammar (family 5, §4) | **YES (weaker)** — same underlying fix (widen `filter_templates_by_size`'s `Mod` coverage) but a DIFFERENT specific template family than 412 needs (nested-reduction, not flat item-compare); phrase says "divisible by k," not "odd" |
| 226 | `i % 2 == 0` gating on the STRING INDEX (not the item value), AND needs `FilterList` exposed to string specs at all (currently absent, §7.1) | **NEAR-MISS** — needs `Mod`, but on the INDEX not the item, inside a primitive (indexed-string-filter) that does not exist at all — a strictly LARGER, two-part gap, not the same reachable-with-one-template-addition need as 412 |
| 273 | `zip`-elementwise tuple subtraction — no `Mod` anywhere | **NO** |
| 277 | `Dict` comprehension filtered by `value >= n` — `DictItems`-shaped, const-compare only, no `Mod` | **NO** |
| 280 | linear search returning `(bool, index)` — no filtering predicate at all | **NO** |
| 401 | `zip`-elementwise tuple addition — no `Mod` | **NO** |
| **426** | `filter(lambda x: x % 2 != 0, nums)` — `FilterList(nums, item, Not(Eq(Mod(item,2),0)))`, hand-verified 3/3 including held-out (§7.2) — **the SAME flat item-compare template family (family 1) task 412 needs**, just with `Eq`→`Not(Eq(...))` | **YES (exact)** — identical op-set, identical template family, near-identical prompt |
| 437 | same INDEX-parity shape as 226 (1-indexed `i % 2 == 0`), same two-part gap | **NEAR-MISS** — same as 226 |
| 445 | `zip`-elementwise tuple multiplication — no `Mod` | **NO** |
| 459 | `re.sub('[A-Z]', '', str1)` — regex char-class removal, no `Mod` | **NO** |
| 478 | `re.sub('[a-z]', '', str1)` — regex char-class removal, no `Mod` | **NO** |

**Result: exactly one exact witness (426), one weaker same-mechanism
witness (75, different template family + different phrase), and two
near-misses (226/437, matching phrase but needing a strictly larger,
two-part gap).** No other task among the 65 needs a modulus/parity
predicate inside a `FilterList`-style construct at all — confirmed by
reading every one of the other 52 tasks' ground-truth code (§7.3, full
per-task table) for a `%` operator or equivalent parity/divisibility
test; none appears outside this already-identified 5-task cluster
(75, 226, 412, 426, 437).

### 7.1 `FilterList` is not offered to string-shaped specs at all — checked fresh

`DEFAULT_STR_OPS` (`synth_enumerate.rs:548-552`): `Concat, CaseFold, Eq,
IfThenElse, Replace, Split, StrCount, Capitalize, Reverse, Slice, Str,
MapList, JoinList` — **`FilterList` is absent.** Tasks 226/437 (both
pure string-in/string-out specs, confirmed via `is_listlike`'s own
exclusion of `Value::Str`, `synth_enumerate.rs:517-519`) therefore never
even reach `filter_templates_by_size`'s construction gate
(`filter_wanted` is `False` for them) — their gap is a strict SUPERSET
of task 412's: BOTH "`FilterList` doesn't exist for strings" AND "no
modulus template exists even where `FilterList` IS offered." This
reconfirms, independently and freshly, `BUDGET_EXHAUSTED_SURVEY_PREREG.md`
§5.4's own characterization of 226/437 as "genuinely different, larger,
2-part gap."

A THIRD, previously-uncited task shares this exact string-`FilterList`-
absence half of the gap: task 310 (`tuple(x for x in str1 if not
x.isspace())`) — filtering by a character-class predicate, not parity.
Named here for completeness (it does not use `Mod`, so it is not part of
412's witness set), but it is independent evidence that "`FilterList`
does not exist for strings" is itself a real, recurring (now 3-task: 226,
310, 437) primitive-availability gap, separable from the `Mod`-specific
one.

### 7.2 Task 426, hand-verified end-to-end

```python
FilterList(nums, item, Not(Eq(Mod(item, 2), 0)))
```

```
{'nums': [1,2,3,4,5,6,7,8,9,10]} -> [1,3,5,7,9]   == expected (revealed)
{'nums': [10,20,45,67,84,93]}    -> [45,67,93]    == expected (revealed)
{'nums': [5,7,9,8,6,4,3]}        -> [5,7,9,3]     == expected (HELD-OUT)
```

Same op-set as 412 (`FilterList` + `Eq`/`Not` + `Mod`, family-1 flat
item-compare template), same trigger words ("odd numbers" verbatim in
both prompts; "remove"/"filter" both denote list-filtering), support = 2.
**This is the cleanest possible witness pair by the letter of the test —
and it still does not justify building anything, per §5.**

### 7.3 The remaining 52 tasks — full population, checked (not sampled),
   for completeness and to confirm no `Mod`-shaped need was missed by the
   keyword scan alone

Every one of the 65 Group B tasks' ground-truth `code` was read in full
(not summarized from a prior document) as part of this rung (§1 step 6).
None of the 52 tasks outside the 13-task keyword-hit set above (§7) uses
a `%` operator, a divisibility check, or any parity-shaped predicate in
its reference solution. Their true op-needs, briefly, for the record
(each independently confirmable from `sanitized-mbpp.json`'s own `code`
field, cited in full in this rung's own working notes, not reproduced
verbatim here to keep this document to its own question):

- **A large, independently-notable secondary population: 8 tasks need a
  "zip two lists/tuples elementwise + apply a binary op" primitive that
  does not exist in this engine at all** — `259` (elementwise max),
  `261` (elementwise `//`), `273` (elementwise `-`), `282` (elementwise
  `-`, list variant), `399` (elementwise `^`), `401` (elementwise `+`),
  `429` (elementwise `&`), `445` (elementwise `*`). `BUDGET_EXHAUSTED_
  SURVEY_PREREG.md` §5.4 named only 2 of these (399, 429, "a zip-two-
  lists-elementwise primitive that does not exist AT ALL in this
  engine") — this rung's full-population read generalizes that finding
  to 6 MORE tasks sharing the exact same missing primitive. This is a
  real, ≥2-witness (in fact 8-witness), zero-`Mod` finding, well outside
  this document's own scope (it is a missing-PRIMITIVE gap, category
  (a), not an operator-shape question), named here because it surfaced
  directly from the same full-population read this rung's own house
  discipline required, and left for a future rung.
- The rest (97, 99, 102, 108, 117, 123, 128, 137, 160, 163, 172, 229,
  240, 242, 248, 251, 252, 255, 262, 265, 277, 280, 293, 297, 299, 301,
  305, 307, 308, 310, 390, 391, 395, 408, 411, 415, 417, 419, 421, 422,
  427, 439, 440, 442, 447, 462, 465, 468, 470) each need a genuinely
  different missing primitive or composition (groupby-aggregate, `Range`/
  iteration, regex, trig functions, recursion, dict-depth, format-string
  application, sliding-window, combinations, etc.) — every one already
  either named in `BUDGET_EXHAUSTED_SURVEY_PREREG.md` §5.4's own table or
  `CEILING_REASSESSMENT_4_PREREG.md` §3.4's, or newly identified here as
  its own single-witness item, and NONE of them involves `Mod` or a
  parity/divisibility predicate at all, so none is a candidate witness
  for task 412's specific need regardless of trigger-word overlap.

---

## 8. GO/NO-GO

**NO-GO on building a third `SynthesisOperatorShape`.** Not because no
witness pair exists — one does, cleanly (task 426, support=2, exact
op-set and near-exact phrase match with task 412) — but because the
witness is for a fix the `SynthesisOperatorShape` mechanism is
structurally incapable of delivering, proven both by direct source
reading (§5) and by a live, empirical, most-favorable-case re-run of the
real search (§5's `ops=["FilterList","Mod","Eq"]` result: still
`found: False`). Building the shape would ship correctly, fire correctly
on both 412 and 426's prose, narrow `spec["ops"]` exactly as designed —
and change the MBPP score by exactly zero, because the actual blocker
(no modulus/parity template in `filter_templates_by_size`) lives in a
code path the shape mechanism never touches. This is a sharper, more
precise negative than `PROGRAM_SYNTHESIS_META_SKILL_ASSESSMENT_
PREREG.md`'s own "no data anywhere" verdict — that document could only
observe that no task cited an operator-shape mismatch; this document
shows that even the ONE population that superficially resembles such a
mismatch is not one, once the mechanism is actually checked. Per
CLAUDE.md's Purpose section, this is exactly the kind of null this arc is
supposed to report as a headline finding, not smooth over: the target
(a third shape) was aimed at, missed for a real, localized, generalizable
reason, and the lesson (SynthesisOperatorShape narrows an OP_TABLE-level
grid; FilterList's predicate lives outside that grid entirely) transfers
to every future candidate task this shape mechanism might ever be
proposed for.

**The real fix for task 412 (and 75, 226, 426, 437)** is a widened
`filter_templates_by_size` (a new template family: `item % const CMP
const`, mirroring the existing family-1 `item OP const` construction at
`synth_enumerate.rs:2717-2726`, for tasks 412/426; a `Mod` addition to
family 5's inner grammar for task 75; a `FilterList`-for-strings
exposure plus an indexed variant for 226/437/310). This is a real,
correctness-verified, ≥2-witness candidate — but it is a
missing-primitive/template-pool-shape addition (category (a) in
`PROGRAM_SYNTHESIS_META_SKILL_ASSESSMENT_PREREG.md`'s own taxonomy), the
SAME class of change `BUDGET_EXHAUSTED_SURVEY_RESULTS.md` §5.2 already
named and explicitly declined to build in that rung ("a materially
higher-blast-radius touch point... deliberately deferred") because it
touches the SAME shared `filter_templates_by_size` pool every
list-shaped/string-shaped spec's search would draw from — the same risk
class Rung 1's task-132 regression already measured as fragile. It is
named here, precisely scoped, for a FUTURE, separately-regression-priced
rung — not built in this one, which was scoped to the
`SynthesisOperatorShape` witness question specifically.

---

## 9. What this document does NOT establish

1. Whether widening `filter_templates_by_size` with a modulus template
   would actually convert 412/75/426 within budget once built — genuinely
   uncertain (the same "reach is not conversion" discount this whole arc
   applies everywhere), and NOT this document's question to answer; it
   only establishes that the current template pool categorically cannot
   reach the target, which is a stronger and different claim.
2. Whether such a widening would regress any currently-passing
   `FilterList`-using canary (the SAME risk class Rung 1's task 132
   regression already measured as real for `LIST_EXTRA_OPS`) — not
   priced or built here.
3. A full per-task trace-level diagnosis for all 52 non-keyword-hit Group
   B tasks (§7.3) — each was read for its true op-need from ground-truth
   code (sufficient to rule out a `Mod`/parity match, this document's own
   question), but not independently hand-verified against revealed AND
   held-out rows the way 412/426 were, since that depth was not needed to
   answer the witness question.
4. Whether the 8-task zip-elementwise cluster named incidentally in §7.3
   is itself worth a standalone rung — real, ≥2-witness (8, in fact), but
   entirely out of this document's own scope; named for a future rung's
   benefit, not sized or built here.
5. Whether the Group A / Group B split reported in §3 is complete or
   stable — it is a snapshot against the CURRENT baseline, re-derived
   fresh per this rung's own instruction, but (per the same instruction's
   own observed lesson) has already been shown to churn as future rungs
   land; it should not be quoted as a fixed population by a later rung
   without re-checking.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /tmp/progsyn-operator-shape-witness-check
git log --oneline -1   # on top of main @ 371475d
git status --short     # empty for tracked files — zero code/seed changes
```

Copy the eight gitignored fixtures named in `MODSQRT_SCOPED_FIX_RESULTS.md`
§5.2 (`mbpp_zero_shot_baseline.json`, `prog_construction_scan.json`,
`prog_chunk_mine.json`, `prog_synthesis_battery.json`,
`mbpp_train_diet.json`, `code_synthesis_baseline.json`,
`mbpp_arc3_endgame.json`, `arc4_structural_verdicts.json`) plus
`mbpp_endgame.json` itself from the canonical tree's `results/` before
running anything below.

```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

Task 412 hand-built term (no code change needed):
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

Empirical mechanism disqualification (§5), no code change needed:
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
rows = [{'inputs':{'a':[1,2,3]},'output':[2]},{'inputs':{'a':[2,4,6]},'output':[2,4,6]}]
spec = {'type':'SynthEnumerate','examples':{'type':'Lit','value':rows},
        'ops':{'type':'Lit','value':['FilterList','Mod','Eq']},
        'max_size':9,'max_candidates':200000,'saturate_k':0,'field':''}
print(s._inner.evaluate(spec, {}))
"
```

The full Group A/B trace (§3, scratch, not committed) is
`scratch_trace_groupab.py` in this worktree, run via
`python3 scratch_trace_groupab.py '<json task-id list>'`.
