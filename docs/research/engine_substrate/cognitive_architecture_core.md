# Executable cognitive architecture core

This upgrade turns several neuroscience-informed descriptions into executable
graph mechanisms. The agent remains the Rust-executed graph. Python only
registers and loads manifests or translates world I/O.

## Closed cognitive loop

1. Grounded observations create current `BeliefState` evidence.
2. One-shot episodic binding retains event, context, schema, state content,
   uncertainty, and provenance.
3. Gated working memory admits a bounded task context and can route selected
   content through the functional broadcast bottleneck.
4. `TransitionHypothesis` nodes project action-conditioned successor beliefs,
   observations, outcomes, and features into bounded `PredictionTrajectory`
   branches.
5. Default-mode cognition recruits the world-model area and runs those
   trajectories during low external demand.
6. Applied actions create efference copies and predicted sensory consequences.
7. Verified receipts produce sensory residuals and signed prediction errors.
8. Bounded eligibility traces assign credit to state, action, controller, and
   attention selections.
9. Replay and reconsolidation update semantic support, controller values,
   forward models, and transition confidence.

Perceived, remembered, predicted, replayed, and imagined material remain
distinct. Only grounded perceived events may become autobiographical episodes
or revise predictions. A status label without a verified receipt cannot drive
adaptive value learning.

## Decision and risk architecture

Irreversible or externally consequential actions are represented as co-present
graph candidates: `wait`, `refine`, and `commit`. A decision establishes a
context-specific future manifold. When an acceptable shape is defined, each
candidate carries a projection of that shape. When only bounds are defined,
as in the F-16 proving-ground experiment, each candidate instead supplies its
own projected path through the bound tube. Execution chooses the minimum sufficient
action/intervention that preserves the defined shape or keeps the projected
path inside the bounds; goals
only break equal-intervention ties. Width, information loss, and time bounds
are explicit and changes are explicit transitions. Hard safety vetoes and
external approval remain separate, non-tradeable host boundaries. The F-16 is
one proving ground, not the scope of the architecture.

The engine computes retained, lost, and escape residuals at every projected
time slice rather than accepting scalar caller claims. The
time/width/information-loss triangle bounds each residual, while path or shape
coordinates and their topology links are preserved and audited. The current gate enforces
the applicable containment residual within each assessment, not persisted lineage across
assessments. Manifold momentum is nonphysical cross-decision continuity when
longitudinal callers reuse an established manifold; identity or bounds changes
must be represented as explicit transitions by those callers.

Prediction is temporally foveated. A producer starts with the dense near
field and spends further model time only while containment remains unresolved.
Earliest bound crossing resolves immediately. Without a defined terminal
shape, early path retention requires the held-action transition to reach an
exact model fixed point; otherwise a computation ceiling is a fail-closed
limit, never evidence of retention. The projection model is the graph's
analysis-by-synthesis model; a plant or simulator outcome may update it only
after the selected action and is never forked for candidate evaluation.

## Core seeds

- `episodic_working_memory_core` implements contextual episodic binding,
  conservative cue completion, reconsolidation, prioritized wake/offline
  replay, replay-driven semantic support, and four-slot gated working memory.
- `generative_world_model` implements belief states, ranked
  action-conditioned transition hypotheses, bounded content-bearing rollouts,
  dead-end terminalization, expiry, and prediction-error revision.
- `adaptive_control_core` implements controller-specific value learning,
  receipt-gated temporal-difference errors, eligibility traces, separated
  expected noise/volatility/model ignorance, forward-model calibration,
  allostatic forecasting, skill-option proposals, and TTL-bounded functional
  broadcast.
- `default_mode_core` recruits content-bearing world simulation and uses
  deterministic source arbitration when multiple goals or episodes compete.

These seeds are part of `CORE_SEEDS` and the frozen cognitive core. Their
transient nodes have explicit deadlines or retention epochs; durable learned
models and semantic support survive transient cleanup.

## Concurrency invariants

- Simultaneous working-memory inputs are serialized before capacity checks.
- Simultaneous default-mode sources select one deterministic context.
- Broadcast priority ties refuse rather than silently use graph order.
- Rollout branches are bounded by branch count, horizon, budget, and deadline.
- A rollout leaf with no applicable transition terminalizes explicitly.
- Core boot remains quiescent without world input.

The cross-faculty contracts are pinned in
`tests/test_cognitive_architecture_integration_migrated.py`.
