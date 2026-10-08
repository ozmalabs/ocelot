# Held-topic trace semantic-parity v1.1 results

Date: 2026-09-28  
Protocol: [preregistration](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_PREREG_20260928.md)  
Amendment: [snapshot and analyzer corrections](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_AMENDMENT_20260928.md); [post-capture provenance audit](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_POSTCAPTURE_AUDIT_20260928.md)

## Outcome

The actual-workspace paired replay passes all **24 independent parity and trace checks** across three distinct processes. Baseline and combined-trace arms have exact semantic signatures within each process; signatures also repeat across all workers. Counterbalanced arm order is baseline/trace, trace/baseline, baseline/trace. Source, native, and local runtime-data locks remain stable.

The fixed capability oracle passes **9/10 checks per arm and worker**: the three teaching operations and six of seven query cases succeed (27/30 outcomes across three trace-arm workers). The only repeatable miss is “Can you tell me about copper?”; comprehension routes it to `honest_capability`, creates an unresolved copper Goal, and asks “What information should I use to answer that?” The held-answer query forms, table query, unknown-topic unresolved/no-leak case, and injected local-hit case all meet their specified contracts. This is a narrow authored suite, not a general language capability estimate.

## Structural and operation evidence

The whole graph after each worker's schedule has 25,363 nodes and 12,259 edges. The seven manually declared task frames have 10–13 nodes, 10–13 internal edges, and deterministic min-fill width upper bounds of 1–2. Their complete direct cuts have 40–51 incidences and 27–34 unique external nodes. These are small operational subgraphs with large cuts relative to their interiors; their membership is harness-declared, not discovered by the substrate.

Conversation access traces contain 76–99 rows and 117,331–315,091 weighted events per operation. Teaching calls generate no native access/work rows in the measurement boundary. Conversation calls have zero dropped rows, conserved weights, resolved RuleUIDs, and no observed static-resource mismatch. Every exposed all-scope scheduler/deferred work row reconciles with per-scope and process-global counters. The independent analyzer also reconstructs all typed cuts and task attribute schemas. These results support use of the trace arm for this measured task/source, but do not establish complete host-language access coverage or zero trace overhead.

## Provenance correction

The earlier v1 capture and the first paired replay ran from an isolated snapshot without the repository's non-code `data/` corpus. Their code/seed locks alone did not describe the live runtime. In this actual-workspace run, the complete `data/` tree was content-hashed: 70,894 files, 3,886,824,402 bytes, SHA-256 `0c6d1817e31c7c0e04b99c6fbcf6e4ddc5de6c73d4509972fa8c75796735dbff`. The hash matches before and after the replay. The capture lock also records the Python/seed source closure, native extension/build manifest, runner, protocol, amendments, and analyzers.

The preregistered analyzer had a nested-lock field-path bug and stopped before producing analysis. Its hash is preserved in the run lock. The independent corrected analyzer [v1.1.1](../../../scripts/analyze_substrate_held_topic_trace_semantic_parity_v1_1_1.py) changes only that field lookup and writes the analysis artifact linked below; it finds all 24 checks pass. This is a disclosed post-capture analyzer correction, not a change to raw worker data or capability criteria.

Post-capture audit found that the current amendment text no longer matches the amendment SHA-256 in the capture lock, and the retained snapshot copy does not recover the locked bytes. The lock preserves the expected digest. Thus the paired worker evidence and raw remain available, while exact reconstruction of the full preregistration bundle is incomplete. The recorded command environment and working directory are documented in the [post-capture audit](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_POSTCAPTURE_AUDIT_20260928.md); they were not serialized into lock fields.

## Artifacts

- [Paired raw capture](../../../evaluation/reports/held_topic_trace_semantic_parity_v1_1_20260928.json)
- [Independent corrected analysis](../../../evaluation/reports/held_topic_trace_semantic_parity_v1_1_1_analysis_20260928.json)
- [Source/runtime-data lock](../../../evaluation/substrate_capability/held_topic_trace_semantic_parity_v1_1_lock_20260928.json)
- [Paired capture runner](../../../scripts/substrate_held_topic_trace_semantic_parity_v1_1.py)
- [Originally locked analyzer](../../../scripts/analyze_substrate_held_topic_trace_semantic_parity_v1_1.py)
- [Corrected analyzer](../../../scripts/analyze_substrate_held_topic_trace_semantic_parity_v1_1_1.py)
- [Post-capture provenance audit](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_POSTCAPTURE_AUDIT_20260928.md)

## Next gates

1. Add preregistered prompt variants for “Can you tell me about copper?” that distinguish a request for held information from a literal capability question; retain an unknown-topic and injected local-hit control.
2. Trace the graph-selected production faculty and receipt state for the unresolved request form, then adjust the oracle only if blinded human adjudication shows the current clarification is appropriate.
3. Extend external-input locking to any additional runtime data paths used by later task families. Do not assume the Python/seed fingerprint alone defines a reproducible runtime.
4. Continue structural evaluation with independently proposed frames, boundary perturbations, and monolithic/partitioned closure parity. This capture does not establish cheap-cut prevalence or decomposition correctness.
