# Describe-scene selective seed profile v1 preregistration (2026-09-27)

## Question

Can the live describe-scene request lifecycle run from the dependency-closed `conversation` seed selection, and what current/high-water RSS does that profile require compared with the full-seed profile?

## Design

In one fresh process on a locked source/native closure, construct `WorldAdapter(seeds=())`, then call `load_all_seeds(..., seed_ids=['conversation'])`. Record selection closure size, loaded/skipped/failed counts, current RSS and process high-water RSS before boot, after selection boot, after scene attachment, and after two simultaneous identical describe-scene calls. Check both replies, request-bound Goals, and request-specific lifecycle event sequence. Do not enable access tracing, scale auditing, or graph readback.

This is a minimal-profile capability probe, not a general claim that conversation is the only required seed family. If required behavior fails, retain the result as a capability loss under the selected profile; do not silently expand the profile after observing the outcome.

## Gates

Source lock must hold through completion; both callers must join; each inbound must have one resolved Goal and request-bound selection/execution/action-result events. The expected public reply is reported as a behavioral gate. A profile that fails the output gate remains informative for memory but is not a successful reduced-capability profile.

## Artifacts

[Runner](../../../scripts/substrate_describe_scene_selective_seed_profile_v1.py), [lock](../../../evaluation/substrate_capability/describe_scene_selective_seed_profile_v1_lock_20260927.json), [report](../../../evaluation/reports/describe_scene_selective_seed_profile_v1_20260927.json).
