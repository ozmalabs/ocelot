# Full-seed GenInfer training work profile — results

The nine-worker native audit capture and independent reconciliation gate pass. Every training closure exactly reconciles requests, cache hits, kernel calls, eligible bases, matrix attempts, and their rejection/survivor partition. The temporary 64-shard extension is source-matched; source manifests remain stable. Semantic gates for acquisition and held-out transfer pass.

## Work attribution

Across relation counts 4, 16, and 64, each training closure has a median of:

- 4 GenInfer requests = 2 cache hits + 2 kernel calls;
- 2 eligible bases, both at bound 5;
- 29,280 matrix attempts: two bases × `(2×5+1)^4 - 1`;
- zero apply rejects and zero candidate-structure rejects.

The residual check rejects 29,172 candidates at N=4 and 29,278 at N=16 and N=64. Candidate survivors fall from 108 at N=4 to 2 at N=16/64. Thus this panel's search count is fixed by the bound and eligible-base count; it does not grow with example count. Each candidate is still transformed and checked against the relation set, so the per-candidate work grows with the data. The source path applies each matrix to the signature, sorts candidate relations, and checks aligned pairs and slots. These operations explain why elapsed time can grow while matrix-attempt count stays constant.

Audit-enabled training medians are 54.024 ms, 212.257 ms, and 872.736 ms at N=4/16/64. The 16× increase in relation count yields a 16.15× time increase across these endpoints. The prior uninstrumented panel showed a similar trend, but the audit capture's timings include instrumentation and are diagnostic. This finite range is consistent with relation-linear work for fixed B and fixed coordinate dimension; it does not establish asymptotic complexity. The search contains the explicit matrix enumeration term `(2B+1)^4 - 1` per eligible base in the implemented 2D path. Although a general n-dimensional matrix search would have an `n²` exponent, the current `eval_gen_infer` skips signatures unless they have exactly two coordinate dimensions; higher-dimensional induction is unsupported rather than merely unmeasured.

## What this changes

The major measured GenInfer training cost is not growth in the number of matrix candidates as more relations are added. It is repeated per-candidate transformation and residual checking over those relations. Bound growth is a separate cost axis and can be much steeper. This distinguishes two engineering questions: reduce work per candidate without changing the candidate set, and constrain or better order bound-driven candidate enumeration without losing exact behavior.

The next gate should vary bound (for example B=3/5/7) and relation count independently, preserve positive and corrupted controls, and reconcile attempts against the exact formula for every cell. Use the already available per-rule/native audit to identify whether any proposed early rejection saves measured term work. Do not change enumeration order or add a prefilter without exact candidate/result parity on a separately locked implementation comparison.

The profile applies only to one authored 2D shape family and full-seed boot on one host. It does not establish world-level frame locality, typical bound distribution, or rung-three tractability across concept classes.

## Artifacts

- [Preregistration](SUBSTRATE_GENINFER_TRAINING_WORK_PROFILE_V1_PREREG_20261006.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_training_work_profile_v1.py)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_training_work_profile_v1_20261006.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_training_work_profile_v1_analysis_20261006.json)
