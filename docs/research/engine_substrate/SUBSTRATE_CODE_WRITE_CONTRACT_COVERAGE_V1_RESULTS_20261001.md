# Code-write contract coverage v1 — results

All four source-locked full-boot workers completed without worker errors and retained stable implementation fingerprints. With the narrow contract (`0→0`, `1→1`), both workers accepted and taught `taught_identity` for a square request. The emitted construction was selected and wrote identity behavior; it failed the independent square oracle on all eight held-out observations across the two workers. With the discriminating contract, adding `2→4` caused both workers to refuse on that row and neither produced a `taught_identity` construction.

| Arm | Workers | Contract outcome | Held-out square outcome | Named acquisition |
|---|---:|---|---:|---|
| Narrow alias (`0`, `1`) | 2 | Accepted; all four supplied rows matched | 0/8 exact | `taught_identity` present and selected |
| Discriminating (`0`, `1`, `2`) | 2 | Refused at `2→4` | No write candidate | `taught_identity` absent |

Median full-seed boot was 15.83 s; median peak RSS about 1.81 GB. Median combined acquisition-call time was 58.53 ms for the narrow contract and 54.57 ms for the wide contract. The timing includes source reading and related work, as well as contract handling.

## Interpretation and measurement limitation

The contract guard works only when its supplied observations distinguish the candidate from the requested behavior. Two correct but weak observations allowed a semantically wrong reusable construction to enter the codebook; a single additional discriminating observation prevented that in this task. This makes probe selection and contract coverage the next capability boundary. It also demonstrates why contract-validation success alone must not be reported as task correctness.

The runner counted code-write construction signatures after full boot and after the combined read/teach call. Counts changed by +9 in the narrow arm and +8 in the refusal arm, so they do not isolate the teaching mutation. The raw capture lacks a post-read/pre-teach named-signature snapshot; the analysis therefore claims only presence/absence of the specific `taught_identity` construction, and does not attribute the aggregate count changes. See the [analysis amendment](SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_ANALYSIS_AMENDMENT_20261001.md).

This single integer function pair is an adversarial coverage demonstration, not a natural false-admission rate or general active-learning result. The external analyzer knows the square oracle; the substrate worker receives only the contract rows. A next study should compare substrate-selected boundary/contrast probes with random and caller-selected probes, with the expected labels held by an independent evaluator, and score discriminating power, query cost, and false admission across several operators and input domains.

## Artifacts

- [Preregistration](SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_PREREG_20261001.md)
- [Analysis amendment](SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_ANALYSIS_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_code_write_contract_coverage_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_code_write_contract_coverage_v1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_code_write_contract_coverage_v1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/substrate_code_write_contract_coverage_v1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_code_write_contract_coverage_v1_analysis_20261001.json)
