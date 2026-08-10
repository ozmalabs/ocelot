# Motor-stack latency tiers

Ground navigation, multirotor flight, humanoid movement, and helicopter energy
control now use the same biological scheduling distinction:

| Tier | Motor work |
|---|---|
| `hard_realtime` | immediate body/goal estimation, viability checks, recovery interruption, action selection and release, causal receipt acknowledgement |
| `soft_realtime` | receipt-backed prediction-error integration and forward/controller-model revision |
| `background` | common option-schema exposure, bounded transition memory and later library consolidation |

The distinction is operational. A verified receipt authors or reaches a
graph-held `SystemTwoEscalation`; the shared `adaptive_learning` and
`embodied_sensorimotor` task sets admit the relevant soft and background
areas. Merely changing a latency label would leave the rule outside the
default dual-process cycle.

All four domain seeds depend on `motor_decision_collapse`. Existing opaque
action models expose the common fields `available`, `default_value`,
`learned_value`, `grounded_value`, and `ordinal`. Ordinary learned selection is
now linked into a reusable episode-local `MotorDecisionState`. Each domain maps
its existing deterministic cost to `grounded_value = -cost`, stamps the whole
eligible set with the request epoch, and arms only after the set is complete.
The shared result includes `selected_option_ref`, so release consumes the exact
winning model or contextual memory rather than reselecting by token.

This is a migration of learned competition, not a universal serial bottleneck.
Calibration interventions, damage probes, humanoid balance/gait interrupts,
get-up behavior, and emergency recovery retain direct hard-real-time graph
paths. The shared collapse occupies the learned-choice slot beneath those
interrupts.

Humanoid primitive calibration uses a deliberately narrower graph path:
verified twitches recruit `adaptive_learning` without minting a complete
multimodal episode for every calibration sample. Phase-conditioned movement
continues through the richer shared receipt lifecycle.

That lifecycle is history-bounded without deleting evidence. Verified receipt
epochs advance a graph-held adaptive clock. Once temporal credit is complete,
outcomes move from `has_adaptive_outcome` to an archival edge; expired
eligibility traces are moved similarly. Credit assignment therefore joins
only the live horizon, while receipt, decision, trace, and learned-value nodes
remain traversable through their provenance edges.

Humanoid program expansion and synthesis-fixpoint closure stay on the hard
sheet because they are action construction. Shape-library insertion and
sequence consolidation stay background work. During locomotion, newly
grounded programs remain working motor memory; an explicit lifetime boundary
recruits the shared integration sheet for durable shape-library selection.

## Helicopter lifecycle boundary

Helicopter receipts now use an explicit graph-authored escalation to schedule
local energy-model learning and bounded-intervention memory. A full alias into
the shared `EmbodiedMotorTrial`/receipt lifecycle was tested and rejected for
this rung: the high-volume reset-calibration stream created an adaptive
decision/efference/eligibility population for every calibration intervention
and exceeded the existing helicopter test runtime, while the helicopter
receipt does not yet carry all shared sensor-latency, contact, position, power,
and thermal fields without reconstruction.

Helicopter learned choice nevertheless uses the shared collapse today.
Contextual transition memories are the options when available; the compact
energy model is the fallback. The safe follow-up for receipts is a native
shared normalizer with a declared helicopter receipt schema and retention
policy, not an aerial-edge alias or host-side physics interpretation. Until
then, helicopter receipts, learning, and slower scheduling remain graph-native
and causally linked through their existing exact trial identity.
