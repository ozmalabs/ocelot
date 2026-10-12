# Warm converse per-thread CPU diagnostic v1 — preregistration

**Status:** diagnostic; one host and three repeats per setting.

## Question

The prior locked caller-thread panel found that about 95% of target process CPU accrues outside the calling thread, while the Rayon pool cap does not change aggregate CPU or wall time. Sample Linux `/proc/<pid>/task/<tid>/schedstat` during the target call to identify whether sampled CPU is concentrated in a small number of persistent threads or spread across the threads created during the call.

## Method

Repeat the existing six-worker interleaved schedule (three default Rayon, three `RAYON_NUM_THREADS=1`) and reuse its exact held-out task, fresh-process, source-lock, and caller/process CPU measurements. A diagnostic Python sampler polls per-thread scheduler runtime every 2 ms only during the target `WorldAdapter.converse` call. Each thread instance is keyed by TID and kernel start-time to avoid confusing TID reuse. Report sampled per-thread runtime deltas, their sum, observed thread instances, sample count, and the locked aggregate process/caller CPU.

`schedstat` is cumulative scheduled runtime, sampled at finite intervals. Sampling can miss short-lived workers or CPU between observations, and the sampler adds some overhead. This captures thread-level CPU distribution, not native stack traces, task identity, or rule attribution. `comm` names are reported only as kernel thread labels and are not treated as subsystem identities.

## Gates

Require six unique fresh PIDs, exact existing semantic controls, stable source/native lock, expected schedule and active Rayon pool sizes, at least 10 samples per target interval, unique thread-instance identities, finite nonnegative per-thread deltas, and per-thread sampled runtime not exceeding aggregate target process CPU by more than 100 ms. Report per-arm medians and ranges. Do not infer absent CPU from sampling as zero, or attribute workers from thread names alone.
