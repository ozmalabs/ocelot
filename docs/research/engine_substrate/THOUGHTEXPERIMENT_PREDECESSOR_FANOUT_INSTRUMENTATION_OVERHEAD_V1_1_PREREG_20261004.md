# Thoughtexperiment predecessor fanout instrumentation overhead v1.1

Date: 2026-10-04

## Question

Does the graph-export/digest instrumentation measurably alter lifecycle time on
the same 100k-node thoughtexperiment workload when replication is increased?

## Design

Repeat the previous matched on/off design at eight replicates per backend,
producing 32 fresh-process workers (16 pairs): four independent-state frames,
four candidate branches, 100,000 unrelated nodes, and full-copy/shared-page
backends. Do not change workload, worker logic, or semantic gates. Randomize
the order of the 16 backend/replicate pairs and the on/off order within each
pair using the fixed Python seed 20261005. The schedule is captured before
execution and source-locked.

Primary measure is paired lifecycle-time difference (on minus off) by backend.
Report all pair differences, median and mean differences, median on/off ratio,
and a paired t interval (mean ± 2.365 standard errors, df=7). Also confirm exact
semantic outcome parity using the amended v1.1 projection. Timer components are
interpreted as descriptive on-arm costs only.

## Gates

Require a pre-run lock of this protocol, runner/analyzer, prior on/off protocol,
runner, lock, capture, amended analysis, cost-breakdown runner/capture/analysis,
the current engine/build sources, and repository commit. Capture 32 unique
workers, complete 16 pairs, stable pre/post lock, per-arm oracle/isolation/
revision/quiescence gates, exact paired candidate-outcome parity, and valid
timing calculations. Preserve failures and do not replace failed workers.

## Limits

Eight pairs per backend improve the diagnostic but still describe one host and
one authored graph/task shape. A paired interval estimates this workload's
combined wrapper-dispatch and clock-call effect; it is not a universal
instrumentation factor or a graph-size scaling law.
