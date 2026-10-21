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

The profile integration gate passes 28 tests. This v1 verdict remains `NOT_ESTABLISHED`; later versions are separately frozen protocols and do not replace or rescore this report.

## Superseded v2 run

**Protocol:** `cognition_p5_mechanism_eval_v2`
**Frozen preregistration commit:** `4b194b3c5c6a58e5d8765de2a4986e57156b2bd1`
**Adapter implementation commit:** `2d322b6179b28cabcb3a927d3d96833dc3ecfd13`
**Registered draw:** indices 0–199, plus 100 executed controls per family.
**Report:** `evaluation/reports/cognition_p5_mechanism_eval_v2_4b194b3c_d0-200.json`
**Analysis:** `evaluation/reports/cognition_p5_mechanism_eval_v2_4b194b3c_d0-200_analysis.json`
The v2 analyzer printed PASS for each item, but a later audit found a comparator defect: the E4 one-step arm returned its outcome from a depth check instead of reading the shared transition graph. The v2 E4 gain is therefore `NOT_ESTABLISHED`, and the v2 all-item result is not used as final evidence. Its D6 controls also did not test rejection of a verifier receipt bound to a different source. The raw v2 report and analysis remain preserved; v3 reruns all families with those contracts exercised.

## Corrected v3 registered evaluation

**Protocol:** `cognition_p5_mechanism_eval_v3`
**Frozen preregistration commit:** `483e6a302c875ffd6b139ff5ed3c1095625e21c7`
**Runtime boundary correction:** `1feac532`
**Adapter implementation commit:** `0e001d60`
**Registered draw:** indices 0–199, plus 100 executed controls per family.
**Report:** `evaluation/reports/cognition_p5_mechanism_eval_v3_483e6a30_d0-200.json`
**Analysis:** `evaluation/reports/cognition_p5_mechanism_eval_v3_483e6a30_d0-200_analysis.json`
**Overall decision:** PASS for the registered mechanism fixtures.

All 4,800 arm executions (300 paired cases × two arms × eight families) returned structured outcomes. Coverage is complete, with zero nulls or arm errors. Oracles remain outside mechanism inputs. The report contains artifact hashes and limits; analysis includes Wilson 95% intervals, exact McNemar tests, Holm adjustment for F2/G2/E4, and paired 10,000-resample work intervals.

| Item | Result | Evidence |
|---|---|---|
| F1 shared attributed-state view | PASS | 200/200 exact conformance (Wilson 95%: 98.12–100%), 100/100 control conformance, no source loss or belief-to-truth leaks. |
| F2 recursive ToM | PASS | 200/200 query accuracy on vs 0/200 off; +100 pp; exact McNemar p=1.24e-60, Holm-adjusted p=3.73e-60; no actual-world overwrites; all 100 inaccessible controls unknown. |
| G2 evidence-preserving reappraisal | PASS | Supported selection 100/100 on vs 0/100 off; +100 pp; exact McNemar p=1.58e-30, Holm-adjusted p=1.58e-30; no unsupported acceptance or source edits. |
| G3 native action inhibition | PASS | Timely stops withheld 167/167; go emissions 66/66; no duplicate emissions or late-stop anomalies. The valid-go Wilson lower bound is 94.50% for this 66-case denominator; the registered point-rate criterion passes. |
| E3 SCM intervention | PASS | 225/225 identified models matched the oracle; 75/75 unsupported models returned unknown; no truth leakage or source mutation. |
| E4 planner | PASS | 200/200 observed planner solves vs 0/200 one-step on depth 2–8; +100 pp; exact McNemar p=1.24e-60, Holm-adjusted p=3.73e-60; 100/100 missing-edge controls rejected. Planner used 3.97 more expansions on average (paired bootstrap 95%: 3.695–4.25), so the registered solve gain does not show work savings. |
| A2 decomposition completion | PASS | 300/300 valid decisions across primary and stale/partial controls; no premature settlement. |
| D6 analog imagery | PASS | 200/200 exact verified primary transforms (Wilson 95%: 98.12–100%); 100/100 wrong-source receipts rejected; no grounding. Actual work (200 units) equaled shortest-angle work (200 units). |

These are fixture-level mechanism results, not evidence of general human-like cognition. F2 covers bounded accessible second-order paths; E3 uses explicit finite models; E4's comparator reads the same graph but only executes a direct goal edge, while tested primary graphs have depth 2–8; D6 uses sampled four-point shapes on a 4×4 lattice and an external request/source-bound verifier. G3 has 66 valid-go cases. Boot-time cost was not instrumented. P4's registered C5 failure and the inherited P3 NOT_ESTABLISHED gate remain unchanged.

Validation after the D6 receipt-boundary correction: 154 focused P5/profile tests passed; the broader named acceptance bundle passed 268 tests, with an additional 13-test SCM backdoor/provenance command; all seven targeted Rust `SCMIntervene` tests passed; both v3 self-checks and the 200-primary/100-control development panel passed before freeze. Seed-only orphan lint now reports no SCM entries after the separately recorded provenance-readout allowlist task. The full Rust library run reports 860 passed, 4 ignored and the one known P2 baseline failure (`graph_rule_patch_node_receives_durable_commit_receipt`); P2 had this and one additional failure, so no new Cargo failure was introduced. Registered report files remain uncommitted.

Reproduction commands:

```sh
git worktree add --detach /tmp/ocelot-p5-v3-repro 483e6a302c875ffd6b139ff5ed3c1095625e21c7
cd /tmp/ocelot-p5-v3-repro
COGNITION_PREREG_HASH=483e6a302c875ffd6b139ff5ed3c1095625e21c7 OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_eval_v3.py 483e6a302c875ffd6b139ff5ed3c1095625e21c7 0 200
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_analysis_v3.py evaluation/reports/cognition_p5_mechanism_eval_v3_483e6a30_d0-200.json
```
