# Live perception self-repair repeatability v1 results

Three fresh, source-locked processes ran the existing `jabberwock_live_self_repair.py` ARC episode. All three passed the independent gates. Each measured its configured self-ID axis during play, auto-minted the fault on frame 11, committed the discriminator rule edit on that same frame, observed later recovery, and kept the repair. Final self classification was `controllable` in each run. Wall times were 22.059 s, 20.438 s, and 21.139 s (median 21.139 s). Source/native hashes matched before and after each episode.

This capture exposed an environment dependency defect before the successful run: `_perceive_regions` imported OpenCV before checking for the native `segment` primitive. This environment has NumPy and the native primitive but no `cv2`; the native path does not need OpenCV. The adapter now imports OpenCV only after the native fast path returns unavailable. The repeated episode confirms the built-in native path works without OpenCV. The Python segmentation fallback was not exercised.

The result measures execution and repeatability of an existing configured repair faculty. The script externally installs a broken discriminator and configures `CapabilityAxis` with the target rule, field, and corrected effect. The substrate detects a later live performance regression and carries out the supplied repair, but it does not discover the target or correction. This is end-to-end rule-based repair under a configured repair specification, not target-blind diagnosis, novel structure induction, or self-improvement in the stronger sense.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_LIVE_SELF_REPAIR_V1_PREREG_20261005.md)
- [Existing episode](../../../scripts/jabberwock_live_self_repair.py)
- [Source-locked runner](../../../evaluation/substrate_capability/thoughtexperiment_live_self_repair_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_live_self_repair_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_live_self_repair_v1_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_live_self_repair_v1_20261005.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_live_self_repair_v1_analysis_20261005.json)
