# Motor-cortex research spike

## Scope

This spike asks which established features of biological motor control should
change the Jabberwock's graph-native humanoid controller. It does not treat the
motor cortex as an isolated inverse-kinematics module, and it does not claim
that graph nodes are neurons. The useful level of comparison is computational:
preparation, population trajectories, output gating, feedback, repertoire
constraints, and learning.

## What the evidence supports

### Population dynamics generate actions

Motor-cortical activity is better explained at population level than as
independent neurons encoding one kinematic variable. During reaching,
population activity follows structured, often rotational trajectories that
can generate time-varying muscle output
([Churchland et al., 2012](https://doi.org/10.1038/nature11129)). This argues
for a motor program as a coordinated population state with dynamics, not a
bag of independently selected joints.

### Preparation and execution occupy different subspaces

Preparatory motor-cortical activity can change substantially without producing
movement because its population pattern lies in an output-null subspace.
Movement begins when activity becomes output-potent
([Kaufman et al., 2014](https://doi.org/10.1038/nn.3643)). Preparatory and
movement computations are largely orthogonal but linked: the preparatory state
sets the initial condition for the movement trajectory
([Elsayed et al., 2016](https://doi.org/10.1038/ncomms13239)).

The engineering implication is structural gating. Candidate programs may be
constructed, compared, and retained without actuator authority. Only an
explicit graph transition may make one program output-potent.

### Dynamics are distributed and input-driven

M1 is not an autonomous central pattern generator. Perturbing motor thalamus
disrupts cortical activity and limb kinematics throughout dexterous movement;
both cortical state and external input predict the next cortical state
([Sauerbrei et al., 2020](https://doi.org/10.1038/s41586-019-1869-9)).
Sensory feedback is therefore part of the movement-generating dynamics, not
just a delayed audit.

M1 also integrates mechanically coupled joints during fast feedback. Neurons
combine shoulder and elbow motion information into task-appropriate
corrections in roughly 50 ms
([Pruszynski et al., 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC4974074/)).
Visual and proprioceptive perturbations partially converge on common M1
correction circuitry
([Cross et al., 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10867723/)).

The current receipt cadence already provides receding sensory feedback at
20–100 Hz. The important gap is not another global tick rate; it is learning
and recalling coordinated, context-conditioned population responses.

### Learning is constrained by an existing repertoire

New motor mappings are learned more readily when they remain inside the
population's intrinsic manifold
([Sadtler et al., 2014](https://doi.org/10.1038/nature13665)). Short-term
learning often reassociates an existing repertoire of population patterns with
new outputs rather than immediately inventing arbitrary new activity
([Golub et al., 2018](https://doi.org/10.1038/s41593-018-0095-3)).
Low-dimensional latent dynamics can remain stable for years despite turnover
in recorded neurons
([Gallego et al., 2020](https://doi.org/10.1038/s41593-019-0555-4)).

Preparatory population states also index learned motor memories and can
separate otherwise interfering dynamics
([Sun et al., 2022](https://doi.org/10.1038/s41586-021-04329-x)). This supports
retaining successful motor programs as context-addressable preparatory states.

### Synergies are useful hypotheses, not fixed anatomy

Repeated cortical and muscular activity patterns consistent with
spatiotemporal synergies have been measured during natural grasp behavior
([Overduin et al., 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4571600/)).
That does not establish a universal fixed synergy dictionary. The conservative
implementation is therefore learned, receipt-backed composition whose width
and membership remain revisable.

## Mapping to the existing substrate

| Biological computation | Existing graph mechanism | Gap before this spike |
|---|---|---|
| Preparatory output-null activity | A building `HumanoidMotorProgram` has no actuator edge | Grounded programs were archived but not available as preparatory memories |
| Output-potent release | Ready program → causal trial → mechanical enaction | Only newly synthesized programs could be released |
| Efference copy / forward model | Trial stores predicted body consequence | Exact learned whole-program consequence was not reused |
| Sensory prediction error | Verified transition receipt | Recalled whole-program means could not consolidate |
| Population repertoire | Primitive and pair models; arbitrary matching pursuit | Every eligible compound request restarted from primitives |
| Fast multi-joint feedback | Receipt-driven receding horizon and cadence contraction | Reusable context-conditioned population corrections were absent |

## Build inspired by the evidence

The upgrade adds cortical-style motor-memory consolidation and reassociation:

1. A safely grounded multi-member motor program stores the running mean of its
   exact observed body consequence.
2. It remains output-null in the graph as a repertoire element.
3. On a later request in the same support context, the graph evaluates all
   eligible memories against the present body state and task.
4. A memory becomes output-potent only if it strictly predicts less task error
   than the best primitive and the learned compound cadence permits release.
5. The new trial is a distinct causal event but refers to the old arbitrary
   member graph; Python neither reconstructs nor selects the bundle.
6. Each recall updates the whole-program consequence by an online mean.
   An unsafe receipt immediately removes that memory from the potent
   repertoire. Wider-program error is never smeared across unidentified
   members.
7. If no memory qualifies, the existing analysis-by-synthesis path constructs
   a new program. Consolidation therefore accelerates familiar control without
   limiting novelty.

There is no fixed repertoire size, recall count, motor-program width, or
special anatomical command.

## Temporal trajectory extension

The follow-on build makes repertoire elements into a learned directed motor
graph:

1. The first safe compound-program receipt establishes the active
   output-potent context.
2. The next safe compound receipt creates a transition from the previous
   program to the new program. Ordinary single-action corrections may occur
   between these high-level population states without destroying the context.
3. The transition stores its own predecessor-conditioned consequence mean,
   response horizon, experience count, and successor edge. It is not just an
   alias for either endpoint.
4. When the predecessor becomes active again, a graph `Argmin` evaluates its
   eligible outgoing transitions in the current body state. The best successor
   becomes output-potent only if its conditional prediction beats the best
   primitive and the existing compound-output guard permits it.
5. The successor's verified receipt advances the context and updates both the
   whole-program memory and the exact temporal edge.
6. An unsafe compound receipt withdraws the corresponding edge and breaks the
   active trajectory. Entering recovery also breaks the context.

Repeated transitions can therefore form arbitrary-length graph paths without
a declared sequence length or a Python state machine. The learned state is
sparse and hierarchical: it sequences coordinated compound corrections while
the existing fast receding controller continues to supply intervening
primitive feedback.

## Falsifiable expectations

- A controlled graph fixture must recall a grounded three-member program
  without synthesizing a duplicate.
- The host boundary must continue to read only graph-authored membership.
- At least one safe repeated PyBullet program should accumulate more than one
  whole-program experience if the environment actually revisits its context.
- Recall must not weaken the existing upright, drift, support-alternation, or
  aerial-phase acceptance criteria.
- HumanoidBench H1 is not expected to improve unless it first grounds a safe
  multi-member program. A result with zero recall is informative rather than a
  failed implementation.

## Remaining biological gaps

The new paths are first-order transitions between sparse compound population
states, not smooth latent neural dynamics. The graph does not yet learn
condition-independent timing trajectories, sequence phase under variable
speed, state estimation under sensory delay, or a distributed
cerebellar/basal-ganglia/thalamocortical loop. Transition choice uses the
current body state and one active predecessor but not a longer history or
explicit uncertainty. Pairwise safety also cannot identify arbitrary
higher-order interactions.

## Spike result

The deterministic PyBullet walking arm recalled five grounded programs during
600 evaluation decisions. Two exact motor memories were reused; their final
experience counts were five and two. Five safe directed transition edges
formed naturally. One learned edge was later selected from its predecessor,
recalled its exact successor, and reached two conditional experiences.

The trajectory controller travels `0.769 m`, compared with `0.798 m` for the
memory-only controller and `0.643 m` for the preceding arbitrary-synthesis
controller. The temporal capability therefore costs `0.029 m` in this single
run; it is not presented as a performance improvement. The body remains
upright, final lateral drift is `0.156 m`, support alternates 206 times, and
six samples are aerial. All existing acceptance criteria pass without changing
a threshold, cadence, or bundle width.

The matched tonic controller recalls no program and forms no transition. The
controlled graph fixture also proves an `A → B → A` path: receipts create the
two directed edges, returning to `A` makes the learned `A → B` edge
output-potent, the next receipt updates its conditional mean, and an unsafe
receipt invalidates the selected edge and clears the trajectory context.

Official HumanoidBench H1 remains the expected falsification. It grounds only
single-member programs before falling at decision 65, so it produces zero
eligible memories and zero recalls. Tonic control falls at decision 64. The
recall mechanism therefore does not hide an inadequate forward model or force
compound behavior where analysis by synthesis has not justified it.

## Follow-on biology-derived control

The temporal spike exposed three distinct concerns that the original
transition representation conflated:

- evidence about whether a learned consequence is reliable;
- preparation versus actuator release; and
- program geometry versus the time taken to traverse it.

The follow-on build now learns whole-body and lateral prediction-error energy,
uses uncertainty of the learned mean as an indirect release cost, creates an
explicit output-null preparation before a separate graph release, and learns
consequence rates that can be evaluated at an adaptive response horizon. See
[Biology-derived motor-control upgrade](biological_motor_control_upgrade.md)
for the research mapping, falsified intermediate designs, and implementation
details.

With the stricter uncertainty gate, the deterministic PyBullet run travels
`0.683 m`, drifts `0.167 m`, alternates support 197 times, has zero aerial
samples, and remains upright. It prepares and releases one learned program
twice. Six safe temporal edges form, but each has only one observation, so
none receives sequence-release authority. The earlier `0.769 m` trajectory
result above remains the historical timing-only baseline, not the current
controller result. HumanoidBench H1 remains unchanged and produces no
preparation, release, transition, or recall.
