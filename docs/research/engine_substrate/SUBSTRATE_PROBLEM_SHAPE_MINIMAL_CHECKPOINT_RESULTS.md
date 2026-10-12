# Minimal ProblemShape continuation checkpoint results

**Status:** exact N=8 continuation parity passes for the explicitly limited ProblemShape contract. This is not a complete `WorldAdapter` checkpoint and must not be read as a general agent restart result.

## Contract tested

Three fresh processes ran: a full-adapter uninterrupted control; a full-adapter writer that resolved eight decomposition goals and checkpointed after the first residual observation and residual-candidate event; and a compact reader that reconstructed only the ProblemShape runtime state. The compact bundle contains the Agent codebook epoch, eight already prepared Goal nodes, the first observation and its event/index/provenance edges, the ProblemShape codebook, required key-index rows, the five active ProblemShape rules, and ten Γ productions needed by those rules and graph relations. It excludes other default faculties, unrelated rules and memories, and solver-internal graph state. The reader continued classifying the prepared goals directly through ProblemShape; it did not continue general solver execution.

The full control and compact reader matched by goal ID on every final observation key/status/coverage/decode epoch, minted shape/support, final index count, transition-event count, codebook epoch, active rule names, and fixed-point status. All eight observations were recognized, one shape (`ps_has_bound=yes`) was minted with support snapshot 2, index support was 8, and all pending/decoded/residual events were consumed. Observation-to-goal and observation-to-index links were exact. All three process IDs were distinct.

Protocol: [`SUBSTRATE_PROBLEM_SHAPE_MINIMAL_CHECKPOINT_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_MINIMAL_CHECKPOINT_PREREG_20260925.md). Runner: [`substrate_problem_shape_minimal_checkpoint.py`](../../../scripts/substrate_problem_shape_minimal_checkpoint.py). Lock: `evaluation/substrate_capability/problem_shape_minimal_checkpoint_lock_20260925.json`. Raw result: [`substrate_problem_shape_minimal_checkpoint_20260925.json`](../../../evaluation/reports/substrate_problem_shape_minimal_checkpoint_20260925.json).

## Size and restore cost

| Measure | Full adapter N=8 | Minimal ProblemShape bundle |
|---|---:|---:|
| Serialized bytes | 113,876,928 | 13,779 |
| Relative size | 1× | 0.0121% (about 8,264× smaller) |
| Graph nodes / edges at write | 24,980 / 11,400 | 13 / 5 |
| Rules / grammar productions | Full default rule store | 5 / 10 |
| Write / read wall time | ~10.3 s / ~5.9 s in the separate scale sweep | 0.52 ms / 3.19 ms |
| Peak RSS | ~2.14 / 1.90 GB in full writer/reader sweep | 1.79 GB writer / 30.5 MB compact reader |

The compact writer still pays full-adapter boot and preparation cost, so its RSS does not fall. The compact reader is the meaningful memory comparison: it restores 13 graph nodes, five active rules, and the minimal Γ subset with about 30 MB peak RSS. Compact timings are one run and exclude durable filesystem flush guarantees; they measure JSON write/read and native graph/rule reconstruction in this local probe.

## Scope and next work

This confirms a viable serialized state for resuming the ProblemShape faculty over already prepared goals. It does not prove the bundle is sufficient for the solver, WorldAdapter reflexes, arbitrary future goals, other faculties, or long-running agent behavior. It does not test schema evolution, corruption/truncation handling, crash-safe atomic replacement, concurrent checkpoint writers, or hostile input. Before product use, define the owning application’s restart boundary, version the bundle schema, validate required nodes/edges/rules fail-closed, and test truncation/corruption and atomic write behavior. Broader capability and task-distribution measures remain necessary for the substrate-wide goal.
