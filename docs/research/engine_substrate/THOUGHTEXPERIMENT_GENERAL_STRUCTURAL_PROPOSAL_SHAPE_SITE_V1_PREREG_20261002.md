# General structural proposal shape-site direction v1 — preregistration

**Question:** Does making ordered attribute-key swap sites explicit graph nodes allow the substrate's native Term Argmax to select a cue-matched direction, refuse ambiguous directions, and produce a useful shape-axis repair?

## Status and scope

This is a diagnostic, not confirmatory: an earlier unlocked smoke exposed the target and wrong-direction candidate outcome. The known useful host candidate is `swap_term_leaf:key->signature`; the earlier composer selected `signature->key`. The new site nodes enumerate actual ordered key pairs from a selected rule. The native Term scores their `keywords_text` against the axis predicates, selects a unique positive maximum, and abstains on ties. Python still extracts sites and applies the selected rewrite. No learning or unsupervised direction inference is claimed.

## Conditions

Use four independent adapter workers for the shape-axis task. In each, capture three graph-composer calls before any held-out scores:

1. **Cue-matched:** predicates contain the exact phrase `key to signature` plus the same target/operator cue.
2. **Reversed:** predicates contain `signature to key` plus the same target/operator cue.
3. **Ambiguous:** predicates contain `key signature` as separate terms and no directional phrase.

The host-generated candidate list is only a semantic reference. Orders/proposals are recorded before held-out scoring. The third condition must abstain rather than choosing an arbitrary tied site. Score both emitted variants, when present, and every host reference candidate against the existing independent shape-axis held-out oracle in isolated branches.

## Gates and reporting

- Freeze runner, analyzer, source code, shape task and adapter, engine/build inputs, this preregistration and amendment, and loaded native binary.
- In all workers, each emitted proposal must target `sd_mint_quantum`, use `swap_term_leaf`, preserve the target, and match one host reference candidate by semantic digest.
- Cue-matched and reversed conditions must emit different ordered variants. The ambiguous condition must abstain.
- Score every host candidate and proposal after order capture. Verify receipts and primary isolation for every branch. Report utility per worker and held-out case, candidate identity, target/operator/site, and cost phases available.
- Preserve all failures. The cue includes the desired direction, so success establishes cue-conditioned site selection, not discovery of which direction is correct. Four workers are repetitions of one authored family, not independent task families.
