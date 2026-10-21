# Cognition build Phase 5 — Results

**Protocol:** `cognition_p5_heldout_v1`  
**Frozen preregistration commit:** `0826089af64c38da3c34d3be2c96ca490364ffa3`  
**Registered draw:** indices 0–199, plus 100 generated adverse/control inputs per family.  
**Report:** `evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200.json`  
**Analysis:** `evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200_analysis.json`

The runner produced 200 primary paired cases and 100 adverse/control input records for each of F1, F2, G2, G3, E3, E4, A2 and D6. The arm adapters were not integrated at freeze time, so each of the 3,200 primary arm result slots is null. Control inputs were generated but were not run through arms. The analysis preserves these nulls and returns `NOT_ESTABLISHED` for every item and overall. This is a harness-completeness result only; it supplies no efficacy, safety-rate, or mechanism-performance evidence.

| Item | Mechanism commit(s) and supported fixture class | Decision and registered evidence |
|---|---|---|
| F1 shared attributed-state view | `35c78e1f`; explicit source rows retaining owner, holder, source identity and epoch | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No conformance or source-preservation rate measured. |
| F2 recursive ToM | `2f9f9c41`; access-gated, acyclic, depth-bounded attributed paths | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No query accuracy or actual-world isolation rate measured. |
| G2 evidence-preserving reappraisal | `b7225e93`; evidence-linked frames preserving source events and forced constraints | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No supported-appraisal gain measured. |
| G3 native action inhibition | `7a15326d`, `6ea3ab94`, `e3fff962`; explicit stop/go events and one-use native-sink authorization | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate mechanism gate passes; this draw measured no sink rates. |
| E3 SCM intervention | `3abbba6e`, `b47a60de`, `64118d55`, `432c902f`; finite, provenance-bearing models with bounded assignments | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No oracle agreement or abstention rate measured. |
| E4 planner | `a3207840`, `9b028b91`; versioned transition graphs, bounded search and exact complete-path projection | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate planner/G3 gates pass; no solve gain measured. |
| A2 decomposition completion | `5fa6e603`; nonempty required-key coverage by verified same-epoch child work | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate runtime/consumer gate passes; no completion rate measured. |
| D6 analog imagery | `5e86399e`, `4719bcb9`; exact square-lattice quarter-turn trajectories | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate imagery/ThoughtManifold gate passes; no held-out shape or work result measured. |

The preregistered criteria were not assessed because there are no arm observations. No null was scored as a failure or success, and no item was dropped. The generated report files remain uncommitted.

Reproduction commands:

```sh
COGNITION_PREREG_HASH=0826089af64c38da3c34d3be2c96ca490364ffa3 OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_heldout_v1.py 0826089af64c38da3c34d3be2c96ca490364ffa3 0 200
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_analysis_v1.py evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200.json
```

The profile integration gate passes 28 tests. The registered analysis verdict remains `NOT_ESTABLISHED`; passing mechanism tests do not replace the missing paired arm observations.
