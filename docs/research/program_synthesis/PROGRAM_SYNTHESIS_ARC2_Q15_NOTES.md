# PROGRAM SYNTHESIS ARC 2 Q1.5 — TEACHING THE EMITTER THE Q1 SHAPES, AND THE REAL HQ1 VERDICT

**Date:** 2026-08-01
**Scope:** the emitter-widening residual Q1 named but could not close under its
own file-ownership boundary (`domains/prog_ir_emit.py` was explicitly
out-of-scope for Q1 — PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md §5/§7). Q1.5 teaches
the Python reader/emitter the IR shapes the Q1 Rust engine now speaks, and
delivers the REAL (not hypothetical, not frozen-artifact) HQ1 verdict.
**Files touched:** `domains/prog_ir_emit.py` (additive widening),
`tests/test_prog_read_python_migrated.py` (additive + two NECESSARY
corrections, named below), `tests/test_value_domain_migrated.py` (docstring/
comment correction only — no assertion changed), NEW
`tests/test_emitter_widening_migrated.py`, `scripts/prog_ir_coverage_measure.py`
(additive `--append-q15` mode), `results/prog_ir_python_coverage.json`
(appended `q15_post_widening` block, the frozen P2 keys byte-unchanged), this
file. Under a mid-task ownership grant from the coordinator (Q2's sibling
finding): `tests/test_mbpp_histogram_migrated.py` and
`tests/test_mbpp_baseline_migrated.py` (reconciliation only — two live-vs-
frozen legs updated toward MORE coverage / converted to frozen-row-only
assertions, dated 2026-08-01; the frozen artifacts
`results/mbpp_blocker_histogram.json` / `results/mbpp_zero_shot_baseline.json`
are byte-unchanged, verified by hash).

---

## 1. What landed, by shape

| Shape | Status | Where in `prog_ir_emit.py` | Notes |
|---|---|---|---|
| **Slicing (read)** `x[a:b:c]` | LANDED | `_emit_slice`, wired from `emit_expr`'s `Subscript` branch | str AND list; each of start/stop/step emitted when present, `None` when absent — the same optional-child convention every other `Prog*` node uses |
| **Slicing (write)** `x[a:b] = v` | STILL BLOCKED (by design) | `_assign_target`'s `Subscript` branch, unchanged | no engine write-back path for a slice target — `SliceSubscript`, same reasoning as mutating recv calls |
| **Bitwise `&`/`\|`/`^`** (int AND set) | LANDED | `_BINOP_AB` (3 new entries) | plain DSL `BitAnd`/`BitOr`/`BitXor` Terms, type-blind emission — dispatch (int vs Set) is the engine's runtime concern |
| **`<<`/`>>`** | STILL BLOCKED (by design) | unchanged | Q1 only landed set-algebra reach for `&`/`\|`/`^`; `OpExt:LShift`/`OpExt:RShift` deliberately out of this widening's scope |
| **Method-oracle recv form** (`word.split()`, `d.get(k)`, ...) | LANDED, AND THE HEADLINE FIX | `_emit_call`, method-NAME-first recognition | see §2 — this is the change that actually reaches real code |
| **Mutating recv methods** (`append`/`sort`/`add`/`setdefault`/...) | HONEST BLOCKER (new) | `_RECV_BLOCKED_METHODS`, `_emit_call` | `RecvMethod:<name>`, emission-time, not emit-and-trap — verified to align with the engine's own `extern:unimplemented:<name>` refusal |
| **Any other method name** (`self.foo()`, `s.zfill()`, `m.group()`) | UNCHANGED (by design) | the pre-Q1.5 `_dotted_name` fallback | zero reclassification risk — this widening never touches a call it wasn't asked to fix |
| **`isinstance(x, T)`** | LANDED | `_emit_isinstance_call` | bare `Name` second arg -> `Lit(name)` (the engine's type-name-string convention, Q1 notes §2 item 3); tuple-of-types -> `IsinstanceMultiType`; anything else -> `IsinstanceComplexType` |
| **`list`/`tuple`/`set`/`frozenset`/`dict`/`all`/`any`/`enumerate`/`zip`/`reversed`/`round`/`pow`/`divmod`/`ord`/`chr`/`math.sqrt`/`math.floor`/`math.ceil`/`math.pow`/`math.trunc`** | LANDED (metadata only) | `NATIVE_ORACLES` widened | zero emission-shape change — these already emitted as ordinary Name-form/dotted calls; only the `predictable` classification moves |
| **str/float/None/bool/dict/set/tuple literals, container ctors (literal syntax)** | ALREADY LANDED (pre-Q1.5) | unchanged | `Constant`/`List`/`Tuple`/`Set`/`Dict` handling already existed from P2 — the Q1 "value domain LANDED" note was about evaluator/enumerator reach, not the emitter |
| kwargs / star-args / lambda | STILL BLOCKED (by design) | unchanged | `KwargsCall`/`StarArgsCall`/`StarArgsParam`/`Lambda` |
| `OpExt:FloorDiv` outside the exact-lift guard | STILL BLOCKED (by design) | unchanged | not in this phase's scope (`floordiv_general`, Q1 notes' own residual) |
| `TypedExcept`, comprehension-advanced forms, `map`/`next`/`iter` | STILL BLOCKED / REFUSED (by design) | unchanged | out of scope; `map`/`next`/`iter` are the engine's own honest refusals (no first-class callable/iterator) |

## 2. The headline fix: method recognition by NAME, not by receiver shape

The pre-Q1.5 `_dotted_name` walk resolves ANY Attribute chain rooted at a
bare `Name` as a "dotted extern" — this is correct for `math.sqrt(x)` but
means `word.split()` (receiver `word` is a plain local variable, not a
module) was ALSO being treated as a dotted Name-form call (`extern name
"word.split"`), never reaching the recv-form path at all. `_dotted_name` has
no symbol table — it cannot tell a local variable from a module apart, and
the overwhelming majority of MBPP receivers are local variables, not
modules. Simply widening `NATIVE_RECV_ORACLES` would therefore have been
**nearly vacuous** on real code.

The fix (`_emit_call`): recognise a recv-form call by the **method name
first** — if the attribute name is in `NATIVE_RECV_ORACLES` (the Q1
string/dict oracle set) or `_RECV_BLOCKED_METHODS` (known mutating
collection/dict methods), the call is ALWAYS resolved as recv-form,
regardless of whether the receiver is a bare Name or a computed expression.
Any OTHER method name keeps the ORIGINAL dotted-vs-recv resolution
byte-unchanged. This is deliberately asymmetric and low-risk:

- `word.split()`, `d.get(k)`, `sep.join(xs)` -> now correctly recv-form,
  predictable.
- `xs.append(v)`, `d.setdefault(k, v)` -> now correctly recv-form, and
  honestly BLOCKED (the engine has no write-back path for a recv-form call).
- `self.compute(x)`, `s.zfill(5)`, `m.group()` -> **untouched**, still the
  pre-Q1.5 dotted Name-form fallback (ok, non-predictable) — because
  `compute`/`zfill`/`group` are in neither set. This is what keeps the
  OOP-heavy `domains/*.py` repo corpus's `self.method()` calls from being
  spuriously reclassified and blocked.

A second, independently-found bug fixed in the same pass: `_finish`'s
`native_oracles` field (the set a CALLER must declare to `ProgEval` to
actually run the emitted program) was computed as `extern_names &
NATIVE_ORACLES` only — correct pre-Q1.5 because a recv-form call always made
`predictable` False, so no predictable program ever needed a recv oracle
declared. Once a recv-form call could itself be predictable, a caller
declaring only that set got a **spurious** `extern:<method>` trap on an
otherwise-predictable program (reproduced: `s.split(sep)` traps
`extern:split` even though `predictable == True`). Fixed to
`(extern_names & NATIVE_ORACLES) | recv_methods`; re-verified live
(`s.split(',')` now correctly returns `('a','b','','c')`).

## 3. Coverage — BOTH numbers, before/after, honestly

### 3a. MBPP (the phase's reason to exist) — HQ1

| | n/427 | ok % | predictable % |
|---|---|---|---|
| Pre-Q1 floor (frozen, Q0) | — | 316 (74.0%) | 147 (34.4%) |
| **Post-Q1.5 LIVE (this phase, measured 2026-08-01)** | — | **322 (75.4%)** | **235 (55.0%)** |

(`tests/test_emitter_widening_migrated.py::test_hq1_live_verdict`, re-derived
from `scripts.mbpp_blocker_histogram.measure()` — imported, never
reimplemented, and never written back to the frozen
`results/mbpp_blocker_histogram.json` artifact, verified by mtime/hash
unchanged across the test run.)

**HQ1 VERDICT: 235/427 = 55.0% — clears the registered bar (≥45%) by a wide
margin, and EXCEEDS the prereg's own full-recommended-scope ceiling of
226/427 = 52.9%** (PROGRAM_SYNTHESIS_ARC2_PREREG.md §3), the number that
scope's own author called the ceiling a follow-on emitter-only phase could
reach "WITHOUT any further Rust work." This phase did exactly that — no Rust
was touched (`runners/dsl/src/**` byte-unchanged this phase) — and beat the
projected ceiling by 2.1pp, because the ceiling's own derivation didn't (and
couldn't) anticipate the `_dotted_name` receiver-ambiguity fix in §2, which
is worth real MBPP mass on its own (see the blocker-mass table below).

**Gap enumerated by blocker mass** (the null-reading check: does
kwargs/collection_methods/lambda dominate the remainder, as the joint curve
predicted?) — **partially confirmed, with a correction**: the joint curve's
top predicted families (`comprehension_advanced`, `kwargs`, `lambda`) are
still the largest STRUCTURAL blocker masses, but the SINGLE largest blocker
of all is now `RecvMethod:append` — a family the curve's own vocabulary
called `collection_methods`, confirmed dominant exactly as predicted, just
concentrated in one method name:

Structural blockers (`ok=False`), MBPP, final state, top masses:

| blocker | mass |
|---|---|
| `RecvMethod:append` | 22 |
| `CompTargetComplex` | 18 |
| `Lambda` | 15 |
| `KwargsCall` | 13 |
| `OpExt:FloorDiv` | 6 |
| `OpExt:LShift` | 6 |
| `CompMultiClause` | 5 |
| `RecvMethod:sort` | 5 |
| `RecvMethod:add` | 4 |
| `StarArgsCall` | 3 |
| `ComprehensionDict` | 3 |
| `RecvMethod:remove` | 3 |
| `InStrStatic` | 2 |
| `SliceSubscript` (write-target only now) | 2 |
| `RecvMethod:pop` | 2 |
| `OpExt:RShift` | 2 |
| `RecvMethod:setdefault` | 2 |

`ok=True but not predictable` (87 tasks) is now dominated by `regex` (28,
explicitly out of the plan's scope — risk #5, "no regex"), `map`/`next` (the
engine's own honest refusal — needs a first-class callable/lazy iterator,
neither exists in this value model), and a long tail of same-corpus
helper-function externs (`is_Power_Of_Two`, `get_char_count_array`, ... — a
declared-oracle/multi-function synthesis concern, Q3+ territory per the
prereg, not an emitter gap).

### 3b. Repo corpus (`domains/` + `substrate/`) — the honest trade-off

| scope | n | ok (representable) | predictable |
|---|---|---|---|
| Frozen P2 (scope A, domains/ top-level) | 7262 | 4099 (56.4%) | 665 (9.2%) |
| **Q1.5 (scope A, this tree)** | 7444 | **3721 (50.0%)** | **1005 (13.5%)** |
| Frozen P2 (scope B, histogram full) | 9685 | 5619 (58.0%) | 928 (9.6%) |
| **Q1.5 (scope B, this tree)** | 9908 | **5029 (50.8%)** | **1360 (13.7%)** |

(`results/prog_ir_python_coverage.json`'s new `q15_post_widening` block,
generated via `scripts/prog_ir_coverage_measure.py --append-q15`; the
pre-existing `scope_baseline_domains_toplevel`/`scope_histogram_full`/
`frozen_27_subset_check` keys are verified byte-identical before/after —
diffed field-by-field, not just eyeballed.)

**The number moved, and it moved DOWN for representability, UP for
predictability — both reported, neither hidden.** `RecvMethod:append`
alone accounts for 1305 of the new blocker mass on scope A (`RecvMethod:add`
268, `RecvMethod:setdefault` 116 close behind) — this repo is
OOP/mutation-heavy Python (list-building loops, `self._x.append(...)`-style
code), so the §2 fix that correctly recognises `xs.append(v)` as a
structurally-unrepresentable recv-form call (no write-back path) costs far
more representability here than it costs on MBPP's smaller, more
functional-style reference solutions — while gaining real predictability on
every function that *only* uses read-only string/dict methods. This is the
`collection_methods`/mutating-`dict_methods` residual Q1 Notes §3 named
explicitly ("a real, scoped follow-on, not a silent gap") landing its cost
side: honestly blocking what was previously honestly-but-uselessly
"representable." `SliceSubscript` dropped from 524 (frozen) to 143 (now
write-targets only) — the single largest **positive** structural move on
this scope.

## 4. Frozen-P2 fixture corpus — byte-identity, proven not asserted

`tests/test_emitter_widening_migrated.py` loads the ACTUAL pre-Q1.5 emitter
source via `git show HEAD:./domains/prog_ir_emit.py` (never a hand-maintained
snapshot) and re-emits all 13 `tests/fixtures/prog_ir_read/` fixtures through
both versions: `ir`/`blockers`/`variants`/`params` are byte-identical for
every one of them. The single, named, deliberate metadata exception:
`dotted_call`'s `predictable` moves `False -> True` (`math.sqrt` is now a
landed native oracle) — `ir` itself is untouched, asserted explicitly
(`test_dotted_call_predictable_move_is_the_only_named_exception`).

Two pre-existing assertions in `tests/test_prog_read_python_migrated.py`
became factually false as a DIRECT, INTENDED consequence of this widening
(not touched arbitrarily — both are the exact residuals this phase exists to
close) and were corrected, each with a dated comment:

1. `test_dotted_extern_name_verbatim` — `math.sqrt` is now native, so
   `dotted_call` is predictable; the "verbatim dotted name traps when
   undeclared" property it exists to pin is re-demonstrated by withholding
   the oracle declaration instead of relying on non-nativeness.
2. `test_expression_grain_residuals` — `xs[1:3]` (plain read-position slice)
   no longer blocks; the residual list drops `SliceSubscript` and a NEW test
   (`test_slice_still_blocks_as_an_assignment_target`) pins that a slice
   WRITE target still does.

## 5. The sibling reconciliation (Q1.5-caused test drift in Q0-owned files)

Per the coordinator's mid-task ownership grant, two more pre-existing test
files were reconciled (frozen artifacts `results/mbpp_blocker_histogram.json`
/ `results/mbpp_zero_shot_baseline.json` verified byte-unchanged by hash
throughout):

- `tests/test_mbpp_histogram_migrated.py::test_known_task_2_bitand_is_set_intersection_not_bitwise`
  — task 2's `set(a) & set(b)` is EXACTLY the finding this test was measuring
  toward a future fix; updated toward MORE coverage (now asserts `ok=True,
  predictable=True` live, with a dated 2026-08-01 note), the frozen artifact
  row assertions below it are untouched.
- `tests/test_mbpp_histogram_migrated.py::test_frozen_artifact_reproducible_from_full_corpus`
  → renamed `test_full_corpus_measure_is_twin_run_deterministic`: its real
  purpose (module-level dicts/sets never leak state across a run) is
  preserved by comparing two LIVE runs to each other instead of a live run
  to the now-stale Q0 snapshot.
- `tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
  — task 11's drift (`gapped:enumerate_failed` -> `accepted_holdout_fail`)
  predates Q1.5 (it's the Q1 `SynthEnumerate` widening, already documented
  as positive evidence in PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md §5); converted
  to a frozen-row-only assertion for that one pick, dated, with the other two
  picks keeping full live re-verification.

Q2's `tests/test_mbpp_spec_migrated.py` (67 tests, not modified) is green
unmodified under the widened emitter — no regression there.

## 6. Gates — final sweep

`PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=.`:

| Suite | Count | Status |
|---|---|---|
| `test_prog_read_python_migrated.py` | 53 (52 + 1 new) | green |
| `test_prog_ir_migrated.py` | 54 | green, untouched |
| `test_value_domain_migrated.py` | 83 | green, untouched (docstring-only edit) |
| `test_program_synthesis_migrated.py` | 17 | green, untouched |
| `test_code_synthesis_baseline_migrated.py` | 11 | green, untouched |
| `test_emitter_widening_migrated.py` (NEW) | 79 | green |
| `test_mbpp_histogram_migrated.py` | 22 | green (2 reconciled) |
| `test_mbpp_baseline_migrated.py` | 40 | green (1 reconciled) |
| `test_mbpp_spec_migrated.py` (Q2, not modified) | 67 | green |
| `test_mbpp_contamination_migrated.py` | 7 | green, untouched |
| `test_synth_enumerate_migrated.py` | 20 | green, untouched |
| `test_prog_descent_migrated.py` | 15 | green, untouched |
| `test_prog_repair_migrated.py` | 11 | green, untouched |
| `test_prog_synthesis_battery_migrated.py` | 21 | green, untouched |

Total: **500/500** across these fourteen suites in one run. Broader sweep
(`pytest tests/ -k "prog_ or mbpp or synth or code_synthesis"`, 536 node ids
incl. neighbouring render/gap/rust_lua/constructions suites that also import
`prog_ir_emit`): 534 passed, 2 skipped (pre-existing, unrelated optional-dep
skips: `whisper`, Piper voice model), 0 failed.

## 7. Residuals (named, not silently absorbed)

1. **The repo-corpus "ok" (representability) number moved DOWN** (56.4% ->
   50.0% on scope A), driven almost entirely by `RecvMethod:append`/`add`/
   `setdefault` — a deliberate, honest trade (§3b), not a bug. A future
   phase that wants representability back on OOP/mutation-heavy code would
   need the write-back mechanism Q1 Notes §3 named (`ProgMethodCallSet` or
   an emitter-side `xs = append(xs, v)` lowering) — out of this phase's
   scope, same as it was Q1's.
2. **`map`/`next`/`iter` remain refused** (the engine's own honest
   refusal — no first-class callable/lazy iterator in this value model);
   9+3 MBPP tasks need them, grouped under `general_builtins` in the
   remaining gap.
3. **Regex remains the single largest MBPP gap family** (28 tasks) — named
   out-of-scope by the plan from Q0 onward (risk #5, "no regex" — a
   genuinely new object model).
4. **Same-corpus helper-function externs** (a task calling a sibling MBPP
   function) are a declared-oracle/multi-function synthesis concern (Q3+
   territory), not an emitter gap — named, not attempted here.
5. **`OpExt:FloorDiv`/`floordiv_general` and `<<`/`>>`** remain out of this
   phase's scope, per the Q1 notes' own residual list — untouched.
6. **`isinstance`'s tuple-of-types form** (`isinstance(x, (int, float))`)
   has no OR-of-type-names engine convention — honest
   `IsinstanceMultiType` blocker, a real design decision for whichever
   phase wants it (the engine's `isinstance` oracle would need a second
   dispatch shape).
7. **Corpus drift** (scope A n: 7262 frozen -> 7444 now; scope B n: 9685 ->
   9908) — the tree grew since P2/Q0 (sibling agents editing `domains/`
   concurrently); every percentage above carries its own measured
   denominator, per the standing "eval-subset coverage is part of every
   claim" rule.
8. **The MBPP `blocker_top20`/`extern_family_top20` fields in the FROZEN
   `results/mbpp_blocker_histogram.json` artifact reflect the PRE-Q1.5
   emitter** (by construction — that file is a Q0-era snapshot, never
   regenerated by this phase). Any future reader computing a live MBPP
   number MUST re-run `mbpp_blocker_histogram.measure()` (as
   `test_hq1_live_verdict` does) rather than reading that file's
   `program_side.predictable_count` and calling it current.
