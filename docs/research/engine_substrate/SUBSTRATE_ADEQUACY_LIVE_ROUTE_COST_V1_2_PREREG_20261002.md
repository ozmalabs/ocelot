# Live strict-route evidence-count, cost, and parent-graph delta panel v1.2 — preregistration

## Question

How do signed evidence count and outcome class affect cost and actual codebook change on the strict selected-probe `WorldAdapter.converse` path?

This confirmatory revision retains the v1 task/cell design and adds a full semantic parent-graph delta gate. The v1 timing/outcome capture is preserved; its omitted graph gate is not retroactively treated as passed.

## Conditions

Use the existing independent parity and threshold tasks with their separate executable oracles, correct and constant-false candidates, broad domains, and held-outs. Cross provider counts 1/3/5 with four conditions: truthful correct candidate; truthful wrong candidate; all trusted sources sign the same false label for the wrong candidate; and conflicting signed labels for the wrong candidate. The conflict condition is undefined at m=1 and is omitted there. Run each task × condition × count × repetition in a fresh process, three repetitions per cell (66 workers).

Every row uses one selector-chosen fresh nonzero-entropy probe and exactly m request-bound HMAC labels. Capture separate process wall, adapter construction, probe selection/request/signing, receipt adjudication, live `converse`, and held-out evaluation timings. The primary cost comparison is the live `converse` call by provider count; process wall includes startup and is separately reported. This measures exact unanimity as implemented; it does not compare hypothetical vote thresholds.

## Gates

Require source/native/base-oracle lock stability; complete schedule and 66 distinct PIDs; exact selector, signature, and receipt replay; condition-specific receipt status, actual code-shape delta and held-out outcome; positive timing values; and a canonical full-graph snapshot immediately before and after the live call. For refusal/ambiguity, require exact graph equality, including allocator `next_id`. For adoption, require exactly one new code-write `ShapeSignature`, no removed or modified old nodes or edges, and permit only new edges incident to that shape. Record all graph snapshots in raw output so the independent analyzer can reproduce the delta. Report medians descriptively; three workers per cell are not a throughput confidence interval.

## Limits

One host, two authored Boolean families, test keys, deterministic labels and finite synthetic domains. Provider IDs are not real trust domains. The false-label case is an adversarial boundary, not prevalence. The panel does not estimate natural boot frequency, multi-probe cost, or full-seed user-request cost.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_2.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_2.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_live_route_cost_v1_2.py
```
