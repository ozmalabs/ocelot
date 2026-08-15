# Fresh ceiling reassessment: `SortBy` op-list gate widening (task 64) — RESULTS

Prereg: `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_PREREG.md` (commit
`6f2cacd`). Base `main @ f1bb4f6` ("Scope the Bigville gossip gap: not a
missing drive, two missing bridges"), verified fresh immediately before
creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-3`, branch
`progsyn-ceiling-reassessment-3` — **not merged to `main`**, left for the
orchestrator to independently verify and merge (per this session's explicit
instruction not to repeat the earlier direct-merge violation).

**Headline: GO, built and measured. `full` 66/257 → 67/257,
`content_stripped` 65/257 → 66/257, `official` 94/257 → 96/257 — all three
arms gain, zero regressions on any arm, confirmed by exact task-id set-diff.
Newly passing: `full`/`content_stripped` gain `{64}`; `official` gains
`{12, 64}`. One `TermNode` gate widened (zero new `TermNode` variants, zero
new templates) — the single cheapest, best-evidenced candidate found in this
sweep.**

---

## 1. Real baseline, confirmed live before touching anything

Worktree provisioning: `data/` re-symlinked and verified
(`data/wiktionary/en.jsonl.gz` resolves to the real 492MB file); engine
rebuilt from source (`cargo build --release`, hash `e2fbf39e6b4e`); full
Rust suite green (`774 passed; 0 failed; 4 ignored`, the documented
`dim_infer_tests` flakes); the fresh worktree's gitignored `results/`
lacked several artifacts referenced at import/fixture time
(`mbpp_zero_shot_baseline.json`, `prog_construction_scan.json`,
`arc4_structural_verdicts.json`, `prog_chunk_mine.json`,
`code_synthesis_baseline.json`, `mbpp_blocker_histogram.json`,
`prog_synthesis_battery.json`, `mbpp_train_diet.json`,
`mbpp_arc3_endgame.json`) — copied the specific closure of referenced files
from the primary tree, matching `PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_
RESULTS.md` §7's own precedent (a provisioning gap, not a code defect).

```
full:              66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
content_stripped:  65/257  p=0.252918  ci=[0.20368,  0.309434]  det_identical=True
official:          94/257  p=0.365759  ci=[0.309252, 0.426219]  det_identical=True
```

Byte-identical to `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md`'s own
"before" measurement on aggregate AND, independently re-derived here, on
exact pass-id set — confirms the task brief's own claim that the
delimjoin/budget-wall queue is fully resolved with zero code retained.

## 2. Failure-cause grouping — the real 191 currently-failing runnable tasks

Full per-task diagnostic sweep (`scripts/ceiling3_diag_sweep.py`, output
`results/ceiling3_diag_sweep.json`), mirroring
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` §2's own methodology —
direct `domains.prog_synthesis.synthesize_from_request` call per task, full
`read_goal()` dict, same `boot_full()` the battery uses:

| outcome | n | Δ vs. `CEILING_REASSESSMENT_2` (194-task population) |
|---|---|---|
| `gapped:enumerate_failed` | 99 | −3 (104, 118, 456 converted by map-template-pool) |
| `accepted_holdout_fail` | 51 | unchanged |
| `gapped:property_verdict_reject` | 26 | unchanged |
| `gapped:structural_verdict_reject` | 10 | unchanged |
| `runner_exception:TypeError` | 2 | −1 (task 98 fixed by the `_plain()` Fraction rung) |
| `not_recognized` | 1 | unchanged |
| `gapped:no_shape` | 1 | unchanged |
| `gapped:exhausted` | 1 | unchanged |

**The population has shrunk by exactly the 4 tasks the intervening rungs
converted (104, 118, 456, 98); every other bucket is byte-identical in
count.** `gapped:enumerate_failed` (99) splits 84 budget-exhausted
(`tested==200,000`) / 15 genuinely saturated under budget — same
84/15-ish split CEILING_REASSESSMENT_2 measured (85/17 on the larger prior
population). `ops=None` for all 99 (the `SynthesisOperatorShape` selection
layer contributes nothing, unchanged). The 87-task
`accepted_holdout_fail`/`*_verdict_reject` population's construction
breakdown is unchanged: 60 `retrieved_exemplar`-sourced (never reaching
`SynthEnumerate` at all), 27 `mck_*`/template-family (search runs, wrong
lane wins).

## 3. What's newly reachable — checked directly, live-verified

### 3.1 Task 64 — the built fix

`SortBy` (DictItems/SortBy rung) was gated to `spec_has_dict_value` only,
scoped narrowly to serve task 475's `Counter.most_common()` shape — never
re-checked against a spec with no dict at all. Task 64 ("sort a list of
tuples using the second value of each tuple") is `List[Tuple]`, no dict
anywhere, so `SortBy` never entered `op_list` under the automatic typed
default.

**Live-verified** with a direct `SynthEnumerate` call
(`ops=["SortBy"]` forced): `found:true, size:4, tested:9, distinct:7`, term
`SortBy(a, item, Sort(item))`. The key template (`Sort(item)`) already
exists in `map_templates_by_size`, gated on `set_map_wanted ||
spec_has_list_of_lists` (the map-template-pool rung's own flag,
already-measured-safe) — task 64's `a` is `List[Tuple]`, and `Tuple`
counts as list-like, so `spec_has_list_of_lists` is already true. `Sort`
on a mixed `(Str, Int)` 2-tuple always places the `Int` first under the
DSL's cross-type total order, so sorting BY that canonicalized key
reproduces "sort by the numeric field" for this exact shape — confirmed
exact-match on both revealed rows and the held-out row directly via
`substrate_rs.Substrate()._inner.evaluate`.

**Fix**: `runners/dsl/src/synth_enumerate.rs`, immediately after the
existing `if spec_has_dict_value { v.push("DictItems"); v.push("SortBy");
v.push("Reverse"); }` block — added a second, narrower guard:

```rust
if spec_has_list_of_lists && !spec_has_dict_value {
    v.push("SortBy");
}
```

`DictItems`/`Reverse` deliberately stay exactly as dict-scoped as before —
only `SortBy` gets the second disjunct, because only `SortBy` had a live
witness under this evidence. Zero new `TermNode`, zero new template pool
entry, one gate widening reusing an already-shipped, already-measured-safe
flag.

### 3.2 The real conversion mechanism — a finding, not a prediction

The PREREG predicted task 64 would convert via a direct `SynthEnumerate`
accept. **Measured, it converts via `construction: retrieved_exemplar`
instead** (`enumerate.tested: None` in the read-back — top-level
`SynthEnumerate` is never invoked for the winning attempt). Confirmed this
is caused by the Rust change and not incidental: reverted the source,
rebuilt, re-ran the identical script — task 64 reproduces `gapped:
enumerate_failed` (`construction: mck_prog_aug_assign_n2_q3`) on the
unmodified engine, deterministically, on two repeat runs each side.

The most likely mechanism, inferred from task 12's own retrieval record
(§3.3): `retrieved_exemplar`'s "retrieved-as-skeleton" path fills a HOLE in
a retrieved program's skeleton using the same op inventory
`SynthEnumerate` draws from (task 12's own stored `accept_edit.hole_term`
is literally `{"type":"Sort","seq":{"name":"arr"}}` — a bare, WRONG
element-wise `Sort`). Widening `SortBy`'s availability widens what the
hole-filler can propose too, so a correct `SortBy`-shaped fill becomes
available where only a wrong `Sort`-shaped one was before. **This is named
as a finding, not fully traced end-to-end in this document** — the exact
code path connecting hole-filling to `OP_TABLE`/`op_list` construction was
not read line-by-line to confirm — mirroring
`PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_RESULTS.md` §9.5's own "not fully
traced to its exact internal mechanism" residual for a structurally
similar `retrieved_exemplar`-labeled conversion. The PASS verdict itself
(held-out row agreement, confirmed independently below) does not depend on
this attribution being fully traced.

### 3.3 Task 12 — a second live `SortBy` witness, and why it converts on
   `official` but not `full`/`content_stripped`

Task 12 ("sort a matrix by row sum") has an exact witness too —
`SortBy(a, item, Sum(item))`, confirmed against all three rows including
held-out. Under the `primary` protocol (2 revealed rows), task 12 stays
`accepted_holdout_fail` via a WRONG `retrieved_exemplar` — same
`{"type":"Sort","seq":{"name":"arr"}}` bare-Sort hole-fill, still wrong at
2 revealed rows because that count of rows apparently isn't enough to
disambiguate/reject it before acceptance. Under `official` (3 revealed
rows), the SAME live-verified mechanism converts it: rerunning
`synthesize_from_request` directly against the official-protocol spec
gives `status:accepted, construction:retrieved_exemplar`, holdout-passing.
**This was not predicted in the PREREG** (which named task 12 explicitly
as NOT expected to convert, based on the `primary`-protocol read where
`enumerate.tested is None`) — measured directly, it converts under
`official` specifically, and this is reported as a genuine, unpredicted
additional gain rather than silently absorbed into the headline. The
`full`/`content_stripped` arms (both `primary` protocol) do NOT gain task
12, matching the original prediction for those two arms exactly.

### 3.4 Other candidates checked and ruled out or deferred (unchanged from
   PREREG §3.3, reconfirmed, not re-narrated here)

Tasks 108 (budget-wall, matches the already-NO-GO'd delimjoin/budgetwall
finding), 87/88/97/283/301/465 (genuine dict-construction/`Counter`
primitive gaps, `GroupCount`/`DictMerge` still priced not built), 111/140
(N-way `Intersect`/`Union` fold, not live-witnessed), Recurse (7 ids, still
NO-GO), Format/Combinations (still exactly one task each) — all re-checked
per §3 of the PREREG, no new evidence beyond what that document already
recorded.

## 4. Regression discipline

**Rust test suite** (`cargo test --lib --release -- --test-threads=1`,
documented pyo3 linking workaround): **774 passed; 0 failed; 4 ignored**
(the documented `dim_infer_tests` flakes) both before AND after this
rung's change. `synth_enumerate::tests::*`: 21/21 passed after the change.

**Canary check.** 11 currently-passing tasks have `spec_has_list_of_lists`
evidence (104, 120, 272, 290, 393, 413, 418, 457, 460, 473, 475) — every
one of these now has `SortBy` newly available in their search too. Plus
task 132, this arc's standing canary. **All 12 checked directly against
the after-battery's pass set: all 12 still pass, zero regressions.**

## 5. Full MBPP battery — before/after, all three arms, real set-diff

**Before** (unmodified `main @ f1bb4f6`, this worktree, engine hash
`e2fbf39e6b4e`):

```
full:              66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
content_stripped:  65/257  p=0.252918  ci=[0.20368,  0.309434]  det_identical=True
official:          94/257  p=0.365759  ci=[0.309252, 0.426219]  det_identical=True
```

**After** (this rung, engine hash `e87c42ebbdfe`, rebuilt from source
three separate times across this investigation — deterministic, identical
hash every time):

```
full:              67/257  p=0.2607    ci=[0.210831, 0.317618]  det_identical=True
content_stripped:  66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
official:          96/257  p=0.373541  ci=[0.316669, 0.434138]  det_identical=True
```

**Exact task-id set-diff, all three arms** (not aggregate counts):

| arm | before (n) | after (n) | newly passing | regressed |
|---|---|---|---|---|
| `full` | 66 | 67 | `{64}` | `{}` |
| `content_stripped` | 65 | 66 | `{64}` | `{}` |
| `official` | 94 | 96 | `{12, 64}` | `{}` |

`before_pass_ids ⊆ after_pass_ids` holds on all three arms, confirmed by
direct set computation from `results/mbpp_endgame.json`'s `runnable_rows`
(saved before/after: `results/mbpp_endgame_BEFORE_sortby.json` vs.
`results/mbpp_endgame.json`). Re-derived a second time after a fresh
from-source rebuild to confirm reproducibility — identical engine hash,
identical pass sets, both times.

## 6. Regression — the named 9-file suite, verified against a genuinely
   fresh unmodified baseline, not assumed

Named 9-file suite (`test_prog_synthesis_battery_migrated.py`,
`test_mbpp_baseline_migrated.py`, `test_mbpp_endgame_migrated.py`,
`test_mbpp_contamination_migrated.py`, `test_mbpp_diet_migrated.py`,
`test_program_synthesis_migrated.py`, `test_prog_moves_migrated.py`,
`test_prog_property_migrated.py`, `test_exact_first_migrated.py`):

**After this rung's change: 3 failed / 241 passed.**

Independently reverted the source (`git checkout --
runners/dsl/src/synth_enumerate.rs`), rebuilt from source, and re-ran the
same 3 named failing tests directly against the genuinely unmodified
engine: **byte-identical 3/3 failure — same test names, same underlying
inner "unexpected" set** (`test_mbpp_arc3_endgame_migrated.py`'s
artifact-hash/headline checks, the same already-documented "shared mutable
output path" fragility this arc's prior rungs have repeatedly re-confirmed
present on clean `main`, not inherited from any prior doc's
characterization). Then re-applied the fix, rebuilt (identical engine hash
`e87c42ebbdfe` both times — confirms deterministic build), and re-ran the
full 9-file suite one final time on the shipped state: same **3 failed /
241 passed**.

**Zero new Rust-suite failures, zero new Python-suite failures — this
rung's failure signature is IDENTICAL to clean `main`'s own, confirmed by
running both, not by citation.**

## 7. GO/NO-GO

**GO, delivered.** `SortBy`'s op-list evidence gate widened from
`spec_has_dict_value` alone to `spec_has_dict_value || spec_has_list_of_lists`
(implemented as a second, narrower guard so `DictItems`/`Reverse` stay
exactly as dict-scoped as before). Real measured MBPP gain: `full` +1
(`{64}`), `content_stripped` +1 (`{64}`), `official` +2 (`{12, 64}`), zero
regressions on any arm, zero new Rust-suite failures, zero new Python-suite
failures (all confirmed against an independently rebuilt, genuinely
unmodified baseline, not assumed). This is the cheapest, best-evidenced
build in this sweep: zero new `TermNode`, zero new template, one boolean
disjunct reusing an already-shipped, already-measured-safe evidence flag —
the same risk class as the map-template-pool rung's own gate widenings, but
cheaper (one touch point).

## 8. What this document does NOT establish

1. **The exact internal mechanism connecting `SortBy`'s op-list
   availability to `retrieved_exemplar`'s hole-filling is inferred from
   task 12's own stored `accept_edit.hole_term`, not read line-by-line in
   the retrieval engine's own source.** Both conversions (task 64 on
   `full`/`content_stripped`, tasks 12+64 on `official`) are independently
   confirmed CORRECT via the held-out-row check, so this residual is about
   attribution/mechanism understanding, not about whether the fix works.
2. **Task 12's `official`-arm conversion was not predicted by the PREREG**
   — it is reported here as a genuine additional finding, not retrofitted
   into the original prediction. Whether other `retrieved_exemplar`-gated
   tasks have similar hidden dependencies on `SynthEnumerate`'s op
   inventory (beyond the two found here) was not swept — only tasks 12 and
   64 were checked this deeply.
3. **The `IntersectAll`/`UnionAll` N-way-set candidate (§3.4/PREREG §3.3)
   remains unwitnessed** — named as a future candidate, not sized to the
   depth §3.1's witness was.
4. **`GroupCount`/`DictMerge`** remain priced (+1 each, tasks 88/87) but
   not built in this rung — deliberately kept out to keep this rung's
   measurement single-variable (one gate widening, not a bundle of a
   gate widening plus two new `TermNode` variants, which would make the
   before/after attribution ambiguous if anything had gone wrong).
5. **The retrieved-exemplar-fallthrough gap** (up to 60 tasks inventory,
   named in `CEILING_REASSESSMENT_2` §4) remains genuinely unpriced and
   not recommended to build blind — this rung's own finding (§3.2/3.3,
   `SortBy` availability silently changing what `retrieved_exemplar`
   itself can construct) is a DIFFERENT, narrower mechanism than that
   60-task fallthrough question and does not resolve or substitute for it.
6. **Whether this reflects real human program-synthesis cognition**
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-3
git log --oneline -1   # on top of main @ f1bb4f6
bash scripts/engine_build.sh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

Named 9-file regression suite:
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q
```

Per-task diagnostic sweep (§2's own data source):
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```
