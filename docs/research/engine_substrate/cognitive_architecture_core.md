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
