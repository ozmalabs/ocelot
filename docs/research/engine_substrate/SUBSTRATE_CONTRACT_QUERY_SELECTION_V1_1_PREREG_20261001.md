# Contract query selection v1.1 — preregistration

V1 showed maximum-entropy selection and one-query identification on three very small hypothesis families, but the random baseline already identified the target in one query on 92.9% of its sampled trials (mean 1.071 queries). This addendum preserves those controls and adds a harder coded-hypothesis family to test whether selected queries have practical value when informative inputs are sparse.

## Added family

Eight Term hypotheses agree with the two initial observations at inputs 0 and 1. Each hypothesis returns its input except at three designated inputs (-5, -4, -3), where it emits the corresponding bit of its 3-bit hypothesis ID (0 or 10). The hidden target is `h5`; it is supplied only to the external labeler. The candidate grid remains -5 through 5, so only 3/9 unused candidate inputs are informative. A balanced query can split the surviving set evenly at each round and identify the target in three oracle calls. Compare against the same 2,000 random without-replacement input orders per worker.

## Panel

Eight fresh native-runtime workers: two repetitions each for the three original families and the added eight-hypothesis family. All v1 gates remain. Additional gate: on `coded_eight`, the selector must identify `h5` in exactly three queries, choosing one of the three encoded inputs per round; random-control mean query count and one-query success rate are analyzed independently. This measures a finite, caller-supplied hypothesis set and an authored sparse-query task, not general active learning.
