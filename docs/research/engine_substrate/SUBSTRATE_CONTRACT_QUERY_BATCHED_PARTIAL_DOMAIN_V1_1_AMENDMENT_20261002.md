# Batched partial-domain selector v1.1 — confirmation amendment

The v1 panel passes exact parity across the eight operators and partial x/y inputs, but reveals eager work: when the initial observation already leaves one candidate, the matrix arm evaluates the complete 8×45 matrix before checking whether another query is needed. That is unnecessary work, even though absolute latency is below a millisecond.

The matrix was changed to populate cells lazily. It now evaluates only current survivors for an observation, filters them first, returns immediately for a singleton, and evaluates candidate inputs only for the remaining survivors. Previously computed cells are reused across later observations. V1.1 reruns the exact v1 workload, oracle, and semantic gates under a fresh runner, analyzer, lock, and capture. The base v1 capture remains immutable evidence for the eager implementation.

- Base protocol: [v1 preregistration](SUBSTRATE_CONTRACT_QUERY_BATCHED_PARTIAL_DOMAIN_V1_PREREG_20261002.md)
- Confirmation runner: `evaluation/substrate_capability/substrate_contract_query_batched_partial_domain_v1_1.py`
- Confirmation analyzer: `evaluation/substrate_capability/analyze_substrate_query_batched_partial_domain_v1_1.py`
