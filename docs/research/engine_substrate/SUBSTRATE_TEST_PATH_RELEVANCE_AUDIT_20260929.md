# Current capability-map test-path relevance audit — 2026-09-29

This audit re-runs the lexical call-name triage against the current capability
map, then manually reviews the conversation/production and language links. The
triage is
[`substrate_test_reference_triage_20260929.json`](../../../evaluation/reports/substrate_test_reference_triage_20260929.json),
bound to the current map SHA-256 recorded in that report. It covers 26 rows and
65 functional-test links; 45 files contain a candidate direct callable-name
match and 20 do not. Neither result proves nor disproves runtime path coverage.
The focused native-runtime linked test batch was rerun on this tree with
`.venv/bin/pytest -q tests/test_cognitive_cycle_migrated.py
tests/test_cognitive_tasks_migrated.py tests/test_native_cycle_measurement.py`:
**59 passed**. That confirms the linked assertions pass; the table below
defines the narrower path-coverage claims each test supports.

| Capability row | Linked test | Classification | Evidence boundary |
|---|---|---|---|
| Native cognitive runtime and scheduling | [`test_cognitive_cycle_migrated.py`](../../../tests/test_cognitive_cycle_migrated.py) | Direct native-extension integration | Calls `agent.inner.run_cycle(...)` and checks cycle-plan boundaries, trace order, default-cycle behavior, and adapter wrapper routing. The Rust `execute` symbol is reached behind the extension API, not imported directly; it does not establish scheduler completeness for every cycle plan. |
| Native cognitive runtime and scheduling | [`test_cognitive_tasks_migrated.py`](../../../tests/test_cognitive_tasks_migrated.py) | Direct native-extension integration | Calls `agent.inner.run_cognitive_tasks(...)`; checks logical ordering, worker-count equivalence, runtime-capacity use, and unknown-kernel failure state. The native task runner is behind the extension boundary; workload coverage is bounded to the listed task kinds. |
| Native cognitive runtime and scheduling | [`test_native_cycle_measurement.py`](../../../tests/test_native_cycle_measurement.py) | Measurement-harness integration | Calls `measure_native_cycle`, which exercises native cycles and reads graph/runtime measurements; asserts replay, resource, and profile contracts. This is not direct coverage of every scheduler callable or an independent proof of full production scheduling behavior. |
| Conversation cognition, interlocutor models, production | [`test_conceptualizer.py`](../../../tests/test_conceptualizer.py) | Relevant partial integration | Exercises graph-composed intent/shape rules, communicative-goal mint/readback, concept scanning, audience-conditioned formulation, and now directly calls `conceptualize_reply()`; it does not call `select_utterance`, `materialize_deliberation`, or `ensure_self_model` directly, and does not prove universal live-turn release. |
| Conversation cognition, interlocutor models, production | [`test_context_model.py`](../../../tests/test_context_model.py) | Direct component integration | Calls context-model and interlocutor-model turn observers, checks open-ended context-dimension minting, residual salience, identity-context feed, and donkey-zero behavior. It does not exercise end-to-end conversation production/release. |
| Conversation cognition, interlocutor models, production | [`test_self_model.py`](../../../tests/test_self_model.py) | Direct component integration | Calls `ensure_self_model` and tests graph-resident rule summaries, refresh/idempotence, and truthful rule-query support. This is evidence for the self-model component, not audience design or the full production path. |
| Language understanding and lexical grounding | [`test_comprehend_text.py`](../../../tests/test_comprehend_text.py) | Direct functional test | Tests the audited text-comprehension entrypoint on typed parses/evidence; this is not by itself evidence for every alternate language-world or lexical-source path in the broad capability row. |
| Language understanding and lexical grounding | [`test_comprehend_instruction_migrated.py`](../../../tests/test_comprehend_instruction_migrated.py) | Direct functional integration | Exercises instruction comprehension in the live adapter/graph boundary and instruction evidence. Its assertions cover this route, not all lexical grounding or construction grammar. |
| Language understanding and lexical grounding | [`test_language.py`](../../../tests/test_language.py) | Adjacent grammar/lexical mechanism | Tests the separate `domains.language` lexical/composition/production DSL. It does not call the row's audited `comprehend_text`, `comprehend_know`, `ingest`, `apply_constructions`, or `decode_reference` entrypoints; retain only as adjacent faculty evidence, not direct path coverage. |
| Language understanding and lexical grounding | [`test_construction_migrated.py`](../../../tests/test_construction_migrated.py) | Irrelevant to this row's language path | Despite its filename, this is an Omniglot handwriting/construction-feature experiment over pen-world data. It does not test `construction_grammar` or the language-understanding path and should not count as a test link for this capability. |
| Graph-resident neural and operation-pipeline execution | [`test_fb_pipe.py`](../../../tests/test_fb_pipe.py) | Irrelevant link / explicit negative control | Exercises the Python shared-memory framebuffer writer (`scripts/fb_pipe.py`) and payload protocol. It does not call or reach Rust `pipeline_runtime`; the capability-map row itself labels this as non-evidence, so it must not count as operation-pipeline coverage. |

## Additional fixpoint-path audit (2026-09-29)

Two links for the rule-matching/fixpoint capability were inspected and rerun
with `.venv/bin/pytest -q tests/test_recursive_rule_closure_migrated.py
tests/test_rule_effect_mutation_audit_migrated.py`: **2 passed**.
`test_recursive_rule_closure_migrated.py` constructs `_native.Substrate`,
installs two native rules, calls the PyO3-exposed `Substrate.run_rules`, and
checks that a six-node path reaches all ten transitive edges and then reaches a
zero-work fixpoint. This directly covers recursive same-type edge visibility
for this fixture; it is not a proof of unrestricted termination or complete
access-set recall. `test_rule_effect_mutation_audit_migrated.py` similarly calls
native `run_rules` and checks counters for edge/node insert/delete, attribute
set, idempotent insert, and edge replacement effects. It verifies the
instrumented mutation arms on its fixtures, not semantic correctness or
scheduler completeness for all effects. These are direct extension-level
functional tests of the closure path, but they do not exercise the higher-level
`PySubstrate` adapter wrapper or establish a general bounded-closure theorem.

This is a scoped manual audit of fourteen links, not a 65-file audit. The other capability rows
and the remaining linked tests still need call-path review; same-name calls
remain candidates until the test setup, wrapper/Term dispatch, and relevant
assertions are inspected. No capability-map row is upgraded to fully audited
coverage from this report.

## Structural-width solver path audit (2026-09-29)

The map-linked `tests/test_solver_decompose_adapter.py` was also inspected and
its success/refusal cases rerun: **2 passed** with
`.venv/bin/pytest -q tests/test_solver_decompose_adapter.py::test_success_real_statements_race_and_decompose
tests/test_solver_decompose_adapter.py::test_honest_wall_bound_too_tight`.
The success fixture sends three authored deduction statements through
`mint_solve_decompose_goal_from_text`, pumps the graph resolver rules, then
reads back the selected `solve_decompose` result, candidate widths, and bags.
The refusal fixture confirms an over-tight width bound ends in the native
`walled` Goal state and no decomposition attempt. This is direct integration
evidence for those solver-dispatch/decompose paths on the synthetic deduction
family; it does not establish natural task-width prevalence, automatic frame
discovery, or partitioned execution. The manual audit now covers **14** linked
test files out of 65; no row-wide test-coverage claim follows.

## Structural-width solver dispatch path audit (2026-09-29)

The capability-map-linked `tests/test_solver_dispatch_migrated.py` case
`test_solve_decompose_chains_from_solve_deduction` was inspected and rerun:
**1 passed** with
`.venv/bin/pytest -q tests/test_solver_dispatch_migrated.py::test_solve_decompose_chains_from_solve_deduction`.
It mints and resolves three real deduction Goals through the live resolver
rule loop, projects two candidate coupling graphs from their schema nodes,
checks their min-fill widths differ, then dispatches a real `solve_decompose`
Goal and asserts the sparse projection wins under bound 1. The resolver calls
`problem_decomposition.decompose_problem`; this is direct bounded integration
evidence for that authored deduction chain, candidate race, and dispatch path.
It does not show natural task-frame discovery, independent correctness of
candidate semantics, broad workload tractability, or general partitioned
execution. This adds one reviewed linked file: **15/65**; Stage 0 remains open.

## Rule dependency and settlement path audit (2026-09-29)

The capability-map-linked `tests/test_per_area_settlement_migrated.py` was
reviewed and rerun: **17 passed** with
`.venv/bin/pytest -q tests/test_per_area_settlement_migrated.py`. It directly
calls the exposed native `run_rules_settle` and global `run_rules` entrypoints.
The fixtures pin default-off separation, exact graph parity between unbounded
area settlement and global fixpoint on synthetic and selected vision workloads,
finite-budget residual carry/convergence, divergence when residuals are
dropped, and zero work in quiet areas. This verifies those mechanism paths and
fixtures; it does not establish scheduler completeness, arbitrary-input parity,
or production adoption (the test explicitly notes no committed caller uses
`run_rules_settle`). The scoped Stage 0 manual review now covers **16/65**
linked test files; the full audit remains open.

## Episodic authored-rule path audit (2026-09-29)

The map-linked `tests/test_episodic_working_memory_migrated.py` was inspected
and rerun after adding an exact-cue `IndexJoinHint`: **16 passed**. The fixture
loads `episodic_working_memory_core`, mints typed `EpisodicEvent` records, and
uses the live `WorldAdapter.tick()` path to exercise graph-authored binding,
provenance admission/refusal, cue-overlap marking, bounded uncertain retrieval,
replay/semantic support, and working-memory gates. The new overlap case checks
that the cue attribute index is declared, same-cue Episodes remain separately
identified and confidence-capped, while distinct cues do not create false
overlap. This is direct evidence for those authored-rule integration paths,
not for the separate Rust `MemoryFaculty` callable family or broad natural
memory utility. The Stage 0 manual review now covers **17/65** linked test
files.

### Current-seed rerun (2026-09-29)

After seed version 1.1.3 split typed working-memory and non-empty-cue
candidate edges, `tests/test_episodic_working_memory_migrated.py` passes
**18/18** and the combined `test_join_index_migrated.py` plus episodic suite
passes **23/23**. Added coverage confirms legacy Episodes with a cue string
stay outside the working-memory collision population and unkeyed working-memory
Episodes are retained but excluded from overlap candidates. The audit remains
limited to this one capability-map link; Stage 0 stays at **17/65** linked
test files.

## Vision primitive bridge path audit (2026-09-29)

The map-linked `tests/test_vision_kernels.py` was inspected and rerun:
**19 passed** with `.venv/bin/pytest -q tests/test_vision_kernels.py`. Its
fixtures exercise the Python `substrate_rs.vision` bridge against the native
graph for image/kernel serialization, DSL-visible kernel attributes, Gaussian
and DoG properties, Sobel/Gabor responses, kernel-bank composition,
`produced_by`/`from_input` provenance, pipeline chaining, pooling/thresholding,
and graph queries over kernel nodes. These are direct integration checks for
this kernel-oriented vision route. They do not cover the separate
`WorldAdapter` upload/update paths, temporal difference/foveation, GPU,
framebuffer, ink-topology, or space-quantization paths listed in the broader
capability row; nor do they establish task-level perception quality. The
scoped Stage 0 manual path review now covers **19/65** linked test files.

## Vision graph lifecycle bridge path audit (2026-09-29)

The map-linked `tests/test_curious_agent_vision_graph_migrated.py` was
inspected and rerun: **1 passed, 7 skipped**. The passing no-engagement case
confirms that `WorldAdapter` does not construct vision state without a frame.
The seven frame-dependent integration cases were skipped because optional
`cv2` is unavailable in this environment, so this run provides no evidence for
their graph-resident receptor construction, introspection, attention,
projection, or persistence behavior. This path is distinct from the kernel
bridge audit above, and neither implies task-level perception quality. The
seven skipped checks remain unverified.

## Graph-authored vision change rung audit (2026-09-29)

The map-linked `tests/test_vision_change_migrated.py` was inspected and rerun:
**5 passed**. This graph-authored workload verifies the singleton
`ChangeParams` contract, exact default median-split baseline, regime-sensitive
change detection, sustained-channel activity under a stable spatial edge, and
independent rule phase keys. It is direct evidence for this selected
vision-change seed path, not for the Rust `temporal_diff` primitive listed in
the capability row, other vision primitives, or general perception quality.
The scoped Stage 0 manual linked-test review now covers **20/65** test files.

## Explicit agent-tool capability path audit (2026-09-29)

The map-linked `tests/test_agent_tools.py` was inspected and rerun:
**20 passed**. Its assertions exercise direct `ToolBox` read/write/command
methods (including the current unrestricted read and `shell=True` command
semantics), frame/microtheory installation, runtime-capability registration,
Action-node recording, and two `answer_within` frame-routing cases. This is
evidence for the explicitly installed demo tool path only; it is not a dynamic
host-I/O route census, workspace read-boundary proof, P0-A containment result,
or evidence that default boot registers these capabilities. The manual linked
test-path review now covers **21/65** files.

## Live conversation/reflective-release path audit (2026-09-29)

The capability-map-linked `tests/test_conversation_loop.py` was manually
inspected and initially rerun against the source-current native extension:
**13 passed, 1 failed**. Its positive assertions exercise the live
`WorldAdapter.converse()` route for explicit diagnostic failures, authorized
non-turn silence, a self-organization answer, action/self-report, scene
description, repair questions, and donkey-zero behavior. The failing
`test_world_question_still_answers` reaches its assertions that the same turn
selected `self_model_rule` and minted a linked planned outbound answer, but
fails on the released-receipt assertion. Runtime inspection showed the
same-turn `ProductionGateReceipt` had
`parse_back_mode=conversation_topic_unresolved_graph`; there was no released
receipt with the expected
`conversation_reflective_self_model_rule_graph` mode. Thus the
selected/planned reflective answer is not the released answer in this run.
This exposed a branch-order defect: unresolved-topic clarification ran before
the selected evidence-backed reflective-answer gate. Moving the reflective
release ahead of that fallback fixed the receipt contract; the full file now
passes **14/14**, including the previously failing test. This is direct
evidence for this selected conversation release path only; it does not prove
all answer classes route through their strongest release authority. It is not
attributed to the literal index optimization, which only narrows the two
steering rules. Manual Stage 0 linked-test review remains **22/65** files; this
count records inspection, not success over every linked capability path.

## Context-model and interlocutor feed path audit (2026-09-29)

The map-linked `tests/test_context_model.py` was inspected and rerun:
**5 passed in 85.54s**. It directly exercises `context_model.observe_turn`,
open-ended dimension mint/redecode, residual salience, the
`context_model.interlocutor_context` feed into identity attribution, and the
collapse-plug route. Its fixtures also check a zero-call self-teacher
counter. This is component-level conversational integration evidence; it does
not test the `WorldAdapter.converse()` production/release route, all context
sources, or functional substrate completeness. Manual Stage 0 linked-test
review now covers **23/65** files; the remaining paths and broader Stage 0
acceptance remain open.

## Audience-conditioned conceptualizer path audit (2026-09-29)

The map-linked `tests/test_conceptualizer.py` was inspected and rerun after
adding a regression for the public `conceptualize_reply()` wrapper:
**12 passed**. It covers graph-composed `CommunicativeIntent` formation,
force/perlocutionary goal readback, residual-derived focus/ground, audience-
conditioned utterance selection, composer-authored rule installation, and
source guards against Python-side decisions or a parallel rule engine. The
new direct-entrypoint case verifies native formation and a released
`Committed` readback. Separately, the adjacent
`tests/test_conceptualized_converse.py` live-route suite was rerun in the same
batch; together the two files pass **20/20** and cover selected answer,
instruction, ask-back, audience-design, monitor, and diagnostic-error cases.
These selected routes still do not prove universal live-turn release or all
production-gate classes. Manual Stage 0
linked-test review now covers **24/65** files; broader Stage 0 acceptance
remains open.

## Language lexical/composition path audit (2026-09-29)

The map-linked `tests/test_language.py` was inspected and rerun: **13 passed**.
Its lexical cases exercise the native character-chain recognizer, longest-form
selection, boundaries, number folding, and category readback; composition cases
exercise graph-authored marked/infix/recursive Merge, vocabulary-independent
runtime signs, prosodic force, and production/comprehension round trips through
the same grammar. This is direct evidence for the selected lexical and
compositional language path. It does not establish phrase-level language
coverage, graph-resident lexicon acquisition, broad multilingual production,
or a complete substrate capability row. Manual Stage 0 linked-test review now
covers **25/65** files; broader Stage 0 acceptance remains open.

## Program-synthesis and native enumerator path audit (2026-10-03)

Four previously unreviewed P4-linked files were inspected against their
current implementation paths. This is a source/assertion audit only; no tests
were run for this entry.

* `tests/test_synth_enumerate_migrated.py` calls the native
  `SynthEnumerate` Term directly through `_inner.evaluate`, compares four
  authored numeric specifications with `domains.generator.synthesize`, and
  checks budget/saturation honesty, reflected Term round-trip, determinism,
  string/list operators, exclusions, and typed list behavior. This is direct
  evidence for the native enumerator and its evaluator contract on those
  finite fixtures. It does not establish request routing, broad hypothesis
  recovery, or scaling beyond those specs.
* `tests/test_program_synthesis_migrated.py` exercises the P4-B adapter path:
  seed loading, request ingestion, rule pumping, goal readback, accepted
  reflected IR execution through `ProgEval`, lattice ordering, CEGIS,
  rung/budget behavior, honest gaps, and source guards against Python-side
  decisions. It is substantial integration coverage of authored synthesis
  routes. Its narrow request fixtures and dedicated battery mean it does not
  establish general-purpose program induction or representative task
  performance.
* `tests/test_prog_synthesis_battery_migrated.py` primarily re-derives
  aggregates and confidence intervals from the frozen battery artifact,
  checks task-set and determinism metadata, and guards continuity against the
  frozen C-BATTERY. A small set of pinned cases is re-run through the driver.
  This is artifact integrity plus limited live-replay evidence; the many
  artifact rows are not all live executions in this test path.
* `tests/test_program_synthesis_grounding_migrated.py` covers graph-resident
  quantity lexeme grounding, operator-shape selection for threshold
  classifiers, arbitrary integer grounding, and execution of accepted
  reflected programs on held-out values. This is direct evidence for the
  narrow quantity/shape-to-enumerator bridge, not open-vocabulary language
  understanding or autonomous primitive invention.

Implementation landmarks inspected include `domains/prog_synthesis.py`
(`ensure_program_synthesis`, `ingest_spec`, the `_wire_rows` serializer,
`run_enumerate`, `pump`, and `read_goal`) and the native Term definitions and
dispatch in `runners/dsl/src/term.rs` / `runners/dsl/src/synth_enumerate.rs`.
These test links therefore reach live native and adapter code, but the audit
does not claim every synthesis capability-map subpath is covered. The manual
Stage 0 manual review now covers **29/65 capability-to-test link entries**;
the triage artifact contains 65 links across 61 unique Python files, so the
remaining 36 entries are not necessarily 36 distinct files. Stage 0 is open.

## Native cognitive scheduling and worker path audit (2026-10-03)

Three linked test entries for `native_cognitive_runtime_and_scheduling` were
reviewed against their current source paths. The triage SHA-256 values match
all three current test files. This was source/assertion inspection; no tests
were run.

* `tests/test_cognitive_cycle_migrated.py` covers native cycle phase ordering,
  adapter delegation to cycle plans, fail-closed unknown plans, dual-process
  soft-rule gating, background service of requested work, and graph-authored
  request admission/parallel-context behavior. It provides integration
  evidence for these scheduling boundaries and authored fixtures. It does not
  establish scheduler fairness, deadline guarantees, or arbitrary concurrent
  workload behavior.
* `tests/test_cognitive_tasks_migrated.py` calls the exposed native
  `run_cognitive_tasks` path on graph-requested tasks and checks logical-order
  result folding, worker-count result stability, runtime capacity selection,
  unknown-kernel failure as graph state, explicit area metadata, dependency
  readiness, area feedback, area-local clocking, mutex release, and a CPU
  workload speed comparison. This covers the task executor contract on those
  kernels/fixtures. It does not establish speedup for small or heterogeneous
  tasks, fairness under sustained load, or broad cognitive task quality.
* `tests/test_native_cycle_measurement.py` is a wide integration/measurement
  suite. It checks bounded replay, graph and RSS-growth limits, native trace
  authority, several authored synthetic profiles, and many receipt-backed
  cognitive delegations. Those checks support selected cycle and delegation
  paths, with synthetic bounded workloads; they do not make the timing probes
  a representative production workload or establish that all Python cognitive
  branches have migrated. Its source audit explicitly retains migration
  debt.

The direct native boundary is exposed in `runners/dsl/src/py.rs` as
`run_cognitive_tasks` and implemented in `runners/dsl/src/cognitive_tasks.rs`;
the cycle wrapper is exercised through `WorldAdapter`. Current test hashes
match the triage capture for these entries. The Stage 0 manual review now
covers **32/65 capability-to-test link entries**. The full triage contains 65
links across 61 unique files; repeated links can refer to one file. Stage 0
remains open, and these cases do not prove real-time guarantees or broad
capability quality.

## Typed-graph state, rewrite, admissibility, and paging path audit (2026-10-03)

Three linked test entries for `typed_graph_node_edge_state` were inspected.
Their current SHA-256 values match the 2026-09-29 triage capture. No tests
were run for this review.

* `tests/test_graph_rewrite.py` builds nodes and edges through `TypedGraph`,
  whose current storage is `substrate_rs.Substrate`; `_insert_edge` delegates
  to the native unchecked edge mutation. Assertions cover graph-resident rule
  data, word-reduction and matrix-operation examples, and graph-Term-driven
  coloring search. However, `domains.graph_rewrite.run` and
  `search_count` provide Python-side rule/search orchestration. This is useful
  evidence for Rust-backed graph state plus selected Python-authored
  constructive procedures, not proof that general rule matching, rewriting,
  or DFS is implemented natively.
* `tests/test_node_admissibility_graphs.py` exercises graph-Term evaluation
  against Rust-backed substrate nodes and attributes. It checks the fixed
  precision-to-weight map, convex interpolation to a flat reference,
  abstention behavior, all-admissible parity, and a source audit excluding
  fitting/gradient machinery. The direct `add_node`/`set_attr` calls are setup;
  the capability evidence concerns the evaluated scoring Terms and selected
  contrast fixtures, not graph mutation performance or general learning.
* `tests/test_graph_virtual_memory.py` exercises `GraphVirtualMemory`'s
  page-out/page-in policy with an mmap key/value slab, canonical byte identity,
  resident-node limits, and retention of kernel nodes. This is a meaningful
  bounded paging integration path, but policy/orchestration is in Python over
  the substrate graph and `reference_slab`; it does not directly validate the
  separate Rust `MemoryFaculty`, process-wide RSS ceilings, crash recovery, or
  large-corpus throughput.

The current binding exposes native graph mutation in `runners/dsl/src/py.rs`
and the backing store in `runners/dsl/src/substrate.rs`; `substrate/graph.py`
retains the compatibility API. The paging path is implemented in
`domains/graph_virtual_memory.py`, backed by `domains/reference_slab.py`.
These distinctions leave native rule execution, mutation cost under realistic
loads, and the Rust memory faculty as separate audit/evaluation items. Stage 0
manual review now covers **35/65 capability-to-test link entries** (65 links
across 61 unique files); 30 entries remain, with duplicates across capability
rows possible. Stage 0 remains open.

## CAN exact/approximate inference and learning path audit (2026-10-03)

The three triage links for `exact_approximate_inference_and_optimization`
were inspected. Their test-file hashes match the captured triage hashes. The
resolver path in `tests/test_solver_dispatch_migrated.py` had prior review for
a separate decomposition case; this entry records its CAN inference assertions.
No tests were run.

* `tests/test_solver_dispatch_migrated.py` builds Bigville resident CAN
  networks and dispatches relaxation, exact junction-tree MAP, and loopy BP
  through graph-resident Goal/Resolver rules. It checks resolver selection,
  resolved/walled states, reported energy/treewidth/convergence fields, and
  explicit treewidth-bound behavior including zero and refusal when a real
  network exceeds the bound. This supports those adapter and honest-refusal
  paths on authored resident networks. The CAN assertions here do not compare
  every returned state/energy against an independent exhaustive oracle, nor
  measure scaling over broad topology distributions.
* `tests/test_solver_can_adapter.py` exercises graph/text adaptation that
  adds genuinely new causal edges from selected property sentences, then
  routes the changed network through exact, relaxation, or BP resolvers. It
  also checks no-evidence and malformed-input declines, preservation of
  static discrete mode, and honest partial grounding. This is a useful
  end-to-end bridge from selected language input to solver dispatch, but the
  evidence is limited to a small authored vocabulary, target concepts, and
  network family.
* `tests/test_can_native_reimplementation.py` exercises graph-authored
  discrete asynchronous CAN updates, ShapeDecode basin recognition, native
  frustration readback, and recurrence-gated Hebbian edge/evidence updates.
  Its convergence panel uses 20 seeded draws of complete 8-node networks for
  2-state/3-state and coarse/fine couplings. That is meaningful repeated
  evidence for the finite mechanism and seed rules; the 3-state convergence
  is explicitly empirical, not a general proof. The removed continuous-sync
  comparison is not covered. The basin and learning assertions do not measure
  exact-vs-approximate MAP accuracy.

The path crosses graph-authored dispatch in `seeds/solver_dispatch.json`,
Python resolver adapters in `domains/solver_dispatch.py`, exact junction-tree
code in `domains/can_junction_tree.py`, loopy BP in `domains/can_native_bp.py`,
and native Rule/Term support including CAN energy/frustration operations in
`runners/dsl/src/can_ops.rs`. Thus the current exact and BP algorithms are
Python implementations operating on the Rust-backed graph and native Term
semantics; the graph-authored discrete update is a distinct native rule path.
Keep these implementations separate in cost claims. No proof of polynomial
inference follows: exact inference remains width-bounded, while BP quality and
cost need independent topology/ground-truth panels. Stage 0 manual review now
covers **38/65 capability-to-test link entries** (65 links across 61 unique
files); 27 entries remain. Stage 0 is open.

## Learning and primitive-proposal lifecycle path audit (2026-10-03)

Three links for `learning_self_modification_proposals` were inspected. Their
current file hashes match the triage capture; this is source/assertion review,
not a test rerun.

* `tests/test_learner.py` exercises `GammaLearner` on a generated Conway
  corpus: observation updates, heldout accuracy and table recovery, conversion
  of the learned grammar into a Substrate, and edit logging. The substrate
  reproduces 20 oracle-checked generations on one independent board. This is
  evidence for a narrow tabular transition learner and execution of its
  acquired grammar; the learner is Python, the task is a fixed cellular
  automaton family, and the tests do not show autonomous substrate rule
  acquisition from unrestricted tasks.
* `tests/test_vision_growth_migrated.py` checks calibration of an orientation
  measure against ideal Gabor/DoG and random kernels, then graph-rule minting
  and Oja updates from BSDS natural-image patches, bounds/fixpoint behavior,
  and that growth decisions reside in seed Terms. The natural-image cases
  require the optional BSDS corpus and skip when it is absent or too small;
  without that data they provide no execution evidence for image-driven
  growth. Even with the corpus, this is one authored kernel-growth rule and
  measure, not general perception or unconstrained new-primitive learning.
* `tests/test_proposal_install.py` covers the existing-primitive
  `ReachableFrom` no-op path live, refuses failed/lossy/tampered proposals,
  verifies a denylist refusal under mocked rendering/revalidation, and checks
  proposal display queries. It provides guardrail and persistence-integrity
  evidence, not an end-to-end new primitive compile/install result: the
  nontrivial install branches are mocked or refused, and the live path avoids
  cargo entirely because the primitive is already present.

The relevant boundaries are `substrate/learner.py` for the Python GammaLearner,
`seeds/vision_growth.json` plus native Term evaluation for kernel growth, and
`domains/proposal_install.py` / `domains/self_extend_rust.py` for host-side
proposal validation and installation. Taken together, these tests cover
narrow supervised induction, one graph-authored parameter-learning mechanism,
and proposal guardrails. They do not establish a closed substrate loop that
selects a capability gap, invents a primitive, validates it on heldout tasks,
and safely installs/adopts it. Stage 0 manual review now covers **41/65
capability-to-test link entries** (65 links across 61 unique files); 24 entries
remain. Stage 0 remains open.

## Shape decoding, dimension inference, and multi-orbit learning path audit (2026-10-03)

Three links for `shape_decode_recognition_transform_dimension_inference` were
reviewed; current test-file hashes match the triage capture. No tests were run.

* `tests/test_dimension_inference_migrated.py` exercises the seeded Occam
  ladder through native `ShapeDecode`, `TransformDecode`, and `DimInfer` Terms
  plus `run_rules`: exact held-shape transforms, finite generator recognition
  (rotation/reflection/scale/modular cycle), length-two composition, residual
  shifts/substitutions, zero-mint recognition, genuine residual minting, and
  re-decode/dedup termination. Most cases author the decoded Observation and
  residual directly to isolate rule behavior; one case enters through
  `induce_concern`. This is strong mechanism evidence for the finite seeded
  generator catalogue on small authored relation sets, not evidence that the
  system discovers arbitrary dimensions or generalizes across natural tasks.
* `tests/test_two_novel_orbits_gate_migrated.py` fixes a real coverage gap by
  presenting two distinct linear orbits, a composition, and repeats to one
  graph; it checks no silent stall, distinct generator/latent-dimension
  records, no repeat mint, and generous wall/epoch bounds. A second grain
  checks three structurally different shapes through graph-authored vision
  quantization. This verifies selected multi-item codebook growth and
  dedup/termination behavior. The linear generator route is explicitly
  opt-in (`gen_infer_enabled`), the orbit set is hand-authored, and wall bounds
  are regression guards rather than a scaling study.
* `tests/test_meta_shape_arity_migrated.py` covers a separate higher-level
  shape grain: a held MetaShape covers an observation with an extra relation,
  while disjoint and strict-subset controls remain residual; a genuinely new
  predicate set still mints; `Covers` retains exact-arity semantics while
  `CoversOpen` is directional; and capability-key encoding stays injective
  and backward-compatible on measured keys. This is evidence for the
  open-arity relation-set matcher and the MetaShape ladder on authored records,
  not a general concept learner or arbitrary compositional frame induction.

Implementation landmarks are `runners/dsl/src/shape_decode.rs`
(`eval_shape_decode`, `eval_dim_infer`, `eval_gen_infer`,
`eval_meta_shape_mint`), `runners/dsl/src/term.rs` (`CoversOpen`),
`seeds/shape_decode_loop.json`, `seeds/meta_shape_growth.json`, and the
mechanical adapter `domains/meta_shape.py`. The path contains native search
Terms and graph-authored rung transitions, but its hypothesis menu and test
shapes are supplied. Stage 0 manual review now covers **44/65
capability-to-test link entries** (65 links across 61 unique files); 21 entries
remain. Stage 0 remains open.

## Language comprehension and instruction grounding path audit (2026-10-03)

The four `language_understanding_and_lexical_grounding` links were adjudicated.
Three current hashes match the triage capture; `tests/test_comprehend_instruction_migrated.py`
does not: the captured digest is
`d3ace66e109cfec2b32a49dfbc409b62e5e1cd06e7a451b4a8ba46aea5e30624`, while the
current working-tree digest is
`7be339b08818b7e8d967b875597479b5a7d2e65487da0c1cefbf53f1ebb34862`.
Inspection shows local additions to production-receipt assertions, comma-headed
instruction parsing, and grounded/deferred instruction cases. They are included
in the path review but remain unverified by a test run.

* `tests/test_comprehend_text.py` exercises a general Python comprehension
  front end against examples missed by a fixed question table, with direct
  frame/intent assertions and selected `answer_question`/`converse` routes.
  It checks question/instruction/statement discrimination, typed unknown-token
  gaps and honest frontiers, plus specific reflexive/self-model routing. This
  is useful end-to-end evidence for selected English forms, but parsing,
  intent classification, and dispatch are substantially Python-side, and the
  fixtures center on questions about the agent's own held state. It is not a
  broad language benchmark or evidence for general semantic understanding.
* `tests/test_comprehend_instruction_migrated.py` spans a Python-comprehended
  instruction written to Message graph data and graph-authored rules that mint
  read/world-action/self-improvement Goals or honest replies. It also pins
  explicit Python fallback for self-report, uncertainty clarification, and a
  safety gate that a SelfConcern stays `noted` instead of arming an experiment
  loop. This is evidence for those routes and authority boundaries; the
  grammar/leading-head parse remains adapter-side and only selected verbs and
  referents are covered. The additional current-tree receipt checks have not
  been run.
* `tests/test_construction_migrated.py` is a lexical false positive for this
  capability link. It tests DigiLeTs handwriting filename/feature extraction,
  Fisher statistics, a nearest-fact classifier, writer-split bookkeeping, and
  seed integrity. It does not exercise text comprehension or lexical
  grounding. Real-data cases are skipped when the separate DigiLeTs corpus is
  absent; synthetic classifier controls are not language evidence.
* `tests/test_language.py` is cross-linked here and was already inspected in
  the earlier lexical/composition audit above. Its evidence is for native
  character-chain recognition and graph-authored grammar composition on the
  listed fixture forms; the limits recorded there still apply.

Path landmarks include `domains/comprehend_text.py` for parsing/classification,
`substrate/world_adapter.py` for mechanical graph projection and selected
Python fallback routing, and `seeds/comprehend_instruction.json` for the
selected graph-rule decisions. The crosswalk's AST name candidates do not
separate these authority layers, and one of its four files is unrelated to the
capability. Stage 0 manual review now covers **48/65 capability-to-test link
entries** (65 links across 61 unique files); 17 entries remain. One reviewed
link's source hash is stale in the 2026-09-29 triage artifact, so a refreshed
current-source inventory is needed before treating its manifest as source
current. Stage 0 remains open.

## Current-source crosswalk refresh (2026-10-03)

The capability map has since changed: the current map has 28 capability rows
and 72 test-link entries across 67 unique paths. The 2026-09-29 source triage
captured 26 rows and 65 test-link entries across 61 files. Its old **48/65**
manual-review counter is therefore historical and cannot be treated as a
current completion fraction; the newly added capability links and altered
evidence catalogs need adjudication before a current denominator can be
claimed.

The static AST crosswalk was rerun against the current map and source tree. The
dated output is
`evaluation/reports/substrate_capability_test_relevance_audit_20261003.json`
(capability-map SHA-256
`6508902b0b548b2fe0d1d408ed5fbc82812278b4583d6c6b8ce2178aa2452891`, runner
SHA-256 `9e69d14ef5322b37377dcec9d999f8ac248802805207639189116a0120f9c5c8`).
It records 28 rows, 72 linked-test entries, 19 rows with candidate callable
name matches (17 with matches lexically inside assert-bearing test functions),
five rows with only generic-name hits, and four rows with no linked source
symbol call. There are 200 candidate call sites inside assert-bearing test
functions and 214 lexically reachable candidate call sites overall. These
are prioritization signals only: AST name matches do not establish that the
production path ran or that an assertion checks its result. Rust test-tail
name mentions are similarly lexical evidence. No tests were run.

The runner now accepts `--output` and records a SHA-256 for every linked test
and linked Rust source file. Reproduction command:
`python3 scripts/audit_substrate_capability_test_relevance.py --output evaluation/reports/substrate_capability_test_relevance_audit_20261003.json`.

Two capability rows are new relative to the old triage:
`counterfactual_imagination_and_thoughtexperiment_harness` and
`production_visual_image_ingestion_and_frame_scoped_settling`. The refreshed
crosswalk is now the appropriate index for selecting remaining manual reviews.
Prioritize those new rows and rows with no candidate source calls, then inspect
the strongest candidate paths and retain the boundary between adapter,
substrate, and test-harness behavior. Do not publish a new manual-review
fraction until the reviewed links have been reconciled against all 72 current
entries.

## Thoughtexperiment and counterfactual test-path review (2026-10-03)

The current map links `tests/test_imagination.py` and
`tests/test_self_correct_cognition.py` to the new
`counterfactual_imagination_and_thoughtexperiment_harness` capability row.
Their current SHA-256 values are respectively
`ddbff84bd8e69c9f0add17e061db151318aec9ab1f523d02a42dc7695ec322b2` and
`1d3db11efabc4f09f5e27bb5692ba452ea02082887835b6ca33f4e141340c0ba`.

* `tests/test_imagination.py` gives direct assertion coverage for detached
  counterfactual runs, grounding cuts, survivor/discarded residuals,
  no-writeback before approval, gated commit, focus-limited snapshots, and
  detached-state isolation. Its fixture authors small rules and hypotheses.
  The implementation documented in `domains/imagination.py` snapshots via
  graph serialization into a new substrate and copies the native rule store;
  these tests therefore establish reversible full-copy counterfactual
  mechanics, not the newer Rust CoW fork path or large-graph speedup.
* `tests/test_self_correct_cognition.py` exercises graph-authored attempt
  gating and candidate ranking, including skip behavior and an end-to-end
  ticks-driven path. The host dispatcher and correction machinery remain
  Python calls, and candidate rule variants in the ranking controls are
  supplied by the fixture. It supports a narrow authored self-correction
  policy path, not substrate-selected gap discovery, open-ended candidate
  invention, blind validation, or autonomous adoption.

The current CoW, delta-return, candidate-generation, and adoption evidence is
in the separately source-locked thoughtexperiment experiments indexed by the
capability map and measurement plan. It should not be attributed to these two
legacy test files. No tests were run during this review. This adjudicates the
two linked test paths for this capability, but does not close the refreshed
Stage 0 inventory; its denominator is 72 link entries and the previously
reported 48/65 figure is historical.

## Planning and action-selection linked-path review (2026-10-03)

The current `planning_and_action_selection` row links two paths. Their current
SHA-256 values are `13998fbf58c6712d24a0797719309aedaa841c4a48a16026840be9e8c6b9bad8`
for `tests/test_operational_planning.py` and
`c1a079f5c0ff046ae51fc1225e7c56eff76cf31107732c752371b9a0c307e713` for
`tests/test_arc_ls20_mapnav_migrated.py`.

* `tests/test_operational_planning.py` asserts selected instruction-to-plan
  bindings, graph-resident plan structure, nested foreach/if execution, and a
  short end-to-end bulk-load/measure/gap-perception workflow. It also checks
  that capability choice is a graph `Argmax` over `OperationalCapability`
  nodes. The evidence is meaningful for this finite seeded operational
  vocabulary and these instruction forms. `domains/operational_planning.py`
  still performs instruction segmentation and plan construction in Python,
  evaluates graph condition Terms through its Python executor, and dispatches
  work through a Python name-to-function registry; the substrate provides the
  graph representation and selected Argmax decision. The tested load is
  capped at two articles, so it is not a scaling result.
* `tests/test_arc_ls20_mapnav_migrated.py` checks wall-layout success
  separation, open-layout parity, retained fog frontiers, source-shape
  constraints, and a default-off control. `worlds/arc_ls20_scenario.py`
  stamps the belief into graph nodes, runs native graph rules for waypoint
  decisions, and calls the shared `quanta_flood_step` whose qf rules select
  the route action. Python constructs scenarios, advances the episode, applies
  collision/world effects, and the measurement script supplies the comparisons
  and confidence intervals. The `source_audit` gate is a string/source scan,
  while route outcomes are the substantive behavioral evidence. This is
  bounded grid-navigation evidence, not general planning or task-derived
  decomposition evidence.

The capability row also links native P2/P4 and spatial-source landmarks that
are not directly exercised merely by these two test imports. Attribute each
assertion to the path it actually reaches; do not treat the broad row as one
end-to-end substrate planner. No tests were run during this review. This is a
path-level audit only; reconciliation of all manually reviewed links against
the current 72-entry capability map remains open.

## Native Enigma admissibility path review (2026-10-03)

The current map links `tests/test_enigma_upgrade.py` to
`graph_resident_hypothesis_admissibility`. The file's current SHA-256 is
`e566c7356a00da2bb3d09c1167f7b11ecd538ed40364464e7a2bbc751021e572`.
Although the refreshed AST crosswalk reports no call to the linked Rust
symbols, this is a concrete cross-module false negative: the test calls
`domains.enigma_solver.graph_crib_admissibility`, which creates graph-resident
candidate nodes and scan nodes, loads `seeds/enigma_recovery.json`, runs native
`run_rules`, and reads survivor IDs/witnesses from the graph-authored result.
The seed rules invoke `EnigmaCrib`, `EnigmaBombeWitness`, and `MapList` Terms;
`runners/dsl/src/term.rs` evaluates these through
`enigma::crib_admissible` / `enigma::bombe_witness` in `enigma.rs`.

The test asserts one exact crib survivor/rejection contrast and one partial
Bombe steckering witness. The same file also contains reciprocal machine,
M4, rotor, and solver-front-door tests, but those do not by themselves
establish the graph-resident admissibility capability. This is strong, narrow
integration evidence that the native predicate is reachable through seed
rules and graph readback. It is not evidence of general hypothesis induction:
candidates and crib are provided, the Enigma hypothesis class is fixed, and
candidate generation / soft language scoring stay outside this hard-cut
capability. The no-candidate AST status is therefore an alias-resolution
limitation, not missing coverage. No tests were run during this review.

## Rule closure and mutation-counter linked-path review (2026-10-03)

The current `rule_matching_effects_fixpoint` links are
`tests/test_recursive_rule_closure_migrated.py` (SHA-256
`3f43954be51df2208107954799f6feac504ac84023b26cdd0667d28fdad9d27a`) and
`tests/test_rule_effect_mutation_audit_migrated.py` (SHA-256
`ce35850bbd1c03910e5ce4b0e0158f5526b53dca3bd8cee7bf4ba729b97adb3e`).

* The recursive closure regression constructs a six-node directed path,
  installs two recursive `add_edge` rules, runs native `run_rules`, and checks
  all ten transitive-reach edges, effect-attempt counters, and a subsequent
  no-op fixed point. It directly catches the same-type edge-write visibility
  regression. Its finite path fixture is mechanism evidence, not a general
  termination or scaling result.
* The mutation-counter test covers eight native effect families in isolated
  tiny graphs and checks the expected instrumentation counters. It validates
  instrumentation wiring for those effects; it does not measure mutation
  costs, semantic interactions, or closure completeness.

The broader closure claim is supported by separate source-locked runs already
listed in the current capability map: exact closure against independent
oracles through the stated path/DAG sizes, same-build audit overhead controls,
and a restricted finite-key minting analyzer/runtime panel. The analyzer's
finite-key result is a termination argument under explicit finite-universe and
monotone-insertion assumptions; it is not unrestricted chase termination or a
polynomial wall-time theorem. Keep those controlled results distinct from
these two pytest regressions. No tests were run during this review.

## Current-map review reconciliation checkpoint (2026-10-03)

A path-based reconciliation after the thoughtexperiment, planning, Enigma, and
rule-closure reviews finds that audit sections now discuss paths corresponding
to **44/72 current capability-to-test link entries**. The remaining 28 entries
span 27 unique test paths; one current test path is linked to more than one
capability row. This reconciles the path references against the current map,
not a claim that each matching test independently proves its whole capability
row. The old 48/65 count remains historical; future progress should use this
current 72-entry denominator and preserve row-specific claim boundaries.

## Term evaluation, value-domain, and JIT linked-path review (2026-10-03)

The three current `terms_and_value_evaluation` links were inspected. Their
working-tree SHA-256 values are `54e468bfa87b9866ab8dd776200689867a4bb21406fcd8e60e9c56662939d167`
for `tests/test_term_eval_counter_migrated.py`,
`0882d9c556ca51344f6a9b516e45c13728c1075b6f0a4e6e4596d5f0a26fa95c` for
`tests/test_value_domain_migrated.py`, and
`019278f2d6a01fed4cc86aa16eef55cafb2ef93fef69e70007a41b8097468738` for
`tests/test_term_jit.py`.

* `test_term_eval_counter_migrated.py` validates the shipped engine's
  per-variant evaluation/unit counters, zero-when-off and live-workload
  behavior, attribution conservation, and a responsiveness gate with red,
  green, and inert controls. Its historical raw-result checks are conditional
  on committed result files being present. This is measurement-instrument
  correctness evidence; it does not itself establish the Term evaluator's
  semantic breadth or asymptotic cost.
* `test_value_domain_migrated.py` compares selected native `ProgEval` and
  ordinary Term cases with CPython, checks explicit traps, dict-order
  semantics, graph purity, and value-domain compatibility. The fixtures span
  several operation families but are hand-selected, small, and mostly scalar
  or short-container cases. Rational-specific compatibility tests skip if
  the installed binary lacks Rational support. Its frozen 147/427 HQ1 number
  is explicitly identified in the file as a historical pre-Q1.5 floor; the
  live emitter measurement is in a separate test path. Do not quote 147/427 as
  current benchmark performance.
* `test_term_jit.py` checks Term-to-IR translation and parity against the
  substrate evaluator on a small i32 arithmetic subset, including selected
  optimization-on/off equivalence. It imports `domains.term_jit`, whose path
  parses/optimizes substrate IR in Python-managed graph state, emits x86-64,
  then assembles through GCC. It does not call the Rust `runners/dsl/src/jit.rs`
  path named in the capability source links, and it has no throughput or
  speedup measurement despite the module's performance motivation.

Together these links give bounded evaluator/value semantics, cost-counter
instrumentation, and a separate Python-orchestrated compiler path. They do not
amount to a full semantic conformance suite or a native JIT performance result.
No tests were run during this review.

## Stage A rule-derivability and refusal path review (2026-10-03)

The remaining `rule_dependency_and_scheduling` link is
`tests/test_stage_a_refusal_migrated.py`, current SHA-256
`19b71223f75363397c43044ba58918f13d7ab36ec1546150a40b146a626c7746`.
The linked Rust predicate `stage_a::rule_is_derivable` refuses node-deleting
rules and rules with intra-rule read/write dependency or write contention;
other rules may use the opt-in Stage A proposal path. The test exercises live
native runs with the mode toggled and checks refusal counters, non-vacuity,
cross-rule propagation, fold-over-bindings exact totals at three sizes, and
settled graph/fixpoint parity on a real motion/boundary workload. It also pins
the previously falsifying parallax case as refused. This is unusually direct
correctness evidence for a scheduler optimization boundary, including positive
controls that prove the speculative path actually ran.

The result is still conditional: it does not prove arbitrary Term reads are
completely derived, cover concurrent graph writes, or establish a runtime
speedup. Several proof/measurement dimensions are specific to the tested
intra-rule coupling taxonomy. One test function launches a nested pytest
subprocess when the suite is run; it was inspected but not run in this review.

**Review reconciliation after term/value and Stage A audits (2026-10-03):**
The audit now discusses paths corresponding to **48/72 current capability-to-test
link entries**; 24 entries across 23 unique files remain. The count is derived
by exact path matching against the current map. It is a review-progress
measure, not a test-pass rate or whole-row capability score.

## Graph persistence, seed selection, and frame representation review (2026-10-03)

Four current source-linked paths were inspected; every digest agrees with the
2026-10-03 hashed crosswalk. SHA-256 values: `tests/test_persistence_migrated.py`
`3281a5af8e820bc8da676734eacdb264c01e3d022c90d076082f7582cb78e752`,
`tests/test_seed_loader_quiet_boot_migrated.py`
`4892aec66e9756a767116d4674909065899215fa7ce5c172f04a87d113596b41`,
`tests/test_rule_driven_look.py`
`accce952bf8bfacf4aa247c99405f153b24e67f9237c79c4bcc354f839753a9d`, and
`tests/test_frame.py`
`f7454b878dd72bd4080bb34f6b50147c41b5e9f9b1a4b10a9e8fc3a20b773255`.

* The persistence tests round-trip a small `WorldAdapter`, node IDs and
  adapter indexes, dynamic grammar, and a seeded concept; they also preserve a
  rule using a live shared-memory feed across save/load. The last case is
  stronger than a graph-only serialization check, while remaining one
  controlled feed/rule setup. `WorldAdapter.save/load` persists graph, grammar,
  active rule store, and selected adapter/profile state, then reconstructs
  them. These tests do not establish crash consistency, corrupt-file recovery,
  concurrent checkpointing, or large-graph I/O throughput.
* The seed-loader file covers declarative normalization, dependency/provider
  closure, typed content references, selective content slices, source-hash
  cache invalidation, incremental conversation loading, checkpoint resume,
  and refusal of incomplete selection before graph mutation. This is broad
  correctness coverage for a sophisticated Python-side seed index/selection
  and prepass with native manifest installation. It is not a measured boot
  latency or memory-scaling envelope, nor does it show all seed decisions run
  inside the Rust substrate.
* `tests/test_frame.py` checks graph-resident Frame/Dimension records,
  membership, equal and dominant relative log weights, thresholds, and
  idempotent refresh by key; it also confirms a value-form frame twin. The
  implementation constructs and queries these records through Python domain
  helpers. The tests validate frame representation and weighting, not
  separator discovery, treewidth reduction, or factorized inference. A
  dimension is an ontology axis here, not evidence that a graph cut is cheap.

These paths support durable graph state, selective seed boot, and explicit
frame semantics. They do not yet connect learned frame boundaries to measured
inference cost on task-derived graphs. No tests were run during this review.

## Production vision ingress link and benchmark reconciliation (2026-10-03)

The current production-ingress row's two linked tests are only supporting
mechanism checks. `tests/test_vision_waves_migrated.py` (SHA-256
`8315d2fd35131696740c085f29aca16148303afdd3bcb94c3f9309b978a47f0a`)
uses a synthetic 16×16 spontaneous retinal-wave model and checks spatial
correlation, burst-based Hebbian learning, and graph-rule winner selection; it
does not ingest production image frames. `tests/test_vision_change_migrated.py`
(SHA-256 `9e887a0e3da500d15058c770682272a11ed4428a418b5d6ffd28a9803ba30d05`)
was previously reviewed as a graph-authored change-detection rung, not a
production-ingress test. The refreshed capability-map summary already states
this distinction; retain the test links as mechanism evidence and do not use
them to support ingress or natural-image claims.

The direct evidence is the separate source-locked production pilot:
`SUBSTRATE_VISION_PRODUCTION_INGRESS_SCOPE_V1_1_RESULTS_20260929.md`, its 16
locked inputs, 32 raw workers (`source_stable=true`), and corrected analysis
with 12/12 integrity checks passing. Across three adapted checkpoints and
256 calls, every `WaveWorld.step(frame=...)` delivered the expected pixel
values. Root-scoped settlement preserved sibling `act`, `act_next`, and `rate`
state in all 24 comparisons; global settlement changed sibling state in all
24. The roots were supplied, inputs were synthetic gratings, and calls were
sequential; median whole-worker wall time was 0.309 s scoped versus 0.390 s
global over a small panel. The orientation readout varied by checkpoint and
is descriptive, not accuracy. This is evidence for the supplied-root frame
scope on a production adapter workload, not learned cheap-cut discovery,
realistic image-family accuracy, internal phase equivalence, or a CPU scaling
law. Separate 90°/180° rate-intervention experiments are diagnostics on
adapted states, not production scheduling behavior. No tests were run during
this review.

## Video codec and transcoding path review (2026-10-03)

The four current linked tests have hashes matching the 2026-10-03 crosswalk:
`tests/test_transcoding_pipeline.py`
`b34eef1c324f2932f61faecafec5ced094a619f457e5931a3defecd844da96a8`,
`tests/test_h264_vs_ffmpeg_trace.py`
`24b56642c44877409e911d38d2b6b1a9ae4337c2bcccf998ba7366abfadf780a`,
`tests/test_codec_graph_resident.py`
`618f927cb4fa4cebc31e9ddb7818929dd4318b6f664181bceaa6143a43ce261d`, and
`tests/test_h264_slice_header_walk.py`
`f4c2f1ecca3c44b4739f3325eb00d3aa8a1c0c1961a117830c5bf4339e3e6ffb`.

* `test_transcoding_pipeline.py` exercises graph-dispatched native H.264
  area-average downscale and CABAC transrate, output metadata/bytes, an Annex-B
  or AVCC format hop, idempotence, and a chained 4K→2K→1K style downscale.
  Fixtures use generated gradient planes and narrow power-of-two ratios. The
  payload check is not an external decode/conformance oracle, and this file
  does not establish H.265 transcode correctness or streaming throughput/RSS.
* `test_codec_graph_resident.py` seeds field grammars and rewrite rules as
  graph data, then tests decode/mutate/encode paths for H.264 PPS, JPEG, and
  selected HEVC PPS/SPS structures plus conditions, loops, and round trips.
  Python supplies the syntax descriptions and builds the fixture graph; the
  generic field walk and graph decisions run through the rule engine. The
  retained activation result reports 24/32 tests passing after rule
  installation was fixed, with eight HEVC/fixed-array failures remaining.
  One HEVC scaling-list case had been a vacuous pass when its rules were
  inactive; activation exposed the real failure. Preserve this negative result:
  supported syntax is partial, and the HEVC array/grammar gap is known.
* `test_h264_vs_ffmpeg_trace.py` compares selected fields against FFmpeg's
  trace_headers on a parrot stream, but imports `BitReader`, SPS/PPS parsing,
  and `walk_slice_header` from the pure-Python
  `test_h264_slice_header_walk.py`. It is a useful independent differential
  for that Python walker when FFmpeg and the external `/tmp/parrot` asset are
  available; it does not validate the mapped Rust H.264 slice walker.
  `test_h264_slice_header_walk.py` itself is explicitly a Python parser, with
  only CABAC context/bin primitives delegated to `substrate_rs`.

The source-linked row therefore contains a real native H.264 transform path
and generic graph-resident field-grammar mechanisms, alongside two misleading
links for the mapped native H.264 slice-header parser. Current direct limits
remain the eight known codec failures, no broad standards conformance, no
external H.265 output oracle, and no throughput/resolution/streaming-memory
envelope. No tests were run during this review. Primary retained evidence is
[the codec activation result](../vision/VISION_CODEC_ACTIVATE_RESULTS.md),
which records the before/after gate and residual failures.

## Auditory pipeline and learned speech-representation review (2026-10-03)

The three current auditory test links match the refreshed source hashes:
`tests/test_auditory_cortex.py`
`940a06a829d6d42de22ce061dda2a0c49019e63f0d27d8edb8b1b5f78b294727`,
`tests/test_cochlear_nucleus.py`
`09dcd42533585fc9afc6c47a01895d87dd85db80b8e6ea92bf7e9404756fdf84`, and
`tests/test_inferior_colliculus.py`
`8e6708fd298640753fee7571e6272277aa8a27d595c72fa40aa8e1956a2ec16a`.
They exercise seeded multiband pipelines over generated tones, band-limited
noise, amplitude-modulated carriers, and discrete bursts. Assertions cover
frequency/modulation selectivity, onset timing, syllable-candidate counts,
graph-resident operation wiring, response provenance, and a graph-edit
threshold intervention. These are useful controlled signal-processing and
mechanism results. They are not an independent DSP benchmark, natural-speech
corpus result, ASR/intent score, noise/accent evaluation, or scaling study.

The separate representation results measure a materially different layer of
the capability row. In the fair-pool study, APC NN-recall is 0.270 (95% CI
0.220–0.320) versus wav2vec2 L6 at 0.817 (0.773–0.857) on 3,000 held-out
LibriSpeech dev-clean word tokens from 10 speakers; the confidence intervals
do not overlap. In the follow-up build, AR-APC recall is 0.237 (0.190–0.287),
masked-CPC 0.220 (0.173–0.267), and masked-CPC with 6.7× more unlabeled
training utterances 0.233 (0.187–0.283), versus wav2vec2 L6 at 0.817. Neither
objective nor data lever improves cross-speaker word recall; multi-layer
Depth remains untested. Do not merge the Step-A 0.270 baseline with the
Step-C 0.237 baseline as though they were one paired run.

The current checkout contains the harnesses and prose result logs
(`scripts/apc_fair_pool_falsification.py`,
`scripts/apc_repr_gap_build.py`,
`docs/research/audio_speech/fair_pool_falsification_results.md`, and
`docs/research/audio_speech/repr_gap_build_results.md`), but a search of
`evaluation/` did not find the corresponding raw per-query captures or a
source/data lock for these two reported runs. The scripts use an external
`/home/matt/data/LibriSpeech` tree and scratch caches. Thus the numeric results
are documented and their method is inspectable, but exact independent
re-analysis from committed raw records is not currently reproducible from this
checkout. Preserve the negative outcome. Prospective machine-readable capture
support was added to both harnesses as documented below. No tests were run
during this review.

**Review reconciliation after codec and auditory audits (2026-10-03):**
Current-map exact-path matching now finds audit discussion for **62/72
capability-to-test link entries**; 10 entries across 9 unique files remain.
This tracks which linked test paths have been adjudicated and does not equate to
capability success. The auditory inventory also surfaced a separate result-data
reproducibility gap: the reported APC comparisons lack committed raw records
and source/data locks in this checkout.

**2026-10-03 prospective APC capture improvement:** Both scoring harnesses now
accept `--output PATH` and atomically emit schema-versioned JSON containing the
ordered word/speaker pool, deterministic seed and configuration, raw Rust recall
detail vectors, metric summaries, cache digests, source and native-extension
digests, runtime versions, verdict, and peak RSS. This supports independent
recalculation of future reported metrics without repeating model training. It
does not reconstruct the historical runs or include the extracted cache
contents themselves. Details and invocation examples are in the [Step A
result](../audio_speech/fair_pool_falsification_results.md) and [Step C
result](../audio_speech/repr_gap_build_results.md). The harnesses were not run;
the three edited Python sources passed AST parsing and `git diff --check`.

**2026-10-03 remaining-link source review:** Reviewed the nine previously
unadjudicated test files against the current crosswalk hashes:

| Test link | SHA-256 | What it establishes | Boundary |
|---|---|---|---|
| `tests/test_control_regime_escalation_migrated.py` | `2f11ed3b8c7fc98752f119c0df8dc8ec13090633b1456d690daac831375c82aa` | Graph-authored regime escalation rules, evidence starvation, Pareto candidate selection, and F-16 seed contracts through `WorldAdapter` settling. | Synthetic regime candidates and seeded scenarios; not a flight-simulation outcome or direct benchmark of the linked L3 controller kernels. |
| `tests/test_embodied_motor_future_manifold_v2_migrated.py` | `104d534809ff58df3bb61c37fb695898d8eb0a0d5ef765200dc26498feedfa6b` | Opt-in graph-rule contracts for manifold projection, width caps, provenance, and a bounded sequence-101 fail-closed scenario. | Much of the suite checks seed structure as JSON; no sustained physical actuator trajectory or broad motor-program generalisation. |
| `tests/test_reflex_net_migrated.py` | `6406f5b0fab4749e0e32c119a15de2e500945a9e5b23a21cfa86b202d0b38f80` | Native `NetForward`, direct and batch parity, toy self-training, external basin gating, threshold tuning, and rule-spine adoption/ablation. | Strong mechanism coverage for a constructed small network and toy targets; it does not establish open-ended network invention, broad task transfer, or performance at scale. |
| `tests/test_code_growth_migrated.py` | `72c971e31524e1e416eb1391997d56c718967b7203c433997c2d915fca87cc4e` | End-to-end bounded code-shape teaching, composition from a small held vocabulary, honest exhaustion, and run-to-validate reply gating through the conversation adapter. | Example and request are authored; generated Python is executed by the test. This is bounded program construction, not autonomous source-code improvement or general synthesis. |
| `tests/test_discourse_state_phase3a.py` | `12098ec627340771bf393e84ab8da9f69e353ef6ff0efe461f5a692f863b8be1` | Graph-backed event identity, goal lifecycle, provenance links, invalid-transition refusal, and expectation closure via Python adapter functions. | Tests the state API and graph storage semantics, not independent cognition or long-horizon interaction. |
| `tests/test_live_discourse_deliberation_bridge.py` | `4026f47446458b930887902d04ad80d955962e65e1043f0a8f9e95d8e8ae3769` | Live adapter binding from incoming messages to typed events, goals, deliberations, and conservative no-candidate/refusal dispositions. | Orchestration is Python-side and fixtures are controlled; this does not measure natural dialogue quality or deliberation scaling. |
| `tests/test_fetch_dispatch.py` | `76ebaed7bbe7a71a2ce4c6871f1d6b746b948e74884d4b8b4febeb10e101761d` | Python fetch dispatch against a local HTTP server, graph materialisation, unreachable-port handling, and `file://` refusal. | Does not call the mapped Rust `tools.rs::call_tool` path or exercise arbitrary external services. |
| `tests/test_control_trace_probe.py` | `7c8c9d808818ad6af27bf7054ed9b65fcfa20f3b2e01f56dd9bbd016a7c92e8e` | Pure reducer semantics for missing fields, canonical identity, transition counts/lags, and stable JSON. | Fixture traces are authored; it does not test collection of live Rust engine traces or controller benefit. |
| `tests/test_scale_split_provenance_migrated.py` | `c72ad8ed495d1913e967a42af850ff0eb38410975957b596cd3f5031e0b819f0` | Scale-audit default-off behavior, disabled-counter behavior, and experiment-rung/source-boundary provenance assertions. | This is an instrumentation and historical-diff integrity guard, not a scale curve or overhead measurement; it relies on pinned git revisions. |

Every hash above matches the refreshed AST crosswalk. `tests/test_fb_pipe.py` was
already discussed earlier in this audit via its relative Markdown link; it
tests the Python shared-memory writer, not the mapped native operation pipeline.
With link targets normalized, all 72/72 current capability-to-test link
entries (67 unique paths) now have an evidence-boundary discussion. The
embodied-motor test accounts for two capability-row links. This completes
test-path adjudication only; the broader capability inventory and empirical
evaluation gates remain open. No tests were run for this review.

The reconciliation is now executable:

```sh
python3 scripts/audit_capability_test_path_adjudication.py \
  --output evaluation/substrate_capability/capability_test_path_adjudication_v1_20261003.json
```

The retained [machine-readable reconciliation](../../../evaluation/substrate_capability/capability_test_path_adjudication_v1_20261003.json)
records the map, audit, crosswalk, and runner hashes; all 72 linked test entries
are mentioned in the audit, and all 72 current test hashes match the AST
crosswalk. These checks establish path coverage and freshness only, not
semantic relevance; the row-by-row judgements above provide that interpretation.

## Current-source inventory reconciliation (2026-10-05)

The capability map and linked files were refreshed after subsequent evidence
updates. The current generated map still has 28 capability rows, 72 linked
test entries, and 67 unique paths. The AST crosswalk was rerun against current
source hashes; it finds candidate callable-name matches for 19 rows, candidate
calls lexically inside assertion-bearing test functions for 17 rows, generic
name hits only for five rows, and no source-symbol call for four rows. These
counts prioritize review and do not establish that a test asserts the mapped
production behavior.

The executable adjudication now confirms all 72/72 linked entries are
mentioned by this audit and all 72 current test hashes match the refreshed
crosswalk, with zero missing mentions or stale hashes across 67 unique paths.
The current capability-map JSON hash is
`ddad48f723b311b1ee841a30fd48d2df679b833ca4e9ba0d0e0153bb6992c3e8`; the
crosswalk and reconciliation are
[`substrate_capability_test_relevance_audit_20261005.json`](../../../evaluation/reports/substrate_capability_test_relevance_audit_20261005.json)
and
[`capability_test_path_adjudication_v1_20261005.json`](../../../evaluation/substrate_capability/capability_test_path_adjudication_v1_20261005.json).
This closes current-source test-link mention/hash reconciliation, not the
semantic validity of each human judgement or the empirical capability gates.
No tests were run for this refresh.
