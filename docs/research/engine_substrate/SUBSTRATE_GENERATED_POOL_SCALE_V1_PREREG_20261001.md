# Generated hypothesis-pool scaling v1

Status: preregistered bounded structural and resource sweep.

## Question

How do expression-size ceiling and the number of unlabeled probe environments affect complete generated-pool cost, pool size, and retention of the true held-out behavior across the three task families used by the active-query comparison?

## Workloads and crossed factors

Reuse the frozen triangular-number, square, and Euler task adapters, training examples, candidate inputs, and held-out inputs from the source-locked active-query comparison. Keep operators `Plus`, `Times`, `Minus`, `Div`, constants `(0, 1, 2, -1)`, output-constant expansion disabled, a 10,000 fitting-behavior cap, and no saturation stop.

Cross each task with four size ceilings and five probe counts:

- Triangular: max size 5/6/7/8.
- Square: max size 2/3/4/5.
- Euler: max size 3/4/5/6.
- Probe count: 0/1/3/6/10, taking the deterministic prefix of the candidate input family. Probes are unlabeled and are only used in the behavior signature.

Run two fresh-process repetitions for each of 60 task × size × probe cells. Randomize worker order independently within each repetition. Generation has an eight-second native synthesizer timeout; each worker also has a 15-second parent timeout. Do not retry, replace, or omit timeouts, crashes, solution-cap stops, or incomplete pools.

## Measures and gates

Capture source/build provenance, training/pool/held-out setup times, wall and CPU time, explored terms, distinct signatures, fitting-pool size, actual `halt_reason`, solution cap, probe count, process `ru_maxrss`, and evaluator-only held-out support checks. `ru_maxrss` is a process high-water mark that includes Python, extension, and task setup; it is not an allocation attribution or incremental pool-memory measurement. Report both raw RSS high-water and change from pre-synthesis high-water, with the latter clamped at zero and interpreted only as a rough lower bound.

The independent analyzer must verify current source and native-binary hashes, all 120 scheduled rows (including explicit worker errors/timeouts), expected cell coverage, complete-pool semantics (`halt_reason == "max_size"`), and held-out behavior for returned hypotheses. A capped/timed-out result is not called complete. Target support is computed only by the evaluator after collection and never affects the collector.

This is a resource and representation scaling study over three authored tasks. Probe-prefix results can be order-sensitive; this protocol does not estimate natural task distributions, prove random-probe behavior, or establish that larger grammars are generally tractable. The generator eagerly constructs each size cohort before registering its terms, so a parent timeout may occur before the synthesizer's internal timeout is observed; retain and report that distinction.

## Reproduction

Create a lock with `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_generated_pool_scale_v1.py --lock`, save it as `evaluation/substrate_capability/substrate_generated_pool_scale_v1_20261001_lock.json`, run the runner, then run `python3 scripts/analyze_substrate_generated_pool_scale_v1.py`. The runner refuses stale source locks and existing raw captures.
