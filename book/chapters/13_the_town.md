# 13 · The Town

*Draft. Sources: `docs/features/bigville.md`; `docs/research/bigville/` (≈202
documents); `docs/research/engine_substrate/AFFECT_WEIGHTED_ROUTE_VALUATION_DESIGN.md`,
`DESIRE_PATH_PRECONDITION_RESULTS.md`, `TERRAIN_WEAR_STIGMERGY_RESULTS.md`.
The town's runtime and data live in a separate repository and are cited as
external.*

---

There is a village. It has an economy, a labour market, land, prices, a council,
a legislature, a court, bylaws, sentencing, a jail, a church, a school, a
newspaper, gossip, drama, and about a hundred residents each carrying the affect
machinery of chapter 10.

The temptation with a thing like that is to inventory it. Two hundred documents
of village would make a very boring chapter.

**So the question this chapter asks instead: what does a mind among minds
compute that a mind alone does not?**

---

## 13.1 What a population is for

Chapter 12 ran fifteen experiments on a coupling between two people, and then
put that coupling in a network — where the results stopped being about a
relationship and started being about a population. That transition is what the
town is for.

Three things only exist at population scale, and all three are mechanisms rather
than themes.

**Belief propagates.** Gossip and news are belief update over a topology.
Chapter 12's sharpest network finding — that nodes with *zero direct
observation* reach a corrupted belief, and that a single truth anchor reverses
the local sign — is a fact about the town's machinery, not about that experiment.
It applies to any belief the town carries.

**Reputation is a held quantity that responds to evidence reaching it.** Not to
what happened. That distinction is invisible in a dyad and load-bearing in a
population, and chapter 12's evidentiary-visibility rung is the measurement of
it: hold the harm identical, change only whether a trace reaches anyone, and the
outcome changes.

**Support is a graph, and it can be severed.** Isolation is measurable as intact
edges, and — chapter 12 again — active severing and ordinary drift are
super-additive.

And underneath all three, one rule. A resident deciding anything — where to
walk, whether to trade, whom to believe — does it by selecting among candidate
appraisals by total value. That is the same template chapter 10 uses for a child
deciding whether to wait for a second marshmallow, and the same one chapter 12
uses, unmodified, as its control for whether concealment requires intent. Not an
analogy between three models: **one rule, doing developmental, clinical and
civic work.** A town of a hundred residents is that rule, a hundred times, with
different held values.

The town is what makes those social rather than stipulated. An experiment that
declares "the network believes X" has assumed its result. One where belief
arrives through the same gossip machinery the town runs anyway has not.

---

## 13.2 Desire paths: the falsifiable prediction

The clearest population-scale result in the thread is also its smallest, and it
was chosen because it is *falsifiable in the world*.

People do not walk where paths are. Paths appear where people walk. A desire
path is the visible residue of many individual route choices, and it is the
canonical example of stigmergy — coordination through modification of a shared
environment rather than through communication.

The prediction: give residents differing route valuations and let traversal wear
the ground, and paths should form where the traffic is, persist while it
continues, and fade when it stops. Nobody plans them.

The build separates two things that are easy to conflate, and the separation is
the design:

> **Route choice is cognition, and lives in a rule. Ground wearing under load is
> physics, and lives in the world.**

Four decisions make the physics side work, each load-bearing:

**One accumulator, read in two directions.** A cell remembers the terrain it was
*seeded* as, plus a wear value. Wearing and fading are the same quantity moving
in opposite directions, so a path that *formed* is never confused with a path
that was *built*. Seeded ground is permanent infrastructure. Worn ground is only
ever the far end of grass's accumulator, and stops being a path when the traffic
stops. Reversion needs no second field, because the target is what the cell
already remembers being.

**Interpolated, not switched.** Part-worn ground is already part-easier to
cross. This is what lets traffic recruit traffic — a threshold-only flip would
make wear invisible until it tripped, and there would be no feedback to converge
on. The positive feedback loop *is* the interpolation.

**Counts, not deltas.** The parameters are "how many crossings make a path" and
"how many idle ticks fade one", because those are the quantities an experimenter
actually wants to set.

**One enactment site.** Footfall hooks where residents arrive, not in every
caller that happens to move someone.

Measured, on one grass cell [TOWN-1]: forty crossings take wear from 0 to 1.0 and the
terrain becomes path, with the movement cost falling smoothly along the way
rather than jumping at the end. Four hundred idle turns take it back to grass.

That is population-scale narrative momentum, in the sense Part VII gives the
term: history surviving as structure, and thereby entering the next possibility
relation. The path is the town's memory of where people went, and it changes
where they go next.

And it is worth being precise about what kind of claim that is, because the
word invites a weaker reading. **This is not a metaphor borrowed from
mechanics.** Momentum, in the sense Part V gives it, is not history carried
forward through time — it is a *currently instantiated* structural consequence
of prior change, constraining what can happen next. The worn ground is exactly
that: nothing about the past crossings persists, and nobody remembers them. What
persists is a compacted cell. Ordinary momentum and narrative momentum have the
same form, and differ in which relations carry the surviving structure.

---

## 13.3 The uncomfortable finding

A chapter about a town where everything works would be selling something. Here
is the thing that does not.

Violence in this town is **fifteen rules across four seed files** — a subsystem
of real engineering weight, rivalling the economy.

**All four of those seed files declare zero grammar productions.**

Which means the entire subsystem mints its edges without going through the
mechanism that decides what edges may exist at all. Every transgression is
modelled as a bespoke rule, in a substrate whose own shape says it should be a
**generated absence** — admissible conduct as the default, inadmissibility as
the rare marked residual, produced by a grammar rather than enumerated by hand.

This is the same defect chapter 3 describes for rules and chapter 9 describes
for control rates, in a third domain, and chapter 15 is where it is counted
across the whole tree. Its appearance here is worth having because it is
*concrete*: a fully working, richly modelled subsystem that is nonetheless built
the wrong way round, and whose wrongness is invisible from inside it because it
behaves correctly.

The refactor is named and not built.

---

## 13.4 The glass box

The reason for a town whose every decision is inspectable is not fidelity. It is
that social findings become **mechanistically auditable** rather than merely
simulated.

An agent-based model that reproduces a social phenomenon has demonstrated that
*some* mechanism produces it. A glass-box one lets you ask which, and check that
the answer is not an artefact of the harness — the questions chapter 16 says
should be asked of every measurement, asked of a society.

The thread carries its own prior-art surveys of social simulation, which is the
right posture: this is not the first town, and the contribution is the
inspectability rather than the simulation.

---

## 13.5 Two boundaries

**The town is a separate project.** Its runtime, world, seeds, agent backends,
client and data live in their own repository. This substrate holds the design
and experiment record for provenance; it does not hold a second implementation,
and any integration belongs at an explicit adapter boundary. Data cited here is
external data.

**The tree computes one thing Part VII forbids.** The only place the word
*narrativium* appears in this substrate is a demonstration script, and what it
computes is a cumulative sum of a per-tick term over ticks — a path integral.
Paper 04's own text says a sequence of expenditures cannot be summed to predict
a later measurement.

The script disclaims itself honestly, in its own comments, as plain host
arithmetic rather than an audited quantity. So it is not a violation by
something claiming compliance. It is recorded here, in the chapter closest to
the subject, because it is the single most likely thing in this tree for a later
reader to mistake for an implementation.

---

## 13.6 What would falsify this

- **Desire paths.** The prediction is falsifiable in the world, which is why it
  was chosen: if a population with heterogeneous route valuations and
  load-sensitive terrain does *not* converge on paths where the traffic is, the
  stigmergy claim fails. It is also falsifiable in the other direction — if
  paths form under *homogeneous* valuations, then heterogeneity was not doing
  the work the design credits it with.
- **The interpolation claim.** If threshold-only wear produces the same
  convergence, the smooth accumulator is unnecessary and the recruitment story
  is wrong.
- **The population claim.** If the network effects of §13.1 can be reproduced in
  a dyad with a stipulated observer, the town is elaborate scaffolding for a
  result that did not need it.
- **The grammar finding.** If the violence subsystem's rules turn out to be
  generated from productions elsewhere, §13.3's count is a misreading of where
  the productions live — which would be a better outcome than the one recorded.

One bound: a hundred residents is a small town, and eight nodes is a small
network. Nothing here establishes that these dynamics hold at a scale where the
interesting sociology usually starts.

---

*Ends. Part IV closes here. Next: Part V, and the smallest statement of what all
of it has been an instance of.*
