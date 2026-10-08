# Describe-scene boot and request memory profile v1 (2026-09-27)

## Question

At which phases does resident memory rise in the full-seed scene fixture: adapter construction, seed boot, scene attachment, or the two-request workload?

## Method

Run one fresh process on the same locked source/native closure as timing v2. Sample `/proc/self/status` and `smaps_rollup` after interpreter startup, adapter construction, `load_all_seeds`, scene attachment, and completion of two simultaneous describe-scene calls. Record process current RSS and high-water RSS, plus PSS, anonymous, file, shared, and private dirty memory when the OS exposes them. Do not materialize diagnostic graph snapshots, enable tracing, scale auditing, or graph readback. Preserve request correctness checks and source lock at start/end.

The OS RSS samples identify when the process footprint grows, not which Python/native data structures own the memory. One worker is a phase-attribution diagnostic, not a distribution estimate.

## Gates

Require stable source/native locks, two joined requests, expected replies, two resolved request Goals, and finite nondecreasing peak RSS readings. Record failures without attributing their memory profile.

## Artifacts

[Runner](../../../scripts/substrate_describe_scene_boot_memory_profile_v1.py), [lock](../../../evaluation/substrate_capability/describe_scene_boot_memory_profile_v1_lock_20260927.json), [report](../../../evaluation/reports/describe_scene_boot_memory_profile_v1_20260927.json).
