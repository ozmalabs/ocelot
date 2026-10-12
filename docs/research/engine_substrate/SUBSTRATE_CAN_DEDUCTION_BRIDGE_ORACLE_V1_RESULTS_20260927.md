# CAN-to-deduction bridge oracle v1 results

Protocol: [preregistration](SUBSTRATE_CAN_DEDUCTION_BRIDGE_ORACLE_V1_PREREG_20260927.md)  
Run: `can-deduction-bridge-oracle-v1-20260927`  
Date: 2026-09-27

## Verdict

The deterministic CAN-state-to-deduction translation passes the exhaustive five-topic ternary oracle: **486/486 case-worker rows match the independently computed expected fact set exactly**. Both fresh processes pass every analyzer and control gate, including a global fact-set comparison across all `SmEntity` nodes. Positive and negative fact precision and recall are 1.0 in this panel, with zero missing, extra, or misattributed facts. The two all-ambivalent vectors emit no facts; all 810 individual zero-state topic decisions across workers are null, with zero false positives. The separate absent-state control also emits no fact.

The duplicate-call control changes no semantic attributes. A distinct all-zero Microtheory produces no facts in another target. Two Residents with ambiguous name-token containment produce no `denotes` edge from the ambiguous SmEntity; the bridge still uses its documented legacy Resident-to-Microtheory owner-name fallback, which is recorded and correctly attributes the tested fact to that owner's entity.

## Cost observed

Each worker constructs the five-topic panel in about 7.3–7.5 ms and spends 4.318–4.341 s in the 243 bridge calls (total process wall time about 4.4–4.5 s). Peak process RSS is 606.6–607.2 MB. At panel end the graph has 3,120 nodes and 1,965 edges.

Native counters per worker include 785,500 candidate enumerations, 559,267 where evaluations, 5,013,117 Term evaluations, and 12,058 rule enumerations. These totals expose the repeated correspondence settlement work on a single graph that grows through the panel. The first bridge call also includes lazy installation/settlement costs. They are workload counters for this harness, not asymptotic bounds or a general commodity-CPU estimate.

## Reproducibility and artifacts

The runner's complete registered source/runtime lock matched before and after each worker and again in the parent. Both worker PIDs are distinct. The independent analyzer passes 21 checks, including full case-ID coverage, per-case truth-table equality, global entity attribution, control outcomes, and cross-worker parity.

- Protocol: [preregistration](SUBSTRATE_CAN_DEDUCTION_BRIDGE_ORACLE_V1_PREREG_20260927.md)
- Runner: [substrate_can_deduction_bridge_oracle_v1.py](../../../scripts/substrate_can_deduction_bridge_oracle_v1.py)
- Independent analyzer: [analyze_substrate_can_deduction_bridge_oracle_v1.py](../../../scripts/analyze_substrate_can_deduction_bridge_oracle_v1.py)
- Source lock: [can_deduction_bridge_oracle_v1_lock_20260927.json](../../../evaluation/substrate_capability/can_deduction_bridge_oracle_v1_lock_20260927.json)
- Raw workers and integrity record: [can_deduction_bridge_oracle_v1_20260927.json](../../../evaluation/reports/can_deduction_bridge_oracle_v1_20260927.json)
- Independent analysis: [can_deduction_bridge_oracle_v1_analysis_20260927.json](../../../evaluation/reports/can_deduction_bridge_oracle_v1_analysis_20260927.json)

## Claim boundary and next measurement

This establishes translation fidelity only for the held five-topic, three-valued schema and the tested entity-resolution paths. It does not show that CAN states correspond to truth, improve downstream reasoning, or occur naturally at this rate. It says nothing about rung 3/4 induction. In particular, the repeated cross-entity correspondence pass already consumes millions of candidate/Term evaluations in this modest harness; scaling should be measured independently before calling bridge application cheap.

Next, measure natural rung-entry frequency on a task stream selected without reference to substrate success. Record transform, dimension-inference, and mint entry, all solved and failed cases, family-specific independent oracles, and full runtime closure. Keep this bridge panel as a narrow answer-fidelity result, not a pooled capability score.
