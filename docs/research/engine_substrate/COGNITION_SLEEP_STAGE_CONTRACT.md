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
immediately preceding stage's terminal, current-cycle receipt (completed or
explicitly deferred):

1. `replay`: delegate one selected replay to the EWM owner; record selected
   episode and replay receipt.
2. `consolidate`: consume that replay receipt to update semantic support under
   existing EWM semantics. Replay itself is not a retention or learning claim.
3. `decay`: update derived memory accessibility/freshness once for the stage
   epoch; never delete protected or disconfirming evidence to improve
   compression.
4. `library`: once implemented in P13.03, propose a bounded reusable chunk
   from verified processes/traces; count definition, references, decoder,
   exceptions, retrieval and validation cost. Keep it only if verified total
   description/work cost falls, with all source evidence retained. Until then,
   this stage writes a deferred receipt and makes no library claim.
5. `recombine`: issue advisory candidates only. Any candidate is inert until
   ordinary native verification and adoption gates produce their own receipts.

Each stage is identified by the cycle's unique scheduler epoch, stage name and
stage epoch, with input identity carried by graph edges to the replay,
semantic support and preceding stage receipt. There is at most one active
cursor and one receipt per stage on a cycle. A receipt binds stage, cycle and
stage epochs, model epoch, budget debit, status and input/output links. Cursor
advancement, receipt creation and debit are one graph-rule effect, so retries
cannot repeat the debit or side effect. A model-epoch mismatch cancels the
stale continuation and requires a newly scheduled cycle.

## Interruption, checkpoint and budget

Foreground demand, urgency, or salient external input interrupts offline work
before the next atomic stage operation. The active stage is either not begun,
or its atomic result and receipt are committed together; partial writes may
not be exposed as complete. The cycle stores a cursor and exact pending stage
key. On quiet resumption, the same key is resumed, completed receipts are
skipped, and only a newly admitted stage may debit the shared budget. The
foreground action path has priority and must never wait for the whole sleep
cycle. Interruption itself costs no offline-stage debit.

One shared `ThinkingBudget` funds cycle admission and later bounded stage
transitions; no stage maintains a private balance. Each stage debit is keyed by
the cycle epoch, stage name and stage epoch, with input identity provided by
the linked prior receipt/evidence. An unaffordable stage leaves the cursor and
graph outputs unchanged. Retry after refill is idempotent for any already
completed stage. Work and debit are recorded in the receipt; completed work
is never charged again after restart. The P13 evaluation must count total
compute and storage for both full-sleep and comparison arms.

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

P13.02 adds the graph-resident cursor, atomic stage receipts, foreground
gating, shared-budget stage debits, checkpoint-resumable state, a derived
episodic-support freshness adapter, and advisory recombination. P13.03 now
consumes the deferred library receipt only when its disabled-by-default policy
is enabled. Its mechanism fixture learns an exact repeated `SolveTask.trace`
sequence, checks the native composition against both solved source tasks,
records a compressed alternate trace with a witness, and includes definition,
reference, decoder, exception, dispatch, retrieval and validation units in the
cost comparison. P13.04 adds disabled-by-default strategy entries from solved
task traces, structure and epoch matching, SoftWeights over observed yield,
per-step native application receipts and bounded-solver fallback. These are
mechanism fixtures on graph-held task traces; held-out benefit and profile
readiness remain unestablished for P13.E1–E3. Human comparison is unavailable
unless a matched protocol is separately preregistered.

### Decay adapter boundary

The current `staleness_decay` and `demotion_hierarchy` rules are attached to
`Retina` (`HeldDecayParams`/`HeldTierParams`, `HeldSurfaceCell` and
`HierTrace`). They do not decay `Episode` or `SemanticSupport` records. P13.02
therefore adds a separate graph-native adapter on `SemanticSupport`: it stores
`sleep_freshness`, `sleep_accessibility`, and `sleep_derived_uncertainty` from
the support's last update epoch and the policy half-life. The original
uncertainty, source episode, provenance and observed event are not rewritten;
the derived fields are not yet wired into retrieval. This is mechanism evidence
only. Any later consumer must preserve those boundaries, and decay must abstain
if it cannot do so.

`SleepRegimePolicy.model_epoch` is the cancellation seam. A producer that
changes the learned model must advance that epoch; the next cycle sees a
mismatch with its stage receipt and enters `canceled` before further stage
work. No generic model-epoch producer is added in P13.02, so automatic
invalidation from unrelated graph mutations remains unestablished.
