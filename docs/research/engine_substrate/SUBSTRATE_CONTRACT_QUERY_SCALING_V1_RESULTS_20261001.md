# Contract query scaling and misspecification v1 — results

All ten fresh source-locked workers completed without worker errors and with stable implementation/native fingerprints. For each closed-set scale cell, both workers identified the hidden candidate using exactly K=log2(H) oracle labels: 3 queries for H=8, 5 for H=32, and 7 for H=128. The independently replayed 2,000-trial random baseline per worker had median query counts of 10, 18, and 26, respectively.

| Hypotheses H | Term depth K | Candidate inputs | Median native Term evaluations | Median selector loop |
|---:|---:|---:|---:|---:|
| 8 | 3 | 12 | 226 | 2.16 ms |
| 32 | 5 | 20 | 1,638 | 22.85 ms |
| 128 | 7 | 28 | 9,434 | 178.59 ms |

The operation count and time increase faster than candidate count over these three cells because both the number of surviving hypotheses and the expression depth grow, and each selection round scores each unused input against every surviving Term. These data are consistent with that nested work structure; three synthetic sizes are not an asymptotic complexity proof. The measurement is local native-Term evaluation through Python orchestration on one host.

## Open-world outcomes

Two observations distinguish closed-set consistency from global correctness:

- When the external oracle's initial label contradicted every supplied hypothesis, both workers returned an empty survivor set and no query candidate.
- When the target matched one supplied hypothesis on the initial observation and all five selected informative probes, but differed by +100 at an unqueried unanimous decoy, both workers reduced the version space to singleton `h10`. At the held-out decoy x=15, the selected candidate predicted 15 while the oracle returned 115. The selector does not test inputs where all current hypotheses agree, so a singleton is only relative to the supplied set and queried evidence.

The second outcome is a demonstrated open-world blind spot, not a defect in entropy arithmetic. A robust learner needs an explicit model-adequacy or residual gate after version-space identification; the current selector cannot certify coverage beyond its hypotheses and probes.

The first independent analyzer pass used the wrong evaluation-count formula. Its correction follows the selector's sequential hypothesis filtering and is disclosed in the [analysis amendment](SUBSTRATE_CONTRACT_QUERY_SCALING_V1_ANALYSIS_AMENDMENT_20261001.md); raw data and worker execution are unchanged.

## Claim boundary and next gate

The finite selector handles up to 128 harness-authored Term hypotheses at the measured costs and efficiently locates sparse discriminating inputs. It does not generate the candidate programs, task, input domain, or trusted labels. At H=128, the 179 ms loop is already material relative to millisecond-scale local work; larger spaces require cost controls, expression caching/indexing, or a different search organization. Next measure H=256/512, expression depth independent of H, decoy-grid size, and caching; include operators with partial domains and a misspecified hypothesis set; then connect selected queries to a separately held oracle and charge end-to-end acquisition cost.

## Artifacts

- [Preregistration](SUBSTRATE_CONTRACT_QUERY_SCALING_V1_PREREG_20261001.md)
- [Analysis amendment](SUBSTRATE_CONTRACT_QUERY_SCALING_V1_ANALYSIS_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_scaling_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_contract_query_scaling_v1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_contract_query_scaling_v1_lock_20261001.json)
- [Capture](../../../evaluation/reports/substrate_contract_query_scaling_v1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_scaling_v1_analysis_20261001.json)
