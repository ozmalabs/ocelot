# Synthesis acquisition/application economics preregistration

**Question.** For a small set of current string-PBE tasks, how does direct native `SynthEnumerate` acquisition cost compare with repeated use of the exact returned Term through native `Substrate._inner.evaluate`? This deliberately measures the direct-PBE term path; it does not measure reflected Program IR through `ProgEval` or the full graph-authored P4 route.

## Fixed workload

Use fixture tasks `pbe_001` (low observed search work), `pbe_010` (moderate composition), and `pbe_024` (higher search work / memorization trap). These IDs are selected from the existing 26-task fixture using the current recheck's declared-arm tested counts (59, 125,344, and 198,949 respectively); they are not sampled from a task population. Use the fixture's revealed examples, the uniform declared `PBE_OPS` and `PBE_CONSTS`, and the direct-PBE default budget (`max_size=15`, `max_candidates=0`, engine default candidate cap).

## Procedure

For each task, perform three independent acquisition calls on fresh `Substrate` instances. Record wall and process CPU time, candidate count, found status, and returned term. Require all three acquisitions to find the same canonical term and pass every held-out example. On the first acquisition's instance, warm the evaluator for 100 calls, then time batches of 1, 2, 5, 100, 1,000, and 10,000 term applications; cycle through that task's held-out inputs and verify every output. Also run same-process repeated acquire-and-use batches of 2 and 5 searches on a fresh substrate per batch, using the same task and budget; each search is followed by one verified held-out evaluation. The direct `SynthEnumerate` term is pure, so repeated calls within that batch use one substrate, matching the single-acquisition/application runtime state.

Report medians and raw repeats. Compare one acquisition plus N applications against N repeated acquire-and-use operations, and state the arithmetic break-even only for this repeated-identical-spec comparison. Exclude Python/native import and substrate construction from both acquisition and repeated-batch timers; disclose that call-boundary overhead remains in both measured operations. Do not compare against an LLM or infer general induction cost, task prevalence, or natural reuse rates.

## Gate and limits

The gate passes only if all three tasks are found consistently, canonical terms agree across acquisition repeats, and all repeated applications equal the held-out expected values. Failed acquisition or a semantic mismatch is reported as a failed cell without dropping the task. Three tasks and three acquisition repeats are a descriptive F3 pilot, not a population estimate or a full end-to-end synthesis-pipeline cost.
