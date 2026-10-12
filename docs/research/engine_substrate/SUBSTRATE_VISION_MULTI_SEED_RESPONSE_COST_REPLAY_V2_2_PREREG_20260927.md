# Vision multi-seed response cost replay v2.2 preregistration

## Question
What wall time, process CPU time, and resident-memory envelope does the v2.1 75-condition response panel incur on the current host, and how much of measured wall time is spent inside native closure calls versus restoring graphs, hashing states, and extracting measurements?

## Design
Replay all 25 registered conditions on each exact v2.0 checkpoint (seeds 20260935, 20260936, 20260937), using the unchanged v1.9 response-phase contract and exact-cycle rule. Do not adapt or mutate checkpoints. Measure per condition: total elapsed wall time, total process CPU time, cumulative wall time inside `run_rules_report(1, False)`, cumulative process CPU time inside those calls, progress steps, pass count, termination class, cycle period, and rate-write state. Also capture resident set size before/after each condition and process peak RSS for each isolated seed worker. Reconcile each condition's starting post-input graph digest, closure outcome, work, cycle period, and rate-write vectors exactly against v2.1.

Run each seed in a fresh child process. This isolates process peak RSS by seed and makes partial results resumable after each condition. The instrumented loop retains exact state hashing for repeated-graph detection but omits per-pass JSON serialization and disk trace flushing. Thus the measured closure-call time is a lower-overhead engine-call metric; total condition time still includes Python orchestration and exact graph hashing.

## Integrity and analysis
Lock this protocol and runner, v1.9 runner/contract/source lock, v2.1 raw/analysis, all three exact checkpoint files, Python/platform, and native engine provenance. Require source-lock identity, all 75 pairs, exact response/work parity with v2.1, valid rate equations/stamps, and no budget exits. Report condition distributions and medians/ranges by seed and size class (blank, single sheet, joint sheets). RSS is process-level, not allocated to individual native routines. Timings are host-specific and diagnostic, not throughput claims.

## Claim boundary
This measures one synthetic 4×4-per-sheet vision workload on one host. It does not test larger frame scaling, natural task prevalence, or induction cost. Closure-call CPU time is distinct from whole-condition wall time; neither alone establishes commodity-scale performance.
