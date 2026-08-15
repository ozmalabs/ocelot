# `IntersectAll`/`UnionAll` — CEILING_REASSESSMENT_4, built — RESULTS

Prereg: `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_4_PREREG.md`, same worktree/
branch. Base `main @ 83b1f24` ("Merge progsyn-rungs124-reconciliation: Rungs
1, 2, 4 staleness-checked against the reassessment PREREG"), verified fresh
via `git log --oneline -1 main` before starting. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-4`, branch
`progsyn-ceiling-reassessment-4` — **not merged to `main`**, left for the
orchestrator to independently verify and merge (this session's explicit
instruction: never merge to `main`, never `git stash`, never push).

**Headline: GO, built and measured exactly as priced. `full` 69/257 →
71/257, `content_stripped` 68/257 → 70/257, `official` 98/257 → 100/257 —
all three arms gain exactly `{111, 140}`, zero regressions, confirmed by
exact task-id set-diff. Zero new `TermNode` variants — the cheapest
touch-point class this entire arc has used (every prior rung added at
least one new Term). Rust suite 778/778 (774 baseline + 4 pre-existing
derived-operator-tier tests, unrelated to this change), byte-identical
before/after. Named regression suite: 3 failed / 241 passed, byte-identical
to the documented pre-existing baseline (same 3 test names, same nested-
sweep detail).**

---

## 1. The fix, exactly as priced in the PREREG

Two new named ops, `IntersectAll`/`UnionAll`, added to `OP_TABLE` as
`OpKind::ListUnary` (`runners/dsl/src/synth_enumerate.rs`), each expanding
at build time into `Fold{source, var_name:item, acc_name:acc,
init:IndexAt{seq:source, index:Lit(0)}, body:Intersect{a:Var(acc),
b:Var(item)}}` (swap `Intersect`→`Union` for the second) — composing
entirely from `Fold`/`Intersect`/`Union`/`IndexAt`/`Var`/`Lit`, six Terms
that all already existed and were already fully wired. Both new ops were
added to `SET_DEFAULT_OPS` (the same narrow, already-measured-safe bucket
`SetMap`/`Intersect`/`Union`/`Sort`/`Reverse`/`Slice` already live in), and
`list_unary_extra_cost` gained two matching entries (`5` each — `Lit(0)`(1)
+ `IndexAt`(1) + `Var(acc)`(1) + `Var(item)`(1) + `Intersect`/`Union`(1) —
worked out and cross-checked against the existing `"JoinList" => 4` entry's
own accounting style in the PREREG §3.2 before writing any code).

**Exactly four edits, all in one file** (`runners/dsl/src/synth_enumerate.rs`):
`OP_TABLE` (2 lines), `SET_DEFAULT_OPS` (2 names appended), `build_list_unary`
(2 new match arms), `list_unary_extra_cost` (2 new match arms). No
`jsonio.rs`/`reflect.rs`/`term_variants.rs`/`py.rs` touch — the first rung
in this arc's own record to introduce zero new `TermNode` enum variants.

## 2. Live verification, before writing the fix (PREREG §3.1) — confirmed
   unchanged after

Both target witnesses (task 111, "common elements in given nested lists";
task 140, "flatten the list of lists into a single set of numbers") were
hand-evaluated via `substrate_rs.Substrate()._inner.evaluate()` on the exact
term-JSON tree above, against ALL THREE real fixture rows each (both
revealed rows AND the held-out row), BEFORE any Rust code was written —
6/6 exact matches, PREREG §3.1. After the build, the SAME result was
re-derived through the REAL pipeline (`domains.prog_synthesis.
synthesize_from_request`, not a hand-built term):

```
task 111: status=accepted, construction=retrieved_exemplar,
          ir=Fold(Var(a), init=IndexAt(Var(a),0), body=Intersect(acc,item))
          holdout_verdict.all_ok = True
task 140: status=accepted, construction=retrieved_exemplar,
          ir=Fold(Var(a), init=IndexAt(Var(a),0), body=Union(acc,item))
          holdout_verdict.all_ok = True
```

Both convert via `retrieved_exemplar`'s hole-filler, not a raw top-level
`SynthEnumerate` accept — the SAME "widening one op's availability silently
changes what a DIFFERENT construction lane's hole-filler proposes"
mechanism `CEILING_REASSESSMENT_3_RESULTS.md` §3.2 and `GROUPCOUNT_
DICTMERGE_RESULTS.md` §4 both already named for tasks 64/88. Not re-traced
to its exact internal code path here either — the PASS verdict (held-out
row agreement, independently confirmed both via the hand-built term AND the
real pipeline) does not depend on this attribution being fully traced,
matching both of those documents' own standing residual.

## 3. Build discipline

**Genuine from-source rebuild**: `cargo build --release` in
`runners/dsl/`, finished in **1m 58s** (not a cached sub-second no-op) after
touching `synth_enumerate.rs`. `bash scripts/engine_build.sh` installed the
built `.so` (`cp --remove-destination`); its own final `python` invocation
hit the documented benign `python: command not found` PATH quirk — the two
trailing commands (`record_build()` + `domains/engine_provenance.py`) were
run directly with `python3` per the task's own standing note. Installed
engine hash: **`44f5ae02cabd`**.

**Rust suite**: `RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib
-lpython3.13" LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:
$LD_LIBRARY_PATH" cargo test --lib --release -- --test-threads=1`:
**778 passed; 0 failed; 4 ignored** (the documented `dim_infer_tests`
flakes) — matches the CURRENT baseline exactly (774 pre-derived-operator-
tier + 4 tests that rung added; this rung adds zero new Rust tests, since it
touches only op-table/search-loop registration code, no new Term evaluator).

## 4. Full MBPP battery — before/after, all three arms, real set-diff

**Before** (this worktree, on the unmodified `main @ 83b1f24` build, freshly
re-measured — not trusted from the cached JSON — before touching any code):

```
full:              69/257  p=0.268482  ci=[0.218003, 0.325781]  det_identical=True
content_stripped:  68/257  p=0.264591  ci=[0.214414, 0.321702]  det_identical=True
official:          98/257  p=0.381323  ci=[0.324101, 0.44204]   det_identical=True
```

**After** (this rung, engine hash `44f5ae02cabd`):

```
full:              71/257  p=0.276265  ci=[0.225196, 0.333924]  det_identical=True
content_stripped:  70/257  p=0.272374  ci=[0.221597, 0.329855]  det_identical=True
official:          100/257 p=0.389105  ci=[0.331549, 0.449927]  det_identical=True
```

**Exact task-id set-diff, all three arms** (direct set computation from
`results/mbpp_endgame.json`'s `runnable_rows`, saved before/after:
`results/mbpp_endgame_BEFORE_this_rung.json` vs. `results/mbpp_endgame.json`):

| arm | before (n) | after (n) | newly passing | regressed | `before ⊆ after` |
|---|---|---|---|---|---|
| `full` | 69 | 71 | `{111, 140}` | `{}` | True |
| `content_stripped` | 68 | 70 | `{111, 140}` | `{}` | True |
| `official` | 98 | 100 | `{111, 140}` | `{}` | True |

**Both gains land exactly where priced — the 2 setlike-output canary tasks
named in the PREREG (232, 473) are confirmed present in BOTH before and
after pass sets** (they are not in `lost=[]`, and the `full`-arm after set
is verified to be a strict superset of the before set) — no regression on
either canary, no SortBy-class hidden second witness materialised.

## 5. Post-build whole-population coverage re-check

Re-ran the diagnostic sweep after the fix (186 rows = 257 − 71). Every task
named checked-and-ruled-out in the PREREG (65, 97, 108, 117, 126, 277, 283,
297, 299, 301, 305, 412, 417, 431, 462, 465, 470, plus task 300 from the
population-reconciliation discussion) remains in its **exact same** outcome
category — no unexpected secondary conversion, no unexpected regression.
The full outcome taxonomy shifted by exactly the two converted tasks and
nothing else:

```
before: gapped:enumerate_failed=96, accepted_holdout_fail=51, property_reject=26,
        structural_reject=10, not_recognized=1, ValueError=1, no_shape=1, exhausted=1, TypeError=1  (total 188)
after:  gapped:enumerate_failed=94, accepted_holdout_fail=51, property_reject=26,
        structural_reject=10, not_recognized=1, ValueError=1, no_shape=1, exhausted=1, TypeError=1  (total 186)
```

`gapped:enumerate_failed` dropped by exactly 2 (96→94, both 111 and 140
were in this category before), every other category byte-identical.

## 6. Regression discipline

**Named 9-file suite** (the arc's own historical convention, per
`GROUPCOUNT_DICTMERGE_RESULTS.md`: `test_prog_synthesis_battery_migrated.py
test_mbpp_baseline_migrated.py test_mbpp_endgame_migrated.py
test_mbpp_contamination_migrated.py test_mbpp_diet_migrated.py
test_program_synthesis_migrated.py test_prog_moves_migrated.py
test_prog_property_migrated.py test_exact_first_migrated.py`): **3 failed /
241 passed** — byte-identical count AND byte-identical failing test names
to the documented pre-existing baseline
(`test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`,
`test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_
drift`, `test_exact_first_migrated.py::test_named_regression_sweep_only_
known_pins_drift`), same nested-sweep detail (`10 failed, 452 passed, 1
skipped` inside the sweep tests) — the already-documented "shared mutable
output path" fragility this arc has repeatedly re-confirmed present on
clean `main`, unrelated to this rung's change (none of the 10 nested
failures or the 3 top-level failures mentions `IntersectAll`, `UnionAll`,
`Fold`, `Intersect`, `Union`, tasks 111/140, or `SET_DEFAULT_OPS`).

The task brief's own literal 5-file list (`test_prog_moves_migrated.py
test_exact_first_migrated.py test_mbpp_baseline_migrated.py
test_prog_property_migrated.py test_opgrammar_migrated.py`, labeled
"9-file" but only enumerating 5, one of which — `test_opgrammar_
migrated.py` — does not appear in the arc's historical 9-file list) was
ALSO run directly, independently: **3 failed / 161 passed**, the exact same
3 test names. Both suites agree; the fuller 9-file historical suite is
reported as primary above since it matches this arc's own established
convention and gives broader coverage.

## 7. What this document does NOT establish

1. Task 111/140's exact conversion mechanism (`retrieved_exemplar`'s
   hole-filler, not a raw `SynthEnumerate` top-level accept) is inferred
   from the same pattern `CEILING_REASSESSMENT_3_RESULTS.md`/`GROUPCOUNT_
   DICTMERGE_RESULTS.md` already found for tasks 64/88, not re-traced
   line-by-line through the retrieval engine's own source here either — the
   PASS verdict does not depend on this attribution being fully traced.
2. `DictFromPairs` (PREREG §3.6, the next-cheapest named candidate for
   tasks 277/465) was NOT built this rung, per the PREREG's own explicit
   single-variable scoping decision — it remains named, partially priced,
   not built.
3. Task 412's search-cost puzzle (an apparently-in-op-table composition
   that still doesn't get found within 140k+ candidates) was named in the
   PREREG but not diagnosed to its exact mechanism here either — out of
   this primitive-layer rung's scope.
4. The retrieved-exemplar-fallthrough NO-GO and the budget-wall NO-GO were
   re-confirmed unchanged (no new evidence sought or found) — not
   re-litigated.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 8. GO/NO-GO

**GO. Built, measured, zero regressions on every axis checked** (Rust
suite, named Python regression suite, full 3-arm MBPP battery with exact
task-id set-diff, post-build whole-population coverage re-check). Real
measured MBPP gain: `full` +2 (`{111, 140}`), `content_stripped` +2
(`{111, 140}`), `official` +2 (`{111, 140}`). Zero new `TermNode` variants —
the cheapest touch-point class this arc has used to date.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-4
git log --oneline -1   # on top of main @ 83b1f24
bash scripts/engine_build.sh   # then: python3 -c "...record_build()..." ; python3 domains/engine_provenance.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

Named 9-file regression suite:
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q
```

Rust suite:
```bash
cd runners/dsl && RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
```
