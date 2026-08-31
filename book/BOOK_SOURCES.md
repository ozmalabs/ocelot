# BOOK_SOURCES — where each chapter's evidence lives

**Status: the lookup table.** For *what* a chapter claims, read
`BOOK_DOSSIERS.md`; this document is *where the material is*. Paths are
relative to the ocelot repo root unless marked otherwise.

## The four repositories

| repo | path | role |
|---|---|---|
| **ocelot** | `~/ozmadev/ocelot` | the substrate. All capability evidence, the Rust engine, the seeds, the ~1,700-document research corpus, the test bench. |
| **internal** | `~/ozmadev/internal` | **private.** The theory drafts, the trilogy, the journey artefacts, the model/compression work. The introduction is written almost entirely from here. |
| **ozma** | `~/ozma` | the KVMA router — link 2 of the introduction's chain. Public git history from 2026-04-01. |
| **bigville** | `~/ozmadev/bigville` | separate live repo (`ozmalabs/bigville`). The town's runtime and data. Ocelot holds only the historical design notes; **cite bigville's own data as external.** |

## Standing entry points

- `CLAUDE.md` (ocelot root) — the project's own running record. Purpose
  statement, the architecture rule, and the dated arc summaries (Omniglot,
  base-as-dimension, shape-is-acquisition, the retractions). Several chapters
  quote it directly.
- `docs/features/*.md` — ten current-state summaries, one per capability
  thread. **Start here for any capability chapter**, then go to the research
  folder behind it.
- `docs/research/INDEX.md` — the 16-folder research archive index.
- `docs/CODE_MAP.md` — what lives where in code.
- `VISION_PROTOCOL.md` (repo root, deliberately not moved) — binding rules and
  the burned-seed ledger every vision document cites.

---

## Per-chapter source map

### Introduction — how I got here

| link | source |
|---|---|
| the KVMA router | `~/ozma` — `README.md`, `git log --reverse` (first commit 2026-04-01, KVMA fabric; V1.1–V1.3 arc through 2026-04-14) |
| the journey retold (facts only, **not** the tone) | `~/ozmadev/internal/research/docs/article_popular.md` |
| the LLM-efficiency phase | `~/ozmadev/internal/research/` — `compressor.py`, `brevity.py`, `bench_tiered.py`, `token_counter.py`, `docs/why-compress.md`, `docs/compression.md`, `docs/hints-vs-prompts.md`; `~/ozmadev/internal/models/ozma-coder-*` |
| the semiotic graph layer + protocol | `~/ozmadev/internal/research/docs/protocol.md`, `protocol-review-v*.md`, `typed_graph_substrate_foundation.md` |
| Γ as the key | `~/ozmadev/internal/research/docs/foundation.md`, `formal_foundations.md`, `gamma_as_variable_draft.md`, `abstract_s0_gamma_draft.md` |
| the physics turn (**dated 2026-04-25**) | `~/ozmadev/internal/research/docs/physics_prior_work.md` — carries the author's own quote |
| the QM bridge **with its falsifier** | `~/ozmadev/internal/research/docs/paper1.md` — Axiom 0/4, the QBism correspondence table, and the explicit falsification clause |
| the trilogy | `~/ozmadev/internal/research/docs/graphs_paper_1_core.md`, `graphs_paper_2_implications.md`, `graphs_paper_3_trajectory.md`, `trilogy_plain_language.md` |
| the substrate's own start | ocelot `git log --reverse` — initial import 2026-08-10 |

### Prologue — three toys

| toy | source |
|---|---|
| Life | `domains/conway.py` (its docstring states the Γ-as-oracle design), `domains_rs/conway.py`, `tests/test_conway.py`, `tests/test_conway_parity.py` |
| chess | `domains/chess.py` (docstring: Γ-admissibility as pseudo-legal move enumeration; python-chess as FEN oracle only), `domains/shared_chess.py`, `tests/test_chess.py` |
| Doom | `docs/research/doom/` (12 docs — `TEXTURE_RECOGNITION_*`, `ROBUST_GEOMETRY_*` for the AUC 0.508 null, `DOOR_OPERATE_*`, `DOOM_EMOTION_NARRATION_*`, `INTERACTIVE_DOOM_RESULTS.md`); `domains/doom_*.py`; `seeds/doom_*.json` |

**Note for the chapter:** there is no PREREG/RESULTS pair for Life or chess —
they predate the discipline. That absence is the prologue's argument.

### Front matter — how to read the numbers

Compressed from ch. 16's sources (below). The drift anecdote is
`docs/research/vision/THE_EYE.md` §8 retraction 4 and §8's "sixteen inert
instruments" paragraph.

### Ch. 1 — The Eye (+ physics coda)

| piece | source |
|---|---|
| **the synthesis (effectively a draft)** | `docs/research/vision/THE_EYE.md` — 302 lines, all six claims, the retraction ledger |
| binding rules + burned-seed ledger | `VISION_PROTOCOL.md` (repo root) |
| current-state summary | `docs/features/vision.md` |
| full arc | `docs/research/vision/` (376 docs) + `INDEX.md`; `VISION_DEVELOPMENT_ARC.md` for the developmental spine and its retraction |
| retina/oculomotor specifics | `VISION_EYE_*`, `VISION_RETINAL_ONSET_*`, `VISION_TROXLER_*`, `VISION_BLINK_*`, `VISION_FOVEA_SALIENCE_BRIDGE_*`, `VISION_TWO_EYES*`, `VISION_STEREO_*` |
| seeds | `seeds/vision_floor.json`, `stage0_prediction.json`, `stage1_control.json`, `stage2_boundary.json`, `sensory_convolution.json` |
| adapters | `domains/eye_world.py`, `domains/vision_world.py`, `domains/doom_pattern_eye.py` |
| gates | `tests/test_vision_*_migrated.py` |
| **physics coda** | `docs/research/vision/physics_perception/` (20 docs) — `PHYSICS_FALL_*`, `ROBUST_ORDER_N_WITNESS_*`, `GALILEO_EQUIVALENCE_*`, `DISSIPATION_IS_INFERENCE_*`; plus `docs/research/engine_substrate/GENERIC_ORDER_N_{PREREG,RESULTS}.md` |

### Ch. 2 — The frame invariant

`CLAUDE.md` § "BASE-AS-DIMENSION + the frame/continuum invariant";
`runners/dsl/DYADIC_DEPTH_DESIGN.md` (the design *refusal*);
`runners/dsl/src/shape_decode.rs` (`coord_ints`, `dim_infer_tests`);
`seeds/shape_decode_loop.json`; `tests/test_dimension_inference_migrated.py`.

### Ch. 3 — Shape and Rule

`docs/research/engine_substrate/` — `RULES_AS_SHAPE_DESIGN_SPIKE.md` (the
diagnosis + §15-16 the self-correction and external convergence),
`RULE_SIGNATURE_SLICE_RESULTS.md` (the N=40 oracle),
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md` (the 318 parallelograms, the mirroring
NO-GO), `SHAPE_AUDIT.md`, `META_SHAPE_FIRST_CLASS_RESULTS.md` (44/55 ties),
`BAICS_WORKSHOP_HARVEST.md`. Rust: `runners/dsl/src/term.rs`
(`AntiUnifyWitness`, `Substitute`, `Unify`, `StructSim`, `Covers`).

### Ch. 4 — Dynamic quantisation

`docs/features/dynamic-quantization.md`; `runners/dsl/src/shape_decode.rs`;
`seeds/shape_decode_loop.json`, `seeds/composer_dispatch.json`,
`seeds/escalation_rungs.json`, `seeds/question_driving.json`;
`CLAUDE.md` § "Composer + driver migrated".

### Ch. 5 — One-shot characters

`CLAUDE.md` § "The Omniglot arc" and § "RUN 15 CORRECTION" / "RUN 16
RECONCILIATION" (the carefully caveated numbers — quote from here, not from
memory); `scripts/jabberwock_omniglot_dynamic_quantization.py`; `results/`
run logs; `runners/dsl/src/strokes.rs`; `seeds/writer_dimensions.json`;
`tests/test_ink_decode_migrated.py`; handwriting docs in
`docs/research/vision/` and `docs/research/audio_speech/`.

### Ch. 6 — Speech and word meaning

`docs/features/audio-speech.md`; `docs/research/audio_speech/` (146 docs);
`docs/research/agent_loop/` (71 docs — the ~54 numbered iteration logs are the
literal working record of the self-directed loop).

### Ch. 7 — Space as a belief

`docs/features/ls20-spatial.md`; `docs/research/ls20/` (37 docs);
`runners/dsl/src/space_quantize.rs`; `seeds/quanta_navigation.json`;
`worlds/arc.py`; `tests/test_quanta_navigation_migrated.py`.

### Ch. 8 — Constructions propose, execution decides

`docs/features/program-synthesis.md`; `docs/research/program_synthesis/` (179
docs — note the internal "ARC 0–6" phase numbering is *not* ARC-AGI);
`tests/test_arc_executor_migrated.py`, `tests/test_arc_goals_migrated.py`.

### Ch. 9 — One sensorimotor core, six bodies

`docs/features/humanoid.md`, `docs/features/flight-control.md`;
`docs/research/humanoid/` (55), `docs/research/flight_control/` (24);
`docs/research/flight_control/regime_pareto_frontier_{prereg,results}.md` (the
Pareto reframe and the "match SHAPES, not numbers" line);
`docs/research/humanoid/HUMANOID_DECOMPOSITION_CONTINUATION.md`;
`seeds/embodied_sensorimotor_core.json`, `seeds/embodied_motor_program.json`,
`seeds/control_regime_escalation.json`, `seeds/f16_flight_path_control.json`;
`tests/test_control_regime_escalation_migrated.py`.

### Ch. 10 — Emotion, and what it is for

`docs/features/psychology-affect.md`; `docs/research/psychology_affect/` (114).
Specifically: `EMOTION_FRAMEWORK_LITERATURE.md` (the posture),
`MOOD_MOMENTUM_SCOPING.md` + `MOOD_R1{,B,C}_*`, the hate/contempt/envy/
admiration coupling family, `SELF_CONSCIOUS_EMOTIONS_*`,
`PERSISTENT_/RELATIVE_/DOMAIN_SELF_WORTH_*`, `SELF_EFFICACY_*`,
`ATTRIBUTION_LOCUS_AS_RESIDUAL_*`, `AROUSAL_CHANNEL_RETIREMENT_*` (the kept
retirement), `HARLOW_D1{,B}_*`, `MARSHMALLOW_DELAY_*`, `AROUSAL_WOT_*`.
Seeds: `seeds/drives.json`, `seeds/modulators.json`,
`seeds/affective_state_core.json`, `seeds/harlow_attachment.json`.
Data: `results/harlow_d1.json`, `results/marshmallow_delay/results.json`.

### Ch. 11 — When grounding fails

`docs/research/psychology_affect/PSYCHOSIS_DEMO_{PREREG,RESULTS}.md`,
`GROUNDING_PSYCHOSIS_LITERATURE.md`; `SEIZURE_ENGINE_*`, `SEIZURE_MODEL_V2_*`,
`SEIZURE_SCIENCE.md`, `SEIZURE_FIELD_COMPARISON.md`, `SEIZURE_DATA_DIVE.md`;
`GROUNDING_NARCISSISM_SCIENCE.md`, `savant_grounding_3a_3b.md`.
Code: `seeds/psychosis_grounding.json`, `scripts/psychosis_grounding_demo.py`,
`tests/test_psychosis_grounding_migrated.py`, `results/psychosis_demo/`.

### Ch. 12 — Coercive control

`docs/research/bigville/` — **start at**
`ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md` (the synthesis; every number cited to
its own rung). The five locked scoping documents: `..._SCOPING.md` (R1–R5),
`..._NETWORK.md` (N1–N4), `..._UNINTENTIONAL_SCOPING.md` (U0–U2),
`..._BARRIERS_AND_RETURN_SCOPING.md` (R6–R7), `..._VISIBILITY_SCOPING.md` (V1).
Then the fifteen rung docs `ABUSIVE_{R1..R7,N1..N4,U0..U2,V1}_*`.
The ethics protocol is stated identically in every prereg — quote it from the
scoping doc, Part C/D.

### Ch. 13 — The town

`docs/features/bigville.md` (note: ocelot no longer owns a runtime);
`docs/research/bigville/` (202 docs) — `BIGVILLE_DESIGN_REFERENCE.md`,
`BIGVILLE_ADMISSIBILITY_GRAMMAR.md` (the `"productions": []` finding),
`GLASS_BOX_SOCIETY_SCOPING.md` + `GLASS_BOX_R1_*`,
`PRIOR_ART_SOCIAL_EXPERIMENTS.md`, `SOCIETY_EXPERIMENTS_SURVEY.md`,
the econ/law/governance/gossip families.
**Desire paths:** `docs/research/engine_substrate/AFFECT_WEIGHTED_ROUTE_VALUATION_DESIGN.md`,
`DESIRE_PATH_PRECONDITION_RESULTS.md`, `TERRAIN_WEAR_STIGMERGY_RESULTS.md`.
Runtime and data: `~/ozmadev/bigville` (external).

### Ch. 14 — The law, and one machine that obeys it

`papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex`,
`papers/formal/A1_constructive_graphic_equalisation_implementation_referenced.tex`;
`~/ozmadev/internal/research/docs/paper1.md` and the drafts around it;
`docs/research/theory_convergence/GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md`;
engine: `runners/dsl/src/{substrate,rewrite,grammar,checker}.rs`.

### Ch. 15 — A number where a shape belonged

`docs/research/engine_substrate/SHAPE_AUDIT.md` (40 confirmed sites, 2
self-caught errors) + `SHAPE_AUDIT_SWEEP2_*`, `SHAPE_AUDIT_PATTERN_C_FIXES_*`;
`docs/research/flight_control/regime_pareto_frontier_prereg.md` (the
rate-needs-a-rate regress, the 60 count-divided learners);
`docs/research/humanoid/HUMANOID_DECOMPOSITION_CONTINUATION.md`;
`docs/research/bigville/BIGVILLE_ADMISSIBILITY_GRAMMAR.md`;
`docs/research/engine_substrate/CONSTANT_RANKING_SELECTOR_CENSUS.md`,
`ARGMIN_TIE_CENSUS_RESULTS.md`; `CLAUDE.md` § "SHAPES, NOT NUMBERS".

### Ch. 16 — Preregistration as an engineering method

The corpus itself (`docs/research/`, ~1,700 paired documents) is the primary
source. The standing rules and their origins: `CLAUDE.md` § "RUN 15
CORRECTION" (power the gate), the **retracted optional-dep note** section (a
baseline is a list, never a count), `results/failure_baseline.json` +
`tests/test_failure_baseline_migrated.py`,
`docs/research/vision/VISION_BASELINE_LIST_RESULTS.md`,
`VISION_GATE_SCOPE_B_RESULTS.md`. Positive-control discipline and the sixteen
inert instruments: `docs/research/vision/THE_EYE.md` §8. Convergence:
`docs/research/theory_convergence/THEORY_CONVERGENCE_AUDIT.md`,
`RAVANA_CONVERGENCE_AUDIT.md`, `TAU_HIERARCHY_AXIS_MAP_{PREREG,RESULTS}.md`.

### Ch. 17 — Seldon manifolds

`papers/formal/02_seldon_manifolds_theory_referenced.tex`;
`runners/dsl/src/future_manifold.rs` (474 lines; **every call site
single-candidate**); `scripts/seldon_manifold_viz_demo.py` (which disclaims
itself honestly — see ch. 18).

### Ch. 18 — Narrative momentum and narrativium

`papers/formal/03_law_of_narrative_momentum_theory_referenced.tex`,
`papers/formal/04_narrativium_theory_referenced.tex`;
`docs/research/theory_convergence/GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` §5
(the only "narrativium" occurrence in the tree computes a **forbidden path
integral** — `scripts/seldon_manifold_viz_demo.py:168-185`).

### Ch. 19 — The open problem

`GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` §4 — the two never-composed
primitives: `runners/dsl/src/future_manifold.rs` and
`Substrate::admissible_moves` (`runners/dsl/src/substrate.rs`).

### Epilogue — there is no natural ending

`~/ozmadev/internal/research/docs/infinity_paper.md` (+ `.tex`, `.pdf`) — the
reflective tower, potential vs actual infinity. The cut's live state:
`runners/dsl/src/effect_audit.rs`,
`docs/research/engine_substrate/STAGE_A_RESULTS.md` (built, measured, **left
off**), `DESIRE_PATH_PRECONDITION_RESULTS.md`.
Register precedent: ch. 12's locked protocol.

---

## Working rules for using these sources

1. **Quote numbers from the source document, never from a summary** — and
   never from `CLAUDE.md`'s prose without following its own pointer. The tree's
   own worst defect was a claim quoted without its condition.
2. **Check a path before citing it.** Documents moved in the 2026-08-11
   reorganisation; a few live at the repo root by deliberate exception
   (`VISION_PROTOCOL.md`).
3. **Prefer `docs/features/` for orientation, the research folder for
   evidence.** The feature docs are summaries and say so.
4. **Bigville and internal are separate repos.** Cite them as external, and
   never import their content back into ocelot.
5. **A result with no committed runner is not a result** (`THE_EYE.md`
   retraction 3). If a number cannot be reproduced from a committed script, it
   does not go in the book.
