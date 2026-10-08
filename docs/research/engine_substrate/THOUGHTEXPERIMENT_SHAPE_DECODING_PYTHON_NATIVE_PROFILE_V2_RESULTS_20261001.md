# Shape-decoding Python/native CPU attribution v2 — results

**Result:** 10/10 gates pass across 12 fresh processes using the now-default native rule patch. Isolated profiles again show negligible CPU overlap (0.97–0.98× CPU/wall) in sequential execution, while concurrent cells remain unprofiled.

For sequential shared-page rehearsal, median self CPU is about 49% Python and 51% native calls. Native `export_rules` and Python JSON `raw_decode` remain among the largest sites despite the new candidate patch, demonstrating that a second rule-store export remains elsewhere in nested imagination setup. Python `predict_collapse` and `_bounded_forward_look` are also prominent. The branch phases measure about 101 ms model-after prediction and 68 ms bounded forward look per rehearsal. For concurrent shared pages, wave wall is about 880 ms, CPU/wall 1.06×, candidate patch 18.9 ms, and model-after prediction 567 ms.

For full-copy sequential operation, about 28% self CPU is Python and 72% native calls; full-copy fork remains the dominant native site. Its concurrent wave is about 1.42 seconds with 2.08× CPU/wall after the GIL-release intervention. This profile is one host and one bounded task, and does not identify concurrent GIL wait or native lock contention.

The remaining full-store export in `_install_detached_rewrite_delta` is avoidable on native fork backends: the fork already owns the copied rule store, and current code serializes it to Python to count active rules and find requested removals. The next intervention replaces this with a native branch-local rule count/removal operation, then repeats the same oracle and profile protocol.

See the [preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V2_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_python_native_profile_v2.py), [lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_python_native_profile_v2_lock_20261001.json), and [raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_python_native_profile_v2_raw_20261001.json).
