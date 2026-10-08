# Foreign-snapshot variation diagnostic v1

Date: 2026-10-05  
Status: preregistered source-locked diagnostic of the global held-topic baseline.

## Question

Does worker-level variation in the held-topic final graph arise because the audience foreign-snapshot input varies, because foreign node enumeration/sample order varies, or because `SystemModel` construction varies after receiving the same input?

## Design

Run three fresh global-arm workers through the same seed, teaching facts, and seven held-topic prompts as the settlement parity study. Set `PYTHONHASHSEED=0` in each worker process. Do not modify production source or disable rules. Wrap `domains.system_model.model_system` in the evaluation runner and record each `foreign_snapshot` call's input graph, node/edge counts and digest, reconstructed foreign node enumeration (IDs and ID-independent node labels), return target metadata, sampled fixed/volatile foreign IDs, and generated model attributes. Associate calls with the conversation turn. Retain normal replies, graph fingerprints, and work reports.

The reconstructed enumeration is a diagnostic replay of the graph input under the pinned hash seed. It records current-source behavior and is not claimed to be the original hidden local enumeration unless it agrees with the returned sample IDs. Compare input graphs first, then enumeration/sample order, then model output. Do not infer causality from final graph counts alone.

## Gates and limits

- Three fresh worker PIDs, seven turns each, source hashes stable before/after, hash seed recorded as zero.
- Report per-call input graph equality, enumeration equality, selected-sample equality, and generated-field equality separately.
- The run diagnoses the global baseline only. If the foreign input or model output still varies, do not attribute area-scheduler effects; preregister the next causal intervention before changing execution behavior.
- No production changes, rule suppression, or response-latency claims are part of this diagnostic.
