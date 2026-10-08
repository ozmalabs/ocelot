# Thoughtexperiment active probe selection v1 — preregistration

## Question

Given two supplied candidate rules for the shape-axis field (`CapabilityAxis.capability_keys` comes from an observation's `key` or its `signature`), can the substrate select a candidate observation that distinguishes the rules when most available observations are uninformative aliases?

This is a bounded probe-selection gate, not open-ended hypothesis generation or structural self-improvement. The hypotheses are supplied as native Terms. A task oracle applies the declared task semantics (`key` is the intended identity field), but its expected output is not passed to the selector.

## Procedure

Each worker creates pools of 100 deterministic observations at alias rates 0%, 50%, 90%, and 99%. An alias has equal `key` and `signature`; a discriminator has distinct values. Two native Terms read the respective fields. The substrate query selector receives only these Terms and candidate inputs. Its selected query, predictions, and entropy are frozen before the runner computes the task-oracle answer. A random single-probe baseline uses a preregistered seed and the same pool. The selected hypothesis is the only survivor if the oracle answer distinguishes the two predictions; otherwise the worker records unresolved.

Four independent workers repeat each condition with disjoint value namespaces. After the probe choice is frozen, the oracle label is applied and the selected hypothesis is checked on 20 separately generated held-out discriminators. No candidate pool output or expected answer is supplied to the selector. Inputs, hypotheses, alias proportions, condition order, random baseline seed, and held-out generation are fixed in this runner.

## Measures and pass conditions

Report selector query validity, entropy, discrimination rate, correct surviving hypothesis, held-out accuracy, random baseline discrimination rate, and selection wall/CPU time. Also report refusals and malformed predictions. The gate passes if all 16 substrate-selected queries are valid and discriminating, the `key` hypothesis survives and gets all held-out cases right in every worker, and the random baseline discrimination rate is no greater than its configured pool's actual discriminator fraction plus sampling variation. No speed or generalization claim follows from this small synthetic task.

## Scope boundary

This measures selecting a useful query among a supplied finite pool and resolving a supplied two-way hypothesis set. It does not measure discovering the hypotheses, choosing the target rule, extracting edit sites, materializing a graph rewrite, or learning a new primitive. A later structural gate must connect this query decision to substrate-composed proposals and an independently authored task family.

## Reproduction

Run `python3 evaluation/substrate_capability/thoughtexperiment_active_probe_selection_v1.py --lock`, then `--capture`, followed by `python3 evaluation/substrate_capability/analyze_thoughtexperiment_active_probe_selection_v1.py`. The source lock prevents captures after source drift.
