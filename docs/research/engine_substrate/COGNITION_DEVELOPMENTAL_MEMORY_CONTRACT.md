# Developmental memory and curriculum contract

**Scope:** P21.01 specification. This contract defines the storage and delivery boundary; it does not claim a retention or curriculum benefit. P21 arms must use the P20 fresh native target learner. P20's mapped-source efficacy remains a failed hypothesis and is not a supported source of learning gain.

## Charged evidence and capacity

Each stream begins with a fixed memory capacity assigned before treatment: 2,048, 4,096 or 8,192 canonical UTF-8 bytes. The sizes are non-efficacy sizing choices and are identical across arms within a stratum. The ledger charges the serialized record, its index/reference, any compressed representation, decoder metadata, exceptions and retrieval receipts. Source records evicted from the ledger are unavailable to all consumers. A test may preserve immutable world receipts in the external evaluator for scoring, but the learner cannot read them after eviction.

Observed transitions and counterexamples carry source, world, model and frame epochs. Compression may create a derived chunk only when it preserves provenance to every source receipt and its reconstruction is validated. The original receipt remains charged while retained; otherwise it is removed from learner-visible storage. Counterevidence is protected from lossy compression. Retrieval creates an auditable copy/reconstruction under the same capacity and charges decode/retrieval work to the shared ThinkingBudget. A rejected, missing, stale or over-capacity item cannot be silently read through host state.

All arms use the same deterministic admission, byte accounting, eviction, retrieval and forgetting implementation. Treatment differences are limited to the registered offline replay/consolidation steps and curriculum selector. The memory adapter performs serialization and storage only; native graph rules select what to retain, replay, retrieve or train on. No separate Python policy may repair a failed task or choose its answer.

## Interference and delayed tests

The stream order is fixed before the draw: acquire source-task receipts, enter an idle interval, deliver the common interference block, perform the registered offline treatment, then deliver a novel delayed task through the native learner. The delayed task identity and labels remain evaluator-only until the external world emits a receipt. The three capacity strata cross the same workload and task pool; none is selected from treatment results. Capacity curves are reported even when every arm is at ceiling or floor.

Sleep-only, replay-only, matched-compute awake rehearsal and no-offline arms receive the same acquired evidence, interference, capacities, retrieval opportunity, fresh learner and primitive-action ceiling. No arm retains uncharged raw traces in a side list or gets a disabled comparator learner. A retained chunk must be used on a later task to count as retrieval. Successful replay, chunk count or graph growth alone is not retention.

## Curriculum delivery

Curriculum evidence is selected natively from eligible training residuals. The emitted task carries no target answer, sealed test ID or held-out label. A mechanical world adapter translates the task specification into an independent training world, returns actual authorized receipts, and passes those receipts to `NativeTargetLearner`. The task outcome is written from those receipts and the learner's observed progress. Random, fixed and residual-selected selectors receive the same task pool, workload, compute and learner. Repeated tasks with no observable progress become terminal and are not reissued from the same evidence key.

No later-test identity, answer, or outcome may influence task creation, selection, replay or compression. The scorecard reports target actions, source-information units, native rule steps, shared-budget debits, serialized and graph memory bytes, evictions, retrieval/decode work, elapsed time and all failures by arm and capacity.

## Registered evaluation and stop conditions

P21.E2 freezes 200 paired learn→idle→interference→delayed-test streams in each of three capacity strata, plus selector ablations on a common generated task pool. The primary sleep criterion is at least a 10 percentage-point delayed learning-curve gain over replay-only with new-task loss at most 2 points. The curriculum criterion is at least a 10-point gain at equal total interactions and work. These criteria are applied independently; a benefit cannot rescue an invalid arm.

Foreground starvation, duplicate debit, uncharged hidden originals, answer leakage, counterevidence loss or unauthorized actions are zero-tolerance structural failures. Any such failure invalidates the affected benefit estimate and blocks phase advancement until repaired. A structurally valid negative result remains a `FAIL`; missing native consumers or non-working matched arms remain `NOT_ESTABLISHED`.
