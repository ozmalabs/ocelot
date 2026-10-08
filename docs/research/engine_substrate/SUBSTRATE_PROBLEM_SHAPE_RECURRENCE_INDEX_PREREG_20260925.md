# ProblemShape recurrence event/index prototype preregistration

**Status:** isolated candidate prototype comparison; baseline seed and default execution are unchanged.

## Question

Can a graph-resident per-key support bucket plus residual-event driver preserve ProblemShape mint/re-decode behavior while reducing the measured `ps_mint` candidate and support-scan work? How much host-side index maintenance does the prototype add?

## Variant definition

The prototype changes only the `ps_residual`, `ps_mint`, and `ps_redecode` rules in an isolated worker. Before closure, the adapter creates/updates a `ProblemShapeKeyIndex{key,support_count}` row for each observation and links the observation to that row. `ps_residual` emits a `problem_shape_residual_candidate` event edge. `ps_mint` matches that event and the observation's key-index edge; it reads support from the row, retains the original residual/no-existing-shape/canonical-Argmin guards, and writes mint support from the same counter. Mint and re-decode consume pending residual-event edges. The support count increments once per newly created observation, regardless of status, matching the current mint-support definition. Other ProblemShape rule match patterns remain unchanged.

This is a candidate-only prototype. It does not eventize `ps_decode`, `ps_recognize`, `ps_residual`, or `ps_redecode` matching globally, so it cannot eliminate the other four rules' scans. It also relies on host-side index creation in this isolated workload; its maintenance time is measured separately.

## Workloads

Reuse the exact N=2/4/8 recognition and recurrent-residual task mixes, task ordering, task constructors, seed files, and native binary from the locked population-scale sweep. Run one fresh process per cell (six prototype workers). The baseline values come from the already-locked six dynamic workers in [`SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_RESULTS.md`](SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_RESULTS.md) and are identified by the baseline raw-report hash in the lock file.

## Required checks and measures

- Exact final application-visible observation statuses, mint count, minted shape key/support, codebook epoch, and fixed-point status must match the baseline for each cell.
- Every observation must have exactly one key-index link; each `support_count` must equal an independent grouping count by observation key.
- Record per-rule candidate pairs, term evaluations/units for all five ProblemShape rules, native closure cost, host index-maintenance cost, whole-engine counters, and process RSS.
- Report candidate-only work reduction separately from total ProblemShape and end-to-end observation cost. Do not claim an overall scaling improvement from `ps_mint` counters alone.

## Acceptance and limits

All semantic/index invariants must pass. If an optimization reduces `ps_mint` counters but increases total cost or fails an exact state check, report the failure; do not tune after seeing results. The small sweep is exploratory and cannot establish a general complexity or natural-task benefit. The prototype does not exercise persistence/rebuild, concurrent observation ingestion, rollback, or the other four rules' global scans; those remain required before any default-path discussion.
