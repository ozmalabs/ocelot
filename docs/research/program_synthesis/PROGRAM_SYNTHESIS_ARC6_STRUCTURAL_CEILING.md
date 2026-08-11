# ARC 6 — THE STRUCTURAL CEILING: what actually blocks the 42

**Date:** 2026-08-01. Follows `PROGRAM_SYNTHESIS_ARC6_A_CEILING.md` §2, which
measured that **42 of the 53 live-unreached MBPP tasks (79%) are blocked by
something no import can supply**, and §3.1's two inversions — `sympy.ntheory`
strictly unlocking *zero* because its hits compute the maths exactly and then die
on a structural primitive, and `sympy.utilities.iterables` topping the strict list
only by supplying a frequency counter, a sort and a combination generator, i.e.
structural primitives dressed as a mathematics import.

This document measures the seam those two inversions point at. **The arc's
premise — that the pipeline is blocked on mathematics it already owns — is wrong
for this corpus. The residual is blocked on structure.**

**Status: MEASUREMENT. Nothing was built.** No file under `seeds/`, `runners/`,
`domains/`, `tests/` or any adapter was modified. No `git add`/`commit`/`stash`.
Artefacts: `scripts/arc6_structural_ceiling.py`,
`results/arc6_structural_ceiling.json`, this document.

**Contamination discipline.** MBPP test-split `code` was read for MEASUREMENT
classification only; no prompt text and no reference code entered any codebook,
cue vocabulary or taught shape. **Held-out rows were never read**: every witness
is scored on `split_rows(rows, "primary")["revealed"]` only, mechanically audited
(`held_out_isolation.clean = true`). Every claim is a **paired id list**.

**Engine provenance, because it is part of the measurement's identity.**
`site-packages/substrate_rs.pth` is an absolute path into the *canonical* tree and
`_native.abi3.so` is gitignored, so a bare script in a worktree silently imports a
different binary than the one it believes it is measuring. **That is live here,
not hypothetical:** this tree's engine is `5c1b472fe674…`; the canonical tree's is
`7dd9af13a038…` — two different binaries. `engine_preamble()` is called before any
`substrate_rs` import and the sha256 is recorded in the artefact beside every
number. Reproduce with `OZMA_NO_LLM=1 python scripts/arc6_structural_ceiling.py`
(twin-run byte-identical; `id_hash=deada67a876a742e`).

---

## 0. The one-paragraph answer

The 42 are blocked by **28 distinct structural units**, and the ladder is
`10 → 26 → 32 → 42`. **10 ids** (`18, 75, 98, 106, 161, 257, 290, 310, 424, 450`)
need **zero new Term variants** — they are op-table entries, filter/map template
entries, and making four already-shipped Terms accept a string. That is exactly
the shape of arc 4's S4 widening, which added 11 ops with no new `TermNode` and
moved 25/85. Getting from 10 to 42 costs **17 new Term variants, a cross-cutting
correction to string ordering, a Value/JSON boundary fix, and a recursion binder**
— and the 7 ids that recursion unlocks are the *least* likely of the 42 to
convert, because a self-referential binder makes an enumerative search worse as it
makes it richer. **Zero of the 42 are blocked by a missing dimension** — every
coordinate involved is an in-frame integer, so this seam is strictly weaker than
arc 5's π result and strictly cheaper. The A-ceiling's 5→27 cherry-picking trap
**does not reproduce in the same form** (you cannot cherry-pick `sort` the way you
can cherry-pick `perrin_sum`); it reproduces as **cost hiding**, and in exactly one
place as itself — generator *order*, where task 255 and task 462 split.

---

## 1. Null conditions, registered before the answer

*(Written into this document before the ranked list below was read back, per the
project's standing prereg discipline.)*

**The structural seam is a null if any of the following hold.**

1. **The zero-new-Term bundle does not convert.** The 10 B0 ids are unlocked *at
   the inventory level*: the primitives exist and the op table is the only gate.
   If a built version converts fewer than the S4-discounted expectation (§6),
   then "the arc-4 shape repeats" is false and the seam is a null **even though
   every probe in this document is true**.
2. **The conversions arrive only via per-task operators.** If the op list that
   converts is not diffable against §4's general unit list — if it contains
   `remove_odd_index_chars` or `binary_reflected_powerset` — the number is 42,
   not 10, and it is not a result.
3. **`fix:StringAsSequence` cannot be landed without breaking existing callers.**
   It is the single largest cheap unit (necessary for 8 ids) and it is the one
   tier-0 unit that is *not* purely additive: `Count(str)` returns `0` today and
   any caller depending on that changes behaviour. If it cannot ship, B0 drops
   from 10 to 5 and the cheap class is not cheap.
4. **`term:Sort` cannot be landed without either shipping a knowingly-wrong string
   order or moving frozen fixtures.** See §7.2. If the only two options are a
   wrong sort and a fixture migration, the ordering class is mis-scoped and its 4
   ids must be re-priced.
5. **Inventory does not survive reach.** Every bundle number is an *inventory*
   ceiling. Only 6 ids have a witness verified in budget (§5). If the rest do not
   survive a live search once the ops exist, the honest number is 6, not 10.
6. **The S4 reach-vs-conversion ratio repeats.** S4 moved 25/85 off
   `gapped:enumerate_failed` and only 8 were fully correct — 32%. If that ratio
   holds, a bundle's *pass* yield is about a third of its *reach* yield, and any
   headline quoting reach as conversion is inflated ~3×.
7. **A conversion has no constructed witness.** Six coincidental fits are already
   on this project's record.

**What a null would and would not mean.** A null here says the *enumerator's
proposal layer* cannot be widened cheaply — it says nothing about MBPP. That is a
sharper statement than a Seam A null, because §3 establishes that the *execution*
layer already has every one of these primitives.

---

## 2. The finding that reframes the whole seam: the gap is PROPOSAL, not EXECUTION

`ProgEval` — the evaluator every accepted program actually runs on — **already
has** `sorted`, `split`, `replace`, `join`, `capitalize`, `count`, `enumerate`,
`reversed`, `round`, `str`, `int`, strided and negative-step slicing, string
subscripting, list comprehensions with `not in` guards, `dict.items()`, and
set/dict/tuple construction. All verified live (21 `CONFIRMED_PRESENT` probes in
`primitive_probes`).

`SynthEnumerate` — the layer that *proposes* — has **30 op names** and none of
them is any of those.

**So cost class (c) "missing `ProgEval` primitive" is almost empty.** The pipeline
can already *run* the answers to most of the 42; it cannot *propose* them. Only
four things are missing at the Prog layer, and each is measured:

| missing at `ProgEval` | evidence | tasks |
|---|---|---|
| `str.format` | `extern:unimplemented:format` | 390 |
| `collections.Counter` | `extern:unimplemented:Counter` | 88, 283 |
| `itertools.combinations` | `extern:unimplemented:combinations` | 255 |
| a *correct* string order | §7.2 | 141, 232, 473, 475 |

This is the single most consequential fact in the document, and it is the reason
the honest ceiling can be as cheap as it is.

---

## 3. Taxonomy — the 42 by the specific primitive that blocks each one

Tasks **do not partition**: most need more than one unit, and a partition would
overstate every single-unit yield. So each unit is listed with the ids it is
**necessary for**, and §4 does the set arithmetic. Full per-task requirement sets
with a one-line `why` are in
`results/arc6_structural_ceiling.json :: per_task_requirements`.

### 3.1 The classes

| # | class — the specific primitive | necessary for (ids) | n | cost class |
|---|---|---|---|---|
| **S1** | **A string is ATOMIC** — it has no length, no index, no last element and no members. `Count("abc")→0`, `IndexAt("abc",1)→None`, `Last("abc")→None`, `In("a","cat")→False`, all measured | `11, 18, 226, 310, 424, 437, 450, 479` | **8** | (a) enum-op, **0 new Term** |
| **S2** | **Sequence construction** — the `Vec` Term builds a tuple and is not in the enumerator's op table | `255, 257, 262, 290, 310, 462, 473, 475` | **8** | (a) enum-op, **0 new Term** |
| **S3** | **Recursion / unfold to depth n** — `Fold` folds an *existing* source; there is no `range`, no self-reference, no fixpoint | `99, 260, 265, 283, 301, 448, 462` | **7** | (a) new **capability** |
| **S4** | **Slice** — no general sequence slice; `StringSlice` is string-only and refuses a negative end | `11, 170, 232, 262, 265` | **5** | (a) 1 new Term |
| **S5** | **Value→string coercion** — `Join` emits `Int(4)` for a non-string element | `99, 421, 439, 479` | **4** | (a) 1 new Term |
| **S6** | **Ordering** — no `Sort`/`Sorted`/`SortBy` Term anywhere | `141, 232, 473, 475` | **4** | (a) 1 new Term |
| **S6b** | **…and string order is WRONG** — `cmp_value` compares interner ids | `141, 232, 473, 475` | **4** | **(c) engine semantics, cross-cutting** |
| **S7** | **String split into substrings** — `Tokenize` returns `(offset,len)` spans | `102, 118, 411` | **3** | (a) 1 new Term |
| **S8** | **(index, element) binding** — no Term binds an index alongside the element (S4 §4.5's named gap) | `11, 226, 437` | **3** | (a) 1 new Term |
| **S9** | **Dict iteration** — a reduction over a Dict yields nothing; `is_listlike` excludes Dict by construction | `301, 475` | **2** | (a) 1 new Term |
| **S10** | **String replace** | `230, 474` | **2** | (a) 1 new Term |
| **S11** | **Frequency map** (Counter) | `88, 283` | **2** | (a) 1 new Term |
| **S12** | **Upper/capitalize** — only `CaseFold`/lower exists | `102, 411` | **2** | (a) 1 new Term |
| **S13** | **List concatenation** — `Cat` is *string* concat and emits Rust debug reprs on lists; `Fold`+`Append` is the real route | `106, 462` | **2** | (a) enum-op, **0 new Term** |
| **S14** | **Set/frozenset at the `Lit` boundary** — S4 §4.3's flagged task-115 breakage, reproduced | `232, 473` | **2** | **(b) boundary** |
| **S15** | **Filter/map template pool** — `item in <list var>`; `len(item)` vs a *variable*; a reduction nested inside a predicate | `161`; `450`; `75` | **3** | (a) template, **0 new Term** |
| **S16** | singletons: dict merge `87`; substring count `172`; round `419`; reverse `456`; product fold `98`; argmax-by-length `290`; parse-int `439`; format `390`; combinations `255` | — | 9 | mixed |
| **S17** | **Pure search budget** — every op already exists | `264` | **1** | **(d) search** |

### 3.2 Two corrections to the A-ceiling's per-task reasons, both found by invocation

- **Task 450** was recorded as a *"template pool gap"*. It is not. The predicate
  `len(item) == n` fails because **`Count` on a string returns 0**, so the filter
  matches nothing — a missing primitive, not a missing template. Live witness:
  `FilterList(a, e, Eq(Count(e), b))` → `()` on every revealed row.
- **Task 264** was classified `missing_structural_primitive` (*"whole-input
  conditional branch"*). It is not structural at all. **Every operator it needs is
  already in `DEFAULT_OPS`**, and a hand-built `IfThenElse(Lte(a,2), a*10.5,
  21+(a-2)*4)` reproduces **2/2 revealed rows**. Its size is **14** against
  `max_size=9`. Task 264 is a **class (d) search-budget** case and belongs with
  the A-ceiling's `budget` bucket, not with the 42.

That second correction moves the honest structural population to **41**, and it is
recorded rather than silently absorbed.

---

## 4. Ranked by tasks-unlocked per unit of work

`unlocked alone` = tasks for which this unit is the *only* thing missing.
`necessary for` = tasks that cannot convert without it. **Quoting the second as
the first is how a structural ceiling inflates**, so both are given.

### 4.1 Tier 0 — ZERO new `TermNode` (the exact arc-4 S4 shape)

| rank | unit | alone | necessary for | blind? |
|---|---|---|---|---|
| 1 | **`fix:StringAsSequence`** — make the existing `Count`/`IndexAt`/`Last`/`In` accept a string | **2** (`18, 424`) | **8** | YES |
| 2 | **`op:TupleOf`** — expose the existing `Vec` Term as an op | **1** (`257`) | **8** | YES |
| 3 | **`op:ConcatList`** — list concat as `Fold`+`Append` (exactly how `JoinList` was built) | **1** (`106`) | 2 | YES |
| 4 | **`tmpl:item_in_listvar`** — `item (not) in <list var>`, over the existing `In` Term | **1** (`161`) | 1 | YES |
| 5 | **`tmpl:nested_reduction`** — a quantifier over the bound item inside a predicate | **1** (`75`) | 1 | YES, but it widens the template grammar from bounded to recursive — S4 §4.4's named architectural seam |
| 6 | **`op:ProdList`** — expose the existing `Prod` Term (the `SumList` twin) | **1** (`98`) | 1 | YES |
| 7 | **`tmpl:len_item_vs_var`** — compare `len(item)` to a *variable*, not only a constant | 0 | 1 (`450`) | YES |
| 8 | **`op:ArgMaxLenOver`** — the arg-twin of the shipped `MaxLenOver` | 0 | 1 (`290`) | **WEAK** — general as "argmax by a projection"; the by-*length* variant is one step from bespoke |

**Tier 0 total: 8 units, 0 new Term variants, 10 ids** —
`18, 75, 98, 106, 161, 257, 290, 310, 424, 450`.

### 4.2 Tier 1 — new Term variants that are standard-library universal

Each of these already exists *at the `ProgEval` layer* (§2), so each is a Term-layer
port of a shipped behaviour, not a new idea.

| unit | alone | necessary for | new Terms |
|---|---|---|---|
| `term:Replace` | 2 (`230, 474`) | 2 | 1 |
| `term:Slice` | 1 (`170`) | **5** | 1 |
| `term:Str` | 1 (`421`) | **4** | 1 |
| `term:Split` | 1 (`118`) | 3 | 1 |
| `term:StrCount` | 1 (`172`) | 1 | 1 |
| `term:Round` | 1 (`419`) | 1 | 1 |
| `term:Reverse` | 1 (`456`) | 1 | 1 |
| `term:IndexedMap` | 0 | 3 (`11, 226, 437`) | 1 |
| `term:Capitalize` | 0 | 2 (`102, 411`) | 1 |
| `term:ParseInt` | 0 | 1 (`439`) | 1 |

**Tier 0+1: 18 units, 10 new Term variants, 26 ids.** The 10 new variants buy
**+16 ids = 1.6 ids per Term variant.**

### 4.3 Tier 2 — ordering, the boundary, and dict

| unit | alone | necessary for | cost |
|---|---|---|---|
| `term:Sort` | 0 | 4 (`141, 232, 473, 475`) | 1 new Term |
| `fix:StrOrder` | 0 | the same 4 | **cross-cutting engine semantics** (§7.2) |
| `boundary:SetLit` | 0 | 2 (`232, 473`) | Python/JSON boundary fix |
| `term:DictItems` | 0 | 2 (`301, 475`) | 1 new Term |
| `term:GroupCount` | 1 (`88`) | 2 | 1 new Term |
| `term:DictMerge` | 1 (`87`) | 1 | 1 new Term |

**Tier 0+1+2: 24 units, 14 new Term variants, 32 ids.** +6 ids for 4 new
variants plus two fixes with real blast radius.

### 4.4 Tier 3 — the expensive tail

| unit | alone | necessary for | cost |
|---|---|---|---|
| `term:Recurse` | 2 (`260, 448`) | **7** (`99, 260, 265, 283, 301, 448, 462`) | a **capability** decision: it changes what the search space *is* |
| `term:Combinations` | 0 | 1 (`255`) | 1 new Term; blind-nameable, and §7.4 shows the order *happens* to be right |
| `term:Format` | 1 (`390`) | 1 | 1 new Term; **WEAK** — one MBPP task uses it and nothing else does |
| `search:max_size` | 1 (`264`) | 1 | raise the budget |

**Everything: 28 units, 17 new Term variants, 42 ids.**

---

## 5. Strict reach — where the claim is verified, and where it is arithmetic

A **witness** is a hand-built Term tree, evaluated live on the task's own revealed
rows, that reproduces every one of them. A witness proves the *primitive inventory
suffices*; it does not prove the search will find the composition.

**Witnesses (inventory suffices, all revealed rows matched):**

| id | witness | size | in `max_size=9`? |
|---|---|---|---|
| 257 | `Vec(b, a)` | 3 | ✅ |
| 98 | `Div(Prod(a), Count(a))` | 6 | ✅ |
| 106 | `Fold(a, acc←b, Append(acc, i))` | 6 | ✅ |
| 161 | `FilterList(a, x, Not(In(x, b)))` | 6 | ✅ |
| 75 | `FilterList(a, s, Eq(MaxOver(s, e, Mod(e, b)), 0))` | 9 | ✅ (but the *template grammar*, not the size, is what blocks it) |
| 290 | `Vec(MaxOver(a,x,Count(x)), Argmax(a,x,Count(x)))` | 9 | ✅ |
| 264 | `IfThenElse(Lte(a,2), a·10.5, 21+(a−2)·4)` | **14** | ❌ — budget |

**`strict_reach.witness_and_in_budget_ids` = `75, 98, 106, 161, 257, 290` (6).**

**The honest boundary, stated plainly:** the size half of that table is
*arithmetic* under the enumerator's own documented rule (`size = 1 + Σ children`),
not a live search — because measuring the search requires *adding the op*, which is
a build. This is the same boundary the A-ceiling drew when it said its 5 strict ids
are unlocked "in principle". **6 is the number that survives both halves; 10 is the
inventory number.**

---

## 6. The two ceilings, side by side

| reading | n | ids | what it costs |
|---|---|---|---|
| **STRICT — witness verified AND in budget** | **6** | `75, 98, 106, 161, 257, 290` | 0 new Term variants |
| **HONEST B0 — zero new `TermNode`** | **10** | `+18, 310, 424, 450` | 0 new Term variants, 8 units |
| HONEST B1 — plus stdlib Term ports | 26 | `+11, 102, 118, 170, 172, 226, 230, 262, 411, 419, 421, 437, 439, 456, 474, 479` | **10 new Term variants** |
| HONEST B2 — plus order, boundary, dict | 32 | `+87, 88, 141, 232, 473, 475` | 14 new variants **+ the string-order fix + the set boundary** |
| **INVENTORY B3 — everything** | **42** | `+99, 255, 260, 264, 265, 283, 301, 390, 448, 462` | **17 new variants + a recursion capability** |
| **CHERRY-PICKED — one bespoke operator per task** | **42** | all of them | an op table that encodes the answer key |

### 6.1 The gap, and why the A-ceiling's trap does not reproduce in the same form

The A-ceiling found **5 → 27 → 60**, a 5.4× and 12× inflation available purely by
changing the granularity of the import unit. **That mechanism is granularity: a
per-task kernel (`perrin_sum`) bought reach a general module (`sympy.ntheory`) did
not, so the big number encoded the test-split answers.**

Here, **the general operator set reaches the same 42 the bespoke one would.**
`sort`, `slice`, `split`, `replace`, `str`, `round`, `reverse`, `enumerate`,
`dict.items` are the standard library of every programming language; you cannot
cherry-pick `sort` the way you can cherry-pick `perrin_sum`. So B3 and the
cherry-picked ceiling coincide at 42, and the "is this unit nameable before the
population is read" test — which did all the work in the A-ceiling — mostly passes
here.

**The inflation mechanism is different, not absent. Here it is COST HIDING.**
B0 = 10 costs *zero* new Term variants. B3 = 42 costs **17 new Term variants, a
cross-cutting engine-semantics correction, a boundary fix, and a new capability**.
Every step is individually defensible in prose ("we just need a sort; sorting is a
real operation"), and the aggregate is a rewrite of the DSL's value layer sold as
an operator list.

> **The rule that keeps 10 from becoming 42, stated so it can be reused:**
> in an import seam you audit the *naming* of the unit; in a structural seam you
> audit the *price*. Count new `TermNode` variants, not operator names — a name is
> free and a variant is not.

### 6.2 The one place the A-ceiling's trap does reproduce exactly

**Generator order, and tasks 255 and 462 split on it — measured, not argued.**

- Task **255** (`combinations_with_replacement`): a blind generator reproduces the
  revealed rows **exactly, order included** (`order_matches_on_every_revealed_row
  = true`). 255 is an honest unlock.
- Task **462** (powerset): a blind size-lexicographic powerset reproduces
  **neither** the outer order **nor** the element order inside each subset —
  `natural_head = [[], ['orange'], ['red'], ['green']]` against
  `expected_head = [[], ['orange'], ['red'], ['red','orange']]`. The operator that
  converts 462 is *binary-reflected*, and it would be chosen **because 462 needs
  it**. That is a cherry-pick.

This is the identical failure the A-ceiling measured for
`sympy.utilities.iterables.subsets` on task 462 (0/3) — reproduced here from a
different direction, which is worth more than either measurement alone.
**Honest inventory ceiling excluding order-specific operators: 41.**

### 6.3 Reach is not conversion — a prior from this very pipeline

Arc 4 S4 added 11 ops and moved **25/85** off `gapped:enumerate_failed`, of which
only **8** were fully correct. **32%.** On the same corpus, the same enumerator and
the same protocol, a structural widening's *pass* yield was about a third of its
*reach* yield. Applying that prior:

- B0's 10 inventory ids → **~3 expected conversions**;
- B1's 26 → ~8; B2's 32 → ~10; B3's 42 → ~13.

Those are not predictions to be scored; they are the discount any headline must
carry. And the discount for `term:Recurse`'s 7 ids should be *worse* than 32%,
because a self-referential binder makes an enumerative search combinatorially
harder as it makes it richer.

---

## 7. What broke while measuring — breakage is the real cost signal

### 7.1 The engine hazard is live in this tree, not hypothetical

The coordinator's mid-task correction was right and it was load-bearing. Without
`engine_preamble()`, a bare script in this worktree imports the **canonical**
tree's `substrate_rs` — and the two binaries are genuinely different here
(`5c1b472fe674…` vs `7dd9af13a038…`). A subtler mismatch than an
`UnknownTermType` crash would have returned entirely plausible numbers. **No probe
in this document was taken before the preamble was in place**, and the engine
sha256 is recorded in the artefact beside the numbers.

### 7.2 `sorted` on strings is WRONG, and it is a function of process history

The single most expensive thing found. `ProgEval`'s `sorted` orders strings by
**interner symbol id** — i.e. by the order the process happened to first see each
string:

```
fresh substrate                      : sorted(["pear","apple","fig"]) -> ('pear','apple','fig')
after interning "zzz" then "apple"   : sorted(["pear","apple","fig"]) -> ('apple','pear','fig')
Python                               :                                  ['apple','fig','pear']
```

Root cause, at source: `value.rs::cmp_value` —
`(Value::Str(x), Value::Str(y)) => x.0.cmp(&y.0)`.

**Blast radius**, all following from that one line: `sorted`/`min`/`max`/`Argmax`/
`MaxOver` over strings; the canonical storage order of every `Value::Set` and
`Value::FrozenSet` (whose doc comment claims they are "sorted … deterministic
regardless of construction order" — true only *within one process history*);
`Value::Dict` key order (documented "sorted by key"); and `Gt`/`Lt`/`Gte`/`Lte`
between two strings.

**Why this matters for scoping:** `term:Sort` looks like one new Term variant. It
is one new Term variant **plus** a correction whose diff can move any frozen
artefact containing a string-keyed set or dict. Shipping a sort that is knowingly
wrong on strings is not an option; shipping the fix is a fixture-migration
question. **This is unpriced in every estimate before this document, exactly as
`Rational(9,2) != 4.5` was unpriced before the A-ceiling.** It is the same *kind*
of cost: a value-layer semantics boundary surfacing as integration work.

### 7.3 Four Terms whose names are right and whose values are wrong

Reading the source would have confirmed each of these. Invocation refuted them.
This is the brief's "verify both directions" requirement earning its keep.

| Term | what the name says | what it returns | tasks it falsely "solves" |
|---|---|---|---|
| `Count(str)` | `len` of a string | **`0`** | 450 — and this is why S4's `len(item)` filter template never fired on strings |
| `IndexAt(str, i)` / `Last(str)` | character at an index | **`None`** | 424 — `item[-1]` **is** in S4's map-template pool, and it silently produced `(None, None, None)` |
| `In(char, str)` | character membership | **`False`** | 18 |
| `Cat([list, list])` | list concatenation | **`'Tuple([Int(1), Int(2)])Tuple([Int(3)])'`** — Rust debug reprs | 106 |
| `Join(sep, [1,2])` | join with a separator | **`'ID-is-Int(4)-UTS'`** on task 421's own row | 421 |
| `Tokenize(text)` | split into words | **`((0,1),(2,1),(4,1))`** — `(offset,len)` spans | 118, 310 |
| `Union(dict, dict)` | merge | **`frozenset()`** | 87 |
| `Sum` over a `Dict` | reduce over values | **`0`** | 301, 475 |

**And the converse error, caught by the same instrument.** Task **172**'s
`StringIndexOf(a, "std")` matches **row 1 exactly** (`3 == 3`) and fails rows 2–4
(`5,4,0` vs `1,2,1`). A probe that sampled one row would have reported a
conversion. That is the same under-sampling failure the A-ceiling caught on task
87 row 1 — **the second instance of it in two days, on two different seams.**

### 7.4 The `Lit` boundary refuses sets — 2 of the 42, named

S4 §4.3 flagged the `{"type":"Lit","value":…}` boundary as a live gap for
set-valued specs (task 115) and did **not** test it. Tested here:
`Lit({1,2,3})` → `TypeError: Object of type set is not JSON serializable`, same for
`frozenset`. **Tasks 232 and 473 cannot have their example rows expressed at all** —
they are blocked *before* any search happens. Cost class **(b)**, and it is the
only (b) in the population.

The boundary is **asymmetric**, which is a useful detail: a set can come *out* of
`ProgEval` (`prog_set_out` → `{1, 2}`) even though it cannot go *in* through `Lit`.
So the fix is on the Python→JSON side only.

### 7.5 Smaller things, recorded rather than smoothed over

- **A list and a tuple are the same value.** `Lit([1,2,3])` and `Lit((1,2,3))` both
  realise as `Value::Tuple`. Tasks 106/257/262/290 assert *tuples* and 118/141/161
  assert *lists*; the value model cannot tell them apart, so any verdict that
  distinguished them would refute correct programs for a reason the domain does not
  have. The witness comparator normalises both, and this is stated because a future
  reader will otherwise "fix" it.
- **`MkDict` takes alternating `k, v, k, v` items, not pairs.** My first probe
  passed a `Vec` pair and got `{}` — a silent wrong answer, found only by checking
  the value against a hand-computed expectation. Fixed before any number was taken.
- **`StringSlice` has no negative index**: `StringSlice("hello", 0, -1)` → `''`, not
  `'hell'`. Refutes the obvious witness for task 456.
- **An unknown op name is a silent no-op, not a trap.** `ops=["Bogus"]` returns
  `found: false, halt_reason: "saturated"`; `ops=["Bogus","Plus"]` solves normally.
  Good news for scoping — the op table is the sole gate and every addition is
  purely additive, the same precondition arc-4 S4 relied on — but it also means a
  typo in an op name degrades silently.

---

## 8. Dimension vs operator — the stronger claim is NOT available here

Arc 5's evidence is that supplying a missing *dimension* closes tasks unreachable
at any search size: it supplied π exactly and closed `82, 85, 139, 233, 276, 312`.
The A-ceiling identified 4 more live-unreached dimension ids (`163, 246, 252,
293`). A dimension claim is strictly stronger than an operator claim, so the
question is worth asking of every structural blocker.

**Answer: zero of the 42 are blocked by a missing dimension.**

The test is CLAUDE.md's own decision procedure — *is this value IN a frame, or
BETWEEN frames?* A missing dimension is a coordinate the frame does not have at
all (π, an irrational, a complex argument — all cross-frame, all in
`Hom(frame, frame)`). Every structural blocker here produces a value **already
inside the value domain** (`Value::Tuple`, `Value::Str`, `Value::Dict`), and every
coordinate involved — a character index, a list position, a digit place — is an
**in-frame integer**.

**Two borderline cases, recorded because each looks like the stronger claim:**

1. **`(index, element)` binding.** *For:* with repeated elements, **no**
   composition of the current ops can distinguish two occurrences — every
   element-wise term is a function of the element alone. That is literally
   unreachable-at-any-search-size, the property arc 5's claim rests on.
   *Against:* a position is the tuple's own integer ordinal and `IndexAt(seq, k)`
   already reads it. The coordinate is in the frame; only the **binder** that
   carries it into a map body is missing. **Verdict: operator.**
2. **String as a sequence.** *For:* a string is atomic in the current value domain
   — measured, four ways — so a character is unreachable at any search size.
   *Against:* the character index is again an in-frame integer, and the Terms exist
   and simply refuse `Value::Str`. This is type coverage in shipped Terms, not an
   absent coordinate. **Verdict: operator.**

**Consequence, and it is one fact stated twice:** the structural seam is a
**weaker** claim than arc 5's π result — no unreachable-at-any-size argument is
available — and a **cheaper** one — nothing here requires a new value domain. The
`missing_dimension` list is empty and the `operator` list is all 42.

---

## 9. Recommended scope

**Take tier 0 and nothing else in the first cut: 8 units, 0 new `TermNode`
variants, 10 ids, of which 6 have a witness verified in budget.**

`op:TupleOf`, `op:ProdList`, `op:ConcatList`, `op:ArgMaxLenOver`,
`tmpl:item_in_listvar`, `tmpl:len_item_vs_var`, `tmpl:nested_reduction`,
`fix:StringAsSequence`.

Why this cut and not a bigger one:

1. **It is the arc-4 S4 shape exactly**, and that shape has already worked once in
   this repo: 11 ops, zero new `TermNode`, 25/85 moved. This is the only structural
   precedent that exists, and matching it is the cheapest way to test whether it
   generalises.
2. **`fix:StringAsSequence` is the highest-leverage single unit in the entire
   document** — necessary for 8 ids, needed by tier 1's `IndexedMap` and `Str`
   classes too, and zero new variants. It is also the **riskiest** tier-0 unit, and
   that is exactly why it should be attempted where the blast radius is small
   enough to observe: it is a *semantic change to shipped Terms*, not an addition
   (null condition 3).
3. **Do not take `term:Sort` yet, despite it being the obvious next thing.** It
   drags in §7.2's cross-cutting order correction, and that correction should be
   priced against frozen fixtures *before* it is committed to — precisely as the
   A-ceiling said to price the exact→rendered boundary before committing to F5.
4. **Do not take `term:Recurse` at all in this arc.** It is 7 ids on paper and it
   changes what the search space *is*; its inventory yield and its conversion yield
   are further apart than any other unit here.
5. **Do not take `term:Format`** — one task uses it, nothing else does. Taking a
   unit because one task needs it is the structural form of the A-ceiling's
   `perrin_sum`.

**Price before committing:** (i) whether `Count`/`IndexAt`/`Last`/`In` can accept
strings without moving an existing caller; (ii) whether the string-order fix moves
any frozen artefact — this is the cost that mirrors `Rational(9,2) != 4.5` and it
is currently unpriced.

**Reproduce with:** `OZMA_NO_LLM=1 python scripts/arc6_structural_ceiling.py`
(deterministic; two consecutive runs byte-identical modulo timestamp and engine
stamp; `id_hash=deada67a876a742e`; engine `5c1b472fe674…`).
