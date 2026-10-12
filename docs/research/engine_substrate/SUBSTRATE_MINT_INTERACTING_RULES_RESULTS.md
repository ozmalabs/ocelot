# Interacting mint rules: native closure and finite-bound results

**Date:** 2026-09-25  
**Evidence grade:** mechanism tested on two synthetic rule sets.  
**Protocol:** [`SUBSTRATE_MINT_INTERACTING_RULES_PREREG_20260925.md`](SUBSTRATE_MINT_INTERACTING_RULES_PREREG_20260925.md)  
**Runner:** [`substrate_mint_interacting_rules.py`](../../../scripts/substrate_mint_interacting_rules.py)  
**Raw report:** [`substrate_mint_interacting_rules_20260925.json`](../../../evaluation/reports/substrate_mint_interacting_rules_20260925.json)

## Results

Both workloads passed every check. The classifier accepted both rule sets; native `add_rule` installed them; `run_rules_report(1000, false)` returned `fixed_point`; native graph state exactly matched the independent positive-closure evaluator, including every edge triple and minted node-type count; and native progress steps remained below the static bound.

| Workload | Mint signatures (`R`) | Edge types (`E`) | Static bound | Native progress steps | Oracle effectful bindings | Final nodes/edges |
|---|---:|---:|---:|---:|---:|---:|
| Cascade | 2 | 4 | 100 | 3 | 4 | 5 / 6 |
| Feedback | 1 | 2 | 31 | 2 | 4 | 4 / 6 |

The cascade produced one shared `Witness` and one shared `Marker`; the feedback cycle created new `seed_link` matches that only produced already-present derived facts, then settled. The independent evaluator's effectful-binding count is not the native `progress_steps` unit: the native runner groups work differently. The measurements are reported separately and only the conservative inequality against the static bound is used.

## What this establishes

This provides native-path evidence for two interacting rule sets, two deduplicated mint signatures in the cascade, positive cross-rule enabling, and one feedback cycle that settles at the exact finite closure. It extends the single-rule probe. It does not prove that every admitted rule set receives complete scheduler wakeups, that imports and rule rewrites preserve the fragment, or that native matching cost is polynomial. The abstract bound counts possible graph facts; work to enumerate candidate bindings remains unbounded by that fact count alone.
