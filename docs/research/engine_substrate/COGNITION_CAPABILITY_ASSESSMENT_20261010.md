# Cognition capability assessment of the substrate (2026-10-10, revision 2)

Purpose: lay out the shape of cognition the substrate already has, component by component, so that the missing parts become visible. For every component the same four questions are asked: what is its aperture, what is its admissibility, does it feed or read qualia, and can it think further (extended thinking)?

**Revision 2.** Revision 1 (`be59ad24`) listed eleven faculties as "absent" and three seeds as "empty stubs". A second audit found that eight of those faculties exist and that the three stubs are declarative knowledge seeds, not empty files. The first audit went wrong in two ways: it searched for lab-paradigm names (Stroop, subitizing, do-calculus, HTN), and it checked only `rules` arrays. The second audit counted rules and productions per seed, and checked `self_load_only`, opt-in guards and CORE_SEEDS membership. Section 4 is the corrected inventory, and sections 1, 3, 5 and 6 are revised to match. All claims come from reading code and seeds at `be59ad24`. No tests were run for this report.

Maturity scale:
- **C**: in CORE_SEEDS (`substrate/boot_core.py:20`), so loaded on every `boot_core()`.
- **Prof**: in the opt-in conversation production profile (`substrate/boot_profiles.py` `CONVERSATION_SEED_ANCHORS`).
- **Bulk**: loaded by the full-corpus `load_all_seeds`, not by core.
- **SLO**: `self_load_only`. Loaded on demand by a domain module and skipped by the bulk boot (`boot_all.py:100`).
- **Off**: rules are guarded on an opt-in node or attribute, so default behaviour is byte-identical.
- **Py**: Python only.
- **Decl**: concepts or head/body principles. `seed_loader.normalize_declarative` turns these into Concept/Principle nodes, not engine Rules.
- **∅**: absent.

## 1. Headline

The substrate covers most of the classical faculty map. It has executable graph rules for:
- working memory with capacity limits, interference and expiry;
- episodic replay and consolidation;
- forgetting, through decay tiers and budget eviction;
- generative world-model rollouts and default-mode prospection;
- detached imagination;
- dual-process arbitration with conflict escalation;
- interventional causal discovery;
- goal construction and decomposition;
- first-order theory of mind;
- language production;
- appraisal emotions, with arousal self-regulation and co-regulation.

Much of this is not on by default. Outside CORE, faculties are SLO, guarded Off, or loaded by a single profile. So the real gap is less whether a faculty exists than whether the faculties are wired together and switched on.

The structural weaknesses from revision 1 still hold, with Phase 1 and Phase 2 primitives now landed. They concern the *proposal* half of cognition, not missing faculties:
- **Soft admissibility and tolerance metadata now exist in the engine and graph (Phase 2), though no general relax loop drives them yet.** Rust now provides `SoftWeights` (`term.rs`, `SOFT_ADMISSIBILITY_RECIPES.md`), `tolerance_registry` (`seeds/tolerance_registry.json`) describes five policy tolerances (`motor_settle_tolerance`, `dual_process_conflict_margin_tolerance`, `dual_process_minimum_confidence_tolerance`, `salience_shape_match_tolerance`, `dim_infer_grain_tolerance`), and the inline tolerance literals in `residual_salience`, `shape_decode_loop`, and `number_runner.py` have been migrated to policy node attributes.
- **There is no general extended-thinking executor yet, though the Phase 1 bridges and Phase 2 `ThinkingBudget` now exist (opt-in).** `synthesis_requested` is consumed by `capability_synthesis_bridge` (SLO + Off, enabled in `boot_cognition_on()`), `Impasse -needs_decomposition-> CapabilityAxis` is consumed by `decomposition_consumer` (SLO + Off, enabled in `boot_cognition_on()`), `thinking_budget` (`seeds/thinking_budget.json`, enabled in `boot_cognition_on()`) provides a shared epoch-refilled `ThinkingBudget` (optionally funded from `ManifoldPolicy.future_manifold_projection_budget`) governing `impasse_simulation_bridge` and `consolidation_scheduler`, and `needs_tool` is consumed by `self_extension.json` (`Fault.needs_decomposition` from `repair_escalation` remains unconsumed). Deepening still does not re-admit options it pruned.
- **Graded aperture relax and questioning now close the motivated-inattention pathology in `aperture_frame`, while domain apertures remain separate.** `af_relax_chosen` now checks residual magnitude against `obs.ap_relax_tolerance` (default `1`), and `af_count_chosen_dwell` / `af_probe_project_*` / `af_question_drop_hiding_frame` probe at full non-chosen acuity after `obs.ap_question_after` generations and drop a chosen frame that hides an unresolved distinction (`APERTURE_PATHOLOGIES.md` §1 closed).
- **Qualia is not yet a cache.** There are three disjoint stores, minting happens in Python, and cross-domain recall has never been tested.
- **The Seldon/Thought manifold has no generator.** It selects among futures but has no projector, does no refinement and keeps no cache.

## 2. Component map (cognition core)

| # | Component | Where | Role | Maturity |
|---|---|---|---|---|
| 1 | Standard codebook | `ShapeSignature`/`MetaShape` (`shape_decode.rs:336 load_parts`); `DimensionGenerator` (`:682`); 5 seeded in `shape_decode_loop.json`; `meta_shape_growth.json` (10 rules) points the same Terms at MetaShape | Vocabulary of parts and generators | `shape_decode_loop` is Prof (via `composer_dispatch`); `meta_shape_growth` is Bulk; grows by minting |
| 2 | DimInfer | `eval_dim_infer` `shape_decode.rs:3031`; `sd_infer_dimension`, `msg_infer_dimension` | Finds the generator×k that explains `coord:*` dims | Prof (`sd_*`) / Bulk (`msg_*`) |
| 3 | GenInfer | `eval_gen_infer` `shape_decode.rs:3901` | Induces a new generator | Off (`gen_infer_enabled`, Cargo features) |
| 4 | TimeInfer / order-N | `time_axis.json`; `domains/order_n_concepts.py` | Temporal axes; finite differences | Bulk / Py |
| 5 | ShapeDecode / TransformDecode | `shape_decode.rs` | Perception front end | Bulk |
| 6 | Seldon manifold | `future_manifold.rs`; `FutureManifoldProjection/Selection` (`term.rs:3238`) | Selects reachable futures under a resolved-dims mask | Bulk; falls back to `motor_compose` |
| 7 | ThoughtManifold | `regulated_train_of_thought.py`, `conversation_deliberation.py` | Regulated deliberation | Py ("planning only") |
| 8 | Generative world model | `generative_world_model.json` (37 rules and productions) | Action-conditioned branching imagined rollouts with pruning; compares predictions with grounded outcomes | **C** |
| 9 | Salience / attention | `residual_salience.json`, `fovea_salience_bridge.json`, `salient_cache.json` | Decides what reaches the inferers | Bulk |
| 10 | Aperture | `observer_aperture.json`, `aperture_frame.json`, plus domain apertures | Resolution and scope of a read | Bulk, plus fragments |
| 11 | Admissibility Γ | `grammar.rs`; `substrate.rs admissible_moves` | Legal and weighted moves | Hard gates only |
| 12 | Qualia field | `qualia_space.json` (Decl), `lexical_qualia.json` (Prof, 2 productions, parked), Shape sig_0..7 + valence | Compressed, felt representation | Py mint / graph match |
| 13 | Metacognition | prediction-world `judge_robust`; `dual_process_core`; `cognitive_supervision`; `generative_skeptic` (Decl + Py) | Judge, arbitrate, supervise | Mixed (see §4) |

## 3. The matrix: aperture × admissibility × qualia × extended thinking

| Component | Aperture | Admissibility | Qualia | Extended thinking |
|---|---|---|---|---|
| Codebook | Partitioned by node type; no similarity index | Exact equality on recall | None: recall is generate-and-test | Grows only by minting; no "search wider" mode |
| DimInfer | `grain` requantization from `agent.dim_grains`, the only relaxation | Hard: equal relation counts, `max_dims`, composition ≤ 2 | None | Pass-2 Occam short-circuit; fixed depth of 2 |
| GenInfer | Data-derived bound B | Exact, plus an optional MDL witness that routes outliers to `sd_mdl_outliers` | None | Exhaustive O((2B+1)^4); no linear→quadratic→coupled ladder; coupled-quadratic transfer 0/10 |
| TimeInfer | Requires integer, exactly regular streams | Exact | None | None; order-N is Python only |
| ShapeDecode | Name scope (no measured benefit in live runs) | Exact `build_candidate` | Shape signatures feed the qualia match | Internal beam and budget, not exposed to the graph |
| Future manifold | `future_manifold_resolved_dims`, stipulated by `stress_aperture.json` | Hard tube; relaxation exists only in the Python twin | `shape_snapshot` capped at 7 dims; no cache | Budget from `arousal_horizon`; `refinement_count` is always 0; no projector |
| Generative world model | `horizon` and `maximum_branching` on SimulationRequest | `prune_terminal_*` rules | None | Bounded branching rollouts, the only graph-native tree search. Requested by default mode, by counterfactual experiments, and (opt-in via `impasse_simulation_bridge`) by `dual_process_core` `instinct_conflict` escalations |
| Salience | `fovea_resolve` ArgminUnique | Graph-weighted (the only such selector) | L1 match against Shape signatures (`valence_salience`) | None |
| Aperture (general) | `af_effective_aperture` Intersect meet | `af_relax_chosen` checks residual magnitude `>= obs.ap_relax_tolerance` (default 1) | None | Non-residual questioning trigger (`af_count_chosen_dwell` → `af_probe_project_*` → `af_question_drop_hiding_frame`) probes at non-chosen acuity after `obs.ap_question_after` generations and drops a chosen frame that hides a residual (`APERTURE_PATHOLOGIES.md` §1 closed). (Correction: `obs_established` is unread, but it is redundant with `obs_unassessable`, which the learner does read. Since `learning_progress_curiosity` v1.1.0, compressed and mastered items stay distinguishable.) |
| Γ | n/a | `SoftWeights` Term in Rust (`term.rs`) computes temperature-controlled exp weights (`τ <= 0` hard max); `ParetoDominates` is integer-only (by explicit contract in `cognitive_pareto`); five tolerances are registered in `tolerance_registry.json`, and inline tolerances in `residual_salience`, `shape_decode_loop`, and `number_runner.py` read policy attributes | None | No relax-to-find-more loop yet (Phase 3) |
| Qualia field | QualiaAperture k (Python) | `SaliencePolicy.shape_match_tolerance` (default `2.0`, registered in `tolerance_registry.json`) | Three disjoint stores | No cross-domain recall tested |
| Dual process | Admits SystemTwoTaskSet areas | Continuous System-2 weight; escalates on conflict, near-conflict and low confidence | None | Admits areas; with `impasse_simulation_bridge` (opt-in) proposes an `ImaginedCandidate` on `instinct_conflict` |
| Capability collapse / impasse | Pre-authored chain; orders 2–6 | Static | None | `synthesis_requested` is consumed (opt-in) by `capability_synthesis_bridge`; `Impasse -needs_decomposition-> CapabilityAxis` is consumed (opt-in) by `decomposition_consumer` (`Fault.needs_decomposition` attr remains unconsumed); `needs_tool` is consumed by `self_extension` (`compose_zero_coverage_impasse`, `compose_from_held_primitives`) |
| Program synthesis | Grammar | Test-based | None | A real propose→enumerate→accept ladder with a cache, but only for code |

## 4. Faculty inventory (corrected)

Each verdict states what exists and what is actually missing inside that faculty.

| Faculty | What exists (executable unless noted) | Boot status | Tests | Real gap |
|---|---|---|---|---|
| **Working memory capacity, interference, forgetting** | `episodic_working_memory_core`: `maximum_slots 4`, `slot_ttl_epochs 8`, five gates (input/update/maintain/output/clear), `working_memory_replace_cross_task_interference` (cross-task replacement of the lowest-priority slot), `working_memory_refuse_same_task_over_capacity`, `working_memory_expire_unmaintained_slot`. `staleness_decay` (integer half-life freshness), `demotion_hierarchy` (FRESH/GIST/LATENT tiers, latent items deleted), `can_decay_identity`. Rust `memory.rs`: `forget_over_budget` (evicts by keep-value per byte), `roll_disposable` (sensory ring buffer), `shuffle` (pages out cold clusters) | EWM is **C** and enabled; decay seeds are SLO + Off | `test_episodic_working_memory_migrated.py` 18; staleness 7; demotion 8; salient_cache 9 | Decay tiers are not on by default; WM capacity is a stipulated 4 |
| **Offline replay and consolidation** | `episodic_prioritize_one_replay_per_cycle` (wake and offline modes; priority = salience + 2·surprise + value + novelty decay); `episodic_replay_creates/updates_semantic_support` (episode→schema); `episodic_reconsolidate_after_retrieval`; Rust `consolidate` writes to disk and ShapeIndex; `default_mode_mint_episode_context` replays consolidated episodes when idle; `consolidation_scheduler` (SLO + Off, enabled in `boot_cognition_on()`) binds `NetworkModeState` as `has_memory_clock` and mints cooldown-paced offline `MemoryCycle` nodes during low-demand default-mode epochs | EWM is **C**; `consolidation_scheduler` is SLO + Off (`boot_cognition_on()`) | EWM offline-replay test; `test_default_mode_core_migrated.py` 8; `test_consolidation_scheduler_migrated.py` 6 | `consolidation_scheduler` is opt-in (off in default `WorldAdapter()` boot) |
| **Imagination / simulation** | `generative_world_model` (C) rollouts; `default_mode_request_content_bearing_simulation`; `impasse_simulation_bridge` (SLO + Off, enabled in `boot_cognition_on()`) triggers GWM counterfactual rollouts on `dual_process_core` `instinct_conflict` escalations and proposes `ImaginedCandidate`; `counterfactual_experiment`, which routes graph self-tests into detached imagination and keeps the results as non-oracular evidence; `composer_imagination_graph` (the ENGAGE decision is graph-authored); `imagination.py`, the mechanical snapshot/cut-grounding/run/diff/reground machinery (the graph decides when it runs) | GWM and DMN are **C**; `impasse_simulation_bridge` is SLO + Off; the others are Bulk; the `imagination` module is in the Prof runtime | `test_imagination.py` 12, `test_imagination_cognition.py` 13, trace retention 9, GWM 5, `test_impasse_simulation_bridge_migrated.py` 5 | `ImaginedCandidate` is proposed on `SystemTwoEscalation` (`status: "proposal"`), not yet arbitrated into `DualProcessContext` resolution |
| **Mental rotation / imagery** | Generators `rotation90`, reflections, `scale2`, `cycle4`, with DimInfer recognition under transformation; `latent:rotation90` is minted | Bulk | `test_dimension_inference_migrated.py` and others (~13 files) | Discrete generator inference only: no analog, angle-cost rotation and no pictorial imagery buffer |
| **Executive / cognitive control** | `dual_process_core` (20 rules / 17 productions): continuous System-2 weight, `escalate_instinct_conflict`, `escalate_near_conflict` (conflict monitoring), task-set recruitment (`SystemTwoTaskSet`), devaluation, extinction, reversal. Rust `CyclePlan::DualProcess`, `admit_system_two`. `adaptive_control_core` (C): TD errors and eligibility traces. `default_mode_interrupt_for_salient_external_demand` (mode switching). `cognitive_supervision`: goal-tree leases; holds a dominated or zero-yield process | dual_process is **optional** (`OPTIONAL_CORE_SEEDS`, loaded in `boot_cognition_on()`); adaptive control and DMN are **C**; supervision is Bulk (and in `boot_cognition_on()`) | dual_process 21; supervision 25; adaptive 10; DMN 8 | No explicit stop/no-go response-inhibition primitive (`cognitive_cycle.rs:557` doc comment reconciled with `boot_core.py:33`) |
| **Causal reasoning** | `experimentation_core` (C): `intervention_lift` and `hypothesis_test` terms. `remote_causal` (12 rules): exhaustion-first exploration, interventional do-contrast (`rc_confirm_interventional`: eff_act==1 ∧ eff_noop==0), refutation, remote attribution, with causal_prior/local_only/no_intervention controls. Also `remote_causal_ground`, `published_net_causal_debugger` (do-contrast utility, restoration evidence), Rust `can_ops` causal-influence edges, and `communication_causal_*` (causal QA) | Terms are C; `remote_causal` is Off (`remote_on`); the debugger is study-gated; causal QA is Prof | remote_causal 16; ground 13; debugger 4; causal retrieval 9; CAN ~61 files | No formal SCM, do-calculus or backdoor adjustment. LS20 remote: the offline gates pass but the live link is null (`LS20_REMOTE_RESULTS.md`) |
| **Planning / goal decomposition** | `goal_construction` (C) mints and chunks goals; `goal_derivation` (one-step means-ends Argmax); `ls20_planning` (salience→investigate→act); `arc_decompose` (order-N child goals per tier); `decomposition_consumer` (partitions order-3 `CapabilityAxis` across `requires_key` into subskill child axes); `cognitive_supervision` (arbitrary-depth goal tree); `hierarchical_effector_control` (unrolls motor programs); `operational_planning` (instruction→capability) | goal_construction is **C**; ls20 is Off (`plan_on`); arc_decompose and `decomposition_consumer` are SLO; the others are Bulk | ls20 7 (results: curious 1.0 vs blind 0.0, N=100); arc_decompose 28; `test_decomposition_consumer_migrated.py` 6; effector 5; operational 14; `test_goal_derivation_migrated.py` 1; `test_compositional_plan_migrated.py` 2 | No domain-general multi-step search planner over graph states |
| **Theory of mind** | `character_tom.py`: the propositional-attitude construction is decoded by ShapeDecode into nested belief-world SmEntities; desires become goals on an intentionality index; unseen attitude verbs join the class by adjacency. Also `bigville_theory_of_mind` (Py), `tom_meta_shape` (Py + `meta_shape_growth`, an attributed mental state as a MetaShape, decided by Rust RecogniseShape/MetaShapeMint), `interlocutor_model`, `audience`, `abusive_n3_belief_propagation` (SLO) | Loaded by domain modules; interlocutor seeds are Prof; `abusive_n3_belief_propagation` is SLO | character_tom 18 (including Sally-Anne); interlocutor 24; tom_meta_shape 5; bigville_tom 4; proposition beliefs 9; `test_modality_tom_migrated.py` 4 | First order only: no test of recursive belief (A believes B believes X). Four ToM systems, only partly unified (`TOM_SYSTEM_UNIFICATION_RESULTS.md`) |
| **Language production** | About 20 executable reply and realization seeds (`self_account_reply`, `conversation_*_reply`, `communication_*_reply`, `recount_realization`, `recount_analysis_realization`, `recount_fluency`, `gamma_production_adopt`, `speech*`); `language_production.py` (a Levelt pipeline with a self-monitoring round-trip), used live by `world_adapter._self_account_producer` | Reply seeds are **Prof** (the production daemon); recount/gamma realization seeds are **Bulk** | ~51 test files (recount 12/16/11/12, self-prose 11, voice 10, …) | Surface realization is mostly Python; `lang_production.json` and `production.json` are Decl theory |
| **Emotion and regulation** | `affective_state_core` (C): leading drive and canonical affect. `core_emotions` (24 rules mapping appraisal to action tendency for fear, anxiety, anger, frustration, disgust, joy, sadness, curiosity, boredom, fulfilment, pride, surprise). `self_conscious_emotions`; `mood_r1` (mood bias and momentum); `arousal_window_coreg` (window of tolerance, hyper/hypo dysregulation, `selfreg_pull`, `coreg_pull`, window widening and narrowing); `arousal_horizon`, which sets the planning horizon from regulation | Affect is **C**; emotions, mood and co-regulation are SLO + Off (enabled in `boot_cognition_on()`) | core_emotions + ~10 files; self-conscious 8 files; mood r1b/r1c; arousal_horizon | No strategy-level regulation (cognitive reappraisal, suppression); regulation happens at the arousal level only |
| **Numerosity** | `number_world.py`: magnitude grounded in countable unit tokens, a successor line, counting up and down. The `number_qualia` capability experiment tests transfer of a felt band, not number sense | Py world adapter | `test_number_world_migrated.py` 5 | **Absent**: subitizing, an approximate number system, Weber-ratio discrimination |
| **Imitation / social learning** | Concepts only (`mirror_neuron`, `psy_social` prose principles). `glassbox_r1_social` is coordination through trade, not imitation | Decl | none | **Absent** as a mechanism |
| **Sleep regime** | `consolidation_scheduler` (SLO + Off, enabled in `boot_cognition_on()`) binds `NetworkModeState` as `has_memory_clock`, mints cooldown-paced offline `MemoryCycle` nodes (with `SystemTwoEscalation` recruiting `memory_replay`, `memory_consolidation`, `memory_cleanup`) during low-demand default-mode epochs, and prunes completed cycles after `retention_epochs` | SLO + Off (`boot_cognition_on()`) | `test_consolidation_scheduler_migrated.py` 6 | Opt-in (`enabled: 0.0` by default); no multi-stage REM/NREM dream cycle |

Corrections to revision 1's "stubs" and "remnants":
- `generative_skeptic.json` holds six FailureLesson concepts (patterns and probe templates), consumed by `domains/generative_skeptic.py` and `autonomous_curation.py`. It is Decl + Py (`tests/test_generative_skeptic.py`).
- `invariant_representation.json` holds six concepts and five relations. It is Decl, and its source `.py` has been deleted.
- `seven_meta_shape_subsystems.json` holds 26 concepts and 6 head/body principles. It is Decl, and `mechanism_index` depends on it.
- None of these three is empty. All three are knowledge, not mechanism. Their executable siblings are `meta_shape_growth` (10 rules) and `vision_invariant_comparator` (4 rules).
- `discourse_state` and `imagination` are already split the right way: the graph decides (`conversation_discourse_state` has 4 rules; `composer_imagination_graph` makes the engage decision), and Python handles mechanism and I/O.
- The real Python-logic remnants are `conjecture.py`, which has no graph seed, and `character_tom.py`.

## 5. Extended thinking: gap analysis

The intended faculty: relax admissibility and widen aperture to reach deeper into the solution space for candidates, then settle back.

| Part | Exists? | Evidence |
|---|---|---|
| Trigger | Yes | `dual_process_core` (prediction error, novelty, uncertainty, conflict, low confidence); `impasse_escalation`; `cc_residual_deepen` |
| Request object | Yes, consumed opt-in | P3 adds `ExtendedThinkingStepRequest` nodes which draw on `ThinkingBudget`; each widening step is approved or denied by the generic budget rules. Existing `synthesis_requested` and `Impasse -needs_decomposition-> CapabilityAxis` bridges remain opt-in; `Fault.needs_decomposition` remains unconsumed. |
| Area admission | Yes | `admit_system_two` admits SystemTwoTaskSet areas, with lease and staleness checks |
| Shared budget / anytime object | Yes (opt-in) | `thinking_budget.json` (`ThinkingBudget`, `tb_refill_once_per_epoch`, `tb_fund_from_horizon`, `tb_debit_request`, `tb_record_exhaustion`), integrated with `impasse_simulation_bridge`, `consolidation_scheduler`, and `boot_cognition_on()` |
| Graded relaxation of admissibility | Yes, scoped | `extended_thinking.json` steps the `agent.dim_grains` ladder `[0] → [0,1] → [0,1,2]` and the `agent.gen_infer_enabled` ladder `0 → 1`; each step is funded and restored by `ToleranceRelaxLease`. Commit-permissiveness tolerances are excluded. |
| Widening of aperture | Partial (`aperture_frame` questioning landed) | `aperture_frame.json` now probes bypassing chosen frames after `ap_question_after` generations and drops hiding chosen frames; `DimInferPolicy.dim_grains` is graph-governed; domain apertures remain separate |
| Re-admission of pruned candidates | Yes, scoped | The executor re-arms one ShapeDecode observation at a time by backdating `decoded_epoch`, after marking it `minted` so frozen `sd_redecode` runs. It re-verifies through DimInfer or GenInfer. Motor collapse and the bigville core still do not re-admit candidates. |
| Generative proposal | Domain-bound | `ps_propose`/`SynthEnumerate` (code); GenInfer (matrices); GWM rollouts (actions); no manifold projector |
| Tree search over graph states | Partial | GWM bounded branching rollouts with `prune_terminal_*` (C); the ShapeDecode internal beam |
| Imagination | Yes, including opt-in impasse trigger | Detached imagination and counterfactual_experiment run on idleness or explicit request; `impasse_simulation_bridge` (opt-in) triggers GWM counterfactual rollouts on `dual_process_core` `instinct_conflict` escalations |
| Verification | Yes | `build_candidate`, the MDL witness, the grounded-outcome comparison in GWM, the judge |
| Settling back and caching | Yes, scoped | Extended thinking restores the original Agent setting on terminal outcomes and caches a successful grain rung by observation key; a minted linear GenInfer generator is the persistent cache for its rung. `ps_accept` and EWM consolidation retain their existing caches; the manifold does not cache. |

Revision 2 changes this picture. Most parts of an executor already exist as graph rules: triggers, admission, imagination, rollout search, verification and consolidation. What is missing is the connective tissue:
- a consumer for the orphaned requests;
- a shared budget;
- a graded relax/widen operator with re-admission;
- a route from impasse into the existing imagination and rollout machinery.

## 6. Missing components, prioritized

1. **Extended-thinking executor (wiring, not new faculties).**
   - Consume `synthesis_requested` and `needs_decomposition` (and route `needs_tool` failures out of `self_extension`) by minting a SystemTwoEscalation plus a SimulationRequest or counterfactual experiment, so that impasse drives the existing GWM and imagination machinery.
   - Add a shared `ThinkingBudget` node, funded from evidence (the arousal horizon, value of information).
   - Add a graded `RelaxAdmissibility(ε)` / `WidenAperture(k)` step that re-admits pruned candidates.
   - Verify with the existing checkers, then settle back through EWM consolidation and codebook minting.
2. **Soft admissibility in Γ.** A Rust softmax / soft excluder over exp(w); tolerance literals promoted to graph nodes; a real-valued `ParetoDominates`. Item 1 needs these, because otherwise there is nothing graded to relax.
3. **Unified aperture.** Recast the domain apertures as Observer-frame instances, chosen by evidence or value of information (the prediction-world judge shows this working). Make the relax step graded, and add a trigger that questions a frame even when it leaves no residual.
4. **Qualia as a cache.**
   - Graph-native Shape minting.
   - One signature space covering QualiaDimension axes, Shape sig_k and valence.
   - A similarity-indexed recall Term. Rust `ShapeIndex` (recall by shape in `memory.rs`) is a ready substrate for it.
   - A pre-registered cross-domain recall test.
5. **Generative manifold.** A projector from moves to trajectories (reusing GWM rollouts), refinement driven by item 1, a manifold cache, the three implementations collapsed into one, and a native ThoughtManifold.
6. **Inference ladder.** Make DimInfer → GenInfer (linear → quadratic → coupled) → TimeInfer/order-N escalation rungs under item 1. Make order-N native, and let TimeInfer accept irregular streams.
7. **Turn on and connect what exists.**
   - A production producer for offline `MemoryCycle`: a sleep/consolidation scheduler driven by idleness and load.
   - Reconcile whether dual_process is core or optional.
   - Decide which Off/SLO faculties belong on by default (decay tiers, emotions, co-regulation, remote_causal, ls20_planning), and test them together rather than in isolation.
8. **Genuine holes inside existing faculties.**
   - Recursive (second-order) ToM, and unification of the four ToM systems.
   - Strategy-level emotion regulation, with reappraisal as re-framing the appraisal input.
   - A formal SCM / do-calculus over the CAN and causal facts.
   - A domain-general multi-step planner over graph states, and tests for `goal_derivation` and `compositional_plan`.
   - An explicit response-inhibition primitive.
   - Analog mental rotation and an imagery buffer.
9. **Truly absent faculties.** Numerosity (subitizing, an approximate number system, Weber discrimination), and imitation or social learning from demonstration.

## 7. Caveats

- Test counts come from inspecting test files or from grep. Pass status is taken from results docs, since no tests were run for this report.
- "No consumer" and "no producer" mean that none was found by searching `seeds/`, `runners/dsl/src`, `domains/`, `substrate/` and `tests/`.
- Boot status was verified mechanically by `scripts/report_seed_boot_status.py` (`SEED_BOOT_STATUS_20261010.md`). Neither `dual_process_core` (`OPT`) nor `cognitive_supervision` (`Bulk`) is pulled into the `CONVERSATION_SEED_ANCHORS` dependency closure, whereas `shape_decode_loop` and `lexical_qualia` are.
- The prediction-world results (v1–v10) are the only held-out evidence about the judge and aperture machinery. They are not evidence about the other faculties.

## 8. Phase 4 evidence update (2026-10-21)

This addendum supersedes the Phase 4 implementation snapshots above where they conflict. Phase 4 is executed against its registered synthetic families. Results establish only the registered conformance and generated-world outcomes; they do not establish general real-world or human-level capability.

- **Representation and recall:** numeric Shape minting and typed signature adapters are graph-backed and tested. `RecallNearest` is implemented natively and exposed through graph/JSON/reflection. SimilarityRecall requires an exact, current, linked verifier receipt and falls back to the existing funded executor. The numeric-Shape path can mint its verifier receipt from linked verified Shape outcome evidence. Live `QualiaDimension` sources, equivalent producers for other domains, and registered recall-cost evidence remain absent.
- **Observer aperture:** guarded frame adapters, explicit positive-VOI authorization, shared same-epoch funding and forced-frame protections are tested. Policies remain off by default; upstream domain producers and empirical VOI remain open.
- **Manifold and thought:** GWM candidates pass through native `FutureManifoldProjection`; exact zero-residual projections now mint provenance-linked feasibility receipts. ThoughtManifold and cognition-manifold use the same native projector, with an equivalent-input shape-snapshot parity test. ThoughtManifold owns concept-region and aperture deviation/frontier decisions. Static lexical/relation extraction remains in the adapter; broader registered projection outcomes are open.
- **Temporal bridge:** regular bounded frame windows, explicit measured-event ingestion/seals, funded TimeInfer and refusal of irregular streams have mechanism tests. No registered result is available.
- **Registered evaluation:** freeze commit `199583ca6c4fe861dae90dd5814d3f0ad3b9f5ed`; fixed draw `[0, 200)`. D2/D3 passes 200/200 parity streams and 100/100 collision controls. D1 passes 200/200 regular synthetic continuations versus 0/200 off, with all 100 unsupported controls refused. E1/E2 passes 80/80 feasible synthetic worlds versus 0/80 off, with 60 infeasible and 60 missing-model controls. D5 passes both generated transfer families with 100% solve in both arms and 50% fewer exact candidate checks on recall-on. C5 fails: 92/200 (46%) resolutions in both arms, 0 pp gain, adjusted p=1.0; funding and forced-frame invariants pass. These outcomes are limited to registered generated fixtures; see raw report and hashes in [`COGNITION_BUILD_P4_RESULTS.md`](COGNITION_BUILD_P4_RESULTS.md).
- **Regression and phase status:** the latest 20-file gate reports 15 GREEN, 3 inherited RED, 1 ALL_SKIPPED and 1 NOT_ESTABLISHED; baseline verification reports 4 held, 0 stale and 0 new. The RED suites are frozen-core, dual-process and Arc; capability-control timed out and staleness-decay was fully skipped. The current P4 acceptance slice passes 139 tests with 1 skip, and P4-filtered orphan lint reports no unallowlisted P4-written signals. Phase 4 H1/H2/H4 are complete and the phase is executed with the C5 failure and supported-input limits preserved. The detailed task and evidence ledger is [`COGNITION_BUILD_P4_RESULTS.md`](COGNITION_BUILD_P4_RESULTS.md).

## 9. Phase 5 evidence update (2026-10-22)

This addendum updates the corrected inventory with P5 mechanism work and registered results. Mechanism tests and v3 establish behavior only on frozen fixtures; they do not establish general cognition. The original v1 harness remains `NOT_ESTABLISHED` with 3,200 null primary arm slots. V2's E4 outcome is invalidated because its one-step adapter used a depth shortcut rather than the shared transition model. Corrected v3 executed 200 paired cases and 100 controls for each item; all eight criteria pass with no nulls or adapter errors. Full results and limits are in [`COGNITION_BUILD_P5_RESULTS.md`](COGNITION_BUILD_P5_RESULTS.md).

| Faculty gap updated | Mechanism and commit evidence | Supported fixture class | Registered P5 outcome |
|---|---|---|---|
| Attributed state / ToM | Native source-preserving views (`35c78e1f`); recursive bounded belief updates (`2f9f9c41`); adapters (`0e001d60`) | Explicit source rows with owner/holder permutations; accessible, acyclic second-order paths | F1/F2 PASS; F2 on 200/200 vs off 0/200, inaccessible controls all unknown |
| Strategy-level emotion regulation | Evidence-preserving funded reappraisal (`b7225e93`); adapter (`0e001d60`) | Alternative frames tied to explicit evidence references; source events retained | G2 PASS; supported selections 100/100 on vs 0/100 off, no unsupported acceptance |
| Response inhibition | Graph stop lifecycle and native action boundary (`7a15326d`, `6ea3ab94`, `e3fff962`); adapter (`0e001d60`) | Explicit stop/go events and one-use authorization at the native reflex sink | G3 PASS; stops withheld 167/167, go emissions 66/66, no duplicates or late-stop anomalies |
| Causal intervention | Finite SCM evaluator and backdoor adjustment (`3abbba6e`, `b47a60de`, `64118d55`, `432c902f`); adapter (`0e001d60`) | Explicit finite confounder/collider/chain models and nonidentified abstention | E3 PASS; identified 225/225, unsupported 75/75 unknown |
| Multi-step planning | Bounded graph planner (`a3207840`); System-2 arbitration (`9b028b91`); corrected adapter (`0e001d60`) | Versioned transitions, depth 2–8, same graph supplied to planner and direct-edge comparator | V3 E4 PASS on registered tasks, 200/200 vs one-step 0/200; planner used 3.97 more expansions on average. V2 is invalidated. |
| Parent completion | Epoch-scoped verified completion witness (`5fa6e603`); adapter (`0e001d60`) | Required-key coverage by verified same-epoch child work; stale and partial evidence controls | A2 PASS; 300/300 valid completion decisions, no premature settlement |
| Analog imagery | Bounded funded graph buffer (`5e86399e`, `4719bcb9`); wrong-source receipt rejection (`1feac532`) and adapter (`0e001d60`) | Sampled four-point 4×4 lattice shapes; quarter turns; external source-bound verifier | D6 PASS; 200/200 primary transforms verified, 100/100 wrong-source controls rejected, no grounding; work equaled shortest-angle work |

The cognition-on profile now includes the P5 planner, arbitration, completion and imagery seeds, with explicit enablement in `cognition_on_params.json` (`0cccbbc7`). Default and conversation boot remain isolated. The registered result does not establish end-to-end use in open environments or human-like capability. F2 covers bounded accessible paths; E3 covers explicit finite SCM fixtures; E4's primary graphs have no direct goal edge and its one-step comparator only executes one direct edge; G3 has 66 valid-go cases and a 94.50% Wilson lower bound; D6 uses an external verifier and shows no work saving. Boot-time cost was not measured. P4's C5 failure and P3's inherited NOT_ESTABLISHED gate remain in force.

## 10. Phase 6 evidence update (2026-10-22)

The linear P6 result adds only a narrow measured PMB slice. The 2×2 Loopover panel solved 0/200 baseline and 200/200 Track I tasks, using the existing generic greedy solver and eight supplied moves; it does not measure process invention or general puzzle-solving. MBPP's existing solver produced identical candidate IR and outcomes in both profiles: 32/240 passed all held-out assertions. D4 and finite mechanism panels were `NOT_RUN` in both arms because no grounded effect/intervention adapters exist. The 100 malformed/stale/opaque ProcessApply controls all failed closed without graph-attribute mutation. Human comparisons and all capability-level claims remain unavailable. Full metrics, hashes and inherited regression status are in [`COGNITION_LINEAR_P6_RESULTS.md`](COGNITION_LINEAR_P6_RESULTS.md); raw held-out records remain outside git.

## 11. Phase 7 evidence update (2026-10-22)

P7 added a graph-rule episode acquisition mechanism and a separate perceptual numerosity fixture. The held-out acquisition panel validated candidates in 40/40 experience-built trials for each of tool/contact and social request/repair, versus 0/40 frozen-space trials. Exposure-only and orthogonal controls produced no candidates in 100/100 per world; label-shuffled annotations stayed detached in 100/100 per world. Source/grounding leak flags were zero. The numerosity graph matched all 200 small-set and 800 ratio fixture labels; equal-ratio scale differences were zero points.

These are mechanism-only results. The numerosity inputs are synthetic area/density signals, not calibrated perception. The ≥20-point later-task transfer criterion is `NOT_ESTABLISHED` because no downstream behavior consumes the acquired axis; human and real-world perception comparisons are unavailable. P7 also leaves general existing-axis residual comparison, finer-grain sweeps, significance calibration, retirement and repeated revision open. Full hashes and per-panel status are in [`COGNITION_LINEAR_P7_RESULTS.md`](COGNITION_LINEAR_P7_RESULTS.md). Phase 8 is authorized only for the observed-episode learning interface and must retain those limits.

## 12. Phase 8 evidence update (2026-10-22)

The P8 mechanism panel completed 1,100 held-out records. Native probe selection identified 200/200 finite cases versus 100/200 for fixed probe and 0/200 for passive exposure, at one interaction per case. Regular latent fixtures verified all 100 held-out continuations; 100 nonrecurring cases and all 200 missing/irregular controls remained unknown. All 100 funded graph projection fixtures produced a result-linked audit and version change. No hidden answer was exposed in the scorecard's agent-input audit.

This is bounded fixture evidence. Finite-mechanism tests use supplied competing hypotheses; they do not show that open-world induction produced those hypotheses. Numeric VOI, calibrated stochastic distributions, and external simulator/actuator refinement remain `NOT_ESTABLISHED`. Full metrics and hashes are in [`COGNITION_LINEAR_P8_RESULTS.md`](COGNITION_LINEAR_P8_RESULTS.md). P9 entry is limited to typed observed effects and the finite probe/audit interface.

## 13. Phase 9 evidence update (2026-10-22)

The registered P9 held-out draw completed 1,500 rows. Funded exact inverse invention over the supplied finite 3-cycle family passed 200/200 with three fresh-state native checks per candidate, versus 0/200 with operators disabled and 0/200 held-only. The paired gain was +100 percentage points; verification failures and answer leaks were zero. Singular/malformed inverse and incomplete-probe alias controls passed 100/100 per arm. Explicit finite distributions retained the registered 0.25 unknown mass in 200/200 cases per arm, and irreversible matrices returned no exact inverse.

These results establish a narrow exact-invention/evaluator conformance slice. They do not show open-world operator discovery, general process induction, learned stochastic distributions, external refinement, downstream solving, or any whole capability level. The repair test uses a declared goal criterion; it establishes verifier behavior and epoch invalidation, not independently discovered repairs. Separate boot-time and heap/RSS measures were not captured; graph size and total per-trial time (including boot) are recorded. Human comparison is unavailable. P10.01 proceeded with parametric lifting and goal interfaces; the final P10 status and its failed advantage gate are recorded in §14. Full metrics and hashes are in [`COGNITION_LINEAR_P9_RESULTS.md`](COGNITION_LINEAR_P9_RESULTS.md).

## 14. Phase 10 evidence update (2026-10-22)

P10 implemented bounded native process lifting, targeted goal regression/inverse invention, exact-context graph strategy capture/replay, and deterministic cube/sliding/tool-goal world fixtures. The solver's process selection is now persisted before state mutation, and trace replay matches the reported state in the registered gates. This establishes the tested mechanisms only; it does not establish transferable strategy.

The first P10 held-out runner is invalidated: `ProcessSchemaPolicy` was disabled, so the runnable graphs had no attached domain affordances. Its raw scorecard is preserved and excluded. The corrected V2 runner used a fresh frozen protocol and allocation. Across 800 supported paired tasks, greedy and discovered-strategy both solved 128 (16%), all in tool-goal composition. Paired gain was 0 percentage points against the registered ≥20-point criterion (`FAIL`). Loopover 3×3, Loopover 4×4 and cube solved 0/200 per arm. All 100 misleading-precondition controls emitted `needs_tool` with no candidate; input and trace audit failures were zero. Baseline, primitive-search and sliding panels remain `UNSUPPORTED`; the human comparison is unavailable. No L2/L5 or other capability-level claim follows. Full statuses, work metrics and hashes are in [`COGNITION_LINEAR_P10_RESULTS.md`](COGNITION_LINEAR_P10_RESULTS.md); raw held-out scorecards remain outside git.

The next supported entry is P11 representation proposals and cross-domain process maps over verified native effects with exact source/epoch identity and acquired P7 distinctions. It must preserve the P10 zero-gain result and may not count exact-context task-trace records as transfer.

## 15. Phase 11 evidence update (2026-10-22)

P11's native representation and process-transfer mechanisms passed the registered safety checks. The frozen heldout panel completed 2,600 records with 800/800 source-exposed transfers verified, 0/800 mismatched-source adoptions, zero wrong-frame or nonconjugate control adoptions, and zero pairing-hash, arm-coverage or agent-input audit failures. The primary transfer-efficacy metric is `NOT_ESTABLISHED`: the fresh arm had no target-learning adapter, so there were zero matched solved source/fresh outcomes from which to measure exact-check savings or solve loss. This result establishes neither a transfer benefit nor no benefit.

The generated permutation and integer-matrix worlds establish a narrow native ProcessSchema transfer mechanism only. They do not establish ARC/LS20 performance, open-world representation learning, a protocol-matched human result, or L4/L5. External grid ingestion remains unsupported, and human comparison remains unavailable. Full metrics, hashes and the explicit next-entry fallback are in [`COGNITION_LINEAR_P11_RESULTS.md`](COGNITION_LINEAR_P11_RESULTS.md); raw heldout records remain outside git. Phase 12 may proceed on the supported P7 episode-acquisition interfaces and verified native effects, without assuming fresh process-map learning.

## 16. Phase 12 evidence update (2026-10-22)

P12's frozen 1,500-record draw establishes a bounded social-acquisition and explanation/rebuild mechanism result. Observation, demonstration and instruction each achieved 200/200 own-trial successes; reward-only also achieved 200/200. The registered social advantage is therefore `FAIL` at 0 percentage points against the ≥20-point threshold. Isolated rebuild adopted 200/200 schemas and matched 200/200 held-out effects; source-ID and source-expression redactions each retained 100/100 agreement. Shuffled, missing and body-mismatch controls had no adoptions or own-trial successes. Pairing, allocation, input-audit, completion, false-grounding and unverified-adoption failures were zero.

This result does not establish a social-learning advantage or whole L1/L6 capability. It is limited to one synthetic primitive under the minimal PMB profile; the reward arm receives two own probes and uses three action calls against one scored call in other arms. The equal outcome is a valid failure for this preregistered comparison, not evidence that social learning can never help. Human comparison is unavailable. Full work metrics and provenance hashes are in [`COGNITION_LINEAR_P12_RESULTS.md`](COGNITION_LINEAR_P12_RESULTS.md); raw records remain outside git. Phase 13 may proceed with verified episodes/processes, the P1 replay scheduler and Phase 10 traces. It must preserve the failed advantage and cannot assume fresh process-map learning.

## 17. Phase 13 evidence update (2026-10-22)

P13's frozen draw completed 800 paired arm records (200 per arm) and 100 interrupt/restart controls. The registered delayed-task accuracy gain was 0 percentage points against the ≥10-point threshold (`FAIL`); new-task loss was 0 against the ≤2-point bound. Package-amortized exact-work reduction was 35.9375% (20.5 versus 32 units, `PASS` against ≥25%), and funded same-shape strategy recall succeeded on 200/200 full-sleep streams. All controls resumed correctly, and pairing, access, answer/strategy, task-completion, receipt-provenance, compute-match, allocation and safety audits had zero failures.

The evidence is limited to synthetic native simulated tasks. No arm performed an external action, no protocol-matched human comparison is available, and no capability level is closed. The accuracy failure means P14 must not assume a sleep-related retention benefit. Its supported inputs are verified library schemas and equivalence witnesses, observed strategy entries and application receipts, P1 replay receipts, and exact task outcomes. P14 must complete I4.5 and I7.3 before I7.1 authorship enters the live invention loop. Full metrics and frozen component hashes are in [`COGNITION_LINEAR_P13_RESULTS.md`](COGNITION_LINEAR_P13_RESULTS.md); raw records remain outside git.

## 18. Phase 14 evidence update (2026-10-22)

The corrected frozen draw completed 200 paired candidate-operator tasks, 200 law claims and 100 tampering controls. The graph-authored `commutator_square` macro solved 200/200 one-call S4 tasks versus 0/200 for one held commutator, a +100-point result against the registered ≥20-point threshold (`PASS`). The macro used four declared work units per task versus one held application, so this is a one-call task advantage at higher algebra work, not a compute-efficiency claim. All eight development cases qualified with invariant checks preserved. At P14 closeout the candidate awaited approval; P15 later records the user's scoped approval and graph event.

All 100 structural commutator-parity laws checked with current bound proof references, all 100 false finite-sample claims were rejected, and all 100 proof-reference/criterion tampering controls failed closed. Pairing, world/access hashes, input audits, proof bindings, work accounting, allocation and external-action checks had zero failures. This establishes only the declared finite S4 commutator law and generated one-call macro task. Numeric evidence-exposure count was not captured; the recorded audits confirm ordinary task goals were visible but answer labels and hidden strategies were absent. Mean boot was about 0.21 s. Mean graph snapshots were 1,906 nodes/452,546 bytes held and 1,947 nodes/468,040 bytes authored; these are accumulating adapter snapshots, not isolated per-task growth. Human comparison remains unavailable, no external action was taken, and no capability level is closed. The initial preregistration was superseded before any held-out run; the corrected revision was run once. Full outcomes and hashes are in [`COGNITION_LINEAR_P14_RESULTS.md`](COGNITION_LINEAR_P14_RESULTS.md); raw files remain outside git.

## 19. Phase 15 evidence update (2026-10-22)

The frozen three-generation process-macro draw completed all 1,800 paired-arm rows and 100/100 analyzer tampering controls with zero integrity failures. Full system solved 600/600, while unchanged and adaptive curriculum each solved 196/600. Full-system success remained 100% at all three checkpoints; unchanged success rose from 0% to 28% to 70%, narrowing its gap with full system. Adaptive curriculum matched unchanged in every generation. Full system used two more declared work units per task on average, with a paired bootstrap 95% interval of 1.9367–2.0650.

The registered generation-trend model is not estimable because of complete or near-complete separation. The preregistered positive-trend criterion is therefore **NOT_ESTABLISHED**. Per-generation paired tests show differences on this specific generated task family but do not substitute for a generation trend. The result supports only the measured finite S4 operator macros and their one-call targets; it does not establish recursive improvement across independently structured tasks, general autonomous invention, cross-domain transfer, or human-relative performance. Human comparison is unavailable, no capability level is closed, and no next phase is automatically authorized. Full metrics and hashes are in [`COGNITION_LINEAR_P15_RESULTS.md`](COGNITION_LINEAR_P15_RESULTS.md); raw records remain outside git.

## 20. Phase 20 frozen result (2026-10-23)

P20 completed its standalone freeze and one held-out allocation. Exact native runtime provenance was `ATTESTED`, allocation coverage was complete, and the structural analyzer passed with no failures. The registered primary mapped-source minus fresh normalized learning-curve AUC was **−0.333** (fresh 0.500, mapped-source 0.167, mismatched-source 0.500), a valid `FAIL` against the preregistered +0.20 threshold. Mapped transfer is not an established benefit and remains unsupported as a prerequisite for later efficacy claims.

The bounded social and explanation mechanisms passed their registered structural checks: observation, demonstration and instruction verified/executed 200/200 each; reward-only abstained 200/200; native explanation reconstruction and adoption passed 200/200 with 100% fidelity; all 100 structural controls passed. This supports only the declared two-domain/two-step simulator mechanisms, not general transfer or open-ended social learning. No capability level is closed. See [`COGNITION_LINEAR_P20_RESULTS.md`](COGNITION_LINEAR_P20_RESULTS.md); raw SHA-256 `76f575f5710449f58adf0d7152452a14d2d831f643bee5b4e7599d90e2f938c8`, analyzer SHA-256 `6ecfaa9738670bb32ef41f87e96c38aaeaf315ed6c2a903bcd9312d84233f5c8`.

## 21. Phase 21 frozen result (2026-10-23)

P21's finite byte-accounted memory, staged native sleep, and native curriculum-to-learning bridge passed structural checks in the registered simulator panels. The one-time holdout completed 2,400 sleep rows, 1,800 curriculum rows and 100/100 controls with `ATTESTED` runtime provenance and zero analyzer failures. Full-sleep minus replay-only normalized delayed learning-curve AUC was **0.000** against +0.10, with new-task loss 0.000; residual curriculum minus mean(random,fixed) delayed accuracy was **0.000** against +0.10. Both are valid `FAIL`s. Every primary arm reached delayed-accuracy ceiling, so no capability level is closed and neither efficacy benefit is established. P22 may proceed only on independent-goal tasks and must not use these failed effects as evidence. See [`COGNITION_LINEAR_P21_RESULTS.md`](COGNITION_LINEAR_P21_RESULTS.md); raw SHA-256 `d906b3c1eca6e4dafac64a9c1f1bf3d807c77d2571f1202657fc0454516aadd1`, analyzer SHA-256 `3a1d8da1920e30ff0266ef142eb15f93ad3718fc7b37332f5b96fcfbaede5fb3`.

## 22. Phase 22 independent-improvement readiness (2026-10-23)

P22.01 freezes independent-goal identity, same-world checkpoint pairing, whole-world cluster resampling, ceiling-safe zero effects, and the separation of score improvement from efficiency. The six analytic estimator tests pass. P22.02 installs a disabled generic proposal boundary that requires expression-digest-attested training candidates and a second distinct native-verified trial. Proposal creation and qualification terminalize their search requests; P19 search now has per-request attempt ceilings and mints at most one candidate per request from the best unminted verified expression. Tests verify bounded requests and no post-qualification attempt growth. Proposals remain non-actionable until exact candidate approval; held-out tasks cannot enter proposal. P22.03's adapter scores independent Loopover and D4 worlds through native application, with strict digest checks and approval/receipt-backed checkpoint capture. Empty panels, duplicate checkpoint identities, malformed permutations and negative work declarations are rejected. Checkpoint snapshots now include parent-linked cumulative primitive work in the immutable digest and enforce the shared ceiling against that total. This records only primitive work; cumulative data, search, approval, model-call, memory and wall-time costs remain unaccounted. P22.E1 exercises native search, exact test approval, action execution, verified simulated receipt and perturbed-state abstention; the fixture is not external authorization. Profile isolation and a shared budget pass. Repeat-adoption diagnosis traced the false rejection to recursive native expression-tree string leaves represented as `Surface(Text)` while approval round-tripping produced `Str`; the adoption and invalidation rules now compare canonical JSON tree values while retaining the digest and effect bindings. Regression tests and a three-generation native development-lineage test pass proposal qualification, candidate-specific test approvals, action receipts and parent-linked immutable checkpoint capture on correctly sized 4-element, Loopover and D4 fixtures; each lineage is scored on one shared training world, and unequal declared work correctly prevents an efficiency comparison. Later-generation development goals derive from their parent, so these results do not establish independent-goal efficacy. Correctly sized Loopover and D4 training probes also produced native-verified, two-trial-qualified candidates; their exact bindings and reproducible digests are recorded in [`COGNITION_P22_CANDIDATE_APPROVALS_20261023.md`](COGNITION_P22_CANDIDATE_APPROVALS_20261023.md). Those candidates remain unapproved and have not been executed. Independent-goal held-out lineages, candidate-specific authorization, actual four-arm learner comparators, remaining cumulative resource accounting, frozen P22 evaluation and efficacy remain open. The L1–L7 matrix leaves every level open; no capability level is closed.

The P22 checkpoint binds a read-only cumulative graph-resource snapshot containing shared ThinkingBudget usage, node/status totals, search attempt and request counts, proposal/qualification/approval/receipt/task/denial totals, and canonical serialized graph bytes. Failure, pending and timeout statuses are retained. The serialized-byte field measures graph readback size, not native memory. No held-out evaluation has run.

The snapshots additionally total training-split evidence and direct task exposures, outcomes, solver steps and declared primitive work, search-attempt work, and requested, approved and denied budget cost. Resource matching compares these dimensions. This still does not provide native rule-step totals, actual model-call coverage, allocator memory or wall time; canonical serialized graph bytes remain a graph-readback measure. The resource-accounting suite passes three tests.

P22.01's arm contract was reconciled with P22.03 to specify unchanged, adaptive-only, invention-only and full conditions. The conditions separate curriculum, invention and their interaction, but no working four-arm learner adapter currently exists. P22.E2 remains open.

Native arm-policy wiring enables the common ProcessSchema/Solver path and configures those four conditions on fresh cognition-on graphs with one shared budget at a common capacity while preserving the active ancestor process portfolio. Tests verify switch patterns, portfolio preservation and budget validation. The wiring test does not show that each arm executes the same training worlds or learns; those comparators remain open.

For curriculum-enabled P22 conditions, a disabled-by-default native bridge releases a selected training `ProcessCurriculumTask` as a runnable same-graph `SolveTask`. Common-ancestor solver completions close tasks without requiring a P19 request, supporting the adaptive-only condition; solver impasses enter P19 search when invention is enabled. After the finite search frontier or another native terminal event is observed, P22 records the outcome and reopens the scheduler. Development integration tests cover the solver-only outcome and two sequential curriculum tasks, with a separate search-isolation regression covering P19 dispatch. No approval or world-action receipt is fabricated. The P22 setup keeps the P21 curriculum-learning bridge disabled. These tests verify arm lifecycle wiring and outcome retention while leaving outcome-weighted adaptation, non-ceiling matched panels, and all four learners unverified. The focused P22 suite passes 111 tests.

A fixed development-only 32-world native common-solver check scored 0/32 generated D4 tasks solved and 11/32 Loopover tasks solved. Neither panel is at the all-success ceiling; D4 is at the ancestor floor, which limits its comparison to recovery from that baseline. This diagnostic does not run the four matched learning arms and is not efficacy evidence.

The original v1 world generators used for the candidate packet have only two distinct goals across 200 validation draws in each family; these candidates therefore remain mechanism evidence and cannot support independent-goal generalization. Versioned v2 generators preserve the v1 packet, use disjoint train/validation family-seed blocks, and yield 8 D4 goals plus 190/195 distinct Loopover goals across 200 training/validation draws. The common solver solves 14/32 D4 and 6/32 Loopover tasks on v2 development panels. This supports using v2 for future development, but does not close the four-arm adapter, efficacy, or held-out gates.

A read-only panel scorer now evaluates one digest-attested unapproved candidate across a common registered validation family, verifies all answer-free world views, retains every row, and hashes the panel identity/outcomes. It is limited to proposal validation and cannot approve or execute a candidate. The four matched learner comparators and P22 efficacy remain open.

Native v2 proposal probes used two distinct training world identities per family and 200 common validation worlds. One proposal per family qualified; another remained awaiting qualification after the bounded request pair was consumed. The qualified D4 proposal solved 16/200 validation worlds, while the qualified Loopover proposal solved 0/200. No matched arms, approvals, or receipts were present, so these frequencies do not estimate improvement. Raw evidence and digests are in [`COGNITION_P22_V2_DEVELOPMENT_PROBES_20261023.md`](COGNITION_P22_V2_DEVELOPMENT_PROBES_20261023.md); v2 validation draws 0000–0199 are unavailable for the final preregistered validation allocation.

The cognition-on P22 profile booted in a median 0.2020 s across three fresh runs, with 1,520 graph nodes, 773 native rules and 288,952 canonical graph-JSON bytes; allocator/resident memory remains unavailable. A profile-level causal regression now verifies that mutating an adopted operator after a receipt invalidates its exact approval binding and abstains before another world transition. The combined P22 regression bundle passes 117 tests. These mechanism and boot measurements do not close the four learner arms, candidate-specific authorization, cumulative matched resource coverage or efficacy gates.

The P22.E1-specific verification bundle passes 88 tests across the estimand, independent-improvement, checkpoint adapter, causal ablation, and cognition-on integration modules. This is local mechanism evidence only; P22.E2 cannot freeze until actual four-arm learner adapters and the remaining resource dimensions are available.

A reproducible four-arm development wiring probe runs all four native policy settings on the same eight v2 training worlds in each family. A native `AddNodeWithinCounter` effect now enforces the shared global-attempt cap at the mutation boundary: the refreshed invention-enabled arms each create and reserve exactly 64 attempts, and the unchanged/adaptive-only arms create and reserve zero. The minimized two-task test at a cap of one also passes. D4 solved counts remain 3/8 in every arm and Loopover 1/8 in every arm; these training-only frequencies are not efficacy estimates. Digest-bound successful native rule-progress firings measure 9/67/24/96 on D4 and 16/109/29/138 on Loopover across unchanged/adaptive/invention/full. The runner made zero external model calls; allocator memory and wall-time remain unavailable, and realized resource vectors still differ, so no efficiency claim is supported. No candidate approvals or world receipts were created. See [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md) and the refreshed raw hashes. P22.E2/E3 remain open pending independently grounded approved checkpoint lineages, candidate-specific authorization, and a preregistered analysis that relies on fixed ceilings rather than an unsupported efficiency claim.

The refreshed P22 regression bundle, including the four-arm runner guard, global ceiling settlement, and digest-bound runtime counters, passes 120 tests. The raw development files reproduce byte-for-byte; their candidate attestations, terminal request statuses and resource mismatches remain in the archived records.

The later isolated-worker refresh supersedes the preceding wall-time and runtime-rule-step gaps for the four-arm development diagnostic: each arm now records elapsed time, successful native rule firings, and a digest-bound `ru_maxrss` process peak. The RSS measure includes the Python interpreter and native runtime; native graph allocator bytes remain unavailable, and the runner's zero external model calls do not establish general model-call coverage. The four-arm resource vectors still differ, so no efficiency comparison is supported. The same report records a distinct-goal qualification probe: D4 training draws 0200/0201 and Loopover 0206/0207 produced proposals but zero qualifications on the second independently generated goal. Eight-world validation scores are descriptive candidate frequencies only; no approvals or receipts were created. See [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md) and the two digest-bound raw probe files. Candidate-specific authorization, independent-goal approved lineages, informative four-arm efficacy, P22 preregistration and held-out results remain open; no capability level is closed.

The subsequent P22 cross-goal composition development test repairs that specific qualification mechanism: a graph-attested candidate can be used as an algebraic operand, its verified child retains parent-digest provenance, and both D4 `0200→0202` and Loopover `0015→0026` selected training fixtures produce a qualified source proposal. This is bounded mechanism evidence from selected pairs, not evidence of broad independent-goal learning; the prior zero-qualification pairs remain valid. The request-counter extension atomically enforces both global and per-request attempt ceilings. Validation scores are descriptive, and neither approval nor action receipt was created. Raw hashes, exact candidate digests and allocation exclusions are in [`COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md`](COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md). Four-arm learners, complete cumulative resource matching, candidate-specific authorization, preregistered held-out efficacy and all L1–L7 capability closures remain open.

The P22 E2 analyzer now rejects overlapping training, validation and evaluation identities and reports development provenance as `DEVELOPMENT_ONLY`, never `ATTESTED` without held-out runtime evidence. Its five focused tests and standalone self-check pass. The runner, complete resource measurements, candidate-specific approved lineages, standalone preregistration and held-out evidence remain open; no capability level closes.

P22 resource snapshots now bind canonical training-node payload bytes and declare measurement coverage instead of implying unavailable quantities are zero. Fresh eight-task four-arm diagnostics at draws 0278–0285 (validation 0378–0385) completed both families: all D4 arms solved 3/8, all Loopover arms solved 1/8; D4 produced five invention-only and four full candidates while Loopover produced none. Resource vectors differ. Retrieval, proposal/verification work units, model refinement, definition/decoder cost, approval labor and rollback costs still lack direct instruments. The raw hashes and single-host timing/RSS limits are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). These remain development diagnostics with no approvals, receipts, held-out access, efficiency claim or capability closure.

Resource snapshots additionally break down ThinkingBudget costs by requester kind and retain proposal, qualification, candidate-validation and approval event counts. These counters do not resolve work units or human cost, and a missing validation counter now makes exact resource comparison incomplete. The same consumed development draws were replayed to verify the expanded schema; the outcomes were identical and are not treated as a fresh sample. Exact digests are in the development report. P22.E2 remains gated on working Loopover proposal/learning comparisons, complete resource instrumentation and authorized checkpoint lineages.

The P22 E2 analyzer now also requires a named source for every declared resource value and rejects partial event counts as if they were measured work units. Its self-check covers absent measurement evidence and incomplete coverage. This forces the future runner to provide measured values or retain a structural failure; no held-out artifact exists or is authorized.

**P22 exact simulated-adoption update (2026-10-23):** Following user approval of the two exact training-only candidate bindings, D4 `#752` and Loopover `#5761` each completed one guarded finite-simulator action with one consumed approval and one verified native receipt. The exact digests, witnesses and raw receipts are in [`COGNITION_P22_V2_CANDIDATE_APPROVALS_20261023.md`](COGNITION_P22_V2_CANDIDATE_APPROVALS_20261023.md). This closes the candidate-approval mechanism gate for those two single actions only. It does not provide lineage-generation evidence, a four-arm matched efficacy result, complete approval-effort accounting, preregistration, held-out evidence or any L1–L7 capability closure.

The native resource module now has one adapter that emits analyzer-ready values, per-field source names, and measured/partial/unavailable statuses from a digest-verified snapshot. It enforces that cumulative checkpoint primitive work cannot be below observed snapshot work. The focused resource/analyzer suite passes 12 tests. Several resource dimensions remain unavailable, so this is a provenance-safe conversion path, not E2 readiness.

The proposal probe now retains a no-candidate-first-task outcome instead of dropping the entire run. Fresh distinct-goal D4 draws 0286/0287 yielded one qualified candidate (4/8 descriptive validation) and one unqualified candidate; Loopover's first task yielded none, and its second-task candidate remained unqualified (0/8). Zero approvals and receipts were created. The full five-test P22 probe module passes, including the per-request ceiling extension. These are small mechanism probes only; the exact raw artifacts, hashes and consumed splits are in the P22 development report. This does not establish qualification reliability or efficacy.

Two more distinct-goal pairs per family reinforce the limitation: D4 qualified one candidate on 0290/0291 but it scored 0/8; D4 0288/0289 did not qualify, and neither Loopover pair qualified. Across these three fresh pairs, the diagnostic count is 1/3 D4 and 0/3 Loopover, with no approvals or receipts. The observations do not estimate qualification rates or establish efficacy. Exact raw artifacts and consumed splits remain in the P22 development report.

The proposal-probe CLI now separates per-request search from its fixed global 30,000-attempt ceiling. A fresh Loopover pair at 20,000 attempts per request produced one candidate, which remained unqualified and scored 0/8; a preceding run that set both global and per-request limits to 20,000 exhausted its global budget on the first task and is retained as confounded evidence. Neither run created approvals or receipts. These results diagnose proposal availability under search limits only; they do not establish independent-goal learning or benefit.

The current broader P22 regression bundle passes 98 tests across inference, native checkpoint/causal paths, cognition-profile integration and analyzer coverage. The exact E2 bundle passes 41 tests; the native proposal-probe module passes 5. All are mechanism/schema evidence. The matched Loopover learner, remaining resource instruments, approved multi-generation lineages, preregistration and held-out results remain open.

The current shared cognition gate also retains the inherited classifications: baseline verifier 4 held RED, zero newly GREEN and zero NEW RED; suite sweep 16 GREEN, 2 RED, one 420-second `NOT_ESTABLISHED` timeout, and one fully skipped file. The report records HEAD `b19b904f` while the worktree was dirty, so it is a current working-tree result rather than a clean-commit attestation. The raw artifact hash is in the build plan. These results do not indicate new P22 regressions or resolve the inherited failures.

**Resource and P22.03 verification refresh (2026-10-23):** The P22 snapshot was corrected to count the full canonical graph, including edges, and now records node/edge counts plus the native graph-memory estimate. The two isolated-worker four-arm artifacts were regenerated and remain resource-unequal; their exact bytes, hashes and measurement limits are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). Thus graph-memory measurement is available as a substrate estimate, while allocator-wide memory remains unavailable. Checkpoint capture now accepts caller-measured native rule steps, model calls and peak RSS, binding them in the checkpoint's digest-protected resource snapshot; descendant captures reject regressed cumulative rule-step, model-call or search-reservation counters. Strict scoring preserves the counters. The P22.03 named verification command passes 25 tests. These tests establish fixture-level native checkpoint and ablation behavior only. There are still no externally authorized candidate adoptions or cross-family live checkpoint lineages, no working matched four-arm efficacy comparison, and no preregistered/held-out P22 result. All L1–L7 levels remain open.

**P22 development candidate-score refresh (2026-10-23):** All proposals from each native four-arm development graph are now scored nonactionably on the same disjoint v2 validation draws 0350–0357, with per-expression outcome rows retained and native evaluation counts added to resource accounting. D4 proposals scored 1/8 in this selected eight-world panel; Loopover produced none. There was no approval or simulated execution. These new diagnostic draws are excluded from preregistration. The raw artifact hashes and duplicate-expression details are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md); this does not establish candidate generalization, matched treatment effects, or capability closure.

**P22 higher-ceiling development audit (2026-10-23):** With a common 10,000-attempt ceiling on two v2 training tasks, native invention-only and full arms each produced candidate proposals in both D4 and Loopover. Every arm solved 0/2; unapproved candidate validation yielded D4 0/2 and 1/2 per candidate, and Loopover 0/2. No approvals or receipts were created, and resource vectors differed. This confirms Loopover proposal availability is sensitive to search ceiling and invalidates treating its zero proposals under the 64-attempt cap as a stable comparator result. The two-world 10,000-ceiling run remains a development diagnostic; it does not establish benefit, working held-out comparators or a frozen budget. Exact artifacts and hashes are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). Training 0260–0261 and validation 0360–0361 are consumed and excluded from later preregistration; all capability levels remain open.

**P22 eight-task development audit (2026-10-23):** A larger common-ceiling panel confirms the native invention-only/full proposal and nonactionable validation paths run in both v2 families. All arms scored D4 5/8 and Loopover 2/8 on training; three unique D4 expressions scored 1/8, 2/8 and 0/8, and Loopover expressions scored 0/8 on the fresh eight-world validation panel. No approvals or receipts were created, and resource vectors remain unequal. These are training/development diagnostics only; the result supports adapter execution but no improvement benefit, approved lineage, efficiency or capability closure. The exact raw artifacts and hashes are in [`COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md`](COGNITION_P22_FOUR_ARM_DEVELOPMENT_20261023.md). Allocations 0270–0277 and 0370–0377 are consumed and excluded from preregistered use.

**P22.01 inference reconciliation (2026-10-23):** The contract and estimator now align on a minimum point slope of 0.05 per generation and phase-wide Holm correction over each family's final-gain and slope tests. The cluster bootstrap reports fixed 10,000-draw one-sided zero-effect p-values, 99% lower bounds and adjusted p-values; flat/ceiling effects remain zero. The estimator requires exactly generations 1–3, fixes the practical thresholds and α, and passes 11 tests, including positive trend passage and null/ceiling failure. The full P22.E1 verification bundle passes 93 tests. This repairs the written inference gap before freeze and does not change the P22 evidence status: no approved independent-goal lineages, preregistration, or held-out result exists, and all capability levels remain open.

**P22 resource and split audit refresh (2026-10-23):** Four-arm development snapshots now include digest-verified per-rule native work totals, with unmatched rule identities explicitly marked; checkpoints preserve cumulative totals and reject descendant regressions. The analyzer requires the native term-evaluation field with a named source, plus disjoint training, selection, validation and evaluation blocks across all families. The exact E2 test bundle passes 42 tests and the analyzer self-check passes. These changes improve measurement and structural validation only. Four-arm development resource vectors remain unequal, the exact cross-goal candidates remain unapproved in the artifact ledger, and no three-generation independent-goal checkpoint lineage, standalone preregistration, or held-out P22 result exists. All L1–L7 dispositions remain open; no capability claim is elevated by these diagnostics.

**P22 exact-binding audit (2026-10-23):** Training-only native graph reconstructions reproduce both selected cross-goal candidate digests and full approval bindings while leaving validation empty and creating no approval or receipt. The authoritative Loopover digest is `f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d`; a transcribed alternate value was corrected in the approval packet. The complete five-test proposal module passes with this reconstruction path. This verifies reconstruction of two consumed development candidates only. It does not constitute candidate authorization, an approved lineage, or independent-goal efficacy; all L1–L7 dispositions remain open.

**P22.E2 runner status (2026-10-23):** The development runner now exercises the loaded native evaluator, disjoint deterministic family/split seeds, checkpoint manifest checks and four structural controls. Runner/analyzer self-checks pass, as do the focused E2 verification tests. This does not establish any capability level: no candidate-specific simulated-adoption approval or multi-generation cross-family checkpoint manifest exists, and remaining resource dimensions/cost matching are incomplete. P22 preregistration and held-out efficacy remain `NOT_RUN`; L1–L7 remain open.

**P22 operation-cost attribution update (2026-10-23):** Digest-bound per-rule term evaluations are now grouped into disjoint native retrieval, proposal, verification, refinement, definition-decode, and rollback categories, with explicit source names and complete-identity requirements. Human approval cost remains unmeasured; approval event counts are not treated as work. The focused P22 E2 bundle passes 54 tests. This does not change capability dispositions or P22.E2/E3 status; candidate-specific approvals, actual checkpoint lineages, and held-out results are still absent.

**P22 development resource audit (2026-10-23):** Recomputed six disjoint native operation-cost categories from the complete, digest-bound per-rule counters in the existing D4 0304/0305 four-arm diagnostic. The category vector (retrieval/proposal/verification/refinement) is 40/20/92/8 unchanged, 140/64/112/28 adaptive-only, 200/24,635/7,724/20 invention-only, and 260/24,659/7,736/40 full; definition decode and rollback are measured zero for this artifact. This is a read-only derived report over the archived development snapshot, not a new draw, raw artifact rewrite, resource match, efficacy result, or capability closure. Approval event counts still do not measure human approval cost.

**P22 control-lineage status (2026-10-23):** Added a native digest-bound passive descendant checkpoint for unchanged/adaptive control arms, with no adoption approval or world receipt. Manifest validation enforces unchanged control expressions and uninterrupted parent links; invention/full descendants retain the candidate-specific approval and receipt boundary. Runner development checks cover all 24 parent links and a tamper. The P22 E2 focused bundle passes 55 tests. This improves evaluation readiness but does not create experimental lineages or alter any capability disposition.

**P22 manifest validation refresh (2026-10-23):** A synthetic digest-valid manifest test now exercises all eight family/arm roots and all 24 generation links, including passive no-approval control chains and approved invention/full chains. It rejects changed passive expressions and missing invention-arm approval/receipt bindings. The P22 E2 bundle passes 56 tests. No actual approved candidate lineage or held-out result exists; all capability dispositions remain unchanged.

**P22 passive-lineage resource guard (2026-10-23):** Passive unchanged/adaptive descendants preserve digest-bound runtime and per-rule work counters and reject regressions, covered by the 56-test focused E2 bundle. This closes a checkpoint-accounting mechanism only and does not alter the missing approval-dependent invention-lineage or held-out classifications.

**P22 sealed-allocation guard (2026-10-23):** The runner performs full per-checkpoint resource-source and ceiling validation before it materializes held-out worlds, including exact isolated wall-time coverage. A regression confirms partial approval-cost instrumentation fails at preflight. The P22 E2 focused bundle passes 57 tests. This prevents resource-incomplete manifests from consuming held-out data; P22.E2 remains open pending complete instruments and candidate-specific invention approvals.

## Current plan status refresh (2026-10-23)

P20's earlier integration note remained pending while its combined runner and
scored explanation panel were unfinished. The later frozen P20 E3 run records
200/200 explanation reconstruction/adoptions at 100% fidelity, and the four
named cognition-on integration tests pass. This closes P20.04 and E1 for the
bounded declared protocol; the transfer primary remains `FAIL`, and no L-level
disposition changes. In the current dirty checkout, a new P20 development run
reports `DEVELOPMENT_ONLY` because the attested build inputs are modified; its
analyzer correctly refuses to label that run attested. The historical frozen
E3 provenance remains the authoritative evaluation record.

The two exact P22 candidates now each have one user-authorized simulated
action, one consumed approval and one verified receipt, as documented in the
candidate packet and raw artifacts. This supersedes older development notes
that said no live candidate approval had been consumed. It does not create a
multi-generation lineage, resolve human approval-effort measurement or
resource mismatches, or authorize any later-generation action. P22.E2/E3 and
all L1–L7 capability closures remain open.

The P22 resource adapter now prospectively measures candidate-review effort
as reviewer-reported seconds and keeps missing historical values partial. The
previous two approvals remain unmeasured; this instrumentation does not
authorize another action or supply an experimental lineage. P22.E2 is still
not admissible until new fully measured checkpoint lineages and every other
frozen resource/control prerequisite are present.

The first fresh training-only probes after adding this instrument used D4 and
Loopover draws 0400/0402. Each produced a candidate but neither qualified it;
both had empty validation allocations and zero approvals/receipts. This is
additional development evidence only and does not alter capability status.

The four-arm development adapter now records arm wall time in its
digest-bound resource snapshots and includes it in cross-arm comparison. Fresh
D4 and Loopover training-only panels on draws 0500–0503 measured all declared
resource dimensions, but realized vectors remained unmatched. All arms solved
2/4 tasks in these small panels; D4 invention-only/full produced two/one
candidates and Loopover produced none. The panels had no validation worlds,
approvals, receipts, or held-out access. This adds instrumentation evidence
only and leaves L1–L7 and P22 efficacy dispositions unchanged.

A repeated native-rule audit then exposed and fixed namespaced rule-ID to
local-index attribution in cumulative snapshots. New digest-bound captures use
native rule-work schema v2 with both IDs; historical v1 snapshots remain
verifiable and unchanged. Two fresh graph stores now retain complete identity
coverage in one process, and the exact synthetic generation-zero/generation-one
checkpoint regression requires complete coverage. The combined affected P22
resource, checkpoint, four-arm and synthetic adoption modules pass 33 tests.
This repairs a measurement defect without changing capability or efficacy
status; genuinely partial capture remains inadmissible for E2.

A separate Loopover training-only run on draws 0504/0505 ended with no
candidate after 5,000 attempts per request. Its raw result has digest-bound
native work at the probe level but omitted it from the resource snapshot, so
the snapshot is not eligible for resource matching. The non-adoption probe path
now carries that work and runtime counters into future snapshots; a focused
snapshot regression, sequential-capture regression, and exact checkpoint test
pass together; runner/analyzer self-checks pass. The raw result is preserved
unchanged, and this diagnostic does not alter L1–L7 or P22 efficacy status.
The approved checkpoint path also now refuses nonempty validation allocations,
keeping candidate reconstruction and adoption evidence strictly training-only.

The P22 source closure now hashes the proposal-training adapter and both
development CLI entry points. A provenance read confirms coverage. The
attestation was `DEVELOPMENT_ONLY` while these source changes were uncommitted;
the later clean-source build is recorded below.

P22 checkpoint capture now preserves and digest-binds the full canonical native
graph, with exact restoration into a normally booted agent. Strict scoring
resolves the process from that graph and checks the compact manifest. This is
checkpoint and finite-process evaluation infrastructure; no full learner
continuation or independent-goal efficacy has been demonstrated. P22.E2/E3 and
every L1–L7 closure remain open.

The training-only P22 probe can now restore an exact parent checkpoint and
continue cumulative runtime and per-rule accounting across graph stores. A
development regression exercises restored training, store-namespaced counter
merge, and the existing candidate-bound adoption path. This closes a
continuation mechanism gap only; no new generation was authorized or adopted,
and no independent-goal improvement or held-out outcome is established.

A fresh Loopover v2 training-only record now includes a fully measured,
digest-valid generation-zero checkpoint on two distinct goals. Generic search
did not produce an independently qualified candidate, so the record has no
adopted child. It adds reusable root evidence only; P22 efficacy and every
L1–L7 closure remain open.

The strict P22 checkpoint scorer now resolves active process parameters from
the digest-bound native graph and checks them against the manifest before
native execution. A captured ancestor and an approved child produce different
scores on the same derived development control world (0 versus 1), and the
P22.03 verification command passes 27 tests. The component-ablation regression
now uses an actual captured ancestor and its approved child rather than
hand-built permutation records. This replaces the earlier manifest-parameter-
only execution path and adds a bounded expression-path dependence control.
The control is still one derived development task, not an independent-goal
effect, and no matched four-arm result exists; therefore P22.E2/E3 and all
L1–L7 capability closures remain open.

The implementation bundle was committed as
`c94aa1c8649dedb4e13d84e85df38df3ca912e5f`. After rebuilding the extension
from that source, strict P22 provenance reports `ATTESTED` with an empty issue
list. The runner/analyzer self-checks pass, as do the 94-test affected Python
bundle and the full repository Rust test wrapper. This removes the dirty-source
obstruction to E2. It does not supply approved multi-generation cross-family
lineages, full approval/resource measurements, frozen per-checkpoint wall-time
records, a standalone preregistration, or held-out results; all L1–L7
dispositions therefore remain open.

A fresh continuation restored the measured Loopover generation-zero graph and
ran on disjoint training draws 0513/0514. Graph, checkpoint, resource, and
cumulative rule-work digests verify. The inherited 30,000-attempt global
ceiling had only 10,000 remaining after the root's 20,000; the first new task
used that remainder and the second received none. The candidate remained
unqualified, with zero approvals or receipts. This confirms cumulative budget
enforcement across restoration but creates no learned child or efficacy
result. The next continuation must reserve enough of the inherited ceiling
for both tasks; all P22 and L1–L7 dispositions remain open.

A bounded graph-wide attempt-cap override is now explicit in the training
continuation API and CLI. It records the parent cap and requested cap while
retaining previously charged attempts. With a requested 100,000 cap, both
fresh Loopover continuation tasks received 10,000 attempts; cumulative work
reached 40,000 from a 20,000-attempt root. The candidate nevertheless remained
unqualified, and no approval or receipt was created. This separates budget
starvation from candidate qualification for these development draws; it does
not establish learning or efficacy. All P22 and L1–L7 dispositions remain
open.

A registered-world native checkpoint panel now restores four distinct D4
policy graphs and evaluates them on one common, fresh training task under the
same cumulative primitive ceiling. All four solve the single task, with
cumulative primitive work 2; digest-bound native rule evaluations differ by
arm. This advances checkpoint continuation beyond direct expression scoring,
but one selected task cannot establish benefit, and the scoring worker lacks
per-arm isolated wall-time/RSS. Resource matching and efficiency remain
unestablished, as do candidate-authorized multi-generation lineages,
preregistration and held-out P22 results. L1–L7 dispositions are unchanged.

The checkpoint panel has now been exercised on both registered v2 families.
D4 scored all four arm snapshots 1/1 on one training task with cumulative
primitive work 2; Loopover scored 0/1 in every arm, with cumulative primitive
work 2 for unchanged/adaptive-only and 130 for invention-only/full. This is
training-only, one-task-per-family evidence: it demonstrates native
checkpoint continuation across both domain sizes and exposes unequal realized
work in Loopover, while establishing no efficacy. Isolated scoring wall-time
and RSS remain missing, so P22 resource matching, approved descendant lineages,
preregistration, and held-out results remain open.

The four-arm root-panel scorer now runs every checkpoint/world cell in an
isolated process and records cumulative wall time and peak RSS. Both D4 and
Loopover pilot panels have complete measured-resource coverage and valid
per-rule work digests, but their actual vectors remain unmatched and neither
supports an efficiency comparison. The isolated panels are one training task
per family with no effect evidence, and approved descendant lineages remain
absent. P22 preregistration/held-out status and L1–L7 closures are unchanged.

The first isolated checkpoint outcomes are now marked preliminary and
superseded: their evaluator directly created `SolveTask`, bypassing the
restored native curriculum policy in adaptive arms. The corrected evaluator
submits the same curriculum evidence to each arm and lets enabled native
curriculum rules create and dispatch the task. On a fresh common D4 training
draw, all four arms solve 1/1; on a fresh common Loopover training draw, all
four solve 0/1. All contract dimensions and work digests verify, while actual
resource vectors remain unmatched. These are single-world training plumbing
checks only. They establish neither adaptive benefit nor learner efficacy;
approved descendant lineages, resource matching, preregistration, and held-out
results remain open, as do every L1–L7 closure.

The corrected generation-zero roots were also scored on 12 shared training
draws per family. D4 solved 4/12 and Loopover 1/12 in every arm, producing
exactly flat paired scores across unchanged, adaptive-only, invention-only,
and full root conditions. Some worlds had unequal cumulative primitive work,
and resource vectors were unmatched despite complete measured coverage.
These selected development panels demonstrate common-world continuation and
preserve a flat baseline; they do not test learned descendants, establish
efficiency, or support efficacy. All approvals and receipts added were zero.
P22 approved-lineage, preregistration and held-out gates remain open, and
L1–L7 dispositions are unchanged.

The resource audit identified substantial realized-work differences despite
complete measurement coverage and shared declared ceilings: median native
term evaluations across the four arms span 4,280–41,023 on D4 and
23,015–47,069 on Loopover. Median primitive work also differs by treatment
arm. Thus the root panels support flat score comparisons under measured but
unmatched work; they do not support efficiency claims. An admissible next
comparison requires a resource protocol frozen before allocation, alongside
approved descendant checkpoints.

The held-out runner has also been corrected to score restored native learner
graphs through the common solver task path. Evaluation tasks are isolated by
world, marked evaluation-only, and excluded from training-exposure accounting;
the analyzer rejects budget overruns and any newly created approval or world
receipt. Synthetic-fixture tests and runner/analyzer self-checks pass. The
registered P22 freeze is still absent, so the corrected held-out path has not
read or scored any registered held-out world. This closes a runner wiring
defect, not the P22 lineage or efficacy gates; L1–L7 remain unchanged.

A final worker-timing audit moved the isolated wall-time start to before fresh
learner boot, so future per-cell timing includes boot, restore, and scoring.
Earlier isolated root panels undercounted that interval; their outcomes and
other measured fields remain valid, but their worker wall-time values are
superseded for timing. A fresh four-world training panel in each family
completed 32/32 arm-world cells with valid digests, respected primitive
ceilings, zero approvals/receipts, and 1/4 solved in every arm. Realized
resources remain unmatched. This improves measurement scope without adding
descendant or efficacy evidence; P22 lineage, freeze, and held-out gates and
all L1–L7 dispositions remain open.

The P22 runner now has a direct freeze-order regression: when standalone freeze verification fails, both held-out world generators remain unreachable. The focused suite passes 52 tests and runner/analyzer self-checks pass. This strengthens the held-out access guard only; it does not satisfy the pending candidate authorization, resource matching, preregistration, or registered held-out evaluation gates. No P22 held-out world was accessed, and L1–L7 dispositions remain unchanged.

The candidate-bound adoption mechanism and resource accounting were re-verified on the current checkout (24 tests passed). The synthetic test fixture exercises one exact approval, guarded simulator transition, verified receipt, reviewer-time charge, and parent-linked child checkpoint. It does not approve or execute the pending live candidate request; P22 descendant-lineage and evaluation gates remain open.

The freeze-order regression now also guards learner construction, confirming that a rejected freeze prevents both learner boot and held-out generator access. The focused test passes; no registered evaluation data was read.

The P22 analyzer now enforces the written resource-matching boundary: score thresholds alone cannot close the registered phase result. Any unmatched measured arm/world vector leaves the registered claim `NOT_ESTABLISHED` and labels the observed held-out scores `CAPABILITY_ONLY`; score-threshold and match diagnostics remain separately visible. A synthetic held-out regression covers this case. The focused P22 bundle passes 53 tests with runner/analyzer self-checks passing. No registered held-out allocation was accessed, and L1–L7 dispositions remain unchanged.

After the P22 claim-gate change, native runtime provenance remains `ATTESTED` with no issues. The current analyzer fingerprint is `dd737d2bbf2561b2d3279e205ad64c11c809d3c6e227b3b0345fe0bf64cf26af` and source bundle is `da5c6f151af018bd277020e39c9a341eb8ff999ff6617335975f1c71017759bd`; the loaded extension and build receipt remain bound to their prior verified digests. A future standalone freeze must bind these current values.

The pending D4 candidate request now has a machine-readable binding and guarded CLI entry point. It requires the exact expression digest, explicit execution flag, reviewer-reported seconds, distinct training-only reconstruction, and a fixed request-bound output path. Negative CLI guard tests pass; no action was executed, and the candidate-specific authorization gate remains open.

Current P22 provenance after the approval CLI addition remains `ATTESTED` with no issues. Runner SHA-256 is `6b5766a5468decc36eb075e824d52d69834b8f2709a2544a197aee14bc086d52` and source-bundle SHA-256 is `0826ac11b7415762a2246c83a1ad865c3ea594621803f9946787fb4aa4c0ffca`; native extension and build receipt remain unchanged. Any future standalone freeze must bind this current runner/source bundle.

The earlier exact D4 and Loopover simulated adoptions establish verified actions only; their raw artifacts contain no generation-one checkpoints. They cannot be reused as lineage evidence. The pending D4 request can create at most its named D4 generation-one checkpoint after exact authorization and review-time reporting; Loopover and later-generation lineage gates would remain open.

A complete recursive inventory of retained P22 result artifacts found no generation-greater-than-zero checkpoint snapshots. Existing development outcomes retain generation-zero roots and scoring reports; historical adoption receipts cannot reconstruct the missing native graph snapshots. Descendant lineage remains unestablished.

The approval CLI parses and hashes the same binding bytes; its two rejection-path tests pass. Updated source-bundle SHA-256 is `8aafcbf1e7e2f16f1b11287b2fbd54d7b75d9fd12fca64bdc04cbf3020429c6f`, with native runtime still attested and clean. No adoption was executed.

The candidate-action CLI durably reserves its one-shot output before any probe work; interrupted attempts cannot be retried under the same request. Three CLI guard tests pass. Native runtime remains attested with no issues; updated P22 source-bundle SHA-256 is `080c96bfb05da93064ab8d5d88d36464be8fac8c8dcb64fc39f6607802a463f2`. No action was run.

The integrated P22 regression bundle now passes 56 tests, including the analyzer resource-match gate and guarded approval CLI. Runner and analyzer self-checks pass; the runner reports no held-out access. Native runtime remains attested and clean. This verifies implementation and controls only; authorized descendant checkpoints, a matched panel, standalone freeze, and held-out evidence remain outstanding.

The exact D4 candidate request was then consumed under its named digest with reviewer-reported review time of 12 seconds. One candidate-specific human approval, one guarded training-simulator transition and one verified receipt produced a digest-valid generation-one checkpoint linked to its generation-zero ancestor. Both checkpoint digests and the parent link verify; no validation or held-out world was used. The raw result is `p22_approved_candidate_d4_0406_0407.json` (SHA-256 `7435894f1b65c8c62d0d7b401f0db73f1513372ee24f66dd2c01b552aafcab9b`). This closes only the named D4 generation-one action. Loopover and later generations still lack authorized checkpoint children, arm resource vectors remain unmatched, and P22 preregistration/held-out evaluation remain `NOT_RUN`; all L1–L7 levels remain open.

Fresh development continuations did not yet extend that lineage. Loopover search on distinct draws 0550–0557 left every proposed candidate unqualified, including a restored generation-zero continuation; D4 continuation from its generation-one checkpoint on distinct draws 0560/0561 also produced no qualified generation-two candidate. These training-only runs created no new approval, receipt, or descendant checkpoint and accessed no validation/held-out allocation. The exact artifacts and hashes are recorded in the P22 development report. P22 remains `NOT_ESTABLISHED` for cross-family multi-generation efficacy, with all L1–L7 dispositions open.

A later D4 continuation on distinct training draws 0562/0563 produced a two-trial-qualified generation-two proposal, but the exact native effect is identity. It remains unapproved and cannot count as improvement; no generation-two checkpoint exists. A candidate-bound request is prepared against the verified generation-one parent and explicitly scopes any approval to one identity transition. The restored-parent CLI path verifies the source artifact, checkpoint digest, graph and frozen ceilings before reserving an output. A Loopover continuation on draws 0564/0565 still yielded no qualified candidate. No validation or held-out allocation was accessed, and all L1–L7 dispositions remain open.

A further Loopover development pair on draws 0566/0567 produced one unqualified candidate and only residual trial outcomes, without approval or receipt. It supplies no generation-one lineage. The raw artifact and digest are retained in the P22 development report; no validation or held-out data was accessed.

The exact D4 identity candidate from draws 0562/0563 was subsequently authorized for one transition with 12 reviewer-reported seconds. Approval `#16727` and verified receipt `#16730` created a digest-valid generation-two checkpoint linked to the verified generation-one parent. Its permutation leaves the world state unchanged, so it is not an improvement and does not support a capability-level increase. The raw result and hash are recorded in the P22 development report. No validation or held-out allocation was accessed. Cross-family multi-generation efficacy, resource matching, preregistration, and the L1–L7 evidence dispositions remain open.

A fresh D4 continuation from that generation-two checkpoint on distinct training draws 0572/0573 produced three candidates, none qualified on the new goals; both tasks stopped as stuck after 5,000 attempts. A preceding pair 0570/0571 was rejected before learner boot because its goals matched. Both records are retained and documented in the P22 development report. The training-only ceiling increase did not reset cumulative attempts, and no new approval, transition, validation or held-out access occurred. The D4 lineage still lacks a generation-three candidate; Loopover still lacks a generation-one checkpoint. No capability level closes.

The D4 continuations on 0572/0573 and 0574/0575 were ceiling-censored because checkpoint restoration kept the parent's per-request limit of 5,000 despite larger requested limits. The bug is fixed and a focused restored-policy regression passes; a fresh 0576/0577 continuation is running with the corrected policy. The censored outcomes do not establish failure at the larger budgets and add no approved lineage. Capability levels remain open.

Loopover's higher-ceiling training probe on distinct draws 0568/0569 completed with both tasks stuck at 30,000 attempts. Its sole candidate had zero independent-goal qualification witnesses; there was no approval, action or receipt. This adds evidence that the tested search budget has not yet yielded a qualified Loopover descendant, but it is not a registered efficacy result. No validation/held-out data was used and all capability levels remain open.

After correcting restored per-request search limits, the complete P22 development module passes 10 tests; runner and analyzer self-checks pass, including `heldout_accessed=false` and negative lineage/resource controls. Current native provenance at commit `68ecf662cd5f7c26badb93ebbe9cdba8d0dba1db` is `ATTESTED` with no issues; its source-bundle SHA-256 is `e4964b4552ac17e0e1cca0301d0c1ee9be951981ff971bfc4ed50538a726ef73`, with exact component hashes recorded in the build plan. This supports mechanism integrity only; the registered multi-generation efficacy claim remains unestablished.

The corrected D4 continuation on draws 0576/0577 actually used its requested 20,000 attempts per task but produced no candidate with two independent-goal witnesses. This closes the ceiling-instrumentation bug and establishes a further negative training-only qualification result; it does not create an approved descendant or an efficacy estimate. A D4 0582/0583 search and Loopover 0580/0581 probe remain underway. Capability levels remain open.

Loopover draws 0580/0581 used their 10,000 per-request ceilings but produced no qualified candidate: the sole candidate had zero independent-goal witnesses, with only residual attempts on the second task. No approval or action occurred. D4 0582/0583 and a higher-ceiling Loopover pair 0584/0585 are in progress; neither has validation or held-out access. The cross-family lineage and all L1–L7 evidence dispositions remain open.

The Loopover probes on 0584/0585 and 0586/0587 were interrupted before a native result was written; PID checks confirm both processes are gone. Their explicit interruption records preserve the unknown outcome, so these draws are consumed and excluded without being classified as qualification failures. No capability disposition changes.

D4 continuation on distinct draws 0582/0583 used the corrected 30,000-attempt request ceiling but still produced no candidate qualified on both goals. The raw evidence is retained; no new approval, action, validation or held-out access occurred. D4 generation three remains unavailable, so the cross-family multi-generation criterion and capability dispositions remain open.

Loopover draws 0588/0589 exhausted their 30,000-per-request, 60,000-global training-search ceilings without a candidate independently qualifying across both goals. Candidate `#30761` had residual trials only on the second draw. This adds no approved Loopover descendant and changes no capability disposition; fresh training draws at a higher global ceiling are the next development probe.

The follow-up on draws 0590/0591 used the runner's maximum 120,000 global ceiling and again produced no qualified candidate. Candidate `#827` had 24 funded but residual trials on the second goal. Loopover still has no approved descendant, and no capability disposition changes.

D4 continuation from the digest-valid generation-two checkpoint on distinct draws 0592/0593 used the raised 120,000 global ceiling and 30,000 attempts per request. Candidate `#16769` had mixed outcomes on the second goal and no independent-goal qualification across both new tasks. The D4 generation-three gate remains unmet; no new approval, receipt, validation, or held-out access occurred.

A repeated D4 continuation on fresh draws 0594/0595 also ended stuck at 30,000 attempts per request. Its identity candidate had residual trials only on the second goal, leaving the generation-three gate unmet. No capability disposition changes.

Loopover draws 0596/0597 used 60 rule-processing ticks at the 30,000-per-request ceiling. The sole candidate had 24 funded residual trials on the second goal, with no independent-goal qualification. Increasing ticks did not change the qualification outcome in this diagnostic; Loopover remains without an approved descendant.

The development CLI now supports an artifact-hash- and checkpoint-digest-bound training-only continuation without adoption approval. Its 16-test focused regression bundle passes, and a low-budget end-to-end smoke restored the D4 generation-two checkpoint with no new action, receipt, validation, or held-out access. This improves reproducibility only; capability dispositions remain open.

A second Loopover 60-tick probe on draws 0602/0603 repeated the prior result: 24 funded residual trials on the second goal and no independently qualified candidate. Extra rule-processing ticks did not resolve the current training transfer failure; no capability disposition changes.

The Loopover training probe now supports up to eight pairwise-distinct goals. On four fresh goals 0609–0612, the candidate was tested on all three later goals and produced 72 residual trials without qualification. No approved descendant or capability disposition changed.

An eight-goal Loopover panel on 0613–0620 used the full 80,000-attempt ceiling. One candidate had 168 residual trials across seven later goals, with no qualification. The current proposal search therefore still lacks a Loopover generation-one descendant; capability dispositions remain unchanged.

**P22 continuation update (2026-10-23):** Five distinct D4 training goals
0635–0639 yielded candidate `#26693` with a non-identity effect and two
qualified pairs. Exact adoption request `COGNITION_P22_APPROVAL_REQUEST_D4_0635_0639`
is pending. Until explicit approval and a verified receipt produce a
checkpoint, this is proposal qualification evidence only; no capability
disposition or held-out claim changes.

The Loopover eight-goal follow-up on draws 0643–0650 again produced no
independent-goal-qualified candidate after 80,000 attempts; all 168 transfer
trials were residual. This is additional negative development evidence, not a
held-out result, and does not change any capability disposition.

A fresh eight-goal Loopover diagnostic with 60 rule-processing ticks (draws
0651–0658) exhausted the 80,000-attempt ceiling. Two candidates were minted,
but neither received a first independent-goal trial. This adds no lineage or
capability evidence and leaves the disposition unchanged.

A read-only same-world Loopover checkpoint panel on draws 0659–0662 scored the
four generation-zero arms at 1/4 each. Resource instrumentation was complete,
but observed resource equality failed. The result is development-only and
supports no efficacy or efficiency claim.

The D4 same-world development checkpoint panel on draws 0664–0667 gave all
four generation-zero arms identical per-world outcomes (3/4 solved). Observed
resource equality failed on one world; no efficacy, efficiency, or capability
level is established.

The exact D4 generation-one/generation-two lineage pair scored 2/4 on the same
four fresh training worlds under the corrected frozen native scoring profile;
per-world scores were identical. The child had higher cumulative historical
work. This establishes no improvement or efficiency claim and is not
held-out evidence. The initial budget-control failure was fixed and excluded
from interpretation.

Loopover received a fresh four-goal panel at 30,000 attempts per task and the
120,000 global ceiling. Candidate `#30761` had 72 residual trials over three
independent goals and did not qualify; all four tasks were stuck. This extends
the negative training-only evidence but does not establish or revise any
capability level.

A bounded two-held-process extension increased native Loopover transfer trials
to 156 on one fresh independent goal, but all remained residual and no
candidate qualified. This additional training search establishes no new
capability level; Loopover transfer and P22.E2–E3 remain open.

A follow-up used the two-held-process grammar across seven fresh independent
Loopover goals (draws 0682–0689), producing 1,092 residual transfer trials for
one candidate and no qualification. All eight training tasks remained stuck
after 80,000 reserved attempts. This larger panel still produced no Loopover
descendant or efficacy estimate; it does not change any L1–L7 disposition.

A rotated Loopover source-goal probe on fresh draws 0690/0691 produced no
candidate on its first task after 20,000 reserved attempts. This proposal
generation miss adds no transfer or capability evidence; all L1–L7
dispositions remain unchanged.

A second rotated Loopover source on distinct draws 0692/0693 produced a new
candidate, but all 156 transfer trials on its independent goal were residual.
This adds no qualified descendant or capability evidence; L1–L7 remain open.

A second fresh Loopover source pair (0694/0695) produced another candidate,
but its 156 one-step/two-step trials on the independent goal were all
residual. No capability disposition changes.

An order-complete two-held-process grammar was added, but its first four-goal
Loopover panel produced no candidate on the source task; a later candidate had
no independent trials. This is no transfer failure estimate and does not
change any L1–L7 disposition.

An order-complete Loopover transfer probe on distinct draws 0700/0701 exercised
all three placements of an acquired candidate around two held processes. All
420 independent-goal trials were residual and no candidate qualified. This
does not establish Loopover transfer or change any L1–L7 disposition.

A four-goal follow-up on fresh Loopover draws 0702–0705 applied the same
order-complete grammar to three independent goals. All 1,260 one-step and
two-step trials were residual; no candidate qualified. This adds no
independent-goal capability evidence and does not change any L1–L7 disposition.

A fresh four-goal Loopover replication on draws 0706–0709 again tested one
candidate across three independent goals using the order-complete grammar.
All 1,260 trials were residual and none qualified. This adds no
independent-goal capability evidence and does not change any L1–L7 disposition.

A D4 generation-two continuation on fresh distinct training draws 0718–0721
qualified candidate `#16750` on three independent-goal pairs. This remains
training-only qualification evidence: there is no candidate approval,
generation-three checkpoint, held-out comparison, or improvement estimate.
L1–L7 dispositions remain unchanged.

The native Loopover transfer grammar was extended to candidate compositions
with three held processes and exercised on fresh draws 0722–0725. All 16,236
transfer trials across three independent goals were residual; no candidate
qualified. This is a mechanism expansion with negative training-only results,
not evidence of Loopover transfer or efficacy. L1–L7 dispositions remain
unchanged.

The current P22 E2 acceptance recheck passes 58 tests, and the runner/analyzer
self-checks pass with no held-out access. The standalone freeze and complete
24-checkpoint manifest are still absent. Candidate `#16750` remains
unapproved. Its request was superseded after an ancestor audit showed its
generation-two parent did not descend from the registered P22 D4 arm root.
These checks establish runner readiness only; no capability level changes
and no held-out result is available.

A fresh Loopover panel on draws 0726–0729 produced candidate `#10761`, which
qualified on two independent-goal pairs. Its exact request binds the 0726/0727
pair and one guarded training transition; the 0726/0728 qualification is
outside that request. The request was superseded after an ancestor audit
showed its generation-zero root did not match the registered P22 Loopover
arm root. No action or checkpoint has been created. The panel used the full 40,000-attempt
training ceiling and produced no validation or held-out evidence. This adds a
qualified proposal, not Loopover transfer efficacy; L1–L7 remain unchanged.

A read-only replay of the same Loopover allocation reproduced candidate
`#10761`, both qualifications and their exact witnesses. It added no approval
or receipt and accessed no validation or held-out worlds. This strengthens
the reproducibility of the candidate proposal only; its request was later
superseded by the common-ancestor audit. All capability-level dispositions
remain unchanged.

The development continuation runner now resumes from the exact family-specific
generation-zero roots registered in the four-arm snapshots. A D4 root
continuation on fresh training draws 0900/0901 completed with one candidate,
2,437 cumulative reserved attempts and zero approvals or receipts. A Loopover
root continuation on the same fresh draw IDs correctly restored the registered
root but found no first-trial candidate and reserved zero attempts. Neither
run allocated validation or held-out worlds. These smoke-scale continuations
fix the root/domain integration and provide no qualified descendant or
improvement evidence. The full common-ancestor lineages, standalone
preregistration and 24-checkpoint manifest remain absent; P22.E2–E3 and all
L1–L7 dispositions remain open.

Further correct-root diagnostics found no qualified descendant. D4 draws
0910–0914 produced two later unqualified proposals after the first two tasks
were budget-exhausted. D4 draws 0915–0918 produced one candidate on the first
task, but it had zero independent-goal qualifications; the remaining tasks
were budget-exhausted or solved by the ancestor. Loopover draws 0902–0905
produced no search attempts or candidates because every task was
budget-exhausted. These training-only results had no approvals, receipts,
validation allocations or held-out access. They leave candidate-specific
lineage creation and P22.E2–E3 open; L1–L7 dispositions do not change.

The continuation fault was traced to the restored four-arm checkpoint's
enabled `SolverPolicy`, which competed with the probe's deliberate impasse
setup. The development runner now disables that inherited policy in the
proposal-search working graph; checkpoint evaluation installs its own fixed
solver. On fresh D4 draws 0932–0935, the registered invention-only root
produced candidate `#1870` (digest
`209f9861ca82daf500284f696298b28b18a420c885bf6c16d4a5aa23e714fd65`,
parameters `[1,3,0,2]`) and recorded qualifications on 0932/0933 and
0932/0935. Exact training-only replay reproduced them. A later effect audit
found the candidate identical to the already-held `rot90` process in that
root, invalidating both qualifications as improvement evidence. Its request
was superseded; no approval, receipt, validation allocation or held-out
access occurred. Native qualification now excludes effects already present
in active or adopted processes. No P22 efficacy or capability result can be
claimed and L1–L7 remain unchanged.

Two Loopover continuations from its registered invention-only root used fresh
four-goal panels after solver isolation was corrected. Both spent the full
40,000-attempt ceiling and produced one proposal each, with zero independent-
goal qualifications. No Loopover adoption request was prepared. The D4
candidate request does not change any capability disposition; cross-family
lineages, preregistration and held-out evaluation remain incomplete, and
L1–L7 remain unchanged.

A further two-goal Loopover continuation on fresh draws 0940/0941 used 20,000
reserved attempts but produced no proposal on its first training task. It had
no approvals, receipts, validation or held-out access. This adds a negative
search result only; the candidate request remains D4-specific, P22.E2–E3
remain open and L1–L7 dispositions are unchanged.

The four-goal Loopover continuation on draws 0944–0947 proposed candidate
`#6689`, whose effect matches held process `R2` in the registered root. It
therefore received no independent-goal trial or qualification. The P22 native
qualification rules now exclude finite effects already present in active or
approved-adopted processes; the regression and affected P22 suite pass. This
closes the duplicate-effect qualification defect, not the Loopover lineage
gate. No checkpoint lineage, preregistration or held-out result has been
added, and L1–L7 dispositions remain unchanged.

Candidate minting was then tightened to skip verified effects already held
in the active domain, before a duplicate can occupy the request's one
candidate slot. The search regression and affected runner, qualification,
development and CLI bundle pass 52 tests. On fresh registered-root training
draws 0951–0954, Loopover candidate `#6542` has a novel effect and two
independent-goal qualifications; exact replay reproduced both. A
[candidate-specific request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0951_0954.md)
for one simulated transition and conditional g1 checkpoint is awaiting exact
approval. No action, validation allocation or
held-out access has occurred. This supplies a qualified training proposal,
not a checkpoint lineage or efficacy evidence; P22.E2–E3 and L1–L7
dispositions remain open.

From the registered D4 invention-only root, candidate `#1908` has a novel
standalone effect. Its 0955/0957 transfer witness produces a child effect
identical to active held process `rot90`, so the earlier qualification was
invalidated. The stricter native rule now requires both source and transfer
child effects to be absent from active/adopted processes; a regression covers
the held-child case. Re-evaluation recorded zero qualifications. The D4
request packet is superseded. The corrected runner/search/qualification/CLI
suite passes 53 tests, and the E2 acceptance bundle passes 60 tests; both
self-checks pass with no held-out access. Loopover candidate `#6542` retains two
qualifications under this stricter rule and exact replay; its separate
[request packet](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0951_0954.md) remains
awaiting exact approval. No candidate has been actioned, and neither family
has validation or held-out evidence. This adds no P22 efficacy result and
leaves L1–L7 dispositions unchanged.

A new D4 training panel then found a valid transfer witness for the same
source expression as the superseded request. Candidate `#1908` qualified on
distinct goals 0962/0972, and its verified child effect `[2,0,3,1]` is absent
from both active root processes. Exact replay reproduced qualification
`#11843`. The [replacement D4 request](COGNITION_P22_APPROVAL_REQUEST_D4_0962_0972.md)
selects only this new witness; the older 0955/0957 audit remains superseded.
The new request and the Loopover request each require exact candidate-specific
approval for one training transition and conditional g1 capture. Neither has
been actioned; both remain training-only with no validation or held-out
evidence. L1–L7 dispositions remain unchanged.

The candidate-adoption CLI now has a regression for stale approval packets:
even with the exact candidate digest and execution flag, a packet marked
`superseded` is rejected before the one-shot output is claimed. The focused
CLI module passes 9 tests, including an already-claimed output replay check
that preserves the consumed result bytes. This closes request-lifecycle
guards only; the current D4 and Loopover registered-root packets remain
awaiting their own exact approvals, with no new action or checkpoint.

The P22 preregistration now has a protocol draft covering the fixed allocation,
estimands, effect thresholds, resource-matching requirement, and structural
controls. It is explicitly not frozen and authorizes no held-out access. The
runner and analyzer self-checks pass, with `heldout_accessed=false`. The
current native provenance audit is `ATTESTED` with no issues; component hashes
are recorded in the preregistration draft and must be recomputed at freeze.
base allocation audit found 1,600 unique world IDs and seeds; its current
SHA-256 is documented in the draft and does not include the frozen roots and
resource ceilings.
24-checkpoint manifest, approved registered-root descendants, and matching
development resource vectors remain unavailable, so no efficacy or capability
disposition changes.

The two pending registered-root candidate packets were independently audited
against their source and replay artifacts. Candidate digests, parameters,
parent digests, qualification IDs/kinds, and exact training-witness pairs
reproduced for D4 and Loopover; no action or held-out allocation is present.
Both still require exact user approval, so capability dispositions remain
unchanged.

The P16 v2, P17 v2, and P18–P21 raw result and analyzer files remain present
in `/tmp`; recomputed hashes for all 12 files match the frozen ledgers. The
rejected P16 v1 and P17 v1 raw inputs also match their recorded hashes and
remain excluded from interpretation. This read-only integrity audit changes
no outcomes or L1–L7 dispositions.

The held-out runner also rejects a committed preregistration draft with no
machine-readable freeze before constructing a learner or any evaluation world.
The focused runner module passes 7 tests. This confirms the current protocol
draft cannot access held-out data and does not alter the evidence dispositions.

P22's resource feasibility protocol was corrected before any preregistration
freeze or held-out access. Exact equality of realized resource vectors is now
required only for efficiency comparisons; the capability estimand uses common
worlds and frozen per-field ceilings, retains all measured work, and reports
`CAPABILITY_ONLY` when realized costs differ. The analyzer and draft
preregistration implement this distinction. Across six retained four-arm root
panels (40 training-world rows), all rows use common worlds, respect the shared
primitive-work and native-rule-progress ceilings, and measure every contract
resource dimension; none has exact realized-resource equality. These are
capability-only development comparisons, not held-out results. The focused
P22 estimand/checkpoint/analyzer bundle passes 41 tests, analyzer and runner
self-checks pass, and the runner confirms `heldout_accessed=false`.

The P22 preregistration remains `DRAFT — NOT FROZEN`: the 24-checkpoint
multi-generation manifest and per-checkpoint resource-ceiling record are
incomplete. Registered-root generation-one requests D4 invention-only `#1908`,
Loopover invention-only `#6542`, and D4 full-arm `#1541` were each approved
and consumed exactly once with 12 reviewer-reported seconds. Verified receipts
and valid generation-one checkpoints were recorded; these fulfill 3 of 12
invention/full descendants. D4 invention-only generation two was then
approved and captured in one verified transition with 12 reviewer seconds,
bringing the count to 4 of 12; eight later transitions remain, each requiring
its own approval. A D4 invention-only g1 continuation produced candidate `#9458`
and qualification `#15851` on training witnesses 0960/0818; an exact replay
matched them, and its one-action request was approved and consumed; the
parent-linked g2 checkpoint verifies. Loopover full-arm still lacks a qualified
generation-one candidate. The earlier D4
identity candidate `#6731` is outside these roots.
No held-out world has been constructed or scored, no efficacy claim is
established, and L1–L7 dispositions remain unchanged.

At P22 implementation commit `d390d58383a48eb48a13a8da1e9206dc0a64ebe6`,
the current native provenance recomputation reports `ATTESTED` with no issues:
runner SHA-256 `14f911f6bbf8083a080eab868b77350b9c028f26b8f2e8d92dafebb228866ec7`,
analyzer `10dce1e6e0b23f7a1f100ad3c7120829ab5335bf87f792b2a08408f5c4122643`,
source bundle `52af8bdd7a91cd536a4a2c4b02322a7d67e4d8a56bff20a1d77bb2841108cde4`,
loaded extension `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`,
and build receipt `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`.
The final preregistration freeze must recompute and bind provenance again after
all implementation changes.

The registered-root regression now audits the three consumed candidate
requests against their source/replay hashes, parent digests, qualification
witnesses, 12-second approval records, verified receipts, single-transition
counts, and valid child checkpoint digest and parent links. Validation and
held-out allocations remain empty. The updated P22 E2 acceptance bundle
passes 74 tests; runner and analyzer self-checks pass with no held-out access.
These actions do not change capability dispositions or held-out status.

The combined P22 E2 estimand/proposal/adoption/checkpoint/ablation/analyzer
bundle and updated registered-root consumed-result audit pass 74 tests. Runner
and analyzer self-checks pass with no held-out access. This is mechanism and
authorization-integrity evidence only; P22 efficacy and L1–L7 dispositions
remain unchanged.


A fresh Loopover full-root continuation on training worlds 0800–0803 reproduced candidate `#11545`, but all 16,236 independent-goal trials were residual and no qualification was recorded. The artifact reports 40,000 reserved attempts, 67 native rule steps, 1,222.628 seconds wall-time, 937,930,752-byte peak RSS, zero approvals/receipts, empty validation allocation, and no held-out allocation. Native rule identity coverage is complete. This is negative candidate-search evidence only; the Loopover full-arm generation-one gate and P22.E2–E3 remain open.


A second fresh Loopover full-root search on distinct training worlds 0804–0807 returned no candidate on its first task; a later task yielded `#31551` with no qualification or independent-goal trials. It reserved 40,000 attempts and recorded 55 native rule steps, 205.445 seconds wall-time, 937,930,752-byte peak RSS, zero approvals/receipts and empty validation allocation. No held-out world was constructed; rule identity coverage is complete. This negative search result leaves the Loopover full-arm g1 gate open.


A third fresh Loopover full-root panel on distinct training worlds 0808–0811 again produced candidate `#11545`, with all 16,236 independent-goal trials residual and no qualification. It reserved 40,000 attempts, recorded 67 native rule steps, 1,188.857 seconds wall-time, 937,930,752-byte peak RSS, zero approvals/receipts and empty validation allocation; no held-out world was constructed. Native rule identity coverage is complete. Loopover full-arm generation one remains unqualified; this is negative candidate-search evidence only.


A higher-budget Loopover full-root panel on fresh distinct training worlds 0812–0814 used 100 search ticks, 20,000 attempts per request, and a 60,000 global ceiling. Candidate `#21545` received 10,824 independent-goal trials, all residual, with zero qualification. The panel reserved 60,000 attempts, recorded 54 native rule steps, 860.849 seconds wall-time, 937,930,752-byte peak RSS, zero approvals/receipts, and empty validation allocation; no held-out world was constructed. Native rule identity coverage is complete. Loopover full-arm generation one remains unqualified.


The highest-bounded Loopover full-root search used 90,000 attempts, 120 ticks, and three fresh distinct training worlds 0815–0817; it found no candidate on any goal. The run measured 47 native rule steps, 2,564.122 seconds wall-time and 937,930,752-byte peak RSS, with zero approvals/receipts, empty validation allocation, no held-out worlds, and complete native-rule identity coverage. This further confirms the current full-root proposal-search setup has not produced a qualified generation-one candidate.


The D4 invention-only generation-one continuation on draws 0818–0821 reproduced candidate `#9458` (digest `84854777d0e3b48f447ecd04236a794eff39a46546edb3f19e47f506492ce66a`) and qualification `#15851` across distinct training worlds 0960/0818; an exact replay reproduced both. The verified transfer child is novel relative to the registered parent's active effects. The candidate-specific request was approved and consumed once; the g2 checkpoint digest and parent link verify. No validation or held-out world was accessed. The updated P22 E2 acceptance bundle passes 75 tests, including 14 tests in the focused development-probe CLI module; runner and analyzer self-checks remain passing with `heldout_accessed=false`.


A D4 invention-only g2 continuation on distinct training worlds 0822/0823/0825 found one formally qualified candidate, `#25873`, but its `power2:flip_r` effect is the identity permutation and cannot count as improvement; it was not approved. Candidate `#9459` had a malformed qualification with no kind and was excluded. The run reserved 60,000 attempts and measured 227 native rule steps, 3,726.471 seconds wall-time, and 3,130,871,808-byte peak RSS. It inherited two approvals/receipts and created none; validation and held-out access remained empty. D4 invention-only g3 remains unavailable.


A Loopover invention-only g1 continuation on fresh distinct training worlds 0826–0829 produced three candidates, all with zero qualifications. It reserved 60,000 attempts and measured 93 native rule steps, 815.398 seconds wall-time, and 2,030,424,064-byte peak RSS, with complete native rule identity coverage. It inherited the g1 approval/receipt but created no new action; validation and held-out access remained empty. Loopover invention-only generation two remains unavailable.


P22 qualification now rejects identity permutation effects for both the proposed source and its independent-goal transfer child using a domain-bound identity fingerprint. This repairs a loophole exposed by the D4 full-arm g1 training diagnostic on draws 0830–0833: candidate `#9440` qualified, but its selected transfer child `#12379` was identity. The diagnostic remains preserved as training-only historical evidence and created no approval or receipt. The affected native-rule, restored-checkpoint, and CLI coverage passes 43 tests. This does not establish an efficacy gain, create a descendant, or close P22.E2–E3.


A fresh D4 full-arm generation-one continuation on training goals 0002/0003 passed the repaired P22 identity-effect qualification guard: candidate `#9440` transferred to non-identity child `#22382` and qualified on distinct goals 0988/0003; exact replay matched. The source/replay artifacts retain only the inherited approval and receipt and have no validation or held-out worlds. A request is prepared for one exact candidate-specific training transition from the full-arm g1 parent and remains awaiting authorization. This is lineage mechanism evidence, not a capability or efficacy result.


After the identity-effect qualification repair, a fresh D4 invention-only g2 continuation on training goals 0004/0005 retained the identity candidate as a proposal artifact but gave it zero qualifications; its identity transfer child also received none. A malformed inherited qualification remained excluded. The two fresh tasks each exhausted 10,000 attempts, with no new approval or receipt and no validation or held-out allocation. D4 invention-only g3 remains unavailable; this is negative search-mechanism evidence, not an efficacy result.


A further Loopover invention-only g1 continuation on distinct training goals 0006/0007 yielded three candidates and zero independent-goal qualifications. Both tasks used 10,000 new attempts; no approval or receipt was added, and validation/held-out allocations remained empty. Loopover invention-only g2 remains unavailable. This result does not estimate efficacy.


The latest distinct-goal Loopover invention-only g1 continuation on draws 0006/0007 produced three candidates without qualification. This continues the training-search limitation; it creates no new descendant and does not estimate efficacy.


Increasing the Loopover invention-only g1 per-request ceiling to 20,000 on fresh distinct goals 0008/0009 yielded three candidates and no independent-goal qualification. This extends the negative candidate-search evidence only; no approval, receipt, validation, held-out allocation, descendant, or efficacy result was added.


A fresh Loopover invention-only g1 continuation at 30,000 attempts per request on goals 0010/0011 again produced three candidates with zero qualification. It reserved 60,000 new attempts without an approval or receipt; validation and held-out worlds remained unused. The lineage gate remains unmet.


A four-goal Loopover invention-only g1 continuation on 0016–0019 reached 120,000 cumulative attempts but produced five candidates with zero independent-goal qualifications. It adds no generation-two descendant or efficacy evidence. A separate invalid draw-allocation launch was stopped before completion and recorded as `INTERRUPTED_INVALID_ALLOCATION`; it is excluded from results.


A fresh four-goal Loopover full-arm continuation from the registered g0 root on 0020–0023 exhausted 25,000 attempts per task and returned `NO_CANDIDATE_FIRST_TRIAL` for every task. It generated two unqualified candidates, with no approval, receipt, validation, or held-out access. The full-arm g1 gate remains unmet.


A five-goal Loopover full-arm panel on fresh distinct goals 0029–0033 reached the 120,000-attempt ceiling and returned `NO_CANDIDATE_FIRST_TRIAL`. Four proposals were produced but none qualified; there were zero approvals, receipts, validation, or held-out access. The full-arm g1 lineage gate remains unmet.


After the 120,000-attempt Loopover full-arm panel exhausted all five task caps without transfer trials, a fresh four-goal panel reserved 10,000 attempts per request and left headroom for independent-goal transfer. Candidate `#1611` qualified on goals 0034/0035, transferred to non-identity child `#16963`, and exact replay reproduced both. Both effects differ from the registered full-arm g0 root's active processes. The resulting exact candidate request remains unapproved; no action or receipt has been created, and validation/held-out allocations remain empty. This is lineage mechanism evidence, not efficacy.

The current P22 regression refresh passes 73 tests across independent-improvement qualification, checkpoint restore/scoring, causal ablation, the held-out runner, development lineage, and development CLI coverage. The prescribed P22.04 subset passes 33 tests. Runner and analyzer self-checks pass, with the runner confirming `heldout_accessed=false`. These checks verify implementation and guardrails; they do not provide the missing 24-descendant manifest, frozen per-checkpoint resource ceilings, or held-out evidence. Capability dispositions remain unchanged.

At that audit checkpoint, the resource snapshot audit covered the 8 registered roots, 12 passive control descendants, and 4 approved invention/full descendants then captured. All 24 snapshots have valid digests and measured values for all 20 resource fields. Eight of the required 24 descendants were uncaptured at that checkpoint; two full-arm descendants were captured later but are not included in that panel, leaving six currently uncaptured. Final isolated scoring wall times and frozen resource ceilings remain outstanding. The D4 invention-only g1 request for digest `84854777…` was consumed once and produced its verified g2 checkpoint; it is not an outstanding approval. At this audit point, the two pending requests concerned D4 full-arm and Loopover full-arm candidates. No held-out worlds were accessed.

The captured D4 invention-only g2 checkpoint carries 487,906 cumulative primitive work. This exceeded the original implementation cap of 120,000; before preregistration freeze, the supported maximum was extended to 1,000,000, while the final shared ceiling remains unset pending the complete checkpoint manifest and development resource panel. A fresh D4 training-world probe and a four-world-per-family resource panel scored this checkpoint under a 600,000 ceiling at cumulative work up to 487,911. The resource panel covered all 24 currently captured checkpoints across 96 cells; all completed, respected both ceilings, and had valid digests and complete 20-field measurement. It recorded 35 solved and 61 unsolved training rows; this is not efficacy evidence. Maximum isolated cell wall time was 21.159 seconds; cumulative wall time including lineage cost reached 1,651.274 seconds. Peak RSS was 2,884,263,936 bytes. Eight descendants and the final frozen ceilings remain outstanding. Capability dispositions remain open.

**P22 current-checkout regression, resource, and provenance refresh (2026-10-24):** The seven-module P22 regression bundle passes 86 tests. Runner and analyzer self-checks pass; the runner verifies all 24 synthetic lineage links and all four required structural controls, and reports `heldout_accessed=false`. A fresh read-only audit confirms all 96 cells in the existing-checkpoint resource panel have valid snapshot digests and respect the recorded 600,000 primitive and 20,000 native-rule-step ceilings. Current runtime provenance at checkout `3e3ef32f6b34f3c5030ccf09114d22a0d3348bd8` attests cleanly with matching build sources, native symbols bound, and no issues; the refreshed source-bundle SHA-256 is `633a01942426ec17adf605b2898b5d6e7150c5e1ebe8cfc6c5cc6939949ee39a`. This readiness snapshot is recorded in [`COGNITION_LINEAR_P22_PREREG.md`](COGNITION_LINEAR_P22_PREREG.md); freeze provenance must be recomputed after all remaining changes. Eight required invention/full descendants, exact candidate decisions, final resource ceilings, preregistration freeze, and held-out efficacy remain outstanding. P22 and L1–L7 dispositions do not change.

**D4 invention-only generation-three continuation (2026-10-24):** A new proposal-only search on training worlds 0924–0926 reserved 60,000 attempts across three distinct goals; every task remained stuck. The run produced no valid improving generation-three qualification or checkpoint. Its sole qualification record had no kind and was excluded, while the identity candidates received no qualification. The parent’s two approvals and two receipts are unchanged; no new approval or receipt was created, and there was no validation or held-out access. Resource snapshots and complete native-rule identity coverage verify; detailed raw artifact and resource hashes are in the P22 preregistration and build-plan ledger. D4 invention-only g3 remains unavailable, and this adds no efficacy evidence or capability closure.

**Loopover invention-only generation-two continuation (2026-10-24):** A proposal-only search from the approved g1 checkpoint on three fresh distinct training goals 0924–0926 reserved 60,000 new attempts. The parent snapshot recorded 20,000 reserved attempts, bringing the recorded lineage total to 80,000 against the run's 120,000 ceiling; all tasks remained stuck and none of three proposals qualified. The inherited single approval and receipt were unchanged; there was no new approval, receipt, checkpoint, validation, or held-out access. Resource and native-rule-work snapshots verify with complete rule identity coverage. This negative search adds no efficacy evidence; Loopover invention-only g2 remains unavailable and capability dispositions remain open.

**D4 invention-only generation-three follow-up (2026-10-24, draws 0989–0991):** A separate proposal-only branch from the immutable g2 checkpoint reserved 15,720 attempts across three globally unused distinct training goals; all tasks remained stuck and none of the three new candidates qualified. It inherited two approvals and receipts but added no approval, receipt, or child checkpoint. The malformed inherited qualification on candidate `#9459` remained excluded. No validation or held-out data was accessed. Resource and native-rule-work digests verify with complete native identity coverage and no unresolved rules. The restored graph attempt counter rose from 44,280 to 60,000 under the configured 120,000 ceiling; wall time increased by 2,568.982 seconds, peak RSS was 3,244,118,016 bytes, and native rule steps increased by 45. This negative training search adds no efficacy evidence; D4 invention-only g3 and the capability dispositions remain open.

**D4 invention-only generation-three second follow-up (2026-10-24, draws 0992–0993):** A separate proposal-only branch restored the same g2 checkpoint, reserved 20,000 attempts across two new distinct training goals, and produced two unqualified candidates; both tasks remained stuck. The inherited malformed qualification on `#9459` remained excluded. It inherited two approvals and two receipts, added neither, and created no checkpoint. No validation or held-out data was accessed. Resource and native-rule-work digests verify with complete native identity coverage and no unresolved rules. The branch's restored graph counter increased from 44,280 to 64,280 under the configured 120,000 ceiling; wall time increased by 1,949.954 seconds, peak RSS was 3,123,765,248 bytes, and native rule steps increased by 33. This is negative search evidence only; D4 invention-only g3 and the capability dispositions remain open.

**Loopover invention-only g1 search follow-up and branch attempt audit (2026-10-24, draws 0994–0996):** The latest three-goal proposal search reserved 60,000 attempts; all tasks remained stuck, and two new candidates did not qualify. It inherited one approval and one receipt, added neither, and created no child checkpoint. No validation or held-out data was accessed; resource and native-rule-work digests verify with complete identity coverage and no unresolved rules. Across the source g1 run and seven completed restored proposal branches, cumulative development search work is 400,000 attempts, while every individual graph stayed within its 120,000 ceiling. The separate interrupted invalid-allocation preflight is excluded because it has no completed attempt record. This reconciles the branch-level history; the aggregate search expenditure does not provide efficacy evidence. Loopover invention-only g2 and capability dispositions remain open.

**Loopover invention-only g1 second search follow-up and attempt audit (2026-10-24, draws 0997–0999):** The three-goal proposal branch reserved 60,000 attempts; all tasks remained stuck and one new candidate did not qualify. It inherited one approval and one receipt, added neither, and created no checkpoint. No validation or held-out data was accessed. Resource and native-rule-work digests verify with complete coverage and zero unresolved rules. Across the g1 source run and eight completed restored proposal branches, cumulative development search work is 460,000 attempts, while each graph remained within its 120,000 ceiling. The interrupted invalid-allocation preflight is excluded because it has no completed attempt record. This negative search adds no efficacy evidence; Loopover invention-only g2 remains unavailable and capability dispositions remain open.

**Loopover invention-only g1 deeper search follow-up and branch audit (2026-10-24, draws 0980–0983):** The four-goal 120-tick proposal branch reserved 60,000 attempts; all tasks remained stuck and three new candidates received no qualification. It inherited one approval and one receipt, added neither, and created no checkpoint. No validation or held-out data was accessed. Resource and native-rule-work digests verify with complete identity coverage and zero unresolved rules. Across the g1 source run and nine restored proposal branches, cumulative development search work is 520,000 attempts, while every graph remained within its 120,000 ceiling. The interrupted invalid-allocation preflight is excluded because it has no completed attempt record. This negative search adds no efficacy evidence; Loopover invention-only g2 and capability dispositions remain open.

**P23 finite search diagnosis (2026-10-24):** The [diagnostic results ledger](COGNITION_LINEAR_P23_RESULTS.md) and [input contract](COGNITION_SEARCH_DIAGNOSIS_CONTRACT.md) bind exact roots, sources and 30 restored branches. The D4 closure is eight effects at both inspected roots; three novel nonidentity effects remain at g2, with two mathematical source/child witnesses and one lacking a source task in the inspected training corpus. Native qualification remains unestablished. Bounded Loopover BFS found 4/5 archived training goal effects by composition depth 3 and labels the remaining effect `UNKNOWN_OUTSIDE_BOUND`. Funnel analysis reconciles 1,401,440 attempts across unique restorations and identifies per-request saturation in the 0980–0983 Loopover branch despite 40,000 global headroom. It also records 19,998/20,000 attempts without candidate-summary expression links. These are development-only diagnostics; no held-out worlds, approvals, receipts, checkpoint transitions or efficacy claims were added. P19–P22 capability levels and all earlier P16–P21 outcomes remain unchanged. P22 remains draft and held-out access stays closed. P24 common-target learning is the next prescribed phase; the measured search repair is reserved for P26.

**P24 common-target transfer result (2026-10-24):** The native common-receipt learner, verified compatible-source proposal path, wrong-source fallback, same-target map-work control, cognition-on integration, and all 300 registered controls completed structurally. The first frozen draw is retained as invalid because its analyzer crashed before scoring; it was not rescored. A corrected v2 protocol used a new standalone freeze and disjoint seed block. Across 200 paired streams in each of heat→thermal and lever→latch, every arm had AUC 0.25 and final accuracy 1.0. Compatible-source gain over the stronger source-free comparator was exactly 0.00 in both families (paired 99% CI [0, 0], Holm-adjusted p=1.00); the ≥0.10 benefit gate failed, with no final accuracy loss, receipt loss, or double credit. Compatible maps/effects verified, wrong-source maps were rejected, and ordinary target learning continued. The complete [P24 results ledger](COGNITION_LINEAR_P24_RESULTS.md) contains allocation, runtime, hashes and cost strata. P24 establishes the bounded mechanism and negative transfer-benefit result only; L4 remains **NOT_ESTABLISHED**, P20's −0.3333 remains unchanged, and no human comparison or capability level is closed. P25 may use the common learner for persistent-memory testing without assuming a source-transfer advantage.

**P25 persistent retention result (2026-10-25):** The standalone preregistration and source/build/runtime hashes bind the single completed held-out draw. All 1,200 paired streams (4,800 rows) and 300/300 eviction/restart/absent-source controls completed; analyzer structural status is `VALID`. Sleep consolidation exceeded replay-only delayed-success AUC by 0.7222 (99% paired bootstrap interval [0.7103, 0.7336]) across both thermal and latch families and all three capacity ratios. The registered 0.10 gain and ≤0.02 new-task loss criteria passed. However, all four arms scored 0/1,200 on the unseen ButtonWidget task, so the non-loss result is a floor comparison and provides no positive transfer evidence. P25 supports persistent retention of the trained target relation under this simulator's tested pressure/interference; it does not support general useful-learning, curriculum-selection, search, or human-equivalence claims. Exact total native-rule counters were enforced at runtime but not written into raw rows; the resource ledger reports the checked ceiling and available phase-local measures. See the [P25 results ledger](COGNITION_LINEAR_P25_RESULTS.md) and retained raw/analysis artifacts. P26 remains planned, must address selection/search as separate hypotheses, and must not inherit P25's retention effect as evidence of those capabilities.

**P26.02 diagnosed search repair (2026-10-25):** The [P26.02 results ledger](COGNITION_P26_02_SEARCH_REPAIR_RESULTS.md) records one retained training-only Loopover g1 branch with 41,722 new attempts, 1,722 reserved independent-goal trials, and 18,278 unspent transfer attempts. Exact-effect deduplication prevented a second candidate from two verified syntactic expressions with the same finite effect. The single new candidate remained unqualified after 1,722 residual independent-goal trials; no new approval, receipt, adoption, or checkpoint resulted. Attempt provenance and complete native rule identity are retained. Two earlier export-failed invocations lost their in-memory attempt counters; this is disclosed as an operational evidence limitation and is not included in the retained branch totals. P26.02 establishes the bounded repair mechanism only. P26.03 is next; P22 held-out access remains closed and no capability level changes.

**P26.03 evidence-selection mechanism (2026-10-25):** Implemented an opt-in graph-native selector with training-split, source/model/frame-matched signals; native predictions contradicted by observed counterexamples; recurring residuals require two distinct counterexamples; progress signals require an authorized receipt, changed learned state, and changed behavior. Residual, fixed and random selectors consume the same opportunity pool and shared ThinkingBudget. Tests prove that selected evidence is delivered through the common learner and changes a later fresh-binding prediction, that receipt fan-out adds no exposure, and that no-progress/state-only outcomes are not retried as useful learning. The phase regression bundle passes 23 tests. This establishes mechanism only: no task-pool efficacy estimate, general learning benefit or capability-level increase is implied. P26.04 is next; P22 held-out access remains closed.

**P26.04 heterogeneous worlds and cost curves (2026-10-25):** Added split-namespaced cyclic/branching finite worlds, repeated and cross-structure transferable relation mechanisms, irrelevant context features, partial transition coverage, and scorer-only unlearnability labels. Selector-visible opportunities expose legal action names but not transition effects, solvability labels, or witnesses; an external world adapter emits the actual authorized receipt only after action execution. The residual, fixed and random arms receive identical opportunity records, and validation/held-out pools are excluded from selector materialization. Geometric search ceilings report cumulative charged work, unique effects, success and finite exhaustion, including invalid/failed transitions. Dedicated world tests pass 9; the broader P26.E1 integration bundle passes 89. This establishes the independent generator and accounting mechanism only; no P26 selection/search efficacy or Track I capability claim is implied. P26.E1 integration is complete; P22 held-out access remains closed.

**P26 heldout outcome (2026-10-25):** The valid, attested 800-stream evaluation did not show residual-directed selection advantage. Its pooled AUC was 0.00875 versus 0.02484 for random, with residual-minus-stronger-control gain −0.01609 (99% interval [−0.02563, −0.00750]); the preregistered gate failed. Outcomes were near floor across all cells. Native search generated proposals but no verified unique effect, approval, receipt, or unseen-binding use. This does not change any capability level or support a search/selection benefit claim. See [`COGNITION_LINEAR_P26_RESULTS.md`](COGNITION_LINEAR_P26_RESULTS.md). P27 is permitted to evaluate scheduled cumulative checkpoints under a new protocol; it must retain no-change intervals and cannot presume a P26 benefit. P22 remains a draft; old heldout access remains closed.

**P26.E1 profile integration (2026-10-25):** The cognition-on closure now includes the useful-evidence selector seed with its policy off by default. The native learning-chain test proves selection→shared-budget approval→checkpoint/restart→authorized simulator receipt→common-learner state→fresh-binding prediction; the selector knockout leaves the control with no selection or budget debit. Default/conversation isolation, native extension attestation, dynamic graph growth, serialized checkpoint bytes, native-rule work, and zero source exposure are checked. Prescribed integration bundle: 88 passed; focused post-accounting assertions: 2 passed. Process-search policy remains separately disabled, and existing candidate approval scopes are untouched. P26 benefit has not been tested; P26.E2 must freeze and preregister before any held-out draw.


**P27 scheduled-checkpoint held-out result (2026-10-25):** The separately versioned P27 successor completed a valid, attested one-shot evaluation across 200 held-out worlds per family at g0–g3 and 200 fresh validation worlds per family at g3. All arms scored 100% at every checkpoint and on validation; paired combined-minus-frozen gains and checkpoint slopes were exactly zero in both cyclic-relation and branching-relation families. The registered advantage gate failed as a flat ceiling outcome. All 100 controls passed; two branching-family search checkpoints retained unapproved candidates, with zero approval, transition, or adoption receipt. Realized resources differed, so efficiency is `NOT_ESTABLISHED`. This supports only exact common-target next-state prediction on these finite simulator families; it does not establish a cumulative advantage or close any L1–L7 capability. P22 remains `DRAFT — NOT FROZEN`, and its missing descendant/resource gates are not repaired by P27. Full metrics and hashes are in [`COGNITION_LINEAR_P27_RESULTS.md`](COGNITION_LINEAR_P27_RESULTS.md). The next required work is a requirement-by-requirement audit of the full build plan, preserving unresolved P16–P22 obligations rather than inferring closure from the completed P27 reporting cycle.

**P22 D4 invention-only g2 search-repair follow-up (2026-10-25):** Applied P26's fixed-budget exact-effect deduplication and qualification reserve to four new distinct D4 training goals. The run completed 43,528 new attempts, spent 3,528 of 20,000 reserved transfer attempts, and produced no new candidate or valid qualification; its only inherited qualification was malformed and rejected. No approval, receipt, checkpoint, validation allocation, or held-out access was added. Complete raw attempt provenance and digests are recorded in the build plan. The result remains training-only negative search evidence and does not change any capability level; the snapshot/live RSS discrepancy also means it cannot establish a resource ceiling.

**P22 RSS attribution limit (2026-10-25):** The 0203–0208 D4 branch's persisted `getrusage(RUSAGE_SELF)` peak cannot be joined to its separate live `ps` sample because neither process ID/sample was retained. Future P22 snapshots now bind per-process peak observations, PID, Unix-nanosecond observation time and scope and mark inherited pre-repair peaks unattributed. No historical RSS value was reconstructed, and the matched-resource, freeze and held-out gates remain open; capability dispositions do not change.

**Full plan audit (2026-10-25):** The requirement-level audit records completed P16–P21 and P23–P27 reporting cycles with their valid negative, bounded-positive, or `NOT_ESTABLISHED` outcomes. P22 remains the only open cycle: its 24-descendant lineage, matched resource ceilings, frozen preregistration, results ledger, and held-out evaluation are incomplete. P27 does not close P22; all L1–L7 dispositions remain open. See [`COGNITION_BUILD_PLAN_COMPLETION_AUDIT_20261025.md`](COGNITION_BUILD_PLAN_COMPLETION_AUDIT_20261025.md).

**P22 registered full-arm lineage update (2026-10-25):** The two exact user approvals for D4 full-arm g1 candidate `#9440` and Loopover full-arm g0 candidate `#1611` were each consumed once with 12 reviewer seconds. Their verified receipts and digest-valid D4 g2 and Loopover g1 checkpoints raise captured invention/full descendants to 6/12. Both results are training-only and include no validation or held-out worlds. Six descendants, full matched-resource preflight, preregistration freeze and P22 held-out evaluation remain outstanding; no capability level changes.

**P22 D4 full-arm g2 bounded proposal search (2026-10-25):** P26's exact-effect deduplication and fixed discovery/transfer reserve were applied to four fresh distinct training goals from the approved g2 checkpoint. The 40,000 new attempts produced no new candidate or qualification; all four tasks remained stuck and no transfer reserve was used. No approval, receipt, checkpoint, validation or held-out allocation was added. Resource and attempt-projection digests verify; process-peak RSS is attributed to the runner PID and timestamp. This is negative training-search evidence and does not change capability dispositions or satisfy the six-descendant/resource/freeze gates.

**P22 Loopover full-arm g1 bounded proposal search (2026-10-25):** The corresponding four-goal P26 continuation added 55,000 training attempts, but all tasks remained stuck. One new candidate received 15,000 independent-goal trials, all residual, and no qualification; no action or checkpoint followed. Resource and attempt-projection digests verify, with complete native identity coverage and attributed process RSS. This remains negative training evidence and changes no capability disposition or P22 gate.

**P22 Loopover full-arm g1 follow-up search (2026-10-25):** A second fresh-goal branch added 60,000 reserved training attempts. Two new candidates received 20,000 independent-goal trials in total, all residual; neither qualified, and no action or checkpoint followed. The native resource and attempt-projection digests verify, with complete rule identity coverage and attributed process RSS. This remains negative search evidence and changes no capability disposition or P22 gate.

**P22 Loopover full-arm g1 second follow-up search (2026-10-25):** A third fresh-goal branch added 55,000 reserved attempts. Candidate `#81580` received 15,000 independent-goal trials, all residual, and did not qualify. No approval, receipt or checkpoint was added. Native resource and attempt-projection digests verify with complete rule identity coverage and attributed process RSS; no capability disposition or P22 gate changes.

**P28.01–P28.08 representation investigation integration (2026-10-25):** The PDS/VAD comparison now has a bounded rotation-only contract, label-blind external source manifest, full-information invariance reference, and a narrow runtime readiness decision. Opt-in native frame/acquisition seeds, two independent receipt-producing world families, P24 prediction, P17 acquired-axis action authorization, and native metric recall are connected behind a self-load-only investigation profile. The 87-test focused P28.01–P28.08 bundle passes; exact fixed-versus-transported controls show the declared finite-metric mechanism, not new information. Forged simulator receipts are rejected. Orphan lint found no P28-named orphan signals; boot classification keeps both P28 seeds self-load-only; the loaded native runtime attests with matching build sources. No behavioral efficacy or semantic-calibration claim is established, and no L1–L7 disposition changes. P28.09 development-only behavior/transfer measurement remains next; P22's separate gates remain open.

**P28.09–P28.10 development checks (2026-10-25):** P28.09's paired four-horizon, six-arm self-check produced identical descriptive outcomes across arms (mean success 0.25, AUC 0.375, abstention 0.50); the specified behavior/geometry bundle passed 11 tests. P28.10's verified-receipt distribution panel passed 6 tests and showed that token frequency can change weighted error/geometry summaries while preserving the three-event world stream and explicit rare-adverse error. These are implementation and sampling-mechanism checks only. No efficacy, environmental risk, semantic calibration, or capability claim follows; P28.11–P28.16 and the separate P22 gates remain outstanding, and L1–L7 dispositions are unchanged.

**P28.09 development behavior panel (2026-10-25):** Paired fixed horizons now include verified source learning, changed-map target calibration and fresh-context graph-selected scoring, with full representation/decoder costs and failures retained. The current 12-test behavior/geometry suite passes. The default two-seed, six-arm, two-family, 96-checkpoint panel produced tool-intervention mean success 0.25/AUC 0.375/abstention 0.50 in each arm, and social-repair success/AUC 0.0 in every arm. This small development result establishes neither representation advantage nor semantic calibration; P28.10–P28.16 remain outstanding, and P22's independent gates and L1–L7 capability dispositions are unchanged.

**P28.10–P28.11 mechanism checks (2026-10-25):** The receipt-sampling controls passed 6 tests; frequency weighting changed weighted geometry/error summaries while preserving fixed event support and rare-adverse visibility. The label-blind GPADS scorer passes 10 tests for complete-anchor-only fitting, held-out-only scoring, frozen checkpoint/bridge/split binding, oversized-cluster handling and missing-concept accounting. No trained token-to-concept bridge exists, so readiness is `UNSUPPORTED` and external scores remain unopened. These implementation results establish no behavior advantage, lexical calibration or capability level; P28.12–P28.16 and P22 remain outstanding.

**P28.12 risk-boundary integration (2026-10-25):** The current exact risk/response-inhibition command passes 21 tests; the recorded combined P28.08–P28.12 regression bundle passes 68. Asserted lexical phrasing did not change simulator receipts or full future-manifold residuals, and a native same-epoch stop still prevented sink emission. Later P28 reporting is recorded below; P22 remains open and L1–L7 dispositions are unchanged.

**P28.13–P28.16 closeout (2026-10-25):** The single preregistered 2,400-row panel and its frozen analysis are recorded in [`COGNITION_OUSIOMETRIC_RESULTS_V1.md`](COGNITION_OUSIOMETRIC_RESULTS_V1.md); the evidence-scoped decision is in [`COGNITION_OUSIOMETRIC_DECISION.md`](COGNITION_OUSIOMETRIC_DECISION.md). Both primary families have exactly zero AUC difference, 99% interval [0, 0], and Holm-adjusted p=1.0; the registered behavioral benefit gate fails. All six arms share the same outcome curves per paired seed. Full-rank parity and runtime attestation pass, all failures are retained, and GPADS/NRC score columns remain unopened because lexical readiness is `UNSUPPORTED`. The report includes calibration adverse exposures and resource costs; it claims no environmental safety or semantic calibration. The decision is to retain the existing default representation with no runtime change. The prescribed P28.14, P28.15, and P28.16 test commands pass 22, 22, and 21 tests respectively. P28 is closed as an investigation/reporting cycle with no L1–L7 disposition change; P22's lineage/resource/freeze/held-out gates remain open.

**P22 resource-provenance checkpoint (2026-10-25):** The current captured-checkpoint audit verifies 26 unique checkpoints (eight roots, 12 passive descendants, six approved invention/full descendants), valid checkpoint/resource digests, and all 20 resource fields measured per checkpoint, with no audit issues. It includes per-field observed ranges for ceiling planning, not frozen ceilings. Its machine-readable disposition is `PASS_PARTIAL_INCOMPLETE`; six invention/full descendants, frozen per-field ceilings, and the isolated final wall-time panel are still missing. No held-out access is allowed and no P22 efficacy or capability claim follows. See [`P22 preregistration`](COGNITION_LINEAR_P22_PREREG.md) and the [audit artifact](../../../evaluation/process_mastery/results/p22_checkpoint_resource_audit_20261025.json).

**P22 supplementary resource measurements (2026-10-25):** Added isolated worker measurements for the two approved full-arm checkpoints missing from the earlier 96-cell resource panel. Eight of eight cells completed on the same registered training worlds, all 20 resource fields are measured, and no approval, receipt, validation, or held-out use occurred. Maximum isolated cell time was 28.563 seconds and worker peak RSS was 3,518,881,792 bytes. These are resource-planning diagnostics only; six descendants and the final shared ceilings/freeze remain open. See the [supplementary panel](../../../evaluation/process_mastery/results/p22_resource_panel_new_approved_checkpoints_0609_0612_0622_0625.json.gz).

**P22 current resource-manifest reconciliation (2026-10-25):** A reproducible reconciliation now covers all currently captured checkpoints: 26/32 checkpoints and 104 isolated cells (four training worlds per checkpoint), with complete 20-field measurement, valid resource digests, and zero issues. Status remains `PASS_PARTIAL_INCOMPLETE`: six invention/full descendants and final per-field ceilings are missing. No validation/held-out data or actions were used, and no efficacy or capability conclusion follows. See the [partial resource manifest](../../../evaluation/process_mastery/results/p22_current_resource_manifest_20261025.json).

**P22 runtime provenance (2026-10-25):** The current native runtime recheck is `ATTESTED`, with native symbols bound, build sources matching, and no issues. This supports mechanism integrity only; the final checkpoint manifest, ceilings, preregistration freeze, and held-out evaluation remain incomplete. The freeze must recompute and bind provenance after lineage completion.

**P22 regression refresh (2026-10-25):** The current combined P22 runner, analyzer, resource, CLI, checkpoint-panel, development, arm, and integration selection passes 79 tests. This supports implementation integrity only; it does not change P22's incomplete lineage/resource disposition or any L1–L7 capability claim.

**P22 ceiling derivation rule (2026-10-25):** The draft now specifies a deterministic pre-freeze rule: use per-checkpoint maximum isolated time across four common training cells; use measured maxima across the complete 32-checkpoint panel for shared field ceilings, retaining primitive-work 600,000 and native-rule-step 20,000 limits. Current partial values remain provisional until all descendants and cells are captured. This improves preregistration specificity without changing capability interpretation or opening held-out access.

**P22 Loopover search updates (recorded 2026-10-26):** Two additional registered-root training branches completed with no qualified candidate. Loopover invention-only g2 searched 0230–0233 and Loopover full-arm g2 searched 0246–0249; their 15,000-trial candidates were entirely residual. No transition or receipt was added, and neither branch accessed validation or held-out data. These negative search results do not alter capability claims. See the dated P22 preregistration and build-plan ledger entries for hashes and resource provenance.

**P22 Loopover full-arm g2 continuation (2026-10-26):** The four-goal training-only continuation on draws 0262–0265 added 60,000 attempts to its 40,000-attempt inherited graph; all tasks stayed stuck, and candidates `#71577` and `#81581` received 10,268 and 9,732 independent-goal trials with zero qualification. There was no new approval, receipt, checkpoint, validation use, or held-out access. Resource and native-work digests validate, rule identity coverage is complete, and no unresolved rules remain. The result is negative search evidence only; P22 capability interpretation and the open lineage/resource/freeze/held-out gates are unchanged. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0262_0265_p26.json) SHA-256 `ea41d9187e462bff479e8ac8d5ba20545171d96c18c24e5ae5f3e95f8a7440bc`.

**P22 Loopover invention-only g2 continuation (2026-10-26):** The four-goal training-only continuation on draws 0254–0257 added 60,000 attempts to its 20,000-attempt inherited graph. All tasks stayed stuck; candidates `#41575` and `#61582` received 10,268 and 9,732 independent-goal trials with zero qualification. No new approval, receipt, checkpoint, validation use, or held-out access occurred. Resource and native-work digests validate with complete rule identity coverage and no unresolved rules. This is negative search evidence only; capability interpretation and P22's open lineage/resource/freeze/held-out gates are unchanged. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0254_0257_p26.json) SHA-256 `fa9419bea42f86f318255f81380940743c2cf43558f8fdb6772bc0c2f2d7086b`.

**P22 D4 invention-only g3 proposal search (2026-10-26):** The training-only continuation on draws 0226–0229 added 43,528 attempts to its 44,280-attempt inherited graph; all four tasks stayed stuck and no eligible new candidate qualified. Inherited `#9459` has a malformed qualification (missing `kind`) and remains excluded; `#25873` is identity and unqualified. No new approval, receipt, checkpoint, validation use, or held-out access occurred. Resource/native-work digests validate with complete rule identity coverage and no unresolved rules. Cumulative declared primitive work was 903,701, above the fixed 600,000 ceiling, so this branch cannot supply an admissible descendant. Capability interpretation and P22's open lineage/resource/freeze/held-out gates are unchanged. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0226_0229_p26.json) SHA-256 `2323a7f35c49a521fc61537142373dae51ef9148064fcf978d94265b86cbe9f4`.

**P22 Loopover full-arm g2 P26 continuation (2026-10-26):** A four-goal, training-only continuation on draws 0046–0049 added 55,000 attempts to its 40,000-attempt inherited graph; all four tasks stayed stuck. Candidate `#61574` received 15,000 independent-goal trials with no qualification. No new approval, receipt, checkpoint, validation use, or held-out access occurred. Resource and native-work snapshot digests validate, native identity coverage is complete, and the 420,826 cumulative declared primitive work is below the fixed 600,000 ceiling. This is negative search evidence only; P22's open lineage, resource, freeze, and held-out gates and all capability claims remain unchanged. Raw result SHA-256 `407ab243f68737ed5ab8104e3eab22f75828508bd1ee8992bf75cc798f2c66d1`.

**P22 Loopover full-arm g2 follow-up (2026-10-26):** A second four-goal training-only continuation from the registered full-arm g1 checkpoint added 55,000 attempts to its 40,000-attempt parent graph; all tasks stayed stuck. Candidate `#51571` received 15,000 independent-goal trials with no qualification. No new approval, receipt, checkpoint, validation use, or held-out access occurred. Resource and native-work digests validate, native identity coverage is complete, and cumulative declared primitive work is 536,820, under the fixed 600,000 ceiling. This negative search evidence does not change P22's open gates or capability claims. Raw result SHA-256 `1a7dc2c179db3ec2db942a8fab4775f487ac42df4fd4e21f5e28497c25f8dbf5`.

**P22 Loopover invention-only g2 continuation (2026-10-26):** A four-goal training-only continuation on draws 0042–0045 added 60,000 attempts to its 20,000-attempt inherited graph; all tasks stayed stuck. Candidates `#41575` and `#51579` received 10,268 and 9,732 independent-goal trials with no qualification. No new approval, receipt, checkpoint, validation use, or held-out access occurred. Resource/native-work digests validate and native identity coverage is complete; cumulative primitive work is 402,984 under the fixed 600,000 ceiling. This negative result does not close the Loopover g2 lineage gate or change capability claims. Raw result SHA-256 `b66fba3851bf6a6a0bb95fb84630944079ea543dfe5d08114797e7dfbb6c385c`.

**P22 Loopover invention-only g2 follow-up (2026-10-26):** A separate four-goal training-only branch on draws 0054–0057 added 55,000 attempts to its 20,000-attempt parent graph; all tasks stayed stuck. Candidate `#31572` received 15,000 independent-goal trials with no qualification. No new approval, receipt, checkpoint, validation use, or held-out access occurred. Resource/native-work digests validate, native identity coverage is complete, and cumulative primitive work is 472,496 under the fixed 600,000 ceiling. This negative result leaves the g2 lineage gate and capability claims unchanged. Raw result SHA-256 `ac9c3babccbd4c62cd4e1b09a20742e23c9515114dd41d48899317820ba221f7`.

**P22 regression verification refresh (2026-10-26):** The current combined native runner/analyzer, resource-accounting, proposal CLI, checkpoint-panel, development, arm, and four-arm integration suite passes 79 tests in 243.72 seconds. This supports mechanism integrity only; P22's six missing descendants, resource freeze, and held-out evaluation remain incomplete. No capability claim changes.

**P22 native runtime provenance refresh (2026-10-26):** The current `linear_p22_v1.provenance()` check returned `ATTESTED`, with native symbols bound, build sources matching, and no issues. Runner/analyzer/source-bundle/dependency-closure hashes remain bound to the previously recorded values. This verifies mechanism provenance and changes no capability claim or P22 lineage/freeze/held-out disposition.

**P22 D4 full-arm g2 continuation (2026-10-26):** The training-only search on draws 0242–0245 added 42,646 attempts to the 30,703-attempt inherited graph; all four tasks stayed stuck and no candidate qualified (candidate `#52306` received 2,646 independent-goal trials). No new approval, receipt, checkpoint, validation access, or held-out access occurred. Resource and native-work digests validate with complete native identity coverage and no unresolved rules. This negative result does not change capability claims; D4 full-arm g3 and the final P22 resource, freeze, and held-out gates remain open. Raw result SHA-256 `2d966fe3aec5b7a18e63cb26e0c066e490d2bea031487d9c6908b072eb18bd92`.

**P22 D4 full-arm g2 follow-up (2026-10-26; reused allocation):** The training-only search on draws 0270–0273 added 40,000 attempts to the 30,703-attempt parent graph; these same training-world IDs appear in the earlier four-arm D4 development artifact. All tasks stayed stuck and no candidate qualified. No new approval, receipt, checkpoint, validation access, or held-out access occurred. Resource and native-work digests validate with complete identity coverage and no unresolved rules. This reused-world result does not support fresh-goal generalization or change capability claims; D4 full-arm g3 and the final P22 resource, freeze, and held-out gates remain open. Raw result SHA-256 `854e1bce991e52fea61a1a4aa910e2b07a0677c88c7b7c06662b59a437930203`.

**P22 Loopover invention-only g2 continuation (2026-10-26):** A fresh distinct-goal search on draws 0058–0061 added 55,000 attempts to its 20,000-attempt inherited graph. All tasks stayed stuck; candidate `#51578` received 15,000 independent-goal trials without qualification. No new approval, receipt, checkpoint, validation access, or held-out access occurred. Resource and native-work digests validate with complete identity coverage and no unresolved rules. This negative training-only result does not change capability claims; the Loopover invention-only descendant and final P22 resource, freeze, and held-out gates remain open. Raw result SHA-256 `50d681ecd22318a98f7ea421b979c0f64c9b401ba64dc17b546263588096c4b5`.

**P22 Loopover full-arm g1 continuation (2026-10-26):** A fresh distinct-goal search on draws 0062–0065 added 60,000 attempts to its 40,000-attempt inherited graph. All tasks stayed stuck; new candidates `#61574` and `#81581` received 20,000 independent-goal trials in total, without qualification. No new approval, receipt, checkpoint, validation access, or held-out access occurred. Resource and native-work digests validate with complete native identity coverage and no unresolved rules. Capability claims remain unchanged; the Loopover full-arm g2 descendant and final P22 resource, freeze, and held-out gates remain open. Raw result SHA-256 `803b27aad5e80b87f5c34da3f52ce1927209cc40f4875ef770b84beceb7f5942`.


**P22 D4 invention-only g3 follow-up (2026-10-26; draws 0266–0269):** This training-only branch added 42,646 attempts to the approved g2 parent's 44,280, with all four tasks stuck. It produced no admissible new candidate or descendant: the inherited malformed `#9459` qualification remains excluded, `#25873` is an identity effect with no qualification, and the only other proposals did not qualify. The attempt export has 86,926 unique IDs (75,402 residual, 11,524 verified, eight exact effects). Resource and native-work digests validate with complete identity coverage. Cumulative declared primitive work reached 916,444, above the 600,000 ceiling, so this branch cannot supply a checkpoint or freeze input. No new approval, receipt, validation, or held-out access occurred; capability interpretation and P22's open gates are unchanged. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0266_0269_p26.json) SHA-256 `0a347e82b43f0efb2323d07fa833153b0bd628d2a62f27fb487c9c8420a93d95`.


**P22 Loopover full-arm g1 continuation (2026-10-26; draws 0102–0105):** The training-only search added 60,000 attempts to its 40,000-attempt inherited graph. All tasks remained stuck; candidates `#61574`, `#71578`, and `#81582` received 20,000 independent-goal trials in total without qualification. No new approval, receipt, checkpoint, validation, or held-out access occurred. Resource and native-work digests validate with complete identity coverage. Capability interpretation is unchanged; the full-arm g2 lineage and final P22 gates remain open. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0102_0105_p26.json) SHA-256 `8ec526d0b23ee759e9581eef73c047693e7636c045ea3af45a9b629efeb0ed59`.

**P22 Loopover invention-only g1 continuation (2026-10-26; draws 0106–0109):** The training-only search added 55,000 attempts to its 20,000-attempt inherited graph. All tasks remained stuck; candidate `#31572` received 15,000 independent-goal trials without qualification. No new approval, receipt, checkpoint, validation, or held-out access occurred. Resource and native-work digests validate with complete identity coverage. Capability interpretation is unchanged; the invention-only g2 lineage and final P22 gates remain open. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0106_0109_p26.json) SHA-256 `c02bcef1c1d6c795c167d3d5e9198e5e6430575053205c5900e8efa03f1b1fb3`.


**P22 Loopover full-arm g1 continuation (2026-10-26; draws 0110–0113):** This training-only branch added 55,000 attempts to the 40,000-attempt inherited graph. All tasks remained stuck; branch-local candidate `#51571` (digest `6591e9d96396fd54161365fc3b6cca83308c75d8f7bdfa90cff1debe5332b00c`) received 15,000 independent-goal trials without qualification. No new approval, receipt, checkpoint, validation, or held-out access occurred. Resource and native-work digests validate with complete identity coverage. Capability interpretation is unchanged; the full-arm g2 lineage and final P22 gates remain open. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0110_0113_p26.json) SHA-256 `5551183edcfa219e5009b6ea9c0f374418894f34cbcbd092a8c22483cf43a0cd`.


**P22 Loopover invention-only g1 continuation (2026-10-26; draws 0114–0117):** The four-goal training-only branch added 55,000 attempts to the 20,000-attempt inherited graph. All tasks stayed stuck, but candidate `#31572` (digest `7fb1f08e6ac6412d271feffcea1bfdec32dd3a484ecfaf42c13fa6a7a681a3ce`) earned one independent-goal qualification on distinct worlds 0114/0115. Its effect is non-identity and absent from the registered parent's 12 active effects. Exact replay reproduced the candidate digest, effect, qualification `#76587`, and distinct witness goals 0114/0115; the 75,000-attempt exports are byte-identical. Resource/native-work digests validate with complete identity coverage. The candidate-specific [request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_INVENTION_G1_0114_0117.md) now awaits exact approval; no checkpoint exists. This proposal-stage result does not change capability claims or close the invention-only g2 and final P22 gates. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0114_0117_p26.json) SHA-256 `bc68b6ba331ce4849154f934289ab7f27c7c87e774598aaa572f0ce16c298a22`.

**P22 Loopover invention-only g1 continuation (2026-10-26; draws 0118–0121):** This training-only branch added 55,000 attempts to its 20,000-attempt inherited graph. All tasks stayed stuck; branch-local candidate `#31572` (digest `6a8aa48a317d8d59d53e3b9616caeb9c4af49eb17fb66a9e998ca808b60d3539`) received 15,000 independent-goal trials without qualification. No new approval, receipt, checkpoint, validation, or held-out access occurred. Resource and native-work digests validate with complete identity coverage. Capability interpretation is unchanged; the invention-only g2 lineage and final P22 gates remain open. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0118_0121_p26.json) SHA-256 `10390a57a511f1e750d67174eb44872e68bb01dbb0639708bf5ec6f351d79c48`.

**P22 D4 full-arm g2 proposal continuations (2026-10-26; draws 0350–0365 and 0370–0385):** Two restored training-only branches from the approved g2 checkpoint added 40,000 attempts each to 30,703-attempt graphs. All eight task instances stayed stuck; three recorded candidates in each branch had zero new qualifications. Resource and native-work digests validate with complete identity coverage and zero unresolved rules. No action, checkpoint, validation or held-out access occurred. These negative searches do not change capability claims; D4 full-arm g3 and the final P22 gates remain open. Raw results are `f9780a926a83dcf2b9e207cb6a810cb65b42696129448700147c43b251915863` and `a2b77c03760810d094d2704db384302b88602c7449476d9c58aaa3f3e9d6d9bc`.

**P22 D4 invention-only g2 continuation (2026-10-26; draws 0340–0343):** This training-only branch added 43,528 attempts to the 44,280-attempt inherited graph. All four tasks stayed stuck. Candidate `#25873` received 3,528 independent-goal trials but has an identity effect; candidate `#9456` received six without qualification, and `#12174`/`#79409` received none. The inherited `#9459` qualification remains invalid because it lacks a qualification kind. No new approval, receipt, checkpoint, validation or held-out access occurred. Resource and native-work digests validate with complete identity coverage. Capability interpretation is unchanged; invention-only g3 and the final P22 gates remain open. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0340_0343_p26.json) SHA-256 `5318217c199603bde00295a6b9349e69d0310a335a084d6f16962c3293bf6596`.

**P22 Loopover full-arm g1 continuation (2026-10-26; draws 0122–0125):** This training-only branch added 60,000 attempts to its 40,000-attempt inherited graph, below the 120,000 ceiling. All tasks remained stuck; two branch-local candidates received 10,268 and 9,732 residual independent-goal trials, with no qualification. No new approval, receipt, checkpoint, validation or held-out access occurred. Resource and native-work digests validate with complete identity coverage and zero unresolved rules. Capability interpretation is unchanged; the full-arm g2 lineage and final P22 gates remain open. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0122_0125_p26.json) SHA-256 `7595ea889c4758a1e302d1f21680d0c775c0424e751f93892a78c79250171acb`.

**P22 D4 invention-only g2 continuation (2026-10-26; draws 0350/0355/0358/0365):** This training-only branch added 42,646 attempts to its 44,280-attempt inherited graph. All four tasks stayed stuck; no new candidate qualified. Candidate `#9456` had one verified and five residual trials, `#9459` had four verified and 108 residual trials but its inherited qualification remains malformed, and identity candidate `#25873` received 2,646 trials. No new approval, receipt, checkpoint, validation or held-out access occurred. Resource and native-work digests validate with complete identity coverage; cumulative declared primitive work (914,449) exceeds the 600,000 ceiling. This cannot produce an admissible g3 checkpoint or change capability claims. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0350_0355_0358_0365_p26.json) SHA-256 `633372167bb3b4328d6e881dd358cde29b33fb19992e12624cdf4660ed9f4664`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0455–0458):** This training-only branch added 42,646 attempts to its 30,703-attempt inherited graph. All tasks remained stuck; candidates `#4022` and `#6521` each received six trials without qualifying, and `#42303` received 2,646 trials without qualifying. No new approval, receipt, checkpoint, validation or held-out access occurred. Resource and native-work digests validate with complete identity coverage. Cumulative declared primitive work (834,872) exceeds the 600,000 ceiling, so this branch cannot supply an admissible g3 checkpoint or change capability claims. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0455_0458_p26.json) SHA-256 `3c03f01c1b6443a530a1fe85ed847eb98e87a4bc75eb86eef7278c0cc15f3336`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0474–0477):** This second fresh-goal branch from the same g2 parent added 42,646 attempts. All tasks remained stuck; candidates `#4022` and `#6521` each received six trials without qualifying, and branch-local `#62309` received 2,646 trials without qualifying. No new approval, receipt, checkpoint, validation or held-out access occurred. Resource and native-work digests validate with complete identity coverage; cumulative declared primitive work (836,209) exceeds the 600,000 ceiling. This cannot supply an admissible g3 checkpoint or change capability claims. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0474_0477_p26.json) SHA-256 `269092f47092ef9ab04fa788ddd32b7e583330e8feb20461f004efc1952bdae3`.

**P22 D4 invention-only g2 continuation (2026-10-26; draws 0430/0435/0438/0445):** This fresh-goal branch added 42,646 attempts to the 44,280-attempt inherited graph. All tasks stayed stuck; no new candidate qualified. Candidate `#9456` had one verified and five residual trials, `#9459` had four verified and 108 residual trials but retains its malformed inherited qualification, and identity candidate `#25873` received 2,646 trials. No new approval, receipt, checkpoint, validation or held-out access occurred. Resource and native-work digests validate with complete identity coverage; cumulative declared primitive work (915,523) exceeds the 600,000 ceiling. This cannot supply an admissible g3 checkpoint or change capability claims. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0430_0435_0438_0445_p26.json) SHA-256 `92b963466c87ba24ded0187613a9d387fff66676105a800711f5c08d217aa982`.

**P22 D4 invention-only g2 continuation (2026-10-26; draws 0460–0463):** A further training-only search added 43,528 attempts to the 44,280-attempt registered parent graph; all four tasks remained stuck. No candidate qualified, and the inherited malformed qualification on `#9459` remains excluded. Resource/native-work digests validate with complete identity coverage; cumulative declared primitive work reached 905,115, above the 600,000 ceiling. No approval, receipt, checkpoint, validation or held-out access occurred. The P22 invention-only g3 descendant and final matched-resource/freeze/held-out gates remain open. Raw result SHA-256 `cce5862dc39d8cbff22c95dbce314477d13dc22da8772d5e6905942a109d86ae`.

**P22 supplementary resource-panel remeasurement (2026-10-26):** The eight training cells for the approved D4 full-g2 and Loopover full-g1 checkpoints were re-run on the registered worlds. All completed with all resource fields measured and valid snapshot digests; the run added no approvals/receipts and accessed no validation/held-out data. This does not change capability claims. The rerun panel is preserved separately as `p22_resource_panel_new_approved_checkpoints_0609_0612_0622_0625_rerun_20261026.json.gz` (SHA-256 `39c1f486e48117da5df14534cd6b6def345549f60a823bd4f68534c085977a88`); the original panel and manifest artifacts remain intact. The updated evidence remains partial at 26/32 checkpoints, with six descendants missing and ceilings unfrozen.

**P22 D4 full-arm g2 reduced-budget continuation (2026-10-26; draws 0480–0483):** Four fresh distinct training tasks remained stuck and produced no qualifying candidate. The branch added 12,646 attempts to its 30,703-attempt parent graph and stayed within the declared primitive-work ceiling at 374,888 cumulative work. No approval, receipt, checkpoint, validation or held-out access was added. This negative search does not change capability claims; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `0f5b801aa2170c5eba43f3cc9fd6a77c48d756edbef1061ac5d608b6ccd8f041`.

**P22 D4 full-arm g2 reduced-budget continuation (2026-10-26; draws 0488–0491):** Four distinct training tasks remained stuck and no candidate qualified. The branch added 12,646 attempts to the 30,703-attempt parent graph and remained within the primitive-work ceiling at 373,198 cumulative work. No approval, receipt, checkpoint, validation or held-out access was added. Capability claims remain unchanged; the D4 full-arm g3 descendant and final P22 gates remain open. Raw result SHA-256 `67085a5d9f363d0285de710fb0634216875535d441f40b50f8324837951d91cc`.

**P22 D4 full-arm g2 reduced-budget continuation (2026-10-26; draws 0512–0515):** Four distinct training tasks remained stuck and no candidate qualified. The branch added 12,646 attempts to the 30,703-attempt parent graph and stayed within the primitive-work ceiling at 373,333 cumulative work. No approval, receipt, checkpoint, validation or held-out access was added. Capability claims remain unchanged; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `2a4622f13a1ba9499d83b2bc0c04a71f3208f7bce88881ad24004778c7681b29`.

**P22 D4 full-arm g2 reduced-budget continuation (2026-10-26; draws 0524–0527):** Four distinct training tasks remained stuck and no candidate qualified. The branch added 12,646 attempts to the 30,703-attempt parent graph; the read-only export covers 43,349 unique attempts (39,474 residual, 3,875 verified) and eight exact effects. Candidate `#37306` repeats a previously nonqualifying expression. These draw IDs overlap the earlier four-arm common-root panel (0522–0533), so this is exploratory negative training evidence and does not count as a fresh independent-goal sample, lineage, or efficacy evidence. No new approval, receipt, checkpoint, validation or held-out access occurred. At 373,333 cumulative primitive work, this branch stayed within the 600,000 ceiling and does not change capability claims. D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `6c1abfd38a86fe9cc2ba214da4d58b8977ae02ef9f55880723646d7bf44b2575`.

**P22 D4 full-arm g2 reduced-budget continuation (2026-10-26; draws 0534–0537):** Four fresh distinct training tasks remained stuck; the branch added 10,000 discovery attempts to the registered g2 parent and produced no new candidate or qualification. The export covers 40,703 unique attempts (37,192 residual, 3,511 verified) and eight exact effects. Draws 0534–0537 do not overlap the earlier 0522–0533 root panel. No action, checkpoint, validation or held-out access occurred; two approvals and receipts are inherited. Resource/native-work digests validate with complete identity coverage, and cumulative primitive work is 348,078. This negative result does not change capability claims; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `ca4276e3bf8dc119ac5a08b6facd15511fd876020f7e0f46ac2cda6d27e8ee3f`.

**P22 D4 full-arm g2 reduced-budget continuation (2026-10-26; draws 0538–0541):** Four fresh distinct training tasks remained stuck; the branch added 10,000 discovery attempts and produced no new candidate or qualification. The export covers 40,703 unique attempts (37,216 residual, 3,487 verified) and eight exact effects. No approval, receipt, adoption, checkpoint, validation or held-out access was added; two approvals/receipts are inherited. Resource/native-work digests validate with complete identity coverage, and cumulative primitive work is 349,792. This negative result does not change capability claims; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `11bffb547fa03ea3bdad4f442dd4f1786f27700ad9946163ee9a2b9842be5eaf`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0542–0545):** Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` on four fresh distinct training goals. The draw IDs were checked against retained P22 artifacts and were unused. Each request used 5,000 discovery attempts; its 5,000-attempt transfer reserve remained unused. The branch added 20,000 attempts to the 30,703-attempt parent graph. The read-only export covers 50,703 unique attempts (45,715 residual, 4,988 verified) and eight exact effects. All tasks remained stuck. Candidates `#4022` and `#6521` each received six independent-goal trials (one verified, five residual); inherited `#22382` received none. No candidate qualified. No new approval, receipt, adoption or checkpoint was created; two approvals/receipts are inherited. Validation and held-out allocations are empty. Resource digest `7a8c00214bd52c3c734185bf54478517bd79aa199532e7868457ab59eed04c94` and native-work digest `d9616b3fcddfde735cfdabf3504eacce33b0e76475a5102ccafe20acb36c831b` validate with complete identity coverage and zero unresolved rules. The run records 216 native steps, 3,332.524 seconds, 2,297,192,448-byte peak RSS (PID `3493676`), and 454,982 cumulative declared primitive work, within the 600,000 ceiling. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0542_0545_budget10k_p26.json) SHA-256 `6cb405cb2691eb27bbf2a1697b9e928b714db1c72e5d62d99ba51ea24fbeb0f7`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0542_0545_budget10k.json) SHA-256 `b5f20da7c24c5bc2dcc43fbc05199cc45081c49f6579ca15e566ec6d1a06ad01` covers all IDs. No admissible D4 full-arm g3 descendant was produced; P22.E2–E3 remain open.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0550–0553):** Continued from the approved D4 g2 checkpoint on four fresh, pairwise-distinct training goals whose draw IDs were unused in retained P22 artifacts. The branch added 12,646 attempts to the 30,703-attempt parent graph; its read-only export contains 43,349 unique attempts (39,405 residual, 3,944 verified) and eight exact effects. All tasks stayed stuck. Candidate `#32300` received 2,646 independent-goal trials (342 verified, 2,304 residual), but repeats the expression digest of candidate `#37306` from prior nonqualifying branches. Candidates `#4022` and `#6521` each received six trials (one verified, five residual); inherited `#22382` received none. No candidate qualified. No new approval, receipt, adoption or checkpoint was created; two approvals and receipts are inherited. Validation and held-out allocations are empty. Resource digest `023607e0c839913d262afd24834912dc41d5c86bd94ee72237cb9952efbf64cf` and native-work digest `6badb4f85d69b336bede439df3fbba51021aff640355ea84b9cd274ca1565815` validate with complete identity coverage and zero unresolved rules. The run records 226 native steps, 3,104.439 seconds cumulative wall time, 2,297,196,544-byte peak RSS (PID `3682828`), and 402,210 cumulative declared primitive work, within the 600,000 ceiling. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0550_0553_budget5k_p26.json) SHA-256 `606dd9d3ccd2c662fcf304816c9ce976cb98a8679b35fdc27246417de9ee7e35`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0550_0553_budget5k.json) SHA-256 `7637f0811c4d705fb46e9fee7ca438e9f13755a43d8b441338c78f6fcd10802a` covers all IDs. No admissible D4 full-arm g3 descendant was produced; P22.E2–E3 remain open.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0554–0557):** Four fresh, pairwise-distinct training tasks stayed stuck. The branch added 10,000 attempts to the 30,703-attempt parent graph; the read-only export covers 40,703 unique attempts (37,155 residual, 3,548 verified) and eight exact effects. Candidates `#4022` and `#6521` each received six independent-goal trials (one verified, five residual); inherited `#22382` received none. No candidate qualified. No new approval, receipt, adoption or checkpoint was created; two approvals/receipts are inherited. Validation and held-out allocations are empty. Resource digest `aad355a3713c1b9a1e81cb3d614cbff358545736f73933085d0643a79b65af2c` and native-work digest `5f273858aaab1ca39c5c173b6658d574ca79c573165a80f1c57b53a2f64ff3da` validate with complete identity coverage and zero unresolved rules. The run records 211 native steps, 2,809.388 seconds cumulative wall time, 2,297,036,800-byte peak RSS (PID `3856289`), and 348,159 cumulative declared primitive work, within the 600,000 ceiling. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0554_0557_budget5k_p26.json) SHA-256 `6ef30bb9db76d6a0e8104cc7903e46f5baaa9b26c06df2648ea0d7b8499b48e0`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0554_0557_budget5k.json) SHA-256 `d776211708b876efd9570582bc68a0b8b2575f86b8363be02013bd7d0be0baf2` covers all IDs. No admissible D4 full-arm g3 descendant was produced; P22.E2–E3 remain open.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0566–0569):** Four fresh, pairwise-distinct training tasks stayed stuck. The branch added 12,646 attempts to the 30,703-attempt parent graph; its read-only export covers 43,349 unique attempts (39,555 residual, 3,794 verified) and eight exact effects. Candidates `#4022` and `#6521` each received six independent-goal trials (one verified, five residual); inherited `#22382` received none. Candidate `#39809` received 2,646 trials (288 verified, 2,358 residual) but repeats the expression digest from prior nonqualifying branches. No candidate qualified. No new approval, receipt, adoption or checkpoint was created; two approvals/receipts are inherited. Validation and held-out allocations are empty. Resource digest `42ec3e647e733da54d365b2105aff08dca56be2f928a2f6eca71b1f0954f6690` and native-work digest `e1b093811bcbfa2ad59465f15afa7efa30618e3770f3ffe73173a5a16ec6c7a5` validate with complete identity coverage and zero unresolved rules. The run records 220 native steps, 3,274.522 seconds cumulative wall time, 2,296,815,616-byte peak RSS (PID `4146357`), and 372,352 cumulative declared primitive work, within the 600,000 ceiling. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0566_0569_budget5k_p26.json) SHA-256 `74942828fc31735d76356b9e2471ac50ee6a2dc120ef505f0cbc8c59e7dd5800`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0566_0569_budget5k.json) SHA-256 `ed21babdb8053eb6155a842156165f9de76bbaa1a29f91f67d5a97c7cf7aed49` covers all IDs. No admissible D4 full-arm g3 descendant was produced; P22.E2–E3 remain open.


**P22 D4 full-arm g2 continuation (2026-10-26; draws 0578–0581):** Four fresh distinct training tasks remained stuck. The branch added 12,646 attempts to the 30,703-attempt parent graph; its read-only export covers 43,349 unique IDs (39,579 residual, 3,770 verified) across eight exact effects. Candidate `#37306` received 2,646 trials (346 verified, 2,300 residual) but repeats expression digest `a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec` from earlier nonqualifying branches. Candidates `#4022` and `#6521` each received six trials (one verified, five residual); inherited `#22382` received none. No candidate qualified. No approval, receipt, adoption or checkpoint was added; two approvals and receipts are inherited. Validation and held-out allocations are empty. Resource/native-work digests validate with complete identity coverage and zero unresolved rules. The run records 219 native steps, 3,336.086 seconds, 2,296,807,424-byte peak RSS (PID `133305`), and 373,598 cumulative declared primitive work, within the 600,000 ceiling. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0578_0581_budget5k_p26.json) SHA-256 `55fa22fdad29a2e36d1c49276ef024068aabf2e08378ad0ae23571e1d3d63363`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0578_0581_budget5k.json) SHA-256 `8c50defdaa6cdf75ae7e2f5ae3d626d387b4808332214f73085baa8d7aa7a20d` covers all IDs. The full-arm g3 descendant and final P22 gates remain open.


**P22 Loopover full-arm g1 qualification (2026-10-26; draws 0126–0129):** Four fresh, pairwise-distinct training goals were searched from checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`); all four tasks stayed stuck. The branch added 17,500 attempts to its 40,000-attempt parent graph. Its read-only export covers 57,500 unique attempts (57,461 residual, 39 verified) and 6,719 exact effects. Candidate `#44071` (digest `20e47b09a3ffcac98a672c43a43cb94c6bccc4a5ae958428d54ff9845ab28b5e`) qualified under `independent_goal_composition` on distinct training worlds 0126/0128; exact replay reproduced the candidate, qualification `#59086`, witness attempts and worlds, and the byte-identical attempt export. Transfer child `#51580` has digest `50b021ab7c8ebc706d9238bdee527c67ed0ae19a77bba2dc0a6115fe97d1a818`; direct audit found both its non-identity effect and the source effect absent from all 12 active parent processes. Candidate-specific [approval request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0126_0128.md) is prepared and awaits exact approval; no action, new receipt or checkpoint was created. One approval/receipt are inherited. Validation and held-out allocations are empty. Source resource/native-work digests `bad1db222202cf3bde4e71095b506b5725865905fe91db10052a715657c5d4eb` and `95985d3a446e5e883ea9f9b1a6186a35b45d4d14827ef7696cd07d8f09d32849` validate with complete native-rule identity coverage and zero unresolved rules. The source records 127 native steps, 1,570.792 seconds wall time, 3,957,927,936-byte peak RSS (PID `343274`), and 292,794 cumulative declared primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0126_0129_budget5k_p26.json) SHA-256 `500787ceac7f618e2a99dcb0bd814a6f649418d18dd5f61bc5e6d36fff21eca0`; exact [replay](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0126_0129_budget5k_p26_replay.json) SHA-256 `33fc4106307607f533376b98ffa42cd4fdff7b13cdcdf167bb507a6fefee6673`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g1_0126_0129_budget5k.json) SHA-256 `3909dd2341bcbd16dd7e2361964f4a6d5e6263b62233712f05caf450344bae8f` is byte-identical to replay. The Loopover full-arm g2 descendant remains pending exact approval; the P22 manifest, freeze and held-out gates remain open.

**P22 D4 invention-only g2 continuation (2026-10-26; draws 0008–0011):** Four fresh distinct training tasks remained stuck. The branch added 7,646 attempts to its 44,280-attempt parent graph; the full read-only export covers 51,926 unique attempts. The identity-effect candidate is ineligible and no candidate qualified. Resource and native-work digests validate with complete rule identity coverage and zero unresolved rules; cumulative declared primitive work is 551,764, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the D4 invention-only g3 descendant and final P22 gates remain open. Raw result SHA-256 `e2979e30ecadda906b00ef896ff1571b4ad29d306278396fd1ce40c08b0c1f68`.

**P22 D4 invention-only g2 continuation (2026-10-26; draws 0040–0043):** Four fresh distinct training tasks remained stuck. The branch added 7,646 attempts to its 44,280-attempt parent graph; the complete export covers 51,926 unique IDs. Identity-effect candidate `#25873` received 2,646 independent-goal trials and remains ineligible; no candidate qualified. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 551,692, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the D4 invention-only g3 descendant and final P22 gates remain open. Raw result SHA-256 `2427f7e8546b2e7494053605f1112d28bca86152a4efcd7523c0f392db6c53b1`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0130–0133):** Four fresh distinct training tasks remained stuck. The branch added 10,000 attempts to its 20,000-attempt parent graph; the full export covers 30,000 unique IDs. New candidates `#24075` and `#25422` received 3,386 and 1,614 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 152,038, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 candidate and final P22 gates remain open. Raw result SHA-256 `83b8d38524d30224e0391c8ea585633c7cbecc4ff5ca7f317dd5e1da5225fea9`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0134–0137):** Four fresh distinct training tasks remained stuck. The branch added 5,000 residual attempts to the 20,000-attempt parent graph; the complete export covers 25,000 unique IDs. No new candidate qualified or was minted. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 121,828, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 candidate and final P22 gates remain open. Raw result SHA-256 `5016ca02154b8674cb0bfff196af00442a9f09f8462c3bd70b1f8a493d73fd3e`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0138–0141):** Four fresh distinct training tasks remained stuck. The branch added 8,750 attempts to the 20,000-attempt parent graph; the full export covers 28,750 unique IDs. Candidate `#24075` received 3,750 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 142,204, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 qualification and final P22 gates remain open. Raw result SHA-256 `966f58ca84fdcef7dd9f23b44846266122717ea807914929e751c17546ef0928`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0142–0145):** Four fresh distinct training tasks remained stuck. The branch added 8,750 attempts to its 20,000-attempt parent graph; the full export covers 28,750 unique IDs. Candidate `#25328` received 3,750 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 145,954, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 qualification and final P22 gates remain open. Raw result SHA-256 `2870ced2379aeebf0cb48930bc76577b7389f0c2a46d1e6cad4d911e45f0b4fe`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0146–0149):** Four fresh distinct training tasks remained stuck. The branch added 8,750 attempts to its 20,000-attempt parent graph; the full export covers 28,750 unique IDs. Candidate `#22822` received 3,750 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 155,422, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 qualification and final P22 gates remain open. Raw result SHA-256 `d01b8bc9b12ac92b88d11c13bb99d607bddc4c2f0754877eef4d02079aedc24b`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0150–0153):** Four fresh distinct training tasks remained stuck. The branch added 10,000 attempts to its 20,000-attempt parent graph; the full export covers 30,000 unique IDs. Candidates `#22915` and `#25329` received 3,386 and 1,614 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 150,266, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 qualification and final P22 gates remain open. Raw result SHA-256 `10e7a01feb41caba42d60be265cddb6ae389a6b7210c37e9f109f9ea2a4f8159`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0154–0157):** Four fresh distinct training tasks remained stuck. The branch added 8,750 attempts to its 20,000-attempt parent graph; the full export covers 28,750 unique IDs. Candidate `#26581` received 3,750 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 142,204, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 qualification and final P22 gates remain open. Raw result SHA-256 `82b456b1f52784be4d5cf872f4320ec628159b147de1b6146dd0d0993dd88d15`.

**P22 Loopover invention-only g2 continuation (2026-10-26; draws 0158–0161):** Four fresh distinct training tasks remained stuck. The branch added 8,750 attempts to its 20,000-attempt parent graph; the full export covers 28,750 unique IDs. Candidate `#24075` received 3,750 independent-goal trials without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 145,954, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; the Loopover invention-only g2 qualification and final P22 gates remain open. Raw result SHA-256 `785f8e26b156694f6c06172334cbc185ed1a87f06da055e8283bc5052b4a5436`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0588–0591):** Four fresh distinct training tasks remained stuck. The branch added 5,000 attempts to its 30,703-attempt parent graph; the complete export covers 35,703 unique IDs. No candidate qualified; inherited candidate `#9440` had 222 trials, and `#4022`/`#6521` had six each. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 309,089, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `07e808d8df1e9b63f461827857892439d6aa732b0c799b253876f23e5d18354e`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0653–0656):** Four fresh distinct training tasks remained stuck. The branch added 5,000 attempts to its 30,703-attempt parent graph; the complete export covers 35,703 unique IDs. No candidate qualified; inherited candidate `#9440` had 222 trials, and `#4022`/`#6521` had six each. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 309,314, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `96a2713ad2183ff859247b8659f2f886596606301f3aad674828b01103d8b11a`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0657–0660):** Four fresh distinct training tasks remained stuck. The branch added 10,000 attempts to its 30,703-attempt parent graph; the complete export covers 40,703 unique IDs. No candidate qualified; inherited candidate `#9440` had 222 trials, and `#4022`/`#6521` had six each. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 348,237, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `81177acaf5d17ce6591f0ecc34e086edad221ea3511425f49a0144aa75d2f1a3`.

**P22 D4 full-arm g2 continuation (2026-10-26; draws 0673–0676):** Four fresh distinct training tasks remained stuck. The branch added 12,646 attempts to its 30,703-attempt parent graph; the full export covers 43,349 unique IDs. No candidate qualified; candidate `#32300` repeats a prior nonqualifying expression after 2,646 trials, and `#4022`/`#6521` had six each. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 402,539, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation or held-out access was added. Capability interpretation is unchanged; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `9bb6ebf4bac4ddfafcad64c7c3ea76e08284bfd374f1fb9512b35a0f41200cb3`.

**P22 D4 full-arm g2 continuation (2026-10-27; draws 0681–0684):** Four fresh distinct training tasks remained stuck. Candidate `#34803` repeated a prior nonqualifying expression after 2,646 independent-goal trials; inherited candidates `#9440`, `#4022`, and `#6521` received 222, six, and six trials. The complete export contains 43,349 attempt IDs. Resource and native-work digests validate with complete identity coverage and zero unresolved rules; cumulative declared primitive work is 372,854, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation, or held-out access was added. Capability interpretation is unchanged; D4 full-arm g3 and final P22 gates remain open. Raw result SHA-256 `8b1e1219b9cd26517f4cfc48ddb0a192ab76a4301055bd3285e86811b711147d`.

**P22 Loopover invention-only g2 continuation (2026-10-27; draws 0162–0165):** Four fresh distinct training tasks remained stuck. The branch added 10,000 attempts to its 20,000-attempt parent graph; the full export covers 30,000 unique IDs. Candidate `#24072` had 7,500 independent-goal trials and inherited candidate `#6542` had 15,000, without qualification. Resource/native-work digests validate with complete rule identity coverage; cumulative declared primitive work is 157,504, within the 600,000 ceiling. No approval, receipt, adoption, checkpoint, validation, or held-out access was added. Capability interpretation is unchanged; Loopover invention-only g3 and final P22 gates remain open. Raw result SHA-256 `16210949da2d56a371e59b750408b36a5f867df6c57e2f01f65d6f582fac36ff`.
