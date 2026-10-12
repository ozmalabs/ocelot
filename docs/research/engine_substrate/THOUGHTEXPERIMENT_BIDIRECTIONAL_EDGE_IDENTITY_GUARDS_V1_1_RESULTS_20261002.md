# Bidirectional edge-identity guard proposals v1.1 — results

The corrected source-locked capture closes v1's held-out timing omission while preserving its tasks and gates. Four workers each tested two rule families. All 16 analysis gates pass, source hashes remain stable, and the result is 8/8 held-out trials correct for each selected scope.

The graph-evidence selector chose `edge_once:out:candidate:has_mint_offer:any_target` in all four recurrence workers and `edge_once:in:m:responds_to:any_target` in all four conversation workers. Candidate-scoped recurrence guards preserved two separately keyed offers; per-message conversation guards preserved replies to repeated greetings and questions. Coarser episode, agent, and speech-act guards failed held-outs. All-wrong and tie controls abstained, and source-rule positive controls passed.

The generator and task construction are evaluation-harness code. The selector used native graph-Term inference over opaque candidate IDs and training outcome evidence, but proposal generation was manually authored as a generic AST scan. This demonstrates substrate-side selection and held-out transfer on two authored fixtures; it does not demonstrate substrate-driven problem discovery, proposal invention, integration, or broad task generalization.

Timing now includes every training and held-out episode, including recurrence, plus setup, proposal generation, composer, selector, controls, source controls, and total stage time. Across workers, median scoring time for all candidate trials was 47.4 ms (recurrence training), 47.6 ms (recurrence held-out), 98.4 ms (conversation training), and 102.6 ms (conversation held-out). Generic proposal generation took 0.11–0.16 ms median; the fixed composer took 29–36 ms; selector calls took 0.46–0.78 ms. These are local sequential diagnostic timings, with no CPU isolation or cross-host replication. They do not constitute a general hardware performance claim.

## Artifacts

- [v1 preregistration](THOUGHTEXPERIMENT_BIDIRECTIONAL_EDGE_IDENTITY_GUARDS_V1_PREREG_20261002.md)
- [v1.1 timing amendment](THOUGHTEXPERIMENT_BIDIRECTIONAL_EDGE_IDENTITY_GUARDS_V1_1_AMENDMENT_20261002.md)
- [v1.1 runner](../../../evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py)
- [v1.1 analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py)
- [source lock](../../../evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_lock_20261002.json)
- [training orders](../../../evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_orders_20261002.json)
- [held-out scores](../../../evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_scores_20261002.json)
- [independent analysis](../../../evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_analysis_20261002.json)

Next, test whether the substrate can produce a useful proposal from a measured residual without a hand-written candidate scanner, then broaden task families and separately measure branch creation/merge costs in the thoughtexperiment harness.
