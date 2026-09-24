# Conversational Manifold Substrate Integration Audit — 2026-09-24

## Result

The substrate already contains most of the cognition and communication
machinery required for the remaining plan. The main duplication risk is in
the live adapter: it has several read-off/release seams, while native rules,
domain faculties, and graph indexes already own the corresponding decisions.
The audit therefore recommends integration and authority reduction, not a new
conversation subsystem.

## Existing capabilities to reuse

| Need | Existing substrate authority | Integration status |
|---|---|---|
| Concept/referent lookup | native `(Concept, name)` attribute index, `nodes_where`, `refers_to` rules | integrated for bounded ordinary ingress; question/meta paths retain their required full vocabulary ledger |
| Speech-act and intent evidence | `communication_intent_arbitration`, intent seeds, `ingest_semantic_event` | native arbitration is bound and measured; adapter only materializes supplied evidence |
| Discourse continuity | `discourse_state`, `conversation_deliberation`, topic-span and coreference seeds | existing graph state is reused; no second turn-state store permitted |
| Self/meta cognition | `reflective_faculty`, `self_model`, `conversation_self_reply` | existing reflective readback reused; live precedence bug fixed so an honest floor cannot shadow a valid meta result |
| Topic answering | `answer_topic` goals, `HeldAnswer`, topic grounding, production gate | existing goal/receipt path reused; legacy retrieval can run without publishing a competing receipt |
| Semantic production | language faculty, render rules, covert parse-back, `ProductionGateReceipt` | existing production authority retained; reply text is not semantic evidence |
| Partial/overlap events | native typed interaction metadata and communication arbitration | native disposition remains authoritative; adapter cannot force a turn/reply |
| Deliberation evidence | `self_dialogue`, `audience`, `global_workspace`, `future_option_risk`, gap-learning | partial typed evidence only; no promotion without a complete approved tuple |

## Reinvention findings

1. No new referent store is justified. The native concept index and graph
   `refers_to` path already provide the required substrate seam. The bounded
   ingress optimization now uses that index for ordinary messages and avoids
   materializing thousands of unrelated `knows_concept` edges.
2. No new speech-act classifier is justified. Surface classification remains
   a boundary input only; native semantic-event arbitration must continue to
   decide interpretation and disposition.
3. No new turn-state machine is justified. `DiscourseState`, goals, events,
   and native reply rules already represent asynchronous and turn-based cases.
   The adapter should remain a mechanical ingress/read-off boundary.
4. No new self-report generator is justified. `reflective_faculty` plus the
   language production faculty already render graph-grounded self-state.
5. No new production/release ledger is justified. `ProductionGateReceipt` is
   the existing release authority. Remaining work is to eliminate competing
   releases and missing authority, not add another receipt type.
6. The adapter still contains several Python read-off bridges. These are not
   automatically defects: they are acceptable only when they render an
   already-selected graph/native commitment and record provenance. Any bridge
   that selects force, disposition, goal, or turn boundary is integration debt.

## Newly verified issue and correction

For `How are you organised?`, the existing meta reader produced a valid
graph-grounded self-organisation answer, but the common read-off path released
the graph's honest-floor response first. The floor therefore shadowed the
substantive meta result. The correction changes precedence so the selected
meta readback is considered before the generic response adjacency; it does
not weaken the production gate or add surface text.

## Current implementation evidence

- Indexed ordinary referent ingress regression: passing.
- Meta/self-report compatibility regressions after the precedence correction:
  passing.
- Native concept index is present after seed boot and is used by the bounded
  ordinary-message path.
- The earlier Phase 7N profile remains valid as a baseline: the dominant cold
  allocation was mechanical full-vocabulary `knows_concept` backfill, not
  conversational wording or policy.

## Plan adjustment

The next implementation work must be split into two bounded tracks:

1. **Substrate integration:** complete equivalence and resource profiling for
   indexed bounded ingress; preserve full vocabulary only for faculties that
   explicitly require it, such as self/meta reflection.
2. **Authority audit:** classify each remaining adapter bridge as mechanical
   materialization, native readback, or prohibited Python selection. Integrate
   existing domain/native authorities before adding any new cognition.

The audit does not authorize broad refactoring. The remaining unbound calls in
the static authority audit are review debt and must be handled incrementally
with tests and replay evidence.

## Phase 7O increment — indexed equivalence and scene-authority binding

- Added a two-agent equivalence regression: indexed ordinary ingress and the
  legacy full-ledger ingress produce the same native `refers_to` concept set
  for the same message, while indexed materialization remains bounded below
  the full vocabulary edge count.
- Added the existing conversation-action scene goal readback to the native
  authority audit. Its `run_rules` call is explicitly classified as graph
  evidence materialization only; Python does not select the scene outcome.
- Current authority audit: **11 bound**, **171 unbound**, **182 total** calls.
  The unbound calls remain visible review debt; the count is not treated as a
  capability score.
- `.venv` verification: indexed equivalence battery **2 passed**; authority
  battery **6 passed**.
- A production-shaped optimized ordinary-event probe (`direct_action`) was
  replay-deterministic, with only **342** graph edges added by the event, but
  its cold first-event RSS delta was **110,010,368 bytes** and latency was
  **11,186 ms**. This keeps the resource exit open: the remaining cost is not
  explained by referent-edge fanout and must be investigated in substrate
  runtime/warm-up allocation, not hidden with a conversation surface change.
- Stage tracing then isolated the dominant cold allocation to the existing
  graph-kind bridge: `_graph_kind_for()` serializes the complete held rule
  program to obtain the `sak_kind_*` rules. Replacing the seed-presence probe
  in `_ensure_comprehension_seeds()` with the resident graph Rule scan removed
  its separate **2.2 s / ~31 MB** cost, but the kind-rule export still measured
  about **3.9 s / ~106 MB**. The next resource increment must integrate a
  selective native rule readback or an explicit boot-time warm-up; it must not
  replace native kind arbitration with a Python classifier.

## Phase 7P increment — selective native kind-rule readback

- Added `Substrate.export_rules_prefix(prefix)` to the Rust/PyO3 substrate.
  It emits only active matching rules in the existing `export_rules()` dialect;
  it is a bounded readback optimization, not a second rule store or authority.
- `_graph_kind_for()` now uses the native selective API for `sak_kind_*`, with
  a compatibility fallback for older binaries.
- Rebuilt the local `.venv` binary and verified the API is present.
- Production-shaped `direct_action` replay remained deterministic. The kind
  bridge fell from **3,918.8 ms / 106,143,744 bytes** to approximately
  **1,705 ms / 73,453,568 bytes**; full event latency fell from **9,193.4 ms**
  to **6,813.0 ms**. The formal probe report is
  `evaluation/reports/phase7_kind_readback_20260924_phase7p.json`.
- Cold RSS remains over budget at **109,969,408 bytes**. The remaining
  allocation is still a substrate warm-up/runtime issue, not a conversation or
  language-surface problem.

## Pre-continuation audit — 2026-09-24

The audit was rerun before continuing implementation. The machine-readable
record is `evaluation/reports/substrate_integration_audit_20260924.json`.

The local `.venv` focused battery passed **7 tests**. The current native
authority inventory is **11 bound / 171 unbound / 182 total** calls. Phase 4
has **0 complete candidate tuples** and **0 near-match tuples**, so no missing
deliberation dimension may be filled from a neighboring faculty.

The reusable substrate authorities are unchanged and explicit: the existing
`DiscourseStore` and native concept index own referent identity; `DiscourseState`
and `DiscourseEvent` own event-local continuity; `CommunicationInterpretation`
and native arbitration own force/disposition; existing `Goal` relations own
goal lifecycle; ThoughtManifold/residual/gap faculties supply deliberation
evidence; and `ProductionGateReceipt` owns release. No parallel referent store,
classifier, turn machine, candidate scorer, learning ledger, or receipt type is
justified.

The remaining `question_followup` discrepancy is a world-model evidence/fixture
contract issue, not evidence for a new conversation rule. The graph does retain
`gate` as the current topic from the earlier `question_referent` event, but no
typed event says that the gate closed and no causal relation explains why it
closed. The immediately preceding event is the unrelated
`question_unavailable`. If the benchmark intends to test causal learning, the
next bounded change must add a typed closure/causal event; otherwise its
expected disposition should be revised to `repair`/`unknown`. A lexical rule
for “Why did it close?” would violate this audit.
