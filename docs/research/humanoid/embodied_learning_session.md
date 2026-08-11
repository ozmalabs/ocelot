# Embodied learning session

`embodied_learning_session` is a coordination seed, not a second motor or
development system. It creates one persistent `EmbodiedLearningSession` for a
published `EmbodiedDevelopmentEpisode`, `EmbodiedBodySchema`, and
`EmbodiedLearningWorld`. It then links the already-owned interfaces:

- `embodied_development`: selected `LearningPlanStep`, active order-N `Goal`,
  developmental capability frontier, and selected reset scenario;
- `embodied_motor_priors` / `embodied_motor_program`: an existing motor prior
  and program, without decoding or selecting their opaque actuator contents;
- `counterfactual_experiment`: an `Experiment` with
  `epistemic_scope=graph_counterfactual`; detached cognition injects the
  graph-selected motor program and projects its learned integer consequence
  coordinates. Its imagined result remains non-oracular and requires outside
  validation;
- a world adapter: only publishes an `EmbodiedPoseAffordance`, then later
  attaches `EmbodiedExternalTrialEvidence` to an already-authored request;
- `cognitive_pareto`: receives three separate, verified integer coordinates
  from grounded evidence: goal progress, negative energy cost, and negative
  peak load. No scalar reward is formed.

## Recurrence after a trial

The session retains every external observation rather than treating it as a
terminal callback. When the world publishes an exact grounded evidence record
and its request/program/pose/reset-scenario/goal provenance links, the graph
closes an `EmbodiedLearningTrialReceipt`. That receipt is simultaneously:

- a causally closed `has_embodied_development_receipt` for the developmental
  DAG and embodied-instruction confirmation path;
- provenance for an `EmbodiedLearnedConsequence`, while the program's integer
  consequence coordinates and experience count are updated from the observed
  values;
- the source of `EmbodiedDevelopmentalEvidence`; only positive measured
  progress adds one capability success unit, while all outcomes remain
  retained as evidence;
- an audited learning check-in that closes the used reset request and asks the
  developmental graph for a fresh request for the already selected scenario.

Closing the receipt marks the completed counterfactual as validated. This
releases the session rule to request a new graph counterfactual rehearsal;
after that rehearsal, the normal affordance/reset gate creates the next
external trial. The generic cognitive supervisor observes each newly requested
external trial and re-arms host work after its prior receipt, so the loop has
no host-side cadence or fixed attempt limit. Program/goal/plan selection stays
with the developmental plan and its Pareto machinery; the session only
preserves evidence and reconnects the next graph-selected cycle.

The program's `predicted_*_units` are intentionally a fast learned default:
each new exact observation replaces those coordinates for the next detached
rehearsal. This does not discard history: every update also retains a separate
receipt-grounded `EmbodiedLearnedConsequence`. A future graph-held estimator
can consume that history without changing the world adapter or inventing a
non-integer aggregate.

An external trial request is emitted only after the graph holds all of: an
active goal, an integer-native selected program, a completed detached rehearsal,
an enabled pose affordance, an active reset request, and the developmental
seed's selected reset scenario. The adapter never
chooses a program, scenario, or outcome; it performs external I/O and writes
the observed integer evidence.

`WorldAdapter(seeds=("embodied_learning_session",))` resolves the dependency
closure from the manifests themselves. Full daemon boot obtains the same
ordering from `load_all_seeds`.
