# Contract query batched prediction matrix v1.1 — confirmation amendment

The first v1 capture completed all 18 workers with stable source/native hashes and matched histories, but its independent analyzer stopped at an incorrect matrix-cell accounting assertion. `TermPredictionMatrix` precomputes each nonempty candidate input and lazily adds the initial observation at x=0, which is outside the candidate grid. Therefore the expected cell count and native-call count are `H × (N + 1)`, not `H × N`. The recorded v1 counts agree with the implementation and raw capture; no result is claimed from the pilot.

V1.1 corrects that independent accounting expectation and retains all semantic and performance gates. The matrix implementation, workload, oracle, and decision rule are unchanged. The confirmation uses a new source lock, runner, analyzer, and raw capture so the pilot remains immutable and the analyzed code is covered by the confirmation lock. The performance decision remains at least 1.25× median speedup in both H=128 and H=512 with no more than 2× peak RSS, after exact pairwise semantic parity.

- Base protocol: [v1 preregistration](SUBSTRATE_CONTRACT_QUERY_BATCHED_PREDICTIONS_V1_PREREG_20261002.md)
- Confirmation runner: `evaluation/substrate_capability/substrate_contract_query_batched_predictions_v1_1.py`
- Confirmation analyzer: `evaluation/substrate_capability/analyze_substrate_query_batched_predictions_v1_1.py`
