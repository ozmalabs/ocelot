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
