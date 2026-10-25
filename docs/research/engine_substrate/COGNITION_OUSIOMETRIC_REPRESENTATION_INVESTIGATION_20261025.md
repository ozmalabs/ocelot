# Phase 28 — Ousiometric representation value investigation

**Date:** 2026-10-25. **Status:** P28.01–P28.16 completed as a bounded investigation and reporting cycle; the registered primary benefit criterion failed and the existing default representation is retained. **Task order:** P28.01 → P28.16. **Canonical schedule:** [cognition linear plan](COGNITION_BUILD_PLAN_20261010.md), Phase 28. This remains the detailed specification and evidence ledger; it does not claim that PDS improves the substrate.

## 1. Question and entry scope

Does a power–danger–structure (PDS) frame make a bounded substrate agent learn, recall, predict, transfer or choose experiments better than an information-matched valence–arousal–dominance (VAD) frame or an unconstrained experience-built frame? If it helps, is the cause a more useful basis under finite aperture, metric or search constraints, additional acquired information, or an artifact of how concepts and experiences were sampled?

Entry is the [2026-10-25 completion audit](COGNITION_BUILD_PLAN_COMPLETION_AUDIT_20261025.md): P16's attested native execution and P17's finite acquired-axis behavioral consumer are available; P23 diagnostics and P24–P27 reported interfaces may be used only in their demonstrated scope. P24 did not show transfer gain, P26 did not show selection gain, and P27 was a flat ceiling result. P22 remains open and unfrozen; this tract requires neither filling its lineage manifest nor treating its development as efficacy. Existing candidate approvals remain exactly scoped and cannot be reused here.

P28.01–P28.04 are specification, provenance and offline geometry tasks. They can establish whether the proposed experiment is mathematically valid before a runtime change. P28.05–P28.08 build bounded native comparators and acquisition/world interfaces. P28.09–P28.12 build development panels and controls only; P28.13 freezes their protocol; P28.14 alone opens/runs the newly sealed panels; P28.15–P28.16 decide and close evidence. No held-out panel is opened until its working adapters and frozen protocol exist.

## 2. What the source establishes

The [primary paper](https://doi.org/10.1126/sciadv.adr4039) (Dodds et al., *Science Advances*, 6 May 2026; [open manuscript](https://digital.library.adelaide.edu.au/server/api/core/bitstreams/47ebc745-5678-4864-b538-fa1a8c418720/content)) transforms human lexical ratings and examines frequency-weighted English corpora. Its 90.9% versus 72.4% result concerns two-dimensional projections of VAD ratings, not predictive accuracy over all semantics. Full three-coordinate VAD/PDS descriptions are related by a linear change of basis; the GPADS circumplex is not five independent latent dimensions. Orthogonality does not establish causal or statistical independence.

The [GPADS v2 data record](https://zenodo.org/records/18509376) provides word scores and the GAS/PDS plane relationship. Structure uses the orientation **high = unstructured** in that file. Freeze the exact version, license, file bytes, units, sign and transformation precision before using it. The main manuscript's rounded matrix is not a numerical exactness oracle. The [authors' overview](https://storylab.w3.uvm.edu/ousiometrics/) describes the token-frequency safety finding. English lexical connotations are not measured world danger; no evolutionary-cause, developmental-origin or universal-three-axis inference follows from this experiment.

These sources supply hypotheses and an external comparison instrument. They do not supply an acquired qualia database for the agent.

## 3. Hard distinctions the study must preserve

1. **Basis versus information.** For a full-rank transform `y = T x`, all coordinates and a metric/predictor transported through `T^-1` retain the same information. Unquantized, untruncated, unregularized full-capacity linear references must give the same predictions to numerical tolerance. A claimed PDS gain here is an implementation defect. With axis-aligned quantization, finite aperture, L1 distance, restricted rules, sparse feature selection or regularization, a rotation can change performance. Report that mechanism explicitly.
2. **Current substrate metric matters.** The signature contract uses dimension-wise tolerance and L1-like numerical distance. A coordinate rotation is not invariant under that fixed metric. Include a transported-metric control `d_PDS(y1,y2)=d_VAD(T^-1 y1,T^-1 y2)` and a fixed-metric arm; otherwise a changed neighbor ranking could be mislabeled new knowledge. An invertible coordinate transformation cannot turn a lossy projection into a new acquired dimension.
3. **Published axes versus operational axes.** Power is a candidate interpretation of ability to cause/resist effects; danger of adverse outcomes/lost future options; structure of organization/constraints. These are hypotheses, not three hidden world-label fields to ingest. Predictability, compressibility and social order must not be conflated. Behavioral inputs are common measured event/action/result features; world latent factors stay with the generator/scorer.
4. **VAD/PDS labels require a compatible calibration.** Applying a published lexical matrix to arbitrary physical coordinates does not make them VAD or PDS. Freeze a common observed-feature encoder and its development-only calibration/anchor evidence before comparing fixed frames. Apply the same source evidence, compute and label access to both fixed arms. Without a justified semantic calibration, label the condition “published rotation of shared coordinates,” not a PDS/VAD psychological validation. Lexical information granted to calibration arms is counted and never described as experience-only acquisition.
5. **Learned versus seeded.** All primary experience-built arms receive identical episodes, raw observed feature access, support/verification policies, node/byte/coordinate precision budget and work limits. One learned frame cannot receive held-out GPADS labels while the others do not. A richer unrestricted-dimensional arm is a separate capacity-scaling reference unless its full representation/decoder cost is matched.
6. **Frequency versus value.** Analyze uniform concept types, measured occurrence tokens and their shuffled-frequency control separately. Repeated exposure does not become independent supporting events merely through count. A frequently safe corpus cannot justify ignoring rare harmful outcomes. Keep controlled rare-event strata and full prediction/escape errors beside mean performance.
7. **Language and world consequences.** Lexical “danger” is an asserted/inferred connotation that may propose a question. It must never replace observed consequence receipts, the future-manifold residual tube, confidence/approval guards or a host veto. Negation, quotation, reassurance, threat and irony controls test the distinction between a dangerous word and a dangerous projected action.

## 4. Experimental conditions and identifying controls

| Condition | Information and representation | Interpretation allowed |
|---|---|---|
| `VAD-full` | All three fixed calibrated VAD coordinates; no quantization; transported reference predictor/metric | Full-information reference |
| `PDS-full` | Same records under full-rank paper-derived transform with inverse; transported predictor/metric | Must match `VAD-full`; zero new information |
| `VAD-bounded` | Same calibrated records with frozen aperture/metric/search restrictions | Fixed-frame bounded baseline |
| `PDS-bounded` | Same calibrated records under PDS, identical total representation/work capacity; fixed and transported metric subconditions | Tests basis utility under those restrictions |
| `learned-3D` | Frame chosen from the common observed evidence using native rules and exactly the same three-dimensional/precision/work envelope | Tests experience-built representation selection |
| `random-basis` | One preregistered seeded rotation per replicate under the same bounds | Detects generic rotation or axis-alignment effects |
| `frozen-space` | Same evidence with representation acquisition disabled, ordinary learner still functional | Tests acquisition, not a missing learner |
| `learned-flex` | Native variable-dimensional acquisition with full cost reported | Capacity curve/reference; primary comparisons only where budgets really match |

Full-reference mathematics is offline audit code; runtime adaptation/search is graph/Rust. Fixed transforms can be installed as declared experimental frame data, never as action or truth labels. GPADS contains redundant projections: do not give it five coordinates against a three-coordinate VAD arm and call that equal capacity. Every arm uses the same raw episode information and ordinary target receipt path; the only permitted intervention is representation/acquisition availability or the explicitly stated aperture/metric condition.

## 5. Panels, measures and decision rules to freeze

**Synthetic factorial worlds.** Use at least two independently implemented families: tool/intervention processes and witnessed social request/repair/cooperation. Independently vary intervention capacity, harmful consequence, organizational constraints and pleasantness/success where the world supports the distinctions. Include powerful-safe, powerful-dangerous, weak-dangerous and weak-safe cases, predictable harmful processes, safe unfamiliar/unstructured processes, and context reversals. Randomly relabel symbols and rotate nuisance coordinate presentations. The world/scorer may know factors; agent inputs contain raw receipts and observable features only. Do not construct all goals or rewards along PDS axes and then infer natural superiority from that axis alignment.

**Learning and transfer.** Predeclare 200 paired task streams per family, with the same action/evidence/work horizon and domain-size distribution. Measure normalized area under observed prediction/action success versus total paid interactions; exact recall/verification/model-query work; unseen-context/binding transfer; total description length including frame, decoder, exceptions and failed proposals; graph nodes/bytes and measured time. Agent action must be the one selected by the native graph and verified by the shared simulator receipt. Abstention, failed trials and pending authorization remain outcomes. These panels do not require invention of new externally acting operator candidates; any such path follows the already existing approval scope.

**Coordinate controls.** Use at least 100 records spanning full-rank, near-singular/invalid and coordinate-scaled cases. Full-information transported predictions/distances must agree within a frozen tolerance justified by transform precision. Any mismatch stops behavioral interpretation until corrected. Compare bounded metric/aperture conditions under fixed aggregate bits, candidate cap and work. Report a benefit conditional on an axis-aligned restriction as such.

**Distribution panels.** Keep physical mechanisms fixed while varying occurrence frequencies in uniform-type, observed-token and frequency-shuffled presentations. Freeze three frequency regimes from independent generator parameters and include 100 rare-adverse controls per family. Report error by occurrence and by distinct mechanism; a token-weighted mean cannot suppress rare-event failures. Statistical decorrelation is not tested causal independence; interventions, rather than coordinate covariance alone, establish separability of the world factors.

**External lexical comparison.** GPADS is locked external evidence. Before opening scores, freeze concept-cluster split membership using lexical identifiers, the trained checkpoint and its token→concept bridge, semantic-axis alignment method and primary metric. An anchor subset may orient signs/permutation/rotation; its labels are counted and cannot reappear in the sealed concept clusters, training or model selection. Evaluate learned interconcept geometry on the untouched clusters, with lexical surface-only and shuffled-label baselines. Missing concepts remain missing; report coverage, word-sense ambiguity and English-corpus limits. A fixed VAD→GPADS transform matching its own derived labels is a conformance check, not evidence that the agent independently learned human semantics.

**Primary value criterion.** P28.01 must choose the exact bounded condition and one primary comparison before development outcome analysis: proposed criterion is at least +0.10 normalized behavioral learning AUC for `PDS-bounded` versus `VAD-bounded` at equal capacity/work, or a separately registered learned-frame criterion versus both fixed frames. Do not select whichever contrast later wins. Conformance and safety are zero-tolerance gates. Lexical agreement is a separate secondary criterion with coverage and an anchored, cluster-held-out uncertainty interval; it cannot rescue a failed behavior primary. Treat full-reference equality as the expected result, not a negative efficacy finding.

Use paired world-level bootstrap intervals (10,000 resamples) or exact paired tests appropriate to the frozen endpoint; Holm-correct all declared primary family/condition comparisons at α=.01. Cluster lexical resampling by the frozen concept family, not individual near-synonymous words. Record effect estimates, 99% lower bounds and 95% descriptive intervals; a positive primary also requires its prespecified minimum margin and corrected p≤.01. No optional stopping or post-draw threshold/coordinate/metric selection. Nulls, costs, calibration/label exposure and unsupported cases are fully reported.

## 6. Ordered tasks

### P28.01 — Freeze the claim map and information-matched study design

- **ID:** P28.01
- **Tier:** T1
- **Goal:** Freeze the claim map and information-matched study design.
- **Read first:** `docs/research/engine_substrate/COGNITION_BUILD_PLAN_COMPLETION_AUDIT_20261025.md`; `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md`; this document §§2–5.
- **Touch:** this document; new `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`.
- **Pattern to copy:** existing P11 frame/inverse/cost contract and P28 full-information invariance rule.
- **Steps:** 1. Enumerate hypotheses for basis utility, new information, acquired significance and sampling geometry. 2. Freeze which primary contrast/metric is tested and equal information/capacity/compute constraints, including semantic calibration. 3. Declare exact unknown/error behavior, compatibility and runtime scope; register descriptive capacity scaling separately.
- **Guard:** documentation only.
- **Acceptance:** every arm has a common evidence path, explicit capacity and intervention; orthogonality is not called independence; no behavioral benefit is assumed.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_representation_search.py tests/test_common_target_evidence.py -q -p no:cacheprovider`.
- **Non-goals:** adding three fixed PDS dimensions as a presumed improvement or assuming P22/P24/P26/P27 efficacy.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.02 — Create a versioned external-data and transformation manifest

- **ID:** P28.02
- **Tier:** T2
- **Goal:** Create a versioned external-data and transformation manifest.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/process_mastery/runtime_attestation.py`; `evaluation/process_mastery/scorecard.py`; this document §2.
- **Touch:** new `evaluation/ousiometrics/source_manifest.py`; new `tests/test_ousiometrics_sources.py`; new `docs/research/engine_substrate/OUSIOMETRIC_DATA_MANIFEST.md`.
- **Pattern to copy:** existing frozen source/loaded-extension attestations and immutable data provenance.
- **Steps:** 1. Obtain exact primary GPADS v2 and the required VAD source under their documented licenses; pin URLs, version, checksum, columns, units and sign. 2. Distinguish paper full-precision/derived transformation from rounded display coefficients and freeze numerical tolerance/conditioning. 3. Create concept-cluster splits from identifiers before loading held-out score columns; identify unavailable sources honestly.
- **Guard:** external data tools only; no seed or runtime ingestion.
- **Acceptance:** `test_source_bytes_and_license_recorded`, `test_structure_orientation_explicit`, `test_transform_precision_not_rounded_oracle`, `test_labels_not_read_when_building_split`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometrics_sources.py -q -p no:cacheprovider`.
- **Non-goals:** training from the GPADS external holdout or automatically installing copyrighted/unsupported source material.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.03 — Establish full-information basis and metric invariance

- **ID:** P28.03
- **Tier:** T2
- **Goal:** Establish full-information basis and metric invariance.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `docs/research/engine_substrate/OUSIOMETRIC_DATA_MANIFEST.md`; `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`; `tests/test_representation_search.py`.
- **Touch:** new `evaluation/ousiometrics/geometry_reference.py`; new `tests/test_ousiometrics_geometry.py`.
- **Pattern to copy:** offline exact mathematical reference and typed map/inverse checks.
- **Steps:** 1. Verify full rank, inverse round trip, condition numbers and source normalization. 2. Compare predictions of transported unquantized linear references and original/transported L1 and quadratic metrics. 3. Show separately how fixed axis-aligned distance or quantization can alter rankings; reject unsupported dimension drops and five-versus-three capacity comparisons.
- **Guard:** offline diagnostic only; never agent candidate selection.
- **Acceptance:** `test_full_information_predictions_equivalent`, `test_transported_metric_same_neighbors`, `test_fixed_l1_rotation_effect_is_explicit`, `test_gpads_rank_not_five_independent_axes`, `test_bad_inverse_refused`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometrics_geometry.py -q -p no:cacheprovider`.
- **Non-goals:** calling an invertible rotation new information or an L1 metric artifact independent evidence of richer meaning.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.04 — Decide whether runtime representation comparison is ready

- **ID:** P28.04
- **Tier:** T1
- **Goal:** Decide whether runtime representation comparison is ready.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/ousiometrics/geometry_reference.py`; `docs/research/engine_substrate/OUSIOMETRIC_DATA_MANIFEST.md`; `docs/research/engine_substrate/COGNITION_BUILD_PLAN_COMPLETION_AUDIT_20261025.md`.
- **Touch:** this document; new `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_READINESS.md`.
- **Pattern to copy:** earlier evidence-scoped entry ledgers and explicit unsupported comparisons.
- **Steps:** 1. Require actual transform/data/invariance evidence and choose the declared compatible common coordinate encoder. 2. Enumerate native operations already expressive by existing Terms and any strictly necessary split engine subtasks before behavior work. 3. Record GO only for supported finite-world comparisons; unsupported psychological calibration receives the narrower rotation-experiment label.
- **Guard:** documentation/diagnostics only.
- **Acceptance:** all runtime arms have compatible source units, invertible full reference and valid equal-capacity comparison; missing data/calibration blocks its associated claim rather than all diagnostics.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometrics_sources.py tests/test_ousiometrics_geometry.py -q -p no:cacheprovider`.
- **Non-goals:** new Rust primitives without a written semantic gap or freezing an interpretation that cannot be operationalized.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.05 — Implement shared native representation frames and finite-aperture variants

- **ID:** P28.05
- **Tier:** T2
- **Goal:** Implement shared native representation frames and finite-aperture variants.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `scripts/gen_representation_search_seed.py`; `scripts/gen_common_target_evidence_seed.py`; `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** new `scripts/gen_ousiometric_frames_seed.py` + `seeds/ousiometric_frames.json`; new `tests/test_ousiometric_frames.py`.
- **Pattern to copy:** existing versioned typed frame maps, graph projection and shared receipt assimilation.
- **Steps:** 1. Express fixed full-rank transforms/inverses, random bases, grain and metric identifiers as graph data using existing native algebra. 2. Keep full source descriptors, owner/frame/model/epoch and missingness through every view; meter projection and decoder cost. 3. Apply fixed/transported metrics and matching aggregate aperture budget by explicit policies without changing default profiles.
- **Guard:** OusiometricFramePolicy disabled; self-load-only seed and complete Γ/dependency declarations.
- **Acceptance:** `test_same_raw_evidence_every_frame`, `test_frame_inverse_retains_source`, `test_equal_total_aperture_budget`, `test_stale_projection_invalidated`, `test_dependency_boot_no_open_grammar`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_frames.py tests/test_common_target_evidence.py -q -p no:cacheprovider`.
- **Non-goals:** host-side representation selection, forced VAD labels on arbitrary physical features, or changing frozen prior frame semantics.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.06 — Acquire and select bounded native frames without lexical answer labels

- **ID:** P28.06
- **Tier:** T2
- **Goal:** Acquire and select bounded native frames without lexical answer labels.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `scripts/gen_qualia_acquisition_seed.py`; `scripts/gen_qualia_behavior_seed.py`; `scripts/gen_representation_search_seed.py`; `seeds/ousiometric_frames.json`.
- **Touch:** new `scripts/gen_ousiometric_acquisition_seed.py` + `seeds/ousiometric_acquisition.json`; new `tests/test_ousiometric_acquisition.py`.
- **Pattern to copy:** P17 recurring consequence witnesses and P11 total-description-cost frame proposals.
- **Steps:** 1. Let observed outcome residuals fund candidate grain/basis/dimension alternatives under the frozen envelope. 2. Reverify on fresh episode contexts before adopting a representation change; preserve basis-versus-new-coordinate provenance. 3. Keep lexical labels absent from experience-built training, and test candidate retirement/knockout behavior only within supported lifecycle.
- **Guard:** OusiometricAcquisitionPolicy disabled; same shared ThinkingBudget and verifier standards.
- **Acceptance:** `test_acquired_frame_has_episode_witnesses`, `test_rotation_not_new_dimension`, `test_new_dimension_requires_observed_information`, `test_heldout_lexical_labels_unavailable`, `test_candidate_proposal_cost_charged`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_acquisition.py tests/test_qualia_behavior.py tests/test_representation_search.py -q -p no:cacheprovider`.
- **Non-goals:** claiming general axis discovery from a fixture-supplied target feature or silently treating unsupported retirement as implemented.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.07 — Generate independent intervention and social worlds

- **ID:** P28.07
- **Tier:** T2
- **Goal:** Generate independent intervention and social worlds.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/process_mastery/qualia_behavior_worlds.py`; `evaluation/process_mastery/observed_worlds.py`; `evaluation/process_mastery/evidence_search_worlds.py`.
- **Touch:** new `evaluation/ousiometrics/worlds.py`; new `tests/test_ousiometric_worlds.py`.
- **Pattern to copy:** independent simulator dynamics and externally verified native action receipts.
- **Steps:** 1. Build two independently coded worlds with independently varied effect capacity, adverse outcomes and organization, plus separate pleasantness/success manipulations where defined. 2. Expose identical observed features/actions/receipts but no hidden-factor, PDS/VAD label or correct-axis fields. 3. Generate crossed combinations, nuisance rotations, unfamiliar contexts and world-owned action verification; publish factor identifiability/unsupported cases.
- **Guard:** world adapter/scorer only; no agent decision code.
- **Acceptance:** `test_factors_can_be_intervened_separately`, `test_factor_labels_not_agent_input`, `test_safe_unfamiliar_and_predictable_harm_exist`, `test_goal_not_frame_axis_function`, `test_receipt_matches_world`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_worlds.py -q -p no:cacheprovider`.
- **Non-goals:** defining all goals along PDS and calling its resulting advantage universal; equating predictable with structured by fiat.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.08 — Connect each frame to the same prediction recall and action consumers

- **ID:** P28.08
- **Tier:** T2
- **Goal:** Connect each frame to the same prediction recall and action consumers.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `seeds/ousiometric_frames.json`; `seeds/ousiometric_acquisition.json`; `evaluation/process_mastery/common_target_learner.py`; `evaluation/process_mastery/cumulative_checkpoint_panel.py`.
- **Touch:** new `evaluation/ousiometrics/native_adapter.py`; new `tests/test_ousiometric_native_adapter.py`; new `tests/test_ousiometric_causal_controls.py`.
- **Pattern to copy:** same common target learner and P16/P17 scored native causal chain.
- **Steps:** 1. Define the explicit opt-in investigation profile inside the mechanical native adapter: load the declared seed dependency closure and configure frame/acquisition availability without changing ordinary receipt assimilation, default/conversation profiles or supplying a host action. 2. Run identical recall/prediction/action consumers and extract actually graph-selected outcomes with receipt verification; own the orphan-signal/boot-status audits required by §7 and fix unconsumed decisions before freeze. 3. Perturb active frame/inverse/axis and trace whether the scored path changes or abstains; check equal primary representation/work budgets and loaded-native provenance.
- **Guard:** explicit experimental policy configuration; native execution and approval guards preserved.
- **Acceptance:** `test_native_consumer_uses_selected_frame`, `test_same_receipt_assimilation_every_arm`, `test_frame_knockout_affects_scored_path`, `test_host_never_selects_action`, `test_common_budget_and_capacity`, `test_investigation_profile_default_isolation`, `test_investigation_dependency_closure`; boot/orphan audits are recorded with no unexplained new decision-signal writer.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_native_adapter.py tests/test_ousiometric_causal_controls.py -q -p no:cacheprovider`.
- **Non-goals:** a working PDS policy compared with a missing VAD/learned learner or host arm-specific process application.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.09 — Measure behavioral and cross-context representation value

- **ID:** P28.09
- **Tier:** T2
- **Goal:** Measure behavioral and cross-context representation value.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/ousiometrics/worlds.py`; `evaluation/ousiometrics/native_adapter.py`; `evaluation/ousiometrics/geometry_reference.py`.
- **Touch:** new `evaluation/ousiometrics/behavior_panel.py`; new `tests/test_ousiometric_behavior_panel.py`.
- **Pattern to copy:** paired learning curves and independent scored checkpoint worlds.
- **Steps:** 1. Run development streams at matched evidence and work horizons; collect AUC, exact-check/query/primitive work and full representation/decoder costs. 2. Transfer to fresh contexts, bindings and changed consequence maps with ordinary target learning still enabled in every arm. 3. Include full-reference equivalence and bounded random-basis/metric/aperture controls; retain all failures and label calibration cost.
- **Guard:** development-only until P28.13 freeze.
- **Acceptance:** `test_same_learning_horizon_and_worlds`, `test_full_reference_no_false_advantage`, `test_work_includes_mapping_and_failed_proposals`, `test_transfer_requires_new_target_verification`, `test_no_success_conditioned_primary`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_behavior_panel.py tests/test_ousiometrics_geometry.py -q -p no:cacheprovider`.
- **Non-goals:** rescuing a failed primary by choosing a different aperture after held-out outcomes or ignoring calibration cost.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.10 — Separate type geometry token exposure and rare-consequence errors

- **ID:** P28.10
- **Tier:** T2
- **Goal:** Separate type geometry token exposure and rare-consequence errors.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/ousiometrics/worlds.py`; `evaluation/ousiometrics/behavior_panel.py`; `evaluation/process_mastery/scorecard.py`.
- **Touch:** new `evaluation/ousiometrics/distribution_panel.py`; new `tests/test_ousiometric_distribution_panel.py`.
- **Pattern to copy:** fixed paired world streams and distinct source-event support counting.
- **Steps:** 1. Hold mechanisms fixed while presenting uniform-type, measured-token and shuffled-frequency regimes with frozen episode IDs. 2. Measure weighted and unweighted geometry and behavioral errors, with explicit rare adverse strata and exposure-normalized estimates. 3. Distinguish representation change caused by data distribution from changed source facts and report repeated-event deduplication.
- **Guard:** experimental stream generation only; no new safety preference or objective.
- **Acceptance:** `test_frequency_shift_preserves_world_dynamics`, `test_replay_not_independent_support`, `test_rare_adverse_errors_never_hidden_in_mean`, `test_type_and_token_statistics_separate`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_distribution_panel.py -q -p no:cacheprovider`.
- **Non-goals:** equating language safety frequency with environmental safety probability or using frequency as a truth/commitment score.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.11 — Build a locked external GPADS comparison

- **ID:** P28.11
- **Tier:** T2
- **Goal:** Build a locked external GPADS comparison.
- **Read first:** `docs/research/engine_substrate/OUSIOMETRIC_DATA_MANIFEST.md`; `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/ousiometrics/source_manifest.py`; `evaluation/ousiometrics/geometry_reference.py`; `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** new `evaluation/ousiometrics/lexical_validation.py`; new `tests/test_ousiometric_lexical_validation.py`.
- **Pattern to copy:** versioned external data provenance and cluster-held-out paired analysis.
- **Steps:** 1. Freeze trained checkpoint/token-to-concept bridge before target scores are opened. 2. Permit only the preregistered anchor split to align signs/rotation; lock untouched concept clusters and report coverage/missing senses. 3. Compare learned geometry with external scores against surface-only and shuffled-label controls; label VAD-derived PDS agreement as mathematical conformance, not independent acquisition.
- **Guard:** read-only external scorer; target score payload never reaches agent graph.
- **Acceptance:** `test_external_scores_not_training_input`, `test_related_concepts_share_split`, `test_anchor_labels_not_in_test`, `test_alignment_frozen_before_test`, `test_missing_concepts_not_dropped_silently`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_lexical_validation.py -q -p no:cacheprovider`.
- **Non-goals:** a lexical lookup table installed as acquired qualia, all-data fitted alignment, or universal-language claims from English ratings.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.12 — Enforce lexical connotation versus actual manifold consequence separation

- **ID:** P28.12
- **Tier:** T2
- **Goal:** Enforce lexical connotation versus actual manifold consequence separation.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_ACTION_ARBITRATION_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`; `evaluation/ousiometrics/native_adapter.py`; `tests/test_ousiometric_causal_controls.py`.
- **Touch:** new `tests/test_ousiometric_risk_boundary.py`; `tests/test_ousiometric_causal_controls.py`; `evaluation/ousiometrics/worlds.py`.
- **Pattern to copy:** existing host veto, full time-indexed residual and source-bound action receipt checks.
- **Steps:** 1. Add contexts with frightening harmless language, reassuring harmful plans, quotation/negation and unfamiliar safe actions. 2. Verify lexical danger may propose evidence gathering but cannot certify or replace a consequence model/manifold assessment. 3. Test frame/lexical changes with identical physical dynamics preserve actual escape/retained residual accounting and approvals.
- **Guard:** no commit-boundary change; lexical data stays asserted/inferred evidence.
- **Acceptance:** `test_lexical_danger_cannot_authorize_action`, `test_reassurance_cannot_hide_projected_escape`, `test_negation_not_word_count_truth`, `test_same_world_same_residual_audit`, `test_host_veto_nontradeable`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_risk_boundary.py tests/test_response_inhibition_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** a new keyword safety filter or a scalar PDS risk score substituted for the existing future-manifold tube.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.13 — Freeze a runnable representation-value protocol

- **ID:** P28.13
- **Tier:** T1
- **Goal:** Freeze a runnable representation-value protocol.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md`; `evaluation/ousiometrics/behavior_panel.py`; `evaluation/ousiometrics/distribution_panel.py`; `evaluation/ousiometrics/lexical_validation.py`; `evaluation/process_mastery/runtime_attestation.py`.
- **Touch:** new `evaluation/ousiometrics/run_v1.py`; new `evaluation/ousiometrics/analyze_v1.py`; new `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_PREREG_V1.md`.
- **Pattern to copy:** working native adapters, loaded-extension attestation and standalone immutable freeze.
- **Steps:** 1. Implement all selected behavioral, metric, frequency, lexical and risk-control paths with development self-checks. 2. Verify P28.08 profile/dependency/isolation, orphan-signal/boot audits and actual native attestation, then freeze the single declared primary, all multiplicity families, capacity/precision/metric conditions, concept/world splits and concrete disjoint seeds after coverage checks, not after selecting the best arm. 3. Pin full source/native/profile/transform/data/checkpoint hashes and commit preregistration alone before any sealed draw; reject missing arms or incompatible calibration.
- **Guard:** evaluation only; no new automatic operator approvals.
- **Acceptance:** runner/analyzer --self-check pass; mathematical equivalence controls pass; lexical test scores locked; every behavior arm executes the same native consumer; exact allocation and statistical decision code frozen.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometric_behavior_panel.py tests/test_ousiometric_lexical_validation.py tests/test_ousiometric_risk_boundary.py -q -p no:cacheprovider`.
- **Non-goals:** freezing null adapters, silently dropping unrepresented concepts or deciding which contrast is primary after looking at heldout scores.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.14 — Run and report frozen outcomes with attribution to mechanism

- **ID:** P28.14
- **Tier:** T1
- **Goal:** Run and report frozen outcomes with attribution to mechanism.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_PREREG_V1.md`; `evaluation/ousiometrics/run_v1.py`; `evaluation/ousiometrics/analyze_v1.py`; `docs/research/engine_substrate/COGNITION_BUILD_PLAN_COMPLETION_AUDIT_20261025.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_RESULTS_V1.md`.
- **Pattern to copy:** immutable earlier negative ledgers and full resource/claim-boundary reporting.
- **Steps:** 1. Run the frozen allocation once, preserve raw bytes outside git and hash before analysis. 2. Report every primary/control, intervals, data/calibration exposure, useful work, missing concepts and costs. 3. Attribute any result to full-information equivalence, bounded metric/aperture utility, acquired new information or sampling shift; unexpected full-information inequality invalidates that panel.
- **Guard:** frozen read-only evaluation.
- **Acceptance:** all registered outcomes classified including nulls; lexical agreement cannot substitute for behavioral failure; positive bounded-basis result is not called new information or universal qualia geometry.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometrics_geometry.py tests/test_ousiometric_behavior_panel.py tests/test_ousiometric_lexical_validation.py -q -p no:cacheprovider`.
- **Non-goals:** retuning basis, tolerance or distribution on heldout data; rescoring a previous phase or treating lack of superiority as disproof of all representational value.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.15 — Decide whether a representation change is warranted

- **ID:** P28.15
- **Tier:** T1
- **Goal:** Decide whether a representation change is warranted.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_RESULTS_V1.md`; `docs/research/engine_substrate/COGNITION_REPRESENTATION_SEARCH_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md`; `docs/research/engine_substrate/COGNITION_QUALIA_BEHAVIOR_CONTRACT.md`.
- **Touch:** new `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_DECISION.md`; this document.
- **Pattern to copy:** evidence-scoped accept/retain/reject decisions and P11 full package cost.
- **Steps:** 1. Choose among retaining current representation, offering a verified optional PDS frame, improving learned basis selection, or gathering missing evidence. 2. Require frozen behavioral benefit, supported domain/units, cost accounting and intact risk boundary for runtime adoption; treat external lexical agreement as a separate descriptive result. 3. If a useful result is only finite-aperture or metric-specific, name the condition and prefer a reversible local frame over a global schema replacement.
- **Guard:** decision only; any runtime adoption is a separate concrete scoped task.
- **Acceptance:** one explicit decision with failed/unavailable comparisons retained; no default seed/metric change from paper authority alone; no blanket new approval condition.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_representation_search.py tests/test_ousiometric_risk_boundary.py -q -p no:cacheprovider`.
- **Non-goals:** declaring a new universal set of qualia dimensions or promoting lexical danger to physical risk.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

### P28.16 — Close the tract and update the canonical evidence ledger

- **ID:** P28.16
- **Tier:** T3
- **Goal:** Close the tract and update the canonical evidence ledger.
- **Read first:** `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_RESULTS_V1.md`; `docs/research/engine_substrate/COGNITION_OUSIOMETRIC_DECISION.md`; `docs/research/engine_substrate/COGNITION_BUILD_PLAN_20261010.md`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`.
- **Touch:** `docs/research/engine_substrate/COGNITION_BUILD_PLAN_20261010.md`; `docs/research/engine_substrate/COGNITION_CAPABILITY_ASSESSMENT_20261010.md`; this document.
- **Pattern to copy:** existing completed reporting cycles with independent capability disposition.
- **Steps:** 1. Record implemented conditions, frozen hashes, result/decision and unsupported scope. 2. Update the Phase 28 status and any justified next task while preserving P22 open obligations and all earlier failures. 3. Leave future runtime changes unimplemented until separately scoped; classify no-benefit or unknown results honestly.
- **Guard:** documentation only.
- **Acceptance:** canonical plan points to exact evidence and decision; no inferred L-level closure, human parity or general semantics claim; reporting completion is distinct from benefit.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_ousiometrics_geometry.py tests/test_ousiometric_native_adapter.py tests/test_ousiometric_risk_boundary.py -q -p no:cacheprovider`.
- **Non-goals:** rewriting past evidence, marking the whole cognition plan complete because this tract closes, or committing generated scorecards.
- **Done when:** the named acceptance is established, the declared artifact/structural gate passes, and the task stays within its Touch groups. New tests and artifacts here are planned, not asserted to exist or pass. Spec tasks freeze their contract before behavior implementation.

## 7. Gates and commands for future implementation

No tests or runtime changes were performed by this planning update. Commands below specify later work. All new agent-state/selection mechanisms must be native graph/Rust, self-load-only and disabled by default, with Γ productions, owner/source/model/frame epochs, evidence status and one shared ThinkingBudget. Default and conversation profiles remain isolated. Add to an explicit investigation profile only after its task's focused tests and dependency boot pass; do not silently alter cognition-on defaults.

P28.08 owns investigation-profile integration and records the orphan/boot/provenance audit; P28.13 checks those artifacts before freezing. At each runtime milestone run the task's focused tests, affected qualia/frame/recall tests, engine provenance after a sanctioned build, and the canonical plan §5 baseline accounting. Preserve inherited reds/skips/timeouts; a failure-baseline rewrite needs a separately explained task. Run orphan lint and boot reporting for new runtime signals, with specific provenance-only allowances rather than suppressing unconsumed decisions. The explicit profile audit commands are `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/lint_orphan_signals.py` and `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/report_seed_boot_status.py`; any necessary allowlist edit requires a separately listed ≤3-file task before mutation. Stage exact files only. No implementation here needs a new operator promotion; if an experiment proposes one, use the already required candidate-specific scope and report pending authorization.

The final runner/analyzer must implement:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.ousiometrics.run_v1 --self-check --output /tmp/p28-development.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.ousiometrics.analyze_v1 /tmp/p28-development.json --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.ousiometrics.run_v1 --split heldout --prereg docs/research/engine_substrate/COGNITION_OUSIOMETRIC_PREREG_V1.md --output /tmp/p28-heldout.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.ousiometrics.analyze_v1 /tmp/p28-heldout.json --prereg docs/research/engine_substrate/COGNITION_OUSIOMETRIC_PREREG_V1.md
```

P28.13 freezes exact world counts, seeds, concept-cluster IDs, metrics, tolerances, source licenses and runtime ceilings before the single sealed draw. Proposed standard limits are 200 paired primary streams/family and 100 controls/category, ≤400 outer ticks with ≤100,000 native rule steps/tick, plus a shared request-level budget and graph/byte limits selected from supported development cost measurements. Freeze smaller meaningful primary bounds where supported; increasing a ceiling after seeing treatment benefit requires a new protocol/version. Each failure, denied request and timeout remains visible. The lexical external test is opened only after the representation/checkpoint/anchor alignment freeze; retrieving its bytes earlier for checksum/split construction must not load its test scores into analysis or training.

## 8. Possible outcomes

- **No behavioral benefit, correct invariance:** retain current native representation; the article still supplies a useful external descriptive instrument.
- **Benefit only with fixed metric/finite aperture:** optional verified frame/aperture/metric choice is justified for that supported class; no new information was acquired by rotation alone.
- **Learned frame matches or exceeds both fixed frames:** improve experience-driven representation search rather than install PDS as privileged axes.
- **Independent acquired information improves prediction/transfer:** retain its episode/intervention witnesses and examine whether any PDS interpretation generalizes to fresh contexts; labels are an interpretation, not the verification.
- **Lexical agreement without behavioral gain:** report descriptive alignment and its English/coverage/sense limits; do not adopt a runtime replacement solely on that basis.
- **Safety-word frequency changes means but not world consequences:** treat it as a sampling/communication finding; preserve rare-event strata and the physical consequence boundary.
- **Full-reference inequality or leakage:** invalid measurement, not discovery; fix the implementation, version the protocol and use untouched test allocations.

## 9. Execution status ledger — 2026-10-25

| Task | Status | Evidence and limits |
|---|---|---|
| P28.01 | Complete | Claims and estimands are fixed by the information-matched contract. A reported bounded effect is not new information or evidence of causal independence. |
| P28.02 | Complete for source identity; semantic calibration unsupported | GPADS v2 and NRC VAD v1 metadata, hashes, versions and terms are recorded. The score columns were not opened. |
| P28.03 | Complete for the rounded map | Full-rank/inverse and transported-metric controls pass for the displayed Eq. 4 coefficients. This is not a reproduction of original empirical coordinates or psychological calibration. |
| P28.04 | Complete with narrowed scope | The supported scope is a published rounded rotation of common numeric coordinates. No compatible feature-to-lexical bridge exists. |
| P28.05 | Complete for fixed frames and bounded controls | Disabled native frame seeds preserve source evidence and owner/epoch bindings; metric and precision controls use the same consumer. Focused P28 integration tests passed. |
| P28.06 | Complete for guarded acquisition proposals | Outcome-witness and cost guards are implemented, with rotation distinguished from a new coordinate. This does not establish a learned-frame advantage or useful acquired dimension. |
| P28.07 | Complete for registered simulators | Independent tool-intervention and social-repair worlds emit verified receipts. Their results are simulator-specific. |
| P28.08 | Complete for the opt-in integration profile | Frame projections reach native prediction, retrieval and action consumers; host action selection is absent. Seed boot, orphan-signal and loaded-native provenance checks passed. The P28.01–P28.08 bundle passed 87 tests. |
| P28.09 | Complete; no primary advantage | The six arms shared one native consumer, four horizons, verified target calibration and fresh score contexts. The 2,400-row frozen panel found identical outcome curves across all arms for every paired seed. |
| P28.10 | Complete for sampling controls | Six tests pass. Event support remains fixed while measured/shuffled token weights alter weighted summaries; adverse strata remain visible. This does not estimate environmental risk. |
| P28.11 | Complete for split/scorer safeguards; semantic scores unsupported | Ten tests pass, including oversized-cluster handling, anchor/test separation, frozen bridge/checkpoint binding and missing-concept accounting. With no checkpoint/bridge, external scores remain unopened and lexical status is `UNSUPPORTED`. |
| P28.12 | Complete for the risk boundary | Twenty-one tests pass on the current exact risk/response-inhibition command. Language wording cannot rewrite verified consequences or the full time-indexed future-manifold residual, and the same-epoch native stop still vetoes sink emission. |
| P28.13 | Complete; frozen | Runner/analyzer self-checks and the prescribed 21-test integration command pass. Standalone preregistration `COGNITION_OUSIOMETRIC_PREREG_V1.md` was committed alone as `d0ab272e`; it binds 51 source files, native runtime/build, split, transform, profile and two disjoint 200-seed blocks before P28.14. |
| P28.14 | Complete; structurally valid, efficacy gate fails | Raw panel (SHA-256 `5c49305198670cc5cfc83790060fff7236635ea386d7fbbfff7ee1e51b0c07ef`) has 2,400 complete rows. The single analysis (SHA-256 `d640da5ccd2f86cad4d3dfc307c79807ab79c22b78588a2c75400f01fdb0947f`) found zero AUC difference, [0, 0] 99% interval and Holm p=1 in both families. The exact 22-test geometry/behavior/lexical command passes. No efficacy, semantic calibration, or environmental safety claim follows. |
| P28.15 | Complete; retain default | `COGNITION_OUSIOMETRIC_DECISION.md` rejects promotion of the Eq. 4 frame and records scope, risks, costs and next evidence conditions. The prescribed representation-search/risk command passes 22 tests. |
| P28.16 | Complete; canonical closeout recorded | The current plan and capability assessment link this preregistration, result and decision. The exact geometry/native-adapter/risk command passes 21 tests. P28 is closed as an investigation/reporting cycle; P22 remains separately open. |

The result reports every arm, failure, abstention, cost and adverse receipt
exposure. In the primary score checkpoints, both arms had 0.21125 adverse
outcome frequency in tool intervention and 0.00375 in social repair; the
primary differences were zero. Calibration receipts were also included in
the descriptive all-receipt risk accounting (204 adverse tool calibrations
per primary arm, zero social calibrations). These are counts from the frozen
simulators, not independent real-world observations. The low 0.04125 social
AUC indicates limited task sensitivity for that family.

The full [results ledger](COGNITION_OUSIOMETRIC_RESULTS_V1.md) and
[decision](COGNITION_OUSIOMETRIC_DECISION.md) preserve the complete scope and
limits. No default representation, metric, risk gate, or capability level
changed. P22's remaining lineage, resource-preflight, standalone-freeze and
held-out obligations remain open.
