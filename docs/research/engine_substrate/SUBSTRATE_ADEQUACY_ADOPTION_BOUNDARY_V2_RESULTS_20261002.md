# Cross-family adequacy-gated adoption boundary v2 — results

Date: 2026-10-02

## Result

All **8/8 independent analyzer gates pass** across nine unique fresh workers covering three task families × three repetitions. Source, native, oracle and fixture locks remained stable. In each worker, the signed false label was rejected before `_teach_shape` and left the relevant code-write shape inventory and epoch unchanged. The truthful signed label was accepted.

The accepted `_teach_shape` boundary produced the same exact full-graph delta for parity, clamp, and square: one new `ShapeSignature`, one pending `ShapeObservation`, one existing Agent record updated with `write_codebook_epoch = 1` and `meta_codebook_epoch = 0`, and no edge additions or removals. There were no other node changes. The analyzer independently recomputed task labels, receipts, HMAC authentication, and native held-out predictions against the separate oracle; all held-out outputs matched (303/303 total).

| Task family | Held-outs per worker | Median `_teach_shape` time |
|---|---:|---:|
| Parity | 41 | 0.526 ms |
| Clamp | 20 | 0.483 ms |
| Square | 41 | 0.518 ms |

The timings cover the instrumented adoption function, including `teach()` and the codebook epoch update. They exclude request construction, parse/Term reading, conversation bootstrap, and the enclosing live `converse` route. Three workers per family provide mechanism replication, not a timing confidence interval.

## Interpretation and limits

This extends the narrow adoption graph-delta invariant from square alone to three distinct authored Term families, including a three-argument clamp function. It supports the claim that this code-write adoption boundary is bounded and repeatable on these fixtures. It does not establish all-caller graph safety, natural-task transfer, oracle independence beyond the checked source module, provider truth, autonomous proposal generation, or general program induction. The separate v1.2 full-conversation gate still fails because the first turn lazily adds hundreds of nodes and edges outside `_teach_shape`.

Next test more independent task families and code-teaching callers, then measure warmed full-conversation adoption and no-adoption controls with cold initialization recorded separately. Continue reporting candidate discovery and acquisition cost separately from application of held structure.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V2_PREREG_20261002.md)
- [Implementation boundary](../../../domains/code_write_growth.py) and [authenticated route](../../../domains/adequacy_provider_auth.py)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_adoption_boundary_v2.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_adoption_boundary_v2_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_adoption_boundary_v2_analysis_20261002.json)
- [Independent oracle and fixtures](../../../evaluation/substrate_capability/independent_codewrite_oracles.py)
