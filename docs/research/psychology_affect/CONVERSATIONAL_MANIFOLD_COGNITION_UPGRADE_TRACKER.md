# Conversational Manifold Cognition Upgrade Tracker

**Parent plan:** [`CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_PLAN.md`](CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_PLAN.md)  
**Related implementation:** [`CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md`](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md)  
**Status:** Active incremental implementation. Conversational cognition/production and functional-substrate establishment are concurrent workstreams, not alternatives; the 150 MiB CAM ceiling constrains the conversational work but does not replace or pause substrate work. Latest full daemon replay with graph-selected host actions drained records 74/74 terminal outcomes and zero pending turns/requests. Cognition/production parity, resource limits, and comparative-evaluation exit evidence remain open.
**Invariants:** `noted` is never a failure surface. A failed cognitive/dispatch path must expose `ERROR: no communicative response could be generated.` The cognition/arbitration layer must be language-agnostic; language-specific modules may provide evidence but may not define the cognitive ontology.

**Named-subject polar relation increment (2026-09-28):** Closed the narrow
`Is the gate open?` gap when an accepted, explicitly evidenced unary
proposition is resident. Native arbitration now selects a yes/no plan only
when the proposition predicate, the adapter's selected subject, and the
event's `comp_know_concept` match, and the proposition has exactly the unary
`subject` role signature. Adapter readback validates that support chain before
English realization and production release. A binary proposition with the
same predicate/subject does not qualify; a topic-only held answer still repairs
instead of answering. Live affirmative release carries the normal supported
answer commitment. A follow-up fixed the English parse boundary for negated
copular adjectives: the selected property complement remains the relation
predicate even when the parser tags it adjectival, and its unique morphology
lemma is carried as adapter evidence. Live `Is the gate not open?` now selects
the native `no` value from the affirmative `open(gate)` proposition and
releases `No.` with the same supported answer commitment. The parse regression,
unary-support/binary-negative-control, live named-polar yes/no, existing
anaphoric positive, and topic-only repair controls pass **5/5**. This does not
establish cross-language realization parity or corpus-level cognition
acceptance; broader cognition, production, resource, and comparative gates
remain open.

The wider contextual-POS/action-evidence run reported **42 passed, 1 failed**;
the sole mismatch was a stale exact-surface assertion expecting an error for
an event-bound learning request. Current documented behavior is a
production-gated information clarification with no answer commitment. After
updating that assertion, the corrected test and adjective-parse control pass
**2/2**. No cognition or answer-authority predicate was relaxed.

**Relation-grounding safety slice (2026-09-28; broader support gate remains
open):** In the settled-nonturn-block replay, `Did the sensor report it?`
received the held topic answer `The gate is open.` The typed parse records a
polar relation with predicate `report`, subject `sensor`, object pronoun `it`;
discourse resolution maps the pronoun to the prior `gate` topic. That topic
grounding did not establish the asked relation. A first graph-native safety
slice now marks anaphoric polar relations `missing` when no relation-support
projection exists, and native arbitration chooses `repair`; the release
readback now requires native `answer` before attaching an answer commitment.
The target turn consequently releases a receipt-backed context clarification
with no answer commitment instead of the unrelated held answer. This is
fail-closed, not full relation reasoning: native arbitration now also projects
positive support when an event-bound topic joins an `accepted` structured
proposition with explicit neutral provenance and matching predicate/role
arguments. Neutral question-polarity evidence is compared to the proposition
polarity by native rules, which select an event-bound `PolarAnswerPlan` with
value `yes` or `no`. The language faculty realizes that semantic value through
the existing producer; output-null parse-back and a production receipt are
required before release. A bounded native recheck allows late discourse/topic
support to supersede only the provisional
`missing_polar_relation_support` repair; otherwise repair remains. Generic
HeldAnswer topic replies remain excluded from anaphoric polar queries. The
positive end-to-end probe with accepted graph evidence returns `Yes.` and a
supported polar answer commitment; the graph support test also validates
`No.` for opposite polarity. The fixed corpus has no proposition evidence for
this turn, so it continues to repair, while its expected label remains
`answer`; independent adjudication is still required. Latest 74-event replay:
[`Phase 8 polar answer plans`](../../../evaluation/reports/phase8_corpus_report_20260928_polar_relation_answer_plans_v1.json).
Counts remain 73/74 exact expected-state matches, grounding F1 0.592, and 55
released substantive replies / 5 explicit errors / 14 authorized silences.
After the answer-plan extension, the full neutral-arbitration module passes
**48/48** (499.45 s); the graph support/yes-no release test and both
supported/unsupported Phase 8 polar probes pass (**3/3**). An ordinary
topic-grounded polar control and the remaining cognition, production,
resource, and comparative gates remain open.

**Historical evidence snapshot (2026-09-27; resource threshold then 100 MiB):** The latest 74-event Phase 8 report
[`phase8_corpus_report_20260927_typed_refusal_defer_v1.json`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_refusal_defer_v1.json)
records 66/74 authoritative dispositions, 50 receipt-backed substantive
releases, 14 explicit errors, and 10 authorized no-reply outcomes (zero
unclassified silences). Grounding remains 21 TP / 29 FN / 0 FP (precision
1.00, recall 0.42, F1 0.592). Phase 4 remains 0/0/0
complete/eligible/promoted tuples; the comparative gate remains blocked at
provenance. Phase 8 synchronous median/p95/max latency is
**89.66/163.78/209.58 ms** (8/74 over 150 ms); latency remains open. Eight
events still lack native disposition authority. The all-event connected seed
profile is deterministic over 74 events with zero errors but exceeds the
absolute 100 MiB RSS cap at **109,445,120 bytes** (max event latency
130.66 ms); separate async daemon and scoped-profile measurements do not
establish full-seed synchronous resource closure. Strict full-boot limits,
fast-reflex-specific latency, and broader cognition/production acceptance are
open. Human reference sessions, an approved scoring rubric, and completed
blinded adjudication remain unavailable. This snapshot updates measurement;
it does not close the release gate.

Current active connected-profile resource check (measured before the 2026-09-28
150 MiB amendment): two independent all-74-event replays select the complete
conversation seed closure, have zero errors and identical **74/74** semantic
observations. Peak RSS is **100,593,664 / 100,687,872 bytes** and max event
latency **134.05 / 143.29 ms**. These measurements also satisfy the amended
RSS ceiling. Full-seed service startup remains outside it; see the current
connected/full-profile comparison in the execution plan.

**Current full Phase 8 replay (2026-09-28):** The negated-copular-polar parser
change initially hid a contrastive comma when the predicate token preceded
the comma, causing `correction_world` to lose its typed correction evidence.
Correction extraction now checks the predicate token's own punctuation as
well as following tokens. The fresh replay
[`negated-copular-polar v2`](../../../evaluation/reports/phase8_corpus_report_20260928_negated_copular_polar_v2.json)
has **zero semantic projection deltas** against the pre-change causal-answer
baseline across all 74 events. It records 74/74 authoritative dispositions,
grounding **20 TP / 30 FN / 0 FP (F1 0.571)**, **54** substantive releases,
**6** explicit errors, **14** authorized silences, and Phase 4 **3 source / 0
complete / 0 promoted**. Turn latency is **105.96/179.82/221.70 ms**
median/p95/max (**16/74** above 150 ms). The fresh connected-profile runs at
**135,426,048–137,072,640 bytes** pass the amended **157,286,400-byte** RSS
ceiling, but one of three narrowly misses the strict 150-ms max-latency target;
the historical full-seed service-template boot measured **1,450,897,408 bytes**
(the checked-in template has since switched to the conversation profile;
installed-unit state remains unverified). The comparative
gate is blocked on provenance; no human reference/rubric/adjudication evidence
is available. Thus the memory-cap amendment changes the connected-profile
resource result, not overall acceptance.

**Current matched-context v5 target and comparative packet (2026-09-28):** A
fresh 74-event v5 replay on the post-fix tree records grounding **20 TP / 30
FN / 0 FP (F1 0.571)**, **54** substantive releases, **6** errors, and **14**
authorized silences; latency is **109.35/189.75/222.76 ms**
median/p95/max (**18/74** over 150 ms). A new blinded packet binds this exact
target to the protocol-matched reference sessions, with **74/74** target
responses verified via the private alias key. The packet has 370 blank-score
rows and the two independent 370-row rater forms share its digest. The key is
outside the shared workspace and must not be distributed to raters. The
comparative, packet, and adjudication suite passes **20/20**. This closes the
v4/v5 target-binding gap only: human reference sessions remain absent, the
rubric is unapproved, and no ratings/adjudication exist. See the comparative
evaluation record for artifact links.

**Phase 6P current-v5 typed response-act bridge recheck (2026-09-28):** The
evaluation-only receipt bridge now recognizes the producer's explicit
response acts: common-ground updates for corrections, social coordination for
offer acceptance, non-endorsing acknowledgement, clarification requests, and
informative/defer outcomes for action requests. Compatibility is classified
from `ProductionGateReceipt` semantic fields only; runtime routing, release
policy, surface text, and corpus labels were not changed. On the matched v5
target, recoverability is **54 semantically compatible releases, 6 explicit
errors/withheld, 0 released semantic mismatches, and 14 authorized silences
without a receipt**. Focused recoverability and mismatch-audit tests pass
**9/9**, including an unrelated-social-response negative control. This closes
the measured receipt/force compatibility check for this target only; it does
not resolve independent expected-state disagreements or close production
acceptance.

**Selected-history evidence lineage (2026-09-29):** Closed a second gap in
the rule-history answer commitment chain. The native reply now carries an
explicit `realizes_rule_firing_answer_evidence` edge; synchronous readback
validates the exact selected evidence, its supporting `RuleFiringHistory`,
matching name, and source-message identity. A candidate lacking the selected
evidence edge is withheld. The full Phase 6A suite plus history-backed answer,
no-history repair, and unrelated-target routes pass **22/22**. The current
Phase 8 tuple digest is unchanged at 74/74
(`37f54c85e5ffb1d5a3a82e76f93dabadb0da70593174187cc3948bc7046a5c12`), with
74 authoritative outcomes and 54 substantive releases. The fresh Phase 7
profile completes deterministic replay with no errors and peak RSS
136,847,360 bytes (~130.5 MiB), but max event latency is 171.60 ms; strict
150-ms repeatability remains open. Comparative, Phase 4, and multilingual
surface-production gates also remain open. Reports:
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_history_evidence_binding_v1.json),
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_history_evidence_binding_v1.json).

**Source-current replay after response-message binding (2026-09-29):** A
fresh 74-event Phase 7 conversation profile completed seed selection, replayed
deterministically, had zero errors, passed every RSS assertion, peaked at
**136,413,184 bytes** (~130.1 MiB), and measured **142.33 ms** maximum turn
latency. Fresh Phase 8 retains **74/74** authoritative dispositions,
**54** substantive releases, and **15** authorized silences; latency is
**63.05/128.34/144.22 ms** median/p95/max with no turn above 150 ms. The
observed-state/reply/release/grounding/authority tuple matches the preceding
neutral-selection replay **74/74**, canonical SHA-256
`37f54c85e5ffb1d5a3a82e76f93dabadb0da70593174187cc3948bc7046a5c12`. The
release gate remains blocked at provenance; grounding is **21 TP / 29 FN / 0
FP**, Phase 4 is **0 complete / 0 promoted**, and comparative human scoring
remains open. Current reports:
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_answer_binding_v1.json),
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_answer_binding_v1.json).

**Connected-content pre-pass on async daemon ingress (2026-09-28):** The
conversation profile already had a validated provider/dependency pre-pass,
but daemon socket and HTTP chat ingress published turns without invoking it.
Both now use one shared mechanical entrypoint that resolves the turn's lexical
candidates through the cached seed index before parsing/graph arbitration;
full-profile startup remains a no-op. The daemon-envelope harness exercises
the same pre-pass and records its result per event. Three fresh 74-event
default-shadow-off runs select the complete declared closure, load content for
50 first-seen events and reuse loaded providers for 24, with identical
canonical observation digests and no external HTTP. RSS is **136,089,600 /
136,134,656 / 136,503,296 bytes**; max ingress is **17.26 / 17.84 / 19.21 ms**
and max native-cycle latency **37.56 / 36.49 / 37.81 ms**, within their
envelope limits. The implementation, daemon-envelope, and seed-loader suite
passes **38/38**; the daemon-envelope and multilingual integration batch
passes **12/12**. This closes pre-pass parity at the daemon ingress boundary,
not complete async turn parity: only **72/74** events terminalized (pending
`info_unknown` and `question_source`), and only **65/74** dispositions were
authoritative. Follow-up comparison found that `question_source` was natively
selected as event-bound attributed recall and synchronously releases a
source-linked receipt, but the daemon dispatcher lacked that faculty bridge.
Added the same graph-chain verifier/receipt release to async dispatch; it
preserves `grounding_status=unresolved` and
`epistemic_status=attributed_source_utterance`. The exact reply is identical to sync in the
dedicated regression. Three post-fix 74-event daemon runs now terminalize
**73/74** (only `info_unknown` remains pending because this signal-only profile
does not dispatch its host action), retain **65/74** authoritative
dispositions, and have identical canonical observation digests. RSS is
**136,540,160 / 136,404,992 / 136,409,088 bytes**; max ingress is
**16.31 / 16.80 / 16.64 ms**, and max native-cycle latency is
**98.42 / 97.11 / 101.52 ms**, under the amended memory and local timing caps.
The combined receipt/daemon/pre-pass/seed-loader suite passes **62/62**. This
closes async source-recall parity and daemon content pre-pass behavior for the
tested paths, not full production parity: `info_unknown`, other corpus
authority gaps, and the actual service profile/checkpoint migration remain
open. Reports: [post-fix run 1](../../../evaluation/reports/phase7_daemon_connected_content_prepass_20260928_current_v4.json),
[run 2](../../../evaluation/reports/phase7_daemon_connected_content_prepass_20260928_current_v5.json),
and [run 3](../../../evaluation/reports/phase7_daemon_connected_content_prepass_20260928_current_v6.json).

**Fresh Phase 2T event-to-commitment overlay (2026-09-28):** Replayed the
seven-case overlay keyed to existing Phase 0 event IDs on current code. All
nine event identities resolve; proposition materialization, commitment-state,
and consequence-projection accuracy are each **7/7**. Proposition provenance
is complete in **5/7** cases and consequence provenance in **1/7**; four
negative cases fail closed. No reply evidence or external-truth claim is used.
The dedicated test module passes **3/3**. This closes the isolated overlay's
specified measurement check only; it does not increase fixed-corpus grounding
recall, fill the missing Phase 4 tuples, or close general cognition acceptance.
Report: [`current Phase 2T measurement`](../../../evaluation/reports/proposition_event_commitment_measurement_20260928_current.json).

The current v5 target's remaining **30** grounding false negatives still
partition into **13** unverified discourse-state annotations, **7** unverified
graph-path declarations, **9** surface/uncertainty-only cases, and **1**
attributed-source recall. Its three Phase 4 partial records are all
grounding-only `topic_grounding` sources; none is a complete tuple from the
approved `ThoughtManifold` source. Corpus annotations alone cannot supply
runtime provenance or missing Phase 4 candidate values, so those gates remain
open pending supported evidence/adjudication. Details are in the current
execution-plan source recheck.

**Language-neutral frame-parity regression (2026-09-28):** Strengthened the
live Spanish/Japanese `LanguageWorld` integration test to assert each parsed
frame matches its semantic annotation and that the equivalent “who broke the
vase?” inputs produce exactly identical semantic frames before entering the
same native force/goal arbitration rules. The frames now cross the public
`ingest_semantic_event()` boundary, and the test verifies event-linked graph
readback plus provider provenance. Extended the same integration test to
realize an identical neutral `break(Mary, vase, past)` frame in English,
Spanish, and Japanese through the live producer and existing semantic release
gate. All three expected surfaces pass with 1.0 concept recovery and a
committed gate candidate. The multilingual variation module passes **2/2**.
This establishes one bounded multilingual production-parity slice, not broad
language coverage, discourse-level parity, or cross-language cognition
acceptance.

**Contrastive-correction increment (2026-09-27):** The language adapter now
emits typed correction evidence for the contrastive pattern “P, not Q” while
retaining ordinary negation as non-correction. Focused neutral-evidence tests
pass **6/6**. The fresh full-seed replay
[`contrastive-correction Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260927_contrastive_correction_v1.json)
records **66/74** authoritative dispositions and **50** receipt-backed
substantive releases (one more each); `correction_world` now selects native
`defer` and releases “I understand the correction.” through a graph-backed
receipt. Grounding remains **21/50 TP, 29 FN, 0 FP**. Latency measures
**92.97/167.54/193.14 ms** median/p95/max (10 above 150 ms); do not attribute
the overall timing change to this parser fix. Eight events remain without
native disposition authority. Phase 4 remains **0/0/0**, and comparative
release is still blocked at provenance. No phase exit gate is closed by this
increment.

The current targeted authority/corpus verification was rerun on 2026-09-27:
`.venv/bin/pytest -q tests/test_language_neutral_evidence_arbitration.py
tests/test_phase6_runtime_state_adjudication.py tests/test_phase8_corpus_runner.py`
=> **74 passed in 520.69 s**. The fixed Phase 5 corpus contract explicitly
contains no learning-observation evidence (`tests/test_phase5_corpus_runner.py`);
therefore the `learn_result`/`learn_uncertain` expected labels cannot be
converted to learning disposition authority without a separately sourced,
event-bound observation. This is an evidence gap, not a parser-label task.

**Typed inability response live-path control (2026-09-27):** A current direct
`WorldAdapter.converse()` check for a response-compatible first-person typed
inability (“I cannot reach the upper switch.”) confirms adapter evidence
`refusal/inability_action`, native disposition `error` with basis
`typed_inability_response`, and the canonical explicit diagnostic at the
surface. Added that end-to-end authority/surface assertion to
`test_language_neutral_evidence_arbitration.py`; the targeted typed refusal,
blocked standalone, and response tests pass **5/5**. This does not close the
fixed corpus `refusal_unknown` gap: “That action is not available” has no
first-person inability-action evidence, so classifying it as the same refusal
would exceed the parse evidence. The event remains unresolved pending distinct
semantic adjudication/evidence.

**Typed refusal defer terminal outcome (2026-09-27):** The live adapter now
returns native no-reply for a turn-compatible typed refusal only when graph
disposition is authoritative `defer` and the graph-derived reply expectation
is `not_expected`. It emits no acknowledgment or synthetic receipt. Phase 8
recognizes that silence only from those native fields. The fresh replay changes
explicit errors **15→14** and authorized silence **9→10**; other reported
cognition, grounding, release, and Phase 4 metrics are unchanged. Focused
conversation/evidence/Phase 8 suites pass **87/87**, and full/connected
structural parity is **74/74**. The all-event connected resource run remains
over the absolute RSS cap. This local control does not close broader
acceptance gates.

**Earlier bounded update (2026-09-26):** Action argument extraction now keeps
the complete nominal phrase and separately records its selected head, so
“open the north gate” produces object `north gate` / head `gate`, and “use the
east path” produces `east path` / `path`. This fixes object-head selection but
exposes unsupported corpus `graph_path` labels: the graph has substantive
direction concepts but not `gate`/`path` referents. Full action evidence plus
Phase 6A pass **45/45**; noun/adjective modifier and anaphora controls pass
**4/4**. Replay
[`phase8_corpus_report_20260926_argument_phrase_v27.json`](../../../evaluation/reports/phase8_corpus_report_20260926_argument_phrase_v27.json)
is blocked with 46/74 force matches, 54/74 authoritative dispositions (53/54
match expected state), 14/50 grounding true positives (precision 1.00, recall
0.28, F1 0.438), and 37 receipt-backed releases. No cognition or comparative
gate is closed by this correction; independent corpus reference labels remain
unchanged pending adjudication.

**Earlier repair-boundary update (2026-09-26):** A live production replay found
that native cognition selected `repair` for “look left then quorplezap the
door”, but the synchronous bridge still let the executable first clause mint
and release a `look(left)` Goal. The bridge now gives the event-bound native
repair disposition precedence over instruction execution. A second parser
defect treated the unknown initial action head in “Quorplezap the door” as a
gap and incorrectly promoted the later noun `door` to the action predicate;
the language adapter now preserves that initial gap as an unresolved action
head, and native arbitration selects repair when the ingress is an action
request. A current v5 replay then showed that preserving the full phrase
“lower sensor” could lose grounding even though both its typed head and
modifier had graph referents. The adapter now exposes the typed modifiers;
grounding accepts a compositional action target only when the head and every
modifier resolve, while explicit unresolved evidence remains a hard veto.
“unknown console” therefore remains unresolved, and the released action still
retains “lower sensor” rather than collapsing to “sensor”. Any actual typed
`gap` in the instruction parse also blocks compositional grounding; a held-out
unknown-token contrast verifies this negative path. The action-evidence and
Phase 6A modules pass **49/49**. The language-neutral arbitration and Phase 8
runner suites passed **52/52** before the final grounding-only refinements; the
current-state full replay below validates their corpus effect.

Fresh full v5 replay
[`phase8_corpus_report_20260926_compositional_action_grounding_v30.json`](../../../evaluation/reports/phase8_corpus_report_20260926_compositional_action_grounding_v30.json)
completes 74/74 events without runtime errors and remains blocked: force exact
46/74, authoritative dispositions 54/74, grounding 14/50 TP (precision 1.00,
recall 0.28, F1 0.438), and zero Phase 4 complete tuples/promotions. This
restores v27 grounding while preserving the full phrase and the unresolved
modifier negative control; no corpus labels were changed. Full release parity,
synchronous latency, resource, Phase 4, and comparative-human gates remain
open.

**Phase 1 parity recheck (2026-09-26):** the current
`tests/test_speech_act_parity_migrated.py` run reports **4 passed, 2 failed**.
The live-path comparison lists eight case-level differences, including
imperative content extraction (`look left`, `move north`), self-report routes,
the recognized imperative `Focus on the reading work.`, one compound
imperative, and the missing-world image question; the signal comparison also
differs on the `Focus` verb reading. These are not all established regressions:
some are evidence that the old fixture may not represent the intended
semantics, while others may be comprehension/adapter defects. Keep the frozen
fixture unchanged until each is independently adjudicated, and repair only
confirmed defects with held-out contrast tests.

**Independent Phase 1 force/goal check (2026-09-26):**
`tests/test_phase1_adjudication_fixture.py` passes **4/4**. Its expanded
communication-science adjudication slice matches graph arbitration on all
**20/20** events with zero false action, answer, or repair routes. This confirms
that the legacy parser parity failures do not imply the same force/goal
failures; it does not close the parser/output parity gate or broader corpus
force-exact-match gap.

**Standalone action-disposition/release increment (2026-09-26):** A new native
arbitration rule selects `act` for a non-turn standalone action only when the
interpretation carries typed action force, an instruction parse route,
candidate-grounded/grounded/partially-grounded evidence, a resolved reference,
and no temporal defer, correction, addressed-attention, or missing-world
marker. The separate graph instruction gate still reports that no world or
faculty is attached; it does not claim execution. The focused action,
language-neutral arbitration, and instruction suites pass **58/58**; the
independent 20-event Phase 1 adjudication passes **4/4**; daemon graph-release
contrasts pass **2/2**. Fresh full replay
[`phase8_corpus_report_20260926_standalone_action_act.json`](../../../evaluation/reports/phase8_corpus_report_20260926_standalone_action_act.json)
confirms `action_check` now has native-authoritative `act` and an exact
released production receipt. Authoritative state mismatches fall from two to
one (`question_ack` remains); corpus force exact match stays 48/74, authority
49/74, grounding F1 .507, and the release gate remains blocked.

**Resource follow-up (2026-09-26):** The connected 74-event synchronous
profile now measures **100,499,456-byte** peak RSS and the full daemon profile
measures **101,724,160 bytes**, both below the 100 MiB limit after completed
turns return glibc-free pages. Structural observation hash and graph counts are
unchanged; a second 74-event replay is `replay_equal=true` with the same hash.
Full seed selection, receipts, and terminal outcomes remain intact.
The **150 ms/event** synchronous latency gate remains open (max 1,236.9 ms,
retrieval-dominated); broader full-boot/resource parity remains to be checked.

**Execution focus handoff (2026-09-26):** The latest full Phase 4 reuse audit
has 3 event-bound `topic_grounding` sources and 0 complete tuples; each source
contains grounding only and lacks expected value, residual cost, consequence,
and novelty. The synchronous latency outlier is external retrieval; skipping it
would change grounded-answer behavior, so no latency-only semantic bypass is
accepted. A bounded functional-substrate tranche was opened alongside the
conversational work, using the programme in
[`FUNCTIONAL_SUBSTRATE_ESTABLISHMENT_PLAN.md`](../engine_substrate/FUNCTIONAL_SUBSTRATE_ESTABLISHMENT_PLAN.md),
starting with a current-source capability/ownership audit and preregistered
frame-locality workloads. This is concurrent work, not a replacement or pause
of conversational cognition, production, latency, or comparative gates; none
of those gates is marked passed by this handoff.

**Async follow-up (2026-09-26):** The graph-selected daemon dispatcher now
releases this instruction family through the same receipt gate. Its fresh
74-event replay adds one graph release (`action_close`), for 19 released graph
replies, 53 explicit errors, and 2 no-response terminals; all turns/host
actions drain. The post-turn allocator trim now lowers this replay's peak RSS
to 101,724,160 bytes. Envelope and daemon/debug suites pass **19/19**. Async
parity is improved but remains open.

**Latest production increment (2026-09-26):** A typed response acknowledgement
with native `defer` / `update_common_ground` now receives a graph-selected
non-endorsing receipt through both synchronous and daemon release paths. The
fresh full Phase 8 v2 replay preserves 52/74 authoritative dispositions,
51/52 authoritative state matches, and 14/50 grounding true positives (F1
0.438), while changing release outcomes to 42 released /26 errors /6
unavailable. The 74-event connected resource replay is deterministic and
measures 96,227,328-byte conversation RSS peak, but its max-turn sample is
152.45 ms; the full-seed v2 latency sample is 152.54-ms median, 233.20-ms p95,
and 285.33-ms max. Cognition, latency, async parity, complete Phase 4 evidence,
and comparative release gates remain open.

## 1. Current baseline snapshot

| Dimension | Evidence | Current status |
|---|---|---|
| Runtime teacher/LLM use | `donkey=0` assertions and native tests | 🟢 Verified in focused paths |
| Action/repair dispatch | `tests/test_action_evidence_and_defer.py`, `tests/test_phase6a_production_gate.py` | 🟢 49/49 passed on current compositional-grounding implementation |
| Turn-compatible continuity and API parity | `tests/test_utterance_conversation_unification.py` | 🟢 Focused gate passed |
| Self-report / scene description | Conversation-loop, conceptualizer, and audience-design regression; selected faculty now outranks generic graph gap release | 🟢 Focused regression and adjacent production gates pass; broader production gate open |
| Explicit failure surface | Conversation and speech grounding tests | 🟢 Verified |
| Topic grounding precision | Topic/reference evidence plus unrelated-answer regression | 🟡 Current matched-context v5 Phase 8: precision 1.00, recall 0.40, F1 0.571 (20 TP, 30 FN, 24 TN, 0 FP). The 30 misses partition into 13 unverified discourse-state claims, 7 unverified graph-path claims, 9 surface/uncertainty-only cases, and 1 attributed-source recall; no corpus-label promotion. |
| Register/common-ground cognition | Discourse lifecycle seam and production receipts | 🟡 Phase 3/6 increments; full integration remains |
| Deliberation trace completeness | Thought-manifold provenance, rejection, settle-back, and Phase 4P proposition boundary traces | 🟡 Current v5 Phase 8 has 3 event-bound `topic_grounding` partial records with grounding only; 0 complete tuples, eligible promotions, or actual promotions. No approved `ThoughtManifold` source supplies a live complete tuple. |
| Parse-back coverage | Production receipts and Phase 6P/6Q receipt-backed recoverability measurement | 🟡 Latest confirmation-source-repair v5 Phase 8 records 55/55 receipt-backed substantive releases, 5 explicit errors, 14 authorized silences, and 0 unclassified silence. Typed response-act compatibility recheck on the preceding current v5 baseline found 54 semantically compatible receipts and 0 force/intent mismatches; the 14 authorized silences are still without receipts. All 74 dispositions are authoritative, but 8 expected-state disagreements remain (`offer`, `question_response`, `question_ack`, `offer_inspect`, `info_choice`, `response_yes`, `social_question`, `learn_result`); adjudication is needed before interpreting them as system vs label errors. |
| Latency / RSS / graph residence | Independent fresh-process connected-profile resource runs; full boot and extended replay tracked separately | 🟡 User-amended ceiling is **157,286,400 bytes (150 MiB)**. Latest all-74 incremental connected-profile runs peak at **133,746,688 / 133,865,472 / 133,865,472 bytes**; max event latency **207.53 / 156.21 / 153.89 ms** is not consistently under 150 ms. In contrast, three fresh full-corpus `batch_before_boot` connected-prepass runs peak at **104,632,320 / 104,316,928 / 104,615,936 bytes**, with max event latency **131.59 / 131.91 / 136.57 ms** and exact normalized output parity with incremental mode at **74/74**. The fully drained offline connected-daemon replay terminalizes **74/74**, drains **11/11** host actions, and leaves no pending requests at **136,982,528 / 137,101,312 bytes RSS**. These measurements fit the RSS ceiling, but batch mode uses a known fixed corpus; it does not establish arbitrary online prefetch. The checked-in service template now requests `conversation`, uses a separate checkpoint directory, and enables strict seed-profile checkpoint checks; the systemd user bus was inaccessible in this evaluation environment, so the installed/running unit and actual checkpoint migration are unverified. Historical full-seed boot measured **1,450,897,408 bytes**. See current-tree reports linked in the execution plan. |
| Baseline comparison | Current target plus protocol-matched ELIZA, two Gemma 3 4B runs, two Qwen 3.5 9B runs; blinded packet refreshed | 🟡 [`confirmation-source-repair blinded packet`](../../../evaluation/reports/phase8_blinded_output_packet_20260928_confirmation_source_repair_v1.json) binds the latest target at 74/74 and has 370 blank-score rows plus two digest-bound rater forms. Both human classes, approved anchors, submitted ratings, and adjudication remain unavailable; comparative acceptance is blocked. |
| Science-grounded annotation | Independent force/goal/grounding labels plus held-out probes | 🟡 Phase 1 evidence exists; corpus expansion still required |
| Language-agnostic cognition | Neutral evidence boundary plus live Spanish/Japanese integration | 🟢 Live Spanish/Japanese equivalent-frame parity and native force/goal arbitration pass; multilingual production/realization parity and broader language coverage remain open |

## 2. Phase status matrix

| Phase | Objective | Primary locations | Status | Acceptance evidence |
|---|---|---|---|---|
| 0 | Evaluation contract and failure taxonomy | `tests/`, `evaluation/`, `docs/` | 🟡 Phase 0C conditional candidate/lifecycle contract | Versioned 74-event corpus, deterministic trace assertions, and explicit Phase 4 cross-reference for observed candidate traces; external baseline report and full-corpus candidate observations remain |
| 1 | Canonical comprehension and intent arbitration | `domains/comprehend_text.py`, `substrate/world_adapter.py`, seeds | 🟡 Historical/current parity is now adjudicated; broader force/intent coverage remains open | `tests/test_speech_act_parity_migrated.py` passes **6/6**: the 133-record capture remains unchanged, native scratch-rule parity is retained, and eight reviewed live deltas plus the `Focus…` verb-head signal change are explicit regression expectations. This resolves the stale byte-identity assertion, not general comprehension/force coverage |
| 2 | Grounding, reference, and epistemic state | topic routing, retrieval, gap seeds | 🟡 Phase 2I authority/grounding separation | Current matched-context v5 replay: 0 false positives, 20/50 true positives, recall 0.40, F1 0.571. The 30 false negatives have no verified referent path or include attributed source content; the Phase 2T event-to-commitment overlay passes separately and does not alter this score. |
| 3 | Discourse state and goal lifecycle | conversation state, goal seeds, interlocutor model | 🟢 Exit slices plus asynchronous common-ground stress pass; event chronology is now explicit within each state | Mixed-act, multi-addressee, interleaved-goal, and zero-reply event stress pass; `DiscourseEvent -follows_event-> DiscourseEvent` links are state-scoped, stale-handle checked, and recoverable from existing event indices |
| 4 | Deliberative candidate generation and arbitration | thought manifold, decision collapse, native cycle | 🟡 Phase 4 evidence-materialization and 4P boundary pass | Four original plus five held-out families, explicit graph evidence transport, native provenance/rejection/settlement, and Phase 4P boundary; latest live corpus has 3 grounding-only partial sources and 0 complete or selected candidates |
| 5 | Learning, gap closure, and self-correction | gap awareness, self-concern, correction model | 🟡 Phase 5O explicit corpus overlay | Six explicitly annotated event observations reuse live ingress; three identity-local native recurrences are measured; the unannotated base corpus remains correctly unavailable for learning claims |
| 6 | Cognitively gated production release | conceptualizer, audience, production, parse-back | 🟡 Latest confirmation-source-repair v5 report has complete receipt coverage for substantive releases; broader reply quality and async/sync parity remain open | Latest Phase 8 has 74/74 authoritative dispositions and 55 substantive released replies; 5 explicit errors and 14 authorized silences are separate outcomes. Eight state/expected-label disagreements remain; `question_ack` is one and requires independent adjudication. |
| 7 | Native integration and performance envelope | Rust substrate/cycle, adapter boundary | 🟡 Current connected profile passes the user-amended RSS ceiling and terminality, but not repeatable sub-150-ms latency; installed service state is unverified | Latest current-tree three fresh 74-event connected runs: max turns **207.53/156.21/153.89 ms**, RSS **133,746,688/133,865,472/133,865,472 bytes**, complete seed selection, and zero errors. Earlier reply/error/silence accounting remains a separate Phase 8 measure. The checked-in template selects the conversation profile with isolated strict checkpoints; systemd user-bus inspection was denied, so runtime activation and checkpoint state are not verified. |
| 8 | Comparative evaluation and release gate | `evaluation/`, `docs/` | 🟡 Latest matched-context v5 packet is fresh and unscored | Current target: 74/74 authoritative dispositions, grounding F1 0.571, 55 substantive receipt-backed releases; Phase 4 complete tuples/promotions remain 0/0. Human references, approved rubric/anchors, ratings, and blinded adjudication are absent, so comparative acceptance remains open |

## 3. Immediate execution queue

1. **Phase 4 upstream cognition:** Preserve explicit `no_candidate` until an approved existing faculty supplies a complete candidate-specific tuple. The current v5 replay has three event-bound `topic_grounding` records, each grounding-only, and no `ThoughtManifold`-owned complete tuple. The reuse/source audit is complete; no safe adapter-only field projection remains. Advance only with a genuine upstream candidate-value/consequence source or a newly authorized faculty contract.
2. **Phase 2/6 evidence adjudication:** Current v5 has 30 grounding false negatives partitioned into unverified source declarations and attributed recall, plus eight authoritative state/label disagreements (`offer`, `question_response`, `question_ack`, `offer_inspect`, `info_choice`, `response_yes`, `social_question`, `learn_result`). Obtain case-bound provenance or independent annotation adjudication before changing arbitration or accepting labels; keep unknown/authority-missing states fail-closed meanwhile.
3. **Phase 7 deployment/resource:** Current connected-profile RSS fits the user-amended 150 MiB ceiling. Three all-74 incremental runs peak at **133,746,688–133,865,472 bytes**; three fixed-corpus batch-prepass runs peak at **104,316,928–104,632,320 bytes** and keep every event below **150 ms** with 74/74 normalized output parity. Two fully drained offline daemon runs peak at **136,982,528 / 137,101,312 bytes**. The checked-in service template now uses `--seeds conversation`, a dedicated checkpoint directory, and strict profile checking; focused tests pass **3/3** for profile mismatch, ambiguous legacy checkpoint rejection, and profile marker round-trip. The installed/running user service could not be inspected because the systemd user bus is inaccessible here; activation and actual checkpoint migration remain unverified. Batch-prepass evidence still does not establish arbitrary service startup content candidates.
4. **Phase 8I comparative release:** The current v5 blinded packet now binds the latest target to the complete ELIZA/Gemma/Qwen raw runs at **74/74**, with two blank, same-digest rater forms. Collect protocol-matched base/advanced-human sessions, approve anchors/rubric, obtain two independent ratings and adjudication, then publish scorecards. No capability superiority or comparative release claim is allowed before those steps.

No wording-only repair is permitted for these items.

## 4A. Audit of remaining exit evidence — 2026-09-23

This audit separates implemented bounded slices from evidence still required by
the phase exit criteria. Counts below are repository `.venv` runs, not inferred
coverage from filenames or fixture size.

| Area | Verified current evidence | Still missing | Bounded next increment |
|---|---|---|---|
| Phase 2 | Runtime correction plus focused regressions are green; latest 74-event SUT rerun has 0 false-grounding violations, precision 1.00, recall 0.46, F1 0.630 | Conservative recall and supported event-to-commitment corpus coverage | Phase 2T neutral overlay keyed to existing events; do not alter the grounding denominator |
| Phase 4 | Combined live-manifold lifecycle suite passes: 27 tests; Phase 4P boundary adds 4 tests; native collapse, rejection, execution, settle-back, and bounded counterfactual traces are present | Production-corpus replay and complete upstream tuples | Identify an existing faculty that can author complete five-field evidence; no promotion by proposition or situation state |
| Phase 5 | A–F recurrence/promotion suite passes: 27 tests; 24 opaque identities/72 events, visible failed repair, explicit review, promotion, and retirement | Broader production-corpus recurrence and impact/priority measurement | Phase 5G verifies six heterogeneous families, priorities 2–7, monotonic growth, stable identities, route transfer, failed repair, and no cross-identity promotion; next is production-corpus recurrence |
| Phase 6 | Focused production/readback/output-null/QA gate passes; Phase 6Q final post-fix receipt readback covers 74/74 events | 6 receipt-semantic mismatches, 45 runtime-state diagnostics, and audience-state evidence | Correct receipt force/multiplicity causes and adjudicate graph state separately; 30 recoverable, 38 explicit/withheld, 6 mismatches, 0 missing |
| Phase 7 | Seven native measurement tests pass; extended dialogue, high ambiguity, graph growth, replay, authority, latency, RSS, and graph residence are measured | Native authority for remaining comprehension/discourse/learning decisions and production-scale resource envelope | Phase 7K neutral semantic-event envelope; current audit is 172 unbound and 10 explicitly bound calls |
| Phase 8 | Current 74-event report has 42/74 force matches and 44/44 matching graph-authoritative dispositions; raw ELIZA-floor and local-LLM observations remain case-bound | Grounding is 0.34/50; only 15/16 expected repairs and 5/9 expected acts have native disposition authority. Human references, adjudicated capability scores, repeated trials, and memory/learning/cost probes are unavailable | Continue cognition/production coverage first; then independently adjudicate existing raw runs, collect human references with provenance, and add repeated trials, confidence intervals, and a separate memory/learning/cost corpus |

Recommended execution order is Phase 4Q complete tuple authorship, Phase 5
production recurrence, Phase 6Q semantic mismatch correction, Phase 7K
production-envelope follow-up, and Phase 8 adjudication. Phase 2T and the
initial Phase 7K envelope are verified bounded increments. No
baseline score may be fabricated from raw observations or a protocol scaffold.

### 4E. Substrate integration audit — 2026-09-23

The architecture audit is recorded in
[`CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`](CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md).
It found that the substrate already provides the authoritative primitives for
messages/events, intents, goals, reference/common ground, thought manifolds,
residual learning, production gates, and native collapse. No new Rust or
substrate API is required.

The audit also found two integration corrections that must precede more Phase 4
work:

- conversation action goals are minted through the existing `has_goal` path but
  are not consistently linked with `Goal -comprehends-> Message`; the live
  deliberation binder therefore sees no eligible goal;
- `conversation.py`, `reference_resolution.py`, `discourse_state.py`, and
  `world_adapter.py` currently expose overlapping common-ground/referent
  writers. The canonical referent store must be reused, with `DiscourseState`
  retaining event-local lifecycle and delta state rather than minting parallel
  identities.

The current live binder is therefore not acceptance evidence for Phase 4. The
next increment is goal/event binding and referent-store consolidation, followed
by a corpus replay requiring event-justified (not universal) deliberation
traces. No source implementation was changed during this audit.

### 4F. Goal/event and live deliberation integration — 2026-09-23

- Added idempotent `Goal -comprehends-> Message` binding and `origin_turn_id`
  provenance to the conversation action boundary. Focused verification:
  **3 passed**.
- Added the live event/goal bridge correction: action/repair early-return paths
  now bind before release; actual `sent_by`/addressee graph provenance is used;
  grounding is read from `CommunicationInterpretation`; unresolved parsed topics
  are not promoted to grounded current topics; and the Phase 4 seed is loaded
  once rather than on every event.
- Empty event-linked deliberations now use the existing native
  `generated_from_discourse_state` contract and settle to explicit
  `status="no_candidate"` with `candidate_trace_complete=1.0`, without
  fabricated candidate evidence.
- Focused live bridge plus production/goal regressions: **19 passed**.
- The 74-event replay now records **74/74** cognition traces and **28**
  event-justified complete deliberation traces (all explicit `no_candidate` in
  the current corpus); no selected-candidate traces are present because the
  live path still lacks evidence-bearing manifold candidates. This is progress
  in observability, not Phase 4 completion.
- Added the Phase 4 manifest to the seed registry so full boot and incremental
  live boot have the same native deliberation vocabulary.

### 4G. Canonical referent ownership — 2026-09-23

- Added `DiscourseConceptProvider` and idempotent
  `DiscourseStore.ensure_referent()`.
- `WorldAdapter` now lazily retains one canonical `DiscourseStore`; `CurrentTopic`
  remains a compatibility/focus projection and no longer mints a new referent
  on every projection.
- Repeated topic projection and save/load rehydration tests pass: **2 focused
  tests**, plus one legacy compatibility test.
- `CommonGround` remains participant-relative claim state; it is not treated as
  a second referent-identity owner.

### 4H. Verification boundary and known legacy conflicts — 2026-09-23

The broader reference/topic regression battery produced **41 passed, 6 failed**
after the integration. The failures fall into two categories: legacy tests
expecting the retired `I don't hold that.` surface, and a fake-grounder test
whose stale surface does not match the later graph-held answer. The explicit
error invariant and production gate are intentionally preserved; these failures
require specification/test-fixture reconciliation, not a wording fallback or
an unrelated-answer release. They are not counted as Phase 2/6 acceptance.

The next cognitive increment remains Phase 4 evidence generation: convert
existing train-of-thought/grounded relation evidence into native candidate
nodes, then let the Phase 4A native collapse select or reject it. Do not create
synthetic candidates merely to turn the current `no_candidate` traces green.

### 4I. Evidence-bearing candidate materialization — 2026-09-23

- Added a mechanical `conversation_deliberation` boundary that materializes
  candidates only from explicit graph evidence. It supports active discourse
  goals with linked evidence, repair/residual stance evidence, and live
  `ThoughtManifold` evidence relations, while preserving source provenance.
- A lifecycle `Goal` without numeric cognitive evidence is not promoted. A
  goal may use an explicitly linked `supported_by` evidence node; no policy
  defaults are copied onto the goal and no language or reply text is used as
  evidence.
- Native Phase 4A rules remain authoritative for valuation, Argmax collapse,
  rejection, execution, settlement, and counterfactual credit. The materializer
  performs no ordering, scoring, selection, or fallback surface generation.
- Local `.venv` verification: focused Phase 4/live-bridge/action battery
  **32 passed**; `py_compile` and `git diff --check` passed.
- This closes the bounded evidence-transport seam, not the live production
  candidate-generation gate. The 74-event corpus still needs a real
  graph-resident train-of-thought/grounded-relation source before selected
  candidate traces can be claimed.

### Phase 4J — Legacy decision-option authority boundary — 2026-09-23

- Audited the existing `ConversationDecisionState`/`DecisionOption` records
  against the Phase 4A candidate schema. They expose fast/learned/grounded
  values and residual/deep metadata, but no declared `consequence` or
  `novelty` evidence mapping.
- Direct promotion would infer missing evidence and create a competing
  authority, so it is explicitly rejected. The live bridge remains
  evidence-only and settles to native `no_candidate` until a faculty supplies
  the complete Phase 4 tuple.
- Added an executable boundary regression; it passed with the focused Phase 4
  suite. No synthetic candidate or surface fallback was introduced.

### Phase 4K — Native deliberation readback diagnostics — 2026-09-23

- Added an evaluation-only `deliberation_readback` summary to the Phase 8 SUT
  observations. It records whether native deliberation trace data exists,
  native statuses and candidate sources, candidate count, selection count, and
  settlement count.
- Missing trace data remains `unavailable`; a native `no_candidate` trace is
  reported as measured with zero candidates. The evaluator never infers a
  candidate from a goal, reply, or surface string.
- Live inspection confirms the current 74-event corpus has no complete upstream
  Phase 4A evidence tuple for ordinary communication events. This increment
  improves the evidence boundary and observability; it does not manufacture
  candidates or claim Phase 4 completion.
- Local `.venv` verification: Phase 8 corpus-runner battery **11 passed in
  374.24s**; compilation and diff checks passed.

### Phase 4K — Pre-continuation substrate reinvention audit — 2026-09-23

- Re-audited the current substrate before beginning another phase. The audit is
  recorded in
  [`CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`](CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md).
- Confirmed reusable authorities for referents/centering, gap recurrence and
  acquisition, graph-prioritized learning, thought-manifold evidence, native
  deliberation, production/readback gates, native cycle execution, and neutral
  communication evidence. No new substrate API or parallel conversation
  cognition store is justified.
- Confirmed the two active boundaries: `DiscourseStore` owns referent identity
  while `DiscourseState`/`CommonGround` retain event-local lifecycle and claims;
  legacy `DecisionOption` records are not promoted into Phase 4A without the
  missing `consequence` and `novelty` evidence dimensions.
- Remaining work is evidence/integration work: production-corpus recurrence,
  complete live manifold evidence, native-authority audit debt, and authorized
  external baselines. No defaults or surface-level substitutes may be added to
  make these gates appear complete.

### Phase 4L — Global Phase 4 tuple availability audit — 2026-09-23

- Added `evaluation/phase4_substrate_tuple_audit.py` and executable tests that
  scan seed-manifest node records for the complete tuple
  (`grounding`, `expected_value`, `residual_cost`, `consequence`, `novelty`).
- The audit found no complete seed-record tuple. `dual_process_core` is a
  reusable arbitration substrate and a near-match, but it lacks the complete
  Phase 4 evidence contract and is not promoted by inference.
- `ThoughtManifold` remains the only approved source type for a complete live
  tuple. This closes the reinvention audit increment without claiming that a
  live manifold generator exists.

### 4B. Phase 6/8 corpus transport correction — 2026-09-23

- Corrected `evaluation/phase8_corpus_runner.py` so corpus events labelled
  `imperative`, `compound_imperative`, or
  `imperative_with_politeness_marker` enter the runtime as `instruction`
  evidence. The runner had been downgrading them to `statement`, losing an
  input-level cognitive signal before native comprehension ran.
- Added a regression in `tests/test_phase8_corpus_runner.py` for that mapping.
  Local `.venv` verification: the Phase 8/manifest replay battery passed
  **16 tests** in 5m23s; the focused Phase 6 bridge battery passed **29 tests**.
- Refreshed `evaluation/reports/phase8_corpus_report_20260923.json`. The live
  manifest diagnostic is now **ready**, with **74/74** cognition traces, **40**
  released receipts, **34** explicit errors, and **74/74** accepted coverage.
- Grounded held-answer release and event-scoped permission evidence were
  implemented; authority precedence now prevents later referent refresh from
  overwriting `authority_missing`. Binary grounding remains precision **1.00**,
  recall **0.38**, F1 **0.551**, with zero false-grounding positives. The
  canonical error surface remains the only unresolved-release surface.
- The corpus semantic-state comparison still has **60/74** mismatches. This
  is the substantive Phase 6 bottleneck: manifest coverage proves that every
  event has a graph-backed release/error/trace, not that the selected state or
  answer relation is correct. The next cognition increment must reduce these
  mismatches by improving state arbitration and relation-specific evidence,
  not by adding conversational wording.

### 4C. Native input-force evidence increment — 2026-09-23

- Added `sak_input_kind` as graph-resident evidence when an upstream language
  adapter supplies `instruction`/`request` force. The native speech-act rules
  consume that evidence before ambiguous POS/wh cues, without adding an
  English verb inventory or using reply text as evidence.
- Added `tests/test_native_instruction_input_evidence.py` covering bare,
  compound, and conditional imperative forms plus a question non-regression.
  Local `.venv` focused verification: **4 passed**; the combined native and
  Phase 6 production battery passed **33 tests**.
- The replay at this earlier increment measured **42** released receipts,
  **31** explicit errors, **73/74** accepted substantive coverage, and one
  uncovered event: `blocked_permission`. A later authority-precedence fix
  brought the current replay to **42** receipts, **32** errors, and **74/74**.
  `action_sequence` now has a graph-backed action receipt. Grounding remains
  precision **1.00**, recall **0.42**, F1 **0.592** at that increment; the
  current binary replay is precision **1.00**, recall **0.38**, F1 **0.551**.
- The full `test_comprehension_cutover_migrated.py` rerun was not completed:
  after installing missing `.venv` dependency `nltk`, it reached 1 test in
  10m48s and was stopped at the existing slow boot path. This is an
  environment/runtime verification limitation, not counted as a passing gate.

### 4D. Permission/authority fail-closed increment — 2026-09-23

- Added graph-resident permission evidence derived from semantic Concept
  attributes and action-role relations. A request with no
  `PermissionDecision`, `AuthorityDecision`, or `PermissionEvidence` is marked
  `authority_missing`; it cannot fall through to an unrelated interlocutor
  self-report.
- The unresolved information production gate now evaluates authority-missing
  requests and emits the canonical explicit error with a withheld receipt.
- Added a focused regression for `Can I access the sealed room?`; the Phase 6
  information bridge suite passes **8 tests**. The latest corpus replay now
  records the canonical error and withheld receipt for `blocked_permission`,
  bringing the manifest to **74/74** accepted events.

## 4. Per-phase execution record

### Phase 1 — Initial increment completed

- Start: 2026-09-22
- Added graph-resident `CommunicationInterpretation{schema:'communication_interpretation.v1'}` records for every live communication event, including selected kind, dispatch path, intent, focus, predicate/object, gap count, native kind, conflict status, and interaction mode.
- Linked each interpretation to its inbound `Message` with `has_interpretation` and `interprets`, and to the agent with `holds_interpretation`.
- Kept the comprehension result as the selected interpretation while retaining native speech-act output as evidence; disagreement is recorded as `kind_conflict`, not silently discarded.
- Added `tests/test_conversational_intent_arbitration.py` covering instruction selection, frontier-gap evidence, native/comprehension conflict retention, and non-turn interaction mode: **4 passed**.
- Existing action/repair regression subset after the change: **4 passed**.
- Added non-turn-mode coverage through the compatible `converse(..., context={"interaction_mode": "streaming_observation"})` boundary; the record remains event-based and does not require turn alternation.
- Added separate graph fields for literal mood/evidence, communicative-force hypothesis, cognitive-goal hypothesis, grounding status, and parse/native evidence provenance. These are recorded hypotheses, not yet adjudicated human labels.
- Remaining work: build the fixed Phase 0 corpus, measure native/front-end agreement, classify conflicts, and promote only a measured arbitration policy to authoritative dispatch.
- Measurement completed: [Phase 1 intent arbitration report](CONVERSATIONAL_MANIFOLD_PHASE1_INTENT_ARBITRATION_MEASUREMENT.md) records 93.8% kind agreement, below the 95% acceptance target.
- Added a science-grounded annotation contract: literal form, communicative force, cognitive goal, grounding status, interaction relation, and evidence are separate labels.
- The current disagreement classes are provisional; indirect information request, assertion/report, compound event, and parser/classifier error must be distinguished before arbitration policy is promoted.
- Expanded `tests/fixtures/comprehension_divergence/phase1_adjudications.json` to **20** independently adjudicated events, adding direct information/action requests, ordinary assertions, unresolved action requests, and social coordination.
- Adjudication verification: **3 tests passed** (JSON/schema coverage, independent force/form separation, and raw corpus measurement).
- Added graph-native `seeds/communication_intent_arbitration.json`; runtime arbitration matches all ten adjudicated force/goal labels, including indirect requests and the declarative gap-report correction.
- Expanded runtime route measurement before the action-evidence upgrade was **19/20 (95.0%)** with one false action route. After the upgrade it is **20/20 (100.0%)**, with false action, false answer, and false repair all at **0**.
- Added canonical action/account evidence in `domains/comprehend_text.py`: a recognized politeness-prefixed clause can use the held verb-head faculty when primary POS is misleading, and reporting/enumeration force survives POS-lattice fragmentation, while native speech-act evidence remains separately auditable.
- Replaced graph arbitration's English predicate/path matching with `communication_evidence.v1`: the language adapter emits neutral force/goal evidence, and graph rules consume only the evidence schema. English-specific markers and POS/order assumptions remain confined to the current English evidence provider and are not part of the cognitive ontology.
- Added `tests/test_language_neutral_evidence_arbitration.py`, where a synthetic semantic adapter drives all five force/goal classes without English words, POS, mood, or dispatch-path fields.
- Added `domains/communication_evidence.py` and Spanish/Japanese semantic-frame variation coverage in `tests/test_language_neutral_variation.py`; the unchanged graph rules pass both languages through the neutral evidence boundary.
- Installed `pyarrow` into the repository `.venv` and enabled the live `LanguageWorld` text-to-frame integration test; Spanish and Japanese frames now cross the neutral evidence boundary successfully.
- Runtime adjudication and expanded-metric gate: **4 tests passed**; existing conversation-loop regression: **12 passed**.
- Added held-out `tests/fixtures/comprehension_divergence/phase1_generalization.json` covering information requests, action requests, repair/defer, assertion/common-ground update, and social coordination.
- Added parser-gap arbitration so unresolved lexical gaps become `repair_or_defer` while ordinary declaratives with non-gap grounding imperfections remain assertions.
- Held-out generalization gate: **1 passed**; combined Phase 1 focused suite (adjudication, runtime interpretation, and generalization): **8 passed**.
- Phase 1 exit evidence: 20/20 force/goal agreement, zero false action/answer/repair routes, neutral synthetic-provider coverage, and live Spanish/Japanese LanguageWorld integration.
- Next phase: begin Phase 2 grounding/reference/epistemic-state work; retain the Phase 1 route and language-variation batteries as regression gates.

### Phase 2 — Initial increment completed

- Start: 2026-09-22
- Added durable `TopicGroundingEvidence` records for persisted `HeldAnswer` data, with explicit referent, support status, source, and evidence path.
- Added compact evidence fields to `HeldAnswer` so graph topic-reply arbitration can require a referent match, supported status, and non-empty evidence path before setting `Goal.outcome='resolved'`.
- Added `_has_topic_grounding_evidence` as a mechanical readback guard for the synchronous fulfiller; unsupported/legacy candidates fall through to the honest unresolved outcome.
- Fixed a cognition-level arbitration conflict: when a follow-up is both generically instructional and graph-routed to an answer topic, the specific grounded topic goal takes precedence.
- Added `test_topic_resolution_requires_referent_linked_evidence`, which poisons a same-key candidate and verifies that unrelated content is not returned as a resolved answer.
- Focused verification: topic tracking suite **6 passed, 1 skipped**; evidence regression **1 passed**; the initial combined run exposed and then fixed the instruction-vs-topic arbitration conflict.
- Remaining work: tighten the unresolved rule's evidence predicate, add multi-referent/coreference and retrieval-candidate coverage, and measure grounding precision/recall across the Phase 0 corpus.

### Phase 0 — Evaluation contract

- Owner: unassigned
- Start: 2026-09-22
- Evidence: versioned 74-event labelled corpus, stratified coverage metadata, deterministic event-trace validator, and non-turn/turn-compatible trace tests. The live trace gate checks neutral evidence, force/goal hypotheses, grounding/gap evidence, intent, goals, mentions, concerns, parse evidence, and reply provenance.
- Blockers: baseline scores and complete candidate-generation traces require later runtime/evaluation phases
- Next action: retain this corpus as the Phase 0 regression substrate; do not treat fixture labels as runtime accuracy until a later measured harness adjudicates them

### Phase 1 — Intent arbitration

- Owner: unassigned
- Start: 2026-09-22
- Evidence: graph-resident interpretation, science-grounded adjudication fixture, seeded force/goal arbitration policy, and held-out generalization fixture
- Blockers: none for the current exit criteria; broader adjudication and compound-event coverage remain future hardening
- Next action: maintain as regression gate; expand compound-event and language-neutral adjudication coverage

### Phase 2 — Grounding and epistemic state

- Owner: unassigned
- Start: 2026-09-22
- Evidence: `TopicGroundingEvidence`, `HeldAnswer` referent/status/path fields, graph reply gate, synchronous fulfiller guard, and unrelated-answer regression
- Blockers: live SUT grounding precision/recall is low and the unrelated-answer gate has violations; broader retrieval/reference coverage remains
- Next action: use the measured false-grounding cases to tighten cognition-level grounding arbitration without treating a reply as evidence

### Phase 6A — Cognitively gated production release

- Start: 2026-09-22
- Added `domains/production_gate.py` as a bounded release seam for the existing
  parse-back/output-null monitor. A surface is released only when its selected
  semantic frame has an event, intent, and content role, the monitor verdict is
  recoverable, and a committed monitor node exists.
- Successful releases now leave a graph-resident `ProductionGateReceipt` linked
  to the committed record, carrying the released surface, semantic content,
  parse-back mode, coverage, and recoverability. Missing evidence remains
  buffered for the existing one-repair attempt and then the explicit error
  floor; no acknowledgement or `noted` fallback is introduced.
- Every gate attempt now leaves a receipt: `released` for complete evidence or
  `withheld` with explicit reasons for empty output, forbidden fallback,
  missing semantics, failed parse-back, or missing commitment. The production
  path uses the same seam for recoverable and output-null candidates.
- Added `tests/test_phase6a_production_gate.py`: release evidence contract,
  missing-evidence withholding, forbidden-fallback rejection, live frame-
  production receipt coverage, and two-attempt output-null audit coverage.
- Focused verification with the repository `.venv`: Phase 6A plus output-null
  suite **10 passed**; adjacent active-frame production regression included in
  the combined run **12 passed**. `py_compile` and `git diff --check` pass.
- Added a bounded legacy fact-readback gate: the existing structural renderer's
  relation, subject, and object must survive deterministic parse-back before a
  `ProductionGateReceipt` can release the answer. A two-case semantic corpus
  covers `is_a(graph, structure)` and `uses(process, data)`; forced parse-back
  failure withholds output and preserves the explicit error floor.
- Verification with the repository `.venv`: Phase 6 production gate,
  output-null, and legacy-readback suite **12 passed**; the adjacent QA,
  relation-rendering, and conversation-unification regressions were **32
  passed, 1 stale noted assertion deselected**. JSON validation, `py_compile`,
  and `git diff --check` pass.
- Expanded the fixed semantic production corpus from two facts to ten
  substantive binary-relation readbacks, covering unmarked, marked, taxonomy,
  containment, optimisation, support, observation, mapping, and ownership
  relations. Added end-to-end `answer_question` traversal assertions and
  receipt-count/release-status checks, so direct retrieval and the legacy QA
  route are both covered by the same production gate.
- Closed the cached-readback bypass found during audit: `answer_question` now
  re-runs graph-resident fact answers through `answer_about` and retains the
  comprehension cache only as fallback for non-fact learned answers. The
  two-pass corpus test records **20/20 released receipts** for 10 facts,
  proving repeat reads do not evade parse-back evidence.
- Verification with the repository `.venv`: Phase 6 gate, legacy corpus,
  output-null, and QA tests **20 passed**; adjacent relation-render and
  conversation-unification regressions also pass below. No `noted` surface is
  released; failed evidence remains withheld and reaches the explicit error
  floor through the existing caller.
- Extended the legacy readback battery across the substantive question faculty:
  `what is`, `what's`, and `what are` routes all re-enter the same
  semantic parse-back/release gate for every fixed-corpus fact. Added a routed
  parse-back failure regression proving that question readback produces a
  withheld receipt rather than a released or `noted` surface.
- Local verification for this increment: Phase 6 production/readback,
  output-null, and QA tests **24 passed**. The adjacent regression command
  reported **35 passed, 1 skipped, 3 failures**; all three failures are stale
  assertions expecting the forbidden `noted` acknowledgment in
  `tests/test_full_turn_migrated.py`. JSON validation, `py_compile`, and
  `git diff --check` passed.
- This bounded Phase 6D increment covers the remaining overt legacy QA forms;
  computational faculties such as predicate evaluation and `answer_within`
  remain cognition results rather than overt production surfaces and are not
  incorrectly routed through a conversation release gate.
- Remaining work: broaden the corpus beyond the bounded binary-relation
  family and audit any additional legacy faculties that emit substantive
  surfaces; this increment does not claim full G6.1 acceptance.
- Remaining work: extend the same receipt/release gate to every other
  substantive legacy readback path and establish the larger fixed production
  corpus required for G6.1; this increment does not claim full Phase 6
  acceptance.

### Phase 6E — Legacy readback path audit and taught-answer gate

- Audited the repository's substantive legacy surface readers. The actual
  routes are direct `WorldAdapter.answer_about`, the fact branch of
  `WorldAdapter.answer_question`, the live question branch of
  `WorldAdapter.converse`, and the taught-capability fallback inside
  `answer_about`. `answer_predicate` and `reason.answer_within` return boolean
  or numeric cognition results rather than overt surfaces and are therefore
  excluded from a production utterance release corpus. Frame production via
  `_realize_frame_reply` already has its own Phase 6 gate.
- Closed the remaining cached-readback bypass: taught answers now use the same
  `legacy_structural_readback` parse-back and `ProductionGateReceipt` release
  seam as graph-resident facts. A topic whose selected referent is not
  recoverable is withheld; a plural topic may recover through its deterministic
  singular structural form (for example `volcanoes` / `volcano`).
- Expanded the semantic relation corpus from 10 to 14 binary cases and added
  path-level tests for direct, question-front-end, live-conversation, taught,
  and forced-failure routes. Explicit error behavior remains observable and no
  `noted` surface can be released.
- Phase 6E local verification: repository `.venv` focused Phase 6 suite **27
  passed in 16.43s** (`test_phase6a_legacy_readback.py`,
  `test_phase6a_production_gate.py`, `test_output_null_gate.py`, and
  `test_qa_migrated.py`). The adjacent topic/self-healing command reached
  **6 passed** before being stopped at 180s in the pre-existing slow
  `self_model.py` path; it was not a Phase 6 failure and the full repository
  suite was not run. The 14-case JSON corpus, Phase 6 Python compilation, and
  relevant-file `git diff --check` all pass. G6.1 remains yellow until the
  full production corpus and every additional substantive surface faculty are
  covered.

### Phase 5A — Gap identity and verified self-correction

- Start: 2026-09-22
- Added `seeds/gap_identity.json` with graph-native `gap_identity.v1`
  canonical identities that preserve cognitive kind, source, content, and
  originating turn/goal provenance. Message-linked concerns use the message
  turn; unresolved topic goals now retain the originating event id as a
  mechanical datum before `gap_awareness` decides whether to file a gap.
- Narrowed legacy duplicate retirement to the cognitive identity components
  already available at filing time (kind/source/content), so same-text gaps
  with different cognitive kinds are not silently collapsed. The canonical
  identity remains metadata for later recurrence, prioritisation, promotion,
  verification, and retirement; it does not make a learning decision.
- Added graph-native correction verification with immutable original concern
  content, `CorrectionRecord` provenance, corrected level-2 `RouteModel`, and
  visible failed-correction state.
- Verification with the repository `.venv`: gap identity suite **2 passed**;
  legacy gap dedup/retirement regressions **2 passed**; human-gated promotion
  and seed reconciliation checks **2 passed**. JSON validation, Python
  compilation, and `git diff --check` also pass. No Python-side canonicalisation
  or learning decision logic was added.
- Remaining work: connect identity to recurrence/prioritisation and verify the
  repaired route through the broader promotion and future-conversation loop;
  the full 15-test gap/promotion battery remains resource-heavy and was not
  used as Phase 5A exit evidence in this increment.

### Phase 5B — Identity recurrence and future-route application

- Added `seeds/gap_learning_phase5b.json`, keeping recurrence as graph state
  keyed by `gap_identity`: one `GapRecurrence` node records recurrence count
  and priority for an identity, so repeated historical occurrences do not mint
  duplicate recurrence records.
- Connected verified `RouteModel` provenance to the matching recurrence node;
  a later `Goal` carrying the same identity is routed through the learned route
  exactly once. The original concern remains historical evidence and no second
  active concern is required for route application.
- Added `tests/test_gap_learning_phase5b.py` covering verified-route transfer,
  identity-keyed recurrence/priority, and no duplicate concern for the future
  route case.
- Verification with the repository `.venv`: Phase 5B focused suite **2 passed
  in 0.21s**; the existing Phase 5A identity/correction slice remained green
  (**4 passed** in the combined run before the Phase 5B test correction).
- Phase 5 remains partial: broader promotion, recurrence across real
  conversation/task events, and the resource-heavy full gap/promotion battery
  remain outside this bounded increment.

### Phase 5C — Recurrence pressure and supervised promotion assessment

- Added `seeds/gap_learning_phase5c.json`, a graph-native assessment seam that
  connects a recurrent `GapRecurrence` to one `GapLearningAssessment` once its
  recurrence count reaches two. The assessment preserves recurrence evidence,
  records failed-repair count, and marks the case `human_review`; it never
  auto-promotes, closes the concern, or rewrites its content.
- Added `tests/test_gap_learning_phase5c.py` with a failed-repair battery and an
  eight-identity resource-heavy replay. The tests verify visible failed
  `CorrectionRecord` state, stable identity recurrence, no duplicate concern
  for the repeated route, one assessment per identity, and idempotent replay.
- Verification with the repository `.venv`: Phase 5C **2 passed in 0.22s**;
  the combined Phase 5A/5B/5C focused battery **8 passed**. JSON validation,
  Python compilation, and `git diff --check` also pass.
- Remaining work: exercise the assessment through the broader real
  conversation/task promotion pipeline and the full resource-heavy gap/
  promotion corpus; human-gated promotion remains intentionally separate from
  this graph assessment.

### Phase 5D — Actual recurrence, review, repair, verification, and decision

- Added `seeds/gap_learning_phase5d.json`, which opens one graph-resident
  `HumanReview` for a recurrent `GapLearningAssessment`, records failed repair
  attempts as durable `FailedRepairRecord` evidence, and requires an explicit
  human `approve` or `retire` decision before changing recurrence state.
- Verified repair creates a `RepairVerification` only after explicit approval;
  promotion and retirement both record `human_review` authority. No rule
  automatically closes a concern, promotes a route, or retires a recurrence.
- Added `tests/test_gap_learning_phase5d.py` covering task recurrence through
  review, failed repair visibility, verified promotion, and explicit retirement.
- Verification with the repository `.venv`: Phase 5D **3 passed**; the full
  Phase 5A/5B/5C/5D focused battery **11 passed**. JSON validation, Python
  compilation, and `git diff --check` passed.
- Phase 5 remains partial: broader real conversation/task promotion and
  resource-heavy end-to-end coverage remain.

### Phase 5E — Real conversation ingress and repeated-task decision coverage

- Added `tests/test_gap_learning_phase5e.py`. One test drives the live
  `WorldAdapter.converse()` unresolved-topic path and verifies that its
  graph-resident `SelfConcern` carries a `gap_identity.v1` origin turn before
  an explicit call to the existing human promotion gate creates a pending
  `StandingConcern`; `converse()` does not promote it automatically.
- The second test runs two historical task stages under one opaque stable task
  identity, then drives recurrence → human review → failed repair → verified
  retry. Failed repair remains graph-visible and the assessment remains
  `human_review` until explicit `approve`; a separate repeated task reaches
  `retired` only after explicit `retire`.
- Local `.venv` verification: Phase 5E **2 passed in 44.22s**. The broader
  Phase 5A–E battery remains the follow-up verification for this increment.
- Phase 5 remains partial: production-scale conversation/task corpus coverage
  and broader promotion-resource stress are still open.

### Phase 5F — Production-shaped recurrence and promotion stress

- Added a bounded production-shaped corpus of 24 opaque task identities and 72
  historical conversation/task events. Each identity is observed through
  conversation, task attempt, and retry stages, with one failed correction
  evidence node. Recurrence is keyed by graph identity rather than surface
  language.
- Verified one `GapRecurrence`, one `GapLearningAssessment`, one visible
  `FailedRepairRecord`, and one pending human review per identity. All 24
  assessments reach the recurrence threshold and remain `human_review` with
  `auto_promoted=0`; no standing
  concern, automatic promotion, or automatic closure is created.
- Verified that one explicit human approval promotes only its selected
  identity and one separate explicit human retirement retires only its
  selected identity; replay does not alter the remaining assessments.
- Local `.venv` verification: Phase 5F **1 passed in 0.25s**; the current
  combined Phase 5A–F battery **27 passed in 15.60s**. The five Phase 5 seed manifests
  parsed successfully, `py_compile` passed, and scoped `git diff --check`
  passed.

### Phase 0 — Expanded evaluation contract slice

- Start: 2026-09-22
- Expanded `communication_event_corpus.v1` in `tests/fixtures/conversational_manifold/phase0_events.json` to 74 independently labelled events spanning non-turn and turn-compatible modes, standalone/continuation/overlap/response relations, all declared force/goal/grounding/state strata, and expected cognitive states.
- Added `evaluation/conversational_manifold_phase0.py` for deterministic schema validation and event-trace contract assertions.
- Added coverage metadata and validation for the planned 60–100 corpus and its trace dimensions: interpretation, intent, goal lifecycle, mention/referent, topic, self-concern, parse evidence, and reply provenance.
- Extended `tests/test_phase0_evaluation_contract.py`: corpus independence/validation checks plus live event-based trace assertions for streaming, asynchronous, and unsolicited interaction modes. Assertions inspect neutral graph evidence, grounding/gap fields, graph interpretation/provenance, and `donkey=0`; they do not snapshot surface wording.
- Added [Phase 0 evaluation contract](CONVERSATIONAL_MANIFOLD_PHASE0_EVALUATION_CONTRACT.md).
- Verification: Phase 0 focused suite and dependent Phase 8 corpus-loading tests pass with the repository `.venv` command.
- Added a conditional candidate/lifecycle cross-reference to the native Phase 4 contract (`seeds/conversation_deliberation_phase4a.json`) and a validator for observed source, candidate count, lifecycle completion, and resolved settle-back evidence. The fixed 74-event corpus carries no synthetic candidate records; events without an actual deliberation remain untraced rather than being mislabeled `no_candidate`.
- Verification: the Phase 0 suite now covers the conditional cross-reference and observed Phase 4 lifecycle shape; full candidate generation remains governed by the Phase 4 native tests.

### Phase 3 — Exit slice

- Start: 2026-09-22
- Added `domains/discourse_state.py` with a graph-resident `DiscourseState` schema, event records, goal origin/addressee/evidence links, guarded lifecycle transitions, and explicit fulfilled/deferred/error expectation closure.
- Added `seeds/conversation_discourse_state.json` as the vocabulary manifest; no Phase 2 topic files or broad world-adapter code were changed.
- Added `tests/test_discourse_state_phase3a.py`: idempotent state/event residence, proposed→selected→executing→resolved lifecycle with no orphaned active goal, invalid-transition rejection, and defer/error-compatible expectation closure.
- Verification: local `.venv` command `PYTHONPATH=runners/dsl/python:. .venv/bin/python -m pytest -q --tb=short tests/test_discourse_state_phase3a.py` => **4 passed**; JSON validation, Python compilation, and `git diff --check` also pass.
- Added `ensure_common_ground` with graph-resident `CommonGround{schema:'common_ground.v1'}` revision/claim state, participant/addressee links, and event contribution edges.
- Extended discourse-state integration so events retain speaker/addressee identity and goals inherit the state's conversational addressee when one is established.
- Added `tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json`, a ten-event mixed-act sequence spanning request, selection, execution, result, assertion, question, and explicit epistemic repair/defer.
- Added `tests/test_discourse_state_phase3_exit.py`: ten-event state/common-ground/addressee assertions and native seed-loaded goal lifecycle execution.
- Added `conversation_discourse_state` seed registration and three native rules for proposed→selected→executing→resolved transitions, with transition-event provenance and closed-goal linkage.
- Verification with the repository `.venv`: Phase 3A plus exit suite **7 passed**; JSON validation, Python compilation, and `git diff --check` pass.
- Phase 3 exit slice is complete. Remaining future hardening is longer dialogue stress, richer interlocutor models, and native handling of blocked/repaired/abandoned branches; these are outside this bounded exit scope.

### Phase 3 — Common-ground/addressee stress increment

- Added `phase3_common_ground_stress.json` and a bounded ten-event stress test
  with two addressees, interleaved goals, observations, assertions, native
  selections/executions/results, and zero reply events.
- Tightened `record_event` so every event recipient is incorporated into the
  graph-resident common-ground participant ledger, including the agent as an
  event recipient. This preserves event-level address without making the
  discourse model turn-dependent.
- Verified both goals can be advanced and closed over mixed communication
  events while unrelated observation/assertion events remain in the event
  stream; no reply event is synthesized or required.
- Verification: local `.venv` Phase 3A plus exit suite, including the new
  stress fixture, passed **9 tests**. JSON validation, Python compilation,
  and `git diff --check` passed.

### Phase 7A — Native cycle measurement and replay determinism

- Start: 2026-09-22
- Added evaluation-only `evaluation/native_cycle_measurement.py`; it constructs a
  graph-authored native transition, runs a bounded Rust `default` cycle, and
  records native reports, graph node/edge residence, wall latency, and peak RSS.
- Added `tests/test_native_cycle_measurement.py`: bounded measurement, native
  graph-authored transition, and fresh-process-equivalent replay comparison.
- Added [Phase 7A measurement protocol](CONVERSATIONAL_MANIFOLD_PHASE7A_NATIVE_MEASUREMENT.md).
- Local `.venv` verification: focused native measurement plus existing cycle
  regressions **11 passed**; `py_compile` and `git diff --check` pass.
- Local measurement (`8` measured cycles, `1` warm-up): median latency **0.080875
  ms**, min/max **0.077741/0.104111 ms**, graph residence **11 nodes / 9 edges**,
  peak RSS **23,519,232 bytes**, replay determinism **true**. The measured
  cycles were settled (`0` additional steps after warm-up); the no-warm-up test
  confirms the native transition takes one step.
- Added bounded `fast`, `deep`, `recovery`, and `long_dialogue` native
  measurement profiles. The profiles assert fixed native step/graph ceilings,
  replay equality, and graph residence without Python-side selection logic.
- Local `.venv` verification: profile/replay suite **3 passed**; exact
  eight-cycle measurements were replay-equal for all four profiles. Profile
  residence: fast **11/9**, deep **34/32**, recovery **22/20**, and
  long-dialogue **42/40** nodes/edges. Warm-up-free native steps were fast
  **1**, deep **1**, recovery **2**, and long-dialogue **1**; later cycles settle
  to zero. Workload-size and graph-residence measures carry the
  depth/dialogue scaling without overstating cycle-step counts.
- The bounded Phase 7 performance-envelope increment is complete. Phase 7
  remains 🟡 because native-authority coverage for remaining cognitive
  decisions and broader resource envelopes are still open.

### Phase 8A — Comparative evaluation and release-gate scaffold

- Start: 2026-09-22
- Added the evaluation-only `comparative_cognition_evaluation.v1` contract in
  `evaluation/comparative_release_gate.py`.
- Fixed the reference classes to `eliza_floor`, `small_llm`, `modern_llm`,
  `base_human`, and `advanced_human`; fixed the cognition dimensions to
  interpretation, grounding, action, repair, memory, learning, calibration,
  provenance, and cost.
- Required scorecards to carry all dimensions, sample count, confidence
  interval, raw-metric description, and evidence references. Overlapping
  intervals are reported as `indeterminate`; missing evidence blocks release.
- Added five focused scaffold tests. Local `.venv` verification:
  `tests/test_phase8a_comparative_release_gate.py` => **5 passed**.
- Added [Phase 8A comparative evaluation protocol](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md).
- No runtime cognition or Phase 2–7 implementation files were edited.
- Remaining work: bind the contract to the fixed corpus, collect real repeated
  baseline observations, publish confidence intervals/failure slices, and
  produce the dated G8.1 comparison report.

### Phase 4A — Deliberative candidate generation/arbitration audit

- Start: 2026-09-22
- Added `domains/conversation_deliberation.py` as a mechanical evidence boundary. It materializes an explicit candidate ledger but performs no ranking, selection, or fallback choice.
- Added `seeds/conversation_deliberation_phase4a.json`: native rules score grounded candidates, collapse through graph `Argmax`, trace the selected candidate, reject unsupported and outcompeted candidates, and expose `no_candidate` when no grounded candidate remains.
- Added `tests/test_conversation_deliberation_phase4a.py` covering winner/rejection traces, explicit no-candidate state, and an adapter audit forbidding Python ranking calls.
- Verification: local `.venv` Phase 4A suite => **3 passed**; JSON validation, Python compilation, and `git diff --check` pass.
- Boundary: this is not full Phase 4 acceptance. Candidate generation is supplied as evidence-bearing input, and live thought-manifold integration, counterfactual credit, and settle-back trace coverage remain open.

- Phase 4 bounded integration: added `materialize_from_thought_manifold(...)`, a real graph-resident `ThoughtManifold -> proposes_candidate` source seam. The adapter copies evidence and provenance only; native rules still score and collapse candidates. Added native execution and resolved settle-back trace rules, including explicit rejection provenance for unsupported proposals. Local `.venv` Phase 4 suite => **5 passed**. Full thought-manifold generation and counterfactual credit assignment remain open.

- Phase 4C bounded counterfactual trace: added native `cm4b_credit_grounded_rejected_alternatives`. After a grounded selected candidate resolves, each grounded alternative rejected by native collapse receives one graph-resident `CounterfactualCredit` node containing the selected/alternative IDs, observed winner outcome, score margin, and negative alternative credit. Unsupported candidates are excluded, and the trace is explicitly marked `unexecuted_alternative`; no counterfactual outcome is represented as observed fact. Local `.venv` Phase 4 suite => **6 passed**. Full manifold candidate generation and repeated-task credit validation remain open.
- Phase 4D bounded graph-state candidate generation: added `materialize_from_discourse_state(...)`, which derives evidence-bearing proposals directly from graph-resident active goals, linked residual stance/repair nodes, and unresolved residual state. It records source provenance while leaving valuation, native collapse, rejection, and counterfactual credit to the seeded rules. An empty cognitive evidence set now reaches an explicit native `no_candidate` state rather than requiring an externally supplied candidate list. Focused local `.venv` Phase 4 deliberation/settle-back suite => **10 passed**. Remaining Phase 4 work: broader live thought-manifold generation and repeated-task credit validation.

- Phase 4E bounded live-manifold generation: added `materialize_from_live_thought_manifold(...)`, which derives proposals from four distinct graph-native evidence relations (`has_goal_evidence`, `has_repair_evidence`, `has_stance_evidence`, and `has_residual_evidence`). The boundary preserves source relation/provenance and transports only pre-existing numeric evidence; native rules remain authoritative for scoring, collapse, rejection, execution, settle-back, and empty-evidence `no_candidate`. The adapter has an AST regression forbidding Python outcome-selection calls. Local `.venv` Phase 4 deliberation/settle-back suite => **14 passed**. Remaining Phase 4 work: repeated-task counterfactual-credit validation.
- Phase 4E repeated-task counterfactual validation: replayed four graph-native thought-manifold tasks through the same native valuation, execution, settle-back, and counterfactual-credit path. Each replay preserved grounded winner evidence, recorded exactly one grounded rejected alternative, produced stable credit/margin, and remained idempotent across additional native settling. Python supplied only graph evidence and observed outcomes; it did not select candidates. Local `.venv` Phase 4 suite => **11 passed**. Remaining Phase 4 work: broader live-manifold/task-family coverage beyond this bounded replay.
- Phase 4F task-family lifecycle validation: exercised live graph-manifold generation for action, repair, social, and information evidence. Each family preserved source-relation provenance, native winner collapse, unsupported and outcompeted rejection traces, resolved execution/settle-back, and exactly one grounded rejected-alternative counterfactual trace with positive winner margin and negative alternative credit. The family matrix changes only cognitive evidence kind/relation; it introduces no language or reply-text shortcut and performs no Python selection. Local `.venv` Phase 4 task-family, deliberation, and settle-back suites => **22 passed** (including 4 family cases). Remaining Phase 4 work: broader task-family/manifold corpus coverage.

### Phase 2B — Reference evidence boundary

- Added `domains/reference_resolution.py` with graph-resident
  `ReferenceResolutionEvidence`, explicit `supported`/`unknown` status, and
  evidence paths for resolved and unresolved references.
- Verification: local focused reference suite **5 passed**.
- Connected retrieval candidate selection to the referent-evidence boundary:
  requests carry explicit supported/unknown referent status and evidence path;
  candidates carry per-referent coverage and native selection requires complete
  supported coverage. Multi-referent requests therefore cannot resolve from a
  partial candidate, and unknown/unresolved references remain unknown.
- Retrieval remains a cognition input: it writes `SearchCandidate`,
  `RetrievalEvidence`, and `HeldAnswer` data but never creates a
  `CommunicationInterpretation` or `Message` and never claims a communication
  event.
- Added Phase 2 coverage for compound referents, unresolved coreference, and a
  resolved discourse referent handed to retrieval explicitly. Local `.venv`
  verification: **9 Phase 2 evidence tests passed**; the existing topic suite
  remains a separate regression gate.
- Remaining work: broader retrieval/reference corpus and grounding
  precision/recall measurement across the Phase 0 corpus.

### Phase 2D — Fixed-corpus grounding precision/recall measurement

- Added the evaluation-only `phase2_grounding_measurement` adapter over all 74
  Phase 0 events. It uses four explicit language-neutral labels: `referent`,
  `coreference`, `unknown`, and `contradiction`.
- `grounded` and `partially_grounded` are annotated as `referent`;
  `unresolved_reference` as `coreference`; `unknown` and `unavailable_world`
  as `unknown`; and `contradicted` as `contradiction`. Runtime labels are
  derived only from grounding evidence, never from reply text or answer shape.
- The report includes expected/observed counts, a four-by-four confusion
  matrix, per-label precision/recall/F1, macro metrics, and an explicit
  unrelated-answer-resolution violation list. A non-referent event observed
  as referent is a failure even when a reply is present.
- Fixed-corpus contract verification: **3 tests passed**. Identity replay
  measurement is 100% precision/recall/F1 across all four labels; the poisoned
  unknown case produces one referent false positive, one unknown false
  negative, and one unrelated-answer-resolution violation.
- Historical pre-correction live SUT result over 74 events: expected labels were referent **50**,
  coreference **6**, unknown **16**, contradiction **2**; observed labels were
  referent **33** and coreference **41**. Per-label precision/recall/F1 were
  referent **0.6364/0.4200/0.5060**, coreference **0/0/0**, unknown **0/0/0**,
  and contradiction **0/0/0**. Macro precision/recall/F1 were
  **0.1591/0.1050/0.1265**. The unrelated-answer-resolution gate recorded
  **12 violations** (`unresolved_reference`, `unavailable_world`,
  `question_weather`, `question_unavailable`, `action_pronoun`,
  `repair_clarify`, `action_world_unknown`, `info_unknown`, `info_world`,
  `info_reference`, `blocked_reference`, `action_referent`). This is a
  measured SUT failure, not a passing result.
- Latest binary live SUT rerun over 74 events: true positive **19**, false
  positive **0**, false negative **31**, true negative **24**, giving precision
  **1.0000**, recall **0.3800**, and F1 **0.5507**. The authority and
  anaphora guards preserve the zero-false-positive boundary.
- Remaining work: broader retrieval/reference/task corpus coverage, recall
  recovery, semantic answer-quality scoring, and live multi-context
  precision/recall beyond the fixed 74-event run.

### Phase 2E — Runtime false-grounding correction

- Replaced the interpretation record's unconditional `candidate_grounded`
  default with a graph-evidence predicate. External topic support now requires
  a held-answer/topic-grounding path or an explicitly resolved referent path;
  unresolved references, unavailable-world requests, unknown topics, and
  unsupported/contradictory parses remain `unresolved` with an empty grounding
  evidence path. Self/faculty routes retain their separate selected-faculty
  evidence, and retrieval remains non-claiming.
- Added a post-retrieval graph refresh so a newly persisted, referent-linked
  `HeldAnswer` can promote the interpretation only after its evidence exists;
  reply text alone cannot promote it.
- Added bounded runtime regressions for the prior false-grounding classes plus
  legitimate held-answer behavior and the three targeted cases. Local `.venv`
  verification: **20 Phase 2 reference/measurement tests passed**, including
  **3 focused regressions**. The post-fix 74-event SUT rerun records **0 false
  positives** (precision **1.0000**) but remains conservative at recall
  **0.3800** (TP 19, FN 31); Phase 2 therefore remains yellow pending recall
  recovery and the four-label post-fix measurement.
- Added provenance-first false-negative categorisation without promoting
  declared paths to evidence. The historical pre-exposure analysis identified
  **16** declared graph paths, **14** declared discourse-state paths, and **9**
  surface/uncertainty-only cases as unverified. The current corpus report now
  exposes **15** verified grounded paths: **8** selected graph faculties and
  **7** `Concept.referent` paths. Recall work remains gated on actual graph
  links rather than labels or reply text.

### Phase 2F — Discourse referent and authority-state increment — 2026-09-23

- Grounded topic readback now writes an explicit `CurrentTopic` paired with an
  in-focus `DiscourseReferent`; later anaphoric comprehension may use that
  state only when the graph binding is present. A direct follow-up probe
  resolved to the grounded `know` path while correctly withholding an answer
  when no causal fact was available.
- Held answers without an `answer_topic` Goal now use the matching
  graph-resident `HeldAnswer` as the production commitment. The `gate` probe
  released `The gate is open.` with a `conversation_information_graph`
  receipt; arbitrary dictionary/source text is not accepted as a substitute.
- Permission evidence is event-scoped. An unrelated authority decision in the
  live graph cannot authorize a new request; missing request-linked authority
  remains `authority_missing` and must fail closed.
- Anaphoric questions now pass through the same production boundary: a bound
  pronoun is not sufficient evidence for a new causal/relational answer, and a
  lexical HeldAnswer for the pronoun cannot escape as an unrelated response.
- Verification: `.venv` targeted bridge/reference tests passed; the latest
  74-event replay measured TP **19**, FP **0**, FN **31**, TN **24** and
  production evidence of **40** released receipts, **34** explicit errors,
  **74** cognitive traces, and **74/74** manifest coverage.

### Phase 2G — Reference-faculty dispatch and committed topic readback — 2026-09-23

- Wired the existing `conversation_action.reference_reply` faculty into the
  live event path. Genuine own-name and manifold-conditioned references now
  cross the same production gate as other substantive replies; no reference
  wording or recognition is invented by the adapter.
- Topic commitments are now restored from graph-resident `HeldAnswer` evidence
  before and after pending retrieval settlement. A later retrieval candidate
  cannot overwrite an already selected grounded topic surface before exact
  production readback.
- The canonical error remains the outcome when no committed graph answer can
  be recovered; the gate was not loosened.
- Local `.venv` verification: complete reference/overfire and topic-tracking
  regression battery **18 passed**. `py_compile` and `git diff --check` passed.
- The post-correction 74-event SUT replay is now measured at TP **22**, FP
  **0**, FN **28**, TN **24**: precision **1.000**, recall **0.440**, F1
  **0.611**. This is an improvement over the prior 19/31 result, but recall
  remains below the Phase 2 exit threshold and the corpus still has no
  memory/learning/cost probes.

### Phase 2H — Grounding/authority separation audit — 2026-09-23

- Permission-shaped communication now records referent grounding and authority
  as separate graph facts when referent evidence is actually present;
  `authority_status="missing"` still blocks production independently.
- Focused `.venv` verification: **40 passed**, including permission,
  reference, topic, and grounding regressions.
- The 74-event replay remains TP **22**, FP **0**, FN **28**, TN **24**;
  recall did not change because the affected corpus events lack the required
  request-linked referent evidence. No recall improvement is claimed from the
  correction; the next increment must add or measure that evidence rather than
  relabel authority-missing events as grounded.

### Phase 7B — Native stress profiles

- Added evaluation-only `fast`, `deep`, `recovery`, and `long_dialogue`
  profiles recording latency, RSS, graph residence, native steps, replay
  equality, and resource ceilings.
- Profile residence: fast **11/9**, deep **34/32**, recovery **22/20**, and
  long-dialogue **42/40** nodes/edges; replay equality held across profiles.
- Verification: native profile suite **3 passed**; adjacent native battery
  **23 passed**. Broader resource envelopes and native-authority audit remain.

### Phase 7C — Dense-neighbourhood native-authority audit

- Added a bounded `dense_graph` profile with twelve candidates and 44
  native-visible edges, exercising a dense graph neighbourhood without
  Python-side outcome selection.
- Added explicit authority evidence to the measurement result: pre-cycle
  graph, native trace/step alignment, native trace as outcome source, and
  post-cycle graph mutation.
- Added regression coverage requiring all candidates to change from
  `resolved=0` to `resolved=1` across the native cycle, with replay, step,
  and graph ceilings preserved.
- Local `.venv` verification: Phase 7 measurement suite **4 passed**.
- Phase 7 remains 🟡: this closes the bounded dense-neighbourhood authority
  increment; broader native-authority coverage and resource envelopes remain.

### Phase 7D — Ambiguity and repeated-gap native envelopes

- Added graph-authored `ambiguity` and `repeated_gaps` profiles to extend the
  native-authority/resource envelope beyond the existing dense, recovery, and
  long-dialogue workloads. Ambiguity contains eight competing evidence-bearing
  candidates; repeated gaps contain eight recurrent gap nodes traversing native
  detect and repair transitions.
- Added assertions for native trace/step alignment, replay equality, graph and
  step ceilings, graph mutation, and complete target-state coverage. Python
  remains an I/O/measurement boundary and does not select outcomes.
- Local `.venv` verification: Phase 7 measurement suite **6 passed**.
- Phase 7 remains 🟡 for broader resource envelopes and additional native
  authority workloads beyond this bounded increment.

### Phase 7E — Broader native resource-envelope loads

- Added bounded `extended_dialogue`, `high_ambiguity`, and `graph_growth`
  profiles. These increase the event/candidate load to 96, ambiguity to 32
  competing candidates, and graph growth to 48 candidates with 144 workload
  edges (152 total canonical edges including native rule edges).
- Added explicit per-profile node/edge/step limits rather than sharing the
  smaller seven-profile ceiling. Each workload still records replay equality,
  native trace/step alignment, graph mutation, and native authority; Python
  performs only I/O and measurement.
- Local `.venv` verification: Phase 7 measurement suite **7 passed**.
- Phase 7 remains 🟡 for full production-scale resource envelopes and broader
  native-authority coverage.

### Phase 8C — Expanded comparative protocol and reference envelopes

- Bound the Phase 8 protocol to the expanded 74-event corpus through
  `evaluation/phase8_corpus_runner.py`; external baselines remain explicitly
  `unavailable` rather than receiving fabricated scores.
- Added reference collection specifications and scorecard scaffolds for ELIZA
  floor, small LLM, modern LLM, base human, and advanced human. Only the ELIZA
  floor has a runnable adapter in this repository; the other four remain
  collection specifications/scaffolds, not measured implementations.
- Corrected the harness to read the authoritative
  `CommunicationInterpretation` node and normalized legacy force aliases for
  measurement only.
- Live report is recorded at
  `evaluation/reports/phase8_corpus_report_20260923.json`; it measures six
  observed dimensions using the declared case denominators across the 74
  events; memory/learning/cost remain unavailable in this corpus.
- Release gate remains **blocked** because external baselines and several
  cognition dimensions are not empirically measured.

### Phase 8D — Deterministic ELIZA-floor adapter

- Added `evaluation/reference_adapters/eliza_floor.py`, a deterministic,
  ordered lexical/reflection adapter that reads only each signal. It does not
  consume corpus labels, create cognitive labels, or claim grounding, action,
  repair, memory, learning, calibration, or cost capability.
- Ran the adapter over all **74** fixed corpus events and recorded one raw
  observation per event, including input tokens, selected rule, captures,
  output, determinism, failure field, and elapsed time. All 74 traces were
  complete and deterministic.
- The fixed protocol permits a measured **provenance = 1.000 (n=74)** result
  for complete adapter traces. All other ELIZA dimensions are explicitly
  `unavailable`; this is not a zero-capability claim.
- Small LLM, modern LLM, base-human, and advanced-human scorecards remain
  `unavailable`. The comparative release gate remains **blocked** because the
  conversational-manifold target and the other baselines are not all
  empirically measured.
- Focused local `.venv` verification: `tests/test_phase8_eliza_floor_adapter.py`
  **5 passed**. JSON validation, Python compilation, and `git diff --check`
  passed for this increment.

### Phase 8E — ELIZA-floor integration in the main corpus report

- Updated `evaluation/phase8_corpus_runner.py` to run the existing deterministic
  ELIZA-floor adapter alongside the SUT and attach its native scorecard plus
  complete case-bound raw adapter provenance under
  `comparison_summary.baselines.eliza_floor`.
- The integrated ELIZA scorecard measures **provenance only**. Interpretation,
  grounding, action, repair, memory, learning, calibration, and cost remain
  explicitly `unavailable`; the small-LLM, modern-LLM, base-human, and
  advanced-human baselines remain unavailable. The comparative release gate
  semantics and blocked status are unchanged.
- Focused local `.venv` verification: **14 passed in 43.28s**, including the
  adapter, comparative-gate, scaffold, and main-report integration contracts.
  No full 74-event replay was run for this increment.

### Phase 8F — Unresolved anaphoric instruction repair — 2026-09-23

- Corrected the live action/repair boundary so an instruction carrying an
  unresolved graph `comp_anaphor` is routed to the existing clarification
  faculty before action enactment. A same-event resolved answer-topic goal
  remains eligible for the specific routed path.
- This consumes neutral parse/discourse evidence and does not add a lexical
  pronoun list or a surface-level action exception.
- Added a regression proving `Move it there.` produces a clarification,
  records `communication_route="ask_back"`, and does not enter the action
  route.
- Local `.venv` verification: focused unresolved-instruction and adjacent
  action/repair tests passed; the new regression passed **1 test**.

### Phases 3–8

- Status: bounded increments through Phase 8C are now implemented; full phase exit gates remain open where marked above.
- Existing foundations must be reused and hardened; duplicate surface-level conversation handlers should not be added.

### Phase 4G — Held-out task-family and asynchronous residual validation

- Added held-out coverage for defer/error, correction, contradiction, topic
  shift, and asynchronous residual evidence. The tests assert native candidate
  provenance, selection/rejection/settlement, counterfactual credit, and
  deep-versus-shallow deliberation rationale from residual/tolerance evidence.
- The held-out cases are event-compatible but not turn-inherent: no message or
  turn identifier is required by the cognitive lifecycle assertions.
- Local `.venv` verification: new suite **9 passed**; combined Phase 4 suites
  **27 passed**. Phase 4 remains yellow pending production-corpus replay and
  broader native workload measurement. The current 74-event report contains
  **0** serialized selected-candidate traces and no deliberation, settlement,
  rejection, or counterfactual fields; generic cognition traces do not satisfy
  this exit criterion.
- Added the graph-resident production trace seam and regression: when a
  `Deliberation` is explicitly linked to an inbound event, the serialized
  cognition trace now carries its candidates, native selections, settlements,
  and counterfactual credit. This is observational only; the live 74-event
  runner still creates no deliberations, so Phase 4 remains open.

### Phase 5G — Heterogeneous recurrence and anti-transfer validation

- Added six opaque task families with competing recurrence priorities from 2
  through 7. The test exercises monotonic priority growth, stable graph
  identities, failed-repair visibility, selected-family route transfer, and
  human-gated promotion.
- A route or promotion from one family is explicitly rejected for every other
  identity; no surface wording is used as the identity or learning decision.
- Local `.venv` verification: Phase 5B–5G focused suite **11 passed**;
  Phase 5G alone **1 passed**. Phase 5 remains yellow pending recurrence over
  the production corpus and broader impact/priority measurement. The latest
  combined Phase 4/5 verification battery passed **42** tests, but no
  production-corpus recurrence trace is yet serialized.

### Phase 6F — Full-corpus production manifest

- Added `evaluation/phase6_production_manifest.py`, a deterministic manifest
  over all 74 communication events. It classifies **65 substantive surfaces**
  and **9 fragment/cognition-only results**.
- Every substantive event must have either a released production receipt or
  the canonical explicit error; arbitrary reply text and `noted` cannot satisfy
  coverage. The manifest never fabricates receipts or releases.
- Local `.venv` verification: manifest suite **10 passed**. Live execution of
  the manifest against production receipts remains the next Phase 6 gate.

- Added strict live-report extraction and `diagnose_live_manifest()`. It
  accepts only serialized released receipts, the canonical explicit error, or
  actual cognitive traces; `trace_coverage` flags and arbitrary reply text do
  not count. Current report diagnostic: **74/74 cognition traces**, **28
  accepted released receipts**, **2 withheld receipts**, **24 explicit errors**,
  and **63/74 accepted events**, leaving **11 substantive events uncovered**.
  Phase 6 remains blocked on receipt/error coverage, not on missing
  observability.

### Phase 6G — Route-specific semantic readback verification — 2026-09-23

- Reconciled the legacy readback assertion with the actual graph-backed route:
  direct legacy readers retain `legacy_structural_readback`, while the live
  `converse` information route records `conversation_information_graph`.
  Both remain behind the same production release gate.
- Local `.venv` verification: production manifest, production gate, legacy
  readback, and output-null battery **32 passed**. This does not close the
  full-corpus semantic recoverability gate.

### Phase 7F — Graph-authored production workload and authority audit

- Added native measurement profiles for Phase 3 asynchronous discourse,
  Phase 4 deliberation, Phase 5 recurrence, and Phase 6 production. Each
  records native steps, replay equality, latency, RSS, graph residence, and
  resource ceilings.
- Local `.venv` verification: native measurement suite **13 passed**. All four
  new profiles satisfy replay/resource assertions. RSS now uses current
-  process-local resident memory rather than contaminated process-wide high
  water. The authority audit scans the current Python cognitive surface and
  now reports **172 unbound Python cycle/task calls** plus **9 explicitly
  native-bound calls**; unbound calls are not counted as native authority.
- Added a focused provenance boundary for the live deliberation bridge:
  Python materializes graph evidence only, while native Phase 4A rules own
  settlement. Focused `.venv` verification: **2 passed**. The broader native
  profile rerun currently has process-local RSS threshold failures; those are
  recorded as resource-envelope debt, not reclassified as authority evidence.
- Phase 7 remains yellow until those decisions are reviewed/migrated or
  explicitly justified and the full production envelope is measured.

### Phase 7G — Live deliberation native-authority boundary — 2026-09-23

- Audited `WorldAdapter._bind_live_goals_and_deliberation` without changing
  the bridge. Its Python work is limited to linking existing discourse/goal
  evidence and materializing complete evidence-bearing graph nodes; valuation,
  collapse, rejection, and `no_candidate` settlement remain native Phase 4A
  rule outcomes.
- Added a narrowly scoped `world_adapter.live_deliberation_bridge` binding to
  `evaluation/native_authority_audit.py`, with explicit provenance,
  `outcome_source=native_rule_readback`, and
  `python_outcome_selection=false` metadata. The audit now includes the exact
  adapter file while preserving all other migration findings.
- Local `.venv` verification: focused authority/provenance tests **2 passed**;
  compile and diff checks passed. A broader selected native measurement run
  had two unrelated process-local RSS threshold failures in existing
  ambiguity/extended-envelope tests; no authority assertion failed.
- Phase 7 remains yellow: this is a bounded authority justification, not a
  claim that the remaining Python cognitive-cycle calls are native-bound.

### Phase 7I — Communication comprehension native execution boundary — 2026-09-23

- Audited `WorldAdapter.comprehend()`: its only cognitive operation is
  execution of the graph-authored communication rules, optionally bounded by
  the graph's `AsyncDaemonCycleBudget`. It does not select a route, surface, or
  cognitive outcome in Python.
- Added an exact native-authority binding with provenance
  `native_rule_readback:communication_comprehension`, boundary
  `graph_rule_execution_only`, and `python_outcome_selection=false`.
- This binds one demonstrated execution boundary only; the remaining audit
  findings remain unbound pending separate evidence and are not silently
  reclassified. The audit now reports **7 bound** and **174 unbound findings**.
- Local `.venv` verification: focused Phase 7 authority/audit battery **4
  passed**; `git diff --check` passed.

### Phase 7J — Native schedule entrypoint authority — 2026-09-23

- Bound `WorldAdapter.tick()` and `dual_process_tick()` as native schedule
  execution only. They invoke the substrate's `default` and `dual_process`
  cycle plans and return native cycle readback; Python does not select a
  cognitive outcome.
- The audit remains conservative: `cognitive_tick()` and `master_tick()` also
  perform Python-side reflex/thread orchestration and remain unbound pending
  separate authority evidence.
- Current native-authority audit: **9 bound**, **172 unbound findings** out of
  181 calls.
- Local `.venv` verification: focused Phase 7 authority/audit battery **5
  passed**; `git diff --check` passed.

### Phase 7H — Native-cycle RSS growth assertion basis — 2026-09-23

- Corrected only the evaluation harness resource assertion: absolute
  `rss_before_bytes`, `rss_after_bytes`, and `peak_rss_bytes` remain recorded
  for observability, while `bounded_rss` now evaluates workload growth via
  `rss_delta_bytes <= resource_limits.rss_growth_bytes`.
- Declared the 100 MiB growth limit, matching the execution plan, and emitted explicit `rss_assertion`
  metadata naming `workload_rss_growth` as the assertion basis; the 1 GiB
  absolute field remains observability-only. Graph, step, replay, and native
  authority limits were unchanged.
- Local `.venv` verification: focused RSS regression **2 passed**; complete
  native measurement module **14 passed in 71.03s**. The focused regression
  includes a synthetic >1 GiB absolute process RSS with 1 MiB workload growth
  and confirms the bounded assertion passes on growth.

### Phase 5H — Production-corpus recurrence measurement — 2026-09-23

- Added `evaluation/phase5_corpus_runner.py`, an evaluation-only adapter over
  the existing graph-native `SelfConcern`, `GapRecurrence`, and
  `GapLearningAssessment` nodes. It preserves graph identity and records
  native node provenance without deriving identities from surface text.
- A single event can cause multiple native settling firings. The evaluator
  deduplicates observations by `(event_id, gap_identity)` while retaining all
  `SelfConcern` node IDs, so internal settling cannot manufacture recurrence.
- Full 74-event replay: runtime measured; **5** graph identities observed,
  each on one event; **0** identities qualified as recurrence. Explicit Phase
  5 learning metadata was absent, so production recurrence is correctly
  reported as `unavailable` with `claim_permitted=false`.
- Local `.venv` verification: Phase 5 corpus runner **3 passed**; full replay
  completed; `py_compile` and `git diff --check` passed. This is measurement
  coverage, not Phase 5 exit acceptance: a learning corpus with explicit
  repeated identity, repair, verification, and review evidence remains needed.

### Phase 2I — Authority/grounding separation rerun — 2026-09-23

- Corrected `_refresh_communication_grounding`: missing permission authority no
  longer prevents independent referent evidence from being read back. A
  supported referent may now be `candidate_grounded` while the separate
  authority gate still withholds production; unsupported permission targets
  retain `authority_missing`.
- Full 74-event SUT replay:
  [`phase8_corpus_report_20260923_phase2i.json`](../../../evaluation/reports/phase8_corpus_report_20260923_phase2i.json)
  records precision **1.00**, recall **0.46**, F1 **0.630**, true positives
  **23**, false positives **0**, and false negatives **27**. The prior replay
  was recall **0.44**, F1 **0.611**, so the change improved recall without
  relaxing the false-positive boundary.
- Local `.venv` verification: permission fail-closed and held-answer grounding
  regressions **2 passed**; the full Phase 2 reference/evidence battery passed
  **40 tests in 623.24s**; full 74-event replay completed successfully.

### Phase 6H — Causal anaphora and explicit-error release boundary — 2026-09-23

- Audited the remaining fixed-string release path. The graph question-response
  route could surface `I don't hold that.` even when no grounded response
  commitment existed; it now remains a canonical explicit error and does not
  mint a released question-response receipt.
- Added a cognition-level relation check for anaphoric reason questions: a
  resolved referent is insufficient to answer why an event occurred. The live
  path now requires an existing substrate `causal_influence` relation before a
  held lexical answer can be released; otherwise the production gate withholds
  it and the caller exposes the explicit error.
- This uses neutral parser relation evidence (`comp_relation_focus="reason"`)
  and existing causal graph structure; it adds no English reply heuristic or
  conversation-only causal store.
- Local `.venv` verification: focused Phase 6 question/information bridge
  battery **13 passed**. The broader Phase 6 gate remains yellow because the
  full 74-event semantic recoverability criterion is still incomplete.

### Phase 2J / Phase 4M — Current full-corpus replay and deliberation readback — 2026-09-23

- Replayed the current implementation over all 74 communication events after
  the authority, causal-anaphora, unresolved-instruction, and explicit-error
  increments:
  [`phase8_corpus_report_20260923_phase2j.json`](../../../evaluation/reports/phase8_corpus_report_20260923_phase2j.json).
- Grounding remains precision **1.00**, recall **0.46**, F1 **0.630**
  (TP **23**, FP **0**, FN **27**). The zero-false-positive boundary is
  preserved; recall remains below the Phase 2 exit criterion.
- Repair state agreement improved from **0.267** to **0.333** and calibration
  agreement from **0.146** to **0.167**. Provenance remains **74/74**.
- Native deliberation readback is now measured for **74/74** events, but every
  event has zero candidates/zero selections. This confirms the observability
  path and the absence of a complete live upstream Phase 4 evidence source;
  it does not count as candidate-generation completion.
- The release gate remains blocked because semantic recoverability and the
  external baseline collection requirements are still unmet.
- Local `.venv` replay completed successfully; no synthetic candidate or
  surface fallback was introduced.

### Phase 8G — Local LLM raw-reference collection — 2026-09-23

- Added `evaluation/reference_adapters/ollama_local.py`, a local-only raw
  collection adapter for the existing `small_llm` and `modern_llm` reference
  classes. It binds every request to a fixed corpus case ID and records the
  model tag, fixed prompt, stdout, stderr, return code, and annotation status.
- Collected a complete small-LLM raw run with installed `gemma3:4b`:
  [`phase8_small_llm_raw_20260923.json`](../../../evaluation/reports/phase8_small_llm_raw_20260923.json),
  **74/74 cases**, zero collection failures. All capability annotations and
  scorecard dimensions remain explicitly unavailable pending blinded review;
  raw text is not cognition evidence.
- A complete modern-LLM raw run was then collected through the local Ollama
  HTTP API with `qwen3.5:9b`, `think=false`, and `num_predict=96`:
  [`phase8_modern_llm_raw_20260923.json`](../../../evaluation/reports/phase8_modern_llm_raw_20260923.json),
  **74/74 cases**, zero collection failures. The HTTP request and response
  JSON are retained as raw provenance; no capability score is inferred.
- Local `.venv` adapter tests: **4 passed**. The comparative release gate
  remains blocked until raw outputs receive independent adjudication and the
  human reference classes are collected.

### Phase 6I — Semantic recoverability mismatch audit — 2026-09-23

- Added `evaluation/phase6_semantic_recoverability_audit.py`, an evaluation-only
  classifier over independent runtime fields. It excludes reply text from
  evidence and separates state, force, and grounding-recall mismatches.
- The current Phase 2J replay is complete at **74/74** observations with **64**
  mismatch cases: state **57**, force **42**, and grounding-recall **27**
  (dimensions overlap). This identifies the next work as cognition/annotation
  adjudication and route reasoning, not surface-string repair.
- Local `.venv` audit tests: **2 passed**. No fallback surface or semantic
  label was changed by this increment.

### Phase 6J — Deferred-goal lifecycle readback correction — 2026-09-23

- Corrected `evaluation/phase8_corpus_runner.py` to read graph-resident Goal
  lifecycle status before mapping an instruction route to `act`. A Goal with
  `status="deferred"` is now measured as `defer`; active goals remain `act`.
  This fixes an evaluation boundary error, not the cognition or its surface.
- The updated replay is recorded at
  [`phase8_corpus_report_20260923_phase2k.json`](../../../evaluation/reports/phase8_corpus_report_20260923_phase2k.json).
  Calibration agreement improved **0.167 → 0.188** and the state mismatch
  count fell **57 → 56**; grounding remains precision **1.00**, recall **0.46**.
- Local `.venv` verification: deferred-goal readback plus existing temporal
  defer regression **2 passed**; full replay completed successfully.

### Phase 4N — Substrate reinvention audit verification — 2026-09-24

- Re-ran the substrate integration audit before selecting the next
  implementation increment. The audit confirms that referent identity, goal
  lifecycle, gap recurrence/learning, thought competition, production gates,
  and native collapse already have substrate authorities available for reuse.
- The executable Phase 4 tuple audit found **0** complete seed-record tuples
  and **0** qualifying near matches. No `DecisionOption`, salience,
  information-commitment, or adaptive-control record is promoted by inferred
  evidence.
- The native-authority audit reports **9** explicitly bound calls and **172**
  unbound Python cognitive cycle/task calls out of **181**. Unbound calls
  remain migration-review debt; they are not silently counted as native.
- Local `.venv` verification of tuple availability, live deliberation
  provenance, native-authority boundaries, and semantic mismatch auditing:
  **12 passed**.
- Audit consequence: the next Phase 4 increment must expose a complete tuple
  from an existing cognitive faculty or preserve explicit `no_candidate`/error
  readback. Defaults, surface-language force heuristics, and parallel
  conversation stores remain prohibited.

### Phase 6K — Neutral-force semantic audit correction — 2026-09-24

- Corrected the evaluation-only semantic recoverability audit to compare the
  corpus's fine-grained labels (`offer`, `refusal`, `correction`) against the
  runtime's declared neutral force ontology using the existing `FORCE_ALIASES`
  boundary. No runtime classifier, language rule, or reply surface changed.
- Added a regression proving that neutral runtime observations for all three
  fine-grained labels produce no false force mismatch. Local `.venv` result:
  **3 passed**.
- Re-reading the current Phase 2K report changes force mismatches from **42**
  to **27**. State mismatches remain **56** and grounding-recall mismatches
  remain **27**; these are still cognition/evidence work, not surface wording.

### Phase 6L — Cognitive-state/release-state separation — 2026-09-24

- Corrected the evaluation boundary so an explicit fail-closed release error
  does not overwrite a graph-resident cognitive state. Runtime route, intent,
  grounding, and goal lifecycle are read first; `release_status` separately
  records `released`, `error`, or `unavailable`.
- Added regressions for repair-under-error and error with no cognitive state.
  Local `.venv` focused verification: **6 passed**.
- Full 74-event replay:
  [`phase8_corpus_report_20260924_phase6k.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6k.json)
  remains correctly blocked, with grounding precision **1.00**, recall **0.46**,
  F1 **0.630**, and **38** explicit errors / **36** released outputs.
- Semantic audit now reports **50** state mismatches (down from 56), **27**
  force mismatches, and **27** grounding-recall mismatches. The remaining
  state errors are not treated as wording debt; they require graph-level route,
  repair, learning, and blocked-goal evidence.

### Phase 2K / Phase 6M — World-support repair integration — 2026-09-24

- Integrated the existing neutral `world_support=missing` comprehension
  evidence into `conversation_action.is_ask_back()`. A well-formed question
  can now enter the existing repair faculty when the substrate lacks an
  attached world; no English cue list, answer fabrication, or new repair
  store was added.
- The existing `repair_evidence=knowledge_deficit` path is also accepted by
  the same faculty. The explicit error surface remains unchanged when repair
  itself cannot produce a response.
- Local `.venv` verification: action/repair, unresolved-instruction, and
  ask-back regressions **4 passed**.
- Full 74-event replay:
  [`phase8_corpus_report_20260924_phase6m.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6m.json)
  remains blocked but explicit errors fell **38 → 34** and released outputs
  rose **36 → 40**. Grounding remains precision **1.00**, recall **0.46**,
  F1 **0.630**; semantic mismatch counts remain state **50**, force **27**,
  grounding recall **27**. The change improves repair release coverage without
  claiming completion of the broader state/grounding gates.

### Phase 2M — Permission-authority scope correction — 2026-09-24

- Corrected the existing permission faculty boundary so authority evidence is
  applied only to interrogative modal-action requests. Declarative
  ability/offer/refusal statements are no longer reclassified as
  `authority_missing` merely because their semantic frame contains a modal and
  an action predicate.
- Missing-world evidence remains a blocked cognition/error boundary, not an
  automatic ask-back or wording fallback. This preserves the explicit error
  invariant and the existing production-withheld contract.
- Local `.venv` permission, production, repair, and unresolved-instruction
  battery: **14 passed**. Full replay:
  [`phase8_corpus_report_20260924_phase2m.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase2m.json)
  remains blocked; grounding precision **1.00**, recall **0.46**, F1 **0.630**.
  The change removes an authority false interpretation but does not claim
  grounding for declarative statements whose graph lacks referent evidence.

### Phase 2N — Grounding-recall false-positive audit — 2026-09-24

- Audited the remaining grounded/partially-grounded false negatives against
  existing Concept definitions and mention bindings.
- Tested a candidate extension that would promote declarative content when a
  mentioned Concept had substantive descriptive attributes. The existing
  false-positive regression correctly rejected this: a lexical Concept is not
  sufficient event-grounding evidence for an arbitrary assertion.
- Reverted the extension and retained the zero-false-positive boundary. The
  audit establishes that the next recall increment must use an event- or
  relation-specific graph path, not lexical Concept presence.
- Verification after reversion: **9 focused tests passed**; `git diff --check`
  passed. No grounding score was inflated by this experiment.

### Phase 2O — Event-predication grounding-source audit — 2026-09-24

- Probed the existing graph-native `reading_collapse._event_predication_graph`
  as a possible source for the remaining grounding false negatives.
- The faculty supplies syntactic event/role predications, but not by itself a
  held fact, common-ground commitment, or grounded world relation. Several
  copular, fragment, and interrogative corpus forms are also parsed
  conservatively or incorrectly for this purpose.
- No integration was made: promoting parse structure to epistemic grounding
  would violate the established zero-false-positive boundary. The next valid
  path must link event predication to an existing commitment/relation node.
- Probe was read-only; existing grounding regressions remain green and no
  score was changed.

### Phase 2P — Event-to-commitment integration search — 2026-09-24

- Searched the existing substrate for event-level grounding authorities. The
  available `reading_collapse` and `situation_model_reader` faculties can
  produce event/role and situation-model structures, but their outputs are not
  automatically linked to a communication event's held fact or common-ground
  commitment.
- The probe therefore does not promote those structures into communication
  grounding or Phase 4 evidence. This preserves the distinction between
  parsed event structure and epistemic support.
- The remaining recall increment is narrowed to a missing event-to-commitment
  integration seam; no safe score-changing patch was justified in this slice.

### Phase 2L / Phase 6N — World-support and anaphora evidence preservation — 2026-09-24

- Preserved existing neutral `language_evidence` fields on the selected
  `CommunicationInterpretation`, including world dependency/support,
  repair evidence, referent status, and authority evidence. This makes the
  evidence available to downstream cognition and evaluation without copying
  surface language.
- Preserved the graph's existing `comp_anaphor` datum on the interpretation so
  a missing world and an unresolved deictic reference are not conflated.
- Blocked/repair readback now uses those evidence fields: missing world support
  is `blocked`; unresolved anaphora remains `repair`.
- Local `.venv` focused verification: **4 passed**. Full replay:
  [`phase8_corpus_report_20260924_phase6o.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6o.json)
  remains blocked, with grounding precision **1.00**, recall **0.46**, F1
  **0.630**, release counts **40 released / 34 explicit errors**, and semantic
  mismatch counts state **47**, force **27**, grounding recall **27**.

### Pre-continuation substrate audit — 2026-09-24

- Re-audited the current source tree, tests, reports, and plan/tracker before
  beginning another implementation increment.
- Confirmed that the repository already owns the relevant mechanisms:
  `DiscourseStore` for referents, `DiscourseState`/`CommonGround` for event
  lifecycle, `conversation_action._bind_goal_to_inbound()` for idempotent goal
  binding, `ThoughtManifold`/Phase 4A for candidate cognition, existing gap
  learning/prioritization, production/readback gates, and native cycle
  scheduling.
- Corrected the earlier audit recommendation: a new goal-binding helper is
  not required and must not be recreated in `discourse_state`; the existing
  helper and tests are the authority.
- Confirmed that `DecisionOption` lacks the complete Phase 4A evidence tuple,
  and that `reading_collapse`/`situation_model_reader` structures do not by
  themselves establish epistemic commitment. Neither is promoted by inference.
- **Plan adjustment:** the next valid implementation target is only a
  mechanical event-to-existing-commitment projection. In the absence of an
  existing held/common-ground/verified relation commitment, the system must
  remain `no_candidate`, repair, or explicit diagnostic error. No new store,
  default evidence, lexical grounding, parse-only grounding, or fixed
  acknowledgment is authorized.
- Documentation updated in
  `CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`.

### Audit consolidation: proposition bridge and event ingress — 2026-09-24

- Independent read-only audits found no justification for another referent
  store, deliberation scorer, gap scheduler, or production gate. Existing
  ownership is now recorded explicitly: `DiscourseStore` owns referent
  identity; `DiscourseState` owns event lifecycle; native Phase 4A owns
  candidate valuation/settlement; production gates own release.
- The genuine missing cognition capability is a structured proposition
  lifecycle connecting neutral semantic evidence to grounded proposition,
  speaker/addressee attribution, epistemic evidence, common-ground
  uptake/challenge/suspension/retraction, and situation-model consequence.
  Action commitment and reply wording are not substitutes.
- The live path remains English-shaped and reply/turn-oriented despite neutral
  substrate components. The plan now requires neutral semantic/semiotic event
  ingress and permits non-turn cognition without forced reply production.
- Existing question-driver, legacy conversation, current-topic, and gap
  prioritization stacks are classified as adapters/parallel scopes requiring
  explicit ownership boundaries, not new implementation targets.
- `.venv` verification of existing reuse seams: **39 passed in 12:31**.
  This is a boundary regression result, not a full-corpus completion claim.
- **Next phase gate:** design and implement the smallest graph-native
  proposition/commitment bridge by reusing existing nodes and native rules;
  preserve `no_candidate`/repair/error when no supported commitment exists.

### Phase 2Q.1 — Neutral semantic-event ingress — 2026-09-24

- Added `WorldAdapter.ingest_semantic_event(...)` as a separate event-only
  ingress. It accepts adapter-produced neutral evidence, creates a
  `SemanticEventFrame`, `CommunicationInterpretation`, and canonical
  `DiscourseEvent`, then lets native arbitration read the evidence.
- The ingress does not call `converse()`, `comprehend_text()`, mint a
  `Message`, infer force from surface language, select a reply, or require a
  turn. `interaction_mode` remains explicit and non-turn events return
  `reply=None`.
- Extended `communication_evidence.from_semantic_frame()` to preserve an
  explicitly supplied neutral proposition payload and to reject unknown
  communicative force instead of silently collapsing it to assertion.
- Local `.venv` verification: semantic ingress plus multilingual neutral
  arbitration **4 passed in 48.33s**; prior reuse-boundary battery remains
  **39 passed in 12:31**.

### Phase 2Q.2 — Explicit proposition evidence bridge — 2026-09-24

- Integrated the delegated `domains.proposition_commitment` bridge. It accepts
  only `neutral_proposition_evidence.v1` with explicit predicate, role-labelled
  arguments, polarity, provider, and evidence id; it records graph-native
  `Proposition`, `PropositionEvidence`, and `PropositionArgument` nodes with
  source-event and attribution edges.
- Surface text, lexical concepts, parse-only predications, unsupported schemas,
  and invalid graph handles are rejected without graph mutation. A proposed
  proposition is not treated as accepted common ground; uptake remains a
  distinct future native lifecycle step.
- Delegated focused verification: proposition bridge **3 passed in 0.20s**.
  Integrated ingress/proposition verification: **11 passed in 109.62s**.
- This phase establishes transport and provenance only. It does not claim
  improved corpus grounding recall until a supported event-to-commitment corpus
  fixture and native uptake/challenge lifecycle are available.

### Phase 2Q.3 — Native proposition uptake lifecycle — 2026-09-24

- Added the self-load-only native seed
  `seeds/proposition_commitment_lifecycle.json`.
- Explicit graph signals now drive native readback transitions:
  `proposed -> accepted`, `proposed -> challenged`, `proposed -> suspended`,
  and `accepted/challenged/suspended -> retracted`. Retraction of a merely
  proposed proposition is rejected by the native guards.
- The seed records `uptake_applied` and uses status guards so repeated rule
  passes are idempotent. Missing or unsupported signals do not transition.
- Corrected the delegated first draft during verification: generic
  `uncertain/rejected` states were not accepted as substitutes for the
  proposition lifecycle, and proposed retraction was removed.
- Local `.venv` native lifecycle verification: **4 passed in 62.96s**.
- This phase still does not claim automatic truth or situation-model change;
  those require a separately evidenced consequence path.

### Phase 2R — Accepted-proposition situation-model projection — 2026-09-24

- Added `apply_situation_consequence()` to the existing proposition bridge as
  a mechanical adapter seam into `domains.situation_model_reader`.
- Eligibility is fail-closed: the proposition must be graph-resident,
  explicitly evidenced, `commitment_status=accepted`,
  `uptake_applied=accept`, `polarity=affirmed`, and carry canonical neutral
  agent/object role arguments. Status alone, missing provenance, negation,
  underspecified roles, and challenged/suspended/retracted propositions do not
  reach the situation model.
- The existing situation-model reader and native event/inference rules own the
  actual world-state transition. The new adapter records a
  `SituationModelConsequence` provenance node and is idempotent on replay.
- This is explicitly an accepted-common-ground projection, not an external
  truth claim. No lexical or surface parser path is used.
- Local `.venv` proposition/lifecycle/consequence battery: **12 passed in
  111.11s**; the complete non-turn ingress → proposition → native uptake →
  situation-model chain adds **5 passed in 81.02s**. The existing situation
model wire suite remains green at **9 passed in 2.50s**. `git diff --check`
and Python compilation pass.

### Phase 2S — Isolated proposition/commitment measurement — 2026-09-24

- Added the separate overlay fixture
  `tests/fixtures/conversational_manifold/proposition_commitment_cases.json`.
  It references no new Phase 0 events and therefore does not inflate the
  74-event grounding corpus or its precision/recall denominator.
- Added `evaluation/proposition_commitment_measurement.py`, which boots a
  fresh graph per case, loads the self-load-only native lifecycle explicitly,
  uses neutral asynchronous ingress, and measures proposition provenance,
  native uptake status, and situation-model consequence projection.
- Four cases cover accepted, challenged, suspended, and negated propositions.
  Accepted uptake yields one supported consequence; challenged, suspended, and
  negated cases fail closed. No reply or surface text participates in scoring.
- Local `.venv` verification: **1 measurement test passed in 66.56s**; the
  combined grounding/bridge/lifecycle/ingress/overlay battery is **24 passed
  in 252.68s**. Overlay report: commitment status accuracy **1.0**,
  consequence projection accuracy **1.0**, provenance complete **4/4**,
  supported consequences **1/4**.
- This is a measurement gate, not corpus grounding improvement. The next
  extension is retraction plus contradiction, multi-referent, ambiguous, and
  no-world cases; Phase 4 still requires a complete native evidence tuple
  before any proposition is promoted to a live thought candidate.

### Phase 2S extension — Lifecycle and boundary coverage — 2026-09-24

- Added `tests/test_proposition_commitment_extended.py` with explicit
  accepted-to-retracted history, retraction without prior acceptance,
  evidence-id conflict replay, malformed multi-referent/duplicate-role
  rejection, ambiguous/no-world/contradicted event boundaries, and equivalent
  cognitive metadata for non-turn and turn-compatible ingress.
- The situation-model adapter now checks the existing reader's typed
  `change_of_state` result before minting `SituationModelConsequence`; an
  accepted proposition for a property, stative, or generic event fails closed
  instead of being relabeled as a state transition.
- Focused local `.venv` verification: **11 passed in 190.47s**. The complete
  dependent Phase 2/3 proposition battery is now **35 passed in 462.52s**.
- This closes the bounded 2S coverage increment. The fixed 74-event grounding
  recall remains unchanged by design; accepted uptake is still not external
  truth and no Phase 4 candidate promotion occurs.

### Phase 3B — Addressee-scoped CommonGround correction — 2026-09-24

- Audit found that `ensure_common_ground()` always selected the first ledger
  attached to a `DiscourseState`; claims addressed to different participants
  therefore leaked into one aggregate ledger.
- Corrected the existing discourse-state authority to reuse/create ledgers by
  explicit addressee scope. Event claim deltas now attach to the addressed
  ledger; unaddressed events use the shared ledger. No second common-ground
  subsystem or proposition lifecycle was introduced.
- Updated the Phase 3 stress assertions to verify separated claims while event
  provenance and goal lifecycle remain unchanged.
- Local `.venv` verification: discourse-state exit suite **5 passed in 0.22s**;
  the dependent Phase 2/3 proposition battery is **35 passed in 462.52s**.
- Compatibility audit: **38 targeted tests passed in 132.61s**. Existing
  unaddressed shared-ledger behavior, explicit proposition common-ground
  handles, idempotence, and legacy callers remain intact. The implemented
  scope is recipient-relative, not full `(speaker, addressee)` pair-relative;
  speakers addressing the same recipient intentionally share that recipient's
  ledger.

### Phase 4P — Proposition-consequence deliberation boundary — 2026-09-24

- Added `tests/test_phase4_proposition_boundary.py` to verify that an accepted
  `SituationModelConsequence` remains situation-model cognition and does not
  itself mint a `ThoughtCandidate` or `DeliberativeCandidate`.
- An incomplete Phase 4 tuple is rejected. An explicitly authored complete
  wrapper is transported once with proposition → consequence → evidence
  provenance intact; native Phase 4 rules still own selection and outcome.
- Local `.venv` verification: **4 passed in 67.74s**. This is a boundary gate,
  not evidence that production events now generate deliberations; the live
  production corpus still lacks complete upstream Phase 4 tuples.

### Phase 6P — Receipt-backed semantic recoverability measurement — 2026-09-24

- Added evaluation-only `evaluation/phase6_receipt_recoverability.py` and
  deterministic tests. It reuses the existing production manifest and
  serialized `ProductionGateReceipt` objects; it does not add parsing,
  routing, or conversation state.
- Events are classified as receipt-backed and semantically recoverable,
  explicit error/withheld, released semantic mismatch, or missing
  authoritative evidence. Semantic decisions use only receipt fields;
  reply text and trace-coverage flags cannot supply meaning.
- Focused local `.venv` verification: **4 passed in 0.14s**. Existing
  `phase6o` 74-event report readback is **74/74 measured**: 31 receipt-semantic
  recoverable, 34 explicit-error/withheld, 9 released receipt-semantic
  mismatches, 0 missing; mismatch dimensions are force 4 and receipt
  multiplicity 5. Runtime state is reported separately: 47 diagnostic
  mismatches in the adapter's heuristic state observation, not receipt
  semantic evidence.
- This strengthens measurement but does not close semantic exit. The remaining
  Phase 6 work is review/correction of the released mismatches and the
  production-scale evidence decision; reply wording is not a repair.

### Phase 2T — Supported event-to-commitment overlay measurement — 2026-09-24

- Added the independent overlay fixture
  `tests/fixtures/conversational_manifold/proposition_event_commitment_cases.json`.
  It is keyed only to existing Phase 0 event IDs; the 74-event corpus remains
  byte-for-byte unchanged and its grounding denominator is untouched.
- Added `evaluation/proposition_event_commitment_measurement.py`, which uses
  the existing neutral ingress, native proposition lifecycle, and typed
  situation-model consequence bridge. It records event identity, proposition
  materialization, explicit uptake/status, provenance, consequence, and
  fail-closed negative stages without using replies or claiming external truth.
- Seven cases / nine event steps cover accepted, challenged,
  accepted-to-retracted, unsupported surface evidence, ambiguous, no-world,
  and conflicting evidence-id paths.
- Local `.venv` verification: **3 passed in 121.50s**; measured results are
  9/9 event identities, proposition materialization **1.0**, commitment status
  **1.0**, consequence projection **1.0**, proposition provenance **5** cases,
  consequence provenance **1** case, fail-closed negatives **4**, reply
  evidence used **false**, external truth claimed **false**.

### Phase 7K — Neutral semantic-event envelope measurement — 2026-09-24

- Added evaluation-only `evaluation/phase7_semantic_event_envelope.py` and
  focused tests. The profile replays challenged, accepted typed-consequence,
  and malformed neutral events through existing semantic ingress.
- It records graph growth, latency, RSS delta, proposition/common-ground/
  consequence readback, no-Message/no-turn/no-reply invariants, malformed
  evidence failure, and fresh-graph replay equality. Python materialization
  and the post-ingress native drain are reported separately; the ingress is
  not falsely labeled wholly native.
- Local `.venv` verification: **4 passed in 45.41s**. Replay is deterministic,
  resource assertions are bounded, accepted `drop(john, glass)` produces one
  typed consequence, challenged state remains challenged, and malformed
  surface evidence creates no proposition or evidence node.
- Direct profile observation: 148 graph nodes / 253 edges added, RSS growth
  62,377,984 bytes (<100 MiB), latency 1,673.11 ms for the three-event
  sequence, and post-ingress drain readback `[0, 0, 0]`. The latency is an
  envelope observation, not a claim that the full path meets the conversational
  soft-real-time target.
- The public ingress does not expose the internal arbitration call's native
  step trace; the profile records a clearly labeled post-ingress drain rather
  than claiming it is the original arbitration trace.

### Phase 5H/5I — Production recurrence evidence audit — 2026-09-24

- Replayed the existing Phase 5 corpus adapter and recurrence authorities
  against the fixed communication fixture. The adapter preserves native
  `SelfConcern.attrs.gap_identity`, `GapRecurrence`, and
  `GapLearningAssessment` ownership; it does not derive identity from surface
  repetition.
- Repeated the `question_unknown` event with both the same and a distinct
  event identifier. Neither produced two graph-native observations for a
  stable gap identity, so recurrence remains unavailable rather than inferred.
- The fixed 74-event communication corpus has no explicit
  `gap_identity`/`learning_stage`/`verification_status` contract. Production
  learning claims therefore remain withheld.
- Local `.venv` verification of the recurrence adapter and Phase 5A–5G
  authorities: **17 passed in 141.70s**. This is a negative evidence gate and
  integration audit; the next valid increment is a separately authored,
  provenance-bearing production-learning fixture, not corpus duplication.

### Phase 4Q — Auditable live deliberation integration failures — 2026-09-24

- Replaced the live Phase 4 bridge's silent exception return with a graph
  resident `CognitiveIntegrationDiagnostic` linked to the inbound message and
  discourse event. It records stage, exception type/message, native-only
  selection ownership, and `surface_fallback=false`.
- The diagnostic is idempotent for the same message/event and does not create a
  candidate or alter native selection. Ordinary unsupported events still
  produce the native `no_candidate` trace.
- Local `.venv` verification of the live bridge, native-authority boundary,
  tuple audit, and forced-failure regression: **11 passed in 188.53s**.

### Phase 6Q — Runtime cognitive-state evidence separation — 2026-09-24

- Extended the Phase 8 observation contract with explicit cognitive-state,
  evidence-source, authority, evidence-availability, and release-state fields.
  Receipt `semantic_intent` remains communicative/action content and is never
  compared directly with `defer`, `repair`, or `blocked` disposition labels.
- The fresh artifact
  [`phase8_corpus_report_20260924_phase6q.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6q.json)
  covers all **74/74** events. State evidence is split into **20** graph
  goal-lifecycle readbacks and **54** interpretation readbacks explicitly
  marked `interpretation_readback_not_disposition`; all 74 have an evidence
  source, but only the goal-lifecycle subset is disposition-grade.
- The pre-fix receipt classification was **29** receipt-semantic recoverable,
  **38** explicit/withheld, **7** released semantic mismatches, and **0**
  missing; runtime-state mismatch count was **47**.
- After the cognition-owned pronoun-target correction and typed authority
  readback correction, the final fresh artifact is **30** receipt-semantic
  recoverable, **38** explicit/withheld, **6** released semantic mismatches,
  **0** missing, and **45** runtime-state mismatches.
- The final runtime-state adjudication splits those 45 diagnostics into
  **38** `disposition_authority_missing` cases, **7** genuine
  `graph_cognitive_state_mismatch` cases, and **29** state matches. The
  `action_pronoun` case now reaches the existing repair faculty instead of
  creating an action goal.
- Local `.venv` verification: **23 passed in 377.24s** for the full Phase 8
  corpus/receipt test battery; focused Phase 6Q contract tests passed **8**.

### Phase 6Q cognition-owned correction — unresolved action pronoun — 2026-09-24

- Corrected the language-adapter evidence boundary so a typed object pronoun is
  retained as the action target instead of being skipped in favor of a later
  adverb (`Move it now` no longer becomes `Move(now)`).
- Unresolved reference evidence now enters the existing clarification/repair
  faculty before an action goal is minted. No referent is guessed and no
  wording-only action repair was added.
- Focused `.venv` verification: **6 passed in 161.09s**. The post-fix fresh
  74-event artifact shows `action_pronoun` routed to repair and improves the
  receipt/runtime metrics recorded above.

### Phase 6R — Typed overlap and partial-event metadata — 2026-09-24

- The live discourse-event bridge now preserves adapter-supplied
  `interaction_relation` and `literal_form` in the event payload. This gives
  native cognition the event relation directly; it does not infer overlap or
  select a disposition from surface text.
- The Phase 8 runner supplies these fields from the versioned corpus metadata,
  and a live bridge regression confirms graph readback for a fragment/overlap
  event.
- Local `.venv` verification: **3 passed in 52.95s**. The remaining seven
  state mismatches are not silently reclassified; the next gate is native
  consumption of this evidence or an explicit adjudication that the corpus
  label is not supported.

### Phase 7L — Production-shaped communication envelope — 2026-09-24

- Added `evaluation/phase7_production_envelope.py`, reusing eight existing
  fixed-corpus events across information, action, reference, overlap,
  correction, social, unavailable-world, and malformed-input strata. No new
  parser, reply policy, or cognitive classifier was introduced.
- The profile records structural graph residence, typed event/interpretation
  readback, explicit error presence, replay stability, and resource evidence;
  reply text is excluded from replay semantics and turn-taking is not required.
- Measured profile: **8/8** observations, **377 nodes / 11,697 edges** added,
  **30,740.9 ms** elapsed, **132,919,296 bytes** total RSS growth, with
  **123,744,256 bytes** attributable to cold start and **9,175,040 bytes** to
  the remaining events; replay is deterministic. Steady-state growth is under
  the 100 MiB bound, but cold start and latency remain open Phase 7 conditions.
- Local `.venv` verification: **3 passed in 92.95s**.

### Phase 5J — Explicit production-shaped learning observations — 2026-09-24

- Added `evaluation/phase5_production_learning_fixture.py` with four typed
  observations over two opaque identities. The fixture supplies explicit
  `gap_identity`, `learning_stage`, and `verification_status`; it never derives
  identity from signal text or repetition.
- Existing native authorities produced two local `GapRecurrence` nodes, each
  with recurrence count **2**, and two `GapLearningAssessment` nodes at
  `human_review` with `auto_promoted=0.0`. No new learning ledger or promotion
  policy was introduced.

### Phase 5K — Verified repair and supervised promotion closure — 2026-09-24

- Extended the fixture with native failed-repair records and one explicit
  human-approved verified retry. The selected opaque identity is promoted with
  `promotion_authority=human_review`; the other remains `human_review`.
- Failed repair is visible for both identities, recurrence/promotion remain
  identity-local, and `auto_promoted=0.0` for every identity.
- Local `.venv` verification: **14 Phase 5 tests passed in 46.04s**, including
  the fixture and Phase 5B–5G recurrence suite.

### Phase 5L — Communication-event learning observation ingress — 2026-09-24

- `WorldAdapter.converse()` now transports validated typed learning
  observations from event context to the inbound message and discourse-event
  payload. The adapter does not derive identity from signal text and does not
  create a learning ledger.
- Added the native `gap_awareness` rule
  `note_explicit_learning_observation`, which creates the existing
  `SelfConcern` with `gap_identity.v1`, learning-stage/verification fields,
  event provenance, and the normal `has_self_concern` ownership edge.
- Live communication regression confirms one stable concern with the supplied
  identity and event provenance. Full Phase 5 fixture/recurrence battery:
  **15 passed in 69.59s**.
- This closes ingress/provenance transport only; impact/priority measurement
  remains the next Phase 5 increment.

### Phase 5M — Live recurrence impact and priority — 2026-09-24

- Two live `converse()` events carrying the same explicit opaque identity now
  produce one native `GapRecurrence` with count **2** and priority **≥2.0**.
  The corresponding assessment remains `human_review` with
  `auto_promoted=0.0`.
- This confirms recurrence impact is graph-native and identity-scoped at the
  communication boundary; no surface repetition participates in the decision.
- Local `.venv` fixture verification: **5 passed in 52.96s**.

### Phase 5N — Competing communication-event learning identities — 2026-09-24

- Replayed two opaque identities through live `converse()` events with native
  recurrence counts **2** and **3**. Their native priorities remained ordered
  by recurrence pressure and each identity retained its own assessment.
- Both assessments remained `human_review` with `auto_promoted=0.0`; no route,
  recurrence, or promotion transferred across identities.
- Local `.venv` fixture verification: **6 passed in 89.07s**.

### Phase 5O — Explicit corpus learning overlay — 2026-09-24

- Added `evaluation/phase5_corpus_learning_overlay.py`, a separately authored
  six-event overlay keyed to existing corpus event IDs. The base 74-event
  corpus remains unchanged and continues to report no learning contract.
- The overlay carries explicit opaque identities and learning-stage/
  verification metadata, then reuses the existing live ingress and native
  recurrence authorities. Three overlay identities each produced native
  recurrence count **2** and priority **2**, with no cross-identity transfer.
- Overlay report:
  `evaluation/reports/phase5_corpus_learning_overlay_report_20260924.json`.
  Native production-recurrence claim is measured for the overlay only; no
  unannotated base-corpus claim is inferred.
- Local `.venv` verification: **3 overlay tests passed in 48.77s** plus the
  existing Phase 5 corpus contract battery (**5 passed in 54.19s**).
- Combined overlay, corpus-contract, live-ingress, and Phase 5B–5G
  compatibility battery: **24 passed in 233.22s**.

### Phase 6S — Native typed partial-event disposition — 2026-09-24

- Integrated the existing `communication_intent_arbitration` seed with typed
  fragment/overlap evidence. Native cognition now records
  `cognitive_disposition=defer` with provenance
  `typed_overlap_partial_event`; no surface route or reply is selected.
- Fresh 74-event replay: **35 state matches**, **39 runtime mismatches**;
  **37** remain `disposition_authority_missing` and **2** are genuine
  `graph_cognitive_state_mismatch` cases (`question_followup`, `error_empty`).
  Receipt semantics remain **30** recoverable, **38** explicit/withheld,
  **6** released mismatches, and **0** missing.
- Local `.venv` verification: **29 passed in 566.43s**; corpus replay
  completed with **74/74** observations.

## 5. Verification gates

| Gate | Required result | Status |
|---|---|---|
| G0.1 | Corpus has cognitive labels, not only expected strings | 🟢 74-event stratified corpus and trace contract pass |
| G0.2 | Trace capture is deterministic with `donkey=0` | 🟡 Focused event trace assertions pass; lifecycle/candidate coverage remains |
| G1.1 | One authoritative interpretation per communication event | 🟢 Focused runtime gate passed |
| G1.2 | Literal form, force, goal, grounding, interaction, and evidence are independently represented | 🟢 Runtime fields, adjudication fixture, and seeded policy verified |
| G1.3 | Adjudicated force/goal agreement reaches ≥95% | 🟢 20/20 = 100.0%; false action/answer/repair = 0 |
| G1.4 | Arbitration consumes language-neutral evidence and survives language variation | 🟢 Spanish/Japanese live LanguageWorld integration passed |
| G2.1 | No unrelated answer can resolve an unknown topic | 🟢 Focused poisoned-candidate regression passed |
| G2.2 | Proposition uptake and consequence projection are measured separately from referent grounding | 🟢 Four-case overlay plus 11 extended lifecycle/boundary tests and seven-case Phase 2T overlay; fixed grounding metrics unchanged |
| G3.1 | Ten-turn mixed dialogue has no orphaned active goals | 🟢 Native mixed-act and asynchronous common-ground stress slices passed |
| G3.2 | CommonGround claims remain scoped to their addressed participant | 🟢 Scoped-ledger correction plus 35-test dependent battery and 38-test compatibility audit; recipient-relative, not pair-relative |
| G4.1 | Candidate generation and native collapse are fully traced | 🟡 Four-family live-manifold generation, native collapse, rejection, execution, settle-back, no-candidate, and repeated counterfactual-credit traces pass; broader task-family coverage remains |
| G4.2 | Accepted proposition consequences cross into deliberation only through a complete authored Phase 4 tuple | 🟢 4 boundary tests passed; native selection and provenance preserved |
| G5.1 | Verified correction changes the intended future route | 🟢 Phase 5A/5B identity, recurrence, and future-route gates passed |
| G6.1 | Every substantive output passes semantic parse-back | 🟡 Phase 6V measures 32 receipt-semantic recoverable releases, 42 explicit/withheld outcomes, and 0 receipt-semantic mismatches; runtime state remains separate with authority gaps and graph-owned disagreements |
| G7.1 | Latency, RSS, graph residence, and replay determinism measured | 🟡 Phase 7L is deterministic and steady-state growth is 9,175,040 bytes, but cold start adds 123,744,256 bytes and the 8-event profile takes 30,740.9 ms; resource/latency targets remain open |
| G8.1 | Baseline comparison report published | 🟡 74-event SUT, ELIZA, local Gemma 4B, and local Qwen 9B raw observations are case-bound by the Phase 8H audit; adjudicated capability scores and human observations remain unavailable, so release gate is blocked |

### Phase 4R — Existing-faculty integration audit — 2026-09-24

- Repeated the substrate audit before the next implementation increment. The
  executable Phase 4 tuple audit remains **0 complete** and **0 near-match**
  seed records; no tuple dimension is inferred from a neighboring faculty.
- Identified reusable partial authorities: `self_dialogue` held graph paths;
  `audience` recipient-relative novelty; `global_workspace` native salience
  and broadcast; `future_option_risk` future residual/escape assessment; and
  the existing gap-prioritization/learning stack for unresolved cognition and
  recurrence.
- Classified these as typed integration seams, not substitutes for Phase 4A:
  salience is not expected value, residual is not consequence, and parse or
  commitment structure is not world grounding without an existing held,
  common-ground, or verified relation.
- **Plan adjustment:** the next increment is a machine-readable partial-evidence
  provenance audit and projection test. Live promotion remains prohibited
  unless one approved faculty supplies all five dimensions. Otherwise native
  `no_candidate` or an explicit integration diagnostic remains the correct
  result.
- Added evaluation-only `evaluation/phase4_partial_evidence_audit.py` and
  `tests/test_phase4_partial_evidence_audit.py`. The audit reports supplying
  faculty, present/missing dimensions, complete-tuple count, eligibility, and
  explicit zero actual promotions; it reads only explicit event-linked graph
  evidence and has deterministic JSON-safe replay. New audit tests: **5
  passed**. Combined Phase 4 battery: **37 passed in 128.96s**.
- Bound the audit into the Phase 8 live observation runner and replayed the
  full 74-event corpus. The current report is
  `evaluation/reports/phase8_corpus_report_20260924_phase4r.json`: **74/74**
  observations, **0** events with typed Phase 4 dimensions, **0** source
  records, **0** complete tuples, **0** eligible promotions, and **0** actual
  promotions; replay determinism is true. Empty `ThoughtManifold` and
  `Deliberation` containers remain native structural/no-candidate traces and
  are not misreported as evidence sources.
- No runtime behavior changed in this audit; no duplicate scorer, scheduler,
referent store, candidate ledger, or surface fallback was added.

### Phase 6T — Receipt mismatch authority audit — 2026-09-24

- Added `evaluation/phase6_receipt_mismatch_audit.py` and a focused regression
  that reads receipt-level provenance without selecting, deleting, or
  rewriting any receipt.
- The 74-event report remains **30** receipt-backed recoverable, **38**
  explicit/withheld, **6** released mismatches, and **0** missing. The six
  mismatches classify as three single-receipt force mismatches, two identical
  duplicate releases, and one competing semantic release pair.
- Report:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924.json`.
  Reply text and trace flags were not used as semantic evidence.
- Local `.venv` verification: **1 focused audit test passed**. Runtime
  correction remains open and must target the producing cognition/release
  authority.

### Phase 6T runtime correction — 2026-09-24

- Added turn/event-scoped idempotence to the existing production gate. It
  collapses identical releases made during one inbound event even when retry
  calls carry distinct transient commitment nodes, while preserving competing
  semantic events for review.
- Corrected the stale production-test expectation for `Move it now.`: an
  unbound pronoun is now explicitly verified as a repair release, consistent
  with the fixed-corpus `action_pronoun` cognition label; no runtime action
  release was forced.
- Targeted Phase 6A/6T verification: **25 passed**.
- Fresh 74-event replay report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6t.json`. Receipt
  readback is now **32** recoverable, **38** explicit/withheld, **4** released
  mismatches, and **0** missing. The remaining mismatches are three
  single-receipt force mismatches and one competing semantic release pair.
- Updated authority audit:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6t.json`.

### Phase 6U — Native partial-event defer/release correction — 2026-09-24

- The existing native `cognitive_disposition=defer` for typed overlap+fragment
  events now controls the release boundary. The adapter no longer releases an
  ask-back repair surface for a partial event; it preserves the graph defer
  state and emits the explicit error floor when no candidate is available.
- Fresh 74-event replay report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6u.json`. Receipt
  readback is **31** recoverable, **42** explicit/withheld, **1** released
  mismatch, and **0** missing. Only `question_ack` retains a competing
  semantic release pair.
- Updated audit:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6u.json`.
- Local `.venv` verification: **20 Phase 6/live-bridge tests passed**; the
  typed partial-event regression is covered explicitly.

### Phase 6V — Authoritative topic-release correction — 2026-09-24

- Audited the remaining `question_ack` competing release to its producing
  path. The topic fulfiller was using `answer_about()` as a retrieval helper,
  but that helper also published a legacy structural receipt before the
  conversation-information bridge published the authoritative
  `answer_topic` receipt.
- Added an explicit `release=False` retrieval mode. It preserves the legacy
  parse-back check and graph-held answer evidence, but leaves communicative
  release to the conversation bridge. Direct legacy callers retain the
  default receipt behavior.
- Fresh 74-event replay report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6v.json`.
- Receipt audit:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6v.json`.
  Results are **32** receipt-backed recoverable, **42** explicit/withheld,
  **0** released semantic mismatches, and **0** missing authoritative
  evidence. No receipt selection was performed and surface text was not used
  as evidence.
- Focused legacy/information/idempotence verification: **13 tests passed**.

### Phase 6W — Runtime-state authority adjudication — 2026-09-24

- Extended the existing runtime-state adjudicator to consume the current Phase
  8 observation schema directly. It reuses graph/evidence fields already
  present in the replay and does not infer state from reply text, receipts, or
  surface wording.
- Adjudication report:
  `evaluation/reports/phase6_runtime_state_adjudication_20260924_phase6v.json`.
  All **74/74** diagnostics are present: **35** state matches, **37**
  interpretation-only `disposition_authority_missing` cases, and **2** genuine
  graph-owned mismatches (`question_followup`, `error_empty`).
- The two graph-owned cases are not silently rewritten. `question_followup`
  lacks the prior discourse context its isolated replay label presupposes;
  `error_empty` lacks an explicit uncertainty evidence field at the adapter
  boundary and is currently routed through an active topic goal. Neither case
  justifies a wording fix; the next cognition increment must either supply
  typed evidence or revise the independent fixture annotation.
- Local `.venv` verification: **3 adjudication tests passed**.

### Phase 7M — Neutral semantic-ingress authority binding — 2026-09-24

- Audited the existing `WorldAdapter.ingest_semantic_event()` boundary. It
  materializes supplied language-neutral evidence and invokes the existing
  `communication_intent_arbitration` rules; it does not choose a force, goal,
  reply, or turn boundary in Python.
- Added an explicit native-boundary record with provenance
  `native_rule_readback:semantic_event_arbitration` and a regression asserting
  `python_outcome_selection=false`. This reuses the existing Phase 7K
  semantic-event envelope and its native lifecycle tests; no parallel ingress
  or classifier was introduced.
- The current static authority audit is now **10 explicitly bound** and **172
  unbound** cycle/task calls. Unbound calls remain review debt; this increment
  does not relabel them.
- Focused Phase 7/6 verification: **12 tests passed**.

### Phase 7N — Production-envelope substrate cost profile — 2026-09-24

- Extended the existing Phase 7L measurement with boot time, per-event
  latency, RSS delta, and graph delta. These fields are diagnostic only and
  are excluded from semantic replay equality.
- Fresh profile:
  `evaluation/reports/phase7_production_envelope_20260924_phase7n.json`.
  Boot was **16,360 ms**; the first information event took **11,693 ms** and
  added **116,801,536 bytes** RSS; later events took **713–3,221 ms** and the
  remaining steady-state growth was **10,231,808 bytes**. Replay remained
  deterministic.
- A graph-type delta audit found the dominant first-event allocation is the
  mechanical `Agent -knows_concept-> Concept` backfill (**10,755** edges),
  not a reply surface or conversational policy. This is an existing substrate
  referent-resolution index and must be optimized at the substrate/index
  layer, preserving the native mention-resolution rules.
- No speculative optimization was applied. The resource/latency exit remains
  yellow until a bounded index implementation and equivalence battery exist.

### Phase 8H — Raw-reference integrity audit — 2026-09-24

- Added `evaluation/phase8_raw_reference_audit.py`, an evaluation-only audit
  that checks fixed protocol identity, all 74 case IDs, duplicates, unknown or
  missing cases, collection failures, and explicit scorecard availability.
- Audited the existing raw reference runs. ELIZA floor, Gemma 4B, and Qwen 9B
  each have **74/74** case-bound observations with no collection failures.
  Base-human and advanced-human references are explicitly **missing**.
- Report:
  `evaluation/reports/phase8_raw_reference_audit_20260924_phase8h.json`.
  Status is **incomplete** (`3 complete_raw`, `2 missing`). No response text
  was interpreted and no capability score was inferred.
- The comparative release gate remains correctly blocked until blinded
  adjudication and human reference collection exist.

### Phase 7O — Substrate integration and reinvention audit — 2026-09-24

- Added the integration audit at
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260924.md`.
- Confirmed reuse points: native `(Concept, name)` lookup, communication
  intent arbitration, discourse state, reflective faculties, topic goals and
  `HeldAnswer`, production receipts, typed partial-event arbitration, and the
  existing partial deliberation faculties.
- Confirmed no new referent store, turn-state machine, self-report generator,
  production ledger, or deliberation scorer is warranted.
- Bounded ordinary ingress now uses the existing concept index; self/meta
  faculties retain their required complete vocabulary ledger.
- Fixed the existing precedence defect where a graph honest-floor response
  shadowed a valid reflective self-organisation readback. This changes
  cognition read-off precedence, not surface wording or production authority.
- Local `.venv` verification: indexed ingress plus two conversation
  compatibility regressions **3 passed**.
- Status: 🟡 — equivalence/resource profiling and the remaining adapter
  authority classification are still required before closing the audit gate.

#### Phase 7O increment — indexed equivalence and scene-authority binding

- Added a two-agent equivalence regression proving indexed ordinary ingress
  and legacy full-ledger ingress produce the same native referent set while
  indexed graph materialization remains bounded.
- Bound the existing conversation-action scene goal `run_rules` readback as
  graph evidence materialization only; no Python outcome selection was added.
- Current audit count: **11 bound**, **171 unbound**, **182 total**. Unbound
  calls remain explicit review debt.
- `.venv`: indexed equivalence **2 passed**; authority battery **6 passed**.
- A one-event production-envelope probe for the optimized ordinary path was
  replay-deterministic, but still measured **11,186 ms** latency and
  **110,010,368 bytes** cold RSS growth with only **342** graph edges added.
  The resource exit therefore remains open as a substrate runtime/warm-up
  issue, not a conversation-surface issue.

## 6. Update rules

- Mark a phase 🟢 only when its exit criterion and tests pass.
- Mark a phase 🟡 when implementation exists but evidence is incomplete.
- Record failures by cognitive category; do not relabel them as style or register issues without evidence.
- Preserve failed traces as regression fixtures.
- Update this tracker in the same change that adds a phase implementation or verification result.

### Phase 7P — Native kind-rule warm-up/readback integration — queued

- Stage tracing isolated the dominant cold allocation in the existing
  `_graph_kind_for()` bridge: complete held-rule serialization to obtain the
  native `sak_kind_*` rules.
- Replaced the separate seed-presence `export_rules()` scan in
  `_ensure_comprehension_seeds()` with the resident graph Rule scan. This
  removed approximately **2.2 s / 31 MB** of separate first-turn cost without
  changing rule authority.
- Remaining kind-rule export cost is approximately **3.9 s / 106 MB** in the
  current probe. The next increment must use selective native readback or an
  explicit boot warm-up; a Python classifier replacement is prohibited.
- Status: queued; Phase 7O resource closure remains yellow.

### Phase 6X — Explicit-failure error disposition — 2026-09-24

- Transported typed `explicit_failure` evidence alongside ordinary
  `explicit_uncertainty`; uncertainty alone remains eligible for repair/defer.
- Added native arbitration for `cognitive_disposition=error` and
  `cognitive_goal=error`, with explicit uncertainty provenance.
- The live adapter now withholds the generic repair/action bridge when the
  native error disposition is present and emits the canonical explicit error.
  No surface token is used as authority.
- The first full replay exposed that treating all uncertainty as error changed
  ordinary defer/repair cases. The rule was narrowed to explicit failure and
  the `error_empty` fixture now carries that distinct evidence.
- Focused `.venv`: **3 tests passed**. Corrected full replay: **36** state
  matches, **37** disposition-authority gaps, **1** graph-owned mismatch
  (`question_followup`); `error_empty` now matches native `error`.
- Report: `evaluation/reports/phase6_explicit_failure_20260924_phase6x_corrected.json`.
- Post-regression recovery battery: **25 tests passed**; the fresh replay is
  `evaluation/reports/phase8_corpus_report_20260924_postregression.json`.
- Full-corpus replay confirmation remains pending; `question_followup` remains
  the separate context-dependent runtime-state mismatch.
- Targeted Phase 8 replay for `error_empty` now matches expected `error` state;
  report: `evaluation/reports/phase6_explicit_uncertainty_20260924_phase6x.json`.
- Status: 🟢 for the Phase 6X focused exit. Phase 6W is adjudicated: the only
  graph-owned mismatch is `question_followup`, whose missing causal world
  evidence is not a conversation-layer defect; the remaining 37 cases lack
  disposition authority rather than proving cognition failure.

### Phase 7P increment — selective native kind-rule readback — 2026-09-24

- Added the Rust/PyO3 `Substrate.export_rules_prefix(prefix)` API and switched
  `_graph_kind_for()` to it for native `sak_kind_*` readback, retaining an
  older-binary fallback.
- Rebuilt the local `.venv` binary. Native API test: **1 passed**.
- `direct_action` replay stayed deterministic; kind-bridge cost improved from
  **3,918.8 ms / 106,143,744 bytes** to about **1,705 ms / 73,453,568 bytes**;
  event latency improved from **9,193.4 ms** to **6,813.0 ms**.
- Report: `evaluation/reports/phase7_kind_readback_20260924_phase7p.json`.
- Cold RSS remains **109,969,408 bytes**, so the resource exit stays yellow;
  remaining work is substrate warm-up/runtime allocation.

#### Phase 7P bounded exit verification — 2026-09-24

- Focused Phase 7 battery covering selective readback, indexed equivalence,
  production envelope, and semantic-event envelope: **11 passed**.
- Native kind authority and replay equality remain green. The cold RSS
  exception is measured and attributed to substrate runtime allocation; no
  Python classifier replacement was introduced.
- Phase 7P: **yellow**. Selective readback is verified, but the declared hard
  resource envelope is still exceeded; the bounded implementation increment is
  complete while the Phase 7 resource exit remains open.

### Phase 7P continuation — conceptualizer output-null authority — 2026-09-24

- The solo alignment audit exposed a remaining Python commitment branch in the
  output-null candidate path: self-target evidence was computed correctly, but
  Python directly minted `Committed` when `recoverable` was true.
- Added the idempotent native rule
  `conceptualizer_output_candidate_commit`. The adapter now materializes the
  candidate and verdict, then reads back the native `Committed` result; it no
  longer selects commit versus withhold in Python.
- This reuses the existing `OutputNullCandidate` / `Verdict` / `Committed`
  vocabulary and leaves `self_target_monitor.score_self_target` as the
  evidence computation. No conversational surface fallback was added.
- Local `.venv` verification: conceptualizer, monitor, output-null, and
  production-gate battery **36 passed**; native-authority focused battery **2
  passed**.
- Native authority census is now **14 bound / 169 unbound / 183 total** and
  remains `review_required`. The increment reduces one direct decision branch;
  the remaining findings and Phase 7 resource envelope are still open.

### Phase 7P continuation — curiosity-topic native settlement — 2026-09-24

- Bound the existing `curiosity_topic_ingest.maintain_topic_interest` native
  settlement path. Python continues to provide only the lexical sensor and
  graph inputs; learning progress and topic-gap minting remain the existing
  native rules.
- Added `NativeCuriosityReceipt` provenance so this boundary is inspectable,
  with `python_outcome_selection=false`.
- Local `.venv`: the native-authority focused test passed; the curiosity
  selection suite passed **5/6**. The remaining test is a pre-existing dirty
  worktree assertion that `runners/dsl/src/py.rs` has no diff; that file is
  already modified by the substrate integration and was not changed here.
- Authority census is now **15 bound / 168 unbound / 183 total**. Status remains
  `review_required`; this is an authority classification increment, not closure
  of Phase 7's resource envelope.

### Phase 7P continuation — cognitive-cycle native boundary — 2026-09-24

- Bound `WorldAdapter.cognitive_tick`'s existing `cognitive_legacy` native
  schedule. The adapter now records `NativeCognitiveCycleReceipt` for the
  native cycle itself; reflex callbacks remain outside this binding and are not
  incorrectly credited as native outcomes.
- Local `.venv` verification: focused native-authority/cognitive-tick battery
  **3 passed**; `git diff --check` passed.
- Authority census is now **16 bound / 167 unbound / 183 total**. Phase 7
  remains `review_required`; this does not close the resource envelope or the
  remaining adapter authority findings.

### Phase 7P continuation — master-cycle native boundary — 2026-09-24

- Bound `WorldAdapter.master_tick`'s existing `master_legacy` native schedule
  with a separate `NativeMasterCycleReceipt`.
- The binding explicitly covers native schedule execution only. Reflex firing,
  thread selection, error capture, and concurrency callbacks remain adapter
  orchestration and are not promoted to native authority.
- Local `.venv` verification: focused native/master/reflex battery **4 passed**;
  `git diff --check` passed.
- Authority census is now **17 bound / 166 unbound / 183 total**. Phase 7
  remains yellow and review-required.

### Phase 7P continuation — live-loop native-cycle delegation — 2026-09-24

- Classified the `live` and `live_examined` adapters' existing
  `cognitive_tick` calls as delegation to the already-bound native
  `cognitive_legacy` schedule. This is deliberately narrower than binding the
  live-loop action gate: world-action authorization and thread/world
  orchestration remain outside the native-cycle claim.
- Local `.venv` verification: focused delegation/authority battery **5 passed**;
  `git diff --check` passed.
- Authority census is now **19 bound / 164 unbound / 183 total**. The audit
  remains `review_required`, with Phase 7 resource and broader authority exits
  still open.

### Phase 7P continuation — actor-goal settlement boundary — 2026-09-24

- Bound `actor_goals.annotate_actor_action`, whose adapter role is to
  materialize structural `ActorAction` facts and invoke the existing native
  actor-goal rules. The native settlement now emits
  `NativeActorGoalReceipt`; Python does not select an actor goal or conflict.
- Local `.venv`: actor-goal migration suite **11 passed**; focused authority
  battery **3 passed**; `git diff --check` passed.
- Authority census is now **20 bound / 163 unbound / 183 total**. This is a
  bounded faculty integration; Phase 7 remains review-required.

### Phase 7P continuation — disclaimer-candidate settlement boundary — 2026-09-24

- Bound `actor_goals.annotate_disclaimer_candidates`: Python emits contiguous
  candidate n-grams mechanically, while the existing agent-authored disclaimer
  codebook rules settle which candidates are meaningful.
- Added `NativeDisclaimerReceipt` with explicit native provenance and no Python
  outcome selection.
- Local `.venv`: focused authority battery **3 passed**; full disclaimer/conflict
  regression suite **7 passed**; `git diff --check` passed.
- Authority census is now **21 bound / 162 unbound / 183 total**. Phase 7 is
  still yellow/review-required.

### Phase 7P continuation — action-pair settlement boundary — 2026-09-24

- Bound `actor_goals.annotate_action_pairs`: structural same-actor/object pair
  enumeration remains mechanical, while opposing-pair and temporal-conflict
  interpretation remains in the existing authored native rules.
- Added `NativeActionPairReceipt` with explicit native provenance and no Python
  outcome selection.
- Focused `.venv` authority test battery: **3 passed**. The full temporal
  regression was stopped after **7:52** at 100% CPU; it reported three
  unrelated/pre-existing failures (seed JSON shape, an authored note fixture,
  and a later pair-coverage assertion) plus a keyboard interrupt. This
  increment did not alter the pair enumeration semantics.
- Authority census is now **22 bound / 161 unbound / 183 total**. Phase 7
  remains review-required; the temporal suite requires separate repair before
  it can be treated as green.

#### Temporal regression data-quality correction — 2026-09-24

- Corrected the persisted `seeds/taught.json` opposing-pair notes from the
  placeholder `x` to the already-documented semantic note. This restores the
  codebook data expected by the temporal reading tests; it does not add a rule
  or surface heuristic.
- Hardened the temporal seed-audit helper to skip valid list-shaped manifests
  rather than treating them as rule dictionaries.
- The isolated temporal tests still exceed the practical runtime envelope and
  were interrupted after roughly 45 seconds without completing; no green
  temporal-suite claim is made. The remaining pair-coverage/runtime issue is
  still open.

### Phase 7P continuation — epistemic assessment boundary — 2026-09-24

- Bound both native `run_rules` passes in
  `actor_goals.assess_epistemic_lean`: detection/structural evidence settlement
  and the epistemic combine band. The Python function only orchestrates those
  passes and reads graph verdicts.
- Added `NativeEpistemicAssessmentReceipt` with explicit native provenance and
  `python_outcome_selection=false`.
- Exact local `.venv` receipt test: **1 passed in 3.22s**. A broader command
  reached **31 passed in 300.85s** before being interrupted because its broad
  selection expression continued into slow suites; it is not used as a green
  full-suite claim.
- Authority census is now **24 bound / 159 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — actor self-authoring execution boundary — 2026-09-24

- Bound `_author_layer_rule`'s post-synthesis native execution. The procedural
  reader, binding resolver, and method synthesizer remain the existing
  self-authoring faculties; the new receipt covers only execution of the
  installed authored rule and does not claim Python semantic authority.
- Added `NativeActorRuleAuthoringReceipt` with explicit provenance.
- Exact local `.venv` verification: **1 passed in 3.34s**; `git diff --check`
  passed.
- Authority census is now **25 bound / 158 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — meaning-inference slot boundary — 2026-09-24

- Bound `meaning_inference.annotate_predication_slots` to the existing native
  selectional-inference rules. Python still extracts grounded predication-slot
  facts mechanically; native rules retain selectional interpretation.
- Added `NativeMeaningInferenceReceipt` with explicit provenance and no Python
  outcome selection.
- Exact local `.venv` verification: **1 passed in 5.26s**; `git diff --check`
  passed.
- Authority census is now **26 bound / 157 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — definitional-inference fact boundary — 2026-09-24

- Bound `meaning_inference.annotate_predication_facts` to the existing native
  definitional-inference rules. Python materializes relational facts; native
  rules retain sense inference and evidence settlement.
- Added the native provenance receipt for this settlement boundary.
- Exact local `.venv` verification: **1 passed in 5.29s**; `git diff --check`
  passed.
- Authority census is now **27 bound / 156 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — morphological-inference candidate boundary — 2026-09-24

- Bound `meaning_inference.annotate_affix_candidates` to the existing native
  morphology rules. Python enumerates structural prefix/suffix candidates;
  native rules retain morpheme interpretation and longest-match settlement.
- Added native provenance receipt without Python outcome selection.
- Exact local `.venv` verification: **1 passed in 5.23s**; `git diff --check`
  passed.
- Authority census is now **28 bound / 155 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — relational-signature inference boundary — 2026-09-24

- Bound `meaning_inference.annotate_relational_signatures` to the existing
  native structural-analogy rules. Python aggregates explicit relational facts;
  native rules retain codebook matching and structural transfer.
- Added native provenance receipt without Python outcome selection.
- Exact local `.venv` verification: **1 passed in 5.37s**; `git diff --check`
  passed.
- Authority census is now **29 bound / 154 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount scene realization boundary — 2026-09-24

- Bound `recount_faculty.project_read_scene` to the existing native recount
  realization/fluency rules. Python materializes the read scene; native rules
  retain event realization and residual decisions.
- Added `NativeRecountReceipt` with explicit native provenance and no Python
  outcome selection.
- Exact local `.venv` verification: **1 passed in 3.38s**; `git diff --check`
  passed.
- Authority census is now **30 bound / 153 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — passive and intent-signal analysis boundaries — 2026-09-24

- Bound the existing `media_analysis` passive-role and intent-signal native
  settlements. Python materializes structural passive/intent facts; native
  rules retain deletion/framing and intent-attribution decisions.
- Added explicit media-analysis provenance receipts for both boundaries.
- Exact local `.venv` verification: **1 passed in 5.17s**; `git diff --check`
  passed.
- Authority census is now **32 bound / 151 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — relational-noun analysis boundary — 2026-09-24

- Bound `media_analysis.annotate_relational_noun` to the existing native
  relational-noun/unsaid-role rules. Python continues to materialize the
  mechanically adjacent nominal evidence; native rules retain relational
  codebook matching and residual-question settlement.
- Added `NativeMediaAnalysisReceipt` provenance for the settlement, with
  `outcome_source: native_rule_readback` and no Python outcome selection.
- Exact local `.venv` verification: **1 passed in 5.20s**; `git diff --check`
  passed.
- Authority census is now **33 bound / 150 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount reasoning boundary — 2026-09-24

- Bound `recount_faculty.recount_what_read`'s instruction-to-reasoning native
  execution to the existing recount communication rules. Article parsing,
  scene projection, and prose production remain their existing faculty/I/O
  responsibilities; this receipt does not promote them to native authority.
- Added a native provenance receipt with explicit `outcome_source` and no
  Python outcome selection.
- Focused local `.venv` receipt test: **1 passed in 0.35s**; `git diff --check`
  passed. The full recount integration test exceeded a bounded 90-second run,
  so it is not claimed as green evidence.
- Authority census is now **34 bound / 149 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount analysis reasoning boundary — 2026-09-24

- Bound `recount_faculty.analyse_what_read`'s analysis-scene reasoning pass to
  the existing native recount analysis rules. The analysis reader continues
  to project already-held readings; native execution remains the authority for
  the resulting reasoning/realization state.
- Added a separate native provenance receipt so surface recount and analysis
  reasoning are not conflated.
- Focused local `.venv` verification: **2 passed in 0.36s** (recount and
  analysis receipt tests); `git diff --check` passed.
- Authority census is now **35 bound / 148 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount analysis-scene boundary — 2026-09-24

- Bound `recount_faculty.project_analysis_scene` to the existing native
  analysis-realization rules. Python remains a type-blind projector of held
  readings; native rules retain frame-slot/realization settlement.
- Added explicit receipt provenance for the analysis scene pass.
- Focused local `.venv` verification: **3 passed in 0.46s** (recount,
  analysis-reasoning, and analysis-scene receipts); `git diff --check` passed.
- Authority census is now **36 bound / 147 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — conceptualizer candidate settlement — 2026-09-24

- Bound `conceptualizer.scan_and_monitor`'s output-candidate native commit
  pass to the existing `conceptualizer_output_candidate_commit` rule. The
  self-target monitor remains evidence production; Python does not select the
  commit outcome.
- Added an explicit candidate-settlement receipt with native provenance.
- Focused local `.venv` verification: **1 passed in 0.39s**; `git diff --check`
  passed.
- Authority census is now **37 bound / 146 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — information-commitment decision boundary — 2026-09-24

- Bound `information_commitment.assess` to the existing native manifold gate.
  Python continues to materialize candidate projections and apply the separate
  external-approval check; native rules retain wait/refine/commit selection.
- Added graph-resident native decision provenance without adding a duplicate
  decision scorer or approval mechanism.
- Exact local `.venv` verification: **1 passed in 0.21s**; `git diff --check`
  passed.
- Authority census is now **38 bound / 145 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — situation-model predication settlement — 2026-09-24

- Bound all four native fixpoint calls in
  `situation_model_reader.ingest_predication` to the existing situation-model
  rules. Python continues to materialize grounded entities/events and
  mechanical indices; native rules retain state-transition and follow-on
  inference settlement.
- Added per-pass native provenance receipts so property, generic-event, and
  change-of-state paths remain distinguishable.
- Exact local `.venv` verification: **1 passed in 2.17s**; `git diff --check`
  passed.
- Authority census is now **42 bound / 141 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — inference-generation relation settlement — 2026-09-24

- Bound `inference_generation._mint_part_of` to its existing native fixpoint
  after mechanical relation materialization. Python writes the graph relation;
  native rules retain downstream inference settlement.
- Added explicit native provenance for the relation pass.
- Exact local `.venv` verification: **1 passed in 0.35s**; `git diff --check`
  passed.
- Authority census is now **43 bound / 140 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — disambiguation and metonymic settlement — 2026-09-24

- Bound `cognitive_disambiguation.coherence_check` and
  `metonymic_redecode` to their existing native coercion rules. Python remains
  responsible for evidence preparation and ledger readback; native rules retain
  role repair and metonymic re-binding decisions.
- Added separate native provenance receipts for coherence and metonymic paths.
- Exact local `.venv` verification: **1 passed in 2.22s**; `git diff --check`
  passed.
- Authority census is now **45 bound / 138 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reflective concern decode boundary — 2026-09-24

- Bound `reflective_faculty.induce_concern` to the existing native
  `shape_decode_loop`. Python continues to ingest the observation and read the
  resulting status; native rules retain recognition/transformation/novelty
  settlement.
- Added explicit native provenance for the concern-decode pass.
- Exact local `.venv` verification: **1 passed in 0.33s**; `git diff --check`
  passed.
- Authority census is now **46 bound / 137 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reflective role and correspondence settlement — 2026-09-24

- Bound `reflective_faculty.check_new_relation_cue_roles` and
  `record_correspondence` to their existing native vocabulary/correspondence
  rules. Python remains mechanical evidence ingestion and verdict readback;
  native rules retain role collision and structural-collapse decisions.
- Added distinct native provenance receipts for both boundaries.
- Focused local `.venv` verification: **2 passed in 32.37s**; `git diff --check`
  passed.
- Authority census is now **48 bound / 135 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reading-drive native-cycle delegation — 2026-09-24

- Bound `reading_drive._tick_reading` as a delegation-only boundary to the
  already verified native cognitive cycle. The reading loop remains a bounded
  steady-state observer; it does not select stage outcomes in Python.
- Focused local `.venv` verification: **1 passed in 3.31s**; `git diff --check`
  passed.
- Authority census is now **49 bound / 134 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — cognitive rule-frame settlements — 2026-09-24

- Bound document reading, situation observation, prediction commitment, and
  private drafting to their existing native rule-frame passes.
- Added distinct native provenance receipts for each cognitive boundary;
  external world action remains outside these private cognition paths.
- Exact local `.venv` verification: **1 passed in 2.09s**; `git diff --check`
  passed.
- Authority census is now **53 bound / 130 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — capability-graph fixpoint settlement — 2026-09-24

- Bound `capability_graph.settle` to the existing native capability fixpoint.
  Python remains graph construction/readback; native rules retain leverage,
  effective-capability, sufficiency, and stage settlement.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 0.24s**; `git diff --check`
  passed.
- Authority census is now **54 bound / 129 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — autonomous-discovery settlement — 2026-09-24

- Bound `autonomous_discovery.settle_native` to the existing native discovery
  rules and recorded provenance directly on the native substrate. This keeps
  the post-submission adapter write guard intact; instrumentation is not an
  adapter-side cognitive write.
- Autonomous-discovery corpus verification: **8 passed in 0.34s**;
  `git diff --check` passed.
- Authority census is now **55 bound / 128 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — analogical correspondence settlement — 2026-09-24

- Bound pair correspondence, directional correspondence, and the legacy
  idempotent native safety pass to existing analogical rules. Python continues
  witness preparation and result readback; native rules retain collapse and
  direction decisions.
- Added native provenance receipts for each correspondence boundary.
- Exact local `.venv` verification: **1 passed in 16.46s**; `git diff --check`
  passed.
- Authority census is now **58 bound / 125 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — procedural referent cross-check — 2026-09-24

- Bound both native passes in `procedural_reader._referent_crosscheck` to the
  existing procedural referent rules: resolution and scratch retirement.
- Added per-pass native provenance receipts; the probe lifecycle remains
  bounded and does not leak conversation `Mention` nodes.
- Exact local `.venv` verification: **1 passed in 16.67s**; `git diff --check`
  passed.
- Authority census is now **60 bound / 123 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — analogy-search settlement — 2026-09-24

- Bound analogy observation and crystallization to their existing native rules.
  Python remains probe/evidence preparation; native rules retain analogy
  emission and identity-field crystallization decisions.
- Added explicit native provenance receipts for both passes.
- Exact local `.venv` verification: **1 passed in 0.28s**; `git diff --check`
  passed.
- Authority census is now **62 bound / 121 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — predictive-reading native-cycle delegation — 2026-09-24

- Bound predictive arc reading and residual-sized dwell processing as
  delegation-only paths to the existing native cognitive cycle. Python remains
  stage setup/readback; native reflexes and graph rules retain anticipation and
  dwell settlement.
- Focused local `.venv` verification: **2 passed in 7.30s**; `git diff --check`
  passed.
- Authority census is now **64 bound / 119 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — cross-text residual re-decode — 2026-09-24

- Bound `cross_text_prior.extend_on_residual`'s post-axis native re-decode to
  the existing `sd_redecode` rule. Python remains feature comparison,
  graph-materialized axis growth, and readback; native rules retain residual
  recognition/re-decode settlement.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 2.15s**; `git diff --check`
  passed.
- Authority census is now **65 bound / 118 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reasoning/CAN correspondence settlement — 2026-09-24

- Bound `reasoning_can_bridge._run_correspondence` to its existing native
  correspondence rules. Python remains name-token preparation; native rules
  retain correspondence settlement into the reasoning/CAN substrate.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 0.35s**; `git diff --check`
  passed.
- Authority census is now **66 bound / 117 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — AST-to-rule native term settlement — 2026-09-24

- Bound `ast_to_rule` expression and body term composition to the existing
  native AST-to-term rules. Python remains AST ingestion and term readback;
  native rules retain graph term construction.
- Added separate native provenance receipts for expression and body passes.
- Exact local `.venv` verification: **1 passed in 1.73s**; `git diff --check`
  passed.
- Authority census is now **68 bound / 115 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — faculty autogenesis settlement — 2026-09-24

- Bound `faculty_autogenesis.pump`'s native discovery pass to the existing
  faculty-autogenesis rules. Python remains evidence serialization and native
  synthesis I/O; native rules retain status, installation, and escalation
  decisions.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 0.82s**; `git diff --check`
  passed.
- Authority census is now **69 bound / 114 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — minting train segment settlement — 2026-09-24

- Bound `minting_train_of_thought.run_minting_train_of_thought` segment
  fixpoints to the existing native minting rules. Python remains segment
  evidence preparation and bounded traversal; native rules retain recurrence
  and settlement decisions.
- Added per-segment native provenance receipts.
- Focused local `.venv` verification: **3 passed in 0.27s**; `git diff --check`
  passed.
- Authority census is now **70 bound / 113 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — solver-dispatch settlement — 2026-09-24

- Bound CAN-network growth and bounded goal-resolution dispatch to their
  existing native rule executions. Python remains evidence preparation,
  scheduling, and readback; native rules retain settlement authority.
- Added typed native provenance receipts without changing the resolver
  selection or outcome semantics.
- Focused local `.venv` verification: **22 passed in 34.54s** across the
  solver-dispatch and natural-language adapter suites. The independent CAN
  growth test remains a pre-existing baseline failure (`grown=False`) even
  without this increment; it is not treated as evidence for the receipt
  change.
- Authority census is now **73 bound / 110 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — fallback-report classification — 2026-09-24

- Bound the fallback readout's existing graph classification pass to its native
  rule set. Python remains counter transcription; the native rules retain
  classification authority.
- Added a typed native provenance receipt without introducing a fallback string
  or conversational repair path.
- Focused local `.venv` verification: **3 passed in 0.50s**; `git diff --check`
  passed.
- Authority census is now **74 bound / 109 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — affect-coordinate readback — 2026-09-24

- Bound `prosody_generation.substrate_affect_coord` to the existing native
  modulator rules. Python configures the drive and reads the resulting affect
  coordinate; it does not compute valence or arousal.
- Added typed native provenance for the affect readback.
- Focused affect verification passed; the suite's independent native-binary
  MD5 discipline check remains red because the current `.so` hash differs from
  its pre-committed canonical hash. This is not caused by the Python change.
- Authority census is now **75 bound / 108 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — upload-text cognitive pump delegation — 2026-09-24

- Bound the upload-text reader's `cognitive_tick` delegation to the existing
  native cognitive schedule. The pump remains mechanical stage progress; it
  does not select or synthesize a conversational outcome.
- Local `.venv` test invocation was dependency-gated: **1 skipped in 0.27s**
  because optional `cv2` is unavailable. No failure was hidden.
- Authority census is now **76 bound / 107 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — foveal salience selection — 2026-09-24

- Bound `fovea_bridge.resolve_fovea` to the existing native
  `ArgminUnique` salience rule and added typed provenance. Python remains
  candidate ingress and graph readback; it does not select the fovea.
- Test collection was refused by the engine-provenance guard because the
  current native binary is stale relative to 18 newer Rust sources. The guard
  was not bypassed.
- Authority census is now **77 bound / 106 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — problem-shape observation decode — 2026-09-24

- Bound structural problem-shape observation to the existing native decode
  rules. Python remains goal-shape extraction and graph ingress; native rules
  retain recognition and growth decisions.
- Focused local `.venv` verification: **3 passed, 5 deselected in 18.33s**;
  `git diff --check` passed.
- Authority census is now **78 bound / 105 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — meta-shape observation growth — 2026-09-24

- Bound meta-shape observation to its existing native growth rules and added
  typed provenance. Python remains signature ingress; native rules retain
  recognition, recurrence, and growth decisions.
- Focused local `.venv` verification: **14 passed in 0.83s**;
  `git diff --check` passed.
- Authority census is now **79 bound / 104 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — rule-dispute settlement — 2026-09-24

- Bound the integrated dispute/self-worth/emotion pipeline to its existing
  native settlement rules and added typed provenance. Python remains evidence
  construction and readback; native rules retain appraisal and outcome
  decisions.
- Focused local `.venv` verification: **2 passed in 0.23s**;
  `git diff --check` passed.
- Authority census is now **80 bound / 103 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — equation isolation settlement — 2026-09-24

- Bound equation solving to its existing native rewrite rules and added typed
  provenance. Python remains equation construction and result readback; native
  rules retain isolation authority.
- Focused local `.venv` verification: **4 passed in 0.22s**;
  `git diff --check` passed.
- Authority census is now **81 bound / 102 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — spatial-belief observation settlement — 2026-09-24

- Bound spatial-belief observation ingestion to its existing native settlement
  rules and added typed provenance. Python remains geometric observation
  preparation; native rules retain occupancy/belief settlement.
- The available Doom integration test could not collect because optional
  `vizdoom` is unavailable; the selected per-area suite contained no matching
  spatial test. No test was bypassed.
- Authority census is now **82 bound / 101 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — disposition trait settlement — 2026-09-24

- Bound trait relaxation, momentary pull, and crystallization to the existing
  native disposition dynamics, with operation-specific typed provenance.
  Python remains evidence/configuration and field readback.
- Focused local `.venv` verification: **5 passed, 25 deselected in 0.59s**;
  `git diff --check` passed.
- Authority census is now **85 bound / 98 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — frame-weight settlement — 2026-09-24

- Bound quantum frame updates and pooled reliability refreshes to their
  existing native weight rules, with separate typed provenance. Python remains
  evidence/request preparation and readback.
- Focused local `.venv` verification: **3 passed, 12 deselected in 0.41s**;
  `git diff --check` passed.
- Authority census is now **87 bound / 96 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — trait-modulator bridge settlement — 2026-09-24

- Bound modulator initialization, trait-to-modulator bias sync,
  modulator-to-trait crystallization, batched trait relaxation, drive
  homeostasis, and personality homeostasis to their existing native rules.
- Added typed provenance for each bridge boundary; Python remains configuration,
  evidence transfer, scheduling, and readback.
- Focused local `.venv` verification: **17 passed, 12 deselected in 1.52s**;
  `git diff --check` passed.
- Authority census is now **94 bound / 89 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — self-worth CAN bridge settlement — 2026-09-24

- Bound resident self-worth initialization/reuse, incident updating, domain
  projection, self-conscious consequence settlement, and peer comparison to
  their existing native CAN rules.
- Provenance receipts are inserted before the native fixpoint so they do not
  perturb the substrate's dirty-tracking/no-op semantics.
- Focused local `.venv` verification: **26 passed in 0.61s**;
  `git diff --check` passed.
- Authority census is now **101 bound / 82 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — native reading-rule validation — 2026-09-24

- Bound all seven native validation passes in `read_method_draft` to explicit
  native-rule provenance. Python remains draft installation, test-instance
  construction, and readback.
- The direct conversational code-growth regression remains upstream-red at
  faculty routing (`no attached world/faculty`), before this validator is
  reached; it is recorded rather than masked.
- Authority census is now **108 bound / 75 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — hate-attribution settlement — 2026-09-24

- Bound understanding incidents and both native passes of hate-incident
  appraisal/evidence settlement to existing native rules. Receipts precede
  each fixpoint to preserve dirty-tracking semantics.
- Focused local `.venv` verification: **19 passed in 0.62s**;
  `git diff --check` passed.
- Authority census is now **111 bound / 72 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — spatial-sense settlement — 2026-09-24

- Bound quanta flood scheduling and spatial navigation settlement to their
  existing native rules, preserving the two-phase convergence schedule and
  graph-owned action decisions.
- Focused local `.venv` verification: **8 passed in 0.32s**; compilation and
  `git diff --check` passed.
- Authority census is now **117 bound / 66 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — ink-decoding settlement — 2026-09-24

- Bound ink lattice forward/backtrace, refinement, and writer settlement to
  existing native rules. Python remains geometry/evidence preparation and
  graph readback; no Python ranking decision was introduced.
- Focused local `.venv` verification: **5 passed, 29 deselected in 0.54s**;
  compilation and `git diff --check` passed.
- Authority census is now **121 bound / 62 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — program-synthesis settlement — 2026-09-24

- Bound program order-lattice forward/backtrace and synthesis fixpoint pumping
  to existing native rules. Python remains mechanical dispatch and readback;
  program-selection decisions remain graph-native.
- Focused local `.venv` verification: **3 passed in 0.32s**;
  `git diff --check` passed.
- Authority census is now **125 bound / 58 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — two-eye super-resolution settlement — 2026-09-24

- Bound retinal sampling and super-resolution fusion to their existing native
  cognitive task/rule execution, with typed provenance. Python remains sensor
  packet/task preparation and reconstruction readback.
- Focused local `.venv` verification: **13 passed, 4 deselected in 0.65s**;
  `git diff --check` passed.
- Authority census is now **129 bound / 54 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — affect/social evidence settlement — 2026-09-24

- Bound resident trust initialization/incidents, self-efficacy incidents,
  shared arousal incidents, and envy deservingness evidence to their existing
  native rules. Python remains evidence ingress and readback.
- Focused local `.venv` verification: **30 passed in 0.74s**;
  `git diff --check` passed.
- Authority census is now **134 bound / 49 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — sensory-selection settlement — 2026-09-24

- Bound sensory kernel selection/discrimination, feature cue selection, and
  modality-reflex training to existing native rules. Python remains field
  ingress and readback; selection remains graph-native.
- Focused local `.venv` verification: **2 passed in 0.77s**; compilation and
  `git diff --check` passed.
- Authority census is now **138 bound / 45 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — 2-D vision task settlement — 2026-09-24

- Bound 2-D retinal sampling and vision-graph convolution task execution to
  existing native task/rule execution. Python remains sensor/task packing and
  readback.
- Focused local `.venv` verification: **9 passed in 0.45s**. The broader
  vision-graph collection remains dependency-limited by missing `cv2`.
- Authority census is now **141 bound / 42 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — world-adapter photon settlement — 2026-09-24

- Bound both world-adapter photon-sheet native task/rule passes to explicit
  cycle provenance. Python remains sensor ingress and percept readback.
- Compilation and `git diff --check` passed. The interactive integration test
  remains dependency-limited because `vizdoom` is unavailable.
- Authority census is now **145 bound / 38 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — program-chunk growth settlement — 2026-09-24

- Bound program-chunk growth's native fixpoint pump to explicit provenance;
  Python remains scan dispatch and readback.
- Focused local `.venv` verification: **1 passed, 10 deselected in 0.27s**;
  compilation and `git diff --check` passed.
- Authority census is now **147 bound / 36 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — grounding and appraisal guards — 2026-09-24

- Bound whisper grounding inference, trait-anxiety classification, Enigma
  crib admissibility, and salience-cache ticking to existing native execution.
- Salience remains delegation-only because disconnected provenance nodes changed
  its existing tale-agency behavior; the receipt mutation was removed. Its
  tale-agency test remains a baseline failure even without that mutation.
- Focused verification for whisper/trait-anxiety/Enigma: **25 passed**; the
  separate native-binary MD5 discipline check remains red. `git diff --check`
  passed.
- Authority census is now **151 bound / 32 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — lifted-rule and extension verification — 2026-09-24

- Bound lifted-rule fixpoint execution and substrate-extension verification to
  native execution boundaries. Extension remains delegation-only because its
  existing verifier changes behavior when disconnected receipt nodes are
  added.
- Substrate-extension verification: **16 passed, 3 baseline failures**;
  teacher-dispatch collection is dependency-limited by missing `requests`.
- Authority census is now **153 bound / 30 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — world identity/enactment settlement — 2026-09-24

- Bound control enactment, cross-frame identity, identity-seam growth, and
  verdict-comparator settlement to existing native rules.
- Cross-frame verification: **12 passed, 5 skipped in 1.24s**. Identity-seam
  verification remains refused by the stale-engine provenance guard.
- Authority census is now **157 bound / 26 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — affective world-model settlement — 2026-09-24

- Bound frustration observation, mood stepping, and harvest/spite decision
  settlement to existing native rules. Python remains world-state ingress and
  readback.
- Focused `.venv` test command completed successfully; `git diff --check`
  passed.
- Authority census is now **160 bound / 23 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — world-discovery settlement — 2026-09-24

- Bound falling-order discovery, Galileo fall discovery, push-mass discovery,
  and physics/lever simulation settlement to existing native rules.
- Physics/Galileo verification: **11 passed in 1.16s**. Falling/mass tests
  remain refused by the stale-engine provenance guard.
- Authority census is now **165 bound / 18 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — perception/world-model boundary settlement — 2026-09-24

- Bound Achieve, agnosia, allocentric-view, Bigville disposition, Bigville
  register, and Marshmallow delay execution to their existing native rules
  with typed provenance. Python remains ingress, orchestration, and readback.
- Focused `.venv` verification: Bigville disposition **8 passed**, Bigville
  register **10 passed**, and allocentric view **19 passed**. Marshmallow
  produced **7 behavioral passes**; its canonical native-binary MD5 discipline
  check remains red, as does the equivalent spite-suite hash check.
- Authority census is now **171 bound / 12 unbound / 183 total**. The twelve
  remaining findings are the Doom ingestion/operation/pattern-eye paths,
  Harvest world, and invariant comparator; Phase 7 remains yellow and
  review-required.

### Phase 7P continuation — complete native authority census — 2026-09-24

- Classified the remaining Harvest, invariant-comparator, and Doom
  ingestion/operation/pattern-eye calls as explicit native delegation
  boundaries. These adapters already perform mechanical ingress/readback; no
  Python outcome selection was added.
- Focused `.venv` verification: Harvest **6 behavioral passes** (one known
  native-binary hash failure), invariant comparator **22 passed / 4 skipped**,
  Doom allocentric **9 passed / 1 skipped**, Doom dual-process **10 passed**,
  Doom predictive priors **9 passed / 1 skipped**, and Doom operate/texture
  **16 passed**. Doom emotion behavior passed; its two failures are canonical
  native-binary/disallowed-runner-diff discipline checks.
- Native authority audit is now **183 bound / 0 unbound / 183 total** with
  status `clean`. This closes the static authority-inventory gate, but does
  not by itself close Phase 7: runtime envelope, artifact provenance, and
  broader cognition exit criteria remain to be verified.

### Phase 7P exit audit — 2026-09-24

- Fresh production-envelope measurement over the fixed eight-event profile:
  replay deterministic, **0 runtime errors**, boot **16,387 ms**, total
  profile latency **46,617 ms**, cold RSS growth **122,265,600 bytes**, and
  steady-state RSS growth **11,411,456 bytes**.
- The cold RSS result exceeds the declared **100 MB** envelope, and the
  measured latency is far above the declared fast/deep limits. The residual is
  attributed to substrate/runtime cold allocation and remains an engineering
  blocker; no surface-language workaround is permitted.
- Added and passed `tests/test_grammar_inversion.py`: **6 focused passes**
  including 100% grammar round-trip recovery and the existing self-target
  monitor. The older `ThoughtSegment -> Committed` deliberative-production
  contract remains open because the live path currently exposes a different
  native deliberation trace and has no causal integration between those node
  types.
- Phase 7 remains open despite the clean **183/183 native authority** census;
  Phase 8 remains blocked on complete target/reference scorecards, especially
  base-human and advanced-human observations.

### Gate 3 contract reconciliation — 2026-09-24

- The legacy `ThoughtSegment -> Committed` label was not the live conversational
  substrate contract. It belongs to autonomous discovery. The conversational
  deliberation authority is the native `DeliberationExecutionTrace` plus
  `DeliberationSettlement` chain.
- Added `tests/test_deliberative_production.py` to establish a grounded
  candidate for one communicative goal, settle it natively, and verify that the
  existing monitor-cleared `Committed` release remains graph-resident for the
  same goal.
- Focused `.venv` verification: **1 passed in 23.27s**. This closes the
  reconciled Gate 3 contract without adding a duplicate thought store.

### Runtime optimization rejection — 2026-09-24

- A native `sak_kind_*` prefix-fixpoint prototype was measured as a possible
  replacement for the selective rule-export boundary in `_graph_kind_for`.
- It was rejected: the live speech-act parity corpus changed instruction
  content and WH-question dispatch, while minimal-boot RSS still grew by about
  **187 MB**. No semantic drift was accepted for a performance optimization.
- The prototype API and live-path use were removed and the native extension was
  rebuilt from the restored source. Future runtime work must preserve held-rule
  parity and target the allocation boundary directly; it must not become a
  language or conversation-level shortcut.

### Existing-faculty comprehension routing correction — 2026-09-24

- Routed the existing `satisfiable` and `honest_no_world` selected dispatch
  paths through their existing faculties in the live adapter. Satisfiable
  self-report results retain their graph-minted goal for the existing
  production bridge. The unresolved plain-statement case continues to expose
  the canonical explicit diagnostic error.
- `.venv` verification: comprehension robustness **9 passed**; conversation
  loop, utterance/conversation unification, output-null, and Phase 6A
  production gates **32 passed**. The handoff-named
  `test_phase6_production_gate.py` is absent in this checkout.
- No Phase 4/6/7/8 acceptance status changes: complete live Phase 4 evidence,
  the measured resource envelope, and base/advanced human references remain
  open.

### Phase 7P continuation — cold comprehension stage attribution — 2026-09-24

- Isolated the Phase 7 kind bridge stages after the selective native readback:
  `kind_signals` took **1,607.6 ms / 66,531,328 bytes** cold and **0.37 ms / 0
  bytes** warm; comprehension seed check took **117.1 ms / 561,152 bytes**;
  native `export_rules_prefix` took **0.28 ms / 0 bytes**; isolated native
  scratch classification took **0.70 ms / 397,312 bytes**.
- A direct first `WordNet.synsets` lookup took **1,635.7 ms** and added
  **61,702,144 bytes**, identifying lazy WordNet loading inside the
  recognition path as the main cold `kind_signals` cost. The native selective
  export was not the remaining multi-second allocation source.
- A one-event warm-up probe moved **1,552.5 ms / 53,657,600 bytes** into boot;
  the first information-question event still took **13,289.3 ms**, added
  **46,931,968 bytes**, and materialized **11,172 edges**. This single-event
  probe does not close the Phase 7 gate or establish a full replay benefit.
- No boot/runtime policy changed. Next: measure a full replay with boot
  warm-up included in the total resource accounting, and separately attribute
  the required question/meta vocabulary backfill before any optimization.

### Phase 7 boot continuation — stream seed manifests — 2026-09-24

- Changed `load_all_seeds()` to retain only the 734-entry seed ID/dependency
  index and source paths, then load each full manifest as it is installed.
  Generated-seed override order and `self_load_only` exclusion are preserved.
- Full-corpus comparison: all **734 IDs**, dependency metadata, and
  topological order match `_read_seeds()` exactly. The streaming boot loaded
  **723 seeds** and produced **24,750 nodes / 11,088 edges**, matching the
  previous instrumented boot totals.
- The full manifest read/index stage measured **2,049.8 ms / 38,842,368
  bytes**, compared with the all-manifests read at **2,169.8 ms / 637,952,000
  bytes**. Full boot RSS growth decreased from **1,549,680,640** to
  **1,457,979,392 bytes** (about **91.7 MB**), with boot time increasing from
  **16.74 s** to **17.89 s** in these runs. The native install stage remains
  about **1.42 GB** after indexing; the overall resource gate remains open.
- Focused `.venv` verification: seed-loader **4 passed**; comprehension plus
  conversation-loop regressions **21 passed**. Full Phase 7 envelope tests
  **4 passed in 135.23 s**. The optional one-event WordNet-prewarm profile
  completed without runtime errors and reported boot-plus-event RSS; it did
  not establish a full replay resource win.
- Next resource increment: profile native seed/rule installation stages and
  reduce retained duplication without changing native rule behavior or seed
  graph equivalence.

### Phase 6W adjudication confirmation — 2026-09-24

> Historical pre-authority-correction result. Its 37/37 label-equality count
> and graph-lifecycle attribution were invalidated by the correction below;
> use the authority-scored report and metrics in the following section.

- The `question_followup` event still carries the high-level goal `learn`, but
  its expected cognitive action is now `repair`: the event has no causal
  closure observation or graph relation supporting an explanation. Its
  referent may still resolve to the prior gate topic; the cause does.
  This is an annotation correction only—no runtime conversation rule was
  added.
- Added the adjudication rationale to the event and a Phase 0 regression for
  the distinction between goal and action. Phase 0/runtime-adjudication tests:
  **11 passed**.
- Fresh 74-event SUT report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6w_adjudicated.json`
  records **74/74** observations. The pre-correction runtime-state readback
  counted **37** label-equality matches and incorrectly attributed the event's
  `repair` label to graph-resident goal lifecycle. The corrected report
  identifies interpretation-only authority instead; see the following
  section for validated counts. Its release state remains `error`, so this does not claim a
  successful repair production. The comparative release gate remains
  `blocked`; human references and measured memory/learning/cost dimensions are
  still unavailable. Latest grounding score remains below target at precision
  **1.00**, recall **0.44**, F1 **0.611**.

### Phase 6W authority/scoring correction — 2026-09-24

- Supersedes the earlier match/gap counts above: those counted label equality
  before checking authority. The corrected adjudicator reports **8
  disposition-authoritative matches, 66 authority gaps, and 0 graph-owned
  mismatches** on the authority-corrected 74-event replay.
- Phase 8 observations preserve raw `observed_state_label_match`, but
  `state_match` is true only for graph/native disposition readback. Action,
  repair, and calibration denominators include only authoritative
  observations, and notes expose coverage. An interpretation-only `repair`
  coincidence (including `question_followup`) is diagnostic, not outcome
  credit.
- Added regression coverage for interpretation-only coincidence and native /
  graph-authoritative matches. Focused Phase 8 checks: **8 passed**.
- Replacement 74-event report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6w_authority_scored.json`.
  It records 8/74 observations with disposition-grade authority and 29
  coincident label matches without it. Action is unavailable (0/9
  authoritative expected-act cases), repair is unavailable (0/16), and
  calibration is measured at 1.00 over 8/49 authoritative cases. The
  `question_followup` label is repair but its `state_match` is false because
  its authority is interpretation-only. Overall release remains blocked.
  Do not cite the earlier `phase6w_adjudicated.json` for disposition score
  claims.
- Follow-up source audit: current native arbitration writes dispositions for
  typed overlap/fragment `defer` and explicit-failure `error`; ordinary
  instruction/ask-back routes only produce interpretation evidence and
  faculty-selected routes/goals, not an explicit native action/repair
  disposition. The next valid closure step is a graph-evidence design for
  native action/repair settlement (including unresolved/failed cases), with
  rule-level negative controls. Do not promote `communication_route`, reply
  text, or evaluator-inferred labels into authority.

### Phase 6X graph-commitment authority replay — 2026-09-24

- `reply_turn_trace` now exposes only event-bound commitments: Goals selected
  by the exact `Goal --comprehends--> inbound` edge, and clarification
  first-pair-parts directly linked by `responds_to`, with `expects_response`
  and the `clarification` speech act. It searches for the commitment itself,
  not only the downstream released surface.
- Phase 8 authority accepts those graph readbacks while continuing to reject
  unrelated/unbound Goals and unlinked clarification surfaces. Regressions
  cover both positive and negative controls; action/repair graph integration
  tests pass **2/2**, and metadata authority tests pass **4/4**.
- Fresh replay:
  `evaluation/reports/phase8_corpus_report_20260924_phase6x_graph_commitments.json`.
  It records **26/74** authoritative observations: **20 matches, 6
  graph-owned mismatches, 48 authority gaps**. Action is **1.00** on 5/9
  authoritative expected-act cases; repair is **0.667** on 9/16; calibration
  is **0.714** on 21/49. This is a coverage increase with newly visible
  disagreements, not a release pass.
- Mismatch rows include `action_world_unknown`, `action_referent`, and
  `blocked_reference` (repair expected, act/blocked observed), plus
  `partial_stream` and `fragment_question` (defer expected, repair observed)
  and `defer_permission` (defer expected, act observed). These now require
  runtime cognition/route investigation; do not reclassify them as evaluator
  gaps or mask them with expected-label edits absent new evidence.

### Phase 6Y native action/repair disposition replay — 2026-09-24

- Native arbitration now maps typed uncertainty plus an unresolved imperative
  dependency to `repair`, and typed non-turn continuation fragments to
  `defer`. The language adapter also emits deferred-condition evidence for
  temporal connectors only when followed by a typed predicate; its
  `Look after the child` negative control remains non-deferred. Native
  disposition readback now takes precedence over adapter-side blocked hints.
- Targeted regressions: **7 passed** across native uncertainty, continuation,
  and Phase 8 disposition precedence; temporal-connector controls: **3
  passed**. The prior graph-commitment integration checks also passed **2/2**.
- Fresh 74-event report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6y_native_action_repair.json`.
  Authority remains **26/74** (coverage gaps 48), but audit improves to **25
  matches / 1 graph-owned mismatch**. Action is **1.00** (n=5, 5/9 coverage),
  repair **1.00** (n=9, 9/16 coverage), calibration **0.952** (n=21, 21/49
  coverage). The sole mismatch is `unavailable_world`: expected `blocked`,
  observed native `repair`. Overall comparative release remains blocked.

### Phase 6Z native world/reference disposition replay — 2026-09-24

- Kept no-scene perception distinct from an unresolved locative reference.
  The language adapter now gives an explicit `world_dependency=perceptual_scene`
  / `world_support=missing` evidence bundle for its no-world route, while
  “over there” is represented as a typed unresolved deictic referent on the
  ordinary instruction path. Native arbitration writes `blocked` for missing
  world support; the typed unresolved instruction rule writes `repair` only
  on the instruction path.
- Focused adapter and native checks passed **2/2**; Phase 8 full replay:
  `evaluation/reports/phase8_corpus_report_20260924_phase6z_native_world_block.json`
  (74 events, release blocked). Runtime-state audit: **28 authoritative
  matches, 0 graph-owned mismatches, 46 disposition-authority gaps**. Both
  `unavailable_world` (native blocked) and `blocked_reference` (native repair)
  now match their corpus expectations.
- Action **1.00** (n=5, 5/9 authoritative coverage), repair **1.00** (n=9,
  9/16), calibration **1.00** (n=23, 23/49). The scorecard remains incomplete
  because 46 observations still lack disposition-grade authority; comparative
  release gate remains blocked.
- Remaining authority gaps by expected state are: **14 defer** (13 statement
  ingress paths plus one authored-concern route), **12 answer**, **7 repair**,
  **4 learn**, **4 act**, **3 blocked**, and **2 error**. Next increment should
  establish event-linked graph commitments for answer/learning and typed
  declarative/update states, without using reply text, fixture labels, or
  route-only inference as disposition authority.
- Prior handoff: audit the **12 answer** and **4 learn** gaps using event-bound
  graph commitments; production reply receipts alone are not disposition
  authority. The answer audit and bounded implementation are recorded below.

### 2026-09-24 — event-bound answer commitment authority

- `reply_turn_trace` now reads two existing graph commitment paths: an
  event-bound `answer_topic` Goal plus agent-held `HeldAnswer` and supported
  `TopicGroundingEvidence`, or a directly linked graph answer Message on a
  response-compatible turn. Topic answers also require causal support where
  applicable; linked responses are rejected when the linked interpretation
  says grounding is unresolved/unknown. No receipt or reply text is used to
  establish disposition authority. Learning settlement remains unimplemented.
- Focused checks passed: answer-authority metadata positive/negative controls
  **2 passed**, supported-answer graph integration **1 passed**, and the
  unresolved-weather one-event control remained unauthorized. The comprehension
  robustness suite passed **9/9**; available production/integration gates
  passed **32/32**.
- Fresh 74-event report (production error-surface gate verified):
  `evaluation/reports/phase8_corpus_report_20260924_phase6zd_error_surface_gate.json`
  (SHA256 `915cfedba34b4e9687080f2f6d577558570cabbfe23e29a713ec4fba4ceeb711`).
  Authority is **34/74**; the audit has **33 authoritative matches, 1
  graph-owned mismatch, 10 matching labels without authority**, and **40
  remaining authority gaps**. Gap counts: defer 14, answer 7, repair 7, act 4,
  blocked 3, error 2, learn 3. Five of 12 expected-answer cases are now
  disposition-authoritative. One of four expected-learning cases is
  authoritative and reveals a real mismatch (`info_explanation`: graph answer
  commitment vs expected learn); do not relabel it to manufacture a match.
- Phase 8 release remains blocked at provenance; human references are
  unavailable and the rest of the cognition/resource gates remain open.
- Next cognition work: adjudicate/repair the graph-owned `info_explanation`
  answer-vs-learn mismatch without changing its annotation; establish genuine
  graph learning settlement for `learn_result` and `learn_uncertain`; then
  address the three learning rows without authority and seven answer rows
  without commitments (five social acts, `question_referent`, and
  `question_source`). Preserve `question_weather` as repair absent causal graph
  evidence that would support a learning or answer disposition.

### 2026-09-24 — diagnostic error withheld from semantic production release

- The production gate now withholds the mandated diagnostic error as a
  semantic release (`diagnostic_error_surface_not_a_release`) while allowing
  the explicit failure surface itself to remain the user's visible output.
  Phase 6A production-gate suite: **13 passed**.
- The fresh report above remains at **34/74** authoritative observations,
  **33 matches**, one graph-owned cognition mismatch (`info_explanation`), and
  10 label matches without authority. For both `info_explanation` and
  `question_weather`, the canonical error is now paired with a **withheld**
  `answer_question` receipt rather than a false released receipt. Comparative
  release remains blocked at provenance.

### 2026-09-24 — native repair for unsupported reason-focused queries

- The adapter records `relation_support=supported|missing` from the typed
  `relation_focus` and the existing graph causal path. The native arbitration
  seed selects `repair` when an information request has `relation_focus=reason`
  and no graph causal support. Answer release/readback now applies the same
  causal evidence requirement to explicit and anaphoric reason queries.
- Negative and positive graph controls pass in
  `test_explicit_reason_question_requires_a_graph_causal_relation`: absent
  causal edge yields `relation_support=missing`, native `repair`, and no answer
  commitment; an existing causal edge is accepted. Combined action-evidence
  and Phase 6A production suites: **26 passed**. The 74-event replay is
  `evaluation/reports/phase8_corpus_report_20260924_phase6ze_native_causal_repair.json`
  (SHA256 `f09e14fd66da4269aa7bea8c86d05501688639902f3f41d674d481d5b145f264`).
- Audit: **35 authoritative**, **34 matches**, **1 graph-owned mismatch**,
  **9 label matches without authority**, **39 authority gaps**. The mismatch
  is `info_explanation` (expected learn, native repair absent causal evidence);
  `question_followup` is now a native repair match. Action **1.00** (5/9
  coverage), repair **1.00** (10/16), calibration **1.00** (24/49). The phase
  remains open; Phase 8 release is still blocked at provenance.
- Next: independently adjudicate the `info_explanation` state contract and
  continue building event-bound learning evidence for `learn_result` and
  `learn_uncertain`; do not infer settlement from declarative wording.

### 2026-09-24 — current Phase 6 authority and release regression check

- Revalidated the current runtime-state adjudicator, production release gate,
  and Phase 8 corpus-runner changes together:
  `.venv/bin/pytest -q tests/test_phase6_runtime_state_adjudication.py
  tests/test_phase6a_production_gate.py tests/test_phase8_corpus_runner.py`
  => **39 passed**. This includes the rule that the mandatory explicit error
  remains the user-visible failure surface but is not counted as a semantic
  production release, and that a matching interpretation label without
  disposition-grade graph authority is still an authority gap.
- The latest supplied 74-event report remains
  `evaluation/reports/phase8_corpus_report_20260924_phase6ze_native_causal_repair.json`:
  **35/74** authoritative dispositions, **34 matches**, one graph-owned
  `info_explanation` mismatch, **9** matching labels without authority, and
  **39** authority gaps. Its incomplete comparative scorecard remains blocked
  at provenance; memory, learning, and normalized cost dimensions are
  unavailable in the fixed corpus. No annotation or reply-surface inference
  was used to manufacture disposition authority.

### 2026-09-24 — connected seed-profile parity expanded and re-opened

- Expanded the Phase 7 comparison beyond coarse output shape to include
  interpretation, discourse/goal traces, referent readback, commitments, and
  production receipts. The eight-event report is
  `evaluation/reports/phase7_seed_profile_parity_20260924_phase7f.json`.
- Result: **1/8 structural matches, 0 errors**. Seven events differ in trace
  referents; `direct_action` also differs in interpretation. Surface text and
  graph identity numbers are excluded from semantic comparison. The earlier
  8/8 coarse parity finding is therefore superseded as evidence of cognitive
  parity; do not filter the differences or broaden the profile until each is
  understood. Expanded comparison also explicitly does not claim replay
  determinism or independent-process resource measurements.
- Root-cause probe: full boot resolves `direct_action` to
  `candidate_grounded` with `CommunicationInterpretation -> Concept.referent`;
  the connected profile is `unresolved` with no evidence path. Full trace
  referents additionally include `north`, `the`, and `it` where the selected
  profile has none. The current provider is the broad `learned_lexicon` seed
  (`seeds/learned_lexicon.json`), not a conversation-specific faculty. The
  Phase 7 test now asserts this concrete knowledge-scope gap rather than
  incorrectly asserting observational equality; the focused regression passed
  (**1 passed in 122.94 s**).
- The connected-profile prepass/cache remains an opt-in optimization only;
  full seed boot remains the default. Next bounded step is to classify these
  referent providers and determine a language-neutral way to expose the
  required lexical content without loading all of `learned_lexicon`; then rerun
  direct-action and unresolved-reference controls before broader parity.
  Phase 7 and the overall upgrade remain open.

### 2026-09-24 — selective lexical content loading restores action grounding

- The cached content-provider pre-pass resolved `open`, `the`, and `north` to
  the large `learned_lexicon` manifest, but the direct-action case did not need
  all 3,917 nodes. Added opt-in exact-name slicing for manifests explicitly
  marked `selective_content_keys`; ordinary/full boots remain unsliced.
  `load_conversation_seed_profile()` accepts upstream content candidates, and
  the comparison harness records slice and closure completeness.
- Focused unit and integration checks: **2 passed**. The report is
  `evaluation/reports/phase7_seed_profile_parity_20260924_phase7g_lexical_slice.json`.
  Three lexical concepts were installed and direct-action interpretation
  (candidate-grounded status and referent evidence path) matches full boot;
  errors: **0**; measured boot-plus-event RSS growth: **352,256 bytes**. This is
  not whole-observation parity: the turn trace still differs in interpreted
  goals and deliberation counts (0/1 structurally equal). Broader event-family
  parity, isolated resource measurement, and production adoption remain open.

### 2026-09-24 — instruction-understanding dependency closes targeted trace parity

- The lexical-only report retained a direct-action turn-trace mismatch: the
  full graph additionally produced an `interpreted_instruction` goal whose
  source was `instruction_understanding`. Added that explicitly relevant
  language-neutral graph faculty to the named conversation profile (60 seeds
  in the closure, up from 59).
- Fresh report:
  `evaluation/reports/phase7_seed_profile_parity_20260924_phase7h_instruction_closure.json`.
  With `open`, `the`, and `north` selected through the content pre-pass, full
  and connected direct-action observations now match **1/1**, including graph
  referent evidence, interpreted goal, and deliberation trace; errors: **0**.
  Resource measurement is a one-event in-process observation, not an
  independently isolated resource-gate result. Focused closure and parity
  tests: **2 passed**. Broader event-family parity and the Phase 7 resource
  gate remain open.

### 2026-09-24 — connected-profile eight-event structural parity

- Replayed the defined eight-event Phase 7 profile with 17 exact content keys
  supplied before boot. The cached pre-pass selected the 60-seed conversation
  closure and sliced `learned_lexicon` to the 12 matching concepts; no
  disposition or interpretation was calculated by the pre-pass.
- Report: `evaluation/reports/phase7_seed_profile_parity_20260924_phase7j_eight_lexical_candidates.json`
  (SHA256 `5cb2e0b2c8deeb87a91605f458797174708058332f70c8e64df1891b48c30f7d`).
  All **8/8 full structural observations match**, with **0 errors**. The
  focused eight-event regression passed (**1 passed in 57.49 s**). Replay
  determinism of this parameterized selection and independent-process RSS are
  not established by the parity report.
- A preceding command omitted `--event-id` and therefore used the 74-event
  default with only the eight-event candidate set (19/74 matched). Its report
  `phase7_seed_profile_parity_20260924_phase7i_eight_lexical_candidates.json`
  is a partial-key 74-event diagnostic, not an eight-event parity result.
  Next: connect lexical candidate production to the pre-boot plan, then measure
  selected and full profiles in independent fresh processes. Phase 7 remains
  open pending those gates.

### 2026-09-24 — isolated Phase 7 profile resource and latency measurement

- Added a one-profile CLI mode so full and connected profiles can be run in
  separate fresh processes. Reports:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_import_attribution.json`
  and `evaluation/reports/phase7_profile_resource_20260924_full.json`.
- Connected profile, eight events, 17 lexical candidates: **133,746,688 bytes
  final RSS**, **107,724,800 bytes growth** against a 100 MiB limit (failed by
  2,867,200 bytes), zero event errors. Full profile: **1,563,488,256 bytes
  final RSS**, **1,537,667,072 bytes growth**. Connected per-event total was
  **1,395 ms**; information question, direct action, unresolved reference,
  and unavailable world each exceeded 150 ms. The first event imported 55
  Python modules and coincided with 33,140,736 bytes additional RSS; this is
  attribution evidence, not proof that imports account for the full delta.
- Result: selective seed loading meaningfully reduces memory and the
  graph-native eight-event observations are equal, but neither the absolute
  <100 MiB runtime requirement nor bounded first-event latency is met. Next
  resource work is to reduce/relocate the first-event import and runtime
  footprint without changing graph decisions, then remeasure from fresh
  processes. The profile remains opt-in; overall Phase 7 stays open.

### 2026-09-24 — bounded self-report and parser cold-path cost

- `_surface_self_state` now constructs the self-account language producer only
  when an identity or compositional frame can use it. The self-organisation
  response is note/area based and bypasses an unused temporary language world.
  Its real conversation regression passed (**1 passed**). The output-null
  commit-rule existence probe now uses the native prefix export when available,
  avoiding serialization of the full rule corpus on each monitor round.
- The internal language parser now opens only its 40 typed chain/meaning/slot
  triples instead of the public constructor's 864-triple permissive grammar;
  public `new_graph()` remains unchanged. The recognition AST gate also caught
  an in-scope regex pattern in `_hypothetical_assumption`; replaced it with the
  existing character-scan token reader, preserving the supported conditional
  evidence. Language, recognition, conceptualizer, and self-organisation
  regression suite: **35 passed**; the counterfactual route regression also
  passed (**1 passed**).
- Fresh eight-event connected profile report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_exact_parser_grammar.json`.
  Peak RSS: **120,754,176 bytes**; boot-plus-event growth: **94,961,664 bytes**
  (within the 100 MiB growth bound, but absolute RSS still fails). Total
  conversation time: **406 ms**, maximum single event **128.7 ms** (under the
  150 ms bound). Full fresh-process baseline report:
  `evaluation/reports/phase7_profile_resource_20260924_full_optimized.json`;
  peak RSS **1,543,512,064 bytes**, maximum event **3,258 ms**. The current
  connected eight-event full-observation parity test passes (**1 passed in
  23.27 s**). At that point this connected workload had not yet been checked
  for repeatability; the following replay entry closes that bounded check.
  Remaining next work is absolute memory reduction and upstream language-neutral
  lexical candidate planning. Full boot remains the default and Phase 7 remains
  open.

### 2026-09-24 — current-native connected-profile refresh

- Re-ran the opt-in eight-event conversation profile from a fresh CLI process
  against the current worktree/native build using the same 17 explicitly
  supplied lexical candidates. Report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_current_native.json`.
- Selection closure is complete; all eight events completed without errors.
  Peak RSS was **120,950,784 bytes**, boot-plus-event growth **95,027,200
  bytes**, total conversation latency **373.4 ms**, and maximum event latency
  **119.0 ms**. Thus growth and per-event latency pass their current bounds;
  absolute RSS still exceeds 100 MiB by **16,093,184 bytes**. This one-process
  run measured resources only; repeatability is separately reported below.
- Current focused Phase 7 profile and seed-loader tests: **18 passed**.
  Automatic lexical candidate production, absolute memory closure, broader
  cognition-family parity, and production adoption remain open; full boot
  remains the default.

### 2026-09-24 — connected-profile replay determinism

- Extended `measure_production_envelope()` and the one-profile CLI to pass the
  same explicit content-key selection to both replays. Added a harness
  regression for that contract and a `--verify-replay` CLI option. The replay
  run reports determinism but does not claim independent-process resource
  measurements.
- Eight-event result:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_replay.json`;
  `replay_equal=true`, selection complete, eight events, zero errors. The
  connected-profile parity regression and replay-argument regression passed
  (**2 passed in 23.36 s**). Candidate keys remain manually supplied; this
  closes repeatability for that exact selected workload, not the broader
  connected-profile or resource gates.

### 2026-09-24 — connected-profile first-event RSS attribution

- Re-read the current fresh-process report and confirmed the exact profile is
  **68 selected seeds**, not 60. It contains the 17 core seed anchors, 29
  named conversation anchors, and the indexed transitive dependency/content
  closure. Updated the current Phase 7 summary; earlier dated counts remain
  historical snapshots.
- Current report breakdown:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_current_native.json`.
  Boot reaches **95,760,384 bytes** from **25,923,584 bytes** baseline. The
  first `information_question` event adds **18,485,248 bytes** RSS while
  adding **188 graph nodes / 575 edges** and importing **52 modules**. The
  event takes **119.0 ms**. Later individual event RSS increases are at most
  **2,318,336 bytes**.
- A one-event `tracemalloc` snapshot comparison reports about **2.92 MB** net
  Python-heap growth across the same booted-agent event. This leaves the larger
  RSS delta unexplained by tracked Python allocations; it is not yet proven to
  be one native allocation source (RSS also includes resident shared mappings).
- Instrumented the same event's **10** `run_rules` calls in a separate fresh
  process: the largest observed call-level RSS increase was **196,608 bytes**;
  the sum of positive sampled deltas was **327,680 bytes**. This argues against
  one rule-settlement call being the dominant 18.5 MB jump, but sampling does
  not rule out allocation between calls or allocator/page effects. Next
  resource work should trace adapter graph construction and import/resident
  module costs before attempting a semantic-path change. No seed was removed
  or split on per-seed RSS deltas because allocator/page reuse made those
  measurements non-additive.

### 2026-09-24 — connected pre-pass closes first-turn seed loads

- The first-turn `_ensure_comprehension_seeds()` checked only graph `Rule`
  nodes, although manifests install the relevant rules in the native compiled
  rule store. This made a connected boot miss already-loaded rules and reload
  **24** selected seed manifests. Four further first-turn requirements were
  outside its anchor set: `composer_dispatch`, `conversation_deliberation_phase4a`,
  `conceptualizer`, and `minting_recurrence_ledger`.
- Changed the guard to probe exact names through native
  `export_rules_prefix()` (with the former graph-node compatibility fallback)
  and added the four missing anchors. The connected profile now selects **72**
  seeds; an instrumented fresh first information event made **zero** additional
  `load_seed_manifest` calls. Focused regression and eight-event full structural
  parity pass, alongside the explicit content-key replay input regression:
  **3 passed in 27.18 s**.
- Fresh resource report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_prereload.json`;
  peak RSS **118,181,888 bytes**, growth **92,241,920 bytes**, total event
  latency **384.4 ms**, maximum event **101.1 ms**. The zero-lazy-manifest
  change lowers peak RSS by **2,768,896 bytes** from the preceding connected
  run, but absolute RSS remains **13,324,288 bytes** over 100 MiB.
- Candidate-aware repeat report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_prereload_replay.json`;
  eight events, 72 selected seeds, selection complete, zero errors,
  `replay_equal=true`. As before, this is two adapter runs in one fresh process,
  not independent-process resource measurement. General cognition and release
gates remain open.

### 2026-09-24 — current speech-act parity regression remains open

- Current worktree verification of
  `tests/test_speech_act_parity_migrated.py` exposed three failures (also seen
  when run with `tests/test_native_selective_rule_readback.py`): captured
  signal drift for “Focus on the reading work.”, eight live-path differences,
  and a canonical rule inventory assertion that omits the manifest's existing
  `sak_kind_instruction_from_input_evidence` rule. The profile/readback change
  does not alter the speech-act seed or signal parser, but its interaction with
  the live parity failure has not yet been ruled out. Attribution and repair are
  pending; do not update frozen corpus expectations merely to turn these checks
  green.

### 2026-09-24 — Existing-faculty routing verification

- Verified the bounded comprehension-routing correction recorded in the
  progress tracker: `tests/test_comprehension_robustness.py` **9 passed**;
  conversation loop, utterance unification, output-null, and Phase 6A
  production-gate tests **33 passed**.
- The handoff's `tests/test_phase6_production_gate.py` path is absent in this
  checkout; it was omitted. The targeted diff check passed.
- This closes verification of that routing increment only. The speech-act
  parity, Phase 6 evidence coverage, Phase 7 resource, and Phase 8H human
comparative gates remain open.

Current-code recheck: full v5 Phase 8
`evaluation/reports/phase8_corpus_report_20260925_typed_receipt_error_terminal.json`
still has 49/74 authoritative dispositions, grounding F1 .507, and zero Phase
4 promotions, while both standalone assertions release the intended neutral
receipt. Full connected Phase 7
`evaluation/reports/phase7_profile_resource_20260925_typed_receipt_error_terminal.json`
is deterministic/error-free but exceeds absolute limits (108,519,424-byte peak
RSS; 1,221.7-ms maximum event). Growth bounds pass; absolute resource and all
other open cognition/production/evaluation criteria remain outstanding.

### 2026-09-24 — Speech-act rule inventory parity

- Corrected the canonical round-trip test inventory to include the existing
  `sak_kind_instruction_from_input_evidence` manifest rule. No runtime rule,
  signal, or frozen corpus annotation changed.
- `.venv/bin/pytest -q
  tests/test_speech_act_parity_migrated.py::test_seed_rules_canon_roundtrip`:
  **1 passed**.
- Phase 1 remains open: the frozen “Focus on the reading work.” signal and
  multiple live-path mismatches still require evidence-based adjudication.

### 2026-09-24 — Speech-act live mismatch source recheck

- Fresh `.venv/bin/pytest -q --tb=short
  tests/test_speech_act_parity_migrated.py::test_live_parity_end_to_end`:
  **failed with eight differences**: argument/content selection for “look left”,
  “move north”, “Promote the first concern.”, “look left then quorplezap the
  door”, and “Stop working on that.”; “Focus on the reading work.” is classified
  as an instruction rather than the captured statement; and the “knowledge
  gaps” / “in the image” questions take `frontier` instead of captured `table`.
- The Focus signal source is now identified: committed
  `wiktionary_reference._POS_OVERRIDE_EN` forces `focus` to `verb`, while the
  installed Wiktionary POS slab lists both `noun` and `verb`. The live
  “Focus…” wording is plausibly imperative, so neither that override nor the
  legacy capture label is changed without independent adjudication.
- These remain a mix of behavioral differences and likely legacy-capture drift,
  not a verified uniform parser regression. Keep Phase 1 open; do not rewrite
  frozen expectations to claim parity.

### 2026-09-24 — Typed instruction-target correction

- Fixed a shared language-adapter extraction defect: a POS-ambiguous
  prenominal modifier followed by a noun-dominant head now retains its
  adjective reading; action evidence skips adjectival modifiers and prefers a
  typed anaphoric oblique over an intervening gerund. This corrects
  “Promote the first concern.” to target `concern` and “Stop working on that.”
  to target `that`, without adding phrase-specific command rules or changing
  graph/native disposition authority.
- Focused `.venv/bin/pytest -q tests/test_action_evidence_and_defer.py`:
  **17 passed**. The separate comprehension robustness + instruction suite was
  **17 passed / 2 failed** in existing full-boot self-concern and unknown-head
  teacher-request assertions; those paths are not covered by this correction.
- The refreshed legacy live-parity replay still fails with nine differences.
  The `Stop working on that.` target now matches the capture; the new typed
  target `concern` and self/anaphoric targets intentionally differ from its
  old raw-span content values. Other route/kind differences remain unresolved.
  This does not close Phase 1 or claim full parity.

### 2026-09-24 — Graph-meta route precedence over incidental spatial evidence

- Preserved an explicitly selected `meta` question-table target as a
  graph-faculty route in both comprehension dispatch and grounding readback.
  A broad spatial-PP signal no longer vetoes the self-gap faculty for “What
  gaps do you have in your knowledge?”; the non-meta “What is in the image?”
  remains frontier/unresolved without image/world support. The result is
  grounded by the selected faculty, not by the question's surface or reply.
- Added positive/negative routing assertions. `.venv/bin/pytest -q
  tests/test_action_evidence_and_defer.py`: **19 passed**; compilation and
  `git diff --check` passed. A fresh full-boot `converse()` integration check
  for the exact self-gap question also passed (**1 passed**), verifying the
  selected table route, `candidate_grounded` status, graph-faculty evidence
  path, and a non-error response.
- Full Phase 2 grounding/reference suite: **28 passed in 486.63s**. Existing
  unresolved-world and unsupported-reference controls remain green under the
  new meta-faculty precedence.
- Fresh legacy live-parity replay now has **eight differences** (down from
  nine): the “knowledge gaps” dispatch difference is resolved; “in the image”
  still correctly refuses the table route without world support. Other legacy
  content/kind differences remain; Phase 1 stays open.

### 2026-09-24 — Conversation-profile resource revalidation

- Re-ran the eight-event conversation profile with replay verification against
  the current parser and graph-meta routing. The fresh report is
  `evaluation/reports/phase7_profile_resource_20260924_conversation_postsemanticfix.json`:
  72 seeds selected, closure complete, zero errors, and deterministic replay.
- Peak RSS was **118,255,616 bytes** (about 112.8 MiB), exceeding the 100 MiB
  absolute cap by about **13.4 MiB**. Boot-plus-event growth was **92,246,016
  bytes**; cold first-event growth was **15,421,440 bytes**; steady-state
  growth after the first event was **6,774,784 bytes**. Relative-growth and
  steady-state assertions pass; the absolute resource gate remains open.
- This revalidation is two adapter runs in one process, not an independent
  process replay/resource measurement. No seed capability or profile scope was
  removed to improve the number. Phase 7 and overall cognition completion stay
  open; the pending next step is evidence-guided RSS reduction, followed by a
  fresh independent-process replay/profile check.

### 2026-09-24 — Independent connected-profile resource repeats

- Repeated the same eight-event, 17-content-key connected profile twice, once
  per fresh Python process, without `--verify-replay`. Reports:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_independent_a.json`
  and `evaluation/reports/phase7_profile_resource_20260924_conversation_independent_b.json`.
- Both runs selected the same complete 72-seed closure, recorded all eight
  events with zero errors, and produced byte-identical canonical observation
  arrays (SHA256 `0ea98838ee74c42b60bf4bf7fd1a33a00e5d3fedf77c3161fbdbe36a4e98dd69`).
  This supplies independent-process semantic replay evidence in addition to
  the earlier same-process replay check.
- Absolute peak RSS was **118,292,480 bytes** and **118,308,864 bytes** in the
  two runs (both ~13.4 MiB above the 100 MiB cap). Boot-plus-event growth was
  **92,319,744 bytes** and **92,307,456 bytes**; all relative-growth checks
  passed and the absolute-RSS assertion failed in both. Maximum event latency
  was 132.2 ms and 96.6 ms, respectively. Independent replay is now evidenced;
  the resource gate is not closed. Continue with attribution and a capability-
  preserving reduction, rather than treating the passing relative bound as
  sufficient.

### 2026-09-24 — Defer evidence-gated pragmatic model imports

- `domains/audience_driven_production.py` no longer imports the foreign-system
  model stack at module load when the interlocutor is unobserved, and defers
  the pragmatic speaker/listener stack and NumPy until the grounded-audience
  argmax path is actually entered. Seed/content boot remains eagerly resolved
  by the connected dependency pre-pass; this only avoids importing runtime
  machinery that the ungrounded evidence path explicitly does not execute.
- Audience-production and conceptualizer suites: **35 passed**. Two independent
  fresh-process runs of the same eight-event, 17-key profile selected the full
  72-seed closure, had zero errors, and produced identical canonical
  observations (SHA256
  `0ea98838ee74c42b60bf4bf7fd1a33a00e5d3fedf77c3161fbdbe36a4e98dd69`).
- Peak RSS was **116,846,592 bytes** and **117,030,912 bytes**, improving over
  the immediately preceding independent runs by about **1.3–1.5 MB**. Cold
  event growth fell from ~15.1 MB to ~13.9 MB; relative-growth and steady-state
  checks passed. Absolute RSS still exceeds the 100 MiB cap by ~12.4 MiB, so
  this is a capability-preserving partial reduction, not Phase 7 closure.
- `git diff --check` passed. The grounded audience-selection code remains
  covered by the passing audience-production tests; the native Argmax-of-Plus
  path is unchanged. Continue attributing the remaining boot/runtime resident
  set and preserve structural parity before claiming resource acceptance.
- Dedicated Phase 7 production-envelope tests: **10 passed in 113.49s**;
  `py_compile` and the scoped diff check passed.

### 2026-09-24 — Closure-connected boot wiring and runtime prewarm

- `load_all_seeds()` now registers code-capability and curriculum-roadmap
  self-account dispatch only when full boot is requested or the corresponding
  faculty seeds are in the resolved connected closure. Conversation-only boot
  no longer imports those unrelated curriculum/corpus stacks. Full boot still
  loads both dispatch functions. The selected conversation profile test
  asserts neither optional import is attempted; a separate full-boot
  registration check verifies both routes remain registered.
- The named conversation profile now prewarms the measured runtime-module
  group after successful seed closure/load and before the first turn. This
  shifts imports out of first-turn latency without changing seed membership or
  graph/native decision authority. The earlier module-attribution run showed
  that boot-time `code_curriculum`/`curriculum_study` imports pulled in
  unrelated corpus dependencies; domain-module event imports are now empty
  across all eight profiled turns.
- Two independent fresh-process runs:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_connected_prewarm_a.json`
  and `_b.json`. Both selected the complete **72-seed** closure, had zero event
  errors, and produced identical canonical observations (SHA256
  `0ea98838ee74c42b60bf4bf7fd1a33a00e5d3fedf77c3161fbdbe36a4e98dd69`). Peak
  RSS: **86,425,600** and **86,421,504 bytes**, below the 100 MiB cap. All
  resource assertions pass. Maximum event latency was **89.4 ms** and **82.9
  ms** (under the 150 ms manifold bound); social greetings were **25.2 ms** and
  **22.9 ms**. No domain module was imported during any measured event.
- Focused profile/import, full-boot dispatch, audience-production,
  conceptualizer, and Phase 7 envelope suites: **47 passed in 118.87s**.
  `py_compile` and scoped `git diff --check` passed. The broader
  `test_code_curriculum_migrated.py` run was interrupted after 7 passed and
  exposed the already-tracked upstream code-action routing failure
  (`no attached world/faculty`); full boot still registered the code faculty,
  and the closure guard leaves the unselected/full-boot branch unchanged.
- The bounded conversation profile’s absolute RSS and manifold latency gates
  are now supported by two independent-process runs. Overall Phase 7 is not
  closed: broad full-boot cost, remaining cognition/production authority gaps,
  speech-act differences, and missing human comparative references remain.

### 2026-09-24 — Current connected-profile structural parity recheck

- Re-ran the expanded full-vs-connected comparison with the current 72-seed
  closure, runtime prewarm, and all 17 explicit content candidates. Fresh report:
  `evaluation/reports/phase7_seed_profile_parity_20260924_phase7k_connected_prewarm.json`.
- Full and connected profiles match **8/8** structural observations with
  **zero errors**; selected closure is complete, and 12 of 3,917
  `learned_lexicon` nodes are loaded. The comparison excludes graph identity
  numbers and response surfaces from semantic evidence. This supersedes the
  earlier 1/8 result for an older connected profile; current parity is proven
  for this exact event slice and supplied lexical candidates, not for the
  broader corpus or upstream autonomous lexical-candidate generation.
- The report does not claim replay determinism or independent-process resource
  measurements; those are independently evidenced by the two connected-profile
  resource reports recorded above. Selected-vs-full fixed-slice parity is no
  longer an open Phase 7 item. General event-family parity, full-boot cost,
  production adoption, and the other cognition/release gates remain open.

### 2026-09-24 — Extended connected-profile resource gate (current status)

- Repeated the exact 74-event connected-profile workload with the WordNet
  membership index already warm. Report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_full74_connected_warm_index.json`.
  The complete 72-seed closure and all 17 requested content keys resolved;
  all 74 events completed with zero errors.
- This extended workload does **not** meet the Phase 7 resource envelope:
  peak RSS **132,231,168 bytes** and conversation/boot-plus-event growth
  **106,147,840 bytes** (over the 100 MiB bound); maximum event latency was
  **10,878 ms** and total event latency **69,942 ms**. Relative RSS growth and
  steady-state growth checks pass, but absolute RSS and total conversation
  growth checks fail. The warm-index repeat is effectively unchanged from the
  initial full-74 run, so first-time WordNet index construction is not the
  cause of the sustained overage.
- Exact-prefix cProfile now reproduces the slowdown with the evaluator's full
  setup and structural readback: the first 52 events complete without errors
  in **60.85 s** of conversation time, with a **11.91 s** maximum event. It
  attributes **55.29 s** to HTTP GETs and **52.22 s** to
  `WorldAdapter._dispatch_pending_io`; the request families include search
  candidate scans, detail retrieval, and topic grounding. Native `run_rules`
  was only 8 ms across nine calls in the earlier slow-question prefix. The
  earlier cProfile attempt that omitted fixture setup/readback was
  non-equivalent; this exact-prefix run supersedes it.
- This establishes the next implementation boundary: external teacher/search
  network waits must leave the turn-release critical path while graph-minted
  requests, graph-native candidate verification, and explicit pending/failed
  outcomes remain authoritative. Do not suppress grounding or treat a pending
  fetch as a supported answer to make latency pass. The queue/commit boundary
  must avoid concurrent mutation of the live graph and must be tested for
  pending-to-completed/failed transitions and replay semantics before this
  resource gate can close.
- The bounded eight-event connected profile remains green (two independent
  processes, <100 MiB peak RSS and <150 ms maximum event), and its 8/8
  fixed-slice full-vs-connected structural parity remains established. These
  bounded results do not close the extended workload/resource gate or Phase 7.

### 2026-09-24 — Deduplicate successful topic grounding dispatch

- Exact replay attribution showed that the graph can mint both a specific
  `GroundRequest` and generic `SearchRequest` for one `answer_topic` goal. The
  turn dispatcher fulfilled both serially; for aspect questions, generic search
  could also install a broad summary alongside the more-specific answer.
- `domains.fetch_dispatch.scan_and_sync_ground()` now marks a matching generic
  search request `superseded` only after successful graph-requested grounding,
  with a `SearchRequest -superseded_by-> GroundRequest` provenance edge. Failed
  or empty grounding leaves generic search requested as fallback. No answer is
  accepted or emitted by this bookkeeping rule.
- `tests/test_topic_grounding_migrated.py`: **9 passed, 1 skipped**; the two
  success/specificity and failure/fallback cases were rerun after the final
  edge-based provenance change: **2 passed**.
- Post-change 74-event run:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_full74_post_ground_dedupe.json`.
  It completed all 74 events with zero errors and the full 72-seed closure, but
  peak RSS is still **132,091,904 bytes**, conversation growth **106,168,320
  bytes**, maximum event latency **10,618 ms**, and total conversation latency
  **72,868 ms**. Compared with the warm-index pre-change run, peak RSS fell by
  only **139,264 bytes** (measurement-scale noise) and total latency increased;
  graph growth fell by 58 nodes / 82 edges. This deduplication is therefore a
  correctness/graph-hygiene fix, not an established resource improvement.
- External HTTPS remains on the synchronous conversation path, so the
  turn-safe scheduler/commit boundary and extended resource envelope remain
  open. At the time of this entry, the composition surface was stale and failed
  production parse-back; the later graph-readback correction below resolves
  that specific case without weakening the gate.

### 2026-09-24 — Graph-authorized capability-answer release

- Live tracing of `Can you navigate 3D spaces?` showed that the native graph
  correctly routed an `answer_capability` Goal and minted its held
  `HeldCapability` reply, but adapter permission-evidence readback also
  classified the shared modal/action concepts as `authority_missing`. The
  fail-closed information bridge then withheld a valid graph capability
  account.
- Same-event `answer_capability` / `answer_imagine` goals now distinguish
  capability questions from permission requests. Capability grounding is read
  from the matching `HeldCapability`; unknown capability is retained as an
  unresolved graph gap; imagined capability remains tied to the graph Goal's
  assumption. The independent “Can I access the sealed room?” control remains
  blocked without event-scoped authority.
- Added a graph-specific production release path requiring the same-event
  capability Goal and exact graph-authored outbound Message, plus the matching
  held capability account or explicit capability-gap record. The existing
  production gate still owns release and records the commitment; no surface
  text classifier or authority bypass was added.
- Verification: both spatial capability cases, negative dance capability,
  chess external-topic routing, conditional routing, and the missing-authority
  control pass (**6 targeted tests passed**). The previously failing composition
  topic case also passes after the stale graph-topic readback retry (**1
  targeted test passed**). Full `tests/test_phase6_information_production_bridge.py`
  passes (**10 passed**), including the fail-closed permission control. The full
  `tests/test_topic_route_selfheal_migrated.py` suite passes (**13 passed**).
- Phase 6’s tested capability release slice is now materially improved, not
  full phase closure. Broader event-family production, speech-act parity,
  human-reference comparison, and the failing extended Phase 7 resource
  envelope remain open.

### 2026-09-24 — Scheduled fulfillment of specific topic grounding

- The daemon's graph-selected `search` host action now fulfills `GroundRequest`
  before the parallel `SearchRequest`. If the source-specific grounding
  succeeds, `scan_and_sync_ground` supersedes the redundant generic search by
  graph edge; if it fails, generic search remains the fallback. This covers
  the daemon's scheduled path as well as the direct adapter dispatcher without
  adding another decision point or mutating graph state from a worker thread.
- `tests/test_topic_grounding_migrated.py` now exercises the daemon host-action
  order (`GroundRequest` then `SearchRequest`): **1 passed**. The scanner's
  successful-specificity and failed-fallback transitions also pass (**2
  passed**); full grounding suite before the final host-action test was **9
  passed, 1 skipped**.
- This is not yet an external-I/O latency solution: the scheduler still
  executes host actions under the daemon's substrate lock, and the direct
  `WorldAdapter.converse()` path still performs synchronous remote retrieval.
  The measured 74-event resource envelope remains failed; a safe transport/
  commit split and fresh end-to-end daemon latency measurement remain required.

### 2026-09-24 — Reuse HTTP(S) connections in the authored GET binding

- Exact-prefix profiling after the topic-request dedupe still attributed
  **17.78 s / 52 turns** to 67 live HTTP GETs. Socket reads took 17.27 s, while
  the earlier cold-connection profile had spent another ~33 s in connection
  setup/TLS handshakes across 92 GETs. The URLs are same-origin Wikipedia
  GETs; process proxy configuration is empty.
- The generated `http_get` binding now delegates to a standard-library
  `HTTPConnection`/`HTTPSConnection` pool bounded to eight origins. It reuses
  keep-alive sockets, retries one stale socket for idempotent GET, follows at
  most five HTTP(S) redirects, refuses HTTPS downgrade/embedded URL
  credentials, preserves the existing response shape and user-agent, and
  drops closed/failed sockets. No decision or graph mutation moved into the
  transport.
- The emitter's generated binding was exercised against a local HTTP/1.1
  server: two resource paths were served over one TCP connection. Full fetch
  dispatch tests: **6 passed**.
- Fresh 74-event report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_full74_keepalive.json`.
  Complete 72-seed closure, zero errors. Conversation time fell from **72.87 s
  to 26.65 s** (~63%); maximum event fell from **10.62 s to 3.60 s** (~66%).
  Peak RSS is **132,177,920 bytes** and boot/event growth **106,094,592 bytes**,
  effectively unchanged and still above both RSS bounds. The slowest events
  remain between 1.58 s and 3.60 s; thus keep-alive materially helps but does
  not close the event latency gate.
- A new exact-prefix profile confirms the remaining **17.70 s** in 67 GETs is
  server response/read time, not connection creation. Next resource work must
  stage external request I/O off the reply-release lock/critical path while
  keeping validation, rule selection, ingestion, and failure outcomes on the
  graph-owning thread. The extended RSS gate and full comparative-evaluation
  gates remain open.

### 2026-09-24 — Bounded same-origin candidate-summary concurrency

- The topic-search path fetched up to five independent Wikipedia summary
  responses sequentially. The authored HTTP(S) transport now supports a
  bounded pool of four independently checked-out keep-alive connections per
  origin, and the search fulfiller overlaps only those read-only summary GETs.
  Candidate parsing, graph writes, native verification/selection, and answer
  commitment remain on the graph-owning caller thread; injected test getters
  retain their deterministic sequential behavior.
- Transport coverage confirms both sequential socket reuse and overlapping
  same-origin GETs (at most four sockets in the local test):
  `tests/test_fetch_dispatch.py` **7 passed**. Topic grounding regression:
  **11 passed, 1 skipped**. `py_compile` and `git diff --check` passed.
- Fresh full 74-event report:
  `evaluation/reports/phase7_profile_resource_20260924_conversation_full74_parallel_summary.json`.
  Selection completed with all 74 events and zero errors. Total conversation
  latency decreased from **26.65 s to 23.88 s** (~10.4%) and the maximum event
  from **3.60 s to 3.07 s** (~14.9%). Peak RSS increased by **3,289,088 bytes**
  to **135,467,008 bytes** and boot/event RSS growth by **3,444,736 bytes** to
  **109,539,328 bytes**. This is a modest latency improvement with a resource
  regression; all absolute/growth RSS bounds and the event-latency bound remain
  open. It does not replace the needed asynchronous I/O/graph-owner commit
  boundary or close comparative evaluation.

### 2026-09-24 — Split search retrieval data from graph commit

- Extracted `retrieve_search_candidate_payloads(query, referent_snapshot, ...)`
  as a graph-free I/O/data-shaping stage and
  `commit_search_candidate_payloads(agent, request, payloads, ...)` as the
  graph-owner write stage. The synchronous scanner now composes these same
  two operations, retaining the existing native `candidates_ready` selection
  and supported-evidence commit sequence.
- The new regression proves retrieval creates no graph nodes or candidate
  edges; the explicit owner commit then adds the candidate. Transport, split-
  boundary, existing successful-search and honest miss/failure paths:
  **10 passed**.
- This provides the immutable payload/owner-commit seam needed for daemon
  off-lock I/O. It is not asynchronous yet: the synchronous scanner and
  `WorldAdapter.converse()` still wait for network retrieval, and the daemon's
  more-specific `GroundRequest` can also perform remote work inside
  `AGENT_LOCK`. Those waits, pending/failed receipt transitions, and fresh
  liveness/resource measurements remain required before claiming the
  reply-release boundary or Phase 7 is closed.

### 2026-09-24 — Daemon off-lock generic search fulfillment

- The daemon's graph-selected `search` host action now snapshots only the
  selected `SearchRequest` (or same-query fallback for a `GroundRequest`) and
  submits immutable values to a bounded four-worker pool. Network retrieval
  uses the graph-free payload API; workers do not receive the adapter or graph
  handles. Search requests stay in the graph's existing `running` pending
  state, suppressing premature unresolved-topic replies. The host action and
  scheduled task are explicitly `io_pending` until completion.
- When futures finish, only the owner/tick thread rejoins them. It verifies
  node liveness, exact query, and per-request token before writing candidate
  evidence; native rules still select candidates, and only a selected
  supported candidate is committed. Stale/superseded responses are discarded.
  At most **16** candidate jobs may be queued. Completion wakes the daemon;
  restart/shutdown requeues orphaned SearchRequests and host actions instead
  of persisting unresumable in-flight state.
- Verification: daemon pending → selected graph commit → receipt, restart
  recovery, graph-free retrieval, and existing host-order/supervisor/transport
  behavior pass. Fresh relevant run: **24 passed** across
  `test_host_action_supervisor_migrated.py`, `test_fetch_dispatch.py`, and
  focused topic-grounding tests. The broader grounding/host/transport run
  yielded **33 passed, 1 skipped**; its two `inspect.getsource(tick_loop)`
  assertions read the wrong lines because the source file changed during that
  run, and the fresh complete host-action suite subsequently passed those
  assertions. Compilation and `git diff --check` pass.
- This moves generic SearchRequest network waits off the daemon graph lock; it
  does **not** yet solve the full boundary. `_search_tick` still fulfills
  specific `GroundRequest` synchronously before starting the fallback, and the
  direct `WorldAdapter.converse()` evaluator path is still synchronous. The
  current 74-event resource report remains the prior direct-path result (RSS
  and latency fail); daemon liveness and full resource measurements must be
  rerun after staging GroundRequest I/O and completing the owner-thread
  pending/failed semantics for all remote retrieval families. Cognition,
  production, and comparative-human acceptance gates remain open.

### 2026-09-24 — Daemon off-lock specific GroundRequest fulfillment

- The daemon graph-selected search action now handles a specific `GroundRequest`
  before its generic `SearchRequest` fallback. Local source lookups remain on
  the graph owner; remote summary/detail retrieval receives only immutable
  query/aspect values on the bounded worker pool. The graph keeps the request
  in `running`, and the host action/task remain `io_pending`. Matching generic
  work is deferred until this specific request resolves.
- The tick owner validates node/query/token, commits the returned source data,
  and records the request result/host receipt. A successful specific grounding
  graph-supersedes a requested or in-flight generic search; an honest miss or
  retrieval error leaves the generic fallback schedulable. Restart/shutdown
  recovery now also requeues interrupted GroundRequests. Worker completion
  never makes graph writes.
- Composition handling retains the existing answer precedence: local detail,
  remote detail, local composition-summary fallback, then remote summary. The
  graph owner selects and persists the answer; fallback evidence is not
  released merely because the worker fetched it. Focused specific-grounding
  async success/fallback, graph-free composition precedence, and existing
  direct scanner success/failure tests: **5 passed**. Restart recovery for
  both request types: **1 passed**. Focused daemon graph-lock availability,
  pending→commit→receipt, and runtime-status tests: **7 passed** in the prior
  relevant run. `py_compile` and `git diff --check` pass.
- This closes the daemon lock wait for generic and specific topic retrieval,
  but not all remote paths: `WorldAdapter.converse()` still dispatches
  synchronously for the direct/evaluation path, while other fetch/detail/upload
  families need an equivalent lifecycle audit. The existing full 74-event
  profile exercises that direct path and still fails both latency and RSS
  bounds; a separate daemon liveness/resource profile and the full evaluation
  gates remain open.

### 2026-09-24 — Daemon off-lock DetailRequest fulfillment

- The graph-selected `detail` host action now checks local progressive detail
  on the owner thread, then submits remote chunk retrieval to the bounded
  executor. The request remains `running` while I/O is pending; the graph owner
  validates its topic/token, commits chunks and receipt, and records failure
  honestly. Restart/shutdown recovery requeues interrupted DetailRequests.
- Regression coverage verifies the graph lock remains available during
  blocked retrieval, completion commits on the owner, and restart clears stale
  detail tokens. Focused tests: **2 passed**; `py_compile` and `git diff --check`
  pass.
- This closes the daemon DetailRequest path only. Direct
  `WorldAdapter.converse()` remains synchronous, as do other fetch/upload
  families pending audit; prior 74-event latency/RSS and cognition/production/
  comparative-human gates remain open.

### 2026-09-25 — Non-turn defer prevents forced ask-back

- The existing native arbitration already marks typed, uncertain continuation
  fragments as `defer`. Previously the adapter could still release a
  conversation-action ask-back, contradicting that graph decision. The live
  bridge now closes a typed non-turn fragment after native defer and event
  binding without creating an outbound reply or production receipt. The
  turn-compatible overlap/error behavior is unchanged.
- A fresh Phase 8 single-event run for `partial_stream` confirms native
  authoritative `defer`, unavailable release, and empty reply. Partial-event/
  uncertainty controls: **8 passed**; neighboring conversation and production
  controls: **33 passed**. `py_compile` and `git diff --check` pass.
- Full 74-event replay and Phase 6/7/8 acceptance suites remain open; do not
  project this single-event result to whole-corpus closure.

### 2026-09-25 — Full-corpus replay and exposed discourse regressions

- Replayed all 74 events after the non-turn release guard. The fresh report is
  `evaluation/reports/phase8_corpus_report_20260925_phase6zf_nonturn_defer_release.json`
  (SHA256 `d11461f8dcb721e57b226bfc324f2aa72488d80bad239fab95692ebd3134d308`).
  The target event now has the intended graph-authoritative defer and empty
  release. No-reply changes propagate through the event sequence, as expected
  when prior false turns are removed.
- Whole-corpus disposition coverage is **34/74 authoritative**, with **32
  authoritative matches**, **2 authoritative mismatches**, and **9** label
  matches lacking disposition authority. The prior report had 35/74, 34
  matches, and one mismatch. `action_world_unknown` is newly exposed as an
  act-vs-repair disagreement; `question_ack` no longer has prior answer
  authority in the changed sequence. Preserve the non-turn boundary and
  investigate these cognition/context effects as separate work.
- The comparative gate remains blocked at provenance; broader cognition,
  production, and resource gates remain open. No overall completion claim.

### 2026-09-25 — Native repair disposition governs imperative release

- A typed uncertain action can have a grounded head noun while still carrying
  an unresolved semantic gap (`gap_count > 0`). Native arbitration now treats
  that combination as repair, and the live imperative bridge dispatches the
  existing clarification faculty whenever graph cognition selected repair.
  The boundary no longer promotes a repair disposition into an action goal.
- Focused typed-gap/arbitration and partial-event controls: **9 passed**;
  repair-release and unresolved-anaphora controls: **3 passed**. Fresh full
  74-event replay:
  `evaluation/reports/phase8_corpus_report_20260925_phase6zh_repair_release_alignment.json`
  (SHA256 `ff23cbc085019a649959f07144b93cd56d9cca49d5d5280541871f3d8effd13e3`).
  It yields **36/74 authoritative dispositions**, **34 matches**, and **2
  authoritative mismatches**; `action_world_unknown` now correctly routes to
  repair. `info_explanation` and `response_no` remain mismatches. The overall
  comparative gate remains blocked at provenance.
### 2026-09-25 — Preserve refusal force across imperative complements

- The input classifier already labels a refusal-plus-imperative (for example,
  “No, hold position.”) as `refusal`, but live interpretation construction
  could overwrite that typed neutral evidence with `action_request` based on
  the selected instruction parse. Refusal evidence now takes precedence over
  parse-path force at this adapter boundary; native arbitration remains the
  disposition authority.
- Added a live regression proving the typed refusal reaches native arbitration
  and selects `defer`. The targeted test and language-neutral evidence suite
  pass **7/7**. A fresh full 74-event replay
  (`evaluation/reports/phase8_corpus_report_20260925_refusal_force_precedence.json`,
  SHA256 `00e9b60bc303562f45bcdd4cf47b98c2ad3031cf86832ad5cc84cf7f00d9fbad`)
  confirms `response_no` now has `defer/native_graph_readback` (previously
  `repair`). Authority coverage rose from 36 to **38/74**, with one remaining
  authoritative mismatch (`info_explanation`, expected `learn`, observed
  `repair`). `response_no` still releases the explicit diagnostic error; this
  repairs its disposition mismatch only, not production. Comparative release
  remains blocked at provenance; other cognition, production, resource, and
  comparative gates remain open.

### 2026-09-25 — Separate missing causal knowledge from anaphoric repair

- Native arbitration now treats a well-formed, non-anaphoric reason request
  with no causal graph path as `learn` / `answer_or_learn`, rather than
  misclassifying missing answer knowledge as user repair. A typed reason
  request with an anaphoric topic remains `repair`, preventing an unsupported
  lexical answer from escaping. Live controls for both branches pass **2/2**.
- Fresh 74-event report:
  `evaluation/reports/phase8_corpus_report_20260925_reason_request_learning_guarded.json`
  (SHA256 `eb024a7066611308cccd700e2a08302a5e8b070abecea78cf4bbb7ccb2d0f7d2`).
  It records **38/74** authoritative dispositions and **zero authoritative
  mismatches**; `info_explanation` is now authoritative `learn`, while
  `question_followup` remains authoritative `repair`, and `response_no`
  remains authoritative `defer`. All three still release the diagnostic error
  in this replay, so production does not yet enact the learned retrieval goal.
  Authority coverage is incomplete and comparative release remains blocked at
  provenance; production, resource, and overall cognition gates remain open.

### 2026-09-25 — Keep optional Wikipedia/parquet imports off the miss path

- Full-corpus profiling attributed an extra **28.8 MB** and **1.9 s** at
  `question_unavailable` to importing `pyarrow` through the Wikipedia teacher,
  despite no Wikipedia snapshot being installed. Moved shared question-subject
  normalization to a lightweight module; grammar, dictionary, trope, and LLVM
  teachers no longer import `wiki_teacher` for that helper. Topic grounding
  now checks for an attached teacher/local snapshot before importing the
  parquet-backed teacher.
- Added a no-snapshot regression that fails if the wiki/parquet modules are
  imported. Grounding, fetch, wiki, dictionary, and grammar suites pass
  **82 passed, 2 skipped**.
- Fresh 74-event connected profile:
  `evaluation/reports/phase7_profile_resource_20260925_full74_lazy_wiki_recheck2.json`.
  Peak RSS fell from **135,720,960** to **109,096,960 bytes** and boot/event
  growth is **82,894,848 bytes** (within the growth bound). No `pyarrow` or
  wiki modules load on `question_unavailable`. Absolute RSS still exceeds 100
  MiB by **4,239,360 bytes** and worst event latency is **5,261 ms**; resource
  acceptance remains open. Sequence hotspots and full production/daemon
  behavior still require separate work.

### 2026-09-25 — Recheck daemon async topic-retrieval lifecycle

- Fresh focused recheck against the current worktree:
  `.venv/bin/pytest -q tests/test_topic_grounding_migrated.py -k
  'daemon_specific_grounding_is_async or
  daemon_failed_specific_grounding_releases_generic_fallback or
  daemon_requeues_search_io_interrupted_by_restart or
  daemon_search_request_runs_off_lock_and_commits_on_owner'` → **3 passed,
  17 deselected**. The selected tests verify async specific grounding,
  failed-grounding fallback to generic search, restart recovery, and generic
  search owner-thread commit while the daemon graph lock remains available.
- This verifies only the bounded retrieval lifecycle, not full daemon turn
  completion. The existing 74-event ingress harness does not dispatch host
  actions or external I/O; a completed-turn daemon corpus profile is still
  required before production latency/resource acceptance can be assessed.

### 2026-09-25 — Fix scheduler shape mismatch in async grounding

- A seed-generated probe (`What do you know about the moon?`) exposed a real
  liveness defect: the graph minted a same-query `GroundRequest`, a generic
  `SearchRequest`, and one search `HostActionRequest` sourced from the generic
  request. The daemon deferred that host action while waiting for a separate
  GroundRequest-sourced host action that the supervisor had not minted; after
  a bounded 14-second probe, both requests and the host action were still
  `requested`, with no reply or I/O in flight.
- Removed that mismatched-source deferral. A graph-selected generic search
  action now stages the matching specific GroundRequest first; successful
  commit supersedes generic search, while a specific miss/error leaves generic
  fallback eligible. This retains the no-race precedence without requiring a
  second host action.
- Added `test_daemon_generic_host_action_stages_matching_ground_request_first`
  and a seed-generated daemon completion regression in
  `tests/test_phase7_daemon_ingress_envelope.py`. The latter proves native
  withholding during `io_pending`, owner-thread GroundRequest commit and host
  receipt, generic-request supersession, then native answer release. Its
  retrieval payload is controlled/mocked; it is not an external-source or
  corpus-level production measurement. The first graph-selected host dispatch
  entered `io_pending` in **37.7 ms** in the isolated smoke probe.
- Verification: daemon ingress/completion tests **2 passed**; the broader
  topic-grounding plus host-action-supervisor suites **34 passed, 1 skipped**
  in **299.03s**; `py_compile` and scoped `git diff --check` passed. A fresh
  full 74-event daemon-completion profile, real external-source completion,
  direct `WorldAdapter.converse()` I/O, absolute RSS/latency acceptance, and
  cognition/production/comparative gates remain open.

### 2026-09-25 — Full daemon completion profile and ordered owner commits

- The opt-in completion harness now runs the daemon's graph-selected host
  action executor and drains worker futures, while the original signal-only
  mode remains unchanged. The seed-generated one-turn/action-chain test proves
  delayed reply release through owner-thread ground and detail commits.
- Two independent 74-event connected-profile runs used the real retrieval
  transport (35 counted topic-grounding HTTP requests each) and produced the
  same canonical chat-observation SHA256:
  `75cd5d4e365b48250ee270559967e1a531c29991f97484de4952adf3a3dc119d`.
  Reports: `evaluation/reports/phase7_daemon_completion_20260925_verified.json`
  and `_verified_replay.json`. Both record 74/74 interpretations, only 10/74
  authoritative dispositions, 37/74 replies after dispatching and completing
  **32** host actions, 37 pending turns, zero pending host actions or host I/O,
  and zero daemon runtime errors. Across the pair, maximum completed-turn
  latency was **3,160.0 ms**; maximum ingress/native-cycle times were
  **31.77/32.17 ms**. Peak RSS was **111,398,912 bytes**; the <100 MiB gate
  still fails.
- The first pair of independent profiles had different final `current_topic`
  values despite equal reply/action counts. Completion scanning was committing
  later ready search futures while an earlier graph-selected request remained
  in flight. Owner commits now preserve host-request insertion order while
  retrieval remains concurrent and the owner never waits under `AGENT_LOCK`.
  The two ordered-run hashes now match; forced out-of-order future completion
  regression plus the seed-generated completion, fallback, restart, and
  pending-owner-commit controls pass **8/8**.
- The canonical chat-observation hashes matching does not prove receipt-level
  replay determinism: external follow-up `DetailRequest` outcomes differed
  (one run: **1 failed/5 done**; replay: **3 failed/3 done**) while both still
  completed 32 host actions. Both reports include 32 receipts and the actual
  HTTP request count. External detail-source reliability remains an open
  production property; do not overstate the matching chat projection as
  identical host-action history.
- These full-profile results falsify full production closure: 37 turns remain
  reply-pending. Among those, 26 interpretations carry `update_common_ground`,
  5 `act_or_clarify`, 3 `answer_or_learn`, and 3 `coordinate_socially`; many
  already have a graph-created non-text adjacency Message, which is not enough
  for `graph_turn_reply()`. The next cognition/production seam is native event
  terminality versus reply expectation, followed by graph-authorized text
  realization/production—not fabricating replies or clearing the daemon's
  pending ledger from Python. The current profile has determinism evidence,
  not a reply/production pass. Resource, cognition/disposition, production,
  and comparative-human/provenance gates remain open.

### 2026-09-25 — Generic-search fallback lifecycle closure

- Follow-up provenance instrumentation confirmed the seven residual requested
  searches each had a completed `search` HostActionRequest, but no request
  terminal state or search I/O token. The selected generic action had staged
  only a same-query `GroundRequest`; a ground miss completed that action while
  leaving its generic SearchRequest requested, after which graph mint-once
  correctly prevented another action.
- The selected action now stages generic SearchRequest retrieval after an
  honest specific-grounding miss. Candidate transport remains off-graph,
  returned candidates remain committed/verified on the owner thread, and no
  reply is synthesized by Python. A seed-generated test exercises ground miss
  followed by an empty generic result and confirms the SearchRequest reaches
  an honest terminal status. The new completion report v4 records request IDs,
  statuses, evidence, linked host actions, and receipt outcomes.
- Fresh 74-event profile
  `evaluation/reports/phase7_daemon_completion_20260925_fallback_recheck.json`:
  0 requested SearchRequests (from 7), 0 requested GroundRequests, 39/74
  reply-ready turns (up from 37 in the previous measured pair), 35 pending
  turns, 32 completed host actions, 53 counted HTTP requests, and 110,223,360
  bytes peak RSS. Search lifecycle drain is now clear; reply terminality and
  the <100 MiB, disposition/cognition, production, and comparative gates remain
  open.

### 2026-09-25 — Characterize graph reply candidates at the daemon boundary

- The canonical parity/deliberative-production/grammar-inversion test battery
  currently passes **8/8**, but this is synchronous-path evidence and does not
  establish daemon completion. A one-turn graph probe shows the native rule
  creates an `acknowledgment` Message with no text; `emit_reply()` can render
  the graph-held sign as “I heard you.”, while the synchronous turn pipeline
  deliberately treats that generic backchannel as intermediate, not as a
  substantive final reply.
- Added per-event graph reply-candidate readback to daemon report schema v4 and
  a one-turn characterization regression. A fresh 74-event profile
  `evaluation/reports/phase7_daemon_completion_20260925_reply_lifecycle_audit.json`
  has 39 text replies and 35 unresolved turns: **31** have only an
  acknowledgment speech-act candidate without text, **2** have no reply
  candidate (both native defer events), and **2** have textless `greeting` or
  `grant` candidates. These classes require separate native-terminality or
  graph-authorized production treatment; releasing the generic acknowledgment
  would contradict the synchronous pipeline's current policy. This narrows the
  next seam to explicit graph reply expectation/terminality and authorized
  realization, without changing acceptance claims.

### 2026-09-25 — Async release for graph-selected social turns

- Native inbound speech-act evidence now gates the owner-thread release bridge:
  only social turns use `emit_reply()` plus the existing `_release_social_reply`
  check, and released text is attached to the same graph-selected reply node.
  Ordinary statement acknowledgments are still never accepted as substantive
  completions.
- Seed-profile regressions cover both greeting and thanks, require exactly one
  `conversation_social_graph` receipt per turn, and retain the non-social
  acknowledgment characterization. All daemon-envelope tests pass **6/6**.
  Fresh 74-event replay
  `evaluation/reports/phase7_daemon_completion_20260925_social_receipt_scoped.json`
  yields **42** text replies, **32** pending turns, zero requested
  SearchRequests, and **111,341,568 bytes** peak RSS. Social receipt
  attribution is exactly one receipt per turn. Acknowledgment continuation and
  other pending classes, cognition, resource, and comparative gates remain
  open. The 32 residual turns are now characterized as 29 acknowledgment-only
  candidates, two no-candidate native defer events, and one `grant` candidate.

### 2026-09-25 — Phase 8 adapter-derived partial-event evidence

- Removed the corpus `literal_form` reference annotation from the live SUT
  input. The language adapter now records fragment evidence from its terminal
  unresolved parse gap and continuation marker; the social-act path reads the
  inbound signal boundary. A complete OOV `hello` remains non-fragment even
  when its reference annotation says fragment.
- Phase 8 and explicit-uncertainty/evidence-arbitration controls passed
  **36/36** before the final social-path refinement; the refined social-path
  regression passes **1/1**. Compilation and diff checks pass.
- Fresh full report
  `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`:
  **41/74** force matches, **38/74** disposition-authoritative events, and
  **35/38** authoritative state matches. `fragment_social` is now an
  authoritative defer match; remaining mismatches are `action_world_unknown`,
  `blocked_reference`, and `action_referent`. `correction_uncertain` remains
  non-authoritative. Broader cognition, production, resource, Phase 4, and
  comparative gates remain open.

### 2026-09-25 — Native repair disposition and force separation

- Parser-selected `literal_form` is now language-adapter evidence rather than
  a corpus label, allowing the existing graph-native unresolved-action rule to
  run in the corpus harness. A typed continuation rule gives uncertain
  non-turn common-ground updates a native repair disposition. Repair
  arbitration no longer overwrites communicative force; native basis-settling
  rules preserve the specific repair rationale after generic force arbitration.
- Targeted ask-back lifecycle, parser-derived action/reference repair,
  uncertain-continuation repair, and Phase 8 fragment/reference controls pass
  **4/4**. JSON validation, compilation, and `git diff --check` pass.
- Current full-corpus report
  `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`:
  **42/74** force exact matches; **39/39** authoritative disposition matches
  with zero authoritative mismatches; grounding **0.34/50**. Native authority
  covers **11/16** expected repairs and **5/9** expected actions. Learning,
  memory, normalized cost, resource, production, Phase 4, and comparative
  gates remain open.

### 2026-09-25 — Native repair dispositions for unresolved non-turn events

- Added graph arbitration for uncertain unresolved non-turn information
  requests and frontiers, plus typed repair responses. These rules leave
  communicative force unchanged, keep turn-compatible information eligible
  for answer/learning, and preserve the existing permission-authority block.
- Full language-neutral evidence-arbitration suite: **8 passed**. Fresh 74-event
  report `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`
  now has **44/44** authoritative disposition matches, **0** authoritative
  mismatches, and **15/16** expected repair / **5/9** expected action authority.
  Grounding remains **0.34/50** and force match **42/74**. One expected repair
  (`offer_unknown`) remains outside native disposition authority; all broader
  resource, production, Phase 4, comparative, and learning/memory/cost gates
  remain open.

### 2026-09-25 — Reject flattened disambiguation headers during topic grounding

- The prior Phase 8 `causal_topic_link` observation for `question_ack` exposed a
  local-library disambiguation header (`Route or routes may refer to:`) followed
  by its alternatives. `_is_disambiguation_extract` only rejected a terminal
  `may refer to:` marker, allowing that flattened list through.
- The grounding boundary now recognizes a leading disambiguation header with
  trailing entries while leaving ordinary article-body mentions untouched. The
  focused regressions pass **4/4**, including no persistence of rejected
  disambiguation content as learned grounding.
- A fresh full Phase 8 replay was written outside the repository to
  `/tmp/phase8_grounding_header_recheck.json`. It remains blocked overall; the
  74-event grounding score is unchanged at **16/50** (precision **0.941**,
  recall **0.32**, F1 **0.478**). Its `question_ack` source returned a regular
  but generic route-of-administration summary rather than the previously
  observed disambiguation list, so this correction is a targeted source-shape
  fix, not evidence of improved corpus grounding. Broader grounding, cognition,
  production, resource, Phase 4, learning/memory/cost, and comparative gates
  remain open.

### 2026-09-25 — Remove parse-gap false positives and type action referents

- The prior uncontaminated v4 replay exposed parse-gap false positives on
  `action_close` and `action_sensor`, plus wrong dispositions for
  `defer_permission` and `error_empty`. The action repair rule now requires a
  typed unresolved referent or unknown grounding; generic grammar gap count is
  not treated as referent evidence.
- The language adapter now emits its neutral `referent_status=unresolved` for
  explicit `unknown` / `unidentified` action-target modifiers. This turns
  grounding unresolved and drives graph-native repair without passing a corpus
  uncertainty label. Deictic references already use the same typed channel.
  A separate graph arbitration rule defers a grounded standalone action in a
  non-turn event.
- Focused boundaries pass **4/4**:
  `tests/test_phase6_explicit_uncertainty.py` cases for unknown action targets,
  deictic references, and parse-derived action repairs. The deictic instruction
  test now explicitly expects native repair with `explicit_uncertainty=0`.
- Fresh full corpus replay:
  `evaluation/reports/phase8_corpus_report_20260925_v4_adapter_typed_referents.json`.
  It records **41/74** graph-authoritative dispositions; among these, only
  `error_empty` mismatches (40/41 authoritative matches), while both grounded
  direct actions now correctly `act` and `defer_permission` correctly defers.
  `action_world_unknown` and `action_referent` repair with unresolved grounding.
  Grounding is **16/50** (precision **1.00**, recall **0.32**, F1 **0.485**).
  Phase 4 still has four evidence-source events, zero complete tuples, and zero
  promotions. The release gate remains blocked; all comparative dimensions
  remain unavailable. Production parity, resource, Phase 4, grounding recall,
  learning/memory/cost, and human/reference comparisons remain open.
- Seed JSON validation and scoped `git diff --check` pass; corpus and resource
  results for this change set are recorded below.

### 2026-09-25 — Typed input-failure boundary and post-change checks

- The adapter now turns bracketed ASR placeholders (`[unintelligible]`,
  `[inaudible]`) into `communication_failure=input_unintelligible`; the
  graph-resident interpretation records that as explicit failure. This makes
  `error_empty` an error from the signal itself, without corpus evidence.
- The complete Phase 6 explicit-uncertainty file passes **11/11**, and the
  language-neutral arbitration suite passes **8/8**. The Phase 8 corpus-runner
  suite passes **24/24**, including annotation isolation and provenance
  controls; the Phase 7 production-envelope suite passes **11/11**. Coverage
  includes signal-derived failure, explicit failure, unknown action targets,
  unresolved deictic targets, native repair release, and runtime-input
  isolation from corpus parse/evidence labels.
- Fresh Phase 8 v4 report
  `evaluation/reports/phase8_corpus_report_20260925_v4_final_signal_only.json`:
  all **41/41** graph-authoritative dispositions match, with no authoritative
  mismatches; disposition authority covers 41/74 events, and five reference
  labels match without native authority. Grounding is **16/50** (precision
  **1.00**, recall **0.32**, F1 **0.485**). Phase 4 remains at four evidence
  sources, zero complete tuples, and zero promotions. Comparative release is
  blocked at provenance; human and model-comparator dimensions remain
  unavailable.
- Fresh 74-event connected-profile resource replay
  `evaluation/reports/phase7_profile_resource_20260925_full74_final_signal_only.json`:
  73 seeds selected, complete closure, zero event errors, 108,576,768-byte
  measured RSS, 82,743,296-byte boot/event growth, and 1,934.8 ms worst event.
  RSS and latency acceptance remain false. The earlier sync replay remains a
  separate production gate; no resource criterion is closed by this run.
- Overall cognition, production parity, resource, Phase 4, grounding recall,
  learning/memory/cost, and comparative evidence gates remain open.
- A subsequent live-parity failure on `describe what you see` exposed that an
  unresolved action-target rule also captured adapter-classified
  `information_request`s. The rule is now force-typed as `action_request`; a
  separate continuation-information rule repairs unresolved world/deictic
  referents. The scene-description regression and the new no-corpus-evidence
  continuing-referent boundary pass (**2/2**), and a fresh 74-event replay
  confirms 41/41 authoritative dispositions still match, including
  `blocked_reference`. The attached-scene dialogue remains eligible for its
  selected scene faculty. Resource/comparative/grounding/Phase 4 gates remain
  open.

### 2026-09-25 — Case-complete v4 local model references

- Added explicit Ollama HTTP controls for seed, temperature, token cap, and
  GPU allocation; CLI transport fails closed if asked to promise CPU-only
  execution. Adapter tests pass **5/5** and raw-reference audit tests pass
  **2/2**.
- Collected fixed-v4 raw outputs over all **74** corpus events from
  `gemma3:4b` with `num_gpu=0` (CPU-only), seed 42, temperature 0, and a
  96-token cap; all cases completed. Collected the same 74-case prompt/options
  from `qwen3.5:9b` with automatic GPU placement; all cases completed. These
  are unannotated outputs, not capability scores.
- Reran ELIZA under v4 and audited all three raw runs with
  `evaluation/phase8_raw_reference_audit.py`. Result
  `evaluation/reports/phase8_raw_reference_audit_20260925_v4.json` is
  **incomplete**, with **3 complete raw** baselines and **2 missing human**
  baselines; it explicitly records that no score interpretation occurred.
  This does not close the comparative gate: only one seed is collected per
  LLM, no blinded dual annotations/adjudication exist, human references are
  missing, and memory/learning/calibration/cost dimensions are not measured
  for the reference models.
- Final verification after the action-force and turn-compatible information
  repair refinements: `tests/test_phase6_explicit_uncertainty.py` passes
  **11/11**; the scene-description and continuation-reference boundary pass
  **3/3**. Fresh signal-only Phase 8 v4 replay remains **41/41** authoritative
  matches with zero errors. The latest 74-event connected-profile resource
  replay has complete 73-seed selection and zero errors, but records
  108,576,768-byte RSS and 1,934.8 ms worst-event latency; both absolute
  resource assertions remain false.

### 2026-09-25 — Attribute the connected-profile latency outlier before tuning

- Rechecked the latest full-74 connected-profile resource report. The
  `question_ack` event (`Can you confirm the route?`, standalone non-turn) is
  the 1,934.8 ms maximum and loads `domains.acronym_expand`,
  `domains.http_transport`, `domains.libraries`, `encodings.idna`, and
  `stringprep` during its conversation call.
- The connected seed loader already uses a pre-pass to resolve and validate
  dependency closure before graph mutation, then caches the seed index; its
  conversation profile also prewarms a declared runtime-module group. This
  implements the dependency-connected loading direction for seed content.
- The runtime path permits topic grounding to use web I/O on synchronous turns.
  A fresh isolated cProfile run of the same connected-profile event completed
  with no errors at 2,036.4 ms. It attributes about 1,832 ms cumulative to
  `domains.http_transport` calls, including approximately 1,652 ms waiting on
  network responses; `_answer_topic_reply` accounts for about 749 ms and
  `_dispatch_pending_io` about 1,102 ms. This identifies remote retrieval as
  the dominant measured cost, not module import. The profile alone does not
  prove whether every request is semantically redundant, so no request was
  suppressed and no I/O policy was changed. Next resource step: trace the
  graph-minted request IDs and URLs across both phases, then test any proposed
  deduplication against request/candidate provenance and answer-release parity.
- The isolated graph readback also shows a cognition/bridge inconsistency:
  communication arbitration records `repair_or_defer` /
  `clarify_or_defer`, while an `answer_topic` goal triggers external retrieval
  and the adapter releases a generic route-of-administration summary. Treat
  this as a case-level authority question, not merely a latency optimization;
  the corpus labels `question_ack` as an answer, so reconcile the intended
  referent/context semantics before changing either routing or release.

### 2026-09-25 — Honor explicit native dispositions at topic retrieval boundary

- Implemented a graph-readback guard in `_answer_topic_reply` and
  `_dispatch_pending_io`: an explicit `cognitive_disposition` of repair,
  defer, blocked, or error prevents lexical topic fulfillment and leaves
  graph-minted searches pending. Force/goal hypotheses alone do not suppress
  a route; an initial broader guard broke the valid turn-compatible
  `Can you play chess?` topic path and was narrowed before acceptance.
- Verification after narrowing: `tests/test_topic_route_selfheal_migrated.py`
  **15 passed**; Phase 6 runtime-state/production plus action/defer and
  conversation-loop suites **48 passed**. The fixed 74-event Phase 8 replay
  `evaluation/reports/phase8_corpus_report_20260925_explicit_disposition_bridge.json`
  completes with zero errors and no reported release-gate regressions; native
  disposition authority remains 41/74 (with 5 additional label matches lacking
  authority), grounding precision/recall/F1 remains 1.00/0.32/0.485, and the
  release gate is still blocked at provenance.
- Fresh 74-event connected-profile resource replay
  `evaluation/reports/phase7_profile_resource_20260925_full74_explicit_disposition_bridge.json`
  selects 65 seeds with complete closure and zero errors. Boot/event RSS growth
  is 81,133,568 bytes, but absolute RSS remains over limit; worst event remains
  `question_ack` at 1,921.9 ms. This corpus event has no explicit selected
  disposition (it carries repair force / clarify goal), so it correctly remains
  unresolved by the new selected-disposition guard. Its label still expects an
  answer despite the observed repair force and generic homonym response; a
  case-level intent/reference adjudication is still required before modifying
  that path. Resource, cognition, provenance, Phase 4, production, and
  comparative gates remain open.

### 2026-09-25 — Repeat the fixed-budget CPU small-model reference

- Collected two additional raw `gemma3:4b` CPU-only runs under the same Phase 8
  v4 prompt, `num_predict=96`, temperature 0, and `num_gpu=0`, using seeds 43
  and 44. Reports:
  `evaluation/reports/phase8_small_llm_gemma3_4b_cpu_seed43_20260925.json` and
  `evaluation/reports/phase8_small_llm_gemma3_4b_cpu_seed44_20260925.json`.
- A case-binding audit against the original seed-42 report confirms all three
  runs have the same 74 cases and no collection failures; all 74 response texts
  are identical across seeds. This is repeatability evidence under deterministic
  decoding, not 222 independent capability samples, a confidence interval, or
  a capability score. Blinded dual annotation, human reference runs, and
  memory/learning/cost measurements are still missing; comparative release
  remains blocked.

### 2026-09-25 — Phase 8 input-equivalence audit

- The current v4 SUT and LLM references do not receive equivalent interaction
  histories. `evaluation/phase8_corpus_runner.py` boots one `WorldAdapter` for
  the entire 74-event sequence, passes each event's `interaction_mode` and
  `interaction_relation`, and injects held-answer setup for two events.
  `evaluation/reference_adapters/ollama_local.py` instead submits one isolated
  prompt per event containing only the signal text. Thus the target can use
  discourse carried across events and typed transport metadata unavailable to
  the LLM; the two preloaded held answers are also omitted from its prompts.
- This is a protocol comparability defect for memory/learning and context-bound
  cases, not a model performance result. Keep existing v4 reports raw and
  unscored. Before any target-vs-LLM capability score, define a matched
  presentation/history protocol and run the target and reference systems under
  it; independent per-event v4 runs may only support dimensions that are
  adjudicated as context-free. Human references, repeated independent response
  samples, and missing memory/learning/cost probes remain open.

### 2026-09-25 — Bounded event-context reference profile

- Added an opt-in `phase8a-fixed-phase0-corpus-v5-event-context-history8`
  Ollama profile. It transmits the runtime input available to the SUT: current
  signal, per-event interaction mode/relation, held-answer setup, and the most
  recent eight signal/response pairs. It omits corpus reference labels. The
  prompt is bounded because a full-history CPU trial exceeded 21 minutes; that
  trial was stopped without producing a report. This documents a compute-cost
  limitation, not a collection result.
- The 74-case `gemma3:4b` run completed under CPU-only `num_gpu=0`, seed 42,
  temperature 0, and a 96-token output cap. It has 0 failures, 87–370
  prompt-evaluation tokens per event, and 321.18 seconds summed model-reported
  generation time. This is raw evidence only; it is not human-adjudicated
  capability evidence or full graph-memory parity.
- The protocol-specific raw audit
  `evaluation/reports/phase8_raw_reference_audit_20260925_v5_event_context_history8.json`
  records one complete raw reference class and four missing classes, with no
  score interpretation. V4/V5 runs must not be combined. V5 still needs a
  target run explicitly bound to this profile, compatible repeated runs,
  blinded dual annotation, human reference sessions, and dedicated
  memory/learning/cost probes. Comparative release remains blocked.

### 2026-09-25 — V5 event-context deterministic repeat

- Collected seed 43 at
  `evaluation/reports/phase8_small_llm_gemma3_4b_cpu_event_context_v5_history8_seed43_20260925.json`.
  Against seed 42, both runs have the same v5 protocol, all 74 case IDs, and
  identical prompts; both are CPU-only with zero collection failures. Response
  text differs on 0/74 cases at temperature 0. This is a deterministic
  repeatability check only, not independent capability sampling or a score.
- V5 remains raw-only and incomparable to the SUT until an explicitly matched
  target run, blinded dual annotation, human references, and memory/learning/
  cost probes are available. Comparative release remains blocked.

### 2026-09-25 — Phase 7N duplicate topic-retrieval cost

- The four-event `cProfile` slice identified overlapping HTTP retrieval:
  `_answer_topic_reply` phrase grounding and the graph-minted
  `SearchRequest` both performed live lookups for the same answer topic. When
  that exact request is pending, topic self-heal now remains local and the
  graph request owns remote retrieval. The same traced workload fell from 24
  to 12 HTTP GETs and from 6.28 s to 3.96 s traced elapsed time.
- Same-73-seed full-corpus single-pass report:
  `evaluation/reports/phase7_profile_resource_20260925_full74_single_search_selfheal_17key.json`.
  It covers 74 events with zero errors and complete closure. Compared with the
  immediately preceding same-key single pass, summed conversation latency
  fell from 9,289.3 ms to 8,252.0 ms, max event from 1,934.8 ms to 1,567.4 ms,
  and RSS from 108,576,768 to 108,216,320 bytes. These are noisy single-run
  measurements: the deterministic two-pass verification report records a
  2,052.8 ms maximum event. The latency/resource gates remain open.
- Cross-version stable-observation comparison differed on `info_reference`
  (production receipt and answer-topic outcome fields). Case review resolves
  the disposition: the fixture expects `repair`, and current native repair
  correctly blocks topic grounding/release and returns the explicit error;
  the prior observation incorrectly ran topic fulfillment and recorded an
  unresolved answer-topic outcome. This is an intentional authority correction,
  not parity. Current-code repeated replay is deterministic. Focused topic,
  grounding, and fetch-dispatch suite: **51 passed, 1 skipped**; compilation
  and `git diff --check` pass.

### 2026-09-25 — Remaining action-event retrieval is a cognition mismatch

- The same resource report's next slow events are `info_unknown` (876.5 ms),
  `action_defer` (461.9 ms), and `action_check` (432.8 ms). Structural
  readback shows the action cases entered `answer_topic`: `action_check` was
  interpreted as `statement` with `comp_intent=assert`, while
  `action_defer` was interpreted as a `question` with
  `comp_intent=ask_world:unresolved`. Those answer-topic goals are why the
  selected retrieval path still spends hundreds of milliseconds on events
  labeled by the fixture as `act` and `defer`.
- The evaluator supplied only the signal and typed interaction mode/relation;
  it did not pass the fixture's expected `literal_form`, force, goal, or state
  labels. This is therefore a live language-to-cognition recognition gap, not
  evidence that those labels entered the runtime. The scoped grammar/evidence
  increment for bare and temporally fronted imperatives is recorded below;
  corpus labels remain excluded from runtime input.

### 2026-09-25 — Imperative evidence reaches native kind and action routing

- The existing `instruction_reading.is_verb_headed` native POS term now
  supplies adapter evidence for a bare verb-headed command and for the verb
  after a fronted comma-delimited condition. The signal-only inputs
  `Check the pressure.` and `When ready, close the hatch.` now enter the
  native `sak_kind` rules as instruction evidence; the graph selects
  `sak_kind=instruction` and existing instruction faculty emits the action
  goal. No reference `literal_form`, force, or expected goal is read.
- Bumped `conversation_topic_tracking` to 1.2.2 and added a native guard so an
  instruction with `topic_followup=1` cannot also mint an elliptical
  `answer_topic` goal from its object. The regression starts with an active
  current topic, checks the instruction goal and ensures there is no
  answer-topic goal or pending remote search for the action turn.
- Focused classifier + instruction evidence + topic tracking tests: **28
  passed**; targeted signal-only classifier/live-route tests: **18 passed**.
  The 133-item frozen speech-act parity battery still has its documented two
  failing tests (live parity and signal drift, including `Focus on the reading
  work.`); its fixture remains unchanged. These new phrases are held-out
  regressions, not retrofitted fixture labels.
- Fresh same-73-seed 74-event profile
  `evaluation/reports/phase7_profile_resource_20260925_full74_imperative_topic_guard_17key.json`
  has complete closure and zero errors. `action_check` is now an instruction
  with only its instruction goal and takes 68.1 ms; `action_defer` is an
  instruction with a deferred close goal and takes 96.6 ms. In a matched
  four-event trace, HTTP GETs fell again from 12 to 7, while remaining remote
  retrieval is confined to the two information-question events in that slice.
  The corpus maximum remains 3,163.6 ms (`info_unknown`) and absolute RSS is
  109,158,400 bytes; latency and memory acceptance remain open.

### 2026-09-25 — Ground/search fallback shares remote retrieval

- A trace of `info_unknown` found seven HTTP calls: two identical OpenSearch
  requests plus five summaries. Graph readback showed a same-topic
  `GroundRequest` and `SearchRequest`; the former should check local sources
  first and leave remote candidate/verification I/O to the latter. The adapter
  now calls the GroundRequest scan with `allow_web=false` only when a matching
  graph-selected SearchRequest is active. Standalone GroundRequests retain
  their prior web behavior; a local GroundRequest success still supersedes the
  SearchRequest, and a local miss leaves it eligible.
- Regression evidence covers the graph request pair, local-only propagation,
  aspect-grounding supersession, failed-specific fallback, and current-goal
  scoping: **12 passed**. Topic self-heal, SearchRequest minting, and held
  answer precedence: **17 passed**.
- In the same four-event cProfile workload, HTTP GETs fell 7→4 and traced wall
  time 3.331→2.712 s. Full 74-event same-73-seed profile
  `evaluation/reports/phase7_profile_resource_20260925_full74_single_remote_fallback_17key.json`
  has complete closure, zero errors, 1208.3 ms max event, 7118.8 ms summed
  conversation latency, and 108,933,120-byte RSS. `info_unknown` is 668.0 ms
  and `question_ack` 1208.3 ms in that pass. These event costs still exceed
  the 150 ms thought-manifold target; absolute RSS remains over 100 MiB, and
  resource exit is open.

### 2026-09-25 — Attribute `question_ack` search fanout

- Replayed the corpus prefix through `question_ack` with the connected 17-key
  profile and instrumented the shared HTTP getter and graph search dispatch.
  The event took 1,201.2 ms. It issued one graph-selected `SearchRequest` for
  `route`; its `GroundRequest` sibling was the local-only path and did not
  issue web calls. The single SearchRequest made one OpenSearch request and
  fetched five candidate summaries (`Route`, `Route nationale`, `Route of
  administration`, `Route (gridiron football)`, `Route number`). The six
  calls summed to 2,563 ms in concurrent candidate verification. Search
  selected/committed a generic route-of-administration answer.
- This is not duplicate GroundRequest/SearchRequest I/O. The unresolved issue
  is the case-level mismatch: signal-only cognition records
  `repair_or_defer` / `clarify_or_defer` for this standalone non-turn, while an
  `answer_topic(route)` goal still authorizes candidate search and a generic
  answer. No I/O suppression or answer-routing change was made; reconcile
  intent/reference authority before changing this path. Latency, cognition,
  production, and comparative/resource gates remain open.

### 2026-09-25 — Full-corpus connected-profile parity needs scoped content keys

- Compared full-seed and connected-profile runs across all 74 events using the
  connected profile's existing 17 content keys. Closure was reported complete
  and both runs had zero errors, but only **18/74** structural observations
  matched. This is not a valid full-corpus parity result: the 17 keys came from
  the smaller eight-event workload, so the profile omitted input vocabulary
  such as `sky` and `blue` from `standalone_assertion`.
- A one-event follow-up isolates that content-coverage error: the incomplete
  set differs only in mention-referents; supplying the known lexical keys
  `the`, `sky`, and `blue` restores **1/1** structural parity with complete
  selection closure. This does not establish 74-event parity or justify
  passing every raw token: unconstrained exact names can pull unrelated seed
  providers and have previously failed closure. The missing work is a
  language-neutral, typed content-key producer/scoping boundary, followed by
  full-corpus parity and resource remeasurement. Do not interpret the 18/74
  run as proof of intrinsic cognition mismatch or connected-loader failure.

### 2026-09-25 — Add scoped typed content references to seed pre-pass

- The cached seed index now retains exact named node references as
  `(seed_id, node_type, name)` tuples. `load_all_seeds` and the conversation
  profile accept `scoped_content_refs`, which select a named seed and validate
  exact typed node names only in that seed; they do not select all same-name
  providers elsewhere. Existing flat `content_keys` behavior is unchanged.
  Selective manifests slice by both node type and name. Missing scoped refs
  make selection incomplete and fail closed before graph mutation.
- Seed-loader tests pass **13/13**. A full-vs-connected single-event
  `standalone_assertion` regression with explicit lexical refs (`the`, `sky`,
  `blue`) plus the relevant `colour_meaning:Concept/blue` provider passes
  **1/1**; the existing eight-event connected-profile parity regression passes
  **8/8**. `py_compile` and `git diff --check` pass.
- This is the scoped selection boundary, not the producer: no runtime path yet
  emits these typed references from graph-grounded comprehension. The 74-event
  profile comparison and RSS/latency gates remain open and must be rerun after
  that producer is integrated.

### 2026-09-25 — Reject unscoped `Concept/name` as the content producer

- A read-only candidate-closure prototype scanned only event signals (not
  corpus labels), retained exact words present in `learned_lexicon`, and
  matched them against typed `Concept/name` providers. Across the 74 events,
  145 unique words yielded 81 lexical keys, 66 provider seeds, and a 95-seed
  dependency/content closure. Sixteen keys still had multiple providers.
- The ambiguous key `signal` reaches
  `operating_systems -> compiler_theory -> llvm_passes`; the selected closure
  then fails on the missing declared dependency `llvm_ir`. Thus adding a
  `Concept` type filter to raw surface matching is insufficient and cannot be
  used as the producer. The loader must receive source/sense-scoped refs from
  a graph-grounded resolver; the scoped API added above is the transport seam.
  No selection policy was changed from this diagnostic. Full-corpus parity and
  resource gates remain open.

### 2026-09-25 — Recheck resource envelope after seed-index v4

- Fresh CLI reports exercise the legacy connected-profile 17-key policy (not
  the new scoped-ref parameter). The eight-event report
  `evaluation/reports/phase7_profile_resource_20260925_conversation_seed_index_v4_17key_recheck.json`
  selects 73 seeds completely, has zero errors, **87,015,424-byte** RSS,
  **60,903,424-byte** boot+event growth, and **76.4 ms** maximum event; all
  reported resource assertions pass for that bounded workload.
- The full-corpus report
  `evaluation/reports/phase7_profile_resource_20260925_full74_seed_index_v4_17key_recheck.json`
  also selects 73 seeds completely with zero errors, but reaches
  **108,240,896-byte** RSS and **1,367.5 ms** maximum event (`question_ack`);
  `info_unknown` is 660.2 ms and summed event latency is 7,343.8 ms. Absolute
  RSS exceeds the 100 MiB bound by **3,383,296 bytes**; the 150 ms thought
  target also fails. This is a current 17-key resource recheck, not a full-seed
  parity or typed-ref evaluation. Broad parity and resource exit remain open.

### 2026-09-25 — Resume `question_ack` evidence audit

- The isolated typed parse is a polar question with predicate `confirm`,
  subject `you`, object `route`, and a determiner; comprehension selects the
  reflexive `frontier` path. The live answer path then creates a
  same-message `answer_topic(route)` goal and a supported `HeldAnswer` plus
  `TopicGroundingEvidence`. This is enough native evidence to resolve the
  frontier hypothesis without using the corpus label or answer surface.
- Added native rule `arbitrate_supported_event_topic_answer`. It requires an
  exact-message `answer_topic` goal, matching active held answer, matching
  supported topic-grounding evidence, non-turn standalone context, and a
  reflexive frontier with candidate grounding. A goal or reply alone cannot
  promote the event. Added positive and missing-evidence negative graph-rule
  regressions. The complete arbitration suite passes **10/10**; the broader
  arbitration/topic/loading slice passed **36/36** before this rule was added.
- Fresh isolated Phase 8 execution of `question_ack` now has native
  `request_information` force, authoritative `answer` disposition, grounded
  event-bound answer evidence, released parse-back gate, and no runtime error.
  The reply is still the adapter-rendered external topic result; this change
  establishes the native selection authority, not semantic adequacy of every
  retrieved summary.
- Fresh 74-event signal-only report
  `evaluation/reports/phase8_corpus_report_20260925_supported_event_topic_answer.json`:
  zero execution errors; force exact-match **42/74**; graph disposition
  authority **48/74**, with **43/48** authoritative states matching and five
  authoritative action/repair mismatches; grounding **19/50** (precision
  **1.00**, recall **0.38**, F1 **0.551**). The release gate remains blocked
  at provenance; Phase 4 still has zero complete tuples/promotions. This
  full-corpus report is not a resource run, so the earlier RSS/latency figures
  must not be carried forward as post-change measurements.
- A previous narrow regression slice passes **36/36**:
  `test_language_neutral_evidence_arbitration.py`,
  `test_topic_route_selfheal_migrated.py`, and
  `test_seed_loader_quiet_boot_migrated.py`.
- A paired current-source 74-event control was run with only this rule
  removed in-memory (no seed/cache files changed). Both arms had 0 event errors,
  48 authoritative states, the same five action/repair mismatches, and
  identical grounding counts/metrics (19/50; F1 0.551). Force exact-match
  improved **41/74 → 42/74**; `question_ack` changed from
  `repair_or_defer` to `request_information` while its answer state was already
  graph-grounded. The rule introduced no change to the other observed native
  states or grounding outcomes in this comparison. Do not treat the label
  match as semantic validation of the external summary.
- Next rerun the connected 74-event resource profile against this post-rule
  source, then continue the remaining cognition, Phase 4, production,
  latency/RSS, and comparative gates.

### 2026-09-25 — Post-rule corpus/resource recheck and declarative transport fix

- The Phase 8 transport test exposed a separate boundary error: a discourse
  initial refusal marker followed by a declarative clause
  (`No, I may have misread it.`) fell through to verb-head detection and was
  mislabeled as a request. `WorldAdapter.classify_speech_act` now keeps this
  transport category `statement` unless the following clause is itself a
  recognized imperative; graph cognition still derives correction/refusal/
  repair from the full typed parse. The previously failing corpus-transport
  test passes **1/1** after the change, and the focused uncertain-continuation
  cognition regression passes **1/1**. The combined route/Phase 8 suite had
  **38 passed / 1 failed** before this targeted correction; a full post-fix
  rerun now passes **39/39** (`tests/test_topic_route_selfheal_migrated.py`
  and `tests/test_phase8_corpus_runner.py`, 645.87 seconds).
- Fresh 74-event Phase 8 report after both changes:
  `evaluation/reports/phase8_corpus_report_20260925_supported_event_topic_answer_transport_recheck.json`.
  There are **0** execution errors; force exact-match is **45/74**; native
  disposition authority is **46/74**, with **43/46** authoritative states
  matching and three mismatches (`action_check`, `correction_route`,
  `social_address`). Grounding remains zero-false-positive at **18/50**
  (precision **1.00**, recall **0.36**, F1 **0.529**). `question_ack` now has
  native `request_information` force, authoritative answer disposition,
  candidate grounding, and released production. `correction_uncertain` no
  longer routes as an action, but lacks native disposition authority.
- Same-source 74-event control with only the supported-event answer rule
  removed in memory: **0** errors, **46** authoritative states, the same
  three authoritative mismatches, and identical grounding. Force matches are
  **44/74** instead of **45/74**; `question_ack` remains graph-state `answer`
  but reverts to `repair_or_defer` force. The rule therefore improves this
  event's native force only, without changing measured state or grounding
  results in the paired control.
- Fresh connected 74-event profile after both changes:
  `evaluation/reports/phase7_profile_resource_20260925_full74_supported_event_topic_answer_transport_recheck_17key.json`.
  It selected **73** seeds with complete closure and **0** errors; peak RSS is
  **109,121,536 bytes**, boot/event growth **83,132,416 bytes**, maximum event
  **1,276.8 ms** (`question_ack`), and total conversation time **10,634.1 ms**.
  Growth bounds pass, but absolute RSS remains above 100 MiB and latency is
  over the 150 ms target. This is the current post-change resource measurement;
  older figures are not substitutes.
- Current remaining work: resolve the three action/repair mismatches with
  typed producer/native authority; establish native authority for correction
  uncertainty; produce complete Phase 4 tuples; reduce absolute memory and
  per-event latency; and close comparative provenance/human-reference gaps.
  No overall phase or release gate is closed by this increment.
- The next `correction_uncertain` parse audit confirms why its disposition
  remains unauthoritative: the frame types `may` as a content verb, `have` as
  an auxiliary, and `it` as a pronoun object, but it supplies no typed
  epistemic-modality or resolved/unresolved antecedent evidence. Runtime
  ingress correctly omits the fixture's `explicit_uncertainty` label. Do not
  teach cognition to read that label or key on the word `may`; the upstream
  language adapter needs a semantic modality/reference evidence contract
  before native arbitration can close this event.

### 2026-09-25 — Adapter-owned epistemic modality for uncertain continuation

- The English comprehension adapter now emits the neutral category
  `epistemic_possibility` for a typed modal + perfect auxiliary + lexical-verb
  statement construction. A bare modal does not qualify, preserving the
  distinction from permission/ability readings; e.g. a modal permission
  question retains its separate `typed_modal_action_frame` evidence.
- Interpretation materialization preserves this modality evidence, and the
  native uncertain-continuation rule accepts it without relying on the
  externally annotated `explicit_uncertainty` flag. The generic declarative
  rule is gated off for such typed modality so it cannot overwrite the more
  specific arbitration basis.
- Runtime integration regression for `No, I may have misread it.` passes with
  `explicit_uncertainty=0`, native `repair`, and
  `uncertain_continuing_common_ground_event`; permission-question negative
  control passes. Focused test command:
  `.venv/bin/pytest -q tests/test_language_neutral_evidence_arbitration.py -k epistemic_modal_perfect`
  => **1 passed**. The first full focused-suite run was **10 passed / 1
  failed** only because its negative control incorrectly expected the
  permission question to have no modality evidence; the corrected control
  distinguishes the adapter's permission tag from epistemic possibility.
- Full language-neutral/explicit-uncertainty focused run initially reported
  **21 passed / 1 failed**: suppressing the generic declarative rule also
  removed its force assignment. The specific modality-repair rule now assigns
  the adapter-supported `assertion_or_correction` force itself. Both the new
  modality regression and the pre-existing explicit-uncertainty regression
  pass individually after that correction (**1/1** each); the broad combined
  suite has not yet been repeated.
- The Phase 8 report has not yet been regenerated after this change. The
  corresponding `correction_uncertain` corpus state, full evidence suite, and
  resource/latency impact remain pending; this is not a release or phase gate
  closure. The construction is a narrow adapter heuristic pending validation
  over broader languages and modal-perfect uses.

### 2026-09-25 — Epistemic modality corpus confirmation

- Corrected combined validation now passes: `.venv/bin/pytest -q
  tests/test_language_neutral_evidence_arbitration.py
  tests/test_phase6_explicit_uncertainty.py` => **22 passed in 486.40 s**.
- Fresh full fixed-corpus replay:
  `evaluation/reports/phase8_corpus_report_20260925_epistemic_modality_recheck.json`
  (Phase 8A fixed corpus v4, 74 events, 0 execution errors). The
  `correction_uncertain` event now has **native graph disposition authority**,
  matches expected `repair`, and preserves `assertion_or_correction` force
  with runtime `explicit_uncertainty=0`. Its response release is still an
  error, so this closes only the cognition authority/state mismatch, not
  production.
- Overall native disposition authority is **47/74**, up from the previous
  post-rule recheck's 46/74. Grounding is unchanged at 18/50 (precision 1.00,
  recall .36, F1 .529). Three authoritative state mismatches remain:
  `action_check` (expected act, observed defer), `correction_route` (expected
  defer, observed act), and `social_address` (expected answer, observed act).
  Resource/latency impact has not yet been reprofiled. The comparative release
  gate remains blocked for missing external reference evidence; no overall
  acceptance gate is closed by this result.
- This corpus run supersedes the preceding note that `correction_uncertain`
  lacked native disposition authority. The narrow modal-perfect heuristic
  still needs broader false-positive/language coverage.

### 2026-09-25 — Comma-prefatory action parse and discourse arbitration

- Imperative head extraction now reparses the clause after an initial comma
  constituent (and removes a recognized leading politeness marker) before
  mapping the action head back into the complete frame. This fixes the parsed
  goal heads for `Actually, use the east path.` (`use`) and
  `Operator, please listen.` (`listen`) while preserving noun/POS-ambiguous
  bare heads and multi-action clauses. Full action-evidence suite passes
  **23/23**; later neutral-evidence positive/negative controls pass **4/4**.
- The English adapter emits neutral discourse evidence for a small lexical
  class of clause-initial corrective markers, and a separate addressed
  attention-request category for polite vocative attention constructions.
  Native rules consume only these neutral categories: the correction
  response becomes common-ground/defer rather than action; the addressed
  attention request becomes social-action/answer. Cognition does not read
  those English cues.
- Fresh 74-event replay:
  `evaluation/reports/phase8_corpus_report_20260925_discourse_relation_recheck.json`.
  It records zero execution errors, force exact-match **47/74** (0.635),
  native disposition authority **47/74**, and only one authoritative state
  mismatch (`action_check`; expected act, observed defer). `correction_route`
  and `social_address` now match force and disposition; `correction_uncertain`
  remains authoritative repair. Grounding stays at 18/50 (precision 1.00,
  recall .36, F1 .529). The comparative release gate remains blocked.
- Correct disposition does not yet imply correct production: the correction
  and social-address events still release the action faculty's “took on the
  goal” response; `correction_uncertain` still reaches the explicit error
  floor. The production path must honor graph-selected social/defer decisions
  before these cases can count as production-complete. Resource/latency
  reprofile after the adapter/rule changes remains pending.
- `action_check` is a substantive mismatch rather than a parse defect. The
  fixed corpus expects act for a non-turn standalone action, but the native
  policy defers non-turn actions even when concept-grounded; the trace also
  reports no attached world/faculty to execute `Check(pressure)`. Do not force
  an act disposition or alter the corpus label merely to improve the match;
  resolve this against the plan's action-authority semantics.

### 2026-09-25 — Discourse arbitration corpus recheck

- Full fixed-corpus report after the prefatory-clause and discourse rules:
  `evaluation/reports/phase8_corpus_report_20260925_discourse_relation_recheck.json`.
  The run has **0** execution errors; interpretation force exact-match improves
  to **47/74** (from 45/74 in the preceding post-modal recheck). Native
  disposition authority is **47/74**, with **46/47** authoritative state
  matches and only `action_check` remaining an authoritative state mismatch.
  `correction_route` now has correction force + defer; `social_address` has
  social-action force + answer; `correction_uncertain` remains native repair.
  Grounding stays 18/50, precision 1.00, recall .36, F1 .529.
- The run does not close production: `correction_route` and `social_address`
  still render through the action-goal bridge; `correction_uncertain` still
  fails closed at the explicit response error. These are now separated from
  their cognition states in the report. Do not count a selected state as a
  successful produced reply.
- Full Phase 8 remains blocked, the latest source changes have not yet been
  reprofiled for RSS/latency, and broad cognition/production, Phase 4, and
  comparative acceptance gates remain open.

### 2026-09-25 — Native repair production bridge and fresh resource profile

- A graph-selected `repair` with adapter-typed `language_repair_focus` now
  routes through the existing clarification faculty; Python reads the chosen
  disposition and focus but does not choose repair. The adapter supplies the
  pronoun focus `it` for the uncertain modal-perfect proposition. The new
  focused integration regression passes **1/1** and checks both native repair
  authority without a gold uncertainty flag and a non-error response containing
  the typed focus.
- Fresh Phase 8 report:
  `evaluation/reports/phase8_corpus_report_20260925_repair_release_recheck.json`.
  It has **0** execution errors, force exact-match **47/74**, native disposition
  authority **47/74**, **46/47** authoritative state matches, and only
  `action_check` as an authoritative mismatch. `correction_uncertain` now
  releases `I'm not familiar with 'it'; might I ask what it means?` with an
  exact released ProductionGateReceipt and recoverable parse-back. Its state is
  native `repair`; expected state matches. `correction_route` is authoritative
  defer and `social_address` authoritative answer; both replies still use the
  action-goal bridge and require semantic production review. Grounding remains
  18/50 (precision 1.00, recall .36, F1 .529). Comparative release remains
  blocked.
- Fresh connected Phase 7 profile with deterministic replay verification:
  `evaluation/reports/phase7_profile_resource_20260925_discourse_modality_full74_recheck.json`.
  All **74** events ran with zero errors; replay outputs are equal. Peak RSS is
  **109,441,024 bytes**, boot/event growth **83,312,640 bytes**, max event
  latency **1,230.5 ms**, and total conversation latency **9,347.6 ms**. Growth
  and determinism pass; absolute RSS exceeds the 100 MiB bound and max latency
  exceeds the 150 ms target. This reprofile includes both recent adapter/rule
  increments and supersedes older post-rule figures.
- Remaining work includes the `action_check` action-authority/corpus semantic
  discrepancy, social/corrective production semantics, the other 27 events
  lacking native disposition authority, grounding recall, Phase 4 complete
  tuples, absolute RSS and latency bounds, and comparative human/small-LLM
  evidence. No overall acceptance or release gate is closed.
- Comparative raw-input check: the local CPU `gemma3:4b` v5 event-context /
  history-8 collector already has two complete 74-event runs (seeds 42 and 43),
  both with `num_gpu=0` and zero collection failures. The two response streams
  are text-identical across all 74 cases. These remain raw outputs only—not
  capability scores. The current v5 raw-reference audit is incomplete (only
  one v5 run included in its audit envelope; modern LLM, ELIZA, and both human
  references missing), and v5 still lacks blinded adjudication and a target
  run under a preregistered matching input profile. Therefore no relative
  capability conclusion is authorized from this evidence.
- The resource trace's `question_ack` event takes **1,231.6 ms** and adds
  **4,612,096 bytes**, lazily importing HTTP transport. A sequence replay shows
  the graph's current topic immediately before the event was `sensor` and no
  `HeldAnswer(topic=route)` existed. The generated `route` HeldAnswer is created
  by `SearchRequest -> SearchCandidate -> RetrievalEvidence`; it is the
  pharmacological “route of administration” definition, not a route established
  in this dialogue. The context-aware Gemma raw response is also unsupported
  (“standard path”) and identical across its two CPU seeds. This is an input /
  grounding ambiguity, not evidence of model superiority or a successful
  substrate answer. The next retrieval/cognition audit must distinguish a
  graph-supported fact from a conversationally supported referent before
  treating `question_ack` as solved or its network latency as necessary.
- Follow-through on this audit: a typed polar proposition-confirmation request
  now carries adapter evidence and its parsed repair focus. Native arbitration
  treats an unsupported confirmation as repair, and generic `answer_topic`
  routing excludes it so a lexical web result cannot masquerade as
  conversational confirmation. The focused integration check passes (1/1).
  Existing route-self-heal/topic-span controls produced 15 passes before the
  long-running suite was interrupted at 8m24s (no failures reported; not a
  complete suite result);
  this does not resolve confirmation when relevant support already exists, or
  close grounding, performance, production, or comparative gates.

Production authority follow-through: the `converse()` action bridge now
declines to invoke `act_on_instruction` when native cognition selected
`defer`, `blocked`, or `error`, when typed social-act evidence selected
social coordination, or when the interpretation is an information request.
Focused live regressions for `correction_route`, `social_address`, and the
unsupported confirmation case pass **3/3**; they verify that the first two
cannot mint a same-event instruction Goal or release the false “took on the
goal” surface. A full-corpus replay is still required to verify reply quality
and measure downstream effects; broader production/release gates remain open.

2026-09-25 action-arbitration narrowing follow-through: typed
`deferred_condition` and its evidence category are now copied onto the native
interpretation. Graph arbitration selects `defer` for typed future-conditioned
actions, while a continuation or partially grounded action may retain `act`
only under its own evidence constraints. Standalone non-turn deferral is
narrowed to candidate-grounded/supported cases; it no longer captures all
non-turn actions. Focused regressions pass **9/9**. In the first corpus replay,
the continuation rule also captured an unresolved pronoun and a fragment; the
rule was tightened to imperative form and excludes typed unresolved
references. The guarded 74-event report
`evaluation/reports/phase8_corpus_report_20260925_action_arbitration_guarded.json`
restores **47/74** native-authoritative dispositions, with only
`question_ack` (repair vs fixture answer; dialogue lacks a supported route
referent) and `action_check` (defer vs fixture act; documented action-authority
discrepancy) as authoritative state mismatches. Force exact match is **48/74**
(0.649); grounding remains TP17/FP0/FN33/TN24 (precision 1.00, recall 0.34,
F1 0.507). The release gate remains blocked; Phase 4 has no complete tuple or
promotion, and this change has not closed production, resource, or comparative
acceptance gates.

Fresh resource reprofile after the guarded action-arbitration changes:
`evaluation/reports/phase7_profile_resource_20260925_action_arbitration_guarded.json`.
All **74** events completed without errors; independent replay was equal and
deterministic. Conversation peak RSS is **109,662,208 bytes**, boot/event RSS
growth **83,533,824 bytes**, maximum event latency **1,206.2 ms**, and total
latency **6,170.1 ms**. Growth bounds pass; the absolute 100 MiB RSS bound and
150 ms maximum-event target still fail. This supersedes the older Phase 7
profile figures above; resource acceptance remains open.

2026-09-25 causal retrieval source narrowing: `domains/causal_retrieval.py`
now filters Wikidata search results to exact normalized query-label matches
(Unicode compatibility normalization, case-folding, and whitespace only)
before fetching entity claims. A regression proves fuzzy neighboring labels
do not trigger detail retrieval. The dedicated causal-retrieval module passes
**5/5**, and the focused daemon/retrieval slice passes **6/6**. This is a
retrieval-integrity narrowing only: matching labels do not establish identity
with the graph Concept, candidates remain `candidate_unverified` with
`authority=none`, and no factual edge or answer is minted. Native entity
identity resolution, event-scoped causal verification, graph evidence
materialization, and production release remain open.

Broader regression recheck after the causal source filter:
`.venv/bin/python -m pytest -q tests/test_causal_retrieval.py tests/test_topic_grounding_migrated.py tests/test_action_evidence_and_defer.py`
completed **61 passed, 1 skipped** in 587.45 seconds. This covers the relevant
retrieval boundary, grounding fallbacks, daemon staging, and action/defer
lifecycle. It is not a full Phase 8 production run and does not close the
event-scoped causal-answer gate.

2026-09-25 native gap-reply disposition guard: `gap_awareness`'s
`note_unhandled_instruction_gap` rule now joins the message's graph-resident
interpretation and cannot file an instruction SelfConcern/reply when native
cognition selected `defer`, `answer`, `repair`, `blocked`, `error`, or `learn`.
This closes the route where a parser-level `comp_kind=instruction` and a
mechanically unhandled outcome overrode correction/social cognition. The
strengthened correction/social/deferred-condition regressions pass **3/3**;
they verify no same-event instruction Goal, SelfConcern, or false “instruction
to … filed as a gap” surface.

The fresh 74-event report
`evaluation/reports/phase8_corpus_report_20260925_gap_disposition_guarded.json`
preserves **47/74** authoritative dispositions, force **48/74**, grounding
TP17/FP0/FN33/TN24, and only the prior `question_ack` / `action_check`
authoritative mismatches. `correction_route` and `social_address` now fail
closed at the explicit error floor instead of emitting the false gap reply;
their production realization remains incomplete. The graph-level correction
is not a production pass.

Fresh Phase 7 reprofile
`evaluation/reports/phase7_profile_resource_20260925_gap_disposition_guarded.json`
has zero errors and equal deterministic replay across **74** events. Peak RSS
is **107,094,016 bytes**, boot/event growth **80,953,344 bytes**, maximum event
latency **1,462.1 ms**, and total latency **6,417.7 ms**. Growth bounds pass;
absolute RSS and latency targets fail. Dedicated gap-awareness tests report
**13 passed, 1 failed**: `test_resolved_topic_files_no_gap` still observes the
`moon` answer goal as unresolved. That is outside the changed instruction-gap
rule's predicates, but the failure remains open and is not claimed as
pre-existing without baseline evidence.

2026-09-25 causal relation-scope guard: language-adapter evidence now carries
neutral `relation_scope` categories, and the non-text semantic-event boundary
preserves/validates the same field. The current English adapter marks
past-event reason questions `event_specific`; native
`communication_causal_retrieval` only mints topic-level retrieval requests for
explicit `conceptual_general` scope. This prevents a topic-level Wikidata P828
claim from being mistaken for an explanation of a particular event. Focused
scope/request tests pass **5/5**. Full Phase 8 report
`evaluation/reports/phase8_corpus_report_20260925_reason_scope_neutral.json`
preserves **47/74** authoritative dispositions, force **48/74**, grounding
TP17/FP0/FN33/TN24 (precision 1.00, recall .34, F1 .507), and the same two
authoritative mismatches (`question_ack`, `action_check`). `info_explanation`
remains native `learn` with no answer commitment and the explicit error floor;
the incompatible topic-level retrieval request is no longer minted. This is
an authority/scope correction, not an answer-production success. A verified
event-scoped causal source, native evidence materialization, reply release,
resource acceptance, and comparative gates remain open.

2026-09-25 causal-retrieval boundary hardening: daemon-owner staging now
rejects externally returned causal candidates unless source label matches the
requested topic under exact normalized comparison, statement identity is
bounded/well-formed, and references use the bounded typed citation schema
(`P854` HTTPS URLs or `P248` entity IDs). Unknown properties and malformed
references fail closed. The candidate still carries
`epistemic_status=candidate_unverified` and `authority=none`; no edge or answer
is authorized by this stage. `tests/test_causal_retrieval.py` passes **7/7**.
Native binding of external entity IDs to graph concepts, verified causal
evidence materialization, release, and corpus-level evidence remain open.

2026-09-25 native identity-bound causal dispatch: a separate native seed now
copies a Wikidata ID only from a verified
`ExternalIdentityEvidence` node attached to the graph-resolved topic and links
it to the request. The daemon refuses an unbound request, retrieves only that
entity ID (no search-based entity selection), rejects a response whose exact
normalized label differs from the topic, and owner commit checks the same ID
binding. The conversation connected profile includes the identity-binding
seed. Focused causal/daemon tests pass **9/9** (31 unrelated tests deselected).
This does not yet acquire trusted identity evidence or promote P828 candidates
into causal edges; no corpus answer-release claim is made.

The current causal-retrieval seed source was not changed in this increment,
but its SHA256 (`5d0fcfb6745e1737e29c55dd1071aa77c13f68cef58032a6451dfd934324beb0`)
does not match the historical v1.7 corpus-lock value
(`fb3445828dae97b6aad46d646a914788f055d71a1cb56ec1c8388c586ba07cc8`). The
historical lock was not rewritten; reconcile this source/lock drift under an
explicit evaluation-provenance decision before using that locked benchmark.

The full v5 Phase 8 replay
`evaluation/reports/phase8_corpus_report_20260925_identity_bound_causal_request.json`
completed 74 events with no errors, preserves 47/74 authoritative dispositions
and grounding F1 .507, and remains blocked with zero Phase 4 complete tuples or
promotions. `info_explanation` remains native `learn` with the explicit error
floor. The 74-event connected resource report
`evaluation/reports/phase7_profile_resource_20260925_identity_bound_causal_request.json`
selects all 68 seeds and verifies equal deterministic replay/no errors; peak
RSS is 107,393,024 bytes, boot/event growth 81,244,160 bytes, and max event
latency 1,218.9 ms. Growth passes but absolute RSS and latency remain outside
the envelope. No cognition, production, or resource acceptance gate is closed.

2026-09-25 cited claim staging: a native rule now transforms a staged P828
candidate into a provenance-linked `CausalClaimEvidence` node only if the
effect and cause concepts both link to verified Wikidata identity evidence.
The node retains its candidate, request, effect, cause, statement, citation
count, and source URL path. It does not create `causal_influence` and does not
authorize production; a sourced claim is not independently established causal
truth. Focused causal, daemon, and profile tests pass **11 passed, 43
deselected**. Full Phase 8 remains at 47/74 authoritative dispositions,
grounding F1 .507, no Phase 4 complete tuples/promotions, and blocked release.
Full Phase 7 replay is deterministic/error-free, but 107,540,480-byte peak
RSS and 1,205.2-ms max event latency still exceed absolute gates. Trusted
identity acquisition, claim adjudication, and a language-neutral supported
cause-to-response path remain open.

2026-09-25 answer-topic outcome lifecycle correction: `WorldAdapter` no
longer records a routed topic as `unresolved` while its graph-minted
`GroundRequest` or `SearchRequest` is still pending. It records `pending`
during active retrieval, then records the terminal outcome after turn-scoped
I/O and before the native gap-awareness pass. `resolved` requires supported
graph-held topic evidence; a settled miss remains `unresolved`, so the native
gap rule still files genuine misses. The previously failing
`test_resolved_topic_files_no_gap` now passes; the complete
`tests/test_gap_awareness_migrated.py` suite passes **9/9**, including forced
miss and self-account-gap controls.

Fresh full v5 Phase 8 report
`evaluation/reports/phase8_corpus_report_20260925_topic_outcome_lifecycle.json`
completed all 74 events without runtime errors. It remains blocked at 47/74
authoritative dispositions, force exact 48/74, grounding TP17/FP0/FN33/TN24
(F1 .507), and zero Phase 4 complete tuples/promotions. The fresh 74-event
conversation Phase 7 profile
`evaluation/reports/phase7_profile_resource_20260925_topic_outcome_lifecycle.json`
has deterministic equal replay and zero errors, but peak RSS is 107,487,232
bytes and maximum event latency is 1,215.8 ms; absolute resource/latency gates
remain open. Production, causal answer, identity acquisition, and comparative
reference gates remain open.

2026-09-25 typed standalone assertion disposition: Phase 8 showed
`assertion_or_correction` plus standalone/non-turn metadata was too broad to
authorize defer; it also matched offer, refusal, social, learning-report, and
error events with no typed assertion evidence. That broad rule/report was
rejected and its temporary reports removed. The language adapter now emits the
neutral `language_statement_act=assertion` category only when its parse marks a
copular declarative assertion; native `defer_standalone_nonturn_common_ground_update`
requires this typed category in addition to neutral force and interaction
metadata. A generic force-only negative control fails closed, and the
turn-compatible contrast remains untouched. The complete
`tests/test_language_neutral_evidence_arbitration.py` suite passes **21/21**.

Fresh v5 Phase 8 report
`evaluation/reports/phase8_corpus_report_20260925_typed_standalone_assertion_defer.json`
has zero execution errors and raises native disposition authority from 47/74
to **49/74**, with both standalone assertion cases matching defer and no lost
prior authoritative cases. The known offer/refusal/social/learning/error cases
remain unclassified rather than being mislabelled. Grounding remains TP17/FP0/
FN33/TN24 (F1 .507); Phase 4 complete tuples/promotions remain zero; release is
blocked. Fresh full connected Phase 7 report
`evaluation/reports/phase7_profile_resource_20260925_typed_standalone_assertion_defer.json`
is replay-equal/error-free at 74 events, but peak RSS is 107,675,648 bytes,
growth 81,518,592 bytes, and max event latency 1,209.8 ms. Growth and
determinism pass; absolute RSS/latency, substantive production, grounding
recall, Phase 4, and comparative gates remain open. The standalone assertion
  received the explicit production error at the time because the graph
  expected acknowledgement but no realization was yet authorized; the
  subsequent graph-owned receipt is recorded below.

### 2026-09-25 — Native non-endorsing receipt for standalone assertions

The typed `standalone_nonturn_common_ground` defer now has a graph-owned
`neutral_receipt` acknowledgment rule. `WorldAdapter` releases only the
corresponding marked reply node, after validating its selected speech act and
surface, through the existing production gate. The production record uses
`acknowledge_receipt_without_endorsement`; the rule never changes the deferred
disposition or writes proposition acceptance. The focused end-to-end regression
passes (1/1), including exactly one graph reply and one released receipt. The
full language-neutral suite passes **21/21**. Fresh Phase 8 v5 report
`evaluation/reports/phase8_corpus_report_20260925_typed_standalone_assertion_neutral_receipt.json`
confirms release for both target assertions and zero event errors; 49/74
dispositions are authoritative, grounding F1 is .507, and Phase 4 promotions
remain zero. Fresh 74-event connected Phase 7 report
`evaluation/reports/phase7_profile_resource_20260925_typed_standalone_assertion_neutral_receipt.json`
is replay-equal/error-free at 107,917,312-byte peak RSS and 1,207.9-ms maximum
event latency. Corpus cognition, grounding, absolute resource, Phase 4, causal,
and comparative gates remain open.

### 2026-09-25 — Daemon integration of native receipts

The live daemon now runs a closed receipt dispatcher for graph-selected
standalone assertion, correction, and social receipts. Readback prefers a
typed receipt to the honest floor only after a same-turn released production
record exists. The actual daemon regression and related daemon/debug plus
synchronous receipt checks pass **6/6**. The targeted async standalone event
settles with native `defer`, one released `acknowledge_receipt_without_endorsement`
receipt, and 32.6/2.6-ms ingress/native-cycle latency at 83,738,624-byte RSS.
The full async corpus releases both standalone receipts, but authority remains
35/74, one turn remains pending, and RSS is 109,150,208 bytes; no full-corpus
cognition or resource gate is claimed closed.

### 2026-09-25 — Explicit async failure terminality

The graph-owned honest-floor diagnostic now has a typed `explicit_error`
terminal outcome. Daemon polling returns `status=error`; turn bookkeeping closes
the pending entry without recording an error as a normal released response.
The daemon-debug suite passes **6/6**, including the HTTP error-status route.
The fresh 74-event async profile records 60 errors, 7 released replies, 2
no-response terminals, and 5 still-pending events (four missing async
production-release bridges and one textless expected answer). The two
standalone assertion receipts release. Ingress/native cycle maxima are
37.5/25.3 ms; peak RSS 105,721,856 bytes remains over the 100 MiB threshold.
Disposition coverage, those five production paths, retrieval completion,
resource, Phase 4, and comparative gates remain open.

### 2026-09-26 — Deferred-action production parity

A typed temporal instruction already had a graph-resident
`Goal{status=deferred}`, but the Python action faculty still surfaced “I took on
the goal…” and the graph production bridge hard-coded semantic intent `act`.
The surface now states only that the request is deferred and that no attached
world/faculty can carry it out; the production receipt reads back `defer` from
the committed Goal lifecycle state. The regression asserts deferred wording,
no “took on” claim, a deferred Goal, and exactly one released `defer` receipt.
The focused regression and related production/action cases passed within a
broader run (**39 passed** before that slow suite was interrupted); no new Phase
8 corpus replay was run. This fixes surface/receipt parity only and does not
claim future execution or close the remaining corpus, grounding, resource,
production, or comparative gates.

Fresh full 74-event Phase 8 v4 replay
`evaluation/reports/phase8_corpus_report_20260926_deferred_action_production_parity.json`
confirms the correction against the canonical corpus path: `action_defer` is
native-authoritative `defer`, releases the exact deferred response, and records
`semantic_intent=defer`. Aggregate cognition is unchanged: 49/74 dispositions
are authoritative, force match 48/74, grounding F1 .507, and Phase 4 still has
three grounding-only sources / zero complete tuples. The comparative release
gate remains blocked. This verifies one production-parity seam only.

### 2026-09-26 — Matched-context LLM reference collection

The target has now been replayed under v5 event-context/history-8 at
`evaluation/reports/phase8_corpus_report_20260926_event_context_v5_target.json`.
The raw reference audit
`evaluation/reports/phase8_raw_reference_audit_20260926_v5_llm_classes.json`
confirms two complete 74-case runs each for CPU `gemma3:4b` and
`qwen3.5:9b`, with zero collection failures; the auditor did not interpret
outputs as scores. Gemma's two runs have identical prompts and outputs on
74/74 cases. Qwen's first output diverges across runs, after which dialogue
history prompts also diverge (only 1/74 case has matching prompts/outputs).
The target replay retains 49/74 authoritative dispositions, grounding F1
.507, and zero complete Phase 4 tuples. Human baselines and blinded dual
annotations are still missing; v5 is input-context matching, not capability
equivalence or full graph-memory parity, and the comparative gate remains
blocked.

### 2026-09-26 — Statement continuation and released-reply trace parity

The five-statement continuity gate previously failed on its first turn because
the generic graph error floor returned before the existing grounded
continuation faculty could record a `ConversationDecisionState`. A guarded
continuation opportunity now runs only for a statement whose graph reply is a
generic floor and whose interpretation has no explicit native disposition;
the unsupported-statement error control remains passing. Its adapter-authored
surface is linked to the measured decision-state ID/token, and turn readback
prefers the newest exact-bound message.

`reply_turn_trace` now prefers a production surface only when its
`ProductionGateReceipt` is released, bound to the same inbound, and linked to
the committed graph node. The receipt is release authority, not cognitive
authority. The continuity, deliberative-production, grammar-inversion, Phase
6A, and action/defer battery passes **46/46**. Fresh 74-event report
`evaluation/reports/phase8_corpus_report_20260926_statement_and_receipt_trace_v5_final.json`
retains 49/74 authoritative dispositions, force match 48/74, grounding F1
.507, 36 explicit errors, and 32 released responses. Reply/trace surface
mismatches fell from **24 to 9**. The nine residuals include non-turn
no-response semantics and other production paths. Phase 4 and comparative
release remain open.

### 2026-09-26 — Adapter-realized answer trace

Inspection of the `information_question` mismatch showed that the answer-force
commitment is a turn-linked graph Message without surface text, while the
selected substantive answer is explicitly marked as adapter-realized on the
inbound parse. The trace now exposes that adapter surface only when a supported,
turn-compatible graph answer commitment exists, the reply route is explicitly
`adapter`, and no released production receipt takes precedence; it does not
misidentify a generic floor Message as the answer. The regression test and the
reason-question-without-causal-support negative control pass. Fresh report
`evaluation/reports/phase8_corpus_report_20260926_adapter_answer_trace_v7.json`
reduces reply/trace mismatches **9 → 8** across 74 events. Authoritative
dispositions remain 49/74 and grounding F1 remains **0.507**; the comparative
gate stays blocked. The eight remaining trace differences require separate
contract-specific investigation.

### 2026-09-26 — Finalized turn-outcome trace parity

The remaining eight cases exposed that trace readback selected the newest
turn-linked graph Message, which can be an intermediate thought/ask-back or
error floor rather than the exact return value of `converse()`. The common
turn-finalization boundary now records the public reply surface and source,
including deliberate silence; the two early non-turn-fragment returns now use
that same boundary. Trace associates a Message ID only when an exact-bound
Message carries the finalized surface. A fresh 74-event report,
`evaluation/reports/phase8_corpus_report_20260926_finalized_turn_trace_v8.json`,
shows **0/74 reply/trace mismatches** and zero execution errors. This does not
alter cognition or release scoring: authoritative dispositions remain 49/74,
grounding F1 .507, Phase 4 complete tuples zero, and comparative release
blocked. The focused trace, silence, unsupported-causal-question, and statement
continuity tests pass **4/4**. A broader legacy conversation-loop battery had
three failures on possessive self-report/scene actions that are currently
documented as unsupported by `conversation_self_reply`; these need a separate
feature/test-contract decision and are not counted as resolved by trace parity.

### 2026-09-26 — Turn-compatible unknown information request disposition

The v8 audit showed `question_weather` lacked native disposition authority even
though its independent label is `learn`. A new language-neutral arbitration
rule selects `learn` only for a turn-compatible interrogative information
request with unknown/unresolved grounding, no anaphoric dependency, and a
predicate mention that resolves to a held Concept. This avoids promoting a
social readiness question whose predicate is not graph-grounded. Positive,
non-turn-unknown, and social-question contrast checks pass. Fresh report
`evaluation/reports/phase8_corpus_report_20260926_grounded_predicate_learning_v10.json`
increases native-authoritative dispositions **49 → 50** and authoritative
state matches **48 → 49**, with the remaining authoritative mismatch still
`question_ack`; trace parity remains 0/74 mismatches and execution errors 0.
Grounding F1 remains .507 and the gate remains blocked. Important boundary:
`question_weather` still returns the explicit error and creates no event-bound
learning Goal or retrieval request at this v10 checkpoint. This closes state
selection only, not learning execution or answer production.

The follow-up rule now also mints one event-bound
`InformationLearningRequest{status=requested, authority=none,
source_policy=unselected, answer_authority=none}` linked to the source event,
interpretation, and held predicate Concept. The non-turn unknown and social
question controls mint no request. The Phase 8 runner now serializes these
typed request records in each observation. The fresh report
`evaluation/reports/phase8_corpus_report_20260926_learning_request_evidence_v12.json`
preserves v10 cognition metrics (50/74 authoritative, 49/50 matches), 0/74
trace mismatches, and zero execution errors. No consumer exists yet for this
request type, so the turn remains explicitly failed closed and learning
execution is still open.

### 2026-09-26 — Learning-request report accounting

Phase 8 now summarizes serialized `InformationLearningRequest` records by
count, event-bound count, status, and actual non-empty answer authority, while
explicitly stating that serialization is not execution. The `none` sentinel is
correctly treated as no answer authority. The corpus-contract assertion covers
the one pending weather request and its lack of authority; no retrieval or
answer behavior is changed by this instrumentation.
Fresh report `evaluation/reports/phase8_corpus_report_20260926_learning_request_accounting_v13.json`
confirms 1 requested/event-bound record, status `requested`, zero requests with
non-empty answer authority, and no execution. The run completes all 74 events
with zero errors; native authority remains 50/74, grounding F1 .507, and the
release gate remains blocked.

The request's semantic scope was checked against the available retrieval
consumer before extending it. The event is “Will it rain today?”; the current
`SearchRequest` consumer resolves static Wikipedia topic summaries, while the
request correctly records `source_policy=unselected` and has no location or
source evidence. Directly translating it to that consumer could mistake a
general article about rain for a current forecast. Therefore this is not merely
missing dispatch plumbing: the source-selection/context-resolution contract
must be established first, and answer authority must stay `none` meanwhile.

### 2026-09-26 — Connected seed pre-pass verification

The proposed connection-based loading shape is present as an opt-in bounded
boot profile: seed source manifests are scanned before graph mutation, a
source-byte-validated connectivity/grouping index is cached, anchor selections
resolve declared and typed-content dependency closure before installation, and
the conversation profile prewarms its connected runtime module set. Focused
verification passes **25/25** across
`tests/test_phase7_production_envelope.py` and
`tests/test_seed_loader_quiet_boot_migrated.py`, including same-stat source
change cache invalidation and zero additional manifest loads on the first
profile event. This confirms that implementation seam only; it does not close
full-boot/resource parity, broad event-family cognition parity, or the overall
upgrade gates. The pending `InformationLearningRequest` still has no consumer
and remains fail-closed without selected source or answer authority.

### 2026-09-26 — Phase 1 compound-command delta adjudication

The legacy parser-parity replay was rerun with the independent 20-event
force/goal adjudication: the latter remains **4/4 passed** while the historical
parity module remains **8 passed, 2 failed**. One mismatch is now explicitly
covered as a semantic contract rather than reverted to the snapshot: for
`look left then quorplezap the door`, graph readback must pair predicate
`look` with the first clause's typed target `left`, not the later clause's
`door`. A focused regression now checks this adapter-to-graph projection;
the action-evidence and comprehension suites pass **67/67**. This adjudicates
that compound-target delta only. The other fixture differences remain open
until their case-level semantics and full live outcomes are separately
verified; no frozen fixture was changed.

The `tell me about yourself` content mismatch was also checked at the complete
live boundary. Its legacy parse reports `tell(me)`, but the graph-native
`conversation_self_reply` route is required to select an event-bound
`report_self` goal from the reflexive referent and produce the self-account.
`tests/test_conversation_loop.py::test_act_tell_about_yourself` now asserts
that graph route explicitly and passes **1/1**. This adjudicates the live
cognitive route for that phrase; it does not establish exact linguistic
content parity or resolve the remaining frozen-parser differences.

### 2026-09-26 — Native promotion-route release parity

The Phase 1 `Focus` delta exposed a production-boundary conflict: the native
steering rule marked a concern and minted a same-event “Promoting” reply, but
without an explicit route marker the adapter rejected it as a selected
instruction response and let a generic Python concern-authoring path replace
it. The steering rule now writes `self_improvement_route=promote_concern`;
the adapter reads the concern through its graph `promote_requested_by` edge,
and the existing instruction readback gate checks the event and concern content
(including regular `promote` → `promoting` surface realization). A new isolated
contrast with an existing reading-work concern confirms the exact graph reply
is released with `semantic_event=promote` while the concern remains `noted`;
human-gated promotion is not bypassed. The focused contrast plus legacy
readback tests pass **11/11**, and the isolated new route test passes **1/1**.

The full steering module currently reports **17 passed, 5 failed**. The five
failures are in existing setup assumptions: “Summarise the report” and
“Transmogrify the data” currently take no-world instruction-goal replies rather
than filing the expected gap, causing downstream promotion/retirement/clarify
pipeline preconditions to fail. This remains a separate cognition/dispatch
defect; the new isolated `Focus ... gap` regression avoids shared-fixture
contamination and passes. Phase 1, broader production parity, and the overall
upgrade remain open.

### 2026-09-26 — Unhandled instruction reaches native gap arbitration

Removed the converse loop's catch-all call to `act_on_instruction` for every
remaining instruction-shaped `act` interpretation. Graph-claimed instruction
replies and explicit faculty routes (repair, deferred condition, perception,
etc.) retain precedence; an unclaimed instruction is now allowed through the
existing mechanical outcome recorder so `note_unhandled_instruction_gap` can
decide whether to file a capability gap. This avoids minting a generic Goal as
an adapter-side substitute for a missing native route. Verification:
`tests/test_nl_steering_migrated.py`,
`tests/test_comprehend_instruction_migrated.py`,
`tests/test_action_evidence_and_defer.py`, and
`tests/test_phase6a_legacy_readback.py` pass **60/60**; `git diff --check` is
clean for the adapter edit. The full manifold objective remains active, with
Phase 1 parity, corpus/resource, and comparative-evaluation gates still open.

Follow-up integration verification found that two explicit faculty cases had
been coupled to that broad fallback. The bridge now preserves the selected
self-account faculty evidence and the perceptual-scene route when a scene is
attached, while leaving unselected imperatives to native gap arbitration. The
conversation-loop, steering, and instruction suites pass **36/36**, including
both previously failing self-report/scene assertions and the unsupported-gap
steering preconditions. The Phase 6A/action-evidence suites passed before this
route refinement and should be included in the next combined regression run.

### 2026-09-26 — Graph-selected world-action completion and full replay

The combined action-evidence, Phase 6A, conversation-loop, steering, and
instruction regression battery now passes **73/73**. A fresh v5 Phase 8 replay
is recorded at
`evaluation/reports/phase8_corpus_report_20260926_native_world_action_v15.json`.
It identifies an existing `interpreted_instruction` Goal linked to the inbound
and a Mention resolving to a held `Concept{instruction_route:world_action}` as
the eligibility evidence for the action faculty to complete the conversational
Goal/reply. This recovers native event-bound action authority for
`direct_action` and `action_sequence` without stealing steering turns or
unsupported verbs. The two replay cases confirm
`graph_resident_event_bound_action_goal`; no world action is claimed executed.

The full replay records **48/74** authoritative dispositions, down from the
prior 50/74: `continuation_context` and `response_yes` no longer receive generic
host-minted action Goals and instead reach the honest capability-gap path. Their
interpretation currently says `act`, but neither has a committed event-bound
action Goal, so the runner correctly records
`interpretation_readback_not_disposition`; this remains a cognition/interaction
contract to resolve, not a metric to restore by relabeling. Grounding remains
precision **1.00**, recall **0.34**, F1 **0.507**; Phase 4 complete tuples and
promotions remain **0**; the pending learning request still has no consumer or
answer authority; comparative release remains blocked. This increment narrows
the adapter fallback to graph-selected world actions but closes none of those
broader gates.

### 2026-09-26 — Continuation action-head recovery

The unresolved continuation trace parsed the clause as `then(inspect)` because
the language adapter chose a leading adverb as the action predicate even though
the utterance's conjunction introduced a following typed verb head. Predicate
selection now skips that adverb only when a conjunction precedes it and a verb
head follows; the noun-tagged-imperative fallback remains unchanged. A focused
action-evidence test and the full suite pass **28/28**. A live continuation
readback now says it understood `inspect 'pump'` and files `inspect pump` as the
held capability gap; it does not claim an inspection faculty. The refreshed
74-event report
`evaluation/reports/phase8_corpus_report_20260926_continuation_head_v16.json`
keeps authority at **48/74**, with unchanged grounding F1 **0.507** and zero
Phase 4 complete tuples/promotions. `continuation_context` remains
interpretation-only (`act`) rather than an event-bound action commitment, and
`response_yes` remains unresolved; no score gain is claimed. Full cognition,
production, resource, and comparative acceptance gates remain open.

An independent-process connected-profile resource measurement after these
adapter changes is recorded at
`evaluation/reports/phase7_profile_resource_20260926_continuation_head_independent_v2.json`.
It selects all required seeds and completes 74/74 events with zero errors;
peak RSS is **101,330,944 bytes** (96.59 MiB), below the 100 MiB limit. The
maximum event is **1,458.4 ms**, and `info_unknown` is the only event above 150
ms: the measured pending retrieval call accounts for **1,358.2 ms**. This
reconfirms that native ingress/turn computation is not the main synchronous
latency outlier; the blocking boundary is awaiting retrieval. It does not
close the end-to-end latency target, nor justify skipping retrieval or
changing its grounded-answer behavior. The current independent measurement
does not include a second-process determinism replay.

### 2026-09-26 — Native causal-repair production release

The Phase 8 `question_followup` event already had a graph-selected
`repair/missing_causal_relation_with_anaphor` disposition but previously ended
at the error floor. The force-arbitration rules now avoid overwriting an
already-selected disposition's arbitration basis with the generic
`interrogative_force`/`indirect_request_force` basis. The causal-retrieval seed
then authors one event-bound clarification Message asking for event/evidence;
the adapter reads that exact graph message only after the second native rule
pass and releases it through the existing repair production gate. It does not
release the held topic summary as a causal answer. Re-entering the graph
fixpoint leaves exactly one repair reply.

Verification: the action-evidence, Phase 6A, causal retrieval, Phase 8 runner,
and information-production suites pass **86/86**; the two focused
causal-repair controls pass **2/2** again after adding the idempotence check.
Fresh replay
`evaluation/reports/phase8_corpus_report_20260926_causal_repair_release_v17.json`
releases `question_followup` with `semantic_event=repair`, `status=released`,
and the exact selected clarification surface. Corpus released responses rise
**32 → 33**; disposition authority remains **48/74**, grounding F1 remains
**0.507**, and Phase 4 complete tuples/promotions remain **0**. Comparative
release remains blocked. This closes the bounded causal-repair production
seam, not the overall production or cognition gate.

The asynchronous split was revalidated against current code with filtered
retrieval/daemon regressions (**20 passed, 19 deselected**) and a fresh full
daemon report at
`evaluation/reports/phase7_daemon_ingress_20260926_async_retrieval_continuation_v3.json`.
All 74 turns terminalized, all 26 selected host actions drained, 16 topic
grounding HTTP requests were dispatched, no errors or pending turns remained,
and peak RSS was **102,600,704 bytes** (97.85 MiB). Maximum ingress and native
cycle latency were **38.4 ms** and **29.0 ms**, respectively, both under their
bounds. Maximum end-to-end completion latency was **1,615.4 ms** because that
metric includes the remote retrieval wait. This verifies bounded cognition
and successful asynchronous completion, not the stricter synchronous or
end-to-end latency target; the retrieval wait remains explicit and measured.

The causal-repair update was then checked in a fresh async drain at
`evaluation/reports/phase7_daemon_ingress_20260926_causal_repair_async_v4.json`.
All **74/74** turns completed, all **26** selected host actions drained, and no
errors, pending turns, host actions, or ground requests remained. The
`question_followup` observation retained the graph-selected
`repair/missing_causal_relation_with_anaphor` interpretation and released its
clarification through `conversation_action_graph` with full coverage. Peak RSS
was **102,715,392 bytes** (97.96 MiB); max ingress/native-cycle latencies were
**37.8/36.8 ms**; max end-to-end completion was **1,357.8 ms** including remote
retrieval. All resource assertions passed. The async runner's own
`disposition_authority_count` is **35** (its async observation schema differs
from the Phase 8 corpus authority count of 48/74); it is not substituted for
the corpus acceptance metric. This confirms parity for the bounded repair
path, while the broader cognition, production, and comparative gates remain
open as described above.

### 2026-09-26 — Declarative correction evidence and native deferral

The Phase 8 `correction` event had been incorrectly left at an unset native
disposition because the language adapter only extracted correction discourse
relations inside its imperative/action-predicate branch. Correction-marker
evidence is now gathered independently of clause force (including a typed
copular `No, ...` correction), and a native graph rule maps typed declarative
corrections in response position to `defer/update_common_ground`. The existing
action-correction route is unchanged. The focused non-action-disposition
regression passes **4/4**, covering the declarative correction, imperative
correction, social attention, and future-conditioned action cases.
The complete language-neutral arbitration and Phase 8 runner suites pass
**50/50** after the change.

Fresh 74-event replay
`evaluation/reports/phase8_corpus_report_20260926_declarative_correction_v18.json`
now records `correction` as authoritative `defer`, with the graph-selected
“I understand the correction.” response released through the correction
production gate. Authority improves **48/74 → 49/74**. Aggregate grounding
remains precision **1.00**, recall **0.34**, F1 **0.507**; Phase 4 complete
tuples/promotions remain **0**; comparative release remains blocked. Other
typed assertion events still fail closed or lack disposition authority, so
this correction seam does not close the broader cognition or production gates.

### 2026-09-26 — Parsed predication evidence and response assertion receipt

The assertion events still lacked `language_statement_act=assertion` when the
language adapter parsed an eventive predicate rather than a copula. The
adapter now emits that neutral category for a structurally aligned
subject–predicate statement; it excludes graph-typed ability/refusal modal
frames and cases where the parser's first verb head does not align with its
selected predicate. Native cognition continues to own disposition selection.
For turn-compatible response assertions, a new graph rule selects
`defer/update_common_ground`, and a separate graph rule authors one neutral
acknowledgment. The adapter releases that exact message through the existing
recoverability gate; the receipt explicitly does not endorse or adopt the
proposition. Standalone assertion handling remains on its existing rule and
receipt.

Focused evidence/production controls pass **4/4**. The full language-neutral
arbitration and Phase 8 runner suites pass **52/52**. Fresh replay
`evaluation/reports/phase8_corpus_report_20260926_response_assertion_v21.json`
raises authoritative dispositions from **49/74** to **56/74**. The
`assertion_weather`, `assertion_uncertain`, `assertion_contradicted`, and
`assertion_source` events now have authoritative `defer` and released neutral
receipts; the graph-authored correction receipt remains intact. Aggregate
grounding remains precision **1.00**, recall **0.34**, F1 **0.507**; Phase 4
complete tuples/promotions remain **0**; comparative references remain
unavailable and the release gate remains blocked. Offer/refusal, several
learning/social cases, and the remaining six label matches without disposition
authority are still unresolved. Resource and full production gates have not
been reclosed by this cognition increment.

The same current code was exercised through the asynchronous daemon in
`evaluation/reports/phase7_daemon_ingress_20260926_assertion_response_v5.json`.
All **74/74** turns completed, all **26** selected host actions drained, and
there were no errors, pending turns, host actions, or ground requests. The two
response-assertion events released the graph-selected neutral acknowledgment
with coverage **1.0**; the `question_followup` causal repair also remained
released at coverage **1.0**. Peak RSS was **102,813,696 bytes** (98.05 MiB),
max ingress/native-cycle latencies were **37.7/49.0 ms**, and max completion
latency was **1,396.9 ms** including remote retrieval. All async resource
assertions passed. This verifies current-code async parity for these output
paths; the synchronous 150-ms event target, the async end-to-end retrieval
latency target, and full production/resource gates remain open.

The semantic-evidence adapter's graph-semantic lookup was then cached per
adapter and restricted to relevant modal/negation heads rather than rescanning
all concepts per utterance. Focused assertion/negation/response controls pass
**7/7** and `py_compile` passes. Fresh async report
`evaluation/reports/phase7_daemon_ingress_20260926_assertion_response_cached_v6.json`
preserves **74/74** completions and **26/26** host-action drains with no errors
or pending work; all resource assertions pass. Max ingress/native-cycle
latencies are **40.8/37.5 ms** (the prior uncached native maximum was 49.0 ms),
peak RSS **102,780,928 bytes** (97.99 MiB), and end-to-end completion maximum
**1,358.3 ms** including retrieval. This closes the observed native-cycle
headroom regression but not the synchronous event-latency or retrieval-inclusive
completion target. The last complete 74-event cognition replay remains v22;
this caching change preserves its semantics and is covered by focused checks.

### 2026-09-26 — Current connected-profile resource and Phase 4 source re-audit

The machine-readable Phase 4 manifest audit was rerun against the current seed
tree: **0 exact and 0 near-match** seed records for the complete
`grounding/expected_value/residual_cost/consequence/novelty` tuple; the only
approved source type remains `ThoughtManifold`. The existing-faculty reuse
audit still finds no authorized complete tuple, so no candidate promotion is
made from incompatible adjacent measures.

Fresh connected-profile measurement
`evaluation/reports/phase7_profile_resource_20260926_assertion_response_connected_v7.json`
selects **70/70** required seeds with no unresolved dependency, processes all
74 events without error, and peaks at **100,966,400 bytes** (96.29 MiB); all
connected-profile memory assertions pass. Its maximum synchronous event is
**1,220.6 ms**, above the 150-ms target. A separate fresh-process replay
measurement
`evaluation/reports/phase7_profile_resource_20260926_assertion_response_determinism_v8.json`
records deterministic replay; selection, graph-growth, errors, and resource
assertions exactly match v7. It peaks at **101,232,640 bytes** (96.47 MiB),
with **1,211.3 ms** maximum event latency. Thus connected memory and replay
determinism pass, while synchronous end-to-end latency remains open.

For scope clarity, the separate all-seed `full` profile report
`evaluation/reports/phase7_profile_resource_20260926_assertion_response_v6.json`
does not meet resource bounds: it reaches **1,438,978,048 bytes** peak RSS and
**3,174.5 ms** maximum conversation latency, with absolute/growth assertions
false. This all-seed figure is not conflated with the closure-complete
connected conversation profile; full-boot resource reduction remains an open
Phase 7 criterion.

A subsequent negative-control replay
`evaluation/reports/phase8_corpus_report_20260926_assertion_negation_guard_v22.json`
confirmed that graph-lexicon-marked negation must not be relabeled as a generic
assertion: the v21 response rule had incorrectly made `refusal_unknown`
authoritatively `defer` rather than the required unresolved/blocked path. The
adapter now withholds assertion evidence for negated clauses unless independent
typed correction evidence is present. The corrected report retains the four
assertion defer-and-release outcomes and the correction receipt; the refusal
case returns to non-authoritative `repair` rather than a false authoritative
disposition. Aggregate authoritative coverage is **54/74** (not v21's
false-positive-inflated 56/74); grounding remains F1 **0.507**, and Phase 4
tuples/promotions remain zero. The full language-neutral arbitration and Phase
8 runner suites pass **52/52** against this final code, including the negation,
offer, refusal, learning, and social evidence controls. Comparative, production,
resource, and wider cognition gates remain open.

### 2026-09-26 — Pending retrieval is not yet a holding disposition

Resumed the retrieval-latency seam and traced `_answer_topic_reply()` through
turn release and `_dispatch_pending_io()`. The graph already records an
answer-topic goal as `outcome=pending` while its matching SearchRequest is
requested/running/candidates-ready. In daemon mode, synchronous dispatch is
intentionally skipped and the graph-selected request is left to the host
worker. In the ordinary synchronous path, the turn still waits for retrieval.
There is no graph-authored pending/holding disposition or two-stage reply
contract in the topic route; `floor_holding_reply()` is only a wording helper
and cannot itself authorize that behavior. Therefore no floor-holding surface
was added: doing so would introduce a conversation policy not selected by the
graph and could interfere with the existing grounded-answer/error release
contract.

Focused retrieval ownership controls pass **3/3**:
`test_daemon_search_io_is_pending_until_graph_owner_commits`,
`test_topic_search_seed_mints_request_from_answer_topic`, and
`test_answer_goal_fulfills_only_its_own_retrieval_request`. A broader run of
the topic-grounding, route-selfheal, and Phase 7 envelope modules was stopped
after 504.6 seconds at **41 passed, 1 skipped** while still executing; it did
not reach a suite summary and is not counted as a pass. To lower synchronous
latency without weakening evidence, the next bounded design increment needs a
native disposition for pending retrieval plus an explicit transport/turn
contract for later completion; it is not a surface-text optimization.

### 2026-09-26 — Graph-selected frontier question repair release

The v22 trace for `question_unknown` (`Who is quorplezap?`) had native
`repair` authority with `dispatch_path=frontier`, but the surface remained the
generic diagnostic. The existing question ask-back predicate only admits an
untyped *head*; this event's typed `Who is` construction leaves `quorplezap` as
the untyped by-position gap after the copula. The synchronous conversation
bridge now renders a repair only when both the graph selected
`cognitive_disposition=repair` and the language adapter preserved
`dispatch_path=frontier`, using the existing ask-back faculty and
`conversation_action_graph` production gate. No new surface heuristic or
authority was introduced.

The explicit-uncertainty and language-neutral arbitration suites pass **35/35**;
additional existing clarification controls for `Move it now.` and
`Quorplezap the door.` pass **2/2**. The current corpus replay
`evaluation/reports/phase8_corpus_report_20260926_frontier_repair_v23.json`
releases the quoted-term clarification with a same-event repair receipt;
receipt-backed releases increase **35 → 36**. Native disposition authority
remains **54/74** and grounding is unchanged (precision **1.00**, recall
**0.34**, F1 **0.507**), so no cognition-score gain is claimed. The comparative
gate remains blocked. A neighboring action-receipt test for
`Please open the north gate.` initially failed under an empty-seed adapter.
Replaying the same input with the full graph seed set produced the event-bound
instruction Goal and released receipt; the integration test now loads the
graph it exercises. The full Phase 6A production-gate module passes **13/13**.
This was a test-fixture mismatch, not a failed action bridge, and does not claim
a new action-cognition score.

The first replay of the anaphoric-question bridge exposed that the generic
unknown-term template quoted `place`, the wh-relation focus, rather than the
unresolved entity. The repair renderer now distinguishes an unresolved
question reference from an unknown lexical item and uses a register-selected
`inquire_reference` surface based on the adapter's selected topic concept. The
result for `info_reference` is “Might I ask which valve you are referring to?”
with the same event-bound repair receipt. Focused frontier, anaphoric-reference,
and explicit-failure controls pass **5/5**. Full replay
`evaluation/reports/phase8_corpus_report_20260926_repair_releases_v25.json`
confirms **37** receipt-backed releases (35 at v22), including both repair
cases; authority remains **54/74**, grounding remains precision **1.00**,
recall **0.34**, F1 **0.507**, and the comparative gate remains blocked.
After the reference-specific template change, the complete
`test_phase6_explicit_uncertainty.py` module passes **12/12**.

The action-target follow-through addresses `Please open the north gate.`: the
Wikt-derived POS pass can mark `gate` as a verb after the noun modifier, so
action evidence previously selected `north` as the object. The adapter now
selects the rightmost clause-local content head after the chosen action, while
respecting clause/action/sequence boundaries and preserving pronoun targets.
Focused action-target/anaphora/compound controls pass **6/6**; the combined
action-evidence and Phase 6A production-gate modules pass **43/43**. Fresh full
replay `evaluation/reports/phase8_corpus_report_20260926_argument_head_v26.json`
now records `object=gate` on the same-event instruction Goal and releases its
action receipt. The corpus has 37 receipt-backed releases and authority
54/74; current grounding is precision **1.00**, recall **0.28**, F1 **0.438**.
The release gate remains blocked. This is a corrected action argument, not an
overall cognition or comparative-capability gain. Relative to v25, grounding
changed from 17 to 14 true positives (recall **0.34 → 0.28**, F1 **0.507 →
0.438**) with the same 24 true negatives and zero false positives. The changed
grounding classifications include `direct_action`, `action_close`, and
`correction_route`; investigate this replay delta before treating the argument
head adjustment as a net corpus improvement.

### 2026-09-26 — Revalidated pending-grounding turn contract

Rechecking the live implementation exposed that the preceding retrieval note
was too broad: daemon ingress already has a two-stage graph-owned answer
contract. It keeps the inbound turn in `pending_turns` while no graph reply is
available, exposes pending status through the transport, and after the host
worker commits retrieval evidence, the cognition tick releases the selected
answer against that same inbound event. The focused end-to-end regression
`test_daemon_completes_seed_generated_grounding_before_reply_release` passes
**1/1**. Combined retrieval, fetch-dispatch, and conversation-loop suites pass
**51 passed, 1 skipped** in 391.88 seconds. This does not prove the full suite
or performance acceptance.

The still-open retrieval-latency path is direct synchronous
`WorldAdapter.converse()`: `_answer_topic_reply()` can invoke local phrase
grounding and `_dispatch_pending_io(mid)` in-line. Preserve daemon behavior;
next investigate whether synchronous callers can use the same graph-selected
request/commit lifecycle without losing the immediate-reply contract. Do not
add a holding surface absent native authority, and measure fast/manifold
latency gates on the production path separately.

The action argument was then refined to preserve modifiers: adapter evidence
now reports `action_target="north gate"` and `action_target_head="gate"`, so
the event-bound Goal retains the whole noun phrase rather than dropping
`north`. The full action-evidence and Phase 6A suites pass **43/43**. Replay
`evaluation/reports/phase8_corpus_report_20260926_argument_phrase_v27.json`
remains at authority **54/74**, 37 receipt-backed releases, and grounding F1
**0.438** (14 TP, 36 FN, 24 TN, 0 FP). Both action cases are still unresolved:
the graph contains substantive referents for `north`/`south`, but not for
`gate` or either full compound. This supports the concern that the old
candidate-grounded outcome used the modifier as the object; it does not yet
adjudicate whether the corpus's expected `grounded` labels or cognition's
compositional grounding path should change. Controlled context replay confirms
`correction_route` is the same failure mode, not a separate history effect:
v25 parsed “Actually, use the east path” as `do:use(east)` and cited the `east`
Concept; v27 parses `do:use(east path)`, whose head `path` has no substantive
graph referent. The preceding `direct_action` alone does not change that
result. A focused regression for `east path` / head `path` passes **1/1**.
The corpus currently labels these events grounded and declares `graph_path`,
but Phase 2 explicitly classifies those declarations as unverified absent a
runtime evidence path. Keep those labels unchanged pending independent
annotation; do not trade semantic correctness for the previous score.

### 2026-09-26 — Missing-world disposition preserves the communicative goal

The expanded Phase 1 adjudication replay had regressed on “Tell me what you
see.” The language adapter correctly supplied neutral
`information_request/answer_or_learn` evidence, but the generic native
missing-world rule replaced its cognitive goal with `blocked` and left the
communicative force unset. The native arbitration seed now handles typed
missing-world information requests explicitly: it preserves
`request_information/answer_or_learn` while keeping the disposition `blocked`
because no perceptual scene is attached. The generic missing-world rule no
longer overwrites an already selected force's cognitive goal. A second
language-neutral test supplies the same evidence without English syntax or
lexical features; an unresolved spatial request retains its own
`repair_or_defer/clarify_or_defer` goal while remaining blocked.

The expanded 20-event Phase 1 adjudication now passes **4/4 tests**, and the
combined Phase 1, language-neutral arbitration, and explicit-uncertainty suites
pass **41/41**. The Phase 6A production-gate plus action-evidence suites pass
**49/49**. Fresh 74-event replay
`evaluation/reports/phase8_corpus_report_20260926_blocked_goal_preservation_v31.json`
completes without errors; aggregate metrics are unchanged from v30
(54/74 authoritative dispositions, grounding 14/50 TP, precision 1.00, recall
0.28, F1 0.438, zero false positives, and zero complete Phase 4 tuples).
This targeted force/goal correction is absent from the fixed Phase 0 corpus,
so it is not a corpus-score gain. Comparative release, grounding recall,
retrieval latency, full-boot resources, and production parity remain open.

### 2026-09-26 — Focus imperative parity case rechecked

The legacy “Focus on the reading work.” mismatch is not explained by a native
kind-rule failure alone. The frozen parity record supplies first-token POS
`noun` and expects a statement; the current English adapter supplies a verb
reading from the imperative construction, and native arbitration records
`request_action/act_or_clarify` with disposition `act`. A live turn still emits
the canonical explicit error surface, so this does not demonstrate successful
action production and must not be reported as a production win. The independent
Phase 1 adjudication fixture does not yet cover this exact sentence. Keep the
legacy capture unchanged; adjudicate the force and separately investigate why
the graph-selected action has no releasable production before changing the
parity contract. The full legacy speech-parity suite remains **4 passed, 2
failed**; its two failures are still open evidence, not waived.

### 2026-09-26 — Focus attention route now reaches native production

The production follow-through exposed the missing integration datum: the
existing `conversation_action` faculty classifies `focus` as a concern-framing
verb, and the graph-native `conversation_self_concern` rules already file and
release confident self-concerns, but that seed's route-Concept inventory did
not contain `focus`. Added `Concept{name:"focus",
instruction_route:"self_improvement"}` to
`seeds/conversation_self_concern.json` (v2.2.1). The existing rules now bind
the parsed predicate and grounded content, mint a same-event
`Goal{kind:self_improvement}` plus `SelfConcern{status:noted}`, and author the
response. The production boundary releases that exact response with a
`conversation_instruction_graph` receipt. No Python phrase ladder or automatic
promotion was added; human approval remains required before self-modification.

The new end-to-end regression and the no-auto-promotion control pass; the full
self-concern lifecycle module passes **7/7**. The Phase 6A/action plus
self-concern/instruction focused batch reported **36 passed, 5 failed**; all
five failures are in `test_instruction_gap_migrated.py` (covered read/run/fix
and taught-verb handling plus ungrounded concern accounting), and that module
alone reproduces the same **5 failures, 3 passes**. This is a current separate
instruction-bookkeeping issue, not counted as a pass or attributed to the new
`focus` node.

The full legacy speech-parity suite remains **4 passed, 2 failed**: its frozen
partial-comprehension capture still expects “Focus on the reading work.” to be
a statement, whereas a full live turn now produces a graph-selected,
human-gated concern response. Keep the historical capture unchanged pending
case-level adjudication. Fresh full replay
`evaluation/reports/phase8_corpus_report_20260926_focus_route_v32.json`
completes all 74 events without error; aggregate scores are unchanged
(54/74 authoritative dispositions; grounding F1 0.438; zero complete Phase 4
tuples/promotions), since this utterance is not in Phase 0. This closes one
focused instruction production path only; corpus production parity, grounding,
resource, Phase 4, and comparative gates remain open.

### 2026-09-26 — Unknown focus target now clarifies

A negative live probe found that “Focus on the blorfnax.” was being filed as a
concern because the graph confidence rule treated resolved function words
(`on`, `the`) as grounded content. Updated both mutually exclusive
self-concern rules to exclude common function words as well as pronouns and
the instruction predicate, and advanced the seed manifest to v2.2.2. The
confidence decision remains graph-native; no parser-side target heuristic was
added. The control “Focus on the reading work.” still files the grounded
`reading` concern, while the unknown-target probe now selects `clarify` and
mints neither a conversation SelfConcern nor Goal. Focused controls passed
**3/3**, then the complete self-concern lifecycle suite passed **8/8** after
the rule refinement. JSON parse and `git diff --check` also pass. The full
Phase 8 replay has not yet been rerun; the existing v32 corpus does not contain
this focus wording, so no score change is expected. Other previously recorded
instruction-gap failures and legacy parity divergences remain open.

### 2026-09-26 — Terminal instruction paths record their outcome

Revalidated the instruction-gap module against the current checkout; its five
failures were still reproducible. Covered read, graph instruction, and action
production paths returned before the shared mechanical
`instruction_outcome=handled` readback. Added the same readback and native
fixpoint pass before those terminal releases. The ungrounded self-improvement
test also counted 11 lazily-created boot-integrity concerns as request
concerns; narrowed that assertion to exclude only `kind=boot_integrity`, while
still checking that the turn files no request/gap concern. The full
`tests/test_instruction_gap_migrated.py` module now passes **8/8**. This closes
that focused bookkeeping regression only; Phase 1 parity, corpus/resource,
Phase 4, and comparative-human acceptance remain open.

The follow-up avoids an unnecessary full fixpoint pass on already-handled
turns; only `instruction_outcome=unhandled` triggers the extra graph pass that
lets the gap rule consume the datum. The instruction-gap suite remains **8/8**
after this refinement. A full signal-only Phase 8 replay
[`phase8_corpus_report_20260926_instruction_terminal_readback_v34.json`](../../../evaluation/reports/phase8_corpus_report_20260926_instruction_terminal_readback_v34.json)
completed **74/74** events with no errors. Its event observations are identical
to the immediately preceding v33 run, with the same 45 recorded production
receipts, authority **54/74**, and grounding F1 **0.438** (14/50 TP, precision
1.00, recall 0.28); no corpus improvement is claimed. Total replay time fell
from 238.5 s in v33 to 162.1 s after limiting the extra pass, but maximum
per-event latency remains 4.44 s, so the 150 ms latency gate is still far
from satisfied. The fixed Phase 0 corpus still contains no memory or learning
probe; Phase 4 complete tuples/promotions remain zero and comparative
references remain unavailable.

The same replay's terminal release breakdown is **41 released, 27 explicit
errors, and 6 unavailable/non-turn outcomes**. The slowest event is
`standalone_assertion` at 4.44 s; `info_unknown` is next at 2.86 s. Thus the
instruction-readback regression is repaired without a structural corpus delta,
but this does not improve the larger release or latency envelope. Next
investigation remains event-family attribution of those synchronous costs and
unreleased outcomes, retaining the explicit diagnostic surface and native
disposition authority.

### 2026-09-26 — Remove repeated all-node seed scans from the turn path

A warm-turn profile isolated repeated `load_seeds_into()` checks as a dominant
cost: each check enumerated every graph node twice (about **1.39 s** on the
representative profiled turn). `installed_seeds()` and the `SeedSummary`
presence check now use the native typed-node index, preserving exactly the
same graph-resident installed-seed authority while avoiding unrelated
conversation nodes. `tests/test_seeds_migrated.py` passes **13/13**. A following
profile found the adapter's native facade was also constructing/decorating a
fresh serialized closure on every graph call; `_AdapterNativeFacade` now caches
the per-method closure while retaining the per-call `RLock`. The seed-loader
plus conversation-loop regression battery passes **26/26**.

Fresh full replay
[`phase8_corpus_report_20260926_seed_lookup_facade_cache_v35.json`](../../../evaluation/reports/phase8_corpus_report_20260926_seed_lookup_facade_cache_v35.json)
completed **74/74** events with no errors. Against v34, all 74 semantic/release
observations, all **45** production receipts, authority **54/74**, and
grounding F1 **0.438** are unchanged. Total runner time fell from **162.1 s**
to **32.3 s** (about 80%); maximum event time fell from **4.44 s** to **2.77 s**.
The 2.77 s cold first event includes first-turn conceptualizer rule authorship;
the next slow events are about 0.5–0.6 s. This is a substantial measured
resource improvement, but still misses the plan's **<150 ms** turn envelope,
and the release breakdown remains 41 released / 27 explicit errors / 6
unavailable. Continue profiling cold setup separately from warm-turn native
graph cost; do not prewarm it invisibly or treat total replay speedup as gate
closure.

### 2026-09-26 — Index event-grounding referent checks

The warm profile still showed repeated graph referent reads during
`CommunicationInterpretation` evidence construction. `_graph_concept_referent_path`
now uses the native `(Concept, name)` index rather than walking the complete
Concept set; the referent still counts only when its graph-held Concept has a
definition/description/why field. The combined Phase 2 grounding/reference,
topic-grounding, and seed-loader battery reported **71 passed, 1 skipped, 1
failed**. The single failure is the network-dependent
`test_topic_search_seed_mints_request_from_answer_topic`: its request status
was `failed` due `URLError: [Errno -2] Name or service not known`. This is an
external retrieval/DNS failure, not an indexed-referent assertion; retain it as
an environment-limited failure, not a pass.

Fresh full replay
[`phase8_corpus_report_20260926_indexed_referent_lookup_v36.json`](../../../evaluation/reports/phase8_corpus_report_20260926_indexed_referent_lookup_v36.json)
completed **74/74** without errors. Compared with v35, all event outputs and
release receipts are structurally identical; authority remains **54/74**,
grounding F1 **0.438**, release counts **41/27/6** (released/error/unavailable),
and Phase 4 complete tuples/promotions **0/0**. Runner time was 30.6 s and
maximum event time 2.79 s, so this index change preserves results but does not
close the latency target. Continue with cold-start conceptualizer setup and
warm-turn graph-call profiling; the overall cognition, production, resource,
and comparative gates remain open.

### 2026-09-26 — Selective native rule readback for cold conceptualizer setup

The remaining cold-turn profile attributed roughly **2.3 s** to
`_compose_conceptualize_rule` serializing every live rule just to test five
generated rule families for idempotency. It now uses the existing native
`export_rules_prefix` readback for those five name prefixes, with the previous
full export retained only as a compatibility fallback. The conceptualizer,
monitor, conceptualized-converse, and deliberative-production suites report
**28 passed, 1 failed**. The one failing Borogove rich-answer control was
reproduced as a `SearchRequest` failing with
`URLError: [Errno -2] Name or service not known`; no HeldAnswer is created, so
the failure is external retrieval unavailability rather than rule-readback
parity. This control remains unverified in an online environment.

Fresh full replay
[`phase8_corpus_report_20260926_selective_conceptualizer_rules_v37.json`](../../../evaluation/reports/phase8_corpus_report_20260926_selective_conceptualizer_rules_v37.json)
completed **74/74** without errors. Compared with v36, all event outputs and
45 receipts are identical; authority remains **54/74**, grounding F1 **0.438**,
and release counts remain **41 released / 27 explicit errors / 6 unavailable**.
Total replay is 28.1 s; median event 399.5 ms and maximum 533.3 ms, down from
the 2.79 s cold maximum in v36. A separate same-context timing probe measured
the first three events at **238 / 295 / 150 ms**. This reduces cold setup
without changing semantics, but the median and maximum still miss the
execution plan's <150 ms target. Warm-turn graph cost and the slow first
event remain active profiling work; all broad cognition, production,
resource, and comparative gates remain open.

### 2026-09-26 — Bound conceptualizer passes by pending work

`run_pipeline()` now exits its bounded tick/shape/monitor loop when both
mechanical pending-request scans return empty, while always retaining the final
native rule pass that consumes any last monitor verdict. The receipt records
both the configured round bound and rounds actually executed. This is a
worklist-exhaustion optimization only: graph-authored rules continue to decide
commit versus revise, and the Python guard cannot inspect utterance content or
select a production outcome. The two conceptualizer source audits were
narrowed to allow this exact guard and continue rejecting every other
unapproved conditional. Focused conceptualizer, monitoring, conversation, and
deliberative-production tests pass **28/28**; the network-dependent rich-prose
retrieval regression remains deselected and unverified offline.

Fresh replay
[`phase8_corpus_report_20260926_bounded_conceptualizer_fixpoint_v39.json`](../../../evaluation/reports/phase8_corpus_report_20260926_bounded_conceptualizer_fixpoint_v39.json)
completed **74/74** events. Compared with v38, replies, observed dispositions,
grounding labels, release states/receipts, and Phase 4 tuple/promotion counts
are unchanged. Authority remains **54/74**, grounding F1 **0.438** (14/50 TP,
precision 1.00, recall 0.28), and Phase 4 complete tuples/promotions remain
**0/0**. Total replay time was **27.65 s** versus 28.02 s in v38. Precisely
measured synchronous `WorldAdapter.converse()` latency is median **206.6 ms**,
p95 **286.6 ms**, max **321.5 ms**, with **53/74** over 150 ms (v38: median
202.6 ms, p95 300.6 ms, max 325.7 ms, 54/74 over 150 ms). These single-run
changes are mixed and do not establish a meaningful latency improvement; the
<150 ms gate remains open. Broad cognition, production, resource, and
comparative gates also remain open.

### 2026-09-26 — Canonical bounded-gate recheck after resume

Re-ran the independent Phase 1 adjudication, grammar inversion, output-null,
deliberative-production, and Phase 6A receipt-gate suites on the current tree:
**24 passed**. This re-establishes those fixture-scoped contracts after the
recent runtime edits; it does not close the broader phases. In particular,
Phase 1 parser parity still has independently recorded mismatches, Phase 8 v39
remains at 54/74 authoritative dispositions and 14/50 grounding true positives,
Phase 4 remains at zero complete evidence tuples/promotions, and the
synchronous turn-latency envelope remains above 150 ms.

The strict language-agnostic evidence boundary was separately rechecked with
`tests/test_language_neutral_evidence_arbitration.py`,
`tests/test_phase0_evaluation_contract.py`, and the independent 20-event Phase
1 adjudication fixture: **37 passed**. The earlier frozen speech-act parity
run remains **4 passed / 2 failed**; its eight case-level differences include
typed action-target changes and evidence-gated image routing, so they remain
adjudication debt rather than a reason to rewrite the capture or weaken graph
authority.

The connected-content closure, named-profile closure/no-curriculum-import, and
daemon retrieval pending-to-release integration controls also pass **3/3** on
this current tree. These confirm the existing pre-pass and asynchronous
completion contract; they do not meet the synchronous latency threshold or
establish comparative capability.

The connected seed-selection path already resolves and validates declared
dependency plus typed-content closure before graph mutation and reuses its
cached seed index/map; the selected-closure equivalence tests are the existing
verification for that requested pre-pass shape. I did not add a second seed
planner. Topic retrieval likewise already has an asynchronous two-stage daemon
contract, covered by the pending-to-release integration test; changing the
synchronous `converse()` return contract would be a separate public API change,
not a safe latency-only patch. Continue cognition work against the remaining
case-adjudicated Phase 1/2 gaps and preserve the explicit retrieval-pending
boundary until such a transport change is specified and evaluated.

### 2026-09-26 — `info_choice` production failure attribution

Inspected the v39 `info_choice` graph trace by replaying the fixed corpus
through that event. The event is a turn-compatible “Should we use the north
route?” input. Native response-adjacency rules create answer-force graph
messages linked to the inbound, but those messages contain no text. The
existing response release requires an event-linked answer commitment and an
exact-bound, non-empty graph surface; the production gate therefore withholds
the diagnostic error rather than releasing the empty response shells. No
supported graph answer surface or Phase 4 tuple is present for this event.
This is an upstream answer-content/evidence generation gap, not a defect in
the release gate. Do not remove the surface-bound release check or count the
corpus's `graph_path` label alone as answer evidence. The next valid increment
must connect a supported path/decision faculty to a graph-authored response
surface, or adjudicate the event with independent evidence before changing its
label. The overall production/cognition gate remains open.
The focused `tests/test_phase6_question_response_production_bridge.py` suite
passes **4/4**, including negative controls for missing graph commitments,
surface mismatch, and non-turn questions; this validates the fail-closed
boundary but does not supply the missing upstream answer content.

### 2026-09-26 — Require graph-bound answer content for state authority

The Phase 8 evidence projection previously counted every event-linked answer
speech-act Message as disposition-grade authority, even when the graph Message
was an empty structural shell and the returned text was only an adapter
diagnostic. `reply_turn_trace()` now retains that commitment but records
`surface_bound` only when its non-empty graph text exactly matches the returned
surface; `_state_evidence_metadata()` accepts linked-message authority only
with that binding. Event-bound supported topic answers retain their separate
evidence-chain rule. Regression coverage includes empty/unbound and exact-bound
messages. The Phase 8 runner and question-response production bridge suites
pass **32/32**.

Full replay
[`phase8_corpus_report_20260926_surface_bound_answer_authority_v40.json`](../../../evaluation/reports/phase8_corpus_report_20260926_surface_bound_answer_authority_v40.json)
completed **74/74** events. It preserves outputs, grounding counts (**14/50**
grounded/partially-grounded true positives; F1 **0.438**), and production
release behavior. The projection now treats an error diagnostic as `error`
when no higher-priority native disposition, graph repair, or graph action
route establishes state; an unresolved question remains `repair` despite a
failed release. Thus `info_choice` is observed as `error` (expected `answer`)
and its empty graph shell is explicitly
`interpretation_readback_not_disposition`. Authority coverage drops from
**54/74** in v39 to **52/74** because two empty/unbound answer shells no longer
count; label matches without authority are **7/74** after the corrected
error-state projection. Grounding remains **14/50** true positives, F1
**0.438**, and release counts remain **41 released / 27 errors / 6
unavailable**. This makes the unmet answer-content case visible rather than
crediting a diagnostic surface or empty shell. The 150 ms synchronous
latency, grounding, Phase 4 complete-tuple, production/cognition, resource,
and comparative gates remain open.

The same v40 report's measured synchronous turn latency is median **208.0 ms**,
p95 **271.0 ms**, max **339.3 ms**, with **52/74** turns over 150 ms. Against
v39 (206.6/286.6/321.5 ms; 53/74 over), the distribution shift is mixed and
does not close the latency gate.

An additional integration regression in `tests/test_conversation_loop.py`
pins the ordinary question-response path's current state: it retains the
event-linked answer-force Message, but its adapter-realized text does not make
the graph shell surface-bound. The question-response bridge, Phase 8 authority
projection, and this trace assertion pass **6/6** focused tests. This closes a
trace-contract gap only; it supplies no new graph-authored answer content.

### 2026-09-26 — Index live Concept lookups on the substrate

Phase 7 turn profiling showed repeated whole-graph Concept-name scans as a
significant synchronous cost. `WorldAdapter._concept_by_name()` now declares
and reads the native maintained `(Concept, name)` attribute index, preserving
first-NodeID duplicate resolution and immediately reflecting later graph
insertions, attribute changes, and deletions. The same native attribute-index
path now serves the existing graph-held write-request cue reader, avoiding a
separate all-Concept scan per turn; its closed fallback and learned cue
behavior remain covered. These indexes accelerate graph queries only and do
not select cognition or production outcomes.

The conversation loop, Phase 8 runner, and question-response bridge pass
**46/46**; code growth, code-writing, and emitter-demand controls pass
**209/209**. Full replay
[`phase8_corpus_report_20260926_indexed_write_cues_v44.json`](../../../evaluation/reports/phase8_corpus_report_20260926_indexed_write_cues_v44.json)
completes **74/74**. Compared with v40, all replies, observed states,
authority labels, grounding results, and release states are unchanged.
Authority remains **52/74**, grounding is **14/50** true positives with F1
**0.438**, and release counts remain **41 released / 27 errors / 6
unavailable**. This synchronous timing sample improves median **208.0 →
153.9 ms**, p95 **271.0 → 241.4 ms**, maximum **339.3 → 254.9 ms**, and turns
over 150 ms **52 → 41**. It is meaningful movement but still misses the
execution plan's maximum-turn bound; no resource RSS reprofile was included,
so the full Phase 7 resource gate remains open along with cognition, Phase 4,
production, and comparative gates.

### 2026-09-26 — Reuse manifold vectors and remeasure the connected profile

The maximum-latency `information_question` profile attributed much of its
audience-adaptation cost to recomputing identical TF-IDF vectors for the same
region anchors. `domains/concept_graph.py::_vec()` now memoizes vectors inside
the already graph-derived model snapshot; model replacement on its existing
microtheory-count invalidation drops the cache with it. This changes no
similarity arithmetic or graph decision. Audience-adaptation and concept
dimension suites pass **28/28**. Full Phase 8 replay
[`phase8_corpus_report_20260926_cached_manifold_vectors_v45.json`](../../../evaluation/reports/phase8_corpus_report_20260926_cached_manifold_vectors_v45.json)
preserves all v44 replies, states, authority labels, grounding results, and
release states. Its latency sample is mixed: median **149.0 ms**, p95
**251.3 ms**, maximum **267.7 ms**, and **34/74** turns over 150 ms, versus
153.9/241.4/254.9 ms and 41/74 for v44. This improves median/coverage but
does not establish the Phase 8 maximum-turn bound.

The fresh connected-profile Phase 7 replay
[`phase7_profile_resource_20260926_conversation_native_indexes_v45.json`](../../../evaluation/reports/phase7_profile_resource_20260926_conversation_native_indexes_v45.json)
selected a complete closure for all 74 events, resolved every declared
dependency/content key, reproduced a deterministic replay with zero errors,
and measured **96,296,960-byte** peak RSS, **69,775,360-byte** conversation
RSS growth, and **136.0 ms** maximum conversation latency. Its connected-profile
absolute/growth RSS and 150 ms latency bounds pass. This does not substitute
for full-boot/profile-equivalence evidence: the canonical Phase 8 full-seed
replay still has 34 events over 150 ms and a 267.7 ms maximum. Full-boot
resource reduction, broad full-vs-connected event-family parity, and the
cognition, production, Phase 4, and comparative gates remain open.

### 2026-09-26 — Source-current isolated `question_ack` adjudication probe

The older 2026-09-25 note that an isolated `question_ack` had matching held
topic evidence is not reproducible against the current working tree. A fresh
one-event Phase 8 run is preserved at
[`phase8_question_ack_isolated_current_20260926.json`](../../../evaluation/reports/phase8_question_ack_isolated_current_20260926.json).
It reads the frozen fixture expectation `answer`, but the current graph readback
selects authoritative `repair`, records `grounding_status=unresolved`, and
releases the graph-linked clarification `I don't know 'route' — what does it
mean?` with no execution error. This confirms that the v45 full-corpus result
is not merely a prior-turn contamination effect. It does not independently
settle whether the frozen answer label is valid: the corpus tags the event as
standalone while asserting groundedness, so Phase 8I still needs blind
case-level adjudication rather than a code change or label rewrite. The probe
used runner SHA-256 `11edc2eedc9240280abc068a0816d016a88f12fe6405340535bb4e5822e98fca`,
adapter SHA-256 `3c07356467ebed6e29fec14778348fe7956abff0a21bdfe02f27e5f046b90c58`,
comprehension SHA-256 `de5576995cb74b17b23507fc936019e09f1917c7518693624694c5ce3f00f48c`,
and fixture SHA-256 `72bf847cb2066ff1a0c679d3412d601100da30b6dd81e4a3b0e547c47f4406c3`.

### 2026-09-26 — Question-ingress backfill latency shadow

The full-vocabulary `knows_concept` materialization at question ingress was
tested as a potential shared turn-cost reduction. In an in-memory shadow only,
question ingress used the existing indexed, message-relevant candidate
materialization; the later full backfill for an already selected meta faculty
was preserved. The 74-event report
[`phase8_corpus_report_20260926_question_candidate_backfill_shadow.json`](../../../evaluation/reports/phase8_corpus_report_20260926_question_candidate_backfill_shadow.json)
has **zero observation-field differences** against v45 outside the two timing
fields: authority remains **52/74** with **51/52** authoritative state matches,
grounding remains **14/50** (F1 **0.438**), and outcomes remain **41 released / 27
errors / 6 unavailable**. The timing sample is mixed and does not justify a
code change: median **161.0 ms** and p95 **240.4 ms**, versus v45's
**149.0/251.3 ms**. Because the paired semantics are unchanged and the median
does not improve, the full-vocabulary ingress path is retained pending a
better-attributed performance experiment. The full-seed latency gate remains
open; this shadow is not a resource/RSS measurement.

### 2026-09-26 — Native neutral receipt for typed response acknowledgement

The corpus event `acknowledgement` had a native `defer` / `update_common_ground`
interpretation but no outbound graph message, so both transports emitted the
diagnostic error. Added a held graph rule in
[`communication_standalone_assertion_reply.json`](../../../seeds/communication_standalone_assertion_reply.json)
that mints exactly one neutral acknowledgment only when the interpretation
has `evidence_force=acknowledgement`, response-compatible interaction metadata,
the native `typed_acknowledgement` arbitration basis, and the selected
`defer`/`update_common_ground` state. The synchronous and daemon bridges release
that same graph message through the existing social production gate with
semantic intent `acknowledge_receipt_without_endorsement`; no proposition is
accepted, and generic social acts, refusals, and standalone assertions do not
match this new rule. Reply-expectation readback now recognizes the typed
graph-selected response plan as an expected acknowledgment rather than a
no-response terminal.

The new synchronous, async daemon, and prior standalone receipt controls pass
**5/5** focused regressions; the full language-neutral arbitration and daemon
ingress suites pass **33/33**. The fresh full Phase 8 replay
[`phase8_corpus_report_20260926_typed_acknowledgement_receipt_v2.json`](../../../evaluation/reports/phase8_corpus_report_20260926_typed_acknowledgement_receipt_v2.json)
completes **74/74** events. High-level semantic comparison against v45 changes
only this event's reply/release: authoritative `defer` remains unchanged,
while outcomes improve from **41 released / 27 errors / 6 unavailable** to
**42 / 26 / 6**. Overall authority remains **52/74**, state matches **51/52**,
grounding **14/50** (F1 **0.438**), and Phase 4 complete tuples/promotions
**0/0**.

The fresh connected-profile report
[`phase7_profile_resource_20260926_typed_acknowledgement_receipt_v2.json`](../../../evaluation/reports/phase7_profile_resource_20260926_typed_acknowledgement_receipt_v2.json)
selects a complete dependency/content closure, has zero errors and equal
deterministic replay, and measures **96,227,328-byte** conversation peak RSS
with **69,816,320-byte** boot/event growth. Its **152.45-ms** maximum turn
slightly exceeds the 150-ms target; an earlier paired run measured 144.15 ms,
so the connected timing bound is not stable. The canonical full-seed replay v2
measures **152.54-ms median, 233.20-ms p95, and 285.33-ms max**; v1 measured
147.63/230.52/249.86 ms. This variance reinforces that the 150-ms connected
turn bound is not stable and full-seed latency remains over target. This closes
only the typed-ack receipt slice, not broad async parity or the Phase 7/8
release gates.

The source-current signal-only daemon ingress replay is also preserved at
[`phase7_daemon_ingress_20260926_typed_acknowledgement_receipt_v3.json`](../../../evaluation/reports/phase7_daemon_ingress_20260926_typed_acknowledgement_receipt_v3.json).
It processes all **74/74** events with zero errors and a complete seed closure;
the typed acknowledgement has native authority and a released graph-selected
receipt. Across the corpus it records **43** disposition authorities, **28**
released replies, **73** completed turns, **19.90-ms** max ingress, **31.58-ms**
max native cycle, and **97,595,392-byte** peak RSS. One turn (`info_unknown`)
remains expected/pending and one teacher host action remains requested because
this signal-only pass deliberately does not execute host retrieval; therefore
these figures verify daemon ingress and receipt selection, not full-turn async
completion. External I/O was not performed, and determinism was not verified in
this pass. The existing completion-mode reports remain the separate evidence
for retrieval-backed async turns.

### 2026-09-26 — Current target replay under comparative v5 input profile

Regenerated the fixed 74-event target report against the current worktree using
the same bounded event-context/history-8 protocol used by the repeated CPU LLM
raw runs:
[`phase8_corpus_report_20260926_typed_acknowledgement_receipt_v3_event_context_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260926_typed_acknowledgement_receipt_v3_event_context_v5.json).
The report binds the canonical fixture hash and labels memory/learning as not
comparable. It records **52/74** authoritative dispositions, **14/50** grounding
true positives (precision **1.0**, recall **0.28**, F1 **0.438**), zero complete
Phase 4 tuples/promotions, and **43/74** synchronous turns over 150 ms (median
**160.26 ms**, p95 **251.26 ms**, max **272.34 ms**). The typed
`acknowledgement` event now has native `defer` authority and releases the
neutral receipt. The release gate remains **blocked**: the report correctly
does not attach unadjudicated raw LLM responses as capability scores; all five
reference classes remain unavailable in its comparison matrix, with human
annotations, matched ELIZA v5 inputs, and blinded adjudication still missing.
This supplies current target-side input-profile evidence only; it closes no
cognition, production, resource, or comparative release gate.

### 2026-09-26 — `information_question` meta-reader authority ablation

The current `information_question` answer is produced by the adapter's
`_meta_reader_reply` over graph-held self-organisation state, not by a native
answer disposition or a releasable graph response. A one-event v5 shadow
disabled only that reader (`WorldAdapter._meta_reader_reply = lambda self,
comp: None`) while preserving normal boot, signal, and turn handling. The
remaining graph path returned the explicit diagnostic error and recorded a
withheld `conversation_question_response_graph` receipt with reason
`diagnostic_error_surface_not_a_release`; disposition authority remained
absent. This falsifies removing the adapter as a safe parity fix. The proper
follow-up is to establish an explicit graph-owned self-report answer
commitment and production release, with its state source and semantic content
bound to the selected reflective faculty. Until that path exists, the adapter
answer remains behaviorally necessary but must not count as native cognition
authority or as a passed output-null gate. Reproduce with a fresh process by
loading `information_question` from the Phase 0 fixture, applying the
one-method shadow above, then calling
`evaluation.phase8_corpus_runner.run_system_under_test` on that single-event
corpus using protocol `phase8a-fixed-phase0-corpus-v5-event-context-history8`.

### 2026-09-26 — Native self-organisation answer commitment and gated release

Implemented the audited follow-up in the existing graph cognition path. The
language adapter now transports the selected reflective-faculty id and links a
`ReflectiveAnswerEvidence` record to the specific held `Microtheory` nodes
reported by the reader. A Rust-executed communication arbitration rule now
requires that typed information-request evidence, a turn-compatible event, the
selected `self_organisation` faculty, and at least one linked `Microtheory`
before it sets native `answer` disposition and mints exactly one
same-event answer `Message`. The host only renders that selected commitment;
the existing production gate checks the event and every reported area, then
binds the released receipt to that graph Message. Unsupported faculty evidence
fails closed. List-valued semantic roles now retain and check each item in
parse-back receipts rather than collapsing a list into one opaque string.

Focused verification: native typed-evidence and sync path **3/3**, daemon
release **1/1**, production-gate regressions **16/16**, and existing
self-organisation reader routing **2/2**. Full v5 target replay
[`phase8_corpus_report_20260926_native_reflective_self_report_v2_event_context_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260926_native_reflective_self_report_v2_event_context_v5.json)
changes only the audited authority gap: disposition authority rises **52→53**,
authoritative state matches **51→52**, and `information_question` is now a
native, correctly matching answer with a released
`conversation_reflective_self_organisation_graph` receipt. Grounding remains
14/50 (F1 **0.438**, recall **0.28**) and Phase 4 complete tuples/promotions
remain **0/0**. The comparative gate is still blocked. Full v5 timing in this
single paired replay is **166.3-ms median / 273.3-ms p95 / 340.0-ms max**,
versus **160.3 / 251.3 / 272.3 ms** in its preceding run; whole-corpus latency
therefore remains above target and these unpaired timings do not establish a
regression or a pass.

The fresh connected-profile resource replay
[`phase7_profile_resource_20260926_native_reflective_self_report_v1.json`](../../../evaluation/reports/phase7_profile_resource_20260926_native_reflective_self_report_v1.json)
selects a complete closure, reports zero errors, and verifies deterministic
replay. Peak conversation RSS is **96,321,536 bytes**, conversation growth
**69,767,168 bytes**, and maximum event latency **125.1 ms**; all reported
conversation RSS bounds pass. Resource measurements were not independent
processes. This closes the specific native self-report cognition/production
slice, not general reflective-faculty routing, full-seed latency, all-corpus
production, or the Phase 8 comparative gate.

### 2026-09-26 — Native authority for selected-concept grounded answers

Closed one follow-on event-authority gap found in the current corpus report:
the ordinary information-request path could select a concept and release its
graph-grounded HeldAnswer, but native arbitration only authorized the distinct
reflexive-frontier answer route. Added a Rust-executed rule for the ordinary
path. It requires the same interpreted Message to carry the selected concept,
a matching supported HeldAnswer, and explicit matching TopicGroundingEvidence;
the interpretation must carry typed information-request and candidate-grounded
evidence. Neither response text nor an unrelated held answer can satisfy the
rule. Seed version is now 1.3.0.

Focused native arbitration tests pass **3/3**, including the existing frontier
case, the selected-concept case, and a negative case without grounding evidence.
The seed parses as JSON and the scoped diff passes `git diff --check`. The
full-corpus replay is recorded at
[`phase8_corpus_report_20260926_selected_concept_answer_v1_event_context_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260926_selected_concept_answer_v1_event_context_v5.json).
The selected-concept `question_referent` is authoritative and matching, with its
graph-selected answer receipt released. Corpus authority rises **53→54/74**,
authoritative state matches **52→53**, and label matches lacking authority fall
**6→5**. Grounding remains 14/50 (F1 **0.438**, recall **0.28**), Phase 4 tuples
and promotions remain **0/0**, and the comparative gate remains blocked. This
confirms one event-specific gain; it does not close the wider cognition or
comparative release gates. Next work remains the five label-matching events
without authority, then the broader grounding and production gaps.

### 2026-09-26 — Typed continuation action authority without clause-form gate

The remaining `continuation_context` event already carried typed
`action_request` and `interaction_relation=continuation`, but native arbitration
also required `literal_form=imperative`. The current adapter reports the clause
form as declarative for “And then inspect the pump,” despite the typed semantic
force being an action request. Removed that redundant grammatical condition
from the continuation-action rule; the graph still requires the typed action
force, continuation relation, no deferred condition, and no unresolved
referent. Seed version is now 1.4.0. A language-neutral regression uses a
synthetic typed action event with declarative clause form and confirms that the
graph selects `act`.

Focused arbitration tests pass **4/4**. Full v5 replay
[`phase8_corpus_report_20260926_typed_continuing_action_v1_event_context_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260926_typed_continuing_action_v1_event_context_v5.json)
raises authoritative dispositions **54→55/74** and reduces label matches
without authority **5→4**. `continuation_context` is now authoritative and
matching; an event-by-event comparison confirms it is the only disposition,
authority, or match change from the preceding selected-concept replay.
Grounding remains 14/50 (F1 **0.438**, recall **0.28**); Phase 4 complete tuples
and promotions remain **0/0**; the comparative gate remains blocked. This
closes one cognition-authority seam only, not instruction execution, full
production parity, or the broader acceptance gates.

### 2026-09-26 — Independent 74-event profile resource measurements

Ran the full and connected Phase 7 profiles in separate fresh CLI processes
over the same 74 events, writing
[`phase7_profile_resource_20260926_independent_full74_full.json`](../../../evaluation/reports/phase7_profile_resource_20260926_independent_full74_full.json)
and
[`phase7_profile_resource_20260926_independent_full74_conversation.json`](../../../evaluation/reports/phase7_profile_resource_20260926_independent_full74_conversation.json).
Both report zero execution errors; the connected closure is complete and both
measurements identify themselves as independent fresh-process runs. The full
profile reaches **1,440,792,576-byte** conversation RSS peak and fails the
absolute/growth bounds. The connected profile peaks at **96,395,264 bytes**
with **69,836,800-byte** growth; its reported RSS bounds pass. It is not yet a
valid replacement: an identity/text-normalized event-observation comparison
of these independent outputs matches only **3/74** events. The existing
same-process profile comparator independently confirms **3/74** parity at
[`phase7_seed_profile_parity_20260926_independent_resource_followup_all74.json`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_independent_resource_followup_all74.json).
The independent-output comparison remains corroborating diagnostic evidence
only. The
resource gate therefore remains open until a connected pre-pass/profile
preserves full-profile behavior while meeting the bound. Full-profile maximum
event latency is **286.8 ms** (median **154.5 ms**, p95 **245.1 ms**); connected
maximum is **153.7 ms** (median **56.7 ms**, p95 **95.4 ms**).

### 2026-09-26 — Typed scoped-content pre-pass for connected profile

The 143-token global content-key sweep was not a valid profile: it selected
ambiguous providers, produced an incomplete closure (`llvm_passes` required the
absent `llvm_ir` dependency), and the loader correctly rejected the selection.
The next experiment uses exact typed references scoped to the lexical content
providers rather than broadcasting each key to every seed. The Phase 7
comparison API/CLI now transports `SEED_ID:TYPE:NAME` scoped references through
the existing boot index and records them in the schema-versioned (`v8`/parity
`v2`) reports. Candidate refs are generated mechanically by intersecting event
tokens with the cached seed index's declared `Concept` refs in
`learned_lexicon` and `colour_meaning`; no expected cognition labels are read.

For the fixed 74-event corpus this creates **82 typed refs** across those two
scopes, selects **74 seeds**, and validates a complete closure. The fresh
connected-only process report
[`phase7_profile_resource_20260926_scoped_lexicon_full74_conversation.json`](../../../evaluation/reports/phase7_profile_resource_20260926_scoped_lexicon_full74_conversation.json)
has zero errors, independent-process measurement, **96,673,792-byte** peak
conversation RSS, **70,094,848-byte** conversation growth, and **70,111,232-byte** boot-and-event growth; all its stated
RSS bounds pass. The paired structural report
[`phase7_seed_profile_parity_20260926_scoped_lexicon_full74.json`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_scoped_lexicon_full74.json)
matches **49/74** events (**25** residual mismatches), versus **3/74** for the
unscoped connected profile. Thus typed scoped content substantially improves
behavior at the measured memory bound, but is not yet full parity and has only
about **7.8 MiB** of headroom under the 100-MiB RSS ceiling. The latest
connected max event is **151.8 ms**, slightly above the 150-ms bound, on
`final_standalone`; the prior scoped replay was below it, so this turn limit is
not yet stable. This fixed-corpus candidate extractor is an evaluation
pre-pass, not a general multilingual semantic-reference producer. Full-boot
RSS and full-profile event latency remain over their bounds; the broader
resource gate remains open.

Added typed-scope replay/selection regressions and updated stale Phase 7
expectations to reflect current evidence: `north gate` is not grounded in
either profile, while the full profile does create a handled, released
event-bound instruction goal that the unscoped connected profile lacks. The
Phase 7 production-envelope module passes **14/14**. The comparison continues
to assert that parity remains incomplete rather than treating this as a gate
pass.

Residual diagnosis for the 25 mismatches: **31** missing mention-reference
occurrences across **13** names, mostly multiple same-name Concepts absent from
the selected scoped providers (`it`×8, `you`×6, `object`×3; the rest are
lower-frequency duplicates). Other differences include reflective-faculty
inventory in the self-report receipt, a causal question-follow-up route, and
the grounding evidence path for `info_status`. Selecting every same-name
provider from the full index is not safe: it expands the profile to 120 seeds
and pulls in the `compiler_theory -> llvm_passes -> llvm_ir` chain, where
`llvm_ir` is absent, so the cached selector correctly marks the closure
incomplete. The next pre-pass increment must resolve content groups/types from
adapter-semantic references and their dependency closure, not select all
same-name providers or promote a partial closure. This narrows the remaining
parity work but does not change any acceptance status.

### 2026-09-26 — Scoped semantic provider groups: 70/74 parity

The missing-reference audit identified `procedural_effect_verbs` as a compact
typed provider for `it`, `you`, `one`, and `access`. Adding only those exact
refs produced a complete 75-seed closure and raised parity **49→61/74**. A
second targeted expansion added exact refs from ten other event-relevant
providers (`arc3_game`, `code_write_request_cues`, communication concept
groups, `gaming_microtheory`, and linguistic/social concept groups), while
excluding providers whose declared closure reaches the absent `llvm_ir`
dependency. The resulting **98-reference**, **95-seed** closure is complete.

The independent fresh-process resource report
[`phase7_profile_resource_20260926_scoped_lexicon_semantic_groups_full74_conversation.json`](../../../evaluation/reports/phase7_profile_resource_20260926_scoped_lexicon_semantic_groups_full74_conversation.json)
has zero errors, **98,959,360-byte** peak RSS, **72,376,320-byte** growth, and
**123.8-ms** maximum event latency, below the 150-ms turn target; its
absolute/growth RSS assertions pass. The paired structural report
[`phase7_seed_profile_parity_20260926_scoped_lexicon_semantic_groups_full74.json`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_scoped_lexicon_semantic_groups_full74.json)
matches **70/74** events with four residual differences: `information_question`
reflective-faculty inventory in the production receipt; `question_followup`
route/repair commitment; `info_status` grounding-evidence path; and one
`defer_permission` referent multiplicity. This is about **1.25 GiB below**
the measured full-boot peak while preserving most observed behavior, but
only **5.6 MiB** of RSS headroom remains. The provider groups were selected for
the fixed English corpus, not generated by a general multilingual semantic
pre-pass, so this is strong bounded-profile evidence rather than closure of
the seed-profile or overall resource/parity gate. `question_followup` and
reflective inventory require cognition/source-policy adjudication before
forcing parity; do not resolve them by adding all name-colliding providers.

#### Adjudication of the four residuals

The four 70/74 structural differences were inspected against their paired
event traces and graph evidence. They do not currently justify blindly adding
providers or claiming a behavioral regression:

* `information_question` (“How are you organised?”): both profiles release a
  valid reflective self-organization receipt, but the inventory contents are
  profile-dependent. This is a genuine inventory-source/parity difference;
  it needs an explicit policy for which held capabilities the bounded profile
  should expose, not surface-key expansion.
* `question_followup` (“Why did it close?”): both profiles keep the answer-topic
  goal resolved and release a repair response. The connected profile routes to
  causal-evidence repair, while the full profile asks back more generally. The
  connected route is more specific, but the trace lacks event/causal evidence
  explaining the closure; preserve the repair and do not infer a causal answer.
* `info_status`: both profiles return the same held sensor-status answer with
  released production. Full boot records `ResolvedQuery -> resolved_referent`,
  while the connected profile records `HeldAnswer -> TopicGroundingEvidence`.
  This is an evidence-path representation difference; confirm the authority
  contract before normalizing it away.
* `defer_permission`: both profiles preserve the same event-bound deferred
  instruction and production receipt. The full profile has one additional
  `signal` referent occurrence (3 versus 2); this is a duplicate/multiplicity
  difference, not a demonstrated instruction-outcome divergence.

Consequently, **70/74 remains an observed structural comparison, not an
accepted parity pass**. The next loading increment remains a graph-grounded,
language-neutral producer of exact seed-scoped refs, followed by fresh-process
full-corpus parity and resource replay. The current fixed-English provider
selection is diagnostic only. Do not choose providers by raw token/name
intersection or force the four traces to match without resolving their source
and authority contracts.

#### Graph-reference binding contract — 2026-09-26

Added `resolve_graph_content_refs` in `substrate/boot_all.py` as the safe
binding stage between an upstream graph resolver and the cached seed index.
It accepts only typed `{type, name}` graph readbacks, resolves a provider only
when unique or when explicit semantic group context narrows it to one, and
returns missing/ambiguous refs as diagnostics. It does not inspect utterance
surfaces, choose among unresolved providers, or expand same-name providers.
The contract tests pass **2/2** (including unique, explicit-group,
ambiguous, and absent refs); whitespace validation passes.

This closes only the deterministic provider-binding seam. The producer that
creates these typed refs from a language-agnostic pre-pass is still absent;
therefore the 70/74 comparison and resource results remain fixed-corpus
diagnostics, not accepted profile parity or a closed resource gate.

#### Content-connection cache — 2026-09-26

Extended the source-validated seed index with named-node `content_connections`
materialized from manifest graph edges, retaining source type/name, edge type,
and target type/name; bumped the cache schema so stale plans rebuild. The graph
reference binder can now use an actual resolved graph connection only when
the same typed edge is declared by exactly one candidate provider; it still
fails closed for partial/multiple matches. Seed-loader tests cover local-node
edge extraction and connection-based disambiguation. A read-only scan of the
current seed corpus found **453** indexed named-content connections across
**26/740** seeds; **41/500** duplicate typed signatures have at least one
single-seed provider connection. This is index coverage evidence, not proof
that Phase 7 event graphs provide those edges or that connected selection
preserves cognition. The graph-native pre-pass and its full-74 replay remain
the next required step.

#### Live graph-reference pre-pass trial — 2026-09-26

The evaluator now has opt-in `--emit-graph-ref-plan` and `--graph-ref-plan`
paths. They read only native mention referents, direct edges among those
referents, and actual Microtheory membership contexts; outputs are replayable
and disclose both reference and closure completeness. The full-74 pre-pass
[`phase7_graph_reference_prepass_20260926_full74_v2.json`](../../../evaluation/reports/phase7_graph_reference_prepass_20260926_full74_v2.json)
resolved **85 refs across 14 seeds**, with **28 ambiguous** and **7 missing**
provider assignments. Direct Concept-to-Concept context edges were present in
**0/74** events; Microtheory contexts were available for 13 ref instances in
9 events. Although the resulting seed closure is syntactically complete,
provider resolution is not. Paired replay
[`phase7_seed_profile_parity_20260926_graph_reference_prepass_v2_full74.json`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_graph_reference_prepass_v2_full74.json)
matches only **42/74** events (32 mismatches; zero execution errors). This
proves the generated refs are not yet a safe selection policy. The next step
is provider identity/semantic context coverage—not adding the remaining
same-name providers wholesale. Do not count this pre-pass process as a
connected-profile resource result.

#### Native node provenance trial — 2026-09-26

To preserve which seed actually created each graph-resolved Concept, the Rust
seed-loader summary now returns local-to-global node IDs. An opt-in
`load_all_seeds(track_content_node_provenance=True)` maps those native IDs to
typed source-seed records; ordinary boots do not retain this per-node map.
The full-74 graph pre-pass now uses exact provider identity instead of
ambiguous name matching. Report
[`phase7_graph_reference_prepass_20260926_full74_v3.json`](../../../evaluation/reports/phase7_graph_reference_prepass_20260926_full74_v3.json)
resolves **119 refs across 22 seeds**, eliminates provider ambiguity, and
exposes **4 missing refs** plus an incomplete dependency closure. The exact
`signal` Concept in `defer_permission` is provided by `operating_systems`,
whose closure includes `compiler_theory -> llvm_passes -> llvm_ir`; the current
vocabulary manifest is `llvm_ir_vocabulary`, so the existing dependency name
does not resolve. This is now a concrete manifest/closure blocker, not a
provider-selection guess. Do not omit the source Concept or call this closure
complete. Reconcile the dependency contract and measure the resulting content
closure before attempting profile parity or resource claims.

#### Closure repair and pre-pass-backed profile — 2026-09-26

The exact `operating_systems` provider exposed a bad dependency ID in
`seeds/llvm_passes.json`: it named `llvm_ir`, while the manifest is
`llvm_ir_vocabulary`. The dependency now names the actual seed, and a regression
verifies the entire four-seed dependency path closes. With that correction,
the v4 native graph pre-pass
[`phase7_graph_reference_prepass_20260926_full74_v4.json`](../../../evaluation/reports/phase7_graph_reference_prepass_20260926_full74_v4.json)
selects **119 typed refs across 22 content seeds**, has **zero provider
ambiguities**, and a complete declared dependency closure. Four graph refs
remain without seed providers (`gate`×3, `blorf`×1), so semantic coverage is
not complete.

The paired pre-pass-derived profile reaches **71/74** structural matches with
zero execution errors; the three residuals are `information_question`
receipt inventory, `question_followup` route/commitment, and `info_status`
grounding path. See
[`phase7_seed_profile_parity_20260926_graph_reference_prepass_v4_full74.json`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_graph_reference_prepass_v4_full74.json).
Two independent 74-event connected runs peak at **98,754,560** and
**99,004,416 bytes** RSS, with **145.70 ms** and **115.57 ms** maximum-event
latency; a same-process replay is structurally equal (`replay_equal=true`) at
**146.82 ms** max. All recorded RSS assertions pass, but the bound has only
about **5.6 MiB** headroom and latency is near 150 ms. Resource reports:
[`first`](../../../evaluation/reports/phase7_profile_resource_20260926_graph_reference_prepass_v4_full74_conversation.json),
[`independent recheck`](../../../evaluation/reports/phase7_profile_resource_20260926_graph_reference_prepass_v4_full74_conversation_recheck.json),
[`determinism replay`](../../../evaluation/reports/phase7_profile_resource_20260926_graph_reference_prepass_v4_full74_conversation_replay.json).
Do not close cognition/parity or comparative release gates from these Phase 7
results; providerless graph refs and the three adjudication cases remain.

Case-level v4 readback sharpens those three differences. The reflective
inventory receipt is profile-bound (conversation lists its own loaded domains;
full boot lists a different, broader held inventory), so it requires a product
contract for bounded-profile self-report rather than copying the full receipt.
`question_followup` remains a repair in both profiles: connected boot asks for
causal evidence, while full boot asks back more generally; neither provides a
causal explanation, and no evidence should be fabricated. `info_status` gives
the same held sensor-status answer and releases a receipt in both profiles,
but grounds through `HeldAnswer -> TopicGroundingEvidence` versus
`ResolvedQuery -> resolved_referent`. These may be valid scoped/evidence-path
alternatives, but remain structural mismatches until explicitly adjudicated.
The prior `defer_permission` referent-count mismatch is absent from v4.

#### Providerless-ref classification — 2026-09-26

The resolver now separates well-formed refs with no seed declaration from
ambiguous/invalid provider binding. The v5 pre-pass
[`phase7_graph_reference_prepass_20260926_full74_v5.json`](../../../evaluation/reports/phase7_graph_reference_prepass_20260926_full74_v5.json)
has **0 ambiguous**, **0 invalid**, **4 unprovided** refs (`gate`×3,
`blorf`), and a complete declared dependency closure. This means provider
resolution is complete for the current seed corpus, not that the agent covers
every referent: `gate` is still unsupported and `blorf` remains OOV. The
scoped provider map is identical to v4, and the fresh v5 paired report
[`phase7_seed_profile_parity_20260926_graph_reference_prepass_v5_full74.json`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_graph_reference_prepass_v5_full74.json)
confirms **71/74** with the same three residual differences. The two v4
independent resource runs and deterministic replay apply to this exact same
scope. Do not equate complete provider resolution with full semantic
coverage, 74/74 parity, or closure of the broader cognition/comparative gates.

#### Resume verification of synchronous conversation seam — 2026-09-26

Rechecked the current Phase 8/conversation/grounding/reference suites:
**77 passed, 1 skipped, 3 failed** in 464.92 s. The topic-search mint test
creates its graph `SearchRequest`, but inline retrieval can end `failed`; its
comment says only minting is asserted. The assertion now accepts that terminal
state, and the targeted test passes **1/1**. `test_question_still_answers`
returns the expected reflective answer
but its legacy trace assertion finds no `linked_graph_answer_message`; the
current v5 corpus report instead records this event through a graph production
receipt, so the old fixture contract needs explicit reconciliation rather than
weakening graph-authority requirements. The third failure
(`test_three_behaviours_discriminated`) passed when run alone and is not
reproduced. A subsequent isolated run confirmed the reflective surface answer
but still failed the legacy trace assertion; the three-behaviour test passed.
No production code changed in this verification. The full suite was not rerun
after the assertion correction. The direct synchronous latency and
trace/production-contract questions remain open.

#### Reflective adaptation release and event trace — 2026-09-26

The reused-turn failure was a production-gate scope mismatch: native
self-organisation evidence retained the supported inventory, while the
audience faculty intentionally abstracted manifold-foreign items in the
surface. The release gate now parses back against the audience-shaped delivery
list derived from that same evidence. The graph evidence records the delivered
list, whether adaptation fired, abstracted source areas, and the abstraction;
the raw supported Microtheory links remain intact. `reply_turn_trace` now
accepts both public inbound speaker roles (`user` and daemon `interlocutor`)
and reports a reflective answer commitment only when native selection,
supported reflective evidence, a same-event answer Message, and a released
receipt all agree.

The prior failing reused-turn chain now passes **5/5**, including both
`test_question_still_answers` and `test_three_behaviours_discriminated`.
Adjacent arbitration, Phase 6A production, and audience-adaptation suites pass
**65/65**. Fresh full v5 report
[`phase8_corpus_report_20260926_reflective_adaptation_release_v1_event_context_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260926_reflective_adaptation_release_v1_event_context_v5.json)
completes **74/74** with zero execution errors. Compared with the previous v5
report, no event reply, release status, authoritative-disposition flag, or
observed-state label changed. Authority remains **55/74**, grounding F1
**0.438**, and Phase 4 complete tuples/promotions remain **0/0**. One-run
turn latency is median **147.56 ms**, p95 **228.19 ms**, max **255.31 ms**;
the <150 ms gate is still open and no improvement is inferred from this single
run. Comparative release remains blocked. The earlier broad run had two
stateful reflective-answer failures before this fix. At that point a full
conversation-module rerun remained outstanding; the later current-code rerun
passes 14/14, as recorded below.

#### Bounded question/meta candidate ingress and fresh envelope — 2026-09-26

The full-ledger bypass experiment showed that skipping Concept backfill entirely
lost one authoritative `question_weather` disposition. Replacing the question
and meta path with the existing indexed, mention-scoped Concept candidates
preserved every Phase 8 event reply, release status, authoritative-disposition
flag, observed-state label, and grounding label; the 74-event comparison had no
event-level differences from the full-ledger v5 run. The code now uses
`_backfill_knows_concept_for_message(mid)` uniformly, including questions, and
no longer widens the ledger again after meta comprehension. Native rules retain
referent/disposition authority; the adapter only materializes exact indexed
name candidates. A regression compares reflective selection and receipt
release against a pre-populated full-ledger control.

The focused index/conversation/native-release set passed **9/9**; follow-up
full current-code verification passes **14/14** for `test_conversation_loop.py`
and **52/52** across indexed referent ingress, language-neutral arbitration,
and Phase 6A production. Fresh full v5 replay
[`phase8_corpus_report_20260926_bounded_question_candidates_v1_event_context_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260926_bounded_question_candidates_v1_event_context_v5.json)
completes **74/74**, zero errors, and no event-level outcome changes. Authority
is **55/74**, grounding F1 **0.438**, and Phase 4 complete tuples/promotions
remain **0/0**. Turn latency is median **143.11 ms**, p95 **231.52 ms**, max
**249.06 ms** (**31/74** over 150 ms). Against the immediately prior single
run, median/over-budget counts are directionally better, but this does not
close latency or prove a stable improvement.

Fresh connected-profile resource reports for the exact v5 graph-ref closure
are
[`first`](../../../evaluation/reports/phase7_profile_resource_20260926_bounded_question_candidates_v1_conversation.json),
[`independent recheck`](../../../evaluation/reports/phase7_profile_resource_20260926_bounded_question_candidates_v1_conversation_recheck.json),
and
[`determinism replay`](../../../evaluation/reports/phase7_profile_resource_20260926_bounded_question_candidates_v1_conversation_replay.json).
All select the complete closure, have zero errors, pass every RSS assertion,
and retain deterministic replay. Peak RSS is **99,094,528**, **98,824,192**,
and **98,975,744 bytes**, leaving only about **5.5 MiB** below the 100 MiB
limit. The first two connected runs peak at **133.94** and **126.84 ms**; the
replay reaches **161.88 ms**, so the strict max-event latency gate is not
robustly closed. Full-boot Phase 8 latency also remains open. Comparative,
Phase 4, broader production and cognition gates remain open.

#### Batched exact RuleSummary lookup — 2026-09-26

Action-sequence profiling showed reflexive-rule detection issuing several
exact RuleSummary queries, each rescanning the complete summary population.
The detector now submits its candidate gap surfaces together; the self-model
resolves them in one graph pass using the same normalized-name OR exact
case-insensitive `keywords_text` predicate and stable `name_rank` ordering as
the single-query API. This preserves the broader query contract without
adding indexes or their memory overhead under the narrow RSS margin. The
combined self-model/conversation/bounded-ingress run passed **29/29**; the
standalone self-model module passed **13/13**, and the batched-vs-single exact
parity regression passed. Two fresh v5 corpus runs preserve all 74 event
outcomes, authority/release labels, and observed states:
[`primary`](../../../evaluation/reports/phase8_corpus_report_20260926_batched_rule_summary_lookup_v1_event_context_v5.json)
and
[`independent recheck`](../../../evaluation/reports/phase8_corpus_report_20260926_batched_rule_summary_lookup_v1_event_context_v5_recheck.json).
Against the prior
v5 run (median/p95/max **143.11/231.52/249.06 ms**, 31 turns over 150 ms),
the fresh runs measure **134.00/187.79/252.45 ms** and
**135.53/198.34/264.55 ms** (median/p95/max); over-budget counts are **27/74**
and **26/74**. Median and p95 improved in both single-run comparisons, but
the maximum regressed and the strict 150 ms gate remains open. The fresh
connected 74-event profile selects the complete closure with no errors,
passes every RSS assertion at **99,143,680 bytes**, and measures **119.28 ms**
maximum event latency
([report](../../../evaluation/reports/phase7_profile_resource_20260926_batched_rule_summary_lookup_v1_conversation.json)).
The independent deterministic replay is also outcome-equal and passes all RSS
assertions at **99,061,760 bytes**, with **142.25 ms** maximum turn latency
([report](../../../evaluation/reports/phase7_profile_resource_20260926_batched_rule_summary_lookup_v1_conversation_replay.json)).
Phase 4,
production/cognition, and comparative gates remain open.

#### Canonical gate repair and matched-context ELIZA reference — 2026-09-26

The canonical acceptance run exposed two real alias-identity regressions from
the public-method serialization decorator and one stale test patching the
class of the forwarding native facade. Serialization now reuses one wrapper
for shared public method objects and rebinds private compatibility aliases;
the facade test patches its instance seam. All three failing cases passed in
isolation after the fixes. The broader battery's pre-fix run had 74 passes and
those three failures; the fixed-tree rerun now passes **77/77** in 239.68 s.

The deterministic ELIZA floor now has a matched v5 raw envelope: its response
function is supplied the event interaction metadata, held-answer setup, and
prior eight signal/response pairs, while its floor policy intentionally stays
stateless and signal-rule-driven. It does not read corpus labels or infer
cognitive capability; provenance is its only measured score. The full
comparative runner suite passes **49/49**, and the stricter context-boundary
adapter tests pass **8/8**. The v5 raw audit
reports ELIZA **1/1**, Gemma **2/2**, and Qwen **2/2** complete raw runs; human
references remain missing and the audit performs no score interpretation.
Fresh full v5 SUT replay
[`report`](../../../evaluation/reports/phase8_corpus_report_20260926_eliza_matched_context_v1_event_context_v5.json)
preserves all 74 event outcomes and traces, embeds the matched ELIZA
provenance (74/74 complete observations), and remains blocked. The latest
replay after the audit optimization
[`report`](../../../evaluation/reports/phase8_corpus_report_20260926_phase4_adjacency_audit_v1_event_context_v5.json)
also preserves every event outcome and the three Phase 4 source records.
Total report time falls from **23.08 s** to **10.05 s** because the post-turn
Phase 4 audit now discovers event links through adjacency rather than scanning
every graph node for each event; this does not change the measured synchronous
turn boundary. Latest turn latency is median **140.02 ms**, p95 **192.95 ms**,
max **257.90 ms**, with **31/74** over 150 ms. Phase 4 remains at **3**
grounding-only sources, zero complete tuples and zero promotions. This closes
only the ELIZA input-profile mismatch; human annotation, cognition/production,
Phase 4 evidence, and strict latency gates remain open. Fresh connected-profile deterministic replay on the current code
selects the complete 74-event closure, has zero unresolved refs/errors, passes
all RSS assertions at **99,131,392 bytes**, and records a **109.96 ms** max
turn with replay equality
([report](../../../evaluation/reports/phase7_profile_resource_20260926_phase4_adjacency_audit_v1_conversation_replay.json)).

#### Conceptualizer worklist flush and current resource replay — 2026-09-26

The conceptualizer now invokes native rules only when the previous scan created
shapes or a monitor verdict leaves native work pending at the round boundary.
This is a worklist-exhaustion optimization only: native graph rules still own
commit/revise decisions, and Python adds no content-selection policy. Receipt
assertions cover the revision path (3 conceptualizer rounds / 4 native passes)
and direct monitor path (2 rounds / 2 passes). The targeted conceptualizer,
conversation-loop, deliberative-production, and Phase 4A suites pass **42/42**.
On a profiled `action_referent` turn, native rule invocations across the full
turn fell from 8 to 6; a single cProfile wall-time sample was noisy, so no
latency improvement is inferred from that measurement.

Fresh full v5 corpus reports
[`primary`](../../../evaluation/reports/phase8_corpus_report_20260926_conceptualizer_worklist_v1_event_context_v5.json)
and
[`recheck`](../../../evaluation/reports/phase8_corpus_report_20260926_conceptualizer_worklist_v1_event_context_v5_recheck.json)
preserve all 74 event outcomes, authority/release labels, graph state, and
Phase 4 source records relative to the adjacency-audit baseline. Primary turn
latency is median/p95/max **132.82/196.97/231.51 ms** with **29/74** over
150 ms; recheck is **136.50/204.69/216.70 ms** with **30/74** over. Median,
maximum, and over-budget count improve against the prior **140.02/192.95/257.90
ms**, **31/74** run, but p95 regresses in both; the strict latency gate remains
open.

The current connected 74-event resource replay
[`report`](../../../evaluation/reports/phase7_profile_resource_20260926_conceptualizer_worklist_v1_conversation_replay.json)
has complete selection, zero errors, equal deterministic replay, no use of
surface text as semantics, all RSS assertions passing, **99,164,160-byte**
conversation peak RSS, and **71,278,592-byte** boot/event growth. Its measured
maximum turn is **119.09 ms**. This is a separate connected-profile sample and
does not erase the slower full-boot corpus tail or close production/cognition,
Phase 4 evidence, or comparative gates. Human reference classes are still
missing; no capability score is inferred.

#### RSS-guarded allocator reclamation — 2026-09-26

A fresh `action_referent` profile attributed about **66 ms** of a 278 ms
profiled synchronous turn to unconditional `malloc_trim`. A full-boot
no-trim diagnostic preserved all 74 event outcomes and lowered turns over
150 ms from 30 to 26, but reached roughly **1.79 GB** process peak RSS; that
policy is rejected. On the connected production profile, a no-trim replay
preserved outcomes and determinism and passed all resource assertions at
**99,766,272 bytes** peak RSS. The implementation now checks current RSS and
skips the allocator scan below the existing **100 MiB** cap, while retaining
best-effort trimming at/above the cap and the old behavior if RSS cannot be
measured. The threshold behavior test passes.

The current connected replay
[`report`](../../../evaluation/reports/phase7_profile_resource_20260926_rss_guarded_heap_trim_v1_conversation_replay.json)
completes all 74 events with zero errors and deterministic equality, complete
seed closure, all RSS assertions passing at **100,167,680 bytes** peak and
**72,265,728-byte** boot/event growth; max turn is **147.29 ms**. Full v5
report
[`report`](../../../evaluation/reports/phase8_corpus_report_20260926_rss_guarded_heap_trim_v1_event_context_v5.json)
matches all 74 prior event outcomes, authority/state labels, release labels,
and Phase 4 records. Its latency is median/p95/max **135.85/192.14/237.09
ms**, with **29/74** turns over 150 ms. The strict full-boot latency gate
therefore remains open; authority is **55/74**, grounding F1 **0.438**, and
Phase 4 still has 3 grounding-only sources, zero complete tuples, and zero
promotions. Combined Phase 7, conceptualizer, and conversation-loop tests
pass **43/43**. Comparative-human references and broader cognition/production
gates remain open.

#### Current full-boot/connected-profile parity audit — 2026-09-26

Replayed the complete 74-event structural comparison on the current source
and graph-reference pre-pass. It now matches **71/74** event observations,
with zero errors in either profile; the older independently captured 3/74
result is stale for this closure/source combination. Differences are:

- `information_question`: the graph reader enumerates all currently loaded
  `Microtheory` nodes, so a connected partial graph yields a different area
  inventory from full boot. Treat this as incomplete answer evidence, not an
  acceptable semantic substitution; the reader or profile needs a sound
  completeness boundary.
- `question_followup`: the full graph binds the repair trouble source to `it`,
  while the connected profile takes `causal_evidence_repair_graph` and asks
  about “causal evidence”. This is a real cognition/production parity defect
  to isolate against the discourse and causal-retrieval ownership boundary.
- `info_status`: the answer and released receipt match; only the normalized
  interpretation readback differs, so investigate whether this is a missing
  graph dependency or trace-only projection difference before changing
  runtime behavior.

The comparison report's full profile reaches **1,436,409,856-byte** RSS and
the connected run measured in the same process reaches **348,336,128 bytes**;
these are not independent resource measurements because the second follows
full boot in that process. Use the fresh-process connected report above for
the memory claim (**100,167,680-byte** peak, within the 100 MiB cap). The
connected profile's normalized parity is substantially improved but not
complete, so it does not yet replace full boot as a production-equivalent
profile. Report:
[`full-vs-connected parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_rss_guarded_heap_trim_v1_full74.json).

#### Native causal-repair priority in full-corpus context — 2026-09-26

The full corpus exposed a scheduler-ordering defect: a generic lexical
ask-back could be released before the already-selected native
`missing_causal_relation_with_anaphor` repair response became available. A
bounded recheck now advances native rules only for that exact graph-selected
repair basis before the generic bridge can commit. It uses no utterance text or
reference label to choose the route. The full corpus sequence regression
passes and verifies the graph-authored clarification receipt, no generic
`which it` receipt, and retention of the event's grounding-only
`Phase4PartialEvidence`; no missing Phase 4 dimensions are imputed.

Fresh full v5 reports
[`primary`](../../../evaluation/reports/phase8_corpus_report_20260926_causal_repair_preflight_v2_event_context_v5.json)
and
[`recheck`](../../../evaluation/reports/phase8_corpus_report_20260926_causal_repair_preflight_v2_recheck_event_context_v5.json)
show that `question_followup` now releases “What event or evidence would help
establish what caused it to close?” with native `repair` authority. Against
the preflight report, this is the only change to event reply, release,
authority, state, or grounding labels. Authority remains **55/74**, grounding
F1 **0.438**, and Phase 4 remains **3** grounding-only sources with **0**
complete tuples/promotions. The full-vs-connected comparison improves to
**72/74**; the remaining differences are `information_question` and
trace-only `info_status`
([report](../../../evaluation/reports/phase7_seed_profile_parity_20260926_causal_repair_preflight_v1_full74.json)).

The independent connected replay
[`report`](../../../evaluation/reports/phase7_profile_resource_20260926_causal_repair_preflight_v2_conversation_replay.json)
selects complete closure, has zero errors and equal deterministic replay, and
passes all RSS assertions at **100,532,224 bytes** peak and **72,503,296-byte**
boot/event growth. Its max turn is **157.08 ms**, so the strict latency gate
remains open. Full-boot latency varied substantially across fresh runs
(primary **236.81/340.30/354.54 ms** median/p95/max; recheck
**197.61/307.25/340.07 ms**), which is not a stable basis for attributing the
change to this one event. The combined Phase 6/Phase 0/Phase 8 batch reported
**47 passed, 1 failed**; the sole failure is the real-weather retrieval test,
which also fails alone in this offline environment. Cognition, production,
latency, Phase 4 completeness, and comparative-human gates remain open.

#### Connected-profile self-organisation scope — 2026-09-26

The remaining `information_question` answer enumerates Microtheories actually
present in the booted graph. A fresh diagnostic found 32 Microtheories in the
agent's explicit `operates_in` closure on full boot and 4 on the connected
profile; the source index contains 740 seed manifests, 412 of them with a
Microtheory grouping. Making the conversation profile load all of that content
just to force inventory parity would discard the bounded-profile contract.
Instead, the reader and surface now explicitly describe the list as the
microtheories currently loaded in the graph, rather than an exhaustive
agent-wide inventory. The graph state carries
`inventory_scope=loaded_substrate_graph` and
`complete_within_scope=true`; names and counts remain graph-derived. This makes
the scope of a partial-profile answer explicit and truthful.

The fresh 74-event full-vs-connected rerun has zero execution errors and
complete seed selection and matches **73/74** events. Its sole residual is
`information_question`, which still differs in `production_receipts` and `turn`
because its loaded inventory differs. This is an explicit scoped deviation,
not a closed parity gate. Separately, `info_status` now prefers its
specific `HeldAnswer -> TopicGroundingEvidence` path over a coincidentally
matching generic `ResolvedQuery`. With the event's scoped lexical content
(`what`, `the`, `sensor`, `status`), an actual full-vs-connected rerun reaches
**1/1 structural parity**, zero errors, and complete connected selection. The
focused regression locks both the evidence priority and the parity result.
Thus `info_status` is closed; `information_question` remains the single
reproduced residual in the current audit. Full report:
[`specific-grounding/scope parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260926_specific_grounding_scope_v1_full74.json).
The focused self-prose/production run reports **21 passed, 1 failed**; the only
failure is the pre-existing network-dependent weather retrieval test. All
other tests in that run, including the graph-authored self-organisation
delivery path, pass. The comparator and full acceptance gates remain open.

#### Validated seed-prepass inventory and refreshed profile parity — 2026-09-26

The seed-index pre-pass now computes a source-hash-validated Microtheory
inventory and caches it with the connectivity index. Boot materializes its
bounded top-12 summary on the existing `Agent` graph root; native arbitration
accepts it only with the inventory schema marker, so the answer remains
graph-supported without loading every grouped seed into the conversation
profile. The reader reports the bounded inventory scope and total area count.

A fresh post-change full-vs-connected run matches **74/74** events with zero
errors and complete connected selection
([report](../../../evaluation/reports/phase7_seed_profile_parity_20260926_cached_inventory_v5_full74.json)).
An independent connected-profile all-event replay is deterministic, complete,
and error-free
([report](../../../evaluation/reports/phase7_profile_resource_20260926_cached_inventory_v2_conversation_replay.json)).
Resource gates are not all closed: peak RSS is **107,868,160 bytes**, above
the 100 MiB absolute cap (although growth assertions pass). Max turn latency
was **123.57 ms** in this replay, but another fresh run exceeded 150 ms, so
the strict latency target remains open. This parity result does not close
cognition/grounding quality, production authority, Phase 4 completeness, or
comparative-human evaluation gates.

#### Connected-profile RSS regression: lazy P0-A exports — 2026-09-26

The prior connected resource regression came from importing
`evaluation.p0a.legacy_io_guard`: Python first executed the package initializer,
which eagerly imported the evaluation broker and manifest verifier, including
Ed25519/cryptography. P0-A's package exports are now lazy, preserving the
historical public names while keeping ordinary guard imports evaluator-light.
A subprocess regression verifies importing the guard does not load the broker,
manifest verifier, or cryptography. The complete evaluation suite passes
**144 passed, 17 skipped**.

Three fresh 74-event connected-profile measurements now pass all RSS assertions
and the 150 ms maximum-event target. Peaks are **102,604,800 bytes**,
**102,449,152 bytes**, and **102,502,400 bytes** for the independent run,
second independent run, and deterministic-replay run respectively; replay is
equal and complete, with zero errors. The strict cap is 100 MiB (104,857,600
bytes), leaving only about **2.1 MiB** of margin. Fresh full-vs-connected parity
remains **74/74** with complete selection and zero errors
([parity](../../../evaluation/reports/phase7_seed_profile_parity_20260926_lazy_p0a_v1_full74.json));
[resource run 1](../../../evaluation/reports/phase7_profile_resource_20260926_lazy_p0a_v1_conversation.json),
[resource run 2](../../../evaluation/reports/phase7_profile_resource_20260926_lazy_p0a_v2_independent.json),
[deterministic replay](../../../evaluation/reports/phase7_profile_resource_20260926_lazy_p0a_v2_conversation_replay.json).
This closes the connected-profile absolute-RSS and per-event latency checks for
these measured runs, not full-boot latency or the broader cognition, production,
Phase 4 completeness, and comparative-human gates.

The current full v5 target recheck after the import fix
([report](../../../evaluation/reports/phase8_corpus_report_20260926_lazy_p0a_import_v1_event_context_v5.json))
confirms cognition/production work remains: authoritative dispositions
**55/74**; grounding recall **0.28**, F1 **0.438**; Phase 4 has three
grounding-only sources but zero complete tuples/promotions. Full-boot latency is
median/p95/max **129.53/211.60/224.29 ms**, with **26/74** turns over 150 ms.
Matched-context comparative release is still blocked on missing human
references and does not interpret scores.

#### Native repair after failed standalone topic retrieval — 2026-09-26

The full profile previously turned `What is a blorf?` into an explicit error:
native answer-topic retrieval ended unresolved, but there was no native
transition from `answer_or_learn` to `repair`. Added a guarded arbitration rule
that acts only after the same standalone event's answer-topic request has
failed without verified support, then routes release through the existing
graph-selected ask-back faculty and production gate. The selected answer-topic
concept supplies the repair focus, so the released clarification targets
`blorf` rather than echoing the whole question. It does not answer or assert
anything about the unknown concept.

The focused repair test passes. The relevant Phase 6/language-neutral/corpus
runner batch is **77 passed, 1 failed**; the sole failure is the known offline
weather-retrieval test, unrelated to the standalone-topic rule. The fresh full
v5 report changes only `info_unknown` relative to the current pre-fix report:
error → released graph-authorized repair; authority increases **55→56/74** and
label matches without authority fall **4→3**. Grounding remains F1 **0.438**,
Phase 4 remains 3 grounding-only sources and **0** complete tuples/promotions,
and full-boot latency remains above the strict bound at
**131.58/195.28/214.94 ms** median/p95/max (**29/74** over 150 ms). Fresh
full-vs-connected parity remains **74/74**; connected replay is deterministic,
error-free, and within current resource bounds at **102,395,904-byte** peak and
**124.70 ms** max event. Reports:
[corpus](../../../evaluation/reports/phase8_corpus_report_20260926_failed_topic_repair_v2_event_context_v5.json),
[parity](../../../evaluation/reports/phase7_seed_profile_parity_20260926_failed_topic_repair_v1_full74.json),
[resource replay](../../../evaluation/reports/phase7_profile_resource_20260926_failed_topic_repair_v1_conversation_replay.json).

#### Native direct-fact continuation candidate — 2026-09-26

The direct held-fact family of declarative continuation now materializes
graph-backed candidates and uses the existing Phase 4A native valuation and
collapse; release is linked to the selected candidate and requires structural
parse-back. Missing native policy fails closed. The Phase 4A discourse-state
adapter now scopes proposals to the specific active goal being bound, avoiding
cross-goal duplicate deliberations. The reflective-answer trace readback now
accepts the validated graph inventory index support path as well as direct
Microtheory nodes.

Focused Phase 4A/live-authority/continuity/reflection/settle-back/Phase 0
verification passes **36/36**. Phase 8 v5 reply, disposition, and release
outcomes are unchanged from the pre-change corpus; authority remains **56/74**,
grounding F1 **0.438**, and Phase 4 complete tuples/promotions **0/0**. New
validated-reference parity is **74/74**; connected replay is deterministic,
complete, error-free, and passes all resource assertions at **98,058,240-byte**
peak and **106.35 ms** maximum event latency. Remaining transitive, held-frame,
residual-stance, follow-up, and floor-holding continuation decisions are still
Python-selected. Full-boot latency and comparative-human gates remain open.
Reports:
[corpus](../../../evaluation/reports/phase8_corpus_report_20260926_native_direct_fact_continuation_v1_event_context_v5.json),
[parity](../../../evaluation/reports/phase7_seed_profile_parity_20260926_native_direct_fact_continuation_v2_graph_ref_full74.json),
[resource replay](../../../evaluation/reports/phase7_profile_resource_20260926_native_direct_fact_continuation_v1_conversation_replay.json).

#### Native collapse for remaining continuation families — 2026-09-26

Extended the Phase 4A native candidate path beyond held direct facts. The
adapter now proposes graph-grounded transitive facts/relations/frames, direct
relation neighbors, held frames, residual-stance frames/facts/inquiries, and
co-mentioned follow-up inquiries in one candidate ledger. Seed-authored policy
rules provide family values/depths; native scoring, Argmax, and rejection
traces choose among alternatives. Python retains candidate discovery and
realization but no longer chooses the winner by family-check order. The
selected `DeliberativeCandidate` is bound to the exact released surface via
`ProductionGateReceipt`; absent current native policy/trace or parse-back, the
continuation fails closed. Floor-holding remains a separate path and is not
claimed migrated by this increment.

Focused verification passes **41/41**. Fresh v5 corpus outcome is **56/74**
authoritative dispositions, grounding recall **0.28**, F1 **0.438**, and
**0/0** complete Phase 4 tuples/promotions. The independent connected 74-event
replay is deterministic and complete with **98,357,248-byte** peak RSS and
**114.35 ms** max event; all resource assertions pass. Validated graph-reference
full-vs-connected parity is **74/74**, zero mismatches/errors. This is an
authority-boundary improvement, not a measured increase in overall semantic
capability. Full-boot latency, grounding/Phase 4 quality, multilingual
realization, generic legacy message release, and comparative-human/small-LLM
references remain open.

#### Exact reflexive RuleSummary lookup cache — 2026-09-26

Profiling identified repeated whole-graph `RuleSummary` scans in reflexive
question parsing (**32 calls / 0.984 s cumulative** under cProfile). A lazy
exact-name / exact-`keywords_text` index now persists on the adapter across
turns and is invalidated before `ensure_rule_provenance()` refreshes or mints
summary nodes. It preserves existing exact matching, `name_rank` ordering,
and no-fuzzy-fallback behavior. Focused self-model/comprehension/conversation
regressions pass **73/73**, including indexed-query equivalence and cache
invalidation after authored-rule refresh.

Fresh Phase 8 v5 event outcomes and authority/grounding/release fields are
unchanged. One full run improves median/p95/max from the immediately preceding
unindexed run's **141.56/198.32/240.44 ms** to **124.97/186.87/221.79 ms**;
over-150-ms turns fall **30→20/74**. This is one-run evidence, not closure of
the strict full-profile latency gate. Connected replay is deterministic and
resource-bounded (**99,749,888-byte** peak, **111.23 ms** max event); current
validated-reference parity is **74/74**. Semantic grounding and Phase 4 tuple
quality are unchanged and remain open. See the linked progress-tracker report
set for machine-readable evidence.

#### Phase 4 promotion eligibility must honor source authority — 2026-09-26

The audit marked complete tuples from any source type promotion-eligible,
while the approved-source audit names only `ThoughtManifold`. Eligibility now
requires both all five physically present dimensions and an approved source
type; a complete `AudienceModel` negative control remains observable as a
complete tuple but is explicitly not eligible. No scoring, promotion, or
missing-dimension inference was added. The focused Phase 4/source/live-bridge
batch passes **24/24**. Fresh Phase 8 remains at 3 grounding-only records and
**0** complete/eligible/promoted tuples; event outcomes remain unchanged.
This fixes a governance gap but does not solve the absent live tuple producer.
Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260926_phase4_authorized_sources_v1_event_context_v5.json).

#### Continuation prior / measured-tuple separation — 2026-09-27

The live continuation producer no longer writes unmeasured zeroes into the
three Phase 4 dimensions it does not observe. It opts into a narrow
`authored_family_prior` mode; native family rules may assign expected value,
and a distinct native score records `valuation_basis=authored_family_prior`.
The complete-tuple scorer now requires `complete_phase4_tuple`. Default
materialization remains strict, and an unlisted family gets no valuation or
selection. Phase 4A tests pass **21/21**. This integrity correction leaves
the missing approved complete-tuple producer and all Phase 4 promotion gates
open. Mode isolation also prevents family-prior seed rules from modifying
complete-tuple expected values. The Phase 4A / tuple-audit batch passes
**31/31**; a fresh Phase 8 v5 replay preserves authority **56/74**, grounding
F1 **0.438**, and zero complete tuples/promotions. Full-boot latency and the
human/small-LLM comparative gate remain open. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260927_prior_mode_isolation_v1.json).

#### Native instruction-gap production receipt — 2026-09-27

The native unhandled-instruction gap rule now marks its event-bound
filed-concern route. After the mechanical instruction-outcome write and
native rule pass, the adapter reads the exact graph-authored reply and binds
the existing graph-instruction receipt only when the report's gap/topic
content is recoverable. The receipt says gap/inform, not that the requested
action was executed. Phase 6A passes **17/17**; fresh Phase 8 v5 confirms all
three formerly unreceipted gap reports now have a released receipt tied to
their graph Message. Across the report there are **43** released substantive
non-error replies and seven withheld diagnostic-error receipts; other
no-receipt cases are explicit errors or silence. Authority, grounding, and
Phase 4 results are unchanged. Latency remains
above budget. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260927_instruction_gap_receipt_v1.json).

The Phase 8 runner now exposes an exact-surface production-release audit:
every nonempty non-diagnostic reply must have a released receipt for that
surface; explicit error and silence outcomes are reported separately. Fresh
v2 replay verifies **43/43** substantive releases, seven withheld
diagnostic-error receipts, no unreceipted substantive surfaces, and no change
to cognition or Phase 4 tuple counts. Latency remains above budget. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260927_instruction_gap_receipt_v2.json).

#### Phase 2 source audit and authority-missing classification — 2026-09-27

The Phase 2 four-way evaluator previously crashed when a live event carried
authority_missing. Since this status includes no supported referent path,
the grounding-only projection maps it to unknown; the permission-authority
field remains separate. Phase 8 now embeds the source-category audit on the
validated fixed corpus, with custom inputs marked unavailable. Phase 2 plus
reference tests pass **36/36**, and the focused Phase 8/status tests pass
**2/2**. Current source evidence remains **14/50** referent true positives,
**36** false negatives, zero false positives (F1 **0.438**): 14 declared
discourse-state, 11 declared graph-path, 11 surface/uncertainty-only
misses. This is attribution, not a relaxation of grounding; actual
event-linked support must be supplied before those observations can be
promoted. Report:
[Phase 8 grounding-source audit](../../../evaluation/reports/phase8_corpus_report_20260927_grounding_source_audit_v1.json).

#### Event-scoped discourse-reference support — 2026-09-27

The grounding trace found that the adapter's graph binding check is global:
`CurrentTopic` and an in-focus `DiscourseReferent` are not joined to the
current conversation, addressee, or event. Existing `ReferenceResolutionEvidence`
also lacks a live `DiscourseEvent` link. The 14 corpus annotations in the
discourse-state source category therefore remain labels for investigation, not
runtime evidence; no statuses were promoted. Phase 2U in the execution plan
specifies the needed scoped evidence seam and positive/cross-scope negative
controls. Phase 2 metrics remain unchanged at **14/50** true positives and
F1 **0.438**.

#### Scoped discourse-reference runtime seam — 2026-09-27

Live message ingress now passes its state/speaker/addressee handles into the
language adapter. Anaphoric support requires an earlier grounded topic event
in that same scope; global `CurrentTopic`/salience is not evidence. The source
audit accepts only the new scoped-event path for this category. Positive and
cross-scope negative controls pass; Phase 2 measurement/reference tests pass
**36/36**. The fresh fixed-corpus replay remains **14/50** referent true
positives, zero false positives (F1 **0.438**): annotated discourse-state
cases still lack an observed event-linked binding. Thus this is a safer
support seam, not a grounding-gate closure. Phase 8 also remains at authority
**56/74**, Phase 4 **0/0/0**, substantive receipt coverage **43/43**, and
median/p95/max latency **131.28/191.13/206.86 ms** (**23/74** over 150 ms).
See [event-scoped reference replay](../../../evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v1.json).

The v1 replay found that scope was derived before the inbound Message received
its `Agent.received` edge, so it selected the interlocutor as addressee while
the persisted event correctly targeted the agent. Scope derivation now uses
the inbound Message origin and matches the event writer. The corrected v2
replay verifies five scoped reference paths, including `question_followup`,
and grounding improves to **18/50** (precision **1.00**, recall **0.36**, F1
**0.529**) with zero false positives. Phase 2 measurement/reference tests
pass **36/36**; unscoped, wrong-speaker, wrong-addressee, and other-state
negative controls pass. The 14 declared discourse-state misses remain an
open evidence set, so Phase 2U is not closed. Current Phase 8 also reports
authority **56/74**, Phase 4 **0/0/0**, receipts **44/44**, and latency
**134.12/192.82/216.68 ms** (**27/74** over 150 ms); comparative status
remains blocked at provenance. Report:
[event-scoped reference v2](../../../evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v2.json).
The dedicated language-neutral evidence-arbitration suite also passes
**33/33** against the corrected scope ordering.

The pre-parse scope lookup now only reads an existing discourse state; it
does not create state/common-ground nodes on the first event. Combined Phase 2
measurement/reference plus arbitration verification passes **70/70**. A fresh
v3 replay preserves the grounding gain (**18/50**, F1 **0.529**, no false
positives) and all five scoped paths, but shows **141.67/199.50/226.41 ms**
median/p95/max latency (**31/74** over 150 ms), so the resource gate remains
open and no timing gain is claimed. Ten declared graph-path misses still have
no runtime-linked evidence; they remain unresolved rather than accepting
corpus labels or lexical Concepts as proof. See
[event-scoped reference v3](../../../evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v3.json).

#### Phase 2T overlay measurement — 2026-09-27

The separate seven-case event-to-commitment overlay now has a persisted,
input-hashed result:
[`Phase 2T report`](../../../evaluation/reports/proposition_event_commitment_measurement_20260927_phase2t.json).
It verifies 9/9 event identities, 1.00 materialization/commitment/consequence
accuracy, five proposition evidence+origin provenance links, one expected
supported consequence with provenance, and four fail-closed negative cases.
No reply evidence or external-world truth is used. The harness injects explicit
typed uptake, therefore these results validate the lifecycle/projection slice
only and do not establish live autonomous uptake or change the fixed 74-event
grounding score. Three focused tests pass.

#### Phase 3B addressed common-ground proposition binding — 2026-09-27

The live neutral semantic-event path now supplies the addressed
`CommonGround` ledger to proposition materialization. A regression with two
addressees in one discourse state verifies each claim is linked only to its
own ledger; an unaddressed path retains the shared-ledger contract. The Phase
3 lifecycle test explicitly links selection/execution/result events to their
Goal. Proposition-bridge and Phase 3 exit suites pass **14/14**. Broader
grounding and comparative gates remain open.

#### Current-code connected-profile refresh — 2026-09-27

The full-vs-connected rerun on current code preserves **74/74** structural
observations, with zero errors and complete selection of 99 seeds. Two
independent connected-profile runs pass the 100-MiB/150-ms resource bounds
(peak RSS **102,395,904 / 102,400,000 bytes**; max turn **136.72 / 142.18
ms**); the deterministic replay is equal at **102,506,496 bytes** and
**149.96 ms** max. The replay sits only 0.04 ms inside the latency ceiling, so
the result is a bounded-profile pass with fragile latency margin, not robust
closure of full-boot resource/latency acceptance. Four graph references remain
unprovided by the closure plan; grounding and comparative gates remain open.

#### Indexed self-dialogue Concept lookup — 2026-09-27

`self_dialogue._find_concept()` now queries the maintained exact-name index
when available, retaining the existing scan fallback. Targeted suites pass
**25/25**, including regression coverage for exact/case-sensitive,
first-match behavior and live index updates. Fresh Phase 8 preserves every
event-level reply/state/force/release/evidence outcome against the preceding
indexed run (74/74; zero errors); authority remains **56/74**, grounding F1
**0.529**, and Phase 4 tuples/promotions **0/0**. Full-boot latency is
**107.31/180.98/233.43 ms** median/p95/max, with **11/74** over 150 ms. The
connected replay is deterministic and passes resource assertions at
**102,522,880-byte** peak RSS and **111.60 ms** max event latency; connected
parity is **74/74**. This lookup optimization does not close full-boot latency
or cognition gates. See the execution plan for reports.

#### Typed modal offer/refusal evidence — 2026-09-27

Graph-backed modal semantics on a first-person parsed action now produce
neutral offer/refusal force evidence; an offer additionally requires a held
object Concept, preventing the OOV `blorf` case from being upgraded. Focused
tests pass **3/3**. Phase 8 authority coverage increases **56/74 -> 59/74**
from force corrections on `refusal`, `refusal_action`, and grounded-target
`offer_inspect`; unresolved-target `offer` stays unpromoted. Replies are
unchanged. Refusal
dispositions remain `defer` instead of expected error/blocked, and the offer
still has no authorized production. Grounding F1 remains **0.529**, Phase 4
tuples/promotions **0/0**. Connected parity is **74/74** and RSS is within the
100-MiB cap, but one measured max event is **154.65 ms**; full-boot latency is
**109.49/168.22/192.05 ms**, with **12/74** over 150 ms. The combined
arbitration/comprehension/parity batch also has two unresolved
speech-act-fixture failures (77 passed, 2 failed). See the execution plan for
reports and exact failure scope.

#### RuleSummary unchanged-body refresh fast path — 2026-09-27

Rule provenance now compares the exported body hash before regenerating
structural summaries; unchanged rule bodies skip nested-tree walks for both
native and graph-resident rules. The self-model suite passes **15/15**, with a
regression test proving the fast path and an authored-rule test proving edits
still remirror. This optimizes repeated refreshes, not first-time materializing
the complete mirror. A fresh 74-event Phase 8 replay is outcome-identical to
the preceding modal-evidence report with zero errors; authority **59/74**,
grounding F1 **0.529**, Phase 4 tuples/promotions **0/0**. Latency remains open
at **110.84/173.35/206.86 ms**, **14/74** over 150 ms. See the execution plan
and linked replay.

#### Grounding-classification integrity — 2026-09-27

The Phase 2 evaluator now maps generic runtime `unresolved` to `unknown`, not
`coreference`; only explicit `unresolved_reference` is coreference evidence.
This avoids claiming an antecedent-resolution attempt where the runtime only
reports absence of grounded support. Phase 2 measurement/reference tests pass
**75/75** across grounding/reference/action tests before the final continuation
rule compatibility adjustment; its focused regression passes **1/1** after
that adjustment. Adapter-typed unresolved anaphoric/deictic references now
retain `unresolved_reference`; generic gaps remain `unresolved`. A fresh fixed
74-event Phase 8 replay yields **4/6** coreference (precision **1.00**,
recall **0.67**, F1 **0.80**) without promoting any referent. Referent recall
remains **18/50**, precision **1.00**, recall **0.36**, F1 **0.529**; authority
is **59/74**, expected-state matches **56/74**, substantive releases **43/43**.
Resource latency (**106.31/172.41/196.13 ms**, **11/74** above 150 ms), Phase 4
tuple promotion (**0**), and comparative adjudication remain open. See the
execution plan's linked refreshed Phase 8 report.
The current connected profile is deterministic with zero errors,
**73,392,128-byte** RSS growth, all resource assertions true, and **132.46
ms** maximum event latency; full-vs-connected structural parity is **74/74**
with zero mismatches under the validated graph-reference pre-pass.

Current latency attribution (separate instrumented replay) counted **119**
`comprehend()` calls, with **74** initial passes and **45** post-write/branch
settles, totaling about **1.41 s**. A cProfile run attributed **15.41 s** to
full load/provenance under instrumentation, **9.42 s** to all 74 synchronous
turns, and **4.37 s** to 58 reply conceptualizer pipelines. No pass was
removed; the full production recovery gate remains mandatory. Uninstrumented
latency is **106.31/172.41/196.13 ms** median/p95/max, **11/74** over 150 ms.

#### Participant-pronoun grounding safeguard — 2026-09-27

The anaphoric-question adapter no longer treats participant “you” as a
discourse antecedent for “Which valve do you mean?” The scoped-anaphor,
action-anaphor, and fragment-actor regressions pass **3/3**. Fresh fixed-corpus
replay removes the `repair_clarify` false-positive grounding promotion, but
also lowers supported-positive recall from **18/50** to **15/50**: precision
**1.00**, recall **0.30**, F1 **0.462**. Treat this as a fail-closed safeguard,
not a capability gain; adjudicate the three removed positives against typed,
event-scoped referent evidence before restoring any binding behavior.
The case audit identifies them as `question_ack`, `social_question`, and
`blocked_permission`; their prior support was only a generic same-scope prior-
topic path with no selected referent identity or argument-to-topic link. Keep
them fail-closed until that typed graph evidence exists; preserve
`repair_clarify` as a negative control.
Authority is **59/74**, state matches **56/74**, Phase 4 tuples/promotions
**0/0**, and release remains blocked. Turn latency is **108.82 ms** median /
**199.68 ms** max. Connected replay is deterministic **74/74**, zero errors,
**73,396,224-byte** RSS growth / **100,171,776-byte** peak, **125.46 ms** max;
resource assertions pass. Full-vs-connected parity remains **74/74**, zero
mismatches. See the latest execution-plan section and linked reports.
The affected grounding/reference/action regression batch now passes **78/78**
in **546 seconds**.

#### Phase 8 latency attribution — 2026-09-27

An instrumented v5 replay profile identifies several distinct costs behind
the open 150 ms turn gate. The slow-turn profile includes repeated native
`run_rules` calls (about **50–104 ms** cumulative in sampled slow turns),
reply conceptualization (**53–118 ms**), and an occasional
`_trim_reclaimable_process_heap()` call (**72 ms** in one sampled turn when
process RSS triggered allocator reclamation). Profiling overhead raised the
sampled turns to **197–244 ms**, so these numbers localize costs but are not a
latency benchmark. No cognitive/native settlement pass was removed and no
optimization is justified by this profile alone; the uninstrumented Phase 8
measurements above remain authoritative. The latency gate stays open pending
an optimization that preserves settlement semantics and a fresh uninstrumented
replay.

#### WordNet-backed connected reference provider — 2026-09-27

Added the sourced lexical Concept `gate` (`WordNet 3.0`, `gate.n.01`) to the
connected seed provider map. It resolves three missing `Concept:gate` refs;
`blorf` remains the sole explicit unprovided/OOV ref. Full-vs-connected parity
is **74/74**, zero mismatches/errors, complete dependency closure; pre-pass
uses neither corpus labels nor surface text. The full grounding/reference/
action batch passes **78/78** after the related neutral reference-scope guard.
Fresh Phase 8 improves referent grounding **15→17/50** (precision **1.00**,
recall **0.34**, F1 **0.507**); coreference **5/6**, unknown **16/16**,
contradiction **0/2**, zero unrelated-answer promotions. Authority and
expected-state matches are **59/74**; Phase 4 remains **0/0** complete /
eligible tuples. Connected replay selection and replay determinism pass, peak
RSS is **102,834,176 bytes** (under 100 MiB), but max event latency is
**151.90 ms**; full Phase 8 max is **190.62 ms**. Production, Phase 4, latency,
and comparative gates remain open; see the new execution-plan section for
linked reports.

#### Current connected-profile and full-boot recheck — 2026-09-27

The current worktree was remeasured on all **74** fixed corpus events. The
connected profile completes seed selection, replays deterministically with zero
errors, peaks at **102,645,760 bytes** RSS, and reaches **139.96 ms** maximum
turn latency; all resource assertions pass. Fresh full-vs-connected parity is
**74/74**, zero mismatches/errors. This closes the connected-profile check for
this snapshot only; the exact reports are linked in the execution plan.

The independent full-seed Phase 8 v5 report remains blocked: median/p95/max
latency **109.70/177.17/232.37 ms**, **12/74** over 150 ms; grounding **17/50**
(precision **1.00**, recall **0.34**, F1 **0.507**); authority **59/74**; Phase
4 **0/0** complete/eligible tuples. The three former generic-topic positives
remain unpromoted (`question_ack` unresolved, `social_question` unresolved,
`blocked_permission` authority-missing). Next recovery requires event-linked
typed evidence and the negative-control cases; it must not relax participant or
prior-topic binding. Production, full-boot latency, Phase 4, and comparative
human-reference gates remain open.

#### Preserve parsed relation provenance without inferring a fact — 2026-09-27

The live language adapter's composed relation was not reaching the graph-resident
`CommunicationInterpretation` when relation fields were nested in the
comprehension object rather than dispatch fields. The adapter now projects the
selected subject/predicate/object values and typed POS/role tags as
`communication_relation_projection.v1`, explicitly marked
`selected_parse_unverified`. Existing predicate/object readbacks are filled
from the same parse when absent. This adds no world edge and no grounding
authority. Post-settlement readback attaches only lexical Concepts already
linked by native comprehension; the `route` Concept edge does not promote an
instance-grounding result. The grounding/reference suite passes **37/37**,
including two relation-projection tests. A fresh full Phase 8 replay changes
no event outcomes (0/74 mismatches), keeps grounding **17/50**, Phase 4 **0/0**,
and release blocked. Fresh connected replay is deterministic/error-free on
**74/74**, selection-complete, **102,850,560-byte** peak RSS, **127.47 ms** max
turn; full-vs-connected parity is **74/74**, zero mismatches. Full-seed latency
is **106.68/173.79/211.80 ms**, with **13/74** above 150 ms. Production and
cognition release gates remain open; see the canonical plan's linked reports.

#### Current 2026-09-27 acceptance snapshot — authored answer evidence

The `vision_science` authored-answer integration gap has been closed for the
ten entries in that seed: v1.1.0 supplies explicit referent/status/path fields,
typed `TopicGroundingEvidence`, `grounded_by` links, and agent ownership edges.
An end-to-end regression proves the answer is released without external
retrieval through the graph information-production receipt; the poisoned
same-topic control remains fail-closed. The focused authored-answer,
scene-description, poisoned-answer, Phase 6 information-production, and seed
the full topic-grounding plus Phase 2 reference-evidence suites pass **69
passed, 1 skipped** on full seed boot. The current Phase 8 report remains
**62/74** authoritative, **47** substantive releases, referent grounding
**18/50** (P=1.00, R=0.36, F1=0.529), Phase 4 **0/0/0**, and comparison
blocked at provenance. The fresh
connected 74-event profile passes resource assertions (**103.31 ms** max,
**102,821,888-byte** RSS peak); fresh full/connected parity is **74/74**, no
mismatches. This is one knowledge-production slice, not cognition-gate closure.

#### Phase 4 valuation-source recheck — 2026-09-27

The live evidence boundary was re-audited after the authored-answer seed
integration. The remaining three `Phase4PartialEvidence` sources are grounding-
only. `_record_conversation_decision()`'s token-indexed `grounded_value` is a
learned response preference, not a candidate-specific valuation source, so it
cannot supply expected value, residual cost, consequence, or novelty. No
promotion or bridge relaxation was made; native `no_candidate` remains
authoritative until a cognition faculty produces the full candidate-bound
tuple. Live-evidence, partial-evidence, and explicit-no-candidate checks pass
**12/12**. Current Phase 4 counts remain **0/0/0** (complete/eligible/
promoted); all other release gates remain open.

#### Current 74-event acceptance recheck — 2026-09-27

Fresh current-tree Phase 8 v5 replay remains blocked at provenance: **62/74**
native-authoritative dispositions, force exact **50/74**, grounding **18/50**
(P=1.00, R=0.36, F1=0.529), **47** substantive releases, and Phase 4
**0/0/0**. The typed refusal/offer adapter force is present; the combined
social-question event remains repair because the graph has no group-readiness
evidence. The report-runner suite passes **29/29** after a stale transport test
was changed to use a genuinely neutral statement while preserving its
annotation-independence assertion. Full report and remaining gates are linked
in the canonical execution plan.

#### Adjudicate the frozen speech-act parity deltas — 2026-09-27

Kept the 133-utterance pre-migration fixture unchanged and separated it from
the current live contract. Eight exact live parse deltas already adjudicated
against current grammar/grounding requirements are now explicit test overrides;
the known `Focus on the reading work.` verb-head signal change is separately
recorded. The full parity module passes **6/6**, retaining scratch native-rule
parity and the canonical-rule round-trip while checking every unchanged live
case against the historical capture. This closes the stale frozen-byte-match
test failure, not broader language-force accuracy or overall Phase 1 exit.

#### Separate offer recognition from offer eligibility — 2026-09-27

The language adapter now recognizes first-person modal ability offers as
`social_action` independently of whether the offered action target is held as
a Concept. It transports `offer_target_status` (`concept_available`,
`unresolved`, or `missing`) as neutral evidence. Arbitration accepts only a
concept-backed target; unresolved turn-compatible offers repair, while
incomplete non-turn offers defer. The release path now sends repairs through
the native-selected clarification faculty; if no recoverable repair surface
exists, it fails closed rather than leaking a generic acceptance. Deferred
non-turn offers suppress candidate replies and have no response expectation;
ordinary non-turn statements retain their neutral acknowledgment behavior.
The Phase 6 social-production module and the focused ordinary-nonturn
acknowledgment regression pass **11/11**; the full
`tests/test_language_neutral_evidence_arbitration.py` module passes **39/39**
after narrowing the non-turn guard. The updated 74-event
replay improves force exact match from **50/74** to **52/74** and authoritative
dispositions from **62/74** to **64/74**; all **48/48** substantive replies
are receipt-backed, with no corpus regressions. `offer_unknown` now emits a
released clarification and `offer_repair` stays silent. Referent grounding
remains **18/50** (P=1.00, R=0.36, F1=0.529), Phase 4 remains **0/0/0**, and
comparison remains blocked at provenance. This targeted correction does not
close Phase 1 or the broader cognition/production gates. Report:
[`typed-offer repair Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_offer_repair_v2.json).

#### Typed nonunderstanding report enters native repair — 2026-09-27

The English language adapter emits typed repair evidence only for a parsed
first-person negated-understanding report. Native arbitration selects the
repair/clarification path, and the graph-selected clarification is released
with a production receipt; third-person and affirmative controls do not
inherit the act. Focused Phase 6 and neutral semantic-frame transport checks
pass **12/12**, with the dedicated end-to-end control passing. Fresh 74-event
Phase 8 authority rises to **65/74** and substantive receipt-backed production
to **49/49**, no regressions. Force exact remains **52/74**; referent grounding
**18/50** (P=1.00, R=0.36, F1=0.529); Phase 4 **0/0/0**; comparative release
blocked at provenance. Connected resource rechecks pass in three runs at
**116.81–135.87 ms** max latency and **103.06–103.10 MB** peak RSS, with
full/connected parity **74/74**. Full boot remains above strict caps at
**347,041,792-byte** boot/event RSS growth and **197.71 ms** maximum event
latency. This is one repair increment, not acceptance closure. See the
progress tracker's linked artifacts for detail.

#### Supplemental teacher-learning and delayed-recall probe — 2026-09-27

Added `phase8b-teacher-grounded-repeat-v1` because the fixed Phase 8 corpus
has no teacher-learning or repeated-memory case. The controlled probe verifies
absence before teaching, typed grounded source evidence, a graph-linked
receipt-backed answer, an unrelated intervening answer, then recall backed by
the identical `HeldAnswer` and `TopicGroundingEvidence` with a distinct
receipt. Pilot results: learning **1/1**, memory **1/1**; focused integration
test **1/1**. This is one deterministic target-system mechanism check only;
the fixed corpus remains unchanged, no matched baseline has been collected,
and broad learning/memory/comparative acceptance stays open. Artifact:
[`Phase 8 memory/learning probe`](../../../evaluation/reports/phase8_memory_learning_probe_20260927_v1.json).

#### Current target blinded packet refresh — 2026-09-27

Rebuilt the anonymous Phase 8A packet against the current target report. It
contains **370 unscored response rows** across 74 cases; target labels and
system identity are absent from the rater packet. The raw-reference audit
remains complete for the three script/model baselines (ELIZA 1/1, Gemma 2/2,
Qwen 2/2) but has no human-reference runs and no scored annotations.
Comparative acceptance is therefore still open on human-reference collection
and blinded dual rating/adjudication. The packet is linked in the canonical
execution plan.

#### Bounded connected profile is now the fresh daemon default — 2026-09-27

The daemon defaults fresh launches to the validated connected `conversation`
profile; explicit `--seeds full` still requests all seeds, and saved-checkpoint
resume remains unchanged. This makes the measured bounded conversational
profile the production path rather than an opt-in. Default/closure tests pass
**3/3**; a fresh 74-event run completes selection without errors and passes
all resource assertions (**121.84 ms** maximum event latency, **103,063,552
bytes** post-run RSS, **74,895,360 bytes** boot/event growth). A real fresh
`--once` launch with no seed flag selects conversation and loads **71/71**
connected seeds. Strict full-boot resource acceptance remains open. Report is
linked in the canonical plan. Async typed-offer acceptance now has an
event-bound graph-act release path through the production gate, with a daemon
regression and synchronous/unresolved controls. The prior honest-floor test
stopped before the dispatcher even though the selected disposition expected
acceptance; it now checks the full release and confirms no action-execution
receipt is produced. Full daemon-debug status is **17 passed, 1 failed**; the remaining
HTTP test is blocked by the runner's socket-bind permission. Focused
default/closure tests pass **3/3**.

#### Ground typed offer targets through exact graph referents — 2026-09-27

The grounding adapter now accepts the existing semantic object from a typed
first-person ability offer only if it is content/noun typed, the language
boundary independently reports `concept_available`, and an exact substantive
Concept exists in the graph. Unknown targets and unrelated refusal/anaphora
paths are not promoted. The history-aware 74-event Phase 8 replay raises
grounded referent TP from **18 to 20** with **zero false positives** (precision
**1.00**, recall **0.36→0.40**, F1 **0.529→0.571**). This closes a specific
adapter omission, not the corpus grounding gate; Phase 4 remains **0/0/0** and
resource and comparative gates remain open. Report is linked in the canonical
execution plan.

#### Recheck connected resource bounds on current code — 2026-09-27

Three independent fresh-process 74-event connected-profile reports after the
typed-offer grounding change show complete seed selection, zero errors, all
resource assertions passing, max turns **107.23/135.58/146.81 ms**, and RSS
peaks **102,416,384/102,539,264/102,363,136 bytes**. The first run additionally
confirms deterministic replay. This revalidates connected production bounds;
full-boot resources and reflex-specific latency are still open. See the three
reports linked in the canonical execution plan.

#### Multi-topic learning and delayed-memory mechanism probe — 2026-09-27

The target probe now covers five distinct, invented topics. Each was absent
before teaching, backed by its own typed graph evidence, answered through a
released graph-linked commitment, and recalled after other-topic queries and
two intervening turns. Learning and delayed memory both pass **5/5**; each
topic preserves its own HeldAnswer/evidence identity and receives distinct
release receipts. This remains target-only mechanism evidence, not a
population estimate or a comparison; raw reference-model and human runs are
still absent. Artifact:
[`multi-topic probe`](../../../evaluation/reports/phase8_memory_learning_probe_20260927_multitopic_v2.json).

#### Blinded annotation workflow made importable — 2026-09-27

Implemented exact-packet-bound dual-rater validation, nominal agreement and
Cohen's kappa readback, and independent blinded adjudication of disagreements.
Incomplete/disputed rows remain unscored; the audit never reads response text
or the private alias key. Focused intake and packet-builder tests pass **6/6**.
Two blank 370-row templates are linked from the Phase 8A note, and packet
target response text matches the newest current-code replay on all **74**
events. This enables, but does not constitute, human adjudication: dimension
rubrics and completed rater forms are still missing, so comparative release
remains open.

#### Language-neutral arbitration regression reconciliation — 2026-09-27

The full `tests/test_language_neutral_evidence_arbitration.py` module exposed
one stale allowed-basis assertion: the typed nonunderstanding repair now
correctly records `typed_nonunderstanding_report`, but the older mixed
uncertainty test had not included that native arbitration basis. Updated only
the expected basis set; focused nonunderstanding controls pass **2/2**, and
the complete language-neutral arbitration module passes **39/39**. Runtime
behavior and corpus outcomes were not changed; broader cognition and release
gates remain open.

#### Current multilingual semantic-ingress recheck — 2026-09-27

Revalidated the existing Spanish/Japanese semantic-frame path together with
the live non-turn semantic-event ingress:
`.venv/bin/pytest -q tests/test_semantic_event_ingress.py
tests/test_language_neutral_variation.py` passes **7/7**. The language-specific
adapters still converge on neutral evidence consumed by native arbitration;
this verifies the existing path only and does not close broader language,
turn-production, or corpus-coverage requirements.

#### Preconnected common-object concept and grounding recheck — 2026-09-27

The conversation anchor set now preloads the curated `wordnet_common_objects`
seed, extended with a WordNet 3.0 `pump.n.01` concept. This verifies the
connection-first seed path on an actual continuation request: “And then
inspect the pump” is candidate-grounded and selects `act`, without implying
an inspect faculty or executing an action. A held-out unknown `blorf` remains
unresolved. The action-evidence module passes **36/36**. Fresh Phase 8 grounding
improves **20→21/50 TP**, with **0 FP**, precision **1.00**, recall **0.42**,
F1 **0.592**; authority/release metrics are unchanged, Phase 4 tuple/promotion
is **0/0**, and the overall comparative gate remains blocked. The fresh
connected-profile run reports complete event seed selection, RSS growth
**73,773,056 bytes**, peak RSS **100,470,784 bytes**, and a maximum turn of
**183.23 ms** (`info_unknown`), exceeding the 150 ms target in this sample.
Thus bounded RSS is observed, but latency acceptance needs another run and is
not claimed. Artifacts:
[`Phase 8 corpus`](../../../evaluation/reports/phase8_corpus_report_20260927_wordnet_pump_connected_seed_v1.json),
[`connected resources`](../../../evaluation/reports/phase7_profile_resource_20260927_wordnet_pump_connected_conversation.json).

#### Connected-profile parity assertions and latency profile — 2026-09-27

Re-audited the current Phase 7 semantics and corrected two stale test
expectations: the unresolved action target remains an event-bound goal with an
honest no-faculty surface, and the scoped profile comparison matches **5/8**
events with three remaining turn-state differences. The Phase 7 module passes
**20/20**. A fresh all-event connected run has full seed selection, zero errors,
and bounded RSS, but maximum turn latency is **167.26 ms**, above 150 ms. A
separate profile of the converse workload locates the dominant work in reply
conceptualization, utterance decoding, and native rule evaluation; no
optimization has yet been validated. The connected latency acceptance gate
remains open. See the current resource report linked in the execution plan.

#### Full-seed Phase 8 v5 replay and latency trace — 2026-09-27

Current full-seed replay of all **74** event-context/history8 cases measures
**147.91/280.15/334.16 ms** median/p95/max, with **36/74** turns exceeding
150 ms. Grounding is **21 TP / 29 FN / 0 FP**, native disposition authority
**65/74**, and production release accounting is **49 substantive releases**,
**16 explicit errors**, **9 authorized silent non-turns**, and **0
unclassified silences**. Phase 4 complete/eligible/actual tuples remain
**0/0/0**; comparative release remains blocked at provenance. A profiled slow
`social_address` call shows a conceptualizer receipt with **3 native passes
across 2 rounds**. The seven `run_rules` calls comprise those three passes,
three full-graph `WorldAdapter.comprehend()` passes, and one isolated
scratch-graph speech-act classifier (six live-graph sweeps total). No pass has
been proven redundant, so no latency optimization is claimed. Artifact:
[`current Phase 8 replay`](../../../evaluation/reports/phase8_corpus_report_20260927_resume_live_tree_v1.json).

#### Connection-first conversational content pre-pass — 2026-09-27

Historical initial checkpoint; resource and test findings below are superseded
by the complete-seed-group correction in the following entry.

The live connected profile now performs a seed-index pre-pass and resolves
message-boundary lexical candidates to typed `Concept` providers, their
content groups, and bounded one-hop/declarative dependency closure before
loading newly needed content. The accumulated per-turn path restores exact
full-profile readback parity (**74/74**, zero mismatches/errors), but is not
resource-acceptable in its current form: the latest 74-event run reaches
**116,498,432-byte** peak RSS and **420.42 ms** maximum turn latency, above the
100 MiB and 150 ms limits. By contrast, the fixed-batch typed pre-pass report
passes those assertions (**102,014,976-byte** peak; **132.66 ms** max turn),
but requires candidates to be known before boot. Therefore connection-first
selection is functionally demonstrated, while open-ended per-turn loading
remains gated on resource reduction. Repeated self-model/grounding reconciliation
was inspected and retained because these passes refresh derived graph evidence;
no speculative skip was introduced. Compilation and `git diff --check` pass;
the combined loader/envelope suite reports **39 passed, 2 failed**. One failure
is a stale expectation that an ambiguous shared `Concept` belongs to only one
provider; current planning intentionally retains both. The other is an
eight-event structural-parity failure and remains unresolved (the separate
74-event incremental parity artifact is 74/74). Artifacts:
[`per-turn parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_per_turn_ingress_prepass_v5.json),
[`per-turn resources`](../../../evaluation/reports/phase7_profile_resource_20260927_per_turn_ingress_prepass_v5.json),
[`fixed-batch resources`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_typed_prepass_v1.json).

#### Complete-seed-group pre-pass parity and resource correction — 2026-09-27

The earlier batch parity gap was traced to slicing candidate-selected manifests
that had not declared `selective_content_keys`: native local edges then pointed
at omitted nodes, the loader's fallback could partially reload nodes, and the
resulting graph differed from full boot. Slicing is now restricted to manifests
that explicitly opt in; selective native slices retain their owning
Microtheory/ancestor scaffolding and only edges whose local endpoints survive.
Connected one-hop closure prefers the current provider, then declared load
dependencies or same-group providers, and does not pull unrelated same-name
providers. The complete loader/envelope suite passes **42/42**; Python
compilation and `git diff --check` pass. Fresh complete-seed-group replay has
**74/74** matched events,
zero mismatches/errors, complete selection, **102,641,664-byte** peak RSS,
**75,825,152-byte** boot/event growth, and **110.20-ms** maximum turn. A second
independent resource process measured **102,719,488-byte** peak and
**128.44-ms** maximum turn; both are under the stated limits, with only about
2 MiB of RSS headroom. This validates the nonincremental batch path when its
candidate set is available before boot. `WorldAdapter.converse()` still uses
the incremental path for newly observed candidates when a caller has not
supplied a preboot candidate set; that open-ended runtime path is not yet
resource-acceptable, so fully eliminating lazy content loading remains open.
Artifacts:
[`full/connected parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_batch_complete_seed_groups_v2.json),
[`complete-group resources`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_complete_seed_groups_v2.json).

#### Sealed preloaded candidate profile — 2026-09-27

Added `incremental_content_loading=False` for callers with a complete
pre-boot candidate set. It resolves and loads the connected groups before the
first turn, then reports any out-of-set terms as `preload_only_unavailable`
without invoking seed loading. The Phase 7 batch path now exercises this mode;
tests assert no per-turn seed mutation and preserve the separate opt-in
incremental behavior. Latest sealed and incremental full-corpus comparisons
both reach **74/74**, with zero mismatches/errors. Fresh sealed resource
reports v3/v4 show **102,658,048 / 102,797,312
bytes** peak RSS; maximum turn was **150.86 / 115.63 ms**. The memory bound
passes narrowly and latency is unstable at the 150-ms boundary. The live
incremental profile remains resource-infeasible (**116,887,552 bytes** peak,
**380.23 ms** max). This is a usable no-per-turn-loading profile only when the
candidate set is available before boot; broad unknown-topic coverage and
overall Phase 7 acceptance remain open. Artifacts:
[`sealed parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_batch_preloaded_sealed_v3.json),
[`incremental parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_per_turn_complete_seed_groups_v1.json),
[`sealed resources v3`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_preloaded_sealed_v3.json),
[`sealed resources v4`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_preloaded_sealed_v4.json),
[`incremental resources`](../../../evaluation/reports/phase7_profile_resource_20260927_per_turn_complete_seed_groups_v1.json).

#### Native continuation deliberation trace coverage — 2026-09-27

The Phase 8 turn trace previously enumerated only deliberations reachable
through `about_goal` links. Live continuation-family deliberations instead
carry a direct `generated_from_message` link, so a selected native candidate
ledger could be omitted from serialized turn readback. The trace now includes
either graph linkage, and the transitive-continuation test verifies the native
candidate ledger is present. This is a readback/observability correction only:
authored family priors remain distinct from complete Phase 4 tuples and do not
change tuple eligibility or promotion counts. Validation: the focused
continuation test passes and `tests/test_phase8_corpus_runner.py` passes
**30/30**. `tests/test_reply_trace_migrated.py::test_adapter_reply_marked_not_agent`
still fails independently because current reply metadata reports `adapter`
while that test expects `agent`; this work does not alter reply-source
semantics. A fresh full Phase 8 corpus replay is still required before
updating corpus-level deliberation or Phase 4 counts.

#### Phase 8 native deliberation readback schema correction — 2026-09-27

The evaluator expected flat deliberation status/source fields, but
`reply_turn_trace()` serializes graph attrs under `attrs`. The evaluator now
supports both forms and a regression test checks selected/candidate/selection
readback while preserving empty-trace semantics. Tests: **52 passed** across
the Phase 8 runner and Phase 4A deliberation suites. Fresh fixed-corpus replay:
[`deliberation readback v2`](../../../evaluation/reports/phase8_corpus_report_20260927_deliberation_readback_v2.json).
Across 74 events it reports **18** deliberations, **15** explicit
`no_candidate`/`discourse_state` results, and no serialized candidates or
selections on this corpus route. The separate live-continuation test proves
that direct `generated_from_message` deliberation is now included in a turn
trace; the corpus does not exercise that continuation path. Phase 4 remains
**0/0/0** complete/eligible/promoted tuples, grounding **21/50 TP, 29 FN, 0
FP** (F1 **0.592**), native disposition authority **66/74**, and substantive
receipt-backed releases **50**. Replay latency is **84.94/169.74/207.84 ms**
median/p95/max, with **8/74** over 150 ms. Comparative status remains blocked
at provenance. Readback correctness is improved, but this does not itself
close the cognition, resource, or comparative gates.

#### Current-tree Phase 4 producer inventory recheck — 2026-09-27

Re-ran `audit_phase4_tuple_sources()` against the active seed tree after the
latest runtime/readback changes. It still finds **0 exact five-dimension seed
records and 0 near matches**; the sole approved source type remains
`ThoughtManifold`. The current 74-event runtime report likewise contains no
candidate/selection rows on the corpus route and its only event-linked partial
records are the three explicitly grounding-only `topic_grounding` sources.
This confirms that the missing Phase 4 work is an upstream candidate-bound
valuation/consequence evidence producer, not an adapter projection or audit
gap. No dimensions have been copied from salience, response preference,
residual-risk, or answer-grounding faculties. The cognition gate remains open;
the next implementation must identify an existing faculty that can
authoritatively supply the full tuple (or establish such a faculty under the
canonical semantics) before native Phase 4A can select/promote live candidates.

Rechecked the closest existing predicted-outcome source, `AdaptiveControl`'s
`OutcomePrediction`: it owns a controller-specific `expected_value` with
`provenance_kind=predicted` and `observation_status=not_observed`, but does not
own grounding, residual cost, consequence, or novelty. Its later
receipt-verified observation is an outcome-calibration record, not the
candidate's missing pre-decision tuple. Neither record can be promoted by
renaming its source type or copying adjacent attrs; integrating it would
require a candidate-bound producer that supplies the complete semantics and
preserves prediction-versus-observation provenance.

#### Incremental connected-loader index reuse — 2026-09-27

The open-ended connected profile previously re-hashed all seed manifest
contents whenever each newly observed lexical candidate required provider
resolution, despite retaining the validated provider map. The runtime path now
checks the manifest file set and `(size, mtime_ns)` snapshot between turns;
any change still goes through `_read_seed_index()` and its authoritative
content digest before refreshing the map. A focused invalidation test proves
that new candidates reuse the cached map while an edited manifest triggers
revalidation. The full seed-loader/Phase 7 suite passes **43/43**. On the
current 838-manifest tree, three local measurements average **15.2 ms** for
the metadata snapshot versus **188.9 ms** for full content hashing (12.4x less
time at that check boundary).

This does not close the end-to-end resource gate. Two fresh 74-event
incremental profile reports show peak RSS **118,759,424 / 118,874,112 bytes**
and maximum turn latency **401.70 / 384.98 ms**, both still over the stated
100-MiB and 150-ms limits; there is no controlled proof yet that overall turn
latency improved. The measurements are recorded as a narrowed loader-index
cost, not as acceptance. Artifacts:
Fresh full-vs-incremental comparison remains **74/74** matched, zero semantic
mismatches, and zero errors:
[`stat-cache parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_per_turn_stat_cached_v1.json).
[`per-turn stat-cache v1`](../../../evaluation/reports/phase7_profile_resource_20260927_per_turn_stat_cached_v1.json),
[`per-turn stat-cache v2`](../../../evaluation/reports/phase7_profile_resource_20260927_per_turn_stat_cached_v2.json).

#### Process-local validated seed-index reuse — 2026-09-27

Follow-up profiling found repeated content hashing in `_read_seed_index()`
itself during startup, before the incremental candidate prepass's separate
metadata check could help. The loader now caches its source-validated index,
paths, provider/rule maps, and digest in process memory. It reuses this entry
only while the manifest path set and `(size, mtime_ns)` snapshot are unchanged;
metadata changes continue through full content-digest and persistent-cache
validation. Focused cache/invalidation tests pass (**3**), and the complete
loader + Phase 7 suite passes **45/45**. Isolated cold-event cProfile time
dropped from **1.20 s to 0.91 s**, diagnostic only.

Fresh full/connected parity is still **74/74**, zero errors/mismatches:
[`parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_per_turn_memory_cached_v1.json).
Two independent incremental resource runs yield **4,550 / 4,490 ms** total
conversation time, **150.37 / 147.86 ms** measured max, with `defer_permission`
slowest at **153.19 / 150.47 ms**. Thus latency remains marginal and not
robustly below the 150-ms threshold. Peak RSS is **122,478,592 / 121,614,336
bytes**; growth assertions pass, but the absolute conversation RSS assertion
fails in both runs. Reports:
[`resource v1`](../../../evaluation/reports/phase7_profile_resource_20260927_per_turn_memory_cached_v1.json),
[`resource v2`](../../../evaluation/reports/phase7_profile_resource_20260927_per_turn_memory_cached_v2.json).
This reduces redundant loader work without changing connectedness or cognitive
decisions; overall resource, cognition, authority, Phase 4, production, and
human-comparison gates remain open.

#### Full-corpus import/prewarm memory diagnostic — 2026-09-27

Retained-allocation tracing of the 74-event connected replay attributes about
**12.3 MiB** to Python code objects unmarshalled through `importlib`. A
no-prewarm diagnostic produced exactly the same 74 observations with zero
errors, but its one run still peaked at **104,833,024 bytes** and reached
**146.22 ms** max event latency. That remains above the 100-MiB cap and too
close to the 150-ms limit to accept. The regular full-corpus report remains
**109,395,968 bytes / 149.01 ms**. Broad runtime prewarm is not the sole or
sufficient memory fix; next investigation should target retained graph state
or a specifically measured import boundary, then repeat resource and parity
tests independently.

The graph-growth audit found no existing bounded-retention/expiry contract for
conversation evidence. The 74-event replay adds **2,065 graph nodes**; the
largest accumulations include **314 Mention**, **242 Message**, **175 Intent**,
**101 Unknown**, and **74 each** of `CommunicationInterpretation`,
`DiscourseEvent`, and `Episode` nodes (counts from the same run without the
evaluator's post-turn audit projections). No nodes were pruned: prior messages,
mentions, discourse events, and episodes can support reference resolution and
later explanation. Therefore blanket turn-history deletion is not an
acceptable resource fix. A valid bounded-memory increment needs an explicit
graph-native retention/compaction contract that preserves active discourse
references, durable propositions/outcomes, and provenance, plus a replay
equivalence/fidelity test across the retention boundary.

#### Sealed prepass current-tree resource check — 2026-09-27

The fixed-corpus batch prepass was rerun against the same tree: it selects the
complete **96-seed** lexical closure and a separate full/connected comparison
matches **74/74** with zero errors or semantic mismatches. Current resource
measurement is **115,396,608 bytes** peak RSS and **119.51 ms** maximum event
latency, so the absolute-memory gate fails. Diagnostic recursive object sizing
finds roughly **8.2 MB** in the retained source index and **6.0 MB** in the
derived selection structures. Clearing loader caches after batch boot frees
about **4.8 MB** of measured peak RSS but remains over the 100-MiB ceiling.
Current reports supersede older sub-limit batch measurements for acceptance:
[`batch parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_batch_prepass_current_v1.json)
and
[`batch resources`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_current_v1.json).
Next resource work should reduce the retained footprint while preserving the
full connected closure and must re-run the same 74-event parity/resource gates.

#### Canonicalized connected-index labels — 2026-09-27

The cached prepass now interns repeated seed IDs, provider/group labels, typed
reference names, rule names, and inventory strings across the full index and
its companion maps. It preserves the same 96-seed closure and selection facts;
a loader regression checks that duplicate provider labels share one string
object. The full loader/Phase 7 suite passes **45/45**. Fresh full/connected
batch parity is **74/74**, zero errors or mismatches:
[`parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_batch_prepass_interned_v1.json).
Two independent resource runs peak at **113,463,296 / 113,455,104 bytes**,
about **1.9 MB** lower than the preceding batch runs, with max event latency
**130.29 / 115.15 ms**. Absolute RSS still misses the 100-MiB cap by about
**8.2 MiB**. Artifacts:
[`resource v1`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_interned_v1.json),
[`resource v2`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_interned_v2.json).
This partial memory reduction leaves the resource gate and broader cognition,
production, authority, Phase 4, and comparative gates open.

#### Sealed-profile index-cache lifetime — 2026-09-27

For a complete non-incremental prepass, the agent already retains the resolved
candidate-to-provider map and loaded-content inventory. The profile now drops
the global full source index and all-provider selection lookup tables after
successful boot; incremental profiles retain them for future terms. Sealed
events still report out-of-prepass terms as unavailable without loading seeds.
The focused cache-isolation test passes, the full loader/Phase 7 suite passes
**46/46**, and fresh full/connected parity remains **74/74** with zero errors or
mismatches. Two resource runs peak at **110,112,768 / 109,854,720 bytes** and
reach **115.14 / 119.04 ms** maximum event latency. Cache-lifetime reduction
saves about **3.6 MB**, but peak RSS remains **4.8 MiB** over the 100-MiB limit.
Reports:
[`parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_batch_prepass_released_cache_v1.json),
[`resource v1`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_released_cache_v1.json),
[`resource v2`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_released_cache_v2.json).
The resource, cognition, production, authority, Phase 4, and human-comparison
gates remain open.

#### Route vocabulary in selective seed slices — 2026-09-27

Selective content slices preserve explicit `instruction_route` Concepts as
runtime routing vocabulary, while their requested-content match count remains
content-only and unrelated concepts remain excluded. A completed connected
prepass over the three comprehension route seeds now suppresses the adapter's
first-turn manifest repair read. Loader/Phase 7 tests: **46 passed**. Fresh
full-vs-connected corpus replay: **74/74**, equal, zero errors/mismatches, no
surface-text semantics ([report](../../../evaluation/reports/phase7_seed_profile_parity_20260927_route_concepts_v1.json)).
The dedicated regression confirms no first-turn manifest reads for those route
seeds. Final full-vs-connected parity remains **74/74**, equal, no errors or
mismatches ([report](../../../evaluation/reports/phase7_seed_profile_parity_20260927_route_concepts_final_v1.json)).
The standard eight-event envelope peaks at **91,299,840 bytes** and **36.67 ms**,
with all configured RSS assertions passing
([report](../../../evaluation/reports/phase7_profile_resource_20260927_route_concepts_v1.json)).
The 74-event diagnostic remains above the absolute cap at **109,395,968 bytes**
and reaches **149.01 ms** ([report](../../../evaluation/reports/phase7_profile_resource_20260927_route_concepts_all_v1.json)).
The standard envelope passes; corpus-scale resource, cognition, production,
authority, Phase 4, and human-comparison gates remain open.

#### Compact reflexive RuleSummary index — 2026-09-27

Turn-allocation tracing found `_build_rule_summary_exact_index()` retaining
duplicate Python attrs dictionaries for about **12,000** native `RuleSummary`
nodes. The per-agent exact lookup snapshot now retains only graph node IDs,
indexed by exact name/keyword and name rank; it reads attrs from the live graph
only when a query matches. No rule matching or answer authority moved out of
the graph. Self-model/comprehension/loader tests pass **80/80**, with targeted
lookup/remirror regressions **3/3** after the final guard. Full/connected parity
is **74/74**, no errors or mismatches:
[`parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_batch_prepass_compact_rule_index_v1.json).
Independent resource runs peak at **109,412,352 / 109,297,664 bytes** and max
turn at **146.53 / 126.39 ms**. RSS improved slightly but remains about **4.2
MiB** above the 100-MiB cap. Reports:
[`run 1`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_compact_rule_index_v1.json),
[`run 2`](../../../evaluation/reports/phase7_profile_resource_20260927_batch_prepass_compact_rule_index_v2.json).
The resource gate remains open, as do the wider cognition, production,
authority, Phase 4, and human-comparison gates.

#### Fresh Phase 8 status and typed-refusal control — 2026-09-27

A current-tree 74-event replay confirms cognition/production
status: grounding **21/50 TP, 29 FN, 0 FP** (F1 **0.592**), disposition
authority **66/74**, receipt-backed substantive releases **50**, explicit
error surfaces **14**, authorized no-reply outcomes **10**, and Phase 4
complete/eligible/promoted tuples **0/0/0**.
Small/modern LLM and human comparison scorecards remain unavailable under the
fixed protocol; ELIZA has provenance coverage only, not capability scores.
Fresh artifact:
[`typed-refusal defer`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_refusal_defer_v1.json).

The typed-refusal terminal path now preserves the graph's `defer` plus
`reply_expectation=not_expected` as native no-reply for turn-compatible
refusals. It does not mint an acknowledgment or synthetic receipt. Phase 8
authorizes that silence only from native force/disposition/mode/reply-slot
readback. The fresh replay changes explicit-error count **15→14** and
authorized silence **9→10**; unclassified silence remains **0**, and all
grounding, disposition-authority, substantive-release, and Phase 4 counts are
unchanged. Focused conversation, language-evidence, and Phase 8 suites pass
**87/87**. Fresh full/connected parity is **74/74**, zero errors/mismatches:
[`parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_typed_refusal_defer_v1.json).
The 74-event connected resource run peaks at **109,445,120 bytes** (absolute
RSS gate still fails), with max latency **130.66 ms**:
[`resource`](../../../evaluation/reports/phase7_profile_resource_20260927_typed_refusal_defer_v1.json).
The cognition/grounding, resource, Phase 4, and human-comparison gates remain
open.

#### Connected-profile optional transport import split — 2026-09-27

Moved `urllib.request` out of eager imports in the bounded HTTP fallback and
uncached Wiktionary download paths. Two fresh 74-event connected replays remain
semantically identical (**74/74**, zero errors, complete selection); measured
peaks were **107,544,576 / 107,925,504 bytes**, with maximum event latencies
**132.88 / 125.23 ms**. Both improve on the previous **109,445,120-byte**
baseline. The persisted repeat still exceeds the absolute 100-MiB memory
ceiling by **3,067,904 bytes**. Its exact resource evidence is
[here](../../../evaluation/reports/phase7_profile_resource_20260927_optional_transport_import_split_v1.json).
Focused tests pass **3/3**. Broader socket-dependent
checks are constrained by this sandbox's denied socket operation and cannot
be counted as passing. Vision/shape runtime dependencies remain because the
selected connected closure includes `vision_foundation` and shape providers.
The resource, cognition, production, Phase 4, authority, and human-comparison
gates remain open; see the detailed evidence and limitations in the
[execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

#### Connected-profile allocator envelope on glibc 2.39 — 2026-09-27

Combining the transport import split with startup settings
`PYTHONMALLOC=malloc MALLOC_ARENA_MAX=1 MALLOC_TRIM_THRESHOLD_=32768`
produced two fresh, exact-parity 74-event runs with complete 96-seed selection,
zero errors, RSS peaks **104,517,632 / 104,321,024 bytes**, and max event
latencies **114.78 / 140.41 ms**. Every resource assertion passed. The loader
and Phase 7 suites pass **46/46** under this configuration. The connected
corpus resource gate is now met on this glibc host under this exact pre-startup
configuration; portability and full-boot RSS remain unproven. See both linked
resource reports and operating-envelope conditions in the
[execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md). Cognition,
production/authority, Phase 4, and comparative gates remain open.

#### Attributed-source path readback — 2026-09-27

After native reported-content production validation succeeds, the graph
interpretation now exposes the `ReportedContentEvidence -> prior same-speaker
DiscourseEvent -> source Message` path as a separate attributed-source trace.
Phase 8 and Phase 2 project it under `attributed_source_utterance`; it does not
replace world/referent grounding evidence, and the grounded status remains
`unresolved` because the path establishes what was said, not its truth. The
focused production/Phase 2/Phase 8 suites pass **57/57**. A fresh 74-event
Phase 8 report preserves **21 TP / 29 FN / 0 FP (F1 0.592)** and verifies the
source path for `question_source` without claiming grounding. This closes the
evidence-path audit for this attributed recall route, not the grounding gate.
See the [report](../../../evaluation/reports/phase8_corpus_report_20260927_reported_source_path_v1.json)
and [execution-plan details](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

#### Turn-compatible missing-authority disposition — 2026-09-27

Added native arbitration for complete turn-compatible information requests
whose typed frame reports missing authority. For `info_choice`, the graph now
records `blocked` / `missing_permission_authority`; its unsupported route
recommendation remains withheld. Phase 6/Phase 2/Phase 8 tests pass **58/58**.
Fresh corpus disposition authority rises **66/74→67/74**; the expected state
is still `answer`, so state-match/release remain open. Grounding F1, production
totals, and Phase 4 counts are unchanged. See the [fresh report](../../../evaluation/reports/phase8_corpus_report_20260927_missing_authority_readback_v1.json)
and [execution-plan details](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).
Full/connected parity is **74/74** with zero errors/mismatches, and the
connected resource rerun passes at **104,423,424 bytes / 128.46 ms** under the
documented glibc environment:
[parity](../../../evaluation/reports/phase7_seed_profile_parity_20260927_missing_authority_rule_v1.json),
[resources](../../../evaluation/reports/phase7_profile_resource_20260927_missing_authority_rule_v1.json).

Phase 4 source re-audit on the same current corpus found **3** linked partial
records, all `topic_grounding` and grounding-only; the other four dimensions
are absent. Seed-manifest audit found **0** exact or near-complete tuples, and
`ThoughtManifold` remains the only approved source. The live result correctly
stays **0 complete / 0 eligible / 0 promoted**. Do not fabricate dimension
values from grounding records or response-preference estimates; an upstream
candidate-bound cognition source and calibration are still required. See the
[execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md) and
[current Phase 8 report](../../../evaluation/reports/phase8_corpus_report_20260927_missing_authority_readback_v1.json).
Phase 4 live-evidence, partial-audit, and deliberation guard suites pass
**32/32**; incomplete/unapproved sources remain non-candidates.

Incremental connected prepass now bounds the agent-local provider map to the
current candidate batch while preserving the validated process-level index.
The loader suite passes **25/25**. A fresh 74-event replay remains complete
with zero errors, but measures **114,651,136 bytes peak RSS** and **153.64 ms**
maximum event latency; growth checks pass while the absolute memory and latency
limits remain open. See the [resource artifact](../../../evaluation/reports/phase7_profile_resource_20260927_incremental_prepass_bounded_provider_cache_v1.json)
and [execution-plan entry](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).



**Selectable connected pre-pass and current tail-latency evidence (2026-09-29):**
The Phase 8 report CLI now permits `--runtime-seed-profile
conversation_corpus_prepass`; its default remains unchanged. The sealed profile
uses the corpus signals only (no reference labels), resolves **150** lexical
candidates into **96** connected seeds before turn one, and performs no
per-turn content loading. The Phase 8 runner suite passes **41/41**, including
full/sealed/hybrid/incremental parity checks. Ten pre-transport runs and six
post-transport runs preserve identical semantic observations. The first set
has one boundary miss; the post-transport set has five passes and one **174.61
ms** `action_referent` miss. Typical median is roughly **49–65 ms**; this does
not close strict max-latency repeatability. A lazy process-local TLS trust-context cache was added after
profiling found repeated context construction on an unknown-topic search; its
focused test passes. Socket-based integration tests are restricted by the
sandbox, so that layer lacks live-socket verification. A timed sealed-corpus
run measured **109,792 KiB** peak RSS. Grounding remains **21/29/0 TP/FN/FP**,
production **54/15/0**, Phase 4 **0/0**, and matched human/LLM comparisons
remain unavailable. Full profile caveats, reports, and links are in the
[execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

**Current-source multilingual live-path regression (2026-09-29):** The live
Spanish/Japanese history-selection route, async evidence/release checks, and
language-neutral variation suite pass **17/17**. This reconfirms only the
covered ES/JA frames, graph-native history decision, and gated realization /
release paths. Broad multilingual comprehension and general production
parity remain unproven; corpus grounding, strict latency, Phase 4, comparative,
and substrate acceptance gates remain open. The substrate stream is still
concurrent rather than deferred. See the current-source regression note in
the [execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The selection cache now stores content-key provider rows as deltas against its
shared Concept-provider map, preserving explicit non-Concept and differing
provider sets. Loader tests pass **26/26**, and full-vs-incremental replay
matches **74/74** with zero errors. Two fresh resource runs reduce peak RSS
repeatably to **113,274,880 / 113,258,496 bytes**; absolute RSS remains above
the 100-MiB cap, and max event latency is **167.41 / 176.04 ms**, above 150 ms.
This narrows—but does not close—the incremental resource gap. See the
[parity report](../../../evaluation/reports/phase7_seed_profile_parity_20260927_delta_selection_index_v1.json),
[resource runs](../../../evaluation/reports/phase7_profile_resource_20260927_incremental_delta_selection_index_v1.json),
and [execution-plan details](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The live incremental profile also compacts its retained per-seed metadata
after the source-validated provider/selection caches are built, retaining
typed content connections and dependency fields while releasing unused full
index payloads. Manifest metadata changes still trigger a fresh source digest
and index rebuild. Loader and Phase 7 envelope suites pass **27/27** and
**21/21**; full-vs-incremental parity is **74/74** with zero errors. Two fresh
resource runs measure **112,836,608 / 112,975,872 bytes** peak RSS and
**150.31 / 175.36 ms** maximum event latency. Both strict absolute bounds
remain open despite the repeatable memory reduction. See the [parity report](../../../evaluation/reports/phase7_seed_profile_parity_20260927_compact_incremental_snapshot_v1.json),
[resource runs](../../../evaluation/reports/phase7_profile_resource_20260927_compact_incremental_snapshot_v1.json),
and [implementation record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

After this seed/rule change, the connected-profile resource envelope was
repeated under the documented glibc settings in two independent fresh
processes. Both selected the same complete 96-seed closure, produced identical
stable observations with zero errors, and passed all resource assertions;
peak RSS was **104,067,072 / 104,275,968 bytes** and max event latency
**133.85 / 137.23 ms**. This reconfirms only the connected profile on this
host/configuration. See the [two reports](../../../evaluation/reports/phase7_profile_resource_20260928_action_availability_run1.json)
and [run 2](../../../evaluation/reports/phase7_profile_resource_20260928_action_availability_run2.json).

The typed communicative-failure path now makes the `error_signal` event's
disposition graph-authoritative: seed concept kind is retained, and only a
typed speech-function subject plus typed deficiency predicate supplies
`communication_failure` evidence to the existing native error rule. The
ordinary inability negative control remains unmarked. The fresh corpus report
now reads **68/74** authoritative dispositions (up from **67/74**); the other
six are still open. This does not change the grounding, resource, Phase 4, or
human-comparison gates. See the [focused implementation and replay record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md#graph-typed-communicative-failure-evidence--2026-09-27)
and [report](../../../evaluation/reports/phase8_corpus_report_20260927_typed_failure_v1.json).

Native arbitration now also assigns `defer` to adapter-typed assertions in a
turn-compatible continuation slot without adopting their proposition. The
language-neutral focused suites pass **79/79**, and the fresh corpus replay
raises authoritative disposition readback to **69/74**; five cases remain.
See the [continuation replay](../../../evaluation/reports/phase8_corpus_report_20260928_continuation_disposition_v1.json)
and [execution record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The current compact-index Phase 8 replay and blinded packet have also been
refreshed: **67/74** disposition authority, **21/50 TP** grounding (F1 **0.592**),
**50** receipt-backed releases, **14** explicit errors, **10** authorized
silent slots, and Phase 4 **0/0/0**. The new **74-case / 370-response** packet
matches the active-tree target **74/74**, with scores and notes blank. Existing
CPU LLM/ELIZA raw references audit as complete, but both human classes remain
missing; the comparative gate additionally awaits rubric approval and blinded
ratings. See the
[current target report](../../../evaluation/reports/phase8_corpus_report_20260927_current_compact_index_v1.json),
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260927_compact_index_v1.json),
and [comparative record](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md).

Typed action availability now contributes neutral evidence only when a
graph-typed dynamic action is negatively available; native arbitration blocks
it in a turn-compatible response slot. The adapter and language-neutral
arbitration modules pass **80/80**; fresh Phase 8 authority rises to **70/74**
with `refusal_unknown` corrected. Four non-authoritative cases remain. See the [fresh replay](../../../evaluation/reports/phase8_corpus_report_20260928_action_availability_v1.json)
and [implementation record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

Full boot remains outside the strict resource gate after a fresh same-settings
run: **1,411,518,464-byte** peak RSS, **424,574,976-byte** post-run RSS,
**397,328,384-byte** boot/event growth, and **201.65 ms** max event latency.
RSS peaked during the **13.73 s** boot, so the next resource investigation
should target full-seed materialization, not connected event handling. The
[full-boot report](../../../evaluation/reports/phase7_profile_resource_20260928_action_availability_fullboot.json)
preserves the detailed counts and measurement boundaries.

The full language-neutral arbitration module passes **44/44**. An unresolved
action request in a non-turn response slot now receives native `defer`, rather
than inheriting `act` from an instruction route. The replay
shows this changed only `response_yes`; native authority is **71/74** and
matched-without-authority count is **0**. Because the fixture expects `act`,
state agreement is **66/74**, so this is an authority/safety improvement with
an explicit reference disagreement, not a score gain. Three cases remain
non-authoritative. See the [replay](../../../evaluation/reports/phase8_corpus_report_20260928_unresolved_response_action_v1.json)
and [rule record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The exact current tree also passes two fresh connected-profile resource runs:
same complete 96-seed selection, identical stable observations, zero errors,
all resource assertions passing, peak RSS **104,300,544 / 104,161,280 bytes**,
and maximum event latency **134.78 / 126.73 ms**. This is bounded only for the
connected profile and documented glibc configuration; the full-boot gate
remains open. Reports:
[run 1](../../../evaluation/reports/phase7_profile_resource_20260928_response_action_run1.json),
[run 2](../../../evaluation/reports/phase7_profile_resource_20260928_response_action_run2.json).

Adapter-derived uncertainty on a selected information gap now crosses the
authoritative interpretation boundary and native arbitration selects `learn`
with an event-bound, source-constrained learning request. The request has no
answer authority and does not imply retrieval occurred. The fresh replay
raises native disposition authority **71/74→72/74** and fixture agreement
**66/74→67/74**; `social_question` and `learn_result` remain non-authoritative.
Grounding is unchanged at **21/50 TP, 29 FN, 0 FP**. Report:
[Phase 8 replay](../../../evaluation/reports/phase8_corpus_report_20260928_uncertain_learning_gap_v2.json).

The latest tree also asks for grounding context when native cognition selects
`learn` for a turn-compatible interrogative without a grounded answer topic.
It makes no answer commitment. Fresh Phase 8 authority is **74/74**; production
is **53 released replies / 8 explicit errors / 13 authorized silences / 0
unclassified silences**. Grounding is **21/29/0 (F1 0.592)** and Phase 4 has
**0** promotions. `learn_uncertain` remains an explicit unresolved declarative
learning case. Two connected-profile replays are deterministic, but both
exceed the absolute RSS bound (**107,012,096 / 107,053,056 bytes**); boot/event
growth and event latency checks pass. Full-boot memory, absolute RSS,
production p95/max latency, fixture agreement, and comparative evidence remain
open. See the [latest full replay](../../../evaluation/reports/phase8_corpus_report_20260928_learning_context_clarification_resume_v2.json),
[execution record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md#unanswered-learning-request-clarification-and-exact-tree-recheck--2026-09-28),
and [resource run 1](../../../evaluation/reports/phase7_profile_resource_20260928_learning_context_clarification_resume_v1.json) /
[run 2](../../../evaluation/reports/phase7_profile_resource_20260928_learning_context_clarification_resume_v2.json).

The subsequent missing-world response increment preserves native
`blocked`/unresolved state and releases a context inquiry without an answer
commitment. The current 74-event replay has **54 replies / 7 errors / 13
authorized silences**, authority **74/74**, grounding F1 **0.592**, and no
Phase 4 promotions. The connected-profile run is deterministic but exceeds
the absolute RSS and event-latency targets (**107,048,960 bytes; 152.13 ms**).
The fresh blinded packet joins the current target **74/74**, but both human
reference classes are still missing. See [latest replay](../../../evaluation/reports/phase8_corpus_report_20260928_missing_world_clarification_v1.json),
[current execution record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md#graph-selected-missing-world-context-inquiry--2026-09-28),
[resource report](../../../evaluation/reports/phase7_profile_resource_20260928_missing_world_clarification_v1.json),
and [current packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_missing_world_clarification_v1.json).

The latest replay additionally releases a context clarification for a
declarative, graph-typed selected-learning request, keeping native `learn`,
source-unselected status, and no answer authority. This reduces Phase 8
diagnostic errors to **6** (with **55** released replies); overall disposition
authority remains **74/74**. The full corpus-runner and comparative artifact
test batch passes **51/51**. Connected-profile absolute RSS still exceeds the
limit (**107,429,888 bytes**), and Phase 4 has no complete/promoted tuple.
Current evidence: [replay](../../../evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v1.json),
[resource profile](../../../evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_v1.json),
[blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v1.json).

The request lookup now uses message-local `for_event` adjacency. A semantic
replay comparison shows all 74 replies/dispositions/releases/forces/grounding
values unchanged. The latest connected profile repeats deterministically at
**123.41 ms** maximum latency and **107,139,072-byte** absolute RSS; latency
passes but memory remains over the bound. The latest unscored packet was
refreshed to this exact replay and joins **74/74**. See [repeat report](../../../evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v2.json),
[resource recheck](../../../evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_v2.json),
and [current packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v2.json).

A separate fresh-process, single-run profile confirms the absolute RSS gate is
still exceeded (**106,942,464 bytes**) even without same-process replay
retention; max latency is **147.22 ms** and selection/error checks pass. A
20-module prewarm trim (plus five late imports) preserved all 74 stable
observations but raised RSS in two fresh runs, so it was reverted. The exact
current profile evidence is [here](../../../evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_single_v1.json).

#### Ordinary topic-grounded polar control — 2026-09-28

The named-topic control exposed that the generic selected-concept answer
could claim a polar question before relation support arbitration. Generic
selected-concept answers now exclude polar-relation interpretations, while
the native missing-relation-support rule handles these requests directly.
With a held answer that the gate is open, “Is the gate open?” now selects
native `repair` and `ask_back`, not the topic sentence; supported proposition
polar answers remain on their separate evidence-bound path. The two direct
native support/repair checks and this corpus-prelude control pass **3/3**.
The full-corpus audit narrowed the repair rule: it now requires either a
same-event `answer_topic` goal or a matching supported topic-answer candidate.
This preserves independently selected weather, blocked-permission, and
fragment outcomes while preventing a topic sentence from answering an
unsupported polar relation. Focused regression checks pass **3/3**. The fresh
[scoped-repair Phase 8 report](../../../evaluation/reports/phase8_corpus_report_20260928_polar_relation_scoped_repair_v1.json)
remains blocked with authority **73/74**, grounding F1 **0.571** (20 TP / 30
FN / 0 FP), **55** substantive releases, **5** errors, **14** authorized
silences, and **0/3** complete/promoted Phase 4 tuples. Its only reply/state/
grounding projection difference from the preceding polar-answer-plan replay
is `blocked_permission` grounding now explicitly `authority_missing` (still
correctly blocked). Human-reference, corpus-label, resource/performance,
production-envelope, and Phase 4 exit gates remain open.
After this scope correction, the complete native arbitration suite passes
**48/48** (**567.80 s**) and the complete Phase 8 corpus-runner suite passes
**35/35** (**157.04 s**). `git diff --check` and seed JSON validation pass.

#### Current-tree connected-profile resource recheck — 2026-09-28

Three fresh all-event runs with `PYTHONMALLOC=malloc`,
`MALLOC_ARENA_MAX=1`, and `MALLOC_TRIM_THRESHOLD_=32768` select the same 96
conversation seeds, produce zero errors, and have byte-equivalent stable
observation records. Peak RSS is **104,366,080 / 104,554,496 / 104,448,000
bytes** (all below the 104,857,600-byte 100 MiB limit); maximum event latency
is **128.89 / 147.36 / 146.52 ms** (all below 150 ms). A fresh default-
allocator run preserves full selection and zero errors and measures **136.88
ms** maximum latency, but reaches **106,774,528 bytes**, exceeding the RSS
limit. Thus the connected-profile envelope passes repeatably under the
documented allocator configuration but the default-process RSS and portable
resource gate remain open. Reports: [allocator runs 1](../../../evaluation/reports/phase7_profile_resource_20260928_scoped_polar_repair_current_v1.json), [2](../../../evaluation/reports/phase7_profile_resource_20260928_scoped_polar_repair_current_v2.json), [3](../../../evaluation/reports/phase7_profile_resource_20260928_scoped_polar_repair_current_v3.json), and [default allocator](../../../evaluation/reports/phase7_profile_resource_20260928_scoped_polar_repair_default_allocator_v1.json).

#### Current matched-context blinded packet refresh — 2026-09-28

The current 74-event target was rerun under the required
`phase8a-fixed-phase0-corpus-v5-event-context-history8` protocol and joined
to the existing matched-context ELIZA, Gemma 3 4B, and Qwen 3.5 9B runs. The
fresh blinded packet contains **74 cases / 370 response annotations** across
five model tracks. The two small-LLM runs and two modern-LLM runs each have
identical outputs under the packet builder; packet contract tests pass **4/4**.
The packet is deliberately **unscored** and contains no human tracks, so it
does not close comparative evaluation. Private alias provenance is kept in a
separate key. See [matched target](../../../evaluation/reports/phase8_corpus_report_20260928_scoped_polar_repair_v5_current.json), [rater packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_scoped_polar_repair_v1.json), and [private key](../../../evaluation/reports/phase8_blinded_output_key_20260928_scoped_polar_repair_v1.json).

#### Current v5 grounding false-negative provenance audit — 2026-09-28

The current matched-context report's **30** referent-grounding false
negatives partition into **13** events annotated only by unverified discourse
state, **7** by an unverified graph-path declaration, **9** by surface or
uncertainty-only cues, and **1** source-attribution case. In the last case,
the graph has an explicit `ReportedContentEvidence` path and correctly answers
what the monitor reported, but the evidence establishes attribution rather
than truth of the reported proposition; current grounding remains unresolved.
Two permission questions are correctly `authority_missing`/blocked despite
their broad corpus label `grounded`. The audit therefore does not justify
weakening the evidence boundary or promoting labels into runtime facts. The
remaining cognition work is to obtain case-bound evidence/adjudication for
these declarations, not add a broad adapter heuristic. Source report:
[matched-context Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_scoped_polar_repair_v5_current.json).

#### Full-seed daemon-profile resource recheck — 2026-09-28

The checked-in `deploy/jabberwock.service` explicitly starts
`scripts/jabberwock_daemon.py --seeds full`, while the daemon's own default is
the connected `conversation` profile. Replaying all 74 events with the
service's explicit full profile on the current tree completes with zero
errors, but full-seed loading peaks at **1,450,897,408 bytes RSS** after
**13.75 s** boot, then settles to **344,903,680 bytes**; maximum event latency
is **226.51 ms**. This fails the documented <100 MiB / <150 ms envelope by a
wide margin. The service template has an existing checkpoint directory, so
changing only `--seeds` would not constrain resumed graphs; a deployment fix
must define and enforce profile identity across checkpoint resume before
claiming the conversation profile as the deployed resource envelope. Report:
[full-seed current-tree profile](../../../evaluation/reports/phase7_profile_resource_20260928_scoped_polar_repair_fullboot_current_v1.json).

**Superseded checkout-state note:** a later same-day source review found that
the checked-in unit had since changed to `--seeds conversation` with a
dedicated checkpoint directory and strict seed-profile checkpoint guards.
The full-seed report above remains valid for the earlier service-equivalent
configuration, but its statement about the then-current unit no longer
describes this checkout. The installed user unit/activation state remains
unverified because the user systemd bus is inaccessible in this environment;
see the later service-template review in the canonical execution plan.

#### Daemon-ingress shadow-read resource isolation — 2026-09-28

Extended the Phase 7 daemon-ingress harness with an explicit shadow/deep-ingest
mode matching the daemon's post-boot switch. The full 74-event conversation
profile with shadow-read **on** (the daemon default) peaks at **270,077,952
bytes** and first-event ingress reaches **2,415.06 ms** while loading the
NLTK deep-reader path; native cycle max is **55.71 ms**. With shadow/deep-ingest
off, ingress max is **21.34 ms** and native-cycle max **48.09 ms**, but RSS is
still **106,700,800 bytes**, above the 100 MiB cap. Both traces have 74
interpretations, 57 authoritative dispositions, and one pending turn in this
single-quantum, no-host-action measurement; neither proves a completed daemon
conversation run. The daemon-ingress suite passes **8/8** after the harness
extension. This rules out turning on the shadow path in a resource-limited
deployment without additional optimization and keeps the full daemon resource
gate open. Reports: [shadow on](../../../evaluation/reports/phase7_daemon_ingress_20260928_shadow_read_resource_configured_v1.json), [shadow off](../../../evaluation/reports/phase7_daemon_ingress_20260928_shadow_read_off_resource_configured_v1.json).

#### Daemon shadow-read default and process-level RSS — 2026-09-28

Shadow/deep-ingest is now explicitly opt-in (`--shadow-read`); no flag means
off. With the configured allocator and a fresh actual `--once` conversation
daemon, `/usr/bin/time -v` records **106,980 KiB / 109,547,520 bytes** peak
RSS against the **104,857,600-byte** cap, a **4,689,920-byte** overrun.
The run selected all **74/74** connected seeds and wrote a strict-profile
checkpoint. An alternate glibc threshold trial measured **107,316 KiB**, so
that tuning was rejected. This resolves shadow-read's unsafe default, not the
daemon RSS gate; the service profile has not been migrated. Report:
[fresh one-shot daemon](../../../evaluation/reports/phase7_daemon_oneshot_20260928_conversation_shadow_off_v1.json).

#### Daemon resident-memory settling and retained-graph census — 2026-09-28

The fresh connected-profile daemon settles to **101,840 KiB** RSS 0.5 s after
coming online—only **573,440 bytes** under the 100 MiB cap—after a **106,980
KiB** startup high-water. The 74-event single-quantum ingress run peaks at
**106,700,800 bytes**, so settled boot RSS does not close the gate. Its
instrumented **1,478**-node growth is led by `Mention` **314**, `Message`
**270**, `Intent` **186**, `Unknown` **112**, and `UnderstandingCheck` **82**;
`CommunicationInterpretation`, `DiscourseEvent`, and `Episode` each add 74.
The run completes **73/74** turns and uses no host actions. Treat the type
census as diagnostic only: deleting epistemic/discourse nodes based on type
counts would violate the retention contract until ownership and reachability
are shown safe. Next inspect those links and terminalized-turn lifetimes before
choosing a compaction target. Evidence: [live smaps](../../../evaluation/reports/phase7_daemon_live_smaps_20260928_conversation_shadow_off_v1.json),
[graph census](../../../evaluation/reports/phase7_daemon_ingress_20260928_graph_type_census_v1.json).

#### Daemon checkpoint seed-profile identity guard — 2026-09-28

Fresh daemon graphs now store a `DaemonSeedProfile` marker inside the saved
graph. Resume rejects an explicitly mismatched marker and refuses to fall back
to a potentially stale older graph after encountering a newer mismatched
checkpoint. The opt-in `--strict-seed-profile-checkpoints` mode rejects
unmarked legacy snapshots; default compatibility mode warns, permits the
legacy resume, and deliberately leaves it unmarked so it cannot be mistaken
for a verified profile later. The daemon test module passes **20/20** with its
one socket-binding HTTP case excluded (sandbox permission denied); focused
marker serialization/profile-guard tests pass **6/6**. Existing checkpoints
are not rewritten or deleted, and the
systemd service still selects `full` without strict mode. A profile migration
and production-shaped bounded-resource service run are still required; the
resource gate remains open.

#### Bind legacy message episodes to their source — 2026-09-28

The type-level link audit found that all 74 legacy `Episode` nodes were owned
by the `Agent` but not linked back to the `Message` that created them. This
made replay traces lack source-utterance provenance. `memory_core` is now
v1.2.0; its native message-episode rule declares and adds
`recorded_from_message`, and daemon resume refreshes that changed rule body.
Regression evidence: the 74-event census reports **74/74** episodes bound to
messages; episodic-memory tests pass **15/15**, and profile/reconciliation
tests pass **4/4**. The ordinary ingress replay still peaks at **106,643,456
bytes**, leaves **1** turn pending, and dispatches no host actions: resource
acceptance and full-turn completion remain open. Reports: [source-bound
census](../../../evaluation/reports/phase7_daemon_ingress_20260928_graph_type_census_v3_memory_provenance.json),
[ordinary replay](../../../evaluation/reports/phase7_daemon_ingress_20260928_memory_core_provenance_v1.json).

#### Resume audit: terminality and held-answer authority boundary — 2026-09-28

Rechecked the current Phase 8 matched-context report and the 74-event daemon
census before selecting another cognition change. The sole single-quantum
pending event is `info_unknown`, marked `graph_outcome: expected`; its
unresolved state is not a turn-completion bug to be forced into a reply. The
census also shows that retained `Unknown` nodes are connected to `Intent`
nodes, so node-type counts alone do not justify pruning. The `info_status`
held-answer path has supported topic-grounding evidence and a production
receipt, but no native selected candidate or complete Phase 4 tuple; it remains
non-authoritative as a deliberative disposition. No missing value, cost,
consequence, or novelty evidence was inferred from the receipt. Focused Phase
8 audit/packet, daemon ingress, and episodic-memory regressions pass **67/67**.
The cognition/grounding, resource, and comparative-human gates remain open.

#### Native authority for event-bound held-topic answers — 2026-09-28

Follow-up established that `info_status`'s answer was supported by an exact
event-bound `answer_topic` Goal and a matching supported
`HeldAnswer -grounded_by-> TopicGroundingEvidence` path; arbitration had only
recognized the legacy `comp_know_concept` field for ordinary information
questions. `communication_intent_arbitration` v1.4.7 now selects native
`answer` only from that same-event graph evidence, excluding polar questions
and explicit missing relation support. Both held-answer and grounding-evidence
paths must be non-null and non-empty. Daemon rule reconciliation refreshes
this seed on checkpoint resume.

The fresh Phase 8 v5 replay raises disposition authority to **74/74** and
state matches to **74/74**. A normalized comparison against the prior report
shows `info_status` is the only changed case; its reply (`nominal`) and
grounding status are unchanged. Final-body rule selection/guard tests pass
**5/5**, and checkpoint refresh passes **1/1**. The broader arbitration plus
daemon regression run is **77 passed**;
the sole failure is the known sandbox `EPERM` on the HTTP socket-binding test.
Grounding remains **20/50 TP (F1 0.571)** and Phase 4 remains **3 sources / 0
complete / 0 promoted**; comparative, cognition-quality, and resource gates
remain open. See [final Phase 8 replay](../../../evaluation/reports/phase8_corpus_report_20260928_event_bound_topic_answer_native_v2.json)
and the [canonical plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

#### Connected content pre-pass audit — 2026-09-28

The user-proposed seed-connected loading map is partly implemented: the
source-validated pre-pass caches typed providers, groups, connection and
dependency closure, plus candidate-to-provider mappings; a sealed profile can
preload a complete candidate set and decline out-of-set lazy loads. The live
daemon currently supplies no complete finite vocabulary at boot, so it keeps
incremental per-turn closure. Eagerly substituting full-seed loading is not
resource-safe (the measured full profile peaks at **1.45 GB**); non-lazy live
loading still needs a bounded, authoritative boot-time content source and
matched parity/resource evidence.

#### Connected pre-pass checkpoint-resume repair — 2026-09-28

The adapter's incremental content-selection cache was session-only while the
daemon resumed only the graph, so resumed conversation checkpoints silently
lost provider/content-load state. `WorldAdapter.save()` now persists compact
stable state (selective-provider loaded names only); incremental provider
caches are re-resolved against the current validated seed index after resume.
`load()` restores this state. For older snapshots,
rehydration is allowed only with an unambiguous conversation profile marker;
it conservatively uses graph-resident `SeedSummary` IDs and current manifests
to continue incremental closure. Current and simulated legacy checkpoint
roundtrips both load a new `valley` candidate successfully. Seed-loader and
daemon-checkpoint regressions pass **49 tests**, excluding the sandbox-denied
HTTP socket-binding case. Resource acceptance and profile migration remain
open; this fix restores cognition/content loading after restart but does not
bound process RSS.

#### High-volume graph retention provenance audit — 2026-09-28

Added a bounded read-only neighbor/identity window to the Phase 7 graph-type
census so counts alone are not used to choose pruning targets. In the
74-event replay, sampled `Unknown` nodes are named `speaker_of_message`, have
`unknown_kind: speaker`, and are linked from `Intent` nodes; they are not
isolated. Sampled `Episode` nodes link to their source `Message` and are
agent-owned. Two runs produced the same canonical observation hash
`3d70229f7948abb39f59a2722de4cbabcb2c872c541bcfb3d8ee30e2c6183dcd`;
`tests/test_phase7_daemon_ingress_envelope.py` passes **9/9**. This establishes
graph adjacency/provenance for representative samples, not safe deletion or
compaction for any class. The instrumented run peaks at **107,495,424 bytes**
RSS and leaves one turn pending under single-quantum/no-host-action mode, so
resource and end-to-end terminality gates remain open. Report:
[`phase7_daemon_ingress_20260928_retention_provenance_v2.json`](../../../evaluation/reports/phase7_daemon_ingress_20260928_retention_provenance_v2.json).

#### Python optimized-mode daemon RSS check — 2026-09-28

An actual fresh daemon `--once` boot under `PYTHONOPTIMIZE=2`, the conversation
profile, strict checkpoint validation, shadow-read off, and the configured
glibc allocator selected **74/74** connected seeds and completed successfully.
GNU time measured **107,672 KiB / 110,256,128 bytes** peak RSS, **5,398,528
bytes** above the 100 MiB cap. The prior unoptimized process report measured
**106,980 KiB**, but this was not a paired repeated experiment; the only firm
conclusion is that optimized mode does not produce an accepted resource run.
Do not adopt it without semantic parity and repeated resource evidence. The
systemd template still selects `full`; migration of existing checkpoints,
absolute RSS, cognition/production, and human comparative gates remain open.
Report:
[`phase7_daemon_oneshot_20260928_python_optimize2_v1.json`](../../../evaluation/reports/phase7_daemon_oneshot_20260928_python_optimize2_v1.json).

#### User-amended RSS ceiling — 2026-09-28

The active absolute/growth RSS ceiling is now **150 MiB (157,286,400 bytes)**
at the user's direction. Phase 7 production and semantic-event envelopes,
native-cycle measurement, daemon-ingress acceptance, and the post-turn heap
trim trigger now agree on this value; prior reports retain their original
100 MiB metadata as historical evidence. A cross-envelope regression checks
the shared effective threshold. Focused resource-cap/native-cycle checks and
daemon-ingress/resource regressions pass **10/10**. The wider four-module
regression run initially found that `_QDAdapter` bypassed the base
`WorldAdapter` initializer that creates the inherited method-serialization
lock. After initializing that required re-entrant lock in the adapter, the
full production, semantic-event, native-cycle, and daemon-ingress test set
passes **74/74** under the new threshold.

Fresh 74-event instrumented daemon ingress peaks at **119,652,352 bytes** with
the new limit explicitly recorded as **157,286,400 bytes**; ingress/native
cycle maxima are **17.53/58.49 ms**. This run is signal-only/no-host-action
and leaves one turn pending, so it does not prove full-turn completion. The
systemd service still requests `full`, whose measured boot peak is
**1,450,897,408 bytes**, well above even the revised budget. Report:
[`phase7_daemon_ingress_20260928_cap150_v2.json`](../../../evaluation/reports/phase7_daemon_ingress_20260928_cap150_v2.json).

#### Current blinded packet rating forms — 2026-09-28

Generated current-digest blank forms for two independent raters from the
74-case / 370-row Phase 8A packet. Both forms share its exact SHA-256, have
distinct blinded rater IDs, and keep all five dimension scores blank; the
private alias key is not in either form. Packet and annotation-adjudication
contracts pass **8/8**, with direct checks for row count, digest, distinct
IDs, and blank scores. This removes the stale-template operational gap, but
the comparative gate remains unscored pending independent human annotations,
adjudication, rubric approval, and unblinding after lock. Current files:
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_event_bound_topic_answer_native_v2_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_event_bound_topic_answer_native_v2_b.json).

#### Reflective self-model answer authority — 2026-09-28

Exact self-model rule questions now have a same-event `ReflectiveAnswerEvidence`
link to the exact matching `RuleSummary` node set. Seeded arbitration—not the
adapter renderer—sets the `answer` disposition and mints the
`native_reflective_answer_plan=self_model_rule` reply. Before release, the
adapter verifies that the exact query still resolves to precisely the linked
summary set and passes the rendered answer through the existing production
readback gate. The interpretation records the support path as
`CommunicationInterpretation -> ReflectiveAnswerEvidence -> RuleSummary`.
The conversation regression requires support links, native disposition/basis,
the graph reply plan, and an event-bound released receipt.

An adjacent gap was exposed: “Why did the alarm trigger?” had a native `learn`
disposition because causal evidence was missing, but a generic learning
clarifier asked the user to supply context. The adapter now preserves the
native learning state but fails closed to the explicit error surface when
`relation_focus=reason`, `relation_support=missing`, and the native basis is
`missing_causal_relation_evidence`. The two affected regressions pass on
current code (**2/2**). Their prior focused suite had **96 passes and this one
failure**; those 96 were not rerun after the narrow fail-closed guard. These
changes close neither the full-boot resource gate nor the independent human
comparative evaluation, and do not claim overall cognition acceptance.

#### Absent-faculty graph value and Phase 8 recheck — 2026-09-28

The first 74-event replay after the reflective-answer and causal fail-closed
changes revealed that an unselected reflective faculty was recorded as an
empty string, while native polar-repair predicates check for `null`. This
representation mismatch prevented the anaphoric polar rule from selecting
repair. The adapter now records absent faculty as graph `null`. Three focused
regressions pass (**3/3**), including the event-bound native rule-answer
receipt and both unsupported-relation cases; the supported-proposition polar
answer control passes separately (**1/1**).

Current Phase 8 recheck restores authority to **74/74** and only changes the
anaphoric polar case from error to a released native repair. Corpus totals are
**66/74** fixture-state matches, grounding **20/50 TP, 30 FN, 0 FP (F1 0.571)**,
**54** substantive releases / **6** explicit errors / **14** authorized
silences / **0** unclassified, Phase 4 **3/0/0**, and
**104.15/177.02/230.34 ms** median/p95/max (**14/74** over 150 ms). The report
remains blocked at comparative provenance; human annotations, Phase 4 tuple
producers, grounding coverage, latency, and full-boot resource acceptance are
still open:
[`reflective/fail-closed Phase 8 v2`](../../../evaluation/reports/phase8_corpus_report_20260928_reflective_answer_failclosed_v2.json).
The complete Phase 8 runner test module passes **35/35** in **140.35 s** on
this current tree.

#### Settled-pass short circuit — 2026-09-28

Profiled the exact `Reset that device.` repair path: the bounded polar loop
applied **16, 2, 0, 0** native rules before the change. It now exits after the
first zero-application pass because another identical quantum has no changed
graph state to act on. The Phase 8 runner module passes **35/35** after the
change, and replayed semantic observations match the preceding report exactly
apart from timing. The new report retains **74/74** authority, **66/74** fixture
agreement, **20 TP / 30 FN / 0 FP** grounding, release counts **54/6/14/0**,
and Phase 4 counts **3/0/0**. Latency evidence is mixed: aggregate
median/p95/max are **103.53/169.51/208.07 ms**, but over-150 ms turns rose from
**14/74 to 16/74**, and the target event's measured time rose from **166.75 to
193.79 ms**. This is a safe no-op pass elimination, not a closed performance
gate. Remaining acceptance gaps include latency, grounding, complete Phase 4
tuples, external blinded ratings/adjudication, and full-boot resource budget.
Evidence: [early-stop Phase 8 replay](../../../evaluation/reports/phase8_corpus_report_20260928_polar_early_stop_v1.json).

#### Current replay: unsupported sensor-report label and absent causal source — 2026-09-28

Read the `question_response` and `info_explanation` traces in the fresh
early-stop report. For `Did the sensor report it?`, the trace has current topic
`gate`, no selected candidate, and no answer commitment; no sensor-report
event or resolving antecedent is supplied. The runtime's repair is therefore
evidence-constrained, while the fixture's `expected_state=answer` still needs
independent adjudication. For `Why did the alarm trigger?`, native disposition
remains `learn` but the corpus graph has no causal source; the generic explicit
error remains fail-closed, not an answer. No fixture label, graph evidence, or
answer authority was changed. This confirms the next step is evidence-backed
case/rubric adjudication or a supported source input, not a rule that releases
an unsupported answer. See [fresh trace report](../../../evaluation/reports/phase8_corpus_report_20260928_polar_early_stop_v1.json)
and [Phase 0 fixture](../../../tests/fixtures/conversational_manifold/phase0_events.json).

#### Causal-answer positive control exposes missing realization path — 2026-09-28

Ran the missing-cause native repair tests together with the explicit reason
question positive control: **2 pass, 1 fails**. Both repair routes release a
graph-linked, production-gated request for event/evidence. The positive control
preloads a single typed `cause -causal_influence-> alarm` edge; the
interpretation reads `relation_support=supported`, but no released answer
message/commitment is produced. This is distinct from the Phase 8 alarm case,
which has no causal edge and correctly remains fail-closed. Next, implement the
missing native causal-answer plan and language realization/readback for the
supported case; preserve no-answer behavior for absent or ambiguous causal
evidence. Do not relax the regression. Evidence:
`tests/test_action_evidence_and_defer.py::test_explicit_reason_question_requires_a_graph_causal_relation`,
`tests/test_phase6_information_production_bridge.py::test_native_causal_repair_asks_for_missing_event_evidence`, and
`tests/test_phase6_information_production_bridge.py::test_full_corpus_context_releases_native_causal_repair_before_generic_askback`.

#### Unique supported-cause plan and production readback — 2026-09-28

Implemented the missing supported causal answer. Reason grounding now checks
incoming causes only; native arbitration selects `answer` only for exactly one
event-matched cause edge and mints a typed `CausalRelationAnswerPlan` plus a
same-event graph answer Message. English realization occurs after selection;
readback verifies the unique live cause edge and selected plan, then records a
production receipt releasing both the plan and realized Message. The turn
trace requires the event-bound receipt, answer surface, graph edge, and plan.
No/incoming cause, outgoing-only influence, or multiple causes do not produce
answer authority. Focused causal tests pass **10/10**, missing-cause repair
controls **3/3**, and the complete Phase 8 corpus-runner module **35/35**. The
fresh [74-event replay](../../../evaluation/reports/phase8_corpus_report_20260928_causal_answer_plan_v1.json)
preserves the previous semantic observation projection and aggregate totals:
authority **74/74**, grounding **20/30/0 (F1 0.571)**, production **54/6/14/0**,
and Phase 4 **3/0/0**. Latency is **107.28/178.31/202.71 ms** median/p95/max,
with **13/74** over 150 ms; no performance improvement is claimed. Native
selection is language-neutral, while realization currently has English
coverage only. Comparative provenance, case adjudication, complete Phase 4
tuples, full resource acceptance, and broader production/latency gates remain
open.

#### Connected conversation profile: three fresh resource runs — 2026-09-28

Measured the current incremental connected-content profile in three separate
fresh processes over all 74 events. Each run selected the complete seed set,
reported zero errors, and accounted for all events as **54 substantive / 6
explicit-error / 14 authorized-silence** outcomes. RSS peaks: **136,904,704 /
135,426,048 / 137,072,640 bytes**, all within **157,286,400 bytes**. Maximum
event latencies: **140.32 / 147.46 / 156.46 ms**; one run exceeds 150 ms, so
the strict latency gate is not repeatable. A separate connected-profile
two-replay determinism run matches across the full corpus, but reports a
154.22-ms max. This evidence closes only the connected-profile RSS and
terminality slices; deployment remains open because the service unit still
uses `--seeds full` (measured **1,450,897,408-byte** peak) and does not enable
strict profile/checkpoint enforcement. No systemd template or persisted
checkpoint was changed. Reports: [fresh run 1](../../../evaluation/reports/phase7_profile_resource_20260928_causal_answer_connected_fresh_v1.json),
[fresh run 2](../../../evaluation/reports/phase7_profile_resource_20260928_causal_answer_connected_fresh_v2.json),
[fresh run 3](../../../evaluation/reports/phase7_profile_resource_20260928_causal_answer_connected_fresh_v3.json),
[determinism replay](../../../evaluation/reports/phase7_profile_resource_20260928_causal_answer_connected_replay_v1.json).

#### Offline retrieval-miss completion of the connected daemon replay — 2026-09-28

Extended the daemon-ingress envelope with an explicit `offline_miss` retrieval
fixture, allowed only when host actions are drained. The fixture makes topic
grounding return no result and audits HTTP requests, so it tests terminal
repair/error behavior without external retrieval. Two independent fresh
74-event runs produce the same canonical observation digest; each selects the
complete seed closure, terminalizes **74/74** turns (**38** released replies,
**34** explicit errors, **2** expected no-response outcomes), drains all **11**
host actions and leaves zero pending turns/search/ground requests. The
`info_unknown` turn closes through its graph-selected repair receipt, while
`question_source` retains the attributed reported-content receipt. Both runs
make **zero** external HTTP requests and remain under the amended **150 MiB**
RSS cap (**136,982,528 / 137,101,312 bytes**); max native-cycle latency is
**88.02 / 94.46 ms** and ingress latency **16.54 / 18.80 ms**. The focused
daemon-envelope suite passes **12/12**. This closes connected-profile offline
host-action terminality and repeatability only; it does not establish retrieval
success, broad product-quality parity, or deployment/service acceptance.
Evidence: [run 1](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_v1.json),
[run 2](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_v2.json).

#### Current gate evidence update — 2026-09-28

The async `question_referent` direct supported-held-answer bridge is recorded
in the execution plan with repeatable full-daemon evidence. The fresh Phase 8
revalidation preserves the synchronous metrics: authority **74/74**, grounding
**20 TP / 30 FN / 0 FP (F1 0.571)**, production **55 released / 5 errors / 14
authorized silences**, Phase 4 **3 sources / 0 complete tuples / 0 promotions**.
A separate current-tree teacher/interference/repeat probe scores **5/5
learning and 5/5 delayed memory** over five topics, with graph-supported
answer commitments and release receipts. This bounded result does not supply
human/model comparative scores or close corpus cognition gaps. Evidence:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_daemon_direct_held_answer_current_v1.json),
[learning/memory probe](../../../evaluation/reports/phase8_memory_learning_probe_20260928_current_v1.json).

#### Latency investigation — 2026-09-28

Full-seed Phase 8 timing is still above the 150-ms max gate (**105.88/176.88/
205.77 ms** median/p95/max; **15/74** over). Per-turn profiling points to
repeated native rules passes and reply self-monitor conceptualization, not just
seed loading. A one-round experiment preserved measured outcomes but worsened
one-run latency (**113.80/194.79/240.70 ms**, **20/74** over), so it was
rejected. No monitor or latency target was weakened; next optimization should
reduce real native/graph work and revalidate complete outputs.

#### Latest async production-parity increment — 2026-09-28

The async reply dispatcher now releases the native
`supported_selected_concept_answer` path for `question_referent` from its
same-turn supported `HeldAnswer` and exact concept grounding, through the
existing conversation production gate. It requires native answer disposition
and exact arbitration basis; no reply text is used as grounding. The direct
candidate is bound to the released surface and same-event error-floor
candidates are suppressed. Regression plus full daemon ingress tests pass
**18/18**. Fresh 74-event offline-miss runs v11/v12 match at digest
`935bdff9d6b75c89e80fecaf6dc68648b7506693ca3e3f5417d8f143995d668a` and
**48 released / 13 explicit errors / 13 authorized no-response**. All host
actions drain, HTTP count is zero, and 150 MiB assertions pass; peak RSS is
**137,916,416 / 138,006,528 bytes**, completion max **84.00 / 122.36 ms**.
Production parity is improved but still open; see execution-plan evidence links
for the remaining explicit-error list and reports.

#### Full-corpus gate recheck — 2026-09-28

The fresh exact-tree Phase 8 replay confirms the daemon-only change preserves
the synchronous fixed-corpus state: disposition authority **74/74**, grounding
**20 TP / 30 FN / 0 FP (F1 0.571)**, production **55 released / 5 explicit
errors / 14 authorized silences**, and Phase 4 **3 sources / 0 complete
tuples / 0 promotions**. The cognition and comparative release gates remain
open. See the linked report in the execution plan.

#### Async context and unresolved-reference reply parity — 2026-09-28

The daemon now releases native-selected clarification for unsupported
decision-context questions, graph-selected learning with unresolved selection
focus, and turn-compatible unresolved-reference repair. These use the existing
ask-back faculty and production gate; answer commitment remains absent. The
non-turn repair continuation and missing-disposition permission case remain
errors. Daemon ingress tests pass **19/19**. Fresh full-corpus runs v15/v16
match at digest
`d1cee4583be4de55ed993c37cda2beaf1cfa664b67837d21075bad7073c33bb2` and yield
**52 released / 9 errors / 13 authorized no-response**, with all 11 host
actions drained, no HTTP, resource checks passing, peak RSS **138,043,392 /
138,166,272 bytes**, and max completion latency **105.91 / 85.73 ms**. Remaining
production parity, synchronous latency, cognition, and comparative gates are
open. Full details and reports are in the execution plan.

#### Non-turn continuation repair terminality — 2026-09-28

`repair_missing` now completes as native authorized defer when the graph has
`grounding_failure` + `repair_or_defer` / `clarify_or_defer`,
`knowledge_deficit` focused on information, and `non_turn` continuation
metadata. This is not a general no-disposition fallback; `blocked_permission`
remains an error. Daemon-ingress tests pass **19/19**. Two repeatable 74-event
offline-miss runs v17/v18 produce **52 replies / 8 errors / 14 authorized
no-replies**, with digest
`d9788958a79e58f1553d634b98b61924e2d57d71a3bfa0c7b188a7cfdc90323a`. They
drain all 11 host actions, perform zero HTTP, pass the resource assertions, and
peak at **137,986,048 / 138,149,888 bytes** with max completion latency
**85.71 / 137.75 ms**. Remaining project gates are open; details are linked in
the execution plan.

#### Unresolved standalone action clarification and parity — 2026-09-28

For `unknown_action` and `action_unknown`, native `repair_or_defer` plus
`clarify_or_defer` now licenses only an ask-back. The event receives a
graph-linked clarification commitment and production receipt; no action is
executed. `repair_missing` remains a non-turn silence, and missing-disposition
permission remains an error. Focused controls pass **3/3**; daemon ingress
passes **20/20**. Two full replays v19/v20 match at digest
`6abfa9789cd8b6c2390e4121701caaed590e46ceb201de039a845c915e83d0af` and yield
**54 released / 6 errors / 14 authorized no-response**. Against synchronous
Phase 8, only the release of non-turn `repair_missing` differs; host actions,
HTTP, memory, and latency checks pass. Full resource/performance values and
report links are recorded in the execution plan.

#### Daemon terminalizes native no-reply dispositions — 2026-09-28

The async daemon previously converted native `defer` for overlap/continuation
fragments, incomplete non-turn offers, and blocked non-turns into the generic
error floor, unlike the synchronous path. Its response dispatcher now reads
the same persisted native disposition and typed interaction boundary, suppresses
only that event's outbound floor, and records an empty graph-bound reply
surface. `graph_turn_reply_expectation()` reports `not_expected` for those
states. It does not infer silence when no native disposition exists:
`blocked_permission` remains an explicit-error negative control. Focused
positive/negative cases pass **3/3**; the full daemon-ingress suite passes
**14/14**.

Two fresh 74-event offline-miss daemon runs have identical canonical semantic
digests and terminalize all turns, draining all 11 host actions with zero HTTP
requests. Both report **37 released / 24 error / 13 authorized no-response**;
21 errors are explicit diagnostic surfaces. Relative to the previous **38 / 34
/ 2** split, 11 error terminalizations became authorized silence, with one
fewer released reply. Peak RSS is **137,539,584 / 137,596,928 bytes** under
the amended cap; maximum turn completion is **84.10 / 88.44 ms**. Remaining
errors include sync-path response faculties not yet bridged through async
ingress; this does not close daemon production parity or justify switching
the checked-in full-seed service template. Evidence:
[run 3](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_v3.json),
[run 4](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_v4.json).

#### Fresh 74-event connected-profile resource and latency replay — 2026-09-28

Two independent fresh processes replayed the full fixed corpus under the
connected conversation profile with `batch_before_boot` content/dependency
selection. Both selected the complete **96-seed** closure with no unresolved
content/dependency items, zero runtime exceptions, and all RSS assertions
passing. Peak RSS was **111,300,608 / 111,366,144 bytes**; boot-plus-event
growth was **84,209,664 / 84,271,104 bytes**, below the amended
**157,286,400-byte** ceiling. Median/p95/max turn latency was
**53.97/97.57/115.47 ms** and **49.99/114.17/138.73 ms**. Normalized semantic,
message, turn, receipt, and release observations match byte-for-byte across
processes. Both results contain 55 released replies, 5 explicit diagnostic
errors, 14 authorized silences, and no runtime exceptions. Reports:
[run 1](../../../evaluation/reports/phase7_connected_full_corpus_current_v1_20260928.json),
[run 2](../../../evaluation/reports/phase7_connected_full_corpus_current_v2_20260928.json).
The connected fixed-corpus memory and 150-ms turn-latency slice now passes;
fast-reflex timing, full-seed deployed-service RSS, production-profile
selection, corpus adjudication, and comparative evaluation remain open.

#### Operator-supplied sealed content pre-pass — 2026-09-28

The conversation daemon now accepts an optional versioned content manifest
(`--conversation-content-manifest`) containing lexical candidates, exact keys,
and/or seed-scoped typed refs. The profile canonicalizes the selection and
records its SHA-256 identity in checkpoint state; a checkpoint with a different
manifest digest is refused rather than reused or silently replaced. No-manifest
startup retains incremental behavior, and no service template or existing
checkpoint was migrated. Focused manifest/parser, actual provider-preloading
and sealed-miss boot, checkpoint round-trip/mismatch, and loader tests pass
**12/12**. This adds reproducible
sealed preloading for known content; arbitrary online candidate discovery,
service profile selection, and broader acceptance gates remain unresolved.

#### Phase 8 grounding-recall source audit — 2026-09-28

Current grounding remains **20 TP / 30 FN / 0 FP**. The report's case-level
runtime-source audit finds **27/30** expected-grounded misses have no
runtime grounding/attributed-source path, **2/30** have only missing
permission-authority paths, and **1/30** has a valid attributed-utterance
source path that supports what was said but not its truth. The latter three
do not warrant a world-grounding positive. This leaves 27 cases for which
case-bound graph evidence or independent Phase 0 annotation review is needed;
no broad status remapping is supported. See the
[current Phase 8 report](../../../evaluation/reports/phase8_corpus_report_20260928_confirmation_source_repair_v2.json)
and [Phase 0 corpus](../../../tests/fixtures/conversational_manifold/phase0_events.json).

#### Native causal cognition for Spanish/Japanese semantic events — 2026-09-28

Added typed `relation_target_ref` evidence to neutral semantic ingress. Only a
unique live graph `Concept` target can be used; incoming causal candidates are
counted from typed graph edges by the adapter, while native rules select the
event-bound answer plan. Missing or ambiguous causes remain `learn`, and a
forged adapter `relation_support` claim is ignored. Spanish and Japanese
provider cases pass through the same live path for no-cause, one-cause, and
ambiguous-cause inputs; only the unique supported graph cause mints a plan.
Focused semantic-frame, bilingual causal, English causal-answer, and Phase 4
evidence regressions pass **6/6**. The Phase 8 fixed-corpus scores are not
claimed to change; multilingual causal surface realization remains open.

#### Current-tree Phase 8 v5 rebaseline after semantic causal ingress — 2026-09-28

The fresh v5 rebaseline preserves **74/74** authoritative dispositions,
grounding **20/30/0 (F1 0.571)**, production **55 released / 5 explicit
errors / 14 authorized silences**, and Phase 4 **3 sources / 0 complete / 0
promotions**. All 74 case-level reply/state/grounding/release projections
match the preceding v5 report after normalizing graph-assigned node IDs. The
release gate remains blocked, and this semantic-event capability does not
alter fixed-corpus cases. Evidence:
[fresh Phase 8 v5 report](../../../evaluation/reports/phase8_corpus_report_20260928_neutral_causal_semantic_events_v5.json).

#### Checkpoint-restored semantic ingress — 2026-09-28

Extended the sealed typed-content pre-pass regression through save/load and
Japanese reason-event ingress. The test exposed two `WorldAdapter.load()`
initialization omissions: the shared reentrant adapter/native lock and the
outbound-message index readiness flag. Restore now rebuilds the shared lock
boundary and starts the derived index as unbuilt. The restored-manifest causal
ingress and bilingual cause-count test pass (**2/2**); profile resume, daemon
checkpoint round-trip, and rule-store checkpoint tests pass (**7/7**). A wider
adapter/persistence batch yielded **44 passed, 1 failed** because the sandbox
denied local socket binding for an HTTP debug-route test; no adapter assertion
failed. These are checkpoint-safety fixes, not evidence that the remaining
corpus-level cognition, production, latency, or comparative gates have closed.

#### Current-tree Phase 4 native-source boundary regression — 2026-09-28

The live evidence-generation, seed-source, and partial-evidence audit suites
pass **12/12**. The current native bridge promotes a complete tuple only from
an approved `ThoughtManifold` source, rejects complete-looking tuples on
generic `Concept` nodes, and preserves explicit `no_candidate` when no
approved source exists. The bridge authority boundary is verified, but Phase 8
still has **0** live complete tuples/promotions; upstream candidate production
remains open.

#### Current-tree cross-language cognition / Phase 4 source recheck — 2026-09-28

The focused current-tree set passes **8/8** across live Spanish/Japanese
semantic-frame ingress, neutral relation-focus transport, graph-supported
named polar answering, confirmation repair, and Phase 4 tuple-source controls.
The seed audit still finds **zero** complete five-dimension tuples and does
not promote production-only near-matches. This is bounded evidence for
language-agnostic evidence transport and preserved graph/native answer
authority, not closure of multilingual deliberation or Phase 4 candidate
production. The latest raw-reference audit has five complete machine runs
(one ELIZA and two each small/modern) but no base- or advanced-human references;
it performs no comparative scoring. Human comparative acceptance therefore
remains open pending approved data and ratings.
Evidence: [latest blinded target packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_confirmation_source_repair_v1.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_confirmation_source_repair_v1.json).

#### `response_yes` action-label provenance — 2026-09-28

Audited the `expected_state=act` / native `defer` mismatch against the current
fixture and Phase 8 trace. The event is labelled acknowledgement, but has no
case-bound offer ID, target, or addressee. The only earlier offer-like event
(`I could—`) is itself an unresolved fragment and deferred; the immediately
preceding event is unrelated. The native trace contains no grounding path,
goal, intent, or production receipt, while the surface parse maps to
`do:proceed`. Keep native action authority fail-closed until the corpus gains
case-bound offer/addressee provenance or the expected state is independently
adjudicated. Evidence: [Phase 8 trace](../../../evaluation/reports/phase8_corpus_report_20260928_confirmation_source_repair_v2.json),
[Phase 0 fixture](../../../tests/fixtures/conversational_manifold/phase0_events.json).

#### Eight Phase 8 expected-state disagreements: evidence, not label authority — 2026-09-28

Audited all eight current expected/native-state disagreements in the current
Phase 8 report. The two ability-offer cases have a grounded typed offer target
and a released social acceptance, but no action-execution goal. The
`question_response` has only discourse-topic grounding, not support for the
asked relation; `question_ack` has no proposition support; `info_choice` is
authority-blocked; `response_yes` lacks a linked actionable offer;
`social_question` has no supported readiness proposition; and `learn_result`
has no grounded proposition/learning event. Preserve current fail-closed or
repair outcomes. The fixture's expected states are not independent evidence;
resolve these cases with case-bound sources or annotation adjudication before
changing dispositions. Evidence: [Phase 8 trace](../../../evaluation/reports/phase8_corpus_report_20260928_confirmation_source_repair_v2.json),
[fixed corpus](../../../tests/fixtures/conversational_manifold/phase0_events.json).

#### Current-tree Phase 6 production-gate regression — 2026-09-28

The production gate, information-production bridge, and social-production
bridge test modules pass **53/53** in **232.75 s**; the social offer/acceptance
bridge separately passes **12/12**. Coverage includes graph-selected offer
acceptance with parse-back receipt, unresolved-offer repair, and the boundary
that accepting an offer does not itself execute an action. This verifies the
focused production mechanisms, not full Phase 8 release acceptance: the latest
corpus still records explicit errors, authorized silences, and unresolved
state-label disagreements.

#### Current-tree Phase 8 v5 rebaseline — 2026-09-28

Freshly replayed all **74** fixed Phase 0 events under the v5 event-context
protocol after the current provider-loading and evidence-transport changes.
Corpus digest remains `72bf847c…4406c3`; disposition authority is **74/74**.
Grounding is **20 TP / 30 FN / 0 FP (F1 0.571)**, with production totals of
**54 substantive releases / 6 explicit errors / 14 authorized silences** and
no unclassified silence or unreleased substantive event. Phase 4 is unchanged
at **3 source-bearing / 0 complete / 0 eligible / 0 promoted**. Measured target
scores are interpretation 0.716, grounding 0.400, action 0.667, repair 1.0,
calibration 1.0, and provenance 1.0; memory, learning, and normalized cost
remain unavailable. The release gate is still **blocked** because the human
baselines are missing and other reference classes/dimensions are not measured
under this protocol. Evidence:
[`current-tree Phase 8 v5 report`](../../../evaluation/reports/phase8_corpus_report_20260928_resume_current_v1.json).

#### Source-context production for unsupported causal questions — 2026-09-28

Kept native `learn` arbitration for an event-specific reason question whose
named topic is grounded but has no supported causal edge, while allowing the
existing production-gated learning-context route to ask for useful source
information. No topic-level causal retrieval, cause assertion, or answer
commitment is created. Focused causal-positive, missing-cause, full-corpus
context, and unresolved-information regressions pass **5/5**. Fresh Phase 8
v5 replay: authority **74/74**; grounding **20 TP / 30 FN / 0 FP (F1 0.571)**;
production **55 released / 5 errors / 14 authorized silences**; Phase 4
**3/0/0**. The formerly generic-error `info_explanation` now releases
“Might I ask what information would ground an answer?” with no answer
commitment. The comparative gate remains blocked; other explicit errors,
grounding recall, Phase 4 tuple production, latency, and deployment acceptance
remain open. Evidence:
[`causal-context Phase 8 replay`](../../../evaluation/reports/phase8_corpus_report_20260928_missing_causal_context_release_v1.json).
The complete Phase 8 corpus-runner suite passes **35/35** in **145.78 s** on
this tree.

The blinded evaluation packet was also refreshed against this exact replay:
**74/74** target responses join through the private alias key; the packet
contains **370** response tracks; both blank rater forms bind to its digest.
The protocol-aware raw audit confirms ELIZA **1/1**, small LLM **2/2**, and
modern LLM **2/2** complete runs, with no scoring; both human classes remain
missing. Packet, adjudication, and raw-audit tests pass **20/20**. See the
[Phase 8A comparative evaluation record](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md#current-protocol-v5-packet-after-causal-context-release--2026-09-28).

#### Proposition-confirmation source inquiry — 2026-09-28

When native arbitration selects `repair` with
`confirmation_lacks_conversational_support`, the adapter now asks for a source
to verify the proposition rather than asking what its known topic noun means.
This is surface realization only: the disposition stays `repair`, grounding
stays unresolved, and no answer commitment is created. The `question_ack`
case now releases “Might I ask which source should ground that confirmation?”
Focused controls pass **2/2**; the Phase 8 corpus-runner suite passes **35/35**
in **142.87 s**. Fresh corpus evidence preserves authority **74/74**, grounding
**20/30/0 (F1 0.571)**, production **55/5/14**, and Phase 4 **3/0/0**. The
exact-tree blinded packet joins at **74/74**; human comparison remains
unmeasured. Reports:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_confirmation_source_repair_v2.json),
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_confirmation_source_repair_v1.json),
[audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_confirmation_source_repair_v1.json).

#### Graph-connected provider loading at semantic ingress — 2026-09-28

Semantic adapters can now pass validated neutral `content_refs` into event
ingress. The provider resolver requires the referenced typed nodes and any
used connections to exist in the live graph; it derives only connections also
declared by a seed manifest. The seed index resolves those refs to exact
provider scopes before mutation; ambiguity fails closed. The dynamic loader
loads selected typed nodes and declared dependencies only, caches provider
grouping plus exact loaded `(type, name)` refs, and persists both for
sealed-profile checkpoint resume. A regression selects the `sensors` provider
for ambiguous `signal` via the live `sensor -measures-> signal` connection,
loads its declared `device_core` dependency, excludes generic lexical and
unrequested concepts, and confirms ambiguous-only follow-up leaves graph size
unchanged. The combined live graph resolver, dependency closure, existing
lexical pre-pass, scoped-provider, and Spanish/Japanese relation-focus
regression set passes **5/5** in **26.20 s**, including the extended
end-to-end checkpoint case. This closes adapter-to-seed provider resolution,
not arbitrary first-turn text-to-ref production; full-corpus resource/parity
acceptance remains open.

#### Cross-language relation-focus evidence transport — 2026-09-28

Added validated transport of neutral `relation_focus` (`polar`, `reason`,
`thing`) from language-adapted frames into graph interpretations. Unknown
labels fail closed, and adapter-supplied `relation_support` is not transported;
only graph evidence/native rules may assert support. Spanish and Japanese
provider regressions verify that the same event-specific reason focus passes
through live semantic ingress and native force/goal rules return the same
`request_information` / `answer_or_learn` result for both. The strengthened
bilingual regression passes **1/1**; the complete language-neutral evidence
arbitration module passes **56/56** in **611.34 s**. This improves evidence
transport but does not close broader multilingual deliberation, production, or
comparative gates.

#### Offline retrieval-miss completion of the connected daemon replay — 2026-09-28

Extended the daemon-ingress envelope with an explicit `offline_miss` retrieval
fixture, allowed only when host actions are drained. The fixture makes topic
grounding return no result and audits HTTP requests, so it tests terminal
repair/error behavior without external retrieval. Two independent fresh
74-event runs produce the same canonical observation digest; each selects the
complete seed closure, terminalizes **74/74** turns (**38** released replies,
**34** explicit errors, **2** expected no-response outcomes), drains all **11**
host actions and leaves zero pending turns/search/ground requests. The
`info_unknown` turn closes through its graph-selected repair receipt, while
`question_source` retains the attributed reported-content receipt. Both runs
make **zero** external HTTP requests and remain under the amended **150 MiB**
RSS cap (**136,982,528 / 137,101,312 bytes**); max native-cycle latency is
**88.02 / 94.46 ms** and ingress latency **16.54 / 18.80 ms**. The focused
daemon-envelope suite passes **12/12**. This closes connected-profile offline
host-action terminality and repeatability only; it does not establish retrieval
success, broad product-quality parity, or deployment/service acceptance.
Evidence: [run 1](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_v1.json),
[run 2](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_v2.json).

#### Connected daemon startup RSS and lazy WordNet availability — 2026-09-28

The first service-style measurement with local teachers attached peaked at
**290,240 KiB**. Inspection showed `domains.dict_teacher.is_available()` was
not a cheap availability check: it initialized NLTK's full WordNet reader and
attempted runtime downloads, then could report success without verifying the
corpus was actually usable. It now checks standard NLTK data directories for
an installed corpus without importing NLTK or downloading anything; `_wordnet`
opens the corpus only on a lookup. A regression proves the availability probe
works with NLTK unavailable. With the configured allocator, strict connected
profile, and grammar/dictionary teachers attached, service startup now peaks
at **108,380 KiB**. The daemon-ingress suite passes **20/20**. However, a
focused dictionary-lookup test process peaks at **265,108 KiB**, so lazy
startup alone does not close the 150 MiB query-path RSS gate; the service keeps
its **384 MiB** systemd hard limit pending a memory-bounded WordNet lookup
path. Checkpoint resume still reconciles only connected seed IDs, covered by
`test_conversation_checkpoint_resume_reconciles_only_connected_seed_scope`.

With the downloaded WordNet corpus now present, reran the full **74-event**
connected offline-miss daemon envelope after the availability change. It
terminalizes **74/74** turns, drains **11** host actions, makes **zero** HTTP
requests, and peaks at **138,072,064 bytes** under the active 150 MiB envelope;
max native-cycle and turn-completion latencies are **82.22 ms** and **82.16
ms**. This verifies the complete tested conversation corpus under the cap, but
does not exercise the dictionary corpus lookup path that exceeds it. Evidence:
[fresh lazy-WordNet replay](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_lazy_wordnet_v1.json).

#### Async post-comprehension authority reconciliation — 2026-09-28

The connected daemon had been releasing the blocked-permission fixture as an
explicit error because its first native pass had not yet linked the message's
modal and effect-verb mentions when communication authority was initially
recorded. Added a bounded second-stage adapter boundary: after initial native
comprehension, it refreshes event-scoped authority only from graph-linked
typed Concepts and invokes another native rule pass only when authority or
grounding changed. This keeps blocked-state choice in native arbitration and
does not infer permission, answer, or reply from sentence text. The fixed
non-turn permission event now ends with native `blocked`, `authority_status`=
`missing`, no reply, and no explicit error. Other no-evidence negative
controls remain fail-closed; a new same-sentence negative control without
provider-backed typed modal/action links retains `authority_status`=
`not_applicable`, no disposition, and no second native settle. The daemon
ingress suite passes **21/21**.

Two fresh 74-event offline-miss connected-profile runs have identical
canonical observation digests. Both complete **74/74** turns (**54** replies,
**5** explicit errors, **15** expected no-response outcomes), drain all **11**
host actions, leave zero pending turns, make zero HTTP requests, and pass every
resource assertion. Peak RSS is **138,420,224 / 138,457,088 bytes** (under
150 MiB); maximum native-cycle latency is **108.87 / 107.02 ms** (under 150
ms). This closes the specific async post-settle permission disposition gap
and demonstrates repeatability on the fixed connected corpus. It does not
close global cognition or product-quality parity: Phase 8 grounding remains
20 TP / 30 FN / 0 FP (F1 0.571), Phase 4 remains 0 complete tuples / 0
promotions, and human/reference comparative scoring remains open. Reports:
[run 1](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_authority_refresh_v1.json),
[run 2](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_authority_refresh_v2.json).

#### Native disposition for non-turn knowledge-deficit continuations — 2026-09-28

Resolved the `repair_missing` async/sync release mismatch with a native
cognitive disposition and an independently typed no-reply boundary. Seed
`communication_intent_arbitration` v1.4.11 selects `repair` only from the
event's typed unresolved/knowledge-deficit/information evidence and explicit
`non_turn`/`continuation` metadata. Native terminal readback then suppresses
the response slot; it does not turn this repair state into a surface reply.
The Phase 8 observation now preserves the graph arbitration basis, and its
silence audit accepts this case only when the exact basis is authoritative and
graph reply expectation is `not_expected`.

Fresh Phase 8 replay: disposition authority **74/74**, zero authority-free
label matches; `repair_missing` is native `repair`, no reply, no response slot.
Production is **54 released / 5 explicit errors / 15 authorized silences / 0
unclassified silences**. Grounding stays **20 TP / 30 FN / 0 FP (F1 0.571)**;
Phase 4 remains **3 sources / 0 complete tuples / 0 promotions**. The release
gate remains blocked at provenance.

Two fresh 74-event async offline-miss runs have identical digest
`9d443552515887fa9809cd403a02751d7f919a4f3e484506156b053598bf308c` and the
same **54 replies / 5 errors / 15 no-response** outcomes. Each drains all
**11** host actions, performs zero HTTP, leaves no pending turns, and passes
all resource assertions. Peak RSS: **138,100,736 / 138,248,192 bytes**;
maximum native-cycle latency: **98.95 / 84.16 ms**; completion latency:
**98.90 / 84.11 ms**. Tests: Phase 7 async **21/21**, Phase 8 corpus-runner
**35/35**, combined Phase 7 authority/action regressions **50/50**. Reports:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_nonturn_repair_native_v2.json),
[async run 1](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_nonturn_repair_native_v1.json),
[async run 2](../../../evaluation/reports/phase7_daemon_connected_offline_miss_20260928_nonturn_repair_native_v2.json).

The specific 1-event sync/async production parity difference is closed. The
overall conversational upgrade remains open on corpus grounding, incomplete
Phase 4 evidence, provenance release, human/reference comparison, and the
separate WordNet query-path RSS measure.

#### Current service-template profile and checkpoint-safety recheck — 2026-09-28

Reconciled the current checkout against the older deployment status above.
`deploy/jabberwock.service` now starts `--seeds conversation`, points at the
separate `%h/.jabberwock/checkpoints-conversation` directory, enables
`--strict-seed-profile-checkpoints`, and retains the 384-MiB hard cgroup limit.
The daemon tests prove three relevant boundaries (**3/3**): a full-profile
checkpoint is rejected for a conversation boot without being relabeled, a
legacy checkpoint without profile identity is rejected in strict mode, and a
conversation profile marker survives checkpoint round-trip. Thus the earlier
statement that the checked-in template still boots `full` is stale; historical
full-profile resource measurements remain valid evidence for why the template
changed. `systemctl --user show/cat jabberwock.service` could not connect to
the user bus in this environment (Operation not permitted), so the installed
unit, its activation state, and checkpoint migration are not verified. A
service-equivalent `--once` boot using the checked-in profile, strict
checkpoint, allocator, no-LLM, and teacher-attachment settings did complete:
it loaded **74/74** conversation seeds, attached grammar and dictionary
teachers, exited successfully in **1.13 s**, and peaked at **109,536 KiB RSS**.
The fresh **2,440,783-byte** checkpoint read back with
`DaemonSeedProfile=conversation`; its isolated temporary directory was removed
after readback. This verifies fresh boot and checkpoint serialization, not a
resumed long-running daemon or the installed systemd unit. The Phase 7 gate
remains open for installed-service/checkpoint validation, repeatable latency,
arbitrary service content prefetch, and query-path RSS.

#### Isolated WordNet query-path RSS attribution — 2026-09-28

Re-measured the dictionary path in a clean `.venv/bin/python` process, without
pytest or daemon fixtures, sampling `/proc/self/status` after interpreter
startup, module import, availability check, first lookup, and a repeated
lookup. Peak RSS was **13,120 kB** after importing `domains.dict_teacher`,
**13,124 kB** after the filesystem-only availability check, and **240,004 kB**
after the first successful `lookup("pump")` (11 senses). The second lookup
did not increase the peak. This confirms the old **265,108 KiB** test-process
peak is attributable primarily to loading/indexing WordNet on the real query
path, not pytest overhead; the isolated growth is about **227 MiB**, and it
exceeds the active **150 MiB** process envelope. No implementation change is
made on this evidence alone: the dictionary query-path resource gate remains
open, while the connected 74-event daemon profile continues to pass the
150-MiB cap when WordNet is not queried. The service unit's 384-MiB hard limit
is therefore unchanged.

#### Current-tree Phase 4 source-contract recheck — 2026-09-28

Re-ran `audit_phase4_tuple_sources('.')` across current seed manifests:
`ThoughtManifold` remains the sole approved tuple owner, with **0** exact
five-dimension seed sources and **0** node/manifest near matches carrying at
least two required dimensions. The live evidence and deliberation boundary
tests pass **29/29** (`test_phase4_partial_evidence_audit.py` and
`test_conversation_deliberation_phase4a.py`), preserving strict rejection of
incomplete/unapproved tuple sources and native-authoritative collapse. This
rules out a seed-only integration fix; Phase 4 still needs a genuine runtime
faculty source or explicit approval for a new native source contract.

#### Phase 8 `social_question` disagreement source check — 2026-09-28

Inspected the current authoritative trace and source fixture for this one of
eight state disagreements. The annotation classifies the entire string
`Good morning, are we ready?` as literal-form `social`, force
`social_action`, and expected state `answer`; runtime comprehension parses a
polar information question and finds no grounded readiness proposition. Both
acts are now preserved as ordered event-bound graph evidence. Native
arbitration independently selects a repair for the unsupported polar
question; a separate native rule selects the greeting reply plan. The live
turn composes the greeting and clarification only after both components have
independent released production receipts, without asserting readiness. The
focused compound-act tests pass **6/6**, including component-to-composition
graph-link checks. The focused follow-up across compound acts, explicit
uncertainty, and non-turn social production passes **19/19**. The initial
neighboring broader regression
selection finished **89 passed / 3 failed**. The two unresolved-reference
failures exposed that native arbitration matched only `action_request`, not
the equally typed imperative information-request case; a new narrow rule now
preserves that force and selects repair from unresolved referent evidence. The
third failure expected an exact reply-expectation mapping without its existing
`native_non_turn_defer` reason; the test now reflects the function contract.
The targeted recheck across these failures and the compound-response tests
passes **9/9**; the complete rerun of that broader selection passes **92/92**
in **466.61 s**. That broad pass predates the later exact composition-receipt
and parse-focused clarification refinements; those later changes pass the
**19/19** focused follow-up, the **6/6** compound suite, and the fresh
full-corpus Phase 8 replay below, but the 92-test batch was not rerun again
afterward. Independent adjudication of the fixture's overall expected state
remains open.

Fresh signal-only Phase 8 full-corpus replay after these changes (74 events)
has graph-authoritative dispositions **74/74**, force exact match **53/74
(0.716)**, grounding TP/FP/FN/TN **20/0/30/24** (precision **1.00**, recall
**0.40**, F1 **0.571**), action **6/9**, repair **16/16**, and calibration
**49/49**. Phase 4 remains **0** complete tuples / **0** eligible / **0**
promoted across three evidence records. The production audit recognizes all
substantive replies: **54/54** released, **15/15** authorized silent events,
zero unclassified silence, and zero unreleased substantive events.
`social_question` has both act-evidence records and independently released
greeting, repair, and exact-composition receipts; its current surface is
“Good day. May I ask what 'ready' means here?” Phase 8 turn latency is
**102.96/180.30/204.63 ms** median/p95/max (**15/74** above 150 ms). The
comparative release gate remains blocked at missing reference provenance;
human baselines, memory, learning, and cost remain unmeasured.

The corpus no longer treats `social_question` as only one mutually exclusive
act: its reference annotation records both greeting/social-action and
polar-question/information-request, plus the expected greeting and repair
components. The legacy scalar `expected_state` is explicitly only a projection.
Phase 8 reports a separate compound-act audit from graph-resident act evidence
and released component receipts; fixture annotations are validated but never
transported as runtime cognition inputs. Focused annotation, isolation, and
audit tests pass **3/3**. Fresh full-corpus replay reports exact act evidence
and complete released components (**1/1**, `complete: true`). Overall scalar
expected-state adjudication remains independent and open.

Two fresh connected-profile 74-event Phase 7 replays after the compound reply
change both select all **74/74** seeds and return zero errors. Peak RSS is
**135,811,072 / 135,987,200 bytes**, below the amended **157,286,400-byte**
ceiling; replay parity is exact. Max event latency is **145.19 / 158.08 ms**,
so the strict 150 ms bound remains variable rather than repeatably closed.
Current `df -h` reports **20 GB available (98% used)** and
`evaluation/reports` occupies **14 GB**; no large report artifact was written
for these runs. A third fresh run after narrowing the repair focus selects
**74/74** seeds, returns zero errors, has exact replay parity, peaks at
**134,750,208 bytes**, and reaches **161.12 ms** maximum event latency. All
resource assertions pass, but the strict per-event latency bound remains open.

The latest fresh in-memory Phase 8 v4 replay keeps the non-exclusive
`social_question` audit complete (**1/1 acts; 1/1 response components**) and
production accounting complete (**54/54 released replies; 15/15 authorized
silences; zero unclassified**), but reports synchronous latency
**109.20/195.31/213.98 ms** median/p95/max (**19/74** above 150 ms). Phase 4
remains **3 partial sources / 0 complete / 0 promoted**. Its cProfile follow-up
points to native rule execution and conceptualizer self-monitor as the main
turn-path costs; startup self-model work is separate and will not improve
turn latency. Preserve all authority/monitor gates while optimizing; repeat
the uninstrumented full-corpus run before closing the latency gate.

A paired one-round reply-conceptualizer trial yielded exact normalized
74-event observation equality with the current three-round ceiling, but did
not improve latency (**100.64/174.09/192.86 ms, 14/74** above 150 ms baseline
vs. **102.46/169.40/203.48 ms, 17/74** in the one-round trial). No code change
was kept; the native pass count is unchanged, so further work should target
rule/monitor execution cost rather than the conceptualizer round ceiling.

An initial connected-profile Phase 8 trial supplied raw utterance strings to
the batch candidate API (which expects lexical candidates); its lower
**65/74** disposition-authority result is invalid for the intended sealed
pre-pass. The corrected in-memory trial used the exact union of
`WorldAdapter.lexical_candidates()` for the 74 fixed events, selected **96**
seeds with declared closure complete, and matched all scored/core semantic
fields (**0/74** differences), authority (**74/74**), substantive releases
(**54/54**), and compound audit (**1/1**). Graph-internal IDs/trace snapshots
still differ, so structural digest equality is not claimed. Connected batch
latency was **50.70/101.94/133.81 ms** (median/p95/max; **0/74** over 150 ms)
versus full boot **108.84/178.75/218.20 ms** (**13/74** over). This supports
the sealed fixed-corpus pre-pass path, but not arbitrary online parity; RSS
under that exact sealed configuration and incremental-order semantic checks
remain open before changing the canonical Phase 8 runner.

Phase 8 now defaults to the service-aligned per-turn `conversation_incremental`
seed profile; explicit `conversation_corpus_prepass` and `full` modes remain
available as controls. A durable 74-event test verifies exact scored semantic
field and receipt parity across full, sealed, and incremental profiles,
including scorecard, grounding, Phase 4, production, and compound-act
summaries (**39/39 Phase 8 runner tests pass**). Incremental mode loads 74
initial seeds, 22 connected content-provider seeds, and reuses 24 providers
across 50 first-seen events. Three fresh runs peak at **135,102,464 /
133,791,744 / 133,283,840 bytes**; maximum turn latency is **140.30 / 143.01 /
146.93 ms**, with no event over 150 ms. A separate paired full-then-incremental
run did reach **165.53 ms** once, so latency requires continued monitoring.
The current service profile passes the 150-MiB and 150-ms bounds in three
fresh processes; Phase 4 tuple production and comparative human adjudication
remain open.

#### Current-tree Phase 8 runner regression — 2026-09-28

Re-ran `.venv/bin/pytest -q tests/test_phase8_corpus_runner.py` on the resumed
tree: **39/39 passed**, including the full/sealed/incremental 74-event
semantic-parity comparison and production receipt accounting. This confirms
runner/profile parity, not overall acceptance: Phase 1 parity deltas, Phase 4
**3 partial / 0 complete / 0 promoted**, variable strict event latency,
missing human ratings/adjudication, and unverified installed service state
remain open.

#### Portfolio clarification — 2026-09-29

Conversational cognition/production and functional substrate establishment are
both active goals and proceed concurrently; this tracker covers the former,
not a choice that suspends the latter. The substrate work remains separately
tracked against [`TRACTABILITY_SUBSTRATE_ASSESSMENT.md`](../engine_substrate/TRACTABILITY_SUBSTRATE_ASSESSMENT.md)
and [`FUNCTIONAL_SUBSTRATE_ESTABLISHMENT_PLAN.md`](../engine_substrate/FUNCTIONAL_SUBSTRATE_ESTABLISHMENT_PLAN.md).
Neither stream's progress is a completion proxy for the other. The current
conversational gates above remain open.

#### 2026-09-29 — Expose last progressing rule in native settlement report

The structured Rust `RuleRunReport` now retains the name of the last rule
whose attempt produced progress in that settlement call; the PyO3 report
resolves that native symbol while holding the substrate lock and exposes it
as `last_progress_rule`. The regression checks the reported name after a
single successful firing. `cargo check --lib` and the rebuilt-extension
targeted Python test pass (**1/1**). This is call-local observability only:
it is not persisted across `converse()`/fixpoint calls, does not establish an
ordered graph-resident event history, and cannot yet answer the temporal
selection query. Preserve Phase 1 and the durable-history gap as open. A
focused `cargo test --lib run_rules_report` attempt compiled the crate but
could not link its test binary because the extension-module build left Python
C API symbols unresolved; use an extension-compatible test path or configure
the test-link environment before claiming Rust test coverage.

#### 2026-09-29 — Persist conversation-scoped rule-firing evidence

The call-local report is now captured across the full conversation turn and
committed by the native substrate at `_finish_turn_reply` (including the
explicit silent-defer exit). Rust stores one bounded `RuleFiringHistory` node
with the last progressing rule name, inbound-message ID, and settlement
sequence, linked from the Agent by `has_rule_firing_history`. The turn capture
opens before conversational prepass and is committed only after reply
selection, preventing the current question from reading its own in-flight
firings as prior evidence. A no-progress turn preserves the last actual
firing. Graph export/import preserves the record.

Evidence: `cargo check --lib` passed; the rebuilt-extension capture/history
API and graph round-trip tests passed (**6/6** in
`test_mint_termination_fragment.py`); the temporal-selection repair check
passed (**1/1**); the full topic-route module passed (**18/18**). This closes
the missing history-source prerequisite at the evidence/storage layer only.
No native graph rule yet consumes `RuleFiringHistory` to select a positive
answer, and no production receipt yet authorizes releasing the selected rule
name; `Which rule fired last?` therefore remains unresolved and Phase 1 stays
open. The earlier call-local-only status is superseded by this entry, not the
open positive-answer gate.

#### 2026-09-29 — Answer prior rule-firing selection through native evidence

Added native arbitration for a turn-compatible, event-specific selection of
the rule referent when the agent has a committed `RuleFiringHistory`. The rule
copies the selected name onto the interpretation and mints
`RuleFiringAnswerEvidence` linked to that exact history node; a graph reply
rule renders the selected identifier. The adapter now gives this already
selected graph answer precedence over the generic unfamiliar-word faculty
and releases it through the existing `answer_question` production gate. The
history capture remains deferred until reply completion, so the answer
evidence points to the previous turn even though the current turn will later
replace the latest-history ledger.

Evidence: updated seed JSON parses; history-backed positive answer,
no-history repair, and unrelated-selection guard pass (**3/3**); full topic
route suite passes (**20/20**); speech-act parity passes (**6/6**). The
positive test checks the selected name against the prior ledger, the evidence
node's source-message ID, and the released `conversation_question_response_graph`
receipt. This closes the tested English event-selection route, not Phase 1
parity overall. The current semantic-adapter target-focus label is still
English-valued (`language_repair_focus=rule`), and multilingual semantic
projection/realization has not been verified; keep language-neutral
generalization open. Re-run the full Phase 1 parity battery and Phase 7/8
resource/latency profiles after this turn-path change. Comparative evidence,
Phase 4 tuple completion, and the other documented acceptance gates remain
open.

#### 2026-09-29 — Phase 1 compound-action recheck and residual adjudication

Added a native arbitration rule for sequential compound action requests with
an unresolved action head and dependency. This preserves `request_action` and
selects `act_or_clarify` while marking the disposition as repair. The focused
graph-arbitration check passes (**1/1**) after the rule was constrained to
neutral adapter evidence (`language_sequence_relation` and
`language_sequence_status`).

The expanded Phase 1 route-metric check now has one remaining mismatch out of
its 20 adjudications: “I cannot parse this.” is delivered as
`refusal/update_common_ground`, while the fixture expects
`assertion_or_correction/update_common_ground`. Physical/action inability
continues to have an intentional refusal path; do not broaden this change
without controls for those cases and typed nonunderstanding repair. Thus the
expanded slice is not yet green and Phase 1 parity remains open. This
conversational work and functional substrate establishment continue in
parallel as parts of the same project. Workspace disk check reported 31 GiB
free (97% used); no disposable in-repository build/temp artifact was
identified, and evidence/log files were preserved rather than deleted.

#### 2026-09-29 — Resolve the cognitive-inability adjudication by semantic role

The remaining expanded Phase 1 mismatch was caused by the English adapter
treating every first-person deficiency modal as action inability. Added
`parse` to the communication concept basis as a `mental_predicate`, then made
the adapter exempt typed mental-predicate deficiency from its action-refusal
classification. The normal declarative evidence path now reports
`assertion_or_correction/update_common_ground`; native cognition still
arbitrates the event from neutral evidence. No fixture expectation was
changed.

Controls protect the adjacent categories: “I cannot reach the upper switch”
remains `refusal/inability_action`, and “I do not understand the signal”
remains `repair_or_defer/nonunderstanding_report`. Evidence: expanded and
strict Phase 1 adjudication module **4/4**; compound communication acts,
speech-act parity, and text-comprehension suites **52/52**. This resolves the
reported 20-event adjudication mismatch but does not close the wider Phase 1
generalization gate or the whole cognition/production acceptance battery.
Because the communication seed changed, rerun full topic-route and Phase 7/8
resource/latency profiles against the current source before claiming profile
parity. Functional substrate establishment continues concurrently; comparative
evaluation, Phase 4 tuple completion, remaining acceptance gates, and overall
goal remain open.

#### 2026-09-29 — Release-engine resource/profile recheck after cognition change

The first current-tree resource replay was run against the 130-MB development
extension and produced 288–293 ms median Phase 8 turn latency. That result was
not comparable to the optimized runtime gate. Rebuilt with the sanctioned
`scripts/engine_build.sh` release profile (engine provenance verified: **9
passed, 1 skipped**); the installed engine shrank to 10.3 MB. On the release
engine, the 74-event Phase 7 connected conversation profile completes with
RSS **136,454,144 bytes** (~130.1 MiB), conversation max **169.74 ms**, zero
runtime errors, complete seed selection, and all RSS assertions passing.

Four fresh Phase 8 v5 runs retain **74/74 authoritative interpretations**,
**54/54 substantive reply releases**, and **15/15 authorized silences**.
Representative source report: [`phase8_corpus_report_20260929_release_current_v5.json`](../../../evaluation/reports/phase8_corpus_report_20260929_release_current_v5.json).
The latest exact-source replay records **65.10 ms median / 130.29 ms p95 /
145.72 ms max** (0/74 over 150 ms); the three earlier runs were
69.63/121.07/167.09, 64.85/120.16/158.97, and 62.24/122.75/166.76 ms
(median/p95/max). Phase 7 repeat max was also 141.32 then 169.74 ms. These
fresh samples show good central latency, but strict 150-ms maximum
repeatability remains open. Phase 4 remains **0 complete tuples / 0 promoted**,
with 3 source-bearing events; comparative capability scorecards remain
unavailable despite protocol-matched raw runs for three model classes. The
release gate reports `blocked` at provenance/empirical-completeness. Full
Phase 8 runner tests pass
**40/40** and the Phase 1 generalization test passes **1/1** on the release
engine; the combined Phase 1/topic-route/communication test battery passes
**76/76**. Phase 1 multilingual projection remains unverified.

Disk hygiene: moved only the representative 372-KiB Phase 7 and 664-KiB Phase
8 reports into `evaluation/reports`, removed the redundant temporary repeat
reports, and removed the disposable Rust development build cache with
`cargo clean --profile dev` (**1.7 GiB reclaimed**). The optimized installed
engine and release build were preserved. Functional substrate establishment
continues as a concurrent workstream; the overall goal remains active.

#### 2026-09-29 — Refresh Phase 8 blinded comparison packet for current release

Rebuilt the v5 blinded packet against the current release-engine target report
and protocol-matched raw ELIZA, Gemma 3 4B CPU (two runs), and Qwen 3.5 9B
(two runs) references. It contains **74 cases / 370 response tracks**, has no
system/corpus labels, randomizes aliases per case, and keeps all scores and
evidence notes blank. The private alias map verifies target-track identity
**74/74**; both blank forms bind to packet digest
`078c7c86b97db92815d87ecca86f32dae96b62d35c3a645742ae335ea5280443`. Raw
reference integrity is **3 complete model classes / 2 human classes missing**.
Audit, packet, and adjudication tests pass **20/20**. The private alias key is
separate in `/tmp`; it is not distributed. This makes current outputs
annotation-ready but does not score them: approved rubric anchors, two
independent ratings, adjudication, and human sessions remain required. Ollama's
local CLI is installed, but the local service socket is inaccessible in this
managed sandbox; no new model inference was run. This advances packet
freshness/integrity, not comparative capability closure.

#### 2026-09-29 — Make event-selection arbitration language-neutral

The rule-firing history answer no longer requires the English-specific
`language_repair_focus=rule` field or a text `Message` binding. The semantic
evidence contract now admits `relation_focus=selection` and validates a
neutral `selection_target_kind=rule`; native arbitration consumes that field
with event scope, unresolved grounding, turn-compatible context, and the
graph-resident history ledger. The English text adapter maps its target into
the same neutral category, while Spanish/Japanese semantic-frame adapters can
provide the category directly. Without prior history, native arbitration
continues to repair rather than guess.

Verification: Spanish/Japanese neutral history selection, no-history repair,
and schema rejection tests **3/3**; language-neutral variation plus temporal
selection **7/7**; English positive/no-history/unrelated-target routes **3/3**;
full topic-route + Phase 1 adjudication + speech-act battery **30/30**; Phase 8
corpus-runner parity **40/40**; packet, rater-form, raw-reference, and
comparative-gate tests **27/27**. The current Phase 8 report retains **74/74**
authoritative dispositions, **54/54** substantive releases, and **15/15**
authorized silences. Representative reports:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_neutral_selection_target_v1.json),
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_neutral_selection_target_v1.json).

Three fresh Phase 8 runs had median/p95/max latency **63.38/125.75/143.13**,
**63.26/123.91/148.85**, and **61.04/137.15/155.98 ms** (one of 74 over
150 ms in the third). Three Phase 7 runs peaked at **135,577,600 / 137,326,592
/ 136,585,216 bytes** (~129.3–131.0 MiB), had max turn latencies **144.74 /
146.93 / 153.64 ms**, and zero errors. Memory is within the 150-MiB cap;
strict maximum-latency repeatability remains open. The current v5 blinded
packet was refreshed to this target: **74 cases / 370 rows**, target join
**74/74**, all ratings blank, with both rater forms bound to digest
`8543fcf5f8e34795ffe1b05f7927b724999b037cec014c733a036076da93bb63`.
Human ratings/rubric approval and Phase 4's missing authored valuation source
remain open. Functional substrate establishment continues concurrently; the
overall goal remains active.

**Production-gap probe (2026-09-29):** The existing semantic frame
`break(Mary, vase, past)` realizes and passes the production gate in English,
Spanish, and Japanese. A candidate `be(rule, test_native_rule_42, past)` frame
returns no surface in any of those languages. The native graph already
selects and supports the prior rule identifier, so this is a bounded
production/lexicalization gap, not a cognition-selection gap. Do not substitute
an English-only canned graph string or bypass parse-back: add an appropriate
typed multilingual realization and bind its output to the same selected
`RuleFiringAnswerEvidence`, with exact production receipts and no-history and
unrelated-target controls. Functional-substrate Stage 0 also advanced
concurrently: the current 26-row/65-link map has refreshed call-name triage
and a scoped manual audit of conversation/production and language links; its
remaining audits are still open.

**Question-response commitment/surface binding (2026-09-29):** A production
gate audit showed that an answer-act commitment and its overt candidate could
come from different graph `Message` nodes linked to the same inbound turn.
The rule-history path exposed this: the selected-evidence message had the
surface but the generic empty response message had the answer act. The adapter
now requires the exact candidate and `answer` act on the same graph message;
the native rule-history reply also attaches its answer act to its own
history-supported message (seed `conversation_topic_reply` 1.2.1). The
split-message negative test plus the full Phase 6A suite and positive,
no-history, and unrelated-target rule-history controls pass **21/21**. This
repairs a bounded release-binding defect; it does not close full multilingual
surface production, Phase 4, the comparative gate, or other cognition/resource
acceptance.

**Grounded identifier token boundary (2026-09-29):** The Latin-script
comprehension tokenizer now preserves a code-like token containing underscores
or digits as one lexical unit only when its exact form is already grounded in
the active language's lexicon; unknown lookalikes retain the historical
letter-only split. This lets a source-bound native rule identifier survive
English/Spanish readback without converting its spelling into inferred
meaning. The multilingual variation plus legacy language-simulation suites
pass **14/14**, and `language_world.py` compiles. This is an input/readback
prerequisite only: the live rule-history surface still lacks a typed
multilingual realization and end-to-end output-null receipt gate. Comparative,
Phase 4, and strict repeatability acceptance remain open; functional substrate
establishment continues concurrently.

**Production-gap recheck (2026-09-29):** On the current checkout, the frame
producer was exercised with candidate typed frames for “rule fired” in all
three target languages. `fire(test_native_rule_42)` yields English
“The test_native_rule_42 fire.” and Spanish “El test_native_rule_42 fire.”;
Japanese also retains the English lexical item. Parse-back rejects all three
(`missing: fire, testnativerule`). Adding a `rule` agent and the selected name
as patient yields malformed English/Spanish order and likewise fails recovery;
Japanese still uses English lexical material and fails recovery. This confirms
that choosing another generic event/role arrangement is not a realization
fix. The frame-production and Phase 6A release-gate suites pass **21/21**;
this new negative probe does not change release policy. Next implementation
must supply a typed language-faculty route for the selected rule-event
proposition, with identity-preserving evidence and the same parse-back/receipt
boundary; otherwise keep the supported native answer unreleased.

**Rule-event realization seam probe (2026-09-29):** An isolated
`LanguageWorld` experiment with parallel English/Spanish/Japanese lexical
evidence for the same `fire(agent=<selected rule ID>, past)` frame produced a
surface in each language, and `LanguageProduction` self-monitor recovered the
exact canonical agent concept in all three. The English/Spanish training rows
also expose an important boundary: bare heuristic parsing of unseen lexical
items is not enough; the graph must contain language-specific, source-backed
lexical entries for the selected identifier and event before realization.
This establishes a viable faculty-level direction, not a production fix: the
probe used a fixed alias-to-ID training example and did not exercise live
selection, arbitrary identifier encoding, question-response routing, or
receipts. Do not promote the probe as multilingual release evidence. The next
implementation needs source-bound lexical identity for arbitrary held rule
names, native-selected event semantics, and end-to-end output-null parse-back
before the answer message is released.

**Native rule-history answer realization (2026-09-29; supersedes the earlier
“production gap remains unimplemented” notes):** The `reply_selected_rule_firing_history`
native rule now creates an output-null answer Message with the selected
`RuleFiringAnswerEvidence`/history links and no English surface (seed
`conversation_topic_reply` 1.2.3). After validating that exact binding, the
adapter registers only the selected rule identifier as a language-local
opaque lexical item, detects the inbound language, and asks
`LanguageProduction` for a one-slot contextual answer fragment. The fragment
construction omits clause-only determiners/particles, preserves the exact
case-sensitive identifier, self-monitors back to the same concept, then must
pass the adapter parse-back gate. Release readback updates the same output-null
Message and emits a receipt whose `releases` edge targets that message; the
same message must retain its answer act and exact selected-evidence/history
edges. The receipt records `semantic_event=answer_fragment` and
`parse_back_mode=grounded_comprehension` rather than a fabricated successful
graph-text gate.

Evidence: prior-history live answer, no-history repair, missing-evidence-edge
withhold, and English/Spanish/Japanese exact-ID answer-fragment tests pass
**4/4**; the complete topic-route module passes **20/20** (243.33 s); the
Phase 6A production-gate plus language-neutral variation suites pass **26/26**;
the language-neutral variation and legacy language-simulation suites pass
**14/14**. Seed JSON, four modified Python modules, and `git diff --check`
validate. This closes the tested live English event-selection surface gap and
the direct three-language identity-fragment slice; live end-to-end ES/JA
question ingress, arbitrary-name corpus coverage, Phase 7/8 replay after this
change, remaining production/cognition gates, Phase 4, comparative ratings,
and strict latency repeatability remain open. Functional-substrate work
continues concurrently.

**Post-change Phase 7/8 recheck (2026-09-29; supersedes the preceding
“replay after this change remains open” status):** Phase 7 processes all 74
events with complete seed selection, deterministic replay, zero errors, and
all RSS assertions passing; peak RSS is **136,867,840 bytes** (~130.5 MiB),
under the amended 150 MiB ceiling. Max event latency is **172.39 ms**, so
strict 150-ms repeatability remains open. Phase 8 retains **74/74**
authoritative dispositions, **54** substantive releases, **15** authorized
silences, and zero unclassified silences. The normalized state/reply/release/
grounding/authority tuples match the preceding source-current report on all
**74/74** events. Grounding remains **21 TP / 29 FN / 0 FP** (F1 **0.592**);
Phase 4 remains **0 complete / 0 promoted**; the comparative release gate
remains blocked at provenance/empirical completeness. Phase 8 latency is
**67.52/138.69/158.69 ms** median/p95/max (**2/74** over 150 ms). Reports:
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_rule_history_fragment_v1.json),
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_rule_history_fragment_v1.json).

**Live multilingual ingress probe (2026-09-29):** An isolated
`WorldAdapter.converse()` replay establishes prior rule history, then asks
`¿Qué regla se ejecutó por última vez?` and
`最後にどのルールが発火しましたか？`. Both fail before native selection:
Spanish repairs on unfamiliar `¿Qué`; Japanese repairs on the complete
unsegmented utterance. The Spanish inbound falls to `frontier`, Japanese to
`statement`; neither message records a detected language, and both preserve
the raw phrase as topic text. This confirms that direct en/es/ja answer-fragment
tests are not live ingress parity. The next cognition/production increment is
grounded Spanish/Japanese segmentation, lexical and question/event-time
evidence feeding the shared native selector, followed by the exact-identity
production/readback gate. No Python translation or surface shortcut is
authorized. Conversational and functional-substrate work remain concurrent,
separately gated streams.

**Live language metadata follow-up (2026-09-29; supersedes only the preceding
claim that inbound messages record no language):** `receive_utterance()` now
stores script-based `language` on each inbound Message as mechanical routing
metadata. The new EN/ES/JA controls and full language-neutral/topic-route
regressions pass **28/28**; the field itself makes no semantic claim. Fresh
Phase 7 replay is deterministic and error-free over **74** events with complete
selection, **113,549,312-byte** (~108.2 MiB) peak RSS, all 150-MiB assertions
passing, and **124.20 ms** max event time. Fresh Phase 8 v5 retains 74/74
authoritative dispositions and exact normalized state/reply/release/grounding/
authority parity (**74/74**) with the preceding source-current report.
Grounding remains **21/29/0 TP/FN/FP**; Phase 4 remains **0 complete / 0
promoted**; production remains **54 substantive replies / 15 authorized
silences / 0 unclassified**. Phase 8 latency is **64.25 ms median / 178.53 ms
max (4/74 above 150 ms)** and the comparative gate remains blocked on
provenance/empirical completeness. Live ES/JA parsing and selection remain
open. Reports:
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_language_label_ingress_v1.json),
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_language_label_ingress_v1.json).
Conversational cognition and functional-substrate establishment remain
concurrent, separately gated workstreams.

**Cross-language wh-NP composition (2026-09-29):** Added Japanese closed-class
interrogatives including ``どの`` to the finite proform reference, taught the
CJK tokenizer to preserve these reference forms even before lexical grounding,
and retained them through the inference replay pass. Wh determiners now compose
with a following nominal head's grounded core-role marking, so the question
variable occupies the queried role rather than being replaced by the nominal
head. The grounded LanguageWorld parses both Spanish ``¿Qué gato se sentó en la
alfombra?`` and Japanese ``どの猫がマットの上に座った？`` as ``?WHAT`` agent,
``sit`` event, and grounded location. Regression evidence: language-neutral and
language-simulation suites **25/25**; expanded ES/JA held-out parse **1/1**.
This advances the multilingual language faculty but is not yet live
``converse()`` integration; native text ingress, event-selection, parse-back,
and release remain open. The cognitively authoritative selector and the
functional-substrate track remain concurrently active and separately gated.

**Live multilingual rule-history bridge (2026-09-29):** Closed the previously
open exact Spanish/Japanese ingress slice. `converse()` and asynchronous
`ingest_turn()` now try a bounded LanguageWorld adapter for validated `es`/`ja`
event-time rule-selection frames; unsupported frames fall back to the ordinary
comprehension path. The language faculty supplies graph-grounded lexical and
semantic-frame evidence, while the existing native communication arbitration
selects answer versus repair and binds any answer to prior `RuleFiringHistory`.
There is no translation, answer choice, or rule-name lookup in the new bridge.
Live `converse()` tests for `¿Qué regla se ejecutó por última vez?` and
`最後にどのルールが発火しましたか？` both select the exact prior rule, retain
the source-history evidence edge, pass grounded output-null parse-back, and
release the exact identifier with the appropriate punctuation. The combined
language-neutral variation and topic-route suites pass **33/33** (342.67 s).
Follow-up asynchronous-ingress evidence-recording controls pass **2/2**; these
verify only evidence transport, not daemon settlement or reply completion.
This closes only the tested language/event/query surface: unsupported
multilingual constructions, asynchronous reply completion, fresh Phase 7/8
replays, strict latency repeatability, Phase 4, broader production/cognition
parity, and comparative-evaluation evidence remain open. Functional-substrate
establishment continues concurrently as an independently gated workstream.

**Post-bridge Phase 7/8 source-current replay (2026-09-29):** Phase 7
replayed all **74** events twice with exact deterministic equality, complete
selection, and zero errors. All six resource assertions pass at the **150 MiB**
ceiling; conversation peak RSS is **111,968,256 bytes** (~106.8 MiB), with
84,275,200 bytes growth. Maximum event latency is **158.28 ms**, leaving the
strict 150-ms latency target open. Phase 8 v5 records authoritative native
dispositions on **74/74** events. The normalized per-event cognition/force/
grounding/release/reply tuples match the preceding source-current report on
**74/74** cases. Grounding remains **21 TP / 29 FN / 0 FP** (F1 **0.592**);
production remains **54** substantive releases, **15** authorized silences,
and **0** unclassified silences; Phase 4 remains **0 complete / 0 promoted**.
Phase 8 latency is **64.11 ms median / 157.69 ms max** (**3/74**
over 150 ms). The comparative gate remains blocked on unavailable human
references and incomplete provenance. Reports:
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_live_multilingual_bridge_v1.json),
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_live_multilingual_bridge_v1.json).
These broad replays do not replace multilingual ingress tests or close the
remaining cognition/production acceptance criteria; functional-substrate
establishment continues as a concurrent, separately gated workstream.

**Async multilingual history-answer completion (2026-09-29):** The live
daemon dispatcher now routes a native `grounded_rule_firing_history` answer
through the same identity-binding, language realization, and production gate
used by synchronous conversation. Spanish and Japanese async tests each run
ingress, native tick/comprehension/authority settlement, selected-history
readback, output-null `answer_fragment` release, and exact reply verification;
they pass **2/2**. The synchronous rule-history refactor plus history-selector
and repair controls pass **5/5**. The daemon debug/interface suite reports
**31 passed, 1 environment-limited failure**: its HTTP debug test cannot bind a
localhost socket in this restricted runtime (`PermissionError`); the failing
test does not reach cognition assertions. Fresh Phase 7 replay covers **74/74**
events with deterministic equality, zero errors, complete selection, and all
150-MiB assertions passing; peak RSS is **111,824,896 bytes** (~106.7 MiB),
max event latency **110.28 ms**. Phase 8 v5 retains **74/74** authoritative
dispositions and exact normalized outcome parity with the prior replay; it
records **54** substantive releases, **15** authorized silences, **0**
unclassified silences, grounding **21/29/0 TP/FN/FP**, and Phase 4 **0 complete
/ 0 promoted**. Phase 8 max latency is **152.77 ms (1/74 above 150 ms)**, and
cross-run latency repeatability remains open. Comparative-evaluation evidence
is still blocked by incomplete references/provenance. Reports:
[Phase 7](../../../evaluation/reports/phase7_profile_resource_20260929_async_multilingual_completion_v1.json),
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260929_async_multilingual_completion_v1.json).
Functional-substrate establishment remains concurrently active and separately
gated.

**Phase 8 blinded comparison packet refreshed to async-completion target
(2026-09-29):** Rebuilt the v5 packet and independent blank rater forms against
the latest source-current Phase 8 target; the target identity join is **74/74**
across **370** response rows. Both forms bind to packet digest
`a25f9f3cef165fb08af721be45755c1772ef5de2fe5dccdf20b0e4385377b70b`; score
fields and notes remain blank. The protocol-aware raw audit remains **3
complete reference classes / 2 missing human classes**, so no scoring was
performed and the comparative gate remains open. Packet/adjudication/raw-audit
tests pass **20/20**. See the current artifacts in the
[Phase 8A comparison record](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md).

**Grounding-recall false-negative triage (2026-09-29):** The current Phase 8
v5 report's **29** reference-label false negatives divide into **13** events
whose corpus source is only declared discourse state, **7** with only a
declared graph path, **8** marked surface/uncertainty-only, and **1** attributed
source utterance. The declared-source categories do not have a verified
runtime referent path; the sparse nonempty paths in this set are
`authority_missing` or attributed-source evidence, neither of which proves a
grounded referent. This is not justification to promote any of these turns
from their text, reply, or source annotation. Continue by auditing individual
declared graph/discourse supports against event-bound graph records and keep
source attribution distinct from world/referent grounding. The 21 TP / 0 FP
trade-off and unresolved 29 FN remain reported; no metric definition or
corpus label was changed. Functional-substrate work continues concurrently.

**Current Phase 4 source audit and concurrent substrate-map validation
(2026-09-29):** Re-ran `audit_phase4_tuple_sources('.')`: **0 exact** and
**0 near** qualifying sources. The three current Phase 8 partial sources are
all `Phase4PartialEvidence` records (grounding only; missing expected value,
residual cost, consequence, and novelty), and none can be promoted without a
genuine authored valuation source. The focused partial-evidence and Phase 4A
tests pass **29/29**. In parallel, regenerated and checked the substrate
capability-map mirror: **26** rows, **224** resolved source links, **65** linked
test references, **239** result-linked runners, and zero validation errors.
This confirms inventory/link integrity only; Stage 0 path/evidence audit and
Stage 2 natural-task locality remain open. These are simultaneous independent
tracks: neither result suspends or substitutes for the other.

**Concurrent current-tree integration regression (2026-09-29):** The language-
neutral variation and Phase 8 corpus runner batch passes **51/51**; the native
CAN reimplementation and solver-dispatch batch passes **24/24**. This rechecks
the live cognition/profile path and the functional substrate path in the same
turn. Results do not close multilingual generalization, grounding, production,
strict latency repeatability, Phase 4, comparative evidence, substrate Stage 0
audit, or Stage 2 natural/authored-task locality. Both streams remain active.

**Discourse-grounding false-negative trace (2026-09-29):** A fresh prefix
replay of Phase 8 `correction` (`No, the gate is closed.`) confirms the prior
instruction placed `north gate` in the graph discourse state, but the corrective
interpretation itself has no parsed topic or event-bound grounding path and
remains `unresolved`. The reference label `partially_grounded` therefore is not
runtime-verified by this path yet. The next cognition change must provide
scope-bound nominal reference evidence, not infer grounding from the repeated
surface noun or global topic projection. The 29 false negatives remain open.

**Polar-relation grounding correction and concurrent substrate refresh
(2026-09-29):** The unsupported polar question “Can you confirm the route?”
was incorrectly given referent status from a lexical `Concept` despite missing
proposition support. The native seed now clears that exact lexical-only path
after repair selection while preserving supported discourse/HeldAnswer paths.
Focused polar-reference checks pass **5/5**, correction still passes **1/1**,
and the discourse-reference checks pass. Fresh Phase 8 v5 preserves **74/74**
reply strings and authoritative dispositions; grounding is **20/30/0 TP/FN/FP**
(F1 **0.571**). The scoped `question_response` path remains supported;
lexical-only `question_ack` is unresolved. This is stricter source accounting,
not a recall gain. Production is **54/15/0** and Phase 4 **0 complete / 0
promoted**. Two independent Phase 7 runs pass all six 150-MiB RSS assertions
at **137,031,680 / 135,983,104 bytes**, but both exceed 150-ms latency (**165.92
/ 159.54 ms**), leaving that gate open. All Phase 8 response strings match the
preceding blinded packet target **74/74**; comparative human ratings remain
missing. Concurrent substrate inventory validation now reports **26 rows / 224
source links / 65 test refs / 245 result-linked runners / 0 validation errors**.
Both workstreams continue, with remaining gates explicitly open.

**Connected pre-pass latency/resource comparison (2026-09-29):** Two fresh
Phase 7 runs moved the known 74-event lexical connected closure (96 seeds) to
before turn one. Both pass all six 150-MiB assertions at **111,841,280 /
112,050,176 bytes** peak RSS, and their stable observation records are exactly
equal to incremental loading on **74/74** events. Maximum event latency is
**145.54 / 150.76 ms**, compared with **165.92 / 159.54 ms** for incremental;
one batch run still narrowly misses 150 ms, so latency repeatability remains
open. This fixed-corpus sealed pre-pass does not replace the live connected
fallback. cProfile on two slow-turn candidates attributes 72–75 ms to the
graph-authored conceptualizer/reply pipeline, including 45–54 ms of native
`run_rules`; tail events vary between runs. Next latency work should target
repeated conceptualizer/rule settlement without changing native decision
authority. In the parallel substrate stream, two focused solver-decompose
success/refusal tests passed and the Stage 0 manual test-path audit now covers
13/65 linked test files. Neither stream's broader gates are closed.

Fresh Phase 8 v5 repeat 2 has identical dispositions, grounding statuses, and
reply strings to v2 (**74/74**), with grounding **20/30/0 TP/FN/FP** and
production **54/15/0**. Its max synchronous turn is **150.09 ms (1/74 over)**,
versus **145.24 ms (0/74 over)** in v2. This confirms the threshold crossing is
not yet repeatable; maintain the strict latency gate as open.

**Conceptualizer attribution and connected-prepass repeats (2026-09-29):** A
diagnostic full-corpus run observed 51 conceptualizer calls over 74 events,
each with exactly three native rule passes; the existing loop skips idle
passes, so the three stages align with successive graph-input boundaries and
are not safe candidates for blind pass deletion. Diagnostic maximum event
latency was 122.16 ms with zero errors. Two further clean-process
connected-prepass Phase 7 runs pass all six 150-MiB assertions over 74/74
events, with peak RSS **111,730,688 / 111,845,376 bytes** and maximum latency
**121.74 / 116.00 ms**, no events above 150 ms. Across four connected-prepass
runs, three are under the strict target and one is **150.76 ms**; latency
repeatability remains open. Reports are
[`repeat 3`](../../../evaluation/reports/phase7_profile_resource_20260929_connected_batch_prepass_repeat3.json)
and [`repeat 4`](../../../evaluation/reports/phase7_profile_resource_20260929_connected_batch_prepass_repeat4.json).
Continue cost attribution within each native/graph pass without weakening
selection or release authority. Functional-substrate work continues
concurrently; these conversational results do not close its Stage 0, Stage 1,
Stage 2, or later gates.

**Scope-bound nominal correction reference (2026-09-29):** The event-bound
trace showed `No, the gate is closed.` following a grounded `north gate`
instruction plus an unrelated unresolved standalone action. The correction
had a parsed subject `gate` but no referent path. The language adapter now
reports support only for a definite subject whose typed head matches a prior
grounded turn-compatible instruction target in the same discourse and
participant scope; indefinite and mismatched subjects remain unsupported.
Native arbitration still selects the disposition. Grounding-evidence tests
pass **39/39**, and the Phase 8 corpus plus language-neutral variation batch
passes **51/51**. A fresh v5 replay changes only the correction event: **21 TP /
29 FN / 0 FP**, F1 **0.592**, with all 74 normalized forces, dispositions,
authority flags, and replies otherwise unchanged. Production is **54/15/0**;
Phase 4 is still **0 complete / 0 promoted**; empirical comparative evidence,
latency repeatability, and the substrate stages remain open. See
[`Phase 8 report`](../../../evaluation/reports/phase8_corpus_report_20260929_definite_nominal_correction_v1.json).
Two source-current clean-process Phase 7 runs after the cognition edit cover
74/74 events with zero errors, identical normalized observations, and all six
150-MiB assertions passing at peak RSS **111,849,472 / 111,820,800 bytes**.
Maximum event latency is **125.68 / 158.94 ms**; the second run exceeds 150 ms
on `assertion_source`, so latency repeatability remains open. Reports:
[`run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_definite_nominal_correction_v1.json),
[`run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_definite_nominal_correction_repeat2.json).

**Concurrent streams and current implementation correction (2026-09-29):**
Conversational cognition and functional-substrate establishment remain
simultaneously active; neither replaces or waits on the other. The language
adapter contributes typed definite-reference parse evidence only. Native
authored rules perform event indexing/carry and select the antecedent under
discourse-order, participant-scope, and matching-head constraints. The focused
native-path, grounding-reference, Phase 8 corpus, and language-neutral batch
now passes **90/90** after this rewrite (940.13 s). Latest Phase 8 replay is
**21/29/0 TP/FN/FP**, F1 **0.592**, and
production is **54/15/0**; Phase 7 v2/v3 resource assertions pass the **150-MiB**
cap at about **107 MiB**, but max latency is **180.56/180.54 ms**, leaving the
latency gate open. The Stage 0 substrate path audit is separately at **17/65**.
Track and close evidence for each stream independently.

Native `rule_costs()` instrumentation over a fresh 74-event connected-prepass
diagnostic (0 errors) attributes **420,818 μs** total to the three new scoped
reference rules (**5.7 ms/event** average, **19.1 ms** combined maximum on one
event). This is a measurable but partial latency contribution, not an
explanation for the full ~180-ms tail. Retain the supported native grounding
behavior and profile the remaining graph/reply path; existing Phase 7 v2/v3
reports remain the replicated resource evidence.

**Cue-indexed episodic overlap join (2026-09-29):** The native memory seed
declares an exact-key `Episode.cue_key` join hint. Episodic rule tests pass
**16/16**; the post-change Phase 8/language-neutral suite passes **51/51**, and
the native nominal-correction case passes **1/1**. The fresh Phase 8 report is
behaviorally identical to the previous normalized report (**21/29/0
TP/FN/FP**, production **54/15/0**, Phase 4 **0/0**), while empirical
comparative release remains blocked. Two independent Phase 7 reports pass all
six memory assertions, but latency is **210.96/183.97 ms**, so strict latency
repeatability is still open. See
[`Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260929_overlap_index_hint_v1.json),
[`Phase 7 run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_overlap_index_hint_v1.json),
[`Phase 7 run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_overlap_index_hint_v2.json).
The intermediate cue-index report used default **v4**, not v5; its **105.56 /
211.21 / 242.41 ms** figures are v4 diagnostics and do not establish v5
latency.

**Typed cue-overlap population (2026-09-29):** Follow-up trace inspection
showed the conversation runner's 74 `Episode` nodes were legacy message
records with no cue key. Seed 1.1.3 now keeps them in generic memory but only
lets bound, non-empty-cue episodic-working-memory traces enter native overlap
matching. The episodic suite passes **18/18**; join-index plus episodic tests
pass **23/23**. Native overlap-rule cost on the 74-event corpus is now **419
μs total** versus **255.9 ms** before scoping. Phase 7 v1/v2 observations
match exactly, all six 150-MiB assertions pass at ~107 MiB, but max latency is
**202.68/204.86 ms**. Two explicit Phase 8 v5 reports retain **21/29/0
TP/FN/FP**, production **54/15/0**, Phase 4 **0/0**; latencies are **108.85 /
124.75 ms median**, **203.61 / 216.62 ms p95**, and **267.88 / 271.70 ms max**
(**19/74** and **22/74** over 150), and comparative release remains blocked.
See [`v5 run 1`](../../../evaluation/reports/phase8_corpus_report_20260929_typed_cue_overlap_population_v5_v1.json),
[`v5 run 2`](../../../evaluation/reports/phase8_corpus_report_20260929_typed_cue_overlap_population_v5_v2.json),
[`Phase 7 run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_typed_cue_candidate_relation_v1.json),
[`Phase 7 run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_typed_cue_candidate_relation_v2.json).

**First-turn import prewarming (2026-09-29):** A cold connected-profile
cProfile of `action_referent` found roughly **45 ms** of first-turn import cost
under `domains.language_world` and `domains.morphology_reference`. Added both
mechanical adapter/reference modules to the existing connected-profile runtime
prewarm. The profile-boot regression passes; `test_phase7_production_envelope.py`
passes **22/22**. A post-change cProfile no longer attributes first-turn time
to those imports. A separate fresh one-event diagnostic reports **1,373 ms
boot**, **49.76 ms conversation turn**, **102,649,856-byte** connected-profile
peak RSS, complete selection, and no errors. This single event does not close
the corpus latency gate; the full current Phase 7/8 maxima remain over 150 ms.
The existing cached dependency/content closure remains the pre-turn load path;
the incremental fallback remains available only for later vocabulary outside
the declared prepass. Conversational and substrate gates remain concurrent.

Two fresh-process 74-event Phase 7 runs after this change are byte-equal in
normalized observations to each other and to the preceding typed-cue
candidate-relation report. Both cover **74/74** events with complete selection,
zero errors, and all six 150-MiB assertions passing at peak RSS
**113,700,864 / 113,582,080 bytes**. Max event latency is **181.10 / 176.45
ms**, with **5/74** turns above 150 ms each. This is lower than the preceding
202.68/204.86-ms pair, but the cross-run comparison does not isolate prewarming
as the cause; strict latency acceptance remains open. Reports:
[`run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_runtime_prewarm_v1.json),
[`run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_runtime_prewarm_v2.json).

**Indexed scoped nominal-grounding join (2026-09-29):** Seed
`communication_intent_arbitration` 1.4.16 now declares an exact-key native
join hint from parser-provided `language_referential_head` to prior grounded
`language_action_target_head`. The rule's discourse edges, ordering, scope,
and grounded-status predicates remain authoritative and unchanged. The
deferred batch-closure correction case and mismatch/scope/future negative
controls pass; grounding-reference + Phase 8 + language-neutral suites pass
**52/52** and join-index + episodic suites pass **23/23**. Native rule-cost
attribution falls from **179,049 μs / 342 calls** to **6,276 μs** total
(**258 μs** maximum per event). Two 74-event Phase 7 runs retain exact
normalized observations and pass all six 150-MiB checks at
**113,590,272 / 113,750,016 bytes**, but still peak at **189.59 / 171.81 ms**
(**7/74 / 5/74** over 150 ms); this rule-local win does not close the overall
latency gate. Fresh explicit Phase 8 v5 behavior matches the prior reports:
**21/29/0 TP/FN/FP**, production **54/15/0**, Phase 4 **0/0**. Latency is
**122.25/213.59/287.86 ms** median/p95/max (**25/74** over 150); the release
gate remains blocked. See
[`Phase 7 run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_nominal_head_index_v1.json),
[`Phase 7 run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_nominal_head_index_v2.json),
[`Phase 8 v5`](../../../evaluation/reports/phase8_corpus_report_20260929_nominal_head_index_v5_v1.json).

**Indexed predecessor join for scoped target carry (2026-09-29):** Event
recording now stores the immediate predecessor's state-local `event_index` as
mechanical `predecessor_event_index`; seed 1.4.17 uses exact-key native hints
for scoped carry and correction grounding. The hints only narrow candidates;
the actual `follows_event`, state, order, mode, speaker/addressee, and grounded
target checks remain in native rules. Legacy predecessors with a usable
`event_index` remain addressable; without one, the optional probe key is
omitted and the matcher falls back to its ordinary edge scan. The full
grounding-reference/Phase 8/language-neutral/discourse-sequence/join-index set
passed **59/59** before adding that missing-index control; current sequence and
grounding focused tests pass **4/4**. Native carry cost across 74 events
falls **261,532→10,398 μs** (max **14,281→386 μs/event**); correction grounding
is **5,999 μs**. The fresh Phase 7 pair is observation-identical to each other
and the prior prewarm pair, error-free, and passes all six 150-MiB assertions
at **113,700,864 / 113,598,464 bytes**. Maxima are **171.56 / 169.12 ms** with
**2/74** over 150 each, leaving a narrow connected-profile latency miss. Fresh
Phase 8 v5 normalized behavior is unchanged (**21/29/0 TP/FN/FP**, production
**54/15/0**, Phase 4 **0/0**), but full-boot latency is **112.53/217.63/264.24
ms** median/p95/max (**20/74** over 150); comparative release remains blocked.
See [`Phase 7 run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_predecessor_index_v1.json),
[`Phase 7 run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_predecessor_index_v2.json),
[`Phase 8 v5`](../../../evaluation/reports/phase8_corpus_report_20260929_predecessor_index_v5_v1.json).

**Native pending-request indexes (2026-09-29):** Conceptualizer shape and
monitor scans now use the native exact `(node type, status='requested')`
attribute indexes rather than enumerating all historical requests on each
pass. This only narrows graph candidates; authored rules still create requests
and govern Verdict/commit/revise, while comprehension and fresh audience
regrounding are unchanged. The conceptualizer/composer audit tests pass
**23/23**. A full-corpus scan diagnostic checked **204** enumerations and
confirmed exact candidate parity while avoiding **5,304** historical-node
checks: **15.1 ms** scan/filter versus **3.2 ms** indexed lookup.

Fresh Phase 7 runs retain exact normalized observations, no errors, and all six
150-MiB assertions at **113,610,752 / 113,729,536 bytes**, but maxima remain
**176.73 / 229.78 ms** (**3/74 / 7/74** over budget). The targeted lookup win
does not establish a stable latency improvement. Full Phase 8 v5 normalized
behavior also remains unchanged (**21/29/0 TP/FN/FP**, production **54/15/0**,
Phase 4 **0/0**); latency is **119.55/223.40/248.84 ms** median/p95/max
(**23/74** over 150), so release remains blocked. See
[`Phase 7 run 1`](../../../evaluation/reports/phase7_profile_resource_20260929_pending_status_index_v1.json),
[`Phase 7 run 2`](../../../evaluation/reports/phase7_profile_resource_20260929_pending_status_index_v2.json),
[`Phase 8 v5`](../../../evaluation/reports/phase8_corpus_report_20260929_pending_status_index_v5_v1.json).

**Connected-path cProfile diagnostic (2026-09-29):** A fresh instrumented
74-event connected-profile run completed without errors. Under profiler
overhead, 51 substantive replies each traversed the reply conceptualizer;
fresh monitor parse-back (`language.comprehend`) and repeated audience
regrounding are material costs, alongside native rule execution and initial
seed/profile boot. This is attribution only, not latency acceptance evidence:
instrumented wall time is not comparable with Phase 7/8 reports. The parse-back
and regrounding are explicit semantic requirements of the release monitor, so
they were not removed or weakened. Phase 7/8 latency remains over target and
all cognition, Phase 4, and comparative gates remain open.

**Full-seed late-turn attribution (2026-09-29):** To avoid extrapolating from
the connected profile, instrumented the full-seed Phase 7 path at the
late-corpus `defer_permission` signal (`Wait until the signal changes.`). The
single-turn cProfile recorded 8 `run_rules` calls (176.08 ms cumulative under
instrumentation), monitor parse-back 37.50 ms, and 134 native production adds
(26.50 ms). A separate opt-in native scale-audit pass on the same event counted
1,952,011 Term evaluations and 238,475 candidate tests. Per-rule attribution
assigns 347,765 Term evaluations to `curiosity_targets_ambivalent_nodes`, then
91,698 to `default_mode_mint_episode_context`; the next two rules each account
for 66,627. These are diagnostic counts, not latency acceptance evidence or a
semantic defect by themselves. The current phase 8 full-boot maximum remains
above 150 ms. The next optimization review must establish the broad
ambivalence rule's intended graph scope and exact parity before narrowing its
candidate population.

**Current Phase 8 expected-state recheck (2026-09-29):** The latest explicit
pending-status-index v5 replay still has the same **8** native/annotation
state disagreements. Two ability offers are graph-grounded and receive a
social acceptance (`answer`), not an action-execution goal; `response_yes`
has no linked actionable antecedent and remains `defer`. The other five lack,
respectively, relation/proposition evidence, permission authority, readiness
evidence, or event-bound learning evidence. No runtime policy change is
justified by these fixture labels; preserve the existing evidence boundary and
keep the action labels pending source-bound support or independent annotation
adjudication. See the [current v5 report](../../../evaluation/reports/phase8_corpus_report_20260929_pending_status_index_v5_v1.json)
and [canonical recheck](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

**Invariant episode-winner query reuse experiment (2026-09-29):** Full-seed
late-turn attribution showed that `default_mode_mint_episode_context` repeats
the same pure graph-query `Argmax` while matching 63 already-consolidated
episodes for one agent. A narrowly scoped native per-step cache is now keyed
by the Argmax term and its free-variable bindings; it bypasses selector/tie
audit modes and clears with graph-dependent caches. The test binary was linked
with the installed Python 3.13 library and loader path; all **56/56**
`term::tests` pass, including the new free-variable/agent-separation and
mutation-invalidation case. The rebuilt source-current release extension and
build provenance pass **9/9** non-skipped checks. Four independent 74-event
Phase 7 connected runs preserve normalized observations and all pass the
150-MiB checks at **110.25–110.33 MiB**; max latency is **139.63/155.22/147.96/
139.21 ms**, so the strict repeated max gate remains open (one run has 1/74 over
150). Two Phase 8 v5 replays also preserve normalized behavior: **21/29/0
TP/FN/FP**, production **54/15/0**, Phase 4 **0/0**. Their latency is
**63.30/114.01/142.70 ms (0/74 over)** and **67.87/124.85/172.72 ms (1/74
over)**. The improvement is now measured, but the corpus still lacks
memory/learning probes and comparative baselines, and grounding/Phase 4 gates
remain open. A separate Phase 7 full-seed control peaks at **1.42 GiB** during
boot; do not generalize the connected-profile resource pass to full boot.
See the [execution-plan results and reports](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).
Substrate Stage 0 continues concurrently; its manual linked-test audit is now
**21/65** (see the functional-substrate plan).

**Literal equality candidate pre-pass (2026-09-29):** Native rewrite hints now
support an exact string literal probe as well as a bound-attribute probe.
`steer_promote_concern` and `steer_retire_concern` declare the already-required
`Message.from == "interlocutor"` equality as an index probe; the original
where-clause, speech-act/mention/concern predicates, and graph-edge checks
remain authoritative. The matcher and JSON checkpoint path are covered by
**29/29** rewrite tests and the literal-hint round-trip test (**1/1**); source
compiles, the rebuilt extension is provenance-current, and provenance checks
pass (**9 passed, 1 skipped**).

The first test-path audit found that lexical unresolved-topic clarification
could release before a native-selected, evidence-backed self-model-rule answer.
The release ordering now gives that supported reflective answer priority;
`tests/test_conversation_loop.py` passes **14/14**, including its exact
same-turn `ProductionGateReceipt` check. Four post-fix fresh 74-event connected
Phase 7 runs preserve identical normalized observations with no errors; all
six 150-MiB assertions pass at **114,024,448–114,200,576 bytes**. Total
conversation times are **3.907 / 3.899 / 3.898 / 3.962 s**, with maxima
**148.25 / 132.96 / 125.60 / 152.13 ms**. Three runs are below 150 ms and one
has 1/74 over, so the strict repeated tail gate remains open and the aggregate
latency change is modest rather than a robust closure.
The same-protocol Phase 8 v5 pair remains behavior-identical (**21/29/0
TP/FN/FP**, production **54 substantive / 15 authorized silences / 0
unclassified**, Phase 4 **0/0**); the post-fix run measures **69.77 ms
median / 133.49 ms p95 / 170.22 ms max**, with **2/74** over 150. Strict
latency and comparative release gates remain open. Stage 0 manual linked-test
review is **22/65**; its inspected conversation-loop route now passes 14/14.
See [Phase 7 run 3](../../../evaluation/reports/phase7_profile_resource_20260929_literal_index_probe_v3.json),
[Phase 7 run 4](../../../evaluation/reports/phase7_profile_resource_20260929_literal_index_probe_v4.json),
[Phase 7 run 5](../../../evaluation/reports/phase7_profile_resource_20260929_literal_index_probe_v5.json),
[Phase 7 run 6](../../../evaluation/reports/phase7_profile_resource_20260929_literal_index_probe_v6.json),
[Phase 8 v5](../../../evaluation/reports/phase8_corpus_report_20260929_literal_index_probe_v2.json),
and the [substrate path audit](../engine_substrate/SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md).

**Exact-source rebuild and replay (2026-09-29):** String literal probes are
represented as interned symbols, preventing unsupported non-string Rust probe
values from reaching the JSON checkpoint exporter. Focused native matcher and
checkpoint tests pass **1/1 each**; the rebuilt extension is engine
`a5aa1ea0812e`, with provenance tests **9 passed, 1 skipped**. The full
conversation-loop suite passes **14/14** against this exact extension. Two
additional independent 74-event Phase 7 runs preserve the same normalized
observations: total time **3.710 / 3.799 s**, maxima **152.43 / 129.27 ms**
(one of two has 1/74 over 150), RSS **113,799,168 / 113,672,192 bytes**, with
all six 150-MiB assertions passing. The matched Phase 8 v5 run preserves the
same semantic projection (**21/29/0 TP/FN/FP**, production **54/15/0**,
Phase 4 **0/0**) and measures **66.15 ms median / 120.75 ms p95 / 140.40 ms
max** (0/74 over); the comparative gate remains blocked. These exact-source
replays match the preceding literal-probe run pair after timing fields are
excluded. See [Phase 7 run 7](../../../evaluation/reports/phase7_profile_resource_20260929_literal_index_probe_v7.json),
[Phase 7 run 8](../../../evaluation/reports/phase7_profile_resource_20260929_literal_index_probe_v8.json),
and [Phase 8 v5 run 3](../../../evaluation/reports/phase8_corpus_report_20260929_literal_index_probe_v3.json).

**Concurrent context/identity component evidence (2026-09-29):** The live
context-model and interlocutor feed path was rechecked with
`tests/test_context_model.py` (**5/5**, 85.54 s). The cases verify seeded and
newly minted context dimensions, residual salience, identity re-attribution
from fed context shifts, collapse-engine routing, and a zero-call self-teacher
counter. This strengthens component-level evidence for conversational context
cognition, but not end-to-end production/release or general language
understanding. At the same time, the substrate Stage 0 linked-test audit
advanced from **22/65 to 23/65**; that audit is independent and still open.
Neither result closes the strict latency, grounding, Phase 4, comparative, or
functional-substrate acceptance gates. See the [path audit](../engine_substrate/SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md).

**Current-tree memory/learning revalidation (2026-09-29):** The supplemental
five-topic teacher/interference/delayed-repeat probe was rerun against the
current tree and still scores **5/5 learning, 5/5 delayed memory**. Prelearning
absence, exact teacher payloads, distinct typed grounding evidence, turn-bound
commitments, and separate released receipts all hold; the focused test passes
**1/1**. This is controlled within-system evidence, not corpus-wide or
comparative evidence; protocol-matched references and the frozen corpus's
memory/learning dimensions remain open. The functional-substrate review
continues concurrently, separately gated. See the [current report](../../../evaluation/reports/phase8_memory_learning_probe_20260929_current_v1.json)
and [execution-plan entry](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

**Phase 4 authority gap re-audited (2026-09-29):** The seed census finds no
complete or near-match evidence tuple; tests pass **5/5** for the live
admission/bridge boundary but inject their own complete `ThoughtManifold`
values. No production valuation/consequence faculty currently supplies those
candidate-bound measurements. This gate therefore remains genuinely open;
the next required work is upstream faculty/evidence generation, not adapter
completion of partial records. Both cognition and substrate workstreams remain
active and separately gated. Details are in the [execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

**Direct conceptualizer-entry coverage (2026-09-29):** Added a behavioral
regression for `conceptualize_reply()` that verifies graph-authored intent,
audience-grounded wording, and native committed-result readback. The combined
conceptualizer and live-converse suites pass **20/20**, covering selected live
answer/instruction/ask-back/monitor routes in addition to the direct wrapper.
This closes an entrypoint coverage gap, not general live-turn production
parity; the substrate manual path audit records **24/65** links reviewed and
remains independently open.

**Blinded target remains current (2026-09-29):** A private-key event join
confirms the Phase 8 v5 current literal-index report matches the existing
Argmax-cache packet's conversational-manifold target on **74/74** exact reply
strings and **74/74** presence flags, including all **15** empty authorized
silences. No packet refresh is required for this replay. This does not supply
ratings or close comparative evaluation; both human classes, rubric approval,
independent annotations, and adjudication are still absent. See the
[comparative evaluation record](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md).

**Late-turn attribution on the accepted batch profile (2026-09-29):** A
targeted cProfile replay of the full connected 74-event path identified the
conceptualizer monitor/commit pipeline and native settling as the dominant
costs on `info_unknown` and `defer_permission`; parser parse-back and
audience-model construction are additional required costs. The correctly
matched batch-before-boot run completed without errors at ~**113.7 MB** peak
RSS. A separate accidental incremental-profile diagnostic exposed an ~**87
ms** mid-corpus loader burst and ~**141.1 MB** peak RSS, so it is not evidence
to replace the batch profile. Profiling alone proves no speedup. Next latency
work must preserve fresh regrounding and semantic parse-back. The Phase 4,
grounding, strict-repeatability, comparative, and substrate gates remain open.

**Native parser graph reuse (2026-09-29):** `comprehend()` now carries
graph-recognized lexical tokens into semantic composition on the same native
scratch graph, avoiding a redundant second graph construction while leaving
native recognition/Merge and semantic readback intact. Focused language,
grammar, neutrality, and selected live-conversation coverage passes **84/84**;
four representative old/new parse cases match exactly. The local 40-call
paired microbenchmark fell from **0.418 s** to **0.329 s**. The accepted
74-event batch-before-boot profile passes with zero errors, deterministic
74/74 observations matching the previous literal-index profile, all 150-MiB
RSS assertions, and **113,913,856-byte** peak RSS; maximum turn latency is
**117.87 ms** in the recorded run (**109.17 ms** in its deterministic replay).
These are separate-run latency observations, not yet a strict repeatability
closure. See the [source-current report](../../../evaluation/reports/phase7_parser_graph_reuse_20260929.json),
[replay report](../../../evaluation/reports/phase7_parser_graph_reuse_replay_20260929.json),
and [execution-plan detail](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md). Both
the cognition gates and functional-substrate plan remain active and
independently tracked.

**Source-current fixed-corpus revalidation (2026-09-29):** After parser graph
reuse, the Phase 8 v5/event-context/history-8 corpus again completed **74/74**
with no execution errors and **65.59/125.34/143.74 ms** median/p95/max
(**0/74** over 150 ms). Normalized observations exactly match the prior v3
report when per-event timing fields are excluded. Grounding remains **21/29/0
TP/FN/FP**, production **54 substantive / 15 authorized silence / 0
unclassified**, and Phase 4 **0 complete / 0 promoted**. The report's release
gate remains blocked by unavailable matched human and small-/modern-LLM
scorecards, not by a failed run. Ollama is installed locally but its service
is not listening; at 97% disk use (33 GiB free), no model download was
attempted. See the [source-current Phase 8 report](../../../evaluation/reports/phase8_corpus_report_20260929_parser_graph_reuse_v1.json)
and [execution-plan entry](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

**Current-tree v5/resource revalidation (2026-09-29):** A fresh sealed
conversation-prepass Phase 8 replay completes **74/74** events with native
disposition authority **74/74**, zero runtime errors, and normalized
state/grounding/release/reply-presence/exact reply parity with all four prior
v5 repeats. Latency is **48.39/91.45/104.22 ms** median/p95/max (**0/74**
over 150 ms). Two fresh connected-profile Phase 7 processes each select all
**96** seeds and complete all 74 events without errors; normalized semantic
observations match, all six RSS assertions pass, and peak RSS is
**107,352,064 / 107,409,408 bytes**, below **150 MiB**. Grounding remains
**23/27/0 TP/FN/FP**, production **54 substantive / 15 authorized silence / 0
unclassified**, Phase 4 **0 complete / 0 eligible / 0 promoted**, and
comparative evaluation remains blocked on human references and independent
ratings. `refusal_unknown` is cognitively blocked but has no graph-selected
reply plan or release receipt; a generic acknowledgment would not be authorized
by the current production contract. These reports establish this connected
profile only, not full-seed boot or daemon/socket operation. Details and report
links are in the [execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

**Current-tree Phase 4 authority recheck (2026-09-29):** The live evidence
generation, partial-evidence audit, Phase 4A lifecycle, and held-out task-family
tests pass **41/41**. Native settlement and source/provenance gates remain
intact; current Phase 8 still has **3 source-bearing events / 0 complete / 0
eligible / 0 promoted** tuples. No candidate-bound outcome/valuation faculty
is wired: `SystemTwoContext` is not a per-candidate outcome estimate and must
not be substituted. Phase 4 remains open pending an approved outcome-grounded
source; this is separate from and concurrent with the live conversational and
functional-substrate workstreams.

**Narrow unavailable-action receipt (2026-09-29):** A typed graph-authored
acknowledgment now releases for `refusal_unknown` while native disposition stays
`blocked/unavailable_action_response`; no action, Goal, or authorization is
created. Focused integration tests pass **103/103**. Fresh Phase 8 is **74/74**
with authoritative disposition **74/74**, zero runtime errors, and no changes
to other events' normalized states/grounding/replies/releases. Synchronous
turn latency is **48.40/91.96/117.36 ms** median/p95/max; the broader
observation clock including post-turn audit is **49.32/95.81/118.78 ms**.
Grounding is **23/27/0 TP/FN/FP**,
production **55 substantive / 15 authorized silent / 0 unclassified**, and four
explicit-error replies. Phase 4 remains **0 complete / 0 eligible / 0
promoted**; raw ELIZA/small-/modern-LLM references exist, while both human
reference classes and ratings remain missing. The cognition and
functional-substrate tracks are both active and
concurrent; substrate full boot/daemon integration is still unverified. See the
[execution-plan update](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md) and [fresh
corpus report](../../../evaluation/reports/phase8_corpus_report_20260929_unavailable_action_ack_v1.json).

**Current comparative target and audit (2026-09-30):** Rebound the blinded
packet to the latest Phase 8 target, including `refusal_unknown` → “understood”;
regenerated the **74-case / 370-response** packet and blank independent R1/R2
forms. The raw audit recognizes protocol-matched runs whose optional `system`
field is null via their typed input key, while rejecting a conflicting explicit
identity. ELIZA, small LLM, and modern LLM raw collections are complete
(**1/1, 2/2, 2/2**); both human classes remain missing and the audit performs
no scoring. The packet/audit regression batch passes **22/22**. This advances
comparative readiness, not its human-rating gate. See the [current
packet](../../../evaluation/reports/phase8_blinded_output_packet_20260930_unavailable_action_ack_v1.json),
[R1](../../../evaluation/reports/phase8_blinded_rater_template_20260930_unavailable_action_ack_v1_r1.json),
[R2](../../../evaluation/reports/phase8_blinded_rater_template_20260930_unavailable_action_ack_v1_r2.json),
and [raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260930_unavailable_action_ack_v1.json).
