# Cold initialization and warmed code-adoption route v1 — preregistration

## Question

How do first-turn initialization and a subsequent full `WorldAdapter.converse` call compare in wall/CPU cost, and does the warmed route retain the same receipt-gated adoption/refusal behavior across parity, clamp, and square?

## Design

Run three fresh workers for each task × condition cell: parity, clamp, square crossed with truthful accepted evidence versus missing evidence (18 workers). Construct the candidate Term and audit request before timing. Each worker boots a strict-auth `WorldAdapter`, performs one identical first-turn `converse("hello")` to exercise cold lazy initialization, then performs one target `converse` with the task function source. The adoption arm supplies one valid request-bound HMAC label and accepted receipt from the independent task oracle; the refusal arm supplies no evidence. Capture wall and process CPU separately for cold warm-up and target turn, plus full graph snapshots and code-write shape/epoch state before and after the target call. Evaluate held-outs against the independent oracle after timing.

## Gates

Require 18 unique fresh PIDs, complete schedule, source/native/seed/oracle lock stability, receipt replay and HMAC verification for adoption rows, exactly one new code-write shape for truthful adoption, zero shape/epoch growth for missing evidence, and exact native held-out predictions on all accepted rows. Reconcile graph counts and codebook changes per turn; full graph equality is not required because ordinary conversation writes turn and communication records. Report cold initialization and warmed-call costs separately and report graph deltas descriptively. Three workers per cell are descriptive, not confidence intervals.

## Limits

One host, three authored arithmetic/Boolean functions, one test provider, one warm-up utterance, and three workers per cell. The warmed call may still perform task-specific lazy initialization; graph deltas and loaded seed counts will expose remaining additions. This is not a production workload or natural-task cost distribution, and HMAC authentication does not establish label truth.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_cost_v1.py
```
