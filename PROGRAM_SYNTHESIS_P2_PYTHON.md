# PROGRAM SYNTHESIS P2 — Python frame → hub IR (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P2,
`PROGRAM_SYNTHESIS_PREREG.md` §4, `PROGRAM_SYNTHESIS_P1_NOTES.md` (the
variant set + ProgEval trap/oracle model this emission targets), and
`results/prog_ir_python_coverage.json` (the enumerated coverage artifact).

## 1. What landed

A NEW, ADDITIVE emission path — `domains/prog_ir_emit.py` —
`emit_prog_ir(source | ast.FunctionDef)` and
`emit_prog_ir_from_graph(container, AstNode-root)` → hub Program-IR
Term-JSON over the FULL P1 variant set (the P0 at_80 21 + the registered
While/Raise deviation, all 23 `Prog*` statement variants), with pure
expressions emitted as ordinary DSL Terms (Plus/Minus/Times/Div/Mod/Pow/
Neg/Not/Eq/Lt/Lte/Gt/Gte/In/IfThenElse — the `ast_to_term` /
`ast_term_rules` CORRESPONDENCE reused at expression grain).

Honesty contract: `{ok: True, ir, externs, predictable, variants, params}`
with the WHOLE function represented, or `{ok: False, blockers: [...]}` with
EVERY out-of-scope feature named (the walk continues past a blocked
construct so the blocker list is complete). Never a partial silent emit.

Design choice, recorded per the task card: this is a **fixed
correspondence walk in Python** (mechanical translation, the
`ast_to_term.ingest_ast` precedent — admissible adapter work; one walker
over an accessor abstraction with an ast backend and an AstNode-graph
backend). The **rule-based bottom-up fold** — extending
`ast_term_rules.CORRESPONDENCE` + `statement_rules()` to statement grain so
the Rust engine performs this fold at `run_rules` fixpoint — is the
**recorded future migration** (the payoff is self-repairability:
"self-repair ⟺ graph-native"). It was not blocked on here; the emission
dialect (field names, explicit-null optionals, list fields) is exactly the
P1 reflect dialect, so the future rule fold has a byte-level target.

## 2. Semantics-pinned mapping decisions (all MEASURED on the P1 engine)

Every decision below was probed against the installed
`runners/dsl/python/substrate_rs/_native.abi3.so` before the mapping was
written; each avoids a silent-wrong emit.

| construct | measured engine fact | mapping |
|---|---|---|
| `a and b` / `a or b` | DSL And/Or return BOOLS (`Or[0,'x']` → True) | right-nested `IfThenElse` OPERAND desugar (`a or b` ≡ `a if a else b`) — the `boolop_rules` precedent; faithful in value position (`name or "anon"` gate-verified) |
| truthiness | IfThenElse cond: 0/""/None/[] falsy, 2/'x' truthy (Python-like) | `IfExp`/BoolOp desugars are faithful |
| `a / b` | `Div(17,2)` → 8.5 (TRUE division) | `/` → Div |
| `a // b` | native aug `floordiv` is TRUNC (−7//2 → −3); DSL `Mod` is Python-exact for POSITIVE divisors only (`Mod(7,-2)` → 1 ≠ −1) | composite statement-lift `__uN = a − (a % b); __uN //= b` (trunc of an exact multiple IS floor) — **CPython-exact incl. negative dividends**, guarded: positive literal divisor, Prog-free operands, statement-value/If-test position (see §5 for the conditional-branch soundness argument). Else honest `OpExt:FloorDiv`. The frozen emitter's FloorDiv→Div fold is refused, not repeated |
| `"a" + b`, `s * 2` | `Plus('a','b')` → 0 (DSL arithmetic is numeric) | statically-string operand → blocker `StrArithStatic`; unknown-typed operands emit Plus/Times under the REGISTERED P1 convention (DSL arithmetic governs expressions) |
| `x in "literal"` | `In('a','cat')` → False (collection membership, not substring) | statically-string container → blocker `InStrStatic`; runtime-typed containers emit `In` (same registered convention class) |
| `except ValueError` | ProgTryOr catches ANY trap (strings, no type dispatch) | only bare/`Exception`/`BaseException` handlers emit; narrower types → `TypedExcept` (semantics preserved, never widened). Multi-handler/else/finally → blockers |
| `raise X("m")` | constructor is an extern; undeclared externs trap `extern:X` | mechanical `ProgRaise{exc: ProgCallExtern}` — surfaces as an `extern:` trap rather than `raise:`; still a trap, still catchable, never a value (documented spelling divergence, gate-verified both branches) |
| expression statements | a bare Term in `ProgSeq.stmts` is evaluated and discarded (probed) | `Expr` statements emit as bare terms |
| `a = b = e` | value semantics, no aliasing | desugar `a = e; b = a` (all-plain-Name only; else `MultiTargetAssign`) |
| `for k, v in xs:` | — | synthetic `__uN` + `ProgTupleUnpack` prelude in the loop body (flat all-Name targets only) |
| `o.a += v`, `d[k] += v` | expressions are pure except externs | read-modify-write desugar, guarded extern-free target subtrees (`AugAssignImpureTarget` otherwise) |
| `ProgCallExtern` name | dotted names trap verbatim (`extern:math.sqrt`, probed) | Name → verbatim; Attribute chain over a Name → DOTTED verbatim; computed receiver → `recv`-form (`name="bit_length"`, recv=IR) |

`NATIVE_ORACLES` (len/abs/min/max/range/sum/str/int/float/bool/sorted) is
exported from the module so coverage computes the predictable subset from
the same table P1 shipped.

## 3. Measured coverage (the headline numbers, with their conditions)

Artifact: `results/prog_ir_python_coverage.json` — every total derived from
an identity list. Scope A is the frozen-baseline scan scope (sorted `*.py`
under `domains/`, TOP-LEVEL `ast.FunctionDef` only — `scan_repo_functions`'
enumeration reproduced); scope B is the P0 histogram's own scope
(`domains/` + `substrate/`, methods + nested + async included). Measured at
this tree state (n drifts with the live tree — two other agents were
editing `domains/` during this phase; the artifact records its own n).

| scope | n | **IR-representable** (emit ok) | **ProgEval-predictable** (no undeclared externs) | histogram-predicted (req ⊆ P1 set) |
|---|---|---|---|---|
| A: domains/ top-level | 7262 | **4099 (56.4%)** | **665 (9.2%; 16.2% of representable)** | 6047 (83.3%) |
| B: histogram full | 9685 | **5619 (58.0%)** | **928 (9.6%)** | 8127 (83.9%) |

- The plan-quoted "~80.5%" was the greedy-curve at_80 read on the P0
  corpus (9522 fns). Recomputed from the histogram's own per-function
  `analyse()` (imported, not reimplemented) for the exact P1 set (at_80 +
  While + Raise) on today's tree: 83.3% / 83.9% per scope above — that is
  the like-for-like prediction the measurement is compared against.
- **Emitted ∧ ¬predicted = 0** (both scopes): the emitter is strictly
  STRICTER than the histogram's model, never looser.
- The representable-vs-predictable split is the honest two-number report:
  representability is the IR claim; predictability (every extern in the P1
  native-oracle set, no recv-form call) is the ProgEval-oracle claim. The
  9-point predictable number is dominated by real code calling repo
  functions and methods — exactly the CallExtern knowledge wall CODE-2/P1
  already drew, now enumerated per function.
- **Growth against the frozen baseline: 27 → 4099 identities** on the
  baseline scope (the P0 term-emittable list was 27; the diff is readable
  from the two artifacts' id lists).

### The measured-vs-predicted gap (prereg §4 null-reading path, taken)

Coverage is BELOW the histogram target with the variant set exhausted, and
per the prereg the correct output is the gap-mass breakdown, not new
unjustified variants. The histogram under-modeled real bodies exactly as
§4 anticipated ("e.g. Call-extern density") — its `analyse()` counted a
function representable when its STATEMENT/EXPRESSION KINDS were in-set,
but did not model these sub-construct facts (blocker mass over the 1948
predicted-but-not-emitted functions, scope A):

| blocker | mass | why it blocks (honest reason) |
|---|---|---|
| `KwargsCall` | 1173 | `ProgCallExtern` has no keyword-argument channel; a dropped kwarg is a wrong call |
| `SliceSubscript` | 524 | no slice form in the P1 IR (`ProgSubscript.index` is a value) |
| `CompTargetComplex` | 136 | comprehension loop var is a single name in the IR |
| `StrArithStatic` | 130 | DSL Plus/Times numeric (measured §2) |
| `TypedExcept` | 102 | ProgTryOr catches any trap; narrowing dropped silently would widen semantics |
| `FStringConversion` | 93 | `!r/!s/!a` has no IR carrier; py_str spelling would silently differ |
| `StarArgsParam` | 74 | `*args/**kwargs` collect-semantics not expressible in ProgDefFnParam |
| `NestedUnpack` | 70 | nested/attribute unpack targets |
| `OpExt:FloorDiv` | 43 | outside the exact-lift guard (non-literal/negative divisor, extern operands, While tests) |
| `CompMultiClause`/`DictUnpack`/`FStringFormatSpec`/`InStrStatic`/`StarArgsCall`/… | ≤30 each | tail; full ranking in the artifact |

These are P3+ facts, not P2 failures: each row is either a candidate for a
future P1-governor-approved IR extension (kwargs and slices carry by far
the most mass) or a permanent honest residual (StrArithStatic, TypedExcept).

## 4. Gates (all green at this commit)

`tests/test_prog_read_python_migrated.py` — **52 passed** (0.14s; well
under the 90s budget; run with `--confcutdir=.` per the P1 worktree-engine
note):

- **Semantic:** 15 fixture runs (13 fixtures × input variants,
  `tests/fixtures/prog_ir_read/`) — emit → ProgEval vs CPython exec of the
  SAME source, RESULT + ENV agreement (CPython locals captured at return
  via a mechanical tracer; module-typed locals excluded; `import_noop`
  pins its own key list). Fixture battery spans if/elif/else, boolean
  operand semantics, for/break/continue/for-else, while, tuple unpack,
  try/raise (both branches), subscripts read/write, comprehensions,
  f-strings, is/is-not, defaults-bind-vs-env-wins, records (dict-record
  convention vs a CPython object twin), floordiv lift incl. negative
  dividends and the conditional-branch position.
- **Honest trap:** undeclared extern → `extern:helper_quantity`,
  halted False, result None, no partial env write; dotted name verbatim
  (`extern:math.sqrt`); `predictable: False` on both.
- **Honest residual:** out-of-set fixture → `{ok: False, blockers:
  ["Assert", "Delete", "Lambda", "With"]}` exactly, no `ir` key; plus the
  expression-grain refusals (`OpExt:FloorDiv` outside the guard,
  `StrArithStatic`, `SliceSubscript`).
- **Reflect round-trip:** every ok fixture's emitted IR →
  `add_term_subgraph` → `term_subgraph_json` → canonically identical +
  idempotent (the P1 law applied to EMITTED trees).
- **Determinism:** emit twice → byte-identical JSON, all fixtures.
- **Variant span:** the ok fixtures jointly exercise ALL 23 P1 variants
  (asserted against `P1_VARIANT_SET`), and the IR type closure is exactly
  {Prog* ∪ the documented DSL expression set} — nothing smuggled.
- **Graph mode:** byte-identical IR to the ast entry on 4 fixtures;
  honest `GraphRepr:fstring_conversion` refusal where `ingest_ast`'s
  representation cannot carry the conversion flag.

## 5. The frozen-27 subset check — and the one mechanism it forced

Prereg §4 registered: the 27 survive as a subset. First measurement said
**NO — 4 exits, all `OpExt:FloorDiv`** (`capability_compose._sum_first_n`,
`_sum_first_n_squares`, `_sum_first_n_cubes`;
`scattering_feature._descr_len_1d`): the old emitter had them only via its
FloorDiv→Div approximation, which this path refuses. Rather than file a
named regression, floor division was made EXACT:

- native aug `floordiv` is trunc-division (measured −7//2 → −3 ≠ −4) —
  P1's fixture corpus only exercised positive operands, so this is a
  **P1 residual recorded here**: bare `x //= k` in ProgEval diverges from
  CPython for mixed-sign operands;
- the composite `__u = a − (a % b); __u //= b` is exact for every int
  dividend when the divisor is positive (trunc of an exact multiple is
  floor; DSL Mod measured Python-exact for positive divisors);
- lifting the prelude out of a conditionally-evaluated position
  (`(J*(J−1))//2 if order2 else 0` — the `_descr_len_1d` shape) is sound
  because the guard admits only Prog-free pure arithmetic and the engine's
  arithmetic NEVER traps (measured: aug-floordiv on None/str/tuple yields
  0, no trap) — a discarded pre-evaluation is observationally invisible;
  While tests (per-iteration staleness) and comprehension subtrees
  (loop-var capture) stay disarmed.

Final artifact: `frozen_27_subset_check.all_present = true, missing = []`.

C-FIXTURE note: the old-path measurement corpus is untouched (this phase
changed no old-path file), so no re-freeze is required; the prereg's
`loopy` criterion is delivered on the NEW path — `loopy` emits AND is
ProgEval-predictable (as are `add`/`is_positive`).

## 6. Old path byte-identical — proof

- **No shared file was modified.** This phase added only:
  `domains/prog_ir_emit.py`, `scripts/prog_ir_coverage_measure.py`,
  `tests/test_prog_read_python_migrated.py`, `tests/fixtures/prog_ir_read/`
  (13 files), `results/prog_ir_python_coverage.json`, and this document.
  `domains/ast_to_term.py`, `domains/ast_term_rules.py`,
  `domains/code_reading.py` are byte-untouched (the new module imports
  `_ast_node_type` read-only).
- **`tests/test_code_synthesis_baseline_migrated.py` green BEFORE (11/11)
  and AFTER (11/11)** on the same worktree engine, plus the P1 gate
  (`test_prog_ir_migrated.py`, 54/54) alongside: 117/117 across the three
  suites at the final state.

## 7. Honest caveats and open residuals

1. **Synthetic env names.** Loop-target and floordiv desugars introduce
   `__uN` variables into `env_out` (CPython-key-only comparison in the
   gate; renderers/round-trips must treat `__u*` as emitter-owned).
2. **Runtime-typed string arithmetic.** Only STATICALLY-visible string
   operands block; a string arriving at `+`/`in` through a variable hits
   the registered P1 DSL-arithmetic convention (numeric semantics, e.g. 0)
   — same class as Div-by-zero → 0.0. Prediction-grade string handling is
   extern/oracle territory (P3+).
3. **Raise spelling.** `raise X(...)` traps as `extern:X`, not
   `raise:<msg>` (constructor is an undeclared extern). Catchability and
   halted-honesty preserved; trap STRING differs from hand-built P1 IR.
4. **Graph-mode representation gaps.** `ingest_ast` does not carry
   f-string conversion flags (`GraphRepr:fstring_conversion` refusal),
   `from X import` module names (`GraphRepr:importfrom_module` refusal),
   `import x as y` asnames (carried as absent — ImportStmt is a ProgEval
   no-op), or comprehension `is_async` (undetectable there; ast entry
   detects and blocks). The ast entry is the coverage instrument.
5. **Float floordiv.** The exact-lift returns int-typed values;
   a FLOAT dividend yields a value-equal int (−7.0//2 → −4 vs −4.0).
6. **ImportFrom multi-alias `as`** blocks (`ImportAsName`) rather than
   invent a names-encoding; single-alias `as` carries via `alias`.
7. **Corpus drift.** Scope-A n (7262) ≠ frozen-baseline n (7177): the tree
   grew since P0 and two sibling agents were editing `domains/` during the
   measurement; the artifact is a snapshot of its own recorded n, and the
   27-identity check matches on (file, qualname) so it is drift-robust.
8. **P1 residual found en route** (recorded in §5): ProgEval's bare
   aug-`floordiv` is trunc-division on mixed signs; DSL `Mod` diverges from
   CPython for negative divisors. Neither is exercised by the P1 fixture
   corpus; both are now pinned by this phase's probes and worked around in
   emission. Worth a P1-side fixture when the Rust tree is next open.
