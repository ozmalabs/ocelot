# Thoughtexperiment graph-authored correction ranking v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does the graph-authored structural-cost rank policy improve correction utility or reduce experiment cost over the fixed default candidate order on the existing bounded runaway-correction task?

## Source-path finding and scope

The current graph-composer adapter loaded `composer_self_correct_graph` as graph data but did not register its Rule node in the executable rewrite store. Its call to `tick()` also did not guarantee composer execution. The implementation now activates the exact seed-authored Rule and uses bounded `run_rules()` to execute it and compile the authored attempt-gate Rule. The experiment must confirm that the graph path returns `served_by=graph` and yields both the active `self_correct_gate_*` rule and `self_correct_rank_*` Program.

## Design

Use the existing `sd_mint_quantum` runaway correction fixture. Each fresh episode grounds the graph-authored collapse-watch and self-correction composers, installs the shape-decode loop, creates three first-wave pending observations, and settles the generated Impasse. The gate must mark that Impasse `correct_ready=true`. A second three-observation wave then creates the correction target workload. Candidate generation remains `_default_candidates`; the only treatment difference is whether the graph-authored rank Program is evaluated to order the candidates or the default fixed order is retained.

Run three fresh workers, each with both arms on fresh substrate instances: `default_order` and `graph_cost_rank` (six episodes total). The ranker scores the measured serialized structural delta against the original rule. Candidate evaluation stops at the first non-inert candidate that predicts convergence, exactly as the production correction loop does. Record order, attempted candidates, candidate cost, selection, adoption, phase and total wall time, and primary state preservation.

After correction, present a third, held-out continuation wave with three new observation signatures and settle native rules. The independent task oracle requires: (a) the approved repair is active and original target rule is inactive; (b) every third-wave observation is no longer pending; (c) exactly one induced CapabilityAxis is recorded for each of the three held-out signatures; and (d) direct rule closure reaches a fixed point. This checks later use on new values, rather than only reusing the correction-time `CollapseModel` verdict.

## Gates and primary comparisons

- Three fresh worker processes, each with both arms and distinct substrate state.
- Both composers are graph-authored; the rank Program exists in both arms before the ranking ablation.
- The gate marks the first Impasse correct-ready, and both arms identify `sd_mint_quantum`.
- Candidate outcomes and successful correction match between arms; both pass all held-out task-oracle conditions.
- Primary graph/rule state is unchanged by branch rehearsals before explicit adoption.
- Source, seed, build-manifest, and native-binary fingerprints are stable.
- Compare candidates tested, rehearsal wall time, end-to-end correction wall time, and held-out outcome. Report all six episode records and medians; do not infer a general ranking benefit from this one authored task.

## Interpretation limits

This measures an authored cost-minimizing selector and one existing correction family. It does not show that prior experiment outcomes train the rank policy, that structural edit size predicts task utility in general, or that the substrate discovers its own task or candidate grammar. The default order is a deliberate ablation control; the graph-authored rank Program remains installed, but is not evaluated in that arm. The held-out wave shares the same observation-processing family and is not a natural task distribution.
