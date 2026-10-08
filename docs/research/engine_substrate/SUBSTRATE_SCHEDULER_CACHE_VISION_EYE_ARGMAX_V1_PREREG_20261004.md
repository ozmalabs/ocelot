# Vision-eye Argmax scheduler-cache replay v1

**Question.** Does schema V6 preserve evaluator-generated Argmax state from the source-authored `vision_eye.ph0_wunit_winner` rule, and does restored native closure match live execution at the next quiescent boundary?

**Workload.** Load `vision_waves` and `vision_eye` through the normal boot/seed loader. Use a 16×16 retinal sheet, four WUnits, `propagate=0`, and the existing fixed 5×5 positive-control burst patch. Advance four phase-0 input steps; after each wave step, present the fixed patch, advance the Eye clock, and execute the installed native `run_rules` closure. The Python adapter supplies only the already-authored test fixture facts. No rule body or decision term is rewritten.

**Replay.** Require that `ph0_wunit_winner` is loaded, the native audit observes Argmax evaluation, and the evaluator-generated Argmax checkpoint map is nonempty. Force all rules dirty without changing graph facts, capture graph/rules/scheduler, restore two independent native stores, and compare checkpoint round-trip, aggregate/per-rule work, graph, and scheduler state after each executes the same closure.

**Source lock.** Hash the runner, protocol, native binary and source fingerprint, relevant seed manifests, boot/seed-loader and vision adapters, native checkpoint/evaluator/rewrite/persistence sources, and build metadata before and after execution.

**Limits.** Four units, one fixed patch, and four input steps are a narrow authored positive-control workload. The final closure is a replay-fidelity check, not a performance benchmark. This does not establish cache speedup, natural task prevalence, task transfer, or tractability at scale. If the current rule/cache invalidation policy leaves no Argmax entry at capture, record the failure and diagnose it before changing the workload.

**Execution.** Run `python3 evaluation/substrate_capability/scheduler_cache_vision_eye_argmax_v1.py --lock` once, then run the same file without arguments. Preserve captures; make a new version for any protocol or source change.
