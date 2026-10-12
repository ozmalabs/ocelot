# Warm converse Rayon-pool diagnostic v1 — preregistration

**Status:** preregistered mechanism diagnostic; not a population performance estimate.

## Question

The prior six-worker diagnostic observed 25 process threads under both default and `RAYON_NUM_THREADS=1` settings, while the active pool size was not visible. A separate fresh-process check now confirms the read-only `rayon_current_num_threads()` binding reports 24 by default and 1 under the cap. Measure those values in the same warm-route process and locate the total OS-thread counts at adapter startup, after warm-up, and around the target call.

## Method

Run the existing warm-route worker function for parity/missing-evidence in six fresh processes using the fixed interleaved schedule default, one-thread, one-thread, default, default, one-thread. Reuse the task construction, timers, held-out oracle, and semantic checks from `substrate_adequacy_warm_converse_cost_v1.py`, but construct a fresh runtime lock from its `frozen()` function because the native binding/source has changed since the original capture. The existing worker checks this complete runtime lock before and after its task.

Wrap `WorldAdapter` only in the diagnostic child process. Record `/proc/self/task` count after adapter construction; after the warm `converse("hello")` but before querying Rayon; after querying the pool size; immediately before the target converse; and after target completion. Record `rayon_current_num_threads()` after warm-up and after the target call. The parent samples peak process thread count every 5 ms while draining child output through temporary files. The wrapper does not add rules or alter route arguments.

## Gates and reporting

Require six distinct PIDs, stable source/native fingerprints, exact fresh runtime lock in all workers, expected schedule, pool-size agreement with the requested Rayon setting, positive thread observations, zero codebook growth in every missing-evidence call, and exact held-out predictions. Report per-arm medians/ranges for target wall/CPU, pool size, phase-local OS-thread counts, and sampled peak count. Do not use a significance test or infer thread CPU attribution.

## Limits

The pool-size getter may initialize Rayon if the warm turn did not; its pre-query and post-query OS-thread observations expose that boundary. OS-thread counts do not identify pool ownership for non-Rayon threads, and process CPU remains aggregate. This is one task, one host, three workers per arm. Per-thread CPU and per-rule worker work remain open.
