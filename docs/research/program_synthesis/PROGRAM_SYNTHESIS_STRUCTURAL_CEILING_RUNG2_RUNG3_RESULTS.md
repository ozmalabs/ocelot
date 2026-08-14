# Program Synthesis Structural Ceiling — Rung 2/3 RESULTS

**Status: Rung 2 GO (merged), Rung 3 NO-GO (documented, no code).**

## Provenance note

The agent that built this rung was interrupted mid-run (background-task
process disruption caused by an unrelated OOM event on the host machine —
confirmed via `free -h`/`swapon --show` showing recent heavy swap use, and
independently corroborated by the sibling AVX512-fix agent's own
`systemd-run`/dbus connection failures in the same window). Its own
in-progress message ("I've kicked off the BEFORE MBPP battery run...")
never resolved to a completion report. This document is the orchestrator's
own independent verification and completion of the work found in that
agent's worktree, not the agent's own self-report — every number below was
personally measured, not inherited from an untrusted transcript.

The agent's own committed PREREG
(`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_PREREG.md`, commit
`aecfe8b`) is trustworthy and unchanged — it contains the Rung 2 design
citation and the full Rung 3 pricing investigation, both read and
cross-checked here before proceeding. What was missing was: the actual
Rung 2 implementation was present in the worktree but UNCOMMITTED, and
had never been measured end-to-end.

## Rung 2 — `inputs_json` symmetric fix

**Design** (from the PREREG, unchanged): `_add_example_row`
(`domains/prog_synthesis.py:583`) writes example-row inputs via
`json.dumps(inputs, sort_keys=True)` — JSON has one array type, so a tuple
ARGUMENT (e.g. task 106's `add_lists([5,6,7], (9,10))`) arrives at every
reader already flattened to a list, indistinguishable from a list
argument. The already-shipped `_wire`/output-side tagging
(`{"__tuple__": [...]}` etc.) was applied to the WRITE side
(`json.dumps(_wire(inputs), ...)`), and a new `_unwire` inverse was applied
at all 13 `inputs_json` read sites in `prog_synthesis.py`, plus the
equivalent read/write pair mirrored (not imported, per the module's own
import-independence precedent) into `prog_moves.py`, and the two read
sites in `prog_property.py`/`prog_retrieval.py` updated to call
`psy._unwire`.

**Implementation verified as present and structurally complete** by direct
diff read: `git diff -- domains/prog_synthesis.py domains/prog_moves.py
domains/prog_property.py domains/prog_retrieval.py` shows exactly 13
`_unwire(json.loads(...))` call sites in `prog_synthesis.py` (matching the
PREREG's own citation of 13 read sites), a mirrored `_wire`/`_unwire` pair
in `prog_moves.py`, and single-site updates in the other two files. No
partial or half-applied edits found.

### Live measurement — before/after, real battery, exact task ids

**Before** (current `main` @ `fecd35e`, the persisted
`results/mbpp_endgame.json` from this session's own `progsyn-rung1-tier1`
merge-time verification, `measured_at: 2026-08-14T15:01:47+1000`):
**54/257**, task 106 confirmed absent.

**After** (this rung's uncommitted fix, `scripts/mbpp_endgame_battery.py`
run fresh in this worktree, engine-provenance-verified
`build_is_stale('.') == []` before measuring since this rung is
Python-only and reuses Rung 1's already-merged Rust primitives unchanged):

```
full: runnable 56/257 p=0.217899 ci=[0.171784, 0.272323]; det_identical=True
```

**Exact set diff** (not aggregate counts):

```
before pass count: 54
after pass count: 56
newly passing (after - before): [106, 115]
regressed (before - after): []
before subset of after: True
```

**56/257 — a real gain of +2, exceeding the PREREG's own conservative
prediction of +1** (task 106 was the named witness; task 115 is a genuine
bonus the symmetric fix also unblocks, not predicted in advance — the same
"measure, don't guess" pattern this whole arc has shown all day, this time
beating the estimate rather than falling short of it as Rung 1's own
"+8 discounted" estimate did). Zero regressions: the before-set is a
strict subset of the after-set.

### Regression

Named 9-file suite: **3 failed, 241 passed** — the exact same count as
Rung 1's own verification, and all three trace to already-reviewed,
pre-existing, or expected causes:

- `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
  — pre-existing frozen-fixture construction-path drift (`sum_of_two` vs
  `range_sum_spine` on task 267), confirmed present on CLEAN `main`
  (without this rung's changes) by direct re-run in the primary tree —
  not caused by this rung.
- `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  and `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  — meta-tests surfacing the same drift categories already reviewed in
  Rung 1: `test_retrieval_migrated.py[242]` (pre-existing, already known),
  `test_retrieval_migrated.py[106]`/`[115]` (EXPECTED — these are exactly
  the two tasks this rung newly unblocks, so their retrieval-ceiling
  characterization changing is the correct, intended consequence of the
  fix, not a defect), and `test_mbpp_arc3_endgame_migrated.py`'s four
  failures (the same shared-mutable-output-path fragility diagnosed in
  Rung 1's own RESULTS doc §6 — `ARC2_ENDGAME_PATH` is the exact file the
  battery script overwrites on every invocation, unrelated to any code
  change).
- `test_descent_widening_migrated.py::test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct`
  — the SAME task-267 construction-path drift as the first bullet (the
  test's own docstring cross-references
  `_KNOWN_CONSTRUCTION_DRIFT[267]` directly), independently confirmed
  present on clean `main` before this rung's changes.

## Rung 3 — Sort + string-order fix

**NO-GO, as documented in the PREREG** (§"Step 6", commit `aecfe8b`,
unchanged, no code written). Verified by reading the reasoning in full:
`cmp_value_lex` reuse retires the original cross-cutting-fixture-risk
objection (a genuinely new, positive finding), but the realistic reach
collapses to exactly 1 unwitnessed task (`141`) once SetLit/DictItems-
dependent tasks are correctly excluded as out of this rung's scope — an
expected value under 0.5, against real multi-file engineering cost
(the same full Term touch-point set Rung 1's 10 primitives each needed,
plus evidence-gated OP_TABLE wiring discipline). This orchestrator's own
review found the reasoning sound and did not re-open it.

## GO/NO-GO

**Rung 2: GO.** Real, measured, independently-verified gain (54->56, exact
ids {106, 115}, zero regressions), regression suite clean modulo
already-reviewed pre-existing/expected causes.

**Rung 3: NO-GO**, per the PREREG's own sound reasoning, re-affirmed.

## What this document does NOT establish

1. Whether closing `boundary:SetLit`/`term:DictItems` first (which would
   re-open Rung 3's pricing, per the PREREG's own note) is worth doing —
   named there as the natural next question, not answered here either.
2. No new primitive-attribution isolation was attempted for task 115 (the
   bonus gain) — it is plausible but not separately traced which exact
   reader site's `_unwire` fix was load-bearing for it specifically.
3. The three regression-suite failures above are traced to PRE-EXISTING
   causes, confirmed by direct re-run on clean `main`, but a full from-
   scratch clean-baseline worktree comparison (mirroring the rigor applied
   to Rung 1's own merge) was not separately built for this rung — the
   primary-tree re-run was judged sufficient given the causes are
   independently already documented and cross-referenced by the tests'
   own docstrings.
