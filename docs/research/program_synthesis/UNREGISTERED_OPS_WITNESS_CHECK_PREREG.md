# Seven unregistered `TermNode` ops — witness check — PREREG

**Date:** 2026-08-16. Base `main @ de1845d` ("Merge mdl-occam-witness-pricing:
witness-priced literals, the Occam-ordering metric fix -- +1 (task 451), zero
regressions"), verified fresh via `git log --oneline -1 main` before creating
the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/unregistered-ops-witness-check`, branch
`unregistered-ops-witness-check`.

---

**HEADLINE, stated up front: of the seven `TermNode` variants named by
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md` (`Pow`, `BitAnd`,
`BitOr`, `BitXor`, `Shl`, `Lshr`, `Ashr`) as shipped-but-unexposed, three
tasks in the CURRENT failing population yield genuine, hand-verified
witnesses for exactly TWO of the seven — `Shl` and `BitXor` — plus a THIRD
op, `BitAnd`, that is required only jointly with the other two for a single
task. `Pow`, `BitOr`, `Lshr`, `Ashr` have ZERO witnesses in the current
population — a real, honest null, not a gap in the search.** `BitXor` and
`BitAnd` already exist in `OP_TABLE`'s neighbourhood only via `ZipWith`'s own
fixed, self-contained `ZIP_ELEMENTWISE_OP_NAMES` pool
(`synth_enumerate.rs:939-940`, confirmed by direct read: `build_zip_
elementwise_op` never consults `OP_TABLE`/`table_kind` at all) — this document
re-confirms, by grep of `OP_TABLE` itself (`synth_enumerate.rs:359-489`, read
in full), that **none of `Pow`/`BitAnd`/`BitOr`/`BitXor`/`Shl`/`Lshr`/`Ashr`
has a general, freestanding `OP_TABLE` entry today** — the task brief's
own claim, reconfirmed against current source.

**The three witnesses, live-verified end-to-end (revealed AND held-out, 100%
agreement) via `substrate_rs.Substrate()._inner.evaluate()` against real
`tests/fixtures/mbpp/sanitized-mbpp.json` rows:**

- **Task 274** ("sum of even index binomial coefficients", `2^(n-1)`) —
  `Shl(1, Minus(a, 1))`. Single-op witness (`Shl` alone suffices), zero
  constant-starvation (`1` is in the default `{0,1,2,-1}` pool). **The
  cleanest of the three** — same shape-class as the `MODSQRT_SCOPED_FIX`
  arc's own `Sqrt` witnesses (no ungrounded literal needed beyond the
  default pool).
- **Task 119** ("element that appears only once in a sorted array", XOR
  self-cancellation) — a **list-fold reduction**, `Fold(a, init=0,
  body=BitXor(acc, item))`, not a bare-scalar composition. This is
  structurally the `IntersectAll`/`UnionAll`/`DictFromPairs` precedent
  (`OpKind::ListUnary`, zero new `TermNode`, a dedicated fold-shaped OP_TABLE
  entry) — proposed here as a new op, `XorList`.
- **Task 228** ("check whether all the bits are unset in the given range") —
  `Eq(BitAnd(n, BitXor(Minus(Shl(1,r),1), Minus(Shl(1,Minus(l,1)),1))), 0)`.
  **Needs `Shl`, `BitXor`, AND `BitAnd` TOGETHER** — a genuine joint,
  multi-op composition (`Shl` twice, `BitXor` once, `BitAnd` once), no single
  one of the three suffices alone for this task.

**Net witness accounting, stated honestly per-op:**

| op | witness tasks | count | shape |
|---|---|---|---|
| `Shl` | 274 (alone), 228 (jointly with BitXor/BitAnd) | **2** | bare-scalar `Binary`, scoped to the `else` branch exactly like `Mod`/`Sqrt` |
| `BitXor` | 228 (bare-scalar, jointly), 119 (list-fold, via a NEW `XorList` op) | **2**, but via TWO DIFFERENT registration shapes | bare-scalar `Binary` (228) + `ListUnary` fold (119, `XorList`) |
| `BitAnd` | 228 only, jointly with `Shl`+`BitXor` | **1** | bare-scalar `Binary`, no task converts on `BitAnd` alone |
| `Pow` | none | **0** | — |
| `BitOr` | none | **0** | — |
| `Lshr` | none | **0** | — |
| `Ashr` | none | **0** | — |

`Shl` and `BitXor` each clear this arc's own usual ≥2-witness bar (though
`BitXor`'s second witness is a structurally different registration, not a
second instance of the same shape). `BitAnd` is an honest single-witness
case — matching the task brief's own explicit instruction to price and build
it if warranted, not silently fold it into a "clears the bar" claim it does
not actually clear.

---

## 1. Re-derivation of the current failing population (not reused from a stale document)

Fresh full battery run in this worktree, before any code change:

```
full:              88/257  (byte-identical to the task brief's cited baseline)
content_stripped:  87/257
official:         114/257
det_identical=True on all three arms
```

Every `TermNode`/`OP_TABLE` fact below is re-confirmed against THIS
worktree's source (`runners/dsl/src/synth_enumerate.rs`,
`runners/dsl/src/term.rs`), not assumed from
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md`'s own (now 82-task,
possibly stale) enumeration.

### 1.1 `OP_TABLE` re-grepped directly, current source

`synth_enumerate.rs:359-489`, read in full:
`Mod`(`Binary`)/`Sqrt`(`Unary`) ARE present (installed by
`PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX`, already merged). `Pow`, `BitAnd`,
`BitOr`, `BitXor`, `Shl`, `Lshr`, `Ashr` are ABSENT from `OP_TABLE` — grepped
directly, zero matches for any of the seven as an `OP_TABLE` tuple. `BitAnd`/
`BitXor` DO appear at `synth_enumerate.rs:940,953-954`, but only inside
`ZIP_ELEMENTWISE_OP_NAMES`/`build_zip_elementwise_op` — a self-contained
function `ZipWith`'s own template-pool builder calls directly
(`synth_enumerate.rs:3510-3525`), which never consults `OP_TABLE` or
`table_kind` — confirmed by reading both call sites: `ZipWith` candidates are
built by iterating the fixed 7-name array and calling
`build_zip_elementwise_op` positionally, with no `OP_TABLE` lookup anywhere
in that path. **This means exposing `BitAnd`/`BitXor` in `OP_TABLE` as
general ops is additive and structurally independent of `ZipWith`'s own
internal use — the two mechanisms cannot interact.**

All seven Term variants confirmed present and evaluable in `term.rs`
(`Shl { a, b }` at `term.rs:878`; `BitAnd`/`BitXor`/`BitOr`/`Lshr`/`Ashr`/
`Pow` similarly present, grepped), and all seven already have full
`jsonio.rs`/`reflect.rs` serialize/parse/reflect support (grepped directly
for `Shl`: `jsonio.rs:273,1804`, `reflect.rs:553,1421` — all present) —
zero new Rust plumbing needed beyond `synth_enumerate.rs` itself, matching
the `Mod`/`Sqrt` precedent exactly.

### 1.2 Candidate search: which currently-failing tasks' real reference code needs one of the seven

A regex sweep over `tests/fixtures/mbpp/sanitized-mbpp.json`'s own `code`
field for `**`/`pow(`/`&`/`|`/`^`/`<<`/`>>` patterns, restricted to task ids
in the `test` split (257 tasks) AND currently failing on the `full` arm,
yields 12 candidates: `119, 163, 166, 167, 224, 228, 235, 274, 311, 388, 396,
447`. Each was read in full (prompt + reference `code`) and checked against
the real revealed/held-out rows (`domains.mbpp_spec.parse_asserts`/
`split_rows`) for whether the reference algorithm's SHAPE is reachable as a
fixed-depth term composition from already-shipped `TermNode`s (the same
"zero-new-`TermNode`, composition-only" scope this whole arc has held to
since `IntersectAll`/`UnionAll`):

| task | prompt shape | verdict |
|---|---|---|
| 119 | XOR-reduce a list to find the unique element | **WITNESS** — `Fold`+`BitXor`, i.e. a new `XorList` op |
| 163 | polygon area, needs `tan`/`pi` | not a witness — needs trig functions this engine has none of; `l**2` itself is `Times(l,l)`, no `Pow` needed |
| 166 | count pairs `(i,j)` with `A[i]^A[j]` even | not a witness — needs an all-pairs double-loop counting primitive that does not exist as any `TermNode`; a materially larger, unpriced gap (same class as the `Range`/iteration gap `BUDGET_EXHAUSTED_SURVEY` already named and declined to build) |
| 167 | smallest power of 2 ≥ n, iterative bit-shift loop | not a witness — the reference algorithm iterates an unbounded number of times (`while n != 0`); no fixed-depth term reproduces an unbounded loop |
| 224 | popcount, iterative | not a witness — same unbounded-loop reason as 167 |
| 228 | bit-range-unset check | **WITNESS** — `Shl`+`BitXor`+`BitAnd` jointly, fixed depth 7 |
| 235 | set even bits, iterative | not a witness — unbounded loop |
| 274 | `2^(n-1)`, single closed-form expression | **WITNESS** — `Shl` alone |
| 311 | leftmost unset bit, iterative | not a witness — unbounded loop |
| 388 | highest power of 2 ≤ n, iterative | not a witness — unbounded loop |
| 396 | string same-start/-end char (regex) | **false positive** — the `\^`/`$` matched are regex anchors inside a Python raw string, not bitwise XOR; unrelated to this survey entirely |
| 447 | cube each list element, `x**3` inside a `map` | not a witness — `x**3` is already expressible as `Times(Times(x,x),x)` via the existing `MapList`+`Times` composition; `Pow` is not NEEDED for this shape, whatever else may be blocking 447's conversion |

**Six of the seven unbounded-loop tasks (167, 224, 235, 311, 388, plus 166's
double-loop) share the SAME root cause**: the reference algorithm genuinely
iterates a variable, unbounded number of times over the bits of its input —
this is the identical `Range`/iteration primitive gap
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md` §5.4 already named,
priced as "a materially larger, unpriced, engine-architecture-level change,"
and explicitly declined to build. Exposing any of the seven bitwise ops as
a plain `OP_TABLE` binary/unary composition does **NOT** close this gap —
the missing primitive there is bounded iteration, not the bitwise operators
themselves. This document does not re-attempt that larger primitive.

### 1.3 Coverage check: is this candidate list exhaustive for the seven ops?

The regex sweep ran over ALL 427 fixture tasks' `code` fields (not
pre-filtered to failures), then intersected with (a) `test`-split membership
and (b) current `full`-arm non-pass — so the 12-task table above is the
complete set of currently-failing test-split tasks whose REFERENCE solution
textually contains any bitwise/power operator. No currently-failing task
outside this 12 needs any of the seven ops (a task whose reference code
never uses `**`/`pow`/`&`/`|`/`^`/`<<`/`>>` cannot need a `TermNode` built
from one, since the search space is Occam-ordered and MDL-priced — a
solution not resembling the reference shape at all would need to be a
different, unrelated coincidental formula, which is a separate risk class
this arc's own `structural_verdict_reject`/`property_verdict_reject`
machinery already guards against downstream, not a missing-primitive
question). This is the same exhaustiveness argument
`BUDGET_EXHAUSTED_SURVEY_PREREG.md` §5.4 used for its own candidate-cause
table.

**Zero witnesses found for `Pow`, `BitOr`, `Lshr`, `Ashr`** — an honest null,
stated as a headline finding, not a gap in this search. (`Pow` came closest —
task 274's `2^(n-1)` and task 447's `x**3` both textually use `**` — but in
both cases the SAME result is reachable without `Pow`: 274 via `Shl` on a
literal base of 1, 447 via nested `Times`. Neither is a genuine witness FOR
`Pow` specifically.)

## 2. The build plan

Following the `MODSQRT_SCOPED_FIX` precedent exactly:

1. **`Shl`** (`OpKind::Binary`) — add to `OP_TABLE`, add a `build_op` match
   arm (`TermNode::Shl { a: kids[0], b: kids[1] }`), scope its exposure to
   the bare-scalar `else` branch of `eval_synth_enumerate`'s typed-default
   construction ONLY (pushed onto the local `v`, never onto the shared
   `DEFAULT_OPS` constant — byte-identical scoping discipline to `Mod`/
   `Sqrt`, so every list-shaped spec including task 132 is untouched by
   construction). Add a `term_json` match arm (mandatory — that match is
   exhaustive and panics via `unreachable!()` on an unhandled variant); add
   a `term_str` arm too for readable candidate display (optional — that
   match has a `_ => "?"` fallback, unlike `term_json`).
2. **`BitXor`**, **`BitAnd`** (`OpKind::Binary`) — same bare-scalar-`else`-
   branch scoping as `Shl`. `term_json` arms for both ALREADY EXIST
   (`synth_enumerate.rs:1579-1584`, installed for `ZipWith`'s own candidate
   rendering) — zero new `term_json` work needed for these two.
3. **`XorList`** (`OpKind::ListUnary`) — add to `OP_TABLE`, add a
   `build_list_unary` match arm building `Fold{source, var_name, acc_name,
   init:Lit(0), body:BitXor(Var(acc),Var(item))}` (the exact `IntersectAll`/
   `UnionAll` `Fold`-composition precedent, zero new `TermNode`), add a
   `list_unary_extra_cost` entry (`4`: `Lit(0)` init + `BitXor`+`Var(acc)`+
   `Var(item)` body, mirroring `IntersectAll`'s own `5`-cost derivation).
   Gated in the list-shaped branch under `spec_output_is_bare_int` (the SAME
   variable `ParseInt`'s own gate already computes and uses,
   `synth_enumerate.rs` list-shaped branch) — **not** added unconditionally
   to `LIST_EXTRA_OPS`, because `RUNG1_RESULTS.md`'s own measured lesson
   (task 132 regressed from even two cheap unconditional `LIST_EXTRA_OPS`
   additions) is exactly the risk class an unconditional `XorList` would
   re-expose; a narrow output-type gate (task 119's own output IS a bare
   int, so this gate does not exclude it) keeps blast radius to the smallest
   evidence-backed slice, matching every gated addition this arc has made to
   this branch since Rung 1's own regression walk.

**What this build does NOT attempt**: `Pow`/`BitOr`/`Lshr`/`Ashr` (zero
witnesses, §1.3); the `Range`/bounded-iteration primitive needed for
167/224/235/311/388/166 (named, not sized here, matching
`BUDGET_EXHAUSTED_SURVEY_PREREG.md`'s own explicit deferral of the same
gap); task 447's own non-conversion (not a `Pow` issue by this document's
own finding, and not otherwise investigated here — out of scope, a
different mechanism).

## 3. Regression risk, priced before building

**Bare-scalar canaries** (currently-passing tasks whose spec routes through
the SAME bare-scalar `else` branch `Shl`/`BitXor`/`BitAnd` will be scoped
to) — computed the same way `BUDGET_EXHAUSTED_SURVEY_PREREG.md` §6 computed
its own 23-canary set, re-derived fresh against the CURRENT 88-task `full`
pass set in §5 of the RESULTS document (not assumed to be the stale 23-task
list from the prior rung, since the pass set has moved since then — this
document does not reuse a stale canary list as a substitute for a live
re-derivation).

This branch is now `DEFAULT_OPS ∪ {Mod, Sqrt}` (post-`MODSQRT_SCOPED_FIX`)
and this build proposes widening it FURTHER to `∪ {Shl, BitXor, BitAnd}` —
**five new ops beyond the original inventory, on the SAME branch the
`MODSQRT_SCOPED_FIX` arc already measured is sensitive to search-cost
inflation from just two additions** (tasks 14/164/455/464's own
mechanism-(a) residual, and the task-59/92 mechanism-(a) unmasking documented
in that arc's own RESULTS §3). Per that document's own precedent, this
document expects (not yet measured — the RESULTS document measures it):

- A repeat of mechanism (a) (search-cost inflation pushing an in-budget
  bare-scalar formula out of budget) is plausible, given `Shl`/`BitXor`/
  `BitAnd` are three MORE ops on top of `Mod`/`Sqrt`'s own two.
- A repeat of mechanism (b) (cross-lane reach via `prog_retrieval.py`'s
  rung (d) and `prog_moves.py`'s shared `_run_synth_enumerate`, both of
  which omit an explicit `ops` key and therefore reach the SAME widened
  bare-scalar typed default) is architecturally certain to be POSSIBLE
  (the same call sites, unchanged since that rung) — whether it actually
  fires for any specific currently-passing task is a live-trace question,
  answered in the RESULTS document exactly the way `MODSQRT_SCOPED_FIX`
  answered it (a proxy substituted for `sub._inner`, not assumed).

`XorList`'s isolation to the list-shaped branch, gated to
`spec_output_is_bare_int`, is expected to be LOW risk (a disjoint branch
from the bare-scalar one by construction, and gated narrowly enough that
only a spec sharing task 119's own output shape is even offered it) — but
this too is measured, not assumed, in the RESULTS document.

## 4. What this document does NOT yet establish

1. Whether `Shl`/`BitXor`/`BitAnd`, once exposed, are actually FOUND within
   the real 200,000-candidate budget for tasks 274/228 — task 228 in
   particular composes to DEPTH 7 with two ungrounded ops on top of the
   default constant pool (`r`, `l` are the spec's own variables, but the
   nested `Shl`/`Minus`/`BitXor`/`BitAnd` structure is a materially deeper
   tree than either `Sqrt` witness or `Mod`'s own witnesses were), so
   conversion is genuinely uncertain even after the ops are exposed — not
   assumed, measured honestly in the RESULTS document.
2. Whether either scoping edit causes ANY bare-scalar canary regression,
   and via which of the two mechanisms named in §3 — the RESULTS document's
   job, via the same live-trace-then-full-battery-diff method
   `MODSQRT_SCOPED_FIX` used, not by structural reasoning alone.
3. Whether `XorList`'s narrow gate is itself narrow enough to avoid a
   task-132-class regression — expected safe by construction (disjoint
   branch, output-type gate) but not yet measured.
4. Whether any further currently-failing task beyond the 12 named in §1.2
   is affected by either build — the RESULTS document's full 257-task
   battery diff is the authoritative check, not this document's own
   12-task table.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 5. GO/NO-GO criterion

**GO** iff the full paired battery, run after applying the build, converts
AT LEAST ONE of {119, 228, 274} to `pass` on `full`/`content_stripped` with
**zero regression** on the currently-passing 88-task set (after applying
whatever `exclude_ops` scoping the live cross-lane trace shows is needed,
matching `MODSQRT_SCOPED_FIX`'s own precedent). If a real, unavoidable
in-branch search-cost cost (mechanism (a), NOT scopeable via `exclude_ops`)
is measured, this document treats that honestly as a NAMED, not
disqualifying, limitation exactly as `MODSQRT_SCOPED_FIX_RESULTS.md` §7
did for its own official-arm residual — provided the `full`/`content_
stripped` arms show a clean, empty lost-set. If the joint `Shl`+`BitXor`+
`BitAnd` cost for task 228 alone (a single witness) turns out to carry a
disproportionate regression cost relative to its own single-task gain, this
document's own honest fallback is to keep `Shl` (2 witnesses) and `XorList`
(clean, isolated) while REVERTING the bare-scalar `BitXor`/`BitAnd`
exposure and reporting 228 as priced-but-declined, matching the `Mod`'s own
75/426 `FilterList`-quantifier precedent of splitting a correctly-diagnosed
but disproportionately-scoped follow-on out of the rung that found it.
**NO-GO** otherwise, with the exact task-id diff reported honestly.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/unregistered-ops-witness-check
git log --oneline -1 main   # de1845d, verify fresh
```

Witness hand-checks (no code change needed to reproduce):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
# task 274: Shl(1, a-1)
t274 = {'type':'Shl','a':{'type':'Lit','value':1},'b':{'type':'Minus','a':{'type':'Var','name':'a'},'b':{'type':'Lit','value':1}}}
for a, exp in [(4,8),(6,32),(2,2)]:
    print('274', a, s._inner.evaluate(t274, {'a': a}), 'expected', exp)

# task 228: ((1<<c)-1) ^ ((1<<(b-1))-1) ; n & that == 0
def mask(shift):
    return {'type':'Minus','a':{'type':'Shl','a':{'type':'Lit','value':1},'b':shift},'b':{'type':'Lit','value':1}}
num = {'type':'BitXor','a':mask({'type':'Var','name':'c'}),
       'b':mask({'type':'Minus','a':{'type':'Var','name':'b'},'b':{'type':'Lit','value':1}})}
t228 = {'type':'Eq','a':{'type':'BitAnd','a':{'type':'Var','name':'a'},'b':num},'b':{'type':'Lit','value':0}}
for a,b,c,exp in [(4,1,2,True),(17,2,4,True),(39,4,6,False)]:
    print('228', (a,b,c), s._inner.evaluate(t228, {'a':a,'b':b,'c':c}), 'expected', exp)

# task 119: Fold XOR-reduce
t119 = {'type':'Fold','source':{'type':'Var','name':'a'},'var_name':'item','acc_name':'acc',
        'init':{'type':'Lit','value':0},
        'body':{'type':'BitXor','a':{'type':'Var','name':'acc'},'b':{'type':'Var','name':'item'}}}
for a, exp in [([1,1,2,2,3],3), ([1,1,3,3,4,4,5,5,7,7,8],8), ([1,2,2,3,3,4,4],1)]:
    print('119', a, s._inner.evaluate(t119, {'a': a}), 'expected', exp)
"
```

Battery + regression suite: same invocation as `MODSQRT_SCOPED_FIX_RESULTS.md`
§ Reproduce (eight gitignored `results/*.json` fixtures already copied into
this worktree from the canonical tree).
