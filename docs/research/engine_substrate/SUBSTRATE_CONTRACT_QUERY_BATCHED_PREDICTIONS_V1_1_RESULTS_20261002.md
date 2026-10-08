# Contract query batched prediction matrix v1.1 — results

**Result:** all six preregistered gates pass in 18 fresh source/native-locked workers. The v1 pilot is retained as diagnostic only; its analyzer expected `H×N` matrix cells although the algorithm also evaluates the initial observation at x=0. The amendment corrects the expected count to `H×(N+1)` and the confirmatory capture uses a new lock.

| Workload | Uncached median | Matrix median | Speedup | Uncached native calls | Matrix calls/cells | Peak RSS ratio |
|---|---:|---:|---:|---:|---:|---:|
| H=32, N=500 | 454.26 ms | 242.85 ms | 1.87× | 62,796 | 16,032 | 1.02× |
| H=128, N=28 | 188.69 ms | 105.98 ms | 1.78× | 18,868 | 3,712 | 0.99× |
| H=512, N=36 | 1,317.22 ms | 703.69 ms | 1.87× | 98,204 | 18,944 | 1.01× |

Within each of the nine paired cells, query order, entropy, predictions, oracle labels, terminal reason, and final survivor match exactly. An independent closed-form oracle verifies selected predictions and tie-breaking. Matrix storage estimates are approximately 14–101 KB in these workloads. The current selector repeats prediction work as observations accumulate; the matrix computes each hypothesis/environment pair once and reuses it throughout the query sequence.

## Misspecification and claim boundary

Both arms preserve the same known limitation: a target that agrees with one supplied hypothesis on every available candidate input reaches that finite singleton even though its held-out output at x=999 differs by 100. Batching reduces work; it does not validate the hypothesis space or make a singleton trustworthy. The implementation is opt-in and restricted to pure, immutable Term/input sequences. The speed and memory measurements are from one host and three small coded families; broader operators, partial domains, task-generated hypotheses, and production integration remain unmeasured. Keep the ordinary selector as the default until that follow-up is complete.

## Artifacts

- [Base preregistration](SUBSTRATE_CONTRACT_QUERY_BATCHED_PREDICTIONS_V1_PREREG_20261002.md)
- [Confirmation amendment](SUBSTRATE_CONTRACT_QUERY_BATCHED_PREDICTIONS_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_batched_predictions_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_batched_predictions_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_batched_predictions_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_contract_query_batched_predictions_v1_1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_batched_predictions_v1_1_analysis_20261002.json)
