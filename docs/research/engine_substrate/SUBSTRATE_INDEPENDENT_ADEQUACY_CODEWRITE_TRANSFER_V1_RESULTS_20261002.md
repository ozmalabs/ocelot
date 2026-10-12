# Independent adequacy gate on code-write acquisition v1 results

The source-locked panel passed all 32 analyzer checks across three fresh,
full-seed worker processes. Starter-codebook baselines abstained for parity,
clamp, and square. Strict evidence accepted both positive tasks; each added one
write shape and advanced the codebook epoch once. The native Term and emitted
Python both matched the separate source-hashed oracle on all held-out cases:

| Task | Per-worker held-out | Total exact native/Python matches |
|---|---:|---:|
| Parity | 41 | 123/123 |
| Clamp | 20 | 60/60 |
| **Combined** | **61** | **183/183** |

The negative control supplied `identity(x)=x` for a square request. Its only
acquisition example (`x=1 -> 1`) matched both candidate and contract, but the
fresh square probes rejected the Term in all three workers. No
`taught_identity` shape appeared and the codebook epoch did not change. Labels
carry the SHA-256 identity of the distinct
[`independent_codewrite_oracles.py`](../../../evaluation/substrate_capability/independent_codewrite_oracles.py)
module, and the analyzer recomputes each labeled value from that source.

Median full-seed boot was 16.68 s; positive receipt acceptance plus teaching
took 21.57 ms for parity and 22.24 ms for clamp; negative refusal took 5.84 ms.
Seed persistence was disabled for this in-memory acquisition panel; persistence
and restart were measured separately. The three functions and oracle outputs
are authored for this evaluation. Source hashing and recomputation improve
auditability but do not authenticate an external oracle or establish task
prevalence. This is example-supervised codebook growth, not autonomous
candidate generation or general program induction.

Artifacts:

- [Preregistration](SUBSTRATE_INDEPENDENT_ADEQUACY_CODEWRITE_TRANSFER_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_independent_adequacy_codewrite_transfer_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_independent_adequacy_codewrite_transfer_v1_lock_20261002.json)
- [Oracle module](../../../evaluation/substrate_capability/independent_codewrite_oracles.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_independent_adequacy_codewrite_transfer_v1.py)
- [Raw capture](../../../evaluation/reports/substrate_independent_adequacy_codewrite_transfer_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_independent_adequacy_codewrite_transfer_v1_analysis_20261002.json)
