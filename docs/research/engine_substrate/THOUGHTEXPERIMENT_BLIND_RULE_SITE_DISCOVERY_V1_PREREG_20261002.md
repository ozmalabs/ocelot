# Thoughtexperiment trace-guided rule-site discovery v1 preregistration

## Question

Can the current per-invocation write observer reduce a repair-site search from the full active rule store to rules that actually wrote during a failing task, without passing the target rule name or an edit cue to the discovery function?

## Protocol

Use the controlled recurrence-ledger duplicate-offer fault already used in the edge-identity proposal panel. Add one due candidate, run the opt-in native `run_rules_delta_report` with a one-progress-step budget, and pass only its event records plus the active rule definitions to the discovery function. The discovery function selects distinct progressed rule IDs with graph write targets, invokes `domains.edit_ops.find_edge_identity_sites` on those definitions, and constructs every edge-scoped identity-guard candidate. It receives no target rule name, cue, expected repair label, or outcome label. The harness keeps the target oracle outside that function for scoring the candidate-discovery result.

Capture three fresh workers. The primary descriptive gates are: no dropped trace events; at least one progressed writer; exact candidate-site reproducibility from the captured event/rule records; candidate descriptors omit source rule names; and source/native hashes remain stable. Report the candidate-generating writer/site count and the full-rule-store scan size. This v1 is a candidate-generation probe, not a claim that the observer or substrate identifies causal necessity. Rule names emitted by the observer remain visible to discovery and may themselves be semantically informative; v1 does not satisfy the stronger lexical-name-blind gate. It also uses one authored task family and does not rank or adopt proposals.

## Interpretation boundary

A successful reduction shows that runtime write evidence can narrow a structural edit search on this fixture. It does not establish target-blind causal diagnosis, because activity is not causal necessity and semantic rule names are retained. The next gate must rename or opaque-map rule identities before discovery, add competing correlated writers and a no-op writer, then require substrate-side proposal ranking/abstention and disjoint held-out utility without target or cue leakage.

## Artifacts

- Runner: [thoughtexperiment_blind_rule_site_discovery_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_blind_rule_site_discovery_v1.py)
- Lock: [thoughtexperiment_blind_rule_site_discovery_v1_lock_20261002.json](../../../evaluation/substrate_capability/thoughtexperiment_blind_rule_site_discovery_v1_lock_20261002.json)
- Capture: [thoughtexperiment_blind_rule_site_discovery_v1_20261002.json](../../../evaluation/reports/thoughtexperiment_blind_rule_site_discovery_v1_20261002.json)
- Analysis: [thoughtexperiment_blind_rule_site_discovery_v1_analysis_20261002.json](../../../evaluation/reports/thoughtexperiment_blind_rule_site_discovery_v1_analysis_20261002.json)
