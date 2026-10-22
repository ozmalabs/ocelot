# Cognition build — single linear execution plan

**Reconciled:** 2026-10-22 against clean HEAD `a43b08fc` (`Merge P4 and complete P5 cognition substrate work`), including Track I foundation commit `53da7321`.

This is the **sole execution order** for the cognition build and former Track I. Phases 0–5 are completed implementation/reporting cycles with the limits below. Continue with Phase 6, then execute Phases 7–15 in order. Former P6 and I0–I7 work is integrated here; there is no parallel Track I schedule. Original IDs are retained in the coverage table and task headings so existing code, tests and results remain traceable.

The [archived overarching roadmap](COGNITION_BUILD_PLAN_20261010_ARCHIVE.md), [former Phase 6 plan](COGNITION_BUILD_P6_NEW_FACULTIES_PLAN.md) and [former Track I specification](COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md) are historical design references. Their ordering and completion assumptions are superseded here. P0–P5 detailed plans and all preregistrations/results remain historical evidence; do not rewrite a failed or invalidated result to fit this schedule.

## 1. Ground rules

1. Read `CLAUDE.md`. Decisions, inference, process selection, adoption and mutable agent state belong in graph rules running in Rust. Python supplies world events, mechanical I/O, bounded ticking and external scoring. No Python solver, strategy, answer-conditioned hint or corrective action is allowed in the agent path.
2. Seeds with generators are changed through their generator and regenerated. New seeds declare Γ productions, dependencies, `self_load_only` and a disabled policy by default. Test dependency-only boot without permissive fixture grammars. Default and conversation profiles remain isolated; integration uses one explicit cognition-on dependency closure and one shared ThinkingBudget.
3. Computation is funded before execution. Every request has an operation/source/epoch identity, at most one debit and a terminal outcome. Bound search, graph growth and detached buffers; test interruption, restart and expiration. Budgets never relax evidence standards, conflict margins, confidence or hard host constraints.
4. For actions with external consequences preserve the engine's time-indexed future-manifold tube and retained/lost/escape residual shapes. Compare wait/refine/commit on the same declared tube, choose minimum sufficient intervention, and use goals for equal-intervention ties. Identity, width, time and information-loss changes are explicit transitions. Real receipts, imagined outcomes, predictions and other-agent reports remain distinct.
5. Inspect `git status --short runners/dsl runners/wasm` before Rust edits. The audited checkout was clean; future concurrent work must not be overwritten. Use an isolated worktree if needed. Build only with `scripts/engine_build.sh`, check disk first, and run Rust checks through `scripts/engine_cargo_test.sh`. Never copy the native library manually. Stage specific files only; no stash/reset. Do not commit generated reports, `papers/`, `tools/`, `evaluation/labels/` or `docs/experiments/qualia-visualization-development-plan.md`.
6. A finite effect fingerprint is evidence of agreement on declared probes. It establishes exact equivalence only for a representation with a complete separating probe set (for example a permutation applied to its identity state). Otherwise retain competing processes, seek distinguishing probes, and reverify on new states before adoption. A missing evaluator is unknown, never identity or zero cost.
7. Preserve all negative and limited results. Distinguish `IMPLEMENTED`, `MECHANISM_PASS`, `HELDOUT_PASS`, `FAIL`, `NOT_ESTABLISHED`, `NOT_RUN` and `UNSUPPORTED`. Completion of a reporting cycle does not establish a failed capability. A negative benefit hypothesis may close a phase if invariants pass and the next phase has an explicit supported fallback; an unsafe or structurally broken prerequisite must be repaired before advancing.
8. Qualia must be acquired through experience. Schema declarations, imported definitions and initialized coordinates cannot stand in for learned dimensions, significance or usable distinctions. Preserve the existing schema, grow it from recurring residuals and test what later behavior changes. Language instruction is one available input route; witnessed interaction and nonlinguistic experience must also be supported.

## 2. Verified starting state

This audit read committed code, tests, commit history and recorded results. **No implementation tests or held-out evaluations were rerun for this documentation change.** Commands and counts below are reported historical evidence, not a new gate run.

| Completed phase | Committed evidence | What is established / retained limit |
|---|---|---|
| 0 — baseline/guardrails | `d83fa140`; [baseline](COGNITION_BUILD_BASELINE.md) | Regression accounting, orphan lint and boot status groundwork |
| 1 — wiring | `5b52a38b`; [P1 results](COGNITION_BUILD_P1_RESULTS.md) | Bridge/replay/decomposition fixture mechanisms; subsequent P5 supplies candidate arbitration and parent completion |
| 2 — graded primitives | `1d5e63f9`; [P2 results](COGNITION_BUILD_P2_RESULTS.md) | SoftWeights, budget contract and aperture mechanisms; integer Pareto intentional; historical Cargo failures recorded |
| 3 — bounded thinking | `32143620`, freeze `eb34efb3`; [P3 results](COGNITION_BUILD_P3_RESULTS.md) | H1/H2/H3/H5 pass; H4 fails overall because Family-A first/repeat both take one step. Preserve that result |
| 4 — representation/recall/manifold | freeze `199583ca`; [P4 results](COGNITION_BUILD_P4_RESULTS.md) | D2/D3 parity, D1 regular sequences, D5 generated recall-work and E1/E2 supplied-model fixtures pass. C5: 92/200 on and off, zero incremental resolution gain. E1/E2 performed zero funded refinements. Live non-Shape signature producers, empirical VOI and external-stream model/refinement remain open |
| 5 — faculty depth | corrected freeze `483e6a30`; [P5 results](COGNITION_BUILD_P5_RESULTS.md) | Corrected v3: all eight registered mechanism-fixture criteria pass, 4,800 structured arm executions, no nulls/errors. v1 has null arms and remains NOT_ESTABLISHED; v2 E4 comparator is invalidated. Bounded ToM, explicit finite SCM, depth-2–8 planner and square-lattice quarter turns do not establish general open-world faculties. Planner gain used more expansions; boot cost was unmeasured |

### What `53da7321` actually adds

- Committed PMB specification, Loopover/D4/blicket generators, graph-install/tick harness, scorecard writer and [I0 results](COGNITION_BUILD_I0_RESULTS.md). The committed baseline scorecard says `NOT_RUN`: I0.3 is still open. It is not a measured zero-score baseline or a completed I0 gate.
- `process_algebra.rs` and Terms `ProcessCompose`, `ProcessInverse`, `ProcessApply`, `EffectSupport`, `EffectFingerprint`, `PermParity`, `MatDet`. Exact dispatch covers permutations, integer matrices, integer deltas, generator steps and sequences. Program, transition-table, capability, motor and family-program views remain opaque where they have no evaluator.
- Generated `process_schema`, `invention_operators`, `invention_round`, `invariant_miner`, `process_solving` seeds. Their existence/loadability does not establish I2's held-out invention gate. `tests/test_track_i_foundation.py` contains deterministic generators, scorecard and 3×3 twelve-distinct-schema fixtures.
- `process_solving` currently uses a hand-written generic greedy Hamming-distance strategy. It must remain a named comparator; it does not meet the original “agent discovers its own strategy” requirement. `harness.py::Agent` also initializes Track I policies on; it cannot silently serve as a Track-I-disabled baseline arm.
- `realised_by` is a node-valued source attribute, with an explicit owner `has_process_schema` edge. Preserve that implemented interface rather than assuming rule effects can add an edge to an arbitrary computed node. P3's RelaxLadder has not been migrated to ProcessSchema.

### Remaining linear schedule

| Phase | Deliverable | Former scope | Entry |
|---|---|---|---|
| 6 | Trustworthy PMB baseline and executable process views | I0 remainder, I1 completion | Audited P0–P5 + committed partial I |
| 7 | Experience-built qualia and perceptual numerosity | P4 source gaps, former P6.D7; explicit acquisition work | 6 |
| 8 | Learned world processes and informative experiments | I4.1–I4.3; P4 live refinement/C5 VOI gaps | 7 |
| 9 | Verified invention, invariants and irreversible effects | I2.1–I2.6 | 8 |
| 10 | Lifted processes, goal regression and discovered strategies | I3.1/I3.4, I5.1/I5.2, I2.7 gate | 9 |
| 11 | Representation invention and cross-domain transfer | I5.3/I5.4 | 10 |
| 12 | Observation, demonstration, instruction and explain/rebuild | former P6.F3, I4.4, I6.1–I6.3 | 11 |
| 13 | Staged sleep, reusable libraries and strategy recall | former P6.B2, I3.2/I3.3 | 12 |
| 14 | Laws, proof-carrying adoption and invention operators | I4.5, I7.1/I7.3 | 13 |
| 15 | Scaled portfolios, self-curriculum and repeated improvement | I7.2/I7.4/I7.5; final L1–L7 evidence | 14 |

These are delivery phases, not the old L0–L7 capability levels. Close a level only when its assembled evidence satisfies the criteria in §6. No later capability is presumed available to an earlier implementation: replay v0 and explicit held processes suffice before library learning; early targeted search does not require a future strategy library.

## 3. Task contract

Execute task IDs in the order printed within each phase, then its `.E1 → .E2 → .E3` integration/freeze/results tasks. Proceed to the next phase only after reviewing that results ledger. Every task below has tier, exact read references (symbol anchors remain authoritative after line movement), ≤3 touch groups (generator plus generated seed counts as one), pattern, steps, guard, acceptance and verification command. Acceptance names referring to new tests are planned assertions, not current passing tests. New paths are marked `new`; references to earlier-phase artifacts mean the artifacts delivered by that phase.

T1 defines unresolved semantics or evaluates evidence; T2 implements native behavior/integration; T3 copies a specified pattern or closes documentation. A T1 spec must freeze error/unknown behavior, ownership, epochs, resource limits and acceptance before implementation. No task can hide unlisted changes to Rust binders or adapters. If a new Term is necessary, split its engine change into separately recorded ≤3-file tasks: evaluator/variant; JSON/reflection; substitution/free-variable/cache metadata; native build/API acceptance. Reuse current Terms first; opaque process support generally needs an evaluator adapter rather than a fresh algebra.

All task `Verify cmd` entries below use the repository `.venv/bin/python`. They are commands for later implementation, not tests run by this planning update. Every implementation task also requires the applicable §5 gate; spec tasks finish when their written contract and acceptance definitions are frozen, without claiming tests for future behavior already pass. Rust subtasks may be an atomic compile integration series, but no downstream seed consumer becomes active before the complete Rust integration passes.

## 4. Detailed linear phases

## Phase 6 — Measured foundation and executable process views

**Entry:** P4/P5 reported results and partial foundation commit `53da7321`. **Status:** planned.

Finish I0 and I1 without rebuilding landed algebra. Preserve opaque native views until their effect evaluation is supported. Baseline must omit Track I policies; the current `Agent` constructor does not. Keep the greedy solver as an explicitly named hand-written comparator.

**Registered evidence:** 200 paired tasks each for Loopover, D4 and finite mechanism worlds, 100 malformed/stale/view controls. Report baseline measurements even when weak; do not require a nonzero baseline. View conformance and pure evaluator equivalence must be 100% for declared supported inputs, with zero live mutation. A family with no executable baseline is NOT_RUN and blocks its comparative claim, not unrelated conformance.

### P6.01 — Freeze the committed foundation gap and PMB arm contracts

- **ID:** P6.01
- **Tier:** T1
- **Goal:** Freeze the committed foundation gap and PMB arm contracts.
- **Read first:** `docs/research/engine_substrate/COGNITION_BUILD_I0_RESULTS.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py::Agent`; `runners/dsl/src/process_algebra.rs:1-34`; `scripts/gen_process_schema_seed.py::view_rules`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Pattern to copy:** I0 source-view decision and P5 actual-adapter audit.
- **Steps:** 1. Enumerate all native view kinds, source references, pre/post semantics, budgets and exact/approximate/opaque behavior. 2. Define baseline/invention arms, measured status vocabulary and held-out probe isolation. 3. State where a finite fingerprint is complete and where collision witnesses are required.
- **Guard:** documentation only.
- **Acceptance:** explicit matrix covers Program, CapabilityProgram, TransitionHypothesis, DimensionGenerator, EmbodiedMotorProgram, FamilyProgram; no opaque None enters dedup as identity.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_track_i_foundation.py -q -p no:cacheprovider`.
- **Non-goals:** declaring I0–I2 complete from loadable seeds.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.02 — Provide real baseline and experimental world adapters

- **ID:** P6.02
- **Tier:** T2
- **Goal:** Provide real baseline and experimental world adapters.
- **Read first:** `evaluation/process_mastery/harness.py::Agent`; `evaluation/process_mastery/generators.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`.
- **Touch:** `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; new `tests/test_pmb_execution_contract.py`.
- **Pattern to copy:** P5 native sink/observed outcome adapter and stable scorecard writer.
- **Steps:** 1. Parameterize seed/policy selection so baseline truly omits Track I. 2. Install world affordances as grammar-admissible data, ingest requested actions into the same world and record observed results; remove reliance on unchecked installation for new runtime edges. 3. Make not-run, unsupported, timeout and failed trial distinguishable; fail fast on missing adapters.
- **Guard:** explicit evaluation arms only.
- **Acceptance:** `test_baseline_has_no_track_i`, `test_arms_share_world_and_budget`, `test_actions_are_graph_selected`, `test_missing_adapter_not_zero_score`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_execution_contract.py tests/test_track_i_foundation.py -q -p no:cacheprovider`.
- **Non-goals:** a Python strategy or world truth injected as schema params.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.03 — Evaluate program and transition process effects natively

- **ID:** P6.03
- **Tier:** T2
- **Goal:** Evaluate program and transition process effects natively.
- **Read first:** `runners/dsl/src/process_algebra.rs::apply`; `runners/dsl/src/term.rs::ProcessApply`; `seeds/cognition_planner.json`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`.
- **Touch:** `runners/dsl/src/process_algebra.rs`; `runners/dsl/src/term.rs`; new `tests/test_process_native_views.py`.
- **Pattern to copy:** current ProcessApply dispatch and existing native program/transition evaluation.
- **Steps:** 1. Reuse native bounded program evaluation and supported explicit transition model execution. 2. Carry source/model epoch and precondition failure; detached evaluation cannot emit an external action. 3. Test agreement with each original native evaluator and unsupported programs.
- **Guard:** ProcessSchema view policy opt-in.
- **Acceptance:** `test_program_view_matches_native`, `test_transition_view_matches_native`, `test_process_precondition_unknown`, `test_apply_has_no_external_effect`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_native_views.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** inventing an inverse for irreversible code; copying native reasoning into Python.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.04 — Evaluate capability motor and family process views within supported models

- **ID:** P6.04
- **Tier:** T2
- **Goal:** Evaluate capability motor and family process views within supported models.
- **Read first:** `runners/dsl/src/process_algebra.rs`; `runners/dsl/src/motor_compose.rs`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`; `tests/test_process_native_views.py`.
- **Touch:** `runners/dsl/src/process_algebra.rs`; `runners/dsl/src/term.rs`; `tests/test_process_native_views.py`.
- **Pattern to copy:** P5 source-bound finite-model evaluation and exact full-path projection.
- **Steps:** 1. Delegate to existing native capability and supported motor/family model evaluation under an explicit detached mode. 2. Keep unsupported or ungrounded effects opaque with a reason. 3. Distinguish model-predicted effects from observed physical effects and test stale sources.
- **Guard:** view policy only; native emission prohibited.
- **Acceptance:** `test_capability_view_matches_native`, `test_motor_family_model_view`, `test_unsupported_model_stays_opaque`, `test_source_epoch_invalidates_view`; documented support matrix reconciled.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_native_views.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming exact physical effects from a learned motor model.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.05 — Complete source views and collision-safe effect indexing

- **ID:** P6.05
- **Tier:** T2
- **Goal:** Complete source views and collision-safe effect indexing.
- **Read first:** `scripts/gen_process_schema_seed.py::view_rules`; `scripts/gen_process_schema_seed.py::merge_newcomer_rule`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`; `tests/test_track_i_foundation.py`.
- **Touch:** `scripts/gen_process_schema_seed.py` + `seeds/process_schema.json`; `tests/test_process_native_views.py`; `tests/test_track_i_foundation.py`.
- **Pattern to copy:** existing schema owner/source views and P4 epoch-sensitive recall.
- **Steps:** 1. Wire six-form views and supported evaluators without migrating authoritative objects. 2. Include owner/frame/model/probe epochs in equivalence identity; retain indistinguishable finite-probe hypotheses until separating evidence. 3. Test source update/delete, cheapest verified equivalent retention and cross-owner isolation.
- **Guard:** ProcessSchemaPolicy enabled only in explicit profile.
- **Acceptance:** `test_six_forms_have_source_views`, `test_probe_collision_retains_alternatives`, `test_complete_perm_probe_dedups`, `test_stale_view_recomputed`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_native_views.py tests/test_track_i_foundation.py -q -p no:cacheprovider`.
- **Non-goals:** automatic merge from approximate matching; forcing every representation into exact inverse semantics.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.


### P6.06 — Register the existing synthesis task family without changing its solver

- **ID:** P6.06
- **Tier:** T2
- **Goal:** Register the existing synthesis task family without changing its solver.
- **Read first:** `tests/test_program_synthesis_migrated.py`; `tests/test_mbpp_baseline_migrated.py`; `tests/fixtures/mbpp/provenance.json`; `evaluation/process_mastery/harness.py`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Touch:** new `evaluation/process_mastery/program_adapter.py`; `evaluation/process_mastery/harness.py`; new `tests/test_pmb_program_adapter.py`.
- **Pattern to copy:** existing native synthesis request/accept path and committed MBPP provenance.
- **Steps:** 1. Reuse the existing specification/runner boundary to install held-out program tasks; do not implement a new synthesis policy. 2. Capture actual emitted candidate code/program, external test outcome, compute and unsupported statuses for matched baseline/Track I arms. 3. Freeze dataset provenance and split IDs and demonstrate no test solutions enter the agent graph.
- **Guard:** explicit PMB family-e registration only.
- **Acceptance:** `test_existing_synthesis_outcome_preserved`, `test_hidden_tests_not_agent_input`, `test_program_arm_not_dummy_baseline`, `test_dataset_split_provenance_recorded`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_program_adapter.py tests/test_program_synthesis_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming a new synthesis gain from exposing an adapter; using benchmark solutions as held processes.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P6.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add the completed process view closure to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p6_profile_chain`, `test_p6_default_isolation`, `test_p6_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_execution_contract.py tests/test_process_native_views.py tests/test_track_i_foundation.py tests/test_cognition_profile_integration.py tests/test_pmb_program_adapter.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.E2 — Freeze a runnable preregistered evaluation

- **ID:** P6.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p6_v1.py`; new `evaluation/process_mastery/analyze_linear_p6_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P6_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_execution_contract.py tests/test_process_native_views.py tests/test_track_i_foundation.py tests/test_pmb_program_adapter.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P6.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P6.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P6_PREREG.md`; `evaluation/process_mastery/linear_p6_v1.py`; `evaluation/process_mastery/analyze_linear_p6_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P6_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_execution_contract.py tests/test_process_native_views.py tests/test_track_i_foundation.py tests/test_pmb_program_adapter.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 7 — Qualia acquired from episodes and perceptual numerosity

**Entry:** Phase 6 executable supported views and actual baseline arms. **Status:** planned.

Explicitly close the developmental gap discussed in this session. Existing P4 schemas, numeric signatures and receipt-backed recall are infrastructure. Acquire distinctions and significance from episodes and preserve contradictory outcomes; do not import a table of qualia or ask fixtures to supply the target dimension name. Include the former P6.D7 task here.

**Registered evidence:** 200 acquired-distinction episodes in each of two independently coded worlds (tool/contact and social request/repair), plus 100 label-shuffled, exposure-only and orthogonal controls per family. Compare experience-built space against frozen space with identical experience and compute. Proposed primary: ≥20 percentage-point transfer gain on a later task requiring the distinction, zero source/grounding leaks. Separately 200 small-set scenes and 200 comparisons per ratio bin 1.1/1.25/1.5/2; ≥95% exact small-set accuracy, ≥75% at ratios≥1.5, equal-ratio scale difference≤10 points. These are proposed criteria, frozen before draws, not claims about human perception.

### P7.01 — Specify episode-grounded dimension and significance acquisition

- **ID:** P7.01
- **Tier:** T1
- **Goal:** Specify episode-grounded dimension and significance acquisition.
- **Read first:** `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`; `domains/qualia_schema.py:1-60`; `tests/test_qualia_dimension_compensation_migrated.py`; `seeds/qualia_shape_mint.json`; `seeds/process_schema.json`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md`; new `tests/test_qualia_acquisition.py`.
- **Pattern to copy:** existing recurring-residual mint lifecycle and dimension-versus-aperture controls.
- **Steps:** 1. Define experienced event/action/outcome histories, source ownership, temporal identity and nonlinguistic feature access. 2. Specify when finer grain suffices versus a new dimension, recurrence evidence, verification on future outcomes and retiring a failed distinction. 3. Define context-sensitive significance from witnessed consequences and standing/live separation; labels can attach later but cannot supply the discriminating answer.
- **Guard:** new QualiaAcquisitionPolicy disabled.
- **Acceptance:** planned `test_no_target_axis_in_inputs`, `test_finer_grain_cannot_fake_missing_dimension`, `test_acquired_axis_has_episode_witnesses`, `test_negative_evidence_can_revise`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_dimension_compensation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** equating a schema declaration or hard-coded valence with acquired qualia.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.02 — Ingest episode evidence and produce non-Shape native signatures

- **ID:** P7.02
- **Tier:** T2
- **Goal:** Ingest episode evidence and produce non-Shape native signatures.
- **Read first:** `docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md`; `scripts/gen_cognition_signature_seed.py`; `scripts/gen_qualia_shape_mint_seed.py`; `tests/test_cognition_signature_migrated.py`.
- **Touch:** new `scripts/gen_experience_signature_seed.py` + `seeds/experience_signature.json`; new `tests/test_experience_signature.py`.
- **Pattern to copy:** P4 source/version-bound signature and receipt contracts.
- **Steps:** 1. Project actual event streams into existing typed signature families without target labels. 2. Bind signatures and verifier receipts to their exact source/model/frame epochs; retain full episode references. 3. Test unsupported modalities, missing coordinates, stale receipts and owner boundaries.
- **Guard:** ExperienceSignaturePolicy disabled by default.
- **Acceptance:** `test_episode_produces_signature`, `test_wrong_episode_receipt_rejected`, `test_live_overlay_not_standing_commitment`, `test_no_experience_no_signature`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_experience_signature.py tests/test_cognition_signature_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** changing lexical parsing or fabricating experiences to fill absent coordinates.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.03 — Grow and revise qualia dimensions from recurring residuals

- **ID:** P7.03
- **Tier:** T2
- **Goal:** Grow and revise qualia dimensions from recurring residuals.
- **Read first:** `docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md`; `scripts/gen_experience_signature_seed.py`; `seeds/meta_shape_growth.json`; `tests/test_qualia_acquisition.py`.
- **Touch:** new `scripts/gen_qualia_acquisition_seed.py` + `seeds/qualia_acquisition.json`; `tests/test_qualia_acquisition.py`.
- **Pattern to copy:** native recognize/transform/infer/mint ladder; use its typed numeric/relational contracts.
- **Steps:** 1. Detect recurrent consequences unexplained by existing dimensions and propose a distinction from witnessed features. 2. Reverify on fresh episodes before it enters standing recognition; bind significance changes to outcomes without scalar truth substitution. 3. Re-decode earlier episodes, retain conflicting evidence and expire unsupported candidates.
- **Guard:** QualiaAcquisitionPolicy; funded probes and bounded candidates.
- **Acceptance:** `test_residual_mints_once`, `test_new_axis_predicts_unseen_consequence`, `test_redecode_uses_acquired_axis`, `test_unrelated_episodes_not_merged`, `test_revision_preserves_old_witnesses`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_acquisition.py tests/test_experience_signature.py -q -p no:cacheprovider`.
- **Non-goals:** a human-authored axis per evaluation class; confidence taken as verification.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.04 — Freeze perceptual numerosity inputs and uncertainty semantics

- **ID:** P7.04
- **Tier:** T1
- **Goal:** Freeze perceptual numerosity inputs and uncertainty semantics.
- **Read first:** `domains/number_world.py:32-111`; `tests/test_number_world_migrated.py`; `runners/dsl/src/term.rs::RatioInduce`; `docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_NUMEROSITY_CONTRACT.md`; new `tests/test_numerosity_migrated.py`.
- **Pattern to copy:** number-world grounding and Observer grain projection.
- **Steps:** 1. Separate ≤4 individuated slots from larger-set aggregate perception and scoring-only exact counts. 2. Specify sensory aggregation, confounds, uncertainty, ratio comparison and abstention. 3. Bound decision work separately from O(n) scene ingestion; prohibit a hand-programmed Weber answer curve.
- **Guard:** NumerosityPolicy planned disabled.
- **Acceptance:** planned `test_small_sets_exact`, `test_hidden_count_not_visible`, `test_area_density_conflict_abstains`, `test_equal_ratio_scale_contract`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_number_world_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** an exact count followed by log advertised as an acquired approximate number system.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.05 — Implement and expose perceptual numerosity through graph rules

- **ID:** P7.05
- **Tier:** T2
- **Goal:** Implement and expose perceptual numerosity through graph rules.
- **Read first:** `docs/research/engine_substrate/COGNITION_NUMEROSITY_CONTRACT.md`; `tests/test_numerosity_migrated.py`; `domains/number_world.py`; `seeds/observer_aperture.json`.
- **Touch:** new `scripts/gen_numerosity_seed.py` + `seeds/numerosity.json`; `domains/number_world.py`; `tests/test_numerosity_migrated.py`.
- **Pattern to copy:** existing numeric Terms and mechanical world input/read-off.
- **Steps:** 1. Add explicit percept input mode, native bounded exact route and aggregate ratio route. 2. Preserve existing symbolic NumberWorld behavior. 3. Instrument actual evidence and work; route unresolved magnitudes through acquired significance without hidden counts.
- **Guard:** NumerosityPolicy; explicit percept mode.
- **Acceptance:** `test_percept_mode_no_count_label`, `test_small_set_bounded_decision_work`, `test_symbolic_mode_parity`, all P7.04 cases.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_numerosity_migrated.py tests/test_number_world_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** changing the old symbolic task to make a new perceptual claim pass.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P7.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add experience signatures, acquisition and numerosity to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p7_profile_chain`, `test_p7_default_isolation`, `test_p7_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_acquisition.py tests/test_experience_signature.py tests/test_numerosity_migrated.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.E2 — Freeze a runnable preregistered evaluation

- **ID:** P7.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p7_v1.py`; new `evaluation/process_mastery/analyze_linear_p7_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P7_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_acquisition.py tests/test_experience_signature.py tests/test_numerosity_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P7.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P7.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P7_PREREG.md`; `evaluation/process_mastery/linear_p7_v1.py`; `evaluation/process_mastery/analyze_linear_p7_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P7_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_acquisition.py tests/test_experience_signature.py tests/test_numerosity_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 8 — Learned process models and informative experimentation

**Entry:** Phase 7 episode evidence and acquired distinction interfaces. **Status:** planned.

Complete I4.1–I4.3 using observed state/action/consequence traces. A simple explicit held-model path is available from P5; this phase must construct and revise models through learning. Separate hidden-state invention from merely indexing more named states. C5’s old zero-gain result remains; evaluate whether acquired evidence and experiment choice add a new advantage.

**Registered evidence:** 200 held-out finite mechanism worlds and 200 temporal/latent worlds, 100 missing/ambiguous controls each. Compare learned portfolio/VOI, passive equal-exposure and fixed-probe arms with equal interaction caps. Primary: ≥20-point identification gain or ≥25% fewer interventions at no more than 2-point accuracy loss; latent re-induction must predict held-out continuations. Include 100 worlds requiring actual funded refinement: zero unsupported certifications and nonzero verified refinement completions. Human intervention comparison remains unavailable until protocol-matched.

### P8.01 — Specify transition induction and hypothesis evidence

- **ID:** P8.01
- **Tier:** T1
- **Goal:** Specify transition induction and hypothesis evidence.
- **Read first:** `seeds/generative_world_model.json`; `docs/research/engine_substrate/COGNITION_SCM_CONTRACT.md`; `evaluation/process_mastery/generators.py::blicket_task`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_MODEL_LEARNING_CONTRACT.md`; new `tests/test_process_induction.py`.
- **Pattern to copy:** P5 explicit finite SCM and GWM observed-outcome comparison.
- **Steps:** 1. Freeze object/parameter binding, pre/post effect inference, negative evidence and model epoch. 2. Keep all currently consistent hypotheses, distinguish empirical distributions from exact laws and bound portfolio size. 3. Define missing evidence and identifiability failure without selecting a favored explanation arbitrarily.
- **Guard:** new ModelLearningPolicy disabled.
- **Acceptance:** planned `test_effect_learned_from_trace`, `test_unseen_object_binding`, `test_counterexample_revises_model`, `test_indistinguishable_hypotheses_retained`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_generative_world_model_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** assuming supplied transition tables constitute learned causal structure.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P8.02 — Induce lifted transition schemas from real episode traces

- **ID:** P8.02
- **Tier:** T2
- **Goal:** Induce lifted transition schemas from real episode traces.
- **Read first:** `docs/research/engine_substrate/COGNITION_MODEL_LEARNING_CONTRACT.md`; `scripts/gen_process_schema_seed.py`; `tests/test_process_induction.py`; `seeds/experience_signature.json`.
- **Touch:** new `scripts/gen_process_induction_seed.py` + `seeds/process_induction.json`; `tests/test_process_induction.py`.
- **Pattern to copy:** existing structural unification Terms and epoch-gated source views.
- **Steps:** 1. Fit supported pre/post bindings using native Terms and witnessed episodes. 2. Mint transition views with supporting/counterexample records and version changes. 3. Revalidate old plans/recall on model updates and test untouched actual observations.
- **Guard:** ModelLearningPolicy; request-funded inference.
- **Acceptance:** P8.01 assertions plus `test_old_plan_invalidated`, `test_no_trace_no_model`, `test_model_prediction_not_observation`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_induction.py tests/test_process_native_views.py -q -p no:cacheprovider`.
- **Non-goals:** unbounded arbitrary program induction or a Python rule learner.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P8.03 — Infer latent state from persistent prediction residuals

- **ID:** P8.03
- **Tier:** T2
- **Goal:** Infer latent state from persistent prediction residuals.
- **Read first:** `seeds/temporal_escalation.json`; `seeds/time_axis.json`; `docs/research/engine_substrate/COGNITION_MODEL_LEARNING_CONTRACT.md`; `tests/test_temporal_escalation_migrated.py`.
- **Touch:** new `scripts/gen_latent_process_seed.py` + `seeds/latent_process.json`; new `tests/test_latent_process.py`.
- **Pattern to copy:** P4 regular frame event ingestion and native DimInfer/TimeInfer.
- **Steps:** 1. Link residual history to real observation windows; invoke funded existing inference after recurrence. 2. Add a verified latent to the model and re-induce on observed data. 3. Require new continuation evidence before accepting improvement; preserve refusal of unsupported irregular streams.
- **Guard:** LatentProcessPolicy disabled; shared budget.
- **Acceptance:** `test_latent_explains_persistent_error`, `test_future_continuation_verifies`, `test_shuffled_residual_no_latent`, `test_irregular_stream_still_refused`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_latent_process.py tests/test_temporal_escalation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** silently filling missing frames; inventing a hidden variable solely to fit every training sample.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P8.04 — Choose discriminating experiments and fund real refinement

- **ID:** P8.04
- **Tier:** T2
- **Goal:** Choose discriminating experiments and fund real refinement.
- **Read first:** `docs/research/engine_substrate/COGNITION_MODEL_LEARNING_CONTRACT.md`; `seeds/cognition_manifold.json`; `seeds/thinking_budget.json`; `seeds/remote_causal.json`; `tests/test_cognition_manifold_migrated.py`.
- **Touch:** new `scripts/gen_experiment_design_seed.py` + `seeds/experiment_design.json`; new `tests/test_experiment_design.py`.
- **Pattern to copy:** SCM do-contrast, portfolio predictions and P4 funding leases.
- **Steps:** 1. Project hypotheses into allowed interventions and compute information gain over declared uncertainty; unknown probabilities remain unknown. 2. Choose sufficient evidence-gathering actions through the manifold boundary and fund once. 3. Consume actual outcomes, update the portfolio and trigger a real projection/refinement revision when justified.
- **Guard:** ExperimentDesignPolicy disabled; host veto intact.
- **Acceptance:** `test_probe_distinguishes_hypotheses`, `test_no_information_no_voi_claim`, `test_actual_outcome_updates_portfolio`, `test_funded_refinement_changes_audit`, `test_exhaustion_not_retained`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_experiment_design.py tests/test_cognition_manifold_migrated.py tests/test_thinking_budget_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** synthetic nonzero refinement counters without actual recomputation; generic threshold relaxation.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P8.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P8.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add learned model, latent and experiment-design seeds to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p8_profile_chain`, `test_p8_default_isolation`, `test_p8_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_induction.py tests/test_latent_process.py tests/test_experiment_design.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P8.E2 — Freeze a runnable preregistered evaluation

- **ID:** P8.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p8_v1.py`; new `evaluation/process_mastery/analyze_linear_p8_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P8_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_induction.py tests/test_latent_process.py tests/test_experiment_design.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P8.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P8.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P8_PREREG.md`; `evaluation/process_mastery/linear_p8_v1.py`; `evaluation/process_mastery/analyze_linear_p8_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P8_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_induction.py tests/test_latent_process.py tests/test_experiment_design.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 9 — Verified invention and invariant walls

**Entry:** Phase 8 supported learned/held process effects and intervention model. **Status:** planned.

Finish committed I2 seed behavior with honest effect semantics. Exact inverses, repair-to-equivalence, and distributional outcomes are different contracts. Invention and wall explanations can be tested here without claiming the no-hand-written-strategy solve gate; that gate follows Phase 10.

**Registered evidence:** 200 novel exact effect goals and 200 irreversible/stochastic goals, plus 100 alias/invalid-inverse controls; equal-budget operators on/off and existing held-only arms. Exact adoption has zero verification failures. Primary ≥20-point verified effect coverage gain; all noninvertible cases return no exact inverse, repair/distribution records carry their limits. Reproduce 3-cycle/dihedral closure counts as conformance, with solver results reserved for Phase 10.

### P9.01 — Specify exact repair and distributional invention semantics

- **ID:** P9.01
- **Tier:** T1
- **Goal:** Specify exact repair and distributional invention semantics.
- **Read first:** `runners/dsl/src/process_algebra.rs:1-34`; `scripts/gen_invention_operators_seed.py`; `scripts/gen_invention_round_seed.py`; `scripts/gen_invariant_miner_seed.py`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_INVENTION_CONTRACT.md`; new `tests/test_process_invention.py`.
- **Pattern to copy:** current inverse/composition operators and complete permutation probe distinction.
- **Steps:** 1. Audit operator templates, composition order, root bounds and budget contract. 2. Freeze exact identity versus probe-equivalent repair and stochastic output distributions. 3. Define precision/support, invariant evidence, novelty and fresh verification with no alias-based adoption.
- **Guard:** existing invention policies remain opt-in.
- **Acceptance:** planned `test_compose_order`, `test_noninvertible_no_inverse`, `test_repair_not_exact_inverse`, `test_finite_probe_collision_not_law`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_track_i_foundation.py -q -p no:cacheprovider`.
- **Non-goals:** using successful repair on finite probes as a universal inverse theorem.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P9.02 — Complete funded exact invention and conjugation closure

- **ID:** P9.02
- **Tier:** T2
- **Goal:** Complete funded exact invention and conjugation closure.
- **Read first:** `docs/research/engine_substrate/COGNITION_INVENTION_CONTRACT.md`; `scripts/gen_invention_round_seed.py`; `scripts/gen_invention_operators_seed.py`; `tests/test_process_invention.py`.
- **Touch:** `scripts/gen_invention_round_seed.py` + `seeds/invention_round.json`; `scripts/gen_invention_operators_seed.py` + `seeds/invention_operators.json`; `tests/test_process_invention.py`.
- **Pattern to copy:** existing pairwise operator/round rules and graph budget approvals.
- **Steps:** 1. Exercise inverse, compose, conjugate, commutator, bounded powers and bounded library-root search. 2. Dedup only under the declared exact equivalence, retain cheapest verified representative and record operator provenance. 3. Bound rounds/pairs/setup closure and prove restart cannot double-spend.
- **Guard:** InventionPolicy explicit enablement.
- **Acceptance:** `test_all_six_operators_execute`, `test_dihedral_closure`, `test_precise_conjugation_coverage`, `test_round_budget_once`, `test_restart_bound`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_invention.py tests/test_track_i_foundation.py -q -p no:cacheprovider`.
- **Non-goals:** assuming generated operator data already executes correctly.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P9.03 — Explain invariant walls and choose verified breakers

- **ID:** P9.03
- **Tier:** T2
- **Goal:** Explain invariant walls and choose verified breakers.
- **Read first:** `scripts/gen_invariant_miner_seed.py`; `docs/research/engine_substrate/COGNITION_INVENTION_CONTRACT.md`; `evaluation/process_mastery/generators.py::parity`; `tests/test_process_invention.py`.
- **Touch:** `scripts/gen_invariant_miner_seed.py` + `seeds/invariant_miner.json`; new `tests/test_invariant_walls.py`.
- **Pattern to copy:** existing parity/MatDet primitives and wall-explanation records.
- **Steps:** 1. Evaluate parity, conserved counts/sums and supported determinant invariants over full families. 2. Separate witnessed invariants from proven ones. 3. Attach a target mismatch explanation and propose the least sufficient held breaker through verification.
- **Guard:** InvariantMinerPolicy; bounded invariant library.
- **Acceptance:** `test_even_tools_cannot_reach_odd_target`, `test_breaker_changes_required_invariant`, `test_partial_probe_not_proof`, `test_no_breaker_honest_impasse`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_invariant_walls.py tests/test_process_invention.py -q -p no:cacheprovider`.
- **Non-goals:** hard-coding a puzzle-specific parity-fix policy in Python.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P9.04 — Evaluate irreversible repair and stochastic effects natively

- **ID:** P9.04
- **Tier:** T2
- **Goal:** Evaluate irreversible repair and stochastic effects natively.
- **Read first:** `docs/research/engine_substrate/COGNITION_INVENTION_CONTRACT.md`; `runners/dsl/src/process_algebra.rs`; `scripts/gen_invention_round_seed.py`; `seeds/scm_reasoning.json`.
- **Touch:** `runners/dsl/src/process_algebra.rs`; `scripts/gen_invention_round_seed.py` + `seeds/invention_round.json`; new `tests/test_process_repair.py`.
- **Pattern to copy:** P8 supported finite models and detached effect evaluation.
- **Steps:** 1. Evaluate repairs against declared equivalent-state criteria without external emission. 2. Use explicit finite distributions for supported stochastic models; retain probabilities/support and unknown mass. 3. Verify on fresh states and reject insufficient evidence or exceeded simulation bounds.
- **Guard:** InventionPolicy repair mode disabled by default.
- **Acceptance:** `test_repair_candidate_reverified`, `test_no_repair_does_not_invent_inverse`, `test_distribution_support_retained`, `test_model_epoch_invalidates_repair`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_repair.py tests/test_process_invention.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** pretending noisy effects have an exact fingerprint; unrestricted probabilistic program inference.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P9.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P9.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add completed invention/invariant closure to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p9_profile_chain`, `test_p9_default_isolation`, `test_p9_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_invention.py tests/test_invariant_walls.py tests/test_process_repair.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P9.E2 — Freeze a runnable preregistered evaluation

- **ID:** P9.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p9_v1.py`; new `evaluation/process_mastery/analyze_linear_p9_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P9_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_invention.py tests/test_invariant_walls.py tests/test_process_repair.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P9.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P9.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P9_PREREG.md`; `evaluation/process_mastery/linear_p9_v1.py`; `evaluation/process_mastery/analyze_linear_p9_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P9_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_invention.py tests/test_invariant_walls.py tests/test_process_repair.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 10 — Lifting goal regression and agent-discovered strategies

**Entry:** Phase 9 verified process library and invariant evidence. **Status:** planned.

Remove the scheduling cycle in the old roadmap: I3.4 needs I5.1, so goal regression and targeted invention are delivered before the no-hand-written-strategy I2.7 gate. The old greedy Hamming solver stays a comparator and cannot supply the new strategy.

**Registered evidence:** 200 held-out scrambles each for Loopover 3×3/4×4 (including odd walls) and 200 tool-goal tasks, 100 misleading-precondition controls. Compare discovered-strategy, committed greedy and primitive-search arms with equal world access and declared compute. Primary ≥20-point observed solve gain; no answer/placement strategy injected. Lifted schemas must verify on unseen indices and sizes 5–6. Human-baseline L2/L5 remains unavailable without matched humans.

### P10.01 — Specify parametric lifting and goal interfaces

- **ID:** P10.01
- **Tier:** T1
- **Goal:** Specify parametric lifting and goal interfaces.
- **Read first:** `runners/dsl/src/term.rs::AntiUnifyWitness`; `docs/research/engine_substrate/COGNITION_PLANNER_CONTRACT.md`; `scripts/gen_process_solving_seed.py:1-25`; `docs/research/engine_substrate/COGNITION_INVENTION_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; new `tests/test_goal_invention.py`.
- **Pattern to copy:** AntiUnifyWitness/Substitute and P5 frontier/path contracts.
- **Steps:** 1. Define parameters, variable capture, constraints, pre/post regression and typed missing-effect interface specs. 2. State goal/frontier identity, depth/node limits and admissible future work. 3. Specify strategy as a graph-held process whose discovery uses ordinary operations, not a provided piece-placement recipe.
- **Guard:** new GoalInventionPolicy disabled.
- **Acceptance:** planned `test_lift_preserves_bindings`, `test_unseen_size_preconditions`, `test_goal_gap_mints_interface`, `test_no_handwritten_strategy_input`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_track_i_foundation.py -q -p no:cacheprovider`.
- **Non-goals:** lifting equal-looking syntax without verified effect conditions.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P10.02 — Lift process families and verify unseen instances

- **ID:** P10.02
- **Tier:** T2
- **Goal:** Lift process families and verify unseen instances.
- **Read first:** `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; `runners/dsl/src/term.rs::AntiUnifyWitness`; `scripts/gen_process_schema_seed.py`; `tests/test_goal_invention.py`.
- **Touch:** new `scripts/gen_process_lifting_seed.py` + `seeds/process_lifting.json`; new `tests/test_process_lifting.py`.
- **Pattern to copy:** existing structural anti-unify/witness/substitution and schema source views.
- **Steps:** 1. Extract parameterized common expressions with retained witness/residue. 2. Generate new instances in graph data and check preconditions and actual native effects. 3. Dedup lifted schemas without merging different domains or unsafe index ranges.
- **Guard:** ProcessLiftingPolicy disabled.
- **Acceptance:** `test_parameterized_commutator_lifts`, `test_unseen_size_verified`, `test_bad_binding_rejected`, `test_lifted_provenance_retained`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_lifting.py tests/test_process_invention.py -q -p no:cacheprovider`.
- **Non-goals:** claiming unseen-size generalization from training-size enumeration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P10.03 — Regress goals into targeted invention and a later thinking rung

- **ID:** P10.03
- **Tier:** T2
- **Goal:** Regress goals into targeted invention and a later thinking rung.
- **Read first:** `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; `scripts/gen_invention_round_seed.py`; `seeds/cognition_planner.json`; `seeds/extended_thinking.json`; `seeds/capability_synthesis_bridge.json`.
- **Touch:** new `scripts/gen_goal_invention_seed.py` + `seeds/goal_invention.json`; `scripts/gen_invention_round_seed.py` + `seeds/invention_round.json`; `tests/test_goal_invention.py`.
- **Pattern to copy:** P5 bounded goal search and P3 one-approved-request-per-step.
- **Steps:** 1. Regress unmet effects into subgoal/interface records and select verified covering schemas. 2. Target operator search toward missing effects under existing bounds; no covering process yields an honest needs_tool/synthesis request. 3. Add an explicit ProcessSchema adapter as a later P3 rung, restoring temporary policy and requiring current observation verification.
- **Guard:** GoalInventionPolicy plus separately enabled targeted-invention rung.
- **Acceptance:** `test_missing_effect_drives_invention`, `test_goal_plan_uses_new_process`, `test_targeted_rung_funded`, `test_denied_rung_restores`, `test_new_program_never_skips_verifier`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_goal_invention.py tests/test_extended_thinking_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** migrating RelaxLadder wholesale or restoring the invalid P1 assumption that generic collapse calls code synthesis.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P10.04 — Discover and execute strategies without the probe solver

- **ID:** P10.04
- **Tier:** T2
- **Goal:** Discover and execute strategies without the probe solver.
- **Read first:** `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; `scripts/gen_process_solving_seed.py`; `scripts/gen_goal_invention_seed.py`; `tests/test_invariant_walls.py`.
- **Touch:** new `scripts/gen_strategy_discovery_seed.py` + `seeds/strategy_discovery.json`; new `tests/test_strategy_discovery.py`.
- **Pattern to copy:** goal regression over fixed-cell invariants and verified process composition.
- **Steps:** 1. Search for reusable subgoal order/constraint-preservation strategies from actual task traces. 2. Store and execute found strategies through native process views. 3. Instrument agent choices to demonstrate that no authored piece-placement routine or oracle trace enters the experimental arm; retain explicit greedy comparator.
- **Guard:** StrategyDiscoveryPolicy disabled.
- **Acceptance:** `test_agent_finds_constraint_preserving_strategy`, `test_delayed_progress_not_greedy_trap`, `test_odd_wall_uses_verified_breaker`, `test_trace_contains_only_graph_decisions`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_strategy_discovery.py tests/test_goal_invention.py tests/test_invariant_walls.py -q -p no:cacheprovider`.
- **Non-goals:** requiring old Python-probe solve counts regardless of new held-out distribution; relabeling authored greedy search as discovered strategy.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.


### P10.05 — Extend permutation evaluation to cube and sliding worlds

- **ID:** P10.05
- **Tier:** T2
- **Goal:** Extend permutation evaluation to cube and sliding worlds.
- **Read first:** `evaluation/process_mastery/generators.py`; `evaluation/process_mastery/harness.py`; `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Touch:** `evaluation/process_mastery/generators.py`; new `evaluation/process_mastery/puzzle_worlds.py`; new `tests/test_pmb_puzzle_worlds.py`.
- **Pattern to copy:** existing Loopover world/affordance installation and external exact outcome scoring.
- **Steps:** 1. Add deterministic 2×2×2 cube and sliding-puzzle worlds with legal moves, reachability and external solved-state oracles. 2. Feed only initial state, goal and primitive affordances to the same graph-discovered strategy pipeline; no human macros. 3. Register 200 tasks each plus 100 illegal/unreachable controls as additional P10 evidence panels; preserve separate family verdicts and do not substitute a trivial scramble distribution.
- **Guard:** PMB family-a world selection; same discovered-strategy policy.
- **Acceptance:** `test_cube_moves_and_inverses`, `test_sliding_moves_legal`, `test_unreachable_control_distinguished`, `test_no_solution_path_ingested`, `test_seeded_world_reproducible`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_puzzle_worlds.py tests/test_strategy_discovery.py -q -p no:cacheprovider`.
- **Non-goals:** a Python puzzle solver, hand-authored placement strategy or unmatched human-record comparison.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P10.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P10.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add lifting, targeted invention and strategy discovery to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p10_profile_chain`, `test_p10_default_isolation`, `test_p10_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_goal_invention.py tests/test_process_lifting.py tests/test_strategy_discovery.py tests/test_cognition_profile_integration.py tests/test_pmb_puzzle_worlds.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P10.E2 — Freeze a runnable preregistered evaluation

- **ID:** P10.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p10_v1.py`; new `evaluation/process_mastery/analyze_linear_p10_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P10_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_goal_invention.py tests/test_process_lifting.py tests/test_strategy_discovery.py tests/test_pmb_puzzle_worlds.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P10.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P10.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P10_PREREG.md`; `evaluation/process_mastery/linear_p10_v1.py`; `evaluation/process_mastery/analyze_linear_p10_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P10_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_goal_invention.py tests/test_process_lifting.py tests/test_strategy_discovery.py tests/test_pmb_puzzle_worlds.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 11 — Representation invention and cross-domain transfer

**Entry:** Phase 10 lifted schemas and goal-directed invention; Phase 7 acquired qualia. **Status:** planned.

Use acquired distinctions and current observer/frame contracts to propose and test representations. P4 D5 proved candidate-work savings on two generated families, not general transfer; P4 C5 measured no resolution advantage. This phase tests new domain pairs and evidence-backed frame choice.

**Registered evidence:** 200 source→target pairs per direction across two new process-domain pairings, 100 nonconjugate/wrong-frame controls each. Compare source-exposed, fresh and mismatched-source arms at equal exposure/compute. Primary ≥25% fewer target interventions or exact checks with solve loss≤2 points; zero wrong-frame acceptance. Representation adoption must reduce total held-out description length including mapping/decoder cost, not merely training fit.

### P11.01 — Specify representation proposals and transferable frame maps

- **ID:** P11.01
- **Tier:** T1
- **Goal:** Specify representation proposals and transferable frame maps.
- **Read first:** `docs/research/engine_substrate/COGNITION_APERTURE_ADAPTER_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; `seeds/qualia_acquisition.json`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; new `tests/test_representation_search.py`.
- **Pattern to copy:** typed Observer frames and structural witness/substitution.
- **Steps:** 1. Specify basis/grain/aperture/latent proposals, information retained/lost and frame identity transitions. 2. Define full description cost including map, model, exceptions and decoder on a fixed training split. 3. Freeze forward/reverse map requirements; noninvertible abstraction cannot be used as an exact conjugation.
- **Guard:** RepresentationSearchPolicy disabled.
- **Acceptance:** planned `test_decoder_cost_included`, `test_forced_frame_not_relaxed`, `test_noninvertible_map_not_conjugation`, `test_holdout_not_selection_input`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_aperture_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** choosing the most flattering frame by suppressing residuals.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P11.02 — Search and verify alternative representations

- **ID:** P11.02
- **Tier:** T2
- **Goal:** Search and verify alternative representations.
- **Read first:** `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; `scripts/gen_cognition_aperture_seed.py`; `seeds/experiment_design.json`; `tests/test_representation_search.py`.
- **Touch:** new `scripts/gen_representation_search_seed.py` + `seeds/representation_search.json`; `tests/test_representation_search.py`.
- **Pattern to copy:** P8 funded evidence probes and chosen-frame restoration.
- **Steps:** 1. Generate bounded candidate descriptions from held/acquired transforms. 2. Compare full model+mapping+residual cost on development evidence and require sufficient discriminating evidence. 3. Adopt explicit frame transitions and invalidate incompatible caches; keep rejected witnesses.
- **Guard:** RepresentationSearchPolicy; shared funded request contract.
- **Acceptance:** `test_verified_representation_shortens_total_description`, `test_mapping_cost_blocks_spurious_gain`, `test_epoch_change_invalidates_recall`, `test_failed_search_restores`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_representation_search.py tests/test_qualia_acquisition.py -q -p no:cacheprovider`.
- **Non-goals:** requiring every domain to share one untyped metric.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P11.03 — Find cross-domain process maps and verify transferred effects

- **ID:** P11.03
- **Tier:** T2
- **Goal:** Find cross-domain process maps and verify transferred effects.
- **Read first:** `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; `seeds/similarity_recall.json`; `seeds/process_lifting.json`; `runners/dsl/src/term.rs::AntiUnifyWitness`.
- **Touch:** new `scripts/gen_process_transfer_seed.py` + `seeds/process_transfer.json`; new `tests/test_process_transfer.py`.
- **Pattern to copy:** P4 candidate-only RecallNearest and graph structural mapping.
- **Steps:** 1. Recall compatible candidate schemas and search structural frame maps. 2. Compose the declared A↔B map with the source process using the frozen composition order. 3. Verify target effects on fresh target states before use; failed maps fall back to local invention.
- **Guard:** ProcessTransferPolicy disabled.
- **Acceptance:** `test_unseen_target_process_transfers`, `test_wrong_frame_rejected`, `test_nonconjugate_control_abstains`, `test_transferred_effect_reverified`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_transfer.py tests/test_representation_search.py -q -p no:cacheprovider`.
- **Non-goals:** transferring solely from name similarity; counting target-trained solutions as source transfer.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.


### P11.04 — Register grid-transfer evidence with source and split provenance

- **ID:** P11.04
- **Tier:** T1
- **Goal:** Register grid-transfer evidence with source and split provenance.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/generators.py::d4_task`; `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; `tests/test_process_transfer.py`.
- **Touch:** new `evaluation/process_mastery/grid_transfer_adapter.py`; new `tests/test_pmb_grid_transfer.py`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Pattern to copy:** existing D4 task generation and P4 candidate-only transfer scoring.
- **Steps:** 1. Audit available ARC/LS20 ingestion/evaluation interfaces and record the exact supported source, license and split without importing its solutions. 2. Expose the same held transformations/world access to fresh/source/mismatched arms and record actual output. 3. Freeze family-c/g panel membership before P11.E2; unavailable external task interfaces remain explicitly unsupported and require a separate adapter task, not a silent D4-only generalization claim.
- **Guard:** evaluation adapter only.
- **Acceptance:** `test_grid_split_provenance`, `test_target_solution_hidden`, `test_comparator_has_same_affordances`, `test_unavailable_source_reported`; result scope names D4 versus actual external grid tasks.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_grid_transfer.py tests/test_process_transfer.py -q -p no:cacheprovider`.
- **Non-goals:** claiming ARC/LS20 coverage solely from generated D4 tasks; researching or asserting a human score without matched protocol.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P11.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P11.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add representation search and process transfer to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p11_profile_chain`, `test_p11_default_isolation`, `test_p11_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_representation_search.py tests/test_process_transfer.py tests/test_cognition_profile_integration.py tests/test_pmb_grid_transfer.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P11.E2 — Freeze a runnable preregistered evaluation

- **ID:** P11.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p11_v1.py`; new `evaluation/process_mastery/analyze_linear_p11_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P11_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_representation_search.py tests/test_process_transfer.py tests/test_pmb_grid_transfer.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P11.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P11.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P11_PREREG.md`; `evaluation/process_mastery/linear_p11_v1.py`; `evaluation/process_mastery/analyze_linear_p11_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P11_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_representation_search.py tests/test_process_transfer.py tests/test_pmb_grid_transfer.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 12 — Social acquisition observation and explain/rebuild

**Entry:** Phase 11 compatible process/representation interfaces and P5 actual action authorization. **Status:** planned.

Integrate former P6.F3 and I6 rather than duplicating demonstration pipelines. Observation of others pursuing ordinary goals is a first-class input route; no caregiver or teacher framing is required. Explicit instruction remains another route. Understanding is tested by reconstruction from an explanation with no access to the original schema.

**Registered evidence:** 200 tasks per observation-only, demonstration, instruction and reward-only family with equal declared evidence opportunities; 100 shuffled/missing/body-mismatch controls each. Primary social own-trial gain≥20 points versus no social input, zero unverified adoption or false own grounding. Explain/rebuild uses 200 fresh process instances with ≥95% held-out effect agreement and controls that remove original IDs/expressions; compare explanation length and exposure across arms.

### P12.01 — Specify social evidence and demonstration-to-process interfaces

- **ID:** P12.01
- **Tier:** T1
- **Goal:** Specify social evidence and demonstration-to-process interfaces.
- **Read first:** `seeds/tom_unified_view.json`; `docs/research/engine_substrate/COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`; `tests/test_instruction_understanding_migrated.py`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_SOCIAL_ACQUISITION_CONTRACT.md`; new `tests/test_imitation_migrated.py`.
- **Pattern to copy:** P5 attributed-state source records and source-bound verifier receipts.
- **Steps:** 1. Define observed actor/action/intent candidates, access, event order and body/frame maps. 2. Separate incidental witnessed interaction, directed demonstration and instruction; incomplete observations remain partial. 3. Specify own-model verification, adoption safety and real own-trial grounding; demonstration can evidence another actor’s outcome without pretending it is the learner’s receipt.
- **Guard:** SocialAcquisitionPolicy disabled.
- **Acceptance:** planned `test_observed_actor_not_self`, `test_missing_step_unknown`, `test_body_mismatch_blocks_trial`, `test_no_directed_teaching_required`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_instruction_understanding_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** inferring absent actions or guaranteed intentions from the desired task answer.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P12.02 — Construct verify and lift demonstrated candidate processes

- **ID:** P12.02
- **Tier:** T2
- **Goal:** Construct verify and lift demonstrated candidate processes.
- **Read first:** `docs/research/engine_substrate/COGNITION_SOCIAL_ACQUISITION_CONTRACT.md`; `seeds/program_synthesis.json`; `seeds/process_lifting.json`; `seeds/adoption_safety.json`; `tests/test_imitation_migrated.py`.
- **Touch:** new `scripts/gen_imitation_seed.py` + `seeds/imitation.json`; `tests/test_imitation_migrated.py`.
- **Pattern to copy:** native candidate→verify→accept and P10 lifting.
- **Steps:** 1. Build candidate programs from ordered observed actions using declared action maps in rules. 2. Run own detached rollout, validate constraints and authorize only through P5 sink/manifold boundary. 3. Lift verified instances; distinguish model-verified adoption from observed own execution.
- **Guard:** ImitationPolicy disabled; existing host/adoption gates mandatory.
- **Acceptance:** `test_demo_candidate_graph_resident`, `test_failed_own_rollout_rejects`, `test_trial_stop_respected`, `test_grounding_requires_own_receipt`, `test_demo_lifts_to_unseen_binding`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py tests/test_response_inhibition_migrated.py tests/test_process_lifting.py -q -p no:cacheprovider`.
- **Non-goals:** a Python trace compiler or hidden imitation-specific solver.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P12.03 — Acquire process candidates from witnessed interaction and instruction

- **ID:** P12.03
- **Tier:** T2
- **Goal:** Acquire process candidates from witnessed interaction and instruction.
- **Read first:** `docs/research/engine_substrate/COGNITION_SOCIAL_ACQUISITION_CONTRACT.md`; `seeds/instruction_understanding.json`; `seeds/qualia_acquisition.json`; `seeds/imitation.json`.
- **Touch:** new `scripts/gen_social_process_seed.py` + `seeds/social_process.json`; new `tests/test_social_process.py`.
- **Pattern to copy:** instruction-understanding graph outputs and P7 episode acquisition.
- **Steps:** 1. Translate existing instruction events into process constraints and candidate schemas. 2. Learn action/request/repair associations from incidental witnessed episodes through the same evidence path. 3. Verify resulting process effects with ordinary learner models and reject unsupported interpretations.
- **Guard:** SocialProcessPolicy disabled.
- **Acceptance:** `test_instruction_to_schema_verified`, `test_incidental_request_repair_acquired`, `test_no_teacher_marker_needed`, `test_wrong_interpretation_counterexample_revises`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_social_process.py tests/test_imitation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** treating text descriptions as already grounded process effects; requiring labels for the target qualia axis.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P12.04 — Explain processes and rebuild them in an isolated receiver

- **ID:** P12.04
- **Tier:** T2
- **Goal:** Explain processes and rebuild them in an isolated receiver.
- **Read first:** `docs/research/engine_substrate/COGNITION_SOCIAL_ACQUISITION_CONTRACT.md`; `seeds/lang_production.json`; `seeds/social_process.json`; `evaluation/process_mastery/harness.py`.
- **Touch:** new `scripts/gen_process_explanation_seed.py` + `seeds/process_explanation.json`; new `tests/test_process_explain_rebuild.py`.
- **Pattern to copy:** production self-monitor round trip and separate native world instances.
- **Steps:** 1. Produce a structured linguistic explanation through the production stack, declaring supported vocabulary. 2. Give a fresh isolated receiver only the explanation plus the shared primitive vocabulary; deny source IDs, AST, fingerprints and original library. 3. Reconstruct by ordinary acquisition and compare effects on fresh probes; test a second agent teaching and learning.
- **Guard:** ProcessExplanationPolicy disabled.
- **Acceptance:** `test_rebuild_from_explanation_only`, `test_source_ast_not_visible`, `test_ambiguous_explanation_abstains`, `test_second_agent_rebuilds_novel_process`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_explain_rebuild.py tests/test_social_process.py -q -p no:cacheprovider`.
- **Non-goals:** serializing an executable AST under the label explanation; claiming unrestricted natural-language understanding.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P12.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P12.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add imitation, social process and explanation seeds to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p12_profile_chain`, `test_p12_default_isolation`, `test_p12_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py tests/test_social_process.py tests/test_process_explain_rebuild.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P12.E2 — Freeze a runnable preregistered evaluation

- **ID:** P12.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p12_v1.py`; new `evaluation/process_mastery/analyze_linear_p12_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P12_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py tests/test_social_process.py tests/test_process_explain_rebuild.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P12.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P12.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P12_PREREG.md`; `evaluation/process_mastery/linear_p12_v1.py`; `evaluation/process_mastery/analyze_linear_p12_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P12_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py tests/test_social_process.py tests/test_process_explain_rebuild.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 13 — Staged sleep reusable libraries and strategy recall

**Entry:** Phase 12 verified episodes/processes, P1 replay scheduler and Phase 10 traces. **Status:** planned.

Merge former P6.B2 with I3.2/I3.3. Preserve the existing paced MemoryCycle producer; one owner delegates existing replay rather than running it twice. Learning is measured by later verified behavior, not support_count or number of stored schemas. Strategy-yield records supplement discovered processes without changing their verification contract.

**Registered evidence:** 200 paired learn→idle→interference→delayed-test streams with full sleep, P1 replay-only, matched-compute awake rehearsal and no-offline arms; 100 interrupt/restart controls. Primary delayed accuracy gain≥10 points over replay-only and new-task loss≤2 points; zero foreground starvation/double debit/ungrounded consolidation. Library reuse must reduce held-out primitive or exact-verifier work≥25% including retrieval and decoder overhead.

### P13.01 — Freeze sleep stage ownership library cost and interruption

- **ID:** P13.01
- **Tier:** T1
- **Goal:** Freeze sleep stage ownership library cost and interruption.
- **Read first:** `seeds/consolidation_scheduler.json`; `seeds/episodic_working_memory_core.json`; `tests/test_consolidation_scheduler_migrated.py`; `seeds/process_solving.json`; `seeds/invention_round.json`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_SLEEP_STAGE_CONTRACT.md`; new `tests/test_sleep_regime_migrated.py`.
- **Pattern to copy:** P1 one-replay-per-cycle markers and P3 request identities.
- **Steps:** 1. Specify replay→consolidate→decay→library→recombination order, cycle/stage receipts and shared budgets. 2. Define foreground interruption, checkpoint cursors, stale-model cancellation and once-only work. 3. Define full description length and protected evidence rules; memory savings cannot erase disconfirming evidence.
- **Guard:** SleepRegimePolicy disabled.
- **Acceptance:** planned `test_one_owner_per_cycle`, `test_replay_not_duplicated`, `test_foreground_interrupts`, `test_resume_no_double_debit`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_consolidation_scheduler_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** replacing the scheduler or counting replay completion as a retention result.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P13.02 — Implement staged offline work and resumable lifecycle

- **ID:** P13.02
- **Tier:** T2
- **Goal:** Implement staged offline work and resumable lifecycle.
- **Read first:** `docs/research/engine_substrate/COGNITION_SLEEP_STAGE_CONTRACT.md`; `scripts/gen_consolidation_scheduler_seed.py`; `seeds/staleness_decay.json`; `seeds/demotion_hierarchy.json`; `seeds/default_mode_core.json`.
- **Touch:** new `scripts/gen_sleep_regime_seed.py` + `seeds/sleep_regime.json`; `tests/test_sleep_regime_migrated.py`.
- **Pattern to copy:** existing replay completion and bounded default-mode simulation.
- **Steps:** 1. Claim a MemoryCycle, delegate replay once, then process named stages only after receipts. 2. Run decay/recombination under their original semantics and budget. 3. Persist stage cursor and interrupt before the next atomic offline operation; test 256-epoch bounds and recovery.
- **Guard:** SleepRegimePolicy; load/idleness gates remain.
- **Acceptance:** `test_stage_order`, `test_decay_once_per_epoch`, `test_recombination_advisory`, `test_save_load_resume`, `test_256_epoch_growth_bounded`, P13.01 assertions.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_consolidation_scheduler_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** blocking foreground action until a whole invention round completes.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P13.03 — Learn reusable sub-process libraries by verified compression

- **ID:** P13.03
- **Tier:** T2
- **Goal:** Learn reusable sub-process libraries by verified compression.
- **Read first:** `docs/research/engine_substrate/COGNITION_SLEEP_STAGE_CONTRACT.md`; `seeds/process_lifting.json`; `seeds/process_schema.json`; `seeds/sleep_regime.json`.
- **Touch:** new `scripts/gen_library_learning_seed.py` + `seeds/library_learning.json`; new `tests/test_library_learning.py`.
- **Pattern to copy:** P10 structural lifting and P7 re-decode after verified growth.
- **Steps:** 1. Extract shared sub-processes from successful programs, capability traces and plans. 2. Include definition/reference/decoder/exception cost and adopt only verified reductions. 3. Rewrite stored traces with equivalence witnesses and revalidate on new states; schedule as a bounded sleep stage.
- **Guard:** LibraryLearningPolicy disabled.
- **Acceptance:** `test_shared_chunk_lowers_total_cost`, `test_rewritten_trace_same_effect`, `test_failure_evidence_preserved`, `test_later_unseen_task_reuses_chunk`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_library_learning.py tests/test_process_lifting.py tests/test_sleep_regime_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** compression through deleting failed experiences or ignoring definition cost.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P13.04 — Recall strategies by problem structure and observed yield

- **ID:** P13.04
- **Tier:** T2
- **Goal:** Recall strategies by problem structure and observed yield.
- **Read first:** `seeds/invention_operators.json`; `seeds/similarity_recall.json`; `seeds/strategy_discovery.json`; `seeds/library_learning.json`; `tests/test_soft_weights_term.py`.
- **Touch:** new `scripts/gen_strategy_library_seed.py` + `seeds/strategy_library.json`; new `tests/test_strategy_library.py`.
- **Pattern to copy:** P4 candidate-only recall, SoftWeights and observed-result provenance.
- **Steps:** 1. Record problem signature→strategy/operator→observed yield with context and model epochs. 2. Retrieve compatible candidates and use native soft weighting where justified; cold start falls back to bounded existing search. 3. Reverify every application and test distribution changes without hard-coding puzzle names.
- **Guard:** StrategyLibraryPolicy disabled.
- **Acceptance:** `test_recall_reduces_candidate_work`, `test_bad_recall_falls_back`, `test_yield_requires_observed_result`, `test_distribution_change_invalidates`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_strategy_library.py tests/test_library_learning.py -q -p no:cacheprovider`.
- **Non-goals:** a scalar learning-rate knob in place of supported shape distinctions; treating expected yield as proof.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P13.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P13.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add sleep, library learning and strategy recall to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p13_profile_chain`, `test_p13_default_isolation`, `test_p13_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_library_learning.py tests/test_strategy_library.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P13.E2 — Freeze a runnable preregistered evaluation

- **ID:** P13.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p13_v1.py`; new `evaluation/process_mastery/analyze_linear_p13_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P13_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_library_learning.py tests/test_strategy_library.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P13.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P13.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P13_PREREG.md`; `evaluation/process_mastery/linear_p13_v1.py`; `evaluation/process_mastery/analyze_linear_p13_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P13_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_library_learning.py tests/test_strategy_library.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 14 — Laws proofs and safely authored invention operators

**Entry:** Phase 13 reusable verified processes and measured strategy outcomes. **Status:** planned.

Complete I4.5 and I7.3 before adopting I7.1 authorship into the live invention loop. Earlier processes retain their supported verification scope; proof requirements apply to explicitly proof-admitting domains. Bounded fingerprints do not become proofs. Operator proposals cannot modify criteria, verifier or held-out tests.

**Registered evidence:** 200 law/claimed-invariant cases (including false finite-sample laws), 200 candidate-operator cases and 100 proof/criterion tampering controls. All adopted processes in declared proof-admitting domains must carry machine-checked invariants; zero false proofs or unauthorized machinery edits. Operator candidates must show positive development-split yield without loss of invariant checks, then face a separate untouched test panel. Original human-gated criterion proposals remain required.

### P14.01 — Specify law statements proof obligations and operator permissions

- **ID:** P14.01
- **Tier:** T1
- **Goal:** Specify law statements proof obligations and operator permissions.
- **Read first:** `seeds/theorem_core.json`; `tests/test_theorems_as_terms_migrated.py`; `seeds/operator_authorship.json`; `seeds/criterion_proposals.json`; `seeds/adoption_safety.json`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md`; new `tests/test_process_laws.py`.
- **Pattern to copy:** existing theorem terms and explicit criterion-proposal lifecycle.
- **Steps:** 1. Define supported law vocabulary, assumptions, quantification and proof-checking boundary. 2. Separate empirical invariant, conjecture and checked theorem. 3. Define editable operator-template data and immutable verifier/evaluation/approval boundaries; promotion requires the existing human gate where specified.
- **Guard:** law/operator policies disabled by default.
- **Acceptance:** planned `test_empirical_invariant_not_theorem`, `test_proof_assumptions_bound`, `test_operator_cannot_edit_verifier`, `test_human_gate_not_bypassed`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_theorems_as_terms_migrated.py tests/test_operator_authorship_migrated.py tests/test_criterion_proposals_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** unbounded theorem proving or automatic approval of self-authored criteria.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P14.02 — Promote verified invariant conjectures into checked laws

- **ID:** P14.02
- **Tier:** T2
- **Goal:** Promote verified invariant conjectures into checked laws.
- **Read first:** `docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md`; `scripts/gen_invariant_miner_seed.py`; `seeds/theorem_core.json`; `tests/test_process_laws.py`.
- **Touch:** new `scripts/gen_process_laws_seed.py` + `seeds/process_laws.json`; `tests/test_process_laws.py`.
- **Pattern to copy:** invariant wall witness and native theorem-checking terms.
- **Steps:** 1. Express supported invariants as law conjectures with exact source family and assumptions. 2. Invoke the existing native proof checker and attach a proof/reference only when checked. 3. Retain unsupported/failed proofs as conjectures and seek counterexamples through the ordinary experiment path.
- **Guard:** ProcessLawsPolicy disabled.
- **Acceptance:** `test_parity_law_checked`, `test_false_finite_sample_law_rejected`, `test_law_proof_bound_to_family`, `test_counterexample_downgrades_conjecture`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_laws.py tests/test_invariant_walls.py -q -p no:cacheprovider`.
- **Non-goals:** assuming absence of a counterexample proves a general law.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P14.03 — Enforce proof-carrying adoption in declared domains

- **ID:** P14.03
- **Tier:** T2
- **Goal:** Enforce proof-carrying adoption in declared domains.
- **Read first:** `docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md`; `seeds/process_laws.json`; `seeds/adoption_safety.json`; `seeds/invention_round.json`.
- **Touch:** new `scripts/gen_process_proof_adoption_seed.py` + `seeds/process_proof_adoption.json`; new `tests/test_process_proof_adoption.py`.
- **Pattern to copy:** existing source-bound verifier receipts and adoption gate.
- **Steps:** 1. Require checked invariant proofs for every newly adopted process where the domain contract requires them. 2. Bind proof/model/frame/process epochs and invalidate changed artifacts. 3. Preserve the separate externally consequential action/manifold authorization after mathematical verification.
- **Guard:** ProcessProofAdoptionPolicy explicit domain registration.
- **Acceptance:** `test_no_required_proof_no_adoption`, `test_wrong_process_proof_rejected`, `test_changed_process_invalidates_proof`, `test_proof_does_not_authorize_external_action`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_proof_adoption.py tests/test_process_laws.py -q -p no:cacheprovider`.
- **Non-goals:** requiring formal proofs in domains without a sound declared proof model.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P14.04 — Author candidate invention operators under frozen criteria

- **ID:** P14.04
- **Tier:** T2
- **Goal:** Author candidate invention operators under frozen criteria.
- **Read first:** `docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md`; `seeds/operator_authorship.json`; `seeds/criterion_proposals.json`; `seeds/strategy_library.json`; `tests/test_operator_authorship_migrated.py`.
- **Touch:** new `scripts/gen_invention_operator_authorship_seed.py` + `seeds/invention_operator_authorship.json`; new `tests/test_invention_operator_authorship.py`.
- **Pattern to copy:** existing operator authorship/adoption_safety and composition template data.
- **Steps:** 1. Propose new combinators over held algebra with source provenance. 2. Sandbox and verify them under the same development tasks, resource limits and proof obligations as held operators. 3. Apply existing review/criterion gates before promotion; keep baseline operators and full rollback lineage.
- **Guard:** InventionOperatorAuthorshipPolicy; existing human gate retained.
- **Acceptance:** `test_new_combinator_is_graph_authored`, `test_unsafe_template_rejected`, `test_candidate_cannot_change_criteria`, `test_promotion_requires_existing_gate`, `test_operator_lineage_retained`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_invention_operator_authorship.py tests/test_process_proof_adoption.py -q -p no:cacheprovider`.
- **Non-goals:** silently mutating the engine/verifier or asking a language model to author the measured operator.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P14.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P14.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add proof/law and candidate operator authorship seeds to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p14_profile_chain`, `test_p14_default_isolation`, `test_p14_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_laws.py tests/test_process_proof_adoption.py tests/test_invention_operator_authorship.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P14.E2 — Freeze a runnable preregistered evaluation

- **ID:** P14.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p14_v1.py`; new `evaluation/process_mastery/analyze_linear_p14_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P14_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_laws.py tests/test_process_proof_adoption.py tests/test_invention_operator_authorship.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P14.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P14.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P14_PREREG.md`; `evaluation/process_mastery/linear_p14_v1.py`; `evaluation/process_mastery/analyze_linear_p14_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P14_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_laws.py tests/test_process_proof_adoption.py tests/test_invention_operator_authorship.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## Phase 15 — Scaled portfolios self-curriculum and repeated improvement

**Entry:** Phase 14 proof/adoption machinery and approved candidate operator workflow. **Status:** planned.

Complete remaining I7 work and measure the entire accumulated system. Parallel execution here is a runtime feature with deterministic folding, not permission to run development phases out of order. Self-curriculum chooses training experiences; an external sealed evaluation remains fixed and unavailable to the learner.

**Registered evidence:** At least three operator generations, each with ≥200 fresh tasks per claimed PMB family and disjoint training/selection/evaluation seeds. Compare unchanged-operator, adaptive-curriculum and full system arms at matched cumulative compute/data. Predefine primary score and trend model; require positive held-out trend with corrected uncertainty, no per-generation regression in grounding/proof/action invariants. Human/beyond-human claims require exactly matched evidence in §6; unavailable comparisons stay unavailable.

### P15.01 — Freeze generation lineage portfolio scaling and final claims

- **ID:** P15.01
- **Tier:** T1
- **Goal:** Freeze generation lineage portfolio scaling and final claims.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `seeds/criterion_proposals.json`; `seeds/invention_operator_authorship.json`; `docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md`; `runners/dsl/src/cognitive_cycle.rs`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Pattern to copy:** existing cycle-plan configuration and P5 frozen comparator correction discipline.
- **Steps:** 1. Define generation boundaries, ancestry, operator approval and fixed versus mutable machinery. 2. Specify shared compute/memory budgets, deterministic parallel fold and progress measures. 3. Inventory actual human-baseline sources or define collection protocols; select claimed L-levels and exact admissible comparisons before draws.
- **Guard:** specification only.
- **Acceptance:** explicit generation/arm/task allocation and invariants; no presumed human baseline; final evaluation cannot be selected by curriculum.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_operator_authorship_migrated.py tests/test_criterion_proposals_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** calling a proof-coverage advantage universal beyond-human intelligence.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P15.02 — Scale hypothesis and invention portfolios deterministically

- **ID:** P15.02
- **Tier:** T2
- **Goal:** Scale hypothesis and invention portfolios deterministically.
- **Read first:** `docs/research/engine_substrate/COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`; `runners/dsl/src/cognitive_cycle.rs`; `seeds/invention_round.json`; `seeds/experiment_design.json`.
- **Touch:** new `scripts/gen_process_portfolio_seed.py` + `seeds/process_portfolio.json`; new `tests/test_process_portfolio.py`; `runners/dsl/src/cognitive_cycle.rs` only for existing-plan configuration integration.
- **Pattern to copy:** AreaParallel execution semantics and graph-owned funding requests.
- **Steps:** 1. Partition hypothesis/operator work as declared graph data. 2. Use existing cycle-plan parallelism with deterministic result folding and one shared budget. 3. Test ordering/restart/cancellation and account total work rather than assuming wall-clock gain means better inference.
- **Guard:** ProcessPortfolioPolicy disabled; bounded worker/area count.
- **Acceptance:** `test_serial_parallel_same_effects`, `test_fold_order_deterministic`, `test_parallel_budget_no_overspend`, `test_cancel_preserves_receipts`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_portfolio.py tests/test_thinking_budget_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** multiple independent budgets multiplying approved compute; architecture fork for parallel semantics.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P15.03 — Generate an experience curriculum from verified residual progress

- **ID:** P15.03
- **Tier:** T2
- **Goal:** Generate an experience curriculum from verified residual progress.
- **Read first:** `docs/research/engine_substrate/COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`; `seeds/qualia_acquisition.json`; `seeds/strategy_library.json`; `seeds/learning_progress_curiosity.json`.
- **Touch:** new `scripts/gen_process_curriculum_seed.py` + `seeds/process_curriculum.json`; new `tests/test_process_curriculum.py`.
- **Pattern to copy:** existing learning-progress curiosity and acquired residual/provenance records.
- **Steps:** 1. Generate training tasks from verified effect/representation novelty and unresolved distinctions. 2. Keep tractable progress, counterexamples and stale-success rechecks within budget; reject incoherent tasks. 3. Keep all sealed PMB evaluation IDs and outcome labels outside agent-visible curriculum state.
- **Guard:** ProcessCurriculumPolicy disabled.
- **Acceptance:** `test_curriculum_targets_real_residual`, `test_unlearnable_task_not_endlessly_repeated`, `test_sealed_holdout_never_visible`, `test_growth_and_cost_bounded`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_curriculum.py tests/test_qualia_acquisition.py -q -p no:cacheprovider`.
- **Non-goals:** optimizing a reported score by choosing easier evaluation tasks.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P15.04 — Run the graph-owned operator improvement lifecycle

- **ID:** P15.04
- **Tier:** T2
- **Goal:** Run the graph-owned operator improvement lifecycle.
- **Read first:** `docs/research/engine_substrate/COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`; `seeds/invention_operator_authorship.json`; `seeds/process_curriculum.json`; `seeds/process_proof_adoption.json`.
- **Touch:** new `scripts/gen_recursive_process_improvement_seed.py` + `seeds/recursive_process_improvement.json`; new `tests/test_recursive_process_improvement.py`.
- **Pattern to copy:** P14 sandbox/proposal/promotion records and persistent generation ancestry.
- **Steps:** 1. Run proposal→sandbox→verification→existing approval→promotion as graph state transitions. 2. Preserve a frozen ancestor arm and rollback the active lineage when adoption/grounding invariants fail. 3. Allow host only to provide declared approval events, tick and record; log any human edits that invalidate an autonomous-generation claim.
- **Guard:** RecursiveProcessImprovementPolicy; unchanged human/host boundaries.
- **Acceptance:** `test_generation_has_complete_ancestry`, `test_no_human_authored_operator_in_claimed_generation`, `test_failed_generation_not_promoted`, `test_restart_keeps_same_generation_budget`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_recursive_process_improvement.py tests/test_invention_operator_authorship.py tests/test_process_curriculum.py -q -p no:cacheprovider`.
- **Non-goals:** removing existing approval requirements to manufacture an autonomy claim.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P15.E1 — Integrate the phase and validate the evidence adapter

- **ID:** P15.E1
- **Tier:** T2
- **Goal:** Integrate the phase and validate the evidence adapter.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `evaluation/process_mastery/harness.py`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 guarded profile chain and native sink assertions.
- **Steps:** 1. Add portfolio, curriculum and recursive process improvement to the explicit profile after focused tests pass. 2. Exercise this phase through world events and actual native rules; test one shared budget and default/conversation isolation. 3. Record boot time, graph/memory growth and receipt provenance. Review adapter parity before E2.
- **Guard:** cognition-on only; all other profiles unchanged.
- **Acceptance:** new `test_p15_profile_chain`, `test_p15_default_isolation`, `test_p15_shared_budget`; focused bundle passes with no unsupported path presented as a success.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_portfolio.py tests/test_process_curriculum.py tests/test_recursive_process_improvement.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** activating experimental processes in CORE; freezing evaluation before runtime integration.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P15.E2 — Freeze a runnable preregistered evaluation

- **ID:** P15.E2
- **Tier:** T1
- **Goal:** Freeze a runnable preregistered evaluation.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `docs/research/engine_substrate/COGNITION_BUILD_P5_RESULTS.md`.
- **Touch:** new `evaluation/process_mastery/linear_p15_v1.py`; new `evaluation/process_mastery/analyze_linear_p15_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P15_PREREG.md`.
- **Pattern to copy:** corrected P5 v3 actual arm adapters, hash freeze and shared-graph comparator.
- **Steps:** 1. Implement the phase-specific families stated above; include development --self-check paths and hard errors on missing adapters. 2. Freeze world/profile/engine/runner/analyzer hashes, exact seed allocation, limits, primary criteria and comparator contracts. 3. Commit preregistration alone only after every arm produces real development outcomes. Use §5 commands; no registered draw before freeze.
- **Guard:** evaluation only.
- **Acceptance:** both --self-check commands pass; no null adapter; answers/strategies absent from agent input; same worlds and primitive/model access in comparison arms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_portfolio.py tests/test_process_curriculum.py tests/test_recursive_process_improvement.py -q -p no:cacheprovider`.
- **Non-goals:** a dummy baseline, depth-shortcut comparator or rescoring old results; treating a human baseline as available without protocol matching.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

### P15.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P15.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P15_PREREG.md`; `evaluation/process_mastery/linear_p15_v1.py`; `evaluation/process_mastery/analyze_linear_p15_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P15_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_portfolio.py tests/test_process_curriculum.py tests/test_recursive_process_improvement.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

## 5. Common integration, evaluation and regression gates

Every new phase uses its own registered protocol and `.E1 → .E2 → .E3` ordering. E1 completes integration **before** freezing hashes. E2 freezes a runner with working adapters and records the full engine build provenance and dependency closure. E3 runs once on the fixed draw and reports all hypotheses, controls, unknowns and failure limits. If an implementation defect invalidates a comparison, preserve it, version the corrected protocol and use an untouched split; never rescore the defective report into success.

### Splits, runtime and accounting

Preserve `evaluation/process_mastery/generators.py::split_seed` and PMB v1 development/held-out ranges. For new phases, version the allocation with nonoverlapping blocks `10_000_000 + phase*1_000_000 + family*10_000 + control_block*1_000 + draw`; with separately reserved development and held-out control blocks, record every concrete seed and confirm disjointness from the committed PMB v1 ranges and all earlier phase draws. Use a separate declared RNG stream for each phase/family/control; paired arms share world instances but use separate agent state. Explicit repeated-encounter arms retain the same agent only within that arm. Public/curated tasks require recorded provenance and split membership; no new internet baseline research is claimed by this plan.

Proposed defaults to freeze at each E2: 200 primary paired tasks per stated family, 100 control tasks, max 400 ticks and 100,000 native rule steps per tick (matching the current harness upper bounds), plus an explicit smaller per-operation ThinkingBudget and model/search depth/node cap from the supported contracts. A host rule-step cap is not a substitute for graph budget enforcement. Long retention streams use the registered 256 epochs; generation-scale runs freeze total compute, data, graph bytes/nodes and approval opportunities before any comparison. All limits and timeouts appear in the raw record.

Report paired binary differences, Wilson 95% intervals and exact McNemar tests; apply Holm correction to all primary superiority tests within a phase at α=.01. For work/latency use paired distributions and a frozen 10,000-resample bootstrap. Deterministic work includes retrieval, generation, verification, model refinement, definition/decoder cost and primitive action use. Record actual observed goal success separately from predicted success, and pipeline failures separately from unsupported input. Do not coerce missing adapters to zero scores. Zero-tolerance provenance/action/proof invariants fail on any violation.

All acceptance thresholds in §4 are proposed criteria for the corresponding future preregistration. They must be reconciled against supported input classes before the first draw; no threshold changes after inspection. A design that cannot express the intended family gets an explicit open task and cannot pass through an irrelevant trivial substitute.

### Commands to be implemented/run at the named phase

The two new evaluation modules for every phase N must accept these CLI forms. `COGNITION_PHASE` is the phase number, `COGNITION_PREREG_HASH` the standalone full freeze hash, and `COGNITION_REPORT` the emitted report path. Set these task-specific variables explicitly; the runner verifies the hash/artifact set and writes `evaluation/reports/cognition_linear_pN_v1_<hash8>_d0-200.json`.

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python "evaluation/process_mastery/linear_p${COGNITION_PHASE}_v1.py" --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python "evaluation/process_mastery/analyze_linear_p${COGNITION_PHASE}_v1.py" --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python "evaluation/process_mastery/linear_p${COGNITION_PHASE}_v1.py" "$COGNITION_PREREG_HASH" 0 200
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python "evaluation/process_mastery/analyze_linear_p${COGNITION_PHASE}_v1.py" "$COGNITION_REPORT"
```

Self-checks use development-only seeds and exercise null, timeout, unsafe output and comparator disagreement. Holdout draws wait until the standalone freeze. The baseline experiment and new phase evaluations produce new scorecards; preserve `evaluation/process_mastery/results/i0_baseline.json` as the original NOT_RUN record. Generated reports remain uncommitted; record their hashes, commands and retention locations in the phase results document.

### Regression gate

Use the current baseline protocol without silently redefining known failures:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/failure_baseline.py verify --list results/cognition_gate_baseline.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/failure_baseline_sweep.py --files-from scripts/cognition_gate_suite.txt --workers 4 --timeout 420 --out /tmp/cognition-linear-gate.json
```

Also run the phase's own tests, `tests/test_track_i_foundation.py`, `tests/test_cognition_profile_integration.py`, prior phase acceptance that the change affects, orphan-signal lint and boot-status reporting. A changed baseline requires an independently explained baseline task; provenance-only allowlist additions require a specific reason and cannot conceal an unconsumed decision request. Test source/epoch collision, malformed inputs, interrupted leases, save/load, default isolation and grammar-only dependency boot for each new runtime seed.

For Rust changes, inspect ownership and disk space, then:

```sh
df -h /
scripts/engine_build.sh
OZMA_SEED_PERSIST_DISABLED=1 scripts/engine_cargo_test.sh --lib -- --test-threads=4
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider
```

P4 records inherited frozen-core, dual-process and Arc RED classifications, the capability-control timeout and fully skipped staleness-decay coverage. P5 records 860 Rust tests passed, four ignored and the known `graph_rule_patch_node_receives_durable_commit_receipt` failure; do not assert these historic counts describe a future checkout. Keep P3/P4 NOT_ESTABLISHED exceptions explicit until actually resolved. Re-run and report the current classifications at each phase gate.

## 6. Original-work coverage and claim gates

This table assigns every original outstanding I work item and former P6 faculty to exactly one principal delivery phase; integration tasks can depend on earlier outputs without creating a second schedule.

| Original items | Linear owner | Disposition |
|---|---|---|
| I0.1/I0.2/I0.4 | 6 | Reuse committed spec/scaffolding/source-view decision; complete runnable adapter and artifact checks |
| I0.3 | 6 | Produce the first actual frozen baseline; original NOT_RUN preserved |
| I1.1–I1.5 | 6 | Complete six-form views/evaluators/probes/dedup and end-to-end tests; landed algebra not rebuilt |
| P4 non-Shape producer gap; former P6.D7 | 7 | Experience-grounded signatures, dimension/significance growth, perceptual numerosity |
| I4.1/I4.2/I4.3; P4 C5 VOI and E1 refinement gaps | 8 | Learned transitions/latents, hypothesis portfolio, experiment selection and actual funded refinement |
| I2.1–I2.6 | 9 | Execute existing operators, exact closure, wall explanations, supported repair/stochastic effects |
| I3.1/I3.4; I5.1/I5.2; I2.7 | 10 | Lifting, goals, targeted invention, discovered strategy and no-authored-solver held-out gate |
| I5.3/I5.4 | 11 | Representation search and verified cross-domain maps |
| Former P6.F3; I4.4; I6.1–I6.3 | 12 | Single demonstration/instruction/observation pipeline plus explain/rebuild and peer teaching |
| Former P6.B2; I3.2/I3.3 | 13 | Single staged offline lifecycle, library compression and strategy recall |
| I4.5; I7.1/I7.3 | 14 | Laws/proofs, proof-required adoption and operator proposal/promotion |
| I7.2/I7.4/I7.5 | 15 | Deterministic runtime portfolios, self-curriculum and multi-generation improvement |

### PMB family delivery

| PMB family | World/adapter owner and evidence |
|---|---|
| (a) Permutation puzzles | Phase 6 Loopover baseline; Phase 10 discovered strategies, cube/sliding adapters and held-out puzzle panels |
| (b) Mechanism discovery | Phase 6 measured finite-world baseline; Phase 8 learned model and intervention comparison |
| (c) Grid transformations | Phase 6 D4 baseline; Phase 11 source/split-audited grid adapter. Generated D4 and external ARC/LS20 results remain separately scoped |
| (d) Tool invention | Phase 10 goal/interface tasks and real emitted effects; Phase 12 own-body social trials |
| (e) Program synthesis | P6.06 reuses the existing native synthesis/MBPP runner, with task/split provenance; later final comparisons cannot omit an unsupported/failed family |
| (f) Explain and rebuild | Phase 12 isolated-receiver reconstruction and held-out effect agreement |
| (g) Cross-domain transfer | Phase 11 source/fresh/mismatched-source learning curves; Phase 13 accumulated-library retention |
| (h) Law rediscovery | Phase 8 observed-data/latent models, Phase 14 law conjectures versus proofs and noisy finite-sample controls |

### Capability levels remain separate evidence questions

| Level | Required evidence assembled from the linear phases |
|---|---|
| L1 Understand | Phase 8 identification/intervention evidence **and** Phase 12 explain/rebuild; human-level claim needs matched human accuracy/intervention protocol |
| L2 Invent | Phase 10 held-out puzzle outcomes with no injected strategy; human comparison must match puzzle, scramble, affordances and stopping rule |
| L3 Accumulate | Phase 10 unseen-size lifting and Phase 13 later-task cost/retention evidence including storage/decoder cost |
| L4 Transfer | Phase 11 faster target learning from source experience versus matched fresh/mismatched controls |
| L5 Invent for goals | Phase 10 novel tool effects and Phase 11 total-description improvements; human-level claim requires matched tool-invention baseline |
| L6 Acquire socially | Phase 12 own-trial learning from observation/instruction/demonstration versus reward-only at declared equal evidence opportunities |
| L7 Specific beyond-human result | A separately registered, directly supported comparison: cheaper processes than matched published human best; matched human accuracy with ≤¼ interactions; 100% checked invariant coverage in a declared proof-admitting class compared with a stated human workflow; or positive held-out trend over ≥3 generations of approved graph-authored operators with no human-authored operator edits |

L7 categories describe specific measured advantages. Proof coverage or a positive trend alone does not imply human superiority in accuracy or general intelligence. Without a protocol-matched human reference, report algorithmic improvement and leave the human comparison unavailable. Human approval events required by the architecture can coexist with graph-authored operators; log them and do not claim unconstrained autonomous self-modification.

### Explicitly retained limits

P3 rung-1 cache speedup remains failed. P4 C5's incremental-resolution test remains failed, and new Phase 8 evidence does not rewrite it. P5 v1 and v2 retain their recorded limitations. Irregular-time streams, arbitrary continuous imagery angles, broad SCM identification, unrestricted natural-language understanding and physical/open-world breadth are not established by this plan's bounded input contracts. A future extension needs an explicit representation/evidence task before adoption; existing unsupported cases must remain honest. Quadratic GenInfer default features and real-valued Pareto stay deferred until a concrete supported consumer justifies a separate engine decision.

## 7. Next executable action

Start **P6.01**, then P6.02–P6.05, then P6.E1–E3. Do not restart completed P4/P5 implementation or treat the committed partial I foundation as a completed capability gate. The first new result should be a measured PMB baseline and an explicit, tested process-support matrix. Every later phase's next action is its first numbered task after the preceding results review.
