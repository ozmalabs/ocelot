# Warm converse caller-thread CPU diagnostic v1 — preregistration

**Status:** preregistered diagnostic; not a population performance estimate.

## Question

The warm-route target consumes about 1.6 seconds of aggregate process CPU in about 0.11 seconds of wall time. A locked follow-up confirms Rayon is 24 threads by default and one thread under `RAYON_NUM_THREADS=1`, while 23 additional OS threads appear during the target route in either arm. Measure CPU on the calling thread separately from aggregate process CPU to determine whether the excess is actually consumed by other threads.

## Method

Run six fresh parity/missing-evidence workers using the existing locked warm-route workload, three each with default Rayon and `RAYON_NUM_THREADS=1`, in the same interleaved order as the Rayon-pool diagnostic. A diagnostic-only `WorldAdapter` subclass wraps the two `converse` calls and measures `time.thread_time_ns()` around the target call on its calling thread. The inherited worker records the target `time.process_time_ns()` and `perf_counter_ns()` around the same route and verifies the exact runtime lock. Compute `other-thread aggregate CPU = max(process CPU − caller-thread CPU, 0)`; this includes every process thread except the caller and does not identify individual workers.

Reuse the Rayon-pool diagnostic's wrapper so the capture also retains live Rayon pool sizes and phase-local process thread counts. Do not change task inputs, route ordering, rules, or evidence conditions. The runner uses temporary files for child stdout/stderr to avoid pipe back-pressure.

## Gates and reporting

Require six unique child PIDs, exact source/native locks, requested pool-size agreement (24 default / 1 capped), expected schedule, exact held-out predictions, zero codebook growth, finite timing/CPU splits, and `caller CPU + other-thread CPU = aggregate process CPU` within 10 ms per worker. Report per-arm medians/ranges for target wall, process CPU, caller-thread CPU, estimated other-thread CPU, CPU/wall, and observed thread counts. Three repetitions per arm are diagnostic only; no significance test or per-rule attribution is claimed.

## Limits

The caller-thread interval is measured by a Python wrapper nested inside the worker's process-time interval, so small boundary/timer differences are expected. The residual process CPU is an aggregate over other threads; threads may include runtimes, libraries, or native task workers. This does not identify which operation or rule used the CPU. One task and one host remain in scope.
