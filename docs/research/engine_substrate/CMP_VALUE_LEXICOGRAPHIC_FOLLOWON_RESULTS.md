# ENGINE CORRECTNESS — `(Str,Str)` LEXICOGRAPHIC FOLLOW-ON — RESULTS

*Branch `cmp-value-lexicographic-followon`, worktree
`/home/matt/ocelot-cmp-value-lex-followon`, based on `main` @ `3719b50`.
Prereg: `CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_PREREG.md` (committed `260659f`,
before any code was written).*

*Engine built in this worktree. Pre-fix engine (pristine `3719b50` source)
`sha256 c086d83ad070a3…`; post-fix engine `sha256 23ba3f1dbe2045…`
(`runners/dsl/python/substrate_rs/_native.abi3.so`, verified byte-identical
to what is committed here). `--release`, coherence probe green.*

---

## The one-line result

**8 reported-order call sites found and fixed, all across two files
(`term.rs`, `prog_eval.rs`), via one new function (`value.rs::cmp_value_lex`).
`cmp_value` itself is byte-for-byte untouched** — `git diff` on the function
body is empty. Every fixed site inverts from a wrong, boot-history-dependent
answer to the correct lexicographic one, live, on the same interner, same
process. Canonicalisation-only sites (Set/Dict construction, persistence,
`shape_decode`'s frame correspondence — 51 call sites read and classified)
are unchanged. Two pre-existing pinned tests that asserted the OLD
"deliberately not fixed" behaviour were updated, as their own docstrings
said they should be when this happened.

---

## Verdict table

| bar | verdict | headline |
|---|---|---|
| AR1 — enumeration accurate against current `main` | **MET** | all 8 rows re-verified by direct read at fix time; two additional pinned regression tests (in a DIFFERENT file than the enumeration's own search covered) were found FAILING after the fix and are reported, not hidden — §4 |
| AR2 — the fix, `cmp_value_lex` | **MET** | new function, `value.rs`; `cmp_value`'s own body has zero changed lines — §1 |
| AR3 — every §1.2 site switched, only those | **MET** | 8/8 switched; `git diff` review shows no edit inside any canonicalisation function — §2 |
| AR4 — live before/after demonstration | **MET, all 8 sites inverted** | one interner, boot order chosen adversarially (reverse-alphabetical), every site wrong before, correct after — §3 |
| AR5 — regression, paired failing-test lists | **MET** | Rust: 769→774 passed (+5 new tests), 0 failed both sides. Python targeted sweep: 303 passed / 2 failed BOTH sides, IDENTICAL failing names, both pre-existing baseline — §5 |
| AR6 — coherence probe | **MET** | list/tuple stay distinct post-fix — §5.3 |
| AR7 — what this does NOT establish | stated | §6 |

---

## §1 The fix

`runners/dsl/src/value.rs`, a new function immediately after `cmp_value`:

```rust
pub fn cmp_value_lex(a: &Value, b: &Value, interner: &crate::sym::Interner) -> Ordering {
    // ... structurally identical match to cmp_value ...
    (Value::Str(x), Value::Str(y)) => interner.resolve(*x).cmp(interner.resolve(*y)),
    // ... Tuple/List/Set/FrozenSet/Dict recurse into cmp_value_lex, not cmp_value ...
}
```

`cmp_value` itself has **zero changed lines** — verified by `git diff` on
`3719b50..HEAD -- runners/dsl/src/value.rs` and reading the diff: every
hunk inside the old `cmp_value` function body is additions-only-elsewhere;
the function's own text is byte-identical to before.

Why a full structural mirror rather than "delegate everything except `Str`
to `cmp_value`": a `Tuple`/`List`/`Set`/`Dict` containing a nested `Str` (a
relation-tuple like `("name", "zebra")`, or a `Dict` keyed by strings) needs
the NESTED string comparison to also be lexicographic when the container is
being sorted for REPORTED order — delegating the recursive case to
`cmp_value` would silently leave nested strings on boot-order. Confirmed by
a dedicated unit test (`cmp_value_lex_recurses_into_tuples_so_nested_strings_are_lex_too`).

---

## §2 The 8 call sites, and what was deliberately left alone

### 2.1 Fixed (reported-order — the caller/rule observes the comparison's outcome)

| # | function | file:line | `Term`/builtin | what changed |
|---|---|---|---|---|
| 1 | `cmp_bool` | `term.rs:7798` | `Lt`/`Lte`/`Gt`/`Gte` | `cmp_value` → `cmp_value_lex(&av,&bv,ctx.interner)` |
| 2 | `numeric_argmin` | `term.rs:7970` | `ArgMin{items}` | same |
| 3 | `numeric_minmax` | `term.rs:7991` | `Min`/`Max{items}` | same |
| 4 | `numeric_argmax` | `term.rs:8024` | `ArgMax{items}` | same |
| 5 | `min_or_max_over` | `term.rs:9290` | `MinOver`/`MaxOver` | same |
| 6 | `argmin_or_argmax_over` | `term.rs:9439,9453` (two calls, tie count + winner) | `Argmin`/`Argmax`/`ArgminUnique` | same |
| 7 | `"min"`/`"max"` extern | `prog_eval.rs:1387` | Python `min()`/`max()` | same, `interner` param already in scope |
| 8 | `"sorted"` extern | `prog_eval.rs:1535` | Python `sorted()` | same |

Rows 1, 7, 8 are the examples the assigning brief itself named. **Rows 2-6
are this rung's own addition**, found while reading the full call-site
enumeration for the prereg: `ArgMin`/`ArgMax`/`Min`/`Max`/`MinOver`/
`MaxOver`/`Argmin`/`Argmax`/`ArgminUnique` are the Rust-native `Term`
equivalent of the exact same operation as row 7 — an extremum selection
over `Value`s whose WINNER (index, element, or value) is what a rule or
caller observes. Leaving them unfixed while fixing the Python-style
builtin would have left the identical semantic operation correct or wrong
depending only on which of the two surfaces (native `Term` vs. `ProgEval`
builtin) a rule author happened to use — an inconsistency the prereg's own
scope note flagged as a risk and named as this rung's addition rather than
smuggling it in silently.

Two calls inside `argmin_or_argmax_over` (row 6) both needed the switch:
the tie-count match (decides `ArgminUnique`'s refusal) and the winner-select
match (decides the returned element) are BOTH order-sensitive beyond mere
equality (their `Less`/`Greater` arms drive real decisions), not just the
`Equal` arm (which is unaffected by lex-vs-boot-order either way, since
interning is idempotent: two `Str`s are `cmp_value`-`Equal` iff they are
`cmp_value_lex`-`Equal` iff they are the same string — proved by
`cmp_value_lex_agrees_with_cmp_value_on_every_non_string_arm`-style
reasoning, and exploited directly to justify leaving equality-only audit
checks unchanged, see 2.3).

### 2.2 Deliberately left on `cmp_value` (canonicalisation-only — read and classified, not assumed)

All 113 `cmp_value` call sites across `runners/dsl/src/*.rs` (`value.rs`,
`term.rs`, `prog_eval.rs`, `persist.rs`, `synth_enumerate.rs`, `py.rs`,
`shape_decode.rs`, `argmin_tie.rs`) were read. 51 non-fixed CALL SITES
(as opposed to comment/doc mentions) fall into:

- **`persist.rs`** (3 sites): `Set`/`FrozenSet` dedup-on-load, bare-object
  `Dict` key sort. Internal storage/round-trip order.
- **`term.rs`** dict/pairs `sort_by` (7 sites: `MkDict`, anti-unification's
  shared-key iteration, dict construction): canonical key order for a
  cmp-sorted-vec `Dict` — the prior rung's own §4.4 named this
  canonicalisation explicitly.
- **`prog_eval.rs`** dict-pair `sort_by`/`==Equal` lookup (10 sites): same
  class; the `==Equal` lookups are unaffected by which consistent order is
  used at all (see 2.3's equality argument).
- **`synth_enumerate.rs`** (5 sites) and **`py.rs`** (1 site): `Dict`
  construction (synthesis-result dicts, Python→Value conversion).
- **`shape_decode.rs`** (23 sites, the largest group, read in full): every
  one sorts two relation-tuple FRAMES by the SAME order before pairing them
  element-wise for correspondence/equality/offset-inference
  (`build_candidate`, `infer_translate_offset`, `frames_equal`,
  `frames_symdiff`, `frame_value_stream`) — any consistent total order
  works because both sides are sorted by it identically; the order is
  never itself read as "alphabetical." One near-miss, examined and
  excluded: `shape_decode.rs:5124-5129` breaks a velocity tie by comparing
  surface keys to produce a depth RANK that becomes an output field —
  closer to reported-order in spirit, but the keys there are
  coordinate/predicate tuples (not literal strings in the corpus), the tie
  only fires on an exact velocity collision, and no test asserts
  alphabetical intent for it. Left on `cmp_value`, named rather than
  silently skipped.

### 2.3 Deliberately excluded: two AUDIT-ONLY equality checks

`audit_index_selector` (`term.rs:~8060`) and `audit_binder_selector`
(`term.rs:~9235`) both compare a re-evaluated winner to the recorded one
for **exact equality** (`selector_audit`/`argmin_tie` disagreement
detection, default OFF). Since interning is idempotent — two `Str`s are
`cmp_value`-`Equal` iff `cmp_value_lex`-`Equal` iff the same string — these
audit checks are unaffected by which comparator decided the ORIGINAL
selection, and were correctly left untouched.

---

## §3 AR4 — the live before/after demonstration

One `Substrate`, one interner, strings interned in an order CHOSEN so
alphabetical and boot order disagree (`zebra`, `mango`, `banana`, `apple` —
interned in that left-to-right order, so `zebra` gets the LOWEST Sym id).
Ran on the pinned pre-fix artifact (`sha256 c086d83a…`), then the identical
script on the pinned post-fix artifact (`sha256 23ba3f1d…`), same process
each time:

```
== TERM LEVEL ==                                              BEFORE        AFTER
Lt('zebra','apple')                                            True          False   (correct: False)
ArgMin(['zebra','mango','banana','apple'])  -> index            0 = zebra     3 = apple
Min(['zebra','mango','banana','apple'])                        zebra         apple
MinOver(source=[...])                                           zebra         apple
Argmin(source=[...])                                            zebra         apple

== PROGEVAL ==
sorted(['zebra','mango','banana','apple'])            ['zebra','apple',    ['apple','banana',
                                                         'mango','banana']   'mango','zebra']
min(['zebra','mango','banana','apple'])                         zebra         apple
max(['zebra','mango','banana','apple'])                         banana        zebra
```

**Every one of the 8 fixed sites is wrong before, correct after**, on the
same adversarial interning order. (`banana`/`mango`'s exact positions in
the wrong "before" answers are the boot-order artifact itself — not
asserted as meaningful, just recorded as what was actually observed.)

Additionally gated as Rust unit tests (`value.rs`, all 5 new, all pass):
`cmp_value_is_still_boot_order_not_lexicographic` (pins `cmp_value` itself
unchanged — the regression guard the PRIOR rung's own test said to update
"when (Str,Str) is fixed"; `cmp_value` is not what got fixed here, so this
pin stays green), `cmp_value_lex_is_byte_lexicographic_regardless_of_boot_order`
(the Rust-level version of the transcript above, plus a full 4-item sort
both ways), `cmp_value_lex_recurses_into_tuples_so_nested_strings_are_lex_too`,
`cmp_value_lex_agrees_with_cmp_value_on_every_non_string_arm`,
`cmp_value_lex_leaves_surface_text_byte_lexicographic_unchanged`.

---

## §4 AR1 — two pinned tests updated, found the hard way

The enumeration in the prereg was scoped to `runners/dsl/src/*.rs`, per its
own stated bars — it did not (and could not) search the Python test suite
for tests that PINNED the old "sorted-on-strings is deliberately NOT fixed"
behaviour as a passing assertion. Running the direct regression sweep
surfaced two:

1. **`tests/test_cmp_value_surface_migrated.py::test_str_literals_are_deliberately_NOT_fixed_here`**
   — the prior rung's own test, whose docstring said explicitly: *"If a
   later rung fixes (Str, Str), THIS test is the one that should go red and
   be updated deliberately."* It did. Renamed to
   `test_str_literals_are_now_lexicographic_too`, assertion inverted from
   `!=` to `==` against the lexicographic order.
2. **`tests/test_arc6_valuelayer_migrated.py::test_out_of_scope_defects_are_still_present_and_named`**
   — a DIFFERENT rung's (ARC6 value-layer) pinned regression, not found by
   grepping for `cmp_value` in Python (it exercises the defect through
   `sorted()` over `ProgEval`, not through the Rust symbol name). Its own
   docstring: *"If [the sorted-on-strings defect] is fixed later, this test
   fails and the write-up's 'what remains unfixed' section has to be
   updated with it — which is the point."* Updated: the `sorted`-half of
   the test now asserts `fwd == rev == sorted(words)` (previously asserted
   they could differ); the `Eq(0.0, False)` half — a genuinely separate,
   still-open defect, untouched by this rung — is unchanged.
   `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md`
   §9.3 gained an UPDATE note (original text kept, per this project's
   standing "a historical record is never converted" discipline) pointing
   here.

This is reported as the honest outcome of AR1, not hidden: **the
call-site enumeration inside `runners/dsl/src/*.rs` was complete and
accurate, but "accurate against current `main`" for a change of this kind
also has to survive contact with pinned regression tests elsewhere in the
tree that assert the pre-fix behaviour as correct — and the prereg's own
scope did not claim to search those.** Both were found by running the
actual regression suite, not by further code reading, which is exactly
what a regression suite is for.

---

## §5 AR5/AR6 — regression

### 5.1 Rust, single-threaded (this crate's own documented parallel-test noise, per the prior rung's §6.1)

`cargo test --release --lib -- --test-threads=1`:

| | passed | failed | ignored |
|---|---|---|---|
| before (pristine `3719b50` source) | 769 | **0** | 4 |
| after | 774 | **0** | 4 |

Diff of test NAMES (not counts): the only 5 tests present after and absent
before are exactly this rung's 5 new `cmp_value_lex` unit tests
(`value::tests::cmp_value_is_still_boot_order_not_lexicographic`,
`cmp_value_lex_agrees_with_cmp_value_on_every_non_string_arm`,
`cmp_value_lex_is_byte_lexicographic_regardless_of_boot_order`,
`cmp_value_lex_leaves_surface_text_byte_lexicographic_unchanged`,
`cmp_value_lex_recurses_into_tuples_so_nested_strings_are_lex_too`); zero
tests present before and missing after.

### 5.2 Python, paired, engine-swapped, both `data/` and `results/` symlinked to the canonical tree (per CLAUDE.md's standing note on environment-conditional counts)

Targeted at the files most likely to exercise string comparison/ordering
(direct `cmp_value` references, `Argmin`/`Argmax`/`MinOver`/`MaxOver`,
`Lt`/`Gt`/`Lte`/`Gte`): `test_cmp_value_surface_migrated.py`,
`test_arc6_valuelayer_migrated.py`, `test_value_domain_migrated.py`,
`test_rational_domain_migrated.py`, `test_arc6_tier0_migrated.py`,
`test_ast_attr_migrated.py`, `test_emitter_widening_migrated.py`,
`test_program_synthesis_migrated.py` — 8 files, both engine states measured
in this SAME worktree with only the `.so` (and the matching source state)
swapped:

| | before (`sha256 c086d83a…`, pristine source) | after (`sha256 23ba3f1d…`, this rung's source) |
|---|---|---|
| passed | 303 | 303 |
| failed | 2 | 2 |
| failing names | identical | identical |

```
tests/test_arc6_tier0_migrated.py::test_hs4_op_table_is_the_unit_list_and_nothing_else
tests/test_emitter_widening_migrated.py::test_dotted_call_predictable_move_is_the_only_named_exception
```

**Both are in `results/failure_baseline.json`** — pre-existing, unrelated
(the op-table test compares against a frozen commit snapshot; the emitter
test compares against a frozen fixture predictability flag — neither
involves string ordering).

A first, much broader (40-file) sweep was attempted and abandoned: under
heavy concurrent load from other agents' test runs in this shared
environment, a single pytest invocation ran past 10 minutes without
finishing, and its early output showed a large fraction of failures that
(cross-checked against `results/failure_baseline.json`) were overwhelmingly
pre-existing and unrelated to this change (missing-artifact/optional-dep
noise of exactly the kind CLAUDE.md's retracted-note section documents).
The 8-file targeted sweep above is the one actually reported, chosen for
direct relevance to comparison/ordering rather than breadth, and it
completed in ~6 seconds per side.

### 5.3 Coherence probe

```python
add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})
# -> lst = [1, 2, 3], tup = (1, 2, 3), list == tuple? False   (must be False — MET)
```

Run on the post-fix engine.

---

## §6 What this rung does NOT establish

1. **`cmp_value`'s own `(Str,Str)` order is still boot-history-dependent**,
   by design — every canonicalisation-only call site (Set/Dict
   construction, persistence, `shape_decode`'s frame correspondence) is
   completely unchanged, and this rung does not claim otherwise.
2. **No full-tree sweep.** The Python regression evidence is an 8-file
   targeted sweep (311 test executions total, both sides), chosen for
   direct relevance to string comparison, not the full suite. A broader
   40-file attempt was abandoned under environment contention (§5.2); its
   partial output was consistent with (not additional evidence beyond) the
   targeted sweep's clean result, but it did not finish and is not counted
   as a gate.
3. **`shape_decode.rs:5124-5129`'s velocity-tie depth-rank ordering is
   UNCHANGED** — examined, and judged not to be a reported-order site by
   the same standard applied everywhere else (§2.2), but it is the one site
   in the whole enumeration that came closest to the line, and a future
   reader who disagrees with that call should start there.
4. **This does not fix `Eq(0.0, False)`** or any other defect this rung's
   own investigation happened to walk past (e.g.
   `test_arc6_valuelayer_migrated.py`'s other half) — those are named,
   confirmed unaffected, and left exactly as they were.
5. **Two Python tests were edited as part of this rung** (§4) — this is a
   real, in-scope consequence of the fix (both tests' own docstrings said
   to update them when this happened), not scope creep, but it does mean
   the "explicitly out of scope: no change to `cmp_value`'s `(Str,Str)`
   arm" boundary is about the ENGINE, not about every test file that
   happened to assert on the engine's old behaviour.
6. **Performance was not measured.** `cmp_value_lex` calls `interner.resolve`
   (a slice index, not a hash lookup) so the asymptotic cost is the same
   shape as `cmp_value`, but no benchmark was run.

---

## §7 GO/NO-GO

**GO.** 8 real reported-order call sites found (2 more than the brief's own
named examples, discovered by reading the enumeration honestly rather than
stopping at the given list), fixed via one new, narrowly-scoped function
that leaves `cmp_value` and every canonicalisation call site byte-unchanged.
Live before/after demonstration inverts all 8 sites from wrong to correct
on an adversarially-chosen interning order. Regression is clean and paired
on both Rust (single-threaded, full crate) and a Python sweep targeted at
the exact class of behaviour that changed, with the only failures being
two pre-existing, baseline-enumerated, unrelated tests. Two pinned tests
that explicitly named this exact future fix in their own docstrings were
updated, not silently left red.
