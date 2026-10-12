# List PBE composition benchmark preregistration (2026-09-25)

**Protocol:** list-pbe-composition-v1. **State:** preregistered pilot. **Primary claim scope:** this generated integer-list workload only.

## Task set and novelty

The frozen suite has 30 one-input integer-list specifications, with four revealed and three held-out rows per task. It spans reductions, projections, maps, filters, compositions, and two controls for median and unique-count concepts outside the declared fixed inventory. Inputs are generated with per-task deterministic seeds and uniformly drawn integers in [−9, 12] on lists of length 3–7; the positive-minimum and zero-filter tasks enforce their stated witness constraints. The fixture and its generator are content-hashed in the pre-run lock.

This is a new input/task sample with both familiar primitive concepts and new compositions (for example, reverse-positive, sum-absolute, count-even). It is not a new modality, a broad domain shift, or 30 independent structural families. Report outcomes by the six frozen task strata and make no natural-task prevalence or general capability claim.

## Conditions and execution

Every task is executed on a fresh substrate with the current unchanged P4 `synthesize_from_request` path and the same four revealed examples:

1. **main:** standard boot, including the current codebook and boarded ConstructionBigram layer.
2. **frozen:** existing `C-CODEBOOK-FROZEN` ablation: retain the eight starter code-write shapes, remove other code-write construction shapes and ConstructionBigram rows.
3. **main replication:** rerun the main condition on a fresh substrate for determinism.

No cross-task memory, retries, prompt edits, budget escalation, seed changes, or task exclusions are permitted. Condition order is fixed and balanced by task ordinal in the harness. The frozen contrast isolates the added code-write constructions and bigram rows only; it does not remove the separately booted exemplar store or every learning-related subsystem.

## Endpoints and analysis

Primary endpoint: a task is a pass only when the pipeline accepts a program and its Program IR exactly agrees with all three held-out expected values under the fixed benchmark scorer. Report accepted-but-holdout-failing, gaps, unrecognized requests, stalls, and other statuses separately; they remain in the attempted-task denominator. Secondary measurements: selected construction and rung read-backs, retrieval rung/candidates, enumeration candidate count, search/gap outcome, route time, boot time, aggregate process CPU/RSS, and main replication fingerprints.

Report per-arm numerator/denominator and descriptive Wilson intervals; report the exact paired task outcome table and paired pass-rate difference. A paired bootstrap interval may be shown descriptively, stratified by the six registered task families. With 30 tasks and one generated sample, intervals do not estimate natural-task performance. Report every task-level record and do not infer causal value for components beyond the defined frozen ablation.

The fixed search budget is whatever the current P4 pipeline records from the checked-in seed/adapter; no harness override is supplied. Record candidate counts per case where available. A run is invalid for the preregistered comparison if an implementation, seed, fixture, generator, harness, or analysis change occurs after lock and before execution. Any such correction must preserve the original artifact, declare a protocol amendment, and report a new run separately.

## Freeze and artifact

Before running the benchmark, `evaluation/substrate_capability/list_pbe_composition_benchmark_lock_20260925.json` records commit, dirty-tree state, platform, task count, command, and hashes for generator, fixture, harness, protocol, P4 runner/adapter/seed, synthesizer, build manifest, extension, and lockfile. The raw run report records the same source hashes, per-task rows, all three arm results, resource use, and exact-main replay comparison.
