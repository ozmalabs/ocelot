# PROGRAM SYNTHESIS ARC 2 Q0 — the MBPP blocker histogram (picks Q1 + Q2 scope)

**Date:** 2026-07-31
**Task:** PROGRAM_SYNTHESIS_ARC2_PLAN.md §2-Q0, part B — *"Blocker histogram
over MBPP: which value types / ops / statement shapes / prompt forms block,
ranked by task mass, greedy cumulative curve — THIS picks Q1's op set and
Q2's comprehension scope, exactly as P0's histogram picked the IR variants
(and note arc 1's lesson: the histogram over-predicted by ~25pp on
sub-construct blockers — Q0 must model sub-construct features explicitly
this time)."*
**Script:** `scripts/mbpp_blocker_histogram.py` (deterministic, stdlib-ast +
the REAL `domains.prog_ir_emit.emit_prog_ir`, no network, no substrate
boot).
**Data:** `results/mbpp_blocker_histogram.json` (full per-task rows, top-20
feature/task-id tables, all four curves, per-split aggregates).
**Companion:** `PROGRAM_SYNTHESIS_ARC2_PREREG.md` (the HQ1-HQ4 bars this
data feeds, the Q1 op-set recommendation reasoning, the three-way assert-
split protocol reconciliation with Q0-A).

## 1. Method

- **Corpus:** all 427 sanitized-MBPP tasks (`tests/fixtures/mbpp/
  sanitized-mbpp.json`), split by `task_id` per `provenance.json`'s
  canonical convention: fewshot [1,10] (7), test [11,510] (257), val
  [511,600] (43), train [601,∞) (120).
- **Entry-function resolution:** the top-level `def` whose name is CALLED
  in `test_list` (measured: unique match on all 427 tasks, including the
  12 multi-def tasks — a task defines a private helper + the tested
  function, and exactly one def name appears as a call in the asserts
  every time; 0 mismatches, the fallback-to-last-def path is never taken
  on this fixture).
- **Program-side:** the REAL `emit_prog_ir(code, name=entry)` — imported,
  never reimplemented or approximated — records `ok`/`blockers`/`externs`/
  `recv_methods`/`predictable` verbatim. Sub-construct features (arc-1's
  registered lesson: model these EXPLICITLY, not just statement/expression
  KIND presence) are counted by an independent ast-walk over the entry
  function's own subtree: kwargs/star-args calls, slices with/without
  step, nested funcs, lambdas, class defs, imports by module, string/
  collection/dict method calls BY NAME, container-literal kinds
  (dict/set/tuple), scalar literal kinds (none/bool/float), comprehension
  kinds, try/raise, recursion (self-call), while/for counts, multiple
  returns.
- **Value-domain:** an INDEPENDENT ast-based assert parser (implemented
  without importing the sibling Q0-A baseline script's `classify_assert` —
  same measured forms, own code, cross-checked in §6) classifies each
  `test_list` assert's call arguments + expected value into a literal type
  tag, peeling known wrap calls (`set`/`sorted`/`list`/`tuple`/`str`/
  `round`/`abs`/`bool`/`int`/`float`) around either side, and RE-TYPING the
  result by the OUTERMOST container-shaping wrap (`set(f(x)) == set((4,5))`
  compares a SET, not the RHS's literal Tuple AST kind — gated). A distinct
  `math.isclose(candidate(...), expected, rel_tol=...)` form (the corpus's
  entire non-Name-func-Call population, 13 tasks / 39 asserts, ALL
  `math.isclose`) is recognized as `float_tolerance` rather than dumped
  into an "unparseable" bucket — a real, well-defined MBPP verdict idiom
  with a direct design consequence (float held-outs need a tolerance
  comparator, not exact `Eq`).
- **Prompt-side:** request-verb form against 4 fixed observed prefixes
  (`write a [python] function to/that/which`) + a 55-word counted
  constraint vocabulary (sorted/prime/palindrome/maximum/.../convert — no
  NLP, a fixed list in the script).
- **Three greedy cumulative curves**, each task unlocking only when its
  ENTIRE remaining requirement set is covered (the P0 precedent: "a
  function unlocks only when its ENTIRE required set is chosen"), floors
  fixed per the arc-1 measured value-domain wall (int + list[int] only)
  and the P1-emitter's own current ok+predictable set:
  1. **value-domain curve** — type additions unlock the most
     ASSERT-TYPEABLE tasks.
  2. **op/feature curve** — Q1 op families (grouped from the REAL
     `emit_prog_ir` blockers + non-native externs + recv/dotted-method
     names) unlock the most fully `ok ∧ predictable` reference solutions.
  3. **joint curve** — a task unlocks only when BOTH axes are covered (the
     arc-1 registered lesson: single-axis curves over-predict by ~25pp —
     this is the honest ceiling line). A **Q1-scoped** variant additionally
     EXCLUDES any task needing an out-of-plan-scope family (regex, a
     same-corpus helper-function extern, complex numbers, or any other
     un-named tail family) — the REACHABLE ceiling for what Q1 can
     actually deliver, not the unrestricted theoretical one.

**Determinism:** the script was run twice (independently, post every code
change); `results/mbpp_blocker_histogram.json` was byte-identical across
runs both times (`cmp` clean; final sha256
`14d23d3356e75f46d3dc4d19cbe61343a90f4a968a4c09e68e4f8a6513330d32`).

## 2. What blocks emission (program-side, ranked)

| blocker (verbatim, real `emit_prog_ir`) | tasks | structural family |
|---|---|---|
| `SliceSubscript` | 25 | `slicing` |
| `CompTargetComplex` | 18 | `comprehension_advanced` |
| `Lambda` | 15 | `lambda` |
| `OpExt:BitXor` | 11 | `bitwise_ops` |
| `KwargsCall` | 11 | `kwargs` |
| `OpExt:BitAnd` | 10 | `bitwise_ops` |
| `OpExt:FloorDiv` | 6 | `floordiv_general` |
| `OpExt:LShift` | 6 | `bitwise_ops` |
| `CompMultiClause` | 5 | `comprehension_advanced` |
| `StarArgsCall` | 3 | `kwargs` |
| `OpExt:BitOr` | 3 | `bitwise_ops` |
| `ComprehensionDict` | 3 | `comprehension_advanced` |
| `InStrStatic` | 2 | `str_substring_static` |
| `OpExt:RShift` | 2 | `bitwise_ops` |
| `NestedUnpack`, `DefFn`, `TypedExcept` | 1 each | own family |

**Sole-blocker mass is high on MBPP** (123 blocker occurrences over 111
blocked tasks, ≈1.1 blockers/task) — the OPPOSITE of arc 1's `domains/`
corpus finding (P0: coverage came from SETS of variants landing together).
MBPP reference solutions are small, single-purpose, canonical — 316/427
(74.0%) are already IR-representable, 147/427 (34.4%) already fully
`predictable`, vs P2's 56.4%/9.2% on the general repo corpus.

**A measured, non-obvious finding.** Python overloads `&`/`|`/`^` between
integer bitwise ops and SET ALGEBRA (`set(a) & set(b)` for intersection —
task 2 `similar_elements`); the real emitter has no operand-type awareness
at emit time and blocks both identically as `OpExt:Bit*`. The `bitwise_ops`
family therefore bundles two distinct capabilities Q1 must both implement
(gated: `test_known_task_2_bitand_is_set_intersection_not_bitwise`).

**Non-native extern / recv-method mass (the PREDICTABILITY gap, among the
316 already-`ok` tasks):** `list`/`set`/`tuple`/`dict` container
constructors (35 tasks, the single largest predictability lever — cheap,
just add them to `NATIVE_ORACLES`); `re.search`/`re.sub`/`re.findall`/
`re.finditer`/match-object methods (27 tasks total — the plan's named
out-of-scope regex mass); `isinstance`/`map`/`all`/`enumerate`/... general
builtins (33 tasks); string methods (`join`/`replace`/`split`/
`capitalize`/...) via both computed-receiver (recv-form) and
accidental-dotted-Name-receiver shapes (20 tasks); `math.sqrt`/`math.pow`/
`round`/`ord`/`pow` (17 tasks); collection methods (`append`/`sort`/
`add`/...) (26 tasks); dict methods (`items`/`values`/`setdefault`) (6
tasks).

## 3. The three greedy cumulative curves

### (a) Value-domain curve (denominator: 425 type-coverable tasks)

Floor = `{int, list[int]}` (arc 1's measured value-domain wall). Top of the
curve (full 30-step table in the JSON):

| step | type added | +tasks | cumulative |
|---|---|---|---|
| 0 (floor) | — | 150 | 35.29% |
| 1 | `str` | +45 | 45.88% |
| 2 | `bool` | +51 | 57.88% |
| 3 | `float` | +22 | 63.06% |
| 4 | `tuple[int]` | +23 | 68.47% |
| 5 | `list[str]` | +18 | 72.71% |
| 6 | `tuple[mixed]` | +13 | 75.76% |
| 7 | `list[list[int]]` | +14 | 79.06% |
| 8 | `dict` | +11 | 81.65% |
| 9 | `list[tuple[int]]` | +12 | 84.47% |
| 10 | `list[list[str]]` | +9 | 86.59% |
| 11-12 | `list[tuple[mixed]]`, `none` | +14 | 89.88% |
| 13-15 | `list[mixed]`, `tuple[str]`, `set[int]` | +18 | 94.12% |
| 16-29 | 14 more (each ≤4 tasks; `list[dict]`, `tuple[tuple[int]]`,
  `list[float]`, `list[empty]`, `list[tuple[str]]`, `tuple[float]`,
  `list[bool]`, `list[list[mixed]]`, `list[tuple[float]]`, `set[str]`,
  `set[tuple[int]]`, `tuple[empty]`, `tuple[list[int]]`,
  `tuple[list[str]]`) | +25 | **100.00%** |

**Never-unlockable: 0** (the candidate set is exhaustive by construction —
the same finding as P0). Reaching 100% needs `str`+`bool`+`float`+`none`+
`dict` (the plan's own scope pin) PLUS every compound container/tuple type
tag observed — the plan's stated "only if the histogram forces them"
qualifier for `set`/generators is answered: `set[int]`/`set[str]`/
`set[tuple[int]]` DO appear (task mass 6 combined) and should be a light
SynthEnumerate leaf, not a new IR concern (representation already exists
via `ProgContainerLit`).

### (b) Op/feature curve (denominator: 427, all tasks — code-side, independent of assert parseability)

| step | family added | +tasks | cumulative |
|---|---|---|---|
| 0 (floor, current `ok ∧ predictable`) | — | 147 | 34.43% |
| 1 | `comprehension_advanced` | +26 | 40.52% |
| 2 | `regex` (OUT OF SCOPE, see §4) | +26 | 46.60% |
| 3 | `slicing` | +23 | 51.99% |
| 4 | `bitwise_ops` | +22 | 57.14% |
| 5 | `general_builtins` | +20 | 61.83% |
| 6 | `container_ctor` | +16 | 65.57% |
| 7 | `collection_methods` | +20 | 70.26% |
| 8 | `string_methods` | +19 | 74.71% |
| 9 | `math_native` | +16 | 78.45% |
| 10 | `lambda` | +15 | 81.97% |
| 11 | `kwargs` | +14 | 85.25% |
| 12-13 | `dict_methods`, `floordiv_general` | +12 | 88.06% |
| 14-56 | a 43-step tail of `stdlib_misc:*` (string/bisect/heapq/
  collections)/`misc_builtin:<other-mbpp-fn>`/`misc_method:*` singletons
  (each exactly 1-2 tasks: `Counter`, the `complex` builtin, `cmath`, and
  25 same-corpus helper-function externs — each MBPP task calling a
  DIFFERENT sibling MBPP function by name — plus `str_substring_static`,
  `nested_def`, `nested_unpack`, `typed_except`) | +51 | **100.00%** |

The unrestricted curve's step-1 pick (`regex` tied with
`comprehension_advanced` at 26 tasks, `comprehension_advanced` winning the
alphabetical tiebreak) is exactly why the RAW curve must not drive the
recommendation directly — regex is a genuinely new object model (match
objects, `re.Match` methods), explicitly out of the arc's scope (plan §1,
risk #5). §4's Q1-scoped curve removes it from the candidate pool entirely.

### (c) Joint curve — unrestricted (denominator: 425) and Q1-scoped (denominator: 355)

The unrestricted joint curve (types AND features both required) starts at
a MUCH lower floor than either single-axis curve — **69/425 = 16.24%**,
vs 150/425 (35.3%) for value-domain alone and 147/427 (34.4%) for
op/feature alone. This is the arc-1 lesson landing exactly as predicted:
single-axis curves over-predict because most tasks need BOTH a type and an
op-family fix simultaneously, and the two requirement sets only partially
overlap.

**The Q1-scoped joint curve is the one that matters for the recommendation**
(§4) — it EXCLUDES the 70 tasks that need an out-of-plan-scope family
(regex, a same-corpus helper extern, complex numbers, or an un-named tail
family) from ever counting as reachable, so its 100% ceiling is honestly
"everything Q1 can deliver," not "everything, including regex." Full table:

| step | added | +tasks | cumulative |
|---|---|---|---|
| 0 (floor) | — | 69 | 19.44% |
| 1 | `bool` | +14 | 23.38% |
| 2 | `bitwise_ops` | +18 | 28.45% |
| 3 | `str` | +15 | 32.68% |
| 4 | `float` | +14 | 36.62% |
| 5 | `math_native` | +15 | **40.85%** |
| 6 | `slicing` | +12 | 44.23% |
| 7 | `string_methods` | +12 | 47.61% |
| 8 | `general_builtins` | +11 | 50.70% |
| 9 | `tuple[int]` | +11 | 53.80% |
| 10 | `container_ctor` | +11 | **56.90%** |
| 11 | `collection_methods` | +11 | 60.00% |
| 12 | `lambda` | +11 | 63.10% |
| 13 | `list[str]` | +10 | 65.92% |
| 14 | `comprehension_advanced` | +11 | 69.01% |
| 15 | `list[tuple[int]]` | +10 | **71.83%** |
| 16 | `tuple[mixed]` | +9 | 74.37% |
| 17 | `list[list[int]]` | +9 | 76.90% |
| 18-19 | `dict`, `none` | +12 | 80.28% |
| 20-25 | `floordiv_general`, `list[mixed]`, `kwargs`,
  `list[list[str]]`, `dict_methods`, `list[tuple[mixed]]` | +36 | 90.42% |
| 26-44 | 19 more, each ≤5 tasks (`tuple[str]`, `list[dict]`, `set[int]`,
  `tuple[tuple[int]]`, `list[float]`, `str_substring_static`,
  `list[bool]`, `list[empty]`, `list[list[mixed]]`, `nested_def`,
  `nested_unpack`, `set[tuple[int]]`, `tuple[empty]`, `tuple[float]`,
  `tuple[list[int]]`, `tuple[list[str]]`, `list[tuple[float]]`,
  `list[tuple[str]]`, `typed_except`) | +34 | **100.00%** |

Never-unlockable under the Q1-scoped candidate set: 0 (same finding).

## 4. Recommended Q1 op set — the 55% mark, with 70% as a stretch goal

**Value domain (fixed by the plan; this histogram confirms full
reachability):** `int`, `list[int]` (existing floor) + `str`, `bool`,
`float`, `none`, `dict`.

**Op families at the 55% mark (step 10, 56.90%; the primary Q1 target):**
`bitwise_ops` (integer bit ops AND set intersection/union/symmetric-
difference — the §2 finding), `math_native` (round/pow/ord/`math.sqrt`/
`math.pow`/... as native oracles), `slicing` (string AND list
slice-with-step), `string_methods` (join/replace/split/capitalize/strip/
upper/lower/... as native oracles), `general_builtins` (isinstance/map/
all/any/next/enumerate/zip/reversed/iter — cheap, no new semantics),
`container_ctor` (`list`/`set`/`tuple`/`dict`/`frozenset` as native
oracles — the single largest non-native-extern mass, 35 tasks).

**Stretch (step 15, 71.83%, the 70% mark):** + `collection_methods`
(append/add/sort/extend/...), `lambda` (an inline anonymous-function IR
variant), `comprehension_advanced` (dict comprehensions + non-trivial
targets/multi-clause), plus `list[str]`/`list[tuple[int]]` enumerator
reach.

**Named exclusions:** `regex` (26 tasks — a new object model, explicit
plan risk #5); same-corpus helper-function externs (30 singleton tasks —
Q3+ declared-oracle territory, not a Q1 value-domain op); the long
`misc_builtin:*`/`stdlib_misc:*` tail (Counter, complex, cmath, bisect,
heapq — 1-2 tasks each, correctly long-tailed).

**Post-Q1 representable+predictable ceiling (derived directly from the
per-task rows, type-domain ⊆ the fixed 7 types AND families ⊆ the chosen
set):**

| Q1 scope | tasks / 427 | % |
|---|---|---|
| pre-Q1 floor (measured) | 147 | 34.4% |
| + 40%-mark families only (`bitwise_ops`, `math_native`) | 147 | 34.4% |
| **+ 55%-mark families (recommended)** | **190** | **44.5%** |
| + 70%-mark families (stretch) | 216 | 50.6% |
| + 70%-mark + `dict_methods`/`kwargs`/`floordiv_general` | 226 | 52.9% |

This is the **HQ1 bar** in `PROGRAM_SYNTHESIS_ARC2_PREREG.md` §3 — a
REPRESENTABILITY/PREDICTABILITY ceiling, not an accept-rate prediction (see
that document's §0 reconciliation with Q0-A's overfitting finding for why
the two are NOT the same number).

## 5. The joint ceiling — the arc's honest reachable denominator

**The Q1-scoped joint curve's 100% (355/425 = 83.5% of type-coverable
tasks, 355/427 = 83.1% of all 427) is the honest reachable denominator for
Q1 + the value-domain floor combined** — every task that does NOT need
regex, a same-corpus helper extern, complex numbers, or an unnamed
tail family. This is NOT a claim that all 355 will actually `pass` (search/
comprehension/repair still gate the SUFFICIENT condition — Q0-A's own
zero-shot measurement shows `accepted_holdout_fail` overfitting is a
LARGER blocker than value-domain representability under an impoverished
split); it is a claim about the ENGINE's representability ceiling, the
same status as P0/P2's "IR-representable vs ProgEval-predictable" split.

**Per-split notes (train vs test feature drift):**

| split | n | `ok` | `predictable` | type-coverable |
|---|---|---|---|---|
| fewshot | 7 | 42.9% | 0.0% | 100.0% |
| test | 257 | 72.8% | 37.7% | 99.6% |
| train | 120 | 75.0% | 28.3% | 100.0% |
| val | 43 | 83.7% | 37.2% | 97.7% |

No material drift between train and test at the structural-family level —
the top structural-family rankings are near-identical (`comprehension_
advanced`, `slicing`, `bitwise_ops`, `lambda`, `kwargs` dominate both, in
the same relative order) — a good sign for Q3's train-mined diet
transferring to the test distribution (fewshot's small n=7 is noisy and
not load-bearing for any bar).

## 6. Honest caveats

1. **Family groupings are an analyst's mapping, not measured Q1 behaviour**
   — only the CURRENT emitter's blockers/externs are measured; if Q1
   implements `bitwise_ops` WITHOUT the set-algebra half (§2's finding),
   realized coverage will be below this curve for the tasks that need
   both.
2. **Independent-parser divergence from Q0-A, by design, is informative,
   not a bug:** this parser recognizes `math.isclose` (13 tasks),
   `set(...)`-wrapper peeling, and raw `{...}` set literals as classifiable
   forms; Q0-A's `classify_assert` treats all three as named-unsupported.
   Cross-checked exact agreement on the RAW COUNT of `math.isclose` tasks
   (13, independently). This is why this document's non-type-coverable
   count (2/427) is far below Q0-A's test-split `assert_unparseable` count
   (17/257) — both are honest under their own declared scope; see
   `PROGRAM_SYNTHESIS_ARC2_PREREG.md` §0.
3. **`predictable` is a single boolean per task in the REAL emitter**
   (`extern_names ⊆ NATIVE_ORACLES AND NOT has_recv_call`) — this
   histogram's per-family modeling of "if Q1 added native support for
   family X, would this task become predictable" is a HYPOTHETICAL
   re-derivation from the per-task extern/recv lists, not a re-run of a
   modified engine. Actual Q1 numbers must be re-measured against the
   real, shipped implementation (HQ1's null-reading clause).
4. **Sub-construct feature counting is scoped to the entry function's own
   AST subtree**, matching `emit_prog_ir`'s own scope; a helper function's
   internal constructs (in the 12 multi-def tasks) are not separately
   counted here (they surface via the entry's `CallExtern` blocker
   instead, correctly).
5. **The three curves' floors are NOT the same population** — the
   value-domain curve's floor (150/425) excludes the 2 non-type-coverable
   tasks from its denominator entirely; the op/feature curve's floor
   (147/427) includes them (representability is independent of assert
   parseability). Always read a percentage with its stated denominator.
6. **Determinism:** two runs post every code change produced byte-identical
   JSON (`cmp` clean; final sha256
   `14d23d3356e75f46d3dc4d19cbe61343a90f4a968a4c09e68e4f8a6513330d32`).
