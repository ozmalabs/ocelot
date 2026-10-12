# Bounded prefix-cost selector v1 preregistration

Date: 2026-10-01

## Question

Can a bounded-sample selector recover low-work clause orders on CAN and retinal rule patterns without enumerating all clause permutations, and what ranking regret and selection overhead does it incur?

## Frozen selector

Build outgoing, incoming, and all-edge lists by relation type from the graph edge list. Start with the smallest relation cardinality, breaking ties by authored clause index. Use beam width 8 and at most 128 sampled partial bindings per beam prefix. For each beam prefix and each remaining clause, expand the sample using the graph's directed relation lists. Estimate extension cost and output-prefix population by scaling sample totals by `estimated_prefix_population / sample_size`. Keep the eight prefixes with lowest estimated cumulative candidate work, breaking ties lexicographically by clause-index sequence. Return the lowest-cost complete sequence. `where` predicates are not incorporated; this estimates structural matcher work only.

The selector does not score all permutations. Its maximum sample state is bounded independently of graph size; measured work is the explicit Python prototype, with edge-list index construction and beam search timed separately. Repeated selector calls over the same edge list characterize timing noise. These times are an implementation-specific estimate, not a native engine integration cost.

## Evaluation

1. **Historical references:** apply the frozen selector to all 18 unique nonempty cyclic/hub/clustered CAN topology cells, four additional nonempty N=128 CAN population cells, and all three retinal support profiles from their source-locked captures. The empty Q=0 CAN cell is omitted because it contains no productive pair and the zero-work early exit is trivial. Compare against their recorded measured-best orders; for retinal, use the exhaustive 120-order outcomes to calculate exact regret.
2. **Held-out confirmation:** generate a new 16-column retinal support profile using `count[r,i] = 1 + ((5i + 3r + floor(i/4) + 1) mod 4)`. Run three fresh workers. Each worker measures the default sequence, all 120 exact orders, the selector order, and instrumented/uninstrumented default and selector executions. The selector parameters remain fixed at beam=8, sample=128.

The held-out graph retains the production retinal rule's real epoch guard and productive writes, with one expected active percept and all other percepts guard-rejected. Record selector order, estimated work, actual matched candidate tests, selection timing, exhaustive minimum, maximum, semantic outcomes, terminal closure, and canonical final digests.

## Gates

- Three held-out workers with stable source/native and historical-capture fingerprints.
- Historical cases regenerate exact expected support edge sets; CAN selected order is compared with the measured-best order and retinal regret uses all 120 measured orders.
- Each held-out worker scores all 120 unique orders and returns the same selector order on repeated deterministic calls.
- The exact productive percept oracle, guard negatives, terminal fixed point, semantic parity across all clause orders, and instrumented/plain parity pass.
- Selector work regret is calculated against exhaustive best, not inferred from its estimate. Report overhead and any failure to match the exact minimum without hiding negative results.

## Limits

This selector is a bounded Python prototype, not a production Rust matcher change. The held-out set is one generated retinal rule fixture at N=16; historical cases are reused to assess coverage, not independent replication. No natural image, broad rule distribution, or end-to-end substrate overhead claim follows.
