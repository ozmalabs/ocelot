# Wire-boundary systemic audit — RESULTS

Companion prereg: `WIRE_BOUNDARY_SYSTEMIC_AUDIT_PREREG.md`.

## 0. Headline

**`_wire`/`_unwire` were never a serialization format of their own — they
were a hand-authored, incomplete, drift-prone re-derivation of a codec
the engine already ships, complete, tested, and exposed to Python, and
never called.** `runners/dsl/src/py.rs` has two module-level
`#[pyfunction]`s, `encode(value)` / `decode(value)`, wired straight
through `py_to_value`/`encode_value`/`decode_value`/`value_to_py` — the
exact chain `set_attr`/`node()`/`add_node`/`evaluate()` already use for
every other graph attribute — registered in the Python extension
(`py.rs:10895-10896`) and re-exported at `substrate_rs.encode` /
`substrate_rs.decode` (`runners/dsl/python/substrate_rs/__init__.py:1182-1190`,
docstring: *"Same wire format as `substrate.persistence.encode`"*).
**Zero call sites in `domains/*.py` used it before this rung.** The fix
is not a fourth patch to the hand-rolled tag-matcher; it is retiring the
hand-rolled tag-matcher in favour of the primitive that was already
sitting there, per CLAUDE.md's own rule: *"Never 'primitive in
Python.'"*

## 1. Every wire-shaped serialization site found

Grep scope: `domains/*.py` for `_wire`/`_unwire`/`_plain`/`_flatten`
function definitions, plus every `inputs_json` reader/writer
(the concrete attr these functions exist to serve), plus a broader
`isinstance(v, (list, tuple))`-family sweep to rule out any missed
non-`_plain`-named sibling (`analogical_thinking.py`,
`audience_driven_production.py`, `implied_rule.py`, `mbpp_spec.py`,
`memory_shape_faculty.py`, `type_system.py` — all checked, none are
wire-boundary code: pattern-matching / anti-unification / type-inference
/ byte-sizing, unrelated to a JSON crossing).

| # | Site | Shape | Status found | Fix |
|---|---|---|---|---|
| 1 | `domains/prog_synthesis.py::_wire`/`_unwire` (was L876-957) | type-faithful round-trip codec for `inputs_json`/`expected` | 3 prior coverage gaps (frozenset, Fraction, non-string dict keys), still missing `Rational`/`Node`/`Surface` tags entirely | **Delegate to `substrate_rs.encode`/`decode`** |
| 2 | `domains/prog_moves.py::_wire`/`_unwire` (was L589-621) | explicitly-documented "duplicated in miniature" mirror of #1 | drifted: missing the non-string-dict-key `__dict__` tag fixed in #1 by `PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_RESULTS.md` — **the exact predicted "same bug class, different missing subset" failure, confirmed live** | **Delegate to `substrate_rs.encode`/`decode`** |
| 3 | `domains/prog_synthesis.py::_plain` (L2757+) | deliberately LOSSY comparator/display flattener (sets→sorted lists, Fraction→float) — NOT a round-trip codec | already fully patched (3 rungs); reference implementation | left as-is (see §3 for why this must NOT switch to `encode`/`decode`) |
| 4 | `domains/prog_retrieval.py::_plain` | thin delegator: `return psy._plain(v)` | correct — reuses the fixed original, does not reinvent | no fix needed; this is the pattern to imitate |
| 5 | `domains/prog_chunk_growth.py::_plain` | independent reinvention of #3, narrower | missing set/frozenset/Fraction (latent — call site is `trigger_tokens`, string-shaped in practice) | brought to parity with #3 |
| 6 | `domains/prog_ir_signature.py::_plain` | independent reinvention of #3, narrower | missing set/frozenset/Fraction (latent — call site is a statement's structural LGG signature, tuple/str/int-shaped in practice) | brought to parity with #3 |
| 7 | `domains/faculty_autogenesis.py::pump` (L28-31) | consumer of `inputs_json`, decode side | **bare `json.loads`, no `_unwire` call at all** — a tuple/set/non-string-keyed-dict-valued `FacultyNeed` example input would reach `ingest_spec` as its raw `{"__tuple__": [...]}` tag dict | now calls `prog_synthesis._unwire(...)` (module already imported, no new cross-import) |
| 8 | `domains/prog_property.py` (L318) | consumer of `inputs_json` | already correct: `psy._unwire(json.loads(...))` | no fix needed |
| 9 | `domains/prog_property.py` (L423) `ps_prop_witness_json` | write, `json.dumps(violations, default=str)` | deliberately lossy witness/log field (never read back and reconstructed) | no fix needed, correct as designed |
| 10 | `tests/test_prog_property_migrated.py::_add_row` (was L196-201) | **test fixture's own local row-writer**, bypassed `_wire` entirely (`json.dumps(inputs)` bare) | latent bug, MASKED by the old hand-rolled `_unwire`'s coincidental bare-array-as-list fallback; surfaced by switching #1 to the stricter engine convention — see §4 | fixed: apply `psy._wire` before `json.dumps`, matching production's `_add_example_row` |

Ten sites, four shapes of the same root defect: (a) an incomplete
hand-rolled encoder duplicated with independently-drifting coverage
(#1, #2); (b) a *different*, deliberately-lossy flattener independently
reinvented with the same incompleteness (#5, #6); (c) a decode site
that skipped the un-wire step altogether (#7); (d) a test-only shortcut
that skipped the wire step altogether (#10). #4, #8, #9 are the
counter-examples — already-correct reuse or already-correct
lossy-by-design — kept in the table to show the sweep did not stop at
the first hit.

## 2. The `Value` type-space audit

`runners/dsl/src/value.rs:46-105` — the `Value` enum, 13 variants:
`None, Bool, Int, Float, Rational, Str, Node, Tuple, List, Set,
FrozenSet, Dict, Surface`.

Two independent Rust-side codecs cover it **completely**, verified by
reading both to the closing brace, not by extrapolation:

- **`persist.rs::encode_value`/`decode_value`** (L25-249) — the
  checkpoint/JSON-tag format (`__nid__`, `__rational__`, `__tuple__`,
  `__list__`, `__set__`, `__fset__`, `__dict__`, `__surface__`; bare
  array/object are `Tuple`/string-keyed-`Dict` respectively). Every one
  of the 13 variants has an encode arm and a decode arm. This is the
  format `substrate/persistence.py` was ported *from* (`persist.rs`'s
  own module doc, line 1) and the format `substrate_rs.encode`/`decode`
  wrap.
- **`py.rs::py_to_value`/`value_to_py`** (L621-800) — the direct PyO3
  FFI conversion, no JSON step at all. Used by `set_attr` (L1802-1832,
  via `pydict_to_attrs`), `add_node`/`add_edge` (L1690+, same), and
  `evaluate()`'s return (L3066, `value_to_py(py, &v, &inner.interner)`)
  — i.e. **every graph attribute already round-trips through this,
  today, for free**, including `Fraction` (L636-644, matched by class
  name *before* the f64 fallback specifically to avoid losing
  exactness), tuple-vs-list (downcast order, L675-705), set/frozenset
  (L682-695), and dict with arbitrary hashable keys (L706-713, no
  string-only restriction — Python's own semantics).

**Empirically confirmed, not just read**, live in this worktree
(`substrate_rs.encode`/`decode` round-tripped `Fraction(9,2)`,
`(1,2,3)`, `[1,2,3]`, `{1:'x',2:'y'}`, `frozenset({1,2})`, `{5,6}` —
all exact, including through an intermediate `json.dumps`/`json.loads`
string hop) and cross-checked for **backward compatibility**: a
JSON string in the exact shape the OLD hand-rolled `_wire` used to
produce (`{"__tuple__": [...]}`, `{"__list__": [...]}`,
`{"__dict__": [[k,v],...]}`) decodes identically under the new
`_unwire` — every already-stored `inputs_json` string on disk or in a
checkpoint reads unchanged.

`_wire`/`_unwire`'s pre-fix coverage: `tuple`, `list`, `frozenset`,
`set`, `dict` (string and non-string keys). **Missing, always**:
`Rational`, `Node`, `Surface` — three of thirteen variants this
function silently could never have represented (a `Fraction` argument
value would have hit `return v` unchanged, then crashed at
`json.dumps` with `TypeError`, exactly the class of bug already fixed
once for the *output* side and never checked for the *input* side).
Switching to `substrate_rs.encode`/`decode` closes this for free — not
because anyone added a case, but because there was never a case to add;
the underlying primitive was already complete.

## 3. Why `_plain` (sites #3, #5, #6) does NOT switch to `encode`/`decode`

`_plain` and `_wire`/`_unwire` look similar (both flatten values for
JSON) and are NOT the same job. `_wire`/`_unwire` is a **faithful**
round-trip: whatever goes in must come back out identical in type and
value. `_plain` is **deliberately lossy**, by design, for exactly two
downstream comparators: `set`/`frozenset` → `sorted(list)` (so a
row-equality check across two independently-constructed sets stays
order-insensitive and correct) and `Fraction` → `float` (so every
numeric comparator in `prog_synthesis.py`, which already expects
`float`, never sees a second, drifting exact-numeric type it wasn't
built to compare against). Routing `_plain`'s call sites through
`substrate_rs.encode`/`decode` would **reintroduce exact types where
the comparators downstream were written assuming floats and sorted
lists** — the wrong fix, re-deriving the exact bug class `_plain`'s own
three prior patches (SETLIT/DICTITEMS, CEILING_REASSESSMENT_3) closed.
`_plain` stays hand-rolled, by design, and its two sibling copies (#5,
#6) were brought to *parity with the correct reference*, not switched
to the round-trip codec.

## 4. The test-fixture bug the refactor surfaced (not introduced)

First worktree run of the named 9-file suite (post-fix) showed **one**
new failure beyond the pre-existing baseline:
`test_prog_property_migrated.py::test_self_detected_wrongness_headline_36_of_36`
— 35/36 instead of 36/36, missing task 143.

Root cause, traced to source: task 143's own MBPP asserts
(`find_lists(([1,2,3,4],[5,6,7,8])) == 2`) pass a **tuple of lists**
as the argument — precisely the shape `_wire`/`_unwire` exists to
preserve, since `find_lists`'s reference implementation branches on
`isinstance(Input, list)`. But `tests/test_prog_property_migrated.py`'s
own local `_add_row` helper (a test-only row constructor, independent
of `prog_synthesis.py::_add_example_row`) wrote
`"inputs_json": json.dumps(inputs)` **directly, skipping `_wire`
entirely** — a bare, untagged JSON array, ambiguous by construction.

- Under the OLD hand-rolled `_unwire`, an untagged bare array decoded
  as a **list at every level** (its own explicit fallback,
  `if isinstance(v, list): return [_unwire(x) for x in v]`) — so the
  tuple-of-lists input silently arrived as a **list of lists**. Wrong,
  but the property happened to still fire (35/36→36/36 was a
  coincidence of which shape the reference relation was sensitive to,
  not a correct reconstruction).
- Under `substrate_rs.decode`, an untagged bare array decodes as a
  **Tuple at every level** (`persist.rs`'s own documented, deliberate
  convention: *"A bare JSON array still decodes as a Tuple"*) — so the
  same input arrived as a **tuple of tuples**. Also wrong, differently.

Neither reconstruction was the TRUE shape (a tuple of *lists*) —
because the true shape was never recorded in the first place; the test
helper threw the type information away before either decoder ever ran.
This was a **latent, pre-existing bug in the test fixture**, masked
for as long as the accidental "list of lists" reconstruction happened
to agree with what that one property check needed, and unmasked the
moment the decode convention changed underneath it.

**Fixed at the root**, not papered over: `_add_row` now calls
`psy._wire(inputs)` before `json.dumps`, matching production's own
`_add_example_row` exactly. Re-run: `test_prog_property_migrated.py`
**63/63 passed**, including the headline at true 36/36 — now firing
because the property genuinely holds over the *correct* tuple-of-lists
shape, not by the coincidence of a wrong flattening. This is recorded
as a genuine, if small, correctness improvement the refactor forced
into the open, not a defect the refactor introduced.

## 5. Full verification

**9-file named regression suite** (`test_prog_synthesis_battery_migrated.py`,
`test_mbpp_baseline_migrated.py`, `test_mbpp_endgame_migrated.py`,
`test_mbpp_contamination_migrated.py`, `test_mbpp_diet_migrated.py`,
`test_program_synthesis_migrated.py`, `test_prog_moves_migrated.py`,
`test_prog_property_migrated.py`, `test_exact_first_migrated.py`):

| | unmodified `main`@c1d0b4c | this worktree, post-fix |
|---|---|---|
| result | **3 failed, 241 passed** | **3 failed, 241 passed** |
| failing ids | `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`, `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`, `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift` | **identical set** |

Both runs measured fresh in this session (main-repo run used as the
"before" reference specifically to avoid a contaminated concurrent-edit
read on the worktree mid-fix — the worktree's own baseline attempt was
killed once this risk was noticed). All three failing ids are
pre-existing on unmodified `main` and untouched by this rung's files.

**MBPP endgame battery** (`scripts/mbpp_endgame_battery.py`, 257-task
test split, three arms):

| arm | before (`main`, copied artifact) | after (this worktree, freshly run) |
|---|---|---|
| full | 69/257 | **69/257**, `det_identical=True` |
| content_stripped | 68/257 | **68/257**, `det_identical=True` |
| official | 98/257 | **98/257**, `det_identical=True` |

Required floor (69/68/98 or better, never lower): **held exactly**.

**One recorded, understood, non-regressing side effect**: task 124
(`angle_complex`, MBPP prompt uses a literal `1j` complex-number
argument) moved from `runner_exception:TypeError` to
`runner_exception:ValueError` in the taxonomy — `k` (pass count)
unchanged in all three arms. Cause: Python `complex` has **no
representation in the `Value` enum at all**, in either codec, before or
after this rung — `_wire`'s old fallthrough (`return v` unchanged) let
a raw `complex` reach `json.dumps`, which raises `TypeError`;
`substrate_rs.encode` calls `py_to_value` in Rust, which has no match
arm for `complex` and returns `PyValueError` (`ValueError` in Python).
Same non-runnable outcome under both codecs — this task was never
going to run either way. Recorded honestly, not silently absorbed;
**adding a `Value::Complex` variant is explicitly out of scope for this
rung** (zero MBPP tasks need it beyond this one already-unsolvable
prompt, and CLAUDE.md's frame/continuum invariant would need its own
design pass for what a complex value even means in-frame).

**Isolated file-level regressions**, all green:
`test_arc6_lit_wire_migrated.py` (12/12 — the original `Lit`-boundary
list/tuple fix's own pin, confirms `_wire`'s callable/behavioural
contract untouched), `test_faculty_autogenesis_migrated.py` (3/3),
`test_prog_chunks_migrated.py` + `test_prog_constructions_migrated.py`
+ `test_two_novel_orbits_third_grain_migrated.py` (24 passed, 1
skipped — exercise `prog_chunk_growth`/`prog_ir_signature`),
`test_prog_property_migrated.py` (63/63, including the fixed
headline). `test_retrieval_ceiling_migrated.py`'s one failure
(`test_q5_failure_coverage_ids_are_a_subset_of_q5_failures`) was
independently confirmed to fail identically on unmodified `main`
(stale cross-artifact fixture, unrelated to this rung — not a file this
rung touched or a symptom this rung's mechanism could cause) and is
excluded from the named regression set for that reason, not omitted
silently.

## 6. Pricing the two design options, honestly

**Option A — reuse `persist.rs`/`py.rs`'s existing codec.** This is
what was built. Cost: **zero new Rust code** (the primitive existed,
compiled, and was already load-bearing for every other attr on the
graph — confirmed by reading its call sites in `py.rs`, not assumed).
Python-side cost: two functions in `prog_synthesis.py` and
`prog_moves.py` reduced to one-line delegators, two `_plain` siblings
extended by ~10 lines each for parity, one missing `_unwire` call
added, one test-fixture bug fixed at its root. Total diff: 7 files,
+228/-101 lines, no test infrastructure changes, no on-disk format
change (verified byte-for-byte backward compatible in §2). This is the
"reuse" side of the investigation's own question, and it was a
genuine, substantial YES: the codec was not merely *similar enough to
reuse*, it was **strictly more complete** than every hand-rolled copy
found, in every case.

**Option B — build a richer binary/native wire format as the primary
representation, JSON as a derived view.** Priced, not assumed: this is
**already what exists**. `persist.rs`'s tagged-JSON format is not a
"json convenience layer bolted onto a richer native format elsewhere"
— reading `graph_to_dict`/`graph_from_dict` and their call sites shows
JSON-with-tags **is** the graph's actual persisted form (`substrate/
persistence.py`'s own original design, ported to Rust unchanged). The
*actually* richer, non-JSON representation the user's instinct was
reaching for **already exists too** — it is `py.rs::py_to_value`/
`value_to_py`, the direct PyO3 FFI path, which is genuinely native
(no JSON step, no string parse, no tag dict allocation) and is what
every `set_attr`/`node()`/`evaluate()` call already uses. Building a
*third*, purpose-built binary format (e.g. a length-prefixed byte
encoding) on top of these two would add a serialization surface with
**no consumer that doesn't already have a faster, more direct option**
— `set_attr` already gets native-speed, zero-copy-ish PyO3 conversion,
and disk/checkpoint persistence already gets a complete, portable,
debuggable JSON-tag format. There is no third boundary this rung's
audit found that needs a third representation. **Priced honestly: this
is not "smaller than it looks" (it doesn't need building) or "bigger
than it looks" (there's no unmet need it would fill) — it is
NOT-NEEDED, because the two things it would provide (completeness,
native speed) are each already provided, separately, by the two
existing mechanisms, for the two different jobs (durable storage vs.
in-process crossing) that actually exist.**

## 7. GO / NOT-YET-READY call

**GO — built, in full, this session.** The buildable first slice named
in the task ("make `prog_synthesis.py` and any sibling copies USE
[the existing complete format] instead of reinventing their own lossy
flattener") turned out to be exactly the right size once measured: not
a large refactor (no on-disk format change, no call-site signature
change, no new Rust), and not a trivial one either (it required
tracing the real root cause of one new test failure through three
layers of indirection to confirm the fix was correct rather than
convenient). Everything named as "in scope" in the task prompt is
landed: the sweep (§1), the type-space cross-reference (§2), the
lossy-vs-faithful distinction that keeps `_plain` correctly unchanged
(§3), the pricing of both design options (§6), and a working,
regression-tested fix (§5).

**Not done, named honestly:**
- The remaining ~150-candidate-wide sweep this session's own
  `SHAPE_AUDIT.md` ran for *rule* shapes was not re-run for *wire*
  shapes outside `domains/*.py` — `scripts/*.py` and `tools/*.py` were
  not swept (out of scope: those are one-off authoring/capture tooling
  per CLAUDE.md, not agent runtime, and the task's own file list named
  `domains/prog_synthesis.py` and siblings specifically).
- `Value::Complex` is a real, tiny, honestly-out-of-scope gap named in
  §5 — one MBPP task (124) needs it and no mechanism in this codebase
  can express it; not sized or built here.
- `test_retrieval_ceiling_migrated.py`'s pre-existing, main-inherited
  failure (§5) was diagnosed as unrelated but not fixed — it belongs
  to whichever rung owns `mbpp_arc3_ceiling`'s artifact-freshness
  contract, not this one.

## 8. What this does not establish

- That every wire-shaped site in the *entire* repository (beyond
  `domains/*.py`, `tests/*.py` touching `inputs_json`, and the named
  Rust files) is now free of this defect class — the sweep was real
  and multi-pass, not exhaustive over every file in the tree.
- That `Value::Complex` (or any other future numeric extension) is
  unneeded going forward — only that it is unneeded by the 257-task
  MBPP corpus this rung measured against.
- That test-fixture helpers elsewhere in the suite don't have their
  own version of the exact bug found and fixed in §4 — only that the
  one this rung's own regression run surfaced was found and fixed.
- Anything about `runners/dsl/src/synth_enumerate.rs` or
  `SynthSpecShape`/`SynthOp` — untouched, per the sibling
  Γ-admissibility rung's declared territory (confirmed by `git diff
  --stat` against `main` before commit: only the 7 files listed in
  §5's table, no Rust files touched at all).

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/wire-boundary-audit
git log --oneline -1   # c020be5, on top of main @ c1d0b4c
ln -sfn /home/matt/ozmadev/ocelot/data data   # if not already symlinked

PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q

PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

Note: `results/*.json` battery artifacts are untracked build output
(not in git) — a fresh worktree needs them copied from an existing run
or regenerated via the battery script before the artifact-reading test
modules (`test_mbpp_baseline_migrated.py`,
`test_mbpp_endgame_migrated.py`, etc.) will collect without
`FileNotFoundError`; this is orthogonal to the wire-boundary fix
itself.
