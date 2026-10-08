# Rule-family engine pilot results

**Status:** exploratory semantic and instrumentation pilot; not a termination theorem or confirmatory envelope.

## Question and method

Do three graph-authored rule behaviors run through the same native Substrate executor and produce independently checkable settled states across sparse and dense directed inputs?

The families are:
- **Transitive closure:** two rules derive all pairs joined by a path of length at least two.
- **Duplicate no-op:** one rule attempts to add the matched input edge again; it should settle without changing state.
- **Bounded mint:** one rule uses AddNodeIfAbsent with a fixed type/attribute key and links each distinct input-edge source to the shared witness. The oracle expects exactly one new witness node and one witness edge per distinct source.

The pilot crossed these three families with path, banded-DAG, and complete-DAG inputs at n=6 and 10. Every instance ran in a fresh worker, with scale audit enabled. An independent Python graph oracle determined expected edge counts; expected witness node growth was specified directly by the bounded-mint construction. A one-step terminal probe checked settlement.

Raw manifest and per-instance records: [rule-family pilot JSON](../../../evaluation/reports/substrate_rule_family_pilot_20260924.json). The harness and analysis rules are in [the closure pilot script](../../../scripts/substrate_capability_closure_pilot.py).

## Results

All 18 instances returned the exact expected graph size and a zero-work terminal probe.

| Rule family | Topology | n | Input edges | Output edges | Minted nodes | Candidate pairs | AddEdge attempts | Progress steps |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Transitive closure | Path | 6 | 5 | 15 | 0 | 19 | 10 | 4 |
| Transitive closure | Path | 10 | 9 | 45 | 0 | 53 | 36 | 8 |
| Transitive closure | Banded DAG | 6 | 9 | 19 | 0 | 39 | 21 | 2 |
| Transitive closure | Banded DAG | 10 | 17 | 53 | 0 | 115 | 77 | 4 |
| Transitive closure | Complete DAG | 6 | 15 | 25 | 0 | 55 | 30 | 1 |
| Transitive closure | Complete DAG | 10 | 45 | 81 | 0 | 285 | 204 | 1 |
| Duplicate no-op | Path | 6 | 5 | 5 | 0 | 5 | 5 | 0 |
| Duplicate no-op | Path | 10 | 9 | 9 | 0 | 9 | 9 | 0 |
| Duplicate no-op | Banded DAG | 6 | 9 | 9 | 0 | 9 | 9 | 0 |
| Duplicate no-op | Banded DAG | 10 | 17 | 17 | 0 | 17 | 17 | 0 |
| Duplicate no-op | Complete DAG | 6 | 15 | 15 | 0 | 15 | 15 | 0 |
| Duplicate no-op | Complete DAG | 10 | 45 | 45 | 0 | 45 | 45 | 0 |
| Bounded mint | Path | 6 | 5 | 10 | 1 | 10 | 10 | 1 |
| Bounded mint | Path | 10 | 9 | 18 | 1 | 18 | 18 | 1 |
| Bounded mint | Banded DAG | 6 | 9 | 14 | 1 | 18 | 18 | 1 |
| Bounded mint | Banded DAG | 10 | 17 | 26 | 1 | 34 | 34 | 1 |
| Bounded mint | Complete DAG | 6 | 15 | 20 | 1 | 30 | 30 | 1 |
| Bounded mint | Complete DAG | 10 | 45 | 54 | 1 | 90 | 90 | 1 |

The no-op rule does not report a progressing step and leaves the graph unchanged, while still enumerating and attempting its duplicate writes. The bounded-mint rule creates one witness node, then settles after adding witness links for the distinct sources. Its edge-attempt count matches the number of matched input edges because duplicate derivations after each source's first link do not occur for this workload. On dense inputs, candidate work rises with the number of input edges.

## Limits

The bounded-mint result demonstrates termination for one explicitly deduplicated rule construction on tiny finite graphs. It does not establish termination for unrestricted minting or prove weak acyclicity. The no-op case tests one duplicate-add behavior, not deletion cycles, conflicting updates, or arbitrary cyclic rules. These runs have no repeated measurements, budget-boundary sweeps, dense sizes beyond n=10, host orchestration, or independent custody.

Progress steps are not fixpoint passes or a typed terminal result. Settlement is established here by the independent graph oracle plus the one-step no-work probe. All performance figures are diagnostic only.

## Next gate

Add a bounded cyclic deletion/recreation workload and an unrestricted fresh-node growth workload with explicit step/memory caps. Preserve termination, cap, and crash as distinct outcomes. Then scale no-op and bounded-mint families over repeated isolated sizes and include them in the preregistered core-engine suite.

