# Shape-decoding native rule-patch comparison v4 — results

**Result:** 8/8 gates pass across 24 fresh processes. The control exports the complete branch rule store into Python, scans for one active named rule, and then removes/adds. The treatment patches the active named rule in Rust on that detached branch. Both routes preserve the exact positive task outcome and each other’s result signatures; primary revision, graph counts, and rules remain unchanged.

| Backend | Mode | Python export wave ms | Native name-patch wave ms | CPU/wall (Python → native) | Patch phase ms/branch (Python → native) |
|---|---|---:|---:|---:|---:|
| Scoped full-copy | Sequential | 1,985 | 1,739 | 0.975× → 0.974× | 21.4 → 1.3 |
| Scoped full-copy | Concurrent | 1,577 | 1,358 | 2.01× → 2.10× | 48.8 → 6.5 |
| Shared graph pages | Sequential | 757 | 645 | 0.991× → 0.988× | 21.3 → 1.3 |
| Shared graph pages | Concurrent | 1,118 | 901 | 1.03× → 1.03× | 198.5 → 30.4 |

Native name patch reduces the candidate-patch phase about 6.5–7.5× in concurrent cells. Total wave time improves about 14% for full-copy and 19% for shared pages. The shared-page backend still has CPU/wall near 1.03×, so reducing Python serialization and rule lookup improves latency but does not itself produce CPU parallelism. Shared-page phase medians still place most concurrent wall in branch setup and model-after prediction.

This confirms the source-based diagnosis that full rule-store export/JSON decode/name scanning was avoidable work. After the follow-up six-case semantic panel passed across both backends, the native route is now the default for `imagine_and_check_convergence`; `_native_rule_patch=False` retains the Python export path as a control. The implementation is generic, while evidence remains bounded to the exercised rule shapes and one 100k-node fixture. The result establishes a task-specific efficiency improvement and exact parity, not general capability or a scaling law. Next optimize or overlap prediction/readout on shared pages, and evaluate the patch path over multiple rule names, absent targets, removals, and larger graph sizes.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_RULE_PATCH_V4_PREREG_20261001.md)
- [Implementation amendment](THOUGHTEXPERIMENT_SHAPE_DECODING_RULE_PATCH_V4_AMENDMENT_20261001.md)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_rule_patch_v4_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_rule_patch_v4.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_rule_patch_v4_raw_20261001.json)
- [V3 GIL-release result](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V3_RESULTS_20261001.md)
