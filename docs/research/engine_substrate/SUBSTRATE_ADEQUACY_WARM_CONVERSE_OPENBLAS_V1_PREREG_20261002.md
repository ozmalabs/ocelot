# Warm converse uninstrumented OpenBLAS cap v1 — preregistration

**Status:** source-locked intervention; three fresh processes per condition on one host.

## Question

The thread-origin diagnostic found 23 OpenBLAS pthread creations per target call with the OpenBLAS environment unset and none with `OPENBLAS_NUM_THREADS=1`. Under the interposer, the one-thread setting was associated with a large process-CPU reduction, but instrumentation may distort timing. Confirm whether the aggregate CPU and wall-time difference persists with no interposer loaded.

## Method

Repeat the exact warm parity/missing-evidence conversation route, held-out oracle, and caller/process CPU split from the prior source-locked diagnostic in six fresh workers. Keep Rayon default and remove `RAYON_NUM_THREADS`; compare OpenBLAS unset to `OPENBLAS_NUM_THREADS=1` in the interleaved schedule unset/1/1/unset/unset/1. Do not load the pthread interposer or any profiler. Preserve process CPU, caller-thread CPU, and wall time from the same target interval. Do not change rules, inputs, boot sequence, or semantic controls.

## Gates and reporting

Require six unique PIDs, stable source/runtime fingerprints, exact schedule and active Rayon size (24), exact held-out predictions, unchanged codebook and graph/rule state on the missing-evidence refusal, finite measurements, and caller plus other-thread CPU reconciliation within 10 ms. Report each arm's median and range for wall, process CPU, caller CPU, other-thread CPU, CPU/wall ratio, and reduction ratio. The OpenBLAS variable is the sole intervention. This is one task/host and does not generalize to other routes or establish a capability improvement by itself.
