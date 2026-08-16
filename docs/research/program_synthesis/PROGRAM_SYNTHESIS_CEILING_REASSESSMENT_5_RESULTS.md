# Ceiling reassessment 5 — `tmpl:item_mod_eq` — RESULTS: GO, +2/+2/+2, zero regression

Prereg: `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_5_PREREG.md`, same
worktree/branch. Base `main @ 84cd082` ("Merge progsyn-zipwith-followon:
D2 binder-recognition bugfix + scoped max_candidates raise -- +8/+8/+8,
complete ZipWith cluster converted"), verified fresh via `git log --oneline
-1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-5`,
branch `progsyn-ceiling-reassessment-5` — **not merged to `main`, not
pushed**, left for the orchestrator to independently verify and merge.

---

## Headline

**GO. Full paired MBPP battery: `full` 84→86/257, `content_stripped`
83→85/257, `official` 109→111/257 — all THREE arms gain the EXACT SAME
2-task set (`412, 426`), zero lost on any arm.** A single, zero-new-`TermNode`
addition to `filter_templates_by_size` (the fixed template pool
`FilterList`'s predicate argument is drawn from): a new `item % c == r` /
`item % c != r` family, composed entirely from already-shipped Terms
(`Mod`, `Eq`, `Not`, `Var`, `Lit`), gated behind the existing `filter_wanted`
flag exactly like every other template family in this function. This is
the exact candidate the immediate-predecessor investigation-only rung
(`PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md`, same-day,
un-merged, `main @ 371475d`) diagnosed and named but did not build.

**Rust suite: 778/0/4, byte-identical to baseline. Named 9-file suite: 3
failed / 241 passed, exactly the 3 known pre-existing pin-drift failures,
nothing new. `test_retrieval_migrated.py`: 3 failed / 30 passed — 1 known
pre-existing (task 238) plus 2 new failures BOTH directly and solely
explained by task 412's own conversion (the point of this rung), isolated
below, not a regression. `test_reject_informs_repair_migrated.py`: exactly
its 4 known pre-existing failures / 18 passed.**

---

## 1. Re-deriving the population — confirmed against the current baseline

Fresh battery run, this worktree, before any code change:

```
full:              84/257  p=0.326848  ci=[0.272418, 0.386379]  det_identical=True
content_stripped:  83/257  p=0.322957  ci=[0.268758, 0.382371]  det_identical=True
official:         109/257  p=0.424125  ci=[0.365256, 0.485227]  det_identical=True
```

Byte-identical to the task brief's own cited baseline (84/83/109) and to
`results/mbpp_endgame.json`'s `head` field (`84cd0826b5298fa05a83a1be979
e9407876c6dd2`, matching `git log --oneline -1 main`). Saved as
`results/mbpp_endgame_BEFORE_this_rung.json`.

`scripts/ceiling3_diag_sweep.py` (unmodified on `main`, reused verbatim),
run against this baseline before any code change — 173 rows
(257−84), the full failure-cause breakdown:

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

**Reconciles exactly against `PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_
CHECK_PREREG.md`'s own re-derivation** (measured at the pre-ZipWith
baseline of 76/257): every bucket is byte-identical except `enumerate_
failed`, which shrank by exactly 8 (79→71) — matching the ZipWith-followon
rung's own +8 conversion exactly. `gapped:enumerate_failed` splits:
budget-exhausted (`tested==200000`) = 58, saturated (`tested<200000`) = 13
(`97, 117, 277, 299, 305, 308, 391, 408, 412, 417, 462, 465, 470` — three of
these, 308/391/408, actually read `tested=300000`, the ZipWith-followon
rung's own scoped budget raise, still architecturally a budget-style halt).

The `accepted_holdout_fail`/`*_verdict_reject` population (91 tasks) is the
same population already sized and decisively NO-GO'd by `PROGRAM_
SYNTHESIS_RETRIEVAL_FALLTHROUGH_RESULTS.md` and `PROGRAM_SYNTHESIS_
STRUCTURAL_REJECT_SURVEY_PREREG.md`/`PROPERTY_REJECT_SURVEY_RESULTS.md` —
not re-investigated here, per the task brief's own instruction not to
re-litigate settled NO-GOs.

---

## 2. The target — task 412's real blocker, diagnosed by the immediate
   predecessor rung, re-verified fresh here before building

Full mechanism (the `filter_templates_by_size` vs `OP_TABLE` disjoint-code-
path finding, the live `halt_reason: 'max_size'` trace, the empirical
`SynthesisOperatorShape` disqualification, the exhaustive 65-task witness
population check) is in `PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_
CHECK_PREREG.md` §4-7 — not duplicated here; summarized in this rung's own
PREREG §3. What was independently re-verified in THIS rung before writing
any code:

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
document. `term_json` (this module's own local Term-to-JSON renderer used
only for the search's winning-candidate return fields) was confirmed, by
grep, to already have match arms for `Eq`/`Not`/`Mod`/`Var`/`Lit` before
writing any code — unlike the `DictFromPairs` rung, which found and had to
fix a real missing-arm panic (`MkDict`) in this exact renderer, no such gap
existed here.

---

## 3. The fix, as built

`runners/dsl/src/synth_enumerate.rs`, inside the existing `if filter_wanted
{ ... }` block that builds `filter_templates_by_size`'s families, a new
family `tmpl:item_mod_eq` inserted between family 1's `scalar_vars` loop
and `tmpl:item_in_listvar`:

- `c`/`r` drawn from the same `numeric_consts` pool every other family
  already uses (spec-derived, never a benchmark-specific literal).
- Restricted to `c > 1` (mod-by-0/1 is degenerate) and `0 <= r < c` (the
  exact range this engine's own `Mod`'s `rem_euclid` semantics can ever
  produce for a positive modulus, confirmed by reading `term.rs`'s `Mod`
  evaluator) — a semantic constraint, not a benchmark-fitted one.
- Only `Eq`/`Not(Eq(...))` offered (not the full 5-way `CMPS` family 1
  uses) — a modulus compared via `Gt`/`Lt` matches no surveyed MBPP task
  (confirmed by the predecessor rung's own exhaustive population read),
  and omitting it keeps the addition's blast radius to exactly the two
  forms 412/426 need, the same "only build what's witnessed" discipline
  `ZIP_ELEMENTWISE_OP_NAMES`'s own fixed 7-op inventory already uses.
- `item % c == r` — size 5, pushed to `filter_templates_by_size[5]`.
- `item % c != r` — size 6 (`Not` wrapping the above), pushed to
  `filter_templates_by_size[6]` — the same "+1 for the negated form" idiom
  the immediately-following `tmpl:item_in_listvar`/`not in` family uses.

**Zero new `TermNode` variant.** For task 412/426's own default const pool
`{0,1,2,-1}`, only `c=2` satisfies `c>1`, and `r∈{0,1}` both satisfy
`0<=r<2` — exactly 4 new template entries (2 at size 5, 2 at size 6), not
a combinatorial explosion, because the `0<=r<c` guard prunes almost all of
the naive `|consts|²` cross product before it is ever built.

---

## 4. Verified post-build — the real pipeline, not a hand-built term

```
task 412: status=accepted, holdout_all_ok=True
  ir: FilterList(a, item, Eq(Mod(item,2), 0))
task 426: status=accepted, holdout_all_ok=True
  ir: FilterList(nums, item, Eq(Mod(item,2), 1))
```

Notably, task 426's real search found `Eq(Mod(item,2),1)` — NOT the
`Not(Eq(Mod(item,2),0))` form hand-verified in §2 — because `r` ranges over
`{0,1}` for `c=2`, and `Eq(mod,1)` is the exact size-5 equivalent of "odd",
smaller than the size-6 `Not`-wrapped form. The search finds the smaller,
simpler, semantically-equivalent expression on its own — confirming the
template family is doing real, general search, not merely reproducing the
one hand-verified witness term.

Both tasks previously showed `construction=None,
gap_reason='enumerate_failed', tested=200000` (426) / `tested=140575,
halt=max_size` (412) on the unmodified engine.

---

## 5. Full paired MBPP battery — exact task-id set diffs

```
                    before (k/n)          after (k/n)           det_identical
full:               84/257  p=0.326848    86/257  p=0.33463     True / True
content_stripped:   83/257  p=0.322957    85/257  p=0.330739    True / True
official:          109/257  p=0.424125   111/257  p=0.431907    True / True
```

**Exact task-id set diff, all three arms:**

| arm | gained | lost |
|---|---|---|
| `full` | `{412, 426}` | `{}` |
| `content_stripped` | `{412, 426}` | `{}` |
| `official` | `{412, 426}` | `{}` |

**Clean +2/+2/+2 on every arm, identical task-id set, empty lost-set on
every arm — matches the exact scope this rung set out to convert (§2 of
the PREREG), nothing more, nothing less.**

---

## 6. Regression risk — priced before building, confirmed after

### 6.1 Architectural argument (priced in the PREREG, §5)

The search explores `FilterList` candidates in increasing TOTAL size order
and short-circuits on the FIRST solved candidate. This rung's new
templates occupy predicate-size slots 5/6 exclusively, so they cannot
appear at any total `FilterList` size below `1+5+1=7`. Any currently-
passing task whose real solution has total size <7 is therefore provably
unaffected. Checked directly: of the 84 pre-rung passing `full`-arm tasks,
exactly 2 are both `SynthEnumerate`-sourced AND use `FilterList` in their
accepted `ir` — task 161 (total size 6) and task 436 (total size 5), both
strictly below 7.

### 6.2 Confirmed empirically

The exact task-id set diff (§5) shows `lost: {}` on all three arms — tasks
161 and 436 (and every other currently-passing task) are unaffected,
confirming the architectural argument directly rather than by analogy
alone.

### 6.3 Rust suite

```
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
cargo test --lib --release -- --test-threads=1
```

**778 passed; 0 failed; 4 ignored** — byte-identical to the documented
778-baseline. Genuine from-source rebuild confirmed non-cached (`touch`ed
`synth_enumerate.rs`, 2m18s, not a sub-second cached finish). `bash
scripts/engine_build.sh` installed; `record_build()` +
`pytest tests/test_engine_provenance_migrated.py` both green (9 passed, 1
skipped).

### 6.4 Named 9-file suite

**3 failed / 241 passed — exactly the 3 known pre-existing pin-drift
failures, nothing new:**

```
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

(An earlier run, before eight gitignored `results/` fixtures were copied
from the canonical tree into this worktree — `mbpp_zero_shot_baseline.json`,
`prog_construction_scan.json`, `prog_ir_histogram.json`, `prog_ir_python_
coverage.json`, `prog_chunk_mine.json`, `mbpp_train_diet.json`, `prog_
synthesis_battery.json`, `mbpp_arc3_endgame.json`, `mbpp_blocker_histogram.
json`, `code_synthesis_baseline.json`, `arc4_structural_verdicts.json`,
`arc4_endgame.json` — showed additional `FileNotFoundError` failures; all
resolved once the fixtures were copied, per every predecessor rung's own
documented prerequisite. Reported for completeness, not a real signal.)

### 6.5 `test_retrieval_migrated.py` and `test_reject_informs_repair_migrated.py`

```
test_retrieval_migrated.py:            3 failed, 30 passed
  FAILED test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing
  FAILED test_ceiling_task_reproduces_measured_outcome_live[238]
  FAILED test_ceiling_task_reproduces_measured_outcome_live[412]
test_reject_informs_repair_migrated.py: exactly its 4 known pre-existing failures
  FAILED test_retrieval_sourced_ids_gap_directly_never_reopen
  FAILED test_reopened_ids_genuinely_tried_and_still_gapped_honestly
  FAILED test_disposition_a_repaired_to_pass_is_empty
  FAILED test_no_wrong_accept_regression_vs_v1_7_0_baseline
  4 failed, 18 passed
```

**`test_reject_informs_repair_migrated.py` matches the task brief's
expectation exactly (its 4 known pre-existing failures, nothing new).**

**`test_retrieval_migrated.py` shows 1 known pre-existing failure (task
238) plus 2 NEW failures — both isolated and confirmed to be the direct,
intended consequence of this rung's own conversion of task 412, not a
regression:**

- **Task 238 (pre-existing, confirmed).** `results/ceiling3_diag_sweep.
  json` (run BEFORE this rung's code change, part of §1's baseline
  population re-derivation) already shows task 238 as `gap_reason:
  'enumerate_failed'`, while the test's own pin
  (`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT[238]`, dated 2026-08-16 in-file)
  expects `'structural_verdict_reject'`. **This drift was present on
  unmodified `main @ 84cd082` before this rung touched anything** — the
  same drift `PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON_RESULTS.md` §5.2 already
  found and confirmed pre-existing/unrelated on `main @ bc0ac10` one rung
  earlier, still present, unchanged, unrelated to `FilterList`/`Mod`
  (task 238 is a budget-exhausted, non-`FilterList` task; `Mod` was
  already in `OP_TABLE` before this rung).
- **Task 412's two new failures (caused by this rung, as intended, not a
  bug).** `test_ceiling_task_reproduces_measured_outcome_live[412]`
  asserts `out["status"] == "accepted"` against a pin recorded when 412
  was still gapped — it now reads `'accepted'`, exactly this rung's own
  headline conversion. `test_ladder_gap_spends_no_attempt_when_retrieval_
  finds_nothing`'s own docstring (read in full) documents that this exact
  test has been RE-PINNED twice before for the IDENTICAL reason — a task
  standing for "retrieval finds nothing" stops standing for that the
  moment an op-table/template-pool widening makes it find something (task
  394→106, arc4 S4; task 106→412, arc6 tier-0's `ConcatList`). **Task 412
  is the CURRENT pin for "finds nothing," and this rung's own fix is
  exactly the kind of widening its own docstring predicts breaks the pin
  — a third re-pin (412 → some other still-gapped task) is the correct
  follow-on, not built here, matching the "left for the orchestrator"
  disposition every predecessor rung in this arc uses for its own
  pin-drift discoveries.**

---

## 7. What this document does NOT establish

Carried forward from the PREREG, plus what this rung's own measurement
resolved:

1. Whether the automatic typed default reaches the witness within the
   real pipeline's actual budget via the real search loop — **resolved,
   YES** (§4: both tasks accepted, holdout-verified, via the real
   pipeline, not a hand-built term).
2. Whether tasks 161/436 regress — **resolved, NO** (§5/§6.2: exact
   task-id set diff shows `lost: {}` on every arm).
3. Task 75 (needs `Mod` inside family 5's nested-reduction inner grammar,
   a different code location) and tasks 226/437 (need `FilterList`
   exposed to string-shaped specs at all, a strictly larger 2-part gap)
   are unaffected and unbuilt — named, not attempted, matching the
   predecessor rung's own scoping.
4. The `test_retrieval_migrated.py` pin drift for task 412 is diagnosed
   and explained, not fixed — a future rung should re-pin
   `test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing` to a
   still-genuinely-gapped task and update `_KNOWN_ARC6_PROPERTY_REJECT_
   DRIFT`/`MEASURED_OUTCOMES`-style fixtures for 412's new `accepted`
   status, exactly as the file's own docstring anticipates.
5. The `gapped:no_shape` bucket (3 tasks: 77, 164, 256 — divisor/primality
   -flavored, but a different failure shape: `SynthEnumerate` itself found
   something, a downstream shape/cover-parts gate rejected it) was noticed
   in the PREREG but not investigated — orthogonal to this rung's target
   (none uses `FilterList`), not established here as a real or fixable
   cluster.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

---

## 8. GO/NO-GO

**GO.** A single, zero-new-`TermNode`, precisely-scoped, live-verified
fix — one new `filter_templates_by_size` predicate family, gated behind
the existing `filter_wanted` flag, bounded to a mathematically well-formed
modulus/remainder range drawn from the spec's own constant pool. Measured
result: `full` 84→86/257, `content_stripped` 83→85/257, `official`
109→111/257, all three arms gaining the IDENTICAL 2-task set (`412, 426`)
with an empty lost-set on every arm. Rust suite 778/0/4 (byte-identical to
baseline). Named 9-file suite 3 failed/241 passed (exactly the 3 known
pre-existing pin-drift failures). `test_reject_informs_repair_migrated.py`
shows exactly its 4 known pre-existing failures.
`test_retrieval_migrated.py`'s 2 new failures were investigated directly,
not assumed, and both trace to the SAME cause — task 412's own intended
conversion breaking a test pin whose own docstring predicts exactly this
failure mode on a successful widening — not a regression; task 238's
continuing failure was confirmed present in this rung's OWN pre-build
baseline sweep, unrelated to this rung's change.

**State left in the worktree**: `runners/dsl/src/synth_enumerate.rs`
diff committed; `results/mbpp_endgame.json` reflects the AFTER state;
`results/mbpp_endgame_BEFORE_this_rung.json` preserved for the diff;
`results/ceiling3_diag_sweep.json` reflects the BEFORE-code-change
population sweep (used both for §1's failure-cause breakdown and §6.5's
task-238 pre-existing-drift confirmation); engine `.so` in
`runners/dsl/python/substrate_rs/` reflects the final build.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-5
git log --oneline -1   # on top of main @ 84cd082
```

```bash
bash scripts/engine_build.sh
python3 -c "import sys; sys.path.insert(0, '.'); from domains.engine_provenance import record_build; print(record_build())"
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q --tb=line -rf
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_retrieval_migrated.py tests/test_reject_informs_repair_migrated.py -q --tb=line -rf
```

Task 238's pre-existing-drift confirmation (§6.5) is reproducible by
inspecting `results/ceiling3_diag_sweep.json` (committed in this
worktree, generated BEFORE any code change in this rung) for
`task_id==238`.
