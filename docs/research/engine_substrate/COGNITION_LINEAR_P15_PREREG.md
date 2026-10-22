# P15 frozen evaluation preregistration

**Protocol:** `linear-p15-v1`
**Frozen:** 2026-10-22, after development validation and before any held-out draw.
**Implementation commit:** `11fb8c436fedce66d976369dfc7c89cc8ce6197e`.

## Purpose and claim boundary

This protocol measures three approved graph-authored generations of one finite permutation process macro. It is not a general invention, transfer, mechanism-learning, autonomy, or human-comparison evaluation. The only supported family is `permutation_process_macro`; mechanism discovery, grid transformations, tool invention, program synthesis, explain-and-rebuild, cross-domain transfer and law rediscovery are `UNSUPPORTED`. No external action adapter is installed. Human comparison is `UNAVAILABLE_PROTOCOL_NOT_MATCHED`.

The primary outcome is task success for the full-system arm versus the unchanged-operator arm across generations 1–3. The registered trend model is a task-seed-stratified conditional logistic regression with arm-by-generation interaction. Report its full-versus-unchanged log-odds slope, standard error, one-sided 99% lower bound, one-sided p-value and Holm-adjusted p-value across the one claimed family. A singular or separated fit is `NOT_ESTIMABLE`, not a pass. Report per-generation Wilson 95% intervals and paired exact two-sided McNemar tests. Report work and latency separately with paired 10,000-resample bootstrap 95% intervals. No capability or efficacy claim is made if the registered trend criterion fails or is not estimable.

## Frozen approvals and generation lineage

The user explicitly approved each named candidate under `pmb-v1-frozen-criteria`: `commutator_square_v1`, `commutator_cube_v2`, and `commutator_fourth_v3`. The adapter materializes three separate human `OperatorPromotionApproval` graph events. No later candidate is approved by this protocol. Each full-system generation must be active with a valid autonomy claim before its rows are emitted; otherwise the run fails closed.

The unchanged and adaptive arms retain the same held commutator at all three checkpoints. Adaptive curriculum enables the graph curriculum and receives the same observed training residual as the full-system arm, with no operator promotion. Full system enables curriculum, graph-authored operator proposal and recursive improvement. The graph authors the three successor expressions, while the host supplies only the declared development measurements, scoped approval events, bounded native ticks and mechanical task outcome collection. All process application and composition outcomes use the native evaluator. Evaluation labels and answer fields do not enter the task graph.

The held-out goal at generation *g* is the state reached by applying `commutator^(g+1)` once to a generated initial permutation. The full-system arm applies the active generation operator; both controls apply the unchanged commutator once. All arms receive the same seed-matched world, target, primitive-access hash, single-call ceiling, one shared 400,000-unit ThinkingBudget ceiling, 100,000-unit per-generation ceiling, and common runtime limits. The full-system arm uses more task work as operator depth grows; exact work is recorded and a gain at greater work is not an efficiency gain.

## Fixed allocation

Every seed is given by `25,000,000 + family_code*10,000 + control_block*1,000 + draw`, with `family_code = 10 + generation_index`. The three family codes are 11, 12 and 13. Ranges are half-open; all listed panels are mutually disjoint and use the phase-15 namespace, separate from earlier P13/P14 allocations.

| Use | Family code(s) | Control block | Draws / concrete range |
|---|---:|---:|---|
| Training residual | 11 | 0 | one seed: 25,110,000 |
| Development task panel | 11 | 1 | draws 0–7: 25,111,000–25,111,007 |
| Development task panel | 12 | 1 | draws 0–7: 25,121,000–25,121,007 |
| Development task panel | 13 | 1 | draws 0–7: 25,131,000–25,131,007 |
| Candidate selection, generation 1 | 11 | 1 | draws 800–801: 25,111,800–25,111,801 |
| Candidate selection, generation 2 | 12 | 1 | draws 800–801: 25,121,800–25,121,801 |
| Candidate selection, generation 3 | 13 | 1 | draws 800–801: 25,131,800–25,131,801 |
| Held-out tasks, generation 1 | 11 | 2 | draws 0–199: 25,112,000–25,112,199 |
| Held-out tasks, generation 2 | 12 | 2 | draws 0–199: 25,122,000–25,122,199 |
| Held-out tasks, generation 3 | 13 | 2 | draws 0–199: 25,132,000–25,132,199 |
| Analyzer integrity controls | 11 | 3 | draws 0–99: 25,113,000–25,113,099 |

The held-out panel contains exactly 200 matched worlds per generation and arm (1,800 scored rows). Each seed deterministically selects an S4 permutation and a transposition; arms share its initial state and goal. Candidate selection uses two separate native development cases per generation and cannot read held-out seeds. The 100 integrity controls perturb one audit field at a time across world hash, primitive-access hash, input audit, invariant receipt and external-action receipt; all must be rejected by the analyzer. Their IDs are control labels and do not create efficacy rows.

## Measures, integrity and resource limits

Primary score is binary task success. Report generation-specific and aggregate arm rates, paired differences, confidence intervals, McNemar results, conditional-logistic trend and exact work/latency intervals. Each task reports native work units, elapsed task time, graph node/serialized-byte counts, remaining budget, world and access hashes, invariant status, actions, and input audit. Full-system task work is `generation + 2`; each control task is 2, excluding the one detached scorer evaluation of the goal effect and two common world-generation operations, which are reported separately. Candidate development work is 8, 12 and 16 for generations 1–3 and is debited from its generation reservation. The shared curriculum and generation reservations draw on the one arm-level ThinkingBudget.

Fail the affected arm/run on any unmatched world or access hash, missing or duplicate arm row, answer/strategy/held-out leakage, invariant failure, action emission, incorrect work receipt, inactive/unfunded generation, budget denial/overspend, stale provenance, or limit exceedance. Do not impute a score after a timeout or failed adapter. The analyzer verifies exact seed sets, family codes, split control block, row counts, per-row work, graph limits, pairing, access, input audits, invariants, action boundary, artifact hashes and all 100 tampering controls.

Fixed ceilings are 400 outer ticks, 100,000 native rule steps per tick, 100,000 graph nodes, 64 MiB serialized graph per arm, 400,000 total ThinkingBudget units per arm, and 100,000 reserved work units per generation. No refill is allowed. The engine profile, operator criteria, task generator, seed formula, score, parser, analyzer and approval events remain fixed. Raw scorecards and their SHA-256 hashes are stored outside git; the preregistration and analyzer output are committed.

## Frozen artifacts

These fingerprints are emitted by the development adapter at the implementation commit. The held-out analyzer checks them against the scorecard before reporting any result.

| Artifact fingerprint | SHA-256 |
|---|---|
| `source_bundle_sha256` | `bb17ff778e2d256a5b400c6e20d6562fe9e7b0d887ec9ea4291fc5a4c23323c3` |
| `runner_sha256` | `48a30c39ab1dce30fbae3dee3e9a0cd43a2589a8894c9f771ac0035a9b2e27ea` |
| `analyzer_sha256` | `7597cf0c74f29cdf5bf476be4908890b26c1dd71c19f895e2de23efcc36afa49` |
| `profile_sha256` | `61a06e01e4a8d4746e3c15feb66962fb6a98c71e225ce186201c178643408aaa` |
| `world_adapter_sha256` | `3eabdfd1f28edca08f64800eab0a37b8d2911ece810160b9d4d62c05f5557985` |
| `engine_binary_sha256` | `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5` |
| `dependency_closure_sha256` | `02192b13a5a16279ec80859c0675710c84b62b38b5c8c890572ed3c30d553fcd` |
| `engine_source_sha256` | `2bdf0869389e7a6e9133a997224b6d32dfd18ddb7310ae4bfe4a2d14e6280bdf` |

Python runtime is 3.13.5. Dependency closure includes the DSL Cargo manifest, Python package manifest, `uv.lock`, and native build metadata. Any fingerprint mismatch invalidates the held-out draw; correcting code requires a new protocol version and untouched split.

## Development validation and commands

The frozen eight-task development panel completed 24 paired worlds with zero integrity failures. Full system solved 24/24, unchanged operator 7/24, adaptive curriculum 7/24. Per-generation full/unchanged counts were 8/8 vs 0/8, 8/8 vs 3/8, and 8/8 vs 4/8. The conditional-logistic trend was not estimable because conditional information was singular. The work bootstrap was +2.0 units/task (95% interval 1.67–2.33); latency interval crossed zero. These results are development-only and were not used to alter the frozen thresholds or seeds. The two self-check commands and 70-test focused P15 bundle passed.

Run before the held-out draw:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p15_v1 --self-check --output /tmp/p15-selfcheck.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.analyze_linear_p15_v1 /tmp/p15-selfcheck.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_portfolio.py tests/test_process_curriculum.py tests/test_recursive_process_improvement.py tests/test_invention_operator_authorship.py tests/test_cognition_profile_integration.py tests/test_linear_p15_adapter.py -q -p no:cacheprovider
```

Run the single held-out draw only after this file is committed, then analyze the saved scorecard:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p15_v1 --split heldout --output /tmp/p15-heldout.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.analyze_linear_p15_v1 /tmp/p15-heldout.json
```
