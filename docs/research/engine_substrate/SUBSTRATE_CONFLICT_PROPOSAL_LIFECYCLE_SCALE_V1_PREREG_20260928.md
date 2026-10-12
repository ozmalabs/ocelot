# Conflict proposal lifecycle and resolution scale v1

## Question

How do graph-resident proposals scale through N=64 contenders, remain deduplicated on re-settlement, and resolve under unique versus tied maximum scores?

## Design

- Three independent fresh processes; N=2,4,8,16,32,64, each with `unique_max` and `tied_max` score distributions.
- A generator rule family creates one `ConflictProposal` node and one `proposes` edge per candidate using `add_node_if_absent`. Each node carries a stable label and integer score.
- Settle generator rules once, then settle them again to measure idempotent lifecycle/deduplication.
- Add one graph-native resolver rule matching `target proposes proposal`; its guard checks proposal score equals `MaxOver(Neighbours(target, proposes), score)`, and its effect writes the selected label with `set_attr_if_different`.
- Unique-max inputs have one maximum. Tied-max inputs set the top two scores equal. Run with cycle detection. Collect graph projections, termination status, candidate/Term scale-audit counts, and source/native lock. Timings are descriptive only.

## Gates

All workers cover all 12 size/distribution cells with stable source/native locks. Generation reaches fixed point with exactly N proposals/edges; a second settle adds no graph state or progress. Unique maximum resolves to the independently calculated label and fixed point. Tied maximum preserves proposals but the basic resolver must not silently claim a unique result; its behavior (including any cycle) is recorded. Operation counters replicate across workers.

## Limits

This measures an authored one-target proposal family and a `MaxOver` resolver, not learned conflict detection or general inference. A tie-induced cycle is a failing resolver design, not a substrate-wide tie-handling conclusion. Graph-state scale ends at N=64 and does not prove asymptotic complexity.
