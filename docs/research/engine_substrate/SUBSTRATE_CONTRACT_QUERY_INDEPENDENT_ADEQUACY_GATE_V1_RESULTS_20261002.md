# Independent post-selection adequacy gate v1 — results

## Result

The source-locked audit covers 24 captured worker outcomes across six representable task configurations, one generated-pool false-singleton configuration, and an out-of-grammar task whose pool was empty. The four fresh audit descriptors per nonempty case are checked against that case's known, candidate, and held-out descriptors; an independent analyzer recomputes all labels and predictions and verifies native/Python agreement. All 24 cases pass source/input integrity and replay checks.

| Audit budget | Accepted | Rejected | Empty-pool refusals | False acceptances | False refusals among positive controls | Native audit evaluations |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 21 | 0 | 3 | 3 | 0/18 | 0 |
| 1 | 18 | 3 | 3 | 0 | 0/18 | 21 |
| 2 | 18 | 3 | 3 | 0 | 0/18 | 42 |
| 4 | 18 | 3 | 3 | 0 | 0/18 | 84 |

The 18 positive controls are three worker repeats each for triangular, square, Euler, correctly recovered cubic, broad-grid cubic, and sparse-grid cubic. All pass every audit prefix. The three alias false singletons pass vacuously at budget 0, then are rejected by the first fresh label in all three workers. The three empty absolute-value pools remain refused without fabricating a candidate or spending audit calls. Total measured native evaluation time across the 21 nonempty cases is about 0.20 ms at budget 1 and 0.29 ms at budget 4 on this host; these tiny timings are descriptive only.

## Interpretation and limits

This supports a low-cost post-selection validation step as a way to catch the specific finite-grid false singleton: one fresh labeled example rejects it, while the represented controls pass and empty pools remain refused. That is a harness-side rule over externally supplied independent labels. It is not yet an integrated substrate learning/adoption gate, does not select or produce trusted audit labels, and does not prove models correct outside the audit set. The 24 cases include repeated workers on only seven task configurations; the observed 0/18 false-refusal and 0/21 post-audit false-accept counts are control-panel outcomes, not natural-task rates or calibrated confidence bounds.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_CONTRACT_QUERY_INDEPENDENT_ADEQUACY_GATE_V1_PREREG_20261002.md)
- Runner: [source and input locked runner](../../../evaluation/substrate_capability/substrate_contract_query_independent_adequacy_gate_v1.py)
- Analyzer: [independent replay analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_independent_adequacy_gate_v1.py)
- Lock: [parent capture/source lock](../../../evaluation/substrate_capability/substrate_contract_query_independent_adequacy_gate_v1_lock_20261002.json)
- Capture: [raw audit outcomes](../../../evaluation/reports/substrate_contract_query_independent_adequacy_gate_v1_raw_20261002.json)
- Analysis: [machine-readable analysis](../../../evaluation/reports/substrate_contract_query_independent_adequacy_gate_v1_analysis_20261002.json)
