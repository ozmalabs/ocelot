# Cyclic rule and progress-cap pilot results

**Status:** exploratory engine-contract diagnostic. This is evidence about one executor path and workload, not a general cap or termination guarantee.

## Question and method

Does the public native `run_rules(max_steps)` call settle or enforce a hard progress-step cap on a simple deterministic oscillation? A two-node graph starts with one `pilot_toggle_a` edge. Rule A deletes it and adds `pilot_toggle_b`; rule B performs the inverse. Fresh graphs were run with caps 1, 2, 3, 4, and 8, followed by a one-step ordinary-runner probe. A separate run used `run_rules_scoped(100, detect_cycles=True)` and then the same probe. The [raw diagnostic](../../../evaluation/reports/substrate_cyclic_cap_pilot_20260924.json) records environment, native artifact hashes, tracked patch hash, commands, and every outcome. The [harness](../../../scripts/substrate_cyclic_cap_pilot.py) can be rerun from the repository root with `PYTHONPATH=runners/dsl/python:.`.

## Results

| Condition | Requested cap | Legacy progress steps | Typed status | Typed overshoot | Probe progress | Typed/legacy parity |
|---|---:|---:|---|---:|---:|---|
| Ordinary | 1 | 2 | `progress_budget_reached` | 1 | 2 | Pass |
| Ordinary | 2 | 2 | `progress_budget_reached` | 0 | 2 | Pass |
| Ordinary | 3 | 4 | `progress_budget_reached` | 1 | 2 | Pass |
| Ordinary | 4 | 4 | `progress_budget_reached` | 0 | 2 | Pass |
| Ordinary | 8 | 8 | `progress_budget_reached` | 0 | 2 | Pass |
| Opt-in cycle detection | 100 | 2 | `repeated_graph_state` | 0 | 2 | Pass; scoped legacy path returned the same count/state. |

For this two-rule construction, the nominal cap is checked at the outer iteration boundary while multiple rules can each contribute a progress step inside a pass. Thus the returned count can exceed `max_steps`; this is not a hard per-rule budget. The new typed report correctly identifies all ordinary calls as budget-limited and reports the overshoot. Opt-in cycle detection returns `repeated_graph_state`, distinct from fixed point. All five ordinary conditions had identical graph state and progress counts between the typed and legacy APIs, and both were still active according to the probe.

The raw artifact contains nine conditions: the five cap values, one opt-in cycle-detection parity comparison, and three boundary controls. The additional controls behaved as specified: an unmatched rule returned `fixed_point` with zero steps; a zero budget returned `progress_budget_reached` with zero passes and preserved the input edge, after which a larger-budget call completed the one-shot rewrite and returned `fixed_point`; a one-shot rewrite that used exactly one progress step under budget 1 returned `progress_budget_reached`, and its follow-up pass established `fixed_point`. The exact-boundary status is intentionally conservative because proving settlement can require an additional pass.

## Implication and next work

Budget-capped benchmarks should inspect the typed status and use a post-run probe as an independent cross-check until focused regression coverage is in place. Do not interpret a legacy `run_rules` integer return as settlement. Next, add focused fixed-point, zero-budget, exact-boundary, and resume-after-budget tests; measure report overhead; then migrate remaining harnesses. Any future strict cap must preserve unprocessed dirty rules across interruption; simply breaking mid-pass could lose scheduled work.

This pilot does not investigate memory exhaustion, host callback loops, asynchronous schedulers, randomized/external-state rules, or other forms of nontermination.
