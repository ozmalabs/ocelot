# ProblemShape eventization cost attribution at N=32

**Status:** preregistered exploratory component-timing diagnostic.

## Question

How is elapsed ProblemShape observation time divided inside the all-transition event/index candidate across recognition-only and recurrent-residual sequences? How do its measured component totals compare descriptively with full-observation timing from the ordinary closure worker?

## Design

Run one fresh-process baseline and one fresh-process candidate worker at N=32 for each of the two existing authored mixes (`recognition`, `recurrent_residual`). Reverse arm order between mixes. Preserve complete worker JSON, including per-observation fields. Candidate components are observation construction, host index/event maintenance, native closure, and remaining measured time (receipts/other work and instrumentation boundary). Baseline provides whole-observation timing and work counters; the existing worker does not separately time baseline construction and closure.

This is a component diagnostic, not a repeated paired timing experiment. It is not powered to estimate an arm effect. Do not interpret component residuals as a causal difference or change the default path.

The lock pins this preregistration, runner, existing baseline/candidate workers, task sources and seeds, native extension/build manifest, and Cargo lock. Require current engine provenance before workers start.

## Interpretation limits

Only one fresh worker per arm/mix; timing is descriptive. The task streams are authored synthetic workloads. Baseline subcomponents are not instrumented at the same granularity, so only candidate components can be decomposed. This does not establish natural-task behavior, scaling, or a general CPU profile.
