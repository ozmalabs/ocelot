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

**Humanoid.** Balance and walking, and one result worth its own sentence
because of how it was obtained. A balance term had been switched off. It was
switched *on* — a single protocol-line change — and measured. Not redesigned,
not tuned around: turned on, run, reported. The cheapest experiments are the
ones nobody runs.

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

One bound over the chapter: every body here is simulated, two of them through
external simulators this project does not control. Nothing in it establishes
transfer to physical hardware, and the failure modes of real actuators —
backlash, thermal drift, sensor dropout — are represented only as far as those
simulators represent them.

---

*Ends. Next: Part IV, where the same substrate stops being a thing that
perceives and acts, and becomes a subject among other subjects.*
