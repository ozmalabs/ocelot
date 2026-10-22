# Cognition build Phase 6 — Numerosity, imitation and staged sleep

> **Historical workstream specification (2026-10-22).** The [canonical linear plan](COGNITION_BUILD_PLAN_20261010.md) supersedes the execution order and gate schedule in this document. Former P6.D7 is now linear Phase 7; former P6.F3 is Phase 12; former P6.B2 is Phase 13. All original task IDs and design details below remain reference material; statements about parallel tracks or waiting to detail phases are historical.

**Detailed on:** 2026-10-21. **Status:** planned; dependent contracts are reconciled after P5 results.
**Parent:** [Cognition build plan](COGNITION_BUILD_PLAN_20261010.md). **Entry:** P5 implementation/invariant gate and item results.

## Scope and order

D7 supplies a bounded perceptual numerosity representation; `number_world` already grounds exact cardinality, so routing an exact hidden count to the answer would not test an approximate number system. F3 builds a candidate program from attributed observed actions, verifies it in a detached rollout, and adopts through existing safety and grounding boundaries. B2 extends P1's paced MemoryCycle producer into staged offline work; it does not replace the scheduler or assert retention merely because support_count increased.

`H0 → D7 spec/implementation`; `F3` requires P5 attributed-state views, action authorization and a supported rollout model; `B2` requires P1 scheduler, P4 recall and P5 model/version contracts. After these item tests: H3 integrates the guarded profile, H1 freezes protocols and artifacts, H2 runs evidence, then H4 closes the documentation. Track I I6.2 adds lifting/generalization to the demonstrated schema; P6 owns ingestion, candidate construction, verification and first adoption. Track I I2.2/I3.2 may register optional sleep stages only through the bounded stage protocol; their absence must not block ordinary replay.

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

### P6.H0 — Reconcile Phase 5 results and freeze Phase 6 scope

- **ID:** P6.H0
- **Tier:** T1
- **Goal:** Reconcile Phase 5 results and freeze Phase 6 scope.
- **Read first:** `COGNITION_BUILD_P5_RESULTS.md` (P5); `COGNITION_BUILD_P1_RESULTS.md:9-24`; `docs/research/engine_substrate/COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md:124-130`; `seeds/consolidation_scheduler.json`.
- **Touch:** this plan; new `COGNITION_BUILD_P6_PREREG.md`.
- **Pattern to copy:** P5 entry ledger and P1 offline replay counts.
- **Steps:** 1. Record supported ToM, rollout, dispatch and recall interfaces, including failed capability hypotheses. 2. Freeze shared schema/adoption references with committed Track I work. 3. State which optional offline stages are available; no dependency on untracked code.
- **Guard:** documentation only.
- **Acceptance:** all three original P6 items have supported prerequisites or an explicit implementation blocker; no silent fallback to Python reasoning.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** assuming every P5 capability passed.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.D7.1 — Specify perceptual numerosity without hidden exact-count leakage

- **ID:** P6.D7.1
- **Tier:** T1
- **Goal:** Specify perceptual numerosity without hidden exact-count leakage.
- **Read first:** `domains/number_world.py:32-111`; `tests/test_number_world_migrated.py:44-95`; `runners/dsl/src/term.rs::RatioInduce`; `COGNITION_SIGNATURE_CONTRACT.md` (P4).
- **Touch:** new `COGNITION_NUMEROSITY_CONTRACT.md`; `COGNITION_BUILD_P6_PREREG.md`; new `tests/test_numerosity_migrated.py`.
- **Pattern to copy:** number_world cardinality grounding and RatioInduce resolution contract.
- **Steps:** 1. Specify individuated percept input, bounded exact capacity ≤4 and aggregate magnitude shape above capacity. 2. Separate external scoring counts from agent-visible evidence; any compression/noise must be declared and have a justified perceptual source. 3. Define ratio comparison, equal-ratio scale tests, abstention and evidence-derived uncertainty; a hand-imposed Weber curve is not a discovery.
- **Guard:** planned `NumerosityPolicy.enabled=0`.
- **Acceptance:** planned `test_small_sets_exact`, `test_small_set_bounded_work`, `test_large_sets_do_not_read_hidden_count`, `test_equal_ratio_scale_contract`, `test_ambiguous_magnitude_abstains`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_numerosity_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming an approximate number system from exact Length followed by log; claiming human Weber behavior from scripted probabilities.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.D7.2 — Implement bounded subitizing and aggregate magnitude perception

- **ID:** P6.D7.2
- **Tier:** T2
- **Goal:** Implement bounded subitizing and aggregate magnitude perception.
- **Read first:** `COGNITION_NUMEROSITY_CONTRACT.md`; `tests/test_numerosity_migrated.py`; `domains/number_world.py:32-111`; `seeds/observer_aperture.json`.
- **Touch:** new `scripts/gen_numerosity_seed.py` + `seeds/numerosity.json`; `tests/test_numerosity_migrated.py`.
- **Pattern to copy:** Observer grain/quantum projection and native numeric/ratio Terms.
- **Steps:** 1. Read at most four individuated slots for the exact route and expose bounded decision work independent of larger set size; report scene ingestion cost separately. 2. Read only the declared percept aggregate for large-set magnitude; compare in ratio space with native Terms. 3. Preserve uncertainty, sensory confounds and unsupported inputs as graph records.
- **Guard:** `NumerosityPolicy.enabled`, default 0.
- **Acceptance:** D7.1 tests plus `test_no_symbolic_answer_input`, `test_conflicting_area_density_abstains`, `test_generator_reproduction`; no new Term required by the initial aggregate contract.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_numerosity_migrated.py tests/test_number_world_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a new arbitrary log primitive when existing numeric Terms suffice; feeding exact scoring counts through a magnitude attribute.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.D7.3 — Expose a mechanical numerosity world adapter

- **ID:** P6.D7.3
- **Tier:** T2
- **Goal:** Expose a mechanical numerosity world adapter.
- **Read first:** `domains/number_world.py:32-111`; `COGNITION_NUMEROSITY_CONTRACT.md`; `tests/test_numerosity_migrated.py`.
- **Touch:** `domains/number_world.py`; `tests/test_numerosity_migrated.py`.
- **Pattern to copy:** NumberWorld external ingest and graph-owned concept grounding.
- **Steps:** 1. Add a separate percept-input mode with individuated tokens/aggregate sensor evidence and no symbolic answer labels. 2. Ingest and read graph conclusions only. 3. Keep existing symbolic cardinality mode behavior and tests intact.
- **Guard:** explicit numerosity input mode and enabled policy.
- **Acceptance:** `test_adapter_translates_only`, `test_symbolic_mode_parity`, `test_percept_mode_no_cardinality_label`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_numerosity_migrated.py tests/test_number_world_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** replacing an existing mathematical-world task with the new perceptual task.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.F3.1 — Specify attributed demonstration-to-program verification

- **ID:** P6.F3.1
- **Tier:** T1
- **Goal:** Specify attributed demonstration-to-program verification.
- **Read first:** `seeds/program_synthesis.json`; `seeds/generative_world_model.json`; `COGNITION_ACTION_ARBITRATION_CONTRACT.md` (P5); `COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md:124-130`; `tests/test_tom_unified_view_migrated.py` (P5).
- **Touch:** new `COGNITION_IMITATION_CONTRACT.md`; `COGNITION_BUILD_P6_PREREG.md`; new `tests/test_imitation_migrated.py`.
- **Pattern to copy:** program_synthesis candidate→verify→accept lifecycle and ToM source attribution.
- **Steps:** 1. Define Demonstration/step order, actor, observation access, body map, initial/final state and missing steps. 2. Specify literal sequence candidate construction in graph rules, supported action translations and own-rollout success checks. 3. Reference committed ProcessSchema or expose a versioned candidate Program bridge; model verification licenses a candidate, real receipts license grounded evidence.
- **Guard:** planned `ImitationPolicy.enabled=0`.
- **Acceptance:** planned `test_demo_actor_not_self`, `test_order_preserved`, `test_failed_own_rollout_rejects`, `test_missing_step_unresolved`, `test_body_mismatch_not_executed`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** general intent inference from demonstrations; assuming a witnessed action is safe for this body.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.F3.2 — Construct candidate programs from observed action traces

- **ID:** P6.F3.2
- **Tier:** T2
- **Goal:** Construct candidate programs from observed action traces.
- **Read first:** `COGNITION_IMITATION_CONTRACT.md`; `tests/test_imitation_migrated.py`; `seeds/program_synthesis.json`; `scripts/gen_tom_unified_view_seed.py` (P5).
- **Touch:** new `scripts/gen_imitation_seed.py` + `seeds/imitation.json`; `tests/test_imitation_migrated.py`.
- **Pattern to copy:** native program construction Terms and graph trace ordering.
- **Steps:** 1. Validate ordered observed steps and actor attribution. 2. Construct a candidate Program and source-linked schema using only declared action maps. 3. Dedup by demonstration/version; charge construction and request detached rollout.
- **Guard:** `ImitationPolicy.enabled`, default 0.
- **Acceptance:** F3.1 construction tests plus `test_demo_duplicate_idempotent`, `test_candidate_graph_resident`, `test_candidate_not_adopted_yet`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a Python trace compiler choosing action semantics; inventing an action to fill a missing step.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.F3.3 — Verify and adopt demonstrated candidates through existing boundaries

- **ID:** P6.F3.3
- **Tier:** T2
- **Goal:** Verify and adopt demonstrated candidates through existing boundaries.
- **Read first:** `COGNITION_IMITATION_CONTRACT.md`; `tests/test_imitation_migrated.py`; `seeds/cognition_planner.json` (P5); `seeds/adoption_safety.json`; `seeds/thinking_budget.json`.
- **Touch:** `scripts/gen_imitation_seed.py` + `seeds/imitation.json`; `tests/test_imitation_migrated.py`.
- **Pattern to copy:** P5 own-model plan verification, G3 token and existing adoption_safety.
- **Steps:** 1. Roll out the candidate in the learner model with supported uncertainty and compare target effects. 2. Apply adoption safety and manifold projection before authorizing own trial. 3. Retain failed verification and model gaps; mark grounded only after real trial receipt; expose schema for I6.2 lifting.
- **Guard:** `ImitationPolicy.enabled`; existing host/action vetoes remain mandatory.
- **Acceptance:** `test_verified_candidate_adopted_with_provenance`, `test_trial_stop_respected`, `test_grounding_requires_own_receipt`, `test_stale_rollout_reverified`, `test_no_unfunded_trial`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** bypassing adoption safety or grounding a borrowed trace as own experience.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.B2.1 — Specify staged offline cycle ownership and interruption

- **ID:** P6.B2.1
- **Tier:** T1
- **Goal:** Specify staged offline cycle ownership and interruption.
- **Read first:** `seeds/consolidation_scheduler.json`; `seeds/episodic_working_memory_core.json`; `tests/test_consolidation_scheduler_migrated.py:138-229`; `seeds/staleness_decay.json`; `seeds/demotion_hierarchy.json`.
- **Touch:** new `COGNITION_SLEEP_STAGE_CONTRACT.md`; `COGNITION_BUILD_P6_PREREG.md`; new `tests/test_sleep_regime_migrated.py`.
- **Pattern to copy:** P1 cooldown-paced cycle producer and one-replay-per-cycle consumer.
- **Steps:** 1. Define cycle ID/epoch, unique stage owner, replay→consolidate→decay→recombine order, pending/running/complete/interrupted terminal semantics. 2. Specify attention/load interrupt before next atomic step, cursor checkpoint, once-only debit and no duplicate original replay. 3. Define optional Track I extension stages, prerequisites, maximum work, disabled-stage skip and stale model cancellation.
- **Guard:** planned `SleepRegimePolicy.enabled=0`.
- **Acceptance:** planned `test_one_owner_per_cycle`, `test_replay_not_duplicated`, `test_foreground_interrupts`, `test_resume_no_double_debit`, `test_optional_stage_missing_skips`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming retention from replay count; modifying P1 scheduler cooldown semantics.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.B2.2 — Implement ordered replay and consolidation stage ownership

- **ID:** P6.B2.2
- **Tier:** T2
- **Goal:** Implement ordered replay and consolidation stage ownership.
- **Read first:** `COGNITION_SLEEP_STAGE_CONTRACT.md`; `tests/test_sleep_regime_migrated.py`; `scripts/gen_consolidation_scheduler_seed.py`; `seeds/episodic_working_memory_core.json`.
- **Touch:** new `scripts/gen_sleep_regime_seed.py` + `seeds/sleep_regime.json`; `tests/test_sleep_regime_migrated.py`.
- **Pattern to copy:** P1 MemoryCycle producer and replay consumer markers.
- **Steps:** 1. Attach the staged lifecycle to existing cycles without creating a second scheduler. 2. Delegate replay to the existing consumer; advance only after its completion receipt. 3. Consolidate provenance-backed outcomes within budget and interrupt at stage boundaries.
- **Guard:** `SleepRegimePolicy.enabled`, default 0.
- **Acceptance:** B2.1 replay/ownership tests plus `test_stage_order`, `test_high_load_no_offline_work`, `test_consolidation_uses_replay_receipt`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_consolidation_scheduler_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** double-running EWM replay or consolidating unsupported imagined facts.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.B2.3 — Add bounded decay and recombination stages with recovery

- **ID:** P6.B2.3
- **Tier:** T2
- **Goal:** Add bounded decay and recombination stages with recovery.
- **Read first:** `COGNITION_SLEEP_STAGE_CONTRACT.md`; `scripts/gen_sleep_regime_seed.py`; `seeds/staleness_decay.json`; `seeds/demotion_hierarchy.json`; `seeds/default_mode_core.json`.
- **Touch:** `scripts/gen_sleep_regime_seed.py` + `seeds/sleep_regime.json`; `tests/test_sleep_regime_migrated.py`.
- **Pattern to copy:** existing decay-tier scheduling, P1 advisory simulation and P3 budget requests.
- **Steps:** 1. Trigger one owned decay pass per eligible cycle epoch, preserving evidence and protected memory semantics. 2. Mint bounded default-mode recombination proposals with imagined provenance. 3. Persist cursors and stage receipts; implement restart, foreground interruption and optional Track I hook skipping.
- **Guard:** `SleepRegimePolicy.enabled`, default 0.
- **Acceptance:** `test_decay_once_per_cycle_epoch`, `test_recombination_advisory_only`, `test_save_load_resume_no_duplicate`, `test_256_epoch_growth_bounded`, all B2.1 tests.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sleep_regime_migrated.py tests/test_staleness_decay_migrated.py tests/test_demotion_hierarchy_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** optimizing retention by disabling forgetting; silently adopting recombinations.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

## Held-out evaluation specification

| Item | Fixed draws and arms | Primary decision criteria |
|---|---|---|
| D7 | 200 paired percept scenes, sizes 1–4; 200 comparisons for each declared ratio bin 1.1/1.25/1.5/2.0 with multiple absolute scales; 100 conflicting area/density controls. Numerosity on/off and symbolic exact-count oracle as a scoring ceiling only | ≥95% exact small-set accuracy with bounded work; for large sets, discrimination nondecreasing with ratio and ≥75% at ratio≥1.5, held-out equal-ratio scale difference ≤10 points; zero hidden-count leakage. Report measured uncertainty and failure of any Weber-style pattern plainly |
| F3 | 200 held-out learner tasks with valid action traces, plus 100 shuffled/incomplete/body-mismatch controls. Demonstration versus no-demonstration and shuffled-demonstration arms, same learner model/trial budget | ≥20-point observed own-trial success gain over no-demo, corrected p<.01; zero unverified adoption, unauthorized action or false own grounding; negative controls rejected or explicitly unresolved |
| B2 | 200 paired task-stream seeds with learning→idle→interference→delayed test. Full staged sleep versus P1 replay-only, matched-compute awake rehearsal, and no-offline-work. Same evidence exposure and total compute; 100 foreground interruption streams | ≥10-point delayed retention gain over replay-only, corrected p<.01, new-task performance loss ≤2 points; zero foreground action starvation, duplicate debit or ungrounded consolidation. Report comparisons with rehearsal and no-offline arms, memory bytes/nodes and rebuild cost |

Register scene construction, area/density/position controls, ratio-bin allocation and uncertainty intervals before drawing. Do not create a Weber curve by sampling answers from a prescribed function. The exact-count oracle remains outside agent inputs. Retention is verified later task performance, with original observations protected consistently across arms; support_count is secondary. If matched compute consumes fewer stage opportunities, record that exposure and do not claim equal work from equal clock duration.

### P6.H1 — Freeze the Phase 6 evaluation machinery

- **ID:** P6.H1
- **Tier:** T1
- **Goal:** Freeze the Phase 6 evaluation machinery.
- **Read first:** `COGNITION_BUILD_P6_PREREG.md`; `evaluation/substrate_capability/cognition_p5_heldout_v1.py` (P5); `evaluation/substrate_capability/cognition_p5_analysis_v1.py` (P5).
- **Touch:** new `evaluation/substrate_capability/cognition_p6_heldout_v1.py`; new `evaluation/substrate_capability/cognition_p6_analysis_v1.py`; `COGNITION_BUILD_P6_PREREG.md`.
- **Pattern to copy:** P5 paired worlds and P1 idle/foreground stream fixtures.
- **Steps:** 1. Implement seeded percept scenes, learner worlds and retention streams with external scoring. 2. Freeze 64-epoch task bounds, 256-epoch retention streams, compute matching and bootstrap ratio/scale tests in the preregistration. 3. Include development self-checks for leakage, zero/negative effect and interrupted stages; commit preregistration alone before draws.
- **Guard:** evaluation only.
- **Acceptance:** all three item protocols and negative controls frozen; analysis cannot infer success from node counts or replay frequency.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_numerosity_migrated.py tests/test_imitation_migrated.py tests/test_sleep_regime_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** using test answers as percepts or program targets.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

The H1 runner and analysis must implement `--self-check` for development-only checks. After H3 profile integration, run these checks before committing the preregistration; after that standalone commit, set `COGNITION_PREREG_HASH` to its full hash and run the registered draw:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p6_heldout_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p6_analysis_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p6_heldout_v1.py "$COGNITION_PREREG_HASH" 0 200
```

The runner writes `evaluation/reports/cognition_p6_heldout_v1_<hash8>_d0-200.json`; invoke `cognition_p6_analysis_v1.py` with that exact report path. It contains every registered subfamily, including separate ratio-bin draws where specified. Record the expanded commands and hashes in results. A self-check never uses registered held-out draw indices.

### P6.H2 — Run and report Phase 6 capability and retention results

- **ID:** P6.H2
- **Tier:** T1
- **Goal:** Run and report Phase 6 capability and retention results.
- **Read first:** `COGNITION_BUILD_P6_PREREG.md`; `evaluation/substrate_capability/cognition_p6_heldout_v1.py`; `evaluation/substrate_capability/cognition_p6_analysis_v1.py`.
- **Touch:** new `COGNITION_BUILD_P6_RESULTS.md`.
- **Pattern to copy:** P3 negative-result reporting and P5 claim boundaries.
- **Steps:** 1. Run `<prereg_hash> 0 200`, including fixed ratio bins and control subfamilies. 2. Analyze paired performance, cost, scale effects and all invariants. 3. Report each arm, original exposure, unsupported inputs and failures; retain generated reports outside git.
- **Guard:** frozen evaluation only.
- **Acceptance:** D7/F3/B2 each receive explicit decisions; retention and own-trial success are observed outcomes; human/beyond-human claims remain separate Track I work.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_numerosity_migrated.py tests/test_imitation_migrated.py tests/test_sleep_regime_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** treating predefined capacity or programmed work curves as human-level evidence.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P6.H3 — Integrate the complete guarded cognition profile before evaluation freeze

- **ID:** P6.H3
- **Tier:** T2
- **Goal:** Integrate the complete guarded cognition profile before evaluation freeze.
- **Read first:** `substrate/boot_profiles.py:769-796`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `COGNITION_BUILD_P6_PREREG.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P5 profile integration and P1 idle cooldown assertions.
- **Steps:** 1. Add mechanism-tested seeds to cognition-on and test perceive → recall → demonstration candidate → own verification → authorized trial → receipt → offline consolidation → delayed recall. 2. Interrupt offline work with foreground input and verify no lost action or duplicate stage. 3. Run full phase gate, engine provenance and boot/memory comparisons.
- **Guard:** cognition-on only; default/conversation isolation retained.
- **Acceptance:** `test_p6_end_to_end_observed_learning`, `test_p6_foreground_interrupt_and_resume`, `test_p6_default_and_conversation_isolation`; no new gate failures.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py tests/test_sleep_regime_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming completion of Track I from finishing P6.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.


### P6.H4 — Close Phase 6 documentation against actual evidence

- **ID:** P6.H4
- **Tier:** T3
- **Goal:** Close Phase 6 documentation against actual evidence.
- **Read first:** `COGNITION_BUILD_P6_RESULTS.md`; `COGNITION_BUILD_PLAN_20261010.md:1-25`; `COGNITION_CAPABILITY_ASSESSMENT_20261010.md:59-160`.
- **Touch:** `COGNITION_BUILD_PLAN_20261010.md`; `COGNITION_CAPABILITY_ASSESSMENT_20261010.md`; `COGNITION_BUILD_P6_RESULTS.md`.
- **Pattern to copy:** P3 parent status and assessment rows with explicit scope.
- **Steps:** 1. Update each delivered item with mechanism, held-out outcome, supported input class and commit hashes. 2. Retain failed hypotheses and inherited gate exceptions. 3. Assign remaining limitations and downstream prerequisite decisions; mark phase executed only after its implementation and reporting obligations are complete.
- **Guard:** documentation only.
- **Acceptance:** all original work items and carryovers have evidence-scoped status; no future task is described as passed; all links resolve to completed artifacts.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** promoting a mechanism fixture to a human capability claim; erasing null results.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

## Exit and remaining research

All three faculties need implemented mechanisms, registered held-out outcomes, bounded resource use and no new baseline regressions. Update the parent plan and capability assessment with per-item maturity and evidence scope. Unsuccessful transfer, unsupported irregular streams, experimental quadratic inference, broader SCM identification, arbitrary-angle imagery, open-world demonstration interpretation and human baselines remain named limits until separately evaluated. Track I I0–I7 remains its own gated program; completing P6 supplies interfaces, not evidence that process understanding or invention exceeds human capability.
