# Generic motor decision collapse

`motor_decision_collapse` extracts the reusable mechanism demonstrated by
Bigville's conduct collapse without importing Bigville's social vocabulary or a
robot body's kinematics.

The agent remains a graph running in Rust. Body-specific graph rules expose
opaque options and arm a decision state; the world adapter only transduces raw
state and enacts the published opaque command.

## Graph protocol

A `MotorDecisionState` is attached to the agent by
`has_motor_decision`. Its candidate set is exactly the set union of:

- `state -in_scene-> DecisionOption`
- `state -in_episode-> DecisionOption`

No global `NodesOfType` scan occurs. Two agents, residents, robots, limbs, or
episodes can therefore share a substrate without seeing one another's options.
An option linked through both edges is deduplicated by `Union`.

Each option holds only domain-neutral decision evidence:

- `token`: opaque external identity;
- `ordinal`: stable mechanical enumeration used only to total-order ties;
- `available`: graph-held availability;
- `default_value`: fast prior before experience;
- `learned_value` and `decision_experience_count`: internalized fast evidence,
  deliberately separate from a plant model's causal `experience_count`;
- `grounded_value`: the active deeper valuation.

The core does not define how those values are observed. A robot forward model,
a conduct consequence model, or another graph faculty can write them.

## One collapse, two depths

`mdc_fast_propose` performs the order-0 proposal. Experienced options use
`learned_value`; novel options use `default_value`. An exact value tie settles
by lowest ordinal, never graph insertion order or a semantic action label.

The scalar residual is the larger of the proposal's local prediction mismatch
and a rank-reversal signal relative to the best currently grounded option:

```text
max(
  abs(proposed_fast_value - proposed_grounded_value),
  if best_grounded_value > proposed_grounded_value:
      settle_tolerance + (best_grounded_value - proposed_grounded_value)
  else:
      0,
)
```

The raw positive difference is retained as `counterfactual_regret`. Lifting any
strict rank reversal above the tolerance is important because body-specific
cost units are arbitrary: a numerically small reversal can still select the
wrong rotor or joint action. A fast habit may settle shallowly only while it is
also the current grounded winner.

There is no separate escalation policy. Only a residual above
`settle_tolerance`, while `deeper_enabled == 1`, authorizes
`mdc_residual_authorized_deepen`. The deeper face evaluates the same scoped
options by grounded value. `rationalise_gain` is retained from Bigville: when
non-zero, fast value can bias deeper valuation rather than assuming active
cognition is automatically unbiased.

If the residual is already within tolerance, `mdc_shallow_settle` commits the
proposal directly. Setting `deeper_enabled = 0` is the falsifier/control that
caps the collapse at order zero.

## Settle-back and internalization

After a deeper collapse, the two scoped internalization rules move the fast
proposal and grounded winner toward their grounded values:

```text
learned += internalization_gain * (grounded - learned)
```

This is contrastive action credit: the rejected proposal learns from its
counterfactual error and the selected action learns its grounded value;
unselected non-competitors do not receive fictitious experience. The update is
stamped with `decision_epoch`, making it idempotent when an option is both
`in_scene` and `in_episode`. `mdc_finish_internalization` exposes `done = 1`
only after both relevant options have settled back (one option when proposal
and winner are identical).

Repeated presentation therefore produces the Bigville automation signature:
initial default proposal, residual-authorized deeper correction, decreasing
residual, then the corrected option proposed directly by order zero.

## Domain-neutral embodied episode bridge

An embodied faculty does not need to reproduce the lifecycle above. It exposes:

```text
agent   -has_embodied_motor_episode-> episode
episode -has_motor_decision_option->  DecisionOption
```

Option exposure provisions one dormant `MotorDecisionState` per episode and
copies the exact exposed set onto its `in_episode` scope. This provisioning is
graph-authored and normally happens before the graph authors a request. The
episode then opens that reusable slot with:

```text
decision_request_epoch = monotonically newer epoch
decision_armed         = 1
```

The policy defaults (`settle_tolerance`, depth, internalization gain and
rationalization gain) live on the graph's `MotorDecisionPolicy`. The opening
rule refuses to arm until the provisioned scope count equals the episode's
exposed option count. The ordinary collapse rules then run unchanged.

Once settled, `mdc_episode_publish_once` copies only an opaque verdict and its
audit trace back to the episode:

- `selected_option_ref`, `selected_token`, `selected_ordinal`, `selected_via`;
- `decision_residual`, `decision_order`, `decision_deepened`;
- `selected_decision_epoch`, `last_published_decision_epoch`;
- `decision_status = "published"`.

It also clears `decision_armed`. Publication requires both `done == 1` and
`internalization_complete == 1`. On the deeper path the complete bit starts
false, the proposal and winner must receive the same epoch stamp, and only
`mdc_finish_internalization` can raise it. Consequently no consumer can enact a
deep verdict while its contrastive fast update is half-written.

The episode slot is bounded and reusable:

- a newer epoch resets and rearms the same state;
- a duplicate or older epoch is consumed as `stale_request_ignored`;
- an empty option set is `refused_no_options`, with no fabricated token;
- options no longer exposed are unscoped while the state is inactive;
- an option linked through both generic scopes is still internalized once.

Multi-episode tests put independent episodes in one substrate and verify that
each publishes only from its own options. No Python chooser, lifecycle loop, or
body-specific bridge is required.

`selected_option_ref` is the exact graph node that won the collapse. The token
remains the opaque actuator-boundary identity, but a token alone is not always
enough inside cognition: several context memories may predict the same actuator
under different body states. Publishing the node identity lets the consuming
faculty release the exact grounded exemplar without repeating selection or
ambiguously joining on a token. The publication bridge derives the external
token and ordinal from this authoritative node reference; cached state labels
cannot drift from the winner when the bounded decision slot is reused.

## Embodied consumers

The body-specific seeds now map their existing deterministic costs into
`grounded_value` and use this bridge for ordinary learned competition:

- ground/racecar control exposes learned local action models;
- aerial control exposes learned three-dimensional flight models;
- helicopter control exposes exact contextual energy/viability memories, or
  compact action models before such memories exist;
- humanoid locomotion exposes only the support-phase and body-state-local
  walking-primary experts.

The mapping is `grounded_value = -cost`; the shared core knows nothing about
wheels, rotors, support phases, or contact physics. Each domain stamps every
eligible option with the current request epoch, arms only after the entire
local set is current, and releases only the exact published option reference.

Calibration babble, fallen-body get-up exploration, and damage probes remain
causal experiments. Upright gait recovery no longer bypasses motor-program
synthesis, however. Its residual stays open beside locomotion until the graph
commits one `HumanoidMotorProgram`. That single causal outcome may contain an
arbitrary number of effector members. The exact member set, interaction
residual, response horizon, support context, and receipt are grounded together
as a new program rather than enacted as two multiplexed commands.

The program records `motor_residual_context = "recovery_locomotion"`,
`collapse_kind = "compound_recovery_locomotion"`, and the number of open
residuals present at collapse. Context matching prevents the resulting chunk
from firing as ordinary locomotion merely because its primary actuator token
matches. Repeated structural synthesis can instead reassociate with the exact
grounded compound, providing the motor equivalent of learning a third program
for a practiced combination.

## Bigville compatibility

`seeds/bigville_decision_core.json` remains unchanged. Its `ConductState`,
`DecAction`, native `NetForward`, and `net_collapse` protocol continue to model
the richer compiled-network version and retain every historical test.

The generic seed is an additive core for consumers that hold scalar fast and
grounded option values. It preserves Bigville's invariants:

- one collapse rather than a System-1/System-2 switch;
- residual as the sole depth authorization;
- scoped consideration sets;
- motivated reasoning may ride into deeper valuation;
- deeper results settle back into the fast substrate.

## Rebuilding and checking

```bash
python scripts/gen_motor_decision_collapse_seed.py
pytest -q tests/test_motor_decision_collapse_migrated.py \
  tests/test_bigville_decision_migrated.py \
  tests/test_decision_scoping_migrated.py
```
