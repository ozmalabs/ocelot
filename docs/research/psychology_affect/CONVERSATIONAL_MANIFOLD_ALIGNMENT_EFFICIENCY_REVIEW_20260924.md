# Conversational Manifold Alignment and Efficiency Review — 2026-09-24

## Verdict

The implementation is directionally aligned: cognition-first, graph/provenance
oriented, increasingly language-neutral at the semantic boundary,
event-compatible rather than inherently turn-based, and explicit about failed
generation. It is not yet exit-complete or efficient enough for the declared
runtime envelope.

## Evidence

- Native authority: **11 bound / 171 unbound / 182 total** Python cognitive
  cycle/task calls; audit status `review_required`.
- Grounding: precision **1.00**, recall **0.46**, F1 **0.630**.
- Phase 4: no complete live candidate tuples; `no_candidate` remains honest.
- Phase 7P: native selective readback is deterministic, but cold cost is
  approximately **6.8 s** and **109,969,408 bytes** RSS, exceeding the
  declared `<150 ms` and `<100 MB` limits.
- Phase 8: ELIZA, Gemma 4B, and Qwen 9B raw observations are case-bound;
  human references and blinded adjudication are missing, so release is blocked.
- Missing declared gate files: `test_conversation_continuity.py`,
  `test_deliberative_production.py`, and `test_grammar_inversion.py`.
- Latest recovery evidence: **25 focused tests passed**; the 74-event replay
  remains **36/74** state matches with one graph-owned `question_followup`
  mismatch.

## Alignment findings

Aligned: native arbitration/readback, provenance, explicit error handling,
event-compatible discourse state, non-reply semantic ingress, and reuse of
existing referent, goal, gap-learning, deliberation, and production authorities.
Internal graph statuses named `noted` are gap-state labels, not communicative
output; the production path guards the forbidden surface word.

At risk:

1. The execution plan still describes backchannels/floor-holding fillers as a
   conversational strategy. They must not conceal absent cognition; only an
   explicitly selected graph goal may authorize a holding behavior.
2. The shared English path remains large: `_QUESTION_LEADS`, `_SELF_WORDS`,
   English pronoun/preposition handling, surface token extraction, and English
   production defaults remain in the adapter. The neutral boundary is real,
   but the system is not yet language-agnostic end-to-end.
3. The 171 unbound calls represent real authority-migration debt; comments
   cannot substitute for native binding or explicit mechanical classification.
4. `world_adapter.py` has repeated parse/readback/release seams, increasing
   latency, review cost, and regression risk.
5. Phase 7P must remain yellow while the hard RSS/latency invariant is violated.
6. The worktree has **374** status entries, impairing attribution and efficiency
   conclusions; evidence should remain report-scoped and reproducible.

## Efficiency assessment

The dominant measured cost is substrate/runtime cold allocation, not response
wording. The next optimization should reduce native boot/graph allocation,
while preserving fresh-graph replay, native provenance, and referent
equivalence. Python semantic caching or surface simplification would be
misaligned.

The broad regression run produced 230 passes and three failures before the
latest fixes; those classes were then covered by the 25-test recovery battery.
The broad suite has not been rerun in full afterward, so a repository-wide
green claim is not justified.

## Required next order

1. Keep Phase 7P yellow; profile the substrate cold-allocation boundary.
2. Bind one existing cognitive faculty at a time, with native provenance tests.
3. Further separate the English adapter from neutral semantic ingestion and add
   non-English semantic-provider coverage.
4. Add or explicitly replace the missing declared gates.
5. Measure Phase 4/5 only when complete graph evidence exists; preserve
   unavailable/no-candidate rather than fabricate coverage.
6. Keep Phase 8 blocked until human references and blinded adjudication exist.

## Overall assessment

The architecture is moving in the right direction, but remains intermediate.
The highest-value work is authority consolidation, native cold-path reduction,
and grounded event/world-model coverage—not more dialogue surface work.

## Current audit addendum — 2026-09-24

The earlier figures in this report are historical checkpoints. The latest
native authority audit reports **171 bound / 12 review-required / 183 total**
Python cognitive cycle/task calls, with status `review_required`. The six
newest bindings cover Achieve, agnosia, allocentric view, Bigville
disposition/register, and Marshmallow delay. Their focused behavioral tests
remain green; the Marshmallow and spite suites still fail only their expected
canonical native-binary MD5 discipline assertions.

The current communication/cognition regression slice passed **24 tests in
134.27s** across language-neutral evidence variation, semantic-event
envelopes, deliberation authority, output-null gating, and comparative release
gating. This supports alignment with the cognition-first and non-inherently-
turn-based goals, but is not an end-to-end capability score.

The remaining authority findings are concentrated in Doom ingestion/operation
and pattern-eye paths, Harvest world, and invariant comparison. They should be
handled as existing-substrate integration work, one boundary at a time, with
dependency-gated evidence; no new conversation-layer abstraction is indicated.

Efficiency remains the principal engineering risk. The documented Phase 7P
cold-path measurements still exceed the declared latency/RSS envelope, so the
next optimization target is native substrate warm-up/allocation and selective
readback. A surface-language optimization or a new turn machine would be
misaligned. The worktree currently contains **465** status entries, which is a
process/attribution risk; future evidence should remain narrowly scoped and
report-backed.

## Authority-gate update — 2026-09-24

The native authority inventory has since reached **183/183 bound, 0 findings**
(`status: clean`). This removes the static unreviewed-call debt identified
above. It does not remove the separate runtime-envelope, native-artifact
provenance, dependency-gated world coverage, or comparative human-baseline
gates, so Phase 7 and the overall upgrade remain open.
