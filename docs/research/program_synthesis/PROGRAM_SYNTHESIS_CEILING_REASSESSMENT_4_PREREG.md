# Fresh ceiling reassessment at the post-GroupCount/DictMerge baseline — PREREG

**Date:** 2026-08-16. Base `main @ 83b1f24` ("Merge progsyn-rungs124-reconciliation:
Rungs 1, 2, 4 staleness-checked against the reassessment PREREG"), verified
fresh via `git log --oneline -1 main` at the start of this task and
re-verified against the diff between the prior blocked attempt's recorded
tip and this one (identical — `git log --oneline c4e6616..83b1f24` shows
only two documentation-only commits, `d0c71dc`/`83b1f24`, zero touched
`runners/`/`domains/`/`seeds/`/`scripts/` files, confirmed by an empty
`git diff --stat` over that range restricted to those paths). Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-4`, branch
`progsyn-ceiling-reassessment-4` — reused directly from the prior,
disk-full-blocked attempt (it did no code work and left a clean tree,
`data/` already symlinked and verified resolving to the real corpus).

**Headline finding, stated up front: a single, zero-new-`TermNode`,
fully-live-verified fix exists — expose `IntersectAll`/`UnionAll` as two new
named `SynthEnumerate` ops that compose ENTIRELY from already-shipped Terms
(`Fold`+`Intersect`/`Union`+`IndexAt`, the exact `ConcatList`/`JoinList`
op-table-exposure precedent), gated into the already-narrow, already-safe
`SET_DEFAULT_OPS` bucket. Both target witnesses (tasks 111, 140) are
independently hand-evaluated end-to-end against ALL THREE rows each
(revealed AND held-out), 100% exact match, using nothing but the engine's
own `evaluate()` binding on already-shipped Terms — no speculative design,
no untested primitive.** This is cheaper than every prior rung in this
arc's own record (0 new `TermNode` variants, vs. 1-2 for `Sort`/`DictItems`/
`SortBy`/`GroupCount`/`DictMerge`), and the regression surface is the
smallest yet measured: exactly 2 currently-passing canaries (232, 473) share
the routing bucket being touched.

Investigation-only up to §5; §6 builds the fix under full house discipline
(genuine from-source rebuild, paired battery, named regression suite,
RESULTS doc) if this document's own plan survives that build.

---

## 1. Real baseline, confirmed live (not trusted from the cached JSON)

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run fresh in this worktree on the existing
(already-current) build:

```
full:              69/257  p=0.268482  ci=[0.218003, 0.325781]  det_identical=True
content_stripped:  68/257  p=0.264591  ci=[0.214414, 0.321702]  det_identical=True
official:          98/257  p=0.381323  ci=[0.324101, 0.44204]   det_identical=True
```

`head` in the resulting `results/mbpp_endgame.json` reads `83b1f24...`,
byte-identical to `git log --oneline -1 main` — this is a genuine fresh
measurement on the current tip, not a stale artifact. This matches the task
brief's own stated current baseline (69/68/98) exactly, and matches
`PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_RESULTS.md`'s own reported "after"
numbers, confirming no code has moved between that rung's merge and this
one's starting point (also confirmed structurally in the header above via
`git log`/`git diff --stat`).

## 2. Failure-cause grouping — the real 188 currently-failing runnable tasks

Every one of the 188 non-passing `full`-arm runnable tasks (257 − 69) was
individually re-run through `domains.prog_synthesis.synthesize_from_request`
directly, reading the FULL `read_goal()` dict, via
`scripts/ceiling3_diag_sweep.py` (already on `main`, reused verbatim — no
edits needed, since it reads the pass-id set from the just-refreshed
`results/mbpp_endgame.json`) — the exact same methodology
`CEILING_REASSESSMENT_2_PREREG.md`/`CEILING_REASSESSMENT_3_PREREG.md` used.
Output: `results/ceiling3_diag_sweep.json`, 188 rows.

| outcome | n | what it means |
|---|---|---|
| `gapped:enumerate_failed` | **96** | reached `SynthEnumerate`, found nothing |
| `accepted_holdout_fail` | **51** | a candidate was ACCEPTED (revealed rows fit) but disagrees on a held-out row |
| `gapped:property_verdict_reject` | **26** | a candidate was built and REJECTED by a held self-verifying property check |
| `gapped:structural_verdict_reject` | **10** | a candidate was built and REJECTED by a structural-trap detector |
| `not_recognized` | **1** | the request text itself was never recognized |
| `runner_exception:ValueError` | **1** | an uncaught Python exception aborted the whole attempt |
| `gapped:no_shape` | **1** | no cover-parts / operator shape matched at all |
| `gapped:exhausted` | **1** | attempt budget exhausted before any status resolved |
| `runner_exception:TypeError` | **1** | an uncaught Python exception aborted the whole attempt |

**The TOTAL reconciles exactly**: CEILING_REASSESSMENT_3's own population
was 191 (257−66). Between that measurement and today, exactly 3 tasks
converted to `pass` — 64 (the SortBy gate-widening REASSESSMENT_3 itself
built), then 87 and 88 (GroupCount/DictMerge) — taking the baseline
66→67→69 and the failing population 191→190→188, matching this sweep's own
188 exactly. **The PER-CATEGORY breakdown is NOT independently reconciled
here** — REASSESSMENT_3's own PREREG reports category counts (99/51/26/10/…)
but not the individual task-id membership of `gapped:enumerate_failed`
specifically, so this document cannot verify, task-by-task, which category
each of the 3 conversions came out of, or whether any OTHER task moved
between categories as a side effect of the GroupCount/DictMerge build (the
kind of secondary shift CEILING_REASSESSMENT_3 §3.2 and GROUPCOUNT_
DICTMERGE_RESULTS §4 both documented can happen when one construction lane's
availability changes another's). The category counts measured today
(96/51/26/10/1/1/1/1 = 188) are reported as a fresh, directly-measured fact,
not asserted to reconcile cell-by-cell against REASSESSMENT_3's own table —
doing so would require REASSESSMENT_3's own raw per-task sweep output, which
is a gitignored `results/` artifact from a now-superseded worktree and was
not available to check against.

`gapped:enumerate_failed` sub-splits the same way prior rungs found:

```
budget-exhausted (tested == 200,000 exactly):  82
genuinely saturated under budget (<200,000):   14
```

Saturated task ids: `97, 111, 117, 140, 277, 283, 299, 301, 305, 412, 417,
462, 465, 470` — a population that overlaps heavily, but not completely,
with REASSESSMENT_3's own named-and-deferred candidates (§3.3, `97, 111,
140, 277, 283, 301, 465` all recur; `117, 299, 305, 412, 417, 462, 470` are
newly examined below, §3.4).

The `accepted_holdout_fail`/`*_verdict_reject` population (87) is the exact
same `retrieved_exemplar`-sourced population `PROGRAM_SYNTHESIS_
RETRIEVAL_FALLTHROUGH_RESULTS.md` already sized and decisively NO-GO'd
(93.3% false-accept rate under a naive fallthrough) — not re-investigated
here; that document's NO-GO stands unchanged (§3.5).

## 3. What's newly reachable — checked directly against real fixtures and a
   real `evaluate()` call, not assumed from prompt text

### 3.1 Tasks 111 and 140 — `IntersectAll`/`UnionAll`, live-verified end-to-end

**Task 111** ("find the common elements in given nested lists",
`common_in_nested_lists`) and **task 140** ("flatten the list of lists into
a single set of numbers", `extract_singly`) both take ONE list-of-lists (or
list-of-tuples) argument and reduce it via `Intersect`/`Union` across an
UNKNOWN number of sublists (2-5 across the three fixture rows each) — this
is a **fold over an already-shipped binary Set op**, not a new primitive.
`runners/dsl/src/term.rs` already ships `TermNode::Fold { source, var_name,
acc_name, init, body }` (a fully general accumulate-over-sequence Term,
already used internally to build `ConcatList`/`JoinList`'s own Fold-based
op-table exposures — `runners/dsl/src/synth_enumerate.rs:649-654`), and
already ships `TermNode::Intersect { a, b }` / `TermNode::Union { a, b }`
(the SetLit/DictItems rung's own zero-new-`TermNode` op-table exposures).

**Live-verified directly**, via `substrate_rs.Substrate()._inner.evaluate()`
(the same "invocation, not inference" discipline every prior rung in this
arc uses), hand-constructing the exact term-JSON tree
`Fold(source=Var(a), init=IndexAt(Var(a),0), body=Intersect(Var(acc),
Var(item)))` for task 111 and the `Union`-bodied twin for task 140, against
ALL THREE real fixture rows (both revealed AND the held-out row) for each
task:

```
task 111 (IntersectAll):
  a=[[12,18,23,25,45],[7,12,18,24,28],[1,5,8,12,15,16,18]] -> {12,18}   == expected  (revealed)
  a=[[12,5,23,25,45],[7,11,5,23,28],[1,5,8,18,23,16]]      -> {5,23}    == expected  (revealed)
  a=[[2,3,4,1],[4,5],[6,4,8],[4,5],[6,8,4]]                -> {4}      == expected  (HELD-OUT)

task 140 (UnionAll):
  a=[(3,4,5),(4,5,7),(1,4)]        -> {1,3,4,5,7}       == expected  (revealed)
  a=[(1,2,3),(4,2,3),(7,8)]        -> {1,2,3,4,7,8}     == expected  (revealed)
  a=[(7,8,9),(10,11,12),(10,11)]   -> {7,8,9,10,11,12}  == expected  (HELD-OUT)
```

**6/6 exact matches, including both held-out rows** — the strongest live
verification standard this arc uses (CEILING_REASSESSMENT_3's own task 64
witness checked revealed + held-out too; this checks the SAME depth for
TWO independent tasks). The reduction `init = IndexAt(source, 0)` (the
first sublist) followed by folding `Intersect`/`Union` across the WHOLE
source (including index 0 again) is correct and safe because both ops are
idempotent under self-application (`Intersect(A,A) = A`, `Union(A,A) = A`)
— confirmed not just by the passing evaluation above but by construction.

Independently confirmed both tasks' fixture-parsed `expected` values are
genuinely `frozenset` (Python) / `Value::Set` (Rust) — i.e. both already
satisfy `spec_output_is_setlike` (`runners/dsl/src/synth_enumerate.rs:2005-2006`),
the exact flag that routes a spec into `SET_DEFAULT_OPS`
(`runners/dsl/src/synth_enumerate.rs:2122-2136`), the same narrow,
already-measured-safe bucket `SetMap`/`Intersect`/`Union`/`Sort`/`Reverse`/
`Slice` already live in. **The gap is therefore purely that `SET_DEFAULT_
OPS` doesn't yet offer a FOLDED reduction of `Intersect`/`Union` across a
variable-length outer sequence** — the 2-ARG `Intersect{a,b}`/`Union{a,b}`
already offered there cannot help these two tasks because neither has TWO
list-shaped variables to bind `a`/`b` to; each has exactly ONE variable
whose OWN elements are the things to reduce.

### 3.2 The exact mechanical fix, matching the `ConcatList` precedent

`runners/dsl/src/synth_enumerate.rs` already has the identical PATTERN for
exactly this shape: `"ConcatList"` (list-BINARY: `Fold{source:b, init:a,
body:Append(acc,item)}`, `build_list_binary`, line ~649) and `"JoinList"`
(list-UNARY: `Fold{source, init:Lit(""), body:StringConcat([acc,item])}`,
`build_list_unary`, line ~613). `IntersectAll`/`UnionAll` are the list-UNARY
class (ONE source argument, like `JoinList`/`ProdList`/`ArgMaxLenOver`), so
they belong in `build_list_unary` (`OpKind::ListUnary`) exactly like those
three — **zero new `TermNode` variant, zero new arity, zero new
registration machinery** (`OpKind::ListUnary` already exists and is already
wired end-to-end: `OP_TABLE` entry → `build_list_unary` match arm →
`list_unary_extra_cost` entry → the `search.list_by_size`-sourced growth
loop at `synth_enumerate.rs:2972-2984`).

Exact touch points (read directly, line numbers current as of this
document):

1. **`OP_TABLE`** (`synth_enumerate.rs:~337`, immediately after
   `ArgMaxLenOver`): add `("IntersectAll", OpKind::ListUnary)`,
   `("UnionAll", OpKind::ListUnary)`.
2. **`build_list_unary`** (`synth_enumerate.rs:~629`, immediately after the
   `ArgMaxLenOver` arm, before the `_ => call_fallback(...)` default): two
   new match arms, each building `Fold{source, var_name:item, acc_name:acc,
   init: IndexAt{seq:source, index:Lit(0)}, body: Intersect{a:Var(acc),
   b:Var(item)}}` (swap `Intersect`→`Union` for the second).
3. **`list_unary_extra_cost`** (`synth_enumerate.rs:~748`, same block): two
   new entries, `"IntersectAll" => 5` and `"UnionAll" => 5` — counted
   precisely against the honest MDL/Occam accounting this function's own
   doc comment requires: the RETURNED node (`Fold`) is covered by the
   caller's own `+1`, so `extra` counts every node BENEATH it that is not
   `source` itself — `Lit(0)` (1) + `IndexAt` (1) + `Var(acc)` (1) +
   `Var(item)` (1) + `Intersect`/`Union` (1) = **5**. (Cross-checked against
   the existing `"JoinList" => 4` entry's own worked comment
   — `Lit("")`(1) + `Var(acc)`(1) + `Var(item)`(1) + `StringConcat`(1) = 4,
   same accounting style, one fewer node because `JoinList`'s `init` is a
   bare `Lit` with no `IndexAt` wrapper.)
4. **`SET_DEFAULT_OPS`** (`synth_enumerate.rs:~455`): append `"IntersectAll"`,
   `"UnionAll"` to the existing array — the bucket already unconditionally
   includes `Intersect`/`Union`/`SetMap`/`Sort`/`Reverse`/`Slice` for ANY
   `spec_output_is_setlike` spec, so this is a same-class, same-bucket
   widening, not a new gate.

No `jsonio.rs`/`reflect.rs`/`term_variants.rs` touch is needed — unlike
every Tier-1/`Sort`/`DictItems`/`GroupCount`/`DictMerge` rung, this fix
introduces **no new `TermNode` enum variant at all**; `Fold`/`Intersect`/
`Union`/`IndexAt`/`Var`/`Lit` are all pre-existing, fully-wired Terms. This
is the SAME "zero-new-variant, pure op-table exposure" class as `SetMap`/
`Intersect`/`Union` themselves were in the SetLit/DictItems rung — cheaper
than every subsequent rung in this arc's own record, which all added at
least one new `TermNode` variant.

### 3.3 Whole-population coverage check, per the SortBy lesson (never scope
   to the two witness tasks alone)

Grepped all 188 currently-failing prompts for
`common|intersect|union|flatten|single set|single list|merge`, individually
triaged against real recorded `construction`/`gap_reason`/outcome data (not
assumed from prompt text):

| task | prompt (truncated) | outcome | verdict |
|---|---|---|---|
| 65 | flatten a list and sum all elements | `accepted_holdout_fail` | in the retrieval-fallthrough NO-GO population (§3.5); `IntersectAll`/`UnionAll` cannot touch it — `SynthEnumerate` is never invoked (`enumerate.tested is None`) |
| **97** | frequency of each element in a **flattened** list of lists | `gapped:enumerate_failed` (saturated, 119001 tested) | needs `GroupCount` (already shipped) PLUS a genuine arbitrary-position FLATTEN-TO-LIST primitive (not fold-to-Set — output is a Dict of counts over the flattened elements, order-independent for counting, but the flatten step itself needs list semantics) — **checked and NOT solved by `IntersectAll`/`UnionAll`** (neither is a flatten-to-list op); named, not built, same as REASSESSMENT_3's own finding |
| 108 | merge three lists into a single sorted list | `gapped:enumerate_failed` (budget-exhausted) | already NO-GO'd (`DELIMJOIN_BUDGETWALL_RESULTS.md`), unaffected |
| **111** | common elements in nested lists | `gapped:enumerate_failed` (saturated) | **THIS RUNG'S TARGET — `IntersectAll`, live-verified §3.1** |
| 126 | sum of common divisors of two given numbers | `gapped:enumerate_failed` (budget-exhausted, not in the 14-saturated set) | a FIXED 2-argument case needing a `Divisors` primitive first (doesn't exist) — a different, unpriced gap; `IntersectAll`/`UnionAll` (which reduce over a variable-length OUTER sequence) don't apply to a 2-scalar-argument spec at all |
| **140** | flatten list of lists into a single SET | `gapped:enumerate_failed` (saturated) | **THIS RUNG'S TARGET — `UnionAll`, live-verified §3.1** |
| 297 | flatten a given nested list **structure** | `gapped:enumerate_failed` (budget-exhausted) | **checked and REJECTED as a witness** — live-tested a hand-built `FlattenList` (nested `Fold`+`Append`) against all 3 rows; row 1 FAILED (`[0, 10, [20,30], ...]` mixes bare scalars and sublists at the SAME level — a non-uniform depth `IntersectAll`/`UnionAll`'s own uniform-fold shape cannot handle safely; a per-item type-branch would be needed, genuinely harder, not attempted) |
| 417 | common FIRST ELEMENT in given list of tuple | `gapped:enumerate_failed` (saturated) | a group-by-first-element-and-consolidate task, structurally unrelated to set reduction (output is `[('x','y','z'),('w','t')]` — grouped tuples, not a set) — different, unpriced gap |
| 431 | two lists share at least one element | `accepted_holdout_fail` | in the retrieval-fallthrough NO-GO population; `Exists`/`Intersect` (2-arg, already shipped) plausibly solves this if construction ever reached `SynthEnumerate`, but it doesn't (`construction: retrieved_exemplar`) — the retrieved-exemplar-fallthrough gap named and NOT built by `RETRIEVAL_FALLTHROUGH_RESULTS.md`, not re-opened here |

**Only 111 and 140 are genuinely `IntersectAll`/`UnionAll`-shaped and
reachable by this fix.** 297 was actively tested and correctly excluded —
the coverage check paid for itself by catching a plausible-looking but
actually-wrong extension before it was built into the Rust source.

### 3.4 The other 7 newly-examined saturated tasks (117, 299, 305, 412, 417,
   462, 470) — checked, none is cheaper than 111/140

| task | prompt | finding |
|---|---|---|
| 117 | convert convertible elements of a list of lists to floats | needs per-element try/except-shaped type coercion across a nested structure — no existing Term composes this; genuinely harder, not priced here |
| 299 | maximum aggregate from a list of tuples | needs a groupby-and-sum-then-argmax composition (`GroupCount`-adjacent but not `GroupCount` itself — aggregates a VALUE, not a count); different, unpriced primitive |
| 305 | return two words from a list starting with letter 'p' | `FilterList` (shipped) + a `Take(2)`-shaped slice exists via `Slice`/`IndexAt`, but the exact composition wasn't live-witnessed and is a DIFFERENT, smaller-population candidate (1 task) — not pursued this rung, named only |
| 412 | remove odd numbers from a list | LOOKS trivial (`FilterList(a, item, Eq(Mod(item,2),0))`, both ops shipped) but is `gapped:enumerate_failed` at 140575 tested under budget, not solved — the miss is NOT primitive-availability (both `FilterList` and modulo arithmetic are already offered under `DEFAULT_OPS ∪ LIST_EXTRA_OPS`); this is a search/pruning-cost question (why doesn't the existing composition get found within budget), a different class of gap than "missing primitive" and out of scope for a primitive-layer rung |
| 417 | common first element in tuples | see §3.3 — different shape (group-by), not set-reduction |
| 462 | all possible combinations of elements | re-confirmed still exactly the standing `Combinations` single-task NO-GO (`CEILING_REASSESSMENT_3_PREREG.md §3.3`) |
| 470 | pairwise addition of neighbouring elements | needs a sliding-window/adjacent-pair primitive (`zip(a, a[1:])`-shaped) — doesn't exist; a plausible FUTURE candidate (unpriced, single task known) |

None of these seven is cheaper, safer, or better-evidenced than the
`IntersectAll`/`UnionAll` fix — each needs either a genuinely new primitive
with only 1 witness task (below this arc's own "needs ≥2 recurring witnesses
to be worth a standalone rung" bar, matching `DERIVED_OPERATOR_TIER_
RESULTS.md`'s own support-≥2 discipline) or is a search-cost question, not a
primitive-availability question (412).

### 3.5 Retrieval-fallthrough (87 tasks) and budget-wall — re-confirmed
   still NO-GO, not re-litigated

`PROGRAM_SYNTHESIS_RETRIEVAL_FALLTHROUGH_RESULTS.md`'s decisive NO-GO
(93.3% false-accept rate on the exact 60-task retrieved-exemplar population,
measured live, a worse failure mode than the gate it would replace) is
unchanged — nothing in this document's own population re-measurement
contradicts it, and no new evidence was sought (out of this rung's scope,
matching the task brief's own instruction to build on, not re-litigate,
settled NO-GOs). `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md`'s
budget-wall NO-GO (task 108 and siblings) is likewise unchanged.

### 3.6 `DictFromPairs` — a second, real, NOT-this-rung candidate, priced
   partially

Tasks **277** (filter a dict by value threshold) and **465** (drop empty/
`None`-valued items from a dict) are both `gapped:enumerate_failed`,
SATURATED under a strikingly SMALL search (`tested: 566` and `377`
respectively — the smallest of any saturated task, meaning the current
`DICT_DEFAULT_OPS = ["Eq", "IfThenElse", "GroupCount", "DictMerge"]` bucket
is exhausted almost immediately). Both are genuinely Dict-shaped in every
variable and output (`spec_output_is_dictlike`, no list-shaped variable —
confirmed directly, same routing check as GroupCount/DictMerge's own task
87), so they never reach `LIST_EXTRA_OPS`/`SET_DEFAULT_OPS` at all.

The natural composition — `DictItems(a)` (shipped) → `FilterList(...)`
(shipped) → **rebuild a Dict from the filtered list of (k,v) pairs** — is
missing exactly one piece: **no existing Term constructs a `Value::Dict`
from a DYNAMIC list of pairs.** `TermNode::MkDict { items: Vec<TermIdx> }`
is FIXED-arity (an alternating key,value literal list, built for a known
number of keys at construction time) and cannot express "however many pairs
survive the filter." **This needs one genuinely new `TermNode`**
(`DictFromPairs { seq: TermIdx }`, the direct structural inverse of the
already-shipped `DictItems`), unlike `IntersectAll`/`UnionAll`.

**Partially live-verified, not fully**: the `DictItems`→`FilterList` half is
already-shipped, already-tested machinery (no new evaluation risk); the
final "build a Dict from an arbitrary-length pair list" half cannot be
live-tested via `evaluate()` without first writing the Rust Term (unlike
§3.1's fix, which composes entirely from Terms that already exist). Given
the CLAUDE.md SHAPES-NOT-NUMBERS framing — prefer the primitive that is
`sd`-loop-shaped composition over already-shipped capability before minting
anything new — `IntersectAll`/`UnionAll` is strictly the cheaper, safer,
more-fully-verified choice for THIS rung; `DictFromPairs` is named here as
the next-priced candidate (2 witness tasks, 1 new `TermNode`, same cost
class as `GroupCount`/`DictMerge`'s own precedent) for a FUTURE rung, not
built now — matching this arc's own repeated discipline of keeping one
rung single-variable (`CEILING_REASSESSMENT_3_PREREG.md §4`'s explicit
reasoning for deferring `GroupCount`/`DictMerge` itself, one rung earlier).

## 4. Regression risk, priced before building

Currently-passing tasks whose parsed `expected` output is genuinely
Set/FrozenSet-shaped on every row (the exact `spec_output_is_setlike`
condition that routes into `SET_DEFAULT_OPS`, the bucket being widened) —
computed directly against the current pass-id set, not assumed:

```
setlike-output currently-passing canaries: [232, 473]
```

Both will be checked directly post-build (exact task-id set diff), not
assumed safe. `IntersectAll`/`UnionAll` are `OpKind::ListUnary` — the
CHEAPEST registration class this search loop has (`O(|list_by_size[size]|)`
per size, the same cost class as `Sort`/`Reverse`/`DictItems`/`GroupCount`,
never the `O(n²)` pairing cost `OpKind::ListBinary` ops like `Intersect`/
`Union`/`DictMerge` themselves carry) — two ADDITIONAL `ListUnary` entries
in an already-narrow 8-op bucket is a small, bounded, easily-measured
addition, not a combinatorial one. Task 132 (this arc's standing canary)
has a string-shaped output, never reaches `SET_DEFAULT_OPS`, and is
expected unaffected — checked anyway per house discipline.

## 5. The plan

**Build `IntersectAll`/`UnionAll`** exactly as specified in §3.2: 4 small,
mechanical edits to `runners/dsl/src/synth_enumerate.rs`, zero new
`TermNode` variants, zero touch to `jsonio.rs`/`reflect.rs`/
`term_variants.rs`. Rebuild from source, run the full paired MBPP battery
(exact task-id set diff against the 69/68/98 baseline established in §1),
run the Rust suite (774/774 expected — this fix touches no Term evaluator,
only op-table/search-loop registration code, so no NEW Rust test is
strictly required, but the existing suite must stay green), run the named
9-file Python regression suite (3 pre-existing failures expected, nothing
new), then write the RESULTS document.

**What this rung does NOT attempt:** `DictFromPairs` (§3.6, priced,
next-cheapest, deliberately deferred to keep this rung single-variable);
task 300's outcome-classification drift (§2.1, named, not chased, matches
this arc's own standing precedent for this exact mechanism); tasks 97/108/
117/126/297/299/305/412/417/462/470 (§3.3-3.4, each individually checked and
found either genuinely harder, under-witnessed, or already NO-GO'd); the
retrieved-exemplar-fallthrough population (§3.5, re-confirmed still NO-GO,
not re-opened).

## What this document does NOT establish

1. §3.1's `IntersectAll`/`UnionAll` witnesses are verified via direct
   `evaluate()` calls on hand-built term-JSON, exactly mirroring the
   engine's own evaluation semantics — but whether the AUTOMATIC typed
   default (after the op-table widening lands) reaches the same witness
   within the real `max_candidates:200,000` budget, via the REAL search
   loop (not a hand-built term), is a build-time question, checked in the
   RESULTS document, not assumed here — this arc's own standing "reach is
   not conversion" discount.
2. Whether the 2 setlike-output canary tasks (232, 473) regress is
   unmeasured until the build lands — priced as a real, small risk above,
   not dismissed.
3. §3.6's `DictFromPairs` sizing is partial — the `DictItems`/`FilterList`
   half is live-verified (already-shipped Terms), the dict-reconstruction
   half is NOT, because it requires writing the new Term first. A future
   rung must verify it live before building, not cite this document's
   partial confidence as sufficient.
4. This document does not re-litigate the retrieval-fallthrough or
   budget-wall NO-GOs — both are re-confirmed at the depth the task brief
   asked for (check for new evidence, find none) and no further.
5. Task 412's search-cost puzzle (§3.4) is named but not diagnosed to its
   exact mechanism — it may indicate a real, separate, worthwhile
   investigation (why does an in-op-table, seemingly-simple composition not
   get found within 140k+ candidates?) but that diagnosis is out of this
   primitive-layer rung's scope.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-4
git log --oneline -1   # 83b1f24, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

Live witness re-check (hand-built term JSON, no code change needed to
reproduce):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
term = {'type':'Fold','source':{'type':'Var','name':'a'},'var_name':'item','acc_name':'acc',
        'init':{'type':'IndexAt','seq':{'type':'Var','name':'a'},'index':{'type':'Lit','value':0}},
        'body':{'type':'Intersect','a':{'type':'Var','name':'acc'},'b':{'type':'Var','name':'item'}}}
print(s._inner.evaluate(term, {'a': [[2,3,4,1],[4,5],[6,4,8],[4,5],[6,8,4]]}))  # expect frozenset({4})
"
```
