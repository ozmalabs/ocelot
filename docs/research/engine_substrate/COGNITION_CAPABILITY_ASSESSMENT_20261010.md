# Cognition capability assessment of the substrate (2026-10-10, revision 2)

Purpose: lay out the shape of cognition the substrate already has, component by component, so the missing parts become visible. Every component gets the same questions: what is its aperture, what is its admissibility, does it feed or read qualia, and can it think further (extended thinking).

**Revision 2.** Revision 1 (`be59ad24`) listed eleven "absent" faculties. A second audit found that eight of them exist, and that the three "empty stubs" are declarative knowledge seeds, not empty files. The error came from searching for lab-paradigm names (Stroop, subitizing, do-calculus, HTN) and checking only `rules` arrays. The audit then counted rules and productions per seed and checked `self_load_only`, opt-in guards and CORE_SEEDS membership. Section 4 now holds the corrected inventory, and sections 1, 3, 5 and 6 were revised to match. All claims come from reading code and seeds at `be59ad24`. No tests were run for this report.

Maturity scale:
- **C**: in CORE_SEEDS (`substrate/boot_core.py:20`), so loaded on every `boot_core()`.
- **Prof**: in the opt-in conversation production profile (`substrate/boot_profiles.py` `CONVERSATION_SEED_ANCHORS`).
- **Bulk**: loaded by the full-corpus `load_all_seeds` but not by core.
- **SLO**: `self_load_only`, loaded on demand by a domain module and skipped by bulk boot (`boot_all.py:100`).
- **Off**: rules guarded on an opt-in node or attribute, so default behaviour is byte-identical.
- **Py**: Python only.
- **Decl**: concepts or head/body principles, which `seed_loader.normalize_declarative` turns into Concept/Principle nodes, not engine Rules.
- **∅**: absent.

## 1. Headline

The substrate covers most of the classical faculty map. It has executable graph rules for:
- working memory with capacity, interference and expiry;
- episodic replay and consolidation;
- forgetting, through decay tiers and budget eviction;
- generative world-model rollouts and default-mode prospection;
- detached imagination;
- dual-process arbitration with conflict escalation;
- interventional causal discovery;
- goal construction and decomposition;
- first-order theory of mind;
- language production;
- appraisal emotions and arousal self- and co-regulation.

Much of it, though, is not on by default. Outside CORE, faculties are SLO, Off-guarded, or loaded by one profile. So the real gap is not whether a faculty exists. It is whether the faculties are wired together and on.

The structural weaknesses from revision 1 still hold. They are about the *proposal* half of cognition, not about missing faculties:
- **Graded admissibility in the graph.** Gates are hard tubes or exact matches. Soft scoring lives in Python.
- **A general extended-thinking executor.** Escalation requests (`synthesis_requested`, `needs_decomposition`, `needs_tool`) have no consumer. Deepening never re-admits options it pruned.
- **Aperture.** Each domain has its own stipulated aperture. The general relax rule is binary.
- **Qualia as a cache.** There are three disjoint stores, minting happens in Python, and cross-domain recall has never been tested.
- **A Seldon/Thought manifold generator.** The manifold can select a future but has no projector, refinement or cache.

## 2. Component map (cognition core)

| # | Component | Where | Role | Maturity |
|---|---|---|---|---|
| 1 | Standard codebook | `ShapeSignature`/`MetaShape` (`shape_decode.rs:336 load_parts`); `DimensionGenerator` (`:682`); 5 seeded in `shape_decode_loop.json`; `meta_shape_growth.json` (10 rules) points the same Terms at MetaShape | Vocabulary of parts and generators | Bulk; grows by minting |
| 2 | DimInfer | `eval_dim_infer` `shape_decode.rs:3031`; `sd_infer_dimension`, `msg_infer_dimension` | Generator×k explaining `coord:*` dims | Bulk |
| 3 | GenInfer | `eval_gen_infer` `shape_decode.rs:3901` | Induce a new generator | Off (`gen_infer_enabled`, Cargo features) |
| 4 | TimeInfer / order-N | `time_axis.json`; `domains/order_n_concepts.py` | Temporal axes; finite differences | Bulk / Py |
| 5 | ShapeDecode / TransformDecode | `shape_decode.rs` | Perception front end | Bulk |
| 6 | Seldon manifold | `future_manifold.rs`; `FutureManifoldProjection/Selection` (`term.rs:3238`) | Select reachable futures under a resolved-dims mask | Bulk; fallback `motor_compose` |
| 7 | ThoughtManifold | `regulated_train_of_thought.py`, `conversation_deliberation.py` | Regulated deliberation | Py ("planning only") |
| 8 | Generative world model | `generative_world_model.json` (37 rules and productions) | Action-conditioned branching imagined rollouts with pruning; compare to grounded outcome | **C** |
| 9 | Salience / attention | `residual_salience.json`, `fovea_salience_bridge.json`, `salient_cache.json` | What reaches the inferers | Bulk |
| 10 | Aperture | `observer_aperture.json`, `aperture_frame.json`, plus domain apertures | Resolution and scope of a read | Bulk + fragments |
| 11 | Admissibility Γ | `grammar.rs`; `substrate.rs admissible_moves` | Legal and weighted moves | Hard only |
| 12 | Qualia field | `qualia_space.json` (Decl), `lexical_qualia.json` (parked), Shape sig_0..7 + valence | Compressed felt representation | Py mint / graph match |
| 13 | Metacognition | prediction-world `judge_robust`; `dual_process_core`; `cognitive_supervision`; `generative_skeptic` (Decl + Py) | Judge, arbitrate, supervise | Mixed (see §4) |

## 3. The matrix: aperture × admissibility × qualia × extended thinking

| Component | Aperture | Admissibility | Qualia | Extended thinking |
|---|---|---|---|---|
| Codebook | Partitioned by node type; no similarity index | Exact equality on recall | None; recall is generate-and-test | Grows only by minting; no "search wider" mode |
| DimInfer | `grain` requantize from `agent.dim_grains`, the only relaxation | Hard: equal relation counts, `max_dims`, composition ≤ 2 | None | Pass-2 Occam short-circuit; fixed depth 2 |
| GenInfer | Data-derived bound B | Exact; optional MDL witness routes outliers to `sd_mdl_outliers` | None | Exhaustive O((2B+1)^4); no linear→quadratic→coupled ladder; coupled-quadratic transfer 0/10 |
| TimeInfer | Needs integer, exactly regular streams | Exact | None | None; order-N is Python |
| ShapeDecode | Name scope (no measured live benefit) | Exact `build_candidate` | Shape sigs feed the qualia match | Internal beam/budget, not graph-exposed |
| Future manifold | `future_manifold_resolved_dims`, stipulated by `stress_aperture.json` | Hard tube; relaxation only in the Python twin | `shape_snapshot` capped at 7 dims; no cache | Budget from `arousal_horizon`; `refinement_count` always 0; no projector |
| Generative world model | `horizon`, `maximum_branching` on SimulationRequest | `prune_terminal_*` rules | None | Bounded branching rollouts: the one graph-native tree search. Requested by default mode or counterfactual experiments, not by impasse |
| Salience | `fovea_resolve` ArgminUnique | Graph-weighted (the only such selector) | L1 match vs Shape sigs (`valence_salience`) | None |
| Aperture (general) | `af_effective_aperture` Intersect meet | `af_relax_chosen` binary, residual-driven (motivated inattention) | None | `obs_established` written, never read |
| Γ | n/a | Weights summed; no softmax in Rust; integer-only `ParetoDominates`; literal tolerances | None | No relax-to-find-more loop |
| Qualia field | QualiaAperture k (Python) | `SHAPE_MATCH_TOL=2.0` literal | Three disjoint stores | No cross-domain recall tested |
| Dual process | Admits SystemTwoTaskSet areas | Continuous System-2 weight; conflict, near-conflict and low-confidence escalation | None | Admits areas; does not widen candidates |
| Capability collapse / impasse | Pre-authored chain; orders 2–6 | Static | None | `synthesis_requested`, `needs_decomposition`, `needs_tool` have no consumer |
| Program synthesis | Grammar | Test-based | None | Real propose→enumerate→accept ladder with cache; code domain only |

## 4. Faculty inventory (corrected)

Each verdict states what exists and what is actually missing inside that faculty.

| Faculty | What exists (executable unless noted) | Boot status | Tests | Real gap |
|---|---|---|---|---|
| **Working memory capacity, interference, forgetting** | `episodic_working_memory_core`: `maximum_slots 4`, `slot_ttl_epochs 8`, five gates (input/update/maintain/output/clear), `working_memory_replace_cross_task_interference` (cross-task replacement of the lowest-priority slot), `working_memory_refuse_same_task_over_capacity`, `working_memory_expire_unmaintained_slot`. `staleness_decay` (integer half-life freshness), `demotion_hierarchy` (FRESH/GIST/LATENT, delete latent), `can_decay_identity`. Rust `memory.rs`: `forget_over_budget` (keep-value-per-byte eviction), `roll_disposable` (sensory ring buffer), `shuffle` (cold-cluster paging) | EWM **C**, enabled; decay seeds SLO + Off | `test_episodic_working_memory_migrated.py` 18; staleness 7; demotion 8; salient_cache 9 | Decay tiers are not on by default; WM capacity is a stipulated 4 |
| **Offline replay and consolidation** | `episodic_prioritize_one_replay_per_cycle` (wake and offline modes; salience + 2·surprise + value + novelty decay), `episodic_replay_creates/updates_semantic_support` (episode→schema), `episodic_reconsolidate_after_retrieval`; Rust `consolidate` to disk + ShapeIndex; `default_mode_mint_episode_context` replays consolidated episodes when idle | **C** | EWM offline-replay test; `test_default_mode_core_migrated.py` 8 | No production code mints `MemoryCycle` (only tests do), so offline replay has no driver in a live loop. No sleep regime schedules it |
| **Imagination / simulation** | `generative_world_model` (C) rollouts; `default_mode_request_content_bearing_simulation`; `counterfactual_experiment` routes graph self-tests into detached imagination and keeps the results as non-oracular evidence; `composer_imagination_graph` (graph-authored ENGAGE); `imagination.py` is the mechanical snapshot/cut-grounding/run/diff/reground machinery, and the graph decides when | GWM, DMN **C**; others Bulk; `imagination` module in Prof runtime | `test_imagination.py` 12, `test_imagination_cognition.py` 13, trace retention 9, GWM 5 | Not triggered by impasse; imagined results are not routed back to the extended-thinking requesters |
| **Mental rotation / imagery** | `rotation90`, reflections, `scale2`, `cycle4` generators with DimInfer recognition under transformation; `latent:rotation90` minted | Bulk | `test_dimension_inference_migrated.py` and others (~13 files) | Discrete generator inference only: no analog, angle-cost rotation and no pictorial imagery buffer |
| **Executive / cognitive control** | `dual_process_core` (20 rules / 17 productions): continuous System-2 weight, `escalate_instinct_conflict`, `escalate_near_conflict` (conflict monitoring), task-set recruitment (`SystemTwoTaskSet`), devaluation, extinction, reversal. Rust `CyclePlan::DualProcess`, `admit_system_two`. `adaptive_control_core` (C): TD errors, eligibility traces. `default_mode_interrupt_for_salient_external_demand` (mode switching). `cognitive_supervision`: goal-tree leases, holding a dominated or zero-yield process | dual_process **optional** (`OPTIONAL_CORE_SEEDS`); adaptive control, DMN **C**; supervision Bulk | dual_process 21; supervision 25; adaptive 10; DMN 8 | No explicit stop/no-go response-inhibition primitive. `cognitive_cycle.rs:557` says dual_process is core, contradicting `boot_core.py:33`; this needs reconciling |
| **Causal reasoning** | `experimentation_core` (C): `intervention_lift`, `hypothesis_test` terms. `remote_causal` (12): exhaustion-first exploration, interventional do-contrast (`rc_confirm_interventional`: eff_act==1 ∧ eff_noop==0), refutation, remote attribution, with causal_prior/local_only/no_intervention controls. `remote_causal_ground`, `published_net_causal_debugger` (do-contrast utility, restoration evidence), Rust `can_ops` causal-influence edges, `communication_causal_*` (causal QA) | C (terms); `remote_causal` Off (`remote_on`); debugger study-gated; causal QA Prof | remote_causal 16; ground 13; debugger 4; causal retrieval 9; CAN ~61 files | No formal SCM / do-calculus / backdoor adjustment. LS20 remote: offline gates pass, live link null (`LS20_REMOTE_RESULTS.md`) |
| **Planning / goal decomposition** | `goal_construction` (C) mints and chunks goals; `goal_derivation` (one-step means-ends Argmax); `ls20_planning` (salience→investigate→act); `arc_decompose` (order-N child goals per tier); `cognitive_supervision` (arbitrary-depth goal tree); `hierarchical_effector_control` (motor-program unrolling); `operational_planning` (instruction→capability) | goal_construction **C**; ls20 Off (`plan_on`); arc_decompose SLO; others Bulk | ls20 7 (results: curious 1.0 vs blind 0.0, N=100); arc_decompose 28; effector 5; operational 14; goal_derivation 0; compositional_plan 0 | No domain-general multi-step search planner over graph states; goal_derivation and compositional_plan are untested |
| **Theory of mind** | `character_tom.py`: propositional-attitude construction decoded by ShapeDecode, nested belief-world SmEntities, desire goals on an intentionality index, unseen attitude verbs joining the class by adjacency. `bigville_theory_of_mind`, `tom_meta_shape` (attributed mental state as a MetaShape, decided by Rust RecogniseShape/MetaShapeMint), `interlocutor_model`, `audience`, `abusive_n3_belief_propagation` | Domain-loaded; interlocutor seeds Prof | character_tom 18 (incl. Sally-Anne); interlocutor 24; tom_meta_shape 5; bigville_tom 4; proposition beliefs 9 | First order only; no test of recursive (A believes B believes X). Four ToM systems, partly unified (`TOM_SYSTEM_UNIFICATION_RESULTS.md`). `modality_tom` itself has 1 modality rule and no tests |
| **Language production** | About 20 executable reply/realization seeds (`self_account_reply`, `conversation_*_reply`, `communication_*_reply`, `recount_realization`, `recount_analysis_realization`, `recount_fluency`, `gamma_production_adopt`, `speech*`); `language_production.py` (Levelt pipeline with a self-monitor round-trip) used live by `world_adapter._self_account_producer` | **Prof** (the production daemon) | ~51 test files (recount 12/16/11/12, self-prose 11, voice 10, …) | Surface realization is mostly Python; `lang_production.json` and `production.json` are Decl theory |
| **Emotion and regulation** | `affective_state_core` (C): leading drive, canonical affect. `core_emotions` (24 rules: appraisal→action tendency for fear, anxiety, anger, frustration, disgust, joy, sadness, curiosity, boredom, fulfilment, pride, surprise). `self_conscious_emotions`, `mood_r1` (mood bias and momentum). `arousal_window_coreg`: window of tolerance, hyper/hypo dysregulation, `selfreg_pull`, `coreg_pull`, window widening and narrowing. `arousal_horizon` sets the planning horizon from regulation | affect **C**; emotions/mood/coreg SLO + Off | core_emotions + ~10 files; self-conscious 8 files; mood r1b/r1c; arousal_horizon | No strategy-level regulation (cognitive reappraisal, suppression): regulation is arousal-level only |
| **Numerosity** | `number_world.py`: magnitude grounded in countable unit tokens, succ line, count up/down; `number_qualia` capability experiment (transfer of a felt band, not number sense) | Py world adapter | `test_number_world_migrated.py` 5 | **Absent**: subitizing, approximate number system, Weber-ratio discrimination |
| **Imitation / social learning** | Concepts only (`mirror_neuron`, `psy_social` prose principles); `glassbox_r1_social` is coordination via trade, not imitation | Decl | none | **Absent** as a mechanism |
| **Sleep regime** | Offline replay mode exists (above) | — | — | **Absent**: no sleep/consolidation scheduler or dream stage, and no producer for offline `MemoryCycle` |

Corrections to revision 1's "stubs" and "remnants":
- `generative_skeptic.json` holds six FailureLesson concepts (patterns, probe templates), consumed by `domains/generative_skeptic.py` and `autonomous_curation.py`. It is Decl + Py and untested.
- `invariant_representation.json` holds six concepts and five relations. It is Decl, and its source `.py` has been deleted.
- `seven_meta_shape_subsystems.json` holds 26 concepts and 6 head/body principles. It is Decl, and `mechanism_in