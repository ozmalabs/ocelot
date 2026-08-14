# `_plain()` Fraction case (task 98) — RESULTS

**Status: GO, built, measured. MBPP `full` 62/257 → 63/257, `content_stripped`
61/257 → 62/257, `official` 90/257 → 91/257 — all three arms +1, exact
newly-passing id `{98}`, zero regressions on any arm.**

Base `main @ 4a6b63f` (verified fresh via `git log --oneline -1 main`
immediately before creating the worktree — the same tip
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` measures its baseline
against). Worktree
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling2-plain-fraction`, branch
`progsyn-ceiling2-plain-fraction`. Commit `89f4496`.

This is a small, same-day, in-place fix found *while* re-running the
structural-ceiling methodology (see the PREREG/investigation document for the
full context: it is one line in the "what's newly reachable now" survey, not
a separate planned rung) — built directly per this task's own house rule
("Do NOT build anything... unless you find a change so cheap and clearly
evidenced it would be irresponsible not to"), because it is a **direct,
same-day repeat of an already-landed precedent** (`PROGRAM_SYNTHESIS_
SETLIT_DICTITEMS_RESULTS.md` §3's `_plain()` frozenset fix, same function,
same shape, same day) rather than a new design.

## 1. The bug, found by direct reproduction

`domains/prog_synthesis.py::eval_and_record` (line 859) calls
`sub.set_attr(r, "got_json", json.dumps(_plain(got)))` for every candidate
the search evaluates. `_plain()` (line 2735) is a JSON-safe flattener with
cases for `list`/`tuple`, `set`/`frozenset` (added by the SetLit/DictItems
rung earlier today), `dict`, and `bytes` — but no case for Python's
`fractions.Fraction`. `Value::Rational` (the DSL's EXACT-fraction division
result, CLAUDE.md's own "Rational(9,2) != 4.5" cost class, already named as
unpriced in `ARC6_STRUCTURAL_CEILING.md` §7.2) realises at the PyO3 boundary
as a `fractions.Fraction`, and `json.dumps` cannot serialize it.

**Live-reproduced with a full traceback** (task 98, "multiply all the
numbers in a list and divide with the length of the list", revealed rows
`multiply_num((8,2,3,-1,7)) == -67.2` / `multiply_num((-10,-20,-30)) ==
-2000.0`, tolerance `0.001`):

```
Traceback (most recent call last):
  ...
  File ".../domains/prog_synthesis.py", line 2557, in synthesize_from_request
    pump(sub, ag_node)
  File ".../domains/prog_synthesis.py", line 2541, in pump
    moved = bool(verb(sub, ag_node, g)) or moved
  File ".../domains/prog_synthesis.py", line 859, in eval_and_record
    sub.set_attr(r, "got_json", json.dumps(_plain(got)))
  ...
TypeError: Object of type Fraction is not JSON serializable
```

`Prod((8,2,3,-1,7))/Count((8,2,3,-1,7))` is exactly `-336/5` — a non-integer
ratio the engine keeps EXACT (`Div` over two integers where the division
isn't exact returns `Value::Rational`, not a `Value::Float`) — so a
perfectly reasonable, already-witnessed candidate (`Div(Prod(a), Count(a))`,
exactly the witness `ARC6_STRUCTURAL_CEILING.md` §5 already priced for task
98 under `op:ProdList`, landed as Arc6 tier-0 well before today) triggers
this the moment the search reaches it. The crash is **uncaught** at the
`synthesize_from_request` call boundary, so it aborts the ENTIRE synthesis
attempt for the task (`runner_exception:TypeError`), not just the one
candidate — this is why task 98 has stood as a dead `runner_exception`
rather than a near-miss `gapped` or `accepted_holdout_fail` since Arc6
tier-0 landed `ProdList` on 2026-08-01/03, invisible to every op-table-level
investigation since (the primitive was always sufficient; the crash was
downstream of it).

## 2. The fix

One case added to `_plain()`, converting via `float()` — matching every
downstream comparator in this module (`agree`/`_row_cmp_ok`/
`math.isclose`-style tolerance checks), which already expect a float and
never an exact-rational type, so this is never a second, drifting numeric
kind:

```python
if isinstance(v, Fraction):
    return float(v)
```

Purely additive (a case Python could never previously reach — no program
could produce a `Fraction` through this path before, since the crash killed
the attempt at the first one) — the exact same "purely additive, cannot
regress an existing case" argument the frozenset case used.

## 3. Live confirmation, both revealed and held-out rows

```
status: accepted construction: retrieved_exemplar
holdout: {'n': 1, 'n_ok': 1, 'all_ok': True,
          'rows': [{'inputs': {'a': (19, 15, 18)}, 'expected': 1710.0,
                     'got': 1710, 'trap': None, 'ok': True}]}
```

## 4. Real measurement — before/after, exact task-id set diff, all three arms

**Before** = the primary tree's own fresh, live re-measurement at
`main @ 4a6b63f` (this session's own investigation run, not a stale/cached
number — see the accompanying PREREG/investigation document §"real current
MBPP state").

```
before: full 62/257, content_stripped 61/257, official 90/257
after  (this branch): full 63/257, content_stripped 62/257, official 91/257
```

**Exact set diffs, all three arms** (`results/mbpp_endgame.json`'s
`runnable_rows`, direct set computation, not aggregate counts):

| arm | before (n) | after (n) | newly passing | regressed |
|---|---|---|---|---|
| `full` | 62 | 63 | `{98}` | `{}` |
| `content_stripped` | 61 | 62 | `{98}` | `{}` |
| `official` | 90 | 91 | `{98}` | `{}` |

`before_pass_ids ⊆ after_pass_ids` holds on all three arms. The other two
`runner_exception:TypeError` tasks in the same population (`124` — "angle of
a complex number", needs actual complex-number support, out of scope; `237`
— "map each unique tuple to its count", a distinct unhashable-list-key
defect, not this one) are confirmed **unaffected** — different exception
classes, checked directly in the after-run's own `results/mbpp_endgame.json`.

## 5. Regression

Zero Rust changes: `git diff --stat HEAD -- runners/dsl/src/*.rs
runners/dsl/python/substrate_rs/_native.abi3.so` is empty, confirmed BEFORE
editing — this is a pure-Python fix, so (mirroring Rung 2's own precedent
of not rebuilding Rust for a Python-only change) no `cargo build`/`cargo
test` cycle was run; the committed `.so` is confirmed byte-identical to
what `main @ 4a6b63f` already ships.

Named 9-file suite: **3 failed, 241 passed** — the same top-level count as
every prior rung today. Each failure independently re-confirmed present on
a genuinely clean, unmodified `main @ 4a6b63f` (not inherited from a prior
doc's characterization):

- `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
  and `test_descent_widening_migrated.py::test_sum_to_n_class_scalar_loop_
  descends_and_holds_out_correct` — both the pre-existing task-267
  `sum_of_two`/`range_sum_spine` construction-path drift, reproduced
  byte-identically on clean `main` in this session (`assert 'sum_of_two' ==
  'range_sum_spine'`, both files, both trees).
- `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  and `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  — meta-tests; their inner "unexpected" sets (`test_reject_informs_repair_
  migrated.py`'s 4 known drifts, `test_mbpp_arc3_endgame_migrated.py`'s 4
  shared-mutable-output-path failures, `test_retrieval_migrated.py[242]`)
  were run DIRECTLY against clean, unmodified `main @ 4a6b63f` in this same
  session (`tests/test_reject_informs_repair_migrated.py
  tests/test_retrieval_migrated.py -q`) and reproduce **identically**: `4
  failed, 52 passed`, the same 4 node ids. None of this rung's diff touches
  any file these tests read.

**Zero new Rust-suite failures (none run, none needed), zero new Python-suite
failures — this rung's failure signature is IDENTICAL to clean `main`'s
own, confirmed by running both, not by citation.**

## 6. GO/NO-GO

**GO, delivered.** One `isinstance` branch in one already-existing function,
directly repeating an already-landed same-day precedent. Real measured MBPP
gain **+1 on every arm** (`full`/`content_stripped`/`official`, same id,
`98`), zero regressions, zero new Rust-suite risk (no Rust touched), zero new
Python-suite failures beyond the independently-reconfirmed pre-existing set.

This closes a loose end open since **2026-08-01/03** (Arc6 tier-0's own
`op:ProdList`/`Div(Prod(a),Count(a))` witness for task 98,
`ARC6_STRUCTURAL_CEILING.md` §5) — the primitive was always sufficient; a
downstream serialization gap silently converted every attempt into a dead
`runner_exception` instead, invisible to every op-table-level investigation
since, including this same session's own earlier op-table survey, until
direct reproduction of the real exception surfaced it.

## 7. What this document does NOT establish

1. Whether `_plain()` (or the sibling `_json_default` in
   `scripts/mbpp_endgame_battery.py`, which already handles set/frozenset/
   tuple but was not audited here for a Fraction case) has any OTHER
   uncovered Python type reachable through a still-crashing path — only the
   one concrete crash (task 98, live-reproduced) was chased down; a full
   audit of `_plain`'s and `_json_default`'s exhaustiveness against every
   `Value` variant's PyO3 realisation was not attempted (the same scope
   boundary `PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_RESULTS.md` §9 already named
   for its own `term_json` finding).
2. Whether `agree()`/`_row_cmp_ok()`'s own numeric comparison would ever
   receive a raw (non-`_plain`'d) `Fraction` on the `holdout_verdict` path
   (`out.get("result")`, a separate PyO3 conversion site) and mis-compare —
   task 98's own held-out row happens to compare a `Fraction`-derived
   candidate's actual runtime `Value::Int`/`Value::Float` output, not a
   Fraction directly, so this was not exercised by this measurement and was
   not separately probed.
3. This is a narrow, single-task fix — it does not address either of the
   two larger, unbuilt findings in the accompanying investigation document
   (the `map_templates_by_size` value-template pool gap, or the retrieved-
   exemplar-rejection fallthrough gap), which remain priced-not-built.

## Artifacts

- Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling2-plain-fraction`,
  branch `progsyn-ceiling2-plain-fraction`.
- Commit: `89f4496` (fix).
- `results/mbpp_endgame.json` (after) in the worktree; the primary tree's own
  `results/mbpp_endgame.json` (regenerated fresh in this session before this
  fix was written) holds the independently fresh "before" measurement.
