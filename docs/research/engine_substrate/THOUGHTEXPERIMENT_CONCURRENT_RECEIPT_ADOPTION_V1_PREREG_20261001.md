# Thoughtexperiment concurrent receipt adoption v1 — preregistration

**Date:** 2026-10-01  
**Question:** When independent branches are forked from one primary revision and their nonempty receipts race to commit, does guarded adoption admit exactly one receipt and reject the rest without partial or lost writes?

## Design

Use three isolated branches created from one immutable snapshot of a primary graph containing three distinct target nodes. Each branch changes one target's `experiment_value` attribute under a delta journal. Verify the primary remains unchanged and each receipt is nonempty before the race. Launch three worker threads behind a barrier and call `apply_experiment_graph_delta()` with the same captured revision token.

Run ten races in each of three fresh worker processes (90 receipt submissions). The receipt targets are disjoint, but every branch is based on the same global revision. Therefore the contract under study is strict stale-base rejection, not automatic merge: exactly one receipt may publish; the other two must fail on the now-stale revision. Which branch wins is intentionally unspecified. After each race, compare the complete primary graph with an independently constructed oracle containing only the winning branch's mutation. Confirm that failed branches' values did not leak into the primary.

Capture source and native binary hashes before and after, per-attempt outcomes/errors, branch isolation, receipt effect counts, winner identity, oracle parity, and timing from barrier release through all three returns. Timings are descriptive for this host and fixture.

## Gates

- Three fresh worker PIDs, ten races per worker, 90 total receipt submissions.
- All three branch receipts are nonempty and each branch leaves the primary graph unchanged before commit.
- Exactly one successful adoption and two stale-revision rejections per race.
- Each rejected attempt leaves primary state unchanged at the point it returns.
- Final complete graph equals the base plus exactly the winner's declared attribute change.
- Stable source/build fingerprints throughout each worker.

Any failure invalidates the corresponding concurrency claim. Do not interpret the test as proving lock-free parallel execution, merge semantics for disjoint receipts, fairness, throughput under production load, or safety for state outside the revision token.
