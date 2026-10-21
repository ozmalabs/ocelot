# Cognition build plan (2026-10-10)

Source audit: `COGNITION_CAPABILITY_ASSESSMENT_20261010.md` (rev 2). This is the overarching plan: phases, sections and work items. In the next step a frontier model breaks each work item into tasks using the contract in §3. A lower-tier or local model then executes each task. Ordering puts wiring and quick wins first: seed-only changes that connect machinery which already exists. New Rust primitives come later, and new faculties last.

## Detailed phase plans

Each detailed plan breaks its phase into tasks using the §3 template, records the findings that changed this plan, and supersedes this document's phase table wherever the two differ.

| Phase | Detailed plan | Status |
|---|---|---|
| 0 — Baseline and guardrails | [`COGNITION_BUILD_P0_BASELINE_PLAN.md`](COGNITION_BUILD_P0_BASELINE_PLAN.md) | Executed (`d83fa140`); baseline in `COGNITION_BUILD_BASELINE.md` |
| 1 — Wiring and quick wins | [`COGNITION_BUILD_P1_WIRING_PLAN.md`](COGNITION_BUILD_P1_WIRING_PLAN.md) | Executed (`5b52a38b`). Results in `COGNITION_BUILD_P1_RESULTS.md`; these are mechanism tests on fixtures, not capability evidence |
| 2 — Graded primitives | [`COGNITION_BUILD_P2_GRADED_PRIMITIVES_PLAN.md`](COGNITION_BUILD_P2_GRADED_PRIMITIVES_PLAN.md) | Executed (`1d5e63f9`); results recorded during P3 in [`COGNITION_BUILD_P2_RESULTS.md`](COGNITION_BUILD_P2_RESULTS.md) |
| 3 — Extended-thinking executor | [`COGNITION_BUILD_P3_EXTENDED_THINKING_PLAN.md`](COGNITION_BUILD_P3_EXTENDED_THINKING_PLAN.md) | Executed (`32143620`; pre-registration `eb34efb3`); H1/H2/H3/H5 pass, H4 partial (Family-A cache threshold fails); TimeInfer deferred to Track I or P4 |
| 4–6 | Not yet detailed; see §4 below | Detail each phase after the previous phase's results doc is written |
| **Track I — Process understanding and invention** | [`COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md`](COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md) | Runs in parallel with P3–P6. Its levels L1–L7 run from understanding and invention up to measurable beyond-human criteria. I0 (the evaluation battery and a `ProcessSchema` decision shared with P3) comes first |

### Amendments from detailing (2026-10-10)

These were found while detailing Phases 0–2. They override the §4 tables below.

- **P1.A1 is re-scoped.**
  - `program_synthesis` is a code-domain ladder: it is entered from a request Message, carries float values and is driven from Python.
  - `capability_collapse` is integer-only and domain-neutral.
  - So the bridge does not call code synthesis. Instead it mints a graph-native `CapabilitySynthesisRequest`, files it as a SelfConcern, and re-arms collapse when any producer supplies a higher-order program.
- **P1.A2 consumes only the Impasse→CapabilityAxis `needs_decomposition` edge.**
  - It partitions the axis by its `requires_key` CapKeys and never clones the parent axis.
  - The repair-side `Fault.needs_decomposition` attribute is already acted on, so the lint allowlists it.
  - `impasse_escalation` is frozen core, so the consumer is a new seed.
- **P1.A3 is dropped from Phase 1.**
  - A counterfactual experiment needs a concrete SeedDelta, and a zero-coverage impasse has none to offer.
  - The existing HumanImpasse is the honest response.
  - The item returns in P3 under relax/re-admit.
- **P1.C1 is dropped.** `obs_established` is `1 - obs_unassessable` by construction, and the learner already reads `obs_unassessable`. The assessment claim that compressed and mastered items look the same was outdated, and is corrected there.
- **P1.H7 gains a repair.** `goal_derivation`'s dependency closure is broken: `llvm_ir_vocabulary` has no seed file.
- **P1.H8 must boot through `WorldAdapter(seeds=…)`.**
  - `load_all_seeds` skips `self_load_only` seeds even when they are selected.
  - The opt-in parameter nodes are supplied by a new `cognition_on_params` seed.
- **P2.C1 drops the `SoftExclude` Term.** Soft exclusion is composed from the new `SoftWeights` Term instead.
- **P2.C2 is now a decision, defaulting to defer.** `ParetoDominates` is integer-only by explicit contract, and two tests pin that.
- **P2.C3 adds tolerance metadata alongside existing attributes.**
  - Most tolerances are already graph attributes on policy nodes. The plan describes them with metadata nodes (`Tolerance -governs_policy->`) and leaves the consuming rules unchanged.
  - Only four inline literals are migrated.
- **P2.C4 starts with a pathology test, because none exists.**
- **P2.A5: `SystemTwoEscalation.budget` is written but never read.** The budget therefore gates the minting of requests, and engine-level enforcement is a P3 question.
- **Rule 4 is relaxed.** The other author's engine and WASM work was committed (`8e82a211`, `5fb07d4f`). Rust tasks still check `git status --short runners/dsl` first.

### Amendments from detailing Phase 3

These override the §4 Phase 3 table. Details and evidence are in the P3 plan.

- **P3.A6 relax targets are replaced.**
  - `settle_tolerance` is a depth gate: raising it means thinking less.
  - `conflict_margin` and `minimum_confidence` are commit-permissiveness knobs. Relaxing them is the motivated-relaxation pathology, so P3 locks them out by construction.
  - `shape_match_tolerance` has no exact verifier.
  - `basin_threshold` would need a contract for re-opening a frozen seed, so it is deferred.
  - The two targets are the DimInfer grain ladder (`agent.dim_grains` `[0]→[0,1]→[0,1,2]`) and the GenInfer rung (`agent.gen_infer_enabled` 0→1). Both have exact verifiers and existing fixtures.
- **There is no generic "relax any Tolerance" rule.** `set_attr` cannot take an attribute name from data, so P3 uses one rule family per ladder, with the rungs held as graph data.
- **Re-admission is a targeted re-decode, not a `pruned_at` record.** It sets `decoded_epoch = codebook_epoch - 1` so that `sd_redecode` re-arms. The gen ladder also clears `gen_checked`/`gen_explained`. No change to `motor_decision_collapse` or the bigville core.
- **P3 is the first producer of `thinking_budget`'s generic pending-request contract.**
- **P3.A7 cache:** an `ExtendedThinkingCacheEntry` for the grain ladder. For the GenInfer rung, the minted `genlin_*` generator is itself the cache.
- **P3.D1 is re-scoped** to a readout seed, `inference_ladder_record`. The quadratic rung is an optional decision task. The TimeInfer/order-N rung is **deferred to Track I or P4**, because Observations carry no frames.
- **No Rust in P3.**
- **The P2 results doc was missing from the committed history.** P3.0.1 records the gate evidence in `COGNITION_BUILD_P2_RESULTS.md`.
- **Time inference remains deferred to Track I / P4.** P3.D1.4 records that the current Observation schema has a single signature and cannot carry the `motion_seq` frames required by TimeInfer.

## 1. Ground rules (apply to every task)

1. **The graph decides; Python is mechanical** (`CLAUDE.md` "Architecture rule"). A decision is a seed Rule. A missing primitive is a Rust Term in `runners/dsl/src/term.rs`, exposed via `py.rs`. Python may only ingest and emit.
2. **Byte-identical by default until Phase 1.8.** New behaviour is guarded on an opt-in policy node (the `HeldXParams.enabled` / `game.x_on` idiom). An unguarded change to a CORE seed needs a phase-gate decision.
3. **Seeds with a generator are edited through the generator.** Edit the script, then regenerate the JSON, so the two never diverge. Current generators: `capability_collapse` ← `scripts/gen_capability_collapse_seed.py`; `repair_escalation` ← `scripts/gen_repair_escalation_seed.py`; aperture minting ← `scripts/gen_aperture_minting_seed.py`. For a large new rule set, write a new `scripts/gen_<seed>_seed.py`. Never put one in `tools/`, which is never committed.
4. **Do not collide with uncommitted engine work.** Before any Rust task, run `git status --short runners/dsl runners/wasm`. If someone else's changes are dirty there, work in a git worktree or wait, and never stage their files. The 2026-10-10 engine/WASM work is now committed (`8e82a211`, `5fb07d4f`). Build only through `scripts/engine_build.sh`; never `cp` the `.so`. Run Rust tests with `scripts/engine_cargo_test.sh`.
5. **Verification for every task:** the task's own test, plus the regression gate for its phase (§5). `tests/test_frozen_core_invariant.py` has 3 known baseline failures, so the gate is "no new failures", not "all pass".
6. **Hygiene.** Stage specific files only. No `git stash` or `git reset`. Set `OZMA_SEED_PERSIST_DISABLED=1` for test runs. Never commit `papers/`, `tools/`, `evaluation/reports/`, `evaluation/labels/` or `docs/experiments/qualia-visualization-development-plan.md`. Check free disk space before a Rust build: the disk filled on 2026-10-10.
7. **Claims need evidence.** A capability counts as done when it passes a test, and when a pre-registered evaluation exists for that phase, it must also pass that. Results docs report failures plainly.

## 2. Sections (workstreams)

| Section | Scope | Audit refs |
|---|---|---|
| **A. Escalation & extended thinking** | Orphaned requests, impasse → imagination, ThinkingBudget, relax/widen/re-admit executor, settle-back | §5, §6.1 |
| **B. Memory & consolidation** | MemoryCycle producer, sleep/consolidation scheduler, decay tiers on by default | §4 memory/replay rows, §6.7 |
| **C. Admissibility & aperture** | Soft Γ, tolerance nodes, real-valued Pareto, graded relax, unified aperture, `obs_established` | §3, §6.2–6.3 |
| **D. Representation & inference** | Qualia cache and recall index, graph-native Shape minting, DimInfer → GenInfer → TimeInfer ladder | §6.4, §6.6 |
| **E. Manifold, world model & planning** | Manifold projector and refinement, native ThoughtManifold, multi-step planner over GWM, SCM | §6.5, §6.8 |
| **F. Social & language** | ToM unification, recursive ToM, imitation | §4 ToM/imitation rows |
| **G. Affect & control** | Reappraisal, response inhibition, dual-process status | §4 executive/emotion rows |
| **H. Integration & evaluation** | Cognition-on profile, orphan-signal lint, coverage gaps, pre-registered phase evaluations | §6.7, §7 |
| **I. Process understanding & invention** | Process schema and effect fingerprints; invention algebra; invariant walls; lifting and library learning; lifted induction and experiment design; explain-and-rebuild; goal-directed and representation invention; social acquisition; meta-invention. Gated by the Process Mastery Battery against human baselines | Track I doc |

## 3. How to break work items into tasks (contract for the frontier model)

Each work item in §4 becomes 1–8 tasks. Every task must be self-contained, so that a model with no conversation history can execute it from the task text alone.

**Task template:**

```
ID:            <phase>.<item>.<n>   e.g. P1.A1.2
Tier:          T1 frontier | T2 mid | T3 local
Goal:          one sentence, observable outcome
Read first:    exact files + line ranges (≤ 5 files)
Touch:         exact files to create/edit (≤ 3; generator + regenerated JSON count as 1)
Pattern to copy: an existing rule/Term/test of the same shape (file:line)
Steps:         numbered, mechanical
Guard:         the opt-in node/attr that keeps default boot byte-identical (or "n/a")
Acceptance:    test file::test names that must pass; written BEFORE the change where possible
Verify cmd:    exact command(s), e.g. OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_x.py -q
Non-goals:     what NOT to change
Done when:     acceptance green + phase gate shows no new failures
```

**Sizing and tiering:**
- **T3 (local):** one seed rule or a small rule family copied from a named pattern; tests from a named pattern; generator-script edits with a clear diff; docs. Aim for a diff of 300 lines or less. Long Term-tree JSON is fine as long as a pattern exists to copy.
- **T2 (mid):** a Rust Term or evaluator change against a written spec; multi-file wiring across seed, PyO3 and test; seed changes that touch CORE.
- **T1 (frontier):** Term semantics and specs; pre-registrations and evaluation design; results analysis; any task whose "Pattern to copy" cannot be named.
- If a task cannot name a pattern to copy, it is not ready for T3. Split off a T1 spec task first.

**Ordering within a work item:**
1. A spec or test task (T1/T2).
2. Implementation tasks (T3/T2).
3. A wiring or integration task.
4. A doc update to the assessment (T3).

## 4. Phases

Every phase ends with a gate (§5). A phase is not started until the previous gate is green, except that Phase 2's Rust spec tasks may run in parallel with Phase 1.

### Phase 0 — Baseline and guardrails (no behaviour change)

| ID | Sec | Work item | Touch points | Tier mix | Done when |
|---|---|---|---|---|---|
| P0.H1 | H | **Pin the regression baseline.** Record pass/fail of `pytest -k migrated`, `tests/test_frozen_core_invariant.py`, `tests/test_cognitive_architecture_integration_migrated.py` and `scripts/engine_cargo_test.sh` at HEAD | new `docs/research/engine_substrate/COGNITION_BUILD_BASELINE.md` | T3 | Baseline committed; later gates diff against it |
| P0.H2 | H | **Orphan-signal lint.** A mechanical script listing every edge type or attr that a seed rule *writes* but no rule, Term or Rust module *reads*. It must flag `synthesis_requested` and `needs_decomposition` and must not flag `needs_tool` | new `scripts/lint_orphan_signals.py`, test `tests/test_lint_orphan_signals.py` | T2 spec, T3 impl | Lint output committed as a checklist; known cases asserted in the test |
| P0.H3 | H | **Boot-status report.** A script printing, per seed: C / Prof / Bulk / SLO, guard attribute, rule and production counts | new `scripts/report_seed_boot_status.py` | T3 | Output matches the audit's §4 table; discrepancies fed back into the audit |
| P0.G1 | G | **Reconcile dual_process status.** `cognitive_cycle.rs:557` says core; `boot_core.py:33` says optional. Write the decision (core or optional) and fix the comment or the list. Promoting it to core changes the default cycle plan, so it needs the full gate | `substrate/boot_core.py` or the comment only (Rust comment edit waits for rule 4) | T1 decision, T3 edit | Decision recorded; code and comment agree |

### Phase 1 — Wiring and quick wins (seed-only, no new Rust)

Goal: the parts that already exist start talking to each other. Every item is guarded off by default until P1.H8 turns on the combined profile.

| ID | Sec | Work item | Touch points | Tier mix | Done when |
|---|---|---|---|---|---|
| P1.A1 | A | **Consume `synthesis_requested`.** When `capability_collapse` sets `state.synthesis_requested=1` (no higher program), mint a SystemTwoEscalation that recruits the program-synthesis ladder (`ps_propose` → `SynthEnumerate` → `ps_accept`) for the stuck channel. On `ps_accept`, reset the flag and hand the new program back to `cc_compile_channel_capability_boundary` | `scripts/gen_capability_collapse_seed.py` (or a new bridge seed `seeds/collapse_synthesis_bridge.json` + generator), the `program_synthesis` seed, new test | T1 spec, T3 rules, T2 wiring | Test: a channel with no higher program ends with a synthesised program bound, or with an honest `synthesis_exhausted` status. The flag is never left at 1 with no consumer |
| P1.A2 | A | **Consume `needs_decomposition`.** `impasse_escalation.order3_reframe` adds `mi -needs_decomposition-> ax`, and `repair_escalation` sets `f.needs_decomposition`. Route both into the existing decomposers: `arc_decompose`-style child-goal minting for CapabilityAxis, and the `cognitive_supervision` goal tree. No duplicate axes (see the dedup note in the `order3_reframe` comment) | new `seeds/decomposition_consumer.json` + generator; tests | T1 spec, T3 rules | Test: an order-3 impasse produces ≥ 1 distinct child axis or sub-goal, and the parent's shortfall reflects child progress |
| P1.A3 | A | **Route self-extension failure.** When `self_extension.compose_zero_coverage_impasse` finds no held primitives that cover the need, mint a `counterfactual_requested` experiment (`counterfactual_experiment.json`) instead of stopping | bridge rule in the A1/A2 seed or `self_extension.json`; test | T3 | Test: a zero-coverage impasse yields a counterfactual experiment node with non-oracular provenance |
| P1.A4 | A | **Impasse → imagination.** Let impasse, prediction-error and low-confidence escalations (the dual_process triggers) mint a `SimulationRequest` for `generative_world_model`, as `default_mode_request_content_bearing_simulation` already does when idle. Feed the best imagined branch back as a *candidate*, not a grounded fact | new `seeds/impasse_simulation_bridge.json`; tests modelled on `test_default_mode_core_migrated.py` | T1 spec, T3 rules | Test: an impasse with available world-model actions produces a completed rollout and a candidate edge on the impasse; grounded beliefs are unchanged |
| P1.B1 | B | **MemoryCycle producer (sleep v0).** A rule that mints `agent -has_memory_cycle-> MemoryCycle{status:pending, mode:offline}` when `NetworkModeState` has been idle past a threshold and load is low, with a cooldown. This drives `episodic_prioritize_one_replay_per_cycle` in live runs | new `seeds/consolidation_scheduler.json` (depends on EWM and DMN); tests | T3 | Test: a long idle stream yields bounded offline replays and semantic support, with no replay under load |
| P1.C1 | C | **Read `obs_established`.** `learning_aperture_gate.lag_gate_observation` writes it and nothing reads it. Make the learner's mastery/credit rule distinguish "compressed (held==obs because unresolved)" from "mastered (resolved and matched)" | `seeds/learning_aperture_gate.json` (or its consumer seed); test | T3 | Test: an unresolved dimension never earns mastery credit |
| P1.H7 | H | **Coverage quick wins.** Tests for `goal_derivation`, `compositional_plan`, `modality_tom` and `generative_skeptic` (currently 0 tests). Behaviour tests only: no semantic changes | new test files | T3 | Each seed has at least one behaviour test |
| P1.H8 | H | **Cognition-on profile + integration test.** A named boot profile: CORE + dual_process + EWM decay tiers (`staleness_decay`, `demotion_hierarchy`) + `core_emotions` / `mood_r1` / `arousal_window_coreg` + `cognitive_supervision` + the P1 bridges. Add one integration test that runs a scripted episode through impasse → simulation → candidate → replay → consolidation | `substrate/boot_profiles.py` (new profile constant + loader; no change to the conversation profile), `tests/test_cognition_profile_integration.py` | T1 scenario, T2 impl | Integration test green; boot time recorded; conversation profile unchanged |

**Phase 1 pre-registration (T1):** before P1.H8 lands, pre-register "wired vs unwired" on an existing task family (capability-collapse channels or prediction-world levels). The question is whether the bridges convert impasses into resolved capabilities at a higher rate than the unwired baseline. Report it honestly either way.

### Phase 2 — Graded primitives (Rust + seed)

The extended-thinking executor needs something graded to relax. Rust tasks follow rule 4. Each Term gets a T1 spec task first: semantics, edge cases, determinism, cost.

| ID | Sec | Work item | Touch points | Tier mix | Done when |
|---|---|---|---|---|---|
| P2.C1 | C | **Softmax / SoftSelect Term.** A temperature-parameterised distribution over a source with a value Term (deterministic: returns weights; selection stays Argmax or ArgminUnique over the weights). Also a `SoftExclude` that down-weights instead of removing | `term.rs`, `term_variants.rs`, `py.rs`, Rust unit tests, a Python test | T1 spec, T2 impl | Cargo and Python tests green; provenance test passes after `engine_build.sh` |
| P2.C2 | C | **Real-valued `ParetoDominates`** (currently integer-only), with an epsilon | `term.rs`; tests | T2 | Integer behaviour byte-identical; float cases covered |
| P2.C3 | C | **Tolerance nodes.** Promote scattered literals (`SHAPE_MATCH_TOL`, `settle_tolerance` in `motor_decision_collapse`, DimInfer grain defaults, manifold tube width) to `Tolerance{name, value, min, max, step}` graph nodes read by the rules that use them. No value changes | the affected seeds + generators; tests asserting equal behaviour | T1 inventory, T3 per-seed migration | All migrated rules read Tolerance nodes; regression gate unchanged |
| P2.C4 | C | **Graded aperture relax.** Replace binary `af_relax_chosen` (`seeds/aperture_frame.json`) with a stepped relax over a Tolerance/aperture node, with an exit condition that prevents motivated inattention: relaxing must be justified by a VOI or evidence term, not by residual alone (see `APERTURE_PATHOLOGIES.md`) | `aperture_frame.json`; `test_aperture_frame_migrated.py` | T1 spec, T3 rules | Pathology regression test: no relax-to-avoid-residual loop |
| P2.A5 | A | **ThinkingBudget node.** A shared anytime budget, funded by rules from evidence (`arousal_horizon`, a VOI estimate, stakes) and debited by SystemTwo areas, GWM rollouts and synthesis. Requests carry `budget_ref` | new `seeds/thinking_budget.json`; edits to the P1 bridges; tests | T1 spec, T3 rules | Test: total spend ≤ budget; exhaustion yields an honest `budget_exhausted` status |

### Phase 3 — Extended-thinking executor

> Superseded by [`COGNITION_BUILD_P3_EXTENDED_THINKING_PLAN.md`](COGNITION_BUILD_P3_EXTENDED_THINKING_PLAN.md) and the Phase 3 amendments above. The table is kept as the original intent.

| ID | Sec | Work item | Touch points | Tier mix | Done when |
|---|---|---|---|---|---|
| P3.A6 | A | **Relax / widen / re-admit loop.** On impasse with budget left: step one Tolerance or aperture outward (P2.C3/C4), re-admit candidates previously pruned at the tighter setting (needs a `pruned_at` record on candidates), re-verify with the existing exact checkers, and repeat until a hit, the bound or budget exhaustion | new `seeds/extended_thinking.json` + generator; pruning record in `motor_decision_collapse` and the bigville core | T1 spec, T3 rules, T2 for pruning records | Test: a task unsolvable at the default tolerance is solved after N relax steps, and the loop stops at the bound |
| P3.A7 | A | **Settle back and cache.** After a hit, restore tolerances, and cache the winner as a codebook mint (generator, shape or program) with provenance `extended_thinking`, so the next encounter is solved at the default tolerance | the A6 seed; minting rules (`sd_mint_*`, `ps_accept`) | T3 | Test: the second encounter solves without relaxing (fewer steps, no budget spend) |
| P3.D1 | D | **Inference ladder as rungs.** DimInfer failure → GenInfer (linear → quadratic → coupled, flag-gated) → TimeInfer/order-N, as escalation rungs that the A6 loop climbs, with an Occam ordering | `shape_decode_loop` / `meta_shape_growth` rules; GenInfer flags; tests | T1 spec, T2/T3 | Test: a quadratic-only task climbs to the quadratic rung and caches it |
| P3.H9 | H | **Pre-registered evaluation.** Extended thinking on vs off on held-out tasks: accuracy, budget spend, and second-encounter speed-up | `evaluation/substrate_capability/extended_thinking_heldout_v1.py`, pre-reg and results docs | T1 | Results doc committed |

### Phase 4 — Representation: qualia cache, unified aperture, generative manifold

| ID | Sec | Work item | Touch points | Tier mix | Done when |
|---|---|---|---|---|---|
| P4.D2 | D | **Graph-native Shape minting.** Move `mint_shape` / `aperture_signature` (`tests/capability/number_qualia/runners/number_runner.py`) into seed rules using `MetaShapeMint` / `msg_mint_shape`. Python keeps only ingest | `meta_shape_growth` or a new `seeds/qualia_shape_mint.json`; tests | T1 spec, T3 | Shapes are minted with no Python decision; existing number_qualia tracks reproduce |
| P4.D3 | D | **One signature space.** Map QualiaDimension axes (`qualia_space.json`), Shape sig_k and valence into a single signature schema. Lexical qualia stays parked | schema doc + seed nodes | T1 | Schema doc; all three stores readable through it |
| P4.D4 | D | **Similarity recall Term.** `RecallNearest(signature, k, tol)` over `memory.rs` ShapeIndex, so the codebook and analogy can look up before they generate and test | `term.rs`, `memory.rs`, `py.rs`; tests | T1 spec, T2 impl | Recall-before-generate cuts candidates on a repeat task |
| P4.D5 | D | **Cross-domain recall evaluation** (pre-registered): a quale minted in domain X shortens solving in domain Y | evaluation harness + docs | T1 | Results doc, honest either way |
| P4.C5 | C | **Unified aperture.** Recast the domain apertures (reading, dwell, finite-difference k, QualiaAperture, ShapeDecode scope, manifold mask) as Observer-frame instances. Aperture chosen by evidence or VOI, reusing the prediction-world judge's salience-selected aperture as the pattern | `observer_aperture.json`, `aperture_frame.json`, each domain seed; tests | T1 spec, T3 per-domain | Each domain aperture readable as an Observer frame; `stress_aperture.json` no longer the sole source for the manifold mask |
| P4.E1 | E | **Manifold projector.** Generate candidate trajectories for `FutureManifoldProjection` from GWM rollouts instead of only from supplied moves; refinement driven by the A6 loop (`refinement_count` > 0); a manifold cache that writes into qualia (P4.D2) | `future_manifold.rs`, the GWM seed, tests | T1 spec, T2 | Projection with no supplied moves produces a feasible set; refinement is observed |
| P4.E2 | E | **Collapse manifold implementations; native ThoughtManifold.** One Rust generic path; `regulated_train_of_thought.py` reduced to ingest and emit | `future_manifold.rs`, `motor_compose`, Python modules | T1 plan, T2 | Python decision code removed; behaviour tests green |

### Phase 5 — Depth inside existing faculties

Each item is independent. Start one with a T1 spec and a pre-registered test.

| ID | Sec | Work item | Starting point |
|---|---|---|---|
| P5.F1 | F | Unify the four ToM systems (character_tom, psychology, interlocutor_model, hate_attribution) through `tom_meta_shape` | `TOM_SYSTEM_UNIFICATION_RESULTS.md` (deferred part) |
| P5.F2 | F | Recursive ToM: nested `belief_world` of a `belief_world` (A believes B believes X); second-order false-belief tests | `domains/character_tom.py` `_nested_entity`; move the decision into seed rules |
| P5.G2 | G | Reappraisal: a rule family that re-frames the appraisal *input* (alternative frame) and re-runs `core_emotions`, distinct from arousal pull | `core_emotions.json`, `arousal_window_coreg.json` |
| P5.G3 | G | Response inhibition: a stop/withhold primitive on committed System-1 actions under conflict, with a go/no-go test | `dual_process_core` refusal mark, `reflex_core` |
| P5.E3 | E | SCM over CAN and CausalFacts: do-operator as graph surgery on a detached copy (reuse `imagination.py` snapshot/cut), with a backdoor adjustment test | `remote_causal`, `can_ops.rs`, `imagination.py` |
| P5.E4 | E | Multi-step planner: bounded search over GWM rollouts toward a goal, replacing one-step `goal_derivation` Argmax; tests for `goal_derivation` and `compositional_plan` already exist from P1.H7 | `generative_world_model.json`, `goal_derivation.json`, `ls20_planning` results as baseline |
| P5.D6 | D | Analog rotation and imagery buffer: angle-parameterised generator with cost proportional to angle (Shepard linear-time signature), held in a detached buffer | `shape_decode_loop` generators, `imagination.py` |

### Phase 6 — Absent faculties

| ID | Sec | Work item | Notes |
|---|---|---|---|
| P6.D7 | D | Numerosity: subitizing (exact, ≤ 4, flat cost) and an approximate number system (log-scale, Weber-ratio discrimination) as perception rules over `number_world` | Needs a T1 spec of the representation; may need a log-magnitude Term |
| P6.F3 | F | Imitation from demonstration: observe another agent's action sequence → mint a candidate program → verify by own rollout (GWM) → adopt | Reuses program synthesis + GWM + ToM attribution |
| P6.B2 | B | Sleep regime v1: staged offline cycles (replay, consolidation, decay pass, default-mode recombination) scheduled by the P1.B1 producer, with measurable retention gains | Builds on P1.B1 + decay tiers |

## 5. Phase gates

| Gate | Required |
|---|---|
| Every task | Its acceptance tests; the task diff limited to its `Touch` list |
| End of P0 | Baseline doc committed; lint and boot-status scripts tested |
| End of P1 | All P1 tests; `pytest -k migrated` no new failures vs baseline; frozen-core no new failures; default boot byte-identical except through the cognition-on profile; P1 pre-reg results doc |
| End of P2 | Above, plus `scripts/engine_cargo_test.sh` green, `tests/test_engine_provenance_migrated.py` green after `engine_build.sh`; tolerance migration behaviour-identical |
| End of P3 | Above, plus the P3.H9 results doc |
| End of P4–P6 | Above, plus each item's pre-registered result; the assessment doc updated to the new maturity labels |

## 6. Dependencies and parallelism

```
P0 ──► P1 (A1,A2,A3,A4,B1,C1,H7 in parallel) ──► P1.H8 ──► gate
        └─ P2 spec tasks (C1,C2,A5) may start here ─┐
P2 (C1,C2 Rust; C3,C4,A5 seed) ─────────────────────┴──► P3 (A6 ► A7; D1 needs A6) ──► P3.H9
P4: D2 ► D3 ► D4 ► D5 ;  C5 needs P2.C4 ;  E1 needs P1.A4 + P3.A6 ; E2 needs E1
P5 items independent (E4 benefits from E1; F2 after F1)
P6: D7 independent ; F3 needs P5.F1 ; B2 needs P1.B1
Track I: I0 ─► I1 ─► I2 ─► I3 ; I1 ─► I4 ; I3+I4 ─► I5 ─► I6 ─► I7
  coupling: I0.4 ProcessSchema decision shared with P3 (P3 as built uses its own RelaxLadder data, which I0.4 may later map onto ProcessSchema) ;
            P3.A6 consumes I5.2 targeted invention (as a later ladder, not in P3 scope) ; P3's deferred time rung moves to I4.2 or P4 ;
            I2.2/I3.2 run in the P1.B1/P6.B2 offline cycle ; I4.3 supplies the VOI that P2.A5 funding lacks ;
            I5.3 needs P4.C5 ; I5.4 needs P4.D4 ; I6.2 extends P6.F3
```

## 7. Risks

- **Concurrent engine edits:** every Rust item is blocked by rule 4. Mitigation: seed-only work fills Phases 0–1, and Rust specs are written in parallel.
- **Behaviour drift in CORE seeds:** every new rule is guarded until P1.H8, and the gate checks byte-identity.
- **Motivated relaxation:** the A6 loop could relax tolerances to dodge residual, the same pathology as `af_relax_chosen`. P2.C4's VOI requirement and P3.A6's bound are mandatory, not optional.
- **Boot cost:** the cognition-on profile adds seeds, so boot time is recorded at P1.H8 and checked at each later gate.
- **Disk:** Rust builds need several GB free. Check `df -h /` before building.
- **Overclaiming:** each phase's pre-registration decides "done" for capability claims, not test greenness alone. Results on deterministic fixtures (such as Phase 1's 1.0 vs 0.0) show only that a mechanism exists. Track I's claims at and beyond human level require held-out instances and human baselines (Track I §0 and §6).
- **Self-modification (Track I L7):** a loop that authors new invention operators changes the agent's own machinery. It goes through `adoption_safety`, human-gated criterion proposals and the future-manifold commit boundary.
