# 9 · One Core, Six Bodies

*Draft. Sources: `docs/features/humanoid.md`, `docs/features/flight-control.md`;
`docs/research/humanoid/` (≈55), `docs/research/flight_control/` (≈24);
`docs/research/flight_control/regime_pareto_frontier_{prereg,results}.md`;
`seeds/embodied_sensorimotor_core.json`. Register per `BOOK_VOICE.md`.*

---

This project's stated measure of success is not a score. It is Heinlein's
competent man — an agent whose competence *generalises* across bodies, domains
and problem shapes rather than being fitted to one of them. Under that measure,
a capability that lands in one body and is then independently re-derived in
another counts for more than the same body scoring higher on its own benchmark.

**This chapter is the most direct test of that claim in the book.** One
body-agnostic sensorimotor layer drives a humanoid, an F-16, an X-15, a
helicopter, wheeled racing bodies and a quadrotor drone. It does not know which
it is driving.

And the chapter's best result is not any of those. It is that a failure in the
jet and a failure in the humanoid — which for a long time looked like two
unrelated bugs in two unrelated projects — turned out to be **the same missing
capability seen from opposite sides**.

---

## 9.1 The core does not know what body it is in

One graph-native layer sits between every body and its physics. What crosses the
simulator boundary is transduction only: position, orientation, velocities,
contact, sample period, sensor latency, actuator activation, energy and thermal
readings. Numbers about a physical situation.

Everything above that line is rules. Prediction, sensor fusion, attention,
interruption, credit assignment, consolidation, replay — none of it is
per-body host-language logic, and none of it names a limb, a control surface,
or a wheel.

The core learns from **opaque effectors, delayed receipts, and uncertain
multimodal observation.** It is not told what an actuator does; it is told that
something was commanded and something was later observed, and it has to relate
them. Which is exactly the situation a nervous system is in, and — chapter 1 —
exactly the situation an eye is in.

**Biological constraints become graph mechanisms rather than simulated
anatomy.** The clearest instance: proprioceptive and vestibular feedback arrives
*late*, so it cannot be read as the current state of the body. The core's answer
is a body belief that advances a prior and precision-weights each delayed receipt
as it lands — the same predictive-coding move the eye makes for retinal input,
in a different modality, for the same reason. Nobody transplanted it; the
constraint produced it twice.

Older body-specific seeds now depend on this shared core rather than carrying
their own copies of it.

---

## 9.2 The six bodies

**Humanoid.** This one gets its own section (§9.2a) because it is not a
controller at all — it is a developmental curriculum, and it is the motor
counterpart of chapter 6.

One result from the same thread is worth a sentence here for how it was
obtained. A balance term had been switched off. It was switched *on* — a single
protocol-line change — and measured. Not redesigned, not tuned around: turned
on, run, reported. The cheapest experiments are the ones nobody runs.

**Damage and wear.** A four-version arc on hidden damage: the body keeps
operating and re-adapts its control policy as components degrade, **without
being told what broke**. The adaptation has to be driven by the discrepancy
between what was commanded and what was received, because that is the only
signal there is.

**Nonholonomic bodies.** Bodies that cannot move directly sideways — the
constraint class that makes parking hard. A two-version arc building the graph
representation for it.

**Generic effector assembly.** The most body-agnostic result in the thread: the
motor substrate discovers coordination structure from a body's *wiring* and its
verified action receipts, without a named skeleton, named muscles, or a
declared morphology. What a limb is turns out not to be something the controller
needs told.

**Fixed-wing.** An F-16 in an external flight simulator: coupled surface
control, departure recovery from deep stall and flat spin, a replication of a
published fault-tolerant-control result, and a characterisation of the raw
longitudinal-stability boundary. An X-15 in both standard and hypersonic
regimes.

**Rotary and wheeled and aerial.** Helicopter autorotation — an unpowered
descent, which is the maneuver with the least margin for a controller that
hesitates. Wheeled bodies with active aerodynamics, individual-wheel and
differential control. And a quadrotor in an external drone simulator, pinned at
a specific commit, under the same adaptation machinery as the damage arc.

The through-line is that these are not six controllers. They are six bodies
attached to one core, and the core's ignorance of which body it has is the
property being tested.

---

## 9.2a The humanoid learns its own body

Chapter 6 argued that the interesting thing about the speech work was not the
recogniser but the *order* — canonical developmental stages, arrived at because
each one exhausted its own room rather than because a curriculum imposed them.
The humanoid thread is that argument in the motor system, and it is further from
a controller than anything else in this chapter.

**It starts on its back.** Not as a canonical pose, and not as a hidden home
state to return to — merely as a currently stable relation between this body and
this surface. Low height and non-upright orientation are *intended conditions*
while the floor is the active ecology. Nothing may invoke a get-up program
unless evidence opens a viability interrupt.

**Development is a dependency graph, not an age clock.** No stage counter, no
scalar progress score. The broad progression runs: spontaneous whole-body
variation, effector consequences, contact, reversible action → side lying,
rolling, prone support, reaching, sitting → transitions, belly mobility,
quadruped support, crawling → kneeling, pulling to stand, cruising, standing,
assisted stepping, walking → running, jumping, stairs, hopping.

But the ordering is deliberately a **DAG**, and that choice is grounded rather
than convenient: it matches the WHO longitudinal finding that achievement
windows overlap, that no fixed sequence should be assumed, and that a minority
of typically-developing children never crawl on hands and knees at all. So
crawling is an optional route to standing rather than a gate before it.

**The first capability is spontaneous general movement**, and the reason is the
same one chapter 6 gives for babbling. Useful early development is not a
sequence of commanded poses; **movement variability is itself the sensorimotor
data** from which directed, repeatable action can be learned. You cannot learn
what a limb does by being told; you learn it by moving and receiving.

### The waves, again

The generator for that variation is the part worth stopping on, because it is
chapter 1 arriving independently in a different modality.

The discovered mechanical effector topology becomes an **excitable sheet**.
Homeostatic deprivation ignites a rested channel, activity travels one
mechanical hop per motor epoch, and a topology-derived active interval makes
adjacent bursts overlap; the overlapping front collapses into one motor program
that may command several effectors at once. Verified reafference then updates
each cell's experience counters. **The field itself has no output authority.**

That is the retinal wave of chapter 1 — structured spontaneous activity before
the function it prepares — with the same properties: no anatomy, no preferred
pose, no fixed wave width or duration, connectivity determined by the body's own
topology. One excitable cell per physical command channel rather than per
opaque token, so that flexion and extension of one joint are polarities of one
channel rather than two independent effectors.

The thread states its own limit here, and it is the right limit: **this does not
claim that human spinal or motor-cortical development is literally a copy of
retinal waves.** The testable claim is narrower — that endogenous correlated
movement provides better developmental evidence than isolated commands, and that
receipts should progressively turn that variation into reusable programs.

### What counts as having learned something

A joint twitch is not a roll, and one lucky event is not a milestone. This is
where the thread's discipline shows, and it is stricter than most learning
claims in this book.

For any capability the graph requires **all four**: causally bound, verified
receipts; repeated success over a body-derived evidence window; more distinct
situated contexts than its prerequisite abilities; and a successful **delayed
retention probe**. Only then is it mastered, and stored as an output-null,
shape-indexed memory.

Two consequences of that design deserve carrying. Clinical-style milestones are
reported **separately** from precursor capabilities — so the report cannot
launder partial progress into an achievement. And **failing to reach a later
milestone is data**, not something hidden by a collapsed progress score. The
next developmental limit is auditable rather than inferred from a stage number.

The frame discipline holds throughout: continuous simulator quantities exist
only at the mechanical interface, and developmental evidence, memory, selection,
competence, retention and transfer are integer-only graph cognition. Recalled
templates have zero output authority — they inform, they do not command.

### Where it has actually got to

As of the most recent run in the record: **active stage ordinal 3**, three
demonstrated capabilities, three demonstrated human analogues, and **zero
clinical milestones.** The active capability is reversible configuration
control; the human analogue is repeated reversible limb action; the ecology is
the floor.

So: it is on its back, on the floor, having learned that its own actions are
reversible. **It is not walking, and nothing here should be read as suggesting
it is.** Walking sits two stages up the graph, behind rolling, sitting,
quadruped support and pulling to stand — each of which has to clear the
four-part evidence bar above, including delayed retention.

That is the honest state, and it is the state the design intends to make
visible. A system reporting a stage number could have told you it was 60% of
the way to walking. This one tells you which capability it is working on, in
which ecology, with which prerequisites unmet — which is the difference between
a progress bar and a measurement.

**And the transfer claim is what makes the whole thread belong in this chapter.**
Because the goals are body-plan-neutral — structural relations and receipts
rather than named limbs — shared kinematic and support relations can warm-start
a structurally similar body. Every transferred ability must be reverified on the
receiving body, which is the same discipline chapter 5 applies to a codebook
entry: transfer proposes, verification decides.

## 9.3 The two failures that were one

Now the finding.

**In the jet:** a controller searching for a fixed point that does not exist.
Some flight regimes have no stable trim to converge to, and a controller built
around finding one will hunt forever.

**In the humanoid:** a controller sitting in a fixed point it should have left.
A stable configuration is not always the right one, and a controller built
around holding a stable point will hold a bad one indefinitely.

These were, for a while, two bugs. One in aviation, one in locomotion, in
different threads, with different symptoms, being separately debugged.

**They are mirror images of one missing capability: the ability to select a
control regime rather than to run a fixed one.** Neither controller was wrong
about its regime. Both were wrong that there was only one.

The reframe that follows is the useful part. Regime selection is not a ladder to
be climbed — try the simple controller, escalate if it fails — because that
presumes an ordering that the two failures show does not hold. It is a **Pareto
frontier**: several regimes, each better on some axis, with selection depending
on where the body currently is.

That was measured, powered, and produced an honest result that inverted the
efficient-sounding design: **full-dwell selection beats a shortlisted one.**
Evaluating the candidate regimes properly wins over pre-filtering to a promising
few — which is, exactly, chapter 5's run-11 inversion in a different domain.
Shortlisting is a bet that your proposal stage is good enough to discard
candidates cheaply, and in both domains that bet lost once the deciding stage
was strong enough to exploit the wider set.

The same shape, twice, in unrelated bodies, arrived at independently. That is
the kind of recurrence this book counts as evidence.

---

## 9.4 What this arc measured about itself

The same retrospective that produced §9.3 produced an uncomfortable finding
about how these controllers were built, and it belongs here because chapter 15
generalises it.

The learning machinery in this thread regressed without terminating. In outline:
a count-divided learning rate assumes the world is stationary; declare a floor
so it keeps adapting; a flat floor costs you in quiet regimes; declare a surprise
factor so the floor moves; surprise needs a reference; add a running average; the
running average needs a rate. **Each rate needs a rate.**

Measured across the tree: **sixty count-divided learners across eight embodied
seeds — and not one of them inside the shape-matching faculties.** The faculties
that decode against a codebook never needed a scalar rate. The ones that track
numbers are where every defect of this class lives.

And the specific cost, in this thread: the motor system's slope-collapse
behaviour was **hand-written as a bespoke rule**, when it is rung 2 of the ladder
chapter 4 describes — a residual read as one uniform step along an existing
dimension. Everything the loop gives for free at that grain, the motor path
either reimplemented or did without.

That is not a criticism of the controllers, which work. It is a statement about
where the debt is, and chapter 15 is where it is enumerated rather than
characterised.

---

## 9.5 What would falsify this

- **Body-agnosticism.** The claim is that one core drives six bodies. If any of
  the six is found to depend on body-specific logic above the transduction
  boundary, the claim narrows to five, and the audit that would show it is
  mechanical.
- **The mirror-image reading.** If the jet's hunting and the humanoid's sitting
  turn out to have separate causes that merely rhyme, §9.3's central claim is a
  coincidence dressed as a finding. The test is whether one regime-selection
  mechanism fixes both, which is stronger than either fix alone.
- **The Pareto result.** Full-dwell beating shortlisting was measured on one
  protocol. If shortlisting wins under a stronger proposal stage, the finding is
  about that proposal stage rather than about selection.
- **Effector discovery.** If the coordination structure the substrate discovers
  from wiring and receipts turns out to encode a morphology assumption in its
  representation, "no named skeleton" is a statement about the interface rather
  than about the learning.
- **The developmental DAG.** The strongest falsifier available to this thread is
  the one it has not yet reached: if the curriculum stalls at a stage for a
  reason that is *not* a missing prerequisite — if the dependency graph is not
  what actually gates progress — then it is an ordering imposed after the fact.
  Zero clinical milestones is currently consistent with both "early" and
  "wrong", and only getting further distinguishes them.

One bound over the chapter: every body here is simulated, two of them through
external simulators this project does not control. Nothing in it establishes
transfer to physical hardware, and the failure modes of real actuators —
backlash, thermal drift, sensor dropout — are represented only as far as those
simulators represent them.

---

*Ends. Next: Part IV, where the same substrate stops being a thing that
perceives and acts, and becomes a subject among other subjects.*
