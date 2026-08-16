# Measured-residual filing — RESULTS (Proposal 3 of DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md §4)

**Date:** 2026-08-16. Worktree `measured-residual-filing`, branched from
`main @ f4394fd` (re-verified fresh immediately before branching). Follows
`MEASURED_RESIDUAL_FILING_PREREG.md` — every prediction there is checked
below against literal output, not description.

---

## 0. Headline

**All 5 falsifiable predictions in the PREREG held, live, against the real
`results/mbpp_endgame.json` artifact (88/67/60/17/14/5/3/1/1/1) — 9 of its 10
outcome buckets minted exactly one `SelfConcern{kind:'engineering_residual'}`
each (the `pass` bucket correctly minted none), re-ingesting the identical
taxonomy produced zero duplicates, zeroing a population's count retired
exactly that population's concern and left the other 8 live, and both
`reflective_faculty._run_self_gaps` and a live `WorldAdapter.converse("what
gaps do you have?")` surfaced all of it with ZERO changes to
`reflective_faculty.py`.**

**One real defect was found and fixed during this rung, not before it:**
the first version of the cross-run persistence path used a raw
`graph_to_dict`/`graph_from_dict` round-trip and the retire rule
*measurably* stopped firing after one save/reload cycle. Root cause,
confirmed by reading the saved JSON directly: `graph_to_dict()` serialises
only `{nodes, edges, next_id}` — **no `rules` key** — so a naive reload
silently drops every `Rule` node. This is the exact checkpoint-resume
rule-loss residual CLAUDE.md already names for the real jabberwock daemon
(`_reconcile_seed_rules`), reproduced independently here and caught by this
rung's own live-verify rather than shipped silently. Fixed by always
reloading via a fresh `load_all_seeds` boot (rules always current) and
RECONCILING only the persisted `EngineeringResidual`/`SelfConcern` data on
top, by content — see §2.

**Proposal 3's mechanism (d)** — a `prog_read` `SelfConcern` reaching
`promote_self_concern` and closing through `_process_prog_read_standing` —
**was already landed in the baseline** (`0e62166`/`4563c3a`, "ARC6 A25"),
before this rung started. Verified still green as part of the regression
gate (§4); not re-implemented.

**Regression gate: 11 pre-existing failures, present byte-identically on
BOTH this worktree and a freshly-checked-out, completely unmodified
`main @ f4394fd`** — measured directly, not assumed (§4). Zero new
regressions from this change.

---

## 1. Live verification — the diagnostic-script wiring, against real data

`domains/engineering_residual_ingest.ingest_taxonomy` called with the REAL
`results/mbpp_endgame.json` `arms.full.outcome_taxonomy` (copied from the
actual repo checkout into this worktree — `results/*` is gitignored, so this
is real prior measurement output, not fabricated):

```
== real taxonomy buckets ==
  pass 88
  gapped:enumerate_failed 67
  accepted_holdout_fail 60
  gapped:property_verdict_reject 17
  gapped:structural_verdict_reject 14
  gapped:exhausted 5
  gapped:no_shape 3
  not_recognized 1
  runner_exception:ValueError 1
  runner_exception:TypeError 1
```

**Prediction 1 (exactly 9 concerns, none for `pass`) — HELD:**

```
== SelfConcerns after ingest #1 == 9
  {'content': 'mbpp_endgame_battery.full:gapped:enumerate_failed', 'status': 'noted', 'count': 67}
  {'content': 'mbpp_endgame_battery.full:accepted_holdout_fail', 'status': 'noted', 'count': 60}
  {'content': 'mbpp_endgame_battery.full:gapped:property_verdict_reject', 'status': 'noted', 'count': 17}
  {'content': 'mbpp_endgame_battery.full:gapped:structural_verdict_reject', 'status': 'noted', 'count': 14}
  {'content': 'mbpp_endgame_battery.full:gapped:exhausted', 'status': 'noted', 'count': 5}
  {'content': 'mbpp_endgame_battery.full:gapped:no_shape', 'status': 'noted', 'count': 3}
  {'content': 'mbpp_endgame_battery.full:not_recognized', 'status': 'noted', 'count': 1}
  {'content': 'mbpp_endgame_battery.full:runner_exception:ValueError', 'status': 'noted', 'count': 1}
  {'content': 'mbpp_endgame_battery.full:runner_exception:TypeError', 'status': 'noted', 'count': 1}
```

**Prediction 2 (re-ingest identical taxonomy → zero new concerns) — HELD:**
`== after re-ingest (dedup check): still 9 ==`

**Prediction 3 (zeroing `accepted_holdout_fail` retires only that
population) — HELD:**

```
== after zeroing accepted_holdout_fail ==
  live: 8 retired: 1
  RETIRED: {'content': 'mbpp_endgame_battery.full:accepted_holdout_fail', 'status': 'retired', 'count': 60}
```

**Prediction 4 (`_run_self_gaps` surfaces the 8 live ones, zero code change
to `reflective_faculty.py`) — HELD:**

```
== _run_self_gaps ==
{
 "self_gaps": true,
 "count": 9,
 "concerns": [
  {"content": "core boot integrity is compromised; inspect the linked seed-load evidence",
   "kind": "boot_integrity", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:gapped:enumerate_failed", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:gapped:property_verdict_reject", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:gapped:structural_verdict_reject", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:gapped:exhausted", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:gapped:no_shape", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:not_recognized", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:runner_exception:ValueError", "kind": "engineering_residual", "source": "implicit", "status": "noted"},
  {"content": "mbpp_endgame_battery.full:runner_exception:TypeError", "kind": "engineering_residual", "source": "implicit", "status": "noted"}
 ], ...
}
```

(The `boot_integrity` concern is pre-existing baseline behaviour — 8
unrelated seeds fail to load in this environment regardless of this change,
see §5 — not something this rung introduced or investigated further; it is
reported here only because it appears in the same `_run_self_gaps` output.)

**Prediction 5 (a real conversational turn surfaces it) — HELD, literal
transcript:**

```
== converse('what gaps do you have?') ==
I currently hold 9 gaps I've flagged about myself (9 implicit): (1) "core
boot integrity is compromised; inspect the linked seed-load evidence"
(boot_integrity); (2) "mbpp_endgame_battery.full:gapped:enumerate_failed"
(engineering_residual); (3) "mbpp_endgame_battery.full:gapped:property_verdict_reject"
(engineering_residual); (4) "mbpp_endgame_battery.full:gapped:structural_verdict_reject"
(engineering_residual); (5) "mbpp_endgame_battery.full:gapped:exhausted"
(engineering_residual); (6) "mbpp_endgame_battery.full:gapped:no_shape"
(engineering_residual); (7) "mbpp_endgame_battery.full:not_recognized"
(engineering_residual); (8) "mbpp_endgame_battery.full:runner_exception:ValueError"
(engineering_residual); (9) "mbpp_endgame_battery.full:runner_exception:TypeError"
(engineering_residual).

ALL PREDICTIONS HELD
```

---

## 2. The persistence bug, found and fixed live

**First attempt (WRONG, corrected in this rung):**
`load_or_boot_residual_substrate` did `srs.Substrate()` +
`s.graph_from_dict(checkpoint)` on a reload. Cross-process test:

```
run1: ingest 10 populations, save checkpoint (accepted_holdout_fail count=60)
run2 (separate python process): reload checkpoint, re-ingest with
     accepted_holdout_fail count=0
run3 (separate python process): reload checkpoint, check retire status
  -> after second (cross-process) ingest: live= 9 retired= 0    *** WRONG ***
```

Root cause, confirmed by reading the saved file directly:

```python
>>> json.load(open('results/engineering_gaps_substrate.json')).keys()
dict_keys(['edges', 'next_id', 'nodes'])   # NO 'rules' key
```

`Substrate.graph_to_dict()` does not serialise Rule nodes at all, so a raw
`graph_from_dict` reload restored the DATA (the `EngineeringResidual`
count=0) but silently dropped `retire_resolved_engineering_residual_gap`
itself — it could never fire again.

**Fix:** `load_or_boot_residual_substrate` now ALWAYS boots fresh via
`WorldAdapter(seeds=()) + load_all_seeds(...)` (rules always current), then
`_reconcile_residual_state` re-materialises only the persisted
`EngineeringResidual` facts and `engineering_residual`-kind `SelfConcern`s
from the checkpoint, by content, mapping old node ids to newly-allocated
ones — the `_reconcile_seed_typed_nodes` find-or-create-by-content
precedent CLAUDE.md already documents for the real daemon's own resume path,
scoped to the two node types and three edge types this seed's rules read.
`save_residual_substrate` was correspondingly narrowed to persist only that
same small subset (not a full-graph `graph_to_dict()`, which would be
redundant with the fresh boot and would bloat the file).

**Re-run after the fix, three separate Python processes:**

```
=== run 1 ===
ingested engineering residuals: 10 populations -> .../results/engineering_gaps_substrate.json
run1 upserted 10
=== checkpoint after run 1 ===
19 nodes 28 edges
=== run 2: separate process, zero out accepted_holdout_fail ===
ingested engineering residuals: 10 populations -> .../results/engineering_gaps_substrate.json
run2 upserted 10
=== run 3: separate process, verify retire persisted ===
live= 8 retired= 1
 RETIRED: mbpp_endgame_battery.full:accepted_holdout_fail
surfaced engineering_residual gaps: 8
```

Cross-process retirement now works correctly. Checkpoint size: 19 nodes /
28 edges (10 `EngineeringResidual` + 9 `SelfConcern`, their
`has_engineering_residual`/`has_self_concern`/`about_residual` edges) — the
"small, dedicated" persisted graph the design intends, not a full-agent
checkpoint.

**Multi-script coexistence, verified live (no cross-contamination):**
ingesting `mbpp_endgame_battery.full`'s 9-bucket taxonomy and
`ceiling3_diag_sweep`'s synthetic 3-bucket smoke taxonomy into the SAME
checkpoint produced exactly 12 distinct `population_key`s, correctly
namespaced by `source_script`:

```
=== combined surface ===
total engineering_residual gaps: 12
  ceiling3_diag_sweep:gapped:enumerate_failed
  ceiling3_diag_sweep:accepted_holdout_fail
  ceiling3_diag_sweep:not_recognized
  mbpp_endgame_battery.full:gapped:enumerate_failed
  mbpp_endgame_battery.full:accepted_holdout_fail
  mbpp_endgame_battery.full:gapped:property_verdict_reject
  mbpp_endgame_battery.full:gapped:structural_verdict_reject
  mbpp_endgame_battery.full:gapped:exhausted
  mbpp_endgame_battery.full:gapped:no_shape
  mbpp_endgame_battery.full:not_recognized
  mbpp_endgame_battery.full:runner_exception:ValueError
  mbpp_endgame_battery.full:runner_exception:TypeError
```

## 3. `ceiling3_diag_sweep.py`'s own wiring (no `mbpp_endgame_battery.py`
   re-run needed — it reuses `battery.taxonomy()` verbatim)

No real `results/ceiling3_diag_sweep.json` exists in this environment (the
script has not been run recently here), and actually running the script's
`main()` would invoke `domains.prog_synthesis.synthesize_from_request`
across ~150 tasks — real synthesis search, explicitly out of scope for this
rung. The wiring was instead verified with a schema-accurate SYNTHETIC smoke
fixture (rows carrying exactly the two fields `battery.taxonomy()` reads,
`task_id`/`outcome` — clearly labelled here as a smoke test, never presented
as a real measurement):

```
ingested engineering residuals: 3 populations -> .../results/engineering_gaps_substrate.json
{
 "source_script": "ceiling3_diag_sweep",
 "upserted": [
  {"outcome": "gapped:enumerate_failed", "count": 5, "population_key": "ceiling3_diag_sweep:gapped:enumerate_failed"},
  {"outcome": "accepted_holdout_fail", "count": 3, "population_key": "ceiling3_diag_sweep:accepted_holdout_fail"},
  {"outcome": "not_recognized", "count": 1, "population_key": "ceiling3_diag_sweep:not_recognized"}
 ], "zeroed_absent": [], "measured_at": "2026-08-16T19:42:14+1000"
}
=== surface check ===
{'content': 'ceiling3_diag_sweep:gapped:enumerate_failed', 'kind': 'engineering_residual', 'source': 'implicit', 'status': 'noted'}
{'content': 'ceiling3_diag_sweep:accepted_holdout_fail', 'kind': 'engineering_residual', 'source': 'implicit', 'status': 'noted'}
{'content': 'ceiling3_diag_sweep:not_recognized', 'kind': 'engineering_residual', 'source': 'implicit', 'status': 'noted'}
```

`ingest_engineering_residuals(out)` in `ceiling3_diag_sweep.py` is
literally `battery.taxonomy(out, [])` (the module already `import
mbpp_endgame_battery as battery`) piped into the same `ingest_taxonomy` —
zero new grouping logic, per the PREREG's own claim.

## 4. `promote_self_concern` — no new routing needed, verified live

An `engineering_residual` `SelfConcern` was promoted through the real,
unmodified `jabberwock_daemon.promote_self_concern`:

```
{
 "ok": true,
 "self_concern": 24313,
 "standing_concern": 24317,
 "about": "promote_check:accepted_holdout_fail",
 "target_words": ["promote_check:accepted_holdout_fail"],
 "kind": "engineering_residual",
 "pipeline": "comprehend_first"
}
```

No crash, no special-casing needed — it falls through to the same
`comprehend_first` default every other unclassified kind gets, exactly as
predicted in the PREREG (§3, "no new `promote_self_concern` routing
branch"). `_process_prog_read_standing` (mechanism (d)) was NOT touched —
confirmed already present at `scripts/jabberwock_daemon.py:2539`, landed by
`0e62166`/`4563c3a` before this rung began.

## 5. Test gates

**New tests, `tests/test_engineering_residual_gap_migrated.py`, 8 tests, all
against the SAME full-seed `WorldAdapter` fixture
`tests/test_gap_awareness_migrated.py` uses:**

```
tests/test_engineering_residual_gap_migrated.py ........            [100%]
8 passed in 89.11s (0:01:29)
```

Covers: one `SelfConcern` per population (never per task-id); `pass` never
mints; identical re-ingest is deduped; count→0 retires only that population
and leaves the others live; a population that VANISHES from a later
taxonomy (not just count=0) also retires (the absence-is-zero precedent);
`_run_self_gaps` surfaces it with the right `by_source` grouping; a live
`converse()` turn surfaces it; two `source_script`s never collide.

**Existing regression gate — the six files CLAUDE.md's own citations name
(`tests/test_gap_awareness_migrated.py`,
`tests/test_prog_read_selfimprove_migrated.py`,
`tests/test_prog_synthesis_selfimprove_migrated.py`,
`tests/test_self_concern_promote_migrated.py`,
`tests/test_self_gaps_surfacing_migrated.py`,
`tests/test_solve_gap_awareness_migrated.py`):**

```
[this worktree, WITH the change]
FAILED tests/test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap
FAILED tests/test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once
FAILED tests/test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content
FAILED tests/test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap
FAILED tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_gap_promote_teach_accept_full_circle
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_capability_report_and_nl_surface_include_synthesis
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_capability_report_prog_read_gap_counts
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_p0_flagged_set_reruns_at_precision_one
FAILED tests/test_solve_gap_awareness_migrated.py::test_solve_decompose_failure_files_a_solve_failure_gap
FAILED tests/test_solve_gap_awareness_migrated.py::test_solve_success_files_no_gap
11 failed, 26 passed, 24 warnings in 371.93s (0:06:11)
```

**The SAME command, on a SEPARATE, freshly-checked-out, completely
UNMODIFIED `main @ f4394fd` worktree (zero files from this rung present)
— run for direct comparison, not assumed to be "known baseline noise":**

```
[separate clean worktree, main @ f4394fd, no changes]
FAILED tests/test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap
FAILED tests/test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once
FAILED tests/test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content
FAILED tests/test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap
FAILED tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_gap_promote_teach_accept_full_circle
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_capability_report_and_nl_surface_include_synthesis
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_capability_report_prog_read_gap_counts
FAILED tests/test_prog_synthesis_selfimprove_migrated.py::test_p0_flagged_set_reruns_at_precision_one
FAILED tests/test_solve_gap_awareness_migrated.py::test_solve_decompose_failure_files_a_solve_failure_gap
FAILED tests/test_solve_gap_awareness_migrated.py::test_solve_success_files_no_gap
11 failed, 26 passed, 24 warnings in 373.54s (0:06:13)
```

**Byte-identical failure lists, byte-identical pass counts (26).**
These 11 failures pre-exist this rung entirely and are unrelated to it (a
sample, `test_solve_decompose_failure_files_a_solve_failure_gap`, fails on
`"the general reading pipeline does not ground 'if X is a dog, X can bark'
into an antecedent is_a + consequent is_a/can predication pair -- the NAMED
residual"` — a documented ungrounded reading-shape residual, nothing to do
with gap filing or this rung's seed). `tests/test_self_concern_promote_
migrated.py` and `tests/test_self_gaps_surfacing_migrated.py` are fully
green in both runs (their tests are among the 26 passing). **Zero
regressions attributable to this change**, established by direct A/B
comparison, not inference from "looks unrelated."

## 6. Seed load — the new seed installs cleanly

`load_all_seeds` with and without `seeds/engineering_residual_gap.json`
present produces the IDENTICAL 8-seed failure list (`acoustic_cue_vocab`,
`character_tom`, `reading_constructions`, `conceptual_categories`,
`cue_investigator`, `named_compound_heads`, `reading_skeleton`,
`vision_change` — all `"seed node missing local_id"`, unrelated
pre-existing seeds), and `"engineering_residual_gap"` appears in the
resolved topological `order` — it loads, depends only on `gap_awareness`
as declared, and is not implicated in any load failure.

## 7. What changed (files)

- `docs/research/engine_substrate/MEASURED_RESIDUAL_FILING_PREREG.md` (new)
- `docs/research/engine_substrate/MEASURED_RESIDUAL_FILING_RESULTS.md` (this file)
- `domains/engineering_residual_ingest.py` (new, ~130 lines): `ingest_taxonomy`
  (mechanical find-or-update + `tick()`), `load_or_boot_residual_substrate`
  / `_reconcile_residual_state` / `save_residual_substrate` (the small
  dedicated persisted checkpoint + its content-keyed reconcile).
- `seeds/engineering_residual_gap.json` (new): `note_engineering_residual_gap`
  (mint, `gap_awareness.json`'s dedup shape verbatim, `"pass"` excluded by
  name) + `retire_resolved_engineering_residual_gap` (`retire_duplicate_gap`'s
  guard shape, pointed at count==0).
- `scripts/mbpp_endgame_battery.py` (+26 lines): `ingest_engineering_residuals`,
  called at the end of `main()` with `arm_full["outcome_taxonomy"]`.
- `scripts/ceiling3_diag_sweep.py` (+22 lines): `ingest_engineering_residuals`,
  reusing `battery.taxonomy()`, called at the end of `main()`.
- `tests/test_engineering_residual_gap_migrated.py` (new, 8 tests).

**Zero lines changed in `domains/reflective_faculty.py`,
`scripts/jabberwock_daemon.py`, or `seeds/gap_awareness.json`.**

## 8. What this rung did NOT do (named, not built)

1. Did not run the real `mbpp_endgame_battery.py` or `ceiling3_diag_sweep.py`
   `main()` sweeps (would invoke synthesis search — explicitly out of
   scope). Verified their wiring against real prior output
   (`results/mbpp_endgame.json`) and a labelled synthetic smoke fixture
   respectively, by calling the exact functions `main()` would call.
2. Did not wire the real jabberwock daemon's own `~/.jabberwock/checkpoints`
   state to read `results/engineering_gaps_substrate.json` — a separate,
   dedicated small checkpoint for this proposal, not the daemon's live
   state. Named as a residual in the PREREG; not built here.
3. Did not add a `promote_self_concern` routing branch for
   `kind:'engineering_residual'` — verified the existing generic
   `comprehend_first` default handles it without error (§4); no special
   routing was named as required by the design doc.
4. Inherits `gap_awareness.json`'s own known limitation: the mint guard's
   `Not Exists SelfConcern content==X` (no status filter) means a
   population that regresses after being retired (count 60 → 0 (retired) →
   5 again) will not re-mint. Not fixed here — `note_solve_exhausted_gap`
   has the identical property today; changing it would be extending the
   precedent's shape, not reusing it.
5. Did not investigate or fix the 8 pre-existing seed-load failures
   (`acoustic_cue_vocab` et al.) or the 11 pre-existing gap-awareness-suite
   failures — both confirmed unrelated to this change (§5, §6) and out of
   this rung's scope.
