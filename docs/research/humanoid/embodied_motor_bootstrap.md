# Opaque embodied motor bootstrap

`embodied_motor_bootstrap` turns a mechanical body observation into initial
motor candidates without importing anatomical labels or a host-side policy.

The world boundary must publish, as integer-native graph data:

- an `EmbodiedBodySchema` with a `morphology_epoch`;
- one `EmbodiedOpaqueActuatorAffordance` per exactly addressable actuator,
  carrying an opaque `opaque_token`, mechanical `ordinal`, opaque group, and
  tonic-default bit;
- zero or more `OpaqueActuatorBundleAffordance` nodes whose member edges state
  mechanically compatible compound sets; and
- one world-attached `EmbodiedMotorBootstrapContract` holding the observed
  minimum actuation quantum, minimum nonzero activation quantum, and integer
  measurement scales; and
- one or more `EmbodiedMeasurementProjectionAffordance` nodes for the available
  Cartesian readings. They declare what the body can observe, rather than
  multiplying an action by possible later interpretations of one observation.

The graph makes a prior, an `EmbodiedMotorProgram`, and a `ParetoCandidate` for
each singleton/compound. The program maps its member nodes directly to
`simulator_tokens` and aligned `simulator_weight_units`; it takes its first
duration from the observed minimum quantum. One physical enactment returns the
full measured Cartesian displacement vector. Goal projection is a separate
graph operation over that retained vector, so an action is never repeated once
per axis/sign merely to recover values already observed. It does not mint a
label for a limb, direction, or bundle.

All candidates are output-null. The graph first compares the explicit integer
Pareto coordinates—untried structure, topology coverage, and activation
effort. Curiosity selects the least-practised non-dominated candidate, then
uses the mechanically observed ordinal as its deterministic opaque tie-breaker.
Candidate and program identity contain only immutable observed
topology: predictions, duration, and experience are initialized afterwards on
separate graph state, so a receipt cannot accidentally mint a duplicate
program.

Frontier publication requests an immutable `EmbodiedMotorSelectionEpoch`; a
small graph-owned asynchronous transition opens that request as the current
epoch. A receipt-triggered successor request and epoch retain an explicit edge
to the exact grounded receipt that caused them. This makes re-selection causal
and visible: there is no host retry cadence, hidden counter, or ambiguous scan
over retained receipt history. Only the resulting
`EmbodiedMotorBootstrapSelection` connects one program and prior to the
existing `EmbodiedMotorEpisode`; the existing learning-session seed can then
rehearse and schedule it.

When generic cognitive supervision reports a zero-yield, replan-required
window, bootstrap does not let the host choose a replacement action. It first
creates one immutable assessment from the exact newest physical receipt. If
the body expended energy yet produced neither goal progress nor a measured
proprioceptive configuration change, and the program remains below the
mechanically published observation horizon, the supervisor re-enacts that
same program with a binary-widened observation aperture. Otherwise—including
at the horizon—the alternative is the least-practised distinct frontier
program. The alternatives consume opposite values of one assessment, so they
cannot race to issue two actions from one receipt.

A separate immutable enactment event is the only operation that resolves the
supervisory residual and restores process, policy, step, capability, and
episode authority. The same-program temporal enactment has an explicit matcher
because graph bindings are injective; this makes equality of the old and new
program causal data rather than a host-side special case. Thus a historical
receipt can remain inspectable without being able to reopen an already
superseded motor probe.

This seed deliberately does not discover which physical actuators form a safe
compound. That is a body-boundary observation requirement for now. A future
topology learner may publish new `OpaqueActuatorBundleAffordance` nodes from
receipts; it must preserve this same opaque, integer-only interface.

The bootstrap also respects the published mechanical bundle ceiling and keeps
a tonic/default actuator out of a compound when the simulator declares that
constraint. This is an interface constraint, not an anatomical category.
