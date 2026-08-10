# Situated motor fixation

The humanoid controller has no privileged joint-space origin. A simulator load
pose is mechanical initial state, not a cognitive target, and tonic control
holds the configuration currently sensed instead of returning the body to a
stored pose.

Calibration on a static new body uses stable configurations as temporary
experimental fixtures. Before an opaque limb probe, the graph receives a
perception-settlement tick. A supported configuration with motion below a
gravity-and-timestep-derived tolerance may become the current
`HumanoidMotorFixation`. Reobserving the same actuator-resolution shape adds
confidence; reaching another stable shape retains a graph transition between
the two. Raw joint vectors remain attached for precise residual learning.

Every issued trial is linked to a `HumanoidMotorEfferenceCopy` containing the
fixation and selected command. It becomes confirmed only when a later
mechanical receipt matches the issued tokens and response horizon. The receipt
also records command displacement energy and error between the sensed
pre-action configuration and the mechanical command reference.

This is the motor analogue of Photon eye fixation and trans-saccadic memory:
temporary situated frames support controlled experiments, while persistent
knowledge consists of uncertain transitions between frames rather than an
unobserved canonical body pose.

The first full walking run after removing origin-resetting commands is retained
in `results/humanoid_walking_situated_fixation_v1.json`. It passes directed
progress, support alternation, and lateral-drift dimensions, but temporarily
loses support and exceeds the prior aerial-occupancy envelope before recovering
upright. That is recorded as a Pareto tradeoff and an identified curriculum
target, not erased by a scalar pass/fail label.

The configuration-conditioned controller is retained in
`results/humanoid_walking_situated_fixation_v2.json`. It adds exact-basin phase
experts, exact-basin motor-memory recall, confirmation-gated fixation changes,
explicit mechanical-reset receipts, and advancing references for learned
locomotion. Across 600 deployment actions it remained upright, stayed within
the lateral and aerial envelopes, and beat tonic control by 1.42 m. It did not
retain useful net progress or support alternation over the complete horizon:
the local policy converged into a safe non-gait. This is the next curriculum
target.

A subsequent complete primitive-sweep spike found the missing forward basin
quickly (1.14 m and 34 support alternations in 240 actions), but also fell and
exceeded the lateral envelope. That spike was not retained in the controller.
It establishes that the next mechanism must pair each advancing curiosity probe
with a stable return configuration and learn explicit lateral-return programs;
simply increasing exploration or handing lateral deviation to the balance
recovery sheet is not biologically or mechanically adequate.

Motor-sequence consolidation now observes the same asynchronous boundary. A
novel receipt-confirmed predecessor/successor pair is detected on the hard
motor sheet, which graph-authors a scoped request for the embodied integration
sheet. Only that background sheet mints the durable transition. Existing
transitions remain available to the fast controller and are updated from later
receipts without reopening arbitrary cognition. A newly minted edge begins
with zero retrospective fit residual because its forward model is the receipt
that created it, but remains output-null. A later independent occurrence must
measure out-of-sample prediction error before the edge may acquire motor
authority. The difference between that conditional receipt and the endpoint
program's marginal effect is stored separately as contextual novelty: one
prior pseudo-observation whose influence decays under repeated exact receipts,
not a fictitious fit error.

A bounded 205-action diagnostic after enabling stagnation habituation reached
1.07 m of directed progress and 16 support alternations, then crossed the
upright envelope at action 183. Raw balance perception recruited recovery in
that same action; every following action switched from `learned_walk` to
`get_up_explore`. The body had not stood again by action 205. This localizes the
next developmental target: the gait exploration loop is productive, and the
missing capability is now a better stable fallen-body exploration curriculum
and reusable roll/kneel/stand return basins—not another locomotion inhibit.

The recovery curriculum now represents that target directly. A fall mints a
temporary basin from the sensed joint-configuration shape, normalized body
height, vertical alignment, support topology, general body contact, and motion
state. Hands and arms therefore become affordances through observed contact;
the controller does not need a host-authored list of recovery limbs.
Receipt-local singleton effects remain attached to that basin. Once the local
actuator alphabet has been surveyed, the graph composes mechanically distinct
effectors. A compound becomes an open motor program: each firing uses the
body-derived nominal response horizon and verified receipts keep the program
active only while it improves at least one viability dimension without being
dominated. Loss of progress, recovery viability, or the originating basin
terminates it. There is no repetition count or independently growing hold
duration.

Recovery is also no longer reduced to a scalar score. The graph retains height,
vertical alignment, foot support, general contact, motion reduction, normalized
energy, and normalized peak load as separate Pareto dimensions. Current need
may focus one coordinate when selecting from the non-dominated frontier, but it
cannot trade the other coordinates away by adding them together. Singleton
receipts update that local frontier; only a receipt-confirmed compound may mint
a successor basin. This prevents transient contact oscillations from restarting
the complete actuator survey.

Successful basin actions are transferable hints, never inherited authority.
A successor tests its predecessor's best positive action once and learns a new
receipt in the new state. At the explicit lifetime boundary, receipt-positive
basins are stored under the existing exact-decoded body-shape library. A later
lifetime recalls the closest retained height/alignment context, but still has
to verify the suggested action against its present configuration and load.
There remains no canonical home pose.

The older retained
`results/humanoid_recovery_basin_probe_v1.json` result is a pre-Pareto historical
diagnostic. Its reported scalar recovery score must not be compared with the
current controller.

The earlier reproducible baseline remains
`protocols/humanoid_recovery_basin_v1.json`, with its cold/warm artifacts in
`results/humanoid_recovery_path_cold_v8.json`,
`results/humanoid_recovery_path_warm_v8.json`, and
`results/humanoid_recovery_path_library_v8.json`. That experiment established
causal transition reuse, but both lifetimes reached the successor at action 88:
recall selected the right command without shortening the route.

The successor curriculum is
`protocols/humanoid_recovery_successor_curriculum_v1.json`. Its horizon is
derived from four complete post-perturbation actuator surveys, so the 181
physical receipts are a consequence of the discovered 42 non-tonic actuators
and the perturbation point rather than a hidden recovery timeout. The retained
cold result, warm result, and unmodified cold library are
`results/humanoid_recovery_option_cold_v1.json`,
`results/humanoid_recovery_option_warm_v2.json`, and
`results/humanoid_recovery_option_library_v1.json`.

The cold lifetime first surveys the fallen body's local singleton alphabet. A
tonic option then damps the body until the sensed gravity- and timestep-derived
quiet condition is met. The graph compares the remaining height and alignment
deficits with the receipt-measured effect of compatible actuator pairs and
inverse-recruits them; no gain ceiling or fixed repetition count is supplied.
Two candidates are rejected. A third pair, actuators 28+16, is recruited at
19.67 times its survey amplitude. Four condition-terminated firings raise the
body from 0.111 m to 0.132 m and mint the first successor at action 103. Later,
actuators 6+4 are recruited at 13.44 times survey amplitude and form a second,
more vertical double-support basin at action 159. The cold graph retains three
basins and two directed transitions.

A retained option now stores its initiation set separately from the final
receipt that crossed a basin boundary: decoded configuration, support, general
contact, normalized motion energy, response horizon, actuator pair, and learned
recruitment. This matters because the transition-producing receipt may be the
fourth firing of an option, not its launch state. Recalled options are released
only when that initiation context recurs. Their internal trajectory remains
Pareto-valued: temporary loss of support, contact, or quiet can trade against
height or alignment rather than acting as a disguised monotone safety gate.
Fresh receipts still terminate the option when it ceases to approach any
successor dimension or becomes dominated by the local action frontier.

In the warm lifetime the exact quiet double-support initiation set recurs after
tonic settling. At action 90 the graph recalls 28+16 at the stored 19.67
recruitment, holds it open for the same four improving receipts, and mints the
first live successor at action 93—ten controller decisions earlier than cold.
The second successor arrives at action 148, eleven decisions earlier than cold.
Warm learning needs one new composition rather than four, while preserving all
three basins and both transitions. This is the requested shorter trajectory
from better causal structure, not a better value on a collapsed score.

The result is still a developmental precursor, not a completed get-up. Neither
lifetime reaches the upright envelope before the curriculum ends. The learned
second basin is best described as a brace/kneel-like intermediate: it reaches
about 0.18 m, substantial reorientation, and double support. The next honest
target is to continue the same graph-native option discovery from that basin
toward high kneel and stand, while allowing arms and any newly observed contact
effectors to enter the local Pareto frontier.
