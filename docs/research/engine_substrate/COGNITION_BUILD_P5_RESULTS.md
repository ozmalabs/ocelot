# Cognition build Phase 5 — Results

**Protocol:** `cognition_p5_heldout_v1`  
**Frozen preregistration commit:** `0826089af64c38da3c34d3be2c96ca490364ffa3`  
**Registered draw:** indices 0–199, plus 100 generated adverse/control inputs per family.  
**Report:** `evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200.json`  
**Analysis:** `evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200_analysis.json`

The runner produced 200 primary paired cases and 100 adverse/control input records for each of F1, F2, G2, G3, E3, E4, A2 and D6. The arm adapters were not integrated at freeze time, so each of the 3,200 primary arm result slots is null. Control inputs were generated but were not run through arms. The analysis preserves these nulls and returns `NOT_ESTABLISHED` for every item and overall. This is a harness-completeness result only; it supplies no efficacy, safety-rate, or mechanism-performance evidence.

| Item | Decision | Evidence and limit |
|---|---|---|
| F1 shared attributed-state view | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No exact-view or source-preservation rate measured. |
| F2 recursive ToM | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No belief-query accuracy or actual-world isolation rate measured. |
| G2 evidence-preserving reappraisal | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No supported-appraisal gain measured. |
| G3 native action inhibition | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No sink stop/go rate measured in this draw. Separate mechanism gate passes. |
| E3 SCM intervention | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No oracle agreement or abstention rate measured. |
| E4 planner | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No solve gain or observed-success rate measured. Separate planner/G3 gates pass. |
| A2 decomposition completion | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No completion accuracy rate measured. Separate runtime/consumer gate passes. |
| D6 analog imagery | NOT_ESTABLISHED | 200 paired input cases and 100 control inputs generated; 400 primary arm results null. No shape verification or transform-work comparison measured. Separate imagery/ThoughtManifold gate passes. |

The preregistered criteria were not assessed because there are no arm observations. No null was scored as a failure or success, and no item was dropped. The generated report files remain uncommitted.

Reproduction commands:

```sh
COGNITION_PREREG_HASH=0826089af64c38da3c34d3be2c96ca490364ffa3 OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_heldout_v1.py 0826089af64c38da3c34d3be2c96ca490364ffa3 0 200
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_analysis_v1.py evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200.json
```

The profile integration gate passes 28 tests. The registered analysis verdict remains `NOT_ESTABLISHED`; passing mechanism tests do not replace the missing paired arm observations.
