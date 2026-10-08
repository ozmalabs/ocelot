# Thoughtexperiment anonymized cause/site discovery v1 preregistration

## Question

Can the substrate's proposal selector recover the useful edit site from anonymized rule-write evidence when a correlated, task-irrelevant rule also fires, and ignore a no-op writer?

## Design

Use the recurrence exact-once offer task. The harness injects a faulty offer rule, a correlated shadow writer that has the same match bindings and emits a separate shadow edge, and a no-effect control rule. All rule identities are mapped to opaque IDs before discovery; each rule definition's `name` field and each trace event's `rule_name`/`origin_rules` are replaced with the corresponding opaque ID. The discovery function receives only those anonymized events and rule definitions. It generates all edge-identity proposals from progressed writers with write targets; the evaluator retains the private ID mapping for applying proposals and scoring, but does not expose it to the discovery function or selector.

For each of four fresh workers, generate the candidate set, score every candidate on two training episodes, and let the graph-Term selector choose using opaque candidate IDs and typed outcome records. Capture the selection before scoring every candidate on two disjoint held-out episodes. Include source-fault, tie, and all-wrong controls. Compare proposal count and source classes, selection accuracy, false selection of the shadow writer, abstention, and end-to-end generation/scoring/selection costs. Exact task success requires one offer for each due candidate and a fixed point.

## Gates and limits

The identity-blind gate requires no original rule names or cue in discovery/selection inputs. The causal-confound gate requires the shadow writer to appear in trace evidence while remaining task-irrelevant; the no-op gate requires the empty-effect rule to be visible as an attempt but excluded from productive candidate generation. Candidate ranking passes only if the selected target-rule edit is the unique training winner and passes all held-outs; controls must abstain. This remains a host-orchestrated, single-family diagnostic: task construction and oracle labels are supplied, and proposal application/scoring are managed by the harness. It is not autonomous residual interpretation or general self-improvement.

## Artifacts

- Runner: [thoughtexperiment_anonymized_cause_site_discovery_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1.py)
- Lock: [thoughtexperiment_anonymized_cause_site_discovery_v1_lock_20261002.json](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1_lock_20261002.json)
- Orders: [thoughtexperiment_anonymized_cause_site_discovery_v1_orders_20261002.json](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_orders_20261002.json)
- Scores: [thoughtexperiment_anonymized_cause_site_discovery_v1_scores_20261002.json](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_scores_20261002.json)
- Analysis: [analyze_thoughtexperiment_anonymized_cause_site_discovery_v1.py](../../../evaluation/substrate_capability/analyze_thoughtexperiment_anonymized_cause_site_discovery_v1.py)
