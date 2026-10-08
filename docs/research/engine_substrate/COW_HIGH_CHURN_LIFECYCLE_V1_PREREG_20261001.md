# High-churn CoW branch lifecycle v1 preregistration

**Question.** Does repeated concurrent fork, branch-local mutation, partial cancellation, and full drop preserve branch isolation and adjusted allocator reclamation while the primary graph and reusable snapshot remain alive?

## Protocol

- Use a source-locked native Rust fixture and the same instrumented `System` allocator and backend-matched no-write fork/drop control as the concurrent lifecycle panel.
- Cross graph sizes `{10,000, 50,000}`, fanouts `{4, 16}`, backends `{shared snapshot, eager full copy}`, and 25 repeated waves per cell. Counterbalance backend order by repetition.
- In each wave, all workers fork one mutable branch, add one uniquely typed node, validate its local result and the unchanged base, then synchronize. Drop half the branches while the other half remain alive; validate survivors; then drop all survivors and join.
- Retain the same primary and reusable snapshot throughout all waves in a cell. At the end, validate the primary and a new fork from the retained snapshot against the original state.
- Capture live requested allocator bytes at baseline, all-live, after-cancellation, and after-drop; capture wave wall time. Subtract a same-backend no-write fork/drop control from allocation deltas. Raw drift and mutation-adjusted drift are reported separately.
- Record exact branch receipts (wave, worker, backend, inserted NodeID), semantic gates, toolchain/source/binary fingerprints, and the full schedule in each source-locked capture.

## Gates

1. Exact per-wave branch semantics and unique receipt coverage; eager/shared branch outcomes agree.
2. Primary and retained-snapshot state stay unchanged throughout all waves; post-run snapshot forks match the original base.
3. Cancelled branches release their measured share while survivors remain valid.
4. Every completed wave returns to its matched no-write control after adjustment; no increasing post-drop residual across wave index is allowed.
5. All declared cells and repetitions complete. Any semantic failure, missing receipt, stale source/build, or adjusted residual failure aborts the run.

## Limits

This isolates repeated native branch lifecycle on synthetic node-only graphs. It does not measure concurrent commit/adoption, natural-task distribution, a real serving runtime, full-Substrate RSS/PSS, or general scaling. Allocator-requested bytes exclude allocator metadata and resident-page effects. Passing is evidence for bounded high-churn isolation/reclamation only, not a universal leak-freedom proof.
