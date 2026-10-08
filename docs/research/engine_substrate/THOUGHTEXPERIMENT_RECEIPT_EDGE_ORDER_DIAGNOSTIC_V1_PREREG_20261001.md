# Receipt edge-order diagnostic v1 preregistration

**Question.** At which task event does receipt adoption first change ordered graph views, and do exposed adjacency/typed-neighbor APIs show the same change?

## Workload

Re-run the frozen ten-event mixed-act dialogue task through Direct, eager-receipt, and shared-snapshot-receipt arms using the v1.1 task protocol. Use eight fresh workers and the same counterbalanced arm schedule, source/native lock, task oracles, branch journal, receipt adoption, and per-event settlement. This diagnostic adds read-only state capture after each event; its timings are not performance evidence.

For every arm/event checkpoint, record:

- Full graph edge-slab sequence `(src,type,tgt,attrs)` from `graph_to_dict()`.
- For each live node, the ordered `incident_edges()` result.
- For each distinct `(src,edge_type)` and `(tgt,edge_type)` in the graph, public `neighbours()` and `in_neighbours()` results; retain multi-result buckets in the report, while retaining total query counts for coverage.
- The canonical edge multiset and existing per-event semantic digest/task outcomes.

The read-only API capture runs outside all route-stage timing. Continue comparing Direct versus both receipt arms per worker and per event.

## Gates and analysis

1. Eight fresh worker PIDs; source/native lock stable before and after; all v1.1 task, identity, closure, receipt, and terminal gates pass.
2. Canonical node and edge facts match at every event; receipt primary state matches its producing branch.
3. Report the first event and first sequence position where edge-slab order diverges, with the adjacent Direct and receipt edge facts.
4. Compare incident-edge sequences and typed `neighbours`/`in_neighbours` outputs by endpoint/relation. Report mismatch counts and exact first bucket; do not infer safety from task outcomes alone.
5. Test repeatability across all workers; preserve every event checkpoint and read-only observation. Any missing probe bucket or semantic mismatch fails the panel.

## Limits

This measures one authored task family and exposed read-order APIs. It does not establish that all clients depend on order, prove a universal ordering contract, or measure task prevalence. It is a diagnostic for choosing between preserving operation order in receipts and defining canonical iteration/serialization semantics.
