# Ceiling reassessment 7 — two real ≥2-witness clusters found and hand-verified
   correct, both blocked by a search-cost wall an order of magnitude past
   every prior scoped-`max_candidates` precedent — PREREG (and the whole
   story: NO-GO, investigation only, no code change)

**Date:** 2026-08-16. Base `main @ 03fa65d` ("Model hate -> pity via a
Theory-of-Mind understanding of the target"), verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-7`, branch
`progsyn-ceiling-reassessment-7` — **not merged to `main`, not pushed**,
left for the orchestrator to independently verify. `git status --short` /
`git diff --stat` are both empty in this worktree at the time of writing —
this document is the only artifact this rung produces.

---

**HEADLINE, stated up front: NO-GO on any build this rung — not for lack of
a genuine candidate, but because both real ≥2-witness clusters found this
rung, once hand-verified correct against real fixture rows (including
held-out), turn out to be gated by a search-cost wall that dwarfs every
established scoped-`max_candidates` precedent in this arc (`ZIP_MAX_
CANDIDATES`/`DICT_FILTER_MAX_CANDIDATES`, both `300,000`) by one to two
orders of magnitude, and — for the more promising of the two — even a
budget large enough to eventually reach a "found" answer returns a
SPURIOUS lookup-table overfit before the genuine composition, not the
genuine composition itself.**

- **Cluster 1 — tasks 102/411 ("convert a snake_case string to camelCase"),
  a near-exact duplicate pair (0.93 prompt-similarity).** The exact
  zero-new-`TermNode` composition needed
  (`MapList(Split(a,"_"), item, Capitalize(item))` joined via `JoinList`)
  is not a fresh discovery — it is EXPLICITLY named in this codebase's own
  source comment (`synth_enumerate.rs:3319-3320`, from an earlier rung:
  *"capitalize(item) — size 2 (tasks 102/411, snake->camel via
  `MapList(Split(a,"_"), item, Capitalize(item))`)"*) and hand-verified
  6/6 exact (both revealed rows AND both held-out rows) in this rung
  (§4.1). **Yet the real pipeline's own typed-default search, at the
  CURRENT `max_size=20`/`max_candidates=200,000`, never finds it — and
  raising the candidate budget to `2,000,000` (6.7× the largest existing
  scoped precedent) still does not reliably help**: task 102 is found at
  `tested=1,732,357`, but the term the search actually returns FIRST is
  `(if (a == 'python_program') then 'PythonProgram' else 'PythonLanguage')`
  — a 2-branch literal lookup table that fits both revealed rows by
  memorizing them, is SMALLER (size 7) than the genuine composition
  (size 11), and fails the held-out row. Task 411, same shape, different
  data, does not converge to ANY candidate even at `2,000,000`. This is a
  genuine, previously-uncharacterized instance of the arc's own
  size-ordered-search-meets-few-examples problem (§5).
- **Cluster 2 — tasks 137/442 ("ratio of zeroes to non-zeroes" / "ratio of
  positive numbers"), a real shared-shape pair** (`Count(FilterList(a,
  item, PRED(item))) / (...)`, `PRED` differing per task). Hand-verified
  6/6 exact (§4.2), composed entirely from already-shipped ops (`Count`,
  `FilterList`, `Div`, `Minus`/`Round`). **The real pipeline's own trace
  confirms genuine zero-recall (never finds ANY candidate at any point,
  Group B not Group A — §4.2), and a direct budget sweep on the real
  typed-default op selection does not converge even at `5,000,000`
  candidates (25× the current default, 16.7× the largest scoped
  precedent)** — confirmed via a genuine sweep, not assumed.

**Both clusters are real, correctly diagnosed, zero-new-primitive
compositions — this rung is not reporting "nothing found," it is reporting
"found, verified correct, priced, and the price is too high to responsibly
build blind."** Building either without first solving the underlying
search-cost/Occam-ordering problem risks the exact `ZIP_ELEMENTWISE_
RESULTS.md` outcome (primitive built and verified correct, MEASURED MBPP
gain ZERO) at best, or a genuinely new `accepted_holdout_fail` regression
at worst (Cluster 1's own spurious-lookup finding is a live demonstration
of the failure mode, not a hypothetical one). Per this arc's own repeated
precedent (`MAX_SIZE_SEAM_PRICING_PREREG.md`, `HOLDOUT_FAIL_SURVEY_PREREG.md`,
`STRUCTURAL_REJECT_SURVEY_PREREG.md`), this is reported as the headline
finding rather than built speculatively.

---

## 0. Method — this is the 7th reassessment in the chain

Read in full, as instructed, before any investigation: `CEILING_
REASSESSMENT_6_PREREG/RESULTS.md` (immediate predecessor — the bundled
`DICT_DEFAULT_OPS` widening + `max_size`/`max_candidates` raise, `277`/
`465`, +2/+2/+2), `ZIP_ELEMENTWISE_PREREG/RESULTS.md` +
`ZIPWITH_FOLLOWON_PREREG/RESULTS.md` (the 8-task `ZipWith` cluster and its
own "primitive correct, MBPP gain ZERO" precedent — directly relevant to
this rung's own Cluster 1 finding), `CEILING_REASSESSMENT_5_PREREG/
RESULTS.md` (`tmpl:item_mod_eq`, `412`/`426`), `META_SKILL_ASSESSMENT_
PREREG.md` (category-(a)/(c) framing, not re-litigated), and the three
already-NO-GO'd survey documents (`HOLDOUT_FAIL_SURVEY`, `STRUCTURAL_
REJECT_SURVEY`, `BUDGET_EXHAUSTED_SURVEY`).

This rung additionally read, in full, the four documents chronologically
between `BUDGET_EXHAUSTED_SURVEY` and `CEILING_REASSESSMENT_5` that the
task brief's own baseline citation implied had landed since: `MODSQRT_
SCOPED_FIX_PREREG/RESULTS.md` (the rung that actually BUILT `Mod`/`Sqrt`,
call-site-scoped, +3/+3/0 — `BUDGET_EXHAUSTED_SURVEY`'s own build was
reverted, this later rung is what actually shipped), `OPERATOR_SHAPE_
WITNESS_CHECK_PREREG.md` (task 412's real blocker diagnosed to
`filter_templates_by_size`, not `SynthesisOperatorShape`), `GAMMA_BULK_
TRANSCRIPTION_PREREG/RESULTS.md` (13 Γ productions ported, zero MBPP
change, confirms current `OP_TABLE` has 57 entries), and `RETRIEVAL_
WITNESS_REPIN_PREREG/RESULTS.md` (the `test_retrieval_migrated.py` pin
fix, `412`→`440`, already landed — confirms the task brief's own
collision note is current).

**Confirmed via direct source read (`synth_enumerate.rs:3030-3083`) that
`BUDGET_EXHAUSTED_SURVEY_PREREG.md §5.4`'s own most promising
still-unbuilt candidate — the `filter_templates_by_size` Mod-quantifier
for tasks 75/426 — has PARTIALLY landed since**: `tmpl:item_mod_eq`
(`CEILING_REASSESSMENT_5`) already covers task 426's exact shape (`item %
c == r`, a FLAT per-item modulus test) using the SAME `Mod`/`Eq` ops the
survey named, converting it via a different route than the survey
anticipated. **Task 75's own shape — `Mod` NESTED INSIDE a `Sum` reduction
over a compound (tuple) bound item, `all(ele % K == 0 for ele in sub)` —
remains genuinely unaddressed**: `synth_enumerate.rs:3124-3138`'s own
`tmpl:nested_reduction` comment still reads verbatim *"the pool has {+, -,
*} and no `Mod`, so a DIVISIBILITY quantifier is not reachable here"* —
byte-identical to what the survey quoted a rung ago. Checked directly for
a second live witness of task 75's specific nested-reduction shape across
every currently-failing task ≤510 (§3) — **none found**; task 75 remains
single-witness, below this arc's own ≥2-witness bar, and is not attempted
here (named, consistent with every predecessor rung's own single-variable
discipline).

## 1. Real baseline, confirmed live

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run fresh in this worktree on the
unmodified build (nine gitignored fixtures copied from the canonical
tree's `results/` first, per every predecessor rung's own documented
prerequisite):

```
full:              88/257  p=0.342412  ci=[0.287101, 0.402365]  det_identical=True
content_stripped:  87/257  p=0.338521  ci=[0.283424, 0.398375]  det_identical=True
official:         113/257  p=0.439689  ci=[0.380336, 0.500818]  det_identical=True
```

`head` in the resulting `results/mbpp_endgame.json` reads
`03fa65d11aa5b3f134a47015f79419b8691ae21c`, byte-identical to `git log
--oneline -1 main` — matching the task brief's own cited baseline
(88/87/113) exactly. Saved as `results/mbpp_endgame_BEFORE_this_rung.json`.

## 2. Failure-cause population, re-derived (not assumed)

`scripts/ceiling3_diag_sweep.py` (unmodified on `main`, reused verbatim),
run against this baseline before any code change — **169 rows**, confirmed
exactly against `257 − 88`:

| outcome | n |
|---|---|
| `gapped:enumerate_failed` | **67** |
| `accepted_holdout_fail` | **60** |
| `gapped:property_verdict_reject` | **17** |
| `gapped:structural_verdict_reject` | **14** |
| `gapped:exhausted` | **5** |
| `gapped:no_shape` | **3** |
| `not_recognized` | **1** |
| `runner_exception:ValueError` | **1** |
| `runner_exception:TypeError` | **1** |
| **total** | **169** |

**Reconciles exactly against `CEILING_REASSESSMENT_6_RESULTS.md`'s own
pre-build sweep** (171 rows at the 86/257 baseline): every bucket is
byte-identical except `enumerate_failed`, which shrank by exactly 2
(69→67) — matching reassessment-6's own +2 conversion (277/465, both
`enumerate_failed` before converting). Population is stable and
well-understood.

`gapped:enumerate_failed` (67) splits by `enumerate.tested` against the
budget that actually applied to that call (200,000 default, or 300,000 for
the 3 tasks whose `op_list` triggers the existing `ZIP_MAX_CANDIDATES`/
`DICT_FILTER_MAX_CANDIDATES` scoped raise):

```
budget-exhausted at 200,000:                64
budget-exhausted at the scoped 300,000 ceiling: 3   (308, 391, 408)
saturated (tested < applicable ceiling):     0
```

**This is a genuine, notable shift from every predecessor rung's own
measurement**: reassessment-6's own pre-build sweep found **9** purely
saturated tasks (`97, 117, 277, 299, 305, 417, 462, 465, 470`) — a
population this rung's own re-derivation shows has gone to **zero**. Two
of those nine converted (`277`/`465`, reassessment-6's own build); the
remaining seven are STILL in the current 67-task `enumerate_failed` set
(confirmed: `97, 117, 299, 305, 417, 462, 470` are all present), but ALL
seven now read `tested==200,000` (budget-exhausted) rather than
`tested<200,000` (saturated). **The mechanism is `max_size` itself**:
reassessment-6 raised `run_enumerate`'s hardcoded `max_size` from `9` to
`20` — a search that used to exhaust its own size ceiling before spending
its full candidate budget (`halt_reason:'max_size'`... reported by this
sweep script as "saturated") now has 11 more size classes to explore and
burns the FULL 200,000-candidate budget getting through them, without
finding anything — the search space got bigger, not the reachable answer
set. Every currently-`enumerate_failed` task is genuinely budget-limited
now; there is no more "search already gave up early" sub-population to
target the way reassessment-6 did.

## 3. Hunting for a NEW ≥2-witness cluster — method and result

Two independent methods, both against the full current 67-task `gapped:
enumerate_failed` population (task-id list in the Reproduce section):

**(a) Manual code read.** Every one of the 67 tasks' real ground-truth
`code` field (`tests/fixtures/mbpp/sanitized-mbpp.json`) was read directly.
Grouped by shape: 34 arithmetic/iteration-heavy singletons (many already
named — divisor sums, primality, recurrences, the `Range`/iteration gap
`BUDGET_EXHAUSTED_SURVEY §5.4` already priced as a materially larger,
unbuilt engine change, not re-priced here), several already-named
single-witness residuals (`97`/`117`/`299`/`417`/`462`/`470`, `META_
SKILL_ASSESSMENT_PREREG.md`'s own residual #15), and two genuine
duplicate/near-duplicate PAIRS: `102`/`411` and `137`/`442` (below).

**(b) Programmatic near-duplicate scan.** `difflib.SequenceMatcher` prompt
similarity, all `C(67,2)=2211` pairs, threshold `>0.55` — surfaces every
candidate a human skim could plausibly miss. Top two hits by a wide margin:
`459`/`478` (0.96 similarity — "remove uppercase substrings" / "remove
lowercase substrings") and `102`/`411` (0.93 — the snake_case pair, also
caught by method (a)). `137`/`442` (0.81) is the highest-ranked hit that is
NOT a superficial wording echo of an unrelated task (several 0.75-0.81
hits — `397`/`432`, `389`/`397`, `301`/`430` — share generic phrasing
("find the ... of a given ...") but ZERO shared computational shape,
checked directly against `code`, and are not pursued).

**`459`/`478`** ("remove uppercase/lowercase substrings", `re.sub('[A-Z]',
'', s)` / `re.sub('[a-z]', '', s)`) is a real shared shape, but it needs a
character-level `FilterList` over a string's own characters — `FilterList`
is NOT in `DEFAULT_STR_OPS` (confirmed by direct read of the 13-entry
list, `synth_enumerate.rs:644-648`). This is the SAME "index/character-
predicate filter over a string" gap `BUDGET_EXHAUSTED_SURVEY_PREREG.md
§5.4` already named for `226`/`437` and explicitly declined to build
("genuinely different, larger, 2-part gap... not built") — confirmed still
true and not re-attempted here (widening `DEFAULT_STR_OPS` with `FilterList`
would ALSO widen the branching factor that already blocks Cluster 1 below,
almost certainly making that problem worse, not better — not tested
further given Cluster 1's own measured wall, §5).

The two clusters investigated in full — `102`/`411` and `137`/`442` — are
detailed next.

## 4. Both clusters, hand-verified correct against real fixture rows

### 4.1 Cluster 1 — tasks 102/411, snake_case → camelCase

Real revealed+held-out rows (`domains.mbpp_spec.parse_asserts` +
`split_rows`, protocol `primary`):

```
102: revealed [python_program->PythonProgram, python_language->PythonLanguage]
     held-out  [programming_language->ProgrammingLanguage]
411: revealed [android_tv->AndroidTv, google_pixel->GooglePixel]
     held-out  [apple_watch->AppleWatch]
```

Hand-built term (`Fold(MapList(Split(a,"_"), item, Capitalize(item)),
item2, acc, init="", body=StringConcat(acc,item2))` — the exact expansion
`JoinList`'s own `build_op` decompiles to, per `synth_enumerate.rs:753-759`),
evaluated directly via `substrate_rs.Substrate()._inner.evaluate()`:
**6/6 exact matches, both tasks, including both held-out rows.**

### 4.2 Cluster 2 — tasks 137/442, ratio of a filtered count

```
137 ("ratio of zeroes to non-zeroes"): n1/(n-n1), n1=count(item==0), n=len(a)
  a=[0,1,2,-1,-5,6,0,-3,-2,3,4,6,8]           -> 0.181818  == expected (revealed, tol 0.001)
  a=[2,1,2,-1,-5,6,4,-3,-2,3,4,6,8]           -> 0.0       == expected (revealed)
  a=[2,4,-6,-9,11,-12,14,-5,17]               -> 0.0       == expected (HELD-OUT)

442 ("ratio of positive numbers"): round(n1/n, 2), n1=count(item>0), n=len(a)
  a=[0,1,2,-1,-5,6,0,-3,-2,3,4,6,8]           -> 0.54      == expected (revealed)
  a=[2,1,2,-1,-5,6,4,-3,-2,3,4,6,8]           -> 0.69      == expected (revealed)
  a=[2,4,-6,-9,11,-12,14,-5,17]               -> 0.56      == expected (HELD-OUT)
```

`Div(Count(FilterList(a,item,Eq(item,0))), Minus(Count(a),Count(FilterList(...))))`
for 137, `Round(Div(Count(FilterList(a,item,Gt(item,0))),Count(a)),2)` for
442 — both composed entirely from already-shipped Terms (`Count`,
`FilterList`, `Div`, `Minus`, `Round`, `Eq`, `Gt`), both **6/6 exact
matches including held-out**, hand-evaluated directly.

**Real-pipeline call trace, both clusters** (a logging proxy substituted
for `sub._inner`, mirroring `BUDGET_EXHAUSTED_SURVEY_PREREG.md §4`'s own
method exactly): for all four tasks (`102`, `411`, `137`, `442`), every
`SynthEnumerate` call in the real `synthesize_from_request` trace shows
`found=False` — **zero find-then-exclude-then-retry cycles anywhere**.
This is genuine Group-B zero-recall (per `BUDGET_EXHAUSTED_SURVEY`'s own
A/B taxonomy), not the Group-A "cheap wrong answer found and correctly
rejected" pattern that document already NO-GO'd — confirmed directly, not
assumed.

## 5. Why NO-GO: the price, measured not guessed

### 5.1 Cluster 1 — the search-cost wall, AND a spurious-accept risk

A direct `max_candidates` sweep on the real typed-default op selection
(`ops` omitted — reassessment-6's own §5.2 finding that the internally-
selected op list explores a genuinely different, larger space than the
same names passed explicitly is reused here, not re-derived), task 102's
real revealed rows:

```
max_candidates    400,000    800,000   1,500,000   3,000,000
found             False      False     False       True (tested=1,732,357)
```

**The candidate the search actually returns is `(if (a ==
'python_program') then 'PythonProgram' else 'PythonLanguage')`** — a
2-branch literal-lookup `IfThenElse`, size 7, smaller than the genuine
size-11 `Fold`/`MapList`/`Split`/`Capitalize` composition — confirmed by
directly reading `term_str` off the returned candidate and evaluating it
against the held-out row (`programming_language` → the WRONG branch,
`'PythonLanguage'`, fails). Task 411, same shape, does not converge to
ANY candidate even at `2,000,000`. **A parallel sweep of all 9
currently-failing string-shaped tasks (`18, 102, 226, 396, 411, 427, 437,
459, 478`) at `max_candidates=2,000,000` finds a candidate for 5 of them
(`102, 396, 427, 437, 478`) — and every single one of the 5 returned
solutions is the SAME degenerate row-by-row `IfThenElse` lookup shape,
confirmed by direct held-out re-evaluation of each: ALL FIVE fail their
held-out row.** With only 2 revealed rows (this arc's `primary` protocol),
a 2-branch literal-equality lookup table is ALWAYS a valid fit for the
revealed rows and is smaller than almost any genuine multi-step string
transform — so size-ordered (Occam) search finds it, or exhausts trying
every combination at that size class, well before it can ever reach a
correct composition. **Raising the budget high enough to reach the GENUINE
answer (unmeasured upper bound — not found even at `2,000,000` for either
task in this cluster) would first walk through this same degenerate-lookup
region for every other string-shaped task in the corpus, at a scoped
budget an order of magnitude past any existing precedent** — the risk is
not hypothetical, it is directly measured, 5 out of 5 times, in this
section.

### 5.2 Cluster 2 — the search-cost wall alone (no spurious accept observed, but no convergence either)

```
max_candidates     200,000   300,000   400,000   600,000   900,000   1,500,000   3,000,000   5,000,000
found (task 137)   False     False     False     False     False     False       False       False
```

Not found at `5,000,000` — 16.7× `ZIP_MAX_CANDIDATES`/`DICT_FILTER_MAX_
CANDIDATES`'s own already-proven `300,000`, 25× the engine's own default.
Wall-clock cost is cheap in isolation (Rust: 5,000,000 candidates evaluate
in ~8.6s for this one spec), so the blocker is not runtime — it is that
this rung has no principled stopping point for "how much further" once the
established 300,000 precedent is this far exceeded with still no
convergence, and no evidence (unlike Cluster 1) of what shape the eventual
answer, if any exists within reach, would take.

### 5.3 The generalizable finding

Both clusters are a THIRD, previously-uncharacterized instance of the same
underlying mechanism `MODSQRT_SCOPED_FIX_RESULTS.md §3` first named for
task 59 ("candidate discovery ORDER shifting pulls a WRONG answer INTO
budget") and `test_prog_synthesis_battery_migrated.py`'s own pre-existing
comment already documents corpus-wide: **with only 2 revealed rows
(`primary` protocol), the search space of "small, wrong, literal-lookup"
candidates is large enough on its own to consume any currently-affordable
candidate budget before a genuinely correct, larger composition is ever
reached** — and reassessment-6's own `max_size` 9→20 raise (§2 above) has
made this WORSE for the whole `enumerate_failed` bucket, not better (the
saturated→budget-exhausted shift measured in §2). This is not the same
mechanism as `HOLDOUT_FAIL_SURVEY`'s own finding (idiosyncratic ALREADY-
ACCEPTED wrong programs, no shared fix) — it is a DIFFERENT, HERE
newly-measured mechanism: genuinely gapped tasks whose correct answer
is real, verifiable, and zero-new-primitive, but is Occam-outranked by an
enormous field of small literal-lookup wrong answers that must be
exhausted first.

## 6. What this document does NOT establish

1. Whether EITHER cluster's genuine composition is reachable at ANY
   candidate budget at all — Cluster 1 task 411 and Cluster 2 (both tasks)
   were not found even at 2,000,000 / 5,000,000 respectively; this
   document did not sweep indefinitely (a responsible stopping point, not
   a proof of unreachability).
2. Whether a DIFFERENT mechanism — e.g., suppressing literal-lookup
   `IfThenElse(Eq(Var,Lit),...)` candidates specifically from the general
   op-composition grid, or requiring 3+ revealed rows before accepting an
   `IfThenElse`-over-input-equality candidate at all — would resolve this
   more cheaply than a raw budget raise. This is a real, plausible,
   entirely unpriced idea for a future rung (it would need its own
   regression-risk pricing against every OTHER task whose genuine answer
   legitimately IS a small conditional), not attempted here.
3. Whether `459`/`478` (character-filter string pair) or `226`/`437`
   (index-parity string pair, already named by `BUDGET_EXHAUSTED_SURVEY`)
   would hit the SAME search-cost wall if `FilterList` were added to
   `DEFAULT_STR_OPS` — plausible by the same mechanism (§5.3), not
   measured.
4. Task 75 (nested-reduction `Mod`, single witness) — confirmed still
   unbuilt and still genuinely single-witness on the current population
   (§0), not attempted, matching this arc's own bar.
5. The `accepted_holdout_fail` (60), `structural_verdict_reject` (14),
   `property_verdict_reject` (17), `exhausted` (5), `no_shape` (3) buckets
   were read for an obvious NEW cross-cutting pattern (prompts printed and
   scanned directly, §3's method (a) applied at lower depth) and none was
   found beyond what predecessor surveys already characterized — this is
   a targeted look for population SHIFT, not a wholesale re-survey (per
   the task brief's own instruction), and should not be read as
   re-confirming those documents' own NO-GOs to their original standard of
   rigor.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 7. GO/NO-GO

**NO-GO on any build this rung.** Two real, hand-verified-correct,
zero-new-`TermNode`, ≥2-witness clusters were found — the highest bar this
arc's own method sets — and both are honestly priced as currently too
expensive/uncertain to build responsibly: Cluster 1 (`102`/`411`) risks
manufacturing spurious `accepted_holdout_fail` regressions (directly
demonstrated, 5/5, on a related probe) rather than genuine passes at any
budget tested; Cluster 2 (`137`/`442`) simply does not converge within
16.7× the largest existing scoped-budget precedent. Building either
speculatively, without first resolving the underlying Occam-ordering
problem named in §5.3, would repeat `ZIP_ELEMENTWISE_RESULTS.md`'s own
"primitive correct, MBPP gain ZERO" outcome at best. No `.rs` or `.py`
production file is touched by this rung. `results/mbpp_endgame.json` /
`results/ceiling3_diag_sweep.json` reflect the unmodified baseline
re-measurement; no `_AFTER` artifacts exist because nothing was built.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-7
git log --oneline -1   # on top of main @ 03fa65d, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

Full `gapped:enumerate_failed` (67) task-id list:
`14, 18, 75, 97, 99, 102, 103, 108, 117, 123, 128, 137, 160, 163, 165, 172,
226, 229, 238, 240, 242, 248, 251, 252, 255, 262, 265, 280, 293, 297, 299,
300, 301, 304, 305, 307, 308, 310, 389, 390, 391, 392, 395, 396, 397, 408,
411, 414, 415, 417, 419, 421, 422, 427, 430, 432, 437, 439, 440, 442, 447,
453, 459, 462, 468, 470, 478`.

Cluster 1/2 hand-verification and budget sweeps (no code change needed,
pre-build engine):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
# Cluster 1, task 102: MapList(Split(a,'_'),item,Capitalize(item)) joined
split = {'type':'Split','text':{'type':'Var','name':'a'},'sep':{'type':'Lit','value':'_'}}
mapl = {'type':'MapList','source':split,'var_name':'item','value':{'type':'Capitalize','text':{'type':'Var','name':'item'}}}
fold = {'type':'Fold','source':mapl,'var_name':'item2','acc_name':'acc','init':{'type':'Lit','value':''},
        'body':{'type':'StringConcat','parts':[{'type':'Var','name':'acc'},{'type':'Var','name':'item2'}]}}
for a,exp in [('python_program','PythonProgram'),('python_language','PythonLanguage'),('programming_language','ProgrammingLanguage')]:
    print(a, s._inner.evaluate(fold, {'a': a}), exp)
# Cluster 2, task 137: Div(Count(FilterList(a,item,Eq(item,0))), Minus(Count(a), n1))
n1 = {'type':'Count','source':{'type':'FilterList','source':{'type':'Var','name':'a'},'var_name':'item',
      'predicate':{'type':'Eq','a':{'type':'Var','name':'item'},'b':{'type':'Lit','value':0}}}}
n = {'type':'Count','source':{'type':'Var','name':'a'}}
div = {'type':'Div','a':n1,'b':{'type':'Minus','a':n,'b':n1}}
for a,exp in [([0,1,2,-1,-5,6,0,-3,-2,3,4,6,8], 0.181818), ([2,4,-6,-9,11,-12,14,-5,17], 0.0)]:
    print(a, s._inner.evaluate(div, {'a': a}), exp)
"
```

The call-trace (§4.2, Group-A/B check) is reproducible by substituting a
logging proxy for `sub._inner`, mirroring `BUDGET_EXHAUSTED_SURVEY_
PREREG.md §4`'s own documented method exactly, then calling
`domains.prog_synthesis.synthesize_from_request` for tasks `102, 411, 137,
442`.
