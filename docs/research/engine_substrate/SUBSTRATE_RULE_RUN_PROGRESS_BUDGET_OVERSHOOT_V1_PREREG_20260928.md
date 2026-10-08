# Rule-run progress-budget overshoot v1

## Question

How tightly does `run_rules_report(max_steps=1)` bound rule progress when many independent dirty rules are eligible in one scheduler pass?

## Protocol

Three fresh workers run N=1/2/4/8/16/32/64 independent rules. Each rule has the same one-edge match and writes a distinct attribute on the same target. Settle once with `max_steps=1` and cycle detection enabled; capture report, graph, write count, matched rule effects, and native counters. Then call closure again with a large budget to verify fixed point and idempotence. The source inspection predicts `max_steps` is checked around scheduler passes; the experiment measures the actual batch overshoot.

## Gates

For each N, the first run must apply all N distinct writes exactly once, report `progress_steps=N`, `budget_overshoot=max(N-1,0)`, and return `progress_budget_reached` (including N=1 if the engine exits on the exhausted outer budget before a no-dirty probe). The second run must be fixed point with zero progress and zero graph writes. Integer native work counters must reproduce across workers after timing fields are excluded.

## Limits

This is a controlled single-pass family, not an adversarial worst-case scheduler load. It measures progress-step overshoot, not wall-time deadline compliance, cancellation, mid-effect interruption, or a general upper bound on batch size. A production guarantee would need a separately measured bound on dirty rules/bindings per pass or a finer-grained cancellation point.
