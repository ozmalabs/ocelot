# Productive coactivation closure v1 preregistration

Date: 2026-10-01

## Question

How do coactivation population Q and installed matcher order affect work and outcomes when the production CAN Hebbian mint/reweight rules perform productive writes?

## Design

Use N={32,64,128}, Q={0,N,4N,floor(N(N−1)/4),N(N−1)}, and three fresh-process replicates per cell (45 workers). Construct Q distinct directed pairs from cyclic offsets. Every coactivation record is initially eligible at `can_tick=1` (`noted_tick=0`, `evidence_tick=0`); concepts have equal nonzero states. Half of the records, rounded down, have a pre-existing `causal_influence` edge and should take the reweight path. Remaining records have no such edge and should take the mint path. Disable all other seed rules. Compare authored and sparse-first match orders from independently built identical inputs.

Run full native rule closure with scale audit and a 100,000-step cap. Record actual installed order, progress, edge/evidence writes, per-rule and global candidate work, graph size, canonical graph-fact digest, and a terminal closure probe. Require exact canonical final graph parity between arms; allow wire-order and progress-count differences if state facts agree. Require all introduced pairs to receive their expected causal link, all evidence ticks to reach the active epoch, bounded completion, and audited/uninstrumented semantic parity on each arm. Counters must reconcile for the two active target rules.

## Gates

- Complete 45 unique worker cells with stable source/input lock.
- Exactly the two named Hebbian rules active; verify installed first-clause order.
- Both variants terminate below the cap and the extra terminal pass makes no change.
- Final causal-link and evidence state meets the fixture's explicit per-pair oracle.
- Canonical graph facts match across order arms; IDs/serialized edge order are not the parity oracle.
- Per-rule candidate tests reconcile with global `cand_tested` in every arm.

## Limits

This is a controlled synthetic productive-closure workload for two rules. The initial ledger is supplied, and half of its links are seeded to isolate mint and reweight paths. It does not measure natural coactivation frequency, rule learning, long-run task quality, or all CAN closure rules. Population sizes and graph sizes are finite; no asymptotic class or commodity-scale claim follows.
