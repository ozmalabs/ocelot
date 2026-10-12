# Thoughtexperiment fresh-rule active query v1 — preregistration

## Question

Does the substrate-composed structural proposal plus active-query sequence transfer to a newly authored target rule, outside the existing control-kind and shape fixtures?

The new target, `classify_meter_mode`, is an authored binary threshold rule over a World → Request → Measurement graph. The fault reverses the comparison inside the rule's effect. The prompt identifies the target family and requested comparator flip; the graph Term must select the target and `flip_comparison`, then the edit applier materializes the changed rule. This tests a new rule family and substrate path, while task construction, the fault, prompt, candidate examples, and oracle remain designed by the harness.

## Procedure

Four workers build the rule in clean substrates, expose a single mutable target, and call `compose_general_structural_variant`. Before outcome labels are computed, each worker captures the emitted target/operator/site, semantic digest, comparison with the independent generic candidate enumerator, and four active-query choices. Each query pool contains 100 unique examples with 0%, 50%, 90%, or 99% zero-score cases. For each candidate, two isolated native branches execute the fault and proposal rules; only score, positive label, negative label, and a nuisance probe ID enter the selector. The expected class is withheld until the orders file is written.

The task oracle returns `HOT` for positive scores and `COLD` otherwise. After query selection freezes, the scorer adjudicates the selected input, measures a seeded random probe, and evaluates both rules on four separate held-out inputs spanning positive, negative, and zero scores. It checks receipts, source preservation, and a second closure pass for fixed point. Source/native hashes are verified before and after each stage.

## Measures and pass conditions

Pass requires all four workers to select the newly authored target and `flip_comparison`, match the generic host candidate semantically, choose a valid one-bit query in all 16 pools, and retain only the composed proposal after the oracle label. The proposal must pass all four held-outs; the faulty rule must fail at least one nonzero held-out in every worker. Every branch must preserve the primary rule store and reach fixed point. Report random one-query outcomes, selector cost, proposal/branch cost, and closure work. These synthetic values do not establish natural task accuracy or asymptotic complexity.

## Scope boundary

This is cross-family structural transfer on a newly authored symbolic rule, not autonomous diagnosis or open-ended invention. The prompt names the repair family, and Python builds the rule, score pools, and oracle. The composer performs graph-resident target/operator selection; Python performs generic rule materialization. The query selector receives native Terms and a finite candidate set; prediction callbacks execute native graph closure. Success would extend measured compositional reach beyond the prior task fixtures, while rung 3/4 learning remains open.

## Reproduction

Run `python3 evaluation/substrate_capability/thoughtexperiment_fresh_rule_active_query_v1.py --lock`, `--orders`, and `--score`, then run `python3 evaluation/substrate_capability/analyze_thoughtexperiment_fresh_rule_active_query_v1.py`.
