# ReachableFrom same-graph cache panel v1 preregistration

**Status:** preregistered before the scale run.  
**Question:** Does opt-in memoization of repeated `ReachableFrom` Terms reduce measured adjacency work for identical same-graph queries while preserving rule outcomes, final graph, and runtime access-trace events? Does graph mutation invalidate the memo before the next rule run?

## Scope and design

The workload is a typed star graph: one `Root` has N `slot` edges to N `Slot` nodes and N `block` edges to N `Blocker` nodes. Each reader rule matches the N slot edges, then evaluates `Count(ReachableFrom(x, block)) == 0`; this predicate rejects every binding and causes no writes. Thus each of the N×R where evaluations repeats the same transitive query without mutation. Cache-off is the control; opt-in cache is the treatment. Three fresh worker processes replicate each cell for N in {32, 128, 512} and R in {1, 16, 64} (27 processes total). Arm order is counterbalanced by replicate parity.

The panel records fixed-point reports, exact graph serialization, runtime access-trace rows, `ReachableFrom` interior work units, and wall time. The prespecified primary cost is the site-defined `term_unit:ReachableFrom` counter, which counts adjacency entries visited, not CPU instructions. The expected operation-count model is N²R off versus N on for this star family. Timing is secondary and exploratory.

A separate mutation control runs a query whose count changes from N to N+1 after adding one `block` edge. The rule predicate is false before the insertion and true after it; all N slot bindings must then produce the expected marker. This tests cache invalidation and semantic freshness, not a scaling cell.

## Gates

1. Native build is current and locked inputs remain byte-identical before/after the run and within each worker.
2. All arms reach the same fixed point and serialize identical graphs; runtime access-trace event rows match exactly.
3. Every scale cell has three distinct worker PIDs and the complete 3×3×3 design.
4. Every cell has exact off/on work counts N²R and N; the observed ratio is therefore N×R for this constructed family.
5. Mutation control changes from no markers to all N markers, reaches fixed point, and records positive `ReachableFrom` work after mutation.

Failure of any gate invalidates the positive claim. A pass supports only repeated, identical, typed `ReachableFrom` queries on an unchanged graph and explicit mutation invalidation for this fixture. It does not establish cache benefit on natural workloads, memory cost, concurrency safety, arbitrary cache lifetimes, or a general tractability theorem.

## Inputs and artifacts

Runner: [`scripts/substrate_reachable_from_cache_v1.py`](../../../scripts/substrate_reachable_from_cache_v1.py)  
Independent analyzer: [`scripts/analyze_substrate_reachable_from_cache_v1.py`](../../../scripts/analyze_substrate_reachable_from_cache_v1.py)  
Lock: `evaluation/substrate_capability/reachable_from_cache_v1_lock_20260928.json`  
Raw report: `evaluation/reports/substrate_reachable_from_cache_v1_20260928.json`  
Analysis: `evaluation/reports/substrate_reachable_from_cache_v1_analysis_20260928.json`
