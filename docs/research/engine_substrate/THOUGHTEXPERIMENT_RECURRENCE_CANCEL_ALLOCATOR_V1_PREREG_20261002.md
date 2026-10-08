# Thoughtexperiment recurrence cancellation allocator v1 preregistration

Extend the source-locked million-node recurrence cancellation wave with glibc allocator counters. Reuse the exact full-copy/shared-page, fanout-eight, cancel-four-before-closure workload and three fresh workers per backend from `THOUGHTEXPERIMENT_RECURRENCE_CANCEL_SCALE_V1`. Do not change task construction, cancellation selection, branch lifetime, or semantic gates.

Record `mallinfo2` in-use (`uordblks+hblkhd`) and free-arena bytes alongside PSS/RSS at fixture baseline, after half the repaired branches are released, after all survivor branches are evaluated/released, and after `malloc_trim(0)`. Also collect allocator values in the 10 ms sampler to estimate a sampled peak. Require six unique PIDs, stable current source/native fingerprints, all four survivors passing 64 exact-once checks and fixed point, and unchanged primary graph/rules/revision. `malloc_trim` may release free pages retained before this experiment; interpret only process-wide deltas and preserve raw values.

This is glibc/Linux process accounting for one synthetic recurrence workload. It does not attribute bytes to graph objects, cover Python or alternative allocator suballocation completely, or support a universal reclamation claim.
