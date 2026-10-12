# Thoughtexperiment revision/receipt validation v1 preregistration

Date: 2026-10-04

## Question

Can the thoughtexperiment candidate lifecycle remove whole-graph export and canonical hashing from its hot path by using the existing graph/rule revision token and exact mutation journal, while preserving exact final semantic parity?

## Design

Compare `full_digest` and `revision_receipt` validation modes in fresh workers, paired on identical configurations: 200,000 and 1,000,000 unrelated noise nodes; four independent-state frames; four candidate branches; both full-copy and shared-graph-page forks; two replicates per cell (16 workers total). Randomize the configuration order with `random.Random(20261008).shuffle` and freeze it in the pre-run lock.

The full-digest arm retains current behavior: whole-graph digest checks inside the candidate lifecycle. The revision/receipt arm uses the O(1) `experiment_graph_rule_revision()` to prove that the primary stayed at its captured base revision through branch exploration and that a stale receipt rejection left the tracked semantic revision unchanged. It applies the selected branch's `conclusions` receipt against that exact base revision. Immediately after the timed lifecycle, it exports and hashes the selected branch and returned primary, and requires exact graph parity; the existing independent monolithic oracle checks both states against a separately built oracle. The exact post-lifecycle parity audit is timed and reported separately.

## Gates

1. Lock all source files, build identity, protocol, worker, analyzer, and underlying thoughtexperiment replay before capture.
2. Require 16 unique fresh workers, exact frozen paired schedule, no failures, and stable source hashes.
3. In every worker require unique correct candidate selection, oracle parity, primary isolation, rule preservation, stale receipt refusal, and quiescent closure.
4. Full-digest mode must perform exactly five graph exports and five canonical digests inside the lifecycle; revision/receipt mode must perform zero of each there.
5. Revision/receipt mode must then pass exact full graph digest parity between the selected branch and returned primary, plus the independent monolithic-oracle checks. Report lifecycle speedup separately from exact-audit cost and their sum.
6. Independently recompute all worker gates, timings, memory summaries, paired speedups, and audit-inclusive costs.

## Claim boundary

This is a synthetic sparse graph and one host, with two replicates per cell. Revision-token safety relies on all semantic graph/rule writes advancing the tracked revision; journal correctness relies on covered mutation paths. The existing mutation matrix covers 17 public sequences but does not establish concurrency safety or exhaust every unsafe interior mutation. This measures a candidate optimization under that contract, not a universal replacement for full-state auditing or a natural-task throughput result.
