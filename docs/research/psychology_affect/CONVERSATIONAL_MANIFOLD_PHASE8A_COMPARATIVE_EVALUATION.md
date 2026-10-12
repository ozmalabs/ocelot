# Phase 8A comparative evaluation and release-gate scaffold

Phase 8A defines the measurement contract for comparing the conversational
manifold against five reference classes:

- ELIZA floor
- small LLM
- modern LLM
- base human
- advanced human

The target and every reference are scored on the same fixed cognition
dimensions:

`interpretation`, `grounding`, `action`, `repair`, `memory`, `learning`,
`calibration`, `provenance`, and `cost`.

This increment is a scaffold, not a benchmark result. It intentionally does
not fabricate scores for models or people, or claim that the target has been
measured when the live corpus runner has not completed. A scorecard is valid only when it
contains all nine dimensions, a fixed protocol identifier, a sample count, a
95% interval, a raw-metric description, and provenance references to the
underlying cases or annotations.

## Raw operational cost observations — 2026-09-28

Existing protocol-v5 CPU Gemma 3 4B runs provide an operational reference only:
each run has 74 cases, `num_gpu=0`, and an average end-to-end request duration
of **4,340 ms** (seed 42) and **4,294 ms** (seed 43), with median durations of
**4,337 ms / 4,279 ms** and p95 durations of **5,529 ms / 5,519 ms**. The mean
generated output is **17.14 tokens** in both runs. Sources:
[`seed 42`](../../../evaluation/reports/phase8_small_llm_gemma3_4b_cpu_event_context_v5_history8_seed42_20260925.json)
and
[`seed 43`](../../../evaluation/reports/phase8_small_llm_gemma3_4b_cpu_event_context_v5_history8_seed43_20260925.json).

The latest target replay reports a `WorldAdapter.converse` synchronous-call
median of **88.59 ms**, p95 of **164.32 ms**, and max of **203.80 ms** across
74 events; **5/74** calls exceed 150 ms. It explicitly excludes post-turn
audit:
[`target replay`](../../../evaluation/reports/phase8_corpus_report_20260928_uncertain_learning_gap_v2.json).
These timings are **not directly comparable**: the target measure covers only
the synchronous adapter call, whereas the LLM measure includes a complete
generation request and its transport/runtime overhead. They document distinct
cost boundaries, not relative efficiency or capability. The connected-profile
resource harness separately passes its configured assertions; full-seed boot
and end-to-end production latency remain open release gates. No cost score is
assigned.

## Measurement semantics

Capability scores are normalized to `[0, 1]`, with higher meaning better. The
`cost` score means cost-effectiveness; raw latency, memory, tokens, energy, or
money must remain in the referenced evidence. The gate never silently
inverts an unlabelled cost number.

Comparisons use interval separation:

- `above`: target lower bound is above the reference upper bound;
- `below`: target upper bound is below the reference lower bound;
- `indeterminate`: intervals overlap.

Indeterminate is not failure and is not superiority. It identifies where the
protocol needs more samples or better measurement precision.

The report scaffold can be generated without running any system:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m evaluation.phase8_corpus_runner \
  --scaffold --output evaluation/reports/phase8_corpus_report_scaffold.json
```

The scaffold binds exactly 74 Phase 0 events, marks the target `not_run`, marks
all five external baselines `unavailable`, and must remain `blocked`. A live
target report is only produced by omitting `--scaffold`; baseline scorecards
remain unavailable until those systems are actually run under this protocol.

The v2 report envelopes also contain `comparison_summary`. This is an availability envelope,
not an additional score: `measured` means interval comparison is eligible,
`unavailable` means the reference was not collected, `missing` means no
scorecard was supplied, and `not_comparable` means the target or reference
cannot support a comparison. Unavailable baselines have empty dimension
comparisons and are never represented as zero performance or superiority.

Each reference class also has a runnable envelope generator:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m evaluation.reference_protocol \
  modern_llm --output evaluation/reports/modern_llm_reference_scaffold.json
```

The envelope records the adapter entrypoint, collection mode, annotation
source, all 74 case IDs, raw observation slots, and an unavailable scorecard.
It does not score absent model or human observations. The five reference
protocols are ELIZA floor, small LLM, modern LLM, base human, and advanced
human; their collection specifications are exposed by
`comparative_release_gate.protocol_contract()`.

## Release rule

The gate reports `ready` only when all six scorecards (target plus five
references) are complete, every dimension has evidence, and no target
dimension is below a baseline. Missing or unproven evidence produces
`blocked`; it does not receive a conversational fallback or an assumed score.

Run the focused scaffold tests with:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m pytest -q --tb=short tests/test_phase8a_comparative_release_gate.py
```

The next Phase 8 increments should bind this contract to the fixed Phase 0
event corpus, preregister case-level annotation rules, collect repeated
baseline observations, and publish a dated report with confidence intervals
and failure slices. Until then, Gate G8.1 remains open.

## Input-profile parity follow-on — 2026-09-25

An implementation audit found that the v4 substrate runner consumes all 74
events in one persistent graph, receives per-event interaction-mode/relation
metadata, and installs two held-answer setups. The v4 local-LLM adapter instead
used isolated signal-only prompts. V4 raw outputs remain valid as v4 collection
records, but must not be treated as cross-system comparisons for history- or
setup-dependent dimensions.

The opt-in `phase8a-fixed-phase0-corpus-v5-event-context-history8` raw profile
adds those per-event metadata/setup fields and the most recent eight
signal/response pairs to each LLM prompt. It is a bounded context-aware profile,
not full graph-memory parity; memory and learning scores remain unavailable.
Two CPU-only Gemma 3 4B runs (seeds 42 and 43) are case-complete raw evidence
for v5; exact response text agrees across all 74 cases. This does not score
capability. V4 and v5 runs must not be combined into one scorecard. A valid v5
comparison still requires a target run explicitly bound to this input profile,
human references, and blinded annotation/adjudication. The raw-reference audit
now accepts repeated `--run SYSTEM=PATH` entries and enforces two complete
seeded runs for both LLM classes. Its protocol-aware v5 report marks small LLM
and modern LLM as complete raw classes, ELIZA as `not_comparable` (only its v4
signal-only adapter existed in that audit), and both human classes as missing.
The ELIZA status was superseded by the 2026-09-27 matched-context raw audit
below; ELIZA remains part of the overall five-class release contract and is
not removed from the gate.
Even the v5 profile is only bounded transcript/setup parity, not full
graph-memory parity, so memory and learning remain unavailable.

The Phase 8 SUT runner now accepts the same protocol explicitly:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m evaluation.phase8_corpus_runner \
  --protocol-id phase8a-fixed-phase0-corpus-v5-event-context-history8 \
  --output evaluation/reports/phase8_corpus_report_<date>_v5.json
```

The v5 report marks `memory_learning_comparable: false` and does not include
the v4-only ELIZA scorecard. The target still uses its graph-resident event
history as its cognitive authority; this protocol label binds the shared event
sequence, setup facts, and interaction metadata, but does not claim equivalent
bounded memory representations. The report must be reviewed for profile
parity before interpreting any dimension; it is not itself a capability
comparison or release result.

Two CPU-only Qwen 3.5 9B v5 runs have completed all 74 cases with no
collection failures; their raw responses agree exactly on all cases. Seed 43
measured mean 35.399 s (p95 47.215 s, max 48.764 s), with 4.18 generated
tokens/s. This is runtime/repeatability evidence, not a capability score. The
latest protocol-aware raw audit is recorded below; the earlier audit state was
superseded when the ELIZA floor gained a matched v5 input envelope.

The graph-native SUT has also completed a v5-bound 74-event report. It retains
graph authority/history and marks memory/learning as not comparable; the
shared protocol identifier alone does not establish equivalent memory
representations.

## Matched ELIZA v5 envelope — 2026-09-26

The deterministic ELIZA floor now emits a v5-bound observation envelope with
the same per-event interaction metadata, held-answer setup, and preceding
eight signal/response pairs supplied to the other v5 systems. Its response
rule remains lexical/reflection-only and does not inspect hidden corpus labels;
only raw-trace provenance is scored, while all eight capability dimensions
remain unavailable. The v5 raw audit accepts ELIZA as **1/1** complete raw
run, Gemma as **2/2**, and Qwen as **2/2**. Both human classes remain missing;
the audit is `incomplete` and performs no score interpretation. Evidence:
[`ELIZA raw run`](../../../evaluation/reports/phase8_eliza_floor_event_context_v5_history8_20260926.json),
[`protocol-aware raw audit`](../../../evaluation/reports/phase8_raw_reference_audit_20260926_v5_eliza_matched_context.json).

This closes the matched-input-profile gap for the ELIZA reference only. It does
not complete blinded human annotation, make memory/learning comparable, or
release the comparative gate.

## Current target recheck — 2026-09-26

After adding the native failed-topic repair transition, a fresh v5-bound
74-event SUT run still blocks comparative release at `provenance`. It records
**56/74** authoritative dispositions, grounding **14/50** (recall **0.28**,
F1 **0.438**), and Phase 4 evidence at three grounding-only sources with **0**
complete tuples/promotions. Turn latency is median/p95/max
**131.58/195.28/214.94 ms**, with **29/74** over 150 ms. The sole outcome change
from the prior current-code report is `info_unknown`, now a graph-selected,
production-gated repair. The refreshed target report is
[`failed-topic repair v2`](../../../evaluation/reports/phase8_corpus_report_20260926_failed_topic_repair_v2_event_context_v5.json).

The latest raw-reference audit remains incomplete: ELIZA is **1/1**, small LLM
**2/2**, and modern LLM **2/2** complete raw collections, but both human
reference classes are missing. Score interpretation is not performed and the
overall release gate remains blocked. No capability comparison is inferred
from raw LLM or ELIZA collection records. See the
[`current raw audit`](../../../evaluation/reports/phase8_raw_reference_audit_20260926_lazy_p0a_import_v1.json).

## Production-release authority slice — 2026-09-27

The target report now includes a production-release audit separate from
cognitive scoring. A substantive nonempty reply is counted receipt-backed
only when its event-bound ProductionGateReceipt has status released and the
exact returned surface. Explicit diagnostic errors and deliberate silence
are separate terminal categories, not successful semantic releases.

Fresh v5 evidence records **43/43** substantive replies released, seven
withheld receipts for diagnostic errors, **25** explicit errors, and **6**
silent events, with no unreleased substantive surfaces. The three prior
instruction-gap report paths now release their exact graph-authored Message
through the production gate. This closes the corpus receipt-coverage slice;
it does not establish semantic correctness, full Levelt-path parity,
grounding quality, or comparative capability. The report continues to show
grounding F1 **0.438**, zero complete Phase 4 tuples, and a blocked
comparative release gate. Evidence:
[Phase 8 production release audit](../../../evaluation/reports/phase8_corpus_report_20260927_instruction_gap_receipt_v2.json).

## Current v5 target and refreshed blinded packet — 2026-09-27

A fresh graph-native target replay is now bound to the fixed v5 context/history
protocol and its 74 event contexts. It records **65/74** graph-authoritative
dispositions, **49** substantive receipt-backed releases, grounding **20/50**
(precision **1.00**, recall **0.40**, F1 **0.571**), and zero complete Phase 4
tuples/promotions. Memory and learning remain non-comparable under v5 because
a bounded transcript is not equivalent to graph memory, despite the separate
target-only five-topic probe. The target report is
[`typed-offer grounding v5`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_offer_grounding_v1.json).

The unscored blinded adjudication packet was refreshed against the preceding
target replay and
the existing complete v5 ELIZA, Gemma 3 4B (two seeds), and Qwen 3.5 9B (two
seeds) raw runs. It contains **370** response rows across 74 cases, randomized
per-case aliases, and no corpus labels, system names, or assigned scores. The
private alias key remains in `/tmp`, outside the repository. Packet and raw-
reference audit tests pass **10/10**. Ollama is installed, but its localhost
daemon is inaccessible in the current sandbox; no new LLM observations were
collected. Human references and blinded dual annotation/adjudication remain
missing, so score interpretation is still unavailable and G8.1 remains
blocked. Artifacts:
[`blinded packet v3`](../../../evaluation/reports/phase8_blinded_output_packet_20260927_v3.json),
[`raw reference audit`](../../../evaluation/reports/phase8_raw_reference_audit_20260927_adjudication_ready_check_v1.json).

## Dual-rater integrity workflow — 2026-09-27

Added `evaluation.phase8_blinded_annotation_adjudication` to bind each rater
form to the SHA-256 of the exact blinded packet, validate complete five-domain
rows and required notes, report nominal agreement/Cohen's kappa, and preserve
disagreements as unscored until an independent blinded adjudicator resolves
them. The workflow never reads response text or the private alias key and does
not create system scorecards. Its tests and the packet-builder tests pass
**6/6**. Blank templates for blind raters A/B are generated from the current
74-case packet.

This is infrastructure, not collected annotation. Rater IDs, completed forms,
adjudication, and a dimension-specific approved scoring rubric are still
missing; do not distribute these score fields as a finished rubric or
interpret model capability until those requirements are supplied and met.
An explicitly unapproved starting point for reviewer discussion is the
[`response-rating rubric proposal`](CONVERSATIONAL_MANIFOLD_PHASE8A_RUBRIC_PROPOSAL_20260927.md).
It covers only the five response-level fields and does not create scores or
close the human-reference/comparative gate.
Current forms:
[`rater A`](../../../evaluation/reports/phase8_blinded_rater_template_20260927_a.json),
[`rater B`](../../../evaluation/reports/phase8_blinded_rater_template_20260927_b.json).
Create and check forms with:

```text
PYTHONPATH=runners/dsl/python:. python3 -m evaluation.phase8_blinded_annotation_adjudication template \
  --packet evaluation/reports/phase8_blinded_output_packet_20260927_nonunderstanding_repair_v1.json \
  --rater-id blind-rater-a --output /path/to/rater-a.json

PYTHONPATH=runners/dsl/python:. python3 -m evaluation.phase8_blinded_annotation_adjudication audit \
  --packet evaluation/reports/phase8_blinded_output_packet_20260927_nonunderstanding_repair_v1.json \
  --rater-a /path/to/rater-a.json --rater-b /path/to/rater-b.json \
  --output /path/to/blind-audit.json
```

### Human response-track support — 2026-09-27

The blinded packet builder now accepts optional, protocol-matched
`base_human` and `advanced_human` sessions with exactly one case-bound response
per corpus event. When present, responses receive randomized aliases and
their history is built independently; system/run provenance remains only in
the private key. Missing human sessions remain absent, never scaffolded into
responses, and the existing model-only packet shape is unchanged. The packet
CLI accepts optional `--base-human` and `--advanced-human` JSON run files.
Focused packet/adjudication tests pass **8/8**. This closes a tooling incompatibility,
not the human-reference evidence gate: no human sessions, approved scoring
anchors, completed ratings, or comparative scorecards are claimed.

### Raw response-body integrity — 2026-09-27

The raw-reference audit now requires a non-empty response body for every
case-bound observation (`output` for ELIZA, `response.stdout` for LLM runs,
and `response`/`output` for human sessions), and its top-level human-reference
status now reflects the audited base/expert rows rather than a hard-coded
missing value. Case-ID completeness alone no longer marks an empty run as
complete. Focused raw-audit, packet, and adjudication tests pass **20/20**.
Re-auditing the current v5 ELIZA, two Gemma,
and two Qwen runs yields **3 complete reference classes** with zero missing
response bodies; both human classes remain missing. The status is still
`incomplete`, and no score interpretation is performed.

The current packet's target response rows match the latest target replay
exactly (**74/74**). The empty forms each have **370** rows and contain no
aliases-to-systems mapping. The workflow does not define behavioral scoring
anchors: a reviewed rubric is still needed before these forms are rated.

The current raw audit reports complete v5 collection for ELIZA (**1/1** run),
the CPU small-LLM class (**2/2** runs), and the modern-LLM class (**2/2** runs);
both human classes remain missing (**0/1** each). The raw runs establish
case/protocol coverage only. Their responses are not scored, and these counts
do not establish relative capability.

### Native no-reply-slot accounting — 2026-09-27

The production summary previously counted every empty reply identically. It
now retains the total and separately attributes silence only when the
observation has a graph-authoritative disposition plus the exact non-turn
state that closes a reply slot (blocked, incomplete fragment, or incomplete
typed offer). The fresh 74-event replay has 49 receipt-backed substantive
releases, 16 explicit errors, and 9 empty replies; all 9 are authorized
non-turn no-reply slots (2 blocked, 6 fragments, 1 incomplete offer), with 0
unclassified silence. No reply surface or fixture expectation is used to
assign the category. Phase 8 corpus-runner tests pass **30/30**. Artifact:
[`no-reply-slot audit replay`](../../../evaluation/reports/phase8_corpus_report_20260927_no_reply_slot_audit_v1.json).

### Active-tree packet refresh — 2026-09-27

Rebuilt the packet from the current full-seed v5 target replay and the existing
protocol-matched ELIZA, Gemma 3 4B CPU (two identical runs), and Qwen 3.5 9B
CPU (two distinct runs) references. The new packet contains **74 cases / 370
responses**, has empty scores and evidence notes, excludes system/corpus labels,
and randomizes response aliases per case. The alias key is stored separately
under `/tmp`; it is not in the packet. Packet and adjudication tests pass
**8/8**. A direct join through the private alias map confirms target response
matching at **74/74** against the active-tree replay. Artifact:
[`active-tree blinded packet`](../../../evaluation/reports/phase8_blinded_output_packet_20260927_active_tree_v1.json).
Fresh packet-bound blank forms each contain 370 rows and share this packet's
SHA256; IDs are distinct and all score values remain null:
[`rater A`](../../../evaluation/reports/phase8_blinded_rater_template_20260927_active_tree_a.json),
[`rater B`](../../../evaluation/reports/phase8_blinded_rater_template_20260927_active_tree_b.json).

This refresh makes the output material current and annotation-ready, but the
rubric remains explicitly unapproved and no human ratings or adjudication have
been collected. Base-human and advanced-human references remain missing, so
this artifact does not close comparative evaluation.

### Follow-up target disposition refresh — 2026-09-27

A graph-typed communication-failure path now makes `error_signal` authoritative
without using the fixture label or reply text. The fresh target report records
**68/74** authoritative dispositions (previously **67/74**); the utterance's
observed reply is unchanged, so the existing blinded output packet remains
content-matched. This is an unscored disposition update, not a comparative
result. Grounding and release gates remain unchanged, and owner rubric approval,
two independent ratings, and adjudication are still required. See the
[`typed-failure target report`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_failure_v1.json).

### Compact-index current-tree packet refresh — 2026-09-27

Replayed the active tree after connected-index compaction and rebuilt the
unscored Phase 8 target report. It remains release-blocked: native disposition
authority is **67/74**; grounding is **21 TP / 29 FN / 0 FP** (F1 **0.592**);
production has **50** receipt-backed substantive releases, **14** explicit
errors, and **10** authorized silent slots with zero unclassified silence;
Phase 4 remains **0 complete / 0 eligible / 0 promoted**. No labels or corpus
annotations are used as runtime decisions. Report:
[`current compact-index target replay`](../../../evaluation/reports/phase8_corpus_report_20260927_current_compact_index_v1.json).

Rebuilt a blinded packet from that exact target run and the existing
protocol-matched ELIZA, Gemma 3 4B CPU, and Qwen 3.5 9B CPU raw runs. It has
**74 cases / 370 responses**, all score fields null and evidence notes blank;
the private alias key is separate under `/tmp`. A direct join through the
private key confirms the target response matches the current replay **74/74**.
Raw-reference audit again finds **3 complete classes** and **2 missing human
classes**; it performs no score interpretation. The new material is therefore
current and structurally ready, not behaviorally scored:
[`current blinded packet`](../../../evaluation/reports/phase8_blinded_output_packet_20260927_compact_index_v1.json),
[`raw-reference audit`](../../../evaluation/reports/phase8_raw_reference_audit_20260927_compact_index_v1.json).

The rubric proposal remains unapproved, and there are no base-human or
advanced-human sessions/ratings. Owner approval, two independent blinded
ratings, and adjudication remain required before capability comparison. The
local Ollama daemon was not reachable from this sandbox; this refresh relies
only on the already collected, protocol-matched raw references and does not
claim new model inference.

## Current-tree blinded packet refresh — 2026-09-28

Rebuilt the unscored packet against the current 74-event v5 target replay and
the existing protocol-matched ELIZA, two Gemma 3 4B CPU runs, and two Qwen 3.5
9B runs. The packet contains 74 cases / 370 response tracks, with randomized
per-case aliases, blank score fields, and no system/corpus labels. A private
alias key is stored separately under `/tmp`; it must not be distributed with
the packet. Direct join through that key confirms the current target matches
the packet at **74/74**. Two blank rater forms bind to the same packet digest.

The refreshed raw-reference audit again finds ELIZA **1/1**, small LLM **2/2**,
and modern LLM **2/2** complete; base-human and advanced-human are missing
(**0/1** each). Audit, packet, and adjudication tests pass **20/20**. This
advances packet freshness and integrity only: scoring remains unperformed, the
rubric is unapproved, and the comparative gate remains incomplete pending
protocol-matched human sessions, approved anchors, two independent ratings,
and adjudication. Artifacts:
[blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_learning_context_clarification_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_learning_context_clarification_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_learning_context_clarification_b.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_learning_context_clarification_v1.json).

The target was then refreshed after the graph-selected missing-world
clarification increment. The current packet supersedes the immediately prior
packet above and binds to that exact replay at **74/74**:
[current packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_missing_world_clarification_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_missing_world_clarification_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_missing_world_clarification_b.json),
[target replay](../../../evaluation/reports/phase8_corpus_report_20260928_missing_world_clarification_v1.json).

After the declarative learning-clarification production change, the packet was
refreshed again against the new target. This version supersedes the preceding
one and verifies target identity **74/74**; both current rater forms bind to
one digest. No ratings or scores have been added:
[current packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertainty_context_clarification_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertainty_context_clarification_b.json),
[target report](../../../evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v1.json).

The target was replayed once more after changing learning-request lookup to
message-local graph adjacency; output semantics are unchanged across all 74
cases. The current blinded packet and empty rater forms were regenerated
against that exact report, with a **74/74** target join:
[packet v2](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v2.json),
[rater A v2](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertainty_context_clarification_v2_a.json),
[rater B v2](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertainty_context_clarification_v2_b.json),
[target v2](../../../evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v2.json).

After the settled non-turn blocked-disposition correction, a fresh Phase 8 v5
target replay changes only `blocked_permission` (diagnostic error/withheld
receipt to graph-authorized no-reply). The blinded packet was regenerated
against that exact target and verified **74/74** by the private alias key; both
370-row forms share the packet digest and every score remains blank. No human
reference or rating is added, and the human-comparison gate remains open:
[target replay](../../../evaluation/reports/phase8_corpus_report_20260928_settled_nonturn_block_closure_v1.json),
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_settled_nonturn_block_closure_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_settled_nonturn_block_closure_v1_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_settled_nonturn_block_closure_v1_b.json).

## Current protocol-v5 target and blinded packet — 2026-09-28

A fresh 74-event target replay was run after the latest parser/correction
fixes using the same v5 event-context/history-8 protocol as the available
reference sessions. It records grounding **20 TP / 30 FN / 0 FP (F1 0.571)**,
**54** substantive receipt-backed releases, **6** explicit errors, and **14**
authorized silences. Turn latency is **109.35/189.75/222.76 ms**
median/p95/max (**18/74** over 150 ms). The comparative gate remains blocked
at provenance; Phase 4 remains **3 source / 0 complete / 0 promoted**. This v5
report is distinct from the v4 replay and is the proper target binding for the
existing v5 references. It is not a new memory/resource acceptance run.

The fresh report and the matched-context ELIZA, two Gemma 3 4B, and two Qwen
3.5 9B sessions now feed a refreshed blinded packet with **74 cases / 370
response rows** across five system tracks. The target response joins the
private alias key at **74/74**. System and corpus labels are excluded, scores
remain blank, and two independent **370-row** rater forms bind to the same
packet digest. The private alias key is kept outside the shared reports and
must not be distributed to raters. Raw-reference, packet, and adjudication
tests pass **20/20**. Artifacts:
[v5 target](../../../evaluation/reports/phase8_corpus_report_20260928_current_v5_resource_amended.json),
[blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_current_v5_resource_amended.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_current_v5_resource_amended_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_current_v5_resource_amended_b.json).

This closes the packet protocol-mismatch and freshness gap only. Neither
human class has a protocol-matched session; the rubric remains unapproved,
ratings have not been submitted, and no adjudication or human scorecard
exists. Memory/learning are not comparable under this bounded text-context
protocol. Comparative capability and release remain unproven.

## Current protocol-v5 packet after confirmation-source repair — 2026-09-28

Rebuilt the packet against the subsequent Phase 8 target, which changes the
unbacked `question_ack` repair wording but not its native disposition or
evidence. The packet contains **74 cases / 370 response tracks** and the
private-key join matches target output at **74/74**. Both blank base-human
forms bind to the same packet digest. The raw audit again confirms ELIZA
**1/1**, small LLM **2/2**, and modern LLM **2/2** complete v5 raw runs; both
human reference classes are missing and no scoring was performed. Artifacts:
[target replay](../../../evaluation/reports/phase8_corpus_report_20260928_confirmation_source_repair_v2.json),
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_confirmation_source_repair_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_confirmation_source_repair_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_confirmation_source_repair_b.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_confirmation_source_repair_v1.json).

The comparative gate remains incomplete pending human sessions, approved
rubric anchors, two independent ratings, and adjudication.

## Current protocol-v5 packet after causal-context release — 2026-09-28

Refreshed the target replay after the missing-causal-context production
increment and rebuilt the blinded packet from that exact report plus the
existing matched-context references. The packet still has **74 cases / 370
response tracks**; private-key join verifies the target at **74/74**. Both
blank base-human forms bind to the same packet, and the refreshed raw audit
confirms ELIZA **1/1**, small LLM **2/2**, and modern LLM **2/2** complete raw
runs. It performs no scoring; base-human and advanced-human sessions remain
missing. Packet/adjudication/raw-audit tests pass **20/20**. The current target
is [the causal-context replay](../../../evaluation/reports/phase8_corpus_report_20260928_missing_causal_context_release_v1.json);
packet, forms, and audit:
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_missing_causal_context_release_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_missing_causal_context_release_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_missing_causal_context_release_b.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_missing_causal_context_release_v1.json).

This refresh closes target/packet staleness and confirms the external-model
raw-collection slice only. Rater sessions, rubric approval, two independent
human ratings, and adjudication remain the comparative-evaluation blockers.

## Service-profile Phase 8 recheck — 2026-09-28

The live Phase 8 runner now defaults to the checked-in service's incremental
conversation seed profile; full boot remains an explicit comparison control.
On the fixed 74-event corpus, full, sealed-corpus-prepass, and online
incremental profiles have exact equality on the scored semantic fields,
production receipt semantics, scorecard, grounding, and release summaries.
The online profile selects 74 anchor seeds and loads 22 connected content
provider seeds across 50 first-seen events, reusing cached providers for 24.
Three clean incremental-profile processes peak at **133–135 MiB RSS** and
reach **140.30–146.93 ms** max synchronous turn latency, with all 74 turns
under 150 ms. These measurements describe the SUT profile only; they do not
create new human ratings or a cost-effectiveness score. The comparative gate
still requires approved rubric anchors, protocol-matched human sessions, two
independent ratings, and blinded adjudication.

## Current protocol-v5 packet after settled non-turn correction — 2026-09-28

The latest target replay is
[`settled_nonturn_block_closure_v2`](../../../evaluation/reports/phase8_corpus_report_20260928_settled_nonturn_block_closure_v2.json):
74/74 authoritative dispositions, 55 substantive releases, 5 explicit
errors, 14 authorized silences, and zero unclassified silences. The matching
blinded packet has 74 cases and 370 annotation rows; its recorded private-key
join is 74/74. Direct integrity recheck computes packet digest
`6bcec06abd1c0e0a3092a4598703c71a452a92245aafaba8772b478fe0baa22a` and
confirms both distinct rater forms bind to it with every score blank. Raw
reference, release-gate, and packet tests pass **23/23**. Artifacts:
[`packet`](../../../evaluation/reports/phase8_blinded_output_packet_20260928_settled_nonturn_block_closure_v1.json),
[`rater A`](../../../evaluation/reports/phase8_blinded_rater_template_20260928_settled_nonturn_block_closure_v1_a.json),
[`rater B`](../../../evaluation/reports/phase8_blinded_rater_template_20260928_settled_nonturn_block_closure_v1_b.json).

This refresh verifies target/packet integrity only. Base-human and
advanced-human sessions, approved rubric anchors, submitted ratings, and
adjudication remain absent; no comparative capability score or release claim
is available.

## Current v5 packet after the 2026-09-29 release-engine cognition update

The current release-engine target replay and same-protocol raw references were
used to refresh the blinded packet: 74 cases / 370 responses, randomized
per-case aliases, no target/reference/corpus labels, and all five score fields
and evidence notes blank per row. Both blank rater templates bind to packet
SHA-256 `078c7c86b97db92815d87ecca86f32dae96b62d35c3a645742ae335ea5280443`.
The private-key join confirms the blinded target track matches the current
target replay **74/74**.
The private alias key is stored separately at `/tmp/phase8_blinded_output_key_20260929_release_current_v5.json` and must not be distributed. Packet and both forms are current to the
**65.10 / 130.29 / 145.72 ms** release-engine Phase 8 v5 replay. Raw-reference
audit finds ELIZA, small LLM (two Gemma CPU runs), and modern LLM (two Qwen CPU
runs) complete; base-human and advanced-human remain missing (**3 complete
raw classes / 2 missing**). Audit, packet, and adjudication tests pass
**20/20**. Artifacts: [packet](../../../evaluation/reports/phase8_blinded_output_packet_20260929_release_current_v5.json),
[rater R1](../../../evaluation/reports/phase8_blinded_rater_template_20260929_release_current_v5_r1.json),
[rater R2](../../../evaluation/reports/phase8_blinded_rater_template_20260929_release_current_v5_r2.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260929_release_current_v5.json),
[target replay](../../../evaluation/reports/phase8_corpus_report_20260929_release_current_v5.json).

This packet is ready for independent scoring but has no ratings. Rubric-anchor
approval, two independently completed forms, and adjudication are still
required. The local Ollama CLI exists, but its localhost service socket is
inaccessible in this managed sandbox; historical Gemma/Qwen runs are reused
as protocol-matched raw observations and no new inference is claimed. The
comparative gate remains blocked, and model-output scoring alone cannot supply
the two missing human reference classes or memory/learning dimensions.

## Current v5 packet after language-neutral event selection — 2026-09-29

The latest target replay uses the neutral `selection_target_kind=rule`
arbitration path. Its current Phase 8 report records 74/74 authoritative
dispositions, 54 substantive releases, and 15 authorized silences. The
refreshed blinded packet has 74 cases / 370 response rows; the private alias
map verifies target identity 74/74, and both blank rater forms bind to packet
SHA-256
`8543fcf5f8e34795ffe1b05f7927b724999b037cec014c733a036076da93bb63`.
Artifacts: [packet](../../../evaluation/reports/phase8_blinded_output_packet_20260929_neutral_selection_v1.json),
[rater R1](../../../evaluation/reports/phase8_blinded_rater_template_20260929_neutral_selection_r1.json),
[rater R2](../../../evaluation/reports/phase8_blinded_rater_template_20260929_neutral_selection_r2.json),
[target replay](../../../evaluation/reports/phase8_corpus_report_20260929_neutral_selection_target_v1.json).
Ratings remain blank: rubric approval, two independent ratings, and
adjudication are still required, so this refresh makes no comparative score
claim. Phase 4 still has zero complete tuples; strict maximum-latency
repeatability and full multilingual surface-production parity also remain
open. Functional-substrate establishment continues as a concurrent workstream.

## Current v5 packet after async multilingual completion (2026-09-29)

Refreshed the blind packet against the source-current Phase 8 v5 report after
the multilingual async production bridge. It contains **74 cases / 370
response rows**; the private-key join verifies the target response on **74/74**
cases. Two independent blank rater forms bind to packet SHA-256
`a25f9f3cef165fb08af721be45755c1772ef5de2fe5dccdf20b0e4385377b70b`, with all
score fields and evidence notes empty. The private alias key is stored outside
the repository at `/tmp/phase8_blinded_output_key_20260929_async_multilingual_completion_v1.json`;
it must not be distributed with the packet. The refreshed raw audit reuses the
audited v5 ELIZA, two Gemma, and two Qwen runs: **3 reference classes complete
raw / 2 human classes missing**, with no score interpretation. Packet,
adjudication, and raw-audit tests pass **20/20**. Artifacts:
[target report](../../../evaluation/reports/phase8_corpus_report_20260929_async_multilingual_completion_v1.json),
[blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260929_async_multilingual_completion_v1.json),
[rater R1](../../../evaluation/reports/phase8_blinded_rater_template_20260929_async_multilingual_completion_v1_r1.json),
[rater R2](../../../evaluation/reports/phase8_blinded_rater_template_20260929_async_multilingual_completion_v1_r2.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260929_async_multilingual_completion_v1.json).

This removes stale target binding only. The packet remains unscored; approved
rubric anchors, protocol-matched base-human and advanced-human sessions, two
submitted independent annotations, and adjudication are still absent. The
comparative capability gate therefore remains blocked.

## V4 default-protocol diagnostic after correction — 2026-09-29

This diagnostic report used the runner's default **v4** protocol; it is not
v5 evidence. The report is
[here](../../../evaluation/reports/phase8_corpus_report_20260929_overlap_index_hint_v1.json).
Its normalized behavior fields match the preceding post-correction report:
**21 TP / 29 FN / 0 FP**, **54 substantive / 15 authorized silent / 0
unclassified**, and Phase 4 **0 complete / 0 promoted**. Its v4 synchronous
call latency is **105.56 ms median / 211.21 ms p95 / 242.41 ms max**, with
**21/74** over 150 ms; latency acceptance remains open.

All 74 reply strings are byte-identical to the target track used by the
preceding async-multilingual blinded packet, so that packet's target response
track remains current; this was checked on per-event `reply` and
`reply_present` fields. The packet still has blank ratings. The raw audit still
has **3 reference classes complete / 2 human classes missing**, and no
independent ratings or adjudication have been submitted. The comparative
capability gate remains blocked; this replay adds no comparative score.

## Current report after typed cue-overlap scoping — 2026-09-29

The final seed 1.1.3 target replay was collected twice under the explicit v5
protocol:
[run 1](../../../evaluation/reports/phase8_corpus_report_20260929_typed_cue_overlap_population_v5_v1.json),
[run 2](../../../evaluation/reports/phase8_corpus_report_20260929_typed_cue_overlap_population_v5_v2.json).
Its normalized behavior remains **21 TP / 29 FN / 0 FP**, production **54
substantive / 15 authorized silent / 0 unclassified**, and Phase 4 **0
complete / 0 promoted**. Synchronous latencies are **108.85 / 124.75 ms
median**, **203.61 / 216.62 ms p95**, and **267.88 / 271.70 ms max**; **19 /
22 of 74** calls exceed 150 ms.

Per-event target reply strings remain unchanged from the preceding blinded
packet's target track. The packet's ratings are still blank; the raw audit has
**3 reference classes complete / 2 human classes missing**, with no submitted
independent annotations or adjudication. This source-current replay therefore
does not close the comparative gate or add a capability score.

## Blinded packet refresh after native Argmax optimization — 2026-09-29

The source-current v5 target replay after the native Argmax cache retains the
same normalized behavior (timing excluded) as the previous target, so the
five-system packet was refreshed against that report. The new packet contains
**74 cases / 370 response rows**, includes the same protocol-matched historical
ELIZA, two Gemma 3 4B CPU, and two Qwen 3.5 9B CPU runs, and exposes no system
names or corpus labels. A private alias-key join verifies the target reply
against the current report on **74/74** cases. Both rater templates bind to
packet SHA-256
`31e3c8da9d4d0f10cf89b3680bc2329e9893dd2254100a7ee6868c6875d75407`; all
**370** score rows in each remain blank. Packet/adjudication/raw-audit tests
pass **20/20**.

The local `ollama` client is installed, but its API is inaccessible from this
managed sandbox and no Ollama process/model store is present here. No model was
downloaded and no fresh LLM inference is claimed; prior v5 raw runs are reused
only for the blinded response packet. The packet is ready for independent
human rating, but rubric approval, both human reference classes, submitted
independent forms, and adjudication remain outstanding; capability comparison
is still blocked. Artifacts:
[current Phase 8 target](../../../evaluation/reports/phase8_corpus_report_20260929_argmax_cache_v5_v1.json),
[blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260929_argmax_cache_v5.json),
[rater R1](../../../evaluation/reports/phase8_blinded_rater_template_20260929_argmax_cache_v5_r1.json),
[rater R2](../../../evaluation/reports/phase8_blinded_rater_template_20260929_argmax_cache_v5_r2.json).

## Current target-track parity check after literal-index source replay — 2026-09-29

Checked the current Phase 8 v5 literal-index report against the target track in
the existing Argmax-cache blinded packet by joining event IDs through the
private alias key. All **74/74** target response strings and all **74/74**
response-presence flags match exactly, including the **15** blank authorized-
silence cases. The packet target therefore remains current for this source
replay and need not be regenerated. This verifies target binding only; the
packet still has blank ratings, the raw audit still lacks both human classes,
and rubric approval, independent annotations, and adjudication remain
outstanding. No comparative score is inferred; the release gate remains
blocked.

## Current source packet after action-surface correction — 2026-09-29

Ran the corrected current tree under matched v5 event-context/history-8 and
refreshed the blinded packet. The target replay covers **74/74** events with
grounding **23 TP / 27 FN / 0 FP** (F1 **0.630**), production **54 substantive
/ 15 authorized silent / 0 unclassified**, and Phase 4 **0 complete / 0
promoted**. Median/p95/max event latency is **51.13/95.96/129.01 ms** with
**0/74** over 150 ms in this run; this single run does not close repeatability.

The packet has **74 cases / 370 response rows**, blinded randomized aliases,
no system names or corpus labels, and separate blank R1/R2 forms. It binds the
current target response to the existing protocol-matched ELIZA, two Gemma 3
4B CPU, and two Qwen 3.5 9B CPU raw runs. The raw audit confirms **3 reference
classes complete raw / 2 human classes missing**, with no score interpretation.
Packet, adjudication, and raw-audit tests pass **20/20**. Human reference
sessions, rubric approval, independent submitted ratings, and adjudication
remain absent, so comparative acceptance remains blocked. No model was
downloaded or newly inferred in this refresh. Artifacts:
[current v5 target](../../../evaluation/reports/phase8_corpus_report_20260929_hatch_surface_v5_v1.json),
[blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260929_hatch_surface_v5.json),
[rater R1](../../../evaluation/reports/phase8_blinded_rater_template_20260929_hatch_surface_v5_r1.json),
[rater R2](../../../evaluation/reports/phase8_blinded_rater_template_20260929_hatch_surface_v5_r2.json),
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260929_hatch_surface_v5.json).

### Repeated connected-profile latency check

Four independent v5 full-corpus connected-prepass target runs on the same
source have **0/74** events above 150 ms; their maximum event times are
**129.01, 143.24, 126.01, and 125.21 ms**. The normalized target outputs
match exactly, so the blinded packet remains bound to all four runs. This
meets the strict per-event limit across this fixed profile but does not prove
full-boot, socket-level, or arbitrary-workload latency. Phase 7's current
connected-profile replay independently stays under the 150-MiB ceiling at
**113,860,608 bytes**; broader production, Phase 4, and comparative-human gates
remain open. Reports: [Phase 8 run 1](../../../evaluation/reports/phase8_corpus_report_20260929_hatch_surface_v5_v1.json),
[run 2](../../../evaluation/reports/phase8_corpus_report_20260929_hatch_surface_v5_repeat2.json),
[run 3](../../../evaluation/reports/phase8_corpus_report_20260929_hatch_surface_v5_repeat3.json),
[run 4](../../../evaluation/reports/phase8_corpus_report_20260929_hatch_surface_v5_repeat4.json).

## Current unavailable-action target packet — 2026-09-30

Refreshed the blinded packet against the latest Phase 8
[`unavailable-action acknowledgment report`](../../../evaluation/reports/phase8_corpus_report_20260929_unavailable_action_ack_v1.json), which releases “understood” for `refusal_unknown` while native disposition remains blocked. The packet binds the current target to the protocol-matched raw ELIZA, Gemma 3 4B CPU (two runs), and Qwen 3.5 9B CPU (two runs): **74 cases / 370 response rows**, randomized per-case aliases, no system names or corpus labels. New blank R1/R2 forms are bound to this packet. The current [raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260930_unavailable_action_ack_v1.json) confirms **3 complete raw classes / 2 human classes missing**, with no score interpretation. The comparative gate remains open pending approved rubric, both human reference sessions, independent annotations, and adjudication. No new model inference or capability score is claimed.

The raw-reference audit now accepts an explicitly typed collection key when a run's optional `system` field is JSON `null`; a contradictory non-null identity remains a failure. Packet, adjudication, and raw-audit regression tests pass **22/22**.

Artifacts: [blinded packet](../../../evaluation/reports/phase8_blinded_output_packet_20260930_unavailable_action_ack_v1.json), [private join key](../../../evaluation/reports/phase8_blinded_output_key_20260930_unavailable_action_ack_v1.json), [R1](../../../evaluation/reports/phase8_blinded_rater_template_20260930_unavailable_action_ack_v1_r1.json), [R2](../../../evaluation/reports/phase8_blinded_rater_template_20260930_unavailable_action_ack_v1_r2.json).
