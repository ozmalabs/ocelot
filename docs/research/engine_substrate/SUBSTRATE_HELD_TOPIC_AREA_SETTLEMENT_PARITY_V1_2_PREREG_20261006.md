# Held-topic area-settlement semantic parity v1.2

Date: 2026-10-06  
Status: preregistered corrected per-turn structural comparison.

## Question and arms

Repeat the same three-arm global, barrier-area, and async-area full-settlement workload with three fresh workers per arm and seven turns per worker. Set `PYTHONHASHSEED=0` for every process. Preserve all rules, assignments, facts, prompts, and settlement settings from v1.1.

## Corrected semantic fingerprint

The v1.1 raw WL comparison treated serialized NodeID references as ordinary attribute values and included `SystemModel.ts` and `SystemModel.runtime_s`, which change across executions. V1.2 records the raw ID-sensitive digest separately and uses the ID-independent fingerprint in `scripts/substrate_graph_semantic_fingerprint.py` for semantic structure. It normalizes `__nid__` and numeric `*_id` attributes as typed reference relationships, preserves directed edge types, attributes, and multiplicity, and excludes only `ts` and `runtime_s` on `SystemModel` nodes. It retains one complete final graph snapshot per worker.

The analyzer must validate the fingerprint on fixtures: ID permutation and timing metadata changes preserve it; semantic node/edge attribute, direction, type, or multiplicity changes alter it. This WL fingerprint is a structural invariant, not a complete graph-isomorphism proof. Report raw and normalized results separately.

## Gates and limits

- Source-locked capture, three workers per arm, seven turns each, stable sources, fixed hash seed.
- Compare normalized fingerprints, replies, counts, settlement termination, and per-area work at every turn.
- Compare normalized final fingerprints across arms and workers; retain final snapshots for diagnosis.
- Report task utility separately. Passing full-settlement parity does not test response-priority deferral, latency, natural-task prevalence, or learning tractability.
