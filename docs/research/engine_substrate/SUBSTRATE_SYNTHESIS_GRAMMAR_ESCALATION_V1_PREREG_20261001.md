# Bounded grammar escalation v1 — preregistration

## Question

What does a caller-directed grammar escalation sequence accomplish when the search fails? Measure both a target recoverable by a registered extension and a target whose required primitive is absent from every registered grammar. Charge all attempted stages and distinguish complete bounded no-fit from timeout.

This evaluates grammar-conditioned synthesis and its gap signal. The caller supplies the ordered grammar ladder. The experiment does not test autonomous primitive discovery, and a no-fit through a term-size ceiling does not prove that no larger finite expression could match the observed rows.

## Tasks and frozen escalation ladder

Two analytic targets share four training examples and a size ceiling of 5:

- **Division recovery:** `x / 2`, training `x={0,2,4,6}`, held-out `x={-5,-3,-1,1,3,5,9}`. The required `Div` primitive first appears at stage 2.
- **Absent-primitive endpoint:** `x % 3`, training `x={0,1,2,3,4,5,6}`, held-out `x={8,9,10,11,12,14,17}`. `Mod` is absent from all three stages.

Stages, in order:

1. **Arithmetic:** `Plus, Times, Minus`.
2. **Numeric:** `Plus, Times, Minus, Div, Min, Max, Abs, Neg`.
3. **Full registered generator grammar:** the numeric stage plus `Gt, Lt, Eq, IfThenElse`.

Constants are `(0,1,2,-1)`, output-derived constants are disabled, `saturate_k=999999`, and each search has a 3-second internal timeout. Stop escalation after the first accepted fit. Run five fresh processes per task with randomized worker order (seed `20261001`); parent timeout is 10 seconds. Preserve every error, timeout, and incomplete stage.

## Measures and gates

Capture each stage's exact grammar, halt reason, fit, term, explored terms, distinct signatures, wall/CPU time; worker PID; source/native provenance; selected stage; and post-selection predictions on all held-out inputs. The independent analyzer verifies the exact randomized schedule, five repetitions per task, ten unique PIDs, current source/native lock, stage order and grammar contents, and finite cost capture. Division must complete stage 1 without a fit, then accept at stage 2 and transfer exactly to all held-outs. Modulo must complete all three stages without a fit, with no `Mod` operator present at any stage. A timeout is incomplete and cannot count as a successful gap report.

Candidate count is comparable only within this fixed grammar ladder. Report total charged synthesis wall and CPU across attempted stages, and stage-level cost; do not infer asymptotic or natural-task costs from this panel.

## Reproduction

Create `evaluation/substrate_capability/synthesis_grammar_escalation_v1_20261001_lock.json` from `python3 scripts/substrate_synthesis_grammar_escalation_v1.py --lock`. Run the runner once, then `python3 scripts/analyze_substrate_synthesis_grammar_escalation_v1.py`. The runner refuses stale locks and existing raw captures.
