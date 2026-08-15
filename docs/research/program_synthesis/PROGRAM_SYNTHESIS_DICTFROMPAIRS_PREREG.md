# `DictFromPairs` — re-priced from scratch, zero new `TermNode` found — PREREG

**Date:** 2026-08-16. Base `main @ 27db12b` ("Merge progsyn-ceiling-reassessment-4:
IntersectAll/UnionAll op-table exposure, MBPP 69->71"), verified fresh via
`git log --oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-dictfrompairs`, branch
`progsyn-dictfrompairs`.

**Headline finding, stated up front: the immediately-prior rung's own claim —
"`DictFromPairs` ... needs one genuinely new `TermNode`" — is WRONG, and the
task brief's own instruction to re-check this before assuming a new Term is
required paid off. The exact composition
`Fold{source, init:MkDict([]), body:DictMerge(acc, MkDict([IndexAt(item,0),
IndexAt(item,1)]))}` builds a `Value::Dict` from an arbitrary-length runtime
list of pairs using SIX already-shipped Terms (`Fold`/`MkDict`/`DictMerge`/
`IndexAt`/`Var`/`Lit`) — zero new Rust. Live-verified end-to-end against BOTH
target tasks (277 `dict_filter`, 465 `drop_empty`), all three real fixture
rows each (including the held-out row), via `substrate_rs.Substrate()._inner.
evaluate()` on hand-built term-JSON: 6/6 exact matches. This is the SAME
"zero-new-`TermNode`, pure op-table exposure" class `IntersectAll`/`UnionAll`
used one rung earlier — cheaper than the `GroupCount`/`DictMerge` precedent
this document's predecessor priced it against.**

**A second, genuine, honestly-priced residual: the search's OWN
`filter_templates_by_size` predicate-template grammar (`synth_enumerate.rs`
~2603-2770) has no "project a fixed index out of the bound item, then compare"
template shape — both target predicates (`item[1] >= n`, `item[1] is not
None`) need exactly this shape and it does not exist in the pool today. This
means RAW `SynthEnumerate` almost certainly cannot construct the needed
`FilterList` predicate even after `DictFromPairs`/`DictItems`/`FilterList` are
all nominally available — the SAME "op exists, search still doesn't reach it"
gap this arc's own `retrieved_exemplar` mechanism has repeatedly closed for
`IntersectAll`/`UnionAll` (task 111/140) and `GroupCount` (task 88) instead.
Widening the filter-template grammar itself is a SEPARATE, unpriced,
genuinely-new primitive-layer decision and is explicitly OUT OF SCOPE for
this rung (single-variable discipline, matching every prior rung's own
scoping rule) — named here, not built.**

Investigation-only up to §5; §6 builds the fix under full house discipline if
this document's own plan survives that build.

---

## 1. What tasks 277 and 465 actually need — read from the real fixture, not
   the prompt text

Both live in `tests/fixtures/mbpp/sanitized-mbpp.json`, confirmed by direct
read (no `text` field on either row — `text: None` — so `code` + `test_list`
are the only source of truth, exactly matching this arc's standing
`ms.parse_asserts` discipline of never reading `task["code"]` either; the
`test_list` asserts alone are what `parse_asserts` turns into rows):

```
task 277 (dict_filter):  def dict_filter(dict, n):
    return {k: v for k, v in dict.items() if v >= n}
  3 asserts, all Dict[str,int] -> Dict[str,int], threshold n varies per row.

task 465 (drop_empty):  def drop_empty(dict1):
    return {k: v for k, v in dict1.items() if v is not None}
  3 asserts, all Dict[str,str|None] -> Dict[str,str].
```

`primary` protocol (the `full` arm) reveals rows 0-1 and holds out row 2 (the
last parseable row) — confirmed directly from `domains/mbpp_spec.py`'s own
`split_rows` docstring. Every live check below (§3) covers all three rows,
including the held-out one, for both tasks — the same depth
`CEILING_REASSESSMENT_4_PREREG.md` §3.1 used for its own two witnesses.

Both are, in every variable and the output, genuinely Dict-shaped with **no
list/tuple/set-shaped value anywhere on any row** — confirmed directly (§2)
by parsing every revealed+held-out row of every currently-passing AND
currently-failing runnable task and checking value types, not assumed from
the prompt.

## 2. Whole-population coverage check, per the `SortBy` lesson (never scope
   to the two witness tasks alone)

The exact routing gate that sends a spec to the `DICT_DEFAULT_OPS` bucket
(`synth_enumerate.rs:2299`, `else if spec_output_is_dictlike` — reached only
when `spec_is_list_shaped` is FALSE, i.e. no variable or the output is
List/Tuple/Set/FrozenSet-shaped on any row) was reproduced directly in
Python against the real fixture data (not re-derived from memory of the Rust
flag names):

```python
# a task routes to DICT_DEFAULT_OPS iff every row's every input value AND
# the expected output are dict-or-scalar, with no list/tuple/set anywhere
```

Run against **every** row of **every** currently-passing (`full`-arm pass-id
set, freshly re-measured, §1 of the fresh baseline below) task:

```
dict-output, no listlike anywhere (routes to DICT_DEFAULT_OPS), passing: [87]
```

— exactly the task `GROUPCOUNT_DICTMERGE_RESULTS.md` §3 already names as the
ONLY currently-passing occupant of this bucket (task 88 is confirmed
list-shaped — its `a` argument is a Python list literal — and routes to the
LIST-shaped branch instead, never `DICT_DEFAULT_OPS`; reproduced directly
here, not assumed from that document).

Run against every currently-**failing** runnable `test`-split task:

```
currently-failing, dict-only-shaped (would route to DICT_DEFAULT_OPS): [277, 465]
```

**Exactly the two named target tasks — no hidden third witness** (the
`SortBy` lesson: task 64 materialised as a SEPARATE later witness after
`SortBy` first shipped scoped to task 475 alone; this rung's own population
check finds no analogous hidden case for `DictFromPairs`). Regression risk is
therefore priced narrowly and exactly: **one** currently-passing canary (87)
shares the bucket being widened.

## 3. Is `DictFromPairs` genuinely a new Term, or does an existing
   composition already reach it? — RE-CHECKED, and the answer changed

The immediately-prior rung (`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_4_
PREREG.md` §3.6) concluded: *"`TermNode::MkDict{items: Vec<TermIdx>}` is
FIXED-arity ... and cannot express 'however many pairs survive the filter.'
This needs one genuinely new `TermNode`."* That document explicitly flagged
its own §3.6 pricing as partial (`What this document does NOT establish`,
item 3: *"the dict-reconstruction half is NOT [live-verified], because it
requires writing the new Term first"*) — i.e. it never actually tried to
compose the reconstruction from existing Terms; it inferred the need for a
new Term from `MkDict`'s fixed arity alone.

**Read directly against `runners/dsl/src/term.rs`, the fixed-arity claim
about `MkDict` is correct, but it does not follow that no existing
composition reaches the goal.** `MkDict{items: Vec<TermIdx>}`'s `items` are
build-time `TermIdx` references (fixed when the search constructs the
candidate), so `MkDict` alone cannot build a dict whose PAIR COUNT is only
known at evaluate time. But `TermNode::Fold{source, var_name, acc_name, init,
body}` (already shipped, already used exactly this way by `IntersectAll`/
`UnionAll` one rung earlier) accumulates over a RUNTIME-LENGTH sequence — and
its accumulator can itself be a `Value::Dict`, built one pair at a time via
`MkDict` (single-pair) merged into the running accumulator via `TermNode::
DictMerge{a, b}` (already shipped, GroupCount/DictMerge rung — `b` wins on
key collision, i.e. later-pair-wins, EXACTLY Python's `dict(pairs)`
semantics for duplicate keys). Composing:

```
DictFromPairs(seq) ==
  Fold{
    source: seq, var_name: item, acc_name: acc,
    init: MkDict{items: []},                              // {}
    body: DictMerge{
      a: Var(acc),
      b: MkDict{items: [IndexAt(Var(item),0), IndexAt(Var(item),1)]},
    },
  }
```

reads: start from the empty dict, and for each pair fold in a
single-entry dict built from that pair's two elements, with the new entry
always winning a collision — Python's `dict()` constructor, exactly.

**Live-verified directly** (`substrate_rs.Substrate()._inner.evaluate()`,
the same "invocation, not inference" discipline every prior rung in this arc
uses), hand-constructing the exact term-JSON tree above wrapped in the full
task pipeline (`DictItems(dict)` -> `FilterList(pairs, item, predicate)` ->
`DictFromPairs(filtered)`), against ALL THREE real fixture rows (both
revealed AND the held-out row) for each task:

```
task 277 (dict_filter):
  dict={...4 entries...}, n=170 -> {'Cierra Vega':175,'Alden Cantrell':180,'Pierre Cox':190}  == expected  (revealed)
  dict={...same...},      n=180 -> {'Alden Cantrell':180,'Pierre Cox':190}                     == expected  (revealed)
  dict={...same...},      n=190 -> {'Pierre Cox':190}                                          == expected  (HELD-OUT)

task 465 (drop_empty):
  {'c1':'Red','c2':'Green','c3':None} -> {'c1':'Red','c2':'Green'}  == expected  (revealed)
  {'c1':'Red','c2':None,'c3':None}    -> {'c1':'Red'}               == expected  (revealed)
  {'c1':None,'c2':'Green','c3':None}  -> {'c2':'Green'}             == expected  (HELD-OUT)
```

**6/6 exact matches, including both held-out rows** — the same depth
`CEILING_REASSESSMENT_4_PREREG.md` §3.1 used for `IntersectAll`/`UnionAll`.
Reproduce script: `scratch_dictfrompairs_live.py` in this worktree (not
committed — a throwaway verification harness, kept only for the reproduce
section below; deleted before commit per house discipline against stray
files).

**This changes the pricing class entirely: `DictFromPairs` does NOT need a
new `TermNode`. It is a `Fold`-based op-table exposure, the exact
`IntersectAll`/`UnionAll` shape — cheaper than the "1 new `TermNode`, same
cost class as `GroupCount`/`DictMerge`" estimate the immediately-prior
document gave it.**

### 3.1 Why the prior document's inference was reasonable but incomplete

`CEILING_REASSESSMENT_4_PREREG.md` §3.6 reasoned from `MkDict`'s fixed arity
directly to "need a new Term" without checking whether a DIFFERENT existing
Term (`Fold`, accumulating a `Value::Dict` via repeated `DictMerge`) could
supply the missing "however many pairs" degree of freedom `MkDict` itself
lacks. This is exactly the "zero-new-Rust possibility" check the task brief
asked to re-run — and exactly the discipline `IntersectAll`/`UnionAll`
demonstrated one rung earlier for a structurally similar problem (`Intersect`/
`Union` are also fixed-arity-2 Terms; `Fold` supplied their missing
variable-length reduction). The lesson generalises: **a fixed-arity Term
constraint on ONE candidate Term does not mean the capability needs a new
Term — check whether `Fold` (or another already-shipped variable-length
primitive) can supply the missing arity first.**

## 4. Exact Rust touch points, priced before writing any code

Mirroring `IntersectAll`/`UnionAll`'s own four-edit shape
(`CEILING_REASSESSMENT_4_RESULTS.md` §1), all in
`runners/dsl/src/synth_enumerate.rs`:

1. **`OP_TABLE`** (currently ends its `IntersectAll`/`UnionAml` block at line
   347): add `("DictFromPairs", OpKind::ListUnary)`.
2. **`build_list_unary`** (`fn build_list_unary`, line 595, `_ =>
   call_fallback(...)` default at line 674): one new match arm building the
   Fold/MkDict/DictMerge composition from §3 above, entirely from
   `scratch.add(TermNode::...)` calls mirroring the existing idiom (each
   reference to `item`/`acc` gets its own fresh `Var` node, matching every
   existing arm's own style — e.g. `MaxLenOver`'s `iv`/`ArgMaxLenOver`'s
   `iv`, never a shared node reused across two different parent slots).
3. **`list_unary_extra_cost`** (`fn list_unary_extra_cost`, line 779):
   `"DictFromPairs" => 10` — counted against the SAME honest MDL/Occam
   accounting `IntersectAll`/`UnionAll`'s own `"IntersectAll" => 5` comment
   uses (the returned `Fold` node is covered by the caller's own `+1`;
   `source` itself is never counted, since it is shared, not duplicated):
   - `init: MkDict{items:[]}` = 1 (empty items list, no children)
   - `body: DictMerge{a: Var(acc), b: MkDict{items:[k,v]}}`:
     - `Var(acc)` = 1
     - `MkDict{items:[k,v]}` pair-builder = 1
       - `k = IndexAt{seq:Var(item), index:Lit(0)}` = `IndexAt`(1) +
         `Var(item)`(1) + `Lit(0)`(1) = 3
       - `v = IndexAt{seq:Var(item), index:Lit(1)}` = `IndexAt`(1) +
         `Var(item)`(1) + `Lit(1)`(1) = 3
     - `DictMerge` itself = 1
   - Total: 1 (init) + 1 (Var acc) + 1 (pair MkDict) + 3 (k) + 3 (v) + 1
     (DictMerge) = **10**
4. **`DICT_DEFAULT_OPS`** (`const DICT_DEFAULT_OPS`, line 480, currently
   `&["Eq", "IfThenElse", "GroupCount", "DictMerge"]`): append
   `"DictFromPairs"` — the same bucket-widening precedent
   `IntersectAll`/`UnionAll` used for `SET_DEFAULT_OPS`.

No `jsonio.rs`/`reflect.rs`/`term_variants.rs`/`py.rs` touch — zero new
`TermNode` enum variant, matching `IntersectAll`/`UnionAll`'s own record as
the cheapest touch-point class this arc has used.

**Deliberately NOT added to `DICT_DEFAULT_OPS` this rung: `DictItems`,
`FilterList`.** Both already exist and are already registered
(`OpKind::Unary` / `OpKind::ListFilter` respectively) — adding their NAMES to
this bucket would be mechanically cheap, but §5 below prices why it would not
help raw `SynthEnumerate` reach either target task, and would add real,
measured-elsewhere regression risk to the ONE currently-passing canary (87)
this bucket already serves (`RUNG1_RESULTS.md`'s own "even cheap
unconditional additions regress a budget-fragile spec" lesson, re-quoted by
`CEILING_REASSESSMENT_4_PREREG.md` §3.2 for exactly this reason). Per the
"only add ops with a live witness under this evidence" discipline
`GroupCount`/`DictMerge`'s own §3 explicitly uses (*"`DictMerge` deliberately
NOT added [to the list-shaped branch]: task 88 has no live witness needing it
under this evidence"*), and given §5's finding that the template grammar
itself blocks the raw-search path regardless, neither earns a place in this
bucket under CURRENT evidence.

## 5. The named, unpriced residual: raw `SynthEnumerate` almost certainly
   cannot reach either witness even after `DictFromPairs` exists

`FilterList`'s predicate comes from `filter_templates_by_size`
(`synth_enumerate.rs` ~2555-2770), built only when `filter_wanted` is true
(`op_list.iter().any(|(n,_)| n == "FilterList")`, confirmed directly at
`synth_enumerate.rs:2540`). Read directly, the pool's ENTIRE template
grammar, for a spec whose bound `item` is itself a `(key, value)` pair
(exactly what `DictItems(dict)` produces per element), offers:

- `item OP <const>` / `item OP <scalar var>` (size 3) — compares the WHOLE
  item, not a projected field
- `len(item) OP <const>` / `len(item) OP <scalar var>` (size 4)
- `item in <list var>` / `item not in <list var>` (size 3/4)
- a one-level nested reduction (`max/min/sum(<inner> for x in item) OP rhs`,
  the `tmpl:nested_reduction` widening) — treats `item` as an iterable to
  reduce OVER, not as a fixed-position tuple to index INTO

**None of these constructs `item[1] OP <const/var>`** — a comparison against
one FIXED-INDEX element of the pair, which is exactly what both target
predicates need (`item[1] >= n` for task 277, `item[1] is not None` for task
465). This is a genuine, structural gap in the template grammar, not a
budget or ordering problem — the shape is simply absent from the pool that
`filter_wanted` builds, confirmed by reading every template-construction
block in that function, not inferred from a failed search alone.

**Consequence, stated honestly:** even with `DictFromPairs` registered and
(hypothetically) `DictItems`/`FilterList` also added to `DICT_DEFAULT_OPS`,
raw `SynthEnumerate`'s own predicate grammar cannot build the correct filter
— so widening `DICT_DEFAULT_OPS` with those two additional names would add
search cost (risking the one live canary, task 87) for **no realistic
raw-search benefit** under the CURRENT template pool. This is exactly why §4
above deliberately excludes them.

**The plausible discovery path for BOTH target tasks, if either converts, is
`retrieved_exemplar`** — the SAME construction lane that solved `IntersectAll`/
`UnionAll` (task 111/140) and `GroupCount` (task 88) despite an identical
"op registered, raw search unlikely to reach it in budget" profile
(`CEILING_REASSESSMENT_4_RESULTS.md` §2, `GROUPCOUNT_DICTMERGE_RESULTS.md`
§4, both converting via `retrieved_exemplar`'s hole-filler, not a raw
top-level `SynthEnumerate` accept). That mechanism is not re-traced to its
exact internal code path here either, matching those two documents' own
standing residual — **this document does not claim to know WHY retrieval
would or would not find `DictFromPairs`'s composition; it names the
mechanism as the plausible path and defers to the actual measurement in §6.**
**Widening the filter-template grammar itself (adding an `item[k] OP rhs`
shape to `filter_templates_by_size`) is a genuinely new, unpriced,
primitive-layer addition and is explicitly OUT OF SCOPE for this rung** —
matching this arc's standing "keep one rung single-variable" discipline
(`CEILING_REASSESSMENT_3_PREREG.md §4`'s original statement of the rule,
reused by every subsequent rung including this document's own predecessor).

## 6. Regression risk, priced before building

Exactly **one** currently-passing task shares the bucket being widened
(`DICT_DEFAULT_OPS`): **task 87**, confirmed directly by set computation
(§2), not assumed. `DictFromPairs` is `OpKind::ListUnary` — the cheapest
registration class this search loop has (same cost class as `Sort`/
`DictItems`/`GroupCount`/`IntersectAll`/`UnionAll`, never the `O(n²)` pairing
cost `OpKind::ListBinary` carries) — one additional `ListUnary` entry in an
already-narrow 5-op (after this rung) bucket is a small, bounded addition.
Task 87's own solution (`DictMerge(DictMerge(c,b),a)`, no `Fold`/list
composition needed at all) is structurally unrelated to anything
`DictFromPairs` could plausibly interfere with — checked directly, not
assumed. Task 132 (this arc's standing canary, string-shaped output) never
reaches `DICT_DEFAULT_OPS` at all.

## 7. The plan

**Build `DictFromPairs`** exactly as specified in §4: 4 small, mechanical
edits to `runners/dsl/src/synth_enumerate.rs`, zero new `TermNode` variants,
zero touch to `jsonio.rs`/`reflect.rs`/`term_variants.rs`. Rebuild from
source, run the full paired MBPP battery (exact task-id set diff against the
71/70/100 baseline confirmed fresh in this worktree), check BOTH the real
pipeline (`synthesize_from_request`, the `retrieved_exemplar` lane per §5)
AND a forced-`ops` direct `SynthEnumerate` invocation (the `GroupCount`/
`DictMerge` rung's own diagnostic-depth precedent) for both target tasks, run
the Rust suite (778/778 expected), run the named 9-file Python regression
suite (3 pre-existing failures expected, nothing new), then write the
RESULTS document — reporting GO only if at least one real conversion is
measured, and an honest, well-localized NULL (per the task brief's own
explicit invitation to report one) if neither task converts through any real
pipeline path despite the op being genuinely, cheaply, correctly available.

**What this rung does NOT attempt:** widening `filter_templates_by_size`
with an `item[k] OP rhs` template shape (§5, named, explicitly out of scope,
single-variable discipline); adding `DictItems`/`FilterList` to
`DICT_DEFAULT_OPS` (§4, priced and rejected — no realistic raw-search benefit
under the current template grammar, real regression risk to task 87); any
other currently-failing task (§2's population check found none beyond the
two named targets).

## What this document does NOT establish

1. Whether `retrieved_exemplar` (or any other real pipeline construction
   lane) actually converts task 277 and/or 465 once `DictFromPairs` is
   registered — this is a build-time question, measured in the RESULTS
   document, not assumed here (the same "reach is not conversion" discount
   `CEILING_REASSESSMENT_4_PREREG.md` §"What this document does NOT
   establish" item 1 already names).
2. `retrieved_exemplar`'s exact internal mechanism is not traced here either
   — named as the plausible discovery path (§5) by pattern-matching against
   two prior rungs' own post-hoc findings, not independently verified against
   its source.
3. Whether widening `filter_templates_by_size` with an index-projection
   template shape would itself be cheap and safe is NOT priced here — named
   as a real, separate, future candidate only.
4. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-dictfrompairs
git log --oneline -1   # on top of main @ 27db12b
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

Live witness re-check (hand-built term JSON, no code change needed to
reproduce — composition entirely from already-shipped Terms):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
def mkdict_pair(item_ref):
    return {'type':'MkDict','items':[
        {'type':'IndexAt','seq':item_ref,'index':{'type':'Lit','value':0}},
        {'type':'IndexAt','seq':item_ref,'index':{'type':'Lit','value':1}}]}
item_ref={'type':'Var','name':'__item'}
term={'type':'Fold','source':{'type':'DictItems','seq':{'type':'Var','name':'dict1'}},
      'var_name':'__item','acc_name':'__acc',
      'init':{'type':'MkDict','items':[]},
      'body':{'type':'DictMerge','a':{'type':'Var','name':'__acc'},'b':mkdict_pair(item_ref)}}
print(s._inner.evaluate(term, {'dict1': {'c1':'Red','c2':'Green','c3':None}}))
# expect {'c1': 'Red', 'c2': 'Green', 'c3': None} -- unfiltered DictFromPairs(DictItems(x)) round-trips x
"
```
