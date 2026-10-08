# Pre-outcome task-frame capture v1

Date: 2026-10-05  
Status: preregistered prospective interface capture; seven authored held-topic turns, not a natural-task prevalence sample.

## Question

At the first native rule-closure boundary in `WorldAdapter.converse`, what part of the runtime graph can be identified from the request and its input-side records alone, and how much of the subsequent rule access trace touches that frame or its direct boundary?

This operationalizes one narrow part of the frame-locality gate. It does not claim a learned frame, a factor graph, bounded treewidth, closure factorization, or natural-task prevalence.

## Checkpoint and ownership fixed before capture

Hook `WorldAdapter._record_live_communication_state` after its original implementation returns. This method is called after ingress parse/communication records have been written and immediately before `converse` calls `comprehend()` for its first native rule closure. No answer, generated task Goal, HeldAnswer, receipt, or reply is available to the ownership procedure.

For inbound Message `m`, define the pre-outcome input frame as:

1. `m`;
2. all Mention nodes reached from `m` by `has_mention`;
3. CommunicationInterpretation nodes reached by `has_interpretation` or `interprets` incident to `m`;
4. DiscourseEvent nodes connected to `m` by `represents_message` or `for_message`.

No other node enters the frame. In particular, Concepts, Interlocutors, Channels, prior-turn records, Goals, held knowledge, evidence, receipts, and replies are boundary or outside nodes even when related to the request. The rule is typed and mechanical; do not change it after observing outcomes.

At the checkpoint, record the complete graph node/edge counts, every edge incident to a frame node, frame and external-boundary node types, frame attribute names/shapes, exact crossing incidences, and deterministic min-fill upper bound on the state-graph induced frame. This is a state-graph projection, not an inference primal graph or factor interface.

Reset the native runtime access trace at the checkpoint, then collect it through the end of the full `converse` call. Join RuleUIDs to current rule access-set metadata. Classify touched node/peer IDs as frame, direct external boundary, or outside the cut. Preserve dropped-event counts and unmapped RuleUIDs. Trace counts describe observed native rule accesses after the checkpoint; they do not cover every host-side read or establish trace completeness for the whole engine.

## Workload and controls

Use the seven prompts and three full-seed workers in the current `substrate_live_held_topic_evidence_v1_6.py` base protocol. This yields 21 prospective checkpoints. Preserve the base result checks so a structural capture cannot silently change the task outcomes. Three workers are reproducibility replicates, not 21 independent samples from a natural task population. The unknown-topic and local-source-hit turns remain authored controls.

## Gates

- Source lock covers this protocol, capture runner, base runner inputs, native extension/build manifest, and repository commit/source closure.
- Exactly one checkpoint and one post-checkpoint trace per turn; 21 total.
- Frame IDs are reproducible across workers for corresponding turns modulo node-ID renaming; compare typed/attribute signatures and counts, not raw IDs.
- No dropped access rows and no unmapped observed RuleUIDs.
- Preserve base task outcome checks and report all failed checks.
- Report per-turn distributions, not pooled “locality percentages.” Do not interpret raw edge cuts or access-trace roles as factor scopes, separators, or proof of execution isolation.

## Interpretation boundary

This captures an outcome-blind ingress frame on one authored task family. Small ingress frames can coexist with broad downstream dependencies; a broad boundary does not by itself refute task-locality if the relevant values form a compact interface. The next gate must independently sample task families and define task frames before outcomes, then capture actual read/write interfaces, dependencies, discovery cost, and monolithic/partitioned semantic parity.
