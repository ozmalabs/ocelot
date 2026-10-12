# ProblemShape all-transition eventization preregistration

**Status:** isolated candidate variant; production seeds/default behavior remain unchanged.

## Question

Can event-driven match inputs for `ps_decode`, `ps_recognize`, `ps_residual`, and `ps_mint`, plus the key-support index, reduce total ProblemShape rule work while preserving exact observation lifecycle behavior? `ps_redecode` deliberately retains its `observed_problem` scan because a codebook mint invalidates the held-basis decode of every prior observation; eventizing ordinary transitions must not omit that global invalidation.

## Variant

The host observation boundary emits one `pending_decode` event. `ps_decode` consumes it and emits one `decoded` event. Exactly one of `ps_recognize` or `ps_residual` consumes that event according to the existing residual condition; residual emits the existing mint-candidate event. `ps_mint` matches residual candidates and a key-index row. On codebook epoch change, `ps_redecode` globally visits old recognized/residual/minted observations, clears stale pending/decoded/residual events, and emits fresh pending-decode events. The key index counts every observation by key and is checked against an independent host grouping oracle.

## Workloads and gates

Run fresh processes for the locked N=2/4/8 recognition and recurrent-residual workloads from the population-scale sweep, compared with its dynamic baseline cells. Stop on the first semantic failure. Each cell must match initial and final observation statuses, mint count/key/mint-time support, codebook epoch, index support, exactly one index link per observation, and fixed point. Record per-rule candidate pairs/Term evaluations, host event/index maintenance, end-to-end observation wall/CPU time, RSS, and native counters. All six worker PIDs must differ.

## Interpretation limits

This remains a small fixed workload, a candidate-only variant, and an exploratory one-run-per-cell comparison. It does not establish production-scale performance, general complexity, natural-task benefit, persistent index recovery, concurrent ingestion, or rollback safety. Any semantic mismatch invalidates the cost interpretation; preserve raw failure evidence and stop rather than tuning the locked run.
