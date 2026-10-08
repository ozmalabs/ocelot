# Live describe-scene access trace v2.3 preregistration (2026-09-27)

## Question

With the current locked conversation route completing its lifecycle, how do selected native accesses divide among request lifecycle cores and the shared Scene/Percept input? Does the public `converse()` surface agree with the same turn's graph-visible outbound Message?

## Design

Use the v2.2 scene-aware projection and the three paired fresh-process traced/untraced replays. Preserve the same fixture, serialized A/B schedule, request intervals, whole-graph semantic projection, and source lock. Add readback capture at `_finish_turn_reply`: while still in the serialized turn, record the public surface/source, the inbound Message's reply annotation, and every graph Message responding to that exact inbound. Temporarily disable native access tracing during this read-only evidence extraction so it does not contaminate operation counts. Keep output agreement as a separately reported capability gate; do not silently replace the public surface with the graph candidate.

## Gates and report

Require all v2.2 source, schedule, lifecycle, trace-completeness, exact-pair semantic parity, and shared Scene/Percept shape gates. Require `turn_output_evidence` for both requests in every worker and exact agreement of that diagnostic projection across each traced/untraced pair. Report whether the public reply surface matches any unsuppressed outbound Message tied to the same inbound turn; this is a capability result distinct from capture integrity. If lifecycle gates fail, the run is censored. If output surfaces disagree but integrity gates pass, preserve the locality trace while stating that the natural-language output is not graph-message aligned.

Access rows remain selected and incomplete; Scene plus its three direct Percepts form a shared input projection, not a complete closure of rule-produced descendants. No natural-task prevalence, asymptotic, or broad language capability claim follows from this fixture.

## Reproduction

Generate `evaluation/substrate_capability/live_describe_scene_access_trace_v2_3_lock_20260927.json` from `scripts/substrate_live_describe_scene_access_trace_v2_3.py --lock`, then store its `locked_inputs` there. Run the driver with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Worker start/completion is printed to stderr; results are written only after all six workers finish.
