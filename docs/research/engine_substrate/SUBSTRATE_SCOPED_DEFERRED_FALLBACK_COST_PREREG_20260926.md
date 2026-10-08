# Preregistration: cost of global fallback after deferred scoped work

**Question.** How does the explicit `scoped settlement → pending check → global closure` policy cost compare with ordinary global closure for the measured TrackIdentity fixture, as the number of frame-owned percepts grows?

**Arms and sizes.** Two fresh-process arms: `full` performs ordinary global closure; `scoped_fallback` performs one scoped call at budget 1 and, after the required pending flag, global closure. Pair counts are 1/2/4/8/16 (2/4/8/16/32 frame owners), with 12 independent fresh workers per cell/arm. A fixed coordinator seed randomizes the execution order. Each worker constructs the same graph and rule family independently.

**Measures.** Separate graph/setup wall time, scoped call wall/CPU time, global closure wall/CPU time, total settlement wall/CPU time, end-to-end subprocess elapsed time, peak RSS, closure progress/passes, and exact identity projection. Report medians, ranges, paired fallback/full ratios, and size curves. The primary cost excludes process import/startup and fixture construction; both are separately recorded. No speed threshold is preregistered.

**Gates.** Every fallback arm must see pending deferred work and then reach a fixed point without a budget exit. Its identity projection must equal its paired ordinary-full arm exactly. All full arms must settle; all terminal probes must be zero-work. Inputs/build hashes and fresh PIDs must match the lock.

**Claim boundary.** This is a cost envelope for one synthetic TrackIdentity queue, one fixed rule, and at most 32 frame owners. It does not estimate natural prevalence, cover other deferred queues, or establish a general fallback cost law. The reported timing is host-specific and separates closure from setup/startup.

## Harness amendment v1.1

The initial capture completed 120 workers and showed exact full/fallback identity parity, but the independent analyzer incorrectly required the post-scoped global drain to report positive rule progress. In this engine, the queued TrackIdentity work drains at the beginning of global closure and need not count as a newly progressing rule application; the fallback call correctly reaches fixed point with zero rule progress. V1.1 gates positive rule progress on the ordinary full arm and on the preceding scoped writer call, while separately requiring fallback global closure to settle and produce exact identity parity. The initial raw capture and failed analysis are retained. The timing measures and matrix are unchanged; the amended lock precedes the v1.1 capture.
