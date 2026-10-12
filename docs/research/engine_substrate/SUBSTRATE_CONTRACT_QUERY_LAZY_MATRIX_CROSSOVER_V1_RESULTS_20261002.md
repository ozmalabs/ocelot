# Contract-query lazy matrix crossover v1 — results

**Result:** all eight preregistered gates pass across 36 fresh source/native-locked workers. Paired histories, entropy, ordered predictions, labels, terminal states, and survivors match exactly; independent closed-form checks confirm the best query and tie-breaks. The off-grid target still reaches the same false singleton in both arms. The performance decision rule passes for both H values at m=0 and m=4.

| H | Initial distinguishing observations m | Survivors | Follow-up queries | Uncached | Lazy matrix | Speedup | Native calls uncached → matrix | Matrix bytes (approx.) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 0 | 128 | 7 | 204.58 ms | 114.22 ms | 1.79× | 9,434 → 3,712 | 29.9 KB |
| 128 | 4 | 8 | 3 | 36.30 ms | 23.99 ms | 1.51× | 1,834 → 560 | 5.6 KB |
| 128 | 7 | 1 | 0 | 7.20 ms | 11.53 ms | 0.63× | 382 → 382 | 3.2 KB |
| 512 | 0 | 512 | 9 | 1,327.61 ms | 667.54 ms | 1.98× | 49,102 → 18,944 | 160.8 KB |
| 512 | 4 | 32 | 5 | 314.89 ms | 158.10 ms | 1.99× | 11,022 → 2,496 | 22.4 KB |
| 512 | 9 | 1 | 0 | 42.12 ms | 56.10 ms | 0.75× | 1,534 → 1,534 | 12.9 KB |

The current lazy implementation meets the preregistered ≥1.25× speed threshold when the sequence contains three or more follow-up queries; peak RSS ratios are 1.00× in all cells at the host's process-level sampling resolution. Approximate logical matrix bytes scale with evaluated survivor/input pairs and are more informative at this small size. At m=K, no candidate prediction cells are evaluated after the initial observations identify a singleton, but the cache-mediated observation scan remains slower than direct evaluation. Use the uncached route for already-resolved/single-query tasks unless a caller has a separate reason to retain matrix state.

## Limits and next gate

This confirms the lazy revision's speedup on the same binary-coded Term family used in earlier work and exposes the query-depth crossover. It remains one host and two finite H values; it does not establish natural task behavior, arbitrary Term complexity, graph-dependent inference, or hypothesis-set adequacy. Both arms still accept a finite singleton that matches every selected input but is wrong at x=999. The next measurement should use task-generated hypothesis pools, partial domains, and larger/deeper Terms while preserving this misspecification control. Keep the matrix opt-in until that evidence exists.

## Artifacts

- [Preregistration](SUBSTRATE_CONTRACT_QUERY_LAZY_MATRIX_CROSSOVER_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_lazy_matrix_crossover_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_lazy_matrix_crossover_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_lazy_matrix_crossover_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_contract_query_lazy_matrix_crossover_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_lazy_matrix_crossover_v1_analysis_20261002.json)
