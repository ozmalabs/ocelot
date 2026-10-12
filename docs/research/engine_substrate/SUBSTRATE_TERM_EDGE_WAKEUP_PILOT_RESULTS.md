# Term-edge wakeup pilot

**Status:** exploratory native runtime diagnostic; three hand-built cases, not a general scheduler correctness claim.

## Question

When a rule's match-pattern edge stays unchanged but a typed edge read by one of its terms is added, does the scheduler re-evaluate the reader's existing binding and refresh its output?

## Workload and oracle

The cases cover a typed term-edge insertion, deletion, and overlapping match/term use. In the first two, the reader matches a stable `trigger` edge and sets an attribute to `Count(Edges(x, "causal"))`; the writer adds or deletes a `causal` edge. In the overlap case, the reader matches `trigger` edges and counts outgoing `trigger` edges while the writer adds a second `trigger` edge from a separate `seed` match. The reference is the final direct count of the relevant typed neighbours.

The initial probe returned a stale zero after the causal edge was added. The scheduler dirtied the reader through its edge read set but retained a semi-naive cursor that only advances on new match-pattern edges. `RewriteRule` now retains typed term-edge reads separately, and `dirty_by_writeset` clears a reader cursor when one of those term resources changes. A write that only adds a new match candidate can still use the incremental cursor path.

## Result

| Case | Progressing firings | Direct final edge count | Reader value | Oracle agreement |
|---|---:|---:|---:|---|
| Typed edge insertion | 3 | 1 | 1 | Yes |
| Typed edge deletion | 3 | 0 | 0 | Yes |
| Match and term edge overlap | 3 | 2 | 2 | Yes |

The run used the rebuilt native extension without replacing the worktree's existing extension file. Raw data, exact source/build hashes, and environment are recorded in [`substrate_term_edge_wakeup_20260924.json`](../../../evaluation/reports/substrate_term_edge_wakeup_20260924.json). Reproduce with [`substrate_term_edge_wakeup_pilot.py`](../../../scripts/substrate_term_edge_wakeup_pilot.py) using a fresh native package built from the recorded source.

The same insertion case was rerun against the pre-fix native binary: it made two progressing firings, left the reader at 0, and the final graph oracle counted 1 edge. The old binary hash and outcome are preserved in [`substrate_term_edge_wakeup_prefx_20260924.json`](../../../evaluation/reports/substrate_term_edge_wakeup_prefx_20260924.json). Its exact source snapshot was not retained, so treat this as a binary-identified diagnostic control rather than a fully reproducible build comparison.

## Claim boundary and next work

These results establish corrected behavior for typed `Edges` insertion, deletion, and one overlapping match/term edge type case in the default runner mode. They do not establish coverage for any-type traversals, `EdgeAttr`, predicate retraction, other execution modes, or broader workload parity. The next evaluation expands these cases and checks whether full cursor invalidation changes closure cost on representative rules.
