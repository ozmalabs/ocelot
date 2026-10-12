# Grammar widening and search-depth pilot (2026-10-03)

## Question

After the Neg/Eq/And learner fails on additive conservation or product
conservation, what does targeted operator widening cost, and how does the
size bound affect recovery?

## Method

This is an exploratory, single-panel-per-family pilot, not a preregistered
capability result. It reuses worker 0's frozen four-example training sets and
32 input probes from the model-adequacy audit v1.1 lock. The target relation is
used by the harness to choose the added operator (Plus for additive, Times for
product), so operator selection is informed by the task and does not measure
autonomous grammar discovery. Candidate terms are rescored on the same
1,296-point disjoint fractional grid.

## Observed outcomes

| Search operators | Maximum size | Additive | Product |
|---|---:|---:|---:|
| Plus, Eq / Times, Eq | 9 | 6 candidates, 1 exact; 5.03 s | 7 candidates, 1 exact; 4.18 s |
| Neg, Eq, And, Plus / Neg, Eq, And, Times | 9 | 17 candidates before 12 s timeout | 28 candidates before 12 s timeout |
| Neg, Eq, And, Plus / Neg, Eq, And, Times | 7 | 2 candidates, 1 exact; 2.13 s | 11 candidates, 1 exact; 1.86 s |

The two exact candidates matched every case in the 1,296-point holdout. The
size-7 search found them before exhausting its bound. Retaining the baseline
operators at size 9 caused timeout after returning partial candidate pools.
The pilot suggests size bound and grammar breadth dominate the measured search
cost on these panels. It also exposes a design tradeoff: the smaller
Plus/Eq and Times/Eq grammars are task-informed and discard baseline
expressivity; the size-7 expanded grammars preserve the baseline operators,
but lower the maximum term size.

## Interpretation and next gate

This pilot demonstrates that the synthesizer can recover these two authored
relations when the relevant primitive is supplied and the search bound includes
a compact expression. It does not show the substrate can infer which primitive
to add, select a safe widening policy, or transfer to other relations. One
panel per task is insufficient to estimate reliability. The next source-locked
run should replay all five existing panels per task, compare size-7 and size-9
expanded grammars under a fixed timeout, and retain a query-only arm as a
control. It should report exact-target inclusion, false singleton, empty and
partial spaces, timeout rate, candidate count, native evaluations, wall/CPU
cost, and the cost of externally supplying the primitive hint. A separate
policy must choose whether to query, widen, or ask for assistance without
seeing held-out labels or the target task label.

## Inputs and reproduction context

The frozen panel source is
[evaluation lock](../../../evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json).
The worker-0 additive and product inputs are in that lock; this pilot used the
current `domains.generator.synthesize` and native engine through the Python
bindings. Measurements are exploratory and not source-locked; no pooled or
general-performance claim should be inferred from them.
