# ZIP_ELEMENTWISE — an 8-task missing-primitive cluster (`zip(a,b)` + a
per-pair binary combiner), design + build — PREREG

**Date:** 2026-08-16. Base `main @ dbe67c6` ("Merge progsyn-operator-shape-
witness-check: task 412's real blocker found, SynthesisOperatorShape
mechanism-disqualified"), verified fresh via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-zip-elementwise`, branch
`progsyn-zip-elementwise` — **not merged to `main`, not pushed**, left for
the orchestrator's independent re-verification.

**Process note, stated honestly rather than silently smoothed over:** the
house discipline for this arc is "write a PREREG doc BEFORE any code
change." The RESEARCH — re-reading the source citation
(`PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md` §7.3/§9 item 4,
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md` §5.4), re-reading all
8 tasks' real ground-truth `code` from `sanitized-mbpp.json`, reading
`term.rs`/`synth_enumerate.rs` for the exact touch points, and hand-
simulating all 8 tasks' term-trees in Python against revealed AND held-out
rows — was genuinely done first, before any `.rs` file was touched. The
literal FILE this document lives in, however, was written after the Rust
edits were already underway, not before the first edit. Recorded here
rather than silently reordered, per this arc's own standing "report
deviations honestly" norm.

---

## 1. Headline

**GO — a genuine 8-task witness cluster, zero-Mod, zero-primitive-overlap
with any prior rung, needing ONE new `TermNode` (`ZipWith`) the search could
not previously reach by any zero-new-Term composition (confirmed by reading
`term.rs` for a two-source lockstep iterator: none exists — `MapList`/
`IndexedMap` both iterate ONE source; `vec_binary`, the closest precedent,
already zips two operands but with a HARD-CODED f64 closure, never a Term
argument). All 8 tasks hand-verified correct against revealed AND held-out
rows via a Python simulation of the exact term-tree BEFORE any Rust code
was written (§4). Touch-point cost matches the `GroupCount`/`DictMerge`
template closely: 1 new `TermNode` variant, 8 files, ~230 lines net
(including doc comments) — see §7 for the exact diff.**

Re-verified fresh against the CURRENT baseline in this worktree
(`scripts/mbpp_endgame_battery.py`, unmodified source):

```
full:              76/257  p=0.29572   ci=[0.243264, 0.354192]  det_identical=True
content_stripped:  75/257  p=0.291829  ci=[0.239641, 0.350148]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

Byte-identical to the task brief's cited baseline and to
`PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md`'s own re-measured
figure — confirms nothing moved on `main` between that rung's merge and this
one's start, despite the concurrent unrelated Bigville session's activity.

**None of the 8 target tasks is already passing under this baseline** —
confirmed directly against `results/mbpp_endgame.json`'s `runnable_rows`
(the `full` arm's own pass-id list), not inferred from the citation:

```python
passing = {row['task_id'] for row in mbpp_endgame['full']['runnable_rows'] if row['passed']}
{259, 261, 273, 282, 399, 401, 429, 445} & passing == set()   # confirmed empty
```

(exact command in §9 "Reproduce")

---

## 2. Re-verifying the 8-task cluster — genuine op-need, not a stale citation

Per the task brief's own instruction ("this arc has caught stale citations
before"), each of the 8 tasks' real prompt + reference `code` was read
directly from `tests/fixtures/mbpp/sanitized-mbpp.json`, not re-quoted from
`PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md`'s own §7.3 table:

| task | prompt (abridged) | reference `code` | shape |
|---|---|---|---|
| 259 | maximize the given two tuples | `tuple(tuple(max(a,b) for a,b in zip(tup1,tup2)) for tup1,tup2 in zip(t1,t2))` | **nested** zip, elementwise `max` |
| 261 | division element-wise across two tuples | `tuple(ele1 // ele2 for ele1,ele2 in zip(t1,t2))` | flat zip, `//` |
| 273 | subtract elements of two tuples, same index | `tuple(map(lambda i,j: i-j, t1,t2))` | flat zip (`map` over 2 iterables ≡ `zip`+apply), `-` |
| 282 | subtract two lists element-wise | `list(map(lambda x,y: x-y, nums1,nums2))` | flat zip, `-`, **List** not Tuple |
| 399 | bitwise xor across given tuples | `tuple(ele1 ^ ele2 for ele1,ele2 in zip(t1,t2))` | flat zip, `^` |
| 401 | index wise addition of nested tuple elements | `tuple(tuple(a+b for a,b in zip(t1,t2)) for t1,t2 in zip(a,b))` | **nested** zip, elementwise `+` |
| 429 | elementwise `and` of two tuples | `tuple(ele1 & ele2 for ele1,ele2 in zip(t1,t2))` | flat zip, `&` |
| 445 | index wise multiplication of tuple elements | `tuple(tuple(a*b for a,b in zip(t1,t2)) for t1,t2 in zip(a,b))` | **nested** zip, elementwise `*` |

Every one of the 8 is confirmed a genuine `zip(a,b)` + per-pair binary
combiner shape — 5 flat (261/273/282/399/429), 3 one-level-nested (a tuple
OF tuples, needing `zip` applied at BOTH the outer and inner level:
259/401/445). This matches the task brief's citation exactly (op-need column
byte-identical to `OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md` §9 item 4's own
one-line description of each), so the citation was NOT stale — a genuine,
if minor, correction to this arc's own repeated caution.

**The actual spec variables the search sees** (via
`domains.mbpp_spec.split_rows`, not the prompt's own parameter names —
confirmed live, `scripts/` not needed, direct call):

```
259: a=Tuple[Tuple[int]], b=Tuple[Tuple[int]] -> Tuple[Tuple[int]]
261: a=Tuple[int], b=Tuple[int] -> Tuple[int]
273: a=Tuple[int], b=Tuple[int] -> Tuple[int]
282: a=List[int],  b=List[int]  -> List[int]      (the ONE List-shaped task)
399: a=Tuple[int], b=Tuple[int] -> Tuple[int]
401: a=Tuple[Tuple[int]], b=Tuple[Tuple[int]] -> Tuple[Tuple[int]]
429: a=Tuple[int], b=Tuple[int] -> Tuple[int]
445: a=Tuple[Tuple[int]], b=Tuple[Tuple[int]] -> Tuple[Tuple[int]]
```

Every task has EXACTLY 2 spec variables, both list/tuple-shaped, equal
length on every row — this is the exact evidence gate used in §6.

**No overlap with any prior rung's mechanism.** None of the 8 references
`%`/`Mod` (the `MODSQRT_SCOPED_FIX`/`412` cluster), no Dict-shaped variable
or output (`GroupCount`/`DictMerge`), no `FilterList` predicate need (the
`filter_templates_by_size` gap). A genuinely separate, additive gain.

---

## 3. Zero-new-Term composability — checked and ruled out, not assumed

Per this arc's own repeated lesson ("check zero-new-Term composability
first" — the `IntersectAll`/`UnionAll`/`DictFromPairs` precedent, all built
as a `Fold`-composition of already-shipped Terms with **zero** new
`TermNode` variants): does any existing Term, or composition of existing
Terms, already iterate TWO sequences in lockstep?

Read `term.rs` end-to-end for every Term that iterates a sequence
(`MapList`, `MapSet`, `IndexedMap`, `Sum`, `Prod`, `MaxOver`, `MinOver`,
`Fold`, `FilterList`, `Exists`) — **every one of them binds ONE variable
(or two variables, `IndexedMap`, but BOTH derived from the SAME single
source: item + its own index) over a SINGLE source.** None iterates two
INDEPENDENT sources in lockstep. Confirmed by grep (`grep -n "Zip\|zip"
runners/dsl/src/term.rs runners/dsl/src/synth_enumerate.rs`): the only
hits are Rust's own internal `.iter().zip(...)` calls INSIDE existing
evaluator code (`covers_value`, `Dot`, a params-loop) — never exposed as a
composable Term or op-table entry.

**The closest existing precedent, `vec_binary`** (`term.rs`, backing
`VecAdd`/`VecSub`/`Dot`) — **already zips two operands and applies a binary
combiner**, but the combiner is a hard-coded Rust closure
(`impl Fn(f64, f64) -> f64`), not a Term argument, and the shape always
truncates numerically through `f64` (wrong for `BitXor`/`BitAnd`, which
need integer semantics) and always emits a bare `Tuple` (wrong for task 282,
which needs `List`). It is direct evidence the ENGINE already has the zip
SHAPE internally — just never exposed generically. This rung's `ZipWith` is
that same shape with the op parameterised as a Term (so any of the 7
needed ops — and, compositionally, arbitrarily many future ones — can use
it) and the output kind following `a` via `Value::reseq` (so 282's List
output is handled for free, not as a special case).

**Verdict: no zero-new-Term composition reaches this shape.** A new
`TermNode` is required, matching the task brief's own expectation ("most
likely, since none of `Fold`/`MapList`/etc. iterate TWO sequences in
lockstep today").

---

## 4. Live hand-verification — Python simulation BEFORE any Rust was written

Per the task brief's step 3, all 8 tasks' exact term-tree were hand-verified
against revealed AND held-out rows via a direct Python simulation of the
intended `ZipWith` semantics (`zip` truncation + `Value::reseq`-style
type-preservation), run BEFORE any `.rs` file was touched:

```python
def zipwith(a, b, op):
    return type(a)(op(x, y) for x, y in zip(a, b))

OPS = {'Max': max, 'IDiv': floordiv, 'Minus': sub, 'BitXor': xor,
       'Plus': add, 'BitAnd': and_, 'Times': mul}
```

Result, all 8 tasks, all rows (revealed + held-out), **24/24 rows correct,
including exact container-type match** (`type(got) == type(expected)` —
catches a List/Tuple mismatch, which this engine's `Value::PartialEq`
treats as a hard inequality, never cross-type-equal — see `value.rs`'s own
"THE FIX (ARC6 value layer)" comment):

```
259 Max nested    -> 3/3 rows OK (Tuple[Tuple[int]])
261 IDiv flat     -> 3/3 rows OK (Tuple[int])
273 Minus flat    -> 3/3 rows OK (Tuple[int])
282 Minus flat    -> 3/3 rows OK (List[int])
399 BitXor flat   -> 3/3 rows OK (Tuple[int])
401 Plus nested   -> 3/3 rows OK (Tuple[Tuple[int]])
429 BitAnd flat   -> 3/3 rows OK (Tuple[int])
445 Times nested  -> 3/3 rows OK (Tuple[Tuple[int]])
```

This simulation directly informed the Term design (§5): `av.reseq(out)` for
type preservation, `op(x,y)` as a Term slot rather than a fixed closure,
and the NESTED shape as `ZipWith` calling `ZipWith` again in its own
`value` argument (no second Term needed — see §5).

Live re-verification through the REAL, now-built engine (not just the
Python simulation) is in §8.

---

## 5. Design

**`TermNode::ZipWith { a: TermIdx, b: TermIdx, a_name: Sym, b_name: Sym,
value: TermIdx }`** (`term.rs`) — iterates `a` and `b` IN LOCKSTEP (Python
`zip` truncation semantics: stops at `min(len(a), len(b))`), binding each
pair's two elements to `a_name`/`b_name` before evaluating `value`, popping
both after. Modelled on:

- `IndexedMap`'s two-bound-variable-over-one-source shape, generalised to
  TWO sources (the same generalisation `IndexedMap`'s own doc comment
  already applied to `MapList`'s one-var shape).
- `vec_binary`'s already-shipped zip-with-fixed-op precedent (§3), made
  generic by making the op a Term argument.

Evaluate (`term.rs`):

```rust
TermNode::ZipWith { a, b, a_name, b_name, value } => {
    let av = evaluate(arena, *a, env, ctx);
    let bv = evaluate(arena, *b, env, ctx);
    let a_snap = av.snapshot();
    let b_snap = bv.snapshot();
    let n = a_snap.len().min(b_snap.len());
    let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(n);
    for i in 0..n {
        env.push((*a_name, a_snap[i].clone()));
        env.push((*b_name, b_snap[i].clone()));
        let v = evaluate(arena, *value, env, ctx);
        env.pop(); env.pop();
        out.push(v);
    }
    av.reseq(out)
}
```

`av.reseq(out)` (the already-shipped, already-used `Value::reseq` helper —
`value.rs`, used at `term.rs:3847` and twice in `shape_decode.rs`) picks
`List` when `a` is a `List` and `Tuple` otherwise — this is what makes task
282 (List-in/List-out) and the other 7 (Tuple-in/Tuple-out) both round-trip
their own container kind with NO separate coercion Term, confirmed
necessary by `value.rs`'s own documented invariant: `Value::List(a) ==
Value::List(b)` compares elementwise, but `List` NEVER cross-compares equal
to `Tuple` — a naive `List`-always output would have silently failed all 7
Tuple-expecting tasks.

**Nested composition — no second Term.** Tasks 259/401/445 need `zip`
applied at BOTH the outer level (over the two top-level tuples) and the
inner level (over each bound PAIR's own two sub-tuples). This composes as
`ZipWith(a, b, __za, __zb, ZipWith(Var(__za), Var(__zb), __zi, __zj,
OP(Var(__zi), Var(__zj))))` — the outer `ZipWith`'s `value` is itself a
`ZipWith` call, referencing the outer-bound `__za`/`__zb` as its OWN `a`/
`b` sources. `env_get`'s existing stack-shadowing semantics (`env.iter()
.rev().find(...)`, `term.rs`) make this correct with no special-casing:
each nesting level's bound vars are looked up from the innermost active
binding outward.

**Registration** (`synth_enumerate.rs`) — a NEW `OpKind::ZipMap`,
deliberately narrower than `OpKind::ListBinary` (`ConcatList`'s own
registration path, the full `sa x sb` cross product over `list_by_size`):
`ZipWith`'s two sources `a`/`b` are drawn ONLY from `list_by_size[1]` (raw
declared spec variables, never a derived subterm) — a documented,
deliberate narrowing, justified because every one of the 8 witness tasks
zips the raw arguments directly, never a wrapped/derived sequence. This
collapses the growth-loop partition from a 3-way `sa x sb x st` search to a
SINGLE partition point per `size` (`st = size - 3`), keeping search cost
near-constant regardless of `max_size` — see §6 for the exact cost
accounting.

**The template pool** (`zip_op_templates_by_size`, built once per search,
gated behind `zip_wanted = op_list.iter().any(|(n,_)| n == "ZipWith")`,
exactly the `filter_templates_by_size`/`indexed_map_templates_by_size`
zero-cost-when-unused discipline) — a SMALL, FIXED set: the 7 elementwise
ops this rung's population needs (`Max`, `IDiv`, `Minus`, `BitXor`, `Plus`,
`BitAnd`, `Times`, all already-shipped `TermNode`s), each in two flavours:

- **FLAT** (size 3): `OP(Var(__za), Var(__zb))`.
- **NESTED** (size 6): `ZipWith(Var(__za), Var(__zb), __zi, __zj,
  OP(Var(__zi), Var(__zj)))`.

No numeric-constant/scalar-variable cross product (unlike
`filter_templates_by_size`'s six families) — every witness composes the
bound pair DIRECTLY, so a bigger pool would only cost budget for zero
additional reach.

**Size accounting** (leaf size 1, node size = 1 + sum of child sizes, this
module's own documented MDL convention): FLAT candidate registers at outer
size `1 (ZipWith node) + 1 (a, a size-1 Var) + 1 (b) + 3 (flat template) =
6`. NESTED candidate registers at outer size `1 + 1 + 1 + 6 (nested
template) = 9` — exactly at `DEFAULT_MAX_SIZE` (9), the tightest possible
fit. Confirmed reachable in §8 (the growth loop is `for size in
2..=max_size` inclusive).

---

## 6. Evidence gating — never a blanket `OP_TABLE` append

`spec_has_two_zippable_list_vars` (`synth_enumerate.rs`) — a NEW evidence
flag: does the spec have at least 2 DISTINCT variables that are
list/tuple-shaped on EVERY row AND pairwise equal-length on every row? A
single list-shaped variable (e.g. task 88's `a`) never sets this — it is a
genuine narrowing past `spec_is_list_shaped` (which only needs ONE
list-shaped var/output), matching this arc's own "output-type/structural
evidence, never input-shape alone" discipline for every gate added since
Rung 1's task-132 regression. `ZipWith` is pushed onto the list-shaped
typed default's op list ONLY under this evidence.

**Regression risk, priced before measuring.** The gate can only ever ADD
`ZipWith` to a spec's op list where it did not exist before; it never
narrows or removes any existing op from any other spec's inventory (purely
additive, matching every prior rung's own gating discipline). The realistic
regression surface is therefore: could `ZipWith`'s ADDITION regress a
CURRENTLY-PASSING task whose spec happens to have 2 equal-length
list-shaped vars, by exhausting search budget before the search reaches its
existing accepted candidate (the exact `task-132`-class mechanism named
throughout this arc)? Checked directly in §8 via the full-battery
before/after set-diff (not assumed safe from the gate's own narrowness) —
the `list_by_size[1]`-only sourcing scope (§5) keeps `ZipWith`'s own
contribution to search cost small (at most `|list_by_size[1]|^2 x 14`
extra candidates checked per size step it fires at, and it fires at exactly
2 size values — 6 and 9 — not the full growth range), which bounds the
worst case even for a canary this gate does fire on.

---

## 7. Touch-point cost — measured against the `GROUPCOUNT_DICTMERGE`
   template

| file | change |
|---|---|
| `runners/dsl/src/term.rs` | +1 enum variant (`ZipWith`, ~26-line doc comment), `copy_subtree` arm, `evaluate` arm (~18 lines), `children` arm |
| `runners/dsl/src/term_variants.rs` | regenerated via `tools/gen_term_variants.py` (mechanical, `NUM_TERM_VARIANTS` 229→230) |
| `runners/dsl/src/reflect.rs` | describe arm, read-back arm |
| `runners/dsl/src/jsonio.rs` | `variant_name` arm, `write_fields` arm, read-back arm |
| `runners/dsl/src/synth_enumerate.rs` | `OpKind::ZipMap` variant + doc, `OP_TABLE` entry, `build_zip_with`, `ZIP_ELEMENTWISE_OP_NAMES` + `build_zip_elementwise_op`, 4 new local `Sym`s (`__za`/`__zb`/`__zi`/`__zj`), `spec_has_two_zippable_list_vars` evidence flag, `zip_op_templates_by_size` pool construction (its own independent `if zip_wanted` block), `OpKind::ZipMap` growth-loop arm, `term_json`/`term_str` arms for `ZipWith` itself PLUS `IDiv`/`BitAnd`/`BitXor` (found live — see RESULTS §1, a genuine mid-rung finding, the same class `DICTFROMPAIRS_PREREG.md` §4 hit for `MkDict`), evidence-gate `v.push("ZipWith")` |

**1 new `TermNode` variant** (matching `GroupCount`'s own single-variant
cost, half of `DictMerge`+`GroupCount`'s combined 2), **6 files touched**
(one more than `GROUPCOUNT_DICTMERGE_RESULTS.md`'s cited "six exhaustive-
match sites" — the extra file is `synth_enumerate.rs` itself carrying both
the `term_json` AND registration logic, which that rung's own count also
folded into its "6" informally). Line count is higher than `GroupCount`/
`DictMerge`'s combined ~100-150 lines because `ZipWith` needs its OWN
template-pool construction (the `IndexedMap`-class registration shape,
which `GroupCount`/`DictMerge` — both `OpKind::Unary`/`OpKind::Binary`,
the cheapest registration classes — did not need at all). Still well within
the "roughly in line" bar the task brief set, and an order of magnitude
below the `Range`/iteration or indexed-string-filter gaps this arc's own
prior surveys explicitly declined to build as "materially larger, unpriced,
engine-architecture-level" changes.

---

## 8. Build + verification

Built, verified correct (hand-simulation, real-engine hand-built terms,
real `SynthEnumerate` search calls — 5/8 tasks solve within the default
200,000-candidate budget, the remaining 3 solve with a larger budget,
confirming the mechanism itself is correct), and measured against the real
MBPP battery: **zero net gain (byte-identical 76/75/101), root cause
diagnosed and localized to pre-existing pipeline architecture, not this
rung's own primitive.** Full detail, the genuine mid-rung `IDiv`/`BitAnd`/
`BitXor` finding, and the completed regression suites (Rust 778/0/4,
named 9-file 241/3-known) are in the accompanying
`PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_RESULTS.md` — not duplicated here.

---

## 9. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-zip-elementwise
git log --oneline -1   # on top of main @ dbe67c6
```

8-task pre-baseline non-membership check:
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import json
with open('results/mbpp_endgame_BEFORE_this_rung.json') as f:
    d = json.load(f)
passing = {r['task_id'] for r in d['full']['runnable_rows'] if r['passed']}
target = {259, 261, 273, 282, 399, 401, 429, 445}
print('overlap:', target & passing)
"
```

Python simulation (§4), no Rust needed:
```bash
PYTHONPATH="runners/dsl/python:." python3 /tmp/.../sim_zipwith.py   # see §4 for inline source
```
