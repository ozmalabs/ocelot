# Live runtime rule-set census v1 — preregistration (2026-10-04)

## Question

How much of the native rule set and measured closure work in the source-locked live route falls within the finite-key insertion fragment used by the synthetic closure scaling results? How much live work is attributable to post-boot minted rules or secondary native stores whose full rule bodies were not exported?

## Fixed inputs and sample

This is a derived analysis of the already completed live runtime closure counters v1.6 capture, not a new runtime run. Select replicate 0, audit-on, its pre-request `native_exported_rules`/full graph snapshot, and both per-request counter records. The worker input remains the authored two-request sequence. Preserve all 2,357 exported rule definitions, all later identity/metadata rows, all secondary stores, and every unsupported or unmapped definition as an explicit census category.

The capture exports the primary rule bodies before the first request, but only `(RuleUID, name, definition hash)` for definitions after each request. Therefore post-boot minted rule bodies and rule bodies belonging to other stores may be unavailable. Report them as uncovered; never infer their effects from names or hashes.

## Procedure

1. Validate the v1.6 raw capture against its locked source manifest and passing independent analysis.
2. Crosswalk each store-qualified audit identity to the primary exported rule vector using both local index and exact metadata name/arity. Select the unique store with the maximum crosswalk for each prompt. Require that crosswalked identities are one-to-one and report every baseline definition absent from a prompt's identity snapshot as unobserved; do not present an unobserved row's zero-filled work fields as evidence of zero execution.
3. For each baseline rule, retain match arity, condition-root/operator features, effect-operation counts, batch flag, and post-request candidate/Term work by prompt.
4. Apply the existing `analyze_mint_termination_fragment.py` checker to every baseline rule. Rules with a non-null `where` are explicitly classified outside the checker schema; all other rules are passed unchanged as `(name, match, effects)` against the captured full graph. This is a static fragment classification using the final captured graph only as the checker’s graph reference; it is not a replay or a termination proof for the production run.
5. Partition measured per-rule work into baseline definitions, primary-store rules minted after the definition export, and secondary stores without exported definitions. Keep direct host `Substrate.evaluate` work separate. Verify each partition sums to the v1.6 global counters.

## Gates

1. Raw capture, v1.6 analysis, source lock, checker, protocol, runner, and analyzer hashes are unchanged before and after profiling.
2. Exactly one worker matches the fixed sample; all 2,357 baseline UIDs are unique and every rule receives a checker or explicit unsupported classification.
3. A unique primary store maps every observed baseline local index to the same definition name and match arity; absent baseline identities, additional local indices, and all secondary-store IDs remain visible as uncovered or unobserved rows.
4. Candidate-pair, candidate-test, and Term-evaluation totals partition exactly by store/definition coverage; direct host Term evaluations are added separately to recover global Term totals.
5. Report accepted-rule count and work share without using acceptance as evidence of natural prevalence, productive firing, or asymptotic behavior.

## Claim boundary

This census describes one full-seed, two-request authored runtime route. It can determine whether the finite-key synthetic fragment overlaps this rule set and its measured work on this route. It does not estimate natural workload frequency, classify all hidden secondary-store definitions, prove termination of excluded rules, or establish general complexity.

## Artifacts

- Runner: `evaluation/substrate_capability/live_runtime_ruleset_census_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_live_runtime_ruleset_census_v1.py`
- Lock: `evaluation/substrate_capability/live_runtime_ruleset_census_v1_lock_20261004.json`
- Profile: `evaluation/reports/live_runtime_ruleset_census_v1_20261004.json`
