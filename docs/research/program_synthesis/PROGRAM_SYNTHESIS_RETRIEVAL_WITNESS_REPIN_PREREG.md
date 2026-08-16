# Retrieval witness re-pin (412 → 440) — PREREG

**Date:** 2026-08-16. Base `main @ aed1d12` ("Build hate attribution: outward
attribution-locus residual + stability gate"), verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/progsyn-retrieval-witness-repin`,
branch `progsyn-retrieval-witness-repin` — not merged to `main`, not pushed,
left for the orchestrator to independently verify and merge.

**This is a pure test-fixture task, scoped to exactly one file:
`tests/test_retrieval_migrated.py`.** No Rust changes. No MBPP battery run
(read-only artifacts are copied from the canonical `results/` tree, per
every predecessor rung's own documented prerequisite for a fresh worktree —
`results/` is gitignored). A sibling agent is running, in parallel, a fresh
MBPP ceiling reassessment that may touch `runners/dsl/src/synth_enumerate.rs`
or seed/battery files, but has been told to defer this exact test file to
this rung.

**Headline finding, stated up front: task 412 ("remove odd numbers") no
longer stands for "retrieval finds nothing" — `PROGRAM_SYNTHESIS_CEILING_
REASSESSMENT_5` (already merged, `_KNOWN_CEILING_REASSESSMENT_5_DRIFT` in
the test file itself) converted it via a new `tmpl:item_mod_eq` `FilterList`
predicate family. Task 440 ("find the first adverb and their positions in a
given sentence") is the new witness: `status == "gapped"`, `rung == "none"`,
`attempts == 0.0`, confirmed LIVE three times in a row (not inherited from
any stale document) against the current engine. It is chosen over 46 other
live-confirmed candidates specifically because its blocker — regex-shaped
pattern matching (`re.finditer(r"\w+ly", text)`, per the fixture's own
reference implementation) — is the one missing-primitive class this arc's
own prior research (`PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md`) has already
named and explicitly excluded from scope as "a genuinely new object model,"
unlike every predecessor witness's blocker (394/106/412), each of which was
a single arithmetic/list-op composition gap inside the SAME Term family
that ordinary widenings already reach.**

---

## 1. Why task 412 stopped standing for "finds nothing"

`tests/test_retrieval_migrated.py::test_ladder_gap_spends_no_attempt_when_
retrieval_finds_nothing`'s own docstring records two prior re-pins (394 →
106, arc4 S4; 106 → 412, arc6 tier 0), each because a widening made the
prior witness newly findable. `_KNOWN_CEILING_REASSESSMENT_5_DRIFT` (already
in the file, dated 2026-08-16, landed and merged) records the third: a new
`tmpl:item_mod_eq` `FilterList` predicate family (`item % c == r` /
`!= r`, composed from already-shipped `Mod`/`Eq`/`Not`) makes the enumerator
propose `FilterList(a, item, Eq(Mod(item,2),0))` for task 412, which
retrieval's rung d now accepts and which passes its held-out row. That
comment explicitly says the re-pin itself was "left for a follow-on rung" —
this is that follow-on rung.

Confirmed by running the suite fresh in this worktree before any edit
(fixture artifacts — `arc4_structural_verdicts.json`, `mbpp_endgame.json`,
`mbpp_zero_shot_baseline.json`, `prog_construction_scan.json`,
`prog_chunk_mine.json` — copied from the canonical tree's `results/` first,
all gitignored, matching every predecessor rung's documented prerequisite):

```
tests/test_retrieval_migrated.py: 2 failed, 31 passed
  FAILED test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing
  FAILED test_ceiling_task_reproduces_measured_outcome_live[238]
```

`test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing` fails with
`out["status"] == "accepted"` (task 412 is genuinely accepted now, matching
`_KNOWN_CEILING_REASSESSMENT_5_DRIFT` exactly) instead of the pinned
`"gapped"`. `test_ceiling_task_reproduces_measured_outcome_live[238]` fails
with `out["gap_reason"] == 'enumerate_failed'` vs the pinned
`'structural_verdict_reject'` — this is investigated separately in §5 below
and is NOT this rung's target.

---

## 2. Search method — outside the fixed `CEILING_TASK_IDS` list

None of the 12 `CEILING_TASK_IDS` (105, 106, 115, 138, 238, 242, 284, 394,
405, 406, 412, 414) currently stand for "finds nothing" — every one of
them has been resolved, superseded, or was never a `rung: none` case to
begin with (confirmed by reading `MEASURED_OUTCOMES` and the five
`_KNOWN_*_DRIFT` dicts already in the file). The new witness has to come
from the wider MBPP population.

`scripts/ceiling3_diag_sweep.py` (unmodified, reused verbatim, its own
gitignored artifact dependency `prog_chunk_mine.json` also copied from the
canonical tree) was re-run fresh in this worktree, producing
`results/ceiling3_diag_sweep.json` — 171 rows, one per currently-failing
`full`-arm runnable task. Breaking down by `(status, gap_reason,
retrieval.rung_reached)`:

| status | gap_reason | rung | n |
|---|---|---|---|
| gapped | enumerate_failed | none | 68 |
| accepted (holdout fail) | — | none | 35 |
| accepted (holdout fail) | — | d | 21 |
| gapped | property_verdict_reject | d | 15 |
| gapped | structural_verdict_reject | d | 12 |
| gapped | exhausted | none | 4 |
| accepted (holdout fail) | — | c | 3 |
| gapped | no_shape | none | 3 |
| gapped | property_verdict_reject | a | 2 |
| runner_exception | — | — | 2 |
| (other, singletons) | | | 5 |

**Important caveat found and corrected during this rung:** `ceiling3_diag_
sweep.py` boots via `boot_full()` (`ensure_program_synthesis` +
`pcg.install_mined_chunks` + `pcg.ensure_mbpp_train_diet`), which is a
DIFFERENT, heavier boot than the test file's own `boot()` (plain
`ensure_program_synthesis` only, no mined chunks, no train diet). The diag
sweep is used here ONLY to shortlist candidates; every number in this
document that the test itself depends on (rung/attempts under `_run_
task_live`) is independently re-verified below using the test's own `boot()`
+ `_run_task_live`, never taken from the diag sweep directly.

Live re-verification (test's own `boot()`/`_run_task_live`, script in
`/tmp/verify_all_ef.py` during this rung) of all 68 `enumerate_failed`/`none`
candidates found **47 that genuinely satisfy `status == "gapped"`, `rung ==
"none"`, `attempts == 0.0` under the test's own boot path** — the other 21
spend nonzero attempts or reach some other rung under the lighter boot
(the heavier `boot_full()` mined-chunk/train-diet install changes which
codebook constructions are even eligible, so the two boots genuinely
diverge on some tasks). The `no_shape`/`exhausted` categories were checked
too and REJECTED as a class: under the test's own plain `boot()`, every
`no_shape`/`exhausted` sample checked (77, 126, 164, 222, 228, 256, 295)
spends `attempts` of 2.0 or 4.0 — those gap reasons are reached only AFTER
at least one attempt, which directly disqualifies them against this test's
own `attempts == 0.0` assertion (HR2, "a failing candidate never touches
`ps_attempts`" — that guarantee is specifically about the case where
`ps_attempts` is never touched at all, which `no_shape`/`exhausted` are not).

The 47 confirmed candidates (task ids): 18, 75, 97, 99, 102, 108, 117, 128,
137, 160, 163, 226, 229, 240, 251, 252, 255, 262, 265, 277, 280, 293, 297,
299, 301, 305, 307, 308, 310, 390, 391, 395, 408, 411, 417, 421, 427, 437,
439, 440, 442, 447, 459, 462, 465, 470, 478.

---

## 3. Choosing the witness — robustness reasoning

The prior two re-pins (394 → 106, 106 → 412) were BOTH closed by adding a
new composition INSIDE the DSL's existing arithmetic/list Term algebra
(`Fold`+`Append` for tuple/list concat; `Mod`+`Eq`+`Not` for a modulus
predicate) — narrow, single-primitive-family widenings that this arc has
now landed three times in a row on exactly this kind of gap. Any witness
whose blocker is "one more predicate/op composition away" is a poor choice
— it is likely to be the NEXT thing an ordinary widening closes, repeating
the churn this test has already been through twice.

Scanning the 47 candidates' prompts and reference implementations
(`tests/fixtures/mbpp/sanitized-mbpp.json`) for the STRUCTURAL CLASS of
each blocker (not just "a token/op is missing"):

- Several (99 decimal→binary, 301 dict depth, 255/462 combinatorial
  generation, 308 top-k cross product) need a different SHAPE of
  computation (unbounded iteration, recursion over nested structure,
  exponential enumeration) rather than a new leaf op — plausible future
  targets, but harder to rule out as "one more template family away"
  the same way 412 turned out to be.
- **Task 440 ("find the first adverb and their positions in a given
  sentence")** is qualitatively different: its own reference implementation
  (`tests/fixtures/mbpp/sanitized-mbpp.json`, `task_id == 440`) is

  ```python
  import re
  def find_adverb_position(text):
   for m in re.finditer(r"\w+ly", text):
      return (m.start(), m.end(), m.group(0))
  ```

  This needs a `re.Match` OBJECT MODEL (pattern search over a string,
  match-span extraction) that has no analogue anywhere in `OP_TABLE`
  (`runners/dsl/src/synth_enumerate.rs` — confirmed by grep: the table has
  arithmetic/comparison ops, `Str`/`Split`/`Replace`/`Slice`/`CaseFold`
  string ops, `Sort`/`Filter`/`Fold`/list ops, `Mod`/`Sqrt` — nothing
  resembling pattern search or regex at all).

This is not a fresh guess — this project's OWN prior population research
already named and priced exactly this gap:

- `PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md` (an early, wide MBPP-population
  histogram of missing capabilities) names `regex` as the single LARGEST
  unrestricted-curve capability family (26 tasks, tied for the #1 step) and
  explicitly EXCLUDES it from the arc's planning scope: *"regex is a
  genuinely new object model (match objects, `re.Match` methods),
  explicitly out of the arc's scope (plan §1, risk #5)"* — every
  Q1-scoped ceiling curve in that document treats regex-needing tasks as
  permanently unreachable by the family of widenings this arc actually
  builds.
- `PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md` (the same-day
  predecessor to the rung that converted 412) independently classifies
  task 440 into its own residual bucket of tasks that "each need a
  genuinely different missing primitive or composition (groupby-aggregate,
  `Range`/iteration, **regex**, trig functions, recursion, dict-depth,
  format-string application, sliding-window, combinations, etc.)" —
  grouping 440 alongside the SAME excluded family, independently, from a
  different angle (an operator-shape survey, not a capability histogram).

**The reasoning, stated explicitly, per the task brief's own request (not
provable with certainty, but the best available evidence in this
codebase):** every widening this arc has actually built and landed —
`ConcatList` (Fold+Append), `tmpl:item_mod_eq` (Mod+Eq+Not), the earlier
`IntersectAll`/`UnionAll`/`DictFromPairs`/`ZipWith` additions — has been a
NEW COMPOSITION drawn from the SAME arithmetic/list/string Term family
already in `OP_TABLE`. Regex pattern-matching is not a composition of that
family; it requires a genuinely different value type (a match object) and
search semantics (scanning a string against a pattern, extracting spans).
The project's own research has already looked at this exact gap TWICE,
independently, and both times classified it as out of the current
architecture's reach rather than "one more template away." That is why
task 440 is chosen as the more durable witness over the other 46
candidates, even though none of them is provably permanent.

---

## 4. Live confirmation (the test's own `boot()`/`_run_task_live` path)

Run three times in a row inside this worktree, script mirrors
`_run_task_live` verbatim:

```
revealed: [{'inputs': {'a': 'clearly!! we can see the sky'}, 'expected': (0, 7, 'clearly')},
           {'inputs': {'a': 'seriously!! there are many roses'}, 'expected': (0, 9, 'seriously')}]
held_out: [{'inputs': {'a': 'unfortunately!! sita is going to home'}, 'expected': (0, 13, 'unfortunately')}]

run 0: status=gapped gap_reason=enumerate_failed attempts=0.0
       retrieval={'rung_reached': 'none', 'n_candidates': 5.0, 'accept_task_id': None,
                  'accept_perm': None, 'accept_edit': None}
run 1: identical
run 2: identical
```

Byte-identical across all three runs — deterministic, `rung == "none"`,
`attempts == 0.0`, `status == "gapped"`, exactly what the test needs to
assert. Retrieval DID score 5 candidates into its pool (`n_candidates: 5`)
but never accepted any of them at any rung — confirming the ladder
genuinely never proposes anything usable, not merely that the pool was
empty. `enumerate` independently exhausted its full search budget
(`tested: 200000` per the diag-sweep row) without finding a fit either —
both the retrieval side and the plain-enumerate side of the ladder come up
empty, which is the strongest form of "genuinely finds nothing" available
in this engine.

---

## 5. Task 238 — confirmed still the same pre-existing, unrelated drift

The task brief asks to confirm `test_ceiling_task_reproduces_measured_
outcome_live[238]`'s failure is still the SAME pre-existing residual
already confirmed by three prior rungs (`MODSQRT_SCOPED_FIX`,
`ZIPWITH_FOLLOWON`, `CEILING_REASSESSMENT_5`), not something new, and to
leave it alone.

`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_5_RESULTS.md` §6.5 already
documents this exact drift on `main @ 84cd082`: the test pins
`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT[238]`'s `gap_reason ==
'structural_verdict_reject'`, but live it reads `'enumerate_failed'` — and
that document traces the cause to task 238 being "a budget-exhausted,
non-`FilterList` task" whose live outcome is unrelated to any of the
FilterList-predicate/Mod work landing around it, confirmed unchanged since
`PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON_RESULTS.md` §5.2 one rung earlier.

Re-run fresh in THIS worktree, on `main @ aed1d12` (one commit further than
`84cd082`), before any edit in this rung:

```
FAILED test_ceiling_task_reproduces_measured_outcome_live[238]
  AssertionError: assert 'enumerate_failed' == 'structural_verdict_reject'
```

Byte-identical failure mode, same field, same values, on the current tip —
confirmed still present, still the same known residual, unchanged across
at least four rungs now. Per the task brief, this is explicitly OUT OF
SCOPE for this rung and is left untouched.

---

## 6. Planned change

`tests/test_retrieval_migrated.py::test_ladder_gap_spends_no_attempt_when_
retrieval_finds_nothing`:

- Re-point `_run_task_live(by_id[412])` → `_run_task_live(by_id[440])`.
- Rewrite the docstring following the exact discipline of the 394→106 and
  106→412 updates already in the file: explain why 412 stopped standing
  for "finds nothing" (cite `_KNOWN_CEILING_REASSESSMENT_5_DRIFT`), confirm
  440's live outcome, and state the robustness reasoning from §3 above
  (including the explicit warning for whoever re-pins this next: a re-pin
  is only ever valid if the NEW task's `rung == "none"` is confirmed LIVE).

No other test in the file changes. No production code changes.

---

## 7. Verification plan

- `tests/test_retrieval_migrated.py` in full, expect all green except the
  pre-existing `test_ceiling_task_reproduces_measured_outcome_live[238]`
  failure (§5).
- No Rust rebuild, no MBPP battery run.
- Commit in this worktree; do not merge, do not push.
