# Warm converse thread-origin diagnostic v1 — preregistration

**Status:** source-locked mechanism diagnostic; three fresh workers per condition on one host.

## Question

The parent `/proc` sampler observes substantial CPU on non-caller threads, and a capped-Rayon exploratory probe sees no standard Python `threading.Thread.start` calls. Identify native pthread creation call sites during the exact target conversation. In particular, test whether per-call Rust JSON parsing threads and NumPy's OpenBLAS pool explain the observed thread activity.

## Conditions and method

Cross Rayon default versus `RAYON_NUM_THREADS=1` with OpenBLAS default (environment unset) versus `OPENBLAS_NUM_THREADS=1`: four cells, three fresh workers each, interleaved in the preregistered schedule. Reuse the same parity/missing-evidence task, exact held-out oracle, no-codebook-growth control, caller/process CPU instrumentation, and runtime locks from the warm-converse CPU panel.

A small LD_PRELOAD probe interposes `pthread_create`, records monotonic timestamp, creator TID, requested stack size, and symbolized native caller frames. Only events inside the child's explicit target begin/end markers are counted. The probe logs successful thread creations only. Its own source and compiled binary hash, compiler version, runner, analyzer, protocol, baseline runner/locks, and underlying runtime fingerprints are locked before capture. Because backtrace instrumentation adds work, timings from this panel are instrumentation-affected and are descriptive; counts and call-site identity are the primary outcomes.

## Gates

Require 12 unique child PIDs; source/probe binary stability; correct observed Rayon sizes; exact predictions and refusal/no-growth behavior; finite timing; valid target markers in order; every logged event within the target window; successful pthread creation records with finite timestamps, stack sizes, and frames; and independent call-site categorization of OpenBLAS, substrate JSON parsing, and other calls. Report all cells, including zeros. Do not infer CPU share or performance benefit from thread-creation counts alone.

## Limits

`pthread_create` interposition observes libraries using glibc pthread creation. It does not see raw `clone`, kernel threads, or threads created before the target interval. Native call frames identify the immediate creation path, not the later work performed by that thread. A separate intervention without the interposer is required to estimate runtime impact.
