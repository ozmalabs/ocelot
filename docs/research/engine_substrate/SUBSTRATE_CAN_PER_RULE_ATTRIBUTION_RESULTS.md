# CAN per-rule work attribution — 2026-09-24

## Question and measurement

Which authored CAN rules generate the candidate work that aggregate measurements associate with sparse/banded graph workloads?

An opt-in extension to `scale_audit` records per-rule candidate pairs/tests, where evaluations/rejections, binding leaves/clones, rule enumerations, and effect attempts, keyed to the loaded native rule index. It also records Term invocation counts by variant and site-defined interior work units. The default remains off. [`scripts/substrate_can_per_rule_attribution.py`](../../../scripts/substrate_can_per_rule_attribution.py) ran 36 fresh worker processes: N=32 and N=128; path, banded-2, and complete topologies; both discrete modes; three replicates per cell; weight granularity 0.25. Each process compares an uninstrumented run with a fresh-graph run using global and per-rule audit.

The final artifact passed two gates for all 36 workers: (1) audited progress count and final graph state equal the uninstrumented run; (2) sums of per-rule candidate pairs/tests, where evaluations/rejections, binding leaves/clones, rule enumerations, effect attempts, total term evaluations/interior units, and each Term variant equal their respective global counters. This is operation attribution, not a wall-time split. The reported workload wall times below are from the uninstrumented run. Audit wall time was also captured: median audited/unaudited ratio was 2.74× over all 36 pairs, with a 1.82×–3.31× observed range. Per-rule term accounting uses opt-in mutex-backed table updates for each term invocation and variant, so this material overhead is expected; audit timing must not be used as workload timing.

Raw per-worker rows, counter tables, and provenance are in [`evaluation/reports/substrate_can_per_rule_attribution_20260924.json`](../../../evaluation/reports/substrate_can_per_rule_attribution_20260924.json). The temporary release extension SHA-256 is `6fbf02c857b4726637121e833d91c0f81af518b8b744a711ad441a48108f63ea`; Rust and PyO3 source hashes are recorded in the raw artifact. After identifying that the rule-attribution thread-local could remain set after an attempt, the audit now clears it at the end of fixpoint and one-shot rule attempts. The 36-worker paired sweep was rerun against a rebuilt temporary extension after adding traversal-work charges: graph/progress parity and all counter conservation checks pass. The extension was built into a temporary Python package; its hash is recorded in the raw artifact.

## Results

The table shows median candidate-pair counts by rule at 2-state / 0.25-granularity, across three identical-seed process replicates. The final column is total median wall time from the uninstrumented twin.

| N | Topology | Update_2state | Update_3state | Note coactivation | Hebbian mint | Hebbian reweight | Total candidates | Wall time |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 32 | Path | 128 | 128 | 4,224 | 39,412 | 72,176 | 116,068 | 29.69 ms |
| 32 | Banded-2 | 96 | 96 | 3,168 | 33,828 | 52,148 | 89,336 | 19.40 ms |
| 32 | Complete | 96 | 96 | 3,168 | 3,168 | 3,168 | 9,696 | 8.67 ms |
| 128 | Path | 384 | 384 | 49,536 | 1,747,038 | 3,277,622 | 5,074,964 | 1,159.23 ms |
| 128 | Banded-2 | 640 | 640 | 82,560 | 2,890,016 | 5,545,592 | 8,519,448 | 2,077.78 ms |
| 128 | Complete | 896 | 896 | 115,584 | 115,584 | 115,584 | 348,544 | 987.45 ms |

At N=128, the mint and reweight rules contribute 99% of path candidate pairs and 99.1% of banded-2 candidate pairs. At N=32 path, those same rules contribute about 96%. The state-update rules contribute little candidate enumeration in this workload. The dense graph produces fewer total candidates than the sparse and banded graphs, despite having far more edges. This confirms that raw edge count is a poor cost predictor for this authored workload.

Per-rule term-invocation counts at N=128 (same 2-state/fine-weight condition) add a second cost dimension:

| Topology | Rule | Candidate pairs | Term evaluations |
|---|---|---:|---:|
| Path | `can_native_note_coactivation` | 49,536 | 5,417,232 |
| Path | `can_native_hebbian_mint` | 1,747,038 | 8,741,718 |
| Path | `can_native_hebbian_reweight` | 3,277,622 | 16,589,326 |
| Banded-2 | `can_native_note_coactivation` | 82,560 | 10,834,300 |
| Banded-2 | `can_native_hebbian_mint` | 2,890,016 | 14,460,960 |
| Banded-2 | `can_native_hebbian_reweight` | 5,545,592 | 28,063,320 |
| Complete | `can_native_note_coactivation` | 115,584 | 15,789,444 |
| Complete | `can_native_hebbian_mint` | 115,584 | 593,152 |
| Complete | `can_native_hebbian_reweight` | 115,584 | 1,047,424 |

The complete graph has far fewer candidates than path/banded-2, but `can_native_note_coactivation` still makes 15.8 million term invocations. Its largest variant counts are 7,779,812 `Var`, 3,862,019 `Eq`, and 3,633,539 `Nth`; `Edges` and `Exists` are 56,670 each. This points to repeated variable/value/tuple traversal within the rule's conditions, rather than showing that `Exists` alone dominates. The expanded interior-work counter now charges `Edges` for emitted edges, `Exists` for predicate items examined (including early success), and `Nth` for sequence positions traversed. At N=128, median units by variant are path: 1.70M/1.19M/3.56M; banded-2: 3.43M/2.44M/7.32M; complete: 7.33M/3.63M/11.30M (`Edges`/`Exists`/`Nth`). These site-defined counts measure inspected items, not machine instructions; they should only be compared within the same variant/site meaning. `ReachableFrom` also counts neighbor entries scanned, but is not exercised by this CAN workload.

## Diagnosis and limits

Both dominant rules match the same four-edge skeleton: `mt -> a`, `mt -> b`, `a -> coact` (`coactivated_with`), and `coact -> b` (`coactivation_of`). That pairwise join is a concrete structural source for large candidate counts. Counts grow by roughly 44× for the path case and 85–106× for banded-2 when N increases fourfold from 32 to 128, depending on which Hebbian rule is counted. This is consistent with super-quadratic candidate-generation growth over these points, but two sizes do not establish an asymptotic complexity class. The topology contrast also shows that the current notion of frame boundary alone does not predict this cost.

This attribution identifies rules, candidate families, and Term variants, but it still does not split uninstrumented wall time among match expansion, individual variant implementations, locking, and effects. The effect counters remain attempts, not successful mutations. The workload uses a particular seed and one fixed weight granularity, and only three replicates per cell. The next measurement should compare safe matcher/index orderings on held fixed graph snapshots with exact-state checks, then validate one candidate frame cut with partitioned-versus-monolithic outputs. Any rule rewrite or structural partitioning proposal must preserve the registered two-tick Hebbian semantics and be tested against this baseline.
