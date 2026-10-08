# Reachability cache versus materialized profile v1 preregistration

## Question

For repeated reachability evaluation inside native rule closure, how do the existing opt-in same-graph `ReachableFrom` cache and explicit finite-key reachability materialization compare in total cost and exact behavior?

## Design

Use binary and ternary rooted trees at N=64,128; create one query edge into every vertex. Cross each graph with 1,4,16 reader rules, five fresh repetitions (60 cases). Every reader rule matches each query edge and evaluates a true `Count(ReachableFrom(x, link)) >= 0` condition with no effects. Compare three arms: cache disabled, cache enabled, and cache disabled with the admitted two-rule materialization profile followed by readers that use `Count(Neighbours(x, reachable))`. The cache is deliberately exercised inside native `run_rules`, where its per-graph EvalCache is shared; direct host calls to `PySubstrate.evaluate` are outside this cache path.

## Cost accounting

All totals include graph construction and query-edge construction. Direct arms add R reader rules and run them. Cache-on arm also includes cache activation. Materialized arm includes profile installation and closure, then reader installation and consumer closure. Report components, wall and CPU totals, cache hits/misses/retained-payload estimate, and exact semantic checks. Do not include oracle evaluation in timed intervals. Alternate the three arm orders by replicate and cell parity.

## Gates

Independently compute every source's link-reachability set and full relation. Require the materialized relation and each arm's observed per-rule query accounting to agree with the expected source set; all three reader arms must reach fixed point with zero progress and identical reader-match counts. Cache-off must report zero cache activity; cache-on must report one miss per source and `(R-1)*N` hits; profile must match exact materialized facts. Require all 60 unique cases, stable source lock, and checker admission plus rejection of an unrestricted fresh-node control.

## Limits

The readers are controlled synthetic no-op rules. They measure the native cache's relevant execution path and the explicit profile's cost, not natural frequency, default activation, or live-task speed. The cache remains experimental and opt-in.

## Reproduction

Run `python3 evaluation/substrate_capability/reachability_cache_materialization_comparison_v1.py --lock`, then the runner without arguments, followed by `python3 evaluation/substrate_capability/analyze_reachability_cache_materialization_comparison_v1.py`.
