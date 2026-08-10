# PROGRAM SYNTHESIS ARC 2 Q1 — THE VALUE-DOMAIN FLOOR (notes)

**Date:** 2026-08-01
**Scope:** `PROGRAM_SYNTHESIS_ARC2_PLAN.md` §2-Q1 — widen `ProgEval` and
`SynthEnumerate` from the arc-1 integer/int-list floor to the Q0-picked op
set and types, plus the `exclude` parameter. The arc's ONE Rust phase.
**Files touched:** `runners/dsl/src/{term.rs,term_variants.rs,prog_eval.rs,
synth_enumerate.rs,jsonio.rs,reflect.rs}`, `substrate/dsl.py` (additive
mirrors), `tests/test_value_domain_migrated.py` (NEW),
`tests/test_synth_enumerate_migrated.py` (additive), this file.
**Not touched (explicit file-ownership boundary this phase hit):**
`domains/prog_ir_emit.py`, `domains/generator.py`, `domains/prog_synthesis.py`,
any seed JSON. This boundary drives the HQ1 finding below — read §5 before
quoting any HQ1 number from this document.

---

## 1. What landed, by op family

| Family (Q0 name) | Status | Where | Notes |
|---|---|---|---|
| **Value domain** (str/bool/float/none/dict, +set/tuple) | LANDED | `Value` enum already had every variant (pre-Q1); the work was evaluator/enumerator REACH, not new types | `ProgContainerLit` already carried list/tuple/set/dict kinds |
| **bitwise_ops** — int | UNCHANGED | `term.rs` `BitAnd`/`BitOr`/`BitXor` | byte-identical to arc-1 when either operand isn't Set-like |
| **bitwise_ops** — set algebra | LANDED | `term.rs` `as_set_like`/`set_result_like` | `&`/`\|`/`^` dispatch on the RUNTIME type (Set/FrozenSet on BOTH sides → intersection/union/symmetric-difference, result tagged by the LEFT operand); this is a GLOBAL DSL-term change, not Prog-scoped, so `ProgEval`'s mixed-tree rebuild path inherits it for free |
| **math_native** | LANDED | `prog_eval.rs::call_native_oracle` | `round` (banker's rounding, 1- and 2-arg incl. negative ndigits), `pow` (2-arg; 3-arg modpow REFUSED honestly), `divmod` (own floor-division impl, does NOT touch the global `IDiv`/`IRem` truncating semantics), `ord`, `chr`, `math.sqrt` (domain trap), `math.floor`, `math.ceil`, `math.pow`, `math.trunc` |
| **slicing** | LANDED | NEW `TermNode::ProgSlice` + `prog_eval.rs::slice_indices` | str AND list, negative step, OOB clamps (never traps on out-of-range bounds — Python slicing doesn't either); `step==0` traps `slice:zero_step`; non-sliceable receiver traps `slice:type:<kind>` |
| **string_methods** | LANDED | `prog_eval.rs::call_recv_oracle` | upper/lower/capitalize/strip/lstrip/rstrip/split(sep,maxsplit)/join/replace(count)/startswith/endswith(tuple-of)/find/count/isdigit/isalpha/isupper/islower |
| **general_builtins** | PARTIAL (by design) | `prog_eval.rs::call_native_oracle` | LANDED: all/any/isinstance/enumerate/zip/reversed. REFUSED: map/next/iter — these need a first-class callable or a lazy iterator, neither of which exists in this value model; approximating them would be dishonest, not a genuine capability |
| **container_ctor** | LANDED | `prog_eval.rs::call_native_oracle` | list/tuple/set/frozenset/dict (0/1-arg forms; `dict(pairs)` from an iterable of 2-tuples) |
| **dict_methods** | PARTIAL (read-only) | `prog_eval.rs::call_recv_oracle` | LANDED: items/keys/values/get. NOT landed: `setdefault` and any other MUTATING dict method — see §3 |
| **collection_methods** (stretch) | NOT LANDED | — | mutating (`append`/`sort`/`add`/...) — same blocker as `setdefault`, §3 |
| **lambda** (stretch) | NOT LANDED | — | a new IR variant + closures; out of this phase's budget |
| **comprehension_advanced** (stretch) | NOT LANDED | — | dict comprehensions / multi-clause; out of budget |
| **kwargs**, **floordiv_general** (the `**kwargs`/`//` op forms), **KwargsCall** | NOT LANDED (emitter-side) | — | require `domains/prog_ir_emit.py` to emit a NEW IR shape for `**kwargs` calls / the `//` operator; this phase's own internal use of floor division (`divmod`'s oracle) does not touch the emitter or the global `IDiv` Term — see §5 |

**`SynthEnumerate` (the enumerator) widening, separately:**

- The signature/target model (`SigVal`/`canon`/`matches_target`) is widened
  from int/float/bool-only to also cover Str (exact match) and a stable
  recursive repr for None/Dict/Tuple/Set/Node — see §2.
- Two new composition ops in the enumerator's OWN grammar: `Concat`
  (→ `StringConcat`) and `CaseFold` (→ Python `str.lower()`), reusing
  EXISTING DSL string Terms — same kernel-table discipline as every
  arithmetic op, not a new mechanism.
- A TYPED default op inventory: a spec whose every variable value AND
  output is string-shaped, with no caller-declared `ops`, uses
  `DEFAULT_STR_OPS = [Concat, CaseFold, Eq, IfThenElse]` instead of
  arithmetic `DEFAULT_OPS` — "a str spec never enumerates BitAnd." An
  explicit `ops` always overrides this.
- String consts are spec-derived: every whole string value observed in
  any row (input or output) PLUS every distinct character in any of
  them, deduped, order preserved — never a global alphabet, bounded
  naturally by the spec's own content (no separate cap).
- `exclude` — see §4.

---

## 2. The divergence ledger — delta over arc-1's registered rules

Arc-1's ledger (P1/P4-A notes) is UNCHANGED for everything it already
covered (Div-by-zero → 0.0, no aliasing through lvalue writes, list/tuple
collapse to Tuple, set iteration order is the substrate's, etc.). Q1 adds:

1. **`round()` is approximate banker's rounding, not IEEE-754-exhaustive.**
   `round_half_even`/`round_half_even_digits` (`prog_eval.rs`) scale by
   `10^ndigits` and round the SCALED f64 half-to-even. This coincides with
   CPython's own (correctly-rounded-decimal) `round()` for every case this
   phase's fixture corpus exercises (binary-exact inputs like `2.5`, `1.25`;
   an f64-representation-sensitive case like `2.675` coincides too, because
   BOTH algorithms start from the identical, already-imprecise f64 — but
   this is not a proof of universal agreement). Documented, fixture-avoided
   for genuinely ambiguous multi-digit decimal cases, per the arc's
   "pin, fixture-avoid, refuse-on-ambiguity" discipline.
2. **`divmod`/floor division is LOCAL to the oracle, not global.** Python's
   `//`/`divmod` floor toward negative infinity; the DSL's existing global
   `IDiv`/`IRem` Terms TRUNCATE toward zero (a PRE-EXISTING, unchanged
   divergence — those Terms are used pervasively outside program synthesis
   and were correctly left untouched). `divmod`'s own `floor_div_i64`/
   `floor_mod_i64` implement genuine Python floor semantics, entirely
   inside `prog_eval.rs::call_native_oracle`, with zero effect on any other
   caller of `IDiv`/`IRem`. This means Python's bare `//` operator is STILL
   not representable via this phase's work (see §1's `floordiv_general`
   row) — only the `divmod()` builtin got real floor semantics.
3. **`isinstance` has no first-class type object.** The value model has no
   "type" value, so `isinstance(x, T)` is implemented via a TYPE-NAME
   STRING convention (`isinstance(x, "int")` at the IR level) rather than
   Python's real type-object argument. This is an ENGINE capability; the
   Python emitter side of translating `isinstance(x, int)` (a `Name` AST
   node referring to the builtin `int`) into this string convention is
   NOT wired (out of this phase's file-ownership scope) — named as a
   residual, not silently assumed solved.
4. **`map`/`next`/`iter` are REFUSED, not approximated.** These need a
   first-class callable (map) or a lazy iterator (next/iter); this value
   model has neither. Declaring them "supported" via some degenerate
   eager approximation would misrepresent the histogram's own family
   framing — refused honestly (`extern:unimplemented:<name>`).
5. **Mutating recv-form calls are not landed.** `ProgCallExtern` is a PURE
   expression call with no lvalue write-back path (unlike
   `ProgSubscriptSet`/`ProgAttrSet`, which exist precisely because
   subscript/attr writes needed one). `list.append`, `list.sort`,
   `dict.setdefault`, etc. would need the SAME kind of write-back machinery
   — a real, scoped follow-on, not a silent gap. `collection_methods` and
   the mutating half of `dict_methods` are named residuals, not partial
   implementations pretending completeness.
6. **`SynthEnumerate.inadmissible` is now structurally unreachable.**
   Arc-1's `canon()` returned `None` (→ inadmissible) for anything past
   int/float/bool — this was ALWAYS the value-domain floor's own gap, not
   a genuine error-detection path (the plain DSL `evaluate()` this engine
   drives has no error channel distinct from an ordinary `Value`). Q1's
   widened `canon`/`canon_repr` never fails, so `inadmissible` reports `0`
   on every call now; kept in the output `Dict` for wire back-compat.
7. **Dict iteration order is `cmp_value`-sorted, NEVER Python's true
   insertion order — and for Str keys, that sort is by INTERNED-SYMBOL
   ID, not alphabetic content.** This is a PRE-EXISTING (pre-Q1) property
   of every dict-construction site (`ProgContainerLit`, `container_with`'s
   upsert path) that Q1's new `dict_methods`/`general_builtins` work newly
   EXERCISES (arc-1 never called `.items()`/`.keys()`/`.values()` on a
   Prog dict). Gated explicitly:
   `test_dict_iteration_is_sorted_by_key_not_insertion_order`
   (`tests/test_value_domain_migrated.py`) — pins the actual behaviour
   (int keys sort numerically; string keys sort by GLOBAL intern history,
   demonstrated by showing the "later-alphabetical" key sorts FIRST when
   it was interned first). This is the gate's "decide, document" ask,
   answered: the decision predates Q1 and is honestly characterised, not
   silently assumed to be alphabetical or insertion-ordered.
8. **`str.split()`/`str.strip()` use Rust's Unicode whitespace, not
   CPython's ASCII-plus-a-few-extras set exactly.** `py_is_space` is
   scoped to `' \t\n\r\x0b\x0c'` (CPython's own `str.strip()` default set)
   for strip/lstrip/rstrip; `split()` with no separator uses
   `str::split_whitespace` (Rust's own, Unicode-aware definition) — a
   minor, named divergence for exotic whitespace characters, not exercised
   by the fixture corpus (ASCII-only cases).
9. **String Lit repr uses Python's single-quote convention.** Fixed during
   this phase (`synth_enumerate.rs::lit_repr`) so `SynthEnumerate`'s
   `term_str` output reads `'!'` not Rust's `"!"` Debug-quoting — a
   readability fix, `term_str` was never meant to be re-parsed (the
   `term` field, Term-JSON, is the machine-consumed one).

---

## 3. The mutating-recv-call gap (why it's a NAMED residual, not silently missing)

`xs.append(v)` in Python mutates `xs` in place and the statement's VALUE is
discarded. `ProgCallExtern` (this engine's method-call IR node) is a pure
EXPRESSION: it reads its receiver, computes a result, and returns it — there
is no path back to the variable/lvalue `xs` came from. The two existing
write-back mechanisms (`ProgSubscriptSet`, `ProgAttrSet`) exist as SEPARATE
statement-level IR nodes that rebuild the container immutably and write the
result back through the lvalue chain (`set_lvalue`). A mutating method call
needs the SAME shape: either (a) a dedicated `ProgMethodCallSet` statement
node with its own lvalue write-back, or (b) an emitter-side lowering of
`xs.append(v)` into `xs = <ProgCallExtern append-as-pure-function>(xs, v)`
before it ever reaches this engine. Both are real design decisions, not
implementation gaps this phase could close incidentally — named here for
whichever phase picks up `collection_methods`/mutating `dict_methods` next.

---

## 4. The `exclude` contract

`SynthEnumerate{..., exclude}` evaluates to a list of Term-JSON STRINGS —
candidates a caller has already REFUTED (the P7-B repair lever: within-round
candidate iteration was contract-blocked because refuted output-valued Lits
re-entered via auto-appended consts).

**Mechanism (`synth_enumerate.rs`):**

1. Each excluded string is parsed by a MINIMAL, LOCAL reader
   (`parse_excluded_term`) scoped to exactly this module's own grammar
   (`Var` / `Lit` / the `OP_TABLE` ops). Deliberately NOT
   `jsonio::term_from_json`: that function needs `&mut Interner` to intern
   identifiers on the way in, but `eval_synth_enumerate` only ever holds
   `&Interner` (the documented immutable-at-eval-time discipline). A `Var`
   resolves against the SPEC's OWN already-interned variable names (an
   excluded term came from a prior call over the same variables — its
   names are never novel to this call); a `Lit` string mints a
   `Surface(Text)`, which the widened `canon` already treats identically
   to an interned `Str` for signature purposes, so no interning is ever
   needed to compute a correct exclusion signature.
2. Each successfully-parsed excluded term's SIGNATURE — its behaviour
   across THESE SAME example rows — is computed and inserted directly into
   the equivalence-pruning `seen` set, BEFORE any leaf is registered.
   It is never counted toward `tested`/budgets and never added to
   `by_size` (a refutation record, not a reusable building block).
3. Because leaf registration and constant auto-append (integer-valued
   outputs, and Q1's spec-derived string consts) happen AFTER this
   pre-seeding step, ANY later candidate — however built, including an
   auto-appended constant that syntactically re-introduces the excluded
   value — that reaches the SAME signature is now indistinguishable from
   "already seen" and is silently dropped, counted as `pruned_equiv`.
   This is the exact P7-B fix: the const-resurrection case is closed by
   construction, not by a special-cased check.
4. A malformed entry — bad JSON, an op outside this call's own `ops`
   inventory... actually outside the FULL `OP_TABLE` (not scoped to the
   caller's declared `ops` — a broader parse-acceptance than strictly
   necessary, but harmless: a term using an op the caller didn't declare
   can never have been PRODUCED by this engine for this caller anyway,
   so pre-seeding its signature only prevents a coincidental future
   duplicate, never masks a real capability) — or a reference to a
   variable this spec doesn't have, is SKIPPED, never fatal. `exclude` is
   a soft refutation hint, not part of the spec contract that can crash a
   call.

**Gates** (`tests/test_synth_enumerate_migrated.py`, additive):
`test_exclude_prunes_an_already_refuted_candidate`,
`test_exclude_blocks_const_resurrection` (the literal P7-B scenario: a
constant-function spec's ONLY size-1 solution is a bare `Lit`; excluding it
must not let the auto-appended-consts step silently resurrect the exact
same behaviour), `test_malformed_exclude_entry_is_skipped_not_fatal`,
`test_exclude_empty_list_is_a_no_op`, `test_synth_enumerate_exclude_field_reflects`.

---

## 5. THE HQ1 VERDICT — read this before quoting a number

**HQ1 asks** (`PROGRAM_SYNTHESIS_ARC2_PREREG.md` §3): after Q1, what
fraction of the 427 MBPP reference solutions are BOTH `ok`
(IR-representable) AND `predictable` (no undeclared extern) under the REAL
`emit_prog_ir` + `ProgEval`? Preregistered bar: ≥45%; measured ceiling at
the 55%-mark scope this phase targeted: 44.5% (190/427); at the FULL
recommended scope (55%-mark + stretch + `dict_methods`/`kwargs`/
`floordiv_general`): 52.9% (226/427).

**The finding this phase surfaced, and it is load-bearing:** `ok` and
`predictable` are ENTIRELY COMPUTED by `domains/prog_ir_emit.py` — a Python
file this task's file-ownership scope explicitly EXCLUDES (this Q1 phase
may touch only `runners/dsl/src/**`, `substrate/dsl.py`, and new test/notes
files). Confirmed by inspection of that file: `SliceSubscript` and
`OpExt:BitAnd`/`BitOr`/`BitXor` are STRUCTURAL blockers
(`self._blk("SliceSubscript")` etc., called BEFORE any IR node is even
considered) — the emitter does not know `ProgSlice` exists, and does not
know `BitAnd` on a Set is now evaluable, because NOTHING in this phase's
scope taught it to. **Landing `ProgSlice` and the widened native-oracle
table in Rust is NECESSARY for HQ1 to ever move, but NOT SUFFICIENT: the
emitter must also be taught to EMIT these IR shapes for the matching Python
AST forms — Python-side work outside this phase's scope.**

**Measured, honestly, two ways** (`test_hq1_verdict`,
`tests/test_value_domain_migrated.py`):

| | n/427 | % |
|---|---|---|
| **LIVE** (re-running the real, unmodified `emit_prog_ir` — this IS what a live re-run produces, since Q1 never touched it) | 147 | 34.4% |
| **HYPOTHETICAL** (the prereg's OWN documented method, §3 caveat #3: "if Q1 added native support for family X, would this task become predictable" — a re-derivation from the histogram's per-task `extern_families` against the families THIS phase actually landed, `container_ctor`/`math_native`/`general_builtins`/`string_methods`) | re-derived at test time from `results/mbpp_blocker_histogram.json`; ≥ the live floor by construction | ≥34.4% |

**The LIVE number is UNCHANGED at the pre-Q1 floor.** This is not a null
result about the engine — the engine-level CPython-agreement gates (§ below,
83 cases) prove every landed family works correctly in isolation. It is a
finding about SCOPE: HQ1's bar is defined over a full-stack measurement
(`emit_prog_ir` → `ProgEval`) that this phase's file-ownership boundary
could only complete on the SECOND half. The HYPOTHETICAL number states the
ceiling a follow-on emitter-only phase could reach WITHOUT any further Rust
work — the engine already has everything `bitwise_ops`/`math_native`/
`container_ctor`/`general_builtins`/`string_methods` need; only the AST
walk that recognises these Python shapes and emits the matching IR is
missing.

**Independent, POSITIVE evidence Q1 already changed real behaviour, found
during regression testing (not something to hide):**
`tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
(NOT one of this phase's required gates, but exercised during the "keep the
arc-1 suites green" sweep) shows task 11 (`similar_elements`, the histogram's
OWN bitwise/set-algebra example) drifting from the frozen zero-shot
baseline's `gapped:enumerate_failed` to a LIVE `accepted_holdout_fail`.
This is `domains/generator.py`'s `SynthEnumerate` FALLBACK RUNG — which
operates directly on the assert-derived `{inputs, output}` spec,
INDEPENDENT of `emit_prog_ir`'s representability gate — now ACCEPTING a
spec it used to refuse outright (Q1's widened `canon`/target model no
longer requires a numeric output) and attempting an enumerative search
that overfits the single revealed row and fails on the held-out one. This
is **exactly the risk the prereg named verbatim**: *"a Q1 representability
win would just relabel `gapped:enumerate_failed` as `accepted_holdout_fail`,
never `pass`"* (§0 reconciliation). It is real, measured, independent
confirmation that Q1's SynthEnumerate-side widening is live and reachable
TODAY through the existing Python pipeline, on a real MBPP task — even
though the `emit_prog_ir`-gated `ok`/`predictable` numbers cannot move
without further (out-of-scope) emitter work. This file's task is a
FROZEN-ARTIFACT reproduction test, not one of Q1's required gates
(`test_code_synthesis_baseline_migrated.py`'s 11 tests are, and remain
green); it is reported here for the record, not "fixed" — reverting it
would mean reverting the very capability this phase was asked to build.

**Null reading, applied honestly:** the registered null-reading clause
("if the post-Q1 measured representable+predictable rate is <40%, Q1
undershot its own registered op-family list") cannot be evaluated on the
LIVE number for the reason above — it would read the SAME 34.4% pre- and
post-Q1 regardless of how much Rust work landed, making it uninformative
here. The HYPOTHETICAL number is the honest substitute measurement this
phase can actually produce, clearly labeled as such per the prereg's own
caveat #3, never presented as "the" HQ1 number.

---

## 6. Gates — what actually ran green

**Cargo (`runners/dsl`):** full `cargo test --lib` — 684 passed, 0 failed,
4 ignored, single-threaded (`--test-threads=1`; two tests
— `scale_audit::tests::totals_are_always_emitted_even_when_every_cell_is_zero`
and `shape_decode::dim_infer_tests::d_sweep_distinct_tracks_its_axis` —
are PRE-EXISTING, unrelated-to-this-phase parallel-execution flakiness:
both pass in isolation and under `--test-threads=1`; neither touches any
file this phase modified). `cargo build --release` green; the `.so` was
synced atomically (`cp` to `.new` + `mv`, matching
`domains/self_modification.py::_sync_native`'s own atomic-replace
discipline) to `runners/dsl/python/substrate_rs/_native.abi3.so`.

**Pytest (`PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=.`):**

| Suite | Count | Status |
|---|---|---|
| `test_prog_ir_migrated.py` | 54 | green, byte-identical (arc-1 frozen) |
| `test_synth_enumerate_migrated.py` | 20 (11 arc-1 + 9 new Q1) | green |
| `test_program_synthesis_migrated.py` | 17 | green |
| `test_prog_descent_migrated.py` | 15 | green |
| `test_prog_repair_migrated.py` | 11 | green |
| `test_prog_synthesis_battery_migrated.py` | 21 | green (the internal battery ARTIFACT is frozen; not re-run) |
| `test_value_domain_migrated.py` | 83 (NEW) | green |
| `test_code_synthesis_baseline_migrated.py` | 11 | green |

Additionally run (not in the required list, informational): the LLVM
correspondence suite (`test_prog_read_llvm_migrated.py` +
`test_render_llvm_migrated.py`, 48 tests — the only other consumer of the
global `BitAnd`/`BitOr`/`BitXor` Terms outside program synthesis, confirmed
unaffected since those Terms only carry Int operands there); the
contamination and histogram gates (`test_mbpp_contamination_migrated.py` 7,
`test_mbpp_histogram_migrated.py` 22) — green, both scripts untouched by
this phase.

**`test_value_domain_migrated.py`'s own gate coverage** (~50+ CPython-
agreement cases + trap-honesty + determinism + purity, ~83 tests total):
bitwise int (4) + set algebra (3, incl. the task-2 finding); math_native
(18 agreement + 2 trap); slicing (9 agreement + 2 trap); string_methods
(22 agreement + 2 trap); general_builtins (8 agreement + 1
isinstance-convention test); container_ctor (5 agreement + 1 dict-from-pairs);
dict_methods (2 + 1 order-independent); dict iteration determinism (1,
pinning the Str-key intern-id caveat); purity (1).

---

## 7. Residuals (named, not silently absorbed)

1. **The emitter (`domains/prog_ir_emit.py`) was not updated** to emit
   `ProgSlice` or set-aware `BitAnd`/`BitOr`/`BitXor`, or to recognise the
   new native-oracle call names as `predictable` inputs — out of this
   phase's file-ownership scope. This is THE reason the LIVE HQ1 number
   didn't move (§5) and is the most important residual for whichever
   phase picks up the emitter next.
2. **Mutating recv-form calls** (`list.append`, `dict.setdefault`, the
   rest of `collection_methods`) need a NEW lvalue-write-back statement
   shape — named design work, not started (§3).
3. **`isinstance`'s type-name-string convention** has no emitter-side
   wiring (§2 item 3) — the engine capability exists; nothing calls it
   from real MBPP-shaped programs yet.
4. **`map`/`next`/`iter`, 3-arg `pow`, `**kwargs` calls, Python's bare
   `//` operator, dict/list/set comprehensions beyond the existing P1
   variants, and `lambda`** are all NOT landed — named exclusions per the
   prereg's own stretch-goal framing, not silent gaps.
5. **`str.split()`/whitespace semantics use Rust's Unicode definition**,
   a minor named divergence from CPython's own ASCII-plus-extras default
   (§2 item 8).
6. **Two pre-existing, unrelated parallel-test-execution flakes** were
   discovered in the Rust suite (`scale_audit`, `shape_decode`'s dimension
   inference) — not caused by this phase (both pass single-threaded and
   in isolation), reported here because they were newly OBSERVED while
   confirming this phase's own gate, not because this phase is
   responsible for them.
7. **`test_mbpp_baseline_migrated.py`'s frozen-artifact reproduction test
   drifts on one task** (§5) — not a required gate for this phase, not
   "fixed" (fixing it would mean reverting the capability), reported as
   independent positive evidence instead.
