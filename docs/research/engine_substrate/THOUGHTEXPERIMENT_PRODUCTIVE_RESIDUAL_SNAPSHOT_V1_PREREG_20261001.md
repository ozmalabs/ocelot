# Productive Thoughtexperiment residual over reusable snapshots v1 preregistration

Date: 2026-10-01

## Question

Can a reusable immutable snapshot serve repeated productive Thoughtexperiment branches that return a nonempty graph residual, with exact parity against eager full-copy and direct shared-page branches? What branch setup, native collapse, and sparse residual-readout costs appear as unrelated base state grows?

## Frozen workload

- Reuse the established one-rule hypothesis-inference fixture: a graph-resident rule matches an injected `Hypothesis --contradicts--> Fact` and `Fact --stale--> Stale`, then changes the Fact attribute, adds a Conclusion node and `yields` edge, and deletes the stale node and edge. Run with a two-step budget, require exactly one productive step followed by convergence, and require a separate one-step terminal probe to make zero progress.
- Add 0, 10,000, or 50,000 unrelated nodes in a disconnected chain. Focus the branch on the Fact with two-hop scope; inject one hypothesis node per branch with a deterministic distinct branch ordinal.
- Compare `native_full_copy_scoped`, `native_shared_graph_pages_scoped`, and `native_reusable_snapshot`. Each worker captures one reusable snapshot from the fixed primary after setup, then evaluates five isolated hypothesis branches per backend. Reusable branches all fork from that same captured snapshot. Backend order alternates by repeat index.
- Run five fresh worker processes per size (15 total). In each worker, record whole backend-batch time and per-branch phase timings, including sparse journal residual readout. Keep the primary unchanged; require each branch to have nonempty `derived_only` residuals containing added, changed, and deleted nodes plus added and deleted edges; require exact equality of full and derived residuals across all three storage paths for the same ordinal; and require a later reusable fork to retain the untouched base.
- No branch residual is applied to the primary in this experiment. Report adoption/merge as an unmeasured lifecycle step unless the repository has an explicit guarded commit API.

## Gates and limits

Require all 15 fresh workers, five branches in each backend arm, exact nonempty residual parity, unchanged primary state, and later-fork isolation. Report per-backend median batch and phase costs; no speed threshold is imposed. One authored rule, one focus topology, and one host do not establish natural-task performance, concurrent mutation safety, cancellation/reclamation bounds, or vLLM compatibility. Changed-object counts are semantic residual size, not all mutation attempts or cloned pages.
