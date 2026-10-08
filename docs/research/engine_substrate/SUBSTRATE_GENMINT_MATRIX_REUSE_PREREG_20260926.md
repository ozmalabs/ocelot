# GenMint matrix/layout and reuse-cost confirmation preregistration

**Lock date:** 2026-09-26, before the confirmatory capture. **Question:** across three 2-D linear matrices and three predicate layouts, does full-seed GenInfer acquire the intended matrix, and how do cumulative closure time, quanta, graph growth, and process RSS compare with induction disabled as the same learned map is applied to additional held-out shapes?

## Design

Matrices: prior `[1,1,0,2]`, `shearA [1,0,1,1]`, and `shearB [1,1,0,1]`. Training coordinates are `(0,0),(1,0),(0,1),(1,1),(2,0),(0,2)`; cross layouts `adjacent_01` (p0 indices 0,1,4), `opposite_03` (0,3,4), and `adjacent_12` (1,2,5). Use only clean targets in this matrix/layout confirmatory sweep.

Cross each matrix/layout with GenInfer enabled/disabled, reuse counts `K={0,1,2,4}`, and five fresh-process replicates: 3 × 3 × 2 × 4 × 5 = 360 workers. Each worker boots the same full seed, presents the six-row training observation, then presents the first K held-out tasks in the fixed order below. The disabled arm receives identical data and stage order. The held-out tasks each use a new four-relation `ShapeSignature` with predicate sequence p0,p1,p0,p1 and the listed base points:

| Task | Base points |
|---|---|
| H0 | (2,1), (1,2), (3,1), (1,3) |
| H1 | (0,3), (2,1), (3,4), (1,0) |
| H2 | (4,0), (1,2), (3,4), (0,1) |
| H3 | (1,4), (3,0), (5,2), (0,1) |

Each target row is produced by the assigned matrix. The held-out baseline signature is added only after training closure. K arms therefore form prefixes of the same fixed task order. The pilot's `shearB × adjacent_01` failure remains in the study.

## Measures and route scoring

Record per-stage native closure wall time, observation status and residual, selected Transform/generator, all linear generators before/after each stage, CapabilityAxis delta, graph node count, and fresh-process peak RSS. Primary transfer credit requires that the expected matrix was minted during training, the held-out Transform references that same acquired generator, and independent application of its matrix plus returned residual transforms exactly predicts all four held-out rows. A matrix minted during an application, another generator, or terminal status without the intended matrix receives no learned-reuse credit and is reported as a distinct route.

For each matched matrix/layout/replicate/K pair, compare cumulative timed closure cost (`training + K applications`), total quanta, exact learned-reuse count, graph-node growth, and peak RSS. Report paired medians/ranges and the first measured K where enabled cumulative closure time is below disabled; if none occurs, report no measured crossover through K=4. This is a bounded accounting curve, not an asymptotic fit or general hardware estimate. Timed closure excludes process startup, boot and graph construction; peak RSS includes the full fresh worker and is not operation-attributed.

Integrity gates: 360 workers/cells as locked, 5 repeats per cell, exact input reconstruction, unique worker PIDs, deterministic within-cell outcomes, source/native/lock hashes, and no unclassified selected-generator routes. The pilot replication is reported separately: the expected matrix should be acquired in all five repetitions for the six prior/shearA layout cells, in the two shearB layouts previously positive, and not acquired for shearB/adjacent_01. These are hypotheses to test, not exclusion rules; any discrepancy remains in the analysis. No requirement is imposed that held-out transfer or a runtime crossover succeed.

## Provenance and execution

The runner's `--lock` output hashes this protocol, exact runner and analyzer sources, relevant seeds/modules/Rust files, and installed native extension. Save it to `evaluation/substrate_capability/genmint_matrix_reuse_lock_20260926.json` before execution; runner refuses changed/missing locks or stale native builds. The raw record embeds each worker PID and inputs. The analyzer verifies the source hashes against the locked file bytes and independently reconstructs the transfer predictions.

Run:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_matrix_reuse_probe_v1.py --lock
# Save the --lock JSON at the path above, then:
PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_matrix_reuse_probe_v1.py
python3 scripts/analyze_genmint_matrix_reuse_probe_v1.py
```

This remains an authored integer-linear family on one host. It does not estimate natural-task prevalence, general learning accuracy, or general-purpose amortization.
