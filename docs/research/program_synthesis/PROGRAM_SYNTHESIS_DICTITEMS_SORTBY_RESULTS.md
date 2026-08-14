# Program Synthesis — DictItems / SortBy (task 475): RESULTS

**Date:** 2026-08-14. Worktree: `/home/matt/worktrees/progsyn-dictitems-sortby`,
branch `progsyn-dictitems-sortby`, off `main @ 938b595` (re-verified fresh
immediately before creating the worktree). Follows
`PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_PREREG.md` (commit `cd5beff`), registered
GO before any code was written.

**Status: GO, built, measured. MBPP `full` 61/257 → 62/257, `content_stripped`
60/257 → 61/257, `official` 89/257 → 90/257 — all three arms +1, exact
newly-passing id `{475}`, zero regressions on any arm.**

Commits: `cd5beff` (PREREG), `4c09dc9` (implementation + live witness
confirmation), this document's commit (measurement + write-up).

---

## 1. What was built

Two new `TermNode` variants (`runners/dsl/src/term.rs`):

- **`DictItems { seq }`** — Python's `dict.items()`: a `Value::Dict` becomes
  a `Value::List` of `(key, value)` 2-tuples (`Value::Tuple`), in the Dict's
  own stored order. `OpKind::Unary`, sourced from the enumerator's general
  `by_size` pool — the exact `Sort`/`Reverse` reuse class, zero new
  registration machinery. Non-Dict input passes through unchanged.
- **`SortBy { source, var_name, key }`** — a stable sort of `source`'s
  elements by a PROJECTED key (the `var_name` binder evaluates `key` per
  element via `cmp_value_lex`, the same comparator `Sort` already uses),
  keeping the ORIGINAL elements — unlike `MapList`, whose template computes
  the OUTPUT value, this template computes only the sort key. Reuses
  `OpKind::ListMap`'s search-registration path and `map_templates_by_size`
  template pool VERBATIM (the `SetMap`/`IndexedMap` precedent) — confirmed
  live, not just designed: `build_list_ho`'s existing dispatch got one new
  arm (`"SortBy" => TermNode::SortBy{...}`), and `map_wanted`'s gate got one
  new disjunct (`sort_by_wanted`), mirroring `set_map_wanted` exactly. No
  new template entries were needed — the one key template this task uses
  (`item[-1]`, projecting a 2-tuple's value) was already in the pool from
  Rung 1's own general `item[0]`/`item[-1]` extraction templates.

**Full touch-point set** (both variants): `term.rs` (definition,
`copy_subtree`, evaluator, `collect_into` free-var-exclusion arm,
`children()` collector — 5 sites each), `jsonio.rs` (`variant_name`, write,
read — 3 sites each), `reflect.rs` (describe, reconstruct — 2 sites each),
`term_variants.rs` (regenerated via `tools/gen_term_variants.py`, 224→226
variants; `DictItems`=47, `SortBy`=48), `synth_enumerate.rs` (`OP_TABLE`
entries, `build_op`/`build_list_ho` arms, `map_wanted` gate, `term_json`
witness-printer arms — see §2 for why the last one was necessary), plus a
new evidence-gated typed default: `spec_has_dict_value` (a top-level,
per-row Dict-value check, the same shallow test `spec_has_string_value`/
`spec_has_float_value` already use), pushing `DictItems`/`SortBy`/`Reverse`
into the `spec_is_list_shaped` branch's op bucket only when true — narrow by
construction, matching the `SET_DEFAULT_OPS`/`Round`/`IndexedMap` evidence-
gate precedent, not a blanket append to `LIST_EXTRA_OPS`.

**Net: 2 new `TermNode` variants (one binder-shaped), zero new combinatorial
search code.** This matches the PREREG's own pricing (§3) exactly.

## 2. Two real bugs found only by running the search end-to-end, not by
   reading the code

Both were found via the same method the PREREG committed to using: build,
then verify the actual witness is found, not just that the Terms evaluate
correctly in isolation.

1. **`DictItems`'s outer container type.** First implementation returned
   `Value::Tuple` for the whole `dict.items()` result (matching the inner
   pairs' own `Value::Tuple` type by analogy). The search then could not
   find the witness even with the exact right 3-op inventory
   (`found:false`, `tested:69`, `distinct:9` — a suspiciously small,
   saturated-looking search). Root-caused via a direct `Eq` probe between
   the composed witness and the spec's own `Lit`-parsed expected output:
   Python's `[('Chemistry', 87), ...]` — a LIST of TUPLES — parses through
   the `Lit` wire boundary's `__list__`/`__tuple__` tagging
   (`runners/dsl/src/py.rs:1152-1155`, `WireMode::Value`) into
   `Value::List(Value::Tuple, Value::Tuple, ...)`, NOT
   `Value::Tuple(Value::Tuple, ...)` — contradicting an assumption carried
   from `ARC6_STRUCTURAL_CEILING.md` §7.5 ("a list and a tuple are the same
   value") that turned out to hold only for the BARE, untagged
   `{"type":"Lit","value": [...]}` JSON-array reading path, not the tagged
   `__list__`/`__tuple__` wire format real MBPP specs are built through.
   **Fixed to match Python's own semantics** (which is also the CORRECT
   fix, not a workaround): `dict.items()`/`list(d.items())` returns a LIST
   of tuples in real Python, so `DictItems`'s outer container is
   `Value::List`, each pair stays `Value::Tuple`. This is recorded because
   it corrects a citation this rung inherited, not because it changes any
   design decision — `SortBy`/`Reverse` were always meant to be
   type-preserving, and now correctly are.
2. **`term_json` (the module's own witness pretty-printer) panicked**:
   `internal error: entered unreachable code: candidates are built only
   from the op table + leaves` — a SEPARATE exhaustive match over
   `TermNode` (`synth_enumerate.rs:1036`) that the compiler does not check
   against the enum (its catch-all `_ => unreachable!(...)` compiles fine
   regardless of enum coverage), so this was invisible until the search
   actually tried to render a found witness containing `DictItems`/
   `SortBy`. Fixed by adding both arms alongside `Sort`'s own (the same
   shape `MapSet`/`Union` already have there).

Neither bug was caught by `cargo build`, `cargo test`, or code review of the
touch-point list alone — both needed a live, end-to-end `SynthEnumerate`
call against the real spec to surface, which is why this document's
measurement includes the direct-probe log (§3) rather than just the
battery's aggregate numbers.

## 3. Live confirmation of the exact predicted witness

Before running the full battery, `SynthEnumerate` was called directly
against task 475's real 3-row spec (both `ops=["DictItems","SortBy",
"Reverse"]` explicit, and `ops=None`/the automatic typed default):

```
found: True, halt_reason: solved, size: 7, tested: 63 (explicit) / 7899 (default)
term: Reverse(SortBy(DictItems(Var(dict1)), item, IndexAt(Var(item), -1)))
```

This is EXACTLY the witness priced in PREREG §3 (`Reverse(SortBy(DictItems(d),
item, IndexAt(item,-1)))`, predicted size 7) — confirms the pricing exercise,
not just the build. The `ops=None` run also confirms the evidence-gate
(`spec_has_dict_value`) wires correctly end-to-end: the automatic typed
default reaches the same witness without a caller-declared `ops` list.

## 4. Rust test suite

`cargo build --lib --release`: clean, no errors (only pre-existing warnings).

`cargo test --lib --release -- --test-threads=1`, run with the documented
pyo3-extension-module linking workaround
(`RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13"
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"`):

```
test result: ok. 774 passed; 0 failed; 4 ignored; 0 measured; 0 filtered out
```

## 5. Real measurement — before/after, exact task-id set diff, all three arms

**A genuinely fresh, independent "before" was re-measured in the PRIMARY
tree** (`/home/matt/ozmadev/ocelot`, unmodified `main @ 938b595`,
`OZMA_NO_LLM=1 python3 scripts/mbpp_endgame_battery.py`, run in this same
session after the worktree's changes were already made — an independent
checkout, not a cached number):

```
before (main @ 938b595): full 61/257, content_stripped 60/257, official 89/257
after  (this branch):    full 62/257, content_stripped 61/257, official 90/257
```

**Exact set diffs, all three arms:**

| arm | before (n) | after (n) | newly passing | regressed |
|---|---|---|---|---|
| `full` | 61 | 62 | `{475}` | `{}` |
| `content_stripped` | 60 | 61 | `{475}` | `{}` |
| `official` | 89 | 90 | `{475}` | `{}` |

`before_pass_ids ⊆ after_pass_ids` holds on all three arms — verified by
direct set computation from `results/mbpp_endgame.json`'s `runnable_rows`,
not by trusting the aggregate counts. **Both `full` and `content_stripped`
were checked and reported separately, per the house discipline note that
these can genuinely diverge on a marginal task** — here they move together
(both +1, same id), so no divergence to report this time, but the check was
done, not skipped.

**No second task was found or claimed** — matching the PREREG §4 corpus
search (task 475 is genuinely isolated; task 301's superficially-similar
`STRUCTURAL_CEILING.md` S9 citation is a red herring, its real blocker is
out-of-scope recursion). The measured gain is exactly the PREREG's own
central estimate, no more, no less.

## 6. Regression — verified against a genuinely fresh, independently-run
   clean baseline, not assumed

Named 9-file suite, run in the worktree (with the two artifact-copying
housekeeping notes in §7): **3 failed, 241 passed.**

The SAME suite, run independently in the unmodified PRIMARY tree
(`/home/matt/ozmadev/ocelot`, `main @ 938b595`, no code changes, its own
natively-present `results/` artifacts, no copying needed): **3 failed, 241
passed — the identical top-level count, and byte-identical failing test
names**:

- `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
  (pre-existing task-267 `sum_of_two`/`range_sum_spine` construction-path
  drift — present on clean `main`, unrelated to this rung)
- `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`
- `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  (both meta-tests surfacing the same already-documented inner "unexpected"
  set: `test_retrieval_migrated.py[106,115,242]` and
  `test_mbpp_arc3_endgame_migrated.py`'s artifact-hash/headline checks — the
  same "shared mutable output path" fragility this arc's prior rungs
  (`PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_RESULTS.md` §5) already documented
  and re-confirmed present on clean `main` here, independently, not
  inherited from that doc's characterization)

**Zero new Rust-suite failures (§4), zero new Python-suite failures — this
rung's failure signature is IDENTICAL to clean `main`'s own, confirmed by
running both, not by citation.**

## 7. Housekeeping note — worktree artifact gap, not a code defect

The fresh worktree's `results/` directory (gitignored, ~1188 files / 21GB on
the primary tree) initially carried almost none of the generated artifacts
`domains/prog_synthesis.py`, `domains/prog_chunk_growth.py`, and several
`tests/test_*_migrated.py` files read at import/fixture time (e.g.
`prog_construction_scan.json`, `prog_chunk_mine.json`,
`mbpp_zero_shot_baseline.json`, `mbpp_train_diet.json`,
`prog_synthesis_battery.json`, `code_synthesis_baseline.json`,
`mbpp_arc3_endgame.json`, plus several `run*_checkpoints/*.json` files) —
this produced a FIRST battery run showing `full: runnable 0/257` (misread
initially as "zero runnable rows"; it is actually `pass_over_runnable`'s `k`
=0, i.e., every task legitimately reached `run_task` but every one hit
`runner_exception:FileNotFoundError` on a missing artifact — a `k=0/n=257`
reading, not `n=0`). Fixed by copying the specific closure of referenced
files from the primary tree (never a blanket `cp -r` of the 21GB directory).
**This is a worktree-provisioning gap, not a code defect** — confirmed by
the fact that the SAME missing-file errors, on the SAME task, disappear the
moment the referenced artifact is present, and the primary tree (which
already has every artifact) never exhibited it.

## 8. GO/NO-GO, honestly restated after building

**GO, delivered**, exactly as priced in the PREREG: `DictItems` + `SortBy`,
evidence-gated (`spec_has_dict_value`, the `SET_DEFAULT_OPS`/`Round`/
`IndexedMap` precedent). Real measured MBPP gain **+1 on every arm**
(`full`/`content_stripped`/`official`, all the same id, `475`), zero
regressions, zero new Rust-suite failures, zero new Python-suite failures
(confirmed against an independently fresh clean-`main` re-run, not assumed).

This closes the last named, precisely-characterized blocked task from this
arc's own investigation chain (`232`/`473`/`141`/`428`/`71` closed by the
already-merged `progsyn-setlit-dictitems` rung; `475` is what remained).

## 9. What this document does NOT establish

1. Whether `DictItems`/`SortBy` reach any task outside the 257-task test
   split (the other 170 vendored-but-unused tasks) — not checked, out of
   this rung's scope (matches every prior rung's own denominator
   discipline).
2. Whether `SortBy`'s general form (an arbitrary key template, not just
   `item[-1]`) is reachable for OTHER, not-yet-examined specs beyond this
   task — only the one concrete witness this task needs was priced or
   measured.
3. Whether `Value::Dict`'s internal iteration order ever matters for a task
   with TIED values — task 475's own three revealed rows and its two
   additional held-out/official rows all have pairwise-distinct values, so
   Python's stable-reverse tie-breaking semantics (§ PREREG §1) were never
   exercised by this measurement.
4. Whether the `term_json` panic (§2.2) has sibling gaps for any OTHER
   already-shipped Term not reachable through the normal `OP_TABLE` +
   `build_list_ho`/`build_op` composition path — only the two variants this
   rung added were checked; a full audit of `term_json`'s exhaustiveness
   against every `TermNode` variant was not attempted.

## Artifacts

- Worktree: `/home/matt/worktrees/progsyn-dictitems-sortby`, branch
  `progsyn-dictitems-sortby`.
- Commits: `cd5beff` (PREREG), `4c09dc9` (implementation), this document's
  commit (measurement + write-up).
- `results/mbpp_endgame.json` (after) in the worktree; the primary tree's own
  `results/mbpp_endgame.json` holds the independently fresh "before"
  measurement (regenerated in place during this rung's own verification —
  gitignored, not a tracked change).
