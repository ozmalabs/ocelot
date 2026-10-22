# Sleep stage and reusable-library contract

**Status:** P13.01 contract freeze. This document specifies a cognition-on,
opt-in lifecycle. It does not claim that staged sleep or library reuse is
implemented or effective; P13.02–E3 must establish that separately. The
existing `ConsolidationSchedulerPolicy` remains disabled by default and stays
the sole producer of offline `MemoryCycle` work.

## Ownership and ordered stages

One owner may advance a given cycle at a time. The scheduler owns cycle entry,
idleness checks, cooldown and the one shared `ThinkingBudget` debit for cycle
admission. The existing EWM `memory_replay` task set owns episodic replay and
its replay receipt; sleep delegates to it once and never implements a second
episode selector or replay pass. Subsequent stages run only from the
immediately preceding stage's completed, current-cycle receipt:

1. `replay`: delegate one selected replay to the EWM owner; record selected
   episode and replay receipt.
2. `consolidate`: consume that replay receipt to update semantic support under
   existing EWM semantics. Replay itself is not a retention or learning claim.
3. `decay`: call existing decay/demotion semantics once for the stage epoch;
   never delete protected or disconfirming evidence to improve compression.
4. `library`: propose a bounded reusable chunk from verified processes/traces;
   count definition, references, decoder, exceptions, retrieval and
   validation cost. Keep it only if verified total description/work cost
   falls, with all source evidence retained.
5. `recombine`: issue advisory candidates only. Any candidate is inert until
   ordinary native verification and adoption gates produce their own receipts.

Each stage has a stable key `(cycle_id, stage, stage_epoch, input_digest)` and
at most one terminal receipt. A receipt binds owner, cycle, stage, input
digest, model/seed epoch, budget debit, status and output identities. Retries
with the same key resume or return the existing receipt; they do not repeat
the debit or side effect. A changed input digest or model epoch cancels the
stale continuation and requires fresh work authorization.

## Interruption, checkpoint and budget

Foreground demand, urgency, or salient external input interrupts offline work
before the next atomic stage operation. The active stage is either not begun,
or its atomic result and receipt are committed together; partial writes may
not be exposed as complete. The cycle stores a cursor and exact pending stage
key. On quiet resumption, the same key is resumed, completed receipts are
skipped, and only a newly admitted stage may debit the shared budget. The
foreground action path has priority and must never wait for the whole sleep
cycle. Interruption itself costs no offline-stage debit.

One shared `ThinkingBudget` funds admission and later bounded stage requests;
no stage maintains a private balance. Each request is identified by cycle,
stage and input digest. A denial creates no stage output. Retry after refill
must be idempotent for any already completed stage. Work, debit, and refund
policy are recorded in the receipt; completed work is never refunded or
charged again after restart. The P13 evaluation must count total compute and
storage for both full-sleep and comparison arms.

## Evidence and compression rules

Observed episodes, negative outcomes, counterexamples and provenance remain
protected records. Decay may change accessibility/status only according to
its existing policy; it cannot turn recalled, predicted, replayed or
consolidated content into observed evidence. A library definition carries
links to every verified source process and equivalence witness. Cost includes
the definition plus each use/reference, decoder, dispatch, exception and
verification overhead. Compare complete package cost and subsequent native
work against the uncompressed traces. Do not count node reduction, support
count, replay completion, or stored schema count as learning or savings.

Strategy-yield records are descriptive evidence, not proof of correctness.
They bind the problem signature, strategy/process identity, environment/model
epoch, attempted work, observed outcome receipt and sample count. Retrieval
returns candidates; existing native preconditions, action authorization,
verification and fallback search remain mandatory. Missing, stale or
incompatible records produce bounded cold-start search.

## Evaluation contract and unresolved measurements

The frozen panel must include 200 paired learn→idle→interference→delayed-test
streams for full sleep, P1 replay-only, matched-compute awake rehearsal and
no-offline controls, plus 100 interrupt/restart controls. Primary thresholds
remain delayed accuracy gain ≥10 percentage points over replay-only and
new-task loss ≤2 points. Foreground starvation, double debit and ungrounded
consolidation must each be zero. Library reuse must reduce held-out primitive
or exact-verifier work by ≥25% after all retrieval/decoder/storage costs.
Report incomplete or unsupported adapters as such; do not replace missing
results with mechanism counts. Preserve any failed benefit and do not rerun or
tune a frozen holdout.

The existing scheduler has no resumable multi-stage cursor, atomic receipt
protocol, interruption handoff, library compression stage, or strategy-yield
store. These remain P13.02–P13.04 implementation requirements. Human comparison
is unavailable unless a matched protocol is separately preregistered.

### Decay adapter boundary

The current `staleness_decay` and `demotion_hierarchy` rules are attached to
`Retina` (`HeldDecayParams`/`HeldTierParams`, `HeldSurfaceCell` and
`HierTrace`). They do not decay `Episode` or `SemanticSupport` records, so
P13.02 cannot claim episodic decay by merely loading those seeds or replaying
their retina rules. The sleep implementation must add an explicit
graph-native, once-per-epoch decay adapter for memory records, preserve their
source/provenance and disconfirming links, and test that decay changes only
derived accessibility/freshness (never observed status or evidence content).
If the adapter cannot preserve those invariants, the decay stage must abstain
and the limitation must remain open rather than deleting or rewriting evidence.
