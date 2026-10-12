# All-transition ProblemShape eventization paired timing preregistration

**Status:** exploratory repeated timing comparison.

## Question and arms

Repeat the N=8 recurrent-residual comparison between the locked dynamic baseline and the all-transition eventized candidate. There are three fresh-process pairs, with within-pair order randomized using Python RNG seed `20260926`. Each arm uses the same observation-to-receipt timing boundary; instrumentation snapshots happen after the interval. Baseline and candidate are distinct processes in every pair.

The candidate is the preregistered all-transition variant: pending-decode, decoded-outcome, and residual-mint-candidate events with a key support index; `ps_redecode` retains its codebook-wide observation scan and republishes pending-decode events.

## Locked inputs and gates

Lock this protocol, the baseline and candidate runners, baseline raw report, native binary, and all three workload seeds before worker launch. Every arm must pass its semantic/fixed-point checks. Require six distinct worker PIDs. Retain all runs; no outlier exclusion or replacement. Report each raw pair, candidate/baseline time ratio, median paired ratio, range, host index/event maintenance, and candidate-work counters.

## Limits

Three pairs on one N=8 authored workload are exploratory and cannot establish general speed or natural-task benefit. No changes to production rules/default behavior are authorized by this timing experiment.
