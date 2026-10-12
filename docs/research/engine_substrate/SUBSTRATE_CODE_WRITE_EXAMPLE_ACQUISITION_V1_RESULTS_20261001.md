# Code-write example acquisition v1 — results

**Result:** all preregistered gates pass in ten source-locked fresh processes.

Five workers per task first fail to write from the starter codebook, then read an externally supplied function, teach a new live `ShapeSignature`, and select that exact signature for the original request. The new nodes carry `taught_from=example` and the exact `taught_for` request. After growth, the normal write path emits executable Python from the learned Term construction.

| Task | Fresh workers | Held-out inputs per worker | Exact native Term and Python outputs |
|---|---:|---:|---:|
| Parity | 5 | 41 | 205/205 |
| Clamp | 5 | 20 | 100/100 |

Across all 305 held-out cases, native evaluation of the selected Term and execution of the generated Python function both match the independent analytic oracle exactly and match each other. The parity panel spans every integer from -20 through 20. The clamp panel covers 20 fixed triples with varying ordered bounds, endpoints, interior points, and values outside the interval. No expected held-out output is supplied to the substrate-side runner.

## Cost and provenance

Median full-seed boot is 12.19 s in both families; median teach time is 27.7 ms for parity and 28.2 ms for clamp. Post-teaching composition and code rendering each take about 3.6–4.2 ms median. Peak process RSS is about 1.68 GiB. That memory figure includes the full seed corpus and is a material cost of this full-boot evaluation; it is not the marginal cost of example teaching. The interleaved held-out native/Python timing fields overlap and are retained as diagnostics, not interpreted as separate phase costs.

All ten workers have distinct PIDs. Their active sources match the pre-run lock before and after each worker, and the runner's complete source, native, and loaded-seed-manifest fingerprints match before and after the panel. The first lock was generated before any experimental worker and is retained with a pre-capture amendment documenting that its recursive seed-data traversal was replaced by exact boot-manifest hashing plus global pre/post tree fingerprints.

## Claim boundary

This shows supervised codebook growth from externally supplied runnable Python examples, followed by exact held-out transfer on two fixed integer tasks. The example source contains the target computation; the substrate's current route parses it and reverses the resulting Term into a reusable write construction. It does not originate the program, infer an absent operator, choose its own examples, or establish general English-to-code synthesis. The internal teach-time execution check compares code against the same Term, so only the separately computed held-out oracle is counted as independent correctness evidence.

## Artifacts

- [Preregistration](SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PREREG_20261001.md)
- [Pre-capture amendment](SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PRECAPTURE_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_code_write_example_acquisition_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_code_write_example_acquisition_v1.py)
- [Execution lock](../../../evaluation/substrate_capability/substrate_code_write_example_acquisition_v1_lock_20261001.json)
- [Preserved unused pre-run lock](../../../evaluation/substrate_capability/substrate_code_write_example_acquisition_v1_lock_20261001_pre_run.json)
- [Raw capture](../../../evaluation/reports/substrate_code_write_example_acquisition_v1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_code_write_example_acquisition_v1_analysis_20261001.json)
