# ProblemShape solver-family transfer v1.1 current-source replication

## Source update and integrity

The v1 capture demonstrated repeatable bridge-Goal structural transfer, but final audit found that the live worktree had since changed `substrate/boot_all.py` and `substrate/boot_profiles.py`. Since those files govern seed selection/indexing and boot memory, the same frozen task schedule was repeated on a read-only snapshot containing the updated versions. The amendment and v1 outcomes were already visible, so v1.1 is a source-current replication, not a new confirmatory sample.

The v1.1 runtime lock covers 311,889 source, seed, native, and runtime assets plus 9 explicit runner/protocol/analyzer/helper/build files. Parent before/after hashes match; both workers used the same immutable lock; the analyzer passes integrity checks. Each full boot loads 731 manifests and reports the same 11 failures.

## Capability outcomes

Both workers reproduce the v1 transitions exactly. A seeded `solve_can_exact` Goal is recognized as `ps_has_targets_mt=yes`. Three resolved `can_to_deduction` Goals over distinct settled resident networks yield `residual → minted/recognized → recognized`; the first is re-decoded, and all three finish covered by `ps_has_direction=can_to_deduction_has_targets_mt=yes`. One resolved `deduction_to_can` near-neighbor remains residual and causes no additional mint. All eight underlying CAN exact/bridge Goals resolve through their registered resolvers.

## Boot and observation cost

| Source snapshot | Boot wall, two workers | Boot process CPU | Peak RSS |
|---|---:|---:|---:|
| v1 snapshot | 11.86 / 11.93 s | 13.17 / 13.18 s | 1.754 / 1.754 GiB |
| v1.1 updated snapshot | 12.81 / 14.88 s | 14.03 / 16.33 s | 1.752 / 1.753 GiB |

Instrumented per-observation wall time is 13.80–18.58 ms in v1.1. Candidate/Term counts per observation remain exactly the same as v1: seeded exact 7/71; bridge observations 16/139, 36/540, 28/195; opposite-direction control 40/289. These two-process ranges cannot attribute the apparent boot-time increase to the `boot_all.py` edits; startup noise and the edited `boot_profiles.py` also differ. They do show that the measured full-boot cost remains much larger than each ProblemShape observation at this fixture size. Import startup is excluded from the boot timer.

## Interpretation and boundary

The bridge transfer behavior is robust across these two locked source snapshots. The updated boot code preserves loaded/failure counts and every solver/ProblemShape outcome. Peak memory changes by only a few MiB in this run. This does not establish bridge answer quality, semantic correctness, natural residual frequency, general induction, or a causal boot optimization. The source versions and raw work records remain separate.

## Artifacts

- [V1.1 amendment](SUBSTRATE_PROBLEM_SHAPE_SOLVER_FAMILY_TRANSFER_V1_1_AMENDMENT_20260927.md)
- [V1 preregistration](SUBSTRATE_PROBLEM_SHAPE_SOLVER_FAMILY_TRANSFER_V1_PREREG_20260927.md)
- [V1 results](SUBSTRATE_PROBLEM_SHAPE_SOLVER_FAMILY_TRANSFER_V1_RESULTS_20260927.md)
- [V1.1 runner](../../../scripts/substrate_problem_shape_solver_family_transfer_v1_1.py)
- [V1.1 analyzer](../../../scripts/analyze_substrate_problem_shape_solver_family_transfer_v1_1.py)
- [V1.1 lock](../../../evaluation/substrate_capability/problem_shape_solver_family_transfer_v1_1_lock_20260927.json)
- [V1.1 raw workers](../../../evaluation/reports/problem_shape_solver_family_transfer_v1_1_20260927.json)
- [V1.1 analysis](../../../evaluation/reports/problem_shape_solver_family_transfer_v1_1_analysis_20260927.json)
