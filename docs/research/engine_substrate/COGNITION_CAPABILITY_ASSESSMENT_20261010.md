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
