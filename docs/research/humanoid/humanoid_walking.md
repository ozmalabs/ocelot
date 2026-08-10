# Graph-native humanoid walking

This development experiment extends the 21-joint humanoid balance result into
directed bipedal locomotion. It uses the same 43 opaque commands: a tonic
posture and positive or negative twitches for each dynamically discovered
joint. It adds no named hips, knees, feet, gait phases, motion clips,
pretrained policy, inverse kinematics, or Python gait controller.

## What the graph learns and controls

Each non-tonic command is first sampled once from the same settled initial
state. Verified transition receipts let the graph learn local changes in:

- body vertical-axis orientation;
- angular velocity; and
- horizontal velocity.

The graph then creates three consequence models per non-tonic action: double
support and the two opaque unilateral-support regimes. Their prior strength is
derived from the square of the number of mechanically possible support
regimes. Each phase/action model permits one verified contextual refinement,
so an observation can specialize but cannot repeatedly overwrite the safe
standing prior.

Familiarization has no fixed action duration. A graph rule closes it after no
new contextual receipt for longer than the complete 126-model
support-conditioned alphabet. The body is reset for evaluation, while unseen
phase/action pairs retain the same one-shot authority during deployment.

For every action the graph predicts balance over the body's gravity-derived
fall timescale and combines it with error from a requested dimensionless
Froude speed, morphology-scaled return velocity toward the commanded travel
line, and the lateral capture point `y + vy × sqrt(height / gravity)`. One
Rust-evaluated graph `Argmin` chooses the best support-conditioned primitive.

That primitive seeds a graph-resident motor program. Analysis by synthesis
then repeatedly forward-predicts the whole program and adds the remaining
independent primitive that strictly reduces predicted task error. There is no
declared bundle width. A program stops at the graph fixpoint where no causally
supported addition improves the prediction. One member per discovered
actuator group prevents contradictory commands and makes the search finite
without knowing joint names.

Composition is receipt-controlled rather than assumed additive. Before
walking, reset-isolated pair probes learn which concurrent commands remain
inside the body's single-action effect, tilt, and height envelope. Each
approved pair stores its measured nonlinear interaction residual. A candidate
may join a larger program only when an approved compatibility edge connects it
to every existing member, so a wider program is a clique of measured-safe
pairwise interactions. Its forward prediction is the horizon-scaled sum of
primitive effects plus those learned residuals.

Each addition consumes a structural resume edge and yields. The mechanical
scheduler may restore only that declared edge on the next cognitive tick; the
graph then decides whether to add another member or close. Thus a stale
same-tick match cannot accidentally cap or over-expand a bundle. Python reads
the final membership edges, checks that the trial names the same program, and
enacts the tokens without choosing, ranking, or repairing them.

The exact whole-program receipt stores observed and residual body effects on
the program node. A single-member receipt can still refine its identifiable
support-conditioned primitive. A two-member receipt has one identifiable
interaction and therefore refines that exact reusable pair residual online.
A wider-program residual is not smeared over its members: it remains attached
to the causal program until later interventions can disambiguate its
higher-order interactions.

Grounded multi-member programs now form a motor repertoire rather than a
write-only archive. Their exact observed consequence is consolidated as an
online mean. On a later request, all safe memories for the current support
context remain output-null while the graph forward-evaluates them against the
current body state. A memory becomes output-potent only when it strictly beats
the best primitive and the learned compound cadence permits release. Its new
receipt updates the whole pattern; an unsafe receipt withdraws it from recall.
If no memory qualifies, ordinary analysis by synthesis constructs a new
program. This is repertoire reassociation, not memoization by Python.

Safe compound receipts also form a directed temporal motor graph. The graph
keeps the last verified compound population state as sparse high-level
context; the next safe compound state creates or updates a conditional
transition between them. Intervening primitive feedback does not erase this
context, while an unsafe compound receipt or recovery does. When the
predecessor recurs, its outgoing transitions remain output-null until a graph
`Argmin` finds one whose receipt-learned conditional consequence beats the
best primitive. The successor trial links the exact transition and exact
program, so its receipt advances and updates the trajectory. There is no
declared path length or host-side sequence machine.

Recall now has an explicit preparation/release stage. A candidate first
becomes a `HumanoidMotorPreparation` with no actuator authority. Its direct
channel carries predicted task cost; its indirect channel carries
receipt-learned uncertainty of the mean. The graph releases the preparation
only when the uncertainty-adjusted candidate beats the primitive globally and
within the lateral capture channel. This is a basal-ganglia-inspired
selection/disinhibition analogy, not an anatomical claim.

The forward model separately consolidates whole-body and lateral sensory
prediction error. Uncertainty falls only with exact verified experiences.
Timing is an independent coordinate: memories and transitions learn
consequence per physics frame, reconstruct the predicted outcome at the
selected horizon, contract after excess prediction error, and relax after a
stable receipt. Changing speed therefore no longer reuses an unscaled
fixed-horizon consequence.

Repeated walking now updates one canonical structural memory instead of
minting a request-identity duplicate on every decision. Analysis by synthesis
still authors each current action. Before execution, the graph checks whether
the exact member set already has a grounded memory. If so, the current
synthesis retains actuator authority while its verified receipt updates the
canonical program's consequence, uncertainty, timing, and experience. The
duplicate working plan is archived off the active scan. On the deterministic
600-action trajectory, behavior remains byte-for-behavior identical to the
stable controller (`0.683 m`, 197 support alternations, no fall), while the
most-used program reaches 200 experiences instead of remaining fragmented
across one-experience nodes.

Stable prediction receipts also relax the compound cadence back toward the
body-derived baseline; surprise lengthens it. Both directions are reversible
and use morphology/sensor-derived horizons rather than a declared control
frequency.

## Shape-indexed motor library

Safe canonical programs are now minted into a persistent body-shape codebook.
This reuses the substrate's existing `ShapeDecode` term rather than introducing
a humanoid compatibility matcher:

- each simulator exposes a name-free integer relation system containing
  kinematic parentage, exact rational actuator axes, and support topology;
- `HumanoidBodyShapeSignature` is a domain-specific ShapeDecode codebook;
- graph rules perform singleton-scoped exact-cover decoding, mint an unseen
  body shape when no held signature covers it, and associate safe programs
  with the recognized shape;
- JSON code only serializes/restores graph facts. On a new lifetime, graph
  equality binds each stored opaque member back to a current
  support-conditioned actuator model, and only a complete binding activates
  the program.

Controller dynamics (physics step, gravity, twitch scale, force and servo
gains) must also match exactly. This prevents morphological resemblance from
silently licensing a program under different actuation.

Restored programs initially remain output-null. A first version allowed a
shape-matched prior to compete for direct output immediately: it recognized
and activated both stored programs, but reduced 180-action travel from
`0.1308496205 m` cold to `0.0404199604 m` warm. That result falsified
shape-match-alone authority. The corrected path requires present-lifetime
analysis by synthesis to independently reconstruct the same bundle and obtain
one fresh receipt before direct recall is permitted. With that gate, a fresh
graph:

- recognized the held body and rebound/activated `2 / 2` programs;
- reproduced the cold trajectory exactly (`0.1308496205 m`, no fall);
- structurally reused imported programs three times; and
- raised the most experienced canonical memory to 128 receipts.

`ShapeDecode` is the appropriate existing machinery for the static morphology.
The substrate's order-N finite-difference machinery is not invoked on a static
body merely to claim reuse; it remains the appropriate next layer for genuine
multi-frame motor-response trajectories once those observations are retained
as ordered frames.

Familiarization also gives the graph its own disturbance reference. For each
verified action it compares the observed horizontal velocity change with the
active support-conditioned prediction. It retains the largest normal
prediction residual, plus the mean and maximum normal vestibular tilt. A
surprise streak must last for the number of receipts derived from the body's
three linear-velocity channels and two support sensors. Excessive tilt can
interrupt immediately. During interruption the graph suppresses walking
twitches, selects the locally learned balance correction, and composes a
compatible second correction when its predicted combined body-axis cost is
lower; it resumes walking only after tilt falls below the learned normal mean.
Python neither labels a push nor requests recovery.

If recovery cannot restore upright posture, the graph now enters a distinct
whole-body get-up regime. Every discovered non-tonic actuator—including
whatever the unknown body uses as arms, trunk, or legs—receives a get-up
consequence model. The graph systematically tries untested actuators, learns
normalized height and vertical-alignment gain, then exploits the best learned
effect. After an actuator-alphabet-length impasse it requests a mechanical body
reset, resumes the same lifetime, and preserves learned programs, transitions,
get-up models, and cumulative progress. In the current Bullet body's tiny
single-twitch get-up action space this produces attempts and a graph-requested
reset but no successful rise. Arbitrary combined get-up programs remain the
honest missing capability; the reset prevents one fall from terminating all
subsequent learning.

The body also exposes two support sensors discovered from whichever links bear
weight after settling. They have stable ordinals but no left/right or
anatomical labels. Graph rules independently measure directed progress,
minimum height, peak tilt, alternating unilateral support, and aerial samples.
Python repeats those measurements as a test oracle and enacts only the token
selected by the graph.

The protocol now declares only the 240 Hz physics clock. The graph derives its
nominal horizon from measured standing height, gravity, physics time step, and
the discovered actuator dimensionality:

`gravity fall horizon / ceil(sqrt(number of opaque actuators))`

For this body the result is 12 physics frames, or 20 Hz, but 20 Hz is no
longer configured. Multi-member commands use the causally calibrated
pair-probe horizon of six frames (40 Hz), independent of width. The balance
reflex on the same body derives a two-frame response (120 Hz) by dividing the
body horizon by the sensor-derived confirmation horizon. Gait prediction
surprise can similarly halve the current response horizon, which then relaxes
one physics frame per stable receipt.

## Paired result

Two fresh graphs and bodies receive identical reset-isolated, one-experience
calibration. One graph receives a directed-walk objective; the matched control
selects only tonic posture. At action 300, after each graph has already chosen
its command, the world applies an unannounced one-frame longitudinal force of
two body weights (`801.36 N` for this body). Over 600 actions, or 30 simulated
seconds:

| Measure | Learned graph | Tonic posture control |
|---|---:|---:|
| Directed travel | `0.683 m` | `-0.003 m` |
| Final lateral drift | `-0.167 m` | `<0.001 m` |
| Minimum base height | `> 0.75 × standing height` | `> 0.75 × standing height` |
| Unilateral support alternations | `197` | `0` |
| First support only | `253` samples | `0` |
| Second support only | `258` samples | `0` |
| Double support | `89` samples | `600` |
| Aerial phase | `0` samples | `0` |
| Multi-motor commands | `10` | `0` |
| Prepared/released program recalls | `2 / 2` | `0 / 0` |
| Learned/recalled transition edges | `6 / 0` | `0 / 0` |
| Nominal/compound command horizon | `12 / 6` frames | `12 / —` frames |
| Realized mean command rate | `20.31 Hz` | `20 Hz` |

Familiarization closes itself after 757 actions. It includes 42 staged
pair-interaction probes and 65 contextual learning events; the last occurs at
action 629, followed by a quiet interval longer than the full phase/action
alphabet. Eight previously unseen support/action contexts receive their
single permitted refinement during evaluation.

The interruption reflex remains available, but this trajectory absorbs the
two-body-weight shove without entering tonic recovery. The learned controller
remains upright and uses more than 20 distinct opaque commands.
The feet repeatedly leave and regain support, the supporting side alternates,
the mean touchdown advances in the requested direction, and at least one
support remains grounded in every sampled interval. Two of the ten
multi-motor commands are output-potent recalls rather than fresh syntheses.
Both pass through distinct output-null preparation and release records. One
grounded program is recalled twice and reaches three exact experiences.
Six safe temporal edges form, but each has only one experience, so none earns
sequence release under the uncertainty gate.

This is a safety/capability result, not a distance improvement. The temporal
controller without uncertainty travelled `0.769 m`; this controller travels
`0.683 m` while reducing aerial samples from six to zero and preserving every
acceptance criterion. It remains above the pre-repertoire
arbitrary-synthesis result of `0.643 m`.

The graph's progress, height, tilt, support-alternation, and aerial counts
exactly match the independent reporting path. The generated seed and complete
trace are deterministic.

## Limits

This is slow, emergent walking on level ground, not a mature gait controller.
The synthesis rule can author arbitrary-width sparse programs, and the
adversarial graph fixture requires three simultaneous motors, but this
PyBullet trajectory currently finds at most a two-motor program worth
executing. That distinction is deliberate: width is an inferred consequence,
not a target or a success metric. Pairwise compatibility also does not prove
that every higher-order interaction is safe. A whole-program memory can reuse
its measured higher-order consequence, but it cannot yet decompose that
consequence into transferable sub-interactions. This is one force, direction,
phase, and seed—not a disturbance envelope. Slopes, steps, friction changes,
obstacles, repeated pushes, and humanoid body damage remain untested.
The learned temporal graph is first-order and sparse: it conditions on one
preceding compound state, not a longer movement history, latent phase, or
uncertainty distribution.
The shape library currently restores canonical programs, not learned temporal
transition edges or higher-order response generators. Exact shape/dynamics
matching is intentionally conservative; transfer across scaled, damaged, or
topologically related bodies requires graph-grounded transforms plus fresh
receipts rather than permissive host-side token remapping.

Run:

```bash
/path/to/.venv/bin/python scripts/gen_humanoid_adaptation_seed.py
/path/to/.venv/bin/python scripts/jabberwock_humanoid_walk.py \
  --motor-library data/learned/humanoid_motor_library.json \
  --json-out results/humanoid_walking_v1.json
/path/to/.venv/bin/python -m pytest \
  tests/test_humanoid_walking_migrated.py -q
```
