# Rule-family scale pilot results

**Status:** exploratory repeated size envelope; semantics checked, no complexity theorem or confirmatory claim.

## Question and method

Do duplicate no-op and bounded shared-witness mint rules preserve the previously observed behavior as candidate work grows? The run used the native PyO3 rule runner with scale audit enabled, isolated workers, three repetitions per condition, and path, banded-DAG, and complete-DAG inputs at n=16, 32, and 64 (54 workers total). An independent expected-state check and a terminal no-work probe were required for every worker. Raw provenance and records are in [the scale pilot JSON](../../../evaluation/reports/substrate_rule_family_scale_pilot_20260924.json); commands and harness are captured there and in the [pilot script](../../../scripts/substrate_capability_closure_pilot.py).

## Results

All 54 workers returned the expected edge/node counts, reported success, and passed the zero-work terminal probe. Each table entry is median across three workers; candidate count is rule matches enumerated and wall time includes the measured primary run.

| Rule family | Topology | n | Input edges | Median candidates | Median wall time (µs) |
|---|---|---:|---:|---:|---:|
| Duplicate no-op | Path | 16 | 15 | 15 | 41.41 |
| Duplicate no-op | Path | 32 | 31 | 31 | 45.01 |
| Duplicate no-op | Path | 64 | 63 | 63 | 50.94 |
| Duplicate no-op | Banded DAG | 16 | 29 | 29 | 44.47 |
| Duplicate no-op | Banded DAG | 32 | 61 | 61 | 48.39 |
| Duplicate no-op | Banded DAG | 64 | 125 | 125 | 60.09 |
| Duplicate no-op | Complete DAG | 16 | 120 | 120 | 65.33 |
| Duplicate no-op | Complete DAG | 32 | 496 | 496 | 192.72 |
| Duplicate no-op | Complete DAG | 64 | 2,016 | 2,016 | 803.54 |
| Bounded mint | Path | 16 | 15 | 30 | 56.52 |
| Bounded mint | Path | 32 | 31 | 62 | 65.58 |
| Bounded mint | Path | 64 | 63 | 126 | 79.67 |
| Bounded mint | Banded DAG | 16 | 29 | 58 | 59.17 |
| Bounded mint | Banded DAG | 32 | 61 | 122 | 82.77 |
| Bounded mint | Banded DAG | 64 | 125 | 250 | 105.60 |
| Bounded mint | Complete DAG | 16 | 120 | 240 | 104.74 |
| Bounded mint | Complete DAG | 32 | 496 | 992 | 334.85 |
| Bounded mint | Complete DAG | 64 | 2,016 | 4,032 | 1,480.11 |

The sparse families produce work roughly proportional to their edge count in this range. Complete-DAG work grows with density: the bounded-mint rule enumerates twice the input edge count because the witness links also participate in a subsequent match pass. These are observed workload relationships, not asymptotic proofs. The increase is consistent with candidate enumeration and does not isolate graph storage, cache, or audit overhead.

## Limits and next gate

This run only tests one duplicate-add rule and one fixed-key, idempotently deduplicated witness. It does not evaluate fresh-node growth without deduplication, cyclic deletion/recreation, rule interactions, adversarial attributes, or host orchestration. Three repetitions are descriptive and too few for performance inference. Continue with explicit step and memory caps on cyclic and unbounded-mint controls; preserve `settled`, `cap reached`, and `crash` as distinct outcomes. Before a confirmatory engine envelope, preregister the sizes, topologies, budgets, and acceptance criteria, and include a compiled-out instrumentation build as an ablation.
