# PROGRAM VALUE DOMAIN, RATIONAL-FIRST — implementation + measurement

**Date:** 2026-08-01. Implements the arc-5 rung named by
`PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md` / `PROGRAM_SYNTHESIS_ARC5_SPECS_
IMPLY_FLOATS.md` / `PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md` /
`PROGRAM_SYNTHESIS_ARC5_FPGA_READINESS.md` / `PROGRAM_SYNTHESIS_P1_NOTES.md`
(read as a pointer to the arc-2 Q1 divergence ledger, `PROGRAM_SYNTHESIS_
ARC2_Q1_NOTES.md` §2 — the nine items) and CLAUDE.md's frame/continuum
invariant: **in-frame is integer/rational, never a float; non-integer
structure is CROSS-FRAME.** `Value::Float` is untouched globally — this is
not a float purge, it is a new exact numeric type for the PROGRAM domain
specifically, with the float boundary named at every point it's crossed.

## What landed

**`Value::Rational(i64, i64)`** (`runners/dsl/src/value.rs`) — a new,
always-reduced, always-positive-denominator variant of the shared `Value`
enum. Collapses to `Value::Int` when the reduced denominator is 1 (there is
no second representation of a whole number). Arithmetic helpers
(`rational_add`/`sub`/`mul`/`div`/`pow_int`) compute in i128 and return
`None` on overflow (bounded denominator, explicit signal, never a silent
wrap) — the two call sites differ in what they do with `None`:

- The **shared, non-fallible** `evaluate()` (`numeric_variadic`/
  `numeric_binary` behind `Plus`/`Times`/`Minus`, plus `Pow`/`Neg`/`Abs`)
  has no trap channel and degrades to `Value::Float` — still honest (a
  real, if imprecise, value), never silent corruption. These arms are
  **purely additive**: `Value::Rational` never existed before this work,
  so every pre-existing Int/Float/Bool code path through them is
  byte-identical.
- **`ProgEval`'s own local exact-division/exact-power interception**
  (`prog_eval.rs`) has a trap channel and uses it explicitly
  (`"arith:overflow"`) once it has committed to the exact path.

**`ProgEval` division is exact, locally — never touching the global `Div`
Term.** `Div` (Python's `/`) is used pervasively OUTSIDE program synthesis
(bigville `fin`/`fisc`/`coll`/`doctor`/`land`/`build`/`affect`/`infant`/
`life`, `convo_experiment`, `character_composition`, `lighting`, `style`,
`psychosis_grounding`, `render_python`, …) and is a documented, deliberate,
always-float true-division Term; changing its `(Int, Int)` behaviour
globally would be exactly the sweeping regression CLAUDE.md's "no
behaviour regression" and "do not remove `Value::Float` globally" guard
against. Instead, following the pre-existing `divmod`/floor-division
precedent ("LOCAL to the oracle, not global"), `ProgEval`'s `eval_expr`
intercepts `Div`/`Pow` itself:

- `eval_expr`'s dispatch was restructured: the documented "compositional
  core" (Plus/Times/Minus/Div/Mod/Pow/bitwise/compare/set-algebra/
  IndexAt/Append/Neg/Abs/Count/Last) now runs **unconditionally**
  (`is_compositional_op`), not only when the subtree contains a Prog*
  node. This is what lets a **plain, Prog-free** expression like
  `1/3 + 1/3 + 1/3` reach the exact path at all — the old
  `contains_prog`-gated fast path delegated such an expression WHOLE to
  the shared `evaluate()`, straight into the deliberately-untouched
  float-producing `Div`. Every op this widening reaches, other than the
  new `Div`/`Pow` exact cases, rebuilds Lit children in a scratch arena
  and delegates to `evaluate()` — value-identical to the pre-existing
  "mixed tree" path, so this is a safe structural widening (proven by the
  full Rust suite staying green, see below).
- `Div`: both operands exact (Int/Bool/Rational) and the divisor nonzero
  → exact rational quotient, trap on overflow. Otherwise (a Float operand,
  or a zero divisor) → rebuild + delegate, **byte-identical** to the
  pre-existing "no ZeroDivisionError, Div-by-zero → 0.0" divergence.
- `Pow`: restricted to a **genuine** `Value::Rational` base with an `Int`
  exponent (the pre-existing `(Int, Int)` `wrapping_pow` fast path is
  never touched, so its overflow-wraps-not-traps behaviour stays exactly
  as it was).

**Native-oracle boundary rendering** (`prog_eval.rs::call_native_oracle`,
`py_str`): `float(x)` on a Rational renders the double (the boundary,
verbatim); `str()`/f-strings spell a Rational exactly the way CPython
would spell the `/` result it stands in for (`py_float_str`, factored out
of the pre-existing Float arm); `int()` truncates toward zero;
`isinstance(x, "float")` matches a Rational too (a Rational IS a float
from Python's point of view — the value that would have been a genuine
`float` is represented exactly internally, but its Python-facing type
identity must still read `float`, or `isinstance(a / b, float)` would
wrongly flip to `False`, a real regression); `abs()`/`round()`/`sum()`
gained additive Rational arms (`sum` stays exact when every addend is
exact, matching `numeric_variadic`'s discipline).

**`SynthEnumerate`'s `canon()`** (`synth_enumerate.rs`) — THE explicit
boundary for the enumerator: a `Value::Rational` candidate result renders
to the SAME `SigVal::Num` shape as `Int`/`Float`, so the existing 1e-9
tolerance compare against a float-valued spec row applies unchanged (a
`SigVal::Other(canon_repr(..))` — exact string compare — would never match
a float target). `canon_repr`'s recursive repr gained a `Q<n>/<d>` arm for
completeness inside containers. The numeric-const filter used to build
`FilterList`/`MapList` templates now also recognises an explicit Rational
const.

**The wire tag** — `{"__rational__": [n, d]}` (`persist::encode_value`/
`decode_value`, reused by `jsonio.rs`'s `Lit` reader/writer and therefore
by `add_term_subgraph`/`term_subgraph_json`/`Substrate.evaluate`). Same
tagged-dict convention as `__nid__`/`__tuple__`/`__set__`/`__dict__`.

**`domains/prog_exact.py::_render_pow_product`** — the geometry family's
fitted `k` (`4/3`, `1/3`, `1/180`, …) now renders as a **single exact
rational Lit** (`{"type": "Lit", "value": {"__rational__": [k_num,
k_den]}}`) instead of `Div(Lit(k_num), Lit(k_den))`. The old rendering
LOOKED exact (two integer Lits) but collapsed to float the moment it was
evaluated (`Div` is always-float); the new rendering carries `k` as an
exact rational all the way through the `Times` it feeds (Rational-aware
via `numeric_variadic`), so the fitted parameter never touches a float
anywhere in the tree, literally, not just syntactically.

**Python-side Fraction bridging** (`py.rs`): `value_to_py` renders
`Value::Rational` as a `fractions.Fraction` (the natural exact Python
type — arithmetic/comparisons against int/float both work out of the
box); `py_to_value` recognises a `Fraction` (checked by class name BEFORE
the `f64` extraction attempt, since PyO3's f64 `FromPyObject` falls back
to `__float__` and would otherwise silently collapse it). `substrate/
dsl.py`'s `Lit` dataclass gained a doc note — no code change needed there:
Python's own `+`/`-`/`*`/`/` on a `Fraction` are already exact.

## Exactness gate — measured

```
1/3 + 1/3 + 1/3 == 1                      # exactly, via ProgEval, Prog-free expression
0.1 + 0.2 != 0.3                          # the float control this whole rung routes around
Div(1, 4) -> Fraction(1, 4)               # ProgEval: division of integers yields a rational
(1/2) - (1/3) -> Fraction(1, 6)           # exact
(2/3) * (3/4) -> Fraction(1, 2)           # exact
(1/2) ** 2   -> Fraction(1, 4)            # exact rational power
(1/3) ** 40                               # overflows i64 -> traps "arith:overflow", never wraps
Div(1, 0) -> 0.0 (float)                  # UNCHANGED documented divergence (not exact-eligible)
volume_sphere k=4/3, exponent 3           # renders as ONE rational Lit, evaluates to 3 exactly for r=3
```

All of the above are gated live in `tests/test_rational_domain_migrated.py`
(32 tests) and the additive spot-checks in `tests/test_value_domain_
migrated.py` (3 new tests: dict-iteration-order unaffected by a Rational
VALUE, `sorted()` agreement across Int/Float/Rational, purity).

## Divergence-ledger delta — the headline, honestly

The nine items are `PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md` §2 (the arc-2 Q1
phase that widened `ProgEval`/`SynthEnumerate` from the arc-1 int/int-list
floor to the FULL Q0 op/type set: str/bool/float/none/dict/set/tuple +
generic builtins, all in ONE commit). `PROGRAM_SYNTHESIS_ARC5_FLOAT_
NECESSITY.md` frames that whole ledger as the price "paid for float
support" — re-reading the nine items individually against that framing is
itself a finding:

| # | item | verdict under this rung |
|---|---|---|
| 1 | `round()` banker's rounding vs CPython's correctly-rounded-decimal `round()` | **REMAINS, reduced trigger surface.** Genuine cross-frame floats (`sqrt`, `pi`, a DTW/ShapeContext metric) still exist and still need `round()` — this divergence cannot be eliminated while `Value::Float` legitimately exists (and per CLAUDE.md it must). What changed: exact division/multiplication no longer MANUFACTURES a float that then needs rounding (`round(1/3+1/3+1/3)` rounds an exact `Int`, never touching the float path at all). Gated: `test_ledger_item_1_round_banker_rounding_reduced_surface_not_eliminated`. |
| 2 | `divmod`/floor division LOCAL to the oracle, not global | **UNAFFECTED — orthogonal.** This is about `//`/`divmod` floor-vs-truncate semantics, unrelated to `/` true-division exactness. Untouched by this rung. |
| 3 | `isinstance` has no first-class type object | **UNAFFECTED — orthogonal.** The type-name-string convention is unchanged; this rung only ADDS Rational to the existing `"float"` string case (necessary — see boundary rendering above), it doesn't touch the underlying limitation. |
| 4 | `map`/`next`/`iter` refused, not approximated | **UNAFFECTED — orthogonal.** No first-class callable/lazy iterator exists in this rung either; unrelated to numerics. |
| 5 | Mutating recv-form calls not landed | **UNAFFECTED — orthogonal.** `ProgCallExtern` still has no lvalue write-back path; unrelated to numerics. |
| 6 | `SynthEnumerate.inadmissible` structurally unreachable | **UNAFFECTED — orthogonal.** Rational is one more always-representable type; doesn't reintroduce inadmissibility. |
| 7 | Dict iteration order: `cmp_value`-sorted by key, Str keys by interned-symbol id | **UNAFFECTED — orthogonal, and verified.** Sorting is by KEY; a Rational VALUE doesn't perturb it (gated: `test_dict_iteration_order_unaffected_by_rational_valued_entries`). |
| 8 | `str.split()`/`str.strip()` Unicode vs CPython ASCII-plus-extras whitespace | **UNAFFECTED — orthogonal.** Unrelated to numerics. |
| 9 | String `Lit` repr single-quote convention (`SynthEnumerate::lit_repr`) | **UNAFFECTED — orthogonal.** Unrelated to numerics. |

**The honest headline: of the nine, zero are structurally eliminated by
this rung, because eight of them were never about float precision in the
first place** — they are the REST of the Q1 value-domain widening (str/
dict/mutation/iteration/callable semantics) that the "paid for float
support" framing folded in under one banner. Only item 1 is even
numerically adjacent, and it persists because `Value::Float` legitimately
still exists at the cross-frame boundary (sqrt/pi/verdict metrics) — this
rung reduces how often a REAL MBPP-shaped program exercises that
divergence (exact arithmetic no longer manufactures floats that need
rounding), which is a real, measured, but frequency-shaped improvement,
not a ledger-line removal. Reporting a false "N eliminated" here would be
exactly the kind of "curve-fitting the ledger to look smaller" this
project's own honesty discipline (CLAUDE.md's retracted-baseline history)
exists to prevent.

## No-regression evidence

- **Rust:** `cargo test --release --lib` — **702 passed, 0 failed, 4
  ignored** (up from the pre-rung baseline; includes 8 new `value::tests`
  rational-law tests). One transient failure
  (`shape_decode::dim_infer_tests::d_sweep_distinct_tracks_its_axis`) was
  observed once under `--test-threads` default parallelism and reproduced
  as PASS in isolation and on a clean re-run of the full suite — a
  pre-existing test-order flake in an unrelated module (`shape_decode.rs`,
  never touched by this rung), not a regression from this work.
- **Python, this rung's own suites:** `tests/test_rational_domain_
  migrated.py` (32/32), `tests/test_value_domain_migrated.py` (86/86, 3
  new), `tests/test_prog_ir_migrated.py` (unchanged, still green),
  `tests/test_synth_enumerate_migrated.py` (unchanged, still green) — 201
  total across the four files in one run, 0 failures.
- **`tests/test_exact_first_migrated.py`** (the 6 geometry conversions):
  18/20 green. The 2 red (`test_program_synthesis_seed_bumped_with_
  three_new_rules`, `test_named_regression_sweep_only_known_pins_drift`)
  are **not caused by this rung** — `git status` shows `seeds/
  program_synthesis.json` / `domains/prog_synthesis.py` modified and a
  new `domains/prog_moves.py` present, all **uncommitted, concurrent work
  by the sibling agent explicitly named out of this task's scope** (this
  task was told not to touch those files). Direct confirmation:
  `test_program_synthesis_seed_bumped_with_three_new_rules` asserts
  `d["version"] == "1.9.0"`; the file on disk is version `1.10.0` — a
  sibling-side version bump, nothing to do with rationals. The broader
  regression-sweep subprocess this test spawns surfaced a shifting set of
  ~14-17 failures across `test_arc4_endgame_migrated.py`/`test_descent_
  widening_migrated.py`/`test_mbpp_*_migrated.py`/`test_search_reach_
  migrated.py`/`test_budget_isolation_migrated.py`/`test_verdict_
  discrimination_migrated.py`/`test_retrieval_migrated.py`/`test_prog_
  synthesis_battery_migrated.py` — direct inspection of one
  (`test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct`)
  shows the construction dispatcher now returning `"sum_of_two"` where it
  expected `"range_sum_spine"`, a construction-selection change entirely
  inside `domains/prog_synthesis.py`/`seeds/program_synthesis.json`
  (files this task does not touch and the sibling is actively editing);
  the failing SET itself changed between two runs of the identical
  command a few minutes apart, consistent with a live, in-progress edit
  rather than a stable regression. None of these files import or exercise
  `runners/dsl/src/{value,term,prog_eval,synth_enumerate,persist,py,
  graph_rules,memory,graph}.rs` in a way this rung's changes could
  plausibly affect (construction/trigger dispatch, not arithmetic).
- **Global `Div`/`Mod`/`IDiv`/`IRem` Terms**: untouched line-for-line
  except `Div`'s doc comment; `test_plain_float_arithmetic_byte_identical`
  and `test_global_div_is_untouched_outside_progeval` pin `Div(1,3)` via
  the plain (non-ProgEval) evaluator still returns a float, exactly as
  before this rung existed.
- **`(Int, Int)` `Pow` overflow** still wraps (`wrapping_pow`, untouched);
  pinned by `test_int_pow_overflow_still_wraps_the_pre_existing_behaviour`.

## What stayed float, and why

- **Named cross-frame constants** (π, √2, √3, …) — `domains/prog_exact.py`
  applies these as their pre-computed `f64` at the render boundary,
  exactly as before; never a fitted parameter.
- **`math.sqrt`/`math.pow`/`math.floor`/`math.ceil`/`math.trunc`** and the
  `Sqrt`/`Log`/`Exp` DSL Terms — genuine cross-frame maps (irrational in
  general); untouched.
- **The verdict-layer metrics** (`DtwTo`/`PointSetDist`/`ShapeContextDist`/
  `TpsDeformDist`/`XCorrPeak`) — class-A cross-frame comparators, not
  touched at all by this rung (no `Value::Rational` arm was added to any
  of their internals; they only ever see the ambient `Value::Float`/
  `Value::Tuple` they always saw).
- **`float()`, `str()`, JSON serialisation (`ToJsonString`/`json.dumps`),
  `round()`'s output** — the documented boundary: a rational renders to a
  double at exactly these points, on purpose.
- **Division/exponentiation with a Float operand present, or a zero
  divisor, or a non-integer exponent** — the exact path is skipped by
  construction; these fall through to the pre-existing float-producing
  code, unchanged.

## Files touched

- `runners/dsl/src/value.rs` — `Value::Rational`, `PartialEq`/`cmp_value`/
  `Hash`/`truthy`/`as_f64`/`as_i64` arms, `make_rational`/`rational_parts`/
  `rational_add`/`sub`/`mul`/`div`/`pow_int`, 8 new unit tests.
- `runners/dsl/src/term.rs` — additive Rational arms in `numeric_variadic`
  (Plus/Times)/`numeric_binary` (Minus)/`Pow`/`Neg`/`Abs`; `Div` doc
  comment only (behaviour untouched); `value_to_json_for_string`'s
  boundary arm.
- `runners/dsl/src/prog_eval.rs` — `is_compositional_op` +
  unconditional-compositional-core restructure; local exact `Div`/`Pow`
  interception with `"arith:overflow"` trap-on-commit; `value_kind`/
  `py_str`(+`py_float_str`)/`abs`/`sum`/`int`/`float`/`round`/`isinstance`
  oracle updates.
- `runners/dsl/src/synth_enumerate.rs` — `canon`/`canon_repr` Rational
  arms (the boundary); numeric-const filter widened.
- `runners/dsl/src/persist.rs` — `{"__rational__": [n, d]}` wire tag
  (`encode_value`/`decode_value`).
- `runners/dsl/src/py.rs` — `value_to_py`/`py_to_value` Fraction bridging.
- `runners/dsl/src/graph_rules.rs`, `runners/dsl/src/memory.rs`,
  `runners/dsl/src/graph.rs` — exhaustiveness-only arms (Rule-attr JSON
  reader treats Rational like Node/Surface — not a Term-JSON shape here;
  byte-size estimator; `#[cfg(test)]` diagnostic dump).
- `substrate/dsl.py` — `Lit` doc note (no behavioural change; Python's
  own Fraction arithmetic is already exact).
- `domains/prog_exact.py` — `_render_pow_product` renders `k` as an exact
  rational Lit instead of `Div(int, int)`.
- NEW `tests/test_rational_domain_migrated.py` (32 tests).
- `tests/test_value_domain_migrated.py` — 3 new additive tests (§9b).
- `tests/test_exact_first_migrated.py` — one existing assertion
  (`test_recovered_parameters_are_integers_only_the_named_constant_is_
  float`) taught to recognise the new `{"__rational__": [n, d]}` Lit
  shape as exact (not a regression in what it checks — the same "no
  float except the named constant" invariant, now honestly stronger).
- NEW `PROGRAM_SYNTHESIS_ARC5_RATIONAL.md` (this file).

**No new `TermNode` variant was needed** — `Value::Rational` rides on the
existing generic `Lit` node, so `runners/dsl/src/term_variants.rs` (the
207-entry scale-audit table) is untouched.

## Residuals (named, not silently assumed solved)

- `Mod`/`IDiv`/`IRem` were left untouched beyond gaining correct
  `as_i64()` coercion for Rational (truncating, matching how they already
  treat Float) — Python's bare `//` isn't even emitted by the frozen
  emitter (`OpExt:FloorDiv`, out of this rung's file-ownership scope
  regardless), and `%`/`//` were never claimed exact for floats either;
  extending exactness there wasn't in scope and wasn't measured as needed.
- `round(fraction, ndigits)` (the 2-arg form on a genuine Rational)
  renders to float rather than a fraction-precision rational round —
  Python's real 2-arg `round()` on a `Fraction` returns a `Fraction`; this
  engine has no fraction-precision-rounding primitive, so it honestly
  degrades to float instead of approximating. Named, not implemented —
  no measured MBPP task needs it.
- `SynthEnumerate`'s own auto-generated constant pool (the `(0,1,2,-1)` +
  integer-valued-output derivation) was ALREADY float-free before this
  rung (verified, not changed) — the geometry family's non-integer `k` is
  recovered by `domains/prog_exact.py`'s dedicated fit, not by the
  generic enumerator; this rung's contribution there is accepting an
  explicit Rational const if a caller supplies one, and rendering any
  Rational candidate result correctly at the `canon()` boundary.
