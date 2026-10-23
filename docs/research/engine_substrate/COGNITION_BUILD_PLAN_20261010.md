# Cognition build — single linear execution plan

**Reconciled:** 2026-10-22 through P11.E3 heldout closeout; includes Track I foundation commit `53da7321`.

This is the **sole execution order** for the cognition build and former Track I. Phases 0–5 are completed implementation/reporting cycles with the limits below. Phases 6–15 now also have completed reporting cycles with explicit failed/unestablished capabilities. Continue with Phase 16, then execute Phases 17–22 in order. Former P6 and I0–I7 work is integrated here; the post-P15 review adds behavioral/provenance closure phases, and there is no parallel Track I schedule. Original IDs are retained in the coverage table and task headings so existing code, tests and results remain traceable.

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

### Linear schedule and reporting-cycle status

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
| 16 | Native execution/provenance and valid comparators | Post-P15 review closure; details below | 15 |
| 17 | Behavioral qualia and acquired significance | Post-P15 review closure; details below | 16 |
| 18 | Observation-built models and real world experiments | Post-P15 review closure; details below | 17 |
| 19 | Generic process invention and reusable strategies | Post-P15 review closure; details below | 18 |
| 20 | Fresh learning, transfer and social acquisition | Post-P15 review closure; details below | 19 |
| 21 | Finite-memory retention and useful curriculum | Post-P15 review closure; details below | 20 |
| 22 | Independent-goal repeated improvement and capability audit | Post-P15 review closure; details below | 21 |

Rows 6–15 are closed reporting cycles, not uniformly passed capability gates; rows 16–22 are planned. These are delivery phases, not the old L0–L7 capability levels. Close a level only when its assembled evidence satisfies the criteria in §6. No later capability is presumed available to an earlier implementation: replay v0 and explicit held processes suffice before library learning; early targeted search does not require a future strategy library.

## 3. Task contract

Execute task IDs in the order printed within each phase, then its `.E1 → .E2 → .E3` integration/freeze/results tasks. Proceed to the next phase only after reviewing that results ledger. Every task below has tier, exact read references (symbol anchors remain authoritative after line movement), ≤3 touch groups (generator plus generated seed counts as one), pattern, steps, guard, acceptance and verification command. Acceptance names referring to new tests are planned assertions, not current passing tests. New paths are marked `new`; references to earlier-phase artifacts mean the artifacts delivered by that phase.

T1 defines unresolved semantics or evaluates evidence; T2 implements native behavior/integration; T3 copies a specified pattern or closes documentation. A T1 spec must freeze error/unknown behavior, ownership, epochs, resource limits and acceptance before implementation. No task can hide unlisted changes to Rust binders or adapters. If a new Term is necessary, split its engine change into separately recorded ≤3-file tasks: evaluator/variant; JSON/reflection; substitution/free-variable/cache metadata; native build/API acceptance. Reuse current Terms first; opaque process support generally needs an evaluator adapter rather than a fresh algebra.

All task `Verify cmd` entries below use the repository `.venv/bin/python`. They are commands for later implementation, not tests run by this planning update. Every implementation task also requires the applicable §5 gate; spec tasks finish when their written contract and acceptance definitions are frozen, without claiming tests for future behavior already pass. Rust subtasks may be an atomic compile integration series, but no downstream seed consumer becomes active before the complete Rust integration passes.

## 4. Detailed linear phases

## Phase 6 — Measured foundation and executable process views

**Entry:** P4/P5 reported results and partial foundation commit `53da7321`. **Status:** evidence closeout complete with limits. P6 implementation and cognition-on integration passed focused gates; P6.E2 preregistration and P6.E3 held-out report are frozen. TransitionHypothesis execution, external receipt-backed outcomes, D4 and finite mechanism arms remain unsupported or NOT_RUN; no broad capability claim is authorized.

Finish I0 and I1 without rebuilding landed algebra. Preserve opaque native views until their effect evaluation is supported. The PMB baseline profile omits Track I seeds and policies; retain the greedy solver as an explicitly named hand-written comparator.

**Registered evidence:** 200 paired tasks each for Loopover, D4 and finite mechanism worlds, 100 malformed/stale/view controls. Report baseline measurements even when weak; do not require a nonzero baseline. View conformance and pure evaluator equivalence must be 100% for declared supported inputs, with zero live mutation. A family with no executable baseline is NOT_RUN and blocks its comparative claim, not unrelated conformance.

**P6.01–P6.05 implementation record (2026-10-22):** Commits `dcd897dd`, `39af9284`, `d473ad9d`, `68c81494` and `d6271e00` froze the contract, added explicit arms, implemented bounded Program views, retained unsupported opaque models, and bound views to owners/epochs with collision-safe probe deduplication. Focused process-view and Track-I tests pass. Current native support remains Program, supported DimensionGenerator effects, and explicitly opaque/unsupported TransitionHypothesis, CapabilityProgram, EmbodiedMotorProgram and FamilyProgram effects. P6.02's strengthened action test now observes native ProcessSchema selection/apply in Loopover; it does not establish an external sink receipt. The 42-test E1 bundle passed after profile integration.

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

**Implementation record (2026-10-22):** `evaluation/process_mastery/program_adapter.py` explicitly registers family (e) on either PMB profile and reuses `domains.prog_synthesis` plus the existing MBPP split/parser/scorer. Task 14's live baseline outcome matches the frozen MBPP artifact (`accepted_holdout_fail`); both profiles use the same task, revealed assertion, solver rules and external held-out scorer. The adapter emits the accepted native IR/node, solver status, attempts/budget, elapsed time, split report and fixture hash. The test split's solution code is stripped by the existing loader; held-out rows stay in the detached scorer record and are checked absent from the graph. Verification: `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_program_adapter.py tests/test_program_synthesis_migrated.py -q -p no:cacheprovider` — 21 passed. This registers a family adapter; it does not establish a synthesis gain or a P6 comparative result.

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

**P6.E1 integration record (2026-10-22):** Added the process-schema, invention-operator/round, invariant-miner and process-solving seed closure to `COGNITION_ON_SEEDS`; their policies remain disabled at profile boot. Default and conversation profile isolation is tested by rule-name absence. The cognition-on profile exposes one enabled ThinkingBudget for requesters (a second attached budget node remains disabled in the existing parameter bundle). A measured profile boot took 0.1342 s, with 879 graph nodes and 528 rules; native per-agent memory bytes are unavailable from the current allocator API. The PMB Loopover graph run emits a ProcessSchema trace and reaches the observed solved state, but it is a simulator mutation without an external sink receipt; physical observed-outcome parity is not established. Verification: the E1 focused bundle listed below passed, 42 tests.

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

**P6.E2 freeze record (2026-10-22):** `COGNITION_LINEAR_P6_PREREG.md` was committed alone as `f31f17ae` after the development allocation completed. It freezes 200 paired Loopover, D4 and mechanism seeds, 100 malformed/stale/opaque controls, the exact 240 runnable MBPP task IDs, arm limits, hashes, scoring boundary and unsupported D4/mechanism disposition. Development scorecard and analyzer hashes are recorded in the preregistration. Both self-checks and the 59-test focused bundle passed before the freeze.

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

**P6.E3 result record (2026-10-22):** See [`COGNITION_LINEAR_P6_RESULTS.md`](COGNITION_LINEAR_P6_RESULTS.md) for all 1,780 raw-row counts, metrics, hashes, regressions and limitations. The frozen Loopover panel measured 0/200 baseline versus 200/200 Track I on supplied 2×2 processes; the registered MBPP arms were identical at 32/240 held-out passes; controls passed 100/100. D4 and finite mechanism remain NOT_RUN in both arms. The result ledger classifies each criterion and authorizes Phase 7.01 episode-acquisition work only; it closes no L1–L7 level and does not authorize unsupported process effects.

## Phase 7 — Qualia acquired from episodes and perceptual numerosity

**Entry:** Phase 6 executable supported views and actual baseline arms. **Status:** evidence closeout complete with limits; P7.01/P7.04 semantics frozen, P7.02/P7.03/P7.05 implemented, P7.E1 integrated, P7.E2 preregistered, P7.E3 reported. The transfer hypothesis and real-world perceptual criteria remain NOT_ESTABLISHED.

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

**P7.01 semantic freeze (2026-10-22):** `COGNITION_QUALIA_ACQUISITION_CONTRACT.md` freezes owner/source/epoch identity, label-free evidence ingress, finer-grain versus new-dimension rules, three-episode recurrence, two fresh-context validations, contradiction/revision semantics, live-versus-standing significance, funding bounds, and terminal states. The four named acceptance cases are present as explicitly skipped placeholders until P7.03 supplies graph-rule behavior; they are not counted as passing tests. Existing compensation contract verification passed 6 tests.

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

**P7.02 implementation record (2026-10-22):** Added generated `experience_signature` (self-load-only, depends on the existing cognition-signature projection, policy disabled by default). It projects only observed episode events with an exact owner/episode/event/action and source/model/frame-epoch matched outcome receipt. The descriptor retains a source-linked `sequence_ref` of measured features, explicit missing values, a separate live overlay, and no target-axis or outcome-class field. Unsupported modalities and mismatched receipts produce no source. Verification: `tests/test_experience_signature.py tests/test_cognition_signature_migrated.py` — 21 passed. The P7.01 acquisition tests remain skipped until P7.03 adds graph-rule acquisition; P7.02 creates signatures only and makes no qualia-acquisition claim.

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

**Entry:** Phase 7 episode evidence and acquired distinction interfaces. **Status:** evidence closeout complete with limits; P8.01 contract frozen, P8.02–P8.04 implemented, P8.E1 integrated, P8.E2 preregistered, P8.E3 reported.

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

**Entry:** Phase 8 supported learned/held process effects and intervention model. **Status:** complete through P9.E3; finite verified-invention evidence recorded with explicit limits.

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

**P9.02 implementation record (2026-10-22):** Native composition/inverse, all six executable operators, the six-element dihedral closure, precise conjugation, one-time budget debit, and restart bound pass in `tests/test_process_invention.py`. Review against the frozen funding contract found a legacy unbudgeted fallback; removed it from the authoring script and regenerated `seeds/invention_round.json`. Missing budget now leaves invention unopened. Focused verification: 14 passed (`tests/test_process_invention.py tests/test_track_i_foundation.py`). Bounded root search remains a library relation search; broad closure runtime and general strategy quality are not established here.

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

**P9.03 implementation record (2026-10-22):** Added live graph acceptance for parity walls, an odd held breaker, partial-probe nonproof, and the no-breaker impasse. The tests exposed repeated wall reminting after an unbreakable result; the miner now suppresses duplicate parity walls per task and the seed was regenerated. A breaker is selected from held odd permutations and applied by the graph. This establishes the finite permutation parity case only; determinant and conserved-count families remain unsupported. Focused verification: 14 passed (`tests/test_invariant_walls.py tests/test_process_invention.py`).

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

**P9.04 implementation record (2026-10-22):** Added native `ProcessRepairVerify` and `ProcessDistribution` terms through evaluator, JSON/reflection, and metadata in the plan's staged ≤3-file Rust commits (`bebcadb6`, `af74abcc`, `55bc59ea`). The repair term requires nonempty fresh states and exact declared goal outputs; it is independent of `ProcessInverse`. The distribution term retains typed support and unknown mass and rejects duplicates, invalid weights, and total mass above one. Invention-round graph rules verify candidate repair records against fresh states and invalidate them on model-epoch change. These are explicit finite evaluator semantics, not a learned probabilistic world model; empirical calibration and distribution induction remain unsupported. Native process algebra Rust tests: 5 passed; focused Python bundle: 47 passed, 1 skipped. The native extension was rebuilt and provenance verified.

**P9.E1 integration record (2026-10-22):** The cognition-on profile already explicitly loads `invention_round` and `invariant_miner`; added assertions for both repair lifecycle rules, default/conversation isolation and the single enabled shared budget. The focused phase/profile bundle passed 41 tests. P9 remains open pending E2 preregistration and E3 held-out results.

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

**P9.E2 freeze record (2026-10-22):** `COGNITION_LINEAR_P9_PREREG.md` was committed alone as `829f824b` after all three arms produced development outcomes. The 1,500-row development allocation completed without missing adapters; exact verified coverage was 200/200 on versus 0/200 in both controls, with zero verification failures and answer leaks. Runner/analyzer self-checks passed. Exact seeds, arm budgets, six-tick/1,000-step limits, criteria and source/engine hashes are frozen in the preregistration.

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

**P9.E3 result record (2026-10-22):** See [`COGNITION_LINEAR_P9_RESULTS.md`](COGNITION_LINEAR_P9_RESULTS.md). All 1,500 held-out rows completed. Exact verified coverage was 200/200 operators-on versus 0/200 operators-off and held-only, a paired +100-point difference with zero verification failures and answer leaks. Irreversible/stochastic evaluator and alias/invalid-inverse controls passed 200/200 and 100/100 per arm. Separate boot time and heap/RSS were not captured; total time includes boot and graph size is reported. No human comparator was available. This finite result authorizes P10.01 contract work only; general induction, stochastic learning, external refinement and capability-level closure remain unsupported.

## Phase 10 — Lifting goal regression and agent-discovered strategies

**Entry:** Phase 9 verified process library and invariant evidence. **Status:** complete through P10.E3 with limits; P10.01 frozen, P10.02 complete for the bounded native grammar, P10.03–P10.05 implemented, and P10.E1 integrated. V1 evaluation was invalidated for missing domain-linked schemas; V2 held-out results are authoritative and the registered strategy-advantage criterion is `FAIL`.

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

**P10.01 semantic freeze (2026-10-22):** `COGNITION_GOAL_INVENTION_CONTRACT.md` defines positional witness bindings, symbolic size/index constraints, domain/epoch-scoped goal identity, typed ProcessGap/interface states, native postcondition checks, depth/expansion/budget bounds, provenance and Python strategy/answer exclusion. AntiUnifyWitness/Substitute reconstruction, unseen valid/invalid size constraints, and the no-authored-strategy input boundary pass. `test_goal_gap_mints_interface` remains explicitly staged for P10.03's policy producer. Verification: 7 passed, 1 staged skip (`tests/test_goal_invention.py tests/test_track_i_foundation.py`).

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

**P10.02 implementation record (2026-10-22):** Added opt-in `process_lifting` rules that retain an AntiUnifyWitness family and instantiate only the frozen native grammar (cycle, swap, compose, inverse, commutator). Every wildcard capture used by the grammar must equal both corresponding source sizes; malformed or mismatched captures return unknown. The graph caps family count, requires target size larger than both sources and ≤16, then fingerprints the concrete process on target-domain probes before minting a lifted ProcessSchema with witness/source provenance. Native code has an independent size cap of 256. Tests cover a size-3/5 commutator lifted to size 6, fresh target effect, altered-binding refusal, incompatible kinds, and provenance. General AST/program lifting remains unsupported. Focused verification: 18 passed, 1 staged P10.01 skip across lifting, goal-contract, and P9 suites; Rust process-algebra unit tests: 6 passed. The extension was rebuilt and provenance verified.

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

**P10.03 implementation record (2026-10-22):** Added opt-in `goal_invention` graph rules. A stuck task creates a typed, epoch-scoped `ProcessGap`; one targeted inverse request draws on the shared ThinkingBudget. Approval temporarily enables the bounded invention policy, and denial leaves it disabled. A candidate is minted only when native inverse/application strictly reduces the current goal distance and its probe fingerprint is available; the existing solver then consumes the graph-held ProcessSchema. Unsupported domains terminate as `needs_tool` with a `SynthesisInterfaceRequest`; no Program/ProgramCandidate bypass is created. Successful and denied paths restore the prior invention-policy state. Verification: `tests/test_goal_invention.py tests/test_extended_thinking_migrated.py` — 20 passed. General effect families and arbitrary program synthesis remain unsupported.

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

**P10.04 implementation record (2026-10-22):** Added opt-in `strategy_discovery` rules that preserve verified task traces as graph-held strategies and replay them only for a new task with identical domain kind, initial state, goal, and source/model/frame/probe epochs. Replay applies one graph-held ProcessSchema per step through native `ProcessApply`; unsupported/mismatched contexts do not match. The `process_solving` generator now selects a process once, stores that selection, and applies/records that same schema, fixing a trace mismatch caused by recalculating selection after state mutation. Tests cover a discovered constraint-preserving trace, native replay, delayed progress via a verified invented commutator, the invariant wall's verified odd breaker, and trace-to-state replay. Verification: `tests/test_strategy_discovery.py tests/test_goal_invention.py tests/test_invariant_walls.py` — 18 passed. General strategy transfer beyond exact initial-state/goal/epoch matches remains unsupported.


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

**P10.05 implementation record (2026-10-22):** Added deterministic 2×2×2 cube face-turn permutations and 3×3 sliding-puzzle adjacent transpositions with legality/reachability checks and exact external solved-state oracles. Seeded task records expose only initial state, goal and primitive affordances; scramble histories are discarded. `puzzle_panel` allocates 200 tasks and 100 controls by default per family. Sliding controls are parity-proven unreachable states; cube controls submit an action absent from the legal affordance set. These are world/evaluation adapters, not an agent solver or human macro library. Verification: `tests/test_pmb_puzzle_worlds.py tests/test_strategy_discovery.py` — 10 passed. No comparative solve claim is made here.

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

**P10.E1 integration record (2026-10-22):** Added `process_lifting`, `goal_invention`, and `strategy_discovery` to the cognition-on closure only; all three policies remain disabled at boot. Added profile-chain, default/conversation isolation, and shared-budget checks. A measured boot took 0.1578 s and produced 980 graph nodes and 575 rules; two ThinkingBudget nodes are attached, exactly one enabled for shared requesters. The five-suite P10 bundle passed 50 tests. Native task simulation and graph traces are verified; external physical-action receipts and allocator memory bytes are unavailable and are not claimed.

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

**P10.E2 freeze record:** V1 preregistration was frozen in [`COGNITION_LINEAR_P10_PREREG.md`](COGNITION_LINEAR_P10_PREREG.md) and retained, then its draw was invalidated because `ProcessSchemaPolicy` was disabled in the runner. Corrected V2 was frozen before a fresh allocation in [`COGNITION_LINEAR_P10_PREREG_V2.md`](COGNITION_LINEAR_P10_PREREG_V2.md). V2 self-check confirmed the primitive schemas were installed in both runnable arms, identical world-access hashes, no input leakage, native trace replay, and real per-arm outcomes. V2 development raw scorecard SHA-256: `1514550d2df274cd6223370c1a2f500643b4ac6b461674c843c3b6a6729ab75f`; analysis SHA-256: `1369affe8e78488c11017c06eef172a328bb47cca05f013c21c5bb3bd3fb5065`.

### P10.E3 — Run the frozen phase, report results and authorize the next entry

- **ID:** P10.E3
- **Tier:** T1
- **Goal:** Run the frozen phase, report results and authorize the next entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P10_PREREG_V2.md`; `evaluation/process_mastery/linear_p10_v2.py`; `evaluation/process_mastery/analyze_linear_p10_v2.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P10_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** P4 C5 negative outcome and P5 versioned corrections retained in results.
- **Steps:** 1. Run all fixed held-out arms and controls with §5 commands and archive raw hashes outside git. 2. Report every primary metric, exact work, actions, evidence exposure, memory, boot time and inherited regression exception. 3. Update this phase status and assessment; list the next phase’s supported inputs/fallbacks. Do not close an unmet safety/mechanism prerequisite.
- **Guard:** frozen artifacts; documentation closeout only.
- **Acceptance:** all stated phase criteria classified; a failed advantage remains FAIL; missing human comparison is unavailable, not parity; next entry explicitly supported.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_goal_invention.py tests/test_process_lifting.py tests/test_strategy_discovery.py tests/test_pmb_puzzle_worlds.py -q -p no:cacheprovider`.
- **Non-goals:** rerunning/tuning the same holdout; claiming a whole L-level from one mechanism panel.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

**P10.E3 result record (2026-10-22):** V2 completed 4,100 rows on its fresh registered allocation; see [`COGNITION_LINEAR_P10_RESULTS.md`](COGNITION_LINEAR_P10_RESULTS.md). On the 800 supported paired tasks, greedy and discovered-strategy both solved 128/800 (all 128 were tool-goal cases), for 0 pp gain against the ≥20 pp criterion (`FAIL`). All 100 misleading-precondition controls passed; input/trace audit failures were zero. Baseline, primitive-search and sliding panels remain `UNSUPPORTED`. The frozen P10 acceptance bundle passed 82 tests. P11 is authorized for representation proposals and cross-domain maps over verified ProcessSchema effects and acquired P7 distinctions; the failed P10 advantage remains in force and does not authorize transferable-strategy or L-level claims.

## Phase 11 — Representation invention and cross-domain transfer

**Entry:** Phase 10 lifted schemas and goal-directed invention; Phase 7 acquired qualia. **Status:** evidence closeout complete with limits; P11.01–P11.04 and P11.E1–E3 complete. Native transfer mechanism and wrong-frame/nonconjugate safety gates pass. Registered transfer benefit and L4/L5 claims remain `NOT_ESTABLISHED`; external ARC/LS20 are `UNSUPPORTED`, human comparison unavailable. Phase 12 is authorized on the supported episode-acquisition interface and must not assume fresh process-map learning.

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

**P11.01 semantic freeze (2026-10-22):** [`COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`](COGNITION_REPRESENTATION_SEARCH_CONTRACT.md) freezes representation identity, full canonical package cost, training/held-out split boundaries, forced-frame preservation, bidirectional map verification and exact-conjugation requirements. Map/decoder/exception/residual costs cannot be omitted, and held-out data can reject adoption but cannot select a proposal. Verification: `tests/test_representation_search.py tests/test_cognition_aperture_migrated.py` — 13 passed.

**P11.02–P11.E1 mechanism record (2026-10-22):** commits `b320adf1`, `a986f75e`, `6288e0d6`, `e282d20a`, `ae52c79e`, `03d2183f`, and `e9a78386` add graph-owned bounded/funded representation search, candidate minting from acquired transform evidence, native development-cost validation and training-only selection, a separate held-out adoption gate, native map inversion/composition and target-transfer gating, opt-in cognition-on profile integration, and a PMB D4 adapter with explicit ARC/LS20 unsupported status. The mechanical canonical-cost serializer rejects incomplete and non-finite packages and includes map, decoder and residual code costs. The 60-test focused bundle also covers the frozen native comparison adapter and analyzer. Live Rust-rule tests exercise the funded search, transform candidate minting, full validation sequence, frame transition, native conjugation, target receipt provenance, and wrong-frame refusal. These establish the exercised mechanisms only; transfer benefit requires the separately registered P11.E2–E3 comparison recorded below.

**P11.E2–E3 result record (2026-10-22):** implementation commit `75061e63` added native source/target adapters and analyzer; preregistration `0215137f` froze hashes, thresholds and allocation. The heldout draw completed 2,600/2,600 rows: 800 per primary arm, 100 wrong-frame controls and 100 nonconjugate controls. Source-exposed transfer verified 800/800; mismatched-source transfers were 0/800; both control adoption rates were 0/100. Pair hashes, arm coverage and input audits had zero failures. The primary ≥25% exact-check saving with ≤2 pp solve loss is `NOT_ESTABLISHED`: fresh solved 0/800 and there were zero matched solved comparisons. This is not evidence of a zero benefit or failure; the fresh adapter has no target-learning path. External ARC/LS20 remain `UNSUPPORTED`, human comparison unavailable. The 60-test acceptance bundle and both runner/analyzer self-checks pass. See [`COGNITION_LINEAR_P11_RESULTS.md`](COGNITION_LINEAR_P11_RESULTS.md) and frozen [`COGNITION_LINEAR_P11_PREREG.md`](COGNITION_LINEAR_P11_PREREG.md). Phase 12 is authorized using verified native effects and P7 episode-acquisition interfaces; fresh process-map learning is not a supported input.

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

**Entry:** Phase 11 compatible process/representation interfaces and P5 actual action authorization. **Status:** evidence closeout complete with limits; P12.01–P12.04 and P12.E1–E3 complete. The registered social-acquisition advantage is `FAIL`; explain/rebuild and safety gates pass. P13 is authorized only on verified episodes/processes and existing replay/trace interfaces, with no claim of social-learning advantage. The inherited full-boot instruction-head regression was fixed in `1226ea38` and the instruction/action-safety regression bundle passes; the unavailable verb self-repair module still needs its missing `requests` dependency before its adjacent test can run.

**P12.01 contract record (2026-10-22):** [`COGNITION_SOCIAL_ACQUISITION_CONTRACT.md`](COGNITION_SOCIAL_ACQUISITION_CONTRACT.md) freezes source attribution, witnessed versus directed versus instructed inputs, partial-visibility unknowns, body/frame mapping, three separate outcome receipts, own-grounding requirements and isolated explain/rebuild boundaries. New `tests/test_imitation_migrated.py` boundary fixtures pass 4/4; they intentionally do not claim runtime imitation. The prescribed combined verification also ran the existing instruction-understanding suite: 13 passed, one full-boot unknown-instruction-head case failed and reproduces alone. No P12 runtime behavior has been promoted on the basis of these fixtures.

**P12.02–P12.03 mechanism record (2026-10-22):** commits `486a7e5a`, `f3c9a100` and `0884156d` add opt-in graph-native demonstration candidate construction, independently funded native detached-rollout validation, failed-rollout rejection, candidate→ProcessSchema adoption with own-trial grounding kept separate, guarded response inhibition, and reuse on a new binding only after another funded rollout. Social-process rules consume verified instruction interpretations matched to an existing held ProcessSchema or incidental request/repair episodes without a teacher marker. Native counterexamples stale an adopted interpretation and create a pending, evidence-linked revision for revalidation. Focused verification: `tests/test_social_process.py tests/test_imitation_migrated.py tests/test_process_lifting.py tests/test_response_inhibition_migrated.py` — 38 passed. These are bounded graph-fixture mechanisms; no registered social-learning benefit is claimed. P12.04 and P12.E1–E3 remain open.

**P12.04–E1 update (2026-10-22):** `fb18004d` integrates explanation-only rebuild with public primitive-token matching; P12 profile integration is in `236c39a4`. The phase enables imitation, social-process, and explanation seeds only in cognition-on; all related policies remain disabled by default. The P12 integration bundle passed 52 tests before the later receipt-ownership guard. Follow-up safety commits `0a17cafe` and `d952a9f8` require agent-owned, emitted and authorized action requests with matching sink receipts before imitation or social schemas can be marked own-trial-grounded; the refreshed P12 integration bundle passed 53 tests. The initially failing full-boot instruction-understanding regression was fixed in `1226ea38` (follow-up recorded below).

**Instruction-regression follow-up (2026-10-22):** `1226ea38` fixes the full-boot hypothesis gap: an unclassified lexical Concept no longer suppresses dictionary head classification, the rule is restricted to the parsed predicate head, and a pending hypothesis prevents request-speech-act fallback from reactivating it. `tests/test_instruction_understanding_migrated.py tests/test_action_evidence_and_defer.py tests/test_embodied_instruction_goal_migrated.py` — 58 passed. An attempted adjacent run including `tests/test_verb_self_repair_migrated.py` could not collect because `.venv` lacks `requests`; no assertion result is claimed for that module.

**P12.E2–E3 result record (2026-10-22):** preregistration [`COGNITION_LINEAR_P12_PREREG.md`](COGNITION_LINEAR_P12_PREREG.md) was frozen separately at `1de4e725`; its runner, source bundle, engine-source and engine-binary hashes match the held-out runtime metadata. The fixed draw completed 1,500/1,500 records: 200 each for observation, demonstration, instruction and reward-only; 100 each for shuffled, missing and body-mismatch controls; 200 isolated rebuild receivers and 100 each for source-ID/source-expression redaction controls. The pooled social own-trial rate was 600/600 (100%), reward-only was 200/200 (100%), and the registered ≥20-point social advantage is `FAIL` (0-point gain). Rebuild adoption and held-out effect agreement were both 200/200 (100%); both redaction controls agreed 100/100. Pairing, allocation, input-audit, completion, false-grounding, unverified-adoption and control failures were all zero; each safety control had zero adoption and zero own-trial success. Mean declared evidence opportunities were 8 per social record, with 1 informative opportunity in social arms and 2 in reward-only. Social arms averaged one world action call; reward-only averaged three, including two authorized own probes and the scored trial. All arms used budget 12, averaged 2 request debits and 10 remaining; mean graph growth was 19–27 nodes / 6,218–6,802 estimated bytes for social arms and 24 nodes / 7,662 bytes for reward-only. Rebuild averaged 8 nodes / 2,774 bytes, one evidence exposure and 3 explanation tokens. Mean boot time ranged 0.0472–0.0681s across social arms and was 0.0516s for rebuild. Human comparison is unavailable, not parity. This bounded single-primitive result establishes neither social-acquisition advantage nor a capability level. P13 may use verified episodes/processes, the P1 replay scheduler and Phase 10 traces; it must treat the P12 advantage as failed and must not infer fresh process-map learning. Raw records and analyzer output remain outside git at `/tmp/linear-p12-heldout.json` and `/tmp/linear-p12-heldout-analysis.json`; SHA-256: `e8149e327ef71ea4b862345c71bb4b3b7fce7b6c59f3fa8165ab698250423789` and `ae66046c2aea0d37c44743aeafdac8999e989d6c0f3537c283664bdec2afc138`. See [`COGNITION_LINEAR_P12_RESULTS.md`](COGNITION_LINEAR_P12_RESULTS.md) and frozen preregistration. The P12 acceptance bundle and runner/analyzer self-checks pass.

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

**Entry:** Phase 12 verified episodes/processes, P1 replay scheduler and Phase 10 traces. **Status:** complete; P13.E3 classified the accuracy criterion `FAIL` and the library work criterion `PASS`. Use only verified P12 episodes/processes and existing replay/trace interfaces. P12's social-acquisition advantage failed at 0 points; this does not block mechanism work, but no social benefit may be assumed.

Merge former P6.B2 with I3.2/I3.3. Preserve the existing paced MemoryCycle producer; one owner delegates existing replay rather than running it twice. Learning is measured by later verified behavior, not support_count or number of stored schemas. Strategy-yield records supplement discovered processes without changing their verification contract.

**Registered evidence:** 200 paired learn→idle→interference→delayed-test streams with full sleep, P1 replay-only, matched-compute awake rehearsal and no-offline arms; 100 interrupt/restart controls. Primary delayed accuracy gain≥10 points over replay-only and new-task loss≤2 points; zero foreground starvation/double debit/ungrounded consolidation. Library reuse must reduce held-out primitive or exact-verifier work≥25% including retrieval and decoder overhead.

**P13.01 record (2026-10-22):** [`COGNITION_SLEEP_STAGE_CONTRACT.md`](COGNITION_SLEEP_STAGE_CONTRACT.md) freezes sole cycle ownership, delegation to the existing one-replay-per-cycle EWM owner, ordered replay→consolidate→decay→library→recombine stages, idempotency keys and receipts, shared-budget billing, foreground interruption/resumption, evidence protection and complete library cost. The new baseline boundary suite `tests/test_sleep_regime_migrated.py` passes 4/4, including single-owner/replay, foreground gating and same-epoch no-double-debit behavior; the existing scheduler suite passes 6/6. This does not claim a staged cursor or checkpoint-resume behavior: those mechanisms are explicitly open for P13.02.

**P13.02 record (2026-10-22):** `scripts/gen_sleep_regime_seed.py` and `seeds/sleep_regime.json` add an opt-in native graph lifecycle over the existing scheduler's completed `MemoryCycle`; `scripts/gen_consolidation_scheduler_seed.py` now initializes a persistent unclaimed cursor without changing the scheduler's replay owner (seed version 1.1.0). The lifecycle records the existing replay receipt, then advances one quiet-epoch stage at a time through semantic consolidation, a once-per-stage freshness/accessibility derivation on `SemanticSupport`, deferred library work, and advisory recombination. Each transition is atomic with a shared `ThinkingBudget` debit and receipt; task demand, external load, or urgency pauses before work, while insufficient budget leaves the cursor unchanged for later resumption. `WorldAdapter.save/load` retains the graph cursor and native rules; stale `SleepRegimePolicy.model_epoch` mismatch cancels pending work. The derived decay fields leave original uncertainty, source episodes, provenance and observations unchanged, and are not yet wired into retrieval. The library receipt remains explicitly deferred for P13.03; neither sleep benefit nor library savings are claimed. Cycle retention extends to 12 epochs only under the enabled sleep policy; stage receipts expire after 8 epochs. `tests/test_sleep_regime_migrated.py tests/test_consolidation_scheduler_migrated.py` — 20 passed, including stage order, once-only decay, advisory-only recombination, foreground pause, budget defer/resume, checkpoint resume, stale-model cancellation, default-off behavior and a 256-epoch bounded-growth stream. Generator reproducibility checks pass. P13.E1 still owns cognition-on profile integration; default profiles remain unchanged.

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
- **Touch:** (1) new `scripts/gen_library_learning_seed.py` + generated `seeds/library_learning.json`; (2) `runners/dsl/src/process_algebra.rs` tagged nested-sequence parsing and unit test; (3) new `tests/test_library_learning.py`.
- **Pattern to copy:** P10 structural lifting and P7 re-decode after verified growth.
- **Steps:** 1. Extract shared sub-processes from successful programs, capability traces and plans. 2. Include definition/reference/decoder/exception cost and adopt only verified reductions. 3. Rewrite stored traces with equivalence witnesses and revalidate on new states; schedule as a bounded sleep stage.
- **Guard:** LibraryLearningPolicy disabled.
- **Acceptance:** `test_shared_chunk_lowers_total_cost`, `test_rewritten_trace_same_effect`, `test_failure_evidence_preserved`, `test_later_unseen_task_reuses_chunk`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_library_learning.py tests/test_process_lifting.py tests/test_sleep_regime_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** compression through deleting failed experiences or ignoring definition cost.
- **Done when:** the specific acceptance is established and §5 has no new regressions; specs are frozen before their implementation. Record unsupported or failed capability criteria without changing them after the draw.

**P13.03 mechanism record (2026-10-22):** `LibraryLearningPolicy` is disabled by default and its graph rules consume only a deferred P13.02 `SleepStageReceipt` for stage `library`. The bounded learner considers at most 8 SolveTasks and traces of 8–32 steps. A repeated exact `SolveTask.trace` is eligible only when both tasks are solved, have the same domain and trace, and the Rust-native `ProcessRepairVerify` validates the composed process on both source initial/goal pairs. The new `ProcessSchema` stores the nested native process sequence; its cost comparison is explicit: inline `2n` references versus definition `n` + two references + decoder + exception + dispatch + retrieval + validation (`n+7`). At `n=8`, the fixture saves one declared unit. The original traces remain intact; each task also stores a one-schema `compressed_trace` and a node-valued equivalence witness. A later unseen task is solved in one step using the learned schema. Failed tasks are not rewritten or removed. An empty eligible trace set closes the deferred stage with an explicit bounded no-compression reason; a disabled policy leaves it deferred. `process_algebra.rs` accepts only an explicitly tagged nested `seq` list for the graph `MapList` output; the targeted Rust test passes. Verification: `tests/test_library_learning.py` — 5 passed; the prescribed P13.03 bundle — 24 passed. This is a mechanism pass on solver traces, not evidence of general program/capability-trace extraction or held-out library benefit; those claims remain unestablished for P13.E2/E3.

**P13.04 mechanism record (2026-10-22):** `StrategyLibraryPolicy` defaults off. It records a strategy entry only from an actually solved `SolveTask`, retaining its process-schema trace, structural signature (process kind and state/goal sizes), observed success yield and source/model/frame/probe epochs. Recall candidates must match those structural fields and current epochs; native `SoftWeights` uses only observed yield. Recall now first creates a `ThinkingBudgetRequest` tied to the task, operation identity, source/model epoch and shared `ThinkingBudget`; only an approved current-epoch request can start recall. A denied/canceled request falls back to the existing bounded solver without a retry. Each recalled process application produces a graph receipt and must make a native state change. A terminal success/failure updates observed yield; a failed recall is rejected and hands the task back to the existing bounded solver. With no compatible entry, the graph records a cold-start fallback and enables that solver. A source-domain epoch change marks the entry stale. Candidate work is counted from compatible strategy entries against active primitive process candidates; the fixture demonstrates 1 versus 2 and one-step held-out reuse. A cognition-on integration case found that a disabled default budget node could trigger the “budget disabled” fallback despite a second enabled shared budget and an approved request. The native fallback rule now requires that no enabled budget be attached; a regression test covers the duplicate-node profile. Verification: `tests/test_strategy_library.py tests/test_library_learning.py` — 11 passed after the guard; strategy seed generation is reproducible. The held-out P13 panel subsequently observed funded same-shape recall on all 200 full-sleep streams. The result is still limited to graph-held task traces.

**P13.E1 integration record (2026-10-22):** Added sleep, library-learning and strategy-library manifests to the explicit cognition-on profile and enabled their bounded policies through `cognition_on_params`; default and conversation profiles remain isolated. The three named P13 profile gates pass, and the prescribed E1 bundle passes 60 tests after the duplicate-budget fallback regression was added. The integrated profile test enters the native sleep rules from an observed episode and quiet `NetworkModeSample`, then uses `WorldAdapter.tick()` to service the scheduler request. The replay receipt is funded by that serviced request and retains `observation_status=not_observed` and `provenance_kind=offline_sleep_stage`. Raw rule-fixpoint calls alone left the request pending; the profile event adapter therefore must use the regular tick path. A profile boot measured 0.2202 s, 1,498 graph nodes and 674 rules in this run. Memory-byte growth and held-out benefit are not established; those remain E2/E3 evidence requirements.

**P13.E2 development adapter evidence (2026-10-22; not a registered draw):** Added the native `linear_p13_v1.py` runner and analyzer and validated them on three paired seeds plus one checkpoint/restart control. Each arm solved two real 32-step source tasks and a delayed task; full sleep produced a verified library chunk, solved the delayed task in one step, then recalled an observed-yield strategy on the second held-out subpanel. Replay-only, matched-compute awake rehearsal and no-offline each solved the delayed task in 32 steps. Delayed accuracy was 100% in all arms (0-point gain over replay-only), so the preregistered ≥10-point sleep accuracy criterion was predicted to fail; that threshold was not relaxed. Package-amortized exact-work reduction was 35.9375%, above the 25% library criterion. The awake rehearsal matched full-sleep native rule steps within 5%; all source/world/access hashes paired, answer/hidden-strategy audits passed, all sleep receipt provenance checks passed, and the interrupt/restart control resumed after foreground demand without a duplicate receipt or debit. The frozen held-out outcome is recorded below.

**P13.E3 held-out result (2026-10-22):** The frozen draw completed 800 paired records (200 per arm) and 100 interrupt/restart controls; raw scorecard SHA-256 is `ff22fcf0317a47bafb6305caad4df40d4cec6cc9e7692fa858ff4444f83babf8`, archived outside git. Full sleep, replay-only, awake rehearsal and no-offline each solved 200/200 delayed tasks. The primary accuracy gain was 0 points against the registered ≥10-point threshold: **FAIL**; new-task loss was 0 against the ≤2-point bound. Full sleep produced a verified library chunk and reduced package-amortized exact work by 35.9375% (20.5 vs 32 units): **PASS** against ≥25%. Funded strategy recall succeeded 200/200. All 100 controls preserved and resumed the interrupted cursor with no same-epoch duplicate receipt/debit. Pairing, primitive-access, answer/strategy, task-completion, receipt-provenance, compute-match, allocation and safety audits each had zero failures. Mean graph growth was 77 nodes/255,219 serialized bytes and boot was 0.2424 seconds for full sleep; no arm performed an external action. Human comparison is unavailable and no capability level is closed. Full metrics, provenance hashes and the supported P14 entry are in [`COGNITION_LINEAR_P13_RESULTS.md`](COGNITION_LINEAR_P13_RESULTS.md); raw scorecard and analysis remain outside git.

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

**Entry:** Phase 13 reusable verified processes and measured strategy outcomes. **Status:** complete; P14.01–P14.E3 complete. P13's accuracy advantage failed, while cost-accounted library reuse and funded same-shape strategy recall passed; do not infer a sleep retention benefit. Use only P13's verified library schemas/equivalence witnesses, observed strategy entries/application receipts, P1 replay receipts and exact task outcomes. Human comparison is unavailable. Do not close a capability level from this panel.

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

**P14.01 completion record (2026-10-22):** Froze [`COGNITION_PROOF_OPERATOR_CONTRACT.md`](COGNITION_PROOF_OPERATOR_CONTRACT.md) before implementation. It separates empirical regularities, conjectures and checked theorems; binds proof references to statement, assumptions, checker, family/model and epochs; makes unsupported cases fail closed; and prohibits candidate operators from changing the verifier, criteria, evaluation or approval boundary. Human promotion gates remain in force and policies remain disabled by default. The four contract acceptance tests pass, as do the prescribed P14.01 bundle (17 passed). An additional run including `test_theorems_as_terms_migrated.py` yielded 20 passed and five environment errors because `python-chess` is absent; no implementation test was required for this specification task.

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

**P14.02 completion record (2026-10-22):** Added disabled-by-default `process_laws` policy and generated `seeds/process_laws.json`. Its sole checked fragment is an exact permutation commutator: two active same-domain permutation arguments, the exact native `ProcessCommutator` result, fixed statement/assumption digests and matching family/model/process epochs are all required before a `LawProofReference` is attached. Finite-sample candidates with counterexamples are rejected; a validated later counterexample downgrades a checked law while retaining its proof reference as history. No broad theorem proving or sampled-invariant promotion is implemented. Verification: P14.02 bundle — 13 passed, including false finite-sample, family-binding, exact-constructor and counterexample controls. The checker is the bounded graph-resident structural rule, not a general proof kernel; P14.03 must preserve this scope.

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

**P14.03 completion record (2026-10-22):** Added disabled-by-default proof-adoption policy and explicit `ProcessProofRequirement` registration. In a registered domain, invented permutation processes enter `proof_blocked` unless a checked `commutator_even` law and proof reference bind the exact process parameters, family/model digests, statement/assumption digests and source/model/frame epochs. Changed process parameters or domain identity epochs invalidate adoption and remove the process from active use. Domains without a requirement are unaffected. The gate sets external-action authorization to zero and leaves any pending action request untouched. Verification: P14.03 bundle — 13 passed, including no-requirement, wrong-process proof, changed-process invalidation, and external-action separation controls. This supports only the narrow P14.02 parity proof fragment.

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

**P14.04 completion record (2026-10-22):** Added disabled-by-default graph-authored operator proposals and promotion rules. The bounded `commutator_square_v1` candidate is represented as an expression graph over held `compose` and `commutator` operators; unsupported composition requests fail closed. Only development-split measurements can qualify a candidate, requiring positive yield over its parent, unchanged invariant-check count, zero proof failures and nonnegative work within the cap. Qualification waits for an explicit human approval carrying the frozen criteria digest. Promotion retains both the source candidate and a direct parent-operator rollback edge. The rules do not write verifier, criterion, or evaluation state. Verification: P14.04 bundle — 9 passed. Actual sandbox development and untouched held-out measurement remain P14.E2 requirements; this mechanism test does not claim efficacy.

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

**P14.E1 completion record (2026-10-22):** Added the law, proof-adoption and invention-authorship seeds to the cognition-on profile and explicitly enabled their policies through `cognition_on_params`; default and conversation profiles remain isolated. The profile integration path now mints a graph-authored combinator, checks an exact permutation commutator law, records a provenance-linked `LawProofReference`, admits only the process covered by that proof, and blocks an unproved process in the registered domain. It confirms one enabled shared ThinkingBudget. Profile boot measured 0.2016 s, with 1,504 nodes, 1,249 edges, 686 rules and 284,610 serialized graph bytes; process max-RSS high-water increased 39,360 KiB from pre-boot measurement (includes imports/runtime). The proof reference records checker `process_laws_seed_v1`, statement/assumption digests and matching family/model/process/frame epochs. Verification: prescribed P14.E1 bundle — 56 passed. No held-out efficacy claim is made; proceed to preregistration.

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

**P14.E2 completion record (2026-10-22):** Added the paired native adapter/analyzer and froze corrected preregistration revision 1 in commit `d288dae2`. The initial freeze `21d9ecda` is explicitly superseded before any held-out run because the analyzer lacked fingerprint/seed enforcement and proof-reference binding audit; no held-out records were run or inspected under that freeze. The registered draw is 200 paired one-call permutation macro tasks, 200 structural/false-finite-sample law claims and 100 proof-reference/criteria tampering controls. Both self-checks pass. Development run (10 paired tasks, 20 law cases, 10 controls) produced candidate 10/10 versus held operator 0/10, 20/20 correct law classifications, 10/10 passed tamper controls, no hash/pair/input/invariant failures; the eight-task development qualification was positive (8/8 vs 0/8) with 8/8 invariant checks and 32/32 work units, and remained `awaiting_human`. No held-out records were used. The prescribed focused regression bundle passes 56 tests. Frozen component hashes are in the corrected preregistration.

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

**P14.E3 completion record (2026-10-22):** Executed the corrected revision-1 held-out draw once and analyzed it against the frozen protocol. The authored `commutator_square` operator solved 200/200 one-call tasks versus 0/200 for the held operator (+100 pp; `PASS` against ≥20 pp), using four work units per task versus one. All 100 structural laws checked with binding proof references; all 100 false finite-sample claims were rejected; all 100 proof-reference/criteria tampering controls failed closed. Pairing, hashes/access, input audits, proof bindings, work accounting, allocation, provenance and external-action checks had zero failures. Runner and analyzer self-checks pass; the prescribed E3 regression bundle passes 18 tests, and the earlier broader E1 focused bundle passes 56 tests. Full results and raw hashes are in [`COGNITION_LINEAR_P14_RESULTS.md`](COGNITION_LINEAR_P14_RESULTS.md); raw records remain outside git. At the time of closeout the candidate was `awaiting_human`; the following authorization update supersedes that entry-gate status. Human comparison remains unavailable; no capability level is closed.

**P14 promotion authorization update (2026-10-22):** In response to the explicit approval request, the user approved `commutator_square_v1` under `pmb-v1-frozen-criteria`. This is a human approval scoped to that candidate and digest. The runtime graph does not yet contain an `OperatorPromotionApproval` node, so the operator remains unpromoted until P15.04 materializes this authorization through the existing graph gate. No approval is implied for later candidates.

## Phase 15 — Scaled portfolios self-curriculum and repeated improvement

**Entry:** Phase 14 proof/adoption machinery and approved candidate operator workflow. **Status:** P15.01–P15.04 and P15.E1–E3 complete. The user explicitly approved `commutator_square_v1`, `commutator_cube_v2`, and `commutator_fourth_v3`, each under `pmb-v1-frozen-criteria`; later candidates still require their own approval. The registered trend criterion was not established, and no capability level is closed.

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

**P15.04 completion record (2026-10-22):** Added a graph-owned recursive generation lifecycle around the existing P14 candidate/proof/approval machinery. A development-qualified graph-authored candidate is recorded as a pending child of an immutable frozen ancestor, with a candidate edge and fixed work budget. It must reserve the complete generation ceiling through one shared ThinkingBudget request before a human-approved operator can remain active; a denied reservation suspends the operator. Promotion still requires the existing explicit approval event with the exact candidate and frozen digest. Failed proof-binding, adoption, grounding or action-safety audits suspend the active operator, record rollback to its direct ancestor and invalidate the autonomy claim. Human-edited candidates invalidate their generation claim. Native graph snapshot/restore preserves generation ancestry, budget and pending identities. Verification: prescribed P15.04 bundle passes 17 tests, covering complete ancestry, graph authorship, failed qualification, shared-budget denial, invariant rollback and restart persistence. Subsequent adapter development exercises graph-authored successor proposals for v2 and v3; v2's approval event is scoped to its exact candidate and digest, while v3 remains independently gated. This mechanism does not establish the preregistered multi-generation evaluation.

**P15.E1 completion record (2026-10-22):** Added process portfolio, process curriculum and recursive improvement to the explicit cognition-on profile. Their policies remain disabled in that profile by default, and the default and conversation profiles still load none of these manifests. The profile integration test enables only the curriculum policy, supplies an observed training transition, and verifies native task/evidence/funding receipts against the one attached ThinkingBudget; P15.02 and P15.04 focused tests exercise the other native paths. Fresh cognition-on boot measured 0.2015 s, 1,510 graph nodes and 286,374 serialized graph bytes in this test environment. The shared-budget integration test confirms one enabled budget across all three policies; the broader P15.E1 bundle passes 61 tests. The evaluator-family adapters and preregistered three-generation run have not yet been frozen or executed.

**P15 approval update (2026-10-22):** The user approved `commutator_cube_v2`, then approved all in response to the separate measured-candidate request for `commutator_fourth_v3`; each approval is under `pmb-v1-frozen-criteria` and scoped to its candidate. The development adapter materializes each as an `OperatorPromotionApproval` event and verifies activation through the generation gate. No approval is inferred for any successor candidate.

**P15.E2 development status (2026-10-22):** The finite-permutation process-macro adapter produces paired native `ProcessApply` outcomes for all three arms and all three approved generations. The eight-task development panel completed 24 paired task worlds with zero integrity failures: full system 24/24, unchanged operator 7/24, adaptive curriculum 7/24. Per-generation outcomes were 8/8 vs 0/8, 8/8 vs 3/8, and 8/8 vs 4/8 for full system versus unchanged operator. Paired bootstraps report +2.0 full-system work units per task on average (95% interval [1.67, 2.33]) and no resolved latency difference. The preregistered conditional-logistic generation slope is not estimable on this development panel due singular conditional information; this is not trend evidence. Candidate selection checks recorded v1 2/2 vs 0/2, v2 2/2 vs 0/2 and v3 2/2 vs 0/2, each with eight invariant checks and candidate work 8/12/16. The v1/v2/v3 approvals are separately materialized with the exact frozen digest. Runner/analyzer self-checks pass and the focused P15 bundle passes 70 tests. E2 froze as preregistration commit `e0483bc2`; the committed hash table matches all evaluated artifacts.

**P15.E3 result record (2026-10-22):** The single frozen draw completed all 1,800 rows (200 tasks × three generations × three arms) and 100/100 preregistered tampering controls, with zero scored-row integrity failures. Full system solved 600/600; unchanged and adaptive each solved 196/600. By generation, full versus unchanged solved 200/200 vs 0/200, 200/200 vs 56/200, and 200/200 vs 140/200; the paired gap narrows from 100 to 72 to 30 points as the unchanged operator increasingly matches the power-specific target. Adaptive curriculum exactly matches unchanged. The primary conditional-logistic trend fit is not estimable due complete/near-complete separation, so the registered positive-trend criterion is NOT_ESTABLISHED; the per-generation exact McNemar results do not replace it. Full system used +2.0 work units/task on average (95% paired-bootstrap interval [1.9367, 2.0650]); the tiny measured latency interval is not interpreted as a practical gain. There were no actions, invariant failures, budget overruns, input leaks, pairing errors or provenance mismatches. Full results and raw hashes are in [`COGNITION_LINEAR_P15_RESULTS.md`](COGNITION_LINEAR_P15_RESULTS.md); raw records remain outside git. Phase 15 closeout is complete with the trend criterion NOT_ESTABLISHED (the registered pass condition was not met), no L-level closed. The subsequent user-requested review authorizes planning Phases 16–22; P16.01 is the next implementation entry. The native-binary fingerprint and scored execution-path qualifications in the post-P15 review remain mandatory.

**P15.03 completion record (2026-10-22):** Added generated `process_curriculum` rules for observed training counterexamples, frozen training representation residuals, contested acquired distinctions and stale strategy successes checked against a fresh zero-step training task. Curriculum tasks are emitted only after shared ThinkingBudget approval, with training split, unknown expected outcome, source epochs, one attempt and no answer/held-out fields. One evidence/task funding lock serializes admissions; policy is disabled by default and caps evidence at 512 and tasks at 256. Unlearnable outcomes suppress their exact source key; progress resolves it; epoch/deadline mismatch marks it stale. The scheduler can mark a new zero-step task stuck before the background rule runs, so the stale-success check accepts that state while still rejecting progressed tasks. Verification: prescribed P15.03 bundle passes 15 tests. No §5 regression identified in this bundle. P15.04 is next; curriculum coverage does not establish an improvement in task success.

**P15.01 completion record (2026-10-22):** Froze [`COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`](COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md) and added its PMB evaluation boundary. The contract defines immutable generation ancestry and rollback, three matched arms, per-candidate human approval, at least three generations with ≥200 fresh matched evaluation tasks per family/generation/arm, disjoint deterministic seed allocation, paired trend analysis with Holm correction, zero-tolerance safety invariants, shared work/memory ceilings, deterministic parallel folding, and the unsupported human-baseline disposition. Exact work uses the shared native ThinkingBudget; E2 must bind its numeric configuration and final family adapters before preregistration. No human comparison is available or presumed. The user approval for the initial P14 candidate is recorded above and remains scoped; runtime graph promotion is deferred to P15.04. Verification: prescribed P15.01 bundle passes. P15.02 is next.

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

**P15.02 completion record (2026-10-22):** Added generated `process_portfolio` policy/seed for graph-authored bounded partition batches. The graph reserves each batch's aggregate cost with one shared `ThinkingBudget` request, admitting only one batch at a time to avoid same-settlement double debits; only approved batches become `CognitiveTask` partitions. The existing `CyclePlan::AreaParallel` and native ordered result fold execute independent `vector_sum` evidence reductions, while graph rules own funding, worker caps, terminal receipts, denial and cancellation state. Policy remains disabled by default. The batch ceiling is 64 partitions and 100,000 aggregate work units, with the cognitive area capped at four workers. No `cognitive_cycle.rs` change was needed because the existing plan already provides bounded worker scheduling and deterministic folding. Verification: P15.02 bundle passes 16 tests, including serial/parallel equivalence, insertion-order-independent fold, within-batch and cross-batch budget exhaustion, cancellation receipt retention, worker-cap enforcement and shared ThinkingBudget regression coverage. P15.03 is next; this infrastructure does not itself establish an improvement in task success.

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


## Post-P15 extension — acquisition and end-to-end capability

**Added:** 2026-10-22 after [the P15 source/results review](COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md). Phases 0–15 remain closed reporting cycles with their recorded limits. Execute **16 → 17 → 18 → 19 → 20 → 21 → 22**, using the same task contract. This extension addresses missing behavioral connections and experiment validity before adding another layer of self-improvement claims. No implementation or new held-out run was performed by this planning update.

A failed advantage can be an informative result. It cannot retire the underlying missing native execution, unsupported comparator or absent acquired-axis consumer. Each phase below has explicit structural prerequisites; these must pass before advancing. Benefit hypotheses remain honest pass/fail/unestablished outcomes, and the next entry names any supported fallback. Preserve earlier preregistrations and all their negative outcomes.

## Phase 16 — Native execution provenance and valid comparators

**Entry:** P15 reporting closed at `41bb53fe`; current dirty native artifacts are excluded from new freezes. **Status:** P16.E1–E3 complete under corrected v2; the v1 freeze was invalidated before interpretation. P17 is now the next entry.

**Reason:** P15 hashes the wrapper as the binary, selects the scored process in Python, and aligns targets to the active macro. Establish the actual decision/execution boundary and artifact identity before any new learning claim.

**Registered evidence to freeze:** Conformance phase: 200 independent goals each in permutation and finite state-dependent tool worlds; 100 controls each for missing/stale/tampered expression, wrapper/native mismatch and unauthorized emission. Required: 100% agreement of instrumented native execution with the externally scored world, zero stale/unauthorized execution, zero missing adapters and exact loaded-extension attestation. Success-rate differences are descriptive here; a correct primitive comparator may legitimately fail hard goals.

### P16.01 — Freeze the post-P15 validity and support contract

- **ID:** P16.01
- **Tier:** T1
- **Goal:** Freeze the post-P15 validity and support contract.
- **Read first:** `evaluation/process_mastery/linear_p15_v1.py::_run_task`; `evaluation/process_mastery/linear_p15_v1.py::provenance`; `scripts/gen_invention_operator_authorship_seed.py::build`; `scripts/gen_recursive_process_improvement_seed.py`; `docs/research/engine_substrate/COGNITION_PROCESS_EXECUTION_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Pattern to copy:** source-bound action authorization and P15 review findings.
- **Steps:** 1. Define agent-owned candidate selection/expression evaluation/world action/receipt boundaries and prohibit arm-specific host process construction. 2. Enumerate process/view/comparator support and exact versus predicted effects. 3. Specify causal knockout/mutation controls, real artifact attestations and end-to-end resource counters.
- **Guard:** specification only.
- **Acceptance:** every scored agent operation has a native owner; all opaque/unsupported forms and missing baselines explicitly listed; original P15 outcomes unchanged.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_linear_p15_adapter.py -q -p no:cacheprovider`.
- **Non-goals:** patching a frozen runner or declaring historical binary provenance reconstructed from a commit.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P16.02 — Attest the loaded native extension and frozen dependency closure

- **ID:** P16.02
- **Tier:** T2
- **Goal:** Attest the loaded native extension and frozen dependency closure.
- **Read first:** `evaluation/process_mastery/linear_p15_v1.py::provenance`; `runners/dsl/python/substrate_rs/__init__.py`; `tests/test_engine_provenance_migrated.py`; `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`.
- **Touch:** new `evaluation/process_mastery/runtime_attestation.py`; new `tests/test_runtime_attestation.py`; new `docs/research/engine_substrate/COGNITION_PROVENANCE_REVIEW.md`.
- **Pattern to copy:** existing engine build metadata and repository failure-baseline accounting.
- **Steps:** 1. Hash the actually loaded native module path separately from wrapper/source/build metadata. 2. Bind imported symbols to that module and reject stale/dirty/unavailable attestation for a new freeze; allow clearly labeled development only. 3. Audit earlier runner fingerprint code, classify which artifacts can be proven and retain unrecoverable execution-time provenance as unknown.
- **Guard:** read/check only; no engine rebuild in this task.
- **Acceptance:** `test_hashes_loaded_extension_not_wrapper`, `test_native_change_breaks_freeze`, `test_same_wrapper_different_native_rejected`, `test_missing_build_receipt_unknown`; previous reports not silently rehashed.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_runtime_attestation.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** copying a native library, pretending the current dirty build proves the archived runtime, or changing historical hash tables.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P16.03 — Execute graph-selected operator expression data end to end

- **ID:** P16.03
- **Tier:** T2
- **Goal:** Execute graph-selected operator expression data end to end.
- **Read first:** `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`; `scripts/gen_invention_operator_authorship_seed.py`; `runners/dsl/src/process_algebra.rs`; `seeds/process_solving.json`; `tests/test_recursive_process_improvement.py`.
- **Touch:** new `scripts/gen_native_process_execution_seed.py` + `seeds/native_process_execution.json`; new `tests/test_native_process_execution.py`; `runners/dsl/src/process_algebra.rs` only if existing composition Terms cannot evaluate the declared expression.
- **Pattern to copy:** native ProcessApply and graph-owned pre/action/receipt lifecycle.
- **Steps:** 1. Select a current eligible process through graph rules and evaluate its actual expression/source reference. 2. Emit a proposed world action through authorization and ingest the externally computed result; no Python arm switch selects the process. 3. Meter expression traversal/composition/application and failed proposals; mutation/deletion of the active operator must affect the very next scored execution.
- **Guard:** NativeProcessExecutionPolicy disabled; existing approval and sink rules preserved.
- **Acceptance:** `test_graph_selected_expression_reaches_world`, `test_mutated_expression_changes_outcome`, `test_missing_expression_abstains`, `test_revocation_blocks_execution`, `test_meter_includes_composition`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_native_process_execution.py tests/test_recursive_process_improvement.py -q -p no:cacheprovider`.
- **Non-goals:** applying a host-computed equivalent process while merely checking that an approved operator exists.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P16.04 — Complete working primitive-search and legal world adapters

- **ID:** P16.04
- **Tier:** T2
- **Goal:** Complete working primitive-search and legal world adapters.
- **Read first:** `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/puzzle_worlds.py`; `seeds/cognition_planner.json`; `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`; `tests/test_pmb_puzzle_worlds.py`.
- **Touch:** `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/puzzle_worlds.py`; new `tests/test_native_world_comparators.py`.
- **Pattern to copy:** P5 bounded graph search and P10 affordance-installation correction.
- **Steps:** 1. Expose the same goal, primitive actions, state-dependent legality and world transition protocol to baseline/search/learned arms. 2. Install an actual native primitive-search policy with explicit frontier/budget and enforce sliding blank adjacency; split out a ≤3-file seed task first if no existing planner expression suffices. 3. Exercise known solvable and unsolvable development cases and supported finite transition receipt adapters; keep unimplemented capability/motor views explicitly opaque.
- **Guard:** explicit evaluator profiles; policy decisions remain native.
- **Acceptance:** `test_primitive_search_executes_real_path`, `test_equal_primitive_access`, `test_illegal_sliding_move_rejected`, `test_failed_search_not_missing_adapter`, `test_observed_receipt_matches_world`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_native_world_comparators.py tests/test_pmb_puzzle_worlds.py tests/test_native_process_execution.py -q -p no:cacheprovider`.
- **Non-goals:** supplying a solution trace or falsely reporting missing physical/capability models as implemented.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P16.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P16.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate attested native process execution and comparator interfaces with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p16_native_causal_chain`, `test_p16_state_perturbation_changes_execution`, `test_p16_default_isolation`, `test_p16_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_runtime_attestation.py tests/test_native_process_execution.py tests/test_native_world_comparators.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P16.E2 — Freeze an informative matched-arm evaluation

- **ID:** P16.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p16_v1.py`; new `evaluation/process_mastery/analyze_linear_p16_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P16_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_runtime_attestation.py tests/test_native_process_execution.py tests/test_native_world_comparators.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P16.E3 — Report all outcomes and decide the next supported entry

- **ID:** P16.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P16_PREREG.md`; `evaluation/process_mastery/linear_p16_v1.py`; `evaluation/process_mastery/analyze_linear_p16_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P16_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_runtime_attestation.py tests/test_native_process_execution.py tests/test_native_world_comparators.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**Implementation record (2026-10-22):** P16.01's native evidence contract was frozen in `0efb5c4f`. P16.02 adds `runtime_attestation.py` and a provenance review: new freezes distinguish the package wrapper from the loaded extension and require a matching build receipt; focused tests cover wrapper/native divergence, changed bytes and missing receipts. P16.03 adds a disabled-by-default graph selector, evaluates the selected expression through native process terms, obtains a shared ThinkingBudget debit before evaluation, and sends only the resulting proposal through the authorization/world-receipt boundary. Mutation, missing-expression, revocation, work-meter and world-receipt tests pass. P16.04 connects the existing graph-resident bounded planner to finite sliding and tool world adapters; complete transition models distinguish a real exhausted search from an unknown/incomplete model, and the sliding search executes through the world-owned legal-action/receipt adapter. P16.E1 installs the policy in cognition-on only, keeps it disabled at profile boot, and passes default/conversation isolation and shared-budget integration checks. The P16 focused bundle passed 74 tests; cognition profile integration and Track I foundation passed 46 tests.

P16.E2/E3 remain open. No P16 runner, analyzer, standalone preregistration, or sealed evaluation has been frozen or run. The currently loaded extension is `16b94f563be757ad9293e4921864466052d02e3fa07102ecff9e014b0b76a12b`, while the tracked native artifact is `a6ec6b37db89ad17fef19c7231ecf3531f8771a8ccf82b0b872bf19227f816e7`; the user-dirty build receipt describes the loaded bytes but cannot establish a clean freeze. Preserve both historical P15 results and the dirty generated artifacts. Do not enter P17 until a clean, matching loaded-native artifact is available, P16.E2 is frozen after development self-checks, and P16.E3 reports its registered outcomes.

**P16.02 attestation correction (2026-10-22):** Commit `0246b0bb` fixes two fail-closed attestation defects found while preparing a clean artifact: the public Python `Substrate` wrapper was compared to the native class instead of `_NativeSubstrate`, and cleanliness was checked against the caller checkout instead of the loaded package's source worktree. The build receipt's exact extension digest and full Rust source closure are now verified; cleanliness covers the wrapper and every build input while allowing the sanctioned generated extension/receipt outputs to differ from checked-in placeholders. The isolated artifact built from commit `0246b0bb` attested `ATTESTED` with bound native symbols, matching source closure, extension SHA-256 `b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1`, and receipt SHA-256 `6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1`. The 121-test P16/profile regression bundle passed. This establishes a buildable attested artifact for development; E2's complete runner/analyzer, source bundle freeze, and sealed allocation remain unimplemented, so P16.E2/E3 remain open and P17 is not authorized.

Regression verification (2026-10-22): `failure_baseline.py verify --list results/cognition_gate_baseline.json` reports the existing four held reds, zero stale listed failures and zero new failures. The 20-file sweep wrote `/tmp/cognition-linear-gate.json`: 16 GREEN, two RED already represented by the frozen baseline (frozen core invariant and dual-process core), one timeout classified `NOT_ESTABLISHED` at 420 seconds (`test_capability_control_fabric_migrated.py`), and one all-skipped file. The broad P16/profile regression bundle passed 121 tests. No baseline entry was changed.

**P16.03 source-binding correction (2026-10-22):** The audit found that `execute_selected` still accepted process values as host-supplied Python arguments and composed the expression in Python. Commit `774e6cbb` moves source IDs into the graph-selected request, checks agent ownership, task domain, active status, source epoch and value digest, and evaluates the graph-authored `native_term` directly in Rust. The expression-graph witness and native-term digest are checked before evaluation; missing, stale, foreign or mutated inputs abstain. Unauthorized proposals are verified not to reach the world adapter. Verification: 129 focused P16/profile/Track-I tests passed. This repairs the mechanism path but does not substitute for the P16 matched-arm runner, frozen allocation or results ledger.

**P16.E2/E3 v2 closeout (2026-10-22):** Commit `cbed5182` adds the matched conformance runner/analyzer and finite one-step permutation/state-dependent-tool panels. The v1 standalone freeze was committed as `756d7db3`, but its build-receipt digest was malformed (61 characters); the held-out raw file was preserved and the analyzer correctly rejected it before reporting. V1 outcomes are not interpreted. Commit `18edc116` versions the protocol and uses a fresh held-out offset; corrected standalone freeze `COGNITION_LINEAR_P16_V2_PREREG.md` was committed alone as `0cfc5765` before the new draw. The v2 held-out allocation passed: 800/800 rows completed, all 400 paired worlds matched, all 800 receipts verified, all 500 fault controls passed and all five tamper probes detected changes. Depth-1 primitive search solved 400/400 versus 25/400 graph-expression outcomes; success differences are descriptive and do not establish strategy quality. The exact native extension attested `ATTESTED`. See [`COGNITION_LINEAR_P16_RESULTS.md`](COGNITION_LINEAR_P16_RESULTS.md) and the standalone freeze for raw hashes and limits. P17 entry is permitted only for the behavioral/qualia question and remains bounded by these results; no capability level closes.

## Phase 17 — Qualia that changes later inference action and significance

**Entry:** P16 attested native execution, P7 episode acquisition and P8 counterexample records. **Status:** P17.E1–E3 complete under corrected v2; v1 was rejected before interpretation. P18 is the next supported entry.

**Reason:** P7 validates feature-associated candidate axes without demonstrating a downstream action/prediction consumer, standing significance, general dimension search or retirement. Close that learning loop rather than adding more declaration nodes.

**Registered evidence to freeze:** 200 fresh later-task worlds each for tool/contact and incidental social request/repair, with acquired/frozen/shuffled/no-experience arms plus 100 orthogonal and reversal controls per family. Native causal use is mandatory: acquired-axis knockout must remove the traced contribution or provoke abstention; unperturbed source truth remains fixed. Primary proposed gain≥20 pp on later prediction/action at equal exposure/compute, zero wrong-source acceptance, and recovery after real counterexamples. A failed gain remains a failure even if axis counts increase.

### P17.01 — Specify behavioral consumers and learned significance without answer axes

- **ID:** P17.01
- **Tier:** T1
- **Goal:** Specify behavioral consumers and learned significance without answer axes.
- **Read first:** `docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md`; `scripts/gen_qualia_acquisition_seed.py`; `scripts/gen_experience_signature_seed.py`; `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`; `tests/test_qualia_acquisition.py`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_QUALIA_BEHAVIOR_CONTRACT.md`; new `tests/test_qualia_behavior.py`.
- **Pattern to copy:** P7 source-grounded witnesses and dimension/aperture distinction.
- **Steps:** 1. Define which prediction, attention allocation and action affordance changes can be justified by acquired distinctions. 2. Separate episode fact, empirical prediction, live relevance and standing significance with support/counterexamples. 3. Prohibit fixtures from naming target axes or writing positive significance; preserve missing-dimension versus finer-grain tests.
- **Guard:** new qualia behavior policies disabled.
- **Acceptance:** planned `test_no_target_dimension_input`, `test_axis_has_native_consumer`, `test_significance_has_outcome_witness`, `test_unknown_feature_not_false_zero`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_acquisition.py tests/test_experience_signature.py -q -p no:cacheprovider`.
- **Non-goals:** equating a validated dimension node or supplied valence with behavioral acquisition.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P17.02 — Use acquired dimensions in native predictions and action proposals

- **ID:** P17.02
- **Tier:** T2
- **Goal:** Use acquired dimensions in native predictions and action proposals.
- **Read first:** `docs/research/engine_substrate/COGNITION_QUALIA_BEHAVIOR_CONTRACT.md`; `seeds/qualia_acquisition.json`; `seeds/experience_signature.json`; `seeds/native_process_execution.json`.
- **Touch:** new `scripts/gen_qualia_behavior_seed.py` + `seeds/qualia_behavior.json`; `tests/test_qualia_behavior.py`.
- **Pattern to copy:** native hypothesis query/goal proposal and source-bound recall.
- **Steps:** 1. Project acquired coordinates for fresh observations through verified frame bindings. 2. Let the native consumer propose discriminating predictions or actions, with source evidence and uncertainty. 3. Recheck outcomes through P16; test dimension knockout/permutation without altering external goals or scorer data.
- **Guard:** QualiaBehaviorPolicy disabled; inference/action funded.
- **Acceptance:** `test_acquired_axis_changes_new_prediction`, `test_axis_knockout_blocks_supported_action`, `test_frozen_space_receives_same_experience`, `test_wrong_owner_axis_hidden`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_behavior.py tests/test_native_process_execution.py -q -p no:cacheprovider`.
- **Non-goals:** a host classifier deciding which learned feature should determine the answer.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P17.03 — Learn context-sensitive significance from verified consequences

- **ID:** P17.03
- **Tier:** T2
- **Goal:** Learn context-sensitive significance from verified consequences.
- **Read first:** `docs/research/engine_substrate/COGNITION_QUALIA_BEHAVIOR_CONTRACT.md`; `seeds/qualia_behavior.json`; `seeds/core_emotions.json`; `seeds/cognition_aperture.json`.
- **Touch:** new `scripts/gen_experiential_significance_seed.py` + `seeds/experiential_significance.json`; new `tests/test_experiential_significance.py`.
- **Pattern to copy:** existing standing/live CAN distinction and P8 evidence-supported experiment choice.
- **Steps:** 1. Decode recurring consequence structures into context-bound relevance/affordance records, retaining favorable and adverse outcomes. 2. Use those records to allocate attention or propose sufficient interventions without converting coherence into truth. 3. Require standing significance to be supported over episodes and contexts; reversals remain evidence, not erased exceptions.
- **Guard:** ExperientialSignificancePolicy disabled; no new arbitrary learning-rate schedule.
- **Acceptance:** `test_significance_earned_from_outcomes`, `test_same_feature_different_context_distinguished`, `test_relevance_changes_attention`, `test_confident_wrong_prediction_rechecked`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_experiential_significance.py tests/test_qualia_behavior.py -q -p no:cacheprovider`.
- **Non-goals:** a universal scalar good/bad ranking or hard-coded salience answer.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P17.04 — Revise split and retire acquired distinctions under counterevidence

- **ID:** P17.04
- **Tier:** T2
- **Goal:** Revise split and retire acquired distinctions under counterevidence.
- **Read first:** `docs/research/engine_substrate/COGNITION_QUALIA_BEHAVIOR_CONTRACT.md`; `scripts/gen_qualia_acquisition_seed.py`; `seeds/experiential_significance.json`; `tests/test_qualia_dimension_compensation_migrated.py`.
- **Touch:** `scripts/gen_qualia_acquisition_seed.py` + `seeds/qualia_acquisition.json`; `scripts/gen_qualia_behavior_seed.py` + `seeds/qualia_behavior.json`; new `tests/test_qualia_revision.py`.
- **Pattern to copy:** P8 disputed hypotheses and epoch invalidation.
- **Steps:** 1. Accumulate exact counterexamples and distinguish changed context from a failed axis. 2. Fund bounded grain/transform/new-dimension alternatives; split only with verified evidence. 3. Retire unsupported candidate influence, preserve all historical witnesses and invalidate dependent recall/plans.
- **Guard:** qualia policies explicitly enabled; terminal leases restored.
- **Acceptance:** `test_counterexample_removes_stale_influence`, `test_context_split_verified`, `test_retired_axis_cannot_drive_action`, `test_orthogonal_information_not_manufactured`, `test_save_load_preserves_revisions`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_revision.py tests/test_qualia_behavior.py tests/test_qualia_dimension_compensation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** silently deleting disconfirming episodes or broadening tolerance to make every outcome match.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P17.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P17.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate behavioral qualia acquisition, significance and revision with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p17_native_causal_chain`, `test_p17_state_perturbation_changes_execution`, `test_p17_default_isolation`, `test_p17_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_behavior.py tests/test_experiential_significance.py tests/test_qualia_revision.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P17.E2 — Freeze an informative matched-arm evaluation

- **ID:** P17.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p17_v1.py`; new `evaluation/process_mastery/analyze_linear_p17_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P17_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_behavior.py tests/test_experiential_significance.py tests/test_qualia_revision.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P17.E3 — Report all outcomes and decide the next supported entry

- **ID:** P17.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P17_PREREG.md`; `evaluation/process_mastery/linear_p17_v1.py`; `evaluation/process_mastery/analyze_linear_p17_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P17_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_behavior.py tests/test_experiential_significance.py tests/test_qualia_revision.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P17.E3 closeout (2026-10-22):** P17 v1's held-out raw scorecard was preserved but rejected before interpretation because the preregistered build source fingerprint contained a transcription error. The v2 protocol and preregistration were frozen independently with held-out offset +2,000,000. The single v2 allocation passed all registered gates: 1,600/1,600 paired-arm rows, 400/400 controls, 5/5 tampering probes, exact loaded-native provenance, and zero structural failures. Acquired prediction/action success was 200/200 in each family versus 0/200 for frozen, shuffled and no-experience controls (+100 pp per comparator, above the registered +20 pp threshold). The result supports only source-bound behavioral use of acquired distinctions in the specified finite simulator families; it does not establish real-world qualia, consciousness, human-relative significance or general strategy. P18 entry is supported for observation-built models and verified simulator experiments; no capability level closes. See [`COGNITION_LINEAR_P17_RESULTS.md`](COGNITION_LINEAR_P17_RESULTS.md), [`COGNITION_LINEAR_P17_PREREG.md`](COGNITION_LINEAR_P17_PREREG.md) and [`COGNITION_LINEAR_P17_V2_PREREG.md`](COGNITION_LINEAR_P17_V2_PREREG.md).

## Phase 18 — Observation-built world models and real experiment consequences

**Entry:** P17 behavioral distinctions and P16 real simulator receipts. **Status:** P18.E1–E3 complete; conformance passed and registered comparative efficacy is NOT_ESTABLISHED. P19's model-view entry is supported with that limit.

**Reason:** P8 selected among supplied hypotheses and revised finite graph fixtures. Build candidate mechanisms from observed traces and run graph-chosen interventions against independent world dynamics; a simulator transition is real to that declared world but is not a physical-world claim.

**Registered evidence to freeze:** 200 object-mechanism worlds and 200 partially observed temporal worlds; learned/held-vocabulary-search/passive/fixed-probe arms at equal world access and interaction budgets, 100 ambiguous/missing/irregular controls each. Primary ≥20 pp held-out effect/continuation prediction gain or ≥25% fewer interventions with solve loss≤2 pp. Require no supplied transition hypotheses/answer feature and at least 100 actual simulator-result-linked refinements; unsupported model classes abstain.

### P18.01 — Specify an observation basis and model search without supplied hypotheses

- **ID:** P18.01
- **Tier:** T1
- **Goal:** Specify an observation basis and model search without supplied hypotheses.
- **Read first:** `docs/research/engine_substrate/COGNITION_MODEL_LEARNING_CONTRACT.md`; `scripts/gen_process_induction_seed.py`; `scripts/gen_latent_process_seed.py`; `scripts/gen_experiment_design_seed.py`; `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_OBSERVED_MODEL_CONTRACT.md`; new `tests/test_observed_model_learning.py`.
- **Pattern to copy:** existing pre/action/post induction and typed ProcessSchema views.
- **Steps:** 1. Freeze raw observed object/action/relation basis and the common held expression vocabulary. 2. Define bounded candidate generation, object binding, contradiction and nonidentifiability; simulator equations remain scorer/world-owned. 3. Specify native model effects for the supported TransitionHypothesis view and stale receipt behavior.
- **Guard:** specification only.
- **Acceptance:** planned `test_no_candidate_hypotheses_ingested`, `test_held_vocabulary_not_world_truth`, `test_ambiguous_model_stays_portfolio`, `test_transition_view_has_model_receipt`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_induction.py tests/test_latent_process.py -q -p no:cacheprovider`.
- **Non-goals:** claiming unrestricted causal induction or using a hidden causal label as a percept.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P18.E3 closeout (2026-10-22):** The single frozen v1 allocation completed 1,600/1,600 paired rows, 300/300 structural controls and 5/5 tampering checks with exact loaded-native provenance and zero integrity failures. It recorded 400 actual simulator-result-linked refinements. Learned models succeeded on 200/200 worlds in both object-mechanism and temporal families; held-vocabulary search also succeeded on 200/200 in both. Passive and fixed-probe arms succeeded on 0/200. The registered efficacy threshold is NOT_ESTABLISHED because the strongest comparator tied; no intervention reduction offsets the tie. This establishes a bounded native model→graph-proposed probe→verified result→model revision path in these finite worlds, not comparative benefit or unrestricted causal discovery. P19's entry is supported because the model view and evidence path exist alongside P16 execution and P17 behavior, with the comparative result carried forward. No capability level closes. See [`COGNITION_LINEAR_P18_RESULTS.md`](COGNITION_LINEAR_P18_RESULTS.md) and [`COGNITION_LINEAR_P18_PREREG.md`](COGNITION_LINEAR_P18_PREREG.md).

### P18.02 — Generate and verify process-model candidates from observations

- **ID:** P18.02
- **Tier:** T2
- **Goal:** Generate and verify process-model candidates from observations.
- **Read first:** `docs/research/engine_substrate/COGNITION_OBSERVED_MODEL_CONTRACT.md`; `scripts/gen_process_induction_seed.py`; `runners/dsl/src/process_algebra.rs`; `tests/test_observed_model_learning.py`.
- **Touch:** `scripts/gen_process_induction_seed.py` + `seeds/process_induction.json`; `runners/dsl/src/process_algebra.rs`; `tests/test_observed_model_learning.py`.
- **Pattern to copy:** native structural unification, bounded program templates and exact finite effect evaluation.
- **Steps:** 1. Build supported candidate expressions from source-bound observations using existing native Terms. 2. Retain all evidence-consistent candidates and separate prediction from observation. 3. Evaluate supported model-backed transition process views and invalidate effects when model/frame epochs change.
- **Guard:** ModelLearningPolicy; bounded shared budget.
- **Acceptance:** `test_unseen_object_effect_induced`, `test_new_action_effect_not_supplied`, `test_model_counterexample_changes_portfolio`, `test_transition_model_epoch_reverified`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_observed_model_learning.py tests/test_process_native_views.py -q -p no:cacheprovider`.
- **Non-goals:** selecting the right member of a fixture-provided completed model set and calling that induction.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P18.03 — Execute discriminating probes against independent worlds

- **ID:** P18.03
- **Tier:** T2
- **Goal:** Execute discriminating probes against independent worlds.
- **Read first:** `docs/research/engine_substrate/COGNITION_OBSERVED_MODEL_CONTRACT.md`; `scripts/gen_experiment_design_seed.py`; `evaluation/process_mastery/harness.py`; `seeds/native_process_execution.json`.
- **Touch:** `scripts/gen_experiment_design_seed.py` + `seeds/experiment_design.json`; new `evaluation/process_mastery/observed_worlds.py`; new `tests/test_world_experiment_loop.py`.
- **Pattern to copy:** P16 authorized native action/observed result boundary.
- **Steps:** 1. Implement mechanical finite worlds from hidden state/equations and expose only allowed observations and actions. 2. Choose probes from native competing predictions and ingest actual world receipts after execution. 3. Recompute projections/models from outcomes; assert result-linked values change, not only an audit version counter.
- **Guard:** ExperimentDesignPolicy and native action authorization.
- **Acceptance:** `test_agent_probe_changes_world_state`, `test_receipt_matches_hidden_world_transition`, `test_actual_outcome_refines_prediction`, `test_no_information_probe_declined`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_world_experiment_loop.py tests/test_observed_model_learning.py -q -p no:cacheprovider`.
- **Non-goals:** a Python experiment selector or declaring physical/robotic validation from a simulator.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P18.04 — Infer latent process state from prediction failures and fresh continuations

- **ID:** P18.04
- **Tier:** T2
- **Goal:** Infer latent process state from prediction failures and fresh continuations.
- **Read first:** `docs/research/engine_substrate/COGNITION_OBSERVED_MODEL_CONTRACT.md`; `scripts/gen_latent_process_seed.py`; `seeds/qualia_behavior.json`; `tests/test_world_experiment_loop.py`.
- **Touch:** `scripts/gen_latent_process_seed.py` + `seeds/latent_process.json`; new `tests/test_latent_observed_world.py`.
- **Pattern to copy:** regular TimeInfer witnesses and P17 distinction revision.
- **Steps:** 1. Collect observed residual windows from the same independent world. 2. Propose supported latent transformations without named target states, re-induce and test on fresh interventions/continuations. 3. Preserve irregular/insufficient refusal and retire a latent that fails new evidence.
- **Guard:** LatentProcessPolicy; observed-data funding.
- **Acceptance:** `test_latent_predicts_new_intervention`, `test_latent_not_hidden_state_label`, `test_spurious_latent_retired`, `test_irregular_time_refused`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_latent_observed_world.py tests/test_latent_process.py -q -p no:cacheprovider`.
- **Non-goals:** inventing a latent solely to memorize the complete training trace.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P18.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P18.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate observed model generation and world experiment/refinement with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p18_native_causal_chain`, `test_p18_state_perturbation_changes_execution`, `test_p18_default_isolation`, `test_p18_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_observed_model_learning.py tests/test_world_experiment_loop.py tests/test_latent_observed_world.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P18.E2 — Freeze an informative matched-arm evaluation

- **ID:** P18.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p18_v1.py`; new `evaluation/process_mastery/analyze_linear_p18_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P18_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_observed_model_learning.py tests/test_world_experiment_loop.py tests/test_latent_observed_world.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P18.E3 — Report all outcomes and decide the next supported entry

- **ID:** P18.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P18_PREREG.md`; `evaluation/process_mastery/linear_p18_v1.py`; `evaluation/process_mastery/analyze_linear_p18_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P18_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_observed_model_learning.py tests/test_world_experiment_loop.py tests/test_latent_observed_world.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

## Phase 19 — Novel goal-directed processes and general strategy search

**Entry:** P18 supported learned model views, P16 actual execution and P17 acquired significance. **Status:** P19.E1–E3 complete with limits. The bounded grammar includes recursive Compose/Inverse/Power(2|3), exact observed-state and failed-subgoal guards, and one explicit composition subgoal. Failure evidence guides a different subgoal order only on an exact matching binding; wider constraint generalization remains open. Strategy lifting, exact candidate approval/revocation, receipt-backed strategy retention, a cognition-on causal fixture and witnessed one-step commutator size transfer are implemented. A composed proposal with a temporarily worsening intermediate state reaches a simulated world, is retained from its receipt, and solves an unseen binding through strategy lift. The standalone preregistration and held-out result are recorded below: all 2,400 rows completed with exact provenance, but primary efficacy is `NOT_ESTABLISHED` because proposals lacked exact candidate approval, and both registered mechanism criteria were unmet. Phase 20 is authorized only for fresh target-learning and social-acquisition interfaces; P19 invention and strategy efficacy remain unsupported.

**Reason:** P10 stored exact-context traces after solving but did not improve strategies; P14/P15 instantiate known commutator-power recipes. Use task residuals to select general legal expression constructions and discover reusable subgoal structure.

**Registered evidence to freeze:** 200 new process-effect goals and 200 multi-step tool/constraint tasks in each of permutation and irreversible object worlds; generic invention/discovered strategy versus measured greedy and native primitive-search at equal primitive-operation/model-query caps. Include 100 impossible/illegal/precondition controls. Primary ≥20 pp observed solve gain over the stronger supported comparator; require at least one verified held-out non-template process and unseen-binding strategy use. Cost frontier and failed searches remain visible.

### P19.01 — Specify a general operator grammar and real strategy choices

- **ID:** P19.01
- **Tier:** T1
- **Goal:** Specify a general operator grammar and real strategy choices.
- **Read first:** `docs/research/engine_substrate/COGNITION_GOAL_INVENTION_CONTRACT.md`; `scripts/gen_invention_operator_authorship_seed.py`; `scripts/gen_recursive_process_improvement_seed.py`; `scripts/gen_strategy_discovery_seed.py`; `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_OPEN_PROCESS_SEARCH_CONTRACT.md`; new `tests/test_open_process_search.py`.
- **Pattern to copy:** held algebra expression templates, graph goal regression and invariant obligations.
- **Steps:** 1. Define generic typed Compose/Inverse/Power/guard/subgoal grammar, admissibility and bounds without candidate-name dispatch. 2. Make operator and strategy proposals follow unmet effects and acquired constraints. 3. Freeze genuine novelty relative to the held library, legal preconditions and exact-versus-model verification requirements.
- **Guard:** new generic search policy disabled.
- **Acceptance:** planned `test_candidate_name_does_not_choose_recipe`, `test_new_effect_drives_expression_search`, `test_strategy_not_exact_trace_lookup`, `test_invalid_composition_unknown`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_invention.py tests/test_strategy_discovery.py -q -p no:cacheprovider`.
- **Non-goals:** unbounded synthesis or hard-coding each benchmark solution as a new proposal rule.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P19.02 — Generate candidate expressions from residual effects in graph rules

- **ID:** P19.02
- **Tier:** T2
- **Goal:** Generate candidate expressions from residual effects in graph rules.
- **Read first:** `docs/research/engine_substrate/COGNITION_OPEN_PROCESS_SEARCH_CONTRACT.md`; `scripts/gen_invention_round_seed.py`; `scripts/gen_goal_invention_seed.py`; `seeds/native_process_execution.json`.
- **Touch:** new `scripts/gen_open_process_search_seed.py` + `seeds/open_process_search.json`; `tests/test_open_process_search.py`.
- **Pattern to copy:** existing graph expression construction and verified native process effects.
- **Steps:** 1. Enumerate admissible expression data from shared held grammar with actual graph frontier state. 2. Rank by verified coverage, residual and declared work without a task-specific recipe. 3. Evaluate candidate expression trees through P16 and retain proof/model/source identity and failures.
- **Guard:** OpenProcessSearchPolicy disabled; exact budget per node/query.
- **Acceptance:** `test_unseen_operator_expression_generated`, `test_changed_goal_changes_proposal`, `test_new_candidate_executed_not_host_rebuilt`, `test_proposal_budget_includes_failures`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_open_process_search.py tests/test_native_process_execution.py -q -p no:cacheprovider`.
- **Non-goals:** counting a familiar power instantiated at a new name as unconstrained meta-invention.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P19.03 — Learn reusable subgoal and constraint-preservation strategies

- **ID:** P19.03
- **Tier:** T2
- **Goal:** Learn reusable subgoal and constraint-preservation strategies.
- **Read first:** `docs/research/engine_substrate/COGNITION_OPEN_PROCESS_SEARCH_CONTRACT.md`; `scripts/gen_strategy_discovery_seed.py`; `scripts/gen_process_lifting_seed.py`; `tests/test_open_process_search.py`.
- **Touch:** `scripts/gen_strategy_discovery_seed.py` + `seeds/strategy_discovery.json`; new `tests/test_strategy_generalization.py`.
- **Pattern to copy:** bounded goal regression, lifting witnesses and invariant-wall evidence.
- **Steps:** 1. Search choices of subgoal order/constraint preservation from partially successful and failed traces. 2. Lift the found control structure with explicit preconditions. 3. Verify unseen bindings, object counts and longer tasks that require temporary worsening rather than greedy Hamming descent.
- **Guard:** StrategyDiscoveryPolicy; bounded native search.
- **Acceptance:** `test_new_binding_uses_discovered_strategy`, `test_temporary_regression_allowed`, `test_failed_constraint_not_replayed`, `test_world_receipt_confirms_strategy`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_strategy_generalization.py tests/test_process_lifting.py tests/test_open_process_search.py -q -p no:cacheprovider`.
- **Non-goals:** a human-authored piece-placement policy, scorer-provided witness plan, or calling trace storage a learned strategy.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P19.04 — Feed novel verified processes through existing adoption and rollback

- **ID:** P19.04
- **Tier:** T2
- **Goal:** Feed novel verified processes through existing adoption and rollback.
- **Read first:** `docs/research/engine_substrate/COGNITION_OPEN_PROCESS_SEARCH_CONTRACT.md`; `seeds/process_proof_adoption.json`; `seeds/invention_operator_authorship.json`; `seeds/recursive_process_improvement.json`.
- **Touch:** new `scripts/gen_open_process_adoption_seed.py` + `seeds/open_process_adoption.json`; new `tests/test_open_process_adoption.py`.
- **Pattern to copy:** existing exact candidate/digest proof/approval gates and ancestry.
- **Steps:** 1. Bind generic candidates to full expression digests and their verification domain. 2. Preserve proof obligations and candidate-specific human approvals where already required; no v1/v2/v3 approval extends to new candidates. 3. Keep rejected/changed candidates and roll back dependent plans on revoked support.
- **Guard:** OpenProcessAdoptionPolicy disabled; existing gates unchanged.
- **Acceptance:** `test_expression_digest_not_candidate_name`, `test_new_candidate_not_preapproved`, `test_proof_binds_new_expression`, `test_invalidated_process_stops_next_action`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_open_process_adoption.py tests/test_process_proof_adoption.py tests/test_native_process_execution.py -q -p no:cacheprovider`.
- **Non-goals:** introducing a new approval requirement beyond existing machinery or bypassing existing approval to finish evaluation.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P19.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P19.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate generic process/strategy search and verified adoption with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p19_native_causal_chain`, `test_p19_state_perturbation_changes_execution`, `test_p19_default_isolation`, `test_p19_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_open_process_search.py tests/test_strategy_generalization.py tests/test_open_process_adoption.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P19.E2 — Freeze an informative matched-arm evaluation

- **ID:** P19.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p19_v1.py`; new `evaluation/process_mastery/analyze_linear_p19_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P19_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_open_process_search.py tests/test_strategy_generalization.py tests/test_open_process_adoption.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P19.E3 — Report all outcomes and decide the next supported entry

- **ID:** P19.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P19_PREREG.md`; `evaluation/process_mastery/linear_p19_v1.py`; `evaluation/process_mastery/analyze_linear_p19_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P19_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_open_process_search.py tests/test_strategy_generalization.py tests/test_open_process_adoption.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P19 implementation checkpoint (2026-10-22):** Added `COGNITION_OPEN_PROCESS_SEARCH_CONTRACT.md`, a disabled-by-default graph seed for bounded Compose in both parent orders, Inverse, and Power(2|3), with exact observed-state guards, composition-subgoal metadata, and rank selection by verified coverage/residual status/work. Residual expressions now recursively compose with held processes in either order and accept recursive Inverse/Power(2|3) constructors up to the declared depth; all attempts are budgeted and recursive parent source identities are included in verifier-side digests. Search links a task's exact-binding failure constraints before enumeration and marks expressions repeating a failed intermediate subgoal `constraint_failed`, allowing a separately verified alternate order to win without minting the failed one. Opt-in strategy lifting applies a receipt-learned expression to a different state and goal when object count and source/model/frame/probe epochs match. A size-transfer path reuses a single-step commutator strategy on a larger domain only after the existing process-lifting policy has two differently sized structural witnesses and an exact native-fingerprinted target instance; arbitrary strategies do not receive size generalization. Failed graph strategy replays retain binding- and epoch-specific constraints that block blind same-binding retries while leaving other bindings eligible. Candidates remain unapproved until a verifier-side content digest receipt and exact candidate-specific human approval are attached; native execution rechecks the live effect and records the independent world-transition result. The cognition-on causal-chain fixture verifies one shared-budget debit, graph-authored choice, candidate-bound approval, independently applied finite-world result, receipt-bound learned strategy, unseen-state reuse, and abstention after a changed model epoch. A composed proposal whose intermediate subgoal worsens Hamming distance is executed, retained from its world receipt, and reused under a new binding. Focused P19 search, strategy, lifting, adoption, native execution and cognition-on integration regressions: 93 passed. This is partial mechanism/integration evidence, not a phase evaluation. Broader constraint guards and general object-count transfer remain incomplete. The representative world receipt used a deterministic finite test transition; external/world-backed evaluation, standalone preregistration, matched held-out allocation and results ledger remain outstanding. Registered criteria are unchanged.

**P19.E2 development record (2026-10-23):** Commit `4b7d5810` adds independent permutation and irreversible-object worlds, receipt verification, disjoint development/held-out/control seed blocks, measured greedy and native primitive-search arms, and a graph-side singular tie-break enabled only in the comparator profile. The development self-check covers all 32 registered development tasks and 100 impossible/illegal/precondition controls. Native primitive search solved 32/32 within 8 primitive actions and 4,096 model queries. Generic graph invention with synthetic candidate-specific development approvals completed 8/32; 16 proposals failed independent world execution and 8 tasks produced no candidate. All 8 receipt-backed strategies solved a changed state and goal binding through native strategy replay. Focused tests: 58 passed. The standalone preregistration was frozen as `cfc4efd2`; held-out results and limitations are reported below.

**P19.E3 closeout (2026-10-23):** See [`COGNITION_LINEAR_P19_RESULTS.md`](COGNITION_LINEAR_P19_RESULTS.md). The sole frozen held-out allocation completed 2,400/2,400 rows with 100/100 controls passing, zero structural failures and exact native provenance. Native primitive search solved 800/800 and greedy 632/800. Invention had 582 proposals awaiting exact candidate approval, 202 no-candidate and 16 ambiguous rows; therefore primary efficacy is `NOT_ESTABLISHED`, not a zero-skill failure. Both required mechanism criteria were unmet in this run (zero receipted non-template inventions and zero unseen-binding strategy solves). No capability claim follows. Phase 20 is authorized only for the fresh target-learning and social-acquisition interfaces supported by P18/P19 evidence paths; it must not assume P19 invention/strategy efficacy.

## Phase 20 — Fresh learning transfer and observational social acquisition

**Entry:** P19 goal search and P18 learned-model interfaces; P17 behavioral qualia. **Status:** P20.01–P20.04 and E1–E3 reported. Native fresh learning, bounded observation/demonstration/instruction acquisition, reward-only abstention and explanation reconstruction passed structural checks. Frozen transfer efficacy failed (mapped-source minus fresh AUC −0.333 versus +0.20); no beneficial transfer claim is supported. P19's NOT_ESTABLISHED efficacy and unmet mechanism limits carry forward.

**Reason:** P11 lacked a fresh target learner and P12 had a single-primitive success ceiling. Implement the same real learner in every arm, vary only available source/social experience, and count its actual world actions and information.

**Registered evidence (frozen and run):** 200 streams per target domain pair; fresh/source/mismatched-source, observation/demonstration/instruction/reward-only; 100 wrong-frame/missing/body/false-description controls. The preregistration selected the ≥20 pp fixed-budget learning-curve AUC criterion and disabled the interaction-cost alternative before holdout. The frozen result is −33.3 pp; retain it as FAIL. Fresh learner development checks passed; held-out structural validity and native provenance passed.

### P20.01 — Specify a common target learner and fair source exposure

- **ID:** P20.01
- **Tier:** T1
- **Goal:** Specify a common target learner and fair source exposure.
- **Read first:** `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_SOCIAL_ACQUISITION_CONTRACT.md`; `evaluation/process_mastery/linear_p11_v1.py`; `evaluation/process_mastery/linear_p12_v1.py`; `seeds/process_induction.json`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LEARNING_TRANSFER_CONTRACT.md`; new `tests/test_target_learner.py`.
- **Pattern to copy:** P18 real observed-model learning and P16 arm-affordance parity.
- **Steps:** 1. Specify common learner/probe/action interfaces for every arm and what source exposure changes. 2. Distinguish evidence opportunities, informative observations, actions and total work; freeze fair data/compute comparisons. 3. Define target generalization, learning curves, right-censoring and unsupported input before outcomes.
- **Guard:** target learner/transfer policies disabled.
- **Acceptance:** planned `test_fresh_has_real_learning_path`, `test_same_target_affordances`, `test_missing_adapter_hard_error`, `test_evidence_and_work_separate`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_process_transfer.py tests/test_social_process.py -q -p no:cacheprovider`.
- **Non-goals:** comparing a working source mapper against an inert fresh arm.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P20.01 implementation record (2026-10-23):** Added [`COGNITION_LEARNING_TRANSFER_CONTRACT.md`](COGNITION_LEARNING_TRANSFER_CONTRACT.md) to bound the initial learner to the existing native receipt-bound categorical transition inducer. `tests/test_target_learner.py` now covers fresh learning, common target affordances across source conditions, missing-adapter hard error, evidence/work separation, missing or mismatched receipt refusal, counterevidence, disabled-policy behavior and separate source/evidence/action accounting. `NativeTargetLearner` ingests typed target-world receipts and reads native hypotheses/predictions; source exposure is separately charged. The P20.01 acceptance tests pass; phase-level closure awaits the registered P20 evaluation.

### P20.02 — Learn target maps and processes from native exploration

- **ID:** P20.02
- **Tier:** T2
- **Goal:** Learn target maps and processes from native exploration.
- **Read first:** `docs/research/engine_substrate/COGNITION_LEARNING_TRANSFER_CONTRACT.md`; `scripts/gen_process_transfer_seed.py`; `seeds/process_induction.json`; `seeds/open_process_search.json`.
- **Touch:** new `scripts/gen_target_learning_seed.py` + `seeds/target_learning.json`; `tests/test_target_learner.py`.
- **Pattern to copy:** P18 model candidates and P19 missing-effect search.
- **Steps:** 1. Let fresh agents infer supported target processes/frame maps from their own evidence. 2. Let source arms propose compatible priors/candidates but require the same target verification. 3. Preserve wrong-source rejection, valid unsuccessful searches and actual per-step learning records.
- **Guard:** TargetLearningPolicy; same resource contract in all arms.
- **Acceptance:** `test_fresh_learns_unseen_target`, `test_source_uses_same_target_verifier`, `test_wrong_map_rejected`, `test_outcomes_recorded_after_each_probe`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_target_learner.py tests/test_world_experiment_loop.py -q -p no:cacheprovider`.
- **Non-goals:** supplying the source map or target answer in a fresh-arm initialization.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P20.02 progress (2026-10-23):** Added independently coded `ThermalWorld` and `LatchWorld` targets plus relabeled heat-source and lever-source domains. The same native learner acquires source effects from actual authorized interactions. Two distinct budgeted paired source/target receipt records now cause a native graph rule to propose a categorical action/type/feature/value map; an independent verifier checks that proposal against the underlying receipts. Matched source-prior prediction still needs a fresh target-effect receipt, and the learner predicts unseen object bindings in both target families. Replay/unauthorized receipts, insufficient pairs, conflicting pairs and wrong maps are rejected. The experiment supplies source↔target object-pair identity; autonomous discovery of that correspondence and uniform arm streams remain open. A two-domain development curve now runs fresh, mapped-source and mismatched-source arms with 8 streams per domain pair, native learning, unseen-object execution and resource counters. Development normalized AUC was 0.500 fresh, 0.167 mapped-source and 0.500 mismatched-source. The mapped arm used three target actions; fresh and mismatched arms used two. Mismatched source evidence failed to produce a native map and the learner then succeeded from target receipts. Raw records are `/tmp/cognition_p20_dev_curve_8_v2.json` (SHA-256 `ad64bacdbe5a7a34737c93ab6e7875fcd60a9777baf52bcbc5e61e065a29e33f`). These are development-only results; the registered full-arm learning-curve evaluation remains open. P20.02 is not closed.

### P20.03 — Acquire multi-step processes from incidental interaction

- **ID:** P20.03
- **Tier:** T2
- **Goal:** Acquire multi-step processes from incidental interaction.
- **Read first:** `docs/research/engine_substrate/COGNITION_LEARNING_TRANSFER_CONTRACT.md`; `scripts/gen_social_process_seed.py`; `scripts/gen_imitation_seed.py`; `seeds/qualia_behavior.json`.
- **Touch:** `scripts/gen_social_process_seed.py` + `seeds/social_process.json`; `scripts/gen_imitation_seed.py` + `seeds/imitation.json`; new `tests/test_observational_process_learning.py`.
- **Pattern to copy:** P12 attributed action events and P17 consequence-grounded distinctions.
- **Steps:** 1. Observe other agents using tools, requesting, misunderstanding and repairing while pursuing ordinary goals. 2. Infer candidate processes through the common target learner without teacher markers, hidden intention labels or source AST. 3. Handle omitted steps/partial access as uncertainty and test own-body multi-step execution through the existing action boundary.
- **Guard:** social policies disabled; ordinary action/adoption checks.
- **Acceptance:** `test_incidental_interaction_teaches_multistep_process`, `test_no_teacher_flag_needed`, `test_hidden_step_not_invented`, `test_other_success_not_own_receipt`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_observational_process_learning.py tests/test_target_learner.py tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a scripted behavioral oracle choosing the demonstration interpretation.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P20.03 progress (2026-10-23):** Added `observed_sequence_learning` native rules and profile wiring. Given a complete two-action episode, current primitive affordances and funded requests, the graph creates an unverified ordered candidate for witnessed observation, demonstration, or parsed instruction without a teacher marker or source AST; partial episodes abstain, and another actor's success creates no own receipt. A reward-only episode with no action sequence produces a funded `abstained_underidentified` result rather than an invented process. A separate executor requires funded fresh-world verification, exact current primitive links and epoch agreement before native promotion. It then routes each own action through a per-step authorization callback and records sink-bound own-trial receipts; denial stops before the denied world action. Source-specific adapters now require ordered world receipts for observation/demonstration, a successful public language parse for instruction, and scalar feedback without sequence data for reward-only; source types and links are declared in the regenerated native seed. A development panel sends every arm through the same funded native learner; instruction is authored in a separate source world and parsed in the receiver world. The three sequence-bearing arms verify and execute on a fresh case, while reward-only abstains. The panel records evidence opportunities, visible observations, source-world and target actions, source-information units, native learner settlement steps, graph size, elapsed time and budget debits. Development-only wrong-frame, missing-step, body-mismatch and false-description controls all abstain without false candidates. An eight-stream-per-arm, 100-control development run passed all 32 social streams and 100/100 controls; output is at `/tmp/cognition_p20_social_dev_8x100.json` (SHA-256 `162b99a6c6e6914f8792259d73c58149d365d89fc3575f093c08e4c5aa0849bf`). This is not a registered comparison and does not replace the frozen allocation. The focused source-adapter, consumer, explanation, target-learning and cognition-on profile suite passes (97 tests). This remains bounded to two-step request→repair; general sequence induction, omitted-step uncertainty beyond complete/partial episodes, and arbitrary own-body replay remain open. P20.E2 still requires matched scoring and the full frozen panel.

### P20.04 — Rebuild novel multi-step processes from bounded explanations

- **ID:** P20.04
- **Tier:** T2
- **Goal:** Rebuild novel multi-step processes from bounded explanations.
- **Read first:** `docs/research/engine_substrate/COGNITION_LEARNING_TRANSFER_CONTRACT.md`; `scripts/gen_process_explanation_seed.py`; `seeds/target_learning.json`; `tests/test_process_explain_rebuild.py`.
- **Touch:** `scripts/gen_process_explanation_seed.py` + `seeds/process_explanation.json`; new `tests/test_multistep_explain_rebuild.py`.
- **Pattern to copy:** isolated P12 receiver and fixed shared primitive vocabulary.
- **Steps:** 1. Produce explanations of new composed processes with preconditions and key contingencies. 2. Reconstruct using an isolated receiver with no original expressions, IDs or fingerprints. 3. Execute on fresh worlds, expose counterexamples to incomplete explanations and measure fidelity beside words/evidence/actions.
- **Guard:** ProcessExplanationPolicy; native reconstruction.
- **Acceptance:** `test_receiver_rebuilds_novel_composition`, `test_source_ids_cannot_leak`, `test_missing_precondition_causes_unknown`, `test_unseen_world_effects_match`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_multistep_explain_rebuild.py tests/test_process_explain_rebuild.py tests/test_target_learner.py -q -p no:cacheprovider`.
- **Non-goals:** an AST serialization called explanation or an unrestricted natural-language claim from a bounded vocabulary.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P20.04 progress (2026-10-23):** Extended the native explanation author to draft a bounded ordered list of public steps from a `ProcessSchema`; it does not include the source expression or fingerprint. A sender produces two independently self-monitored sentences with explicit precondition headers; an isolated receiver reparses each sentence through the grounded language comprehension path and passes only event labels, explicit preconditions, current shared vocabulary and epochs to the graph. The graph binds each event/precondition to a distinct shared primitive, creates an unverified candidate without source IDs/AST/fingerprint, and records `unknown_missing_precondition` when a step precondition is absent. A funded fresh-world verifier checks the composed effect and rejects a counterexample starting outside the first-step precondition; only its epoch-bound receipt can trigger native schema adoption. Focused tests cover the native draft→production→independent reparse→native reconstruction→independent finite-world path, plus the request→repair cognition-on profile path. At this checkpoint, integrated end-to-end work/fidelity measurements and broader contingency coverage remained open.

**P20.E1 progress (2026-10-23):** Added the guarded `target_learning` and `observed_sequence_learning` rules to the cognition-on seed closure; both policies remain disabled by default. Profile-level causal tests show that receipted target observations produce a native hypothesis and new-binding prediction; a matched source prior enters only with exact map and current target receipts; changing the observed effect changes prediction; and a complete incidental episode yields an unverified candidate linked to observed primitives. The profile test also fresh-world verifies, natively promotes and executes that sequence through per-step authorization with own-trial receipts. P20.04 now has a native draft→production→independent comprehension→native reconstruction→fresh-world verification test, and its native consumer is also exercised through the cognition-on profile. Default/conversation isolation and shared-budget debits hold in profile tests. At this checkpoint, the full registered multi-arm panel and integrated explanation cost/fidelity accounting were pending.

### P20.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P20.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate common fresh learner and multi-step social/explanation consumers with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p20_native_causal_chain`, `test_p20_state_perturbation_changes_execution`, `test_p20_default_isolation`, `test_p20_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_target_learner.py tests/test_observational_process_learning.py tests/test_multistep_explain_rebuild.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P20.E2 — Freeze an informative matched-arm evaluation

- **ID:** P20.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p20_v1.py`; new `evaluation/process_mastery/analyze_linear_p20_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P20_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_target_learner.py tests/test_observational_process_learning.py tests/test_multistep_explain_rebuild.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P20.E2 development checkpoint (2026-10-23):** Added `linear_p20_v1.py` to run the current fresh/mapped/mismatched target learner in both domain pairs together with observation, demonstration, parsed-instruction and reward-only social arms, native explanation production/reconstruction/fidelity, and structural controls. Added `analyze_linear_p20_v1.py`, which checks pair×arm completeness, duplicate rows, receipt gates, social execution/abstention, explanation fidelity/adoption/source isolation, resource fields, control outcomes, exact source-file hashes and allocation digest. It labels the payload `DEVELOPMENT_ONLY` and the primary `NOT_ESTIMATED`; held-out execution raises until the standalone freeze exists. The analyzer verified loaded-extension/build-source attestation as `ATTESTED`. An eight-stream-per-cell integrated development payload completed 48 target rows, 32 social rows, 8 native explanation-rebuild trials and 100 controls, all with structural status PASS. The deterministic development allocation digest is `8f4b89c4f2cd2ac58d2b11d8f998f08ae447b60b1865cf9f6730d78b830d167a`. Raw payload and analyzer output are `/tmp/cognition_p20_combined_dev_8x100.json` (SHA-256 `7f563d3328367d304fe5089df81cbb2d3b1707360ae4327593894d1973bf1304`) and `/tmp/cognition_p20_combined_dev_8x100_analysis.json` (SHA-256 `1507506c0babe2182aaaa7694ef145cf20915766db62f38d78dc87e194b7a0b0`). Descriptive development normalized AUCs were 0.500 fresh, 0.167 mapped-source and 0.500 mismatched-source; the primary remains unestimated because this is development data. The focused combined P20 regression suite passes 100 tests, including tampering checks. Task/source distribution independence, frozen effect/stop rules, standalone preregistration and held-out runner remain open. E2 is not complete and no held-out access has occurred.

### P20.E3 — Report all outcomes and decide the next supported entry

- **ID:** P20.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P20_PREREG.md`; `evaluation/process_mastery/linear_p20_v1.py`; `evaluation/process_mastery/analyze_linear_p20_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P20_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_target_learner.py tests/test_observational_process_learning.py tests/test_multistep_explain_rebuild.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P20.E3 results (2026-10-23):** See [`COGNITION_LINEAR_P20_RESULTS.md`](COGNITION_LINEAR_P20_RESULTS.md). The standalone preregistration was committed alone as `42e577db`; its fixed allocation completed 1,200 target arm rows, 800 social rows, 200 explanations and 100 controls. Runtime provenance was `ATTESTED`; structural analysis passed with zero failures. Primary mapped-source minus fresh normalized AUC was −0.333 (fresh 0.500, mapped 0.167, mismatched 0.500), a valid `FAIL` against +0.20. Observation, demonstration and instruction each verified/executed 200/200; reward-only abstained 200/200; explanation reconstruction/adoption was 200/200 at 100% fidelity; controls passed 100/100. P21 may use the fresh native learner as its supported consumer, but must carry the transfer failure unchanged. Raw payload SHA-256 `76f575f5710449f58adf0d7152452a14d2d831f643bee5b4e7599d90e2f938c8`; analyzer SHA-256 `6ecfaa9738670bb32ef41f87e96c38aaeaf315ed6c2a903bcd9312d84233f5c8`. Focused regression: 101 tests before final freeze hardening; the changed runner/analyzer tests then passed 4 tests.

**P20.04 and E1 closeout (2026-10-23):** The later integrated P20 runner and frozen E3 allocation supplied the previously missing explanation work/fidelity accounting: all 200 explanation reconstructions/adoptions matched at 100% fidelity, with source isolation and controls passing. The four named cognition-on profile tests (`test_p20_native_causal_chain`, state perturbation, default isolation and shared budget) pass. Together with the native explanation reconstruction tests and E3's complete scored profile run, this closes P20.04 and E1 for the declared finite two-step protocol. General contingency coverage, transfer benefit and human-relative claims remain unestablished; the registered transfer primary remains `FAIL` as reported above.

## Phase 21 — Resource-bounded retention and useful self-curriculum

**Entry:** P20 actual fresh-learning streams and P13 staged replay/library machinery. **Status:** entry supported using the fresh native target learner; mapped-source transfer benefit is unsupported and must not be assumed.

**Reason:** P13 showed verified cost savings but no accuracy/retention benefit; P15 curriculum matched unchanged and its generated task was not a demonstrated learning input. Connect replay/curriculum to the actual learner, with finite memory and equal evidence policies. **Status:** P21.01–E3 complete. Charged-memory storage, staged native sleep, cognition-on integration and native curriculum delivery passed structural checks. Both registered held-out efficacy primaries failed validly; retain the ceiling-limited task-distribution gap for future work.

**Registered evidence to freeze:** 200 paired learning→idle→interference→delayed-novel-test streams at each of three fixed workload/capacity strata; full sleep/replay-only/matched awake/no offline and residual-selected versus random versus fixed curriculum ablations. Primary delayed learning-curve area gain≥10 pp over replay-only at new-task loss≤2 pp; curriculum primary≥10 pp under equal total interactions/work. Report the full capacity curves even at ceiling/floor. No arm may retain hidden originals outside its charged memory or receive an artificially disabled learner.

### P21.01 — Specify charged memory interference and training-task delivery

- **ID:** P21.01
- **Tier:** T1
- **Goal:** Specify charged memory interference and training-task delivery.
- **Read first:** `docs/research/engine_substrate/COGNITION_SLEEP_STAGE_CONTRACT.md`; `scripts/gen_process_curriculum_seed.py`; `scripts/gen_library_learning_seed.py`; `seeds/target_learning.json`; `docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md`; new `tests/test_developmental_memory.py`.
- **Pattern to copy:** existing sleep cursors, memory tiers and real target learner.
- **Steps:** 1. Specify charged resident/durable evidence, retrieval/rebuild cost and equal capacity/forgetting semantics across arms. 2. Define independent interference/delayed test distributions and candidate training tasks with real solvability/unknown outcomes. 3. Freeze three broad capacity/workload strata from non-efficacy sizing checks; do not choose a stratum by treatment benefit.
- **Guard:** memory/curriculum extensions disabled.
- **Acceptance:** planned `test_no_uncharged_hidden_originals`, `test_all_arms_same_memory_policy`, `test_curriculum_task_reaches_learner`, `test_later_test_not_curriculum_input`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_process_curriculum.py -q -p no:cacheprovider`.
- **Non-goals:** breaking the control learner or importing a planted forgetting curve to manufacture retention.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P21.02 — Consolidate and retrieve learned evidence under real capacity limits

- **ID:** P21.02
- **Tier:** T2
- **Goal:** Consolidate and retrieve learned evidence under real capacity limits.
- **Read first:** `docs/research/engine_substrate/COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md`; `scripts/gen_sleep_regime_seed.py`; `scripts/gen_library_learning_seed.py`; `scripts/gen_strategy_library_seed.py`.
- **Touch:** `scripts/gen_sleep_regime_seed.py` + `seeds/sleep_regime.json`; `scripts/gen_library_learning_seed.py` + `seeds/library_learning.json`; `tests/test_developmental_memory.py`.
- **Pattern to copy:** P13 verified chunk cost accounting and restart-safe stage ownership.
- **Steps:** 1. Apply the same declared capacity/eviction model to source evidence, chunks and rebuild data in all arms. 2. Let sleep retain/reconstruct verified useful structure without discarding counterexamples. 3. Route retrieval into the P20 learner and meter actual delayed task decisions, retrieval overhead and interference failures.
- **Guard:** SleepRegimePolicy/LibraryLearningPolicy; existing shared budget.
- **Acceptance:** `test_sleep_chunk_used_on_delayed_task`, `test_evicted_source_not_read_through_host`, `test_counterevidence_survives_compression`, `test_foreground_resume_preserved`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_developmental_memory.py tests/test_sleep_regime_migrated.py tests/test_library_learning.py -q -p no:cacheprovider`.
- **Non-goals:** calling a library cost gain a retention gain or exempting original traces from capacity.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P21.03 — Run generated curriculum tasks through native learning

- **ID:** P21.03
- **Tier:** T2
- **Goal:** Run generated curriculum tasks through native learning.
- **Read first:** `docs/research/engine_substrate/COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md`; `scripts/gen_process_curriculum_seed.py`; `seeds/target_learning.json`; `scripts/gen_qualia_acquisition_seed.py` (P17 revision rules).
- **Touch:** `scripts/gen_process_curriculum_seed.py` + `seeds/process_curriculum.json`; new `scripts/gen_curriculum_learning_bridge_seed.py` + `seeds/curriculum_learning_bridge.json`; new `tests/test_curriculum_learning.py`.
- **Pattern to copy:** observed residual admission locks and P20 actual task execution.
- **Steps:** 1. Transform admissible native curriculum requests into independent world training events without a target solution. 2. Execute/probe/learn under shared work and exposure caps and feed observed progress back to task selection. 3. Test random/fixed/residual selectors against identical task pools; suppress repeated unlearnable tasks and preserve held-out isolation.
- **Guard:** CurriculumLearningBridgePolicy disabled; no extra operator approval.
- **Acceptance:** `test_curriculum_result_changes_learner`, `test_generated_task_not_just_status_receipt`, `test_random_arm_same_task_access`, `test_no_progress_stops_repetition`, `test_sealed_eval_ids_hidden`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_curriculum_learning.py tests/test_process_curriculum.py tests/test_target_learner.py -q -p no:cacheprovider`.
- **Non-goals:** using graph task creation alone as evidence that curriculum improved learning.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P21.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P21.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate capacity-bounded consolidation and actual curriculum learning with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p21_native_causal_chain`, `test_p21_state_perturbation_changes_execution`, `test_p21_default_isolation`, `test_p21_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_developmental_memory.py tests/test_curriculum_learning.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P21.01 contract record (2026-10-23):** Added [`COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md`](COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md), freezing byte-accounted capacities, shared admission/eviction policy, protected counterevidence, answer-free training-task delivery, delayed-test isolation and zero-tolerance controls. Added `ChargedMemory`, which stores serialized bytes only, rejects over-capacity evidence, provides deterministic eviction and counts retrieval/decode work. Lossless compressed chunks carry source-record IDs and reconstruct their full evidence. This does not yet connect the P13 native sleep cursor to charged storage or establish retention benefit.

**P21.02/P21.03 mechanism record (2026-10-23):** Retrieved transition receipts have been passed to the common P20 `NativeTargetLearner`; the delayed probe is answered from a native hypothesis. Protected counterevidence survives lossless chunk replacement, and evicted records are unavailable from the store. A new generated `curriculum_learning_bridge` seed emits answer-free training requests from native P15 tasks and writes an outcome only after two distinct observed receipts and a matching native candidate hypothesis. An end-to-end development test starts from a graph-authored counterexample task, executes authorized actions in a new thermal world, feeds typed receipts to native learning and observes the curriculum task complete. The seed is installed in the cognition-on closure with its policy disabled; default and conversation profiles remain isolated. These are mechanism checks, not a retention/curriculum efficacy estimate.

**P21.E2/E3 result (2026-10-23):** The standalone protocol was frozen in `31ce0440` against code commit `f9212d28`; its 600 sleep-stream IDs, 600 curriculum-stream IDs and 100 controls completed once. Exact native runtime provenance was `ATTESTED`; the analyzer returned structural `PASS`, zero failures, 2,400 sleep rows, 1,800 curriculum rows and 100/100 controls. Full-sleep minus replay-only delayed learning-curve AUC was 0.000 against +0.10, with new-task loss 0.000: valid `FAIL`. Residual minus mean(random,fixed) curriculum delayed accuracy was 0.000 against +0.10: valid `FAIL`. All primary arms were at delayed-accuracy ceiling. The ledger is [`COGNITION_LINEAR_P21_RESULTS.md`](COGNITION_LINEAR_P21_RESULTS.md); raw SHA-256 `d906b3c1eca6e4dafac64a9c1f1bf3d807c77d2571f1202657fc0454516aadd1`, analyzer SHA-256 `3a1d8da1920e30ff0266ef142eb15f93ad3718fc7b37332f5b96fcfbaede5fb3`. This does not establish efficacy or close a capability level.

### P21.E2 — Freeze an informative matched-arm evaluation

- **ID:** P21.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p21_v1.py`; new `evaluation/process_mastery/analyze_linear_p21_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P21_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_developmental_memory.py tests/test_curriculum_learning.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P21.E3 — Report all outcomes and decide the next supported entry

- **ID:** P21.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P21_PREREG.md`; `evaluation/process_mastery/linear_p21_v1.py`; `evaluation/process_mastery/analyze_linear_p21_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P21_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_developmental_memory.py tests/test_curriculum_learning.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

## Phase 22 — Independent-goal multi-generation improvement and capability audit

**Entry:** P16 exact execution/provenance, P17–P21 supported learned behavior and P19 generic proposals; all claimed prerequisites reviewed. P21 mechanisms are available but both efficacy primaries failed at ceiling, so P22 must use a new independent-goal panel and cannot rely on a P21 benefit. **Status:** active. P22.01 estimand, P22.02 generic training-only proposals with two-trial qualification, P22.03 Loopover/D4 task adapters and native checkpoint scoring fixtures, and P22.04 evidence matrix are implemented. The cognition-on fixture now traverses native search, a digest-bound approval fixture, native action execution and a verified local-world receipt; a perturbed guard state abstains before the sink. A new post-approval operator-mutation regression confirms the exact approval binding also blocks execution before the world transition. These tests verify the native boundary, not external human authorization. Selected distinct-goal Loopover/D4 development fixtures now pass native candidate-composition qualification. Checkpoints carry restorable native graph state, and the training-only probe can extend a parent checkpoint with cumulative work accounting. Approved multi-generation cross-family lineages, resource-matched learner comparators, and general independent-goal efficacy remain open. P22.E1 integration mechanisms pass; P22.E2–E3 remain open.

**Reason:** Replace operator-aligned targets and hard-coded successors with an actual learning/invention loop on independent task distributions. This is a new protocol on untouched goals; it must not repair/rescore the P15 trend or assume a human comparison.

**Registered evidence to freeze:** At least 3 approved generations where existing policy requires approval, ≥200 common task worlds per claimed family/checkpoint plus ≥200 fresh validation worlds, in at least two structurally distinct supported domains. Same sealed evaluation panel at each checkpoint, disjoint training/selection/world-parameter validation blocks and identical primitive-work/model-query ceilings across arms. Primary paired checkpoint improvement versus frozen ancestor at equal budget; prespecify ≥10 pp final improvement and a ≥5 pp/generation slope in paired score differences with one-sided 99% lower bound>0, Holm-corrected across claimed families. Use world-cluster bootstrap or a design-based bounded-score estimator defined for all-success/all-failure; ceiling/flat scores mean zero improvement, not an estimator failure or a changed test.

### P22.01 — Freeze independent worlds resource matching and ceiling-safe inference

- **ID:** P22.01
- **Tier:** T1
- **Goal:** Freeze independent worlds resource matching and ceiling-safe inference.
- **Read first:** `docs/research/engine_substrate/COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `docs/research/engine_substrate/COGNITION_OPEN_PROCESS_SEARCH_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`; new `tests/test_improvement_estimand.py`.
- **Pattern to copy:** paired raw outcome/bootstrap accounting, without P15 separated logistic primary.
- **Steps:** 1. Choose supported independent goal-generating worlds before candidate search; neither operator names nor powers may affect them. 2. Freeze common and fresh panels, equal budget frontiers, primary paired improvement/slope estimands and multiplicity. 3. Write analytic fixtures for ceiling, floor, flat, reversed and positive trends and verify zero effect remains zero; capability claims require actual family coverage.
- **Guard:** specification only.
- **Acceptance:** `test_ceiling_flat_is_zero_improvement`, `test_ancestor_same_worlds`, `test_generation_not_goal_parameter`, `test_cost_mismatch_blocks_efficiency_claim`, `test_pair_cluster_preserved`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_improvement_estimand.py -q -p no:cacheprovider`.
- **Non-goals:** switching estimators after a held-out fit fails or claiming superiority from a one-call restriction that gives one arm extra primitive work.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P22.02 — Drive generic operator proposals and qualification from observed tasks

- **ID:** P22.02
- **Tier:** T2
- **Goal:** Drive generic operator proposals and qualification from observed tasks.
- **Read first:** `docs/research/engine_substrate/COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md`; `scripts/gen_open_process_search_seed.py`; `scripts/gen_recursive_process_improvement_seed.py`; `seeds/curriculum_learning_bridge.json`.
- **Touch:** new `scripts/gen_independent_improvement_seed.py` + `seeds/independent_improvement.json`; new `tests/test_independent_improvement.py`.
- **Pattern to copy:** P19 generic expression search, P21 actual training progress and existing candidate approval.
- **Steps:** 1. Propose next operators from training residuals using graph-selected generic grammar/search. 2. Qualify on separate native development trials with measured effects/cost/proofs; retain unchanged ancestor and rollback lineage. 3. Request only candidate-specific existing approvals when required; record approval costs and human edits without assuming any past authorization extends forward.
- **Guard:** IndependentImprovementPolicy disabled; existing approval boundaries remain.
- **Acceptance:** `test_next_candidate_not_named_in_seed`, `test_qualification_from_native_trials`, `test_no_holdout_in_proposal`, `test_new_approval_exact_expression`, `test_rollback_stops_current_execution`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_independent_improvement.py tests/test_open_process_adoption.py tests/test_curriculum_learning.py -q -p no:cacheprovider`.
- **Non-goals:** an adapter constructing each next recipe or entering fabricated development measurements.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P22.03 — Evaluate actual checkpoints with causal ablations and fixed compute

- **ID:** P22.03
- **Tier:** T2
- **Goal:** Evaluate actual checkpoints with causal ablations and fixed compute.
- **Read first:** `docs/research/engine_substrate/COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md`; `evaluation/process_mastery/runtime_attestation.py`; `seeds/native_process_execution.json`; `tests/test_independent_improvement.py`.
- **Touch:** new `evaluation/process_mastery/checkpoint_world_adapter.py`; new `tests/test_checkpoint_world_adapter.py`; new `tests/test_improvement_causal_ablation.py`.
- **Pattern to copy:** P16 source-expression execution checks and same-world native comparators.
- **Steps:** 1. Snapshot genuine ancestor and learned checkpoints without changing goals or host action rules. 2. Run unchanged/adaptive-only/invention-only/full arms through the same learner/native sink at equal cumulative data/primitive budgets. 3. Knock out learned axes, libraries or active operators in development-only control panels and verify the scored path depends on the claimed components.
- **Guard:** read-only frozen checkpoint evaluation; all policies explicit.
- **Acceptance:** `test_all_arms_same_world_and_compute`, `test_changed_active_expression_changes_scored_result`, `test_checkpoint_restore_no_state_leak`, `test_component_ablation_changes_claimed_path`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_checkpoint_world_adapter.py tests/test_improvement_causal_ablation.py tests/test_independent_improvement.py -q -p no:cacheprovider`.
- **Non-goals:** choosing the process in Python by arm name, dropping failed tasks or excluding composition/approval/training costs.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P22.04 — Audit capability levels against demonstrated input breadth

- **ID:** P22.04
- **Tier:** T1
- **Goal:** Audit capability levels against demonstrated input breadth.
- **Read first:** `docs/research/engine_substrate/PMB_V1_SPEC.md`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`; `docs/research/engine_substrate/COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md`; this plan §6.
- **Touch:** new `docs/research/engine_substrate/COGNITION_CAPABILITY_CLOSURE_MATRIX.md`; `docs/research/engine_substrate/PMB_V1_SPEC.md`.
- **Pattern to copy:** existing explicit L1–L7 evidence gates and review gap ledger.
- **Steps:** 1. Map each level to actual world/adaptor/mechanism/held-out evidence and noncovered prerequisites. 2. Record protocol-matched human sources or unavailable status; do not infer human equivalence from perfect synthetic scores. 3. Retain opaque motor/capability/family processes, unsupported raw perception/irregular time and limited language as open with named consumers needed before any further extension.
- **Guard:** documentation only.
- **Acceptance:** every L-level has supported/failed/unavailable disposition and exact evidence; no blanket capability closure from a finite family.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_improvement_estimand.py tests/test_checkpoint_world_adapter.py -q -p no:cacheprovider`.
- **Non-goals:** creating a new benchmark to label the system powerful without its underlying causal learning evidence.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

**P22.01 record (2026-10-23):** Added [`COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md`](COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md) and a ceiling-safe paired estimator. The estimator keeps repeated checkpoints clustered by world, reports exact zero for flat/ceiling/floor paired outcomes, requires complete paired worlds across checkpoints and blocks efficiency claims when paired work differs. Its six estimand fixtures pass.

**P22.02/P22.03/E1 mechanism record (2026-10-23):** A disabled generic P22 policy references expression-digest-attested P19 candidates only when their source task is explicitly training. It creates a candidate-specific proposal, then qualifies it only after a second distinct training task has a native-verified attempt with the same expression tree; the proposal remains non-actionable pending exact approval. Proposal creation terminalizes its source search request, and successful qualification terminalizes both supporting requests. P19 search now also enforces a per-request attempt ceiling and mints at most one candidate per request, selecting the lowest-work verified expression whose key has not already been minted; these controls keep multiple training trials from exhausting the global cap or candidate limit. Tests verify per-request ceilings and one-candidate bounds. Repeated same-goal training worlds use explicit trial keys and remain disjoint from sealed tasks. The five proposal/approval-boundary tests pass. A read-only native finite-process checkpoint adapter scores snapshots on common isolated world IDs and a shared primitive-work ceiling. Unattested synthetic expressions require an explicit development-fixture adapter flag; strict scoring recomputes snapshot digests and rejects tampering. Independent training-world generators cover 3×3 Loopover and 2×2 D4 corner transformations; both generated goals agree with native process composition. The adapter captures generation-zero native ProcessSchema ancestors and adopted candidates only after exact consumed approval and a matching verified execution receipt; child capture verifies the frozen parent's generation and digest. Changed candidate expressions, altered parent snapshots and skipped generations are rejected. Empty world panels, duplicate checkpoint identities, malformed permutations and negative work declarations now fail closed. The cognition-on fixture exercises native search, a candidate-bound approval fixture, native execution, verified simulated receipt and perturbed-state abstention; the approval fixture is test input only. Default isolation and one shared enabled budget pass. Repeat-adoption diagnosis found that recursive expression trees can carry `Surface(Text)` leaves from native `StringConcat`; copying the displayed tree into an approval stores `Str`, which fails recursive native `Eq` even though the visible trees and digest match. Adoption and revocation now compare exact JSON representations for the tree while retaining digest, effect, parameter, guard and epoch bindings. The regression verifies both later recursive adoption and invalidation after a tree mutation. A three-generation native development-lineage test passes proposal qualification, exact test approval, action receipt and immutable parent-linked checkpoint capture on the bounded 4-element fixture and on correctly sized Loopover and D4 fixtures; each lineage is scored on a shared development training world, with unequal declared work correctly blocking an efficiency comparison. Checkpoints now bind parent-linked cumulative primitive work in their immutable digest and enforce the shared ceiling against that total. This closes only the primitive-work dimension; cumulative data, search, approval, model-call, memory and wall-time accounting remain open. Later-generation development goals derive from the parent expression, so this is mechanism evidence, not independent-goal efficacy. All approvals are test fixtures. A fresh two-trial training probe produced qualified, unapproved candidates from correctly sized Loopover and D4 probe batteries; their complete exact bindings and reproducible digests are recorded in [`COGNITION_P22_CANDIDATE_APPROVALS_20261023.md`](COGNITION_P22_CANDIDATE_APPROVALS_20261023.md). Their graph instances were ephemeral and no action or checkpoint was created. Candidate-specific live approvals, independent-goal held-out lineages, four-arm learner comparators, remaining cumulative resource accounting and efficacy remain open; no P22 held-out evaluation has occurred.

**P22.04 record (2026-10-23):** Added [`COGNITION_CAPABILITY_CLOSURE_MATRIX.md`](COGNITION_CAPABILITY_CLOSURE_MATRIX.md) and linked it from PMB v1. It maps all L1–L7 levels to exact phase evidence and leaves each open as failed, not established, or unavailable; human comparisons and unsupported input breadth remain explicit. No level is closed.

**P22 resource-accounting update (2026-10-23):** Each immutable checkpoint now binds parent-linked cumulative primitive work and a digest-verified read-only native graph snapshot. The snapshot records enabled shared ThinkingBudget capacity, remaining and spent values; all node and status counts; search attempts and requests; proposals, qualifications, approval events, world receipts, solve and curriculum tasks, budget denials; and canonical serialized graph bytes. Failed, pending and timed-out statuses remain recorded. Common-world comparisons report whether all recorded dimensions match. This still does not establish training-data exposure, native rule-step or model-call totals, allocator memory or wall-time accounting. Serialized graph bytes measure graph readback size only. Two resource-accounting tests and the P22 regression bundle (108 tests) pass; no P22 held-out evaluation has run.

**P22.01 contract reconciliation (2026-10-23):** The written arm specification now matches P22.03's required four-arm design: unchanged, adaptive-only, invention-only and full. Adaptive-only uses the native curriculum selector with the ancestor portfolio frozen; invention-only uses a frozen nonadaptive task schedule with native proposal/verification/promotion enabled; full enables both. This resolves the prior three-versus-four-arm protocol inconsistency before any E2 freeze. These conditions are specified but their end-to-end learner adapters are still unimplemented.

**P22 arm wiring update (2026-10-23):** Added `configure_p22_arm` to enable the common native ProcessSchema/Solver ancestor path, set the curriculum/invention policy switches on a fresh cognition-on graph for each of the four specified conditions, and initialize exactly one shared ThinkingBudget to the same capacity. It does not select tasks, expressions, approvals or actions. Tests verify all arm switch patterns, unchanged active ancestor portfolios, unknown-arm rejection and the native budget ceiling. The unchanged ancestor solves the current two-primitive composition control in two native steps; therefore that sanity task cannot support binary-success improvement inference. This establishes condition wiring and a same-graph training-task route, while multi-task curriculum feedback and informative all-arm learner panels remain incomplete.

**P22 curriculum/search bridge update (2026-10-23):** The P22 seed now contains a disabled-by-default native bridge from a native-selected `ProcessCurriculumTask` to a training-split `SolveTask` in the same graph and domain. The P22 arm setup enables this bridge only with curriculum conditions and disables the P21 target-learning bridge to prevent cross-phase dispatch. A cognition-on development regression feeds registered training evidence through native curriculum selection, verifies the resulting task enters native process search and produces a verified search attempt, and confirms no adoption approval or world-action receipt was fabricated. A separate common-ancestor control solves the current two-primitive composition in two native steps without any invention candidate. That world is a task-delivery/sink control, not an informative binary-success efficacy world; the E2 development panel must establish non-ceiling tasks for every arm. The focused P22 bundle passes 110 tests. This proves one same-graph task handoff; multi-task curriculum feedback, all-arm learner comparisons, candidate approvals and held-out evidence remain open.

**P22 sequential training feedback update (2026-10-23):** The native bridge now records a `ProcessCurriculumOutcome` after an observed solve, bounded-search completion, proposal, qualification, or budget denial. It preserves the terminal status, split, task key, epochs, and attempt count, closes the selected task, resolves its evidence, and returns the curriculum scheduler to `ready`; P19's finite search rules are ordered before this closeout. A two-task cognition-on regression confirms the first task's native-search outcome reopens the scheduler and the second task is selected and dispatched into the same graph. This establishes sequential delivery and outcome retention only. The selector remains the existing residual-ranked P21 mechanism; outcome-weighted adaptation, all-arm learner adapters and comparisons, candidate approvals, cumulative resource coverage, and held-out evidence remain open.

**P22 arm feedback correction (2026-10-23):** Curriculum dispatch now creates a runnable `SolveTask` (`active` when the common SolverPolicy is enabled; `stuck` only in the explicit search-isolation fixture where that solver is disabled). Native solver completions now close a curriculum task even when no P19 request exists, which is required for the adaptive-only condition; solver impasses are recorded directly only when open-process search is disabled. Development regressions verify both the common-ancestor solve path without invention and the full-condition path through P19 search and sequential task release. The focused P22 regression bundle passes 111 tests. This repairs arm task lifecycle wiring; it does not establish matched learning outcomes, adaptive benefit, candidate approval, or held-out efficacy.

**P22 cumulative accounting update (2026-10-23):** Digest-bound checkpoint snapshots now include registered training-evidence and direct training-task exposures, training outcomes, native solver steps and declared primitive work, P19 attempt work, and requested/approved/denied ThinkingBudget cost. The matched-resource comparator includes these dimensions, so mismatches preclude efficiency claims. The new resource fixtures pass (3 tests). This measures graph-recorded work and exposure only; model-call coverage, allocator memory, and wall time remain unavailable, and the existing serialized-byte field is graph readback size rather than memory.

**P22 v1 development ceiling audit (2026-10-23):** A fixed 32-world training-block control ran the common native solver over the original v1 generators with fresh isolated worlds. It solved 0/32 D4 tasks and 11/32 Loopover tasks. Later goal-diversity audit found only two distinct goals across 200 validation draws in each v1 family; those rates are not an informative independent-goal panel. The D4 panel was also at the ancestor floor. This historical diagnostic is superseded for future development by the v2 panel recorded below.

**P22 task-distribution audit (2026-10-23):** The v1 candidate-packet generators produce only two distinct goals across 200 validation draws in each family, so those cards do not establish independent-goal generalization. Their seeds and exact candidate bindings remain preserved as mechanism evidence. Added versioned v2 generators under disjoint family seed codes: 200 training and 200 validation draws have disjoint IDs/seeds; v2 yields all 8 D4 goals and 190 training / 195 validation Loopover goals. A native composition check verifies the generated goal from each hidden sequence while `agent_view` withholds that sequence. The 32-world common-solver diagnostic on v2 solves 14/32 D4 and 6/32 Loopover tasks, avoiding both ceiling and floor. These are development checks only; v2 is not frozen as the P22 preregistration panel until all matched learner adapters and resource controls pass.

**P22 regression refresh (2026-10-23):** The combined P22 estimator, proposal/adoption, native checkpoint, resource, arm-wiring, causal-ablation and cognition-profile suite passes 113 tests. No P22 held-out draw has been accessed.

**P22 generator and proposal-validation update (2026-10-23):** The combined P22 suite now passes 116 tests. New v2 world generators preserve the v1 candidate packet while providing varied independent-goal development worlds. A read-only verifier scores a digest-attested, training-derived unapproved candidate only against the exact answer-free v2 validation view; it rejects held-out worlds, hidden evaluator fields, guard mismatches, tampered candidates, and candidates already on approval/action paths. This is proposal-generalization support, not an approved checkpoint or a held-out result.

**P22 validation panel reader (2026-10-23):** Added a read-only batch scorer for one unapproved training proposal over a common v2 validation panel. It rejects empty/duplicate IDs and mixed families, verifies each generated answer-free world view, and returns every per-world outcome with a reproducible panel digest. It creates no approval or receipt and chooses no candidate. This develops the evaluation adapter only; it does not replace the four matched learner arms or establish efficacy.

**P22 v2 proposal probe results (2026-10-23):** The reproducible runner searched two distinct same-goal training worlds in each family, retained every proposal, and scored each on the same 200 v2 validation worlds. One proposal per family qualified on the two distinct native training trials; the second remained `awaiting_native_qualification` after those bounded search requests were terminalized for the first proposal. The qualified D4 proposal solved 16/200 validation worlds (8%); the qualified Loopover proposal solved 0/200. Both remaining proposals also scored 16/200 and 0/200 respectively, but are not qualified. All remained unapproved, with zero approvals and receipts. Raw JSON, candidate digests, panel digests, and result hashes are in [`COGNITION_P22_V2_DEVELOPMENT_PROBES_20261023.md`](COGNITION_P22_V2_DEVELOPMENT_PROBES_20261023.md). These are unpaired proposal frequencies, not an improvement estimate; no matched ancestor, curriculum-only, or full learner arms were run. Validation draws 0000–0199 are consumed by the v2 audit/probe and must be excluded from preregistered allocations. The sealed held-out split remains untouched.

**P22 trial-qualification guard and probe regression (2026-10-23):** Qualification now requires a source request already tied to a proposal and a separate funded/proposal-recorded trial request, then terminalizes both requests after one qualification. The regression confirms each qualification cites two distinct verified task identities and does not mint duplicate qualification records. The second proposal can remain pending when another expression has already consumed the bounded request pair; it is kept in the result denominator. The refreshed combined P22 suite passes 117 tests.

The reproducible probe CLI outputs were rerun and matched the archived raw JSON byte-for-byte for both families. P22 resource snapshots now count the two direct training `SolveTask` inputs as training exposure in addition to curriculum evidence exposure. No held-out data or candidate approvals were used.

**P22.E1 profile integration measurement (2026-10-23):** Three fresh `boot_cognition_on()` runs measured a median 0.2020 s boot, 1,520 graph nodes, 773 exported native rules, and 288,952 bytes of canonical graph JSON. The P22 policies remain disabled in the profile; its shared budget and default/conversation isolation regressions pass. The P22 bundle passes 117 tests. Allocator/resident memory remains unavailable, and these boot measurements do not substitute for cumulative matched-arm resource accounting. The cognition-on causal-chain regression now also mutates the approved operator after one verified receipt and confirms exact approval binding abstains before a second world transition. No held-out tasks or real candidate approvals were used.

**P22.E1 acceptance verification refresh (2026-10-23):** The exact E1 verification bundle (`test_improvement_estimand.py`, `test_independent_improvement.py`, `test_checkpoint_world_adapter.py`, `test_improvement_causal_ablation.py`, `test_cognition_profile_integration.py`) passes 88 tests. This confirms the local native mechanism and profile gates; the full four-arm training adapters and external candidate-specific approvals remain outstanding.

**P22 four-arm development wiring probe (initial run, 2026-10-23):** Added a training-only native runner and exercised all four explicit arms on the same eight v2 training worlds per family, with fresh cognition-on graphs and 64 shared-budget capacity. Training-only solved counts were D4 3/8 in each arm and Loopover 1/8 in each arm for unchanged/adaptive/invention/full. These are not effects. Native `global_attempt_ceiling` settlement let every arm terminalize all tasks, but the 64-attempt global limit was overshot by simultaneous grammar activations: D4/Loopover full arms recorded 68/66 attempts, D4 invention-only 108, and Loopover invention-only 132. Digest-bound native rule-progress counters were 9/67/24/96 D4 and 16/109/29/138 Loopover; no external model calls were made. Resource vectors differed across arms, allocator memory and wall-time were unavailable, and no approvals or world receipts were created. This initial raw run is superseded by the hard-cap-refreshed diagnostic below, with the original evidence preserved by its former hashes in the report history.

**P22 global-attempt cap minimization (pre-repair, 2026-10-23):** Reproduced the overshoot in a focused native fixture with a configured cap of one: after funding two requests, one `tick(1)` created six attempts (three compose pairs per task) before settlement. A graph `SetAttr` reservation counter did not serialize simultaneous grammar activations and was removed. The native mutation-boundary repair and its verification are recorded below; post-hoc request terminalization alone remains insufficient. Full details are in the development report.

**P22.02 hard-cap repair contract (frozen 2026-10-23):** The cap is global across every open request and every base/recursive grammar rule. Enforcement occurs in the native effect that creates an `OpenProcessSearchAttempt`: read the current policy reservation and maximum, atomically decline creation at/above the limit, otherwise increment the reservation and create/bind the attempt in that firing. Later edge effects must no-op when creation was declined. The existing rule-level `Count` guards remain an early filter only. Acceptance requires exact `attempt_nodes <= max_attempts` under simultaneous task/request activations, the reservation count to equal created attempts, per-request ceilings to remain enforced, restart persistence of the counter, and unchanged candidate provenance/qualification. Freeze this behavior before E1/E2; do not replace the global limit with a larger ceiling or post-hoc settlement.

**P22.02 hard-cap implementation and refreshed diagnostic (2026-10-23):** Added `AddNodeWithinCounter` to atomically reserve and create each attempt in the native rule effect. The minimized two-task cap-one regression now creates one attempt and verifies reservation parity. The refreshed eight-world runs create exactly 64 attempts/reservations in each invention-enabled D4/Loopover arm and zero in the two arms with invention disabled. Solved counts remain D4 3/8 and Loopover 1/8 in every arm. The refreshed raw hashes are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). The focused cap/resource/P22 runner bundle passes 19 tests; the expanded P22 regression bundle passes 118 tests. Resource vectors remain unequal and memory/wall-time remain unavailable, so no efficiency effect is supported. This repairs the cap prerequisite but does not establish independent-goal learning, cross-family approved checkpoint lineages, or candidate authorization; P22.E2/E3 remain open.

The refreshed combined P22 regression bundle, including `tests/test_p22_four_arm_development.py`, funded-request ceiling settlement, and digest-bound native rule-progress accounting, passes 120 tests. Both four-arm raw JSON files were rerun byte-identically; their hashes are recorded in the development report.

**P22 resource instrumentation refresh (2026-10-23):** The CLI now runs each four-arm development condition in an isolated worker process, recording per-arm elapsed time and digest-bound `ru_maxrss` peak process RSS. On the same eight-world training-only panels, wall time was 0.228–0.264 s for D4 and 0.230–0.292 s for Loopover; peak process RSS was 63.9–64.5 MB for D4 and 63.2–64.5 MB for Loopover. These single-host measurements include interpreter/native-runtime and setup overhead, are scheduling-sensitive, and do not measure native graph allocator bytes. Wall time is retained as an observed outcome rather than an exact-match dimension. Resource vectors remain unequal; exact candidate authorization and independent-goal checkpoint lineages remain open, so E2/E3 are still gated. Refreshed hashes and limitations are in the development report.

**P22 cumulative resource accounting correction (2026-10-23):** Audit found that the earlier `serialized_graph_bytes` calculation summed node records but omitted graph edges. The snapshot now measures the canonical full `graph_to_dict()` JSON, records graph node/edge counts, and includes native `memory_total_bytes()` as a separate graph-memory estimate. Refreshed training-only eight-world artifacts preserve the same solved/proposal counts and still show unequal resource vectors; no resource-matched or efficiency claim follows. D4 full-graph bytes range 275,805–372,400 and native graph-memory estimates 163,135–205,280; Loopover ranges 283,098–388,032 and 169,144–226,542, respectively. The native estimate is distinct from process RSS and allocator-wide memory. Updated raw hashes and detailed values are in the development report. Snapshot regression checks confirm exact correspondence to the native persistence and memory APIs. P22.E2/E3 remain gated on working matched controls, authorized cross-family lineages, and the remaining preregistration requirements.

**P22.03 verification refresh (2026-10-23):** The named P22.03 adapter, causal-ablation and independent-improvement suite passes 25 tests, including four-checkpoint same-world scoring, fixed-work comparison, expression-change sensitivity, restore isolation, and family-sized three-generation test lineages. Checkpoint capture now accepts measured native rule-step/model-call and peak-RSS counters and binds them inside the immutable graph-resource snapshot; descendant captures fail closed if cumulative rule steps, model calls, or search reservations regress. Regressions confirm counter preservation through strict digest-checked scoring and rejection of a regressed descendant. These fixtures validate native checkpoint mechanics and test-only approval plumbing; they do not supply live candidate authorization or independent-goal efficacy. The four-arm development runner and refreshed resource snapshots remain diagnostics with unequal realized work/graph vectors. E2 is not frozen; no held-out allocation was read.

**P22 native proposal validation refresh (2026-10-23):** The four-arm development runner now evaluates every digest-verified unapproved candidate on a common, disjoint answer-free v2 validation panel without approval or world execution. D4 draws 0350–0357 yielded 5 invention-only and 1 full candidate node, with every candidate scoring 1/8; three unique invention-only digests were present and one digest also appeared in full. Loopover yielded no proposal in any arm, so no candidate score was imputed. The resource vector counts each native validation evaluation. The generated raw files and hashes are recorded in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). Training draws 0250–0257 and validation draws 0350–0357 are consumed for development and unavailable to later preregistration. This improves the development adapter audit but remains a selected small-panel diagnostic, not a four-arm effect or checkpoint lineage; P22.E2/E3 remain open.

**P22 higher-ceiling comparator pilot (2026-10-23):** The runner now takes one explicit global/per-request attempt ceiling applied identically to all arms. At a common development ceiling of 10,000 on two fresh v2 training tasks per family, both invention-enabled arms produced digest-attested candidates in D4 and Loopover; unchanged/adaptive-only remained proposal-free. All arms terminalized, but all solved 0/2, resource vectors differed, and candidate validation panels contained only two worlds. No approvals or receipts were created. This shows the earlier Loopover no-proposal outcome depended on the 64-attempt ceiling, so the small 64-cap panels do not establish a working proposal comparator for that family. The 10,000 ceiling is exploratory, not an E2 choice. Raw hashes and candidate scores are recorded in the development report; training draws 0260–0261 and validation draws 0360–0361 are consumed. P22.E2/E3 remain open pending informative non-ceiling development controls, authorized checkpoint lineages, and the preregistration gates.

**P22 eight-task comparator development refresh (2026-10-23):** With the common 10,000-attempt ceiling, all four arms terminalized on eight fresh tasks in both families. Every arm solved D4 5/8 and Loopover 2/8; invention-only/full produced proposals in both domains, which were scored nonactionably on eight disjoint validation tasks. The D4 candidate scores were 1/8, 2/8 and 0/8 across three unique digests; Loopover candidates all scored 0/8. No approvals or receipts were created; resource vectors differed. This verifies both domain adapters execute candidate proposal and validation paths but offers no benefit result and does not close the authorized checkpoint lineage gate. Artifacts and hashes are in the development report. Training 0270–0277 and validation 0370–0377 are consumed development allocations. E2/E3 remain open.

**P22.01 inference reconciliation (2026-10-23):** The independent-improvement contract now matches the Phase 22 practical trend criterion (point slope ≥0.05 per generation) and specifies the two one-sided zero-effect tests per family, 10,000-world-cluster bootstrap p-value calculation, and phase-wide Holm adjustment at α=.01. `improvement_estimand.summarize_families` reports both endpoint bounds, raw bootstrap p-values and Holm-adjusted values; all-success/floor/flat data remain exactly zero and fail the practical thresholds. Its tests pass 11 cases, including positive and null trends under multi-family Holm, exact generation allocation, immutable thresholds, and invalid input rejection. The full P22.E1 verification bundle passes 93 tests. This closes an inferential-specification inconsistency before any P22 freeze; it does not supply the missing authorized checkpoint lineages or held-out outcomes.

**P22.E2 analysis implementation (2026-10-23):** Added `analyze_linear_p22_v1.py` with a standalone `--self-check` and strict complete-panel schema. It checks exact family/generation/arm/world coverage, stable goal/world digests, checkpoint roots and parent links, approval/receipt evidence for invention lineages, all declared cumulative resource fields and ceilings, and zero-tolerance structural controls. It retains non-scored rows as failures, reports per-arm Wilson intervals, exact full-versus-ancestor McNemar tests, paired resource distributions with deterministic 10,000-resample bootstrap intervals, and the registered phase-wide Holm estimator. Its seven self-check cases cover null scores, timeouts, unsafe outputs, comparator disagreement, missing resource sources, partial resource measurements, and flat panels. Five analyzer tests and the CLI self-check pass. This is analyzer infrastructure only: the P22 runner, matching development comparators, frozen preregistration, authorized lineages, and all held-out work remain open.

**P22.E2 split-integrity correction (2026-10-23):** Analyzer review found reporting gaps: training, selection, validation and evaluation identities were not required to be disjoint, and a development payload could be labeled `ATTESTED` despite lacking a held-out runtime attestation. The analyzer requires all four allocations by family, rejects repeated or overlapping identities, and labels development provenance `DEVELOPMENT_ONLY`. A focused regression and self-check cover split overlap; six analyzer tests pass. This remains analyzer-only work, and P22.E2 is still open.

**P22.E2 selection-split enforcement (2026-10-23):** Re-auditing the analyzer against the independent-improvement contract showed its earlier integrity check omitted the explicit candidate-selection block. The schema now requires `selection_world_ids_by_family`, checks selection against training, validation and evaluation for within-family overlap, rejects identity reuse across any split or family, and requires at least 200 selection worlds per family on held-out payloads. Missing and overlapping selection allocations are covered by regressions. Analyzer tests pass 6/6 and its standalone self-check passes. This is a fail-closed schema correction; no held-out worlds were read.

**P22.E2 native-work resource alignment (2026-10-23):** The analyzer's required resource vector now includes `native_rule_term_evaluations`, which the checkpoint resource adapter reports only from a verified per-rule native snapshot; missing values remain unavailable and fail the panel rather than becoming zero. The standalone self-check now includes selection-split integrity, and accounting/checkpoint/analyzer tests pass 29 cases with the self-check. No held-out allocation was read.

**P22.02 candidate-binding reconstruction (2026-10-23):** Training-only proposal probes now emit the exact candidate expression/effect/guard/parameter/epoch binding and qualification witnesses without replaying validation. Fresh graph reconstructions on the selected D4 `0200→0202` and Loopover `0015→0026` training pairs reproduced the expected digests and distinct-goal witnesses; both recorded zero approvals and receipts and no validation worlds. The Loopover replay exposed and corrected a one-character transcription error in the candidate-approval packet against both authoritative raw artifacts. The complete five-test proposal module passes after adding the training-only binding case. This only improves exact reviewability and preserves consumed training evidence; no simulated action occurred and candidate authorization/checkpoint gates remain.

**P22.E2 resource provenance guard (2026-10-23):** The analyzer now requires a named measurement source for every declared per-row resource field and rejects unavailable or partial event-only coverage as a resource measurement. Its self-check exercises missing-source and partial-measurement cases in addition to null, timeout, unsafe-output, comparator-disagreement and flat-panel cases. This closes a reporting-integrity hole only; a real runner must supply source-backed counters for all fields before held-out analysis can pass. P22.E2 remains open.

**P22.03 analyzer resource adapter (2026-10-23):** Added `analyzer_resource_record` to convert a digest-valid native snapshot into P22 analyzer resource values with a named source and coverage status for each field. It maps measured graph/runtime values, caller-supplied cumulative lineage work and isolated-worker wall time; proposal, verification and approval event counts stay `PARTIAL_EVENT_COUNT`, while uninstrumented dimensions become `None`/`UNAVAILABLE`. The adapter rejects tampered snapshots, invalid counters and cumulative primitive work below snapshot-observed work. Resource-accounting and analyzer tests pass 12/12. This enables honest row construction but cannot pass E2 until missing direct instruments and the actual runner/lineages are supplied.

**P22.02 no-candidate failure retention (2026-10-23):** The development proposal probe now preserves a first-task no-candidate outcome with exact training identities, goal digests, task statuses and native request/attempt counters instead of raising before an artifact is written. On fresh distinct-goal draws 0286/0287, one D4 candidate qualified and scored 4/8 in a selected eight-world validation panel; a second was unqualified. Loopover produced no first-task candidate; its second-task candidate remained unqualified and scored 0/8. Neither pair created an approval or receipt. These selected small-pair observations are mechanism diagnostics, not efficacy or qualification-rate evidence; draws 0286/0287 and validation 0386–0393 are consumed. Artifacts and hashes are in the development report. The full P22 probe module now passes 5 tests after the per-request ceiling extension. Cross-family approved lineages and P22.E2/E3 remain open.

**P22.02 independent-goal reliability follow-up (2026-10-23):** Two additional distinct-goal training pairs per family preserve qualification uncertainty: D4 qualified one candidate on pair 0290/0291 (0/8 validation), while pair 0288/0289 did not qualify; neither Loopover pair qualified. All candidate scores and unqualified outcomes remain present in raw artifacts. Across the three fresh pairs 0286/0287–0290/0291, D4 qualified on 1/3 and Loopover 0/3; this small diagnostic is not an estimated rate or efficacy. No approval or receipt was created. Training 0288–0291 and validation 0394–0409 are consumed. Raw hashes and limitations are in the development report.

**P22.02 search-ceiling diagnostic (2026-10-23):** The proposal probe now separates its per-request limit from the fixed 30,000 global cap. A confounded 20,000-global/20,000-per-request Loopover run on draws 0292/0293 exhausted the global budget on its first task and is retained as a diagnostic. A new distinct-goal pair 0294/0295 with a 20,000 per-request limit generated one candidate on the first request, then exhausted the remaining 10,000 global attempts on the second; the candidate did not qualify and scored 0/8 on validation. No approval or receipt was created. This demonstrates proposal-path sensitivity only, not qualification reliability or efficacy. Training 0292–0295 and validation 0410–0425 are consumed; exact hashes and limit details are recorded in the development report.

**P22.03 native rule-work diagnostic (2026-10-23):** The isolated development probe can opt into native per-rule work capture, with rule-index/name attribution, a digest-bound snapshot and guaranteed audit reset. On fresh distinct-goal D4 training draws 0296/0297 and validation draws 0426–0433, it recorded 1,547 rule enumerations, 580,108 candidate pairs/tests and 301,479,018 term evaluations across 178 rules. The candidate scored 2/8 nonactionably; no approval or receipt was created. This is a direct native runtime-work measurement for that probe, not an efficiency comparison; it excludes host-side work, allocator memory and wall time. Draws are consumed. Details and raw hash are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). Resource-matching, authorized lineages and held-out evaluation remain open.

**P22.03 four-arm work-accounting integration (2026-10-23):** Each isolated learner-arm worker can now collect digest-verified per-rule native work and include the totals in its resource snapshot. The comparator flags partial capture and compares term evaluations, rule enumeration, candidate testing and other observed metrics alongside existing dimensions. Native rule identity is complete when available; unmatched indices remain explicit and mark identity coverage partial while preserving direct aggregate counters. The analyzer resource adapter reports term evaluations only when a named capture source exists. Fresh D4 two-task panels at a 64-attempt ceiling captured all four arms: on draws 0302/0303 (validation 0434/0435), each arm solved 1/2 and term evaluations ranged 2,725–62,136; on a fresh draw pair 0304/0305 (validation 0436/0437), each solved 1/2 and term evaluations ranged 2,717–41,742, with complete identity coverage. In both, invention-only/full proposed one candidate each, resource vectors remained unequal, and no approval or receipt was created. These small development data are instrumentation checks only and are consumed. Resource accounting, four-arm, analyzer and checkpoint-adapter modules pass 32 tests. Raw hashes and limits are in the P22 development report. E2/E3 remain open.

**P22.03 checkpoint resource lineage guard (2026-10-23):** Generation-zero and adopted checkpoint capture now accept digest-verified native rule-work snapshots. Descendant capture requires every previously measured native-work metric to remain present and nondecreasing, alongside the existing cumulative runtime-counter checks; the resource snapshot remains bound into the immutable checkpoint digest. A regression rejects a child whose term-evaluation total falls below its parent. The E2 estimand, lineage, causal-ablation, checkpoint and analyzer bundle passes 41 tests. This closes a lineage-accounting mechanism only; no live cross-family approval or checkpoint lineage was created, and P22.E2/E3 remain open.

**P22 regression verification refresh (2026-10-23):** The broader integration bundle (`test_improvement_estimand.py`, `test_independent_improvement.py`, `test_checkpoint_world_adapter.py`, `test_improvement_causal_ablation.py`, `test_cognition_profile_integration.py`, and `test_analyze_linear_p22_v1.py`) passes 98 tests. The exact E2 verification bundle without profile integration passes 41 tests. The five-test native proposal-probe module also passes after the separate per-request ceiling API was added. These checks validate mechanisms and schema guards; they do not close the missing Loopover learning comparator, resource dimensions or authorized lineages, and no held-out access occurred.

**P22 shared regression gate refresh (2026-10-23):** The baseline verifier reports four held RED tests, zero newly GREEN entries and zero NEW RED entries. The 20-file suite sweep reports 16 GREEN, two RED (frozen-core and dual-process), one `NOT_ESTABLISHED` timeout at 420 seconds (`test_capability_control_fabric_migrated.py`), and one `ALL_SKIPPED` file (`test_staleness_decay_migrated.py`). The report records HEAD `b19b904f`; the worktree was dirty, so this is a current working-tree gate result, not a clean-commit attestation. The classifications match the plan's recorded inherited limits; they are not fixed or reclassified by P22. Raw report: `/tmp/cognition-linear-gate.json`, SHA-256 `de681e9185528124d03f1cb38fbecd3a909ed0e26290110dd1e470a97c320498`. Command: `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/failure_baseline_sweep.py --files-from scripts/cognition_gate_suite.txt --workers 4 --timeout 420 --out /tmp/cognition-linear-gate.json`. No P22 held-out allocation was accessed.

**P22.03 resource-coverage refresh (2026-10-23):** Native snapshots now bind canonical byte counts for the training evidence/task/outcome node payloads and an explicit map of measured versus unavailable resource dimensions. The separate full-graph serialized-byte count still includes edges. Fresh eight-task, 10,000-attempt-ceiling diagnostics on D4 and Loopover draws 0278–0285 with validation draws 0378–0385 terminalized every arm. D4 solved 3/8 per arm with five invention-only and four full proposals; Loopover solved 1/8 per arm with no proposals. Resource vectors remain unequal, and the coverage audit identifies missing retrieval, proposal/verification work, model refinement, definition/decoder, approval and rollback costs. No approvals or receipts were created. Raw hashes and process-level measurements are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md); these draws are consumed development data. Resource-accounting and four-arm tests pass 10/10. P22.E2/E3 remain open, with no held-out access.

**P22.03 resource event counters (2026-10-23):** The snapshot now retains exact ThinkingBudget request cost by `requester_kind` and digest-binds counts for search attempts/proposal records, qualifications, candidate-validation evaluations and approvals. These are counts and declared budget costs, not an unsupported conversion to operation cost; proposal/verification work units and retrieval, refinement, decoder, rollback and human-approval costs remain gaps. Replaying the same consumed eight-world development allocation with the expanded schema reproduced the earlier outcomes, not a new independent sample: D4 solved 3/8 per arm and generated five invention-only/four full proposals; Loopover solved 1/8 per arm with no proposals. Raw hashes are recorded in the development report. The resource comparator now treats a missing candidate-validation counter as incomplete rather than an equal zero; 20 accounting/checkpoint tests pass. E2/E3 remain open.

**P22 distinct-goal qualification diagnostic (2026-10-23):** A separate training-only probe gave native search two independently generated v2 goals per family: D4 draws 0200/0201 and Loopover draws 0206/0207. The runs produced two and one candidates respectively, but none qualified on the second task. Nonactionable eight-world development validation yielded 3/8 and 0/8 for the D4 candidates and 0/8 for Loopover. No approval or world receipt was created. This is mechanism-level `NOT_ESTABLISHED`, not an efficacy estimate. It confirms current same-target qualification evidence cannot be treated as independent-goal learning. The raw files and hashes are in the development report; training draws 0200–0207 and validation draws 0201–0208 are consumed and excluded from any future preregistration.

**P22.02 distinct-goal composition repair and development result (2026-10-23):** The earlier zero-qualification probe remains unchanged as historical evidence. Added a native candidate-as-operand composition attempt before broad recursive expansion and a dedicated mint rule for its verified child, whose digest binds the parent candidate. `AddNodeWithinCounters` now atomically reserves both the shared policy ceiling and per-request ceiling at insertion; request reservation counts equal attempt edges. The focused suite passes 26 tests, the native Rust suite passes 869 tests (4 ignored), and engine provenance passes 9 tests (1 skipped). Selected development fixtures qualified one source candidate in each family: D4 training goals `0200→0202`, Loopover `0015→0026`. The D4 source digest is unchanged from candidate `#752` in the prior approval packet; the Loopover candidate is a different expression/digest from its prior packet entry. Both child candidates remain unapproved. No approval, world receipt, or checkpoint was created. The eight-world validation scores (D4 source/child 3/8 and 1/8; Loopover 0/8 and 0/8) are descriptive only; Loopover's training pair was selected by inspecting generated composition relations. This proves a bounded native qualification mechanism on selected fixtures, not general independent-goal learning or efficacy. Raw hashes and consumed allocations are recorded in [`COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md`](COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md). Validation draws 0201–0208 remain excluded from all future preregistered allocations. P22.E2/E3 remain open.

### P22.E1 — Integrate the native phase and audit causal dependencies

- **ID:** P22.E1
- **Tier:** T2
- **Goal:** Integrate the native phase and audit causal dependencies.
- **Read first:** `substrate/boot_profiles.py::COGNITION_ON_SEEDS`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** existing guarded cognition profile and one-budget integration.
- **Steps:** 1. Integrate independent-goal multi-generation loop and checkpoint evaluation with disabled defaults and declared dependency closure. 2. Execute world input→native choice→authorized result→observed receipt through the actual consumer. 3. Perturb the learned state/operator/model and verify the declared causal path changes or abstains; record boot/memory/work and default isolation.
- **Guard:** cognition-on opt-in only; no new host approval assumed.
- **Acceptance:** `test_p22_native_causal_chain`, `test_p22_state_perturbation_changes_execution`, `test_p22_default_isolation`, `test_p22_shared_budget`; no Python agent dispatch.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_improvement_estimand.py tests/test_independent_improvement.py tests/test_checkpoint_world_adapter.py tests/test_improvement_causal_ablation.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** a disconnected lifecycle fixture substituted for scored execution.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P22.E2 — Freeze an informative matched-arm evaluation

- **ID:** P22.E2
- **Tier:** T1
- **Goal:** Freeze an informative matched-arm evaluation.
- **Read first:** `docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md`; `evaluation/process_mastery/harness.py`; `evaluation/process_mastery/scorecard.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/process_mastery/linear_p22_v1.py`; new `evaluation/process_mastery/analyze_linear_p22_v1.py`; new `docs/research/engine_substrate/COGNITION_LINEAR_P22_PREREG.md`.
- **Pattern to copy:** P15 fixed artifact/allocation checks, corrected by P16 actual extension attestation.
- **Steps:** 1. Implement the phase-specific panels, working comparators and development self-checks. 2. Freeze task/source distributions independently of learned operators; include all failures and every declared resource. 3. Freeze actual loaded-native/source/wrapper/build/profile/world hashes and commit preregistration alone before sealed allocation access; use §5 CLI and extension rules.
- **Guard:** evaluation only; no frozen historical protocol edits.
- **Acceptance:** all arm adapters and structural audit controls pass development checks; effect criteria, exposure limits and exact allocations frozen; missing adapters prevent freeze.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_improvement_estimand.py tests/test_independent_improvement.py tests/test_checkpoint_world_adapter.py tests/test_improvement_causal_ablation.py tests/test_analyze_linear_p22_v1.py -q -p no:cacheprovider`.
- **Non-goals:** threshold tuning on held-out data; non-working controls scored as zero skill; superiority inferred solely from unequal macro-call expressiveness.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

### P22.E3 — Report all outcomes and decide the next supported entry

- **ID:** P22.E3
- **Tier:** T1
- **Goal:** Report all outcomes and decide the next supported entry.
- **Read first:** `docs/research/engine_substrate/COGNITION_LINEAR_P22_PREREG.md`; `evaluation/process_mastery/linear_p22_v1.py`; `evaluation/process_mastery/analyze_linear_p22_v1.py`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_LINEAR_P22_RESULTS.md`; this plan; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Pattern to copy:** earlier immutable negative ledgers plus P16 provenance classification.
- **Steps:** 1. Run the frozen allocation once and archive raw bytes/hashes and artifact identities. 2. Report all benefit and zero-tolerance structural criteria, learning curves, resource denominators and unsupported inputs. 3. Mark the next entry supported only when its native consumers and evidence paths exist; retain negative benefits and add explicit repair tasks for failed structural gates.
- **Guard:** new frozen protocol; documentation closeout only.
- **Acceptance:** every registered criterion classified; exact-native artifact attested; no missing arm hidden; next entry supported or explicitly blocked.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_improvement_estimand.py tests/test_independent_improvement.py tests/test_checkpoint_world_adapter.py tests/test_improvement_causal_ablation.py -q -p no:cacheprovider`.
- **Non-goals:** closing a missing mechanism as merely an unfavorable efficacy result; rewriting P15 or earlier holdout outcomes.
- **Done when:** the specified mechanism, provenance and §5 regression gates pass; the phase evaluation reports its registered outcomes without weakening criteria. A passing fixture cannot replace a missing end-to-end consumer or comparator.

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


### Additional gates for Phases 16–22

- **Artifact identity:** P16's runtime attestation is mandatory for every new freeze, including the actual loaded native extension, wrapper, build metadata, relevant full Rust source closure, profile, generators, world code and analyzer. Missing/dirty artifact identity blocks a held-out run. Do not use the P15 wrapper hash as evidence for native provenance.
- **Causal execution:** the same graph-selected expression/model/acquired distinction must reach the scored native execution path. Native mutation/knockout controls must change or block that path. Host code can generate independent world truth and externally score results; it cannot choose the agent's operator, compile a target-specific recipe or decide adoption by arm name.
- **Independent goals:** task generation cannot use active operator/candidate name, power, generation index or learned solution. All arms share the same world and primitive/model access; checkpoint evaluation uses fixed task distribution and matched primitive-work ceilings. Record literal task IDs/seeds and enforce disjoint training/selection/evaluation allocations. Extend the existing namespace with phase codes 16–22 and check every prior recorded range for collisions before freeze.
- **Working controls:** every comparator must execute and learn on declared development sanity worlds before E2 freezes. Missing adapters are hard errors. All-zero held-out performance is allowed when it comes from a real learner, and all-success outcomes must yield an honest zero improvement under the chosen estimator. Do not condition primary work comparisons only on successful treatment cases or silently drop censored failures.
- **Coverage and order:** required native consumer/provenance/support tests must pass before advancing. Failed benefit hypotheses remain failed with named safe fallbacks. L-level closure additionally requires its particular model, learning, transfer, explanation or human-baseline evidence in the closure matrix; no new arbitrary stopping criterion is introduced by this planning update.

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

Continue **P22.03** with candidate-authorized native lineage evaluation, resource matching, and the preregistered development audit. The four actual arm checkpoint adapters, common registered-world evaluator, cumulative primitive accounting, isolated wall-time/RSS capture and full resource snapshots are implemented for Loopover and D4. The P22 held-out runner has now been corrected to restore each full checkpoint graph in an isolated native learner and score an externally assigned task through its native solver; evaluation-only task records are excluded from training exposure, and the analyzer requires budget and no-action invariants. This path is synthetic-fixture tested only; no registered held-out world has been read. Corrected single-world and 12-world training panels still use generation-zero roots, so no approved experimental descendant lineage has been evaluated. Realized work and resource vectors differ across arms, so efficiency is not established. The selected training-only cross-goal composition mechanism and one exact simulated adoption in each family remain mechanism evidence only. The D4 request for digest `badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255` is still incomplete until the reviewer supplies numeric `review_seconds`; no action may be created from a plain approval. Further lineage generations require separate candidate-specific authorizations. Do not freeze or score the P22 held-out allocation until approved cross-family lineages and a committed standalone freeze exist. P21's valid failures and P15's `NOT_ESTABLISHED` trend remain unchanged; do not rerun or rescore historical sealed allocations.

The immediate next goal is to test whether acquired qualia changes what the agent predicts and does. P16's attested graph-selected expression path and verified finite-world receipts are available as bounded execution interfaces; its primitive-search solve rate is not a general strategy result. This user-requested extension authorizes planning and ordinary implementation tasks; it grants no new candidate-specific operator approval beyond those already recorded.

**P7.03 implementation record (2026-10-22):** Added generated `qualia_acquisition` with its policy disabled by default. Observed feature/outcome records must match owner, episode, event and source/model/frame epochs, then receive an approved ThinkingBudget request before witness creation. Three distinct recurrence witnesses propose one owner/feature candidate; two fresh contexts must repeat supported consequences before a `QualiaDimension` becomes standing. Contradictions retain their validation evidence and mark the dimension contested; two fresh positive validations restore standing, and earlier episode witnesses can be decoded through the acquired coordinate. The named P7.03 acceptance cases plus no-target, finer-grain, funding exhaustion, stale receipt and owner separation controls are covered. Verification: `tests/test_qualia_acquisition.py tests/test_experience_signature.py tests/test_qualia_dimension_compensation_migrated.py` — 27 passed.

**P7.03 limits:** The producer uses observed feature→outcome recurrence as the residual test; it does not yet run a general explanatory comparison against every existing dimension or implement finer-grain sweeps. It stores witnessed categorical consequences and keeps the existing live overlay separate; it does not infer a calibrated standing-significance scalar. Retirement on epoch expiry/deletion and recovery after repeated revision cycles remain unsupported. The registered P7 evaluation must score only capabilities actually exercised and preserve these as open criteria.

**P7.04 semantic freeze (2026-10-22):** `COGNITION_NUMEROSITY_CONTRACT.md` freezes source-bound sensor inputs, the ≤4 individuated-token route, aggregate-only larger-set route, explicit uncertainty and abstention, confound controls, equal-ratio scale behavior, and the separation between O(n) scene ingestion and bounded graph decision work. Four planned P7.05 acceptance names are present as skipped placeholders, not passing mechanism tests. Existing symbolic `NumberWorld` verification passed 5 tests; this does not establish perceptual numerosity.

**P7.05 implementation record (2026-10-22):** Added generated `numerosity` with `NumerosityPolicy.enabled=0` and two separate graph-rule routes. Clear small sets compare at most four source-bound individuated object nodes; five or ambiguous tokens abstain. Aggregate groups expose only occupied area, density signal and their uncertainty; rules calculate bounded intervals, return more/less/same only when supported, and abstain on crossed area-density cues or unresolved intervals. Added the mechanical `perceptual_scene_attrs` boundary in `domains/number_world.py`; it bounds sensor regions, validates finite nonnegative aggregate values and has no exact-count field. The existing symbolic line world was not changed. Verification: `tests/test_numerosity_migrated.py tests/test_number_world_migrated.py tests/test_qualia_acquisition.py tests/test_experience_signature.py tests/test_cognition_profile_integration.py` — 49 passed before the final two small-set boundary assertions; `tests/test_numerosity_migrated.py` then passed 7 tests.

**P7.E1 integration record (2026-10-22):** Added `experience_signature`, `qualia_acquisition` and `numerosity` to the explicit cognition-on profile only. The three profile acceptance tests verify rule registration, default/conversation isolation, one enabled shared ThinkingBudget and disabled P7 policies. Boot measured 0.1509 s, 974 graph nodes and 546 rules; allocator memory remains unavailable. Focused profile plus P7 implementation bundle passed 49 tests. Evidence remains simulator/graph observations; no external sensor or physical receipt adapter is claimed.

**P7 implementation limits before evaluation:** Aggregate magnitude is currently the product of two supplied sensor signals with first-order uncertainty bounds; no calibrated visual sensor producer has been established. The graph does not yet learn uncertainty parameters, and it does not route unresolved numerosity to a learned significance dimension. P7.E2/E3 must report these limitations and may not score synthetic aggregate inputs as real-world perception.


**P7.E2 freeze record (2026-10-22):** `COGNITION_LINEAR_P7_PREREG.md` was committed alone as `60546572` after both runner/analyzer self-checks and seven concrete development outcomes passed. It freezes 1,760 held-out scorecard rows, disjoint seed allocations, profile/engine/source hashes, limits, scorer separation, control criteria and the explicit unsupported disposition for downstream transfer and calibrated visual perception.

**P7.E3 result record (2026-10-22):** See [`COGNITION_LINEAR_P7_RESULTS.md`](COGNITION_LINEAR_P7_RESULTS.md) for all metrics and hashes. All 1,760 rows completed; episode acquisition validated 40/40 trials in each experience-built world versus 0/40 frozen-space, with zero source leaks. Exposure-only and orthogonal controls produced no candidates, and shuffled labels remained detached. Synthetic numerosity fixtures passed 200/200 small-set and 200/200 in each of four ratio bins, with zero equal-ratio scale difference. Downstream transfer and real-world perception remain NOT_ESTABLISHED, not inferred from the mechanism panel. P8 entry is authorized for source-bound observed episode learning and the acquired-axis interface only; unsupported P7 capabilities are not prerequisites for that entry.

**P8.01 semantic freeze (2026-10-22):** `COGNITION_MODEL_LEARNING_CONTRACT.md` freezes source-bound observed pre/action/post traces, typed object binding, finite effect templates, competing consistent hypotheses, counterexample retention, epoch invalidation, unknown/identifiability behavior and funded search bounds. Four planned acceptance names are present as skipped placeholders until P8.02; they are not passing tests. P7's synthetic numerosity features are explicitly outside the observation basis for learned world models.

**P8.02 implementation record (2026-10-22):** Added generated `process_induction` with a disabled `ModelLearningPolicy`. Owner/episode/event and source/model/frame-matched action and outcome receipts gate a ThinkingBudget request; only approved traces enter learning. Two distinct objects and episodes with the same typed action/pre/effect mint an empirical candidate, with support links. Contradictory outcomes create retained `ProcessCounterexample` records and dispute the candidate while competing effect candidates remain. A new-object query creates a `predicted` result without adding an observation; a newer observed model epoch marks attached old plans stale. Bounds guard hypothesis count and examined funding requests. Verification: `tests/test_process_induction.py tests/test_process_native_views.py` — 23 passed. General program induction, calibrated stochastic distributions and source-epoch lifecycle expiry remain unsupported.

**P8.03 implementation record (2026-10-22):** Added generated `latent_process` with a disabled policy. Owner/event and source/model/frame-matched transition residuals receive funded requests before inference. Three distinct complete, regularly sampled windows with a repeated feature→residual relation propose a bounded candidate; a matching held-out continuation validates it. Shuffled mappings and irregular windows remain candidate-free. Verification: `tests/test_latent_process.py tests/test_temporal_escalation_migrated.py` — 21 passed. This supports only the explicit residual fixture; it does not establish general latent-variable induction or irregular-stream handling.

**P8.04 implementation record (2026-10-22):** Added generated `experiment_design` with a disabled policy. The native rules request budget only for allowed probes whose retained predictions differ, select the lowest-cost probe with a stable tie-break, and refuse host-vetoed or non-informative choices. Numeric VOI remains absent because prior probabilities are not established. An observed result appends per-hypothesis support/disconfirmation audits, retains a counterexample on a refuted hypothesis, and increments the world-model projection version with a result-linked recomputation audit. Verification: `tests/test_experiment_design.py tests/test_cognition_manifold_migrated.py tests/test_thinking_budget_migrated.py` — 23 passed. The projection revision is a finite graph projection fixture; no external world refinement or sink adapter is claimed.

**P8.E1 integration record (2026-10-22):** Added process induction, latent-process search and experiment design to the explicit cognition-on profile. All three policies remain disabled at boot; default and conversation profiles remain isolated. The P8 focused bundle passed 37 tests. Boot measured 0.1501 s, 977 graph nodes and 563 rules; one shared ThinkingBudget remains enabled, allocator memory is unavailable. Inputs and receipts remain graph-simulator fixtures, not external actuator outcomes.


**P8.E2 freeze record (2026-10-22):** `COGNITION_LINEAR_P8_PREREG.md` was committed alone as `df072293` after the runner/analyzer self-checks and six concrete development outcomes passed. The freeze records 1,100 held-out rows, non-overlapping seed blocks, three equal-exposure mechanism arms, temporal controls, funded refinement trials, runner/engine/profile hashes and the supplied-hypothesis limitation.

**P8.E3 result record (2026-10-22):** See [`COGNITION_LINEAR_P8_RESULTS.md`](COGNITION_LINEAR_P8_RESULTS.md) for the full ledger. The native selector scored 200/200 versus 100/200 fixed and 0/200 passive on supplied finite portfolios; all arms used one interaction per world. One hundred regular latent continuations verified, and all missing/irregular controls stayed unknown. One hundred funded graph projection fixtures updated their audit/version. The registered mechanism thresholds pass within these fixtures; general world induction, numeric VOI and external refinement remain NOT_ESTABLISHED. Phase 9 entry is authorized only for the typed effects and finite evidence/probe interfaces delivered here.

**P9.01 semantic freeze (2026-10-22):** `COGNITION_INVENTION_CONTRACT.md` freezes process composition/inverse order, exact versus probe-relative equivalence, repair versus inverse, finite distribution support/unknown mass, invariant proof status, fresh verification and bounded budget identity. Acceptance names are explicitly pending P9.02–P9.04; no new invention capability is claimed by this spec.

**P22.E2 runner development (2026-10-23):** Added the four-split seed allocation to the frozen P22 runner, including concrete deterministic seeds, source/runtime provenance, checkpoint-manifest validation, analyzer-bound resource ceilings and ancestor roots, native `ProcessApply` scoring, and development checks for digest tampering, malformed permutations, lineage parent binding and repeatability. The runner and analyzer self-checks pass; allocation/runner tests pass. This remains development-only. P22.E2 cannot freeze or advance to held-out scoring: the candidate-specific simulated-adoption approvals and resulting multi-generation cross-family checkpoint manifest do not exist, and the development resource audit still records unmeasured dimensions and unmatched arm costs. No preregistration or held-out world was created or accessed.

**P22 native operation-cost attribution (2026-10-23):** Resource snapshots now classify digest-bound native term evaluations into disjoint retrieval, proposal, verification, model-refinement, definition-decode, and rollback rule classes using explicit rule-name mappings. The adapter reports each as measured native term-evaluation work only when per-rule identity coverage is complete; incomplete/missing capture remains unavailable. Approval events remain a partial count because human review time/cost is not measured. The focused P22 E2 bundle passes 54 tests, including a classification/source regression. This improves the development resource adapter but does not establish equal realized arm costs or make the E2 resource gate pass. No candidate adoption, checkpoint lineage, preregistration, or held-out run occurred.

**P22 operation-cost attribution audit (2026-10-23):** The category adapter was applied read-only to the existing D4 development artifact `p22_four_arm_native_rule_work_d4_304_305.json` (SHA-256 `6ef40d74f94ffd08e89c913b01a5e3f1a9c1aaef8a6941dd4c1ad5216c423776`). With complete native rule identity coverage, unchanged recorded 40/20/92/8 term evaluations for retrieval/proposal/verification/refinement; adaptive-only 140/64/112/28; invention-only 200/24,635/7,724/20; full 260/24,659/7,736/40. Definition decode and rollback are measured zero for these D4 development graphs. The raw artifact was not rewritten, and these selected development costs do not establish matched resources or efficacy. The focused E2 bundle passes 54 tests after adding the category and legacy-snapshot regressions.

**P22 passive control-lineage repair (2026-10-23):** Generation>0 checkpoints may now be digest-bound without approval/receipt when they represent passive unchanged/adaptive control state. `capture_passive_checkpoint` preserves the parent expression and parameters, binds the parent digest and cumulative resource snapshot, requires consecutive generations, and creates no candidate adoption or world-action receipt. The P22 manifest validator permits this form only for unchanged/adaptive-only arms and rejects changed expressions or adoption evidence there; invention/full arms still require exact approval and receipt evidence. The held-out runner's lineage control now checks all 24 root/generation parent links across families and arms; the development self-check passes a correct chain and rejects a tampered link. The focused P22 E2 bundle passes 55 tests. This closes a control-checkpoint representation gap only; approved invention lineages, preregistration and held-out evaluation remain open.

**P22 manifest-lineage validation refresh (2026-10-23):** Added an end-to-end schema fixture with eight digest-valid roots and 24 linked generations. The manifest loader accepts three-generation passive unchanged/adaptive control lineages and approved invention/full lineages; mutations that change a passive expression or remove required invention-arm approval/receipt evidence are rejected. The runner self-check covers the complete 24-link structural control and tampering. The updated P22 E2 bundle passes 56 tests. This is manifest and checkpoint-mechanism evidence only: no live candidate approval was consumed, no experimental checkpoint manifest or preregistration was created, and no held-out world was read.

**P22 passive-lineage resource guard (2026-10-23):** The passive checkpoint regression now carries native runtime counters and digest-bound per-rule work through a control generation, verifies their cumulative values in the snapshot, and rejects a child that regresses either runtime steps or term evaluations. The full focused P22 E2 bundle passes 56 tests. This verifies resource continuity for no-adoption controls; no candidate-specific invention approvals or experimental lineage were created.

**P22 held-out resource preflight guard (2026-10-23):** The runner now verifies the frozen wall-time record and every checkpoint resource value/source against the declared ceilings before constructing any held-out world. A regression supplies otherwise complete native checkpoint counters but retains partial approval-cost evidence; preflight rejects it before evaluation. The focused P22 E2 bundle passes 57 tests. Human approval effort remains unmeasured, so the current freeze cannot pass this guard; no held-out world was accessed.

**P22 exact simulated-adoption completion (2026-10-23):** After user approval of the two exact candidate bindings in `COGNITION_P22_V2_CANDIDATE_APPROVALS_20261023.md`, the native probe rebuilt each candidate in a fresh training-only graph and checked its full binding, distinct-goal witnesses, digest and epochs before creating approval. D4 `#752` and Loopover `#5761` each consumed one candidate-specific approval and completed exactly one guard-satisfied transition in the registered finite simulator, with a verified native receipt. Raw results are `p22_simulated_adoption_d4_200_202.json` and `p22_simulated_adoption_loopover_015_026.json`. This authorizes no other candidate or later generation, creates no held-out evidence, and establishes no efficacy. The guarded D4 adoption regression passes. P22.03 still requires approved multi-generation cross-family checkpoint lineages, complete cumulative resource controls and four-arm comparisons; P22.E2 remains blocked by unmeasured approval effort and unmatched resource vectors. No preregistration or held-out access occurred.

**P22 approval-effort instrumentation (2026-10-23):** The independent-improvement contract now defines `approval_cost` as reviewer self-reported seconds attached to each approval, with an explicit source. Native snapshots measure zero when no approval events exist, measure the sum only when every event has a valid self-report, and retain event counts as `PARTIAL_EVENT_COUNT` otherwise. The exact-adoption development path now requires this value before it creates an approval; prior approvals remain unmeasured and are not backfilled. Resource accounting and preflight regressions cover zero, complete, mixed and missing duration cases; the focused P22 mechanism/resource/checkpoint bundle passes 69 tests, and runner/analyzer self-checks pass. Two fresh distinct-goal training pairs (0400/0402) produced no qualified candidate in either family, with no approval, validation, or receipt; their raw hashes are in the P22 development report. This adds an honest prospective instrument but does not repair historical P22 candidate resource records, provide future approved lineages, or permit preregistration/held-out access.

**P22 prospective generation-one checkpoint capture (2026-10-23):** The candidate-specific training-only probe now records a generation-zero identity ancestor and, after one approved verified simulated action, a receipt-bound generation-one child. Both checkpoints persist digest-bound resource snapshots; reviewer-reported approval seconds enter the child snapshot, while the ancestor remains at zero. `NativeRuleWorkCapture.snapshot()` supports cumulative reads without ending the capture, and runtime wall time/RSS remain monotonic across descendants. A repeated-capture audit exposed that per-rule counters use store-namespaced audit IDs while the adapter joined them as local indices; new captures now use `p22_native_rule_work_v2`, preserving both values, while digest validation continues to accept historical v1. The two-store capture regression and generation-zero/generation-one checkpoint test require complete rule identity coverage. The combined resource, checkpoint, four-arm and synthetic adoption modules pass 33 tests. Existing raw artifacts were not rewritten, and E2 preflight continues to reject any genuinely partial resource capture. The 62-test mechanism/resource/checkpoint suite and P22 runner/analyzer self-checks passed before this capture fix; the updated 33-test suite passes after it. No new candidate action, held-out access, or preregistration occurred.

**P22 four-arm wall-time snapshot correction (2026-10-23):** The isolated development arm elapsed-time measurement is now included in the digest-bound resource snapshot runtime counters as well as the arm result, with coverage marked `MEASURED`. The shared-world four-arm D4 regression passes and checks exact agreement of both values. The measurement spans learner execution and candidate-validation scoring; it does not substitute for the separately frozen isolated-worker wall-time record required by E2.

**P22 wall-time resource matching correction (2026-10-23):** `compare_resource_snapshots` now compares `wall_time_seconds` whenever snapshots carry it, alongside steps, calls, validation work and RSS. The resource regression verifies unequal durations are reported as unmatched and rejects negative durations. Both affected resource-accounting and four-arm development test modules pass. This closes a comparator omission; it does not imply the four arms are resource matched or clear the E2 preflight.

**P22 fresh four-arm resource refresh (2026-10-23):** Using fresh training-only draws 0500–0503 in each family, all four arms completed on common worlds with native rule-work and arm wall time captured. Every arm solved 2/4 tasks in both D4 and Loopover; D4 invention-only/full proposed two/one candidates, while Loopover proposed none. Each run had empty validation allocation and zero approvals/receipts. All contract resource dimensions were measured, but realized vectors and wall time remain unmatched, so this is wiring/resource evidence only and supports no efficacy or efficiency claim. Artifacts and hashes are in the P22 report. The 16-test resource-accounting/four-arm suite passes; no held-out world or preregistration was accessed.

**P22 no-candidate resource-snapshot repair (2026-10-23):** A fresh distinct-goal Loopover training-only probe on draws 0504/0505 produced no first-task candidate after 5,000 attempts per request, with no validation, approval or receipt. Its unchanged raw artifact contains complete v2 native-rule-work counters at the probe level but omitted them from `resource_snapshot`, so the snapshot is explicitly incomplete for resource matching. The probe's non-adoption return path now binds captured native work and runtime counters into the resource snapshot, and approved checkpoint reconstruction rejects any validation allocation. Three focused regressions pass for snapshot binding, the training-only guard and generation-one checkpoint capture; the sequential rule-capture regression and P22 runner/analyzer self-checks also pass. The source artifact and its measured outcome remain preserved, not retroactively repaired. No held-out data was accessed.

**P22 provenance closure correction (2026-10-23):** The standalone P22 source bundle now includes the training proposal adapter and both development CLI entry points, which determine candidate reconstruction, resource capture and artifact output. A closure regression and direct provenance read confirm all three paths are hashed. At that point the runtime attestation was `DEVELOPMENT_ONLY` (`artifact_tree_dirty`); see the later clean-source attestation record below.

**P22 immutable native graph checkpoint completion (2026-10-23):** New generation-zero, passive and adopted checkpoints now include the canonical full `graph_to_dict()` snapshot, and its SHA-256 is bound into the immutable checkpoint digest alongside the resource snapshot. The digest verifier also confirms that the graph contains an active process schema or adopted candidate whose expression digest and parameters match the checkpoint. This preserves the learner's active native graph state for future generation continuation; the resource summary alone was insufficient for that purpose. `restore_native_checkpoint_graph` restores the snapshot into a normally booted native agent and requires an exact canonical round trip. P22 manifest loading rejects checkpoints without graph snapshots or an expression mismatch. The checkpoint, manifest and analyzer regression bundle passes 27 tests, and the standalone runner self-check passes. The checkpoint scoring adapter still evaluates only its declared finite process expression; this does not establish a full learner continuation, matched four-arm resources, live candidate approvals, preregistration, or held-out efficacy. No held-out data was accessed.

**P22 restored-generation development path (2026-10-23):** The training-only proposal probe can now restore an exact parent checkpoint, retain its native policies/domain/candidate evidence, and reject any reused training-world identity. Runtime counters continue cumulatively; native per-rule counters merge across graph-store instances using source-capture digests, preserving store and rule identities and rejecting double-counted captures. Historical v1 and current v2 rule-work snapshots are accepted as merge inputs; merged results use digest-bound v3. A fresh-checkpoint continuation regression verifies a second-store merge, cumulative task/resource records, and zero approvals or receipts; the existing exact candidate-bound approval/action/checkpoint path still passes. The focused continuation/resource/approval subset passes five tests. This enables a later authorized generation to extend its captured parent, but does not create authorization, demonstrate a continued-generation effect, complete matched four-arm learning, or authorize held-out access.

**P22 cumulative rule-work merger verification (2026-10-23):** The v3 verifier now checks capture/store identity declarations, unique rule rows, and that per-metric totals equal the retained rows; it rejects malformed or duplicate capture sources. The full P22 resource-accounting module plus parent-checkpoint continuation and exact candidate-action regressions passes 16 tests. `git diff --check` passes. These checks validate resource integrity across restored generations; they do not change the unmatched four-arm outcome or approval gate.

**P22 measured generation-zero root output (2026-10-23):** Training-only probes with native work capture now emit a digest-valid generation-zero checkpoint even before any candidate approval. A fresh Loopover v2 probe on distinct training draws 0510/0511 reached the 10,000-attempt ceiling on both tasks and produced one unapproved, unqualified candidate only on the second task. The root checkpoint includes the complete native graph, resource snapshot, and native-rule work; all resource dimensions are measured. It records 20,000 reserved attempts, 22 native rule steps, 101.925 s elapsed and 1,136,861,184 bytes peak process RSS. There are no validation worlds, approvals, or receipts. The raw artifact SHA-256 is `a22093e99013320e42fe50c27938121e3d22e8e5bcc931fbebcc9c914ecb510c`. This gives a current Loopover root but no adoptable generation-one child or efficacy evidence; P22.E2/E3 remain open.

**P22 repeated-draw root diagnostic (2026-10-23):** A follow-up training-only run on distinct draws 0511/0512 produced a generation-zero root and one candidate (`fb7e3d70756562027d9acb693ff8e97d4c7007eb25665e9eedc3504f21ef36f4`), with qualification count zero. Draw 0511 was already used by the preceding 0510/0511 diagnostic, so this is repeated development exposure and not an independent trial or eligible preregistration allocation. The artifact contains zero validation worlds, approvals, and receipts; its source hash is `235196b6f7b6c61bd37ed2a75b92d31b2c3a24dea7d48e287c3f79706c61c65f`. Four targeted regression groups (including the full resource-accounting module) pass, 17 tests total, and `git diff --check` passes. This adds no candidate authorization or held-out evidence; P22.E2/E3 remain gated by candidate-bound lineage authorization, matched arm resources, clean provenance and preregistration.

**P22.03 checkpoint execution and ablation (2026-10-23):** Strict checkpoint scoring now resolves process parameters from the immutable native graph (active ancestor ProcessSchema, approved adopted candidate, or passive ancestor control) and requires agreement with the compact manifest. A development-only native checkpoint ablation compares the captured ancestor with its exact approved child on a common training-derived control: the ancestor fails and the adopted expression succeeds. The P22.03 verification command passes 27 tests. This is bounded path-dependence evidence on one derived task, not an independent-goal effect; matched four-arm evaluation and P22.E2/E3 remain open.

**P22 implementation commit and loaded-native attestation (2026-10-23):** The accumulated P16–P22 implementation/evidence bundle was committed as `c94aa1c8649dedb4e13d84e85df38df3ca912e5f`. The release extension was rebuilt from that source using `scripts/engine_build.sh --lib-only`; `runtime_attestation.provenance` reports `ATTESTED`, with no issues, exact extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`, build-receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`, source-bundle SHA-256 `539131da9af055a94439aa17a4c6651fa3766707c74f775c13a4da32e1a760cd`, and deterministic allocation digest `ab8571b0d83c27b5704002910fd50dc7fa1022a3445287da6717f72ae28fc454`. Runner and analyzer self-checks pass without accessing held-out worlds. The 94-test affected Python bundle and the full `scripts/engine_cargo_test.sh -- --test-threads=1` suite pass (869 library tests; integration and doctest runs also pass, with two ignored doctests). This removes the source-cleanliness/provenance blocker. P22.E2 is still not admissible: approved multi-generation cross-family lineages, complete approval/resource measurements and the required frozen isolated wall-time records are still absent; no preregistration or held-out world was created or accessed.

**P22 restored Loopover generation-zero continuation (2026-10-23):** The digest-valid Loopover root from draws 0510/0511 was restored and continued on fresh, distinct-goal training draws 0513/0514. The continuation preserves the root digest and full native graph, merges digest-valid rule work, and records cumulative wall time 228.641 s, 39 native rule steps, 1,258,934,272-byte peak RSS, and 30,000 total reserved attempts. The parent's 20,000-attempt search had left only 10,000 under the inherited global ceiling, so the first new task consumed that remainder and the second received no attempts. One candidate remained unqualified (qualification count 0); approvals, receipts, validation worlds, and held-out worlds are all zero. The native graph, checkpoint, resource-snapshot, and rule-work digests verify. This is a useful continuation/accounting control but no generation-one child or efficacy evidence. The raw JSON SHA-256 is `b5016774abcb656ec80152862812a2480192318360a973eed5a0cfc6ea0e2471`; the retained deterministic gzip artifact SHA-256 is `60bf3c8022d446b9f7494b0d01e1a5c3e4bf8fcb189c8b6500192a5aa205de82`. A future continuation root must leave sufficient inherited search budget for both distinct training tasks; no ceiling is to be reset silently.

**P22 explicit cumulative search-cap continuation control (2026-10-23):** The training-only probe and CLI now accept a bounded explicit graph-wide cap (30,000 default; maximum 120,000), report the inherited and requested ceilings, and change only the policy limit after graph restore—the stored attempt counter is never reset. Repeating on fresh draws 0515/0516 with requested cap 100,000 and inherited cap 30,000 let both tasks receive their full 10,000 attempts. Cumulative attempts are 40,000 (20,000 root plus 20,000 new), wall time 335.909 s, 46 native rule steps, and peak RSS 1,419,657,216 bytes. The one retained candidate is still unqualified; approvals and receipts remain zero. The resource and merged native-rule-work digests verify. This isolates budget starvation from candidate qualification: a larger declared ceiling permits both trials but does not produce a qualified child. Raw JSON SHA-256: `cf3a092738de51da0b41822d3a86b124e7a10516b3da3e690e5544f66488b6bd`; retained deterministic gzip SHA-256: `bcda44aa9df03b6c36f6a54c24a3b56f6f265af62bd58c1a0548de8b5bddcab1`. This is another development-only negative result; no efficacy or held-out claim follows.

**P22.03 restored native learner task path (2026-10-23):** Added `score_restored_checkpoint_task`, which boots a fresh caller-selected native learner profile, restores the immutable checkpoint graph, adds a fresh training task in the checkpoint's native process domain, and lets native rules solve it. The result records task status, native rule steps/rounds, quiescence, and approval/receipt counts; it creates no action approval or simulator receipt. The checkpoint adapter, causal-ablation, and independent-improvement bundle passes 28 tests, including a regression where the restored native process solves a non-identity task through the native solver. This closes a graph-restoration execution primitive; it does not yet provide complete four-arm checkpoint continuation, matched cumulative resources, additional candidate approval, or efficacy evidence. No held-out allocation was accessed.

**P22.03 registered-world continuation guard (2026-10-23):** Tightened `score_restored_checkpoint_task` to accept only an exact answer-free view of a registered v2 training draw; validation, held-out, malformed, or mutated world views fail before learner boot. The restored domain now receives the training world's visible held-process schemas with digest and active-state conflict checks, and the runner adds the actual registered world ID as its training-trial identity. The regression runs a one-operator D4 training task through the restored native solver and rejects the same draw from the held-out split. The P22.03 28-test bundle plus runner/analyzer self-checks pass; both self-checks report PASS and no held-out access. This closes split provenance for this one-task native continuation primitive; it does not close four-arm checkpoint continuation, matching resource budgets, candidate-specific approvals, or efficacy.

**P22.03 common checkpoint panel (2026-10-23):** Restored task scoring now enforces a cumulative primitive-work ceiling through the native SolverPolicy max_steps field, captures per-rule native work plus runtime/resource snapshots, and reports budget exhaustion as a retained outcome. `compare_restored_checkpoint_panel` evaluates each named checkpoint on every common registered training world with a fresh learner and the same cumulative primitive ceiling. A secondary native rule-progress limit is reported separately because the scheduler can overshoot it within one run_rules call; it is not treated as the compute budget. Realized resource matching remains separately reported. A four-checkpoint D4 regression passes on a shared registered training world with zero new approvals/receipts. Its four checkpoint IDs intentionally refer to the same captured graph; this verifies panel plumbing only, not the four distinct learner conditions or efficacy. The P22.03 bundle passes 29 tests; this comparison helper does not clear P22.E2 resource/lineage gates.

**P22 compute-cap measurement correction (2026-10-23):** The native scheduler's `run_rules(max_steps)` return can exceed the requested progress count when one batch-safe rule commits multiple graph updates. The checkpoint panel now labels that value as a rule-progress limit, detects and retains any overrun, and does not treat it as a hard compute cap. The actual common primitive-work limit is applied to the native `SolverPolicy.max_steps` after subtracting each checkpoint's previously consumed cumulative primitive work; post-run graph accounting verifies the total remains within the declared ceiling. Fixed ceilings still do not imply equal realized resources, so comparisons remain marked non-efficient when runtime/resource vectors differ.

**P22.03 four-arm native checkpoint panel (2026-10-23):** The isolated development runner can now emit digest-valid generation-zero checkpoints for each explicit arm, with complete per-arm native rule-work, RSS, wall-time, search-reservation, and primitive-work source snapshots. On fresh D4 training draw 0520, all four actual policy graphs solved their common training task and produced root checkpoints with no approvals or receipts. The four arm graphs were restored independently and scored on the separate registered training draw 0521 under a shared cumulative primitive ceiling of 30,000. Each solved 1/1, reached cumulative primitive work 2, and added zero approvals/receipts. Digest-bound native term evaluations were 4,363 unchanged, 4,363 invention-only, 5,713 adaptive-only, and 5,709 full. Realized resources were not matched: the in-process comparison lacks isolated wall-time and RSS measurements, and other graph/resource vectors differ; efficiency is inadmissible. This is a selected, single-world training diagnostic, not a held-out or efficacy result. Draws 0520/0521 are consumed for development. The root artifact is [`p22_four_arm_checkpoint_roots_d4_0520.json`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_d4_0520.json), SHA-256 `bb88741136b5c2dc88daa33cdd0bbe6dbb94b261c45292b2cdef0b79c1661aee`; the cumulative evaluation is retained as deterministic gzip at [`p22_four_arm_checkpoint_eval_d4_0521_cumulative.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0521_cumulative.json.gz), decompressed JSON SHA-256 `42f54ebdff262d011fba04684c71cd067d7709d612bf82ec6e6338deb38260d8`, gzip SHA-256 `868dad46eb06d6e7c3665fbec61cd49558b0643b0de89909fc316874f7aba477`. A preliminary same-allocation result with increment-only rule counters is preserved separately and superseded by the cumulative artifact; it is not an independent rerun.

**P22.03 cross-family checkpoint panel refresh (2026-10-23):** The same isolated root-capture and registered-world continuation path now runs in both domains. On Loopover v2, four arm roots from training draw 0520 were scored on the common training draw 0521; all completed with zero solves and zero new approvals/receipts. Adaptive-only and unchanged each retained cumulative primitive work 2, while invention-only and full each used 130, all below the common 30,000 ceiling. Native term evaluations were 15,661 unchanged, 18,011 adaptive-only, 34,110 invention-only, and 36,537 full. The D4 counterpart solved 1/1 in each arm with cumulative work 2 and native term evaluations 4,363 unchanged, 4,363 invention-only, 5,713 adaptive-only, and 5,709 full. Both panels used the same registered training world within family and retain complete native-work digests; neither is resource matched, and the in-process evaluator lacks isolated wall-time/RSS. These two one-world training diagnostics show no four-arm efficacy and do not meet the complete resource-control gate. Draws 0520/0521 are consumed in both families. Loopover root artifact [`p22_four_arm_checkpoint_roots_loopover_0520.json`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_loopover_0520.json), SHA-256 `3cbcc409fb0572dc6cfb0cc3d013f0084c2ae21ab12e3705dca181bb9818e346`; cumulative evaluation gzip [`p22_four_arm_checkpoint_eval_loopover_0521_cumulative.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0521_cumulative.json.gz), decompressed SHA-256 `d24d98ba20ed7497cfb7c1f51e386851b53164f6985349e6d882efae68d1ad51`, gzip SHA-256 `b517c8ed698641017c2401ce17a7dc61244b1f43b1178247e9e2fd463cf742b5`.

**P22.03 isolated checkpoint resource-measurement refresh (2026-10-23):** Added `p22_checkpoint_panel` to the P22 provenance closure and used a separate worker process for every arm/world cell. It records isolated elapsed wall time and peak RSS, merges both with the checkpoint's cumulative counters, reseals each resource snapshot, and validates the registered training split before launching workers. For the D4 and Loopover panels above, all contract dimensions now have measured sources and all snapshot/work digests verify; both panels still report unmatched resources and inadmissible efficiency. Scores and primitive totals match the prior in-process outputs. D4 cumulative primitive work is 2 in all arms; Loopover remains 2/2/130/130 for unchanged/adaptive/invention/full. Isolated panel gzip hashes: D4 `11a838c6ca87d83b11808631c5510e38164597522f61d1a3bc8c968323ddbb6b`, decompressed JSON `264f379a6d5f63c2f8bfbd90f7ffed812a17451eabd762980d43837e81d9554e`; Loopover `4a83adddb30551a1664be1088e16d4690771414146f9d61397abf007698b7b0a`, decompressed JSON `844831e0c8c3d7c8c6b66d44e1959376be3d5e68ed9cdb6c4948fd0803bad27a`. Earlier same-allocation in-process panel artifacts remain preserved as preliminary records; isolated outputs supersede their incomplete wall-time/RSS measurements. This does not create approved descendant lineages or an efficacy result.

**P22.03 adaptive-path correction and curriculum-faithful isolated panel (2026-10-23):** A path audit found that the first checkpoint evaluator directly added `SolveTask` for every arm, bypassing the restored graph's `ProcessCurriculumPolicy`. Those prior isolated outputs and the preceding P22.03 score/work summaries are preserved as preliminary, but are superseded for outcome validity. The evaluator now submits common `ProcessCurriculumEvidence` to every arm and lets an enabled native curriculum policy construct and dispatch the task; only solver-isolation fixtures without that policy use the direct task path. A regression confirms that restored adaptive checkpoints take the native curriculum route. Fresh isolated panels use D4 and Loopover training draw 0521 with the generation-zero roots from 0520. D4 solved 1/1 in all four arms; Loopover solved 0/1 in all four. Cumulative primitive work was 2 in every D4 arm and 2/2/130/130 for Loopover (unchanged/adaptive/invention/full); native term evaluations were 4,379/7,696/4,379/7,688 for D4 (unchanged/adaptive/invention/full) and 15,677/21,121/34,158/39,537 for Loopover. All four arms in each panel received the same registered world, all contract dimensions were measured, budget and resource/work digests verify, and every arm added zero approvals and receipts. Realized resource vectors remain unmatched; `efficiency_comparable=false` and `efficacy_established=false`. These are selected single-world training diagnostics, not efficacy evidence. Draws 0520/0521 are consumed for development. Corrected isolated gzip artifacts: D4 [`p22_four_arm_checkpoint_eval_d4_0521_curriculum.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0521_curriculum.json.gz), gzip SHA-256 `42dc3df6336574ea202e52e8c69f9e40388b5cc950cead7fbcc9f46499922169`, decompressed JSON SHA-256 `9270ae98ed4ffccb72b84e0952c67190effba4ec92dd2230f1137edfc0fc47a5`; Loopover [`p22_four_arm_checkpoint_eval_loopover_0521_curriculum.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0521_curriculum.json.gz), gzip SHA-256 `970ed2f5bbcc3bb4ac840b20f88546a669187ff172a4bd820e74c796364b7735`, decompressed JSON SHA-256 `4ba264900870f3f904d8ac0aa845febb9ebf90c38ab0dbca0af0b300842277a3`. The corrected P22 bundle passes 42 tests; runner and analyzer self-checks pass without held-out access. Candidate-authorized multi-generation lineages, resource matching, efficacy, preregistration, and held-out evidence remain open.

**P22.03 expanded root-checkpoint development panel (2026-10-23):** The corrected isolated evaluator scored the same four generation-zero roots on 12 common registered training worlds per family, draws 0522–0533. Every world was retained for each arm, all contract dimensions were measured, native-work and resource digests verified, and primitive ceilings were respected. D4 scores were 4/12 in every arm; Loopover scores were 1/12 in every arm. Each panel added zero approvals and receipts. Realized cumulative primitive work differed between arms on some worlds (`same_cumulative_primitive_work=false`), and resource vectors were unmatched, so efficiency is inadmissible. The paired score differences are exactly flat across the four root arms on these selected development worlds; this does not estimate descendant improvement or efficacy. Development artifacts: D4 [`p22_four_arm_checkpoint_eval_d4_0522_0533.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0522_0533.json.gz), gzip SHA-256 `4036c49166109aec807fe882ae8d70c8e5556322359ee7e89fc1c50c1bd0f791`, decompressed JSON SHA-256 `b101fde7e83770240ae99135c32d7bdd593004a6749e535d8ffc56875fc3b513`; Loopover [`p22_four_arm_checkpoint_eval_loopover_0522_0533.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0522_0533.json.gz), gzip SHA-256 `ee1f133714b39c64bf931c039fee883561eb4cfee2ab4fc36b2f22c657cac734`, decompressed JSON SHA-256 `6b271e22c64351cd9ff0dc25060660a106bd819e96606a999a9d2d0df85fd619`. Draws 0522–0533 are consumed for development. No validation or held-out world was accessed.

**P22.03 resource-mismatch diagnosis (2026-10-23):** The complete snapshots localize the remaining mismatch to realized treatment work, rather than missing instrumentation: every row has zero measurement gaps and no unavailable dimensions. Across the 12 D4 worlds, median cumulative native term evaluations by arm were 4,280 unchanged, 7,684 adaptive-only, 37,546 invention-only, and 41,023 full; median cumulative primitive work was 2, 2, 198, and 198 respectively. Loopover medians were 23,015, 28,637, 41,516, and 47,069 term evaluations, with primitive work 3, 3, 131, and 131. D4 median captured cumulative wall time ranged from 0.3415–0.3870 s; peak RSS from 88.445–95.289 MiB. Loopover wall time ranged 0.3640–0.3848 s and peak RSS 88.602–95.820 MiB. The common ceilings are respected, but unequal realized work and graph states make resource matching and efficiency claims inadmissible. Do not pad work or alter arm ceilings post hoc to manufacture a match; any new equal-cost protocol must be frozen before another allocation.

**P22.03 native held-out runner path repair (2026-10-23):** Code review found that linear_p22_v1.run_heldout still used the expression-only CheckpointWorldAdapter, despite P22.03 requiring actual restored learner checkpoints. It now scores each arm/generation/world in a fresh worker that restores the digest-bound native graph and runs the common native solver against an externally assigned answer-free task. The held-out task is marked evaluation_only and excluded from training-evidence/task exposure bytes and counts; native search and solve work remain measured. The held-out runner first verifies the committed standalone freeze, which must declare bounded cumulative primitive and native rule-progress ceilings before the runner constructs its world allocation. The analyzer requires a native learner/task outcome, respected ceilings, zero new approvals and zero world receipts; worker exceptions remain rows and fail closed. A synthetic split fixture confirms the native task path and training-exposure exclusion without reading a registered held-out draw. The focused P22 suite passes 50 tests, runner/analyzer self-checks pass, and no registered P22 held-out world was accessed. Commit 91fb8bdffcac1ec7f82947d4a48a03061ce80315 has native runtime status ATTESTED, no issues, loaded extension SHA-256 5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07, build receipt SHA-256 661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66, and P22 source-bundle SHA-256 480b9493a7e99cfb9bde6ba1c983d3dccddee1122842d6b6849dffc55c1d408d. This repairs the runner-to-P22.03 consumer mismatch; it does not create approved lineages, freeze a preregistration, or establish efficacy.

**P22 isolated wall-time scope correction (2026-10-23):** A worker audit found that the previous panel timer started after learner boot, while the intended per-cell wall time includes fresh learner boot, graph restoration, and scoring. The worker timer now starts before learner boot. The earlier isolated artifacts retain valid outcomes and RSS/resource digests, but their isolated worker wall-time values omit learner boot and are superseded for that measurement only. A timing regression injects a controlled boot delay and confirms it enters the digest-bound wall-time counter. Fresh training draws 0546–0549 were scored with the corrected scope: all arms solved 1/4 worlds in both families, all 32 cells had valid resource/work digests and respected the primitive ceiling, and every arm added zero approvals/receipts. Resource vectors remain unmatched. D4 median worker wall times (boot through scoring, Python import/startup excluded) were 0.3305/0.3523/0.3517/0.3680 seconds and median peak RSS 74.93/74.86/77.85/77.59 MiB (unchanged/adaptive/invention/full). Loopover medians were 0.3404/0.3478/0.3545/0.3549 seconds and 75.11/75.80/78.14/78.45 MiB. Artifacts: [p22_four_arm_checkpoint_eval_d4_0546_0549_bootincluded.json.gz](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0546_0549_bootincluded.json.gz), gzip SHA-256 a575ca7a283957f6b56cae64dd456eb166279061930ad2ce0bd2bd1e3609620e, decompressed JSON SHA-256 eec6eae4af6188827d7f96239bce114827b4585674033622367cc524ddc943b5; Loopover [p22_four_arm_checkpoint_eval_loopover_0546_0549_bootincluded.json.gz](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0546_0549_bootincluded.json.gz), gzip SHA-256 a3a8c98c8cd7089b1ebfbfadcd9e92524e2d9baaff79235a9ec88a8bb10ec5f8, decompressed JSON SHA-256 ee9292e0e8d47038cc2da7198f42daf4c5a09eb24b58fda9100f4cf259363bbb. The focused P22 suite passes 51 tests and runner/analyzer self-checks pass. Timer correction commit 68980afbc394de545a0ad11af239ed4cdb01b085 retains runtime attestation ATTESTED with no issues, source-bundle SHA-256 f53e89d817e4e64319fbc6b85b73ccc598d80120f9050be8473571179eaacceb, loaded extension SHA-256 5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07 and build receipt SHA-256 661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66. Draws 0546–0549 are consumed for development only; no validation or held-out worlds were accessed.

**P22 held-out freeze-order regression (2026-10-23):** Added a runner test that forces standalone freeze verification to fail and makes both registered held-out world generators fail if called. `run_heldout` raises from freeze verification first, establishing that allocation is not reached on an uncommitted or invalid freeze. The focused P22 bundle passes 52 tests; runner and analyzer self-checks pass, with `heldout_accessed=false`. Commit `e2c9463b` contains the regression. No registered held-out allocation was accessed; candidate-authorized lineages, resource matching, preregistration and held-out results remain open.

**P22 candidate approval-path audit (2026-10-23):** Re-ran `tests/test_p22_development.py` and `tests/test_p22_resource_accounting.py` on the current checkout; 24 tests pass, including the synthetic candidate-bound D4 approval, one guarded simulator transition, verified receipt, reviewer-time accounting, and parent-linked generation-one checkpoint capture. This verifies the mechanism with test-fixture authorization only. The live D4 request remains pending its exact digest approval and numeric reviewer-reported `review_seconds`; no live action was created.

**P22 freeze-order guard strengthening (2026-10-23):** Extended the regression to make both learner construction (`Agent`) and both held-out world generators fail if reached. A forced freeze-verification rejection still occurs first; the focused regression passes. This proves the runner does not boot a learner or access held-out worlds before verifying the standalone freeze.

**P22 matched-resource claim gate (2026-10-23):** Analyzer review found that the frozen score thresholds could produce phase `PASS` even when paired arms had unequal measured work, contrary to the contract's capability-only boundary. The analyzer now reports score-threshold and resource-match results separately and marks the registered phase pass only when every scored arm/world comparison matches every `MATCHED_RESOURCE_FIELDS` dimension; wall time remains separately reported as an outcome. A held-out synthetic control with passing score thresholds and one resource mismatch is classified `NOT_ESTABLISHED` / `CAPABILITY_ONLY`. The focused P22 bundle passes 53 tests and both runner/analyzer self-checks pass. No registered held-out allocation was accessed. Commit `bb5f4b67` contains the correction; lineage authorization, matched panels, preregistration and held-out results remain open.

**P22 analyzer provenance after claim-gate correction (2026-10-23):** Current provenance reports native runtime `ATTESTED` with no issues; analyzer SHA-256 `dd737d2bbf2561b2d3279e205ad64c11c809d3c6e227b3b0345fe0bf64cf26af`, source-bundle SHA-256 `da5c6f151af018bd277020e39c9a341eb8ff999ff6617335975f1c71017759bd`, loaded extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`, and build receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`. These fingerprints must be used in any future standalone freeze; the prior generation-zero development artifacts are unchanged.

**P22 approval execution path (2026-10-23):** Added a machine-readable binding for the pending D4 0406/0407 request and wired `run_p22_development_probe.py` to consume it only with the exact approved expression digest, reviewer-reported seconds, training-only distinct-goal settings, an explicit `--execute-approved-adoption` flag, and the request-bound output path. Missing authorization fields, changed digests, and non-training settings fail before the proposal probe. CLI guard tests pass (2); no adoption command was run. The pending request remains awaiting exact user approval and review duration.

**P22 guarded approval CLI provenance (2026-10-23):** After committing the structured request and CLI, native runtime provenance remains `ATTESTED` with no issues. Runner SHA-256 is `6b5766a5468decc36eb075e824d52d69834b8f2709a2544a197aee14bc086d52`; current source-bundle SHA-256 is `0826ac11b7415762a2246c83a1ad865c3ea594621803f9946787fb4aa4c0ffca`. Loaded extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07` and build receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66` remain unchanged. No action was executed.

**P22 historical adoption versus checkpoint audit (2026-10-23):** Inspected the raw D4 `#752` and Loopover `#5761` simulated-adoption artifacts cited in the cross-goal record. Each preserves one consumed approval and verified receipt, but neither contains a generation-one checkpoint snapshot; these historical actions cannot populate the current lineage manifest or authorize replay. The pending D4 `#1089` request is a separate, single-action request that conditionally captures one D4 generation-one checkpoint. Even if authorized, it does not establish Loopover checkpoint coverage or later generations. No historical action was replayed, no approval was reused, and no held-out allocation was accessed.

**P22 retained-checkpoint inventory (2026-10-23):** Audited every `evaluation/process_mastery/results/p22*` JSON and gzip JSON artifact recursively for nonroot checkpoint records or `generation_one_checkpoint`/`child_checkpoint` payloads. None contains a generation>0 checkpoint snapshot; the only checkpoint artifacts are generation-zero roots and their scoring reports. The prior D4/Loopover adoption receipts therefore cannot be upgraded into native checkpoint lineage after the fact. No sealed allocation was read or modified.

**P22 approval request hash binding correction (2026-10-23):** The CLI now parses and hashes the same raw binding bytes, eliminating a read/parse versus hash discrepancy. Its two negative guard tests still pass. The runner remains unchanged; after this CLI correction the source-bundle SHA-256 is `8aafcbf1e7e2f16f1b11287b2fbd54d7b75d9fd12fca64bdc04cbf3020429c6f`; runtime attestation remains `ATTESTED` with no issues. No action was executed.

**P22 one-shot approval attempt guard (2026-10-23):** The guarded CLI now durably creates its request-bound output marker with exclusive creation and `fsync` before running proposal or action work. A completed action replaces the marker with its result; a crash or exception leaves the marker, blocking retries under the one-action request. The three CLI tests pass, including duplicate-claim rejection. Runtime provenance remains `ATTESTED` with no issues; current source-bundle SHA-256 is `080c96bfb05da93064ab8d5d88d36464be8fac8c8dcb64fc39f6607802a463f2`. No adoption was executed.

**P22 integrated regression refresh (2026-10-23):** The checkpoint adapters, four-arm development panel, isolated checkpoint panel, causal-ablation and independent-improvement modules, linear runner/analyzer, and approval CLI pass together: 56 tests. Runner self-check passes with `heldout_accessed=false`; analyzer self-check passes. Native runtime remains `ATTESTED` with no issues and source-bundle SHA-256 `080c96bfb05da93064ab8d5d88d36464be8fac8c8dcb64fc39f6607802a463f2`. No registered held-out allocation or candidate action was accessed.

**P22 D4 candidate-specific adoption and generation-one capture (2026-10-23):** After explicit approval of expression digest `badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255` and reviewer self-reported review time of 12 seconds, the one-shot CLI reconstructed D4 candidate `#1089` from distinct training draws 0406/0407 and checked its binding before creating approval. It consumed one human approval (`#6708`), executed exactly one guarded simulator transition on `p22:d4-v2:train:0406`, and verified receipt `#6710` for resulting state `[2,0,3,1]`. It captured generation-one checkpoint `p22-d4-g1-badd1251ee4e` (digest `f3d6c15ac7f9187cef0e4c7ca21f3615958955565101a891fbc8796c997e6ed6`) linked to generation-zero ancestor `e80842b7932ce9bbcc326254c6844caf64ec6fc0ac8600d62f89d5f088ca52cf`. Both immutable checkpoint digests and the consecutive parent link verify; cumulative primitive work is 47,677 including the one transition. Validation allocation is empty. The raw artifact [`p22_approved_candidate_d4_0406_0407.json`](../../../evaluation/process_mastery/results/p22_approved_candidate_d4_0406_0407.json) has SHA-256 `7435894f1b65c8c62d0d7b401f0db73f1513372ee24f66dd2c01b552aafcab9b` and remains outside version control. The prior CLI rejection tests assumed this fixed one-shot path was unclaimed; they now use temporary request bindings and outputs. The first integrated rerun exposed two stale path assumptions; after that test-fixture correction, the complete affected P22 bundle passes 97 tests in 286.89 seconds. Runner and analyzer self-checks pass, with `heldout_accessed=false`. This single D4 generation does not satisfy the required cross-family multi-generation lineage; the request grants no later adoption, Loopover adoption, preregistration, or held-out access. Resource-matched arms, standalone freeze requirements, and efficacy remain open.

**P22 fresh candidate continuation results (2026-10-23):** Four Loopover-only training probes on draws 0550–0557 included one restored generation-zero continuation. The 0550/0551 pair produced no candidate; 0552/0553 and 0554/0555 produced candidates that did not qualify; and the 0552/0553 candidate remained unqualified on new distinct goals 0556/0557. All had empty validation allocations and no approvals or receipts. The source records and hashes are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). A separate restored D4 generation-one continuation on distinct training draws 0560/0561 completed without a qualified generation-two candidate or a new action; its one approval/receipt count is inherited from the parent, and no generation-two checkpoint was created. Its raw hash is `504e01786e2f141eede6f0d664cf39c87c33e44132ef5daf69d52b9c2ccf1158`. These outcomes leave Loopover generation one and D4 generation two unavailable for the registered lineage; candidate-specific approval, resource matching, standalone preregistration, and held-out evaluation remain open.

**P22 qualified D4 generation-two candidate (2026-10-23):** Continuation from the approved D4 generation-one checkpoint on new distinct training draws 0562/0563 produced candidate `#6731`, digest `1e3590935d290140171bd81f966a1dcc336e72278231d844b6411f7a2286f9b4`, with two native qualification witnesses. Its measured effect is the identity permutation, so it is explicitly classified as non-improving. No approval or generation-two checkpoint has been created. [`COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.md`](COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.md) documents the exact candidate and its single-action scope; approval would authorize only one identity-effect transition and conditional child checkpoint. The guarded CLI now supports an artifact-hash-bound restored parent, verifies the parent checkpoint and graph, and binds the search ceilings before its one-shot claim. Its negative-digest preflight rejects before creating the output. Loopover continuations on draws 0564/0565 and fresh training draws 0566/0567 also remain unqualified; their raw evidence is documented in the P22 development report. These results do not close cross-family lineages, matched resources, preregistration, or efficacy.

**P22 D4 identity action and generation-two capture (2026-10-23):** The user approved candidate `#6731` by its exact digest and reported 12 review seconds. The bound one-shot CLI verified its request and generation-one parent, consumed approval `#16727`, executed exactly one transition on training draw 0562, and verified receipt `#16730`. The effect is identity and the observed state stayed `[0,1,2,3]`; it is not evidence of improvement. The child checkpoint `p22-d4-g2-1e3590935d29` has digest `5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc`, generation 2, parent digest `f3d6c15ac7f9187cef0e4c7ca21f3615958955565101a891fbc8796c997e6ed6`, and cumulative primitive work 107,073. Raw artifact SHA-256 is `8c6e6392c47a7f9fb8f212df0bc747df3a88a02fc8d190358e0841082d41bd25`; it remains outside version control. No validation or held-out world was accessed, and no later action is authorized by this approval. Current P22 provenance at commit `b5a8c4467bcc7058abb127dee5b0742ae0458d36` remains native-runtime `ATTESTED` with no issues: runner SHA-256 `6b5766a5468decc36eb075e824d52d69834b8f2709a2544a197aee14bc086d52`, analyzer SHA-256 `dd737d2bbf2561b2d3279e205ad64c11c809d3c6e227b3b0345fe0bf64cf26af`, source-bundle SHA-256 `f9bf4c6fa51a771969ee93bf978b4873b40b326c575ae077c08c1e0b233c36de`, loaded extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`, and build receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`. Cross-family three-generation lineages, a resource-matched panel, standalone preregistration, and held-out efficacy remain unestablished.

**P22 D4 generation-two continuation (2026-10-23):** A proposed continuation pair 0570/0571 was rejected before learner boot because both training draws generated the same goal; the preflight record is preserved (SHA-256 `54d73db5463edca2133111a5b4f367a1299c1b1cb79b087d42d37684329d47ac`) and those draws are consumed. Restoring the verified generation-two checkpoint on distinct draws 0572/0573 with a 120,000 cumulative attempt ceiling and 10,000 per-request ceiling produced three candidate records but no candidate qualified on either new goal; both tasks ended stuck after 5,000 attempts each. Approval/receipt counts are inherited (two each), with no new approval, action, or receipt. There were no validation or held-out worlds. Raw artifact SHA-256 is `e8cf05934a774824fbfbcce73d246b285717a155235a291f08beec74f6efe018`. This pair does not extend the lineage to generation three; the complete report is in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). A fresh higher-ceiling D4 continuation on draws 0574/0575 is now running from the same parent; the Loopover 0568/0569 probe remains in progress. Both are training-only and create no approval authority.

**P22 restored search-ceiling correction (2026-10-23):** The completed D4 continuations on draws 0572/0573 and 0574/0575 both retained the parent checkpoint's 5,000 per-request cap after restoration, despite request ceilings of 10,000 and 20,000 respectively. Both are preserved as ceiling-censored diagnostics and neither produced a qualified candidate. Fixed `run_p22_training_proposal_probe` to apply the bound per-request ceiling after graph restoration and to report each request's actual ceiling. The new regression uses a parent cap of 1 and continuation cap of 2, and verifies that the fresh requests carry 2; it passes. A rerun on fresh draws 0576/0577 is in progress, and is not a replay of the censored attempts. The D4 0574/0575 raw artifact hash is `69cbf546dfd86f6783200b782519e0d981f3d1c7ffb5463026ca31d0cd4e82a7`; see the P22 development report for both raw records and limitations.

**P22 high-ceiling Loopover search result (2026-10-23):** The long-running fresh Loopover probe on distinct training draws 0568/0569 completed. At the configured 30,000 per-request and 90,000 global ceilings, both tasks ended stuck after 30,000 attempts. One candidate (`#30830`, digest `20db63f2bf032030ffc2293e3361aeb58d4b7a9e3d887f4b34429054ba475da8`) had zero independent-goal witnesses; the runner classified the pair `NO_CANDIDATE_FIRST_TRIAL`. No approval, receipt, validation or held-out access occurred. Raw artifact SHA-256 is `f7a3312131002cd7dead4b469fb56e5f68a2887361e7709ebe2346a8ec968fd1`. This does not provide a qualified Loopover generation-one candidate. Draws 0568/0569 are consumed; the D4 0576/0577 continuation is separately running with the corrected restored per-request ceiling.

**P22 restored-ceiling regression and current provenance (2026-10-23):** The complete `tests/test_p22_development.py` module passes (10 tests). The P22 runner self-check passes with `heldout_accessed=false`; lineage tamper fixtures are rejected. The analyzer self-check passes its nine cases covering missing/partial/mismatched sources and positive controls. At commit `68ecf662cd5f7c26badb93ebbe9cdba8d0dba1db`, runtime attestation remains `ATTESTED` with no issues; runner SHA-256 `6b5766a5468decc36eb075e824d52d69834b8f2709a2544a197aee14bc086d52`, analyzer SHA-256 `dd737d2bbf2561b2d3279e205ad64c11c809d3c6e227b3b0345fe0bf64cf26af`, source-bundle SHA-256 `e4964b4552ac17e0e1cca0301d0c1ee9be951981ff971bfc4ed50538a726ef73`, loaded extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`, and build receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`. The D4 0576/0577 corrected-ceiling continuation is still running; this provenance must be refreshed again if any source or integration changes before a future freeze.
