# `gapped:enumerate_failed` / budget-exhausted bucket survey — PREREG

**Date:** 2026-08-16 (session date; harness clock reads 2026-08-16, prior
rungs in this same-day sequence are dated 2026-08-16 too). Base
`main @ 78afd81` ("Merge progsyn-structural-reject-survey: NO-GO,
property-reject fallback pattern ported and measured, zero conversions"),
verified fresh via `git log --oneline -1 main` before creating the worktree.
Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-budget-exhausted-survey`,
branch `progsyn-budget-exhausted-survey`.

---

**HEADLINE, stated up front: the population is NOT what its own name
suggests, and that reframing is the primary finding of this document.**
`gapped:enumerate_failed`/budget-exhausted (82 tasks, re-measured live
against the current 73/72/101 baseline, byte-identical in count to the
task brief's own cited figure) is usually described as "the search never
found ANYTHING within budget." **Measured directly, task-by-task, via a
call-tracing probe on the real pipeline: 20 of the 82 tasks (24%) DO find
a real, budget-cheap candidate that fits every revealed row — that
candidate is then excluded (almost certainly by a downstream structural/
property verdict, matching this arc's own `STRUCTURAL_REJECT_SURVEY`/
`PROPERTY_REJECT_SURVEY` mechanism) and the RETRY, not the original
search, is what exhausts the 200,000-candidate budget.** The other 62
(76%) are genuine first-attempt zero-recall cases — no candidate is EVER
proposed, at any budget. Only this second, 62-task population is a
plausible target for a primitive-layer fix; the first 20 share the same
information-theoretic floor this arc's structural/property-reject surveys
already NO-GO'd (§2).

**Within the 62-task genuine-zero-recall population, grouped by spec
shape (34 bare-scalar, 39 list-shaped, 9 pure-string; zero Dict-shaped —
the task brief's Dict-exclusion instruction is confirmed MOOT for this
specific population, §3) and cross-checked against `synth_enumerate.rs`'s
own OP_TABLE: `Mod`/`Pow`/`Sqrt`/all six bitwise ops (`BitAnd`/`BitOr`/
`BitXor`/`Shl`/`Lshr`/`Ashr`) already exist as fully-evaluated,
already-wired `TermNode` variants — used elsewhere in the engine — but
NONE of the eleven is exposed in `OP_TABLE` at all. `synth_enumerate.rs`'s
own source comment (line ~2737) independently confirms this for one of
them: "the pool has `{+, -, *}` and no `Mod`, so a DIVISIBILITY quantifier
is not reachable here."**

**Two independent, zero-new-`TermNode` clusters were found, each with
≥2 live-verified (revealed AND held-out) witnesses, both scoped to the
SAME narrow, low-blast-radius branch:**

- **`Sqrt`** (tasks 246, 293) — `Sqrt(a)` and
  `Sqrt(a*a + b*b)`, both live-verified end-to-end (6/6 exact matches
  including held-out), and — unlike every other candidate checked —
  **neither needs any ungrounded literal constant**: both compositions
  use only the spec's own variables, so the usual "structural constant
  not in the default `{0,1,2,-1}+outputs` pool" search-cost tax
  (§4, the SAME mechanism `MAX_SIZE_SEAM_PRICING_PREREG.md` and this
  document's own task-171 case study both independently hit) does not
  apply to either witness.
- **`Mod`** (tasks 77, 435 for the general-grid/bare-scalar shape; 75,
  426 ALSO live-verified correct but requiring a SEPARATE,
  higher-blast-radius change to `filter_templates_by_size` — named,
  priced, explicitly NOT built this rung, §5.2) — `Eq(Mod(a,11),0)` and
  `Mod(a,10)`, both live-verified end-to-end. Both witnesses need an
  UNGROUNDED literal modulus (11, 10) not present in the default constant
  pool — the SAME search-cost risk factor named above — so, unlike
  `Sqrt`, conversion is genuinely uncertain even after the op is exposed;
  this is measured, not assumed, in §7.

**Plan**: build `Sqrt`(Unary)/`Mod`(Binary) exposure SCOPED ONLY to the
bare-scalar `else` branch of `eval_synth_enumerate`'s typed-default
construction (`domains/prog_synthesis.py` is untouched; the change is
100% Rust, `synth_enumerate.rs`) — the branch used exclusively by specs
with no list/dict/set/string-shaped variable or output. This branch is
architecturally disjoint from `LIST_EXTRA_OPS`/`filter_templates_by_size`
(the machinery Rung 1 already measured is fragile — task 132's own
regression), so this build carries **zero blast radius to any list-shaped
spec, including task 132**, confirmed by construction (the bare `else`
branch and the list-shaped branch are mutually exclusive `if`/`elif` arms)
and re-confirmed by the live regression battery in §7-8. The
`filter_templates_by_size` Mod-quantifier needed for tasks 75/426 is
named, correctness-verified, and explicitly deferred (§5.2) — it touches
the SAME shared FilterList template pool every list-shaped spec's search
uses, a materially different risk class this single-variable rung
declines to bundle in, matching this arc's own repeated
`DICTFROMPAIRS`/`MAX_SIZE_SEAM_PRICING` precedent for splitting a
correctly-diagnosed but differently-scoped follow-on candidate out of the
rung that found it.

---

## 1. Re-measurement against the CURRENT baseline, not the task brief's cited count

`scripts/mbpp_endgame_battery.py`, run fresh in this worktree:

```
full:              73/257  p=0.284047  ci=[0.232408, 0.342046]  det_identical=True
content_stripped:  72/257  p=0.280156  ci=[0.228799, 0.337987]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

Byte-identical to the task brief's own cited baseline (73/72/101) and to
`STRUCTURAL_REJECT_SURVEY_PREREG.md`'s own re-measurement one rung earlier
— confirms nothing has moved between that rung's merge and this one's
starting point.

`scripts/ceiling3_diag_sweep.py` (unmodified), re-run against all 184
non-passing runnable `full`-arm tasks:

```
gapped:enumerate_failed           94
accepted_holdout_fail             51
gapped:property_verdict_reject    18
gapped:structural_verdict_reject  15
gapped:exhausted                   2
not_recognized                     1
runner_exception:ValueError        1
gapped:no_shape                    1
runner_exception:TypeError         1
                                 -----
total                            184
```

Byte-identical to `STRUCTURAL_REJECT_SURVEY_PREREG.md`'s own §1 table —
confirms the population has not moved since that rung landed.

Splitting `gapped:enumerate_failed` (94) by `halt_reason` (via the
`enumerate.tested` field the diagnostic sweep already records — `==200000`
is budget-exhausted/`max_candidates`, `<200000` is genuinely saturated):

```
budget-exhausted (tested == 200,000 exactly): 82
saturated (tested < 200,000):                 12
```

**82, byte-identical to the task brief's own cited count and to
`CEILING_REASSESSMENT_4_PREREG.md`'s original 82** — this specific
sub-population's SIZE has not moved even though its membership plausibly
could have (the task brief's own caution); the saturated count (12) is
exactly `14 − 2` (tasks 111/140, `IntersectAll`/`UnionAll`'s own
witnesses, converted between REASSESSMENT_4 and today — `IntersectAll`/
`UnionAll_RESULTS.md` §4/§5), confirming exact reconciliation.

**Full 82-task-id list** (`results/ceiling3_diag_sweep.json`, this
worktree): `14, 18, 75, 77, 80, 92, 102, 103, 108, 123, 126, 128, 137,
160, 163, 165, 170, 171, 172, 226, 228, 229, 240, 242, 246, 248, 251, 252,
255, 256, 259, 260, 261, 262, 264, 265, 273, 274, 280, 282, 293, 295, 297,
300, 304, 307, 308, 310, 389, 390, 391, 392, 395, 396, 397, 399, 401, 408,
411, 414, 415, 419, 421, 422, 426, 427, 429, 430, 432, 435, 437, 439, 440,
442, 445, 447, 448, 453, 459, 468, 478, 479`.

## 2. Dict-shaped-slice exclusion — confirmed MOOT for this specific population

Every one of the 82 task's revealed-row spec shape was computed via
`domains/prog_synthesis.py::_synth_spec_shape_flags` (the module's own
Python mirror of the Rust routing predicates, read in full before use —
its docstring names the 10-flag scope and the known `output_is_dictlike`
gap, patched locally in this survey's own scratch script since the shipped
mirror doesn't carry that one flag; `has_dict_value` is unaffected and
confirms the same conclusion independently). **Zero of the 82 tasks is
Dict-shaped** (`output_is_dictlike` false, `has_dict_value` false, for
every one) — the two known Dict-shaped SATURATED tasks this arc already
covered (`DICTFROMPAIRS_PREREG.md`/`_RESULTS.md`, tasks 277/465) are in the
**saturated** 12, not the **budget-exhausted** 82. The task brief's
explicit "exclude the already-covered Dict-shaped slice" instruction is
therefore satisfied by construction — there is nothing to exclude from
this specific 82-task population.

## 3. Grouping by spec shape and typed-default op bucket

Bucket computed by mirroring `eval_synth_enumerate`'s own typed-default
branch selection (`synth_enumerate.rs` lines ~2215-2370, read in full) in
a scratch Python re-implementation, cross-checked against the real
pipeline's own `enumerate.ops`/`ps_enum_ops` field for all 82 (confirmed
empty for every one — **none of the 82 uses a curated/rule-selected `ops`
list; all 82 reach the Rust-internal typed default**, so this
re-implementation is the operative routing, not an approximation of a
path the real spec never takes):

| bucket | n | task ids |
|---|---|---|
| `DEFAULT_OPS+LIST_EXTRA_OPS` (list-shaped) | 39 | 75, 108, 128, 137, 170, 229, 240, 251, 252, 255, 259, 261, 262, 265, 273, 280, 282, 297, 304, 307, 308, 310, 390, 391, 399, 401, 408, 414, 415, 419, 421, 426, 429, 439, 440, 442, 445, 447, 468 |
| `DEFAULT_OPS(bare)` (scalar-only) | 34 | 14, 77, 80, 92, 103, 123, 126, 160, 163, 165, 171, 172, 228, 242, 246, 248, 256, 260, 264, 274, 293, 295, 300, 389, 392, 395, 397, 422, 430, 432, 435, 448, 453, 479 |
| `DEFAULT_STR_OPS` (pure-string) | 9 | 18, 102, 226, 396, 411, 427, 437, 459, 478 |
| `SET_DEFAULT_OPS` | 0 | — |
| `DICT_DEFAULT_OPS` | 0 | — |

No single op-bucket dominates alone (39/34/9) — the task brief's own
caution about a heterogeneous population is confirmed at this grain. The
next section's Group-A/Group-B split is what actually separates a
plausible-fix population from a not-plausible one, cutting ACROSS these
three buckets.

## 4. THE central finding: 20 of the 82 already find and reject a candidate before exhausting budget — this is NOT "never found anything"

**Method**: a call-tracing probe (`/tmp/trace_all.py` in this session,
scratch, not committed — reproduce steps in the Reproduce section) wraps
`sub._inner.evaluate` via a Python proxy object substituted for
`sub._inner` (the native PyO3 substrate cannot be monkey-patched directly;
its wrapper attribute CAN be reassigned) and records every
`SynthEnumerate` call `domains.prog_synthesis.synthesize_from_request`
makes internally for each of the 82 tasks, in order, with each call's
`exclude` list length and result (`found`/`tested`/`distinct`/
`halt_reason`).

**Task 171 ("perimeter of a regular pentagon", `5*a`) as the worked
case, traced call-by-call:**

```
call 1 (max_size=9, exclude=[]):  found=True,  tested=5046,   halt=solved,  term='min(50, (a * a))'
call 2 (max_size=1, exclude=[]):  found=True,  tested=1,      halt=solved,  term='0'      (a separate, unrelated max_size=1 probe lane)
call 3 (max_size=9, exclude=[]):  found=True,  tested=5046,   halt=solved,  term='min(50, (a * a))'
call 4 (max_size=1, exclude=[]):  found=True,  tested=1,      halt=solved,  term='0'
call 5 (max_size=9, exclude=[the exact 'min(50,a*a)' term JSON]):
                                   found=False, tested=200000, halt=budget
```

**`min(50, a*a)` is a spurious fit**: `a=5→a*a=25=min(50,25)` and
`a=10→a*a=100→min(50,100)=50` both coincidentally match the 2 revealed
rows, but the program is wrong in general (it is NOT `5*a`). The real
pipeline finds this exact candidate, at LOW cost (`tested=5046`, far under
budget), on its FIRST real attempt — then a downstream mechanism (not
re-traced to its exact rule here, but structurally identical to the
`structural_verdict_reject`/`property_verdict_reject` machinery this
arc's own two immediately-preceding surveys already characterized in
detail) adds this exact term to the goal's `exclude` list and re-invokes
`SynthEnumerate`. **The re-search — not the original search — is what
exhausts the 200,000-candidate budget**, because the TRUE general solution
(`5*a`) needs the literal constant `5`, which is not in the default
`{0,1,2,-1}+outputs(25,50)` constant pool and must be built via a multi-step
arithmetic chain (e.g. `Plus(Plus(Plus(Plus(2,2),2),2),1)`), a
combinatorially larger sub-search than the shortcut the exclude just
removed.

**Applied to the full 82-task population** (same probe, all 82 tasks,
counting a task as "Group A" iff SOME earlier `SynthEnumerate` call in its
trace shows `halt_reason=='solved'` with `tested>1` — i.e. a REAL search
attempt, not the unrelated `max_size=1` probe lane — at a STRICTLY LOWER
`exclude` length than the terminal budget-exhausted call):

```
Group A (finds-then-excludes-then-budget-exhausts): 20 / 82  (24%)
  14, 77, 92, 103, 126, 165, 171, 228, 256, 295, 300, 304, 389, 392, 396,
  397, 414, 430, 432, 453
Group B (genuine first-attempt zero-recall):        62 / 82  (76%)
  18, 75, 80, 102, 108, 123, 128, 137, 160, 163, 170, 172, 226, 229, 240,
  242, 246, 248, 251, 252, 255, 259, 260, 261, 262, 264, 265, 273, 274,
  280, 282, 293, 297, 307, 308, 310, 390, 391, 395, 399, 401, 408, 411,
  415, 419, 421, 422, 426, 427, 429, 435, 437, 439, 440, 442, 445, 447,
  448, 459, 468, 478, 479
```

**Group A shares the SAME root cause `STRUCTURAL_REJECT_SURVEY_
RESULTS.md` §4 already named and NO-GO'd**: a spec underdetermined by 1-3
revealed rows admits cheap degenerate shapes (here, an arithmetic
coincidence rather than a memoized lookup table or an unread parameter,
but the same "few examples, many cheap wrong fits" floor) that a
downstream verdict correctly rejects, and the retry cannot manufacture
information the revealed rows do not contain. **This document does not
re-attempt the property/structural-reject fallback pattern against Group
A** — that pattern was already built, ported, and measured to convert
ZERO of its own eligible population one rung earlier
(`STRUCTURAL_REJECT_SURVEY_RESULTS.md` §3.2, 0/10) for exactly this
reason, and Group A is architecturally the SAME failure class one level
upstream (rejected-before-terminal-`gapped` rather than
terminal-`gapped`-itself). Group A is out of this rung's primitive-layer
scope and is not investigated further here.

**Group B (62 tasks) is the genuine target population**: for these, NO
candidate is EVER proposed by the search, at any point in its trace, at
any budget up to 200,000 — a real coverage gap, not an artifact of a
reject-and-retry cycle. §5 investigates Group B.

## 5. Group B, cross-checked against `OP_TABLE` — the missing-primitive finding

### 5.1 Eleven already-shipped, already-evaluated `TermNode` variants are absent from `OP_TABLE` entirely

`grep` over `runners/dsl/src/term.rs`'s `TermNode` enum (read in full for
the relevant region, lines ~640-860) confirms `Mod`, `Pow`, `Sqrt`,
`BitAnd`, `BitOr`, `BitXor`, `Shl`, `Lshr`, `Ashr` all exist as full
enum variants with working `evaluate()` arms (`term.rs:7653` `Mod`,
`:7663` `Pow`, `:7682` `Sqrt`, plus the bitwise family) — used elsewhere in
the engine (rule-authored code, other domains), fully round-trippable.
`grep` over `synth_enumerate.rs`'s `OP_TABLE` (`synth_enumerate.rs:291-403`,
read in full) and `build_op` (`:562-602`, read in full) confirms **none of
these eleven names appears in either** — an unrecognized op name is
silently filtered from any explicit `ops` list (`table_kind` returns
`None`, the name is dropped, `synth_enumerate.rs:2404-2432`), and none of
them can ever be produced by the typed-default construction either (they
are absent from `DEFAULT_OPS`/`LIST_EXTRA_OPS`/`DEFAULT_STR_OPS`/
`SET_DEFAULT_OPS`/`DICT_DEFAULT_OPS`/`TUPLE_BUILD_OPS`, all read in full).

**The module's own source comment independently corroborates this for
`Mod` specifically**, unprompted by this survey
(`synth_enumerate.rs:2737`, inside the `tmpl:nested_reduction`
`filter_templates_by_size` builder): *"the pool has `{+, -, *}` and no
`Mod`, so a DIVISIBILITY quantifier is not reachable here."* This is a
pre-existing, named-but-unaddressed gap in the codebase's own
documentation, not a novel diagnosis by this survey — this survey adds the
live measurement and the cross-population witness count.

### 5.2 Live-verified correctness — four `Mod`-shaped witnesses, two op-buckets

All four hand-built via `substrate_rs.Substrate()._inner.evaluate()`
against real fixture rows (revealed AND held-out), composing ONLY
already-shipped Terms (`Mod`/`Eq`/`FilterList`/`Sum`/`Var`/`Lit`):

```
task 77 (divisible by 11): Eq(Mod(a,11), 0)
  a=12345    -> False  == expected (revealed)
  a=1212112  -> True   == expected (revealed)
  a=1212     -> False  == expected (HELD-OUT)

task 435 (last digit): Mod(a,10)
  a=123 -> 3  == expected (revealed)
  a=25  -> 5  == expected (revealed)
  a=30  -> 0  == expected (HELD-OUT)

task 426 (filter odd numbers): FilterList(a, item, Eq(Mod(item,2),1))
  a=[1..10]           -> [1,3,5,7,9]     == expected (revealed)
  a=[10,20,45,67,84,93] -> [45,67,93]    == expected (revealed)
  a=[5,7,9,8,6,4,3]   -> [5,7,9,3]       == expected (HELD-OUT)

task 75 (tuples all-divisible-by-k): FilterList(a, item,
    Eq(Sum(source=item, var_name=x, value=Mod(x,b)), 0))
  a=[[6,24,12],[7,9,6],[12,18,21]], k=6 -> [[6,24,12]]  == expected (revealed)
  a=[[5,25,30],[4,2,3],[7,8,9]], k=5    -> [[5,25,30]]  == expected (revealed)
  a=[[7,9,16],[8,16,4],[19,17,18]], k=4 -> [[8,16,4]]   == expected (HELD-OUT)
```

**77/435 are `DEFAULT_OPS(bare)`-bucket (scalar-only spec, general
op-composition grid — the SAME registration class as `Minus`/`Div`/`Gt`).
75/426 are `DEFAULT_OPS+LIST_EXTRA_OPS`-bucket and specifically need `Mod`
INSIDE a `FilterList` PREDICATE, which is built by a SEPARATE, hardcoded
micro-grammar (`filter_templates_by_size`, `synth_enumerate.rs:2609-2820`)
that does not simply compose from `OP_TABLE` — exposing `Mod` as a Binary
op alone does NOT make it reachable inside a `FilterList` predicate; a
second, distinct change (a new template shape in
`filter_templates_by_size`, mirroring the existing `CMPS × numeric_consts`
loop) would be needed.** This second change touches the SAME shared
template pool `LIST_EXTRA_OPS`'s `FilterList` unconditionally offers to
EVERY list-shaped spec — the exact machinery `RUNG1_RESULTS.md` already
measured is fragile (task 132's own regression when even cheap unary ops
were added unconditionally to this branch). **This document prices but
does NOT build the 75/426 half** (§8) — it is a real, correctness-verified,
2-task candidate for a FUTURE, separately-regression-priced rung, matching
this arc's own repeated single-variable-rung discipline
(`DICTFROMPAIRS_RESULTS.md` §3.6, `MAX_SIZE_SEAM_PRICING_PREREG.md`'s own
explicit "named, not bundled" precedent).

### 5.3 Live-verified correctness — two `Sqrt`-shaped witnesses, BOTH constant-starvation-free

```
task 246 (babylonian-method sqrt; black-box I/O is just "return sqrt(a)"): Sqrt(a)
  a=10 -> 3.1622776601683795 ~= 3.162277660168379  (revealed, tol 0.001)
  a=2  -> 1.4142135623730951 ~= 1.414213562373095  (revealed, tol 0.001)
  a=9  -> 3.0                == 3.0                (HELD-OUT, tol 0.001)

task 293 (third side of a right triangle): Sqrt(Plus(Times(a,a), Times(b,b)))
  a=7,b=8  -> 10.63014581273465 == expected (revealed)
  a=3,b=4  -> 5.0               == expected (revealed)
  a=7,b=15 -> 16.55294535724685 == expected (HELD-OUT)
```

**Both compositions use ONLY the spec's own bound variables — no literal
constant beyond what the variables themselves supply.** This is the
material difference from the `Mod` cluster (§5.2, §7): neither witness is
exposed to the "structural constant absent from the default
`{0,1,2,-1}+outputs` pool" search-cost tax this document's own §4 worked
example (task 171) and `MAX_SIZE_SEAM_PRICING_PREREG.md` (task 277/465's
own `max_size` constant-reach ceiling) both independently identified as a
real, separate search-cost mechanism in this codebase. `Sqrt` is therefore
the higher-confidence half of this rung's build.

### 5.4 Whole-Group-B coverage check, per the SortBy lesson — other candidate primitives checked and NOT built

Every remaining Group-B task was checked against the prompt text and real
fixture rows for a plausible missing-primitive cause, cross-referenced
against what already exists as a `TermNode` (necessary for a
zero-new-Term fix) — not assumed from the prompt alone:

| candidate cause | tasks | witness count | verdict |
|---|---|---|---|
| bitwise family (`BitAnd`/`Shl`/…) | 228 (bit-range check), 399/429 (elementwise XOR/AND across two tuples) | 1 clean formula witness (228, needs `Shl`+`BitAnd`+`Not` TOGETHER — a multi-op composition); 399/429 additionally need a "zip two lists elementwise" primitive that does not exist AT ALL in this engine (no dual-source `MapList`) | below the arc's own ≥2-single-cause bar; 399/429 need a SEPARATE, larger primitive (elementwise zip) this survey did not find any OTHER witness for either — named, not built |
| `Range`/iteration over `1..n` (no `Range` `TermNode` exists at all, confirmed by grep) | 123 (amicable numbers), 126 (common divisors sum), 248 (harmonic sum), 256 (primes count), 295/453 (divisor sums), 389/448 (Lucas/Perrin recurrences), 260 (NSW primes), 422 (avg of cubes), 274 (binomial coefficients) | up to ~10 tasks share the NEED for iteration, but the FIX itself (a new `Range`-producing `TermNode` PLUS how it would enter the search's `list_by_size` pool from a SCALAR variable, a genuinely different registration shape than every existing `OpKind`) is a materially larger, unpriced, engine-architecture-level change — not a same-class "expose an existing Term" fix | real, large, multi-task-witnessed candidate — explicitly named as future work, NOT sized or built (out of this rung's "expose an already-shipped Term" scope) |
| string-index-parity filter (Mod on the INDEX, not the value) | 226, 437 (remove chars at odd string index/remove odd-position chars) | 2 tasks share the SHAPE, but the fix needs BOTH `Mod` availability AND an indexed string-filter/map primitive that does not exist for strings at all (`IndexedMap`'s source pool is Tuple/List/Set/FrozenSet only, never `Str` — confirmed by `is_listlike`'s own exclusion, `synth_enumerate.rs:507-509`) | genuinely different, larger, 2-part gap (index-aware string composition is entirely unaddressed in `DEFAULT_STR_OPS`) — named, not built |
| constant-starved arithmetic (formula reachable with EXISTING ops, but needs a "structural" literal not in the default consts pool) | 14, 80, 92 (partially), 160, 163, 172, 242, 264, 274, 300, 392, 395, 397, 419 (checked directly, not exhaustively re-derived for every single one) | the SAME mechanism §4's task-171 case study and `MAX_SIZE_SEAM_PRICING_PREREG.md` both already independently characterized as a search-cost, not primitive-availability, issue | out of THIS rung's scope by the task brief's own framing (a size/search-cost seam, already separately priced and NO-GO'd once); not re-investigated task-by-task here |

**No other candidate reaches the arc's own "≥2 live-verified witnesses,
zero-new-`TermNode`, single shared cause" bar this cleanly.** `Mod`/`Sqrt`
remain the largest, cheapest, most-verified cluster found in this survey.

## 6. Regression risk, priced before building

**Currently-passing bare-scalar (`DEFAULT_OPS(bare)`-bucket) canaries** —
computed the same way as §3's bucket assignment, against the CURRENT
73-task `full`-arm pass set:

```
[16, 17, 20, 58, 59, 82, 84, 85, 89, 127, 135, 138, 139, 227, 233, 234,
 266, 276, 309, 312, 404, 406, 458]
```

23 canaries, a real, non-trivial regression surface — checked directly
post-build (§7-8 exact task-id set diff), not assumed safe. Task 406
("find whether the parity of a given number is odd") is notable: it
already PASSES today WITHOUT `Mod` — its current accepted candidate uses
a different, currently-unknown mechanism (not re-traced here; checked
post-build only for whether it stays in the pass set).

**Zero of the 23 canaries is list/dict/set/string-shaped** (by
construction — they are members of the SAME bare-`else` branch this
build's scope is confined to), so the ONLY population this build can
possibly touch, by construction of where the code change lives, is this
23-canary set plus the 34-task bare-scalar Group-B/Group-A population
already surveyed above. **Task 132 (this arc's own standing
most-budget-fragile canary) is list-shaped and therefore structurally
unreachable by this change** — confirmed by the `if`/`elif` branch
exclusivity in `eval_synth_enumerate` (a spec cannot be BOTH
`is_list_shaped` and route through the bare `else` arm; task 132's own
`is_list_shaped` flag is `True`, confirmed in `RUNG1_RESULTS.md`'s own
prior measurement, unchanged by this document).

## 7. What this document does NOT establish before the build

1. Whether `Mod`, once exposed to the bare-scalar general grid, is
   actually FOUND within the real 200,000-candidate budget for tasks
   77/435 — genuinely uncertain, because both witnesses need an
   ungrounded literal modulus (11, 10) that must be built via a multi-step
   arithmetic chain from the default `{0,1,2,-1}+outputs` pool (the SAME
   search-cost tax §4's task-171 case study demonstrates is real and can
   fully block an otherwise-correct, small, already-reachable-by-existing-
   ops formula). This is a build-time question, measured honestly in the
   RESULTS document (not assumed), matching this arc's own standing
   "reach is not conversion" discipline.
2. Whether `Sqrt` is found within budget for 246/293 — considered
   HIGH-confidence (§5.3, no constant-starvation issue, small tree depth
   2-5), but not yet measured through the real pipeline.
3. Whether either op's exposure causes ANY of the 23 bare-scalar canaries
   (§6) to regress — priced as low-risk by construction (disjoint branch
   from list-shaped specs) but not yet measured; the RESULTS document
   measures this exactly, not by sampling.
4. The `filter_templates_by_size` Mod-quantifier for tasks 75/426 (§5.2)
   is correctness-verified but NOT sized for regression risk against
   task 132 or any other `FilterList`-using canary — deliberately deferred
   to a future, separately-scoped rung.
5. The `Range`/iteration gap (§5.4) affecting up to ~10 tasks is real and
   witnessed but not priced, designed, or built here — it is a materially
   larger primitive (a NEW way for a scalar to produce a dynamically-sized
   list, not merely exposing an existing Term) that this rung's own
   "expose an already-shipped Term" scope explicitly excludes.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 8. The plan

Build `Sqrt` (`OpKind::Unary`) and `Mod` (`OpKind::Binary`) in
`synth_enumerate.rs`, scoped EXCLUSIVELY to the bare-scalar `else` branch
of `eval_synth_enumerate`'s typed-default construction (NOT added to the
shared `DEFAULT_OPS` constant, which is also consumed by the list-shaped
branch — the two new ops are pushed only onto the LOCAL `v` vector inside
the `else` arm, so `DEFAULT_OPS` itself, and therefore every list-shaped
spec's op inventory including task 132's, is byte-unchanged). Zero new
`TermNode` variants (`Mod`/`Sqrt` are pre-existing, already-wired Terms —
the `IntersectAll`/`UnionAll`/`DictFromPairs` precedent class). Rebuild
from source, run the full paired MBPP battery (exact task-id-set diff
against the 73/72/101 baseline established in §1), run the Rust suite,
run the named 9-file Python regression suite, then write the RESULTS
document reporting the REAL conversion outcome for all four witnesses
(77, 435, 246, 293) honestly — including a null on any that do not convert
within budget, per §7's own stated uncertainty.

**What this rung does NOT attempt**: the `filter_templates_by_size`
Mod-quantifier for tasks 75/426 (§5.2, correctness-verified, deliberately
deferred — different risk class); the bitwise-family/zip-primitive gap
(228, 399, 429, §5.4, single-witness or needs a second missing primitive);
the `Range`/iteration gap (~10 tasks, §5.4, a materially larger primitive);
the string-index-parity gap (226, 437, §5.4, a different, 2-part gap);
Group A (20 tasks, §4, the SAME information-theoretic floor
`STRUCTURAL_REJECT_SURVEY_RESULTS.md` already NO-GO'd); constant-starved
arithmetic tasks whose formula is already expressible with existing ops
(§5.4's last row, a search-cost seam already separately priced and
NO-GO'd by `MAX_SIZE_SEAM_PRICING_PREREG.md`).

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-budget-exhausted-survey
git log --oneline -1 main   # 78afd81, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

`Mod`/`Sqrt` live-witness re-check (hand-built term JSON, no code change
needed to reproduce, matching the `IntersectAll`/`UnionAll` precedent):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
# task 77: Eq(Mod(a,11),0)
t77 = {'type':'Eq','a':{'type':'Mod','a':{'type':'Var','name':'a'},'b':{'type':'Lit','value':11}},'b':{'type':'Lit','value':0}}
print('77', [s._inner.evaluate(t77, {'a': a}) for a in (12345, 1212112, 1212)])
# task 246: Sqrt(a)
t246 = {'type':'Sqrt','arg':{'type':'Var','name':'a'}}
print('246', [s._inner.evaluate(t246, {'a': a}) for a in (10, 2, 9)])
# task 293: Sqrt(a*a + b*b)
t293 = {'type':'Sqrt','arg':{'type':'Plus','items':[
    {'type':'Times','items':[{'type':'Var','name':'a'},{'type':'Var','name':'a'}]},
    {'type':'Times','items':[{'type':'Var','name':'b'},{'type':'Var','name':'b'}]}]}}
print('293', [s._inner.evaluate(t293, {'a': a, 'b': b}) for a,b in ((7,8),(3,4),(7,15))])
"
```

Group A/B trace (the call-tracing probe, §4, scratch — not committed):
the method is to substitute `sub._inner` with a thin proxy object whose
`evaluate` method records `(exclude_length, result)` for every
`SynthEnumerate` call before delegating to the real native `evaluate`,
then call `domains.prog_synthesis.synthesize_from_request` normally and
inspect the recorded call sequence.
