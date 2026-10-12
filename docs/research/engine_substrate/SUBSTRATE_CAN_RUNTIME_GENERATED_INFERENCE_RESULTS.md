# Inference on runtime-generated authored CAN snapshots

**Run date:** 2026-09-25  
**Runner:** [`can_runtime_generated_inference_envelope.py`](../../../scripts/can_runtime_generated_inference_envelope.py)  
**Raw report:** [`can_runtime_generated_inference_envelope_20260925.json`](../../../evaluation/reports/can_runtime_generated_inference_envelope_20260925.json)  
**Authored workload baseline:** [`SUBSTRATE_CAN_AUTHORED_WORKLOAD_RESULTS.md`](SUBSTRATE_CAN_AUTHORED_WORKLOAD_RESULTS.md)

## Question and protocol

This benchmark measures inference after the authored native CAN rule engine has generated a fixed point, so the measured networks are runtime snapshots rather than graphs directly assembled by the inference benchmark. It reuses the current graph constructor from `tests/test_can_native_reimplementation.py`: eight concepts, a complete symmetric coupling network (28 undirected pairs/56 directed edges), and matched seeded fields/couplings for 2-state and 3-state modes at coarse (1.0) and fine (0.25) weight granularity. There are 20 matched seeds per mode/granularity cell, 80 total.

For each draw, the native rule closure is run to its cap of 3,000 progressing steps, followed by a one-step zero-work terminal probe. The resulting snapshot is evaluated by a separately coded energy function and exhaustive enumeration (256 states for 2-state; 6,561 for 3-state). Direct junction-tree MAP, max-product BP (40 rounds, epsilon 1e-7), and native 20-start relaxation are compared on that same fixed model. Relaxation is scored by energy despite selecting its winner by native frustration. Its input model is re-extracted afterward to check that fields/couplings/topology did not change. Per-stage nanosecond timings and Python `tracemalloc` peak are recorded.

The measured complete graph has min-fill width upper bound 7. The junction-tree call here is direct and diagnostic: the production exact entrypoint's width-4 gate would refuse it. The small N=8 graph was deliberately kept within an exhaustive-oracle envelope. Tracemalloc excludes native Rust allocations and process RSS.

## Results

All 80 native closures converged, their terminal probes did zero work, every baseline state used its configured vocabulary, every oracle enumerated the expected number of states, and direct junction-tree MAP matched the independent oracle on all 80. All multi-start runs returned 20 candidates, passed the terminal fixed-point probe, preserved the input model, and had native energy agreeing with the independently scored objective.

| Mode | Weights | N | Baseline fixed point at MAP | BP at MAP / converged | Multi-start at MAP | Median gaps: baseline / BP / multi |
|---|---:|---:|---:|---:|---:|---:|
| 2-state | coarse 1.0 | 20 | 5/20 | 11/20 / 10/20 | 7/20 | 0.693 / 0 / 0.308 |
| 2-state | fine 0.25 | 20 | 11/20 | 8/20 / 11/20 | 7/20 | 0 / 0.347 / 0.330 |
| 3-state | coarse 1.0 | 20 | 6/20 | 11/20 / 10/20 | 6/20 | 0.303 / 0 / 0.299 |
| 3-state | fine 0.25 | 20 | 7/20 | 8/20 / 11/20 | 9/20 | 0.062 / 0.347 / 0.069 |

Across all 80, the ordinary native fixed point was globally optimal in 29 cases, BP in 38, and 20-start relaxation in 29. BP converged in 42 cases; convergence and MAP success are distinct. The per-cell results show no single approximate method winning uniformly. The relaxation path is not guaranteed to improve the ordinary settled state on every case.

Median component costs by cell (milliseconds):

| Mode / weights | Native closure | Extract | Width bound | Junction-tree MAP* | Exhaustive oracle | BP | 20-start relaxation |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2-state coarse | 0.284 | 0.247 | 0.083 | 1.357 | 1.653 | 179.593 | 8.585 |
| 2-state fine | 0.220 | 0.242 | 0.079 | 1.346 | 1.658 | 105.294 | 8.656 |
| 3-state coarse | 0.350 | 0.243 | 0.079 | 23.499 | 42.115 | 270.787 | 10.397 |
| 3-state fine | 0.327 | 0.244 | 0.078 | 23.332 | 42.059 | 160.466 | 10.684 |

`*` Direct junction-tree timings are diagnostic and outside the production width gate. Graph construction and seed loading occurred before the native closure timer and are excluded from these per-stage timings.

## Interpretation and limits

This is a runtime-derived benchmark, but its inputs remain authored synthetic draws from a test fixture, with complete coupling at one size. It provides a matched comparison between the engine's ordinary settled state and opt-in inference methods on identical post-closure models. It gives exact quality evidence through N=8, and also demonstrates substantial cost for Python BP on this complete graph. It does not establish performance on natural task graphs, learned frame partitions, sparse or hierarchical structure, production gate acceptance, or larger graph sizes.

## Next measurement

Construct sparse, modular, and frame-structured authored networks at several sizes, preserve matched seeds across graph families, and record boundary size and exact width separately. Add process-level RSS and native allocation evidence. For any claimed frame benefit, compare boundary-preserving partitioned execution with monolithic execution on identical rule-generated workloads and perturbations.
