# Native query-eligibility scaling v1 preregistration

## Question

How do native candidate-positive eligibility closure and the once-per-query `ArgminUnique` selector scale as the probe population grows, and do they retain exact parity with a separately reconstructed host oracle?

## Workload and design

Use the same graph rule shapes as native candidate-positive selection in query-selector v1.3: eligibility joins the selected-family edge, episode probe edges, family vote edges, and vote-to-example edges, then adds an eligibility edge for positive predictions. A second native rule selects the eligible probe with the smallest task-blind rank. Do not include model scoring or label adjudication in the timed closure.

Measure pool sizes 512, 1,024, 2,048, 4,096, and 8,192 with five fresh deterministic seeds per size. Each example has one candidate vote with a deterministic prediction and unique deterministic rank; predictions are generated independently of any target label. Ensure both predictions occur at every size. Candidate-positive count, eligible node identities, and selected node must match an independently reconstructed host oracle exactly. Each worker builds a fresh graph and native substrate. Record graph-build, eligibility, selection, total CPU, wall time, and peak RSS separately. Report medians and p90 by size; do not fit or claim an asymptotic complexity class from five points.

## Gates

Require 25 successful source-locked workers, stable source fingerprints, exact positive-count/eligible-set/selected-node parity, a unique selected rank, and finite timings. The timing comparison is within this same worker and uses the eligibility and selection closures independently. No optimization is accepted in this panel; it establishes the cost curve and identifies whether candidate generation/matching, rather than ranking, dominates.

## Limits

This is a synthetic graph-level mechanism benchmark derived from one authored query path. Repeated feature values are allowed because the question is population cost and node identity/rank parity. It does not establish task-natural prevalence, end-to-end application latency, graph-frame locality, or general query competence. `run_rules` closure time includes matcher and effect work; graph construction and Python-side oracle work are reported separately.

## Reproduction

Create the immutable panel/source lock with `python3 evaluation/substrate_capability/native_query_eligibility_scale_v1.py --lock`, run with `--run`, and independently analyze with `python3 evaluation/substrate_capability/analyze_native_query_eligibility_scale_v1.py`.

