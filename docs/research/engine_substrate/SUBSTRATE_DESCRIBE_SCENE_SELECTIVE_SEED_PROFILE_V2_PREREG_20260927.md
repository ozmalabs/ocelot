# Describe-scene selective seed profile v2 preregistration (2026-09-27)

## Question

Can the scene-description workload be retained in a reduced seed profile that explicitly includes conversation, instruction understanding/routing, and substrate identity, and what memory footprint does that selected dependency closure require?

## Frozen selection

Request exactly these four seed roots: `conversation`, `comprehend_instruction`, `communication_intent_arbitration`, and `jabberwock_identity`. Load their declared dependency closure through `load_all_seeds(seed_ids=...)`. Do not add seeds in response to observed failures. Run the same two simultaneous scene-description requests, recording selected closure, load report, RSS phases, public replies, and request-bound Goals/lifecycle events.

The v1 conversation-only profile selected four seeds and failed with an ungrounded substrate identity reply. V2 explicitly adds the identity and instruction-routing roots. This is a confirmatory profile definition; it is not presumed sufficient. Compare capability gates and memory directly with full-seed v2 timing/profile evidence on the same source/native build.

## Gates and interpretation

Require stable source locks, complete selection, two joined requests, and one resolved request Goal with selection/execution/action-result events for each inbound. Expected public replies are a separate behavior gate. If identity or lifecycle still fails, preserve it as a reduced-profile capability loss; do not repair the selection post hoc. Report RSS as phase snapshots and process high-water separately.

## Artifacts

[Runner](../../../scripts/substrate_describe_scene_selective_seed_profile_v2.py), [lock](../../../evaluation/substrate_capability/describe_scene_selective_seed_profile_v2_lock_20260927.json), [report](../../../evaluation/reports/describe_scene_selective_seed_profile_v2_20260927.json).
