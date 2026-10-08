# Warm converse thread-limit diagnostic v1 — preregistration

**Status:** preregistered diagnostic; not a population performance estimate.

## Question

Does setting `RAYON_NUM_THREADS=1` reduce the operating-system thread count or aggregate process CPU observed during the source-locked warm-route target call? The existing warm-route panel reported about 1.65–1.70 seconds process CPU in about 0.11 seconds wall time, but attributed neither work nor threads.

## Method

Run the existing `substrate_adequacy_warm_converse_cost_v1.py --worker parity missing_evidence <rep>` in six fresh child processes. Use three workers with the default Rayon configuration and three with `RAYON_NUM_THREADS=1`, in this fixed interleaved order: default, one-thread, one-thread, default, default, one-thread. Each worker independently enforces the existing source/native lock before its workload. The parent drains worker output to temporary files while sampling `/proc/<pid>/task` every 5 ms; capture the maximum observed OS-thread count. Do not retain the full graph dump emitted by the worker; preserve semantic fields, active source fingerprints, timers, PID, environment, and sampled count in the compact raw record.

## Recorded outcomes and gates

Record target wall time, aggregate process CPU time, CPU/wall ratio, warm-up wall time, maximum observed thread count, requested Rayon setting, child PID, reply, codebook delta, held-out predictions, and source/native fingerprints. Pass only if the six PIDs are distinct, every child completed successfully, the parent warm-route lock is unchanged, every child reports the exact locked active source fingerprints, all missing-evidence calls leave codebook shapes/epoch unchanged, and held-out outputs match the independent task oracle. Summarize each arm with medians and ranges. No significance test or general CPU attribution is claimed at three workers per arm.

## Limits

`RAYON_NUM_THREADS` controls Rayon’s global pool when honored by the loaded runtime. `/proc` sampling can miss short-lived threads. A stable thread count does not identify which threads consumed CPU, and process CPU remains aggregate work across threads. The fixture covers one task/control arm on one host; full per-thread CPU attribution and per-rule work instrumentation require a separate experiment.
