# Full seed boot stage profile results

Date: 2026-09-25  
Status: four fresh profiled boots; full-state parity passed

## Findings

Four fresh processes loaded the locked 833-manifest snapshot in cold/warm/warm/cold cache order. All produced identical node and edge counts, serialized graph, grammar, rule store, access sets, active-rule order, and load report: 24,784 nodes and 11,090 edges. Warm cache bytes were stable across both warm loads.

| Stage, cumulative cProfile time | Cold range | Warm range |
|---|---:|---:|
| `load_all_seeds` total | 35.16–36.52 s | 30.07–32.47 s |
| `_read_seed_index` | 3.63–4.38 s | 0.37–0.39 s |
| `_build_seed_index` | 2.85–3.58 s | not called |
| `_seed_sources_digest` | 0.25–0.27 s | 0.26–0.28 s |
| Native `load_seed_manifest` (748 calls) | 11.62–11.82 s | 9.83–11.71 s |
| `ensure_self_model` | 12.51–13.86 s | 13.09–13.28 s |
| Native `export_rules` (inside self-model; one call) | 5.97–6.05 s | 5.44–6.05 s |

The table reports cumulative profiler time. Parent and child rows overlap and must not be added. JSON loads also remain substantial: 1,570 calls / 5.76–6.16 s in cold boots versus 738 calls / 3.07–3.45 s warm. `ensure_rule_provenance` walks more than a million structural read components in the profile. These data identify costs; they do not show that any stage is unnecessary or safe to defer.

## Interpretation and limits

The warm index avoids the index reconstruction pass, reducing the profiled `_read_seed_index` interval to under 0.4 s. It does not remove source-byte validation, per-manifest parsing/installation, or the full rule/provenance export performed at boot. Native manifest loading and boot-time self-model provenance are larger recurring contributors than warm index validation. cProfile overhead is present throughout; profiler wall time is not a production latency estimate. The earlier unprofiled comparison remains the source for the rough 24–29 s boot interval.

The follow-up source audit found self-query, reflective rule selection/editing, conversation response, and frozen-core/collapse provenance consumers, confirming that the mirror has active behavior contracts. The unprofiled six-process repeat measured medians of 32.18 s cold and 26.75 s warm on the same corpus; it corroborates the long startup envelope without implying the mirror can be omitted ([consumer audit](SUBSTRATE_SELF_MODEL_BOOT_CONSUMER_AUDIT.md), [unprofiled repeats](SUBSTRATE_SEED_BOOT_UNPROFILED_REPEATS_RESULTS.md)). Next separate imports, manifest installation, and mirror construction on more than one corpus size. Any eager/lazy design must preserve complete rule/program/provenance coverage and downstream consumer behavior.

## Artifacts

- Protocol: [`preregistration`](SUBSTRATE_SEED_BOOT_PROFILE_PREREG_20260925.md)
- Runner: [`profile probe`](../../../scripts/substrate_seed_boot_profile_v1.py)
- Raw report: [`four-run cProfile data`](../../../evaluation/reports/substrate_seed_boot_profile_v1_20260925.json)
- Workload-level startup baseline: [`cold/warm ProblemShape result`](SUBSTRATE_SEED_INDEX_COLD_WARM_PROBLEM_SHAPE_RESULTS.md)
