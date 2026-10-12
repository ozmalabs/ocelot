# Task-derived anaphora join-order estimator v1 preregistration (2026-09-29)

## Question

Can a bounded sample of partial bindings rank the native match orders for the four-edge anaphora rule on its actual task graph, and does the selected order repay sampling and installation cost as irrelevant prior context grows?

## Task and variation

Use the production `intent` seed and its `rule_anaphoric_it_resolves_to_prior_about_concept` rule. Each task has D prior distractor turns from the fixed list `answer, idea, plan, story`, followed by `the question matters` and the target utterance `answer it`. D is 0, 2, or 4. Comprehend each turn in order. The target oracle requires that the new `it` Mention resolves to `question` and the target Intent includes `question`.

At the target closure, evaluate the eight distinct edge orders already shown realizable by the current native rule installer. Each exact-order cell runs in two fresh processes: 3 context sizes × 8 orders × 2 replicates = 48 audit-on exact-cost workers. Independently run plain source-order and estimator-selected closures for sample budgets B=8, 32, and 128: 3 sizes × 4 arms × 2 replicates = 24 workers. Total planned worker count is 72. The estimator scores every realizable order from a pre-closure graph snapshot and chooses the lowest estimated cumulative candidate expansion, breaking ties by a preregistered stable order key.

## Estimator

Build outgoing, incoming, and relation-wide edge indexes from the pre-closure graph. For each order, begin with one empty binding. At each clause and sampled partial binding, reproduce the matcher candidate source: outgoing edges when source-bound, incoming edges when only target-bound, outgoing edges followed by target filtering when both are bound, and all edges of the relation when neither is bound. Uniformly sample at most B candidate pairs per layer with a fixed seed. Estimate surviving partial-binding population and cumulative candidate expansion by inverse sampling fraction. Score all eight orders. This is a Python diagnostic; it does not modify production source or engine policy.

## Measurements and gates

- Exact arm: realized installed edge order; target-rule candidate tests and per-clause conservation; fixed point; task oracle; canonical full-graph digest; audited/unaudited state and progress parity where paired arms exist.
- Estimator: all eight finite order scores at each budget; selected order; estimated work; measured planning CPU/wall; separate Python allocation diagnostic; deterministic output for fixed graph and seed.
- Plain arm: source-order and B=8/32/128 selected-order graph/task parity; rule-install time; uninstrumented closure CPU/wall. Charge `planning wall + selected-order installation + plain closure` and compare with source-order plain closure. Report paired ratios per size and replicate; no aggregate speed claim if any semantic, source, or instrumentation gate fails.
- Provenance: current native build, pre-run lock, exact source/native hashes before and after every worker and after the panel, 72 unique PIDs, complete child logs with hashes, and exact factorial coverage.

## Claim boundary

This is one authored four-edge anaphora rule and three generated context lengths in one seed profile. The distractor turns are controlled inputs, not a sample of natural conversation. Candidate work is an exact native counter for the measured rule; estimator predictions are compared against that oracle. The benchmark does not establish general join-order optimization, natural task prevalence, or production safety.

## Reproduction

```sh
python3 scripts/substrate_task_derived_anaphora_order_estimator_v1.py --lock
python3 scripts/substrate_task_derived_anaphora_order_estimator_v1.py
python3 scripts/analyze_substrate_task_derived_anaphora_order_estimator_v1.py
```
