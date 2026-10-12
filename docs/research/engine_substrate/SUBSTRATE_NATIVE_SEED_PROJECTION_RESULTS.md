# Native seed manifest projection probe results

Date: 2026-09-25  
Status: 12 fresh workers; exact state parity; source and runtime intervention gates pass

## Results

The control passes the original full manifest to the native loader. The projection arm builds an allowlisted dict containing only fields read by the locked `PySubstrate::load_seed_manifest` implementation; Python boot continues to use the original manifest unchanged. Each condition ran three fresh processes at N=512 and N=737.

| IDs | Arm | Native calls | JSON bytes passed to native | Median boot wall | Median process CPU | Peak RSS observed |
|---:|---|---:|---:|---:|---:|---:|
| 512 | control | 518 | 151,796,871 | 14.239 s | 15.257 s | 2,160–2,161 MiB |
| 512 | projection | 518 | 44,995,405 | 11.041 s | 11.848 s | 2,161 MiB |
| 737 | control | 748 | 157,437,537 | 14.834 s | 15.868 s | 2,295–2,299 MiB |
| 737 | projection | 748 | 49,788,760 | 12.012 s | 13.001 s | 2,298–2,299 MiB |

For N=512, projection reduces converted payload bytes by 70.4%, median wall by 22.5%, and median CPU by 22.3%. For N=737, the reductions are 68.4%, 19.0%, and 18.1%. Every repetition within each condition and both conditions at a given size have identical full boot reports, graph, grammar, rule store, rule access/order, and self-model report state. The 518/748 interception counts match across paired arms.

## Interpretation and limits

This is causal evidence that whole-object conversion at this PyO3 boundary contributes materially to measured startup for this corpus and implementation. It does not explain the entire earlier 256-to-512 discontinuity: the 512 control here is substantially faster than the earlier scale-sweep point, demonstrating host/run or source-path variation. The projection is a promising loader optimization candidate because parity held while the original Python manifest remained available to downstream code, but this is not yet production adoption evidence. Direct callers outside `load_all_seeds`, serialization error behavior, mutation/aliasing assumptions, and broader task-level consumer parity still need audit.

RSS is inflated by the harness retaining all manifest references until after the timed boot so byte sizes can be computed without putting JSON diagnostic serialization in the measured interval. Thus the ~2.1–2.25 GiB figures are not representative uninstrumented peaks. The run is one host, one frozen authored corpus, two sizes, and three repetitions per arm. It does not establish general scaling, cheap-cut prevalence, or learning tractability.

Two initial harness attempts are excluded: attempt 1 failed in parent PID bookkeeping after an unrecorded completed worker; attempt 2 patched the facade instead of the PyO3 class and recorded zero intercepted calls. The parity-only attempt's diagnostic report and lock are retained; the first worker's result was not persisted. See the preregistration for exact deviations.

## Artifacts

- Protocol: [`preregistration`](SUBSTRATE_NATIVE_SEED_PROJECTION_PREREG_20260925.md)
- Source/build lock: [`lock`](../../../evaluation/substrate_capability/native_seed_projection_lock_20260925.json)
- Runner and independent analyzer: [`runner`](../../../scripts/substrate_native_seed_projection_probe_v1.py), [`analyzer`](../../../scripts/analyze_substrate_native_seed_projection_probe_v1.py)
- Raw report and validated analysis: [`raw`](../../../evaluation/reports/substrate_native_seed_projection_probe_v1_20260925.json), [`analysis`](../../../evaluation/reports/substrate_native_seed_projection_probe_v1_analysis_20260925.json)
- Excluded attempt 1: worker completed but its output was lost to driver bookkeeping failure; no raw row exists.
- Excluded attempt 2: [`parity-only report`](../../../evaluation/reports/substrate_native_seed_projection_probe_v1_harness_attempt2_20260925.json), [`attempt lock`](../../../evaluation/substrate_capability/native_seed_projection_lock_harness_attempt2_20260925.json)
- Related scale envelope: [`prefix scale results`](SUBSTRATE_SEED_BOOT_PREFIX_SCALE_RESULTS.md)
