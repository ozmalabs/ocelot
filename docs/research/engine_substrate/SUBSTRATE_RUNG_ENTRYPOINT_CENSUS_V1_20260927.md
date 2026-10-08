# Rung entrypoint census v1

Date: 2026-09-27  
Type: source audit; no runtime frequency estimate.  
Purpose: define which production rung can be measured without adding a new cognitive path.

## Finding

`ProblemShape.observe` is an opt-in, after-goal observer. A source search finds its direct callsites in tests and experiment runners, but none under the production `domains/` or `substrate/` runtime. Therefore its experiment counts cannot be called natural task frequency. Wiring it into a user task path would be an intervention that must be evaluated separately.

The substrate does have live, residual-driven dimension acquisition through `reflective_faculty.induce_concern`. It ingests an `Observation`, calls the existing native rule fixpoint, and reads back one of `recognized`, `recognized_transformed`, or a minted capability axis. The source documents the covered/no-growth and uncovered/mint branches. Production callsites include reading residuals (`reading_collapse.py`), code reading (`code_reading.py`), and ink recognition (`ink_decode.py`). The function emits `NativeReflectiveFacultyReceipt` rows with the `reflective_faculty.concern_decode_settlement` cluster and returns the final status, so task-bounded graph deltas can count actual attempts without invoking the observer a second time.

`teach.py` also calls `meta_shape.observe` when teaching a type. That is an explicit teaching path and should be reported separately from passive natural-task learning. The `ProblemShape` family has a different limitation: `solver_dispatch.py` defines several `mint_solve_*_goal` entrypoints, but production callers are sparse and the generic ProblemShape observer is not wired after Goal resolution. ProblemShape experiments currently create and observe Goals directly.

## Source anchors inspected

- `domains/problem_shape.py::observe` (around line 147): explicitly invoked observer; writes a `ProblemShapeObservation` and optionally runs rules.
- `domains/reflective_faculty.py::induce_concern` (around line 1302): production dimension-decode/mint path; receipt creation around line 1337.
- `domains/reading_collapse.py` around line 1691 and `domains/code_reading.py` around line 377: residual-triggered calls into `induce_concern`.
- `domains/ink_decode.py` around lines 918 and 1172: on-path stroke/ink residuals call the same mechanism.
- `domains/teach.py` around line 164: explicit `meta_shape.observe` during teaching.
- `domains/solver_dispatch.py` around lines 160–715: Goal constructors; research scripts, not a universal natural-task dispatcher, dominate observed `mint_solve_*` invocations.

## Consequence for the measurement plan

The next empirical gate should count production `induce_concern` entries and outcomes around a task stream. It should not turn on `ProblemShape.observe` and label its results natural. For each independently selected task, take graph receipt/observation counts immediately before and after the ordinary task route; classify each newly created receipt with its Observation's settled status and any linked minted axis. Record tasks with no entry as zero-entry cases, not as missing data. Keep teaching (`meta_shape`) and ProblemShape intervention arms separate.

This source census alone gives no frequency estimate. A data audit found 12,424 train, 1,139 validation, and 1,135 test records; all 1,135 test records have a proof target and non-empty statement, and none share a normalized theorem title with train/validation. A deterministic hash-ranked 64-record frame is frozen in [the dataset audit report](../../../evaluation/reports/naturalproofs_rung_stream_frame_v1_20260927.json); the [selector](../../../scripts/audit_naturalproofs_holdout_for_rung_stream_v1.py) ranks on record ID alone, independent of substrate outcomes. However, `naturalproofs_local` reads all shards and indexes `target` proofs, so this frame is not a clean proof-generation holdout and title separation does not rule out paraphrase or theorem-family overlap. Its initial use must measure reading-path induction entry only, with the statement supplied as task input and proof-target access excluded from that route. It cannot support theorem-solving accuracy until that access boundary is verified.

## Next actions

1. Verify the NaturalProofs proof-target access boundary on the ordinary reading path; if access cannot be excluded, retain the stream strictly as an entry-rate pilot.
2. Run the frozen 64-record frame through the ordinary reading path with an external receipt-delta collector. It may read graph state and timestamps but must not call `induce_concern`, `ProblemShape.observe`, or modify the task graph.
3. Publish selected IDs, failures, residuals, transform/recognition/mint outcomes, and per-task costs.
4. Use a second independent task family only after the first stream's route, missing-task handling, and oracle are validated.

## Interpretation boundary

This source census distinguishes available live induction machinery from a purely experimental observer. It is not evidence that natural inputs commonly reach induction, that induction succeeds, or that acquired structure improves task performance. No tractability, general capability, or scaling claim follows.
