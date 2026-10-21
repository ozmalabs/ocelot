# Cognition build Phase 5 — Results

**Archived protocol:** `cognition_p5_heldout_v1`
**Frozen preregistration commit:** `0826089af64c38da3c34d3be2c96ca490364ffa3`  
**Registered draw:** indices 0–199, plus 100 generated adverse/control inputs per family.  
**Report:** `evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200.json`  
**Analysis:** `evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200_analysis.json`

The runner produced 200 primary paired cases and 100 adverse/control input records for each of F1, F2, G2, G3, E3, E4, A2 and D6. The arm adapters were not integrated at freeze time, so each of the 3,200 primary arm result slots is null. Control inputs were generated but were not run through arms. The analysis preserves these nulls and returns `NOT_ESTABLISHED` for every item and overall. This is a harness-completeness result only; it supplies no efficacy, safety-rate, or mechanism-performance evidence.

| Item | Mechanism commit(s) and supported fixture class | Decision and registered evidence |
|---|---|---|
| F1 shared attributed-state view | `35c78e1f`; explicit source rows retaining owner, holder, source identity and epoch | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No conformance or source-preservation rate measured. |
| F2 recursive ToM | `2f9f9c41`; access-gated, acyclic, depth-bounded attributed paths | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No query accuracy or actual-world isolation rate measured. |
| G2 evidence-preserving reappraisal | `b7225e93`; evidence-linked frames preserving source events and forced constraints | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No supported-appraisal gain measured. |
| G3 native action inhibition | `7a15326d`, `6ea3ab94`, `e3fff962`; explicit stop/go events and one-use native-sink authorization | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate mechanism gate passes; this draw measured no sink rates. |
| E3 SCM intervention | `3abbba6e`, `b47a60de`, `64118d55`, `432c902f`; finite, provenance-bearing models with bounded assignments | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. No oracle agreement or abstention rate measured. |
| E4 planner | `a3207840`, `9b028b91`; versioned transition graphs, bounded search and exact complete-path projection | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate planner/G3 gates pass; no solve gain measured. |
| A2 decomposition completion | `5fa6e603`; nonempty required-key coverage by verified same-epoch child work | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate runtime/consumer gate passes; no completion rate measured. |
| D6 analog imagery | `5e86399e`, `4719bcb9`; exact square-lattice quarter-turn trajectories | NOT_ESTABLISHED; 200 primary pairs, 100 control inputs, 400 null primary arm results. Separate imagery/ThoughtManifold gate passes; no held-out shape or work result measured. |

The preregistered criteria were not assessed because there are no arm observations. No null was scored as a failure or success, and no item was dropped. The generated report files remain uncommitted.

Reproduction commands:

```sh
COGNITION_PREREG_HASH=0826089af64c38da3c34d3be2c96ca490364ffa3 OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_heldout_v1.py 0826089af64c38da3c34d3be2c96ca490364ffa3 0 200
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_analysis_v1.py evaluation/reports/cognition_p5_heldout_v1_0826089a_d0-200.json
```

The profile integration gate passes 28 tests. This v1 verdict remains `NOT_ESTABLISHED`; the later v2 result below is a separately frozen protocol and does not replace or rescore this report.

## Adapter-backed v2 registered evaluation

**Protocol:** `cognition_p5_mechanism_eval_v2`
**Frozen preregistration commit:** `4b194b3c5c6a58e5d8765de2a4986e57156b2bd1`
**Adapter implementation commit:** `2d322b6179b28cabcb3a927d3d96833dc3ecfd13`
**Registered draw:** indices 0–199, plus 100 executed controls per family.
**Report:** `evaluation/reports/cognition_p5_mechanism_eval_v2_4b194b3c_d0-200.json`
**Analysis:** `evaluation/reports/cognition_p5_mechanism_eval_v2_4b194b3c_d0-200_analysis.json`
**Overall decision:** PASS for the registered mechanism fixtures.

The runner exercised the shipped graph/native mechanisms for all eight families. All 4,800 arm executions (300 paired cases × two arms × eight families) returned structured results. There were zero null arm results, adapter errors, or coverage gaps. The scoring oracle remained outside each mechanism input. The artifact SHA-256 manifest, limits and complete per-case outcomes are in the uncommitted report; the analyzer reports Wilson 95% intervals, exact McNemar tests, Holm-adjusted p values for F2/G2/E4, and paired 10,000-resample bootstrap intervals for work.

| Item | Registered result | Key evidence and limits |
|---|---|---|
| F1 shared attributed-state view | PASS | 200/200 exact conformance (Wilson 95%: 98.12–100%); 100/100 control conformance; no source loss or belief-to-truth leaks. |
| F2 recursive ToM | PASS | 200/200 query accuracy on vs 0/200 off; +100 pp; exact McNemar p=1.24e-60, Holm-adjusted p=3.73e-60; no actual-world overwrites. All 100 inaccessible controls returned unknown. |
| G2 evidence-preserving reappraisal | PASS | Supported-appraisal selection 100/100 on vs 0/100 off; +100 pp; exact McNemar p=1.58e-30, Holm-adjusted p=1.58e-30; no unsupported acceptance or source edits. |
| G3 native action inhibition | PASS | Timely stops withheld 167/167; valid go emissions 66/66; zero duplicate emissions and late-stop anomalies. The valid-go Wilson lower bound is 94.50% because this deterministic panel contains 66 go cases; the registered point-rate criterion passes. |
| E3 SCM intervention | PASS | 225/225 identified finite models matched the oracle; 75/75 nonidentified cases returned unknown; no truth leakage or live-model mutation. This is the tested finite confounder/collider/chain fixture class. |
| E4 planner | PASS | Observed success 200/200 for planner vs 0/200 for one-step on depth 2–8; +100 pp; exact McNemar p=1.24e-60, Holm-adjusted p=3.73e-60; all 100 missing-edge controls were rejected. Planner expansions were 4.97 higher on average than one-step (paired bootstrap 95%: 4.69–5.25), so this result establishes solve gain on the registered graph family, not work savings. |
| A2 decomposition completion | PASS | 300/300 valid completion decisions across primary and stale/partial controls; zero premature settlements. |
| D6 analog imagery | PASS | 300/300 exact externally verified transforms (Wilson 95%: 98.74–100%); zero grounded buffers. Actual transform work was 300 units and shortest-angle work was also 300, so no work advantage over the registered baseline was observed. |

These are fixture-level mechanism results, not evidence of general human-like cognition. F2 uses bounded accessible second-order paths; E3 uses explicit finite models; E4's one-step baseline is restricted to direct-goal transitions, while the planner receives depth-2–8 graphs; D6 uses sampled four-point shapes on a 4×4 lattice and an external request/source-bound verifier. G3's valid-go denominator is only 66. Boot-time cost was not instrumented. P4's registered C5 failure and the inherited P3 NOT_ESTABLISHED gate remain unchanged.

Validation after the D6 receipt-boundary correction: 153 focused P5/profile tests passed; both v2 development self-checks passed; the full 200-primary/100-control development panel passed before freeze. Registered report files remain uncommitted.

Reproduction commands:

```sh
COGNITION_PREREG_HASH=4b194b3c5c6a58e5d8765de2a4986e57156b2bd1 OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_eval_v2.py 4b194b3c5c6a58e5d8765de2a4986e57156b2bd1 0 200
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_analysis_v2.py evaluation/reports/cognition_p5_mechanism_eval_v2_4b194b3c_d0-200.json
```
