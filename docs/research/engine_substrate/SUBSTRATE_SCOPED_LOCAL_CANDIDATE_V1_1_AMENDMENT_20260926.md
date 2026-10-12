# Scoped local-candidate V1.1 amendment

**Amends:** [`SUBSTRATE_SCOPED_LOCAL_CANDIDATE_PREREG_20260926.md`](SUBSTRATE_SCOPED_LOCAL_CANDIDATE_PREREG_20260926.md)  
**Reason:** the first order-control pilot compared one scoped progress step with unscoped `run_rules(1)`. Those are not equivalent oracles: unscoped closure applies multiple progressing bindings within its pass and ended on the second source, while scoped cold closure applies the first progressing binding and then returns at its requested progress cap. The first pilot's three focused gates fail for this oracle mismatch; its raw capture and runner are preserved.

## Corrected order gate

For the order-sensitive two-match case, compare the optimized scoped call against the same scoped API forced onto its existing full-match/filter fallback. The control forces fallback by deleting an unrelated edge after installing the ordered `choice_edge` inputs; it does not delete or reorder either choice edge. Both scoped arms run with progress cap 1. The fixture's independent construction order is `first` then `second`; the scoped rule sets the target to the first binding and stops, so both arms must yield `selected="first"` and one progress step. The unscoped full closure is retained as a descriptive reference, but its final `selected="second"` is expected because it continues applying both progressing bindings in the closure pass.

## Unchanged gates

The exact-order requirement, local-path counter, delete/reuse fallback, multi-edge fallback, topology parity, notification coverage, omission sensitivity, and provenance gates remain. V1.1 captures to new raw/analysis paths and never overwrites V1.
