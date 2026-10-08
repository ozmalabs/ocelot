# High-degree edge deletion and reinsertion v1 preregistration

**Question:** after high-degree insertion is indexed, how does deleting every edge from one hub scale, and does reinsertion preserve exact lookup semantics?

## Workload

Use one root node and N target nodes, with one `hub_child` edge from the root to each target. Sweep N=5,000/20,000/80,000 with three fresh processes per size. The setup uses the native public Python API. Time node creation, edge creation, full edge deletion, and full edge reinsertion separately. No rules, access tracing, or scale audit are enabled. Delete in ascending target order using `remove_edge`, then reinsert the same edge set with `add_edge_unchecked`.

## Correctness gates

Before deletion require exactly N edges and sampled edge lookups. Require every deletion call to return true, zero edges after deletion, and sampled lookups false. After reinsertion require exactly N edges, sampled lookups true, and no node-count change. Require stable source fingerprints, unique PIDs, positive phase timings, and a fresh native build. The independent analyzer must recalculate per-size medians from worker rows.

## Claim limits

This is a controlled mutation-cost probe for one high-degree source/type bucket. Three sizes can characterize the measured curve but cannot prove an asymptotic bound. The probe does not measure mixed edge types, deletion of one hub node with incoming and outgoing edges, rule invalidation cost, concurrent readers, or application-level churn.
