# Program Synthesis — SetLit / DictItems: precise characterization + Sort re-pricing — PREREG

**Date:** 2026-08-14. Follows `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md`
(the original `boundary:SetLit`/`term:DictItems` citation, §4.3/§7.4) and
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_RESULTS.md` (Rung 3's own
NO-GO on `Sort`, which named this exact gap as its reopening condition:
*"Re-open this call only if `boundary:SetLit` and/or `term:DictItems` are
separately taken first ... which would change Sort's realistic reach from 1
to up to 4"*). Baseline: MBPP 56/257, `main @ 2b1661c` (re-verified below).

**Status: investigation complete, GO on a narrower, more precisely-targeted
scope than the citing doc implied.** Root causes for both `SetLit` and
`DictItems` are precisely characterized by reading source and testing live
against the current engine (not inferred from the 2026-08-01 doc's naming).

---

## 1. What `boundary:SetLit` actually is TODAY — already closed at the wire layer

`STRUCTURAL_CEILING.md` §7.4 measured `Lit({1,2,3})` raising `TypeError:
Object of type set is not JSON serializable` on the 2026-08-01 engine. That
defect was **fixed on 2026-08-03** by `PROGRAM_SYNTHESIS_ARC6_LIT_WIRE.md`
(prereg amendment A8, `pyobj_to_json_term`/`WireMode::Value` in
`runners/dsl/src/py.rs`), which shipped **before** this session's Rung 1/2/3
work and is unrelated to it — the citing doc's table row was written before
the fix landed and was never updated after.

**Verified live on current `main`, this session:**

```
>>> s._inner.evaluate({"type":"Lit","value":{1,2,3}}, {})
{1, 2, 3}
```

No error. `domains/prog_synthesis.py`'s own `_wire`/`_unwire` (Rung 2, this
session) independently ALSO handles `set`/`frozenset` at the `inputs_json`
node-attr boundary (`{"__set__": [...]}` / `{"__fset__": [...]}`,
`py.rs::py_to_value` handles `PySet`/`PyFrozenSet` natively for node attrs —
a THIRD, independent path, never JSON at all). **All three boundaries a set
value can cross in this pipeline are closed.** `boundary:SetLit`, precisely
as `STRUCTURAL_CEILING.md` §7.4 named it, is a **stale citation** — not a
live defect.

**Live-run confirmation that nothing crashes end-to-end today:** running
tasks 141/232/473/475 through the real `scripts/mbpp_endgame_battery.py`
pipeline on unmodified `main` gives `gapped:enumerate_failed` for all four —
**not** a JSON/wire exception. The pipeline builds every spec row
successfully (including the frozenset-valued `expected` for 232/473); the
search simply never finds a fitting candidate.

## 2. The REAL residual gap: SynthEnumerate's OP_TABLE cannot PROPOSE a Set

`ProgEval`/the Term evaluator already has `Union`/`Intersect`/`Difference`/
`MapSet` (Terms, `term.rs`) — genuine, general, already-shipped, already-pure
Set operations. **`synth_enumerate.rs`'s OP_TABLE (30 op names) exposes NONE
of them.** This is the *exact* "gap is PROPOSAL, not EXECUTION" shape
`STRUCTURAL_CEILING.md` §2 already diagnosed for Tier 0/1 — it just wasn't
traced far enough to notice it also applies to Sets. Precise root cause:
**a missing enumerator OP, not a missing Term and not a wire boundary.**

## 3. `term:DictItems` — confirmed genuinely missing, and separately, `Sort`-by-value is a BIGGER gap than priced

Tested live: `Sum`/`MapSet`/Fold-style reduction over a `Value::Dict` all
return an empty/zero result (`Sum over dict: 0`, `MapSet over dict:
frozenset()`) — `synth_enumerate.rs`'s own `is_listlike` comment already
says this ("Dict is deliberately excluded ... a dict-shaped reduction is out
of this widening's scope"), confirmed live. **No Term extracts
`(key, value)` pairs from a Dict at all.** `term:DictItems` is real, priced
correctly by the original doc as "1 new Term."

**New finding, not in either prior doc:** task 475 (`sort_counter`) sorts a
dict **BY VALUE**, not by key — `Counter(d).most_common()`. A plain
element-wise `Sort` (the only thing `Sort` was ever priced as, Rung 3's own
`cmp_value_lex`-reuse design) sorts `(k, v)` TUPLES lexicographically **by
key first**, which does not reproduce `most_common()`'s by-value order. 475
therefore needs `DictItems` **plus a KEY-PROJECTED sort ("SortBy")** — an
unpriced, materially larger capability (a template-parameterized sort,
mirroring `FilterList`/`MapList`'s template mechanism, not a simple Unary
Term) that no document in this arc has priced. **NO-GO for 475 this
session** — named, not built; see §6.

## 4. Task-level dependency, confirmed by direct fixture read + hand witness (not assumed)

Real specs read from `tests/fixtures/mbpp/sanitized-mbpp.json`:

| id | needs (confirmed) | Sort needed? | witness built? |
|---|---|---|---|
| **141** | `pancake_sort` — plain ascending sort, all-int list → list | **yes, ALONE** (independent of SetLit/DictItems, confirms Rung 3's own finding) | `Sort(Var(a))`, size 2 |
| **232** | `heapq.nlargest(n, list)` → **frozenset** of the n largest | yes, PLUS a Set-wrap op | `SetMap(Slice(Reverse(Sort(a)),0,b), identity)`, size 8 |
| **473** | pairwise-canonicalize 2-tuples + set intersection | **NO — corrected finding** | `Intersect(SetMap(a,item,Sort(item)), SetMap(b,item,Sort(item)))`, size 9 |
| **475** | dict → sort BY VALUE → list of tuples | yes, but needs SortBy (unpriced, bigger) | not built — NO-GO this session |

**473 does not need `Sort` in the "sort a whole list" sense at all** — every
tuple in the corpus is arity-2, so `Sort` applied to a 2-tuple (ascending,
`cmp_value_lex`) IS the canonical `(min, max)` pair, exactly reproducing the
reference code's own `tuple(sorted(ele))`. This corrects
`STRUCTURAL_CEILING.md`'s framing (which listed `Sort` as necessary for all
four of 141/232/473/475) — 473's requirement is `SetMap`+`Intersect`+a
per-element `Sort`, general (not 2-tuple-specific in the Term itself; the
arity-2 case is what happens to occur in this corpus).

**141's reach is confirmed INDEPENDENT of SetLit/DictItems** (per the task
brief's own question) — it needs `Sort` alone, unaffected by this rung's
other work, exactly as Rung 3 found.

**All three witnesses (141, 232, 473) are HAND-VERIFIED live against every
real revealed row of their MBPP spec** (not inferred), via direct
`Substrate.evaluate()` calls, and are **within the search's default
`max_size=9` budget** by the enumerator's own size formula — the STRICT bar
`STRUCTURAL_CEILING.md` §5 defined (witness AND in-budget), not merely the
inventory-level HONEST bar.

## 5. What is buildable and its cost, mirroring Rung 1's touch-point discipline

**One new `TermNode`: `Sort { seq: TermIdx }`** — general, type-preserving
ascending sort via the already-shipped, already-safe `cmp_value_lex`
(`value.rs:461`, the SAME zero-blast-radius reuse Rung 3's own investigation
already vetted for exactly this purpose — `cmp_value` itself is untouched).
Full touch-point set (confirmed by reading Rung 1's own commit `5b8c2c7` as
the template): `term.rs` (variant + doc + `copy_subtree` + children
collector + evaluator, mirroring `Reverse`'s type-preserving-List/Tuple,
pass-through-otherwise shape exactly), `jsonio.rs` (`variant_name` +
`write_fields` + `read_term`), `reflect.rs` (`describe` + `reconstruct`),
`term_variants.rs` (regenerated via `tools/gen_term_variants.py`,
223→224).

**Zero new `TermNode`s: `SetMap`/`Intersect`/`Union` as SynthEnumerate ops**
— `MapSet`/`Intersect`/`Union` already exist as pure Terms; this is purely
`synth_enumerate.rs` op-table + builder wiring, the exact Tier-0 shape.
`SetMap` reuses `OpKind::ListMap` verbatim (same template pool, same
registration code path as `MapList` — only `build_list_ho`'s match gains one
arm producing `TermNode::MapSet` instead of `TermNode::MapList`).
`Intersect`/`Union` reuse `OpKind::ListBinary` verbatim (the `ConcatList`
precedent), with `list_binary_extra_cost` = 0 for both (direct wrap, no
injected fixed nodes).

**One new map-template entry: `Sort(Var(__item))`**, size 2, added to
`map_templates_by_size` — gated to fire ONLY when `SetMap` is in the op
list (a new `set_map_wanted` flag, narrower than the existing `map_wanted`
gate), so every already-shipped `MapList`-only spec's template pool is
BYTE-IDENTICAL to today.

**Evidence gating (Rung 1's own hard-won discipline, reused, not
reinvented):** `Sort` offered only when `spec_output_is_listlike ||
spec_output_is_setlike` (mirrors `TUPLE_BUILD_OPS`'s exact narrow,
output-type gate — NOT the broad "any var is list-shaped" test, precisely
because Rung 1 measured that even cheap unconditional Unary/Ternary
additions regressed task 132). `SET_BUILD_OPS = [SetMap, Intersect, Union]`
offered only when `spec_output_is_setlike` (new flag, mirrors
`spec_output_is_listlike` for `Value::Set`/`Value::FrozenSet`). This keeps
blast radius to the SAME narrow shape `TUPLE_BUILD_OPS` already uses, and
will be verified (not assumed) against the full 9-file regression suite +
full 257-task battery before/after, per house discipline.

## 6. GO/NO-GO, made from what was found

**GO** on: `Sort` (Term) + `SetMap`/`Intersect`/`Union` (ops) + the
`Sort(item)` map template, output-type evidence-gated. Target: **141, 232,
473** — all three hand-witnessed, in-budget, and the task-level dependency
confirmed genuine (not assumed from the old doc's naming).

**NO-GO** on `DictItems` + a key-projected `SortBy` for **475** this
session — `DictItems` alone is cheap and real, but converts ZERO tasks
without ALSO building `SortBy` (a materially bigger, unpriced capability: a
template-parameterized comparator, not a simple Term port). Building
`DictItems` alone, with no measured conversion, would repeat exactly the
mistake this arc's own discipline warns against ("do not take a unit because
one task needs it" — and here it doesn't even fully cover the one task).
Named as the next reopening condition, mirroring Rung 3's own precedent:
*re-open only if a key-projected/templated Sort ("SortBy") is separately
priced and built.*

**Estimate discipline (per house rule — do not just trust the count):** 3
witnessed candidates (141, 232, 473) is the CEILING this rung aims at; the
actual measured MBPP delta is reported in the RESULTS doc from a real
before/after battery run, not asserted here.

## 7. Plan

1. Worktree off `main` tip (re-verified fresh below), branch
   `progsyn-setlit-dictitems`.
2. Implement `Sort` (full touch-point set) + `SetMap`/`Intersect`/`Union`
   ops + template + evidence gates, per §5.
3. `cargo build --release` clean, `cargo test --lib --release` (accept the 3
   known `dim_infer_tests` flakes only if reproduced with
   `--test-threads=1`).
4. Re-run the three hand witnesses through the REAL `SynthEnumerate` search
   (not just direct `evaluate()`) to confirm the search itself finds them
   within budget — this is the step that turns "witness exists" into "the
   proposal layer can reach it."
5. Named 9-file regression suite green or honestly accounted.
6. Full 257-task MBPP battery before/after, exact task-id set diff, zero
   regressions confirmed.
7. Commit promptly once implementation passes isolated tests, before the
   slow full battery sweep (house discipline #7).
8. RESULTS doc with real numbers.
