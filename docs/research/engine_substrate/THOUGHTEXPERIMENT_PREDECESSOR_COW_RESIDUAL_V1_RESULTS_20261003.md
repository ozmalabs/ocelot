# Predecessor-dependent closure in CoW thought experiments — results

Date: 2026-10-03

Status: source-locked integration evaluation; three fresh workers.

## Result

The runner and independent analyzer pass all gates across six discourse cases
and five arms (90 arm executions): monolithic closure on the primary,
monolithic closure in full-copy and shared-graph-pages branches, and scoped
closure in both branch backends. All arms agree on the full canonical graph,
correction grounding status, and exact evidence path. The retained-interface
and topicless-chain cases ground; wrong-speaker, topic-interruption,
missing-predecessor-edge, and omitted-target-interface controls remain
unresolved.

For both positive cases, each branch emits one derived-only `nodes_changed`
record for the correction interpretation. The returned graph exactly matches
the branch and monolithic result. Every primary remains unchanged through
branch execution and residual extraction; revision-checked return succeeds,
and the primary rule store is unchanged. Negative controls produce an empty
derived-only graph delta. The experiment therefore connects native
predecessor-dependent rule execution to branch isolation and usable residual
return on this fixture.

## Cost and scope

The final locked capture gives median branch-total time (fork, closure,
residual extraction, and application) of 1.32 ms for full-copy monolithic,
1.00 ms for shared-page monolithic, 0.93 ms for full-copy scoped, and 0.90 ms
for shared-page scoped. Median fork times range from 0.49–0.53 ms full-copy
and about 0.20 ms shared pages. The ordering changes across arms, so this tiny
panel does not establish an end-to-end timing advantage for one closure mode
or backend. Direct primary closure has a different cost boundary and is not a
fair end-to-end comparator. These measurements do not show the requested
order-of-magnitude improvement or a scaling law. The ownership root,
communication rules, task construction, expected outcomes, and merge timing
are authored. This does not establish learned frame
discovery, natural-task prevalence, broad self-improvement, or parallel
candidate throughput.

The first capture attempt found that `derived_only` was empty without a
journal checkpoint before closure. The runner was corrected to checkpoint the
fully materialized input as the derivation baseline; the final source lock
includes this correction, and the final capture and independent analysis pass.

## Next gate

Expand from one correction frame to predecessor-bearing multi-frame traces
with shared and independent discourse states, then add candidate fanout and
larger unrelated host graphs. Keep full-copy, shared-page, monolithic, and
scoped controls. Measure branch count, fork/closure/readout/return cost,
residual size, peak memory, and useful correct outcomes per unit time. Require
full-graph parity when interfaces are retained, explicit expected residuals
when interfaces are withheld, and rejection of stale-revision merges. This
integration result is a foundation for those gates, not evidence that the
system selects or invents its own improvements.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_PREDECESSOR_COW_RESIDUAL_V1_PROTOCOL_20261003.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_cow_residual_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_cow_residual_v1_20261003.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_predecessor_cow_residual_v1_analysis_20261003.json)
