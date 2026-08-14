# Program Synthesis — SetLit / DictItems: RESULTS

**Date:** 2026-08-14. Worktree: `/home/matt/worktrees/progsyn-setlit-dictitems`,
branch `progsyn-setlit-dictitems`, off `main @ 30b7d9c`. Commits `ebee2e3`
(Sort Term + SetMap/Intersect/Union ops) and `cb8c97b` (`_plain()` fix,
measured numbers). Follows
`PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_PREREG.md`, registered before any build.

**Status: GO, built, measured. MBPP 56/257 → 61/257, +5, zero regressions.**

---

## 1. The exact citation and what it turned out to mean

`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §4.3/§7.4 named
`boundary:SetLit` ("the `Lit` boundary refusing Python `set`") and
`term:DictItems` ("no Term binds Dict iteration") as necessary, alongside
`Sort`, for tasks 141/232/473/475.
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_RESULTS.md`'s own Rung 3
re-read the real fixtures and found only 141 reachable by `Sort` alone,
naming `SetLit`/`DictItems` as the reopening condition for the other three.
**This task was that reopening question, and the honest answer to "what IS
`boundary:SetLit`, precisely" turned out to be two different things layered
on top of each other:**

1. **The literal defect the 2026-08-01 doc measured — `Lit({1,2,3})` raising
   `TypeError` — was ALREADY FIXED on 2026-08-03**, two days after that
   measurement, by `PROGRAM_SYNTHESIS_ARC6_LIT_WIRE.md` (prereg A8,
   `pyobj_to_json_term`/`WireMode::Value`, `runners/dsl/src/py.rs`), a rung
   this session's Rung 2/3 investigation never cross-referenced. Verified
   live on current `main` before writing a line of new code: `Lit({1,2,3})`
   evaluates cleanly. This is a **stale citation, not a live defect** — the
   PREREG's own §1 makes this the headline finding, and it holds.
2. **The REAL residual gap, found by reading `synth_enumerate.rs`'s actual
   `OP_TABLE`, is a PROPOSAL-layer gap, not a wire boundary**: `Union`/
   `Intersect`/`MapSet` were already shipped, already-pure Terms
   (`term.rs`), and `SynthEnumerate`'s 30-ish op names exposed none of
   them. The search could not PROPOSE a Set-valued candidate, even though
   the engine could already EXECUTE one — exactly the "gap is proposal,
   not execution" shape `STRUCTURAL_CEILING.md` §2 diagnosed for Tier 0/1
   and never traced as far as Sets.

`term:DictItems` was confirmed genuinely missing (Dict reduction/iteration
still returns empty/zero, live-tested), priced correctly by the original
doc. What was NOT in either prior document: task 475 needs `DictItems`
**plus a key-projected `SortBy`** (sort BY VALUE, `Counter.most_common()`),
a materially bigger, unpriced capability — named in §6 below, not built.

## 2. Task-level dependency, confirmed live, not assumed

| id | real need | witnessed | in real search budget |
|---|---|---|---|
| 141 | `Sort` alone (confirmed independent of SetLit/DictItems, per Rung 3) | `Sort(a)`, size 2 | yes, `tested=18` |
| 232 | `Sort` + a Set-wrap op (`SetMap`) + `Reverse`/`Slice` (already shipped) | `SetMap(Slice(Reverse(Sort(a)),0,b))`, size 8 | yes, `tested=19772` |
| 473 | **NOT general Sort** — `SetMap`+`Intersect`, `Sort` applied per-ELEMENT to a 2-tuple (== `(min,max)`) | `Intersect(SetMap(a,Sort),SetMap(b,Sort))`, size 9 | yes, `tested=74830` |
| 475 | `DictItems` (missing) **+ SortBy-by-value** (missing, bigger, unpriced) | not built | — |

**473 corrects `STRUCTURAL_CEILING.md`'s own framing** — it does not need a
general "sort the whole list" capability at all; every tuple in the corpus
is arity-2, so `Sort` applied to a 2-tuple ascending IS the canonical
`(min, max)` pair, exactly reproducing the reference code's own
`tuple(sorted(ele))`. The dependency is real but narrower than priced.

## 3. What was built

One new `TermNode`: **`Sort { seq: TermIdx }`** — type-preserving ascending
sort via `cmp_value_lex` (`value.rs:461`), the SAME zero-blast-radius reuse
Rung 3's own PREREG already vetted (`cmp_value` itself, the boot-order
comparator every frozen fixture depends on, is never touched). Full
touch-point set, mirroring Rung 1's own commit as the template: `term.rs`
(variant + `copy_subtree` + children collector + evaluator), `jsonio.rs`
(`variant_name`/`write_fields`/`read_term`), `reflect.rs` (`describe`/
`reconstruct`), `term_variants.rs` (regenerated via
`tools/gen_term_variants.py`, 223→224).

Zero new `TermNode`s: **`SetMap`** (`OpKind::ListMap`, `MapList`'s
Set-returning twin — reuses `MapList`'s exact registration path and
template pool), **`Intersect`/`Union`** (`OpKind::ListBinary`, the
`ConcatList` precedent, direct Term wrap, 0 extra nodes). One new map
template, **`Sort(Var(__item))`**, gated to `set_map_wanted` only so every
already-shipped `MapList`-only spec's template pool stays byte-identical.

**The one real engineering surprise, found by measuring rather than
assuming:** a naive typed-default (layering `Sort`/`SetMap`/`Intersect`/
`Union` onto the existing `DEFAULT_OPS ∪ LIST_EXTRA_OPS` bucket) reproduced
**exactly Rung 1's own lesson** — `tested==200000, found:false` for BOTH
232 and 473, despite both being witnessed and in-budget. Fixed the same way
Rung 1 fixed it: a **dedicated, narrow, shape-tailored typed default**
(`SET_DEFAULT_OPS`, the `DEFAULT_STR_OPS` precedent) for a Set-shaped-output
spec, excluding `DEFAULT_OPS`'s arithmetic and `LIST_EXTRA_OPS`'s dozen
list-reduction ops entirely. Measured before/after this fix:

| | 232 (`DEFAULT_OPS ∪ LIST_EXTRA_OPS ∪` new ops) | 232 (`SET_DEFAULT_OPS`) | 473 (same layering) | 473 (`SET_DEFAULT_OPS`) |
|---|---|---|---|---|
| found | true (barely — `176977/200000`) | true | **false** | true |
| tested | 176977 | 19772 | 200000 | 74830 |

This branch is mutually exclusive with task 132 (Rung 1's own budget-fragile
spec) by construction — 132's output is a STRING, never Set-shaped, so it
can never reach `SET_DEFAULT_OPS` at all.

**A second, genuinely new residual, found only by running the REAL
end-to-end pipeline (not just the raw `SynthEnumerate` call):**
`domains/prog_synthesis.py`'s `_plain()` — the JSON-safe flattener behind
`eval_and_record`'s `got_json` debug attr — had no `set`/`frozenset` case,
because no program could ever produce one before this rung. `got_json =
json.dumps(_plain(got))` raised `TypeError: Object of type frozenset is not
JSON serializable` for exactly 232 and 473 (`runner_exception:TypeError` in
the battery's own outcome taxonomy) even though the raw `SynthEnumerate`
call already found the correct witness. Fixed with a `sorted()` conversion
(mirrors `mbpp_endgame_battery.py`'s own `_json_default` precedent exactly)
— equality-preserving for every `_plain(a) == _plain(b)` comparison site
already in the module.

## 4. Real measurement — before/after, exact task-id set diff

Both arms run fresh, same protocol as every prior rung this arc
(`scripts/mbpp_endgame_battery.py`, `OZMA_NO_LLM=1`, twin-run determinism
confirmed `det_identical=True` on both). **"Before" is this rung's own
branch point** (`main @ 30b7d9c`, freshly re-measured in an independent
worktree, not the stated 56 taken on faith):

```
before (main @ 30b7d9c): full: runnable 56/257 p=0.217899
after  (this branch):    full: runnable 61/257 p=0.237354
```

**Exact set diff:**

```
before_pass_ids (n=56): [11,16,20,58,59,69,74,82,84,85,89,90,106,115,120,127,
  131,132,135,138,139,142,145,161,227,230,233,234,249,257,266,272,276,278,
  281,290,309,312,393,394,404,406,410,413,418,433,436,443,450,451,457,458,
  460,472,474,477]
after_pass_ids  (n=61): before ∪ {71, 141, 232, 428, 473}
newly passing: [71, 141, 232, 428, 473]
regressed (lost): []
before_pass_ids ⊆ after_pass_ids: True
```

**56 → 61, +5, exceeding the PREREG's own witnessed-3 ceiling by 2.** 141,
232, 473 are exactly the three hand-witnessed, in-budget candidates. 71
(`comb_sort`) and 428 (`shell_sort`) were NOT predicted individually in the
PREREG, but are an honest, expected consequence of the same mechanism, not
a fluke: both are "sort a list of ints" specs — the identical behavioural
shape as 141 (`pancake_sort`) — so `Sort`'s own output-type-gated typed
default (`spec_output_is_listlike`) reaches all three MBPP tasks that share
that shape, exactly as `Sort` "reaching the same 42 the bespoke one would"
was `STRUCTURAL_CEILING.md`'s own stated expectation for general stdlib
operators (§6.1: "you cannot cherry-pick `sort`"). Mirrors Rung 2's own
precedent (task 115, "a genuine bonus... not predicted in advance") of this
same arc measuring past its own estimate rather than falling short.

## 5. Regression — verified against a genuinely fresh baseline, not assumed

`cargo test --lib --release`: **774/774** — 772 direct pass + the 2 known
`shape_decode::dim_infer_tests` thread-race flakes under default parallel
execution, confirmed identical to the documented pre-existing flake via
`--test-threads=1` (22/22 green in that module).

Named 9-file suite: **3 failed, 241 passed on BOTH before and after** —
verified byte-identical, not assumed, by running the exact same suite
against a fresh, independent "before" worktree at this rung's own branch
point (`30b7d9c`):

| failure | before | after |
|---|---|---|
| `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live` | FAIL | FAIL (identical: task-267 `sum_of_two`/`range_sum_spine` construction-path drift) |
| `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift` | FAIL | FAIL (identical inner "unexpected" set: `test_retrieval_migrated[106,115,242]`, `test_retrieval_ceiling_migrated`, `test_search_reach_migrated`'s 4, `test_mbpp_arc3_endgame_migrated`'s 2) |
| `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift` | FAIL | FAIL (same inner set) |

All three, and every one of the inner meta-sweep's own "unexpected"
sub-failures, are **byte-identical between the two independently-run
worktrees** — genuinely pre-existing, not caused by this rung, confirmed
rather than inherited from a prior doc's characterization (the house
discipline's own explicit trap-avoidance).

## 6. GO/NO-GO, honestly restated after building

**GO, delivered:** `Sort` + `SetMap`/`Intersect`/`Union`, output-type
evidence-gated (`SET_DEFAULT_OPS`, the `DEFAULT_STR_OPS` precedent). Real
measured MBPP gain **+5** (141, 232, 473, 71, 428), zero regressions,
zero new Rust-suite failures, zero new Python-suite failures.

**NO-GO, named and left unbuilt:** `DictItems` + a key-projected `SortBy`
for task 475. `DictItems` alone is cheap (one new Term, the same
touch-point shape as `Sort`) but converts **zero** tasks without also
building `SortBy` — a materially bigger, genuinely unpriced capability (a
template-parameterized comparator, the same class of lift `FilterList`/
`MapList` needed over plain `Filter`/`Map`, not a simple Unary Term port).
Building `DictItems` alone, with a measured zero conversion, would repeat
exactly the mistake this arc's own discipline warns against — the
`term:Format` precedent ("one task uses it, nothing else does... named
explicitly to avoid quoting it as a reach number later"). **Reopen only if
a key-projected sort is separately priced and built** — the same shape of
condition Rung 3 itself used to hand off to this rung.

## 7. What this document does NOT establish

1. Whether a key-projected `SortBy` (task 475's real remaining blocker) is
   itself worth building — priced nowhere in this arc yet, named as the
   next reopening question, not answered here.
2. Whether `SET_DEFAULT_OPS`'s narrow bucket leaves reach on the table for
   OTHER, not-yet-examined MBPP tasks whose output is Set-shaped but who
   also need an op this bucket excludes (e.g. a filtered/counted Set
   construction) — not probed beyond the two witnessed ids' own needs.
3. Whether `_plain()`'s new `set`/`frozenset` branch has any OTHER
   downstream reader (beyond the `got_json` crash site and the
   `_plain(a) == _plain(b)` comparison sites already audited in §3) whose
   behaviour meaningfully changes now that it never silently `TypeError`s
   — the fix was scoped to the actual crash found, not a full audit of
   every one of `_plain`'s ~15 call sites individually.
4. `retrieved_exemplar`-constructed passes (428) were not separately
   traced to confirm the exemplar itself required no additional fix beyond
   `Sort` existing — its construction differs from 71/141/232/473's direct
   `SynthEnumerate` witnesses, and that mechanism was not independently
   audited here.

## Artifacts

- Worktree: `/home/matt/worktrees/progsyn-setlit-dictitems`, branch
  `progsyn-setlit-dictitems`.
- Commits: `ebee2e3` (Sort Term + ops), `cb8c97b` (`_plain()` fix + measured
  numbers).
- `results/mbpp_endgame.json` (after) in that worktree; the independent
  "before" worktree (`/home/matt/worktrees/progsyn-setlit-before`, detached
  at `30b7d9c`) holds the before measurement for reproduction.
