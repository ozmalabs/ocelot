# Task-derived anaphora join-order estimator v1.2 preregistration (2026-09-29)

## Question

Can a bounded sample of partial bindings rank native match orders for the four-edge anaphora rule on task graphs of increasing context size, and does the selected order repay sampling and installation cost?

## Task and factorial

Load the production `intent` seed and its `rule_anaphoric_it_resolves_to_prior_about_concept` rule. Use D prior distractor turns from `answer, idea, plan, story`, followed by `the question matters` and `answer it`; D∈{0,2,4}. Comprehend each turn in order. The target oracle requires that the new `it` Mention resolves to `question` and the target Intent includes `question`.

For each of 6 `(D, replicate)` graph cells, collect exact audited candidate costs for the 24 requested permutations of the four positive match clauses plus the untouched source order, with two fresh-process replicates per context count. Run plain source-order and estimator-selected closures at sample budgets B={8,32,128}. This yields 3×2×25=150 exact workers and 3×2×4=24 plain workers, 174 total. The native installer may realize different installed orders at different context sizes; record both requested and realized order for every worker and analyze optimum over realized orders only.

## Estimator

Build outgoing, incoming, and relation-wide edge indexes from the pre-closure graph. For each of the 24 requested clause orders, start with one empty binding. At each clause and sampled partial binding, reproduce the matcher candidate source: outgoing edges when source-bound, incoming edges when only target-bound, outgoing edges plus target filtering when both are bound, and all edges of the relation when neither is bound. Uniformly sample at most B candidate pairs per layer with deterministic seeds. Estimate surviving binding population and cumulative candidate expansion by inverse sampling fraction; select the request with lowest estimated expansion, breaking ties lexicographically. The estimator is a Python diagnostic and does not alter production source or matcher policy.

## Measurements and gates

- Exact arms: exact 24-cell requested-order coverage per `(D, replicate)`, complete clause multisets, observed installed-order map, target-rule candidate tests, per-clause conservation, fixed point, task oracle, canonical graph digest, stable sources.
- Estimator: deterministic scores for all 24 requested orders and each budget, selected request and resulting installed order, prediction error/regret against exact costs for the realized order, CPU/wall planning cost, and separate Python allocation diagnostic.
- Plain arms: source-order and B=8/32/128 selected-order task/full-graph parity. Record install time and instrumentation-off closure time. Charge measured single-budget planning wall + selected-order installation + plain closure against source-order plain closure. Report all 6 paired cells; no aggregate win if semantic, order-map, or provenance gates fail.
- Provenance: current native build, pre-run lock, per-worker and post-run source/native stability, unique PIDs, complete hashed child logs, and exact coverage of 174 declared cells.

## Amendment history and claim boundary

V1 and v1.1 harness captures are retained but excluded: v1 indexed requests through the loaded match array, and v1.1 assumed the prior eight-order realization map was invariant as context grew. The v1.2 design enumerates all 24 requested orders and records the actual installer result per graph cell. This is one authored four-edge rule and three controlled conversation context sizes; distractor turns are not a natural task sample. It does not establish a general optimizer, natural task prevalence, or production safety.

## Reproduction

```sh
python3 scripts/substrate_task_derived_anaphora_order_estimator_v1_2.py --lock
python3 scripts/substrate_task_derived_anaphora_order_estimator_v1_2.py
python3 scripts/analyze_substrate_task_derived_anaphora_order_estimator_v1_2.py
```
