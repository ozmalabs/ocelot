# Live strict-route evidence-count and cost panel v1 — preregistration

## Question

How do signed evidence count and outcome class affect cost and actual codebook change on the strict selected-probe `WorldAdapter.converse` path?

## Conditions

Use the existing independent parity and threshold tasks with their separate executable oracles, correct and constant-false candidates, broad domains, and held-outs. Cross provider counts 1/3/5 with four conditions: truthful correct candidate; truthful wrong candidate; all trusted sources sign the same false label for the wrong candidate; and conflicting signed labels for the wrong candidate. The conflict condition is undefined at m=1 and is omitted there. Run each task × condition × count × repetition in a fresh process, three repetitions per cell (66 workers).

Every row uses one selector-chosen fresh nonzero-entropy probe and exactly m request-bound HMAC labels. Capture separate process wall, adapter construction, probe selection/request/signing, receipt adjudication, live `converse`, and held-out evaluation timings. The primary cost comparison is the live `converse` call by provider count; process wall includes startup and is separately reported. This measures exact unanimity as implemented; it does not compare hypothetical vote thresholds.

## Gates

Require source/native/base-oracle lock stability; complete schedule and 66 distinct PIDs; exact selector, signature, and receipt replay; condition-specific receipt status, actual code-shape delta and held-out outcome; parent graph unchanged except the expected single code-shape adoption; and positive timing values. Report medians descriptively; three workers per cell are not a throughput confidence interval.

## Limits

One host, two authored Boolean families, test keys, deterministic labels and finite synthetic domains. Provider IDs are not real trust domains. The false-label case is an adversarial boundary, not prevalence. The panel does not estimate natural boot frequency, multi-probe cost, or full-seed user-request cost.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_live_route_cost_v1.py
```
