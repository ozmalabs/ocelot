# Cognition capability assessment of the substrate (2026-10-10)

Purpose: lay out the shape of cognition the substrate already has, component by component, so the missing parts become visible. For every component the same four questions are asked: what is its aperture, what is its admissibility, does it feed or read qualia, and can it think further (extended thinking). Every claim below comes from reading code and seeds at `2cd46a6a`. Python-only mechanisms are marked as such, because the graph is supposed to decide and Python is supposed to be mechanical.

Maturity scale: **P** = in production (in CORE_SEEDS or on the default path); **G** = gated (feature flag or agent flag, off by default); **O** = optional seed, not in CORE_SEEDS; **Py** = Python only; **D** = design doc only; **∅** = absent or an empty stub.

## 1. Headline

The substrate is strong at exact, exhaustive, closed-world induction. The codebook, DimInfer, GenInfer, TimeInfer and ShapeDecode all generate candidates and test them for exact equality, and the Occam/MDL ordering is good. It is weak at everything that makes cognition fast or flexible:

- **No graded admissibility in the graph.** Every gate is a hard tube or an exact match. Soft scoring exists only in Python.
- **No general extended-thinking faculty.** Escalation signals exist (`synthesis_requested`, `needs_decomposition`, `needs_tool`), but nothing consumes them. Deepening climbs pre-authored chains and never re-admits options it pruned.
- **Aperture is fragmented.** There are at least six domain apertures with no shared frame. The general aperture-relaxation rule is binary and residual-driven, and it produces motivated inattention.
- **Qualia is not yet a cache.** There are three disjoint representations. Shapes are minted in Python. No stored quale has ever been recalled across domains.
- **The Seldon/Thought manifold is three implementations with no generator.** It can select a feasible future but cannot project moves into trajectories, refine itself, or cache what it found.

In short, the substrate has the *verification* half of cognition and lacks most of the *proposal* half: widening the search, relaxing the gates, and recalling by similarity.

## 2. Component map

| # | Component | Where | Role | Maturity |
|---|---|---|---|---|
| 1 | Standard codebook | `ShapeSignature`/`MetaShape` nodes (`shape_decode.rs:336 load_parts`); `DimensionGenerator` nodes (`:682 load_generators`); 5 seeded in `seeds/shape_decode_loop.json` | Vocabulary of parts and generators | P (grows by minting) |
| 2 | DimInfer | `TermNode::DimInfer`; `eval_dim_infer` `shape_decode.rs:3031`; rule `sd_infer_dimension` | Find the generator×k that explains `coord:*` dims | P |
| 3 | GenInfer | `eval_gen_infer` `shape_decode.rs:3901` | Induce a new generator (2×2 integer matrix, quadratic, full-rank) | G (`gen_infer_enabled`, Cargo features) |
| 4 | TimeInfer / order-N | `seeds/time_axis.json`; `domains/order_n_concepts.py` | Infer temporal axes; finite differences as Term-trees | P (TimeInfer) / Py (order-N) |
| 5 | ShapeDecode / TransformDecode | `shape_decode.rs` | Decode an observation into parts and transforms (internal beam/budget) | P |
| 6 | Seldon manifold (future manifold) | `future_manifold.rs`; `FutureManifoldProjection/Selection` (`term.rs:3238`) | Project and select reachable futures under a resolved-dimension mask | P (generic), fallback `motor_compose` |
| 7 | ThoughtManifold | `domains/regulated_train_of_thought.py`, `conversation_deliberation.py`, `world_adapter.py` | Regulated deliberation trajectory | Py ("planning only" per production plan) |
| 8 | Salience / attention | `seeds/residual_salience.json` (`valence_salience`), `fovea_salience_bridge.json` (`fovea_resolve`), `salient_cache.json` | Choose what to attend to; working-memory salience | P |
| 9 | Aperture | `seeds/observer_aperture.json`, `seeds/aperture_frame.json`; plus domain apertures | Choose the resolution and scope of a read | P (general) + fragments |
| 10 | Admissibility Γ | `grammar.rs` (weight Term, exp(w)); `substrate.rs admissible_moves` | Which moves are legal or weighted | P (hard) |
| 11 | Qualia field | `qualia_space.json` (16 dims, no rules); `lexical_qualia.json` (PARKED); Shape nodes sig_0..7 + valence | Compressed, felt representation | Py mint / P match |
| 12 | Dual process | `dual_process_core`, `cognitive_cycle.rs admit_system_two` | Escalate to System 2 | O |
| 13 | Capability collapse / escalation | `capability_collapse`, `impasse_escalation` (orders 2–6), `repair_escalation` | Deepen on residual or impasse | P, but consumers are missing |
| 14 | Program synthesis | `program_synthesis` (`ps_propose` → `SynthEnumerate` → `ps_gap_file`, `ps_accept` caches) | Best existing proposal ladder | P (code domain only) |
| 15 | Analogy | `domains/analogy_search.py` | Signature-based analogy | Py, single pass |
| 16 | Default mode | `default_mode_core` | Idle-time recombination | P, triggered by idleness only, results not cached back |
| 17 | Affect / valence | Shape valence; `AFFECT_WEIGHTED_ROUTE_VALUATION_DESIGN.md` | Valuation signal | Partial |
| 18 | Metacognition (judge) | prediction-world `judge_robust` (loop 1.11.0) | Trend and aperture judge over N views | P (prediction world only) |
| 19 | Memory | episodic/WM seeds, `salient_cache` | Store and recall | P for working memory; no capacity or interference forgetting |

## 3. The matrix: aperture × admissibility × qualia × extended thinking

| Component | Aperture | Admissibility | Qualia | Extended thinking |
|---|---|---|---|---|
| Codebook | Partitioned by node type only; no similarity index | Exact equality on recall | None: recall is generate-and-test, not lookup | Grows only by minting (`sd_mint_generator`, `_quadratic_`, `sd_chunk_composite`, `sd_mint_quantum`); there is no "search wider" mode |
| DimInfer | `grain` requantize `floor((v-min)/2^g)` from `agent.dim_grains`, which is the only relaxation | Hard: equal relation counts, `max_dims`, composition ≤ 2 | None | Pass-2 Occam short-circuit (91% saved); depth is fixed at 2, with no deepen-on-failure |
| GenInfer | Data-derived bound B | Exact, plus optional MDL witness (`geninfer_grain_mdl`) that routes outliers to `sd_mdl_outliers` | None | Exhaustive O((2B+1)^4); coupled-quadratic transfer is 0/10; no ladder from linear to quadratic to coupled |
| TimeInfer | Needs integer, exactly regular streams | Exact | None | None; order-N lives in Python |
| ShapeDecode | Name scope, which gives no measured live benefit | Exact build_candidate | Shapes sig_0..7 feed the qualia match | Internal beam/budget, not exposed to the graph |
| Future manifold | `policy.future_manifold_resolved_dims` mask, set only by `stress_aperture.json` (stipulated, not chosen); an unresolved dimension counts as `information_loss` | Hard tube; relaxation only in the Python twin (`future_option_risk.py`) | `shape_snapshot` capped at 7 dims; no cache | Budget from `arousal_horizon.json`; `refinement_count` is always 0; no generative projector |
| ThoughtManifold | Python | Python | Python | Python |
| Salience | `fovea_resolve` ArgminUnique | Graph-weighted, the only place this is true | L1 match against Shape sigs (`valence_salience`) | None |
| Aperture (general) | `af_effective_aperture` = Intersect meet; forced and negotiated modes | `af_relax_chosen` is binary and residual-driven (motivated inattention, `APERTURE_PATHOLOGIES.md`) | None | `obs_established` is written but never read, so "compressed" and "mastered" look the same |
| Γ | Not applicable | Weights summed in `admissible_moves`; **no softmax in Rust**; `ParetoDominates` is integer-only; tolerances are scattered literals; soft excluders only in `frame_inference_v2.py` | None | No relax-to-find-more loop; `FRAME_AND_DIMENSION_AS_EDGE.md` is design only |
| Qualia field | QualiaAperture k (Python `felt_aperture_read`) | `SHAPE_MATCH_TOL=2.0` literal | Three disjoint stores | No cross-domain recall tested; transfer is recipe-level only (track_j, track_j4) |
| Dual process | Admits rule areas | Triggers: prediction_error, novelty, uncertainty, conflict, low_confidence, etc. | None | Escalation admits areas; it does not widen candidates |
| Capability collapse | Pre-authored chain | Static | None | `cc_request_synthesis_no_higher_program` sets `synthesis_requested=1`, which **has no consumer** |
| Impasse escalation | Orders 2–6 | Static | None | `order3_reframe` `needs_decomposition` and `order4_self_extend` `needs_tool` are unconsumed or weakly consumed |
| Motor decision collapse | Not applicable | `settle_tol` is static | None | Deepening never re-admits pruned options |
| Program synthesis | Grammar | Test-based | None | A real ladder with an acceptance cache, but code only |
| Default mode | Idle | None | None | Not triggered by impasse; results are not cached back |
| Judge (prediction world) | Salience-selected views, all levels in scope at aperture 0 | Magnitude-weighted Z over views | None | Rehearsal plus confirm-before-commit (v10); H15 failed its margin |

Reading the matrix by column:

- **Aperture.** Each component owns a private, stipulated aperture. None is chosen by evidence or value of information, and none is an Observer frame the rest of the graph can reason over.
- **Admissibility.** Hard everywhere except fovea salience and the prediction-world judge. Every relaxation knob is a literal or a Python parameter.
- **Qualia.** Read in exactly one place (`valence_salience`) and written in no graph rule. It is not functioning as a cache.
- **Extended thinking.** Plenty of triggers, no executor. The one working executor (program synthesis) is bound to a single domain.

## 4. "?? what else": components the list omitted

Present in the substrate and part of the shape of cognition:

1. **TimeInfer / order-N.** This is the temporal sibling of DimInfer. Order-N (finite differences as Term-trees) is how trends are judged ("this is what order N is for"), but it is Python-only, and TimeInfer rejects irregular streams.
2. **ShapeDecode / TransformDecode.** The perception front end that DimInfer and GenInfer serve.
3. **Salience / attention.** It decides what reaches the inferers. It is the only graph-weighted selector.
4. **Γ admissibility grammar.** The common gate under every component.
5. **Episodic and working memory.** `salient_cache` and related seeds.
6. **A generative world model.** Prediction-world experts and the future manifold. It predicts but does not imagine.
7. **Analogy** (`analogy_search`). This is the natural consumer of qualia.
8. **Dominance / multi-objective selection** (`ParetoDominates`).
9. **Metacognition**, now the trend/aperture judge.
10. **Affect and valence** as a valuation channel.
11. **Default mode** (offline recombination).

Absent, empty, or design-only (the holes in the shape):

- Imitation and social learning.
- Numerosity and subitizing as a native faculty. `number_qualia` is a Python test harness.
- Mental rotation and imagery. Generators exist, but there is no imagery workspace.
- General causal-graph reasoning / do-calculus.
- Graph-native recursive theory of mind / false belief (`modality_tom`: r1, 0 tests; ToM modules are Python).
- Domain-general hierarchical planning (`goal_derivation`, `compositional_plan`: 0 tests).
- Language production (`lang_production`, empty manifest).
- Capacity- and interference-based forgetting.
- Executive inhibition and task switching.
- Emotion regulation and reappraisal.
- A sleep or consolidation regime (default mode is the nearest, and it does not consolidate).
- Empty stubs: `generative_skeptic`, `invariant_representation`, `seven_meta_shape_subsystems`.
- Python remnants that should be graph-native: `conjecture.py`, `discourse_state.py`, `imagination.py`.

## 5. Extended thinking: gap analysis

The intended faculty is to relax admissibility and widen aperture so the search reaches deeper into solution space for candidates, then settle back. Decomposed into its parts:

| Part | Exists? | Evidence |
|---|---|---|
| Trigger (impasse, surprise, low confidence) | Yes | `dual_process_core` triggers; `impasse_escalation`; `cc_residual_deepen` |
| Request object | Yes, but orphaned | `synthesis_requested`, `needs_decomposition`, `needs_tool` have no consumer |
| Shared budget / anytime object | No | Budgets are per component (`arousal_horizon`, ShapeDecode internal, GenInfer B) |
| Graded relax-admissibility operator | No | Tolerances are literals; `af_relax_chosen` is binary; `settle_tol` is static |
| Widen-aperture operator | Partial | `grain`, QualiaAperture k, manifold mask; each is private and stipulated |
| Re-admit pruned candidates | No | Motor collapse and the bigville core never re-admit |
| Generative proposal step | Domain-only | `ps_propose`/`SynthEnumerate` (code); GenInfer (matrices); no projector in the manifold |
| Tree/beam search over graph states | No | Only the ShapeDecode internal beam |
| Imagination on impasse | No | `default_mode_core` fires on idleness; `imagination.py` is Python |
| Verify | Yes | Exact `build_candidate`, MDL witness, judge |
| Settle back and cache | Domain-only | `ps_accept`; minting in the codebook; the manifold and default mode do not cache |

Every part except the generic middle exists somewhere: a shared budget, a graded relax/widen operator, re-admission, and generic proposal. Extended thinking is missing as a *faculty*, even though its pieces are scattered across domains.

## 6. Missing components, prioritized

Each item is ordered by how much of the shape it unlocks. None should require Python to decide.

1. **Extended-thinking executor (graph-native).** Highest leverage, because the triggers already exist.
   - One consumer rule set for `synthesis_requested`, `needs_decomposition` and `needs_tool`.
   - A shared `ThinkingBudget` node: anytime, funded from evidence such as arousal and value of information.
   - A graded `RelaxAdmissibility(ε)` / `WidenAperture(k)` operator that moves tolerances one step at a time and re-admits pruned candidates.
   - Verify with the existing exact checkers, then settle back: restore tolerances and cache the winner as a codebook mint or a shape.
2. **Soft admissibility in Γ.** Add a softmax / soft-excluder Term in Rust over the existing exp(w) weights. Promote the scattered tolerance literals to graph nodes. Add a real-valued `ParetoDominates`. Item 1 needs this to have something to relax.
3. **Unified aperture.**
   - Recast the domain apertures (reading, dwell, finite-difference k, QualiaAperture, ShapeDecode scope, manifold mask) as Observer-frame instances.
   - Have aperture chosen by evidence or value of information, not stipulated. The prediction-world judge already shows salience-selected aperture working.
   - Replace binary `af_relax_chosen` with a graded choice.
   - Read `obs_established` so that "mastered" and "compressed" are distinguishable.
4. **Qualia as a cache.**
   - Mint Shapes in the graph rather than in `number_runner.py`.
   - Join the three stores into one signature space: `QualiaDimension` axes, Shape sig_k and valence. Lexical qualia can stay parked.
   - Add a similarity-indexed recall Term so the codebook and analogy can *look up* rather than generate-and-test.
   - Pre-register a cross-domain recall test, since none exists today.
5. **Generative manifold.**
   - A projector from moves to trajectories.
   - `refinement_count` driven by item 1 (deepen and widen).
   - A manifold cache that writes into qualia.
   - Collapse the three implementations into the Rust generic one.
   - Make the ThoughtManifold native; it is Python and "planning only" today.
6. **Inference ladder.**
   - Connect DimInfer → GenInfer (linear → quadratic → coupled) → TimeInfer/order-N as escalation rungs under item 1, so failure at one rung requests the next.
   - Make order-N finite differences native.
   - Relax TimeInfer's regularity requirement.
7. **Impasse-triggered imagination and consolidation.** Fire default mode on impasse as well as idleness, and cache its results back. That turns default mode into a consolidation regime.
8. **Absent faculties** (each is a separate build): executive inhibition and task switching; causal / do-calculus; hierarchical planning with tests; graph-native recursive ToM; imitation; language production; capacity and interference forgetting; numerosity; imagery and mental rotation; emotion regulation.

## 7. Caveats

- The maturity labels come from code and seed reading plus the CORE_SEEDS list (`substrate/boot_core.py:20`). No new runtime measurements were taken for this report.
- "Unconsumed" means no rule or Term reading that key was found by search. A consumer outside the searched trees (seeds, `runners/dsl/src`, `domains`) cannot be ruled out.
- The prediction-world results (v1–v10) are the only held-out evidence of the judge and aperture machinery. They show trend-level improvement, with several pre-registered hypotheses failing. That world should not be read as evidence about the other components.
