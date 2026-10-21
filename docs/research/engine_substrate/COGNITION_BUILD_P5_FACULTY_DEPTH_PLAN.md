# Cognition build Phase 5 — Depth in existing faculties

**Detailed on:** 2026-10-21. **Status:** Phase 5 implementation and reporting cycle complete. The original v1 harness run remains NOT_ESTABLISHED; the separately frozen v2 adapter-backed draw passes all eight registered mechanism-fixture criteria. H4 records the evidence limits and remaining follow-up work; no general capability claim is made.
**Parent:** [Cognition build plan](COGNITION_BUILD_PLAN_20261010.md). **Entry:** P4 implementation/invariant gate and item results; [P3 results](COGNITION_BUILD_P3_RESULTS.md) remain the latest completed phase.

## Scope and sequencing

F1 shares typed attributed-state views across existing ToM systems. `domains/tom_meta_shape.py` and `tests/test_tom_meta_shape.py` already demonstrate a shared meta-shape; `TOM_SYSTEM_UNIFICATION_RESULTS.md` describes earlier scope, not the final current state. Preserve distinct domain belief stores and the retired Python psychology functions. F2 adds true nested attribution in rules; it does not infer that first-order belief worlds already imply recursion.

E4 owns the deferred P1 `ImaginedCandidate` consumer and explicit dual-process candidate re-opening. A separate A2 task owns completion of decomposed axes; `child_mean_saturation` remains diagnostic until the completion contract is satisfied. Reappraisal changes appraisal interpretation while keeping observed events immutable. Response inhibition operates before irreversible emission; an already executed action cannot be withheld retroactively.

After H0: `F1 → F2`; `E3` supplies optional causal models to `E4`, while `G3` must pass before E4's action arbitration integration. `G2`, `D6` and `A2` can be implemented independently using the P4 contracts. Every item has a spec and acceptance task before behavior implementation. After focused item tests, H3 integrates the guarded profile, H1 freezes all artifacts, H2 runs the held-out evaluation, then H4 closes the documentation. There is no dependency from the core planner to Track I invention: missing tools yield an explicit request/impasse; Track I I5 may consume it later.

## Execution contract

This document details the parent plan's §3 task contract. Tasks below are **planned**, including named acceptance tests; none is claimed implemented or passing by this document. Read references use `path:line` or `path::symbol`; symbol anchors are authoritative when lines move. New files are explicitly marked. Generator plus generated seed count as one touch point. Each task changes at most three touch points. Read this contract with each task; the per-task fields give its specific scope.

- The agent's decisions and state live in seed rules and Rust. Python evaluation code may generate worlds, ingest events, tick to a declared limit, collect outputs and compute offline statistics. It must not select the agent's next action, perform recall, infer schemas or decide adoption.
- Declare Γ productions for every new edge, test dependency-closure boot without permissive test grammars, and record provenance on inferred, imagined and observed objects. New runtime seeds are self-load-only and disabled by default. Add them only to the cognition-on profile at the final integration task; default and conversation boots remain isolated.
- Before Rust edits, inspect `git status --short runners/dsl runners/wasm`. The 2026-10-21 checkout has concurrent uncommitted engine and Track I work. Use a clean worktree for engine implementation; never stage or regenerate over another author's changes. Read and apply `CLAUDE.md` and parent §1. No staging or commits are part of this planning update.
- Reuse existing Terms first. Where a task specifies a new Term, its schema, error behavior, graph ownership, invalidation, serialization and cost bound must be frozen before implementation. Use the Rust integration tasks below; never hide changes to additional Rust files in a seed task.
- A declared budget limits computation, not evidence standards. Each funded operation has one request, one approval and at most one debit, including retry and restart. Terminal paths restore temporary policy state. Commit confidence, conflict margins and safety vetoes cannot be relaxed to produce a success.
- Tests are written before behavior changes where possible. Every task is done only after its named acceptance and the phase regression gate show no new failures. A timeout or skip is NOT_ESTABLISHED. Preserve P3's NOT_ESTABLISHED classification for `test_capability_control_fabric_migrated.py` until it is actually resolved; do not describe the inherited gate as fully green.

### Commands for implementation, not commands executed by this plan

Every `Verify cmd` below is prefixed by `OZMA_SEED_PERSIST_DISABLED=1`; use the repository `.venv/bin/python`. Run the focused tests for each task, then the phase gate at integration and after engine changes:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/failure_baseline.py verify --list results/cognition_gate_baseline.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/failure_baseline_sweep.py --files-from scripts/cognition_gate_suite.txt --workers 4 --timeout 420 --out /tmp/cognition-PHASE-gate.json
```

Replace `PHASE` with this phase number. Also retain P0–P3 acceptance tests, including `tests/test_extended_thinking_migrated.py`, `tests/test_inference_ladder_record_migrated.py` and `tests/test_cognition_profile_integration.py`. Before an engine build run `df -h /`; build only via `scripts/engine_build.sh`, run `scripts/engine_cargo_test.sh --lib -- --test-threads=4`, and run `tests/test_engine_provenance_migrated.py` with the built artifact. Compare known failures with `COGNITION_BUILD_P2_RESULTS.md`; changes to a baseline require a separate explained decision, never automatic acceptance. Record runtime, engine provenance, head commit, seed hashes and boot node/rule counts in results.

### Evaluation contract

Each phase has one preregistration document with a separate subsection per work item. Spec tasks fill and freeze those subsections; commit the complete preregistration alone **after** implementation and runner freeze, **before** any held-out draw. A spec task can use development fixtures only. The preregistration commit hash seeds a reproducible held-out split, disjoint from development and previous phases. Freeze runner, instance generators, analysis, engine and seeds. Draw index `i` uses `int(hash[:8],16) + 7919*i`; family and arm salts are declared in the preregistration. Use identical instances, training exposure and budgets across paired arms. Independent agents prevent cross-arm cache contamination. Repeat experiments explicitly retain the same agent within an arm.

Report every registered metric, null, timeout and exclusion. For binary outcomes report paired differences, Wilson 95% intervals and exact McNemar tests; for work/latency report paired distributions and a prespecified paired bootstrap interval (10,000 resamples). Use Holm correction over each phase's primary superiority tests at family-wise α=.01. Zero-tolerance invariants fail on any violation. Fixed draws end without optional stopping. Report accuracy beside work saved, graph growth and budget spend. Wall time is secondary to deterministic work counters. Thresholds below are proposed decision criteria to freeze before draws, not observed results. Changing one after draws requires a new version and untouched holdout.

Before freezing artifacts, run `scripts/lint_orphan_signals.py` and `scripts/report_seed_boot_status.py`; each new runtime seed must be SLO with its dependency closure tested. A write-only signal needs a consumer or an explicitly justified provenance-only allowlist entry. If an allowlist change is necessary, record a separate ≤3-file task before editing it; never suppress an unresolved decision signal merely to clear the lint.

A phase can finish implementation with a negative capability result, provided every item is evaluated and limitations are recorded. Integration requires mechanism and invariant tests to pass with no new regressions. Downstream work requiring a failed capability must supply its own fixture-backed fallback or remain explicitly blocked. A result document never silently promotes a failed hypothesis to a pass. Human-level and beyond-human claims remain governed by Track I and require its human baselines.

### P5.H0 — Reconcile Phase 4 results and freeze Phase 5 interfaces

- **ID:** P5.H0
- **Tier:** T1
- **Goal:** Reconcile Phase 4 results and freeze Phase 5 interfaces.
- **Read first:** `COGNITION_BUILD_P4_RESULTS.md` (created by P4); `COGNITION_BUILD_P1_RESULTS.md:26-40`; `domains/tom_meta_shape.py:1-70`; `COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md:115-130`.
- **Touch:** this plan; new `COGNITION_BUILD_P5_PREREG.md`.
- **Pattern to copy:** P3 explicit deferral ledger.
- **Steps:** 1. Record which P4 capabilities are supported, failed or unavailable. 2. Freeze fallback local verification when transfer is unavailable and list native migration boundaries. 3. Assign every P1/P3 carryover to E4 or A2 below.
- **Guard:** documentation only.
- **Acceptance:** no dependent task assumes failed P4 evidence; all seven P5 work items and both carryovers are scheduled.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** inferring readiness from untracked Track I files.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task. Verified: 9 executable contract tests pass; runtime implementation is P5.A2.2.

### P5.F1.1 — Specify a shared attributed-state view across ToM systems

- **ID:** P5.F1.1
- **Tier:** T1
- **Goal:** Specify a shared attributed-state view across ToM systems.
- **Read first:** `domains/tom_meta_shape.py:31-70`; `tests/test_tom_meta_shape.py:40-108`; `docs/research/engine_substrate/TOM_SYSTEM_UNIFICATION_RESULTS.md:1-100`; `domains/character_tom.py:340-396`; `seeds/interlocutor_shapes.json`.
- **Touch:** `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_tom_unified_view_migrated.py`.
- **Pattern to copy:** existing attributed_mental_state_signature and shared-meta-shape convergence.
- **Steps:** 1. Map character beliefs, psychology vocabulary, interlocutor estimates and resident agency attribution to holder/target/content/modality/source/epoch. 2. Distinguish own affect, attributed affect and asserted world truth. 3. Write parity, contradiction and separate-owner fixtures.
- **Guard:** planned `TomViewPolicy.enabled=0`.
- **Acceptance:** planned `test_four_sources_project_without_merge`, `test_own_affect_is_not_other_belief`, `test_contradictions_preserved`, `test_source_epoch_refresh`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_tom_unified_view_migrated.py tests/test_tom_meta_shape.py -q -p no:cacheprovider`.
- **Non-goals:** resurrecting retired psychology.py functions; structurally merging unrelated domain corpora.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.F1.2 — Wire native attributed-state projections

- **ID:** P5.F1.2
- **Tier:** T2
- **Goal:** Wire native attributed-state projections.
- **Read first:** `tests/test_tom_unified_view_migrated.py`; `domains/tom_meta_shape.py:31-70`; `scripts/gen_cognition_signature_seed.py` (P4); `seeds/psychology.json`.
- **Touch:** `scripts/gen_tom_unified_view_seed.py`; `seeds/tom_unified_view.json`; `domains/tom_meta_shape.py`; `domains/character_tom.py`; `domains/interlocutor_model.py`; `substrate/world_adapter.py`; `domains/bigville_theory_of_mind.py`; `tests/test_tom_unified_view_migrated.py`.
- **Pattern to copy:** P4 source-descriptor epoch invalidation and existing ToM relation signatures.
- **Steps:** 1. Create graph projections with domain-specific source references. 2. Recognize through the shared meta-shape without replacing original stores. 3. Register Γ edges and verify minimal dependency boot; adapters only translate fields.
- **Guard:** `TomViewPolicy.enabled`, default 0.
- **Acceptance:** F1.1 tests plus `test_dependency_boot`, `test_no_cross_owner_recall`, `test_generator_reproduction`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_tom_unified_view_migrated.py tests/test_tom_meta_shape.py tests/test_character_tom.py -q -p no:cacheprovider`.
- **Non-goals:** adding a single truth field for incompatible beliefs; new Python ToM inference.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.F2.1 — Specify scoped recursive belief updates and queries

- **ID:** P5.F2.1
- **Tier:** T1
- **Goal:** Specify scoped recursive belief updates and queries.
- **Read first:** `domains/character_tom.py:340-396`; `tests/test_character_tom.py:68-101`; `tests/test_tom_unified_view_migrated.py`; `COGNITION_BUILD_P5_PREREG.md`.
- **Touch:** `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_recursive_tom_migrated.py`.
- **Pattern to copy:** character_tom nested entities and first-order Sally-Anne isolation.
- **Steps:** 1. Freeze identity by complete holder path, referent and world version. 2. Specify observation/access events, mistaken beliefs, depth bound 2 initially, cycles and unknown answers. 3. Write second-order true/false belief minimal pairs, swapped names and update-access controls.
- **Guard:** planned `RecursiveTomPolicy.enabled=0`.
- **Acceptance:** planned `test_second_order_false_belief`, `test_actual_world_not_overwritten`, `test_no_access_no_belief_update`, `test_cycles_and_depth_bound`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_recursive_tom_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** an unbounded nesting claim; lexical answer templates keyed to test names.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.F2.2 — Implement recursive belief-world reasoning in rules

- **ID:** P5.F2.2
- **Tier:** T2
- **Goal:** Implement recursive belief-world reasoning in rules.
- **Read first:** `tests/test_recursive_tom_migrated.py`; `domains/character_tom.py::_nested_entity`; `scripts/gen_tom_unified_view_seed.py`.
- **Touch:** new `scripts/gen_recursive_tom_seed.py` + `seeds/recursive_tom.json`; `tests/test_recursive_tom_migrated.py`.
- **Pattern to copy:** scoped graph entities and native JOIN/Exists rules.
- **Steps:** 1. Materialize path-scoped worlds and event-driven updates. 2. Resolve queries inside the requested holder path; preserve unknowns. 3. Prevent cycles, duplicate worlds and cross-level leakage through explicit guards.
- **Guard:** `RecursiveTomPolicy.enabled`, default 0.
- **Acceptance:** F2.1 tests plus `test_repeated_event_idempotent`, `test_holder_swap_changes_answer`, `test_minimal_dependency_boot`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_recursive_tom_migrated.py tests/test_character_tom.py -q -p no:cacheprovider`.
- **Non-goals:** changing actual observations to match a character belief.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.F2.3 — Make the recursive ToM adapter mechanical

- **ID:** P5.F2.3
- **Tier:** T2
- **Goal:** Make the recursive ToM adapter mechanical.
- **Read first:** `domains/character_tom.py:340-522`; `tests/test_recursive_tom_migrated.py`; `tests/test_character_tom.py:245-279`.
- **Touch:** `domains/character_tom.py`; `domains/wiktionary_reference.py` (English POS fallback when its optional slab is absent); `tests/test_character_tom.py` (recursive rule contract remains covered by the F2.2 fixture suite).
- **Pattern to copy:** P4 regulated-thought adapter migration.
- **Steps:** 1. Replace nested-world decision branches with event ingestion and graph query readback. 2. Keep sentence parsing as translation only where permitted by architecture. 3. Compare captured first-order public outputs and second-order cases.
- **Guard:** explicit ToM API invocation; recursive policy opt-in.
- **Acceptance:** `test_adapter_has_no_belief_update_decisions`, all first-order tests, and all F2 acceptance tests pass.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_recursive_tom_migrated.py tests/test_character_tom.py -q -p no:cacheprovider`.
- **Non-goals:** a Python helper deciding who knows what.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.G2.1 — Specify evidence-preserving reappraisal

- **ID:** P5.G2.1
- **Tier:** T1
- **Goal:** Specify evidence-preserving reappraisal.
- **Read first:** `seeds/core_emotions.json`; `seeds/arousal_window_coreg.json`; `tests/test_core_emotions_migrated.py:50-98`; `COGNITION_APERTURE_ADAPTER_CONTRACT.md` (P4).
- **Touch:** `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_reappraisal_migrated.py`.
- **Pattern to copy:** core emotion minimal-pair discriminators and chosen-frame proposals.
- **Steps:** 1. Define observed event, appraisal frame, competing interpretations and validity checks. 2. Separate reappraisal from arousal pull and unsupported denial. 3. Write beneficial valid frame, adverse evidence, no alternative and forced-frame fixtures.
- **Guard:** planned `ReappraisalPolicy.enabled=0`.
- **Acceptance:** planned `test_alternative_input_reappraised`, `test_event_unchanged`, `test_unsupported_optimism_rejected`, `test_no_frame_no_reappraisal`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_reappraisal_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** rewarding reduced distress alone; changing core emotion thresholds.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.G2.2 — Re-run core appraisal over verified alternative frames

- **ID:** P5.G2.2
- **Tier:** T2
- **Goal:** Re-run core appraisal over verified alternative frames.
- **Read first:** `tests/test_reappraisal_migrated.py`; `seeds/core_emotions.json`; `seeds/thinking_budget.json`; `scripts/gen_cognition_aperture_seed.py` (P4).
- **Touch:** new `scripts/gen_reappraisal_seed.py` + `seeds/reappraisal.json`; `tests/test_reappraisal_migrated.py`.
- **Pattern to copy:** funded chosen-frame probe and immutable source descriptor.
- **Steps:** 1. Propose bounded alternative interpretations. 2. Check against grounded evidence and core appraisal rules in a separate view. 3. Adopt only the interpretation view with provenance; restore on failed/denied probe.
- **Guard:** `ReappraisalPolicy.enabled`, default 0.
- **Acceptance:** G2.1 tests plus `test_probe_funded_once`, `test_appraisal_provenance_retained`, `test_forced_constraints_preserved`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_reappraisal_migrated.py tests/test_core_emotions_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** editing the immutable source event or passing off relief as verified truth.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.G3.1 — Specify action inhibition before external emission

- **ID:** P5.G3.1
- **Tier:** T1
- **Goal:** Specify action inhibition before external emission.
- **Read first:** `seeds/dual_process_core.json`; `seeds/reflex_core.json`; `tests/test_dual_process_core_migrated.py`; `CLAUDE.md:40-65`.
- **Touch:** new `COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_response_inhibition_migrated.py`.
- **Pattern to copy:** dual-process refusal provenance and engine commit boundary.
- **Steps:** 1. Enumerate proposal, selected, authorized, emitted and observed action states. 2. Define conflict/stop event priority, late-stop outcome and retry identity. 3. Specify one common emission token check in the native dispatch path; graph inhibition cannot revoke an already emitted action.
- **Guard:** planned `ResponseInhibitionPolicy.enabled=0`.
- **Acceptance:** planned `test_stop_before_emit_withholds`, `test_go_executes_once`, `test_late_stop_reports_already_emitted`, `test_same_epoch_stop_wins`; exact dispatch file and symbol recorded in contract.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a promise to undo physical effects; lowering action safety checks.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.G3.2 — Implement graph stop and withhold lifecycle

- **ID:** P5.G3.2
- **Tier:** T2
- **Goal:** Implement graph stop and withhold lifecycle.
- **Read first:** `COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `tests/test_response_inhibition_migrated.py`; `seeds/dual_process_core.json`; `seeds/reflex_core.json`.
- **Touch:** new `scripts/gen_response_inhibition_seed.py` + `seeds/response_inhibition.json`; `tests/test_response_inhibition_migrated.py`.
- **Pattern to copy:** existing refusal marks with monotonic action states.
- **Steps:** 1. Mint idempotent stop requests and revoke pending authorization tokens. 2. Emit explicit withheld/late terminal records. 3. Test priority and stale events at fixpoint.
- **Guard:** `ResponseInhibitionPolicy.enabled`, default 0.
- **Acceptance:** G3.1 tests pass for graph lifecycle; `test_withheld_cannot_rearm_from_same_request`, `test_default_off_parity`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming emission safety before G3.3 dispatch integration.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.G3.3 — Enforce authorization at the native action boundary

- **ID:** P5.G3.3
- **Tier:** T2
- **Goal:** Enforce authorization at the native action boundary.
- **Read first:** `COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `runners/dsl/src/py.rs`; `seeds/reflex_core.json`; `tests/test_response_inhibition_migrated.py`.
- **Touch:** `substrate/world_adapter.py` (`WorldAdapter.fire_reflexes`, `_apply_world_action_at_sink`, and active `live`/`live_examined`/`live_gamma` sinks); `runners/dsl/src/py.rs` (`PySubstrate` authorization/commit methods); `tests/test_response_inhibition_migrated.py`. `lib.rs` is not required because the gate stays in existing `PySubstrate` methods.
- **Pattern to copy:** native dispatch ownership identified by G3.1; freeze exact symbol before edits.
- **Steps:** 1. Route native dispatch and world `apply_action` commits through a monotonic authorization check immediately before emission. 2. Cover reflex callbacks and the active `live`/`live_examined`/`live_gamma` action sinks. 3. Test instrumented sinks for zero stopped emissions, one authorized emission, receipt creation, and terminal sink failure; rebuild and provenance-check.
- **Guard:** policy guard preserves default path; hard host veto always enforced.
- **Acceptance:** `test_native_sink_never_receives_stopped_action`, `test_same_epoch_stop_wins_at_sink`, `test_sink_idempotence`, `test_world_action_sink_never_receives_stopped_action`, `test_world_action_sink_consumes_once_and_records_receipt`, and `test_world_action_sink_failure_is_terminal`; graph-only assertions are insufficient.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_response_inhibition_migrated.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** host-side Python action selection; skipping a dispatch route because fixtures do not exercise it.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.E3.1 — Specify an explicit SCM beside CAN and causal facts

- **ID:** P5.E3.1
- **Tier:** T1
- **Goal:** Specify an explicit SCM beside CAN and causal facts.
- **Read first:** `runners/dsl/src/can_ops.rs:40-119`; `domains/imagination.py:176-236`; `tests/test_remote_causal_migrated.py:42-62`; `tests/test_can_ops.py:96-137`.
- **Touch:** new `COGNITION_SCM_CONTRACT.md`; `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_scm_intervention_migrated.py`.
- **Pattern to copy:** remote causal do-contrast and detached grounding cut; no generic SCM precedent, so T1 spec.
- **Steps:** 1. Define finite acyclic endogenous variables, exogenous inputs and structural equations; declare unsupported cycles. 2. Map CausalFacts to supported structural mechanisms only; CAN energy/couplings are not automatically causal equations. 3. Freeze do(X=x) edge surgery, shared exogenous assignment for counterfactuals and a valid observed backdoor adjustment set with positivity checks.
- **Guard:** planned `ScmPolicy.enabled=0`.
- **Acceptance:** planned `test_do_differs_from_conditioning`, `test_confounder_adjustment_matches_oracle`, `test_collider_not_adjusted`, `test_no_identification_returns_unknown`, `test_live_graph_unchanged`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_scm_intervention_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** general do-calculus completeness; interpreting associative CAN edges as causal mechanisms.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

## P5.R — Rust integration for `SCMIntervene`

These tasks run only if the corresponding spec establishes that existing Terms cannot express the operation. Each task is a single variant change. The spec freezes the argument and result schema first. No caller becomes active until R4 passes. If no new variant is needed, record all four tasks as not required with the existing expression and test evidence.

### P5.R1 — Define and evaluate SCMIntervene

- **ID:** P5.R1
- **Tier:** T2
- **Goal:** Define and evaluate SCMIntervene.
- **Read first:** `runners/dsl/src/term.rs::TermNode`; `runners/dsl/src/can_ops.rs`; `COGNITION_SCM_CONTRACT.md`.
- **Touch:** `runners/dsl/src/can_ops.rs`; `COGNITION_SCM_CONTRACT.md` (freeze the concrete finite dict layout and implement/test the pure evaluator helper; the TermNode wiring is R2).
- **Pattern to copy:** `term.rs::TimeInfer` dispatch and `shape_decode.rs::eval_time_infer`.
- **Steps:** 1. Implement the frozen pure finite-model evaluator helper. 2. Add Rust unit tests for valid, empty, malformed and bounded inputs. 3. Cover every ownership and failure case in the spec; TermNode/dispatch wiring follows in R2 so each bounded file touch remains reviewable.
- **Guard:** new variant has no callers in default seeds.
- **Acceptance:** Rust unit tests assert the frozen output and no mutation of the live graph.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** new Python decision code; changes to other variants.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.R2 — Wire SCMIntervene JSON and graph reflection

- **ID:** P5.R2
- **Tier:** T2
- **Goal:** Wire SCMIntervene JSON and graph reflection.
- **Read first:** `runners/dsl/src/jsonio.rs`; `runners/dsl/src/reflect.rs`; `COGNITION_SCM_CONTRACT.md`.
- **Touch:** `runners/dsl/src/term.rs`; `runners/dsl/src/jsonio.rs`; `runners/dsl/src/reflect.rs`; `runners/dsl/src/term_variants.rs` (the frozen variant must be declared and assigned metadata in the same compileable schema-wiring step).
- **Pattern to copy:** existing `TimeInfer` arms in both modules.
- **Steps:** 1. Add parse and serialize arms. 2. Add reflection and reconstruction. 3. Test JSON and graph round trips without losing optional fields.
- **Guard:** new variant only.
- **Acceptance:** round-trip tests preserve every field and reject malformed forms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** evaluator semantics changes.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.R3 — Wire SCMIntervene traversal and variant metadata

- **ID:** P5.R3
- **Tier:** T2
- **Goal:** Wire SCMIntervene traversal and variant metadata.
- **Read first:** `runners/dsl/src/rewrite.rs`; `runners/dsl/src/term.rs`; `runners/dsl/src/term_variants.rs`.
- **Touch:** `runners/dsl/src/rewrite.rs`; `runners/dsl/src/term.rs`; `runners/dsl/src/term_variants.rs`.
- **Pattern to copy:** existing `TimeInfer` substitution, free-variable and metadata arms.
- **Steps:** 1. Cover substitution, clone/remap, free variables and stability. 2. Regenerate tracked variant metadata by its existing generator. 3. Audit all exhaustive dispatch sites; if additional sites are found, add separate ≤3-file task records before touching them.
- **Guard:** new variant only.
- **Acceptance:** free-variable isolation, graph-change invalidation, serialization and compile checks pass; no missing dispatch arm.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** unconditional memoization of graph mutation; copying another author’s generated artifacts.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.R4 — Build and expose SCMIntervene through the native evaluator

- **ID:** P5.R4
- **Tier:** T2
- **Goal:** Build and expose SCMIntervene through the native evaluator.
- **Read first:** `scripts/engine_build.sh`; `runners/dsl/src/py.rs`; `COGNITION_SCM_CONTRACT.md`.
- **Touch:** `runners/dsl/src/can_ops.rs`; `runners/dsl/src/term.rs`; `runners/dsl/src/sym.rs`; `tests/test_scm_intervention_migrated.py` (native conformance fixtures; pure Term dispatch uses a small fixed reserved-symbol vocabulary because `EvalCtx`'s interner is immutable).
- **Pattern to copy:** `tests/test_time_infer_migrated.py::_boot` and native Term evaluation.
- **Steps:** 1. Build through engine_build.sh after disk check. 2. Evaluate JSON through the native API; add a thin binding only if required. 3. Run Rust tests, provenance and regression gates; record artifact hash.
- **Guard:** no default feature or default seed changes.
- **Acceptance:** native acceptance covers the full frozen spec; provenance identifies the new engine; Cargo baseline has no new failures.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_scm_intervention_migrated.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** default Cargo feature changes; JIT or WASM semantic forks.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.E3.1a — Freeze the native backdoor-adjustment query shape

- **ID:** P5.E3.1a
- **Tier:** T1
- **Goal:** Extend the native SCM query contract to cover registered finite backdoor adjustment explicitly.
- **Read first:** `COGNITION_SCM_CONTRACT.md`; P5.E3.1 adjustment and collider fixtures.
- **Touch:** `COGNITION_SCM_CONTRACT.md`.
- **Pattern to copy:** existing finite query/result shape and preregistered positivity and d-separation criteria.
- **Steps:** 1. Add `adjustment` as a query kind with an explicit adjustment set and one treatment value. 2. Freeze standardized stratum-weight output and unknown conditions for descendants, open backdoor paths and failed positivity.
- **Guard:** finite supplied exogenous assignments only; no general do-calculus or learned mechanisms.
- **Acceptance:** the contract fixes exact query fields, output row shape, population weights and abstention reasons before implementation.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_scm_intervention_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** changing the held-out E3 thresholds or adding continuous variables.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch.

### P5.E3.1b — Implement finite native backdoor adjustment

- **ID:** P5.E3.1b
- **Tier:** T2
- **Goal:** Evaluate registered backdoor adjustments in `SCMIntervene` with exact finite graph checks.
- **Read first:** `COGNITION_SCM_CONTRACT.md`; `runners/dsl/src/can_ops.rs`; the native test fixture.
- **Touch:** `runners/dsl/src/can_ops.rs`; `runners/dsl/src/sym.rs`; generated native artifact pair `runners/dsl/python/substrate_rs/_native.abi3.so` + `_native.build.json`.
- **Pattern to copy:** finite equation validation and exact detached model evaluation in P5.R1.
- **Steps:** 1. Build the causal DAG from explicit endogenous-parent and exogenous-parent links. 2. Validate the backdoor set using descendant exclusion, treatment-mutilated d-separation and stratum positivity. 3. Emit weighted finite outcome rows or `unknown` with a typed reason.
- **Guard:** reject malformed sets, missing adjustment values, cycles, unsupported variables and empty/unsupported populations.
- **Acceptance:** native Rust Term tests match the confounded oracle and reject collider/descendant and positivity failures; no graph handle is available to this evaluator.
- **Verify cmd:** `scripts/engine_cargo_test.sh --lib scm_backdoor_adjustment -- --test-threads=4`.
- **Non-goals:** general do-calculus completeness or adjustment-set search.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch.

### P5.E3.1c — Verify backdoor adjustment through the built Python engine

- **ID:** P5.E3.1c
- **Tier:** T2
- **Goal:** Pin the finite adjustment result and abstentions through the public native Term API.
- **Read first:** `tests/test_scm_backdoor_adjustment_migrated.py`; `COGNITION_SCM_CONTRACT.md`.
- **Touch:** new `tests/test_scm_backdoor_adjustment_migrated.py`.
- **Pattern to copy:** `test_scm_intervention_migrated.py` native `SCMIntervene` invocation.
- **Steps:** 1. Assert standardized outcome weights on a held-out confounded fixture. 2. Assert collider/descendant and positivity cases return unknown.
- **Guard:** use the provenance-verified release artifact; no Python SCM oracle supplies evaluator decisions.
- **Acceptance:** all native adjustment API fixtures pass and provenance remains current.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_scm_backdoor_adjustment_migrated.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** end-to-end causal claims outside the finite fixture class.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch.

### P5.E3.2 — Wire causal queries through detached native SCM evaluation

- **ID:** P5.E3.2
- **Tier:** T2
- **Goal:** Wire causal queries through detached native SCM evaluation.
- **Read first:** `COGNITION_SCM_CONTRACT.md`; `tests/test_scm_intervention_migrated.py`; `seeds/remote_causal.json`; `seeds/thinking_budget.json`.
- **Touch:** new `scripts/gen_scm_reasoning_seed.py` + `seeds/scm_reasoning.json`; `tests/test_scm_intervention_migrated.py`.
- **Pattern to copy:** remote do-contrast with explicit detached query/result records.
- **Steps:** 1. Build explicit SCM query objects from supported model facts. 2. Evaluate graph surgery on detached native data; charge computation and retain source model hash. 3. Return intervention, adjustment or nonidentification records without promoting them to observations.
- **Guard:** `ScmPolicy.enabled`, default 0.
- **Acceptance:** E3.1 tests plus `test_source_model_epoch_invalidates`, `test_query_budget_bound`, `test_detached_result_not_observed`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_scm_intervention_migrated.py tests/test_remote_causal_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** rewriting imagination.py or existing remote causal semantics; hidden-variable identification without assumptions.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.E3.2a — Register detached SCM query readouts as provenance-only signals

- **ID:** P5.E3.2a
- **Tier:** T1
- **Goal:** Keep the linter honest while explicitly classifying detached SCM result and stale-reason attributes as terminal query readouts.
- **Read first:** `scripts/lint_orphan_signals.py`; `scripts/orphan_signal_allowlist.json`; `seeds/scm_reasoning.json`; `COGNITION_SCM_CONTRACT.md`.
- **Touch:** this plan; `scripts/orphan_signal_allowlist.json`.
- **Pattern to copy:** narrowly scoped provenance-only P4 allowlist entries.
- **Steps:** 1. Confirm only `scm_result` and `scm_reason` are new query-result orphans. 2. Allowlist those exact attributes with a reason stating they are caller-visible detached diagnostic records, not observations or decision inputs. 3. Verify seed-only orphan lint still reports no other unallowlisted SCM outputs.
- **Guard:** allowlist only the two named attributes; no node-type or general SCM exemption.
- **Acceptance:** linter reports both with the explicit reason and no other new SCM orphan.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/lint_orphan_signals.py --seed-only --exclude-allowlisted`.
- **Non-goals:** hiding an unconsumed signal that later drives a decision; promoting a query result into world evidence.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch.

### P5.E4.1 — Specify a bounded planner and grounded candidate arbitration

- **ID:** P5.E4.1
- **Tier:** T1
- **Goal:** Specify a bounded planner and grounded candidate arbitration.
- **Read first:** `seeds/generative_world_model.json`; `seeds/goal_derivation.json`; `COGNITION_BUILD_P1_RESULTS.md:26-40`; `COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md` (P4).
- **Touch:** new `COGNITION_PLANNER_CONTRACT.md`; `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_cognition_multistep_planner_migrated.py`.
- **Pattern to copy:** GWM bounded rollout requests and P1 advisory ImaginedCandidate.
- **Steps:** 1. Freeze state/goal satisfaction, admissible successor generation, model version, frontier identity, cycle detection, depth=8 and max expanded states=256. 2. Preserve feasible alternatives; use manifold minimum-sufficient intervention selection and goal tie rules, never a sum of arbitrary costs. 3. Define terminal solved/exhausted/unknown/model-stale statuses, budget requests, candidate re-open tokens and observation-grounded settlement.
- **Guard:** planned `CognitionPlannerPolicy.enabled=0`.
- **Acceptance:** planned `test_two_step_delayed_reward`, `test_cycle_terminates`, `test_missing_transition_unknown`, `test_imagined_not_system_one`, `test_stale_model_replans`; exact re-open contract recorded.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_multistep_planner_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** assuming stochastic GWM predictions are certainties; silently disabling frozen dual-process guards.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.E4.2 — Implement graph-resident bounded multi-step search (complete)

- **ID:** P5.E4.2
- **Tier:** T2
- **Goal:** Implement graph-resident bounded multi-step search.
- **Read first:** `COGNITION_PLANNER_CONTRACT.md`; `seeds/generative_world_model.json`; `scripts/gen_impasse_simulation_bridge_seed.py`; `seeds/thinking_budget.json`.
- **Touch:** new `scripts/gen_cognition_planner_seed.py` + `seeds/cognition_planner.json`; `tests/test_cognition_multistep_planner_migrated.py`.
- **Pattern to copy:** GWM rollout expansion and P3 one-request-per-funded-step.
- **Steps:** 1. Materialize frontier and parent/path state as graph data. 2. Expand only grammar-admissible model actions under depth, node and budget bounds; keep uncertainty branches. 3. Verify terminal goals and emit a candidate plan or explicit impasse/needs_tool request.
- **Guard:** `CognitionPlannerPolicy.enabled`, default 0.
- **Acceptance:** E4.1 contract fixtures plus graph-backed tests: `test_graph_planner_materializes_and_funds_two_step_plan`, `test_graph_planner_deduplicates_cycles_and_stale_transitions`, `test_graph_planner_missing_transition_is_unknown`, `test_graph_planner_depth_bound_is_terminal`, `test_graph_planner_expansion_limit_is_terminal`, `test_graph_planner_hard_depth_cap_is_eight`, `test_graph_planner_rejects_stale_model_snapshot`, `test_graph_planner_cancels_stale_snapshot_before_state_adaptation`, `test_graph_planner_preserves_two_goal_paths_but_counts_unique_expansions`, `test_graph_planner_does_not_solve_without_projection_feasibility`, `test_graph_planner_rejects_invalid_native_feasibility_receipt`, `test_graph_planner_cancels_expired_request`, `test_graph_planner_propagates_deadline_and_blocks_late_budget_debit`, `test_graph_planner_rejects_mismatched_owner_or_start_identity`, `test_graph_planner_preserves_alternate_paths_through_shared_intermediate` (including distinct full path-arrival chains), `test_graph_planner_path_arrival_limit_closes_without_partial_candidates`, and `test_graph_planner_accepts_native_p4_projection_receipt`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_multistep_planner_migrated.py tests/test_goal_derivation_migrated.py tests/test_compositional_plan_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** Python beam search; duplicating Track I goal-directed invention.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P5.E4.2a — Make shared budget requests deadline-aware (complete)

- **ID:** P5.E4.2a
- **Tier:** T2
- **Goal:** Ensure a stale planning request cannot consume ThinkingBudget after its deadline.
- **Read first:** `scripts/gen_thinking_budget_seed.py`; `tests/test_thinking_budget_migrated.py`; `COGNITION_PLANNER_CONTRACT.md`.
- **Touch:** `scripts/gen_thinking_budget_seed.py`; `seeds/thinking_budget.json`; `tests/test_thinking_budget_migrated.py`. Planner request propagation of `deadline_epoch` is completed separately within E4.2's three-file touch set.
- **Steps:** 1. Cancel pending requests whose optional deadline is behind the current `NetworkModeState.epoch`. 2. Guard enabled and disabled approval paths so expired requests cannot be approved or debited in the same rules pass. 3. Preserve legacy requests with no deadline.
- **Guard:** Existing ThinkingBudget behavior for requests without `deadline_epoch` remains unchanged.
- **Acceptance:** New enabled-budget and disabled-budget expiration tests assert terminal cancellation and zero debit; existing ThinkingBudget acceptance remains green.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest tests/test_thinking_budget_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** Planner-owned budget accounting or changing non-expired requester behavior.
- **Done when:** named acceptance passes, seed generator reproduces the manifest, and boot/test regressions stay green.

### P5.E4.2b — Compose complete planner paths through the native manifold projector (complete)

- **ID:** P5.E4.2b
- **Tier:** T2
- **Goal:** Ensure a multi-step imagined plan is feasible only when its complete ordered path has a native P4 manifold projection and measured intervention comparison.
- **Read first:** `COGNITION_PLANNER_CONTRACT.md` § Complete-path projection profile; `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`; `runners/dsl/src/future_manifold.rs::projection_field`; `scripts/gen_cognition_manifold_seed.py`.
- **Touch:** `scripts/gen_cognition_planner_seed.py`; `seeds/cognition_planner.json`; `tests/test_cognition_multistep_planner_migrated.py`; `runners/dsl/src/future_manifold.rs`; `tests/test_future_manifold_projection_native.py`; `tests/test_cognition_manifold_migrated.py`.
- **Steps:** 1. Give every path arrival one predecessor path arrival, transition and destination; cap arrivals per request and close explicitly at the cap. 2. Extend the existing `FutureManifoldProjection` source handling for one terminal path candidate: compose only contiguous, explicitly timed transition matrices, preserving every shape row through the required horizon. 3. Carry the shared-unit sum of model-represented non-negative effort into the existing P4 minimum-intervention selector; retain all exact minima and never assign zero to missing effort. 4. Return unresolved/`unknown` on missing, malformed, gapped, stale or incomplete path evidence.
- **Guard:** Existing `CognitionPlannerPolicy.enabled=0`; do not add a term variant or default profile activation.
- **Acceptance:** `test_path_projection_composes_contiguous_segments_and_uses_native_shape_audit`, `test_path_projection_rejects_missing_or_gapped_segment`, `test_path_projection_ranks_by_measured_effort_and_keeps_ties`, `test_path_arrival_lineage_keeps_distinct_shared_prefix_paths`, `test_path_arrival_limit_closes_without_partial_candidates`, and `test_single_candidate_projection_compatibility_unchanged`, plus the complete E4.2 acceptance list.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_multistep_planner_migrated.py tests/test_cognition_manifold_migrated.py tests/test_future_manifold_projection_native.py tests/test_goal_derivation_migrated.py tests/test_compositional_plan_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** Python path construction or scoring; a new TermNode variant; approximate time alignment; goal rank overriding intervention; policy/default activation.
- **Done when:** named native and graph acceptance passes; same-source P4 projection regressions pass; generator/serialization and boot checks pass; path and projection gaps are either closed or explicitly returned as unknown. Verified: 85 combined Python acceptance tests and 24 focused Rust future-manifold tests pass; seed load tests report no skipped planner rules.

### P5.E4.3 — Consume imagined candidates through System-2 arbitration (complete)

- **ID:** P5.E4.3
- **Tier:** T2
- **Goal:** Consume imagined candidates through System-2 arbitration.
- **Read first:** `COGNITION_PLANNER_CONTRACT.md`; `COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `seeds/impasse_simulation_bridge.json`; `tests/test_cognition_multistep_planner_migrated.py`.
- **Touch:** new `scripts/gen_imagined_candidate_arbitration_seed.py` + `seeds/imagined_candidate_arbitration.json`; `scripts/gen_cognition_planner_seed.py` + `seeds/cognition_planner.json` (preserve the first action/state and stable path identity); `tests/test_cognition_multistep_planner_migrated.py`.
- **Pattern to copy:** P1 proposal provenance and G3 authorization token.
- **Steps:** 1. Consume has_imagined_candidate into a new System-2 decision revision tied to context/model epochs. 2. Re-open only candidates named by the explicit contract; verify current goal and manifold before authorizing through G3. 3. Keep imagined provenance through execution; create grounded evidence only after matching real receipt, then settle parent context.
- **Guard:** `ImaginedArbitrationPolicy.enabled`, default 0.
- **Acceptance:** `test_advisory_candidate_consumed_once`, `test_tied_minimum_candidates_keep_distinct_system_two_action_ids`, `test_no_grounding_before_receipt`, `test_matching_observation_after_sink_receipt_grounds_candidate`, `test_mismatched_observed_state_does_not_ground_candidate`, `test_reopened_candidate_reverified`, `test_stop_blocks_imagined_action`, `test_model_change_cancels_authorization`, and `test_imagined_arbitration_policy_is_disabled_by_default`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_multistep_planner_migrated.py tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** editing frozen dual_process_core to weaken its confidence thresholds; treating a rollout as action success.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. The 53-test E4.3 planner/G3 command and the 85-test E4.2b combined command pass. The opt-in seed selects a concrete first path action but does not mint G3 authorization; only the native G3 dispatch boundary may consume that token. Grounding requires the sink receipt plus the expected first-step state observation. Held-out evidence is produced at the phase evaluation task.

### P5.A2.1 — Specify parent completion after capability decomposition (complete)

- **ID:** P5.A2.1
- **Tier:** T1
- **Goal:** Specify parent completion after capability decomposition.
- **Read first:** `COGNITION_BUILD_P1_RESULTS.md:26-40`; `seeds/decomposition_consumer.json`; `seeds/impasse_escalation.json`; `tests/test_decomposition_consumer_migrated.py`.
- **Touch:** `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_decomposition_completion_migrated.py`.
- **Pattern to copy:** dc_parent_progress_from_children diagnostic rollup.
- **Steps:** 1. Require every required CapKey to be covered by verified completed child work in the same decomposition/model epoch. 2. Define empty-child, overlapping-child, partial and stale cases. 3. Separate parent saturation update from impasse resolution; require both completion evidence and no outstanding required child.
- **Guard:** planned `DecompositionCompletionPolicy.enabled=0`.
- **Acceptance:** `test_partial_children_do_not_complete`, `test_all_required_keys_complete_parent`, `test_stale_child_reopens`, `test_empty_children_never_complete`, plus overlap, stale-epoch, verification, pending-child and diagnostic-only saturation controls.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_decomposition_completion_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** using child_mean_saturation alone as completion evidence.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task. Verified: 9 executable contract tests pass; runtime implementation is P5.A2.2.

### P5.A2.2 — Resolve completed parent axes without premature de-escalation

- **ID:** P5.A2.2
- **Tier:** T2
- **Goal:** Resolve completed parent axes without premature de-escalation.
- **Read first:** `tests/test_decomposition_completion_migrated.py`; `seeds/decomposition_consumer.json`; `scripts/gen_decomposition_consumer_seed.py`.
- **Touch:** new `scripts/gen_decomposition_completion_seed.py` + `seeds/decomposition_completion.json`; `tests/test_decomposition_completion_migrated.py`.
- **Pattern to copy:** P1 deduplicated child axes and explicit provenance edges.
- **Steps:** 1. Add completion witness rules and parent/impasse settlement. 2. Invalidate the witness when required coverage changes. 3. Test epoch changes and repeated fixpoints; preserve original diagnostic rollup.
- **Guard:** `DecompositionCompletionPolicy.enabled`, default 0.
- **Acceptance:** A2.1 tests plus `test_completion_idempotent`, `test_parent_impasse_settles_only_with_witness`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_decomposition_completion_migrated.py tests/test_decomposition_consumer_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** rewriting escalation order or declaring a parent solved from average progress.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. **Complete:** runtime acceptance and legacy-consumer command pass 22 tests. The default-off seed requires parent model/decomposition epochs and child `completion_status="completed"`, `completion_verified=1`, and matching epochs; missing evidence keeps the impasse open. Coverage loss or epoch changes invalidate the witness, restore pre-completion saturation and reopen the impasse. Parent `child_mean_saturation` remains diagnostic only.

### P5.D6.1 — Specify analog rotation and detached imagery work

- **ID:** P5.D6.1
- **Tier:** T1
- **Goal:** Specify analog rotation and detached imagery work.
- **Read first:** `seeds/shape_decode_loop.json`; `domains/imagination.py:124-236`; `tests/test_geninfer_grain_migrated.py`; `runners/dsl/src/shape_decode.rs::eval_time_infer`.
- **Touch:** `COGNITION_BUILD_P5_PREREG.md`; new `tests/test_analog_imagery_migrated.py`.
- **Pattern to copy:** existing held rotation generators and detached grounding cut.
- **Steps:** 1. Freeze shortest-angle path, angular quantum from representation resolution, intermediate witnesses and wrap-around. 2. Declare initial lattice-preserving domain; unsupported arbitrary angles remain unresolved until a sampled continuous representation is explicitly specified. 3. Measure actual bounded transform work per angular increment; a planted angle-based latency value is not evidence.
- **Guard:** planned `AnalogImageryPolicy.enabled=0`.
- **Acceptance:** planned `test_angle_wrap_and_identity`, `test_intermediate_witnesses`, `test_buffer_never_grounds`, `test_cost_counts_executed_transforms`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_analog_imagery_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming human mental-rotation timing from a programmed cost counter.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

  **Complete:** the executable D6.1 contract fixture passes five tests. The initial domain is the square lattice at 0/90/180/270 degrees, shortest signed quarter-turn paths, clockwise tie-breaking at 180 degrees, intermediate witnesses, detached buffers and transform-count cost. Unsupported angles remain unresolved.

### P5.D6.2 — Run rotation trajectories in a bounded native imagery buffer

- **ID:** P5.D6.2
- **Tier:** T2
- **Goal:** Run rotation trajectories in a bounded native imagery buffer.
- **Read first:** `tests/test_analog_imagery_migrated.py`; `seeds/thought_manifold.json` (P4); `seeds/shape_decode_loop.json`; `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md` (P4).
- **Touch:** new `scripts/gen_analog_imagery_seed.py` + `seeds/analog_imagery.json`; `tests/test_analog_imagery_migrated.py`.
- **Pattern to copy:** P4 ThoughtManifold detached trajectory and existing exact rotation Terms.
- **Steps:** 1. Compose held transforms in graph rules and retain intermediate witnesses. 2. Fund each increment, bound buffer size and expire terminal buffers. 3. Verify transformed shape before proposing a reading; source observations stay unchanged.
- **Guard:** `AnalogImageryPolicy.enabled`, default 0.
- **Acceptance:** D6.1 tests plus `test_budget_exhausts_unresolved`, `test_shape_verified_after_rotation`, `test_buffer_growth_bounded`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_analog_imagery_migrated.py tests/test_thought_manifold_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a new arbitrary-angle solver; Python image transforms as agent reasoning.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

  **Complete:** the combined analog-imagery and ThoughtManifold gate passes 27 tests. The default-off graph seed executes quarter-turn transforms one step per shared ThinkingBudget unit, records every intermediate signature, caps each request at three increments/four buffer entries, verifies exact expected shape, leaves source observations unchanged, never marks imagery grounded, rejects unsupported increments and expires terminal buffers. Budget exhaustion leaves the request unresolved.

## Held-out evaluation specification

Freeze 200 independently generated paired instances per primary family and 100 adverse/control cases per item. F1/E3 conformance checks may use exact finite oracles; all source identities, event orders and model parameters are held out. Register all families before the H1 commit.

| Item | Arms and families | Primary decision criteria |
|---|---|---|
| F1 | Shared view on/off; four source representations, contradictions and owner permutations | ≥95% exact view conformance; zero belief-to-truth leaks; no loss of original source assertions |
| F2 | Recursive rules on/off; second-order false/true belief minimal pairs, unseen holder names and access orders | ≥80% exact query accuracy and ≥20-point gain, corrected p<.01; zero actual-world overwrites |
| G2 | Reappraisal on/off with identical arousal; valid alternative interpretation versus adverse evidence | ≥20-point gain in evidence-supported appraisal selection, corrected p<.01; zero source-event edits or accepted unsupported interpretations |
| G3 | Inhibition on/off; randomized stop-before/go/late-stop orders at instrumented native sink | 100% timely stops withheld and ≥95% valid go emissions; zero duplicate emissions; late stops reported separately |
| E3 | SCM do/query versus conditioning-only; confounder, collider, chain and nonidentified cases | ≥95% oracle agreement on identifiable finite models; all nonidentified/unsupported cases return unknown; live graph unchanged |
| E4 | Planner versus one-step goal derivation, equal model exposure and budget; delayed reward, traps and missing transitions | ≥20-point solve gain on depth 2–8 cases, corrected p<.01; zero unapproved/unsafe emissions, false grounding or bound violations |
| A2 | Completion consumer on/off; mixed required-key coverage and model-epoch changes | 100% valid completion decisions and zero premature settlements; stale evidence cannot complete a parent |
| D6 | Buffered incremental versus direct exact transform; unseen lattice shapes and angles 0/90/180/270 | ≥95% exact shape verification, zero detached grounding; report actual work versus shortest angle. Any linear work trend is an implementation property; a human timing claim needs a separate protocol |

G3 tests the action boundary even when E4 finds no good plan. E4 reports end-to-end observed success separately from predicted goal satisfaction. A2 and F1 are mechanism evidence without a claim of human cognition.

### P5.H1 — Freeze Phase 5 evaluation artifacts

- **ID:** P5.H1
- **Tier:** T1
- **Goal:** Freeze Phase 5 evaluation artifacts.
- **Read first:** `COGNITION_BUILD_P5_PREREG.md`; `evaluation/substrate_capability/cognition_p4_heldout_v1.py` (P4); `evaluation/substrate_capability/cognition_p4_analysis_v1.py` (P4).
- **Touch:** new `evaluation/substrate_capability/cognition_p5_heldout_v1.py`; new `evaluation/substrate_capability/cognition_p5_analysis_v1.py`; `COGNITION_BUILD_P5_PREREG.md`.
- **Pattern to copy:** P4 seeded paired evaluation; native-sink assertions for inhibition.
- **Steps:** 1. Implement deterministic families, external oracles and arm toggles; use max 64 epochs, planner depth 8 and 256 expansions. 2. Add development self-checks in each module, including null and unsafe-emission reports. 3. Freeze hashes and commit preregistration alone before draws.
- **Guard:** evaluation only.
- **Acceptance:** all eight item protocols represented; self-checks reject absent/altered hashes; intervention truth and belief answers never enter agent inputs.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_multistep_planner_migrated.py tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a Python planner or ToM oracle choosing actions.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

  **Complete:** the original v1 null-preserving harness remains archived. Adapter-backed v2 was frozen separately in commit `4b194b3c5c6a58e5d8765de2a4986e57156b2bd1`; self-checks and the focused P5/profile gate pass, and all eight mechanism adapters return structured outcomes.

The v2 runner and analysis implement `--self-check` for development-only checks. H3 profile integration and focused tests passed before the standalone v2 freeze. The registered run used the frozen hash and command below:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_eval_v2.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_analysis_v2.py --self-check
COGNITION_PREREG_HASH=4b194b3c5c6a58e5d8765de2a4986e57156b2bd1 OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p5_mechanism_eval_v2.py 4b194b3c5c6a58e5d8765de2a4986e57156b2bd1 0 200
```

The runner writes `evaluation/reports/cognition_p5_mechanism_eval_v2_<hash8>_d0-200.json`; invoke `cognition_p5_mechanism_analysis_v2.py` with that exact report. A self-check never uses registered held-out draw indices. The earlier v1 report remains an independent historical NOT_ESTABLISHED result.

### P5.H2 — Run and report every Phase 5 hypothesis

- **ID:** P5.H2
- **Tier:** T1
- **Goal:** Run and report every Phase 5 hypothesis.
- **Read first:** `COGNITION_BUILD_P5_PREREG.md`; `evaluation/substrate_capability/cognition_p5_heldout_v1.py`; `evaluation/substrate_capability/cognition_p5_analysis_v1.py`.
- **Touch:** new `COGNITION_BUILD_P5_RESULTS.md`.
- **Pattern to copy:** P3 honest results and P4 per-item status reporting.
- **Steps:** 1. Run `<prereg_hash> 0 200` and the registered 100 control draws. 2. Analyze all outcomes, invariant failures and corrected tests. 3. Record predicted versus observed success, native work, boot cost and gate exceptions.
- **Guard:** frozen evaluation only.
- **Acceptance:** all eight items have a decision and claim boundary; generated reports remain uncommitted; no failed item disappears from summary.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_multistep_planner_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** retuning on holdout; declaring recursive ToM or SCM general beyond the tested class.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

  **Complete:** v1 commit `0826089af64c38da3c34d3be2c96ca490364ffa3` remains NOT_ESTABLISHED with 3,200 null primary outcomes and unexecuted controls. V2 commit `4b194b3c5c6a58e5d8765de2a4986e57156b2bd1` executed 200 primary cases and 100 controls for all eight items; all eight criteria pass with zero nulls/errors. Full metrics and fixture boundaries are recorded in `COGNITION_BUILD_P5_RESULTS.md`; raw reports remain uncommitted.

### P5.H3 — Integrate the Phase 5 cognition profile

- **ID:** P5.H3
- **Tier:** T2
- **Goal:** Integrate the Phase 5 cognition profile.
- **Read first:** `substrate/boot_profiles.py:769-796`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `COGNITION_BUILD_P5_PREREG.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P4 guarded closure and G3 instrumented sink.
- **Steps:** 1. Add mechanism-tested seed closures with explicit enablement. 2. Test impasse → plan → arbitration → stop/go → observed receipt → completion, with ToM and reappraisal provenance intact. 3. Run phase gates and record no new baseline failures.
- **Guard:** cognition-on only.
- **Acceptance:** `test_p5_planner_arbitration_receipt_chain`, `test_p5_stop_at_native_sink`, `test_p5_default_and_conversation_isolation`; no new regression failures.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** promoting imagined candidates to grounded System-1 habits before observation.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

  **Complete:** the cognition-on profile now loads the P5 planner, imagined arbitration, decomposition completion and analog imagery seeds, with enabled policies attached only by `cognition_on_params`. The profile integration and G3 sink suite passes 28 tests, including policy closure, receipt-gated grounding, native stop withholding and default/conversation isolation. The adapter-backed registered evaluation is complete; imagery proposals remain ungrounded absent an external receipt.


### P5.H4 — Close Phase 5 documentation against actual evidence

- **ID:** P5.H4
- **Tier:** T3
- **Goal:** Close Phase 5 documentation against actual evidence.
- **Read first:** `COGNITION_BUILD_P5_RESULTS.md`; `COGNITION_BUILD_PLAN_20261010.md:1-25`; `COGNITION_CAPABILITY_ASSESSMENT_20261010.md:59-160`.
- **Touch:** `COGNITION_BUILD_PLAN_20261010.md`; `COGNITION_CAPABILITY_ASSESSMENT_20261010.md`; `COGNITION_BUILD_P5_RESULTS.md`.
- **Pattern to copy:** P3 parent status and assessment rows with explicit scope.
- **Steps:** 1. Update each delivered item with mechanism, held-out outcome, supported input class and commit hashes. 2. Retain failed hypotheses and inherited gate exceptions. 3. Assign remaining limitations and downstream prerequisite decisions; mark phase executed only after its implementation and reporting obligations are complete.
- **Guard:** documentation only.
- **Acceptance:** all original work items and carryovers have evidence-scoped status; no future task is described as passed; all links resolve to completed artifacts.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** promoting a mechanism fixture to a human capability claim; erasing null results.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

  **Complete:** parent plan, capability assessment and P5 results record each mechanism's supported fixture class, the archived v1 NOT_ESTABLISHED result, the v2 fixture-level PASS results, inherited P4 C5 failure boundary, and remaining generalization limits. P5 is marked executed as an implementation and reporting cycle; the registered hypotheses establish only behavior on their frozen fixtures.

## Exit and handoff

P6 requires verified planning/rollout and attributed-agent interfaces for imitation. A failed held-out planner gain does not prevent a fixture-backed demonstration verifier, but that limitation must be named in P6 results. Hand off the native dispatch authorization boundary, SCM identification assumptions, supported rotation domain and parent-completion witness format. Update assessment maturity per item after results, retaining negative evidence.
