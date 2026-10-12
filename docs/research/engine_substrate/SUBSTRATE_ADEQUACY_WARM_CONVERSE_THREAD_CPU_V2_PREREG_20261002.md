# Warm converse external per-thread CPU diagnostic v2 — preregistration

**Status:** diagnostic only; one host and three repetitions per Rayon setting.

## Question

The source-locked caller-thread panel finds roughly 95% of target process CPU outside the calling thread. An in-process `/proc` sampler failed its minimum-sample gate, consistent with the sampler being delayed by the target's GIL-held phases. This v2 samples from the supervising parent process, outside the target process, and asks which thread instances accrue CPU during the marked target call.

## Method

Run six fresh workers in the interleaved default / `RAYON_NUM_THREADS=1` schedule, reusing the exact workload, semantic checks, caller/process CPU timing, and source/runtime locks from the prior warm-converse CPU panel. The child appends monotonic-clock begin/end markers immediately around the target `WorldAdapter.converse`. While the child is active within that interval, the parent polls `/proc/<pid>/task/*/schedstat` every 2 ms and records each thread's scheduler runtime, kernel start time, and `comm`. Per-thread CPU is estimated from the maximum-minus-minimum observed scheduler runtime for each `(TID, starttime)` key inside the marked interval.

## Gates and limits

Require six unique child processes; source/runtime lock stability; expected schedule and active Rayon size; exact prediction, missing-evidence refusal, and zero codebook growth; at least 20 parent samples per target interval; unique per-thread identity keys; finite nonnegative CPU deltas; and sampled thread runtime no more than aggregate process CPU +100 ms. Report sampled CPU coverage relative to process CPU. Scheduling counters are sampled and may miss short-lived work between polls; kernel thread names do not identify code ownership. This probe can identify the distribution of scheduled CPU by thread instance, but cannot attribute the work to a rule or subsystem without a separate intervention or stack/work instrumentation.
