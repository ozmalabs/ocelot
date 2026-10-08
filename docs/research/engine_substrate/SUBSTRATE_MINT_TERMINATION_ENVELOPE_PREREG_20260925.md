# Mint termination envelope probe preregistration

**Status:** preregistered diagnostic probe; this is not a weak-acyclicity theorem.

## Question

Does the native rule runner distinguish a recursively expanding fresh-node rule from a keyed, deduplicated witness rule, and do the typed termination statuses agree with exact graph oracles?

## Fixture

Start from a directed path of `n` `Seed` nodes joined by `link` edges. One rule matches `x -link-> y`, mints a `Witness`, then adds `y -link-> witness`. The newly created link is eligible for the same rule, so ordinary `add_node` generates an unbounded chain. The paired rule substitutes `add_node_if_absent` with the constant key `{tag: shared}`; all recursive firings reuse one witness and duplicate link insertions cease to progress.

## Conditions and measurements

- Sizes: 1, 2, 4 seed links; three independently constructed substrate instances per size/condition in one runner process.
- Conditions: `add_node`, `add_node_if_absent`.
- Progress budget: 32; `detect_cycles=false`; process supervisor timeout: 20 seconds.
- Capture typed status, passes, progress count, budget overshoot, node/edge counts, wall/CPU time, and native build provenance.
- Independent oracle: bounded arms must finish with exactly `n+1` nodes, one shared witness, and `n+1` links (the initial path plus one link from every path endpoint/derived match to that witness; exact derived-link count is checked from final edge tuples). Unrestricted arms must be labeled `progress_budget_reached` and exceed their initial node count. Since pass-boundary budgets are soft, overshoot is recorded and not treated as a failure.

## Interpretation rules

The probe tests one recursive rule shape and current engine semantics. A capped unrestricted run is evidence of observed growth, never a proof of nontermination. Successful keyed runs establish a mechanism-level behavior only; the finite key and monotone effect restrictions are not yet statically enforced or proven polynomial for general schemas. Do not infer general weak-acyclic termination from this result.

## Reproduction

Run `python3 scripts/substrate_mint_termination_envelope.py --output evaluation/reports/substrate_mint_termination_envelope_20260925.json` after confirming the native build is current with `domains.engine_provenance`.
