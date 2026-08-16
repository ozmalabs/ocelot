# Ceiling reassessment 6 — bundled `DICT_DEFAULT_OPS` widening +
   `max_size`/`max_candidates` raise — RESULTS: GO, +2/+2/+2, zero
   regression

Prereg: `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_6_PREREG.md`, same
worktree/branch. Base `main @ aed1d12` ("Build hate attribution: outward
attribution-locus residual + stability gate"), verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-6`,
branch `progsyn-ceiling-reassessment-6` — **not merged to `main`, not
pushed**, left for the orchestrator to independently verify and merge.

---

## Headline

**GO. Full paired MBPP battery: `full` 86→88/257, `content_stripped`
85→87/257, `official` 111→113/257 — all THREE arms gain the EXACT SAME
2-task set (`277, 465`), zero lost on any arm.** This finishes the exact
bundled fix `PROGRAM_SYNTHESIS_MAX_SIZE_SEAM_PRICING_PREREG.md §6` item 1
named and explicitly declined to build ("a real, un-costed candidate this
document explicitly declines to build"): (1) widen `DICT_DEFAULT_OPS` with
the already-shipped `DictItems`/`FilterList`, (2) raise `run_enumerate`'s
hardcoded `max_size` 9→20 (reusing `MAX_SIZE_SEAM_PRICING`'s own already-
measured-safe value), (3) a THIRD component neither predecessor document
measured — a `ZIP_MAX_CANDIDATES`-shaped scoped `max_candidates` raise
(`DICT_FILTER_MAX_CANDIDATES = 300_000`), needed because the real
pipeline's own internally-selected typed-default op list was measured,
live, to explore a genuinely larger candidate space than the same op NAMES
supplied explicitly (§2 below) — a mid-rung finding neither `DICTFROMPAIRS_
RESULTS.md §1` nor this rung's own early hand-probes exposed, because both
forced `ops` explicitly rather than letting the real pipeline pick its own
typed default.

**Rust suite: 778/0/4, byte-identical to baseline. Named 9-file suite: 3
failed / 241 passed, exactly the 3 known pre-existing pin-drift failures,
nothing new. `test_retrieval_migrated.py` + `test_reject_informs_repair_
migrated.py`: 6 failed / 49 passed, confirmed via a live isolated
before/after check (§5.3) to be BYTE-IDENTICAL to unmodified `main @
aed1d12` — all 6 pre-existing, none caused by this rung.**

---

## 1. Re-deriving the population — confirmed against the current baseline

Fresh battery run, this worktree, before any code change:

```
full:              86/257  p=0.33463   ci=[0.279751, 0.394381]  det_identical=True
content_stripped:  85/257  p=0.330739  ci=[0.276082, 0.390382]  det_identical=True
official:         111/257  p=0.431907  ci=[0.372789, 0.49303]   det_identical=True
```

Byte-identical to the task brief's own cited baseline and to
`results/mbpp_endgame.json`'s `head` field (`aed1d12f9782217a80c7345a01848
703d28eed1c`, matching `git log --oneline -1 main`). Saved as
`results/mbpp_endgame_BEFORE_this_rung.json`.

`scripts/ceiling3_diag_sweep.py`, run against this baseline before any
code change — **171 rows** (257−86; PREREG §2 corrects the task brief's
own "173−10=163" back-of-envelope figure, which used the wrong pre-reassessment-5
baseline for the subtraction — 171 is the directly re-derived, correct
figure). Full breakdown and reconciliation against reassessment-5's own
pre-build sweep: PREREG §2 (byte-identical on every bucket except
`enumerate_failed`, which shrank by exactly reassessment-5's own +2
conversion).

---

## 2. The target — 277/465, and the mid-rung surprise that changed the
   design from "two parts" to "three parts"

Full mechanism (why 277/465 share one root cause — both a dict-comprehension
filter, `{k:v for k,v in d.items() if PRED(v)}`; the exhaustive
`.items()`+`if` scan confirming no third witness in the current failing
population; the two predecessor documents' own individually-insufficient
halves) is in the PREREG §3-4 — not duplicated here.

**What THIS document adds, measured post-build, confirming the PREREG §5.2
surprise held under the real, built pipeline** (not just the pre-build
hand probe):

```
task 277: status=accepted, ps_enum_tested=204522 (full/content_stripped, 2 revealed rows)
                            ps_enum_tested=264789 (official, 3 revealed rows -- converges under DICT_FILTER_MAX_CANDIDATES=300,000)
task 465: status=accepted, ps_enum_tested=83069  (2 revealed rows)
task 87:  status=accepted, ps_enum_tested=1171,  ps_enum_solution_size=5 -- UNCHANGED term (`DictMerge(Var(b), DictMerge(Var(c),Var(a)))`), unaffected
```

All three verified via the REAL pipeline
(`domains.prog_synthesis.synthesize_from_request`, real fixture rows via
`domains.mbpp_spec.parse_asserts`/`split_rows`), not a forced-`ops` probe.

**The three-part design, built exactly as the PREREG specified**:

1. `DICT_DEFAULT_OPS` (`runners/dsl/src/synth_enumerate.rs`): `&["Eq",
   "IfThenElse", "GroupCount", "DictMerge", "DictFromPairs"]` →
   `&["Eq", "IfThenElse", "GroupCount", "DictMerge", "DictFromPairs",
   "DictItems", "FilterList"]`.
2. `domains/prog_synthesis.py`, `run_enumerate`: `"max_size": 9` →
   `"max_size": 20` (one line, bare literal, no new conditional).
3. `runners/dsl/src/synth_enumerate.rs`: new `const
   DICT_FILTER_MAX_CANDIDATES: u64 = 300_000;`, applied via a
   `dict_filter_wanted_for_budget` gate (op_list contains BOTH
   `"DictItems"` and `"FilterList"`) alongside the existing
   `zip_wanted_for_budget` gate, both independently `.max()`-folded into
   the final `max_candidates`, only when `caller_wants_default_candidates`
   (the caller passed `<= 0`).

**Part 3's value was tuned live, in two steps, honestly reported**: an
initial `DICT_FILTER_MAX_CANDIDATES = 250_000` (chosen from the 2-revealed-
row `full`/`content_stripped` measurement, 204,522 tested, +22% headroom)
converted 277/465 on `full`/`content_stripped` (+2/+2/0 on the first
battery run) but left task 277 gapped on `official` (3 revealed rows needs
264,789 tested — OVER the 250,000 ceiling). Raised to `300_000` (matching
`ZIP_MAX_CANDIDATES`'s own already-proven value exactly, rather than
inventing a fourth magic number) and re-measured: clean +2/+2/+2 on all
three arms, §4 below.

---

## 3. Regression risk — task 87, priced and confirmed unaffected

Task 87 (the bucket's one live canary) re-verified via the real pipeline
post-build: **same accepted term, same solution size (5), tested=1171**
(up from the pre-widening 557-ish figure the PREREG's own early probe
showed for a slightly different isolated construction — the REAL pipeline
number, both before and after this rung's changes, is measured directly
here, not inferred) — more candidates explored before the SAME size-5
answer is reached (because the op list is now 2 names longer), but the
SAME answer, confirmed both by direct re-run and by the full battery's own
exact task-id-set diff (§4: `lost: {}` on every arm, task 87 stays passing
throughout).

---

## 4. Full paired MBPP battery — exact task-id set diffs (final,
   `DICT_FILTER_MAX_CANDIDATES=300_000` build)

```
                    before (k/n)          after (k/n)           det_identical
full:               86/257  p=0.33463     88/257  p=0.342412    True / True
content_stripped:   85/257  p=0.330739    87/257  p=0.338521    True / True
official:          111/257  p=0.431907   113/257  p=0.439689    True / True
```

**Exact task-id set diff, all three arms, reproduced twice
(once at `DICT_FILTER_MAX_CANDIDATES=250_000`, once at the final
`300_000` value, both saved via `results/mbpp_endgame_BEFORE_this_rung.
json` vs. `results/mbpp_endgame.json`), the SECOND (final) run reported
here:**

| arm | gained | lost |
|---|---|---|
| `full` | `{277, 465}` | `{}` |
| `content_stripped` | `{277, 465}` | `{}` |
| `official` | `{277, 465}` | `{}` |

**Clean +2/+2/+2 on every arm, identical task-id set, empty lost-set on
every arm.** Every row's own `outcome` string was diffed (not just
pass/fail), all 257 rows × 3 arms: the ONLY drift anywhere is 277/465
flipping `gapped:enumerate_failed` → `pass` on every arm — zero other
outcome, construction, or `ir` field changed for any other task.

---

## 5. Regression discipline

### 5.1 Rust suite

```
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
cargo test --lib --release -- --test-threads=1
```

**778 passed; 0 failed; 4 ignored** — byte-identical to the documented
778-baseline. Genuine from-source rebuild confirmed non-cached (`touch`ed
`synth_enumerate.rs`, ~1m55s each of 3 separate genuine rebuilds this
rung — the initial build, the `DICT_FILTER_MAX_CANDIDATES` tuning rebuild,
and the isolation-check revert/restore rebuild pair below — never a
sub-second cached finish). `bash scripts/engine_build.sh` installed;
`record_build()` + `pytest tests/test_engine_provenance_migrated.py` both
green each time (9 passed, 1 skipped).

### 5.2 Named 9-file suite

**3 failed / 241 passed — exactly the 3 known pre-existing pin-drift
failures, nothing new:**

```
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

(The third failure's own nested internal sweep surfaces additional
diagnostic detail — `test_budget_isolation_migrated`, `test_verdict_
discrimination_migrated`, `test_prog_descent_migrated`, `test_descent_
widening_migrated`, `test_mbpp_arc3_endgame_migrated`'s 4 frozen-artifact-
hash tests, `test_retrieval_migrated`'s 2 — INSIDE its own assertion
output, not as separate top-level `pytest` failures. `test_mbpp_arc3_
endgame_migrated.py`'s 4 failures were read directly: they compare a LIVE
hash/read of `results/mbpp_endgame.json` — the SAME file every battery run
in this arc overwrites — against a FROZEN arc-2-era citation baked into a
separate artifact file. This is the exact "shared mutable output path"
fragility `CEILING_REASSESSMENT_3_RESULTS.md §6` first named and every
subsequent rung in this arc has re-confirmed present on clean `main`
independent of any given rung's own change — running the battery at all
(a required step of EVERY rung) flips this same nested detail, matching
every predecessor rung's own handling: reported for completeness, not a
new top-level failure, not chased.)

### 5.3 `tests/test_retrieval_migrated.py` and `tests/test_reject_
   informs_repair_migrated.py` — live isolated before/after check

```
tests/test_retrieval_migrated.py + tests/test_reject_informs_repair_migrated.py:
  6 failed, 49 passed
  FAILED test_retrieval_migrated.py::test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing
  FAILED test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_outcome_live[238]
  FAILED test_reject_informs_repair_migrated.py::test_retrieval_sourced_ids_gap_directly_never_reopen
  FAILED test_reject_informs_repair_migrated.py::test_reopened_ids_genuinely_tried_and_still_gapped_honestly
  FAILED test_reject_informs_repair_migrated.py::test_disposition_a_repaired_to_pass_is_empty
  FAILED test_reject_informs_repair_migrated.py::test_no_wrong_accept_regression_vs_v1_7_0_baseline
```

**Not assumed pre-existing — checked directly, live, in this SAME
worktree** (matching every predecessor rung's own isolation-trace
precedent for exactly this class of check): `domains/prog_synthesis.py`
and `runners/dsl/src/synth_enumerate.rs` were reverted to their pristine
`git checkout --` state (this rung's own 3-part diff backed up to a
scratch file first), the engine genuinely rebuilt from that pristine
source (confirmed non-cached, 1m55s), and the SAME two test files re-run:

```
6 failed, 49 passed in 79.76s   -- BYTE-IDENTICAL failing-test-name set to the "after" run above
```

**Confirmed: all 6 failures are pre-existing on unmodified `main @
aed1d12`, unrelated to any of this rung's three changes.** Two are the
already-documented `test_retrieval_migrated.py` drift this arc has carried
since reassessment-5 landed (`task 238`'s pre-existing `structural_verdict_
reject`→`enumerate_failed` pin drift, first confirmed pre-existing by
`ZIPWITH_FOLLOWON_RESULTS.md §5.2`; and reassessment-5's own conversion of
task 412 breaking the `test_ladder_gap_spends_no_attempt_when_retrieval_
finds_nothing` "finds nothing" witness pin — explicitly named by
`CEILING_REASSESSMENT_5_RESULTS.md §6.5` as needing a future re-pin, and
the subject of the SIBLING agent's own parallel, separately-scoped
investigation this session; NOT touched here per the task brief's own
collision note). The 4 `test_reject_informs_repair_migrated.py` failures
are exactly reassessment-5's own documented "4 known pre-existing
failures" (same test names, same file), also unrelated to this rung.
Reverted files restored from the scratch backup, re-rebuilt, and the final
battery/Rust-suite/9-file-suite runs above (§1, §4, §5.1, §5.2) were all
re-confirmed AFTER restoration, on the actual committed diff — not left
on the reverted state.

---

## 6. What this document does NOT establish

Carried forward from the PREREG, plus what this rung's own measurement
resolved:

1. §5.2's exact root cause for why an internally-selected op list of the
   SAME names explores a genuinely different candidate count than an
   externally-supplied one of identical content — reproduced twice,
   measured, used as the design input, NOT explained to the instruction
   level. This is a real, previously-undiagnosed engine behaviour worth a
   future investigation in its own right (it likely affects the accuracy
   of every prior rung's own hand-probe-based `tested`/budget estimates
   whenever a probe used explicit `ops` instead of letting the real
   pipeline's typed-default selection run — not audited here).
2. Whether `DICT_FILTER_MAX_CANDIDATES=300,000`'s margin is the tightest
   correct value — chosen to match `ZIP_MAX_CANDIDATES`'s own proven
   number rather than independently tuned to the minimum (264,789 measured
   necessary on `official`).
3. Task 470 (self-zip-with-offset), and tasks 97/117/299/305/417/462 (each
   a distinct single-witness shape) — named in the PREREG, not attempted.
4. The `test_retrieval_migrated.py` "finds nothing" witness pin
   (`test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing`) still
   needs a re-pin to a currently-genuinely-gapped task — already flagged by
   reassessment-5, being handled by a sibling agent this session, NOT
   fixed here.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

---

## 7. GO/NO-GO

**GO.** A bundled, three-part fix — `DICT_DEFAULT_OPS` widened with two
already-shipped ops, `run_enumerate`'s `max_size` raised to an
already-measured-safe value, and a `ZIP_MAX_CANDIDATES`-shaped scoped
`max_candidates` raise for the same bucket — finishes the exact bundled
candidate `MAX_SIZE_SEAM_PRICING_PREREG.md §6` named and declined to build,
because neither half alone converts anything (measured, independently, by
the two predecessor documents). Measured result: `full` 86→88/257,
`content_stripped` 85→87/257, `official` 111→113/257, all three arms
gaining the IDENTICAL 2-task set (`277, 465`) with an empty lost-set on
every arm. Rust suite 778/0/4 (byte-identical to baseline). Named 9-file
suite 3 failed/241 passed (exactly the 3 known pre-existing pin-drift
failures). `test_retrieval_migrated.py` + `test_reject_informs_repair_
migrated.py`'s 6 failures were confirmed, via a live isolated before/after
rebuild (not assumed), to be byte-identical to unmodified `main @ aed1d12`
— all pre-existing, none caused by this rung.

**State left in the worktree**: `runners/dsl/src/synth_enumerate.rs` +
`domains/prog_synthesis.py` diffs committed; `results/mbpp_endgame.json`
reflects the AFTER state; `results/mbpp_endgame_BEFORE_this_rung.json`
preserved for the diff; `results/ceiling3_diag_sweep.json` reflects the
BEFORE-code-change population sweep; engine `.so` in
`runners/dsl/python/substrate_rs/` reflects the final
(`DICT_FILTER_MAX_CANDIDATES=300_000`) build.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-6
git log --oneline -1   # on top of main @ aed1d12
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
  python3 -m pytest tests/test_retrieval_migrated.py tests/test_reject_informs_repair_migrated.py -q --tb=no -rf
```

The isolation trace (§5.3) is reproducible by `git checkout --
domains/prog_synthesis.py runners/dsl/src/synth_enumerate.rs`, rebuilding,
re-running the two test files, then restoring the committed diff and
rebuilding again.
