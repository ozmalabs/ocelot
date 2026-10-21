# Cognition build Phase 4 — Representation, recall and manifold integration

**Detailed on:** 2026-10-21. **Status:** execution in progress; mechanism implementation is partial and held-out evaluation has not been run.
**Parent:** [Cognition build plan](COGNITION_BUILD_PLAN_20261010.md). **Entry evidence:** [P3 results](COGNITION_BUILD_P3_RESULTS.md), implementation `32143620`, preregistration `eb34efb3`.

## Scope corrections from the current checkout

- P3 H1/H2/H3/H5 passed; H4 failed overall. Family-A first and repeat encounters both cost one funded step, so caching rung 1 is not a demonstrated speedup. Preserve that result. P4 measures actual candidate/verification work, with independently generated deeper cases where needed; it does not re-score P3.
- `qualia_space.json` already defines typed dimensions and `test_qualia_space_migrated.py` already exercises dimension-tagged signatures. D3 connects numeric Shape signatures and native consumers to that schema; it does not create a second space or rewrite lexical qualia.
- `memory.rs::ShapeIndex` keeps a most-recent **cluster** leaf key and returns a cluster, not exact per-record nearest neighbors. D4 must define record-level indexing, invalidation and ties. Exposing `descent()` under a new name is insufficient.
- `MetaShapeMint` anti-unifies recurring relation signatures. It is not a numeric finite-difference signature primitive. D2 first characterizes `number_runner.py::aperture_signature` and `mint_shape`, then composes numeric Rust primitives and graph rules. It does not force numeric shapes through MetaShapeMint.
- `future_manifold.rs` and `test_future_manifold_projection_native.py` already cover generic projection, learned paths, residual shapes, sparse refinement, fixed points and budget exhaustion. E1 adds the GWM candidate producer and links its refinement to funded requests. E2 consolidates remaining callers based on an audited map; it does not rebuild the native projector.
- TimeInfer/order-N already exists in `shape_decode.rs`, and `time_axis.json` accepts `Observation{frames, status:motion_seq}` (`test_time_infer_migrated.py`). P3's ordinary observations have no frames. P4.D1 closes that input/lifecycle gap for regular streams; irregular sampling remains an explicit decision, with unsupported input refused.

## Order and interfaces

`H0 → D2.1 → D3.1 → D2.2/D3.2 → D4 spec → R1–R4 → D4.2 → D5`; `C5` follows H0 and the P2 aperture pathology tests. `E1` needs C5 plus D3; `E2` needs E1. `D1` needs the temporal schema in D3.1 and P3's budget contract. H3 integrates the profile before H1 freezes all artifacts; H2 draws and reports, then H4 closes the documentation.

Track I receives versioned signature descriptors from D3, candidate recall from D4 and Observer frames from C5. Read any committed I0/I1 schema decision before implementation. The untracked `process_schema.json` and generators are not a stable dependency. Exchange a graph reference to the representation, owner, epoch and provenance; do not redefine ProcessSchema here. D1 owns observation sequence assembly; I4.2 owns using a temporal latent to explain persistent prediction error.

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

### P4.H0 — Pin entry state and implementation boundaries

- **ID:** P4.H0
- **Tier:** T1
- **Goal:** Pin entry state and implementation boundaries.
- **Read first:** `COGNITION_BUILD_P3_RESULTS.md:1`; `COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md:65`; `substrate/boot_profiles.py:769`; `results/cognition_gate_baseline.json`.
- **Touch:** this plan; new `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** P3 results verification table.
- **Steps:** 1. Record committed head, engine provenance, dirty ownership and P3 statuses. 2. Freeze a producer/consumer and default-isolation table for new seeds. 3. Record acceptance names and proposed protocols below in the preregistration.
- **Guard:** documentation only.
- **Acceptance:** entry ledger distinguishes pass, baseline failure and NOT_ESTABLISHED; every original P4 item and deferred temporal item has an owner.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** running held-out draws; assuming concurrent Track I code has landed.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.H0.1 — Keep inherited subsystem guards scoped to their subsystem

- **ID:** P4.H0.1
- **Tier:** T1
- **Goal:** Preserve the Arc decompose no-new-Rust guard while allowing unrelated, explicitly scoped cognition engine Terms.
- **Read first:** `tests/test_arc_decompose_migrated.py::test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`; P4.R0 and P4.R1.
- **Touch:** this plan; `tests/test_arc_decompose_migrated.py`.
- **Steps:** Replace the whole-engine Rust diff assertion with a check on Arc-owned Rust paths; retain the exact AST pins for the Arc routing functions. Copy the ignored ARC6 input artifact into the isolated worktree for the inherited test, without modifying the source checkout.
- **Acceptance:** the Arc gate still rejects changes under Arc-owned engine paths and passes when unrelated P4 terms change.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_arc_decompose_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** changing Arc seed behavior, test vectors or its held-out result.
- **Done when:** the named gate passes; any red status is compared against the P3 baseline.

### P4.H0.2 — Count Γ-constrained node types as consumed in orphan-signal lint

- **ID:** P4.H0.2
- **Tier:** T1
- **Goal:** Avoid false orphan reports for node types that a matched Γ edge consumes.
- **Read first:** `scripts/lint_orphan_signals.py::_extract_seed_writes_and_reads`; P4's new candidate/window node productions.
- **Touch:** this plan; `scripts/lint_orphan_signals.py`; new `tests/test_lint_orphan_signals.py`.
- **Steps:** Build an edge-to-endpoint-type map from seed productions. When a rule matches a declared edge, count its production endpoint types as reads, since Γ constrains the matched nodes by those types. Do not suppress node types without a matched declared edge, and do not change attribute/edge orphan semantics.
- **Guard:** linter accounting only; no allowlist additions.
- **Acceptance:** a fixture with a produced node type consumed through a declared matched edge is not an orphan; an unconsumed node type remains an orphan.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_lint_orphan_signals.py -q -p no:cacheprovider`.
- **Non-goals:** treating provenance attrs/edges as consumed; broad allowlist edits.
- **Done when:** fixture tests pass and full orphan lint reports no false orphan node types for P4 candidate/window nodes.

### P4.H0.3 — Justify P4 audit-only outputs in the orphan-signal allowlist

- **ID:** P4.H0.3
- **Tier:** T1
- **Goal:** Keep auditable residual, version, event and provenance outputs without hiding decision signals.
- **Read first:** P4.H0.2; `scripts/lint_orphan_signals.py`; current P4 manifold and temporal seeds.
- **Touch:** this plan; `scripts/orphan_signal_allowlist.json`; `docs/research/engine_substrate/COGNITION_BUILD_P4_PREREG.md`.
- **Steps:** Confirm each new orphan is an audit/provenance output with a concrete consumer in phase reporting or lineage inspection. Remove any field that is neither consumed nor needed for audit. Add exact allowlist reasons for only retained audit/provenance outputs.
- **Guard:** no decision, status, budget, eligibility, or adoption signal may be allowlisted.
- **Acceptance:** P4 signal audit identifies all new entries and classifies them as projection metrics, event provenance, model lineage, request identity, or terminal provenance; orphan lint leaves no unclassified P4 writes.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/lint_orphan_signals.py --exclude-allowlisted`.
- **Non-goals:** suppressing runtime decisions, changing linter semantics, or broad allowlist cleanup.
- **Done when:** every remaining P4 orphan has a specific reason and no decision signal is allowlisted.

### P4.D2.1 — Specify native numeric signature minting

- **ID:** P4.D2.1
- **Tier:** T1
- **Goal:** Specify native numeric signature minting.
- **Read first:** `tests/capability/number_qualia/runners/number_runner.py:594-659`; `domains/order_n_concepts.py:32-65`; `seeds/meta_shape_growth.json`; `runners/dsl/src/memory.rs:435-472`.
- **Touch:** `COGNITION_BUILD_P4_PREREG.md`; new `tests/test_qualia_shape_mint_migrated.py`.
- **Pattern to copy:** number_runner.py::mint_shape and native meta_shape_growth mint lifecycle.
- **Steps:** 1. Freeze finite-difference order, padding/truncation compatibility and invalid-input behavior. 2. Specify signed evidence updates, reading adoption and deterministic matching for multiple candidates. 3. Write legacy parity fixtures plus collision, empty, repeated and negative-outcome cases; preserve original full coordinate as audit data.
- **Guard:** planned `QualiaShapeMintPolicy.enabled=0`.
- **Acceptance:** planned tests `test_legacy_signature_parity`, `test_repeated_outcome_is_idempotent`, `test_negative_outcome_cannot_ground_reading`; ambiguous matches remain unresolved unless verifier distinguishes them.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_shape_mint_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** porting number_runner rescue/solver oracles into the agent; changing legacy fixed width without a version.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D3.1 — Freeze a dimension-tagged representation and temporal envelope

- **ID:** P4.D3.1
- **Tier:** T1
- **Goal:** Freeze a dimension-tagged representation and temporal envelope.
- **Read first:** `seeds/qualia_space.json:1-95`; `domains/qualia_schema.py::validate_signature`; `tests/test_qualia_space_migrated.py:102-156`; `runners/dsl/src/term.rs:1959-1995`; `domains/tom_meta_shape.py:31-50`.
- **Touch:** new `COGNITION_SIGNATURE_CONTRACT.md`; `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** qualia_space typed dimensions and separate crystallized/live overlay.
- **Steps:** 1. Define version, dimension identity, value kind, missing versus zero, grain, frame, owner, source epoch and evidence status. 2. Map sig_k, valence and existing dimension coordinates through typed adapters; retain original forms. 3. Define ordered SequenceObservation/frame links, timestamps, window identity and regular-sampling support; prohibit filling invented frames.
- **Guard:** schema only; no boot changes.
- **Acceptance:** all three existing representations have a reversible source reference; dimension mismatch cannot become a match; temporal support and rejection are explicit.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_space_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** flattening heterogeneous dimensions; treating valence as evidence of truth; redesigning lexical parsing.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D2.2 — Mint and update verified Shapes through graph rules

- **ID:** P4.D2.2
- **Tier:** T2
- **Goal:** Mint and update verified Shapes through graph rules.
- **Read first:** `COGNITION_SIGNATURE_CONTRACT.md`; `tests/test_qualia_shape_mint_migrated.py`; `scripts/gen_extended_thinking_seed.py`; `seeds/tolerance_registry.json`.
- **Touch:** new `scripts/gen_qualia_shape_mint_seed.py` + `seeds/qualia_shape_mint.json`; `tests/test_qualia_shape_mint_migrated.py`.
- **Pattern to copy:** P3 generator dedup and provenance; D2.1 parity expression.
- **Steps:** 1. Compose existing numeric Terms for the frozen signature. 2. Mint once per verified outcome ID; dedup within owner/frame/grain, store conflicting evidence separately. 3. Admit positive reading candidates only through the existing exact verifier; test dependency-only boot and generator reproduction.
- **Guard:** `QualiaShapeMintPolicy.enabled`, default 0.
- **Acceptance:** D2.1 tests plus `test_dependency_closure_loads`, `test_generator_reproduces_seed`, `test_ambiguous_match_does_not_overwrite`; runtime Python performs ingestion only.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_shape_mint_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** editing the legacy oracle runner to make parity pass; global signature dedup across frames.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D3.2 — Expose existing signatures to native consumers

- **ID:** P4.D3.2
- **Tier:** T2
- **Goal:** Expose existing signatures to native consumers.
- **Read first:** `COGNITION_SIGNATURE_CONTRACT.md`; `seeds/qualia_space.json`; `tests/test_qualia_space_migrated.py:118-180`; `domains/qualia_schema.py::validate_signature`.
- **Touch:** new `scripts/gen_cognition_signature_seed.py` + `seeds/cognition_signature.json`; new `tests/test_cognition_signature_migrated.py`.
- **Pattern to copy:** dimension-tagged coordinate assertions in test_qualia_space_migrated.
- **Steps:** 1. Add graph projection/adaptation rules and Γ edges for source descriptors. 2. Preserve missing dimensions and live/standing distinction. 3. Rebuild descriptors on source epoch changes; retire stale views.
- **Guard:** `CognitionSignaturePolicy.enabled`, default 0.
- **Acceptance:** `test_three_sources_are_readable`, `test_dimension_tags_prevent_false_match`, `test_source_epoch_invalidates`, `test_live_overlay_is_not_commitment`, `test_verified_numeric_shape_is_adapted_from_real_graph_record`, and `test_verified_qualia_valence_revision_retires_old_descriptor`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_signature_migrated.py tests/test_qualia_space_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** rewriting domains/analogy_search Python reasoning in this task; a new lexical codebook.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D4.1 — Specify bounded record-level similarity recall

- **ID:** P4.D4.1
- **Tier:** T1
- **Goal:** Specify bounded record-level similarity recall.
- **Read first:** `runners/dsl/src/memory.rs:603-718`; `runners/dsl/src/memory.rs::recall_by_shape`; `COGNITION_SIGNATURE_CONTRACT.md`; `tests/test_qualia_space_migrated.py:225-270`.
- **Touch:** `COGNITION_SIGNATURE_CONTRACT.md`; `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** ShapeIndex::put, remove_key and descent as storage precedents; no exact top-k precedent, so freeze a T1 spec.
- **Steps:** 1. Specify RecallNearest with explicit query owner/frame/epoch and source scope; k=0 and malformed queries return typed empty/error results. 2. Define per-dimension metric, missing-coordinate policy, tolerance units, deterministic stable-key tie order and no arbitrary tie-as-truth. 3. Specify per-record keys, tombstones, stale disk entries, eviction/recovery, query bounds and candidate-only result `{key,distance,source_epoch}`; durable loading is separate from pure retrieval.
- **Guard:** new Term has no default caller.
- **Acceptance:** spec includes exhaustive-scan reference, equal-distance ties, absent dimensions, cross-owner isolation, updated/deleted record and checkpoint round-trip cases.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_qualia_space_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** assuming cluster leaf keys can rank records; automatic adoption or I/O inside a pure query.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

## P4.R — Rust integration for `RecallNearest`

These tasks run only if the corresponding spec establishes that existing Terms cannot express the operation. Each task is a single variant change. The spec freezes the argument and result schema first. No caller becomes active until R4 passes. If no new variant is needed, record all four tasks as not required with the existing expression and test evidence.

### Numeric-signature primitive deviation (P4.H0/D2.1)

The Term audit found no compact existing operation that computes the legacy dynamic-length, repeated finite difference followed by strict ordinal ranks over a numeric list. `Fold` and `Append` can express list reductions, but without a range/map operation the dynamic sequence of adjacent differences cannot be constructed without a large unrolled rule set. P4 therefore adds one pure `ShapeRankSignature(samples, order, width)` Term that delegates to the existing Rust `memory::shape_signature` after finite-difference construction. Its contract is frozen in `COGNITION_SIGNATURE_CONTRACT.md`; it returns a fixed-width integer list and `None` for malformed, non-finite, over-bound, or invalid-order input. This is a single graph-composable primitive, not a Python reasoning path.

The additional work items, each scoped to the files listed, are:

| Task | Touch | Acceptance |
|---|---|---|
| P4.R0.1 — evaluator and Rust tests | `runners/dsl/src/term.rs` | Valid ranks, ties, empty differences, invalid orders and no graph mutation |
| P4.R0.2 — serialization and reflection | `runners/dsl/src/jsonio.rs`, `runners/dsl/src/reflect.rs` | JSON and graph round trips preserve all inputs |
| P4.R0.3 — traversal and variant metadata | `runners/dsl/src/rewrite.rs`, `runners/dsl/src/term_variants.rs`, `runners/dsl/src/shape.rs` | Free-variable/remap/stability coverage, exhaustive variant dispatch and regenerated metadata |
| P4.R0.4 — native exposure | new `tests/test_shape_rank_signature_migrated.py` | Evaluates the Term through the built native engine and matches the legacy fixtures |

R0.1–R0.4 precede D2.2. The same clean-worktree and engine-provenance gate applies. This evidence-based deviation replaces only D2.2's instruction to compose the signature from existing Terms; all Shape decisions and lifecycle remain graph rules.

### P4.R1 — Define and evaluate RecallNearest

- **ID:** P4.R1
- **Tier:** T2
- **Goal:** Define and evaluate RecallNearest.
- **Read first:** `runners/dsl/src/term.rs::TermNode`; `runners/dsl/src/memory.rs`; `COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** `runners/dsl/src/term.rs`; `runners/dsl/src/memory.rs`.
- **Pattern to copy:** `term.rs::TimeInfer` dispatch and `shape_decode.rs::eval_time_infer`.
- **Steps:** 1. Add the frozen variant and evaluator. 2. Add Rust unit tests for valid, empty, malformed and bounded inputs. 3. Cover every ownership and failure case in the spec.
- **Guard:** new variant has no callers in default seeds.
- **Acceptance:** Rust unit tests assert the frozen output and no mutation of the live graph.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** new Python decision code; changes to other variants.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.R2 — Wire RecallNearest JSON and graph reflection

- **ID:** P4.R2
- **Tier:** T2
- **Goal:** Wire RecallNearest JSON and graph reflection.
- **Read first:** `runners/dsl/src/jsonio.rs`; `runners/dsl/src/reflect.rs`; `COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** `runners/dsl/src/jsonio.rs`; `runners/dsl/src/reflect.rs`.
- **Pattern to copy:** existing `TimeInfer` arms in both modules.
- **Steps:** 1. Add parse and serialize arms. 2. Add reflection and reconstruction. 3. Test JSON and graph round trips without losing optional fields.
- **Guard:** new variant only.
- **Acceptance:** round-trip tests preserve every field and reject malformed forms.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** evaluator semantics changes.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.R3 — Wire RecallNearest traversal and variant metadata

- **ID:** P4.R3
- **Tier:** T2
- **Goal:** Wire RecallNearest traversal and variant metadata.
- **Read first:** `runners/dsl/src/rewrite.rs`; `runners/dsl/src/term.rs`; `runners/dsl/src/term_variants.rs`.
- **Touch:** `runners/dsl/src/rewrite.rs`; `runners/dsl/src/term.rs`; `runners/dsl/src/term_variants.rs`.
- **Pattern to copy:** existing `TimeInfer` substitution, free-variable and metadata arms.
- **Steps:** 1. Cover substitution, clone/remap, free variables and stability. 2. Regenerate tracked variant metadata by its existing generator. 3. Audit all exhaustive dispatch sites; if additional sites are found, add separate ≤3-file task records before touching them.
- **Guard:** new variant only.
- **Acceptance:** free-variable isolation, graph-change invalidation, serialization and compile checks pass; no missing dispatch arm.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** unconditional memoization of graph mutation; copying another author’s generated artifacts.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.R4 — Build and expose RecallNearest through the native evaluator

- **ID:** P4.R4
- **Tier:** T2
- **Goal:** Build and expose RecallNearest through the native evaluator.
- **Read first:** `scripts/engine_build.sh`; `runners/dsl/src/py.rs`; `COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** new `tests/test_recall_nearest_migrated.py`; `runners/dsl/src/py.rs` only if generic evaluation is insufficient.
- **Pattern to copy:** `tests/test_time_infer_migrated.py::_boot` and native Term evaluation.
- **Steps:** 1. Build through engine_build.sh after disk check. 2. Evaluate JSON through the native API; add a thin binding only if required. 3. Run Rust tests, provenance and regression gates; record artifact hash.
- **Guard:** no default feature or default seed changes.
- **Acceptance:** native acceptance covers the full frozen spec; provenance identifies the new engine; Cargo baseline has no new failures.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_recall_nearest_migrated.py tests/test_engine_provenance_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** default Cargo feature changes; JIT or WASM semantic forks.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D4.2 — Recall candidates before funded generation

- **ID:** P4.D4.2
- **Tier:** T2
- **Goal:** Recall candidates before funded generation.
- **Read first:** `COGNITION_SIGNATURE_CONTRACT.md`; `seeds/extended_thinking.json`; `tests/test_extended_thinking_migrated.py`; `seeds/thinking_budget.json`.
- **Touch:** new `scripts/gen_similarity_recall_seed.py` + `seeds/similarity_recall.json`; new `tests/test_similarity_recall_migrated.py`.
- **Pattern to copy:** P3 pending-request approval and cache-to-verifier path.
- **Steps:** 1. Query compatible held records before generation. 2. Reverify recalled reading/program against the present observation. 3. On no hit, stale hit or failed verification, continue the original funded ladder; instrument retrieved, verified and generated candidates separately.
- **Guard:** `SimilarityRecallPolicy.enabled`, default 0.
- **Acceptance:** `test_hit_reverified_before_acceptance`, `test_stale_hit_falls_back`, `test_no_unfunded_generation`, `test_incompatible_owner_is_hidden`; P3 rung-1 repeats still report one step.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_similarity_recall_migrated.py tests/test_extended_thinking_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** replacing exact verifiers with nearest-neighbor scores; modifying P3 H4.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D5.1 — Freeze cross-domain transfer and recall cost evaluation

- **ID:** P4.D5.1
- **Tier:** T1
- **Goal:** Freeze cross-domain transfer and recall cost evaluation.
- **Read first:** `COGNITION_BUILD_P4_PREREG.md`; `COGNITION_SIGNATURE_CONTRACT.md`; `tests/capability/number_qualia/track_j_cross_domain_transfer.py`; `evaluation/substrate_capability/extended_thinking_instances_v1.py`.
- **Touch:** new `evaluation/substrate_capability/cognition_p4_instances_v1.py`; new `tests/test_cognition_p4_instances.py`; `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** P3 seeded instance generation; Track J oracle is external scoring only.
- **Steps:** 1. Generate 200 held-out target instances per transfer direction across graph-role and numeric-sequence families with explicit shared structural relation, plus 100 incompatible decoys per direction. Graph-role targets must contain at least two candidate nodes so the outcome requires matching the source relation; incompatible controls contain no candidate with the source relation. 2. Fix source-only training exposure, disjoint identities and compatible frame-map requirements; remove all score labels and deterministic draw seeds from agent-visible payloads. 3. Register paired recall-on/off and mismatched-source arms over identical target problems; primary success is ≥25% fewer exact candidate checks on successful paired targets, solve-rate loss ≤2 percentage points, and zero false grounded decoys. Development draws must use indices outside 0–199 and may not consume registered indices.
- **Guard:** evaluation only.
- **Acceptance:** `test_disjoint_source_target_ids`, `test_generator_deterministic`, `test_scoring_oracle_never_ingested`, and two-candidate graph-role controls with null oracle target for incompatible decoys; paired arm target identity; opaque IDs; no seed/compatibility labels in agent payload; full-hash/range validation; development-index isolation. Report failures to find a transferable frame.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_p4_instances.py -q -p no:cacheprovider`.
- **Non-goals:** label leakage through signatures, target answers or human-selected solution indices.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D5.2 — Remove compatibility leakage and make numeric transfer choices explicit

- **ID:** P4.D5.2
- **Tier:** T1
- **Goal:** Ensure D5 agent payloads do not expose compatibility labels and both families require choosing between target candidates.
- **Read first:** P4.D5.1; `evaluation/substrate_capability/cognition_p4_instances_v1.py`; `tests/test_cognition_p4_instances.py`.
- **Touch:** this plan; `evaluation/substrate_capability/cognition_p4_instances_v1.py`; `tests/test_cognition_p4_instances.py`.
- **Steps:** Remove nested compatibility/status labels from the agent view while retaining the concrete frame map. Add two opaque candidate values to numeric targets; only compatible targets contain a candidate consistent with the source pattern. Make mismatched-source arms differ in source evidence while keeping the target and valid frame mapping unchanged. Keep candidate identity and correctness in the scorer-only oracle.
- **Guard:** generator/evaluator boundary only; oracle remains separate.
- **Acceptance:** recursively inspect agent payloads for compatibility/status labels; both families have two candidates; only the scorer oracle identifies the target candidate; mismatch arms retain identical targets/frame maps and differ only in source evidence.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_p4_instances.py -q -p no:cacheprovider`.
- **Non-goals:** changing registered sample sizes or D5 thresholds.
- **Done when:** development fixtures prove label isolation and two-candidate discrimination.

### P4.D5.3 — Execute the transfer arms with native candidate retrieval

- **ID:** P4.D5.3
- **Tier:** T2
- **Goal:** Replace D5 null outcome slots with graph/native agent outcomes and scorer-derived decisions.
- **Read first:** P4.D5.1/D5.2; `tests/test_recall_nearest_migrated.py`; `evaluation/substrate_capability/cognition_p4_heldout_v1.py`; `evaluation/substrate_capability/cognition_p4_analysis_v1.py`.
- **Touch:** `evaluation/substrate_capability/cognition_p4_heldout_v1.py`; `evaluation/substrate_capability/cognition_p4_analysis_v1.py`; `tests/test_cognition_p4_analysis.py`.
- **Steps:** Mechanically project source/candidate evidence into typed records; let native `RecallNearest` rank the recall-on arm and native exact projection terms execute the recall-off baseline. Keep selection and exact-check counts in native Term output. Derive solved and false-grounded outcomes only in the analyzer from the separate scorer oracle. Preserve paired digests, timeout/null accounting and full range checks.
- **Guard:** evaluation only; no oracle or label in agent-visible values.
- **Acceptance:** development panel has non-null measured outcomes; compatible targets are solved by both arms with lower recall-on exact-check work; incompatible decoys and mismatched-source arms never select a candidate; numeric and graph-role actions execute through native Terms; analyzer self-check catches false certification and malformed work counts.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_p4_analysis.py -q -p no:cacheprovider`.
- **Non-goals:** counting retrieval work as exact verification work; using oracle labels to select candidates.
- **Done when:** all registered D5 outcomes are mechanically generated by the runner, with the held-out result still gated by H1's frozen artifact rule.

### P4.C5.1 — Specify Observer-frame adapters and ownership

- **ID:** P4.C5.1
- **Tier:** T1
- **Goal:** Specify Observer-frame adapters and ownership.
- **Read first:** `seeds/observer_aperture.json:1-80`; `tests/test_observer_aperture_migrated.py:119-260`; `tests/test_aperture_frame_migrated.py:121-173`; `seeds/stress_aperture.json`; `COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** new `COGNITION_APERTURE_ADAPTER_CONTRACT.md`; `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** Observer projection and aperture_frame meet/intersection.
- **Steps:** 1. Map reading, dwell, finite-difference k, QualiaAperture, ShapeDecode scope and manifold mask to distinct typed frame dimensions. 2. Specify chosen versus forced frame authority, physiological floor, source epoch and restoration. 3. Freeze lossless legacy readbacks and evidence/VOI predicates; unknown VOI cannot claim a positive value.
- **Guard:** schema only.
- **Acceptance:** six-row adapter matrix gives source attrs, units, owner, read/write direction and invalidation; forced constraints cannot be relaxed.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_aperture_frame_migrated.py tests/test_observer_aperture_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** calling all aperture parameters the same scalar; silently substituting stress for the mask.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.C5.2 — Implement six frame adapters and funded questioning

- **ID:** P4.C5.2
- **Tier:** T2
- **Goal:** Implement six frame adapters and funded questioning.
- **Read first:** `COGNITION_APERTURE_ADAPTER_CONTRACT.md`; `scripts/gen_aperture_frame_seed.py`; `seeds/thinking_budget.json`; `tests/test_aperture_frame_migrated.py:269-333`.
- **Touch:** new `scripts/gen_cognition_aperture_seed.py` + `seeds/cognition_aperture.json`; new `tests/test_cognition_aperture_migrated.py`.
- **Pattern to copy:** existing hidden-residual questioning and forced-frame tests.
- **Steps:** 1. Implement one explicit rule family per adapter, avoiding dynamic attribute-name writes. 2. Project held and observed shapes through the same frame. 3. Fund bounded chosen-frame probes; preserve forced constraints and restore all terminal leases; keep a diagnostic full-view comparison where permitted.
- **Guard:** `CognitionAperturePolicy.enabled`, default 0.
- **Acceptance:** parameterized `test_six_adapters_round_trip`, `test_two_observers_do_not_leak`, `test_forced_frame_preserved`, `test_hidden_residual_probe_is_funded`, `test_terminal_restore`; dependency-only boot passes.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_aperture_migrated.py tests/test_aperture_frame_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** generic relaxation of arbitrary tolerance metadata; changing frozen observer rules.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.C5.3 — Add an opt-in authorization hook for funded aperture questions

- **ID:** P4.C5.3
- **Tier:** T2
- **Goal:** Ensure the legacy chosen-frame questioning rules cannot run a P4-governed probe before its funded authorization.
- **Read first:** `scripts/gen_aperture_frame_seed.py::build_seed`; P4.C5.1/C5.2; `tests/test_aperture_frame_migrated.py` hidden-residual fixtures.
- **Touch:** this plan; `scripts/gen_aperture_frame_seed.py`; `tests/test_aperture_frame_migrated.py`.
- **Steps:** 1. Add an absent-by-default observer flag that preserves legacy question semantics when not set. 2. When `ap_question_funding_required` is true, gate only the probe projection and verdict rules on a P4 authorization flag; keep dwell accounting and forced/agreed aperture constraints intact. 3. Test the legacy path and that a guarded observer does not probe without authorization.
- **Guard:** no default behavior change; P4 opt-in only.
- **Acceptance:** existing ApertureFrame suite remains behavior-compatible; new fixture proves no probe and no frame change while guarded without authorization.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_aperture_frame_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** changing physiological floors, forced-frame authority, residual semantics, or other Observer rules.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Any fund/unlock/restore state remains owned by C5.2's P4 adapter.

### P4.C5.4 — Fund and restore per-observer hidden-residual probes

- **ID:** P4.C5.4
- **Tier:** T2
- **Goal:** Bind P4 aperture sources to concrete Observers and authorize legacy probes only after one same-epoch ThinkingBudget debit.
- **Read first:** P4.C5.1–C5.3; `seeds/thinking_budget.json`; `COGNITION_APERTURE_ADAPTER_CONTRACT.md`.
- **Touch:** this plan; `scripts/gen_cognition_aperture_seed.py` + `seeds/cognition_aperture.json`; `tests/test_cognition_aperture_migrated.py`.
- **Steps:** 1. Require a source-to-Observer link and chosen authority. 2. Save the Observer's question threshold, set the funding-required guard, open one request per observer/frame-generation/source-epoch, and authorize only after same-epoch debit. 3. Denial and epoch change leave probes blocked; terminal keep/drop restores authorization state and closes the request.
- **Guard:** `CognitionAperturePolicy.enabled`, default 0; forced observers cannot request or unlock.
- **Acceptance:** `test_hidden_residual_probe_is_funded`, `test_two_observers_do_not_leak`, `test_forced_frame_preserved`, `test_denied_probe_does_not_run`, `test_terminal_restore`, `test_unknown_voi_stays_unresolved`; request is debited once and forced constraints remain unchanged.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_aperture_migrated.py tests/test_aperture_frame_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** changing residual scoring or allowing a P4 policy to unlock negotiated/forced frames.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Held-out C5 evidence remains owned by H1/H2.

### P4.E1.1 — Specify GWM-to-manifold projection and refinement

- **ID:** P4.E1.1
- **Tier:** T1
- **Goal:** Specify GWM-to-manifold projection and refinement.
- **Read first:** `runners/dsl/src/future_manifold.rs::projection_field`; `tests/test_future_manifold_projection_native.py:659-740`; `seeds/generative_world_model.json`; `seeds/impasse_simulation_bridge.json`; `CLAUDE.md:40-65`.
- **Touch:** new `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`; `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** existing native time-addressed residual audit and GWM SimulationRequest.
- **Steps:** 1. Map model branches to time-indexed candidate cells/topology, uncertainty widths, support, retained/lost/escape residuals and physical horizons. 2. Require model-derived candidates when caller supplies no moves; absent transitions mean unresolved, not an invented feasible path. 3. Specify funded refinements as new projection versions, and explicit identity/bound transitions for wait/refine/commit comparison.
- **Guard:** no new active caller yet.
- **Acceptance:** contract retains full residual shapes and hard vetoes; goals only break equal-intervention ties; incomplete horizon and budget exhaustion cannot certify retention.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_future_manifold_projection_native.py -q -p no:cacheprovider`.
- **Non-goals:** inventing a scalar risk score; altering the existing engine-wide commit boundary.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.E1.2 — Produce and refine audited manifold candidates from GWM

- **ID:** P4.E1.2
- **Tier:** T2
- **Goal:** Produce and refine audited manifold candidates from GWM.
- **Read first:** `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`; `scripts/gen_impasse_simulation_bridge_seed.py`; `seeds/generative_world_model.json`; `seeds/thinking_budget.json`.
- **Touch:** new `scripts/gen_cognition_manifold_seed.py` + `seeds/cognition_manifold.json`; new `tests/test_cognition_manifold_migrated.py`.
- **Pattern to copy:** P1 SimulationRequest lifecycle and P3 request/lease lifecycle.
- **Steps:** 1. Generate admissible candidate trajectories from model actions without supplied moves. 2. Project via the existing native Terms and version each funded refinement; cache only descriptors linked to model/frame epochs. 3. Restore and terminate on no model, exhaustion, changed manifold or unsupported uncertainty.
- **Guard:** `CognitionManifoldPolicy.enabled`, default 0.
- **Acceptance:** `test_no_supplied_moves_uses_gwm`, `test_missing_model_unresolved`, `test_refinement_request_debited_once`, `test_model_change_invalidates_cache`, `test_residual_shapes_preserved`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_manifold_migrated.py tests/test_future_manifold_projection_native.py -q -p no:cacheprovider`.
- **Non-goals:** editing frozen GWM core; assuming P3 scalar knob leases directly refine a trajectory.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.E1.3 — Mint exact feasibility receipts from complete native projections

- **ID:** P4.E1.3
- **Tier:** T2
- **Goal:** Distinguish an exact in-bounds full-horizon model path from a candidate projection that is merely resolved or has an escape.
- **Read first:** P4.E1.1/E1.2; `runners/dsl/src/future_manifold.rs::projection_field`; `tests/test_cognition_manifold_migrated.py`.
- **Touch:** `scripts/gen_cognition_manifold_seed.py` + `seeds/cognition_manifold.json`; `tests/test_cognition_manifold_migrated.py`.
- **Steps:** Add a receipt rule requiring same-model/epoch supported transition provenance, projection support and resolution, zero residual loss, zero information loss, and full candidate horizon. Preserve projection/residual evidence; a resolved escape must not mint a receipt.
- **Guard:** `CognitionManifoldPolicy.enabled`, default 0; receipt certifies only the registered target/bounds predicate, not real-world execution.
- **Acceptance:** `test_complete_in_bounds_projection_mints_receipt`; `test_escape_and_incomplete_projection_never_mint_receipt`; `test_receipt_binds_model_epoch_and_projection_version`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_manifold_migrated.py tests/test_future_manifold_projection_native.py -q -p no:cacheprovider`.
- **Non-goals:** turning projection into observation; changing native projection semantics.
- **Done when:** only complete, supported, same-epoch, zero-loss projections receive a provenance-linked receipt.

### P4.E1.4 — Score E1/E2 worlds from graph feasibility receipts

- **ID:** P4.E1.4
- **Tier:** T2
- **Goal:** Replace E1/E2's unconditional null verifier outcomes with measured receipt-backed candidate outcomes.
- **Read first:** P4.E1.3; `evaluation/substrate_capability/cognition_p4_heldout_v1.py::_e1e2_arm`; `evaluation/substrate_capability/cognition_p4_analysis_v1.py::_analyze_e1e2`.
- **Touch:** `evaluation/substrate_capability/cognition_p4_heldout_v1.py`; `evaluation/substrate_capability/cognition_p4_analysis_v1.py`; `tests/test_cognition_p4_analysis.py`.
- **Steps:** Read only graph receipts tied to the current candidate/model/epoch/version. Report receipt count and false certification separately; compute supplied-path parity as before. Keep the randomized world label in the scorer-only sibling field.
- **Guard:** evaluation adapter; no world-kind or feasibility label enters the agent graph.
- **Acceptance:** development worlds show receipts for feasible paths, none for escaped or missing paths, and the analyzer treats malformed/stale receipts as violations or nulls.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_p4_analysis.py tests/test_cognition_manifold_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming the symbolic GWM core already supplies numeric paths; using evaluator labels to certify.
- **Done when:** E1/E2 arm outcomes reflect graph-produced feasibility receipts and preserve scorer isolation.

### P4.E2.1 — Audit remaining manifold implementations and freeze parity

- **ID:** P4.E2.1
- **Tier:** T1
- **Goal:** Audit remaining manifold implementations and freeze parity.
- **Read first:** `domains/regulated_train_of_thought.py:66-200`; `runners/dsl/src/future_manifold.rs::projection_field`; `runners/dsl/src/motor_compose.rs`; `tests/test_future_manifold_projection_native.py:659-740`; `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`.
- **Touch:** `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`; new `tests/test_thought_manifold_migrated.py`.
- **Pattern to copy:** existing atomic projection snapshots and field parity tests.
- **Steps:** 1. Enumerate live entry points, decision owners and fallback paths instead of assuming exactly three remain. 2. Freeze native/legacy parity fixtures for thought regions, aperture deviation and trajectories. 3. Specify detached imagery and ThoughtManifold graph lifecycle with explicit grounding cuts.
- **Guard:** fixtures use opt-in policy.
- **Acceptance:** `test_legacy_trace_fixture`, `test_empty_topic_unresolved`, `test_detached_trace_cannot_ground`; inventory states which Python functions become mechanical.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_thought_manifold_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** deleting callers based on names; moving legacy decisions to new Python helpers.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.E2.2 — Implement graph-native ThoughtManifold and shared projection

- **ID:** P4.E2.2
- **Tier:** T2
- **Goal:** Implement graph-native ThoughtManifold and shared projection.
- **Read first:** `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`; `tests/test_thought_manifold_migrated.py`; `scripts/gen_cognition_manifold_seed.py`.
- **Touch:** new `scripts/gen_thought_manifold_seed.py` + `seeds/thought_manifold.json`; `tests/test_thought_manifold_migrated.py`; `runners/dsl/src/future_manifold.rs` only for shared helper extraction.
- **Pattern to copy:** existing native projection_field with graph-native request scheduling.
- **Steps:** 1. Put topic/frame selection and trajectory refinement in rules. 2. Reuse native projection; extract only behavior-identical helpers if duplicated. 3. Apply residual and detached-evidence contracts to thought trajectories.
- **Guard:** `ThoughtManifoldPolicy.enabled`, default 0.
- **Acceptance:** E2.1 parity plus `test_same_projection_for_equivalent_inputs`, `test_detached_buffer_is_bounded`, `test_terminal_restore`; the current implementation additionally requires `test_graph_selects_initial_topic_from_in_tube_candidates`, `test_graph_controller_accounts_segment_and_steers_without_grounding`, `test_graph_controller_terminates_when_no_fresh_frontier_exists`, `test_aperture_grain_deviation_and_frontier_are_graph_owned`, and `test_unresolved_aperture_axis_is_dark_in_graph_projection`. The concept-region slice passes bounded-buffer and policy-restoration checks and opens/debits one same-epoch shared-budget request before each segment; denial, disabled budget and stale epoch refuse generation/accounting. The aperture route supplies raw codebook field values and global quantum/half-width metadata; graph rules apply Observer resolution/grain, clamp projection, mark hidden/zero coordinates dark, and own admitted-set assembly, deviation, width and frontier decisions. Both ThoughtManifold and cognition-manifold now call the same native `FutureManifoldProjection` term; equivalent numeric path inputs produce the same atomic shape snapshot in `test_same_projection_for_equivalent_inputs`. Static lexical/relation coordinate extraction remains in the shared Python signature extractor; broader registered projection outcomes remain open.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_thought_manifold_migrated.py tests/test_future_manifold_projection_native.py -q -p no:cacheprovider`.
- **Non-goals:** changing motor policy or behavior; introducing a new projection algorithm.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.E2.3 — Reduce the regulated thought adapter to I/O

- **ID:** P4.E2.3
- **Tier:** T2
- **Goal:** Reduce the regulated thought adapter to I/O.
- **Read first:** `domains/regulated_train_of_thought.py:66-200`; `tests/test_thought_manifold_migrated.py`; `COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md`.
- **Touch:** `domains/regulated_train_of_thought.py`; `tests/test_thought_manifold_migrated.py`.
- **Pattern to copy:** WorldAdapter ingest/tick/read-off pattern and E2 parity fixture.
- **Steps:** 1. Replace topic-region, deviation and next-step decisions with ingestion of ThoughtManifold requests. 2. Preserve public output shape from graph readout. 3. Remove obsolete decision helpers once all callers use the graph path; compare captured traces.
- **Guard:** explicit existing API call; automatic boot still unchanged.
- **Acceptance:** concept-region route passes `test_adapter_is_mechanical`, `test_public_output_parity`, and `test_graph_owns_next_step`; `test_graph_constructs_default_concept_region` proves default ancestry construction is graph-owned. Aperture route supplies raw codebook fields for native Observer projection and static coordinates through the shared mechanical extractor; deviation/frontier decisions are graph-owned. No Python recomputation of the migrated region or aperture control decisions.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_thought_manifold_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** rewriting unrelated imagination or motor adapters.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D1.1 — Specify the temporal escalation bridge

- **ID:** P4.D1.1
- **Tier:** T1
- **Goal:** Specify the temporal escalation bridge.
- **Read first:** `tests/test_time_infer_migrated.py:110-150`; `seeds/time_axis.json`; `seeds/extended_thinking.json`; `COGNITION_SIGNATURE_CONTRACT.md`.
- **Touch:** `COGNITION_SIGNATURE_CONTRACT.md`; `COGNITION_BUILD_P4_PREREG.md`; new `tests/test_temporal_escalation_migrated.py`.
- **Pattern to copy:** time_axis motion_seq ingestion and P3 funded-step executor.
- **Steps:** 1. Specify nonoverlapping owner/window identity, duplicate and out-of-order events, minimum witness length and bounded retention. 2. Escalate only an available real sequence after spatial ladders fail; preserve the source observation. 3. Freeze regular-sampling contract and refusal of irregular sampling; any later irregular-time solver is a separate version and preregistration.
- **Guard:** planned `TemporalEscalationPolicy.enabled=0`.
- **Acceptance:** planned `test_single_frame_cannot_escalate`, `test_irregular_time_refused`, `test_window_identity_prevents_duplicate_charge`; budget cannot be bypassed by direct bridge invocation.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_temporal_escalation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** claiming general irregular-stream inference; enabling optional quadratic GenInfer.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D1.2 — Assemble real frame windows and fund TimeInfer

- **ID:** P4.D1.2
- **Tier:** T2
- **Goal:** Assemble real frame windows and fund TimeInfer.
- **Read first:** `COGNITION_SIGNATURE_CONTRACT.md`; `tests/test_temporal_escalation_migrated.py`; `seeds/time_axis.json`; `scripts/gen_extended_thinking_seed.py`.
- **Touch:** new `scripts/gen_temporal_escalation_seed.py` + `seeds/temporal_escalation.json`; `tests/test_temporal_escalation_migrated.py`.
- **Pattern to copy:** TimeInfer exact verifier and P3 terminal restoration.
- **Steps:** 1. Assemble graph-linked regular windows mechanically ingested by adapters. 2. Mint one funded time request per eligible window; prevent time_axis from running that bridge window before approval. 3. Reverify held-out continuation, record time winner and expiry without turning prediction into observation.
- **Guard:** `TemporalEscalationPolicy.enabled`, default 0; no edits to time_axis core.
- **Acceptance:** `test_acceleration_infers_and_predicts`, `test_shuffled_stream_remains_unexplained`, `test_no_frames_no_time_rung`, `test_denied_request_does_not_infer`, `test_window_growth_bounded`.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_temporal_escalation_migrated.py tests/test_time_infer_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** synthesizing frames from a single signature; duplicated I4.2 latent-state induction.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.D1.3 — Ingest measured frame events and explicit window seals

- **ID:** P4.D1.3
- **Tier:** T2
- **Goal:** Connect the temporal graph assembler to a real mechanical ingestion boundary.
- **Read first:** P4.D1.1/D1.2; `substrate/world_adapter.py::WorldAdapter`; `tests/test_temporal_escalation_migrated.py`.
- **Touch:** this plan; `substrate/world_adapter.py`; `tests/test_temporal_escalation_migrated.py`.
- **Steps:** Add an explicit adapter call that records externally measured frame values with caller-supplied window, sequence index, timestamp, dimension identity and source epoch. Emit a close seal only when the caller explicitly closes the window and supplies its expected count. Make identical replay idempotent and reject conflicting event/seal identity. The adapter must not infer missing frames, timestamps, cadence, values or a close event.
- **Guard:** explicit ingestion call only; temporal policy and budget remain disabled unless independently enabled.
- **Acceptance:** replaying an identical event creates no duplicate; conflicting replay is rejected; an explicit seal reaches the existing D1.2 assembler, while absence of a seal produces no window or TimeInfer request.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_temporal_escalation_migrated.py -q -p no:cacheprovider`.
- **Non-goals:** enabling sensor hardware, manufacturing timestamps, or changing temporal rule semantics.
- **Done when:** the named ingestion and assembly acceptance passes; phase gate has no new failures; changes stay within Touch. Held-out evaluation remains owned by H1/H2.

## Held-out families and final tasks

D5's source-to-target transfer protocol is specified above. Add the following independent sections to the P4 preregistration:

| Item | Fixed draws and arms | Primary decision criteria |
|---|---|---|
| D2/D3 | 200 verified outcome streams, native versus frozen legacy oracle; 100 dimension/frame collision controls | Identical compatible legacy readbacks; zero incompatible merges or false grounded readings; all source epochs auditable |
| C5 | 200 hidden-residual/chosen-frame episodes and 100 forced-frame controls, adapters on/off | ≥20 percentage-point gain in resolving hidden residuals, family-wise Bonferroni-adjusted p<.01 across C5, E1/E2 and D1; zero forced-frame changes and zero unfunded probes in the adapter-on arm (adapter-off legacy behavior is measured as the control) |
| E1/E2 | 200 randomized model worlds, including feasible, infeasible and missing-model cases; GWM bridge on/off and supplied-path parity arm | ≥20 percentage-point gain in finding verified feasible candidates where models support them, family-wise Bonferroni-adjusted p<.01 across C5, E1/E2 and D1; zero falsely certified escapes; supplied-path residuals identical; refinement count and work reported |
| D1 | 200 regular orbit/order-N sequences plus 100 shuffled/no-frame/irregular controls, bridge on/off | ≥50 percentage-point continuation accuracy gain, family-wise Bonferroni-adjusted p<.01 across C5, E1/E2 and D1; zero exact claims on unsupported inputs; all steps funded |

No native/legacy parity arm may supply a target solution to the native agent. D2/D3 parity and invariants are conformance checks, not human capability measurements.

### P4.H1 — Freeze the Phase 4 evaluation machinery

- **ID:** P4.H1
- **Tier:** T1
- **Goal:** Freeze the Phase 4 evaluation machinery.
- **Read first:** `COGNITION_BUILD_P4_PREREG.md`; `evaluation/substrate_capability/extended_thinking_heldout_v1.py`; `evaluation/substrate_capability/extended_thinking_analysis_v1.py`; `evaluation/substrate_capability/cognition_p4_instances_v1.py`.
- **Touch:** new `evaluation/substrate_capability/cognition_p4_heldout_v1.py`; new `evaluation/substrate_capability/cognition_p4_analysis_v1.py`; `COGNITION_BUILD_P4_PREREG.md`.
- **Pattern to copy:** P3 frozen runner and mechanical hypothesis decisions.
- **Steps:** 1. Implement the registered families and paired arms using fixed run limits of 64 epochs and declared per-operation budgets; record timeouts as failures. 2. Freeze all artifacts and commit preregistration alone. 3. Reject runs without frozen hashes and verify deterministic development draws.
- **Guard:** evaluation only.
- **Acceptance:** runner/analysis development checks cover null, timeout and invariant violation; each original work item has a frozen decision rule.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_p4_instances.py -q -p no:cacheprovider`.
- **Non-goals:** held-out tuning; changing P3 evaluation or silently dropping failed items.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

The H1 runner and analysis must implement `--self-check` for development-only checks. After H3 profile integration, run these checks before committing the preregistration; after that standalone commit, set `COGNITION_PREREG_HASH` to its full hash and run the registered draw:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p4_heldout_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p4_analysis_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/cognition_p4_heldout_v1.py "$COGNITION_PREREG_HASH" 0 200
```

The runner writes `evaluation/reports/cognition_p4_heldout_v1_<hash8>_d0-200.json`; invoke `cognition_p4_analysis_v1.py` with that exact report path. It contains every registered subfamily, including separate ratio-bin draws where specified. Record the expanded commands and hashes in results. A self-check never uses registered held-out draw indices.

### P4.H2 — Run and report all Phase 4 evaluations

- **ID:** P4.H2
- **Tier:** T1
- **Goal:** Run and report all Phase 4 evaluations.
- **Read first:** `COGNITION_BUILD_P4_PREREG.md`; `evaluation/substrate_capability/cognition_p4_heldout_v1.py`; `evaluation/substrate_capability/cognition_p4_analysis_v1.py`.
- **Touch:** new `COGNITION_BUILD_P4_RESULTS.md`.
- **Pattern to copy:** P3 results with failed H4 retained.
- **Steps:** 1. Run runner as `<prereg_hash> 0 200`, with the registered 100-draw control subfamilies. 2. Analyze reports under evaluation/reports, leaving generated reports uncommitted. 3. Record every item, work counter, cost, gate status and claim limit.
- **Guard:** read-only evaluation against frozen artifacts.
- **Acceptance:** all registered hypotheses classified pass/fail/NOT_ESTABLISHED; Family-A P3 H4 remains failed; raw artifact paths and hashes recorded.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_p4_instances.py -q -p no:cacheprovider`.
- **Non-goals:** benchmark or human-level claims beyond the registered families.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.H3 — Integrate the guarded Phase 4 profile before evaluation freeze

- **ID:** P4.H3
- **Tier:** T2
- **Goal:** Integrate the guarded Phase 4 profile before evaluation freeze.
- **Read first:** `substrate/boot_profiles.py:769-796`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`; `COGNITION_BUILD_P4_PREREG.md`.
- **Touch:** `substrate/boot_profiles.py`; `seeds/cognition_on_params.json`; `tests/test_cognition_profile_integration.py`.
- **Pattern to copy:** P3 profile isolation and one funded solve integration.
- **Steps:** 1. Add the mechanism-tested guarded seed dependency closure to cognition-on. 2. Test real ingest → mint → recall → candidate verification → projection and temporal denial. 3. Record boot growth, default/conversation isolation and all phase gates in results via H2.
- **Guard:** cognition-on only; new policy defaults remain disabled elsewhere.
- **Acceptance:** `test_p4_profile_chain`, `test_p4_default_and_conversation_isolation`, `test_p4_budget_shared`; no new gate failures.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** promoting experimental seeds into CORE; treating a failed held-out capability as passed.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

### P4.H3.1 — Resolve the virtual `core` dependency in boot closure

- **ID:** P4.H3.1
- **Tier:** T1
- **Goal:** Allow cognition-on dependency closure to include legacy seeds that declare the built-in `core` root without looking for a nonexistent `seeds/core.json` manifest.
- **Read first:** `substrate/boot_core.py::boot_core`; `substrate/boot_core.py::load_seeds_into`; `seeds/observer_aperture.json`.
- **Touch:** this plan; `substrate/boot_core.py`; `tests/test_cognition_profile_integration.py`.
- **Steps:** Treat `core` as the already-present built-in substrate root during boot dependency resolution, matching the registry loader's behavior. Preserve all other manifest resolution and cycle checks.
- **Guard:** dependency resolution only; no rule or profile semantics change.
- **Acceptance:** cognition-on boot resolves `cognition_aperture` through `aperture_frame` and `observer_aperture`; default profile remains isolated.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** changing the seed registry or removing declared dependencies.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch.


### P4.H4 — Close Phase 4 documentation against actual evidence

- **ID:** P4.H4
- **Tier:** T3
- **Goal:** Close Phase 4 documentation against actual evidence.
- **Read first:** `COGNITION_BUILD_P4_RESULTS.md`; `COGNITION_BUILD_PLAN_20261010.md:1-25`; `COGNITION_CAPABILITY_ASSESSMENT_20261010.md:59-160`.
- **Touch:** `COGNITION_BUILD_PLAN_20261010.md`; `COGNITION_CAPABILITY_ASSESSMENT_20261010.md`; `COGNITION_BUILD_P4_RESULTS.md`.
- **Pattern to copy:** P3 parent status and assessment rows with explicit scope.
- **Steps:** 1. Update each delivered item with mechanism, held-out outcome, supported input class and commit hashes. 2. Retain failed hypotheses and inherited gate exceptions. 3. Assign remaining limitations and downstream prerequisite decisions; mark phase executed only after its implementation and reporting obligations are complete.
- **Guard:** documentation only.
- **Acceptance:** all original work items and carryovers have evidence-scoped status; no future task is described as passed; all links resolve to completed artifacts.
- **Verify cmd:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_cognition_profile_integration.py -q -p no:cacheprovider`.
- **Non-goals:** promoting a mechanism fixture to a human capability claim; erasing null results.
- **Done when:** named acceptance passes; phase gate has no new failures; changes stay within Touch. Spec tasks finish when their decisions and executable acceptance definitions are recorded; held-out evidence is produced at the phase evaluation task.

## Exit and handoff

Close implementation only with all focused tests and regression comparisons recorded, Rust provenance established, no uncontrolled seed drift, and all result sections written. Update the parent status and assessment through H4 below. Hand P5 the versioned signature, Observer-frame and manifold contracts, including null results and unsupported irregular sampling. If D4 has no measured transfer gain, P5 may still use verified local candidates but cannot assume cross-domain transfer. Quadratic GenInfer defaults and real-valued Pareto remain deferred unless a separately specified consumer requires them.
