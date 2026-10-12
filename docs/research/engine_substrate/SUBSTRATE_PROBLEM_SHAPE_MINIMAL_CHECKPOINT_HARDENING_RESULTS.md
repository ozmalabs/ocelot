# Minimal ProblemShape checkpoint hardening results

**Status:** the bounded format probe passes schema-version, fail-closed validation, corruption, and atomic replacement checks. This does not make the experimental format a production checkpoint contract.

## Result

The N=8 full-adapter control, compact writer, and compact reader ran in three distinct processes. Compact continuation matched the full control exactly on all existing gates: eight recognized observations, the minted shape and support, final index support, consumed events, codebook epoch, five restored ProblemShape rules, fixed point, and exact support/index links. The bundle was 13,420 bytes, below 5% of the 113,876,928-byte full-adapter checkpoint.

The runtime validator rejected all nine malformed inputs: unsupported version, missing rule, missing production, dangling edge, wrong index support count, missing residual event, event/status disagreement, missing index link, and truncated JSON. The writer's injected exception after temporary-file fsync but before `os.replace` preserved the prior checkpoint and cleaned the temporary file. A successful replacement was accepted by the bundle reader.

Protocol: [hardening preregistration](SUBSTRATE_PROBLEM_SHAPE_MINIMAL_CHECKPOINT_HARDENING_PREREG_20260925.md). Format: [schema v1](../../../evaluation/substrate_capability/problem_shape_checkpoint.schema.v1.json). Runner: [checkpoint probe](../../../scripts/substrate_problem_shape_minimal_checkpoint.py). Raw data: [hardening result JSON](../../../evaluation/reports/substrate_problem_shape_minimal_checkpoint_hardening_20260925.json). Frozen inputs: [lock](../../../evaluation/substrate_capability/problem_shape_minimal_checkpoint_hardening_lock_20260925.json).

## Limits and remaining work

The atomic-write probe injects failure only before replacement. It does not establish behavior under process termination at arbitrary points, power loss, filesystem or storage faults, or concurrent writers. The validator is a format-specific guard, not a hostile-input security boundary or schema-migration system. The continuation still covers only already prepared goals for the ProblemShape faculty; it does not restore solver execution, arbitrary future goals, Python adapter state, or a general agent. The compact writer still pays the full-adapter startup and preparation cost. A real consumer restart boundary, compatibility policy, concurrent-writer policy, and broader continuation workloads remain to be defined.
