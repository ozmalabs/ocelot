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
| Request object | Yes, consumed opt-in | `synthesis_requested` (capability_collapse) is consumed by `capability_synthesis_bridge` (opt-in); `Impasse -needs_decomposition-> CapabilityAxis` (impasse_escalation) is consumed by `decomposition_consumer` (opt-in); `Fault.needs_decomposition` (repair_escalation) remains unconsumed; `needs_tool` → `self_extension` composes an operator from held primitives |
| Area admission | Yes | `admit_system_two` admits SystemTwoTaskSet areas, with lease and staleness checks |
| Shared budget / anytime object | Yes (opt-in) | `thinking_budget.json` (`ThinkingBudget`, `tb_refill_once_per_epoch`, `tb_fund_from_horizon`, `tb_debit_request`, `tb_record_exhaustion`), integrated with `impasse_simulation_bridge`, `consolidation_scheduler`, and `boot_cognition_on()` |
| Graded relaxation of admissibility | Metadata + primitive ready | `SoftWeights` Term in Rust; `tolerance_registry.json` (`Tolerance` metadata linked via `governs_policy` to policy nodes); inline tolerances migrated to `SaliencePolicy.shape_match_tolerance` and `DimInferPolicy.dim_grains`; `af_relax_chosen` graded on `ap_relax_tolerance`. (Active relax/restore executor loop is Phase 3) |
| Widening of aperture | Partial (`aperture_frame` questioning landed) | `aperture_frame.json` now probes bypassing chosen frames after `ap_question_after` generations and drops hiding chosen frames; `DimInferPolicy.dim_grains` is graph-governed; domain apertures remain separate |
| Re-admission of pruned candidates | No | Motor collapse and the bigville core never re-admit |
| Generative proposal | Domain-bound | `ps_propose`/`SynthEnumerate` (code); GenInfer (matrices); GWM rollouts (actions); no manifold projector |
| Tree search over graph states | Partial | GWM bounded branching rollouts with `prune_terminal_*` (C); the ShapeDecode internal beam |
| Imagination | Yes, including opt-in impasse trigger | Detached imagination and counterfactual_experiment run on idleness or explicit request; `impasse_simulation_bridge` (opt-in) triggers GWM counterfactual rollouts on `dual_process_core` `instinct_conflict` escalations |
| Verification | Yes | `build_candidate`, the MDL witness, the grounded-outcome comparison in GWM, the judge |
| Settling back and caching | Domain-bound | `ps_accept`; codebook minting; EWM consolidation; the manifold does not cache |

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
