# Shape-decoding Python/native attribution v3 — native rule-store summary results

**Result:** 10/10 gates pass across 12 fresh processes. The new native branch summary replaces full `export_rules()` serialization and Python scanning when a detached branch already owns its native rule store. All positive correction outcomes, cross-backend/mode signatures, primary isolation, source/binary lock, and profile accounting match.

| Backend | Mode | v2 wave ms | v3 wave ms | CPU/wall v2 → v3 | Model-after phase ms v2 → v3 | Bounded-look phase ms v2 → v3 |
|---|---|---:|---:|---:|---:|---:|
| Scoped full-copy | Sequential | 2,126 | 1,613 | 0.97× → 0.97× | 209 → 160 | 181 → 132 |
| Scoped full-copy | Concurrent | 1,421 | 854 | 2.08× → 2.70× | 613 → 248 | 425 → 219 |
| Shared graph pages | Sequential | 961 | 430 | 0.98× → 0.97× | 101 → 52 | 68 → 24 |
| Shared graph pages | Concurrent | 880 | 388 | 1.06× → 1.09× | 567 → 318 | 217 → 64 |

The largest shared-page improvement is in sequential rehearsal: wave time drops about 55%; concurrent wave time drops about 56%. Concurrent shared-page execution now completes the eight-branch wave slightly faster than the eight sequential rehearsals (388 ms vs 430 ms), with modest 1.09× worker-CPU overlap. Full-copy also improves and reaches 2.70× CPU/wall in the concurrent cell. Sequential cProfile no longer shows `export_rules` among the leading sites, and Python JSON `raw_decode` self CPU falls from about 742 ms summed across profiled shared-page branches to 295 ms. Prediction and bounded forward look also shrink substantially.

This is direct evidence that redundant branch rule-store serialization was a major cost in the measured pipeline. Remaining JSON decode and Python prediction work persist, and cProfile does not attribute concurrent GIL wait. This remains one fixture, candidate, host, and graph size; the next gate should test whether the reduction and concurrent gain persist across graph sizes and candidate families, while separately identifying remaining JSON decode callers.

See the [preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V3_PREREG_20261001.md), [amendment](THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V3_AMENDMENT_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_python_native_profile_v3.py), [lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_python_native_profile_v3_lock_20261001.json), and [raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_python_native_profile_v3_raw_20261001.json).
