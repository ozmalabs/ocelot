# Concurrent CoW branch lifecycle v1 preregistration

**Status:** preregistered native Rust measurement; independent of the sequential Python prefix probe.

**Amendments:** the first diagnostic found a repeatable 24-byte-per-worker baseline offset after joins. The [first amendment](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_AMENDMENT_20261001.md) added a thread-only control; a follow-up showed that control's delta is zero and does not explain branch-bearing drift. The [second amendment](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_AMENDMENT_2_20261001.md) adds a backend-matched fork/drop/no-mutation control. Reclamation is evaluated relative to the latter; retain the thread-only values as instrumentation context.

## Question

Can one immutable `Substrate` snapshot be forked and mutated by concurrent Rust workers, retain sibling isolation while a subset is cancelled/dropped, and return measured live Rust allocator bytes to the pre-wave baseline after all branches are dropped? How does this compare with concurrent eager full-copy branches?

## Protocol

- Use a native Rust fixture with an instrumented `System` global allocator that tracks currently live requested allocation bytes. Capture the baseline after the primary graph, snapshot (for CoW), and synchronization controls are built.
- Cross base graph sizes `{10,000, 50,000}` nodes, fanouts `{1, 4, 16}`, backends `{shared snapshot fork, eager full-copy fork}`, and five randomized-order paired repetitions per cell.
- Each worker concurrently forks one branch, inserts one uniquely typed node, validates the base graph count and branch-local insertion, and waits at a ready barrier while all branches remain alive. Matched thread-only and same-backend fork/drop/no-mutation waves run for each fanout.
- Cancel/drop half the branches (zero at fanout 1); surviving branches must still validate. Release survivors and join all threads.
- Record live allocator bytes at baseline, all-branches-live, after cancellation, and after all branches are dropped. Each wave must return exactly to its own baseline. The stable `Arc` snapshot and primary remain alive across both backend arms.
- Check primary and later snapshot-fork state against the original graph; compare all branch outcomes across backends.

## Gates

1. `ExperimentSnapshot: Send + Sync` and concurrent worker execution succeeds.
2. All branch writes remain local; primary and later forks preserve the base graph.
3. Cancellation of half the branches leaves every survivor valid.
4. Eager and shared-snapshot outcomes match exactly for each paired repetition.
5. Instrumented live requested bytes increase while branches are live and decrease after cancellation when branches are cancelled. After all workers join, the mutation wave's raw delta must equal the paired same-backend fork/drop control delta; the mutation-adjusted residual must be exactly zero.
6. The capture records source/binary/toolchain hashes and the complete cell schedule; any semantic or allocation-return failure aborts the panel.

## Limits

The allocator counts requested Rust allocation payload sizes, not allocator metadata, RSS/PSS, GPU memory, or object-level attribution. Thread-launch/synchronization allocations are included in the concurrent wave delta. Results apply to one host and the tested synthetic graph family. This measures concurrent branch lifecycle and native reclamation, not a serving adapter, vLLM/KV compatibility, scheduler behavior, or application throughput.
