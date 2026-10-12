# Thoughtexperiment recurrence early-rejection v1 — preregistration

## Question

Can a fixed per-stage rule-work budget reject recurrence candidate branches early while preserving the current evaluator's candidate pass/fail decisions and the graph-Term winner?

## Paired design

Run four workers, eight unchanged host-generated candidate variants, and four training plus four disjoint held-out episodes per candidate and worker. One episode contains two keyed due candidates. On every identical candidate/episode input, execute both (A) the current `score_candidate` reference and (B) a bounded evaluator. Both start from fresh equivalent substrate instances and use the same rule bundle, recurrence keys, offer-count oracle, and fixed-point requirement.

The bounded evaluator has two stages: process the first due candidate to a fixed point, add the second due candidate, then process again. Each stage makes batches of at most 100 rule calls and stops when a batch uses fewer than its limit. If both batches consume 100 calls, reject that candidate as `work_budget_exhausted` and do not enter the next stage. The hard budget is 200 rule calls per stage. Candidates that complete a stage continue exactly as in the reference sequence.

During training, freeze both evaluators' episode outcomes, graph-Term selections from their own training evidence, candidate descriptors, and source hashes. Orders contain no held-out outcomes or keys. Only afterward execute paired held-out episodes for every candidate and compare pass/fail parity and fixed-point status.

## Pass conditions and measures

Pass requires identical candidate descriptors, both evaluators selecting `dedup_identity_fix` in every worker, exact pass/fail parity for all 256 paired candidate episodes (128 train, 128 held-out), selected candidate success on all held-outs, zero selected-candidate closure-budget rejects, and no bounded stage exceeding 200 rule calls. Every capped candidate must be rejected before the second recurrence candidate is inserted when stage one exhausts its budget. Primary rule definitions must remain unchanged, one compact residual must return per worker, and candidate/evidence nodes must remain branch-local. Report baseline and bounded task runtime, rule-call counts by stage, graph scoring, candidate generation, and early-rejection savings.

This measures proposal evaluation and resource control for one authored recurrence family. It does not prove termination in general or move host candidate generation/oracle authorship into the substrate.

## Reproduction

Run the source-locked runner with `--lock`, `--orders`, and `--score`, then run the independent analyzer. The score stage must refuse to run without a frozen order artifact.
