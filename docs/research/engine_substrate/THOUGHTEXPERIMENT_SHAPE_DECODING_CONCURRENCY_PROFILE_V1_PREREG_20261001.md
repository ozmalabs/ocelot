# Shape-decoding concurrency phase profile v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does the threaded shape-decoding rehearsal overlap native CPU work, and which wall-time phases expand or shrink at fanout 8?

## Design

Repeat the source-locked 100k-node shape-axis fixture at fanout 8 for scoped full-copy and scoped shared-graph-page backends, sequential and barrier-synchronized concurrent modes, and three fresh-process repeats per backend/mode (12 processes). Compute the baseline prediction before timing. Call `imagine_and_check_convergence(..., _measure_phases=True, record_trace=False)` for each rehearsal. Record per-branch wall and `thread_time_ns` CPU, total wave wall, and existing phase timings for snapshot/setup, candidate patch, prediction, structural scan, and bounded forward look. The concurrent worker barrier aligns operation starts after thread-pool creation. Require all task outcomes and primary-state invariants to match.

## Gates

- 12 unique fresh processes, source/native-binary lock parity, 100k nodes, eight rehearsals per wave.
- Every run applies the shape-axis correction, is non-inert, converges, and preserves primary graph/rules/revision.
- Sequential/concurrent signatures match within each backend; both backends match semantically.
- Per-thread CPU and requested phase timings are present and nonnegative; report aggregate CPU/wall overlap and median per-phase wall demand.

## Interpretation limits

Thread CPU/wall ratios estimate simultaneous CPU execution, not GIL ownership or hardware-counter utilization. Wall phase timers include Python and native work. The panel can identify whether work overlaps and where time is spent, but cannot by itself prove that a specific Python or Rust phase caused the slowdown. It uses one task and host; three repeats are exploratory.
