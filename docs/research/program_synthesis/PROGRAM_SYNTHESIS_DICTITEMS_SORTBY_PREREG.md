# Program Synthesis — DictItems / SortBy (task 475): PREREG

**Date:** 2026-08-14. Worktree: `/home/matt/worktrees/progsyn-dictitems-sortby`,
branch `progsyn-dictitems-sortby`, off `main @ 938b595` (re-verified fresh
immediately before creating the worktree). Follows
`PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_RESULTS.md` §6-7, which named task 475's
remaining blocker — `term:DictItems` (confirmed missing) **plus a
key-projected `SortBy`** (`Counter.most_common()`'s shape) — as "a materially
bigger, unpriced capability" and explicitly left it NO-GO, unbuilt, "reopen
only if a key-projected sort is separately priced and built."

**Baseline, measured fresh, not assumed:** `full: runnable 61/257`
(`content_stripped: 60/257`), `OZMA_NO_LLM=1 python3
scripts/mbpp_endgame_battery.py` run on `main @ 938b595` before any change in
this rung, `results/mbpp_endgame.json` (`measured_at:
2026-08-14T16:25:12+1000`). Exact pass-id set for the `full` arm (61 ids):
`11, 16, 20, 58, 59, 69, 71, 74, 82, 84, 85, 89, 90, 106, 115, 120, 127, 131,
132, 135, 138, 139, 141, 142, 145, 161, 227, 230, 232, 233, 234, 249, 257,
266, 272, 276, 278, 281, 290, 309, 312, 393, 394, 404, 406, 410, 413, 418,
428, 433, 436, 443, 450, 451, 457, 458, 460, 472, 473, 474, 477`. Task 475
confirmed NOT in this set.

---

## 1. The gap, confirmed live against the real fixture

Task 475 (`tests/fixtures/mbpp/sanitized-mbpp.json`, `task_id: 475`):

```
prompt: "Write a function to sort a dictionary by value."
code:
    from collections import Counter
    def sort_counter(dict1):
        x = Counter(dict1)
        sort_counter = x.most_common()
        return sort_counter
test_list:
    sort_counter({'Math':81,'Physics':83,'Chemistry':87}) ==
        [('Chemistry',87),('Physics',83),('Math',81)]
    sort_counter({'Math':400,'Physics':300,'Chemistry':250}) ==
        [('Math',400),('Physics',300),('Chemistry',250)]
    sort_counter({'Math':900,'Physics':1000,'Chemistry':1250}) ==
        [('Chemistry',1250),('Physics',1000),('Math',900)]
```

**Confirmed, both halves, genuinely required:**

1. **Dict → (key,value) iteration** — the input is a `Dict`, the output is a
   list of `(key, value)` tuples. `is_listlike` (`synth_enumerate.rs`)
   deliberately excludes `Dict` by construction (doc comment: "a dict-shaped
   reduction is out of this widening's scope") — `term:DictItems` is
   genuinely absent from the search's reachable primitive set, exactly as
   `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §3.1 class S9 and the
   SetLit/DictItems RESULTS doc both found.
2. **Sort BY VALUE, descending** — `Counter.most_common()` sorts by the
   tuple's SECOND element, descending, stable on ties (Python's `sorted(...,
   key=itemgetter(1), reverse=True)`, CPython implements `reverse=True` via a
   reverse-sort-reverse trick that preserves original relative order on
   ties — NOT equivalent to "sort ascending then reverse the whole list",
   which would invert tie order). The existing `Sort` Term
   (`term.rs:5170`) is a **plain `cmp_value_lex` lexicographic** sort — over
   `(key, value)` tuples that sorts by KEY FIRST, the wrong field entirely.
   **No existing Term projects a sort key** — confirmed by reading
   `synth_enumerate.rs`'s full `OP_TABLE` (`Sort`, `Reverse`, `Slice` are all
   the ordering-related ops that exist, none takes a key expression).

**Tie behaviour is a non-issue for the actual asserts**: all three revealed
rows have pairwise-distinct values, so tie-order fidelity to
`Counter.most_common()`'s exact stable-reverse semantics does not gate
passing these three tests — recorded honestly, not assumed away as a general
claim.

## 2. Can `SortBy` be COMPOSED from the existing `Sort`, or is it a genuinely
   new primitive? — investigated, not assumed

**Composition-only route, priced and REJECTED on size budget, not
infeasibility in principle.** The only composition available with existing
Terms is: map each `(k,v)` pair to `(v,k)`, `Sort` ascending (lexicographic
now primary-sorts on `v`), `Reverse` for descending, map back to `(k,v)`.
Sizing this against the enumerator's own `size = 1 + Σ children` rule
(`synth_enumerate.rs` module doc):

- `DictItems(d)` = 2 (op + var).
- Swap template `Vec(IndexAt(item,1), IndexAt(item,0))` = 1 + 3 + 3 = 7
  (`IndexAt(item,k)` = 1(op)+1(var)+1(lit) = 3 each).
- Inner `MapList(DictItems(d), swap)` = 1 + 2 + 7 = **10** — already over
  `max_size=9` (the enumerator's default, and the budget every other rung
  this arc has used) **before `Sort`, `Reverse`, or the outer swap-back
  `MapList` are even added** (which would bring the full composed witness to
  roughly 19-20).

**This is a genuine, measured size-budget wall, not a search-budget
(`max_candidates`) issue** — the witness literally does not exist at
`max_size=9`, so no amount of `tested` budget would find it. Raising
`max_size` to ~20 to accommodate it would blow up the search combinatorially
for every OTHER spec sharing this op bucket (the exact class of cost this
arc's own `SET_DEFAULT_OPS`/`TUPLE_BUILD_OPS` discipline exists to avoid) —
not attempted, correctly rejected on the same reasoning `STRUCTURAL_CEILING.md`
used to reject `term:Recurse`.

**Conclusion: `SortBy` (a Term that sorts a sequence by a *projected key*,
keeping the original element) is a genuinely new capability, not reachable
by composing `Sort`+`MapList`+`Reverse` within budget.** This confirms, not
merely repeats, the prior doc's characterization.

## 3. Pricing `SortBy` and `DictItems` honestly — the actual finding of this
   investigation

**The prior doc's own uncertainty — "a template-parameterized comparator,
the same class of lift `FilterList`/`MapList` needed over plain
`Filter`/`Map`, not a simple Unary Term port" — turns out to be right about
the SHAPE and pessimistic about the COST**, because the machinery that lift
needs is **already built and already reused twice** (`MapList`→`MapSet`,
`MapList`→`IndexedMap`):

- **`SortBy` reuses `OpKind::ListMap`'s entire registration/template
  mechanism verbatim** — same `list_by_size` source, same
  `map_templates_by_size` template pool, only a new arm in `build_list_ho`
  (`"SortBy" => TermNode::SortBy { source, var_name: item, key: tmpl }`,
  mirroring the existing `"SetMap" => TermNode::MapSet{...}` arm exactly).
  **Zero new combinatorial search code** — the same reuse class `SetMap` was
  measured to be (`SET_DEFAULT_OPS` rung), not a new search dimension.
- **The one key template this task needs — `item[-1]` (the last/second
  element of a 2-tuple, i.e. the dict-item's value) — is ALREADY IN
  `map_templates_by_size` at size 3** (`synth_enumerate.rs`, the
  `for k in [0i64, -1i64] { ... IndexAt{seq:iv, index:lit} ... }` block,
  gated only on `map_wanted`). **No new template entries are required** —
  the exact thing the prior doc worried was unpriced (the template grammar
  lift) turns out to already exist for this task's specific need, built for
  a different reason (Rung 1's own general `item[0]`/`item[-1]` extraction
  templates).
- Witness size with `SortBy` as a real primitive:
  `Reverse(SortBy(DictItems(d), item, IndexAt(item,-1)))` =
  `DictItems(d)`=2, key template=3, `SortBy` node = 1+2+3=6,
  `Reverse` wraps = 7. **Well inside `max_size=9`.**
- **`DictItems` is `OpKind::Unary`**, sourced from the general `by_size`
  pool exactly like `Sort`/`Reverse` — zero new registration machinery,
  same cost class as `Sort`'s own port.

**Concrete touch-point accounting** (mirroring Rung 1/SetLit's own
full-cost template):

| | `DictItems` (Unary, no binder — `Sort`-class) | `SortBy` (binder — `MapList`/`IndexedMap`-class) |
|---|---|---|
| `term.rs` | variant def, `copy_subtree`, evaluator, `children()` collector (~4 sites, matches `Sort`: L232, L2961, L5170, L10379) | variant def, `copy_subtree` (~L3256), evaluator, `collect_into` free-var-exclusion arm (~L9982), `children()` collector (~L10184) (~5 sites, matches `MapList`/`MapSet`) |
| `jsonio.rs` | `variant_name`, write, read (3 sites, matches `Sort`: L216, L638, L1440) | `variant_name`, write (with `var_name` as a scalar sym field), read (3 sites, matches `MapList`: L316, L823, L1877) |
| `reflect.rs` | describe, reconstruct (2 sites, matches `Sort`: L403, L1254) | describe (with `ScalarSym` for `var_name`), reconstruct (2 sites, matches `MapList`: L610, L1484) |
| `term_variants.rs` | regenerated via `tools/gen_term_variants.py` | regenerated (same run) |
| `synth_enumerate.rs` | `OP_TABLE` entry, `build_op` arm | `OP_TABLE` entry, `build_list_ho` arm, `map_wanted` gate extended (`sort_by_wanted`, mirrors `set_map_wanted`) |

**Net: 2 new `TermNode` variants, one of them (`SortBy`) binder-shaped (the
`IndexedMap`/`MapList`/`MapSet` cost class — the single most expensive class
this arc has built), the other (`DictItems`) `Sort`-class. Zero new
combinatorial search code for either.** This is the honest price, and it is
lower than the prior doc's "materially bigger, unpriced" fear (no new
template-grammar entries needed, no new search dimension) but genuinely
higher than a single `Sort`-class port.

## 4. Second-task search — done for real, not assumed

Grepped the full 427-task vendored fixture (not just the 257 test split) for
`Counter`/`most_common`/`sorted(...items()...)`/dict-sort-by-value shape,
and separately for every task whose PROMPT mentions "dict"/"dictionary" (19
tasks: 87, 88, 97, 115, 237, 277, 301, 391, 464, 465, 475, 568, 582, 720,
722, 740, 758, 779, 796), reading each candidate's actual `code`/`test_list`.

**Result: 475 is genuinely isolated.** No other task shares the
dict-sort-by-value shape. The nearest candidate, **task 301**
(`dict_depth` — recursive depth of a nested dict), was named alongside 475
in `STRUCTURAL_CEILING.md`'s S9 class ("Sum over Dict... necessary for 301,
475") but that citation is for a DIFFERENT, unrelated missing primitive
(`Sum` over Dict values) — 301's real blocker, confirmed by reading its
`code`, is **recursion** (`term:Recurse`, `STRUCTURAL_CEILING.md`'s own Tier
3, explicitly named "do not take `term:Recurse` at all in this arc" and out
of scope here entirely). `DictItems`/`SortBy` do not move 301.

**Regression-safety cross-check, also done for real**: of the 19
dict-mentioning tasks, exactly one (115, "check whether all dictionaries in
a list are empty") is in the CURRENT 61-task pass set — and its top-level
spec variable is a **list of dicts** (`Value::List`), not a top-level
`Value::Dict`, so the planned evidence gate (`spec_has_dict_value`, checking
each row's variable value directly, the same shallow top-level-only test
`spec_has_string_value`/`spec_has_float_value` already use) does not fire
for it. **No currently-passing task has a top-level Dict-shaped variable —
the new ops can only ever be OFFERED to specs that are not currently
passing**, which is what makes the planned narrow evidence-gate safe by
construction, not merely by hope.

## 5. GO/NO-GO

**Leaning GO, registered before writing code**, for these reasons, weighed
honestly against the counter-case:

- **The counter-case (recorded, not dismissed):** 1 confirmed task against 2
  new `TermNode` variants (one binder-class) is, on raw "tasks per new
  Term" arithmetic, a *worse* ratio than `STRUCTURAL_CEILING_RUNG2_RUNG3`'s
  own `term:Sort` NO-GO (1 unwitnessed task against 1 new Term, rejected
  explicitly on this ratio). A mechanical repeat of that rung's own
  reasoning would say NO-GO here too, and that would be a legitimate,
  disciplined call.
- **What tips it to GO:** the *marginal, novel* engineering is materially
  smaller than the raw Term count suggests, because §3 found the two hard
  parts already solved by prior rungs — `OpKind::ListMap`'s registration
  path (proven 2× already: `MapList`→`MapSet`, `MapList`→`IndexedMap`) and
  the exact key template needed (`item[-1]`, already in the pool for an
  unrelated reason). This is the FOURTH instance of an established,
  mechanical pattern, not a new design — closer in risk profile to a
  boilerplate port than to `Rung3`'s "no precedent for what the capability
  even looks like" 1-task NO-GO. And unlike Rung 3's `term:Sort` (which
  turned out to reach 5 tasks via shared shape, unpredicted), this rung is
  the one place in the arc where the ceiling is HONESTLY 1 — that has been
  actively checked (§4), not left as an unstated risk.
- **This is the last named, precisely-characterized blocked task in the
  whole day's investigation chain** (232/473/141/428/71 closed by the
  merged SetLit/DictItems rung; 475 is what remains). Closing or honestly
  re-confirming NO-GO on it is the natural terminus of the arc either way;
  GO is chosen here because the price, once actually measured (not
  assumed), is lower than what was already rejected at the same yield.

**If the build measures out worse than priced here** (e.g. `SortBy`'s
evaluator turns out to need more touch points than the `MapList` template
predicts, or the evidence-gate regresses something not caught in §4's
audit), **this PREREG's GO does not bind the outcome** — a build that
measures badly reverts to NO-GO and is reported as such, per this arc's own
standing discipline (Rung 3 itself did exactly this in the other direction).

## 6. What this document does NOT establish

1. Whether `DictItems`/`SortBy` reach any task OUTSIDE the 257-task test
   split (the other 170 vendored-but-unused tasks) — not checked, out of
   this rung's scope (matches every prior rung's own denominator discipline).
2. Whether `SortBy`'s general form (arbitrary key template, not just
   `item[-1]`) is reachable for OTHER not-yet-examined specs beyond this
   task — only the one concrete witness this task needs was priced.
3. Whether `Value::Dict`'s internal iteration order (confirmed
   `Arc<[(Value,Value)]>`, order fixed at construction — NOT necessarily
   Python dict insertion order; `ARC6_STRUCTURAL_CEILING.md` §7.2 flags
   `Value::Dict`'s doc comment claims "sorted by key") ever matters for a
   task with tied values — task 475's own three revealed rows have no tied
   values, so this was not exercised, and is named rather than silently
   assumed safe in general.
