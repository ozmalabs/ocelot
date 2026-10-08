# Task-generated residual transfer v1 preregistration

**Question.** Can the reusable snapshot, sparse mutation journal, and revision-checked receipt-adoption path preserve an existing substrate task's ordinary outcomes when it runs each event closure in an isolated branch?

## Workload

Replay the frozen ten-event `phase3_common_ground_stress.v1` fixture with the ordinary `conversation_discourse_state` seed and current discourse lifecycle rules. This task fixture predates and is independent of the CoW receipt panel; it is held out from the synthetic generated-residual family design, but is not claimed to be a natural-task sample. Compare three fresh `WorldAdapter` episodes per worker:

1. **Direct:** construct each event on the primary and run ordinary native closure there.
2. **Eager receipt:** construct each event on the primary, fork a guarded eager branch, journal its closure writes, and adopt the branch receipt against the captured graph/rule revision.
3. **Shared snapshot receipt:** construct each event on the primary, capture/reuse a shared snapshot, fork, journal its closure writes, and adopt the receipt against the captured graph/rule revision.

All three arms use identical fixture order, event construction, seed, active rules, and `run_rules(100_000)` closure API. For each event, the receipt arms begin and checkpoint the journal immediately before closure, finish it immediately afterward, then apply only the total `conclusions` delta. Verify the adopted primary against the branch before proceeding to the next event. Keep full serialized edge order as an observed outcome; do not require it to match because graph-delta adoption can append equivalent edges in a different order.

Run eight fresh worker processes. Counterbalance arm order by worker index. Record source/native fingerprints before and after each worker, event/goal identities, per-event closure steps and canonical graph-state digests, receipt effect counts, graph wire-order parity, expected goal transition paths, common-ground claims, and a terminal no-progress probe. The terminal probe in receipt arms runs on a read-only branch and must not mutate the primary.

## Gates

1. All workers use the current locked source/native inputs; every worker has a distinct PID and fingerprints remain unchanged.
2. All arms use the ten frozen events, create matching event and goal IDs, and pass the task's exact two-goal transition-path and common-ground oracles.
3. Per-event progress and canonical node/edge facts match Direct across all arms; every receipt's adopted primary matches its producing branch canonically before the next event.
4. Every terminal closure reports zero progress and preserves the full canonical graph state. Receipt-arm terminal probes produce empty graph deltas and leave the primary unchanged.
5. Report serialized graph wire equality separately from canonical semantic parity; a wire-order mismatch is not silently normalized or called exact equality.
6. Preserve all arms, workers, stage timings, errors, and receipts. Any missing worker, stale input, task-oracle failure, or canonical semantic mismatch makes the panel inconclusive.

## Measures and limits

Report event-construction, branch setup, rule closure, journal readout, receipt adoption, terminal-probe, and total episode timing separately. The main cost comparison is summed measured stage time per episode; Python-side oracle serialization is reported separately. This panel tests one authored task fixture and its actual task-generated closure residuals, not learned proposal quality, natural-task prevalence, general commit authorization, concurrent writers, large-graph scaling, or serving-runtime compatibility. Edge insertion order is tracked because consumers may observe it even when canonical graph facts match.

## Development pilot disclosure

A nonconfirmatory development replay produced equal event identity, closure progress, task path, common-ground claims, and canonical node/edge facts for Direct versus shared-snapshot receipt/adoption. Full serialized graph wire equality was false in both eager and shared receipt arms, while canonical facts matched. This confirms the edge-order risk is real and motivates the explicit wire-order observation above. Pilot timings and outcomes are excluded from the locked panel.
