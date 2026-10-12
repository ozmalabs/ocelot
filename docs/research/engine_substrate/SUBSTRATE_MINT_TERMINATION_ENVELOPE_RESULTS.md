# Mint termination envelope probe results

**Date:** 2026-09-25  
**Evidence grade:** mechanism tested (synthetic rule shape).  
**Protocol:** [`SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md`](SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md)  
**Raw records:** [`substrate_mint_termination_envelope_20260925.json`](../../../evaluation/reports/substrate_mint_termination_envelope_20260925.json)

## Result

All 18 independently constructed substrate instances passed their preregistered status and state checks (three repeats × three input sizes × two conditions, in one runner process). The keyed `add_node_if_absent` condition reached `fixed_point` in two progress steps for every size. Final `(nodes, edges)` were `(3,3)`, `(4,5)`, and `(6,9)` for one, two, and four initial path links. The unrestricted `add_node` condition returned `progress_budget_reached` at exactly 32 progress steps and grew to `(34,33)`, `(67,66)`, and `(133,132)` respectively. No budget overshoot occurred in this fixture.

This confirms that recursive fresh-node growth is observable and that finite-key deduplication can stop this particular rule family. It demonstrates why a status-returning API is useful: node growth and the typed cap status agree. Wall and CPU times are retained in the raw report as descriptive single-run measurements; the probe was designed around semantics and stopping behavior, not timing inference.

## Limits and next proof obligation

This is not a general mint-termination result, nor a weak-acyclicity result. The conservative finite-key fragment and abstract progress bound have since been written down, and one admitted rule has passed native loader/access-set and post-install wakeup checks; see [`SUBSTRATE_MINT_TERMINATION_FRAGMENT_ANALYSIS.md`](SUBSTRATE_MINT_TERMINATION_FRAGMENT_ANALYSIS.md). Remaining gaps include broad native schema parity, interacting rule sets, effects outside the insertion-only fragment, scheduler completeness, and matching cost. The current API permits unrestricted `AddNode`; callers still need progress budgets and external resource supervision outside any separately proven fragment.
