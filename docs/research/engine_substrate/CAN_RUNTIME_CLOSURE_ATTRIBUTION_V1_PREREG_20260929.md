# Runtime CAN closure attribution v1 preregistration (2026-09-29)

## Question

Which native rule-matching and Term-evaluation counters account for the sharp closure-time growth seen in the exact-inference scale panel, and does audit instrumentation preserve the settled state and progress count?

## Design

Use N in {128,256}, topology in {path, banded2}, mode in {2state,3state}, and two deterministic replicates per cell (16 fresh workers). Recreate the same fields, quantized factors, and native graph as `can_runtime_generated_exact_inference_scale_v1.py`. Each worker runs an uninstrumented closure, then builds an identical fresh graph and repeats closure with native scale audit and per-rule counters enabled. Compare progress count and complete final state; independently check the final state is a fixed point using the fixture's local update predicate. Record whole-run candidate, tested-binding, Term-evaluation, edge/node effect counters and per-rule breakdown. Instrumented time is diagnostic only.

## Integrity gates

Require 16 unique worker PIDs and complete coverage; deterministic input graphs; uninstrumented/audited state and progress parity; zero independent fixed-point residuals; no closure cap reached; nonempty audit counters; pre/post source/native-lock equality; and a complete per-rule metric capture. No timing threshold or post hoc cell exclusion.

## Scope

This attributes one authored CAN rule family on fixture-generated path/banded2 graphs. It does not attribute other seeds/domains, prove a general complexity bound, or measure natural graph distributions. Audit timings are not used as ordinary runtime estimates.

## Reproduction

```sh
python3 evaluation/substrate_capability/can_runtime_closure_attribution_v1.py --lock
python3 evaluation/substrate_capability/can_runtime_closure_attribution_v1.py
```
