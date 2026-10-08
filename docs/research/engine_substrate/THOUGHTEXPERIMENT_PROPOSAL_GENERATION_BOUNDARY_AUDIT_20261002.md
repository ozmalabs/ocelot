# Thoughtexperiment proposal-generation boundary audit — 2026-10-02

## Finding

### 2026-10-03 Native residual cue bridge

The follow-up moves the per-trial opposite-action test from a host Python decoder into a native graph rule running in an isolated snapshot branch. Given raw actual/expected actions and four supplied opposite-action ontology facts, the rule derives the `flip_comparison` cue in all four positive cases; the existing graph composer produces a held-out-correct repair in each. Eight ambiguity/non-inversion controls produce no cue or proposal, and the absent-target control produces a cue but no edit. A raw-only baseline proposes nothing. All 13 trials return one compact residual while primary graph/rules/revision remain unchanged. The ontology, mapping rule, cue vocabulary, and task class remain designed inputs; no new rule or relation was learned. This closes a bounded host-to-substrate execution seam, not the induction gap. Next require the substrate to infer a reusable relation from examples and test it on a held-out relation family, with false-mint controls. See [protocol](RESIDUAL_TO_COMPOSER_NATIVE_CUE_V1_PREREG_20261003.md) and [results](RESIDUAL_TO_COMPOSER_NATIVE_CUE_V1_RESULTS_20261003.md).

### 2026-10-03 A8 bridge corrective replay

The v1.3 held-out replay resolves v1.2's scoring-worker crash and confirms a narrow useful composition path: with an explicit `flip/comparison/gate` cue, graph-resident A8 composition emits a `flip_comparison` proposal for `hop_descend_gradient`; it passes both held-out navigation directions in all four workers, while the common-cue control abstains in all four. The preregistered exact-reference identity criterion still fails: generated and host reference rule objects differ in `content_hash`, `revision`, and `rule_uid` in addition to the generated rule name. Other rule fields match in the capture. The strict failure is retained; the rule is not credited as identical to the host candidate. Graph-route median total was 133.20 ms, compared with 77.51 ms for the host default-order policy, so this capture shows no operating-cost advantage. The follow-up boundary remains residual/cue generation, explicit semantic-versus-provenance identity policy, and reducing the host-extracted applicability and Python materialization responsibilities. See [v1.3 results](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_3_RESULTS_20261003.md).

The substrate already has a graph-resident structural-edit composer. Its A8 action-rule path chooses an applicable `EditOp` with a Term over graph nodes and can place a selected variant into an experiment delta. The navigation polarity study exercised that path: with the cue `flip`, it selected `flip_comparison` and the generated rule passed four held-out directions in each of three workers. A new opt-in general-rule path has now been extended with an edge-identity guard operator and graph-held site selection. These are useful prompted structural repairs, not autonomous diagnosis or a general candidate search.

That path is narrower than the host correction candidate space in the four-family panel:

- The A8 rule selector filters `RuleSummary` candidates to `writes_chosen_action == 1.0` (`seeds/composer_experiment_graph.json`, `compose_experiment_mint_parametric`). It is designed to vary action rules.
- The action-rule edit catalogue includes comparison flip, attribute-key swap, match-edge drop, and match-guard insertion. A8's EditOp choice is graph-resident, but applicability features are derived from `RuleSummary.rule_json` by host Python and copied onto graph nodes. The rule JSON variant is then assembled into the experiment delta by the graph composer.
- The four-family thoughtexperiment panel also includes non-action targets. Shape-axis's successful structural repair is `swap_term_leaf:key->signature`; recurrence's is the domain-specific `dedup_identity_fix`; control-kind's target is a classifier, not a chosen-action rule. These are outside A8's current selection filter or operator vocabulary.
- A clean-boot exploratory shape-axis call to `ground_concern` with a swap cue did not produce a variant: there was no eligible `RuleSummary` matching the action-rule selector. This smoke probe is not source-locked evidence; it is consistent with the selector's explicit scope and is retained only to guide the next protocol.

The edge-identity proposal gate closes a narrow portion of this gap: the harness no longer enumerates its proposal sites or supplies candidate edits for the recurrence and repeated-reply fixtures. The reusable edit layer extracts applicable sites from rule JSON, graph `EditSite` nodes expose the alternatives, and a native Term selects the operator/site before a mechanical Python applier constructs the variant. Applicability extraction and application still run in Python, and the task adapter supplies the target, residual cue, examples, and oracle. Broader self-correction rule families and residual discovery remain unmeasured.

## Next gated evaluation

The next protocol should add a substrate-composed proposal arm to the v1.2 held-out task fixtures and keep the host-enumerated candidate list as a reference arm. Before capture, define the supported rule classes and operator/site vocabulary, specify how proposals are materialized and rejected when invalid, and freeze the symptom cue per task. On the same held-out instances, report:

1. whether the substrate emits a proposal or honestly abstains;
2. candidate digest inclusion in the host reference set, plus exact edit operator and site;
3. held-out task utility, false-proposal and invalid-rule rates;
4. useful-candidate recall and candidate diversity;
5. substrate decision time, host feature extraction/materialization time, branch/oracle time, and total cost.

The v1.1 extension added a real actor-recipient rule as a broader-scope failure boundary: an agent-level guard suppresses a second valid verb in all eight held-out episodes. V1.2 adds attribute-signature hypotheses from direct bound Attr terms on fresh `add_node` targets. The graph Term selects `actor+verb`; it restores `[1,1]` outputs in all eight cases while the relation-only negative control continues to produce `[1,0]`. Thus the bounded edit language now covers both relation-level idempotence and this actor/verb identity case. It remains limited to directly grounded fields and O(m²) site enumeration, with extraction and application in Python. The next gate should measure larger signatures and graph sizes, test computed attribute expressions and additional rule families, then determine whether residual evidence can select or formulate cues without task-specific prompting. Keep the held-out oracle outside the proposal process and report Python applicability/materialization, graph-Term choice, branch execution, and total cost separately. Prompted composition does not establish open-ended self-improvement.

## Evidence

- [A8 graph-resident EditOp selection results](MAC_FAC_A8_RESULTS.md) and [A8 protocol](MAC_FAC_A8_PREREG.md)
- [Navigation prompted-repair results](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_RESULTS_20261002.md)
- [Four-family proposal-utility results](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_RESULTS_20261002.md)
- [`compose_experiment_mint_parametric`](../../../seeds/composer_experiment_graph.json), [`_compose_structural_variant`](../../../domains/reflective_faculty.py), [`_ensure_editop_applicability`](../../../domains/reflective_faculty.py), and [`_default_candidates`](../../../domains/self_correction.py)
- [Substrate edge-identity composer v1 results](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_RESULTS_20261002.md), [protocol](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_PREREG_20261002.md), and [source-locked analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_analysis_20261002.json)
- [Substrate edge-identity composer v1.1 results](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_1_RESULTS_20261002.md), [protocol](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_1_PREREG_20261002.md), and [source-locked analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_1_analysis_20261002.json)
- [Substrate edge-attribute identity results](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_V1_RESULTS_20261002.md), [protocol](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_V1_PREREG_20261002.md), and [source-locked analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_v1_analysis_20261002.json)
