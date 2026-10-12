# Phase-0 vision-eye WUnit scaling v1

**Question.** How do source-authored phase-0 rule closure time and measured engine work grow as the number of WUnits increases, with retinal size and all-to-all WUnit wiring fixed?

**Workload.** Use the `vision_waves` and `vision_eye` seeds, a 16×16 retinal sheet, deterministic diffuse WUnit wiring, the authored fixed 5×5 burst patch, and the unchanged `ph0_wunit_*` rules. Sweep WUnit counts 4/16/64/256, three fresh graph builds per size, and eight Eye-clock closure steps per build. Alternate ascending and descending size order by replicate. Time only `run_rules` closures with scale audit off. For each timed case, build an identical fresh graph and repeat with audit on to record candidate and Term work. Require exact final graph digest and per-step progress-vector parity between timed and audited twins.

**Recorded measures.** Per-closure wall time, aggregate closure time, candidate/Term/Argmax evaluations, graph node/edge counts, and Argmax cache occupancy. Source fingerprints and hashes of the runner, protocol, all seed manifests, adapters, engine sources, and build metadata are locked before execution and checked afterward.

**Limits.** One authored phase-0 family, one input pattern, and one host do not estimate natural task distribution or general capability. Audit counters are measured on a separate twin because instrumentation perturbs timing. There is no cache-disabled control, so this does not estimate causal Argmax speedup. The input facts and graph construction are not included in closure timing. Treat timings as a bounded scale profile, not an asymptotic theorem.

**Execution.** Run `python3 evaluation/substrate_capability/vision_eye_wunit_scale_v1.py --lock` once, then execute the runner without arguments. Preserve outputs; version the protocol and artifact paths for changes.
